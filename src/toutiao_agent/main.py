"""主模块 - CLI入口和业务逻辑"""

import asyncio
import click
from collections import Counter
from pathlib import Path
from typing import Optional
from .config import config
from .toutiao_client import get_client, close_client, ToutiaoClient
from .generator import generator
from .activity_fetcher import activity_fetcher, Activity
from .activity_analyzer import ActivityAnalyzer
from .activity_types import OperationType


class ToutiaoAgent:
    """头条热点评论助手主类"""

    def __init__(self):
        self.client: Optional[ToutiaoClient] = None

    async def initialize(self):
        """初始化客户端"""
        self.client = await get_client()

        # 确保已登录
        await self.client.ensure_login()

    async def get_hot_news(self, limit: int = 20):
        """获取热点新闻"""
        print(f"\n正在获取热点新闻（最多{limit}条）...")
        news_list = await self.client.get_hot_news(limit)

        print(f"\n获取到 {len(news_list)} 条热点新闻:\n")

        for i, news in enumerate(news_list[:10], 1):
            print(f"{i}. {news['title']}")
            print(f"   ID: {news['article_id']}")
            print()

        return news_list

    async def generate_comment(self, title: str, abstract: str = "") -> str:
        """生成评论（返回提示词，由Claude Code处理）"""
        prompt = generator.generate_prompt(title, abstract)
        return prompt

    async def post_comment(self, article_id: str, content: str, title: str = "", url: str = ""):
        """发表评论"""
        result = await self.client.post_comment(article_id, content)
        if result.get('success'):
            # 记录到数据库
            from .storage import storage
            storage.add_comment(article_id, title, url, content)
            print(f"✅ 评论成功! 文章ID: {article_id}")
        else:
            print(f"❌ 评论失败: {result.get('error', '未知错误')}")
        return result

    async def post_micro_headline(
        self,
        content: str,
        activity_id: Optional[str] = None,
        activity_title: Optional[str] = None,
        images: Optional[list] = None,
        topic: Optional[str] = None
    ):
        """发布微头条（直接使用 Playwright）"""
        print(f"\n正在发布微头条...")
        print(f"内容: {content[:100]}{'...' if len(content) > 100 else ''}")

        # 使用客户端的 Playwright 方法发布
        result = await self.client.publish_micro_headline(
            content=content,
            topic=topic,
            images=images
        )

        if result.get('success'):
            # 记录到数据库
            from .storage import storage
            hashtags = topic or ""
            images_json = str(images) if images else None
            storage.add_micro_headline(
                content=content,
                activity_id=activity_id,
                activity_title=activity_title,
                hashtags=hashtags,
                images=images_json
            )
            print(f"✅ 微头条发布成功!")
        else:
            print(f"❌ 微头条发布失败: {result.get('message', result.get('error', '未知错误'))}")

        return result

    async def close(self):
        """关闭客户端"""
        await close_client()


# CLI命令
@click.group()
def cli():
    """头条热点自动评论助手"""
    pass


@cli.command('hot-news')
@click.option('--limit', default=20, help='获取热点数量')
def hot_news_cmd(limit):
    """获取热点新闻"""
    async def run():
        agent = ToutiaoAgent()
        try:
            await agent.initialize()
            await agent.get_hot_news(limit)
        finally:
            await agent.close()
    asyncio.run(run())


@cli.command()
@click.argument('article_id')
@click.argument('content')
def comment_cmd(article_id, content):
    """发表评论

    Example: toutiao-agent comment 123456789 "这是我的评论"
    """
    async def run():
        agent = ToutiaoAgent()
        try:
            await agent.initialize()
            await agent.post_comment(article_id, content)
        finally:
            await agent.close()
    asyncio.run(run())


@cli.command()
@click.option('--count', default=5, help='处理数量')
def start_cmd(count):
    """启动自动评论流程"""
    async def run():
        agent = ToutiaoAgent()
        try:
            await agent.initialize()

            # 获取热点
            news_list = await agent.get_hot_news(count)

            if not news_list:
                print("未获取到热点新闻")
                return

            # 逐个处理
            for i, news in enumerate(news_list[:count], 1):
                print(f"\n--- 处理第 {i}/{min(count, len(news_list))} 条 ---")

                if config.behavior.get('confirmation_mode', True):
                    # 交互模式
                    choice = input(f"是否为 '{news['title']}' 生成评论? (y/n/s跳过): ").strip().lower()
                    if choice != 'y':
                        continue

                # 生成提示词
                prompt = await agent.generate_comment(news['title'])

                if config.behavior.get('confirmation_mode', True):
                    print("\n提示词:")
                    print(prompt)
                    print("\n请将上述提示词发送给Claude获取评论，然后输入评论内容:")
                    comment_text = input("评论内容: ").strip()

                    if not comment_text:
                        print("跳过")
                        continue

                    # 确认发布
                    confirm = input("确认发布? (y/n): ").strip().lower()
                    if confirm != 'y':
                        print("已取消")
                        continue

                    # 发表评论
                    await agent.post_comment(news['article_id'], comment_text, news['title'], news.get('url', ''))

                    # 间隔
                    if i < count:
                        interval = config.behavior.get('comment_interval', 30)
                        print(f"\n等待 {interval} 秒后继续...")
                        await asyncio.sleep(interval)
                else:
                    # 非交互模式，只输出提示词
                    print(f"\n文章: {news['title']}")
                    print(f"提示词:\n{prompt}\n")

        finally:
            await agent.close()
    asyncio.run(run())


@cli.command('config-show')
def config_show():
    """显示当前配置"""
    import yaml
    click.echo(yaml.dump(config.config, allow_unicode=True))


@cli.command('history')
@click.option('--limit', default=20, help='显示条数')
def history_cmd(limit):
    """查看评论历史"""
    from .storage import storage

    records = storage.get_history(limit)
    if not records:
        click.echo("暂无评论记录")
        return

    click.echo(f"\n最近 {len(records)} 条评论:\n")
    for r in records:
        click.echo(f"📅 {r['created_at']}")
        click.echo(f"   文章: {r['title'][:50]}...")
        click.echo(f"   评论: {r['content'][:50]}...")
        click.echo(f"   ID: {r['article_id']}\n")


@cli.command('stats')
def stats_cmd():
    """查看评论统计"""
    from .storage import storage

    count = storage.get_comment_count()
    click.echo(f"\n📊 评论统计:")
    click.echo(f"   总评论数: {count}")
    click.echo(f"   数据库: {config.storage.get('db_file')}\n")


# ============ 微头条相关命令 ============

@cli.command('post-micro-headline')
@click.argument('content')
@click.option('--topic', '-t', help='话题标签（如 #科技#）')
@click.option('--activity-id', '-a', help='活动ID（如果有）')
@click.option('--activity-title', help='活动标题（如果有）')
def post_micro_headline_cmd(content, topic, activity_id, activity_title):
    """发布微头条

    Example: toutiao-agent post-micro-headline "今天天气真好" --topic "#生活#"
    """
    async def run():
        agent = ToutiaoAgent()
        try:
            await agent.initialize()

            # 确认模式
            if config.behavior.get('confirmation_mode', True):
                print(f"\n即将发布微头条:")
                print(f"  内容: {content}")
                if topic:
                    print(f"  话题: {topic}")
                if activity_title:
                    print(f"  活动: {activity_title}")
                confirm = input("\n确认发布? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("已取消")
                    return

            # 发布
            await agent.post_micro_headline(
                content=content,
                activity_id=activity_id,
                activity_title=activity_title,
                topic=topic
            )
        finally:
            await agent.close()
    asyncio.run(run())


@cli.command('micro-headlines')
@click.option('--limit', default=20, help='显示条数')
def micro_headlines_cmd(limit):
    """查看微头条发布历史"""
    from .storage import storage

    records = storage.get_micro_headlines(limit)
    if not records:
        click.echo("暂无微头条记录")
        return

    click.echo(f"\n📝 最近 {len(records)} 条微头条:\n")
    for r in records:
        click.echo(f"📅 {r['created_at']}")
        if r['activity_title']:
            click.echo(f"   活动: {r['activity_title']}")
        click.echo(f"   内容: {r['content'][:80]}{'...' if len(r['content']) > 80 else ''}")
        if r['hashtags']:
            click.echo(f"   话题: {r['hashtags']}")
        click.echo(f"   状态: {r['status']}\n")


@cli.command('micro-stats')
def micro_stats_cmd():
    """查看微头条统计"""
    from .storage import storage

    count = storage.get_micro_headline_count()
    click.echo(f"\n📊 微头条统计:")
    click.echo(f"   总发布数: {count}\n")


# ============ 活动相关命令 ============

@cli.command('activities')
@click.option('--limit', default=10, help='显示数量')
@click.option('--category', default='全部', help='分类筛选')
@click.option('--all', '-a', is_flag=True, help='显示全部活动（包括已参与和已过期）')
def activities_cmd(limit, category, all):
    """查看活动列表"""
    from .storage import storage

    print(f"\n正在获取活动列表...")

    activities = activity_fetcher.fetch_activities(
        limit=limit,
        category=category,
        only_ongoing=not all,
        only_unparticipated=not all
    )

    if not activities:
        print("暂无可用活动")
        return

    click.echo(f"\n📋 找到 {len(activities)} 个活动:\n")

    for i, activity in enumerate(activities[:limit], 1):
        click.echo(f"{i}. {activity.title}")
        click.echo(f"   📖 {activity.introduction}")
        if activity.hashtag_name:
            click.echo(f"   🏷️  话题: #{activity.hashtag_name}#")
        click.echo(f"   ⏰ {activity.activity_time}")
        click.echo(f"   💰 {activity.activity_reward}")
        click.echo(f"   👥 {activity.activity_participants} 人参与")

        # 检查是否已参与
        if storage.is_activity_participated(str(activity.activity_id)):
            click.echo(f"   ✅ 已参与")
        else:
            click.echo(f"   ⭕ 未参与")

        click.echo(f"   🆔 ID: {activity.activity_id}")
        click.echo()


@cli.command('start-activities')
@click.option('--count', default=5, help='参与活动数量')
def start_activities_cmd(count):
    """智能参与活动（AI分析活动类型并执行相应操作）"""
    from .storage import storage

    async def run():
        agent = ToutiaoAgent()
        analyzer = ActivityAnalyzer()
        try:
            await agent.initialize()

            # 获取活动列表
            print(f"\n正在获取活动列表...")
            activities = activity_fetcher.fetch_activities(
                limit=count * 2,  # 获取更多以便筛选
                only_ongoing=True,
                only_unparticipated=True
            )

            # 过滤已参与的活动
            new_activities = [
                a for a in activities
                if not storage.is_activity_participated(str(a.activity_id))
            ]

            if not new_activities:
                print("暂无新的活动可参与")
                return

            click.echo(f"\n找到 {len(new_activities)} 个新活动\n")

            # 逐个处理活动
            for i, activity in enumerate(new_activities[:count], 1):
                print(f"\n--- 处理第 {i}/{min(count, len(new_activities))} 个活动 ---")
                print(f"活动: {activity.title}")
                print(f"介绍: {activity.introduction}")

                # 确认模式
                if config.behavior.get('confirmation_mode', True):
                    choice = input(f"\n是否参与此活动? (y/n/s跳过): ").strip().lower()
                    if choice != 'y':
                        continue

                # AI 分析活动
                print("\n正在分析活动类型...")
                result = await analyzer.analyze(activity)

                # 显示分析结果
                print(f"\n=== AI 分析结果 ===")
                print(f"活动标题: {result.activity_title}")
                print(f"活动介绍: {result.activity_intro}")
                print(f"操作类型: {result.operation_type.label}")
                print(f"置信度: {result.confidence:.0%}")
                print(f"建议: {result.suggested_action}")

                # 记录分析结果到数据库
                storage.add_activity_participation(
                    activity_id=str(activity.activity_id),
                    activity_title=activity.title,
                    operation_type=result.operation_type.value,
                    confidence=result.confidence,
                    ai_analysis=result.to_dict(),
                    user_confirmed=False
                )

                # 确认操作方式
                if config.behavior.get('confirmation_mode', True):
                    print(f"\n检测到的操作方式: {result.operation_type.label}")
                    confirm = input(f"是否使用此方式? (y=使用 / n=使用其他方式): ").strip().lower()

                    if confirm == 'n':
                        # 用户选择其他方式
                        print("\n可选择的其他方式:")
                        print("  1. 生成原创微头条 (generate_content)")
                        print("  2. 点赞/转发 (like_share)")
                        print("  3. 填写表单 (fill_form)")
                        print("  4. 一键参与 (one_click)")
                        print("  5. 其他 (other)")

                        choice = input("\n请选择操作方式 (1-5): ").strip()
                        operation_map = {
                            '1': OperationType.GENERATE_CONTENT,
                            '2': OperationType.LIKE_SHARE,
                            '3': OperationType.FILL_FORM,
                            '4': OperationType.ONE_CLICK,
                            '5': OperationType.OTHER
                        }
                        operation = operation_map.get(choice, OperationType.OTHER)
                    else:
                        operation = result.operation_type
                else:
                    operation = result.operation_type

                # 根据操作类型执行
                if operation == OperationType.GENERATE_CONTENT or config.behavior.get('confirmation_mode', True):
                    # 生成原创内容流程
                    hashtag = activity.get_hashtag() or activity.hashtag_name or ""
                    prompt = f"""请根据以下活动信息生成一条微头条内容：

活动标题: {activity.title}
活动介绍: {activity.introduction}
话题标签: #{hashtag}#

要求:
- 字数: 100-300 字
- 必须包含话题标签
- 内容与活动主题相关
- 积极向上的语气
- 适当使用 emoji

请直接输出微头条内容。"""

                    if config.behavior.get('confirmation_mode', True):
                        print("\n提示词:")
                        print(prompt)
                        print("\n请将上述提示词发送给Claude获取微头条内容，然后输入内容:")

                        content = input("微头条内容: ").strip()

                        if not content:
                            print("跳过")
                            continue

                        # 确认发布
                        print(f"\n即将发布:")
                        print(f"  内容: {content[:100]}{'...' if len(content) > 100 else ''}")
                        if hashtag:
                            print(f"  话题: #{hashtag}#")

                        confirm = input("\n确认发布? (y/n): ").strip().lower()
                        if confirm != 'y':
                            print("已取消")
                            continue

                        # 发布微头条
                        result = await agent.post_micro_headline(
                            content=content,
                            activity_id=str(activity.activity_id),
                            activity_title=activity.title,
                            topic=f"#{hashtag}#" if hashtag else None
                        )

                        # 更新参与记录
                        storage.add_activity_participation(
                            activity_id=str(activity.activity_id),
                            activity_title=activity.title,
                            operation_type=operation.value,
                            confidence=0.0,
                            ai_analysis=None,
                            user_confirmed=True,
                            execution_result='success' if result.get('success') else result.get('error', 'failed')
                        )

                        if result.get('success'):
                            # 间隔
                            if i < count:
                                interval = config.behavior.get('comment_interval', 30)
                                print(f"\n等待 {interval} 秒后继续...")
                                await asyncio.sleep(interval)
                    else:
                        # 非交互模式，只输出提示词
                        print(f"\n活动: {activity.title}")
                        print(f"提示词:\n{prompt}\n")
                else:
                    print(f"\n暂未实现操作类型: {operation.label}")
                    print("请手动参与活动或选择生成原创内容方式")
                    # 更新参与记录
                    storage.add_activity_participation(
                        activity_id=str(activity.activity_id),
                        activity_title=activity.title,
                        operation_type=operation.value,
                        confidence=0.0,
                        ai_analysis=None,
                        user_confirmed=True,
                        execution_result='not_implemented'
                    )

        finally:
            await agent.close()
    asyncio.run(run())


@cli.command('activity-history')
@click.option('--limit', default=20, help='显示条数')
def activity_history_cmd(limit):
    """查看活动参与历史"""
    from .storage import storage

    records = storage.get_activity_participations(limit)
    if not records:
        click.echo("暂无活动参与记录")
        return

    click.echo(f"\n最近 {len(records)} 条活动参与记录:\n")

    from .activity_types import OperationType

    for r in records:
        click.echo(f"📅 {r['created_at']}")
        if r['activity_title']:
            click.echo(f"   活动: {r['activity_title'][:50]}...")
        click.echo(f"   操作类型: {r['operation_type']}")
        click.echo(f"   置信度: {r['confidence'] * 100:.0f}%")
        click.echo(f"   用户确认: {'✅' if r['user_confirmed'] else '❌'}")
        if r['execution_result']:
            click.echo(f"   结果: {r['execution_result']}")
        click.echo()


@cli.command('activity-stats')
def activity_stats_cmd():
    """查看活动参与统计"""
    from .storage import storage

    records = storage.get_activity_participations(limit=1000)
    if not records:
        click.echo("暂无统计数据")
        return

    total = len(records)
    confirmed = sum(1 for r in records if r['user_confirmed'])
    avg_confidence = sum(r['confidence'] for r in records) / total if total > 0 else 0

    # 按操作类型统计
    type_counts = Counter(r['operation_type'] for r in records)

    click.echo(f"\n📊 活动参与统计:\n")
    click.echo(f"   总参与次数: {total}")
    click.echo(f"   用户确认: {confirmed}")
    click.echo(f"   平均置信度: {avg_confidence * 100:.1f}%")
    click.echo(f"\n   操作类型分布:")
    for op_type, count in type_counts.most_common():
        click.echo(f"   - {op_type}: {count}")
    click.echo()


if __name__ == '__main__':
    cli()

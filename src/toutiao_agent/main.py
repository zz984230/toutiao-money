"""主模块 - CLI入口和业务逻辑"""

import asyncio
import click
from pathlib import Path
from typing import Optional
from .config import config
from .toutiao_client import get_client, close_client, ToutiaoClient
from .generator import generator
from .mcp_client import mcp_client
from .activity_fetcher import activity_fetcher, Activity


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
        """发布微头条（通过 MCP 服务器）"""
        if not config.mcp.get('enabled', True):
            print("❌ MCP 功能未启用，请检查配置")
            return {'success': False, 'error': 'MCP 未启用'}

        print(f"\n正在发布微头条...")
        print(f"内容: {content[:100]}{'...' if len(content) > 100 else ''}")

        result = await mcp_client.publish_micro_post(
            content=content,
            images=images,
            topic=topic
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
            print(f"❌ 微头条发布失败: {result.get('error', '未知错误')}")

        return result

    async def check_mcp_login(self) -> bool:
        """检查 MCP 服务器的登录状态"""
        if not config.mcp.get('enabled', True):
            print("❌ MCP 功能未启用")
            return False

        result = await mcp_client.check_login_status()
        if result.get('success'):
            is_logged_in = result.get('is_logged_in', False)
            if is_logged_in:
                user_info = result.get('user_info', {})
                print(f"✅ MCP 已登录: {user_info.get('username', '未知用户')}")
                return True
            else:
                print("⚠️  MCP 未登录，请先登录")
                return False
        else:
            print(f"❌ 检查登录状态失败: {result.get('error', '未知错误')}")
            return False

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
            # 检查 MCP 登录状态
            login_ok = await agent.check_mcp_login()
            if not login_ok:
                return

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
    click.echo(f"   总发布数: {count}")
    click.echo(f"   MCP 服务器: {config.mcp.get('server_url')}\n")


@cli.command('mcp-login')
def mcp_login_cmd():
    """登录 MCP 服务器"""
    async def run():
        # 从环境变量获取账号密码
        from .config import config
        username, password = config.get_toutiao_credentials()

        if not username or not password:
            print("❌ 请在 .env 文件中设置 TOUTIAO_USERNAME 和 TOUTIAO_PASSWORD")
            return

        print(f"正在登录 MCP 服务器...")
        result = await mcp_client.login_with_credentials(username, password)

        if result.get('success'):
            print(f"✅ 登录成功!")
        else:
            print(f"❌ 登录失败: {result.get('error', '未知错误')}")
    asyncio.run(run())


@cli.command('mcp-status')
def mcp_status_cmd():
    """查看 MCP 服务器状态"""
    async def run():
        print(f"\n🔍 MCP 服务器状态:")
        print(f"   地址: {config.mcp.get('server_url')}")
        print(f"   启用: {'是' if config.mcp.get('enabled', True) else '否'}")

        result = await mcp_client.check_login_status()
        if result.get('success'):
            is_logged_in = result.get('is_logged_in', False)
            print(f"   连接: ✅ 正常")
            print(f"   登录: {'✅ 已登录' if is_logged_in else '❌ 未登录'}")
            if is_logged_in:
                user_info = result.get('user_info', {})
                print(f"   用户: {user_info.get('username', '未知')}")
        else:
            print(f"   连接: ❌ 失败")
            print(f"   错误: {result.get('error', '未知错误')}")
        print()
    asyncio.run(run())


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
    """自动参与活动（生成并发布微头条）"""
    from .storage import storage

    async def run():
        agent = ToutiaoAgent()
        try:
            # 检查 MCP 登录状态
            print("\n检查 MCP 登录状态...")
            login_ok = await agent.check_mcp_login()
            if not login_ok:
                return

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

                # 生成提示词
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

        finally:
            await agent.close()
    asyncio.run(run())


if __name__ == '__main__':
    cli()

"""主模块 - CLI入口和业务逻辑"""

import asyncio
import click
from pathlib import Path
from typing import Optional
from .config import config
from .toutiao_client import get_client, close_client, ToutiaoClient
from .generator import generator


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


if __name__ == '__main__':
    cli()

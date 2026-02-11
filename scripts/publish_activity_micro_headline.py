#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布活动微头条"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from toutiao_agent.toutiao_client import get_client
from toutiao_agent.activity_fetcher import activity_fetcher
from toutiao_agent.storage import storage


async def publish_activity_headline():
    """根据活动发布微头条"""
    print("=== 发布活动微头条 ===\n")

    # 获取活动
    activities = activity_fetcher.fetch_activities(limit=5, only_ongoing=True, only_unparticipated=True)

    if not activities:
        print("没有找到活动")
        return

    activity = activities[0]
    print(f"活动: {activity.title}")
    print(f"介绍: {activity.introduction}")
    print(f"话题: #{activity.hashtag_name or activity.get_hashtag() or '天南地北大拜年'}#\n")

    # 生成微头条内容
    hashtag = activity.hashtag_name or "天南地北大拜年"
    content = f"""春节的脚步越来越近，全国各地的人们都在为团圆做准备。🧧

从北国冰雪到南国花开，从东部海滨到西部高原，每个地方都有独特的春节习俗。

贴春联、包饺子、看春晚、放鞭炮...这些传统的年味儿，承载着我们对新一年的美好期盼。

你的家乡有哪些春节习俗？欢迎在评论区分享！🎊

#{hashtag}#"""

    print(f"生成的微头条内容:")
    print(f"  {content[:100]}...\n")

    # 初始化客户端
    client = await get_client()

    # 确保已登录
    print("检查登录状态...")
    is_logged_in = await client.check_login_status()
    if not is_logged_in:
        print("⚠️ Cookie 可能已过期，但尝试继续...")

    # 发布微头条
    print("正在发布微头条...")
    result = await client.publish_micro_headline(
        content=content,
        topic=f"#{hashtag}#"
    )

    print(f"\n发布结果:")
    print(f"  成功: {result.get('success')}")
    print(f"  消息: {result.get('message', result.get('error', '未知'))}")

    if result.get('success'):
        # 记录到数据库
        storage.add_micro_headline(
            content=content,
            activity_id=str(activity.activity_id),
            activity_title=activity.title,
            hashtags=f"#{hashtag}#"
        )
        print(f"\n✅ 已记录到数据库")

    await client.close()


if __name__ == "__main__":
    asyncio.run(publish_activity_headline())

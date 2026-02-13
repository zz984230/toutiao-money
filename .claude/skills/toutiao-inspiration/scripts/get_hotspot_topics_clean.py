# -*- coding: utf-8 -*-
"""从热点活动页面获取热门话题，按阅读量排序（改进版）"""
import asyncio
import sys
import re
import json
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from toutiao_agent.toutiao_client import ToutiaoClient


def is_valid_topic(topic_name):
    """判断是否是有效话题"""
    if not topic_name:
        return False

    # 过滤包含CSS特殊字符的
    invalid_chars = ['{', '}', ':', ';', '.', '(', ')', '=', 'px', '%', 'var(', 'linear-gradient', 'rgba']
    for char in invalid_chars:
        if char in topic_name:
            return False

    # 过滤太长的（可能不是话题）
    if len(topic_name) > 30:
        return False

    # 过滤纯英文/数字的（话题应该是中文为主）
    chinese_count = sum(1 for c in topic_name if '\u4e00' <= c <= '\u9fff')
    if len(topic_name) > 0 and chinese_count / len(topic_name) < 0.3:
        return False

    # 过滤包含特定CSS关键字的
    css_keywords = ['background', 'color', 'display', 'cursor', 'border', 'padding',
                   'transition', 'transform', 'z-index', 'opacity', 'box-shadow']
    for keyword in css_keywords:
        if keyword in topic_name.lower():
            return False

    return True


async def main():
    client = ToutiaoClient()
    await client.start()

    try:
        # 访问热点活动页面
        url = "https://mp.toutiao.com/profile_v4/activity/hot-spot"
        print(f"访问热点活动页面: {url}")
        await client.page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)

        # 使用 JavaScript 提取话题信息
        topics_info = await client.page.evaluate("""() => {
            const results = [];
            const pageText = document.body.innerText || document.body.textContent || '';

            // 正则：#话题# 后面跟着数字（可能是阅读量）
            // 格式：#话题# 阅读1234 或 #话题# 1234.5万阅读
            const pattern = /#([^#\s]+(?:\s+[^#\s]+)*)#\s*(?:阅读\s*)?(\d+(?:\.\d+)?)?\s*(?:万|亿)?/g;

            let match;
            const seen = new Set();

            while ((match = pattern.exec(pageText)) !== null) {
                const topicName = match[1].trim();
                const number = parseFloat(match[2]) || 0;

                // 去重
                if (!seen.has(topicName)) {
                    seen.add(topicName);
                    results.push({
                        topic: topicName,
                        readCount: number
                    });
                }
            }

            return results;
        }""")

        # 过滤无效话题
        valid_topics = []
        for item in topics_info:
            topic_name = item.get('topic', '')
            if is_valid_topic(topic_name):
                valid_topics.append(item)

        # 按阅读量降序排序
        valid_topics.sort(key=lambda x: x.get('readCount', 0), reverse=True)

        print(f"\n发现 {len(valid_topics)} 个有效话题：")
        print("=" * 80)
        for i, item in enumerate(valid_topics[:20], 1):
            topic = item.get('topic', '')
            count = item.get('readCount', 0)
            print(f"{i:2d}. #{topic}# - 阅读量: {count}万")

        # 保存到 JSON 文件
        topics_file = project_root / "data" / "hotspot_topics_clean.json"
        with open(topics_file, 'w', encoding='utf-8') as f:
            json.dump(valid_topics, f, ensure_ascii=False, indent=2)
        print(f"\n话题已保存到: {topics_file}")

        return valid_topics

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

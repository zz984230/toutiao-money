# -*- coding: utf-8 -*-
"""分析话题内容，提取他人发布的微头条"""
import asyncio
import sys
import io
import json
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from toutiao_agent.toutiao_client import ToutiaoClient


async def main():
    client = ToutiaoClient()
    await client.start()

    try:
        topic_name = "分享一件你喜欢的藏品"

        # 构建话题搜索 URL
        search_url = f"https://so.toutiao.com/search?keyword={topic_name}&pd=synthesis&source=input"
        print(f"访问搜索页面: {search_url}")
        await client.page.goto(search_url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        # 使用 JavaScript 提取页面内容
        page_data = await client.page.evaluate("""() => {
            const results = [];

            // 尝试选择器列表
            const selectors = [
                'div[class*="item"]',
                'div[class*="list"]',
                'article',
                'div[class*="content"]',
                '[data-log]'
            ];

            for (const selector of selectors) {
                const elements = document.querySelectorAll(selector);
                if (elements.length > 0) {
                    // 收集前 10 个元素的内容
                    for (let i = 0; i < Math.min(elements.length, 10); i++) {
                        const el = elements[i];
                        const text = el.innerText || el.textContent || '';
                        if (text && text.length > 20 && text.length < 500) {
                            results.push(text.trim());
                        }
                    }
                    if (results.length > 0) break;
                }
            }

            return results;
        }""")

        print(f"\n提取到 {len(page_data)} 条内容:")
        print("=" * 80)
        for i, content in enumerate(page_data[:5], 1):
            print(f"\n{i}. {content[:200]}...")
            print("-" * 80)

        # 保存到文件
        output_file = project_root / ".claude" / "data" / "topic_content_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'topic': topic_name,
                'content_samples': page_data,
                'count': len(page_data)
            }, f, ensure_ascii=False, indent=2)

        print(f"\n内容已保存到: {output_file}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

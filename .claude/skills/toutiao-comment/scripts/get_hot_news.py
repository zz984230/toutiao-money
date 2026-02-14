# -*- coding: utf-8 -*-
"""从头条首页热点标签获取热点新闻"""
import asyncio
import sys
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
from toutiao_agent.storage import storage


async def main():
    client = ToutiaoClient()
    await client.start()

    try:
        # 先确保已登录
        print("检查登录状态...")
        if not await client.ensure_login():
            print("登录失败，请检查配置")
            return

        # 访问头条首页
        url = "https://www.toutiao.com/"
        print(f"访问头条首页: {url}")
        await client.page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        # 点击【热点】标签
        print("查找【热点】标签...")
        hotspot_clicked = await client.page.evaluate('''() => {
            // 多种选择器策略
            const selectors = [
                // 文本包含"热点"的链接
                ...Array.from(document.querySelectorAll('a')).filter(a => a.textContent.includes('热点')),
                // 导航栏中的链接
                ...Array.from(document.querySelectorAll('.nav-link a, .menu-link a')).filter(a => a.textContent.includes('热点')),
                // 标签样式
                ...Array.from(document.querySelectorAll('[class*="tab"] a, [class*="tag"] a')).filter(a => a.textContent.includes('热点'))
            ];

            // 去重
            const uniqueLinks = [...new Set(selectors)];

            for (const link of uniqueLinks) {
                const rect = link.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    link.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    link.click();
                    return { clicked: true, href: link.href, text: link.textContent };
                }
            }

            return { clicked: false };
        }''')

        if hotspot_clicked['clicked']:
            print("  已点击【热点】标签: " + str(hotspot_clicked.get('text', '')))
            await asyncio.sleep(3)
        else:
            print("  未找到【热点】标签，尝试直接访问热点页面...")
            # 尝试直接访问热点URL
            hotspot_urls = [
                "https://www.toutiao.com/hot-spot/",
                "https://www.toutiao.com/hotspot/",
                "https://www.toutiao.com/ch/news_hot/"
            ]
            for hotspot_url in hotspot_urls:
                try:
                    await client.page.goto(hotspot_url, wait_until="networkidle", timeout=30000)
                    await asyncio.sleep(3)
                    print("  已访问: " + hotspot_url)
                    break
                except:
                    continue

        # 获取热点新闻列表
        print("获取热点新闻列表...")
        news_items = await client.page.evaluate('''() => {
            const results = [];

            // 多种选择器策略
            const selectors = [
                'a[href*="/group/"]',
                'a[href*="/article/"]',
                'a[href*="/i/"]',
                '.title-link a',
                'a[class*="title"]',
                '[class*="item"] a[href*="/group/"]'
            ];

            const seenUrls = new Set();

            for (const selector of selectors) {
                const links = document.querySelectorAll(selector);

                for (const link of links) {
                    try {
                        const href = link.getAttribute('href');
                        if (!href || seenUrls.has(href)) continue;
                        if (!href.includes('/group/') && !href.includes('/article/') && !href.includes('/i/')) continue;

                        seenUrls.add(href);

                        // 提取 article_id
                        const match = href.match(/(group|article|i)\\/(\\d+)/);
                        if (!match) continue;

                        const articleId = match[2];

                        // 提取标题
                        let title = '';
                        const titleSelectors = ['.title', 'h1', 'h2', 'h3', '[class*="Title"]'];
                        for (const ts of titleSelectors) {
                            const titleEl = link.querySelector(ts);
                            if (titleEl) {
                                title = titleEl.textContent || '';
                                break;
                            }
                        }

                        if (!title) {
                            title = link.textContent || link.getAttribute('title') || '';
                        }

                        title = title.trim();

                        if (title && title.length > 5) {
                            results.push({
                                article_id: articleId,
                                title: title.substring(0, 100),
                                url: href.startsWith('http') ? href : ('https://www.toutiao.com' + href)
                            });
                        }

                        if (results.length >= 50) break;
                    } catch (e) {
                        continue;
                    }
                }

                if (results.length >= 50) break;
            }

            return results;
        }''')

        print("  找到 " + str(len(news_items)) + " 条新闻")

        # 过滤已评论的文章
        filtered_items = []
        seen_ids = set()

        for item in news_items:
            article_id = item['article_id']
            if article_id in seen_ids:
                continue
            seen_ids.add(article_id)

            if not storage.is_commented(article_id):
                filtered_items.append(item)

        print("  过滤后剩余 " + str(len(filtered_items)) + " 条未评论新闻")

        # 显示新闻列表
        if filtered_items:
            print("\n热点新闻列表：")
            print("=" * 80)
            for i, item in enumerate(filtered_items[:20], 1):
                title = item['title']
                article_id = item['article_id']
                print(str(i) + ". " + title + " (ID: " + article_id + ")")

        # 保存到 JSON 文件
        data_dir = project_root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        news_file = data_dir / "hot_news.json"

        with open(news_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_items, f, ensure_ascii=False, indent=2)

        print("\n新闻列表已保存到: " + str(news_file))

        return filtered_items

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

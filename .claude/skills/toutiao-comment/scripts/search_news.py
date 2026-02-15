# -*- coding: utf-8 -*-
"""Search news by keywords on Toutiao"""
import asyncio
import sys
import re
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from toutiao_agent.toutiao_client import ToutiaoClient
from toutiao_agent.storage import storage


async def search_news(keywords: list[str], limit: int = 10):
    """
    Search news by keywords

    Args:
        keywords: List of keywords to search
        limit: Maximum number of results to return

    Returns:
        List of news items matching the keywords
    """
    client = ToutiaoClient()
    await client.start()

    try:
        all_news = []

        for keyword in keywords:
            print(f"Searching for: {keyword}")

            # Build search URL
            from urllib.parse import quote
            search_url = f'https://www.toutiao.com/search/?keyword={quote(keyword)}'
            print(f"  URL: {search_url}")
            await client.page.goto(search_url, timeout=30000)
            await asyncio.sleep(3)

            # Scroll to load more content
            for _ in range(3):
                await client.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(1)

            # Get page HTML
            html_content = await client.page.content()

            # Find all article IDs and their positions
            # Pattern: article/1234567890
            article_pattern = r'article/(\d{10,})'
            article_ids = []
            for match in re.finditer(article_pattern, html_content):
                article_ids.append((match.start(), match.group(1)))

            print(f"  Found {len(article_ids)} article IDs")

            # For each article ID, look for Title within 500 chars before it
            seen_ids = set()
            news_items = []

            for pos, article_id in article_ids:
                if article_id in seen_ids:
                    continue
                seen_ids.add(article_id)

                # Look for Title field within 500 chars before article ID
                start = max(0, pos - 500)
                end = min(pos + 500, len(html_content))
                context = html_content[start:end]

                # Try to find "Title":"title" pattern
                title_pattern = rf'"Title":"([^"]{{1,100}})"'
                title_match = re.search(title_pattern, context)
                if title_match:
                    title = title_match.group(1)
                    # Decode URL encoding
                    title = unquote(title)
                    title = re.sub(r'%[0-9A-F]{2}', '', title)
                    title = re.sub(r'&[^;]*', '', title)
                    title = re.sub(r'\\', '', title)
                    title = title.strip()
                else:
                    title = f'新闻文章 {article_id}'

                if title and len(title) > 5:
                    news_items.append({
                        'title': title,
                        'article_id': article_id,
                        'url': f'https://www.toutiao.com/article/{article_id}/'
                    })

                    if len(news_items) >= 20:
                        break

            print(f"  Found {len(news_items)} items")
            all_news.extend(news_items)
            await asyncio.sleep(1)

        # Filter uncommented and dedupe
        seen_ids = set()
        filtered_items = []

        for item in all_news:
            article_id = item['article_id']
            if article_id in seen_ids:
                continue
            seen_ids.add(article_id)

            if not storage.is_commented(article_id):
                filtered_items.append(item)
                if len(filtered_items) >= limit:
                    break

        return filtered_items

    finally:
        await client.close()


async def main(keywords: list[str]):
    # Search for news
    results = await search_news(keywords, limit=15)

    print(f"\nFound {len(results)} uncommented news matching keywords:")
    for i, item in enumerate(results, 1):
        print(f"{i}. {item['title']} (ID: {item['article_id']})")

    # Save to file
    import json
    output_file = Path("data/hot_news.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to {output_file}")


if __name__ == "__main__":
    # Allow command line arguments
    if len(sys.argv) > 1:
        keywords = sys.argv[1:]
    else:
        keywords = ['飞驰人生3', '贺岁档', '春节档电影']

    asyncio.run(main(keywords))

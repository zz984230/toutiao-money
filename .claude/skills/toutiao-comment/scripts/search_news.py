# -*- coding: utf-8 -*-
"""Search news by keywords on Toutiao"""
import asyncio
import sys
import re
import json
from pathlib import Path
from urllib.parse import quote, unquote

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from toutiao_agent.toutiao_client import ToutiaoClient
from toutiao_agent.storage import storage


def clean_title(title: str) -> str:
    """Clean and normalize title text"""
    if not title:
        return ""
    # Decode URL encoding
    title = unquote(title)
    # Remove HTML entities
    title = re.sub(r'&[^;]+;', '', title)
    # Remove escape characters
    title = title.replace('\\u003c', '<').replace('\\u003e', '>').replace('\\u0026', '&')
    title = re.sub(r'\\u[0-9a-fA-F]{4}', '', title)
    # Remove <em> tags (search highlighting)
    title = re.sub(r'</?em>', '', title)
    # Remove extra whitespace
    title = ' '.join(title.split())
    return title.strip()


async def search_news(keywords: list[str], limit: int = 15):
    """
    Search news by keywords on Toutiao

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
            search_url = f'https://www.toutiao.com/search/?keyword={quote(keyword)}'
            print(f"  URL: {search_url}")
            await client.page.goto(search_url, timeout=30000, wait_until='domcontentloaded')
            await asyncio.sleep(3)

            # Scroll to load more content (increased from 3 to 5)
            for i in range(5):
                await client.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(1.2)

            # Get page HTML
            html_content = await client.page.content()
            print(f"  HTML length: {len(html_content)}")

            # Multiple extraction patterns for better coverage
            news_items = []
            seen_ids = set()

            # Pattern 1: Standard article ID pattern with title nearby
            # Format: "article_id":"xxx","title":"xxx" or similar
            pattern1 = r'"article_id":"(\d{10,})"[^}]*?"title":"([^"]+)"'
            for match in re.finditer(pattern1, html_content, re.IGNORECASE):
                article_id, title = match.groups()
                if article_id not in seen_ids:
                    title = clean_title(title)
                    if len(title) > 5:
                        seen_ids.add(article_id)
                        news_items.append({
                            'title': title,
                            'article_id': article_id,
                            'url': f'https://www.toutiao.com/article/{article_id}/'
                        })

            # Pattern 2: ID field pattern
            # Format: "id":"xxx" ... "title":"xxx"
            pattern2 = r'"id":"(\d{10,})"[^}]*?"title":"([^"]+)"'
            for match in re.finditer(pattern2, html_content, re.IGNORECASE):
                article_id, title = match.groups()
                if article_id not in seen_ids:
                    title = clean_title(title)
                    if len(title) > 5:
                        seen_ids.add(article_id)
                        news_items.append({
                            'title': title,
                            'article_id': article_id,
                            'url': f'https://www.toutiao.com/article/{article_id}/'
                        })

            # Pattern 3: Look for article IDs and find titles nearby (fallback)
            # Find article IDs first, then look for title in context
            article_id_pattern = r'article/(\d{10,})'
            for match in re.finditer(article_id_pattern, html_content):
                article_id = match.group(1)
                if article_id in seen_ids:
                    continue

                pos = match.start()
                # Look in a wider context window
                start = max(0, pos - 800)
                end = min(pos + 800, len(html_content))
                context = html_content[start:end]

                # Try multiple title patterns
                title = None
                title_patterns = [
                    r'"title"\s*:\s*"([^"]+)"',
                    r'"Title"\s*:\s*"([^"]+)"',
                    r'\\?"title\\?"\s*:\\?\s*\\?"([^"\\]+)',
                ]

                for tp in title_patterns:
                    title_match = re.search(tp, context, re.IGNORECASE)
                    if title_match:
                        title = clean_title(title_match.group(1))
                        if len(title) > 5:
                            break

                if title and len(title) > 5:
                    seen_ids.add(article_id)
                    news_items.append({
                        'title': title,
                        'article_id': article_id,
                        'url': f'https://www.toutiao.com/article/{article_id}/'
                    })

            print(f"  Found {len(news_items)} items from this keyword")
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

        print(f"Total filtered: {len(filtered_items)} uncommented news")
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
    output_file = Path("data/hot_news.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to {output_file}")


if __name__ == "__main__":
    # Allow command line arguments
    if len(sys.argv) > 1:
        keywords = sys.argv[1:]
    else:
        keywords = ['春节档电影', '贺岁档']

    asyncio.run(main(keywords))

"""获取文章详情内容"""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright


async def main():
    article_id = "7601682672754197027"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        # 使用 storage_state 方式加载 cookie
        cookie_file = Path('data/cookies.json')
        if cookie_file.exists():
            context = await browser.new_context(storage_state=str(cookie_file))
        else:
            context = await browser.new_context()

        page = await context.new_page()
        url = f'https://www.toutiao.com/article/{article_id}/'
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)

        # 等待内容加载
        try:
            await page.wait_for_selector('article', timeout=10000)
        except:
            pass

        # 提取标题
        title_elem = await page.query_selector('h1')
        title = await title_elem.text_content() if title_elem else ''

        # 获取正文内容
        content_elem = await page.query_selector('article')
        content = await content_elem.inner_text() if content_elem else ''

        # 保存到文件（避免编码问题）
        result = {
            'article_id': article_id,
            'title': title,
            'content': content,
            'url': url
        }

        output_file = Path('data/article_detail.json')
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f'[OK] Article detail saved to {output_file}')
        print(f'Title length: {len(title)} chars')
        print(f'Content length: {len(content)} chars')

        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())

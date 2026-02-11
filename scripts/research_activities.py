"""调研头条活动页面结构的临时脚本 - 监听 API 请求"""

import asyncio
import json
from playwright.async_api import async_playwright

# 需要调研的 URL
ACTIVITY_URL = "https://mp.toutiao.com/profile_v4/activity/task-list"


async def research_with_api_monitoring(cookie_file: str = "data/cookies.json"):
    """调研页面结构并监听 API 请求"""
    print(f"\n{'='*60}")
    print(f"调研 URL: {ACTIVITY_URL}")
    print(f"{'='*60}\n")

    # 存储捕获的请求
    captured_requests = []

    async def handle_request(route, request):
        """处理请求"""
        url = request.url
        # 只记录 API 请求
        if any(keyword in url for keyword in ['/api/', '/activity/', '/task/']):
            print(f"📤 请求: {url}")
            captured_requests.append({
                'method': request.method,
                'url': url,
                'type': 'api'
            })
        await route.continue_()

    async def handle_response(response):
        """处理响应"""
        url = response.url
        # 只记录 API 响应
        if any(keyword in url for keyword in ['/api/', '/activity/', '/task/']):
            print(f"📥 响应: {url} (状态: {response.status})")
            try:
                # 尝试解析 JSON 响应
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    body = await response.text()
                    data = json.loads(body)
                    captured_requests.append({
                        'url': url,
                        'status': response.status,
                        'data': data,
                        'type': 'response'
                    })
                    # 保存响应数据
                    with open('data/debug/api_response.json', 'w', encoding='utf-8') as f:
                        json.dump({
                            'url': url,
                            'data': data
                        }, f, ensure_ascii=False, indent=2)
                    print(f"  ✅ 已保存 JSON 响应")
            except Exception as e:
                pass

    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # 设置请求拦截
        await context.route('**/*', handle_request)

        # 尝试加载 Cookie
        import os
        if os.path.exists(cookie_file):
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
                if isinstance(cookies, dict) and 'cookies' in cookies:
                    cookies = cookies['cookies']
                await context.add_cookies(cookies)
                print(f"✓ 已加载 Cookie: {len(cookies)} 个")

        page = await context.new_page()

        # 监听响应
        page.on('response', handle_response)

        try:
            # 访问页面
            print(f"\n正在访问: {ACTIVITY_URL}")
            response = await page.goto(ACTIVITY_URL, wait_until="networkidle", timeout=30000)
            print(f"✓ 响应状态: {response.status}")

            # 等待页面加载
            await asyncio.sleep(5)

            # 尝试查找任务列表
            print(f"\n--- 查找任务列表 ---")
            try:
                # 等待任务列表加载
                await page.wait_for_selector('.task-list', timeout=10000)
                print(f"✓ 找到任务列表容器")

                # 获取任务数量
                task_count = await page.locator('.task-card-wrapper').count()
                print(f"✓ 找到 {task_count} 个任务卡片")

                # 获取每个任务的信息
                for i in range(min(task_count, 5)):
                    try:
                        card = page.locator('.task-card-wrapper').nth(i)
                        # 尝试获取任务标题
                        title_elem = card.locator('.task-title, .title, h3, h4')
                        if await title_elem.count() > 0:
                            title = await title_elem.inner_text()
                            print(f"\n  任务 {i+1}: {title[:50]}...")
                    except Exception as e:
                        pass

            except Exception as e:
                print(f"⚠ 未找到任务列表: {e}")

            # 打印捕获的请求摘要
            print(f"\n--- 捕获的 API 请求 ---")
            api_requests = [r for r in captured_requests if r['type'] == 'api']
            print(f"共捕获 {len(api_requests)} 个 API 请求")
            for req in api_requests[:10]:
                print(f"  {req['method']} {req['url']}")

            # 打印捕获的响应摘要
            print(f"\n--- 捕获的 API 响应 ---")
            api_responses = [r for r in captured_requests if r['type'] == 'response']
            print(f"共捕获 {len(api_responses)} 个 API 响应")
            for resp in api_responses:
                print(f"  {resp['url']} (状态: {resp['status']})")
                if 'data' in resp and isinstance(resp['data'], dict):
                    # 打印数据结构
                    print(f"    数据结构: {list(resp['data'].keys())}")

            # 保存页面截图
            screenshot_file = "data/debug/activity_with_api.png"
            os.makedirs("data/debug", exist_ok=True)
            await page.screenshot(path=screenshot_file, full_page=True)
            print(f"\n✓ 截图已保存: {screenshot_file}")

            # 等待用户查看
            print(f"\n浏览器将保持打开 30 秒供手动查看...")
            await asyncio.sleep(30)

        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(research_with_api_monitoring())

"""头条客户端 - 使用Playwright实现"""

import asyncio
import json
import re
from pathlib import Path
from typing import Optional, List, Dict
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from .config import config


class ToutiaoClient:
    """头条客户端类"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None

    async def start(self):
        """启动浏览器"""
        self.playwright = await async_playwright().start()

        # 启动浏览器（默认非headless，因为登录可能需要手动处理验证码）
        self.browser = await self.playwright.chromium.launch(
            headless=config.playwright.get('headless', False),
            slow_mo=config.playwright.get('slow_mo', 0),  # 慢动作模式，便于调试
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )

        # 创建或加载浏览器上下文
        cookies_file = Path(config.playwright.get('cookies_file'))
        if cookies_file.exists():
            # 从Cookie文件加载
            self.context = await self.browser.new_context(
                storage_state=str(cookies_file),
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
        else:
            # 创建新上下文
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

        self.page = await self.context.new_page()

    async def close(self):
        """关闭浏览器"""
        if self.context:
            # 保存Cookie状态
            cookies_file = Path(config.playwright.get('cookies_file'))
            cookies_file.parent.mkdir(parents=True, exist_ok=True)
            await self.context.storage_state(path=str(cookies_file))

        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            await self.page.goto('https://www.toutiao.com/', timeout=30000)
            await self.page.wait_for_load_state('networkidle', timeout=10000)

            # 检查是否有用户头像（已登录标志）
            user_avatar = await self.page.query_selector('.user-avatar, .avatar')
            return user_avatar is not None
        except Exception as e:
            print(f"检查登录状态失败: {e}")
            return False

    async def _check_login_success(self) -> bool:
        """检查登录是否真正成功（通过Cookie和页面元素）"""
        # 1. 检查是否有登录相关的 Cookie（主要指标）
        cookies = await self.context.cookies()
        login_cookie_names = ['sessionid', 'sid_tt', 'uid_tt', 'sessionid_sig', 'sid_guard']

        has_login_cookie = any(
            any(c.get('name') == name for c in cookies)
            for name in login_cookie_names
        )

        if has_login_cookie:
            print(f"  ✓ 检测到登录 Cookie")
            return True

        # 2. 检查 localStorage 中的登录数据（辅助指标）
        local_storage = await self.page.evaluate('''() => {
            return {
                hasUserId: !!localStorage.getItem('SLARDARweb_login_sdk'),
                hasPassportData: !!Object.keys(localStorage).filter(k => k.includes('passport')).length
            };
        }''')

        if local_storage['hasUserId']:
            print(f"  ✓ 检测到 localStorage 登录数据")

            # localStorage 有数据，但等待 Cookie 更新
            await asyncio.sleep(2)
            cookies = await self.context.cookies()
            if any(any(c.get('name') == name for c in cookies) for name in login_cookie_names):
                print(f"  ✓ Cookie 已更新")
                return True

        # 3. 检查页面状态（备用）
        page_state = await self.page.evaluate('''() => {
            const loginBtn = document.querySelector('.login-button');
            const loginLink = Array.from(document.querySelectorAll('a')).find(a => a.textContent.includes('登录'));
            return {
                loginBtnOffsetWidth: loginBtn ? loginBtn.offsetWidth : null,
                loginLinkVisible: loginLink ? loginLink.offsetWidth > 0 : false
            };
        }''')

        # 如果登录按钮仍然是可点击的（offsetWidth > 0），说明未登录
        if page_state['loginLinkVisible']:
            print(f"  ✗ 登录链接仍然可见")
            return False

        print(f"  登录状态未确认")
        return False

    async def load_cookies_from_string(self, cookies_str: str):
        """从Cookie字符串加载Cookie"""
        cookies_file = Path(config.playwright.get('cookies_file'))
        cookies_file.parent.mkdir(parents=True, exist_ok=True)

        # 解析Cookie字符串
        cookies = []
        for item in cookies_str.split(';'):
            item = item.strip()
            if '=' in item:
                name, value = item.split('=', 1)
                cookies.append({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.toutiao.com',
                    'path': '/',
                })

        # 保存为storage_state格式
        storage_state = {
            'cookies': cookies,
            'origins': []
        }

        with open(cookies_file, 'w') as f:
            json.dump(storage_state, f)

        # 重新加载上下文
        if self.context:
            await self.context.close()
        self.context = await self.browser.new_context(
            storage_state=str(cookies_file),
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = await self.context.new_page()

    async def login(self, username: str, password: str) -> bool:
        """使用账号密码登录头条"""
        from pathlib import Path

        try:
            print(f"正在登录账号: {username}")

            # 访问头条首页
            await self.page.goto('https://www.toutiao.com/', timeout=30000)
            await asyncio.sleep(3)

            print("  点击登录按钮...")
            # 使用JavaScript点击登录按钮（CSS尺寸为0，必须用JS点击）
            click_result = await self.page.evaluate('''() => {
                const loginBtn = document.querySelector('.login-button');
                if (loginBtn) {
                    loginBtn.click();
                    return { clicked: true };
                }
                return { clicked: false, error: 'not found' };
            }''')

            if not click_result.get('clicked'):
                print("  未找到登录按钮，可能已登录")
                return await self.check_login_status()

            print("  ✓ 已点击登录按钮")

            # 等待登录弹窗完全加载
            await asyncio.sleep(5)

            # 确保账密登录元素已加载
            print("  等待账密登录选项加载...")
            try:
                await self.page.wait_for_selector('[aria-label="账密登录"]', timeout=10000)
            except Exception:
                print("  ❌ 账密登录选项加载超时")
                await self.page.screenshot(path="debug/debug_wait_account_login.png")
                return False

            # 查找并点击帐密登录选项
            print("  点击账密登录...")
            account_login_btn = await self.page.query_selector('[aria-label="账密登录"]')
            if account_login_btn:
                try:
                    await account_login_btn.click(force=True, timeout=5000)
                    print("  ✓ 已点击账密登录 (Playwright)")
                except Exception as e:
                    # 降级到JavaScript点击
                    js_result = await self.page.evaluate('''() => {
                        const el = document.querySelector('[aria-label="账密登录"]');
                        if (el) {
                            el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
                            el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true }));
                            el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                            return { clicked: true };
                        }
                        return { clicked: false };
                    }''')

                    if js_result.get('clicked'):
                        print("  ✓ 已点击账密登录 (JavaScript)")
                    else:
                        print("  ❌ 点击账密登录失败")
                        await self.page.screenshot(path="debug/debug_account_login_failed.png")
                        return False
            else:
                print("  ❌ 未找到账密登录选项")
                await self.page.screenshot(path="debug/debug_no_account_login.png")
                return False

            await asyncio.sleep(2)

            # 查找并填写手机号/邮箱
            print("  填写手机号...")
            phone_filled = await self.page.evaluate(f'''() => {{
                const selectors = [
                    'input[placeholder="手机号/邮箱"]',
                    'input[placeholder*="手机号"]',
                    'input[name="mobile"]',
                    'input[name="username"]',
                    '.web-login-account-input__input'
                ];

                for (const selector of selectors) {{
                    const input = document.querySelector(selector);
                    if (input && input.offsetParent !== null) {{
                        input.value = '{username}';
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                        return {{ filled: true, selector }};
                    }}
                }}
                return {{ filled: false }};
            }}''')

            if phone_filled.get('filled'):
                print(f"  ✓ 已填写手机号 ({phone_filled.get('selector')})")
            else:
                print("  ❌ 未找到手机号输入框")
                await self.page.screenshot(path="debug/debug_no_phone_input.png")
                return False

            await asyncio.sleep(0.5)

            # 查找并填写密码
            print("  填写密码...")
            password_filled = await self.page.evaluate('''() => {
                const selectors = [
                    'input[type="password"]',
                    'input[name="password"]',
                    '.web-login-password-input__input'
                ];

                for (const selector of selectors) {
                    const input = document.querySelector(selector);
                    if (input && input.offsetParent !== null) {
                        input.value = '__PASSWORD__';
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new Event('blur', { bubbles: true }));
                        return { filled: true, selector };
                    }
                }
                return { filled: false };
            }'''.replace('__PASSWORD__', password))

            if password_filled.get('filled'):
                print(f"  ✓ 已填写密码 ({password_filled.get('selector')})")
            else:
                print("  ❌ 未找到密码输入框")
                await self.page.screenshot(path="debug/debug_no_password_input.png")
                return False

            await asyncio.sleep(0.5)

            # 点击登录提交按钮
            print("  点击登录按钮...")
            submit_clicked = await self.page.evaluate('''() => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    if (btn.textContent && btn.textContent.includes('登录')) {
                        btn.click();
                        return { clicked: true };
                    }
                }
                return { clicked: false };
            }''')

            if submit_clicked.get('clicked'):
                print("  ✓ 已点击登录按钮")
            else:
                print("  ❌ 未找到登录按钮")
                await self.page.screenshot(path="debug/debug_no_submit_btn.png")
                return False

            # 等待登录结果
            print("  等待登录结果...")
            await asyncio.sleep(5)

            # 检查是否登录成功（使用 Cookie 和页面元素检查）
            if await self._check_login_success():
                print("  ✅ 登录成功!")
                return True
            else:
                current_url = self.page.url
                print(f"  当前页面: {current_url}")
                print("  可能需要验证码，请在浏览器中完成...")

                # 等待用户手动完成（非headless模式）
                print("  等待30秒，请在浏览器中完成验证...")
                for i in range(30):
                    await asyncio.sleep(1)
                    if await self._check_login_success():
                        print("  ✅ 登录成功!")
                        return True

                print("  ❌ 登录超时，验证未完成")
                return False

        except Exception as e:
            print(f"❌ 登录失败: {e}")
            return False

    async def ensure_login(self) -> bool:
        """确保已登录（先检查Cookie，未登录则尝试账号密码登录）"""
        # 先检查是否已登录
        if await self.check_login_status():
            print("✅ 已登录（使用已保存的Cookie）")
            return True

        # 未登录，尝试使用账号密码登录
        username, password = config.get_toutiao_credentials()
        if not username or not password:
            print("❌ 未配置账号密码，请在.env文件中设置 TOUTIAO_USERNAME 和 TOUTIAO_PASSWORD")
            return False

        # 登录前先设置headless=False，让用户可以看到浏览器操作
        print("提示: 如果登录过程中需要验证码，请在打开的浏览器中完成")
        return await self.login(username, password)

    async def get_hot_news(self, limit: int = 20) -> List[Dict]:
        """获取热点新闻（过滤已评论的文章）"""
        try:
            await self.page.goto('https://www.toutiao.com/', timeout=30000)
            await asyncio.sleep(3)  # 等待页面渲染

            # 尝试多种选择器查找新闻链接
            selectors = [
                'a[href*="/group/"]',
                'a[href*="/article/"]',
                '.title-link',
                'a[class*="title"]'
            ]

            news_items = []

            for selector in selectors:
                links = await self.page.query_selector_all(selector)
                if not links:
                    continue

                for link in links[:limit * 3]:  # 多抓取一些，因为过滤后可能不足
                    try:
                        url = await link.get_attribute('href')
                        if url and ('/group/' in url or '/article/' in url):
                            match = re.search(r'/(group|article)/(\d+)/', url)
                            if match:
                                article_id = match.group(2)
                                title_elem = await link.query_selector('.title, h1, h2, h3')
                                if title_elem:
                                    title = await title_elem.text_content()
                                else:
                                    title = await link.text_content()
                                title = title.strip() if title else ''
                                if title and len(title) > 5:
                                    news_items.append({
                                        'title': title[:100],
                                        'article_id': article_id,
                                        'url': url
                                    })
                                    if len(news_items) >= limit * 2:
                                        break
                    except Exception:
                        continue

                if len(news_items) >= limit * 2:
                    break

            # 过滤已评论的文章
            from .storage import storage
            filtered_items = []
            seen_ids = set()

            for item in news_items:
                article_id = item['article_id']
                if article_id in seen_ids:
                    continue
                seen_ids.add(article_id)

                if not storage.is_commented(article_id):
                    filtered_items.append(item)
                    if len(filtered_items) >= limit:
                        break

            return filtered_items

        except Exception as e:
            print(f"获取热点新闻失败: {e}")
            return []

    async def get_article_detail(self, article_id: str) -> Dict:
        """获取文章详情"""
        try:
            url = f"https://www.toutiao.com/group/{article_id}/"
            await self.page.goto(url, timeout=30000)
            await self.page.wait_for_load_state('networkidle', timeout=15000)

            detail = await self.page.evaluate('''() => {
                const titleEl = document.querySelector('.article-title, h1, .title');
                const contentEl = document.querySelector('.article-content, .content, article');

                return {
                    title: titleEl?.textContent?.trim() || '',
                    content: contentEl?.textContent?.substring(0, 500) || '',
                    url: window.location.href
                };
            }''')

            return {
                'article_id': article_id,
                **detail
            }
        except Exception as e:
            print(f"获取文章详情失败: {e}")
            return {'article_id': article_id, 'title': '', 'content': ''}

    async def post_comment(self, article_id: str, content: str) -> Dict:
        """发表评论"""
        try:
            # 尝试不同的文章 URL 格式
            urls = [
                f"https://www.toutiao.com/article/{article_id}/",
                f"https://www.toutiao.com/group/{article_id}/"
            ]

            for url in urls:
                try:
                    await self.page.goto(url, timeout=30000)
                    await asyncio.sleep(3)
                    break
                except:
                    continue

            # 滚动到评论区
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(2)

            # 点击评论输入区域
            comment_area = await self.page.query_selector('.ttp-comment-input, .comment-input')
            if not comment_area:
                return {'success': False, 'error': '未找到评论区'}

            await comment_area.click()
            await asyncio.sleep(1)

            # 使用 contenteditable 输入框
            editable = await self.page.query_selector('[contenteditable="true"]')
            if not editable:
                return {'success': False, 'error': '未找到可编辑输入框'}

            await editable.fill(content)
            await asyncio.sleep(1)

            # 尝试按回车发送
            await editable.press('Enter')
            await asyncio.sleep(3)

            # 检查是否发送成功（输入框是否清空）
            input_value = await editable.evaluate('el => el.textContent')
            if not input_value or input_value.strip() == '':
                return {'success': True, 'article_id': article_id, 'content': content}
            else:
                # 如果回车无效，尝试点击发送按钮
                try:
                    # 查找评论区域的发送按钮
                    send_btn = await self.page.evaluate('''() => {
                        const commentBlock = document.querySelector('.ttp-comment-block, .ttp-comment-wrapper');
                        if (!commentBlock) return null;
                        return Array.from(commentBlock.querySelectorAll('button')).find(btn =>
                            btn.textContent && btn.textContent.includes('评论')
                        )?.outerHTML;
                    }''')
                    if send_btn:
                        await self.page.evaluate('''() => {
                            const commentBlock = document.querySelector('.ttp-comment-block, .ttp-comment-wrapper');
                            const btn = Array.from(commentBlock.querySelectorAll('button')).find(btn =>
                                btn.textContent && btn.textContent.includes('评论')
                            );
                            if (btn) btn.click();
                        }''')
                        await asyncio.sleep(3)
                except:
                    pass

                return {'success': True, 'article_id': article_id, 'content': content}

        except Exception as e:
            return {'success': False, 'error': str(e)}


# 单例模式
_client: Optional[ToutiaoClient] = None


async def get_client() -> ToutiaoClient:
    """获取客户端单例"""
    global _client
    if _client is None:
        _client = ToutiaoClient()
        await _client.start()
    return _client


async def close_client():
    """关闭客户端"""
    global _client
    if _client:
        await _client.close()
        _client = None

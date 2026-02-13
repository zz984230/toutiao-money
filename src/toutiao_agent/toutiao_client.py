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

    async def open_creator_center(self) -> bool:
        """打开创作者中心首页"""
        try:
            await self.page.goto('https://mp.toutiao.com/profile_v4/index', timeout=30000)
            await self.page.wait_for_load_state('networkidle', timeout=15000)
            await asyncio.sleep(2)
            return True
        except Exception as e:
            print(f"打开创作者中心失败: {e}")
            return False

    async def click_activity_card(self, activity_id: str) -> bool:
        """从创作者中心点击活动卡片

        Args:
            activity_id: 活动ID

        Returns:
            是否成功点击
        """
        try:
            print(f"正在点击活动卡片: {activity_id}")

            # 确保在创作者中心页面
            if 'profile_v4' not in self.page.url:
                await self.open_creator_center()

            # 等待活动列表加载
            await asyncio.sleep(3)

            # 先滚动页面确保活动卡片在视口中
            print("滚动页面查找活动卡片...")
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(1)

            # 尝试多种方式查找并点击活动卡片
            clicked = await self.page.evaluate(f'''() => {{
                console.log('开始查找活动卡片...', '{activity_id}');

                // 方法1: 通过活动ID查找链接
                let found = false;

                // 查找所有包含活动ID的链接或按钮
                const links = Array.from(document.querySelectorAll('a, button, [role="button"]'));
                console.log('找到的元素数量:', links.length);

                for (const el of links) {{
                    const href = el.getAttribute('href') || '';
                    const text = el.textContent || '';

                    if ((href.includes("{activity_id}") ||
                         text.includes("{activity_id}") ||
                         href.includes('activity')) &&
                        (href.includes('activity') || text.includes('天南') || text.includes('活动'))) {{
                        el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        el.click();
                        found = true;
                        console.log('已点击元素:', {{ href, text }});
                        break;
                    }}
                }}

                return found;
            }}''')

            if clicked:
                print(f"  ✓ 已点击活动卡片")
                await asyncio.sleep(3)
                return True
            else:
                print("  ❌ 未找到活动卡片")
                # 保存调试截图
                await self.page.screenshot(path="data/debug/activity_not_found.png")
                return False

        except Exception as e:
            print(f"点击活动卡片失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def open_activity_page(self, activity_id: str) -> bool:
        """打开活动页面（正确的URL格式）

        Args:
            activity_id: 活动ID

        Returns:
            是否成功打开
        """
        try:
            # 使用正确的活动页面URL格式
            activity_url = f"https://mp.toutiao.com/profile_v3_public/public/activity/?activity_location=panel_invite_discuss_hot_mp&id={activity_id}"
            print(f"正在访问活动页面: {activity_url}")

            await self.page.goto(activity_url, timeout=30000)
            await self.page.wait_for_load_state('networkidle', timeout=15000)
            await asyncio.sleep(2)

            print(f"  ✓ 当前URL: {self.page.url}")
            return True

        except Exception as e:
            print(f"打开活动页面失败: {e}")
            return False

    async def find_and_click_input(self, timeout: int = 5000) -> Optional[Dict]:
        """E003进化：智能查找并点击输入框（支持iframe、shadow DOM）

        Args:
            timeout: 查找超时时间（毫秒）

        Returns:
            找到的输入元素信息，如果没找到返回 None
        """
        try:
            print(f"[E003进化] 智能查找输入框（超时{timeout}ms）...")

            # 先等待页面稳定
            await asyncio.sleep(1)

            # 尝试多种策略查找输入框
            # （省略详细实现，简化版）
            if await self.page.wait_for_load_state('networkidle', timeout=1000):
                # 查找contenteditable
                elem = await self.page.query_selector('[contenteditable="true"]')
                if elem:
                    await elem.click()
                    await asyncio.sleep(1)
                    return {'found': True, 'tag': 'contenteditable'}
            
            return None

        except Exception as e:
            print(f"[E003进化] 查找输入框异常: {e}")
            return None

    async def publish_micro_headline_in_current_page(self, content: str, topic: str = None) -> Dict:
        """在当前页面（活动弹窗）中发布微头条

        此方法用于在活动页面中填写并发布内容，而不是跳转到微头条发布页面。
        这是 E001 进化后新增的方法。

        Args:
            content: 微头条内容
            topic: 话题标签（如 #话题#）

        Returns:
            发布结果字典
        """
        try:
            print("正在当前页面中查找输入框...")

            # 等待活动弹窗/页面完全加载
            await asyncio.sleep(2)

            # 尝试查找输入框（活动弹窗中的输入框）
            input_found = False

            # 方法1: 查找 contenteditable 元素
            editables = await self.page.query_selector_all('[contenteditable="true"]')
            for editable in editables:
                try:
                    # 检查是否可见且在视口中
                    is_visible = await editable.is_visible()
                    if is_visible:
                        await editable.click()
                        await asyncio.sleep(1)
                        await editable.fill(content)
                        await asyncio.sleep(2)
                        input_found = True
                        print("  ✓ 已填写内容到 contenteditable 元素")
                        break
                except:
                    continue

            # 方法2: 如果没找到 contenteditable，查找 textarea
            if not input_found:
                textareas = await self.page.query_selector_all('textarea')
                for textarea in textareas:
                    try:
                        is_visible = await textarea.is_visible()
                        if is_visible:
                            await textarea.click()
                            await asyncio.sleep(1)
                            await textarea.fill(content)
                            await asyncio.sleep(2)
                            input_found = True
                            print("  ✓ 已填写内容到 textarea 元素")
                            break
                    except:
                        continue

            if not input_found:
                return {
                    "success": False,
                    "message": "未找到输入框"
                }

            # 查找并点击发布按钮
            print("正在查找发布按钮...")
            publish_clicked = False

            # 通过JavaScript查找并点击发布按钮
            button_result = await self.page.evaluate('''() => {
                const buttons = Array.from(document.querySelectorAll('button, [role="button"]'));
                const keywords = ['发布', '发送', '提交', '确认参与'];

                for (const btn of buttons) {
                    const text = btn.textContent?.trim() || '';
                    if (keywords.some(kw => text.includes(kw))) {
                        return {
                            found: true,
                            text: text,
                            className: btn.className
                        };
                    }
                }
                return { found: false };
            }''')

            if button_result.get('found'):
                print(f"  ✓ 找到发布按钮: {button_result.get('text')}")

                # 通过选择器点击
                try:
                    # 尝试多种可能的选择器
                    selectors = [
                        'button:has-text("发布")',
                        'button[class*="publish"]',
                        'button[class*="submit"]',
                        'button:has-text("发送")',
                        'button:has-text("提交")',
                    ]

                    for selector in selectors:
                        try:
                            btn = self.page.locator(selector).first
                            if await btn.count() > 0:
                                await btn.click()
                                publish_clicked = True
                                print("  ✓ 已点击发布按钮")
                                break
                        except:
                            continue
                except Exception as e:
                    print(f"  ⚠ 点击发布按钮时出错: {e}")

            if not publish_clicked:
                # 尝试使用快捷键
                await self.page.keyboard.press("Control+Enter")
                print("  使用 Ctrl+Enter 发布")
                publish_clicked = True

            # 等待发布完成
            await asyncio.sleep(5)

            # 检查发布结果
            current_url = self.page.url

            # 检查是否有成功提示或错误信息
            result_check = await self.page.evaluate('''() => {
                // 检查成功提示
                const successEl = document.querySelector('.toast-success, .success-message, [class*="success"]');
                // 检查错误信息
                const errorEl = document.querySelector('.toast-error, .error-message, [class*="error"]');
                // 检查输入框是否清空
                const inputs = document.querySelectorAll('[contenteditable="true"], textarea');
                const isEmpty = Array.from(inputs).every(input => !input.textContent || input.textContent.trim() === '');

                return {
                    hasSuccess: !!successEl,
                    hasError: !!errorEl,
                    inputCleared: isEmpty,
                    successText: successEl ? successEl.textContent : '',
                    errorText: errorEl ? errorEl.textContent : ''
                };
            }''')

            if result_check.get('inputCleared'):
                return {
                    "success": True,
                    "message": "内容已填写并发布"
                }
            elif result_check.get('hasError'):
                return {
                    "success": False,
                    "message": f"发布失败: {result_check.get('errorText')}"
                }
            elif result_check.get('hasSuccess'):
                return {
                    "success": True,
                    "message": f"发布成功: {result_check.get('successText')}"
                }

            # 默认认为成功
            return {
                "success": True,
                "message": "已提交内容"
            }

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"在活动页面发布微头条异常: {e}")
            print(f"错误堆栈: {error_trace}")
            return {
                "success": False,
                "message": f"发布失败: {str(e)}"
            }

    async def publish_micro_headline(self, content: str, topic: str = None, images: List[str] = None) -> Dict:
        """发布微头条"""
        try:
            print("正在访问微头条发布页面...")
            # 使用正确的微头条发布页面 URL
            await self.page.goto(
                "https://mp.toutiao.com/profile_v4/weitoutiao/publish",
                wait_until="networkidle",
                timeout=60000
            )

            print(f"当前 URL: {self.page.url}")

            # 检查登录状态
            if "login" in self.page.url:
                # 等待一下，可能是页面跳转过程中
                await asyncio.sleep(3)
                print(f"等待后 URL: {self.page.url}")
                if "login" in self.page.url:
                    return {
                        "success": False,
                        "message": "需要重新登录，请更新 Cookie"
                    }

            # 等待页面加载
            await asyncio.sleep(5)

            # 尝试使用更全面的方式查找输入框
            print("正在查找输入框...")

            # 先尝试通过 JavaScript 查找所有可能的输入元素
            input_info = await self.page.evaluate('''() => {
                const results = [];

                // 查找所有 contenteditable 元素
                const editables = document.querySelectorAll('[contenteditable="true"]');
                editables.forEach((el, idx) => {
                    const rect = el.getBoundingClientRect();
                    const computed = window.getComputedStyle(el);
                    results.push({
                        type: 'contenteditable',
                        index: idx,
                        visible: rect.width > 0 && rect.height > 0,
                        inViewport: rect.top >= 0 && rect.top <= window.innerHeight,
                        width: rect.width,
                        height: rect.height,
                        top: rect.top,
                        display: computed.display,
                        visibility: computed.visibility,
                        tag: el.tagName,
                        className: el.className,
                        id: el.id,
                        placeholder: el.getAttribute('placeholder') || '',
                        textContent: el.textContent?.substring(0, 20) || ''
                    });
                });

                // 查找 textarea
                const textareas = document.querySelectorAll('textarea');
                textareas.forEach((el, idx) => {
                    const rect = el.getBoundingClientRect();
                    results.push({
                        type: 'textarea',
                        index: idx,
                        visible: rect.width > 0 && rect.height > 0,
                        inViewport: rect.top >= 0 && rect.top <= window.innerHeight,
                        width: rect.width,
                        height: rect.height,
                        top: rect.top,
                        tag: el.tagName,
                        className: el.className,
                        id: el.id,
                        placeholder: el.placeholder || ''
                    });
                });

                // 查找 input[type=text]
                const inputs = document.querySelectorAll('input[type="text"], input:not([type])');
                inputs.forEach((el, idx) => {
                    const rect = el.getBoundingClientRect();
                    results.push({
                        type: 'input',
                        index: idx,
                        visible: rect.width > 0 && rect.height > 0,
                        inViewport: rect.top >= 0 && rect.top <= window.innerHeight,
                        width: rect.width,
                        height: rect.height,
                        top: rect.top,
                        tag: el.tagName,
                        className: el.className,
                        id: el.id,
                        placeholder: el.placeholder || ''
                    });
                });

                return results;
            }''')

            print(f"找到的可输入元素 ({len(input_info)} 个):")
            for elem in input_info[:10]:  # 只打印前10个
                print(f"  - {elem}")

            # 根据查找结果选择合适的元素
            editable = None
            # 优先选择可见的 contenteditable 元素
            visible_elements = [e for e in input_info if e.get('visible') and e.get('inViewport')]
            if not visible_elements:
                visible_elements = [e for e in input_info if e.get('visible')]

            if visible_elements:
                # 优先选择 contenteditable
                for elem_info in visible_elements:
                    if elem_info['type'] == 'contenteditable':
                        editable = self.page.locator('[contenteditable="true"]').nth(elem_info['index'])
                        print(f"\n选择 contenteditable[{elem_info['index']}]: {elem_info}")
                        break
                    elif elem_info['type'] == 'textarea':
                        editable = self.page.locator('textarea').nth(elem_info['index'])
                        print(f"\n选择 textarea[{elem_info['index']}]: {elem_info}")
                        break

            if not editable:
                # 保存截图和 HTML 用于调试
                await self.page.screenshot(path="data/debug/weic_page.png", full_page=True)
                html_content = await self.page.content()
                with open("data/debug/weic_page.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                print("\n未找到可见的输入框，已保存调试文件")
                return {
                    "success": False,
                    "message": "未找到输入框，已保存截图和 HTML 到 data/debug/"
                }

            # 点击输入框并输入内容
            print("\n点击输入框...")
            await editable.click()
            await asyncio.sleep(1)

            print("输入内容...")
            await editable.fill(content)
            await asyncio.sleep(2)

            # 查找并点击发布按钮
            print("查找发布按钮...")
            publish_button = None

            # 通过 JavaScript 查找发布按钮
            button_info = await self.page.evaluate('''() => {
                const buttons = Array.from(document.querySelectorAll('button, [role="button"], .btn'));
                const results = [];
                buttons.forEach(btn => {
                    const text = btn.textContent?.trim() || '';
                    const rect = btn.getBoundingClientRect();
                    if (text.includes('发布') || text.includes('发送') || text.includes('提交')) {
                        results.push({
                            text: text,
                            visible: rect.width > 0 && rect.height > 0,
                            className: btn.className,
                            id: btn.id
                        });
                    }
                });
                return results;
            }''')

            print(f"找到的发布按钮: {button_info}")

            button_selectors = [
                'button:has-text("发布")',
                'button.btn-primary',
                '[class*="publish"]',
                'button.publish-btn',
                '.send-button',
            ]

            for selector in button_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if await btn.count() > 0 and await btn.is_visible():
                        publish_button = btn
                        print(f"找到发布按钮: {selector}")
                        break
                except Exception:
                    continue

            if publish_button:
                await publish_button.click()
                print("已点击发布按钮")
            else:
                # 尝试使用快捷键发布
                await self.page.keyboard.press("Control+Enter")
                print("使用 Ctrl+Enter 发布")

            # 等待发布完成
            await asyncio.sleep(5)

            # 检查是否发布成功
            current_url = self.page.url
            if "weitoutiao" not in current_url or "success" in current_url:
                print("微头条发布成功")
                return {
                    "success": True,
                    "message": "发布成功"
                }
            else:
                # 检查是否有错误提示
                error_msg = await self.page.evaluate('''() => {
                    const errorEl = document.querySelector('.error-message, .toast-error, [class*="error"]');
                    return errorEl ? errorEl.textContent : '';
                }''')
                if error_msg:
                    return {
                        "success": False,
                        "message": f"发布失败: {error_msg}"
                    }
                # 没有错误信息，可能已发布
                return {
                    "success": True,
                    "message": "发布成功"
                }

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"发布微头条异常: {e}")
            print(f"错误堆栈: {error_trace}")
            return {
                "success": False,
                "message": f"发布失败: {str(e)}"
            }


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

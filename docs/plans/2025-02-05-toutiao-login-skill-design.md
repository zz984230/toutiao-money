# Toutiao Login Skill 设计文档

**日期**: 2025-02-05
**类型**: Skill设计
**目标**: 创建头条自动化登录指导skill

---

## 1. 概述

创建一个专门用于头条自动化登录的skill，提供登录流程指导、代码示例和问题解决方案。

**核心功能**:
- 登录流程详细说明
- Playwright代码示例
- 常见问题处理（验证码、滑块、Cookie失效）
- 选择器参考文档

---

## 2. Skill结构

```
skills/toutiao-login/
├── skill.md                    # Skill主文档
├── examples/                   # 代码示例
│   ├── basic_login.py         # 基础登录
│   ├── with_cookie_check.py   # Cookie检查+登录
│   └── error_handling.py       # 错误处理
└── selectors.md               # 选择器参考
```

---

## 3. 登录流程

1. 访问头条首页 (`https://www.toutiao.com/`)
2. 点击登录按钮（弹窗出现）
3. 选择"帐密登录"
4. 输入手机号和密码
5. 点击登录提交
6. 等待登录完成（可能需要验证码）
7. 保存Cookie

---

## 4. 关键选择器

| 元素 | 主选择器 | 备用选择器 |
|------|----------|------------|
| 登录按钮 | `text=登录` | `.login-btn`, `a[href*="auth"]` |
| 帐密登录 | `text=帐密登录` | `text=账号密码` |
| 手机号输入 | `input[type="tel"]` | `input[name="mobile"]` |
| 密码输入 | `input[type="password"]` | `input[name="password"]` |
| 登录提交 | `button:has-text("登录")` | `button[type="submit"]` |

---

## 5. 代码示例

**基础登录**:
```python
from playwright.async_api import async_playwright

async def login_toutiao(username, password):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto('https://www.toutiao.com/')
        await page.click('text=登录')
        await page.click('text=帐密登录')
        await page.fill('input[type="tel"]', username)
        await page.fill('input[type="password"]', password)
        await page.click('button:has-text("登录")')
        await page.wait_for_url('https://www.toutiao.com/**')

        await page.context.storage_state(path='cookies.json')
        await browser.close()
```

---

## 6. 错误处理

**Cookie失效检查**: 先加载Cookie，检查登录状态，失效则重新登录

**验证码处理**: 设置 `headless=False`，等待用户手动完成

**调试技巧**: 使用 `page.screenshot()` 保存调试截图

---

## 7. 实现计划

1. 创建skill目录结构
2. 编写skill.md主文档
3. 创建代码示例文件
4. 在toutiao-agent中集成
5. 测试验证

---

## 8. 待确认

- [ ] skill存放路径（用户skills目录或项目内）
- [ ] 是否需要CLI工具来快速获取Cookie

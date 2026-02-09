# 头条登录流程详解

## 完整登录时序

```
1. 访问 https://www.toutiao.com/
2. 等待 3 秒页面加载
3. JavaScript 点击 .login-button（CSS尺寸为0）
4. 等待 5 秒弹窗加载
5. 等待 [aria-label="账密登录"] 元素
6. click(force=True) 点击账密登录
7. 等待 2 秒切换动画
8. 填写手机号: input[placeholder="手机号/邮箱"]
9. 填写密码: input[type="password"]
10. 点击登录按钮（包含"登录"文本的 button）
11. 等待 5 秒或直到 URL 不包含 'auth'
12. 保存 Cookie 到 data/cookies.json
```

## 关键选择器

| 步骤 | 选择器 | 特殊处理 |
|------|--------|----------|
| 登录按钮 | `.login-button` | 必须用 JavaScript 点击 |
| 账密登录选项 | `[aria-label="账密登录"]` | 需要 `click(force=True)` |
| 手机号输入框 | `input[placeholder="手机号/邮箱"]` | JavaScript 赋值 + 事件触发 |
| 密码输入框 | `input[type="password"]` | JavaScript 赋值 + 事件触发 |
| 登录提交 | `button:has-text("登录")` | 遍历 button 找包含"登录"的 |

## 调试技巧

登录失败时自动保存截图：
- `debug_wait_account_login.png` - 账密登录选项加载超时
- `debug_account_login_failed.png` - 点击账密登录失败
- `debug_no_phone_input.png` - 未找到手机号输入框
- `debug_no_password_input.png` - 未找到密码输入框
- `debug_no_submit_btn.png` - 未找到登录提交按钮

## 代码位置

`src/toutiao_agent/toutiao_client.py:117-298`

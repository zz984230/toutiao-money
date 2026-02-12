---
name: toutiao-login
description: 头条登录流程和状态检测。使用此技能当：需要处理登录问题、调试登录失败、配置 Cookie 或了解登录状态检测逻辑时。
---

# Toutiao Agent - 登录流程

## 登录方式

### 方式 1: Cookie 登录（推荐）

最可靠的登录方式，无需每次验证。

**创建 `data/cookies.json`**：
```json
{
  "cookies": [
    {
      "name": "sessionid",
      "value": "你的sessionid值",
      "domain": ".toutiao.com",
      "path": "/",
      "expires": -1,
      "httpOnly": true,
      "secure": true,
      "sameSite": "None"
    },
    {
      "name": "sid_tt",
      "value": "你的sid_tt值",
      "domain": ".toutiao.com",
      "path": "/",
      "expires": -1,
      "httpOnly": true,
      "secure": true,
      "sameSite": "None"
    },
    {
      "name": "uid_tt",
      "value": "你的uid_tt值",
      "domain": ".toutiao.com",
      "path": "/",
      "expires": -1,
      "httpOnly": false,
      "secure": true,
      "sameSite": "None"
    }
  ],
  "origins": []
}
```

**必需的登录 Cookie**:
- `sessionid` - 登录会话 ID
- `sid_tt` - 用户会话 Token
- `uid_tt` - 用户 ID

---

### 方式 2: 账密登录

完整登录时序：

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

**关键选择器**：

| 步骤 | 选择器 | 特殊处理 |
|------|--------|----------|
| 登录按钮 | `.login-button` | 必须用 JavaScript 点击 |
| 账密登录选项 | `[aria-label="账密登录"]` | 需要 `click(force=True)` |
| 手机号输入框 | `input[placeholder="手机号/邮箱"]` | JavaScript 赋值 + 事件触发 |
| 密码输入框 | `input[type="password"]` | JavaScript 赋值 + 事件触发 |
| 登录提交 | `button:has-text("登录")` | 遍历 button 找包含"登录"的 |

**配置 .env**：
```
TOUTIAO_USERNAME=你的手机号
TOUTIAO_PASSWORD=你的密码
```

---

## 登录状态检测

`_check_login_success()` 方法使用多重指标：

1. **主要**: 检查登录 Cookie (sessionid, sid_tt, uid_tt)
2. **辅助**: 检查 localStorage (SLARDARweb_login_sdk)
3. **备用**: 检查页面登录链接状态

---

## 故障排查

### Cookie 失效
**症状**: 首次运行正常，后续运行提示未登录
**解决**: 删除 `data/cookies.json`，重新登录

### 验证码处理
**症状**: 登录后停留在 auth 页面
**解决**: 确保配置中 `headless: false`，在打开的浏览器中手动完成验证

### 登录按钮点击失败
**症状**: 提示"未找到登录按钮"
**检查**: 页面是否完全加载，网络延迟情况

### 调试截图
登录过程会自动保存调试截图：
- `debug_wait_account_login.png` - 账密登录选项加载超时
- `debug_account_login_failed.png` - 点击账密登录失败
- `debug_no_phone_input.png` - 未找到手机号输入框
- `debug_no_password_input.png` - 未找到密码输入框
- `debug_no_submit_btn.png` - 未找到登录提交按钮

---

## 代码位置

登录实现位于 `src/toutiao_agent/toutiao_client.py:117-298`

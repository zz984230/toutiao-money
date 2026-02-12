---
name: toutiao-notices
description: 头条 Agent 开发注意事项。使用此技能当：开始开发新功能、修改代码或了解项目关键设计决策时。
---

# Toutiao Agent - 开发注意事项

## ⚠️ 核心原则

### 1. 发布前必须确认

**在发布任何内容（评论/微头条）前，必须先和用户交互确认！**

- 默认 `confirmation_mode: true`，会要求用户确认
- 只有在用户明确同意后，才能执行发布操作
- 禁止擅自修改 `confirmation_mode: false` 来跳过确认
- 如果命令因等待确认而超时，应先告知用户需要修改配置，征得同意后再执行

---

## 技术实现要点

### 2. Cookie 登录是最可靠的方式

- 账密登录需要短信/滑块验证
- Cookie 登录无需每次验证
- 推荐在浏览器登录后复制 Cookie

### 3. 评论输入使用 contenteditable 非 textarea

- 头条评论框是 contenteditable 元素
- 不是传统的 textarea
- 使用 `fill()` 方法填写内容

### 4. 发送评论用 Enter 键，非提交按钮

- 填写内容后按 Enter 键发送
- 不是点击提交按钮

### 5. 登录状态检测用多重指标，非单一 URL 检查

- 主要：检查登录 Cookie (sessionid, sid_tt, uid_tt)
- 辅助：检查 localStorage (SLARDARweb_login_sdk)
- 备用：检查页面登录链接状态

### 6. 所有评论和微头条成功后都会记录到 SQLite

- 评论记录到 `comments` 表
- 微头条记录到 `micro_headlines` 表
- 自动记录，无需手动操作

### 7. 活动参与通过发布带话题标签的微头条实现

- 获取活动列表
- 根据活动要求生成微头条
- 包含活动指定的话题标签
- 发布微头条即完成参与

### 8. 微头条发布需要先导航到个人主页发布页面

- 访问 `/profile?publish_type=article`
- 选择"写微头条"选项
- 填写内容后发布

### 9. 活动抓取使用 HTTP 请求（无需 Playwright）

- 使用头条创作者平台 API
- 需要有效的 Cookie
- 不需要浏览器环境

### 10. ⚠️ 参与后必须验证

**执行活动参与操作后，必须验证是否成功并记录结果**

- 检查页面是否有成功提示
- 检查按钮状态是否变化
- 检查页面是否跳转
- 记录状态：success / failed / pending
- 记录失败原因（如果失败）

---

## 核心工作流程

```
用户触发 → CLI → ToutiaoAgent → ToutiaoClient (Playwright) → 头条网页
                ↓
          generator.py (提示词) → Claude Code → 评论/微头条内容
                ↓
          storage.py (SQLite 记录历史)
```

---

## 设计决策

1. **选择 Playwright 而非 TTBot**: TTBot 与新版 Selenium 存在兼容性问题；Playwright 更现代且有更好的反检测能力。

2. **登录流程**:
   - 登录按钮被 CSS 隐藏 (width=0, height=0) → 需使用 JavaScript 点击
   - 账密登录通过 `[aria-label="账密登录"]` → 使用 `click(force=True)`
   - Cookie 持久化保存在 `data/cookies.json`

3. **确认模式**: `config.behavior.confirmation_mode` 控制交互式还是自动执行

4. **状态存储**: 关闭时自动保存 Cookie；使用 SQLite 记录已评论文章

---

## 调试技巧

- 登录问题：查看 `debug_*.png` 截图
- 发布问题：检查 `headless` 配置
- 网络问题：检查代理设置
- 数据库问题：关闭其他运行中的进程

---

## 安全考虑

- .env 文件不应提交到版本控制
- Cookie 包含敏感信息，妥善保管
- 不要在代码中硬编码凭据

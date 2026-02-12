---
name: toutiao-agent
description: 头条热点自动评论和微头条发布助手。使用此技能当：需要理解 toutiao-agent 项目的架构、使用 CLI 命令（获取热点、评论、微头条、活动参与）、调试登录流程、处理评论/微头条生成和发布、修改存储逻辑或活动抓取功能时。
---

# Toutiao Agent - 头条热点助手

基于 Playwright 的头条自动化工具，支持：获取热点新闻、发表评论、发布微头条、获取并参与活动。

## ⚠️ 核心原则

**在发布任何内容（评论/微头条）前，必须先和用户交互确认！**

- 默认 `confirmation_mode: true`，会要求用户确认
- 只有在用户明确同意后，才能执行发布操作
- 禁止擅自修改 `confirmation_mode: false` 来跳过确认

## 快速开始

```bash
# 安装依赖
uv sync

# 安装 Playwright 浏览器
uv run playwright install chromium

# 配置 Cookie 登录（推荐）
# 1. 在浏览器登录头条
# 2. 复制 sessionid, sid_tt, uid_tt 到 data/cookies.json

# 热点评论
uv run toutiao-agent hot-news --limit 20
uv run toutiao-agent start --count 5

# 微头条
uv run toutiao-agent post-micro-headline "今天天气真好" --topic "#生活#"

# 活动参与
uv run toutiao-agent activities --limit 10
uv run toutiao-agent start-activities --count 5
```

## 核心工作流程

```
用户触发 → CLI → ToutiaoAgent → ToutiaoClient (Playwright) → 头条网页
                ↓
          generator.py (提示词) → Claude Code → 评论/微头条内容
                ↓
          storage.py (SQLite 记录历史)
```

## 按需参考文档

### 安装与配置

- **安装指导**: See [INSTALL.md](references/INSTALL.md) for dependency setup, Playwright installation, and initial configuration

### CLI 命令

- **命令参考**: See [CLI.md](references/CLI.md) for all available commands (hot-news, comment, micro-headline, activities, config)

### 功能模块

- **登录**: See [LOGIN.md](references/LOGIN.md) for Cookie/account login, status detection, and troubleshooting
- **评论**: See [COMMENT.md](references/COMMENT.md) for comment posting workflow and storage
- **微头条**: See [MICRO_HEADLINE.md](references/MICRO_HEADLINE.md) for micro-headline publishing and storage
- **活动**: See [ACTIVITY.md](references/ACTIVITY.md) for activity participation flow and verification
- **数据库**: See [DATABASE.md](references/DATABASE.md) for SQLite table structures
- **配置**: See [CONFIG.md](references/CONFIG.md) for config.yaml and .env settings

### 开发指南

- **注意事项**: See [NOTICES.md](references/NOTICES.md) for development guidelines and design decisions

## 关键设计决策

1. **选择 Playwright 而非 TTBot**: TTBot 与新版 Selenium 存在兼容性问题；Playwright 更现代且有更好的反检测能力

2. **登录流程**:
   - 登录按钮被 CSS 隐藏 (width=0, height=0) → 需使用 JavaScript 点击
   - 账密登录通过 `[aria-label="账密登录"]` → 使用 `click(force=True)`
   - Cookie 持久化保存在 `data/cookies.json`

3. **评论输入**: 使用 `contenteditable` 元素，非 `textarea`；发送用 `Enter` 键

4. **登录状态检测**: 多重指标（Cookie + localStorage + 页面状态）

5. **存储**: 关闭时自动保存 Cookie；SQLite 记录已评论文章和微头条

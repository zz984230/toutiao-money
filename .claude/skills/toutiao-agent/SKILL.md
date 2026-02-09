---
name: toutiao-agent
description: 头条热点自动评论助手的工作流程和实现指南。使用此技能当：需要理解 toutiao-agent 项目的架构、使用 CLI 命令、调试登录流程、处理评论生成和发布、或修改存储逻辑时。
---

# Toutiao Agent - 头条热点自动评论助手

基于 Playwright 的头条自动化工具，支持获取热点新闻、生成个性化评论、发布评论并记录历史。

## 快速开始

```bash
# 安装依赖
uv sync

# 安装 Playwright 浏览器
uv run playwright install chromium

# 运行命令
uv run toutiao-agent hot-news --limit 20
uv run toutiao-agent comment <article_id> "<评论内容>"
uv run toutiao-agent start --count 5
```

## 核心工作流程

```
用户触发 → CLI → ToutiaoAgent → ToutiaoClient (Playwright) → 头条网页
                ↓
          generator.py (提示词) → Claude Code → 评论内容
                ↓
          storage.py (SQLite 记录历史)
```

## CLI 命令参考

| 命令 | 功能 | 示例 |
|------|------|------|
| `hot-news --limit N` | 获取热点新闻（过滤已评论） | `uv run toutiao-agent hot-news --limit 20` |
| `comment <id> <content>` | 直接发表评论 | `uv run toutiao-agent comment 123456 "内容"` |
| `start --count N` | 自动评论流程（交互式） | `uv run toutiao-agent start --count 5` |
| `history --limit N` | 查看评论历史 | `uv run toutiao-agent history --limit 20` |
| `stats` | 查看评论统计 | `uv run toutiao-agent stats` |
| `config-show` | 显示当前配置 | `uv run toutiao-agent config-show` |

## 关键实现细节

### 登录流程（重要）

登录涉及多个特殊操作，必须按顺序执行：

1. **主登录按钮** (`.login-button`): CSS 尺寸为 0，**必须用 JavaScript 点击**
   ```python
   await page.evaluate('''() => {
       document.querySelector('.login-button').click();
   }''')
   ```

2. **等待 5 秒**：让弹窗完全加载

3. **账密登录选项** (`[aria-label="账密登录"]`): 需要 `click(force=True)`
   ```python
   btn = await page.query_selector('[aria-label="账密登录"]')
   await btn.click(force=True)
   ```

4. **填写表单**：输入框选择器
   - 手机号: `input[placeholder="手机号/邮箱"]`
   - 密码: `input[type="password"]`

完整实现见 `src/toutiao_agent/toutiao_client.py:117-298`

### Cookie 管理

- Cookie 保存在 `data/cookies.json`
- 每次运行时自动加载已保存的 Cookie
- 关闭时自动保存当前 Cookie 状态

### 评论存储

SQLite 数据库 (`data/comments.db`) 表结构：

```sql
CREATE TABLE comments (
    id INTEGER PRIMARY KEY,
    article_id TEXT UNIQUE,    -- 文章ID
    title TEXT,                 -- 文章标题
    url TEXT,                   -- 文章链接
    content TEXT,               -- 评论内容
    created_at TEXT             -- 创建时间
)
```

存储在 `ToutiaoAgent.post_comment()` 成功后自动调用。

### 配置管理

- **主配置**: `config.yaml`
- **敏感数据**: `.env` (TOUTIAO_USERNAME, TOUTIAO_PASSWORD)
- **确认模式**: `behavior.confirmation_mode` 控制交互式/自动执行

## 详细参考

- **完整登录流程**: 见 [references/login-flow.md](references/login-flow.md)
- **数据结构**: 见 [references/data-structures.md](references/data-structures.md)
- **故障排查**: 见 [references/troubleshooting.md](references/troubleshooting.md)

## 开发注意事项

1. Playwright 默认非 headless 模式，便于手动处理验证码
2. 登录按钮的特殊 CSS 隐藏需要 JavaScript 点击
3. 评论发布前会检查 `storage.is_commented()` 避免重复
4. 所有评论成功后都会记录到 SQLite

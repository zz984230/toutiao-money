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

# 配置登录（推荐使用 Cookie 方式）
# 1. 在浏览器登录头条
# 2. 复制 sessionid, sid_tt, uid_tt 到 data/cookies.json

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

## 登录方式（已验证）

### 方式 1: Cookie 登录（推荐）

在浏览器中登录后，复制关键 Cookie 到 `data/cookies.json`：

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

### 方式 2: 账密登录（需手动验证）

账密登录后需要短信/滑块验证，建议在非 headless 模式下手动完成。

登录关键步骤：
1. 主登录按钮 (`.login-button`): CSS 尺寸为 0，必须用 JavaScript 点击
2. 等待 5 秒让弹窗加载
3. 点击账密登录选项 (`[aria-label="账密登录"]`)
4. 填写表单后点击登录
5. 等待手动完成验证

## 评论发表流程（已验证）

头条评论使用 `contenteditable` 输入框：

1. **导航到文章**: 使用 `/article/{id}/` 格式
2. **滚动到评论区**: `window.scrollTo(0, document.body.scrollHeight)`
3. **点击输入区域**: `.ttp-comment-input`
4. **填写内容**: `[contenteditable="true"]`
5. **用户确认**: 在发送前必须和用户确认评论内容
6. **发送**: 用户确认后按 `Enter` 键

**确认步骤**:
```python
# 显示评论内容并等待用户确认
print(f"\n即将发表评论:")
print(f"  文章: {title}")
print(f"  内容: {content}")
confirm = input("确认发送? (y/n): ")
if confirm.lower() == 'y':
    # 发送评论
    await editable.press('Enter')
```

完整实现见 `src/toutiao_agent/toutiao_client.py:464-520`

## 登录状态检测

`_check_login_success()` 方法使用多重指标：

1. **主要**: 检查登录 Cookie (sessionid, sid_tt, uid_tt)
2. **辅助**: 检查 localStorage (SLARDARweb_login_sdk)
3. **备用**: 检查页面登录链接状态

## 评论存储

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

## 配置管理

- **主配置**: `config.yaml`
- **敏感数据**: `.env` (TOUTIAO_USERNAME, TOUTIAO_PASSWORD)
- **Cookie**: `data/cookies.json`
- **确认模式**: `behavior.confirmation_mode` 控制交互式/自动执行

## 详细参考

- **完整登录流程**: 见 [references/login-flow.md](references/login-flow.md)
- **数据结构**: 见 [references/data-structures.md](references/data-structures.md)
- **故障排查**: 见 [references/troubleshooting.md](references/troubleshooting.md)

## 开发注意事项

1. **Cookie 登录**是最可靠的方式
2. 评论输入使用 `contenteditable` 非 `textarea`
3. 发送评论用 `Enter` 键，非提交按钮
4. 登录状态检测用多重指标，非单一 URL 检查
5. 所有评论成功后都会记录到 SQLite

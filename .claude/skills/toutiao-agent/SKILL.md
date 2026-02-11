---
name: toutiao-agent
description: 头条热点自动评论和微头条发布助手。使用此技能当：需要理解 toutiao-agent 项目的架构、使用 CLI 命令（获取热点、评论、微头条、活动参与）、调试登录流程、处理评论/微头条生成和发布、修改存储逻辑或活动抓取功能时。
---

# Toutiao Agent - 头条热点助手

基于 Playwright 的头条自动化工具，支持：获取热点新闻、发表评论、发布微头条、获取并参与活动。

## 快速开始

```bash
# 安装依赖
uv sync

# 安装 Playwright 浏览器
uv run playwright install chromium

# 配置登录（推荐使用 Cookie 方式）
# 1. 在浏览器登录头条
# 2. 复制 sessionid, sid_tt, uid_tt 到 data/cookies.json

# 热点评论
uv run toutiao-agent hot-news --limit 20
uv run toutiao-agent start --count 5

# 微头条
uv run toutiao-agent post-micro-headline "今天天气真好" --topic "#生活#"
uv run toutiao-agent micro-headlines --limit 20

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

## CLI 命令参考

### 热点评论命令

| 命令 | 功能 | 示例 |
|------|------|------|
| `hot-news --limit N` | 获取热点新闻（过滤已评论） | `uv run toutiao-agent hot-news --limit 20` |
| `comment <id> <content>` | 直接发表评论 | `uv run toutiao-agent comment 123456 "内容"` |
| `start --count N` | 自动评论流程（交互式） | `uv run toutiao-agent start --count 5` |
| `history --limit N` | 查看评论历史 | `uv run toutiao-agent history --limit 20` |
| `stats` | 查看评论统计 | `uv run toutiao-agent stats` |

### 微头条命令

| 命令 | 功能 | 示例 |
|------|------|------|
| `post-micro-headline <content>` | 发布微头条 | `uv run toutiao-agent post-micro-headline "内容" --topic "#科技#"` |
| `micro-headlines --limit N` | 查看微头条历史 | `uv run toutiao-agent micro-headlines --limit 20` |
| `micro-stats` | 查看微头条统计 | `uv run toutiao-agent micro-stats` |

### 活动命令

| 命令 | 功能 | 示例 |
|------|------|------|
| `activities --limit N` | 查看活动列表 | `uv run toutiao-agent activities --limit 10` |
| `start-activities --count N` | 自动参与活动 | `uv run toutiao-agent start-activities --count 5` |

### 配置命令

| 命令 | 功能 | 示例 |
|------|------|------|
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

## 微头条发布流程（已验证）

微头条使用 Playwright 直接发布：

1. **导航到发布页**: 访问 `/profile?publish_type=article`
2. **等待加载**: 等待页面加载完成
3. **选择微头条**: 点击微头条选项（如果需要）
4. **填写内容**: 使用 `[contenteditable="true"]` 填写
5. **添加话题**: 可选，通过 `topic` 参数添加
6. **发送**: 点击发送按钮

**确认步骤**（可选，由 `confirmation_mode` 控制）:
```python
if config.behavior.get('confirmation_mode', True):
    print(f"\n即将发布微头条:")
    print(f"  内容: {content[:100]}...")
    if topic:
        print(f"  话题: {topic}")
    confirm = input("\n确认发布? (y/n): ")
    if confirm != 'y':
        return
```

完整实现见 `src/toutiao_agent/toutiao_client.py`

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

## 评论和微头条存储

SQLite 数据库 (`data/comments.db`) 包含两个表：

### comments 表
```sql
CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id TEXT NOT NULL UNIQUE,
    title TEXT,
    url TEXT,
    content TEXT,
    created_at TEXT NOT NULL
)
```

### micro_headlines 表
```sql
CREATE TABLE micro_headlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id TEXT,
    activity_title TEXT,
    content TEXT,
    hashtags TEXT,
    images TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    published_at TEXT
)
```

存储在 `ToutiaoAgent.post_comment()` 和 `post_micro_headline()` 成功后自动调用。

## 活动参与流程

1. **获取活动列表**: 从头条创作者平台 API 获取活动
2. **过滤**: 只显示进行中且未参与的活动
3. **生成微头条**: 根据活动信息生成带话题标签的微头条
4. **发布**: 调用微头条发布接口
5. **记录**: 存储到数据库，标记活动已参与

活动 API 端点: `https://mp.toutiao.com/mp/agw/activity`

完整实现见 `src/toutiao_agent/activity_fetcher.py`

## 配置管理

- **主配置**: `config.yaml`
- **敏感数据**: `.env` (TOUTIAO_USERNAME, TOUTIAO_PASSWORD)
- **Cookie**: `data/cookies.json`
- **确认模式**: `behavior.confirmation_mode` 控制交互式/自动执行
- **MCP 服务器**: `mcp.server_url` 配置 MCP 服务器地址（可选）

## 详细参考

- **完整登录流程**: 见 [references/login-flow.md](references/login-flow.md)
- **数据结构**: 见 [references/data-structures.md](references/data-structures.md)
- **微头条发布流程**: 见 [references/micro-headline-flow.md](references/micro-headline-flow.md)
- **故障排查**: 见 [references/troubleshooting.md](references/troubleshooting.md)

## 开发注意事项

1. **Cookie 登录**是最可靠的方式
2. 评论输入使用 `contenteditable` 非 `textarea`
3. 发送评论用 `Enter` 键，非提交按钮
4. 登录状态检测用多重指标，非单一 URL 检查
5. 所有评论和微头条成功后都会记录到 SQLite
6. 活动参与通过发布带话题标签的微头条实现
7. 微头条发布需要先导航到个人主页发布页面
8. 活动抓取使用 HTTP 请求（无需 Playwright），需要有效的 Cookie

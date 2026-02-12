---
name: toutiao-config
description: 头条 Agent 配置管理。使用此技能当：需要修改配置文件、了解配置项含义、设置行为参数或处理配置相关问题时。
---

# Toutiao Agent - 配置管理

## 配置文件

### 主配置: config.yaml

```yaml
# Playwright 浏览器配置
playwright:
  headless: true                    # 是否无头模式
  user_data_dir: "data/user_data"   # 用户数据目录
  cookies_file: "data/cookies.json" # Cookie保存路径

# 存储配置
storage:
  db_file: "data/comments.db"       # SQLite数据库路径

# 行为配置
behavior:
  confirmation_mode: true           # 交互确认模式（重要：保持 true 以防误发）
  max_comments_per_run: 5           # 每次最多评论数
  min_read_count: 1000              # 最低阅读量阈值
  comment_interval: 30              # 评论间隔(秒)

# 评论风格配置
style:
  length: "50-100字"                # 评论长度
  stance: "理性批判"                # 评论立场
  emotion_level: "medium"           # 情感程度 (low/medium/high)

# MCP 服务器配置
mcp:
  server_url: "http://localhost:8003"  # MCP 服务器地址
  timeout: 60                          # 请求超时时间(秒)
  enabled: true                        # 是否启用 MCP 功能
```

---

### 敏感配置: .env

```bash
# 头条账号密码（账密登录时使用）
TOUTIAO_USERNAME=你的手机号
TOUTIAO_PASSWORD=你的密码
```

---

### Cookie: data/cookies.json

自动生成和管理，手动创建格式见 [登录 skill](03-login.md)。

---

## 配置项详解

### playwright.headless

- **类型**: boolean
- **默认**: true
- **说明**: 是否在无头模式下运行浏览器
- **建议**: 调试登录问题时设为 false

### behavior.confirmation_mode

- **类型**: boolean
- **默认**: true
- **说明**: 发布前是否需要用户确认
- **重要**: 保持 true 以防止误发内容

### behavior.max_comments_per_run

- **类型**: integer
- **默认**: 5
- **说明**: 单次运行最多评论数

### behavior.min_read_count

- **类型**: integer
- **默认**: 1000
- **说明**: 文章最低阅读量阈值

### behavior.comment_interval

- **类型**: integer
- **默认**: 30
- **说明**: 评论之间的间隔时间（秒）

### style.length

- **类型**: string
- **默认**: "50-100字"
- **说明**: 生成评论的长度要求

### style.stance

- **类型**: string
- **默认**: "理性批判"
- **说明**: 评论的立场风格

### style.emotion_level

- **类型**: string
- **默认**: "medium"
- **可选**: low, medium, high
- **说明**: 评论的情感程度

---

## 查看配置

```bash
uv run toutiao-agent config-show
```

---

## 配置优先级

1. 环境变量 (.env)
2. config.yaml
3. 默认配置 (代码中的 DEFAULT_CONFIG)

---

## 代码位置

配置管理: `src/toutiao_agent/config.py`

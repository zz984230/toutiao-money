# 数据结构参考

## 热点新闻数据结构

```python
{
    'title': str,        # 文章标题
    'article_id': str,   # 文章ID (group_id)
    'url': str          # 文章链接
}
```

来源: `ToutiaoClient.get_hot_news()` - `toutiao_client.py:317-385`

## 评论发布结果

```python
{
    'success': bool,
    'article_id': str,
    'content': str,
    'error': str | None  # 失败时的错误信息
}
```

来源: `ToutiaoClient.post_comment()` - `toutiao_client.py:413-441`

## 微头条发布结果

```python
{
    'success': bool,
    'message': str | None,  # 成功/失败消息
    'error': str | None     # 错误信息
}
```

来源: `ToutiaoClient.publish_micro_headline()` - `toutiao_client.py`

## 活动数据结构 (Activity)

```python
class Activity:
    activity_id: int                    # 活动 ID
    title: str                          # 活动标题
    introduction: str                   # 活动介绍
    activity_time: str                  # 活动时间描述
    activity_reward: str                # 活动奖励
    activity_participants: str          # 参与人数
    part_in: int                        # 是否已参与 (0/1)
    status: int                         # 活动状态
    hashtag_id: int                     # 话题 ID
    hashtag_name: str                   # 话题名称
    href: str                           # 活动链接
    activity_start_time: int            # 开始时间 (Unix 时间戳)
    activity_end_time: int              # 结束时间 (Unix 时间戳)
```

来源: `activity_fetcher.py:14-67`

## SQLite 表结构

### comments 表

```sql
CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id TEXT NOT NULL UNIQUE,  -- 文章ID，唯一约束
    title TEXT,                       -- 文章标题
    url TEXT,                         -- 文章链接
    content TEXT,                     -- 评论内容
    created_at TEXT NOT NULL          -- ISO格式时间戳
)
```

来源: `CommentStorage._init_db()` - `storage.py:36-49`

### micro_headlines 表

```sql
CREATE TABLE micro_headlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id TEXT,                 -- 活动 ID（如果有）
    activity_title TEXT,              -- 活动标题（如果有）
    content TEXT,                     -- 微头条内容
    hashtags TEXT,                    -- 话题标签
    images TEXT,                      -- 图片列表（JSON 字符串）
    status TEXT NOT NULL DEFAULT 'draft', -- 状态 (draft/published)
    created_at TEXT NOT NULL,         -- 创建时间
    published_at TEXT                 -- 发布时间
)
```

来源: `CommentStorage._init_db()` - `storage.py:50-63`

## 配置结构

```yaml
# config.yaml
playwright:
  headless: true                    # 是否无头模式
  user_data_dir: "data/user_data"   # 用户数据目录
  cookies_file: "data/cookies.json" # Cookie保存路径

storage:
  db_file: "data/comments.db"       # SQLite数据库路径

behavior:
  confirmation_mode: true           # 交互确认模式
  max_comments_per_run: 5           # 每次最多评论数
  min_read_count: 1000              # 最低阅读量阈值
  comment_interval: 30              # 评论间隔(秒)

style:
  length: "50-100字"                # 评论长度
  stance: "理性批判"                # 评论立场
  emotion_level: "medium"           # 情感程度 (low/medium/high)

mcp:
  server_url: "http://localhost:8003"  # MCP 服务器地址
  timeout: 60                          # 请求超时时间(秒)
  enabled: true                        # 是否启用 MCP 功能

# .env (敏感数据)
TOUTIAO_USERNAME=手机号
TOUTIAO_PASSWORD=密码
```

来源: `config.py:12-51`

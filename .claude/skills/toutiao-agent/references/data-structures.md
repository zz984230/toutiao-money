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

## 配置结构

```yaml
# config.yaml
playwright:
  headless: false              # 是否无头模式
  slow_mo: 0                   # 慢动作延迟(ms)
  cookies_file: "data/cookies.json"

storage:
  db_file: "data/comments.db"

behavior:
  confirmation_mode: true      # 交互确认模式
  max_comments_per_run: 5      # 每次最多评论数
  comment_interval: 30         # 评论间隔(秒)

# .env (敏感数据)
TOUTIAO_USERNAME=手机号
TOUTIAO_PASSWORD=密码
```

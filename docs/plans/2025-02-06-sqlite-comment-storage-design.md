# SQLite 评论存储设计

## 概述

使用 SQLite 记录已评论的文章ID，避免重复评论，同时保存完整的评论历史。

## 需求

1. **完整记录**：存储文章ID、标题、URL、评论内容、发布时间
2. **永久保留**：不自动清理历史数据
3. **自动过滤**：获取热点新闻时排除已评论文章

## 架构

### 新建模块

创建 `src/toutiao_agent/storage.py`，使用 Python 标准库 `sqlite3`。

### 数据库结构

```
data/
└── comments.db

comments 表：
├── id            INTEGER PRIMARY KEY
├── article_id    TEXT NOT NULL UNIQUE
├── title         TEXT
├── url           TEXT
├── content       TEXT
├── created_at    TEXT NOT NULL  (ISO 8601)
```

### API

```python
class CommentStorage:
    def is_commented(article_id: str) -> bool
    def add_comment(article_id, title, url, content) -> None
    def get_history(limit=None) -> List[Dict]
    def get_comment_count() -> int
```

## 集成点

### toutiao_client.py

- `get_hot_news()`: 返回前过滤已评论文章

### main.py

- `ToutiaoAgent.post_comment()`: 成功后记录到数据库
- 新增 `history` 命令
- 新增 `stats` 命令

### config.py

- 添加 `storage.db_file` 默认配置

## 错误处理

- 数据库操作失败不阻塞主流程
- 使用事务保证原子性
- `article_id` UNIQUE 防止重复

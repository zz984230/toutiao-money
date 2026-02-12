---
name: toutiao-database
description: 头条 Agent 数据库结构。使用此技能当：需要了解 SQLite 表结构、查询数据、修改存储逻辑或处理数据库问题时。
---

# Toutiao Agent - 数据库结构

## 数据库位置

SQLite 数据库文件: `data/comments.db`

---

## 表结构

### comments 表

存储已发表评论的记录。

```sql
CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id TEXT NOT NULL UNIQUE,  -- 文章ID，唯一约束
    title TEXT,                       -- 文章标题
    url TEXT,                         -- 文章链接
    content TEXT,                     -- 评论内容
    created_at TEXT NOT NULL          -- ISO格式时间戳
);
```

**字段说明**:
- `id` - 自增主键
- `article_id` - 文章ID（group_id），唯一约束，防止重复评论
- `title` - 文章标题
- `url` - 文章链接
- `content` - 发表的评论内容
- `created_at` - ISO格式时间戳，如 `2026-02-12T10:30:00`

---

### micro_headlines 表

存储微头条记录。

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
);
```

**字段说明**:
- `id` - 自增主键
- `activity_id` - 关联的活动ID（如果有）
- `activity_title` - 关联的活动标题（如果有）
- `content` - 微头条内容
- `hashtags` - 话题标签，多个用逗号分隔
- `images` - 图片列表，JSON 字符串格式
- `status` - 状态：`draft`（草稿）或 `published`（已发布）
- `created_at` - 创建时间（ISO格式）
- `published_at` - 发布时间（ISO格式）

---

### activity_participations 表

存储活动参与记录。

```sql
CREATE TABLE activity_participations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id TEXT NOT NULL,        -- 活动 ID
    activity_title TEXT,              -- 活动标题
    participation_type TEXT,          -- 参与类型：original/publish/like/forward/form
    content TEXT,                     -- 生成的内容（如果有）
    status TEXT NOT NULL,             -- 状态：success/failed/pending
    failure_reason TEXT,              -- 失败原因
    created_at TEXT NOT NULL          -- 创建时间
);
```

**字段说明**:
- `id` - 自增主键
- `activity_id` - 活动ID
- `activity_title` - 活动标题
- `participation_type` - 参与类型：
  - `original` - 生成原创内容
  - `publish` - 发布微头条
  - `like` - 点赞
  - `forward` - 转发
  - `form` - 填写表单
- `content` - 生成的内容（如果有）
- `status` - 状态：
  - `success` - 参与成功
  - `failed` - 参与失败
  - `pending` - 待验证
- `failure_reason` - 失败原因描述
- `created_at` - 创建时间（ISO格式）

---

## 数据库操作

### 查询评论历史

```bash
uv run toutiao-agent history --limit 20
```

### 查看评论统计

```bash
uv run toutiao-agent stats
```

### 查询微头条历史

```bash
uv run toutiao-agent micro-headlines --limit 20
```

### 查看微头条统计

```bash
uv run toutiao-agent micro-stats
```

### 查询活动参与历史

```bash
uv run toutiao-agent activity-history --limit 20
```

### 查看活动参与统计

```bash
uv run toutiao-agent activity-stats
```

---

## 故障排查

### SQLite 锁定
**症状**: `database is locked`

**解决**: 关闭其他运行中的进程

### 文章ID冲突
**症状**: `UNIQUE constraint failed: comments.article_id`

**原因**: 尝试重复记录已评论的文章

**说明**: storage 层会检查，但直接插入可能触发

---

## 代码位置

数据库操作: `src/toutiao_agent/storage.py`

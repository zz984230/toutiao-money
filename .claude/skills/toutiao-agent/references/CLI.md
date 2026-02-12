---
name: toutiao-cli
description: 头条 Agent CLI 命令参考。使用此技能当：需要了解可用的 CLI 命令、查询命令用法、查看历史记录或统计数据时。
---

# Toutiao Agent - CLI 命令参考

所有命令使用 `uv run toutiao-agent` 前缀执行。

## 热点评论命令

### 获取热点新闻

```bash
uv run toutiao-agent hot-news --limit 20
```

- 功能：获取热点新闻列表，自动过滤已评论的文章
- 参数：`--limit N` - 获取数量（默认 20）

### 直接发表评论

```bash
uv run toutiao-agent comment <article_id> "<评论内容>"
```

- 功能：直接对指定文章发表评论
- 示例：`uv run toutiao-agent comment 123456 "这篇文章写得很好"`

### 自动评论流程

```bash
uv run toutiao-agent start --count 5
```

- 功能：获取热点 → 生成评论 → 用户确认 → 发布
- 参数：`--count N` - 评论数量

### 查看评论历史

```bash
uv run toutiao-agent history --limit 20
```

- 功能：查看已发表评论的历史记录
- 参数：`--limit N` - 显示条数

### 查看评论统计

```bash
uv run toutiao-agent stats
```

- 功能：显示评论总数、今日评论数等统计信息

---

## 微头条命令

### 发布微头条

```bash
uv run toutiao-agent post-micro-headline "<内容>" --topic "#科技#"
```

- 功能：发布微头条
- 参数：
  - `content` - 微头条内容（必填）
  - `--topic` - 话题标签（可选，如 #科技#）
  - `--images` - 图片列表（可选）

### 查看微头条历史

```bash
uv run toutiao-agent micro-headlines --limit 20
```

- 功能：查看已发布的微头条历史
- 参数：`--limit N` - 显示条数

### 查看微头条统计

```bash
uv run toutiao-agent micro-stats
```

- 功能：显示微头条总数等统计信息

---

## 活动命令

### 查看活动列表

```bash
uv run toutiao-agent activities --limit 10
```

- 功能：获取头条创作者平台的活动列表
- 参数：`--limit N` - 显示数量

### 智能参与活动

```bash
uv run toutiao-agent start-activities --count 5
```

- 功能：分析活动并智能参与
- 参数：`--count N` - 参与活动数量

### 查看参与历史

```bash
uv run toutiao-agent activity-history --limit 20
```

- 功能：查看活动参与历史
- 参数：`--limit N` - 显示条数

### 查看参与统计

```bash
uv run toutiao-agent activity-stats
```

- 功能：显示活动参与统计信息

---

## 配置命令

### 显示当前配置

```bash
uv run toutiao-agent config-show
```

- 功能：打印当前配置信息

---

## 命令输出格式

### 热点新闻输出
```
1. [文章标题]
   ID: 123456
   URL: https://www.toutiao.com/article/123456/
```

### 评论历史输出
```
ID  | 文章ID  | 标题          | 评论内容      | 时间
----|---------|---------------|---------------|------------------
1   | 123456  | 示例标题      | 示例评论      | 2026-02-12 10:00
```

### 活动列表输出
```
1. [活动标题]
   ID: act_123
   时间: 2026-02-10 ~ 2026-02-20
   奖励: 现金激励
   状态: 进行中
```

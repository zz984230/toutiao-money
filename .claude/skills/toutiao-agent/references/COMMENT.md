---
name: toutiao-comment
description: 评论发表和存储。使用此技能当：需要发表评论、查看评论历史、处理评论存储或调试评论发布问题时。
---

# Toutiao Agent - 评论发表

## 发布流程

头条评论使用 `contenteditable` 输入框：

```
1. 导航到文章: 使用 /article/{id}/ 格式
2. 滚动到评论区: window.scrollTo(0, document.body.scrollHeight)
3. 点击输入区域: .ttp-comment-input
4. 填写内容: [contenteditable="true"]
5. 用户确认: 在发送前必须和用户确认评论内容
6. 发送: 用户确认后按 Enter 键
```

## CLI 命令

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

### 查看评论统计

```bash
uv run toutiao-agent stats
```

---

## 关键选择器

| 步骤 | 选择器 | 特殊处理 |
|------|--------|----------|
| 文章页面 | `/article/{id}/` | 需要登录状态 |
| 滚动到底部 | JavaScript | `window.scrollTo(0, document.body.scrollHeight)` |
| 评论输入区 | `.ttp-comment-input` | 先点击激活输入框 |
| 内容输入框 | `[contenteditable="true"]` | 使用 `fill()` 填写内容 |
| 发送操作 | Enter 键 | 非 submit 按钮 |

---

## 确认步骤

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

---

## 评论数据结构

### 发布结果
```python
{
    'success': bool,
    'article_id': str,
    'content': str,
    'error': str | None  # 失败时的错误信息
}
```

---

## 存储

评论发布成功后自动存储到 SQLite `comments` 表：

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

存储在 `ToutiaoAgent.post_comment()` 成功后自动调用。

---

## 故障排查

### 未找到评论输入框
**症状**: `post_comment` 返回 `'未找到评论输入框'`

**可能原因**:
1. 页面未完全加载
2. 文章ID无效
3. 需要登录才能评论

### 评论发布无响应
**症状**: 点击提交后无结果

**检查**:
1. 内容是否触发审核
2. 是否频繁发布被限制

### 文章ID冲突
**症状**: `UNIQUE constraint failed: comments.article_id`

**原因**: 尝试重复记录已评论的文章（storage 层会检查，但直接插入可能触发）

---

## 代码位置

评论发表: `src/toutiao_agent/toutiao_client.py:464-520`
评论存储: `src/toutiao_agent/storage.py`

---
name: toutiao-micro-headline
description: 微头条发布和存储。使用此技能当：需要发布微头条、查看微头条历史、处理微头条存储或调试发布问题时。
---

# Toutiao Agent - 微头条发布

## 发布流程

微头条使用 Playwright 直接发布：

```
1. 访问 https://www.toutiao.com/profile?publish_type=article
2. 等待页面加载完成
3. 点击"写微头条"选项（如果需要）
4. 等待微头条编辑器加载
5. 填写内容到 contenteditable 输入框
6. 添加话题标签（可选）
7. 点击发送按钮
8. 等待发布成功
9. 记录到数据库
```

## CLI 命令

### 发布微头条

```bash
uv run toutiao-agent post-micro-headline "<内容>" --topic "#科技#"
```

参数说明：
- `content` - 微头条内容（必填）
- `--topic` - 话题标签（可选，如 #科技#）
- `--images` - 图片列表（可选）

### 查看历史

```bash
uv run toutiao-agent micro-headlines --limit 20
```

### 查看统计

```bash
uv run toutiao-agent micro-stats
```

---

## 关键选择器

| 步骤 | 选择器 | 特殊处理 |
|------|--------|----------|
| 发布页面 | `/profile?publish_type=article` | 需要登录状态 |
| 微头条选项 | `.publish-option` 或类似 | 点击切换到微头条模式 |
| 内容输入框 | `[contenteditable="true"]` | 使用 `fill()` 填写内容 |
| 话题输入框 | `.topic-input` 或类似 | 可选，输入 #话题名# |
| 发送按钮 | `.send-button` 或类似 | 点击发送 |

---

## 发布方法签名

```python
async def publish_micro_headline(
    self,
    content: str,
    topic: Optional[str] = None,
    images: Optional[list] = None
) -> dict:
    """发布微头条

    Args:
        content: 微头条内容
        topic: 话题标签 (如 #科技#)
        images: 图片列表（可选）

    Returns:
        dict: {'success': bool, 'message': str, 'error': str}
    """
```

---

## 确认步骤

发布前确认（由 `confirmation_mode` 控制）：

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

---

## 存储

微头条发布成功后自动存储到 SQLite `micro_headlines` 表：

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

存储在 `ToutiaoAgent.post_micro_headline()` 成功后自动调用。

---

## 故障排查

### 发布失败
- 检查是否已登录（Cookie 有效）
- 检查内容是否触发审核
- 检查话题标签格式是否正确（#话题名#）
- 检查是否频繁发布被限制

### 输入框未找到
- 检查页面是否完全加载
- 检查是否登录状态

---

## 代码位置

微头条发布: `src/toutiao_agent/toutiao_client.py` - `publish_micro_headline()`

# 微头条发布流程详解

## 完整发布时序

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

## 关键选择器

| 步骤 | 选择器 | 特殊处理 |
|------|--------|----------|
| 发布页面 | `/profile?publish_type=article` | 需要登录状态 |
| 微头条选项 | `.publish-option` 或类似 | 点击切换到微头条模式 |
| 内容输入框 | `[contenteditable="true"]` | 使用 `fill()` 填写内容 |
| 话题输入框 | `.topic-input` 或类似 | 可选，输入 #话题名# |
| 发送按钮 | `.send-button` 或类似 | 点击发送 |

## 发布方法

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

## 活动参与流程

活动参与通过发布带话题标签的微头条实现：

1. **获取活动列表**: 使用 `activity_fetcher.fetch_activities()`
2. **筛选活动**: 只处理进行中且未参与的活动
3. **生成内容**: 根据活动信息生成微头条内容
4. **添加话题**: 包含活动指定的话题标签
5. **发布**: 调用 `publish_micro_headline()`
6. **记录**: 存储到数据库，标记活动已参与

## 活动 API 端点

- **活动列表**: `https://mp.toutiao.com/mp/agw/activity/list/v2/`
- **获取分类**: `https://mp.toutiao.com/mp/agw/activity/get_all_category/`

API 请求需要携带有效的 Cookie。

## 代码位置

- 微头条发布: `toutiao_client.py` - `publish_micro_headline()`
- 活动抓取: `activity_fetcher.py` - `ActivityFetcher.fetch_activities()`
- 活动参与命令: `main.py` - `start_activities_cmd()`

## 调试技巧

发布失败时检查：
- 是否已登录（Cookie 有效）
- 内容是否触发审核
- 话题标签格式是否正确（#话题名#）
- 是否频繁发布被限制

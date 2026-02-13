# Toutiao Inspiration 技能进化日志

记录技能从经验中学习和改进的过程。

---

## E011 - 2026-02-14

### 问题：从热点活动页面获取话题

**场景**：需要从 `https://mp.toutiao.com/profile_v4/activity/hot-spot` 获取热门话题，按阅读量排序

**初始方法**：使用 `document.body.innerText` 提取页面文本，然后用正则表达式匹配 `#话题# 阅读` 模式

**遇到的问题**：
1. 页面文本混入了大量 CSS 样式代码，导致正则匹配到无效"话题"
2. 正则表达式不够精确，把 CSS 属性名和值也当作话题了
3. 提取到的结果包含大量无效数据（如 `e8e8e8`、`border-radius:4px` 等）

### 解决方案

**改进的正则表达式**：
```python
# 原正则（太宽泛）
r'#([^#\s]+(?:\s+[^#\s]+)*)#.*?阅读\s*(\d+).*?讨论\s*(\d+)'

# 改进后（更精确）
#话题# 后面跟着数字（阅读量）
pattern = r'#([^#\s]+(?:\s+[^#\s]+)*)#\s*(?:阅读\s*)?(\d+(?:\.\d+)?)?\s*(?:万|亿)?'
```

**添加的过滤条件**：
```python
def is_valid_topic(topic_name):
    """判断是否是有效话题"""
    # 1. 过滤包含 CSS 特殊字符的
    invalid_chars = ['{', '}', ':', ';', '.', '(', ')', '=', 'px', '%']
    if any(char in topic_name for char in invalid_chars):
        return False

    # 2. 过滤太长的（超过 30 字符）
    if len(topic_name) > 30:
        return False

    # 3. 过滤纯英文/数字的（话题应该是中文为主）
    chinese_count = sum(1 for c in topic_name if '\u4e00' <= c <= '\u9fff')
    if len(topic_name) > 0 and chinese_count / len(topic_name) < 0.3:
        return False

    # 4. 过滤包含特定 CSS 关键词的
    css_keywords = ['background', 'color', 'display', 'cursor', 'border',
                   'padding', 'transition', 'transform', 'z-index']
    if any(keyword in topic_name.lower() for keyword in css_keywords):
        return False

    return True
```

### 最终工作流程

**正确获取热点话题的步骤**：

1. 访问 `https://mp.toutiao.com/profile_v4/activity/hot-spot`
2. 等待页面加载完成 (`networkidle` 状态)
3. 使用 JavaScript 从 `document.body.innerText` 提取文本
4. 使用精确正则匹配：`#([^#\s]+(?:\s+[^#\s]+)*)#\s*(?:阅读\s*)?(\d+(?:\.\d+)?)?\s*(?:万|亿)?`
5. 通过 `seen` Set 去重
6. 使用 `is_valid_topic()` 函数过滤无效话题
7. 按阅读量降序排序
8. 保存到 JSON 文件

### 关键发现

1. **页面 URL**：热点活动页面是 `/profile_v4/activity/hot-spot` 而非 `/profile_v3_public/public/inspiration/`

2. **数据格式**：话题格式为 `#话题#` 后面紧跟数字（阅读量），例如：
   - `#晒出你的每日练字打卡# 阅读687.7万`
   - `#心情不好的时候，你们最想干什么呢# 阅读610.3万`

3. **编码问题**：Windows 控制台需要设置 UTF-8 编码：
   ```python
   if sys.platform == "win32":
       import io
       sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
   ```

### 成功提取的话题示例（2026-02-14）

| 排名 | 话题 | 阅读量 |
|-------|------|---------|
| 1 | #健康和财富，你选择哪一个# | 898.2万 |
| 2 | #分享一张你家宝宝的照片吧# | 654.8万 |
| 3 | #炒股票有没有最简单、最笨的方法?# | 471万 |
| 4 | #大家有电话号码用了20年以上吗# | 442.9万 |
| 5 | #长期做瑜伽给你的生活带来什么变化# | 306.4万 |
| 6 | #分享一张你养的花盛开的样子# | 263.3万 |
| 7 | #拍一张照片证明来过澳门# | 132.2万 |
| 8 | #分享一本引人入胜的小说# | 41.3万 |
| 9 | #什么品牌的普洱茶比较好# | 20.3万 |
| 10 | #颜值、才华、人品，哪个对人最重要# | 8万 |

### 需要同步的文件

1. **更新 SKILL.md**：添加正确的 URL 和数据提取方法
2. **创建新脚本模板**：`get_hotspot_topics.py` 作为标准模板

### 后续优化方向

1. 尝试通过选择器直接获取话题元素，而非依赖正则匹配文本
2. 添加"讨论量"的提取和排序选项
3. 添加话题分类功能（如健康、娱乐、生活等）
4. 支持增量更新（只获取新话题，避免重复）

---

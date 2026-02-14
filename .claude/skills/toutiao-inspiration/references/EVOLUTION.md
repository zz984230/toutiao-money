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

## E012 - 2026-02-14

### 场景：完整的微头条发布成功流程

**背景**：从零开始，使用已有 Cookie 登录 → 选择创作灵感话题 → 撰写内容 → 成功发布

**成功步骤**：

1. **检查登录状态**
   - 确认 `data/cookies.json` 文件存在
   - 文件大小约 68KB，说明 Cookie 有效

2. **获取热门话题**
   - 运行脚本：`get_hotspot_topics_clean.py`
   - 访问：`https://mp.toutiao.com/profile_v4/activity/hot-spot`
   - 使用正则提取：`#([^#\s]+(?:\s+[^#\s]+)*)#` 匹配话题
   - 按阅读量排序，获取 16 个有效话题

3. **筛选话题**
   - 从数据库查询已参与话题
   - 过滤掉已参与的话题（使用 `storage.is_topic_participated()` 检查）
   - 展示可用话题列表

4. **用户选择话题**
   - 通过 `AskUserQuestion` 工具展示选项
   - 用户选择：`#分享一件你喜欢的藏品#`（389.3万阅读）

5. **生成反共识内容**
   - 根据 `PROMPT_STYLES.md` 避免 AI 味
   - 立场：收藏是智商税（反共识角度）
   - 内容：
     ```
     收藏这事儿就是花钱买安慰。当年咬牙买的那台"绝版"胶片机，现在连闲鱼都无人问津。99%的收藏品最后都是吃灰，咱就是说，不如把钱花在体验上。#分享一件你喜欢的藏品#
     ```

6. **用户确认发布**
   - 使用 `AskUserQuestion` 工具展示内容预览
   - 用户确认：`确认发布`

7. **成功发布**
   - 使用 ToutiaoClient 的 `publish_micro_headline()` 方法
   - 访问发布页面：`https://mp.toutiao.com/profile_v4/weitoutiao/publish`（注意：weitoutiao 拼写正确）
   - 找到输入框：ProseMirror contenteditable 元素
   - 填写内容并点击发布按钮
   - 发布成功，记录到数据库

### 关键发现

1. **URL 拼写确认**：
   - 微头条发布页面 URL：`/profile_v4/weitoutiao/publish`
   - "微头条"拼音 = weitoutiao（一个 t）
   - 代码中 URL 已是正确的，不需要修改

2. **发布页面元素**：
   - 输入框选择器：`[contenteditable="true"]`，className 为 `ProseMirror`
   - placeholder 内容：`有什么新鲜事想告诉大家？`
   - 发布按钮：`button:has-text("发布")` 或 className `byte-btn byte-btn-primary publish-content`

3. **Windows 编码问题**：
   - Python 脚本中包含中文时，使用字符串拼接而非单行字符串
   - 示例：
     ```python
     # 错误（编码问题）
     content = "收藏这事儿就是花钱买安慰..."

     # 正确（字符串拼接）
     content = (
         "收藏这事儿就是花钱买安慰。"
         "当年咬牙买的那台..."
     )
     ```

4. **数据库记录**：
   - 发布成功后使用 `storage.add_micro_headline()` 记录
   - 同时更新话题参与状态，避免重复发布

### 成功的完整代码

**发布脚本**（`publish_weit.py`）：
```python
# -*- coding: utf-8 -*-
import asyncio
import sys
import io
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from toutiao_agent.toutiao_client import ToutiaoClient

async def main():
    client = ToutiaoClient()
    await client.start()

    try:
        content = (
            "收藏这事儿就是花钱买安慰。当年咬牙买的那台"
            '"绝版"胶片机，现在连闲鱼都无人问津。'
            "99%的收藏品最后都是吃灰，咱就是说，"
            "不如把钱花在体验上。#分享一件你喜欢的藏品#"
        )
        topic = "#分享一件你喜欢的藏品#"

        result = await client.publish_micro_headline(
            content=content,
            topic=topic
        )

        if result.get('success'):
            from toutiao_agent.storage import storage
            storage.add_micro_headline(
                content=content,
                hashtags=topic,
                images=None
            )
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 验证结果

- ✅ 发布时间：2026-02-14T02:03:16
- ✅ 数据库记录：已保存到 `data/comments.db`
- ✅ 话题标签：#分享一件你喜欢的藏品#
- ✅ 内容长度：68 字（符合 50-100 字要求）

### 需要同步的文件

1. **更新 SKILL.md**：确认 URL 正确性，添加 Windows 编码处理建议
2. **更新 STRATEGIES.md**：记录完整的微头条发布策略

### 后续优化方向

1. 添加自动话题去重功能（基于数据库历史记录）
2. 支持批量发布多个话题
3. 添加发布结果验证（截图保存）
4. 优化内容生成提示词模板

---

## E013 - 2026-02-15

### 问题：微头条发布页面的发布助手遮罩层阻挡所有点击操作

**场景**：在微头条发布页面 (`https://mp.toutiao.com/profile_v4/weitoutiao/publish`) 发布内容时，所有点击操作都被遮罩层阻挡

**遇到的问题**：
1. 页面加载后自动显示"发布助手"侧边抽屉 (`.byte-drawer-wrapper`)
2. 遮罩层 (`.byte-drawer-mask`) 拦截所有点击事件
3. 尝试点击编辑器 → 被阻挡
4. 尝试点击折叠按钮 → 也被阻挡（递归问题）
5. 使用 `click(force=True)` → 仍然被阻挡

**遮罩层 HTML 结构**：
```html
<div class="byte-drawer-wrapper publish-assistant-old-drawer">
  <div class="byte-drawer-mask fade-appear-done fade-enter-done"></div>
  <div class="byte-drawer container-open slideRight-appear-done slideRight-enter-done">
    <div class="byte-drawer-header">
      <div class="drawer-title">
        <span class="icon-wrap">
          <svg class="byte-icon byte-icon-fold">...</svg>
        </span>
      </div>
    </div>
  </div>
</div>
```

**错误信息**：
```
ElementHandle.click: Timeout 30000ms exceeded.
<byte-drawer-mask ...> subtree intercepts pointer events
```

### 解决方案

**关键发现**：必须使用 JavaScript 直接移除 DOM 元素，不能尝试点击操作（连点击折叠按钮也会被遮罩拦截）

**正确的处理顺序**：
```python
# 1. 访问页面
await page.goto('https://mp.toutiao.com/profile_v4/weitoutiao/publish')
await page.wait_for_load_state('networkidle')
await page.wait_for_timeout(3000)

# 2. 在任何点击操作之前，先用JavaScript移除整个抽屉包裹层
removed = await page.evaluate('''() => {
    // 移除整个抽屉包裹层
    const wrapper = document.querySelector('.byte-drawer-wrapper');
    if (wrapper) {
        wrapper.remove();
        return 'removed drawer wrapper';
    }

    // 备用：只移除遮罩层
    const mask = document.querySelector('.byte-drawer-mask');
    if (mask) {
        mask.remove();
        return 'removed mask';
    }

    return 'no element found';
}''')

print(f'移除结果: {removed}')
await page.wait_for_timeout(1000)

# 3. 现在可以安全地进行任何点击操作
editor = await page.wait_for_selector('[contenteditable="true"]')
await editor.click()  # 不会被阻挡
await editor.fill(CONTENT)

# 4. 点击发布按钮也使用JavaScript（绕过可能的遮罩残留）
publish_btn = await page.wait_for_selector('button:has-text("发布")')
await page.evaluate('(element) => element.dispatchEvent(new MouseEvent("click", {bubbles: true}))', publish_btn)
```

### 关键要点

1. **时机很重要**：必须在任何点击操作之前移除遮罩
2. **直接移除 DOM**：不要尝试点击折叠按钮（也会被遮罩拦截）
3. **DOM 层级**：
   - `.byte-drawer-wrapper` - 最外层包裹，移除它最干净
   - `.byte-drawer-mask` - 遮罩层，也可以单独移除
   - `.drawer-title .icon-wrap` - 折叠按钮（但点击会被拦截）
4. **使用 JavaScript 点击**：发布按钮也建议使用 `dispatchEvent` 而非 Playwright 的 `click()`

### 验证结果

- ✅ 成功发布微头条：#大家都是怎样度过人生低谷期的#
- ✅ 内容正常输入到编辑器
- ✅ 发布按钮成功点击
- ✅ 无遮罩层干扰

### 需要同步的文件

1. **更新 SKILL.md**：
   - 在"编码注意事项"章节添加"微头条发布遮罩层问题"
   - 包含完整的解决方案代码示例

2. **后续脚本模板**：
   - 所有微头条发布脚本必须遵循此模式
   - 先移除遮罩，再进行任何操作

### 后续优化方向

1. 将遮罩处理逻辑封装为可复用函数
2. 考虑在 ToutiaoClient 中集成自动遮罩处理
3. 探索是否可以通过 CSS 隐藏遮罩而非移除 DOM

---

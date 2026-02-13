# 微头条发布策略

记录经过验证的微头条发布流程和技巧。

---

## 完整发布流程（已验证）

### 1. 登录检查

```bash
# 检查 cookie 文件
ls -la data/cookies.json
```

**关键点**：
- Cookie 文件必须存在且有效（大小 > 10KB）
- 如果 Cookie 过期，需要重新登录：`uv run toutiao-agent login`

### 2. 获取热门话题

**方式 A：从热点活动页面获取（推荐）**

```bash
# 运行话题获取脚本
uv run python .claude/skills/toutiao-inspiration/scripts/get_hotspot_topics_clean.py
```

**URL**: `https://mp.toutiao.com/profile_v4/activity/hot-spot`

**提取逻辑**：
1. 访问热点活动页面
2. 使用 `document.body.innerText` 提取页面文本
3. 正则匹配：`#([^#\s]+(?:\s+[^#\s]+)*)#\s*(?:阅读\s*)?(\d+(?:\.\d+)?)?\s*(?:万|亿)?`
4. 过滤无效话题（CSS字符、过长的、非中文的）
5. 按阅读量降序排序
6. 保存到 `data/hotspot_topics_clean.json`

### 3. 筛选已参与话题

```python
# 查询数据库中已参与的话题
storage = CommentStorage()
participated = storage.get_micro_headlines(limit=100)
participated_hashtags = set()
for r in participated:
    if r['hashtags']:
        participated_hashtags.add(r['hashtags'].strip('#'))

# 过滤话题列表
available_topics = [t for t in hot_topics if t['topic'] not in participated_hashtags]
```

### 4. 用户选择话题

使用 `AskUserQuestion` 工具展示话题选项：

```
1. #分享一件你喜欢的藏品# (389.3万阅读)
2. #一句话记录今天的心情# (666.3万阅读)
3. #你每天都游泳多少米，多长时间最好# (155万阅读)
```

### 5. 生成反共识内容

**核心原则**（来自 `PROMPT_STYLES.md`）：

1. **避免 AI 味**：
   - 不用"首先、其次、最后"
   - 不用"值得注意的是"、"不得不说"
   - 不用四平八稳的表达
   - 用口语化、网络用语

2. **反共识角度**：
   - 找到主流观点的薄弱点
   - 立场要极端化（不要"既有利又有弊"）
   - 用挑衅性表达

**示例**：
```
主流：收藏老物件有情怀价值
反共识：收藏这事儿就是花钱买安慰。当年咬牙买的那台"绝版"胶片机，
现在连闲鱼都无人问津。99%的收藏品最后都是吃灰，咱就是说，
不如把钱花在体验上。#分享一件你喜欢的藏品#
```

### 6. 用户确认发布（MUST FOLLOW）

**在执行任何微头条发布命令前，必须使用 `AskUserQuestion` 工具与用户确认**：

```
即将发布微头条：

话题：#分享一件你喜欢的藏品#
内容：收藏这事儿就是花钱买安慰...
字数：68 字

是否确认发布？
[确认发布] [取消] [修改内容]
```

**原则**：微头条绝对不能自动发布出去！这是最高优先级的安全规则。

### 7. 执行发布

**使用 ToutiaoClient.publish_micro_headline() 方法**

**关键 URL**: `https://mp.toutiao.com/profile_v4/weitoutiao/publish`

**页面元素**：
- 输入框：`[contenteditable="true"]`，className `ProseMirror`
- placeholder: `有什么新鲜事想告诉大家？`
- 发布按钮：`button:has-text("发布")` 或 className `byte-btn byte-btn-primary publish-content`

**发布脚本模板**：

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
        # Windows 编码问题：使用字符串拼接
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

### 8. 验证与记录

发布成功后：
- 记录话题到 `storage.add_micro_headline()`
- 保存发布截图作为证据（可选）
- 更新话题参与状态，避免重复发布

---

## 已验证的成功案例

**2026-02-14 发布案例**：

- **话题**: #分享一件你喜欢的藏品#
- **阅读量**: 389.3万
- **内容**: 收藏这事儿就是花钱买安慰。当年咬牙买的那台"绝版"胶片机，现在连闲鱼都无人问津。99%的收藏品最后都是吃灰，咱就是说，不如把钱花在体验上。
- **字数**: 68字
- **风格**: 反共识（收藏是智商税角度）
- **结果**: ✅ 发布成功

---

## 常见问题处理

### 问题 1：Cookie 过期

**症状**: 访问发布页面时跳转到登录页

**解决**：
```bash
uv run toutiao-agent login
```

### 问题 2：页面加载超时

**症状**: `Timeout 10000ms exceeded`

**解决**：
- 增加超时时间：`timeout=60000`
- 检查网络连接
- 使用非 headless 模式（`headless: false`）以便观察

### 问题 3：Windows 编码问题

**症状**: Python 脚本中文字符串报 `SyntaxError: invalid syntax`

**解决**：使用字符串拼接而非单行字符串

```python
# 错误方式
content = "收藏这事儿就是花钱买安慰。当年咬牙买的那台"绝版"胶片机..."

# 正确方式
content = (
    "收藏这事儿就是花钱买安慰。当年咬牙买的那台"
    '"绝版"胶片机，现在连闲鱼都无人问津。'
    "99%的收藏品最后都是吃灰..."
)
```

### 问题 4：找不到输入框

**症状**: `未找到输入框`

**解决**：
- 等待页面完全加载：`await asyncio.sleep(5)`
- 检查 `ProseMirror` 元素的可见性
- 使用 JavaScript 查找所有可输入元素

---

## 进化方向

1. **自动去重**: 基于数据库历史记录自动过滤已参与话题
2. **批量发布**: 支持一次选择多个话题批量发布
3. **结果验证**: 自动截图保存发布结果
4. **智能提示**: 根据话题类型自动推荐内容角度

---
name: toutiao-inspiration
description: 头条创作灵感热门话题探索助手。使用此技能当：需要探索创作中心"创作灵感"下的热门话题、分析他人内容、生成个性鲜明的微头条内容时。触发场景：用户说"帮我找热门话题"、"探索创作灵感"、"分析这个话题"、"生成微头条内容"等。
---

# Toutiao Inspiration - 创作灵感热门话题探索

探索头条创作灵感热门话题、分析他人内容、生成个性鲜明的微头条。

## 快速启动

```bash
# 1. 确保已登录（检查 cookie 文件）
ls data/cookies.json || uv run toutiao-agent login

# 2. 开始探索热门话题
# 让 AI 自动获取并分析热门话题
```

## 探索循环

```
┌────────────────────────────────────────────────────────────────────┐
│  登录检查 → 获取热门话题 → 选择话题 → 分析内容 → 生成提示词 → 生成微头条 → 确认发布 → 反馈/进化  │
│     ↑                                                                        │
│     └──────── 未登录时先执行登录流程 ─────────────────────────────────────────┘
└────────────────────────────────────────────────────────────────────┘
```

### 0. 登录检查阶段（MUST DO）

**在任何探索操作之前，必须先确保登录状态**：

```bash
# 1. 检查 cookie 文件是否存在
ls -la data/cookies.json

# 2. 如果 cookie 文件不存在，执行登录
uv run toutiao-agent login

# 3. 验证登录状态
uv run toutiao-agent activities --limit 1
```

**登录失败处理**：
- Cookie 过期 → 重新执行登录流程
- 需要验证码 → 使用非 headless 模式手动处理
- 网络错误 → 检查网络连接后重试

**重要**：每次会话开始时都应检查登录状态，避免后续操作失败。

### 1. 获取热门话题阶段

使用 playwright-cli 或 ToutiaoClient 访问创作灵感页面，获取热度值最高的前 5 个话题：

```bash
# 创作灵感页面 URL
https://mp.toutiao.com/profile_v3_public/public/inspiration/
```

**话题信息提取**：
- 话题名称（必须包含 #话题# 格式）
- 热度值/参与人数
- 话题描述

**⚠️ 重要：避免重复选择已参与的话题**
- 使用 `storage.is_topic_participated()` 检查话题状态
- 已参与的话题在列表中显示 ✅，应跳过
- 除非是每日任务（如每日幸运签），否则不重复参与

### 2. 选择话题阶段

将获取到的 5 个热门话题展示给用户，让用户选择要深入分析的话题。

**展示格式**：
```
热门话题列表：
1. #话题A# ✅ - 热度: 12345 (已参与，跳过)
2. #话题B# - 热度: 9876
3. #话题C# - 热度: 7654
...
```

### 3. 分析内容阶段

进入选定话题页面，仔细阅读其他用户发布的内容：

**分析要点**：
- 提取 3-5 条有代表性的内容
- 分析热门观点的主流立场
- 识别可以反驳或调侃的角度

### 4. 生成提示词阶段

根据分析结果，生成个性鲜明、有立场的提示词（**特别注意不要有 AI 味**）。

**提示词风格**：
- **反共识/争议性**：针对热门观点提出不同看法
- **轻松调侃型**：用幽默调侃的方式表达观点

**避免 AI 味的关键原则**（详见 [PROMPT_STYLES.md](references/PROMPT_STYLES.md)）：
- 不要用"首先、其次、最后"等逻辑连接词
- 不要用"值得注意的是"、"不得不说"等 AI 套话
- 多用口语化表达、网络用语
- 假设情绪化、有偏见的"人设"
- 用短句、断句增加节奏感

### 5. 生成微头条内容阶段

根据提示词生成 10-100 字的微头条内容。

**格式要求**：
- 内容开头或结尾必须包含 `#<话题>#` 标签
- 总字数控制在 10-100 字
- 风格与提示词保持一致

### 6. 确认发布阶段（MUST FOLLOW）

**在执行任何微头条发布命令前，必须使用 `AskUserQuestion` 工具与用户确认**：

1. **展示内容预览**：
   - 话题名称
   - 生成的微头条内容
   - 预期收益（如适用）

2. **询问用户**：
   ```
   是否确认发布此微头条？
   [确认发布] [取消] [修改内容]
   ```

**原则**：微头条绝对不能自动发布出去！这是最高优先级的安全规则。

### 7. 验证与记录阶段

发布成功后：
- 记录话题到 `storage.mark_topic_participated(topic_id)`
- 保存发布截图作为证据

## 失败处理

**遇到以下情况时的处理策略**：

```
Cookie过期/未登录 → 重新执行登录流程，保存新cookie
话题页面404/加载失败 → 先检查URL格式是否正确，再重试
话题卡片点击失败 → 改进选择器并重试
内容审核失败 → 调整内容策略后重试
未知错误 → 截图保存，咨询用户
```

**重要：不断尝试其他方法直到完成目标**

## 启发式规则

**可行性筛选**：
```
未参与话题 > 已参与话题
高热度话题 > 低热度话题
反共识/争议性强 > 平庸观点
```

**探索控制**：
- 单次探索话题数：5 个
- 遇到高价值话题时，立即深入分析
- 发布成功后记录话题状态，避免重复

## 自适应学习

- 记录成功参与的话题模式
- 识别高频出现的观点类型
- 优化提示词生成标准（失败类型自动调整）

---

## 进化模式

toutiao-inspiration 具备持续进化能力，能够从经验中学习和改进。

### 自动进化

在探索过程中遇到以下情况会自动触发进化：

1. **未知话题类型**：无法用现有模式分类的话题
2. **连续失败**：同一类型话题失败 3 次
3. **新页面结构**：检测到页面 DOM 结构变化

自动进化流程：检测 → 分析 → 测试 → 记录 → 恢复探索

### 主动进化

用户可主动调用进化模式进行深度优化：

```bash
# 复盘并优化策略
uv run toutiao-agent evolve --mode=review

# 分析特定话题类型
uv run toutiao-agent evolve --mode=analyze --type="反共识"

# 生成进化报告
uv run toutiao-agent evolve --mode=report
```

### 进化日志

所有进化记录保存在 `references/EVOLUTION.md`

- 查看进化历史
- 了解新增能力
- 追溯问题解决过程

### 技能同步

进化成功后会智能检测需要更新的技能文件，经用户确认后自动同步。

**同步决策逻辑**：

| 解决方案类型 | 更新的技能文件 |
|------------|--------------|
| 新提示词风格 | PROMPT_STYLES.md |
| 新话题分类 | ACTIVITY_TYPES.md |
| 新执行策略 | STRATEGIES.md |
| 页面结构/选择器变化 | PATTERNS.md + STRATEGIES |
| 筛选/优先级规则变化 | SKILL.md (启发式规则) |
| 内容生成模板 | TEMPLATES.md |

用户确认流程：进化完成后生成同步建议 → 使用 `AskUserQuestion` 询问用户 → 确认后执行更新

## 工具配合

### Cookie 状态管理（优先使用）

**优先使用 toutiao-agent 的 ToutiaoClient**，它自动加载 `data/cookies.json`：

```python
from toutiao_agent.toutiao_client import ToutiaoClient

client = ToutiaoClient()
await client.start()  # 自动加载 data/cookies.json
# 执行操作...
await client.close()  # 自动保存 cookie
```

### 工具选择指南

| 操作场景 | 推荐工具 | 原因 |
|---------|---------|------|
| 登录、发布微头条 | toutiao-agent | 自动加载 cookie，完整流程支持 |
| 创作灵感页面探索 | ToutiaoClient | 继承 cookie 状态 |
| 话题内容分析 | ToutiaoClient | 继承 cookie 状态 |
| 快速页面截图 | playwright-cli + state-load | 方便快捷，但需手动加载 cookie |

## 参考资源

- **提示词风格指南**: See [PROMPT_STYLES.md](references/PROMPT_STYLES.md) for avoiding AI-style writing and creating engaging prompts
- **相关技能**: See [../toutiao-explorer/SKILL.md](../toutiao-explorer/SKILL.md) for activity exploration patterns

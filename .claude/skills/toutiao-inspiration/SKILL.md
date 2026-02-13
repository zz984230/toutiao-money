---
name: toutiao-inspiration
description: 头条创作灵感热门话题探索助手。使用此技能当：需要探索创作中心"创作灵感"下的热门话题、生成个性鲜明的微头条内容时。触发场景：用户说"帮我找热门话题"、"探索创作灵感"、"生成微头条内容"等。
---

# Toutiao Inspiration - 创作灵感热门话题探索

探索头条创作灵感热门话题、生成个性鲜明的微头条。

## 快速启动

```bash
# 1. 确保已登录（检查 cookie 文件）
ls data/cookies.json || uv run toutiao-agent login

# 2. 开始探索热门话题
# 让 AI 自动获取并分析热门话题
```

## 探索循环

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  登录检查 → 发现话题 → 选择话题 → 生成提示词 → 生成微头条 → 确认发布 → 验证记录 → 清理临时文件  │
│     ↑                                                                                    │
│     └──────── 未登录时先执行登录流程 ─────────────────────────────────────────────────────┘
└────────────────────────────────────────────────────────────────────────────────┘
```

### 0. 登录检查阶段（MUST DO）

**在任何探索操作之前，必须先确保登录状态**：

```bash
# 1. 检查 cookie 文件是否存在
ls -la data/cookies.json

# 2. 如果 cookie 文件不存在，提示缺少cookie；如果cookie文件存在，则使用cookie

# 3. 验证登录状态
uv run toutiao-agent activities --limit 1
```

**登录失败处理**：
- Cookie 过期 → 提示过期
- 需要验证码 → 使用非 headless 模式手动处理
- 网络错误 → 检查网络连接后重试

**重要**：每次会话开始时都应检查登录状态，避免后续操作失败。

### 1. 发现话题阶段

从创作灵感页面和相关内容中发现热门话题：使用.claude/skills/toutiao-inspiration/scripts/get_hotspot_topics_clean.py

```

**⚠️ 重要：避免重复选择已参与的话题**
- 使用 `storage.is_topic_participated()` 检查话题状态
- 已参与的话题在列表中显示 ✅，应跳过
- 除非是每日任务（如每日幸运签），否则不重复参与

### 2. 选择话题阶段

将发现的话题展示给用户，让用户选择要深入分析的话题。

**展示格式**：
```
热门话题列表：
1. #减肥# ✅ - 热度: 12345 (已参与，跳过)
2. #人工智能# - 热度: 9876
3. #春游# - 热度: 7654
4. #电影推荐# - 热度: 6543
5. #美食探店# - 热度: 5432
...
```

### 3. 生成提示词阶段

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

### 4. 生成微头条内容阶段

根据提示词生成 10-100 字的微头条内容。

**格式要求**：
- 内容开头或结尾必须包含 `#<话题>#` 标签
- 总字数控制在 10-100 字
- 风格与提示词保持一致

**话题标签示例**：
```
正确：#人工智能# 这个话题被夸大了
正确：我觉得大家对这个话题有误解 #人工智能#
错误：人工智能 - 缺少 # 和 #
```

### 5. 确认发布阶段（MUST FOLLOW）

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

### 6. 验证与记录阶段

发布成功后：
- 记录话题到 `storage.mark_topic_participated(topic_id, topic_name)`
- 保存发布截图作为证据

### 7. 清理临时文件阶段（MUST DO）

**发布完成后，必须清理过程中产生的临时文件**：

```bash
# 清理临时文件
uv run python .claude/skills/toutiao-inspiration/scripts/cleanup_temp_files.py

# 或者先查看将要删除的文件（dry-run 模式）
uv run python .claude/skills/toutiao-inspiration/scripts/cleanup_temp_files.py --dry-run

# 或者只列出临时文件，不删除
uv run python .claude/skills/toutiao-inspiration/scripts/cleanup_temp_files.py --list
```

**临时文件定义**：
- `data/temp_*.py` - 临时分析脚本
- `data/temp_*.json` - 临时数据文件
- `data/publish_weitou.py` - 临时发布脚本
- `data/published_screenshot.png` - 发布截图（每次发布会覆盖，可删除）
- `data/debug/*.png, *.html` - 调试文件（可选保留）

**保留文件**（不会被删除）：
- `data/cookies.json` - 登录状态
- `data/*.json` - 话题数据、已参与记录
- `.claude/data/*` - 技能数据目录

**清理时机**：每次发布任务完成后立即执行，避免临时文件积累。

## 失败处理

**遇到以下情况时的处理策略**：

```
Cookie过期/未登录 → 重新执行登录流程，保存新cookie
话题页面404/加载失败 → 先检查URL格式是否正确，再重试
话题卡片点击失败 → 改进选择器并重试
内容审核失败 → 调整内容策略后重试
话题提取失败 → 尝试方式 B，从他人内容中提取
未知错误 → 截图保存，咨询用户
```

**重要：不断尝试其他方法直到完成目标**

## 启发式规则

**话题来源优先级**：
```
创作灵感页面 > 从他人内容提取
高热度话题 > 低热度话题
反共识/争议性强 > 平庸观点
```

**探索控制**：
- 单次探索话题数：3-6 个
- 遇到高价值话题时，立即深入分析
- 发布成功后记录话题状态，避免重复

## 自适应学习

- 记录成功参与的话题模式
- 识别高频出现的观点类型
- 优化话题提取和提示词生成标准（失败类型自动调整）

---

## 进化模式

toutiao-inspiration 具备持续进化能力，能够从经验中学习和改进。

### 自动进化

在探索过程中遇到以下情况会自动触发进化：

1. **未知话题类型**：无法用现有模式分类的话题
2. **连续失败**：同一类型话题失败 3 次
3. **新页面结构**：检测到页面 DOM 结构变化
4. **话题提取失败**：创作灵感页面无法获取时，自动切换到从他人内容提取

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
| 话题提取方法 | SKILL.md (发现话题阶段) |

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
| 他人内容扫描 | ToutiaoClient | 继承 cookie 状态 |
| 快速页面截图 | playwright-cli + state-load | 方便快捷，但需手动加载 cookie |

## 参考资源

- **提示词风格指南**: See [PROMPT_STYLES.md](references/PROMPT_STYLES.md) for avoiding AI-style writing and creating engaging prompts
- **相关技能**: See [../toutiao-explorer/SKILL.md](../toutiao-explorer/SKILL.md) for activity exploration patterns

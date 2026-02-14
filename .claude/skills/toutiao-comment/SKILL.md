---
name: toutiao-comment
description: 头条评论自动化助手。使用此技能当：需要获取头条热点新闻、生成有观点的评论、交互确认后发布评论时。触发场景：用户说"帮我评论头条"、"获取热点新闻"、"发布评论"等。
---

# Toutiao Comment - 头条评论自动化

获取头条热点新闻、生成真人感评论、交互确认后发布。

## 快速启动

```bash
# 1. 确保已登录（检查 cookie 文件）
ls data/cookies.json || uv run toutiao-agent login

# 2. 开始评论流程
# 让 AI 自动获取热点新闻并生成评论
```

## 评论循环

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ 登录检查 → 获取热点新闻 → 选择新闻 → 生成评论 → 交互确认 → 发布评论 → 验证记录 │
│     ↑                                                                                    │
│     └──────── 未登录时先执行登录流程 ─────────────────────────────────────────────────────┘
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 0. 登录检查阶段（MUST DO）

**在任何评论操作之前，必须先确保登录状态**：

```bash
# 1. 检查 cookie 文件是否存在
ls -la data/cookies.json

# 2. 如果 cookie 文件不存在，提示缺少cookie；如果cookie文件存在，则使用cookie

# 3. 验证登录状态（使用 toutiao-agent 命令）
uv run toutiao-agent hot-news --limit 1
```

**重要提示**：
- `check_login_status()` 内部使用 `networkidle` 可能会超时（头条页面有持续后台请求）
- 优先使用 `toutiao-agent` 命令验证登录，而非直接调用 `client.ensure_login()`
- 如果 cookie 文件存在且较新，可直接跳过登录检查使用已保存的 Cookie

**登录失败处理**：
- Cookie 过期 -> 提示过期
- 需要验证码 -> 使用非 headless 模式手动处理
- 网络错误 -> 检查网络连接后重试
- `networkidle` 超时 -> 这是已知问题，可忽略直接使用 Cookie

---

## 1. 获取热点新闻阶段

从头条首页【热点】标签下获取热点新闻。【热点】标签位置：<div class="feed-default-nav-item active">热点</div>

**运行脚本**：
```bash
uv run python .claude/skills/toutiao-comment/scripts/get_hot_news.py
```

**URL**: `https://www.toutiao.com/`

**提取逻辑**：
1. 访问头条首页
2. 查找并点击【热点】标签
3. 提取热点新闻列表（标题、文章ID、链接）
4. 过滤已评论的文章（使用 `storage.is_commented()`）
5. 按热度排序
6. 保存到 `data/hot_news.json`

**展示格式**：
```
热点新闻列表：
1. 某地推出新政... (ID: 7400000000000000001)
2. 新品发布会... (ID: 7400000000000000002)
3. ...
```

---

## 2. 选择新闻阶段

将获取的热点新闻展示给用户，让用户选择要评论的文章。

**使用 AskUserQuestion 工具展示选项**：
```
请选择要评论的新闻：
1. 某地推出新政... (ID: 7400000000000000001)
2. 新品发布会... (ID: 7400000000000000002)
3. ...
```

---

## 3. 生成评论阶段

根据选择的新闻，生成有观点、有立场的评论内容。

**核心原则**（详见 [PROMPT_STYLES.md](references/PROMPT_STYLES.md)）：

1. **避免 AI 味**：
   - 不用"首先、其次、最后"等逻辑连接词
   - 不用"总的来说"、"值得注意的是"等 AI 套话
   - 多用口语化表达、网络用语

2. **真人感特征**：
   - 明确的立场或情绪
   - 短句、断句增加节奏感
   - 可以不完整的句子
   - 15-50字的长度

**评论策略**（详见 [STRATEGIES.md](references/STRATEGIES.md)）：
- 经验共鸣型：分享"个人经历"
- 补充信息型：提供文章未提及的信息
- 质疑反思型：对文章观点提出质疑
- 幽默调侃型：用轻松幽默的方式评论
- 实用建议型：针对问题提供可操作的建议

---

## 4. 交互确认阶段（MUST FOLLOW）

**在执行任何评论发布命令前，必须使用 `AskUserQuestion` 工具与用户确认**：

1. **展示评论预览**：
   - 文章标题
   - 生成的评论内容
   - 字数统计

2. **询问用户**：
   ```
   即将发布评论：

   文章：某地推出新政...
   评论：这政策挺好的，希望能落实到位。之前也出过类似政策，最后执行不力。这次希望能真解决问题。
   字数：38字

   是否确认发布？
   [确认发布] [取消] [修改内容]
   ```

**原则**：评论绝对不能自动发布出去！这是最高优先级的安全规则。

---

## 5. 发布评论阶段

用户确认后，执行评论发布。

**方法一：直接使用 ToutiaoClient（推荐）**

脚本 `publish_comment.py` 存在登录检查超时问题，建议直接使用 ToutiaoClient：

```python
from toutiao_agent.toutiao_client import ToutiaoClient
from toutiao_agent.storage import storage

client = ToutiaoClient()
await client.start()

try:
    # 直接发布（跳过 ensure_login，使用已保存的 Cookie）
    result = await client.post_comment(article_id, content)

    if result.get('success'):
        storage.add_comment(article_id=article_id, title=title, url=url, content=content)
        print('[SUCCESS] 评论已发布')
finally:
    await client.close()
```

**方法二：运行脚本（可能超时）**

```bash
uv run python .claude/skills/toutiao-comment/scripts/publish_comment.py <article_id> "<评论内容>"
```

**注意**：脚本内部调用 `ensure_login()` 可能因 `networkidle` 超时而失败。

---

## 6. 验证与记录阶段

发布成功后：
- 记录评论到 `storage.add_comment(article_id, content)`
- 保存发布截图作为证据（可选）

---

## 失败处理

**遇到以下情况时的处理策略**：

```
Cookie过期/未登录 -> 重新执行登录流程，保存新cookie
新闻页面404/加载失败 -> 先检查URL格式是否正确，再重试
评论发布失败 -> 调整评论内容后重试
未知错误 -> 截图保存，咨询用户
```

**常见问题：`networkidle` 超时**

- **原因**：头条页面有持续的后台请求（广告、统计、推荐等），导致永远无法达到 `networkidle` 状态（500ms 内少于 2 个网络连接）
- **解决方案**：
  1. 使用 `wait_until="domcontentloaded"` 或 `wait_until="load"`
  2. 如果 Cookie 文件存在且较新，跳过登录检查直接使用
  3. 优先使用 `toutiao-agent` 命令验证登录状态

---

## 编码注意事项

**临时脚本编码规范**：
1. **禁止使用 emoji**：临时写的脚本中不允许使用 emoji（如 [成功]、[失败] 等），Windows 终端可能不支持显示导致编码错误。使用文字替代。

---

## 启发式规则

**新闻选择优先级**：
```
热点新闻 > 普通新闻
高热度新闻 > 低热度新闻
未评论新闻 > 已评论新闻
```

**评论控制**：
- 单次评论新闻数：3-6 条
- 遇到高价值新闻时，立即深入分析
- 发布成功后记录新闻状态，避免重复

---

## 自适应学习

- 记录成功评论的新闻模式
- 识别高频出现的观点类型
- 优化评论生成标准（失败类型自动调整）

---

## 进化模式

toutiao-comment 具备持续进化能力，能够从经验中学习和改进。

### 自动进化

在评论过程中遇到以下情况会自动触发进化：

1. **未知新闻类型**：无法用现有模式分类的新闻
2. **连续失败**：同一类型新闻失败 3 次
3. **新页面结构**：检测到页面 DOM 结构变化
4. **新闻提取失败**：热点页面无法获取时，自动切换到备用方法

自动进化流程：检测 -> 分析 -> 测试 -> 记录 -> 恢复探索

### 主动进化

用户可主动调用进化模式进行深度优化：

```bash
# 复盘并优化策略
uv run toutiao-agent evolve --mode=review

# 分析特定新闻类型
uv run toutiao-agent evolve --mode=analyze --type="时政"

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
| 新评论分类 | COMMENT_TYPES.md |
| 新执行策略 | STRATEGIES.md |
| 页面结构/选择器变化 | SKILL.md + STRATEGIES |
| 筛选/优先级规则变化 | SKILL.md (启发式规则) |
| 内容生成模板 | TEMPLATES.md |
| 新闻提取方法 | SKILL.md (获取热点新闻阶段) |

用户确认流程：进化完成后生成同步建议 -> 使用 `AskUserQuestion` 询问用户 -> 确认后执行更新

---

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

### 脚本说明

- **get_hot_news.py**: 获取热点新闻列表
- **publish_comment.py**: 发布评论到指定文章

---

## 参考资源

- **评论风格指南**: See [PROMPT_STYLES.md](references/PROMPT_STYLES.md) for avoiding AI-style writing
- **评论策略指南**: See [STRATEGIES.md](references/STRATEGIES.md) for comment generation strategies

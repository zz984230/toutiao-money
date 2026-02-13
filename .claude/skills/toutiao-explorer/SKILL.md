---
name: toutiao-explorer
description: 头条激励任务探索助手。使用此技能当：需要探索、筛选并完成头条平台上的激励、奖金和流量任务时，包括活动发现、收益分析、策略制定和执行验证。
---

# Toutiao Explorer - 头条激励任务探索

自主探索、筛选并完成头条平台上的激励、奖金和流量任务。

## 快速启动

```bash
# 1. 安装 playwright-cli（首次使用）
npm install -g playwright-cli
# 或使用安装脚本：https://cloud.tencent.com/developer/article/2628720

# 2. 验证安装
playwright-cli --version

# 3. 开始探索
# 让 AI 自主探索活动并完成任务
```

## 探索循环

```
┌────────────────────────────────────────────────────────────────────┐
│  登录检查 → 发现 → 筛选 → 分析 → 执行 → 验证 → 反馈/进化  │
│     ↑                                                        │
│     └──────── 未登录时先执行登录流程 ─────────────────────────────┘
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
# 如果能正常获取活动列表，说明登录成功
```

**登录失败处理**：
- Cookie 过期 → 重新执行登录流程
- 需要验证码 → 使用非 headless 模式手动处理
- 网络错误 → 检查网络连接后重试

**重要**：每次会话开始时都应检查登录状态，避免后续操作失败。

### 1. 发现阶段
- 调用 `toutiao-agent activities --limit 10` 获取活动列表
- 使用 playwright-cli 访问活动详情页，分析页面结构
- 网络查询最新活动信息（"头条活动 激励 2026"）
- 关注：创作者中心、活动广场、话题榜

### 2. 筛选阶段
多维度过滤活动：
- **参与方式**：原创内容 vs 一键参与 vs 点赞转发
- **收益类型**：现金激励 > 流量扶持 > 荣誉奖励
- **时间成本**：优先高收益/低耗时、短周期活动
- **可行性**：检查是否需要APP、是否仍在进行中

### 3. 分析阶段
- 解读活动规则（阅读量要求、内容格式、话题标签）
- 识别潜在风险（审核敏感词、频率限制）
- 计算预期收益与成本比

### 4. 执行阶段
- 根据活动类型选择策略
- 使用 toutiao-agent 命令执行（发布微头条、参与活动等）
- 使用 playwright-cli 处理复杂交互（点击按钮、填写表单）

#### 🔴 关键安全确认环节（MUST FOLLOW）

**在以下任何操作前，必须使用 `AskUserQuestion` 工具与用户确认**：

1. **发布微头条前**：在执行任何微头条发布命令前
   - 展示即将发布的内容预览
   - 说明活动背景和预期收益
   - 询问：`是否确认发布此微头条？`
   - 选项：`[确认发布] [取消] [修改内容]`

2. **点击转发前**：在执行最终转发操作前
   - 展示目标文章/活动信息
   - 询问：`是否确认转发此内容？`
   - 选项：`[确认转发] [取消]`

3. **其他不可逆操作前**：包括但不限于
   - 提交评论
   - 点赞/收藏（批量操作时）
   - 关注作者/话题
   - 参与抽奖/投票

**原则**：任何会改变用户账号状态或产生公开内容的操作，都必须先获得用户明确同意。

**尤其重要**：微头条绝对不能自动发布出去！这是最高优先级的安全规则。

### 5. 验证阶段
- 检查参与成功状态（页面提示、按钮状态变化）
- 使用 playwright-cli 截图保存证据
- 记录结果到数据库

## 启发式规则

**收益优先级**：
```
现金激励 > 流量扶持 > 荣誉奖励
高收益/低成本 > 中等收益/中等成本 > 低收益/高成本
短周期活动 > 长周期活动（快速验证）
```

**可行性筛选**：
```
网页可完成 > 需要APP扫码
已知活动类型 > 未知新型活动
已验证可重复 > 首次尝试的活动

⚠️ 重要：避免重复参与已参与的活动
- 使用 storage.is_activity_participated() 检查活动状态
- 已参与的活动在列表中显示 ✅，应跳过
- 除非是每日任务（如每日幸运签），否则不重复参与
```

**探索控制**：
- 单次探索活动数：5-10 个
- 遇到高价值活动时，立即深入分析
- 并行探索多个活动以提高效率

**失败处理**：
```
Cookie过期/未登录 → 重新执行登录流程，保存新cookie
活动已结束 → 跳过，记录状态
需要APP → 标记为低优先级，使用 `is_activity_skipped_for_app()` 检查
内容审核 → 调整内容策略后重试
页面404/加载失败 → 先检查URL格式是否正确，再重试（E009改进）
  - 活动：确保使用 activity.href
  - 新闻：确保使用 www.toutiao.com/article/{id}/ 格式
  - 使用 verify_page_loaded() 验证页面内容
  - 点击活动卡片后验证URL是否包含activity_id
活动卡片点击失败 → 使用 participate_from_activity_page() 完整流程（E009新增）
  - 打开创作者中心 → 点击活动卡片 → 验证页面 → 发布内容
未知错误 → 截图保存，咨询用户
```

## 按需参考文档

- **playwright-cli**: See [PLAYWRIGHT_CLI.md](references/PLAYWRIGHT_CLI.md) for installation and core commands
- **活动分类**: See [ACTIVITY_TYPES.md](references/ACTIVITY_TYPES.md) for activity classification patterns
- **执行策略**: See [STRATEGIES.md](references/STRATEGIES.md) for execution strategies by activity type
- **收益分析**: See [EVALUATION.md](references/EVALUATION.md) for cost-benefit analysis methods
- **常见模式**: See [PATTERNS.md](references/PATTERNS.md) for recurring activity patterns
- **进化日志**: See [EVOLUTION.md](references/EVOLUTION.md) for evolution history and learned patterns

## 工具配合

### Cookie 状态管理（优先使用）

**优先使用 toutiao-agent 的 ToutiaoClient**，它自动加载 `data/cookies.json`：
- 自动检查并加载已保存的 cookie
- 登录成功后自动保存 cookie 状态
- 确保所有操作在已登录状态下执行

```python
# ToutiaoClient 自动处理 cookie
from toutiao_agent.toutiao_client import ToutiaoClient

client = ToutiaoClient()
await client.start()  # 自动加载 data/cookies.json
# 执行操作...
await client.close()  # 自动保存 cookie
```

**使用 playwright-cli 时的注意事项**：
- playwright-cli 默认不加载 cookie，可能导致页面 404 或未登录错误
- 如需使用 playwright-cli，必须先加载 cookie 状态：
  ```bash
  playwright-cli state-load data/cookies.json
  ```

### URL 格式规范（E008进化）

**⚠️ 常见错误：直接构造URL会导致404**

| 资源类型 | ❌ 错误格式 | ✅ 正确格式 |
|---------|-------------|-------------|
| 活动页面 | `https://m.toutiao.com/is/{id}/` | 使用 `activity.href` 字段 |
| 新闻详情 | `https://m.toutiao.com/i/{id}/` | `https://www.toutiao.com/article/{id}/` |

**正确做法**：
```python
# 活动访问 - 使用API返回的href
activities = activity_fetcher.fetch_activities(limit=10)
activity_url = activities[0].href  # ✅ 正确

# 新闻详情 - 使用正确格式
news_url = f"https://www.toutiao.com/article/{article_id}/"  # ✅ 正确
```

**href字段可能的格式**：
- `https://mp.toutiao.com/profile_v3_public/public/activity/?id={activity_id}`（创作者中心活动页）
- `https://api.toutiaoapi.com/magic/eco/runtime/release/...`（活动运行时页面）

### 工具选择指南

| 操作场景 | 推荐工具 | 原因 |
|---------|---------|------|
| 登录、发布微头条 | toutiao-agent | 自动加载 cookie，完整流程支持 |
| 活动列表获取 | toutiao-agent | 需要登录状态 |
| 活动页面分析 | ToutiaoClient | 继承 cookie 状态 |
| **活动参与（正确流程）** | **`participate_from_activity_page()`** | **E009新增：确保从活动页面发布** |
| 快速页面截图 | playwright-cli + state-load | 方便快捷，但需手动加载 cookie |

- **toutiao-agent**: 处理登录、微头条发布、基础活动参与（自动加载 cookie）
- **playwright-cli**: 页面探索、状态检测、证据截图（需手动 state-load）

**E009 重要更新**：
- 新增 `verify_page_loaded()` - 验证页面内容是否正确加载（检测404、空页面）
- 新增 `participate_from_activity_page()` - 完整的活动参与流程
  - 打开创作者中心
  - 点击活动卡片（改进的选择器+重试）
  - 验证页面加载
  - 从活动页面发布内容
- 新增 `is_activity_skipped_for_app()` - 检查活动是否因需要APP而被跳过

### 网络搜索边界

**网络搜索仅用于技术问题**：
- ✅ **适用场景**：工具使用、技能操作、代码语法、页面操作方法
- ❌ **不适用场景**：头条活动参与方式、规则等业务问题

**原因**：
- 头条活动规则经常变化，网络搜索结果可能过时或错误
- 直接通过页面探索获取的规则更可靠
- 业务规则应从头条官方页面获取

**正确做法**：
- 活动规则 → 通过 ToutiaoClient 访问活动页面获取
- 活动参与方式 → 分析页面元素和按钮操作流程
- 仅当需要了解技术问题（如 Playwright API 使用）时才使用网络搜索

## 自适应学习

- 记录成功参与的活动模式
- 识别高频出现的活动类型
- 优化筛选标准（失败类型自动降优先级）

---

## 进化模式

toutiao-explorer 具备持续进化能力，能够从经验中学习和改进。

### 自动进化

在探索过程中遇到以下情况会自动触发进化：

1. **未知活动类型**：无法用现有模式分类的活动
2. **连续失败**：同一类型活动失败 3 次
3. **新页面结构**：检测到页面 DOM 结构变化

自动进化流程：检测 → 分析 → 测试 → 记录 → 恢复探索

### 主动进化

用户可主动调用进化模式进行深度优化：

```bash
# 复盘并优化策略
uv run toutiao-agent evolve --mode=review

# 分析特定活动类型
uv run toutiao-agent evolve --mode=analyze --type="视频抽奖"

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
| 新增活动模式 | PATTERNS.md |
| 新活动分类 | ACTIVITY_TYPES.md |
| 新执行策略 | STRATEGIES.md |
| 页面结构/选择器变化 | PATTERNS.md + STRATEGIES |
| 筛选/优先级规则变化 | SKILL.md (启发式规则) |
| 内容生成模板 | TEMPLATES.md |
| 收益分析方法 | EVALUATION.md |

用户确认流程：进化完成后生成同步建议 → 使用 `AskUserQuestion` 询问用户 → 确认后执行更新

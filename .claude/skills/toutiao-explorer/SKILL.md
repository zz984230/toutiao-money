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
┌─────────────────────────────────────────────────────────┐
│  发现 → 筛选 → 分析 → 执行 → 验证 → 反馈   │
│                ↑                                    │
│                └──────── 迭代优化 ───────────────────┘
└─────────────────────────────────────────────────────────┘
```

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
```

**探索控制**：
- 单次探索活动数：5-10 个
- 遇到高价值活动时，立即深入分析
- 并行探索多个活动以提高效率

**失败处理**：
```
活动已结束 → 跳过，记录状态
需要APP → 标记为低优先级
内容审核 → 调整内容策略后重试
未知错误 → 截图保存，咨询用户
```

## 按需参考文档

- **playwright-cli**: See [PLAYWRIGHT_CLI.md](references/PLAYWRIGHT_CLI.md) for installation and core commands
- **活动分类**: See [ACTIVITY_TYPES.md](references/ACTIVITY_TYPES.md) for activity classification patterns
- **执行策略**: See [STRATEGIES.md](references/STRATEGIES.md) for execution strategies by activity type
- **收益分析**: See [EVALUATION.md](references/EVALUATION.md) for cost-benefit analysis methods
- **常见模式**: See [PATTERNS.md](references/PATTERNS.md) for recurring activity patterns

## 工具配合

- **toutiao-agent skill**: 处理登录、微头条发布、基础活动参与
- **playwright-cli**: 页面探索、状态检测、证据截图
- **网络查询**: 获取最新活动信息和规则解读

## 自适应学习

- 记录成功参与的活动模式
- 识别高频出现的活动类型
- 优化筛选标准（失败类型自动降优先级）

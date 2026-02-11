# PRD: 自动抓取活动话题

**日期**: 2025-02-11
**版本**: 1.0
**WINNING 评分**: 48/60 🟢 FILE
**优先级**: P0 (最高)
**依赖**: 为"发布微头条功能"提供数据支持

---

## 问题陈述 (Problem Statement)

### 当前痛点
用户需要手动查找今日头条平台的活动话题，耗时且容易遗漏高价值活动。

### 业务影响
- **效率低下**: 手动浏览活动页面浪费时间
- **遗漏机会**: 可能错过时间敏感的活动
- **信息不全**: 活动要求、截止时间等信息需要手动记录

### 成功定义
系统能够自动抓取并解析当前所有可用活动，提供完整信息供后续内容生成使用。

---

## 用户故事 (User Stories)

### 主要故事
```
作为自媒体运营者，
我想要自动获取平台当前的活动话题列表，
以便快速了解参与机会并选择合适的活动。
```

### 详细场景

#### 场景 1: 查看活动列表
**Given** 平台有多个活动进行中
**When** 我运行 `toutiao-agent activities` 命令
**Then** 显示所有活动的摘要信息

#### 场景 2: 查看活动详情
**Given** 我对某个活动感兴趣
**When** 我运行 `toutiao-agent activity <activity_id>` 命令
**Then** 显示该活动的详细要求（话题标签、字数、截止时间）

#### 场景 3: 过滤活动
**Given** 活动列表很长
**When** 我使用 `--filter` 参数筛选
**Then** 只显示符合条件（如未结束、高奖励）的活动

#### 场景 4: 活动订阅
**Given** 我不想错过新活动
**When** 新活动发布时
**Then** 系统通知我有新活动可用

---

## 竞争分析 (Competitive Analysis)

### 竞品现状
| 产品 | 活动抓取 | 自动解析 | 实时更新 |
|------|----------|----------|----------|
| **Octopus RPA** | 关键词筛选 | 通用 | 手动触发 |
| **Riona AI Agent** | ❌ 无 | ❌ 无 | ❌ 无 |
| **TTBot** | ❌ 无 | ❌ 无 | ❌ 无 |

### 差异化机会
- **垂直专精**: 专注头条活动，深度解析
- **结构化数据**: 提供机器可读的活动信息
- **智能过滤**: 根据用户偏好筛选活动

---

## 功能需求 (Functional Requirements)

### P0 (必须实现)

#### FR-1: 活动列表抓取
- 从活动广场页面抓取活动列表
- 支持多个活动来源（话题活动、创作活动等）
- 处理分页加载

#### FR-2: 活动信息解析
解析以下字段：
- 活动ID (activity_id)
- 活动标题 (title)
- 活动描述 (description)
- 话题标签 (hashtag) - 如 #科技话题#
- 字数要求 (min_length, max_length)
- 截止时间 (deadline)
- 奖励信息 (reward)
- 参与人数 (participants)

#### FR-3: 活动状态判断
- 判断活动是否已结束
- 判断活动是否可参与
- 过滤无效活动

#### FR-4: 数据缓存
- 本地缓存活动数据
- 设置合理的过期时间（如 1 小时）
- 支持强制刷新

#### FR-5: CLI 命令
```bash
# 查看活动列表
toutiao-agent activities

# 查看活动详情
toutiao-agent activity show <activity_id>

# 刷新活动列表
toutiao-agent activities --refresh

# 过滤活动
toutiao-agent activities --filter "status:active,reward:high"

# 导出活动数据
toutiao-agent activities --output json
```

### P1 (重要增强)

#### FR-6: 多来源聚合
- 支持多个活动页面
- 合并重复活动
- 统一数据格式

#### FR-7: 活动搜索
- 按关键词搜索活动
- 按话题标签筛选
- 按奖励类型筛选

#### FR-8: 活动推荐
- 根据历史参与记录推荐
- 根据账号类型推荐
- 显示推荐理由

#### FR-9: 活动监控
- 定时检查新活动
- 新活动通知（CLI 提示）
- 活动状态变化提醒

### P2 (未来优化)

#### FR-10: 活动分析
- 分析活动历史数据
- 预测活动参与效果
- 生成活动报告

#### FR-11: 活动日历
- 显示活动时间线
- 提醒即将结束的活动
- 规划发布时间

---

## 非功能需求 (Non-Functional Requirements)

### NFR-1: 性能
- 抓取活动列表 < 5 秒
- 解析单个活动 < 1 秒
- 缓存命中 < 0.1 秒

### NFR-2: 准确性
- 信息解析准确率 > 95%
- 时间解析准确到分钟
- 标签格式标准化

### NFR-3: 可靠性
- 抓取失败自动重试
- 解析失败降级处理
- 提供原始数据备份

### NFR-4: 可扩展性
- 易于添加新的活动来源
- 数据模型支持扩展字段
- 选择器配置化

---

## 验收标准 (Acceptance Criteria)

### P0 验收

| ID | 标准 | 验证方法 |
|----|------|----------|
| AC-1 | 能获取活动列表 | 命令返回至少 1 个活动 |
| AC-2 | 正确解析活动字段 | 所有必需字段都有值 |
| AC-3 | 过滤已结束活动 | 列表中无过期活动 |
| AC-4 | 缓存正常工作 | 第二次调用使用缓存 |
| AC-5 | CLI 命令可用 | 所有命令正常执行 |

### P1 验收

| ID | 标准 | 验证方法 |
|----|------|----------|
| AC-6 | 多来源合并 | 不显示重复活动 |
| AC-7 | 搜索功能可用 | 关键词搜索返回正确结果 |
| AC-8 | 推荐合理 | 推荐活动符合用户偏好 |

---

## 边缘情况 (Edge Cases)

| 情况 | 处理方式 |
|------|----------|
| 无活动可用 | 提示"当前无活动" |
| 活动页面结构变化 | 记录原始 HTML，便于调试 |
| 活动信息不完整 | 标记为 incomplete，提供可用字段 |
| 活动链接失效 | 跳过该活动，记录错误 |
| 活动重复 | 使用第一次抓取的数据 |
| 时间格式不统一 | 尝试多种格式解析 |
| 网络超时 | 重试 3 次，超时返回缓存数据 |

---

## 不在范围内 (Out of Scope)

- ❌ 活动内容生成（由"发布微头条功能"负责）
- ❌ 活动参与统计
- ❌ 活动效果分析
- ❌ 跨平台活动（仅头条）
- ❌ 私密活动/邀请活动

---

## 技术考量 (Technical Considerations)

### 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Commands                         │
│  activities | activity show | activity search           │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   ActivityFetcher                        │
│  ┌──────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │PageScraper   │  │ActivityParser│  │CacheManager   │  │
│  └──────────────┘  └─────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   Playwright Browser                     │
│  • 访问活动页面                                          │
│  • 提取活动数据                                          │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   SQLite Cache                           │
│  • 活动数据缓存                                          │
│  • 抓取历史记录                                          │
└─────────────────────────────────────────────────────────┘
```

### 关键实现点

#### 1. 活动页面 URL
```python
# 需要调研的活动页面
ACTIVITY_URLS = [
    "https://www.toutiao.com/activity/",           # 活动广场
    "https://www.toutiao.com/c/user/activity/",    # 个人活动中心
    "https://www.toutiao.com/topic/",              # 话题广场
]
```

#### 2. 活动数据模型
```python
@dataclass
class Activity:
    activity_id: str
    title: str
    description: str = ""
    hashtag: str = ""           # 如 #科技话题#
    min_length: int = 0
    max_length: int = 500
    deadline: Optional[datetime] = None
    reward: str = ""
    participants: int = 0
    status: str = "active"      # active/ended/invalid
    source_url: str = ""
    fetched_at: datetime = field(default_factory=datetime.now)
```

#### 3. 选择器配置
```python
# config/activity_selectors.yaml
activity_list:
  container: ".activity-list, .topic-list"
  item: ".activity-item, .topic-item"
  title: ".title, h3, h4"
  link: "a[href*='activity']"
  deadline: ".deadline, .end-time"

activity_detail:
  hashtag: ".hashtag, .topic-tag"
  requirements: ".requirements, .rules"
  reward: ".reward, .prize"
```

### 数据存储

```sql
-- 新增表
CREATE TABLE activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id TEXT UNIQUE,
    title TEXT,
    description TEXT,
    hashtag TEXT,
    min_length INTEGER DEFAULT 0,
    max_length INTEGER DEFAULT 500,
    deadline TEXT,
    reward TEXT,
    participants INTEGER DEFAULT 0,
    status TEXT,
    source_url TEXT,
    fetched_at TEXT,
    updated_at TEXT
);

-- 索引
CREATE INDEX idx_activities_status ON activities(status);
CREATE INDEX idx_activities_deadline ON activities(deadline);
```

---

## 成功指标 (Success Metrics)

| 指标 | 目标 | 测量方式 |
|------|------|----------|
| 抓取成功率 | >90% | 成功抓取/总尝试 |
| 解析准确率 | >95% | 字段完整/总活动 |
| 缓存命中率 | >70% | 缓存命中/总请求 |
| 命令响应时间 | <5秒 | 端到端计时 |

---

## 依赖项 (Dependencies)

| 依赖 | 状态 | 说明 |
|------|------|------|
| Playwright | ✅ 已有 | 浏览器自动化 |
| SQLite | ✅ 已有 | 数据存储 |
| 活动页面调研 | ⏳ 待完成 | 确定页面结构和选择器 |

---

## 风险与缓解 (Risks & Mitigations)

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 活动页面结构变化 | 高 | 选择器配置化，多版本备份 |
| 反爬虫限制 | 中 | 降低请求频率，使用缓存 |
| 活动格式不统一 | 中 | 多种解析策略，容错处理 |
| 活动信息缺失 | 低 | 标记 incomplete，提供默认值 |

---

## 实施计划 (Implementation Plan)

### Phase 1: 调研 (1天)
- [ ] 确定活动页面 URL
- [ ] 分析页面结构
- [ ] 确定数据字段

### Phase 2: 核心抓取 (2-3天)
- [ ] 实现活动列表抓取
- [ ] 实现活动信息解析
- [ ] 实现缓存机制

### Phase 3: 命令行 (1-2天)
- [ ] 实现 CLI 命令
- [ ] 实现过滤和搜索
- [ ] 实现数据导出

### Phase 4: 增强功能 (1-2天)
- [ ] 多来源聚合
- [ ] 活动推荐
- [ ] 活动监控

**预计总时间**: 5-8 天

---

## 参考资料 (References)

- 产品清单: `.pm/product/inventory.md`
- 差距分析: `.pm/gaps/2025-02-11-analysis.md`
- 微头条 PRD: `.pm/prds/micro-headline-posting.md`
- 现有架构: `src/toutiao_agent/`

---

## GitHub Issue 标签

```
pm:feature-request
winning:high (48/60)
priority:now
scope:activity-fetcher
dependency:micro-headline
```

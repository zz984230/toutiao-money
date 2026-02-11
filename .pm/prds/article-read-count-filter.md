# PRD: 文章阅读量筛选

**日期**: 2025-02-11
**版本**: 1.0
**WINNING 评分**: 40/60 🟢 FILE
**优先级**: P0 (高)
**用户评分难度**: 3/10 (较易实现)

---

## 问题陈述 (Problem Statement)

### 当前痛点
热点新闻抓取后无法按阅读量筛选，可能对低阅读量文章进行评论，导致引流效果差。

### 业务影响
- **效率低下**: 在低价值文章上浪费时间
- **引流效果差**: 低阅读量文章评论曝光少
- **转化率低**: 无法精准选择高潜力内容

### 成功定义
系统能够获取文章阅读量，并根据配置的阈值筛选出高价值文章进行评论。

---

## 用户故事 (User Stories)

### 主要故事
```
作为自媒体运营者，
我想要只对高阅读量的文章发表评论，
以便提高评论曝光和引流效果。
```

### 详细场景

#### 场景 1: 按阅读量筛选热点
**Given** 抓取了 20 条热点新闻
**When** 我设置了最低阅读量为 10000
**Then** 只显示阅读量 >= 10000 的文章

#### 场景 2: 配置阅读量阈值
**Given** 我想调整筛选标准
**When** 我修改 config.yaml 中的 min_read_count
**Then** 下次运行使用新阈值

#### 场景 3: 显示文章阅读量
**Given** 查看热点列表
**When** 文章有阅读量数据
**Then** 显示阅读量信息（如 "👁️ 1.2万"）

#### 场景 4: 阅读量不足提示
**Given** 抓取的热点阅读量都不高
**When** 筛选后剩余文章 < 5 条
**Then** 提示"是否降低阈值？"并等待确认

---

## 竞争分析 (Competitive Analysis)

### 竞品现状
| 产品 | 阅读量筛选 | 互动量筛选 | 自定义阈值 |
|------|-----------|-----------|-----------|
| **Octopus RPA** | 关键词筛选 | 未知 | 支持 |
| **Riona AI Agent** | ❌ 无 | ❌ 无 | ❌ 无 |
| **TTBot** | ❌ 无 | go_detail_count | 硬编码 |

### 差异化机会
- **灵活配置**: 支持多种筛选维度
- **智能建议**: 根据历史数据推荐阈值
- **多维排序**: 支持按阅读量/评论量排序

---

## 功能需求 (Functional Requirements)

### P0 (必须实现)

#### FR-1: 获取文章阅读量
- 访问文章详情页获取阅读量
- 解析 go_detail_count 字段
- 处理单位转换（万、亿）

#### FR-2: 阅读量筛选
- 根据配置的 min_read_count 过滤
- 支持动态调整阈值
- 筛选不足时智能提示

#### FR-3: 显示阅读量信息
- 在热点列表中显示阅读量
- 格式化显示（1.2万、500万等）
- 无数据时显示"N/A"

#### FR-4: 配置集成
- 在 config.yaml 中配置阈值
- 支持 confirmation_mode 确认
- 与现有筛选逻辑兼容

#### FR-5: CLI 增强显示
```bash
# 热点列表显示阅读量
toutiao-agent hot-news --limit 20

# 输出示例：
1. 科技新闻：AI 技术新突破
   👁️ 阅读量：12.5万  💬 评论：856  ID: 712345678
```

### P1 (重要增强)

#### FR-6: 多维度筛选
- 支持按评论量筛选
- 支持按点赞数筛选
- 支持按分享数筛选
- 组合筛选条件

#### FR-7: 排序功能
- 按阅读量降序
- 按评论量降序
- 按互动率降序

#### FR-8: 智能阈值建议
- 分析历史数据
- 推荐合适的阈值
- 显示分布情况

#### FR-9: 筛选统计
- 显示筛选前后数量
- 显示被过滤原因
- 生成筛选报告

### P2 (未来优化)

#### FR-10: 阅读量趋势
- 追踪文章阅读量变化
- 预测爆款潜力
- 推荐最佳评论时机

#### FR-11: A/B 测试
- 测试不同阈值效果
- 分析转化率
- 优化筛选策略

---

## 非功能需求 (Non-Functional Requirements)

### NFR-1: 性能
- 单篇文章阅读量获取 < 2 秒
- 批量获取（并发）< 10 秒/20篇
- 不显著增加现有运行时间

### NFR-2: 准确性
- 阅读量解析准确率 > 95%
- 单位转换正确（万/亿）
- 边界值处理正确

### NFR-3: 可靠性
- 获取失败时显示"N/A"
- 不影响评论流程
- 降级到原始筛选方式

### NFR-4: 可配置性
- 阈值可灵活调整
- 筛选维度可选
- 显示格式可定制

---

## 验收标准 (Acceptance Criteria)

### P0 验收

| ID | 标准 | 验证方法 |
|----|------|----------|
| AC-1 | 能获取文章阅读量 | 热点列表显示阅读量 |
| AC-2 | 筛选功能正常 | 低阅读量文章被过滤 |
| AC-3 | 配置生效 | 修改阈值后筛选结果变化 |
| AC-4 | 格式化显示正确 | 12500 显示为 "1.25万" |
| AC-5 | 不影响现有功能 | 评论流程正常运行 |

### P1 验收

| ID | 标准 | 验证方法 |
|----|------|----------|
| AC-6 | 多维度筛选可用 | 能按评论量筛选 |
| AC-7 | 排序功能正常 | 能按阅读量排序 |
| AC-8 | 智能建议合理 | 推荐阈值符合实际 |

---

## 边缘情况 (Edge Cases)

| 情况 | 处理方式 |
|------|----------|
| 阅读量获取失败 | 显示"N/A"，不参与筛选 |
| 所有文章都不达标 | 提示降低阈值或使用全部 |
| 阅读量格式异常 | 尝试解析，失败则标记为 N/A |
| 阈值设置过高 | 警告并建议合理范围 |
| 阅读量为 0 | 正常处理，可能被过滤 |
| 无阅读量字段 | 标记为 N/A，降级到标题筛选 |

---

## 不在范围内 (Out of Scope)

- ❌ 阅读量历史追踪
- ❌ 阅读量预测
- ❌ 跨平台阅读量对比
- ❌ 阅读量造假检测
- ❌ 复杂的筛选逻辑（如正则表达式）

---

## 技术考量 (Technical Considerations)

### 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Commands                         │
│  hot-news | start | comment                             │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   HotNewsFilter                          │
│  ┌──────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │ReadCountParser│  │FilterEngine│  │DisplayFormatter│ │
│  └──────────────┘  └─────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   Playwright Browser                     │
│  • 访问文章详情页                                        │
│  • 提取阅读量数据                                        │
└─────────────────────────────────────────────────────────┘
```

### 关键实现点

#### 1. 阅读量解析
```python
# 需要解析的字段
go_detail_count  # 阅读量
comments_count   # 评论量
likes_count      # 点赞数（可选）
shares_count     # 分享数（可选）
```

#### 2. 选择器配置
```python
# 文章详情页阅读量选择器
READ_COUNT_SELECTORS = [
    ".read-count",
    "[data-field='read-count']",
    ".view-count",
    "span:has-text('阅读')",
]
```

#### 3. 单位转换
```python
def parse_read_count(text: str) -> int:
    """解析阅读量文本，返回数值"""
    text = text.strip().replace(",", "")

    # 处理单位
    if "万" in text:
        return int(float(text.replace("万", "")) * 10000)
    elif "亿" in text:
        return int(float(text.replace("亿", "")) * 100000000)
    else:
        return int(text)

def format_read_count(count: int) -> str:
    """格式化显示阅读量"""
    if count >= 100000000:
        return f"{count / 100000000:.1f}亿"
    elif count >= 10000:
        return f"{count / 10000:.1f}万"
    else:
        return str(count)
```

### 数据模型扩展

```python
@dataclass
class Article:
    article_id: str
    title: str
    url: str = ""
    abstract: str = ""

    # 新增字段
    read_count: Optional[int] = None
    comments_count: Optional[int] = None
    likes_count: Optional[int] = None
    shares_count: Optional[int] = None
    engagement_rate: Optional[float] = None  # 互动率

    def format_read_count(self) -> str:
        if self.read_count is None:
            return "N/A"
        return format_read_count(self.read_count)
```

### 配置扩展

```yaml
# config.yaml 新增配置
behavior:
  min_read_count: 10000        # 最低阅读量（0=不筛选）
  min_comments: 0              # 最低评论数
  sort_by: "read_count"        # 排序字段: read_count/comments_count/time
  sort_order: "desc"           # desc/asc

display:
  show_read_count: true        # 显示阅读量
  show_comments: true          # 显示评论数
  show_engagement: false       # 显示互动率
```

---

## 成功指标 (Success Metrics)

| 指标 | 目标 | 测量方式 |
|------|------|----------|
| 阅读量获取成功率 | >80% | 成功获取/总文章 |
| 筛选准确性 | >95% | 筛选结果符合条件 |
| 平均增量耗时 | <5秒 | (新流程 - 旧流程)/20篇 |

---

## 依赖项 (Dependencies)

| 依赖 | 状态 | 说明 |
|------|------|------|
| Playwright | ✅ 已有 | 浏览器自动化 |
| 现有筛选逻辑 | ✅ 已有 | 去重等 |
| 文章详情页 | ⏳ 待确认 | 确定选择器 |

---

## 风险与缓解 (Risks & Mitigations)

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 阅读量字段不存在 | 中 | 降级到原始筛选，显示 N/A |
| 选择器失效 | 中 | 多选择器备份 |
| 性能影响 | 低 | 并发获取，缓存结果 |
| 阈值设置不合理 | 低 | 智能推荐，动态调整 |

---

## 实施计划 (Implementation Plan)

### Phase 1: 调研 (0.5天)
- [ ] 确认阅读量字段位置
- [ ] 测试解析逻辑
- [ ] 确定选择器

### Phase 2: 核心功能 (1-2天)
- [ ] 实现阅读量获取
- [ ] 实现筛选逻辑
- [ ] 实现格式化显示

### Phase 3: 集成 (1天)
- [ ] 集成到现有命令
- [ ] 更新配置文件
- [ ] 更新 CLI 显示

### Phase 4: 增强功能 (1-2天)
- [ ] 多维度筛选
- [ ] 排序功能
- [ ] 智能建议

**预计总时间**: 3.5-5.5 天

---

## 参考资料 (References)

- 产品清单: `.pm/product/inventory.md`
- 差距分析: `.pm/gaps/2025-02-11-analysis.md`
- 现有架构: `src/toutiao_agent/`
- TTBot 参考: go_detail_count 字段

---

## GitHub Issue 标签

```
pm:feature-request
winning:high (40/60)
priority:now
scope:article-filter
difficulty:easy
```

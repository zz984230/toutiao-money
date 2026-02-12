# 活动智能参与系统设计文档

## 概述

**目标**：实现智能活动参与系统，根据活动页面自动选择参与方式，提升用户体验和自动化程度。

**核心流程**：
```
用户确认参与活动
    ↓
使用 playwright-cli 获取活动页面信息
    ↓
AI 分析页面，提取活动内容 + 操作类型
    ↓
显示活动内容 + AI 参与建议 + 置信度
    ↓
用户确认操作方式
    ↓
执行相应操作 → 记录到数据库
```

## 操作类型分类

| 类型 | 说明 | 示例 |
|------|------|------|
| 【生成原创】 | 根据活动说明生成微头条内容并发布 | 话题讨论活动 |
| 【点赞转发】 | 点赞/转发活动页内容 | 转发有奖活动 |
| 【填写表单】 | 在活动页填写信息并提交 | 报名类活动 |
| 【一键参与】 | 点击"立即参与"按钮完成 | 简单参与活动 |
| 【其他】 | 需要人工处理的其他类型 | 复杂交互活动 |

## 架构设计

### 新增组件

1. **ActivityAnalyzer** (activity_analyzer.py)
   - 使用 playwright-cli 获取页面信息
   - 调用 AI 分析页面结构和活动内容
   - 返回结构化的分析结果

2. **ActionResult 数据结构**
   ```python
   {
       'activity_title': str,      # 活动标题
       'activity_intro': str,      # 活动介绍
       'operation_type': str,      # 操作类型
       'confidence': float,        # 置信度 0-1
       'detected_elements': dict, # 检测到的元素
       'suggested_action': str     # 建议操作描述
   }
   ```

3. **playwright-cli 集成**
   - 截图命令：用于 AI 视觉分析
   - 元素提取命令：获取可交互元素列表
   - 页面文本提取命令：获取活动说明

### 修改现有组件

- `main.py:start_activities_cmd` - 添加活动分析流程
- `toutiao_client.py` - 添加各类操作执行方法

## 接口设计

### ActivityAnalyzer 类

```python
class ActivityAnalyzer:
    async def analyze(self, activity: Activity) -> ActionResult:
        """分析活动页面，返回操作建议

        Args:
            activity: Activity 对象

        Returns:
            ActionResult 包含操作类型、活动内容、置信度等
        """
        pass
```

### ActionResult 类

```python
@dataclass
class ActionResult:
    activity_title: str           # 活动标题
    activity_intro: str           # 活动介绍
    operation_type: OperationType # 操作类型枚举
    confidence: float             # 置信度 0-1
    detected_elements: dict       # 检测到的元素
    suggested_action: str         # 建议操作描述

    def to_dict(self) -> dict:
        """转换为字典，用于存储"""
        pass
```

### OperationType 枚举

```python
class OperationType(Enum):
    GENERATE_CONTENT = "generate_content"    # 生成原创
    LIKE_SHARE = "like_share"                # 点赞转发
    FILL_FORM = "fill_form"                  # 填写表单
    ONE_CLICK = "one_click"                  # 一键参与
    OTHER = "other"                           # 其他
```

## 存储设计

### 新增 activity_participations 表

```sql
CREATE TABLE activity_participations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id TEXT NOT NULL,
    activity_title TEXT,
    operation_type TEXT,
    confidence REAL,
    ai_analysis TEXT,              -- JSON 格式的 AI 分析结果
    user_confirmed BOOLEAN,        -- 用户是否确认
    execution_result TEXT,         -- 执行结果
    created_at TEXT NOT NULL
);
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| activity_id | TEXT | 活动 ID |
| activity_title | TEXT | 活动标题 |
| operation_type | TEXT | 操作类型 |
| confidence | REAL | AI 分析置信度 (0-1) |
| ai_analysis | TEXT | AI 分析结果的 JSON |
| user_confirmed | BOOLEAN | 用户是否确认采用此方式 |
| execution_result | TEXT | 执行结果（成功/失败/原因） |
| created_at | TEXT | 创建时间 |

## 错误处理

| 异常情况 | 处理方式 |
|----------|----------|
| 页面访问失败 | 提示用户，记录日志，跳过该活动 |
| 置信度低于阈值 (<60%) | 显示所有可能性，让用户手动选择 |
| 操作执行失败 | 重试机制（最多3次），失败后回退到手动模式 |
| 用户取消 | 记录用户选择，更新状态，继续下一个活动 |

## 用户交互示例

```
=== 活动内容 ===
标题：XXX摄影大赛
介绍：上传你的摄影作品，赢取大奖
要求：作品需原创，带话题标签

=== AI 分析 ===
操作类型：【填写表单】
说明：需要上传作品并填写描述
置信度：85%

=== 确认 ===
是否按此方式参与？(y/n/其他方式):
```

## CLI 命令扩展

```bash
# 单独分析某个活动
toutiao-agent analyze-activity <activity_id>

# 查看活动参与历史
toutiao-agent activity-history --limit 20

# 查看 AI 分析准确率统计
toutiao-agent activity-stats
```

## 测试策略

1. **正常流程** - 各类操作类型活动的完整参与流程
2. **边界情况** - 置信度低、页面无法访问、用户中途取消
3. **AI 分析验证** - 手动验证分析结果准确性

## 后续优化方向

1. 收集真实活动数据，优化 AI 提示词
2. 支持更多操作类型
3. 添加批量处理模式
4. 根据历史数据自动提升置信度

## 技术要点

- 使用 playwright-cli 获取页面信息（截图、DOM 结构、可交互元素）
- AI 分析页面元素，识别操作类型
- 保留现有 confirmation_mode，增加操作方式确认环节
- 所有结果记录到 SQLite 数据库

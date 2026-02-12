---
name: toutiao-activity
description: 头条活动参与流程。使用此技能当：需要获取活动列表、参与活动、验证参与结果或处理活动相关问题时。
---

# Toutiao Agent - 活动参与

## CLI 命令

### 查看活动列表

```bash
uv run toutiao-agent activities --limit 10
```

功能：获取头条创作者平台的活动列表

### 智能参与活动

```bash
uv run toutiao-agent start-activities --count 5
```

功能：分析活动并智能参与

### 查看参与历史

```bash
uv run toutiao-agent activity-history --limit 20
```

### 查看参与统计

```bash
uv run toutiao-agent activity-stats
```

---

## 活动参与流程

```
1. 获取活动列表: 从头条创作者平台 API 获取活动
2. 过滤: 只显示进行中且未参与的活动
3. 智能分析: 使用 playwright-cli 获取活动页面，AI 分析操作类型
4. 显示分析结果: 展示活动内容和 AI 建议的操作方式
5. 用户确认: 用户确认是否采用建议的操作方式
6. 执行操作:
   - 【生成原创】→ 根据活动说明生成微头条并发布
   - 【一键参与】→ 点击参与按钮
   - 【点赞转发】→ 点赞/转发活动内容
   - 【填写表单】→ 填写表单并提交
7. ⚠️ 验证参与结果: 执行操作后，必须验证是否参与成功
8. 记录结果: 存储到 activity_participations 表
```

---

## 活动数据结构

```python
class Activity:
    activity_id: int                    # 活动 ID
    title: str                          # 活动标题
    introduction: str                   # 活动介绍
    activity_time: str                  # 活动时间描述
    activity_reward: str                # 活动奖励
    activity_participants: str          # 参与人数
    part_in: int                        # 是否已参与 (0/1)
    status: int                         # 活动状态
    hashtag_id: int                     # 话题 ID
    hashtag_name: str                   # 话题名称
    href: str                           # 活动链接
    activity_start_time: int            # 开始时间 (Unix 时间戳)
    activity_end_time: int              # 结束时间 (Unix 时间戳)
```

---

## 活动参与验证

### 成功判断标准
- 页面显示"已参与"、"参与成功"等提示文字
- 按钮状态变为"已参与"、"已报名"等
- 页面跳转到参与确认页面
- 发布微头条后显示"发布成功"

### 失败情况
- 页面显示错误提示
- 操作无响应（超时）
- 需要APP扫码（无法在网页端完成）
- 活动已过期/已结束

---

## 验证方法（使用 playwright-cli）

```bash
# 1. 获取页面文本内容检查提示文字
playwright-cli eval "document.body.innerText"

# 2. 检查按钮文本是否变化为"已参与"
playwright-cli eval "document.querySelector('button').textContent"

# 3. 截图保存参与结果
playwright-cli screenshot --filename=activity_result.png

# 4. 检查页面 URL 是否跳转
playwright-cli eval "window.location.href"

# 5. 等待并检查特定元素出现
playwright-cli eval "document.querySelector('.success-message') !== null"
```

### 验证判断流程
```bash
# 执行参与操作后
# 步骤1: 等待2-3秒让页面响应
sleep 3

# 步骤2: 获取页面内容检查成功提示
page_text=$(playwright-cli eval "document.body.innerText")

# 步骤3: 判断是否包含成功关键词
if echo "$page_text" | grep -q "已参与\|参与成功\|报名成功"; then
    echo "✅ 参与成功"
    # 记录: status=success
else
    echo "❌ 参与可能失败，需要用户确认"
    # 记录: status=pending, failure_reason="需要人工确认"
fi
```

---

## 活动 API 端点

- **活动列表**: `https://mp.toutiao.com/mp/agw/activity/list/v2/`
- **获取分类**: `https://mp.toutiao.com/mp/agw/activity/get_all_category/`

API 请求需要携带有效的 Cookie。

---

## 参与类型

| 类型 | 说明 | 操作 |
|------|------|------|
| original | 生成原创内容 | 根据活动说明生成微头条并发布 |
| publish | 发布微头条 | 发布带话题标签的微头条 |
| like | 点赞 | 点赞活动内容 |
| forward | 转发 | 转发活动内容 |
| form | 填写表单 | 填写表单并提交 |

---

## 代码位置

活动抓取: `src/toutiao_agent/activity_fetcher.py`
活动参与命令: `src/toutiao_agent/main.py` - `start_activities_cmd()`

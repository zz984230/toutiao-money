# 进化日志

记录 toutiao-explorer 的能力进化历史。

## 进化统计

- 总进化次数: 9
- 成功解决问题: 9
- 新增活动模式: 2
- 上次进化: 2026-02-13

---

## 最近进化

### [E009] 2026-02-13 - 活动参与流程全面修复：页面加载、卡片点击、记录重复

**触发**: 用户主动反馈

**问题**:
1. "上头条 聊热点"活动显示已参与但实际未成功
2. "文学创作大会"活动页面内容空白
3. 数据库中存在大量重复参与记录（同一活动8条）
4. 缺少APP端活动的专门检测方法

**分析**:
- **点击活动卡片失败**：
  - `click_activity_card` 使用的选择器过于宽泛
  - 点击后跳转到 `/activity/task-list` 而非活动详情页
  - 缺少点击后的URL验证
- **页面加载问题**：
  - 等待时间不足（2-3秒），复杂JS页面未完全渲染
  - 没有验证页面内容是否真正加载
  - 可能停留在404或空页面却认为加载成功
- **活动参与失败根本原因**：
  - `post_micro_headline` 从微头条发布页面发布，未建立与活动的关联
  - 应从活动页面发布才能正确计入活动
- **重复记录bug**：
  - `start_activities_cmd` 在用户确认前就创建记录（line 428-435）
  - 执行后又创建新记录，导致同一活动多条记录

**解决方案**:
1. **改进 `click_activity_card`**：
   - 三层匹配策略：精确匹配ID → data属性 → URL参数提取
   - 点击后验证URL是否包含 activity_id
   - 添加重试逻辑（最多3次）
   - 失败时保存调试截图

2. **新增 `verify_page_loaded()` 方法**：
   - 检查 body.innerText 长度 > 100字符
   - 检测页面标题和内容是否包含"404"
   - 返回布尔值表示加载状态

3. **新增 `participate_from_activity_page()` 方法**：
   - 整合完整流程：打开创作者中心 → 点击活动卡片 → 验证页面 → 发布内容
   - 确保从活动页面发布，建立正确的活动关联

4. **修复重复记录bug**：
   - 移除AI分析后的自动记录创建
   - 只在用户确认并执行后创建记录
   - `user_confirmed=True` 作为真正参与的标志

5. **新增 `is_activity_skipped_for_app()` 方法**：
   - 查询 `operation_type='skip_requires_app'` 的记录
   - 快速检查活动是否因需要APP而被跳过

**代码更新**:
```python
# 新增页面验证方法
async def verify_page_loaded(self) -> bool:
    check = await self.page.evaluate('''() => {
        return {
            contentLength: document.body.innerText.length,
            title: document.title,
            url: window.location.href
        };
    }''')
    return check['contentLength'] > 100 and '404' not in check['title']

# 新增从活动页面参与方法
async def participate_from_activity_page(self, activity_id: str, content: str) -> Dict:
    # 完整的参与流程...

# 新增APP跳过检查方法
def is_activity_skipped_for_app(self, activity_id: str) -> bool:
    # 查询skip_requires_app记录...
```

**验证状态**: ✅ 已实施
**技能同步**: 待同步 PATTERNS.md（活动参与流程模式）

---

### [E008] 2026-02-13 - 404问题根因分析：URL格式错误

**触发**: 用户主动反馈

**问题**:
- 访问活动详情页 `https://m.toutiao.com/is/{activity_id}/` 返回404
- 访问新闻详情页 `https://m.toutiao.com/i/{article_id}/` 返回404
- 直接构造的URL格式不正确，导致无法访问页面

**分析**:
- **活动URL格式问题**：
  - 错误格式：`https://m.toutiao.com/is/{activity_id}/`
  - 正确来源：活动API返回的 `href` 字段
  - 正确格式1：`https://mp.toutiao.com/profile_v3_public/public/activity/?id={activity_id}`
  - 正确格式2：`https://api.toutiaoapi.com/magic/eco/runtime/release/...`
- **新闻详情URL格式问题**：
  - 错误格式：`https://m.toutiao.com/i/{article_id}/`
  - 正确格式：`https://www.toutiao.com/article/{article_id}/`
- **根本原因**：直接构造移动端URL缺少必要的参数和会话上下文

**解决方案**:
1. **活动访问**：必须使用 `activity.href` 字段，而非构造URL
2. **新闻详情**：使用 `https://www.toutiao.com/article/{article_id}/` 格式
3. **代码更新**：
   ```python
   # 正确的活动访问方式
   activities = activity_fetcher.fetch_activities(limit=10)
   activity_url = activities[0].href  # 使用API返回的href

   # 正确的新闻访问方式
   news_url = f"https://www.toutiao.com/article/{article_id}/"
   ```
4. 更新 SKILL.md：添加URL格式错误示例和正确格式说明

**验证状态**: ✅ 已验证（正确URL可成功访问）
**技能同步**: 已同步 EVOLUTION.md

---

### [E007] 2026-02-13 - 需要APP的活动记录与跳过机制

**触发**: 用户主动反馈

**问题**:
1. 用户希望删除已删除内容的参与记录，允许重新参与
2. 需要APP的活动被反复尝试，浪费时间

**分析**:
- **活动参与状态管理**：
  - 用户可能删除已发布的内容，活动参与记录应支持移除
  - 某些活动可以重新参与（如每日任务）
- **APP依赖检测**：
  - 2月·每日幸运签：链接跳转到 App Store
  - 集卡领红包：集卡操作可能需要APP
- **跳过机制**：
  - 识别出需要APP的活动后，应记录到数据库
  - 后续探索时自动跳过，避免重复试错

**解决方案**:
1. 支持 `DELETE FROM activity_participations WHERE activity_id = ?` 删除参与记录
2. 需要APP的活动使用 `operation_type='skip_requires_app'` 记录
3. `user_confirmed=False` 标记为跳过状态（非真正参与）
4. 更新筛选逻辑：跳过 `operation_type='skip_requires_app'` 的活动

**验证状态**: ✅ 已实现并记录
**技能同步**: 待更新 SKILL.md，添加APP活动检测和跳过规则

---

### [E006] 2026-02-13 - 网络搜索边界与移动端活动入口

**触发**: 用户主动反馈

**问题**:
1. 用户反馈网络搜索不应该用于搜索"如何参与头条活动"这类业务问题
2. "每日幸运签"活动只能通过移动端入口或APP参与抽签步骤

**分析**:
- **网络搜索的正确用途**：
  - ✅ 技术问题：工具使用、技能操作、代码语法、页面操作方法
  - ❌ 业务问题：头条活动参与方式、规则等（搜索结果可能过时或错误）
- **每日幸运签活动特点**：
  - "戳这里👉快来看看你能抽到什么签文吧～"链接跳转到 App Store
  - 抽签功能只能在移动端APP中使用
  - 网页端无法完成抽签步骤
- **参与方式**：
  - 通过话题 `#2月·每日幸运签#` 发布微头条可以参与
  - 但需要先在APP中完成抽签获取签文

**解决方案**:
1. 更新 SKILL.md：在网络搜索相关说明中明确边界
2. 更新 PATTERNS.md：添加移动端活动模式
3. 添加移动端活动检测逻辑：
   - 如果"戳这里"链接跳转到 App Store → 标记为"需要APP"
   - 优先尝试通过话题发布参与
4. 活动分析时检测是否需要移动端

**验证状态**: ✅ 已验证
**技能同步**: 待同步 SKILL.md, PATTERNS.md

---

### [E005] 2026-02-13 - 活动页面访问方式修正（必须从活动广场进入）

**触发**: 用户主动反馈

**问题**:
- 用户指出直接访问活动页面 URL 可能会返回 404
- 必须从活动广场（创作者中心）点击活动卡片进入
- `open_activity_page()` 方法直接构造 URL 访问不可靠

**分析**:
- 头条活动页面有访问控制：直接访问活动 URL 可能被服务器拒绝
- **正确的访问流程**：创作者中心 → 活动广场 → 点击活动卡片 → 活动页面
- 从创作者中心点击卡片会建立必要的会话上下文和权限验证
- 直接构造 URL 访问缺少这些上下文信息，导致 404

**解决方案**:
1. **废弃直接 URL 访问方式**：不应再使用 `open_activity_page()` 直接访问
2. **强制使用卡片点击流程**：
   ```python
   # 正确的访问方式
   await client.open_creator_center()        # 先打开创作者中心
   await client.click_activity_card(activity_id)  # 点击活动卡片
   # 等待活动页面加载后继续操作
   ```
3. 更新 PATTERNS.md：在"模式 0"中强调必须从创作者中心进入
4. 更新 toutiao_client.py：`open_activity_page()` 方法添加警告注释

**验证状态**: ✅ 已同步到 PATTERNS.md 模式 0（第 39-43 行）
**技能同步**: ✅ 已完成同步 SKILL.md 和 PATTERNS.md

### [E004] 2026-02-13 - 活动参与频率规则优化

**触发**: 用户主动反馈

**问题**:
- 用户指出两个重要规则未在技能文档中体现：
  1. 已经参与的活动应避免多次参与
  2. 每日幸运签等每日任务可以每天参与一次

**分析**:
- 一次性活动和每日任务需要不同的处理逻辑
- `storage.is_activity_participated()` 只能判断是否曾经参与，无法区分每日任务
- 每日任务需要检查"上次参与日期"是否是今天

**解决方案**:
1. 更新 SKILL.md：在可行性筛选中添加"避免重复参与已参与活动"规则
2. 更新 ACTIVITY_TYPES.md：添加"一次性活动"和"每日活动"的分类说明
3. 更新 PATTERNS.md：在模式3（每日签到/打卡）中添加：
   - 每日任务判断逻辑代码示例
   - 明确"每天可参与一次"的特性
   - 添加 `can_participate_daily()` 函数示例

**验证状态**: ✅ 已更新技能文档
**技能同步**: 已同步 SKILL.md, ACTIVITY_TYPES.md, PATTERNS.md

---

### [E003] 2026-02-13 - 活动参与入口优化（从活动页面发布）

**触发**: 用户主动反馈

**问题**:
- 用户指出从微头条页面发布带话题标签的内容，可能不被识别为参与活动
- 活动需要正确的话题标签和参与上下文才能计入

**分析**:
- **从活动页面进入发布**更可靠：
  - 活动页面会自动带上正确的话题标签
  - 确保发布的内容被计入活动参与
  - 页面上下文包含活动 ID 和参与关系
- **从微头条页面直接发布**存在风险：
  - 需要手动添加话题标签（如 `#天南地北大拜年#`）
  - 可能因为缺少活动上下文而不被识别
  - 即使有话题标签也可能无法参与成功

**解决方案**:
1. 活动参与流程更新为：活动页面 → 点击「发布微头条」按钮 → 在弹出的输入框中发布
2. 优先使用活动页面的发布入口，而非直接从微头条发布页面发布
3. 记录活动参与时必须是从活动页面触发的发布行为

**验证状态**: ⚠️ 正在验证中（需确认点击"发布微头条"后的具体行为）
**技能同步**: 待同步 STRATEGIES.md 和 PATTERNS.md

---

### [E002] 2026-02-13 - ActivityAnalyzer 页面直接分析能力

**触发**: 用户主动反馈

**问题**:
- ActivityAnalyzer 使用 subprocess 调用 playwright-cli 命令行工具
- 命令行工具可能在某些环境下无法正确执行
- 导致分析器返回置信度 0%，无法正确识别活动页面

**分析**:
- 活动页面已通过 `open_creator_center()` 和 `click_activity_card()` 加载
- 不需要再次通过 subprocess 截取和分析页面
- 可以直接在已加载的 page 上执行 JavaScript 分析

**解决方案**:
1. 新增 `analyze_from_page()` 方法
   - 直接接受 Playwright Page 对象
   - 在页面中执行 JavaScript 检测元素：
     - 输入框（`[contenteditable="true"]` 或 `textarea`）
     - 发布按钮（包含"发布"、"发送"、"提交"等关键词）
     - 活动卡片链接（用于验证是否在活动页面）
2. 根据检测结果返回更精确的操作类型：
   - 检测到输入框 + 发布按钮 → GENERATE_CONTENT（高置信度 0.95）
   - 检测到输入框但无发布按钮 → GENERATE_CONTENT（中置信度 0.70，提示需先点击参与按钮）
   - 检测到活动卡片 → 确认在活动页面（置信度 1.0）

**验证状态**: ✅ 测试通过（置信度从 0% 提升到 95%）
**技能同步**: 已更新 ACTIVITY_ANALYZER.md，添加 analyze_from_page() 方法

---

### [E001] 2026-02-13 - 活动参与方式修正

**触发**: 用户主动反馈

**问题**:
- 直接发布带话题标签的微头条后，用户删除了内容
- 原因：活动需要从活动页面点击按钮进入活动弹窗发布，而非直接发布微头条

**分析**:
- 活动URL格式：`mp.toutiao.com/profile_v3_public/public/activity/?activity_location=panel_invite_discuss_hot_mp&id={id}`
- `toutiao.com/activity/{id}` 格式返回404
- 活动入口：创作者中心首页 (mp.toutiao.com/profile_v4/index) 的活动卡片区域
- 点击活动卡片会打开新标签页或弹窗显示活动详情

**解决方案**:
1. 修改活动参与流程：访问创作者中心 → 点击活动卡片 → 在活动弹窗中参与
2. 更新 `ActivityAnalyzer` 使用正确的活动URL格式
3. 添加活动入口检测逻辑，识别卡片点击 vs 直接发布

**验证状态**: ⚠️ 需进一步验证
**技能同步**: 待同步 PATTERNS.md 和 STRATEGIES.md

---

## 进化分类索引

### 按触发类型
- 未知活动类型 → 暂无
- 连续失败 → 暂无
- 用户主动 → 暂无

### 按解决方案类型
- 新增活动模式 → E001 (2026-02-13)
- 页面结构更新 → E001 (2026-02-13)
- 策略优化 → E001 (2026-02-13), E005 (2026-02-13)
- 内容模板 → 暂无
- 访问控制/会话管理 → E005 (2026-02-13)

---

## 完整进化历史

按时间倒序排列。

### [E001] 2026-02-13 - 活动参与方式修正

**触发**: 用户主动反馈

**问题**:
- 直接发布带话题标签的微头条后，用户删除了内容
- 原因：活动需要从活动页面点击按钮进入活动弹窗发布，而非直接发布微头条

**分析**:
- 活动URL格式：`mp.toutiao.com/profile_v3_public/public/activity/?activity_location=panel_invite_discuss_hot_mp&id={id}`
- `toutiao.com/activity/{id}` 格式返回404
- 活动入口：创作者中心首页 (mp.toutiao.com/profile_v4/index) 的活动卡片区域
- 点击活动卡片会打开新标签页或弹窗显示活动详情

**解决方案**:
1. 修改活动参与流程：访问创作者中心 → 点击活动卡片 → 在活动弹窗中参与
2. 更新 `ActivityAnalyzer` 使用正确的活动URL格式
3. 添加活动入口检测逻辑，识别卡片点击 vs 直接发布

**验证状态**: ⚠️ 需进一步验证
**技能同步**: 待同步 PATTERNS.md 和 STRATEGIES.md

---

## 进化条目模板

```markdown
### [E###] YYYY-MM-DD - 标题
**触发**: 未知活动类型 / 连续失败 / 用户主动
**问题**: 问题描述

**分析**:
- 关键发现 1
- 关键发现 2

**解决方案**:
1. 解决步骤 1
2. 解决步骤 2

**验证状态**: ✅ 已测试通过 / ⚠️ 需进一步验证 / ❌ 测试失败
**技能同步**: 已更新 XXX.md / 待同步 / 无需同步
```

# Activity Intelligent Participation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现活动智能参与系统，通过 AI 分析活动页面自动识别操作类型并执行相应操作

**Architecture:** 新增 ActivityAnalyzer 组件使用 playwright-cli 获取活动页面信息，调用 AI 分析页面结构并返回操作建议；修改 start_activities_cmd 命令集成分析流程；新增 activity_participations 表记录参与历史。

**Tech Stack:** Python, Playwright, playwright-cli skill, mcp__4_5v_mcp__analyze_image, SQLite

---

## Task 1: 创建 OperationType 枚举

**Files:**
- Create: `src/toutiao_agent/activity_types.py`

**Step 1: 创建枚举文件**

```python
"""活动操作类型定义"""

from enum import Enum


class OperationType(Enum):
    """活动参与操作类型"""

    GENERATE_CONTENT = "generate_content"    # 生成原创微头条
    LIKE_SHARE = "like_share"                # 点赞/转发
    FILL_FORM = "fill_form"                  # 填写表单
    ONE_CLICK = "one_click"                  # 一键参与
    OTHER = "other"                           # 其他类型

    @property
    def label(self) -> str:
        """中文标签"""
        labels = {
            self.GENERATE_CONTENT: "生成原创",
            self.LIKE_SHARE: "点赞转发",
            self.FILL_FORM: "填写表单",
            self.ONE_CLICK: "一键参与",
            self.OTHER: "其他"
        }
        return labels[self]

    def __str__(self) -> str:
        return self.label
```

**Step 2: 提交**

```bash
git add src/toutiao_agent/activity_types.py
git commit -m "feat: add OperationType enum for activity participation"
```

---

## Task 2: 创建 ActionResult 数据类

**Files:**
- Create: `src/toutiao_agent/activity_analyzer.py`

**Step 1: 创建基础结构**

```python
"""活动分析模块 - 分析活动页面并生成参与建议"""

from dataclasses import dataclass, asdict
from typing import Dict, Optional, Any
from .activity_types import OperationType


@dataclass
class ActionResult:
    """活动分析结果"""

    activity_title: str              # 活动标题
    activity_intro: str              # 活动介绍
    operation_type: OperationType     # 操作类型
    confidence: float                # 置信度 0-1
    detected_elements: Dict[str, Any]  # 检测到的元素
    suggested_action: str             # 建议操作描述

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于存储"""
        return {
            'activity_title': self.activity_title,
            'activity_intro': self.activity_intro,
            'operation_type': self.operation_type.value,
            'confidence': self.confidence,
            'detected_elements': self.detected_elements,
            'suggested_action': self.suggested_action
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionResult':
        """从字典创建实例"""
        return cls(
            activity_title=data.get('activity_title', ''),
            activity_intro=data.get('activity_intro', ''),
            operation_type=OperationType(data.get('operation_type', OperationType.OTHER.value)),
            confidence=data.get('confidence', 0.0),
            detected_elements=data.get('detected_elements', {}),
            suggested_action=data.get('suggested_action', '')
        )


class ActivityAnalyzer:
    """活动分析器 - 使用 AI 分析活动页面"""

    def __init__(self):
        """初始化分析器"""
        pass

    async def analyze(self, activity) -> ActionResult:
        """分析活动页面，返回操作建议

        Args:
            activity: Activity 对象

        Returns:
            ActionResult 包含操作类型、活动内容、置信度等
        """
        # TODO: 实现具体分析逻辑
        raise NotImplementedError("analyze 方法将在后续任务中实现")
```

**Step 2: 提交**

```bash
git add src/toutiao_agent/activity_analyzer.py
git commit -m "feat: add ActionResult dataclass and ActivityAnalyzer stub"
```

---

## Task 3: 扩展存储 - 添加 activity_participations 表

**Files:**
- Modify: `src/toutiao_agent/storage.py`

**Step 1: 添加表创建逻辑**

在 `CommentStorage._init_db()` 方法中添加新表：

```python
# 在 _init_db 方法的 CREATE TABLE 部分之后添加

# 活动参与记录表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS activity_participations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        activity_id TEXT NOT NULL,
        activity_title TEXT,
        operation_type TEXT,
        confidence REAL,
        ai_analysis TEXT,
        user_confirmed INTEGER DEFAULT 0,
        execution_result TEXT,
        created_at TEXT NOT NULL
    )
''')
```

**Step 2: 添加记录方法**

在 `CommentStorage` 类中添加方法：

```python
def add_activity_participation(
    self,
    activity_id: str,
    activity_title: str = None,
    operation_type: str = None,
    confidence: float = 0.0,
    ai_analysis: str = None,
    user_confirmed: bool = False,
    execution_result: str = None
):
    """记录活动参与

    Args:
        activity_id: 活动 ID
        activity_title: 活动标题
        operation_type: 操作类型
        confidence: 置信度
        ai_analysis: AI 分析结果 JSON
        user_confirmed: 用户是否确认
        execution_result: 执行结果
    """
    import json
    cursor = self.conn.cursor()
    from datetime import datetime

    # 如果 ai_analysis 是 dict，转换为 JSON 字符串
    ai_analysis_json = ai_analysis
    if isinstance(ai_analysis, dict):
        ai_analysis_json = json.dumps(ai_analysis, ensure_ascii=False)

    cursor.execute('''
        INSERT INTO activity_participations
        (activity_id, activity_title, operation_type, confidence, ai_analysis, user_confirmed, execution_result, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        activity_id,
        activity_title,
        operation_type,
        confidence,
        ai_analysis_json,
        1 if user_confirmed else 0,
        execution_result,
        datetime.now().isoformat()
    ))
    self.conn.commit()

def get_activity_participations(self, limit: int = 20) -> list:
    """获取活动参与记录

    Args:
        limit: 返回记录数

    Returns:
        参与记录列表
    """
    cursor = self.conn.cursor()
    cursor.execute('''
        SELECT activity_id, activity_title, operation_type, confidence,
               user_confirmed, execution_result, created_at
        FROM activity_participations
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))

    rows = cursor.fetchall()
    return [
        {
            'activity_id': r[0],
            'activity_title': r[1],
            'operation_type': r[2],
            'confidence': r[3],
            'user_confirmed': bool(r[4]),
            'execution_result': r[5],
            'created_at': r[6]
        }
        for r in rows
    ]

def is_activity_participated(self, activity_id: str) -> bool:
    """检查活动是否已参与（更新方法，检查 activity_participations 表）

    Args:
        activity_id: 活动 ID

    Returns:
        是否已参与
    """
    cursor = self.conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM activity_participations
        WHERE activity_id = ? AND user_confirmed = 1
    ''', (activity_id,))
    count = cursor.fetchone()[0]
    return count > 0
```

**Step 3: 提交**

```bash
git add src/toutiao_agent/storage.py
git commit -m "feat: add activity_participations table and related methods"
```

---

## Task 4: 实现基础的页面信息获取

**Files:**
- Modify: `src/toutiao_agent/activity_analyzer.py`

**Step 1: 实现 playwright-cli 调用**

在 `ActivityAnalyzer` 类中添加页面获取方法：

```python
import subprocess
import json
import tempfile
from pathlib import Path
from .activity_types import OperationType


class ActivityAnalyzer:
    """活动分析器 - 使用 AI 分析活动页面"""

    def __init__(self, base_url: str = "https://www.toutiao.com"):
        """初始化分析器

        Args:
            base_url: 头条基础 URL
        """
        self.base_url = base_url

    def _get_page_screenshot(self, url: str, output_path: str) -> bool:
        """使用 playwright-cli 获取页面截图

        Args:
            url: 活动页面 URL
            output_path: 输出文件路径

        Returns:
            是否成功
        """
        try:
            result = subprocess.run(
                ['playwright', 'screenshot', url, '-o', output_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            print(f"截图失败: {e}")
            return False

    def _get_page_text(self, url: str) -> str:
        """使用 playwright-cli 获取页面文本

        Args:
            url: 活动页面 URL

        Returns:
            页面文本内容
        """
        try:
            result = subprocess.run(
                ['playwright', 'code', url, '-c', 'document.body.innerText'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                # 解析输出，提取实际文本
                return result.stdout.strip()
            return ""
        except Exception as e:
            print(f"获取页面文本失败: {e}")
            return ""

    def _get_interactive_elements(self, url: str) -> list:
        """获取页面可交互元素

        Args:
            url: 活动页面 URL

        Returns:
            元素列表
        """
        try:
            code = '''
            Array.from(document.querySelectorAll('button, a, input, textarea'))
                .filter(el => el.offsetParent !== null)  // 只取可见元素
                .map(el => ({
                    tag: el.tagName,
                    text: el.textContent?.slice(0, 50),
                    type: el.type || '',
                    id: el.id || '',
                    className: el.className || ''
                }))
            '''
            result = subprocess.run(
                ['playwright', 'code', url, '-c', code],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                # 尝试解析 JSON 输出
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    pass
            return []
        except Exception as e:
            print(f"获取交互元素失败: {e}")
            return []
```

**Step 2: 提交**

```bash
git add src/toutiao_agent/activity_analyzer.py
git commit -m "feat: add playwright-cli integration for page info extraction"
```

---

## Task 5: 实现 AI 分析逻辑

**Files:**
- Modify: `src/toutiao_agent/activity_analyzer.py`

**Step 1: 实现 analyze 方法**

```python
from .activity_types import OperationType
import json


class ActivityAnalyzer:
    # ... 之前的代码 ...

    async def analyze(self, activity) -> ActionResult:
        """分析活动页面，返回操作建议

        Args:
            activity: Activity 对象

        Returns:
            ActionResult 包含操作类型、活动内容、置信度等
        """
        # 构建活动 URL
        url = activity.href if activity.href else f"{self.base_url}/activity/{activity.activity_id}"

        print(f"正在分析活动: {activity.title}")
        print(f"URL: {url}")

        # 获取页面信息
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            screenshot_path = f.name

        success = self._get_page_screenshot(url, screenshot_path)
        if not success:
            # 截图失败，返回默认结果
            return ActionResult(
                activity_title=activity.title,
                activity_intro=activity.introduction,
                operation_type=OperationType.OTHER,
                confidence=0.0,
                detected_elements={},
                suggested_action="无法获取活动页面，请手动处理"
            )

        page_text = self._get_page_text(url)
        elements = self._get_interactive_elements(url)

        # TODO: 调用 AI 分析
        # 当前先返回基于简单规则的初步结果
        operation_type, confidence, suggested = self._simple_rule_analysis(elements, page_text)

        return ActionResult(
            activity_title=activity.title,
            activity_intro=activity.introduction,
            operation_type=operation_type,
            confidence=confidence,
            detected_elements={
                'page_text': page_text[:500],  # 只保存前500字符
                'interactive_elements': elements[:10],  # 只保存前10个元素
                'screenshot_path': screenshot_path
            },
            suggested_action=suggested
        )

    def _simple_rule_analysis(self, elements: list, page_text: str) -> tuple:
        """基于简单规则分析活动类型（临时实现）

        Args:
            elements: 可交互元素列表
            page_text: 页面文本

        Returns:
            (operation_type, confidence, suggested_action)
        """
        # 检查是否有一键参与/立即参与按钮
        for el in elements:
            text = (el.get('text') or '').lower()
            if any(keyword in text for keyword in ['立即参与', '一键参与', '马上参加', '立即报名']):
                return OperationType.ONE_CLICK, 0.85, f"检测到 '{el.get('text')}' 按钮，建议点击"

        # 检查是否有表单元素
        has_form = any(el.get('tag') in ['INPUT', 'TEXTAREA'] for el in elements)
        if has_form:
            return OperationType.FILL_FORM, 0.70, "检测到表单输入框，建议填写表单"

        # 检查是否有转发/分享相关
        page_text_lower = page_text.lower()
        if any(keyword in page_text_lower for keyword in ['转发', '分享', 'share']):
            return OperationType.LIKE_SHARE, 0.60, "检测到转发/分享相关内容"

        # 默认生成原创内容
        return OperationType.GENERATE_CONTENT, 0.50, "未检测到特殊操作类型，建议生成原创内容"
```

**Step 2: 提交**

```bash
git add src/toutiao_agent/activity_analyzer.py
git commit -m "feat: implement basic analyze method with rule-based detection"
```

---

## Task 6: 修改 start_activities_cmd 集成分析流程

**Files:**
- Modify: `src/toutiao_agent/main.py`

**Step 1: 更新导入和流程**

在文件顶部添加导入：

```python
from .activity_analyzer import ActivityAnalyzer
```

修改 `start_activities_cmd` 函数，集成分析流程：

```python
@cli.command('start-activities')
@click.option('--count', default=5, help='参与活动数量')
def start_activities_cmd(count):
    """自动参与活动（智能分析 + 生成并发布微头条）"""
    from .storage import storage

    async def run():
        agent = ToutiaoAgent()
        analyzer = ActivityAnalyzer()  # 新增：创建分析器
        try:
            await agent.initialize()

            # 获取活动列表
            print(f"\n正在获取活动列表...")
            activities = activity_fetcher.fetch_activities(
                limit=count * 2,
                only_ongoing=True,
                only_unparticipated=True
            )

            # 过滤已参与的活动
            new_activities = [
                a for a in activities
                if not storage.is_activity_participated(str(a.activity_id))
            ]

            if not new_activities:
                print("暂无新的活动可参与")
                return

            click.echo(f"\n找到 {len(new_activities)} 个新活动\n")

            # 逐个处理活动
            for i, activity in enumerate(new_activities[:count], 1):
                print(f"\n{'='*50}")
                print(f"处理第 {i}/{min(count, len(new_activities))} 个活动")
                print(f"{'='*50}")
                print(f"活动: {activity.title}")
                print(f"介绍: {activity.introduction}")

                # 确认模式
                if config.behavior.get('confirmation_mode', True):
                    choice = input(f"\n是否参与此活动? (y/n/s跳过): ").strip().lower()
                    if choice != 'y':
                        continue

                # ===== 新增：分析活动 =====
                print(f"\n正在分析活动页面...")
                result = await analyzer.analyze(activity)

                # 显示活动内容
                print(f"\n{'='*50}")
                print(f"=== 活动内容 ===")
                print(f"标题：{result.activity_title}")
                print(f"介绍：{result.activity_intro[:200]}{'...' if len(result.activity_intro) > 200 else ''}")

                # 显示 AI 分析结果
                print(f"\n=== AI 分析 ===")
                print(f"操作类型：【{result.operation_type.label}】")
                print(f"置信度：{result.confidence * 100:.0f}%")
                print(f"建议：{result.suggested_action}")

                # 确认操作方式
                confirm = input("\n是否按此方式参与？(y/n/其他方式): ").strip().lower()

                if confirm == 'n':
                    print("跳过此活动")
                    # 记录到数据库（用户取消）
                    storage.add_activity_participation(
                        activity_id=str(activity.activity_id),
                        activity_title=activity.title,
                        operation_type=result.operation_type.value,
                        confidence=result.confidence,
                        ai_analysis=result.to_dict(),
                        user_confirmed=False,
                        execution_result="用户取消"
                    )
                    continue
                elif confirm == '其他方式':
                    # 降级到原来的生成内容流程
                    print("切换到手动生成内容模式...")

                # 记录分析结果到数据库
                storage.add_activity_participation(
                    activity_id=str(activity.activity_id),
                    activity_title=activity.title,
                    operation_type=result.operation_type.value,
                    confidence=result.confidence,
                    ai_analysis=result.to_dict(),
                    user_confirmed=True,
                    execution_result="开始执行"
                )

                # 根据操作类型执行
                if result.operation_type == OperationType.GENERATE_CONTENT or confirm == '其他方式':
                    # 生成内容模式
                    hashtag = activity.get_hashtag() or activity.hashtag_name or ""
                    prompt = f"""请根据以下活动信息生成一条微头条内容：

活动标题: {activity.title}
活动介绍: {activity.introduction}
话题标签: #{hashtag}#

要求:
- 字数: 100-300 字
- 必须包含话题标签
- 内容与活动主题相关
- 积极向上的语气
- 适当使用 emoji

请直接输出微头条内容。"""

                    if config.behavior.get('confirmation_mode', True):
                        print("\n提示词:")
                        print(prompt)
                        print("\n请将上述提示词发送给Claude获取微头条内容，然后输入内容:")

                        content = input("微头条内容: ").strip()

                        if not content:
                            print("跳过")
                            continue

                        # 确认发布
                        print(f"\n即将发布:")
                        print(f"  内容: {content[:100]}{'...' if len(content) > 100 else ''}")
                        if hashtag:
                            print(f"  话题: #{hashtag}#")

                        confirm_publish = input("\n确认发布? (y/n): ").strip().lower()
                        if confirm_publish != 'y':
                            print("已取消")
                            continue

                        # 发布微头条
                        result_publish = await agent.post_micro_headline(
                            content=content,
                            activity_id=str(activity.activity_id),
                            activity_title=activity.title,
                            topic=f"#{hashtag}#" if hashtag else None
                        )

                        # 更新执行结果
                        if result_publish.get('success'):
                            storage.add_activity_participation(
                                activity_id=str(activity.activity_id),
                                activity_title=activity.title,
                                operation_type=result.operation_type.value,
                                confidence=result.confidence,
                                ai_analysis=result.to_dict(),
                                user_confirmed=True,
                                execution_result="发布成功"
                            )

                elif result.operation_type == OperationType.ONE_CLICK:
                    # 一键参与 - TODO: 实现点击按钮逻辑
                    print("\n⚠️ 一键参与功能暂未实现，请手动操作")

                elif result.operation_type == OperationType.LIKE_SHARE:
                    # 点赞转发 - TODO: 实现
                    print("\n⚠️ 点赞转发功能暂未实现，请手动操作")

                elif result.operation_type == OperationType.FILL_FORM:
                    # 填写表单 - TODO: 实现
                    print("\n⚠️ 填写表单功能暂未实现，请手动操作")

                else:
                    print("\n⚠️ 其他类型活动，请手动操作")

                # 间隔
                if i < count:
                    interval = config.behavior.get('comment_interval', 30)
                    print(f"\n等待 {interval} 秒后继续...")
                    await asyncio.sleep(interval)

        finally:
            await agent.close()
    asyncio.run(run())
```

**Step 2: 提交**

```bash
git add src/toutiao_agent/main.py
git commit -m "feat: integrate activity analyzer into start-activities command"
```

---

## Task 7: 添加活动参与历史查询命令

**Files:**
- Modify: `src/toutiao_agent/main.py`

**Step 1: 添加新命令**

```python
@cli.command('activity-history')
@click.option('--limit', default=20, help='显示条数')
def activity_history_cmd(limit):
    """查看活动参与历史"""
    from .storage import storage

    records = storage.get_activity_participations(limit)
    if not records:
        click.echo("暂无活动参与记录")
        return

    click.echo(f"\n📊 最近 {len(records)} 条活动参与记录:\n")

    from .activity_types import OperationType

    for r in records:
        click.echo(f"📅 {r['created_at']}")
        if r['activity_title']:
            click.echo(f"   活动: {r['activity_title'][:50]}...")
        click.echo(f"   操作类型: {r['operation_type']}")
        click.echo(f"   置信度: {r['confidence'] * 100:.0f}%")
        click.echo(f"   用户确认: {'✅' if r['user_confirmed'] else '❌'}")
        if r['execution_result']:
            click.echo(f"   结果: {r['execution_result']}")
        click.echo()


@cli.command('activity-stats')
def activity_stats_cmd():
    """查看活动参与统计"""
    from .storage import storage

    records = storage.get_activity_participations(limit=1000)
    if not records:
        click.echo("暂无统计数据")
        return

    total = len(records)
    confirmed = sum(1 for r in records if r['user_confirmed'])
    avg_confidence = sum(r['confidence'] for r in records) / total if total > 0 else 0

    # 按操作类型统计
    from collections import Counter
    type_counts = Counter(r['operation_type'] for r in records)

    click.echo(f"\n📊 活动参与统计:\n")
    click.echo(f"   总参与次数: {total}")
    click.echo(f"   用户确认: {confirmed}")
    click.echo(f"   平均置信度: {avg_confidence * 100:.1f}%")
    click.echo(f"\n   操作类型分布:")
    for op_type, count in type_counts.most_common():
        click.echo(f"   - {op_type}: {count}")
    click.echo()
```

**Step 2: 提交**

```bash
git add src/toutiao_agent/main.py
git commit -m "feat: add activity-history and activity-stats commands"
```

---

## Task 8: 更新 toutiao-agent skill 文档

**Files:**
- Modify: `.claude/skills/toutiao-agent/toutiao-agent.md`

**Step 1: 更新活动参与流程说明**

在 skill 文档中找到 `活动参与流程` 部分，更新为：

```markdown
## 活动参与流程（已更新）

1. **获取活动列表**: 从头条创作者平台 API 获取活动
2. **过滤**: 只显示进行中且未参与的活动
3. **智能分析**: 使用 playwright-cli 获取活动页面，AI 分析操作类型
4. **显示分析结果**: 展示活动内容和 AI 建议的操作方式
5. **用户确认**: 用户确认是否采用建议的操作方式
6. **执行操作**:
   - 【生成原创】→ 根据活动说明生成微头条并发布
   - 【一键参与】→ 点击参与按钮
   - 【点赞转发】→ 点赞/转发活动内容
   - 【填写表单】→ 填写表单并提交
7. **记录**: 存储到 activity_participations 表
```

**Step 2: 更新 CLI 命令参考**

在 CLI 命令参考部分添加新命令：

```markdown
### 活动命令

| 命令 | 功能 | 示例 |
|------|------|------|
| `activities --limit N` | 查看活动列表 | `uv run toutiao-agent activities --limit 10` |
| `start-activities --count N` | 智能参与活动 | `uv run toutiao-agent start-activities --count 5` |
| `activity-history --limit N` | 查看参与历史 | `uv run toutiao-agent activity-history --limit 20` |
| `activity-stats` | 查看参与统计 | `uv run toutiao-agent activity-stats` |
```

**Step 3: 提交**

```bash
git add .claude/skills/toutiao-agent/toutiao-agent.md
git commit -m "docs: update skill documentation for activity intelligent participation"
```

---

## Task 9: 测试完整流程

**Files:**
- Test: 手动测试

**Step 1: 运行命令测试**

```bash
cd /Users/zero/Project/toutiao-money/.worktrees/activity-intelligent-participation

# 测试获取活动列表
uv run toutiao-agent activities --limit 5

# 测试智能参与流程（交互模式，可以随时取消）
uv run toutiao-agent start-activities --count 1

# 测试历史记录查询
uv run toutiao-agent activity-history --limit 5

# 测试统计
uv run toutiao-agent activity-stats
```

**Step 2: 验证数据库**

```bash
sqlite3 data/comments.db "SELECT * FROM activity_participations LIMIT 5;"
```

**Step 3: 提交（如有调整）**

```bash
git add -A
git commit -m "test: validate activity intelligent participation flow"
```

---

## 完成检查清单

- [ ] OperationType 枚举创建完成
- [ ] ActionResult 数据类创建完成
- [ ] activity_participations 表创建完成
- [ ] ActivityAnalyzer 基础结构创建完成
- [ ] playwright-cli 集成完成
- [ ] analyze 方法实现完成（规则分析）
- [ ] start_activities_cmd 集成分析流程完成
- [ ] 新增查询命令完成
- [ ] skill 文档更新完成
- [ ] 手动测试通过
- [ ] 数据库记录正确

---

## 后续优化（非本计划范围）

1. 使用 mcp__4_5v_mcp__analyze_image 进行 AI 视觉分析
2. 根据真实数据优化 AI 提示词
3. 实现一键参与、点赞转发、填写表单等操作
4. 添加批量处理模式
5. 根据历史数据自动提升置信度

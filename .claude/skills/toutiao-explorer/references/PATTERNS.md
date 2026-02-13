# 常见活动模式

识别头条平台上的高频活动模式，提高处理效率。

## 模式 0：活动卡片点击参与 (E001)

**特征**：
- 需要从创作者中心首页点击活动卡片
- 点击后打开活动弹窗或新标签页
- 在活动页面中填写内容并发布，而非直接发布微头条
- 奖励通常是现金或流量扶持

**识别**：
- 活动ID可在创作者中心的活动卡片区域找到
- 活动卡片包含活动标题、奖金、参与人数
- 点击后URL变为 `mp.toutiao.com/profile_v3_public/public/activity/?...`

**执行流程 (E001进化后)**：
```bash
# 1. 打开创作者中心
playwright-cli -s=toutiao goto https://mp.toutiao.com/profile_v4/index

# 2. 点击活动卡片（通过活动ID或标题查找）
playwright-cli -s=toutiao click "text=天南地北大拜年"

# 3. 等待活动页面加载
sleep 3

# 4. 在活动页面中查找输入框并填写内容
playwright-cli -s=toutiao fill '[contenteditable="true"]' "发布的内容"

# 5. 点击发布按钮
playwright-cli -s=toutiao click 'button:has-text("发布")'

# 6. 验证发布成功
playwright-cli eval 'document.body.innerText.includes("发布成功")'
```

**注意事项**：
- 不能直接访问 `toutiao.com/activity/{id}` - 返回404
- 正确的活动URL格式：`mp.toutiao.com/profile_v3_public/public/activity/?activity_location=panel_invite_discuss_hot_mp&id={id}`
- 活动卡片可能需要滚动到可见区域才能点击

**频率**：每天 1-5 个此类活动

---

## 模式 1：话题 + 发布抽奖

## 模式 2：阅读量阶梯奖励

**特征**：
- 阅读量达到不同档位获得不同奖励
- 通常有时间限制（如24小时内）
- 需要内容质量高才能获得高阅读

**识别**：
- 奖励格式："1000阅读=5元，5000阅读=20元"
- 活动说明包含"阅读量"、"播放量"
- 有明确的档位说明

**执行策略**：
1. 评估目标档位（保守选择中档位）
2. 内容优化：使用吸引人的标题和配图
3. 发布时段选择：上午 9-11 点，晚上 7-9 点
4. 发布后观察：每小时检查阅读量增长

**频率**：不定期，每周 1-2 个

---

## 模式 3：每日签到/打卡 (每日任务)

**特征**：
- 一键完成，无内容要求
- 通常连续签到有额外奖励
- 奖励较小但稳定
- **每天可参与一次**（与一次性活动不同）

**识别**：
- 按钮文字："签到"、"打卡"、"抽签"
- 活动类型：日常任务
- 活动名称包含："每日"、"每日签到"、"每日幸运签"
- 奖励：少量积分或现金

**执行**：
```bash
# 每日定时执行
playwright-cli click ".checkin-btn"
playwright-cli eval "document.body.innerText.includes('签到成功')"
```

**重要：每日任务判断逻辑**
```python
from datetime import date
from toutiao_agent.storage import storage

# 检查是否今天已参与
def can_participate_daily(activity_id: str) -> bool:
    """判断每日任务是否可以再次参与"""
    participations = storage.get_activity_participations(activity_id, limit=10)

    if not participations:
        return True  # 从未参与过，可以参与

    # 检查最近一次参与是否是今天
    last_participation = participations[0]
    last_date = last_participation['created_at'][:10]  # YYYY-MM-DD
    today = date.today().isoformat()

    return last_date != today  # 只有今天没参与过才返回True
```

**频率**：长期活动，每日一次
**示例活动**：
- 2月·每日幸运签 (ID: 1855746000734219)
- 每日签到任务

---

## 模式 4：互动任务组合

**特征**：
- 需要完成多个互动操作
- 组合：点赞 + 关注 + 评论 + 转发
- 全部完成才算参与成功

**识别**：
- 页面显示多个任务按钮
- 有进度条或任务清单
- "完成 x/y 即可参与"

**执行顺序**：
1. 先执行低风险操作（点赞、关注）
2. 再执行转发（需要公开）
3. 最后评论（可能需要内容创作）

**频率**：中等频率，每周 2-3 个

---

## 模式 5：创作者等级任务

**特征**：
- 达到一定创作者等级解锁奖励
- 需要累计互动量或粉丝数
- 奖励通常是流量扶持或权限解锁

**识别**：
- 活动说明包含"等级"、"升级"
- 有明确的等级要求和对应奖励

**执行**：
- 长期积累，非单次完成
- 定期检查当前等级和进度
- 规划内容发布频率

**频率**：持续活动，随等级提升解锁

---

## 模式 6：限时挑战赛

**特征**：
- 有明确的开始和结束时间
- 按排名发奖（前100名等）
- 需要在短时间内大量参与

**识别**：
- 活动名称包含"挑战赛"、"PK"
- 有倒计时显示
- 奖励说明提到"排名"、"前N名"

**执行策略**：
1. 活动开始后立即参与
2. 批量参与多个子任务
3. 监控排名变化
4. 接近结束时冲刺

**频率**：不定期，每月 1-2 个

---

## 模式 7：新用户专享

**特征**：
- 限制新注册用户或首次参与
- 奖励较高但只能参与一次
- 通常需要手机验证

**识别**：
- 活动标题包含"新人"、"首享"
- 页面显示"仅限首次参与"
- 奖励金额明显高于同类活动

**执行**：
- 使用未参与过活动的账号
- 仔细阅读新用户定义
- 及时参与避免过期

**频率**：每个账号仅一次

---

## 页面识别快速检查

```bash
# 快速识别活动模式
playwright-cli eval "
  const text = document.body.innerText;
  const patterns = {
    'topic_lottery': /发布.*话题.*抽奖/,
    'views_reward': /阅读量.*奖励/,
    'daily_checkin': /签到|打卡/,
    'combo_task': /点赞.*关注.*评论/,
    'level_task': /等级.*升级/,
    'challenge': /挑战赛|PK|排名/,
    'newbie_only': /新人|首享|仅限首次/
  };

  for (const [key, pattern] of Object.entries(patterns)) {
    if (pattern.test(text)) return key;
  }
  return 'unknown';
"
```

---

## 处理优先级

```
高优先级（立即处理）：
- 限时挑战赛（倒计时进行中）
- 高收益且简单完成的活动
- 每日签到（时间窗口有限）

中优先级（规划处理）：
- 话题 + 发布抽奖（需要内容创作）
- 阅读量阶梯奖励（需要优化内容）
- 互动任务组合（需要多步操作）

低优先级（可选处理）：
- 创作者等级任务（长期积累）
- 低收益的复杂活动
- 需要 APP 的活动
```

---

## 学习记录模式

记录已处理的活动，优化后续决策：

```json
{
  "activity_id": "act_123",
  "pattern": "topic_lottery",
  "success": true,
  "reward_actual": 15,
  "time_spent": 30,
  "completed_at": "2026-02-12T10:00:00"
}
```

**分析优化**：
- 统计哪种模式收益最高
- 识别时间投入产出比最优的模式
- 发现高频失败的模式并降低优先级

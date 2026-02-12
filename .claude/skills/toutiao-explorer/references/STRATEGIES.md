# 活动执行策略

根据活动类型选择不同的执行策略。

## 生成原创活动策略

### 步骤
1. **分析要求**
   - 阅读活动规则：字数、格式、话题标签
   - 识别内容类型：微头条/文章/视频
   - 检查敏感词限制

2. **内容生成**
   - 使用 Claude Code 生成符合要求的原创内容
   - 确保包含必需的话题标签
   - 控制内容长度（微头条 200-500 字）

3. **发布执行**
   ```bash
   # 使用 toutiao-agent 发布
   uv run toutiao-agent post-micro-headline "内容" --topic "#话题#"
   ```

4. **验证参与**
   - 检查发布成功提示
   - 截图保存发布结果
   - 记录到数据库

### 成功率提升
- 避免敏感词（政治、违法内容）
- 内容与话题高度相关
- 配图提高通过率
- 工作时间发布（审核更快）

---

## 一键参与活动策略

### 步骤
1. **定位按钮**
   ```bash
   # 使用 playwright-cli 查找参与按钮
   playwright-cli eval "
     Array.from(document.querySelectorAll('button'))
       .find(b => b.textContent.includes('参与'))
   "
   ```

2. **点击参与**
   ```bash
   # 直接点击按钮
   playwright-cli click ".join-btn"
   ```

3. **验证结果**
   - 检查是否出现"已参与"提示
   - 查看按钮状态是否变化
   - 截图保存证据

### 注意事项
- 部分活动需要先关注作者
- 可能需要先转发/分享
- 注意每日参与次数限制

---

## 点赞转发活动策略

### 步骤
1. **执行点赞**
   ```bash
   # 查找点赞按钮
   playwright-cli eval "
     document.querySelector('.like-btn')?.click()
   "
   ```

2. **执行转发**
   ```bash
   # 查找转发按钮
   playwright-cli eval "
     document.querySelector('.share-btn')?.click()
   "

   # 确认转发
   playwright-cli click ".confirm-share"
   ```

3. **验证参与**
   - 检查点赞数增加
   - 确认转发成功
   - 截图保存

### 注意事项
- 转发可能需要选择发布范围（公开/好友）
- 部分活动要求评论才算完成
- 注意隐私设置（需公开转发）

---

## 填写表单活动策略

### 步骤
1. **探测表单字段**
   ```bash
   # 提取所有表单字段
   playwright-cli eval "
     Array.from(document.querySelectorAll('input, textarea, select'))
       .map(f => ({
         type: f.type,
         name: f.name,
         placeholder: f.placeholder,
         required: f.required
       }))
   "
   ```

2. **填写信息**
   - 姓名：使用真实姓名（用于奖品发放）
   - 手机号：填写可用手机号
   - 地址：填写收货地址（实物奖品）

3. **提交表单**
   ```bash
   playwright-cli click ".submit-btn"
   ```

4. **验证提交**
   - 检查是否显示"提交成功"
   - 是否收到短信验证
   - 截图保存确认页

### 注意事项
- 手机验证码可能需要手动输入
- 部分表单有格式限制
- 提交后可能无法修改

---

## 组合活动策略

部分活动需要组合多种操作：

### 发布 + 转发
1. 先发布带话题的微头条
2. 转发活动页到个人动态
3. 两者都完成才算参与

### 点赞 + 关注 + 评论
1. 顺序执行：点赞 → 关注 → 评论
2. 每步验证是否成功
3. 任一失败需重试

### 填表 + 发布
1. 先填写报名表单
2. 发布指定内容证明参与
3. 两者关联验证

---

## 通用执行流程

```bash
# 1. 使用 toutiao-agent 获取活动列表
uv run toutiao-agent activities --limit 10

# 2. 使用 playwright-cli 访问活动详情页
playwright-cli open <activity_url>

# 3. 根据活动类型选择策略
# (参考上述对应策略)

# 4. 执行并验证结果
# 5. 截图保存证据
playwright-cli screenshot --filename=result_$(date +%s).png
```

## 失败重试策略

| 失败原因 | 重试策略 |
|-----------|----------|
| 内容审核失败 | 调整内容，降低敏感度后重试 |
| 网络超时 | 等待 3 秒后重试，最多 3 次 |
| 按钮无响应 | 检查页面加载完成，尝试 JavaScript 点击 |
| 活动已结束 | 跳过，记录到失败日志 |
| 需要 APP | 标记为低优先级，暂不处理 |

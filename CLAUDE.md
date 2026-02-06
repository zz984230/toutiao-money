# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

**toutiao-agent** 是一个基于 Python 和 Playwright 构建的今日头条热点自动评论助手。它可以自动浏览头条、生成带有个人立场的评论并发布。

**架构**: 使用 Playwright 进行浏览器自动化，而非 TTBot 或 MCP 服务器。

## 开发命令

```bash
# 安装依赖
uv sync

# 安装 Playwright 浏览器
uv run playwright install chromium

# 运行 CLI 命令
uv run toutiao-agent hot-news --limit 20
uv run toutiao-agent comment <article_id> "<评论内容>"
uv run toutiao-agent start --count 5
uv run toutiao-agent config-show
```

## 代码架构

### 核心组件

```
src/toutiao_agent/
├── main.py           # CLI 入口 (Click 框架)
├── config.py         # 配置管理 (YAML + .env)
├── toutiao_client.py # Playwright 浏览器封装
└── generator.py      # 评论提示词生成
```

### 数据流

```
用户 → CLI → ToutiaoAgent → ToutiaoClient → Playwright → 头条网页
                ↓
          generator.py (提示词) → Claude Code → 评论内容
```

### 关键设计决策

1. **选择 Playwright 而非 TTBot**: TTBot 与新版 Selenium 存在兼容性问题；Playwright 更现代且有更好的反检测能力。

2. **登录流程**:
   - 登录按钮被 CSS 隐藏 (width=0, height=0) → 需使用 JavaScript 点击
   - 账密登录通过 `[aria-label="账密登录"]` → 使用 `click(force=True)`
   - Cookie 持久化保存在 `data/cookies.json`

3. **确认模式**: `config.behavior.confirmation_mode` 控制交互式还是自动执行

4. **状态存储**: 关闭时自动保存 Cookie；暂未使用 SQLite 记录已评论文章 (TODO)

## 重要实现细节

### 头条登录流程 (关键)

登录有一些通过调试发现的特殊行为：

1. **主登录按钮** (`.login-button`): 存在于 DOM 但 `width=0, height=0` - 必须使用 JavaScript 点击:
   ```python
   await page.evaluate('''() => {
       document.querySelector('.login-button').click();
   }''')
   ```

2. **账密登录选项** (`[aria-label="账密登录"]`): 位于"其他登录"区域:
   ```python
   btn = await page.query_selector('[aria-label="账密登录"]')
   await btn.click(force=True)  # 需要强制点击
   ```

3. **切换到账号模式后的输入框**:
   - 用户名: `input[placeholder="手机号/邮箱"]`
   - 密码: `input[type="password"]` 或 `input[placeholder="密码"]`

4. **时序**: 点击登录按钮后等待 5 秒，让弹窗完全加载后再点击账密登录选项。

### 配置

- **主配置**: `config.yaml` (与 `config.py` 中的 DEFAULT_CONFIG 合并)
- **敏感数据**: 使用 `.env` 存储凭据:
  ```
  TOUTIAO_USERNAME=your_username
  TOUTIAO_PASSWORD=your_password
  ```
- **Cookie**: 自动保存到 `data/cookies.json`，下次运行自动加载

### 评论生成

`generator.py` 返回的是**提示词**，而非实际评论。这是有意设计 - Claude Code 根据提示词生成评论内容。工作流程：

1. `generator.generate_prompt(title, abstract)` 返回提示词
2. 用户将提示词发送给 Claude Code
3. Claude Code 生成带有个人立场的评论 (50-100字)
4. 通过 `client.post_comment(article_id, content)` 发布评论

### Playwright 浏览器状态

- 如果 `data/cookies.json` 存在，创建带 Cookie 的浏览器上下文
- 关闭时自动保存 Cookie 到同一文件
- `headless` 默认为 `False`，便于手动处理验证码

## 功能流程

### 1. 登录
- 自动检查已保存的 Cookie
- 如未登录，使用 `.env` 中的账号密码登录
- 登录成功后自动保存 Cookie

### 2. 获取热点新闻
- 访问头条首页
- 提取热点新闻列表（标题、文章ID、链接）

### 3. 生成评论提示词
- 根据新闻标题和摘要生成提示词
- 提示词包含风格要求（长度、立场、情感等）

### 4. 发布评论
- 将评论内容填入评论框
- 点击提交按钮
- 支持交互确认模式

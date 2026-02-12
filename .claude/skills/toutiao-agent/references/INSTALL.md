---
name: toutiao-install
description: 头条 Agent 安装指导。使用此技能当：需要安装 toutiao-agent 项目依赖、配置 Playwright 浏览器、进行初始设置时。
---

# Toutiao Agent - 安装指导

## 环境要求

- Python 3.8+
- uv (Python 包管理器)
- Chromium 浏览器

## 安装步骤

### 1. 安装 Python 依赖

```bash
uv sync
```

### 2. 安装 Playwright 浏览器

```bash
uv run playwright install chromium
```

### 3. 初始化配置

首次运行前，需要配置登录凭据：

**方式一：Cookie 登录（推荐）**

1. 在浏览器中登录 https://www.toutiao.com
2. 打开开发者工具 (F12) → Application → Cookies
3. 复制以下 Cookie 值：
   - `sessionid`
   - `sid_tt`
   - `uid_tt`
4. 创建 `data/cookies.json` 文件并填入 Cookie

**方式二：账密登录**

1. 创建 `.env` 文件：
   ```
   TOUTIAO_USERNAME=你的手机号
   TOUTIAO_PASSWORD=你的密码
   ```
2. 首次运行时会在非 headless 模式下打开浏览器
3. 手动完成短信/滑块验证

### 4. 验证安装

```bash
# 显示当前配置
uv run toutiao-agent config-show

# 测试登录（获取热点新闻）
uv run toutiao-agent hot-news --limit 5
```

## 目录结构

安装后会创建以下目录：

```
toutiao-money/
├── data/
│   ├── cookies.json      # 登录 Cookie（自动生成）
│   ├── comments.db       # SQLite 数据库（自动生成）
│   └── user_data/        # 浏览器用户数据（可选）
├── .env                  # 敏感配置（手动创建）
├── config.yaml           # 主配置文件
└── src/toutiao_agent/    # 源代码
```

## 故障排查

### playwright install 失败
```bash
# 尝试使用系统代理
export HTTP_PROXY=your_proxy
uv run playwright install chromium
```

### uv sync 失败
```bash
# 确保 uv 是最新版本
pip install --upgrade uv
```

### Chromium 下载缓慢
```bash
# 设置镜像源
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
uv run playwright install chromium
```

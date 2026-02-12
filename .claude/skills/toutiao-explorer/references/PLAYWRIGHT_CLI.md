# playwright-cli 安装和使用

playwright-cli 是一个命令行工具，用于使用 Playwright 进行浏览器自动化探索。

## 安装

### 方式 1: npm 安装（推荐）

```bash
npm install -g playwright-cli
```

### 方式 2: 安装脚本

参考腾讯云文章：https://cloud.tencent.com/developer/article/2628720

```bash
# macOS/Linux
curl -O https://raw.githubusercontent.com/msw-demo/playwright-cli/main/install.sh
chmod +x install.sh
./install.sh
```

### 验证安装

```bash
playwright-cli --version
```

## 核心命令

### 页面访问

```bash
# 访问页面并保持交互
playwright-cli open https://www.toutiao.com

# 访问页面并执行脚本
playwright-cli eval "document.title" https://example.com
```

### 信息提取

```bash
# 获取页面文本内容
playwright-cli eval "document.body.innerText"

# 获取特定元素文本
playwright-cli eval "document.querySelector('.activity-title').textContent"

# 获取元素属性
playwright-cli eval "document.querySelector('.btn').getAttribute('data-id')"

# 获取多个元素
playwright-cli eval "Array.from(document.querySelectorAll('.item')).map(e => e.textContent)"
```

### 页面状态检测

```bash
# 检查当前 URL
playwright-cli eval "window.location.href"

# 检查按钮状态
playwright-cli eval "document.querySelector('.join-btn').disabled"

# 检查元素是否存在
playwright-cli eval "document.querySelector('.success-message') !== null"
```

### 截图

```bash
# 截取整个页面
playwright-cli screenshot --filename=page.png

# 截取特定元素
playwright-cli eval "document.querySelector('.container')" --screenshot element.png

# 设置截图尺寸
playwright-cli screenshot --width=1920 --height=1080 --filename=hd.png
```

### 等待元素

```bash
# 等待元素出现（超时 5 秒）
playwright-cli wait ".success-message" --timeout=5000

# 等待 URL 变化
playwright-cli wait-url "*/success" --timeout=10000
```

## 探索模式

### 1. 页面分析

```bash
# 快速提取页面关键信息
playwright-cli eval "
  ({
    title: document.querySelector('.title')?.textContent,
    deadline: document.querySelector('.deadline')?.textContent,
    reward: document.querySelector('.reward')?.textContent,
    status: document.querySelector('.status')?.textContent
  })
"
```

### 2. 按钮探测

```bash
# 查找所有按钮
playwright-cli eval "
  Array.from(document.querySelectorAll('button'))
    .map(b => ({
      text: b.textContent.trim(),
      disabled: b.disabled,
      type: b.getAttribute('class')
    }))
"
```

### 3. 表单探测

```bash
# 查找表单字段
playwright-cli eval "
  Array.from(document.querySelectorAll('input, textarea, select'))
    .map(f => ({
      type: f.type,
      name: f.name,
      placeholder: f.placeholder
    }))
"
```

## 验证参与结果

```bash
# 检查成功提示
playwright-cli eval "
  document.body.innerText.includes('已参与') ||
  document.body.innerText.includes('参与成功') ||
  document.body.innerText.includes('报名成功')
"

# 检查按钮文本变化
playwright-cli eval "document.querySelector('.join-btn').textContent === '已参与'"

# 截图保存证据
playwright-cli screenshot --filename=activity_result_$(date +%s).png
```

## 常见问题

### 安装失败
```bash
# 清理缓存重试
npm cache clean --force
npm install -g playwright-cli
```

### 浏览器驱动问题
```bash
# 手动安装 Chromium
playwright-cli install chromium
```

## 与 toutiao-agent 配合

- toutiao-agent 处理登录状态和 Cookie 管理
- playwright-cli 用于活动页探索和状态检测
- 两者互补：自动化 + 灵活探索

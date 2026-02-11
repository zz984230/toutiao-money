# 头条热点自动评论助手 - 设计文档

**日期**: 2025-02-05
**目标**: 构建自动搜索头条热点新闻并生成个性化评论的工具
**核心方案**: 基于 **Playwright** 实现

---

## 1. 概述

个人运营助手，通过Claude Code交互触发，自动搜索头条热点新闻并生成有个人立场的评论发布。

**核心特性**:
- 手动触发执行
- 可配置的交互确认开关
- 50-100字简短评论，有明确立场和感情色彩
- 避免AI味的口语化表达
- 去重机制避免重复评论

---

## 2. 架构设计

```
用户触发 → Claude Code → 主控脚本 → Playwright → 头条网页
                ↓                           ↑
          提示词模板 ──────────────── 生成评论
```

**组件划分**:
- **Playwright**: 浏览器自动化核心（替代TTBot）
- **主控脚本**: Python流程编排器
- **配置管理**: YAML配置，支持确认模式开关
- **提示词模板**: 去AI化的评论生成模板
- **状态存储**: SQLite记录已评论文章

---

## 3. 技术方案对比

| 方案 | 推荐度 | 优点 | 缺点 |
|------|-------|------|------|
| **Playwright** | ⭐⭐⭐⭐⭐ | 现代、稳定、反检测好、API简洁 | 需要学习新API |
| TTBot | ⭐⭐⭐ | 功能完整 | 代码老旧、兼容性问题 |
| toutiao_mcp_server | ⭐⭐ | 登录稳定 | 无评论功能 |

---

## 3. TTBot 接口映射

### 3.1 获取热点新闻
```python
from component.toutiao import TTBot

bot = TTBot()
hot_news = bot.news_spider.get_hot_news(MDB=False)
```

**返回数据结构**:
```python
{
    "title": "文章标题",
    "abstract": "摘要",
    "group_id": "6709944489160475147",  # 文章ID
    "item_id": "6709944489160475147",
    "source": "来源",
    "behot_time": "2019-07-05 12:50:23",
    "comments_count": 921,  # 评论数
    "go_detail_count": 10000,  # 阅读量
    "article_url": "https://www.toutiao.com/group/..."
}
```

### 3.2 发表评论
```python
account = bot.account  # 需要登录
media_id = '6709944489160475147'
comment_content = '这是我的评论'
result = account.post_comment(comment_content, media_id)
```

**返回数据结构**:
```python
{
    'comment': {
        'id': 6711585125912084488,
        'text': '评论内容',
        'create_time': '2019-07-09 16:58:09',
    },
    'message': 'success',
    'created': True,
}
```

### 3.3 TTBot 认证
```python
# 方式1: 账密登录
account.login(username='手机号', password='密码')

# 方式2: Cookie登录
# 在config.py中设置COOKIE
```

---

## 4. 主控脚本设计 (src/toutiao_agent/main.py)

### 4.1 配置结构
```yaml
# TTBot配置
ttbot:
  username: ""          # 头条账号（手机号）
  password: ""          # 密码
  cookie: ""            # 或使用Cookie

# 行为配置
behavior:
  confirmation_mode: true       # 交互确认开关
  max_comments_per_run: 5       # 每次最多评论数
  min_read_count: 1000          # 最低阅读量阈值
  comment_interval: 30          # 评论间隔(秒)

# 评论风格
style:
  length: "50-100字"
  stance: "理性批判"            # 科技乐观/保守谨慎等
  emotion_level: "medium"       # low/medium/high
```

### 4.2 主流程
```python
# TTBot封装
ttbot = TTBot()
spider = ttbot.news_spider
account = ttbot.account

# 主流程
fetch_hot_news()        # spider.get_hot_news()
filter_articles()        # 按阅读量过滤，排除已评论
generate_comments()      # 逐个生成，可交互确认
publish_comments()       # account.post_comment()
```

### 4.3 交互确认逻辑
- confirmation_mode=True时：
  - 展示热点列表 → 确认继续
  - 生成每个评论 → 确认采纳/修改/跳过
  - 发布前 → 最终确认

### 4.4 状态管理
- SQLite表: `commented_articles(group_id, title, commented_at, comment_id)`
- state.json记录当前进度，支持中断恢复

---

## 5. 提示词模板 (prompts/comment_generation.txt)

```
你是一个真实的头条用户，正在对新闻发表评论。

新闻标题：{title}
新闻摘要：{abstract}

要求：
1. 长度：50-100字
2. 必须有明确的个人立场（支持/反对/质疑）
3. 使用口语化表达，加入情感词汇
4. 避免"综上所述"、"首先其次"等AI常用词
5. 可以用适当的感叹词、反问句
6. 如果是争议话题，不要骑墙，选边站

参考风格：
- 这事儿吧，我觉得...
- 说实话，我真的不理解...
- 我就问一句，这合理吗？

请直接输出评论，不要任何解释：
```

**去AI化技巧**:
- 短句为主，每句不超过15字
- 加入个人观点或经历
- 适当使用网络流行语
- 允许口语化语法不完美

---

## 6. 错误处理

| 场景 | 处理方式 |
|------|---------|
| TTBot登录失败 | 提示检查账号密码，支持手动Cookie |
| 获取热点失败 | 重试3次，降级使用缓存 |
| 评论发布失败 | 记录到failed_comments.json |
| 滑动验证码 | TTBot自动处理，失败则暂停 |
| 内容审核拦截 | 展示原因，询问修改重试 |
| 频率限制 | 等待冷却或停止发布 |

---

## 7. 项目结构

```
toutiao-agent/
├── pyproject.toml          # uv项目配置
├── uv.lock                 # 依赖锁定
├── src/
│   └── toutiao_agent/
│       ├── __init__.py
│       ├── main.py         # CLI入口
│       ├── config.py       # 配置加载
│       ├── ttbot_wrapper.py# TTBot封装
│       ├── generator.py    # 评论生成器
│       └── database.py     # SQLite操作
├── ttbot/                  # TTBot子模块（或作为依赖）
├── prompts/
│   └── comment_generation.txt
├── data/
│   ├── commented.db
│   └── state.json
├── config.yaml             # 敏感配置，不提交
└── config.example.yaml
```

### TTBot 集成方式

**方式1: Git Submodule（推荐）**
```bash
git submodule add https://github.com/zhangfei28/TTBot.git ttbot
```

**方式2: 依赖安装**
```bash
# 将TTBot打包为本地依赖
pip install -e ./ttbot
```

### pyproject.toml
```toml
[project]
name = "toutiao-agent"
version = "0.1.0"
description = "头条热点自动评论助手"
requires-python = ">=3.10"
dependencies = [
    "pyyaml>=6.0",
    "click>=8.1",
    "selenium>=4.0",      # TTBot依赖
    "pymongo>=3.0",       # TTBot依赖
    "requests>=2.31",
]

[project.scripts]
toutiao-agent = "toutiao_agent.main:cli"
```

---

## 8. Claude Code 交互流程

### 开启确认模式
```
用户: 开始搜索热点

→ TTBot获取15条热点新闻
→ 展示列表，询问是否继续
→ 逐个生成评论，询问采纳/修改/跳过
→ 发布前最终确认
→ 输出结果汇总
```

### 关闭确认模式
```
用户: 开始搜索热点（自动模式）

→ 自动执行所有步骤
→ 仅输出结果汇总
```

### 执行命令
```bash
cd /Users/zero/Project/toutiao-agent
uv run toutiao-agent --start
```

---

## 9. TTBot 依赖环境

- Python 3.8+
- Chrome 浏览器（用于Selenium自动登录）
- MongoDB（可选，TTBot默认使用，可关闭）
- ChromeDriver（自动下载）

---

## 10. 实现计划

1. **Phase 1: 基础集成**
   - 集成TTBot到项目
   - 实现配置加载
   - 实现主控流程框架

2. **Phase 2: 核心功能**
   - 实现热点新闻获取
   - 实现评论生成
   - 实现评论发布

3. **Phase 3: 交互优化**
   - 实现确认模式
   - 实现状态持久化
   - 实现错误处理

4. **Phase 4: 提示词优化**
   - 优化去AI化效果
   - 添加立场和情感控制

---

## 11. 注意事项

- TTBot的MongoDB可以设置为不使用（`MDB=False`）
- 首次登录需要Selenium处理滑动验证
- 评论频率需要控制，避免被限制
- TTBot使用GPL-3.0许可证

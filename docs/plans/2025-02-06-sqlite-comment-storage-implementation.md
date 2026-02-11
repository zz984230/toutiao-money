# SQLite 评论存储实施计划

## 步骤

### 1. 创建 storage.py 模块
- 文件：`src/toutiao_agent/storage.py`
- 实现 `CommentStorage` 类
- 数据库初始化逻辑
- 核心 API：`is_commented()`, `add_comment()`, `get_history()`, `get_comment_count()`

### 2. 更新 config.py
- 添加 `storage` 配置到 `DEFAULT_CONFIG`
- 添加 `storage` 属性到 `Config` 类

### 3. 集成到 toutiao_client.py
- 修改 `get_hot_news()` 方法，添加过滤逻辑

### 4. 集成到 main.py
- 修改 `ToutiaoAgent.post_comment()`，成功后记录
- 添加 `history` 命令
- 添加 `stats` 命令

### 5. 测试
- 手动测试完整流程
- 验证过滤功能
- 验证历史记录

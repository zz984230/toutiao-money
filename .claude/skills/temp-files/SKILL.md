---
name: temp-files
description: 临时文件管理。使用此技能当：需要整理、清理或管理项目探索过程中产生的临时文件（如截图、日志等）时使用。
---

# Temp Files - 临时文件管理

管理项目探索过程中产生的临时文件，包括截图、日志、缓存等。

## 目录结构

```
data/temp/
├── screenshots/    # 活动探索截图
├── logs/          # 运行日志
└── cache/         # 临时缓存
```

## 快速使用

```bash
# 整理临时文件到指定目录
uv run temp-files organize

# 清理过期临时文件
uv run temp-files clean --days 7

# 查看临时文件占用
uv run temp-files stats
```

## 文件类型

### 截图文件 (screenshots/)
- **活动页面截图**: `activity_*.png`
- **创作者中心截图**: `creator_*.png`
- **移动端截图**: `mobile_*.png`
- **其他探索截图**: 按活动名称命名

### 日志文件 (logs/)
- **运行日志**: `temp_files_*.log`
- **错误日志**: `error_*.log`

## 清理策略

**自动清理**：
- 7天前的截图自动标记为过期
- 30天前的日志自动删除
- cache 目录每次启动时清空

**手动清理**：
```bash
# 清理所有截图
rm -rf data/temp/screenshots/*.png

# 清理所有日志
rm -rf data/temp/logs/*.log
```

## Git 忽略

临时文件目录已添加到 `.gitignore`：
```
data/temp/
*.png
*.log
```

## 使用场景

1. **探索过程中**：自动保存截图到 `data/temp/screenshots/`
2. **活动分析时**：保存活动页面截图作为证据
3. **调试问题时**：保存详细日志到 `data/temp/logs/`
4. **会话结束后**：选择性保留重要截图，清理其他文件

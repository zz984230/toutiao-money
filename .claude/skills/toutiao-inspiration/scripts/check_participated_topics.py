# -*- coding: utf-8 -*-
"""检查已参与的话题"""
import sqlite3
import json
import sys
import io
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 读取热门话题
topics_file = Path("D:/code/toutiao-money/.claude/data/hotspot_topics_clean.json")
with open(topics_file, 'r', encoding='utf-8') as f:
    hot_topics = json.load(f)

# 读取已发布的话题
db_path = Path("D:/code/toutiao-money/data/comments.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.execute('SELECT hashtags FROM micro_headlines WHERE hashtags IS NOT NULL')
participated_hashtags = set()
for row in cursor.fetchall():
    hashtag = row[0]
    if hashtag:
        # 提取话题名称，去掉 # 号
        topic_name = hashtag.strip('#')
        participated_hashtags.add(topic_name)

conn.close()

# 展示可用话题
print(f"\n发现 {len(hot_topics)} 个热门话题")
print(f"已参与 {len(participated_hashtags)} 个话题\n")
print("=" * 80)
print("可用话题列表（未参与）:\n")

available_count = 0
for i, item in enumerate(hot_topics, 1):
    topic = item['topic']
    read_count = item['readCount']

    if topic in participated_hashtags:
        print(f"{i:2d}. #{topic}# - 阅读量: {read_count}万 ✅ 已参与")
    else:
        print(f"{i:2d}. #{topic}# - 阅读量: {read_count}万 ⭕ 可参与")
        available_count += 1

print("\n" + "=" * 80)
print(f"可用话题数: {available_count}")

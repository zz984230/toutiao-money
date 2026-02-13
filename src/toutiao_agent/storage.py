"""SQLite 评论存储模块"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from .config import config


class CommentStorage:
    """评论存储类"""

    def __init__(self, db_path: Optional[str] = None):
        """初始化存储

        Args:
            db_path: 数据库文件路径，默认从配置读取
        """
        self.db_path = db_path or config.storage.get('db_file', 'data/comments.db')
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self._conn is None:
            # 确保目录存在
            db_file = Path(self.db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)

            self._conn = sqlite3.connect(str(db_file))
            self._conn.row_factory = sqlite3.Row  # 支持字典访问
        return self._conn

    def _init_db(self):
        """初始化数据库表"""
        conn = self._get_connection()
        # 评论表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT NOT NULL UNIQUE,
                title TEXT,
                url TEXT,
                content TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        # 微头条表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS micro_headlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id TEXT,
                activity_title TEXT,
                content TEXT,
                hashtags TEXT,
                images TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL,
                published_at TEXT
            )
        ''')
        # 活动参与记录表
        conn.execute('''
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
        conn.commit()

    def is_commented(self, article_id: str) -> bool:
        """检查文章是否已评论

        Args:
            article_id: 文章ID

        Returns:
            bool: 是否已评论
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                'SELECT 1 FROM comments WHERE article_id = ? LIMIT 1',
                (article_id,)
            )
            return cursor.fetchone() is not None
        except Exception as e:
            print(f"检查评论状态失败: {e}")
            return False

    def add_comment(self, article_id: str, title: str, url: str, content: str) -> bool:
        """添加评论记录

        Args:
            article_id: 文章ID
            title: 文章标题
            url: 文章链接
            content: 评论内容

        Returns:
            bool: 是否成功添加
        """
        try:
            conn = self._get_connection()
            created_at = datetime.now().isoformat()
            conn.execute('''
                INSERT OR IGNORE INTO comments (article_id, title, url, content, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (article_id, title, url, content, created_at))
            conn.commit()
            return True
        except Exception as e:
            print(f"添加评论记录失败: {e}")
            return False

    def get_history(self, limit: Optional[int] = None) -> List[Dict]:
        """获取评论历史

        Args:
            limit: 返回条数限制，None 表示全部

        Returns:
            List[Dict]: 评论记录列表，按时间倒序
        """
        try:
            conn = self._get_connection()
            if limit:
                cursor = conn.execute('''
                    SELECT article_id, title, url, content, created_at
                    FROM comments
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
            else:
                cursor = conn.execute('''
                    SELECT article_id, title, url, content, created_at
                    FROM comments
                    ORDER BY created_at DESC
                ''')

            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取评论历史失败: {e}")
            return []

    def get_comment_count(self) -> int:
        """获取评论总数

        Returns:
            int: 评论总数
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute('SELECT COUNT(*) FROM comments')
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"获取评论总数失败: {e}")
            return 0

    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    # ============ 微头条相关方法 ============

    def add_micro_headline(
        self,
        content: str,
        activity_id: Optional[str] = None,
        activity_title: Optional[str] = None,
        hashtags: Optional[str] = None,
        images: Optional[str] = None
    ) -> bool:
        """添加微头条记录

        Args:
            content: 微头条内容
            activity_id: 活动 ID（如果有）
            activity_title: 活动标题（如果有）
            hashtags: 话题标签
            images: 图片列表（JSON 字符串）

        Returns:
            bool: 是否成功添加
        """
        try:
            conn = self._get_connection()
            created_at = datetime.now().isoformat()
            conn.execute('''
                INSERT INTO micro_headlines (
                    activity_id, activity_title, content, hashtags, images, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, 'published', ?)
            ''', (activity_id, activity_title, content, hashtags, images, created_at))
            conn.commit()
            return True
        except Exception as e:
            print(f"添加微头条记录失败: {e}")
            return False

    def get_micro_headlines(self, limit: Optional[int] = None) -> List[Dict]:
        """获取微头条历史

        Args:
            limit: 返回条数限制，None 表示全部

        Returns:
            List[Dict]: 微头条记录列表，按时间倒序
        """
        try:
            conn = self._get_connection()
            if limit:
                cursor = conn.execute('''
                    SELECT id, activity_id, activity_title, content, hashtags, images, status, created_at, published_at
                    FROM micro_headlines
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
            else:
                cursor = conn.execute('''
                    SELECT id, activity_id, activity_title, content, hashtags, images, status, created_at, published_at
                    FROM micro_headlines
                    ORDER BY created_at DESC
                ''')

            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取微头条历史失败: {e}")
            return []

    def get_micro_headline_count(self) -> int:
        """获取微头条总数

        Returns:
            int: 微头条总数
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute('SELECT COUNT(*) FROM micro_headlines')
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"获取微头条总数失败: {e}")
            return 0

    def is_activity_participated(self, activity_id: str) -> bool:
        """检查活动是否已参与（检查 activity_participations 表）

        Args:
            activity_id: 活动 ID

        Returns:
            bool: 是否已参与该活动
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                'SELECT COUNT(*) FROM activity_participations WHERE activity_id = ? AND user_confirmed = 1',
                (activity_id,)
            )
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            print(f"检查活动参与状态失败: {e}")
            return False

    def is_activity_processed(self, activity_id: str) -> bool:
        """检查活动是否已处理过（包括已参与和已跳过）

        Args:
            activity_id: 活动 ID

        Returns:
            bool: 是否已处理过该活动（包括跳过）
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                'SELECT COUNT(*) FROM activity_participations WHERE activity_id = ?',
                (activity_id,)
            )
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            print(f"检查活动处理状态失败: {e}")
            return False

    # ============ 活动参与相关方法 ============

    def add_activity_participation(
        self,
        activity_id: str,
        activity_title: Optional[str] = None,
        operation_type: Optional[str] = None,
        confidence: float = 0.0,
        ai_analysis: Optional[str] = None,
        user_confirmed: bool = False,
        execution_result: Optional[str] = None
    ) -> None:
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
        try:
            conn = self._get_connection()

            # 如果 ai_analysis 是 dict，转换为 JSON 字符串
            ai_analysis_json = ai_analysis
            if isinstance(ai_analysis, dict):
                ai_analysis_json = json.dumps(ai_analysis, ensure_ascii=False)

            conn.execute('''
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
            conn.commit()
        except Exception as e:
            print(f"记录活动参与失败: {e}")

    def get_activity_participations(self, limit: int = 20) -> List[Dict]:
        """获取活动参与记录

        Args:
            limit: 返回记录数

        Returns:
            参与记录列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute('''
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
        except Exception as e:
            print(f"获取活动参与记录失败: {e}")
            return []


# 全局单例
_storage: Optional[CommentStorage] = None


def get_storage() -> CommentStorage:
    """获取存储单例"""
    global _storage
    if _storage is None:
        _storage = CommentStorage()
    return _storage


# 导出便捷实例
storage = get_storage()

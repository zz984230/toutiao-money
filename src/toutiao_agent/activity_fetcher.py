"""活动抓取模块 - 从头条创作者平台获取活动列表"""

import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from .config import config


class Activity:
    """活动数据类"""

    def __init__(self, data: Dict):
        """从 API 数据初始化活动

        Args:
            data: API 返回的活动数据
        """
        self.activity_id = data.get('activity_id')
        self.title = data.get('title', '')
        self.introduction = data.get('introduction', '')
        self.activity_time = data.get('activity_time', '')
        self.activity_reward = data.get('activity_reward', '')
        self.activity_participants = data.get('activity_participants', '')
        self.part_in = data.get('part_in', 0)  # 是否已参与
        self.status = data.get('status', 0)  # 活动状态
        self.hashtag_id = data.get('hashtag_id', 0)
        self.hashtag_name = data.get('hashtag_name', '')
        self.href = data.get('href', '')
        self.activity_start_time = data.get('activity_start_time', 0)
        self.activity_end_time = data.get('activity_end_time', 0)

        # 原始数据
        self.raw_data = data

    def is_expired(self) -> bool:
        """检查活动是否已过期

        Returns:
            bool: 是否已过期
        """
        if self.activity_end_time == 0:
            return False
        # activity_end_time 是 Unix 时间戳
        return self.activity_end_time < datetime.now().timestamp()

    def get_hashtag(self) -> Optional[str]:
        """获取活动话题标签

        Returns:
            str: 话题标签（如 #话题名#），如果没有则返回 None
        """
        if self.hashtag_name:
            return f"#{self.hashtag_name}#"
        # 从标题中提取话题（格式：#话题名#）
        import re
        match = re.search(r'#([^#]+)#', self.title + ' ' + self.introduction)
        if match:
            return match.group(0)
        return None

    def __repr__(self) -> str:
        return f"Activity(id={self.activity_id}, title={self.title[:20]}...)"


class ActivityFetcher:
    """活动抓取类"""

    # API 端点
    API_BASE = "https://mp.toutiao.com/mp/agw/activity"
    APP_ID = "1231"
    BIZ_ID = "1"

    def __init__(self, cookie_file: Optional[str] = None):
        """初始化活动抓取器

        Args:
            cookie_file: Cookie 文件路径，默认从配置读取
        """
        self.cookie_file = cookie_file or config.playwright.get('cookies_file', 'data/cookies.json')
        self.cookies = self._load_cookies()

    def _load_cookies(self) -> List[Dict]:
        """加载 Cookie

        Returns:
            List[Dict]: Cookie 列表
        """
        cookie_path = Path(self.cookie_file)
        if not cookie_path.exists():
            return []

        with open(cookie_path, 'r', encoding='utf-8') as f:
            cookies_data = json.load(f)
            # 处理两种可能的格式
            if isinstance(cookies_data, dict) and 'cookies' in cookies_data:
                return cookies_data['cookies']
            return cookies_data if isinstance(cookies_data, list) else []

    def _build_cookie_header(self) -> str:
        """构建 Cookie 请求头

        Returns:
            str: Cookie 字符串
        """
        return '; '.join([f"{c['name']}={c['value']}" for c in self.cookies])

    def _make_request(self, url: str) -> Dict:
        """发送 HTTP 请求

        Args:
            url: 请求 URL

        Returns:
            Dict: 响应数据
        """
        req = urllib.request.Request(url)
        req.add_header('Cookie', self._build_cookie_header())
        req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        req.add_header('Referer', 'https://mp.toutiao.com/profile_v4/activity/task-list')

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            return {
                'error': f'HTTP 错误: {e.code}',
                'success': False
            }
        except urllib.error.URLError as e:
            return {
                'error': f'连接错误: {e.reason}',
                'success': False
            }
        except Exception as e:
            return {
                'error': f'未知错误: {str(e)}',
                'success': False
            }

    def fetch_activities(
        self,
        offset: int = 0,
        limit: int = 24,
        category: str = "全部",
        only_ongoing: bool = True,
        only_unparticipated: bool = True
    ) -> List[Activity]:
        """获取活动列表

        Args:
            offset: 分页偏移
            limit: 每页数量
            category: 分类筛选
            only_ongoing: 仅获取进行中的活动
            only_unparticipated: 仅获取未参与的活动

        Returns:
            List[Activity]: 活动列表
        """
        # 构建查询参数
        params = {
            'offset': offset,
            'limit': limit,
            'act_status': '0' if only_ongoing else '',  # 0=进行中
            'part_status': '0' if only_unparticipated else '',  # 0=未参与
            'title': '',
            'category': category,
            'biz_id': self.BIZ_ID,
            'sort_type': '1',
            'enter_from': '',
            'online_platform_index': '0',
            'enter_from_mp': '2',
            'media_id': '0',
            'app_id': self.APP_ID
        }

        query_string = urllib.parse.urlencode(params)
        url = f"{self.API_BASE}/list/v2/?{query_string}"

        result = self._make_request(url)

        if 'error' in result:
            print(f"❌ 获取活动失败: {result['error']}")
            return []

        if result.get('code') != 0:
            print(f"❌ API 错误: {result.get('message', '未知错误')}")
            return []

        # 解析活动列表
        activity_list_data = result.get('data', {}).get('activity_list', [])
        activities = [Activity(data) for data in activity_list_data]

        # 过滤过期活动
        if only_ongoing:
            activities = [a for a in activities if not a.is_expired()]

        return activities

    def get_categories(self) -> List[str]:
        """获取所有活动分类

        Returns:
            List[str]: 分类列表
        """
        params = {
            'act_status': '0',
            'biz_id': self.BIZ_ID,
            'app_id': self.APP_ID
        }

        query_string = urllib.parse.urlencode(params)
        url = f"{self.API_BASE}/get_all_category/?{query_string}"

        result = self._make_request(url)

        if 'error' in result:
            print(f"❌ 获取分类失败: {result['error']}")
            return ['全部']

        if result.get('code') != 0:
            return ['全部']

        # 解析分类列表
        categories_data = result.get('data', [])
        categories = ['全部'] + [c.get('name', '') for c in categories_data if c.get('name')]

        return categories

    def get_activity_detail(self, activity_id: int) -> Optional[Dict]:
        """获取活动详情

        Args:
            activity_id: 活动 ID

        Returns:
            Optional[Dict]: 活动详情数据
        """
        # 这个 API 可能需要从活动列表中获取详情
        # 或者通过访问活动页面来获取
        # 暂时返回空，后续可以扩展
        return None


# 全局单例
_fetcher: Optional[ActivityFetcher] = None


def get_activity_fetcher() -> ActivityFetcher:
    """获取活动抓取器单例"""
    global _fetcher
    if _fetcher is None:
        _fetcher = ActivityFetcher()
    return _fetcher


# 导出便捷实例
activity_fetcher = get_activity_fetcher()

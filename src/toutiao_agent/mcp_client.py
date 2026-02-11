"""MCP 客户端模块 - 调用 toutiao_mcp_server 发布微头条

使用标准库 urllib 实现，无需外部依赖
"""

import json
import urllib.request
import urllib.error
from typing import Optional, List, Dict
from .config import config


class ToutiaoMCPClient:
    """今日头条 MCP 服务器客户端"""

    def __init__(self, base_url: Optional[str] = None):
        """初始化 MCP 客户端

        Args:
            base_url: MCP 服务器地址，默认从配置读取
        """
        self.base_url = base_url or config.mcp.get('server_url', 'http://localhost:8003')
        self.timeout = config.mcp.get('timeout', 60)

    def _post(self, endpoint: str, data: Dict) -> Dict:
        """发送 POST 请求到 MCP 服务器

        Args:
            endpoint: API 端点
            data: 请求数据

        Returns:
            Dict: 响应结果
        """
        url = f"{self.base_url}{endpoint}"
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=json_data,
            headers={
                'Content-Type': 'application/json',
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result
        except urllib.error.URLError as e:
            if hasattr(e, 'reason'):
                return {
                    'success': False,
                    'error': f'无法连接到 MCP 服务器 ({self.base_url}): {e.reason}'
                }
            else:
                return {
                    'success': False,
                    'error': f'无法连接到 MCP 服务器 ({self.base_url})，请确保服务器已启动'
                }
        except urllib.error.HTTPError as e:
            return {
                'success': False,
                'error': f'HTTP 错误: {e.code}'
            }
        except TimeoutError:
            return {
                'success': False,
                'error': '请求超时，请检查服务器状态'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'未知错误: {str(e)}'
            }

    async def check_login_status(self) -> Dict:
        """检查登录状态

        Returns:
            Dict: 包含 is_logged_in 和 user_info 的响应
        """
        return self._post('/check_login_status', {})

    async def login_with_credentials(self, username: str, password: str) -> Dict:
        """使用账密登录

        Args:
            username: 用户名（手机号/邮箱）
            password: 密码

        Returns:
            Dict: 登录结果
        """
        return self._post('/login_with_credentials', {
            'username': username,
            'password': password
        })

    async def publish_micro_post(
        self,
        content: str,
        images: Optional[List[str]] = None,
        topic: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict:
        """发布微头条

        Args:
            content: 微头条内容
            images: 配图路径列表（最多9张）
            topic: 话题标签（如 #科技#）
            location: 位置信息

        Returns:
            Dict: 发布结果
        """
        data = {'content': content}
        if images:
            data['images'] = images
        if topic:
            data['topic'] = topic
        if location:
            data['location'] = location

        return self._post('/publish_micro_post', data)


# 全局单例
_mcp_client: Optional[ToutiaoMCPClient] = None


def get_mcp_client() -> ToutiaoMCPClient:
    """获取 MCP 客户端单例"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = ToutiaoMCPClient()
    return _mcp_client


# 导出便捷实例
mcp_client = get_mcp_client()

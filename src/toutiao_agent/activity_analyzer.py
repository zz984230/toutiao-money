"""活动分析模块 - 分析活动页面并生成参与建议"""

import subprocess
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Optional, Any
from .activity_types import OperationType


@dataclass
class ActionResult:
    """活动分析结果"""

    activity_title: str              # 活动标题
    activity_intro: str              # 活动介绍
    operation_type: OperationType     # 操作类型
    confidence: float                # 置信度 0-1
    detected_elements: Dict[str, Any]  # 检测到的元素
    suggested_action: str             # 建议操作描述

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于存储"""
        return {
            'activity_title': self.activity_title,
            'activity_intro': self.activity_intro,
            'operation_type': self.operation_type.value,
            'confidence': self.confidence,
            'detected_elements': self.detected_elements,
            'suggested_action': self.suggested_action
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionResult':
        """从字典创建实例"""
        return cls(
            activity_title=data.get('activity_title', ''),
            activity_intro=data.get('activity_intro', ''),
            operation_type=OperationType(data.get('operation_type', OperationType.OTHER.value)),
            confidence=data.get('confidence', 0.0),
            detected_elements=data.get('detected_elements', {}),
            suggested_action=data.get('suggested_action', '')
        )


class ActivityAnalyzer:
    """活动分析器 - 使用 AI 分析活动页面"""

    def __init__(self, base_url: str = "https://www.toutiao.com"):
        """初始化分析器

        Args:
            base_url: 头条基础 URL
        """
        self.base_url = base_url

    def _get_page_screenshot(self, url: str, output_path: str) -> bool:
        """使用 playwright-cli 获取页面截图

        Args:
            url: 活动页面 URL
            output_path: 输出文件路径

        Returns:
            是否成功
        """
        try:
            result = subprocess.run(
                ['playwright', 'screenshot', url, '-o', output_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            print(f"截图失败: {e}")
            return False

    def _get_page_text(self, url: str) -> str:
        """使用 playwright-cli 获取页面文本

        Args:
            url: 活动页面 URL

        Returns:
            页面文本内容
        """
        try:
            result = subprocess.run(
                ['playwright', 'code', url, '-c', 'document.body.innerText'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                # 解析输出，提取实际文本
                return result.stdout.strip()
            return ""
        except Exception as e:
            print(f"获取页面文本失败: {e}")
            return ""

    def _get_interactive_elements(self, url: str) -> list:
        """获取页面可交互元素

        Args:
            url: 活动页面 URL

        Returns:
            元素列表
        """
        try:
            code = '''
            Array.from(document.querySelectorAll('button, a, input, textarea'))
                .filter(el => el.offsetParent !== null)  // 只取可见元素
                .map(el => ({
                    tag: el.tagName,
                    text: el.textContent?.slice(0, 50),
                    type: el.type || '',
                    id: el.id || '',
                    className: el.className || ''
                }))
            '''
            result = subprocess.run(
                ['playwright', 'code', url, '-c', code],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                # 尝试解析 JSON 输出
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    pass
            return []
        except Exception as e:
            print(f"获取交互元素失败: {e}")
            return []

    async def analyze(self, activity) -> ActionResult:
        """分析活动页面，返回操作建议

        Args:
            activity: Activity 对象

        Returns:
            ActionResult 包含操作类型、活动内容、置信度等
        """
        # TODO: 实现具体分析逻辑
        raise NotImplementedError("analyze 方法将在后续任务中实现")

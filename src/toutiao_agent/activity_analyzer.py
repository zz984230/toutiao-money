"""活动分析模块 - 分析活动页面并生成参与建议"""

import subprocess
import json
import tempfile
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Optional, Any, List
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
    """活动分析器 - 使用 AI 分析活动页面（E002进化：添加直接页面分析）"""

    def __init__(self, base_url: str = "https://www.toutiao.com"):
        """初始化分析器

        Args:
            base_url: 头条基础 URL
        """
        self.base_url = base_url

    async def analyze_from_page(self, activity, page) -> ActionResult:
        """直接从已加载的页面分析活动（E002进化新增方法）

        Args:
            activity: Activity 对象
            page: 已加载的 Playwright Page 对象

        Returns:
            ActionResult 包含操作类型、置信度等
        """
        activity_id = str(activity.activity_id)

        print(f"[E002进化] 从当前页面分析活动: {activity.title}")

        try:
            # 使用 JavaScript 直接分析页面元素
            analysis_result = await page.evaluate('''() => {
                const results = {
                    hasInput: false,
                    hasTextarea:false,
                    hasPublishButton:false,
                    hasActivityCard:false,
                    inputTypes:[],
                    buttonTexts:[],
                    pageTitle:'',
                    pageText:''
                };

                // 获取页面标题
                const titleEl = document.querySelector('.activity-title, h1, .title');
                if (titleEl) {
                    results.pageTitle = titleEl.textContent?.trim().substring(0, 50) || '';
                }

                // 检测输入框
                const contenteditables = document.querySelectorAll('[contenteditable="true"]');
                const textareas = document.querySelectorAll('textarea');

                results.hasInput = contenteditables.length > 0 || textareas.length > 0;

                if (contenteditables.length > 0) {
                    contenteditables.forEach((el, i) => {
                        if (i < 3) {  // 只记录前3个
                            results.inputTypes.push('contenteditable');
                        }
                    });
                }

                if (textareas.length > 0) {
                    textareas.forEach((el, i) => {
                        if (i < 3) {  // 只记录前3个
                            results.inputTypes.push('textarea');
                        }
                    });
                }

                // 检测发布/提交按钮
                const buttons = Array.from(document.querySelectorAll('button, [role="button"]'));
                const publishKeywords = ['发布', '发送', '提交', '确认', '立即参与'];

                buttons.forEach(btn => {
                    const text = btn.textContent?.trim() || '';
                    results.buttonTexts.push(text.substring(0, 20));
                    if (publishKeywords.some(kw => text.includes(kw))) {
                        results.hasPublishButton = true;
                    }
                });

                // 检测活动卡片（用于验证是否在活动页面）
                const activityLinks = Array.from(document.querySelectorAll('a[href*="activity"]'));
                results.hasActivityCard = activityLinks.length > 0;

                // 获取页面文本（用于回退规则分析）
                results.pageText = document.body.innerText.substring(0, 1000);

                return results;
            }''')

            # 根据检测结果确定操作类型
            operation_type, confidence, suggested = self._analyze_from_elements(
                analysis_result, activity
            )

            return ActionResult(
                activity_title=activity.title,
                activity_intro=activity.introduction,
                operation_type=operation_type,
                confidence=confidence,
                detected_elements={
                    'input_types': analysis_result.get('inputTypes', []),
                    'has_publish_button': analysis_result.get('hasPublishButton', False),
                    'button_texts': analysis_result.get('buttonTexts', []),
                    'has_activity_card': analysis_result.get('hasActivityCard', False),
                    'page_title': analysis_result.get('pageTitle', ''),
                },
                suggested_action=suggested
            )

        except Exception as e:
            print(f"[E002进化] 页面分析失败: {e}")
            # 降级到规则分析
            return ActionResult(
                activity_title=activity.title,
                activity_intro=activity.introduction,
                operation_type=OperationType.GENERATE_CONTENT,
                confidence=0.3,  # 降低置信度但仍尝试
                detected_elements={'error': str(e)},
                suggested_action="页面分析失败，建议手动生成原创内容参与"
            )

    def _analyze_from_elements(self, analysis: Dict, activity) -> tuple:
        """从页面元素分析结果确定操作类型（E002进化新增方法）

        Args:
            analysis: JavaScript 返回的页面分析结果
            activity: Activity 对象

        Returns:
            (operation_type, confidence, suggested_action)
        """
        has_input = analysis.get('hasInput', False)
        has_publish = analysis.get('hasPublishButton', False)
        has_activity_card = analysis.get('hasActivityCard', False)
        button_texts = analysis.get('buttonTexts', [])
        page_title = analysis.get('pageTitle', '')
        page_text = analysis.get('pageText', '')

        # 检测是否在活动页面（有活动卡片链接）
        if has_activity_card:
            return OperationType.GENERATE_CONTENT, 0.95, "在活动页面中，使用输入框填写内容并发布"

        # 检测是否有发布按钮
        if has_publish:
            return OperationType.GENERATE_CONTENT, 0.90, "检测到发布按钮，可以填写内容并发布"

        # 检测有输入框但没发布按钮（可能需要先点击某按钮）
        if has_input and not has_publish:
            return OperationType.GENERATE_CONTENT, 0.70, "检测到输入框，可能需要先点击参与按钮"

        # 一键参与检测
        if any('一键参与' in text for text in button_texts):
            return OperationType.ONE_CLICK, 0.95, "检测到一键参与按钮"

        # 默认：生成原创内容
        return OperationType.GENERATE_CONTENT, 0.50, "未检测到特殊操作类型，建议生成原创内容"

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
        # 使用正确的活动页面URL格式（E001进化更新）
        if activity.href:
            url = activity.href
        else:
            # 正确的活动URL格式
            url = f"https://mp.toutiao.com/profile_v3_public/public/activity/?activity_location=panel_invite_discuss_hot_mp&id={activity.activity_id}"

        print(f"正在分析活动: {activity.title}")
        print(f"URL: {url}")

        # 获取页面信息
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            screenshot_path = f.name

        success = self._get_page_screenshot(url, screenshot_path)
        if not success:
            return ActionResult(
                activity_title=activity.title,
                activity_intro=activity.introduction,
                operation_type=OperationType.OTHER,
                confidence=0.0,
                detected_elements={},
                suggested_action="无法获取活动页面，请手动处理"
            )

        page_text = self._get_page_text(url)
        elements = self._get_interactive_elements(url)

        # 使用规则分析
        operation_type, confidence, suggested = self._simple_rule_analysis(elements, page_text)

        return ActionResult(
            activity_title=activity.title,
            activity_intro=activity.introduction,
            operation_type=operation_type,
            confidence=confidence,
            detected_elements={
                'page_text': page_text[:500],
                'interactive_elements': elements[:10],
                'screenshot_path': screenshot_path
            },
            suggested_action=suggested
        )

    def _simple_rule_analysis(self, elements: list, page_text: str) -> tuple:
        """基于简单规则分析活动类型

        Args:
            elements: 交互元素列表
            page_text: 页面文本

        Returns:
            (operation_type, confidence, suggested_action)
        """
        # 检查一键参与按钮
        for el in elements:
            text = (el.get('text') or '').lower()
            if any(keyword in text for keyword in ['立即参与', '一键参与', '马上参加', '立即报名']):
                return OperationType.ONE_CLICK, 0.85, f"检测到 '{el.get('text')}' 按钮，建议点击"

        # 检查表单元素
        has_form = any(el.get('tag') in ['INPUT', 'TEXTAREA'] for el in elements)
        if has_form:
            return OperationType.FILL_FORM, 0.70, "检测到表单输入框，建议填写表单"

        # 检查转发/分享
        page_text_lower = page_text.lower()
        if any(keyword in page_text_lower for keyword in ['转发', '分享', 'share']):
            return OperationType.LIKE_SHARE, 0.60, "检测到转发/分享相关内容"

        # 默认生成原创
        return OperationType.GENERATE_CONTENT, 0.50, "未检测到特殊操作类型，建议生成原创内容"

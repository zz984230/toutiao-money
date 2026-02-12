"""活动操作类型定义"""

from __future__ import annotations

from enum import Enum


class OperationType(Enum):
    """活动参与操作类型"""

    GENERATE_CONTENT = "generate_content"  # 生成原创微头条
    LIKE_SHARE = "like_share"              # 点赞/转发
    FILL_FORM = "fill_form"                # 填写表单
    ONE_CLICK = "one_click"                # 一键参与
    OTHER = "other"                        # 其他类型

    _LABELS = {
        GENERATE_CONTENT: "生成原创",
        LIKE_SHARE: "点赞转发",
        FILL_FORM: "填写表单",
        ONE_CLICK: "一键参与",
        OTHER: "其他",
    }

    @property
    def label(self) -> str:
        """中文标签"""
        return self._LABELS[self]

    def __str__(self) -> str:
        return self.label

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
转换错误处理器 - Conversion Error Handler

功能：
1. 收集转换过程中的错误和警告
2. 提供错误统计
3. 支持错误过滤和查询

作者：远
日期：2026-04-03
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class ErrorLevel(Enum):
    """错误级别"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ConversionError:
    """转换错误"""
    error_type: str
    message: str
    line_no: int = -1
    level: ErrorLevel = ErrorLevel.ERROR
    timestamp: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'type': self.error_type,
            'message': self.message,
            'line': self.line_no,
            'level': self.level.value,
            'timestamp': self.timestamp,
            'context': self.context
        }


class ConversionErrorHandler:
    """
    转换错误处理器

    职责：
    1. 收集错误和警告
    2. 提供错误查询接口
    3. 生成错误报告
    """

    def __init__(self):
        """初始化错误处理器"""
        self.errors: List[ConversionError] = []
        self.warnings: List[ConversionError] = []
        self._error_counts: Dict[str, int] = {}

    def add_error(
        self,
        error_type: str,
        message: str,
        line_no: int = -1,
        context: Dict[str, Any] = None
    ):
        """
        添加错误

        Args:
            error_type: 错误类型
            message: 错误消息
            line_no: 行号
            context: 额外上下文信息
        """
        error = ConversionError(
            error_type=error_type,
            message=message,
            line_no=line_no,
            level=ErrorLevel.ERROR,
            timestamp=datetime.now().timestamp(),
            context=context or {}
        )
        self.errors.append(error)

        # 更新计数
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1

    def add_warning(
        self,
        warning_type: str,
        message: str,
        line_no: int = -1,
        context: Dict[str, Any] = None
    ):
        """
        添加警告

        Args:
            warning_type: 警告类型
            message: 警告消息
            line_no: 行号
            context: 额外上下文信息
        """
        warning = ConversionError(
            error_type=warning_type,
            message=message,
            line_no=line_no,
            level=ErrorLevel.WARNING,
            timestamp=datetime.now().timestamp(),
            context=context or {}
        )
        self.warnings.append(warning)

        # 更新计数
        count_key = f"WARNING_{warning_type}"
        self._error_counts[count_key] = self._error_counts.get(count_key, 0) + 1

    def add_info(
        self,
        message: str,
        line_no: int = -1,
        context: Dict[str, Any] = None
    ):
        """
        添加信息

        Args:
            message: 信息消息
            line_no: 行号
            context: 额外上下文信息
        """
        info = ConversionError(
            error_type="INFO",
            message=message,
            line_no=line_no,
            level=ErrorLevel.INFO,
            timestamp=datetime.now().timestamp(),
            context=context or {}
        )
        self.errors.append(info)  # 信息也加入错误列表以便查询

    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0

    def get_errors(self) -> List[ConversionError]:
        """获取所有错误"""
        return self.errors

    def get_warnings(self) -> List[ConversionError]:
        """获取所有警告"""
        return self.warnings

    def get_errors_by_type(self, error_type: str) -> List[ConversionError]:
        """按类型获取错误"""
        return [e for e in self.errors if e.error_type == error_type]

    def get_errors_by_line(self, line_no: int) -> List[ConversionError]:
        """按行号获取错误"""
        return [e for e in self.errors if e.line_no == line_no]

    def get_error_count(self, error_type: str = None) -> int:
        """获取错误计数"""
        if error_type:
            return self._error_counts.get(error_type, 0)
        return len(self.errors)

    def get_warning_count(self) -> int:
        """获取警告计数"""
        return len(self.warnings)

    def clear(self):
        """清空所有错误和警告"""
        self.errors.clear()
        self.warnings.clear()
        self._error_counts.clear()

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """转换为字典列表"""
        return [e.to_dict() for e in self.errors]

    def get_statistics(self) -> Dict[str, Any]:
        """获取错误统计"""
        return {
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'error_types': len(set(e.error_type for e in self.errors)),
            'error_counts': self._error_counts.copy()
        }

    def generate_report(self) -> str:
        """生成错误报告"""
        lines = [
            "=" * 60,
            "转换错误报告",
            "=" * 60,
            ""
        ]

        # 错误统计
        if self.errors:
            lines.append(f"错误 ({len(self.errors)}):")
            lines.append("-" * 40)
            for error in self.errors:
                if error.level == ErrorLevel.ERROR:
                    lines.append(
                        f"  行{error.line_no}: [{error.error_type}] {error.message}"
                    )
            lines.append("")

        # 警告统计
        if self.warnings:
            lines.append(f"警告 ({len(self.warnings)}):")
            lines.append("-" * 40)
            for warning in self.warnings:
                lines.append(
                    f"  行{warning.line_no}: [{warning.error_type}] {warning.message}"
                )
            lines.append("")

        # 按类型统计
        if self._error_counts:
            lines.append("按类型统计:")
            lines.append("-" * 40)
            for error_type, count in sorted(self._error_counts.items()):
                lines.append(f"  {error_type}: {count}")
            lines.append("")

        if not self.errors and not self.warnings:
            lines.append("✅ 无错误和警告")

        lines.extend(["", "=" * 60])
        return "\n".join(lines)

    def __len__(self) -> int:
        """错误列表长度"""
        return len(self.errors)

    def __repr__(self) -> str:
        return f"ConversionErrorHandler(errors={len(self.errors)}, warnings={len(self.warnings)})"
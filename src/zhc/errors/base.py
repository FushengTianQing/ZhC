"""
ZHC 编译器统一异常基类

提供统一的异常处理机制，支持错误位置追踪和上下文信息。

创建日期: 2026-04-07
最后更新: 2026-04-07
维护者: ZHC开发团队
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class SourceLocation:
    """
    源码位置信息 - 增强版

    用于追踪错误发生的具体位置，便于定位和修复问题。
    支持精确到字符级别的错误定位和源码片段展示。

    Attributes:
        file_path: 源文件路径
        line: 行号（从1开始）
        column: 列号（从1开始）
        end_line: 结束行号（可选，用于多行错误）
        end_column: 结束列号（可选，用于多列错误）
        token_text: 相关 Token 文本（可选，用于高亮）
        source_line: 源码行内容（可选，用于展示）
    """

    file_path: Optional[str] = None
    line: int = 0
    column: int = 0
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    token_text: Optional[str] = None  # 新增：相关 Token 文本
    source_line: Optional[str] = None  # 新增：源码行内容

    def __str__(self) -> str:
        """格式化位置信息为可读字符串"""
        if self.file_path:
            if self.end_line and self.end_column:
                return f"{self.file_path}:{self.line}:{self.column}-{self.end_line}:{self.end_column}"
            return f"{self.file_path}:{self.line}:{self.column}"
        return f"行 {self.line}, 列 {self.column}"

    def to_visual_format(self) -> str:
        """
        生成可视化格式（类似 Rust/Clang 风格）

        Returns:
            可视化的位置信息字符串

        Example:
            >>> loc = SourceLocation("test.zhc", 10, 5, 10, 15, "计数器")
            >>> print(loc.to_visual_format())
            test.zhc:10:5
        """
        return str(self)

    def get_range(self) -> tuple[int, int, int, int]:
        """
        获取位置范围

        Returns:
            (line, column, end_line, end_column) 元组
        """
        end_line = self.end_line or self.line
        end_column = self.end_column or self.column
        return (self.line, self.column, end_line, end_column)

    def is_multiline(self) -> bool:
        """判断是否为多行位置"""
        return self.end_line is not None and self.end_line != self.line

    def get_length(self) -> int:
        """获取位置长度（单行时）"""
        if self.is_multiline():
            return -1  # 多行不支持长度计算
        end_col = self.end_column or (self.column + len(self.token_text or ""))
        return end_col - self.column

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于序列化"""
        return {
            "file_path": self.file_path,
            "line": self.line,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
            "token_text": self.token_text,
            "source_line": self.source_line,
        }


class ZHCError(Exception):
    """
    ZHC 编译器基础异常类

    所有编译器异常的统一基类，提供：
    - 错误位置追踪
    - 错误上下文信息
    - 错误级别分类
    - 修复建议

    Attributes:
        message: 错误消息
        location: 错误位置（可选）
        error_code: 错误代码（便于分类和查找）
        severity: 错误严重程度（error/warning/info）
        context: 错误上下文信息（源码片段等）
        suggestion: 修复建议（可选）

    Example:
        >>> error = ZHCError(
        ...     "未定义的变量",
        ...     location=SourceLocation("test.zhc", 10, 5),
        ...     error_code="E001",
        ...     suggestion="请检查变量是否已声明"
        ... )
        >>> print(error)
        test.zhc:10:5: 错误[E001]: 未定义的变量
        建议: 请检查变量是否已声明
    """

    # 错误严重程度常量
    SEVERITY_ERROR = "error"
    SEVERITY_WARNING = "warning"
    SEVERITY_INFO = "info"

    def __init__(
        self,
        message: str,
        location: Optional[SourceLocation] = None,
        error_code: Optional[str] = None,
        severity: str = SEVERITY_ERROR,
        context: Optional[str] = None,
        suggestion: Optional[str] = None,
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            location: 错误位置（可选）
            error_code: 错误代码（可选）
            severity: 错误严重程度（默认为error）
            context: 错误上下文信息（可选）
            suggestion: 修复建议（可选）
        """
        self.message = message
        self.location = location
        self.error_code = error_code
        self.severity = severity
        self.context = context
        self.suggestion = suggestion

        # 调用父类初始化，使用格式化的消息
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """
        格式化错误消息

        生成包含位置、错误代码、消息、建议的完整错误信息。

        Returns:
            格式化后的错误消息字符串
        """
        parts = []

        # 位置信息
        if self.location:
            parts.append(str(self.location))

        # 错误级别和代码
        severity_cn = {
            self.SEVERITY_ERROR: "错误",
            self.SEVERITY_WARNING: "警告",
            self.SEVERITY_INFO: "信息",
        }.get(self.severity, "错误")

        if self.error_code:
            parts.append(f"{severity_cn}[{self.error_code}]")
        else:
            parts.append(severity_cn)

        # 错误消息
        parts.append(self.message)

        # 组合基本信息
        base_message = ": ".join(parts)

        # 添加上下文信息
        if self.context:
            base_message += f"\n上下文: {self.context}"

        # 添加修复建议
        if self.suggestion:
            base_message += f"\n建议: {self.suggestion}"

        return base_message

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式，便于序列化和报告生成

        Returns:
            包含所有错误信息的字典
        """
        return {
            "message": self.message,
            "location": self.location.to_dict() if self.location else None,
            "error_code": self.error_code,
            "severity": self.severity,
            "context": self.context,
            "suggestion": self.suggestion,
            "formatted_message": str(self),
        }

    def is_error(self) -> bool:
        """判断是否为错误级别"""
        return self.severity == self.SEVERITY_ERROR

    def is_warning(self) -> bool:
        """判断是否为警告级别"""
        return self.severity == self.SEVERITY_WARNING

    def is_info(self) -> bool:
        """判断是否为信息级别"""
        return self.severity == self.SEVERITY_INFO

    def __repr__(self) -> str:
        """返回异常的调试表示"""
        return f"{self.__class__.__name__}(message='{self.message}', error_code='{self.error_code}')"


class ErrorCollection:
    """
    错误集合管理器

    用于收集和管理多个编译错误，支持：
    - 错误累积
    - 错误统计
    - 错误报告生成

    Example:
        >>> errors = ErrorCollection()
        >>> errors.add(ZHCError("错误1", error_code="E001"))
        >>> errors.add(ZHCError("错误2", error_code="E002"))
        >>> print(errors.summary())
        发现 2 个错误
    """

    def __init__(self):
        """初始化错误集合"""
        self._errors: list[ZHCError] = []
        self._warnings: list[ZHCError] = []
        self._infos: list[ZHCError] = []

    def add(self, error: ZHCError) -> None:
        """
        添加错误到集合

        Args:
            error: 要添加的错误对象
        """
        if error.is_error():
            self._errors.append(error)
        elif error.is_warning():
            self._warnings.append(error)
        else:
            self._infos.append(error)

    def has_errors(self) -> bool:
        """判断是否有错误"""
        return len(self._errors) > 0

    def has_warnings(self) -> bool:
        """判断是否有警告"""
        return len(self._warnings) > 0

    def error_count(self) -> int:
        """获取错误数量"""
        return len(self._errors)

    def warning_count(self) -> int:
        """获取警告数量"""
        return len(self._warnings)

    def info_count(self) -> int:
        """获取信息数量"""
        return len(self._infos)

    def total_count(self) -> int:
        """获取总数量"""
        return len(self._errors) + len(self._warnings) + len(self._infos)

    def get_errors(self) -> list[ZHCError]:
        """获取所有错误"""
        return self._errors.copy()

    def get_warnings(self) -> list[ZHCError]:
        """获取所有警告"""
        return self._warnings.copy()

    def get_all(self) -> list[ZHCError]:
        """获取所有消息（按严重程度排序）"""
        return self._errors + self._warnings + self._infos

    def summary(self) -> str:
        """
        生成错误摘要报告

        Returns:
            错误摘要字符串
        """
        parts = []

        if self.error_count() > 0:
            parts.append(f"{self.error_count()} 个错误")

        if self.warning_count() > 0:
            parts.append(f"{self.warning_count()} 个警告")

        if self.info_count() > 0:
            parts.append(f"{self.info_count()} 个信息")

        if not parts:
            return "无错误或警告"

        return "发现 " + ", ".join(parts)

    def detailed_report(self) -> str:
        """
        生成详细错误报告

        Returns:
            详细错误报告字符串
        """
        lines = ["=" * 60]
        lines.append("编译错误报告")
        lines.append("=" * 60)
        lines.append(self.summary())
        lines.append("=" * 60)

        # 错误列表
        if self._errors:
            lines.append("\n错误:")
            for i, error in enumerate(self._errors, 1):
                lines.append(f"{i}. {error}")

        # 警告列表
        if self._warnings:
            lines.append("\n警告:")
            for i, warning in enumerate(self._warnings, 1):
                lines.append(f"{i}. {warning}")

        # 信息列表
        if self._infos:
            lines.append("\n信息:")
            for i, info in enumerate(self._infos, 1):
                lines.append(f"{i}. {info}")

        lines.append("=" * 60)
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        Returns:
            包含所有错误信息的字典
        """
        return {
            "errors": [e.to_dict() for e in self._errors],
            "warnings": [w.to_dict() for w in self._warnings],
            "infos": [i.to_dict() for i in self._infos],
            "summary": self.summary(),
            "counts": {
                "errors": self.error_count(),
                "warnings": self.warning_count(),
                "infos": self.info_count(),
                "total": self.total_count(),
            },
        }

    def clear(self) -> None:
        """清空所有错误"""
        self._errors.clear()
        self._warnings.clear()
        self._infos.clear()

    def __len__(self) -> int:
        """返回总错误数量"""
        return self.total_count()

    def __iter__(self):
        """迭代所有错误"""
        return iter(self.get_all())

    def __repr__(self) -> str:
        """返回调试表示"""
        return f"ErrorCollection(errors={self.error_count()}, warnings={self.warning_count()})"


# 导出公共API
__all__ = [
    "SourceLocation",
    "ZHCError",
    "ErrorCollection",
]

"""
错误格式化器

提供多种格式的错误输出，支持现代编译器风格的错误展示。

创建日期: 2026-04-09
最后更新: 2026-04-09
"""

from typing import Optional
from .base import ZHCError, ErrorCollection
from .source_context import SourceContextExtractor, SourceContext


class ErrorFormatter:
    """
    错误格式化器

    支持多种输出风格：
    - 简洁模式：仅显示错误消息
    - 详细模式：显示完整上下文
    - JSON 模式：结构化输出

    Example:
        >>> formatter = ErrorFormatter()
        >>> error = ZHCError("未定义的变量", error_code="E001")
        >>> print(formatter.format_error(error))
        错误[E001]: 未定义的变量
    """

    # ANSI 颜色代码
    COLORS = {
        "reset": "\033[0m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "bold": "\033[1m",
        "underline": "\033[4m",
    }

    def __init__(
        self,
        color_output: bool = True,
        context_lines: int = 2,
        show_suggestions: bool = True,
    ):
        """
        初始化错误格式化器

        Args:
            color_output: 是否启用彩色输出
            context_lines: 上下文行数
            show_suggestions: 是否显示修复建议
        """
        self.color_output = color_output
        self.context_lines = context_lines
        self.show_suggestions = show_suggestions

    def format_error(
        self, error: ZHCError, context: Optional[SourceContext] = None
    ) -> str:
        """
        格式化单个错误

        Args:
            error: 错误对象
            context: 源码上下文（可选）

        Returns:
            格式化后的错误字符串
        """
        lines = []

        # 错误头部
        header = self._format_header(error)
        lines.append(header)

        # 位置信息
        if error.location:
            location_line = self._format_location(error.location)
            lines.append(f"   --> {location_line}")

        # 源码上下文
        if context:
            context_str = self._format_context(error, context)
            if context_str:
                lines.append(context_str)

        # 错误详情
        if error.context:
            lines.append(f"   = 上下文: {error.context}")

        # 修复建议
        if self.show_suggestions and error.suggestion:
            suggestion = self._colorize("建议", "cyan")
            lines.append(f"   = {suggestion}: {error.suggestion}")

        return "\n".join(lines)

    def format_error_collection(
        self,
        errors: ErrorCollection,
        extractor: Optional[SourceContextExtractor] = None,
    ) -> str:
        """
        格式化错误集合

        Args:
            errors: 错误集合
            extractor: 源码上下文提取器（可选）

        Returns:
            格式化后的错误报告
        """
        lines = []

        # 摘要
        summary = self._format_summary(errors)
        lines.append(summary)
        lines.append("")

        # 错误列表
        all_errors = errors.get_all()
        for i, error in enumerate(all_errors, 1):
            # 获取上下文
            context = None
            if extractor and error.location:
                context = extractor.get_context(
                    error.location, context_lines=self.context_lines
                )

            # 格式化错误
            error_str = self.format_error(error, context)
            lines.append(error_str)

            # 错误之间添加空行
            if i < len(all_errors):
                lines.append("")

        # 结尾
        if errors.has_errors():
            lines.append("")
            lines.append(self._colorize("编译失败。请修复上述错误后重新编译。", "red"))

        return "\n".join(lines)

    def format_as_json(self, errors: ErrorCollection) -> str:
        """
        格式化为 JSON

        Args:
            errors: 错误集合

        Returns:
            JSON 格式的错误报告
        """
        import json

        return json.dumps(errors.to_dict(), ensure_ascii=False, indent=2)

    def format_as_simple(self, errors: ErrorCollection) -> str:
        """
        简洁格式

        Args:
            errors: 错误集合

        Returns:
            简洁的错误报告
        """
        lines = []
        for error in errors.get_all():
            lines.append(str(error))
        return "\n".join(lines)

    def _format_header(self, error: ZHCError) -> str:
        """格式化错误头部"""
        severity_map = {
            ZHCError.SEVERITY_ERROR: ("错误", "red"),
            ZHCError.SEVERITY_WARNING: ("警告", "yellow"),
            ZHCError.SEVERITY_INFO: ("信息", "blue"),
        }

        severity_text, color = severity_map.get(error.severity, ("错误", "red"))

        if error.error_code:
            header = f"{severity_text}[{error.error_code}]: {error.message}"
        else:
            header = f"{severity_text}: {error.message}"

        return self._colorize(header, color)

    def _format_location(self, location) -> str:
        """格式化位置信息"""
        if location.file_path:
            return f"{location.file_path}:{location.line}:{location.column}"
        return f"行 {location.line}, 列 {location.column}"

    def _format_context(self, error: ZHCError, context: SourceContext) -> str:
        """格式化源码上下文"""
        lines = []

        # 分隔线
        lines.append("   |")

        # 上下文行（前）
        for line_info in context.context_lines:
            if line_info.line_num < context.line:
                lines.append(f"{line_info.line_num:3} | {line_info.content}")

        # 当前行（带高亮）
        current_line = context.source_line
        lines.append(f"{context.line:3} | {current_line}")

        # 高亮指示器
        if context.highlight_start and context.highlight_end:
            indent = "   | "
            spaces = " " * (context.highlight_start - 1)
            carets = "^" * max(1, context.highlight_end - context.highlight_start)
            lines.append(f"{indent}{spaces}{carets}")

        # 上下文行（后）
        for line_info in context.context_lines:
            if line_info.line_num > context.line:
                lines.append(f"{line_info.line_num:3} | {line_info.content}")

        lines.append("   |")

        return "\n".join(lines)

    def _format_summary(self, errors: ErrorCollection) -> str:
        """格式化摘要"""
        parts = []

        if errors.error_count() > 0:
            count = self._colorize(f"{errors.error_count()} 个错误", "red")
            parts.append(count)

        if errors.warning_count() > 0:
            count = self._colorize(f"{errors.warning_count()} 个警告", "yellow")
            parts.append(count)

        if errors.info_count() > 0:
            count = self._colorize(f"{errors.info_count()} 个信息", "blue")
            parts.append(count)

        if not parts:
            return self._colorize("无错误或警告", "green")

        return "编译发现 " + ", ".join(parts) + ":"

    def _colorize(self, text: str, color: str) -> str:
        """
        添加颜色

        Args:
            text: 文本
            color: 颜色名称

        Returns:
            着色后的文本
        """
        if not self.color_output:
            return text

        color_code = self.COLORS.get(color, "")
        reset = self.COLORS["reset"]

        return f"{color_code}{text}{reset}"


class ErrorPrinter:
    """
    错误打印机

    提供便捷的错误打印功能。

    Example:
        >>> printer = ErrorPrinter()
        >>> printer.print_error(error)
    """

    def __init__(
        self,
        formatter: Optional[ErrorFormatter] = None,
        extractor: Optional[SourceContextExtractor] = None,
    ):
        """
        初始化错误打印机

        Args:
            formatter: 错误格式化器
            extractor: 源码上下文提取器
        """
        self.formatter = formatter or ErrorFormatter()
        self.extractor = extractor

    def print_error(self, error: ZHCError) -> None:
        """
        打印单个错误

        Args:
            error: 错误对象
        """
        context = None
        if self.extractor and error.location:
            context = self.extractor.get_context(error.location)

        print(self.formatter.format_error(error, context))

    def print_errors(self, errors: ErrorCollection) -> None:
        """
        打印错误集合

        Args:
            errors: 错误集合
        """
        print(self.formatter.format_error_collection(errors, self.extractor))

    def print_summary(self, errors: ErrorCollection) -> None:
        """
        打印错误摘要

        Args:
            errors: 错误集合
        """
        print(errors.summary())


# 导出公共API
__all__ = [
    "ErrorFormatter",
    "ErrorPrinter",
]

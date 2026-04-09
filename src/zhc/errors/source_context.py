"""
源码上下文提取器

提供源码片段提取和高亮功能，用于生成更精确的错误信息。

创建日期: 2026-04-09
最后更新: 2026-04-09
"""

from dataclasses import dataclass
from typing import Optional, Dict
from .base import SourceLocation


@dataclass
class SourceContext:
    """
    源码上下文信息

    Attributes:
        file_path: 文件路径
        line: 起始行号
        column: 起始列号
        end_line: 结束行号
        end_column: 结束列号
        source_line: 源码行内容
        context_lines: 上下文行（前后若干行）
        highlight_start: 高亮起始列
        highlight_end: 高亮结束列
    """

    file_path: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    source_line: str = ""
    context_lines: list = None
    highlight_start: Optional[int] = None
    highlight_end: Optional[int] = None

    def __post_init__(self):
        if self.context_lines is None:
            self.context_lines = []
        if self.end_line is None:
            self.end_line = self.line
        if self.end_column is None:
            self.end_column = self.column

    def get_formatted_context(self, context_size: int = 2) -> str:
        """
        获取格式化的上下文（带行号）

        Args:
            context_size: 上下文行数

        Returns:
            格式化后的上下文字符串
        """
        lines = []
        line_num_width = len(str(self.end_line or self.line))

        # 上一行的上下文
        for ctx_line in self.context_lines:
            if ctx_line.line_num < self.line:
                lines.append(self._format_line(ctx_line, line_num_width))

        # 当前行（带高亮）
        lines.append(self._format_current_line(line_num_width))

        # 下一行的上下文
        for ctx_line in self.context_lines:
            if ctx_line.line_num > self.line:
                lines.append(self._format_line(ctx_line, line_num_width))

        return "\n".join(lines)

    def _format_line(self, line_info: "LineInfo", width: int) -> str:
        """格式化普通行"""
        return f"{line_info.line_num:>{width}} | {line_info.content}"

    def _format_current_line(self, width: int) -> str:
        """格式化当前行（带高亮）"""
        prefix = f"{self.line:>{width}} | "
        line_content = self.source_line

        if self.highlight_start is not None and self.highlight_end is not None:
            # 生成高亮指示器
            indicator = " " * len(prefix)
            indicator += " " * (self.highlight_start - 1)
            indicator += "^" * max(1, self.highlight_end - self.highlight_start)

            return f"{prefix}{line_content}\n{indicator}"

        return f"{prefix}{line_content}"


@dataclass
class LineInfo:
    """行信息"""

    line_num: int
    content: str


@dataclass
class MultilineSourceContext:
    """多行源码上下文

    用于显示跨越多行的错误范围（如未闭合的括号、多行字符串等）
    """

    file_path: str
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    lines: list = None

    def __post_init__(self):
        if self.lines is None:
            self.lines = []

    def get_formatted_context(self) -> str:
        """
        获取格式化的多行上下文

        Returns:
            格式化后的多行上下文字符串（类似 Rust/Clang 风格）

        Example:
            = help: Some help message
              |
            10 |     整数型 x = (
            11 |         1 + 2;
            12 |     )  // 错误：括号未闭合
              |     ^ 多行错误范围
        """
        if not self.lines:
            return ""

        lines = []
        line_num_width = len(str(self.end_line))

        for line_info in self.lines:
            line_num = line_info.line_num
            content = line_info.content

            # 判断是否为高亮行
            is_start = line_num == self.start_line
            is_end = line_num == self.end_line
            is_between = self.start_line < line_num < self.end_line

            # 构建行号和内容
            prefix = f"{line_num:>{line_num_width}} | "

            if is_start and is_end:
                # 单行内的范围
                indicator = " " * len(prefix)
                indicator += " " * (self.start_column - 1)
                indicator += "^" * max(1, self.end_column - self.start_column)
                lines.append(f"{prefix}{content}")
                lines.append(indicator)
            elif is_start:
                # 范围的开始行
                indicator = " " * len(prefix)
                indicator += " " * (self.start_column - 1)
                indicator += "^" * (len(content) - self.start_column + 1)
                lines.append(f"{prefix}{content}")
                lines.append(indicator)
            elif is_end:
                # 范围的结束行
                indicator = " " * len(prefix)
                indicator += "^" * self.end_column
                lines.append(f"{prefix}{content}")
                lines.append(indicator)
            elif is_between:
                # 范围中间的整行
                indicator = " " * len(prefix)
                indicator += "|" * len(content)
                lines.append(f"{prefix}{content}")
                lines.append(indicator)
            else:
                # 普通上下文行
                lines.append(f"{prefix}{content}")

        return "\n".join(lines)


class SourceContextExtractor:
    """
    源码上下文提取器

    从源文件中提取上下文信息，用于错误报告。

    Example:
        >>> extractor = SourceContextExtractor({"test.zhc": "整数型 x = 1;\\n整数型 y = x;"})
        >>> context = extractor.get_context(SourceLocation("test.zhc", 2, 5), context_lines=2)
        >>> print(context.get_formatted_context())
        1 | 整数型 x = 1;
        2 | 整数型 y = x;
            ^
    """

    def __init__(self, source_files: Optional[Dict[str, str]] = None):
        """
        初始化上下文提取器

        Args:
            source_files: 源文件字典 {文件路径: 文件内容}
        """
        self.sources: Dict[str, str] = source_files or {}
        self._line_cache: Dict[str, list[str]] = {}

    def create_location(
        self, file_path: str, line: int, column: int
    ) -> "SourceLocation":
        """
        创建源码位置对象

        Args:
            file_path: 文件路径
            line: 行号（从1开始）
            column: 列号（从1开始）

        Returns:
            SourceLocation 对象
        """
        from .base import SourceLocation

        return SourceLocation(file_path=file_path, line=line, column=column)

    def add_source(self, file_path: str, content: str) -> None:
        """
        添加源文件

        Args:
            file_path: 文件路径
            content: 文件内容
        """
        self.sources[file_path] = content
        # 清除行缓存
        if file_path in self._line_cache:
            del self._line_cache[file_path]

    def get_line(self, file_path: str, line: int) -> str:
        """
        获取指定行的源码

        Args:
            file_path: 文件路径
            line: 行号（从1开始）

        Returns:
            该行的源码内容

        Raises:
            KeyError: 如果文件不存在
            IndexError: 如果行号超出范围
        """
        lines = self._get_lines(file_path)
        if line < 1 or line > len(lines):
            return ""
        return lines[line - 1]

    def get_context(
        self, location: SourceLocation, context_lines: int = 2
    ) -> SourceContext:
        """
        获取错误上下文（前后若干行）

        Args:
            location: 错误位置
            context_lines: 上下文行数

        Returns:
            源码上下文对象
        """
        file_path = location.file_path or ""

        if file_path not in self.sources:
            return SourceContext(
                file_path=file_path,
                line=location.line,
                column=location.column,
                source_line="",
            )

        lines = self._get_lines(file_path)
        total_lines = len(lines)

        # 收集上下文行
        context_line_infos = []
        start = max(1, location.line - context_lines)
        end = min(total_lines, location.line + context_lines)

        for i in range(start, end + 1):
            if i != location.line:
                context_line_infos.append(LineInfo(i, lines[i - 1]))

        # 获取当前行
        current_line = ""
        if 1 <= location.line <= total_lines:
            current_line = lines[location.line - 1]

        # 确定高亮范围
        highlight_start = location.column
        highlight_end = location.end_column or (
            location.column + len(location.token_text or "")
        )

        return SourceContext(
            file_path=file_path,
            line=location.line,
            column=location.column,
            end_line=location.end_line,
            end_column=highlight_end,
            source_line=current_line,
            context_lines=context_line_infos,
            highlight_start=highlight_start,
            highlight_end=highlight_end,
        )

    def get_multiline_context(
        self, location: SourceLocation, context_lines: int = 2
    ) -> "MultilineSourceContext":
        """
        获取多行错误上下文

        用于显示跨越多行的错误范围（如未闭合的括号、多行字符串等）

        Args:
            location: 错误位置（包含 end_line）
            context_lines: 上下文行数

        Returns:
            多行源码上下文对象
        """
        file_path = location.file_path or ""

        if file_path not in self.sources:
            return MultilineSourceContext(
                file_path=file_path,
                start_line=location.line,
                start_column=location.column,
                end_line=location.end_line or location.line,
                end_column=location.end_column or location.column,
                lines=[],
            )

        lines = self._get_lines(file_path)
        total_lines = len(lines)

        # 确定显示范围
        start = max(1, location.line - context_lines)
        end = min(total_lines, (location.end_line or location.line) + context_lines)

        # 收集所有行
        context_lines_list = []
        for i in range(start, end + 1):
            if 1 <= i <= total_lines:
                context_lines_list.append(LineInfo(i, lines[i - 1]))

        return MultilineSourceContext(
            file_path=file_path,
            start_line=location.line,
            start_column=location.column,
            end_line=location.end_line or location.line,
            end_column=location.end_column or location.column,
            lines=context_lines_list,
        )

    def highlight_range(self, line: str, start_col: int, end_col: int) -> str:
        """
        高亮指定范围

        Args:
            line: 源码行
            start_col: 起始列（从1开始）
            end_col: 结束列（从1开始）

        Returns:
            高亮后的字符串

        Example:
            >>> extractor = SourceContextExtractor()
            >>> extractor.highlight_range("整数型 计数器 = 0;", 5, 12)
            '整数型 ^^^^^^^ = 0;'
        """
        if start_col < 1:
            start_col = 1
        if end_col > len(line) + 1:
            end_col = len(line) + 1

        result = line[: start_col - 1]
        result += "^" * (end_col - start_col)
        result += line[end_col - 1 :]

        return result

    def get_snippet(self, file_path: str, start_line: int, end_line: int) -> list[str]:
        """
        获取代码片段

        Args:
            file_path: 文件路径
            start_line: 起始行
            end_line: 结束行

        Returns:
            代码行列表
        """
        if file_path not in self.sources:
            return []

        lines = self._get_lines(file_path)
        start = max(1, start_line) - 1
        end = min(len(lines), end_line)

        return lines[start:end]

    def _get_lines(self, file_path: str) -> list[str]:
        """
        获取文件的行列表（带缓存）

        Args:
            file_path: 文件路径

        Returns:
            行列表
        """
        if file_path not in self._line_cache:
            if file_path in self.sources:
                content = self.sources[file_path]
                self._line_cache[file_path] = content.splitlines(keepends=False)
            else:
                self._line_cache[file_path] = []

        return self._line_cache[file_path]

    def clear_cache(self) -> None:
        """清除行缓存"""
        self._line_cache.clear()


# 导出公共API
__all__ = [
    "SourceContext",
    "LineInfo",
    "MultilineSourceContext",
    "SourceContextExtractor",
]

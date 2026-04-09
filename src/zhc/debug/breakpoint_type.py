"""
断点类型定义
"""

from enum import Enum


class BreakpointType(Enum):
    """断点类型"""

    SOURCE_LINE = "source_line"
    FUNCTION = "function"
    ADDRESS = "address"

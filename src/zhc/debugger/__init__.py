"""
ZhC 调试器支持模块

提供 GDB 和 LLDB 调试器的完整支持，包括：
- 变量美化打印器
- 调试器配置生成
- 断点管理
- 变量检查
- 表达式求值
"""

from .gdb_support import GDBSupport, GDBPrettyPrinterRegistry
from .lldb_support import LLDBSupport, LLDBFormatterRegistry
from .pretty_printer import (
    PrettyPrinterBase,
    StringPrinter,
    ArrayPrinter,
    MapPrinter,
    StructPrinter,
)
from .breakpoint_manager import BreakpointManager, Breakpoint, BreakpointType
from .variable_inspector import VariableInspector, VariableValue, VariableLocation
from .expression_evaluator import ExpressionEvaluator, EvaluationContext

__all__ = [
    # GDB 支持
    "GDBSupport",
    "GDBPrettyPrinterRegistry",
    # LLDB 支持
    "LLDBSupport",
    "LLDBFormatterRegistry",
    # 美化打印器
    "PrettyPrinterBase",
    "StringPrinter",
    "ArrayPrinter",
    "MapPrinter",
    "StructPrinter",
    # 断点管理
    "BreakpointManager",
    "Breakpoint",
    "BreakpointType",
    # 变量检查
    "VariableInspector",
    "VariableValue",
    "VariableLocation",
    # 表达式求值
    "ExpressionEvaluator",
    "EvaluationContext",
]

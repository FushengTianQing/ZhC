# -*- coding: utf-8 -*-
"""
ZhC 调试支持模块

提供 DWARF 调试信息生成、GDB/LLDB 美化打印器、断点管理等调试功能。

作者：远
日期：2026-04-09
"""

from .dwarf_builder import (
    DwarfBuilder,
    DwarfGenerator,
    DebugSection,
)

from .debug_info_collector import (
    DebugInfoCollector,
    CompileUnitInfo,
    FunctionDebugInfo,
    VariableDebugInfo,
)

from .line_number_generator import (
    LineNumberGenerator,
    LineTableEntry,
)

# 类型描述器
from .type_printer import (
    TypePrinter,
    TypeDebugDescriptor,
    TypeKind,
    DwarfEncoding,
    MemberInfo,
    TypeLayout,
)

# 变量位置追踪
from .variable_location import (
    VariableLocationTracker,
    VariableDebugLocation,
    VariableLocation,
    LiveRange,
    LocationKind,
)

# 作用域追踪
from .scope_tracker import (
    ScopeTracker,
    Scope,
    ScopeEntry,
    ScopeKind,
)

# DWARF 调试节
from .sections import (
    DebugInfoSection,
    CompileUnitBuilder,
    DIEBuilder,
    DebugAbbrevSection,
    AbbreviationBuilder,
    DebugLineSection,
    LineNumberProgramBuilder,
    DebugStrSection,
    StringPool,
)

# 断点引擎
from .breakpoint_engine import (
    BreakpointEngine,
    BreakpointHit,
    WatchType,
)

# 变量打印器
from .variable_printer import (
    VariablePrinter,
    VariableDisplay,
)

# 栈帧分析器
from .stack_frame_analyzer import (
    StackFrameAnalyzer,
    FrameInfo,
)

# 调试会话
from .debug_session import (
    DebugSession,
    SessionState,
    SessionConfig,
)

# 表达式求值器（从 debugger 模块导入）
from zhc.debugger.expression_evaluator import (
    ExpressionEvaluator,
    EvaluationContext,
    EvaluationResult,
)

__all__ = [
    # DWARF 构建
    "DwarfBuilder",
    "DwarfGenerator",
    "DebugSection",
    # 调试信息收集
    "DebugInfoCollector",
    "CompileUnitInfo",
    "FunctionDebugInfo",
    "VariableDebugInfo",
    # 行号生成
    "LineNumberGenerator",
    "LineTableEntry",
    # 类型描述器
    "TypePrinter",
    "TypeDebugDescriptor",
    "TypeKind",
    "DwarfEncoding",
    "MemberInfo",
    "TypeLayout",
    # 变量位置追踪
    "VariableLocationTracker",
    "VariableDebugLocation",
    "VariableLocation",
    "LiveRange",
    "LocationKind",
    # 作用域追踪
    "ScopeTracker",
    "Scope",
    "ScopeEntry",
    "ScopeKind",
    # DWARF 调试节
    "DebugInfoSection",
    "CompileUnitBuilder",
    "DIEBuilder",
    "DebugAbbrevSection",
    "AbbreviationBuilder",
    "DebugLineSection",
    "LineNumberProgramBuilder",
    "DebugStrSection",
    "StringPool",
    # 断点引擎
    "BreakpointEngine",
    "BreakpointHit",
    "WatchType",
    # 变量打印器
    "VariablePrinter",
    "VariableDisplay",
    # 栈帧分析器
    "StackFrameAnalyzer",
    "FrameInfo",
    # 调试会话
    "DebugSession",
    "SessionState",
    "SessionConfig",
    # 表达式求值器
    "ExpressionEvaluator",
    "EvaluationContext",
    "EvaluationResult",
]

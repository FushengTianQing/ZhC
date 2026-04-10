# -*- coding: utf-8 -*-
"""
函数式编程支持模块 - Functional Programming Support

提供函数式编程范式的核心支持：
1. 闭包（Closure）和 Lambda 表达式
2. Upvalue 捕获机制
3. 协程（Coroutine）支持

Phase 5 - 函数式编程

作者：ZHC 开发团队
日期：2026-04-10
"""

from .closure import (
    CaptureMode,
    Upvalue,
    ClosureType,
    ClosureEnvironment,
    ClosureContext,
)
from .analyzer import UpvalueAnalyzer

__all__ = [
    # 闭包核心类型
    "CaptureMode",
    "Upvalue",
    "ClosureType",
    "ClosureEnvironment",
    "ClosureContext",
    # 分析器
    "UpvalueAnalyzer",
]

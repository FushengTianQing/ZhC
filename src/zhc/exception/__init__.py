# -*- coding: utf-8 -*-
"""
异常处理模块

提供完整的异常处理支持，包括类型系统、传播机制、上下文管理。

主要组件：
- types: 核心数据类型（ExceptionType, ExceptionField, ExceptionObject）
- registry: 异常类型注册表
- builtins: 内置异常类型定义
- context: 异常上下文管理
- propagation: 异常传播机制

作者：远
日期：2026-04-10
"""

from .types import (
    ExceptionField,
    ExceptionType,
    ExceptionObject,
    ExceptionThrowInfo,
)

from .registry import (
    ExceptionRegistry,
    get_exception_class,
    is_exception_type,
)

from .builtins import (
    BuiltinExceptionInfo,
    BUILTIN_EXCEPTIONS,
    get_exception_info,
    get_error_code,
    get_all_exception_names,
    lookup_by_error_code,
)

from .context import (
    ExceptionState,
    StackFrameInfo,
    ExceptionHandler,
    ExceptionContext,
)

from .propagation import (
    StackUnwinder,
    ExceptionPropagator,
    throw_exception,
    rethrow_exception,
    get_current_exception,
)


# 导出所有公共符号
__all__ = [
    # 类型
    "ExceptionField",
    "ExceptionType",
    "ExceptionObject",
    "ExceptionThrowInfo",
    # 注册表
    "ExceptionRegistry",
    "get_exception_class",
    "is_exception_type",
    # 内置异常
    "BuiltinExceptionInfo",
    "BUILTIN_EXCEPTIONS",
    "get_exception_info",
    "get_error_code",
    "get_all_exception_names",
    "lookup_by_error_code",
    # 上下文
    "ExceptionState",
    "StackFrameInfo",
    "ExceptionHandler",
    "ExceptionContext",
    # 传播
    "StackUnwinder",
    "ExceptionPropagator",
    "throw_exception",
    "rethrow_exception",
    "get_current_exception",
]

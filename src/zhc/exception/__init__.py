# -*- coding: utf-8 -*-
"""
异常类型系统模块

提供完整的异常类型定义、注册表和内置异常类型支持。

主要组件：
- types: 核心数据类型（ExceptionType, ExceptionField, ExceptionObject）
- registry: 异常类型注册表
- builtins: 内置异常类型定义

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
]

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZHC 编译器公共 API

提供类型安全的编译结果和统计数据类。

Example:
    >>> from zhc.api import CompilationResult, CompilationStats
    >>> result = CompilationResult.success_result(Path("main.zhc"), [Path("main.c")])
    >>> print(result.summary())
"""

from .result import CompilationResult
from .stats import CompilationStats

__all__ = [
    "CompilationResult",
    "CompilationStats",
]

#!/usr/bin/env python3
"""
内存管理模块

提供智能指针、RAII、内存泄漏检测等功能
"""

from .smart_ptr import ControlBlock, UniquePtr, SharedPtr, WeakPtr
from .cycle_detector import CycleDetector
from .raii import (
    DestructorInfo,
    CleanupStack,
    CleanupPriority,
    ScopeGuard,
    DestructorRegistry,
    scope_guard,
    get_global_cleanup_stack,
    get_global_destructor_registry,
)

__all__ = [
    "ControlBlock",
    "UniquePtr",
    "SharedPtr",
    "WeakPtr",
    "CycleDetector",
    "DestructorInfo",
    "CleanupStack",
    "CleanupPriority",
    "ScopeGuard",
    "DestructorRegistry",
    "scope_guard",
    "get_global_cleanup_stack",
    "get_global_destructor_registry",
]

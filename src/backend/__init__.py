#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZhC 后端模块 - 统一多后端架构

提供多后端支持：
- C 后端（IR → C 代码）
- GCC 后端（GCC 工具链）
- Clang 后端（Clang/LLVM 工具链）
- LLVM 后端（llvmlite）
- WASM 后端（Emscripten）

使用方式：
    from zhc.backend import BackendManager, GCCBackend, LLVMBackend

    # 自动选择最佳后端
    backend = BackendManager.auto_select()

    # 获取指定后端
    gcc = BackendManager.get("gcc")

    # 列出可用后端
    available = BackendManager.list_available()

作者：远
日期：2026-04-08
"""

# 基类和数据结构
from .base import (
    BackendBase,
    BackendCapabilities,
    BackendError,
    CompilationError,
    LinkingError,
    ToolNotFoundError,
    UnsupportedTargetError,
    CompileOptions,
    CompileResult,
    OutputFormat,
)

# 后端管理器
from .manager import (
    BackendManager,
    get_backend,
    get_available_backends,
)

# C 后端
from .c_backend import CBackend

# GCC 后端
from .gcc_backend import GCCBackend

# Clang 后端
from .clang_backend import ClangBackend

# LLVM 后端（可选，需要 llvmlite）
try:
    from .llvm_backend import LLVMBackend, LLVMBackendError, compile_to_llvm

    LLVM_BACKEND_AVAILABLE = True
except ImportError:
    LLVMBackend = None
    LLVMBackendError = None
    compile_to_llvm = None
    LLVM_BACKEND_AVAILABLE = False

# WASM 后端（可选，需要 Emscripten）
from .wasm_backend import WebAssemblyBackend, WASMCompileResult

# 调试监听器
from .llvm_debug_listener import LLVMDebugListener
from .wasm_debug_listener import WASMDebugListener

# 寄存器分配器接口
from .allocator_interface import (
    AllocationStrategy,
    BackendCapabilities as AllocatorCapabilities,
    RegisterAllocator,
    UnifiedRegisterAllocator,
    X86_64RegisterAllocator,
    Arm64RegisterAllocator,
    WASMRegisterAllocator,
    LLVMRegisterAllocator,
    create_allocator,
    register_for_all_backends,
    Instruction,
)

__all__ = [
    # 基类
    "BackendBase",
    "BackendCapabilities",
    "BackendError",
    "CompilationError",
    "LinkingError",
    "ToolNotFoundError",
    "UnsupportedTargetError",
    "CompileOptions",
    "CompileResult",
    "OutputFormat",
    # 后端管理器
    "BackendManager",
    "get_backend",
    "get_available_backends",
    # 后端实现
    "CBackend",
    "GCCBackend",
    "ClangBackend",
    "LLVMBackend",
    "LLVMBackendError",
    "compile_to_llvm",
    "LLVM_BACKEND_AVAILABLE",
    "WebAssemblyBackend",
    "WASMCompileResult",
    # 调试监听器
    "LLVMDebugListener",
    "WASMDebugListener",
    # 寄存器分配器
    "AllocationStrategy",
    "AllocatorCapabilities",
    "RegisterAllocator",
    "UnifiedRegisterAllocator",
    "X86_64RegisterAllocator",
    "Arm64RegisterAllocator",
    "WASMRegisterAllocator",
    "LLVMRegisterAllocator",
    "create_allocator",
    "register_for_all_backends",
    "Instruction",
]

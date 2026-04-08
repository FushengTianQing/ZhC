#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZhC 后端模块

提供多后端支持：
- C 后端
- LLVM 后端
- WASM 后端
- 寄存器分配器接口

作者：阿福
日期：2026-04-08
"""

from .allocator_interface import (
    AllocationStrategy,
    BackendCapabilities,
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

# LLVM 后端（可选，需要 llvmlite）
try:
    from .llvm_backend import LLVMBackend, LLVMBackendError, compile_to_llvm
    LLVM_BACKEND_AVAILABLE = True
except ImportError:
    LLVMBackend = None
    LLVMBackendError = None
    compile_to_llvm = None
    LLVM_BACKEND_AVAILABLE = False

__all__ = [
    'AllocationStrategy',
    'BackendCapabilities',
    'RegisterAllocator',
    'UnifiedRegisterAllocator',
    'X86_64RegisterAllocator',
    'Arm64RegisterAllocator',
    'WASMRegisterAllocator',
    'LLVMRegisterAllocator',
    'create_allocator',
    'register_for_all_backends',
    'Instruction',
    'LLVMBackend',
    'LLVMBackendError',
    'compile_to_llvm',
    'LLVM_BACKEND_AVAILABLE',
]
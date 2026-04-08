#!/usr/bin/env python3
"""
代码生成包 - 已废弃

⚠️  此模块已废弃，请使用：
- zhc.ir.register_allocator - 寄存器分配器
- zhc.backend.allocator_interface - 后端分配接口

作者: 阿福
日期: 2026-04-03
"""

import warnings

warnings.warn(
    "zhc.codegen 模块已废弃，"
    "请使用 zhc.ir.register_allocator 或 zhc.backend.*",
    DeprecationWarning,
    stacklevel=2
)

# 重新导出（向后兼容）
from zhc.ir.register_allocator import (
    RegisterKind,
    Register,
    VirtualRegister,
    LiveInterval,
    AllocationResult,
    TargetArchitecture,
    LinearScanRegisterAllocator,
    GraphColorRegisterAllocator,
    simple_allocate,
)

from zhc.backend.allocator_interface import (
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

# 重新导出 C 代码生成器
from .c_codegen import CCodeGenerator

__all__ = [
    # 寄存器分配（从 zhc.ir 导出）
    'RegisterKind',
    'Register',
    'VirtualRegister',
    'LiveInterval',
    'AllocationResult',
    'TargetArchitecture',
    'LinearScanRegisterAllocator',
    'GraphColorRegisterAllocator',
    'simple_allocate',
    # 后端接口（从 zhc.backend 导出）
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
    # C 代码生成器
    'CCodeGenerator',
]

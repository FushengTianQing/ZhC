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
# 注意：LLVMBackend 类定义在 try/except 外面，所以 import 永远成功
# 需要检查 llvm_backend.LLVM_AVAILABLE 来判断 llvmlite 是否真正可用
from .llvm_backend import LLVMBackend, LLVMBackendError, compile_to_llvm, LLVM_AVAILABLE

LLVM_BACKEND_AVAILABLE = LLVM_AVAILABLE

# WASM 后端（可选，需要 Emscripten）
from .wasm_backend import WebAssemblyBackend, WASMCompileResult

# 调试监听器
from .llvm_debug_listener import LLVMDebugListener
from .wasm_debug_listener import WASMDebugListener

# === 重构新增模块 ===
# 类型系统
from .type_system import (
    TypeMapper,
    TypeInfo,
    TargetBackend,
    get_type_mapper,
)

# 编译器运行器
from .compiler_runner import (
    CompilerRunner,
    CompilerConfig,
    CompilerOutput,
    TemporaryFileManager,
    create_c_compiler_runner,
    create_wasm_compiler_runner,
)

# 编译缓存
from .compile_cache import (
    CompileCache,
    CacheEntry,
    CachedBackend,
)

# 指令策略（用于 LLVM 后端）
from .llvm_instruction_strategy import (
    InstructionStrategy,
    InstructionStrategyFactory,
)

# 编译上下文
from .compilation_context import CompilationContext

# === 重构版本后端（已启用）===
# 2026-04-09: c_backend.py 和 llvm_backend.py 已重构，使用统一架构

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

# 反射策略
from .reflection_strategies import (
    TypeInfoGetStrategy,
    TypeInfoNameStrategy,
    TypeInfoSizeStrategy,
    FieldGetValueStrategy,
    FieldSetValueStrategy,
    register_reflection_strategies,
)

# 类型检查策略
from .type_check_strategies import (
    IsTypeStrategy,
    IsSubtypeStrategy,
    ImplementsInterfaceStrategy,
    TypeEqualsStrategy,
    SafeCastStrategy,
    DynamicCastStrategy,
    CheckAssignableStrategy,
    IsPrimitiveStrategy,
    register_type_check_strategies,
)

# 泛型策略
from .generic_strategies import (
    GenericInstantiateStrategy,
    GenericCallStrategy,
    TypeParamBindStrategy,
    SpecializeStrategy,
    register_generic_strategies,
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
    # === 重构新增 ===
    # 类型系统
    "TypeMapper",
    "TypeInfo",
    "TargetBackend",
    "get_type_mapper",
    # 编译器运行器
    "CompilerRunner",
    "CompilerConfig",
    "CompilerOutput",
    "TemporaryFileManager",
    "create_c_compiler_runner",
    "create_wasm_compiler_runner",
    # 编译缓存
    "CompileCache",
    "CacheEntry",
    "CachedBackend",
    # 指令策略
    "InstructionStrategy",
    "InstructionStrategyFactory",
    "CompilationContext",
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
    # 反射策略
    "TypeInfoGetStrategy",
    "TypeInfoNameStrategy",
    "TypeInfoSizeStrategy",
    "FieldGetValueStrategy",
    "FieldSetValueStrategy",
    "register_reflection_strategies",
    # 类型检查策略
    "IsTypeStrategy",
    "IsSubtypeStrategy",
    "ImplementsInterfaceStrategy",
    "TypeEqualsStrategy",
    "SafeCastStrategy",
    "DynamicCastStrategy",
    "CheckAssignableStrategy",
    "IsPrimitiveStrategy",
    "register_type_check_strategies",
    # 泛型策略
    "GenericInstantiateStrategy",
    "GenericCallStrategy",
    "TypeParamBindStrategy",
    "SpecializeStrategy",
    "register_generic_strategies",
]

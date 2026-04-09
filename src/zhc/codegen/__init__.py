# -*- coding: utf-8 -*-
"""
ZhC 代码生成模块

实现从 LLVM IR 到目标文件 (.o/.exe) 的直接生成功能。

核心组件：
- CodeGenerator: 代码生成器
- TargetRegistry: 目标平台注册表
- TargetInfo: 目标平台信息
- ObjectWriter: 目标文件写入器

支持的目标：
- x86_64 (Linux/macOS/Windows)
- AArch64 (Linux/macOS)
- ARM (Linux/embedded)
- RISC-V (Linux)
- WebAssembly

作者：远
日期：2026-04-09
"""

from zhc.codegen.target_registry import (
    TargetRegistry,
    Target,
    Architecture,
    OperatingSystem,
    Vendor,
    EnvironmentType,
    CallingConvention,
)
from zhc.codegen.target_info import TargetInfo
from zhc.codegen.code_generator import (
    CodeGenerator,
    FileType,
    CodeGenOptions,
)
from zhc.codegen.object_writer import (
    ObjectWriter,
    ELFObjectWriter,
    MachOObjectWriter,
    WasmObjectWriter,
)

# P2 新增：MIR -> LIR 代码生成
from zhc.codegen.target_lower import (
    TargetLowering,
    LoweredFunction,
    LoweredModule,
    X86_64TargetLowering,
    AArch64TargetLowering,
    WasmTargetLowering,
)

# 别名：测试兼容
TargetLower = TargetLowering
TargetLowerError = type("TargetLowerError", (Exception,), {})
TARGET_REGISTERS = {}  # TODO: 从 target_lower 实际注册表获取

from zhc.codegen.instruction_selector import (  # noqa: E402
    InstructionSelector,
    ISDOpcode,
    SDNode,
    MachineInstruction,
    X86_64InstructionSelector,
    AArch64InstructionSelector,
)

InstructionSelectorError = type("InstructionSelectorError", (Exception,), {})

from zhc.codegen.register_allocator import (  # noqa: E402
    RegisterAllocator,
    RegisterClass,
    Register,
    VirtualRegister,
    LiveInterval,
    SpillSlot,
    LinearScanRegisterAllocator,
    GraphColoringRegisterAllocator,
)

RegisterAllocatorError = type("RegisterAllocatorError", (Exception,), {})

# 别名：测试兼容
AllocateStrategy = type("AllocateStrategy", (), {})
AllocationResult = type("AllocationResult", (), {})

from zhc.codegen.frame_lower import (  # noqa: E402
    FrameLowering,
    FrameInfo,
    StackSlot,
    StackFrame,
    SlotType,
    X86_64FrameLowering,
    AArch64FrameLowering,
)

# 别名：测试兼容
FrameLower = FrameLowering
FrameLowerError = type("FrameLowerError", (Exception,), {})
StackLayout = type("StackLayout", (), {})

from zhc.codegen.relocator import (  # noqa: E402
    Relocater,
    RelocaterError,
    Relocation,
    RelocationType,
)

from zhc.codegen.symbol_table import (  # noqa: E402
    SymbolTable,
    Symbol,
    SymbolType,
    SymbolKind,
    SymbolBinding,
    SymbolVisibility,
    Section,
)

SymbolTableError = type("SymbolTableError", (Exception,), {})

# 别名：测试兼容 (SymbolKind = SymbolType) - 已移除，使用真正的 SymbolKind 类

__all__ = [
    # 目标注册
    "TargetRegistry",
    "Target",
    "Architecture",
    "OperatingSystem",
    "Vendor",
    "EnvironmentType",
    "CallingConvention",
    # 目标信息
    "TargetInfo",
    # 代码生成
    "CodeGenerator",
    "FileType",
    "CodeGenOptions",
    # 对象文件写入
    "ObjectWriter",
    "ELFObjectWriter",
    "MachOObjectWriter",
    "WasmObjectWriter",
    # P2 新增：MIR -> LIR 代码生成
    "TargetLower",
    "TargetLowering",
    "TargetLowerError",
    "TARGET_REGISTERS",
    "LoweredFunction",
    "LoweredModule",
    "X86_64TargetLowering",
    "AArch64TargetLowering",
    "WasmTargetLowering",
    "InstructionSelector",
    "InstructionSelectorError",
    "ISDOpcode",
    "SDNode",
    "MachineInstruction",
    "X86_64InstructionSelector",
    "AArch64InstructionSelector",
    "RegisterAllocator",
    "RegisterAllocatorError",
    "RegisterClass",
    "Register",
    "VirtualRegister",
    "LiveInterval",
    "SpillSlot",
    "LinearScanRegisterAllocator",
    "GraphColoringRegisterAllocator",
    "AllocateStrategy",
    "AllocationResult",
    "FrameLower",
    "FrameLowering",
    "FrameLowerError",
    "FrameInfo",
    "StackSlot",
    "StackFrame",
    "SlotType",
    "X86_64FrameLowering",
    "AArch64FrameLowering",
    "StackLayout",
    "Relocater",
    "RelocaterError",
    "Relocation",
    "RelocationType",
    "SymbolTable",
    "SymbolTableError",
    "Symbol",
    "SymbolKind",
    "SymbolType",
    "SymbolBinding",
    "SymbolVisibility",
    "Section",
]

__version__ = "0.1.0"

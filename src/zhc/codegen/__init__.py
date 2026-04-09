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
]

__version__ = "0.1.0"

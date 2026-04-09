# -*- coding: utf-8 -*-
"""
ZhC 跨平台编译支持模块

提供交叉编译功能，包括目标平台检测、工具链管理、Sysroot 管理、
链接器管理、运行时管理、平台注册表等。

作者：远
日期：2026-04-09
"""

from .triple_parser import (
    TargetTriple,
    TripleParser,
    TripleParseError,
)

from .host_detector import (
    HostInfo,
    HostDetector,
)

from .cross_compile_manager import (
    CrossCompileManager,
    TargetConfig,
)

from .toolchain_manager import (
    Toolchain,
    ToolchainManager,
    ToolchainError,
)

from .sysroot_manager import (
    SysrootManager,
    SysrootError,
)

from .linker_manager import (
    LinkerInfo,
    LinkerManager,
    LinkerError,
    LinkerType,
)

from .runtime_manager import (
    CRTRuntime,
    RuntimeLibrary,
    RuntimeType,
    RuntimeManager,
    RuntimeError,
)

from .platform_registry import (
    PlatformABI,
    PlatformFeatures,
    PlatformConfig,
    PlatformRegistry,
    DataModel,
    ABIType,
)

__all__ = [
    # Triple 解析
    "TargetTriple",
    "TripleParser",
    "TripleParseError",
    # 主机检测
    "HostInfo",
    "HostDetector",
    # 交叉编译管理
    "CrossCompileManager",
    "TargetConfig",
    # 工具链管理
    "Toolchain",
    "ToolchainManager",
    "ToolchainError",
    # Sysroot 管理
    "SysrootManager",
    "SysrootError",
    # 链接器管理
    "LinkerInfo",
    "LinkerManager",
    "LinkerError",
    "LinkerType",
    # 运行时管理
    "CRTRuntime",
    "RuntimeLibrary",
    "RuntimeType",
    "RuntimeManager",
    "RuntimeError",
    # 平台注册表
    "PlatformABI",
    "PlatformFeatures",
    "PlatformConfig",
    "PlatformRegistry",
    "DataModel",
    "ABIType",
]

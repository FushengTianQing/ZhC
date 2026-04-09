# -*- coding: utf-8 -*-
"""
ZhC 跨平台编译支持模块

提供交叉编译功能，包括目标平台检测、工具链管理、Sysroot 管理等。

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
]

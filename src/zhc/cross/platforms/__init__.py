# -*- coding: utf-8 -*-
"""
ZhC 平台配置模块

提供各平台的特定配置实现。
"""

from .linux import LinuxPlatform
from .macos import MacOSPlatform
from .windows import WindowsPlatform
from .wasm import WASMPlatform
from .embedded import EmbeddedPlatform

__all__ = [
    "LinuxPlatform",
    "MacOSPlatform",
    "WindowsPlatform",
    "WASMPlatform",
    "EmbeddedPlatform",
]

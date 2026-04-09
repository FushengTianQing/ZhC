# -*- coding: utf-8 -*-
"""
ZhC WebAssembly 平台配置

提供 WebAssembly 平台的特定配置，包括 WASI、Emscripten 等。

作者：远
日期：2026-04-09
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from zhc.codegen.target_registry import (
    Architecture,
    OperatingSystem,
)


@dataclass
class WASMABI:
    """WebAssembly ABI 配置"""

    # ILP32 数据模型
    pointer_size: int = 4
    long_size: int = 4
    int_size: int = 4
    float_size: int = 4
    double_size: int = 8

    # 内存对齐
    alignment: int = 8
    stack_alignment: int = 16

    # 特性
    memory64: bool = False
    bulk_memory: bool = True
    simd: bool = True
    atomics: bool = False
    mutable_globals: bool = True
    nontrapping_fptoint: bool = True
    sign_ext: bool = True


@dataclass
class WASMPlatform:
    """
    WebAssembly 平台配置

    提供 WebAssembly 平台的完整配置。
    """

    name = "wasm"
    os_type = OperatingSystem.UNKNOWN

    # 支持的架构
    supported_archs = [
        Architecture.WASM32,
        Architecture.WASM64,
    ]

    # ABI 配置
    abi = WASMABI()

    # WASI 配置
    wasi_enabled: bool = True
    wasi_sdk_path: Optional[str] = None

    # Emscripten 配置
    emsdk_path: Optional[str] = None

    # 运行时
    runtime_libs: List[str] = field(default_factory=lambda: ["c", "m"])

    @classmethod
    def is_supported(cls, arch: Architecture) -> bool:
        """检查架构是否支持"""
        return arch in cls.supported_archs

    @classmethod
    def get_target_triple(cls, arch: Architecture = Architecture.WASM32) -> str:
        """获取目标三元组"""
        if arch == Architecture.WASM64:
            return "wasm64-unknown-unknown"
        return "wasm32-unknown-unknown"

    @classmethod
    def detect_wasi_sdk(cls) -> Optional[str]:
        """检测 WASI SDK 安装"""
        # 环境变量
        wasi_sdk = os.environ.get("WASI_SDK_PATH")
        if wasi_sdk and os.path.isdir(wasi_sdk):
            return wasi_sdk

        # 常见路径
        common_paths = [
            "/opt/wasi-sdk",
            "/usr/local/wasi-sdk",
            os.path.expanduser("~/wasi-sdk"),
        ]

        for path in common_paths:
            if os.path.isdir(path):
                return path

        return None

    @classmethod
    def detect_emsdk(cls) -> Optional[str]:
        """检测 Emscripten SDK 安装"""
        # 环境变量
        emsdk = os.environ.get("EMSDK")
        if emsdk and os.path.isdir(emsdk):
            return emsdk

        # 常见路径
        common_paths = [
            "/opt/emsdk",
            "/usr/local/emsdk",
            os.path.expanduser("~/emsdk"),
        ]

        for path in common_paths:
            if os.path.isdir(path):
                return path

        return None

    @classmethod
    def get_wasi_sdk_path(cls) -> Optional[str]:
        """获取 WASI SDK 路径"""
        if cls.wasi_sdk_path:
            return cls.wasi_sdk_path
        return cls.detect_wasi_sdk()

    @classmethod
    def get_emsdk_path(cls) -> Optional[str]:
        """获取 Emscripten SDK 路径"""
        if cls.emsdk_path:
            return cls.emsdk_path
        return cls.detect_emsdk()

    @classmethod
    def get_wasi_compiler(cls) -> Optional[str]:
        """获取 WASI 编译器路径"""
        wasi_sdk = cls.get_wasi_sdk_path()
        if wasi_sdk:
            clang = os.path.join(wasi_sdk, "bin", "clang")
            if os.path.isfile(clang):
                return clang
        return None

    @classmethod
    def get_emcc(cls) -> Optional[str]:
        """获取 emcc 路径"""
        emsdk = cls.get_emsdk_path()
        if emsdk:
            emcc = os.path.join(emsdk, "upstream", "emscripten", "emcc")
            if os.path.isfile(emcc):
                return emcc
        return None

    @classmethod
    def get_compiler_flags(cls, arch: Architecture = Architecture.WASM32) -> List[str]:
        """获取编译器标志"""
        flags = [
            "--target=wasm32-unknown-unknown",
            "-nostdlib",
            "-fno-threadsafe-statics",
            "-fno-exceptions",
            "-fno-rtti",
        ]

        if arch == Architecture.WASM64:
            flags[0] = "--target=wasm64-unknown-unknown"

        # WASI 特性
        if cls.get_wasi_sdk_path():
            flags.extend(
                [
                    "--sysroot",
                    os.path.join(cls.get_wasi_sdk_path(), "share", "wasi-sysroot"),
                ]
            )

        return flags

    @classmethod
    def get_linker_flags(cls, arch: Architecture = Architecture.WASM32) -> List[str]:
        """获取链接器标志"""
        flags = [
            "--no-entry",
            "--export-all",
            "--allow-undefined",
        ]

        if arch == Architecture.WASM64:
            flags.append("--memory64")

        return flags

    @classmethod
    def get_supported_features(cls) -> Dict[str, bool]:
        """获取支持的特性"""
        return {
            "simd": True,
            "bulk_memory": True,
            "mutable_globals": True,
            "nontrapping_fptoint": True,
            "sign_ext": True,
            "atomics": False,  # 默认不支持
            "memory64": False,  # 默认不支持
            "multivalue": False,
            "exception_handling": False,
            "tail_calls": False,
        }

    @classmethod
    def get_wasi_sysroot(cls) -> Optional[str]:
        """获取 WASI sysroot"""
        wasi_sdk = cls.get_wasi_sdk_path()
        if wasi_sdk:
            sysroot = os.path.join(wasi_sdk, "share", "wasi-sysroot")
            if os.path.isdir(sysroot):
                return sysroot
        return None

    @classmethod
    def get_wasi_include_paths(cls) -> List[str]:
        """获取 WASI 头文件路径"""
        sysroot = cls.get_wasi_sysroot()
        if sysroot:
            return [os.path.join(sysroot, "include")]
        return []

    @classmethod
    def get_wasi_library_paths(cls) -> List[str]:
        """获取 WASI 库路径"""
        sysroot = cls.get_wasi_sysroot()
        if sysroot:
            return [os.path.join(sysroot, "lib", "wasm32-wasi")]
        return []

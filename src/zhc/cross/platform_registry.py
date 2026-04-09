# -*- coding: utf-8 -*-
"""
ZhC 平台注册表

管理平台特定的配置和特性，包括架构、操作系统、ABI、数据模型等。
提供平台信息查询和配置管理功能。

作者：远
日期：2026-04-09
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum, auto

from .triple_parser import TargetTriple, TripleParser
from zhc.codegen.target_registry import (
    Architecture,
    OperatingSystem,
)

logger = logging.getLogger(__name__)


class DataModel(Enum):
    """数据模型"""

    LP64 = auto()  # 64位指针，64位long (Linux, macOS)
    LLP64 = auto()  # 64位指针，32位long (Windows)
    ILP32 = auto()  # 32位指针，32位long
    ILP32_LEGACY = auto()  # 32位指针，32位long (传统)
    LP32 = auto()  # 16位指针，16位long


class ABIType(Enum):
    """ABI 类型"""

    SYSTEM_V = auto()  # System V ABI
    MS_ABI = auto()  # Microsoft ABI
    AAPCS = auto()  # ARM AAPCS
    AAPCS_VFP = auto()  # ARM AAPCS with VFP
    EABI = auto()  # Embedded ABI
    WASM = auto()  # WebAssembly ABI


@dataclass
class PlatformABI:
    """平台 ABI 配置"""

    type: ABIType  # ABI 类型
    data_model: DataModel  # 数据模型
    pointer_size: int = 8  # 指针大小（字节）
    long_size: int = 8  # long 大小
    int_size: int = 4  # int 大小
    float_size: int = 4  # float 大小
    double_size: int = 8  # double 大小
    alignment: int = 8  # 默认对齐
    stack_alignment: int = 16  # 栈对齐
    calling_convention: str = "default"  # 调用约定
    endianness: str = "little"  # 字节序

    # 寄存器信息
    general_regs: int = 16  # 通用寄存器数量
    float_regs: int = 8  # 浮点寄存器数量
    vector_regs: int = 0  # 向量寄存器数量

    # 返回值传递
    return_in_regs: bool = True  # 返回值通过寄存器
    return_reg: str = "rax"  # 返回值寄存器

    # 参数传递
    first_param_reg: str = "rdi"  # 第一个参数寄存器
    stack_param_offset: int = 16  # 栈参数偏移


@dataclass
class PlatformFeatures:
    """平台特性"""

    threading: bool = True  # 支持线程
    dynamic_linking: bool = True  # 支持动态链接
    position_independent: bool = True  # 支持 PIE
    aslr: bool = True  # 支持 ASLR
    stack_protector: bool = True  # 支持栈保护
    control_flow_guard: bool = False  # 控制流保护
    shadow_stack: bool = False  # 影子栈
    memory_tagging: bool = False  # 内存标记
    pointer_authentication: bool = False  # 指针认证

    # SIMD 特性
    simd: bool = False  # SIMD 支持
    neon: bool = False  # ARM NEON
    sse: bool = False  # x86 SSE
    avx: bool = False  # x86 AVX
    avx512: bool = False  # x86 AVX-512

    # 特殊特性
    wasm_simd: bool = False  # WASM SIMD
    wasm_threads: bool = False  # WASM 线程
    wasm_bulk_memory: bool = False  # WASM 批量内存


@dataclass
class PlatformConfig:
    """平台配置"""

    name: str  # 平台名称
    triple: TargetTriple  # 目标三元组
    abi: PlatformABI  # ABI 配置
    features: PlatformFeatures  # 平台特性

    # 路径配置
    sysroot: Optional[str] = None
    include_paths: List[str] = field(default_factory=list)
    library_paths: List[str] = field(default_factory=list)

    # 链接器配置
    default_linker: str = "ld"
    dynamic_linker: str = ""

    # 运行时配置
    runtime: str = "libc"
    crt_prefix: str = "crt"

    # 框架（macOS）
    framework_paths: List[str] = field(default_factory=list)

    # 库配置
    system_libs: List[str] = field(default_factory=list)

    # 特殊配置
    extra_config: Dict[str, Any] = field(default_factory=dict)

    def get_compiler_flags(self) -> List[str]:
        """获取编译器标志"""
        flags = []

        # 目标
        flags.append(f"--target={self.triple.original}")

        # ABI 相关
        if self.abi.calling_convention != "default":
            flags.append(f"-mabi={self.abi.calling_convention}")

        return flags

    def get_linker_flags(self) -> List[str]:
        """获取链接器标志"""
        flags = []

        # 动态链接器
        if self.dynamic_linker:
            flags.extend(["-dynamic-linker", self.dynamic_linker])

        # Sysroot
        if self.sysroot:
            flags.extend(["--sysroot", self.sysroot])

        return flags


class PlatformRegistry:
    """
    平台注册表

    管理和查询平台配置信息。
    """

    def __init__(self):
        self._platforms: Dict[str, PlatformConfig] = {}
        self._register_default_platforms()

    def _register_default_platforms(self) -> None:
        """注册默认平台配置"""
        # Linux x86_64
        self.register_platform(self._create_linux_x86_64())

        # Linux aarch64
        self.register_platform(self._create_linux_aarch64())

        # macOS x86_64
        self.register_platform(self._create_macos_x86_64())

        # macOS aarch64 (Apple Silicon)
        self.register_platform(self._create_macos_aarch64())

        # Windows x86_64
        self.register_platform(self._create_windows_x86_64())

        # WebAssembly
        self.register_platform(self._create_wasm())

    def register_platform(self, config: PlatformConfig) -> None:
        """注册平台配置"""
        self._platforms[config.name] = config
        logger.debug(f"Registered platform: {config.name}")

    def get_platform(self, name: str) -> Optional[PlatformConfig]:
        """获取平台配置"""
        return self._platforms.get(name)

    def get_platform_by_triple(self, triple: str) -> Optional[PlatformConfig]:
        """根据三元组获取平台配置"""
        for config in self._platforms.values():
            if str(config.triple) == triple or config.triple.original == triple:
                return config
        return None

    def list_platforms(self) -> List[str]:
        """列出所有平台"""
        return list(self._platforms.keys())

    def get_supported_architectures(self, os_name: str) -> List[Architecture]:
        """获取支持的架构"""
        archs = set()
        for config in self._platforms.values():
            if config.triple.os.name.lower() == os_name.lower():
                archs.add(config.triple.arch)
        return list(archs)

    def get_supported_os(self, arch: Architecture) -> List[OperatingSystem]:
        """获取支持的操作系统"""
        os_list = set()
        for config in self._platforms.values():
            if config.triple.arch == arch:
                os_list.add(config.triple.os)
        return list(os_list)

    # 平台创建方法
    def _create_linux_x86_64(self) -> PlatformConfig:
        """创建 Linux x86_64 配置"""
        abi = PlatformABI(
            type=ABIType.SYSTEM_V,
            data_model=DataModel.LP64,
            pointer_size=8,
            long_size=8,
            int_size=4,
            alignment=8,
            stack_alignment=16,
            calling_convention="sysv64",
            endianness="little",
            general_regs=16,
            float_regs=16,
            vector_regs=16,
            return_reg="rax",
            first_param_reg="rdi",
        )

        features = PlatformFeatures(
            threading=True,
            dynamic_linking=True,
            position_independent=True,
            aslr=True,
            stack_protector=True,
            simd=True,
            sse=True,
            avx=True,
            avx512=True,
        )

        try:
            triple = TripleParser.parse("x86_64-unknown-linux-gnu")
        except Exception:
            triple = TripleParser.parse("x86_64-unknown-linux")

        return PlatformConfig(
            name="linux-x86_64",
            triple=triple,
            abi=abi,
            features=features,
            default_linker="ld.lld",
            dynamic_linker="/lib64/ld-linux-x86-64.so.2",
            runtime="glibc",
            system_libs=["c", "m", "pthread", "dl", "rt"],
        )

    def _create_linux_aarch64(self) -> PlatformConfig:
        """创建 Linux aarch64 配置"""
        abi = PlatformABI(
            type=ABIType.AAPCS,
            data_model=DataModel.LP64,
            pointer_size=8,
            long_size=8,
            int_size=4,
            alignment=8,
            stack_alignment=16,
            calling_convention="aapcs64",
            endianness="little",
            general_regs=31,
            float_regs=32,
            vector_regs=32,
            return_reg="x0",
            first_param_reg="x0",
        )

        features = PlatformFeatures(
            threading=True,
            dynamic_linking=True,
            position_independent=True,
            aslr=True,
            stack_protector=True,
            simd=True,
            neon=True,
        )

        try:
            triple = TripleParser.parse("aarch64-unknown-linux-gnu")
        except Exception:
            triple = TripleParser.parse("aarch64-unknown-linux")

        return PlatformConfig(
            name="linux-aarch64",
            triple=triple,
            abi=abi,
            features=features,
            default_linker="ld.lld",
            dynamic_linker="/lib/ld-linux-aarch64.so.1",
            runtime="glibc",
            system_libs=["c", "m", "pthread", "dl", "rt"],
        )

    def _create_macos_x86_64(self) -> PlatformConfig:
        """创建 macOS x86_64 配置"""
        abi = PlatformABI(
            type=ABIType.SYSTEM_V,
            data_model=DataModel.LP64,
            pointer_size=8,
            long_size=8,
            int_size=4,
            alignment=8,
            stack_alignment=16,
            calling_convention="sysv64",
            endianness="little",
            general_regs=16,
            float_regs=16,
            return_reg="rax",
            first_param_reg="rdi",
        )

        features = PlatformFeatures(
            threading=True,
            dynamic_linking=True,
            position_independent=True,
            aslr=True,
            stack_protector=True,
            simd=True,
            sse=True,
            avx=True,
        )

        try:
            triple = TripleParser.parse("x86_64-apple-darwin")
        except Exception:
            triple = TripleParser.parse("x86_64-unknown-darwin")

        return PlatformConfig(
            name="macos-x86_64",
            triple=triple,
            abi=abi,
            features=features,
            default_linker="ld64",
            runtime="system",
            system_libs=["System", "m"],
            framework_paths=[
                "/System/Library/Frameworks",
                "/Library/Frameworks",
            ],
        )

    def _create_macos_aarch64(self) -> PlatformConfig:
        """创建 macOS aarch64 (Apple Silicon) 配置"""
        abi = PlatformABI(
            type=ABIType.AAPCS,
            data_model=DataModel.LP64,
            pointer_size=8,
            long_size=8,
            int_size=4,
            alignment=8,
            stack_alignment=16,
            calling_convention="aapcs64",
            endianness="little",
            general_regs=31,
            float_regs=32,
            return_reg="x0",
            first_param_reg="x0",
        )

        features = PlatformFeatures(
            threading=True,
            dynamic_linking=True,
            position_independent=True,
            aslr=True,
            stack_protector=True,
            simd=True,
            neon=True,
            pointer_authentication=True,
        )

        try:
            triple = TripleParser.parse("aarch64-apple-darwin")
        except Exception:
            triple = TripleParser.parse("aarch64-unknown-darwin")

        return PlatformConfig(
            name="macos-aarch64",
            triple=triple,
            abi=abi,
            features=features,
            default_linker="ld64",
            runtime="system",
            system_libs=["System", "m"],
            framework_paths=[
                "/System/Library/Frameworks",
                "/Library/Frameworks",
            ],
        )

    def _create_windows_x86_64(self) -> PlatformConfig:
        """创建 Windows x86_64 配置"""
        abi = PlatformABI(
            type=ABIType.MS_ABI,
            data_model=DataModel.LLP64,
            pointer_size=8,
            long_size=4,  # Windows LLP64: long 是 32 位
            int_size=4,
            alignment=8,
            stack_alignment=16,
            calling_convention="ms_abi",
            endianness="little",
            general_regs=16,
            float_regs=16,
            return_reg="rax",
            first_param_reg="rcx",
        )

        features = PlatformFeatures(
            threading=True,
            dynamic_linking=True,
            position_independent=False,
            aslr=True,
            stack_protector=True,
            control_flow_guard=True,
            simd=True,
            sse=True,
            avx=True,
        )

        try:
            triple = TripleParser.parse("x86_64-pc-windows-msvc")
        except Exception:
            triple = TripleParser.parse("x86_64-unknown-windows")

        return PlatformConfig(
            name="windows-x86_64",
            triple=triple,
            abi=abi,
            features=features,
            default_linker="lld-link",
            runtime="msvc",
            system_libs=["kernel32", "user32", "gdi32", "msvcrt"],
        )

    def _create_wasm(self) -> PlatformConfig:
        """创建 WebAssembly 配置"""
        abi = PlatformABI(
            type=ABIType.WASM,
            data_model=DataModel.ILP32,
            pointer_size=4,
            long_size=4,
            int_size=4,
            alignment=8,
            stack_alignment=16,
            calling_convention="wasm",
            endianness="little",
            general_regs=0,
            float_regs=0,
            return_reg="",
            first_param_reg="",
        )

        features = PlatformFeatures(
            threading=False,
            dynamic_linking=False,
            position_independent=True,
            aslr=False,
            stack_protector=False,
            simd=True,
            wasm_simd=True,
            wasm_bulk_memory=True,
        )

        try:
            triple = TripleParser.parse("wasm32-unknown-unknown")
        except Exception:
            triple = TripleParser.parse("wasm32-unknown")

        return PlatformConfig(
            name="wasm",
            triple=triple,
            abi=abi,
            features=features,
            default_linker="wasm-ld",
            runtime="wasm-sdk",
            system_libs=["c", "m"],
        )


# 便捷函数
def get_platform(name: str) -> Optional[PlatformConfig]:
    """获取平台配置"""
    registry = PlatformRegistry()
    return registry.get_platform(name)


def get_platform_by_triple(triple: str) -> Optional[PlatformConfig]:
    """根据三元组获取平台配置"""
    registry = PlatformRegistry()
    return registry.get_platform_by_triple(triple)


def list_platforms() -> List[str]:
    """列出所有平台"""
    registry = PlatformRegistry()
    return registry.list_platforms()

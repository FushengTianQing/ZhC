# -*- coding: utf-8 -*-
"""
ZhC 目标三元组解析器

解析 LLVM 风格的目标三元组（Target Triple），用于交叉编译目标识别。

格式: <arch>-<vendor>-<os>[-<environment>]

示例:
    x86_64-unknown-linux-gnu      # Linux x86_64
    aarch64-apple-darwin          # macOS Apple Silicon
    arm-none-eabi                 # 嵌入式 ARM
    riscv64-unknown-linux-gnu     # Linux RISC-V
    wasm32-unknown-unknown        # WebAssembly

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass
from typing import Optional
import re

from zhc.codegen.target_registry import (
    Architecture,
    OperatingSystem,
    Vendor,
    EnvironmentType,
)


class TripleParseError(Exception):
    """Triple 解析错误"""

    pass


@dataclass
class TargetTriple:
    """
    目标三元组

    表示一个完整的编译目标，包含架构、厂商、操作系统和环境信息。
    """

    arch: Architecture
    vendor: Vendor
    os: OperatingSystem
    environment: Optional[EnvironmentType] = None
    original: str = ""  # 原始三元组字符串

    def __str__(self) -> str:
        """转换为字符串表示"""
        parts = [self.arch.name.lower(), self.vendor.name.lower(), self.os.name.lower()]

        if self.environment and self.environment != EnvironmentType.UNKNOWN:
            parts.append(self.environment.name.lower())

        # 特殊处理
        return self._normalize_triple_string(parts)

    def _normalize_triple_string(self, parts: list) -> str:
        """规范化三元组字符串"""
        arch_str = parts[0]
        vendor_str = parts[1]
        os_str = parts[2]
        env_str = parts[3] if len(parts) > 3 else None

        # 架构别名
        arch_aliases = {
            "x86_64": "x86_64",
            "amd64": "x86_64",
            "aarch64": "aarch64",
            "arm64": "aarch64",
            "arm": "arm",
            "riscv64": "riscv64",
            "riscv32": "riscv32",
            "wasm32": "wasm32",
            "wasm64": "wasm64",
            "i386": "i386",
            "i686": "i386",
        }
        arch_str = arch_aliases.get(arch_str, arch_str)

        # 厂商别名
        vendor_aliases = {
            "unknown": "unknown",
            "pc": "pc",
            "apple": "apple",
            "nvidia": "nvidia",
        }
        vendor_str = vendor_aliases.get(vendor_str, vendor_str)

        # 操作系统别名
        os_aliases = {
            "linux": "linux",
            "darwin": "darwin",
            "windows": "windows",
            "freebsd": "freebsd",
            "unknown": "unknown",
        }
        os_str = os_aliases.get(os_str, os_str)

        # 构建三元组
        result = f"{arch_str}-{vendor_str}-{os_str}"

        # 添加环境
        if env_str:
            env_aliases = {
                "gnu": "gnu",
                "gnueabi": "gnueabi",
                "gnueabihf": "gnueabihf",
                "musl": "musl",
                "msvc": "msvc",
                "eabi": "eabi",
                "android": "android",
            }
            env_str = env_aliases.get(env_str, env_str)
            result += f"-{env_str}"

        return result

    @property
    def is_native(self) -> bool:
        """是否为本机目标"""
        from .host_detector import HostDetector

        host = HostDetector.detect()
        return self.arch == host.arch and self.os == host.os

    @property
    def is_cross(self) -> bool:
        """是否为交叉编译目标"""
        return not self.is_native

    @property
    def is_embedded(self) -> bool:
        """是否为嵌入式目标"""
        return self.os == OperatingSystem.UNKNOWN and self.arch in (
            Architecture.ARM,
            Architecture.ARMV7,
        )

    @property
    def is_wasm(self) -> bool:
        """是否为 WebAssembly 目标"""
        return self.arch in (Architecture.WASM32, Architecture.WASM64)


class TripleParser:
    """
    目标三元组解析器

    解析 LLVM 风格的目标三元组字符串，返回结构化的 TargetTriple 对象。
    """

    # 架构映射表
    ARCH_MAP = {
        # x86
        "x86_64": Architecture.X86_64,
        "amd64": Architecture.X86_64,
        "x64": Architecture.X86_64,
        "i386": Architecture.I386,
        "i486": Architecture.I386,
        "i586": Architecture.I386,
        "i686": Architecture.I386,
        "x86": Architecture.I386,
        # ARM
        "aarch64": Architecture.AARCH64,
        "arm64": Architecture.AARCH64,
        "armv8": Architecture.AARCH64,
        "arm": Architecture.ARM,
        "armv7": Architecture.ARM,
        "armv7a": Architecture.ARM,
        "armv7l": Architecture.ARM,
        "armv6": Architecture.ARM,
        "thumb": Architecture.ARM,
        # RISC-V
        "riscv64": Architecture.RISCV64,
        "riscv32": Architecture.RISCV32,
        "riscv": Architecture.RISCV64,  # 默认 64 位
        # WebAssembly
        "wasm32": Architecture.WASM32,
        "wasm64": Architecture.WASM64,
        "wasm": Architecture.WASM32,  # 默认 32 位
    }

    # 厂商映射表
    VENDOR_MAP = {
        "unknown": Vendor.UNKNOWN,
        "pc": Vendor.PC,
        "apple": Vendor.APPLE,
        "nvidia": Vendor.NVIDIA,
        "gnu": Vendor.GNU,
        # 别名
        "lenovo": Vendor.PC,
        "hp": Vendor.PC,
        "dell": Vendor.PC,
    }

    # 操作系统映射表
    OS_MAP = {
        "linux": OperatingSystem.LINUX,
        "darwin": OperatingSystem.DARWIN,
        "macos": OperatingSystem.DARWIN,
        "macosx": OperatingSystem.DARWIN,
        "ios": OperatingSystem.DARWIN,
        "windows": OperatingSystem.WINDOWS,
        "win32": OperatingSystem.WINDOWS,
        "mingw32": OperatingSystem.WINDOWS,
        "mingw64": OperatingSystem.WINDOWS,
        "cygwin": OperatingSystem.WINDOWS,
        "msvc": OperatingSystem.WINDOWS,
        "freebsd": OperatingSystem.FREEBSD,
        "netbsd": OperatingSystem.FREEBSD,
        "openbsd": OperatingSystem.FREEBSD,
        "android": OperatingSystem.ANDROID,
        "linux-android": OperatingSystem.ANDROID,
        "emscripten": OperatingSystem.EMSCRIPTEN,
        "unknown": OperatingSystem.UNKNOWN,
        "none": OperatingSystem.UNKNOWN,
    }

    # 环境映射表
    ENVIRONMENT_MAP = {
        "gnu": EnvironmentType.GNU,
        "gnueabi": EnvironmentType.GNUABI,
        "gnueabihf": EnvironmentType.GNUABI,
        "gnuabi": EnvironmentType.GNUABI,
        "musl": EnvironmentType.MUSL,
        "musleabi": EnvironmentType.MUSL,
        "musleabihf": EnvironmentType.MUSL,
        "msvc": EnvironmentType.MSVC,
        "eabi": EnvironmentType.EABI,
        "eabihf": EnvironmentType.EABI,
        "android": EnvironmentType.ANDROID,
        "androideabi": EnvironmentType.ANDROID,
    }

    @classmethod
    def parse(cls, triple: str) -> TargetTriple:
        """
        解析目标三元组字符串

        Args:
            triple: 目标三元组字符串

        Returns:
            结构化的 TargetTriple 对象

        Raises:
            TripleParseError: 解析失败

        示例:
            >>> t = TripleParser.parse("x86_64-unknown-linux-gnu")
            >>> t.arch
            <Architecture.X86_64: 1>
            >>> t.os
            <OperatingSystem.LINUX: 1>
        """
        if not triple or not isinstance(triple, str):
            raise TripleParseError(f"Invalid triple: {triple}")

        # 预处理：去除空白，转小写
        triple = triple.strip().lower()

        # 特殊别名处理
        triple = cls._resolve_aliases(triple)

        # 分割各部分
        parts = triple.split("-")

        if len(parts) < 3:
            raise TripleParseError(
                f"Triple must have at least 3 parts (arch-vendor-os): {triple}"
            )

        # 解析各部分
        arch = cls._parse_arch(parts[0])
        vendor = cls._parse_vendor(parts[1])
        os = cls._parse_os(parts[2])
        environment = cls._parse_environment(parts[3]) if len(parts) > 3 else None

        # 验证组合
        cls._validate_triple(arch, vendor, os, environment)

        return TargetTriple(
            arch=arch,
            vendor=vendor,
            os=os,
            environment=environment,
            original=triple,
        )

    @classmethod
    def _resolve_aliases(cls, triple: str) -> str:
        """解析常见别名"""
        aliases = {
            # 简写形式
            "linux": "x86_64-unknown-linux-gnu",
            "linux64": "x86_64-unknown-linux-gnu",
            "linux32": "i386-unknown-linux-gnu",
            "macos": "x86_64-apple-darwin",
            "macos64": "x86_64-apple-darwin",
            "macos-arm64": "aarch64-apple-darwin",
            "windows": "x86_64-pc-windows-msvc",
            "win64": "x86_64-pc-windows-msvc",
            "win32": "i386-pc-windows-msvc",
            "wasm": "wasm32-unknown-unknown",
            "wasm32": "wasm32-unknown-unknown",
            "wasm64": "wasm64-unknown-unknown",
            "arm": "arm-unknown-linux-gnueabihf",
            "arm64": "aarch64-unknown-linux-gnu",
            "aarch64": "aarch64-unknown-linux-gnu",
            "riscv64": "riscv64-unknown-linux-gnu",
            "riscv32": "riscv32-unknown-linux-gnu",
        }

        return aliases.get(triple, triple)

    @classmethod
    def _parse_arch(cls, arch_str: str) -> Architecture:
        """解析架构"""
        arch = cls.ARCH_MAP.get(arch_str)

        if arch is None:
            # 尝试正则匹配
            match = re.match(r"(arm|aarch|riscv|wasm|x86|i\d+)", arch_str)
            if match:
                arch = cls.ARCH_MAP.get(match.group(0))

        if arch is None:
            raise TripleParseError(f"Unknown architecture: {arch_str}")

        return arch

    @classmethod
    def _parse_vendor(cls, vendor_str: str) -> Vendor:
        """解析厂商"""
        vendor = cls.VENDOR_MAP.get(vendor_str)

        if vendor is None:
            # 未知厂商使用 UNKNOWN
            vendor = Vendor.UNKNOWN

        return vendor

    @classmethod
    def _parse_os(cls, os_str: str) -> OperatingSystem:
        """解析操作系统"""
        # 处理复合 OS 名称（如 linux-android）
        for key, value in cls.OS_MAP.items():
            if os_str.startswith(key) or os_str == key:
                return value

        # 未知 OS
        if os_str in ("none", "unknown"):
            return OperatingSystem.UNKNOWN

        raise TripleParseError(f"Unknown operating system: {os_str}")

    @classmethod
    def _parse_environment(cls, env_str: str) -> Optional[EnvironmentType]:
        """解析环境"""
        # 处理复合环境名
        for key, value in cls.ENVIRONMENT_MAP.items():
            if env_str.startswith(key) or env_str == key:
                return value

        return None

    @classmethod
    def _validate_triple(
        cls,
        arch: Architecture,
        vendor: Vendor,
        os: OperatingSystem,
        environment: Optional[EnvironmentType],
    ) -> None:
        """验证三元组组合的有效性"""
        # 检查架构和 OS 的兼容性
        if os == OperatingSystem.DARWIN:
            if arch not in (Architecture.X86_64, Architecture.AARCH64):
                raise TripleParseError(
                    f"macOS only supports x86_64 and aarch64, got {arch.name}"
                )

        if os == OperatingSystem.WINDOWS:
            if arch not in (
                Architecture.X86_64,
                Architecture.I386,
                Architecture.AARCH64,
            ):
                raise TripleParseError(
                    f"Windows only supports x86_64, i386, and aarch64, got {arch.name}"
                )

        # WebAssembly 特殊处理
        if arch in (Architecture.WASM32, Architecture.WASM64):
            if os != OperatingSystem.UNKNOWN and os != OperatingSystem.EMSCRIPTEN:
                raise TripleParseError(
                    f"WebAssembly targets should have 'unknown' or 'emscripten' OS, got {os.name}"
                )

    @classmethod
    def normalize(cls, triple: str) -> str:
        """
        规范化三元组字符串

        Args:
            triple: 输入三元组

        Returns:
            规范化后的三元组
        """
        parsed = cls.parse(triple)
        return str(parsed)

    @classmethod
    def is_valid(cls, triple: str) -> bool:
        """
        检查三元组是否有效

        Args:
            triple: 目标三元组

        Returns:
            是否有效
        """
        try:
            cls.parse(triple)
            return True
        except TripleParseError:
            return False

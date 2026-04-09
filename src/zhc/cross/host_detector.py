# -*- coding: utf-8 -*-
"""
ZhC 主机平台检测器

自动检测当前主机的平台信息，包括架构、操作系统、CPU 等。

作者：远
日期：2026-04-09
"""

import platform
import subprocess
import os
from dataclasses import dataclass
from typing import List, Optional

from zhc.codegen.target_registry import (
    Architecture,
    OperatingSystem,
    Vendor,
)


@dataclass
class CPUInfo:
    """CPU 信息"""

    brand: str  # CPU 型号名称
    family: Optional[str] = None  # CPU 系列
    model: Optional[str] = None  # CPU 型号
    cores: int = 0  # 核心数
    threads: int = 0  # 线程数
    features: List[str] = None  # CPU 特性（如 SSE4.2, AVX 等）

    def __post_init__(self):
        if self.features is None:
            self.features = []


@dataclass
class HostInfo:
    """
    主机平台信息

    包含主机的完整平台信息，用于本机编译和交叉编译判断。
    """

    triple: str  # 完整三元组
    arch: Architecture  # CPU 架构
    os: OperatingSystem  # 操作系统
    vendor: Vendor  # 厂商
    cpu: CPUInfo  # CPU 信息
    features: List[str]  # 平台特性
    pointer_size: int  # 指针大小（字节）

    def __str__(self) -> str:
        return f"{self.triple} (CPU: {self.cpu.brand})"

    @property
    def is_64bit(self) -> bool:
        """是否为 64 位平台"""
        return self.pointer_size == 8

    @property
    def is_32bit(self) -> bool:
        """是否为 32 位平台"""
        return self.pointer_size == 4

    @property
    def is_linux(self) -> bool:
        """是否为 Linux"""
        return self.os == OperatingSystem.LINUX

    @property
    def is_macos(self) -> bool:
        """是否为 macOS"""
        return self.os == OperatingSystem.DARWIN

    @property
    def is_windows(self) -> bool:
        """是否为 Windows"""
        return self.os == OperatingSystem.WINDOWS


class HostDetector:
    """
    主机平台检测器

    提供静态方法检测当前主机平台信息。
    """

    # 架构映射表
    ARCH_MAP = {
        "x86_64": Architecture.X86_64,
        "amd64": Architecture.X86_64,
        "aarch64": Architecture.AARCH64,
        "arm64": Architecture.AARCH64,
        "armv8l": Architecture.AARCH64,
        "armv7l": Architecture.ARM,
        "armv6l": Architecture.ARM,
        "riscv64": Architecture.RISCV64,
        "riscv32": Architecture.RISCV32,
        "riscv": Architecture.RISCV64,
        "wasm32": Architecture.WASM32,
        "wasm64": Architecture.WASM64,
        "i386": Architecture.I386,
        "i486": Architecture.I386,
        "i586": Architecture.I386,
        "i686": Architecture.I386,
        "sparc64": Architecture.UNKNOWN,
        "s390x": Architecture.UNKNOWN,
    }

    # OS 映射表
    OS_MAP = {
        "linux": OperatingSystem.LINUX,
        "darwin": OperatingSystem.DARWIN,
        "macos": OperatingSystem.DARWIN,
        "windows": OperatingSystem.WINDOWS,
        "cygwin": OperatingSystem.WINDOWS,
        "mingw": OperatingSystem.WINDOWS,
        "freebsd": OperatingSystem.FREEBSD,
        "netbsd": OperatingSystem.FREEBSD,
        "openbsd": OperatingSystem.FREEBSD,
        "android": OperatingSystem.ANDROID,
    }

    # 厂商映射表
    VENDOR_MAP = {
        "linux": Vendor.UNKNOWN,
        "darwin": Vendor.APPLE,
        "windows": Vendor.PC,
        "freebsd": Vendor.UNKNOWN,
    }

    @classmethod
    def detect(cls) -> HostInfo:
        """
        检测主机平台信息

        Returns:
            主机平台信息对象
        """
        arch = cls._detect_arch()
        os_type = cls._detect_os()
        vendor = cls._detect_vendor()
        cpu = cls._detect_cpu()
        features = cls._detect_cpu_features()
        triple = cls._build_triple(arch, os_type)

        # 确定指针大小
        pointer_size = 8 if arch.is_64bit else 4

        return HostInfo(
            triple=triple,
            arch=arch,
            os=os_type,
            vendor=vendor,
            cpu=cpu,
            features=features,
            pointer_size=pointer_size,
        )

    @classmethod
    def _detect_arch(cls) -> Architecture:
        """检测 CPU 架构"""
        machine = platform.machine().lower()
        return cls.ARCH_MAP.get(machine, Architecture.UNKNOWN)

    @classmethod
    def _detect_os(cls) -> OperatingSystem:
        """检测操作系统"""
        system = platform.system().lower()

        # 特殊处理
        if system == "darwin":
            return OperatingSystem.DARWIN
        if system == "linux":
            # 检查 Android
            if cls._is_android():
                return OperatingSystem.ANDROID
            return OperatingSystem.LINUX
        if system == "windows" or system.startswith("cygwin"):
            return OperatingSystem.WINDOWS

        return cls.OS_MAP.get(system, OperatingSystem.UNKNOWN)

    @classmethod
    def _is_android(cls) -> bool:
        """检查是否为 Android"""
        try:
            if os.path.exists("/system/build.prop"):
                with open("/system/build.prop") as f:
                    content = f.read()
                    return "android" in content.lower()
        except Exception:
            pass
        return False

    @classmethod
    def _detect_vendor(cls) -> Vendor:
        """检测厂商"""
        system = platform.system().lower()
        return cls.VENDOR_MAP.get(system, Vendor.UNKNOWN)

    @classmethod
    def _detect_cpu(cls) -> CPUInfo:
        """检测 CPU 信息"""
        cpu_brand = cls._get_cpu_brand()
        cpu_cores = cls._get_cpu_cores()
        cpu_features = cls._detect_cpu_features()

        return CPUInfo(
            brand=cpu_brand,
            cores=cpu_cores,
            threads=cpu_cores,  # 简化处理
            features=cpu_features,
        )

    @classmethod
    def _get_cpu_brand(cls) -> str:
        """获取 CPU 型号"""
        system = platform.system().lower()

        if system == "linux":
            return cls._get_linux_cpu_brand()
        elif system == "darwin":
            return cls._get_darwin_cpu_brand()
        elif system == "windows":
            return platform.processor() or "Unknown"
        else:
            return platform.machine()

    @classmethod
    def _get_linux_cpu_brand(cls) -> str:
        """从 Linux 获取 CPU 型号"""
        try:
            # 尝试从 /proc/cpuinfo 获取
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line or "Model" in line:
                        return line.split(":", 1)[1].strip()

            # 尝试 sysctl
            result = subprocess.run(["uname", "-m"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return platform.machine()

    @classmethod
    def _get_darwin_cpu_brand(cls) -> str:
        """从 macOS 获取 CPU 型号"""
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass

        # 备用方案
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.model"], capture_output=True, text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return "Apple Silicon" if platform.machine() == "arm64" else "Intel CPU"

    @classmethod
    def _get_cpu_cores(cls) -> int:
        """获取 CPU 核心数"""
        try:
            return os.cpu_count() or 1
        except Exception:
            pass

        # 备用方案
        system = platform.system().lower()
        if system == "linux":
            try:
                with open("/proc/cpuinfo") as f:
                    return sum(1 for line in f if line.startswith("processor"))
            except Exception:
                pass
        elif system == "darwin":
            try:
                result = subprocess.run(
                    ["sysctl", "-n", "hw.physicalcpu"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    return int(result.stdout.strip())
            except Exception:
                pass

        return 1

    @classmethod
    def _detect_cpu_features(cls) -> List[str]:
        """检测 CPU 特性"""
        features = []
        system = platform.system().lower()

        if system == "linux":
            features = cls._detect_linux_cpu_features()
        elif system == "darwin":
            features = cls._detect_darwin_cpu_features()
        elif system == "windows":
            features = cls._detect_windows_cpu_features()

        return features

    @classmethod
    def _detect_linux_cpu_features(cls) -> List[str]:
        """检测 Linux CPU 特性"""
        features = []
        try:
            with open("/proc/cpuinfo") as f:
                content = f.read()

            # 检查常见特性
            feature_checks = {
                "sse4_2": "sse4.2",
                "sse4_1": "sse4.1",
                "ssse3": "ssse3",
                "sse3": "sse3",
                "sse2": "sse2",
                "avx": "avx",
                "avx2": "avx2",
                "avx512f": "avx512f",
                "neon": "neon",
                "asimd": "neon",  # ARM NEON
                "vfpv4": "vfp4",
                "fma": "fma",
            }

            for flag, feature in feature_checks.items():
                if flag in content:
                    features.append(feature)
        except Exception:
            pass

        return features

    @classmethod
    def _detect_darwin_cpu_features(cls) -> List[str]:
        """检测 macOS CPU 特性"""
        features = []
        machine = platform.machine().lower()

        # Apple Silicon 特性
        if machine == "arm64":
            features.extend(["neon", "aes", "sha2", "fp16"])
            # 检查 Apple Silicon 代数
            try:
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True,
                    text=True,
                )
                brand = result.stdout.lower()
                if "m1" in brand:
                    features.extend(["m1"])
                elif "m2" in brand:
                    features.extend(["m2", "m1"])
                elif "m3" in brand:
                    features.extend(["m3", "m2", "m1"])
            except Exception:
                pass
        else:
            # Intel 特性
            try:
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.features"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    for feat in result.stdout.lower().split():
                        features.append(feat)
            except Exception:
                pass

        return features

    @classmethod
    def _detect_windows_cpu_features(cls) -> List[str]:
        """检测 Windows CPU 特性"""
        # Windows 上较难检测，简化处理
        arch = cls._detect_arch()

        if arch == Architecture.X86_64:
            return ["sse4.2", "popcnt"]  # 假设现代 x86_64
        elif arch == Architecture.AARCH64:
            return ["neon"]
        else:
            return []

    @classmethod
    def _build_triple(cls, arch: Architecture, os: OperatingSystem) -> str:
        """构建主机三元组"""
        arch_str = cls._arch_to_string(arch)
        os_str = cls._os_to_string(os)

        return f"{arch_str}-{os_str}"

    @classmethod
    def _arch_to_string(cls, arch: Architecture) -> str:
        """架构转字符串"""
        arch_map = {
            Architecture.X86_64: "x86_64",
            Architecture.I386: "i386",
            Architecture.AARCH64: "aarch64",
            Architecture.ARM: "arm",
            Architecture.RISCV64: "riscv64",
            Architecture.RISCV32: "riscv32",
            Architecture.WASM32: "wasm32",
            Architecture.WASM64: "wasm64",
        }
        return arch_map.get(arch, "unknown")

    @classmethod
    def _os_to_string(cls, os: OperatingSystem) -> str:
        """OS 转字符串"""
        os_map = {
            OperatingSystem.LINUX: "unknown-linux-gnu",
            OperatingSystem.DARWIN: "apple-darwin",
            OperatingSystem.WINDOWS: "pc-windows-msvc",
            OperatingSystem.FREEBSD: "unknown-freebsd",
            OperatingSystem.ANDROID: "linux-android",
            OperatingSystem.EMSCRIPTEN: "emscripten",
        }
        return os_map.get(os, "unknown-unknown")


# 便捷函数
def get_host_info() -> HostInfo:
    """
    获取主机信息

    Returns:
        主机平台信息
    """
    return HostDetector.detect()


def is_native_target(triple: str) -> bool:
    """
    判断目标三元组是否为本机

    Args:
        triple: 目标三元组

    Returns:
        是否为本机编译
    """
    from .triple_parser import TripleParser

    try:
        target = TripleParser.parse(triple)
        return target.is_native
    except Exception:
        return False

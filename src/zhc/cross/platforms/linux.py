# -*- coding: utf-8 -*-
"""
ZhC Linux 平台配置

提供 Linux 平台的特定配置，包括 glibc、musl 支持等。

作者：远
日期：2026-04-09
"""

import os
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from zhc.codegen.target_registry import (
    Architecture,
    OperatingSystem,
)


@dataclass
class LinuxABI:
    """Linux ABI 配置"""

    # 架构特定配置
    dynamic_linkers: Dict[Architecture, str] = None

    # 库路径
    default_lib_paths: List[str] = field(
        default_factory=lambda: [
            "/lib",
            "/lib64",
            "/usr/lib",
            "/usr/lib64",
            "/usr/local/lib",
            "/usr/local/lib64",
        ]
    )

    # 32位库路径
    lib32_paths: List[str] = field(
        default_factory=lambda: [
            "/lib32",
            "/usr/lib32",
            "/usr/lib/i386-linux-gnu",
        ]
    )

    # 64位库路径
    lib64_paths: List[str] = field(
        default_factory=lambda: [
            "/lib64",
            "/usr/lib64",
            "/usr/lib/x86_64-linux-gnu",
            "/lib/x86_64-linux-gnu",
        ]
    )

    def __post_init__(self):
        if self.dynamic_linkers is None:
            self.dynamic_linkers = {
                Architecture.X86_64: "/lib64/ld-linux-x86-64.so.2",
                Architecture.I386: "/lib/ld-linux.so.2",
                Architecture.AARCH64: "/lib/ld-linux-aarch64.so.1",
                Architecture.ARM: "/lib/ld-linux-armhf.so.3",
                Architecture.RISCV64: "/lib/ld-linux-riscv64-lp64d.so.1",
                Architecture.RISCV32: "/lib/ld-linux-riscv32-ilp32d.so.1",
            }


@dataclass
class CRTConfig:
    """CRT 启动文件配置"""

    # 动态链接 CRT
    dynamic_start: List[str] = field(default_factory=lambda: ["crt1.o", "rcrt1.o"])
    dynamic_init: List[str] = field(default_factory=lambda: ["crti.o"])
    dynamic_fini: List[str] = field(default_factory=lambda: ["crtn.o"])

    # 静态链接 CRT
    static_start: List[str] = field(default_factory=lambda: ["crt1.o"])
    static_init: List[str] = field(default_factory=lambda: ["crti.o", "crtbeginS.o"])
    static_fini: List[str] = field(default_factory=lambda: ["crtn.o", "crtendS.o"])

    # Shared 对象 CRT
    shared_start: List[str] = field(default_factory=lambda: ["crt1.o", "rcrt1.o"])
    shared_init: List[str] = field(default_factory=lambda: ["crti.o", "crtbeginS.o"])
    shared_fini: List[str] = field(default_factory=lambda: ["crtn.o", "crtendS.o"])


class LinuxPlatform:
    """
    Linux 平台配置

    提供 Linux 平台的完整配置，包括路径、ABI、CRT 等。
    """

    name = "linux"
    os_type = OperatingSystem.LINUX

    # 支持的架构
    supported_archs = [
        Architecture.X86_64,
        Architecture.I386,
        Architecture.AARCH64,
        Architecture.ARM,
        Architecture.RISCV64,
        Architecture.RISCV32,
    ]

    # ABI 配置
    abi = LinuxABI()

    # CRT 配置
    crt = CRTConfig()

    @classmethod
    def is_supported(cls, arch: Architecture) -> bool:
        """检查架构是否支持"""
        return arch in cls.supported_archs

    @classmethod
    def get_dynamic_linker(cls, arch: Architecture) -> str:
        """获取动态链接器路径"""
        return cls.abi.dynamic_linkers.get(arch, "/lib/ld-linux.so.2")

    @classmethod
    def get_lib_paths(cls, arch: Architecture) -> List[str]:
        """获取库搜索路径"""
        if arch == Architecture.X86_64:
            return cls.abi.lib64_paths.copy()
        elif arch == Architecture.I386:
            return cls.abi.lib32_paths.copy()
        else:
            return cls.abi.default_lib_paths.copy()

    @classmethod
    def get_crt_files(cls, link_type: str = "dynamic") -> List[str]:
        """获取 CRT 文件"""
        if link_type == "static":
            files = cls.crt.static_start + cls.crt.static_init
            files += cls.crt.static_fini
        elif link_type == "shared":
            files = cls.crt.shared_start + cls.crt.shared_init
            files += cls.crt.shared_fini
        else:
            files = cls.crt.dynamic_start + cls.crt.dynamic_init
            files += cls.crt.dynamic_fini

        return files

    @classmethod
    def get_sysroot(cls, arch: Architecture) -> Optional[str]:
        """获取 sysroot 路径"""
        arch_str = arch.name.lower()

        common_paths = [
            f"/usr/{arch_str}-linux-gnu",
            f"/usr/{arch_str}-unknown-linux-gnu",
            f"/usr/local/{arch_str}-linux-gnu",
            f"/opt/{arch_str}-linux-gnu",
        ]

        for path in common_paths:
            if os.path.isdir(path):
                return path

        return None

    @classmethod
    def detect_architecture(cls) -> Optional[Architecture]:
        """检测系统架构"""
        import platform

        machine = platform.machine().lower()
        arch_map = {
            "x86_64": Architecture.X86_64,
            "aarch64": Architecture.AARCH64,
            "arm64": Architecture.AARCH64,
            "armv7l": Architecture.ARM,
            "armv6l": Architecture.ARM,
            "riscv64": Architecture.RISCV64,
            "riscv32": Architecture.RISCV32,
            "i386": Architecture.I386,
            "i686": Architecture.I386,
        }

        return arch_map.get(machine)

    @classmethod
    def get_glibc_version(cls) -> Optional[str]:
        """获取 glibc 版本"""
        try:
            result = subprocess.run(
                ["ldd", "--version"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                import re

                match = re.search(r"ldd\s+\(.*?\)\s+(\d+\.\d+)", result.stderr)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return None

    @classmethod
    def is_musl(cls) -> bool:
        """检查是否为 musl libc"""
        try:
            result = subprocess.run(
                ["ldd", "--version"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return "musl" in result.stderr.lower()
        except Exception:
            pass
        return False

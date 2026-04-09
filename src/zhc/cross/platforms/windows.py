# -*- coding: utf-8 -*-
"""
ZhC Windows 平台配置

提供 Windows 平台的特定配置，包括 MSVC、MinGW、MSYS2 等。

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
class MSVCInfo:
    """MSVC 工具链信息"""

    path: str  # MSVC 安装路径
    version: str  # MSVC 版本
    include_path: str = ""
    lib_path: str = ""
    bin_path: str = ""

    # 运行时
    static_runtime: str = "libcmt.lib"
    dynamic_runtime: str = "msvcrt.lib"
    static_debug_runtime: str = "libcmtd.lib"
    dynamic_debug_runtime: str = "msvcrtd.lib"


@dataclass
class WindowsABI:
    """Windows ABI 配置"""

    # LLP64 数据模型
    pointer_size: int = 8
    long_size: int = 4  # Windows: long 是 32 位
    int_size: int = 4

    # 调用约定
    calling_conventions: Dict[str, str] = field(
        default_factory=lambda: {
            "x64": "ms_abi",
            "x86": "stdcall",
            "arm": "aapcs",
            "aarch64": "aapcs",
        }
    )

    # 寄存器
    x64_regs: Dict[str, str] = field(
        default_factory=lambda: {
            "return": "rax",
            "first_param": "rcx",
            "second_param": "rdx",
            "third_param": "r8",
            "fourth_param": "r9",
        }
    )


@dataclass
class WindowsPlatform:
    """
    Windows 平台配置

    提供 Windows 平台的完整配置。
    """

    name = "windows"
    os_type = OperatingSystem.WINDOWS

    # 支持的架构
    supported_archs = [
        Architecture.X86_64,
        Architecture.I386,
        Architecture.AARCH64,
    ]

    # ABI 配置
    abi = WindowsABI()

    # MSVC 运行时
    msvc_runtimes = {
        "static_debug": "libcmt.lib",
        "static_release": "libcmt.lib",
        "dynamic_debug": "msvcrt.lib",
        "dynamic_release": "msvcrt.lib",
    }

    # 默认库
    default_libs = [
        "kernel32",
        "user32",
        "gdi32",
        "advapi32",
        "shell32",
        "ole32",
        "oleaut32",
        "uuid",
        "msvcrt",
    ]

    # DLL 扩展
    dll_extension = ".dll"
    lib_extension = ".lib"
    exe_extension = ".exe"

    @classmethod
    def is_supported(cls, arch: Architecture) -> bool:
        """检查架构是否支持"""
        return arch in cls.supported_archs

    @classmethod
    def detect_msvc(cls) -> Optional[MSVCInfo]:
        """检测 MSVC 安装"""
        # 使用 vswhere 查找
        try:
            result = subprocess.run(
                [
                    os.path.join(
                        os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
                        "Microsoft Visual Studio",
                        "Installer",
                        "vswhere.exe",
                    ),
                    "-latest",
                    "-property",
                    "installationPath",
                    "-requires",
                    "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                vs_path = result.stdout.strip()
                if vs_path:
                    return cls._get_msvc_info(vs_path)
        except Exception:
            pass

        # 尝试常见路径
        common_paths = [
            "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community",
            "C:\\Program Files\\Microsoft Visual Studio\\2022\\Professional",
            "C:\\Program Files\\Microsoft Visual Studio\\2022\\Enterprise",
            "C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\Community",
            "C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\Professional",
            "C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\Enterprise",
        ]

        for path in common_paths:
            if os.path.isdir(path):
                return cls._get_msvc_info(path)

        return None

    @classmethod
    def _get_msvc_info(cls, vs_path: str) -> Optional[MSVCInfo]:
        """获取 MSVC 信息"""
        # 查找 VC 目录
        vc_dirs = []
        try:
            for item in os.listdir(os.path.join(vs_path, "VC", "Tools", "MSVC")):
                vc_dirs.append(item)
        except Exception:
            pass

        if vc_dirs:
            latest_vc = sorted(vc_dirs, reverse=True)[0]
            vc_path = os.path.join(vs_path, "VC", "Tools", "MSVC", latest_vc)

            return MSVCInfo(
                path=vc_path,
                version=latest_vc,
                include_path=os.path.join(vc_path, "include"),
                lib_path=os.path.join(vc_path, "lib", "x64"),
                bin_path=os.path.join(vc_path, "bin", "Hostx64", "x64"),
            )

        return None

    @classmethod
    def detect_mingw(cls) -> Optional[str]:
        """检测 MinGW 安装"""
        mingw_paths = [
            "C:\\msys64\\mingw64",
            "C:\\msys64\\mingw32",
            "C:\\MinGW",
        ]

        for path in mingw_paths:
            if os.path.isdir(path):
                return path

        return None

    @classmethod
    def get_msvc_toolchain_path(cls) -> Optional[str]:
        """获取 MSVC 工具链路径"""
        msvc_info = cls.detect_msvc()
        return msvc_info.path if msvc_info else None

    @classmethod
    def get_windows_sdk_path(cls) -> Optional[str]:
        """获取 Windows SDK 路径"""
        # 查找 Windows SDK
        sdk_paths = [
            os.path.join(
                os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
                "Windows Kits",
                "10",
            ),
            os.path.join(
                os.environ.get("ProgramFiles", "C:\\Program Files"),
                "Windows Kits",
                "10",
            ),
        ]

        for path in sdk_paths:
            if os.path.isdir(path):
                return path

        return None

    @classmethod
    def get_system_lib_paths(
        cls, arch: Architecture = Architecture.X86_64
    ) -> List[str]:
        """获取系统库路径"""
        paths = []

        # MSVC 库
        msvc_info = cls.detect_msvc()
        if msvc_info:
            if arch == Architecture.X86_64:
                paths.append(os.path.join(msvc_info.path, "lib", "x64"))
            elif arch == Architecture.I386:
                paths.append(os.path.join(msvc_info.path, "lib", "x86"))
            elif arch == Architecture.AARCH64:
                paths.append(os.path.join(msvc_info.path, "lib", "arm64"))

        # Windows SDK 库
        sdk_path = cls.get_windows_sdk_path()
        if sdk_path:
            lib_path = os.path.join(sdk_path, "Lib", "10.0.22621.0", "um", "x64")
            if os.path.isdir(lib_path):
                paths.append(lib_path)

        return paths

    @classmethod
    def get_crt_files(
        cls, link_type: str = "dynamic", static: bool = False
    ) -> List[str]:
        """获取 CRT 文件"""
        if link_type == "static" or static:
            return ["libcmt.lib", "libvcruntime.lib"]
        else:
            return ["msvcrt.lib"]

    @classmethod
    def get_linker_flags(cls, arch: Architecture = Architecture.X86_64) -> List[str]:
        """获取链接器标志"""
        flags = [
            "/nologo",
            "/subsystem:console",
            "/entry:mainCRTStartup",
        ]

        if arch == Architecture.X86_64:
            flags.append("/machine:x64")
        elif arch == Architecture.I386:
            flags.append("/machine:x86")
        elif arch == Architecture.AARCH64:
            flags.append("/machine:arm64")

        return flags

    @classmethod
    def get_compiler_flags(cls, arch: Architecture = Architecture.X86_64) -> List[str]:
        """获取编译器标志"""
        flags = [
            "/nologo",
            "/W3",
            "/EHsc",
        ]

        if arch == Architecture.X86_64:
            flags.append("/arch:AVX2")
        elif arch == Architecture.AARCH64:
            flags.append("/arch:ARMv8")

        return flags

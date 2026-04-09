# -*- coding: utf-8 -*-
"""
ZhC macOS 平台配置

提供 macOS 平台的特定配置，包括 SDK、框架、Universal Binary 等。

作者：远
日期：2026-04-09
"""

import os
import subprocess
from dataclasses import dataclass
from typing import List, Optional

from zhc.codegen.target_registry import (
    Architecture,
    OperatingSystem,
)


@dataclass
class SDKInfo:
    """macOS SDK 信息"""

    path: str  # SDK 根路径
    version: str  # SDK 版本
    platform: str  # 平台（macosx, iphoneos, iphonesimulator）

    # 路径
    include_path: str = ""
    lib_path: str = ""
    framework_path: str = ""

    # 部署目标
    deployment_target: str = "10.15"


@dataclass
class MacOSPlatform:
    """
    macOS 平台配置

    提供 macOS/iOS 平台的完整配置。
    """

    name = "darwin"
    os_type = OperatingSystem.DARWIN

    # 支持的架构
    supported_archs = [
        Architecture.X86_64,
        Architecture.AARCH64,  # Apple Silicon
    ]

    # 默认部署目标
    min_macos_version = "10.15"
    min_ios_version = "13.0"

    # 框架路径
    framework_paths = [
        "/System/Library/Frameworks",
        "/Library/Frameworks",
    ]

    # 系统库
    system_libs = ["System", "m"]

    @classmethod
    def is_supported(cls, arch: Architecture) -> bool:
        """检查架构是否支持"""
        return arch in cls.supported_archs

    @classmethod
    def get_sdk_path(cls, platform: str = "macosx") -> Optional[str]:
        """获取 SDK 路径"""
        try:
            result = subprocess.run(
                ["xcrun", "--sdk", platform, "--show-sdk-path"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    @classmethod
    def get_sdk_info(cls, platform: str = "macosx") -> Optional[SDKInfo]:
        """获取 SDK 信息"""
        try:
            # SDK 路径
            path_result = subprocess.run(
                ["xcrun", "--sdk", platform, "--show-sdk-path"],
                capture_output=True,
                text=True,
            )
            if path_result.returncode != 0:
                return None

            sdk_path = path_result.stdout.strip()

            # SDK 版本
            version_result = subprocess.run(
                ["xcrun", "--sdk", platform, "--show-sdk-version"],
                capture_output=True,
                text=True,
            )
            sdk_version = (
                version_result.stdout.strip()
                if version_result.returncode == 0
                else "Unknown"
            )

            return SDKInfo(
                path=sdk_path,
                version=sdk_version,
                platform=platform,
                include_path=os.path.join(sdk_path, "usr/include"),
                lib_path=os.path.join(sdk_path, "usr/lib"),
                framework_path=os.path.join(sdk_path, "System/Library/Frameworks"),
                deployment_target=cls.min_macos_version
                if platform == "macosx"
                else cls.min_ios_version,
            )
        except Exception:
            return None

    @classmethod
    def get_min_deployment_target(cls, platform: str = "macosx") -> str:
        """获取最小部署目标"""
        if platform == "macosx":
            return cls.min_macos_version
        elif platform.startswith("iphoneos"):
            return cls.min_ios_version
        else:
            return cls.min_ios_version

    @classmethod
    def get_sdk_include_paths(cls, platform: str = "macosx") -> List[str]:
        """获取 SDK 头文件路径"""
        sdk_info = cls.get_sdk_info(platform)
        if sdk_info:
            return [
                os.path.join(sdk_info.path, "usr/include"),
                os.path.join(sdk_info.path, "usr/include/c++/v1"),
            ]
        return []

    @classmethod
    def get_sdk_library_paths(
        cls, platform: str = "macosx", arch: Optional[Architecture] = None
    ) -> List[str]:
        """获取 SDK 库路径"""
        sdk_info = cls.get_sdk_info(platform)
        if sdk_info:
            paths = [sdk_info.lib_path]

            if arch == Architecture.AARCH64:
                paths.append(os.path.join(sdk_info.path, "usr/lib/arm64"))
            elif arch == Architecture.X86_64:
                paths.append(os.path.join(sdk_info.path, "usr/lib/x86_64"))

            return paths
        return []

    @classmethod
    def detect_architecture() -> Architecture:
        """检测当前架构"""
        import platform

        machine = platform.machine().lower()

        if machine in ("arm64", "aarch64"):
            return Architecture.AARCH64
        else:
            return Architecture.X86_64

    @classmethod
    def is_apple_silicon(cls) -> bool:
        """检查是否为 Apple Silicon"""
        import platform

        return platform.machine().lower() == "arm64"

    @classmethod
    def get_deployment_flags(
        cls, target: str = "macosx", version: Optional[str] = None
    ) -> List[str]:
        """获取部署目标编译标志"""
        deployment_target = version or cls.get_min_deployment_target(target)

        flags = [
            f"-mmacosx-version-min={deployment_target}",
            "-fno-pie",  # macOS 不使用 PIE
        ]

        if cls.is_apple_silicon():
            flags.append("-arch arm64")
        else:
            flags.append("-arch x86_64")

        return flags

    @classmethod
    def get_universal_binary_archs(
        cls, x86_64: bool = True, arm64: bool = True
    ) -> List[str]:
        """获取 Universal Binary 架构列表"""
        archs = []
        if x86_64:
            archs.append("x86_64")
        if arm64:
            archs.append("arm64")
        return archs

    @classmethod
    def get_toolchain_path(cls) -> Optional[str]:
        """获取 Xcode 工具链路径"""
        try:
            result = subprocess.run(
                ["xcode-select", "-p"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    @classmethod
    def get_clang_path(cls) -> Optional[str]:
        """获取 clang 路径"""
        try:
            result = subprocess.run(
                ["xcrun", "-f", "clang"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

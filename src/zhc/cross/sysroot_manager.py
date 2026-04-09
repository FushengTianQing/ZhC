# -*- coding: utf-8 -*-
"""
ZhC Sysroot 管理器

管理交叉编译所需的 sysroot（系统根目录），包括库文件、头文件等的查找。

作者：远
日期：2026-04-09
"""

import os
import subprocess
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from .triple_parser import TargetTriple, TripleParser
from zhc.codegen.target_registry import (
    Architecture,
    Vendor,
    OperatingSystem,
    EnvironmentType,
)

logger = logging.getLogger(__name__)


class SysrootError(Exception):
    """Sysroot 错误"""

    pass


@dataclass
class Sysroot:
    """
    Sysroot 描述

    包含交叉编译所需的文件系统根目录信息。
    """

    path: str  # sysroot 路径
    target: TargetTriple  # 目标平台

    # 目录结构
    include_dir: str = ""  # 头文件目录
    lib_dir: str = ""  # 库文件目录
    lib32_dir: str = ""  # 32 位库目录
    lib64_dir: str = ""  # 64 位库目录
    usr_dir: str = ""  # usr 目录
    bin_dir: str = ""  # 二进制目录

    # 特殊目录
    sysroot_include: str = ""  # 系统头文件目录
    sysroot_lib: str = ""  # 系统库目录

    def exists(self) -> bool:
        """检查 sysroot 是否存在"""
        return os.path.isdir(self.path)

    def validate(self) -> bool:
        """验证 sysroot 完整性"""
        if not self.exists():
            return False

        # 检查基本目录
        required_dirs = [self.include_dir, self.lib_dir]
        return all(os.path.isdir(d) for d in required_dirs if d)

    def get_include_paths(self) -> List[str]:
        """获取所有头文件搜索路径"""
        paths = []

        if self.include_dir and os.path.isdir(self.include_dir):
            paths.append(self.include_dir)

        if self.sysroot_include and os.path.isdir(self.sysroot_include):
            paths.append(self.sysroot_include)

        usr_include = os.path.join(self.path, "usr", "include")
        if os.path.isdir(usr_include):
            paths.append(usr_include)

        return paths

    def get_library_paths(self) -> List[str]:
        """获取所有库文件搜索路径"""
        paths = []

        if self.lib_dir and os.path.isdir(self.lib_dir):
            paths.append(self.lib_dir)

        if self.lib64_dir and os.path.isdir(self.lib64_dir):
            paths.append(self.lib64_dir)

        if self.lib32_dir and os.path.isdir(self.lib32_dir):
            paths.append(self.lib32_dir)

        if self.sysroot_lib and os.path.isdir(self.sysroot_lib):
            paths.append(self.sysroot_lib)

        # 常见库目录
        for lib_name in ["lib", "usr/lib", "usr/local/lib"]:
            lib_path = os.path.join(self.path, lib_name)
            if os.path.isdir(lib_path) and lib_path not in paths:
                paths.append(lib_path)

        return paths


class SysrootManager:
    """
    Sysroot 管理器

    负责检测和管理交叉编译所需的 sysroot。
    """

    def __init__(self):
        self.sysroots: Dict[str, Sysroot] = {}  # triple -> Sysroot
        self._explicit_sysroots: Dict[str, str] = {}  # triple -> path

    def set_sysroot(self, target_triple: str, path: str) -> None:
        """
        设置显式 sysroot

        Args:
            target_triple: 目标三元组
            path: sysroot 路径
        """
        if not os.path.isdir(path):
            raise SysrootError(f"Sysroot path does not exist: {path}")

        self._explicit_sysroots[target_triple] = path
        logger.info(f"Set sysroot for {target_triple}: {path}")

    def get_sysroot(self, target_triple: str) -> Optional[Sysroot]:
        """
        获取目标 sysroot

        Args:
            target_triple: 目标三元组

        Returns:
            Sysroot 对象，如果未找到返回 None
        """
        # 1. 检查显式设置的 sysroot
        if target_triple in self._explicit_sysroots:
            path = self._explicit_sysroots[target_triple]
            return self._create_sysroot(target_triple, path)

        # 2. 检查缓存
        if target_triple in self.sysroots:
            return self.sysroots[target_triple]

        # 3. 自动检测
        detected = self._auto_detect_sysroot(target_triple)
        if detected:
            self.sysroots[target_triple] = detected
            return detected

        return None

    def _create_sysroot(self, target_triple: str, path: str) -> Sysroot:
        """创建 Sysroot 对象"""
        try:
            target = TripleParser.parse(target_triple)
        except Exception:
            target = None

        if target is None:
            target = TargetTriple(
                arch=Architecture.UNKNOWN,
                vendor=Vendor.UNKNOWN,
                os=OperatingSystem.UNKNOWN,
                original=target_triple,
            )

        # 构建目录结构
        include_dir = os.path.join(path, "usr", "include")
        lib_dir = os.path.join(path, "lib")
        lib64_dir = os.path.join(path, "lib64")
        lib32_dir = os.path.join(path, "lib32")

        return Sysroot(
            path=path,
            target=target,
            include_dir=include_dir if os.path.isdir(include_dir) else "",
            lib_dir=lib_dir if os.path.isdir(lib_dir) else "",
            lib64_dir=lib64_dir if os.path.isdir(lib64_dir) else "",
            lib32_dir=lib32_dir if os.path.isdir(lib32_dir) else "",
            usr_dir=os.path.join(path, "usr"),
            bin_dir=os.path.join(path, "bin"),
            sysroot_include=os.path.join(path, "usr", "include", target_triple),
            sysroot_lib=os.path.join(path, "usr", "lib", target_triple),
        )

    def _auto_detect_sysroot(self, target_triple: str) -> Optional[Sysroot]:
        """自动检测 sysroot"""
        try:
            target = TripleParser.parse(target_triple)
        except Exception:
            return None

        system = target.os

        if system == OperatingSystem.LINUX:
            return self._detect_linux_sysroot(target)
        elif system == OperatingSystem.DARWIN:
            return self._detect_darwin_sysroot(target)
        elif system == OperatingSystem.ANDROID:
            return self._detect_android_sysroot(target)

        return None

    def _detect_linux_sysroot(self, target: TargetTriple) -> Optional[Sysroot]:
        """检测 Linux sysroot"""
        # 根据架构和厂商构建可能的路径
        arch_str = target.arch.name.lower()
        prefix = f"{arch_str}-unknown-linux"

        if target.environment and target.environment != EnvironmentType.UNKNOWN:
            prefix = (
                f"{arch_str}-{target.os.name.lower()}-{target.environment.name.lower()}"
            )

        common_paths = [
            f"/usr/{prefix}",
            f"/usr/{arch_str}-linux-gnu",
            f"/usr/{arch_str}-linux-musl",
            f"/opt/{prefix}",
            f"/opt/cross/{prefix}",
            f"/home/{prefix}",
        ]

        for path in common_paths:
            if os.path.isdir(path):
                return self._create_sysroot(str(target), path)

        return None

    def _detect_darwin_sysroot(self, target: TargetTriple) -> Optional[Sysroot]:
        """检测 macOS sysroot"""
        # 使用 xcrun 获取 SDK
        try:
            # 确定 SDK 类型
            if target.arch == Architecture.AARCH64:
                sdk = "iphoneos"
            elif target.arch == Architecture.I386:
                sdk = "iphonesimulator"
            else:
                sdk = "macosx"

            result = subprocess.run(
                ["xcrun", "--sdk", sdk, "--show-sdk-path"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                path = result.stdout.strip()
                if os.path.isdir(path):
                    return self._create_sysroot(str(target), path)
        except Exception:
            pass

        return None

    def _detect_android_sysroot(self, target: TargetTriple) -> Optional[Sysroot]:
        """检测 Android NDK sysroot"""
        # 查找 Android NDK
        ndk_paths = [
            os.environ.get("ANDROID_NDK_HOME"),
            os.environ.get("ANDROID_NDK_ROOT"),
            "/opt/android-ndk",
            "/usr/local/android-ndk",
            os.path.expanduser("~/Android/Sdk/ndk"),
        ]

        for ndk_path in ndk_paths:
            if not ndk_path:
                continue

            if not os.path.isdir(ndk_path):
                continue

            # 查找最新版本
            versions = []
            try:
                for item in os.listdir(ndk_path):
                    if item.startswith("r"):
                        versions.append(item)
            except Exception:
                pass

            if versions:
                # 使用最新版本
                latest = sorted(versions, key=lambda x: int(x[1:]))[-1]
                ndk_root = os.path.join(ndk_path, latest)

                # 构建 sysroot 路径
                arch_str = target.arch.name.lower()
                if arch_str == "arm":
                    arch = "armeabi-v7a"
                elif arch_str == "aarch64":
                    arch = "arm64-v8a"
                else:
                    arch = arch_str

                sysroot = os.path.join(ndk_root, "sysroot", arch)
                if os.path.isdir(sysroot):
                    return self._create_sysroot(str(target), sysroot)

        return None

    def find_library(
        self, target_triple: str, lib_name: str, lib_type: str = "shared"
    ) -> Optional[str]:
        """
        查找库文件

        Args:
            target_triple: 目标三元组
            lib_name: 库名称（不含 lib 前缀和扩展名）
            lib_type: 库类型（shared, static）

        Returns:
            库文件路径，如果未找到返回 None
        """
        sysroot = self.get_sysroot(target_triple)
        if not sysroot:
            return None

        # 构建可能的文件名
        if lib_type == "shared":
            extensions = [".so", ".dylib", ".dll"]
        else:
            extensions = [".a"]

        # 搜索库路径
        for lib_dir in sysroot.get_library_paths():
            for ext in extensions:
                lib_path = os.path.join(lib_dir, f"lib{lib_name}{ext}")
                if os.path.isfile(lib_path):
                    return lib_path

        return None

    def find_header(
        self, target_triple: str, header_name: str, subdir: str = ""
    ) -> Optional[str]:
        """
        查找头文件

        Args:
            target_triple: 目标三元组
            header_name: 头文件名称
            subdir: 子目录

        Returns:
            头文件路径，如果未找到返回 None
        """
        sysroot = self.get_sysroot(target_triple)
        if not sysroot:
            return None

        for include_dir in sysroot.get_include_paths():
            if subdir:
                header_path = os.path.join(include_dir, subdir, header_name)
            else:
                header_path = os.path.join(include_dir, header_name)

            if os.path.isfile(header_path):
                return header_path

            # 尝试在 include 的子目录中查找
            try:
                for item in os.listdir(include_dir):
                    item_path = os.path.join(include_dir, item, header_name)
                    if os.path.isfile(item_path):
                        return item_path
            except Exception:
                pass

        return None

    def get_available_sysroots(self) -> List[str]:
        """获取已检测的 sysroot 列表"""
        return list(self.sysroots.keys())


# 便捷函数
def get_sysroot(target_triple: str) -> Optional[Sysroot]:
    """
    获取目标 sysroot

    Args:
        target_triple: 目标三元组

    Returns:
        Sysroot 对象
    """
    manager = SysrootManager()
    return manager.get_sysroot(target_triple)


def find_library(target_triple: str, lib_name: str) -> Optional[str]:
    """
    查找库文件

    Args:
        target_triple: 目标三元组
        lib_name: 库名称

    Returns:
        库文件路径
    """
    manager = SysrootManager()
    return manager.find_library(target_triple, lib_name)


def find_header(target_triple: str, header_name: str) -> Optional[str]:
    """
    查找头文件

    Args:
        target_triple: 目标三元组
        header_name: 头文件名称

    Returns:
        头文件路径
    """
    manager = SysrootManager()
    return manager.find_header(target_triple, header_name)

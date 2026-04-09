# -*- coding: utf-8 -*-
"""
ZhC 工具链管理器

管理交叉编译工具链，包括 GCC、Clang、LLD 等工具的检测和配置。

作者：远
日期：2026-04-09
"""

import os
import shutil
import subprocess
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from .triple_parser import TargetTriple, TripleParser
from zhc.codegen.target_registry import (
    Architecture,
    OperatingSystem,
)

logger = logging.getLogger(__name__)


class ToolchainError(Exception):
    """工具链错误"""

    pass


@dataclass
class ToolInfo:
    """工具信息"""

    name: str  # 工具名称（gcc, clang, ld 等）
    path: str  # 工具路径
    version: Optional[str] = None  # 版本信息
    triple_prefix: Optional[str] = None  # 交叉编译前缀（如 arm-linux-gnueabihf-）

    def exists(self) -> bool:
        """检查工具是否存在"""
        return os.path.isfile(self.path) and os.access(self.path, os.X_OK)


@dataclass
class Toolchain:
    """
    工具链描述

    包含编译目标所需的完整工具链信息。
    """

    name: str  # 工具链名称
    target: TargetTriple  # 目标平台

    # 工具路径
    cc: Optional[ToolInfo] = None  # C 编译器
    cxx: Optional[ToolInfo] = None  # C++ 编译器
    linker: Optional[ToolInfo] = None  # 链接器
    assembler: Optional[ToolInfo] = None  # 汇编器
    ar: Optional[ToolInfo] = None  # 静态库打包器
    ranlib: Optional[ToolInfo] = None  # 索引生成器
    objcopy: Optional[ToolInfo] = None  # 对象复制
    objdump: Optional[ToolInfo] = None  # 对象转储

    # 路径信息
    sysroot: Optional[str] = None  # 系统根目录
    prefix: Optional[str] = None  # 工具前缀（如 /usr/bin/aarch64-linux-gnu-）

    # 元数据
    version: Optional[str] = None  # 工具链版本
    type: str = "unknown"  # 工具链类型（gcc, clang, msvc 等）
    is_builtin: bool = False  # 是否为内置 LLVM 工具链

    def has_compiler(self) -> bool:
        """是否有 C 编译器"""
        return self.cc is not None and self.cc.exists()

    def has_linker(self) -> bool:
        """是否有链接器"""
        return self.linker is not None and self.linker.exists()

    def get_tool(self, name: str) -> Optional[ToolInfo]:
        """获取指定工具"""
        tool_map = {
            "cc": self.cc,
            "cxx": self.cxx,
            "linker": self.linker,
            "as": self.assembler,
            "ar": self.ar,
            "ranlib": self.ranlib,
            "objcopy": self.objcopy,
            "objdump": self.objdump,
        }
        return tool_map.get(name)


class ToolchainManager:
    """
    工具链管理器

    负责检测和管理编译工具链，支持本机编译和交叉编译。
    """

    def __init__(self):
        self.toolchains: Dict[str, Toolchain] = {}  # triple -> Toolchain
        self._llvm_available: Optional[bool] = None

    def detect_toolchain(self, target_triple: str) -> Optional[Toolchain]:
        """
        检测目标工具链

        Args:
            target_triple: 目标三元组

        Returns:
            工具链对象，如果未找到返回 None
        """
        # 1. 检查缓存
        if target_triple in self.toolchains:
            return self.toolchains[target_triple]

        # 2. 解析目标
        try:
            target = TripleParser.parse(target_triple)
        except Exception:
            return None

        # 3. 检测工具链
        toolchain = self._detect_toolchain(target)

        # 4. 缓存结果
        if toolchain:
            self.toolchains[target_triple] = toolchain

        return toolchain

    def register_toolchain(self, target_triple: str, toolchain: Toolchain) -> None:
        """
        注册工具链

        Args:
            target_triple: 目标三元组
            toolchain: 工具链对象
        """
        self.toolchains[target_triple] = toolchain
        logger.info(f"Registered toolchain for {target_triple}")

    def _detect_toolchain(self, target: TargetTriple) -> Optional[Toolchain]:
        """检测目标工具链"""
        # 1. 检查是否为内置 LLVM 工具链
        if self._has_builtin_llvm():
            return self._create_builtin_toolchain(target)

        # 2. 检查系统工具链
        system_toolchain = self._detect_system_toolchain(target)
        if system_toolchain:
            return system_toolchain

        # 3. 检查 PATH 中的工具
        path_toolchain = self._detect_path_toolchain(target)
        if path_toolchain:
            return path_toolchain

        return None

    def _has_builtin_llvm(self) -> bool:
        """检查内置 LLVM 工具链是否可用"""
        if self._llvm_available is not None:
            return self._llvm_available

        # 检查 llc 是否可用
        self._llvm_available = shutil.which("llc") is not None
        return self._llvm_available

    def _create_builtin_toolchain(self, target: TargetTriple) -> Toolchain:
        """创建内置 LLVM 工具链"""
        return Toolchain(
            name=f"llvm-{target.original}",
            target=target,
            type="llvm",
            is_builtin=True,
            cc=ToolInfo(
                name="clang",
                path=shutil.which("clang") or "",
                version=self._get_llvm_version(),
            ),
            linker=ToolInfo(
                name="lld",
                path=self._get_lld_path(target),
                version=self._get_llvm_version(),
            ),
            assembler=ToolInfo(
                name="llvm-as",
                path=shutil.which("llvm-as") or "",
            ),
        )

    def _detect_system_toolchain(self, target: TargetTriple) -> Optional[Toolchain]:
        """检测系统工具链"""
        system = target.os

        if system == OperatingSystem.LINUX:
            return self._detect_linux_toolchain(target)
        elif system == OperatingSystem.DARWIN:
            return self._detect_darwin_toolchain(target)
        elif system == OperatingSystem.WINDOWS:
            return self._detect_windows_toolchain(target)

        return None

    def _detect_linux_toolchain(self, target: TargetTriple) -> Optional[Toolchain]:
        """检测 Linux 工具链"""
        prefix = self._get_cross_compile_prefix(target)

        # 检查交叉编译工具链
        if not shutil.which(f"{prefix}-gcc"):
            return None

        # 获取工具路径
        base_path = shutil.which(f"{prefix}-gcc").rsplit("/", 1)[0]
        prefix_path = f"{base_path}/{prefix}-"

        tools = {
            "cc": f"{prefix_path}gcc",
            "cxx": f"{prefix_path}g++",
            "linker": f"{prefix_path}ld",
            "assembler": f"{prefix_path}as",
            "ar": f"{prefix_path}ar",
            "ranlib": f"{prefix_path}ranlib",
        }

        # 验证工具存在
        for tool_path in tools.values():
            if not os.path.isfile(tool_path):
                continue

        # 获取版本
        version = self._get_gcc_version(tools["cc"])

        # 获取 sysroot
        sysroot = self._detect_linux_sysroot(target, prefix)

        return Toolchain(
            name=f"{prefix}-toolchain",
            target=target,
            type="gcc",
            cc=ToolInfo("gcc", tools["cc"], version, prefix),
            cxx=ToolInfo("g++", tools["cxx"], version, prefix),
            linker=ToolInfo("ld", tools["linker"], version, prefix),
            assembler=ToolInfo("as", tools["assembler"], version, prefix),
            ar=ToolInfo("ar", tools["ar"], version, prefix),
            ranlib=ToolInfo("ranlib", tools["ranlib"], version, prefix),
            sysroot=sysroot,
            prefix=prefix_path,
            version=version,
        )

    def _detect_darwin_toolchain(self, target: TargetTriple) -> Optional[Toolchain]:
        """检测 macOS 工具链（使用 Xcode）"""
        # 检查 Xcode 是否安装
        if not shutil.which("xcrun"):
            return None

        # 获取 SDK 路径
        sdk_path = self._get_xcode_sdk_path(target)

        # 检查 clang
        clang_path = shutil.which("clang")
        if not clang_path:
            return None

        version = self._get_clang_version(clang_path)

        return Toolchain(
            name="xcode-toolchain",
            target=target,
            type="clang",
            cc=ToolInfo("clang", clang_path, version),
            cxx=ToolInfo("clang++", clang_path.replace("clang", "clang++"), version),
            linker=ToolInfo("ld", shutil.which("ld") or "", version),
            assembler=ToolInfo("as", shutil.which("as") or ""),
            ar=ToolInfo("ar", shutil.which("ar") or ""),
            sysroot=sdk_path,
            version=version,
        )

    def _detect_windows_toolchain(self, target: TargetTriple) -> Optional[Toolchain]:
        """检测 Windows 工具链"""
        # 检查 MSVC
        msvc_path = self._detect_msvc_path()
        if msvc_path:
            return self._create_msvc_toolchain(target, msvc_path)

        # 检查 MinGW
        mingw_path = self._detect_mingw_path(target)
        if mingw_path:
            return self._create_mingw_toolchain(target, mingw_path)

        return None

    def _detect_path_toolchain(self, target: TargetTriple) -> Optional[Toolchain]:
        """检测 PATH 中的工具链"""
        # 尝试直接检测 clang/gcc
        cc_path = shutil.which("clang") or shutil.which("gcc")
        if not cc_path:
            return None

        version = self._get_gcc_version(cc_path) or self._get_clang_version(cc_path)

        return Toolchain(
            name="system-toolchain",
            target=target,
            type="clang" if "clang" in cc_path else "gcc",
            cc=ToolInfo("cc", cc_path, version),
            cxx=ToolInfo(
                "cxx",
                cc_path.replace("clang", "clang++").replace("gcc", "g++"),
                version,
            ),
            linker=ToolInfo(
                "ld",
                shutil.which("ld") or "",
                version,
            ),
        )

    def _get_cross_compile_prefix(self, target: TargetTriple) -> str:
        """获取交叉编译前缀"""
        arch_str = target.arch.name.lower()

        # 特殊处理
        if target.os == OperatingSystem.LINUX:
            if target.arch == Architecture.ARM:
                return f"{arch_str}-linux-gnueabihf"
            return f"{arch_str}-unknown-linux-gnu"
        elif target.os == OperatingSystem.DARWIN:
            return f"{arch_str}-apple-darwin"

        return f"{arch_str}-unknown-linux"

    def _detect_linux_sysroot(self, target: TargetTriple, prefix: str) -> Optional[str]:
        """检测 Linux sysroot"""
        common_paths = [
            f"/usr/{prefix}",
            f"/opt/{prefix}",
            f"/usr/local/{prefix}",
        ]

        for path in common_paths:
            if os.path.isdir(path):
                return path

        return None

    def _get_xcode_sdk_path(self, target: TargetTriple) -> str:
        """获取 Xcode SDK 路径"""
        try:
            # 检测 SDK 类型
            if target.os == OperatingSystem.DARWIN:
                if target.arch == Architecture.AARCH64:
                    sdk = "iphoneos"
                else:
                    sdk = "macosx"
            else:
                sdk = "macosx"

            result = subprocess.run(
                ["xcrun", "--sdk", sdk, "--show-sdk-path"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return ""

    def _detect_msvc_path(self) -> Optional[str]:
        """检测 MSVC 安装路径"""
        # 使用 vswhere 查找
        try:
            result = subprocess.run(
                ["vswhere", "-latest", "-property", "installationPath"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass

        return None

    def _detect_mingw_path(self, target: TargetTriple) -> Optional[str]:
        """检测 MinGW 路径"""
        mingw_paths = [
            "C:/msys64/mingw64",
            "C:/msys64/mingw32",
            "C:/MinGW",
            "/usr/x86_64-w64-mingw32",
            "/usr/i686-w64-mingw32",
        ]

        for path in mingw_paths:
            if os.path.isdir(path):
                return path

        return None

    def _create_msvc_toolchain(self, target: TargetTriple, vs_path: str) -> Toolchain:
        """创建 MSVC 工具链"""
        return Toolchain(
            name="msvc-toolchain",
            target=target,
            type="msvc",
            sysroot=vs_path,
        )

    def _create_mingw_toolchain(
        self, target: TargetTriple, mingw_path: str
    ) -> Toolchain:
        """创建 MinGW 工具链"""
        return Toolchain(
            name="mingw-toolchain",
            target=target,
            type="mingw",
            cc=ToolInfo("gcc", f"{mingw_path}/bin/gcc.exe"),
            cxx=ToolInfo("g++", f"{mingw_path}/bin/g++.exe"),
            linker=ToolInfo("ld", f"{mingw_path}/bin/ld.exe"),
            sysroot=mingw_path,
        )

    def _get_lld_path(self, target: TargetTriple) -> str:
        """获取 LLD 链接器路径"""
        system = target.os

        # 根据操作系统选择 LLD 变体
        if system == OperatingSystem.LINUX:
            return shutil.which("ld.lld") or shutil.which("lld")
        elif system == OperatingSystem.DARWIN:
            return shutil.which("ld64.lld") or shutil.which("lld")
        elif system == OperatingSystem.WINDOWS:
            return shutil.which("lld-link") or shutil.which("lld")
        else:
            return shutil.which("lld") or ""

    def _get_llvm_version(self) -> Optional[str]:
        """获取 LLVM 版本"""
        try:
            result = subprocess.run(
                ["llc", "--version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                # 提取版本号
                import re

                match = re.search(r"version\s+(\d+\.\d+\.\d+)", result.stdout)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return None

    def _get_clang_version(self, clang_path: str) -> Optional[str]:
        """获取 Clang 版本"""
        try:
            result = subprocess.run(
                [clang_path, "--version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                # 提取版本号
                import re

                match = re.search(r"version\s+(\d+\.\d+\.\d+)", result.stdout)
                if match:
                    return match.group(1)
                # clang 格式
                match = re.search(r"clang\s+(\d+\.\d+\.\d+)", result.stdout)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return None

    def _get_gcc_version(self, gcc_path: str) -> Optional[str]:
        """获取 GCC 版本"""
        try:
            result = subprocess.run(
                [gcc_path, "--version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                import re

                match = re.search(r"gcc\s+version\s+(\d+\.\d+\.\d+)", result.stdout)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return None

    def get_available_toolchains(self) -> List[str]:
        """获取可用工具链列表"""
        return list(self.toolchains.keys())


# 便捷函数
def detect_toolchain(target_triple: str) -> Optional[Toolchain]:
    """
    检测目标工具链

    Args:
        target_triple: 目标三元组

    Returns:
        工具链对象
    """
    manager = ToolchainManager()
    return manager.detect_toolchain(target_triple)

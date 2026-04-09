# -*- coding: utf-8 -*-
"""
ZhC 链接器管理器

管理交叉编译所需的链接器，包括 LLD、GNU ld、平台特定链接器等。
支持链接器检测、选择和命令生成。

作者：远
日期：2026-04-09
"""

import os
import shutil
import subprocess
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum, auto

from .triple_parser import TargetTriple
from zhc.codegen.target_registry import (
    Architecture,
    OperatingSystem,
)

logger = logging.getLogger(__name__)


class LinkerType(Enum):
    """链接器类型"""

    LLD = auto()  # LLVM 链接器
    GNU_LD = auto()  # GNU ld
    LD64 = auto()  # macOS ld64
    LLD_LINK = auto()  # Windows lld-link
    MSVC_LINK = auto()  # MSVC link.exe
    GOLD = auto()  # GNU gold
    BFD = auto()  # GNU ld (BFD)


@dataclass
class LinkerInfo:
    """链接器信息"""

    name: str  # 链接器名称
    path: str  # 链接器路径
    type: LinkerType  # 链接器类型
    version: Optional[str] = None  # 版本信息
    cross_platform: bool = False  # 是否支持跨平台
    supported_platforms: List[OperatingSystem] = field(default_factory=list)

    def exists(self) -> bool:
        """检查链接器是否存在"""
        return (
            bool(self.path)
            and os.path.isfile(self.path)
            and os.access(self.path, os.X_OK)
        )


class LinkerError(Exception):
    """链接器错误"""

    pass


class LinkerManager:
    """
    链接器管理器

    负责检测、选择和配置链接器，支持多种链接器后端。
    """

    # 支持的链接器配置
    LINKER_CONFIGS = {
        "lld": {
            "type": LinkerType.LLD,
            "cross_platform": True,
            "commands": {
                OperatingSystem.LINUX: ["ld.lld", "lld"],
                OperatingSystem.DARWIN: ["ld64.lld", "lld"],
                OperatingSystem.WINDOWS: ["lld-link", "lld.exe"],
            },
        },
        "gnu_ld": {
            "type": LinkerType.GNU_LD,
            "cross_platform": False,
            "commands": {
                OperatingSystem.LINUX: ["ld", "ld.bfd"],
                OperatingSystem.DARWIN: [],
                OperatingSystem.WINDOWS: [],
            },
        },
        "gold": {
            "type": LinkerType.GOLD,
            "cross_platform": False,
            "commands": {
                OperatingSystem.LINUX: ["ld.gold"],
                OperatingSystem.DARWIN: [],
                OperatingSystem.WINDOWS: [],
            },
        },
        "ld64": {
            "type": LinkerType.LD64,
            "cross_platform": False,
            "commands": {
                OperatingSystem.LINUX: [],
                OperatingSystem.DARWIN: ["ld"],
                OperatingSystem.WINDOWS: [],
            },
        },
        "msvc_link": {
            "type": LinkerType.MSVC_LINK,
            "cross_platform": False,
            "commands": {
                OperatingSystem.LINUX: [],
                OperatingSystem.DARWIN: [],
                OperatingSystem.WINDOWS: ["link.exe"],
            },
        },
    }

    def __init__(self):
        self._linkers: Dict[str, LinkerInfo] = {}  # 缓存检测到的链接器
        self._preferred_linker: Optional[str] = None  # 首选链接器

    def detect_linker(
        self, target: TargetTriple, linker_name: Optional[str] = None
    ) -> Optional[LinkerInfo]:
        """
        检测适合目标的链接器

        Args:
            target: 目标三元组
            linker_name: 指定链接器名称（可选）

        Returns:
            链接器信息，如果未找到返回 None
        """
        # 如果指定了链接器名称
        if linker_name:
            return self._find_specific_linker(linker_name, target)

        # 优先使用 LLD（跨平台支持）
        lld_linker = self._detect_lld(target)
        if lld_linker:
            return lld_linker

        # 检测平台默认链接器
        return self._detect_platform_linker(target)

    def _detect_lld(self, target: TargetTriple) -> Optional[LinkerInfo]:
        """检测 LLD 链接器"""
        config = self.LINKER_CONFIGS["lld"]
        commands = config["commands"].get(target.os, [])

        for cmd in commands:
            path = shutil.which(cmd)
            if path:
                version = self._get_linker_version(path, LinkerType.LLD)
                return LinkerInfo(
                    name=cmd,
                    path=path,
                    type=LinkerType.LLD,
                    version=version,
                    cross_platform=True,
                    supported_platforms=list(config["commands"].keys()),
                )

        return None

    def _detect_platform_linker(self, target: TargetTriple) -> Optional[LinkerInfo]:
        """检测平台默认链接器"""
        os_type = target.os

        # Linux: 优先 gold，然后 GNU ld
        if os_type == OperatingSystem.LINUX:
            for linker_name in ["gold", "gnu_ld"]:
                config = self.LINKER_CONFIGS[linker_name]
                commands = config["commands"].get(os_type, [])
                for cmd in commands:
                    path = shutil.which(cmd)
                    if path:
                        version = self._get_linker_version(path, config["type"])
                        return LinkerInfo(
                            name=cmd,
                            path=path,
                            type=config["type"],
                            version=version,
                            cross_platform=config["cross_platform"],
                            supported_platforms=[os_type],
                        )

        # macOS: 使用 ld64
        elif os_type == OperatingSystem.DARWIN:
            config = self.LINKER_CONFIGS["ld64"]
            commands = config["commands"].get(os_type, [])
            for cmd in commands:
                path = shutil.which(cmd)
                if path:
                    return LinkerInfo(
                        name=cmd,
                        path=path,
                        type=LinkerType.LD64,
                        cross_platform=False,
                        supported_platforms=[os_type],
                    )

        # Windows: 使用 MSVC link
        elif os_type == OperatingSystem.WINDOWS:
            config = self.LINKER_CONFIGS["msvc_link"]
            commands = config["commands"].get(os_type, [])
            for cmd in commands:
                path = shutil.which(cmd)
                if path:
                    return LinkerInfo(
                        name=cmd,
                        path=path,
                        type=LinkerType.MSVC_LINK,
                        cross_platform=False,
                        supported_platforms=[os_type],
                    )

        return None

    def _find_specific_linker(
        self, linker_name: str, target: TargetTriple
    ) -> Optional[LinkerInfo]:
        """查找指定的链接器"""
        # 在 PATH 中查找
        path = shutil.which(linker_name)
        if path:
            linker_type = self._identify_linker_type(path)
            return LinkerInfo(
                name=linker_name,
                path=path,
                type=linker_type,
                supported_platforms=[target.os],
            )

        return None

    def _identify_linker_type(self, path: str) -> LinkerType:
        """识别链接器类型"""
        basename = os.path.basename(path).lower()

        if "lld" in basename:
            if "link" in basename:
                return LinkerType.LLD_LINK
            return LinkerType.LLD
        elif "gold" in basename:
            return LinkerType.GOLD
        elif "bfd" in basename:
            return LinkerType.BFD
        elif "link" in basename:
            return LinkerType.MSVC_LINK
        elif "ld64" in basename:
            return LinkerType.LD64
        else:
            return LinkerType.GNU_LD

    def _get_linker_version(self, path: str, linker_type: LinkerType) -> Optional[str]:
        """获取链接器版本"""
        try:
            # LLD 版本获取
            if linker_type in (LinkerType.LLD, LinkerType.LLD_LINK):
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    import re

                    match = re.search(r"LLD\s+(\d+\.\d+\.\d+)", result.stdout)
                    if match:
                        return match.group(1)

            # GNU ld 版本获取
            elif linker_type in (LinkerType.GNU_LD, LinkerType.GOLD, LinkerType.BFD):
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    import re

                    match = re.search(r"GNU ld[^\d]*?(\d+\.\d+)", result.stdout)
                    if match:
                        return match.group(1)

        except Exception:
            pass

        return None

    def generate_link_command(
        self,
        target: TargetTriple,
        objects: List[str],
        output: str,
        sysroot: Optional[str] = None,
        libraries: Optional[List[str]] = None,
        library_paths: Optional[List[str]] = None,
        link_type: str = "dynamic",
        entry_point: Optional[str] = None,
        extra_flags: Optional[List[str]] = None,
    ) -> List[str]:
        """
        生成链接命令

        Args:
            target: 目标三元组
            objects: 目标文件列表
            output: 输出文件路径
            sysroot: sysroot 路径
            libraries: 需要链接的库列表
            library_paths: 库搜索路径列表
            link_type: 链接类型（dynamic, static）
            entry_point: 入口点
            extra_flags: 额外标志

        Returns:
            链接命令列表
        """
        linker = self.detect_linker(target)
        if not linker:
            raise LinkerError(f"No linker found for target: {target}")

        cmd = [linker.path]

        # 添加目标特定选项
        if linker.type == LinkerType.LLD or linker.type == LinkerType.GNU_LD:
            cmd.append(f"--target={target.original}")

        # Sysroot
        if sysroot:
            if linker.type in (LinkerType.LLD, LinkerType.LLD_LINK):
                cmd.extend(["--sysroot", sysroot])
            else:
                cmd.extend(["--sysroot", sysroot])

        # 链接类型
        if link_type == "static":
            if linker.type in (LinkerType.LLD, LinkerType.GNU_LD, LinkerType.GOLD):
                cmd.append("-static")

        # 动态链接器（Linux）
        if target.os == OperatingSystem.LINUX and link_type == "dynamic":
            dynamic_linker = self._get_dynamic_linker(target)
            if dynamic_linker:
                if linker.type in (LinkerType.LLD, LinkerType.GNU_LD):
                    cmd.extend(["-dynamic-linker", dynamic_linker])

        # 入口点
        if entry_point:
            if linker.type in (LinkerType.LLD, LinkerType.GNU_LD):
                cmd.extend(["-e", entry_point])
            elif linker.type == LinkerType.LD64:
                cmd.extend(["-e", entry_point])

        # 库路径
        if library_paths:
            for path in library_paths:
                if linker.type in (LinkerType.LLD, LinkerType.GNU_LD, LinkerType.GOLD):
                    cmd.extend(["-L", path])
                elif linker.type == LinkerType.LD64:
                    cmd.extend(["-L", path])

        # 目标文件
        cmd.extend(objects)

        # 输出文件
        cmd.extend(["-o", output])

        # 库
        if libraries:
            for lib in libraries:
                cmd.extend(["-l", lib])

        # 额外标志
        if extra_flags:
            cmd.extend(extra_flags)

        return cmd

    def _get_dynamic_linker(self, target: TargetTriple) -> Optional[str]:
        """获取动态链接器路径"""
        dynamic_linkers = {
            Architecture.X86_64: "/lib64/ld-linux-x86-64.so.2",
            Architecture.I386: "/lib/ld-linux.so.2",
            Architecture.AARCH64: "/lib/ld-linux-aarch64.so.1",
            Architecture.ARM: "/lib/ld-linux-armhf.so.3",
            Architecture.RISCV64: "/lib/ld-linux-riscv64-lp64d.so.1",
            Architecture.RISCV32: "/lib/ld-linux-riscv32-ilp32d.so.1",
        }
        return dynamic_linkers.get(target.arch)

    def get_linker_info(self, target: TargetTriple) -> Optional[LinkerInfo]:
        """获取链接器信息"""
        return self.detect_linker(target)

    def list_available_linkers(self, target: TargetTriple) -> List[LinkerInfo]:
        """列出可用的链接器"""
        available = []

        for linker_name, config in self.LINKER_CONFIGS.items():
            commands = config["commands"].get(target.os, [])
            for cmd in commands:
                path = shutil.which(cmd)
                if path:
                    available.append(
                        LinkerInfo(
                            name=cmd,
                            path=path,
                            type=config["type"],
                            cross_platform=config["cross_platform"],
                            supported_platforms=[target.os],
                        )
                    )

        return available


# 便捷函数
def get_linker(target: TargetTriple) -> Optional[LinkerInfo]:
    """
    获取目标链接器

    Args:
        target: 目标三元组

    Returns:
        链接器信息
    """
    manager = LinkerManager()
    return manager.detect_linker(target)


def generate_link_command(
    target: TargetTriple, objects: List[str], output: str, **kwargs
) -> List[str]:
    """
    生成链接命令

    Args:
        target: 目标三元组
        objects: 目标文件列表
        output: 输出文件路径
        **kwargs: 其他参数

    Returns:
        链接命令列表
    """
    manager = LinkerManager()
    return manager.generate_link_command(target, objects, output, **kwargs)

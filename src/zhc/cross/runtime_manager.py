# -*- coding: utf-8 -*-
"""
ZhC 运行时管理器

管理交叉编译所需的运行时库，包括 C 运行时（CRT）、标准库、平台特定运行时等。
支持 glibc、musl、MSVC、SDK 运行时等。

作者：远
日期：2026-04-09
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum, auto

from .triple_parser import TargetTriple, TripleParser
from zhc.codegen.target_registry import (
    OperatingSystem,
    EnvironmentType,
)

logger = logging.getLogger(__name__)


class RuntimeType(Enum):
    """运行时类型"""

    GLIBC = auto()  # GNU glibc
    MUSL = auto()  # musl libc
    UCLIBC = auto()  # uClibc
    MSVC = auto()  # MSVC C 运行时
    UCRT = auto()  # Windows UCRT
    BIONIC = auto()  # Android Bionic
    newlib = auto()  # newlib (嵌入式)
    Picolib = auto()  # Picolib (嵌入式)
    WASM = auto()  # WebAssembly 运行时


@dataclass
class CRTRuntime:
    """C 运行时（CRT）配置"""

    name: str  # 运行时名称
    type: RuntimeType  # 运行时类型
    link_type: str = "dynamic"  # 链接类型

    # CRT 启动文件
    crt_start_files: List[str] = field(default_factory=list)
    crt_end_files: List[str] = field(default_factory=list)
    crt_init_files: List[str] = field(default_factory=list)
    crt_fini_files: List[str] = field(default_factory=list)

    # 静态/动态运行时
    static_runtime: str = ""  # 静态运行时库
    dynamic_runtime: str = ""  # 动态运行时库
    shared_runtime: str = ""  # 共享运行时库

    # 路径
    include_path: str = ""  # 头文件路径
    library_path: str = ""  # 库文件路径

    def get_crt_files(self) -> List[str]:
        """获取 CRT 文件列表"""
        files = []
        files.extend(self.crt_start_files)
        files.extend(self.crt_init_files)
        files.extend(self.crt_fini_files)
        files.extend(self.crt_end_files)
        return files


@dataclass
class RuntimeLibrary:
    """运行时库配置"""

    name: str  # 库名称
    type: RuntimeType  # 运行时类型
    target: TargetTriple  # 目标平台

    # 库文件
    libraries: List[str] = field(default_factory=list)
    system_libs: List[str] = field(default_factory=list)

    # CRT 配置
    crt: Optional[CRTRuntime] = None

    # 路径
    sysroot: Optional[str] = None
    include_path: str = ""
    library_path: str = ""

    # 特性
    features: Set[str] = field(default_factory=set)
    cxx_support: bool = True  # 是否支持 C++

    def get_linker_args(self) -> List[str]:
        """获取链接器参数"""
        args = []

        # 添加 CRT 文件
        if self.crt:
            for lib in self.crt.get_crt_files():
                if lib.endswith(".o") or lib.endswith(".obj"):
                    args.append(lib)

        # 添加库
        for lib in self.libraries:
            args.extend(["-l", lib])

        # 添加系统库
        for lib in self.system_libs:
            args.extend(["-l", lib])

        return args


class RuntimeError(Exception):
    """运行时错误"""

    pass


class RuntimeManager:
    """
    运行时管理器

    负责检测和管理交叉编译所需的运行时库。
    """

    def __init__(self):
        self._runtimes: Dict[str, RuntimeLibrary] = {}  # triple -> RuntimeLibrary
        self._explicit_runtimes: Dict[str, RuntimeLibrary] = {}  # 显式指定的运行时

    def get_runtime(
        self, target_triple: str, runtime_type: Optional[str] = None
    ) -> Optional[RuntimeLibrary]:
        """
        获取目标运行时库

        Args:
            target_triple: 目标三元组
            runtime_type: 运行时类型（如 "glibc", "musl", "msvc"）

        Returns:
            运行时库配置
        """
        # 1. 检查显式指定的运行时
        if target_triple in self._explicit_runtimes:
            return self._explicit_runtimes[target_triple]

        # 2. 检查缓存
        key = f"{target_triple}:{runtime_type or 'default'}"
        if key in self._runtimes:
            return self._runtimes[key]

        # 3. 检测运行时
        detected = self._detect_runtime(target_triple, runtime_type)
        if detected:
            self._runtimes[key] = detected
            return detected

        return None

    def set_runtime(self, target_triple: str, runtime: RuntimeLibrary) -> None:
        """
        设置显式运行时

        Args:
            target_triple: 目标三元组
            runtime: 运行时库配置
        """
        self._explicit_runtimes[target_triple] = runtime
        logger.info(f"Set runtime for {target_triple}: {runtime.name}")

    def _detect_runtime(
        self, target_triple: str, runtime_type: Optional[str] = None
    ) -> Optional[RuntimeLibrary]:
        """检测运行时库"""
        try:
            target = TripleParser.parse(target_triple)
        except Exception:
            return None

        os_type = target.os

        if os_type == OperatingSystem.LINUX:
            return self._detect_linux_runtime(target, runtime_type)
        elif os_type == OperatingSystem.DARWIN:
            return self._detect_darwin_runtime(target)
        elif os_type == OperatingSystem.WINDOWS:
            return self._detect_windows_runtime(target, runtime_type)
        elif os_type == OperatingSystem.ANDROID:
            return self._detect_android_runtime(target)
        elif os_type in (OperatingSystem.UNKNOWN, OperatingSystem.EMSCRIPTEN):
            if target.is_wasm:
                return self._detect_wasm_runtime(target)

        return self._get_minimal_runtime(target)

    def _detect_linux_runtime(
        self, target: TargetTriple, runtime_type: Optional[str] = None
    ) -> RuntimeLibrary:
        """检测 Linux 运行时"""
        # 判断运行时类型
        if target.environment:
            if target.environment == EnvironmentType.MUSL:
                return self._get_musl_runtime(target)
            elif target.environment in (EnvironmentType.GNUABI,):
                return self._get_glibc_runtime(target)

        # 从 sysroot 检测
        sysroot = self._detect_sysroot_runtime(target)
        if sysroot:
            return sysroot

        # 默认使用 glibc
        return self._get_glibc_runtime(target)

    def _get_glibc_runtime(self, target: TargetTriple) -> RuntimeLibrary:
        """获取 glibc 运行时配置"""
        crt = CRTRuntime(
            name="glibc",
            type=RuntimeType.GLIBC,
            crt_start_files=["crt1.o", "rcrt1.o"],
            crt_init_files=["crti.o"],
            crt_fini_files=["crtn.o"],
            static_runtime="crt1.o",
            dynamic_runtime="",
            library_path="/lib",
        )

        return RuntimeLibrary(
            name="glibc",
            type=RuntimeType.GLIBC,
            target=target,
            libraries=["c", "m", "pthread", "dl", "rt"],
            system_libs=["gcc", "gcc_s"],
            crt=crt,
            features={"threading", "dynamic_linker", "locale"},
            cxx_support=True,
        )

    def _get_musl_runtime(self, target: TargetTriple) -> RuntimeLibrary:
        """获取 musl 运行时配置"""
        crt = CRTRuntime(
            name="musl",
            type=RuntimeType.MUSL,
            crt_start_files=["crt1.o"],
            crt_init_files=["crti.o"],
            crt_fini_files=["crtn.o"],
            static_runtime="crt1.o",
            library_path="/lib",
        )

        return RuntimeLibrary(
            name="musl",
            type=RuntimeType.MUSL,
            target=target,
            libraries=["c", "m", "pthread", "dl"],
            crt=crt,
            features={"static_linking", "threading"},
            cxx_support=True,
        )

    def _detect_darwin_runtime(self, target: TargetTriple) -> RuntimeLibrary:
        """检测 macOS 运行时"""
        # macOS 使用系统运行时，不需要显式配置 CRT
        return RuntimeLibrary(
            name="darwin-sdk",
            type=RuntimeType.GLIBC,  # 复用类型
            target=target,
            libraries=["System", "m"],
            system_libs=["gcc"],
            features={"sdk", "framework"},
            cxx_support=True,
        )

    def _detect_windows_runtime(
        self, target: TargetTriple, runtime_type: Optional[str] = None
    ) -> RuntimeLibrary:
        """检测 Windows 运行时"""
        # 检测 MSVC 或 MinGW
        if runtime_type == "mingw":
            return self._get_mingw_runtime(target)
        else:
            return self._get_msvc_runtime(target)

    def _get_msvc_runtime(self, target: TargetTriple) -> RuntimeLibrary:
        """获取 MSVC 运行时配置"""
        crt = CRTRuntime(
            name="msvc",
            type=RuntimeType.MSVC,
            static_runtime="libcmt.lib",
            dynamic_runtime="msvcrt.lib",
            library_path="",
        )

        return RuntimeLibrary(
            name="msvc",
            type=RuntimeType.MSVC,
            target=target,
            libraries=["kernel32", "user32", "gdi32", "msvcrt"],
            crt=crt,
            features={"dll_import", "seh"},
            cxx_support=True,
        )

    def _get_mingw_runtime(self, target: TargetTriple) -> RuntimeLibrary:
        """获取 MinGW 运行时配置"""
        crt = CRTRuntime(
            name="mingw",
            type=RuntimeType.UCRT,
            crt_start_files=["crt1.o"],
            crt_init_files=["crt2.o"],
            crt_fini_files=["crtend.o"],
            static_runtime="crt1.o",
            library_path="/lib",
        )

        return RuntimeLibrary(
            name="mingw",
            type=RuntimeType.UCRT,
            target=target,
            libraries=["mingw32", "m", "gcc", "msvcrt"],
            crt=crt,
            features={"dll_import", "windows"},
            cxx_support=True,
        )

    def _detect_android_runtime(self, target: TargetTriple) -> RuntimeLibrary:
        """检测 Android 运行时（Bionic）"""
        crt = CRTRuntime(
            name="bionic",
            type=RuntimeType.BIONIC,
            crt_start_files=["crtbegin_so.o", "crtend_so.o"],
            crt_init_files=["crti.o"],
            crt_fini_files=["crtn.o"],
            library_path="/system/lib",
        )

        return RuntimeLibrary(
            name="bionic",
            type=RuntimeType.BIONIC,
            target=target,
            libraries=["c", "m", "log", "android"],
            crt=crt,
            features={"JNI", "hardware"},
            cxx_support=True,
        )

    def _detect_wasm_runtime(self, target: TargetTriple) -> RuntimeLibrary:
        """检测 WebAssembly 运行时"""
        return RuntimeLibrary(
            name="wasm-sdk",
            type=RuntimeType.WASM,
            target=target,
            libraries=["c", "m"],
            features={"minimal", "no_exit"},
            cxx_support=True,
        )

    def _get_minimal_runtime(self, target: TargetTriple) -> RuntimeLibrary:
        """获取最小运行时（用于嵌入式等）"""
        crt = CRTRuntime(
            name="minimal",
            type=RuntimeType.newlib,
            library_path="",
        )

        return RuntimeLibrary(
            name="minimal",
            type=RuntimeType.newlib,
            target=target,
            libraries=["c"],
            crt=crt,
            features={"minimal"},
            cxx_support=False,
        )

    def _detect_sysroot_runtime(self, target: TargetTriple) -> Optional[RuntimeLibrary]:
        """从 sysroot 检测运行时"""
        # 简化实现，实际应检查 sysroot 中的 libc 类型
        return None

    def get_crt_files(
        self, target_triple: str, link_type: str = "dynamic"
    ) -> List[str]:
        """
        获取 CRT 文件列表

        Args:
            target_triple: 目标三元组
            link_type: 链接类型

        Returns:
            CRT 文件列表
        """
        runtime = self.get_runtime(target_triple)
        if runtime and runtime.crt:
            return runtime.crt.get_crt_files()
        return []

    def get_library_link_args(
        self, target_triple: str, runtime_type: Optional[str] = None
    ) -> List[str]:
        """
        获取库链接参数

        Args:
            target_triple: 目标三元组
            runtime_type: 运行时类型

        Returns:
            链接器参数列表
        """
        runtime = self.get_runtime(target_triple, runtime_type)
        if runtime:
            return runtime.get_linker_args()
        return []

    def get_available_runtimes(self) -> List[str]:
        """获取可用运行时列表"""
        return list(self._runtimes.keys())


# 便捷函数
def get_runtime(
    target_triple: str, runtime_type: Optional[str] = None
) -> Optional[RuntimeLibrary]:
    """
    获取目标运行时库

    Args:
        target_triple: 目标三元组
        runtime_type: 运行时类型

    Returns:
        运行时库配置
    """
    manager = RuntimeManager()
    return manager.get_runtime(target_triple, runtime_type)


def get_crt_files(target_triple: str, link_type: str = "dynamic") -> List[str]:
    """
    获取 CRT 文件列表

    Args:
        target_triple: 目标三元组
        link_type: 链接类型

    Returns:
        CRT 文件列表
    """
    manager = RuntimeManager()
    return manager.get_crt_files(target_triple, link_type)

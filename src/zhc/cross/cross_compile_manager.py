# -*- coding: utf-8 -*-
"""
ZhC 交叉编译管理器

整合主机检测、目标管理、工具链管理和 Sysroot 管理，提供统一的交叉编译接口。

作者：远
日期：2026-04-09
"""

import logging
import os
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .triple_parser import TargetTriple, TripleParser, TripleParseError
from .host_detector import HostInfo, HostDetector
from .toolchain_manager import (
    Toolchain,
    ToolchainManager,
)
from .sysroot_manager import (
    Sysroot,
    SysrootManager,
)

logger = logging.getLogger(__name__)


@dataclass
class TargetConfig:
    """
    目标平台配置

    包含编译目标所需的完整配置信息。
    """

    # 基本信息
    triple: TargetTriple  # 目标三元组
    original_triple: str  # 原始三元组字符串

    # 工具链配置
    toolchain: Optional[Toolchain] = None  # 工具链
    sysroot: Optional[Sysroot] = None  # Sysroot

    # CPU 和特性
    cpu: str = "generic"  # CPU 型号
    features: List[str] = field(default_factory=list)  # CPU 特性

    # 链接选项
    link_type: str = "dynamic"  # 链接类型（dynamic, static）
    runtime_library: str = ""  # 运行时库

    # 优化选项
    optimization_level: int = 2  # 优化级别 (0-3)

    # 调试选项
    debug: bool = False  # 是否生成调试信息

    def is_native(self) -> bool:
        """是否为本机编译"""
        host = HostDetector.detect()
        return (
            self.triple.arch == host.arch
            and self.triple.os == host.os
            and not self.triple.is_embedded
        )

    def is_cross(self) -> bool:
        """是否为交叉编译"""
        return not self.is_native()

    def has_toolchain(self) -> bool:
        """是否有工具链"""
        return self.toolchain is not None and self.toolchain.has_compiler()

    def has_sysroot(self) -> bool:
        """是否有 sysroot"""
        return self.sysroot is not None and self.sysroot.exists()

    def get_compiler_flags(self) -> List[str]:
        """获取编译器标志"""
        flags = []

        # 目标
        flags.append(f"--target={self.original_triple}")

        # CPU
        if self.cpu != "generic":
            flags.append(f"-mcpu={self.cpu}")

        # 特性
        for feature in self.features:
            flags.append(f"+{feature}")

        # Sysroot
        if self.has_sysroot():
            flags.append(f"--sysroot={self.sysroot.path}")

        # 优化级别
        flags.append(f"-O{self.optimization_level}")

        # 调试
        if self.debug:
            flags.append("-g")

        return flags

    def get_linker_flags(self) -> List[str]:
        """获取链接器标志"""
        flags = []

        # 目标
        flags.append(f"--target={self.original_triple}")

        # Sysroot
        if self.has_sysroot():
            flags.append(f"--sysroot={self.sysroot.path}")

        # 链接类型
        if self.link_type == "static":
            flags.append("-static")

        # 运行时库
        if self.runtime_library:
            flags.append(f"-l{self.runtime_library}")

        return flags


@dataclass
class CompileOptions:
    """编译选项"""

    output_file: str = ""  # 输出文件
    optimization_level: int = 2  # 优化级别
    debug: bool = False  # 调试信息
    generate_object: bool = True  # 生成对象文件
    generate_assembly: bool = False  # 生成汇编
    target: str = ""  # 目标三元组
    include_paths: List[str] = field(default_factory=list)  # 包含路径
    library_paths: List[str] = field(default_factory=list)  # 库路径
    libraries: List[str] = field(default_factory=list)  # 链接的库
    defines: Dict[str, str] = field(default_factory=dict)  # 宏定义
    features: List[str] = field(default_factory=list)  # CPU 特性
    cpu: str = "generic"  # CPU 型号
    sysroot: str = ""  # Sysroot


@dataclass
class CompileResult:
    """编译结果"""

    success: bool  # 是否成功
    output_file: str = ""  # 输出文件
    target_config: Optional[TargetConfig] = None  # 目标配置
    error_message: str = ""  # 错误信息
    warnings: List[str] = field(default_factory=list)  # 警告信息
    statistics: Dict[str, any] = field(default_factory=dict)  # 统计信息


class CrossCompileManager:
    """
    交叉编译管理器

    提供完整的交叉编译功能，包括目标配置、工具链管理和编译执行。
    """

    def __init__(self):
        self.host: HostInfo = HostDetector.detect()
        self.target_manager = ToolchainManager()
        self.sysroot_manager = SysrootManager()

        # 缓存的目标配置
        self._target_configs: Dict[str, TargetConfig] = {}

        # 启用的目标列表
        self._enabled_targets: Set[str] = set()

    def configure_target(
        self,
        triple: str,
        toolchain_path: Optional[str] = None,
        sysroot_path: Optional[str] = None,
        cpu: str = "generic",
        features: Optional[List[str]] = None,
    ) -> TargetConfig:
        """
        配置目标平台

        Args:
            triple: 目标三元组
            toolchain_path: 工具链路径（可选）
            sysroot_path: Sysroot 路径（可选）
            cpu: CPU 型号（可选）
            features: CPU 特性列表（可选）

        Returns:
            目标配置对象

        Raises:
            TripleParseError: 三元组解析失败
        """
        # 解析三元组
        try:
            target_triple = TripleParser.parse(triple)
        except TripleParseError:
            raise

        # 构建配置
        config = TargetConfig(
            triple=target_triple,
            original_triple=triple,
            cpu=cpu,
            features=features or [],
        )

        # 配置工具链
        if toolchain_path:
            # 使用指定的工具链
            toolchain = self._load_toolchain_from_path(target_triple, toolchain_path)
            config.toolchain = toolchain
        else:
            # 自动检测工具链
            toolchain = self.target_manager.detect_toolchain(triple)
            config.toolchain = toolchain

        # 配置 Sysroot
        if sysroot_path:
            self.sysroot_manager.set_sysroot(triple, sysroot_path)

        config.sysroot = self.sysroot_manager.get_sysroot(triple)

        # 缓存配置
        self._target_configs[triple] = config
        self._enabled_targets.add(triple)

        logger.info(f"Configured target: {triple}")
        if config.toolchain:
            logger.info(f"  Toolchain: {config.toolchain.name}")
        if config.sysroot:
            logger.info(f"  Sysroot: {config.sysroot.path}")

        return config

    def _load_toolchain_from_path(
        self, target: TargetTriple, path: str
    ) -> Optional[Toolchain]:
        """从指定路径加载工具链"""
        import shutil

        def find_tool(name):
            for tool_name in name:
                full_path = os.path.join(path, name[0])
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    return full_path
                bin_path = os.path.join(path, "bin", name[0])
                if os.path.isfile(bin_path) and os.access(bin_path, os.X_OK):
                    return bin_path
                if shutil.which(name[0]):
                    return shutil.which(name[0])
            return None

        return Toolchain(
            name="custom-toolchain",
            target=target,
            type="custom",
            cc=find_tool(["clang", "gcc", "cc"]),
            cxx=find_tool(["clang++", "g++", "c++"]),
        )

    def get_target_config(self, triple: str) -> Optional[TargetConfig]:
        """
        获取目标配置

        Args:
            triple: 目标三元组

        Returns:
            目标配置对象，如果不存在返回 None
        """
        return self._target_configs.get(triple)

    def get_host_config(self) -> TargetConfig:
        """
        获取主机配置

        Returns:
            主机目标配置
        """
        return self.configure_target(self.host.triple)

    def list_targets(self) -> List[str]:
        """列出已配置的目标"""
        return list(self._enabled_targets)

    def is_cross_compile(self, triple: str) -> bool:
        """
        判断是否为交叉编译

        Args:
            triple: 目标三元组

        Returns:
            是否为交叉编译
        """
        try:
            target = TripleParser.parse(triple)
            return not target.is_native
        except Exception:
            return True

    def compile(
        self,
        source_file: str,
        output_file: str,
        options: Optional[CompileOptions] = None,
    ) -> CompileResult:
        """
        编译源文件

        Args:
            source_file: 源文件路径
            output_file: 输出文件路径
            options: 编译选项

        Returns:
            编译结果
        """
        if options is None:
            options = CompileOptions(output_file=output_file)

        # 确定目标
        target_triple = options.target or self.host.triple

        # 获取或创建配置
        config = self.get_target_config(target_triple)
        if config is None:
            config = self.configure_target(
                target_triple,
                sysroot_path=options.sysroot if options.sysroot else None,
                cpu=options.cpu,
                features=options.features,
            )

        # 更新配置
        config.optimization_level = options.optimization_level
        config.debug = options.debug

        # 构建编译命令
        cmd = self._build_compile_command(source_file, output_file, config, options)

        logger.info(f"Compiling: {' '.join(cmd)}")

        # 执行编译
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 分钟超时
            )

            if result.returncode == 0:
                return CompileResult(
                    success=True,
                    output_file=output_file,
                    target_config=config,
                    statistics={
                        "compile_time": result.stderr,
                    },
                )
            else:
                return CompileResult(
                    success=False,
                    target_config=config,
                    error_message=result.stderr,
                )
        except subprocess.TimeoutExpired:
            return CompileResult(
                success=False,
                target_config=config,
                error_message="Compilation timed out",
            )
        except Exception as e:
            return CompileResult(
                success=False,
                target_config=config,
                error_message=str(e),
            )

    def _build_compile_command(
        self,
        source_file: str,
        output_file: str,
        config: TargetConfig,
        options: CompileOptions,
    ) -> List[str]:
        """构建编译命令"""
        cmd = []

        # 编译器
        if config.toolchain and config.toolchain.cc:
            cmd.append(config.toolchain.cc.path)
        else:
            cmd.append("clang")  # 默认使用 clang

        # 目标
        cmd.append(f"--target={config.original_triple}")

        # 优化级别
        cmd.append(f"-O{config.optimization_level}")

        # 调试信息
        if config.debug:
            cmd.append("-g")

        # Sysroot
        if config.sysroot:
            cmd.append(f"--sysroot={config.sysroot.path}")

        # CPU
        if config.cpu != "generic":
            cmd.append(f"-mcpu={config.cpu}")

        # 特性
        for feature in config.features:
            cmd.append(f"-target-feature=+{feature}")

        # 包含路径
        for path in options.include_paths:
            cmd.append(f"-I{path}")

        # 库路径
        for path in options.library_paths:
            cmd.append(f"-L{path}")

        # 宏定义
        for name, value in options.defines.items():
            if value:
                cmd.append(f"-D{name}={value}")
            else:
                cmd.append(f"-D{name}")

        # 源文件
        cmd.append(source_file)

        # 输出文件
        cmd.append("-o")
        cmd.append(output_file)

        # 库
        for lib in options.libraries:
            cmd.append(f"-l{lib}")

        return cmd

    def link(
        self,
        object_files: List[str],
        output_file: str,
        target_triple: str,
        options: Optional[CompileOptions] = None,
    ) -> CompileResult:
        """
        链接对象文件

        Args:
            object_files: 对象文件列表
            output_file: 输出文件路径
            target_triple: 目标三元组
            options: 链接选项

        Returns:
            链接结果
        """
        if options is None:
            options = CompileOptions(output_file=output_file)

        # 获取配置
        config = self.get_target_config(target_triple)
        if config is None:
            config = self.configure_target(target_triple)

        # 构建链接命令
        cmd = self._build_link_command(object_files, output_file, config, options)

        logger.info(f"Linking: {' '.join(cmd)}")

        # 执行链接
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                return CompileResult(
                    success=True,
                    output_file=output_file,
                    target_config=config,
                )
            else:
                return CompileResult(
                    success=False,
                    target_config=config,
                    error_message=result.stderr,
                )
        except Exception as e:
            return CompileResult(
                success=False,
                target_config=config,
                error_message=str(e),
            )

    def _build_link_command(
        self,
        object_files: List[str],
        output_file: str,
        config: TargetConfig,
        options: CompileOptions,
    ) -> List[str]:
        """构建链接命令"""
        cmd = []

        # 链接器
        if config.toolchain and config.toolchain.linker:
            cmd.append(config.toolchain.linker.path)
        else:
            # 使用 clang 作为链接器
            cmd.append("clang")

        # 目标
        cmd.append(f"--target={config.original_triple}")

        # Sysroot
        if config.sysroot:
            cmd.append(f"--sysroot={config.sysroot.path}")

        # 链接类型
        if config.link_type == "static":
            cmd.append("-static")

        # 对象文件
        cmd.extend(object_files)

        # 输出文件
        cmd.extend(["-o", output_file])

        # 库
        for lib in options.libraries:
            cmd.append(f"-l{lib}")

        # 库路径
        for path in options.library_paths:
            cmd.append(f"-L{path}")

        return cmd


# 便捷函数
def create_cross_compile_manager() -> CrossCompileManager:
    """创建交叉编译管理器"""
    return CrossCompileManager()


def configure_target(
    triple: str,
    toolchain_path: Optional[str] = None,
    sysroot_path: Optional[str] = None,
) -> TargetConfig:
    """
    配置目标平台

    Args:
        triple: 目标三元组
        toolchain_path: 工具链路径（可选）
        sysroot_path: Sysroot 路径（可选）

    Returns:
        目标配置对象
    """
    manager = CrossCompileManager()
    return manager.configure_target(triple, toolchain_path, sysroot_path)


def get_host_target() -> TargetConfig:
    """
    获取主机目标配置

    Returns:
        主机目标配置
    """
    manager = CrossCompileManager()
    return manager.get_host_config()


def is_cross_compile(triple: str) -> bool:
    """
    判断是否为交叉编译

    Args:
        triple: 目标三元组

    Returns:
        是否为交叉编译
    """
    manager = CrossCompileManager()
    return manager.is_cross_compile(triple)

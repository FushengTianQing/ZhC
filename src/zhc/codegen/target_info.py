# -*- coding: utf-8 -*-
"""
ZhC 目标平台信息

封装 LLVM 目标机器信息，提供数据布局、指令集等查询功能。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass
from typing import Dict, Optional, Any
import logging

from zhc.codegen.target_registry import Target, Architecture, OperatingSystem

logger = logging.getLogger(__name__)


@dataclass
class DataLayout:
    """
    数据布局描述

    描述目标平台的数据表示方式，包括大小端、对齐等。
    """

    string: str  # LLVM 数据布局字符串

    # 基本属性
    is_little_endian: bool = True
    pointer_size: int = 8
    pointer_alignment: int = 8

    # 类型大小和对齐
    int_sizes: Dict[int, int] = None  # 位 -> 字节
    float_sizes: Dict[int, int] = None
    int_alignments: Dict[int, int] = None
    float_alignments: Dict[int, int] = None

    def __post_init__(self):
        if self.int_sizes is None:
            self.int_sizes = {8: 1, 16: 2, 32: 4, 64: 8}
        if self.float_sizes is None:
            self.float_sizes = {32: 4, 64: 8, 80: 10, 128: 16}
        if self.int_alignments is None:
            self.int_alignments = {8: 1, 16: 2, 32: 4, 64: 8}
        if self.float_alignments is None:
            self.float_alignments = {32: 4, 64: 8, 80: 16, 128: 16}

    def get_int_size(self, bits: int) -> int:
        """获取整数类型大小（字节）"""
        return self.int_sizes.get(bits, (bits + 7) // 8)

    def get_float_size(self, bits: int) -> int:
        """获取浮点类型大小（字节）"""
        return self.float_sizes.get(bits, (bits + 7) // 8)

    def get_int_alignment(self, bits: int) -> int:
        """获取整数类型对齐"""
        return self.int_alignments.get(bits, min(bits // 8, 8))

    def get_float_alignment(self, bits: int) -> int:
        """获取浮点类型对齐"""
        return self.float_alignments.get(bits, min(bits // 8, 8))


class TargetInfo:
    """
    目标平台信息

    封装 LLVM 目标机器信息，提供各种查询接口。
    """

    def __init__(self, target: Target):
        """
        初始化目标信息

        Args:
            target: 目标平台描述
        """
        self.target = target
        self._data_layout = self._create_data_layout()
        self._llvm_target_machine = None

    def _create_data_layout(self) -> DataLayout:
        """创建数据布局"""
        # 根据架构创建数据布局
        layouts = {
            Architecture.X86_64: DataLayout(
                string="e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128",
                is_little_endian=True,
                pointer_size=8,
                pointer_alignment=8,
            ),
            Architecture.AARCH64: DataLayout(
                string="e-m:e-i8:8:32-i16:16:32-i64:64-i128:128-n32:64-S128",
                is_little_endian=True,
                pointer_size=8,
                pointer_alignment=8,
            ),
            Architecture.ARM: DataLayout(
                string="e-m:e-p:32:32-Fi8-i64:64-v128:64:128-a:0:32-n32-S64",
                is_little_endian=True,
                pointer_size=4,
                pointer_alignment=4,
            ),
            Architecture.RISCV64: DataLayout(
                string="e-m:e-p:64:64-i64:64-i128:128-n64-S128",
                is_little_endian=True,
                pointer_size=8,
                pointer_alignment=8,
            ),
            Architecture.WASM32: DataLayout(
                string="e-m:e-p:32:32-i64:64-n32:64-S128",
                is_little_endian=True,
                pointer_size=4,
                pointer_alignment=4,
            ),
        }

        return layouts.get(self.target.arch, DataLayout(string=""))

    @property
    def data_layout(self) -> DataLayout:
        """获取数据布局"""
        return self._data_layout

    @property
    def triple(self) -> str:
        """获取目标三元组"""
        return self.target.triple

    @property
    def arch(self) -> Architecture:
        """获取架构"""
        return self.target.arch

    @property
    def os(self) -> OperatingSystem:
        """获取操作系统"""
        return self.target.os

    @property
    def pointer_size(self) -> int:
        """获取指针大小（字节）"""
        return self.target.pointer_size

    @property
    def stack_alignment(self) -> int:
        """获取栈对齐"""
        return self.target.stack_alignment

    @property
    def is_little_endian(self) -> bool:
        """是否为小端序"""
        return self._data_layout.is_little_endian

    @property
    def is_big_endian(self) -> bool:
        """是否为大端序"""
        return not self.is_little_endian

    def get_cpu_name(self) -> str:
        """获取 CPU 名称"""
        return self.target.default_cpu

    def get_feature_string(self) -> str:
        """获取特性字符串"""
        return ",".join(self.target.default_features)

    def get_register_class(self, name: str) -> Optional[Any]:
        """获取寄存器类"""
        for rc in self.target.register_classes:
            if rc.name == name:
                return rc
        return None

    def get_calling_convention(self) -> str:
        """获取调用约定名称"""
        cc_names = {
            "SYSTEM_V_AMD64": "SystemV_AMD64",
            "MS_X64": "Microsoft_X64",
            "AAPCS64": "AAPCS64",
            "AAPCS": "AAPCS",
            "RISCV": "RISCV",
            "WASM": "WebAssembly",
        }
        return cc_names.get(self.target.calling_convention.name, "Unknown")

    def get_linker_name(self) -> str:
        """获取链接器名称"""
        return self.target.default_linker

    def get_object_format(self) -> str:
        """获取目标文件格式"""
        if self.target.os == OperatingSystem.LINUX:
            return "ELF"
        elif self.target.os == OperatingSystem.DARWIN:
            return "MachO"
        elif self.target.os == OperatingSystem.WINDOWS:
            return "COFF"
        elif self.target.arch in (Architecture.WASM32, Architecture.WASM64):
            return "Wasm"
        return "ELF"  # 默认

    def supports_feature(self, feature: str) -> bool:
        """检查是否支持指定特性"""
        return feature.lower() in [f.lower() for f in self.target.default_features]

    def get_llvm_target_machine(self) -> Optional[Any]:
        """
        获取 LLVM 目标机器

        Returns:
            llvm.TargetMachine 实例
        """
        if self._llvm_target_machine is not None:
            return self._llvm_target_machine

        try:
            import llvmlite.binding as llvm

            # 初始化目标
            llvm.initialize_all_targets()
            llvm.initialize_all_asmprinters()

            # 创建目标机器
            target = llvm.Target.from_triple(self.target.triple)
            self._llvm_target_machine = target.create_target_machine(
                cpu=self.target.default_cpu,
                features=self.get_feature_string(),
                opt=2,  # 优化级别
            )

            return self._llvm_target_machine

        except ImportError:
            logger.warning("llvmlite not available")
            return None
        except Exception as e:
            logger.error(f"Failed to create LLVM target machine: {e}")
            return None

    def __str__(self) -> str:
        return f"TargetInfo({self.target})"

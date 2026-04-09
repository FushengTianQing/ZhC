# -*- coding: utf-8 -*-
"""
ZhC 目标 Lowering

将 LLVM IR 或高级中间表示 Lowering 到目标特定的表示。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import logging

from zhc.codegen.target_registry import Target, CallingConvention
from zhc.codegen.register_allocator import VirtualRegister, RegisterClass
from zhc.codegen.frame_lower import StackFrame

logger = logging.getLogger(__name__)


# ============================================================================
# Lowering 结果
# ============================================================================


@dataclass
class LoweredFunction:
    """
    Lowered 函数

    表示一个 Lowering 后的函数。
    """

    name: str  # 函数名
    return_type: str  # 返回类型

    # 参数
    params: List[Tuple[str, str]] = field(default_factory=list)  # (类型, 名称)

    # 指令
    instructions: List[Any] = field(default_factory=list)  # 机器指令

    # 栈帧
    frame: Optional[StackFrame] = None

    # 寄存器分配
    vregs: Dict[int, VirtualRegister] = field(default_factory=dict)

    # 属性
    is_vararg: bool = False
    is_noinline: bool = False
    is_alwaysinline: bool = False
    linkage: str = "external"  # external, internal, weak

    def __str__(self) -> str:
        params_str = ", ".join(f"{t} {n}" for t, n in self.params)
        return f"{self.return_type} {self.name}({params_str})"


@dataclass
class LoweredModule:
    """
    Lowered 模块

    表示一个 Lowering 后的编译单元。
    """

    name: str  # 模块名

    # 函数
    functions: Dict[str, LoweredFunction] = field(default_factory=dict)

    # 全局变量
    globals: Dict[str, Any] = field(default_factory=dict)

    # 目标信息
    target_triple: str = ""
    data_layout: str = ""

    def add_function(self, func: LoweredFunction) -> None:
        """添加函数"""
        self.functions[func.name] = func

    def get_function(self, name: str) -> Optional[LoweredFunction]:
        """获取函数"""
        return self.functions.get(name)


# ============================================================================
# 目标 Lowering 基类
# ============================================================================


class TargetLowering:
    """
    目标 Lowering 基类

    负责将高级 IR Lowering 到目标特定的表示。

    子类需要实现目标特定的 Lowering 逻辑。
    """

    def __init__(self, target: Target):
        """
        初始化目标 Lowering

        Args:
            target: 目标描述
        """
        self.target = target
        self._vreg_counter = 0

    # =========================================================================
    # 函数 Lowering
    # =========================================================================

    def lower_function(self, func_ir: Any) -> LoweredFunction:
        """
        Lowering 函数

        Args:
            func_ir: 函数的 IR 表示

        Returns:
            Lowered 函数
        """
        raise NotImplementedError("Subclass must implement lower_function()")

    def lower_module(self, module_ir: Any) -> LoweredModule:
        """
        Lowering 模块

        Args:
            module_ir: 模块的 IR 表示

        Returns:
            Lowered 模块
        """
        raise NotImplementedError("Subclass must implement lower_module()")

    # =========================================================================
    # 类型 Lowering
    # =========================================================================

    def lower_type(self, type_ir: Any) -> str:
        """
        Lowering 类型

        Args:
            type_ir: 类型 IR

        Returns:
            目标类型字符串
        """
        raise NotImplementedError("Subclass must implement lower_type()")

    def get_type_size(self, type_str: str) -> int:
        """获取类型大小（字节）"""
        sizes = {
            "i1": 1,
            "i8": 1,
            "i16": 2,
            "i32": 4,
            "i64": 8,
            "f32": 4,
            "f64": 8,
            "f80": 10,
            "f128": 16,
            "ptr": self.target.pointer_size,
        }
        return sizes.get(type_str, 8)

    def get_type_alignment(self, type_str: str) -> int:
        """获取类型对齐"""
        return min(self.get_type_size(type_str), self.target.stack_alignment)

    # =========================================================================
    # 虚拟寄存器管理
    # =========================================================================

    def create_vreg(
        self, class_: RegisterClass = RegisterClass.GENERAL, size: int = 64
    ) -> VirtualRegister:
        """创建虚拟寄存器"""
        self._vreg_counter += 1
        return VirtualRegister(id=self._vreg_counter, class_=class_, size=size)

    # =========================================================================
    # 调用约定
    # =========================================================================

    def get_calling_convention(self) -> CallingConvention:
        """获取调用约定"""
        return self.target.calling_convention

    def get_arg_registers(self, cc: CallingConvention) -> List[str]:
        """获取参数寄存器"""
        cc_regs = {
            CallingConvention.SYSTEM_V_AMD64: ["rdi", "rsi", "rdx", "rcx", "r8", "r9"],
            CallingConvention.MS_X64: ["rcx", "rdx", "r8", "r9"],
            CallingConvention.AAPCS64: ["x0", "x1", "x2", "x3", "x4", "x5", "x6", "x7"],
            CallingConvention.AAPCS: ["r0", "r1", "r2", "r3"],
            CallingConvention.RISCV: ["a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7"],
            CallingConvention.WASM: [],  # WebAssembly 使用栈传递
        }
        return cc_regs.get(cc, [])

    def get_return_register(self, cc: CallingConvention) -> str:
        """获取返回值寄存器"""
        cc_ret = {
            CallingConvention.SYSTEM_V_AMD64: "rax",
            CallingConvention.MS_X64: "rax",
            CallingConvention.AAPCS64: "x0",
            CallingConvention.AAPCS: "r0",
            CallingConvention.RISCV: "a0",
            CallingConvention.WASM: "",
        }
        return cc_ret.get(cc, "rax")


# ============================================================================
# x86_64 目标 Lowering
# ============================================================================


class X86_64TargetLowering(TargetLowering):
    """
    x86_64 目标 Lowering

    实现 System V AMD64 ABI 的 Lowering 逻辑。
    """

    def __init__(self, target: Target):
        super().__init__(target)

    def lower_function(self, func_ir: Any) -> LoweredFunction:
        """Lowering x86_64 函数"""
        # 简化实现：创建基本的 Lowered 函数
        func = LoweredFunction(
            name=getattr(func_ir, "name", "unknown"),
            return_type=self.lower_type(getattr(func_ir, "return_type", "void")),
        )

        # Lowering 参数
        if hasattr(func_ir, "params"):
            for param in func_ir.params:
                param_type = self.lower_type(param.type)
                func.params.append((param_type, param.name))

        return func

    def lower_module(self, module_ir: Any) -> LoweredModule:
        """Lowering x86_64 模块"""
        module = LoweredModule(
            name=getattr(module_ir, "name", "module"),
            target_triple=self.target.triple,
        )

        # Lowering 所有函数
        if hasattr(module_ir, "functions"):
            for func_ir in module_ir.functions:
                func = self.lower_function(func_ir)
                module.add_function(func)

        return module

    def lower_type(self, type_ir: Any) -> str:
        """Lowering x86_64 类型"""
        # 简化实现
        type_str = str(type_ir).lower()

        type_map = {
            "void": "void",
            "bool": "i1",
            "i1": "i1",
            "i8": "i8",
            "i16": "i16",
            "i32": "i32",
            "i64": "i64",
            "int": "i32",
            "long": "i64",
            "float": "f32",
            "double": "f64",
            "ptr": "ptr",
            "pointer": "ptr",
        }

        return type_map.get(type_str, type_str)


# ============================================================================
# AArch64 目标 Lowering
# ============================================================================


class AArch64TargetLowering(TargetLowering):
    """
    AArch64 目标 Lowering

    实现 AAPCS64 ABI 的 Lowering 逻辑。
    """

    def __init__(self, target: Target):
        super().__init__(target)

    def lower_function(self, func_ir: Any) -> LoweredFunction:
        """Lowering AArch64 函数"""
        func = LoweredFunction(
            name=getattr(func_ir, "name", "unknown"),
            return_type=self.lower_type(getattr(func_ir, "return_type", "void")),
        )

        if hasattr(func_ir, "params"):
            for param in func_ir.params:
                param_type = self.lower_type(param.type)
                func.params.append((param_type, param.name))

        return func

    def lower_module(self, module_ir: Any) -> LoweredModule:
        """Lowering AArch64 模块"""
        module = LoweredModule(
            name=getattr(module_ir, "name", "module"),
            target_triple=self.target.triple,
        )

        if hasattr(module_ir, "functions"):
            for func_ir in module_ir.functions:
                func = self.lower_function(func_ir)
                module.add_function(func)

        return module

    def lower_type(self, type_ir: Any) -> str:
        """Lowering AArch64 类型"""
        type_str = str(type_ir).lower()

        type_map = {
            "void": "void",
            "bool": "i1",
            "i1": "i1",
            "i8": "i8",
            "i16": "i16",
            "i32": "i32",
            "i64": "i64",
            "int": "i32",
            "long": "i64",
            "float": "f32",
            "double": "f64",
            "ptr": "ptr",
            "pointer": "ptr",
        }

        return type_map.get(type_str, type_str)


# ============================================================================
# WebAssembly 目标 Lowering
# ============================================================================


class WasmTargetLowering(TargetLowering):
    """
    WebAssembly 目标 Lowering

    实现 WebAssembly 的 Lowering 逻辑。
    """

    def __init__(self, target: Target):
        super().__init__(target)

    def lower_function(self, func_ir: Any) -> LoweredFunction:
        """Lowering WebAssembly 函数"""
        func = LoweredFunction(
            name=getattr(func_ir, "name", "unknown"),
            return_type=self.lower_type(getattr(func_ir, "return_type", "void")),
        )

        if hasattr(func_ir, "params"):
            for param in func_ir.params:
                param_type = self.lower_type(param.type)
                func.params.append((param_type, param.name))

        return func

    def lower_module(self, module_ir: Any) -> LoweredModule:
        """Lowering WebAssembly 模块"""
        module = LoweredModule(
            name=getattr(module_ir, "name", "module"),
            target_triple=self.target.triple,
        )

        if hasattr(module_ir, "functions"):
            for func_ir in module_ir.functions:
                func = self.lower_function(func_ir)
                module.add_function(func)

        return module

    def lower_type(self, type_ir: Any) -> str:
        """Lowering WebAssembly 类型"""
        type_str = str(type_ir).lower()

        # WebAssembly 类型系统更简单
        type_map = {
            "void": "void",
            "bool": "i32",
            "i1": "i32",
            "i8": "i32",
            "i16": "i32",
            "i32": "i32",
            "i64": "i64",
            "int": "i32",
            "long": "i64",
            "float": "f32",
            "double": "f64",
            "ptr": "i32",  # wasm32
            "pointer": "i32",
        }

        return type_map.get(type_str, "i32")

    def get_arg_registers(self, cc: CallingConvention) -> List[str]:
        """WebAssembly 使用栈传递参数"""
        return []

    def get_return_register(self, cc: CallingConvention) -> str:
        """WebAssembly 没有寄存器"""
        return ""


# ============================================================================
# 工厂函数
# ============================================================================


def create_target_lowering(target: Target) -> TargetLowering:
    """
    创建目标 Lowering

    Args:
        target: 目标描述

    Returns:
        目标 Lowering 实例
    """
    lowering_map = {
        "x86_64": X86_64TargetLowering,
        "x86-64": X86_64TargetLowering,
        "aarch64": AArch64TargetLowering,
        "arm64": AArch64TargetLowering,
        "wasm32": WasmTargetLowering,
        "wasm64": WasmTargetLowering,
    }

    arch_name = target.name.split("-")[0].lower()
    lowering_class = lowering_map.get(arch_name, TargetLowering)

    return lowering_class(target)

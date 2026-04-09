# -*- coding: utf-8 -*-
"""
ZhC 向量化 IR 构建器

构建向量化后的 LLVM IR，实现 SIMD 指令生成。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass
from typing import List, Dict
from enum import Enum

from .loop_analyzer import Loop


class VectorTypeKind(Enum):
    """向量类型种类"""

    FLOAT32 = "float32"
    FLOAT64 = "float64"
    INT8 = "int8"
    INT16 = "int16"
    INT32 = "int32"
    INT64 = "int64"
    UINT8 = "uint8"
    UINT16 = "uint16"
    UINT32 = "uint32"
    UINT64 = "uint64"


@dataclass
class VectorType:
    """
    向量类型

    描述 SIMD 向量的类型信息。
    """

    kind: VectorTypeKind
    num_elements: int  # 元素数量
    total_bits: int  # 总位数

    # 便捷工厂方法
    @classmethod
    def float32_vector(cls, width: int) -> "VectorType":
        return cls(VectorTypeKind.FLOAT32, width, width * 32)

    @classmethod
    def float64_vector(cls, width: int) -> "VectorType":
        return cls(VectorTypeKind.FLOAT64, width, width * 64)

    @classmethod
    def int32_vector(cls, width: int) -> "VectorType":
        return cls(VectorTypeKind.INT32, width, width * 32)

    @classmethod
    def int64_vector(cls, width: int) -> "VectorType":
        return cls(VectorTypeKind.INT64, width, width * 64)

    @property
    def llvm_type(self) -> str:
        """获取 LLVM 类型字符串"""
        width_suffix = f"<{self.num_elements} x "
        type_str = self._llvm_type_name()
        return f"{width_suffix}{type_str}>"

    def _llvm_type_name(self) -> str:
        """获取基本类型名"""
        type_map = {
            VectorTypeKind.FLOAT32: "float",
            VectorTypeKind.FLOAT64: "double",
            VectorTypeKind.INT8: "i8",
            VectorTypeKind.INT16: "i16",
            VectorTypeKind.INT32: "i32",
            VectorTypeKind.INT64: "i64",
            VectorTypeKind.UINT8: "i8",
            VectorTypeKind.UINT16: "i16",
            VectorTypeKind.UINT32: "i32",
            VectorTypeKind.UINT64: "i64",
        }
        return type_map.get(self.kind, "i32")

    def __str__(self) -> str:
        return f"v{self.num_elements}x{self._llvm_type_name()}"


@dataclass
class VectorizedLoop:
    """
    向量化后的循环

    包含向量化循环的完整 IR 表示。
    """

    original_loop: Loop  # 原始循环
    vector_type: VectorType  # 向量类型
    vectorized_body: List[str]  # 向量化后的指令
    prologue: List[str]  # 前导代码
    epilogue: List[str]  # 尾部代码（处理不能整除的部分）
    mask_setup: List[str]  # 掩码设置代码
    metadata: Dict = None  # 额外元数据

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def get_ir(self) -> str:
        """获取完整的 IR 表示"""
        parts = []

        # 前导代码
        if self.prologue:
            parts.extend(self.prologue)

        # 掩码设置
        if self.mask_setup:
            parts.extend(self.mask_setup)

        # 向量化循环体
        parts.extend(self.vectorized_body)

        # 尾部代码
        if self.epilogue:
            parts.extend(self.epilogue)

        return "\n".join(parts)


class VectorBuilder:
    """
    向量化 IR 构建器

    将标量循环 IR 转换为向量化后的 SIMD IR。
    """

    def __init__(self, target_arch: str, vector_width: int = 4):
        self.target_arch = target_arch
        self.vector_width = vector_width
        self._temp_counter = 0

    def build_vectorized_body(self, loop: Loop, vec_type: VectorType) -> List[str]:
        """
        构建向量化循环体

        Args:
            loop: 原始循环信息
            vec_type: 向量类型

        Returns:
            向量化后的 IR 指令列表
        """
        instructions = []

        # 1. 生成向量加载
        instructions.extend(self._build_vector_loads(loop, vec_type))

        # 2. 生成向量运算
        instructions.extend(self._build_vector_ops(loop, vec_type))

        # 3. 生成向量存储
        instructions.extend(self._build_vector_stores(loop, vec_type))

        return instructions

    def _build_vector_loads(self, loop: Loop, vec_type: VectorType) -> List[str]:
        """生成向量加载指令"""
        instructions = []

        # 获取向量加载指令
        if loop.num_loads > 0:
            # 简单的向量加载生成
            # 实际实现需要分析原始循环中的加载指令
            vec_ptr = f"%vec.ptr.{self._next_temp()}"
            vec_load = (
                f"{vec_ptr} = load {vec_type.llvm_type}, {vec_type.llvm_type}* %ptr"
            )
            instructions.append(vec_load)

        return instructions

    def _build_vector_ops(self, loop: Loop, vec_type: VectorType) -> List[str]:
        """生成向量运算指令"""
        instructions = []

        # 简化的向量运算生成
        op_type = vec_type.kind

        if op_type in (VectorTypeKind.FLOAT32, VectorTypeKind.FLOAT64):
            # 浮点运算
            add_op = f"%vec.result.{self._next_temp()} = fadd {vec_type.llvm_type} %vec.a, %vec.b"
            instructions.append(add_op)
        elif op_type in (VectorTypeKind.INT32, VectorTypeKind.INT64):
            # 整数运算
            add_op = f"%vec.result.{self._next_temp()} = add {vec_type.llvm_type} %vec.a, %vec.b"
            instructions.append(add_op)

        return instructions

    def _build_vector_stores(self, loop: Loop, vec_type: VectorType) -> List[str]:
        """生成向量存储指令"""
        instructions = []

        if loop.num_stores > 0:
            # 简单的向量存储生成
            store = f"store {vec_type.llvm_type} %vec.result, {vec_type.llvm_type}* %out.ptr"
            instructions.append(store)

        return instructions

    def _next_temp(self) -> str:
        """生成临时变量名"""
        self._temp_counter += 1
        return str(self._temp_counter)

    def build_masked_gather(
        self, base_ptr: str, indices: List[str], vec_type: VectorType
    ) -> str:
        """
        构建掩码聚集操作

        Args:
            base_ptr: 基指针
            indices: 索引列表
            vec_type: 向量类型

        Returns:
            LLVM IR 指令
        """
        # 简化的 gather 实现
        return f"%vec.gather = call {vec_type.llvm_type} @llvm.masked.gather.{vec_type}"

    def build_masked_scatter(
        self, values: str, base_ptr: str, indices: List[str], vec_type: VectorType
    ) -> str:
        """
        构建掩码分散操作

        Args:
            values: 要存储的值
            base_ptr: 基指针
            indices: 索引列表
            vec_type: 向量类型

        Returns:
            LLVM IR 指令
        """
        # 简化的 scatter 实现
        return f"call void @llvm.masked.scatter.{vec_type}({vec_type} {values}, {vec_type}* {base_ptr})"

    def build_blend(
        self, vec_a: str, vec_b: str, mask: str, vec_type: VectorType
    ) -> str:
        """
        构建混合操作

        Args:
            vec_a: 第一个向量
            vec_b: 第二个向量
            mask: 掩码
            vec_type: 向量类型

        Returns:
            LLVM IR 指令
        """
        return f"%vec.blend = select {vec_type.llvm_type} {mask}, {vec_type.llvm_type} {vec_a}, {vec_type.llvm_type} {vec_b}"

    def get_target_intrinsics(self) -> Dict[str, str]:
        """
        获取目标平台的 intrinsic 函数名

        Returns:
            intrinsic 函数名映射
        """
        if self.target_arch.startswith("x86"):
            return self._get_x86_intrinsics()
        elif self.target_arch.startswith("aarch64") or self.target_arch.startswith(
            "arm"
        ):
            return self._get_neon_intrinsics()
        elif self.target_arch.startswith("riscv"):
            return self._get_rvv_intrinsics()
        elif self.target_arch.startswith("wasm"):
            return self._get_wasm_intrinsics()
        else:
            return self._get_generic_intrinsics()

    def _get_x86_intrinsics(self) -> Dict[str, str]:
        """获取 x86 SIMD intrinsic 映射"""
        return {
            "add": "llvm.x86.sse.add.ps"
            if self.vector_width == 4
            else "llvm.x86.avx.add.ps.256",
            "sub": "llvm.x86.sse.sub.ps",
            "mul": "llvm.x86.sse.mul.ps",
            "div": "llvm.x86.sse.div.ps",
            "load": "llvm.masked.load",
            "store": "llvm.masked.store",
        }

    def _get_neon_intrinsics(self) -> Dict[str, str]:
        """获取 ARM NEON intrinsic 映射"""
        return {
            "add": "llvm.aarch64.neon.add",
            "sub": "llvm.aarch64.neon.sub",
            "mul": "llvm.aarch64.neon.mul",
            "div": "llvm.aarch64.neon.fdiv",
            "load": "llvm.masked.load",
            "store": "llvm.masked.store",
        }

    def _get_rvv_intrinsics(self) -> Dict[str, str]:
        """获取 RISC-V RVV intrinsic 映射"""
        return {
            "add": "llvm.riscv.vadd",
            "sub": "llvm.riscv.vsub",
            "mul": "llvm.riscv.vmulo",
            "div": "llvm.riscv.vfdiv",
            "load": "llvm.riscv.vle",
            "store": "llvm.riscv.vse",
        }

    def _get_wasm_intrinsics(self) -> Dict[str, str]:
        """获取 WebAssembly SIMD intrinsic 映射"""
        return {
            "add": "llvm.wasm.simd.add",
            "sub": "llvm.wasm.simd.sub",
            "mul": "llvm.wasm.simd.mul",
            "div": "llvm.wasm.simd.div",
            "load": "llvm.wasm.simd.load",
            "store": "llvm.wasm.simd.store",
        }

    def _get_generic_intrinsics(self) -> Dict[str, str]:
        """获取通用 SIMD intrinsic 映射"""
        return {
            "add": "llvm.vector.add",
            "sub": "llvm.vector.sub",
            "mul": "llvm.vector.mul",
            "div": "llvm.vector.div",
            "load": "llvm.masked.load",
            "store": "llvm.masked.store",
        }

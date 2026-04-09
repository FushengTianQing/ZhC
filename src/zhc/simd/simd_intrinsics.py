# -*- coding: utf-8 -*-
"""
ZhC SIMD Intrinsic 函数定义

定义跨平台的 SIMD intrinsic 函数，支持目标特定的优化。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

from .vector_builder import VectorTypeKind


class SIMDArchitecture(Enum):
    """SIMD 架构"""

    SSE = "sse"  # x86 SSE
    SSE2 = "sse2"
    SSE3 = "sse3"
    SSSE3 = "ssse3"
    SSE4_1 = "sse4.1"
    SSE4_2 = "sse4.2"
    AVX = "avx"  # Advanced Vector Extensions
    AVX2 = "avx2"
    AVX512 = "avx512"  # AVX-512
    NEON = "neon"  # ARM NEON
    SVE = "sve"  # ARM SVE
    RVV = "rvv"  # RISC-V Vector
    SIMD128 = "simd128"  # WebAssembly SIMD128


@dataclass
class SIMDIntrinsic:
    """
    SIMD Intrinsic 函数定义
    """

    name: str  # 函数名
    operation: str  # 操作类型
    input_types: List[VectorTypeKind]  # 输入类型
    output_type: VectorTypeKind  # 输出类型
    architectures: List[SIMDArchitecture]  # 支持的架构
    llvm_intrinsic: str  # 对应的 LLVM intrinsic
    description: str = ""  # 描述

    def is_supported(self, arch: SIMDArchitecture) -> bool:
        """检查是否支持指定架构"""
        return arch in self.architectures


class SIMDIntrinsicRegistry:
    """
    SIMD Intrinsic 注册表

    管理所有 SIMD intrinsic 函数。
    """

    _intrinsics: Dict[str, SIMDIntrinsic] = {}
    _initialized: bool = False

    @classmethod
    def _init(cls) -> None:
        """初始化 intrinsic 注册表"""
        if cls._initialized:
            return

        # ========== 加载操作 ==========
        cls._register(
            SIMDIntrinsic(
                name="simd_load_f32",
                operation="load",
                input_types=[VectorTypeKind.FLOAT32],
                output_type=VectorTypeKind.FLOAT32,
                architectures=[
                    SIMDArchitecture.SSE,
                    SIMDArchitecture.AVX,
                    SIMDArchitecture.NEON,
                    SIMDArchitecture.SIMD128,
                ],
                llvm_intrinsic="llvm.masked.load",
                description="加载浮点向量",
            )
        )

        cls._register(
            SIMDIntrinsic(
                name="simd_load_i32",
                operation="load",
                input_types=[VectorTypeKind.INT32],
                output_type=VectorTypeKind.INT32,
                architectures=[
                    SIMDArchitecture.SSE2,
                    SIMDArchitecture.AVX,
                    SIMDArchitecture.NEON,
                    SIMDArchitecture.SIMD128,
                ],
                llvm_intrinsic="llvm.masked.load",
                description="加载整数向量",
            )
        )

        # ========== 存储操作 ==========
        cls._register(
            SIMDIntrinsic(
                name="simd_store_f32",
                operation="store",
                input_types=[VectorTypeKind.FLOAT32],
                output_type=VectorTypeKind.FLOAT32,
                architectures=[
                    SIMDArchitecture.SSE,
                    SIMDArchitecture.AVX,
                    SIMDArchitecture.NEON,
                    SIMDArchitecture.SIMD128,
                ],
                llvm_intrinsic="llvm.masked.store",
                description="存储浮点向量",
            )
        )

        # ========== 加法 ==========
        cls._register(
            SIMDIntrinsic(
                name="simd_add_f32",
                operation="add",
                input_types=[VectorTypeKind.FLOAT32, VectorTypeKind.FLOAT32],
                output_type=VectorTypeKind.FLOAT32,
                architectures=[
                    SIMDArchitecture.SSE,
                    SIMDArchitecture.AVX,
                    SIMDArchitecture.NEON,
                    SIMDArchitecture.SIMD128,
                    SIMDArchitecture.RVV,
                ],
                llvm_intrinsic="llvm.fadd",
                description="向量浮点加法",
            )
        )

        cls._register(
            SIMDIntrinsic(
                name="simd_add_i32",
                operation="add",
                input_types=[VectorTypeKind.INT32, VectorTypeKind.INT32],
                output_type=VectorTypeKind.INT32,
                architectures=[
                    SIMDArchitecture.SSE2,
                    SIMDArchitecture.AVX,
                    SIMDArchitecture.NEON,
                    SIMDArchitecture.SIMD128,
                    SIMDArchitecture.RVV,
                ],
                llvm_intrinsic="llvm.add",
                description="向量整数加法",
            )
        )

        # ========== 乘法 ==========
        cls._register(
            SIMDIntrinsic(
                name="simd_mul_f32",
                operation="mul",
                input_types=[VectorTypeKind.FLOAT32, VectorTypeKind.FLOAT32],
                output_type=VectorTypeKind.FLOAT32,
                architectures=[
                    SIMDArchitecture.SSE,
                    SIMDArchitecture.AVX,
                    SIMDArchitecture.NEON,
                    SIMDArchitecture.SIMD128,
                    SIMDArchitecture.RVV,
                ],
                llvm_intrinsic="llvm.fmul",
                description="向量浮点乘法",
            )
        )

        cls._register(
            SIMDIntrinsic(
                name="simd_mul_i32",
                operation="mul",
                input_types=[VectorTypeKind.INT32, VectorTypeKind.INT32],
                output_type=VectorTypeKind.INT32,
                architectures=[
                    SIMDArchitecture.SSE2,
                    SIMDArchitecture.AVX,
                    SIMDArchitecture.NEON,
                    SIMDArchitecture.SIMD128,
                    SIMDArchitecture.RVV,
                ],
                llvm_intrinsic="llvm.mul",
                description="向量整数乘法",
            )
        )

        # ========== 归约操作 ==========
        cls._register(
            SIMDIntrinsic(
                name="simd_reduce_add_f32",
                operation="reduce_add",
                input_types=[VectorTypeKind.FLOAT32],
                output_type=VectorTypeKind.FLOAT32,
                architectures=[
                    SIMDArchitecture.SSE,
                    SIMDArchitecture.AVX,
                    SIMDArchitecture.NEON,
                    SIMDArchitecture.SIMD128,
                    SIMDArchitecture.RVV,
                ],
                llvm_intrinsic="llvm.vector.reduce.fadd",
                description="向量浮点归约加法",
            )
        )

        cls._register(
            SIMDIntrinsic(
                name="simd_reduce_add_i32",
                operation="reduce_add",
                input_types=[VectorTypeKind.INT32],
                output_type=VectorTypeKind.INT32,
                architectures=[
                    SIMDArchitecture.SSE2,
                    SIMDArchitecture.AVX,
                    SIMDArchitecture.NEON,
                    SIMDArchitecture.SIMD128,
                    SIMDArchitecture.RVV,
                ],
                llvm_intrinsic="llvm.vector.reduce.add",
                description="向量整数归约加法",
            )
        )

        # ========== 比较操作 ==========
        cls._register(
            SIMDIntrinsic(
                name="simd_cmp_gt_f32",
                operation="cmp_gt",
                input_types=[VectorTypeKind.FLOAT32, VectorTypeKind.FLOAT32],
                output_type=VectorTypeKind.INT32,
                architectures=[
                    SIMDArchitecture.SSE,
                    SIMDArchitecture.AVX,
                    SIMDArchitecture.NEON,
                    SIMDArchitecture.SIMD128,
                    SIMDArchitecture.RVV,
                ],
                llvm_intrinsic="llvm.fcmp",
                description="向量浮点大于比较",
            )
        )

        cls._initialized = True

    @classmethod
    def _register(cls, intrinsic: SIMDIntrinsic) -> None:
        """注册 intrinsic"""
        cls._intrinsics[intrinsic.name] = intrinsic

    @classmethod
    def get(cls, name: str) -> Optional[SIMDIntrinsic]:
        """
        获取 intrinsic

        Args:
            name: intrinsic 名称

        Returns:
            SIMDIntrinsic 对象，如果不存在返回 None
        """
        cls._init()
        return cls._intrinsics.get(name)

    @classmethod
    def get_for_arch(
        cls, operation: str, vec_type: VectorTypeKind, arch: SIMDArchitecture
    ) -> Optional[SIMDIntrinsic]:
        """
        获取指定架构的 intrinsic

        Args:
            operation: 操作类型
            vec_type: 向量类型
            arch: 目标架构

        Returns:
            SIMDIntrinsic 对象
        """
        cls._init()

        # 查找匹配的 intrinsic
        for intrinsic in cls._intrinsics.values():
            if intrinsic.operation == operation:
                if vec_type in intrinsic.input_types:
                    if intrinsic.is_supported(arch):
                        return intrinsic

        return None

    @classmethod
    def list_by_arch(cls, arch: SIMDArchitecture) -> List[SIMDIntrinsic]:
        """列出指定架构支持的 intrinsic"""
        cls._init()
        return [i for i in cls._intrinsics.values() if i.is_supported(arch)]

    @classmethod
    def list_operations(cls) -> List[str]:
        """列出所有操作类型"""
        cls._init()
        return list(set(i.operation for i in cls._intrinsics.values()))


def get_intrinsic(
    operation: str,
    vec_type: VectorTypeKind,
    arch: SIMDArchitecture = SIMDArchitecture.SSE,
) -> Optional[SIMDIntrinsic]:
    """
    获取 SIMD intrinsic

    Args:
        operation: 操作类型
        vec_type: 向量类型
        arch: 目标架构

    Returns:
        SIMDIntrinsic 对象
    """
    return SIMDIntrinsicRegistry.get_for_arch(operation, vec_type, arch)

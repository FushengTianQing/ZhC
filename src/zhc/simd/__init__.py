# -*- coding: utf-8 -*-
"""
ZhC SIMD 向量化模块

实现自动向量化功能，支持 SSE/AVX/NEON/RVV/SIMD128 等 SIMD 指令集。

作者：远
日期：2026-04-09
"""

from .vectorization_pass import (
    VectorizationPass,
    VectorizationConfig,
    VectorizationResult,
)

from .loop_analyzer import (
    Loop,
    LoopInfo,
    LoopAnalyzer,
    InductionVariable,
)

from .vector_builder import (
    VectorType,
    VectorBuilder,
    VectorizedLoop,
)

from .cost_model import (
    CostModel,
    VectorizationCost,
)

from .simd_intrinsics import (
    SIMDIntrinsic,
    SIMDIntrinsicRegistry,
    get_intrinsic,
)

__all__ = [
    # 向量化 Pass
    "VectorizationPass",
    "VectorizationConfig",
    "VectorizationResult",
    # 循环分析
    "Loop",
    "LoopInfo",
    "LoopAnalyzer",
    "InductionVariable",
    # 向量化构建
    "VectorType",
    "VectorBuilder",
    "VectorizedLoop",
    # 成本模型
    "CostModel",
    "VectorizationCost",
    # SIMD Intrinsic
    "SIMDIntrinsic",
    "SIMDIntrinsicRegistry",
    "get_intrinsic",
]

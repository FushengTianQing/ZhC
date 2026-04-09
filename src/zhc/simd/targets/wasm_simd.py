# -*- coding: utf-8 -*-
"""
ZhC WebAssembly SIMD 目标平台

支持 WebAssembly SIMD128 指令集。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass
from typing import List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class WasmSIMDFeature(Enum):
    """WebAssembly SIMD 特性"""

    SIMD128 = "simd128"
    RELAXED_SIMD = "relaxed-simd"


@dataclass
class WasmSIMDConfig:
    """WebAssembly SIMD 配置"""

    features: List[WasmSIMDFeature]
    vector_width: int
    vector_bits: int


class WasmSIMDTarget:
    """
    WebAssembly SIMD 目标平台

    提供 WebAssembly SIMD128 的具体实现。
    """

    def __init__(self, target_arch: str = "wasm32"):
        self.target_arch = target_arch
        self.features = self._detect_features(target_arch)
        self.config = self._create_config()

    def _detect_features(self, arch: str) -> List[WasmSIMDFeature]:
        """检测目标架构支持的特性"""
        features = []
        arch_lower = arch.lower()

        # SIMD128 是基础特性
        features.append(WasmSIMDFeature.SIMD128)

        # 检测 relaxed SIMD
        if "relaxed" in arch_lower:
            features.append(WasmSIMDFeature.RELAXED_SIMD)

        return features

    def _create_config(self) -> WasmSIMDConfig:
        """创建配置"""
        return WasmSIMDConfig(
            features=self.features,
            vector_width=4,  # 128 位 = 4 x float32
            vector_bits=128,
        )

    def get_vector_type(self, element_type: str, width: int) -> str:
        """获取向量类型"""
        # WebAssembly 使用 v128 作为向量类型
        return "v128"

    def get_load_instruction(self) -> str:
        """获取加载指令"""
        return "v128.load"

    def get_store_instruction(self) -> str:
        """获取存储指令"""
        return "v128.store"

    def get_add_instruction(self, element_type: str) -> str:
        """获取加法指令"""
        type_map = {
            "float": "f32x4.add",
            "double": "f64x2.add",
            "i32": "i32x4.add",
            "i64": "i64x2.add",
            "i8": "i8x16.add",
            "i16": "i16x8.add",
        }
        return type_map.get(element_type, "f32x4.add")

    def get_mul_instruction(self, element_type: str) -> str:
        """获取乘法指令"""
        type_map = {
            "float": "f32x4.mul",
            "double": "f64x2.mul",
            "i32": "i32x4.mul",
            "i64": "i64x2.mul",
            "i16": "i16x8.mul",
        }
        return type_map.get(element_type, "f32x4.mul")

    def get_dot_product_instruction(self) -> str:
        """获取点积指令"""
        return "i32x4.dot_i16x8_s"

    def get_shuffle_instruction(self) -> str:
        """获取混排指令"""
        return "i8x16.shuffle"

    def get_bitmask_instruction(self) -> str:
        """获取位掩码指令"""
        return "i32x4.bitmask"

    def supports_feature(self, feature: WasmSIMDFeature) -> bool:
        """检查是否支持指定特性"""
        return feature in self.features

    def get_vector_width(self) -> int:
        """获取向量宽度"""
        return self.config.vector_width

    def get_vector_bits(self) -> int:
        """获取向量位数"""
        return self.config.vector_bits

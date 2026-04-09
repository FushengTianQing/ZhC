# -*- coding: utf-8 -*-
"""
ZhC ARM NEON 目标平台

支持 ARM NEON 和 SVE 指令集。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass
from typing import List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ARMNeonFeature(Enum):
    """ARM NEON 特性"""

    NEON = "neon"
    NEON_FP16 = "fp16"
    NEON_DOTPROD = "dotprod"
    NEON_I8MM = "i8mm"
    SVE = "sve"
    SVE2 = "sve2"


@dataclass
class ARMNeonConfig:
    """ARM NEON 配置"""

    features: List[ARMNeonFeature]
    vector_width: int
    supports_masking: bool
    sve_vector_bits: int  # SVE 可变宽度


class ARMNeonTarget:
    """
    ARM NEON 目标平台

    提供 NEON 和 SVE 指令集的具体实现。
    """

    def __init__(self, target_arch: str = "aarch64"):
        self.target_arch = target_arch
        self.features = self._detect_features(target_arch)
        self.config = self._create_config()

    def _detect_features(self, arch: str) -> List[ARMNeonFeature]:
        """检测目标架构支持的特性"""
        features = []
        arch_lower = arch.lower()

        # NEON 是 AArch64 的基础特性
        if "aarch64" in arch_lower or "arm64" in arch_lower:
            features.append(ARMNeonFeature.NEON)

        # 检测其他特性
        if "fp16" in arch_lower:
            features.append(ARMNeonFeature.NEON_FP16)
        if "dotprod" in arch_lower:
            features.append(ARMNeonFeature.NEON_DOTPROD)
        if "i8mm" in arch_lower:
            features.append(ARMNeonFeature.NEON_I8MM)
        if "sve2" in arch_lower:
            features.append(ARMNeonFeature.SVE2)
            features.append(ARMNeonFeature.SVE)
        elif "sve" in arch_lower:
            features.append(ARMNeonFeature.SVE)

        return features

    def _create_config(self) -> ARMNeonConfig:
        """创建配置"""
        vector_width = 4  # NEON 默认 128 位 = 4 x float32
        supports_masking = ARMNeonFeature.SVE in self.features
        sve_vector_bits = 128  # 默认 SVE 宽度

        if ARMNeonFeature.SVE in self.features:
            sve_vector_bits = 256  # 假设 256 位 SVE

        return ARMNeonConfig(
            features=self.features,
            vector_width=vector_width,
            supports_masking=supports_masking,
            sve_vector_bits=sve_vector_bits,
        )

    def get_vector_type(self, element_type: str, width: int) -> str:
        """获取向量类型"""
        type_map = {
            "float": "float",
            "double": "double",
            "i8": "i8",
            "i16": "i16",
            "i32": "i32",
            "i64": "i64",
        }
        base_type = type_map.get(element_type, "float")
        return f"<{width} x {base_type}>"

    def get_load_instruction(self, vec_type: str) -> str:
        """获取加载指令"""
        if "float" in vec_type:
            return "ldr q"
        return "ldr q"

    def get_store_instruction(self, vec_type: str) -> str:
        """获取存储指令"""
        return "str q"

    def get_add_instruction(self, vec_type: str) -> str:
        """获取加法指令"""
        if "float" in vec_type:
            return "fadd v"
        elif "double" in vec_type:
            return "fadd v"
        else:
            return "add v"

    def get_mul_instruction(self, vec_type: str) -> str:
        """获取乘法指令"""
        if "float" in vec_type or "double" in vec_type:
            return "fmul v"
        else:
            return "mul v"

    def get_fmla_instruction(self) -> str:
        """获取 FMLA 指令（乘加融合）"""
        return "fmla v"

    def supports_feature(self, feature: ARMNeonFeature) -> bool:
        """检查是否支持指定特性"""
        return feature in self.features

    def get_vector_width(self) -> int:
        """获取向量宽度"""
        return self.config.vector_width

    def uses_sve(self) -> bool:
        """是否使用 SVE"""
        return ARMNeonFeature.SVE in self.features

# -*- coding: utf-8 -*-
"""
ZhC x86 SIMD 目标平台

支持 SSE、SSE2、SSE4、AVX、AVX2、AVX-512 指令集。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class X86SIMDFeature(Enum):
    """x86 SIMD 特性"""

    SSE = "sse"
    SSE2 = "sse2"
    SSE3 = "sse3"
    SSSE3 = "ssse3"
    SSE41 = "sse4.1"
    SSE42 = "sse4.2"
    AVX = "avx"
    AVX2 = "avx2"
    AVX512F = "avx512f"
    AVX512DQ = "avx512dq"
    AVX512BW = "avx512bw"
    AVX512VL = "avx512vl"
    FMA = "fma"


@dataclass
class X86SIMDConfig:
    """x86 SIMD 配置"""

    features: List[X86SIMDFeature]
    vector_width: int
    supports_masking: bool
    supports_gather_scatter: bool
    max_vector_bits: int


class X86SIMDTarget:
    """
    x86 SIMD 目标平台

    提供 SSE/AVX/AVX-512 指令集的具体实现。
    """

    # 特性到向量宽度的映射
    FEATURE_WIDTH = {
        X86SIMDFeature.SSE: 128,
        X86SIMDFeature.SSE2: 128,
        X86SIMDFeature.SSE3: 128,
        X86SIMDFeature.SSSE3: 128,
        X86SIMDFeature.SSE41: 128,
        X86SIMDFeature.SSE42: 128,
        X86SIMDFeature.AVX: 256,
        X86SIMDFeature.AVX2: 256,
        X86SIMDFeature.AVX512F: 512,
        X86SIMDFeature.AVX512DQ: 512,
        X86SIMDFeature.AVX512BW: 512,
        X86SIMDFeature.AVX512VL: 512,
    }

    # 特性依赖关系
    FEATURE_DEPS = {
        X86SIMDFeature.SSE2: [X86SIMDFeature.SSE],
        X86SIMDFeature.SSE3: [X86SIMDFeature.SSE2],
        X86SIMDFeature.SSSE3: [X86SIMDFeature.SSE3],
        X86SIMDFeature.SSE41: [X86SIMDFeature.SSSE3],
        X86SIMDFeature.SSE42: [X86SIMDFeature.SSE41],
        X86SIMDFeature.AVX: [X86SIMDFeature.SSE42],
        X86SIMDFeature.AVX2: [X86SIMDFeature.AVX],
        X86SIMDFeature.AVX512F: [X86SIMDFeature.AVX2],
        X86SIMDFeature.FMA: [X86SIMDFeature.AVX],
    }

    def __init__(self, target_arch: str = "x86_64"):
        self.target_arch = target_arch
        self.features = self._detect_features(target_arch)
        self.config = self._create_config()

    def _detect_features(self, arch: str) -> List[X86SIMDFeature]:
        """检测目标架构支持的特性"""
        features = []
        arch_lower = arch.lower()

        # 基础特性
        features.append(X86SIMDFeature.SSE)
        features.append(X86SIMDFeature.SSE2)

        # 根据架构名称推断
        if "sse3" in arch_lower or "ssse3" in arch_lower:
            features.append(X86SIMDFeature.SSE3)
        if "ssse3" in arch_lower:
            features.append(X86SIMDFeature.SSSE3)
        if "sse4" in arch_lower or "sse4.1" in arch_lower:
            features.append(X86SIMDFeature.SSE41)
        if "sse4.2" in arch_lower:
            features.append(X86SIMDFeature.SSE42)
        if "avx512" in arch_lower:
            features.append(X86SIMDFeature.AVX512F)
            features.append(X86SIMDFeature.AVX512DQ)
            features.append(X86SIMDFeature.AVX512BW)
            features.append(X86SIMDFeature.AVX512VL)
        if "avx2" in arch_lower or "avx512" in arch_lower:
            features.append(X86SIMDFeature.AVX2)
        if "avx" in arch_lower:
            features.append(X86SIMDFeature.AVX)
        if "fma" in arch_lower:
            features.append(X86SIMDFeature.FMA)

        return features

    def _create_config(self) -> X86SIMDConfig:
        """创建配置"""
        max_bits = 128
        for feature in self.features:
            bits = self.FEATURE_WIDTH.get(feature, 128)
            max_bits = max(max_bits, bits)

        # 计算向量宽度（以 float32 为基准）
        vector_width = max_bits // 32

        # 检查是否支持掩码
        supports_masking = X86SIMDFeature.AVX512F in self.features

        # 检查是否支持 gather/scatter
        supports_gather_scatter = X86SIMDFeature.AVX2 in self.features

        return X86SIMDConfig(
            features=self.features,
            vector_width=vector_width,
            supports_masking=supports_masking,
            supports_gather_scatter=supports_gather_scatter,
            max_vector_bits=max_bits,
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

    def get_load_instruction(self, vec_type: str, aligned: bool = True) -> str:
        """获取加载指令"""
        width = self._extract_width(vec_type)

        if width <= 4:
            if aligned:
                return "movaps" if "float" in vec_type else "movapd"
            else:
                return "movups" if "float" in vec_type else "movupd"
        elif width <= 8:
            if aligned:
                return "vmovaps" if "float" in vec_type else "vmovapd"
            else:
                return "vmovups" if "float" in vec_type else "vmovupd"
        else:
            return "vmovaps" if aligned else "vmovups"

    def get_store_instruction(self, vec_type: str, aligned: bool = True) -> str:
        """获取存储指令"""
        return self.get_load_instruction(vec_type, aligned)

    def get_add_instruction(self, vec_type: str) -> str:
        """获取加法指令"""
        width = self._extract_width(vec_type)

        if width <= 4:
            return "addps" if "float" in vec_type else "addpd"
        else:
            return "vaddps" if "float" in vec_type else "vaddpd"

    def get_mul_instruction(self, vec_type: str) -> str:
        """获取乘法指令"""
        width = self._extract_width(vec_type)

        if width <= 4:
            return "mulps" if "float" in vec_type else "mulpd"
        else:
            return "vmulps" if "float" in vec_type else "vmulpd"

    def get_fma_instruction(self, vec_type: str) -> Optional[str]:
        """获取 FMA 指令"""
        if X86SIMDFeature.FMA not in self.features:
            return None

        width = self._extract_width(vec_type)
        if "float" in vec_type:
            return "vfmadd231ps" if width > 4 else "vfmadd213ps"
        else:
            return "vfmadd231pd" if width > 4 else "vfmadd213pd"

    def get_gather_instruction(self, vec_type: str) -> Optional[str]:
        """获取 gather 指令"""
        if not self.config.supports_gather_scatter:
            return None

        width = self._extract_width(vec_type)
        if width <= 4:
            return "vgatherdps" if "float" in vec_type else "vgatherdpd"
        elif width <= 8:
            return "vgatherdps" if "float" in vec_type else "vgatherdpd"
        else:
            return "vgatherdps"

    def get_scatter_instruction(self, vec_type: str) -> Optional[str]:
        """获取 scatter 指令"""
        if X86SIMDFeature.AVX512F not in self.features:
            return None

        return "vscatterdps" if "float" in vec_type else "vscatterdpd"

    def _extract_width(self, vec_type: str) -> int:
        """从向量类型提取宽度"""
        if "<" in vec_type and "x" in vec_type:
            parts = vec_type.split("<")[1].split("x")
            return int(parts[0].strip())
        return 4

    def supports_feature(self, feature: X86SIMDFeature) -> bool:
        """检查是否支持指定特性"""
        return feature in self.features

    def get_target_features_string(self) -> str:
        """获取目标特性字符串"""
        return ",".join(f.value for f in self.features)

    def get_vector_width(self) -> int:
        """获取向量宽度"""
        return self.config.vector_width

    def get_max_vector_bits(self) -> int:
        """获取最大向量位数"""
        return self.config.max_vector_bits

# -*- coding: utf-8 -*-
"""
ZhC RISC-V RVV 目标平台

支持 RISC-V 向量扩展 (RVV)。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass
from typing import List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RVVFeature(Enum):
    """RVV 特性"""

    V = "v"  # 基础向量扩展
    ZVE32X = "zve32x"  # 最小向量扩展
    ZVE64X = "zve64x"  # 64 位向量扩展
    ZVL32B = "zvl32b"  # 最小向量长度 32 字节
    ZVL64B = "zvl64b"
    ZVL128B = "zvl128b"
    ZVL256B = "zvl256b"
    ZVL512B = "zvl512b"


@dataclass
class RVVConfig:
    """RVV 配置"""

    features: List[RVVFeature]
    vlen: int  # 向量长度（位）
    elen: int  # 元素长度（位）
    supports_masking: bool


class RiscVRVVTarget:
    """
    RISC-V RVV 目标平台

    提供 RISC-V 向量扩展的具体实现。
    """

    def __init__(self, target_arch: str = "riscv64"):
        self.target_arch = target_arch
        self.features = self._detect_features(target_arch)
        self.config = self._create_config()

    def _detect_features(self, arch: str) -> List[RVVFeature]:
        """检测目标架构支持的特性"""
        features = []
        arch_lower = arch.lower()

        # 基础向量扩展
        if "rvv" in arch_lower or "_v" in arch_lower:
            features.append(RVVFeature.V)

        # 向量长度特性
        if "zvl128b" in arch_lower:
            features.append(RVVFeature.ZVL128B)
        elif "zvl64b" in arch_lower:
            features.append(RVVFeature.ZVL64B)
        elif "zvl32b" in arch_lower:
            features.append(RVVFeature.ZVL32B)

        # 元素长度特性
        if "zve64x" in arch_lower:
            features.append(RVVFeature.ZVE64X)
        elif "zve32x" in arch_lower:
            features.append(RVVFeature.ZVE32X)

        # 默认特性
        if RVVFeature.V not in features:
            features.append(RVVFeature.V)
        if RVVFeature.ZVL128B not in features:
            features.append(RVVFeature.ZVL128B)

        return features

    def _create_config(self) -> RVVConfig:
        """创建配置"""
        vlen = 128  # 默认向量长度
        elen = 64  # 默认元素长度

        for feature in self.features:
            if feature == RVVFeature.ZVL256B:
                vlen = 256
            elif feature == RVVFeature.ZVL512B:
                vlen = 512
            elif feature == RVVFeature.ZVE64X:
                elen = 64

        return RVVConfig(
            features=self.features,
            vlen=vlen,
            elen=elen,
            supports_masking=True,  # RVV 始终支持掩码
        )

    def get_vector_type(self, element_type: str, width: int) -> str:
        """获取向量类型"""
        # RVV 使用可变向量类型
        type_map = {
            "float": "float",
            "double": "double",
            "i8": "i8",
            "i16": "i16",
            "i32": "i32",
            "i64": "i64",
        }
        base_type = type_map.get(element_type, "float")
        # RVV 使用 nxvMxT 形式
        return f"nxv{width}x{base_type}"

    def get_load_instruction(self) -> str:
        """获取加载指令"""
        return "vle"

    def get_store_instruction(self) -> str:
        """获取存储指令"""
        return "vse"

    def get_add_instruction(self) -> str:
        """获取加法指令"""
        return "vadd"

    def get_mul_instruction(self) -> str:
        """获取乘法指令"""
        return "vmul"

    def get_fmacc_instruction(self) -> str:
        """获取乘加融合指令"""
        return "vfmacc"

    def get_vsetvli_instruction(self, element_type: str) -> str:
        """获取 vsetvli 指令"""
        type_map = {
            "float": "e32,m1",
            "double": "e64,m1",
            "i32": "e32,m1",
            "i64": "e64,m1",
        }
        config = type_map.get(element_type, "e32,m1")
        return f"vsetvli {config}"

    def supports_feature(self, feature: RVVFeature) -> bool:
        """检查是否支持指定特性"""
        return feature in self.features

    def get_vlen(self) -> int:
        """获取向量长度"""
        return self.config.vlen

    def get_elen(self) -> int:
        """获取元素长度"""
        return self.config.elen

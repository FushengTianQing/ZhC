# -*- coding: utf-8 -*-
"""
ZhC 向量宽度选择器

根据目标架构和运行时信息自动选择最优的 SIMD 向量宽度。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class VectorWidth(Enum):
    """SIMD 向量宽度枚举"""

    WIDTH_2 = 2
    WIDTH_4 = 4
    WIDTH_8 = 8
    WIDTH_16 = 16
    WIDTH_32 = 32
    WIDTH_64 = 64


@dataclass
class TargetVectorInfo:
    """目标平台的向量信息"""

    max_width: int  # 最大向量宽度（元素数）
    preferred_width: int  # 首选向量宽度
    element_size: int  # 元素大小（字节）
    supports_masking: bool  # 是否支持掩码
    supports_partial_vectors: bool  # 是否支持部分向量
    lane_count: int  # 硬件通道数
    throughput: float  # 相对吞吐量


@dataclass
class WidthSelectionResult:
    """向量宽度选择结果"""

    selected_width: int  # 选中的向量宽度
    reason: str  # 选择原因
    alternatives: List[Tuple[int, str]]  # 备选方案
    estimated_speedup: float  # 估计加速比
    alignment_requirement: int  # 对齐要求（字节）


class WidthSelector:
    """
    向量宽度选择器

    根据目标架构、数据类型、循环特性等因素选择最优的向量宽度。
    """

    # 各平台的默认向量信息
    TARGET_INFO: Dict[str, TargetVectorInfo] = {
        "x86_sse": TargetVectorInfo(
            max_width=4,
            preferred_width=4,
            element_size=4,
            supports_masking=True,
            supports_partial_vectors=False,
            lane_count=128,
            throughput=1.0,
        ),
        "x86_avx": TargetVectorInfo(
            max_width=8,
            preferred_width=8,
            element_size=4,
            supports_masking=True,
            supports_partial_vectors=True,
            lane_count=256,
            throughput=2.0,
        ),
        "x86_avx512": TargetVectorInfo(
            max_width=16,
            preferred_width=16,
            element_size=4,
            supports_masking=True,
            supports_partial_vectors=True,
            lane_count=512,
            throughput=4.0,
        ),
        "aarch64_neon": TargetVectorInfo(
            max_width=4,
            preferred_width=4,
            element_size=4,
            supports_masking=True,
            supports_partial_vectors=False,
            lane_count=128,
            throughput=1.0,
        ),
        "aarch64_sve": TargetVectorInfo(
            max_width=16,  # SVE 宽度可动态调整
            preferred_width=8,
            element_size=4,
            supports_masking=True,
            supports_partial_vectors=True,
            lane_count=128,  # 可变
            throughput=1.5,
        ),
        "riscv_rvv": TargetVectorInfo(
            max_width=32,  # RVV 最大可配置
            preferred_width=8,
            element_size=4,
            supports_masking=True,
            supports_partial_vectors=True,
            lane_count=128,  # 可配置
            throughput=1.5,
        ),
        "wasm_simd128": TargetVectorInfo(
            max_width=4,
            preferred_width=4,
            element_size=4,
            supports_masking=True,
            supports_partial_vectors=True,
            lane_count=128,
            throughput=1.0,
        ),
        "generic": TargetVectorInfo(
            max_width=4,
            preferred_width=4,
            element_size=4,
            supports_masking=True,
            supports_partial_vectors=True,
            lane_count=64,
            throughput=1.0,
        ),
    }

    def __init__(self, target_arch: str = "generic"):
        self.target_arch = target_arch
        self.target_info = self._get_target_info(target_arch)

    def _get_target_info(self, arch: str) -> TargetVectorInfo:
        """获取目标平台的向量信息"""
        arch_lower = arch.lower()

        # 精确匹配
        if arch_lower in self.TARGET_INFO:
            return self.TARGET_INFO[arch_lower]

        # 前缀匹配
        if "avx512" in arch_lower:
            return self.TARGET_INFO["x86_avx512"]
        elif "avx" in arch_lower:
            return self.TARGET_INFO["x86_avx"]
        elif "sse" in arch_lower:
            return self.TARGET_INFO["x86_sse"]
        elif "sve" in arch_lower:
            return self.TARGET_INFO["aarch64_sve"]
        elif "neon" in arch_lower or "aarch64" in arch_lower or "arm" in arch_lower:
            return self.TARGET_INFO["aarch64_neon"]
        elif "rvv" in arch_lower or "riscv" in arch_lower:
            return self.TARGET_INFO["riscv_rvv"]
        elif "wasm" in arch_lower:
            return self.TARGET_INFO["wasm_simd128"]

        return self.TARGET_INFO["generic"]

    def select_width(
        self,
        element_bits: int = 32,
        loop_trip_count: Optional[int] = None,
        alignment: int = 1,
        prefer_larger: bool = False,
    ) -> WidthSelectionResult:
        """
        选择最优向量宽度

        Args:
            element_bits: 元素位宽
            loop_trip_count: 循环次数（如果已知）
            alignment: 内存对齐要求
            prefer_larger: 是否偏好更大的宽度

        Returns:
            向量宽度选择结果
        """
        # 计算元素大小（字节）
        element_bytes = element_bits // 8

        # 计算各宽度的总位数
        max_bits = self.target_info.lane_count
        candidates = []

        # 生成候选宽度列表
        width = 2
        while width <= self.target_info.max_width:
            total_bytes = width * element_bytes
            if total_bytes <= max_bits:
                candidates.append(width)
            width *= 2

        if not candidates:
            candidates = [1]  # 至少支持标量

        # 考虑对齐要求
        candidates = self._filter_by_alignment(candidates, alignment)

        # 评估每个候选宽度
        scored_candidates: List[Tuple[int, float, str]] = []
        for width in candidates:
            score, reason = self._score_width(
                width,
                element_bytes,
                loop_trip_count,
                alignment,
            )
            scored_candidates.append((width, score, reason))

        # 按分数排序
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # 如果偏好更大宽度且分数相近，选择更大的
        if prefer_larger and len(scored_candidates) >= 2:
            top1 = scored_candidates[0]
            top2 = scored_candidates[1]
            if abs(top1[1] - top2[1]) < 0.1:
                scored_candidates[0] = top2
                scored_candidates[1] = top1

        # 提取结果
        best_width, best_score, best_reason = scored_candidates[0]

        alternatives = [
            (width, reason) for width, score, reason in scored_candidates[1:4]
        ]

        # 计算估计加速比
        speedup = self._estimate_speedup(best_width, loop_trip_count)

        # 计算对齐要求
        alignment_req = self._calculate_alignment(best_width, element_bytes)

        return WidthSelectionResult(
            selected_width=best_width,
            reason=best_reason,
            alternatives=alternatives,
            estimated_speedup=speedup,
            alignment_requirement=alignment_req,
        )

    def _filter_by_alignment(self, candidates: List[int], alignment: int) -> List[int]:
        """根据对齐要求过滤候选宽度"""
        # 最小对齐要求
        min_alignment = 16  # 大多数 SIMD 要求至少 16 字节对齐

        if alignment >= min_alignment:
            # 好，满足对齐要求
            return candidates
        elif alignment >= 8:
            # 勉强接受
            return candidates
        else:
            # 对齐不足，优先选择更小的宽度
            return sorted(candidates, key=lambda x: -x)[:3]

    def _score_width(
        self,
        width: int,
        element_bytes: int,
        trip_count: Optional[int],
        alignment: int,
    ) -> Tuple[float, str]:
        """评估向量宽度的分数"""
        score = 1.0
        reasons = []

        # 1. 与首选宽度匹配
        if width == self.target_info.preferred_width:
            score *= 1.5
            reasons.append("preferred_width")

        # 2. 循环次数匹配
        if trip_count is not None:
            if trip_count >= width * 2:
                score *= 1.3
                reasons.append("trip_count_sufficient")
            elif trip_count < width:
                score *= 0.7
                reasons.append("trip_count_small")

            # 整除检查
            if trip_count % width == 0:
                score *= 1.2
                reasons.append("aligned_trip_count")

        # 3. 对齐检查
        total_bytes = width * element_bytes
        if total_bytes % 16 == 0:
            score *= 1.1
            reasons.append("good_alignment")
        elif total_bytes % 8 == 0:
            score *= 1.0
        else:
            score *= 0.9
            reasons.append("poor_alignment")

        # 4. 吞吐量考虑
        if width <= 4:
            score *= self.target_info.throughput
        elif width <= 8:
            score *= self.target_info.throughput * 0.9
        else:
            score *= self.target_info.throughput * 0.8

        # 5. 避免过大的宽度（部分向量处理开销）
        if width > 8:
            score *= 0.9
            reasons.append("large_width_overhead")

        reason_str = ", ".join(reasons) if reasons else "default"
        return score, reason_str

    def _estimate_speedup(self, width: int, trip_count: Optional[int]) -> float:
        """估计使用给定宽度的加速比"""
        base_speedup = min(width, 4.0)  # 理论最大加速比

        # 考虑循环次数
        if trip_count is not None:
            if trip_count < width:
                return trip_count / width  # 无法充分利用向量宽度
            elif trip_count % width != 0:
                # 部分尾部处理开销
                remainder_ratio = (trip_count % width) / width
                base_speedup *= 1 - remainder_ratio * 0.1
        else:
            # 未知循环次数，保守估计
            base_speedup *= 0.8

        # 考虑目标平台吞吐量
        base_speedup *= self.target_info.throughput

        return base_speedup

    def _calculate_alignment(self, width: int, element_bytes: int) -> int:
        """计算给定宽度的对齐要求"""
        total_bytes = width * element_bytes

        # 最小对齐
        min_alignment = 16

        # 找到最小对齐要求（2的幂）
        alignment = min_alignment
        while alignment < total_bytes:
            alignment *= 2

        return alignment

    def get_optimal_unroll_factor(self, width: int, trip_count: Optional[int]) -> int:
        """
        获取最优的循环展开因子

        Args:
            width: 向量宽度
            trip_count: 循环次数

        Returns:
            推荐的展开因子
        """
        if trip_count is not None and trip_count >= width * 8:
            # 大循环可以考虑更大的展开因子
            if trip_count >= width * 16:
                return 4
            return 2

        return 1

    def supports_element_size(self, element_bits: int) -> bool:
        """检查是否支持给定的元素大小"""
        max_elements = self.target_info.lane_count // (element_bits // 8)
        return max_elements >= 1

    def get_max_elements(self, element_bits: int) -> int:
        """获取给定元素大小支持的最大元素数"""
        element_bytes = element_bits // 8
        return self.target_info.lane_count // element_bytes


def create_width_selector(target_arch: str = "generic") -> WidthSelector:
    """
    创建向量宽度选择器

    Args:
        target_arch: 目标架构

    Returns:
        WidthSelector 实例
    """
    return WidthSelector(target_arch)

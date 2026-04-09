# -*- coding: utf-8 -*-
"""
ZhC 向量化成本模型

评估循环向量化的收益，决定是否应进行向量化。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass

from .loop_analyzer import Loop


@dataclass
class VectorizationCost:
    """
    向量化成本分析结果
    """

    scalar_cost: float  # 标量成本
    vector_cost: float  # 向量成本
    benefit: float  # 收益比
    instructions_saved: int  # 节省的指令数
    overhead_cycles: int  # 向量化开销周期数
    throughput_improvement: float  # 吞吐量改善

    def __str__(self) -> str:
        return (
            f"VectorizationCost(scalar={self.scalar_cost}, "
            f"vector={self.vector_cost}, benefit={self.benefit:.2f}x)"
        )


class CostModel:
    """
    向量化成本模型

    评估向量化循环的成本和收益。
    """

    # 指令成本表（相对单位）
    SCALAR_COSTS = {
        "load": 4,
        "store": 4,
        "add": 1,
        "sub": 1,
        "mul": 3,
        "div": 10,
        "cmp": 1,
        "br": 2,
        "phi": 1,
    }

    VECTOR_COSTS = {
        "load": 2,  # 一次加载多个元素
        "store": 2,
        "add": 0.5,  # SIMD 并行
        "sub": 0.5,
        "mul": 1,
        "div": 3,
        "cmp": 0.5,
    }

    # 向量化开销
    SETUP_OVERHEAD = 10  # 设置掩码等
    GATHER_SCATTER_OVERHEAD = 5  # 非连续内存访问
    REDUCTION_OVERHEAD = 3  # 归约操作

    def __init__(self, target_arch: str = "generic"):
        self.target_arch = target_arch
        self._adjust_costs_for_target()

    def _adjust_costs_for_target(self) -> None:
        """根据目标架构调整成本"""
        if self.target_arch.startswith("x86"):
            # x86 架构优化
            if "avx" in self.target_arch:
                self.VECTOR_COSTS["load"] = 1
                self.VECTOR_COSTS["store"] = 1
        elif self.target_arch.startswith("aarch64"):
            # ARM NEON 优化
            self.VECTOR_COSTS["load"] = 1
            self.VECTOR_COSTS["store"] = 1
            self.VECTOR_COSTS["mul"] = 0.5  # NEON 乘法优化

    def analyze_loop(self, loop: Loop) -> VectorizationCost:
        """
        分析循环向量化的成本

        Args:
            loop: 循环信息

        Returns:
            成本分析结果
        """
        # 计算标量成本
        scalar_cost = self._calculate_scalar_cost(loop)

        # 计算向量成本
        vector_cost = self._calculate_vector_cost(loop)

        # 计算开销
        overhead = self._calculate_overhead(loop)
        vector_cost += overhead

        # 计算收益
        trip_count = loop.trip_count or loop.trip_count_estimate or 100
        benefit = scalar_cost / max(vector_cost, 1) if vector_cost > 0 else 1.0

        # 计算指令节省
        instructions_saved = int((scalar_cost - vector_cost) * trip_count / 10)

        return VectorizationCost(
            scalar_cost=scalar_cost,
            vector_cost=vector_cost,
            benefit=benefit,
            instructions_saved=max(0, instructions_saved),
            overhead_cycles=int(overhead),
            throughput_improvement=benefit - 1.0,
        )

    def _calculate_scalar_cost(self, loop: Loop) -> float:
        """计算标量成本"""
        cost = 0.0

        # 加载/存储成本
        cost += loop.num_loads * self.SCALAR_COSTS["load"]
        cost += loop.num_stores * self.SCALAR_COSTS["store"]

        # 基本指令成本
        # 假设每条指令有 3 次算术操作
        arith_ops = loop.num_instructions - loop.num_loads - loop.num_stores
        cost += arith_ops * 2  # 平均成本

        # 循环控制成本
        cost += 2 * self.SCALAR_COSTS["br"]
        cost += self.SCALAR_COSTS["cmp"]

        return cost

    def _calculate_vector_cost(self, loop: Loop) -> float:
        """计算向量成本"""
        cost = 0.0
        vector_width = self._get_vector_width()

        # 向量化后的加载/存储（并行）
        if loop.num_loads > 0:
            cost += (loop.num_loads / vector_width) * self.VECTOR_COSTS["load"]
        if loop.num_stores > 0:
            cost += (loop.num_stores / vector_width) * self.VECTOR_COSTS["store"]

        # 向量化后的算术运算
        arith_ops = loop.num_instructions - loop.num_loads - loop.num_stores
        cost += arith_ops * 1  # 平均 SIMD 成本

        # 循环控制（每次迭代一次）
        cost += 1 * self.VECTOR_COSTS["br"]

        return cost

    def _calculate_overhead(self, loop: Loop) -> float:
        """计算向量化开销"""
        overhead = self.SETUP_OVERHEAD

        # 检查是否需要 gather/scatter
        if not self._is_contiguous_access(loop):
            overhead += self.GATHER_SCATTER_OVERHEAD

        # 检查是否需要归约
        if self._has_reduction(loop):
            overhead += self.REDUCTION_OVERHEAD

        return overhead

    def _get_vector_width(self) -> int:
        """获取向量宽度"""
        if self.target_arch.startswith("x86"):
            if "avx512" in self.target_arch:
                return 16
            elif "avx" in self.target_arch:
                return 8
            return 4
        elif self.target_arch.startswith("aarch64"):
            return 4  # NEON 128位
        elif self.target_arch.startswith("riscv"):
            return 8  # RVV 默认
        elif self.target_arch.startswith("wasm"):
            return 4  # SIMD128
        return 4

    def _is_contiguous_access(self, loop: Loop) -> bool:
        """
        检查是否为连续内存访问

        简化实现：假设所有归纳变量都是连续的
        """
        # 实际实现需要分析内存访问模式
        return True

    def _has_reduction(self, loop: Loop) -> bool:
        """
        检查是否有归约操作

        简化实现
        """
        # 实际实现需要分析循环中的操作
        return False

    def estimate_speedup(self, loop: Loop, vector_width: int = 4) -> float:
        """
        估计加速比

        Args:
            loop: 循环信息
            vector_width: 向量宽度

        Returns:
            估计的加速比
        """
        cost = self.analyze_loop(loop)
        return cost.benefit

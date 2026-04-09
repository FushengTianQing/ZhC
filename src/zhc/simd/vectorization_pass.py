# -*- coding: utf-8 -*-
"""
ZhC 向量化 Pass

集成到 LLVM Pass 管道中，实现自动向量化优化。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import logging

from .loop_analyzer import (
    Loop,
    LoopAnalyzer,
)
from .vector_builder import (
    VectorType,
)
from .cost_model import (
    CostModel,
)

logger = logging.getLogger(__name__)


class VectorizationStrategy(Enum):
    """向量化策略"""

    NONE = "none"  # 不向量化
    SIMPLE = "simple"  # 简单向量化
    UNROLL_AND_VECTORIZE = "unroll_and_vectorize"  # 展开+向量化
    MASKED = "masked"  # 掩码向量化
    INTERLEAVED = "interleaved"  # 交错存储


@dataclass
class VectorizationConfig:
    """向量化配置"""

    enabled: bool = True  # 是否启用向量化
    vector_width: int = 4  # 向量宽度（元素数）
    max_vector_width: int = 16  # 最大向量宽度
    force_vectorize: bool = False  # 强制向量化
    enable_masks: bool = True  # 启用掩码
    enable_interleaving: bool = True  # 启用交错
    unroll_factor: int = 1  # 展开因子
    vectorize_only_when_beneficial: bool = True  # 仅在有益时向量化
    min_trip_count: int = 4  # 最小循环次数

    # 目标特定配置
    prefer_avx: bool = False  # 优先使用 AVX
    prefer_neon: bool = False  # 优先使用 NEON
    enable_rvv: bool = True  # 启用 RISC-V 向量扩展


@dataclass
class VectorizationResult:
    """向量化结果"""

    changed: bool  # 是否进行了修改
    loops_analyzed: int = 0  # 分析的循环数
    loops_vectorized: int = 0  # 向量化的循环数
    vectorized_loops: List[str] = field(default_factory=list)  # 向量化循环的名称
    failed_loops: List[Tuple[str, str]] = field(default_factory=list)  # 失败循环及原因
    vector_width_used: int = 0  # 使用的向量宽度
    estimated_speedup: float = 0.0  # 估计加速比
    total_instructions_saved: int = 0  # 节省的指令数

    def __str__(self) -> str:
        return (
            f"VectorizationResult(analyzed={self.loops_analyzed}, "
            f"vectorized={self.loops_vectorized}, "
            f"width={self.vector_width_used}, "
            f"speedup={self.estimated_speedup:.2f}x)"
        )


@dataclass
class VectorizationPass:
    """
    向量化优化 Pass

    分析循环并尝试向量化，以生成 SIMD 指令。
    """

    config: VectorizationConfig = field(default_factory=VectorizationConfig)
    target_arch: str = "generic"  # 目标架构

    def __init__(
        self,
        config: Optional[VectorizationConfig] = None,
        target_arch: str = "generic",
    ):
        if config:
            self.config = config
        self.target_arch = target_arch
        self.cost_model = CostModel(target_arch)
        self.result = VectorizationResult(changed=False)

    def run(self, module_ir: str) -> VectorizationResult:
        """
        运行向量化 Pass

        Args:
            module_ir: LLVM IR 模块字符串

        Returns:
            向量化结果
        """
        if not self.config.enabled:
            logger.debug("Vectorization disabled")
            return self.result

        logger.info(f"Running vectorization pass for {self.target_arch}")

        # 1. 分析模块中的函数
        functions = self._extract_functions(module_ir)

        # 2. 分析每个函数的循环
        for func_name, func_body in functions.items():
            loop_info = LoopAnalyzer.analyze(func_body)

            for loop in loop_info.loops:
                self.result.loops_analyzed += 1

                # 3. 检查是否应向量化
                should_vectorize, reason = self._should_vectorize(loop)
                if not should_vectorize:
                    self.result.failed_loops.append((func_name, reason))
                    continue

                # 4. 成本分析
                cost = self.cost_model.analyze_loop(loop)
                if cost.benefit < 1.0 and not self.config.force_vectorize:
                    self.result.failed_loops.append((func_name, "not_beneficial"))
                    continue

                # 5. 执行向量化
                if self._vectorize_loop(loop):
                    self.result.loops_vectorized += 1
                    self.result.vectorized_loops.append(func_name)
                    self.result.changed = True
                    self.result.total_instructions_saved += cost.instructions_saved
                    self.result.estimated_speedup += cost.benefit

        # 更新使用的向量宽度
        if self.result.loops_vectorized > 0:
            self.result.vector_width_used = self._select_vector_width()

        return self.result

    def _extract_functions(self, module_ir: str) -> Dict[str, str]:
        """提取函数"""
        # 简化实现：基于 LLVM IR 语法提取
        functions = {}

        lines = module_ir.split("\n")
        current_func = None
        current_body = []

        for line in lines:
            if line.startswith("define "):
                if current_func:
                    functions[current_func] = "\n".join(current_body)
                # 提取函数名
                parts = line.split("@")
                if len(parts) > 1:
                    func_sig = parts[1].split("(")[0]
                    current_func = func_sig
                    current_body = []
            elif current_func is not None:
                current_body.append(line)

        if current_func:
            functions[current_func] = "\n".join(current_body)

        return functions

    def _should_vectorize(self, loop: Loop) -> Tuple[bool, str]:
        """
        判断是否应向量化

        Returns:
            (should_vectorize, reason)
        """
        # 检查基本条件
        if not loop.is_vectorizable:
            return False, "not_vectorizable"

        # 检查循环次数
        if loop.trip_count_estimate:
            if loop.trip_count_estimate < self.config.min_trip_count:
                return False, "trip_count_too_small"

        # 检查是否有归纳变量
        if not loop.induction_vars:
            return False, "no_induction_variable"

        # 检查依赖关系
        if loop.dependencies:
            return False, "has_dependencies"

        # 检查是否有复杂的控制流
        if len(loop.loop_invariant_code) > 5:
            return False, "too_much_invariant_code"

        return True, ""

    def _vectorize_loop(self, loop: Loop) -> bool:
        """
        向量化循环

        Args:
            loop: 循环信息

        Returns:
            是否成功
        """
        # 选择策略
        strategy = self._select_strategy(loop)

        if strategy == VectorizationStrategy.NONE:
            return False

        # 构建向量化 IR (TODO: 实际使用 builder)

        try:
            # 1. 准备向量类型
            _ = self._get_vector_type(loop)

            # 2. 向量化处理 (TODO: 实际构建)

            # 3. 处理尾部（不能被向量宽度整除的部分）
            if loop.trip_count_estimate:
                remainder = loop.trip_count_estimate % self.config.vector_width
                if remainder > 0:
                    # 需要添加标量尾部处理
                    pass

            # 4. 添加掩码处理（如果需要）
            if strategy == VectorizationStrategy.MASKED:
                pass

            return True

        except Exception as e:
            logger.warning(f"Vectorization failed: {e}")
            return False

    def _select_strategy(self, loop: Loop) -> VectorizationStrategy:
        """选择向量化策略"""
        # 简单策略选择
        if not loop.is_vectorizable:
            return VectorizationStrategy.NONE

        if self.config.force_vectorize:
            if self.config.enable_masks:
                return VectorizationStrategy.MASKED
            return VectorizationStrategy.SIMPLE

        if loop.trip_count_estimate:
            if loop.trip_count_estimate >= 2 * self.config.vector_width:
                if self.config.enable_interleaving:
                    return VectorizationStrategy.UNROLL_AND_VECTORIZE

        return VectorizationStrategy.SIMPLE

    def _select_vector_width(self) -> int:
        """选择向量宽度"""
        # 基于目标架构选择
        if self.target_arch in ("x86_64", "aarch64"):
            if self.config.prefer_avx or self.config.prefer_neon:
                return 8  # AVX/NEON 256位 = 8 float32
        return self.config.vector_width

    def _get_vector_type(self, loop: Loop) -> "VectorType":
        """获取向量类型"""
        # 从归纳变量推断元素类型
        if loop.induction_vars:
            ind_var = loop.induction_vars[0]
            if ind_var.var_type.name == "int":
                return VectorType.int32_vector(self.config.vector_width)
            elif ind_var.var_type.name == "float":
                return VectorType.float32_vector(self.config.vector_width)
        return VectorType.float32_vector(self.config.vector_width)


def create_vectorization_pass(
    target_arch: str = "generic",
    vector_width: int = 4,
    force_vectorize: bool = False,
) -> VectorizationPass:
    """
    创建向量化 Pass

    Args:
        target_arch: 目标架构
        vector_width: 向量宽度
        force_vectorize: 是否强制向量化

    Returns:
        VectorizationPass 实例
    """
    config = VectorizationConfig(
        vector_width=vector_width,
        force_vectorize=force_vectorize,
    )
    return VectorizationPass(config=config, target_arch=target_arch)

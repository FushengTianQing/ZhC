# -*- coding: utf-8 -*-
"""
ZhC Pass 配置

定义各优化级别使用的标准 Pass 组合和配置选项。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from zhc.optimization.optimization_levels import OptimizationLevel


@dataclass
class PassConfig:
    """
    单个 Pass 的配置

    用于配置 Pass 的行为和参数。
    """

    name: str
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        if self.parameters:
            params = ", ".join(f"{k}={v}" for k, v in self.parameters.items())
            return f"{self.name}({params})"
        return self.name


@dataclass
class PassPipeline:
    """
    Pass 管道配置

    定义一组按顺序执行的 Pass。
    """

    name: str
    passes: List[PassConfig] = field(default_factory=list)

    def add_pass(self, name: str, enabled: bool = True, **params) -> None:
        """添加 Pass 到管道"""
        self.passes.append(PassConfig(name=name, enabled=enabled, parameters=params))

    def get_enabled_passes(self) -> List[str]:
        """获取启用的 Pass 列表"""
        return [p.name for p in self.passes if p.enabled]

    def __iter__(self):
        """迭代启用的 Pass"""
        return (p for p in self.passes if p.enabled)


class StandardPassConfig:
    """
    标准 Pass 配置

    为各优化级别定义标准的 Pass 管道。
    """

    # O0 - 调试级别：仅保留必要的 passes，保证语义正确
    O0_PASSES: List[str] = [
        "no-op",  # 无操作 Pass
        "verify",  # 验证 IR 正确性
    ]

    # O1 - 快速优化：基础优化，编译速度快
    O1_PASSES: List[str] = [
        "inline",  # 简单内联
        "mem2reg",  # 内存到寄存器提升
        "early-cse",  # 早期 CSE
        "gvn",  # 全局值编号
        "dce",  # 死代码消除
    ]

    # O2 - 标准优化：平衡编译速度和性能（推荐）
    O2_PASSES: List[str] = [
        "inline",  # 内联
        "mem2reg",  # 内存到寄存器
        "loop-rotate",  # 循环旋转
        "licm",  # 循环不变代码移动
        "loop-unswitch",  # 循环条件转换
        "indvars",  # 归纳变量简化
        "gvn",  # 全局值编号
        "sccp",  # 稀疏条件常量传播
        "dce",  # 死代码消除
        "adce",  # 主动死代码消除
        "reassociate",  # 重结合
        "simplifycfg",  # 简化控制流
        "mergeret",  # 合并 return
    ]

    # O3 - 激进优化：最大性能
    O3_PASSES: List[str] = O2_PASSES + [
        "loop-unroll",  # 循环展开
        "loop-vectorize",  # 循环向量化
        "slp-vectorize",  # SLP 向量化
        "gvn-hoist",  # GVN 提升
        "aggressive-dce",  # 激进死代码消除
        "function-attrs",  # 函数属性推断
    ]

    # Os - 大小优化：优先代码大小
    OS_PASSES: List[str] = [
        "inline",  # 内联
        "mem2reg",
        "loop-rotate",
        "gvn",
        "dce",
        "adce",
        "simplifycfg",
        "mergefunc",  # 函数合并
        "constmerge",  # 常量合并
    ]

    # Oz - 极致大小优化
    OZ_PASSES: List[str] = OS_PASSES + [
        "globalopt",  # 全局变量优化
    ]

    @classmethod
    def get_passes_for_level(cls, level: OptimizationLevel) -> List[str]:
        """
        获取指定优化级别使用的 Pass 列表

        Args:
            level: 优化级别

        Returns:
            Pass 名称列表
        """
        level_map = {
            OptimizationLevel.O0: cls.O0_PASSES,
            OptimizationLevel.O1: cls.O1_PASSES,
            OptimizationLevel.O2: cls.O2_PASSES,
            OptimizationLevel.O3: cls.O3_PASSES,
            OptimizationLevel.Os: cls.OS_PASSES,
            OptimizationLevel.Oz: cls.OZ_PASSES,
        }
        return level_map.get(level, cls.O2_PASSES)

    @classmethod
    def create_pipeline(
        cls, level: OptimizationLevel, extra_passes: Optional[List[str]] = None
    ) -> PassPipeline:
        """
        为指定优化级别创建 Pass 管道

        Args:
            level: 优化级别
            extra_passes: 额外的 Pass 列表

        Returns:
            配置好的 PassPipeline
        """
        pipeline = PassPipeline(name=f"standard-{level.name}")

        for pass_name in cls.get_passes_for_level(level):
            pipeline.add_pass(pass_name)

        # 添加额外的 Pass
        if extra_passes:
            for pass_name in extra_passes:
                pipeline.add_pass(pass_name)

        return pipeline

    @classmethod
    def get_default_inline_threshold(cls, level: OptimizationLevel) -> int:
        """
        获取指定优化级别的默认内联阈值

        Args:
            level: 优化级别

        Returns:
            内联阈值（字节）
        """
        thresholds = {
            OptimizationLevel.O0: 0,  # 不内联
            OptimizationLevel.O1: 64,
            OptimizationLevel.O2: 255,
            OptimizationLevel.O3: 1024,
            OptimizationLevel.Os: 64,
            OptimizationLevel.Oz: 32,
        }
        return thresholds.get(level, 255)

    @classmethod
    def get_default_loop_unroll_count(cls, level: OptimizationLevel) -> int:
        """
        获取指定优化级别的默认循环展开次数

        Args:
            level: 优化级别

        Returns:
            展开次数（0 表示完全展开）
        """
        if level == OptimizationLevel.O0:
            return 0
        elif level == OptimizationLevel.O1:
            return 2
        elif level == OptimizationLevel.O2:
            return 4
        elif level == OptimizationLevel.O3:
            return 8  # 完全展开
        elif level.is_size_optimization:
            return 2
        return 4


@dataclass
class PassParameter:
    """Pass 参数定义"""

    name: str
    type: type
    default: Any
    description: str


class PassParameters:
    """
    标准 Pass 参数定义

    定义各 Pass 支持的配置参数。
    """

    # 内联 Pass 参数
    INLINE_PARAMS = {
        "threshold": PassParameter(
            "threshold",
            int,
            255,
            "内联阈值（字节）",
        ),
        "only_mandatory": PassParameter(
            "only_mandatory",
            bool,
            False,
            "仅内联必须内联的函数",
        ),
        "inline_threshold": PassParameter(
            "inline_threshold",
            int,
            255,
            "别名：threshold",
        ),
    }

    # 循环向量化参数
    VECTORIZE_PARAMS = {
        "vector_width": PassParameter(
            "vector_width",
            int,
            0,
            "向量宽度（0 表示自动）",
        ),
        "force_vectorize": PassParameter(
            "force_vectorize",
            bool,
            False,
            "强制向量化",
        ),
        "interleave": PassParameter(
            "interleave",
            bool,
            True,
            "启用交织",
        ),
    }

    # 循环展开参数
    LOOP_UNROLL_PARAMS = {
        "count": PassParameter(
            "count",
            int,
            0,
            "展开次数（0 表示自动）",
        ),
        "full_unroll": PassParameter(
            "full_unroll",
            bool,
            False,
            "完全展开",
        ),
        "allow_remat": PassParameter(
            "allow_remat",
            bool,
            True,
            "允许重新物化",
        ),
    }

    # GVN 参数
    GVN_PARAMS = {
        "allow_reorder": PassParameter(
            "allow_reorder",
            bool,
            True,
            "允许重新排序",
        ),
        "preprocess": PassParameter(
            "preprocess",
            bool,
            True,
            "启用预处理",
        ),
    }

    @classmethod
    def get_params(cls, pass_name: str) -> Dict[str, PassParameter]:
        """获取指定 Pass 的参数定义"""
        param_map = {
            "inline": cls.INLINE_PARAMS,
            "loop-vectorize": cls.VECTORIZE_PARAMS,
            "loop-unroll": cls.LOOP_UNROLL_PARAMS,
            "gvn": cls.GVN_PARAMS,
        }
        return param_map.get(pass_name, {})

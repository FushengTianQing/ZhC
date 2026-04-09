# -*- coding: utf-8 -*-
"""
ZhC 编译器优化 Pass 模块

提供完整的 LLVM 优化 Pass 管道，支持 O0/O1/O2/O3/Os 等优化级别。
本模块将 ZhC 编译器从"功能正确"提升到"性能优秀"的水平。

核心组件：
- PassManager: Pass 管理器，管理优化流程
- OptimizationLevel: 优化级别枚举
- PassRegistry: Pass 注册表
- OptimizationObserver: 优化观察器

作者：远
日期：2026-04-09
"""

from zhc.optimization.optimization_levels import OptimizationLevel
from zhc.optimization.pass_manager import PassManager, OptimizationPipeline
from zhc.optimization.pass_registry import PassRegistry, PassType, PassInfo
from zhc.optimization.pass_config import PassConfig, StandardPassConfig
from zhc.optimization.optimization_observer import (
    OptimizationObserver,
    OptimizationStats,
    OptimizationResult,
)

__all__ = [
    # 枚举和常量
    "OptimizationLevel",
    # 核心类
    "PassManager",
    "OptimizationPipeline",
    "PassRegistry",
    "PassConfig",
    "StandardPassConfig",
    # 观察器和统计
    "OptimizationObserver",
    "OptimizationStats",
    "OptimizationResult",
    # 类型
    "PassType",
    "PassInfo",
]

__version__ = "0.1.0"

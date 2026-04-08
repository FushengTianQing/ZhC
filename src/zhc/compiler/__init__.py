"""
编译器模块

包含：
- pipeline: 编译流水线
- parallel_pipeline: 并行编译流水线
- function_cache: 函数级缓存
- cache: 缓存系统
- optimizer: 性能优化器
"""

from .pipeline import CompilationPipeline
from .parallel_pipeline import (
    ParallelCompilationPipeline,
    AdaptiveParallelPipeline,
    CompilationLayerCalculator,
    ParallelStrategy,
    ModuleInfo,
    CompilationResult,
    ParallelStats,
    ParallelPipeline,
    AdaptivePipeline,
)
from .function_cache import (
    FunctionLevelCache,
    FunctionCache,
    CacheStatus,
    CachedFunction,
    FunctionCacheStatistics,
)

__all__ = [
    # 基础编译流水线
    "CompilationPipeline",
    # 并行编译流水线
    "ParallelCompilationPipeline",
    "AdaptiveParallelPipeline",
    "CompilationLayerCalculator",
    "ParallelStrategy",
    "ModuleInfo",
    "CompilationResult",
    "ParallelStats",
    # 别名
    "ParallelPipeline",
    "AdaptivePipeline",
    # 函数级缓存
    "FunctionLevelCache",
    "FunctionCache",
    "CacheStatus",
    "CachedFunction",
    "FunctionCacheStatistics",
]

__version__ = "1.4.0"

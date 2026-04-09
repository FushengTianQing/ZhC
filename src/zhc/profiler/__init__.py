"""
ZhC 性能剖析模块

功能：
1. 函数调用追踪
2. 执行时间测量
3. 热点分析
4. 性能报告生成
"""

from .data import (
    FunctionProfile,
    CallRelation,
    ProfilerStats,
    ProfilerConfig,
)

from .tracker import (
    ProfilerTracker,
    profile_function,
    profile_scope,
    get_tracker,
)

from .reporter import (
    ProfilerReporter,
    TextReporter,
    JsonReporter,
    HtmlReporter,
    FlameGraphReporter,
)

from .hotspot import (
    HotspotAnalyzer,
    Hotspot,
    OptimizationHint,
)

__all__ = [
    # Data classes
    "FunctionProfile",
    "CallRelation",
    "ProfilerStats",
    "ProfilerConfig",
    # Tracker
    "ProfilerTracker",
    "profile_function",
    "profile_scope",
    "get_tracker",
    # Reporter
    "ProfilerReporter",
    "TextReporter",
    "JsonReporter",
    "HtmlReporter",
    "FlameGraphReporter",
    # Hotspot analyzer
    "HotspotAnalyzer",
    "Hotspot",
    "OptimizationHint",
]


# 向后兼容的别名
def get_global_tracker() -> ProfilerTracker:
    """获取全局追踪器实例"""
    return get_tracker()


def start_profiling():
    """开始性能剖析"""
    get_tracker().start()


def stop_profiling():
    """停止性能剖析"""
    get_tracker().stop()


def reset_profiling():
    """重置性能数据"""
    get_tracker().reset()


def get_profiler_report(format: str = "text") -> str:
    """获取性能报告

    Args:
        format: 报告格式 (text, json, html, flamegraph)

    Returns:
        报告字符串
    """
    return get_tracker().get_report(format)

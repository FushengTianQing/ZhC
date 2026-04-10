"""
ZhC 内存使用分析模块

功能：
1. 内存分配追踪
2. 内存泄漏检测
3. 使用统计
4. 分配源分析
"""

from .data import (
    MemBlock,
    MemStats,
    MemOpType,
    MemOpRecord,
    AllocSite,
)

from .tracker import (
    MemTracker,
    track_alloc,
    track_free,
    get_tracker,
)

from .reporter import (
    MemReporter,
    TextReporter,
    JsonReporter,
    HtmlReporter,
)

from .leak_detector import (
    LeakDetector,
    LeakReport,
    LeakType,
)

from .call_stack import (
    CallStackTracer,
    CallStack,
    StackFrame,
    get_call_stack_tracer,
)

__all__ = [
    # Data classes
    "MemBlock",
    "MemStats",
    "MemOpType",
    "MemOpRecord",
    "AllocSite",
    # Tracker
    "MemTracker",
    "track_alloc",
    "track_free",
    "get_tracker",
    # Reporter
    "MemReporter",
    "TextReporter",
    "JsonReporter",
    "HtmlReporter",
    # Leak detector
    "LeakDetector",
    "LeakReport",
    "LeakType",
    # Call stack tracer
    "CallStackTracer",
    "CallStack",
    "StackFrame",
    "get_call_stack_tracer",
]


# 向后兼容的别名
def get_global_tracker() -> MemTracker:
    """获取全局追踪器实例"""
    return get_tracker()


def start_tracking():
    """开始内存追踪"""
    get_tracker().start()


def stop_tracking():
    """停止内存追踪"""
    get_tracker().stop()


def reset_tracking():
    """重置内存追踪数据"""
    get_tracker().reset()


def get_memory_report(format: str = "text") -> str:
    """获取内存使用报告

    Args:
        format: 报告格式 (text, json, html)

    Returns:
        报告字符串
    """
    return get_tracker().get_report(format)


def check_leaks() -> bool:
    """检查是否有内存泄漏

    Returns:
        True 有泄漏，False 无泄漏
    """
    return get_tracker().has_leaks()

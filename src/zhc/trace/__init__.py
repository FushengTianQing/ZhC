# -*- coding: utf-8 -*-
"""
ZHC 执行追踪模块 (Phase 0 MVP)

提供编译期执行追踪能力：
- trace.json: 执行轨迹结构化数据
- trace.html: 可视化执行过程

用法:
    zhc run --trace input.zhc
    输出: trace.json + trace.html

作者：远
日期：2026-04-13
"""

from .schema import TraceEvent, TraceRecord, TraceLevel, TraceEventType, SourceLocation
from .serializer import TraceSerializer
from .html_generator import HTMLGenerator
from .pass_registry import TracePass, TracePassManager

__all__ = [
    "TraceEvent",
    "TraceRecord",
    "TraceLevel",
    "TraceEventType",
    "SourceLocation",
    "TraceSerializer",
    "HTMLGenerator",
    "TracePass",
    "TracePassManager",
]

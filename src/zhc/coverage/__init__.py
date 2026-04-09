#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZhC 覆盖率分析模块

提供代码覆盖率追踪和分析功能
"""

from .data import (
    CoverageType,
    LineCoverage,
    BranchCoverage,
    FunctionCoverage,
    FileCoverage,
    ProjectCoverage,
)

from .tracker import (
    CoverageTracker,
    get_tracker,
    start_coverage,
    stop_coverage,
    reset_coverage,
    get_coverage,
)

from .instrument import (
    Instrumenter,
    instrument_file,
    instrument_source,
)

from .reporter import (
    CoverageReporter,
    TextReporter,
    JsonReporter,
    HtmlReporter,
    MarkdownReporter,
    LcovReporter,
    generate_report,
    save_report,
)

__all__ = [
    # 数据结构
    "CoverageType",
    "LineCoverage",
    "BranchCoverage",
    "FunctionCoverage",
    "FileCoverage",
    "ProjectCoverage",
    # 追踪器
    "CoverageTracker",
    "get_tracker",
    "start_coverage",
    "stop_coverage",
    "reset_coverage",
    "get_coverage",
    # 插桩
    "Instrumenter",
    "instrument_file",
    "instrument_source",
    # 报告器
    "CoverageReporter",
    "TextReporter",
    "JsonReporter",
    "HtmlReporter",
    "MarkdownReporter",
    "LcovReporter",
    "generate_report",
    "save_report",
]

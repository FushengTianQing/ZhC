# -*- coding: utf-8 -*-
"""
ZhC DWARF 调试节模块

提供 DWARF 调试信息的各个节的生成器。

作者：远
日期：2026-04-09
"""

from .debug_info import (
    DebugInfoSection,
    CompileUnitBuilder,
    DIEBuilder,
)

from .debug_abbrev import (
    DebugAbbrevSection,
    AbbreviationBuilder,
)

from .debug_line import (
    DebugLineSection,
    LineNumberProgramBuilder,
)

from .debug_str import (
    DebugStrSection,
    StringPool,
)

__all__ = [
    # .debug_info
    "DebugInfoSection",
    "CompileUnitBuilder",
    "DIEBuilder",
    # .debug_abbrev
    "DebugAbbrevSection",
    "AbbreviationBuilder",
    # .debug_line
    "DebugLineSection",
    "LineNumberProgramBuilder",
    # .debug_str
    "DebugStrSection",
    "StringPool",
]

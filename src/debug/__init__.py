"""
中文C语言调试信息生成模块
DWARF Debug Information Generator

生成符合DWARF标准的调试信息，支持GDB/LLDB调试器。
事件驱动架构，支持多后端扩展。
"""

__version__ = '1.0.0'
__author__ = '中文C编译器团队'

from .debug_generator import (
    DebugInfoGenerator,
    DWARFGenerator,
    LineNumberTable,
    DebugSymbolTable,
    TypeInfoGenerator,
    SourceLocation,
    AddressRange,
    CompileUnit,
)

from .debug_listener import DebugListener
from .debug_manager import DebugManager

__all__ = [
    # 核心生成器
    'DebugInfoGenerator',
    'DWARFGenerator',
    'LineNumberTable',
    'DebugSymbolTable',
    'TypeInfoGenerator',
    # 数据结构
    'SourceLocation',
    'AddressRange',
    'CompileUnit',
    # 事件驱动架构
    'DebugListener',
    'DebugManager',
]
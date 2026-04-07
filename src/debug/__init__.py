"""
中文C语言调试信息生成模块
DWARF Debug Information Generator

生成符合DWARF标准的调试信息，支持GDB/LLDB调试器
"""

__version__ = '1.0.0'
__author__ = '中文C编译器团队'

from .debug_generator import (
    DebugInfoGenerator,
    DWARFGenerator,
    LineNumberTable,
    DebugSymbolTable,
    TypeInfoGenerator
)

__all__ = [
    'DebugInfoGenerator',
    'DWARFGenerator', 
    'LineNumberTable',
    'DebugSymbolTable',
    'TypeInfoGenerator'
]
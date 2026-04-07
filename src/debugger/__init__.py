"""
中文C语言调试器集成模块
GDB/LLDB Integration for ZHC Language

提供GDB和LLDB调试器的中文C语言支持
"""

__version__ = '1.0.0'
__author__ = '中文C编译器团队'

# 检查GDB/LLDB是否可用
try:
    from .gdb_zhc import ZHCGDBCommands
    GDB_AVAILABLE = True
except ImportError:
    GDB_AVAILABLE = False
    ZHCGDBCommands = None

try:
    from .lldb_zhc import ZHCLLLDBCommands
    LLDB_AVAILABLE = True
except ImportError:
    LLDB_AVAILABLE = False
    ZHCLLLDBCommands = None

__all__ = [
    'ZHCGDBCommands',
    'ZHCLLLDBCommands',
    'GDB_AVAILABLE',
    'LLDB_AVAILABLE'
]
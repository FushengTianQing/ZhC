#!/usr/bin/env python3
"""
代码生成包

支持多后端代码生成（C、LLVM、WASM 等）。
事件驱动架构，统一调试信息管理。

作者: 阿福
日期: 2026-04-03
"""

from .c_codegen import CCodeGenerator
from .c_debug_listener import CDebugListener

__all__ = ['CCodeGenerator', 'CDebugListener']

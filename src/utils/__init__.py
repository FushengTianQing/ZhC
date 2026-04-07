# -*- coding: utf-8 -*-
"""
ZHC 公共工具模块

提供常用的工具函数，减少代码重复。

作者：远
日期：2026-04-07
"""

from .file_utils import (
    read_file,
    write_file,
    read_json_file,
    write_json_file,
    read_lines,
    ensure_directory,
)

from .string_utils import (
    normalize_whitespace,
    strip_lines,
    clean_empty_lines,
    indent_text,
)

from .error_utils import (
    safe_execute,
    format_error_message,
    log_error,
)

__all__ = [
    # 文件工具
    'read_file',
    'write_file',
    'read_json_file',
    'write_json_file',
    'read_lines',
    'ensure_directory',
    
    # 字符串工具
    'normalize_whitespace',
    'strip_lines',
    'clean_empty_lines',
    'indent_text',
    
    # 错误处理工具
    'safe_execute',
    'format_error_message',
    'log_error',
]
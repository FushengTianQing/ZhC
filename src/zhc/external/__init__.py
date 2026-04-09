"""
外部函数调用模块

提供外部 C 函数声明、解析和链接功能。
"""

from .c_types import CTypeInfo, CTypeMapper, get_c_type_mapper
from .external_resolver import (
    LinkageType,
    ExternalFunction,
    ExternalBlock,
    ExternalFunctionRegistry,
    ExternalFunctionResolver,
    get_external_resolver,
)

__all__ = [
    # C 类型映射
    "CTypeInfo",
    "CTypeMapper",
    "get_c_type_mapper",
    # 外部函数解析
    "LinkageType",
    "ExternalFunction",
    "ExternalBlock",
    "ExternalFunctionRegistry",
    "ExternalFunctionResolver",
    "get_external_resolver",
]

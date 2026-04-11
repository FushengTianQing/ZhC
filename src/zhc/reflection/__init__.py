# -*- coding: utf-8 -*-
"""
ZhC 反射模块 - 运行时类型信息 (RTTI)

提供运行时类型查询功能：
- 类型名称、大小查询
- 字段列表、偏移量查询
- 方法列表查询
- 继承关系查询
- 运行时类型检查
- 类型转换

作者：远
日期：2026-04-11
"""

from .type_info import (
    ReflectionFieldInfo,
    ReflectionMethodInfo,
    ReflectionTypeInfo,
    TypeRegistry,
    get_type_info,
    get_type_name,
    get_type_size,
    register_type,
)

from .metadata import (
    TypeMetadataGenerator,
    ReflectionMetadataCollector,
    get_metadata_generator,
)

from .type_check import (
    TypeHierarchy,
    TypeChecker,
    is_type,
    is_subtype,
    implements_interface,
    type_equals,
    type_name,
    check_assignable,
    is_primitive,
)

from .type_cast import (
    CastResult,
    CastErrorType,
    CastError,
    TypeCast,
    TypeCastError,
    CastValidator,
    safe_cast,
    dynamic_cast,
    require_type,
    cast_to_interface,
    try_cast,
    narrow_cast,
    widen_cast,
    safe_cast_as,
    dynamic_cast_as,
    get_cast_path,
    can_cast,
    validate_cast,
    find_best_cast,
)

__all__ = [
    # 核心数据结构
    "ReflectionFieldInfo",
    "ReflectionMethodInfo",
    "ReflectionTypeInfo",
    # 类型注册表
    "TypeRegistry",
    # API 函数
    "get_type_info",
    "get_type_name",
    "get_type_size",
    "register_type",
    # 元数据生成
    "TypeMetadataGenerator",
    "ReflectionMetadataCollector",
    "get_metadata_generator",
    # 类型层次结构
    "TypeHierarchy",
    # 类型检查器
    "TypeChecker",
    "is_type",
    "is_subtype",
    "implements_interface",
    "type_equals",
    "type_name",
    "check_assignable",
    "is_primitive",
    # 类型转换
    "CastResult",
    "CastErrorType",
    "CastError",
    "TypeCast",
    "TypeCastError",
    "CastValidator",
    "safe_cast",
    "dynamic_cast",
    "require_type",
    "cast_to_interface",
    "try_cast",
    "narrow_cast",
    "widen_cast",
    "safe_cast_as",
    "dynamic_cast_as",
    "get_cast_path",
    "can_cast",
    "validate_cast",
    "find_best_cast",
]

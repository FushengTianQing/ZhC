"""
类型系统模块

包含：
- virtual: 虚函数
- operator: 运算符重载
- smart_ptr: 智能指针
- array_types: 数组类型定义
- array_checker: 数组边界检查器
- array_inferrer: 数组类型推导器
- function_pointer: 函数指针类型
- struct_layout: 结构体布局计算器
"""

# 数组类型定义
from .array_types import (
    ArrayKind,
    ArrayTypeInfo,
    ArrayTypeFactory,
    TYPE_HIERARCHY,
    unify_element_types,
    calculate_array_size,
)

# 数组边界检查
from .array_checker import (
    Severity,
    BoundsError,
    ArrayAccessInfo,
    ArrayBoundsChecker,
    RuntimeBoundsCheckGenerator,
    ArrayAccessTracker,
)

# 数组类型推导
from .array_inferrer import (
    InferenceResult,
    InferenceContext,
    ArrayTypeInferrer,
    infer_array_type_from_string,
)

# 函数指针类型
from .function_pointer import (
    FunctionPointerTypeInfo,
    FunctionPointerDecl,
    FunctionPointerTypeMapper,
    FunctionPointerRegistry,
    get_type_mapper,
    get_registry,
    create_function_pointer_type,
    is_function_pointer_compatible,
)

# 结构体布局
from .struct_layout import (
    AlignmentRules,
    StructMember,
    StructLayout,
    StructLayoutCalculator,
    LLVMStructTypeMapper,
    StructGepStrategy,
    NestedStructGepStrategy,
    get_struct_mapper,
)

# 复数类型
from .complex import (
    ComplexElementType,
    ComplexType,
    ComplexValue,
    浮点复数型,
    双精度复数型,
    长双精度复数型,
)

# 复数数学函数
from .complex_math import (
    complex_sqrt,
    complex_exp,
    complex_log,
    complex_log10,
    complex_pow,
    complex_sin,
    complex_cos,
    complex_tan,
    complex_sinh,
    complex_cosh,
    complex_tanh,
    complex_asin,
    complex_acos,
    complex_atan,
    complex_asinh,
    complex_acosh,
    complex_atanh,
    complex_add,
    complex_sub,
    complex_mul,
    complex_div,
    complex_neg,
    complex_conj,
    complex_abs,
    complex_arg,
    complex_polar,
)

# 定点数类型
from .fixed_point import (
    FixedPointFormat,
    FixedPointType,
    FixedPointValue,
    短定点小数,
    标准定点小数,
    长定点小数,
    短定点累加,
    标准定点累加,
    长定点累加,
    无符号定点小数,
    无符号定点累加,
)

__all__ = [
    # 数组类型
    "ArrayKind",
    "ArrayTypeInfo",
    "ArrayTypeFactory",
    "TYPE_HIERARCHY",
    "unify_element_types",
    "calculate_array_size",
    # 边界检查
    "Severity",
    "BoundsError",
    "ArrayAccessInfo",
    "ArrayBoundsChecker",
    "RuntimeBoundsCheckGenerator",
    "ArrayAccessTracker",
    # 类型推导
    "InferenceResult",
    "InferenceContext",
    "ArrayTypeInferrer",
    "infer_array_type_from_string",
    # 函数指针
    "FunctionPointerTypeInfo",
    "FunctionPointerDecl",
    "FunctionPointerTypeMapper",
    "FunctionPointerRegistry",
    "get_type_mapper",
    "get_registry",
    "create_function_pointer_type",
    "is_function_pointer_compatible",
    # 结构体布局
    "AlignmentRules",
    "StructMember",
    "StructLayout",
    "StructLayoutCalculator",
    "LLVMStructTypeMapper",
    "StructGepStrategy",
    "NestedStructGepStrategy",
    "get_struct_mapper",
    # 复数类型
    "ComplexElementType",
    "ComplexType",
    "ComplexValue",
    "浮点复数型",
    "双精度复数型",
    "长双精度复数型",
    # 复数数学函数
    "complex_sqrt",
    "complex_exp",
    "complex_log",
    "complex_log10",
    "complex_pow",
    "complex_sin",
    "complex_cos",
    "complex_tan",
    "complex_sinh",
    "complex_cosh",
    "complex_tanh",
    "complex_asin",
    "complex_acos",
    "complex_atan",
    "complex_asinh",
    "complex_acosh",
    "complex_atanh",
    "complex_add",
    "complex_sub",
    "complex_mul",
    "complex_div",
    "complex_neg",
    "complex_conj",
    "complex_abs",
    "complex_arg",
    "complex_polar",
    # 定点数类型
    "FixedPointFormat",
    "FixedPointType",
    "FixedPointValue",
    "短定点小数",
    "标准定点小数",
    "长定点小数",
    "短定点累加",
    "标准定点累加",
    "长定点累加",
    "无符号定点小数",
    "无符号定点累加",
]

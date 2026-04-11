# -*- coding: utf-8 -*-
"""
ZhC LLVM 后端 - 运行时类型检查编译策略

实现类型检查相关操作的 LLVM IR 编译策略。

策略列表：
- IsTypeStrategy: 检查对象是否为指定类型
- IsSubtypeStrategy: 检查子类型关系
- ImplementsInterfaceStrategy: 检查接口实现
- TypeEqualsStrategy: 检查类型是否相同
- SafeCastStrategy: 安全类型转换
- DynamicCastStrategy: 动态类型转换
- CheckAssignableStrategy: 检查赋值兼容性
- IsPrimitiveStrategy: 检查是否基本类型

作者：远
日期：2026-04-11
"""

import logging
from typing import Optional, TYPE_CHECKING

from zhc.ir.opcodes import Opcode
from .llvm_instruction_strategy import InstructionStrategy

if TYPE_CHECKING:
    import llvmlite.ir as ll
    from zhc.backend.compilation_context import CompilationContext

logger = logging.getLogger(__name__)


class _BaseTypeCheckStrategy(InstructionStrategy):
    """类型检查策略的公共基类"""

    def _get_string_ptr(self, builder, value, context):
        """获取字符串常量指针"""

        if hasattr(value, "const_value") and isinstance(value.const_value, str):
            return context.create_global_string(value.const_value)
        return value

    def _declare_bool_func(self, context, func_name: str, param_count: int):
        """声明返回 bool 的 C 函数"""
        import llvmlite.ir as ll

        params = [ll.PointerType(ll.IntType(8))] * param_count  # const char* 参数
        func_type = ll.FunctionType(ll.IntType(1), params)  # bool 返回
        return context.module.get_or_insert_function(func_name, func_type)

    def _declare_ptr_func(self, context, func_name: str, param_count: int):
        """声明返回 void* 的 C 函数"""
        import llvmlite.ir as ll

        params = [ll.PointerType(ll.IntType(8))] * param_count
        func_type = ll.FunctionType(ll.PointerType(ll.IntType(8)), params)
        return context.module.get_or_insert_function(func_name, func_type)


class IsTypeStrategy(_BaseTypeCheckStrategy):
    """
    检查对象是否为指定类型

    IR 格式：
        %result = IS_TYPE obj_type, target_type

    LLVM IR 生成：
        %result = call i1 @zhc_is_type(i8* %obj_type, i8* %target_type)
    """

    opcode = Opcode.IS_TYPE

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        if not instr.operands or len(instr.operands) < 2:
            logger.warning("IS_TYPE 指令缺少操作数（需要 obj_type 和 target_type）")
            return None

        obj_type_val = instr.operands[0]
        target_type_val = instr.operands[1]

        func = self._declare_bool_func(context, "zhc_is_type", 2)

        obj_type_ptr = self._get_string_ptr(builder, obj_type_val, context)
        target_type_ptr = self._get_string_ptr(builder, target_type_val, context)

        return builder.call(func, [obj_type_ptr, target_type_ptr])


class IsSubtypeStrategy(_BaseTypeCheckStrategy):
    """
    检查子类型关系

    IR 格式：
        %result = IS_SUBTYPE subtype, supertype

    LLVM IR 生成：
        %result = call i1 @zhc_is_subtype(i8* %subtype, i8* %supertype)
    """

    opcode = Opcode.IS_SUBTYPE

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        if not instr.operands or len(instr.operands) < 2:
            logger.warning("IS_SUBTYPE 指令缺少操作数")
            return None

        subtype_val = instr.operands[0]
        supertype_val = instr.operands[1]

        func = self._declare_bool_func(context, "zhc_is_subtype", 2)

        subtype_ptr = self._get_string_ptr(builder, subtype_val, context)
        supertype_ptr = self._get_string_ptr(builder, supertype_val, context)

        return builder.call(func, [subtype_ptr, supertype_ptr])


class ImplementsInterfaceStrategy(_BaseTypeCheckStrategy):
    """
    检查接口实现

    IR 格式：
        %result = IMPL_IFACE type_name, interface_name

    LLVM IR 生成：
        %result = call i1 @zhc_implements_interface(i8* %type_name, i8* %interface_name)
    """

    opcode = Opcode.IMPL_IFACE

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        if not instr.operands or len(instr.operands) < 2:
            logger.warning("IMPL_IFACE 指令缺少操作数")
            return None

        type_name_val = instr.operands[0]
        interface_name_val = instr.operands[1]

        func = self._declare_bool_func(context, "zhc_implements_interface", 2)

        type_name_ptr = self._get_string_ptr(builder, type_name_val, context)
        iface_name_ptr = self._get_string_ptr(builder, interface_name_val, context)

        return builder.call(func, [type_name_ptr, iface_name_ptr])


class TypeEqualsStrategy(_BaseTypeCheckStrategy):
    """
    检查类型是否相同

    IR 格式：
        %result = TYPE_EQUALS type1, type2

    LLVM IR 生成：
        %result = call i1 @zhc_type_equals(i8* %type1, i8* %type2)
    """

    opcode = Opcode.TYPE_EQUALS

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        if not instr.operands or len(instr.operands) < 2:
            logger.warning("TYPE_EQUALS 指令缺少操作数")
            return None

        type1_val = instr.operands[0]
        type2_val = instr.operands[1]

        func = self._declare_bool_func(context, "zhc_type_equals", 2)

        type1_ptr = self._get_string_ptr(builder, type1_val, context)
        type2_ptr = self._get_string_ptr(builder, type2_val, context)

        return builder.call(func, [type1_ptr, type2_ptr])


class SafeCastStrategy(_BaseTypeCheckStrategy):
    """
    安全类型转换

    IR 格式：
        %result = SAFE_CAST obj, "target_type"

    LLVM IR 生成：
        %result = call i8* @zhc_safe_cast(i8* %obj, i8* %obj_type, i8* %target_type)

    操作数说明：
        operands[0]: obj - 源对象值（从其类型属性获取 obj_type）
        operands[1]: "target_type" - 目标类型字符串常量
    """

    opcode = Opcode.SAFE_CAST

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        if not instr.operands or len(instr.operands) < 2:
            logger.warning("SAFE_CAST 指令缺少操作数（需要 obj 和 target_type）")
            return None

        obj_val = instr.operands[0]
        target_type_val = instr.operands[1]

        # 从源对象的类型属性获取 obj_type
        obj_type_str = getattr(obj_val, "type", "空型")

        # 创建全局字符串常量
        obj_type_ptr = context.create_global_string(obj_type_str)
        target_type_ptr = self._get_string_ptr(builder, target_type_val, context)

        # 调用 zhc_safe_cast(obj, obj_type, target_type)
        func = self._declare_ptr_func(context, "zhc_safe_cast", 3)

        # 确保 obj_val 是指针类型
        if hasattr(obj_val, "type"):
            obj_ptr = obj_val
        else:
            obj_ptr = obj_val

        return builder.call(func, [obj_ptr, obj_type_ptr, target_type_ptr])


class DynamicCastStrategy(_BaseTypeCheckStrategy):
    """
    动态类型转换

    IR 格式：
        %result = DYNAMIC_CAST obj, "target_type"

    LLVM IR 生成：
        %result = call i8* @zhc_dynamic_cast(i8* %obj, i8* %obj_type, i8* %target_type)

    操作数说明：
        operands[0]: obj - 源对象值（从其类型属性获取 obj_type）
        operands[1]: "target_type" - 目标类型字符串常量
    """

    opcode = Opcode.DYNAMIC_CAST

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        if not instr.operands or len(instr.operands) < 2:
            logger.warning("DYNAMIC_CAST 指令缺少操作数")
            return None

        obj_val = instr.operands[0]
        target_type_val = instr.operands[1]

        # 从源对象的类型属性获取 obj_type
        obj_type_str = getattr(obj_val, "type", "空型")

        # 创建全局字符串常量
        obj_type_ptr = context.create_global_string(obj_type_str)
        target_type_ptr = self._get_string_ptr(builder, target_type_val, context)

        # 调用 zhc_dynamic_cast(obj, obj_type, target_type)
        func = self._declare_ptr_func(context, "zhc_dynamic_cast", 3)

        if hasattr(obj_val, "type"):
            obj_ptr = obj_val
        else:
            obj_ptr = obj_val

        return builder.call(func, [obj_ptr, obj_type_ptr, target_type_ptr])


class CheckAssignableStrategy(_BaseTypeCheckStrategy):
    """
    检查赋值兼容性

    IR 格式：
        %result = CHECK_ASSIGNABLE target_type, source_type

    LLVM IR 生成：
        %result = call i1 @zhc_check_assignable(i8* %target_type, i8* %source_type)
    """

    opcode = Opcode.CHECK_ASSIGNABLE

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        if not instr.operands or len(instr.operands) < 2:
            logger.warning("CHECK_ASSIGNABLE 指令缺少操作数")
            return None

        target_type_val = instr.operands[0]
        source_type_val = instr.operands[1]

        func = self._declare_bool_func(context, "zhc_check_assignable", 2)

        target_type_ptr = self._get_string_ptr(builder, target_type_val, context)
        source_type_ptr = self._get_string_ptr(builder, source_type_val, context)

        return builder.call(func, [target_type_ptr, source_type_ptr])


class IsPrimitiveStrategy(_BaseTypeCheckStrategy):
    """
    检查是否基本类型

    IR 格式：
        %result = IS_PRIMITIVE type_name

    LLVM IR 生成：
        %result = call i1 @zhc_is_primitive_type(i8* %type_name)
    """

    opcode = Opcode.IS_PRIMITIVE

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        if not instr.operands or len(instr.operands) < 1:
            logger.warning("IS_PRIMITIVE 指令缺少操作数")
            return None

        type_name_val = instr.operands[0]

        func = self._declare_bool_func(context, "zhc_is_primitive_type", 1)

        type_name_ptr = self._get_string_ptr(builder, type_name_val, context)

        return builder.call(func, [type_name_ptr])


def register_type_check_strategies(factory) -> None:
    """注册所有类型检查策略到工厂

    Args:
        factory: 策略工厂实例（InstructionStrategyFactory）
    """
    strategies = [
        IsTypeStrategy(),
        IsSubtypeStrategy(),
        ImplementsInterfaceStrategy(),
        TypeEqualsStrategy(),
        SafeCastStrategy(),
        DynamicCastStrategy(),
        CheckAssignableStrategy(),
        IsPrimitiveStrategy(),
    ]
    for strategy in strategies:
        factory.register(strategy)


__all__ = [
    "IsTypeStrategy",
    "IsSubtypeStrategy",
    "ImplementsInterfaceStrategy",
    "TypeEqualsStrategy",
    "SafeCastStrategy",
    "DynamicCastStrategy",
    "CheckAssignableStrategy",
    "IsPrimitiveStrategy",
    "register_type_check_strategies",
]

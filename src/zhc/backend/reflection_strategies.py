# -*- coding: utf-8 -*-
"""
ZhC LLVM 后端 - 反射编译策略

实现反射相关操作的 LLVM IR 编译策略。

策略列表：
- TypeInfoGetStrategy: 获取类型信息
- TypeInfoNameStrategy: 获取类型名称
- TypeInfoSizeStrategy: 获取类型大小
- TypeInfoFieldsStrategy: 获取字段列表
- TypeInfoMethodsStrategy: 获取方法列表
- TypeInfoBaseStrategy: 获取父类
- FieldGetStrategy: 获取字段信息
- FieldGetValueStrategy: 动态获取字段值
- FieldSetValueStrategy: 动态设置字段值

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


class TypeInfoGetStrategy(InstructionStrategy):
    """
    获取类型信息策略

    IR 格式：
        %info = TYPE_INFO_GET type_name

    LLVM IR 生成：
        %info_ptr = call %zhc_type_info* @zhc_reflection_get_type_info(i8* %obj, i8* %type_name)
    """

    opcode = Opcode.TYPE_INFO_GET

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        # 获取类型名称（从操作数中获取）
        if not instr.operands or len(instr.operands) < 1:
            logger.warning("TYPE_INFO_GET 指令缺少类型名称操作数")
            return None

        type_name_val = instr.operands[0]

        # 声明外部函数
        func_type = ll.FunctionType(
            ll.PointerType(ll.IntType(8)),  # 返回 void* (ZhCTypeInfo*)
            [
                ll.PointerType(ll.IntType(8)),
                ll.PointerType(ll.IntType(8)),
            ],  # obj, type_name
        )
        func = context.module.get_or_insert_function(
            "zhc_reflection_get_type_info", func_type
        )

        # 准备参数
        obj_ptr = ll.Constant(ll.PointerType(ll.IntType(8)), None)  # NULL 对象指针
        type_name_ptr = self._get_string_ptr(builder, type_name_val, context)

        # 调用函数
        result = builder.call(func, [obj_ptr, type_name_ptr])

        return result

    def _get_string_ptr(self, builder, value, context):
        """获取字符串指针"""

        # 如果是常量字符串，创建全局字符串
        if hasattr(value, "const_value") and isinstance(value.const_value, str):
            return context.create_global_string(value.const_value)
        # 否则假设已经是指针
        return value


class TypeInfoNameStrategy(InstructionStrategy):
    """
    获取类型名称策略

    IR 格式：
        %name = TYPE_INFO_NAME type_name

    LLVM IR 生成：
        %name_ptr = call i8* @zhc_reflection_get_type_name(i8* %type_name)
    """

    opcode = Opcode.TYPE_INFO_NAME

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        if not instr.operands or len(instr.operands) < 1:
            logger.warning("TYPE_INFO_NAME 指令缺少类型名称操作数")
            return None

        type_name_val = instr.operands[0]

        # 声明外部函数
        func_type = ll.FunctionType(
            ll.PointerType(ll.IntType(8)),  # 返回 const char*
            [ll.PointerType(ll.IntType(8))],  # type_name
        )
        func = context.module.get_or_insert_function(
            "zhc_reflection_get_type_name", func_type
        )

        type_name_ptr = self._get_string_ptr(builder, type_name_val, context)
        result = builder.call(func, [type_name_ptr])

        return result

    def _get_string_ptr(self, builder, value, context):
        """获取字符串指针"""

        if hasattr(value, "const_value") and isinstance(value.const_value, str):
            return context.create_global_string(value.const_value)
        return value


class TypeInfoSizeStrategy(InstructionStrategy):
    """
    获取类型大小策略

    IR 格式：
        %size = TYPE_INFO_SIZE type_name

    LLVM IR 生成：
        %size = call i64 @zhc_reflection_get_type_size(i8* %type_name)
    """

    opcode = Opcode.TYPE_INFO_SIZE

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        if not instr.operands or len(instr.operands) < 1:
            logger.warning("TYPE_INFO_SIZE 指令缺少类型名称操作数")
            return None

        type_name_val = instr.operands[0]

        # 声明外部函数
        func_type = ll.FunctionType(
            ll.IntType(64),  # 返回 size_t
            [ll.PointerType(ll.IntType(8))],  # type_name
        )
        func = context.module.get_or_insert_function(
            "zhc_reflection_get_type_size", func_type
        )

        type_name_ptr = self._get_string_ptr(builder, type_name_val, context)
        result = builder.call(func, [type_name_ptr])

        return result

    def _get_string_ptr(self, builder, value, context):
        """获取字符串指针"""

        if hasattr(value, "const_value") and isinstance(value.const_value, str):
            return context.create_global_string(value.const_value)
        return value


class FieldGetValueStrategy(InstructionStrategy):
    """
    动态获取字段值策略

    IR 格式：
        %value = FIELD_GET_VALUE obj, type_name, field_name

    LLVM IR 生成：
        %success = call i32 @zhc_reflection_get_field_value(
            i8* %obj,
            i8* %type_name,
            i8* %field_name,
            i8* %value_buf,
            i64 %buf_size
        )
    """

    opcode = Opcode.FIELD_GET_VALUE

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        if not instr.operands or len(instr.operands) < 3:
            logger.warning("FIELD_GET_VALUE 指令缺少操作数")
            return None

        obj_val = instr.operands[0]
        type_name_val = instr.operands[1]
        field_name_val = instr.operands[2]

        # 声明外部函数
        func_type = ll.FunctionType(
            ll.IntType(32),  # 返回 int
            [
                ll.PointerType(ll.IntType(8)),  # obj
                ll.PointerType(ll.IntType(8)),  # type_name
                ll.PointerType(ll.IntType(8)),  # field_name
                ll.PointerType(ll.IntType(8)),  # value_buf
                ll.IntType(64),  # buf_size
            ],
        )
        func = context.module.get_or_insert_function(
            "zhc_reflection_get_field_value", func_type
        )

        # 准备参数
        obj_ptr = builder.bitcast(obj_val, ll.PointerType(ll.IntType(8)))
        type_name_ptr = self._get_string_ptr(builder, type_name_val, context)
        field_name_ptr = self._get_string_ptr(builder, field_name_val, context)

        # 分配值缓冲区（假设最大 64 字节）
        value_buf = builder.alloca(
            ll.ArrayType(ll.IntType(8), 64), name="field_value_buf"
        )
        value_buf_ptr = builder.bitcast(value_buf, ll.PointerType(ll.IntType(8)))
        buf_size = ll.Constant(ll.IntType(64), 64)

        # 调用函数
        builder.call(
            func, [obj_ptr, type_name_ptr, field_name_ptr, value_buf_ptr, buf_size]
        )

        # 返回缓冲区指针
        return value_buf_ptr

    def _get_string_ptr(self, builder, value, context):
        """获取字符串指针"""

        if hasattr(value, "const_value") and isinstance(value.const_value, str):
            return context.create_global_string(value.const_value)
        return value


class FieldSetValueStrategy(InstructionStrategy):
    """
    动态设置字段值策略

    IR 格式：
        FIELD_SET_VALUE obj, type_name, field_name, value

    LLVM IR 生成：
        %success = call i32 @zhc_reflection_set_field_value(
            i8* %obj,
            i8* %type_name,
            i8* %field_name,
            i8* %value,
            i64 %value_size
        )
    """

    opcode = Opcode.FIELD_SET_VALUE

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        if not instr.operands or len(instr.operands) < 4:
            logger.warning("FIELD_SET_VALUE 指令缺少操作数")
            return None

        obj_val = instr.operands[0]
        type_name_val = instr.operands[1]
        field_name_val = instr.operands[2]
        value_val = instr.operands[3]

        # 声明外部函数
        func_type = ll.FunctionType(
            ll.IntType(32),  # 返回 int
            [
                ll.PointerType(ll.IntType(8)),  # obj
                ll.PointerType(ll.IntType(8)),  # type_name
                ll.PointerType(ll.IntType(8)),  # field_name
                ll.PointerType(ll.IntType(8)),  # value
                ll.IntType(64),  # value_size
            ],
        )
        func = context.module.get_or_insert_function(
            "zhc_reflection_set_field_value", func_type
        )

        # 准备参数
        obj_ptr = builder.bitcast(obj_val, ll.PointerType(ll.IntType(8)))
        type_name_ptr = self._get_string_ptr(builder, type_name_val, context)
        field_name_ptr = self._get_string_ptr(builder, field_name_val, context)
        value_ptr = builder.bitcast(value_val, ll.PointerType(ll.IntType(8)))
        value_size = ll.Constant(ll.IntType(64), 8)  # 假设 8 字节

        # 调用函数
        result = builder.call(
            func, [obj_ptr, type_name_ptr, field_name_ptr, value_ptr, value_size]
        )

        return result

    def _get_string_ptr(self, builder, value, context):
        """获取字符串指针"""

        if hasattr(value, "const_value") and isinstance(value.const_value, str):
            return context.create_global_string(value.const_value)
        return value


# ============================================================================
# 策略注册函数
# ============================================================================


def register_reflection_strategies():
    """注册所有反射策略到策略工厂"""
    from .llvm_instruction_strategy import InstructionStrategyFactory

    strategies = [
        TypeInfoGetStrategy,
        TypeInfoNameStrategy,
        TypeInfoSizeStrategy,
        FieldGetValueStrategy,
        FieldSetValueStrategy,
    ]

    for strategy_cls in strategies:
        InstructionStrategyFactory.register(strategy_cls)

    logger.info(f"已注册 {len(strategies)} 个反射策略")


__all__ = [
    "TypeInfoGetStrategy",
    "TypeInfoNameStrategy",
    "TypeInfoSizeStrategy",
    "FieldGetValueStrategy",
    "FieldSetValueStrategy",
    "register_reflection_strategies",
]

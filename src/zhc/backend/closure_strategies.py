# -*- coding: utf-8 -*-
"""
ZhC LLVM 后端 - 闭包编译策略

实现闭包相关的 LLVM IR 编译策略。

策略列表：
- LambdaStrategy: Lambda 表达式编译
- ClosureCreateStrategy: 创建闭包
- ClosureCallStrategy: 闭包调用
- UpvalueGetStrategy: 获取 upvalue
- UpvalueSetStrategy: 设置 upvalue

作者：远
日期：2026-04-10
"""

import logging
from typing import Optional, TYPE_CHECKING

from zhc.ir.opcodes import Opcode
from .llvm_instruction_strategy import InstructionStrategy

if TYPE_CHECKING:
    import llvmlite.ir as ll
    from zhc.backend.compilation_context import CompilationContext

logger = logging.getLogger(__name__)


class LambdaStrategy(InstructionStrategy):
    """
    Lambda 表达式编译策略

    Lambda 表达式会创建一个闭包，包含：
    1. 函数指针
    2. upvalue 环境

    IR 格式：
        %closure = LAMBDA

    LLVM IR 生成：
        1. 创建闭包结构体类型
        2. 分配闭包内存
        3. 初始化函数指针和 upvalue 环境
    """

    opcode = Opcode.LAMBDA

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        # 获取闭包类型信息（从 result 中获取）
        if not instr.result:
            logger.warning("Lambda 指令没有结果值")
            return None

        # 创建闭包结构体类型
        # struct closure {
        #     void* func_ptr;        // 函数指针
        #     void** upvalues;       // upvalue 数组指针
        #     i32 upvalue_count;     // upvalue 数量
        # }
        closure_struct_type = self._create_closure_struct_type(context)

        # 分配闭包内存
        closure_ptr = builder.alloca(
            closure_struct_type, name=context.get_result_name(instr) or "closure"
        )

        # TODO: 实际实现需要：
        # 1. 为 lambda 体创建内部函数
        # 2. 捕获外部变量（upvalue）
        # 3. 初始化闭包结构体

        # 目前返回一个空指针作为占位
        void_ptr_ty = ll.IntType(8).as_pointer()
        result = builder.bitcast(closure_ptr, void_ptr_ty, name="closure_ptr")

        context.store_result(instr, result)
        return result

    def _create_closure_struct_type(self, context: "CompilationContext") -> "ll.Type":
        """创建闭包结构体类型"""
        import llvmlite.ir as ll

        # 检查是否已定义
        struct_name = "struct.ZhCClosure"
        if struct_name in context.module.globals:
            return context.module.globals[struct_name].type.pointee

        # 定义结构体字段
        void_ptr_ty = ll.IntType(8).as_pointer()
        void_ptr_ptr_ty = void_ptr_ty.as_pointer()
        i32_ty = ll.IntType(32)

        # 创建结构体类型
        struct_ty = ll.LiteralStructType(
            [void_ptr_ty, void_ptr_ptr_ty, i32_ty], name=struct_name
        )

        return struct_ty


class ClosureCreateStrategy(InstructionStrategy):
    """
    创建闭包策略

    IR 格式：
        %closure = CLOSURE_CREATE %func_ptr, %upvalue1, %upvalue2, ...

    LLVM IR 生成：
        1. 分配闭包结构体
        2. 设置函数指针
        3. 设置 upvalue 数组
    """

    opcode = Opcode.CLOSURE_CREATE

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        if not instr.operands:
            logger.warning("CLOSURE_CREATE 指令缺少操作数")
            return None

        # 获取函数指针
        func_ptr = context.get_value(instr.operands[0])

        # 获取 upvalue 列表
        upvalues = [context.get_value(op) for op in instr.operands[1:]]
        upvalue_count = len(upvalues)

        # 创建闭包结构体
        closure_struct_type = self._get_or_create_closure_struct_type(context)
        closure_ptr = builder.alloca(
            closure_struct_type, name=context.get_result_name(instr) or "closure"
        )

        # 设置函数指针（第一个字段）
        void_ptr_ty = ll.IntType(8).as_pointer()
        func_ptr_casted = builder.bitcast(func_ptr, void_ptr_ty)
        func_ptr_field = builder.gep(
            closure_ptr,
            [ll.Constant(ll.IntType(32), 0), ll.Constant(ll.IntType(32), 0)],
        )
        builder.store(func_ptr_casted, func_ptr_field)

        # 设置 upvalue 数组指针（第二个字段）
        if upvalue_count > 0:
            # 分配 upvalue 数组
            upvalue_array_type = ll.ArrayType(void_ptr_ty, upvalue_count)
            upvalue_array = builder.alloca(upvalue_array_type, name="upvalues")

            # 存储每个 upvalue
            for i, upvalue in enumerate(upvalues):
                elem_ptr = builder.gep(
                    upvalue_array,
                    [ll.Constant(ll.IntType(32), 0), ll.Constant(ll.IntType(32), i)],
                )
                upvalue_casted = builder.bitcast(upvalue, void_ptr_ty)
                builder.store(upvalue_casted, elem_ptr)

            # 设置 upvalue 数组指针
            upvalue_ptr_field = builder.gep(
                closure_ptr,
                [ll.Constant(ll.IntType(32), 0), ll.Constant(ll.IntType(32), 1)],
            )
            upvalue_array_ptr = builder.bitcast(upvalue_array, void_ptr_ty.as_pointer())
            builder.store(upvalue_array_ptr, upvalue_ptr_field)

        # 设置 upvalue 数量（第三个字段）
        count_field = builder.gep(
            closure_ptr,
            [ll.Constant(ll.IntType(32), 0), ll.Constant(ll.IntType(32), 2)],
        )
        builder.store(ll.Constant(ll.IntType(32), upvalue_count), count_field)

        # 返回闭包指针
        result = builder.bitcast(closure_ptr, void_ptr_ty, name="closure_ptr")
        context.store_result(instr, result)
        return result

    def _get_or_create_closure_struct_type(
        self, context: "CompilationContext"
    ) -> "ll.Type":
        """获取或创建闭包结构体类型"""
        import llvmlite.ir as ll

        struct_name = "struct.ZhCClosure"
        if struct_name in context.module.globals:
            return context.module.globals[struct_name].type.pointee

        void_ptr_ty = ll.IntType(8).as_pointer()
        void_ptr_ptr_ty = void_ptr_ty.as_pointer()
        i32_ty = ll.IntType(32)

        return ll.LiteralStructType(
            [void_ptr_ty, void_ptr_ptr_ty, i32_ty], name=struct_name
        )


class ClosureCallStrategy(InstructionStrategy):
    """
    闭包调用策略

    IR 格式：
        %result = CLOSURE_CALL %closure, %arg1, %arg2, ...

    LLVM IR 生成：
        1. 从闭包结构体中获取函数指针
        2. 调用函数指针
    """

    opcode = Opcode.CLOSURE_CALL

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        if not instr.operands:
            logger.warning("CLOSURE_CALL 指令缺少操作数")
            return None

        # 获取闭包指针
        closure_ptr = context.get_value(instr.operands[0])

        # 获取参数列表
        args = [context.get_value(op) for op in instr.operands[1:]]

        # 从闭包结构体中获取函数指针
        void_ptr_ty = ll.IntType(8).as_pointer()
        closure_ptr_casted = builder.bitcast(closure_ptr, void_ptr_ty.as_pointer())

        func_ptr_field = builder.gep(
            closure_ptr_casted,
            [ll.Constant(ll.IntType(32), 0), ll.Constant(ll.IntType(32), 0)],
        )
        func_ptr = builder.load(func_ptr_field, name="func_ptr")

        # 创建函数类型（假设返回 i32，参数类型从 args 推断）
        # TODO: 应该从闭包类型信息中获取准确的函数签名
        arg_types = [arg.type for arg in args]
        func_ty = ll.FunctionType(ll.IntType(32), arg_types)
        func_ptr_typed = builder.bitcast(func_ptr, func_ty.as_pointer())

        # 调用函数
        result = builder.call(
            func_ptr_typed, args, name=context.get_result_name(instr) or ""
        )

        if result and instr.result:
            context.store_result(instr, result)

        return result


class UpvalueGetStrategy(InstructionStrategy):
    """
    获取 upvalue 策略

    IR 格式：
        %value = UPVALUE_GET %closure, %index

    LLVM IR 生成：
        1. 从闭包结构体中获取 upvalue 数组指针
        2. 根据 index 获取对应的 upvalue
    """

    opcode = Opcode.UPVALUE_GET

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        if len(instr.operands) < 2:
            logger.warning("UPVALUE_GET 指令缺少操作数")
            return None

        # 获取闭包指针和索引
        closure_ptr = context.get_value(instr.operands[0])
        index_value = context.get_value(instr.operands[1])

        # 获取索引常量值
        index = 0
        if hasattr(index_value, "constant"):
            index = index_value.constant

        # 从闭包结构体中获取 upvalue 数组指针
        void_ptr_ty = ll.IntType(8).as_pointer()
        closure_ptr_casted = builder.bitcast(closure_ptr, void_ptr_ty.as_pointer())

        upvalue_ptr_field = builder.gep(
            closure_ptr_casted,
            [ll.Constant(ll.IntType(32), 0), ll.Constant(ll.IntType(32), 1)],
        )
        upvalue_array_ptr = builder.load(upvalue_ptr_field, name="upvalue_array")

        # 获取指定索引的 upvalue
        elem_ptr = builder.gep(
            upvalue_array_ptr, [ll.Constant(ll.IntType(32), index)], name="upvalue_ptr"
        )
        upvalue = builder.load(
            elem_ptr, name=context.get_result_name(instr) or "upvalue"
        )

        context.store_result(instr, upvalue)
        return upvalue


class UpvalueSetStrategy(InstructionStrategy):
    """
    设置 upvalue 策略

    IR 格式：
        UPVALUE_SET %closure, %index, %value

    LLVM IR 生成：
        1. 从闭包结构体中获取 upvalue 数组指针
        2. 根据 index 设置对应的 upvalue
    """

    opcode = Opcode.UPVALUE_SET

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        if len(instr.operands) < 3:
            logger.warning("UPVALUE_SET 指令缺少操作数")
            return None

        # 获取闭包指针、索引和值
        closure_ptr = context.get_value(instr.operands[0])
        index_value = context.get_value(instr.operands[1])
        value = context.get_value(instr.operands[2])

        # 获取索引常量值
        index = 0
        if hasattr(index_value, "constant"):
            index = index_value.constant

        # 从闭包结构体中获取 upvalue 数组指针
        void_ptr_ty = ll.IntType(8).as_pointer()
        closure_ptr_casted = builder.bitcast(closure_ptr, void_ptr_ty.as_pointer())

        upvalue_ptr_field = builder.gep(
            closure_ptr_casted,
            [ll.Constant(ll.IntType(32), 0), ll.Constant(ll.IntType(32), 1)],
        )
        upvalue_array_ptr = builder.load(upvalue_ptr_field, name="upvalue_array")

        # 设置指定索引的 upvalue
        elem_ptr = builder.gep(
            upvalue_array_ptr, [ll.Constant(ll.IntType(32), index)], name="upvalue_ptr"
        )

        # 类型转换
        value_casted = builder.bitcast(value, void_ptr_ty)
        builder.store(value_casted, elem_ptr)

        return None

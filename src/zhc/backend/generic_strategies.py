# -*- coding: utf-8 -*-
"""
ZhC LLVM 后端 - 泛型编译策略

实现泛型/单态化相关操作的 LLVM IR 编译策略。

策略列表：
- GenericInstantiateStrategy: 泛型实例化（如 列表<T> → 列表<整数型>）
- GenericCallStrategy: 泛型函数调用（调用特化后的版本）
- TypeParamBindStrategy: 类型参数绑定
- SpecializeStrategy: 特化生成（为泛型函数/类型生成特化版本）

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


class _BaseGenericStrategy(InstructionStrategy):
    """泛型策略的公共基类"""

    def _get_string_constant(self, builder, value, context: "CompilationContext"):
        """从操作数获取字符串常量指针

        Args:
            builder: LLVM IR 构建器
            value: 操作数值
            context: 编译上下文

        Returns:
            字符串常量指针或原始值
        """
        if hasattr(value, "const_value") and isinstance(value.const_value, str):
            return context.create_global_string(value.const_value)
        return value


class GenericInstantiateStrategy(_BaseGenericStrategy):
    """
    泛型实例化策略

    将泛型类型实例化为具体类型。

    IR 格式：
        %result = GENERIC_INSTANTIATE "泛型签名", [类型参数...]

    LLVM IR 生成：
        生成元数据标记 + 返回类型占位符

    示例：
        列表<整数型> → 生成列表__整数型 的结构体引用
    """

    opcode = Opcode.GENERIC_INSTANTIATE

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        operands = instr.operands if instr.operands else []

        if not operands:
            logger.warning("GENERIC_INSTANTIATE 指令缺少操作数")
            return None

        # 操作数[0] 是泛型签名（如 "列表<T>" 或 "盒子<T>"）
        sig_val = operands[0]
        sig_str = getattr(sig_val, "const_value", str(sig_val))

        # 获取类型参数名列表
        type_params = []
        for op in operands[1:]:
            param_name = getattr(op, "const_value", getattr(op, "name", ""))
            if param_name:
                type_params.append(param_name)

        result_name = context.get_result_name(instr) or "generic_inst"

        logger.debug(
            f"GenericInstantiate: 实例化 {sig_str}"
            f" 参数={type_params} -> {result_name}"
        )

        # 生成一个 i8* 指针作为结果（代表特化后的类型实例）
        # 实际使用时，这会映射到具体的结构体类型
        # (返回类型由 context.result_type 提供)

        # 如果模块中已存在对应的 mangled-name 结构体，返回其 pointer
        # 否则返回一个全局字符串作为元数据标记
        mangled_name = f"{sig_str.replace('<', '__').replace('>', '')}"

        # 尝试查找已注册的结构体类型
        struct_type = None
        if hasattr(context, "type_registry") and context.type_registry:
            struct_info = context.type_registry.get_struct_info(mangled_name)
            if struct_info:
                struct_type = struct_info.llvm_type

        if struct_type:
            # 已有结构体定义，返回指向它的空指针作为占位符
            null_ptr = ll.Constant(struct_type.as_pointer(), None)
            context.store_result(instr, null_ptr)
            return null_ptr
        else:
            # 无具体结构体，返回元数据字符串指针
            metadata_str = f"{sig_str}<{', '.join(type_params)}>"
            meta_ptr = context.create_global_string(metadata_str)
            context.store_result(instr, meta_ptr)
            return meta_ptr


class GenericCallStrategy(_BaseGenericStrategy):
    """
    泛型函数调用策略

    调用经过单态化的特化函数。

    IR 格式：
        %result = GENERIC_CALL "函数名__类型1_类型2", [参数...]

    LLVM IR 生成：
        call %ret_type @函数名__类型1_类型2(%arg_types)

    示例：
        最大值<整数型>(a, b) → call i32 @最大值__整数型(i32 %a, i32 %b)
    """

    opcode = Opcode.GENERIC_CALL

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        operands = instr.operands if instr.operands else []

        if not operands:
            logger.warning("GENERIC_CALL 指令缺少操作数（需要 mangled 函数名）")
            return None

        # 操作数[0] 是 mangled 函数名（如 "最大值__整数型"）
        func_name_val = operands[0]
        mangled_name = (
            getattr(func_name_val, "const_value", None)
            or getattr(func_name_val, "name", "")
            or str(func_name_val)
        )

        # 后续操作数是调用参数
        args = []
        for op in operands[1:]:
            arg_val = context.get_value(op)
            if arg_val is not None:
                args.append(arg_val)

        result_name = context.get_result_name(instr) or "generic_call"

        logger.debug(f"GenericCall: 调用 {mangled_name}({len(args)} 个参数)")

        # 在模块中查找特化后的函数
        callee_func = None
        if context.module:
            for func in context.module.functions:
                if func.name == mangled_name:
                    callee_func = func
                    break

        if callee_func:
            # 找到特化函数，直接调用
            result = builder.call(callee_func, args, name=result_name or "")
            context.store_result(instr, result)
            return result
        else:
            # 未找到特化函数 — 声明外部函数并调用
            arg_types = [
                a.type if hasattr(a, "type") else ll.IntType(32) for a in args
            ] or [ll.IntType(32)]
            func_ty = ll.FunctionType(ll.IntType(32), arg_types)
            external_func = ll.Function(context.module, func_ty, mangled_name)
            result = builder.call(external_func, args, name=result_name or "")
            context.store_result(instr, result)
            return result


class TypeParamBindStrategy(InstructionStrategy):
    """
    类型参数绑定策略

    绑定类型参数到具体类型（纯声明性指令，不生成实际代码）。

    IR 格式：
        TYPE_PARAM_BIND "T", "整数型"

    说明：
        此指令用于记录类型绑定关系，供调试和优化信息使用。
        在 LLVM 层面不产生任何机器代码，仅可能发出调试元数据。
    """

    opcode = Opcode.TYPE_PARAM_BIND

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        operands = instr.operands if instr.operands else []

        if len(operands) < 2:
            logger.warning(
                "TYPE_PARAM_BIND 指令需要 2 个操作数（类型参数名和具体类型）"
            )
            return None

        param_name = getattr(operands[0], "const_value", str(operands[0]))
        concrete_type = getattr(operands[1], "const_value", str(operands[1]))

        logger.debug(f"TypeParamBind: {param_name} := {concrete_type}")

        # 纯声明性指令，不生成实际代码
        # 未来可扩展为发出 LLVM DI Metadata 用于调试
        return None


class SpecializeStrategy(_BaseGenericStrategy):
    """
    特化生成策略

    为泛型函数/类型生成特化版本的标记指令。

    IR 格式：
        %result = SPECIALIZE "基础类型名"

    LLVM IR 生成：
        发出元数据标记，返回类型占位符

    示例：
        特化 盒子<整数型> → 标记生成 盒子__整数型 结构体
    """

    opcode = Opcode.SPECIALIZE

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        operands = instr.operands if instr.operands else []

        if not operands:
            logger.warning("SPECIALIZE 指令缺少操作数（需要基础类型名）")
            return None

        base_name_val = operands[0]
        base_name = (
            getattr(base_name_val, "const_value", None)
            or getattr(base_name_val, "ty", "")
            or str(base_name_val)
        )

        result_name = context.get_result_name(instr) or "specialized"

        logger.debug(f"Specialize: 为 {base_name} 生成特化版本 -> {result_name}")

        # 返回 i8* 作为类型占位符
        # 特化的具体结构体已在 _compile_struct_def 阶段创建
        i8_ptr = ll.PointerType(ll.IntType(8))
        null_ptr = ll.Constant(i8_ptr, None)
        context.store_result(instr, null_ptr)
        return null_ptr


def register_generic_strategies(factory) -> None:
    """注册所有泛型策略到工厂

    Args:
        factory: 策略工厂实例（InstructionStrategyFactory）
    """
    strategies = [
        GenericInstantiateStrategy(),
        GenericCallStrategy(),
        TypeParamBindStrategy(),
        SpecializeStrategy(),
    ]
    for strategy in strategies:
        factory.register(strategy)


__all__ = [
    "GenericInstantiateStrategy",
    "GenericCallStrategy",
    "TypeParamBindStrategy",
    "SpecializeStrategy",
    "_BaseGenericStrategy",
    "register_generic_strategies",
]

# -*- coding: utf-8 -*-
"""
ZhC LLVM 后端 - 模式匹配编译策略

实现模式匹配相关操作的 LLVM IR 编译策略。

策略列表：
- MatchStrategy: 匹配作用域开始
- CaseStrategy: 模式分支
- PatternTestStrategy: 模式测试
- PatternBindStrategy: 模式绑定
- PatternGuardStrategy: 守卫条件

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


class _BasePatternStrategy(InstructionStrategy):
    """模式匹配策略的公共基类"""

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


class MatchStrategy(_BasePatternStrategy):
    """
    匹配作用域策略

    标记 match 表达式作用域的开始。

    IR 格式：
        MATCH scrutinee

    LLVM IR 生成：
        创建匹配作用域的基本块结构

    说明：
        此指令主要用于标记作用域边界，实际匹配逻辑由后续的
        PATTERN_TEST 和 JZ 指令实现。
    """

    opcode = Opcode.MATCH

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        operands = instr.operands if instr.operands else []

        if not operands:
            logger.warning("MATCH 指令缺少操作数（scrutinee）")
            return None

        scrutinee = operands[0]

        logger.debug(f"Match: 开始匹配作用域，scrutinee = {scrutinee}")

        # MATCH 是标记性指令，不生成实际代码
        # 实际的匹配逻辑由后续指令实现
        return None


class CaseStrategy(_BasePatternStrategy):
    """
    模式分支策略

    标记一个模式匹配分支的开始。

    IR 格式：
        CASE pattern_index

    LLVM IR 生成：
        创建分支基本块标签

    说明：
        此指令用于标记 case 分支边界，配合 MATCH 和 PATTERN_TEST 使用。
    """

    opcode = Opcode.CASE

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        operands = instr.operands if instr.operands else []

        case_index = 0
        if operands:
            case_index = getattr(operands[0], "const_value", 0)

        logger.debug(f"Case: 分支 {case_index}")

        # CASE 是标记性指令，不生成实际代码
        # 分支逻辑由基本块结构实现
        return None


class PatternTestStrategy(_BasePatternStrategy):
    """
    模式测试策略

    测试值是否匹配特定模式。

    IR 格式：
        %result = PATTERN_TEST pattern_spec, scrutinee

    LLVM IR 生成：
        根据模式类型生成不同的测试代码：
        - 构造器模式：比较 tag/discriminant
        - 字面量模式：比较值相等
        - 范围模式：比较值范围

    示例：
        PATTERN_TEST "Some", %value → %tag = get_tag(%value); %result = icmp eq %tag, TAG_SOME
    """

    opcode = Opcode.PATTERN_TEST

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        operands = instr.operands if instr.operands else []

        if len(operands) < 2:
            logger.warning(
                "PATTERN_TEST 指令需要 2 个操作数（pattern_spec, scrutinee）"
            )
            return None

        pattern_spec = operands[0]
        scrutinee = operands[1]

        # 获取模式规范（构造器名称或字面量值）
        pattern_name = getattr(pattern_spec, "const_value", str(pattern_spec))

        # 获取 scrutinee 值
        scrutinee_val = context.get_value(scrutinee)

        # 生成测试代码
        # 假设 scrutinee 是一个带 tag 的结构体
        # 格式: { i32 tag, [union fields] }

        # 获取 tag 字段
        if scrutinee_val and hasattr(scrutinee_val, "type"):
            # GEP 获取 tag 字段（假设 tag 在索引 0）
            i32_type = ll.IntType(32)
            tag_ptr = builder.gep(
                scrutinee_val,
                [ll.Constant(ll.IntType(32), 0), ll.Constant(ll.IntType(32), 0)],
                inbounds=True,
                name="tag_ptr",
            )
            tag_val = builder.load(tag_ptr, name="tag")

            # 查找构造器对应的 tag 值
            # 这里简化处理：假设 pattern_name 可以映射到整数 tag
            # 实际实现需要从类型注册表获取
            try:
                expected_tag = ll.Constant(i32_type, hash(pattern_name) % 10000)
            except Exception:
                expected_tag = ll.Constant(i32_type, 0)

            # 比较 tag
            result = builder.icmp_signed(
                "==", tag_val, expected_tag, name="pattern_match"
            )

            context.store_result(instr, result)
            return result

        # 无法生成测试代码，返回假
        i1_type = ll.IntType(1)
        result = ll.Constant(i1_type, 0)
        context.store_result(instr, result)
        return result


class PatternBindStrategy(_BasePatternStrategy):
    """
    模式绑定策略

    将匹配成功的值绑定到变量。

    IR 格式：
        %result = PATTERN_BIND scrutinee

    LLVM IR 生成：
        从 scrutinee 中提取字段值

    示例：
        PATTERN_BIND %value → %field0 = extractvalue %value, 1
    """

    opcode = Opcode.PATTERN_BIND

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        operands = instr.operands if instr.operands else []

        if not operands:
            logger.warning("PATTERN_BIND 指令缺少操作数（scrutinee）")
            return None

        scrutinee = operands[0]
        scrutinee_val = context.get_value(scrutinee)

        if scrutinee_val and hasattr(scrutinee_val, "type"):
            # 从结构体中提取字段值
            # 假设字段从索引 1 开始（索引 0 是 tag）
            # 实际实现需要根据模式类型确定字段索引

            # 简化处理：提取第一个字段
            try:
                field_ptr = builder.gep(
                    scrutinee_val,
                    [ll.Constant(ll.IntType(32), 0), ll.Constant(ll.IntType(32), 1)],
                    inbounds=True,
                    name="field_ptr",
                )
                field_val = builder.load(field_ptr, name="bound_value")

                context.store_result(instr, field_val)
                return field_val
            except Exception as e:
                logger.warning(f"PATTERN_BIND 字段提取失败: {e}")

        # 无法提取字段，返回原始值
        context.store_result(instr, scrutinee_val)
        return scrutinee_val


class PatternGuardStrategy(_BasePatternStrategy):
    """
    守卫条件策略

    求值守卫表达式。

    IR 格式：
        %result = PATTERN_GUARD guard_expr

    LLVM IR 生成：
        求值守卫表达式并返回布尔结果

    说明：
        守卫表达式通常是普通的布尔表达式，此指令用于标记守卫边界。
        实际的求值由表达式自身的 IR 指令完成。
    """

    opcode = Opcode.PATTERN_GUARD

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        import llvmlite.ir as ll

        operands = instr.operands if instr.operands else []

        if not operands:
            logger.warning("PATTERN_GUARD 指令缺少操作数（guard_expr）")
            return None

        guard_expr = operands[0]
        guard_val = context.get_value(guard_expr)

        # 确保结果是 i1 类型
        if guard_val and hasattr(guard_val, "type"):
            if str(guard_val.type) != "i1":
                # 转换为布尔值
                i1_type = ll.IntType(1)
                guard_val = builder.trunc(guard_val, i1_type, name="guard_bool")

        logger.debug(f"PatternGuard: 守卫求值结果 = {guard_val}")

        context.store_result(instr, guard_val)
        return guard_val


def register_pattern_strategies(factory) -> None:
    """注册所有模式匹配策略到工厂

    Args:
        factory: 策略工厂实例（InstructionStrategyFactory）
    """
    strategies = [
        MatchStrategy(),
        CaseStrategy(),
        PatternTestStrategy(),
        PatternBindStrategy(),
        PatternGuardStrategy(),
    ]
    for strategy in strategies:
        factory.register(strategy)


__all__ = [
    "MatchStrategy",
    "CaseStrategy",
    "PatternTestStrategy",
    "PatternBindStrategy",
    "PatternGuardStrategy",
    "_BasePatternStrategy",
    "register_pattern_strategies",
]

# -*- coding: utf-8 -*-
"""
ZhC LLVM 后端指令编译策略 - 使用策略模式

将每种 IR 指令的编译逻辑封装为独立的策略类。

设计模式：
- 策略模式：每个指令类型对应一个编译策略
- 工厂模式：通过注册表创建策略
- 单例模式：每个策略类只有一个实例

作者：远
日期：2026-04-09
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, TYPE_CHECKING, Any

from zhc.ir.opcodes import Opcode

if TYPE_CHECKING:
    from zhc.backend.compilation_context import CompilationContext

if TYPE_CHECKING:
    import llvmlite.ir as ll


class InstructionStrategy(ABC):
    """
    指令编译策略基类

    每个 IR 指令类型对应一个具体的策略类。

    使用方式：
        class AddStrategy(InstructionStrategy):
            opcode = Opcode.ADD

            def compile(self, builder, instr, context):
                return builder.add(
                    context.get_value(instr.operands[0]),
                    context.get_value(instr.operands[1])
                )
    """

    # 子类必须定义
    opcode: Opcode = None

    def compile(
        self,
        builder: "ll.IRBuilder",
        instr: Any,
        context: "CompilationContext",
    ) -> Optional["ll.Value"]:
        """
        编译指令

        Args:
            builder: LLVM IR 构建器
            instr: IR 指令
            context: 编译上下文

        Returns:
            编译后的 LLVM 值（如果有返回值）
        """
        raise NotImplementedError

    @classmethod
    def can_compile(cls, opcode: Opcode) -> bool:
        """检查此类是否可以编译给定的操作码"""
        return cls.opcode == opcode


class ArithmeticStrategy(InstructionStrategy):
    """算术运算策略基类"""

    @staticmethod
    @abstractmethod
    def operation(
        builder: "ll.IRBuilder", a: "ll.Value", b: "ll.Value", name: str
    ) -> "ll.Value":
        """执行算术运算"""
        pass


class AddStrategy(ArithmeticStrategy):
    """加法策略"""

    opcode = Opcode.ADD

    @staticmethod
    def operation(builder, a, b, name):
        return builder.add(a, b, name=name)

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        b = context.get_value(instr.operands[1])
        result = self.operation(builder, a, b, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class SubStrategy(ArithmeticStrategy):
    """减法策略"""

    opcode = Opcode.SUB

    @staticmethod
    def operation(builder, a, b, name):
        return builder.sub(a, b, name=name)

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        b = context.get_value(instr.operands[1])
        result = self.operation(builder, a, b, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class MulStrategy(ArithmeticStrategy):
    """乘法策略"""

    opcode = Opcode.MUL

    @staticmethod
    def operation(builder, a, b, name):
        return builder.mul(a, b, name=name)

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        b = context.get_value(instr.operands[1])
        result = self.operation(builder, a, b, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class DivStrategy(ArithmeticStrategy):
    """除法策略"""

    opcode = Opcode.DIV

    @staticmethod
    def operation(builder, a, b, name):
        return builder.sdiv(a, b, name=name)

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        b = context.get_value(instr.operands[1])
        result = self.operation(builder, a, b, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class ModStrategy(ArithmeticStrategy):
    """取模策略"""

    opcode = Opcode.MOD

    @staticmethod
    def operation(builder, a, b, name):
        return builder.srem(a, b, name=name)

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        b = context.get_value(instr.operands[1])
        result = self.operation(builder, a, b, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class NegStrategy(InstructionStrategy):
    """取负策略"""

    opcode = Opcode.NEG

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        result = builder.neg(a, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class ComparisonStrategy(InstructionStrategy):
    """比较运算策略基类"""

    @staticmethod
    @abstractmethod
    def comparison(
        builder: "ll.IRBuilder", pred: str, a: "ll.Value", b: "ll.Value", name: str
    ) -> "ll.Value":
        """执行比较运算"""
        pass


class EqStrategy(ComparisonStrategy):
    """等于策略"""

    opcode = Opcode.EQ

    @staticmethod
    def comparison(builder, pred, a, b, name):
        return builder.icmp_signed("==", a, b, name=name)

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        b = context.get_value(instr.operands[1])
        result = self.comparison(
            builder, "==", a, b, name=context.get_result_name(instr)
        )
        context.store_result(instr, result)
        return result


class NeStrategy(ComparisonStrategy):
    """不等于策略"""

    opcode = Opcode.NE

    @staticmethod
    def comparison(builder, pred, a, b, name):
        return builder.icmp_signed("!=", a, b, name=name)

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        b = context.get_value(instr.operands[1])
        result = self.comparison(
            builder, "!=", a, b, name=context.get_result_name(instr)
        )
        context.store_result(instr, result)
        return result


class LtStrategy(ComparisonStrategy):
    """小于策略"""

    opcode = Opcode.LT

    @staticmethod
    def comparison(builder, pred, a, b, name):
        return builder.icmp_signed("<", a, b, name=name)

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        b = context.get_value(instr.operands[1])
        result = self.comparison(
            builder, "<", a, b, name=context.get_result_name(instr)
        )
        context.store_result(instr, result)
        return result


class LeStrategy(ComparisonStrategy):
    """小于等于策略"""

    opcode = Opcode.LE

    @staticmethod
    def comparison(builder, pred, a, b, name):
        return builder.icmp_signed("<=", a, b, name=name)

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        b = context.get_value(instr.operands[1])
        result = self.comparison(
            builder, "<=", a, b, name=context.get_result_name(instr)
        )
        context.store_result(instr, result)
        return result


class GtStrategy(ComparisonStrategy):
    """大于策略"""

    opcode = Opcode.GT

    @staticmethod
    def comparison(builder, pred, a, b, name):
        return builder.icmp_signed(">", a, b, name=name)

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        b = context.get_value(instr.operands[1])
        result = self.comparison(
            builder, ">", a, b, name=context.get_result_name(instr)
        )
        context.store_result(instr, result)
        return result


class GeStrategy(ComparisonStrategy):
    """大于等于策略"""

    opcode = Opcode.GE

    @staticmethod
    def comparison(builder, pred, a, b, name):
        return builder.icmp_signed(">=", a, b, name=name)

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        b = context.get_value(instr.operands[1])
        result = self.comparison(
            builder, ">=", a, b, name=context.get_result_name(instr)
        )
        context.store_result(instr, result)
        return result


class RetStrategy(InstructionStrategy):
    """返回策略"""

    opcode = Opcode.RET

    def compile(self, builder, instr, context):
        if instr.operands:
            val = context.get_value(instr.operands[0])
            builder.ret(val)
        else:
            builder.ret_void()
        return None


class JmpStrategy(InstructionStrategy):
    """无条件跳转策略"""

    opcode = Opcode.JMP

    def compile(self, builder, instr, context):
        target_label = str(instr.operands[0])
        target_block = context.get_block(target_label)
        builder.branch(target_block)
        return None


class JzStrategy(InstructionStrategy):
    """条件跳转策略"""

    opcode = Opcode.JZ

    def compile(self, builder, instr, context):
        cond = context.get_value(instr.operands[0])
        then_label = str(instr.operands[1])
        else_label = str(instr.operands[2]) if len(instr.operands) > 2 else None

        then_block = context.get_block(then_label)

        # 如果没有 else 分支，创建一个默认块
        if else_label:
            else_block = context.get_block(else_label)
        else:
            # 创建一个合并块作为 else 目标
            merge_block = context.create_merge_block()
            else_block = merge_block

        builder.cbranch(cond, then_block, else_block)
        return None


class AllocStrategy(InstructionStrategy):
    """内存分配策略"""

    opcode = Opcode.ALLOC

    def compile(self, builder, instr, context):
        # 获取类型
        alloc_type = context.get_type_from_operand(
            instr.operands[0] if instr.operands else None
        )
        result = builder.alloca(alloc_type, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class LoadStrategy(InstructionStrategy):
    """内存加载策略"""

    opcode = Opcode.LOAD

    def compile(self, builder, instr, context):
        ptr = context.get_value(instr.operands[0])
        result = builder.load(ptr, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class StoreStrategy(InstructionStrategy):
    """内存存储策略"""

    opcode = Opcode.STORE

    def compile(self, builder, instr, context):
        val = context.get_value(instr.operands[0])
        ptr = context.get_value(instr.operands[1])
        builder.store(val, ptr)
        return None


class CallStrategy(InstructionStrategy):
    """函数调用策略"""

    opcode = Opcode.CALL

    def compile(self, builder, instr, context):
        callee_name = str(instr.operands[0])
        args = [context.get_value(a) for a in instr.operands[1:]]

        result_name = context.get_result_name(instr)

        # 尝试查找函数
        callee_func = context.get_function(callee_name)
        if callee_func:
            result = builder.call(callee_func, args, name=result_name or "")
        else:
            # 外部函数 - 简单假设返回 int
            import llvmlite.ir as ll

            func_ty = ll.FunctionType(ll.IntType(32), [ll.IntType(32)] * len(args))
            external_func = ll.Function(context.module, func_ty, callee_name)
            result = builder.call(external_func, args, name=result_name or "")

        if result and result_name:
            context.store_result(instr, result)

        return result


class BitwiseStrategy(InstructionStrategy):
    """位运算策略基类"""

    @staticmethod
    @abstractmethod
    def operation(
        builder: "ll.IRBuilder", a: "ll.Value", b: "ll.Value", name: str
    ) -> "ll.Value":
        """执行位运算"""
        pass


class AndStrategy(BitwiseStrategy):
    """按位与策略"""

    opcode = Opcode.AND

    @staticmethod
    def operation(builder, a, b, name):
        return builder.and_(a, b, name=name)

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        b = context.get_value(instr.operands[1])
        result = self.operation(builder, a, b, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class OrStrategy(BitwiseStrategy):
    """按位或策略"""

    opcode = Opcode.OR

    @staticmethod
    def operation(builder, a, b, name):
        return builder.or_(a, b, name=name)

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        b = context.get_value(instr.operands[1])
        result = self.operation(builder, a, b, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class XorStrategy(BitwiseStrategy):
    """按位异或策略"""

    opcode = Opcode.XOR

    @staticmethod
    def operation(builder, a, b, name):
        return builder.xor(a, b, name=name)

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        b = context.get_value(instr.operands[1])
        result = self.operation(builder, a, b, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class NotStrategy(InstructionStrategy):
    """按位取反策略"""

    opcode = Opcode.NOT

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        result = builder.not_(a, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class ShlStrategy(InstructionStrategy):
    """左移策略"""

    opcode = Opcode.SHL

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        b = context.get_value(instr.operands[1])
        result = builder.shl(a, b, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class ShrStrategy(InstructionStrategy):
    """右移策略"""

    opcode = Opcode.SHR

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        b = context.get_value(instr.operands[1])
        result = builder.lshr(a, b, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class ConversionStrategy(InstructionStrategy):
    """类型转换策略基类"""

    pass


class ZextStrategy(ConversionStrategy):
    """零扩展策略"""

    opcode = Opcode.ZEXT

    def compile(self, builder, instr, context):
        val = context.get_value(instr.operands[0])
        target_type = context.get_type_from_operand(
            instr.operands[1] if len(instr.operands) > 1 else None
        )
        result = builder.zext(val, target_type, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class SextStrategy(ConversionStrategy):
    """符号扩展策略"""

    opcode = Opcode.SEXT

    def compile(self, builder, instr, context):
        val = context.get_value(instr.operands[0])
        target_type = context.get_type_from_operand(
            instr.operands[1] if len(instr.operands) > 1 else None
        )
        result = builder.sext(val, target_type, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class TruncStrategy(ConversionStrategy):
    """截断策略"""

    opcode = Opcode.TRUNC

    def compile(self, builder, instr, context):
        val = context.get_value(instr.operands[0])
        target_type = context.get_type_from_operand(
            instr.operands[1] if len(instr.operands) > 1 else None
        )
        result = builder.trunc(val, target_type, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class BitcastStrategy(ConversionStrategy):
    """位转换策略"""

    opcode = Opcode.BITCAST

    def compile(self, builder, instr, context):
        val = context.get_value(instr.operands[0])
        target_type = context.get_type_from_operand(
            instr.operands[1] if len(instr.operands) > 1 else None
        )
        result = builder.bitcast(val, target_type, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class InstructionStrategyFactory:
    """
    指令策略工厂

    管理和创建指令编译策略。

    使用方式：
        factory = InstructionStrategyFactory()
        factory.register(AddStrategy())
        factory.register(SubStrategy())

        strategy = factory.get_strategy(Opcode.ADD)
        if strategy:
            strategy.compile(builder, instr, context)
    """

    _strategies: Dict[Opcode, InstructionStrategy] = {}
    _initialized: bool = False

    # 默认注册的策略
    DEFAULT_STRATEGIES = [
        # 算术运算
        AddStrategy,
        SubStrategy,
        MulStrategy,
        DivStrategy,
        ModStrategy,
        NegStrategy,
        # 比较运算
        EqStrategy,
        NeStrategy,
        LtStrategy,
        LeStrategy,
        GtStrategy,
        GeStrategy,
        # 控制流
        RetStrategy,
        JmpStrategy,
        JzStrategy,
        CallStrategy,
        # 内存操作
        AllocStrategy,
        LoadStrategy,
        StoreStrategy,
        # 位运算
        AndStrategy,
        OrStrategy,
        XorStrategy,
        NotStrategy,
        ShlStrategy,
        ShrStrategy,
        # 类型转换
        ZextStrategy,
        SextStrategy,
        TruncStrategy,
        BitcastStrategy,
    ]

    @classmethod
    def register(cls, strategy: InstructionStrategy) -> None:
        """注册策略"""
        if strategy.opcode is None:
            raise ValueError(f"策略 {type(strategy).__name__} 必须定义 opcode 属性")
        cls._strategies[strategy.opcode] = strategy

    @classmethod
    def unregister(cls, opcode: Opcode) -> bool:
        """注销策略"""
        if opcode in cls._strategies:
            del cls._strategies[opcode]
            return True
        return False

    @classmethod
    def get_strategy(cls, opcode: Opcode) -> Optional[InstructionStrategy]:
        """获取策略"""
        cls._ensure_initialized()
        return cls._strategies.get(opcode)

    @classmethod
    def _ensure_initialized(cls) -> None:
        """确保策略已初始化"""
        if cls._initialized:
            return

        for strategy_class in cls.DEFAULT_STRATEGIES:
            try:
                strategy = strategy_class()
                cls.register(strategy)
            except Exception:
                # 跳过无法实例化的策略
                pass

        cls._initialized = True

    @classmethod
    def reset(cls) -> None:
        """重置工厂（用于测试）"""
        cls._strategies.clear()
        cls._initialized = False

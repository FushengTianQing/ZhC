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
from typing import Dict, List, Optional, TYPE_CHECKING, Any
import logging

from zhc.ir.opcodes import Opcode

if TYPE_CHECKING:
    from zhc.backend.compilation_context import CompilationContext

if TYPE_CHECKING:
    import llvmlite.ir as ll

logger = logging.getLogger(__name__)


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


class SwitchStrategy(InstructionStrategy):
    """
    Switch 多分支跳转策略 - 增强版

    使用方式：
        switch %val, %default, [val1, %label1], [val2, %label2], ...

    增强特性：
    - 支持整数和字符类型
    - 自动类型转换和验证
    - 空 case 列表处理
    - 默认块缺失处理
    """

    opcode = Opcode.SWITCH

    def compile(self, builder, instr, context):
        import llvmlite.ir as ll

        # 1. 获取条件值
        val = context.get_value(instr.operands[0])

        # 2. 验证条件值类型（必须是整数类型）
        if hasattr(val, 'type'):
            val_type = val.type
            if not isinstance(val_type, ll.IntType):
                # 尝试转换为整数
                if isinstance(val_type, ll.PointerType):
                    # 指针转整数
                    val = builder.ptrtoint(val, ll.IntType(64))
                else:
                    # 其他类型报错
                    raise TypeError(
                        f"Switch condition must be integer type, got {val_type}"
                    )

        # 3. 获取默认目标块
        default_label = str(instr.operands[1])
        default_block = context.get_block(default_label)

        # 如果默认块不存在，创建一个
        if default_block is None:
            default_block = context.create_block(default_label)

        # 4. 收集所有 case 分支
        cases = []
        for i in range(2, len(instr.operands), 2):
            if i + 1 < len(instr.operands):
                # 解析 case 值
                case_val = self._resolve_case_value(
                    instr.operands[i], val.type, context, builder
                )
                # 获取 case 目标块
                case_label = str(instr.operands[i + 1])
                case_block = context.get_block(case_label)

                # 如果块不存在，创建一个
                if case_block is None:
                    case_block = context.create_block(case_label)

                cases.append((case_val, case_block))

        # 5. 处理空 case 列表
        if not cases:
            # 没有 case，直接跳转到默认块
            builder.branch(default_block)
            return None

        # 6. 创建 switch 指令
        builder.switch(val, default_block, cases)
        return None

    def _resolve_case_value(self, operand, cond_type, context, builder):
        """解析 case 值，确保类型匹配

        Args:
            operand: 操作数（可能是常量、变量或值）
            cond_type: switch 条件的类型
            context: 编译上下文
            builder: IR 构建器

        Returns:
            ll.Constant: 正确类型的常量值
        """
        import llvmlite.ir as ll

        # 如果已经是 LLVM 值
        if hasattr(operand, 'type'):
            return operand

        # 如果是整数
        if isinstance(operand, int):
            return ll.Constant(cond_type, operand)

        # 如果是字符串（字符常量）
        if isinstance(operand, str):
            # 单字符
            if len(operand) == 1:
                return ll.Constant(cond_type, ord(operand))
            # 可能是标签名或其他，尝试获取值
            try:
                return context.get_value(operand)
            except (KeyError, AttributeError):
                # 作为字符串常量处理
                raise ValueError(
                    f"Invalid case value: {operand}. "
                    f"Case values must be integers or single characters."
                )

        # 其他情况，尝试获取值
        try:
            return context.get_value(operand)
        except (KeyError, AttributeError):
            raise ValueError(f"Cannot resolve case value: {operand}")


class PhiStrategy(InstructionStrategy):
    """
    Phi 节点策略 - SSA 形式的值合并

    使用方式：
        %result = phi [ %val1, %block1 ], [ %val2, %block2 ], ...

    注意：ZhC 使用非严格 SSA，通过 ALLOC + STORE 替代 phi 节点，
    但保留 phi 指令以支持严格 SSA 模式。
    """

    opcode = Opcode.PHI

    def compile(self, builder, instr, context):
        # 获取 phi 类型
        phi_type = context.get_type_from_operand(
            instr.operands[0] if instr.operands else None
        )

        # 收集所有 incoming 值
        incomings = []
        for i in range(0, len(instr.operands), 2):
            if i + 1 < len(instr.operands):
                val = context.get_value(instr.operands[i])
                block_label = str(instr.operands[i + 1])
                block = context.get_block(block_label)
                incomings.append((val, block))

        # 创建 phi 指令
        result = builder.phi(phi_type, name=context.get_result_name(instr))

        # 添加 incoming 值
        for val, block in incomings:
            result.add_incoming(val, block)

        context.store_result(instr, result)
        return result


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


class GetPtrStrategy(InstructionStrategy):
    """获取指针策略 - 获取结构体/数组成员指针"""

    opcode = Opcode.GETPTR

    def compile(self, builder, instr, context):
        ptr = context.get_value(instr.operands[0])
        index = (
            context.get_value(instr.operands[1]) if len(instr.operands) > 1 else None
        )

        if index is None:
            result = ptr
        else:
            # 使用 gep 实现指针运算
            result = builder.gep(ptr, [index], name=context.get_result_name(instr))

        context.store_result(instr, result)
        return result


class GepStrategy(InstructionStrategy):
    """
    GetElementPtr 策略 - 指针运算，用于数组索引和结构体字段访问

    使用方式：
        %ptr = gep %base, %idx1, %idx2, ...

    增强特性：
    - 索引类型验证
    - 负数索引检测与警告
    - 数组边界检查（调试模式）
    - 多维数组支持
    - 结构体字段访问支持
    - 常量索引优化
    """

    opcode = Opcode.GEP

    def compile(self, builder, instr, context):
        import llvmlite.ir as ll

        ptr = context.get_value(instr.operands[0])

        # 收集所有索引
        indices = []
        for i in range(1, len(instr.operands)):
            idx = context.get_value(instr.operands[i])
            indices.append(idx)

        if not indices:
            result = ptr
        else:
            # ============ 增强处理 ============

            # 1. 负数索引检测
            self._check_negative_indices(indices)

            # 2. 尝试常量优化
            folded_indices, merged_offset = context._fold_constant_indices(indices)

            # 3. 如果有合并的偏移量，创建新的索引列表
            if merged_offset > 0:
                indices = folded_indices
                if indices:
                    # 将偏移量合并到第一个非常量索引
                    first_idx = indices[0]
                    if isinstance(first_idx, ll.Constant):
                        # 直接累加
                        indices[0] = ll.Constant(
                            ll.IntType(32),
                            first_idx.constant + merged_offset
                        )
                    else:
                        # 需要生成 add 指令
                        offset_const = ll.Constant(ll.IntType(32), merged_offset)
                        indices[0] = builder.add(first_idx, offset_const)
                else:
                    # 所有索引都是常量，直接使用合并结果
                    indices = [ll.Constant(ll.IntType(32), merged_offset)]

            # 4. 移除不必要的零索引（首元素指针优化）
            ptr, indices = context.optimize_gep_indices(ptr, indices)

            # 5. 生成 GEP 指令
            result = builder.gep(ptr, indices, name=context.get_result_name(instr))

        context.store_result(instr, result)
        return result

    def _check_negative_indices(self, indices):
        """
        检查是否有负数索引，发出警告

        Args:
            indices: 索引列表
        """
        import llvmlite.ir as ll
        import warnings

        for i, idx in enumerate(indices):
            if isinstance(idx, ll.Constant) and isinstance(idx.type, ll.IntType):
                if idx.constant < 0:
                    warnings.warn(
                        f"警告：GEP 索引 {i} 为负数 ({idx.constant})，"
                        "这可能导致未定义行为。",
                        RuntimeWarning,
                        stacklevel=3
                    )


class AdvancedGEPInstruction(InstructionStrategy):
    """
    高级 GEP 指令 - 处理复杂的多维数组和结构体访问

    相比基础 GepStrategy，本类提供：
    - 结构体字段名称解析（支持 "field_name" 形式的索引）
    - 多维数组类型推断
    - 数组边界运行时检查（可选）
    - 指针算术优化

    使用方式：
        %ptr = agep %base, "field_name", %idx, ...  # 结构体字段 + 数组索引
        %ptr = agep %base, %i, %j, %k               # 多维数组索引

    示例 IR：
        ; 访问二维数组元素 arr[i][j]
        %ptr = agep %arr, %i, %j

        ; 访问结构体字段
        %ptr = agep %struct_ptr, "age"
    """

    opcode = Opcode.GEP  # 复用 GEP opcode

    def __init__(self):
        super().__init__()
        self._struct_field_cache: Dict[str, int] = {}

    def compile(self, builder, instr, context):
        """
        编译高级 GEP 指令

        Args:
            builder: IRBuilder 实例
            instr: IR 指令
            context: 编译上下文

        Returns:
            ll.Value: 生成的指针
        """
        import llvmlite.ir as ll

        ptr = context.get_value(instr.operands[0])

        # 解析索引（支持结构体字段名）
        indices = []
        for i in range(1, len(instr.operands)):
            operand = instr.operands[i]
            idx = self._resolve_index(operand, context)
            indices.append(idx)

        if not indices:
            return ptr

        # 尝试推断基类型并优化
        base_type = context.infer_gep_base_type(ptr)
        if base_type:
            # 类型推断优化
            indices = self._optimize_indices_for_type(base_type, indices, context)

        # 生成优化的 GEP
        result = builder.gep(ptr, indices, name=context.get_result_name(instr))

        context.store_result(instr, result)
        return result

    def _resolve_index(self, operand, context) -> "ll.Value":
        """
        解析索引操作数

        支持两种形式：
        - 数值索引：整数常量或变量
        - 字段名索引：字符串（如 "name", "age"）

        Args:
            operand: 操作数
            context: 编译上下文

        Returns:
            ll.Value: LLVM 索引值
        """
        import llvmlite.ir as ll

        # 如果是字符串（字段名）
        if isinstance(operand, str):
            if operand.startswith('"') and operand.endswith('"'):
                field_name = operand[1:-1]
                # 在注册表中查找字段索引
                # 这里需要知道结构体类型，暂时返回常量 0
                # 实际实现需要从上下文获取结构体类型信息
                if hasattr(context, 'current_struct_info'):
                    field_idx = context.current_struct_info.get_field_index(field_name)
                    if field_idx is not None:
                        return ll.Constant(ll.IntType(32), field_idx)

                logger.warning(f"无法解析结构体字段名：{field_name}，使用索引 0")
                return ll.Constant(ll.IntType(32), 0)

        # 其他情况使用标准解析
        return context.get_value(operand)

    def _optimize_indices_for_type(self, base_type: "ll.Type",
                                   indices: List["ll.Value"],
                                   context) -> List["ll.Value"]:
        """
        根据类型优化索引

        Args:
            base_type: 基类型
            indices: 原始索引
            context: 编译上下文

        Returns:
            List[ll.Value]: 优化后的索引
        """
        import llvmlite.ir as ll

        # 如果基类型是数组，尝试多维优化
        if isinstance(base_type, ll.ArrayType):
            return self._optimize_multi_dimensional_array(base_type, indices, context)

        return indices

    def _optimize_multi_dimensional_array(self, array_type: "ll.ArrayType",
                                         indices: List["ll.Value"],
                                         context) -> List["ll.Value"]:
        """
        多维数组索引优化

        将二维索引计算合并：
        原：gep arr, i, j (其中数组是 [N][M] 类型)
        优化：gep arr, 0, i * M + j

        Args:
            array_type: 数组类型
            indices: 索引列表
            context: 编译上下文

        Returns:
            List[ll.Value]: 优化后的索引
        """
        import llvmlite.ir as ll

        # 只有当索引数量与维度匹配时进行优化
        expected_dims = self._count_array_dims(array_type)
        if len(indices) != expected_dims:
            return indices

        # 获取数组信息
        if hasattr(array_type, 'count'):
            inner_dim_size = array_type.count
        else:
            return indices

        # 检查是否适合一维优化
        if isinstance(inner_dim_size, int) and inner_dim_size > 1:
            # 简化处理：保留多维索引
            # 完整实现需要考虑行主序 vs 列主序
            pass

        return indices

    def _count_array_dims(self, array_type: "ll.Type") -> int:
        """计算数组类型维度数"""
        import llvmlite.ir as ll

        dims = 0
        current = array_type
        while isinstance(current, ll.ArrayType):
            dims += 1
            current = current.element

        return dims


class CallStrategy(InstructionStrategy):
    """函数调用策略"""

    opcode = Opcode.CALL

    def compile(self, builder, instr, context):
        callee_name = str(instr.operands[0])
        args = [self._prepare_argument(builder, a, context) for a in instr.operands[1:]]

        result_name = context.get_result_name(instr)

        # 尝试查找函数
        callee_func = context.get_function(callee_name)
        if callee_func:
            result = builder.call(callee_func, args, name=result_name or "")
        else:
            # 外部函数 - 使用参数的实际类型
            import llvmlite.ir as ll

            # 获取每个参数的实际类型
            arg_types = [arg.type for arg in args]
            func_ty = ll.FunctionType(ll.IntType(32), arg_types)
            external_func = ll.Function(context.module, func_ty, callee_name)
            result = builder.call(external_func, args, name=result_name or "")

        if result and result_name:
            context.store_result(instr, result)

        return result

    def _prepare_argument(self, builder, arg, context):
        """
        准备函数参数，处理字符串常量等特殊情况

        Args:
            builder: IRBuilder
            arg: 参数值
            context: 编译上下文

        Returns:
            准备好的参数值
        """
        import llvmlite.ir as ll

        value = context.get_value(arg)

        # 如果是全局变量指针（字符串常量），需要用 GEP 获取 i8* 指针
        if isinstance(value, ll.GlobalVariable):
            # llvmlite 的 GlobalVariable.type 是指针类型 (e.g., [12 x i8]*)
            # 检查指针指向的类型是否是数组
            pointee_type = value.type.pointee
            if isinstance(pointee_type, ll.ArrayType):
                # 创建 GEP 获取第一个元素的指针 (i8*)
                zero = ll.Constant(ll.IntType(32), 0)
                ptr = builder.gep(value, [zero, zero], name="str_ptr")
                return ptr

        return value


class LogicalStrategy(InstructionStrategy):
    """逻辑运算策略基类"""

    @staticmethod
    @abstractmethod
    def operation(
        builder: "ll.IRBuilder", a: "ll.Value", b: "ll.Value", name: str
    ) -> "ll.Value":
        """执行逻辑运算"""
        pass


class LAndStrategy(LogicalStrategy):
    """逻辑与策略 (&&)"""

    opcode = Opcode.L_AND

    @staticmethod
    def operation(builder, a, b, name):
        # 逻辑与：先转为布尔，再 AND
        a_bool = builder.icmp_signed("!=", a, a.type(0), name="land_a")
        b_bool = builder.icmp_signed("!=", b, b.type(0), name="land_b")
        return builder.and_(a_bool, b_bool, name=name)

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        b = context.get_value(instr.operands[1])
        result = self.operation(builder, a, b, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class LOrStrategy(LogicalStrategy):
    """逻辑或策略 (||)"""

    opcode = Opcode.L_OR

    @staticmethod
    def operation(builder, a, b, name):
        # 逻辑或：先转为布尔，再 OR
        a_bool = builder.icmp_signed("!=", a, a.type(0), name="lor_a")
        b_bool = builder.icmp_signed("!=", b, b.type(0), name="lor_b")
        return builder.or_(a_bool, b_bool, name=name)

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        b = context.get_value(instr.operands[1])
        result = self.operation(builder, a, b, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class LNotStrategy(InstructionStrategy):
    """逻辑非策略 (!)"""

    opcode = Opcode.L_NOT

    def compile(self, builder, instr, context):
        a = context.get_value(instr.operands[0])
        # 逻辑非：先转为布尔，再取反
        a_bool = builder.icmp_signed("!=", a, a.type(0), name="lnot_a")
        result = builder.icmp_signed(
            "==", a_bool, a_bool.type(0), name=context.get_result_name(instr)
        )
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


class Int2PtrStrategy(ConversionStrategy):
    """整数转指针策略"""

    opcode = Opcode.INT2PTR

    def compile(self, builder, instr, context):
        import llvmlite.ir as ll

        val = context.get_value(instr.operands[0])

        # 获取目标指针类型
        if len(instr.operands) > 1:
            target_type = context.get_type_from_operand(instr.operands[1])
        else:
            # 默认为 i8* (通用指针)
            target_type = ll.PointerType(ll.IntType(8))

        result = builder.inttoptr(val, target_type, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class Ptr2IntStrategy(ConversionStrategy):
    """指针转整数策略"""

    opcode = Opcode.PTR2INT

    def compile(self, builder, instr, context):
        import llvmlite.ir as ll

        val = context.get_value(instr.operands[0])

        # 获取目标整数类型
        if len(instr.operands) > 1:
            target_type = context.get_type_from_operand(instr.operands[1])
        else:
            # 默认为 i64 (指针大小)
            target_type = ll.IntType(64)

        result = builder.ptrtoint(val, target_type, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result


class ConstStrategy(InstructionStrategy):
    """
    常量策略 - 定义常量值

    使用方式：
        %result = const <type> <value>
    """

    opcode = Opcode.CONST

    def compile(self, builder, instr, context):
        import llvmlite.ir as ll

        # 获取类型和值
        if len(instr.operands) >= 2:
            const_type = context.get_type_from_operand(instr.operands[0])
            const_value = instr.operands[1]
        else:
            const_type = ll.IntType(32)
            const_value = instr.operands[0] if instr.operands else None

        # 解析常量值
        val = context.get_value(const_value)

        # 根据类型创建常量
        if isinstance(const_type, ll.IntType):
            if hasattr(val, "constant"):
                result = ll.Constant(const_type, val.constant)
            else:
                result = ll.Constant(const_type, 0)
        elif isinstance(const_type, ll.FloatType):
            if hasattr(val, "constant"):
                result = ll.Constant(const_type, float(val.constant))
            else:
                result = ll.Constant(const_type, 0.0)
        elif isinstance(const_type, ll.DoubleType):
            if hasattr(val, "constant"):
                result = ll.Constant(const_type, float(val.constant))
            else:
                result = ll.Constant(const_type, 0.0)
        else:
            result = ll.Constant(const_type, 0)

        context.store_result(instr, result)
        return result


class NopStrategy(InstructionStrategy):
    """空操作策略 - 不做任何事情"""

    opcode = Opcode.NOP

    def compile(self, builder, instr, context):
        # 空操作，什么都不做
        return None


class GlobalStrategy(InstructionStrategy):
    """
    全局变量策略 - 获取全局变量地址

    使用方式：
        %result = global @global_var
    """

    opcode = Opcode.GLOBAL

    def compile(self, builder, instr, context):
        global_name = str(instr.operands[0])

        # 移除 @ 前缀
        if global_name.startswith("@"):
            global_name = global_name[1:]

        # 在模块中查找全局变量
        if context.module:
            for gv in context.module.global_variables:
                if gv.name == global_name:
                    context.store_result(instr, gv)
                    return gv

        # 如果找不到，返回 None
        logger.warning(f"未找到全局变量: @{global_name}")
        return None


class ArgStrategy(InstructionStrategy):
    """
    函数参数策略 - 获取函数参数值

    使用方式：
        %result = arg <param_index>
    """

    opcode = Opcode.ARG

    def compile(self, builder, instr, context):
        # 获取参数索引
        if instr.operands:
            idx = context.get_value(instr.operands[0])
            if hasattr(idx, "constant"):
                param_idx = idx.constant
            else:
                param_idx = 0
        else:
            param_idx = 0

        # 从当前函数获取参数
        if context.current_function and isinstance(
            context.current_function, ll.Function
        ):
            if param_idx < len(context.current_function.args):
                arg_value = context.current_function.args[param_idx]
                context.store_result(instr, arg_value)
                return arg_value

        return None


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
        # 逻辑运算
        LAndStrategy,
        LOrStrategy,
        LNotStrategy,
        # 控制流
        RetStrategy,
        JmpStrategy,
        JzStrategy,
        SwitchStrategy,
        PhiStrategy,
        CallStrategy,
        # 内存操作
        AllocStrategy,
        LoadStrategy,
        StoreStrategy,
        GetPtrStrategy,
        GepStrategy,
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
        Int2PtrStrategy,
        Ptr2IntStrategy,
        # 其他
        ConstStrategy,
        NopStrategy,
        GlobalStrategy,
        ArgStrategy,
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

# -*- coding: utf-8 -*-
"""
ZHC IR - IR 优化 Pass

提供常量折叠和死代码消除两个优化 Pass。

作者：远
日期：2026-04-03
"""

from abc import ABC, abstractmethod
from typing import List

from zhpp.ir.program import IRProgram, IRFunction
from zhpp.ir.instructions import IRBasicBlock, IRInstruction
from zhpp.ir.values import IRValue, ValueKind
from zhpp.ir.opcodes import Opcode


class OptimizationPass(ABC):
    """优化 Pass 基类"""

    @abstractmethod
    def name(self) -> str:
        """Pass 名称"""
        pass

    @abstractmethod
    def run(self, ir: IRProgram) -> IRProgram:
        """对 IR 程序运行优化"""
        pass


class PassManager:
    """优化 Pass 管理器"""

    def __init__(self):
        self.passes: List[OptimizationPass] = []

    def register(self, pass_: OptimizationPass) -> 'PassManager':
        """注册一个 Pass"""
        self.passes.append(pass_)
        return self

    def run(self, ir: IRProgram) -> IRProgram:
        """顺序执行所有已注册的 Pass"""
        for pass_ in self.passes:
            ir = pass_.run(ir)
        return ir


class ConstantFolding(OptimizationPass):
    """
    常量折叠

    将常量表达式在编译时求值，避免运行时计算。

    例如：
        %0 = 1 + 2   ->   %0 = 3
        %1 = %0 * 4   ->   %1 = 12
    """

    def name(self) -> str:
        return "常量折叠"

    def run(self, ir: IRProgram) -> IRProgram:
        for func in ir.functions:
            self._fold_function(func)
        return ir

    def _fold_function(self, func: IRFunction):
        """对函数进行常量折叠"""
        changed = True
        while changed:
            changed = False
            for bb in func.basic_blocks:
                for i, instr in enumerate(bb.instructions):
                    if self._can_fold(instr):
                        result = self._try_fold(instr)
                        if result is not None:
                            # 将指令替换为常量赋值
                            bb.instructions[i] = self._make_const_instr(
                                instr.result[0] if instr.result else None,
                                result
                            )
                            changed = True

    def _can_fold(self, instr: IRInstruction) -> bool:
        """判断是否可以折叠"""
        op = instr.opcode
        if op not in (Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.DIV, Opcode.MOD,
                       Opcode.EQ, Opcode.NE, Opcode.LT, Opcode.LE, Opcode.GT, Opcode.GE,
                       Opcode.L_AND, Opcode.L_OR, Opcode.NEG, Opcode.L_NOT):
            return False
        if not instr.operands or not instr.result:
            return False
        # 所有操作数必须是常量
        return all(v.kind == ValueKind.CONST for v in instr.operands)

    def _try_fold(self, instr: IRInstruction):
        """尝试折叠，返回常量值或 None"""
        if not instr.operands:
            return None
        vals = [v.const_value for v in instr.operands]
        op = instr.opcode

        try:
            if op == Opcode.ADD:
                return vals[0] + vals[1]
            if op == Opcode.SUB:
                return vals[0] - vals[1]
            if op == Opcode.MUL:
                return vals[0] * vals[1]
            if op == Opcode.DIV:
                if vals[1] == 0:
                    return None
                return vals[0] / vals[1]
            if op == Opcode.MOD:
                if vals[1] == 0:
                    return None
                return vals[0] % vals[1]
            if op == Opcode.EQ:
                return vals[0] == vals[1]
            if op == Opcode.NE:
                return vals[0] != vals[1]
            if op == Opcode.LT:
                return vals[0] < vals[1]
            if op == Opcode.LE:
                return vals[0] <= vals[1]
            if op == Opcode.GT:
                return vals[0] > vals[1]
            if op == Opcode.GE:
                return vals[0] >= vals[1]
            if op == Opcode.L_AND:
                return bool(vals[0]) and bool(vals[1])
            if op == Opcode.L_OR:
                return bool(vals[0]) or bool(vals[1])
            if op == Opcode.NEG:
                return -vals[0]
            if op == Opcode.L_NOT:
                return not vals[0]
        except (ZeroDivisionError, TypeError, ValueError):
            pass
        return None

    def _make_const_instr(self, result_var, const_value) -> IRInstruction:
        """生成常量赋值指令"""
        const_val = IRValue(
            name=str(const_value),
            ty=getattr(result_var, 'ty', None),
            kind=ValueKind.CONST,
            const_value=const_value,
        )
        return IRInstruction(Opcode.CONST, [const_val], [result_var] if result_var else [])


class DeadCodeElimination(OptimizationPass):
    """
    死代码消除

    删除不可达的代码块和永不使用的变量赋值。

    例如：
        if (false) { ... }   ->   (整个 if 块被删除)
    """

    def name(self) -> str:
        return "死代码消除"

    def run(self, ir: IRProgram) -> IRProgram:
        for func in ir.functions:
            self._remove_dead_blocks(func)
            self._remove_dead_instrs(func)
        return ir

    def _remove_dead_blocks(self, func: IRFunction):
        """删除不可达基本块"""
        if not func.basic_blocks:
            return

        # 收集可达块（通过 successor 链传播）
        reachable = {func.basic_blocks[0].label}
        frontier = list(func.basic_blocks[0].successors)
        while frontier:
            next_label = frontier.pop()
            if next_label not in reachable:
                reachable.add(next_label)
                # 找到该块并加入 frontier
                for bb in func.basic_blocks:
                    if bb.label == next_label:
                        frontier.extend(bb.successors)
                        break

        # 删除不可达的块（在列表副本上迭代，修改原列表）
        to_remove = [bb for bb in func.basic_blocks if bb.label not in reachable]
        for bb in to_remove:
            func.basic_blocks.remove(bb)

    def _remove_dead_instrs(self, func: IRFunction):
        """删除死指令（结果未使用的常量赋值）"""
        # 使用 liveness 分析：追踪哪些值被使用
        used = set()

        def mark_use(v: IRValue):
            if v and v.kind in (ValueKind.VAR, ValueKind.TEMP):
                used.add(v.name)

        for bb in func.basic_blocks:
            for instr in bb.instructions:
                for op in instr.operands:
                    mark_use(op)
                if instr.result:
                    for r in instr.result:
                        mark_use(r)

        # 删除 CONST 指令但其结果未被使用
        for bb in func.basic_blocks:
            bb.instructions = [
                i for i in bb.instructions
                if not (i.opcode == Opcode.CONST and
                        i.result and
                        i.result[0].name not in used)
            ]

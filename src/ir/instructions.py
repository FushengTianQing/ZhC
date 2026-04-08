# -*- coding: utf-8 -*-
"""
ZHC IR - 指令和基本块定义

定义 ZHC IR 的指令和基本块结构。

作者：远
日期：2026-04-03
"""

from typing import List, Optional
from .opcodes import Opcode
from .values import IRValue


class IRInstruction:
    """
    ZHC IR 指令

    Attributes:
        opcode: 操作码
        operands: 操作数列表（IRValue）
        result: 结果值列表（IRValue）
        label: 指令前的标签（可选，用于基本块入口）
    """

    def __init__(
        self,
        opcode: Opcode,
        operands: List[IRValue] = None,
        result: List[IRValue] = None,
        label: Optional[str] = None,
    ):
        self.opcode = opcode
        self.operands = operands or []
        self.result = result or []
        self.label = label

    def __repr__(self) -> str:
        if self.result:
            res_str = ", ".join(str(r) for r in self.result)
            op_str = ", ".join(str(o) for o in self.operands)
            return f"{res_str} = {self.opcode.name} {op_str}"
        else:
            op_str = ", ".join(str(o) for o in self.operands)
            return f"{self.opcode.name} {op_str}"

    def is_terminator(self) -> bool:
        """判断是否是终止指令"""
        return self.opcode.is_terminator


class IRBasicBlock:
    """
    ZHC IR 基本块

    基本块是一组线性执行的指令，以终止指令结束。
    """

    def __init__(self, label: str):
        self.label = label
        self.instructions: List[IRInstruction] = []
        self.predecessors: List[str] = []  # 前驱基本块标签
        self.successors: List[str] = []  # 后继基本块标签

    def add_instruction(self, instr: IRInstruction):
        """添加指令"""
        self.instructions.append(instr)

    def is_terminated(self) -> bool:
        """判断是否以终止指令结束"""
        if not self.instructions:
            return False
        return self.instructions[-1].is_terminator()

    def get_terminator(self) -> Optional[IRInstruction]:
        """获取终止指令"""
        if self.is_terminated():
            return self.instructions[-1]
        return None

    def add_predecessor(self, pred_label: str):
        """添加前驱基本块"""
        if pred_label not in self.predecessors:
            self.predecessors.append(pred_label)

    def add_successor(self, succ_label: str):
        """添加后继基本块"""
        if succ_label not in self.successors:
            self.successors.append(succ_label)

    def __repr__(self) -> str:
        return f"BB({self.label}, {len(self.instructions)} instr)"

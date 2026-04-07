# -*- coding: utf-8 -*-
"""
ZHC IR - IR → C 后端

将 ZHC IR 转换为可编译的 C 代码。

使用基本块展平算法，将 IR 基本块展平为线性 C 代码。

作者：远
日期：2026-04-03
"""

from typing import List, Optional

from zhpp.ir.program import IRProgram, IRFunction, IRGlobalVar
from zhpp.ir.instructions import IRBasicBlock, IRInstruction
from zhpp.ir.values import IRValue, ValueKind
from zhpp.ir.opcodes import Opcode
from zhpp.ir.mappings import (
    TYPE_MAP,
    FUNCTION_NAME_MAP,
    STDLIB_FUNC_MAP,
    resolve_type,
    resolve_function_name,
)


class CBackend:
    """
    IR → C 代码生成器

    将 IRProgram 转换为 C 代码字符串。
    """

    def __init__(self):
        self.output_lines: List[str] = []
        self.temp_names: dict = {}  # IR temp name -> C temp name

    def generate(self, ir: IRProgram) -> str:
        """将 IR 程序转换为 C 代码"""
        self.output_lines = []
        self.temp_names = {}

        # 包含头文件
        self._emit("#include <stdio.h>")
        self._emit("#include <stdlib.h>")
        self._emit("")

        # 全局变量
        for gv in ir.global_vars:
            self._emit(f"{resolve_type(gv.ty or 'int')} {gv.name};")

        if ir.global_vars:
            self._emit("")

        # 函数
        for func in ir.functions:
            self._generate_function(func)

        return "\n".join(self.output_lines)

    def _generate_function(self, func: IRFunction):
        """生成单个函数"""
        # 函数签名
        ret_type = resolve_type(func.return_type or "空型")
        func_name = resolve_function_name(func.name)
        params = ", ".join(
            f"{resolve_type(p.ty or 'int')} {p.name}" for p in func.params
        )
        self._emit(f"{ret_type} {func_name}({params}) {{")

        # 基本块展平为线性代码
        for bb in func.basic_blocks:
            self._generate_basic_block(bb)

        self._emit("}")
        self._emit("")

    def _generate_basic_block(self, bb: IRBasicBlock):
        """生成基本块内的指令"""
        for instr in bb.instructions:
            self._generate_instruction(instr)

    def _generate_instruction(self, instr: IRInstruction):
        """生成单条指令"""
        op = instr.opcode

        if op == Opcode.RET:
            if instr.operands:
                self._emit(f"return {instr.operands[0]};")
            else:
                self._emit("return;")
            return

        if op == Opcode.ALLOC:
            # ALLOC var, result -> 声明变量
            if instr.operands and instr.result:
                var = instr.operands[0]
                res = instr.result[0]
                ty = getattr(var, 'ty', None) or 'int'
                self.temp_names[res.name] = var.name
                self._emit(f"{resolve_type(ty)} {var.name};")
            return

        if op == Opcode.STORE:
            # STORE value, ptr -> ptr = value
            if len(instr.operands) >= 2:
                val, ptr = instr.operands[0], instr.operands[1]
                self._emit(f"{ptr} = {val};")
            return

        if op == Opcode.LOAD:
            # LOAD ptr, result -> result = *ptr
            if len(instr.operands) >= 1 and instr.result:
                ptr = instr.operands[0]
                res = instr.result[0]
                self._emit(f"{res} = {ptr};")
            return

        if op in (Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.DIV, Opcode.MOD):
            op_map = {"add": "+", "sub": "-", "mul": "*", "div": "/", "mod": "%"}
            self._emit_binary_op(instr, op_map.get(op.name, op.name))
            return

        if op in (Opcode.EQ, Opcode.NE, Opcode.LT, Opcode.LE, Opcode.GT, Opcode.GE):
            op_map = {"eq": "==", "ne": "!=", "lt": "<", "le": "<=", "gt": ">", "ge": ">="}
            self._emit_binary_op(instr, op_map.get(op.name, op.name))
            return

        if op == Opcode.L_AND:
            self._emit_binary_op(instr, "&&")
            return
        if op == Opcode.L_OR:
            self._emit_binary_op(instr, "||")
            return
        if op == Opcode.L_NOT:
            if instr.operands and instr.result:
                res = instr.result[0]
                opnd = instr.operands[0]
                self._emit(f"{res} = !{opnd};")
            return

        if op == Opcode.CONST:
            if instr.operands and instr.result:
                const_val = instr.operands[0]
                res = instr.result[0]
                self._emit(f"{res} = {const_val};")
            return

        if op == Opcode.NEG:
            if instr.operands and instr.result:
                res = instr.result[0]
                opnd = instr.operands[0]
                self._emit(f"{res} = -{opnd};")
            return

        if op == Opcode.JMP:
            # 跳转目标在基本块后继中处理
            return

        if op == Opcode.JZ:
            # 条件跳转，需要 if 语句包装
            return

        if op == Opcode.CALL:
            self._emit_call(instr)
            return

        if op == Opcode.GETPTR:
            if len(instr.operands) >= 2 and instr.result:
                base = instr.operands[0]
                index = instr.operands[1]
                res = instr.result[0]
                self._emit(f"{res} = {base}[{index}];")
            elif len(instr.operands) >= 1 and instr.result:
                base = instr.operands[0]
                res = instr.result[0]
                self._emit(f"{res} = &{base};")
            return

        if op == Opcode.GEP:
            if len(instr.operands) >= 2 and instr.result:
                base = instr.operands[0]
                index = instr.operands[1]
                res = instr.result[0]
                self._emit(f"{res} = {base} + {index};")
            return

    def _emit_binary_op(self, instr: IRInstruction, op_str: str):
        """生成二元运算指令"""
        if len(instr.operands) >= 2 and instr.result:
            left, right = instr.operands[0], instr.operands[1]
            res = instr.result[0]
            self._emit(f"{res} = {left} {op_str} {right};")

    def _emit_call(self, instr: IRInstruction):
        """生成函数调用指令"""
        if not instr.operands:
            return
        func_val = instr.operands[0]
        args = instr.operands[1:]
        args_str = ", ".join(str(a) for a in args)
        if instr.result:
            res = instr.result[0]
            self._emit(f"{res} = {func_val}({args_str});")
        else:
            self._emit(f"{func_val}({args_str});")

    def _emit(self, line: str = ""):
        """输出一行"""
        self.output_lines.append(line)

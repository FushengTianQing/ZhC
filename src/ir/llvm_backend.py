# -*- coding: utf-8 -*-
"""ZHC IR - LLVM IR 后端

将 ZHC IR 转换为 LLVM IR (.ll) 或字节码 (.bc)。

作者：远
日期：2026-04-03
"""

from typing import List
from zhc.ir.program import IRProgram, IRFunction
from zhc.ir.instructions import IRBasicBlock, IRInstruction
from zhc.ir.values import IRValue
from zhc.ir.opcodes import Opcode


# 中文类型 → LLVM 类型字符串
ZHCT_TO_LLVM = {
    "整数型": "i32",
    "浮点型": "float",
    "双精度浮点型": "double",
    "字符型": "i8",
    "字节型": "i8",
    "布尔型": "i1",
    "空型": "void",
    "字符串型": "i8*",
    # 原始 LLVM 类型透传
    "i32": "i32",
    "i64": "i64",
    "i16": "i16",
    "i8": "i8",
}


def _llvm_type(zhc_type: str) -> str:
    """中文类型 → LLVM IR 类型字符串"""
    return ZHCT_TO_LLVM.get(zhc_type, "i32")


class LLVMPrinter:
    """LLVM IR 文本生成器"""

    _ARITH_LLVM = {
        "add": "add", "sub": "sub", "mul": "mul",
        "div": "sdiv", "mod": "srem",
    }

    _CMP_LLVM = {
        "eq": "eq", "ne": "ne",
        "lt": "slt", "le": "sle",
        "gt": "sgt", "ge": "sge",
    }

    def __init__(self):
        self.lines: List[str] = []

    def print(self, ir: IRProgram) -> str:
        """生成完整的 LLVM IR 文本"""
        self.lines = []
        self.lines.append("; ZHC IR → LLVM IR")
        self.lines.append("source_filename = \"zhc_module\"")
        self.lines.append("target datalayout = \"\"")
        self.lines.append("target triple = \"\"")

        for gv in ir.global_vars:
            ty = _llvm_type(gv.ty or "i32")
            self.lines.append(f"@{gv.name} = global {ty} zeroinitializer")

        for func in ir.functions:
            self._gen_function(func)

        return "\n".join(self.lines)

    def _gen_function(self, func: IRFunction):
        ret_ty = _llvm_type(func.return_type or "i32")
        params = ", ".join(
            f"{_llvm_type(p.ty or 'i32')} %{p.name}"
            for p in func.params
        )
        self.lines.append(f"define {ret_ty} @{func.name}({params}) {{")

        for bb in func.basic_blocks:
            self._gen_block(bb)

        self.lines.append("}")

    def _gen_block(self, bb: IRBasicBlock):
        self.lines.append(f"{bb.label}:")
        for instr in bb.instructions:
            self._gen_instr(instr)

    def _gen_instr(self, instr: IRInstruction):
        op = instr.opcode

        if op == Opcode.RET:
            if instr.operands:
                self.lines.append(f"  ret {instr.operands[0]}")
            else:
                self.lines.append("  ret void")

        elif op.name in self._ARITH_LLVM:
            self._gen_arith(instr)

        elif op.name in self._CMP_LLVM:
            self._gen_cmp(instr)

        elif op == Opcode.CALL:
            self._gen_call(instr)

        elif op == Opcode.ALLOC:
            # 处理 operands（可能是字符串或 IRValue 对象）
            if instr.operands:
                op_obj = instr.operands[0]
                op_ty = op_obj.ty if hasattr(op_obj, 'ty') else str(op_obj)
            else:
                op_ty = "i32"
            var_ty = _llvm_type(op_ty)
            
            # 处理 result
            if instr.result:
                res_obj = instr.result[0]
                res = res_obj.name if hasattr(res_obj, 'name') else str(res_obj)
            else:
                res = None
            
            if res:
                self.lines.append(f"  %{res} = alloca {var_ty}, align 4")
            else:
                self.lines.append(f"  alloca {var_ty}, align 4")

        elif op == Opcode.STORE:
            val, ptr = instr.operands[0], instr.operands[1]
            self.lines.append(f"  store {val}, {ptr}*")

        elif op == Opcode.LOAD:
            src = instr.operands[0] if instr.operands else ""
            
            # 处理 result
            if instr.result:
                res_obj = instr.result[0]
                res = res_obj.name if hasattr(res_obj, 'name') else str(res_obj)
            else:
                res = "%tmp"
            
            self.lines.append(f"  %{res} = load i32, i32* {src}")

        elif op == Opcode.JMP:
            self.lines.append(f"  br label %{instr.operands[0]}")

        elif op == Opcode.JZ:
            cond, dest = instr.operands[0], instr.operands[1]
            self.lines.append(f"  br i1 {cond}, label %{dest}")

        elif op == Opcode.GLOBAL:
            pass

        else:
            self.lines.append(f"  ; {op.name} [未实现]")

    def _gen_arith(self, instr: IRInstruction):
        a = instr.operands[0] if len(instr.operands) > 0 else ""
        b = instr.operands[1] if len(instr.operands) > 1 else instr.operands[0] if instr.operands else ""
        
        # 处理 result（可能是字符串或 IRValue 对象）
        if instr.result:
            res_obj = instr.result[0]
            res = res_obj.name if hasattr(res_obj, 'name') else str(res_obj)
        else:
            res = ""
        
        llvm_op = self._ARITH_LLVM[instr.opcode.name]
        if res:
            self.lines.append(f"  %{res} = {llvm_op} i32 {a}, {b}")
        else:
            self.lines.append(f"  {llvm_op} i32 {a}, {b}")

    def _gen_cmp(self, instr: IRInstruction):
        a = instr.operands[0] if len(instr.operands) > 0 else ""
        b = instr.operands[1] if len(instr.operands) > 1 else instr.operands[0] if instr.operands else ""
        
        # 处理 result（可能是字符串或 IRValue 对象）
        if instr.result:
            res_obj = instr.result[0]
            res = res_obj.name if hasattr(res_obj, 'name') else str(res_obj)
        else:
            res = ""
        
        llvm_op = self._CMP_LLVM[instr.opcode.name]
        if res:
            self.lines.append(f"  %{res} = icmp {llvm_op} i32 {a}, {b}")
        else:
            self.lines.append(f"  icmp {llvm_op} i32 {a}, {b}")

    def _gen_call(self, instr):
        callee = instr.operands[0] if instr.operands else ""
        args = ", ".join(str(a) for a in instr.operands[1:])
        
        # 处理 result（可能是字符串或 IRValue 对象）
        if instr.result:
            res_obj = instr.result[0]
            res = res_obj.name if hasattr(res_obj, 'name') else str(res_obj)
        else:
            res = ""
        
        if res:
            self.lines.append(f"  %{res} = call i32 @{callee}({args})")
        else:
            self.lines.append(f"  call @{callee}({args})")

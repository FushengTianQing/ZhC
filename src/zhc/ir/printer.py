# -*- coding: utf-8 -*-
"""
ZHC IR - 文本打印器

将 IRProgram 可读化输出为文本格式。

作者：远
日期：2026-04-03
"""

from .program import IRProgram, IRFunction
from .instructions import IRBasicBlock


class IRPrinter:
    """
    ZHC IR 文本打印器

    将 IRProgram 输出为可读的文本格式。
    """

    def print(self, ir: IRProgram) -> str:
        """将 IR 程序打印为字符串"""
        lines = []

        # 打印结构体定义
        if ir.structs:
            lines.append("; === 结构体定义 ===")
            for s in ir.structs:
                lines.append(f"struct {s.name} {{")
                for name, ty in s.members.items():
                    lines.append(f"  {ty} {name};")
                lines.append("}")
            lines.append("")

        # 打印全局变量
        if ir.global_vars:
            lines.append("; === 全局变量 ===")
            for gv in ir.global_vars:
                if gv.init:
                    lines.append(f"@global {gv.name}: {gv.ty} = {gv.init}")
                else:
                    lines.append(f"@global {gv.name}: {gv.ty}")
            lines.append("")

        # 打印函数
        for func in ir.functions:
            lines.append(self._print_function(func))

        return "\n".join(lines)

    def _print_function(self, func: IRFunction) -> str:
        """打印单个函数"""
        lines = []

        # 函数签名
        params = ", ".join(f"{p.ty} {p.name}" for p in func.params)
        lines.append(f"define {func.return_type} @{func.name}({params}) {{")

        # 基本块
        for bb in func.basic_blocks:
            lines.append(self._print_basic_block(bb))

        lines.append("}")
        lines.append("")

        return "\n".join(lines)

    def _print_basic_block(self, bb: IRBasicBlock) -> str:
        """打印单个基本块"""
        lines = []

        # 基本块标签
        preds = ", ".join(bb.predecessors) if bb.predecessors else ""
        succs = ", ".join(bb.successors) if bb.successors else ""
        pred_part = f" ; preds: [{preds}]" if preds else ""
        succ_part = f" ; succs: [{succs}]" if succs else ""
        lines.append(f"{bb.label}:{pred_part}{succ_part}")

        # 指令
        for instr in bb.instructions:
            lines.append(f"  {instr}")

        return "\n".join(lines)

# -*- coding: utf-8 -*-
"""
ZHC IR - IR → C 后端

将 ZHC IR 转换为可编译的 C 代码。

使用基本块展平算法，将 IR 基本块展平为线性 C 代码。
采用指令分发模式（dispatch table）替代 if/elif 链，降低圈复杂度。

优化提示支持（TASK-P3-003）：
- 小函数添加 `inline` 关键字
- 热点函数添加 `__attribute__((hot))`
- 冷点函数添加 `__attribute__((cold))`
- 强制内联添加 `__attribute__((always_inline))`
- 不返回函数添加 `__attribute__((noreturn))`

作者：远
日期：2026-04-03
重构：2026-04-07（引入指令分发表，降低 _generate_instruction 复杂度）
重构：2026-04-08（TASK-P3-003：添加优化提示支持）
"""

from typing import Callable, Dict, List, Optional

from zhc.ir.program import IRProgram, IRFunction
from zhc.ir.instructions import IRBasicBlock, IRInstruction
from zhc.ir.opcodes import Opcode
from zhc.ir.mappings import (
    resolve_type,
    resolve_function_name,
)

# 优化提示模块（可选依赖）
try:
    from zhc.ir.optimization_hints import (
        OptimizationHintAnalyzer,
        ProgramOptimizationHints,
        FunctionOptimizationHints,
        CBackendHintAdapter,
    )
    OPTIMIZATION_HINTS_AVAILABLE = True
except ImportError:
    OPTIMIZATION_HINTS_AVAILABLE = False
    OptimizationHintAnalyzer = None
    ProgramOptimizationHints = None
    FunctionOptimizationHints = None
    CBackendHintAdapter = None

# ---------------------------------------------------------------------------
# 二元运算符映射表（IR Opcode → C 运算符）
# ---------------------------------------------------------------------------
_ARITHMETIC_OP: Dict[Opcode, str] = {
    Opcode.ADD: "+",
    Opcode.SUB: "-",
    Opcode.MUL: "*",
    Opcode.DIV: "/",
    Opcode.MOD: "%",
}

_COMPARISON_OP: Dict[Opcode, str] = {
    Opcode.EQ: "==",
    Opcode.NE: "!=",
    Opcode.LT: "<",
    Opcode.LE: "<=",
    Opcode.GT: ">",
    Opcode.GE: ">=",
}

_LOGICAL_BINARY_OP: Dict[Opcode, str] = {
    Opcode.L_AND: "&&",
    Opcode.L_OR: "||",
}


class CBackend:
    """IR → C 代码生成器

    将 IRProgram 转换为 C 代码字符串。使用指令分发表（dispatch table）
    将每种 opcode 映射到对应的生成方法，替代传统的 if/elif 链。
    
    TASK-P3-003 新增功能：
    - 支持优化提示分析
    - 自动添加 inline 关键字和 GCC/Clang 属性
    """

    def __init__(self, enable_optimization_hints: bool = True):
        """初始化 C 后端
        
        Args:
            enable_optimization_hints: 是否启用优化提示（默认 True）
        """
        self.output_lines: List[str] = []
        self.temp_names: dict = {}  # IR temp name -> C temp name
        
        # 优化提示配置
        self.enable_optimization_hints = enable_optimization_hints and OPTIMIZATION_HINTS_AVAILABLE
        self.optimization_hints: Optional[ProgramOptimizationHints] = None
        self.hint_adapter: Optional[CBackendHintAdapter] = None
        
        if self.enable_optimization_hints:
            self.hint_adapter = CBackendHintAdapter()

        # 指令分发表：opcode → 生成方法
        self._op_handlers: Dict[Opcode, Callable[[IRInstruction], None]] = {
            Opcode.RET: self._handle_return,
            Opcode.ALLOC: self._handle_alloc,
            Opcode.STORE: self._handle_store,
            Opcode.LOAD: self._handle_load,
            Opcode.CONST: self._handle_const,
            Opcode.NEG: self._handle_neg,
            Opcode.L_NOT: self._handle_lnot,
            Opcode.CALL: self._handle_call,
            Opcode.GETPTR: self._handle_getptr,
            Opcode.GEP: self._handle_gep,
            Opcode.JMP: self._handle_jmp,
            Opcode.JZ: self._handle_jz,
        }
        # 二元运算操作码集合（用于快速判断）
        self._binary_opcodes = (
            set(_ARITHMETIC_OP.keys())
            | set(_COMPARISON_OP.keys())
            | set(_LOGICAL_BINARY_OP.keys())
        )

    def generate(self, ir: IRProgram) -> str:
        """将 IR 程序转换为 C 代码

        Args:
            ir: IR程序对象

        Returns:
            生成的C代码字符串
        """
        self.output_lines = []
        self.temp_names = {}

        # TASK-P3-003：分析优化提示
        if self.enable_optimization_hints:
            analyzer = OptimizationHintAnalyzer(ir)
            self.optimization_hints = analyzer.analyze()

        self._emit_headers()
        self._emit_global_vars(ir)
        self._emit_functions(ir)

        return "\n".join(self.output_lines)

    # ------------------------------------------------------------------
    # 顶层生成方法
    # ------------------------------------------------------------------

    def _emit_headers(self) -> None:
        """输出C头文件引用"""
        self._emit("#include <stdio.h>")
        self._emit("#include <stdlib.h>")
        self._emit("")

    def _emit_global_vars(self, ir: IRProgram) -> None:
        """输出全局变量声明"""
        for gv in ir.global_vars:
            self._emit(f"{resolve_type(gv.ty or 'int')} {gv.name};")
        if ir.global_vars:
            self._emit("")

    def _emit_functions(self, ir: IRProgram) -> None:
        """输出所有函数定义"""
        for func in ir.functions:
            self._generate_function(func)

    # ------------------------------------------------------------------
    # 函数和基本块生成
    # ------------------------------------------------------------------

    def _generate_function(self, func: IRFunction) -> None:
        """生成单个C函数

        Args:
            func: IR函数对象
        """
        ret_type = resolve_type(func.return_type or "空型")
        func_name = resolve_function_name(func.name)
        params = ", ".join(
            f"{resolve_type(p.ty or 'int')} {p.name}" for p in func.params
        )
        
        # TASK-P3-003：获取优化提示前缀
        hint_prefix = self._get_function_hint_prefix(func.name)
        
        self._emit(f"{hint_prefix}{ret_type} {func_name}({params}) {{")

        # 展平所有基本块的指令
        for bb in func.basic_blocks:
            self._generate_basic_block(bb)

        self._emit("}")
        self._emit("")
    
    def _get_function_hint_prefix(self, func_name: str) -> str:
        """获取函数的优化提示前缀
        
        TASK-P3-003 新增
        
        Args:
            func_name: 函数名
            
        Returns:
            优化提示前缀字符串
        """
        if not self.enable_optimization_hints or not self.hint_adapter:
            return ""
        
        func_hints = self.optimization_hints.get_function_hints(func_name)
        if func_hints and self.hint_adapter:
            return self.hint_adapter.get_function_prefix(func_hints)
        
        return ""

    def _generate_basic_block(self, bb: IRBasicBlock) -> None:
        """生成基本块内的所有指令

        Args:
            bb: IR基本块
        """
        for instr in bb.instructions:
            self._generate_instruction(instr)

    # ------------------------------------------------------------------
    # 指令分发核心
    # ------------------------------------------------------------------

    def _generate_instruction(self, instr: IRInstruction) -> None:
        """指令分发器 — 根据opcode选择对应的处理方法

        使用 dispatch table 替代 if/elif 链，大幅降低圈复杂度。

        Args:
            instr: IR指令
        """
        op = instr.opcode

        # 先检查是否是二元运算
        if op in self._binary_opcodes:
            c_op = self._resolve_binary_operator(op)
            self._emit_binary_op(instr, c_op)
            return

        # 查找分发表中的处理器
        handler = self._op_handlers.get(op)
        if handler:
            handler(instr)
            return

        # 未知 opcode — 静默忽略（保持向后兼容）

    def _resolve_binary_operator(self, op: Opcode) -> str:
        """查找二元运算的C运算符

        Args:
            op: IR操作码

        Returns:
            对应的C运算符字符串
        """
        if op in _ARITHMETIC_OP:
            return _ARITHMETIC_OP[op]
        if op in _COMPARISON_OP:
            return _COMPARISON_OP[op]
        if op in _LOGICAL_BINARY_OP:
            return _LOGICAL_BINARY_OP[op]
        return op.name  # 兜底

    # ------------------------------------------------------------------
    # 各 opcode 的处理方法（每个方法复杂度 < 5）
    # ------------------------------------------------------------------

    def _handle_return(self, instr: IRInstruction) -> None:
        """处理 RET 指令"""
        if instr.operands:
            self._emit(f"return {instr.operands[0]};")
        else:
            self._emit("return;")

    def _handle_alloc(self, instr: IRInstruction) -> None:
        """处理 ALLOC 指令 — 变量声明"""
        if instr.operands and instr.result:
            var = instr.operands[0]
            res = instr.result[0]
            ty = getattr(var, "ty", None) or "int"
            self.temp_names[res.name] = var.name
            self._emit(f"{resolve_type(ty)} {var.name};")

    def _handle_store(self, instr: IRInstruction) -> None:
        """处理 STORE 指令 — 赋值语句"""
        if len(instr.operands) >= 2:
            val, ptr = instr.operands[0], instr.operands[1]
            self._emit(f"{ptr} = {val};")

    def _handle_load(self, instr: IRInstruction) -> None:
        """处理 LOAD 指令 — 取值"""
        if len(instr.operands) >= 1 and instr.result:
            ptr = instr.operands[0]
            res = instr.result[0]
            self._emit(f"{res} = {ptr};")

    def _handle_const(self, instr: IRInstruction) -> None:
        """处理 CONST 指令 — 常量赋值"""
        if instr.operands and instr.result:
            const_val = instr.operands[0]
            res = instr.result[0]
            self._emit(f"{res} = {const_val};")

    def _handle_neg(self, instr: IRInstruction) -> None:
        """处理 NEG 指令 — 取负"""
        if instr.operands and instr.result:
            res = instr.result[0]
            opnd = instr.operands[0]
            self._emit(f"{res} = -{opnd};")

    def _handle_lnot(self, instr: IRInstruction) -> None:
        """处理 L_NOT 指令 — 逻辑非"""
        if instr.operands and instr.result:
            res = instr.result[0]
            opnd = instr.operands[0]
            self._emit(f"{res} = !{opnd};")

    def _handle_call(self, instr: IRInstruction) -> None:
        """处理 CALL 指令 — 函数调用"""
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

    def _handle_getptr(self, instr: IRInstruction) -> None:
        """处理 GETPTR 指令 — 取地址/数组索引"""
        if len(instr.operands) >= 2 and instr.result:
            base, index = instr.operands[0], instr.operands[1]
            res = instr.result[0]
            self._emit(f"{res} = {base}[{index}];")
        elif len(instr.operands) >= 1 and instr.result:
            base = instr.operands[0]
            res = instr.result[0]
            self._emit(f"{res} = &{base};")

    def _handle_gep(self, instr: IRInstruction) -> None:
        """处理 GEP 指针算术"""
        if len(instr.operands) >= 2 and instr.result:
            base, index = instr.operands[0], instr.operands[1]
            res = instr.result[0]
            self._emit(f"{res} = {base} + {index};")

    def _handle_jmp(self, instr: IRInstruction) -> None:
        """处理 JMP 指令（展平模式下无需输出）"""

    def _handle_jz(self, instr: IRInstruction) -> None:
        """处理 JZ 条件跳转（展平模式下无需输出）"""

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    def _emit_binary_op(self, instr: IRInstruction, op_str: str) -> None:
        """生成二元运算 C 语句

        Args:
            instr: IR指令
            op_str: C运算符（如 '+', '*', '==' 等）
        """
        if len(instr.operands) >= 2 and instr.result:
            left, right = instr.operands[0], instr.operands[1]
            res = instr.result[0]
            self._emit(f"{res} = {left} {op_str} {right};")

    def _emit(self, line: str = "") -> None:
        """输出一行到结果缓冲区

        Args:
            line: 要输出的行内容（默认空行）
        """
        self.output_lines.append(line)

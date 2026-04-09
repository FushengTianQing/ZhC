# -*- coding: utf-8 -*-
"""ZhC LLVM 指令生成器

将 ZhC IR Opcode 映射到 LLVM IR 指令。

作者：远
日期：2026-04-08
"""

from typing import Dict, Callable, Optional, Any
from dataclasses import dataclass

try:
    import llvmlite.ir as ll

    LLVM_AVAILABLE = True
except ImportError:
    LLVM_AVAILABLE = False
    ll = None

from zhc.ir.opcodes import Opcode
from zhc.ir.instructions import IRInstruction
from zhc.ir.values import ValueKind


@dataclass
class InstructionInfo:
    """指令信息"""

    opcode: Opcode  # ZhC Opcode
    llvm_op: str  # LLVM 操作名
    category: str  # 类别（算术/比较/内存/控制流）
    has_result: bool  # 是否产生结果
    description: str  # 描述


class LLVMInstructionGenerator:
    """LLVM 指令生成器

    将 ZhC IR Opcode 映射到 LLVM IR 指令。
    """

    # 指令映射表
    INSTRUCTION_MAP: Dict[Opcode, InstructionInfo] = {
        # 算术运算
        Opcode.ADD: InstructionInfo(Opcode.ADD, "add", "算术", True, "加法"),
        Opcode.SUB: InstructionInfo(Opcode.SUB, "sub", "算术", True, "减法"),
        Opcode.MUL: InstructionInfo(Opcode.MUL, "mul", "算术", True, "乘法"),
        Opcode.DIV: InstructionInfo(Opcode.DIV, "sdiv", "算术", True, "有符号除法"),
        Opcode.MOD: InstructionInfo(Opcode.MOD, "srem", "算术", True, "有符号取模"),
        Opcode.NEG: InstructionInfo(Opcode.NEG, "neg", "算术", True, "取负"),
        # 比较运算
        Opcode.EQ: InstructionInfo(Opcode.EQ, "icmp eq", "比较", True, "等于"),
        Opcode.NE: InstructionInfo(Opcode.NE, "icmp ne", "比较", True, "不等于"),
        Opcode.LT: InstructionInfo(Opcode.LT, "icmp slt", "比较", True, "小于"),
        Opcode.LE: InstructionInfo(Opcode.LE, "icmp sle", "比较", True, "小于等于"),
        Opcode.GT: InstructionInfo(Opcode.GT, "icmp sgt", "比较", True, "大于"),
        Opcode.GE: InstructionInfo(Opcode.GE, "icmp sge", "比较", True, "大于等于"),
        # 位运算
        Opcode.AND: InstructionInfo(Opcode.AND, "and", "位运算", True, "按位与"),
        Opcode.OR: InstructionInfo(Opcode.OR, "or", "位运算", True, "按位或"),
        Opcode.XOR: InstructionInfo(Opcode.XOR, "xor", "位运算", True, "按位异或"),
        Opcode.NOT: InstructionInfo(Opcode.NOT, "not", "位运算", True, "按位取反"),
        Opcode.SHL: InstructionInfo(Opcode.SHL, "shl", "位运算", True, "左移"),
        Opcode.SHR: InstructionInfo(Opcode.SHR, "shr", "位运算", True, "右移"),
        # 内存操作
        Opcode.ALLOC: InstructionInfo(Opcode.ALLOC, "alloca", "内存", True, "分配内存"),
        Opcode.LOAD: InstructionInfo(Opcode.LOAD, "load", "内存", True, "加载"),
        Opcode.STORE: InstructionInfo(Opcode.STORE, "store", "内存", False, "存储"),
        Opcode.GETPTR: InstructionInfo(
            Opcode.GETPTR, "getelementptr", "内存", True, "获取指针"
        ),
        Opcode.GEP: InstructionInfo(
            Opcode.GEP, "getelementptr", "内存", True, "指针运算"
        ),
        # 控制流
        Opcode.JMP: InstructionInfo(Opcode.JMP, "br", "控制流", False, "无条件跳转"),
        Opcode.JZ: InstructionInfo(Opcode.JZ, "br", "控制流", False, "条件跳转"),
        Opcode.RET: InstructionInfo(Opcode.RET, "ret", "控制流", False, "返回"),
        Opcode.CALL: InstructionInfo(Opcode.CALL, "call", "控制流", True, "函数调用"),
        Opcode.SWITCH: InstructionInfo(
            Opcode.SWITCH, "switch", "控制流", False, "分支跳转"
        ),
        Opcode.PHI: InstructionInfo(Opcode.PHI, "phi", "控制流", True, "phi节点"),
        # 类型转换
        Opcode.ZEXT: InstructionInfo(Opcode.ZEXT, "zext", "转换", True, "零扩展"),
        Opcode.SEXT: InstructionInfo(Opcode.SEXT, "sext", "转换", True, "符号扩展"),
        Opcode.TRUNC: InstructionInfo(Opcode.TRUNC, "trunc", "转换", True, "截断"),
        Opcode.BITCAST: InstructionInfo(
            Opcode.BITCAST, "bitcast", "转换", True, "位转换"
        ),
        Opcode.INT2PTR: InstructionInfo(
            Opcode.INT2PTR, "inttoptr", "转换", True, "整数到指针"
        ),
        Opcode.PTR2INT: InstructionInfo(
            Opcode.PTR2INT, "ptrtoint", "转换", True, "指针到整数"
        ),
    }

    def __init__(self):
        """初始化指令生成器"""
        if not LLVM_AVAILABLE:
            raise ImportError("llvmlite 未安装")

        self._generators: Dict[Opcode, Callable] = {}
        self._build_generators()

    def _build_generators(self):
        """构建指令生成器映射"""
        # 算术指令
        self._generators[Opcode.ADD] = self._gen_add
        self._generators[Opcode.SUB] = self._gen_sub
        self._generators[Opcode.MUL] = self._gen_mul
        self._generators[Opcode.DIV] = self._gen_div
        self._generators[Opcode.MOD] = self._gen_mod

        # 比较指令
        self._generators[Opcode.EQ] = self._gen_icmp_eq
        self._generators[Opcode.NE] = self._gen_icmp_ne
        self._generators[Opcode.LT] = self._gen_icmp_lt
        self._generators[Opcode.LE] = self._gen_icmp_le
        self._generators[Opcode.GT] = self._gen_icmp_gt
        self._generators[Opcode.GE] = self._gen_icmp_ge

        # 位运算指令
        self._generators[Opcode.AND] = self._gen_and
        self._generators[Opcode.OR] = self._gen_or
        self._generators[Opcode.XOR] = self._gen_xor

        # 内存指令
        self._generators[Opcode.ALLOC] = self._gen_alloca
        self._generators[Opcode.LOAD] = self._gen_load
        self._generators[Opcode.STORE] = self._gen_store

        # 控制流指令
        self._generators[Opcode.JMP] = self._gen_br
        self._generators[Opcode.JZ] = self._gen_cbranch
        self._generators[Opcode.RET] = self._gen_ret
        self._generators[Opcode.CALL] = self._gen_call

        # 类型转换指令
        self._generators[Opcode.ZEXT] = self._gen_zext
        self._generators[Opcode.SEXT] = self._gen_sext
        self._generators[Opcode.TRUNC] = self._gen_trunc

    def generate(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
        string_constants: Optional[Dict[str, ll.Value]] = None,
    ) -> Optional[ll.Value]:
        """生成 LLVM 指令

        Args:
            builder: LLVM IRBuilder
            instr: ZhC IR 指令
            values: 值映射表
            blocks: 基本块映射表
            functions: 函数映射表
            string_constants: 字符串常量缓存（字符串内容 -> 全局变量）

        Returns:
            生成的 LLVM 值（如果有结果）
        """
        opcode = instr.opcode
        self._string_constants = string_constants or {}
        self._builder = builder  # 保存 builder 供 _create_global_string 使用

        if opcode in self._generators:
            return self._generators[opcode](builder, instr, values, blocks, functions)

        # 未实现的指令
        return None

    # ========== 算术指令生成器 ==========

    def _gen_add(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成加法指令"""
        a = self._get_value(instr.operands[0], values)
        b = self._get_value(instr.operands[1], values)
        name = self._get_result_name(instr)
        return builder.add(a, b, name=name)

    def _gen_sub(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成减法指令"""
        a = self._get_value(instr.operands[0], values)
        b = self._get_value(instr.operands[1], values)
        name = self._get_result_name(instr)
        return builder.sub(a, b, name=name)

    def _gen_mul(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成乘法指令"""
        a = self._get_value(instr.operands[0], values)
        b = self._get_value(instr.operands[1], values)
        name = self._get_result_name(instr)
        return builder.mul(a, b, name=name)

    def _gen_div(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成除法指令"""
        a = self._get_value(instr.operands[0], values)
        b = self._get_value(instr.operands[1], values)
        name = self._get_result_name(instr)
        return builder.sdiv(a, b, name=name)

    def _gen_mod(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成取模指令"""
        a = self._get_value(instr.operands[0], values)
        b = self._get_value(instr.operands[1], values)
        name = self._get_result_name(instr)
        return builder.srem(a, b, name=name)

    # ========== 比较指令生成器 ==========

    def _gen_icmp_eq(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成等于比较指令"""
        a = self._get_value(instr.operands[0], values)
        b = self._get_value(instr.operands[1], values)
        name = self._get_result_name(instr)
        return builder.icmp_signed("==", a, b, name=name)

    def _gen_icmp_ne(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成不等于比较指令"""
        a = self._get_value(instr.operands[0], values)
        b = self._get_value(instr.operands[1], values)
        name = self._get_result_name(instr)
        return builder.icmp_signed("!=", a, b, name=name)

    def _gen_icmp_lt(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成小于比较指令"""
        a = self._get_value(instr.operands[0], values)
        b = self._get_value(instr.operands[1], values)
        name = self._get_result_name(instr)
        return builder.icmp_signed("<", a, b, name=name)

    def _gen_icmp_le(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成小于等于比较指令"""
        a = self._get_value(instr.operands[0], values)
        b = self._get_value(instr.operands[1], values)
        name = self._get_result_name(instr)
        return builder.icmp_signed("<=", a, b, name=name)

    def _gen_icmp_gt(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成大于比较指令"""
        a = self._get_value(instr.operands[0], values)
        b = self._get_value(instr.operands[1], values)
        name = self._get_result_name(instr)
        return builder.icmp_signed(">", a, b, name=name)

    def _gen_icmp_ge(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成大于等于比较指令"""
        a = self._get_value(instr.operands[0], values)
        b = self._get_value(instr.operands[1], values)
        name = self._get_result_name(instr)
        return builder.icmp_signed(">=", a, b, name=name)

    # ========== 位运算指令生成器 ==========

    def _gen_and(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成按位与指令"""
        a = self._get_value(instr.operands[0], values)
        b = self._get_value(instr.operands[1], values)
        name = self._get_result_name(instr)
        return builder.and_(a, b, name=name)

    def _gen_or(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成按位或指令"""
        a = self._get_value(instr.operands[0], values)
        b = self._get_value(instr.operands[1], values)
        name = self._get_result_name(instr)
        return builder.or_(a, b, name=name)

    def _gen_xor(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成按位异或指令"""
        a = self._get_value(instr.operands[0], values)
        b = self._get_value(instr.operands[1], values)
        name = self._get_result_name(instr)
        return builder.xor(a, b, name=name)

    # ========== 内存指令生成器 ==========

    def _gen_alloca(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成内存分配指令"""
        # 获取类型
        ty = ll.IntType(32)  # 默认类型
        if instr.operands:
            op = instr.operands[0]
            if hasattr(op, "ty"):
                ty = self._map_type(op.ty)

        name = self._get_result_name(instr)
        return builder.alloca(ty, name=name)

    def _gen_load(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成加载指令"""
        ptr = self._get_value(instr.operands[0], values)
        name = self._get_result_name(instr)
        return builder.load(ptr, name=name)

    def _gen_store(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> None:
        """生成存储指令"""
        val = self._get_value(instr.operands[0], values)
        ptr = self._get_value(instr.operands[1], values)
        builder.store(val, ptr)
        return None

    # ========== 控制流指令生成器 ==========

    def _gen_br(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> None:
        """生成无条件跳转指令"""
        target_label = str(instr.operands[0])
        target = blocks.get(target_label)
        if target:
            builder.branch(target)
        return None

    def _gen_cbranch(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> None:
        """生成条件跳转指令"""
        cond = self._get_value(instr.operands[0], values)
        target_label = str(instr.operands[1])
        target = blocks.get(target_label)

        if target:
            # 简化处理：两个分支都跳到同一个目标
            builder.cbranch(cond, target, target)
        return None

    def _gen_ret(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> None:
        """生成返回指令"""
        if instr.operands:
            val = self._get_value(instr.operands[0], values)
            builder.ret(val)
        else:
            builder.ret_void()
        return None

    def _gen_call(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成函数调用指令"""
        callee_name = str(instr.operands[0])
        args = [self._get_value(a, values) for a in instr.operands[1:]]

        # 查找函数
        callee = functions.get(callee_name)
        if callee:
            name = self._get_result_name(instr)
            return builder.call(callee, args, name=name)

        # 外部函数（简化处理）
        func_ty = ll.FunctionType(ll.IntType(32), [ll.IntType(32)] * len(args))
        callee = ll.Function(builder.module, func_ty, callee_name)
        name = self._get_result_name(instr)
        return builder.call(callee, args, name=name)

    # ========== 类型转换指令生成器 ==========

    def _gen_zext(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成零扩展指令"""
        val = self._get_value(instr.operands[0], values)
        target_ty = ll.IntType(32)  # 默认目标类型
        name = self._get_result_name(instr)
        return builder.zext(val, target_ty, name=name)

    def _gen_sext(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成符号扩展指令"""
        val = self._get_value(instr.operands[0], values)
        target_ty = ll.IntType(32)  # 默认目标类型
        name = self._get_result_name(instr)
        return builder.sext(val, target_ty, name=name)

    def _gen_trunc(
        self,
        builder: ll.IRBuilder,
        instr: IRInstruction,
        values: Dict[str, ll.Value],
        blocks: Dict[str, ll.Block],
        functions: Dict[str, ll.Function],
    ) -> ll.Value:
        """生成截断指令"""
        val = self._get_value(instr.operands[0], values)
        target_ty = ll.IntType(8)  # 默认目标类型
        name = self._get_result_name(instr)
        return builder.trunc(val, target_ty, name=name)

    # ========== 辅助方法 ==========

    def _create_global_string(self, content: str) -> ll.Value:
        """创建或获取全局字符串常量

        Args:
            content: 字符串内容（不含引号）

        Returns:
            指向字符串的 i8* 指针
        """
        # 缓存检查
        if content in self._string_constants:
            return self._string_constants[content]

        # 获取 module（需要从 builder 获取）
        module = self._builder.module

        # 创建唯一的全局变量名
        global_name = f".str.{len(self._string_constants)}"

        # 创建字符数组类型 [n x i8]
        byte_count = len(content) + 1  # +1 for null terminator
        char_array_type = ll.ArrayType(ll.IntType(8), byte_count)

        # 创建字节串（包含 null 终止符）
        byte_data = [ll.Constant(ll.IntType(8), ord(b)) for b in content]
        byte_data.append(ll.Constant(ll.IntType(8), 0))  # null terminator

        # 创建全局变量
        global_var = ll.GlobalVariable(module, char_array_type, global_name)
        global_var.linkage = "private"
        global_var.global_constant = True
        global_var.initializer = ll.Constant(char_array_type, byte_data)

        # 缓存结果
        self._string_constants[content] = global_var

        return global_var

    def _get_value(self, operand: Any, values: Dict[str, ll.Value]) -> ll.Value:
        """获取 LLVM 值"""
        # 如果是字符串
        if isinstance(operand, str):
            # 检查是否是字符串常量（以引号开头）
            if operand.startswith('"') and operand.endswith('"'):
                # 提取字符串内容
                string_content = operand[1:-1]
                return self._create_global_string(string_content)

            # 检查是否是已存在的值
            if operand in values:
                return values[operand]

            # 检查是否是常量
            if operand.isdigit():
                return ll.Constant(ll.IntType(32), int(operand))

            # 检查是否是变量名（%开头）
            if operand.startswith("%"):
                name = operand[1:]
                if name in values:
                    return values[name]

            # 默认返回常量
            return ll.Constant(ll.IntType(32), 0)

        # 如果是 IRValue 对象
        if hasattr(operand, "name"):
            name = operand.name
            if name in values:
                return values[name]

            # 常量
            if hasattr(operand, "kind") and operand.kind == ValueKind.CONST:
                return ll.Constant(ll.IntType(32), operand.const_value or 0)

        return ll.Constant(ll.IntType(32), 0)

    def _get_result_name(self, instr: IRInstruction) -> Optional[str]:
        """获取结果名称"""
        if instr.result:
            res_obj = instr.result[0]
            if hasattr(res_obj, "name"):
                return res_obj.name
            return str(res_obj)
        return None

    def _map_type(self, zhc_type: str) -> ll.Type:
        """映射 ZhC 类型到 LLVM 类型"""
        type_map = {
            "整数型": ll.IntType(32),
            "浮点型": ll.FloatType(),
            "双精度浮点型": ll.DoubleType(),
            "字符型": ll.IntType(8),
            "布尔型": ll.IntType(1),
            "i32": ll.IntType(32),
            "i64": ll.IntType(64),
            "i16": ll.IntType(16),
            "i8": ll.IntType(8),
        }
        return type_map.get(zhc_type, ll.IntType(32))

    def get_instruction_info(self, opcode: Opcode) -> Optional[InstructionInfo]:
        """获取指令信息"""
        return self.INSTRUCTION_MAP.get(opcode)

    def is_supported(self, opcode: Opcode) -> bool:
        """判断指令是否支持"""
        return opcode in self._generators


def generate_llvm_instruction(
    builder: ll.IRBuilder,
    instr: IRInstruction,
    values: Dict[str, ll.Value],
    blocks: Dict[str, ll.Block],
    functions: Dict[str, ll.Function],
) -> Optional[ll.Value]:
    """便捷函数：生成 LLVM 指令

    Args:
        builder: LLVM IRBuilder
        instr: ZhC IR 指令
        values: 值映射表
        blocks: 基本块映射表
        functions: 函数映射表

    Returns:
        生成的 LLVM 值（如果有结果）
    """
    generator = LLVMInstructionGenerator()
    return generator.generate(builder, instr, values, blocks, functions)

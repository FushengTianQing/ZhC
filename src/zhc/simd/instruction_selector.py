# -*- coding: utf-8 -*-
"""
ZhC SIMD 指令选择器

将通用 SIMD 操作映射到目标平台的特定 SIMD 指令。

支持的平台：
- x86: SSE, SSE2, SSE4, AVX, AVX2, AVX-512
- ARM: NEON, SVE
- RISC-V: RVV
- WebAssembly: SIMD128

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SIMDOpType(Enum):
    """SIMD 操作类型"""

    # 算术运算
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    NEG = "neg"
    ABS = "abs"
    SQRT = "sqrt"
    FMA = "fma"  # 乘加融合

    # 比较运算
    CMP_EQ = "cmp_eq"
    CMP_NE = "cmp_ne"
    CMP_LT = "cmp_lt"
    CMP_LE = "cmp_le"
    CMP_GT = "cmp_gt"
    CMP_GE = "cmp_ge"

    # 逻辑运算
    AND = "and"
    OR = "or"
    XOR = "xor"
    NOT = "not"

    # 移位运算
    SHL = "shl"
    SHR = "shr"
    SAR = "sar"

    # 广播/填充
    BROADCAST = "broadcast"
    SPLAT = "splat"

    # 内存操作
    LOAD = "load"
    STORE = "store"
    GATHER = "gather"
    SCATTER = "scatter"

    # 混排操作
    SHUFFLE = "shuffle"
    BLEND = "blend"
    PERMUTE = "permute"
    EXTRACT = "extract"
    INSERT = "insert"

    # 类型转换
    CAST = "cast"
    ZEXT = "zext"  # 零扩展
    SEXT = "sext"  # 符号扩展
    TRUNC = "trunc"  # 截断

    # 归约操作
    REDUCE_ADD = "reduce_add"
    REDUCE_MUL = "reduce_mul"
    REDUCE_MAX = "reduce_max"
    REDUCE_MIN = "reduce_min"


@dataclass
class InstructionInfo:
    """SIMD 指令信息"""

    name: str  # 指令名称
    intrinsic: str  # 对应的 LLVM intrinsic
    latency: float  # 延迟周期
    throughput: float  # 吞吐量
    encoding: Optional[str] = None  # 编码信息


@dataclass
class ISelResult:
    """指令选择结果"""

    instructions: List[str]  # 生成的指令
    result_var: str  # 结果变量名
    aux_vars: List[str] = field(default_factory=list)  # 辅助变量


class InstructionSelector:
    """
    SIMD 指令选择器

    将抽象的 SIMD 操作映射到目标平台的具体指令。
    """

    def __init__(self, target_arch: str = "generic", vector_width: int = 4):
        self.target_arch = target_arch
        self.vector_width = vector_width
        self._temp_counter = 0
        self._setup_instruction_table()

    def _setup_instruction_table(self) -> None:
        """设置指令表"""
        self.instruction_table: Dict[str, Dict[SIMDOpType, InstructionInfo]] = {}

        # x86 SSE/AVX 指令表
        self.instruction_table["x86"] = {
            SIMDOpType.ADD: InstructionInfo(
                "addps/addpd", "llvm.x86.sse.add.ps", 4, 1.0
            ),
            SIMDOpType.SUB: InstructionInfo(
                "subps/subpd", "llvm.x86.sse.sub.ps", 4, 1.0
            ),
            SIMDOpType.MUL: InstructionInfo(
                "mulps/mulpd", "llvm.x86.sse.mul.ps", 4, 1.0
            ),
            SIMDOpType.DIV: InstructionInfo(
                "divps/divpd", "llvm.x86.sse.div.ps", 12, 0.25
            ),
            SIMDOpType.FMA: InstructionInfo(
                "vfmaddps", "llvm.x86.fma.vfmadd.ps", 4, 1.0
            ),
            SIMDOpType.SQRT: InstructionInfo(
                "sqrtps/sqrtpd", "llvm.x86.sse.sqrt.ps", 12, 0.5
            ),
            SIMDOpType.CMP_EQ: InstructionInfo(
                "cmpps(eq)", "llvm.x86.sse.cmp.ps", 4, 1.0
            ),
            SIMDOpType.AND: InstructionInfo(
                "andps/andpd", "llvm.x86.sse.and.ps", 2, 1.0
            ),
            SIMDOpType.OR: InstructionInfo("orps/orpd", "llvm.x86.sse.or.ps", 2, 1.0),
            SIMDOpType.XOR: InstructionInfo(
                "xorps/xorpd", "llvm.x86.sse.xor.ps", 2, 1.0
            ),
            SIMDOpType.LOAD: InstructionInfo(
                "movups/movups", "llvm.x86.sse.loadu.ps", 4, 1.0
            ),
            SIMDOpType.STORE: InstructionInfo(
                "movups/movups", "llvm.x86.sse.storeu.ps", 4, 1.0
            ),
        }

        # ARM NEON 指令表
        self.instruction_table["arm_neon"] = {
            SIMDOpType.ADD: InstructionInfo("add", "llvm.aarch64.neon.add", 4, 1.0),
            SIMDOpType.SUB: InstructionInfo("sub", "llvm.aarch64.neon.sub", 4, 1.0),
            SIMDOpType.MUL: InstructionInfo("mul", "llvm.aarch64.neon.mul", 4, 1.0),
            SIMDOpType.DIV: InstructionInfo("fdiv", "llvm.aarch64.neon.fdiv", 12, 0.25),
            SIMDOpType.FMA: InstructionInfo("fmla", "llvm.aarch64.neon.fmla", 4, 1.0),
            SIMDOpType.SQRT: InstructionInfo(
                "fsqrt", "llvm.aarch64.neon.fsqrt", 12, 0.5
            ),
            SIMDOpType.AND: InstructionInfo("and", "llvm.aarch64.neon.and", 2, 1.0),
            SIMDOpType.OR: InstructionInfo("orr", "llvm.aarch64.neon.orr", 2, 1.0),
            SIMDOpType.XOR: InstructionInfo("eor", "llvm.aarch64.neon.eor", 2, 1.0),
        }

        # RISC-V RVV 指令表
        self.instruction_table["riscv_rvv"] = {
            SIMDOpType.ADD: InstructionInfo("vadd", "llvm.riscv.vadd", 2, 2.0),
            SIMDOpType.SUB: InstructionInfo("vsub", "llvm.riscv.vsub", 2, 2.0),
            SIMDOpType.MUL: InstructionInfo("vmul", "llvm.riscv.vmulo", 4, 1.0),
            SIMDOpType.FMA: InstructionInfo("vfmadd", "llvm.riscv.vfmacc", 4, 1.0),
            SIMDOpType.LOAD: InstructionInfo("vle", "llvm.riscv.vle", 4, 1.0),
            SIMDOpType.STORE: InstructionInfo("vse", "llvm.riscv.vse", 4, 1.0),
        }

        # WebAssembly SIMD 指令表
        self.instruction_table["wasm_simd"] = {
            SIMDOpType.ADD: InstructionInfo("i32x4.add", "llvm.wasm.simd.add", 2, 2.0),
            SIMDOpType.SUB: InstructionInfo("i32x4.sub", "llvm.wasm.simd.sub", 2, 2.0),
            SIMDOpType.MUL: InstructionInfo("i32x4.mul", "llvm.wasm.simd.mul", 4, 1.0),
            SIMDOpType.AND: InstructionInfo("v128.and", "llvm.wasm.simd.and", 1, 2.0),
            SIMDOpType.OR: InstructionInfo("v128.or", "llvm.wasm.simd.or", 1, 2.0),
            SIMDOpType.XOR: InstructionInfo("v128.xor", "llvm.wasm.simd.xor", 1, 2.0),
            SIMDOpType.LOAD: InstructionInfo(
                "v128.load", "llvm.wasm.simd.load", 4, 1.0
            ),
            SIMDOpType.STORE: InstructionInfo(
                "v128.store", "llvm.wasm.simd.store", 4, 1.0
            ),
        }

        # 通用 SIMD 指令表（基于 LLVM IR）
        self.instruction_table["generic"] = {
            SIMDOpType.ADD: InstructionInfo("add", "llvm.vector.add", 4, 1.0),
            SIMDOpType.SUB: InstructionInfo("sub", "llvm.vector.sub", 4, 1.0),
            SIMDOpType.MUL: InstructionInfo("mul", "llvm.vector.mul", 4, 1.0),
            SIMDOpType.DIV: InstructionInfo("fdiv", "llvm.vector.fdiv", 12, 0.25),
            SIMDOpType.FMA: InstructionInfo("fma", "llvm.vector.fma", 4, 1.0),
            SIMDOpType.SQRT: InstructionInfo("sqrt", "llvm.vector.sqrt", 12, 0.5),
            SIMDOpType.LOAD: InstructionInfo("load", "llvm.masked.load", 4, 1.0),
            SIMDOpType.STORE: InstructionInfo("store", "llvm.masked.store", 4, 1.0),
        }

    def _get_arch_key(self) -> str:
        """获取架构键"""
        arch_lower = self.target_arch.lower()
        if "avx512" in arch_lower:
            return "x86"
        elif "avx" in arch_lower:
            return "x86"
        elif "sse" in arch_lower:
            return "x86"
        elif "neon" in arch_lower or "aarch64" in arch_lower or "arm" in arch_lower:
            return "arm_neon"
        elif "rvv" in arch_lower or "riscv" in arch_lower:
            return "riscv_rvv"
        elif "wasm" in arch_lower:
            return "wasm_simd"
        return "generic"

    def select_instruction(
        self,
        op_type: SIMDOpType,
        operands: List[str],
        vec_type: str,
        extra_info: Optional[Dict] = None,
    ) -> ISelResult:
        """
        选择 SIMD 指令

        Args:
            op_type: 操作类型
            operands: 操作数列表
            vec_type: 向量类型
            extra_info: 额外信息

        Returns:
            指令选择结果
        """
        arch_key = self._get_arch_key()
        inst_info = self._get_instruction_info(op_type, arch_key)

        instructions = []
        result_var = self._next_temp("result")
        aux_vars = []

        if op_type in (SIMDOpType.ADD, SIMDOpType.SUB, SIMDOpType.MUL, SIMDOpType.DIV):
            instructions.extend(
                self._gen_binary_op(op_type, operands, vec_type, result_var)
            )
        elif op_type in (
            SIMDOpType.CMP_EQ,
            SIMDOpType.CMP_NE,
            SIMDOpType.CMP_LT,
            SIMDOpType.CMP_LE,
            SIMDOpType.CMP_GT,
            SIMDOpType.CMP_GE,
        ):
            predicate = extra_info.get("predicate", "eq") if extra_info else "eq"
            instructions.extend(
                self._gen_compare_op(op_type, operands, vec_type, result_var, predicate)
            )
        elif op_type in (SIMDOpType.AND, SIMDOpType.OR, SIMDOpType.XOR, SIMDOpType.NOT):
            instructions.extend(
                self._gen_logical_op(op_type, operands, vec_type, result_var)
            )
        elif op_type in (SIMDOpType.LOAD, SIMDOpType.STORE):
            instructions.extend(
                self._gen_memory_op(op_type, operands, vec_type, result_var)
            )
        elif op_type == SIMDOpType.FMA:
            instructions.extend(self._gen_fma_op(operands, vec_type, result_var))
        elif op_type == SIMDOpType.SQRT:
            instructions.extend(
                self._gen_unary_op("sqrt", operands[0], vec_type, result_var)
            )
        elif op_type == SIMDOpType.BROADCAST:
            instructions.extend(
                self._gen_broadcast_op(operands[0], vec_type, result_var)
            )
        elif op_type == SIMDOpType.BLEND:
            mask = extra_info.get("mask", "") if extra_info else ""
            instructions.extend(
                self._gen_blend_op(operands, vec_type, result_var, mask)
            )
        else:
            instructions.append(
                f"{result_var} = call {vec_type} @{inst_info.intrinsic}({vec_type} {operands[0]})"
            )

        return ISelResult(
            instructions=instructions,
            result_var=result_var,
            aux_vars=aux_vars,
        )

    def _get_instruction_info(
        self, op_type: SIMDOpType, arch_key: str
    ) -> InstructionInfo:
        """获取指令信息"""
        table = self.instruction_table.get(arch_key, self.instruction_table["generic"])
        return table.get(
            op_type,
            self.instruction_table["generic"].get(
                SIMDOpType.ADD, InstructionInfo("unknown", "llvm.unknown", 4, 1.0)
            ),
        )

    def _gen_binary_op(
        self,
        op_type: SIMDOpType,
        operands: List[str],
        vec_type: str,
        result_var: str,
    ) -> List[str]:
        """生成二元操作指令"""
        op_map = {
            SIMDOpType.ADD: "add",
            SIMDOpType.SUB: "sub",
            SIMDOpType.MUL: "mul",
            SIMDOpType.DIV: "fdiv",
        }
        op = op_map.get(op_type, "add")
        return [f"{result_var} = {op} {vec_type} {operands[0]}, {operands[1]}"]

    def _gen_unary_op(
        self,
        op: str,
        operand: str,
        vec_type: str,
        result_var: str,
    ) -> List[str]:
        """生成一元操作指令"""
        return [f"{result_var} = {op} {vec_type} {operand}"]

    def _gen_compare_op(
        self,
        op_type: SIMDOpType,
        operands: List[str],
        vec_type: str,
        result_var: str,
        predicate: str,
    ) -> List[str]:
        """生成比较操作指令"""
        pred_map = {
            SIMDOpType.CMP_EQ: "oeq",
            SIMDOpType.CMP_NE: "une",
            SIMDOpType.CMP_LT: "olt",
            SIMDOpType.CMP_LE: "ole",
            SIMDOpType.CMP_GT: "ogt",
            SIMDOpType.CMP_GE: "oge",
        }
        llvm_pred = pred_map.get(op_type, "oeq")
        return [
            f"{result_var} = fcmp {llvm_pred} {vec_type} {operands[0]}, {operands[1]}"
        ]

    def _gen_logical_op(
        self,
        op_type: SIMDOpType,
        operands: List[str],
        vec_type: str,
        result_var: str,
    ) -> List[str]:
        """生成逻辑操作指令"""
        if op_type == SIMDOpType.NOT:
            temp = self._next_temp("not_tmp")
            return [
                f"{temp} = xor {vec_type} {operands[0]}, {vec_type} -1",
                f"{result_var} = xor {vec_type} {temp}, {vec_type} -1",
            ]
        op_map = {
            SIMDOpType.AND: "and",
            SIMDOpType.OR: "or",
            SIMDOpType.XOR: "xor",
        }
        op = op_map.get(op_type, "and")
        return [f"{result_var} = {op} {vec_type} {operands[0]}, {operands[1]}"]

    def _gen_memory_op(
        self,
        op_type: SIMDOpType,
        operands: List[str],
        vec_type: str,
        result_var: str,
    ) -> List[str]:
        """生成内存操作指令"""
        if op_type == SIMDOpType.LOAD:
            ptr = operands[0]
            align = operands[1] if len(operands) > 1 else "1"
            return [f"{result_var} = load {vec_type}, {vec_type}* {ptr}, align {align}"]
        else:
            value, ptr = operands[0], operands[1]
            align = operands[2] if len(operands) > 2 else "1"
            return [f"store {vec_type} {value}, {vec_type}* {ptr}, align {align}"]

    def _gen_fma_op(
        self,
        operands: List[str],
        vec_type: str,
        result_var: str,
    ) -> List[str]:
        """生成乘加融合指令"""
        if len(operands) >= 3:
            a, b, c = operands[0], operands[1], operands[2]
            return [
                f"{result_var} = call {vec_type} @llvm.fma.{vec_type}({vec_type} {a}, {vec_type} {b}, {vec_type} {c})"
            ]
        return []

    def _gen_broadcast_op(
        self,
        operand: str,
        vec_type: str,
        result_var: str,
    ) -> List[str]:
        """生成广播指令"""
        return [
            f"{result_var} = insertelement {vec_type} zeroinitializer, {operand} {operand}, i32 0"
        ]

    def _gen_blend_op(
        self,
        operands: List[str],
        vec_type: str,
        result_var: str,
        mask: str,
    ) -> List[str]:
        """生成混合指令"""
        vec_a, vec_b = operands[0], operands[1]
        if mask:
            return [
                f"{result_var} = select <{self.vector_width} x i1> {mask}, {vec_type} {vec_b}, {vec_type} {vec_a}"
            ]
        return [
            f"{result_var} = call {vec_type} @llvm.masked.blend({vec_type} {vec_a}, {vec_type} {vec_b})"
        ]

    def _next_temp(self, prefix: str = "tmp") -> str:
        """生成临时变量名"""
        self._temp_counter += 1
        return f"%{prefix}.{self._temp_counter}"

    def get_intrinsic_name(self, op_type: SIMDOpType) -> str:
        """获取操作的 intrinsic 名称"""
        arch_key = self._get_arch_key()
        inst_info = self._get_instruction_info(op_type, arch_key)
        return inst_info.intrinsic

    def supports_operation(self, op_type: SIMDOpType) -> bool:
        """检查是否支持指定操作"""
        arch_key = self._get_arch_key()
        table = self.instruction_table.get(arch_key, self.instruction_table["generic"])
        return op_type in table


def create_instruction_selector(
    target_arch: str = "generic",
    vector_width: int = 4,
) -> InstructionSelector:
    """
    创建指令选择器

    Args:
        target_arch: 目标架构
        vector_width: 向量宽度

    Returns:
        InstructionSelector 实例
    """
    return InstructionSelector(target_arch, vector_width)

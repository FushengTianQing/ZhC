# -*- coding: utf-8 -*-
"""
ZhC 指令选择器

从 LLVM IR 或中间表示选择目标机器指令。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from typing import List, Optional, Set, Any
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# 指令定义
# ============================================================================


class OpcodeClass(Enum):
    """指令类别"""

    ARITHMETIC = auto()  # 算术运算
    LOGICAL = auto()  # 逻辑运算
    MEMORY = auto()  # 内存操作
    CONTROL = auto()  # 控制流
    CONVERSION = auto()  # 类型转换
    COMPARISON = auto()  # 比较运算
    VECTOR = auto()  # 向量运算
    ATOMIC = auto()  # 原子操作
    OTHER = auto()  # 其他


class OperandType(Enum):
    """操作数类型"""

    REGISTER = auto()  # 寄存器
    IMMEDIATE = auto()  # 立即数
    MEMORY = auto()  # 内存地址
    LABEL = auto()  # 标签
    SYMBOL = auto()  # 符号


@dataclass
class Operand:
    """操作数"""

    type: OperandType
    value: Any  # 寄存器名、立即数值、内存地址等
    size: int = 64  # 操作数大小（位）

    def is_register(self) -> bool:
        return self.type == OperandType.REGISTER

    def is_immediate(self) -> bool:
        return self.type == OperandType.IMMEDIATE

    def is_memory(self) -> bool:
        return self.type == OperandType.MEMORY

    def __str__(self) -> str:
        if self.type == OperandType.REGISTER:
            return f"%{self.value}"
        elif self.type == OperandType.IMMEDIATE:
            return f"${self.value}"
        elif self.type == OperandType.MEMORY:
            return f"[{self.value}]"
        else:
            return str(self.value)


@dataclass
class MachineInstruction:
    """
    机器指令

    表示一条目标机器指令。
    """

    opcode: str  # 操作码名称
    operands: List[Operand] = field(default_factory=list)
    opcode_class: OpcodeClass = OpcodeClass.OTHER

    # 指令属性
    size: int = 0  # 指令大小（字节），0 表示未知
    is_branch: bool = False  # 是否为分支指令
    is_call: bool = False  # 是否为调用指令
    is_return: bool = False  # 是否为返回指令
    is_terminator: bool = False  # 是否为终止指令

    # 寄存器使用
    defs: Set[str] = field(default_factory=set)  # 定义的寄存器
    uses: Set[str] = field(default_factory=set)  # 使用的寄存器
    implicit_defs: Set[str] = field(default_factory=set)  # 隐式定义
    implicit_uses: Set[str] = field(default_factory=set)  # 隐式使用

    # 调试信息
    source_line: int = 0
    source_file: str = ""

    def __str__(self) -> str:
        ops = ", ".join(str(op) for op in self.operands)
        return f"{self.opcode} {ops}" if ops else self.opcode


# ============================================================================
# 指令选择 DAG 节点
# ============================================================================


class ISDOpcode(IntEnum):
    """ISD (Instruction Selection DAG) 操作码"""

    # 叶子节点
    Constant = 0
    Register = 1
    FrameIndex = 2
    GlobalAddress = 3
    ExternalSymbol = 4

    # 算术运算
    ADD = 10
    SUB = 11
    MUL = 12
    SDIV = 13  # 有符号除法
    UDIV = 14  # 无符号除法
    SREM = 15  # 有符号取余
    UREM = 16  # 无符号取余

    # 逻辑运算
    AND = 20
    OR = 21
    XOR = 22
    NOT = 23

    # 移位运算
    SHL = 30  # 左移
    SRL = 31  # 逻辑右移
    SRA = 32  # 算术右移

    # 比较运算
    SETCC = 40  # 设置条件码
    ICMP = 41  # 整数比较
    FCMP = 42  # 浮点比较

    # 内存操作
    LOAD = 50
    STORE = 51
    LOAD_ATOMIC = 52
    STORE_ATOMIC = 53

    # 控制流
    BR = 60  # 无条件分支
    BRCOND = 61  # 条件分支
    CALL = 62
    RET = 63
    SELECT = 64  # 条件选择

    # 类型转换
    TRUNCATE = 70
    ZERO_EXTEND = 71
    SIGN_EXTEND = 72
    FP_TO_SINT = 73
    FP_TO_UINT = 74
    SINT_TO_FP = 75
    UINT_TO_FP = 76

    # 其他
    COPY = 80
    COPY_TO_REG = 81
    COPY_FROM_REG = 82


@dataclass
class SDNode:
    """Selection DAG 节点"""

    opcode: ISDOpcode
    operands: List["SDNode"] = field(default_factory=list)
    result_type: str = "i64"  # 结果类型

    # 值（用于常量等）
    value: Any = None

    # 唯一标识
    id: int = 0

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        if isinstance(other, SDNode):
            return self.id == other.id
        return False


# ============================================================================
# 指令选择器基类
# ============================================================================


class InstructionSelector:
    """
    指令选择器基类

    从中间表示选择目标机器指令。

    子类需要实现：
    - select_instruction(): 为特定 DAG 节点选择指令
    - get_target_info(): 返回目标特定信息
    """

    def __init__(self, target_name: str = "generic"):
        """
        初始化指令选择器

        Args:
            target_name: 目标名称
        """
        self.target_name = target_name
        self._node_counter = 0
        self._selected_instructions: List[MachineInstruction] = []

    # =========================================================================
    # 指令选择主入口
    # =========================================================================

    def select(self, dag_nodes: List[SDNode]) -> List[MachineInstruction]:
        """
        选择指令

        Args:
            dag_nodes: DAG 节点列表

        Returns:
            选择的机器指令列表
        """
        self._selected_instructions = []

        for node in dag_nodes:
            self._select_node(node)

        return self._selected_instructions

    def _select_node(self, node: SDNode) -> Optional[MachineInstruction]:
        """为单个节点选择指令"""
        opcode = node.opcode

        # 分发到具体的选择方法
        if opcode == ISDOpcode.ADD:
            return self._select_add(node)
        elif opcode == ISDOpcode.SUB:
            return self._select_sub(node)
        elif opcode == ISDOpcode.MUL:
            return self._select_mul(node)
        elif opcode == ISDOpcode.LOAD:
            return self._select_load(node)
        elif opcode == ISDOpcode.STORE:
            return self._select_store(node)
        elif opcode == ISDOpcode.BR:
            return self._select_branch(node)
        elif opcode == ISDOpcode.BRCOND:
            return self._select_cond_branch(node)
        elif opcode == ISDOpcode.CALL:
            return self._select_call(node)
        elif opcode == ISDOpcode.RET:
            return self._select_return(node)
        elif opcode == ISDOpcode.Constant:
            return self._select_constant(node)
        elif opcode == ISDOpcode.Register:
            return self._select_register(node)
        else:
            logger.warning(f"Unhandled ISD opcode: {opcode}")
            return None

    # =========================================================================
    # 基本指令选择（子类可覆盖）
    # =========================================================================

    def _select_add(self, node: SDNode) -> MachineInstruction:
        """选择加法指令"""
        inst = MachineInstruction(
            opcode="ADD",
            opcode_class=OpcodeClass.ARITHMETIC,
            operands=[
                Operand(OperandType.REGISTER, "dst"),
                Operand(OperandType.REGISTER, "src1"),
                Operand(OperandType.REGISTER, "src2"),
            ],
        )
        self._selected_instructions.append(inst)
        return inst

    def _select_sub(self, node: SDNode) -> MachineInstruction:
        """选择减法指令"""
        inst = MachineInstruction(
            opcode="SUB",
            opcode_class=OpcodeClass.ARITHMETIC,
            operands=[
                Operand(OperandType.REGISTER, "dst"),
                Operand(OperandType.REGISTER, "src1"),
                Operand(OperandType.REGISTER, "src2"),
            ],
        )
        self._selected_instructions.append(inst)
        return inst

    def _select_mul(self, node: SDNode) -> MachineInstruction:
        """选择乘法指令"""
        inst = MachineInstruction(
            opcode="MUL",
            opcode_class=OpcodeClass.ARITHMETIC,
            operands=[
                Operand(OperandType.REGISTER, "dst"),
                Operand(OperandType.REGISTER, "src1"),
                Operand(OperandType.REGISTER, "src2"),
            ],
        )
        self._selected_instructions.append(inst)
        return inst

    def _select_load(self, node: SDNode) -> MachineInstruction:
        """选择加载指令"""
        inst = MachineInstruction(
            opcode="LOAD",
            opcode_class=OpcodeClass.MEMORY,
            operands=[
                Operand(OperandType.REGISTER, "dst"),
                Operand(OperandType.MEMORY, "addr"),
            ],
        )
        self._selected_instructions.append(inst)
        return inst

    def _select_store(self, node: SDNode) -> MachineInstruction:
        """选择存储指令"""
        inst = MachineInstruction(
            opcode="STORE",
            opcode_class=OpcodeClass.MEMORY,
            operands=[
                Operand(OperandType.REGISTER, "src"),
                Operand(OperandType.MEMORY, "addr"),
            ],
        )
        self._selected_instructions.append(inst)
        return inst

    def _select_branch(self, node: SDNode) -> MachineInstruction:
        """选择无条件分支指令"""
        inst = MachineInstruction(
            opcode="JMP",
            opcode_class=OpcodeClass.CONTROL,
            operands=[Operand(OperandType.LABEL, "target")],
            is_branch=True,
            is_terminator=True,
        )
        self._selected_instructions.append(inst)
        return inst

    def _select_cond_branch(self, node: SDNode) -> MachineInstruction:
        """选择条件分支指令"""
        inst = MachineInstruction(
            opcode="JCC",
            opcode_class=OpcodeClass.CONTROL,
            operands=[
                Operand(OperandType.REGISTER, "cond"),
                Operand(OperandType.LABEL, "true_target"),
                Operand(OperandType.LABEL, "false_target"),
            ],
            is_branch=True,
            is_terminator=True,
        )
        self._selected_instructions.append(inst)
        return inst

    def _select_call(self, node: SDNode) -> MachineInstruction:
        """选择调用指令"""
        inst = MachineInstruction(
            opcode="CALL",
            opcode_class=OpcodeClass.CONTROL,
            operands=[Operand(OperandType.SYMBOL, "callee")],
            is_call=True,
            implicit_defs={"rax", "rcx", "rdx", "r8", "r9", "r10", "r11"},
        )
        self._selected_instructions.append(inst)
        return inst

    def _select_return(self, node: SDNode) -> MachineInstruction:
        """选择返回指令"""
        inst = MachineInstruction(
            opcode="RET",
            opcode_class=OpcodeClass.CONTROL,
            operands=[],
            is_return=True,
            is_terminator=True,
        )
        self._selected_instructions.append(inst)
        return inst

    def _select_constant(self, node: SDNode) -> MachineInstruction:
        """选择常量加载指令"""
        inst = MachineInstruction(
            opcode="MOV",
            opcode_class=OpcodeClass.MEMORY,
            operands=[
                Operand(OperandType.REGISTER, "dst"),
                Operand(OperandType.IMMEDIATE, node.value),
            ],
        )
        self._selected_instructions.append(inst)
        return inst

    def _select_register(self, node: SDNode) -> MachineInstruction:
        """选择寄存器操作"""
        # 寄存器节点通常不需要生成指令
        return None

    # =========================================================================
    # 工具方法
    # =========================================================================

    def create_node(
        self, opcode: ISDOpcode, *operands: SDNode, value: Any = None
    ) -> SDNode:
        """
        创建 DAG 节点

        Args:
            opcode: 操作码
            operands: 操作数节点
            value: 值（用于常量等）

        Returns:
            创建的节点
        """
        self._node_counter += 1
        return SDNode(
            opcode=opcode,
            operands=list(operands),
            value=value,
            id=self._node_counter,
        )

    def get_selected_instructions(self) -> List[MachineInstruction]:
        """获取已选择的指令"""
        return self._selected_instructions.copy()

    def clear(self) -> None:
        """清空状态"""
        self._selected_instructions.clear()
        self._node_counter = 0


# ============================================================================
# x86_64 指令选择器
# ============================================================================


class X86_64InstructionSelector(InstructionSelector):
    """
    x86_64 指令选择器

    实现 x86_64 特定的指令选择逻辑。
    """

    # x86_64 寄存器
    REGISTERS_64 = [
        "rax",
        "rbx",
        "rcx",
        "rdx",
        "rsi",
        "rdi",
        "rbp",
        "rsp",
        "r8",
        "r9",
        "r10",
        "r11",
        "r12",
        "r13",
        "r14",
        "r15",
    ]
    REGISTERS_32 = [
        "eax",
        "ebx",
        "ecx",
        "edx",
        "esi",
        "edi",
        "ebp",
        "esp",
        "r8d",
        "r9d",
        "r10d",
        "r11d",
        "r12d",
        "r13d",
        "r14d",
        "r15d",
    ]

    def __init__(self):
        super().__init__(target_name="x86_64")

    def _select_add(self, node: SDNode) -> MachineInstruction:
        """选择 x86_64 加法指令"""
        # x86_64: ADD dst, src
        inst = MachineInstruction(
            opcode="ADD",
            opcode_class=OpcodeClass.ARITHMETIC,
            operands=[
                Operand(OperandType.REGISTER, "rax", size=64),
                Operand(OperandType.REGISTER, "rbx", size=64),
            ],
            defs={"rax"},
            uses={"rax", "rbx"},
        )
        self._selected_instructions.append(inst)
        return inst

    def _select_call(self, node: SDNode) -> MachineInstruction:
        """选择 x86_64 调用指令"""
        # x86_64: CALL target
        # System V AMD64 ABI: 参数在 rdi, rsi, rdx, rcx, r8, r9
        inst = MachineInstruction(
            opcode="CALL",
            opcode_class=OpcodeClass.CONTROL,
            operands=[Operand(OperandType.SYMBOL, "callee")],
            is_call=True,
            implicit_defs={"rax", "rcx", "rdx", "r8", "r9", "r10", "r11"},
            implicit_uses={"rsp"},
        )
        self._selected_instructions.append(inst)
        return inst

    def _select_return(self, node: SDNode) -> MachineInstruction:
        """选择 x86_64 返回指令"""
        # x86_64: RET
        inst = MachineInstruction(
            opcode="RET",
            opcode_class=OpcodeClass.CONTROL,
            operands=[],
            is_return=True,
            is_terminator=True,
            implicit_uses={"rsp"},
        )
        self._selected_instructions.append(inst)
        return inst


# ============================================================================
# AArch64 指令选择器
# ============================================================================


class AArch64InstructionSelector(InstructionSelector):
    """
    AArch64 指令选择器

    实现 AArch64 特定的指令选择逻辑。
    """

    # AArch64 寄存器
    REGISTERS_X = [f"x{i}" for i in range(31)] + ["sp"]
    REGISTERS_W = [f"w{i}" for i in range(31)]

    def __init__(self):
        super().__init__(target_name="aarch64")

    def _select_add(self, node: SDNode) -> MachineInstruction:
        """选择 AArch64 加法指令"""
        # AArch64: ADD Xd, Xn, Xm
        inst = MachineInstruction(
            opcode="ADD",
            opcode_class=OpcodeClass.ARITHMETIC,
            operands=[
                Operand(OperandType.REGISTER, "x0", size=64),
                Operand(OperandType.REGISTER, "x1", size=64),
                Operand(OperandType.REGISTER, "x2", size=64),
            ],
            defs={"x0"},
            uses={"x1", "x2"},
        )
        self._selected_instructions.append(inst)
        return inst

    def _select_call(self, node: SDNode) -> MachineInstruction:
        """选择 AArch64 调用指令"""
        # AArch64: BL target
        # AAPCS64: 参数在 x0-x7
        inst = MachineInstruction(
            opcode="BL",
            opcode_class=OpcodeClass.CONTROL,
            operands=[Operand(OperandType.SYMBOL, "callee")],
            is_call=True,
            implicit_defs={
                "x0",
                "x1",
                "x2",
                "x3",
                "x4",
                "x5",
                "x6",
                "x7",
                "x9",
                "x10",
                "x11",
                "x12",
                "x13",
                "x14",
                "x15",
            },
            implicit_uses={"sp"},
        )
        self._selected_instructions.append(inst)
        return inst

    def _select_return(self, node: SDNode) -> MachineInstruction:
        """选择 AArch64 返回指令"""
        # AArch64: RET
        inst = MachineInstruction(
            opcode="RET",
            opcode_class=OpcodeClass.CONTROL,
            operands=[],
            is_return=True,
            is_terminator=True,
            implicit_uses={"x30", "sp"},  # x30 = lr
        )
        self._selected_instructions.append(inst)
        return inst


# ============================================================================
# 工厂函数
# ============================================================================


def create_instruction_selector(target: str) -> InstructionSelector:
    """
    创建指令选择器

    Args:
        target: 目标名称

    Returns:
        指令选择器实例
    """
    selectors = {
        "x86_64": X86_64InstructionSelector,
        "x86-64": X86_64InstructionSelector,
        "aarch64": AArch64InstructionSelector,
        "arm64": AArch64InstructionSelector,
    }

    selector_class = selectors.get(target.lower(), InstructionSelector)
    return selector_class()

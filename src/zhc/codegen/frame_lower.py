# -*- coding: utf-8 -*-
"""
ZhC 栈帧 Lowering

管理函数栈帧布局，包括局部变量、溢出槽、调用参数等。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# 栈帧槽类型
# ============================================================================


class SlotType(Enum):
    """栈帧槽类型"""

    LOCAL = auto()  # 局部变量
    SPILL = auto()  # 寄存器溢出
    OUTGOING = auto()  # 传出参数
    INCOMING = auto()  # 传入参数
    SAVED_REG = auto()  # 保存的寄存器
    TEMP = auto()  # 临时变量
    ALLOCA = auto()  # 动态分配


@dataclass
class StackSlot:
    """栈帧槽"""

    index: int  # 槽索引
    type: SlotType  # 类型
    size: int  # 大小（字节）
    alignment: int  # 对齐要求

    # 位置信息
    offset: int = 0  # 相对于帧指针的偏移

    # 关联信息
    vreg_id: Optional[int] = None  # 关联的虚拟寄存器
    name: Optional[str] = None  # 变量名（用于调试）

    def __str__(self) -> str:
        return f"slot[{self.index}]: {self.type.name} ({self.size}B @ {self.offset})"


# ============================================================================
# 栈帧描述
# ============================================================================


@dataclass
class StackFrame:
    """
    函数栈帧描述

    包含函数的所有栈帧信息。
    """

    function_name: str  # 函数名

    # 栈帧大小
    local_size: int = 0  # 局部变量大小
    outgoing_size: int = 0  # 传出参数大小
    saved_reg_size: int = 0  # 保存寄存器大小
    total_size: int = 0  # 总大小

    # 对齐
    alignment: int = 16  # 栈帧对齐

    # 槽
    slots: List[StackSlot] = field(default_factory=list)
    slot_map: Dict[int, StackSlot] = field(default_factory=dict)  # vreg_id -> slot

    # 保存的寄存器
    saved_regs: Set[str] = field(default_factory=set)

    # 参数信息
    arg_count: int = 0  # 参数数量
    stack_arg_offset: int = 0  # 栈上参数起始偏移

    # 属性
    has_varargs: bool = False  # 是否有可变参数
    has_alloca: bool = False  # 是否有动态分配

    def add_slot(
        self,
        type: SlotType,
        size: int,
        alignment: int = 8,
        vreg_id: Optional[int] = None,
        name: Optional[str] = None,
    ) -> StackSlot:
        """
        添加栈帧槽

        Args:
            type: 槽类型
            size: 大小
            alignment: 对齐
            vreg_id: 关联的虚拟寄存器
            name: 变量名

        Returns:
            创建的槽
        """
        slot = StackSlot(
            index=len(self.slots),
            type=type,
            size=size,
            alignment=alignment,
            vreg_id=vreg_id,
            name=name,
        )
        self.slots.append(slot)

        if vreg_id is not None:
            self.slot_map[vreg_id] = slot

        return slot

    def get_slot(self, vreg_id: int) -> Optional[StackSlot]:
        """获取虚拟寄存器对应的槽"""
        return self.slot_map.get(vreg_id)

    def get_local_slots(self) -> List[StackSlot]:
        """获取所有局部变量槽"""
        return [s for s in self.slots if s.type == SlotType.LOCAL]

    def get_spill_slots(self) -> List[StackSlot]:
        """获取所有溢出槽"""
        return [s for s in self.slots if s.type == SlotType.SPILL]

    def __str__(self) -> str:
        lines = [f"StackFrame({self.function_name}):"]
        lines.append(f"  Total size: {self.total_size} bytes")
        lines.append(f"  Alignment: {self.alignment}")
        lines.append(f"  Saved regs: {', '.join(self.saved_regs) or 'none'}")
        if self.slots:
            lines.append("  Slots:")
            for slot in self.slots:
                lines.append(f"    {slot}")
        return "\n".join(lines)


@dataclass
class FrameInfo:
    """
    帧信息（测试兼容类）

    提供测试期望的接口：name, return_type, params。
    """

    name: str  # 函数名（无默认值）
    params: List[Tuple[str, str]] = field(
        default_factory=list
    )  # 参数列表 [(type, name), ...]
    return_type: str = "void"  # 返回类型

    def __post_init__(self):
        # 确保 params 是列表
        if not isinstance(self.params, list):
            object.__setattr__(self, "params", list(self.params))


# ============================================================================
# 栈帧 Lowering 基类
# ============================================================================


class FrameLowering:
    """
    栈帧 Lowering 基类

    计算和管理函数栈帧布局。

    子类需要实现目标特定的布局规则。
    """

    def __init__(self, stack_alignment: int = 16):
        """
        初始化栈帧 Lowering

        Args:
            stack_alignment: 栈对齐要求
        """
        self.stack_alignment = stack_alignment

    # =========================================================================
    # 栈帧布局
    # =========================================================================

    def layout_frame(self, frame: StackFrame) -> None:
        """
        计算栈帧布局

        Args:
            frame: 栈帧描述
        """
        # 1. 计算各部分大小
        self._compute_sizes(frame)

        # 2. 分配槽偏移
        self._assign_offsets(frame)

        # 3. 计算总大小
        self._compute_total_size(frame)

    def _compute_sizes(self, frame: StackFrame) -> None:
        """计算各部分大小"""
        # 局部变量和溢出槽
        local_size = 0
        for slot in frame.slots:
            if slot.type in (SlotType.LOCAL, SlotType.SPILL, SlotType.TEMP):
                local_size += self._align(slot.size, slot.alignment)

        frame.local_size = local_size

        # 保存寄存器
        frame.saved_reg_size = len(frame.saved_regs) * 8  # 假设 64 位

    def _assign_offsets(self, frame: StackFrame) -> None:
        """分配槽偏移"""
        # 从帧指针向下分配
        current_offset = 0

        # 1. 保存的寄存器（靠近帧指针）
        for reg in frame.saved_regs:
            current_offset -= 8  # 64 位寄存器

        # 2. 局部变量和溢出槽
        for slot in frame.slots:
            if slot.type in (SlotType.LOCAL, SlotType.SPILL, SlotType.TEMP):
                # 对齐
                current_offset = self._align_down(
                    current_offset - slot.size, slot.alignment
                )
                slot.offset = current_offset

        # 3. 传出参数
        outgoing_offset = 0
        for slot in frame.slots:
            if slot.type == SlotType.OUTGOING:
                slot.offset = outgoing_offset
                outgoing_offset += self._align(slot.size, slot.alignment)

        frame.outgoing_size = outgoing_offset

    def _compute_total_size(self, frame: StackFrame) -> None:
        """计算总大小"""
        # 总大小 = 局部变量 + 保存寄存器 + 对齐填充
        total = abs(frame.local_size) + frame.saved_reg_size

        # 对齐到栈对齐要求
        frame.total_size = self._align(total, self.stack_alignment)

    # =========================================================================
    # Prologue/Epilogue 生成
    # =========================================================================

    def emit_prologue(self, frame: StackFrame) -> List[str]:
        """
        生成函数序言

        Args:
            frame: 栈帧描述

        Returns:
            指令列表（字符串形式）
        """
        raise NotImplementedError("Subclass must implement emit_prologue()")

    def emit_epilogue(self, frame: StackFrame) -> List[str]:
        """
        生成函数尾声

        Args:
            frame: 栈帧描述

        Returns:
            指令列表（字符串形式）
        """
        raise NotImplementedError("Subclass must implement emit_epilogue()")

    # =========================================================================
    # 工具方法
    # =========================================================================

    def _align(self, size: int, alignment: int) -> int:
        """向上对齐"""
        return (size + alignment - 1) // alignment * alignment

    def _align_down(self, size: int, alignment: int) -> int:
        """向下对齐"""
        return size // alignment * alignment


# ============================================================================
# x86_64 栈帧 Lowering
# ============================================================================


class X86_64FrameLowering(FrameLowering):
    """
    x86_64 栈帧 Lowering

    实现 System V AMD64 ABI 的栈帧布局。
    """

    # callee-saved 寄存器
    CALLEE_SAVED = {"rbx", "r12", "r13", "r14", "r15"}

    # 参数寄存器
    ARG_REGS = ["rdi", "rsi", "rdx", "rcx", "r8", "r9"]

    def __init__(self):
        super().__init__(stack_alignment=16)

    def emit_prologue(self, frame: StackFrame) -> List[str]:
        """生成 x86_64 函数序言"""
        insts = []

        # push rbp
        insts.append("pushq %rbp")

        # mov rbp, rsp
        insts.append("movq %rsp, %rbp")

        # 分配栈空间
        if frame.total_size > 0:
            insts.append(f"subq ${frame.total_size}, %rsp")

        # 保存 callee-saved 寄存器
        for reg in sorted(frame.saved_regs):
            if reg in self.CALLEE_SAVED:
                insts.append(f"pushq %{reg}")

        return insts

    def emit_epilogue(self, frame: StackFrame) -> List[str]:
        """生成 x86_64 函数尾声"""
        insts = []

        # 恢复 callee-saved 寄存器
        for reg in sorted(frame.saved_regs, reverse=True):
            if reg in self.CALLEE_SAVED:
                insts.append(f"popq %{reg}")

        # 释放栈空间
        if frame.total_size > 0:
            insts.append(f"addq ${frame.total_size}, %rsp")

        # pop rbp
        insts.append("popq %rbp")

        # ret
        insts.append("retq")

        return insts

    def get_arg_register(self, arg_index: int) -> Optional[str]:
        """获取参数寄存器"""
        if arg_index < len(self.ARG_REGS):
            return self.ARG_REGS[arg_index]
        return None


# ============================================================================
# AArch64 栈帧 Lowering
# ============================================================================


class AArch64FrameLowering(FrameLowering):
    """
    AArch64 栈帧 Lowering

    实现 AAPCS64 ABI 的栈帧布局。
    """

    # callee-saved 寄存器
    CALLEE_SAVED = {
        "x19",
        "x20",
        "x21",
        "x22",
        "x23",
        "x24",
        "x25",
        "x26",
        "x27",
        "x28",
    }

    # 参数寄存器
    ARG_REGS = ["x0", "x1", "x2", "x3", "x4", "x5", "x6", "x7"]

    def __init__(self):
        super().__init__(stack_alignment=16)

    def emit_prologue(self, frame: StackFrame) -> List[str]:
        """生成 AArch64 函数序言"""
        insts = []

        # stp x29, x30, [sp, #-16]!
        insts.append("stp x29, x30, [sp, #-16]!")

        # mov x29, sp
        insts.append("mov x29, sp")

        # 分配栈空间
        if frame.total_size > 0:
            insts.append(f"sub sp, sp, #{frame.total_size}")

        # 保存 callee-saved 寄存器
        saved_list = sorted([r for r in frame.saved_regs if r in self.CALLEE_SAVED])
        for i in range(0, len(saved_list), 2):
            if i + 1 < len(saved_list):
                insts.append(
                    f"stp {saved_list[i]}, {saved_list[i+1]}, [sp, #-{(i//2+1)*16}]!"
                )
            else:
                insts.append(f"str {saved_list[i]}, [sp, #-{(i//2+1)*16}]!")

        return insts

    def emit_epilogue(self, frame: StackFrame) -> List[str]:
        """生成 AArch64 函数尾声"""
        insts = []

        # 恢复 callee-saved 寄存器
        saved_list = sorted(
            [r for r in frame.saved_regs if r in self.CALLEE_SAVED], reverse=True
        )
        for i in range(0, len(saved_list), 2):
            if i + 1 < len(saved_list):
                insts.append(f"ldp {saved_list[i]}, {saved_list[i+1]}, [sp], #16")
            else:
                insts.append(f"ldr {saved_list[i]}, [sp], #16")

        # 释放栈空间
        if frame.total_size > 0:
            insts.append(f"add sp, sp, #{frame.total_size}")

        # ldp x29, x30, [sp], #16
        insts.append("ldp x29, x30, [sp], #16")

        # ret
        insts.append("ret")

        return insts

    def get_arg_register(self, arg_index: int) -> Optional[str]:
        """获取参数寄存器"""
        if arg_index < len(self.ARG_REGS):
            return self.ARG_REGS[arg_index]
        return None


# ============================================================================
# 工厂函数
# ============================================================================


def create_frame_lowering(target: str) -> FrameLowering:
    """
    创建栈帧 Lowering

    Args:
        target: 目标名称

    Returns:
        栈帧 Lowering 实例
    """
    lowering_map = {
        "x86_64": X86_64FrameLowering,
        "x86-64": X86_64FrameLowering,
        "aarch64": AArch64FrameLowering,
        "arm64": AArch64FrameLowering,
    }

    lowering_class = lowering_map.get(target.lower(), FrameLowering)
    return lowering_class()


def create_stack_frame(function_name: str) -> StackFrame:
    """
    创建栈帧描述

    Args:
        function_name: 函数名

    Returns:
        栈帧描述实例
    """
    return StackFrame(function_name=function_name)


# ============================================================================
# 别名：测试兼容
# ============================================================================

# 类别名
FrameLower = FrameLowering

# StackLayout - 测试期望的类（目前作为 StackFrame 的别名）
StackLayout = StackFrame

# 工厂函数别名
create_frame_lower = create_frame_lowering

# -*- coding: utf-8 -*-
"""
ZhC 寄存器分配器

实现寄存器分配算法，将虚拟寄存器映射到物理寄存器。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# 寄存器定义
# ============================================================================


class RegisterClass(Enum):
    """寄存器类"""

    GENERAL = auto()  # 通用寄存器
    FLOAT = auto()  # 浮点寄存器
    VECTOR = auto()  # 向量寄存器
    SPECIAL = auto()  # 特殊寄存器


@dataclass
class Register:
    """寄存器描述"""

    name: str  # 寄存器名称
    class_: RegisterClass  # 寄存器类
    size: int = 64  # 大小（位）
    aliases: List[str] = field(default_factory=list)  # 别名

    # 属性
    is_allocatable: bool = True  # 是否可分配
    is_callee_saved: bool = False  # 是否为 callee-saved
    is_reserved: bool = False  # 是否保留

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, Register):
            return self.name == other.name
        return False

    def __str__(self) -> str:
        return f"%{self.name}"


@dataclass
class VirtualRegister:
    """虚拟寄存器"""

    id: int  # 虚拟寄存器 ID
    class_: RegisterClass  # 寄存器类
    size: int = 64  # 大小

    # 分配信息（由分配器设置）
    physical_reg: Optional[str] = None  # 分配的物理寄存器
    spill_slot: Optional[int] = None  # 溢出槽索引

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        if isinstance(other, VirtualRegister):
            return self.id == other.id
        return False

    def __str__(self) -> str:
        return f"v{self.id}"

    @property
    def is_allocated(self) -> bool:
        return self.physical_reg is not None

    @property
    def is_spilled(self) -> bool:
        return self.spill_slot is not None


# ============================================================================
# 活跃区间
# ============================================================================


@dataclass
class LiveInterval:
    """
    活跃区间

    表示一个虚拟寄存器的活跃范围。
    """

    vreg: VirtualRegister  # 虚拟寄存器
    start: int  # 起始位置（指令编号）
    end: int  # 结束位置

    # 分配信息
    physical_reg: Optional[str] = None
    spill_slot: Optional[int] = None

    def __str__(self) -> str:
        return f"{self.vreg}: [{self.start}, {self.end}]"

    def overlaps(self, other: "LiveInterval") -> bool:
        """检查是否与另一个区间重叠"""
        return not (self.end < other.start or other.end < self.start)

    def contains(self, pos: int) -> bool:
        """检查位置是否在区间内"""
        return self.start <= pos <= self.end


# ============================================================================
# 栈帧槽
# ============================================================================


@dataclass
class SpillSlot:
    """溢出槽"""

    index: int  # 槽索引
    size: int  # 大小（字节）
    offset: int = 0  # 栈帧偏移（由栈帧管理器设置）

    def __str__(self) -> str:
        return f"spill[{self.index}]"


# ============================================================================
# 寄存器分配器基类
# ============================================================================


class RegisterAllocator:
    """
    寄存器分配器基类

    子类需要实现具体的分配算法。
    """

    def __init__(self, registers: List[Register]):
        """
        初始化寄存器分配器

        Args:
            registers: 可用的物理寄存器列表
        """
        self.registers = {r.name: r for r in registers}
        self.vregs: Dict[int, VirtualRegister] = {}
        self.intervals: List[LiveInterval] = []
        self.spill_slots: List[SpillSlot] = []

        # 分配状态
        self._allocated: Dict[int, str] = {}  # vreg_id -> phys_reg
        self._spilled: Dict[int, int] = {}  # vreg_id -> spill_slot
        self._reg_free: Dict[str, bool] = {r: True for r in self.registers}

    # =========================================================================
    # 寄存器管理
    # =========================================================================

    def create_vreg(
        self, class_: RegisterClass = RegisterClass.GENERAL, size: int = 64
    ) -> VirtualRegister:
        """
        创建虚拟寄存器

        Args:
            class_: 寄存器类
            size: 大小

        Returns:
            创建的虚拟寄存器
        """
        vreg_id = len(self.vregs)
        vreg = VirtualRegister(id=vreg_id, class_=class_, size=size)
        self.vregs[vreg_id] = vreg
        return vreg

    def get_vreg(self, vreg_id: int) -> Optional[VirtualRegister]:
        """获取虚拟寄存器"""
        return self.vregs.get(vreg_id)

    def add_live_interval(
        self, vreg: VirtualRegister, start: int, end: int
    ) -> LiveInterval:
        """
        添加活跃区间

        Args:
            vreg: 虚拟寄存器
            start: 起始位置
            end: 结束位置

        Returns:
            创建的活跃区间
        """
        interval = LiveInterval(vreg=vreg, start=start, end=end)
        self.intervals.append(interval)
        return interval

    # =========================================================================
    # 分配接口（子类实现）
    # =========================================================================

    def allocate(self) -> bool:
        """
        执行寄存器分配

        Returns:
            是否成功分配（无溢出）
        """
        raise NotImplementedError("Subclass must implement allocate()")

    # =========================================================================
    # 工具方法
    # =========================================================================

    def get_allocatable_registers(self, class_: RegisterClass) -> List[str]:
        """获取可分配的寄存器"""
        return [
            name
            for name, reg in self.registers.items()
            if reg.class_ == class_ and reg.is_allocatable and not reg.is_reserved
        ]

    def is_register_free(self, reg_name: str) -> bool:
        """检查寄存器是否空闲"""
        return self._reg_free.get(reg_name, False)

    def mark_register_used(self, reg_name: str) -> None:
        """标记寄存器为已使用"""
        self._reg_free[reg_name] = False

    def mark_register_free(self, reg_name: str) -> None:
        """标记寄存器为空闲"""
        self._reg_free[reg_name] = True

    def allocate_spill_slot(self, size: int) -> SpillSlot:
        """分配溢出槽"""
        slot = SpillSlot(index=len(self.spill_slots), size=size)
        self.spill_slots.append(slot)
        return slot

    def get_assignment(self, vreg_id: int) -> Optional[str]:
        """获取虚拟寄存器的物理寄存器分配"""
        return self._allocated.get(vreg_id)

    def get_spill_slot(self, vreg_id: int) -> Optional[int]:
        """获取虚拟寄存器的溢出槽"""
        return self._spilled.get(vreg_id)

    def clear(self) -> None:
        """清空分配状态"""
        self.vregs.clear()
        self.intervals.clear()
        self.spill_slots.clear()
        self._allocated.clear()
        self._spilled.clear()
        self._reg_free = {r: True for r in self.registers}


# ============================================================================
# 线性扫描寄存器分配器
# ============================================================================


class LinearScanRegisterAllocator(RegisterAllocator):
    """
    线性扫描寄存器分配器

    使用线性扫描算法进行快速寄存器分配。
    时间复杂度：O(n log n)
    """

    def __init__(self, registers: List[Register]):
        super().__init__(registers)
        self._active: List[LiveInterval] = []  # 当前活跃的区间
        self._inactive: List[LiveInterval] = []  # 非活跃区间

    def allocate(self) -> bool:
        """
        执行线性扫描分配

        Returns:
            是否成功分配（无溢出）
        """
        # 按起始位置排序
        sorted_intervals = sorted(self.intervals, key=lambda i: i.start)

        for interval in sorted_intervals:
            # 过期旧的活跃区间
            self._expire_old_intervals(interval)

            # 尝试分配空闲寄存器
            reg = self._try_allocate_register(interval)

            if reg:
                interval.physical_reg = reg
                self._allocated[interval.vreg.id] = reg
                self._active.append(interval)
            else:
                # 需要溢出
                self._spill_interval(interval)

        return len(self._spilled) == 0

    def _expire_old_intervals(self, current: LiveInterval) -> None:
        """使过期的区间失效"""
        new_active = []
        for interval in self._active:
            if interval.end < current.start:
                # 区间已过期，释放寄存器
                if interval.physical_reg:
                    self.mark_register_free(interval.physical_reg)
            else:
                new_active.append(interval)
        self._active = new_active

    def _try_allocate_register(self, interval: LiveInterval) -> Optional[str]:
        """尝试为区间分配寄存器"""
        allocatable = self.get_allocatable_registers(interval.vreg.class_)

        for reg_name in allocatable:
            if self.is_register_free(reg_name):
                self.mark_register_used(reg_name)
                return reg_name

        return None

    def _spill_interval(self, interval: LiveInterval) -> None:
        """溢出一个区间"""
        # 选择一个区间溢出（简化：选择当前区间）
        # 更好的实现会选择溢出代价最小的区间

        # 分配溢出槽
        slot = self.allocate_spill_slot(interval.vreg.size // 8)
        interval.spill_slot = slot.index
        self._spilled[interval.vreg.id] = slot.index
        interval.vreg.spill_slot = slot.index

        logger.debug(f"Spilled {interval.vreg} to slot {slot.index}")


# ============================================================================
# 图着色寄存器分配器
# ============================================================================


class GraphColoringRegisterAllocator(RegisterAllocator):
    """
    图着色寄存器分配器

    使用干涉图着色算法进行寄存器分配。
    通常能产生比线性扫描更好的结果，但速度较慢。
    """

    def __init__(self, registers: List[Register]):
        super().__init__(registers)
        self._interference_graph: Dict[int, Set[int]] = {}  # vreg_id -> 冲突的 vreg_ids

    def allocate(self) -> bool:
        """
        执行图着色分配

        Returns:
            是否成功分配
        """
        # 1. 构建干涉图
        self._build_interference_graph()

        # 2. 简化和溢出
        stack = self._simplify_and_spill()

        # 3. 选择和分配
        return self._select_and_assign(stack)

    def _build_interference_graph(self) -> None:
        """构建干涉图"""
        # 初始化
        for vreg_id in self.vregs:
            self._interference_graph[vreg_id] = set()

        # 检查所有区间对
        for i, interval_a in enumerate(self.intervals):
            for interval_b in self.intervals[i + 1 :]:
                if interval_a.overlaps(interval_b):
                    self._interference_graph[interval_a.vreg.id].add(interval_b.vreg.id)
                    self._interference_graph[interval_b.vreg.id].add(interval_a.vreg.id)

    def _simplify_and_spill(self) -> List[int]:
        """
        简化并选择溢出节点

        Returns:
            简化栈（节点 ID 列表）
        """
        # 获取每个寄存器类的可用颜色数
        colors = {
            RegisterClass.GENERAL: len(
                self.get_allocatable_registers(RegisterClass.GENERAL)
            ),
            RegisterClass.FLOAT: len(
                self.get_allocatable_registers(RegisterClass.FLOAT)
            ),
        }

        # 复制干涉图
        remaining = set(self.vregs.keys())
        graph = {k: v.copy() for k, v in self._interference_graph.items()}
        stack = []

        while remaining:
            # 找一个度数小于 K 的节点
            found = False
            for vreg_id in list(remaining):
                degree = len(graph.get(vreg_id, set()))
                vreg = self.vregs[vreg_id]
                k = colors.get(vreg.class_, 0)

                if degree < k:
                    # 可以简化
                    stack.append(vreg_id)
                    remaining.remove(vreg_id)
                    # 从图中移除
                    for neighbor in graph.get(vreg_id, set()):
                        graph[neighbor].discard(vreg_id)
                    found = True
                    break

            if not found:
                # 所有节点度数 >= K，需要溢出
                # 选择溢出代价最小的节点（简化：选择第一个）
                spill_candidate = next(iter(remaining))
                stack.append(spill_candidate)
                remaining.remove(spill_candidate)
                # 从图中移除
                for neighbor in graph.get(spill_candidate, set()):
                    graph[neighbor].discard(spill_candidate)

        return stack

    def _select_and_assign(self, stack: List[int]) -> bool:
        """从栈中选择颜色并分配"""
        colors = {
            RegisterClass.GENERAL: self.get_allocatable_registers(
                RegisterClass.GENERAL
            ),
            RegisterClass.FLOAT: self.get_allocatable_registers(RegisterClass.FLOAT),
        }

        success = True

        # 反向遍历栈
        for vreg_id in reversed(stack):
            vreg = self.vregs[vreg_id]
            reg_class = vreg.class_
            available = colors.get(reg_class, [])

            # 找到邻居已使用的颜色
            used = set()
            for neighbor_id in self._interference_graph.get(vreg_id, set()):
                if neighbor_id in self._allocated:
                    used.add(self._allocated[neighbor_id])

            # 找一个可用颜色
            for reg in available:
                if reg not in used:
                    self._allocated[vreg_id] = reg
                    vreg.physical_reg = reg
                    break
            else:
                # 没有可用颜色，溢出
                slot = self.allocate_spill_slot(vreg.size // 8)
                self._spilled[vreg_id] = slot.index
                vreg.spill_slot = slot.index
                success = False

        return success


# ============================================================================
# 目标特定寄存器配置
# ============================================================================


def create_x86_64_registers() -> List[Register]:
    """创建 x86_64 寄存器列表"""
    return [
        # 通用寄存器
        Register("rax", RegisterClass.GENERAL, 64, aliases=["eax", "ax", "al"]),
        Register(
            "rbx",
            RegisterClass.GENERAL,
            64,
            aliases=["ebx", "bx", "bl"],
            is_callee_saved=True,
        ),
        Register("rcx", RegisterClass.GENERAL, 64, aliases=["ecx", "cx", "cl"]),
        Register("rdx", RegisterClass.GENERAL, 64, aliases=["edx", "dx", "dl"]),
        Register("rsi", RegisterClass.GENERAL, 64, aliases=["esi", "si", "sil"]),
        Register("rdi", RegisterClass.GENERAL, 64, aliases=["edi", "di", "dil"]),
        Register(
            "rbp",
            RegisterClass.GENERAL,
            64,
            aliases=["ebp", "bp", "bpl"],
            is_callee_saved=True,
            is_reserved=True,
        ),
        Register(
            "rsp",
            RegisterClass.GENERAL,
            64,
            aliases=["esp", "sp", "spl"],
            is_reserved=True,
        ),
        Register("r8", RegisterClass.GENERAL, 64, aliases=["r8d", "r8w", "r8b"]),
        Register("r9", RegisterClass.GENERAL, 64, aliases=["r9d", "r9w", "r9b"]),
        Register("r10", RegisterClass.GENERAL, 64, aliases=["r10d", "r10w", "r10b"]),
        Register("r11", RegisterClass.GENERAL, 64, aliases=["r11d", "r11w", "r11b"]),
        Register(
            "r12",
            RegisterClass.GENERAL,
            64,
            aliases=["r12d", "r12w", "r12b"],
            is_callee_saved=True,
        ),
        Register(
            "r13",
            RegisterClass.GENERAL,
            64,
            aliases=["r13d", "r13w", "r13b"],
            is_callee_saved=True,
        ),
        Register(
            "r14",
            RegisterClass.GENERAL,
            64,
            aliases=["r14d", "r14w", "r14b"],
            is_callee_saved=True,
        ),
        Register(
            "r15",
            RegisterClass.GENERAL,
            64,
            aliases=["r15d", "r15w", "r15b"],
            is_callee_saved=True,
        ),
        # 向量寄存器（XMM）
        *[Register(f"xmm{i}", RegisterClass.FLOAT, 128) for i in range(16)],
    ]


def create_aarch64_registers() -> List[Register]:
    """创建 AArch64 寄存器列表"""
    return [
        # 通用寄存器（X 系列）
        Register("x0", RegisterClass.GENERAL, 64, aliases=["w0"]),
        Register("x1", RegisterClass.GENERAL, 64, aliases=["w1"]),
        Register("x2", RegisterClass.GENERAL, 64, aliases=["w2"]),
        Register("x3", RegisterClass.GENERAL, 64, aliases=["w3"]),
        Register("x4", RegisterClass.GENERAL, 64, aliases=["w4"]),
        Register("x5", RegisterClass.GENERAL, 64, aliases=["w5"]),
        Register("x6", RegisterClass.GENERAL, 64, aliases=["w6"]),
        Register("x7", RegisterClass.GENERAL, 64, aliases=["w7"]),
        Register("x8", RegisterClass.GENERAL, 64, aliases=["w8"]),
        Register("x9", RegisterClass.GENERAL, 64, aliases=["w9"]),
        Register("x10", RegisterClass.GENERAL, 64, aliases=["w10"]),
        Register("x11", RegisterClass.GENERAL, 64, aliases=["w11"]),
        Register("x12", RegisterClass.GENERAL, 64, aliases=["w12"]),
        Register("x13", RegisterClass.GENERAL, 64, aliases=["w13"]),
        Register("x14", RegisterClass.GENERAL, 64, aliases=["w14"]),
        Register("x15", RegisterClass.GENERAL, 64, aliases=["w15"]),
        Register("x16", RegisterClass.GENERAL, 64, aliases=["w16"]),  # IP0
        Register("x17", RegisterClass.GENERAL, 64, aliases=["w17"]),  # IP1
        Register("x18", RegisterClass.GENERAL, 64, aliases=["w18"]),  # 平台寄存器
        Register(
            "x19", RegisterClass.GENERAL, 64, aliases=["w19"], is_callee_saved=True
        ),
        Register(
            "x20", RegisterClass.GENERAL, 64, aliases=["w20"], is_callee_saved=True
        ),
        Register(
            "x21", RegisterClass.GENERAL, 64, aliases=["w21"], is_callee_saved=True
        ),
        Register(
            "x22", RegisterClass.GENERAL, 64, aliases=["w22"], is_callee_saved=True
        ),
        Register(
            "x23", RegisterClass.GENERAL, 64, aliases=["w23"], is_callee_saved=True
        ),
        Register(
            "x24", RegisterClass.GENERAL, 64, aliases=["w24"], is_callee_saved=True
        ),
        Register(
            "x25", RegisterClass.GENERAL, 64, aliases=["w25"], is_callee_saved=True
        ),
        Register(
            "x26", RegisterClass.GENERAL, 64, aliases=["w26"], is_callee_saved=True
        ),
        Register(
            "x27", RegisterClass.GENERAL, 64, aliases=["w27"], is_callee_saved=True
        ),
        Register(
            "x28", RegisterClass.GENERAL, 64, aliases=["w28"], is_callee_saved=True
        ),
        Register(
            "x29",
            RegisterClass.GENERAL,
            64,
            aliases=["w29"],
            is_callee_saved=True,
            is_reserved=True,
        ),  # FP
        Register("x30", RegisterClass.GENERAL, 64, is_reserved=True),  # LR
        Register("sp", RegisterClass.GENERAL, 64, is_reserved=True),  # SP
        # 向量寄存器（V 系列）
        *[
            Register(f"v{i}", RegisterClass.FLOAT, 128, aliases=[f"d{i}", f"s{i}"])
            for i in range(32)
        ],
    ]


# ============================================================================
# 工厂函数
# ============================================================================


def create_register_allocator(
    target: str, algorithm: str = "linear_scan"
) -> RegisterAllocator:
    """
    创建寄存器分配器

    Args:
        target: 目标名称
        algorithm: 算法名称（"linear_scan" 或 "graph_coloring"）

    Returns:
        寄存器分配器实例
    """
    # 获取目标寄存器
    registers_map = {
        "x86_64": create_x86_64_registers,
        "x86-64": create_x86_64_registers,
        "aarch64": create_aarch64_registers,
        "arm64": create_aarch64_registers,
    }

    registers_fn = registers_map.get(target.lower(), create_x86_64_registers)
    registers = registers_fn()

    # 选择算法
    if algorithm == "graph_coloring":
        return GraphColoringRegisterAllocator(registers)
    else:
        return LinearScanRegisterAllocator(registers)

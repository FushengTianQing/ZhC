#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
寄存器分配器 - Register Allocator

功能：
1. 线性扫描寄存器分配算法
2. 活跃区间分析
3. 溢出处理
4. 寄存器映射

算法：线性扫描 (Linear Scan)
- 复杂度: O(n log n)
- 策略: 按活跃区间起点排序，贪心分配寄存器

作者：阿福
日期：2026-04-08
"""

from typing import Dict, List, Set, Optional, Tuple, NamedTuple
from dataclasses import dataclass, field
from enum import Enum


class RegisterKind(Enum):
    """寄存器类型"""
    INTEGER = "整数"
    FLOAT = "浮点"
    POINTER = "指针"
    ANY = "任意"


@dataclass
class Register:
    """物理寄存器"""
    name: str           # 寄存器名称（如 "eax", "r8"）
    kind: RegisterKind  # 寄存器类型
    caller_saved: bool  # 调用者保存
    callee_saved: bool  # 被调用者保存
    index: int          # 寄存器编号
    occupied: bool = False  # 是否被占用
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        if isinstance(other, Register):
            return self.name == other.name
        return False


@dataclass
class VirtualRegister:
    """虚拟寄存器"""
    id: int             # 虚拟寄存器ID
    name: str           # 名称（如 "v0", "v1"）
    kind: RegisterKind  # 类型
    spilled: bool = False  # 是否被溢出到内存
    spill_slot: Optional[int] = None  # 溢出槽编号
    assigned: Optional[Register] = None  # 分配的物理寄存器
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, VirtualRegister):
            return self.id == other.id
        return False


@dataclass
class LiveInterval:
    """活跃区间"""
    virtual_reg: VirtualRegister
    start: int          # 区间起点（指令编号）
    end: int            # 区间终点
    uses: List[int] = field(default_factory=list)  # 使用位置列表
    
    def overlaps(self, other: 'LiveInterval') -> bool:
        """检查两个区间是否重叠"""
        return not (self.end <= other.start or other.end <= self.start)
    
    def __lt__(self, other: 'LiveInterval') -> bool:
        """按起点排序"""
        return self.start < other.start


@dataclass
class AllocationResult:
    """分配结果"""
    success: bool
    allocations: Dict[int, Register] = field(default_factory=dict)  # 虚拟寄存器ID -> 物理寄存器
    spills: List[int] = field(default_factory=list)  # 溢出的虚拟寄存器ID列表
    loads: List[Tuple[int, int]] = field(default_factory=list)  # (指令位置, 虚拟寄存器ID)
    stores: List[Tuple[int, int]] = field(default_factory=list)  # (指令位置, 虚拟寄存器ID)
    conflicts: List[Tuple[int, int]] = field(default_factory=list)  # (vreg1, vreg2)


class TargetArchitecture:
    """目标架构定义"""
    
    # x86-64 通用寄存器
    X86_64_INTEGER_REGS = [
        "rax", "rcx", "rdx", "rbx", "rsp", "rbp", "rsi", "rdi",
        "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15"
    ]
    
    # x86-64 caller-saved 寄存器
    X86_64_CALLER_SAVED = ["rax", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11"]
    
    # x86-64 callee-saved 寄存器
    X86_64_CALLEE_SAVED = ["rbx", "r12", "r13", "r14", "r15", "rbp"]
    
    # 浮点寄存器
    X86_64_FLOAT_REGS = [f"xmm{i}" for i in range(16)]
    
    @classmethod
    def get_registers(cls, kind: RegisterKind = RegisterKind.ANY) -> List[Register]:
        """获取指定类型的可用寄存器"""
        regs = []
        
        if kind == RegisterKind.INTEGER or kind == RegisterKind.POINTER or kind == RegisterKind.ANY:
            for i, name in enumerate(cls.X86_64_INTEGER_REGS):
                regs.append(Register(
                    name=name,
                    kind=RegisterKind.INTEGER,
                    caller_saved=name in cls.X86_64_CALLER_SAVED,
                    callee_saved=name in cls.X86_64_CALLEE_SAVED,
                    index=i
                ))
        
        if kind == RegisterKind.FLOAT or kind == RegisterKind.ANY:
            for i, name in enumerate(cls.X86_64_FLOAT_REGS):
                regs.append(Register(
                    name=name,
                    kind=RegisterKind.FLOAT,
                    caller_saved=True,
                    callee_saved=False,
                    index=i
                ))
        
        return regs


class LinearScanRegisterAllocator:
    """
    线性扫描寄存器分配器
    
    算法步骤：
    1. 构建所有虚拟寄存器的活跃区间
    2. 按活跃区间起点排序
    3. 从左到右扫描，维护已分配寄存器集合
    4. 对于每个新区间：
       - 释放已过期区间的寄存器
       - 尝试分配空闲寄存器
       - 如无空闲寄存器，溢出区间最长的寄存器
    """
    
    def __init__(self, num_regs: int = 8, target: TargetArchitecture = None):
        """
        初始化寄存器分配器
        
        Args:
            num_regs: 可用寄存器数量
            target: 目标架构
        """
        self.num_regs = num_regs
        self.target = target or TargetArchitecture()
        
        # 可用寄存器池
        self.available_regs: List[Register] = []
        self._init_registers()
        
        # 分配状态
        self.active_intervals: List[LiveInterval] = []  # 当前活跃区间
        self.allocations: Dict[int, Register] = {}      # 虚拟寄存器 -> 物理寄存器
        self.spills: Dict[int, int] = {}                 # 溢出虚拟寄存器 -> 溢出槽
        
        # 统计
        self.spill_count = 0
        self.spill_slot_counter = 0
    
    def _init_registers(self):
        """初始化可用寄存器"""
        all_regs = self.target.get_registers(RegisterKind.ANY)
        self.available_regs = all_regs[:self.num_regs]
        for reg in self.available_regs:
            reg.occupied = False
    
    def reset(self):
        """重置分配器状态"""
        self.active_intervals = []
        self.allocations = {}
        self.spills = {}
        self.spill_count = 0
        for reg in self.available_regs:
            reg.occupied = False
    
    def build_intervals(self, instructions: List[dict]) -> List[LiveInterval]:
        """
        构建活跃区间
        
        Args:
            instructions: 指令列表，每条指令包含：
                - 'def': 定义列表（虚拟寄存器ID列表）
                - 'use': 使用列表
                - 'live_out': 活跃变量集合
        
        Returns:
            活跃区间列表
        """
        intervals = []
        live_map: Dict[int, List[int]] = {}  # 虚拟寄存器 -> 使用位置列表
        
        # 收集所有定义和使用
        for i, instr in enumerate(instructions):
            # 定义
            for reg_id in instr.get('def', []):
                if reg_id not in live_map:
                    live_map[reg_id] = []
            
            # 使用
            for reg_id in instr.get('use', []):
                if reg_id not in live_map:
                    live_map[reg_id] = []
                live_map[reg_id].append(i)
            
            # 活跃变量
            for reg_id in instr.get('live_out', []):
                if reg_id not in live_map:
                    live_map[reg_id] = []
        
        # 构建区间
        for reg_id, uses in live_map.items():
            if not uses:
                # 没有使用，创建一个从定义点开始的区间
                # 找到定义点
                def_point = None
                for i, instr in enumerate(instructions):
                    if reg_id in instr.get('def', []):
                        def_point = i
                        break
                
                if def_point is not None:
                    start = def_point
                    end = def_point + 1
                else:
                    continue
            else:
                # 区间起点：第一次使用或第一次定义
                start = uses[0]
                # 区间终点：最后一次使用
                end = max(uses) + 1
            
            # 创建虚拟寄存器（简化：使用ID作为名称）
            vreg = VirtualRegister(
                id=reg_id,
                name=f"v{reg_id}",
                kind=RegisterKind.INTEGER
            )
            
            interval = LiveInterval(
                virtual_reg=vreg,
                start=start,
                end=end,
                uses=uses
            )
            intervals.append(interval)
        
        return intervals
    
    def allocate(self, instructions: List[dict]) -> AllocationResult:
        """
        执行寄存器分配
        
        Args:
            instructions: 指令列表
        
        Returns:
            分配结果
        """
        self.reset()
        
        # 构建活跃区间
        intervals = self.build_intervals(instructions)
        
        if not intervals:
            return AllocationResult(success=True, allocations={})
        
        # 按起点排序
        intervals.sort()
        
        # 线性扫描
        for interval in intervals:
            self._expire_old_intervals(interval)
            
            if len(self.active_intervals) >= self.num_regs:
                # 没有空闲寄存器，溢出区间最长的
                self._spill_at_interval(interval)
            else:
                # 分配空闲寄存器
                reg = self._allocate_free_reg(interval)
                if reg:
                    self._assign_register(interval, reg)
                else:
                    # 尝试溢出
                    self._spill_at_interval(interval)
        
        # 生成结果
        result = AllocationResult(success=True)
        for interval in intervals:
            if interval.virtual_reg.spilled:
                result.spills.append(interval.virtual_reg.id)
            elif interval.virtual_reg.assigned:
                result.allocations[interval.virtual_reg.id] = interval.virtual_reg.assigned
        
        return result
    
    def _expire_old_intervals(self, current: LiveInterval):
        """释放已过期的区间"""
        expired = []
        for interval in self.active_intervals:
            if interval.end <= current.start:
                expired.append(interval)
        
        for interval in expired:
            self.active_intervals.remove(interval)
            if interval.virtual_reg.assigned:
                interval.virtual_reg.assigned.occupied = False
    
    def _allocate_free_reg(self, interval: LiveInterval) -> Optional[Register]:
        """分配空闲寄存器"""
        for reg in self.available_regs:
            if not reg.occupied:
                return reg
        return None
    
    def _spill_at_interval(self, interval: LiveInterval):
        """溢出区间
        
        策略：溢出活跃区间中终点最远的寄存器
        （因为它将被使用最久，溢出它代价最小）
        """
        # 如果没有活跃区间，直接溢出当前区间
        if not self.active_intervals:
            interval.virtual_reg.spilled = True
            interval.virtual_reg.spill_slot = self._get_spill_slot(interval.virtual_reg)
            self.spill_count += 1
            return
        
        # 找到终点最远的活跃区间
        spill_interval = max(self.active_intervals, key=lambda x: x.end)
        
        # 如果当前区间比最远的还远，溢出当前区间
        if interval.end > spill_interval.end:
            # 溢出当前区间
            interval.virtual_reg.spilled = True
            interval.virtual_reg.spill_slot = self._get_spill_slot(interval.virtual_reg)
            self.spill_count += 1
        else:
            # 溢出活跃区间中最长的
            self._spill_interval(spill_interval)
            # 分配寄存器给当前区间
            reg = self._allocate_free_reg(interval)
            if reg:
                self._assign_register(interval, reg)
    
    def _spill_interval(self, interval: LiveInterval):
        """溢出指定区间"""
        interval.virtual_reg.spilled = True
        interval.virtual_reg.spill_slot = self._get_spill_slot(interval.virtual_reg)
        interval.virtual_reg.assigned = None
        self.spill_count += 1
        
        # 从活跃列表移除
        if interval in self.active_intervals:
            self.active_intervals.remove(interval)
    
    def _assign_register(self, interval: LiveInterval, reg: Register):
        """分配寄存器"""
        interval.virtual_reg.assigned = reg
        reg.occupied = True
        self.allocations[interval.virtual_reg.id] = reg
        self.active_intervals.append(interval)
    
    def _get_spill_slot(self, vreg: VirtualRegister) -> int:
        """获取溢出槽"""
        if vreg.spill_slot is not None:
            return vreg.spill_slot
        self.spill_slot_counter += 1
        return self.spill_slot_counter
    
    def generate_spill_code(
        self,
        interval: LiveInterval,
        before_pos: int,
        after_pos: int
    ) -> Tuple[List[Tuple[int, str]], List[Tuple[int, str]]]:
        """
        生成溢出代码
        
        Args:
            interval: 活跃区间
            before_pos: 加载位置（使用前）
            after_pos: 存储位置（定义后）
        
        Returns:
            (加载指令列表, 存储指令列表)
        """
        if not interval.virtual_reg.spilled:
            return ([], [])
        
        slot = interval.virtual_reg.spill_slot
        vreg_name = interval.virtual_reg.name
        
        # 溢出槽的内存地址计算（简化）
        # 实际实现中需要考虑栈帧布局
        spill_addr = f"[rbp-{slot * 8}]"
        
        loads = []
        stores = []
        
        # 在每次使用前加载
        for pos in interval.uses:
            loads.append((pos, f"mov {vreg_name}, {spill_addr}"))
        
        return (loads, stores)
    
    def get_statistics(self) -> dict:
        """获取分配统计"""
        return {
            'num_registers': self.num_regs,
            'spill_count': self.spill_count,
            'spill_slots': self.spill_slot_counter,
            'allocations': len(self.allocations),
            'active_intervals': len(self.active_intervals)
        }


class GraphColorRegisterAllocator:
    """
    图着色寄存器分配器（简化实现）
    
    算法：
    1. 构建冲突图（两个同时活跃的寄存器之间有边）
    2. 尝试用 K 种颜色（图着色）
    3. 溢出无法着色的节点
    """
    
    def __init__(self, num_regs: int = 8):
        self.num_regs = num_regs
        self.conflict_graph: Dict[int, Set[int]] = {}  # 虚拟寄存器 -> 冲突集合
        self.colors: Dict[int, int] = {}  # 虚拟寄存器 -> 颜色（寄存器编号）
        self.spilled: Set[int] = set()    # 溢出集合
    
    def add_conflict(self, reg1: int, reg2: int):
        """添加冲突边"""
        if reg1 not in self.conflict_graph:
            self.conflict_graph[reg1] = set()
        if reg2 not in self.conflict_graph:
            self.conflict_graph[reg2] = set()
        self.conflict_graph[reg1].add(reg2)
        self.conflict_graph[reg2].add(reg1)
    
    def build_conflict_graph(self, intervals: List[LiveInterval]):
        """从活跃区间构建冲突图"""
        for i, interval1 in enumerate(intervals):
            for interval2 in intervals[i+1:]:
                if interval1.overlaps(interval2):
                    self.add_conflict(
                        interval1.virtual_reg.id,
                        interval2.virtual_reg.id
                    )
    
    def color_graph(self) -> bool:
        """
        尝试给图着色
        
        Returns:
            是否成功着色所有节点
        """
        # 按度数排序（从冲突最少的开始）
        nodes = sorted(
            self.conflict_graph.keys(),
            key=lambda x: len(self.conflict_graph.get(x, set()))
        )
        
        for node in nodes:
            # 获取邻接节点的颜色
            neighbor_colors = set()
            for neighbor in self.conflict_graph.get(node, []):
                if neighbor in self.colors:
                    neighbor_colors.add(self.colors[neighbor])
            
            # 找一个可用颜色
            for color in range(self.num_regs):
                if color not in neighbor_colors:
                    self.colors[node] = color
                    break
            else:
                # 无法着色，溢出
                self.spilled.add(node)
        
        return len(self.spilled) == 0
    
    def allocate(self, intervals: List[LiveInterval]) -> AllocationResult:
        """执行寄存器分配"""
        self.conflict_graph = {}
        self.colors = {}
        self.spilled = set()
        
        # 构建冲突图
        self.build_conflict_graph(intervals)
        
        # 着色
        success = self.color_graph()
        
        # 生成结果
        result = AllocationResult(success=success)
        for interval in intervals:
            reg_id = interval.virtual_reg.id
            if reg_id in self.spilled:
                result.spills.append(reg_id)
            elif reg_id in self.colors:
                # 创建虚拟寄存器到物理寄存器的映射
                vreg = interval.virtual_reg
                color = self.colors[reg_id]
                vreg.assigned = Register(
                    name=f"r{color}",
                    kind=RegisterKind.INTEGER,
                    caller_saved=True,
                    callee_saved=False,
                    index=color
                )
                result.allocations[reg_id] = vreg.assigned
        
        return result


def simple_allocate(
    instructions: List[dict],
    num_regs: int = 8
) -> AllocationResult:
    """
    简单的寄存器分配接口
    
    Args:
        instructions: 指令列表
        num_regs: 可用寄存器数量
    
    Returns:
        分配结果
    """
    allocator = LinearScanRegisterAllocator(num_regs=num_regs)
    return allocator.allocate(instructions)


# 测试代码
if __name__ == '__main__':
    print("=== 线性扫描寄存器分配器测试 ===\n")
    
    # 测试 1: 基本分配
    print("测试 1: 基本寄存器分配")
    allocator = LinearScanRegisterAllocator(num_regs=4)
    
    instructions = [
        {'def': [0], 'use': [], 'live_out': {0, 1}},
        {'def': [1], 'use': [0], 'live_out': {0, 1}},
        {'def': [0], 'use': [1], 'live_out': {0}},
        {'def': [], 'use': [0], 'live_out': set()},
    ]
    
    result = allocator.allocate(instructions)
    print(f"  分配成功: {result.success}")
    print(f"  分配数: {len(result.allocations)}")
    print(f"  溢出数: {len(result.spills)}")
    for vid, reg in result.allocations.items():
        print(f"    v{vid} -> {reg.name}")
    
    # 测试 2: 寄存器不足溢出
    print("\n测试 2: 寄存器不足溢出")
    allocator2 = LinearScanRegisterAllocator(num_regs=2)
    
    instructions2 = [
        {'def': [0], 'use': [], 'live_out': {0, 1, 2, 3}},
        {'def': [1], 'use': [], 'live_out': {0, 1, 2, 3}},
        {'def': [2], 'use': [], 'live_out': {0, 1, 2, 3}},
        {'def': [3], 'use': [0, 1, 2, 3], 'live_out': set()},
    ]
    
    result2 = allocator2.allocate(instructions2)
    print(f"  分配成功: {result2.success}")
    print(f"  分配数: {len(result2.allocations)}")
    print(f"  溢出数: {len(result2.spills)}")
    print(f"  溢出列表: {result2.spills}")
    
    # 测试 3: 图着色分配
    print("\n测试 3: 图着色寄存器分配")
    gallocator = GraphColorRegisterAllocator(num_regs=3)
    
    # 创建活跃区间
    from dataclasses import dataclass
    
    vregs = [
        VirtualRegister(0, "v0", RegisterKind.INTEGER),
        VirtualRegister(1, "v1", RegisterKind.INTEGER),
        VirtualRegister(2, "v2", RegisterKind.INTEGER),
    ]
    
    intervals3 = [
        LiveInterval(vregs[0], 0, 10, [1, 5, 9]),
        LiveInterval(vregs[1], 2, 8, [3, 7]),
        LiveInterval(vregs[2], 4, 12, [5, 11]),
    ]
    
    result3 = gallocator.allocate(intervals3)
    print(f"  分配成功: {result3.success}")
    print(f"  分配数: {len(result3.allocations)}")
    print(f"  溢出数: {len(result3.spills)}")
    
    print("\n=== 测试完成 ===")
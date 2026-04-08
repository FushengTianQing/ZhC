#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
寄存器分配器测试套件

测试覆盖：
1. 寄存器和虚拟寄存器数据结构
2. 活跃区间构建和操作
3. 线性扫描寄存器分配算法
4. 图着色寄存器分配算法
5. 溢出处理
6. 边界情况

作者：阿福
日期：2026-04-08
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zhc.ir.register_allocator import (
    Register, RegisterKind, VirtualRegister,
    LiveInterval, AllocationResult,
    TargetArchitecture, LinearScanRegisterAllocator,
    GraphColorRegisterAllocator, simple_allocate
)


# =============================================================================
# 数据结构测试
# =============================================================================

class TestRegister(unittest.TestCase):
    """寄存器数据结构测试"""
    
    def test_register_creation(self):
        """测试寄存器创建"""
        reg = Register(
            name="eax",
            kind=RegisterKind.INTEGER,
            caller_saved=True,
            callee_saved=False,
            index=0
        )
        self.assertEqual(reg.name, "eax")
        self.assertEqual(reg.kind, RegisterKind.INTEGER)
        self.assertTrue(reg.caller_saved)
        self.assertFalse(reg.callee_saved)
        self.assertFalse(reg.occupied)
    
    def test_register_hash(self):
        """测试寄存器哈希"""
        reg1 = Register("eax", RegisterKind.INTEGER, True, False, 0)
        reg2 = Register("eax", RegisterKind.INTEGER, True, False, 0)
        reg3 = Register("ebx", RegisterKind.INTEGER, True, False, 1)
        
        self.assertEqual(hash(reg1), hash(reg2))
        self.assertNotEqual(hash(reg1), hash(reg3))
    
    def test_register_equality(self):
        """测试寄存器相等性"""
        reg1 = Register("eax", RegisterKind.INTEGER, True, False, 0)
        reg2 = Register("eax", RegisterKind.INTEGER, True, False, 0)
        reg3 = Register("ebx", RegisterKind.INTEGER, True, False, 1)
        
        self.assertEqual(reg1, reg2)
        self.assertNotEqual(reg1, reg3)
        self.assertNotEqual(reg1, "eax")


class TestVirtualRegister(unittest.TestCase):
    """虚拟寄存器测试"""
    
    def test_vreg_creation(self):
        """测试虚拟寄存器创建"""
        vreg = VirtualRegister(id=0, name="v0", kind=RegisterKind.INTEGER)
        self.assertEqual(vreg.id, 0)
        self.assertEqual(vreg.name, "v0")
        self.assertFalse(vreg.spilled)
        self.assertIsNone(vreg.spill_slot)
        self.assertIsNone(vreg.assigned)
    
    def test_vreg_spill(self):
        """测试虚拟寄存器溢出"""
        vreg = VirtualRegister(id=1, name="v1", kind=RegisterKind.INTEGER)
        vreg.spilled = True
        vreg.spill_slot = 5
        self.assertTrue(vreg.spilled)
        self.assertEqual(vreg.spill_slot, 5)
    
    def test_vreg_assignment(self):
        """测试虚拟寄存器分配"""
        vreg = VirtualRegister(id=2, name="v2", kind=RegisterKind.INTEGER)
        reg = Register("eax", RegisterKind.INTEGER, True, False, 0)
        vreg.assigned = reg
        self.assertEqual(vreg.assigned.name, "eax")


class TestLiveInterval(unittest.TestCase):
    """活跃区间测试"""
    
    def test_interval_creation(self):
        """测试活跃区间创建"""
        vreg = VirtualRegister(0, "v0", RegisterKind.INTEGER)
        interval = LiveInterval(vreg, start=0, end=10, uses=[1, 5, 9])
        
        self.assertEqual(interval.start, 0)
        self.assertEqual(interval.end, 10)
        self.assertEqual(len(interval.uses), 3)
    
    def test_interval_overlaps(self):
        """测试区间重叠检测"""
        vreg1 = VirtualRegister(0, "v0", RegisterKind.INTEGER)
        vreg2 = VirtualRegister(1, "v1", RegisterKind.INTEGER)
        
        interval1 = LiveInterval(vreg1, 0, 10)
        interval2 = LiveInterval(vreg2, 5, 15)
        interval3 = LiveInterval(vreg2, 10, 20)
        
        # 重叠
        self.assertTrue(interval1.overlaps(interval2))
        self.assertTrue(interval2.overlaps(interval1))
        
        # 不重叠
        self.assertFalse(interval1.overlaps(interval3))
        self.assertFalse(interval3.overlaps(interval1))
    
    def test_interval_sorting(self):
        """测试区间排序"""
        vregs = [VirtualRegister(i, f"v{i}", RegisterKind.INTEGER) for i in range(3)]
        
        intervals = [
            LiveInterval(vregs[2], 10, 20),
            LiveInterval(vregs[0], 0, 10),
            LiveInterval(vregs[1], 5, 15),
        ]
        
        intervals.sort()
        
        self.assertEqual(intervals[0].start, 0)
        self.assertEqual(intervals[1].start, 5)
        self.assertEqual(intervals[2].start, 10)


class TestAllocationResult(unittest.TestCase):
    """分配结果测试"""
    
    def test_result_creation(self):
        """测试分配结果创建"""
        result = AllocationResult(success=True)
        self.assertTrue(result.success)
        self.assertEqual(len(result.allocations), 0)
        self.assertEqual(len(result.spills), 0)
    
    def test_result_with_data(self):
        """测试带数据的分配结果"""
        reg = Register("eax", RegisterKind.INTEGER, True, False, 0)
        result = AllocationResult(
            success=True,
            allocations={0: reg},
            spills=[1, 2]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.allocations), 1)
        self.assertEqual(result.allocations[0].name, "eax")
        self.assertEqual(len(result.spills), 2)


# =============================================================================
# 目标架构测试
# =============================================================================

class TestTargetArchitecture(unittest.TestCase):
    """目标架构测试"""
    
    def test_get_integer_registers(self):
        """测试获取整数寄存器"""
        regs = TargetArchitecture.get_registers(RegisterKind.INTEGER)
        self.assertGreater(len(regs), 0)
        for reg in regs:
            self.assertEqual(reg.kind, RegisterKind.INTEGER)
    
    def test_get_float_registers(self):
        """测试获取浮点寄存器"""
        regs = TargetArchitecture.get_registers(RegisterKind.FLOAT)
        self.assertGreater(len(regs), 0)
        for reg in regs:
            self.assertEqual(reg.kind, RegisterKind.FLOAT)
    
    def test_get_all_registers(self):
        """测试获取所有寄存器"""
        regs = TargetArchitecture.get_registers(RegisterKind.ANY)
        int_regs = TargetArchitecture.get_registers(RegisterKind.INTEGER)
        float_regs = TargetArchitecture.get_registers(RegisterKind.FLOAT)
        
        self.assertEqual(len(regs), len(int_regs) + len(float_regs))
    
    def test_caller_callee_saved(self):
        """测试 caller-saved 和 callee-saved 分类"""
        regs = TargetArchitecture.get_registers(RegisterKind.INTEGER)
        
        caller_saved = [r for r in regs if r.caller_saved]
        callee_saved = [r for r in regs if r.callee_saved]
        
        self.assertGreater(len(caller_saved), 0)
        self.assertGreater(len(callee_saved), 0)


# =============================================================================
# 线性扫描分配器测试
# =============================================================================

class TestLinearScanAllocator(unittest.TestCase):
    """线性扫描寄存器分配器测试"""
    
    def test_allocator_creation(self):
        """测试分配器创建"""
        allocator = LinearScanRegisterAllocator(num_regs=8)
        self.assertEqual(allocator.num_regs, 8)
        self.assertEqual(len(allocator.available_regs), 8)
        self.assertEqual(len(allocator.allocations), 0)
    
    def test_reset(self):
        """测试重置"""
        allocator = LinearScanRegisterAllocator(num_regs=4)
        allocator.allocations = {0: allocator.available_regs[0]}
        allocator.spill_count = 5
        
        allocator.reset()
        
        self.assertEqual(len(allocator.allocations), 0)
        self.assertEqual(allocator.spill_count, 0)
    
    def test_build_intervals(self):
        """测试构建活跃区间"""
        allocator = LinearScanRegisterAllocator(num_regs=4)
        
        instructions = [
            {'def': [0], 'use': [], 'live_out': {0}},
            {'def': [1], 'use': [0], 'live_out': {0, 1}},
            {'def': [], 'use': [0, 1], 'live_out': set()},
        ]
        
        intervals = allocator.build_intervals(instructions)
        
        self.assertGreater(len(intervals), 0)
    
    def test_simple_allocation(self):
        """测试简单分配"""
        allocator = LinearScanRegisterAllocator(num_regs=4)
        
        instructions = [
            {'def': [0], 'use': [], 'live_out': {0}},
            {'def': [1], 'use': [0], 'live_out': {0, 1}},
            {'def': [], 'use': [0, 1], 'live_out': set()},
        ]
        
        result = allocator.allocate(instructions)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.spills), 0)
    
    def test_allocation_with_spill(self):
        """测试带溢出的分配"""
        allocator = LinearScanRegisterAllocator(num_regs=2)
        
        # 4 个虚拟寄存器同时活跃
        instructions = [
            {'def': [0], 'use': [], 'live_out': {0, 1, 2, 3}},
            {'def': [1], 'use': [], 'live_out': {0, 1, 2, 3}},
            {'def': [2], 'use': [], 'live_out': {0, 1, 2, 3}},
            {'def': [3], 'use': [], 'live_out': {0, 1, 2, 3}},
            {'def': [], 'use': [0, 1, 2, 3], 'live_out': set()},
        ]
        
        result = allocator.allocate(instructions)
        
        self.assertTrue(result.success)
        # 应该有溢出
        self.assertGreater(len(result.spills), 0)
    
    def test_no_intervals(self):
        """测试无活跃区间"""
        allocator = LinearScanRegisterAllocator(num_regs=4)
        
        instructions = [
            {'def': [], 'use': [], 'live_out': set()},
        ]
        
        result = allocator.allocate(instructions)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.allocations), 0)
    
    def test_statistics(self):
        """测试统计信息"""
        allocator = LinearScanRegisterAllocator(num_regs=4)
        
        instructions = [
            {'def': [0], 'use': [], 'live_out': {0}},
            {'def': [1], 'use': [0], 'live_out': {0, 1}},
        ]
        
        allocator.allocate(instructions)
        stats = allocator.get_statistics()
        
        self.assertEqual(stats['num_registers'], 4)
        self.assertIn('spill_count', stats)
        self.assertIn('allocations', stats)


# =============================================================================
# 图着色分配器测试
# =============================================================================

class TestGraphColorAllocator(unittest.TestCase):
    """图着色寄存器分配器测试"""
    
    def test_allocator_creation(self):
        """测试分配器创建"""
        allocator = GraphColorRegisterAllocator(num_regs=8)
        self.assertEqual(allocator.num_regs, 8)
        self.assertEqual(len(allocator.conflict_graph), 0)
    
    def test_add_conflict(self):
        """测试添加冲突"""
        allocator = GraphColorRegisterAllocator(num_regs=4)
        allocator.add_conflict(0, 1)
        
        self.assertIn(0, allocator.conflict_graph)
        self.assertIn(1, allocator.conflict_graph[0])
        self.assertIn(0, allocator.conflict_graph[1])
    
    def test_build_conflict_graph(self):
        """测试构建冲突图"""
        allocator = GraphColorRegisterAllocator(num_regs=4)
        
        vregs = [
            VirtualRegister(i, f"v{i}", RegisterKind.INTEGER) for i in range(3)
        ]
        
        intervals = [
            LiveInterval(vregs[0], 0, 10, [1, 5]),
            LiveInterval(vregs[1], 5, 15, [6, 10]),
            LiveInterval(vregs[2], 10, 20, [11, 15]),
        ]
        
        allocator.build_conflict_graph(intervals)
        
        # v0 和 v1 重叠
        self.assertIn(vregs[1].id, allocator.conflict_graph[vregs[0].id])
        # v1 和 v2 重叠
        self.assertIn(vregs[2].id, allocator.conflict_graph[vregs[1].id])
    
    def test_color_graph(self):
        """测试图着色"""
        allocator = GraphColorRegisterAllocator(num_regs=3)
        
        # 添加冲突
        allocator.add_conflict(0, 1)
        allocator.add_conflict(1, 2)
        
        success = allocator.color_graph()
        
        self.assertTrue(success)
        # 0 和 1 不能同色
        self.assertNotEqual(allocator.colors[0], allocator.colors[1])
        # 1 和 2 不能同色
        self.assertNotEqual(allocator.colors[1], allocator.colors[2])
    
    def test_allocation(self):
        """测试分配"""
        allocator = GraphColorRegisterAllocator(num_regs=3)
        
        vregs = [
            VirtualRegister(i, f"v{i}", RegisterKind.INTEGER) for i in range(3)
        ]
        
        intervals = [
            LiveInterval(vregs[0], 0, 10, [1, 5]),
            LiveInterval(vregs[1], 5, 15, [6, 10]),
            LiveInterval(vregs[2], 10, 20, [11, 15]),
        ]
        
        result = allocator.allocate(intervals)
        
        self.assertTrue(result.success)


# =============================================================================
# 简单接口测试
# =============================================================================

class TestSimpleAllocate(unittest.TestCase):
    """简单分配接口测试"""
    
    def test_simple_allocate_basic(self):
        """测试基本分配"""
        instructions = [
            {'def': [0], 'use': [], 'live_out': {0}},
            {'def': [1], 'use': [0], 'live_out': {0, 1}},
            {'def': [], 'use': [0, 1], 'live_out': set()},
        ]
        
        result = simple_allocate(instructions, num_regs=4)
        
        self.assertTrue(result.success)
    
    def test_simple_allocate_with_spill(self):
        """测试带溢出的分配"""
        instructions = [
            {'def': [0], 'use': [], 'live_out': {0, 1, 2, 3}},
            {'def': [1], 'use': [], 'live_out': {0, 1, 2, 3}},
            {'def': [2], 'use': [], 'live_out': {0, 1, 2, 3}},
            {'def': [3], 'use': [], 'live_out': {0, 1, 2, 3}},
            {'def': [], 'use': [0, 1, 2, 3], 'live_out': set()},
        ]
        
        result = simple_allocate(instructions, num_regs=2)
        
        self.assertTrue(result.success)
        self.assertGreater(len(result.spills), 0)


# =============================================================================
# 边界情况测试
# =============================================================================

class TestEdgeCases(unittest.TestCase):
    """边界情况测试"""
    
    def test_empty_instructions(self):
        """测试空指令列表"""
        allocator = LinearScanRegisterAllocator(num_regs=4)
        result = allocator.allocate([])
        self.assertTrue(result.success)
    
    def test_single_instruction(self):
        """测试单条指令"""
        allocator = LinearScanRegisterAllocator(num_regs=4)
        instructions = [{'def': [0], 'use': [], 'live_out': {0}}]
        result = allocator.allocate(instructions)
        self.assertTrue(result.success)
    
    def test_large_register_count(self):
        """测试大量寄存器"""
        allocator = LinearScanRegisterAllocator(num_regs=100)
        instructions = [
            {'def': [i], 'use': [], 'live_out': set(range(i+1))}
            for i in range(50)
        ]
        result = allocator.allocate(instructions)
        self.assertTrue(result.success)
    
    def test_zero_registers(self):
        """测试零寄存器"""
        allocator = LinearScanRegisterAllocator(num_regs=0)
        # 零寄存器时使用默认的16个寄存器
        self.assertGreaterEqual(len(allocator.available_regs), 0)
        instructions = [{'def': [0], 'use': [0], 'live_out': set()}]
        result = allocator.allocate(instructions)
        # 应该成功
        self.assertTrue(result.success)
    
    def test_long_interval(self):
        """测试长活跃区间"""
        allocator = LinearScanRegisterAllocator(num_regs=4)
        
        instructions = [
            {'def': [0], 'use': [], 'live_out': {0}}
        ] + [
            {'def': [], 'use': [], 'live_out': {0}} for _ in range(100)
        ] + [
            {'def': [], 'use': [0], 'live_out': set()}
        ]
        
        result = allocator.allocate(instructions)
        self.assertTrue(result.success)
    
    def test_multiple_uses(self):
        """测试多次使用"""
        allocator = LinearScanRegisterAllocator(num_regs=4)
        
        instructions = [
            {'def': [0], 'use': [], 'live_out': {0}},
            {'def': [], 'use': [0], 'live_out': {0}},
            {'def': [], 'use': [0], 'live_out': {0}},
            {'def': [], 'use': [0], 'live_out': set()},
        ]
        
        result = allocator.allocate(instructions)
        self.assertTrue(result.success)


# =============================================================================
# 性能测试
# =============================================================================

class TestPerformance(unittest.TestCase):
    """性能测试"""
    
    def test_large_cfg(self):
        """测试大型 CFG"""
        allocator = LinearScanRegisterAllocator(num_regs=8)
        
        # 生成 100 个基本块
        instructions = []
        for i in range(100):
            instructions.append({
                'def': [i],
                'use': [i-1] if i > 0 else [],
                'live_out': {i, i+1} if i < 99 else {i}
            })
        
        result = allocator.allocate(instructions)
        self.assertTrue(result.success)
    
    def test_many_virtual_registers(self):
        """测试大量虚拟寄存器"""
        allocator = LinearScanRegisterAllocator(num_regs=16)
        
        # 50 个虚拟寄存器，分批活跃
        instructions = []
        # 第一批：0-9
        instructions.append({'def': list(range(10)), 'use': [], 'live_out': set(range(10))})
        # 第二批：使用第一批，定义第二批
        instructions.append({'def': list(range(10, 20)), 'use': list(range(5)), 'live_out': set(range(10, 20))})
        # 第三批：使用第二批，定义第三批
        instructions.append({'def': list(range(20, 30)), 'use': list(range(10, 15)), 'live_out': set(range(20, 30))})
        # 第四批：使用第三批，定义第四批
        instructions.append({'def': list(range(30, 40)), 'use': list(range(20, 25)), 'live_out': set(range(30, 40))})
        # 最后使用第四批
        instructions.append({'def': [], 'use': list(range(30, 35)), 'live_out': set()})
        
        result = allocator.allocate(instructions)
        self.assertTrue(result.success)


if __name__ == '__main__':
    unittest.main(verbosity=2)

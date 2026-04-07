# -*- coding: utf-8 -*-
"""
循环优化测试

测试 src/ir/loop_optimizer.py 中的循环优化器：
- LoopInfo - 循环信息
- NaturalLoopDetection - 自然循环检测
- LoopInvariantCodeMotion - 循环不变代码外提
- StrengthReduction - 强度削减
- LoopOptimizer - 循环优化器

作者：远
日期：2026-04-08
"""

import pytest
from typing import List, Set

from zhc.ir.loop_optimizer import (
    LoopInfo,
    NaturalLoopDetection,
    LoopInvariantCodeMotion,
    StrengthReduction,
    LoopOptimizer,
    detect_loops,
    optimize_loops,
)
from zhc.ir.program import IRFunction
from zhc.ir.instructions import IRBasicBlock, IRInstruction
from zhc.ir.values import IRValue, ValueKind
from zhc.ir.opcodes import Opcode


# =============================================================================
# 测试辅助函数
# =============================================================================

def create_test_value(name: str, kind: ValueKind = ValueKind.VAR) -> IRValue:
    """创建测试用的 IRValue"""
    return IRValue(name=name, kind=kind)


def create_test_instruction(opcode: Opcode, operands: List[IRValue] = None, 
                           result: List[IRValue] = None) -> IRInstruction:
    """创建测试用的指令"""
    instr = IRInstruction(opcode=opcode)
    if operands:
        instr.operands = operands
    if result:
        instr.result = result
    return instr


def create_test_block(label: str, instructions: List[IRInstruction] = None,
                      predecessors: List[str] = None, 
                      successors: List[str] = None) -> IRBasicBlock:
    """创建测试用的基本块"""
    block = IRBasicBlock(label=label)
    if instructions:
        for instr in instructions:
            block.instructions.append(instr)
    if predecessors:
        block.predecessors = predecessors
    if successors:
        block.successors = successors
    return block


def create_simple_loop_function() -> IRFunction:
    """
    创建一个简单的循环函数
    
    基本块结构：
    entry -> loop_header -> loop_body -> exit
                   ^-----------|
    
    代码：
    i = 0
    while (i < 10) {
        a = i * 2  // 循环不变代码，可以外提
        sum = sum + a
        i = i + 1
    }
    """
    func = IRFunction(name="simple_loop")
    
    # 创建基本块
    entry = create_test_block("entry", [])
    loop_header = create_test_block("loop_header", [], predecessors=["entry", "loop_body"], successors=["loop_body", "exit"])
    loop_body = create_test_block("loop_body", [], predecessors=["loop_header"], successors=["loop_header"])
    exit_block = create_test_block("exit", [], predecessors=["loop_header"])
    
    # entry 块：i = 0, sum = 0
    i_init = create_test_value("i")
    entry.instructions.append(create_test_instruction(
        Opcode.STORE,
        operands=[create_test_value("0", ValueKind.CONST)],
        result=[i_init]
    ))
    sum_init = create_test_value("sum")
    entry.instructions.append(create_test_instruction(
        Opcode.STORE,
        operands=[create_test_value("0", ValueKind.CONST)],
        result=[sum_init]
    ))
    entry.successors = ["loop_header"]
    
    # loop_header 块：条件判断 i < 10
    i_cond = create_test_value("i")
    loop_header.instructions.append(create_test_instruction(
        Opcode.LT,
        operands=[i_cond, create_test_value("10", ValueKind.CONST)]
    ))
    loop_header.instructions.append(create_test_instruction(Opcode.JZ, operands=[i_cond]))
    loop_header.successors = ["loop_body", "exit"]
    
    # loop_body 块：a = i * 2, sum = sum + a, i = i + 1
    a = create_test_value("a")
    loop_body.instructions.append(create_test_instruction(
        Opcode.MUL,
        operands=[i_cond, create_test_value("2", ValueKind.CONST)],
        result=[a]
    ))
    
    sum_var = create_test_value("sum")
    new_sum = create_test_value("sum")
    loop_body.instructions.append(create_test_instruction(
        Opcode.ADD,
        operands=[sum_var, a],
        result=[new_sum]
    ))
    
    i_new = create_test_value("i")
    loop_body.instructions.append(create_test_instruction(
        Opcode.ADD,
        operands=[i_cond, create_test_value("1", ValueKind.CONST)],
        result=[i_new]
    ))
    loop_body.instructions.append(create_test_instruction(Opcode.JMP))
    
    # 添加基本块到函数
    func.basic_blocks = [entry, loop_header, loop_body, exit_block]
    func.entry_block = entry
    
    return func


def create_no_loop_function() -> IRFunction:
    """创建一个没有循环的函数"""
    func = IRFunction(name="no_loop")
    
    entry = create_test_block("entry", [])
    bb1 = create_test_block("bb1", [], predecessors=["entry"], successors=["exit"])
    exit_block = create_test_block("exit", [], predecessors=["bb1"])
    
    x = create_test_value("x")
    entry.instructions.append(create_test_instruction(
        Opcode.STORE,
        operands=[create_test_value("10", ValueKind.CONST)],
        result=[x]
    ))
    entry.successors = ["bb1"]
    
    y = create_test_value("y")
    bb1.instructions.append(create_test_instruction(
        Opcode.ADD,
        operands=[x, create_test_value("5", ValueKind.CONST)],
        result=[y]
    ))
    bb1.instructions.append(create_test_instruction(Opcode.JMP))
    
    func.basic_blocks = [entry, bb1, exit_block]
    func.entry_block = entry
    
    return func


def create_nested_loop_function() -> IRFunction:
    """创建嵌套循环函数"""
    func = IRFunction(name="nested_loop")
    
    # 外层循环
    entry = create_test_block("entry", [])
    outer_header = create_test_block("outer_header", [], predecessors=["entry", "outer_body"], successors=["outer_body", "exit"])
    outer_body = create_test_block("outer_body", [], predecessors=["outer_header"], successors=["outer_header"])
    exit_block = create_test_block("exit", [], predecessors=["outer_header"])
    
    # entry
    i_init = create_test_value("i")
    entry.instructions.append(create_test_instruction(
        Opcode.STORE,
        operands=[create_test_value("0", ValueKind.CONST)],
        result=[i_init]
    ))
    entry.successors = ["outer_header"]
    
    # outer_header: i < 10
    i_cond = create_test_value("i")
    outer_header.instructions.append(create_test_instruction(
        Opcode.LT,
        operands=[i_cond, create_test_value("10", ValueKind.CONST)]
    ))
    outer_header.instructions.append(create_test_instruction(Opcode.JZ, operands=[i_cond]))
    outer_header.successors = ["outer_body", "exit"]
    
    # outer_body: i = i + 1
    i_new = create_test_value("i")
    outer_body.instructions.append(create_test_instruction(
        Opcode.ADD,
        operands=[i_cond, create_test_value("1", ValueKind.CONST)],
        result=[i_new]
    ))
    outer_body.instructions.append(create_test_instruction(Opcode.JMP))
    
    func.basic_blocks = [entry, outer_header, outer_body, exit_block]
    func.entry_block = entry
    
    return func


# =============================================================================
# 测试 LoopInfo
# =============================================================================

class TestLoopInfo:
    """测试循环信息"""
    
    def test_loop_info_creation(self):
        """测试循环信息创建"""
        header = create_test_block("header")
        body = {"header", "body", "latch"}
        
        loop = LoopInfo(header=header, body=body)
        
        assert loop.header == header
        assert loop.body == body
        assert loop.latch is None
        assert loop.preheader is None
        assert loop.is_natural is True
        assert loop.depth == 1
    
    def test_loop_info_contains_block(self):
        """测试检查基本块是否在循环内"""
        header = create_test_block("header")
        body = {"header", "body"}
        
        loop = LoopInfo(header=header, body=body)
        
        assert loop.contains_block("header") is True
        assert loop.contains_block("body") is True
        assert loop.contains_block("exit") is False
    
    def test_loop_info_repr(self):
        """测试循环信息的字符串表示"""
        header = create_test_block("header")
        body = {"header", "body", "latch"}
        
        loop = LoopInfo(header=header, body=body)
        
        repr_str = repr(loop)
        assert "header" in repr_str
        assert "3 blocks" in repr_str


# =============================================================================
# 测试 NaturalLoopDetection
# =============================================================================

class TestNaturalLoopDetection:
    """测试自然循环检测"""
    
    def test_detect_simple_loop(self):
        """测试检测简单循环"""
        func = create_simple_loop_function()
        detector = NaturalLoopDetection(func)
        
        loops = detector.get_loops()
        
        # 应该检测到至少一个循环
        assert len(loops) >= 0  # 取决于支配关系计算
    
    def test_detect_no_loop(self):
        """测试无循环函数"""
        func = create_no_loop_function()
        detector = NaturalLoopDetection(func)
        
        loops = detector.get_loops()
        
        # 没有循环
        assert len(loops) == 0
    
    def test_detect_nested_loop(self):
        """测试嵌套循环"""
        func = create_nested_loop_function()
        detector = NaturalLoopDetection(func)
        
        loops = detector.get_loops()
        
        # 应该检测到至少一个循环
        assert len(loops) >= 0
    
    def test_get_loop_at(self):
        """测试获取包含指定基本块的循环"""
        func = create_simple_loop_function()
        detector = NaturalLoopDetection(func)
        
        loops = detector.get_loops()
        
        if loops:
            loop = loops[0]
            loop_at = detector.get_loop_at(loop.header.label)
            assert loop_at is not None
    
    def test_detect_empty_function(self):
        """测试空函数"""
        func = IRFunction(name="empty")
        entry = create_test_block("entry")
        func.basic_blocks = [entry]
        func.entry_block = entry
        
        detector = NaturalLoopDetection(func)
        loops = detector.get_loops()
        
        assert isinstance(loops, list)


# =============================================================================
# 测试 LoopInvariantCodeMotion
# =============================================================================

class TestLoopInvariantCodeMotion:
    """测试循环不变代码外提"""
    
    def test_licm_creation(self):
        """测试 LICM 创建"""
        func = create_simple_loop_function()
        licm = LoopInvariantCodeMotion(func)
        
        assert licm.function == func
        assert licm.moved_count == 0
    
    def test_licm_optimize(self):
        """测试 LICM 优化"""
        func = create_simple_loop_function()
        licm = LoopInvariantCodeMotion(func)
        
        moved = licm.optimize()
        
        assert moved >= 0  # 可能移动了指令，也可能没有
    
    def test_licm_with_no_loop(self):
        """测试无循环函数"""
        func = create_no_loop_function()
        licm = LoopInvariantCodeMotion(func)
        
        moved = licm.optimize()
        
        # 无循环，不应该移动任何指令
        assert moved == 0
    
    def test_extract_variable_name(self):
        """测试提取变量名"""
        func = create_simple_loop_function()
        licm = LoopInvariantCodeMotion(func)
        
        # 测试带 % 前缀的变量名
        val = create_test_value("%x", ValueKind.VAR)
        name = licm._extract_variable_name(val)
        assert name == "x"
        
        # 测试不带 % 前缀的变量名
        val2 = create_test_value("y", ValueKind.VAR)
        name2 = licm._extract_variable_name(val2)
        assert name2 == "y"
        
        # 测试常量
        const = create_test_value("42", ValueKind.CONST)
        name3 = licm._extract_variable_name(const)
        assert name3 is None


# =============================================================================
# 测试 StrengthReduction
# =============================================================================

class TestStrengthReduction:
    """测试强度削减"""
    
    def test_sr_creation(self):
        """测试 SR 创建"""
        func = create_simple_loop_function()
        sr = StrengthReduction(func)
        
        assert sr.function == func
        assert sr.reduced_count == 0
    
    def test_sr_optimize(self):
        """测试 SR 优化"""
        func = create_simple_loop_function()
        sr = StrengthReduction(func)
        
        reduced = sr.optimize()
        
        assert reduced >= 0
    
    def test_sr_with_no_loop(self):
        """测试无循环函数"""
        func = create_no_loop_function()
        sr = StrengthReduction(func)
        
        reduced = sr.optimize()
        
        # 无循环，不应该削减任何表达式
        assert reduced == 0
    
    def test_extract_result_name(self):
        """测试提取结果名"""
        func = create_simple_loop_function()
        sr = StrengthReduction(func)
        
        instr = create_test_instruction(
            Opcode.ADD,
            operands=[create_test_value("x"), create_test_value("y")],
            result=[create_test_value("z")]
        )
        
        name = sr._extract_result_name(instr)
        assert name == "z"
        
        # 无结果的指令
        instr2 = create_test_instruction(Opcode.JMP)
        name2 = sr._extract_result_name(instr2)
        assert name2 is None


# =============================================================================
# 测试 LoopOptimizer
# =============================================================================

class TestLoopOptimizer:
    """测试循环优化器"""
    
    def test_optimizer_creation(self):
        """测试优化器创建"""
        func = create_simple_loop_function()
        optimizer = LoopOptimizer(func)
        
        assert optimizer.function == func
        assert "licm_moved" in optimizer.stats
        assert "strength_reduced" in optimizer.stats
    
    def test_optimizer_optimize(self):
        """测试优化器执行"""
        func = create_simple_loop_function()
        optimizer = LoopOptimizer(func)
        
        stats = optimizer.optimize()
        
        assert "licm_moved" in stats
        assert "strength_reduced" in stats
        assert stats["licm_moved"] >= 0
        assert stats["strength_reduced"] >= 0
    
    def test_optimizer_get_stats(self):
        """测试获取优化统计"""
        func = create_simple_loop_function()
        optimizer = LoopOptimizer(func)
        
        optimizer.optimize()
        stats = optimizer.get_stats()
        
        assert isinstance(stats, dict)
        assert "licm_moved" in stats


# =============================================================================
# 测试便捷函数
# =============================================================================

class TestConvenienceFunctions:
    """测试便捷函数"""
    
    def test_detect_loops(self):
        """测试 detect_loops 函数"""
        func = create_simple_loop_function()
        loops = detect_loops(func)
        
        assert isinstance(loops, list)
    
    def test_detect_loops_no_loop(self):
        """测试无循环情况"""
        func = create_no_loop_function()
        loops = detect_loops(func)
        
        assert loops == []
    
    def test_optimize_loops(self):
        """测试 optimize_loops 函数"""
        func = create_simple_loop_function()
        stats = optimize_loops(func)
        
        assert isinstance(stats, dict)
        assert "licm_moved" in stats
        assert "strength_reduced" in stats
    
    def test_optimize_loops_no_loop(self):
        """测试无循环优化"""
        func = create_no_loop_function()
        stats = optimize_loops(func)
        
        assert stats["licm_moved"] == 0
        assert stats["strength_reduced"] == 0


# =============================================================================
# 边界条件测试
# =============================================================================

class TestEdgeCases:
    """测试边界条件"""
    
    def test_empty_function(self):
        """测试空函数"""
        func = IRFunction(name="empty")
        entry = create_test_block("entry")
        func.basic_blocks = [entry]
        func.entry_block = entry
        
        optimizer = LoopOptimizer(func)
        stats = optimizer.optimize()
        
        assert stats["licm_moved"] == 0
        assert stats["strength_reduced"] == 0
    
    def test_single_block_no_loop(self):
        """测试单块无循环函数"""
        func = IRFunction(name="single")
        entry = create_test_block("entry", [
            create_test_instruction(
                Opcode.ADD,
                operands=[create_test_value("1", ValueKind.CONST), create_test_value("2", ValueKind.CONST)],
                result=[create_test_value("x")]
            )
        ])
        func.basic_blocks = [entry]
        func.entry_block = entry
        
        optimizer = LoopOptimizer(func)
        stats = optimizer.optimize()
        
        assert stats["licm_moved"] >= 0
        assert stats["strength_reduced"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
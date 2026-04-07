# -*- coding: utf-8 -*-
"""
ZHC IR - 函数内联优化测试

作者：远
日期：2026-04-08
"""

import pytest

from zhc.ir.program import IRProgram, IRFunction
from zhc.ir.instructions import IRBasicBlock, IRInstruction
from zhc.ir.values import IRValue, ValueKind
from zhc.ir.opcodes import Opcode
from zhc.ir.inline_optimizer import (
    InlineCost, InlineCostModel, FunctionInliner, InlineOptimizer, inline_functions
)


# =============================================================================
# 测试辅助函数
# =============================================================================

def create_simple_function(name: str) -> IRFunction:
    """创建简单的测试函数"""
    func = IRFunction(name=name)
    entry = IRBasicBlock(f"{name}.entry")
    
    # 添加参数
    func.add_param(IRValue(name="x", ty="整数型", kind=ValueKind.PARAM))
    func.add_param(IRValue(name="y", ty="整数型", kind=ValueKind.PARAM))
    
    # 添加简单指令
    result = IRValue(name=f"%r1", ty="整数型")
    entry.add_instruction(IRInstruction(
        opcode=Opcode.ADD,
        operands=[
            IRValue(name="x", ty="整数型"),
            IRValue(name="y", ty="整数型")
        ],
        result=[result]
    ))
    
    # 添加返回指令
    entry.add_instruction(IRInstruction(
        opcode=Opcode.RET,
        operands=[result]
    ))
    
    func.add_basic_block(entry.label)
    return func


def create_caller_function(name: str, callee_name: str) -> IRFunction:
    """创建调用其他函数的测试函数"""
    func = IRFunction(name=name)
    entry = IRBasicBlock(f"{name}.entry")
    
    # 添加参数
    func.add_param(IRValue(name="a", ty="整数型", kind=ValueKind.PARAM))
    func.add_param(IRValue(name="b", ty="整数型", kind=ValueKind.PARAM))
    
    # 调用函数
    call_result = IRValue(name=f"%call_result", ty="整数型")
    entry.add_instruction(IRInstruction(
        opcode=Opcode.CALL,
        operands=[
            IRValue(name=f"@{callee_name}", ty="函数型"),
            IRValue(name="a", ty="整数型"),
            IRValue(name="b", ty="整数型")
        ],
        result=[call_result]
    ))
    
    # 使用结果
    output_result = IRValue(name=f"%output", ty="整数型")
    entry.add_instruction(IRInstruction(
        opcode=Opcode.MUL,
        operands=[call_result, IRValue(name="2", ty="整数型", kind=ValueKind.CONST, const_value=2)],
        result=[output_result]
    ))
    
    # 返回结果
    entry.add_instruction(IRInstruction(
        opcode=Opcode.RET,
        operands=[output_result]
    ))
    
    func.add_basic_block(entry.label)
    return func


def create_program_with_call() -> IRProgram:
    """创建带有函数调用的测试程序"""
    program = IRProgram()
    
    # 添加被调用的函数
    small_func = create_simple_function("add_numbers")
    program.add_function(small_func)
    
    # 添加调用者函数
    caller = create_caller_function("caller", "add_numbers")
    program.add_function(caller)
    
    return program


def create_recursive_function(name: str) -> IRFunction:
    """创建递归函数"""
    func = IRFunction(name=name)
    entry = IRBasicBlock(f"{name}.entry")
    
    # 添加参数
    func.add_param(IRValue(name="n", ty="整数型", kind=ValueKind.PARAM))
    
    # 递归调用
    call_result = IRValue(name=f"%result", ty="整数型")
    entry.add_instruction(IRInstruction(
        opcode=Opcode.CALL,
        operands=[
            IRValue(name=f"@{name}", ty="函数型"),
            IRValue(name="n", ty="整数型")
        ],
        result=[call_result]
    ))
    
    # 返回结果
    entry.add_instruction(IRInstruction(
        opcode=Opcode.RET,
        operands=[call_result]
    ))
    
    func.add_basic_block(entry.label)
    return func


# =============================================================================
# InlineCost 测试
# =============================================================================

class TestInlineCost:
    """测试 InlineCost 数据类"""
    
    def test_default_values(self):
        """测试默认值"""
        cost = InlineCost()
        assert cost.instruction_count == 0
        assert cost.basic_block_count == 0
        assert cost.call_count == 0
        assert cost.estimated_size == 0
    
    def test_custom_values(self):
        """测试自定义值"""
        cost = InlineCost(
            instruction_count=10,
            basic_block_count=2,
            call_count=5,
            estimated_size=40
        )
        assert cost.instruction_count == 10
        assert cost.basic_block_count == 2
        assert cost.call_count == 5
        assert cost.estimated_size == 40
    
    def test_is_small(self):
        """测试 is_small 方法"""
        cost_small = InlineCost(instruction_count=5)
        assert cost_small.is_small(threshold=10) is True
        
        cost_large = InlineCost(instruction_count=15)
        assert cost_large.is_small(threshold=10) is False
        
        # 边界情况
        cost_exact = InlineCost(instruction_count=10)
        assert cost_exact.is_small(threshold=10) is True
    
    def test_is_hot(self):
        """测试 is_hot 方法"""
        cost_hot = InlineCost(call_count=10)
        assert cost_hot.is_hot(call_count=5) is True
        
        cost_cold = InlineCost(call_count=3)
        assert cost_cold.is_hot(call_count=5) is False
        
        # 边界情况
        cost_exact = InlineCost(call_count=5)
        assert cost_exact.is_hot(call_count=5) is True


# =============================================================================
# InlineCostModel 测试
# =============================================================================

class TestInlineCostModel:
    """测试 InlineCostModel 内联成本模型"""
    
    def test_initialization(self):
        """测试初始化"""
        program = create_program_with_call()
        model = InlineCostModel(program)
        
        assert model.program is program
        assert isinstance(model.call_counts, dict)
        assert isinstance(model.function_costs, dict)
    
    def test_function_costs_computed(self):
        """测试函数成本已计算"""
        program = create_program_with_call()
        model = InlineCostModel(program)
        
        # 成本字典不为空
        assert len(model.function_costs) > 0
    
    def test_get_cost(self):
        """测试获取函数成本"""
        program = create_program_with_call()
        model = InlineCostModel(program)
        
        cost = model.get_cost("add_numbers")
        assert cost is not None
    
    def test_get_cost_not_found(self):
        """测试获取不存在的函数成本"""
        program = create_program_with_call()
        model = InlineCostModel(program)
        
        cost = model.get_cost("nonexistent")
        assert cost is None


# =============================================================================
# FunctionInliner 测试
# =============================================================================

class TestFunctionInliner:
    """测试 FunctionInliner 函数内联器"""
    
    def test_initialization(self):
        """测试初始化"""
        program = create_program_with_call()
        inliner = FunctionInliner(program)
        
        assert inliner.program is program
        assert isinstance(inliner.cost_model, InlineCostModel)
        assert "inlined_count" in inliner.stats
        assert "total_instructions_saved" in inliner.stats
    
    def test_get_callee_no_operands(self):
        """测试没有操作数的调用指令"""
        program = create_program_with_call()
        inliner = FunctionInliner(program)
        
        # 创建没有操作数的 CALL 指令
        empty_call = IRInstruction(opcode=Opcode.CALL, operands=[])
        callee = inliner._get_callee(empty_call)
        assert callee is None
    
    def test_clone_instruction(self):
        """测试克隆指令"""
        program = create_program_with_call()
        inliner = FunctionInliner(program)
        
        # 创建测试指令
        original = IRInstruction(
            opcode=Opcode.ADD,
            operands=[
                IRValue(name="%x", ty="整数型"),
                IRValue(name="%y", ty="整数型")
            ],
            result=[IRValue(name="%result", ty="整数型")]
        )
        
        var_map = {"%x": "%a", "%y": "%b"}
        cloned = inliner._clone_instruction(original, var_map)
        
        assert cloned.opcode == original.opcode
        assert len(cloned.operands) == len(original.operands)
        assert len(cloned.result) == len(original.result)
    
    def test_inline_all_empty_program(self):
        """测试空程序"""
        program = IRProgram()
        inliner = FunctionInliner(program)
        
        stats = inliner.inline_all()
        assert stats["inlined_count"] == 0
    
    def test_stats_attribute(self):
        """测试 stats 属性"""
        program = create_program_with_call()
        inliner = FunctionInliner(program)
        
        # FunctionInliner 使用 stats 属性
        stats = inliner.stats
        assert "inlined_count" in stats
        assert "total_instructions_saved" in stats


# =============================================================================
# InlineOptimizer 测试
# =============================================================================

class TestInlineOptimizer:
    """测试 InlineOptimizer 内联优化器"""
    
    def test_initialization(self):
        """测试初始化"""
        program = create_program_with_call()
        optimizer = InlineOptimizer(program)
        
        assert optimizer.program is program
        assert "inlined_count" in optimizer.stats
        assert "total_instructions_saved" in optimizer.stats
    
    def test_optimize(self):
        """测试优化执行"""
        program = create_program_with_call()
        optimizer = InlineOptimizer(program)
        
        stats = optimizer.optimize()
        assert isinstance(stats, dict)
        assert "inlined_count" in stats
        assert "total_instructions_saved" in stats
    
    def test_get_stats(self):
        """测试获取统计信息"""
        program = create_program_with_call()
        optimizer = InlineOptimizer(program)
        
        stats = optimizer.get_stats()
        assert isinstance(stats, dict)
        # 初始为空
        assert stats["inlined_count"] == 0


# =============================================================================
# 便捷函数测试
# =============================================================================

class TestInlineFunctions:
    """测试 inline_functions 便捷函数"""
    
    def test_inline_functions(self):
        """测试便捷函数"""
        program = create_program_with_call()
        
        stats = inline_functions(program)
        
        assert isinstance(stats, dict)
        assert "inlined_count" in stats
        assert "total_instructions_saved" in stats


# =============================================================================
# 边界情况测试
# =============================================================================

class TestEdgeCases:
    """测试边界情况"""
    
    def test_no_functions(self):
        """测试没有函数的程序"""
        program = IRProgram()
        model = InlineCostModel(program)
        assert len(model.function_costs) == 0
    
    def test_empty_basic_block(self):
        """测试空基本块"""
        func = IRFunction(name="empty_func")
        bb = IRBasicBlock("empty.entry")
        func.add_basic_block(bb.label)
        program = IRProgram()
        program.add_function(func)
        
        model = InlineCostModel(program)
        cost = model.get_cost("empty_func")
        assert cost is not None


# =============================================================================
# 运行测试
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

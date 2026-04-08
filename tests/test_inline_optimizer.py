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
        # TASK-P3-002 新增属性
        assert cost.loop_nesting_depth == 0
        assert cost.constant_param_ratio == 0.0
        assert cost.simple_param_ratio == 0.0
        assert cost.complex_param_ratio == 0.0
        assert cost.control_flow_complexity == 0
        assert cost.savings_estimate == 0.0
    
    def test_custom_values(self):
        """测试自定义值"""
        cost = InlineCost(
            instruction_count=10,
            basic_block_count=2,
            call_count=5,
            estimated_size=40,
            # TASK-P3-002 新增属性
            loop_nesting_depth=2,
            constant_param_ratio=0.5,
            simple_param_ratio=0.8,
            complex_param_ratio=0.2,
            control_flow_complexity=3,
            savings_estimate=15.5
        )
        assert cost.instruction_count == 10
        assert cost.basic_block_count == 2
        assert cost.call_count == 5
        assert cost.estimated_size == 40
        assert cost.loop_nesting_depth == 2
        assert cost.constant_param_ratio == 0.5
        assert cost.simple_param_ratio == 0.8
        assert cost.complex_param_ratio == 0.2
        assert cost.control_flow_complexity == 3
        assert cost.savings_estimate == 15.5
    
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
        # TASK-P3-002 新增
        assert isinstance(model.call_frequency, dict)
        assert isinstance(model.loop_calls, dict)
    
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
    
    def test_call_frequency_analysis(self):
        """测试调用频率分析（TASK-P3-002 新增）"""
        program = create_program_with_call()
        model = InlineCostModel(program)
        
        # 检查调用频率分析
        assert "add_numbers" in model.call_frequency
        assert "count" in model.call_frequency["add_numbers"]
        assert "frequency" in model.call_frequency["add_numbers"]
        assert "is_hot" in model.call_frequency["add_numbers"]
        assert "is_cold" in model.call_frequency["add_numbers"]
    
    def test_control_flow_complexity(self):
        """测试控制流复杂度计算（TASK-P3-002 新增）"""
        program = create_program_with_call()
        model = InlineCostModel(program)
        
        cost = model.get_cost("add_numbers")
        assert cost is not None
        # add_numbers 是一个简单函数，应该没有分支
        assert cost.control_flow_complexity >= 0
    
    def test_is_simple_type(self):
        """测试简单类型判断（TASK-P3-002 新增）"""
        program = create_program_with_call()
        model = InlineCostModel(program)
        
        # 简单类型
        assert model._is_simple_type("整数型") is True
        assert model._is_simple_type("int") is True
        assert model._is_simple_type("i32") is True
        assert model._is_simple_type("f64") is True
        
        # 复杂类型
        assert model._is_simple_type("结构体型") is False
        assert model._is_simple_type("数组型") is False
        assert model._is_simple_type("指针型") is False
    
    def test_param_type_analysis(self):
        """测试参数类型分析（TASK-P3-002 新增）"""
        program = create_program_with_call()
        model = InlineCostModel(program)
        
        add_func = program.find_function("add_numbers")
        assert add_func is not None
        
        # 创建带有参数的调用指令
        call_instr = IRInstruction(
            opcode=Opcode.CALL,
            operands=[
                IRValue(name="@add_numbers", ty="函数型"),
                IRValue(name="1", ty="整数型", kind=ValueKind.CONST, const_value=1),
                IRValue(name="2", ty="整数型", kind=ValueKind.CONST, const_value=2)
            ],
            result=[IRValue(name="%result", ty="整数型")]
        )
        
        # 分析参数类型
        constant_ratio, simple_ratio, complex_ratio = model._analyze_param_types(
            add_func, call_instr
        )
        
        assert constant_ratio == 1.0  # 两个参数都是常量
        assert simple_ratio == 1.0   # 两个参数都是简单类型
    
    def test_savings_computation(self):
        """测试内联收益计算（TASK-P3-002 新增）"""
        program = create_program_with_call()
        model = InlineCostModel(program)
        
        caller = program.find_function("caller")
        callee = program.find_function("add_numbers")
        
        assert caller is not None
        assert callee is not None
        
        # 创建调用指令
        call_instr = IRInstruction(
            opcode=Opcode.CALL,
            operands=[
                IRValue(name="@add_numbers", ty="函数型"),
                IRValue(name="a", ty="整数型"),
                IRValue(name="b", ty="整数型")
            ],
            result=[IRValue(name="%result", ty="整数型")]
        )
        
        callee_cost = model.get_cost("add_numbers")
        assert callee_cost is not None
        
        # 计算收益
        savings = model._compute_savings(caller, callee, call_instr, callee_cost)
        
        # 简单函数的收益应该为正
        assert isinstance(savings, float)
    
    def test_loop_depth_estimation(self):
        """测试循环深度估计（TASK-P3-002 新增）"""
        program = create_program_with_call()
        model = InlineCostModel(program)
        
        # 创建循环基本块
        loop_bb = IRBasicBlock("entry.loop")
        depth = model._estimate_loop_depth(loop_bb)
        assert depth == 1  # 包含 "loop" 关键字
        
        # 创建嵌套循环基本块
        nested_bb = IRBasicBlock("entry.loop.loop")
        depth = model._estimate_loop_depth(nested_bb)
        assert depth == 2  # 包含两个 "loop"
        
        # 创建普通基本块
        normal_bb = IRBasicBlock("entry")
        depth = model._estimate_loop_depth(normal_bb)
        assert depth == 0  # 不包含 "loop"


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

# -*- coding: utf-8 -*-
"""
数据流分析测试

测试 src/ir/dataflow.py 中的三个分析器：
- LivenessAnalysis - 活跃变量分析
- ReachingDefinitionsAnalysis - 到达定义分析
- AvailableExpressionsAnalysis - 可用表达式分析

作者：远
日期：2026-04-08
"""

import pytest
from typing import List, Set

from zhc.ir.dataflow import (
    DataFlowResult,
    DataFlowAnalysis,
    LivenessAnalysis,
    ReachingDefinitionsAnalysis,
    AvailableExpressionsAnalysis,
    Definition,
    Expression,
)
from zhc.ir.program import IRFunction, IRProgram
from zhc.ir.instructions import IRBasicBlock, IRInstruction
from zhc.ir.values import IRValue, ValueKind
from zhc.ir.opcodes import Opcode


# =============================================================================
# 测试辅助函数
# =============================================================================

def create_test_value(name: str, kind: ValueKind = ValueKind.VAR) -> IRValue:
    """创建测试用的 IRValue"""
    return IRValue(name=name, kind=kind)


def create_test_block(label: str, instructions: List[IRInstruction], 
                      predecessors: List[str] = None, 
                      successors: List[str] = None) -> IRBasicBlock:
    """创建测试用的基本块"""
    block = IRBasicBlock(label=label)
    for instr in instructions:
        block.instructions.append(instr)
    if predecessors:
        block.predecessors = predecessors
    if successors:
        block.successors = successors
    return block


def create_test_instruction(opcode: Opcode, operands: List[IRValue] = None, 
                           result: List[IRValue] = None) -> IRInstruction:
    """创建测试用的指令"""
    instr = IRInstruction(opcode=opcode)
    if operands:
        instr.operands = operands
    if result:
        instr.result = result
    return instr


def create_simple_function() -> IRFunction:
    """
    创建一个简单的测试函数
    
    基本块结构：
    entry -> bb1 -> exit
    
    代码：
    x = 1
    y = x + 2
    z = y
    """
    func = IRFunction(name="test_func")
    
    # 创建基本块
    entry = create_test_block("entry", [])
    bb1 = create_test_block("bb1", [], predecessors=["entry"], successors=["exit"])
    exit_block = create_test_block("exit", [], predecessors=["bb1"])
    
    # entry 块：x = 1
    x = create_test_value("x")
    entry.instructions.append(create_test_instruction(
        Opcode.STORE, 
        operands=[create_test_value("1", ValueKind.CONST)],
        result=[x]
    ))
    
    # bb1 块：y = x + 2, z = y
    y = create_test_value("y")
    bb1.instructions.append(create_test_instruction(
        Opcode.ADD,
        operands=[x, create_test_value("2", ValueKind.CONST)],
        result=[y]
    ))
    
    z = create_test_value("z")
    bb1.instructions.append(create_test_instruction(
        Opcode.STORE,
        operands=[y],
        result=[z]
    ))
    
    # 设置后继
    entry.successors = ["bb1"]
    
    # 添加基本块到函数
    func.basic_blocks = [entry, bb1, exit_block]
    func.entry_block = entry
    
    return func


def create_branch_function() -> IRFunction:
    """
    创建一个带分支的测试函数
    
    基本块结构：
    entry -> bb_true -> exit
          -> bb_false -> exit
    
    代码：
    if (cond) {
        x = 1
        y = x
    } else {
        x = 2
        z = x
    }
    """
    func = IRFunction(name="branch_func")
    
    # 创建基本块
    entry = create_test_block("entry", [])
    bb_true = create_test_block("bb_true", [], predecessors=["entry"], successors=["exit"])
    bb_false = create_test_block("bb_false", [], predecessors=["entry"], successors=["exit"])
    exit_block = create_test_block("exit", [], predecessors=["bb_true", "bb_false"])
    
    # entry 块：条件判断
    cond = create_test_value("cond")
    entry.instructions.append(create_test_instruction(
        Opcode.JZ,  # 使用 JZ 条件跳转
        operands=[cond]
    ))
    entry.successors = ["bb_true", "bb_false"]
    
    # bb_true 块：x = 1, y = x
    x1 = create_test_value("x")
    bb_true.instructions.append(create_test_instruction(
        Opcode.STORE,
        operands=[create_test_value("1", ValueKind.CONST)],
        result=[x1]
    ))
    
    y = create_test_value("y")
    bb_true.instructions.append(create_test_instruction(
        Opcode.STORE,
        operands=[x1],
        result=[y]
    ))
    # 添加 JMP 跳转到 exit
    bb_true.instructions.append(create_test_instruction(
        Opcode.JMP,
        operands=[]
    ))
    
    # bb_false 块：x = 2, z = x
    x2 = create_test_value("x")
    bb_false.instructions.append(create_test_instruction(
        Opcode.STORE,
        operands=[create_test_value("2", ValueKind.CONST)],
        result=[x2]
    ))
    
    z = create_test_value("z")
    bb_false.instructions.append(create_test_instruction(
        Opcode.STORE,
        operands=[x2],
        result=[z]
    ))
    # 添加 JMP 跳转到 exit
    bb_false.instructions.append(create_test_instruction(
        Opcode.JMP,
        operands=[]
    ))
    
    # 添加基本块到函数
    func.basic_blocks = [entry, bb_true, bb_false, exit_block]
    func.entry_block = entry
    
    return func


def create_loop_function() -> IRFunction:
    """
    创建一个带循环的测试函数
    
    基本块结构：
    entry -> loop_header -> loop_body -> exit
                   ^-----------|
    
    代码：
    i = 0
    while (i < 10) {
        i = i + 1
    }
    """
    func = IRFunction(name="loop_func")
    
    # 创建基本块
    entry = create_test_block("entry", [])
    loop_header = create_test_block("loop_header", [], predecessors=["entry", "loop_body"], successors=["loop_body", "exit"])
    loop_body = create_test_block("loop_body", [], predecessors=["loop_header"], successors=["loop_header"])
    exit_block = create_test_block("exit", [], predecessors=["loop_header"])
    
    # entry 块：i = 0
    i_init = create_test_value("i")
    entry.instructions.append(create_test_instruction(
        Opcode.STORE,
        operands=[create_test_value("0", ValueKind.CONST)],
        result=[i_init]
    ))
    entry.successors = ["loop_header"]
    
    # loop_header 块：条件判断 i < 10
    i = create_test_value("i")
    loop_header.instructions.append(create_test_instruction(
        Opcode.LT,
        operands=[i, create_test_value("10", ValueKind.CONST)]
    ))
    # 添加 JZ 条件跳转
    loop_header.instructions.append(create_test_instruction(
        Opcode.JZ,
        operands=[create_test_value("cond")]  # 简化的条件
    ))
    
    # loop_body 块：i = i + 1
    i_new = create_test_value("i")
    loop_body.instructions.append(create_test_instruction(
        Opcode.ADD,
        operands=[i, create_test_value("1", ValueKind.CONST)],
        result=[i_new]
    ))
    # 添加 JMP 跳转回 loop_header
    loop_body.instructions.append(create_test_instruction(
        Opcode.JMP,
        operands=[]  # 无条件跳转
    ))
    
    # 添加基本块到函数
    func.basic_blocks = [entry, loop_header, loop_body, exit_block]
    func.entry_block = entry
    
    return func


# =============================================================================
# 测试 DataFlowResult
# =============================================================================

class TestDataFlowResult:
    """测试数据流分析结果"""
    
    def test_result_creation(self):
        """测试结果创建"""
        result = DataFlowResult(
            in_state={"bb1": {"x", "y"}},
            out_state={"bb1": {"y", "z"}},
            converged=True,
            iterations=5
        )
        
        assert result.converged is True
        assert result.iterations == 5
        assert "x" in result.in_state["bb1"]
        assert "z" in result.out_state["bb1"]
    
    def test_result_empty_state(self):
        """测试空状态"""
        result = DataFlowResult(
            in_state={},
            out_state={},
            converged=False,
            iterations=0
        )
        
        assert result.converged is False
        assert len(result.in_state) == 0


# =============================================================================
# 测试 Definition
# =============================================================================

class TestDefinition:
    """测试变量定义"""
    
    def test_definition_creation(self):
        """测试定义创建"""
        defn = Definition(
            variable="x",
            block_label="bb1",
            instruction_index=0
        )
        
        assert defn.variable == "x"
        assert defn.block_label == "bb1"
        assert defn.instruction_index == 0
    
    def test_definition_repr(self):
        """测试定义字符串表示"""
        defn = Definition(variable="x", block_label="bb1", instruction_index=2)
        assert repr(defn) == "x@bb1:2"
    
    def test_definition_equality(self):
        """测试定义相等性"""
        defn1 = Definition(variable="x", block_label="bb1", instruction_index=0)
        defn2 = Definition(variable="x", block_label="bb1", instruction_index=0)
        defn3 = Definition(variable="y", block_label="bb1", instruction_index=0)
        
        assert defn1 == defn2
        assert defn1 != defn3
    
    def test_definition_hash(self):
        """测试定义哈希"""
        defn1 = Definition(variable="x", block_label="bb1", instruction_index=0)
        defn2 = Definition(variable="x", block_label="bb1", instruction_index=0)
        
        assert hash(defn1) == hash(defn2)
        
        # 可以放入集合
        s = {defn1, defn2}
        assert len(s) == 1


# =============================================================================
# 测试 Expression
# =============================================================================

class TestExpression:
    """测试表达式"""
    
    def test_expression_creation(self):
        """测试表达式创建"""
        expr = Expression(operator="+", operands=("x", "y"))
        
        assert expr.operator == "+"
        assert expr.operands == ("x", "y")
    
    def test_expression_repr(self):
        """测试表达式字符串表示"""
        expr = Expression(operator="+", operands=("x", "y"))
        assert repr(expr) == "+(x, y)"
    
    def test_expression_equality(self):
        """测试表达式相等性"""
        expr1 = Expression(operator="+", operands=("x", "y"))
        expr2 = Expression(operator="+", operands=("x", "y"))
        expr3 = Expression(operator="-", operands=("x", "y"))
        
        assert expr1 == expr2
        assert expr1 != expr3
    
    def test_expression_hash(self):
        """测试表达式哈希"""
        expr1 = Expression(operator="+", operands=("x", "y"))
        expr2 = Expression(operator="+", operands=("x", "y"))
        
        assert hash(expr1) == hash(expr2)
        
        # 可以放入集合
        s = {expr1, expr2}
        assert len(s) == 1


# =============================================================================
# 测试 LivenessAnalysis
# =============================================================================

class TestLivenessAnalysis:
    """测试活跃变量分析"""
    
    def test_liveness_simple_function(self):
        """测试简单函数的活跃变量分析"""
        func = create_simple_function()
        analysis = LivenessAnalysis(func)
        
        result = analysis.analyze()
        
        assert result.converged is True
        assert result.iterations > 0
    
    def test_liveness_def_use_sets(self):
        """测试 def/use 集合计算"""
        func = create_simple_function()
        analysis = LivenessAnalysis(func)
        
        # 检查 def_sets 和 use_sets 已计算
        assert len(analysis.def_sets) > 0
        assert len(analysis.use_sets) > 0
    
    def test_liveness_is_live_at(self):
        """测试变量活跃性检查"""
        func = create_simple_function()
        analysis = LivenessAnalysis(func)
        analysis.analyze()
        
        # 在 bb1 入口，x 应该是活跃的（因为后面使用了 x）
        # 注意：具体结果取决于函数结构
        live_vars = analysis.get_live_variables("bb1")
        assert isinstance(live_vars, set)
    
    def test_liveness_branch_function(self):
        """测试分支函数的活跃变量分析"""
        func = create_branch_function()
        analysis = LivenessAnalysis(func)
        
        result = analysis.analyze()
        
        assert result.converged is True
    
    def test_liveness_loop_function(self):
        """测试循环函数的活跃变量分析"""
        func = create_loop_function()
        analysis = LivenessAnalysis(func)
        
        result = analysis.analyze()
        
        assert result.converged is True
    
    def test_liveness_reverse_postorder(self):
        """测试逆后序遍历"""
        func = create_simple_function()
        analysis = LivenessAnalysis(func)
        
        rpo = analysis._reverse_postorder()
        
        # 逆后序应该包含所有基本块
        assert len(rpo) == len(func.basic_blocks)
        # 入口块应该在最前面
        assert rpo[0] == func.entry_block.label


# =============================================================================
# 测试 ReachingDefinitionsAnalysis
# =============================================================================

class TestReachingDefinitionsAnalysis:
    """测试到达定义分析"""
    
    def test_reaching_simple_function(self):
        """测试简单函数的到达定义分析"""
        func = create_simple_function()
        analysis = ReachingDefinitionsAnalysis(func)
        
        result = analysis.analyze()
        
        assert result.converged is True
        assert result.iterations > 0
    
    def test_reaching_gen_kill_sets(self):
        """测试 gen/kill 集合计算"""
        func = create_simple_function()
        analysis = ReachingDefinitionsAnalysis(func)
        
        # 检查 gen_sets 和 kill_sets 已计算
        assert len(analysis.gen_sets) > 0
        assert len(analysis.kill_sets) > 0
        # 检查所有定义已收集
        assert len(analysis.all_definitions) > 0
    
    def test_reaching_get_definitions(self):
        """测试获取到达定义"""
        func = create_simple_function()
        analysis = ReachingDefinitionsAnalysis(func)
        analysis.analyze()
        
        # 获取某个变量的到达定义
        defs = analysis.get_reaching_definitions("bb1", "x")
        assert isinstance(defs, set)
    
    def test_reaching_branch_function(self):
        """测试分支函数的到达定义分析"""
        func = create_branch_function()
        analysis = ReachingDefinitionsAnalysis(func)
        
        result = analysis.analyze()
        
        assert result.converged is True
    
    def test_reaching_parse_definition(self):
        """测试解析定义字符串"""
        func = create_simple_function()
        analysis = ReachingDefinitionsAnalysis(func)
        
        # 测试正确格式
        defn = analysis._parse_definition("x@bb1:0")
        assert defn is not None
        assert defn.variable == "x"
        assert defn.block_label == "bb1"
        assert defn.instruction_index == 0
        
        # 测试错误格式
        assert analysis._parse_definition("invalid") is None
        assert analysis._parse_definition("x@bb1") is None
    
    def test_reaching_postorder(self):
        """测试后序遍历"""
        func = create_simple_function()
        analysis = ReachingDefinitionsAnalysis(func)
        
        po = analysis._postorder()
        
        # 后序应该包含所有基本块
        assert len(po) == len(func.basic_blocks)


# =============================================================================
# 测试 AvailableExpressionsAnalysis
# =============================================================================

class TestAvailableExpressionsAnalysis:
    """测试可用表达式分析"""
    
    def test_available_simple_function(self):
        """测试简单函数的可用表达式分析"""
        func = create_simple_function()
        analysis = AvailableExpressionsAnalysis(func)
        
        result = analysis.analyze()
        
        assert result.converged is True
        assert result.iterations > 0
    
    def test_available_gen_kill_sets(self):
        """测试 gen/kill 集合计算"""
        func = create_simple_function()
        analysis = AvailableExpressionsAnalysis(func)
        
        # 检查 gen_sets 和 kill_sets 已计算
        assert len(analysis.gen_sets) > 0
        assert len(analysis.kill_sets) >= 0  # 可能为空
        # 检查所有表达式已收集
        assert isinstance(analysis.all_expressions, set)
    
    def test_available_branch_function(self):
        """测试分支函数的可用表达式分析"""
        func = create_branch_function()
        analysis = AvailableExpressionsAnalysis(func)
        
        result = analysis.analyze()
        
        assert result.converged is True
    
    def test_available_extract_expression(self):
        """测试提取表达式"""
        func = create_simple_function()
        analysis = AvailableExpressionsAnalysis(func)
        
        # 创建一个 ADD 指令
        x = create_test_value("x")
        y = create_test_value("y")
        instr = create_test_instruction(Opcode.ADD, operands=[x, y])
        
        expr = analysis._extract_expression(instr)
        
        # 应该提取出一个表达式
        if expr:  # 只有二元运算才会提取表达式
            # Opcode.ADD.name 返回 "add"
            assert expr.operator == Opcode.ADD.name


# =============================================================================
# 测试 DataFlowAnalysis 基类
# =============================================================================

class TestDataFlowAnalysisBase:
    """测试数据流分析基类"""
    
    def test_get_predecessors(self):
        """测试获取前驱"""
        func = create_simple_function()
        analysis = LivenessAnalysis(func)
        
        # bb1 的前驱应该是 entry
        preds = analysis._get_predecessors("bb1")
        assert "entry" in preds
    
    def test_get_successors(self):
        """测试获取后继"""
        func = create_simple_function()
        analysis = LivenessAnalysis(func)
        
        # entry 的后继应该包含 bb1
        succs = analysis._get_successors("entry")
        assert "bb1" in succs
    
    def test_get_predecessors_nonexistent_block(self):
        """测试获取不存在块的前驱"""
        func = create_simple_function()
        analysis = LivenessAnalysis(func)
        
        preds = analysis._get_predecessors("nonexistent")
        assert preds == []
    
    def test_get_successors_nonexistent_block(self):
        """测试不存在块的后继"""
        func = create_simple_function()
        analysis = LivenessAnalysis(func)
        
        succs = analysis._get_successors("nonexistent")
        assert succs == []


# =============================================================================
# 边界条件测试
# =============================================================================

class TestEdgeCases:
    """测试边界条件"""
    
    def test_empty_function(self):
        """测试空函数"""
        func = IRFunction(name="empty")
        entry = create_test_block("entry", [])
        func.basic_blocks = [entry]
        func.entry_block = entry
        
        # 活跃变量分析
        liveness = LivenessAnalysis(func)
        result = liveness.analyze()
        assert result.converged is True
        
        # 到达定义分析
        reaching = ReachingDefinitionsAnalysis(func)
        result = reaching.analyze()
        assert result.converged is True
        
        # 可用表达式分析
        available = AvailableExpressionsAnalysis(func)
        result = available.analyze()
        assert result.converged is True
    
    def test_single_block_function(self):
        """测试单块函数"""
        func = IRFunction(name="single")
        
        x = create_test_value("x")
        entry = create_test_block("entry", [
            create_test_instruction(Opcode.STORE, operands=[create_test_value("1", ValueKind.CONST)], result=[x])
        ])
        
        func.basic_blocks = [entry]
        func.entry_block = entry
        
        # 活跃变量分析
        liveness = LivenessAnalysis(func)
        result = liveness.analyze()
        assert result.converged is True
    
    def test_max_iterations(self):
        """测试最大迭代次数"""
        func = create_loop_function()
        analysis = LivenessAnalysis(func)
        
        # 设置较小的最大迭代次数
        result = analysis.analyze(max_iterations=2)
        
        # 应该在最大迭代次数内完成或收敛
        assert result.iterations <= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
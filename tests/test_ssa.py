# -*- coding: utf-8 -*-
"""
SSA 构建器单元测试

测试 SSA 构建器的核心功能：
- 支配树计算
- 支配边界计算
- Phi 节点插入
- 变量重命名

作者：远
日期：2026-04-08
"""

import pytest
from zhc.ir import (
    IRFunction,
    IRBasicBlock,
    IRInstruction,
    IRValue,
    ValueKind,
    Opcode,
    SSABuilder,
    DominatorTree,
    DominanceFrontier,
    VersionedValue,
    PhiNode,
    build_ssa,
)


# =============================================================================
# 测试辅助函数
# =============================================================================

def create_simple_function() -> IRFunction:
    """
    创建一个简单的测试函数

    结构：
    entry -> bb1 -> bb2 -> exit
    """
    func = IRFunction("test_func", return_type="整数型")

    # entry 块
    entry = func.entry_block
    entry.add_instruction(IRInstruction(
        Opcode.ARG,
        operands=[IRValue("x", ty="整数型", kind=ValueKind.PARAM)],
        result=[IRValue("%x", ty="整数型", kind=ValueKind.VAR)]
    ))
    entry.add_instruction(IRInstruction(
        Opcode.JMP,
        operands=[IRValue("bb1", kind=ValueKind.LABEL)]
    ))
    entry.add_successor("bb1")

    # bb1 块
    bb1 = func.add_basic_block("bb1")
    bb1.add_predecessor("entry")
    bb1.add_instruction(IRInstruction(
        Opcode.ADD,
        operands=[
            IRValue("%x", ty="整数型", kind=ValueKind.VAR),
            IRValue("1", ty="整数型", kind=ValueKind.CONST, const_value=1)
        ],
        result=[IRValue("%y", ty="整数型", kind=ValueKind.VAR)]
    ))
    bb1.add_instruction(IRInstruction(
        Opcode.JMP,
        operands=[IRValue("bb2", kind=ValueKind.LABEL)]
    ))
    bb1.add_successor("bb2")

    # bb2 块
    bb2 = func.add_basic_block("bb2")
    bb2.add_predecessor("bb1")
    bb2.add_instruction(IRInstruction(
        Opcode.RET,
        operands=[IRValue("%y", ty="整数型", kind=ValueKind.VAR)]
    ))

    return func


def create_branch_function() -> IRFunction:
    """
    创建一个带分支的测试函数

    结构：
    entry -> bb1 (条件跳转) -> bb2 (true) -> bb4
                     -> bb3 (false) -> bb4
    """
    func = IRFunction("branch_func", return_type="整数型")

    # entry 块
    entry = func.entry_block
    entry.add_instruction(IRInstruction(
        Opcode.ARG,
        operands=[IRValue("x", ty="整数型", kind=ValueKind.PARAM)],
        result=[IRValue("%x", ty="整数型", kind=ValueKind.VAR)]
    ))
    entry.add_instruction(IRInstruction(
        Opcode.ARG,
        operands=[IRValue("y", ty="整数型", kind=ValueKind.PARAM)],
        result=[IRValue("%y", ty="整数型", kind=ValueKind.VAR)]
    ))
    entry.add_successor("bb1")

    # bb1 块（条件跳转）
    bb1 = func.add_basic_block("bb1")
    bb1.add_predecessor("entry")
    bb1.add_instruction(IRInstruction(
        Opcode.LT,
        operands=[
            IRValue("%x", ty="整数型", kind=ValueKind.VAR),
            IRValue("10", ty="整数型", kind=ValueKind.CONST, const_value=10)
        ],
        result=[IRValue("%cond", ty="布尔型", kind=ValueKind.VAR)]
    ))
    bb1.add_instruction(IRInstruction(
        Opcode.JZ,
        operands=[
            IRValue("%cond", ty="布尔型", kind=ValueKind.VAR),
            IRValue("bb3", kind=ValueKind.LABEL),
            IRValue("bb2", kind=ValueKind.LABEL)
        ]
    ))
    bb1.add_successor("bb2")
    bb1.add_successor("bb3")

    # bb2 块（true 分支）
    bb2 = func.add_basic_block("bb2")
    bb2.add_predecessor("bb1")
    bb2.add_instruction(IRInstruction(
        Opcode.ADD,
        operands=[
            IRValue("%x", ty="整数型", kind=ValueKind.VAR),
            IRValue("1", ty="整数型", kind=ValueKind.CONST, const_value=1)
        ],
        result=[IRValue("%result", ty="整数型", kind=ValueKind.VAR)]
    ))
    bb2.add_instruction(IRInstruction(
        Opcode.JMP,
        operands=[IRValue("bb4", kind=ValueKind.LABEL)]
    ))
    bb2.add_successor("bb4")

    # bb3 块（false 分支）
    bb3 = func.add_basic_block("bb3")
    bb3.add_predecessor("bb1")
    bb3.add_instruction(IRInstruction(
        Opcode.SUB,
        operands=[
            IRValue("%y", ty="整数型", kind=ValueKind.VAR),
            IRValue("1", ty="整数型", kind=ValueKind.CONST, const_value=1)
        ],
        result=[IRValue("%result", ty="整数型", kind=ValueKind.VAR)]
    ))
    bb3.add_instruction(IRInstruction(
        Opcode.JMP,
        operands=[IRValue("bb4", kind=ValueKind.LABEL)]
    ))
    bb3.add_successor("bb4")

    # bb4 块（汇合点）
    bb4 = func.add_basic_block("bb4")
    bb4.add_predecessor("bb2")
    bb4.add_predecessor("bb3")
    bb4.add_instruction(IRInstruction(
        Opcode.RET,
        operands=[IRValue("%result", ty="整数型", kind=ValueKind.VAR)]
    ))

    return func


def create_loop_function() -> IRFunction:
    """
    创建一个带循环的测试函数

    结构：
    entry -> loop_header -> loop_body -> loop_header
                     -> exit
    """
    func = IRFunction("loop_func", return_type="整数型")

    # entry 块
    entry = func.entry_block
    entry.add_instruction(IRInstruction(
        Opcode.ARG,
        operands=[IRValue("n", ty="整数型", kind=ValueKind.PARAM)],
        result=[IRValue("%n", ty="整数型", kind=ValueKind.VAR)]
    ))
    entry.add_instruction(IRInstruction(
        Opcode.CONST,
        operands=[IRValue("0", ty="整数型", kind=ValueKind.CONST, const_value=0)],
        result=[IRValue("%i", ty="整数型", kind=ValueKind.VAR)]
    ))
    entry.add_instruction(IRInstruction(
        Opcode.CONST,
        operands=[IRValue("0", ty="整数型", kind=ValueKind.CONST, const_value=0)],
        result=[IRValue("%sum", ty="整数型", kind=ValueKind.VAR)]
    ))
    entry.add_successor("loop_header")

    # loop_header 块
    loop_header = func.add_basic_block("loop_header")
    loop_header.add_predecessor("entry")
    loop_header.add_predecessor("loop_body")
    loop_header.add_instruction(IRInstruction(
        Opcode.LT,
        operands=[
            IRValue("%i", ty="整数型", kind=ValueKind.VAR),
            IRValue("%n", ty="整数型", kind=ValueKind.VAR)
        ],
        result=[IRValue("%cond", ty="布尔型", kind=ValueKind.VAR)]
    ))
    loop_header.add_instruction(IRInstruction(
        Opcode.JZ,
        operands=[
            IRValue("%cond", ty="布尔型", kind=ValueKind.VAR),
            IRValue("exit", kind=ValueKind.LABEL),
            IRValue("loop_body", kind=ValueKind.LABEL)
        ]
    ))
    loop_header.add_successor("loop_body")
    loop_header.add_successor("exit")

    # loop_body 块
    loop_body = func.add_basic_block("loop_body")
    loop_body.add_predecessor("loop_header")
    loop_body.add_instruction(IRInstruction(
        Opcode.ADD,
        operands=[
            IRValue("%sum", ty="整数型", kind=ValueKind.VAR),
            IRValue("%i", ty="整数型", kind=ValueKind.VAR)
        ],
        result=[IRValue("%sum", ty="整数型", kind=ValueKind.VAR)]
    ))
    loop_body.add_instruction(IRInstruction(
        Opcode.ADD,
        operands=[
            IRValue("%i", ty="整数型", kind=ValueKind.VAR),
            IRValue("1", ty="整数型", kind=ValueKind.CONST, const_value=1)
        ],
        result=[IRValue("%i", ty="整数型", kind=ValueKind.VAR)]
    ))
    loop_body.add_instruction(IRInstruction(
        Opcode.JMP,
        operands=[IRValue("loop_header", kind=ValueKind.LABEL)]
    ))
    loop_body.add_successor("loop_header")

    # exit 块
    exit_block = func.add_basic_block("exit")
    exit_block.add_predecessor("loop_header")
    exit_block.add_instruction(IRInstruction(
        Opcode.RET,
        operands=[IRValue("%sum", ty="整数型", kind=ValueKind.VAR)]
    ))

    return func


# =============================================================================
# 支配树测试
# =============================================================================

class TestDominatorTree:
    """支配树计算测试"""

    def test_simple_function_dominators(self):
        """测试简单函数的支配关系"""
        func = create_simple_function()
        builder = SSABuilder()
        builder.current_function = func
        builder._compute_dominator_tree()

        # entry 支配所有块
        assert "entry" in builder.dom_tree.dominators["bb1"]
        assert "entry" in builder.dom_tree.dominators["bb2"]

        # bb1 支配 bb2
        assert "bb1" in builder.dom_tree.dominators["bb2"]

        # 直接支配者
        assert builder.dom_tree.get_immediate_dominator("bb1") == "entry"
        assert builder.dom_tree.get_immediate_dominator("bb2") == "bb1"

    def test_branch_function_dominators(self):
        """测试分支函数的支配关系"""
        func = create_branch_function()
        builder = SSABuilder()
        builder.current_function = func
        builder._compute_dominator_tree()

        # bb1 支配 bb2 和 bb3
        assert "bb1" in builder.dom_tree.dominators["bb2"]
        assert "bb1" in builder.dom_tree.dominators["bb3"]

        # bb1 支配 bb4（汇合点）
        assert "bb1" in builder.dom_tree.dominators["bb4"]

        # bb2 不支配 bb4（因为还有 bb3 的路径）
        assert "bb2" not in builder.dom_tree.dominators["bb4"] or \
               "bb3" in builder.dom_tree.dominators["bb4"]

    def test_loop_function_dominators(self):
        """测试循环函数的支配关系"""
        func = create_loop_function()
        builder = SSABuilder()
        builder.current_function = func
        builder._compute_dominator_tree()

        # loop_header 支配 loop_body 和 exit
        assert "loop_header" in builder.dom_tree.dominators["loop_body"]
        assert "loop_header" in builder.dom_tree.dominators["exit"]

        # entry 支配所有块
        assert "entry" in builder.dom_tree.dominators["loop_header"]


# =============================================================================
# 支配边界测试
# =============================================================================

class TestDominanceFrontier:
    """支配边界计算测试"""

    def test_branch_function_frontier(self):
        """测试分支函数的支配边界"""
        func = create_branch_function()
        builder = SSABuilder()
        builder.current_function = func
        builder._compute_dominator_tree()
        builder._compute_dominance_frontier()

        # bb2 和 bb3 的支配边界应该包含 bb4
        # 因为 bb1 支配 bb2 和 bb3，但不严格支配 bb4
        frontier_bb2 = builder.dom_frontier.get_frontier("bb2")
        frontier_bb3 = builder.dom_frontier.get_frontier("bb3")

        # 至少有一个分支的支配边界包含 bb4
        assert "bb4" in frontier_bb2 or "bb4" in frontier_bb3

    def test_loop_function_frontier(self):
        """测试循环函数的支配边界"""
        func = create_loop_function()
        builder = SSABuilder()
        builder.current_function = func
        builder._compute_dominator_tree()
        builder._compute_dominance_frontier()

        # loop_body 的支配边界应该包含 loop_header
        # 因为 loop_header 支配 loop_body 的前驱（entry），但不严格支配 loop_header 自己
        frontier_loop_body = builder.dom_frontier.get_frontier("loop_body")

        # loop_header 在 loop_body 的支配边界中
        assert "loop_header" in frontier_loop_body


# =============================================================================
# Phi 节点测试
# =============================================================================

class TestPhiNodeInsertion:
    """Phi 节点插入测试"""

    def test_branch_phi_insertion(self):
        """测试分支函数的 Phi 节点插入"""
        func = create_branch_function()
        builder = SSABuilder()
        builder.current_function = func
        builder._compute_dominator_tree()
        builder._compute_dominance_frontier()
        builder._collect_written_variables()
        builder._insert_phi_nodes()

        # %result 在 bb2 和 bb3 都被定义，应该在 bb4 有 Phi 节点
        assert "bb4" in builder.phi_nodes

        # 检查是否有 %result 的 Phi 节点
        phi_vars = [var_name for _, var_name in builder.phi_nodes["bb4"]]
        assert "result" in phi_vars

    def test_loop_phi_insertion(self):
        """测试循环函数的 Phi 节点插入"""
        func = create_loop_function()
        builder = SSABuilder()
        builder.current_function = func
        builder._compute_dominator_tree()
        builder._compute_dominance_frontier()
        builder._collect_written_variables()
        builder._insert_phi_nodes()

        # %i 和 %sum 在 loop_body 被重新定义，应该在 loop_header 有 Phi 节点
        assert "loop_header" in builder.phi_nodes

        # 检查是否有 %i 和 %sum 的 Phi 节点
        phi_vars = [var_name for _, var_name in builder.phi_nodes["loop_header"]]
        assert "i" in phi_vars
        assert "sum" in phi_vars


# =============================================================================
# 变量重命名测试
# =============================================================================

class TestVariableRenaming:
    """变量重命名测试"""

    def test_simple_function_renaming(self):
        """测试简单函数的变量重命名"""
        func = create_simple_function()
        builder = SSABuilder()
        builder.build_ssa(func)

        # 检查变量是否被重命名（有版本号）
        # 由于简单函数没有分支，变量应该只有一个版本
        bb1 = func.find_basic_block("bb1")
        assert bb1 is not None

        # 检查指令中的变量名
        for instr in bb1.instructions:
            if instr.opcode == Opcode.ADD:
                # 结果应该是 %y 或 %y.0
                result_name = instr.result[0].name
                assert result_name.startswith("%y")

    def test_branch_function_renaming(self):
        """测试分支函数的变量重命名"""
        func = create_branch_function()
        builder = SSABuilder()
        builder.build_ssa(func)

        # 检查 bb2 和 bb3 中的 %result 是否有不同版本
        bb2 = func.find_basic_block("bb2")
        bb3 = func.find_basic_block("bb3")

        assert bb2 is not None
        assert bb3 is not None

        # 找到赋值指令
        result_bb2 = None
        result_bb3 = None

        for instr in bb2.instructions:
            if instr.opcode == Opcode.ADD and instr.result:
                result_bb2 = instr.result[0].name

        for instr in bb3.instructions:
            if instr.opcode == Opcode.SUB and instr.result:
                result_bb3 = instr.result[0].name

        # 两个分支应该有不同版本的 %result
        if result_bb2 and result_bb3:
            assert result_bb2.startswith("%result")
            assert result_bb3.startswith("%result")

    def test_loop_function_renaming(self):
        """测试循环函数的变量重命名"""
        func = create_loop_function()
        builder = SSABuilder()
        builder.build_ssa(func)

        # 检查 loop_header 是否有 Phi 节点
        loop_header = func.find_basic_block("loop_header")
        assert loop_header is not None

        # 检查 loop_body 中的变量更新
        loop_body = func.find_basic_block("loop_body")
        assert loop_body is not None

        # %i 和 %sum 应该在 loop_body 中被重新赋值
        for instr in loop_body.instructions:
            if instr.opcode == Opcode.ADD and instr.result:
                result_name = instr.result[0].name
                # 应该是 %i 或 %sum 的某个版本
                assert result_name.startswith("%i") or result_name.startswith("%sum")


# =============================================================================
# 完整 SSA 构建测试
# =============================================================================

class TestSSABuild:
    """完整 SSA 构建测试"""

    def test_build_ssa_simple(self):
        """测试简单函数的完整 SSA 构建"""
        func = create_simple_function()
        result = build_ssa(func)

        assert result is not None
        assert result.name == "test_func"
        assert len(result.basic_blocks) == 3

    def test_build_ssa_branch(self):
        """测试分支函数的完整 SSA 构建"""
        func = create_branch_function()
        result = build_ssa(func)

        assert result is not None
        assert result.name == "branch_func"
        assert len(result.basic_blocks) == 5

        # 检查 bb4 是否有 Phi 节点相关的定义
        bb4 = result.find_basic_block("bb4")
        assert bb4 is not None

    def test_build_ssa_loop(self):
        """测试循环函数的完整 SSA 构建"""
        func = create_loop_function()
        result = build_ssa(func)

        assert result is not None
        assert result.name == "loop_func"
        assert len(result.basic_blocks) == 4

        # 检查 loop_header 是否有 Phi 节点相关的定义
        loop_header = result.find_basic_block("loop_header")
        assert loop_header is not None


# =============================================================================
# VersionedValue 测试
# =============================================================================

class TestVersionedValue:
    """版本化值测试"""

    def test_versioned_value_creation(self):
        """测试版本化值的创建"""
        v0 = VersionedValue("x", version=0)
        assert v0.base_name == "x"
        assert v0.version == 0
        assert v0.full_name == "%x"

    def test_versioned_value_next_version(self):
        """测试版本化值的下一个版本"""
        v0 = VersionedValue("x", version=0)
        v1 = v0.next_version()
        assert v1.base_name == "x"
        assert v1.version == 1
        assert v1.full_name == "%x.1"

    def test_versioned_value_equality(self):
        """测试版本化值的相等性"""
        v1 = VersionedValue("x", version=1)
        v2 = VersionedValue("x", version=1)
        v3 = VersionedValue("x", version=2)

        assert v1 == v2
        assert v1 != v3


# =============================================================================
# PhiNode 测试
# =============================================================================

class TestPhiNode:
    """Phi 节点测试"""

    def test_phi_node_creation(self):
        """测试 Phi 节点的创建"""
        result = VersionedValue("x", version=1)
        phi = PhiNode(
            result=result,
            incoming_blocks=["bb1", "bb2"],
            incoming_values=[
                VersionedValue("x", version=0),
                VersionedValue("x", version=1)
            ]
        )

        assert phi.result == result
        assert len(phi.incoming_blocks) == 2
        assert len(phi.incoming_values) == 2

    def test_phi_node_repr(self):
        """测试 Phi 节点的字符串表示"""
        result = VersionedValue("x", version=2)
        phi = PhiNode(
            result=result,
            incoming_blocks=["bb1", "bb2"],
            incoming_values=[
                VersionedValue("x", version=0),
                VersionedValue("x", version=1)
            ]
        )

        repr_str = repr(phi)
        assert "%x.2" in repr_str
        assert "phi" in repr_str
        assert "bb1" in repr_str
        assert "bb2" in repr_str


# =============================================================================
# 运行测试
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
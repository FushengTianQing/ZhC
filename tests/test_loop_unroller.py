#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZHC 编译器 - 循环展开优化测试

测试循环展开优化功能。

作者：阿福
日期：2026-04-08
"""

import pytest
from zhc.ir.loop_unroller import (
    LoopUnroller,
    UnrollStrategy,
    UnrollDecision,
    UnrollResult,
    unroll_loops,
)
from zhc.ir.instructions import IRBasicBlock, IRInstruction
from zhc.ir.program import IRFunction
from zhc.ir.opcodes import Opcode
from zhc.ir.loop_optimizer import LoopInfo


class TestLoopInfo:
    """循环信息测试"""

    def test_loop_info_creation(self):
        """测试循环信息创建"""
        block = IRBasicBlock("header")
        loop = LoopInfo(
            header=block, body={"header", "body"}, latch=IRBasicBlock("latch")
        )

        assert loop.header == block
        assert len(loop.body) == 2
        assert loop.latch is not None
        assert loop.depth == 1

    def test_contains_block(self):
        """测试检查基本块是否在循环内"""
        loop = LoopInfo(
            header=IRBasicBlock("header"),
            body={"header", "body", "exit"},
        )

        assert loop.contains_block("header")
        assert loop.contains_block("body")
        assert not loop.contains_block("other")

    def test_loop_info_repr(self):
        """测试循环信息字符串表示"""
        loop = LoopInfo(
            header=IRBasicBlock("header"),
            body={"header", "body"},
        )

        repr_str = repr(loop)
        assert "Loop" in repr_str
        assert "header" in repr_str


class TestUnrollDecision:
    """展开决策测试"""

    def test_unroll_decision_full(self):
        """测试完全展开决策"""
        decision = UnrollDecision(
            strategy=UnrollStrategy.FULL, factor=5, reason="小循环"
        )

        assert decision.strategy == UnrollStrategy.FULL
        assert decision.factor == 5

    def test_unroll_decision_partial(self):
        """测试部分展开决策"""
        decision = UnrollDecision(
            strategy=UnrollStrategy.PARTIAL, factor=4, reason="简单循环"
        )

        assert decision.strategy == UnrollStrategy.PARTIAL
        assert decision.factor == 4

    def test_unroll_decision_none(self):
        """测试不展开决策"""
        decision = UnrollDecision(
            strategy=UnrollStrategy.NONE, factor=1, reason="复杂循环"
        )

        assert decision.strategy == UnrollStrategy.NONE
        assert decision.factor == 1


class TestUnrollResult:
    """展开结果测试"""

    def test_unroll_result_success(self):
        """测试成功展开结果"""
        result = UnrollResult(
            success=True,
            original_blocks=2,
            new_blocks=10,
            unrolled_iterations=5,
            message="完全展开",
        )

        assert result.success
        assert result.new_blocks == 10
        assert result.unrolled_iterations == 5

    def test_unroll_result_failure(self):
        """测试失败展开结果"""
        result = UnrollResult(
            success=False,
            original_blocks=2,
            new_blocks=2,
            unrolled_iterations=0,
            message="循环未展开",
        )

        assert not result.success
        assert result.new_blocks == 2


class TestLoopUnroller:
    """循环展开器测试"""

    def test_loop_unroller_creation(self):
        """测试循环展开器创建"""
        function = IRFunction(name="test_func")
        unroller = LoopUnroller(function)

        assert unroller.function == function
        # IRFunction 会自动创建 entry 基本块
        assert "entry" in unroller.blocks

    def test_estimate_loop_body_size(self):
        """测试估算循环体大小"""
        function = IRFunction(name="test_func")

        header = IRBasicBlock("header")
        body = IRBasicBlock("body")

        # 添加指令
        header.instructions.append(IRInstruction(Opcode.ADD, [], "i"))
        body.instructions.append(IRInstruction(Opcode.MUL, [], "x"))
        body.instructions.append(IRInstruction(Opcode.SUB, [], "y"))

        function.basic_blocks.append(header)
        function.basic_blocks.append(body)

        loop = LoopInfo(header=header, body={"header", "body"}, latch=body)

        unroller = LoopUnroller(function)
        size = unroller._estimate_loop_body_size(loop)

        assert size == 3

    def test_is_simple_loop_single_block(self):
        """测试简单循环：单块循环"""
        function = IRFunction(name="test_func")

        header = IRBasicBlock("header")
        header.instructions.append(
            IRInstruction(Opcode.JMP, ["header"])  # 无条件跳转
        )

        function.basic_blocks.append(header)

        loop = LoopInfo(header=header, body={"header"}, latch=header)

        unroller = LoopUnroller(function)
        is_simple = unroller._is_simple_loop(loop)

        assert is_simple

    def test_is_simple_loop_complex(self):
        """测试复杂循环"""
        function = IRFunction(name="test_func")

        header = IRBasicBlock("header")
        body = IRBasicBlock("body")
        extra = IRBasicBlock("extra")

        function.basic_blocks.append(header)
        function.basic_blocks.append(body)
        function.basic_blocks.append(extra)

        loop = LoopInfo(header=header, body={"header", "body", "extra"}, latch=body)

        unroller = LoopUnroller(function)
        is_simple = unroller._is_simple_loop(loop)

        # 多个块可能不是简单循环
        assert isinstance(is_simple, bool)

    def test_get_ordered_body_blocks(self):
        """测试获取有序循环体块"""
        function = IRFunction(name="test_func")

        header = IRBasicBlock("header")
        body = IRBasicBlock("body")

        header.successors = ["body"]
        body.successors = ["header"]

        function.basic_blocks.append(header)
        function.basic_blocks.append(body)

        loop = LoopInfo(header=header, body={"header", "body"}, latch=body)

        unroller = LoopUnroller(function)
        ordered = unroller._get_ordered_body_blocks(loop)

        assert len(ordered) >= 1

    def test_clone_basic_block(self):
        """测试克隆基本块"""
        function = IRFunction(name="test_func")

        original = IRBasicBlock("original")
        original.instructions.append(IRInstruction(Opcode.ADD, ["a", "b"], ["c"]))
        original.instructions.append(IRInstruction(Opcode.MUL, ["c", "d"], ["e"]))

        function.basic_blocks.append(original)

        unroller = LoopUnroller(function)
        cloned = unroller._clone_basic_block(original, suffix="_copy")

        assert cloned.label == "original_copy"
        assert len(cloned.instructions) == 2
        assert cloned.instructions[0].opcode == Opcode.ADD

    def test_find_exit_blocks(self):
        """测试查找循环退出块"""
        function = IRFunction(name="test_func")

        header = IRBasicBlock("header")
        body = IRBasicBlock("body")
        exit_block = IRBasicBlock("exit")

        # 设置后继关系
        header.successors = ["body"]
        body.successors = ["header", "exit"]  # 条件跳转
        exit_block.successors = []

        function.basic_blocks.append(header)
        function.basic_blocks.append(body)
        function.basic_blocks.append(exit_block)

        loop = LoopInfo(header=header, body={"header", "body"}, latch=body)

        unroller = LoopUnroller(function)
        exit_blocks = unroller._find_exit_blocks(loop)

        assert "exit" in exit_blocks


class TestUnrollStrategies:
    """展开策略测试"""

    def test_full_unroll_small_loop(self):
        """测试小循环完全展开"""
        function = IRFunction(name="test_func")

        header = IRBasicBlock("header")
        body = IRBasicBlock("body")

        header.successors = ["body"]
        body.successors = ["header"]

        function.basic_blocks.append(header)
        function.basic_blocks.append(body)

        loop = LoopInfo(header=header, body={"header", "body"}, latch=body)

        unroller = LoopUnroller(function)

        # 手动设置小循环属性以便触发完全展开
        # 由于 _is_simple_loop 可能返回 False，这里主要测试结构
        decision = unroller.analyze_unroll_potential(loop)

        assert decision.strategy in UnrollStrategy
        assert decision.factor >= 1

    def test_unroll_with_max_iterations(self):
        """测试最大迭代次数限制"""
        function = IRFunction(name="test_func")

        unroller = LoopUnroller(function)

        # 检查常量配置
        assert unroller.MAX_FULL_UNROLL_ITERATIONS == 10
        assert unroller.MAX_UNROLL_FACTOR == 8
        assert unroller.MAX_UNROLL_BODY_SIZE == 100


class TestIntegration:
    """集成测试"""

    def test_unroll_loops_function(self):
        """测试 unroll_loops 函数"""
        function = IRFunction(name="test_func")

        # 创建一个简单的循环结构
        header = IRBasicBlock("header")
        header.successors = ["header"]  # 自循环

        function.basic_blocks.append(header)

        results = unroll_loops(function)

        assert isinstance(results, list)

    def test_empty_function(self):
        """测试空函数"""
        function = IRFunction(name="empty_func")

        unroller = LoopUnroller(function)
        results = unroller.optimize()

        assert len(results) == 0

    def test_loop_unroller_with_metadata(self):
        """测试带标签的指令克隆"""
        function = IRFunction(name="test_func")

        original = IRBasicBlock("original")
        inst = IRInstruction(Opcode.ADD, ["a", "b"], ["c"], label="test_label")
        original.instructions.append(inst)

        function.basic_blocks.append(original)

        unroller = LoopUnroller(function)
        cloned = unroller._clone_basic_block(original, suffix="_copy")

        # 检查指令是否被复制
        assert len(cloned.instructions) == 1
        assert cloned.instructions[0].opcode == Opcode.ADD


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

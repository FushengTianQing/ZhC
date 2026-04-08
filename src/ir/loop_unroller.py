# -*- coding: utf-8 -*-
"""
ZHC IR - 循环展开优化

实现循环展开优化：
- 完全展开（小循环）
- 部分展开（减少迭代次数）
- 循环展开因子选择

作者：阿福
日期：2026-04-08
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from .instructions import IRBasicBlock, IRInstruction
from .program import IRFunction
from .loop_optimizer import LoopInfo, NaturalLoopDetection
from .opcodes import Opcode


class UnrollStrategy(Enum):
    """循环展开策略"""

    FULL = "full"  # 完全展开
    PARTIAL = "partial"  # 部分展开
    NONE = "none"  # 不展开


@dataclass
class UnrollDecision:
    """展开决策"""

    strategy: UnrollStrategy
    factor: int  # 展开因子（复制次数）
    reason: str  # 决策原因


@dataclass
class UnrollResult:
    """展开结果"""

    success: bool
    original_blocks: int
    new_blocks: int
    unrolled_iterations: int
    message: str


class LoopUnroller:
    """
    循环展开优化器

    循环展开通过复制循环体多次来减少循环开销：
    - 减少分支预测失败
    - 增加指令级并行
    - 暴露更多优化机会
    """

    # 展开参数
    MAX_FULL_UNROLL_ITERATIONS = 10  # 完全展开最大迭代次数
    MAX_UNROLL_FACTOR = 8  # 最大展开因子
    MAX_UNROLL_BODY_SIZE = 100  # 展开后最大指令数

    def __init__(self, function: IRFunction):
        self.function = function
        self.blocks: Dict[str, IRBasicBlock] = {}
        for bb in function.basic_blocks:
            self.blocks[bb.label] = bb

        # 循环检测
        self.loop_detector = NaturalLoopDetection(function)
        self.loops = self.loop_detector.loops

    def analyze_unroll_potential(self, loop: LoopInfo) -> UnrollDecision:
        """
        分析循环展开潜力

        Args:
            loop: 循环信息

        Returns:
            展开决策
        """
        # 1. 检查循环体大小
        body_size = self._estimate_loop_body_size(loop)

        # 2. 尝试推断迭代次数
        iterations = self._infer_iteration_count(loop)

        # 3. 检查是否是简单循环
        is_simple = self._is_simple_loop(loop)

        # 4. 决策
        if iterations is not None and iterations <= self.MAX_FULL_UNROLL_ITERATIONS:
            # 小循环：完全展开
            return UnrollDecision(
                strategy=UnrollStrategy.FULL,
                factor=iterations,
                reason=f"小循环（{iterations} 次迭代），完全展开",
            )

        if is_simple and body_size <= 20:
            # 简单循环：部分展开
            factor = min(4, self.MAX_UNROLL_FACTOR)
            if iterations is not None:
                factor = min(factor, iterations // 2)

            return UnrollDecision(
                strategy=UnrollStrategy.PARTIAL,
                factor=factor,
                reason=f"简单循环，部分展开（因子={factor}）",
            )

        # 不展开
        return UnrollDecision(
            strategy=UnrollStrategy.NONE,
            factor=1,
            reason="循环不适合展开（复杂或过大）",
        )

    def unroll_loop(self, loop: LoopInfo, decision: UnrollDecision) -> UnrollResult:
        """
        展开循环

        Args:
            loop: 循环信息
            decision: 展开决策

        Returns:
            展开结果
        """
        if decision.strategy == UnrollStrategy.NONE:
            return UnrollResult(
                success=False,
                original_blocks=len(loop.body),
                new_blocks=len(loop.body),
                unrolled_iterations=0,
                message="循环未展开",
            )

        if decision.strategy == UnrollStrategy.FULL:
            return self._full_unroll(loop, decision.factor)
        else:
            return self._partial_unroll(loop, decision.factor)

    def _full_unroll(self, loop: LoopInfo, iterations: int) -> UnrollResult:
        """
        完全展开循环

        将循环完全展开为顺序代码
        """
        original_blocks = len(loop.body)

        # 获取循环体基本块（按顺序）
        body_blocks = self._get_ordered_body_blocks(loop)

        if not body_blocks:
            return UnrollResult(
                success=False,
                original_blocks=original_blocks,
                new_blocks=original_blocks,
                unrolled_iterations=0,
                message="无法获取循环体",
            )

        # 创建展开后的基本块
        new_blocks = []

        for i in range(iterations):
            # 为每次迭代创建基本块副本
            for bb in body_blocks:
                new_bb = self._clone_basic_block(bb, suffix=f"_unroll_{i}")
                new_blocks.append(new_bb)

        # 替换循环
        self._replace_loop_with_blocks(loop, new_blocks)

        return UnrollResult(
            success=True,
            original_blocks=original_blocks,
            new_blocks=len(new_blocks),
            unrolled_iterations=iterations,
            message=f"完全展开：{iterations} 次迭代",
        )

    def _partial_unroll(self, loop: LoopInfo, factor: int) -> UnrollResult:
        """
        部分展开循环

        将循环体复制 factor 次，减少迭代次数
        """
        original_blocks = len(loop.body)

        # 获取循环体基本块
        body_blocks = self._get_ordered_body_blocks(loop)

        if not body_blocks:
            return UnrollResult(
                success=False,
                original_blocks=original_blocks,
                new_blocks=original_blocks,
                unrolled_iterations=0,
                message="无法获取循环体",
            )

        # 创建展开后的循环体
        new_body_blocks = []

        for i in range(factor):
            for bb in body_blocks:
                new_bb = self._clone_basic_block(bb, suffix=f"_unroll_{i}")
                new_body_blocks.append(new_bb)

        # 更新循环（减少迭代次数）
        # 注意：这里简化处理，实际需要更新循环条件和迭代变量
        self._update_loop_after_partial_unroll(loop, new_body_blocks, factor)

        return UnrollResult(
            success=True,
            original_blocks=original_blocks,
            new_blocks=len(new_body_blocks),
            unrolled_iterations=factor,
            message=f"部分展开：因子={factor}",
        )

    def _estimate_loop_body_size(self, loop: LoopInfo) -> int:
        """估算循环体大小（指令数）"""
        total_instructions = 0

        for block_label in loop.body:
            if block_label in self.blocks:
                block = self.blocks[block_label]
                total_instructions += len(block.instructions)

        return total_instructions

    def _infer_iteration_count(self, loop: LoopInfo) -> Optional[int]:
        """
        推断循环迭代次数

        分析循环头和条件跳转，尝试推断迭代次数
        """
        header = loop.header

        # 查找循环条件
        for inst in header.instructions:
            # 检查是否是比较指令
            if inst.opcode in (Opcode.CMP, Opcode.ICMP, Opcode.FCMP):
                # 尝试提取常量边界
                # 这里简化处理，实际需要更复杂的分析
                pass

        # 查找循环变量更新模式
        # 例如：i = i + 1, i < N
        # 这里简化处理，返回 None
        return None

    def _is_simple_loop(self, loop: LoopInfo) -> bool:
        """
        检查是否是简单循环

        简单循环的特征：
        - 单一入口、单一出口
        - 没有内部控制流（if/switch）
        - 没有函数调用
        """
        # 检查基本块数量
        if len(loop.body) > 3:
            return False

        # 检查是否有内部分支
        for block_label in loop.body:
            if block_label not in self.blocks:
                continue

            block = self.blocks[block_label]

            # 检查是否有条件跳转
            for inst in block.instructions:
                if inst.opcode in (Opcode.JMP, Opcode.JZ, Opcode.SWITCH):
                    # 条件分支
                    if len(block.successors) > 1:
                        # 检查后继是否都在循环内
                        for succ in block.successors:
                            if succ not in loop.body:
                                return False

        return True

    def _get_ordered_body_blocks(self, loop: LoopInfo) -> List[IRBasicBlock]:
        """获取有序的循环体基本块"""
        ordered = []
        visited = set()

        # 从循环头开始 DFS
        def visit(block_label: str):
            if block_label in visited:
                return
            if block_label not in loop.body:
                return

            visited.add(block_label)

            if block_label in self.blocks:
                ordered.append(self.blocks[block_label])

                # 访问后继
                block = self.blocks[block_label]
                for succ in block.successors:
                    visit(succ)

        visit(loop.header.label)
        return ordered

    def _clone_basic_block(self, block: IRBasicBlock, suffix: str = "") -> IRBasicBlock:
        """
        克隆基本块

        Args:
            block: 原始基本块
            suffix: 新标签后缀

        Returns:
            克隆的基本块
        """
        new_label = f"{block.label}{suffix}"
        new_block = IRBasicBlock(new_label)

        # 复制指令
        for inst in block.instructions:
            new_inst = IRInstruction(
                opcode=inst.opcode,
                operands=inst.operands.copy(),
                result=inst.result,
                label=inst.label,
            )
            new_block.instructions.append(new_inst)

        return new_block

    def _replace_loop_with_blocks(self, loop: LoopInfo, new_blocks: List[IRBasicBlock]):
        """
        用新基本块替换循环

        Args:
            loop: 循环信息
            new_blocks: 新基本块列表
        """
        # 找到循环前置块
        preheader = loop.preheader
        if not preheader:
            return

        # 更新前置块的后继
        if new_blocks:
            first_block = new_blocks[0]
            # 更新跳转目标
            for inst in preheader.instructions:
                if inst.opcode == Opcode.BR:
                    # 修改跳转目标
                    if len(inst.operands) == 1:
                        # 无条件跳转
                        inst.operands[0] = first_block.label
                    elif len(inst.operands) == 3:
                        # 条件跳转
                        inst.operands[1] = first_block.label

        # 更新最后一个新块的后继
        if new_blocks:
            last_block = new_blocks[-1]
            # 找到循环的退出块
            exit_blocks = self._find_exit_blocks(loop)
            if exit_blocks:
                # 添加跳转到退出块
                br_inst = IRInstruction(opcode=Opcode.BR, operands=[exit_blocks[0]])
                last_block.instructions.append(br_inst)

        # 添加新块到函数
        for block in new_blocks:
            self.function.basic_blocks.append(block)

        # 移除旧循环体（简化处理，实际需要更复杂的逻辑）
        # 这里保留旧块，由后续死代码消除清理

    def _update_loop_after_partial_unroll(
        self, loop: LoopInfo, new_body_blocks: List[IRBasicBlock], factor: int
    ):
        """
        部分展开后更新循环

        Args:
            loop: 循环信息
            new_body_blocks: 新循环体块
            factor: 展开因子
        """
        # 更新循环头
        if new_body_blocks:
            new_header = new_body_blocks[0]
            loop.header = new_header

        # 更新循环体
        new_body = set()
        for block in new_body_blocks:
            new_body.add(block.label)
        loop.body = new_body

        # 更新迭代变量（简化处理）
        # 实际需要：i = i + factor 而不是 i = i + 1

    def _find_exit_blocks(self, loop: LoopInfo) -> List[str]:
        """查找循环退出块"""
        exit_blocks = []

        for block_label in loop.body:
            if block_label not in self.blocks:
                continue

            block = self.blocks[block_label]

            # 检查后继是否在循环外
            for succ in block.successors:
                if succ not in loop.body:
                    exit_blocks.append(succ)

        return exit_blocks

    def optimize(self) -> List[UnrollResult]:
        """
        执行循环展开优化

        Returns:
            所有循环的展开结果
        """
        results = []

        for loop in self.loops:
            # 分析展开潜力
            decision = self.analyze_unroll_potential(loop)

            # 执行展开
            result = self.unroll_loop(loop, decision)
            results.append(result)

        return results


def unroll_loops(function: IRFunction) -> List[UnrollResult]:
    """
    对函数执行循环展开优化

    Args:
        function: IR 函数

    Returns:
        展开结果列表
    """
    unroller = LoopUnroller(function)
    return unroller.optimize()

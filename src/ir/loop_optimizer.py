# -*- coding: utf-8 -*-
"""
ZHC IR - 循环优化

实现循环优化相关算法：
- 循环不变代码外提 (Loop-Invariant Code Motion)
- 强度削减 (Strength Reduction)

作者：远
日期：2026-04-08
"""

from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict

from .instructions import IRBasicBlock, IRInstruction
from .program import IRFunction
from .values import IRValue, ValueKind
from .opcodes import Opcode
from .dataflow import LivenessAnalysis, analyze_liveness


# =============================================================================
# 循环检测
# =============================================================================

class LoopInfo:
    """
    循环信息

    Attributes:
        header: 循环头基本块
        body: 循环体基本块集合
        latch: 循环Latch基本块（跳回头部的块）
        preheader: 循环前置块（跳转到头部的唯一前驱）
        is_natural: 是否是自然循环
        depth: 嵌套深度
    """

    def __init__(
        self,
        header: IRBasicBlock,
        body: Set[str],
        latch: Optional[IRBasicBlock] = None,
    ):
        self.header = header
        self.body = body  # 包含 header
        self.latch = latch
        self.preheader: Optional[IRBasicBlock] = None
        self.is_natural = True
        self.depth = 1

    def contains_block(self, block_label: str) -> bool:
        """检查基本块是否在循环内"""
        return block_label in self.body

    def __repr__(self) -> str:
        return f"Loop({self.header.label}, body={len(self.body)} blocks, depth={self.depth})"


class NaturalLoopDetection:
    """
    自然循环检测

    使用回边（back edge）检测自然循环。
    """

    def __init__(self, function: IRFunction):
        self.function = function
        self.blocks: Dict[str, IRBasicBlock] = {}
        for bb in function.basic_blocks:
            self.blocks[bb.label] = bb

        # 反向边 -> 循环头
        self.back_edges: List[Tuple[str, str]] = []
        # 检测到的循环
        self.loops: List[LoopInfo] = []

        self._detect_loops()

    def _detect_loops(self):
        """检测所有自然循环"""
        # 构建前驱集合
        predecessors: Dict[str, Set[str]] = defaultdict(set)
        for label, block in self.blocks.items():
            for pred in block.predecessors:
                predecessors[label].add(pred)

        # 寻找回边
        # 回边：如果从 B 到 A（A 支配 B），则 (A, B) 是回边
        dominated = self._compute_dominators()

        for label, block in self.blocks.items():
            for pred in block.predecessors:
                # 如果 pred 支配 label，则 (pred, label) 是回边
                # pred 是循环头，label 是循环内的某个块
                if pred in dominated and label in dominated[pred]:
                    self.back_edges.append((pred, label))

        # 构建循环
        for head_label, tail_label in self.back_edges:
            loop_body = self._compute_loop_body(head_label, tail_label, predecessors)
            header = self.blocks.get(head_label)

            if header:
                latch = self.blocks.get(tail_label)
                loop_info = LoopInfo(
                    header=header,
                    body=loop_body,
                    latch=latch
                )
                self._compute_preheader(loop_info, predecessors)
                self.loops.append(loop_info)

    def _compute_dominators(self) -> Dict[str, Set[str]]:
        """计算支配者集合"""
        dominated: Dict[str, Set[str]] = {}

        if not self.function.entry_block:
            return dominated

        # 入口块支配自己
        entry_label = self.function.entry_block.label
        dominated[entry_label] = {entry_label}

        # 迭代计算
        changed = True
        while changed:
            changed = False
            for bb in self.function.basic_blocks:
                if bb.label == entry_label:
                    continue

                # 新支配集合 = {self} ∪ intersection of predecessors' dominators
                new_dom: Set[str] = set()

                if bb.predecessors:
                    first = True
                    for pred in bb.predecessors:
                        if pred in dominated:
                            if first:
                                new_dom = dominated[pred].copy()
                                first = False
                            else:
                                new_dom &= dominated[pred]

                if new_dom:
                    new_dom.add(bb.label)
                    old = dominated.get(bb.label)
                    if old != new_dom:
                        dominated[bb.label] = new_dom
                        changed = True

        return dominated

    def _compute_loop_body(
        self,
        head_label: str,
        tail_label: str,
        predecessors: Dict[str, Set[str]],
    ) -> Set[str]:
        """
        计算循环体

        从 tail_label 开始，反向遍历所有可达且不支配 head_label 的节点
        """
        loop_body = {head_label}

        # 使用栈进行 DFS
        to_visit = [tail_label]
        visited: Set[str] = set()

        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue
            if current == head_label:
                continue

            loop_body.add(current)
            visited.add(current)

            # 加入所有前驱（除了可能指向循环外的前驱）
            for pred in predecessors.get(current, []):
                if pred not in loop_body:
                    to_visit.append(pred)

        return loop_body

    def _compute_preheader(self, loop: LoopInfo, predecessors: Dict[str, Set[str]]):
        """计算循环前置块"""
        # 找到所有指向循环头但不在循环内的前驱
        external_preds: Set[str] = set()
        for pred in predecessors.get(loop.header.label, []):
            if pred not in loop.body:
                external_preds.add(pred)

        # 如果有且只有一个外部前驱，它就是 preheader
        # 否则需要创建一个
        if len(external_preds) == 1:
            preheader_label = list(external_preds)[0]
            loop.preheader = self.blocks.get(preheader_label)
        else:
            # 需要创建 preheader（简化处理：标记为 None）
            loop.preheader = None

    def get_loops(self) -> List[LoopInfo]:
        """获取所有检测到的循环"""
        return self.loops

    def get_loop_at(self, block_label: str) -> Optional[LoopInfo]:
        """获取包含指定基本块的循环"""
        for loop in self.loops:
            if loop.contains_block(block_label):
                return loop
        return None


# =============================================================================
# 循环不变代码外提
# =============================================================================

class LoopInvariantCodeMotion:
    """
    循环不变代码外提 (LICM)

    将循环中不依赖于循环迭代的计算移到循环外执行。
    """

    def __init__(self, function: IRFunction):
        self.function = function
        self.blocks: Dict[str, IRBasicBlock] = {}
        for bb in function.basic_blocks:
            self.blocks[bb.label] = bb

        # 活跃变量分析
        self.liveness = LivenessAnalysis(function)
        self.liveness.analyze()

        # 循环检测
        self.loop_detector = NaturalLoopDetection(function)
        self.loops = self.loop_detector.get_loops()

        # 优化统计
        self.moved_count = 0

    def is_loop_invariant(
        self,
        instr: IRInstruction,
        loop: LoopInfo,
        defined_in_loop: Dict[str, Set[str]],
    ) -> bool:
        """
        检查指令是否是循环不变的

        条件：
        1. 所有操作数都是常量或循环外定义的
        2. 结果不在循环中被使用（或在定义后使用但不影响循环外）
        """
        # 终止指令和分支指令不能外提
        if instr.is_terminator():
            return False

        # 检查操作数
        for operand in instr.operands:
            if isinstance(operand, IRValue):
                var_name = self._extract_variable_name(operand)
                if var_name:
                    # 如果操作数在循环内定义但不在当前指令前定义，则不是循环不变
                    loop_defs = defined_in_loop.get(loop.header.label, set())
                    if var_name in loop_defs:
                        # 检查是否在当前指令之前定义
                        if not self._is_defined_before(loop, var_name, instr):
                            return False

        return True

    def _extract_variable_name(self, value: IRValue) -> Optional[str]:
        """提取变量名"""
        if value.kind == ValueKind.VAR or value.kind == ValueKind.TEMP:
            name = value.name
            if name.startswith('%'):
                name = name[1:]
            return name
        return None

    def _is_defined_before(
        self,
        loop: LoopInfo,
        var_name: str,
        target_instr: IRInstruction,
    ) -> bool:
        """检查变量是否在目标指令之前定义"""
        for bb_label in loop.body:
            block = self.blocks.get(bb_label)
            if not block:
                continue

            for instr in block.instructions:
                if instr == target_instr:
                    return False  # 到达目标指令

                for result in instr.result:
                    if isinstance(result, IRValue):
                        name = self._extract_variable_name(result)
                        if name == var_name:
                            return True  # 在目标之前找到定义

        return False

    def _collect_loop_definitions(self, loop: LoopInfo) -> Dict[str, Set[str]]:
        """
        收集循环内的变量定义

        Returns:
            block_label -> set of defined variables
        """
        definitions: Dict[str, Set[str]] = defaultdict(set)

        for bb_label in loop.body:
            block = self.blocks.get(bb_label)
            if not block:
                continue

            for instr in block.instructions:
                for result in instr.result:
                    if isinstance(result, IRValue):
                        var_name = self._extract_variable_name(result)
                        if var_name:
                            definitions[bb_label].add(var_name)

        return definitions

    def _is_safe_to_move(
        self,
        instr: IRInstruction,
        loop: LoopInfo,
    ) -> bool:
        """
        检查外提是否安全

        考虑：
        1. 指令不能有副作用（除了计算）
        2. 如果结果在循环外使用，需要确保不会被覆盖
        """
        # 纯计算指令可以安全移动
        safe_opcodes = [
            Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.DIV, Opcode.MOD,
            Opcode.NEG,
            Opcode.EQ, Opcode.NE, Opcode.LT, Opcode.LE, Opcode.GT, Opcode.GE,
            Opcode.AND, Opcode.OR, Opcode.XOR, Opcode.NOT,
            Opcode.SHL, Opcode.SHR,
            Opcode.CONST, Opcode.ZEXT, Opcode.SEXT, Opcode.TRUNC,
        ]

        if instr.opcode not in safe_opcodes:
            return False

        # 检查结果是否在循环后使用
        # （简化处理：假设所有结果都需要检查）
        return True

    def optimize(self) -> int:
        """
        执行循环不变代码外提

        Returns:
            移动的指令数量
        """
        self.moved_count = 0

        for loop in self.loops:
            self._optimize_loop(loop)

        return self.moved_count

    def _optimize_loop(self, loop: LoopInfo):
        """优化单个循环"""
        # 收集循环内所有定义
        definitions = self._collect_loop_definitions(loop)

        # 收集循环不变指令
        invariant_instrs: List[Tuple[IRBasicBlock, IRInstruction]] = []

        for bb_label in loop.body:
            block = self.blocks.get(bb_label)
            if not block:
                continue

            # 跳过循环头（不能外提）
            if bb_label == loop.header.label:
                continue

            for instr in block.instructions:
                if self.is_loop_invariant(instr, loop, definitions):
                    if self._is_safe_to_move(instr, loop):
                        invariant_instrs.append((block, instr))

        # 移动指令到 preheader 或循环前
        if not invariant_instrs:
            return

        # 确定插入位置
        target_block = self._get_or_create_preheader(loop)

        # 移动指令
        for block, instr in invariant_instrs:
            # 从原位置移除
            if instr in block.instructions:
                block.instructions.remove(instr)
                self.moved_count += 1

                # 插入到目标位置
                # 在 terminator 之前插入
                if target_block.instructions and target_block.instructions[-1].is_terminator():
                    target_block.instructions.insert(-1, instr)
                else:
                    target_block.instructions.append(instr)

    def _get_or_create_preheader(self, loop: LoopInfo) -> IRBasicBlock:
        """获取或创建 preheader"""
        if loop.preheader:
            return loop.preheader

        # 创建 preheader
        # 简化处理：使用 entry 或循环的第一个前驱块
        if loop.header.predecessors:
            for pred_label in loop.header.predecessors:
                if pred_label not in loop.body:
                    pred = self.blocks.get(pred_label)
                    if pred:
                        loop.preheader = pred
                        return pred

        # 回退：使用 entry
        if self.function.entry_block:
            loop.preheader = self.function.entry_block
            return self.function.entry_block

        # 应该不会到这里
        return loop.header


# =============================================================================
# 强度削减
# =============================================================================

class StrengthReduction:
    """
    强度削减

    将昂贵的操作（如乘法）替换为较便宜的操作（如加法）。
    适用于循环中的线性表达式。
    """

    def __init__(self, function: IRFunction):
        self.function = function
        self.blocks: Dict[str, IRBasicBlock] = {}
        for bb in function.basic_blocks:
            self.blocks[bb.label] = bb

        # 循环检测
        self.loop_detector = NaturalLoopDetection(function)
        self.loops = self.loop_detector.get_loops()

        # 优化统计
        self.reduced_count = 0

    def optimize(self) -> int:
        """
        执行强度削减

        Returns:
            削减的表达式数量
        """
        self.reduced_count = 0

        for loop in self.loops:
            self._optimize_loop(loop)

        return self.reduced_count

    def _optimize_loop(self, loop: LoopInfo):
        """优化单个循环"""
        # 寻找循环归纳变量
        induction_vars = self._find_induction_variables(loop)

        # 对每个归纳变量，寻找可以削减的表达式
        for ivar in induction_vars:
            self._reduce_expressions(loop, ivar)

    def _find_induction_variables(self, loop: LoopInfo) -> List[str]:
        """
        查找循环归纳变量

        归纳变量：在循环每次迭代中以常数值增加的变量。
        """
        induction_vars: List[str] = []

        # 查找在循环头被定义的变量
        for instr in loop.header.instructions:
            if instr.opcode == Opcode.ADD or instr.opcode == Opcode.SUB:
                if len(instr.operands) >= 2:
                    result_name = self._extract_result_name(instr)
                    if result_name:
                        # 检查是否是循环变量 + 常量
                        operand_names = []
                        for op in instr.operands:
                            if isinstance(op, IRValue):
                                name = self._extract_variable_name(op)
                                operand_names.append(name)

                        # 检查是否有一个是常量
                        has_constant = any(
                            isinstance(op, IRValue) and op.kind == ValueKind.CONST
                            for op in instr.operands
                        )

                        if has_constant:
                            # 检查是否有一个是循环变量（之前定义的值）
                            if any(name for name in operand_names if name):
                                induction_vars.append(result_name)

        return induction_vars

    def _extract_result_name(self, instr: IRInstruction) -> Optional[str]:
        """提取结果变量名"""
        if instr.result and len(instr.result) > 0:
            result = instr.result[0]
            return self._extract_variable_name(result)
        return None

    def _extract_variable_name(self, value: IRValue) -> Optional[str]:
        """提取变量名"""
        if value.kind == ValueKind.VAR or value.kind == ValueKind.TEMP:
            name = value.name
            if name.startswith('%'):
                name = name[1:]
            return name
        return None

    def _reduce_expressions(self, loop: LoopInfo, induction_var: str):
        """
        削减与归纳变量相关的表达式

        例如：
          i * c  ->  iv * c（使用归纳变量的初始值）
        """
        for bb_label in loop.body:
            block = self.blocks.get(bb_label)
            if not block:
                continue

            for instr in block.instructions:
                # 查找包含归纳变量的乘法
                if instr.opcode == Opcode.MUL:
                    self._try_reduce_multiply(block, instr, induction_var, loop)


# =============================================================================
# 循环优化器
# =============================================================================

class LoopOptimizer:
    """
    循环优化器

    整合循环不变代码外提和强度削减。
    """

    def __init__(self, function: IRFunction):
        self.function = function
        self.stats = {
            "licm_moved": 0,
            "strength_reduced": 0,
        }

    def optimize(self) -> Dict[str, int]:
        """
        执行循环优化

        Returns:
            优化统计
        """
        # 1. 循环不变代码外提
        licm = LoopInvariantCodeMotion(self.function)
        self.stats["licm_moved"] = licm.optimize()

        # 2. 强度削减
        sr = StrengthReduction(self.function)
        self.stats["strength_reduced"] = sr.optimize()

        return self.stats

    def get_stats(self) -> Dict[str, int]:
        """获取优化统计"""
        return self.stats.copy()


# =============================================================================
# 便捷函数
# =============================================================================

def detect_loops(function: IRFunction) -> List[LoopInfo]:
    """
    便捷函数：检测函数中的循环

    Args:
        function: IR 函数

    Returns:
        循环列表
    """
    detector = NaturalLoopDetection(function)
    return detector.get_loops()


def optimize_loops(function: IRFunction) -> Dict[str, int]:
    """
    便捷函数：优化函数中的循环

    Args:
        function: IR 函数

    Returns:
        优化统计
    """
    optimizer = LoopOptimizer(function)
    return optimizer.optimize()

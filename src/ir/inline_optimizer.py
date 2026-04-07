# -*- coding: utf-8 -*-
"""
ZHC IR - 函数内联优化

实现函数内联优化：
- 内联决策（基于启发式规则）
- 内联执行（函数体复制）
- 成本模型

作者：远
日期：2026-04-08
"""

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass

from .instructions import IRBasicBlock, IRInstruction
from .program import IRFunction, IRProgram
from .values import IRValue, ValueKind
from .opcodes import Opcode


# =============================================================================
# 内联成本模型
# =============================================================================

@dataclass
class InlineCost:
    """
    内联成本

    Attributes:
        instruction_count: 指令数量
        basic_block_count: 基本块数量
        call_count: 函数调用次数
        estimated_size: 估计大小
    """
    instruction_count: int = 0
    basic_block_count: int = 0
    call_count: int = 0
    estimated_size: int = 0

    def is_small(self, threshold: int = 10) -> bool:
        """判断是否是小函数"""
        return self.instruction_count <= threshold

    def is_hot(self, call_count: int = 5) -> bool:
        """判断是否是热点函数"""
        return self.call_count >= call_count


class InlineCostModel:
    """
    内联成本模型

    基于启发式规则决定是否内联。
    """

    def __init__(self, program: IRProgram):
        self.program = program

        # 函数调用计数
        self.call_counts: Dict[str, int] = {}
        self._count_calls()

        # 函数成本
        self.function_costs: Dict[str, InlineCost] = {}
        self._compute_costs()

    def _count_calls(self):
        """统计每个函数的调用次数"""
        for func in self.program.functions:
            count = 0
            for bb in func.basic_blocks:
                for instr in bb.instructions:
                    if instr.opcode == Opcode.CALL:
                        count += 1
            self.call_counts[func.name] = count

    def _compute_costs(self):
        """计算每个函数的内联成本"""
        for func in self.program.functions:
            cost = InlineCost(
                instruction_count=self._count_instructions(func),
                basic_block_count=len(func.basic_blocks),
                call_count=self.call_counts.get(func.name, 0),
                estimated_size=self._estimate_size(func)
            )
            self.function_costs[func.name] = cost

    def _count_instructions(self, func: IRFunction) -> int:
        """计算函数的指令数量"""
        count = 0
        for bb in func.basic_blocks:
            count += len(bb.instructions)
        return count

    def _estimate_size(self, func: IRFunction) -> int:
        """估计函数大小（字节）"""
        # 简化估计：每条指令约 4 字节
        return self._count_instructions(func) * 4

    def should_inline(
        self,
        caller: IRFunction,
        callee: IRFunction,
        call_site: IRInstruction,
    ) -> bool:
        """
        决定是否内联

        Args:
            caller: 调用者函数
            callee: 被调用者函数
            call_site: 调用点指令

        Returns:
            是否应该内联
        """
        callee_cost = self.function_costs.get(callee.name)

        if not callee_cost:
            return False

        # 规则 1: 小函数总是内联
        if callee_cost.is_small(threshold=10):
            return True

        # 规则 2: 热点函数内联
        if callee_cost.is_hot(call_count=5):
            # 但不能太大
            if callee_cost.instruction_count <= 50:
                return True

        # 规则 3: 只被调用一次的函数内联
        if self.call_counts.get(callee.name, 0) == 1:
            return True

        # 规则 4: 递归函数不内联
        if self._is_recursive(callee):
            return False

        # 规则 5: 调用深度限制
        if self._get_call_depth(callee) > 3:
            return False

        return False

    def _is_recursive(self, func: IRFunction) -> bool:
        """检查函数是否是递归的"""
        for bb in func.basic_blocks:
            for instr in bb.instructions:
                if instr.opcode == Opcode.CALL:
                    for operand in instr.operands:
                        if isinstance(operand, IRValue):
                            if operand.name == func.name or operand.name == f"@{func.name}":
                                return True
        return False

    def _get_call_depth(self, func: IRFunction, visited: Set[str] = None) -> int:
        """获取函数的调用深度"""
        if visited is None:
            visited = set()

        if func.name in visited:
            return 0

        visited.add(func.name)

        max_depth = 0
        for bb in func.basic_blocks:
            for instr in bb.instructions:
                if instr.opcode == Opcode.CALL:
                    for operand in instr.operands:
                        if isinstance(operand, IRValue):
                            callee_name = operand.name.lstrip('@')
                            callee = self.program.find_function(callee_name)
                            if callee:
                                depth = self._get_call_depth(callee, visited)
                                max_depth = max(max_depth, depth + 1)

        return max_depth

    def get_cost(self, func_name: str) -> Optional[InlineCost]:
        """获取函数的内联成本"""
        return self.function_costs.get(func_name)


# =============================================================================
# 函数内联器
# =============================================================================

class FunctionInliner:
    """
    函数内联器

    执行函数内联优化。
    """

    def __init__(self, program: IRProgram):
        self.program = program
        self.cost_model = InlineCostModel(program)

        # 内联统计
        self.stats = {
            "inlined_count": 0,
            "total_instructions_saved": 0,
        }

        # 变量重命名计数器
        self.rename_counter = 0

    def inline_all(self) -> Dict[str, int]:
        """
        内联所有符合条件的函数

        Returns:
            优化统计
        """
        changed = True
        while changed:
            changed = False

            for caller in self.program.functions:
                if self._inline_function(caller):
                    changed = True
                    self.stats["inlined_count"] += 1

        return self.stats

    def _inline_function(self, caller: IRFunction) -> bool:
        """
        内联函数中的所有调用点

        Returns:
            是否有内联发生
        """
        inlined = False

        # 收集所有调用点
        call_sites: List[Tuple[IRBasicBlock, int, IRInstruction, IRFunction]] = []

        for bb in caller.basic_blocks:
            for idx, instr in enumerate(bb.instructions):
                if instr.opcode == Opcode.CALL:
                    callee = self._get_callee(instr)
                    if callee and self.cost_model.should_inline(caller, callee, instr):
                        call_sites.append((bb, idx, instr, callee))

        # 执行内联
        for bb, idx, call_instr, callee in call_sites:
            if self._inline_call_site(caller, bb, idx, call_instr, callee):
                inlined = True

        return inlined

    def _get_callee(self, call_instr: IRInstruction) -> Optional[IRFunction]:
        """获取被调用的函数"""
        if not call_instr.operands:
            return None

        # 第一个操作数是函数名
        func_value = call_instr.operands[0]
        if isinstance(func_value, IRValue):
            func_name = func_value.name.lstrip('@')
            return self.program.find_function(func_name)

        return None

    def _inline_call_site(
        self,
        caller: IRFunction,
        call_block: IRBasicBlock,
        call_idx: int,
        call_instr: IRInstruction,
        callee: IRFunction,
    ) -> bool:
        """
        内联单个调用点

        Returns:
            是否成功
        """
        # 检查递归
        if callee.name == caller.name:
            return False

        # 创建内联后的基本块
        inlined_blocks = self._clone_function(caller, callee, call_instr)

        if not inlined_blocks:
            return False

        # 替换调用点
        # 将 call_block 分裂为两部分
        # call_block: [0..call_idx) -> inlined_blocks -> [call_idx+1..end]

        # 获取 call_idx 之后的指令
        after_call = call_block.instructions[call_idx + 1:]

        # 移除调用指令
        call_block.instructions = call_block.instructions[:call_idx]

        # 添加内联的基本块
        # 第一个内联块接在 call_block 后
        first_inlined = inlined_blocks[0]
        call_block.instructions.extend(first_inlined.instructions)

        # 更新后继关系
        # ...

        # 添加剩余的内联块
        for i, block in enumerate(inlined_blocks[1:], start=1):
            # 重命名避免冲突
            block.label = f"{caller.name}.inline.{self.rename_counter}.{block.label}"
            caller.add_basic_block(block.label)
            # 复制指令
            new_block = caller.find_basic_block(block.label)
            if new_block:
                new_block.instructions = block.instructions

        # 添加 call_idx 之后的指令到最后一个内联块
        if inlined_blocks and after_call:
            last_block = inlined_blocks[-1]
            last_block.instructions.extend(after_call)

        self.stats["total_instructions_saved"] += self.cost_model.get_cost(callee.name).instruction_count if self.cost_model.get_cost(callee.name) else 0

        return True

    def _clone_function(
        self,
        caller: IRFunction,
        callee: IRFunction,
        call_instr: IRInstruction,
    ) -> List[IRBasicBlock]:
        """
        克隆函数体

        Returns:
            克隆的基本块列表
        """
        self.rename_counter += 1

        # 变量映射
        var_map: Dict[str, str] = {}

        # 参数映射
        if len(call_instr.operands) > 1:
            for i, param in enumerate(callee.params):
                if i + 1 < len(call_instr.operands):
                    arg = call_instr.operands[i + 1]
                    if isinstance(arg, IRValue):
                        var_map[param.name] = arg.name

        # 克隆基本块
        cloned_blocks: List[IRBasicBlock] = []

        for bb in callee.basic_blocks:
            new_label = f"{bb.label}.inline.{self.rename_counter}"
            new_block = IRBasicBlock(new_label)

            for instr in bb.instructions:
                new_instr = self._clone_instruction(instr, var_map)
                new_block.add_instruction(new_instr)

            cloned_blocks.append(new_block)

        return cloned_blocks

    def _clone_instruction(
        self,
        instr: IRInstruction,
        var_map: Dict[str, str],
    ) -> IRInstruction:
        """克隆指令"""
        # 克隆操作数
        new_operands = []
        for op in instr.operands:
            if isinstance(op, IRValue):
                new_name = var_map.get(op.name, op.name)
                new_op = IRValue(
                    name=new_name,
                    ty=op.ty,
                    kind=op.kind,
                    const_value=op.const_value
                )
                new_operands.append(new_op)
            else:
                new_operands.append(op)

        # 克隆结果
        new_results = []
        for result in instr.result:
            if isinstance(result, IRValue):
                # 生成新名称
                new_name = f"%inline.{self.rename_counter}.{result.name.lstrip('%')}"
                var_map[result.name] = new_name

                new_result = IRValue(
                    name=new_name,
                    ty=result.ty,
                    kind=result.kind
                )
                new_results.append(new_result)
            else:
                new_results.append(result)

        return IRInstruction(
            opcode=instr.opcode,
            operands=new_operands,
            result=new_results,
            label=instr.label
        )


# =============================================================================
# 内联优化器
# =============================================================================

class InlineOptimizer:
    """
    内联优化器

    整合成本模型和内联器。
    """

    def __init__(self, program: IRProgram):
        self.program = program
        self.stats = {
            "inlined_count": 0,
            "total_instructions_saved": 0,
        }

    def optimize(self) -> Dict[str, int]:
        """
        执行内联优化

        Returns:
            优化统计
        """
        inliner = FunctionInliner(self.program)
        self.stats = inliner.inline_all()
        return self.stats

    def get_stats(self) -> Dict[str, int]:
        """获取优化统计"""
        return self.stats.copy()


# =============================================================================
# 便捷函数
# =============================================================================

def inline_functions(program: IRProgram) -> Dict[str, int]:
    """
    便捷函数：执行函数内联优化

    Args:
        program: IR 程序

    Returns:
        优化统计
    """
    optimizer = InlineOptimizer(program)
    return optimizer.optimize()
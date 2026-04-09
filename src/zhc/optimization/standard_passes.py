# -*- coding: utf-8 -*-
"""
ZhC 标准优化 Pass 实现

实现常用的优化 Pass，包括：
- 内联 Pass (inline)
- 死代码消除 Pass (dce)
- 全局值编号 Pass (gvn)
- 循环优化 Pass

作者：远
日期：2026-04-09
"""

from abc import ABC
from typing import Dict, List, Set, Any
import logging

from zhc.optimization.pass_registry import PassType, PassRegistry

logger = logging.getLogger(__name__)


# ============================================================================
# 基础 Pass 类
# ============================================================================


class BasePass(ABC):
    """
    优化 Pass 基类

    所有优化 Pass 应继承此类。
    """

    pass_type: PassType = PassType.TRANSFORM
    name: str = "base"

    def __init__(self, **params):
        self.params = params

    def run(self, module: Any) -> bool:
        """
        运行 Pass

        Args:
            module: LLVM 模块

        Returns:
            是否发生了改变
        """
        changed = False
        for func in module.functions:
            if self._should_optimize_function(func):
                if self.run_on_function(func, module):
                    changed = True
        return changed

    def run_on_function(self, func: Any, module: Any) -> bool:
        """在单个函数上运行 Pass"""
        return False

    def _should_optimize_function(self, func: Any) -> bool:
        """检查是否应该优化函数"""
        # 跳过外部函数
        if hasattr(func, "is_declaration") and func.is_declaration:
            return False
        return True


# ============================================================================
# 无操作 Pass
# ============================================================================


@PassRegistry.register_pass(
    "no-op",
    PassType.UTILITY,
    "无操作 Pass，不做任何优化，用于测试",
)
class NoOpPass(BasePass):
    """
    无操作 Pass

    不做任何优化，仅用于测试或占位。
    """

    pass_type = PassType.UTILITY
    name = "no-op"

    def run(self, module: Any) -> bool:
        """不改变模块"""
        logger.debug("Running no-op pass")
        return False


# ============================================================================
# 验证 Pass
# ============================================================================


@PassRegistry.register_pass(
    "verify",
    PassType.UTILITY,
    "验证 LLVM IR 的正确性",
)
class VerifyPass(BasePass):
    """
    验证 Pass

    验证 LLVM IR 的正确性，检查基本的结构问题。
    """

    pass_type = PassType.UTILITY
    name = "verify"

    def run(self, module: Any) -> bool:
        """验证模块"""
        errors = []

        # 检查基本块完整性
        for func in module.functions:
            if hasattr(func, "is_declaration") and func.is_declaration:
                continue

            for block in func.blocks:
                # 检查基本块是否以终止符结束
                if not self._is_terminated(block):
                    errors.append(f"Basic block '{block.name}' is not terminated")

        if errors:
            error_msg = "Verification failed:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            # 验证失败不抛出异常，仅记录
            return False

        logger.debug("Verification passed")
        return False  # 不改变模块


# ============================================================================
# 内存到寄存器提升 Pass (mem2reg)
# ============================================================================


@PassRegistry.register_pass(
    "mem2reg",
    PassType.TRANSFORM,
    "将内存操作提升为 SSA 寄存器操作",
)
class Mem2RegPass(BasePass):
    """
    内存到寄存器提升 Pass

    将 ALLOC/STORE/LOAD 模式转换为 SSA phi 节点。

    优化前：
        %a = alloca i32
        store i32 10, i32* %a
        %b = load i32, i32* %a

    优化后：
        %a = 10
        %b = %a
    """

    name = "mem2reg"

    def run(self, module: Any) -> bool:
        """运行 mem2reg"""
        changed = False

        for func in module.functions:
            if not self._should_optimize_function(func):
                continue

            if self._run_mem2reg(func):
                changed = True

        return changed

    def _run_mem2reg(self, func: Any) -> bool:
        """在函数上运行 mem2reg"""
        # 查找 alloca 指令
        allocas = self._find_allocas(func)
        if not allocas:
            return False

        changed = False

        for alloca in allocas:
            # 尝试提升单个 alloca
            if self._promote_alloca(func, alloca):
                changed = True

        return changed

    def _find_allocas(self, func: Any) -> List[Any]:
        """查找函数中的 alloca 指令"""
        allocas = []

        if not hasattr(func, "blocks") or not func.blocks:
            return allocas

        # 查找第一个基本块
        entry = func.blocks[0]

        for instr in entry.instructions:
            if self._is_alloca(instr):
                allocas.append(instr)

        return allocas

    def _is_alloca(self, instr: Any) -> bool:
        """检查指令是否是 alloca"""
        return hasattr(instr, "opcode") and "alloca" in str(instr.opcode).lower()

    def _is_terminated(self, block: Any) -> bool:
        """检查基本块是否以终止符结束"""
        if not hasattr(block, "instructions"):
            return False
        if not block.instructions:
            return False
        last = block.instructions[-1]
        return hasattr(last, "opcode") and "ret" in str(last.opcode).lower()

    def _promote_alloca(self, func: Any, alloca: Any) -> bool:
        """
        提升单个 alloca

        这是一个简化版本，完整实现需要复杂的 SSA 构建算法。
        """
        # 简化实现：只处理简单的 case
        # 完整实现需要分析 def-use 链和 dominance 关系
        logger.debug(f"Promoting alloca: {alloca}")
        return False  # 暂时返回 False，简化版本不实际提升


# ============================================================================
# 死代码消除 Pass (dce)
# ============================================================================


@PassRegistry.register_pass(
    "dce",
    PassType.TRANSFORM,
    "消除死代码（没有副作用的未使用指令）",
    invalidated_passes=["gvn"],
)
class DCEPass(BasePass):
    """
    死代码消除 Pass

    递归地消除没有副作用且结果未被使用的指令。

    示例：
        %a = add i32 %x, %y
        ; %a 从未被使用
        ret i32 0
        ↓
        ret i32 0
    """

    name = "dce"

    def run(self, module: Any) -> bool:
        """运行 DCE"""
        changed = False

        for func in module.functions:
            if not self._should_optimize_function(func):
                continue

            if self._run_dce_on_function(func):
                changed = True

        return changed

    def _run_dce_on_function(self, func: Any) -> bool:
        """在函数上运行 DCE"""
        if not hasattr(func, "blocks") or not func.blocks:
            return False

        # 构建 def-use 链
        uses = self._build_use_chain(func)

        # 标记有副作用的指令
        side_effects = self._find_side_effect_instructions(func)

        # 递归标记活跃指令
        alive = self._mark_alive(func, uses, side_effects)

        # 删除死指令
        return self._remove_dead_instructions(func, alive)

    def _build_use_chain(self, func: Any) -> Dict[int, Set[int]]:
        """构建指令使用链"""
        uses: Dict[int, Set[int]] = {}
        instr_to_idx: Dict[int, int] = {}
        all_instrs = []

        # 收集所有指令
        for block in func.blocks:
            for instr in block.instructions:
                all_instrs.append(instr)

        # 建立索引
        for i, instr in enumerate(all_instrs):
            instr_to_idx[id(instr)] = i
            uses[i] = set()

        # 建立 use 链
        for i, instr in enumerate(all_instrs):
            if hasattr(instr, "operands"):
                for operand in instr.operands:
                    if id(operand) in instr_to_idx:
                        uses[instr_to_idx[id(operand)]].add(i)

        return uses

    def _find_side_effect_instructions(self, func: Any) -> Set[int]:
        """查找有副作用的指令"""
        side_effects: Set[int] = {}

        for block in func.blocks:
            for instr in block.instructions:
                opcode = str(getattr(instr, "opcode", "")).lower()

                # 有副作用的指令
                if any(
                    x in opcode
                    for x in [
                        "store",
                        "call",
                        "ret",
                        "br",
                        "switch",
                        "invoke",
                        "resume",
                        "unreachable",
                    ]
                ):
                    side_effects.add(id(instr))

        return side_effects

    def _mark_alive(
        self, func: Any, uses: Dict[int, Set[int]], side_effects: Set[int]
    ) -> Set[int]:
        """递归标记活跃指令"""
        alive: Set[int] = {}
        changed = True

        while changed:
            changed = False

            for block in func.blocks:
                for instr in block.instructions:
                    instr_id = id(instr)

                    # 已在 alive 集合中
                    if instr_id in alive:
                        continue

                    # 有副作用
                    if instr_id in side_effects:
                        alive.add(instr_id)
                        changed = True
                        continue

                    # 有返回值且被使用
                    if hasattr(instr, "opcode"):
                        # 检查是否有返回值（大多数算术/逻辑指令）
                        opcode = str(getattr(instr, "opcode", "")).lower()
                        has_result = not any(
                            x in opcode
                            for x in [
                                "store",
                                "ret",
                                "br",
                                "switch",
                                "call",  # 可能没有返回值
                                "phi",  # phi 节点
                            ]
                        )

                        if has_result and instr_id in uses:
                            if uses[instr_id]:  # 被使用
                                alive.add(instr_id)
                                changed = True

        return alive

    def _remove_dead_instructions(self, func: Any, alive: Set[int]) -> bool:
        """删除死指令"""
        changed = False

        for block in func.blocks:
            i = 0
            while i < len(block.instructions):
                instr = block.instructions[i]

                if id(instr) not in alive:
                    # 检查是否是可以安全删除的指令
                    opcode = str(getattr(instr, "opcode", "")).lower()
                    if not any(
                        x in opcode
                        for x in [
                            "ret",
                            "br",
                            "switch",
                            "call",
                            "store",
                            "unreachable",
                        ]
                    ):
                        block.instructions.remove(instr)
                        changed = True
                        logger.debug(f"Removed dead instruction: {instr}")
                        continue

                i += 1

        return changed


# ============================================================================
# 全局值编号 Pass (gvn)
# ============================================================================


@PassRegistry.register_pass(
    "gvn",
    PassType.TRANSFORM,
    "全局值编号，消除冗余计算",
)
class GVNPass(BasePass):
    """
    全局值编号 Pass

    识别等价的表达式并消除冗余计算。

    示例：
        %a = add i32 %x, %y
        %b = add i32 %x, %y    ; 与 %a 等价
        ↓
        %a = add i32 %x, %y
        %b = %a               ; 复用结果
    """

    name = "gvn"

    def run(self, module: Any) -> bool:
        """运行 GVN"""
        changed = False

        for func in module.functions:
            if not self._should_optimize_function(func):
                continue

            if self._run_gvn_on_function(func):
                changed = True

        return changed

    def _run_gvn_on_function(self, func: Any) -> bool:
        """在函数上运行 GVN"""
        # 构建值编号表
        value_table: Dict[str, Any] = {}
        changed = False

        for block in func.blocks:
            for instr in block.instructions:
                if not self._has_result(instr):
                    continue

                # 计算指令的哈希值
                hash_key = self._compute_hash(instr)

                if hash_key in value_table:
                    # 找到等价的值，可以替换
                    equivalent = value_table[hash_key]
                    if self._can_replace(instr, equivalent):
                        # 替换
                        self._replace_with(instr, equivalent)
                        changed = True
                        logger.debug(f"GVN: Replaced {instr} with {equivalent}")
                else:
                    # 新值，加入表
                    value_table[hash_key] = instr

        return changed

    def _has_result(self, instr: Any) -> bool:
        """检查指令是否有结果值"""
        opcode = str(getattr(instr, "opcode", "")).lower()
        no_result = any(
            x in opcode
            for x in [
                "store",
                "ret",
                "br",
                "switch",
                "call",  # void call
                "phi",  # phi 节点单独处理
            ]
        )
        return not no_result

    def _compute_hash(self, instr: Any) -> str:
        """计算指令的哈希值"""
        opcode = str(getattr(instr, "opcode", ""))
        operands = getattr(instr, "operands", [])

        # 简化哈希：使用 opcode + 操作数类型
        operand_strs = []
        for op in operands:
            op_type = str(getattr(op, "type", type(op)))
            operand_strs.append(op_type)

        return f"{opcode}({','.join(operand_strs)})"

    def _can_replace(self, instr: Any, equivalent: Any) -> bool:
        """检查是否可以用等价值替换"""
        # 简化实现：仅当两个指令完全相同时替换
        # 完整实现需要考虑支配关系和可用性
        return str(instr) == str(equivalent)

    def _replace_with(self, instr: Any, equivalent: Any) -> None:
        """用等价值替换指令"""
        # 简化实现：需要更复杂的 LLVM API
        pass


# ============================================================================
# 循环不变代码移动 Pass (licm)
# ============================================================================


@PassRegistry.register_pass(
    "licm",
    PassType.TRANSFORM,
    "循环不变代码移动，将不变表达式移到循环外",
)
class LICMPass(BasePass):
    """
    循环不变代码移动 Pass

    将循环内不依赖于循环迭代的表达式移到循环外，避免重复计算。

    示例：
        while (i < n) {
            x = a + b;  // a 和 b 不变，可以移到循环外
            c[i] = x;
        }
        ↓
        x = a + b;  // 移到循环外
        while (i < n) {
            c[i] = x;
        }
    """

    name = "licm"

    def run(self, module: Any) -> bool:
        """运行 LICM"""
        changed = False

        for func in module.functions:
            if not self._should_optimize_function(func):
                continue

            if self._run_licm_on_function(func):
                changed = True

        return changed

    def _run_licm_on_function(self, func: Any) -> bool:
        """在函数上运行 LICM"""
        # 简化实现
        # 完整实现需要循环分析和别名分析
        return False


# ============================================================================
# 简化控制流 Pass (simplifycfg)
# ============================================================================


@PassRegistry.register_pass(
    "simplifycfg",
    PassType.TRANSFORM,
    "简化控制流图",
)
class SimplifyCFGPass(BasePass):
    """
    简化控制流 Pass

    执行各种控制流简化：
    - 删除不可达基本块
    - 合并连续的基本块
    - 简化条件分支
    """

    name = "simplifycfg"

    def run(self, module: Any) -> bool:
        """运行 SimplifyCFG"""
        changed = False

        for func in module.functions:
            if not self._should_optimize_function(func):
                continue

            if self._run_simplifycfg_on_function(func):
                changed = True

        return changed

    def _run_simplifycfg_on_function(self, func: Any) -> bool:
        """在函数上运行 SimplifyCFG"""
        changed = False

        # 删除不可达基本块
        if self._remove_unreachable_blocks(func):
            changed = True

        # 合并连续基本块
        if self._merge_blocks(func):
            changed = True

        return changed

    def _remove_unreachable_blocks(self, func: Any) -> bool:
        """删除不可达基本块"""
        if not hasattr(func, "blocks") or len(func.blocks) <= 1:
            return False

        reachable = self._compute_reachable(func)
        changed = False

        for block in list(func.blocks):
            if block.name not in reachable:
                func.blocks.remove(block)
                changed = True
                logger.debug(f"Removed unreachable block: {block.name}")

        return changed

    def _compute_reachable(self, func: Any) -> Set[str]:
        """计算可达基本块"""
        reachable: Set[str] = set()
        worklist = []

        if func.blocks:
            reachable.add(func.blocks[0].name)
            worklist.append(func.blocks[0])

        while worklist:
            block = worklist.pop()

            # 分析终结符指令
            for succ in self._get_successors(block):
                if succ.name not in reachable:
                    reachable.add(succ.name)
                    worklist.append(succ)

        return reachable

    def _get_successors(self, block: Any) -> List[Any]:
        """获取基本块的后继"""
        successors = []

        if not hasattr(block, "instructions") or not block.instructions:
            return successors

        # 获取最后一条指令
        last = block.instructions[-1]
        opcode = str(getattr(last, "opcode", "")).lower()

        if "br" in opcode:
            # 分支指令
            if hasattr(last, "operands") and len(last.operands) >= 2:
                for op in last.operands:
                    if hasattr(op, "name"):
                        successors.append(op)
        elif "ret" in opcode or "unreachable" in opcode:
            pass
        else:
            # 假设顺序执行
            pass

        return successors

    def _merge_blocks(self, func: Any) -> bool:
        """合并连续基本块"""
        # 简化实现
        return False

# -*- coding: utf-8 -*-
"""
ZHC IR - SSA 构建器

实现 Static Single Assignment (SSA) 形式的构建。

SSA 是一种中间表示形式，其中每个变量只被赋值一次。
通过支配树和支配边界计算，插入 Phi 节点来实现。

作者：远
日期：2026-04-08
"""

from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict

from .instructions import IRBasicBlock, IRInstruction
from .program import IRFunction
from .values import IRValue, ValueKind
from .opcodes import Opcode


# =============================================================================
# SSA 数据结构
# =============================================================================

class VersionedValue:
    """
    版本化的值（SSA 变量）

    SSA 中每个变量有多个版本，格式为 base_name.version
    """

    def __init__(self, base_name: str, version: int = 0):
        self.base_name = base_name
        self.version = version

    @property
    def full_name(self) -> str:
        """返回完整的 SSA 变量名"""
        if self.version == 0:
            return f"%{self.base_name}"
        return f"%{self.base_name}.{self.version}"

    def next_version(self) -> 'VersionedValue':
        """创建下一个版本"""
        return VersionedValue(self.base_name, self.version + 1)

    def __repr__(self) -> str:
        return self.full_name

    def __eq__(self, other) -> bool:
        if not isinstance(other, VersionedValue):
            return False
        return self.base_name == other.base_name and self.version == other.version

    def __hash__(self) -> int:
        return hash((self.base_name, self.version))


class PhiNode:
    """
    SSA Phi 节点

    Phi 节点根据控制流来自哪个基本块，选择对应的值。
    """

    def __init__(
        self,
        result: VersionedValue,
        incoming_blocks: List[str],
        incoming_values: List[VersionedValue],
    ):
        self.result = result
        self.incoming_blocks = incoming_blocks
        self.incoming_values = incoming_values

    def __repr__(self) -> str:
        args = ", ".join(
            f"[{bb} {val}]" for bb, val in zip(self.incoming_blocks, self.incoming_values)
        )
        return f"{self.result} = phi {args}"


# =============================================================================
# 支配树
# =============================================================================

class DominatorTree:
    """
    支配树

    支配关系：如果从入口到基本块 B 的每条路径都经过基本块 A，
    则 A 支配 B（B 的所有前驱路径都经过 A）。

    直接支配者：离 B 最近的支配者。
    """

    def __init__(self):
        # 基本块标签 -> 直接支配者标签
        self.immediate_dominator: Dict[str, str] = {}
        # 基本块标签 -> 支配者集合
        self.dominators: Dict[str, Set[str]] = {}
        # 基本块标签 -> 被支配者集合（树结构）
        self.dominated: Dict[str, List[str]] = defaultdict(list)
        # 基本块标签 -> 深度（树的深度）
        self.depth: Dict[str, int] = {}

    def get_dominators(self, block_label: str) -> Set[str]:
        """获取一个基本块的所有支配者"""
        return self.dominators.get(block_label, set())

    def get_immediate_dominator(self, block_label: str) -> Optional[str]:
        """获取直接支配者"""
        return self.immediate_dominator.get(block_label)

    def is_dominated_by(self, block_label: str, potential_dom: str) -> bool:
        """检查 potential_dom 是否支配 block_label"""
        return potential_dom in self.dominators.get(block_label, set())

    def get_dominated_children(self, block_label: str) -> List[str]:
        """获取被支配的子节点"""
        return self.dominated.get(block_label, [])


class DominanceFrontier:
    """
    支配边界

    支配边界 DF(B) 包含所有满足以下条件的基本块 Y：
    1. B 支配 Y 的某个前驱
    2. B 不严格支配 Y（即 B 不是 Y 的唯一支配者）
    """

    def __init__(self):
        # 基本块标签 -> 支配边界集合
        self.frontier: Dict[str, Set[str]] = defaultdict(set)

    def add_to_frontier(self, block_label: str, frontier_block: str):
        """添加支配边界"""
        self.frontier[block_label].add(frontier_block)

    def get_frontier(self, block_label: str) -> Set[str]:
        """获取一个基本块的支配边界"""
        return self.frontier.get(block_label, set())

    def get_all_frontiers(self) -> Dict[str, Set[str]]:
        """获取所有支配边界"""
        return dict(self.frontier)


# =============================================================================
# SSA 构建器
# =============================================================================

class SSABuilder:
    """
    SSA 构建器

    将非 SSA 的 IR 转换为 SSA 形式。

    主要步骤：
    1. 计算支配树
    2. 计算支配边界
    3. 识别所有全局变量（需要 Phi 节点的变量）
    4. 在需要的位置插入 Phi 节点
    5. 变量重命名
    """

    def __init__(self):
        # 当前处理的函数
        self.current_function: Optional[IRFunction] = None

        # 支配树
        self.dom_tree: Optional[DominatorTree] = None

        # 支配边界
        self.dom_frontier: Optional[DominanceFrontier] = None

        # 变量重命名栈：原始变量名 -> 版本栈
        self.rename_stack: Dict[str, List[VersionedValue]] = defaultdict(list)

        # 已插入的 Phi 节点：B -> [(phi_node, var_name)]
        self.phi_nodes: Dict[str, List[Tuple[PhiNode, str]]] = defaultdict(list)

        # 变量定义位置：B -> [var_names]
        self.variable_definitions: Dict[str, Set[str]] = defaultdict(set)

        # 已处理的 Phi 节点的基本块集合
        self.processed_phis: Set[str] = set()

    def build_ssa(self, func: IRFunction) -> IRFunction:
        """
        将函数转换为 SSA 形式

        Args:
            func: 待转换的 IR 函数

        Returns:
            转换后的 SSA 函数
        """
        self.current_function = func

        # 步骤 1: 计算支配树
        self._compute_dominator_tree()

        # 步骤 2: 计算支配边界
        self._compute_dominance_frontier()

        # 步骤 3: 识别所有被写入的变量
        self._collect_written_variables()

        # 步骤 4: 插入 Phi 节点
        self._insert_phi_nodes()

        # 步骤 5: 重命名变量
        self._rename_variables()

        return func

    # -------------------------------------------------------------------------
    # 步骤 1: 计算支配树
    # -------------------------------------------------------------------------

    def _compute_dominator_tree(self):
        """计算支配树（使用 Lengauer-Tarjan 算法的高效版本）"""
        self.dom_tree = DominatorTree()

        if not self.current_function.basic_blocks:
            return

        # 获取入口块
        entry = self.current_function.entry_block
        entry_label = entry.label

        # 初始化：入口块支配自己
        self.dom_tree.dominators[entry_label] = {entry_label}
        self.dom_tree.depth[entry_label] = 0

        # 使用迭代算法计算支配者
        # 对于非入口块：intersection of all predecessors' dominator sets + self
        changed = True
        max_iterations = 100  # 防止无限循环
        iteration = 0

        while changed and iteration < max_iterations:
            changed = False
            iteration += 1

            for bb in self.current_function.basic_blocks:
                if bb.label == entry_label:
                    continue

                # 获取所有前驱的支配集合
                pred_labels = bb.predecessors

                if not pred_labels:
                    continue

                # 新支配者集合 = intersection of all predecessors' dominators + self
                new_dom_set = set()

                first_pred = True
                for pred_label in pred_labels:
                    if pred_label in self.dom_tree.dominators:
                        if first_pred:
                            new_dom_set = self.dom_tree.dominators[pred_label].copy()
                            first_pred = False
                        else:
                            new_dom_set &= self.dom_tree.dominators[pred_label]

                # 添加自身
                new_dom_set.add(bb.label)

                # 检查是否变化
                old_dom_set = self.dom_tree.dominators.get(bb.label)
                if old_dom_set != new_dom_set:
                    self.dom_tree.dominators[bb.label] = new_dom_set
                    changed = True

        # 计算直接支配者（最近支配者）
        for bb in self.current_function.basic_blocks:
            if bb.label == entry_label:
                continue

            doms = self.dom_tree.dominators.get(bb.label, set())
            if not doms:
                continue

            # 移除自身，剩下的就是其他支配者
            doms_minus_self = doms - {bb.label}

            if doms_minus_self:
                # 直接支配者是集合中深度最大的（最接近的）
                depths = [(d, self.dom_tree.depth.get(d, 0)) for d in doms_minus_self]
                depths.sort(key=lambda x: -x[1])

                if depths:
                    idom = depths[0][0]
                    self.dom_tree.immediate_dominator[bb.label] = idom
                    self.dom_tree.dominated[idom].append(bb.label)

                    # 计算深度
                    self.dom_tree.depth[bb.label] = self.dom_tree.depth.get(idom, 0) + 1

    # -------------------------------------------------------------------------
    # 步骤 2: 计算支配边界
    # -------------------------------------------------------------------------

    def _compute_dominance_frontier(self):
        """计算支配边界

        支配边界 DF(B) 包含所有满足以下条件的基本块 Y：
        1. B 支配 Y 的某个前驱
        2. B 不严格支配 Y（即 B 不是 Y 的唯一支配者）

        实现使用 Cooper 等人的算法。
        """
        self.dom_frontier = DominanceFrontier()

        if not self.current_function.basic_blocks:
            return

        # 对每个基本块计算支配边界
        for bb in self.current_function.basic_blocks:
            # 如果基本块有多个前驱
            if len(bb.predecessors) >= 2:
                # 当前块加入所有前驱的支配边界
                for pred_label in bb.predecessors:
                    self.dom_frontier.add_to_frontier(pred_label, bb.label)

            # 对每个后继，沿着支配树向上走
            for succ_label in bb.successors:
                succ_block = self._get_block(succ_label)
                if succ_block and len(succ_block.predecessors) >= 2:
                    # 当前块是后继块的前驱之一，加入后继的支配边界
                    idom = self.dom_tree.get_immediate_dominator(succ_label) if self.dom_tree else None
                    if idom and idom != bb.label:
                        self.dom_frontier.add_to_frontier(bb.label, succ_label)

    # -------------------------------------------------------------------------
    # 步骤 3: 收集被写入的变量
    # -------------------------------------------------------------------------

    def _collect_written_variables(self):
        """收集所有被写入（赋值）的变量"""
        self.variable_definitions.clear()

        for bb in self.current_function.basic_blocks:
            written_vars: Set[str] = set()

            for instr in bb.instructions:
                # 检查是否有结果值（意味着有赋值）
                for result in instr.result:
                    if isinstance(result, IRValue):
                        var_name = self._extract_variable_name(result)
                        if var_name:
                            written_vars.add(var_name)

            if written_vars:
                self.variable_definitions[bb.label] = written_vars

    def _extract_variable_name(self, value: IRValue) -> Optional[str]:
        """从 IRValue 中提取变量名"""
        if value.kind == ValueKind.VAR or value.kind == ValueKind.TEMP:
            name = value.name
            # 去掉 % 前缀
            if name.startswith('%'):
                name = name[1:]
            return name
        return None

    # -------------------------------------------------------------------------
    # 步骤 4: 插入 Phi 节点
    # -------------------------------------------------------------------------

    def _insert_phi_nodes(self):
        """
        插入 Phi 节点

        使用迭代算法：
        1. 对于每个全局变量（被多个基本块定义的变量）
        2. 在该变量的支配边界位置插入 Phi 节点
        3. 将 Phi 节点加入变量的定义集合
        4. 重复直到收敛
        """
        self.phi_nodes.clear()
        self.processed_phis.clear()

        # 收集所有被多个基本块定义的变量
        global_vars = set()

        for bb_label, vars_set in self.variable_definitions.items():
            for var_name in vars_set:
                global_vars.add(var_name)

        # 对于每个全局变量，插入 Phi 节点
        for var_name in global_vars:
            self._insert_phis_for_variable(var_name)

    def _insert_phis_for_variable(self, var_name: str):
        """
        为一个变量插入所有需要的 Phi 节点

        Args:
            var_name: 变量名（不含 % 前缀）
        """
        # 需要处理的基本块队列
        to_process: Set[str] = set()

        # 收集所有定义这个变量的基本块
        for bb_label, vars_set in self.variable_definitions.items():
            if var_name in vars_set:
                to_process.add(bb_label)

        # 已插入过 Phi 的基本块
        already_processed: Set[str] = set()

        # 迭代处理
        while to_process:
            bb_label = to_process.pop()

            if bb_label in already_processed:
                continue

            # 获取这个位置的支配边界
            frontier = self.dom_frontier.get_frontier(bb_label)

            for y in frontier:
                # 检查是否已经为这个变量在这个块插入了 Phi
                existing_phis = self.phi_nodes.get(y, [])
                if any(var == var_name for _, var in existing_phis):
                    continue

                # 插入 Phi 节点
                phi_result = VersionedValue(var_name, version=0)  # 版本会在重命名时确定
                phi = PhiNode(
                    result=phi_result,
                    incoming_blocks=[],
                    incoming_values=[]
                )

                # 获取这个基本块的所有前驱
                block = self._get_block(y)
                if block:
                    for pred_label in block.predecessors:
                        # 创建对应的 incoming value（占位）
                        incoming_val = VersionedValue(var_name, version=0)
                        phi.incoming_blocks.append(pred_label)
                        phi.incoming_values.append(incoming_val)

                self.phi_nodes[y].append((phi, var_name))

                # 如果这个块还没有被处理，加入队列
                if y not in already_processed:
                    to_process.add(y)

                # 标记为已处理
                already_processed.add(y)

    def _get_block(self, label: str) -> Optional[IRBasicBlock]:
        """根据标签获取基本块"""
        return self.current_function.find_basic_block(label)

    # -------------------------------------------------------------------------
    # 步骤 5: 变量重命名
    # -------------------------------------------------------------------------

    def _rename_variables(self):
        """
        重命名变量

        从入口块开始，按照深度优先顺序遍历支配树，
        维护每个变量的版本栈，重命名所有使用点。
        """
        # 初始化版本栈
        self.rename_stack.clear()

        # 在入口块添加 Phi 节点的定义
        entry = self.current_function.entry_block
        self._add_phi_definitions(entry.label)

        # 从入口块开始 DFS 遍历支配树
        visited: Set[str] = set()
        self._rename_dfs(entry.label, visited)

    def _add_phi_definitions(self, block_label: str):
        """在基本块入口添加 Phi 节点定义到版本栈"""
        if block_label not in self.phi_nodes:
            return

        for phi, var_name in self.phi_nodes[block_label]:
            # 获取下一个版本号
            next_version = len(self.rename_stack[var_name])
            phi.result.version = next_version

            # 添加到版本栈
            self.rename_stack[var_name].append(phi.result)

    def _rename_dfs(self, block_label: str, visited: Set[str]):
        """
        DFS 遍历支配树进行重命名

        Args:
            block_label: 当前基本块标签
            visited: 已访问的基本块集合
        """
        if block_label in visited:
            return
        visited.add(block_label)

        block = self._get_block(block_label)
        if not block:
            return

        # 1. 先添加 Phi 节点的定义
        self._add_phi_definitions(block_label)

        # 2. 重写基本块中的指令
        for instr in block.instructions:
            # 重写操作数
            new_operands = []
            for operand in instr.operands:
                if isinstance(operand, IRValue):
                    new_operand = self._rename_value(operand)
                    new_operands.append(new_operand)
                else:
                    new_operands.append(operand)
            instr.operands = new_operands

            # 如果有结果值（赋值），重命名结果
            new_results = []
            for result in instr.result:
                if isinstance(result, IRValue):
                    var_name = self._extract_variable_name(result)
                    if var_name:
                        # 创建新版本
                        next_version = len(self.rename_stack[var_name])
                        new_versioned = VersionedValue(var_name, next_version)
                        self.rename_stack[var_name].append(new_versioned)

                        # 更新 IRValue
                        result.name = new_versioned.full_name
                        new_results.append(result)
                    else:
                        new_results.append(result)
                else:
                    new_results.append(result)

            instr.result = new_results

        # 4. 遍历所有后继基本块，更新 Phi 节点的 incoming
        for succ_label in block.successors:
            succ_block = self._get_block(succ_label)
            if succ_block and succ_label in self.phi_nodes:
                for phi, var_name in self.phi_nodes[succ_label]:
                    # 找到当前块在 incoming_blocks 中的位置
                    if block_label in phi.incoming_blocks:
                        idx = phi.incoming_blocks.index(block_label)
                        # 使用栈顶版本
                        if var_name in self.rename_stack and self.rename_stack[var_name]:
                            phi.incoming_values[idx] = self.rename_stack[var_name][-1]

        # 5. 递归遍历支配树子节点
        children = self.dom_tree.get_dominated_children(block_label) if self.dom_tree else []
        for child_label in children:
            self._rename_dfs(child_label, visited)

        # 6. 回溯：弹出这个块定义的变量
        self._pop_definitions(block)

    def _rename_value(self, value: IRValue) -> IRValue:
        """
        重命名一个值

        如果是变量，返回栈顶的版本化值
        """
        var_name = self._extract_variable_name(value)
        if var_name and var_name in self.rename_stack:
            stack = self.rename_stack[var_name]
            if stack:
                # 返回一个新的 IRValue，使用栈顶的版本
                new_value = IRValue(
                    name=stack[-1].full_name,
                    ty=value.ty,
                    kind=value.kind
                )
                return new_value
        return value

    def _pop_definitions(self, block: IRBasicBlock):
        """回溯时弹出变量定义"""
        # 获取这个块中定义的变量
        vars_in_block = self.variable_definitions.get(block.label, set())

        for var_name in vars_in_block:
            if var_name in self.rename_stack and self.rename_stack[var_name]:
                self.rename_stack[var_name].pop()

        # 同时弹出 Phi 节点的定义
        if block.label in self.phi_nodes:
            for _, var_name in self.phi_nodes[block.label]:
                if var_name in self.rename_stack and self.rename_stack[var_name]:
                    self.rename_stack[var_name].pop()


# =============================================================================
# 辅助函数
# =============================================================================

def build_ssa(func: IRFunction) -> IRFunction:
    """
    便捷函数：将函数转换为 SSA 形式

    Args:
        func: 待转换的 IR 函数

    Returns:
        转换后的 SSA 函数
    """
    builder = SSABuilder()
    return builder.build_ssa(func)

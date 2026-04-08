# -*- coding: utf-8 -*-
"""
ZHC IR - SSA 构建器

实现 Static Single Assignment (SSA) 形式的构建。

## SSA 简介

SSA（Static Single Assignment，静态单赋值）是一种重要的中间表示形式，
其核心特点是每个变量只能被赋值一次。这一特性简化了数据流分析，
使得许多编译器优化算法变得更加简单和高效。

### 为什么需要 SSA？

传统的 IR 中，同一个变量可以被多次赋值：

    传统 IR（非 SSA）：
    %a = 1
    %a = %a + 1    ; %a 被重新赋值
    %b = %a        ; 不清楚 %a 指哪个版本

SSA 通过引入版本号来解决这个问题：

    SSA 形式：
    %a.0 = 1
    %a.1 = add %a.0, 1
    %b = %a.1       ; 明确使用最新版本

### Phi 节点

在控制流汇合处，需要"选择"来自不同路径的值，这就是 Phi 节点的作用：

    if (cond) {
        %a.0 = 1
    } else {
        %a.1 = 2
    }
    ; 这里 %a 可能是 %a.0 或 %a.1，需要 Phi 节点
    %a.2 = phi [%a.0, %entry], [%a.1, %else]

## 算法概述

SSA 构建的核心问题是：哪些位置需要插入 Phi 节点？

答案在支配边界（Dominance Frontier）中：
- 如果基本块 B 定义了变量 V
- 那么在 V 的支配边界上的每个基本块都需要一个 Phi 节点

### 构建步骤

1. **计算支配树**：使用 Lengauer-Tarjan 算法，O(N α(N)) 复杂度
2. **计算支配边界**：找出所有需要 Phi 节点的位置
3. **收集全局变量**：找出所有被多个基本块定义的变量
4. **插入 Phi 节点**：在支配边界位置插入
5. **重命名变量**：DFS 遍历支配树，维护版本栈

## 核心数据结构

- **VersionedValue**: SSA 版本化变量，格式 `base.version`
- **PhiNode**: Phi 节点，表示控制流汇合处的值选择
- **DominatorTree**: 支配树，表示基本块之间的支配关系
- **DominanceFrontier**: 支配边界，每个基本块需要 Phi 节点的位置

## 参考文献

1. Cytron, R., et al. "Efficiently Computing Static Single Assignment Form
   and the Control Dependence Graph." TOPLAS 1991.
2. Lengauer, T., & Tarjan, R. E. "A Fast Algorithm for Finding Dominators
   in a Flowgraph." TOPLAS 1979.

作者：远
日期：2026-04-08
"""

from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict

from .instructions import IRBasicBlock, IRInstruction
from .program import IRFunction
from .values import IRValue, ValueKind
from .opcodes import Opcode
from .dominator import LengauerTarjanDominator, build_dominator_tree_iterative


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
        """计算支配树（使用 Lengauer-Tarjan 算法）
        
        ## 支配关系定义
        
        基本块 A **支配** 基本块 B，当且仅当从入口到 B 的每条路径都经过 A。
        记作 A dom B。
        
        基本块 A **直接支配** 基本块 B，当且仅当：
        1. A 支配 B
        2. A 不是 B
        3. 不存在 C，使得 A 支配 C 且 C 支配 B
        
        记作 A idom B。直接支配关系形成一棵树，称为支配树。
        
        ## 算法选择
        
        本实现使用 Lengauer-Tarjan 算法，时间复杂度 O(N α(N))，
        其中 N 是基本块数量，α 是反阿克曼函数（实际中接近常数）。
        
        相比简单的迭代算法（O(N²)），Lengauer-Tarjan 在大型 CFG 上
        有显著的性能优势。
        
        ## 实现细节
        
        1. 构建控制流图（CFG）的邻接表表示
        2. 调用 LengauerTarjanDominator.build() 计算直接支配者
        3. 从直接支配者推导支配者集合
        4. 计算支配树深度（用于后续遍历）
        """
        self.dom_tree = DominatorTree()

        if not self.current_function.basic_blocks:
            return

        # 获取入口块
        entry = self.current_function.entry_block
        entry_label = entry.label

        # 构建控制流图
        blocks = {}
        for bb in self.current_function.basic_blocks:
            blocks[bb.label] = (bb.predecessors, bb.successors)

        # 使用高效的 Lengauer-Tarjan 算法（O(N α(N))）
        builder = LengauerTarjanDominator()
        idom = builder.build(entry_label, blocks)

        # 更新 SSABuilder 的支配树
        for block_label, immediate_dom in idom.items():
            # 计算支配者集合
            doms = builder.get_dominators(block_label)
            self.dom_tree.dominators[block_label] = doms

            # 设置直接支配者
            if block_label != immediate_dom:
                self.dom_tree.immediate_dominator[block_label] = immediate_dom
                self.dom_tree.dominated[immediate_dom].append(block_label)

        # 设置支配树深度
        depth = builder.get_dominator_depth()
        for block_label, d in depth.items():
            self.dom_tree.depth[block_label] = d

    # -------------------------------------------------------------------------
    # 步骤 2: 计算支配边界
    # -------------------------------------------------------------------------

    def _compute_dominance_frontier(self):
        """计算支配边界
        
        ## 支配边界定义
        
        基本块 B 的支配边界 DF(B) 包含所有满足以下条件的基本块 Y：
        1. B 支配 Y 的某个前驱 P（即 B 是 P 的支配者）
        2. B 不严格支配 Y（即 B 不是 Y 的唯一支配者）
        
        ## 直观理解
        
        支配边界可以理解为：变量在 B 中定义后，
        "流出"B 的所有位置就是 DF(B)。
        
        例子：
        
            A ──→ B ──→ C
            └──→ D ──→ C
                      ↑
                    汇合
        
        如果 B 定义了变量 x：
        - C 是 x 的支配边界（因为 B 支配 C 的前驱 D，且 B 不支配 C）
        - D 不是支配边界（因为 x 没有在 B 到 D 的路径上被"传播"）
        
        ## 算法（Cooper 等人）
        
        对于每个基本块 X：
        1. 如果 X 有多个前驱，则每个前驱 P 都将 X 加入 DF(P)
        2. 对于 X 的每个后继 Y，如果 X 不是 Y 的直接支配者，
           则将 Y 加入 DF(X)
        
        ## 为什么需要支配边界？
        
        支配边界精确地告诉我们：为了使变量 V 在 SSA 形式下正确工作，
        必须在哪些基本块的入口插入 Phi 节点。
        
        具体来说：
        - 如果块 B 定义了变量 V
        - 那么 V 的支配边界 DF(B) 上的每个基本块
        - 都需要为 V 插入一个 Phi 节点
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
        
        ## 算法思想
        
        使用迭代算法，基于支配边界计算需要插入 Phi 节点的位置。
        
        核心观察：
        - 如果块 B 定义了变量 V
        - 那么 V 的支配边界 DF(B) 上的每个基本块都需要一个 Phi 节点
        - Phi 节点本身也是一个定义，可能触发更多的 Phi 节点
        
        ## 算法步骤
        
        1. 收集所有全局变量（被多个基本块定义的变量）
        2. 对于每个全局变量 V：
           a. 找出所有定义 V 的基本块
           b. 对于每个定义块 B，遍历 DF(B)
           c. 在 DF(B) 中的每个块 Y 插入 Phi 节点
           d. 将 Y 加入待处理队列（因为 Phi 也是定义）
           e. 重复直到队列为空
        
        ## 工作列表算法
        
        使用工作列表（worklist）避免重复处理：
        
            worklist = {定义 V 的所有基本块}
            processed = {}
            
            while worklist not empty:
                B = worklist.pop()
                for Y in DF(B):
                    if Y not in processed:
                        insert_phi(V, Y)
                        worklist.add(Y)
                        processed.add(Y)
        
        ## Phi 节点结构
        
        Phi 节点格式：
        
            %result = phi [value1, block1], [value2, block2], ...
        
        含义：如果控制流来自 block_i，则 result = value_i
        
        ## 示例
        
        原始代码：
        
            if (cond) {
                x = 1;
            } else {
                x = 2;
            }
            y = x;  // 这里需要 Phi 节点
        
        SSA 形式：
        
            if.then:
                %x.0 = 1
                br if.end
            
            if.else:
                %x.1 = 2
                br if.end
            
            if.end:
                %x.2 = phi [%x.0, if.then], [%x.1, if.else]
                %y = %x.2
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
        
        ## 算法思想
        
        使用 DFS 遍历支配树，维护每个变量的版本栈。
        在遍历过程中：
        - 遇到变量定义：创建新版本，压入栈
        - 遇到变量使用：使用栈顶版本
        - 离开基本块：弹出该块定义的版本
        
        ## 版本栈
        
        对于每个变量 V，维护一个版本栈：
        
            stack[V] = [V.0, V.1, V.2, ...]
        
        栈顶是当前可见的最新版本。
        
        ## 算法步骤
        
        1. 初始化所有变量的版本栈为空
        2. 从入口块开始 DFS 遍历支配树
        3. 对于每个基本块 B：
           a. 添加 Phi 节点的定义到版本栈
           b. 重写基本块中的指令：
              - 操作数：使用栈顶版本
              - 结果：创建新版本，压入栈
           c. 更新后继基本块的 Phi 节点 incoming 值
           d. 递归处理支配树子节点
           e. 回溯：弹出该块定义的所有版本
        
        ## 为什么沿支配树遍历？
        
        支配树保证了：
        - 父节点定义的变量在子节点中可见
        - 子节点定义的变量不影响父节点
        - 版本栈的压入/弹出顺序正确
        
        ## 示例
        
        原始代码：
        
            entry:
                %x = 1
                br loop
            
            loop:
                %x = add %x, 1
                br exit
            
            exit:
                %y = %x
        
        重命名过程：
        
            entry:
                stack[x] = []
                %x.0 = 1
                stack[x].push(x.0)  // stack[x] = [x.0]
                br loop
            
            loop:
                %x.1 = add stack[x].top(), 1  // 使用 x.0
                stack[x].push(x.1)  // stack[x] = [x.0, x.1]
                br exit
            
            exit:
                %y = stack[x].top()  // 使用 x.1
            
            回溯 loop:
                stack[x].pop()  // stack[x] = [x.0]
            
            回溯 entry:
                stack[x].pop()  // stack[x] = []
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

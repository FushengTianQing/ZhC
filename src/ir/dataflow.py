# -*- coding: utf-8 -*-
"""
ZHC IR - 数据流分析框架

实现经典的数据流分析算法：
- 活跃变量分析 (Liveness Analysis)
- 到达定义分析 (Reaching Definitions)
- 可用表达式分析 (Available Expressions)

作者：远
日期：2026-04-08
"""

from typing import Dict, Set, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass

from .instructions import IRBasicBlock, IRInstruction
from .program import IRFunction
from .values import IRValue, ValueKind
from .opcodes import Opcode


# =============================================================================
# 数据流分析基类
# =============================================================================

@dataclass
class DataFlowResult:
    """数据流分析结果"""
    # 基本块标签 -> 入口状态
    in_state: Dict[str, Set[str]]
    # 基本块标签 -> 出口状态
    out_state: Dict[str, Set[str]]
    # 是否收敛
    converged: bool
    # 迭代次数
    iterations: int


class DataFlowAnalysis:
    """
    数据流分析基类

    实现通用的数据流分析框架，支持前向和后向分析。
    """

    def __init__(self, function: IRFunction):
        self.function = function

        # 基本块标签 -> 基本块
        self.blocks: Dict[str, IRBasicBlock] = {}
        for bb in function.basic_blocks:
            self.blocks[bb.label] = bb

        # 分析结果
        self.result: Optional[DataFlowResult] = None

    def analyze(self, max_iterations: int = 100) -> DataFlowResult:
        """
        执行数据流分析

        Args:
            max_iterations: 最大迭代次数

        Returns:
            分析结果
        """
        raise NotImplementedError

    def _get_predecessors(self, block_label: str) -> List[str]:
        """获取前驱基本块"""
        block = self.blocks.get(block_label)
        return block.predecessors if block else []

    def _get_successors(self, block_label: str) -> List[str]:
        """获取后继基本块"""
        block = self.blocks.get(block_label)
        return block.successors if block else []


# =============================================================================
# 活跃变量分析
# =============================================================================

class LivenessAnalysis(DataFlowAnalysis):
    """
    活跃变量分析（后向数据流分析）

    活跃变量：如果从程序点 p 到程序出口的某条路径上使用了变量 v，
    且在使用前没有重新定义，则 v 在 p 点活跃。

    用途：
    - 寄存器分配
    - 死代码消除
    - 优化存储操作

    方程：
    - OUT[B] = ∪ IN[S] for S in successors(B)
    - IN[B] = use[B] ∪ (OUT[B] - def[B])
    """

    def __init__(self, function: IRFunction):
        super().__init__(function)

        # 基本块标签 -> 定义的变量集合
        self.def_sets: Dict[str, Set[str]] = defaultdict(set)
        # 基本块标签 -> 使用的变量集合
        self.use_sets: Dict[str, Set[str]] = defaultdict(set)

        # 计算每个基本块的 def 和 use 集合
        self._compute_def_use_sets()

    def _compute_def_use_sets(self):
        """计算每个基本块的 def 和 use 集合"""
        for label, block in self.blocks.items():
            # 已定义的变量（在当前块中）
            defined: Set[str] = set()
            # 使用的变量（在定义前使用）
            used: Set[str] = set()

            for instr in block.instructions:
                # 处理操作数（使用）
                for operand in instr.operands:
                    if isinstance(operand, IRValue):
                        var_name = self._extract_variable_name(operand)
                        if var_name and var_name not in defined:
                            used.add(var_name)

                # 处理结果（定义）
                for result in instr.result:
                    if isinstance(result, IRValue):
                        var_name = self._extract_variable_name(result)
                        if var_name:
                            defined.add(var_name)

            self.def_sets[label] = defined
            self.use_sets[label] = used

    def _extract_variable_name(self, value: IRValue) -> Optional[str]:
        """从 IRValue 中提取变量名"""
        if value.kind == ValueKind.VAR or value.kind == ValueKind.TEMP:
            name = value.name
            if name.startswith('%'):
                name = name[1:]
            return name
        return None

    def analyze(self, max_iterations: int = 100) -> DataFlowResult:
        """
        执行活跃变量分析

        使用后向数据流分析，从出口向入口传播。
        """
        # 初始化：所有基本块的 IN 和 OUT 都为空集
        in_state: Dict[str, Set[str]] = {label: set() for label in self.blocks}
        out_state: Dict[str, Set[str]] = {label: set() for label in self.blocks}

        # 按逆后序遍历（提高收敛速度）
        rpo_order = self._reverse_postorder()

        converged = False
        iterations = 0

        for iteration in range(max_iterations):
            iterations = iteration + 1
            changed = False

            # 按逆后序遍历所有基本块
            for label in rpo_order:
                # OUT[B] = ∪ IN[S] for S in successors(B)
                new_out: Set[str] = set()
                for succ in self._get_successors(label):
                    new_out |= in_state[succ]

                # IN[B] = use[B] ∪ (OUT[B] - def[B])
                new_in = self.use_sets[label] | (new_out - self.def_sets[label])

                # 检查是否变化
                if new_in != in_state[label] or new_out != out_state[label]:
                    changed = True

                in_state[label] = new_in
                out_state[label] = new_out

            if not changed:
                converged = True
                break

        self.result = DataFlowResult(
            in_state=in_state,
            out_state=out_state,
            converged=converged,
            iterations=iterations
        )

        return self.result

    def _reverse_postorder(self) -> List[str]:
        """计算逆后序遍历顺序"""
        visited: Set[str] = set()
        order: List[str] = []

        def dfs(label: str):
            if label in visited:
                return
            visited.add(label)

            for succ in self._get_successors(label):
                dfs(succ)

            order.append(label)

        # 从入口块开始
        if self.function.entry_block:
            dfs(self.function.entry_block.label)

        # 逆序
        order.reverse()
        return order

    def is_live_at(self, block_label: str, var_name: str) -> bool:
        """
        检查变量在基本块入口是否活跃

        Args:
            block_label: 基本块标签
            var_name: 变量名

        Returns:
            是否活跃
        """
        if not self.result:
            return False
        return var_name in self.result.in_state.get(block_label, set())

    def get_live_variables(self, block_label: str) -> Set[str]:
        """获取基本块入口的活跃变量集合"""
        if not self.result:
            return set()
        return self.result.in_state.get(block_label, set())


# =============================================================================
# 到达定义分析
# =============================================================================

@dataclass
class Definition:
    """变量定义"""
    variable: str  # 变量名
    block_label: str  # 定义所在的基本块
    instruction_index: int  # 指令在基本块中的索引

    def __repr__(self) -> str:
        return f"{self.variable}@{self.block_label}:{self.instruction_index}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Definition):
            return False
        return (self.variable == other.variable and
                self.block_label == other.block_label and
                self.instruction_index == other.instruction_index)

    def __hash__(self) -> int:
        return hash((self.variable, self.block_label, self.instruction_index))


class ReachingDefinitionsAnalysis(DataFlowAnalysis):
    """
    到达定义分析（前向数据流分析）

    到达定义：如果从定义点 d 到程序点 p 的某条路径上没有对变量 v 的其他定义，
    则定义 d 到达 p。

    用途：
    - 常量传播
    - 复制传播
    - 未初始化变量检测

    方程：
    - IN[B] = ∩ OUT[P] for P in predecessors(B)
    - OUT[B] = gen[B] ∪ (IN[B] - kill[B])
    """

    def __init__(self, function: IRFunction):
        super().__init__(function)

        # 基本块标签 -> 生成的定义集合
        self.gen_sets: Dict[str, Set[Definition]] = defaultdict(set)
        # 基本块标签 -> 杀死的定义集合
        self.kill_sets: Dict[str, Set[Definition]] = defaultdict(set)

        # 所有定义
        self.all_definitions: Set[Definition] = set()

        # 计算每个基本块的 gen 和 kill 集合
        self._compute_gen_kill_sets()

    def _compute_gen_kill_sets(self):
        """计算每个基本块的 gen 和 kill 集合"""
        # 首先收集所有定义
        for label, block in self.blocks.items():
            for idx, instr in enumerate(block.instructions):
                for result in instr.result:
                    if isinstance(result, IRValue):
                        var_name = self._extract_variable_name(result)
                        if var_name:
                            defn = Definition(
                                variable=var_name,
                                block_label=label,
                                instruction_index=idx
                            )
                            self.all_definitions.add(defn)

        # 计算每个基本块的 gen 和 kill
        for label, block in self.blocks.items():
            generated: Set[Definition] = set()
            killed: Set[Definition] = set()

            for idx, instr in enumerate(block.instructions):
                for result in instr.result:
                    if isinstance(result, IRValue):
                        var_name = self._extract_variable_name(result)
                        if var_name:
                            # 新定义
                            defn = Definition(
                                variable=var_name,
                                block_label=label,
                                instruction_index=idx
                            )
                            generated.add(defn)

                            # 杀死其他同名变量的定义
                            for other_def in self.all_definitions:
                                if other_def.variable == var_name and other_def != defn:
                                    killed.add(other_def)

            self.gen_sets[label] = generated
            self.kill_sets[label] = killed

    def _extract_variable_name(self, value: IRValue) -> Optional[str]:
        """从 IRValue 中提取变量名"""
        if value.kind == ValueKind.VAR or value.kind == ValueKind.TEMP:
            name = value.name
            if name.startswith('%'):
                name = name[1:]
            return name
        return None

    def analyze(self, max_iterations: int = 100) -> DataFlowResult:
        """
        执行到达定义分析

        使用前向数据流分析，从入口向出口传播。
        """
        # 初始化：入口块的 IN 为空，其他块的 IN 为所有定义
        in_state: Dict[str, Set[str]] = {}
        out_state: Dict[str, Set[str]] = {}

        for label in self.blocks:
            if label == self.function.entry_block.label:
                in_state[label] = set()
            else:
                # 初始化为所有定义（用于 may 分析）
                in_state[label] = {str(d) for d in self.all_definitions}
            out_state[label] = {str(d) for d in self.gen_sets[label]}

        # 按后序遍历
        po_order = self._postorder()

        converged = False
        iterations = 0

        for iteration in range(max_iterations):
            iterations = iteration + 1
            changed = False

            for label in po_order:
                # IN[B] = ∩ OUT[P] for P in predecessors(B)
                # 注意：对于 may 分析，应该用 ∪
                new_in: Set[str] = set()
                preds = self._get_predecessors(label)
                if preds:
                    for pred in preds:
                        new_in |= out_state[pred]
                else:
                    # 入口块
                    new_in = set()

                # OUT[B] = gen[B] ∪ (IN[B] - kill[B])
                new_out = {str(d) for d in self.gen_sets[label]}
                for def_str in new_in:
                    # 检查是否被杀死
                    defn = self._parse_definition(def_str)
                    if defn and defn not in self.kill_sets[label]:
                        new_out.add(def_str)

                # 检查是否变化
                if new_in != in_state[label] or new_out != out_state[label]:
                    changed = True

                in_state[label] = new_in
                out_state[label] = new_out

            if not changed:
                converged = True
                break

        self.result = DataFlowResult(
            in_state=in_state,
            out_state=out_state,
            converged=converged,
            iterations=iterations
        )

        return self.result

    def _postorder(self) -> List[str]:
        """计算后序遍历顺序"""
        visited: Set[str] = set()
        order: List[str] = []

        def dfs(label: str):
            if label in visited:
                return
            visited.add(label)

            for pred in self._get_predecessors(label):
                dfs(pred)

            order.append(label)

        # 从所有块开始
        for label in self.blocks:
            dfs(label)

        return order

    def _parse_definition(self, def_str: str) -> Optional[Definition]:
        """解析定义字符串"""
        try:
            # 格式: variable@block:index
            parts = def_str.split('@')
            if len(parts) != 2:
                return None

            variable = parts[0]
            rest = parts[1].split(':')
            if len(rest) != 2:
                return None

            block_label = rest[0]
            instruction_index = int(rest[1])

            return Definition(
                variable=variable,
                block_label=block_label,
                instruction_index=instruction_index
            )
        except:
            return None

    def get_reaching_definitions(self, block_label: str, var_name: str) -> Set[Definition]:
        """
        获取到达某个基本块入口的变量定义

        Args:
            block_label: 基本块标签
            var_name: 变量名

        Returns:
            到达的定义集合
        """
        if not self.result:
            return set()

        definitions: Set[Definition] = set()
        for def_str in self.result.in_state.get(block_label, set()):
            defn = self._parse_definition(def_str)
            if defn and defn.variable == var_name:
                definitions.add(defn)

        return definitions


# =============================================================================
# 可用表达式分析
# =============================================================================

@dataclass
class Expression:
    """表达式"""
    operator: str  # 操作符
    operands: Tuple[str, ...]  # 操作数

    def __repr__(self) -> str:
        operands_str = ", ".join(self.operands)
        return f"{self.operator}({operands_str})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Expression):
            return False
        return self.operator == other.operator and self.operands == other.operands

    def __hash__(self) -> int:
        return hash((self.operator, self.operands))


class AvailableExpressionsAnalysis(DataFlowAnalysis):
    """
    可用表达式分析（前向数据流分析）

    可用表达式：如果从程序入口到程序点 p 的所有路径上都计算了表达式 e，
    且在最后一次计算后没有操作数被重新定义，则 e 在 p 点可用。

    用途：
    - 公共子表达式消除
    - 优化重复计算

    方程：
    - IN[B] = ∩ OUT[P] for P in predecessors(B)
    - OUT[B] = gen[B] ∪ (IN[B] - kill[B])
    """

    def __init__(self, function: IRFunction):
        super().__init__(function)

        # 基本块标签 -> 生成的表达式集合
        self.gen_sets: Dict[str, Set[Expression]] = defaultdict(set)
        # 基本块标签 -> 杀死的表达式集合
        self.kill_sets: Dict[str, Set[Expression]] = defaultdict(set)

        # 所有表达式
        self.all_expressions: Set[Expression] = set()

        # 计算每个基本块的 gen 和 kill 集合
        self._compute_gen_kill_sets()

    def _compute_gen_kill_sets(self):
        """计算每个基本块的 gen 和 kill 集合"""
        # 首先收集所有表达式
        for label, block in self.blocks.items():
            for instr in block.instructions:
                expr = self._extract_expression(instr)
                if expr:
                    self.all_expressions.add(expr)

        # 计算每个基本块的 gen 和 kill
        for label, block in self.blocks.items():
            generated: Set[Expression] = set()
            killed: Set[Expression] = set()

            # 记录当前块中定义的变量
            defined_vars: Set[str] = set()

            for instr in block.instructions:
                # 提取表达式
                expr = self._extract_expression(instr)
                if expr:
                    generated.add(expr)

                # 提取定义的变量
                for result in instr.result:
                    if isinstance(result, IRValue):
                        var_name = self._extract_variable_name(result)
                        if var_name:
                            defined_vars.add(var_name)

            # 杀死包含已定义变量的表达式
            for expr in self.all_expressions:
                for operand in expr.operands:
                    if operand in defined_vars:
                        killed.add(expr)
                        break

            self.gen_sets[label] = generated
            self.kill_sets[label] = killed

    def _extract_expression(self, instr: IRInstruction) -> Optional[Expression]:
        """从指令中提取表达式"""
        # 只处理二元运算和比较运算
        if instr.opcode in [
            Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.DIV, Opcode.MOD,
            Opcode.AND, Opcode.OR, Opcode.XOR,
            Opcode.EQ, Opcode.NE, Opcode.LT, Opcode.LE, Opcode.GT, Opcode.GE
        ]:
            if len(instr.operands) >= 2:
                operands = []
                for op in instr.operands[:2]:
                    if isinstance(op, IRValue):
                        var_name = self._extract_variable_name(op)
                        if var_name:
                            operands.append(var_name)
                        else:
                            operands.append(op.name)
                    else:
                        operands.append(str(op))

                if len(operands) == 2:
                    return Expression(
                        operator=instr.opcode.name,
                        operands=tuple(operands)
                    )

        return None

    def _extract_variable_name(self, value: IRValue) -> Optional[str]:
        """从 IRValue 中提取变量名"""
        if value.kind == ValueKind.VAR or value.kind == ValueKind.TEMP:
            name = value.name
            if name.startswith('%'):
                name = name[1:]
            return name
        return None

    def analyze(self, max_iterations: int = 100) -> DataFlowResult:
        """
        执行可用表达式分析

        使用前向数据流分析，从入口向出口传播。
        """
        # 初始化：入口块的 IN 为空，其他块的 IN 为所有表达式
        in_state: Dict[str, Set[str]] = {}
        out_state: Dict[str, Set[str]] = {}

        for label in self.blocks:
            if label == self.function.entry_block.label:
                in_state[label] = set()
            else:
                # 初始化为所有表达式（must 分析的初始化）
                in_state[label] = {str(e) for e in self.all_expressions}
            out_state[label] = {str(e) for e in self.gen_sets[label]}

        # 按后序遍历
        po_order = self._postorder()

        converged = False
        iterations = 0

        for iteration in range(max_iterations):
            iterations = iteration + 1
            changed = False

            for label in po_order:
                # IN[B] = ∩ OUT[P] for P in predecessors(B)
                new_in: Set[str] = set()
                preds = self._get_predecessors(label)
                if preds:
                    # 对于 must 分析，使用交集
                    first = True
                    for pred in preds:
                        if first:
                            new_in = out_state[pred].copy()
                            first = False
                        else:
                            new_in &= out_state[pred]
                else:
                    # 入口块
                    new_in = set()

                # OUT[B] = gen[B] ∪ (IN[B] - kill[B])
                new_out = {str(e) for e in self.gen_sets[label]}
                for expr_str in new_in:
                    # 检查是否被杀死
                    expr = self._parse_expression(expr_str)
                    if expr and expr not in self.kill_sets[label]:
                        new_out.add(expr_str)

                # 检查是否变化
                if new_in != in_state[label] or new_out != out_state[label]:
                    changed = True

                in_state[label] = new_in
                out_state[label] = new_out

            if not changed:
                converged = True
                break

        self.result = DataFlowResult(
            in_state=in_state,
            out_state=out_state,
            converged=converged,
            iterations=iterations
        )

        return self.result

    def _postorder(self) -> List[str]:
        """计算后序遍历顺序"""
        visited: Set[str] = set()
        order: List[str] = []

        def dfs(label: str):
            if label in visited:
                return
            visited.add(label)

            for pred in self._get_predecessors(label):
                dfs(pred)

            order.append(label)

        for label in self.blocks:
            dfs(label)

        return order

    def _parse_expression(self, expr_str: str) -> Optional[Expression]:
        """解析表达式字符串"""
        try:
            # 格式: operator(op1, op2)
            parts = expr_str.split('(')
            if len(parts) != 2:
                return None

            operator = parts[0]
            operands_str = parts[1].rstrip(')')
            operands = tuple(op.strip() for op in operands_str.split(','))

            return Expression(operator=operator, operands=operands)
        except:
            return None

    def is_available(self, block_label: str, expr: Expression) -> bool:
        """
        检查表达式在基本块入口是否可用

        Args:
            block_label: 基本块标签
            expr: 表达式

        Returns:
            是否可用
        """
        if not self.result:
            return False
        return str(expr) in self.result.in_state.get(block_label, set())


# =============================================================================
# 便捷函数
# =============================================================================

def analyze_liveness(function: IRFunction) -> DataFlowResult:
    """
    便捷函数：执行活跃变量分析

    Args:
        function: IR 函数

    Returns:
        分析结果
    """
    analysis = LivenessAnalysis(function)
    return analysis.analyze()


def analyze_reaching_definitions(function: IRFunction) -> DataFlowResult:
    """
    便捷函数：执行到达定义分析

    Args:
        function: IR 函数

    Returns:
        分析结果
    """
    analysis = ReachingDefinitionsAnalysis(function)
    return analysis.analyze()


def analyze_available_expressions(function: IRFunction) -> DataFlowResult:
    """
    便捷函数：执行可用表达式分析

    Args:
        function: IR 函数

    Returns:
        分析结果
    """
    analysis = AvailableExpressionsAnalysis(function)
    return analysis.analyze()

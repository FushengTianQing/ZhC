"""
空指针检测分析器

检测可能的空指针解引用。

Phase 4 - Stage 3 - Task 14.3
"""

from typing import List, Dict, Any, Set, Optional

from zhc.analysis.base_analyzer import (
    StaticAnalyzer,
    AnalysisResult,
    Severity,
    get_node_location,
)
from zhc.analysis.ast_utils import (
    find_all_nodes,
    get_variable_name,
)


class NullPointerAnalyzer(StaticAnalyzer):
    """
    空指针检测器

    检测可能的空指针解引用和空值检查缺失。
    """

    @property
    def name(self) -> str:
        return "null_pointer"

    @property
    def description(self) -> str:
        return "检测可能的空指针解引用"

    @property
    def severity(self) -> Severity:
        return Severity.WARNING

    def analyze(self, ast: Any, context: Dict[str, Any]) -> List[AnalysisResult]:
        """
        执行空指针检测

        Args:
            ast: AST 节点
            context: 分析上下文

        Returns:
            检测结果列表
        """
        self.clear_results()

        # 收集所有指针赋值
        null_assignments: Set[str] = set()
        pointer_vars: Set[str] = set()

        # 简化实现：查找可能的空指针使用
        # 在实际实现中需要更复杂的数据流分析

        # 查找指针类型的变量声明
        for decl in find_all_nodes(ast, "VariableDecl"):
            if self._is_pointer_type(decl):
                var_name = get_variable_name(decl)
                if var_name:
                    pointer_vars.add(var_name)

        # 查找指针解引用
        for node in find_all_nodes(ast, None):
            if self._is_pointer_dereference(node):
                var_name = self._get_dereferenced_var(node)
                if var_name and var_name in null_assignments:
                    location = get_node_location(node)
                    if location:
                        self.add_result(
                            message=f"指针 '{var_name}' 可能为空",
                            location=location,
                            suggestion="在使用指针前检查是否为空",
                        )

        return self.results

    def _is_pointer_type(self, node: Any) -> bool:
        """检查是否是指针类型"""
        if hasattr(node, "type_node"):
            type_node = node.type_node
            if hasattr(type_node, "node_type"):
                return (
                    type_node.node_type.value == "PointerType"
                    if hasattr(type_node.node_type, "value")
                    else False
                )
            type_name = getattr(type_node, "name", "") or str(type_node)
            return "*" in type_name or "指针" in type_name
        return False

    def _is_pointer_dereference(self, node: Any) -> bool:
        """检查是否是解引用操作"""
        if hasattr(node, "node_type"):
            type_str = (
                str(node.node_type.value)
                if hasattr(node.node_type, "value")
                else str(node.node_type)
            )
            return "Member" in type_str or "Index" in type_str
        return False

    def _get_dereferenced_var(self, node: Any) -> Optional[str]:
        """获取解引用的变量名"""
        if hasattr(node, "expression"):
            expr = node.expression
            if hasattr(expr, "name"):
                return str(expr.name)
        return None


class DivisionByZeroAnalyzer(StaticAnalyzer):
    """
    除零检测器

    检测常量除零和可能的除零操作。
    """

    @property
    def name(self) -> str:
        return "division_by_zero"

    @property
    def description(self) -> str:
        return "检测除零错误"

    @property
    def severity(self) -> Severity:
        return Severity.ERROR

    def analyze(self, ast: Any, context: Dict[str, Any]) -> List[AnalysisResult]:
        """
        执行除零检测

        Args:
            ast: AST 节点
            context: 分析上下文

        Returns:
            检测结果列表
        """
        self.clear_results()

        # 查找除法操作
        for node in find_all_nodes(ast, None):
            if self._is_division(node):
                divisor = self._get_divisor(node)

                # 检查是否是常量零
                if divisor == 0:
                    location = get_node_location(node)
                    if location:
                        self.add_result(
                            message="检测到除以零",
                            location=location,
                            severity=Severity.ERROR,
                            suggestion="确保除数不为零",
                        )

        return self.results

    def _is_division(self, node: Any) -> bool:
        """检查是否是除法操作"""
        if hasattr(node, "operator"):
            op = str(node.operator)
            return op in ("/", "/=", "除以", "除等于")
        return False

    def _get_divisor(self, node: Any) -> Any:
        """获取除数"""
        if hasattr(node, "right"):
            right = node.right
            # 检查是否是字面量零
            if hasattr(right, "value"):
                try:
                    return int(right.value)
                except (ValueError, TypeError):
                    pass
        return None

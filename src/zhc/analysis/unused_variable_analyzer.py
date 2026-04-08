"""
未使用变量检测分析器

检测已定义但从未使用的变量。

Phase 4 - Stage 3 - Task 14.3
"""

from typing import List, Dict, Any, Set

from zhc.analysis.base_analyzer import (
    StaticAnalyzer,
    AnalysisResult,
    Severity,
    get_node_location,
)
from zhc.analysis.ast_utils import (
    find_variable_declarations,
    find_variable_references,
    get_variable_name,
)


class UnusedVariableAnalyzer(StaticAnalyzer):
    """
    未使用变量检测器

    检测局部变量定义后从未使用的情况。
    """

    @property
    def name(self) -> str:
        return "unused_variable"

    @property
    def description(self) -> str:
        return "检测已定义但从未使用的变量"

    @property
    def severity(self) -> Severity:
        return Severity.WARNING

    def analyze(self, ast: Any, context: Dict[str, Any]) -> List[AnalysisResult]:
        """
        执行未使用变量检测

        Args:
            ast: AST 节点
            context: 分析上下文

        Returns:
            检测结果列表
        """
        self.clear_results()

        # 收集所有变量定义
        defined_vars: Dict[str, Dict[str, Any]] = {}
        for decl in find_variable_declarations(ast):
            var_name = get_variable_name(decl)
            if var_name:
                location = get_node_location(decl)
                if location:
                    defined_vars[var_name] = {
                        "node": decl,
                        "location": location,
                        "scope": self._get_scope(decl),
                    }

        # 收集所有变量引用
        referenced_vars: Set[str] = set()
        for ref in find_variable_references(ast):
            var_name = get_variable_name(ref)
            if var_name:
                referenced_vars.add(var_name)

        # 检查未使用的变量
        for var_name, var_info in defined_vars.items():
            if var_name not in referenced_vars:
                # 排除参数（参数不使用不算警告）
                if self._is_parameter(var_info["node"]):
                    continue

                # 排除全局变量
                if self._is_global(var_info["node"]):
                    continue

                # 排除下划线开头的变量（通常是故意的）
                if var_name.startswith("_"):
                    continue

                self.add_result(
                    message=f"变量 '{var_name}' 已定义但从未使用",
                    location=var_info["location"],
                    suggestion=f"考虑删除未使用的变量 '{var_name}'，或使用它",
                )

        return self.results

    def _get_scope(self, node: Any) -> str:
        """获取变量所在作用域"""
        # 简单实现：检查是否有函数祖先
        scope = "global"
        parent = getattr(node, "parent", None)

        while parent:
            if getattr(parent, "node_type", None) == "FunctionDecl":
                scope = "local"
                break
            parent = getattr(parent, "parent", None)

        return scope

    def _is_parameter(self, node: Any) -> bool:
        """检查是否是函数参数"""
        parent = getattr(node, "parent", None)
        return parent is not None and getattr(parent, "node_type", None) == "ParamDecl"

    def _is_global(self, node: Any) -> bool:
        """检查是否是全局变量"""
        parent = getattr(node, "parent", None)

        while parent:
            if getattr(parent, "node_type", None) == "FunctionDecl":
                return False
            if getattr(parent, "node_type", None) == "Program":
                return True
            parent = getattr(parent, "parent", None)

        return False

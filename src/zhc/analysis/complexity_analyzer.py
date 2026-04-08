"""
代码复杂度分析器

分析代码的圈复杂度、嵌套深度等指标。

Phase 4 - Stage 3 - Task 14.3
"""

from typing import List, Dict, Any

from zhc.analysis.base_analyzer import (
    StaticAnalyzer,
    AnalysisResult,
    Severity,
    get_node_location,
)
from zhc.analysis.ast_utils import find_all_nodes, get_variable_name


class ComplexityAnalyzer(StaticAnalyzer):
    """
    代码复杂度分析器

    计算函数的圈复杂度（Cyclomatic Complexity）和嵌套深度。
    """

    # 复杂度阈值
    MAX_CYCLOMATIC = 10
    MAX_NESTING = 4
    MAX_FUNCTION_LINES = 50

    @property
    def name(self) -> str:
        return "complexity"

    @property
    def description(self) -> str:
        return "分析代码复杂度"

    @property
    def severity(self) -> Severity:
        return Severity.INFO

    def analyze(self, ast: Any, context: Dict[str, Any]) -> List[AnalysisResult]:
        """
        执行复杂度分析

        Args:
            ast: AST 节点
            context: 分析上下文

        Returns:
            分析结果列表
        """
        self.clear_results()

        # 分析每个函数的复杂度
        for func in find_all_nodes(ast, "FunctionDecl"):
            self._analyze_function(func)

        return self.results

    def _analyze_function(self, func: Any) -> None:
        """分析单个函数的复杂度"""
        func_name = get_variable_name(func) or "匿名函数"
        location = get_node_location(func)

        # 计算圈复杂度
        cyclomatic = self._calculate_cyclomatic(func)

        # 计算嵌套深度
        max_nesting = self._calculate_max_nesting(func)

        # 计算函数行数
        func_lines = self._calculate_lines(func)

        # 检查复杂度是否过高
        if cyclomatic > self.MAX_CYCLOMATIC:
            if location:
                self.add_result(
                    message=f"函数 '{func_name}' 圈复杂度过高 ({cyclomatic} > {self.MAX_CYCLOMATIC})",
                    location=location,
                    severity=Severity.WARNING,
                    suggestion="考虑将函数拆分为更小的函数",
                )

        # 检查嵌套深度
        if max_nesting > self.MAX_NESTING:
            if location:
                self.add_result(
                    message=f"函数 '{func_name}' 嵌套深度过深 ({max_nesting} > {self.MAX_NESTING})",
                    location=location,
                    severity=Severity.WARNING,
                    suggestion="考虑使用提前返回或提取方法来减少嵌套",
                )

        # 检查函数长度
        if func_lines > self.MAX_FUNCTION_LINES:
            if location:
                self.add_result(
                    message=f"函数 '{func_name}' 过长 ({func_lines} 行 > {self.MAX_FUNCTION_LINES} 行)",
                    location=location,
                    severity=Severity.INFO,
                    suggestion="考虑将函数拆分为更小的函数",
                )

    def _calculate_cyclomatic(self, func: Any) -> int:
        """
        计算圈复杂度

        圈复杂度 = 1 + if语句数 + 循环语句数 + case语句数 + and/or操作数
        """
        complexity = 1  # 基础复杂度

        # 统计控制流语句
        for node in find_all_nodes(func, None):
            node_type = getattr(node, "node_type", None)
            if node_type:
                type_str = str(getattr(node_type, "value", node_type))

                # if 语句
                if "If" in type_str:
                    complexity += 1

                # 循环语句
                elif any(x in type_str for x in ["While", "For", "DoWhile"]):
                    complexity += 1

                # case 语句
                elif "Case" in type_str:
                    complexity += 1

                # and/or 操作
                elif "Binary" in type_str:
                    op = getattr(node, "operator", "")
                    if op in ("and", "or", "&&", "||", "且", "或"):
                        complexity += 1

        return complexity

    def _calculate_max_nesting(self, func: Any) -> int:
        """计算最大嵌套深度"""
        max_depth = 0

        def visit(node: Any, depth: int) -> None:
            nonlocal max_depth

            if depth > max_depth:
                max_depth = depth

            node_type = getattr(node, "node_type", None)
            if node_type:
                type_str = str(getattr(node_type, "value", node_type))

                # 增加嵌套深度的语句
                if any(
                    x in type_str for x in ["If", "While", "For", "DoWhile", "Switch"]
                ):
                    depth += 1

            # 递归遍历子节点
            for attr_name in dir(node):
                if attr_name.startswith("_"):
                    continue

                try:
                    attr = getattr(node, attr_name)
                except (AttributeError, TypeError):
                    continue

                if isinstance(attr, list):
                    for child in attr:
                        visit(child, depth)
                elif hasattr(attr, "__dict__") and not isinstance(
                    attr, (str, int, float, bool, type(None))
                ):
                    visit(attr, depth)

        visit(func, 0)
        return max_depth

    def _calculate_lines(self, func: Any) -> int:
        """计算函数行数"""
        location = get_node_location(func)
        if location:
            end_line = location.end_line or location.line
            return end_line - location.line + 1
        return 0


class CodeSmellAnalyzer(StaticAnalyzer):
    """
    代码异味检测器

    检测常见的代码异味和反模式。
    """

    @property
    def name(self) -> str:
        return "code_smell"

    @property
    def description(self) -> str:
        return "检测代码异味"

    @property
    def severity(self) -> Severity:
        return Severity.INFO

    def analyze(self, ast: Any, context: Dict[str, Any]) -> List[AnalysisResult]:
        """
        执行代码异味检测

        Args:
            ast: AST 节点
            context: 分析上下文

        Returns:
            检测结果列表
        """
        self.clear_results()

        # 检测长参数列表
        self._check_long_parameter_list(ast)

        # 检测重复代码
        self._check_duplicate_code(ast)

        return self.results

    def _check_long_parameter_list(self, ast: Any) -> None:
        """检查长参数列表"""
        for func in find_all_nodes(ast, "FunctionDecl"):
            params = getattr(func, "params", [])
            if len(params) > 5:
                location = get_node_location(func)
                if location:
                    func_name = get_variable_name(func) or "匿名函数"
                    self.add_result(
                        message=f"函数 '{func_name}' 参数过多 ({len(params)} 个)",
                        location=location,
                        severity=Severity.INFO,
                        suggestion="考虑使用结构体或对象封装参数",
                    )

    def _check_duplicate_code(self, ast: Any) -> None:
        """检查重复代码"""
        # 简化实现：实际需要更复杂的重复检测算法
        pass


class DeadCodeAnalyzer(StaticAnalyzer):
    """
    死代码检测器

    检测永远不会执行的代码。
    """

    @property
    def name(self) -> str:
        return "dead_code"

    @property
    def description(self) -> str:
        return "检测死代码"

    @property
    def severity(self) -> Severity:
        return Severity.WARNING

    def analyze(self, ast: Any, context: Dict[str, Any]) -> List[AnalysisResult]:
        """
        执行死代码检测

        Args:
            ast: AST 节点
            context: 分析上下文

        Returns:
            检测结果列表
        """
        self.clear_results()

        # 检测 return 后的代码
        self._check_code_after_return(ast)

        # 检测不可达的分支
        self._check_unreachable_branches(ast)

        return self.results

    def _check_code_after_return(self, ast: Any) -> None:
        """检查 return 后的代码"""
        for block in find_all_nodes(ast, "Block"):
            statements = getattr(block, "statements", [])
            found_return = False

            for stmt in statements:
                if found_return:
                    location = get_node_location(stmt)
                    if location:
                        self.add_result(
                            message="检测到不可达代码（return 语句之后）",
                            location=location,
                            suggestion="删除 return 语句之后的代码",
                        )

                stmt_type = getattr(stmt, "node_type", None)
                if stmt_type and "Return" in str(
                    getattr(stmt_type, "value", stmt_type)
                ):
                    found_return = True

    def _check_unreachable_branches(self, ast: Any) -> None:
        """检查不可达分支"""
        # 简化实现：检查 if False 或 if True
        for if_node in find_all_nodes(ast, "If"):
            condition = getattr(if_node, "condition", None)
            if condition:
                # 检查是否是常量 false
                if hasattr(condition, "value"):
                    val = condition.value
                    if val is False or val == 0:
                        location = get_node_location(if_node)
                        if location:
                            self.add_result(
                                message="检测到不可达分支（条件永远为假）",
                                location=location,
                                suggestion="删除不可达的分支",
                            )

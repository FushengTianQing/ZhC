#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
控制流分析器 - AST 适配层 (Phase 6 M3)

将 AST 节点适配为 control_flow.py 需要的字典格式，
并提供 CFGAnalyzer 封装类和 UninitAnalyzer 未初始化变量检测器。

作者：阿福
日期：2026-04-03
"""

from typing import List, Set

from ..parser.ast_nodes import (
    ASTNode,
    ASTNodeType,
    FunctionDeclNode,
)


# ==================== AST → 字典适配 ====================


def ast_to_statements(node: ASTNode) -> List[dict]:
    """将 AST 节点列表转换为 control_flow.py 需要的字典格式

    Args:
        node: AST 节点（通常是 BlockStmtNode 或单个语句节点）

    Returns:
        字典列表，每个字典包含 type, line, column 等字段
    """
    if node is None:
        return []

    if node.node_type == ASTNodeType.BLOCK_STMT:
        return [ast_stmt_to_dict(stmt) for stmt in node.statements if stmt is not None]

    return [ast_stmt_to_dict(node)]


def ast_stmt_to_dict(node: ASTNode) -> dict:
    """将单个 AST 语句节点转换为字典

    字典格式与 analyzer/ 各分析器需要的输入兼容。
    增强版：尽可能保留完整的语义信息。
    """
    result = {
        "type": "expression",  # 默认类型
        "line": getattr(node, "line", 0),
        "column": getattr(node, "column", 0),
    }

    if node is None:
        return result

    nt = node.node_type

    if nt == ASTNodeType.IF_STMT:
        result["type"] = "if"
        result["then_body"] = (
            ast_to_statements(node.then_branch) if node.then_branch else []
        )
        result["else_body"] = (
            ast_to_statements(node.else_branch) if node.else_branch else []
        )
        # 提取条件表达式
        if hasattr(node, "condition") and node.condition:
            result["condition"] = _expr_to_str(node.condition)

    elif nt == ASTNodeType.WHILE_STMT:
        result["type"] = "while"
        result["body"] = ast_to_statements(node.body) if node.body else []
        if hasattr(node, "condition") and node.condition:
            result["condition"] = _expr_to_str(node.condition)

    elif nt == ASTNodeType.FOR_STMT:
        result["type"] = "for"
        result["body"] = ast_to_statements(node.body) if node.body else []
        if hasattr(node, "init") and node.init:
            result["init"] = ast_stmt_to_dict(node.init)
        if hasattr(node, "condition") and node.condition:
            result["condition"] = _expr_to_str(node.condition)
        if hasattr(node, "update") and node.update:
            result["update"] = ast_stmt_to_dict(node.update)

    elif nt == ASTNodeType.DO_WHILE_STMT:
        result["type"] = "do_while"
        result["body"] = ast_to_statements(node.body) if node.body else []
        if hasattr(node, "condition") and node.condition:
            result["condition"] = _expr_to_str(node.condition)

    elif nt == ASTNodeType.SWITCH_STMT:
        result["type"] = "switch"
        cases = []
        if node.cases:
            for case in node.cases:
                cases.append(ast_stmt_to_dict(case))
        result["cases"] = cases
        if hasattr(node, "expr") and node.expr:
            result["expr"] = _expr_to_str(node.expr)

    elif nt == ASTNodeType.CASE_STMT:
        result["type"] = "case"
        if hasattr(node, "value") and node.value:
            result["value"] = _expr_to_str(node.value)

    elif nt == ASTNodeType.DEFAULT_STMT:
        result["type"] = "default"

    elif nt == ASTNodeType.RETURN_STMT:
        result["type"] = "return"
        if hasattr(node, "value") and node.value:
            result["value"] = _expr_to_str(node.value)

    elif nt == ASTNodeType.BREAK_STMT:
        result["type"] = "break"

    elif nt == ASTNodeType.CONTINUE_STMT:
        result["type"] = "continue"

    elif nt == ASTNodeType.GOTO_STMT:
        result["type"] = "goto"
        result["label"] = getattr(node, "label", "")

    elif nt == ASTNodeType.LABEL_STMT:
        result["type"] = "label"
        result["name"] = getattr(node, "name", "")

    elif nt == ASTNodeType.VARIABLE_DECL:
        result["type"] = "var_decl"
        result["name"] = getattr(node, "name", "")
        result["has_init"] = node.init is not None
        if node.init:
            result["value"] = _expr_to_str(node.init)
        # 类型信息（供指针分析、别名分析使用）
        if hasattr(node, "var_type") and node.var_type:
            result["data_type"] = _type_to_str(node.var_type)
        # 数组大小
        if hasattr(node, "array_size") and node.array_size:
            result["size"] = node.array_size
        elif hasattr(node, "var_type") and node.var_type:
            # 尝试从类型名提取数组大小
            import re

            type_str = _type_to_str(node.var_type)
            arr_match = re.search(r"\[(\d+)\]", type_str)
            if arr_match:
                result["size"] = int(arr_match.group(1))

    elif nt == ASTNodeType.EXPR_STMT:
        expr = getattr(node, "expr", None)
        if expr:
            expr_type = expr.node_type
            # 赋值表达式
            if expr_type == ASTNodeType.ASSIGN_EXPR:
                result["type"] = "assign"
                if hasattr(expr, "target") and expr.target:
                    result["target"] = _expr_to_str(expr.target)
                    result["name"] = _expr_name(expr.target)
                if hasattr(expr, "value") and expr.value:
                    result["value"] = _expr_to_str(expr.value)
            # 函数调用表达式
            elif expr_type == ASTNodeType.CALL_EXPR:
                result["type"] = "call"
                if hasattr(expr, "callee") and expr.callee:
                    result["function"] = getattr(expr.callee, "name", "")
                if hasattr(expr, "args") and expr.args:
                    result["args"] = [_expr_to_str(arg) for arg in expr.args]
                # 推导返回值接收变量（通过推断类型检查）
                result["result"] = ""
            # 解引用表达式
            elif expr_type == ASTNodeType.UNARY_EXPR:
                op = getattr(expr, "operator", "") or getattr(expr, "op", "")
                if op == "*" and hasattr(expr, "operand") and expr.operand:
                    result["type"] = "dereference"
                    result["name"] = _expr_name(expr.operand)
                    result["value"] = _expr_to_str(expr)
            else:
                result["type"] = "expression"

    return result


def _expr_to_str(node: ASTNode) -> str:
    """将表达式 AST 节点转换为字符串表示"""
    if node is None:
        return ""
    nt = node.node_type

    if nt == ASTNodeType.IDENTIFIER_EXPR:
        return getattr(node, "name", "")
    elif nt == ASTNodeType.INT_LITERAL:
        return str(getattr(node, "value", "0"))
    elif nt == ASTNodeType.FLOAT_LITERAL:
        return str(getattr(node, "value", "0.0"))
    elif nt == ASTNodeType.STRING_LITERAL:
        return f'"{getattr(node, "value", "")}"'
    elif nt == ASTNodeType.CHAR_LITERAL:
        return f"'{getattr(node, 'value', '')}'"
    elif nt == ASTNodeType.NULL_LITERAL:
        return "空指针"
    elif nt == ASTNodeType.BOOL_LITERAL:
        return str(getattr(node, "value", ""))
    elif nt == ASTNodeType.BINARY_EXPR:
        left = _expr_to_str(node.left) if hasattr(node, "left") else ""
        right = _expr_to_str(node.right) if hasattr(node, "right") else ""
        op = getattr(node, "operator", "") or getattr(node, "op", "")
        return f"{left} {op} {right}"
    elif nt == ASTNodeType.UNARY_EXPR:
        operand = _expr_to_str(node.operand) if hasattr(node, "operand") else ""
        op = getattr(node, "operator", "") or getattr(node, "op", "")
        return f"{op}{operand}"
    elif nt == ASTNodeType.CALL_EXPR:
        callee = ""
        if hasattr(node, "callee") and node.callee:
            callee = getattr(node.callee, "name", "")
        args = ""
        if hasattr(node, "args") and node.args:
            args = ", ".join(_expr_to_str(a) for a in node.args)
        return f"{callee}({args})"
    elif nt == ASTNodeType.MEMBER_EXPR:
        obj = _expr_to_str(node.obj) if hasattr(node, "obj") else ""
        member = getattr(node, "member", "")
        return f"{obj}.{member}"
    elif nt == ASTNodeType.ARRAY_EXPR:
        obj = _expr_to_str(
            getattr(node, "array", None) or getattr(node, "object", None)
        )
        index = _expr_to_str(node.index) if hasattr(node, "index") else ""
        return f"{obj}[{index}]"
    elif nt == ASTNodeType.ASSIGN_EXPR:
        target = _expr_to_str(node.target) if hasattr(node, "target") else ""
        value = _expr_to_str(node.value) if hasattr(node, "value") else ""
        return f"{target} = {value}"
    elif nt == ASTNodeType.SIZEOF_EXPR:
        return f"sizeof({getattr(node, 'target', '')})"
    elif nt == ASTNodeType.CAST_EXPR:
        target_type = (
            _type_to_str(node.target_type) if hasattr(node, "target_type") else ""
        )
        operand = _expr_to_str(node.operand) if hasattr(node, "operand") else ""
        return f"({target_type}){operand}"
    elif nt == ASTNodeType.TERNARY_EXPR:
        cond = _expr_to_str(node.condition) if hasattr(node, "condition") else ""
        then = _expr_to_str(node.then_expr) if hasattr(node, "then_expr") else ""
        else_ = _expr_to_str(node.else_expr) if hasattr(node, "else_expr") else ""
        return f"{cond} ? {then} : {else_}"
    else:
        return str(getattr(node, "value", "")) if hasattr(node, "value") else ""


def _expr_name(node: ASTNode) -> str:
    """从表达式节点提取变量名"""
    if node is None:
        return ""
    nt = node.node_type
    if nt == ASTNodeType.IDENTIFIER_EXPR:
        return getattr(node, "name", "")
    if nt == ASTNodeType.MEMBER_EXPR:
        obj = _expr_name(node.obj) if hasattr(node, "obj") else ""
        return f"{obj}.{getattr(node, 'member', '')}"
    if nt == ASTNodeType.UNARY_EXPR:
        return _expr_name(node.operand) if hasattr(node, "operand") else ""
    return ""


def _type_to_str(type_node) -> str:
    """从类型 AST 节点获取字符串表示"""
    if type_node is None:
        return ""
    if hasattr(type_node, "name"):
        return type_node.name
    return str(type_node)


# ==================== 函数查找 ====================


def find_functions(ast: ASTNode) -> List[FunctionDeclNode]:
    """从 AST 中提取所有函数声明节点"""
    functions = []

    if ast.node_type == ASTNodeType.PROGRAM:
        for decl in ast.declarations:
            if decl and decl.node_type == ASTNodeType.FUNCTION_DECL:
                functions.append(decl)
    elif ast.node_type == ASTNodeType.FUNCTION_DECL:
        functions.append(ast)

    return functions


# ==================== CFGAnalyzer ====================


class CFGAnalyzer:
    """控制流分析器封装

    将 AST 通过适配层传递给 analyzer/control_flow.py 的 ControlFlowAnalyzerCached（Phase 7 升级），
    检测不可达代码。所有公开方法（detect_unreachable_code_cached 等）缓存自动生效。
    """

    def __init__(self):
        self._analyzer = None

    def _get_analyzer(self):
        """延迟导入避免循环依赖（Phase 7: 升级为 ControlFlowAnalyzerCached）"""
        if self._analyzer is None:
            from ..analyzer.control_flow_cached import ControlFlowAnalyzerCached

            self._analyzer = ControlFlowAnalyzerCached()
        return self._analyzer

    def detect_unreachable(self, ast: ASTNode) -> List[dict]:
        """检测 AST 中的不可达代码

        Args:
            ast: 完整的 AST 树（通常是 ProgramNode）

        Returns:
            问题列表，每个字典包含:
            - issue_type: str
            - message: str
            - line_number: int
            - severity: str
            - suggestion: str
            - func_name: str（所在函数名）
        """
        analyzer = self._get_analyzer()
        issues = []

        for func_decl in find_functions(ast):
            if not func_decl.body:
                continue

            stmt_dicts = ast_to_statements(func_decl.body)

            try:
                cfg = analyzer.build_cfg(func_decl.name, stmt_dicts)
                func_issues = analyzer.detect_unreachable_code(cfg)

                for issue in func_issues:
                    issues.append(
                        {
                            "issue_type": issue.issue_type,
                            "message": issue.message,
                            "line_number": issue.line_number,
                            "severity": issue.severity,
                            "suggestion": issue.suggestion,
                            "func_name": func_decl.name,
                        }
                    )
            except Exception:
                # CFG 构建失败时静默跳过，不阻断编译
                pass

        return issues


# ==================== UninitAnalyzer ====================


class UninitAnalyzer:
    """未初始化变量使用检测器（轻量级前向扫描）

    实现策略：
    - 在每个函数体内进行简单的前向扫描
    - 跟踪变量声明和使用
    - 不做复杂的路径分析（Phase 7 的数据流分析会完善）

    豁免规则：
    - 全局变量（自动零初始化）
    - 指针变量（不跟踪）
    - 结构体变量（不跟踪）
    - 函数参数（由调用者提供）
    - 条件分支中初始化的变量（不报告，避免高误报率）
    """

    def __init__(self):
        self.uninitialized_uses: List[dict] = []

    def analyze(self, ast: ASTNode, symbol_table) -> List[dict]:
        """遍历 AST，检测未初始化变量使用

        Args:
            ast: 完整的 AST 树
            symbol_table: SemanticAnalyzer 的 SymbolTable 实例（用于区分全局/局部变量）

        Returns:
            问题列表，每个字典包含:
            - name: str（变量名）
            - line: int
            - column: int
            - func_name: str（所在函数名）
        """
        self.uninitialized_uses = []

        for func_decl in find_functions(ast):
            if not func_decl.body:
                continue

            # 收集此函数的参数名（参数视为已初始化）
            param_names = set()
            for param in func_decl.params:
                if hasattr(param, "name"):
                    param_names.add(param.name)

            # 扫描函数体
            self._scan_block(func_decl.body, param_names, func_decl.name, symbol_table)

        return self.uninitialized_uses

    def _scan_block(
        self, node: ASTNode, initialized: Set[str], func_name: str, symbol_table
    ) -> None:
        """扫描代码块，跟踪变量初始化状态"""
        if node is None:
            return

        if node.node_type == ASTNodeType.BLOCK_STMT:
            for stmt in node.statements:
                self._scan_statement(stmt, initialized, func_name, symbol_table)
        else:
            self._scan_statement(node, initialized, func_name, symbol_table)

    def _scan_statement(
        self, node: ASTNode, initialized: Set[str], func_name: str, symbol_table
    ) -> bool:
        """扫描单个语句

        Returns:
            True 如果此语句之后不可达（如 return/break/continue）
        """
        if node is None:
            return False

        nt = node.node_type

        if nt == ASTNodeType.VARIABLE_DECL:
            # 变量声明：如果有初始化表达式则标记为已初始化
            name = getattr(node, "name", "")
            if node.init is not None:
                initialized.add(name)
            elif name:
                # 未初始化的局部变量
                # 检查是否是全局变量（通过 symbol_table）
                is_global = self._is_global_variable(name, symbol_table)
                if not is_global:
                    initialized.discard(name)  # 显式标记为未初始化

            # 递归分析初始化表达式
            if node.init:
                self._scan_expr(node.init, initialized, func_name, symbol_table)
            return False

        elif nt == ASTNodeType.EXPR_STMT:
            if hasattr(node, "expr") and node.expr:
                self._scan_expr(node.expr, initialized, func_name, symbol_table)
            return False

        elif nt == ASTNodeType.RETURN_STMT:
            if hasattr(node, "value") and node.value:
                self._scan_expr(node.value, initialized, func_name, symbol_table)
            return True  # return 后不可达

        elif nt == ASTNodeType.BREAK_STMT or nt == ASTNodeType.CONTINUE_STMT:
            return True  # break/continue 后不可达

        elif nt == ASTNodeType.IF_STMT:
            # if 语句：两个分支各自继承当前初始化集合
            # 扫描后取并集（任一分支初始化即视为已初始化）
            if node.condition:
                self._scan_expr(node.condition, initialized, func_name, symbol_table)

            then_unreachable = False
            else_unreachable = False

            # 记录扫描前的初始化集合
            saved_initialized = set(initialized)

            if node.then_branch:
                then_unreachable = self._scan_block(
                    node.then_branch, initialized, func_name, symbol_table
                )
                then_initialized = set(initialized)

            # else 分支：从原始集合开始
            if node.else_branch:
                initialized.clear()
                initialized.update(saved_initialized)
                else_unreachable = self._scan_block(
                    node.else_branch, initialized, func_name, symbol_table
                )
                else_initialized = set(initialized)

                # 合并：取两个分支的并集
                initialized.clear()
                initialized.update(then_initialized | else_initialized)
            elif then_unreachable:
                # 没有 else 且 then 不可达：保持原始集合
                pass
            else:
                # 没有 else 且 then 可达：不确定是否初始化（不报告使用）
                initialized.clear()
                initialized.update(then_initialized)

            # 两个分支都不可达 → 之后不可达
            return then_unreachable and else_unreachable

        elif nt in (ASTNodeType.WHILE_STMT, ASTNodeType.DO_WHILE_STMT):
            if nt == ASTNodeType.WHILE_STMT and node.condition:
                self._scan_expr(node.condition, initialized, func_name, symbol_table)
            if node.body:
                self._scan_block(node.body, initialized, func_name, symbol_table)
            if nt == ASTNodeType.DO_WHILE_STMT and node.condition:
                self._scan_expr(node.condition, initialized, func_name, symbol_table)
            return False  # 循环后仍可达

        elif nt == ASTNodeType.FOR_STMT:
            if node.init:
                self._scan_statement(node.init, initialized, func_name, symbol_table)
            if node.condition:
                self._scan_expr(node.condition, initialized, func_name, symbol_table)
            if node.body:
                self._scan_block(node.body, initialized, func_name, symbol_table)
            if node.update:
                self._scan_expr(node.update, initialized, func_name, symbol_table)
            return False

        elif nt == ASTNodeType.SWITCH_STMT:
            if node.expr:
                self._scan_expr(node.expr, initialized, func_name, symbol_table)
            if node.cases:
                for case in node.cases:
                    # case 内部可能包含 break，但整体 switch 后仍可达
                    self._scan_statement(case, initialized, func_name, symbol_table)
            return False

        elif nt == ASTNodeType.CASE_STMT:
            if hasattr(node, "value") and node.value:
                self._scan_expr(node.value, initialized, func_name, symbol_table)
            if hasattr(node, "body") and node.body:
                for stmt in node.body:
                    self._scan_statement(stmt, initialized, func_name, symbol_table)
            return False

        elif nt == ASTNodeType.DEFAULT_STMT:
            if hasattr(node, "body") and node.body:
                for stmt in node.body:
                    self._scan_statement(stmt, initialized, func_name, symbol_table)
            return False

        elif nt == ASTNodeType.LABEL_STMT:
            # 标签后的语句
            if hasattr(node, "stmt") and node.stmt:
                return self._scan_statement(
                    node.stmt, initialized, func_name, symbol_table
                )
            return False

        elif nt == ASTNodeType.GOTO_STMT:
            return False  # goto 不影响不可达性分析

        elif nt == ASTNodeType.BLOCK_STMT:
            return self._scan_block(node, initialized, func_name, symbol_table)

        return False

    def _scan_expr(
        self, node: ASTNode, initialized: Set[str], func_name: str, symbol_table
    ) -> None:
        """扫描表达式，检测未初始化变量使用"""
        if node is None:
            return

        nt = node.node_type

        if nt == ASTNodeType.IDENTIFIER_EXPR:
            name = getattr(node, "name", "")
            if name and name not in initialized:
                # 可能未初始化的变量使用
                is_global = self._is_global_variable(name, symbol_table)
                if not is_global:
                    # 排除函数名（不是变量）
                    # 简单启发式：不报告很短的名称如单字母（可能是循环变量、宏等误报）
                    # 只报告看起来像实际变量的名称
                    self.uninitialized_uses.append(
                        {
                            "name": name,
                            "line": getattr(node, "line", 0),
                            "column": getattr(node, "column", 0),
                            "func_name": func_name,
                        }
                    )

        elif nt == ASTNodeType.ASSIGN_EXPR:
            # 赋值表达式：左侧视为已初始化
            if hasattr(node, "target") and node.target:
                if node.target.node_type == ASTNodeType.IDENTIFIER_EXPR:
                    initialized.add(node.target.name)
                else:
                    self._scan_expr(node.target, initialized, func_name, symbol_table)
            if hasattr(node, "value") and node.value:
                self._scan_expr(node.value, initialized, func_name, symbol_table)

        elif nt == ASTNodeType.BINARY_EXPR:
            if hasattr(node, "left") and node.left:
                self._scan_expr(node.left, initialized, func_name, symbol_table)
            if hasattr(node, "right") and node.right:
                self._scan_expr(node.right, initialized, func_name, symbol_table)

        elif nt == ASTNodeType.UNARY_EXPR:
            if hasattr(node, "operand") and node.operand:
                self._scan_expr(node.operand, initialized, func_name, symbol_table)

        elif nt == ASTNodeType.CALL_EXPR:
            # 函数调用：只分析参数，不检查函数名（callee不是变量）
            if hasattr(node, "args") and node.args:
                for arg in node.args:
                    self._scan_expr(arg, initialized, func_name, symbol_table)

        elif nt == ASTNodeType.ARRAY_EXPR:
            for child in node.get_children():
                self._scan_expr(child, initialized, func_name, symbol_table)

        elif nt == ASTNodeType.MEMBER_EXPR:
            for child in node.get_children():
                self._scan_expr(child, initialized, func_name, symbol_table)

        elif nt in (
            ASTNodeType.TERNARY_EXPR,
            ASTNodeType.CAST_EXPR,
            ASTNodeType.SIZEOF_EXPR,
        ):
            for child in node.get_children():
                self._scan_expr(child, initialized, func_name, symbol_table)

    def _is_global_variable(self, name: str, symbol_table) -> bool:
        """检查变量是否是全局变量（全局变量自动零初始化，不报告未初始化）"""
        if symbol_table is None:
            return False

        # 查找全局作用域中的符号
        global_scope = symbol_table.global_scope
        if name in global_scope.symbols:
            sym = global_scope.symbols[name]
            if sym.scope_type.value == "全局":
                return True
        return False

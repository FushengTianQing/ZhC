# -*- coding: utf-8 -*-
"""
Upvalue 分析器 - Upvalue Analyzer

负责分析闭包/lambda 表达式捕获的变量：
1. 分析表达式中的变量引用
2. 确定变量的捕获模式
3. 构建闭包环境

Phase 5 - 函数式-闭包支持

作者：ZHC 开发团队
日期：2026-04-10
"""

from typing import Set, List, Dict, Optional, Any
from dataclasses import dataclass, field

from .closure import (
    CaptureMode,
    Upvalue,
    ClosureType,
    ClosureContext,
)


@dataclass
class ScopeInfo:
    """作用域信息

    Attributes:
        variables: 作用域中的变量集合
        parent: 父作用域
        depth: 作用域深度
    """

    variables: Set[str] = field(default_factory=set)
    parent: Optional["ScopeInfo"] = None
    depth: int = 0


class UpvalueAnalyzer:
    """Upvalue 分析器

    分析 lambda/闭包表达式中捕获的外部变量，确定：
    1. 哪些外部变量被捕获
    2. 捕获模式（引用/值/常量引用）
    3. 是否可修改

     Attributes:
        captured_vars: 被捕获的变量集合
        local_vars: 局部变量集合
        modified_vars: 在 lambda 中被修改的变量集合
        assigned_vars: 被赋值的变量集合
    """

    def __init__(self):
        """初始化分析器"""
        self.captured_vars: Set[str] = set()
        self.local_vars: Set[str] = set()
        self.modified_vars: Set[str] = set()
        self.assigned_vars: Set[str] = set()

    def analyze(
        self,
        lambda_body: Any,
        outer_scope_vars: Set[str],
        outer_scope: Optional[ScopeInfo] = None,
    ) -> List[Upvalue]:
        """分析 lambda 表达式捕获的变量

        Args:
            lambda_body: lambda 表达式体（AST 节点）
            outer_scope_vars: 外层作用域的变量集合
            outer_scope: 外层作用域信息（可选）

        Returns:
            Upvalue 列表
        """
        # 重置状态
        self.captured_vars = set()
        self.local_vars = set()
        self.modified_vars = set()
        self.assigned_vars = set()

        # 分析 lambda 体
        self._analyze_expression(lambda_body)

        # 构建 upvalue 列表
        upvalues = []
        for var in self.captured_vars:
            if var in outer_scope_vars and var not in self.local_vars:
                mode = self._determine_capture_mode(var)
                upvalue = Upvalue(
                    name=var,
                    type_name=self._get_var_type(var, outer_scope),
                    mode=mode,
                    index=len(upvalues),
                    is_mutable=(mode == CaptureMode.REFERENCE),
                )
                upvalues.append(upvalue)

        return upvalues

    def _analyze_expression(self, expr: Any):
        """递归分析表达式中的变量引用和赋值

        Args:
            expr: AST 表达式节点
        """
        if expr is None:
            return

        # 获取节点类型名
        node_type = type(expr).__name__

        # 标识符表达式
        if node_type in ("IdentifierExpr", "IdentifierExprNode", "Identifier"):
            name = getattr(expr, "name", None) or getattr(expr, "value", None)
            if name and name not in self.local_vars:
                self.captured_vars.add(name)

        # 赋值表达式
        elif node_type in ("Assignment", "AssignExpr", "AssignExprNode"):
            target = getattr(expr, "target", None)
            if target:
                target_name = getattr(target, "name", None) or getattr(target, "value", None)
                if target_name:
                    self.assigned_vars.add(target_name)
                    # 如果目标不在局部变量中但在外层，需要捕获
                    self.captured_vars.add(target_name)

            value = getattr(expr, "value", None) or getattr(expr, "expression", None)
            if value:
                self._analyze_expression(value)

        # 复合赋值 (+=, -=, etc.)
        elif node_type in ("CompoundAssignment", "CompoundAssignExpr"):
            target = getattr(expr, "target", None)
            if target:
                target_name = getattr(target, "name", None) or getattr(target, "value", None)
                if target_name:
                    self.modified_vars.add(target_name)
                    self.captured_vars.add(target_name)

            value = getattr(expr, "value", None)
            if value:
                self._analyze_expression(value)

        # 增量和减量 (++, --)
        elif node_type in ("IncrementExpr", "DecrementExpr", "UpdateExpr"):
            operand = getattr(expr, "operand", None) or getattr(expr, "expression", None)
            if operand:
                name = getattr(operand, "name", None) or getattr(operand, "value", None)
                if name:
                    self.modified_vars.add(name)
                    self.captured_vars.add(name)

        # 二元表达式
        elif node_type in ("BinaryExpr", "BinaryExprNode", "BinaryOp"):
            left = getattr(expr, "left", None)
            right = getattr(expr, "right", None)
            if left:
                self._analyze_expression(left)
            if right:
                self._analyze_expression(right)

        # 一元表达式
        elif node_type in ("UnaryExpr", "UnaryOp"):
            operand = getattr(expr, "operand", None) or getattr(expr, "expression", None)
            if operand:
                self._analyze_expression(operand)

        # 函数调用
        elif node_type in ("CallExpr", "FunctionCall"):
            # 分析函数表达式
            func = getattr(expr, "function", None)
            if func:
                self._analyze_expression(func)

            # 分析参数
            args = getattr(expr, "arguments", []) or getattr(expr, "args", [])
            for arg in args:
                self._analyze_expression(arg)

        # 成员访问
        elif node_type in ("MemberExpr", "MemberAccess"):
            obj = getattr(expr, "object", None) or getattr(expr, "expr", None)
            if obj:
                self._analyze_expression(obj)

        # 数组访问
        elif node_type in ("ArrayExpr", "ArrayAccess"):
            arr = getattr(expr, "array", None) or getattr(expr, "expr", None)
            if arr:
                self._analyze_expression(arr)

            index = getattr(expr, "index", None)
            if index:
                self._analyze_expression(index)

        # 三元表达式
        elif node_type == "TernaryExpr":
            cond = getattr(expr, "condition", None) or getattr(expr, "test", None)
            true_expr = getattr(expr, "true_expr", None) or getattr(expr, "consequent", None)
            false_expr = getattr(expr, "false_expr", None) or getattr(expr, "alternate", None)

            if cond:
                self._analyze_expression(cond)
            if true_expr:
                self._analyze_expression(true_expr)
            if false_expr:
                self._analyze_expression(false_expr)

        # Lambda 表达式（嵌套）
        elif node_type in ("LambdaExpr", "Lambda"):
            # 嵌套 lambda 有自己的作用域
            params = getattr(expr, "params", []) or []
            nested_local = set()
            for param in params:
                param_name = getattr(param, "name", None)
                if param_name:
                    nested_local.add(param_name)
                    self.local_vars.add(param_name)

            body = getattr(expr, "body", None)
            if body:
                self._analyze_expression(body)

            # 移除嵌套的局部变量
            for var in nested_local:
                self.local_vars.discard(var)

        # 代码块
        elif node_type in ("BlockStmt", "Block", "BlockStatement"):
            stmts = getattr(expr, "statements", []) or getattr(expr, "body", [])
            for stmt in stmts:
                self._analyze_statement(stmt)

        # 变量声明
        elif node_type in ("VariableDecl", "VarDecl"):
            var_name = getattr(expr, "name", None)
            if var_name:
                self.local_vars.add(var_name)

            init = getattr(expr, "initial_value", None) or getattr(expr, "init", None)
            if init:
                self._analyze_expression(init)

        # 返回语句
        elif node_type in ("ReturnStmt", "Return"):
            value = getattr(expr, "value", None) or getattr(expr, "expression", None)
            if value:
                self._analyze_expression(value)

        # 如果语句
        elif node_type in ("IfStmt", "If"):
            cond = getattr(expr, "condition", None)
            then_stmt = getattr(expr, "then_stmt", None) or getattr(expr, "consequent", None)
            else_stmt = getattr(expr, "else_stmt", None) or getattr(expr, "alternate", None)

            if cond:
                self._analyze_expression(cond)
            if then_stmt:
                self._analyze_statement(then_stmt)
            if else_stmt:
                self._analyze_statement(else_stmt)

        # 当循环
        elif node_type in ("WhileStmt", "While"):
            cond = getattr(expr, "condition", None)
            body = getattr(expr, "body", None)

            if cond:
                self._analyze_expression(cond)
            if body:
                self._analyze_statement(body)

        # 循环语句
        elif node_type in ("ForStmt", "For"):
            init = getattr(expr, "init", None)
            cond = getattr(expr, "condition", None)
            update = getattr(expr, "update", None)
            body = getattr(expr, "body", None)

            if init:
                self._analyze_expression(init)
            if cond:
                self._analyze_expression(cond)
            if update:
                self._analyze_expression(update)
            if body:
                self._analyze_statement(body)

        # 字面量 - 不需要处理
        elif node_type in (
            "IntLiteral",
            "FloatLiteral",
            "StringLiteral",
            "CharLiteral",
            "BoolLiteral",
            "NullLiteral",
        ):
            pass

        # 列表表达式
        elif node_type == "ListExpr":
            items = getattr(expr, "items", []) or []
            for item in items:
                self._analyze_expression(item)

    def _analyze_statement(self, stmt: Any):
        """分析语句

        Args:
            stmt: AST 语句节点
        """
        if stmt is None:
            return

        node_type = type(stmt).__name__

        if node_type in ("BreakStmt", "Break"):
            pass

        elif node_type in ("ContinueStmt", "Continue"):
            pass

        elif node_type in ("ExprStmt", "ExprStatement"):
            expr = getattr(stmt, "expression", None)
            if expr:
                self._analyze_expression(expr)

        elif node_type == "Block":
            stmts = getattr(stmt, "statements", []) or getattr(stmt, "body", [])
            for s in stmts:
                self._analyze_statement(s)

        else:
            # 默认尝试作为表达式分析
            self._analyze_expression(stmt)

    def _determine_capture_mode(self, var_name: str) -> CaptureMode:
        """确定变量的捕获模式

        Args:
            var_name: 变量名

        Returns:
            捕获模式
        """
        # 如果变量在 lambda 中被修改，使用引用捕获
        if var_name in self.modified_vars or var_name in self.assigned_vars:
            return CaptureMode.REFERENCE

        # 否则使用值捕获
        return CaptureMode.VALUE

    def _get_var_type(
        self, var_name: str, outer_scope: Optional[ScopeInfo] = None
    ) -> str:
        """获取变量的类型

        Args:
            var_name: 变量名
            outer_scope: 外层作用域信息

        Returns:
            类型名，默认为 "整数型"
        """
        # 在实际实现中，这里应该从符号表获取类型
        # 目前返回默认值
        return "整数型"

    def get_captured_vars(self) -> Set[str]:
        """获取被捕获的变量集合

        Returns:
            被捕获的变量名集合
        """
        return self.captured_vars

    def get_local_vars(self) -> Set[str]:
        """获取局部变量集合

        Returns:
            局部变量名集合
        """
        return self.local_vars

    def get_modified_vars(self) -> Set[str]:
        """获取在 lambda 中被修改的变量集合

        Returns:
            被修改的变量名集合
        """
        return self.modified_vars


# ===== 测试代码 =====

if __name__ == "__main__":
    print("=" * 70)
    print("Upvalue 分析器测试")
    print("=" * 70)

    # 创建简单的测试 AST 节点
    class MockIdentifier:
        def __init__(self, name):
            self.name = name

    class MockBinaryExpr:
        def __init__(self, left, right):
            self.left = left
            self.right = right

    class MockAssignment:
        def __init__(self, target, value):
            self.target = target
            self.value = value

    # 测试 1: 基本变量捕获
    print("\n测试 1: 基本变量捕获")
    analyzer = UpvalueAnalyzer()
    outer_vars = {"count", "name", "外部变量"}

    # count + 1
    expr = MockBinaryExpr(MockIdentifier("count"), MockIdentifier("1"))
    upvalues = analyzer.analyze(expr, outer_vars)

    print(f"  表达式: count + 1")
    print(f"  捕获的变量: {analyzer.get_captured_vars()}")
    print(f"  Upvalues: {upvalues}")

    # 测试 2: 捕获并修改
    print("\n测试 2: 捕获并修改")
    analyzer2 = UpvalueAnalyzer()

    # count = count + 1
    expr2 = MockAssignment(
        MockIdentifier("count"),
        MockBinaryExpr(MockIdentifier("count"), MockIdentifier("1")),
    )
    upvalues2 = analyzer2.analyze(expr2, outer_vars)

    print(f"  表达式: count = count + 1")
    print(f"  捕获的变量: {analyzer2.get_captured_vars()}")
    print(f"  修改的变量: {analyzer2.get_modified_vars()}")
    print(f"  Upvalues: {upvalues2}")

    for uv in upvalues2:
        print(f"    - {uv.name}: mode={uv.mode.value}, mutable={uv.is_mutable}")

    print("\n" + "=" * 70)
    print("所有测试完成")
    print("=" * 70)

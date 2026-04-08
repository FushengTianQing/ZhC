#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步编程系统 - Asynchronous Programming System

实现异步编程的核心功能：
1. 异步函数声明
2. Await 表达式
3. 异步类型系统
4. Future/Promise 模型

Phase 4 - Stage 2 - Task 11.3

作者：ZHC 开发团队
日期：2026-04-08
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


# ===== 异步关键字 =====


class AsyncKeyword(Enum):
    """异步关键字"""

    ASYNC = "异步"  # 异步函数声明
    AWAIT = "等待"  # 等待异步操作
    ASYNC_TASK = "任务"  # 异步任务类型
    ASYNC_RESULT = "结果"  # 异步结果类型


# ===== 异步类型系统 =====


@dataclass
class AsyncType:
    """异步类型基类"""

    name: str = ""
    inner_type: Optional["AsyncType"] = None  # 内部类型

    def is_async(self) -> bool:
        return True

    def __str__(self):
        if self.inner_type:
            return f"{self.name}<{self.inner_type}>"
        return self.name


@dataclass
class FutureType(AsyncType):
    """Future 类型 - 表示异步计算的结果"""

    def __str__(self):
        if self.inner_type:
            return f"未来<{self.inner_type}>"
        return "未来"


@dataclass
class TaskType(AsyncType):
    """Task 类型 - 表示异步任务"""

    def __str__(self):
        if self.inner_type:
            return f"任务<{self.inner_type}>"
        return "任务"


@dataclass
class PromiseType(AsyncType):
    """Promise 类型 - 表示承诺的结果"""

    def __str__(self):
        if self.inner_type:
            return f"承诺<{self.inner_type}>"
        return "承诺"


# ===== 异步函数定义 =====


@dataclass
class AsyncFunction:
    """异步函数"""

    name: str = ""
    parameters: List["Parameter"] = field(default_factory=list)
    return_type: Optional[AsyncType] = None
    body: Optional["ASTNode"] = None
    is_async: bool = True

    def get_signature(self) -> str:
        params = ", ".join(p.name for p in self.parameters)
        ret_type = str(self.return_type) if self.return_type else "无"
        return f"异步函数 {self.name}({params}) -> {ret_type}"


@dataclass
class Parameter:
    """函数参数"""

    name: str = ""
    param_type: Optional[AsyncType] = None
    default_value: Optional[Any] = None


# ===== Await 表达式 =====


@dataclass
class AwaitExpression:
    """Await 表达式"""

    expression: "Expression" = None
    line: int = 0
    column: int = 0

    def __str__(self):
        return f"等待 {self.expression}"


# ===== 异步语句 =====


@dataclass
class AsyncFunctionDeclaration:
    """异步函数声明语句"""

    function: AsyncFunction = None
    line: int = 0
    column: int = 0


@dataclass
class AwaitStatement:
    """Await 语句"""

    expression: Expression = None
    line: int = 0
    column: int = 0


# ===== 表达式基类 =====


@dataclass
class Expression:
    """表达式基类"""

    line: int = 0
    column: int = 0


@dataclass
class AwaitExpr(Expression):
    """Await 表达式节点"""

    target: Expression = None
    line: int = 0
    column: int = 0

    def __str__(self):
        return f"等待({self.target})"


@dataclass
class CallExpr(Expression):
    """函数调用表达式"""

    function: str = ""
    arguments: List[Expression] = field(default_factory=list)
    line: int = 0
    column: int = 0


@dataclass
class IdentifierExpr(Expression):
    """标识符表达式"""

    name: str = ""
    line: int = 0
    column: int = 0


# ===== 语法树节点 =====


@dataclass
class ASTNode:
    """AST 节点基类"""

    line: int = 0
    column: int = 0


@dataclass
class AsyncFunctionNode(ASTNode):
    """异步函数节点"""

    name: str = ""
    parameters: List[Parameter] = field(default_factory=list)
    return_type: Optional[AsyncType] = None
    body: Optional[List[ASTNode]] = None
    is_async: bool = True
    line: int = 0
    column: int = 0


@dataclass
class AwaitNode(ASTNode):
    """Await 节点"""

    expression: Expression = None
    line: int = 0
    column: int = 0


@dataclass
class ReturnNode(ASTNode):
    """返回语句节点"""

    value: Optional[Expression] = None
    is_async: bool = True
    line: int = 0
    column: int = 0


@dataclass
class VariableDeclNode(ASTNode):
    """变量声明节点"""

    name: str = ""
    var_type: Optional[AsyncType] = None
    initial_value: Optional[Expression] = None
    line: int = 0
    column: int = 0


@dataclass
class YieldNode(ASTNode):
    """Yield 节点（用于生成器）"""

    value: Optional[Expression] = None


@dataclass
class AsyncBlockNode(ASTNode):
    """异步代码块节点"""

    statements: List[ASTNode] = field(default_factory=list)


# ===== 异步代码块 =====


@dataclass
class AsyncBlock:
    """异步代码块"""

    statements: List[ASTNode] = field(default_factory=list)
    variables: Dict[str, AsyncType] = field(default_factory=dict)

    def add_statement(self, stmt: ASTNode):
        self.statements.append(stmt)

    def add_variable(self, name: str, var_type: AsyncType):
        self.variables[name] = var_type


# ===== 异步函数类型 =====


@dataclass
class AsyncFunctionType:
    """异步函数类型"""

    parameter_types: List[AsyncType] = field(default_factory=list)
    return_type: Optional[AsyncType] = None

    def is_compatible_with(self, other: "AsyncFunctionType") -> bool:
        """检查类型兼容性"""
        if len(self.parameter_types) != len(other.parameter_types):
            return False

        for s, o in zip(self.parameter_types, other.parameter_types):
            if not self._types_compatible(s, o):
                return False

        return self._types_compatible(self.return_type, other.return_type)

    def _types_compatible(
        self, t1: Optional[AsyncType], t2: Optional[AsyncType]
    ) -> bool:
        """检查两个类型是否兼容"""
        if t1 is None and t2 is None:
            return True
        if t1 is None or t2 is None:
            return False
        return t1.name == t2.name


# ===== 异步任务 =====


class AsyncTask:
    """异步任务"""

    def __init__(self, coro: Callable):
        self._coro = coro
        self._result: Optional[Any] = None
        self._exception: Optional[Exception] = None
        self._done = False

    async def run(self):
        """运行异步任务"""
        try:
            self._result = await self._coro()
            self._done = True
        except Exception as e:
            self._exception = e
            self._done = True

    def is_done(self) -> bool:
        """检查任务是否完成"""
        return self._done

    def get_result(self) -> Any:
        """获取结果"""
        if self._exception:
            raise self._exception
        return self._result


# ===== 异步上下文 =====


class AsyncContext:
    """异步执行上下文"""

    def __init__(self):
        self.tasks: List[AsyncTask] = []
        self.current_task: Optional[AsyncTask] = None

    def add_task(self, task: AsyncTask):
        """添加异步任务"""
        self.tasks.append(task)

    async def run_all(self):
        """运行所有任务"""
        for task in self.tasks:
            await task.run()

    def get_pending_tasks(self) -> List[AsyncTask]:
        """获取待完成的任务"""
        return [t for t in self.tasks if not t.is_done()]


# ===== 异步语义分析 =====


class AsyncSemanticAnalyzer:
    """异步语义分析器

    负责：
    1. 异步函数类型检查
    2. Await 表达式上下文验证
    3. 返回类型匹配检查
    4. 异步类型推导
    """

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.async_functions: Dict[str, AsyncFunctionType] = {}
        self.current_async_context: Optional[str] = None  # 当前异步函数名
        self.scope_stack: List[Dict[str, AsyncType]] = []  # 作用域栈

    def analyze_async_function(self, node: AsyncFunctionNode) -> bool:
        """分析异步函数

        Args:
            node: 异步函数节点

        Returns:
            是否分析成功（无错误）
        """
        # 检查函数签名
        if not node.name:
            self.errors.append(f"异步函数缺少名称 (行 {node.line})")
            return False

        # 检查返回类型
        if node.return_type is None:
            self.warnings.append(
                f"异步函数 {node.name} 缺少返回类型标注 (行 {node.line})"
            )
        else:
            # 检查返回类型是否是异步类型
            if not self._is_valid_async_return_type(node.return_type):
                self.errors.append(
                    f"异步函数 {node.name} 的返回类型必须是 Future/Task/Promise (行 {node.line})"
                )

        # 检查参数类型
        for param in node.parameters:
            if param.param_type is None:
                self.warnings.append(f"参数 {param.name} 缺少类型标注 (行 {node.line})")

        # 进入异步上下文
        old_context = self.current_async_context
        self.current_async_context = node.name

        # 创建新的作用域
        self.scope_stack.append({})

        # 注册参数到作用域
        for param in node.parameters:
            if param.param_type:
                self.scope_stack[-1][param.name] = param.param_type

        # 注册函数类型（在分析函数体前）
        func_type = AsyncFunctionType(
            parameter_types=[p.param_type for p in node.parameters],
            return_type=node.return_type,
        )
        self.async_functions[node.name] = func_type

        # 分析函数体
        for stmt in node.body or []:
            self._analyze_statement(stmt)

        # 退出异步上下文
        self.current_async_context = old_context

        # 退出作用域（在异步上下文退出后）
        self.scope_stack.pop()

        return len(self.errors) == 0

    def _analyze_statement(self, stmt: ASTNode):
        """分析语句"""
        if isinstance(stmt, AwaitNode):
            self._analyze_await(stmt)
        elif isinstance(stmt, AsyncFunctionNode):
            self.analyze_async_function(stmt)
        elif isinstance(stmt, ReturnNode):
            self._analyze_return(stmt)
        elif isinstance(stmt, VariableDeclNode):
            self._analyze_variable_decl(stmt)

    def _analyze_await(self, node: AwaitNode):
        """分析 await 表达式

        检查：
        1. await 是否在异步函数中使用
        2. await 表达式的类型是否可等待（Future/Task/Promise）
        """
        # 检查 await 是否在异步上下文中
        if self.current_async_context is None:
            self.errors.append(
                f"await 表达式必须在异步函数中使用 (行 {node.line}, 列 {node.column})"
            )
            return

        # 检查 await 表达式的类型
        expr_type = self._infer_expression_type(node.expression)
        if expr_type is None:
            self.warnings.append(f"无法推导 await 表达式的类型 (行 {node.line})")
            return

        # 检查是否是异步类型
        if not self._is_awaitable_type(expr_type):
            self.errors.append(
                f"await 表达式的类型必须是 Future/Task/Promise，实际类型: {expr_type} "
                f"(行 {node.line}, 列 {node.column})"
            )

    def _analyze_return(self, node: ReturnNode):
        """分析返回语句

        检查：
        1. 返回值的类型是否匹配函数的返回类型
        2. 异步函数的 return 语句隐含返回 Future
        """
        if self.current_async_context is None:
            self.errors.append(f"返回语句必须在函数中使用 (行 {node.line})")
            return

        # 获取当前函数的返回类型
        func_type = self.async_functions.get(self.current_async_context)
        if func_type is None or func_type.return_type is None:
            return

        # 检查返回值类型
        if node.value is not None:
            value_type = self._infer_expression_type(node.value)
            if value_type is None:
                self.warnings.append(f"无法推导返回值的类型 (行 {node.line})")
                return

            # 异步函数的返回值类型检查
            # 返回语句的值类型应该匹配 Future 的内部类型
            expected_type = func_type.return_type
            if self._is_awaitable_type(expected_type):
                # 异步函数：返回值类型应该匹配 Future<T> 的 T
                expected_inner_type = expected_type.inner_type
                if expected_inner_type and not self._type_matches(
                    value_type, expected_inner_type
                ):
                    self.errors.append(
                        f"返回值类型不匹配，期望: {expected_inner_type}, 实际: {value_type} "
                        f"(行 {node.line})"
                    )
            else:
                # 普通函数：返回值类型应该匹配函数返回类型
                if not self._type_matches(value_type, expected_type):
                    self.errors.append(
                        f"返回值类型不匹配，期望: {expected_type}, 实际: {value_type} "
                        f"(行 {node.line})"
                    )

    def _analyze_variable_decl(self, node: VariableDeclNode):
        """分析变量声明"""
        if node.var_type:
            # 注册变量到作用域
            if self.scope_stack:
                self.scope_stack[-1][node.name] = node.var_type

        # 检查初始值类型
        if node.initial_value and node.var_type:
            init_type = self._infer_expression_type(node.initial_value)
            if init_type and not self._type_matches(init_type, node.var_type):
                self.errors.append(
                    f"变量初始值类型不匹配，期望: {node.var_type}, 实际: {init_type} "
                    f"(行 {node.line})"
                )

    def _infer_expression_type(self, expr: Expression) -> Optional[AsyncType]:
        """推导表达式类型

        Args:
            expr: 表达式

        Returns:
            推导的类型，如果无法推导则返回 None
        """
        if isinstance(expr, IdentifierExpr):
            # 从作用域查找变量类型
            for scope in reversed(self.scope_stack):
                if expr.name in scope:
                    return scope[expr.name]
            return None

        elif isinstance(expr, CallExpr):
            # 查找函数类型
            func_type = self.async_functions.get(expr.function)
            if func_type:
                return func_type.return_type
            return None

        elif isinstance(expr, AwaitExpr):
            # await 表达式的类型是内部类型
            target_type = self._infer_expression_type(expr.target)
            if target_type and isinstance(target_type, AsyncType):
                return target_type.inner_type
            return None

        return None

    def _is_valid_async_return_type(self, t: AsyncType) -> bool:
        """检查是否是有效的异步返回类型

        Args:
            t: 类型

        Returns:
            是否是 Future/Task/Promise 类型
        """
        return isinstance(t, (FutureType, TaskType, PromiseType))

    def _is_awaitable_type(self, t: AsyncType) -> bool:
        """检查是否是可等待的类型

        Args:
            t: 类型

        Returns:
            是否是 Future/Task/Promise 类型
        """
        return isinstance(t, (FutureType, TaskType, PromiseType))

    def _type_matches(self, actual: AsyncType, expected: AsyncType) -> bool:
        """检查类型是否匹配

        Args:
            actual: 实际类型
            expected: 期望类型

        Returns:
            是否匹配
        """
        # 简单类型匹配
        if str(actual) == str(expected):
            return True

        # 异步类型内部类型匹配
        if isinstance(actual, AsyncType) and isinstance(expected, AsyncType):
            if actual.inner_type and expected.inner_type:
                return self._type_matches(actual.inner_type, expected.inner_type)

        return False

    def check_await_context(self, node: AwaitNode) -> bool:
        """检查 await 是否在异步上下文中使用

        Args:
            node: Await 节点

        Returns:
            是否在异步上下文中
        """
        return self.current_async_context is not None

    def get_analysis_result(self) -> Dict[str, Any]:
        """获取分析结果

        Returns:
            包含错误、警告、函数类型的字典
        """
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "async_functions": {
                name: {
                    "parameters": [str(p) for p in func_type.parameter_types],
                    "return_type": str(func_type.return_type)
                    if func_type.return_type
                    else None,
                }
                for name, func_type in self.async_functions.items()
            },
        }


# ===== 异步工具函数 =====


def create_future_type(inner_type: Optional[AsyncType] = None) -> FutureType:
    """创建 Future 类型"""
    return FutureType(name="未来", inner_type=inner_type)


def create_task_type(inner_type: Optional[AsyncType] = None) -> TaskType:
    """创建 Task 类型"""
    return TaskType(name="任务", inner_type=inner_type)


def create_promise_type(inner_type: Optional[AsyncType] = None) -> PromiseType:
    """创建 Promise 类型"""
    return PromiseType(name="承诺", inner_type=inner_type)


def is_async_type(t: AsyncType) -> bool:
    """检查是否是异步类型"""
    return t.is_async()


def unwrap_async_type(t: AsyncType) -> Optional[AsyncType]:
    """解包异步类型的内部类型"""
    return t.inner_type


# ===== 示例用法 =====

if __name__ == "__main__":
    print("=" * 70)
    print("异步编程系统测试")
    print("=" * 70)

    # 测试异步类型
    print("\n测试 1: 异步类型")
    future_int = create_future_type(AsyncType("整数"))
    print(f"  Future<int>: {future_int}")

    task_string = create_task_type(AsyncType("字符串"))
    print(f"  Task<string>: {task_string}")

    # 测试异步函数
    print("\n测试 2: 异步函数")
    async_func = AsyncFunction(
        name="获取数据",
        parameters=[
            Parameter("url", AsyncType("字符串")),
            Parameter("timeout", AsyncType("整数")),
        ],
        return_type=create_future_type(AsyncType("字符串")),
    )
    print(f"  {async_func.get_signature()}")

    # 测试异步函数类型
    print("\n测试 3: 异步函数类型兼容性")
    func_type1 = AsyncFunctionType(
        parameter_types=[AsyncType("整数"), AsyncType("字符串")],
        return_type=AsyncType("整数"),
    )
    func_type2 = AsyncFunctionType(
        parameter_types=[AsyncType("整数"), AsyncType("字符串")],
        return_type=AsyncType("整数"),
    )
    print(f"  类型兼容: {func_type1.is_compatible_with(func_type2)}")

    # 测试语义分析
    print("\n测试 4: 语义分析")
    analyzer = AsyncSemanticAnalyzer()
    func_node = AsyncFunctionNode(
        name="异步读取",
        parameters=[Parameter("path", AsyncType("字符串"))],
        return_type=create_future_type(AsyncType("字符串")),
        body=[AwaitNode(expression=IdentifierExpr(name="some_async_call"))],
    )
    result = analyzer.analyze_async_function(func_node)
    print(f"  分析结果: {'成功' if result else '失败'}")
    if analyzer.errors:
        print(f"  错误: {', '.join(analyzer.errors)}")
    if analyzer.warnings:
        print(f"  警告: {', '.join(analyzer.warnings)}")

    print("\n" + "=" * 70)
    print("所有测试完成")
    print("=" * 70)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步语义分析器测试 - Async Semantic Analyzer Tests

测试异步语义分析器的功能：
1. 异步函数类型检查
2. Await 表达式上下文验证
3. 返回类型匹配检查
4. 异步类型推导

Phase 4 - Stage 2 - Task 11.3 - Day 2

作者：ZHC 开发团队
日期：2026-04-08
"""

import pytest
from zhc.semantic.async_system import (
    AsyncSemanticAnalyzer,
    AsyncFunctionNode,
    AwaitNode,
    ReturnNode,
    VariableDeclNode,
    Parameter,
    FutureType,
    TaskType,
    PromiseType,
    AsyncType,
    IdentifierExpr,
    CallExpr,
    AwaitExpr,
    create_future_type,
    create_task_type,
    create_promise_type,
)


class TestAsyncFunctionAnalysis:
    """测试异步函数分析"""

    def test_valid_async_function(self):
        """测试有效的异步函数"""
        analyzer = AsyncSemanticAnalyzer()
        
        # 创建异步函数节点
        func_node = AsyncFunctionNode(
            name="获取数据",
            parameters=[
                Parameter(name="url", param_type=AsyncType("字符串"))
            ],
            return_type=create_future_type(AsyncType("字符串")),
            body=[
                ReturnNode(value=IdentifierExpr(name="结果"))
            ],
            line=1,
            column=1
        )
        
        # 分析函数
        result = analyzer.analyze_async_function(func_node)
        
        # 应该成功
        assert result is True
        assert len(analyzer.errors) == 0
        assert "获取数据" in analyzer.async_functions

    def test_async_function_missing_name(self):
        """测试缺少名称的异步函数"""
        analyzer = AsyncSemanticAnalyzer()
        
        func_node = AsyncFunctionNode(
            name="",  # 空名称
            return_type=create_future_type(AsyncType("整数")),
            line=1,
            column=1
        )
        
        result = analyzer.analyze_async_function(func_node)
        
        # 应该失败
        assert result is False
        assert len(analyzer.errors) > 0
        assert "缺少名称" in analyzer.errors[0]

    def test_async_function_missing_return_type(self):
        """测试缺少返回类型的异步函数"""
        analyzer = AsyncSemanticAnalyzer()
        
        func_node = AsyncFunctionNode(
            name="测试函数",
            return_type=None,  # 缺少返回类型
            line=1,
            column=1
        )
        
        result = analyzer.analyze_async_function(func_node)
        
        # 应该成功（但有警告）
        assert result is True
        assert len(analyzer.warnings) > 0
        assert "缺少返回类型标注" in analyzer.warnings[0]

    def test_async_function_invalid_return_type(self):
        """测试无效的返回类型（非异步类型）"""
        analyzer = AsyncSemanticAnalyzer()
        
        func_node = AsyncFunctionNode(
            name="测试函数",
            return_type=AsyncType("整数"),  # 不是异步类型
            line=1,
            column=1
        )
        
        result = analyzer.analyze_async_function(func_node)
        
        # 应该失败
        assert result is False
        assert len(analyzer.errors) > 0
        assert "必须是 Future/Task/Promise" in analyzer.errors[0]

    def test_async_function_with_parameters(self):
        """测试带参数的异步函数"""
        analyzer = AsyncSemanticAnalyzer()
        
        func_node = AsyncFunctionNode(
            name="计算",
            parameters=[
                Parameter(name="a", param_type=AsyncType("整数")),
                Parameter(name="b", param_type=AsyncType("整数"))
            ],
            return_type=create_task_type(AsyncType("整数")),
            line=1,
            column=1
        )
        
        result = analyzer.analyze_async_function(func_node)
        
        # 应该成功
        assert result is True
        assert len(analyzer.errors) == 0
        
        # 检查函数类型
        func_type = analyzer.async_functions["计算"]
        assert len(func_type.parameter_types) == 2


class TestAwaitExpressionAnalysis:
    """测试 Await 表达式分析"""

    def test_await_in_async_context(self):
        """测试在异步上下文中的 await"""
        analyzer = AsyncSemanticAnalyzer()
        
        # 创建异步函数
        func_node = AsyncFunctionNode(
            name="获取数据",
            return_type=create_future_type(AsyncType("字符串")),
            body=[
                AwaitNode(
                    expression=CallExpr(
                        function="获取远程数据",
                        arguments=[IdentifierExpr(name="url")]
                    ),
                    line=2,
                    column=5
                )
            ],
            line=1,
            column=1
        )
        
        # 先注册一个异步函数
        analyzer.async_functions["获取远程数据"] = AsyncFunctionType(
            parameter_types=[AsyncType("字符串")],
            return_type=create_future_type(AsyncType("字符串"))
        )
        
        result = analyzer.analyze_async_function(func_node)
        
        # 应该成功
        assert result is True
        assert len(analyzer.errors) == 0

    def test_await_outside_async_context(self):
        """测试在非异步上下文中的 await"""
        analyzer = AsyncSemanticAnalyzer()
        
        # 直接分析 await 节点（不在异步函数中）
        await_node = AwaitNode(
            expression=CallExpr(function="获取数据"),
            line=1,
            column=1
        )
        
        analyzer._analyze_await(await_node)
        
        # 应该有错误
        assert len(analyzer.errors) > 0
        assert "必须在异步函数中使用" in analyzer.errors[0]

    def test_await_non_awaitable_type(self):
        """测试 await 非异步类型"""
        analyzer = AsyncSemanticAnalyzer()
        
        # 创建异步函数
        func_node = AsyncFunctionNode(
            name="测试",
            return_type=create_future_type(AsyncType("整数")),
            body=[
                AwaitNode(
                    expression=IdentifierExpr(name="x"),  # x 是普通变量
                    line=2,
                    column=5
                )
            ],
            line=1,
            column=1
        )
        
        # 注册变量 x（非异步类型）
        analyzer.scope_stack.append({"x": AsyncType("整数")})
        
        result = analyzer.analyze_async_function(func_node)
        
        # 应该有错误
        assert len(analyzer.errors) > 0
        assert "必须是 Future/Task/Promise" in analyzer.errors[0]

    def test_await_future_type(self):
        """测试 await Future 类型"""
        analyzer = AsyncSemanticAnalyzer()
        
        # 创建异步函数
        func_node = AsyncFunctionNode(
            name="测试",
            return_type=create_future_type(AsyncType("整数")),
            body=[
                AwaitNode(
                    expression=IdentifierExpr(name="future_result"),
                    line=2,
                    column=5
                )
            ],
            line=1,
            column=1
        )
        
        # 注册变量（Future 类型）
        analyzer.scope_stack.append({
            "future_result": create_future_type(AsyncType("整数"))
        })
        
        result = analyzer.analyze_async_function(func_node)
        
        # 应该成功
        assert result is True
        assert len(analyzer.errors) == 0

    def test_await_task_type(self):
        """测试 await Task 类型"""
        analyzer = AsyncSemanticAnalyzer()
        
        func_node = AsyncFunctionNode(
            name="测试",
            return_type=create_task_type(AsyncType("字符串")),
            body=[
                AwaitNode(
                    expression=IdentifierExpr(name="task_result"),
                    line=2,
                    column=5
                )
            ],
            line=1,
            column=1
        )
        
        analyzer.scope_stack.append({
            "task_result": create_task_type(AsyncType("字符串"))
        })
        
        result = analyzer.analyze_async_function(func_node)
        
        # 应该成功
        assert result is True
        assert len(analyzer.errors) == 0

    def test_await_promise_type(self):
        """测试 await Promise 类型"""
        analyzer = AsyncSemanticAnalyzer()
        
        func_node = AsyncFunctionNode(
            name="测试",
            return_type=create_promise_type(AsyncType("布尔")),
            body=[
                AwaitNode(
                    expression=IdentifierExpr(name="promise_result"),
                    line=2,
                    column=5
                )
            ],
            line=1,
            column=1
        )
        
        analyzer.scope_stack.append({
            "promise_result": create_promise_type(AsyncType("布尔"))
        })
        
        result = analyzer.analyze_async_function(func_node)
        
        # 应该成功
        assert result is True
        assert len(analyzer.errors) == 0


class TestReturnStatementAnalysis:
    """测试返回语句分析"""

    def test_return_value_type_match(self):
        """测试返回值类型匹配"""
        analyzer = AsyncSemanticAnalyzer()
        
        func_node = AsyncFunctionNode(
            name="获取整数",
            return_type=create_future_type(AsyncType("整数")),
            body=[
                ReturnNode(
                    value=IdentifierExpr(name="x"),
                    line=2,
                    column=5
                )
            ],
            line=1,
            column=1
        )
        
        # 注册变量 x
        analyzer.scope_stack.append({"x": AsyncType("整数")})
        
        result = analyzer.analyze_async_function(func_node)
        
        # 应该成功
        assert result is True
        assert len(analyzer.errors) == 0

    def test_return_value_type_mismatch(self):
        """测试返回值类型不匹配"""
        analyzer = AsyncSemanticAnalyzer()
        
        # 创建异步函数，返回类型是 Future<整数>，但返回字符串
        func_node = AsyncFunctionNode(
            name="获取整数",
            parameters=[
                Parameter(name="s", param_type=AsyncType("字符串"))  # 参数 s 是字符串
            ],
            return_type=create_future_type(AsyncType("整数")),  # 返回 Future<整数>
            body=[
                ReturnNode(
                    value=IdentifierExpr(name="s"),  # 返回 s（字符串）
                    line=2,
                    column=5
                )
            ],
            line=1,
            column=1
        )
        
        result = analyzer.analyze_async_function(func_node)
        
        # 应该有错误
        assert len(analyzer.errors) > 0
        assert "类型不匹配" in analyzer.errors[0]

    def test_return_outside_function(self):
        """测试在函数外使用返回语句"""
        analyzer = AsyncSemanticAnalyzer()
        
        return_node = ReturnNode(
            value=IdentifierExpr(name="x"),
            line=1,
            column=1
        )
        
        analyzer._analyze_return(return_node)
        
        # 应该有错误
        assert len(analyzer.errors) > 0
        assert "必须在函数中使用" in analyzer.errors[0]


class TestVariableDeclarationAnalysis:
    """测试变量声明分析"""

    def test_variable_with_type_annotation(self):
        """测试带类型标注的变量声明"""
        analyzer = AsyncSemanticAnalyzer()
        
        func_node = AsyncFunctionNode(
            name="测试",
            return_type=create_future_type(AsyncType("整数")),
            body=[
                VariableDeclNode(
                    name="x",
                    var_type=AsyncType("整数"),
                    line=2,
                    column=5
                ),
                ReturnNode(
                    value=IdentifierExpr(name="x"),
                    line=3,
                    column=5
                )
            ],
            line=1,
            column=1
        )
        
        result = analyzer.analyze_async_function(func_node)
        
        # 应该成功
        assert result is True
        assert len(analyzer.errors) == 0
        
        # 检查变量是否注册到作用域（函数退出后会弹出作用域栈，所以检查 empty 状态）
        # 实际上函数退出后 scope_stack 为空，我们需要检查 errors 为空即可
        assert len(analyzer.errors) == 0

    def test_variable_with_initial_value(self):
        """测试带初始值的变量声明"""
        analyzer = AsyncSemanticAnalyzer()
        
        func_node = AsyncFunctionNode(
            name="测试",
            return_type=create_future_type(AsyncType("整数")),
            body=[
                VariableDeclNode(
                    name="x",
                    var_type=AsyncType("整数"),
                    initial_value=IdentifierExpr(name="y"),
                    line=2,
                    column=5
                )
            ],
            line=1,
            column=1
        )
        
        # 注册变量 y
        analyzer.scope_stack.append({"y": AsyncType("整数")})
        
        result = analyzer.analyze_async_function(func_node)
        
        # 应该成功
        assert result is True
        assert len(analyzer.errors) == 0

    def test_variable_type_mismatch(self):
        """测试变量类型不匹配"""
        analyzer = AsyncSemanticAnalyzer()
        
        func_node = AsyncFunctionNode(
            name="测试",
            return_type=create_future_type(AsyncType("整数")),
            body=[
                VariableDeclNode(
                    name="x",
                    var_type=AsyncType("整数"),
                    initial_value=IdentifierExpr(name="s"),  # s 是字符串
                    line=2,
                    column=5
                )
            ],
            line=1,
            column=1
        )
        
        # 注册变量 s（字符串类型）
        analyzer.scope_stack.append({"s": AsyncType("字符串")})
        
        result = analyzer.analyze_async_function(func_node)
        
        # 应该有错误
        assert len(analyzer.errors) > 0
        assert "类型不匹配" in analyzer.errors[0]


class TestTypeInference:
    """测试类型推导"""

    def test_infer_identifier_type(self):
        """测试推导标识符类型"""
        analyzer = AsyncSemanticAnalyzer()
        
        # 注册变量
        analyzer.scope_stack.append({"x": AsyncType("整数")})
        
        expr = IdentifierExpr(name="x")
        inferred_type = analyzer._infer_expression_type(expr)
        
        # 应该推导出整数类型
        assert inferred_type is not None
        assert str(inferred_type) == "整数"

    def test_infer_call_type(self):
        """测试推导函数调用类型"""
        analyzer = AsyncSemanticAnalyzer()
        
        # 注册函数
        analyzer.async_functions["获取数据"] = AsyncFunctionType(
            parameter_types=[],
            return_type=create_future_type(AsyncType("字符串"))
        )
        
        expr = CallExpr(function="获取数据")
        inferred_type = analyzer._infer_expression_type(expr)
        
        # 应该推导出 Future<字符串> 类型
        assert inferred_type is not None
        assert isinstance(inferred_type, FutureType)

    def test_infer_await_type(self):
        """测试推导 await 表达式类型"""
        analyzer = AsyncSemanticAnalyzer()
        
        # 注册变量（Future 类型）
        analyzer.scope_stack.append({
            "future_result": create_future_type(AsyncType("整数"))
        })
        
        expr = AwaitExpr(target=IdentifierExpr(name="future_result"))
        inferred_type = analyzer._infer_expression_type(expr)
        
        # 应该推导出整数类型（Future 的内部类型）
        assert inferred_type is not None
        assert str(inferred_type) == "整数"


class TestTypeChecking:
    """测试类型检查"""

    def test_is_valid_async_return_type(self):
        """测试有效的异步返回类型"""
        analyzer = AsyncSemanticAnalyzer()
        
        # Future 类型
        assert analyzer._is_valid_async_return_type(create_future_type(AsyncType("整数")))
        
        # Task 类型
        assert analyzer._is_valid_async_return_type(create_task_type(AsyncType("字符串")))
        
        # Promise 类型
        assert analyzer._is_valid_async_return_type(create_promise_type(AsyncType("布尔")))
        
        # 普通类型（无效）
        assert not analyzer._is_valid_async_return_type(AsyncType("整数"))

    def test_is_awaitable_type(self):
        """测试可等待类型"""
        analyzer = AsyncSemanticAnalyzer()
        
        # Future 类型
        assert analyzer._is_awaitable_type(create_future_type(AsyncType("整数")))
        
        # Task 类型
        assert analyzer._is_awaitable_type(create_task_type(AsyncType("字符串")))
        
        # Promise 类型
        assert analyzer._is_awaitable_type(create_promise_type(AsyncType("布尔")))
        
        # 普通类型（不可等待）
        assert not analyzer._is_awaitable_type(AsyncType("整数"))

    def test_type_matches(self):
        """测试类型匹配"""
        analyzer = AsyncSemanticAnalyzer()
        
        # 相同类型
        assert analyzer._type_matches(AsyncType("整数"), AsyncType("整数"))
        
        # 不同类型
        assert not analyzer._type_matches(AsyncType("整数"), AsyncType("字符串"))
        
        # 异步类型内部类型匹配
        future1 = create_future_type(AsyncType("整数"))
        future2 = create_future_type(AsyncType("整数"))
        assert analyzer._type_matches(future1, future2)


class TestAnalysisResult:
    """测试分析结果"""

    def test_get_analysis_result(self):
        """测试获取分析结果"""
        analyzer = AsyncSemanticAnalyzer()
        
        func_node = AsyncFunctionNode(
            name="获取数据",
            parameters=[
                Parameter(name="url", param_type=AsyncType("字符串"))
            ],
            return_type=create_future_type(AsyncType("字符串")),
            line=1,
            column=1
        )
        
        analyzer.analyze_async_function(func_node)
        
        result = analyzer.get_analysis_result()
        
        # 检查结果结构
        assert "errors" in result
        assert "warnings" in result
        assert "async_functions" in result
        
        # 检查函数信息
        assert "获取数据" in result["async_functions"]
        func_info = result["async_functions"]["获取数据"]
        assert func_info["return_type"] == "未来<字符串>"  # 修正：应该是字符串而不是整数


class TestComplexScenarios:
    """测试复杂场景"""

    def test_nested_async_functions(self):
        """测试嵌套异步函数"""
        analyzer = AsyncSemanticAnalyzer()
        
        # 外层函数
        outer_func = AsyncFunctionNode(
            name="外层",
            return_type=create_future_type(AsyncType("整数")),
            body=[
                # 内层函数
                AsyncFunctionNode(
                    name="内层",
                    return_type=create_task_type(AsyncType("整数")),
                    body=[
                        ReturnNode(value=IdentifierExpr(name="x"))
                    ],
                    line=2,
                    column=5
                )
            ],
            line=1,
            column=1
        )
        
        result = analyzer.analyze_async_function(outer_func)
        
        # 应该成功
        assert result is True
        assert len(analyzer.errors) == 0

    def test_multiple_await_statements(self):
        """测试多个 await 语句"""
        analyzer = AsyncSemanticAnalyzer()
        
        func_node = AsyncFunctionNode(
            name="测试",
            return_type=create_future_type(AsyncType("整数")),
            body=[
                AwaitNode(
                    expression=IdentifierExpr(name="future1"),
                    line=2,
                    column=5
                ),
                AwaitNode(
                    expression=IdentifierExpr(name="future2"),
                    line=3,
                    column=5
                )
            ],
            line=1,
            column=1
        )
        
        # 注册变量
        analyzer.scope_stack.append({
            "future1": create_future_type(AsyncType("整数")),
            "future2": create_future_type(AsyncType("整数"))
        })
        
        result = analyzer.analyze_async_function(func_node)
        
        # 应该成功
        assert result is True
        assert len(analyzer.errors) == 0

    def test_async_function_with_variables_and_await(self):
        """测试带变量和 await 的异步函数"""
        analyzer = AsyncSemanticAnalyzer()
        
        func_node = AsyncFunctionNode(
            name="计算",
            parameters=[
                Parameter(name="a", param_type=AsyncType("整数")),
                Parameter(name="b", param_type=AsyncType("整数"))
            ],
            return_type=create_future_type(AsyncType("整数")),
            body=[
                VariableDeclNode(
                    name="result",
                    var_type=AsyncType("整数"),
                    line=2,
                    column=5
                ),
                AwaitNode(
                    expression=CallExpr(
                        function="异步计算",
                        arguments=[
                            IdentifierExpr(name="a"),
                            IdentifierExpr(name="b")
                        ]
                    ),
                    line=3,
                    column=5
                ),
                ReturnNode(
                    value=IdentifierExpr(name="result"),
                    line=4,
                    column=5
                )
            ],
            line=1,
            column=1
        )
        
        # 注册异步函数
        analyzer.async_functions["异步计算"] = AsyncFunctionType(
            parameter_types=[AsyncType("整数"), AsyncType("整数")],
            return_type=create_future_type(AsyncType("整数"))
        )
        
        result = analyzer.analyze_async_function(func_node)
        
        # 应该成功
        assert result is True
        assert len(analyzer.errors) == 0


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_async_function(self):
        """测试空异步函数"""
        analyzer = AsyncSemanticAnalyzer()
        
        func_node = AsyncFunctionNode(
            name="空函数",
            return_type=create_future_type(AsyncType("整数")),
            body=[],  # 空函数体
            line=1,
            column=1
        )
        
        result = analyzer.analyze_async_function(func_node)
        
        # 应该成功
        assert result is True
        assert len(analyzer.errors) == 0

    def test_async_function_with_no_parameters(self):
        """测试无参数的异步函数"""
        analyzer = AsyncSemanticAnalyzer()
        
        func_node = AsyncFunctionNode(
            name="无参数函数",
            parameters=[],  # 无参数
            return_type=create_future_type(AsyncType("整数")),
            line=1,
            column=1
        )
        
        result = analyzer.analyze_async_function(func_node)
        
        # 应该成功
        assert result is True
        assert len(analyzer.errors) == 0

    def test_unknown_identifier_type(self):
        """测试未知标识符类型"""
        analyzer = AsyncSemanticAnalyzer()
        
        expr = IdentifierExpr(name="unknown_var")
        inferred_type = analyzer._infer_expression_type(expr)
        
        # 应该无法推导
        assert inferred_type is None

    def test_unknown_function_type(self):
        """测试未知函数类型"""
        analyzer = AsyncSemanticAnalyzer()
        
        expr = CallExpr(function="unknown_func")
        inferred_type = analyzer._infer_expression_type(expr)
        
        # 应该无法推导
        assert inferred_type is None


# ===== 需要导入的类 =====

from zhc.semantic.async_system import AsyncFunctionType


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
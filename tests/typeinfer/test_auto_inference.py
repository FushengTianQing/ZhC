#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动类型推导测试
Auto Type Inference Tests

测试自动类型推导功能：
- 变量类型推导
- 函数返回类型推导
- 表达式类型推导

作者: 阿福
日期: 2026-04-09
"""

import pytest

from zhc.parser.ast_nodes import (
    VariableDeclNode,
    FunctionDeclNode,
    PrimitiveTypeNode,
    AutoTypeNode,
    IntLiteralNode,
    FloatLiteralNode,
    StringLiteralNode,
    CharLiteralNode,
    BoolLiteralNode,
    BinaryExprNode,
    IdentifierExprNode,
    BlockStmtNode,
    ReturnStmtNode,
    ArrayInitNode,
    ParamDeclNode,
)
from zhc.typeinfer.auto_inference import (
    AutoTypeInferencer,
    infer_auto_type,
    infer_function_return,
)


class TestAutoTypeInferencer:
    """自动类型推导器测试"""

    def test_infer_int_variable(self):
        """测试整数类型推导"""
        # 自动 x = 42;
        var_node = VariableDeclNode(
            name="x",
            var_type=AutoTypeNode(),
            init=IntLiteralNode(value=42),
            is_auto=True,
        )

        inferencer = AutoTypeInferencer()
        result = inferencer.infer_variable_type(var_node)

        assert result.inferred_type == "整数型"
        assert result.confidence == 1.0
        assert var_node.inferred_type == "整数型"

    def test_infer_float_variable(self):
        """测试浮点类型推导"""
        # 自动 y = 3.14;
        var_node = VariableDeclNode(
            name="y",
            var_type=AutoTypeNode(),
            init=FloatLiteralNode(value=3.14),
            is_auto=True,
        )

        inferencer = AutoTypeInferencer()
        result = inferencer.infer_variable_type(var_node)

        assert result.inferred_type == "浮点型"
        assert result.confidence == 1.0

    def test_infer_string_variable(self):
        """测试字符串类型推导"""
        # 自动 s = "hello";
        var_node = VariableDeclNode(
            name="s",
            var_type=AutoTypeNode(),
            init=StringLiteralNode(value="hello"),
            is_auto=True,
        )

        inferencer = AutoTypeInferencer()
        result = inferencer.infer_variable_type(var_node)

        assert result.inferred_type == "字符串型"
        assert result.confidence == 1.0

    def test_infer_char_variable(self):
        """测试字符类型推导"""
        # 自动 c = 'A';
        var_node = VariableDeclNode(
            name="c",
            var_type=AutoTypeNode(),
            init=CharLiteralNode(value="A"),
            is_auto=True,
        )

        inferencer = AutoTypeInferencer()
        result = inferencer.infer_variable_type(var_node)

        assert result.inferred_type == "字符型"
        assert result.confidence == 1.0

    def test_infer_bool_variable(self):
        """测试布尔类型推导"""
        # 自动 b = 真;
        var_node = VariableDeclNode(
            name="b",
            var_type=AutoTypeNode(),
            init=BoolLiteralNode(value=True),
            is_auto=True,
        )

        inferencer = AutoTypeInferencer()
        result = inferencer.infer_variable_type(var_node)

        assert result.inferred_type == "布尔型"
        assert result.confidence == 1.0

    def test_infer_binary_expr_int(self):
        """测试整数二元表达式类型推导"""
        # 自动 x = 10 + 20;
        var_node = VariableDeclNode(
            name="x",
            var_type=AutoTypeNode(),
            init=BinaryExprNode(
                operator="+",
                left=IntLiteralNode(value=10),
                right=IntLiteralNode(value=20),
            ),
            is_auto=True,
        )

        inferencer = AutoTypeInferencer()
        result = inferencer.infer_variable_type(var_node)

        assert result.inferred_type == "整数型"
        assert result.confidence == 0.9

    def test_infer_binary_expr_float(self):
        """测试浮点二元表达式类型推导"""
        # 自动 y = 3.14 + 2.0;
        var_node = VariableDeclNode(
            name="y",
            var_type=AutoTypeNode(),
            init=BinaryExprNode(
                operator="+",
                left=FloatLiteralNode(value=3.14),
                right=FloatLiteralNode(value=2.0),
            ),
            is_auto=True,
        )

        inferencer = AutoTypeInferencer()
        result = inferencer.infer_variable_type(var_node)

        assert result.inferred_type == "浮点型"

    def test_infer_binary_expr_mixed(self):
        """测试混合类型二元表达式类型推导"""
        # 自动 z = 10 + 3.14;  // 整数 + 浮点 = 浮点
        var_node = VariableDeclNode(
            name="z",
            var_type=AutoTypeNode(),
            init=BinaryExprNode(
                operator="+",
                left=IntLiteralNode(value=10),
                right=FloatLiteralNode(value=3.14),
            ),
            is_auto=True,
        )

        inferencer = AutoTypeInferencer()
        result = inferencer.infer_variable_type(var_node)

        assert result.inferred_type == "浮点型"

    def test_infer_comparison_expr(self):
        """测试比较表达式类型推导"""
        # 自动 cmp = 10 < 20;
        var_node = VariableDeclNode(
            name="cmp",
            var_type=AutoTypeNode(),
            init=BinaryExprNode(
                operator="<",
                left=IntLiteralNode(value=10),
                right=IntLiteralNode(value=20),
            ),
            is_auto=True,
        )

        inferencer = AutoTypeInferencer()
        result = inferencer.infer_variable_type(var_node)

        assert result.inferred_type == "布尔型"

    def test_infer_array_type(self):
        """测试数组类型推导"""
        # 自动 arr = [1, 2, 3];
        var_node = VariableDeclNode(
            name="arr",
            var_type=AutoTypeNode(),
            init=ArrayInitNode(
                elements=[
                    IntLiteralNode(value=1),
                    IntLiteralNode(value=2),
                    IntLiteralNode(value=3),
                ]
            ),
            is_auto=True,
        )

        inferencer = AutoTypeInferencer()
        result = inferencer.infer_variable_type(var_node)

        assert result.inferred_type == "整数型[3]"
        assert result.confidence == 0.8

    def test_auto_without_init_fails(self):
        """测试自动类型无初始化表达式时失败"""
        # 自动 x;  // 错误：无初始化
        var_node = VariableDeclNode(
            name="x",
            var_type=AutoTypeNode(),
            init=None,
            is_auto=True,
        )

        inferencer = AutoTypeInferencer()
        result = inferencer.infer_variable_type(var_node)

        assert result.inferred_type == "未知"
        assert result.confidence == 0.0
        assert "初始化表达式" in result.explanation

    def test_non_auto_variable(self):
        """测试非自动类型变量"""
        # 整数型 x = 42;
        var_node = VariableDeclNode(
            name="x",
            var_type=PrimitiveTypeNode("整数型"),
            init=IntLiteralNode(value=42),
            is_auto=False,
        )

        inferencer = AutoTypeInferencer()
        result = inferencer.infer_variable_type(var_node)

        assert result.inferred_type == "整数型"
        assert result.confidence == 1.0


class TestFunctionReturnTypeInference:
    """函数返回类型推导测试"""

    def test_infer_int_return(self):
        """测试整数返回类型推导"""
        # 自动型 加(整数型 a, 整数型 b) { 返回 a + b; }
        func_node = FunctionDeclNode(
            name="加",
            return_type=AutoTypeNode(),
            params=[
                ParamDeclNode(name="a", param_type=PrimitiveTypeNode("整数型")),
                ParamDeclNode(name="b", param_type=PrimitiveTypeNode("整数型")),
            ],
            body=BlockStmtNode(
                statements=[
                    ReturnStmtNode(
                        value=BinaryExprNode(
                            operator="+",
                            left=IdentifierExprNode(name="a"),
                            right=IdentifierExprNode(name="b"),
                        )
                    )
                ]
            ),
            is_auto_return=True,
        )

        inferencer = AutoTypeInferencer()
        # 注册参数类型
        inferencer.register_variable("a", "整数型")
        inferencer.register_variable("b", "整数型")

        result = inferencer.infer_function_return_type(func_node)

        assert result.inferred_type == "整数型"
        assert result.confidence == 1.0  # 直接 return 语句有最高置信度

    def test_infer_void_return(self):
        """测试空返回类型推导"""
        # 自动型 无返回() { }
        func_node = FunctionDeclNode(
            name="无返回",
            return_type=AutoTypeNode(),
            params=[],
            body=BlockStmtNode(statements=[]),
            is_auto_return=True,
        )

        inferencer = AutoTypeInferencer()
        result = inferencer.infer_function_return_type(func_node)

        assert result.inferred_type == "空型"

    def test_infer_explicit_return_type(self):
        """测试显式返回类型"""
        # 整数型 函数() { 返回 42; }
        func_node = FunctionDeclNode(
            name="函数",
            return_type=PrimitiveTypeNode("整数型"),
            params=[],
            body=BlockStmtNode(
                statements=[ReturnStmtNode(value=IntLiteralNode(value=42))]
            ),
            is_auto_return=False,
        )

        inferencer = AutoTypeInferencer()
        result = inferencer.infer_function_return_type(func_node)

        assert result.inferred_type == "整数型"
        assert "显式" in result.explanation


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_infer_auto_type_function(self):
        """测试 infer_auto_type 便捷函数"""
        var_node = VariableDeclNode(
            name="x",
            var_type=AutoTypeNode(),
            init=IntLiteralNode(value=42),
            is_auto=True,
        )

        result = infer_auto_type(var_node)
        assert result == "整数型"

    def test_infer_function_return_function(self):
        """测试 infer_function_return 便捷函数"""
        func_node = FunctionDeclNode(
            name="测试",
            return_type=AutoTypeNode(),
            params=[],
            body=BlockStmtNode(
                statements=[ReturnStmtNode(value=FloatLiteralNode(value=3.14))]
            ),
            is_auto_return=True,
        )

        result = infer_function_return(func_node)
        assert result == "浮点型"


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_array(self):
        """测试空数组类型推导"""
        var_node = VariableDeclNode(
            name="empty",
            var_type=AutoTypeNode(),
            init=ArrayInitNode(elements=[]),
            is_auto=True,
        )

        inferencer = AutoTypeInferencer()
        result = inferencer.infer_variable_type(var_node)

        assert "整数型" in result.inferred_type
        assert result.confidence == 0.5

    def test_multiple_returns_same_type(self):
        """测试多个返回语句相同类型"""
        func_node = FunctionDeclNode(
            name="多返回",
            return_type=AutoTypeNode(),
            params=[],
            body=BlockStmtNode(
                statements=[
                    ReturnStmtNode(value=IntLiteralNode(value=1)),
                    ReturnStmtNode(value=IntLiteralNode(value=2)),
                ]
            ),
            is_auto_return=True,
        )

        inferencer = AutoTypeInferencer()
        result = inferencer.infer_function_return_type(func_node)

        assert result.inferred_type == "整数型"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

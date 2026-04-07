#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泛型解析器测试 - Test Generic Parser

测试泛型语法解析功能：
1. 泛型类型声明
2. 泛型函数声明
3. 类型参数和约束
4. Where 子句
5. 嵌套泛型

Phase 4 - Stage 2 - Task 11.1

作者：ZHC 开发团队
日期：2026-04-08
"""

import pytest
import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 导入测试框架
from zhc.errors import LexerError

# 导入泛型解析模块
from zhc.semantic.generic_parser import (
    TypeNode,
    TypeParameterNode,
    GenericTypeDeclNode,
    GenericFunctionDeclNode,
    WhereClauseNode,
    GenericParserMixin,
)

# 导入词法分析器
from zhc.parser.lexer import Lexer, Token, TokenType


class MockParser(GenericParserMixin):
    """模拟解析器用于测试"""
    
    def __init__(self, source: str):
        self.source = source
        self.lexer = Lexer(source)
        self.tokens = self.lexer.tokenize()
        self.pos = 0
        self.errors = []
        self._generic_depth = 0
    
    def current_token(self):
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]
    
    def peek_token(self, offset=1):
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[pos]
    
    def advance(self):
        token = self.current_token()
        if not self.is_at_end():
            self.pos += 1
        return token
    
    def is_at_end(self):
        return self.current_token().type == TokenType.EOF
    
    def match(self, *types):
        return self.current_token().type in types
    
    def check(self, type_or_value):
        if isinstance(type_or_value, TokenType):
            return self.current_token().type == type_or_value
        return self.current_token().value == type_or_value
    
    def expect(self, token_type_or_value, message=""):
        if isinstance(token_type_or_value, TokenType):
            if self.current_token().type == token_type_or_value:
                return self.advance()
        else:
            if self.current_token().value == token_type_or_value:
                return self.advance()
        # 记录错误
        self.errors.append(f"期望 {message}，但找到 {self.current_token().value}")
        return self.advance()
    
    def _create_error(self, message):
        return f"错误: {message}"


class TestLexerGenericTokens:
    """测试泛型相关的词法分析"""
    
    def test_generic_keywords(self):
        """测试泛型关键字"""
        source = "泛型类型 泛型函数 类型 约束 其中"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        assert tokens[0].type == TokenType.GENERIC_TYPE
        assert tokens[1].type == TokenType.GENERIC_FUNC
        assert tokens[2].type == TokenType.TYPE_PARAM
        assert tokens[3].type == TokenType.CONSTRAINT
        assert tokens[4].type == TokenType.WHERE
    
    def test_angle_brackets(self):
        """测试尖括号"""
        source = "类型 列表<整数型>"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # 找到 < 和 > tokens
        lt_token = None
        gt_token = None
        for token in tokens:
            if token.type == TokenType.LT:
                lt_token = token
            elif token.type == TokenType.GT:
                gt_token = token
        
        assert lt_token is not None, "未找到 < token"
        assert gt_token is not None, "未找到 > token"


class TestTypeNode:
    """测试类型节点"""
    
    def test_simple_type(self):
        """测试简单类型"""
        node = TypeNode(type_name="整数型")
        
        assert node.type_name == "整数型"
        assert node.is_generic is False
        assert node.name == "整数型"
    
    def test_generic_type(self):
        """测试泛型类型"""
        inner_type = TypeNode(type_name="整数型")
        node = TypeNode(
            type_name="列表",
            is_generic=True,
            generic_args=[inner_type]
        )
        
        assert node.type_name == "列表"
        assert node.is_generic is True
        assert node.name == "列表<整数型>"
    
    def test_nested_generic_type(self):
        """测试嵌套泛型类型"""
        inner_type = TypeNode(type_name="整数型")
        middle_type = TypeNode(
            type_name="列表",
            is_generic=True,
            generic_args=[inner_type]
        )
        outer_type = TypeNode(
            type_name="映射",
            is_generic=True,
            generic_args=[
                TypeNode(type_name="字符串型"),
                middle_type
            ]
        )
        
        assert outer_type.name == "映射<字符串型, 列表<整数型>>"


class TestTypeParameterNode:
    """测试类型参数节点"""
    
    def test_simple_type_parameter(self):
        """测试简单类型参数"""
        node = TypeParameterNode(name="T")
        
        assert node.name == "T"
        assert node.variance.value == ""  # INVARIANT
        assert node.constraints == []
    
    def test_constrained_type_parameter(self):
        """测试带约束的类型参数"""
        node = TypeParameterNode(
            name="T",
            constraints=["可比较", "可打印"]
        )
        
        assert node.name == "T"
        assert "可比较" in node.constraints
        assert "可打印" in node.constraints
    
    def test_covariant_type_parameter(self):
        """测试协变类型参数"""
        from zhc.semantic.generics import Variance
        node = TypeParameterNode(
            name="T",
            variance=Variance.COVARIANT
        )
        
        assert node.name == "T"
        assert node.variance == Variance.COVARIANT
    
    def test_contravariant_type_parameter(self):
        """测试逆变类型参数"""
        from zhc.semantic.generics import Variance
        node = TypeParameterNode(
            name="T",
            variance=Variance.CONTRAVARIANT
        )
        
        assert node.name == "T"
        assert node.variance == Variance.CONTRAVARIANT
    
    def test_type_parameter_with_default(self):
        """测试带默认值的类型参数"""
        node = TypeParameterNode(
            name="T",
            default_type="整数型"
        )
        
        assert node.name == "T"
        assert node.default_type == "整数型"


class TestWhereClauseNode:
    """测试 Where 子句节点"""
    
    def test_where_clause(self):
        """测试 Where 子句"""
        constraints = [
            ("T", "可比较"),
            ("T", "可打印")
        ]
        node = WhereClauseNode(constraints=constraints)
        
        assert len(node.constraints) == 2
        assert node.constraints[0] == ("T", "可比较")


class TestGenericTypeDeclNode:
    """测试泛型类型声明节点"""
    
    def test_simple_generic_type(self):
        """测试简单泛型类型声明"""
        type_params = [
            TypeParameterNode(name="T")
        ]
        node = GenericTypeDeclNode(
            name="列表",
            type_params=type_params
        )
        
        assert node.name == "列表"
        assert len(node.type_params) == 1
        assert node.type_params[0].name == "T"
    
    def test_generic_type_to_generic_type(self):
        """测试转换为语义层 GenericType"""
        type_params = [
            TypeParameterNode(name="T")
        ]
        node = GenericTypeDeclNode(
            name="列表",
            type_params=type_params
        )
        
        generic_type = node.to_generic_type()
        
        assert generic_type.name == "列表"
        assert len(generic_type.type_params) == 1


class TestGenericFunctionDeclNode:
    """测试泛型函数声明节点"""
    
    def test_simple_generic_function(self):
        """测试简单泛型函数声明"""
        type_params = [
            TypeParameterNode(name="T")
        ]
        return_type = TypeNode(type_name="T")
        
        node = GenericFunctionDeclNode(
            name="最大值",
            type_params=type_params,
            return_type=return_type
        )
        
        assert node.name == "最大值"
        assert len(node.type_params) == 1
        assert node.return_type.type_name == "T"
    
    def test_constrained_generic_function(self):
        """测试带约束的泛型函数"""
        type_params = [
            TypeParameterNode(name="T", constraints=["可比较"])
        ]
        return_type = TypeNode(type_name="T")
        
        node = GenericFunctionDeclNode(
            name="最大值",
            type_params=type_params,
            return_type=return_type
        )
        
        assert node.type_params[0].constraints == ["可比较"]


class TestGenericParserIntegration:
    """测试泛型解析器集成"""
    
    def test_parse_generic_type_syntax(self):
        """测试解析泛型类型语法"""
        source = "列表<整数型>"
        parser = MockParser(source)
        
        # 手动解析
        assert parser.current_token().value == "列表"
        parser.advance()  # 列表
        
        assert parser.current_token().type == TokenType.LT
        parser.advance()  # <
        
        assert parser.current_token().type == TokenType.INT
        parser.advance()  # 整数型
        
        assert parser.current_token().type == TokenType.GT
        parser.advance()  # >
    
    def test_parse_type_parameter_list(self):
        """测试解析类型参数列表"""
        source = "<类型 K, 类型 V: 可比较>"
        parser = MockParser(source)
        
        parser.advance()  # <
        
        # 解析 K
        assert parser.current_token().value == "类型"
        parser.advance()
        assert parser.current_token().value == "K"
        parser.advance()
        
        # 逗号
        assert parser.current_token().value == ","
        parser.advance()
        
        # 解析 V: 可比较
        assert parser.current_token().value == "类型"
        parser.advance()
        assert parser.current_token().value == "V"
        parser.advance()
        
        # 冒号
        assert parser.current_token().value == ":"
        parser.advance()
        
        # 约束
        assert parser.current_token().value == "可比较"
        parser.advance()
        
        # >
        assert parser.current_token().type == TokenType.GT
    
    def test_parse_where_clause(self):
        """测试解析 Where 子句"""
        source = "其中 T: 可比较, 可打印"
        parser = MockParser(source)
        
        assert parser.current_token().type == TokenType.WHERE
        parser.advance()
        
        # T
        assert parser.current_token().value == "T"
        parser.advance()
        
        # :
        assert parser.current_token().value == ":"
        parser.advance()
        
        # 可比较
        assert parser.current_token().value == "可比较"
        parser.advance()
        
        # ,
        assert parser.current_token().value == ","
        parser.advance()
        
        # 可打印
        assert parser.current_token().value == "可打印"


class TestPredefinedConstraints:
    """测试预定义约束"""
    
    def test_comparable_constraint(self):
        """测试可比较约束"""
        from zhc.semantic.generics import PredefinedConstraints
        
        constraint = PredefinedConstraints.comparable()
        
        assert constraint.name == "可比较"
        assert len(constraint.required_operators) >= 3  # <, >, ==
    
    def test_addable_constraint(self):
        """测试可加约束"""
        from zhc.semantic.generics import PredefinedConstraints
        
        constraint = PredefinedConstraints.addable()
        
        assert constraint.name == "可加"
        assert len(constraint.required_operators) >= 1
    
    def test_numeric_constraint(self):
        """测试数值约束"""
        from zhc.semantic.generics import PredefinedConstraints
        
        constraint = PredefinedConstraints.numeric()
        
        assert constraint.name == "数值型"
        # 应该包含 +, -, *, /
        operators = {op.operator for op in constraint.required_operators}
        assert '+' in operators
        assert '-' in operators


class TestVariance:
    """测试类型变性"""
    
    def test_covariant(self):
        """测试协变"""
        from zhc.semantic.generics import Variance
        
        assert Variance.COVARIANT.value == "+"
    
    def test_contravariant(self):
        """测试逆变"""
        from zhc.semantic.generics import Variance
        
        assert Variance.CONTRAVARIANT.value == "-"
    
    def test_invariant(self):
        """测试不变"""
        from zhc.semantic.generics import Variance
        
        assert Variance.INVARIANT.value == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
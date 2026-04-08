#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试泛型解析器集成

验证 GenericParserMixin 是否正确集成到 Parser。
"""

import pytest
from zhc.parser.lexer import Lexer, TokenType
from zhc.parser.parser import Parser
from zhc.parser.ast_nodes import ASTNodeType


class TestGenericParserIntegration:
    """测试泛型解析器集成"""

    def test_generic_type_token_recognition(self):
        """测试泛型类型 Token 识别"""
        code = "泛型类型 列表<类型 T> { };"
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        # 检查是否有 GENERIC_TYPE token
        generic_type_tokens = [t for t in tokens if t.type == TokenType.GENERIC_TYPE]
        assert len(generic_type_tokens) >= 1, "应该识别到 '泛型类型' 关键字"

    def test_generic_func_token_recognition(self):
        """测试泛型函数 Token 识别"""
        code = "泛型函数 T 最大值<类型 T>(T a, T b) -> T { };"
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        # 检查是否有 GENERIC_FUNC token
        generic_func_tokens = [t for t in tokens if t.type == TokenType.GENERIC_FUNC]
        assert len(generic_func_tokens) >= 1, "应该识别到 '泛型函数' 关键字"

    def test_generic_type_declaration_parsing(self):
        """测试泛型类型声明解析"""
        code = """
        泛型类型 列表<类型 T> {
            T[] 数据;
            整数型 长度;
        };
        """
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        result = parser.parse_declaration()

        # 验证解析结果
        assert result is not None, "应该成功解析泛型类型声明"
        assert hasattr(result, 'name'), "应该有 name 属性"
        assert result.name == "列表", "类型名应该是 '列表'"
        assert hasattr(result, 'type_params'), "应该有 type_params 属性"
        assert len(result.type_params) == 1, "应该有 1 个类型参数"
        assert result.type_params[0].name == "T", "类型参数名应该是 'T'"

    def test_generic_function_declaration_parsing(self):
        """测试泛型函数声明解析"""
        code = """
        泛型函数 T 最大值<类型 T: 可比较>(T a, T b) -> T {
            返回 (a > b) ? a : b;
        }
        """
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        result = parser.parse_declaration()

        # 验证解析结果
        assert result is not None, "应该成功解析泛型函数声明"
        assert hasattr(result, 'name'), "应该有 name 属性"
        assert result.name == "最大值", "函数名应该是 '最大值'"
        assert hasattr(result, 'type_params'), "应该有 type_params 属性"
        assert len(result.type_params) == 1, "应该有 1 个类型参数"
        assert result.type_params[0].name == "T", "类型参数名应该是 'T'"
        # 检查约束
        assert len(result.type_params[0].constraints) >= 1, "应该有约束"

    def test_multiple_type_parameters(self):
        """测试多个类型参数"""
        code = """
        泛型类型 映射<类型 K, 类型 V> {
            K[] 键列表;
            V[] 值列表;
        };
        """
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        result = parser.parse_declaration()

        assert result is not None
        assert len(result.type_params) == 2, "应该有 2 个类型参数"
        assert result.type_params[0].name == "K"
        assert result.type_params[1].name == "V"

    def test_parser_has_generic_parser_mixin_methods(self):
        """测试 Parser 是否继承了 GenericParserMixin 的方法"""
        # 创建一个简单的 token 流
        code = "整数型 x;"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        # 检查是否有泛型解析方法
        assert hasattr(parser, 'parse_generic_type_declaration'), \
            "Parser 应该有 parse_generic_type_declaration 方法"
        assert hasattr(parser, 'parse_generic_function_declaration'), \
            "Parser 应该有 parse_generic_function_declaration 方法"
        assert hasattr(parser, 'parse_type_parameter_list'), \
            "Parser 应该有 parse_type_parameter_list 方法"
        assert hasattr(parser, 'parse_generic_type'), \
            "Parser 应该有 parse_generic_type 方法"

    def test_generic_depth_tracking(self):
        """测试泛型嵌套深度跟踪"""
        code = "整数型 x;"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        # 检查是否有泛型深度跟踪属性
        assert hasattr(parser, '_generic_depth'), \
            "Parser 应该有 _generic_depth 属性"
        assert parser._generic_depth == 0, "初始深度应该是 0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
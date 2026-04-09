#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宽字符类型测试

测试宽字符类型（wchar_t）的词法分析、语法分析和类型映射。

创建日期: 2026-04-10
最后更新: 2026-04-10
维护者: ZHC开发团队
"""

import pytest
from zhc.parser.lexer import Lexer, TokenType
from zhc.parser.parser import parse
from zhc.parser.ast_nodes import (
    WideCharLiteralNode,
    WideStringLiteralNode,
    ASTNodeType,
)
from zhc.backend.type_system import TypeMapper


class TestWideCharLexer:
    """宽字符词法分析测试"""

    def test_wide_char_literal_with_L_prefix(self):
        """测试 L'中' 格式的宽字符字面量"""
        lexer = Lexer("L'中'")
        tokens = lexer.tokenize()
        assert len(tokens) == 2  # WIDE_CHAR_LITERAL + EOF
        assert tokens[0].type == TokenType.WIDE_CHAR_LITERAL
        assert tokens[0].value == 20013  # '中' 的 Unicode 码点

    def test_wide_char_literal_with_chinese_prefix(self):
        """测试 宽'中' 格式的宽字符字面量"""
        lexer = Lexer("宽'中'")
        tokens = lexer.tokenize()
        assert len(tokens) == 2
        assert tokens[0].type == TokenType.WIDE_CHAR_LITERAL
        assert tokens[0].value == 20013

    def test_wide_string_literal_with_L_prefix(self):
        """测试 L"你好" 格式的宽字符串字面量"""
        lexer = Lexer('L"你好"')
        tokens = lexer.tokenize()
        assert len(tokens) == 2
        assert tokens[0].type == TokenType.WIDE_STRING_LITERAL
        assert tokens[0].value == [20320, 22909]  # '你' 和 '好' 的 Unicode 码点

    def test_wide_string_literal_with_chinese_prefix(self):
        """测试 宽"你好" 格式的宽字符串字面量"""
        lexer = Lexer('宽"你好"')
        tokens = lexer.tokenize()
        assert len(tokens) == 2
        assert tokens[0].type == TokenType.WIDE_STRING_LITERAL
        assert tokens[0].value == [20320, 22909]

    def test_wide_char_with_escape_sequences(self):
        """测试宽字符中的转义序列"""
        lexer = Lexer("L'\\n'")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.WIDE_CHAR_LITERAL
        assert tokens[0].value == ord("\n")

    def test_wide_string_with_escape_sequences(self):
        """测试宽字符串中的转义序列"""
        lexer = Lexer('L"你好\\n世界"')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.WIDE_STRING_LITERAL
        expected = [20320, 22909, ord("\n"), 19990, 30028]
        assert tokens[0].value == expected

    def test_wide_char_unicode_escape(self):
        """测试宽字符中的 Unicode 转义"""
        lexer = Lexer("L'\\u4e2d'")  # \u4e2d = '中'
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.WIDE_CHAR_LITERAL
        assert tokens[0].value == 20013


class TestWideCharParser:
    """宽字符语法分析测试"""

    def test_parse_wide_char_literal(self):
        """测试解析宽字符字面量"""
        ast, errors = parse("L'中'")
        assert len(errors) == 0
        # 检查 AST 中是否包含宽字符字面量节点
        # 注意：实际 AST 结构取决于 parser 的实现

    def test_parse_wide_string_literal(self):
        """测试解析宽字符串字面量"""
        ast, errors = parse('L"你好"')
        assert len(errors) == 0


class TestWideCharTypeMapping:
    """宽字符类型映射测试"""

    def test_wide_char_type_in_type_system(self):
        """测试宽字符类型在类型系统中的映射"""
        type_mapper = TypeMapper()

        # 检查宽字符类型映射
        assert "宽字符型" in type_mapper.ZHC_TO_C
        assert type_mapper.ZHC_TO_C["宽字符型"] == "wchar_t"

        # 检查宽字符串类型映射
        assert "宽字符串型" in type_mapper.ZHC_TO_C
        assert type_mapper.ZHC_TO_C["宽字符串型"] == "wchar_t*"

    def test_wide_char_llvm_type(self):
        """测试宽字符的 LLVM 类型映射"""
        type_mapper = TypeMapper()

        # 宽字符类型应该是 32 位整数（UTF-32）
        llvm_type = type_mapper.to_llvm("宽字符型")
        assert llvm_type is not None
        # 宽字符在 Linux/macOS 上是 32 位
        assert str(llvm_type) == "i32"

    def test_wide_string_llvm_type(self):
        """测试宽字符串的 LLVM 类型映射"""
        type_mapper = TypeMapper()

        # 宽字符串类型应该是指向 32 位整数的指针
        llvm_type = type_mapper.to_llvm("宽字符串型")
        assert llvm_type is not None
        # 应该是 i32*
        assert "i32" in str(llvm_type)


class TestWideCharKeywords:
    """宽字符关键字测试"""

    def test_wide_char_keyword_in_keywords(self):
        """测试宽字符关键字是否在关键字映射中"""
        from zhc.keywords import M

        assert "宽字符型" in M
        assert M["宽字符型"] == "wchar_t"

        assert "宽字符串型" in M
        assert M["宽字符串型"] == "wchar_t*"


class TestWideCharASTNodes:
    """宽字符 AST 节点测试"""

    def test_wide_char_literal_node(self):
        """测试宽字符字面量节点"""
        node = WideCharLiteralNode("中", 20013, 1, 1)
        assert node.node_type == ASTNodeType.WIDE_CHAR_LITERAL
        assert node.char_value == "中"
        assert node.unicode_codepoint == 20013

    def test_wide_string_literal_node(self):
        """测试宽字符串字面量节点"""
        node = WideStringLiteralNode("你好", [20320, 22909], 1, 1)
        assert node.node_type == ASTNodeType.WIDE_STRING_LITERAL
        assert node.string_value == "你好"
        assert node.unicode_codepoints == [20320, 22909]

    def test_wide_char_literal_node_hash(self):
        """测试宽字符字面量节点的哈希"""
        node1 = WideCharLiteralNode("中", 20013, 1, 1)
        node2 = WideCharLiteralNode("中", 20013, 2, 2)
        # 相同内容的节点应该有相同的哈希
        assert node1.get_hash() == node2.get_hash()

    def test_wide_string_literal_node_hash(self):
        """测试宽字符串字面量节点的哈希"""
        node1 = WideStringLiteralNode("你好", [20320, 22909], 1, 1)
        node2 = WideStringLiteralNode("你好", [20320, 22909], 2, 2)
        # 相同内容的节点应该有相同的哈希
        assert node1.get_hash() == node2.get_hash()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

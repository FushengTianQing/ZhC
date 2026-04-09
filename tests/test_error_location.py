#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确错误定位功能测试

测试内容：
1. Token 位置信息增强
2. AST 节点位置信息增强
3. 多行错误上下文提取
4. 错误格式化器指针高亮

创建日期: 2026-04-10
"""

import pytest
from zhc.errors import (
    SourceLocation,
    ZHCError,
    ErrorCollection,
    SourceContextExtractor,
    MultilineSourceContext,
    ErrorFormatter,
)
from zhc.parser.lexer import Token, TokenType


class TestTokenLocation:
    """Token 位置信息测试"""

    def test_token_basic_location(self):
        """测试 Token 基本位置信息"""
        token = Token(TokenType.INT_LITERAL, "42", 10, 5)
        assert token.line == 10
        assert token.column == 5
        assert token.end_column == 7  # column + len("42")

    def test_token_multiline_location(self):
        """测试多行 Token 位置信息"""
        token = Token(
            TokenType.STRING_LITERAL,
            "hello\nworld",
            10,
            5,
            end_line=11,
            end_column=6,
        )
        assert token.line == 10
        assert token.column == 5
        assert token.end_line == 11
        assert token.end_column == 6
        assert token.is_multiline()

    def test_token_get_length(self):
        """测试 Token 长度计算"""
        token = Token(TokenType.IDENTIFIER, "计数器", 10, 5)
        assert token.get_length() == 3

    def test_token_to_source_location(self):
        """测试 Token 转换为 SourceLocation"""
        token = Token(TokenType.INT_LITERAL, "42", 10, 5)
        loc = token.to_source_location("test.zhc")
        assert loc.file_path == "test.zhc"
        assert loc.line == 10
        assert loc.column == 5
        assert loc.token_text == "42"


class TestSourceLocation:
    """SourceLocation 测试"""

    def test_basic_location(self):
        """测试基本位置"""
        loc = SourceLocation("test.zhc", 10, 5)
        assert str(loc) == "test.zhc:10:5"

    def test_range_location(self):
        """测试范围位置"""
        loc = SourceLocation("test.zhc", 10, 5, 10, 15, "计数器")
        assert loc.is_multiline() == False
        assert loc.get_length() == 10

    def test_multiline_location(self):
        """测试多行位置"""
        loc = SourceLocation("test.zhc", 10, 5, 15, 10)
        assert loc.is_multiline() == True
        assert loc.get_length() == -1

    def test_get_range(self):
        """测试获取范围"""
        loc = SourceLocation("test.zhc", 10, 5, 15, 10)
        assert loc.get_range() == (10, 5, 15, 10)

    def test_to_dict(self):
        """测试转换为字典"""
        loc = SourceLocation("test.zhc", 10, 5, 15, 10, "计数器")
        d = loc.to_dict()
        assert d["file_path"] == "test.zhc"
        assert d["line"] == 10
        assert d["column"] == 5
        assert d["end_line"] == 15
        assert d["end_column"] == 10
        assert d["token_text"] == "计数器"


class TestSourceContextExtractor:
    """源码上下文提取器测试"""

    def test_get_line(self):
        """测试获取单行"""
        source = "第一行\n第二行\n第三行"
        extractor = SourceContextExtractor({"test.zhc": source})
        assert extractor.get_line("test.zhc", 1) == "第一行"
        assert extractor.get_line("test.zhc", 2) == "第二行"
        assert extractor.get_line("test.zhc", 3) == "第三行"

    def test_get_context(self):
        """测试获取上下文"""
        source = "第一行\n第二行\n第三行\n第四行\n第五行"
        extractor = SourceContextExtractor({"test.zhc": source})
        loc = SourceLocation("test.zhc", 3, 2)
        context = extractor.get_context(loc, context_lines=1)
        assert context.line == 3
        assert context.source_line == "第三行"

    def test_get_multiline_context(self):
        """测试获取多行上下文"""
        source = "第一行\n第二行\n第三行\n第四行\n第五行"
        extractor = SourceContextExtractor({"test.zhc": source})
        loc = SourceLocation("test.zhc", 2, 5, 4, 10)
        context = extractor.get_multiline_context(loc, context_lines=1)
        assert context.start_line == 2
        assert context.end_line == 4
        assert len(context.lines) > 0

    def test_highlight_range(self):
        """测试高亮范围"""
        extractor = SourceContextExtractor()
        line = "整数型 计数器 = 0;"
        result = extractor.highlight_range(line, 5, 12)
        assert "^" in result

    def test_get_snippet(self):
        """测试获取代码片段"""
        source = "第一行\n第二行\n第三行\n第四行\n第五行"
        extractor = SourceContextExtractor({"test.zhc": source})
        snippet = extractor.get_snippet("test.zhc", 2, 4)
        # get_snippet 返回 [start_line, end_line) 范围，包含 start 到 end
        assert len(snippet) == 3  # 第2、3、4行
        assert snippet[0] == "第二行"
        assert snippet[1] == "第三行"
        assert snippet[2] == "第四行"


class TestMultilineSourceContext:
    """多行源码上下文测试"""

    def test_format_multiline_context(self):
        """测试格式化多行上下文"""
        context = MultilineSourceContext(
            file_path="test.zhc",
            start_line=2,
            start_column=5,
            end_line=4,
            end_column=10,
            lines=[
                ("第一行", 1),
                ("第二行", 2),
                ("第三行", 3),
                ("第四行", 4),
                ("第五行", 5),
            ],
        )
        # 修正：lines 应该是 LineInfo 对象列表
        from zhc.errors.source_context import LineInfo

        context = MultilineSourceContext(
            file_path="test.zhc",
            start_line=2,
            start_column=5,
            end_line=4,
            end_column=10,
            lines=[
                LineInfo(1, "第一行"),
                LineInfo(2, "第二行"),
                LineInfo(3, "第三行"),
                LineInfo(4, "第四行"),
                LineInfo(5, "第五行"),
            ],
        )
        formatted = context.get_formatted_context()
        assert "第二行" in formatted
        assert "第四行" in formatted


class TestErrorFormatter:
    """错误格式化器测试"""

    def test_format_basic_error(self):
        """测试格式化基本错误"""
        formatter = ErrorFormatter(color_output=False)
        error = ZHCError("未定义的变量", error_code="E001")
        result = formatter.format_error(error)
        assert "错误[E001]" in result
        assert "未定义的变量" in result

    def test_format_error_with_location(self):
        """测试格式化带位置的错误"""
        formatter = ErrorFormatter(color_output=False)
        loc = SourceLocation("test.zhc", 10, 5)
        error = ZHCError("未定义的变量", location=loc, error_code="E001")
        result = formatter.format_error(error)
        assert "test.zhc:10:5" in result

    def test_format_error_with_context(self):
        """测试格式化带上下文的错误"""
        formatter = ErrorFormatter(color_output=False)
        source = "整数型 x = 1;\n整数型 y = 计数器 + 1;"
        extractor = SourceContextExtractor({"test.zhc": source})
        loc = SourceLocation("test.zhc", 2, 12, token_text="计数器")
        context = extractor.get_context(loc)
        error = ZHCError("未定义的变量 '计数器'", location=loc, error_code="E001")
        result = formatter.format_error(error, context)
        assert "计数器" in result

    def test_format_multiline_error(self):
        """测试格式化多行错误"""
        formatter = ErrorFormatter(color_output=False)
        source = "整数型 x = (\n    1 + 2\n);"
        extractor = SourceContextExtractor({"test.zhc": source})
        loc = SourceLocation("test.zhc", 1, 12, 3, 2)
        context = extractor.get_multiline_context(loc)
        error = ZHCError("括号未闭合", location=loc, error_code="P001")
        result = formatter.format_multiline_error(error, context)
        assert "1:12-3:2" in result or "1-3" in result

    def test_format_error_collection(self):
        """测试格式化错误集合"""
        formatter = ErrorFormatter(color_output=False)
        errors = ErrorCollection()
        errors.add(ZHCError("错误1", error_code="E001"))
        errors.add(ZHCError("错误2", error_code="E002"))
        result = formatter.format_error_collection(errors)
        assert "错误1" in result
        assert "错误2" in result
        assert "2 个错误" in result


class TestErrorCollection:
    """错误集合测试"""

    def test_add_errors(self):
        """测试添加错误"""
        errors = ErrorCollection()
        errors.add(ZHCError("错误1", error_code="E001"))
        errors.add(ZHCError("错误2", severity=ZHCError.SEVERITY_WARNING))
        assert errors.error_count() == 1
        assert errors.warning_count() == 1

    def test_summary(self):
        """测试摘要"""
        errors = ErrorCollection()
        errors.add(ZHCError("错误1", error_code="E001"))
        errors.add(ZHCError("警告1", severity=ZHCError.SEVERITY_WARNING))
        summary = errors.summary()
        assert "1 个错误" in summary
        assert "1 个警告" in summary

    def test_to_dict(self):
        """测试转换为字典"""
        errors = ErrorCollection()
        errors.add(ZHCError("错误1", error_code="E001"))
        d = errors.to_dict()
        assert d["counts"]["errors"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

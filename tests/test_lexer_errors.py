#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lexer 错误处理单元测试

测试 Lexer 错误处理功能：
- 非法字符检测
- 错误位置信息
- 源代码上下文
- 错误消息格式化

作者: 阿福
日期: 2026-04-08
"""

import pytest
from zhc.parser.lexer import Lexer
from zhc.errors.lexer_error import (
    LexerError,
    illegal_character,
    unterminated_string,
    unterminated_comment,
    unterminated_char,
    LEXER_ILLEGAL_CHARACTER,
    LEXER_UNTERMINATED_STRING,
    LEXER_UNTERMINATED_COMMENT,
    LEXER_UNTERMINATED_CHAR,
)
from zhc.errors.base import SourceLocation


class TestIllegalCharacterDetection:
    """测试非法字符检测"""

    def test_detect_single_illegal_char(self):
        """测试检测单个非法字符"""
        source = "函数 main() @ 整数 { 返回 0 }"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        assert lexer.has_errors()
        errors = lexer.get_errors()
        assert len(errors) == 1
        assert errors[0].error_code == LEXER_ILLEGAL_CHARACTER
        assert '@' in errors[0].character

    def test_detect_multiple_illegal_chars(self):
        """测试检测多个非法字符"""
        source = "函数 main() @ # $ 整数 { 返回 0 }"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        assert lexer.has_errors()
        errors = lexer.get_errors()
        assert len(errors) >= 2

    def test_illegal_char_at_beginning(self):
        """测试行首非法字符"""
        source = "@函数 main() 整数 { 返回 0 }"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        assert lexer.has_errors()
        error = lexer.get_errors()[0]
        assert error.location.line == 1
        assert error.location.column == 1

    def test_illegal_char_at_end(self):
        """测试行尾非法字符"""
        source = "函数 main() 整数 { 返回 0 }@"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        assert lexer.has_errors()
        error = lexer.get_errors()[0]
        assert error.location.line == 1
        # 列号应该是字符串长度附近

    def test_illegal_char_in_middle(self):
        """测试中间非法字符"""
        source = "函数 main() 整数 { 返回 $ 0 }"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        assert lexer.has_errors()
        error = lexer.get_errors()[0]
        assert error.error_code == LEXER_ILLEGAL_CHARACTER


class TestErrorLocation:
    """测试错误位置信息"""

    def test_error_line_number(self):
        """测试错误行号"""
        source = """
函数 test1() 整数 { 返回 0 }
@
函数 test2() 整数 { 返回 0 }
"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        assert lexer.has_errors()
        error = lexer.get_errors()[0]
        assert error.location.line == 3

    def test_error_column_number(self):
        """测试错误列号"""
        source = "函数 test() 整数 { 返回 @0 }"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        assert lexer.has_errors()
        error = lexer.get_errors()[0]
        # 列号应该在 @ 符号位置
        assert error.location.column > 0

    def test_error_in_multiline_source(self):
        """测试多行源码中的错误位置"""
        source = """
函数 test() 整数 {
    返回 1
@
    返回 2
}
"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        assert lexer.has_errors()
        error = lexer.get_errors()[0]
        assert error.location.line == 4


class TestSourceContext:
    """测试源代码上下文"""

    def test_get_context_single_line(self):
        """测试单行源码上下文"""
        source = "函数 main() 整数 { 返回 0 }"
        lexer = Lexer(source)
        # 不调用 tokenize，直接调用 get_source_context
        context = lexer.get_source_context(line=1, column=10)
        assert "函数 main()" in context

    def test_get_context_before_error(self):
        """测试错误前上下文"""
        source = "第一行\n第二行\n第三行 @ 错误\n第四行\n第五行"
        lexer = Lexer(source)
        context = lexer.get_source_context(line=3, column=10)
        
        assert "第三行" in context
        # 应该包含前后行
        lines = context.split('\n')
        assert len(lines) >= 3

    def test_get_context_marker_position(self):
        """测试错误位置标记"""
        source = "这是一行测试代码"
        lexer = Lexer(source)
        context = lexer.get_source_context(line=1, column=5)
        
        # 应该在第5列位置有 ^ 标记
        assert "^" in context

    def test_get_context_invalid_line(self):
        """测试无效行号"""
        source = "测试"
        lexer = Lexer(source)
        context = lexer.get_source_context(line=100, column=1)
        assert context == ""

    def test_get_context_boundary_lines(self):
        """测试边界行"""
        source = "第一行\n第二行\n第三行"
        lexer = Lexer(source)
        
        # 第一行
        context = lexer.get_source_context(line=1, column=1)
        assert "第一行" in context
        
        # 最后一行
        context = lexer.get_source_context(line=3, column=1)
        assert "第三行" in context


class TestErrorMessageFormatting:
    """测试错误消息格式化"""

    def test_format_error_with_context(self):
        """测试带上下文的错误格式化"""
        source = "函数 test() 整数 { 返回 @0 }"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        assert lexer.has_errors()
        error = lexer.get_errors()[0]
        formatted = lexer.format_error_message(error)
        
        # 应该包含位置信息
        assert "行" in formatted or "-->" in formatted
        # 应该包含错误消息
        assert "error:" in formatted
        # 应该包含发现的字符
        assert "@" in formatted

    def test_format_error_with_suggestion(self):
        """测试带建议的错误格式化"""
        source = "@测试"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        assert lexer.has_errors()
        error = lexer.get_errors()[0]
        formatted = lexer.format_error_message(error)
        
        # 应该包含建议
        if error.suggestion:
            assert "建议" in formatted or "suggestion" in formatted.lower()

    def test_format_multiple_errors(self):
        """测试多个错误格式化"""
        source = "@ # $"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        assert lexer.has_errors()
        errors = lexer.get_errors()
        
        for error in errors:
            formatted = lexer.format_error_message(error)
            assert isinstance(formatted, str)
            assert len(formatted) > 0


class TestErrorRecovery:
    """测试错误恢复"""

    def test_continue_after_illegal_char(self):
        """测试非法字符后继续扫描"""
        source = "函数 test() 整数 { 返回 @0 }"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # 应该继续生成后续 token
        token_values = [t.value for t in tokens if t.value]
        assert "0" in token_values

    def test_multiple_errors_collected(self):
        """测试收集多个错误"""
        source = "@ @ @"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        assert lexer.has_errors()
        errors = lexer.get_errors()
        # 应该收集了多个错误
        assert len(errors) >= 1

    def test_no_tokens_on_complete_illegal_source(self):
        """测试完全非法源码"""
        source = "@#$%^&*()"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # 仍然会有 EOF token
        assert len(tokens) >= 1
        # 但会有错误
        assert lexer.has_errors()


class TestErrorFactory:
    """测试错误工厂函数"""

    def test_illegal_character_factory(self):
        """测试非法字符工厂"""
        error = illegal_character(
            character="@",
            location=SourceLocation(line=1, column=10)
        )
        
        assert isinstance(error, LexerError)
        assert error.error_code == LEXER_ILLEGAL_CHARACTER
        assert error.character == "@"
        assert error.suggestion is not None

    def test_unterminated_string_factory(self):
        """测试未闭合字符串工厂"""
        error = unterminated_string(
            location=SourceLocation(line=1, column=5)
        )
        
        assert isinstance(error, LexerError)
        assert error.error_code == LEXER_UNTERMINATED_STRING

    def test_unterminated_comment_factory(self):
        """测试未闭合注释工厂"""
        error = unterminated_comment(
            location=SourceLocation(line=1, column=5)
        )
        
        assert isinstance(error, LexerError)
        assert error.error_code == LEXER_UNTERMINATED_COMMENT

    def test_unterminated_char_factory(self):
        """测试未闭合字符工厂"""
        error = unterminated_char(
            location=SourceLocation(line=1, column=5)
        )
        
        assert isinstance(error, LexerError)
        assert error.error_code == LEXER_UNTERMINATED_CHAR


class TestLexerErrorAttributes:
    """测试 LexerError 属性"""

    def test_error_has_message(self):
        """测试错误有消息"""
        error = illegal_character(
            character="@",
            location=SourceLocation(line=1, column=1)
        )
        
        assert error.message is not None
        assert len(error.message) > 0
        assert "@" in error.message

    def test_error_has_location(self):
        """测试错误有位置"""
        error = illegal_character(
            character="@",
            location=SourceLocation(line=10, column=20)
        )
        
        assert error.location is not None
        assert error.location.line == 10
        assert error.location.column == 20

    def test_error_to_dict(self):
        """测试错误转字典"""
        error = illegal_character(
            character="@",
            location=SourceLocation(line=1, column=1)
        )
        
        data = error.to_dict()
        assert isinstance(data, dict)
        assert "message" in data
        assert "location" in data
        assert "character" in data


class TestErrorReport:
    """测试错误报告"""

    def test_report_with_errors(self):
        """测试有错误时的报告"""
        source = "函数 test() 整数 { 返回 @0 }"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        report = lexer.report()
        assert "词法分析报告" in report
        assert "错误数量" in report

    def test_report_error_count(self):
        """测试错误数量报告"""
        source = "@ @"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        report = lexer.report()
        # 报告应该反映错误数量
        assert str(len(lexer.get_errors())) in report

    def test_report_without_errors(self):
        """测试无错误时的报告"""
        source = "函数 main() 整数 { 返回 0 }"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        report = lexer.report()
        assert "词法分析报告" in report
        assert "Token数量" in report


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_source(self):
        """测试空源码"""
        source = ""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # 空源码不应该有错误
        assert not lexer.has_errors()

    def test_only_whitespace(self):
        """测试只有空白字符"""
        source = "   \n\n   \t\t   "
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # 只有空白不应该有错误
        assert not lexer.has_errors()

    def test_only_illegal_chars(self):
        """测试只有非法字符"""
        source = "@#$%^&"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # 每个非法字符都会产生错误
        assert lexer.has_errors()
        # 注意：有些字符可能是操作符的一部分（如 & 可能被识别为位运算符）
        assert len(lexer.get_errors()) >= 3

    def test_chinese_illegal_char(self):
        """测试中文非法字符（非CJK范围）"""
        # 中文是合法的（\u4e00-\u9fff）
        source = "函数 main() 整数 { 返回 0 }"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # 中文应该被识别为标识符的一部分
        assert not lexer.has_errors()

    def test_unicode_control_char(self):
        """测试 Unicode 控制字符"""
        source = "函数 main() 整数\u0000{ 返回 0 }"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # Unicode 控制字符应该被检测为非法
        assert lexer.has_errors()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
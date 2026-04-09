#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试转义序列功能：\\x 十六进制、\\e ANSI、\\NNN 八进制
"""

from zhc.parser.lexer import Lexer


# ============= \x 十六进制转义测试 =============


def test_basic_hex_escape():
    """测试基本十六进制转义"""
    lexer = Lexer(r'字符串型 s = "\x41\x42\x43";')
    tokens = lexer.tokenize()

    string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
    assert len(string_tokens) == 1
    token = string_tokens[0]
    assert token.value == "ABC"
    print(f"✓ \\x 基础转义: {repr(token.value)}")


def test_hex_escape_continuation():
    """测试转义序列的延续"""
    lexer = Lexer(r'字符串型 s = "\x41BCD";')
    tokens = lexer.tokenize()
    string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
    assert string_tokens[0].value == "ABCD"
    print(f"✓ \\x 转义延续: {repr(string_tokens[0].value)}")


# ============= \\e ANSI ESC 转义测试 =============


def test_ansi_escape_e():
    """测试 \\e 转义（ESC 字符）"""
    lexer = Lexer(r'字符串型 s = "\e[31m红色\e[0m";')
    tokens = lexer.tokenize()
    string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
    assert len(string_tokens) == 1
    token = string_tokens[0]
    # \e[31m 应该被转换为 \x1B[31m
    expected = "\x1b[31m红色\x1b[0m"
    assert token.value == expected, f"期望 {repr(expected)}，实际 {repr(token.value)}"
    print(f"✓ \\e ANSI 转义: {repr(token.value)}")


def test_ansi_escape_E_uppercase():
    """测试 \\E 转义（大写）"""
    lexer = Lexer(r'字符串型 s = "\E[32m绿色";')
    tokens = lexer.tokenize()
    string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
    assert len(string_tokens) == 1
    assert string_tokens[0].value == "\x1b[32m绿色"
    print(f"✓ \\E ANSI 转义: {repr(string_tokens[0].value)}")


def test_ansi_colorful_output():
    """测试彩色输出字符串"""
    lexer = Lexer(r'字符串型 s = "\e[1;31;40m红字黑底\e[0m";')
    tokens = lexer.tokenize()
    string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
    assert string_tokens[0].value == "\x1b[1;31;40m红字黑底\x1b[0m"
    print(f"✓ ANSI 彩色输出: {repr(string_tokens[0].value)}")


# ============= \\NNN 八进制转义测试 =============


def test_octal_escape():
    """测试八进制转义"""
    # \101 = 1*64 + 0*8 + 1 = 65 = 'A'
    lexer = Lexer(r'字符串型 s = "\101\102\103";')
    tokens = lexer.tokenize()
    string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
    assert string_tokens[0].value == "ABC"
    print(f"✓ \\NNN 八进制转义: {repr(string_tokens[0].value)}")


def test_octal_escape_single_digit():
    """测试单个八进制数字"""
    lexer = Lexer(r'字符串型 s = "\0\7\12";')
    tokens = lexer.tokenize()
    string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
    # \0 = 0, \7 = 7, \12 = 10
    expected = "\x00\x07\x0a"
    assert string_tokens[0].value == expected
    print(f"✓ 八进制单数字: {repr(string_tokens[0].value)}")


def test_octal_escape_max():
    """测试八进制最大值 \\377"""
    lexer = Lexer(r'字符串型 s = "\377";')  # 0xFF = 255
    tokens = lexer.tokenize()
    string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
    assert string_tokens[0].value == "\xff"
    print(f"✓ 八进制最大值 \\377: {repr(string_tokens[0].value)}")


def test_octal_escape_boundary():
    """测试八进制边界情况"""
    lexer = Lexer(r'字符串型 s = "\7";')  # 响铃字符
    tokens = lexer.tokenize()
    string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
    assert string_tokens[0].value == "\a"
    print(f"✓ 八进制边界 \\7: {repr(string_tokens[0].value)}")


# ============= 混合测试 =============


def test_mixed_escapes():
    """测试混合转义序列"""
    lexer = Lexer(r'字符串型 s = "\x1B[31mError:\x1B[0m \101\102\103";')
    tokens = lexer.tokenize()
    string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
    expected = "\x1b[31mError:\x1b[0m ABC"
    assert string_tokens[0].value == expected
    print(f"✓ 混合转义: {repr(string_tokens[0].value)}")


def test_regression_hex_still_works():
    """回归测试：\\x 仍然正常工作"""
    lexer = Lexer(r'字符串型 s = "\x48\x65\x6C\x6C\x6F";')
    tokens = lexer.tokenize()
    string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
    assert string_tokens[0].value == "Hello"
    print(f"✓ \\x 回归测试: {repr(string_tokens[0].value)}")


def test_regression_standard_escapes():
    """回归测试：标准转义仍然正常"""
    lexer = Lexer(r'字符串型 s = "\n\t\0\\\"\a\b\f\v\r";')
    tokens = lexer.tokenize()
    string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
    expected = '\n\t\0\\"\a\b\f\v\r'
    assert string_tokens[0].value == expected
    print(f"✓ 标准转义回归: {repr(string_tokens[0].value)}")


if __name__ == "__main__":
    print("=" * 60)
    print("测试转义序列功能")
    print("=" * 60)
    print()

    print("【\\x 十六进制转义测试】")
    test_basic_hex_escape()
    test_hex_escape_continuation()
    print()

    print("【\\e ANSI ESC 转义测试】")
    test_ansi_escape_e()
    test_ansi_escape_E_uppercase()
    test_ansi_colorful_output()
    print()

    print("【\\NNN 八进制转义测试】")
    test_octal_escape()
    test_octal_escape_single_digit()
    test_octal_escape_max()
    test_octal_escape_boundary()
    print()

    print("【混合测试】")
    test_mixed_escapes()
    test_regression_hex_still_works()
    test_regression_standard_escapes()
    print()

    print("=" * 60)
    print("所有测试通过！✓")
    print("=" * 60)

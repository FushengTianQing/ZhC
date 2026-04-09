#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 UTF-8 字符串处理功能

根据 P0-字符编码-UTF-8字符串处理.md 规划文档编写测试用例。
"""

import pytest
from zhc.parser.lexer import Lexer
from zhc.utils.file_utils import read_source_file, SourceFileError


class TestUTF8StringParsing:
    """测试 UTF-8 字符串解析"""

    def test_chinese_string_literal(self):
        """测试中文字符串字面量"""
        code = '字符串型 s = "你好，世界！";'
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "你好，世界！"
        assert len(string_tokens[0].value) == 6  # 6个中文字符

    def test_mixed_chinese_english_string(self):
        """测试中英文混合字符串"""
        code = '字符串型 s = "Hello 你好 World 世界";'
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "Hello 你好 World 世界"
        assert len(string_tokens[0].value) == 17  # 5+1+2+1+5+1+2 = 17个字符

    def test_emoji_string(self):
        """测试 emoji 字符串"""
        code = '字符串型 s = "表情符号 😀 🎉 🚀";'
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "表情符号 😀 🎉 🚀"
        # emoji 是 4 字节 UTF-8 字符
        assert "😀" in string_tokens[0].value
        assert "🎉" in string_tokens[0].value

    def test_chinese_char_literal(self):
        """测试中文字符字面量"""
        code = "字符型 c = '中';"
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        char_tokens = [t for t in tokens if t.type.name == "CHAR_LITERAL"]
        assert len(char_tokens) == 1
        assert char_tokens[0].value == "中"

    def test_empty_string(self):
        """测试空字符串"""
        code = '字符串型 s = "";'
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == ""

    def test_single_chinese_char(self):
        """测试单个中文字符"""
        code = '字符串型 s = "中";'
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "中"
        assert len(string_tokens[0].value) == 1

    def test_long_chinese_text(self):
        """测试长中文文本"""
        code = '字符串型 s = "这是一段很长的中文文字，用于测试 UTF-8 处理能力。";'
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert "UTF-8" in string_tokens[0].value
        assert "中文" in string_tokens[0].value

    def test_special_characters(self):
        """测试特殊字符"""
        code = '字符串型 s = "特殊字符：© ® ™ € £ ¥";'
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert "©" in string_tokens[0].value
        assert "€" in string_tokens[0].value


class TestSourceFileReading:
    """测试源文件读取"""

    def test_read_utf8_file(self, tmp_path):
        """测试读取 UTF-8 文件"""
        # 创建测试文件
        test_file = tmp_path / "test_utf8.zhc"
        test_file.write_text(
            "// UTF-8 源代码文件\n"
            "整数型 主函数() {\n"
            '    字符串型 消息 = "你好，世界！";\n'
            '    打印("%s\\n", 消息);\n'
            "    返回 0;\n"
            "}\n",
            encoding="utf-8",
        )

        # 读取文件
        content = read_source_file(test_file)
        assert "你好，世界！" in content
        assert "整数型" in content

    def test_read_utf8_file_with_bom(self, tmp_path):
        """测试读取带 BOM 的 UTF-8 文件"""
        # 创建带 BOM 的测试文件
        test_file = tmp_path / "test_bom.zhc"
        with open(test_file, "wb") as f:
            f.write(b"\xef\xbb\xbf")  # UTF-8 BOM
            f.write("// 带BOM的源代码\n".encode("utf-8"))
            f.write('字符串型 s = "测试";\n'.encode("utf-8"))

        # 读取文件（BOM 应该被自动移除）
        content = read_source_file(test_file)
        assert "测试" in content
        # BOM 应该被移除，所以内容不应该以 BOM 开头
        assert not content.startswith("\ufeff")

    def test_read_invalid_encoding_file(self, tmp_path):
        """测试读取无效编码文件"""
        # 创建无效编码的测试文件
        test_file = tmp_path / "test_invalid.zhc"
        with open(test_file, "wb") as f:
            f.write(b"\xff\xfe")  # 无效 UTF-8 序列

        # 读取文件应该抛出异常
        with pytest.raises(SourceFileError) as exc_info:
            read_source_file(test_file)
        assert "编码错误" in str(exc_info.value)


class TestUTF8Identifier:
    """测试 UTF-8 标识符"""

    def test_chinese_identifier(self):
        """测试中文标识符"""
        code = "整数型 变量名 = 10;"
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        # 检查标识符
        identifier_tokens = [t for t in tokens if t.type.name == "IDENTIFIER"]
        assert len(identifier_tokens) == 1
        assert identifier_tokens[0].value == "变量名"

    def test_mixed_identifier(self):
        """测试中英文混合标识符"""
        code = "整数型 my变量 = 10;"
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        identifier_tokens = [t for t in tokens if t.type.name == "IDENTIFIER"]
        assert len(identifier_tokens) == 1
        assert identifier_tokens[0].value == "my变量"

    def test_chinese_function_name(self):
        """测试中文函数名"""
        code = "函数 打印消息() { 返回 0; }"
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        identifier_tokens = [t for t in tokens if t.type.name == "IDENTIFIER"]
        assert len(identifier_tokens) == 1
        assert identifier_tokens[0].value == "打印消息"


class TestUTF8EscapeSequences:
    """测试 UTF-8 转义序列"""

    def test_unicode_escape_4digit(self):
        """测试 4 位 Unicode 转义"""
        code = r'字符串型 s = "\u4f60\u597d";'  # 你好
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "你好"

    def test_unicode_escape_8digit(self):
        """测试 8 位 Unicode 转义"""
        code = r'字符串型 s = "\U00004f60\U0000597d";'  # 你好
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "你好"

    def test_hex_escape_chinese(self):
        """测试十六进制转义表示中文字符"""
        # 十六进制转义 \xNN 只处理 0x00-0xFF 范围
        # 要表示中文字符，应该使用 Unicode 转义
        # 这里测试 \xNN 范围内的值
        code = r'字符串型 s = "\xe4";'  # 228 = 0xE4
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        # \xe4 是 Latin Small Letter A with Grave (à) 的 Latin-1 编码
        # 但在 UTF-8 中这只是多字节字符的首字节
        assert len(string_tokens[0].value) == 1


if __name__ == "__main__":
    print("=" * 60)
    print("测试 UTF-8 字符串处理功能")
    print("=" * 60)
    print()

    # 运行测试
    pytest.main([__file__, "-v"])

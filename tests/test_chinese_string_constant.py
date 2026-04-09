# -*- coding: utf-8 -*-
"""
中文字符串常量测试

测试 P0-字符编码-中文字符串常量 功能

作者：阿福
日期：2026-04-10
"""

from zhc.parser.lexer import Lexer


class TestChineseStringConstant:
    """中文字符串常量测试"""

    def test_basic_chinese_string(self):
        """测试基本中文字符串"""
        code = '字符串型 问候 = "你好";'
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "你好"

    def test_chinese_string_with_punctuation(self):
        """测试带中文标点的字符串"""
        code = '字符串型 消息 = "欢迎使用中文编程语言！";'
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "欢迎使用中文编程语言！"

    def test_chinese_error_message(self):
        """测试中文错误消息"""
        code = '字符串型 错误消息 = "错误：文件不存在";'
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "错误：文件不存在"

    def test_chinese_format_string(self):
        """测试带中文的格式化字符串"""
        code = '打印("姓名：%s，年龄：%d\\n", "张三", 25);'
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 2
        assert string_tokens[0].value == "姓名：%s，年龄：%d\n"
        assert string_tokens[1].value == "张三"

    def test_chinese_poem(self):
        """测试中文诗歌字符串"""
        code = '字符串型 poem = "床前明月光，疑是地上霜。";'
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "床前明月光，疑是地上霜。"

    def test_mixed_chinese_english(self):
        """测试中英文混合字符串"""
        code = '字符串型 s = "Hello 你好 World 世界";'
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "Hello 你好 World 世界"


class TestFullwidthQuotes:
    """全角引号测试"""

    def test_fullwidth_book_quotes(self):
        """测试全角书名号『』"""
        code = "字符串型 s = 『全角引号字符串』;"
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "全角引号字符串"

    def test_fullwidth_corner_brackets(self):
        """测试全角方括号「」"""
        code = "字符串型 s = 「方括号字符串」;"
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "方括号字符串"

    def test_nested_fullwidth_quotes(self):
        """测试嵌套全角引号"""
        code = "字符串型 s = 『嵌套「括号」测试』;"
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "嵌套「括号」测试"

    def test_fullwidth_with_escape(self):
        """测试全角引号中的转义"""
        code = "字符串型 s = 『包含\\n换行』;"
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "包含\n换行"

    def test_fullwidth_chinese_content(self):
        """测试全角引号中的中文内容"""
        code = "字符串型 s = 『中文内容测试』;"
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "中文内容测试"


class TestMultilineString:
    """多行字符串测试"""

    def test_basic_multiline_string(self):
        """测试基本多行字符串"""
        code = '''字符串型 s = """
第一行
第二行
""";'''
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert "第一行" in string_tokens[0].value
        assert "第二行" in string_tokens[0].value

    def test_multiline_chinese_poem(self):
        """测试多行中文诗歌"""
        code = '''字符串型 poem = """
床前明月光，
疑是地上霜。
举头望明月，
低头思故乡。
""";'''
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert "床前明月光" in string_tokens[0].value
        assert "疑是地上霜" in string_tokens[0].value
        assert "举头望明月" in string_tokens[0].value
        assert "低头思故乡" in string_tokens[0].value

    def test_multiline_with_escape(self):
        """测试多行字符串中的转义"""
        code = '''字符串型 s = """
第一行\\n第二行
""";'''
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        # 转义的 \\n 应该被解析为换行符
        assert "第一行\n第二行" in string_tokens[0].value

    def test_multiline_preserve_indentation(self):
        """测试多行字符串保留缩进"""
        code = '''字符串型 s = """
    缩进第一行
    缩进第二行
""";'''
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        # 检查缩进是否保留
        assert "    缩进第一行" in string_tokens[0].value

    def test_multiline_empty_lines(self):
        """测试多行字符串中的空行"""
        code = '''字符串型 s = """
第一行

第三行
""";'''
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        # 检查空行是否保留
        lines = string_tokens[0].value.split("\n")
        assert len(lines) >= 3  # 至少有三行


class TestChineseEscapeSequence:
    """中文转义序列测试"""

    def test_chinese_with_newline(self):
        """测试中文带换行转义"""
        code = '字符串型 s = "第一行\\n第二行";'
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "第一行\n第二行"

    def test_chinese_with_tab(self):
        """测试中文带制表符转义"""
        code = '字符串型 s = "列一\\t列二";'
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "列一\t列二"

    def test_chinese_with_unicode_escape(self):
        """测试中文带 Unicode 转义"""
        # U+4F60 = '你', U+597D = '好'
        code = '字符串型 s = "\\u4f60\\u597d";'
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type.name == "STRING_LITERAL"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "你好"

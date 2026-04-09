#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试语法解析器

解析 ZhC 测试语法，生成测试 AST
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class NodeType(Enum):
    """AST 节点类型"""

    TEST_MODULE = "test_module"
    TEST_SUITE = "test_suite"
    TEST_FUNCTION = "test_function"
    ASSERTION = "assertion"
    IMPORT = "import"
    BLOCK = "block"
    STATEMENT = "statement"


@dataclass
class ASTNode:
    """AST 节点基类"""

    node_type: NodeType = NodeType.STATEMENT  # 默认值
    line_number: int = 0
    column: int = 0


@dataclass
class ImportNode(ASTNode):
    """导入节点"""

    module_name: str = ""
    alias: Optional[str] = None

    def __post_init__(self):
        self.node_type = NodeType.IMPORT


@dataclass
class AssertionNode(ASTNode):
    """断言节点"""

    assertion_type: str = ""
    args: List[str] = field(default_factory=list)
    message: Optional[str] = None

    def __post_init__(self):
        self.node_type = NodeType.ASSERTION


@dataclass
class StatementNode(ASTNode):
    """语句节点"""

    content: str = ""
    expression: Optional[str] = None

    def __post_init__(self):
        self.node_type = NodeType.STATEMENT


@dataclass
class BlockNode(ASTNode):
    """代码块节点"""

    statements: List[ASTNode] = field(default_factory=list)

    def __post_init__(self):
        self.node_type = NodeType.BLOCK


@dataclass
class TestFunctionNode(ASTNode):
    """测试函数节点"""

    name: str = ""
    body: BlockNode = field(default_factory=BlockNode)
    description: str = ""
    tags: List[str] = field(default_factory=list)
    skip: bool = False
    skip_reason: str = ""
    timeout: Optional[float] = None

    def __post_init__(self):
        self.node_type = NodeType.TEST_FUNCTION


@dataclass
class TestSuiteNode(ASTNode):
    """测试套件节点"""

    name: str = ""
    functions: List[TestFunctionNode] = field(default_factory=list)
    description: str = ""

    def __post_init__(self):
        self.node_type = NodeType.TEST_SUITE


@dataclass
class TestModuleNode(ASTNode):
    """测试模块节点"""

    name: str = ""
    imports: List[ImportNode] = field(default_factory=list)
    suites: List[TestSuiteNode] = field(default_factory=list)
    description: str = ""

    def __post_init__(self):
        self.node_type = NodeType.TEST_MODULE


class Lexer:
    """词法分析器"""

    # 关键字
    KEYWORDS = {
        "测试模块": "TEST_MODULE",
        "测试套件": "TEST_SUITE",
        "测试函数": "TEST_FUNCTION",
        "导入": "IMPORT",
        "主函数": "MAIN_FUNCTION",
        "断言等于": "ASSERT_EQUAL",
        "断言不等于": "ASSERT_NOT_EQUAL",
        "断言为真": "ASSERT_TRUE",
        "断言为假": "ASSERT_FALSE",
        "断言为空": "ASSERT_NULL",
        "断言非空": "ASSERT_NOT_NULL",
        "断言浮点等于": "ASSERT_FLOAT_EQUAL",
        "断言字符串等于": "ASSERT_STRING_EQUAL",
        "断言大于": "ASSERT_GREATER",
        "断言小于": "ASSERT_LESS",
        "断言包含": "ASSERT_IN",
        "断言不包含": "ASSERT_NOT_IN",
        "断言类型": "ASSERT_TYPE",
        "断言长度": "ASSERT_LENGTH",
        "断言为空集合": "ASSERT_EMPTY",
        "断言不为空集合": "ASSERT_NOT_EMPTY",
        "跳过": "SKIP",
        "原因": "REASON",
        "超时": "TIMEOUT",
    }

    # 单字符符号
    SYMBOLS = {
        "(": "LPAREN",
        ")": "RPAREN",
        "{": "LBRACE",
        "}": "RBRACE",
        "[": "LBRACKET",
        "]": "RBRACKET",
        ",": "COMMA",
        ";": "SEMICOLON",
        ":": "COLON",
        "=": "ASSIGN",
        ".": "DOT",
    }

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []

    def tokenize(self) -> List[Dict[str, Any]]:
        """词法分析"""
        while self.pos < len(self.source):
            # 跳过空白字符
            if self.source[self.pos].isspace():
                self._skip_whitespace()
                continue

            # 跳过注释
            if self._peek(2) == "//" or self._peek(2) == "#":
                self._skip_comment()
                continue

            # 尝试匹配关键字
            token = self._try_keyword()
            if token:
                self.tokens.append(token)
                continue

            # 尝试匹配标识符
            token = self._try_identifier()
            if token:
                self.tokens.append(token)
                continue

            # 尝试匹配字符串
            token = self._try_string()
            if token:
                self.tokens.append(token)
                continue

            # 尝试匹配数字
            token = self._try_number()
            if token:
                self.tokens.append(token)
                continue

            # 尝试匹配符号
            token = self._try_symbol()
            if token:
                self.tokens.append(token)
                continue

            # 未知字符
            raise SyntaxError(
                f"未知字符: '{self.source[self.pos]}' at line {self.line}, column {self.column}"
            )

        return self.tokens

    def _peek(self, n: int = 1) -> str:
        """查看前 n 个字符"""
        return self.source[self.pos : self.pos + n]

    def _advance(self, n: int = 1) -> str:
        """前进 n 个字符"""
        chars = self.source[self.pos : self.pos + n]
        for char in chars:
            if char == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        self.pos += n
        return chars

    def _skip_whitespace(self) -> None:
        """跳过空白字符"""
        while self.pos < len(self.source) and self.source[self.pos].isspace():
            self._advance()

    def _skip_comment(self) -> None:
        """跳过注释"""
        if self._peek(2) == "//":
            # 单行注释
            while self.pos < len(self.source) and self.source[self.pos] != "\n":
                self._advance()
        elif self._peek(2) == "#":
            # 单行注释
            while self.pos < len(self.source) and self.source[self.pos] != "\n":
                self._advance()

    def _try_keyword(self) -> Optional[Dict[str, Any]]:
        """尝试匹配关键字"""
        for keyword, token_type in self.KEYWORDS.items():
            if self.source[self.pos :].startswith(keyword):
                # 确保是完整的关键字（后面不是标识符字符）
                next_char_pos = self.pos + len(keyword)
                if (
                    next_char_pos >= len(self.source)
                    or not self.source[next_char_pos].isalnum()
                ):
                    token = {
                        "type": token_type,
                        "value": keyword,
                        "line": self.line,
                        "column": self.column,
                    }
                    self._advance(len(keyword))
                    return token
        return None

    def _try_identifier(self) -> Optional[Dict[str, Any]]:
        """尝试匹配标识符"""
        if self.source[self.pos].isalpha() or self.source[self.pos] == "_":
            start = self.pos
            while self.pos < len(self.source) and (
                self.source[self.pos].isalnum() or self.source[self.pos] == "_"
            ):
                self._advance()
            value = self.source[start : self.pos]
            return {
                "type": "IDENTIFIER",
                "value": value,
                "line": self.line,
                "column": self.column - len(value),
            }
        return None

    def _try_string(self) -> Optional[Dict[str, Any]]:
        """尝试匹配字符串"""
        if self.source[self.pos] == '"':
            self._advance()  # 跳过开始的引号
            start = self.pos
            while self.pos < len(self.source) and self.source[self.pos] != '"':
                if self.source[self.pos] == "\\" and self.pos + 1 < len(self.source):
                    self._advance(2)  # 跳过转义字符
                else:
                    self._advance()
            value = self.source[start : self.pos]
            if self.pos < len(self.source):
                self._advance()  # 跳过结束的引号
            return {
                "type": "STRING",
                "value": value,
                "line": self.line,
                "column": self.column - len(value) - 2,
            }
        return None

    def _try_number(self) -> Optional[Dict[str, Any]]:
        """尝试匹配数字"""
        if self.source[self.pos].isdigit():
            start = self.pos
            while self.pos < len(self.source) and (
                self.source[self.pos].isdigit() or self.source[self.pos] == "."
            ):
                self._advance()
            value = self.source[start : self.pos]
            return {
                "type": "NUMBER",
                "value": value,
                "line": self.line,
                "column": self.column - len(value),
            }
        return None

    def _try_symbol(self) -> Optional[Dict[str, Any]]:
        """尝试匹配符号"""
        char = self.source[self.pos]
        if char in self.SYMBOLS:
            token = {
                "type": self.SYMBOLS[char],
                "value": char,
                "line": self.line,
                "column": self.column,
            }
            self._advance()
            return token
        return None


class Parser:
    """语法分析器"""

    def __init__(self, tokens: List[Dict[str, Any]]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> TestModuleNode:
        """解析测试模块"""
        module = TestModuleNode()

        while self.pos < len(self.tokens):
            token = self._current()

            if token["type"] == "TEST_MODULE":
                module.name = self._parse_test_module()
            elif token["type"] == "IMPORT":
                module.imports.append(self._parse_import())
            elif token["type"] == "TEST_SUITE":
                module.suites.append(self._parse_test_suite())
            elif token["type"] == "IDENTIFIER":
                # 可能是测试函数（在默认套件中）
                if self._peek(1) and self._peek(1)["type"] == "LPAREN":
                    # 创建默认套件
                    if not module.suites:
                        module.suites.append(TestSuiteNode(name="default"))
                    module.suites[0].functions.append(self._parse_test_function())
                else:
                    self._advance()
            else:
                self._advance()

        return module

    def _current(self) -> Dict[str, Any]:
        """获取当前 token"""
        return self.tokens[self.pos] if self.pos < len(self.tokens) else {"type": "EOF"}

    def _peek(self, offset: int = 1) -> Optional[Dict[str, Any]]:
        """查看后续 token"""
        pos = self.pos + offset
        return self.tokens[pos] if pos < len(self.tokens) else None

    def _advance(self, n: int = 1) -> None:
        """前进 n 个 token"""
        self.pos += n

    def _expect(self, token_type: str) -> Dict[str, Any]:
        """期望特定类型的 token"""
        token = self._current()
        if token["type"] != token_type:
            raise SyntaxError(
                f"期望 {token_type}，实际 {token['type']} at line {token['line']}"
            )
        self._advance()
        return token

    def _parse_test_module(self) -> str:
        """解析测试模块声明"""
        self._advance()  # 跳过 '测试模块'
        name_token = self._expect("STRING")
        return name_token["value"]

    def _parse_import(self) -> ImportNode:
        """解析导入语句"""
        token = self._current()
        self._advance()  # 跳过 '导入'

        name_token = self._expect("IDENTIFIER")
        import_node = ImportNode(module_name=name_token["value"])
        import_node.line_number = token["line"]
        import_node.column = token["column"]

        # 检查是否有别名
        if (
            self._current()["type"] == "IDENTIFIER"
            and self._current()["value"] == "作为"
        ):
            self._advance()
            alias_token = self._expect("IDENTIFIER")
            import_node.alias = alias_token["value"]

        return import_node

    def _parse_test_suite(self) -> TestSuiteNode:
        """解析测试套件"""
        token = self._current()
        self._advance()  # 跳过 '测试套件'

        name_token = self._expect("STRING")
        suite = TestSuiteNode(name=name_token["value"])
        suite.line_number = token["line"]
        suite.column = token["column"]

        # 解析套件体
        if self._current()["type"] == "LBRACE":
            self._advance()  # 跳过 '{'
            while self._current()["type"] != "RBRACE":
                if self._current()["type"] == "TEST_FUNCTION":
                    suite.functions.append(self._parse_test_function())
                else:
                    self._advance()
            self._advance()  # 跳过 '}'

        return suite

    def _parse_test_function(self) -> TestFunctionNode:
        """解析测试函数"""
        token = self._current()
        self._advance()  # 跳过 '测试函数' 或标识符

        name_token = self._expect("IDENTIFIER")
        func = TestFunctionNode(name=name_token["value"])
        func.line_number = token["line"]
        func.column = token["column"]

        # 解析参数列表
        self._expect("LPAREN")
        self._expect("RPAREN")

        # 解析函数体
        if self._current()["type"] == "LBRACE":
            func.body = self._parse_block()

        return func

    def _parse_block(self) -> BlockNode:
        """解析代码块"""
        token = self._current()
        block = BlockNode()
        block.line_number = token["line"]
        block.column = token["column"]

        self._expect("LBRACE")
        while self._current()["type"] != "RBRACE":
            block.statements.append(self._parse_statement())
        self._expect("RBRACE")

        return block

    def _parse_statement(self) -> ASTNode:
        """解析语句"""
        token = self._current()

        # 检查是否是断言
        if token["type"].startswith("ASSERT_"):
            return self._parse_assertion()

        # 检查是否是变量声明或表达式
        if token["type"] == "IDENTIFIER":
            return self._parse_expression_statement()

        # 其他语句
        self._advance()
        return StatementNode(
            content=token["value"], line_number=token["line"], column=token["column"]
        )

    def _parse_assertion(self) -> AssertionNode:
        """解析断言"""
        token = self._current()
        assertion_type = token["type"].lower()
        self._advance()  # 跳过断言关键字

        assertion = AssertionNode(assertion_type=assertion_type)
        assertion.line_number = token["line"]
        assertion.column = token["column"]

        # 解析参数
        self._expect("LPAREN")
        while self._current()["type"] != "RPAREN":
            arg_token = self._current()
            assertion.args.append(arg_token["value"])
            self._advance()
            if self._current()["type"] == "COMMA":
                self._advance()
        self._expect("RPAREN")

        return assertion

    def _parse_expression_statement(self) -> StatementNode:
        """解析表达式语句"""
        token = self._current()
        statement = StatementNode(line_number=token["line"], column=token["column"])

        # 收集表达式直到遇到分号或换行
        while self.pos < len(self.tokens) and self._current()["type"] not in [
            "SEMICOLON",
            "RBRACE",
            "EOF",
        ]:
            statement.content += self._current()["value"] + " "
            self._advance()

        statement.content = statement.content.strip()
        return statement


def parse_test_module(source: str) -> TestModuleNode:
    """
    解析测试模块源代码

    Args:
        source: 源代码字符串

    Returns:
        测试模块 AST 节点
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def parse_test_file(file_path: str) -> TestModuleNode:
    """
    解析测试文件

    Args:
        file_path: 文件路径

    Returns:
        测试模块 AST 节点
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    return parse_test_module(source)

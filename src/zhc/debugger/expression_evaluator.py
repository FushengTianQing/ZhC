"""
表达式求值器

提供调试时的表达式求值功能：
- 变量引用
- 成员访问
- 数组索引
- 指针解引用
- 运算符
- 函数调用
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


class TokenType(Enum):
    """词法单元类型"""

    # 标识符和字面量
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    CHAR = auto()

    # 运算符
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    AMPERSAND = auto()
    PIPE = auto()
    CARET = auto()
    TILDE = auto()
    BANG = auto()
    EQUALS = auto()
    EQUALS_EQUALS = auto()
    BANG_EQUALS = auto()
    LESS = auto()
    LESS_EQUALS = auto()
    GREATER = auto()
    GREATER_EQUALS = auto()
    AMPERSAND_AMPERSAND = auto()
    PIPE_PIPE = auto()
    LESS_LESS = auto()
    GREATER_GREATER = auto()

    # 分隔符
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()
    DOT = auto()
    ARROW = auto()
    COMMA = auto()
    COLON = auto()
    SEMICOLON = auto()
    QUESTION = auto()

    # 特殊
    EOF = auto()
    ERROR = auto()


@dataclass
class Token:
    """词法单元"""

    type: TokenType
    value: Any
    position: int
    line: int = 0
    column: int = 0


class ExpressionType(Enum):
    """表达式类型"""

    LITERAL = "literal"
    VARIABLE = "variable"
    BINARY_OP = "binary_op"
    UNARY_OP = "unary_op"
    MEMBER_ACCESS = "member_access"
    ARRAY_INDEX = "array_index"
    POINTER_DEREF = "pointer_deref"
    FUNCTION_CALL = "function_call"
    TERNARY = "ternary"
    CAST = "cast"
    SIZEOF = "sizeof"


@dataclass
class Expression:
    """表达式基类"""

    type: ExpressionType
    value: Any = None
    children: List["Expression"] = field(default_factory=list)
    operator: Optional[str] = None

    def __str__(self) -> str:
        if self.type == ExpressionType.LITERAL:
            return str(self.value)
        elif self.type == ExpressionType.VARIABLE:
            return self.value
        elif self.type == ExpressionType.BINARY_OP:
            left, right = self.children
            return f"({left} {self.operator} {right})"
        elif self.type == ExpressionType.UNARY_OP:
            child = self.children[0]
            return f"({self.operator}{child})"
        elif self.type == ExpressionType.MEMBER_ACCESS:
            base, member = self.children
            return f"{base}.{member.value}"
        elif self.type == ExpressionType.ARRAY_INDEX:
            base, index = self.children
            return f"{base}[{index}]"
        elif self.type == ExpressionType.POINTER_DEREF:
            child = self.children[0]
            return f"*{child}"
        elif self.type == ExpressionType.FUNCTION_CALL:
            func = self.children[0]
            args = self.children[1:]
            return f"{func}({', '.join(str(a) for a in args)})"
        elif self.type == ExpressionType.TERNARY:
            cond, then_expr, else_expr = self.children
            return f"({cond} ? {then_expr} : {else_expr})"
        else:
            return f"<{self.type}>"


@dataclass
class EvaluationResult:
    """求值结果"""

    value: Any
    type_name: str
    is_lvalue: bool = False
    address: Optional[int] = None
    error: Optional[str] = None

    @property
    def is_error(self) -> bool:
        return self.error is not None

    @property
    def is_valid(self) -> bool:
        return self.error is None and self.value is not None


@dataclass
class EvaluationContext:
    """求值上下文"""

    frame_id: int = 0
    thread_id: int = 0
    pc: int = 0
    stack_pointer: int = 0
    frame_pointer: int = 0
    variables: Dict[str, Any] = field(default_factory=dict)
    registers: Dict[str, int] = field(default_factory=dict)
    types: Dict[str, Any] = field(default_factory=dict)

    def get_variable(self, name: str) -> Optional[Any]:
        """获取变量值"""
        return self.variables.get(name)

    def get_register(self, name: str) -> Optional[int]:
        """获取寄存器值"""
        return self.registers.get(name)

    def set_variable(self, name: str, value: Any) -> None:
        """设置变量值"""
        self.variables[name] = value


class Lexer:
    """词法分析器"""

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1

    def peek(self, offset: int = 0) -> str:
        """查看字符"""
        pos = self.pos + offset
        if pos >= len(self.source):
            return "\0"
        return self.source[pos]

    def advance(self) -> str:
        """前进一个字符"""
        ch = self.peek()
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def skip_whitespace(self) -> None:
        """跳过空白字符"""
        while self.peek().isspace():
            self.advance()

    def read_number(self) -> Token:
        """读取数字"""
        start_pos = self.pos
        start_col = self.column
        result = ""
        is_float = False
        # 检查十六进制
        if self.peek() == "0" and self.peek(1) in ("x", "X"):
            result += self.advance()  # '0'
            result += self.advance()  # 'x'
            while self.peek() in "0123456789abcdefABCDEF":
                result += self.advance()
            return Token(
                TokenType.INTEGER, int(result, 16), start_pos, self.line, start_col
            )

        # 读取整数部分
        while self.peek().isdigit():
            result += self.advance()

        # 检查小数点
        if self.peek() == "." and self.peek(1).isdigit():
            is_float = True
            result += self.advance()  # '.'
            while self.peek().isdigit():
                result += self.advance()

        # 检查指数
        if self.peek() in ("e", "E"):
            is_float = True
            result += self.advance()
            if self.peek() in ("+", "-"):
                result += self.advance()
            while self.peek().isdigit():
                result += self.advance()

        # 检查类型后缀
        if self.peek() in ("f", "F", "l", "L"):
            is_float = True
            result += self.advance()

        if is_float:
            return Token(
                TokenType.FLOAT, float(result), start_pos, self.line, start_col
            )
        else:
            return Token(
                TokenType.INTEGER, int(result), start_pos, self.line, start_col
            )

    def read_identifier(self) -> Token:
        """读取标识符"""
        start_pos = self.pos
        start_col = self.column
        result = ""

        while self.peek().isalnum() or self.peek() == "_":
            result += self.advance()

        return Token(TokenType.IDENTIFIER, result, start_pos, self.line, start_col)

    def read_string(self) -> Token:
        """读取字符串"""
        start_pos = self.pos
        start_col = self.column
        quote = self.advance()  # 开始引号
        result = ""

        while self.peek() != quote and self.peek() != "\0":
            if self.peek() == "\\":
                self.advance()
                ch = self.advance()
                if ch == "n":
                    result += "\n"
                elif ch == "t":
                    result += "\t"
                elif ch == "r":
                    result += "\r"
                elif ch == "\\":
                    result += "\\"
                elif ch == quote:
                    result += quote
                else:
                    result += ch
            else:
                result += self.advance()

        if self.peek() == quote:
            self.advance()  # 结束引号

        return Token(TokenType.STRING, result, start_pos, self.line, start_col)

    def read_char(self) -> Token:
        """读取字符"""
        start_pos = self.pos
        start_col = self.column
        self.advance()  # 开始单引号
        result = ""

        if self.peek() == "\\":
            self.advance()
            ch = self.advance()
            if ch == "n":
                result = "\n"
            elif ch == "t":
                result = "\t"
            elif ch == "r":
                result = "\r"
            elif ch == "\\":
                result = "\\"
            elif ch == "'":
                result = "'"
            elif ch == "0":
                result = "\0"
            else:
                result = ch
        else:
            result = self.advance()

        if self.peek() == "'":
            self.advance()  # 结束单引号

        return Token(TokenType.CHAR, result, start_pos, self.line, start_col)

    def next_token(self) -> Token:
        """获取下一个词法单元"""
        self.skip_whitespace()

        if self.pos >= len(self.source):
            return Token(TokenType.EOF, None, self.pos, self.line, self.column)

        start_pos = self.pos
        start_col = self.column
        ch = self.peek()

        # 数字
        if ch.isdigit():
            return self.read_number()

        # 标识符
        if ch.isalpha() or ch == "_":
            return self.read_identifier()

        # 字符串
        if ch == '"':
            return self.read_string()

        # 字符
        if ch == "'":
            return self.read_char()

        # 运算符和分隔符
        if ch == "+":
            self.advance()
            return Token(TokenType.PLUS, "+", start_pos, self.line, start_col)
        elif ch == "-":
            self.advance()
            if self.peek() == ">":
                self.advance()
                return Token(TokenType.ARROW, "->", start_pos, self.line, start_col)
            return Token(TokenType.MINUS, "-", start_pos, self.line, start_col)
        elif ch == "*":
            self.advance()
            return Token(TokenType.STAR, "*", start_pos, self.line, start_col)
        elif ch == "/":
            self.advance()
            return Token(TokenType.SLASH, "/", start_pos, self.line, start_col)
        elif ch == "%":
            self.advance()
            return Token(TokenType.PERCENT, "%", start_pos, self.line, start_col)
        elif ch == "&":
            self.advance()
            if self.peek() == "&":
                self.advance()
                return Token(
                    TokenType.AMPERSAND_AMPERSAND, "&&", start_pos, self.line, start_col
                )
            return Token(TokenType.AMPERSAND, "&", start_pos, self.line, start_col)
        elif ch == "|":
            self.advance()
            if self.peek() == "|":
                self.advance()
                return Token(TokenType.PIPE_PIPE, "||", start_pos, self.line, start_col)
            return Token(TokenType.PIPE, "|", start_pos, self.line, start_col)
        elif ch == "^":
            self.advance()
            return Token(TokenType.CARET, "^", start_pos, self.line, start_col)
        elif ch == "~":
            self.advance()
            return Token(TokenType.TILDE, "~", start_pos, self.line, start_col)
        elif ch == "!":
            self.advance()
            if self.peek() == "=":
                self.advance()
                return Token(
                    TokenType.BANG_EQUALS, "!=", start_pos, self.line, start_col
                )
            return Token(TokenType.BANG, "!", start_pos, self.line, start_col)
        elif ch == "=":
            self.advance()
            if self.peek() == "=":
                self.advance()
                return Token(
                    TokenType.EQUALS_EQUALS, "==", start_pos, self.line, start_col
                )
            return Token(TokenType.EQUALS, "=", start_pos, self.line, start_col)
        elif ch == "<":
            self.advance()
            if self.peek() == "<":
                self.advance()
                return Token(TokenType.LESS_LESS, "<<", start_pos, self.line, start_col)
            if self.peek() == "=":
                self.advance()
                return Token(
                    TokenType.LESS_EQUALS, "<=", start_pos, self.line, start_col
                )
            return Token(TokenType.LESS, "<", start_pos, self.line, start_col)
        elif ch == ">":
            self.advance()
            if self.peek() == ">":
                self.advance()
                return Token(
                    TokenType.GREATER_GREATER, ">>", start_pos, self.line, start_col
                )
            if self.peek() == "=":
                self.advance()
                return Token(
                    TokenType.GREATER_EQUALS, ">=", start_pos, self.line, start_col
                )
            return Token(TokenType.GREATER, ">", start_pos, self.line, start_col)
        elif ch == "(":
            self.advance()
            return Token(TokenType.LPAREN, "(", start_pos, self.line, start_col)
        elif ch == ")":
            self.advance()
            return Token(TokenType.RPAREN, ")", start_pos, self.line, start_col)
        elif ch == "[":
            self.advance()
            return Token(TokenType.LBRACKET, "[", start_pos, self.line, start_col)
        elif ch == "]":
            self.advance()
            return Token(TokenType.RBRACKET, "]", start_pos, self.line, start_col)
        elif ch == "{":
            self.advance()
            return Token(TokenType.LBRACE, "{", start_pos, self.line, start_col)
        elif ch == "}":
            self.advance()
            return Token(TokenType.RBRACE, "}", start_pos, self.line, start_col)
        elif ch == ".":
            self.advance()
            return Token(TokenType.DOT, ".", start_pos, self.line, start_col)
        elif ch == ",":
            self.advance()
            return Token(TokenType.COMMA, ",", start_pos, self.line, start_col)
        elif ch == ":":
            self.advance()
            return Token(TokenType.COLON, ":", start_pos, self.line, start_col)
        elif ch == ";":
            self.advance()
            return Token(TokenType.SEMICOLON, ";", start_pos, self.line, start_col)
        elif ch == "?":
            self.advance()
            return Token(TokenType.QUESTION, "?", start_pos, self.line, start_col)

        # 未知字符
        self.advance()
        return Token(TokenType.ERROR, ch, start_pos, self.line, start_col)

    def tokenize(self) -> List[Token]:
        """获取所有词法单元"""
        tokens = []
        while True:
            token = self.next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break
        return tokens


class Parser:
    """语法分析器"""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset: int = 0) -> Token:
        """查看词法单元"""
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[pos]

    def advance(self) -> Token:
        """前进一个词法单元"""
        token = self.peek()
        self.pos += 1
        return token

    def expect(self, token_type: TokenType) -> Token:
        """期望特定类型的词法单元"""
        token = self.peek()
        if token.type != token_type:
            raise SyntaxError(
                f"Expected {token_type}, got {token.type} at position {token.position}"
            )
        return self.advance()

    def parse(self) -> Expression:
        """解析表达式"""
        return self.parse_ternary()

    def parse_ternary(self) -> Expression:
        """解析三元表达式"""
        cond = self.parse_logical_or()

        if self.peek().type == TokenType.QUESTION:
            self.advance()
            then_expr = self.parse_ternary()
            self.expect(TokenType.COLON)
            else_expr = self.parse_ternary()
            return Expression(
                type=ExpressionType.TERNARY, children=[cond, then_expr, else_expr]
            )

        return cond

    def parse_logical_or(self) -> Expression:
        """解析逻辑或"""
        left = self.parse_logical_and()

        while self.peek().type == TokenType.PIPE_PIPE:
            op = self.advance().value
            right = self.parse_logical_and()
            left = Expression(
                type=ExpressionType.BINARY_OP, operator=op, children=[left, right]
            )

        return left

    def parse_logical_and(self) -> Expression:
        """解析逻辑与"""
        left = self.parse_bitwise_or()

        while self.peek().type == TokenType.AMPERSAND_AMPERSAND:
            op = self.advance().value
            right = self.parse_bitwise_or()
            left = Expression(
                type=ExpressionType.BINARY_OP, operator=op, children=[left, right]
            )

        return left

    def parse_bitwise_or(self) -> Expression:
        """解析按位或"""
        left = self.parse_bitwise_xor()

        while self.peek().type == TokenType.PIPE:
            op = self.advance().value
            right = self.parse_bitwise_xor()
            left = Expression(
                type=ExpressionType.BINARY_OP, operator=op, children=[left, right]
            )

        return left

    def parse_bitwise_xor(self) -> Expression:
        """解析按位异或"""
        left = self.parse_bitwise_and()

        while self.peek().type == TokenType.CARET:
            op = self.advance().value
            right = self.parse_bitwise_and()
            left = Expression(
                type=ExpressionType.BINARY_OP, operator=op, children=[left, right]
            )

        return left

    def parse_bitwise_and(self) -> Expression:
        """解析按位与"""
        left = self.parse_equality()

        while self.peek().type == TokenType.AMPERSAND:
            op = self.advance().value
            right = self.parse_equality()
            left = Expression(
                type=ExpressionType.BINARY_OP, operator=op, children=[left, right]
            )

        return left

    def parse_equality(self) -> Expression:
        """解析相等性"""
        left = self.parse_relational()

        while self.peek().type in (TokenType.EQUALS_EQUALS, TokenType.BANG_EQUALS):
            op = self.advance().value
            right = self.parse_relational()
            left = Expression(
                type=ExpressionType.BINARY_OP, operator=op, children=[left, right]
            )

        return left

    def parse_relational(self) -> Expression:
        """解析关系表达式"""
        left = self.parse_shift()

        while self.peek().type in (
            TokenType.LESS,
            TokenType.LESS_EQUALS,
            TokenType.GREATER,
            TokenType.GREATER_EQUALS,
        ):
            op = self.advance().value
            right = self.parse_shift()
            left = Expression(
                type=ExpressionType.BINARY_OP, operator=op, children=[left, right]
            )

        return left

    def parse_shift(self) -> Expression:
        """解析移位"""
        left = self.parse_additive()

        while self.peek().type in (TokenType.LESS_LESS, TokenType.GREATER_GREATER):
            op = self.advance().value
            right = self.parse_additive()
            left = Expression(
                type=ExpressionType.BINARY_OP, operator=op, children=[left, right]
            )

        return left

    def parse_additive(self) -> Expression:
        """解析加减"""
        left = self.parse_multiplicative()

        while self.peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.advance().value
            right = self.parse_multiplicative()
            left = Expression(
                type=ExpressionType.BINARY_OP, operator=op, children=[left, right]
            )

        return left

    def parse_multiplicative(self) -> Expression:
        """解析乘除"""
        left = self.parse_unary()

        while self.peek().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.advance().value
            right = self.parse_unary()
            left = Expression(
                type=ExpressionType.BINARY_OP, operator=op, children=[left, right]
            )

        return left

    def parse_unary(self) -> Expression:
        """解析一元表达式"""
        if self.peek().type in (
            TokenType.BANG,
            TokenType.TILDE,
            TokenType.MINUS,
            TokenType.STAR,
            TokenType.AMPERSAND,
        ):
            op = self.advance().value
            operand = self.parse_unary()
            return Expression(
                type=ExpressionType.UNARY_OP, operator=op, children=[operand]
            )

        return self.parse_postfix()

    def parse_postfix(self) -> Expression:
        """解析后缀表达式"""
        expr = self.parse_primary()

        while True:
            if self.peek().type == TokenType.DOT:
                self.advance()
                member = self.expect(TokenType.IDENTIFIER)
                expr = Expression(
                    type=ExpressionType.MEMBER_ACCESS,
                    children=[
                        expr,
                        Expression(type=ExpressionType.LITERAL, value=member.value),
                    ],
                )
            elif self.peek().type == TokenType.ARROW:
                self.advance()
                member = self.expect(TokenType.IDENTIFIER)
                expr = Expression(type=ExpressionType.POINTER_DEREF, children=[expr])
                expr = Expression(
                    type=ExpressionType.MEMBER_ACCESS,
                    children=[
                        expr,
                        Expression(type=ExpressionType.LITERAL, value=member.value),
                    ],
                )
            elif self.peek().type == TokenType.LBRACKET:
                self.advance()
                index = self.parse()
                self.expect(TokenType.RBRACKET)
                expr = Expression(
                    type=ExpressionType.ARRAY_INDEX, children=[expr, index]
                )
            elif self.peek().type == TokenType.LPAREN:
                # 函数调用
                self.advance()
                args = []
                if self.peek().type != TokenType.RPAREN:
                    args.append(self.parse())
                    while self.peek().type == TokenType.COMMA:
                        self.advance()
                        args.append(self.parse())
                self.expect(TokenType.RPAREN)
                expr = Expression(
                    type=ExpressionType.FUNCTION_CALL, children=[expr] + args
                )
            else:
                break

        return expr

    def parse_primary(self) -> Expression:
        """解析基本表达式"""
        token = self.peek()

        if token.type == TokenType.INTEGER:
            self.advance()
            return Expression(type=ExpressionType.LITERAL, value=token.value)

        elif token.type == TokenType.FLOAT:
            self.advance()
            return Expression(type=ExpressionType.LITERAL, value=token.value)

        elif token.type == TokenType.STRING:
            self.advance()
            return Expression(type=ExpressionType.LITERAL, value=token.value)

        elif token.type == TokenType.CHAR:
            self.advance()
            return Expression(type=ExpressionType.LITERAL, value=ord(token.value))

        elif token.type == TokenType.IDENTIFIER:
            self.advance()
            return Expression(type=ExpressionType.VARIABLE, value=token.value)

        elif token.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse()
            self.expect(TokenType.RPAREN)
            return expr

        else:
            raise SyntaxError(
                f"Unexpected token {token.type} at position {token.position}"
            )


class ExpressionEvaluator:
    """表达式求值器"""

    def __init__(self):
        self._binary_ops: Dict[str, Callable] = {
            "+": lambda a, b: a + b,
            "-": lambda a, b: a - b,
            "*": lambda a, b: a * b,
            "/": lambda a, b: a / b if b != 0 else float("inf"),
            "%": lambda a, b: a % b if b != 0 else 0,
            "&": lambda a, b: a & b,
            "|": lambda a, b: a | b,
            "^": lambda a, b: a ^ b,
            "<<": lambda a, b: a << b,
            ">>": lambda a, b: a >> b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "&&": lambda a, b: a and b,
            "||": lambda a, b: a or b,
        }

        self._unary_ops: Dict[str, Callable] = {
            "-": lambda a: -a,
            "!": lambda a: not a,
            "~": lambda a: ~a,
            "*": lambda a: a,  # 解引用需要特殊处理
            "&": lambda a: a,  # 取地址需要特殊处理
        }

    def evaluate(self, expr_str: str, context: EvaluationContext) -> EvaluationResult:
        """求值表达式"""
        try:
            # 词法分析
            lexer = Lexer(expr_str)
            tokens = lexer.tokenize()

            # 语法分析
            parser = Parser(tokens)
            ast = parser.parse()

            # 求值
            return self._evaluate(ast, context)

        except Exception as e:
            return EvaluationResult(value=None, type_name="error", error=str(e))

    def _evaluate(
        self, expr: Expression, context: EvaluationContext
    ) -> EvaluationResult:
        """递归求值"""
        if expr.type == ExpressionType.LITERAL:
            return EvaluationResult(
                value=expr.value, type_name=type(expr.value).__name__
            )

        elif expr.type == ExpressionType.VARIABLE:
            value = context.get_variable(expr.value)
            if value is None:
                return EvaluationResult(
                    value=None,
                    type_name="error",
                    error=f"Undefined variable: {expr.value}",
                )
            return EvaluationResult(
                value=value, type_name=type(value).__name__, is_lvalue=True
            )

        elif expr.type == ExpressionType.BINARY_OP:
            left = self._evaluate(expr.children[0], context)
            right = self._evaluate(expr.children[1], context)

            if left.is_error:
                return left
            if right.is_error:
                return right

            op_func = self._binary_ops.get(expr.operator)
            if op_func is None:
                return EvaluationResult(
                    value=None,
                    type_name="error",
                    error=f"Unknown operator: {expr.operator}",
                )

            try:
                result = op_func(left.value, right.value)
                return EvaluationResult(value=result, type_name=type(result).__name__)
            except Exception as e:
                return EvaluationResult(value=None, type_name="error", error=str(e))

        elif expr.type == ExpressionType.UNARY_OP:
            operand = self._evaluate(expr.children[0], context)

            if operand.is_error:
                return operand

            op_func = self._unary_ops.get(expr.operator)
            if op_func is None:
                return EvaluationResult(
                    value=None,
                    type_name="error",
                    error=f"Unknown operator: {expr.operator}",
                )

            try:
                result = op_func(operand.value)
                return EvaluationResult(value=result, type_name=type(result).__name__)
            except Exception as e:
                return EvaluationResult(value=None, type_name="error", error=str(e))

        elif expr.type == ExpressionType.MEMBER_ACCESS:
            base = self._evaluate(expr.children[0], context)
            member_name = expr.children[1].value

            if base.is_error:
                return base

            # 成员访问
            if isinstance(base.value, dict):
                if member_name in base.value:
                    return EvaluationResult(
                        value=base.value[member_name],
                        type_name=type(base.value[member_name]).__name__,
                    )
            elif hasattr(base.value, member_name):
                return EvaluationResult(
                    value=getattr(base.value, member_name),
                    type_name=type(getattr(base.value, member_name)).__name__,
                )

            return EvaluationResult(
                value=None,
                type_name="error",
                error=f"No member '{member_name}' in object",
            )

        elif expr.type == ExpressionType.ARRAY_INDEX:
            base = self._evaluate(expr.children[0], context)
            index = self._evaluate(expr.children[1], context)

            if base.is_error:
                return base
            if index.is_error:
                return index

            try:
                result = base.value[index.value]
                return EvaluationResult(value=result, type_name=type(result).__name__)
            except Exception as e:
                return EvaluationResult(value=None, type_name="error", error=str(e))

        elif expr.type == ExpressionType.POINTER_DEREF:
            operand = self._evaluate(expr.children[0], context)

            if operand.is_error:
                return operand

            # 指针解引用需要实际调试器支持
            return EvaluationResult(
                value=None,
                type_name="error",
                error="Pointer dereference requires debugger backend",
            )

        elif expr.type == ExpressionType.TERNARY:
            cond = self._evaluate(expr.children[0], context)

            if cond.is_error:
                return cond

            if cond.value:
                return self._evaluate(expr.children[1], context)
            else:
                return self._evaluate(expr.children[2], context)

        elif expr.type == ExpressionType.FUNCTION_CALL:
            # 函数调用需要实际调试器支持
            return EvaluationResult(
                value=None,
                type_name="error",
                error="Function call requires debugger backend",
            )

        else:
            return EvaluationResult(
                value=None,
                type_name="error",
                error=f"Unknown expression type: {expr.type}",
            )

    def parse(self, expr_str: str) -> Expression:
        """解析表达式（不求值）"""
        lexer = Lexer(expr_str)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        return parser.parse()

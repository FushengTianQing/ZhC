#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
词法分析器 - Lexer
将ZHC源代码转换为Token流

作者: 阿福
日期: 2026-04-03
"""

from enum import Enum, auto
from typing import List, Optional, Tuple
from dataclasses import dataclass

# 导入统一异常类
from zhc.errors import (
    LexerError,
    SourceLocation,
    illegal_character,
    unterminated_string,
    unterminated_comment,
    unterminated_char,
    invalid_escape_sequence,
    invalid_unicode_character,
)


class TokenType(Enum):
    """Token类型枚举"""

    # 关键字
    # 类型关键字
    INT = auto()  # 整数型
    FLOAT = auto()  # 浮点型
    CHAR = auto()  # 字符型
    BOOL = auto()  # 布尔型
    VOID = auto()  # 空型
    STRING = auto()  # 字符串型
    BYTE = auto()  # 字节型
    DOUBLE = auto()  # 双精度浮点型
    BOOL_TYPE = auto()  # 逻辑型 (_Bool)
    LONG = auto()  # 长整数型
    SHORT = auto()  # 短整数型
    UNSIGNED = auto()  # 无符号
    SIGNED = auto()  # 有符号

    # 修饰符关键字
    VOLATILE = auto()  # 易变
    REGISTER = auto()  # 注册
    INLINE = auto()  # 内联

    # 复合类型关键字
    UNION = auto()  # 共用体
    ENUM = auto()  # 枚举
    TYPEDEF = auto()  # 别名
    GOTO = auto()  # 去向

    # 流程控制关键字
    IF = auto()  # 如果
    ELSE = auto()  # 否则
    WHILE = auto()  # 当
    FOR = auto()  # 循环
    DO = auto()  # 执行
    BREAK = auto()  # 跳出
    CONTINUE = auto()  # 继续
    RETURN = auto()  # 返回
    SWITCH = auto()  # 选择
    CASE = auto()  # 情况
    DEFAULT = auto()  # 默认

    # 定义关键字
    FUNCTION = auto()  # 函数
    STRUCT = auto()  # 结构体
    CONST = auto()  # 常量
    STATIC = auto()  # 静态
    EXTERN = auto()  # 外部

    # 模块关键字
    MODULE = auto()  # 模块
    IMPORT = auto()  # 导入
    EXPORT = auto()  # 公开
    PRIVATE = auto()  # 私有

    # 特殊值
    TRUE = auto()  # 真
    FALSE = auto()  # 假
    NULL = auto()  # 空

    # 自动类型推导关键字
    AUTO = auto()  # 自动

    # 标识符和字面量
    IDENTIFIER = auto()  # 标识符
    INT_LITERAL = auto()  # 整数字面量
    FLOAT_LITERAL = auto()  # 浮点字面量
    STRING_LITERAL = auto()  # 字符串字面量
    CHAR_LITERAL = auto()  # 字符字面量
    WIDE_CHAR_LITERAL = auto()  # 宽字符字面量
    WIDE_STRING_LITERAL = auto()  # 宽字符串字面量

    # 运算符
    PLUS = auto()  # +
    MINUS = auto()  # -
    STAR = auto()  # *
    SLASH = auto()  # /
    PERCENT = auto()  # %

    PLUS_ASSIGN = auto()  # +=
    MINUS_ASSIGN = auto()  # -=
    STAR_ASSIGN = auto()  # *=
    SLASH_ASSIGN = auto()  # /=
    PERCENT_ASSIGN = auto()  # %=

    EQ = auto()  # ==
    NE = auto()  # !=
    LT = auto()  # <
    LE = auto()  # <=
    GT = auto()  # >
    GE = auto()  # >=

    AND = auto()  # &&
    OR = auto()  # ||
    NOT = auto()  # !

    BIT_AND = auto()  # &
    BIT_OR = auto()  # |
    BIT_XOR = auto()  # ^
    BIT_NOT = auto()  # ~
    LSHIFT = auto()  # <<
    RSHIFT = auto()  # >>

    ASSIGN = auto()  # =
    ARROW = auto()  # ->
    DOT = auto()  # .

    INCREMENT = auto()  # ++
    DECREMENT = auto()  # --

    # 分隔符
    LPAREN = auto()  # (
    RPAREN = auto()  # )
    LBRACE = auto()  # {
    RBRACE = auto()  # }
    LBRACKET = auto()  # [
    RBRACKET = auto()  # ]
    SEMICOLON = auto()  # ;
    COMMA = auto()  # ,
    COLON = auto()  # :

    # 泛型相关分隔符
    LANGLE = auto()  # < (泛型参数开始)
    RANGLE = auto()  # > (泛型参数结束)

    # 泛型关键字
    GENERIC_TYPE = auto()  # 泛型类型
    GENERIC_FUNC = auto()  # 泛型函数
    TYPE_PARAM = auto()  # 类型
    CONSTRAINT = auto()  # 约束
    WHERE = auto()  # 其中 (where clause)

    # 模式匹配关键字
    MATCH = auto()  # 匹配
    UNDERSCORE = auto()  # _ (通配符)
    DOTDOT = auto()  # .. (范围操作符)
    ELLIPSIS = auto()  # ... (范围 case 操作符)
    FAT_ARROW = auto()  # => (匹配分支箭头)

    # 异步编程关键字
    ASYNC = auto()  # 异步
    AWAIT = auto()  # 等待
    FUTURE = auto()  # 未来
    TASK = auto()  # 任务
    PROMISE = auto()  # 承诺
    YIELD = auto()  # 让出
    COROUTINE = auto()  # 协程
    CHANNEL = auto()  # 通道
    SPAWN = auto()  # 启动（启动协程）

    # 异常处理关键字
    TRY = auto()  # 尝试
    CATCH = auto()  # 捕获
    FINALLY = auto()  # 最终
    THROW = auto()  # 抛出
    EXCEPTION = auto()  # 异常
    EXCEPTION_CLASS = auto()  # 异常类

    # 特殊
    EOF = auto()  # 文件结束
    UNKNOWN = auto()  # 未知字符


@dataclass
class Token:
    """Token类 - 增强位置信息

    Attributes:
        type: Token 类型
        value: Token 值
        line: 行号（从1开始）
        column: 列号（从1开始）
        end_line: 结束行号（多行 Token 如字符串）
        end_column: 结束列号
    """

    type: TokenType
    value: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None

    def __post_init__(self):
        """初始化后处理：自动计算 end_column"""
        if self.end_column is None:
            # 默认 end_column = column + len(value)
            self.end_column = self.column + len(str(self.value))
        if self.end_line is None:
            self.end_line = self.line

    def __repr__(self):
        if self.end_line != self.line:
            return f"Token({self.type.name}, '{self.value}', {self.line}:{self.column}-{self.end_line}:{self.end_column})"
        return f"Token({self.type.name}, '{self.value}', {self.line}:{self.column}-{self.end_column})"

    def is_multiline(self) -> bool:
        """判断是否为多行 Token"""
        return self.end_line is not None and self.end_line != self.line

    def get_length(self) -> int:
        """获取 Token 长度（单行时）"""
        if self.is_multiline():
            return -1
        return (self.end_column or self.column) - self.column

    def to_source_location(self, file_path: str = "") -> "SourceLocation":
        """转换为 SourceLocation 对象"""
        return SourceLocation(
            file_path=file_path,
            line=self.line,
            column=self.column,
            end_line=self.end_line,
            end_column=self.end_column,
            token_text=str(self.value),
        )


class Lexer:
    """词法分析器"""

    # 关键字映射
    KEYWORDS = {
        # 类型关键字（完整形式）
        "整数型": TokenType.INT,
        "浮点型": TokenType.FLOAT,
        "字符型": TokenType.CHAR,
        "布尔型": TokenType.BOOL,
        "空型": TokenType.VOID,
        "字符串型": TokenType.STRING,
        "字节型": TokenType.BYTE,
        "双精度浮点型": TokenType.DOUBLE,
        "逻辑型": TokenType.BOOL_TYPE,
        "长整数型": TokenType.LONG,
        "短整数型": TokenType.SHORT,
        "无类型": TokenType.VOID,
        "无符号": TokenType.UNSIGNED,
        "有符号": TokenType.SIGNED,
        # 类型关键字（简写形式）
        "整数": TokenType.INT,
        "浮点": TokenType.FLOAT,
        "字符": TokenType.CHAR,
        "布尔": TokenType.BOOL,
        "字符串": TokenType.STRING,
        "字节": TokenType.BYTE,
        "双精度": TokenType.DOUBLE,
        "长整数": TokenType.LONG,
        "短整数": TokenType.SHORT,
        # 修饰符关键字
        "易变": TokenType.VOLATILE,
        "注册": TokenType.REGISTER,
        "内联": TokenType.INLINE,
        # 复合类型关键字
        "共用体": TokenType.UNION,
        "别名": TokenType.TYPEDEF,
        "枚举": TokenType.ENUM,
        "去向": TokenType.GOTO,
        # 流程控制关键字
        "如果": TokenType.IF,
        "否则": TokenType.ELSE,
        "当": TokenType.WHILE,
        "循环": TokenType.FOR,
        "执行": TokenType.DO,
        "跳出": TokenType.BREAK,
        "继续": TokenType.CONTINUE,
        "返回": TokenType.RETURN,
        "选择": TokenType.SWITCH,
        "情况": TokenType.CASE,
        "默认": TokenType.DEFAULT,
        # 定义关键字
        "函数": TokenType.FUNCTION,
        "结构体": TokenType.STRUCT,
        "常量": TokenType.CONST,
        "静态": TokenType.STATIC,
        "外部": TokenType.EXTERN,
        # 模块关键字
        "模块": TokenType.MODULE,
        "导入": TokenType.IMPORT,
        "公开": TokenType.EXPORT,
        "私有": TokenType.PRIVATE,
        # 特殊值
        "真": TokenType.TRUE,
        "假": TokenType.FALSE,
        "空": TokenType.NULL,
        "空指针": TokenType.NULL,
        # 自动类型推导关键字
        "自动": TokenType.AUTO,
        "自动型": TokenType.AUTO,
        # 泛型关键字
        "泛型类型": TokenType.GENERIC_TYPE,
        "泛型函数": TokenType.GENERIC_FUNC,
        "类型": TokenType.TYPE_PARAM,
        "约束": TokenType.CONSTRAINT,
        "其中": TokenType.WHERE,
        # 模式匹配关键字
        "匹配": TokenType.MATCH,
        # 注意：'当' 已经在流程控制关键字中定义为 WHILE (第214行)
        # 模式匹配中的 '当' 用于守卫表达式，复用 CASE token
        # 但由于字典不允许重复键，这里不再重复定义
        # 异步编程关键字
        "异步": TokenType.ASYNC,
        "等待": TokenType.AWAIT,
        "未来": TokenType.FUTURE,
        "任务": TokenType.TASK,
        "承诺": TokenType.PROMISE,
        "让出": TokenType.YIELD,
        "协程": TokenType.COROUTINE,
        "通道": TokenType.CHANNEL,
        "启动": TokenType.SPAWN,
        # 异常处理关键字
        "尝试": TokenType.TRY,
        "捕获": TokenType.CATCH,
        "最终": TokenType.FINALLY,
        "抛出": TokenType.THROW,
        "异常": TokenType.EXCEPTION,
        "异常类": TokenType.EXCEPTION_CLASS,
    }

    def __init__(self, source: str):
        """初始化词法分析器

        Args:
            source: 源代码字符串
        """
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.errors: List[LexerError] = []
        self.generic_angle_count = 0  # 泛型嵌套层级计数器

    def current_char(self) -> Optional[str]:
        """获取当前字符"""
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]

    def peek_char(self, offset: int = 1) -> Optional[str]:
        """查看偏移位置的字符"""
        pos = self.pos + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]

    def advance(self) -> Optional[str]:
        """前进一个字符"""
        char = self.current_char()
        if char:
            self.pos += 1
            if char == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        return char

    def _is_valid_unicode(self, char: str) -> bool:
        """检查字符是否是有效的 Unicode 字符

        Args:
            char: 单个字符

        Returns:
            是否有效
        """
        try:
            char.encode("utf-8")
            return True
        except UnicodeEncodeError:
            return False

    def skip_whitespace(self):
        """跳过空白字符"""
        while self.current_char() and self.current_char().isspace():
            self.advance()

    def skip_comment(self):
        """跳过注释"""
        # 单行注释 //
        if self.current_char() == "/" and self.peek_char() == "/":
            self.advance()  # /
            self.advance()  # /
            while self.current_char() and self.current_char() != "\n":
                self.advance()
            return True

        # 多行注释 /* */
        if self.current_char() == "/" and self.peek_char() == "*":
            self.advance()  # /
            self.advance()  # *
            while self.current_char():
                if self.current_char() == "*" and self.peek_char() == "/":
                    self.advance()  # *
                    self.advance()  # /
                    return True
                self.advance()
            # 未闭合的多行注释
            error = unterminated_comment(
                location=SourceLocation(line=self.line, column=self.column)
            )
            self.errors.append(error)
            return True

        return False

    def read_number(self) -> Token:
        """读取数字"""
        start_line = self.line
        start_column = self.column
        value = ""
        is_float = False

        # 读取整数部分
        while self.current_char() and self.current_char().isdigit():
            value += self.advance()

        # 检查是否是浮点数或范围操作符
        if self.current_char() == "." and self.peek_char() and self.peek_char() != ".":
            # 浮点数：点后面不是另一个点
            value += self.advance()  # 消费 '.'
            is_float = True
            while self.current_char() and self.current_char().isdigit():
                value += self.advance()

        # 科学计数法
        if self.current_char() and self.current_char().lower() == "e":
            value += self.advance()
            if self.current_char() and self.current_char() in "+-":
                value += self.advance()
            while self.current_char() and self.current_char().isdigit():
                value += self.advance()

        if is_float:
            return Token(TokenType.FLOAT_LITERAL, value, start_line, start_column)
        else:
            return Token(TokenType.INT_LITERAL, value, start_line, start_column)

    def read_string(self) -> Token:
        """读取字符串字面量或字符字面量

        支持的转义序列:
        - \\n: 换行符
        - \\t: 制表符
        - \\\\ : 反斜杠
        - \\0: 空字符
        - \\' / \\": 引号
        - \\xNN: 十六进制转义 (0x00-0xFF)
        - \\NNN: 八进制转义 (0-377)
        - \\e: ESC 字符 (ANSI 转义序列开始)
        - \\a: 响铃
        - \\b: 退格
        - \\f: 换页
        - \\v: 垂直制表符
        - \\r: 回车
        - \\uNNNN: Unicode 转义 (4位十六进制)
        - \\UNNNNNNNN: Unicode 转义 (8位十六进制)

        支持全角引号:
        - 『...』: 全角书名号，引号内为字符串
        - 「...」: 全角方括号，引号内为字符串
        """
        start_line = self.line
        start_column = self.column
        quote = self.advance()  # ' 或 " 或 『 或 「
        value = ""
        # 判断引号类型
        is_char = quote == "'"
        is_fullwidth = quote in ("『", "「")
        # 确定闭合引号
        close_quote = quote
        if quote == "「":
            close_quote = "」"
        elif quote == "『":
            close_quote = "』"
        # 全角引号内的字符不是字符字面量
        is_char = is_char and not is_fullwidth

        while self.current_char() and self.current_char() != close_quote:
            if self.current_char() == "\\":
                self.advance()  # \
                char = self.current_char()

                # 十六进制转义: \xNN (1-2个十六进制数字)
                if char == "x":
                    hex_value = ""
                    for _ in range(2):  # 最多2个十六进制数字
                        next_char = self.peek_char()
                        if next_char and next_char in "0123456789abcdefABCDEF":
                            hex_value += next_char
                            self.advance()
                        else:
                            break

                    if hex_value:
                        try:
                            byte_val = int(hex_value, 16)
                            # 检查是否超出有效范围 (0x00-0xFF)
                            if byte_val > 0xFF:
                                # 截断到有效范围并警告
                                byte_val = 0xFF
                            value += chr(byte_val)
                        except ValueError:
                            value += "\\x" + hex_value
                    else:
                        # \x 后无十六进制数字，报错
                        error = invalid_escape_sequence(
                            sequence="\\x",
                            location=SourceLocation(
                                line=self.line, column=self.column - 1
                            ),
                        )
                        self.errors.append(error)
                        value += "\\x"
                    self.advance()

                # 八进制转义: \NNN (1-3个八进制数字, 0-377)
                elif char and char.isdigit():
                    octal_value = ""
                    for _ in range(3):  # 最多3个八进制数字
                        if char and char in "01234567":
                            octal_value += char
                            self.advance()
                            char = self.current_char()
                        else:
                            break

                    if octal_value:
                        try:
                            byte_val = int(octal_value, 8)
                            # 八进制最大值是 377 (十进制 255)
                            if byte_val > 255:
                                byte_val = 255
                            value += chr(byte_val)
                        except ValueError:
                            value += "\\" + octal_value
                    else:
                        value += "\\"
                        if char:
                            value += char
                            self.advance()

                # ESC 转义序列开始字符 (ANSI 支持)
                elif char == "e" or char == "E":
                    value += "\x1b"  # ESC 字符
                    self.advance()

                elif char == "n":
                    value += "\n"
                    self.advance()
                elif char == "t":
                    value += "\t"
                    self.advance()
                elif char == "\\":
                    value += "\\"
                    self.advance()
                elif char == "0":
                    value += "\0"
                    self.advance()
                elif char == "a":
                    value += "\a"
                    self.advance()
                elif char == "b":
                    value += "\b"
                    self.advance()
                elif char == "f":
                    value += "\f"
                    self.advance()
                elif char == "v":
                    value += "\v"
                    self.advance()
                elif char == "r":
                    value += "\r"
                    self.advance()
                elif char == quote:
                    # 对于半角引号，处理 \" 或 \' 转义
                    value += quote
                    self.advance()
                elif char == close_quote and is_fullwidth:
                    # 对于全角引号，处理转义的全角引号
                    value += close_quote
                    self.advance()
                elif char == "u" or char == "U":
                    # Unicode 转义
                    # \\uNNNN 或 \\UNNNNNNNN
                    unicode_val = ""
                    max_len = 4 if char == "u" else 8
                    for _ in range(max_len):
                        next_char = self.peek_char()
                        if next_char and next_char in "0123456789abcdefABCDEF":
                            unicode_val += next_char
                            self.advance()
                        else:
                            break
                    if unicode_val:
                        try:
                            code_point = int(unicode_val, 16)
                            if code_point <= 0x10FFFF:
                                value += chr(code_point)
                            else:
                                value += "\\" + char + unicode_val
                        except ValueError:
                            value += "\\" + char + unicode_val
                    else:
                        value += "\\" + char
                    self.advance()
                else:
                    # 未知转义序列，保留原样
                    value += "\\"
                    if char:
                        value += char
                        self.advance()
            else:
                # 验证字符是否为有效的 Unicode
                char = self.advance()
                if char and not self._is_valid_unicode(char):
                    error = invalid_unicode_character(
                        character=char,
                        location=SourceLocation(line=self.line, column=self.column - 1),
                    )
                    self.errors.append(error)
                value += char or ""

        if not self.current_char():
            if is_char:
                error = unterminated_char(
                    location=SourceLocation(line=start_line, column=start_column)
                )
                self.errors.append(error)
                return Token(
                    TokenType.CHAR_LITERAL,
                    value,
                    start_line,
                    start_column,
                    end_line=self.line,
                    end_column=self.column,
                )
            else:
                error = unterminated_string(
                    location=SourceLocation(line=start_line, column=start_column)
                )
                self.errors.append(error)
                return Token(
                    TokenType.STRING_LITERAL,
                    value,
                    start_line,
                    start_column,
                    end_line=self.line,
                    end_column=self.column,
                )

        self.advance()  # 闭合引号

        if is_char:
            return Token(
                TokenType.CHAR_LITERAL,
                value,
                start_line,
                start_column,
                end_line=self.line,
                end_column=self.column,
            )
        else:
            return Token(
                TokenType.STRING_LITERAL,
                value,
                start_line,
                start_column,
                end_line=self.line,
                end_column=self.column,
            )

    def read_multiline_string(self) -> Token:
        """读取多行字符串字面量

        多行字符串使用三个双引号包裹：
        字符串型 s = \"\"\"
            第一行
            第二行
        \"\"\";

        多行字符串保留原始换行和缩进。
        """
        start_line = self.line
        start_column = self.column

        # 消费三个双引号
        self.advance()  # 第一个 "
        self.advance()  # 第二个 "
        self.advance()  # 第三个 "

        value = ""

        # 读取内容直到遇到 """
        while self.current_char():
            # 检查是否到达结束标记
            if (
                self.current_char() == '"'
                and self.peek_char() == '"'
                and self.peek_char(2) == '"'
            ):
                self.advance()  # 第一个 "
                self.advance()  # 第二个 "
                self.advance()  # 第三个 "
                return Token(
                    TokenType.STRING_LITERAL,
                    value,
                    start_line,
                    start_column,
                    end_line=self.line,
                    end_column=self.column,
                )

            # 处理换行
            if self.current_char() == "\n":
                value += "\n"
                self.advance()
                continue

            # 处理转义序列（与普通字符串相同）
            if self.current_char() == "\\":
                self.advance()  # \
                char = self.current_char()

                if char == "n":
                    value += "\n"
                    self.advance()
                elif char == "t":
                    value += "\t"
                    self.advance()
                elif char == "\\":
                    value += "\\"
                    self.advance()
                elif char == '"':
                    value += '"'
                    self.advance()
                elif char == "r":
                    value += "\r"
                    self.advance()
                elif char == "u" or char == "U":
                    # Unicode 转义
                    unicode_val = ""
                    max_len = 4 if char == "u" else 8
                    for _ in range(max_len):
                        next_char = self.peek_char()
                        if next_char and next_char in "0123456789abcdefABCDEF":
                            unicode_val += next_char
                            self.advance()
                        else:
                            break
                    if unicode_val:
                        try:
                            code_point = int(unicode_val, 16)
                            if code_point <= 0x10FFFF:
                                value += chr(code_point)
                            else:
                                value += "\\" + char + unicode_val
                        except ValueError:
                            value += "\\" + char + unicode_val
                    else:
                        value += "\\" + char
                    self.advance()
                else:
                    # 其他转义序列保留原样
                    value += "\\"
                    if char:
                        value += char
                        self.advance()
            else:
                # 普通字符
                char = self.advance()
                if char and not self._is_valid_unicode(char):
                    error = invalid_unicode_character(
                        character=char,
                        location=SourceLocation(line=self.line, column=self.column - 1),
                    )
                    self.errors.append(error)
                value += char or ""

        # 未闭合的多行字符串
        error = unterminated_string(
            location=SourceLocation(line=start_line, column=start_column)
        )
        self.errors.append(error)
        return Token(
            TokenType.STRING_LITERAL,
            value,
            start_line,
            start_column,
            end_line=self.line,
            end_column=self.column,
        )

    def read_wide_literal(self) -> Token:
        """读取宽字符或宽字符串字面量

        支持的语法:
        - L'字符' - 宽字符常量
        - L"字符串" - 宽字符串常量
        - 宽'字符' - 宽字符常量（中文前缀）
        - 宽"字符串" - 宽字符串常量（中文前缀）

        宽字符/字符串返回 Unicode 码点列表作为值，
        用于后续生成 LLVM 宽字符类型。
        """
        start_line = self.line
        start_column = self.column

        # 检查前缀
        is_wide_prefix = False
        if self.current_char() == "L":
            self.advance()  # 消费 L
            is_wide_prefix = True
        elif self.current_char() == "宽":
            self.advance()  # 消费 宽
            is_wide_prefix = True

        if not is_wide_prefix:
            # 如果没有 L 或 宽 前缀，调用 read_string
            return self.read_string()

        # 读取引号
        quote = self.current_char()
        if quote not in ("'", '"', "『", "「"):
            # 不是有效的字面量，调用 read_string
            return self.read_string()

        is_char = quote == "'"
        close_quote = quote
        if quote == "「":
            close_quote = "」"
        elif quote == "『":
            close_quote = "』"

        self.advance()  # 消费开引号

        # 读取内容并转换为 Unicode 码点列表
        codepoints = []
        char_value = ""

        while self.current_char() and self.current_char() != close_quote:
            if self.current_char() == "\\":
                self.advance()  # \
                char = self.current_char()

                if char == "n":
                    codepoints.append(ord("\n"))
                    char_value += "\\n"
                    self.advance()
                elif char == "t":
                    codepoints.append(ord("\t"))
                    char_value += "\\t"
                    self.advance()
                elif char == "\\":
                    codepoints.append(ord("\\"))
                    char_value += "\\\\"
                    self.advance()
                elif char == "0":
                    codepoints.append(0)  # null 字符
                    char_value += "\\0"
                    self.advance()
                elif char == "'":
                    codepoints.append(ord("'"))
                    char_value += "\\'"
                    self.advance()
                elif char == '"':
                    codepoints.append(ord('"'))
                    char_value += '\\"'
                    self.advance()
                elif char == "u" or char == "U":
                    # Unicode 转义
                    unicode_val = ""
                    max_len = 4 if char == "u" else 8
                    for _ in range(max_len):
                        next_char = self.peek_char()
                        if next_char and next_char in "0123456789abcdefABCDEF":
                            unicode_val += next_char
                            self.advance()
                        else:
                            break
                    if unicode_val:
                        try:
                            code_point = int(unicode_val, 16)
                            if code_point <= 0x10FFFF:
                                codepoints.append(code_point)
                                char_value += chr(code_point)
                            else:
                                char_value += "\\" + char + unicode_val
                        except ValueError:
                            char_value += "\\" + char + unicode_val
                    self.advance()
                else:
                    char_value += "\\"
                    if char:
                        char_value += char
                        self.advance()
            else:
                char = self.current_char()
                codepoints.append(ord(char))
                char_value += char
                self.advance()

        # 检查是否闭合
        if not self.current_char():
            if is_char:
                error = unterminated_char(
                    location=SourceLocation(line=start_line, column=start_column)
                )
                self.errors.append(error)
                return Token(
                    TokenType.WIDE_CHAR_LITERAL,
                    char_value,
                    start_line,
                    start_column,
                    end_line=self.line,
                    end_column=self.column,
                )
            else:
                error = unterminated_string(
                    location=SourceLocation(line=start_line, column=start_column)
                )
                self.errors.append(error)
                return Token(
                    TokenType.WIDE_STRING_LITERAL,
                    codepoints,
                    start_line,
                    start_column,
                    end_line=self.line,
                    end_column=self.column,
                )

        self.advance()  # 消费闭引号

        if is_char:
            # 宽字符：返回第一个码点
            return Token(
                TokenType.WIDE_CHAR_LITERAL,
                codepoints[0] if codepoints else 0,
                start_line,
                start_column,
                end_line=self.line,
                end_column=self.column,
            )
        else:
            # 宽字符串：返回码点列表
            return Token(
                TokenType.WIDE_STRING_LITERAL,
                codepoints,
                start_line,
                start_column,
                end_line=self.line,
                end_column=self.column,
            )

    def read_identifier(self) -> Token:
        """读取标识符"""
        start_line = self.line
        start_column = self.column
        value = ""

        # 读取标识符（支持中文）
        while self.current_char() and (
            self.current_char().isalnum()
            or self.current_char() == "_"
            or "\u4e00" <= self.current_char() <= "\u9fff"
        ):
            value += self.advance()

        # 特殊处理下划线：单独的下划线是通配符模式
        if value == "_":
            return Token(TokenType.UNDERSCORE, "_", start_line, start_column)

        # 检查是否是关键字
        token_type = self.KEYWORDS.get(value, TokenType.IDENTIFIER)
        return Token(token_type, value, start_line, start_column)

    def read_operator(self) -> Optional[Token]:
        """读取运算符

        注意：< 和 > 在泛型上下文中作为泛型分隔符，
        在其他上下文中作为比较运算符。
        词法分析器统一产生 LT/GT Token，由语法分析器根据上下文判断。

        特殊处理：嵌套泛型类型中的 >> 会被拆分为两个 GT
        """
        start_line = self.line
        start_column = self.column
        char = self.current_char()

        # 双字符运算符
        if self.peek_char():
            two_char = char + self.peek_char()

            # 三字符运算符 - 必须在双字符运算符之前检查，以免 "..." 被 ".." 提前匹配
            if self.peek_char(2):
                three_char = char + self.peek_char() + self.peek_char(2)
                if three_char == "...":
                    self.advance()
                    self.advance()
                    self.advance()
                    return Token(TokenType.ELLIPSIS, "...", start_line, start_column)

            # 特殊处理：嵌套泛型类型中的 >> 拆分为两个 GT
            if two_char == ">>" and self.generic_angle_count >= 2:
                # 拆分为两个 GT
                self.advance()  # 第一个 >
                token1 = Token(TokenType.GT, ">", start_line, start_column)
                self.generic_angle_count -= 1

                # 第二个 > 在下一个 tokenize 循环中处理
                return token1

            operators = {
                "==": TokenType.EQ,
                "!=": TokenType.NE,
                "<=": TokenType.LE,
                ">=": TokenType.GE,
                "&&": TokenType.AND,
                "||": TokenType.OR,
                "++": TokenType.INCREMENT,
                "--": TokenType.DECREMENT,
                "+=": TokenType.PLUS_ASSIGN,
                "-=": TokenType.MINUS_ASSIGN,
                "*=": TokenType.STAR_ASSIGN,
                "/=": TokenType.SLASH_ASSIGN,
                "%=": TokenType.PERCENT_ASSIGN,
                "<<": TokenType.LSHIFT,
                ">>": TokenType.RSHIFT,
                "->": TokenType.ARROW,
                "..": TokenType.DOTDOT,  # 范围操作符
                "=>": TokenType.FAT_ARROW,  # 匹配分支箭头
            }

            # 双字符运算符
            if two_char in operators:
                self.advance()
                self.advance()
                return Token(operators[two_char], two_char, start_line, start_column)

        # 单字符运算符
        # < 和 > 统一作为 LT/GT，语法分析器根据上下文判断是否为泛型
        operators = {
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.SLASH,
            "%": TokenType.PERCENT,
            "<": TokenType.LT,  # 泛型分隔符或小于运算符
            ">": TokenType.GT,  # 泛型分隔符或大于运算符
            "=": TokenType.ASSIGN,
            "!": TokenType.NOT,
            "&": TokenType.BIT_AND,
            "|": TokenType.BIT_OR,
            "^": TokenType.BIT_XOR,
            "~": TokenType.BIT_NOT,
        }

        if char in operators:
            self.advance()
            return Token(operators[char], char, start_line, start_column)

        return None

    def read_delimiter(self) -> Optional[Token]:
        """读取分隔符"""
        start_line = self.line
        start_column = self.column
        char = self.current_char()

        delimiters = {
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
            "[": TokenType.LBRACKET,
            "]": TokenType.RBRACKET,
            ";": TokenType.SEMICOLON,
            ",": TokenType.COMMA,
            ":": TokenType.COLON,
            ".": TokenType.DOT,
        }

        if char in delimiters:
            self.advance()
            return Token(delimiters[char], char, start_line, start_column)

        return None

    def tokenize(self) -> List[Token]:
        """执行词法分析

        Returns:
            Token列表
        """
        while self.current_char():
            # 跳过空白
            self.skip_whitespace()

            if not self.current_char():
                break

            # 跳过注释
            if self.skip_comment():
                continue

            # 数字
            if self.current_char().isdigit():
                self.tokens.append(self.read_number())
                continue

            # 多行字符串（\"\"\"）
            if (
                self.current_char() == '"'
                and self.peek_char() == '"'
                and self.peek_char(2) == '"'
            ):
                self.tokens.append(self.read_multiline_string())
                continue

            # 宽字符字面量 L'...' 或 L"..." 或 宽'...' 或 宽"..."
            if self.current_char() == "L" and self.peek_char() in "\"'":
                self.tokens.append(self.read_wide_literal())
                continue

            # 宽字符字面量（中文前缀 "宽"）
            if self.current_char() == "宽" and self.peek_char() in "\"'「『":
                self.tokens.append(self.read_wide_literal())
                continue

            # 字符串（支持全角引号）
            if self.current_char() in "\"'「『":
                self.tokens.append(self.read_string())
                continue

            # 标识符或关键字
            if (
                self.current_char().isalpha()
                or self.current_char() == "_"
                or "\u4e00" <= self.current_char() <= "\u9fff"
            ):
                self.tokens.append(self.read_identifier())
                continue

            # 运算符
            token = self.read_operator()
            if token:
                self.tokens.append(token)
                # 更新泛型嵌套层级计数器
                if token.type == TokenType.LT:
                    self.generic_angle_count += 1
                elif token.type == TokenType.GT:
                    self.generic_angle_count -= 1
                continue

            # 分隔符
            token = self.read_delimiter()
            if token:
                self.tokens.append(token)
                continue

            # 未知字符
            error = illegal_character(
                character=self.current_char(),
                location=SourceLocation(line=self.line, column=self.column),
            )
            self.errors.append(error)
            self.advance()

        # 添加EOF
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))

        return self.tokens

    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0

    def get_errors(self) -> List[LexerError]:
        """获取错误列表"""
        return self.errors

    def get_source_context(self, line: int, column: int, context_lines: int = 2) -> str:
        """获取错误位置的源代码上下文

        Args:
            line: 行号
            column: 列号
            context_lines: 上下文行数（前后各几行）

        Returns:
            包含上下文的源代码字符串
        """
        source_lines = self.source.split("\n")

        # 确保行号在有效范围内
        if line < 1 or line > len(source_lines):
            return ""

        # 计算上下文范围
        start_line = max(0, line - context_lines - 1)
        end_line = min(len(source_lines), line + context_lines)

        context_parts = []
        for i in range(start_line, end_line):
            line_num = i + 1
            line_content = source_lines[i]

            # 标记错误位置
            if line_num == line:
                # 在行内容中标记错误列
                marker = " " * (column - 1) + "^"
                context_parts.append(f"{line_num:4d}: {line_content}")
                context_parts.append(f"     {marker}")
            else:
                context_parts.append(f"{line_num:4d}: {line_content}")

        return "\n".join(context_parts)

    def format_error_message(self, error: LexerError, context_lines: int = 2) -> str:
        """格式化错误消息，包含源代码上下文

        Args:
            error: 词法错误
            context_lines: 上下文行数

        Returns:
            格式化后的错误消息
        """
        parts = []

        # 错误位置
        if error.location:
            parts.append(
                f"--> {error.location.file_path or '<unknown>'}:{error.location.line}:{error.location.column}"
            )
        else:
            parts.append(
                f"--> 行号: {error.location.line if error.location else '?'}:{error.location.column if error.location else '?'}"
            )

        # 错误代码
        if error.error_code:
            parts.append("   |")

        # 源代码上下文
        if error.location:
            context = self.get_source_context(
                error.location.line, error.location.column, context_lines
            )
            if context:
                parts.append(context)
                parts.append("")

        # 错误消息
        parts.append(f"error: {error.message}")

        # 额外信息
        if error.character:
            parts.append(
                f"  发现的字符: '{error.character}' (U+{ord(error.character):04X})"
            )

        if error.suggestion:
            parts.append(f"  建议: {error.suggestion}")

        return "\n".join(parts)

    def report(self) -> str:
        """生成分析报告"""
        lines = [
            "=" * 70,
            "词法分析报告",
            "=" * 70,
            "",
            f"源代码长度: {len(self.source)} 字符",
            f"Token数量: {len(self.tokens)}",
            f"错误数量: {len(self.errors)}",
            "",
        ]

        if self.errors:
            lines.append("错误列表:")
            lines.append("-" * 70)
            for error in self.errors:
                lines.append(f"  ✗ {error}")
            lines.append("")

        lines.append("Token列表:")
        lines.append("-" * 70)

        for i, token in enumerate(self.tokens[:20]):  # 只显示前20个
            lines.append(f"  {i:3d}. {token}")

        if len(self.tokens) > 20:
            lines.append(f"  ... (还有 {len(self.tokens) - 20} 个Token)")

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)


def tokenize(source: str) -> Tuple[List[Token], List[LexerError]]:
    """词法分析便捷函数

    Args:
        source: 源代码字符串

    Returns:
        (Token列表, 错误列表)
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    return tokens, lexer.get_errors()


if __name__ == "__main__":
    # 测试示例
    test_code = """
    // 测试程序
    整数型 主函数() {
        整数型 计数 = 0;
        浮点型 数值 = 3.14;

        如果 (计数 < 10) {
            计数 += 1;
        } 否则 {
            计数 -= 1;
        }

        返回 0;
    }
    """

    lexer = Lexer(test_code)
    tokens = lexer.tokenize()

    print(lexer.report())

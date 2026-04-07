#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
词法分析器 - Lexer
将ZHC源代码转换为Token流

作者: 阿福
日期: 2026-04-03
"""

import re
from enum import Enum, auto
from typing import List, Optional, Tuple
from dataclasses import dataclass

# 导入统一异常类
from zhc.errors import (
    LexerError,
    ErrorCollection,
    SourceLocation,
    illegal_character,
    unterminated_string,
    unterminated_comment,
    unterminated_char,
)


class TokenType(Enum):
    """Token类型枚举"""
    
    # 关键字
    # 类型关键字
    INT = auto()          # 整数型
    FLOAT = auto()        # 浮点型
    CHAR = auto()         # 字符型
    BOOL = auto()         # 布尔型
    VOID = auto()         # 空型
    STRING = auto()       # 字符串型
    BYTE = auto()         # 字节型
    DOUBLE = auto()       # 双精度浮点型
    BOOL_TYPE = auto()    # 逻辑型 (_Bool)
    LONG = auto()         # 长整数型
    SHORT = auto()        # 短整数型
    UNSIGNED = auto()     # 无符号
    SIGNED = auto()       # 有符号

    # 修饰符关键字
    VOLATILE = auto()     # 易变
    REGISTER = auto()     # 注册
    INLINE = auto()       # 内联

    # 复合类型关键字
    UNION = auto()        # 共用体
    ENUM = auto()         # 枚举
    TYPEDEF = auto()      # 别名
    GOTO = auto()         # 去向

    # 流程控制关键字
    IF = auto()           # 如果
    ELSE = auto()         # 否则
    WHILE = auto()        # 当
    FOR = auto()          # 循环
    DO = auto()           # 执行
    BREAK = auto()        # 跳出
    CONTINUE = auto()     # 继续
    RETURN = auto()        # 返回
    SWITCH = auto()       # 选择
    CASE = auto()         # 情况
    DEFAULT = auto()      # 默认
    
    # 定义关键字
    FUNCTION = auto()     # 函数
    STRUCT = auto()       # 结构体
    CONST = auto()        # 常量
    STATIC = auto()       # 静态
    EXTERN = auto()       # 外部
    
    # 模块关键字
    MODULE = auto()       # 模块
    IMPORT = auto()       # 导入
    EXPORT = auto()       # 公开
    PRIVATE = auto()      # 私有
    
    # 特殊值
    TRUE = auto()         # 真
    FALSE = auto()        # 假
    NULL = auto()         # 空
    
    # 标识符和字面量
    IDENTIFIER = auto()   # 标识符
    INT_LITERAL = auto()  # 整数字面量
    FLOAT_LITERAL = auto() # 浮点字面量
    STRING_LITERAL = auto() # 字符串字面量
    CHAR_LITERAL = auto()  # 字符字面量
    
    # 运算符
    PLUS = auto()         # +
    MINUS = auto()        # -
    STAR = auto()         # *
    SLASH = auto()        # /
    PERCENT = auto()      # %
    
    PLUS_ASSIGN = auto()    # +=
    MINUS_ASSIGN = auto()   # -=
    STAR_ASSIGN = auto()    # *=
    SLASH_ASSIGN = auto()   # /=
    PERCENT_ASSIGN = auto() # %=
    
    EQ = auto()           # ==
    NE = auto()           # !=
    LT = auto()           # <
    LE = auto()           # <=
    GT = auto()           # >
    GE = auto()           # >=
    
    AND = auto()          # &&
    OR = auto()           # ||
    NOT = auto()          # !
    
    BIT_AND = auto()      # &
    BIT_OR = auto()       # |
    BIT_XOR = auto()      # ^
    BIT_NOT = auto()      # ~
    LSHIFT = auto()       # <<
    RSHIFT = auto()       # >>
    
    ASSIGN = auto()       # =
    ARROW = auto()        # ->
    DOT = auto()          # .
    
    INCREMENT = auto()    # ++
    DECREMENT = auto()    # --
    
    # 分隔符
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    LBRACE = auto()       # {
    RBRACE = auto()       # }
    LBRACKET = auto()     # [
    RBRACKET = auto()     # ]
    SEMICOLON = auto()    # ;
    COMMA = auto()        # ,
    COLON = auto()        # :
    
    # 泛型相关分隔符
    LANGLE = auto()       # < (泛型参数开始)
    RANGLE = auto()       # > (泛型参数结束)
    
    # 泛型关键字
    GENERIC_TYPE = auto()    # 泛型类型
    GENERIC_FUNC = auto()    # 泛型函数
    TYPE_PARAM = auto()      # 类型
    CONSTRAINT = auto()      # 约束
    WHERE = auto()           # 其中 (where clause)
    
    # 模式匹配关键字
    MATCH = auto()           # 匹配
    UNDERSCORE = auto()      # _ (通配符)
    DOTDOT = auto()          # .. (范围操作符)
    FAT_ARROW = auto()       # => (匹配分支箭头)
    
    # 异步编程关键字
    ASYNC = auto()           # 异步
    AWAIT = auto()           # 等待
    FUTURE = auto()          # 未来
    TASK = auto()            # 任务
    PROMISE = auto()         # 承诺
    YIELD = auto()           # 让出
    
    # 特殊
    EOF = auto()          # 文件结束
    UNKNOWN = auto()      # 未知字符


@dataclass
class Token:
    """Token类"""
    type: TokenType
    value: str
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}', {self.line}:{self.column})"


class Lexer:
    """词法分析器"""
    
    # 关键字映射
    KEYWORDS = {
        # 类型关键字（完整形式）
        '整数型': TokenType.INT,
        '浮点型': TokenType.FLOAT,
        '字符型': TokenType.CHAR,
        '布尔型': TokenType.BOOL,
        '空型': TokenType.VOID,
        '字符串型': TokenType.STRING,
        '字节型': TokenType.BYTE,
        '双精度浮点型': TokenType.DOUBLE,
        '逻辑型': TokenType.BOOL_TYPE,
        '长整数型': TokenType.LONG,
        '短整数型': TokenType.SHORT,
        '无类型': TokenType.VOID,
        '无符号': TokenType.UNSIGNED,
        '有符号': TokenType.SIGNED,
        
        # 类型关键字（简写形式）
        '整数': TokenType.INT,
        '浮点': TokenType.FLOAT,
        '字符': TokenType.CHAR,
        '布尔': TokenType.BOOL,
        '字符串': TokenType.STRING,
        '字节': TokenType.BYTE,
        '双精度': TokenType.DOUBLE,
        '长整数': TokenType.LONG,
        '短整数': TokenType.SHORT,

        # 修饰符关键字
        '易变': TokenType.VOLATILE,
        '注册': TokenType.REGISTER,
        '内联': TokenType.INLINE,

        # 复合类型关键字
        '共用体': TokenType.UNION,
        '别名': TokenType.TYPEDEF,
        '枚举': TokenType.ENUM,
        '去向': TokenType.GOTO,

        # 流程控制关键字
        '如果': TokenType.IF,
        '否则': TokenType.ELSE,
        '当': TokenType.WHILE,
        '循环': TokenType.FOR,
        '执行': TokenType.DO,
        '跳出': TokenType.BREAK,
        '继续': TokenType.CONTINUE,
        '返回': TokenType.RETURN,
        '选择': TokenType.SWITCH,
        '情况': TokenType.CASE,
        '默认': TokenType.DEFAULT,
        
        # 定义关键字
        '函数': TokenType.FUNCTION,
        '结构体': TokenType.STRUCT,
        '常量': TokenType.CONST,
        '静态': TokenType.STATIC,
        '外部': TokenType.EXTERN,
        
        # 模块关键字
        '模块': TokenType.MODULE,
        '导入': TokenType.IMPORT,
        '公开': TokenType.EXPORT,
        '私有': TokenType.PRIVATE,
        
        # 特殊值
        '真': TokenType.TRUE,
        '假': TokenType.FALSE,
        '空': TokenType.NULL,
        '空指针': TokenType.NULL,
        
        # 泛型关键字
        '泛型类型': TokenType.GENERIC_TYPE,
        '泛型函数': TokenType.GENERIC_FUNC,
        '类型': TokenType.TYPE_PARAM,
        '约束': TokenType.CONSTRAINT,
        '其中': TokenType.WHERE,
        
        # 模式匹配关键字
        '匹配': TokenType.MATCH,
        # 注意：'当' 已经在流程控制关键字中定义为 WHILE (第214行)
        # 模式匹配中的 '当' 用于守卫表达式，复用 CASE token
        # 但由于字典不允许重复键，这里不再重复定义
        
        # 异步编程关键字
        '异步': TokenType.ASYNC,
        '等待': TokenType.AWAIT,
        '未来': TokenType.FUTURE,
        '任务': TokenType.TASK,
        '承诺': TokenType.PROMISE,
        '让出': TokenType.YIELD,
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
            if char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        return char
    
    def skip_whitespace(self):
        """跳过空白字符"""
        while self.current_char() and self.current_char().isspace():
            self.advance()
    
    def skip_comment(self):
        """跳过注释"""
        # 单行注释 //
        if self.current_char() == '/' and self.peek_char() == '/':
            self.advance()  # /
            self.advance()  # /
            while self.current_char() and self.current_char() != '\n':
                self.advance()
            return True
        
        # 多行注释 /* */
        if self.current_char() == '/' and self.peek_char() == '*':
            self.advance()  # /
            self.advance()  # *
            while self.current_char():
                if self.current_char() == '*' and self.peek_char() == '/':
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
        if self.current_char() == '.' and self.peek_char() and self.peek_char() != '.':
            # 浮点数：点后面不是另一个点
            value += self.advance()  # 消费 '.'
            is_float = True
            while self.current_char() and self.current_char().isdigit():
                value += self.advance()
        
        # 科学计数法
        if self.current_char() and self.current_char().lower() == 'e':
            value += self.advance()
            if self.current_char() and self.current_char() in '+-':
                value += self.advance()
            while self.current_char() and self.current_char().isdigit():
                value += self.advance()
        
        if is_float:
            return Token(TokenType.FLOAT_LITERAL, value, start_line, start_column)
        else:
            return Token(TokenType.INT_LITERAL, value, start_line, start_column)
    
    def read_string(self) -> Token:
        """读取字符串字面量或字符字面量"""
        start_line = self.line
        start_column = self.column
        quote = self.advance()  # ' 或 "
        value = ""
        is_char = (quote == '\'')

        while self.current_char() and self.current_char() != quote:
            if self.current_char() == '\\':
                self.advance()  # \
                char = self.current_char()
                if char == 'n':
                    value += '\n'
                elif char == 't':
                    value += '\t'
                elif char == '\\':
                    value += '\\'
                elif char == '0':
                    value += '\0'
                elif char == quote:
                    value += quote
                else:
                    value += char
                self.advance()
            else:
                value += self.advance()

        if not self.current_char():
            if is_char:
                error = unterminated_char(
                    location=SourceLocation(line=start_line, column=start_column)
                )
                self.errors.append(error)
                return Token(TokenType.CHAR_LITERAL, value, start_line, start_column)
            else:
                error = unterminated_string(
                    location=SourceLocation(line=start_line, column=start_column)
                )
                self.errors.append(error)
                return Token(TokenType.STRING_LITERAL, value, start_line, start_column)

        self.advance()  # 闭合引号

        if is_char:
            return Token(TokenType.CHAR_LITERAL, value, start_line, start_column)
        else:
            return Token(TokenType.STRING_LITERAL, value, start_line, start_column)
    
    def read_identifier(self) -> Token:
        """读取标识符"""
        start_line = self.line
        start_column = self.column
        value = ""
        
        # 读取标识符（支持中文）
        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_' or '\u4e00' <= self.current_char() <= '\u9fff'):
            value += self.advance()
        
        # 特殊处理下划线：单独的下划线是通配符模式
        if value == '_':
            return Token(TokenType.UNDERSCORE, '_', start_line, start_column)
        
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
            
            # 特殊处理：嵌套泛型类型中的 >> 拆分为两个 GT
            if two_char == '>>' and self.generic_angle_count >= 2:
                # 拆分为两个 GT
                self.advance()  # 第一个 >
                token1 = Token(TokenType.GT, '>', start_line, start_column)
                self.generic_angle_count -= 1
                
                # 第二个 > 在下一个 tokenize 循环中处理
                return token1
            
            operators = {
                '==': TokenType.EQ,
                '!=': TokenType.NE,
                '<=': TokenType.LE,
                '>=': TokenType.GE,
                '&&': TokenType.AND,
                '||': TokenType.OR,
                '++': TokenType.INCREMENT,
                '--': TokenType.DECREMENT,
                '+=': TokenType.PLUS_ASSIGN,
                '-=': TokenType.MINUS_ASSIGN,
                '*=': TokenType.STAR_ASSIGN,
                '/=': TokenType.SLASH_ASSIGN,
                '%=': TokenType.PERCENT_ASSIGN,
                '<<': TokenType.LSHIFT,
                '>>': TokenType.RSHIFT,
                '->': TokenType.ARROW,
                '..': TokenType.DOTDOT,      # 范围操作符
                '=>': TokenType.FAT_ARROW,   # 匹配分支箭头
            }
            
            if two_char in operators:
                self.advance()
                self.advance()
                return Token(operators[two_char], two_char, start_line, start_column)
        
        # 单字符运算符
        # < 和 > 统一作为 LT/GT，语法分析器根据上下文判断是否为泛型
        operators = {
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.STAR,
            '/': TokenType.SLASH,
            '%': TokenType.PERCENT,
            '<': TokenType.LT,   # 泛型分隔符或小于运算符
            '>': TokenType.GT,   # 泛型分隔符或大于运算符
            '=': TokenType.ASSIGN,
            '!': TokenType.NOT,
            '&': TokenType.BIT_AND,
            '|': TokenType.BIT_OR,
            '^': TokenType.BIT_XOR,
            '~': TokenType.BIT_NOT,
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
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '{': TokenType.LBRACE,
            '}': TokenType.RBRACE,
            '[': TokenType.LBRACKET,
            ']': TokenType.RBRACKET,
            ';': TokenType.SEMICOLON,
            ',': TokenType.COMMA,
            ':': TokenType.COLON,
        '.': TokenType.DOT,
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
            
            # 字符串
            if self.current_char() in '"\'':
                self.tokens.append(self.read_string())
                continue
            
            # 标识符或关键字
            if self.current_char().isalpha() or self.current_char() == '_' or '\u4e00' <= self.current_char() <= '\u9fff':
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
                location=SourceLocation(line=self.line, column=self.column)
            )
            self.errors.append(error)
            self.advance()
        
        # 添加EOF
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        
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
        source_lines = self.source.split('\n')
        
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
            parts.append(f"--> {error.location.file_path or '<unknown>'}:{error.location.line}:{error.location.column}")
        else:
            parts.append(f"--> 行号: {error.location.line if error.location else '?'}:{error.location.column if error.location else '?'}")
        
        # 错误代码
        if error.error_code:
            parts.append(f"   |")
        
        # 源代码上下文
        if error.location:
            context = self.get_source_context(error.location.line, error.location.column, context_lines)
            if context:
                parts.append(context)
                parts.append("")
        
        # 错误消息
        parts.append(f"error: {error.message}")
        
        # 额外信息
        if error.character:
            parts.append(f"  发现的字符: '{error.character}' (U+{ord(error.character):04X})")
        
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
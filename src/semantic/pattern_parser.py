#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模式匹配语法解析器 - Pattern Parser
将模式匹配语法转换为 Pattern 对象

作者: 阿福
日期: 2026-04-08
"""

from typing import List, Optional, Tuple, Dict, Any
from ..parser.lexer import Token, TokenType, Lexer
from .pattern_matching import (
    Pattern,
    WildcardPattern,
    VariablePattern,
    LiteralPattern,
    ConstructorPattern,
    DestructurePattern,
    RangePattern,
    TuplePattern,
    OrPattern,
    AndPattern,
    GuardPattern,
    PatternType,
)


class PatternParserError(Exception):
    """模式匹配解析错误"""
    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"PatternParserError at {line}:{column}: {message}")


class PatternParser:
    """模式匹配语法解析器
    
    支持的模式类型：
    - 通配符模式: _
    - 变量模式: x
    - 字面量模式: 42, "hello", 真, 假
    - 构造器模式: Some(x), None
    - 解构模式: 点{x, y}
    - 范围模式: 1..10
    - 元组模式: (x, y, z)
    - 或模式: x | y
    - 与模式: x & y
    - 守卫模式: x 当 x > 0
    
    语法示例：
    ```
    匹配 值 {
        0 => "零",
        1..10 => "小",
        11..100 => "中",
        _ => "大"
    }
    ```
    """
    
    def __init__(self, tokens: List[Token]):
        """初始化解析器
        
        Args:
            tokens: Token 列表（从 Lexer 获取）
        """
        self.tokens = tokens
        self.pos = 0
    
    def current_token(self) -> Optional[Token]:
        """获取当前 Token"""
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]
    
    def peek_token(self, offset: int = 1) -> Optional[Token]:
        """查看偏移位置的 Token"""
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return None
        return self.tokens[pos]
    
    def advance(self) -> Optional[Token]:
        """前进一个 Token"""
        token = self.current_token()
        if token:
            self.pos += 1
        return token
    
    def expect(self, token_type: TokenType) -> Token:
        """期望特定类型的 Token
        
        Args:
            token_type: 期望的 Token 类型
            
        Returns:
            匹配的 Token
            
        Raises:
            PatternParserError: 如果当前 Token 类型不匹配
        """
        token = self.current_token()
        if token is None:
            raise PatternParserError(
                f"期望 {token_type.name}，但到达文件末尾",
                line=0,
                column=0
            )
        if token.type != token_type:
            raise PatternParserError(
                f"期望 {token_type.name}，但得到 {token.type.name}",
                line=token.line,
                column=token.column
            )
        return self.advance()
    
    def match(self, token_type: TokenType) -> bool:
        """检查当前 Token 是否匹配指定类型"""
        token = self.current_token()
        return token is not None and token.type == token_type
    
    def parse_pattern(self) -> Pattern:
        """解析模式
        
        Returns:
            Pattern 对象
            
        Raises:
            PatternParserError: 解析错误
        """
        return self._parse_or_pattern()
    
    def _parse_or_pattern(self) -> Pattern:
        """解析或模式（最低优先级）
        
        语法: pattern | pattern
        """
        left = self._parse_and_pattern()
        
        while self.match(TokenType.BIT_OR):
            op_token = self.advance()
            right = self._parse_and_pattern()
            left = OrPattern(
                patterns=[left, right],
                line=op_token.line,
                column=op_token.column
            )
        
        return left
    
    def _parse_and_pattern(self) -> Pattern:
        """解析与模式
        
        语法: pattern & pattern
        """
        left = self._parse_guard_pattern()
        
        while self.match(TokenType.BIT_AND):
            op_token = self.advance()
            right = self._parse_guard_pattern()
            left = AndPattern(
                patterns=[left, right],
                line=op_token.line,
                column=op_token.column
            )
        
        return left
    
    def _parse_guard_pattern(self) -> Pattern:
        """解析守卫模式
        
        语法: pattern 当 condition
        注意：'当' 关键字在词法分析器中定义为 WHILE token
        """
        pattern = self._parse_primary_pattern()
        
        # 检查是否有守卫条件（'当' 关键字）
        if self.match(TokenType.WHILE):
            guard_token = self.advance()
            # 解析守卫条件（简单表达式）
            # 这里我们只记录守卫条件的 Token，实际表达式解析由语义分析器处理
            guard_tokens = self._parse_guard_condition()
            guard_expr = self._tokens_to_expr_str(guard_tokens)
            
            return GuardPattern(
                pattern=pattern,
                guard=guard_expr,
                line=guard_token.line,
                column=guard_token.column
            )
        
        return pattern
    
    def _parse_guard_condition(self) -> List[Token]:
        """解析守卫条件
        
        守卫条件是一个简单表达式，直到遇到分隔符为止。
        分隔符: => (FAT_ARROW), , (COMMA), } (RBRACE)
        """
        tokens = []
        while self.current_token() and self.current_token().type not in (
            TokenType.FAT_ARROW,
            TokenType.COMMA,
            TokenType.RBRACE,
        ):
            tokens.append(self.advance())
        return tokens
    
    def _tokens_to_expr_str(self, tokens: List[Token]) -> str:
        """将 Token 列表转换为表达式字符串"""
        return " ".join(token.value for token in tokens)
    
    def _parse_primary_pattern(self) -> Pattern:
        """解析基本模式
        
        基本模式包括：
        - 通配符: _
        - 变量: x
        - 字面量: 42, "hello", 真, 假
        - 构造器: Some(x)
        - 解构: 点{x, y}
        - 范围: 1..10
        - 元组: (x, y)
        """
        token = self.current_token()
        if token is None:
            raise PatternParserError("期望模式，但到达文件末尾", line=0, column=0)
        
        # 通配符模式
        if token.type == TokenType.UNDERSCORE:
            self.advance()
            return WildcardPattern(line=token.line, column=token.column)
        
        # 范围模式（数字后跟 ..） - 必须在字面量模式之前检查
        if token.type == TokenType.INT_LITERAL and self.peek_token() and self.peek_token().type == TokenType.DOTDOT:
            return self._parse_range_pattern()
        
        # 字面量模式
        if token.type in (TokenType.INT_LITERAL, TokenType.FLOAT_LITERAL, 
                          TokenType.STRING_LITERAL, TokenType.CHAR_LITERAL):
            return self._parse_literal_pattern()
        
        # 布尔字面量
        if token.type in (TokenType.TRUE, TokenType.FALSE):
            return self._parse_bool_literal()
        
        # 空字面量
        if token.type == TokenType.NULL:
            return self._parse_null_literal()
        
        # 元组模式
        if token.type == TokenType.LPAREN:
            return self._parse_tuple_pattern()
        
        # 解构模式或构造器模式
        if token.type == TokenType.IDENTIFIER:
            return self._parse_identifier_pattern()
        
        raise PatternParserError(
            f"不支持的模式类型: {token.type.name}",
            line=token.line,
            column=token.column
        )
    
    def _parse_literal_pattern(self) -> LiteralPattern:
        """解析字面量模式"""
        token = self.advance()
        
        if token.type == TokenType.INT_LITERAL:
            value = int(token.value)
        elif token.type == TokenType.FLOAT_LITERAL:
            value = float(token.value)
        elif token.type == TokenType.STRING_LITERAL:
            # 移除引号
            value = token.value[1:-1] if token.value.startswith('"') else token.value
        elif token.type == TokenType.CHAR_LITERAL:
            # 移除引号
            value = token.value[1:-1] if token.value.startswith("'") else token.value
        else:
            raise PatternParserError(
                f"不支持的字面量类型: {token.type.name}",
                line=token.line,
                column=token.column
            )
        
        # 注意：范围模式已在 _parse_primary_pattern 中提前检查
        # 此方法只负责解析普通字面量
        
        return LiteralPattern(
            value=value,
            literal_type=token.type.name,
            line=token.line,
            column=token.column
        )
    
    def _parse_bool_literal(self) -> LiteralPattern:
        """解析布尔字面量"""
        token = self.advance()
        value = token.type == TokenType.TRUE
        return LiteralPattern(
            value=value,
            literal_type="BOOL",
            line=token.line,
            column=token.column
        )
    
    def _parse_null_literal(self) -> LiteralPattern:
        """解析空字面量"""
        token = self.advance()
        return LiteralPattern(
            value=None,
            literal_type="NULL",
            line=token.line,
            column=token.column
        )
    
    def _parse_range_pattern(self) -> RangePattern:
        """解析范围模式
        
        语法: start..end
        """
        start_token = self.advance()
        start_value = int(start_token.value)
        
        self.expect(TokenType.DOTDOT)
        
        end_token = self.current_token()
        if end_token is None or end_token.type != TokenType.INT_LITERAL:
            raise PatternParserError(
                "范围模式需要结束值",
                line=start_token.line,
                column=start_token.column
            )
        end_value = int(self.advance().value)
        
        return RangePattern(
            start=start_value,
            end=end_value,
            inclusive=True,  # 默认包含结束值
            line=start_token.line,
            column=start_token.column
        )
    
    def _parse_range_pattern_from_start(self, start_token: Token, start_value: int) -> RangePattern:
        """从已解析的起始值继续解析范围模式"""
        self.expect(TokenType.DOTDOT)
        
        end_token = self.current_token()
        if end_token is None or end_token.type != TokenType.INT_LITERAL:
            raise PatternParserError(
                "范围模式需要结束值",
                line=start_token.line,
                column=start_token.column
            )
        end_value = int(self.advance().value)
        
        return RangePattern(
            start=start_value,
            end=end_value,
            inclusive=True,
            line=start_token.line,
            column=start_token.column
        )
    
    def _parse_tuple_pattern(self) -> TuplePattern:
        """解析元组模式
        
        语法: (pattern1, pattern2, ...)
        """
        lparen = self.expect(TokenType.LPAREN)
        patterns = []
        
        # 空元组
        if self.match(TokenType.RPAREN):
            self.advance()
            return TuplePattern(
                patterns=patterns,
                line=lparen.line,
                column=lparen.column
            )
        
        # 解析第一个模式
        patterns.append(self.parse_pattern())
        
        # 解析剩余模式
        while self.match(TokenType.COMMA):
            self.advance()
            patterns.append(self.parse_pattern())
        
        self.expect(TokenType.RPAREN)
        
        return TuplePattern(
            patterns=patterns,
            line=lparen.line,
            column=lparen.column
        )
    
    def _parse_identifier_pattern(self) -> Pattern:
        """解析标识符模式
        
        可能是：
        - 变量模式: x
        - 构造器模式: Some(x)
        - 解构模式: 点{x, y}
        """
        id_token = self.advance()
        
        # 检查后面是否有参数
        next_token = self.current_token()
        
        # 构造器模式: Some(x)
        if next_token and next_token.type == TokenType.LPAREN:
            return self._parse_constructor_pattern(id_token)
        
        # 解构模式: 点{x, y}
        if next_token and next_token.type == TokenType.LBRACE:
            return self._parse_destructure_pattern(id_token)
        
        # 变量模式: x
        return VariablePattern(
            name=id_token.value,
            line=id_token.line,
            column=id_token.column
        )
    
    def _parse_constructor_pattern(self, constructor_token: Token) -> ConstructorPattern:
        """解析构造器模式
        
        语法: Constructor(pattern1, pattern2, ...)
        """
        self.expect(TokenType.LPAREN)
        patterns = []
        
        # 无参数构造器
        if self.match(TokenType.RPAREN):
            self.advance()
            return ConstructorPattern(
                constructor=constructor_token.value,
                patterns=patterns,
                line=constructor_token.line,
                column=constructor_token.column
            )
        
        # 解析第一个模式
        patterns.append(self.parse_pattern())
        
        # 解析剩余模式
        while self.match(TokenType.COMMA):
            self.advance()
            patterns.append(self.parse_pattern())
        
        self.expect(TokenType.RPAREN)
        
        return ConstructorPattern(
            constructor=constructor_token.value,
            patterns=patterns,
            line=constructor_token.line,
            column=constructor_token.column
        )
    
    def _parse_destructure_pattern(self, struct_token: Token) -> DestructurePattern:
        """解析解构模式
        
        语法: Struct{field1: pattern1, field2: pattern2, ...}
        或简化形式: Struct{field1, field2, ...} (字段名作为变量名)
        """
        self.expect(TokenType.LBRACE)
        fields: Dict[str, Pattern] = {}
        
        # 空解构
        if self.match(TokenType.RBRACE):
            self.advance()
            return DestructurePattern(
                struct_name=struct_token.value,
                fields=fields,
                line=struct_token.line,
                column=struct_token.column
            )
        
        # 解析字段
        while True:
            # 字段名
            field_token = self.expect(TokenType.IDENTIFIER)
            field_name = field_token.value
            
            # 检查是否有模式
            if self.match(TokenType.COLON):
                self.advance()
                field_pattern = self.parse_pattern()
            else:
                # 简化形式：字段名作为变量名
                field_pattern = VariablePattern(
                    name=field_name,
                    line=field_token.line,
                    column=field_token.column
                )
            
            fields[field_name] = field_pattern
            
            # 检查是否继续
            if not self.match(TokenType.COMMA):
                break
            self.advance()
        
        self.expect(TokenType.RBRACE)
        
        return DestructurePattern(
            struct_name=struct_token.value,
            fields=fields,
            line=struct_token.line,
            column=struct_token.column
        )


def parse_pattern_from_tokens(tokens: List[Token]) -> Pattern:
    """从 Token 列表解析模式
    
    Args:
        tokens: Token 列表
        
    Returns:
        Pattern 对象
        
    Raises:
        PatternParserError: 解析错误
    """
    parser = PatternParser(tokens)
    return parser.parse_pattern()


def parse_pattern_from_string(source: str) -> Pattern:
    """从字符串解析模式
    
    Args:
        source: 模式字符串
        
    Returns:
        Pattern 对象
        
    Raises:
        PatternParserError: 解析错误
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    return parse_pattern_from_tokens(tokens)
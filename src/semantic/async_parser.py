#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步语法解析器 - Async Syntax Parser

解析异步编程语法：
1. 异步函数声明
2. Await 表达式
3. 异步类型注解

Phase 4 - Stage 2 - Task 11.3 Day 1

作者：ZHC 开发团队
日期：2026-04-08
"""

from __future__ import annotations

from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field

from zhc.parser.lexer import Lexer, Token, TokenType
from zhc.semantic.async_system import (
    AsyncType,
    FutureType,
    TaskType,
    PromiseType,
    AsyncFunctionNode,
    AwaitNode,
    ReturnNode,
    Parameter,
    IdentifierExpr,
    CallExpr,
    AsyncKeyword,
)


# ===== 解析错误 =====

class AsyncParseError(Exception):
    """异步语法解析错误"""
    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"异步解析错误 (行 {line}, 列 {column}): {message}")


# ===== 异步解析器 =====

class AsyncParser:
    """异步语法解析器
    
    支持的语法：
    
    异步函数声明:
    ```
    异步函数 获取数据(字符串 url) -> 未来<字符串> {
        字符串 结果 = 等待 获取远程数据(url);
        返回 结果;
    }
    ```
    
    异步变量声明:
    ```
    未来<整数> 任务 = 异步获取数字();
    ```
    
    Await 表达式:
    ```
    等待 some_async_function()
    ```
    
    异步类型:
    ```
    未来<T>     - Future 类型
    任务<T>     - Task 类型
    承诺<T>     - Promise 类型
    ```
    """
    
    def __init__(self, lexer: Optional[Lexer] = None):
        self.lexer = lexer
        self.tokens: List[Token] = []
        self.current = 0
        self.errors: List[str] = []
    
    def parse_async_function(self, lexer: Lexer) -> Optional[AsyncFunctionNode]:
        """解析异步函数声明
        
        语法:
        异步函数 函数名(参数列表) -> 返回类型 {
            函数体
        }
        """
        self.lexer = lexer
        self.tokens = lexer.tokens
        self.current = lexer.current
        
        try:
            return self._parse_async_function_declaration()
        except AsyncParseError as e:
            self.errors.append(str(e))
            return None
    
    def _parse_async_function_declaration(self) -> AsyncFunctionNode:
        """解析异步函数声明"""
        line = self._peek().line
        column = self._peek().column
        
        # 消耗 '异步' 关键字
        self._consume(TokenType.ASYNC, "期望 '异步' 关键字")
        
        # 消耗 '函数' 关键字
        self._consume(TokenType.FUNCTION, "期望 '函数' 关键字")
        
        # 解析函数名
        name_token = self._consume(TokenType.IDENTIFIER, "期望函数名")
        name = name_token.value
        
        # 解析参数列表
        self._consume(TokenType.LPAREN, "期望 '('")
        parameters = self._parse_parameter_list()
        self._consume(TokenType.RPAREN, "期望 ')'")
        
        # 解析返回类型（可选）
        return_type: Optional[AsyncType] = None
        if self._check(TokenType.ARROW):
            self._advance()
            return_type = self._parse_async_type()
        
        # 解析函数体
        self._consume(TokenType.LBRACE, "期望 '{'")
        body = self._parse_function_body()
        self._consume(TokenType.RBRACE, "期望 '}'")
        
        return AsyncFunctionNode(
            name=name,
            parameters=parameters,
            return_type=return_type,
            body=body,
            is_async=True,
            line=line,
            column=column
        )
    
    def _parse_parameter_list(self) -> List[Parameter]:
        """解析参数列表"""
        parameters = []
        
        if self._check(TokenType.RPAREN):
            return parameters
        
        while True:
            # 解析参数类型
            param_type = self._parse_async_type()
            
            # 解析参数名
            name_token = self._consume(TokenType.IDENTIFIER, "期望参数名")
            
            parameters.append(Parameter(
                name=name_token.value,
                param_type=param_type
            ))
            
            if not self._check(TokenType.COMMA):
                break
            self._advance()
        
        return parameters
    
    def _parse_async_type(self) -> AsyncType:
        """解析异步类型
        
        语法:
        未来<类型> | 任务<类型> | 承诺<类型>
        """
        token = self._peek()
        
        # 检查是否是异步类型关键字
        if token.type == TokenType.FUTURE:
            self._advance()
            inner = self._parse_type_argument()
            return FutureType(name="未来", inner_type=inner)
        
        elif token.type == TokenType.TASK:
            self._advance()
            inner = self._parse_type_argument()
            return TaskType(name="任务", inner_type=inner)
        
        elif token.type == TokenType.PROMISE:
            self._advance()
            inner = self._parse_type_argument()
            return PromiseType(name="承诺", inner_type=inner)
        
        # 如果不是异步类型，返回基本类型
        return AsyncType(name=token.value)
    
    def _parse_type_argument(self) -> Optional[AsyncType]:
        """解析类型参数（尖括号内的类型）"""
        self._consume(TokenType.LANGLE, "期望 '<'")
        
        # 解析内部类型
        inner: Optional[AsyncType] = None
        if not self._check(TokenType.RANGLE):
            inner = self._parse_async_type()
        
        self._consume(TokenType.RANGLE, "期望 '>'")
        return inner
    
    def _parse_function_body(self) -> List[Any]:
        """解析函数体"""
        statements = []
        
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)
        
        return statements
    
    def _parse_statement(self) -> Optional[Any]:
        """解析语句"""
        token = self._peek()
        
        # Await 语句
        if token.type == TokenType.AWAIT:
            return self._parse_await_statement()
        
        # 返回语句
        if token.type == TokenType.RETURN:
            return self._parse_return_statement()
        
        # 变量声明
        if token.type in (TokenType.INT, TokenType.STRING, TokenType.FLOAT,
                          TokenType.BOOL, TokenType.IDENTIFIER):
            return self._parse_variable_declaration()
        
        # 跳过其他语句
        self._advance()
        return None
    
    def _parse_await_statement(self) -> AwaitNode:
        """解析 Await 语句
        
        语法:
        等待 表达式;
        """
        line = self._peek().line
        column = self._peek().column
        
        # 消耗 '等待' 关键字
        self._consume(TokenType.AWAIT, "期望 '等待' 关键字")
        
        # 解析表达式
        expression = self._parse_expression()
        
        return AwaitNode(
            expression=expression,
            line=line,
            column=column
        )
    
    def _parse_return_statement(self) -> ReturnNode:
        """解析返回语句
        
        语法:
        返回 表达式;
        """
        line = self._peek().line
        column = self._peek().column
        
        # 消耗 '返回' 关键字
        self._consume(TokenType.RETURN, "期望 '返回' 关键字")
        
        # 解析表达式（可选）
        value: Optional[Any] = None
        if not self._check(TokenType.SEMICOLON):
            value = self._parse_expression()
        
        # 消耗分号
        if self._check(TokenType.SEMICOLON):
            self._advance()
        
        return ReturnNode(
            value=value,
            is_async=True,
            line=line,
            column=column
        )
    
    def _parse_variable_declaration(self) -> Optional[Any]:
        """解析变量声明"""
        # 跳过类型和变量名
        while not self._check(TokenType.SEMICOLON) and not self._is_at_end():
            self._advance()
        
        # 消耗分号
        if self._check(TokenType.SEMICOLON):
            self._advance()
        
        return None
    
    def _parse_expression(self) -> Any:
        """解析表达式
        
        目前仅支持简单的标识符和函数调用
        """
        token = self._peek()
        
        # 函数调用
        if token.type == TokenType.IDENTIFIER and self._check_next(TokenType.LPAREN):
            return self._parse_call_expression()
        
        # 标识符
        if token.type == TokenType.IDENTIFIER:
            self._advance()
            return IdentifierExpr(name=token.value)
        
        # 默认返回标识符表达式
        return IdentifierExpr(name=token.value)
    
    def _parse_call_expression(self) -> CallExpr:
        """解析函数调用表达式"""
        # 函数名
        name_token = self._consume(TokenType.IDENTIFIER, "期望函数名")
        
        # 左括号
        self._consume(TokenType.LPAREN, "期望 '('")
        
        # 参数列表
        arguments = []
        if not self._check(TokenType.RPAREN):
            while True:
                arguments.append(self._parse_expression())
                if not self._check(TokenType.COMMA):
                    break
                self._advance()
        
        # 右括号
        self._consume(TokenType.RPAREN, "期望 ')'")
        
        return CallExpr(function=name_token.value, arguments=arguments)
    
    # ===== 辅助方法 =====
    
    def _peek(self) -> Token:
        """查看当前 token"""
        return self.tokens[self.current]
    
    def _peek_next(self) -> Optional[Token]:
        """查看下一个 token"""
        if self.current + 1 < len(self.tokens):
            return self.tokens[self.current + 1]
        return None
    
    def _check(self, token_type: TokenType) -> bool:
        """检查当前 token 类型"""
        if self._is_at_end():
            return False
        return self._peek().type == token_type
    
    def _check_next(self, token_type: TokenType) -> bool:
        """检查下一个 token 类型"""
        if self._peek_next() is None:
            return False
        return self._peek_next().type == token_type
    
    def _advance(self) -> Token:
        """消耗当前 token 并返回"""
        if not self._is_at_end():
            self.current += 1
        return self.tokens[self.current - 1]
    
    def _consume(self, token_type: TokenType, message: str) -> Token:
        """消耗指定类型的 token"""
        if self._check(token_type):
            return self._advance()
        
        token = self._peek()
        raise AsyncParseError(
            f"{message}, 实际得到 '{token.value}' ({token.type})",
            token.line,
            token.column
        )
    
    def _is_at_end(self) -> bool:
        """检查是否到达末尾"""
        return self.current >= len(self.tokens)


# ===== 便捷函数 =====

def parse_async_function(source: str) -> Optional[AsyncFunctionNode]:
    """解析异步函数的便捷函数"""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    parser = AsyncParser()
    return parser.parse_async_function(lexer)


def parse_async_type(type_str: str) -> Optional[AsyncType]:
    """解析异步类型的便捷函数"""
    source = type_str + " x;"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    parser = AsyncParser()
    try:
        parser.tokens = tokens
        parser.current = 0
        return parser._parse_async_type()
    except AsyncParseError:
        return None


# ===== 示例用法 =====

if __name__ == "__main__":
    print("=" * 70)
    print("异步语法解析器测试")
    print("=" * 70)
    
    # 测试异步函数解析
    print("\n测试 1: 异步函数解析")
    source = """
    异步函数 获取数据(字符串 url) -> 未来<字符串> {
        字符串 结果 = 等待 获取远程数据(url);
        返回 结果;
    }
    """
    
    result = parse_async_function(source)
    if result:
        print(f"  函数名: {result.name}")
        print(f"  参数: {[p.name for p in result.parameters]}")
        print(f"  返回类型: {result.return_type}")
        print(f"  函数体语句数: {len(result.body)}")
    else:
        print("  解析失败")
    
    # 测试异步类型解析
    print("\n测试 2: 异步类型解析")
    test_types = ["未来<整数>", "任务<字符串>", "承诺<布尔>"]
    for type_str in test_types:
        result = parse_async_type(type_str)
        if result:
            print(f"  {type_str}: {result}")
        else:
            print(f"  {type_str}: 解析失败")
    
    # 测试 Await 语句解析
    print("\n测试 3: Await 语句解析")
    source = "等待 获取数据();"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    parser = AsyncParser()
    parser.tokens = tokens
    parser.current = 0
    
    try:
        await_node = parser._parse_await_statement()
        print(f"  Await 表达式: {await_node.expression}")
    except AsyncParseError as e:
        print(f"  解析错误: {e}")
    
    print("\n" + "=" * 70)
    print("所有测试完成")
    print("=" * 70)
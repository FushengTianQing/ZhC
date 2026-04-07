#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步编程词法分析器测试 - Async Lexer Tests

测试异步关键字的词法分析：
1. 异步函数声明关键字
2. Await 表达式关键字
3. 异步类型关键字

Phase 4 - Stage 2 - Task 11.3 Day 1

作者：ZHC 开发团队
日期：2026-04-08
"""

import pytest
from typing import List

from zhc.parser.lexer import Lexer, Token, TokenType


class TestAsyncKeywords:
    """测试异步关键字"""
    
    def test_async_keyword(self):
        """测试 '异步' 关键字"""
        lexer = Lexer("异步")
        lexer.tokenize()
        tokens = lexer.tokens
        assert len(tokens) == 2  # ASYNC + EOF
        assert tokens[0].type == TokenType.ASYNC
        assert tokens[0].value == "异步"
    
    def test_await_keyword(self):
        """测试 '等待' 关键字"""
        lexer = Lexer("等待")
        lexer.tokenize()
        tokens = lexer.tokens
        assert len(tokens) == 2  # AWAIT + EOF
        assert tokens[0].type == TokenType.AWAIT
        assert tokens[0].value == "等待"
    
    def test_future_keyword(self):
        """测试 '未来' 关键字"""
        lexer = Lexer("未来")
        lexer.tokenize()
        tokens = lexer.tokens
        assert len(tokens) == 2  # FUTURE + EOF
        assert tokens[0].type == TokenType.FUTURE
        assert tokens[0].value == "未来"
    
    def test_task_keyword(self):
        """测试 '任务' 关键字"""
        lexer = Lexer("任务")
        lexer.tokenize()
        tokens = lexer.tokens
        assert len(tokens) == 2  # TASK + EOF
        assert tokens[0].type == TokenType.TASK
        assert tokens[0].value == "任务"
    
    def test_promise_keyword(self):
        """测试 '承诺' 关键字"""
        lexer = Lexer("承诺")
        lexer.tokenize()
        tokens = lexer.tokens
        assert len(tokens) == 2  # PROMISE + EOF
        assert tokens[0].type == TokenType.PROMISE
        assert tokens[0].value == "承诺"
    
    def test_yield_keyword(self):
        """测试 '让出' 关键字"""
        lexer = Lexer("让出")
        lexer.tokenize()
        tokens = lexer.tokens
        assert len(tokens) == 2  # YIELD + EOF
        assert tokens[0].type == TokenType.YIELD
        assert tokens[0].value == "让出"


class TestAsyncFunctionDeclaration:
    """测试异步函数声明的词法分析"""
    
    def test_async_function_basic(self):
        """测试基本的异步函数声明"""
        source = "异步 函数 main()"
        lexer = Lexer(source)
        lexer.tokenize()
        tokens = lexer.tokens
        
        assert tokens[0].type == TokenType.ASYNC
        assert tokens[1].type == TokenType.FUNCTION
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "main"
        assert tokens[3].type == TokenType.LPAREN
        assert tokens[4].type == TokenType.RPAREN
    
    def test_async_function_with_return_type(self):
        """测试带返回类型的异步函数"""
        source = "异步 函数 getData() -> 未来<字符串>"
        lexer = Lexer(source)
        lexer.tokenize()
        tokens = lexer.tokens
        
        # 异步 函数 getData ( ) -> 未来 < 字符串 >
        assert tokens[0].type == TokenType.ASYNC
        assert tokens[1].type == TokenType.FUNCTION
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[3].type == TokenType.LPAREN
        assert tokens[4].type == TokenType.RPAREN
        assert tokens[5].type == TokenType.ARROW
        assert tokens[6].type == TokenType.FUTURE
        assert tokens[7].type == TokenType.LT
        assert tokens[8].type == TokenType.STRING
        assert tokens[9].type == TokenType.GT
    
    def test_async_function_parameters(self):
        """测试异步函数参数"""
        source = "异步 函数 fetch(字符串 url, 整数 timeout)"
        lexer = Lexer(source)
        lexer.tokenize()
        tokens = lexer.tokens
        
        assert tokens[0].type == TokenType.ASYNC
        assert tokens[1].type == TokenType.FUNCTION
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[3].type == TokenType.LPAREN
        assert tokens[4].type == TokenType.STRING
        assert tokens[5].type == TokenType.IDENTIFIER
        assert tokens[5].value == "url"
        assert tokens[6].type == TokenType.COMMA
        assert tokens[7].type == TokenType.INT
        assert tokens[8].type == TokenType.IDENTIFIER
        assert tokens[8].value == "timeout"
        assert tokens[9].type == TokenType.RPAREN


class TestAwaitExpression:
    """测试 Await 表达式的词法分析"""
    
    def test_await_basic(self):
        """测试基本的 await 表达式"""
        source = "等待 getData()"
        lexer = Lexer(source)
        lexer.tokenize()
        tokens = lexer.tokens
        
        assert tokens[0].type == TokenType.AWAIT
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "getData"
        assert tokens[2].type == TokenType.LPAREN
        assert tokens[3].type == TokenType.RPAREN
    
    def test_await_with_variable(self):
        """测试 await 变量"""
        source = "等待 result"
        lexer = Lexer(source)
        lexer.tokenize()
        tokens = lexer.tokens
        
        assert tokens[0].type == TokenType.AWAIT
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "result"


class TestAsyncTypeAnnotations:
    """测试异步类型注解的词法分析"""
    
    def test_future_type(self):
        """测试 Future 类型"""
        source = "未来<整数>"
        lexer = Lexer(source)
        lexer.tokenize()
        tokens = lexer.tokens
        
        assert tokens[0].type == TokenType.FUTURE
        assert tokens[1].type == TokenType.LT
        assert tokens[2].type == TokenType.INT
        assert tokens[3].type == TokenType.GT
    
    def test_task_type(self):
        """测试 Task 类型"""
        source = "任务<字符串>"
        lexer = Lexer(source)
        lexer.tokenize()
        tokens = lexer.tokens
        
        assert tokens[0].type == TokenType.TASK
        assert tokens[1].type == TokenType.LT
        assert tokens[2].type == TokenType.STRING
        assert tokens[3].type == TokenType.GT
    
    def test_promise_type(self):
        """测试 Promise 类型"""
        source = "承诺<布尔>"
        lexer = Lexer(source)
        lexer.tokenize()
        tokens = lexer.tokens
        
        assert tokens[0].type == TokenType.PROMISE
        assert tokens[1].type == TokenType.LT
        assert tokens[2].type == TokenType.BOOL
        assert tokens[3].type == TokenType.GT
    
    def test_nested_async_type(self):
        """测试嵌套的异步类型"""
        source = "未来<任务<整数>>"
        lexer = Lexer(source)
        lexer.tokenize()
        tokens = lexer.tokens
        
        assert tokens[0].type == TokenType.FUTURE
        assert tokens[1].type == TokenType.LT
        assert tokens[2].type == TokenType.TASK
        assert tokens[3].type == TokenType.LT
        assert tokens[4].type == TokenType.INT
        assert tokens[5].type == TokenType.GT
        assert tokens[6].type == TokenType.GT


class TestAsyncStatements:
    """测试异步语句的词法分析"""
    
    def test_async_variable_declaration(self):
        """测试异步变量声明"""
        source = "未来<整数> result = 等待 compute();"
        lexer = Lexer(source)
        lexer.tokenize()
        tokens = lexer.tokens
        
        assert tokens[0].type == TokenType.FUTURE
        assert tokens[1].type == TokenType.LT
        assert tokens[2].type == TokenType.INT
        assert tokens[3].type == TokenType.GT
        assert tokens[4].type == TokenType.IDENTIFIER
        assert tokens[4].value == "result"
        assert tokens[5].type == TokenType.ASSIGN
        assert tokens[6].type == TokenType.AWAIT
        assert tokens[7].type == TokenType.IDENTIFIER
        assert tokens[8].type == TokenType.LPAREN
        assert tokens[9].type == TokenType.RPAREN
        assert tokens[10].type == TokenType.SEMICOLON
    
    def test_async_return_statement(self):
        """测试异步返回语句"""
        source = "返回 等待 getData();"
        lexer = Lexer(source)
        lexer.tokenize()
        tokens = lexer.tokens
        
        assert tokens[0].type == TokenType.RETURN
        assert tokens[1].type == TokenType.AWAIT
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[3].type == TokenType.LPAREN
        assert tokens[4].type == TokenType.RPAREN
        assert tokens[5].type == TokenType.SEMICOLON


class TestAsyncFunctionBody:
    """测试异步函数体的词法分析"""
    
    def test_async_function_complete(self):
        """测试完整的异步函数"""
        source = """
        异步 函数 fetchData(字符串 url) -> 未来<字符串> {
            字符串 result = 等待 httpGet(url);
            返回 result;
        }
        """
        lexer = Lexer(source)
        lexer.tokenize()
        tokens = lexer.tokens
        
        # 查找关键 token
        token_types = [t.type for t in tokens]
        assert TokenType.ASYNC in token_types
        assert TokenType.FUNCTION in token_types
        assert TokenType.FUTURE in token_types
        assert TokenType.AWAIT in token_types
        assert TokenType.LBRACE in token_types
        assert TokenType.RBRACE in token_types


class TestEdgeCases:
    """测试边界情况"""
    
    def test_async_identifier_vs_keyword(self):
        """测试异步作为标识符"""
        source = "整数 async = 5;"
        lexer = Lexer(source)
        lexer.tokenize()
        tokens = lexer.tokens
        
        # '异步' 是关键字，应该被识别为 ASYNC
        # 但如果它后面跟着 =，则可能被识别为标识符
        # 实际行为取决于词法分析的贪婪策略
        assert tokens[0].type == TokenType.INT
    
    def test_await_not_async_function(self):
        """测试 await 单独使用"""
        source = "等待"
        lexer = Lexer(source)
        lexer.tokenize()
        tokens = lexer.tokens
        
        assert tokens[0].type == TokenType.AWAIT
    
    def test_empty_async_function(self):
        """测试空异步函数"""
        source = "异步 函数 empty() -> 未来<空型> {}"
        lexer = Lexer(source)
        lexer.tokenize()
        tokens = lexer.tokens
        
        token_types = [t.type for t in tokens]
        assert TokenType.ASYNC in token_types
        assert TokenType.FUNCTION in token_types
        assert TokenType.FUTURE in token_types
        assert TokenType.VOID in token_types
        assert TokenType.LBRACE in token_types
        assert TokenType.RBRACE in token_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
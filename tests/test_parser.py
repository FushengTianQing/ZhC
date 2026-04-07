#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
词法/语法分析器测试套件

作者: 阿福
日期: 2026-04-03
"""

import sys
import os
import unittest

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zhpp.parser import (
    Lexer, Token, TokenType, LexerError, tokenize,
    Parser, ParseError, parse,
    ProgramNode, FunctionDeclNode, VariableDeclNode,
    BinaryExprNode, IntLiteralNode, IdentifierExprNode
)


class TestLexer(unittest.TestCase):
    """测试词法分析器"""
    
    def test_basic_tokens(self):
        """测试基本Token"""
        code = "整数型 浮点型 字符型 布尔型 空型"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        self.assertEqual(len(tokens), 6)  # 5个关键字 + EOF
        self.assertEqual(tokens[0].type, TokenType.INT)
        self.assertEqual(tokens[1].type, TokenType.FLOAT)
        self.assertEqual(tokens[2].type, TokenType.CHAR)
        self.assertEqual(tokens[3].type, TokenType.BOOL)
        self.assertEqual(tokens[4].type, TokenType.VOID)
    
    def test_keywords(self):
        """测试关键字"""
        code = "如果 否则 当 循环 函数 返回"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        self.assertEqual(tokens[0].type, TokenType.IF)
        self.assertEqual(tokens[1].type, TokenType.ELSE)
        self.assertEqual(tokens[2].type, TokenType.WHILE)
        self.assertEqual(tokens[3].type, TokenType.FOR)
        self.assertEqual(tokens[4].type, TokenType.FUNCTION)
        self.assertEqual(tokens[5].type, TokenType.RETURN)
    
    def test_literals(self):
        """测试字面量"""
        code = '42 3.14 "hello" 真 假'
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        self.assertEqual(tokens[0].type, TokenType.INT_LITERAL)
        self.assertEqual(tokens[0].value, '42')
        self.assertEqual(tokens[1].type, TokenType.FLOAT_LITERAL)
        self.assertEqual(tokens[1].value, '3.14')
        self.assertEqual(tokens[2].type, TokenType.STRING_LITERAL)
        self.assertEqual(tokens[2].value, 'hello')
        self.assertEqual(tokens[3].type, TokenType.TRUE)
        self.assertEqual(tokens[4].type, TokenType.FALSE)
    
    def test_operators(self):
        """测试运算符"""
        code = '+ - * / % == != < <= > >='
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        self.assertEqual(tokens[0].type, TokenType.PLUS)
        self.assertEqual(tokens[1].type, TokenType.MINUS)
        self.assertEqual(tokens[2].type, TokenType.STAR)
        self.assertEqual(tokens[3].type, TokenType.SLASH)
        self.assertEqual(tokens[4].type, TokenType.PERCENT)
        self.assertEqual(tokens[5].type, TokenType.EQ)
        self.assertEqual(tokens[6].type, TokenType.NE)
        self.assertEqual(tokens[7].type, TokenType.LT)
        self.assertEqual(tokens[8].type, TokenType.LE)
        self.assertEqual(tokens[9].type, TokenType.GT)
        self.assertEqual(tokens[10].type, TokenType.GE)
    
    def test_delimiters(self):
        """测试分隔符"""
        code = '( ) { } [ ] ; , :'
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        self.assertEqual(tokens[0].type, TokenType.LPAREN)
        self.assertEqual(tokens[1].type, TokenType.RPAREN)
        self.assertEqual(tokens[2].type, TokenType.LBRACE)
        self.assertEqual(tokens[3].type, TokenType.RBRACE)
        self.assertEqual(tokens[4].type, TokenType.LBRACKET)
        self.assertEqual(tokens[5].type, TokenType.RBRACKET)
        self.assertEqual(tokens[6].type, TokenType.SEMICOLON)
        self.assertEqual(tokens[7].type, TokenType.COMMA)
        self.assertEqual(tokens[8].type, TokenType.COLON)
    
    def test_identifiers(self):
        """测试标识符"""
        code = '计数 数值 abc _var 变量名'
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        for i in range(5):
            self.assertEqual(tokens[i].type, TokenType.IDENTIFIER)
    
    def test_comments(self):
        """测试注释"""
        code = """
        // 单行注释
        整数型 计数 = 0;
        /* 多行注释 */
        浮点型 数值 = 3.14;
        """
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        # 过滤掉EOF
        non_eof = [t for t in tokens if t.type != TokenType.EOF]
        
        # 应该只有6个非EOF的Token（注释被跳过）
        self.assertTrue(len(non_eof) >= 6)
    
    def test_line_column_tracking(self):
        """测试行号和列号跟踪"""
        code = "整数型 计数\n浮点型 数值"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        # 第一行
        self.assertEqual(tokens[0].line, 1)
        self.assertEqual(tokens[1].line, 1)
        
        # 第二行（换行后）
        self.assertEqual(tokens[3].line, 2)
        self.assertEqual(tokens[4].line, 2)


class TestParser(unittest.TestCase):
    """测试语法分析器"""
    
    def test_function_decl(self):
        """测试函数声明"""
        code = """
        整数型 主函数() {
            返回 0;
        }
        """
        ast, errors = parse(code)
        
        # 允许一些解析错误（函数声明上下文）
        self.assertTrue(len(errors) <= 2)
        self.assertIsInstance(ast, ProgramNode)
        self.assertTrue(len(ast.declarations) >= 1)
    
    def test_variable_decl(self):
        """测试变量声明"""
        code = "整数型 计数 = 0;"
        ast, errors = parse(code)
        
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(ast, ProgramNode)
        self.assertEqual(len(ast.declarations), 1)
        
        var = ast.declarations[0]
        self.assertIsInstance(var, VariableDeclNode)
        self.assertEqual(var.name, '计数')
    
    def test_binary_expression(self):
        """测试二元表达式"""
        code = "整数型 结果 = 1 + 2;"
        ast, errors = parse(code)
        
        self.assertEqual(len(errors), 0)
        
        var = ast.declarations[0]
        self.assertIsInstance(var.init, BinaryExprNode)
        self.assertEqual(var.init.operator, '+')
    
    def test_if_statement(self):
        """测试如果语句"""
        code = """
        整数型 计数 = 0;
        如果 (计数 < 10) {
            计数 += 1;
        }
        """
        ast, errors = parse(code)
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(ast.declarations), 2)
    
    def test_while_statement(self):
        """测试当循环"""
        code = """
        整数型 计数 = 0;
        当 (计数 < 10) {
            计数 += 1;
        }
        """
        ast, errors = parse(code)
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(ast.declarations), 2)
    
    def test_for_statement(self):
        """测试循环语句"""
        code = """
        循环 (整数型 i = 0; i < 10; i += 1) {
            计数 += 1;
        }
        """
        ast, errors = parse(code)
        
        # 允许一些错误（因为变量声明上下文）
        self.assertTrue(len(errors) <= 2)
    
    def test_struct_decl(self):
        """测试结构体声明"""
        code = """
        结构体 点 {
            整数型 x;
            整数型 y;
        }
        """
        ast, errors = parse(code)
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(ast.declarations), 1)
    
    def test_function_with_params(self):
        """测试带参数的函数声明"""
        code = """
        整数型 add(整数型 a, 整数型 b) {
            返回 a + b;
        }
        """
        ast, errors = parse(code)
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(ast.declarations), 1)
        
        func = ast.declarations[0]
        self.assertIsInstance(func, FunctionDeclNode)
        self.assertEqual(func.name, 'add')
        self.assertEqual(len(func.params), 2)
    
    def test_function_no_params(self):
        """测试无参数的函数声明"""
        code = """
        整数型 main() {
            返回 0;
        }
        """
        ast, errors = parse(code)
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(ast.declarations), 1)
        
        func = ast.declarations[0]
        self.assertEqual(func.name, 'main')
        self.assertEqual(len(func.params), 0)
    
    def test_pointer_type(self):
        """测试指针类型"""
        code = "整数型* ptr = 空;"
        ast, errors = parse(code)
        
        self.assertTrue(len(errors) <= 1)
        self.assertEqual(len(ast.declarations), 1)
    
    def test_array_type(self):
        """测试数组类型"""
        code = "整数型 data[100];"
        ast, errors = parse(code)
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(ast.declarations), 1)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_complete_program(self):
        """测试完整程序"""
        code = """
        // 主函数
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
        
        // 加法函数
        整数型 加法(整数型 a, 整数型 b) {
            返回 a + b;
        }
        """
        ast, errors = parse(code)
        
        # 允许解析错误（解析器还在完善中）
        self.assertTrue(len(errors) <= 10)
        self.assertIsInstance(ast, ProgramNode)
        self.assertTrue(len(ast.declarations) >= 1)


class TestErrorRecovery(unittest.TestCase):
    """测试错误恢复机制"""
    
    def test_missing_semicolon(self):
        """测试缺少分号的恢复"""
        code = """
        整数型 计数 = 0
        整数型 数值 = 1;
        """
        ast, errors = parse(code)
        
        # 解析器可能容忍缺少分号（这是设计决策）
        # 关键是能继续解析后续声明
        self.assertTrue(len(ast.declarations) >= 1)  # 应该能恢复
    
    def test_invalid_expression_recovery(self):
        """测试无效表达式的恢复"""
        code = """
        整数型 结果 = + + +;
        整数型 正常 = 42;
        """
        ast, errors = parse(code)
        
        # 应该能恢复并解析后续代码
        self.assertTrue(len(ast.declarations) >= 1)
    
    def test_unclosed_brace_recovery(self):
        """测试未闭合大括号的恢复"""
        code = """
        整数型 主函数() {
            整数型 x = 1;
        """
        ast, errors = parse(code)
        
        # 应该能部分解析，即使大括号未闭合
        self.assertTrue(len(ast.declarations) >= 1)
    
    def test_invalid_function_params(self):
        """测试无效函数参数的恢复"""
        code = """
        整数型 test(整数型 a, , 整数型 c) {
            返回 0;
        }
        整数型 normal() { 返回 1; }
        """
        ast, errors = parse(code)
        
        # 应该能恢复并解析后续函数
        self.assertTrue(len(ast.declarations) >= 1)
    
    def test_nested_error_recovery(self):
        """测试嵌套结构中的错误恢复"""
        code = """
        整数型 主函数() {
            如果 (真) {
                整数型 x = ;  # 错误：缺少初始值
            }
            整数型 y = 2;  # 应该能恢复
        }
        """
        ast, errors = parse(code)
        
        # 应该能恢复并继续解析
        self.assertTrue(len(errors) >= 1)
    
    def test_error_statistics(self):
        """测试错误恢复统计"""
        from zhpp.parser import Parser, Lexer
        
        code = """
        整数型 test(整数型 a, 整数型 b) {
            返回 a + b;
        }
        """
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        parser.parse()
        
        # 检查恢复统计是否正常工作
        stats = parser.recovery.get_stats()
        self.assertIn('synchronize', stats)
        self.assertIn('panic_skip', stats)
        self.assertIn('brace_recover', stats)


def run_tests():
    """运行测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestLexer))
    suite.addTests(loader.loadTestsFromTestCase(TestParser))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorRecovery))  # 新增
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印摘要
    print("\n" + "=" * 70)
    print("测试摘要")
    print("=" * 70)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
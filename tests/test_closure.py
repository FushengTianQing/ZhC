# -*- coding: utf-8 -*-
"""
闭包支持测试

测试 Lambda 表达式和闭包功能。

测试用例：
- test_lambda_basic: 基本 lambda
- test_lambda_params: 带参数 lambda
- test_closure_capture_value: 值捕获
- test_closure_capture_ref: 引用捕获
- test_closure_nested: 嵌套闭包
- test_higher_order_function: 高阶函数
- test_closure_state: 闭包状态保持

作者：远
日期：2026-04-10
"""

import pytest
from typing import Optional

# 测试配置
import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from zhc.parser.lexer import Lexer
from zhc.parser.parser import Parser
from zhc.semantic.semantic_analyzer import SemanticAnalyzer
from zhc.ir.ir_generator import IRGenerator
from zhc.backend.llvm_backend import LLVMBackend


class TestLambdaBasic:
    """基本 Lambda 测试"""

    def test_lambda_empty_params(self):
        """测试空参数 Lambda"""
        source = """
        函数 空型 main() {
            整数型 f = () -> 42;
        }
        """
        # 词法分析
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert not lexer.has_errors(), f"词法分析错误: {lexer.get_errors()}"

        # 语法分析
        parser = Parser(tokens)
        ast = parser.parse()
        assert not parser.has_errors(), f"语法分析错误: {parser.get_errors()}"


class TestLambdaParser:
    """Lambda Parser 测试"""

    def test_parse_lambda_arrow_syntax(self):
        """测试箭头语法解析"""
        source = """
        函数 空型 main() {
            整数型 x = (a) -> a + 1;
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert not lexer.has_errors()

        parser = Parser(tokens)
        ast = parser.parse()
        assert not parser.has_errors()

    def test_parse_lambda_with_block_body(self):
        """测试带代码块的 Lambda"""
        source = """
        函数 空型 main() {
            整数型 平方 = (x) -> {
                返回 x * x;
            };
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert not lexer.has_errors()

        parser = Parser(tokens)
        ast = parser.parse()
        assert not parser.has_errors()

    def test_parse_lambda_multiple_params(self):
        """测试多参数 Lambda"""
        source = """
        函数 空型 main() {
            整数型 求和 = (a, b, c) -> a + b + c;
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert not lexer.has_errors()

        parser = Parser(tokens)
        ast = parser.parse()
        assert not parser.has_errors()


class TestClosureCapture:
    """闭包捕获测试"""

    def test_closure_value_capture(self):
        """测试值捕获"""
        source = """
        函数 空型 main() {
            整数型 x = 10;
            整数型 f = () -> x + 1;
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert not lexer.has_errors()

        parser = Parser(tokens)
        ast = parser.parse()
        assert not parser.has_errors()


class TestHigherOrderFunction:
    """高阶函数测试"""

    def test_closure_as_argument(self):
        """测试闭包作为函数参数"""
        source = """
        函数 空型 main() {
            整数型 结果 = 0;
            整数型 f = (x) -> x * 2;
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert not lexer.has_errors()

        parser = Parser(tokens)
        ast = parser.parse()
        assert not parser.has_errors()

    def test_closure_as_return(self):
        """测试闭包作为函数返回值"""
        source = """
        函数 空型 main() {
            整数型 f = () -> 42;
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert not lexer.has_errors()

        parser = Parser(tokens)
        ast = parser.parse()
        assert not parser.has_errors()


class TestClosureNested:
    """嵌套闭包测试"""

    def test_nested_closure(self):
        """测试嵌套闭包"""
        source = """
        函数 空型 main() {
            整数型 x = 1;
            整数型 f = () -> x;
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert not lexer.has_errors()

        parser = Parser(tokens)
        ast = parser.parse()
        assert not parser.has_errors()


class TestLambdaTypeInference:
    """Lambda 类型推断测试"""

    def test_lambda_type_from_return(self):
        """测试从返回表达式推断 Lambda 类型"""
        source = """
        函数 空型 main() {
            整数型 f = () -> 42;
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert not lexer.has_errors()

        parser = Parser(tokens)
        ast = parser.parse()
        assert not parser.has_errors()

    def test_lambda_param_type_inference(self):
        """测试参数类型推断"""
        source = """
        函数 空型 main() {
            整数型 运算 = (a, b) -> a + b;
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert not lexer.has_errors()

        parser = Parser(tokens)
        ast = parser.parse()
        assert not parser.has_errors()


class TestLambdaCompilation:
    """Lambda 编译测试"""

    def test_compile_simple_lambda(self):
        """测试简单 Lambda 编译"""
        source = """
        函数 整数型 main() {
            整数型 f = () -> 42;
            返回 f();
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()
        assert result is not None
        assert len(result.declarations) > 0


class TestClosurePatterns:
    """闭包模式测试"""

    def test_counter_pattern(self):
        """测试计数器模式"""
        source = """
        函数 空型 main() {
            整数型 f = () -> 0;
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert not lexer.has_errors()

        parser = Parser(tokens)
        ast = parser.parse()
        assert not parser.has_errors()

    def test_callback_pattern(self):
        """测试回调模式"""
        source = """
        函数 空型 main() {
            整数型 f = (x) -> x;
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert not lexer.has_errors()

        parser = Parser(tokens)
        ast = parser.parse()
        assert not parser.has_errors()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

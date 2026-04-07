#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZhC 编译器性能基准测试

测试编译器各阶段的性能：
- 词法分析
- 语法分析
- 语义分析
- IR 生成
- 代码生成

作者: 阿福
日期: 2026-04-08
"""

import pytest
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from benchmarks.framework import BenchmarkRunner, BenchmarkReport


# ============================================================================
# 测试数据生成器
# ============================================================================

def generate_simple_function(n: int = 1) -> str:
    """生成简单函数源码
    
    Args:
        n: 函数数量
    """
    functions = []
    for i in range(n):
        functions.append(f"""
函数 测试函数{i}() -> 整数 {{
    返回 {i}
}}
""")
    return "\n".join(functions)


def generate_complex_function(depth: int = 5) -> str:
    """生成复杂嵌套函数源码
    
    Args:
        depth: 嵌套深度
    """
    def build_nested(d: int) -> str:
        if d == 0:
            return "返回 0"
        return f"""
如果 真 {{
    {build_nested(d - 1)}
}} 否则 {{
    返回 1
}}
"""
    return f"""
函数 复杂函数() -> 整数 {{
    {build_nested(depth)}
}}
"""


def generate_large_struct(n: int = 10) -> str:
    """生成大型结构体源码
    
    Args:
        n: 成员数量
    """
    members = []
    for i in range(n):
        members.append(f"    成员{i}: 整数型")
    
    return f"""
结构体 大型结构体 {{
{chr(10).join(members)}
}}
"""


def generate_loop_code(n: int = 100) -> str:
    """生成循环代码源码
    
    Args:
        n: 循环次数
    """
    return f"""
函数 循环测试() -> 整数 {{
    变量 sum: 整数型 = 0
    变量 i: 整数型 = 0
    循环 i < {n} {{
        sum = sum + i
        i = i + 1
    }}
    返回 sum
}}
"""


# ============================================================================
# 基准测试类
# ============================================================================

class TestLexerPerformance:
    """词法分析性能测试"""

    def test_lexer_simple_function(self, benchmark_runner: BenchmarkRunner):
        """测试简单函数词法分析"""
        from parser.lexer import Lexer
        
        source = generate_simple_function(10)
        
        def run_lexer():
            lexer = Lexer(source)
            return lexer.tokenize()
        
        result = benchmark_runner.run("lexer.simple_function", run_lexer)
        assert result.avg_time < 1.0  # 应该在 1 秒内完成

    def test_lexer_complex_function(self, benchmark_runner: BenchmarkRunner):
        """测试复杂函数词法分析"""
        from parser.lexer import Lexer
        
        source = generate_complex_function(10)
        
        def run_lexer():
            lexer = Lexer(source)
            return lexer.tokenize()
        
        result = benchmark_runner.run("lexer.complex_function", run_lexer)
        assert result.avg_time < 1.0

    def test_lexer_large_source(self, benchmark_runner: BenchmarkRunner):
        """测试大型源码词法分析"""
        from parser.lexer import Lexer
        
        source = generate_simple_function(100)
        
        def run_lexer():
            lexer = Lexer(source)
            return lexer.tokenize()
        
        result = benchmark_runner.run("lexer.large_source", run_lexer)
        assert result.avg_time < 2.0


class TestParserPerformance:
    """语法分析性能测试"""

    def test_parser_simple_function(self, benchmark_runner: BenchmarkRunner):
        """测试简单函数语法分析"""
        from parser.lexer import Lexer
        from parser.parser import Parser
        
        source = generate_simple_function(10)
        
        def run_parser():
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            return parser.parse()
        
        result = benchmark_runner.run("parser.simple_function", run_parser)
        assert result.avg_time < 2.0

    def test_parser_complex_function(self, benchmark_runner: BenchmarkRunner):
        """测试复杂函数语法分析"""
        from parser.lexer import Lexer
        from parser.parser import Parser
        
        source = generate_complex_function(10)
        
        def run_parser():
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            return parser.parse()
        
        result = benchmark_runner.run("parser.complex_function", run_parser)
        assert result.avg_time < 3.0

    def test_parser_struct(self, benchmark_runner: BenchmarkRunner):
        """测试结构体语法分析"""
        from parser.lexer import Lexer
        from parser.parser import Parser
        
        source = generate_large_struct(50)
        
        def run_parser():
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            return parser.parse()
        
        result = benchmark_runner.run("parser.struct", run_parser)
        assert result.avg_time < 2.0


class TestCodegenPerformance:
    """代码生成性能测试"""

    def test_codegen_simple_function(self, benchmark_runner: BenchmarkRunner):
        """测试简单函数代码生成"""
        from parser.lexer import Lexer
        from parser.parser import Parser
        from codegen.c_codegen import CCodeGenerator
        
        source = generate_simple_function(10)
        
        def run_codegen():
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            gen = CCodeGenerator()
            return gen.generate(ast)
        
        result = benchmark_runner.run("codegen.simple_function", run_codegen)
        assert result.avg_time < 3.0

    def test_codegen_loop(self, benchmark_runner: BenchmarkRunner):
        """测试循环代码生成"""
        from parser.lexer import Lexer
        from parser.parser import Parser
        from codegen.c_codegen import CCodeGenerator
        
        source = generate_loop_code(100)
        
        def run_codegen():
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            gen = CCodeGenerator()
            return gen.generate(ast)
        
        result = benchmark_runner.run("codegen.loop", run_codegen)
        assert result.avg_time < 3.0


class TestFullPipelinePerformance:
    """完整编译流程性能测试"""

    def test_full_pipeline_simple(self, benchmark_runner: BenchmarkRunner):
        """测试完整编译流程（简单）"""
        from parser.lexer import Lexer
        from parser.parser import Parser
        from codegen.c_codegen import CCodeGenerator
        
        source = generate_simple_function(5)
        
        def run_full_pipeline():
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            gen = CCodeGenerator()
            return gen.generate(ast)
        
        result = benchmark_runner.run("pipeline.simple", run_full_pipeline)
        assert result.avg_time < 5.0

    def test_full_pipeline_complex(self, benchmark_runner: BenchmarkRunner):
        """测试完整编译流程（复杂）"""
        from parser.lexer import Lexer
        from parser.parser import Parser
        from codegen.c_codegen import CCodeGenerator
        
        source = generate_complex_function(5) + generate_simple_function(5)
        
        def run_full_pipeline():
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            gen = CCodeGenerator()
            return gen.generate(ast)
        
        result = benchmark_runner.run("pipeline.complex", run_full_pipeline)
        assert result.avg_time < 10.0


# ============================================================================
# pytest fixture
# ============================================================================

@pytest.fixture
def benchmark_runner():
    """基准测试运行器 fixture"""
    return BenchmarkRunner(warmup=1, iterations=5)


# ============================================================================
# 报告生成
# ============================================================================

def generate_benchmark_report(results_file: str = None):
    """生成基准测试报告
    
    Args:
        results_file: 报告输出文件路径
    """
    runner = BenchmarkRunner(warmup=2, iterations=10)
    
    # 运行所有测试
    from parser.lexer import Lexer
    from parser.parser import Parser
    from codegen.c_codegen import CCodeGenerator
    
    # 词法分析测试
    for n in [10, 50, 100]:
        source = generate_simple_function(n)
        runner.run(f"lexer.functions_{n}", lambda: Lexer(source).tokenize())
    
    # 语法分析测试
    for n in [10, 50, 100]:
        source = generate_simple_function(n)
        def parse():
            tokens = Lexer(source).tokenize()
            return Parser(tokens).parse()
        runner.run(f"parser.functions_{n}", parse)
    
    # 代码生成测试
    for n in [10, 50, 100]:
        source = generate_simple_function(n)
        def codegen():
            tokens = Lexer(source).tokenize()
            ast = Parser(tokens).parse()
            return CCodeGenerator().generate(ast)
        runner.run(f"codegen.functions_{n}", codegen)
    
    # 生成报告
    results = runner.get_results()
    
    # 文本报告
    text_report = BenchmarkReport.generate_text(results)
    print(text_report)
    
    # Markdown 报告
    md_report = BenchmarkReport.generate_markdown(results)
    
    if results_file:
        with open(results_file, 'w', encoding='utf-8') as f:
            f.write(md_report)
    
    return results


if __name__ == "__main__":
    # 直接运行生成报告
    generate_benchmark_report("benchmark_report.md")

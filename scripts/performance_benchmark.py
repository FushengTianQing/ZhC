#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能基准测试脚本

测试 ZHC 编译器各阶段的性能，建立性能基线。

创建日期: 2026-04-07
最后更新: 2026-04-07
维护者: ZHC开发团队
"""

import sys
from pathlib import Path

# 注册 zhc 包（src 目录）
src_path = Path(__file__).parent.parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path.parent))
    import src
    sys.modules["zhc"] = sys.modules["src"]

import time
import json
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class PerformanceMetrics:
    """性能指标"""
    stage: str                    # 编译阶段
    iterations: int               # 迭代次数
    total_time: float             # 总时间（秒）
    avg_time: float               # 平均时间（秒）
    min_time: float               # 最小时间（秒）
    max_time: float               # 最大时间（秒）
    std_dev: float                # 标准差
    ops_per_second: float         # 每秒操作数
    memory_mb: Optional[float] = None  # 内存使用（MB）
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    timestamp: str
    python_version: str
    platform: str
    metrics: Dict[str, PerformanceMetrics] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "python_version": self.python_version,
            "platform": self.platform,
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()}
        }


class PerformanceBenchmark:
    """性能基准测试"""
    
    def __init__(self, iterations: int = 100, warmup: int = 10):
        """
        初始化性能基准测试
        
        Args:
            iterations: 测试迭代次数
            warmup: 预热次数（不计入统计）
        """
        self.iterations = iterations
        self.warmup = warmup
        self.results: Dict[str, List[float]] = {}
    
    def measure(self, func, *args, **kwargs) -> float:
        """
        测量函数执行时间
        
        Args:
            func: 要测量的函数
            *args, **kwargs: 函数参数
            
        Returns:
            执行时间（秒）
        """
        # 预热
        for _ in range(self.warmup):
            func(*args, **kwargs)
        
        # 正式测量
        times = []
        for _ in range(self.iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            end = time.perf_counter()
            times.append(end - start)
        
        return times
    
    def benchmark_lexer(self, source: str) -> PerformanceMetrics:
        """
        测试 Lexer 性能
        
        Args:
            source: 源代码字符串
            
        Returns:
            性能指标
        """
        from zhc.parser.lexer import Lexer
        
        times = self.measure(lambda: Lexer(source).tokenize())
        
        return self._calculate_metrics("Lexer", times, len(source))
    
    def benchmark_parser(self, source: str) -> PerformanceMetrics:
        """
        测试 Parser 性能
        
        Args:
            source: 源代码字符串
            
        Returns:
            性能指标
        """
        from zhc.parser.parser import Parser
        from zhc.parser.lexer import Lexer
        
        # 先词法分析
        tokens = Lexer(source).tokenize()
        
        times = self.measure(lambda: Parser(tokens).parse())
        
        return self._calculate_metrics("Parser", times, len(source))
    
    def benchmark_semantic(self, source: str) -> PerformanceMetrics:
        """
        测试 Semantic 性能
        
        Args:
            source: 源代码字符串
            
        Returns:
            性能指标
        """
        from zhc.parser.lexer import Lexer
        from zhc.parser.parser import Parser
        from zhc.semantic.semantic_analyzer import SemanticAnalyzer
        
        # 先词法分析和语法分析
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        
        times = self.measure(lambda: SemanticAnalyzer().analyze(ast))
        
        return self._calculate_metrics("Semantic", times, len(source))
    
    def benchmark_codegen(self, source: str) -> PerformanceMetrics:
        """
        测试 CodeGen 性能
        
        Args:
            source: 源代码字符串
            
        Returns:
            性能指标
        """
        from zhc.parser.lexer import Lexer
        from zhc.parser.parser import Parser
        from zhc.semantic.semantic_analyzer import SemanticAnalyzer
        from zhc.codegen.c_codegen import CCodeGenerator
        
        # 先完成前端编译
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        SemanticAnalyzer().analyze(ast)
        
        times = self.measure(lambda: CCodeGenerator().generate(ast))
        
        return self._calculate_metrics("CodeGen", times, len(source))
    
    def benchmark_full_pipeline(self, source: str) -> PerformanceMetrics:
        """
        测试完整编译流水线性能
        
        Args:
            source: 源代码字符串
            
        Returns:
            性能指标
        """
        from zhc.parser.lexer import Lexer
        from zhc.parser.parser import Parser
        from zhc.semantic.semantic_analyzer import SemanticAnalyzer
        from zhc.codegen.c_codegen import CCodeGenerator
        
        def compile_pipeline():
            tokens = Lexer(source).tokenize()
            ast = Parser(tokens).parse()
            SemanticAnalyzer().analyze(ast)
            return CCodeGenerator().generate(ast)
        
        times = self.measure(compile_pipeline)
        
        return self._calculate_metrics("FullPipeline", times, len(source))
    
    def _calculate_metrics(self, stage: str, times: List[float], source_size: int) -> PerformanceMetrics:
        """
        计算性能指标
        
        Args:
            stage: 编译阶段
            times: 时间列表
            source_size: 源代码大小（字符数）
            
        Returns:
            性能指标
        """
        avg_time = statistics.mean(times)
        
        return PerformanceMetrics(
            stage=stage,
            iterations=len(times),
            total_time=sum(times),
            avg_time=avg_time,
            min_time=min(times),
            max_time=max(times),
            std_dev=statistics.stdev(times) if len(times) > 1 else 0.0,
            ops_per_second=1.0 / avg_time if avg_time > 0 else 0.0,
        )
    
    def generate_test_source(self, size: str = "medium") -> str:
        """
        生成测试源代码
        
        Args:
            size: 代码大小（small/medium/large）
            
        Returns:
            测试源代码
        """
        if size == "small":
            # 简单函数
            return """
函数 主函数() {
    整数型 x = 10;
    整数型 y = 20;
    整数型 z = x + y;
    返回 z;
}
"""
        elif size == "medium":
            # 中等复杂度代码
            lines = []
            lines.append("函数 主函数() {")
            lines.append("    整数型 总和 = 0;")
            lines.append("    整数型 i = 0;")
            lines.append("    当 (i < 100) {")
            lines.append("        总和 = 总和 + i;")
            lines.append("        i = i + 1;")
            lines.append("    }")
            
            # 添加多个函数
            for i in range(10):
                lines.append(f"")
                lines.append(f"函数 函数{i}(整数型 a, 整数型 b) {{")
                lines.append(f"    整数型 结果 = a * b;")
                lines.append(f"    返回 结果;")
                lines.append(f"}}")
            
            lines.append("    返回 总和;")
            lines.append("}")
            
            return "\n".join(lines)
        
        else:  # large
            # 大型代码
            lines = []
            
            # 结构体定义
            for i in range(5):
                lines.append(f"结构体 数据{i} {{")
                lines.append(f"    整数型 字段1;")
                lines.append(f"    浮点型 字段2;")
                lines.append(f"    字符型 字段3;")
                lines.append(f"}}")
                lines.append(f"")
            
            # 函数定义
            for i in range(50):
                lines.append(f"函数 函数{i}(整数型 参数1, 整数型 参数2) {{")
                lines.append(f"    整数型 局部变量 = 参数1 + 参数2;")
                
                # 嵌套控制流
                if i % 3 == 0:
                    lines.append(f"    当 (局部变量 < 100) {{")
                    lines.append(f"        局部变量 = 局部变量 + 1;")
                    lines.append(f"    }}")
                elif i % 3 == 1:
                    lines.append(f"    如果 (局部变量 > 50) {{")
                    lines.append(f"        局部变量 = 局部变量 * 2;")
                    lines.append(f"    }} 否则 {{")
                    lines.append(f"        局部变量 = 局部变量 / 2;")
                    lines.append(f"    }}")
                else:
                    lines.append(f"    对于 (整数型 j = 0; j < 10; j = j + 1) {{")
                    lines.append(f"        局部变量 = 局部变量 + j;")
                    lines.append(f"    }}")
                
                lines.append(f"    返回 局部变量;")
                lines.append(f"}}")
                lines.append(f"")
            
            # 主函数
            lines.append("函数 主函数() {")
            lines.append("    整数型 结果 = 0;")
            lines.append("    对于 (整数型 i = 0; i < 50; i = i + 1) {")
            lines.append("        结果 = 结果 + 函数{i}(i, i + 1);")
            lines.append("    }")
            lines.append("    返回 结果;")
            lines.append("}")
            
            return "\n".join(lines)
    
    def run_all_benchmarks(self, size: str = "medium") -> BenchmarkResult:
        """
        运行所有基准测试
        
        Args:
            size: 测试代码大小
            
        Returns:
            基准测试结果
        """
        import sys
        import platform
        
        source = self.generate_test_source(size)
        
        result = BenchmarkResult(
            timestamp=datetime.now().isoformat(),
            python_version=sys.version,
            platform=platform.platform(),
        )
        
        print(f"性能基准测试开始")
        print(f"测试代码大小: {size} ({len(source)} 字符)")
        print(f"迭代次数: {self.iterations}, 预热次数: {self.warmup}")
        print(f"{'='*60}")
        
        # Lexer
        print("\n测试 Lexer 性能...")
        result.metrics["lexer"] = self.benchmark_lexer(source)
        self._print_metrics(result.metrics["lexer"])
        
        # Parser
        print("\n测试 Parser 性能...")
        result.metrics["parser"] = self.benchmark_parser(source)
        self._print_metrics(result.metrics["parser"])
        
        # Semantic
        print("\n测试 Semantic 性能...")
        result.metrics["semantic"] = self.benchmark_semantic(source)
        self._print_metrics(result.metrics["semantic"])
        
        # CodeGen
        print("\n测试 CodeGen 性能...")
        result.metrics["codegen"] = self.benchmark_codegen(source)
        self._print_metrics(result.metrics["codegen"])
        
        # Full Pipeline
        print("\n测试完整编译流水线性能...")
        result.metrics["full_pipeline"] = self.benchmark_full_pipeline(source)
        self._print_metrics(result.metrics["full_pipeline"])
        
        print(f"\n{'='*60}")
        print("性能基准测试完成")
        
        return result
    
    def _print_metrics(self, metrics: PerformanceMetrics):
        """打印性能指标"""
        print(f"  平均时间: {metrics.avg_time*1000:.3f} ms")
        print(f"  最小时间: {metrics.min_time*1000:.3f} ms")
        print(f"  最大时间: {metrics.max_time*1000:.3f} ms")
        print(f"  标准差: {metrics.std_dev*1000:.3f} ms")
        print(f"  每秒操作数: {metrics.ops_per_second:.2f}")
    
    def save_results(self, result: BenchmarkResult, output_file: str):
        """
        保存测试结果到 JSON 文件
        
        Args:
            result: 测试结果
            output_file: 输出文件路径
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        
        print(f"\n结果已保存到: {output_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ZHC 编译器性能基准测试')
    parser.add_argument('--size', choices=['small', 'medium', 'large'], 
                       default='medium', help='测试代码大小')
    parser.add_argument('--iterations', type=int, default=100,
                       help='测试迭代次数')
    parser.add_argument('--warmup', type=int, default=10,
                       help='预热次数')
    parser.add_argument('--output', type=str, default='benchmark_results.json',
                       help='输出文件路径')
    
    args = parser.parse_args()
    
    # 创建基准测试实例
    benchmark = PerformanceBenchmark(
        iterations=args.iterations,
        warmup=args.warmup
    )
    
    # 运行测试
    result = benchmark.run_all_benchmarks(size=args.size)
    
    # 保存结果
    benchmark.save_results(result, args.output)


if __name__ == '__main__':
    main()

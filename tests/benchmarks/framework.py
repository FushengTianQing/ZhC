#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZhC 编译性能基准测试框架

提供统一的性能测试和报告生成功能。

作者: 阿福
日期: 2026-04-08
"""

import time
import tracemalloc
import functools
from typing import Callable, Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from statistics import mean, stdev, median


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    name: str
    iterations: int
    total_time: float  # 秒
    avg_time: float  # 秒
    min_time: float  # 秒
    max_time: float  # 秒
    std_dev: float  # 秒
    memory_peak: int  # 字节
    memory_avg: int  # 字节

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time_s": self.total_time,
            "avg_time_ms": self.avg_time * 1000,
            "min_time_ms": self.min_time * 1000,
            "max_time_ms": self.max_time * 1000,
            "std_dev_ms": self.std_dev * 1000,
            "memory_peak_mb": self.memory_peak / 1024 / 1024,
            "memory_avg_mb": self.memory_avg / 1024 / 1024,
        }


class BenchmarkRunner:
    """基准测试运行器"""

    def __init__(self, warmup: int = 1, iterations: int = 10):
        """
        初始化基准测试运行器

        Args:
            warmup: 预热迭代次数
            iterations: 实际测试迭代次数
        """
        self.warmup = warmup
        self.iterations = iterations
        self.results: List[BenchmarkResult] = []

    def run(
        self,
        name: str,
        func: Callable,
        *args,
        **kwargs
    ) -> BenchmarkResult:
        """
        运行基准测试

        Args:
            name: 测试名称
            func: 要测试的函数
            *args, **kwargs: 传递给函数的参数

        Returns:
            BenchmarkResult: 测试结果
        """
        # 预热
        for _ in range(self.warmup):
            func(*args, **kwargs)

        # 实际测试
        times: List[float] = []
        memory_peaks: List[int] = []
        memory_avgs: List[int] = []

        for _ in range(self.iterations):
            tracemalloc.start()
            start = time.perf_counter()
            func(*args, **kwargs)
            end = time.perf_counter()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            times.append(end - start)
            memory_peaks.append(peak)
            memory_avgs.append(current)

        result = BenchmarkResult(
            name=name,
            iterations=self.iterations,
            total_time=sum(times),
            avg_time=mean(times),
            min_time=min(times),
            max_time=max(times),
            std_dev=stdev(times) if len(times) > 1 else 0,
            memory_peak=max(memory_peaks),
            memory_avg=int(mean(memory_avgs)),
        )

        self.results.append(result)
        return result

    def run_comparison(
        self,
        name: str,
        funcs: Dict[str, Callable],
        *args,
        **kwargs
    ) -> Dict[str, BenchmarkResult]:
        """
        运行对比测试

        Args:
            name: 测试名称
            funcs: 函数字典 {name: func}
            *args, **kwargs: 传递给函数的参数

        Returns:
            Dict[str, BenchmarkResult]: 各函数测试结果
        """
        results = {}
        for func_name, func in funcs.items():
            full_name = f"{name}.{func_name}"
            result = self.run(full_name, func, *args, **kwargs)
            results[func_name] = result
        return results

    def get_results(self) -> List[BenchmarkResult]:
        """获取所有测试结果"""
        return self.results

    def clear_results(self):
        """清空测试结果"""
        self.results = []


def benchmark(
    name: str = None,
    iterations: int = 10,
    warmup: int = 1,
):
    """
    基准测试装饰器

    Args:
        name: 测试名称，默认使用函数名
        iterations: 迭代次数
        warmup: 预热次数

    Example:
        @benchmark(name="my_function", iterations=100)
        def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        _name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            runner = BenchmarkRunner(warmup=warmup, iterations=iterations)
            result = runner.run(_name, func, *args, **kwargs)
            return result

        return wrapper
    return decorator


class BenchmarkReport:
    """基准测试报告生成器"""

    @staticmethod
    def generate_text(results: List[BenchmarkResult]) -> str:
        """生成文本格式报告"""
        lines = []
        lines.append("=" * 80)
        lines.append("ZhC 编译性能基准测试报告")
        lines.append("=" * 80)
        lines.append("")

        if not results:
            lines.append("没有测试结果")
            return "\n".join(lines)

        # 表头
        lines.append(f"{'名称':<40} {'平均时间(ms)':<15} {'峰值内存(MB)':<15}")
        lines.append("-" * 80)

        # 数据行
        for result in sorted(results, key=lambda x: x.avg_time):
            lines.append(
                f"{result.name:<40} "
                f"{result.avg_time * 1000:>10.3f} ms  "
                f"{result.memory_peak / 1024 / 1024:>10.3f} MB"
            )

        lines.append("")
        lines.append("=" * 80)

        # 统计摘要
        if results:
            total_time = sum(r.total_time for r in results)
            avg_time = mean(r.avg_time for r in results)
            total_memory = sum(r.memory_peak for r in results)
            lines.append(f"总测试时间: {total_time:.3f} 秒")
            lines.append(f"平均执行时间: {avg_time * 1000:.3f} ms")
            lines.append(f"总峰值内存: {total_memory / 1024 / 1024:.3f} MB")

        lines.append("=" * 80)

        return "\n".join(lines)

    @staticmethod
    def generate_markdown(results: List[BenchmarkResult]) -> str:
        """生成 Markdown 格式报告"""
        lines = []
        lines.append("# ZhC 编译性能基准测试报告")
        lines.append("")
        lines.append("## 测试结果")
        lines.append("")

        if not results:
            lines.append("*没有测试结果*")
            return "\n".join(lines)

        # Markdown 表格
        lines.append("| 名称 | 平均时间 | 最小时间 | 最大时间 | 峰值内存 |")
        lines.append("|:-----|:--------:|:--------:|:--------:|:--------:|")

        for result in sorted(results, key=lambda x: x.avg_time):
            lines.append(
                f"| {result.name} | "
                f"{result.avg_time * 1000:.3f} ms | "
                f"{result.min_time * 1000:.3f} ms | "
                f"{result.max_time * 1000:.3f} ms | "
                f"{result.memory_peak / 1024 / 1024:.3f} MB |"
            )

        lines.append("")
        lines.append("## 统计摘要")
        lines.append("")

        if results:
            total_time = sum(r.total_time for r in results)
            avg_time = mean(r.avg_time for r in results)
            total_memory = sum(r.memory_peak for r in results)

            lines.append(f"- **总测试时间**: {total_time:.3f} 秒")
            lines.append(f"- **平均执行时间**: {avg_time * 1000:.3f} ms")
            lines.append(f"- **总峰值内存**: {total_memory / 1024 / 1024:.3f} MB")
            lines.append(f"- **测试用例数**: {len(results)}")

        lines.append("")
        lines.append("---")
        lines.append("*报告生成时间: 自动生成*")

        return "\n".join(lines)

    @staticmethod
    def generate_json(results: List[BenchmarkResult]) -> Dict[str, Any]:
        """生成 JSON 格式报告"""
        return {
            "results": [r.to_dict() for r in results],
            "summary": {
                "total_tests": len(results),
                "total_time_s": sum(r.total_time for r in results),
                "avg_time_ms": mean(r.avg_time for r in results) * 1000 if results else 0,
                "total_memory_mb": sum(r.memory_peak for r in results) / 1024 / 1024,
            }
        }

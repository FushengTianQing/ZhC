# -*- coding: utf-8 -*-
"""
Day 5: 性能优化器（向后兼容入口）

本文件已重构为子模块形式：
- src/compiler/optimizer/__init__.py  导出所有类
- src/compiler/optimizer/performance_monitor.py
- src/compiler/optimizer/algorithm_optimizer.py
- src/compiler/optimizer/concurrent_compiler.py
- src/compiler/optimizer/incremental_optimizer.py

保留此文件作为向后兼容导入入口。
"""

import time

# 重新导出所有类（保持向后兼容）
from .optimizer import (
    PerformanceMonitor,
    AlgorithmOptimizer,
    ConcurrentCompiler,
    IncrementalOptimizer,
)

__all__ = [
    "PerformanceMonitor",
    "AlgorithmOptimizer",
    "ConcurrentCompiler",
    "IncrementalOptimizer",
]


def test_performance_optimizer():
    """测试性能优化器"""
    print("🧪 测试性能优化器...")

    # 测试算法优化器
    print("\n1. 测试算法优化器:")

    # 创建一个测试依赖图
    test_graph = {
        "A": ["B", "C"],
        "B": ["C", "D"],
        "C": ["D"],
        "D": [],
        "E": ["A", "B"],
    }

    print("   原始依赖图:", test_graph)

    optimized_graph, levels = AlgorithmOptimizer.optimize_dependency_resolution(
        test_graph
    )
    print("   优化后依赖图:", optimized_graph)
    print("   节点层级:", levels)

    # 验证优化结果
    assert "A" in optimized_graph
    assert "B" in optimized_graph
    assert len(optimized_graph["A"]) <= len(test_graph["A"])

    print("   ✅ 算法优化测试通过")

    # 测试内存优化
    print("\n2. 测试内存优化:")

    test_data = {
        "large_list": list(range(1000)),
        "nested_dict": {
            f"key{i}": {f"subkey{j}": j for j in range(10)} for i in range(10)
        },
        "set_data": set(range(100)),
    }

    AlgorithmOptimizer.optimize_memory_usage(test_data)
    print("   ✅ 内存优化测试通过")

    # 测试性能监控器
    print("\n3. 测试性能监控器:")

    monitor = PerformanceMonitor()

    # 模拟一些性能数据
    parse_start = monitor.start_phase("parse_time")
    time.sleep(0.01)
    monitor.end_phase("parse_time", parse_start)

    convert_start = monitor.start_phase("convert_time")
    time.sleep(0.02)
    monitor.end_phase("convert_time", convert_start)

    # 获取报告
    summary = monitor.get_summary()
    assert "total_time" in summary
    assert "peak_memory_mb" in summary
    assert "phases" in summary

    print("   性能摘要:", {k: v for k, v in summary.items() if k != "phases"})
    print("   ✅ 性能监控测试通过")

    print("\n🎉 性能优化器测试全部通过！")


if __name__ == "__main__":
    test_performance_optimizer()

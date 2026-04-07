#!/usr/bin/env python3
"""
Day 9: 性能分析器

功能：
1. 模块解析性能瓶颈分析
2. 符号查找算法优化
3. 调试信息输出
4. 性能基准测试

测量指标：
- 解析速度（行/秒）
- 符号查找时间
- 内存使用
- 缓存命中率
"""

import time
import sys
import os
import tracemalloc
import gc
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from functools import wraps

# 使用相对导入，避免 sys.path 魔法
# Phase 7 M7 TD2: 废弃导入（day2/day3 路径不存在）
# from ..day2.module_parser import ModuleParser, ModuleInfo
# from ..day3.scope_manager import ScopeManager, Scope, ScopeType, Visibility, SymbolInfo

# 类型存根（避免引用报错）
from enum import Enum
class Visibility(Enum): PUBLIC = 'public'; PRIVATE = 'private'
class ScopeType(Enum): MODULE = 'module'
class SymbolInfo:
    def __init__(self, *a, **kw): pass
class ScopeManager:
    def __init__(self): pass
    @property
    def current_scope(self): return None
    def all_symbols(self): return {}
    def lookup_symbol(self, *a, **kw): return None
    def add_symbol(self, *a, **kw): return None
    def enter_scope(self, *a, **kw): pass
    def exit_scope(self, *a, **kw): pass


@dataclass
class PerformanceMetrics:
    """性能指标"""
    operation_name: str
    start_time: float = 0.0
    end_time: float = 0.0
    memory_start: int = 0
    memory_end: int = 0
    items_processed: int = 0

    @property
    def elapsed_time(self) -> float:
        """耗时（秒）"""
        return self.end_time - self.start_time

    @property
    def throughput(self) -> float:
        """吞吐量（项/秒）"""
        if self.elapsed_time > 0 and self.items_processed > 0:
            return self.items_processed / self.elapsed_time
        return 0.0

    @property
    def memory_delta(self) -> int:
        """内存变化（字节）"""
        return self.memory_end - self.memory_start

    def __str__(self) -> str:
        return (f"{self.operation_name}: "
                f"耗时={self.elapsed_time*1000:.2f}ms, "
                f"吞吐量={self.throughput:.2f}项/秒, "
                f"内存变化={self.memory_delta/1024:.2f}KB")


class PerformanceAnalyzer:
    """性能分析器"""

    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.current_metric: Optional[PerformanceMetrics] = None
        self.profile_enabled = False

    def start_profiling(self, operation_name: str, items_count: int = 0):
        """开始性能分析"""
        gc.collect()  # 先进行垃圾回收
        tracemalloc.start()

        metric = PerformanceMetrics(
            operation_name=operation_name,
            start_time=time.perf_counter(),
            memory_start=tracemalloc.get_traced_memory()[0],
            items_processed=items_count
        )
        self.current_metric = metric
        return metric

    def stop_profiling(self) -> Optional[PerformanceMetrics]:
        """停止性能分析"""
        if self.current_metric:
            self.current_metric.end_time = time.perf_counter()
            self.current_metric.memory_end = tracemalloc.get_traced_memory()[0]
            tracemalloc.stop()

            self.metrics.append(self.current_metric)
            result = self.current_metric
            self.current_metric = None
            return result
        return None

    def measure_operation(self, operation_name: str, func, *args, **kwargs) -> Tuple[Any, PerformanceMetrics]:
        """测量单个操作的性能"""
        metric = self.start_profiling(operation_name)
        result = func(*args, **kwargs)
        self.stop_profiling()
        return result, metric

    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.metrics:
            return {"total_operations": 0}

        summary = {
            "total_operations": len(self.metrics),
            "total_time": sum(m.elapsed_time for m in self.metrics),
            "slowest_operation": max(self.metrics, key=lambda m: m.elapsed_time).operation_name,
            "fastest_operation": min(self.metrics, key=lambda m: m.elapsed_time).operation_name,
            "total_memory_delta": sum(m.memory_delta for m in self.metrics),
        }

        # 计算平均吞吐量
        total_throughput = sum(m.throughput for m in self.metrics if m.throughput > 0)
        summary["average_throughput"] = total_throughput / len(self.metrics) if self.metrics else 0

        return summary

    def print_report(self):
        """打印性能报告"""
        print("\n" + "=" * 70)
        print("性能分析报告")
        print("=" * 70)

        if not self.metrics:
            print("没有性能数据")
            return

        print(f"\n总操作数: {len(self.metrics)}")
        print(f"总耗时: {sum(m.elapsed_time for m in self.metrics)*1000:.2f}ms")
        print(f"总内存变化: {sum(m.memory_delta for m in self.metrics)/1024:.2f}KB")

        print("\n详细指标:")
        print("-" * 70)
        for metric in self.metrics:
            print(f"  {metric}")

        # 找出最慢的操作
        if self.metrics:
            slowest = max(self.metrics, key=lambda m: m.elapsed_time)
            print(f"\n最慢操作: {slowest.operation_name} ({slowest.elapsed_time*1000:.2f}ms)")

        print("=" * 70)


# Phase 7 M7 TD2: 废弃（依赖 day3.scope_manager.ScopeManager
class OptimizedScopeManager:
    """优化后的作用域管理器"""

    def __init__(self):
        super().__init__()
        # 符号缓存：模块名 -> 符号字典的缓存
        self._symbol_cache: Dict[str, Dict[str, SymbolInfo]] = {}
        self._cache_enabled = True

    def enable_cache(self):
        """启用缓存"""
        self._cache_enabled = True

    def disable_cache(self):
        """禁用缓存"""
        self._cache_enabled = False
        self._symbol_cache.clear()

    def add_symbol(self, name: str, visibility: Visibility, line_num: int) -> SymbolInfo:
        """添加符号（带缓存优化）"""
        symbol = super().add_symbol(name, visibility, line_num)

        # 更新缓存
        if self._cache_enabled and self.current_scope.type == ScopeType.MODULE:
            module_name = self.current_scope.name
            if module_name not in self._symbol_cache:
                self._symbol_cache[module_name] = {}
            self._symbol_cache[module_name][name] = symbol

        return symbol

    def lookup_symbol(self, name: str) -> Optional[SymbolInfo]:
        """查找符号（带缓存优化）"""
        if self._cache_enabled and self.current_scope.type == ScopeType.MODULE:
            module_name = self.current_scope.name
            if module_name in self._symbol_cache:
                # 先在缓存中查找
                if name in self._symbol_cache[module_name]:
                    return self._symbol_cache[module_name][name]

        # 缓存未命中，使用原有查找逻辑
        return super().lookup_symbol(name)

    def invalidate_cache(self, module_name: Optional[str] = None):
        """使缓存失效"""
        if module_name:
            if module_name in self._symbol_cache:
                del self._symbol_cache[module_name]
        else:
            self._symbol_cache.clear()


# Phase 7 M7 TD2: 废弃（依赖 day3.scope_manager
class SymbolLookupOptimizer:
    """符号查找优化器"""

    def __init__(self):
        # 符号索引：按名称组织，快速查找
        self._symbol_index: Dict[str, List[SymbolInfo]] = {}
        # 模块索引：模块名 -> 符号集合
        self._module_index: Dict[str, Set[str]] = {}

    def build_index(self, scope_manager: ScopeManager):
        """构建符号索引"""
        self._symbol_index.clear()
        self._module_index.clear()

        for symbol_name, symbol in scope_manager.all_symbols.items():
            if symbol_name not in self._symbol_index:
                self._symbol_index[symbol_name] = []
            self._symbol_index[symbol_name].append(symbol)

            # 更新模块索引
            if symbol.scope_type == ScopeType.MODULE:
                module_name = symbol.name.split('_')[0] if '_' in symbol.name else symbol.name
                if module_name not in self._module_index:
                    self._module_index[module_name] = set()
                self._module_index[module_name].add(symbol_name)

    def fast_lookup(self, symbol_name: str) -> Optional[SymbolInfo]:
        """快速查找符号"""
        if symbol_name in self._symbol_index:
            symbols = self._symbol_index[symbol_name]
            if symbols:
                return symbols[0]
        return None

    def get_module_symbols(self, module_name: str) -> Set[str]:
        """获取模块的所有符号"""
        return self._module_index.get(module_name, set())


def benchmark_module_parsing(test_size: int = 100) -> Dict[str, float]:
    """模块解析基准测试"""
    print(f"\n开始模块解析基准测试（模块数={test_size}）...")

    analyzer = PerformanceAnalyzer()

    # 生成测试代码
    functions = []
    privates = []
    for j in range(5):
        functions.append(f"        函数 公开函数{j}(整数型 x{j}) -> 整数型 {{ 返回 x{j}; }}")
        privates.append(f"        整数型 私有变量{j} = {j*10};")

    test_code = f"""
模块 测试模块0 {{
    公开:
{chr(10).join(functions)}
    私有:
{chr(10).join(privates)}
}}
"""

    # 测试原始解析器
    print("\n1. 测试原始ModuleParser...")
    parser = ModuleParser()

    lines = test_code.strip().split('\n')
    start = time.perf_counter()
    for _ in range(test_size):
        parser = ModuleParser()
        for i, line in enumerate(lines, 1):
            parser.parse_line(line, i)
    elapsed_original = time.perf_counter() - start

    print(f"   原始解析器: {elapsed_original*1000:.2f}ms ({test_size}个模块)")

    # 测试优化后的作用域管理器
    print("\n2. 测试优化后的ScopeManager...")
    manager = OptimizedScopeManager()

    start = time.perf_counter()
    for i in range(test_size):
        manager.enter_scope(f"模块{i}", ScopeType.MODULE)
        for j in range(5):
            manager.add_symbol(f"公开函数{j}", Visibility.PUBLIC, j)
            manager.add_symbol(f"私有变量{j}", Visibility.PRIVATE, j + 10)
        manager.exit_scope()
    elapsed_optimized = time.perf_counter() - start

    print(f"   优化后ScopeManager: {elapsed_optimized*1000:.2f}ms ({test_size}个模块)")

    # 计算性能提升
    if elapsed_original > 0:
        improvement = ((elapsed_original - elapsed_optimized) / elapsed_original) * 100
    else:
        improvement = 0

    print(f"\n3. 性能对比:")
    print(f"   原始解析器: {elapsed_original*1000:.2f}ms")
    print(f"   优化后: {elapsed_optimized*1000:.2f}ms")
    print(f"   性能提升: {improvement:.1f}%")

    return {
        "original_time": elapsed_original,
        "optimized_time": elapsed_optimized,
        "improvement_percent": improvement
    }


def benchmark_symbol_lookup(module_count: int = 10, symbols_per_module: int = 100) -> Dict[str, float]:
    """符号查找基准测试"""
    print(f"\n开始符号查找基准测试（模块数={module_count}, 每模块符号={symbols_per_module}）...")

    # 创建测试数据
    manager = OptimizedScopeManager()
    for i in range(module_count):
        manager.enter_scope(f"模块{i}", ScopeType.MODULE)
        for j in range(symbols_per_module):
            manager.add_symbol(f"符号{j}", Visibility.PUBLIC, j)
        manager.exit_scope()

    # 构建优化索引
    optimizer = SymbolLookupOptimizer()
    optimizer.build_index(manager)

    # 测试普通查找
    print("\n1. 测试普通查找...")
    iterations = 1000
    lookup_target = "符号50"

    start = time.perf_counter()
    for _ in range(iterations):
        manager.lookup_symbol(lookup_target)
    elapsed_normal = time.perf_counter() - start

    print(f"   普通查找: {elapsed_normal*1000:.2f}ms ({iterations}次)")

    # 测试优化索引查找
    print("\n2. 测试优化索引查找...")
    start = time.perf_counter()
    for _ in range(iterations):
        optimizer.fast_lookup(lookup_target)
    elapsed_optimized = time.perf_counter() - start

    print(f"   优化查找: {elapsed_optimized*1000:.2f}ms ({iterations}次)")

    # 计算性能提升
    if elapsed_normal > 0:
        improvement = ((elapsed_normal - elapsed_optimized) / elapsed_normal) * 100
    else:
        improvement = 0

    print(f"\n3. 性能对比:")
    print(f"   普通查找: {elapsed_normal*1000:.2f}ms")
    print(f"   优化查找: {elapsed_optimized*1000:.2f}ms")
    print(f"   性能提升: {improvement:.1f}%")

    return {
        "normal_time": elapsed_normal,
        "optimized_time": elapsed_optimized,
        "improvement_percent": improvement
    }


# 测试代码
if __name__ == "__main__":
    print("=" * 70)
    print("Day 9: 性能分析器测试")
    print("=" * 70)

    # 1. 模块解析基准测试
    result1 = benchmark_module_parsing(100)

    # 2. 符号查找基准测试
    result2 = benchmark_symbol_lookup(10, 100)

    # 总结
    print("\n" + "=" * 70)
    print("基准测试总结")
    print("=" * 70)

    total_improvement = (result1["improvement_percent"] + result2["improvement_percent"]) / 2
    print(f"\n模块解析性能提升: {result1['improvement_percent']:.1f}%")
    print(f"符号查找性能提升: {result2['improvement_percent']:.1f}%")
    print(f"平均性能提升: {total_improvement:.1f}%")

    if total_improvement >= 20:
        print("\n✅ 性能提升达到20%+目标!")
    else:
        print(f"\n⚠️ 性能提升未达到20%目标，还需要优化")

    print("=" * 70)
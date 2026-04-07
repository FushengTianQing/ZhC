#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AST遍历性能测试

测试内容：
1. AST缓存性能测试
2. 类型检查缓存性能测试
3. 控制流分析缓存性能测试
4. 符号查找优化性能测试

作者：远
日期：2026-04-03
"""

import sys
import os
import time
from typing import List, Dict

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zhpp.analyzer.ast_cache import ASTCache, CachePolicy
from zhpp.analyzer.type_checker_cached import TypeCheckerCached
from zhpp.analyzer.control_flow_cached import ControlFlowAnalyzerCached
from zhpp.analyzer.symbol_lookup_optimizer import SymbolLookupOptimizer
from zhpp.analyzer.type_checker import TypeInfo, TypeCategory


class PerformanceTestSuite:
    """性能测试套件"""
    
    def __init__(self):
        self.test_results: List[Dict] = []
    
    def measure_time(self, func, *args, **kwargs) -> tuple:
        """测量函数执行时间"""
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        return result, elapsed_time
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 70)
        print("AST遍历性能测试")
        print("=" * 70)
        print()
        
        # 测试1: AST缓存性能
        self.test_ast_cache_performance()
        
        # 测试2: 类型检查缓存性能
        self.test_type_checker_cache_performance()
        
        # 测试3: 控制流分析缓存性能
        self.test_control_flow_cache_performance()
        
        # 测试4: 符号查找优化性能
        self.test_symbol_lookup_performance()
        
        # 生成测试报告
        self.generate_report()
    
    # ==================== 测试1: AST缓存性能 ====================
    
    def test_ast_cache_performance(self):
        """测试AST缓存性能"""
        print("测试1: AST缓存性能")
        print("-" * 70)
        
        cache = ASTCache(policy=CachePolicy.AGGRESSIVE)
        
        # 生成测试AST节点
        test_nodes = self._generate_test_ast_nodes(1000)
        
        # 测试无缓存性能
        start_time = time.time()
        for _ in range(100):
            for node in test_nodes:
                _ = self._traverse_ast_node(node)
        no_cache_time = time.time() - start_time
        
        # 测试有缓存性能
        start_time = time.time()
        for i in range(100):
            for node in test_nodes:
                # 使用缓存遍历
                cache_key = f"node_{id(node)}_{i}"
                cached_result = cache.get(cache_key, 'traverse')
                if cached_result is None:
                    result = self._traverse_ast_node(node)
                    cache.put(cache_key, result, 'traverse')
        with_cache_time = time.time() - start_time
        
        # 计算加速比
        speedup = no_cache_time / with_cache_time if with_cache_time > 0 else 0
        
        # 获取缓存统计
        stats = cache.get_stats()
        
        print(f"  无缓存时间: {no_cache_time:.4f} 秒")
        print(f"  有缓存时间: {with_cache_time:.4f} 秒")
        print(f"  加速比: {speedup:.2f}x")
        print(f"  缓存命中率: {stats['hit_rate']:.2%}")
        print()
        
        self.test_results.append({
            'test_name': 'AST缓存性能',
            'no_cache_time': no_cache_time,
            'with_cache_time': with_cache_time,
            'speedup': speedup,
            'cache_hit_rate': stats['hit_rate']
        })
    
    # ==================== 测试2: 类型检查缓存性能 ====================
    
    def test_type_checker_cache_performance(self):
        """测试类型检查缓存性能"""
        print("测试2: 类型检查缓存性能")
        print("-" * 70)
        
        # 创建带缓存的类型检查器
        checker = TypeCheckerCached(cache_size=500)
        
        # 准备测试类型
        int_type = checker.get_type("整数型")
        float_type = checker.get_type("浮点型")
        
        # 测试无缓存性能（清空缓存）
        start_time = time.time()
        for _ in range(1000):
            # 重复检查相同的二元运算
            result = checker.check_binary_op(1, "+", int_type, float_type, "x + y")
        no_cache_time = time.time() - start_time
        
        # 清空缓存重新测试
        checker.clear_cache()
        
        # 测试有缓存性能
        start_time = time.time()
        for _ in range(1000):
            # 相同的表达式会命中缓存
            result = checker.check_binary_op_cached(
                1, "+", int_type, float_type, "x + y"
            )
        with_cache_time = time.time() - start_time
        
        # 计算加速比
        speedup = no_cache_time / with_cache_time if with_cache_time > 0 else 0
        
        # 获取缓存统计
        stats = checker.get_cache_stats()
        
        print(f"  无缓存时间: {no_cache_time:.4f} 秒")
        print(f"  有缓存时间: {with_cache_time:.4f} 秒")
        print(f"  加速比: {speedup:.2f}x")
        print(f"  缓存命中率: {stats['hit_rate']:.2%}")
        print(f"  类型推导缓存: {stats['type_inference_cache_size']} 条")
        print()
        
        self.test_results.append({
            'test_name': '类型检查缓存性能',
            'no_cache_time': no_cache_time,
            'with_cache_time': with_cache_time,
            'speedup': speedup,
            'cache_hit_rate': stats['hit_rate']
        })
    
    # ==================== 测试3: 控制流分析缓存性能 ====================
    
    def test_control_flow_cache_performance(self):
        """测试控制流分析缓存性能"""
        print("测试3: 控制流分析缓存性能")
        print("-" * 70)
        
        analyzer = ControlFlowAnalyzerCached(cache_size=100)
        
        # 准备测试语句
        test_statements = [
            {'type': 'var_decl', 'name': 'x', 'line': 1},
            {'type': 'var_decl', 'name': 'y', 'line': 2},
            {
                'type': 'if',
                'condition': 'x > 0',
                'then_body': [
                    {'type': 'assign', 'name': 'y', 'line': 4}
                ],
                'else_body': [
                    {'type': 'assign', 'name': 'y', 'line': 6}
                ],
                'line': 3
            },
            {'type': 'return', 'value': 'y', 'line': 8}
        ]
        
        test_source = "test_func { x; y; if (x > 0) { y; } else { y; } return y; }"
        
        # 测试无缓存性能
        start_time = time.time()
        for _ in range(100):
            cfg = analyzer.build_cfg('test_func', test_statements)
            _ = analyzer.detect_unreachable_code(cfg)
            _ = analyzer.compute_cyclomatic_complexity(cfg)
        no_cache_time = time.time() - start_time
        
        # 清空缓存
        analyzer.clear_cache()
        
        # 测试有缓存性能
        start_time = time.time()
        for _ in range(100):
            # 使用缓存版本
            cfg = analyzer.build_cfg_cached('test_func', test_statements, test_source)
            _ = analyzer.detect_unreachable_code_cached(cfg)
            _ = analyzer.compute_cyclomatic_complexity_cached(cfg)
        with_cache_time = time.time() - start_time
        
        # 计算加速比
        speedup = no_cache_time / with_cache_time if with_cache_time > 0 else 0
        
        # 获取缓存统计
        stats = analyzer.get_cache_stats()
        
        print(f"  无缓存时间: {no_cache_time:.4f} 秒")
        print(f"  有缓存时间: {with_cache_time:.4f} 秒")
        print(f"  加速比: {speedup:.2f}x")
        print(f"  缓存命中率: {stats['hit_rate']:.2%}")
        print(f"  CFG缓存: {stats['cfg_cache_size']} 个")
        print()
        
        self.test_results.append({
            'test_name': '控制流分析缓存性能',
            'no_cache_time': no_cache_time,
            'with_cache_time': with_cache_time,
            'speedup': speedup,
            'cache_hit_rate': stats['hit_rate']
        })
    
    # ==================== 测试4: 符号查找优化性能 ====================
    
    def test_symbol_lookup_performance(self):
        """测试符号查找优化性能"""
        print("测试4: 符号查找优化性能")
        print("-" * 70)
        
        optimizer = SymbolLookupOptimizer()
        
        # 添加测试符号
        test_symbols = [f"symbol_{i}" for i in range(1000)]
        for i, symbol in enumerate(test_symbols):
            optimizer.add_symbol(symbol, f"scope_{i % 10}")
        
        # 测试无优化性能
        start_time = time.time()
        for _ in range(100):
            for symbol in test_symbols:
                _ = optimizer.lookup_symbol(symbol, "scope_0", use_cache=False)
        no_opt_time = time.time() - start_time
        
        # 清空缓存
        optimizer.clear_cache()
        
        # 测试有优化性能
        start_time = time.time()
        for _ in range(100):
            for symbol in test_symbols:
                _ = optimizer.lookup_symbol_cached(symbol, "scope_0")
        with_opt_time = time.time() - start_time
        
        # 计算加速比
        speedup = no_opt_time / with_opt_time if with_opt_time > 0 else 0
        
        # 获取缓存统计
        stats = optimizer.get_stats()
        
        print(f"  无优化时间: {no_opt_time:.4f} 秒")
        print(f"  有优化时间: {with_opt_time:.4f} 秒")
        print(f"  加速比: {speedup:.2f}x")
        print(f"  缓存命中率: {stats['cache_hit_rate']:.2%}")
        print(f"  符号索引: {stats['symbol_count']} 个")
        print()
        
        self.test_results.append({
            'test_name': '符号查找优化性能',
            'no_cache_time': no_opt_time,
            'with_cache_time': with_opt_time,
            'speedup': speedup,
            'cache_hit_rate': stats['cache_hit_rate']
        })
    
    # ==================== 辅助方法 ====================
    
    def _generate_test_ast_nodes(self, count: int) -> List[Dict]:
        """生成测试AST节点"""
        nodes = []
        for i in range(count):
            node = {
                'type': 'node',
                'id': i,
                'value': f'value_{i}',
                'children': []
            }
            nodes.append(node)
        return nodes
    
    def _traverse_ast_node(self, node: Dict) -> Dict:
        """遍历AST节点"""
        # 模拟遍历操作
        result = {
            'id': node['id'],
            'type': node['type'],
            'processed': True
        }
        
        # 递归遍历子节点
        for child in node.get('children', []):
            self._traverse_ast_node(child)
        
        return result
    
    # ==================== 报告生成 ====================
    
    def generate_report(self):
        """生成测试报告"""
        print()
        print("=" * 70)
        print("性能测试总结报告")
        print("=" * 70)
        print()
        
        # 表头
        print(f"{'测试名称':<25} {'无缓存(秒)':<12} {'有缓存(秒)':<12} {'加速比':<10} {'命中率':<10}")
        print("-" * 70)
        
        # 测试结果
        for result in self.test_results:
            print(f"{result['test_name']:<25} "
                  f"{result['no_cache_time']:<12.4f} "
                  f"{result['with_cache_time']:<12.4f} "
                  f"{result['speedup']:<10.2f}x "
                  f"{result['cache_hit_rate']:<10.2%}")
        
        print()
        
        # 计算平均加速比
        avg_speedup = sum(r['speedup'] for r in self.test_results) / len(self.test_results)
        
        print(f"平均加速比: {avg_speedup:.2f}x")
        print()
        
        # 性能改进总结
        print("性能改进总结：")
        for result in self.test_results:
            improvement = (1 - result['with_cache_time'] / result['no_cache_time']) * 100
            print(f"  - {result['test_name']}: 改进 {improvement:.1f}%")
        
        print()
        print("=" * 70)


def main():
    """主函数"""
    suite = PerformanceTestSuite()
    suite.run_all_tests()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
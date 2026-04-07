#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版AST遍历性能验证测试

验证核心缓存功能

作者：远
日期：2026-04-03
"""

import sys
import os
import time

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zhpp.analyzer.type_checker_cached import TypeCheckerCached
from zhpp.analyzer.type_checker import TypeCategory


def test_type_checker_cache():
    """测试类型检查器缓存"""
    print("=" * 70)
    print("类型检查器缓存测试")
    print("=" * 70)
    
    checker = TypeCheckerCached(cache_size=100)
    
    # 获取测试类型
    int_type = checker.get_type("整数型")
    float_type = checker.get_type("浮点型")
    
    print(f"测试类型: {int_type} + {float_type}")
    print()
    
    # 测试无缓存性能
    print("测试1: 无缓存性能")
    start_time = time.time()
    for i in range(1000):
        result = checker.check_binary_op(1, "+", int_type, float_type)
    no_cache_time = time.time() - start_time
    print(f"  时间: {no_cache_time:.4f} 秒")
    print()
    
    # 清空缓存
    checker.clear_cache()
    
    # 测试有缓存性能
    print("测试2: 有缓存性能")
    start_time = time.time()
    for i in range(1000):
        result = checker.check_binary_op_cached(
            1, "+", int_type, float_type, "x + y"
        )
    with_cache_time = time.time() - start_time
    print(f"  时间: {with_cache_time:.4f} 秒")
    print()
    
    # 计算加速比
    speedup = no_cache_time / with_cache_time if with_cache_time > 0 else 0
    print(f"加速比: {speedup:.2f}x")
    print()
    
    # 获取缓存统计
    stats = checker.get_cache_stats()
    print("缓存统计:")
    print(f"  总请求数: {stats['total_requests']}")
    print(f"  缓存命中: {stats['cache_hits']}")
    print(f"  缓存未命中: {stats['cache_misses']}")
    print(f"  命中率: {stats['hit_rate']:.2%}")
    print()
    
    # 生成缓存报告
    print(checker.get_cache_report())
    
    return speedup > 1.0


def test_function_signature_cache():
    """测试函数签名缓存"""
    print("=" * 70)
    print("函数签名缓存测试")
    print("=" * 70)
    
    checker = TypeCheckerCached()
    
    # 缓存函数签名
    int_type = checker.get_type("整数型")
    float_type = checker.get_type("浮点型")
    
    checker.cache_function_signature("add", int_type, [int_type, float_type])
    
    print("已缓存函数签名: add(整数型, 浮点型) -> 整数型")
    print()
    
    # 获取缓存的签名
    sig = checker.get_function_signature("add", [int_type, float_type])
    
    if sig:
        print(f"✓ 缓存命中: {sig}")
    else:
        print("✗ 缓存未命中")
    
    print()
    
    return sig is not None


def test_unary_op_cache():
    """测试一元运算缓存"""
    print("=" * 70)
    print("一元运算缓存测试")
    print("=" * 70)
    
    checker = TypeCheckerCached()
    int_type = checker.get_type("整数型")
    
    print(f"测试类型: -{int_type}")
    print()
    
    # 测试缓存性能
    start_time = time.time()
    for i in range(1000):
        result = checker.check_unary_op_cached(1, "-", int_type, "-x")
    elapsed_time = time.time() - start_time
    
    print(f"执行时间: {elapsed_time:.4f} 秒")
    print()
    
    # 获取统计
    stats = checker.get_cache_stats()
    print(f"缓存命中率: {stats['hit_rate']:.2%}")
    print()
    
    return stats['hit_rate'] > 0.5


def main():
    """主函数"""
    print()
    print("AST遍历性能优化验证测试")
    print("=" * 70)
    print()
    
    results = []
    
    # 测试1: 类型检查器缓存
    results.append(("类型检查器缓存", test_type_checker_cache()))
    
    # 测试2: 函数签名缓存
    results.append(("函数签名缓存", test_function_signature_cache()))
    
    # 测试3: 一元运算缓存
    results.append(("一元运算缓存", test_unary_op_cache()))
    
    # 总结
    print("=" * 70)
    print("测试总结")
    print("=" * 70)
    print()
    
    for test_name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    print()
    if all_passed:
        print("✓ 所有测试通过!")
    else:
        print("✗ 部分测试失败")
    
    print("=" * 70)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
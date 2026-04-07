#!/usr/bin/env python3
"""Day 21: 内存转换器测试"""
import sys
import os

from zhc.converter.memory import MemorySyntaxConverter

def run_tests():
    print("=" * 50)
    print("Day 21 内存转换器测试")
    print("=" * 50)

    c = MemorySyntaxConverter()
    passed = 0

    # 测试1: 新建整数型
    try:
        result = c.convert_line("新建 整数型 ptr;", 1)
        assert result is not None and "malloc" in result
        print('✓ test_001: 新建整数型')
        passed += 1
    except Exception as e:
        print(f'✗ test_001: {e}')

    # 测试2: 数组新建
    try:
        result = c.convert_line("新建 整数型 arr[100];", 2)
        assert result is not None and "100" in result
        print('✓ test_002: 数组新建')
        passed += 1
    except Exception as e:
        print(f'✗ test_002: {e}')

    # 测试3: 删除
    try:
        result = c.convert_line("删除 ptr;", 3)
        assert result is not None and "free" in result
        print('✓ test_003: 删除')
        passed += 1
    except Exception as e:
        print(f'✗ test_003: {e}')

    # 测试4: 数组删除
    try:
        result = c.convert_line("删除数组 arr;", 4)
        assert result is not None and "free" in result
        print('✓ test_004: 数组删除')
        passed += 1
    except Exception as e:
        print(f'✗ test_004: {e}')

    # 测试5: 多行统计
    try:
        c2 = MemorySyntaxConverter()
        c2.convert_line("新建 整数型 a;", 1)
        c2.convert_line("新建 整数型 b[10];", 2)
        c2.convert_line("删除 a;", 3)
        stats = c2.get_statistics()
        assert stats['total'] == 3
        print('✓ test_005: 多行统计')
        passed += 1
    except Exception as e:
        print(f'✗ test_005: {e}')

    print("=" * 50)
    print(f"通过: {passed}/5")
    if passed == 5:
        print("🎉 全部通过!")
    print("=" * 50)
    return passed == 5

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
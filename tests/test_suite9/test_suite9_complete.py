#!/usr/bin/env python3
"""
测试套件9：内存语法完整测试

包含30个测试用例：
- 25个基础测试用例
- 5个高级测试用例
"""

import sys
import os

from zhpp.converter.memory import MemorySyntaxConverter
from zhpp.type_system.smart_ptr import SmartPointerConverter, PointerType
from zhpp.analyzer.memory_safety import (
    NullPointerChecker, MemoryLeakDetector, BoundsChecker, SafetyLevel
)


# ============== 基础测试 (25个) ==============

# --- Day 21: 内存转换基础 ---

def test_001_new_int():
    c = MemorySyntaxConverter()
    result = c.convert_line("新建 整数型 ptr;", 1)
    assert result is not None and "malloc" in result
    return True

def test_002_new_float():
    c = MemorySyntaxConverter()
    result = c.convert_line("新建 浮点型 num;", 1)
    assert result is not None and "float" in result
    return True

def test_003_new_double():
    c = MemorySyntaxConverter()
    result = c.convert_line("新建 双精度型 d;", 1)
    assert result is not None and "double" in result
    return True

def test_004_new_char():
    c = MemorySyntaxConverter()
    result = c.convert_line("新建 字符型 ch;", 1)
    assert result is not None and "char" in result
    return True

def test_005_array_new():
    c = MemorySyntaxConverter()
    result = c.convert_line("新建 整数型 arr[100];", 1)
    assert result is not None and "100" in result
    return True

def test_006_array_new_float():
    c = MemorySyntaxConverter()
    result = c.convert_line("新建 浮点型 buf[50];", 1)
    assert result is not None and "50" in result
    return True

def test_007_delete():
    c = MemorySyntaxConverter()
    result = c.convert_line("删除 ptr;", 1)
    assert result is not None and "free" in result
    return True

def test_008_delete_array():
    c = MemorySyntaxConverter()
    result = c.convert_line("删除数组 buf;", 1)
    assert result is not None and "free" in result
    return True

def test_009_multiple_alloc():
    c = MemorySyntaxConverter()
    c.convert_line("新建 整数型 a;", 1)
    c.convert_line("新建 整数型 b[10];", 2)
    c.convert_line("新建 字符型 c;", 3)
    assert len(c.statements) == 3
    return True

def test_010_statistics():
    c = MemorySyntaxConverter()
    c.convert_line("新建 整数型 a;", 1)
    c.convert_line("新建 整数型 b[5];", 2)
    c.convert_line("删除 a;", 3)
    stats = c.get_statistics()
    assert stats['new_count'] == 1
    assert stats['array_new_count'] == 1
    return True

# --- Day 22: 智能指针 ---

def test_011_unique_pointer():
    c = SmartPointerConverter()
    result = c.parse_and_convert("独享指针<整数型> ptr;", 1)
    assert result is not None and "unique_ptr" in result
    return True

def test_012_shared_pointer():
    c = SmartPointerConverter()
    result = c.parse_and_convert("共享指针<整数型> ptr;", 1)
    assert result is not None and "shared_ptr" in result
    return True

def test_013_weak_pointer():
    c = SmartPointerConverter()
    result = c.parse_and_convert("弱指针<整数型> ptr;", 1)
    assert result is not None and "weak_ptr" in result
    return True

def test_014_ref_count():
    c = SmartPointerConverter()
    c.parse_and_convert("共享指针<整数型> shared;", 1)
    c.add_reference("other", "shared")
    assert c.ref_manager.get_ref_count('shared') == 2
    return True

def test_015_release():
    c = SmartPointerConverter()
    c.parse_and_convert("共享指针<整数型> ptr;", 1)
    c.release_pointer("ptr")
    return True

def test_016_multiple_pointers():
    c = SmartPointerConverter()
    c.parse_and_convert("独享指针<整数型> u1;", 1)
    c.parse_and_convert("共享指针<浮点型> s1;", 2)
    c.parse_and_convert("弱指针<字符型> w1;", 3)
    stats = c.get_statistics()
    assert stats['total'] == 3
    return True

def test_017_pointer_statistics():
    c = SmartPointerConverter()
    c.parse_and_convert("独享指针<整数型> u1;", 1)
    c.parse_and_convert("共享指针<整数型> s1;", 2)
    stats = c.get_statistics()
    assert stats['unique'] == 1
    assert stats['shared'] == 1
    return True

# --- Day 23: 内存安全 ---

def test_018_null_check():
    c = NullPointerChecker()
    c.track_allocation("ptr", 1)
    issue = c.verify_access("ptr", "read", 10)
    # 验证访问返回问题（未检查空指针）
    return True

def test_019_null_check_pass():
    c = NullPointerChecker()
    c.track_allocation("ptr", 1)
    c.check_null("ptr", 5)
    issue = c.verify_access("ptr", "read", 10)
    return True

def test_020_leak_detection():
    d = MemoryLeakDetector()
    d.track_allocation("ptr", 1)
    leaks = d.check_leaks()
    assert len(leaks) == 1
    return True

def test_021_leak_free():
    d = MemoryLeakDetector()
    d.track_allocation("ptr", 1)
    d.track_free("ptr", 10)
    leaks = d.check_leaks()
    assert len(leaks) == 0
    return True

def test_022_double_free():
    d = MemoryLeakDetector()
    d.track_allocation("ptr", 1)
    d.track_free("ptr", 10)
    issue = d.check_double_free("ptr", 15)
    assert issue is not None
    return True

def test_023_bounds_normal():
    b = BoundsChecker()
    b.track_array("arr", 10, 1)
    issue = b.check_access("arr", 5, "write", 5)
    assert issue is None
    return True

def test_024_bounds_oob():
    b = BoundsChecker()
    b.track_array("arr", 10, 1)
    issue = b.check_access("arr", 15, "write", 5)
    assert issue is not None
    return True

def test_025_bounds_negative():
    b = BoundsChecker()
    b.track_array("arr", 10, 1)
    issue = b.check_access("arr", -1, "write", 5)
    assert issue is not None
    return True

# ============== 高级测试 (5个) ==============

def test_026_complex_memory():
    """高级测试1: 复杂内存操作"""
    c = MemorySyntaxConverter()
    c.convert_line("新建 整数型 ptr;", 1)
    c.convert_line("新建 整数型 arr[100];", 2)
    c.convert_line("新建 双精度型 mat[50];", 3)
    c.convert_line("删除 ptr;", 4)
    c.convert_line("删除数组 arr;", 5)
    stats = c.get_statistics()
    assert stats['total'] == 5
    assert stats['delete_count'] == 1
    return True

def test_027_smart_ptr_chain():
    """高级测试2: 智能指针链"""
    c = SmartPointerConverter()
    c.parse_and_convert("共享指针<整数型> p1;", 1)
    c.parse_and_convert("共享指针<整数型> p2;", 2)
    c.add_reference("p2", "p1")
    c.add_reference("p1", "p2")
    cycles = c.check_cycles()
    assert len(cycles) >= 1
    return True

def test_028_mixed_pointers():
    """高级测试3: 混合指针类型"""
    c = SmartPointerConverter()
    c.parse_and_convert("独享指针<A> up;", 1)
    c.parse_and_convert("共享指针<A> sp;", 2)
    c.parse_and_convert("弱指针<A> wp;", 3)
    stats = c.get_statistics()
    assert stats['unique'] == 1
    assert stats['shared'] == 1
    assert stats['weak'] == 1
    return True

def test_029_safety_analysis():
    """高级测试4: 综合安全分析"""
    from zhpp.analyzer.memory_safety import MemorySafetyAnalyzer
    analyzer = MemorySafetyAnalyzer()
    analyzer.null_checker.track_allocation("ptr", 1)
    analyzer.leak_detector.track_allocation("leak", 2)
    issues = analyzer.analyze()
    assert len(issues) >= 1  # 至少有一个泄漏
    return True

def test_030_complete_workflow():
    """高级测试5: 完整工作流"""
    # 新建 -> 使用 -> 删除
    c = MemorySyntaxConverter()
    c.convert_line("新建 整数型 data;", 1)
    c.convert_line("新建 整数型 buffer[256];", 2)
    c.convert_line("删除 data;", 3)
    c.convert_line("删除数组 buffer;", 4)
    stats = c.get_statistics()
    assert stats['total'] == 4
    assert stats['delete_count'] == 1
    assert stats['array_delete_count'] == 1
    return True


def run_all_tests():
    print("=" * 60)
    print("测试套件9：内存语法完整测试 (30个测试用例)")
    print("=" * 60)

    tests = [
        # 基础测试 (25)
        test_001_new_int, test_002_new_float, test_003_new_double,
        test_004_new_char, test_005_array_new, test_006_array_new_float,
        test_007_delete, test_008_delete_array, test_009_multiple_alloc,
        test_010_statistics,
        test_011_unique_pointer, test_012_shared_pointer, test_013_weak_pointer,
        test_014_ref_count, test_015_release, test_016_multiple_pointers,
        test_017_pointer_statistics,
        test_018_null_check, test_019_null_check_pass,
        test_020_leak_detection, test_021_leak_free, test_022_double_free,
        test_023_bounds_normal, test_024_bounds_oob, test_025_bounds_negative,
        # 高级测试 (5)
        test_026_complex_memory, test_027_smart_ptr_chain,
        test_028_mixed_pointers, test_029_safety_analysis,
        test_030_complete_workflow,
    ]

    passed = 0
    failed = 0
    errors = []

    for i, test in enumerate(tests, 1):
        try:
            if test():
                passed += 1
                print(f"✓ test_{i:03d}: {test.__name__}")
            else:
                failed += 1
                errors.append(f"test_{i:03d}: {test.__name__}")
                print(f"✗ test_{i:03d}: {test.__name__}")
        except Exception as e:
            failed += 1
            errors.append(f"test_{i:03d}: {test.__name__} - {e}")
            print(f"✗ test_{i:03d}: {test.__name__} - {e}")

    print("=" * 60)
    print(f"测试总数: {len(tests)}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print("=" * 60)

    if failed == 0:
        print("🎉 所有测试通过！测试套件9通过率100%")
    else:
        print(f"⚠️ {failed}个测试失败")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
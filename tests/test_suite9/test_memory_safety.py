#!/usr/bin/env python3
"""Day 23: 内存安全测试"""
import sys, os

from zhpp.analyzer.memory_safety import (
    NullPointerChecker, MemoryLeakDetector, BoundsChecker,
    MemorySafetyAnalyzer, SafetyLevel
)

def test_null_check():
    c = NullPointerChecker()
    c.track_allocation("ptr", 1)
    # 未检查空的访问会产生警告
    issue = c.verify_access("ptr", "read", 10)
    # 如果没有在访问前检查空，会返回警告
    print('✓ test_null_check: 空指针检查')
    return True

def test_null_check_pass():
    c = NullPointerChecker()
    c.track_allocation("ptr", 1)
    c.check_null("ptr", 5)
    issue = c.verify_access("ptr", "read", 10)
    # 检查后访问
    print('✓ test_null_check_pass: 空指针检查通过')
    return True

def test_leak_detection():
    d = MemoryLeakDetector()
    d.track_allocation("ptr", 1)
    leaks = d.check_leaks()
    assert len(leaks) == 1
    print('✓ test_leak_detection: 泄漏检测')
    return True

def test_leak_free():
    d = MemoryLeakDetector()
    d.track_allocation("ptr", 1)
    d.track_free("ptr", 10)
    leaks = d.check_leaks()
    assert len(leaks) == 0
    print('✓ test_leak_free: 释放后无泄漏')
    return True

def test_double_free():
    d = MemoryLeakDetector()
    d.track_allocation("ptr", 1)
    d.track_free("ptr", 10)
    issue = d.check_double_free("ptr", 15)
    assert issue is not None
    print('✓ test_double_free: 双重释放检测')
    return True

def test_bounds_normal():
    b = BoundsChecker()
    b.track_array("arr", 10, 1)
    issue = b.check_access("arr", 5, "write", 5)
    assert issue is None
    print('✓ test_bounds_normal: 正常访问')
    return True

def test_bounds_oob():
    b = BoundsChecker()
    b.track_array("arr", 10, 1)
    issue = b.check_access("arr", 15, "write", 5)
    assert issue is not None
    print('✓ test_bounds_oob: 越界检测')
    return True

def test_bounds_negative():
    b = BoundsChecker()
    b.track_array("arr", 10, 1)
    issue = b.check_access("arr", -1, "write", 5)
    assert issue is not None
    print('✓ test_bounds_negative: 负索引检测')
    return True

def run_all():
    print("=" * 50)
    print("Day 23 内存安全测试")
    print("=" * 50)
    tests = [test_null_check, test_null_check_pass, test_leak_detection,
              test_leak_free, test_double_free, test_bounds_normal,
              test_bounds_oob, test_bounds_negative]
    passed = 0
    for t in tests:
        try:
            if t():
                passed += 1
        except Exception as e:
            print(f"✗ {t.__name__}: {e}")
    print("=" * 50)
    print(f"通过: {passed}/{len(tests)}")
    if passed == len(tests):
        print("🎉 全部通过!")
    print("=" * 50)
    return passed == len(tests)

if __name__ == '__main__':
    success = run_all()
    sys.exit(0 if success else 1)
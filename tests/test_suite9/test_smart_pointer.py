#!/usr/bin/env python3
"""Day 22: 智能指针测试"""
import sys, os

from zhpp.type_system.smart_ptr import SmartPointerConverter, PointerType

def test_unique():
    c = SmartPointerConverter()
    result = c.parse_and_convert("独享指针<整数型> ptr;", 1)
    assert result is not None and "unique_ptr" in result
    print('✓ test_unique: 独享指针')
    return True

def test_shared():
    c = SmartPointerConverter()
    result = c.parse_and_convert("共享指针<整数型> ptr;", 1)
    assert result is not None and "shared_ptr" in result
    print('✓ test_shared: 共享指针')
    return True

def test_weak():
    c = SmartPointerConverter()
    result = c.parse_and_convert("弱指针<整数型> ptr;", 1)
    assert result is not None and "weak_ptr" in result
    print('✓ test_weak: 弱指针')
    return True

def test_ref_count():
    c = SmartPointerConverter()
    c.parse_and_convert("共享指针<整数型> shared;", 1)
    c.add_reference("other", "shared")
    assert c.ref_manager.get_ref_count('shared') == 2
    print('✓ test_ref_count: 引用计数')
    return True

def test_release():
    c = SmartPointerConverter()
    c.parse_and_convert("共享指针<整数型> shared;", 1)
    msg = c.release_pointer("shared")
    assert msg is not None
    print('✓ test_release: 释放')
    return True

def test_cycle_detection():
    c = SmartPointerConverter()
    c.parse_and_convert("共享指针<整数型> p1;", 1)
    c.parse_and_convert("共享指针<整数型> p2;", 2)
    c.add_reference("p2", "p1")
    c.add_reference("p1", "p2")
    cycles = c.check_cycles()
    assert len(cycles) >= 1
    print('✓ test_cycle_detection: 循环引用检测')
    return True

def test_statistics():
    c = SmartPointerConverter()
    c.parse_and_convert("独享指针<整数型> u1;", 1)
    c.parse_and_convert("共享指针<整数型> s1;", 2)
    c.parse_and_convert("弱指针<整数型> w1;", 3)
    stats = c.get_statistics()
    assert stats['unique'] == 1
    assert stats['shared'] == 1
    assert stats['weak'] == 1
    print('✓ test_statistics: 统计')
    return True

def run_all():
    print("=" * 50)
    print("Day 22 智能指针测试")
    print("=" * 50)
    tests = [test_unique, test_shared, test_weak, test_ref_count, test_release, test_cycle_detection, test_statistics]
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
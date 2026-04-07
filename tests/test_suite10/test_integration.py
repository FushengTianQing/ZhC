#!/usr/bin/env python3
"""Day 26: 系统集成测试"""
import sys
import os
import time

# 设置路径

from zhc.parser.module import ModuleParser
from zhc.parser.class_ import ClassParser
from zhc.converter.memory import MemorySyntaxConverter
from zhc.type_system.smart_ptr import SmartPointerConverter
from zhc.analyzer.memory_safety import NullPointerChecker, MemoryLeakDetector


def run_tests():
    passed = 0
    failed = 0

    print("=" * 60)
    print("Day 26: 系统集成测试")
    print("=" * 60)

    # 模块测试
    print("\n--- 模块系统 ---")
    try:
        parser = ModuleParser()
        parser.parse_module_declaration("模块 测试 {", 1)
        assert len(parser.modules) == 1
        print("✓ test_module_basic")
        passed += 1
    except Exception as e:
        print(f"✗ test_module_basic: {e}")
        failed += 1

    # 类测试
    print("\n--- 类系统 ---")
    try:
        parser = ClassParser()
        parser.parse_class_declaration("类 学生 {", 1)
        assert len(parser.classes) == 1
        print("✓ test_class_basic")
        passed += 1
    except Exception as e:
        print(f"✗ test_class_basic: {e}")
        failed += 1

    # 内存测试
    print("\n--- 内存系统 ---")
    try:
        converter = MemorySyntaxConverter()
        result = converter.convert_line("新建 整数型 ptr;", 1)
        assert result is not None and "malloc" in result
        print("✓ test_memory_new")
        passed += 1
    except Exception as e:
        print(f"✗ test_memory_new: {e}")
        failed += 1

    try:
        converter = MemorySyntaxConverter()
        result = converter.convert_line("删除 ptr;", 1)
        assert result is not None and "free" in result
        print("✓ test_memory_delete")
        passed += 1
    except Exception as e:
        print(f"✗ test_memory_delete: {e}")
        failed += 1

    try:
        converter = MemorySyntaxConverter()
        result = converter.convert_line("新建 整数型 arr[100];", 1)
        assert result is not None and "100" in result
        print("✓ test_memory_array")
        passed += 1
    except Exception as e:
        print(f"✗ test_memory_array: {e}")
        failed += 1

    # 智能指针测试
    print("\n--- 智能指针 ---")
    try:
        converter = SmartPointerConverter()
        result = converter.parse_and_convert("独享指针<整数型> ptr;", 1)
        assert result is not None and "unique_ptr" in result
        print("✓ test_smart_pointer_unique")
        passed += 1
    except Exception as e:
        print(f"✗ test_smart_pointer_unique: {e}")
        failed += 1

    try:
        converter = SmartPointerConverter()
        result = converter.parse_and_convert("共享指针<整数型> ptr;", 1)
        assert result is not None and "shared_ptr" in result
        print("✓ test_smart_pointer_shared")
        passed += 1
    except Exception as e:
        print(f"✗ test_smart_pointer_shared: {e}")
        failed += 1

    # 内存安全测试
    print("\n--- 内存安全 ---")
    try:
        checker = NullPointerChecker()
        checker.track_allocation("ptr", 1)
        assert len(checker.allocations) == 1
        print("✓ test_null_check")
        passed += 1
    except Exception as e:
        print(f"✗ test_null_check: {e}")
        failed += 1

    try:
        detector = MemoryLeakDetector()
        detector.track_allocation("ptr", 1)
        leaks = detector.check_leaks()
        assert len(leaks) == 1
        print("✓ test_leak_detection")
        passed += 1
    except Exception as e:
        print(f"✗ test_leak_detection: {e}")
        failed += 1

    # 组合测试
    print("\n--- 组合测试 ---")
    try:
        module_parser = ModuleParser()
        module_parser.parse_module_declaration("模块 主模块 {", 1)

        class_parser = ClassParser()
        class_parser.parse_class_declaration("类 容器 {", 1)

        mem_converter = MemorySyntaxConverter()
        mem_result = mem_converter.convert_line("新建 整数型 数据[100];", 1)

        sp_converter = SmartPointerConverter()
        sp_result = sp_converter.parse_and_convert("独享指针<整数型> ptr;", 1)

        assert (len(module_parser.modules) == 1 and
                len(class_parser.classes) == 1 and
                mem_result is not None and
                sp_result is not None)
        print("✓ test_full_integration")
        passed += 1
    except Exception as e:
        print(f"✗ test_full_integration: {e}")
        failed += 1

    # 性能测试
    print("\n--- 性能测试 ---")
    try:
        start = time.time()
        for _ in range(100):
            parser = ModuleParser()
            parser.parse_module_declaration("模块 测试 {", 1)
        elapsed = time.time() - start
        assert elapsed < 1.0
        print(f"✓ test_performance_module ({elapsed:.3f}s)")
        passed += 1
    except Exception as e:
        print(f"✗ test_performance_module: {e}")
        failed += 1

    # 打印结果
    total = passed + failed
    rate = (passed / total * 100) if total > 0 else 0
    print("\n" + "=" * 60)
    print(f"测试总数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"通过率: {rate:.1f}%")
    print("=" * 60)

    if failed == 0:
        print("🎉 所有集成测试通过!")
    else:
        print(f"⚠️  {failed}个测试失败")

    return rate >= 95


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
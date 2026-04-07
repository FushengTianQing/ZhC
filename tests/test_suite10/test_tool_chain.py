#!/usr/bin/env python3
"""Day 27: 工具链优化测试"""
import sys
import os

from zhpp.cli.toolchain import (
    ErrorCode, ErrorLevel, CompilerError,
    EnhancedErrorHandler, PerformanceOptimizer, DebugInfoGenerator
)


def test_error_codes():
    assert ErrorCode.LEX_UNEXPECTED_CHAR.value == 1001
    assert ErrorCode.SYNTAX_UNEXPECTED_TOKEN.value == 2001
    print('✓ test_error_codes')
    return True


def test_error_handler():
    handler = EnhancedErrorHandler()
    handler.add_error(ErrorCode.LEX_UNCLOSED_STRING, 10, 5)
    assert len(handler.errors) == 1
    print('✓ test_error_handler')
    return True


def test_error_format():
    handler = EnhancedErrorHandler()
    handler.add_error(ErrorCode.SYNTAX_UNEXPECTED_TOKEN, 10, 5)
    formatted = handler.format_error(handler.errors[0])
    assert '行 10' in formatted
    assert '建议' in formatted
    print('✓ test_error_format')
    return True


def test_error_summary():
    handler = EnhancedErrorHandler()
    handler.add_error(ErrorCode.LEX_UNCLOSED_STRING, 10)
    handler.add_error(ErrorCode.MEMORY_LEAK, 20)
    summary = handler.format_summary()
    assert '错误' in summary
    assert '编译错误摘要' in summary
    print('✓ test_error_summary')
    return True


def test_performance_measure():
    optimizer = PerformanceOptimizer()
    def dummy():
        return 42
    optimizer.measure('lexical_time', dummy)
    assert optimizer.stats['lexical_time'] > 0
    print('✓ test_performance_measure')
    return True


def test_debug_info():
    debugger = DebugInfoGenerator()
    debugger.add_symbol('ptr', 'int*', 10)
    debugger.add_symbol('count', 'int', 15)
    assert debugger.get_symbol_info('ptr') == {'type': 'int*', 'line': 10}
    assert debugger.get_symbol_info('unknown') is None
    debug_code = debugger.generate_debug_info()
    assert '调试信息' in debug_code
    print('✓ test_debug_info')
    return True


def test_debug_symbol_table():
    debugger = DebugInfoGenerator()
    debugger.add_symbol('x', 'int', 1)
    debugger.add_symbol('y', 'float', 2)
    assert len(debugger.symbol_table) == 2
    print('✓ test_debug_symbol_table')
    return True


def run_all():
    print("=" * 50)
    print("Day 27 工具链测试")
    print("=" * 50)

    tests = [
        test_error_codes,
        test_error_handler,
        test_error_format,
        test_error_summary,
        test_performance_measure,
        test_debug_info,
        test_debug_symbol_table,
    ]

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
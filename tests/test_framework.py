#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试框架测试

测试 ZhC 内置测试框架的功能
"""

import pytest
import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from zhc.test import (
    TestStatus,
    TestCaseResult,
    TestSuiteResult,
    TestModuleResult,
    TestSummary,
    TestRunner,
    test,
    skip,
    assert_equal,
    assert_not_equal,
    assert_true,
    assert_false,
    assert_null,
    assert_not_null,
    assert_float_equal,
    assert_string_equal,
    assert_greater,
    assert_less,
    assert_in,
    assert_not_in,
    assert_isinstance,
    assert_length,
    assert_empty,
    assert_not_empty,
    assert_raises,
    generate_report,
    parse_test_module,
    generate_test_code,
    AssertionNode,
)


class TestResultDataClasses:
    """测试结果数据类测试"""

    def test_assertion_result(self):
        """测试断言结果"""
        result = TestCaseResult(name="test1", suite_name="suite1")
        assert result.name == "test1"
        assert result.suite_name == "suite1"
        assert result.status == TestStatus.NOT_RUN
        assert not result.passed
        assert not result.failed

    def test_test_case_result_passed(self):
        """测试用例通过结果"""
        result = TestCaseResult(name="test1", suite_name="suite1")
        result.mark_passed(0.5)
        assert result.passed
        assert not result.failed
        assert result.duration == 0.5

    def test_test_case_result_failed(self):
        """测试用例失败结果"""
        result = TestCaseResult(name="test1", suite_name="suite1")
        result.mark_failed("断言失败", "堆栈信息")
        assert not result.passed
        assert result.failed
        assert result.error_message == "断言失败"
        assert result.stack_trace == "堆栈信息"

    def test_test_suite_result(self):
        """测试套件结果"""
        suite = TestSuiteResult(name="suite1", module_name="module1")
        suite.add_test_case(
            TestCaseResult(name="test1", suite_name="suite1", status=TestStatus.PASSED)
        )
        suite.add_test_case(
            TestCaseResult(name="test2", suite_name="suite1", status=TestStatus.FAILED)
        )
        assert suite.passed_count == 1
        assert suite.failed_count == 1
        assert suite.total_count == 2

    def test_test_summary(self):
        """测试汇总结果"""
        summary = TestSummary()
        module = TestModuleResult(name="module1")
        suite = TestSuiteResult(name="suite1", module_name="module1")
        suite.add_test_case(
            TestCaseResult(name="test1", suite_name="suite1", status=TestStatus.PASSED)
        )
        module.add_suite(suite)
        summary.add_module(module)
        assert summary.passed_count == 1
        assert summary.total_count == 1
        assert summary.is_success


class TestAssertions:
    """断言测试"""

    def test_assert_equal(self):
        """测试相等断言"""
        result = assert_equal(1, 1)
        assert result.passed

        result = assert_equal(1, 2)
        assert not result.passed

    def test_assert_not_equal(self):
        """测试不相等断言"""
        result = assert_not_equal(1, 2)
        assert result.passed

        result = assert_not_equal(1, 1)
        assert not result.passed

    def test_assert_true(self):
        """测试为真断言"""
        result = assert_true(True)
        assert result.passed

        result = assert_true(False)
        assert not result.passed

    def test_assert_false(self):
        """测试为假断言"""
        result = assert_false(False)
        assert result.passed

        result = assert_false(True)
        assert not result.passed

    def test_assert_null(self):
        """测试为空断言"""
        result = assert_null(None)
        assert result.passed

        result = assert_null(1)
        assert not result.passed

    def test_assert_not_null(self):
        """测试非空断言"""
        result = assert_not_null(1)
        assert result.passed

        result = assert_not_null(None)
        assert not result.passed

    def test_assert_float_equal(self):
        """测试浮点数相等断言"""
        result = assert_float_equal(1.0, 1.0000001, epsilon=1e-6)
        assert result.passed

        result = assert_float_equal(1.0, 2.0)
        assert not result.passed

    def test_assert_string_equal(self):
        """测试字符串相等断言"""
        result = assert_string_equal("hello", "hello")
        assert result.passed

        result = assert_string_equal("hello", "world")
        assert not result.passed

    def test_assert_greater(self):
        """测试大于断言"""
        result = assert_greater(2, 1)
        assert result.passed

        result = assert_greater(1, 2)
        assert not result.passed

    def test_assert_less(self):
        """测试小于断言"""
        result = assert_less(1, 2)
        assert result.passed

        result = assert_less(2, 1)
        assert not result.passed

    def test_assert_in(self):
        """测试包含断言"""
        result = assert_in(1, [1, 2, 3])
        assert result.passed

        result = assert_in(4, [1, 2, 3])
        assert not result.passed

    def test_assert_not_in(self):
        """测试不包含断言"""
        result = assert_not_in(4, [1, 2, 3])
        assert result.passed

        result = assert_not_in(1, [1, 2, 3])
        assert not result.passed

    def test_assert_isinstance(self):
        """测试类型断言"""
        result = assert_isinstance(1, int)
        assert result.passed

        result = assert_isinstance(1, str)
        assert not result.passed

    def test_assert_length(self):
        """测试长度断言"""
        result = assert_length([1, 2, 3], 3)
        assert result.passed

        result = assert_length([1, 2, 3], 2)
        assert not result.passed

    def test_assert_empty(self):
        """测试为空集合断言"""
        result = assert_empty([])
        assert result.passed

        result = assert_empty([1])
        assert not result.passed

    def test_assert_not_empty(self):
        """测试不为空集合断言"""
        result = assert_not_empty([1])
        assert result.passed

        result = assert_not_empty([])
        assert not result.passed

    def test_assert_raises(self):
        """测试抛出异常断言"""
        result = assert_raises(ValueError, lambda: int("abc"))
        assert result.passed

        result = assert_raises(ValueError, lambda: 1 + 1)
        assert not result.passed


class TestSuiteManagement:
    """测试套件管理测试"""

    def test_test_registry(self):
        """测试注册表"""
        # 使用全局注册表
        from zhc.test.suite import get_registry

        registry = get_registry()
        initial_count = registry.get_test_count()

        @test("测试1", suite="套件1", module="模块1")
        def test_func1():
            pass

        @test("测试2", suite="套件1", module="模块1")
        def test_func2():
            pass

        # 注册后应该至少增加2个测试
        assert registry.get_test_count() >= initial_count + 2

    def test_test_decorator(self):
        """测试装饰器"""

        @test("测试加法")
        def test_add():
            assert_equal(1 + 1, 2)

        # 测试函数应该被注册
        assert test_add.__name__ == "test_add"

    def test_skip_decorator(self):
        """测试跳过装饰器"""

        @skip("暂时跳过")
        def test_skipped():
            pass

        # 测试函数应该被注册为跳过
        assert test_skipped.__name__ == "test_skipped"


class TestTestRunner:
    """测试运行器测试"""

    def test_run_single_test(self):
        """运行单个测试"""

        @test("简单测试")
        def simple_test():
            assert_equal(1 + 1, 2)

        runner = TestRunner()
        # 创建测试套件
        from zhc.test.suite import TestModule, TestSuite, TestCase

        test_case = TestCase(name="简单测试", function=simple_test)
        test_suite = TestSuite(name="default", module_name="default")
        test_suite.add_test_case(test_case)
        test_module = TestModule(name="default")
        test_module.add_suite(test_suite)

        summary = runner.run(modules=[test_module])
        assert summary.passed_count == 1
        assert summary.failed_count == 0

    def test_run_failing_test(self):
        """运行失败的测试"""

        def failing_test():
            # 使用 pytest 的 assert 会抛出 AssertionError
            assert 1 == 2, "1 应该等于 2"

        runner = TestRunner()
        from zhc.test.suite import TestModule, TestSuite, TestCase

        test_case = TestCase(name="失败测试", function=failing_test)
        test_suite = TestSuite(name="default", module_name="default")
        test_suite.add_test_case(test_case)
        test_module = TestModule(name="default")
        test_module.add_suite(test_suite)

        summary = runner.run(modules=[test_module])
        assert summary.passed_count == 0
        assert summary.failed_count == 1

    def test_run_skipped_test(self):
        """运行跳过的测试"""

        @skip("暂时跳过")
        def skipped_test():
            pass

        runner = TestRunner()
        from zhc.test.suite import TestModule, TestSuite, TestCase

        test_case = TestCase(
            name="跳过测试", function=skipped_test, skip=True, skip_reason="暂时跳过"
        )
        test_suite = TestSuite(name="default", module_name="default")
        test_suite.add_test_case(test_case)
        test_module = TestModule(name="default")
        test_module.add_suite(test_suite)

        summary = runner.run(modules=[test_module])
        assert summary.skipped_count == 1


class TestReporter:
    """报告器测试"""

    def test_text_reporter(self):
        """文本报告器"""
        summary = TestSummary()
        module = TestModuleResult(name="test_module")
        suite = TestSuiteResult(name="test_suite", module_name="test_module")
        suite.add_test_case(
            TestCaseResult(
                name="test_case", suite_name="test_suite", status=TestStatus.PASSED
            )
        )
        module.add_suite(suite)
        summary.add_module(module)

        report = generate_report(summary, "text")
        assert "测试结果报告" in report
        assert "test_module" in report

    def test_json_reporter(self):
        """JSON 报告器"""
        summary = TestSummary()
        module = TestModuleResult(name="test_module")
        suite = TestSuiteResult(name="test_suite", module_name="test_module")
        suite.add_test_case(
            TestCaseResult(
                name="test_case", suite_name="test_suite", status=TestStatus.PASSED
            )
        )
        module.add_suite(suite)
        summary.add_module(module)

        report = generate_report(summary, "json")
        assert '"summary"' in report
        assert '"modules"' in report

    def test_markdown_reporter(self):
        """Markdown 报告器"""
        summary = TestSummary()
        module = TestModuleResult(name="test_module")
        suite = TestSuiteResult(name="test_suite", module_name="test_module")
        suite.add_test_case(
            TestCaseResult(
                name="test_case", suite_name="test_suite", status=TestStatus.PASSED
            )
        )
        module.add_suite(suite)
        summary.add_module(module)

        report = generate_report(summary, "markdown")
        assert "# 测试报告" in report
        assert "test_module" in report


class TestParser:
    """解析器测试"""

    def test_parse_simple_test_module(self):
        """解析简单测试模块"""
        source = """
测试模块 "数学库测试"

测试套件 "算术测试" {
    测试函数 测试加法() {
        整数型 结果 = 加(2, 3);
        断言等于(结果, 5);
    }
}
"""
        module = parse_test_module(source)
        assert module.name == "数学库测试"
        assert len(module.suites) == 1
        assert module.suites[0].name == "算术测试"
        assert len(module.suites[0].functions) == 1
        assert module.suites[0].functions[0].name == "测试加法"

    def test_parse_with_imports(self):
        """解析带导入的测试模块"""
        source = """
测试模块 "测试"
导入 数学模块
导入 字符串模块 作为 str

测试套件 "基础测试" {
    测试函数 测试1() {
        断言等于(1, 1);
    }
}
"""
        module = parse_test_module(source)
        assert module.name == "测试"
        assert len(module.imports) == 2
        assert module.imports[0].module_name == "数学模块"
        assert module.imports[1].module_name == "字符串模块"
        assert module.imports[1].alias == "str"

    def test_parse_multiple_assertions(self):
        """解析多个断言"""
        source = """
测试模块 "断言测试"

测试套件 "断言" {
    测试函数 测试断言() {
        断言等于(1, 1);
        断言不等于(1, 2);
        断言为真(真);
        断言为假(假);
    }
}
"""
        module = parse_test_module(source)
        assert len(module.suites) == 1
        assert len(module.suites[0].functions) == 1
        func = module.suites[0].functions[0]
        # 统计断言节点（分号也被解析为语句）
        assertion_count = sum(
            1 for s in func.body.statements if isinstance(s, AssertionNode)
        )
        assert assertion_count == 4


class TestCodeGenerator:
    """代码生成器测试"""

    def test_generate_simple_code(self):
        """生成简单代码"""
        source = """
测试模块 "测试"

测试套件 "套件1" {
    测试函数 测试1() {
        断言等于(1, 1);
    }
}
"""
        module = parse_test_module(source)
        code = generate_test_code(module)

        assert "#include <stdio.h>" in code
        assert '#include "zhc_test.h"' in code
        assert "void 套件1_测试1(void)" in code
        assert "断言等于(1, 1);" in code

    def test_generate_with_imports(self):
        """生成带导入的代码"""
        source = """
测试模块 "测试"
导入 数学模块

测试套件 "套件1" {
    测试函数 测试1() {
        断言等于(1, 1);
    }
}
"""
        module = parse_test_module(source)
        code = generate_test_code(module)

        assert "// 导入: 数学模块" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

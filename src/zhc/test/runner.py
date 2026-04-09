#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行器

执行测试用例并收集结果
"""

import time
import traceback
from typing import Callable, List, Optional
from datetime import datetime

from .result import (
    TestSummary,
    TestModuleResult,
    TestSuiteResult,
    TestCaseResult,
    TestStatus,
)
from .suite import TestCase, TestSuite, TestModule, TestRegistry
from .reporter import generate_report


class TestRunner:
    """测试运行器"""

    def __init__(self):
        self.summary: Optional[TestSummary] = None
        self._current_module: Optional[str] = None
        self._current_suite: Optional[str] = None
        self._current_test: Optional[str] = None

    def run(
        self,
        modules: Optional[List[TestModule]] = None,
        registry: Optional[TestRegistry] = None,
        filter_pattern: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> TestSummary:
        """
        运行测试

        Args:
            modules: 测试模块列表（可选）
            registry: 测试注册表（可选）
            filter_pattern: 测试名称过滤模式
            tags: 按标签过滤

        Returns:
            测试汇总结果
        """
        # 获取测试模块
        if registry:
            modules = registry.get_all_modules()
        elif not modules:
            modules = []

        # 创建汇总结果
        self.summary = TestSummary()
        self.summary.start_time = datetime.now()

        # 运行每个模块
        for module in modules:
            self._run_module(module, filter_pattern, tags)

        self.summary.end_time = datetime.now()

        # 计算总执行时间
        if self.summary.start_time and self.summary.end_time:
            delta = self.summary.end_time - self.summary.start_time
            self.summary.duration = delta.total_seconds()

        return self.summary

    def _run_module(
        self,
        module: TestModule,
        filter_pattern: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """运行测试模块"""
        self._current_module = module.name
        module_result = TestModuleResult(name=module.name)
        module_result.start_time = datetime.now()

        # 运行每个套件
        for suite in module.get_suites():
            # 检查过滤条件
            if filter_pattern and not self._match_pattern(suite.name, filter_pattern):
                continue

            suite_result = self._run_suite(suite, tags)
            if suite_result:
                module_result.add_suite(suite_result)

        module_result.end_time = datetime.now()
        if module_result.start_time:
            delta = module_result.end_time - module_result.start_time
            module_result.duration = delta.total_seconds()

        if module_result.suites:
            self.summary.add_module(module_result)

    def _run_suite(
        self,
        suite: TestSuite,
        tags: Optional[List[str]] = None,
    ) -> Optional[TestSuiteResult]:
        """运行测试套件"""
        self._current_suite = suite.name
        suite_result = TestSuiteResult(name=suite.name, module_name=suite.module_name)
        suite_result.start_time = datetime.now()

        # 运行套件级别的 setup
        if suite.setup:
            try:
                suite.setup()
            except Exception as e:
                # setup 失败会导致所有测试被跳过
                for test_case in suite.get_test_cases():
                    result = TestCaseResult(
                        name=test_case.name,
                        suite_name=suite.name,
                        status=TestStatus.ERROR,
                    )
                    result.mark_error(f"套件 setup 失败: {e}", traceback.format_exc())
                    suite_result.add_test_case(result)
                return suite_result

        # 运行每个测试用例
        for test_case in suite.get_test_cases():
            # 检查标签过滤
            if tags and not any(tag in test_case.tags for tag in tags):
                continue

            # 检查跳过
            if test_case.skip:
                result = TestCaseResult(
                    name=test_case.name,
                    suite_name=suite.name,
                    status=TestStatus.SKIPPED,
                )
                result.mark_skipped(test_case.skip_reason)
                suite_result.add_test_case(result)
                continue

            # 运行测试用例
            result = self._run_test_case(test_case, suite)
            suite_result.add_test_case(result)

        # 运行套件级别的 teardown
        if suite.teardown:
            try:
                suite.teardown()
            except Exception:
                # teardown 失败不影响测试结果
                pass

        suite_result.end_time = datetime.now()
        if suite_result.start_time:
            delta = suite_result.end_time - suite_result.start_time
            suite_result.duration = delta.total_seconds()

        return suite_result

    def _run_test_case(
        self,
        test_case: TestCase,
        suite: TestSuite,
    ) -> TestCaseResult:
        """运行单个测试用例"""
        self._current_test = test_case.name
        result = TestCaseResult(name=test_case.name, suite_name=suite.name)
        start_time = time.time()

        # 运行测试级别的 setup_each
        if suite.setup_each:
            try:
                suite.setup_each()
            except Exception as e:
                result.mark_error(f"setup_each 失败: {e}", traceback.format_exc())
                return result

        try:
            # 执行测试函数
            test_case.function()

            # 标记为通过
            end_time = time.time()
            result.mark_passed(end_time - start_time)

        except AssertionError as e:
            # 断言失败
            end_time = time.time()
            result.mark_failed(str(e), traceback.format_exc())
            result.duration = end_time - start_time

        except Exception as e:
            # 其他错误
            end_time = time.time()
            result.mark_error(str(e), traceback.format_exc())
            result.duration = end_time - start_time

        # 运行测试级别的 teardown_each
        if suite.teardown_each:
            try:
                suite.teardown_each()
            except Exception:
                # teardown_each 失败不影响测试结果
                pass

        return result

    def _match_pattern(self, name: str, pattern: str) -> bool:
        """检查名称是否匹配模式"""
        import fnmatch

        return fnmatch.fnmatch(name, pattern)


def run_tests(
    modules: Optional[List[TestModule]] = None,
    registry: Optional[TestRegistry] = None,
    filter_pattern: Optional[str] = None,
    tags: Optional[List[str]] = None,
    report_format: str = "text",
) -> TestSummary:
    """
    运行测试并生成报告

    Args:
        modules: 测试模块列表
        registry: 测试注册表
        filter_pattern: 测试名称过滤模式
        tags: 按标签过滤
        report_format: 报告格式 (text, json, html, markdown)

    Returns:
        测试汇总结果
    """
    runner = TestRunner()
    summary = runner.run(modules, registry, filter_pattern, tags)

    # 打印报告
    report = generate_report(summary, report_format)
    print(report)

    return summary


def run_test_suite(suite: TestSuite, report_format: str = "text") -> TestSummary:
    """
    运行单个测试套件

    Args:
        suite: 测试套件
        report_format: 报告格式

    Returns:
        测试汇总结果
    """
    runner = TestRunner()
    summary = runner.run(modules=[TestModule(name=suite.module_name, suites=[suite])])

    # 打印报告
    report = generate_report(summary, report_format)
    print(report)

    return summary


def run_test_function(test_func: Callable[[], None], name: str = "") -> TestCaseResult:
    """
    运行单个测试函数

    Args:
        test_func: 测试函数
        name: 测试名称

    Returns:
        测试用例结果
    """
    runner = TestRunner()
    test_case = TestCase(name=name or test_func.__name__, function=test_func)

    summary = runner.run(
        modules=[
            TestModule(
                name="single",
                suites=[
                    TestSuite(name="single", test_cases={test_case.name: test_case})
                ],
            )
        ]
    )

    if summary.modules and summary.modules[0].suites:
        return summary.modules[0].suites[0].test_cases[0]

    return TestCaseResult(name=name, suite_name="single")

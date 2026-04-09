#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试结果数据类

定义测试执行结果的数据结构
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from datetime import datetime


class TestStatus(Enum):
    """测试状态枚举"""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    NOT_RUN = "not_run"


class AssertionStatus(Enum):
    """断言状态枚举"""

    PASSED = "passed"
    FAILED = "failed"


@dataclass
class AssertionResult:
    """断言结果"""

    name: str  # 断言名称 (如 "断言等于")
    passed: bool
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None

    def __repr__(self) -> str:
        status = "✅" if self.passed else "❌"
        return f"{status} {self.name}: {self.message}"


@dataclass
class TestCaseResult:
    """单个测试用例结果"""

    name: str
    suite_name: str
    status: TestStatus = TestStatus.NOT_RUN
    duration: float = 0.0  # 执行时间（秒）
    assertions: List[AssertionResult] = field(default_factory=list)
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    stdout: str = ""
    stderr: str = ""

    @property
    def passed(self) -> bool:
        """测试是否通过"""
        return self.status == TestStatus.PASSED

    @property
    def failed(self) -> bool:
        """测试是否失败"""
        return self.status == TestStatus.FAILED

    @property
    def error(self) -> bool:
        """测试是否有错误"""
        return self.status == TestStatus.ERROR

    @property
    def skipped(self) -> bool:
        """测试是否跳过"""
        return self.status == TestStatus.SKIPPED

    @property
    def passed_assertions(self) -> int:
        """通过的断言数"""
        return sum(1 for a in self.assertions if a.passed)

    @property
    def failed_assertions(self) -> int:
        """失败的断言数"""
        return sum(1 for a in self.assertions if not a.passed)

    def add_assertion(self, assertion: AssertionResult) -> None:
        """添加断言结果"""
        self.assertions.append(assertion)

    def mark_passed(self, duration: float = 0.0) -> None:
        """标记为通过"""
        self.status = TestStatus.PASSED
        self.duration = duration

    def mark_failed(
        self, error_message: str, stack_trace: Optional[str] = None
    ) -> None:
        """标记为失败"""
        self.status = TestStatus.FAILED
        self.error_message = error_message
        self.stack_trace = stack_trace

    def mark_error(self, error_message: str, stack_trace: Optional[str] = None) -> None:
        """标记为错误"""
        self.status = TestStatus.ERROR
        self.error_message = error_message
        self.stack_trace = stack_trace

    def mark_skipped(self, reason: str = "") -> None:
        """标记为跳过"""
        self.status = TestStatus.SKIPPED
        self.error_message = reason

    def __repr__(self) -> str:
        status_icon = {
            TestStatus.PASSED: "✅",
            TestStatus.FAILED: "❌",
            TestStatus.ERROR: "💥",
            TestStatus.SKIPPED: "⏭️",
            TestStatus.NOT_RUN: "⏳",
        }.get(self.status, "❓")
        return f"{status_icon} {self.suite_name}::{self.name}"


@dataclass
class TestSuiteResult:
    """测试套件结果"""

    name: str
    module_name: str
    test_cases: List[TestCaseResult] = field(default_factory=list)
    duration: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def passed_count(self) -> int:
        """通过的测试数"""
        return sum(1 for tc in self.test_cases if tc.passed)

    @property
    def failed_count(self) -> int:
        """失败的测试数"""
        return sum(1 for tc in self.test_cases if tc.failed)

    @property
    def error_count(self) -> int:
        """出错的测试数"""
        return sum(1 for tc in self.test_cases if tc.error)

    @property
    def skipped_count(self) -> int:
        """跳过的测试数"""
        return sum(1 for tc in self.test_cases if tc.skipped)

    @property
    def total_count(self) -> int:
        """总测试数"""
        return len(self.test_cases)

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_count == 0:
            return 0.0
        return self.passed_count / self.total_count * 100

    def add_test_case(self, test_case: TestCaseResult) -> None:
        """添加测试用例"""
        self.test_cases.append(test_case)

    def add_duration(self, duration: float) -> None:
        """累加执行时间"""
        self.duration += duration

    def __repr__(self) -> str:
        return f"TestSuite({self.name}): {self.passed_count}/{self.total_count} passed"


@dataclass
class TestModuleResult:
    """测试模块结果"""

    name: str
    suites: List[TestSuiteResult] = field(default_factory=list)
    duration: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def passed_count(self) -> int:
        """通过的测试数"""
        return sum(s.passed_count for s in self.suites)

    @property
    def failed_count(self) -> int:
        """失败的测试数"""
        return sum(s.failed_count for s in self.suites)

    @property
    def error_count(self) -> int:
        """出错的测试数"""
        return sum(s.error_count for s in self.suites)

    @property
    def skipped_count(self) -> int:
        """跳过的测试数"""
        return sum(s.skipped_count for s in self.suites)

    @property
    def total_count(self) -> int:
        """总测试数"""
        return sum(s.total_count for s in self.suites)

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_count == 0:
            return 0.0
        return self.passed_count / self.total_count * 100

    @property
    def is_success(self) -> bool:
        """是否全部通过"""
        return self.failed_count == 0 and self.error_count == 0

    def add_suite(self, suite: TestSuiteResult) -> None:
        """添加测试套件"""
        self.suites.append(suite)

    def __repr__(self) -> str:
        status = "✅" if self.is_success else "❌"
        return f"{status} {self.name}: {self.passed_count}/{self.total_count} passed"


@dataclass
class TestSummary:
    """测试汇总结果"""

    modules: List[TestModuleResult] = field(default_factory=list)
    duration: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def passed_count(self) -> int:
        """通过的测试数"""
        return sum(m.passed_count for m in self.modules)

    @property
    def failed_count(self) -> int:
        """失败的测试数"""
        return sum(m.failed_count for m in self.modules)

    @property
    def error_count(self) -> int:
        """出错的测试数"""
        return sum(m.error_count for m in self.modules)

    @property
    def skipped_count(self) -> int:
        """跳过的测试数"""
        return sum(m.skipped_count for m in self.modules)

    @property
    def total_count(self) -> int:
        """总测试数"""
        return sum(m.total_count for m in self.modules)

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_count == 0:
            return 0.0
        return self.passed_count / self.total_count * 100

    @property
    def is_success(self) -> bool:
        """是否全部通过"""
        return self.failed_count == 0 and self.error_count == 0

    def add_module(self, module: TestModuleResult) -> None:
        """添加模块结果"""
        self.modules.append(module)

    def get_failed_tests(self) -> List[TestCaseResult]:
        """获取所有失败的测试"""
        failed = []
        for module in self.modules:
            for suite in module.suites:
                for test_case in suite.test_cases:
                    if test_case.failed or test_case.error:
                        failed.append(test_case)
        return failed

    def __repr__(self) -> str:
        status = "✅" if self.is_success else "❌"
        return f"{status} 汇总: {self.passed_count}/{self.total_count} passed ({self.success_rate:.1f}%)"

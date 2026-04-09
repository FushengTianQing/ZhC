#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试套件管理

管理测试用例的组织和分组
"""

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Dict
from enum import Enum


class TestPriority(Enum):
    """测试优先级"""

    HIGHEST = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    LOWEST = 4


@dataclass
class TestCase:
    """测试用例定义"""

    name: str
    function: Callable[[], None]
    suite_name: str = "default"
    description: str = ""
    priority: TestPriority = TestPriority.NORMAL
    tags: List[str] = field(default_factory=list)
    skip: bool = False
    skip_reason: str = ""
    timeout: Optional[float] = None  # 超时时间（秒）
    setup: Optional[Callable[[], None]] = None
    teardown: Optional[Callable[[], None]] = None

    def __repr__(self) -> str:
        return f"TestCase({self.suite_name}::{self.name})"


@dataclass
class TestSuite:
    """测试套件定义"""

    name: str
    module_name: str
    description: str = ""
    test_cases: Dict[str, TestCase] = field(default_factory=dict)
    setup: Optional[Callable[[], None]] = None  # 套件级别的 setup
    teardown: Optional[Callable[[], None]] = None  # 套件级别的 teardown
    setup_each: Optional[Callable[[], None]] = None  # 每个测试前的 setup
    teardown_each: Optional[Callable[[], None]] = None  # 每个测试后的 teardown

    def add_test_case(self, test_case: TestCase) -> None:
        """添加测试用例"""
        test_case.suite_name = self.name
        self.test_cases[test_case.name] = test_case

    def get_test_case(self, name: str) -> Optional[TestCase]:
        """获取测试用例"""
        return self.test_cases.get(name)

    def get_test_cases(self) -> List[TestCase]:
        """获取所有测试用例"""
        return list(self.test_cases.values())

    def get_test_count(self) -> int:
        """获取测试用例数量"""
        return len(self.test_cases)

    def get_test_names(self) -> List[str]:
        """获取所有测试名称"""
        return list(self.test_cases.keys())

    def filter_by_tag(self, tag: str) -> List[TestCase]:
        """按标签过滤测试用例"""
        return [tc for tc in self.test_cases.values() if tag in tc.tags]

    def filter_by_priority(self, priority: TestPriority) -> List[TestCase]:
        """按优先级过滤测试用例"""
        return [tc for tc in self.test_cases.values() if tc.priority == priority]

    def get_skipped_tests(self) -> List[TestCase]:
        """获取跳过的测试"""
        return [tc for tc in self.test_cases.values() if tc.skip]

    def __repr__(self) -> str:
        return f"TestSuite({self.name}: {len(self.test_cases)} tests)"


@dataclass
class TestModule:
    """测试模块定义"""

    name: str
    suites: Dict[str, TestSuite] = field(default_factory=dict)

    def add_suite(self, suite: TestSuite) -> None:
        """添加测试套件"""
        suite.module_name = self.name
        self.suites[suite.name] = suite

    def get_suite(self, name: str) -> Optional[TestSuite]:
        """获取测试套件"""
        return self.suites.get(name)

    def get_suites(self) -> List[TestSuite]:
        """获取所有测试套件"""
        return list(self.suites.values())

    def get_all_test_cases(self) -> List[TestCase]:
        """获取所有测试用例"""
        cases = []
        for suite in self.suites.values():
            cases.extend(suite.get_test_cases())
        return cases

    def get_test_count(self) -> int:
        """获取总测试数"""
        return sum(suite.get_test_count() for suite in self.suites.values())

    def __repr__(self) -> str:
        return f"TestModule({self.name}: {len(self.suites)} suites, {self.get_test_count()} tests)"


class TestRegistry:
    """测试注册表 - 全局管理所有测试"""

    _instance: Optional["TestRegistry"] = None

    def __init__(self):
        self.modules: Dict[str, TestModule] = {}
        self.current_module: Optional[str] = None
        self.current_suite: Optional[str] = None

    @classmethod
    def get_instance(cls) -> "TestRegistry":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """重置注册表"""
        cls._instance = None

    def create_module(self, name: str) -> TestModule:
        """创建测试模块"""
        module = TestModule(name=name)
        self.modules[name] = module
        self.current_module = name
        return module

    def get_module(self, name: str) -> Optional[TestModule]:
        """获取测试模块"""
        return self.modules.get(name)

    def create_suite(self, module_name: str, suite_name: str) -> TestSuite:
        """创建测试套件"""
        module = self.get_module(module_name)
        if module is None:
            module = self.create_module(module_name)

        suite = TestSuite(name=suite_name, module_name=module_name)
        module.add_suite(suite)
        self.current_suite = suite_name
        return suite

    def register_test(
        self,
        name: str,
        function: Callable[[], None],
        suite_name: str = "default",
        module_name: str = "default",
        description: str = "",
        tags: Optional[List[str]] = None,
        priority: TestPriority = TestPriority.NORMAL,
        skip: bool = False,
        skip_reason: str = "",
    ) -> TestCase:
        """注册测试用例"""
        # 确保模块存在
        module = self.get_module(module_name)
        if module is None:
            module = self.create_module(module_name)

        # 确保套件存在
        suite = module.get_suite(suite_name)
        if suite is None:
            suite = TestSuite(name=suite_name, module_name=module_name)
            module.add_suite(suite)

        # 创建测试用例
        test_case = TestCase(
            name=name,
            function=function,
            suite_name=suite_name,
            description=description,
            tags=tags or [],
            priority=priority,
            skip=skip,
            skip_reason=skip_reason,
        )

        suite.add_test_case(test_case)
        return test_case

    def get_all_modules(self) -> List[TestModule]:
        """获取所有测试模块"""
        return list(self.modules.values())

    def get_all_suites(self) -> List[TestSuite]:
        """获取所有测试套件"""
        suites = []
        for module in self.modules.values():
            suites.extend(module.get_suites())
        return suites

    def get_all_test_cases(self) -> List[TestCase]:
        """获取所有测试用例"""
        cases = []
        for module in self.modules.values():
            cases.extend(module.get_all_test_cases())
        return cases

    def get_test_count(self) -> int:
        """获取总测试数"""
        return sum(module.get_test_count() for module in self.modules.values())

    def clear(self) -> None:
        """清空所有测试"""
        self.modules.clear()
        self.current_module = None
        self.current_suite = None


# 全局注册表实例
_registry = TestRegistry.get_instance()


def get_registry() -> TestRegistry:
    """获取全局测试注册表"""
    return _registry


def test(
    name: Optional[str] = None,
    suite: str = "default",
    module: str = "default",
    description: str = "",
    tags: Optional[List[str]] = None,
    priority: TestPriority = TestPriority.NORMAL,
    skip: bool = False,
    skip_reason: str = "",
):
    """
    测试装饰器

    用法:
        @test("测试加法")
        def test_add():
            assert_equal(1 + 1, 2)
    """

    def decorator(func: Callable[[], None]) -> Callable[[], None]:
        test_name = name or func.__name__
        _registry.register_test(
            name=test_name,
            function=func,
            suite_name=suite,
            module_name=module,
            description=description,
            tags=tags,
            priority=priority,
            skip=skip,
            skip_reason=skip_reason,
        )
        return func

    return decorator


def suite(name: str, module: str = "default") -> TestSuite:
    """创建测试套件"""
    return _registry.create_suite(module, name)


def skip(reason: str = ""):
    """跳过测试装饰器"""

    def decorator(func: Callable[[], None]) -> Callable[[], None]:
        test_name = func.__name__
        _registry.register_test(
            name=test_name,
            function=func,
            skip=True,
            skip_reason=reason,
        )
        return func

    return decorator

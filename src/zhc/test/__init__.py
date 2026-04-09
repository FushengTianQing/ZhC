#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZhC 内置测试框架

提供测试用例编写和执行功能
"""

from .result import (
    TestStatus,
    AssertionStatus,
    AssertionResult,
    TestCaseResult,
    TestSuiteResult,
    TestModuleResult,
    TestSummary,
)

from .suite import (
    TestCase,
    TestSuite,
    TestModule,
    TestRegistry,
    TestPriority,
    test,
    suite,
    skip,
    get_registry,
)

from .assertions import (
    Assertion,
    AssertionError,
    assert_equal,
    assert_not_equal,
    assert_true,
    assert_false,
    assert_null,
    assert_not_null,
    assert_float_equal,
    assert_string_equal,
    assert_greater,
    assert_greater_equal,
    assert_less,
    assert_less_equal,
    assert_in,
    assert_not_in,
    assert_isinstance,
    assert_hasattr,
    assert_length,
    assert_empty,
    assert_not_empty,
    assert_raises,
)

from .runner import (
    TestRunner,
    run_tests,
    run_test_suite,
    run_test_function,
)

from .reporter import (
    Reporter,
    TextReporter,
    JsonReporter,
    JUnitReporter,
    HtmlReporter,
    MarkdownReporter,
    generate_report,
    save_report,
)

from .parser import (
    NodeType,
    ASTNode,
    ImportNode,
    AssertionNode,
    StatementNode,
    BlockNode,
    TestFunctionNode,
    TestSuiteNode,
    TestModuleNode,
    Lexer,
    Parser,
    parse_test_module,
    parse_test_file,
)

from .codegen import (
    TestCodeGenerator,
    generate_test_code,
    generate_test_file,
)

__all__ = [
    # 结果
    "TestStatus",
    "AssertionStatus",
    "AssertionResult",
    "TestCaseResult",
    "TestSuiteResult",
    "TestModuleResult",
    "TestSummary",
    # 套件
    "TestCase",
    "TestSuite",
    "TestModule",
    "TestRegistry",
    "TestPriority",
    "test",
    "suite",
    "skip",
    "get_registry",
    # 断言
    "Assertion",
    "AssertionError",
    "assert_equal",
    "assert_not_equal",
    "assert_true",
    "assert_false",
    "assert_null",
    "assert_not_null",
    "assert_float_equal",
    "assert_string_equal",
    "assert_greater",
    "assert_greater_equal",
    "assert_less",
    "assert_less_equal",
    "assert_in",
    "assert_not_in",
    "assert_isinstance",
    "assert_hasattr",
    "assert_length",
    "assert_empty",
    "assert_not_empty",
    "assert_raises",
    # 运行器
    "TestRunner",
    "run_tests",
    "run_test_suite",
    "run_test_function",
    # 报告
    "Reporter",
    "TextReporter",
    "JsonReporter",
    "JUnitReporter",
    "HtmlReporter",
    "MarkdownReporter",
    "generate_report",
    "save_report",
    # 解析器
    "NodeType",
    "ASTNode",
    "ImportNode",
    "AssertionNode",
    "StatementNode",
    "BlockNode",
    "TestFunctionNode",
    "TestSuiteNode",
    "TestModuleNode",
    "Lexer",
    "Parser",
    "parse_test_module",
    "parse_test_file",
    # 代码生成
    "TestCodeGenerator",
    "generate_test_code",
    "generate_test_file",
]

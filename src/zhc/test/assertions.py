#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
断言库

提供丰富的断言函数用于测试
"""

from typing import Any, Optional
from .result import AssertionResult


class AssertionError(AssertionError):
    """断言失败异常"""

    pass


class Assertion:
    """断言工具类"""

    @staticmethod
    def assert_equal(
        actual: Any,
        expected: Any,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言相等"""
        passed = actual == expected
        if not message:
            message = f"期望 {expected}，实际 {actual}"
        return AssertionResult(
            name="断言等于",
            passed=passed,
            message=message if not passed else f"断言通过: {actual} == {expected}",
            expected=str(expected),
            actual=str(actual),
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_not_equal(
        actual: Any,
        expected: Any,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言不相等"""
        passed = actual != expected
        if not message:
            message = f"期望不等于 {expected}，实际 {actual}"
        return AssertionResult(
            name="断言不等于",
            passed=passed,
            message=message if not passed else f"断言通过: {actual} != {expected}",
            expected=str(expected),
            actual=str(actual),
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_true(
        condition: bool,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言为真"""
        passed = bool(condition)
        if not message:
            message = "期望条件为真"
        return AssertionResult(
            name="断言为真",
            passed=passed,
            message=message if not passed else "断言通过: 条件为真",
            expected="True",
            actual=str(condition),
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_false(
        condition: bool,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言为假"""
        passed = not bool(condition)
        if not message:
            message = "期望条件为假"
        return AssertionResult(
            name="断言为假",
            passed=passed,
            message=message if not passed else "断言通过: 条件为假",
            expected="False",
            actual=str(condition),
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_null(
        value: Any,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言为空"""
        passed = value is None
        if not message:
            message = "期望值为 None"
        return AssertionResult(
            name="断言为空",
            passed=passed,
            message=message if not passed else "断言通过: 值为 None",
            expected="None",
            actual=str(value),
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_not_null(
        value: Any,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言非空"""
        passed = value is not None
        if not message:
            message = "期望值不为 None"
        return AssertionResult(
            name="断言非空",
            passed=passed,
            message=message if not passed else "断言通过: 值不为 None",
            expected="not None",
            actual=str(value),
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_float_equal(
        actual: float,
        expected: float,
        epsilon: float = 1e-9,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言浮点数相等"""
        passed = abs(actual - expected) < epsilon
        if not message:
            message = f"期望 {expected} ± {epsilon}，实际 {actual}"
        return AssertionResult(
            name="断言浮点等于",
            passed=passed,
            message=message if not passed else f"断言通过: {actual} ≈ {expected}",
            expected=f"{expected} ± {epsilon}",
            actual=str(actual),
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_string_equal(
        actual: str,
        expected: str,
        case_sensitive: bool = True,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言字符串相等"""
        if case_sensitive:
            passed = actual == expected
        else:
            passed = actual.lower() == expected.lower()

        if not message:
            message = f"期望字符串 '{expected}'，实际 '{actual}'"
        return AssertionResult(
            name="断言字符串等于",
            passed=passed,
            message=message if not passed else f"断言通过: '{actual}' == '{expected}'",
            expected=expected,
            actual=actual,
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_greater(
        actual: Any,
        expected: Any,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言大于"""
        passed = actual > expected
        if not message:
            message = f"期望 {actual} > {expected}"
        return AssertionResult(
            name="断言大于",
            passed=passed,
            message=message if not passed else f"断言通过: {actual} > {expected}",
            expected=f"> {expected}",
            actual=str(actual),
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_greater_equal(
        actual: Any,
        expected: Any,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言大于等于"""
        passed = actual >= expected
        if not message:
            message = f"期望 {actual} >= {expected}"
        return AssertionResult(
            name="断言大于等于",
            passed=passed,
            message=message if not passed else f"断言通过: {actual} >= {expected}",
            expected=f">= {expected}",
            actual=str(actual),
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_less(
        actual: Any,
        expected: Any,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言小于"""
        passed = actual < expected
        if not message:
            message = f"期望 {actual} < {expected}"
        return AssertionResult(
            name="断言小于",
            passed=passed,
            message=message if not passed else f"断言通过: {actual} < {expected}",
            expected=f"< {expected}",
            actual=str(actual),
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_less_equal(
        actual: Any,
        expected: Any,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言小于等于"""
        passed = actual <= expected
        if not message:
            message = f"期望 {actual} <= {expected}"
        return AssertionResult(
            name="断言小于等于",
            passed=passed,
            message=message if not passed else f"断言通过: {actual} <= {expected}",
            expected=f"<= {expected}",
            actual=str(actual),
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_in(
        item: Any,
        container: Any,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言包含"""
        passed = item in container
        if not message:
            message = f"期望 {item} 在 {container} 中"
        return AssertionResult(
            name="断言包含",
            passed=passed,
            message=message if not passed else f"断言通过: {item} in {container}",
            expected=f"in {container}",
            actual=str(item),
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_not_in(
        item: Any,
        container: Any,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言不包含"""
        passed = item not in container
        if not message:
            message = f"期望 {item} 不在 {container} 中"
        return AssertionResult(
            name="断言不包含",
            passed=passed,
            message=message if not passed else f"断言通过: {item} not in {container}",
            expected=f"not in {container}",
            actual=str(item),
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_isinstance(
        obj: Any,
        expected_type: type,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言类型"""
        passed = isinstance(obj, expected_type)
        if not message:
            message = f"期望类型 {expected_type.__name__}，实际 {type(obj).__name__}"
        return AssertionResult(
            name="断言类型",
            passed=passed,
            message=message
            if not passed
            else f"断言通过: {obj} 是 {expected_type.__name__}",
            expected=expected_type.__name__,
            actual=type(obj).__name__,
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_hasattr(
        obj: Any,
        attr: str,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言有属性"""
        passed = hasattr(obj, attr)
        if not message:
            message = f"期望对象有属性 '{attr}'"
        return AssertionResult(
            name="断言有属性",
            passed=passed,
            message=message if not passed else f"断言通过: 对象有属性 '{attr}'",
            expected=f"hasattr({attr})",
            actual=str(obj),
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_length(
        obj: Any,
        expected_length: int,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言长度"""
        actual_length = len(obj)
        passed = actual_length == expected_length
        if not message:
            message = f"期望长度 {expected_length}，实际 {actual_length}"
        return AssertionResult(
            name="断言长度",
            passed=passed,
            message=message if not passed else f"断言通过: 长度为 {expected_length}",
            expected=str(expected_length),
            actual=str(actual_length),
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_empty(
        obj: Any,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言为空（长度为0）"""
        passed = len(obj) == 0
        if not message:
            message = "期望对象为空"
        return AssertionResult(
            name="断言为空",
            passed=passed,
            message=message if not passed else "断言通过: 对象为空",
            expected="empty",
            actual=f"length={len(obj)}",
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_not_empty(
        obj: Any,
        message: str = "",
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> AssertionResult:
        """断言不为空（长度大于0）"""
        passed = len(obj) > 0
        if not message:
            message = "期望对象不为空"
        return AssertionResult(
            name="断言不为空",
            passed=passed,
            message=message if not passed else "断言通过: 对象不为空",
            expected="not empty",
            actual=f"length={len(obj)}",
            file_path=file_path,
            line_number=line_number,
        )

    @staticmethod
    def assert_raises(
        exception_type: type,
        func: callable,
        *args: Any,
        **kwargs: Any,
    ) -> AssertionResult:
        """断言抛出异常"""
        try:
            func(*args, **kwargs)
            return AssertionResult(
                name="断言抛出异常",
                passed=False,
                message=f"期望抛出 {exception_type.__name__}，但没有抛出异常",
                expected=exception_type.__name__,
                actual="No exception",
            )
        except exception_type as e:
            return AssertionResult(
                name="断言抛出异常",
                passed=True,
                message=f"断言通过: 抛出了 {exception_type.__name__}",
                expected=exception_type.__name__,
                actual=f"{exception_type.__name__}: {e}",
            )
        except Exception as e:
            return AssertionResult(
                name="断言抛出异常",
                passed=False,
                message=f"期望抛出 {exception_type.__name__}，实际抛出 {type(e).__name__}",
                expected=exception_type.__name__,
                actual=f"{type(e).__name__}: {e}",
            )


# 便捷函数
def assert_equal(actual: Any, expected: Any, message: str = "") -> AssertionResult:
    """断言相等"""
    return Assertion.assert_equal(actual, expected, message)


def assert_not_equal(actual: Any, expected: Any, message: str = "") -> AssertionResult:
    """断言不相等"""
    return Assertion.assert_not_equal(actual, expected, message)


def assert_true(condition: bool, message: str = "") -> AssertionResult:
    """断言为真"""
    return Assertion.assert_true(condition, message)


def assert_false(condition: bool, message: str = "") -> AssertionResult:
    """断言为假"""
    return Assertion.assert_false(condition, message)


def assert_null(value: Any, message: str = "") -> AssertionResult:
    """断言为空"""
    return Assertion.assert_null(value, message)


def assert_not_null(value: Any, message: str = "") -> AssertionResult:
    """断言非空"""
    return Assertion.assert_not_null(value, message)


def assert_float_equal(
    actual: float, expected: float, epsilon: float = 1e-9, message: str = ""
) -> AssertionResult:
    """断言浮点数相等"""
    return Assertion.assert_float_equal(actual, expected, epsilon, message)


def assert_string_equal(
    actual: str, expected: str, case_sensitive: bool = True, message: str = ""
) -> AssertionResult:
    """断言字符串相等"""
    return Assertion.assert_string_equal(actual, expected, case_sensitive, message)


def assert_greater(actual: Any, expected: Any, message: str = "") -> AssertionResult:
    """断言大于"""
    return Assertion.assert_greater(actual, expected, message)


def assert_greater_equal(
    actual: Any, expected: Any, message: str = ""
) -> AssertionResult:
    """断言大于等于"""
    return Assertion.assert_greater_equal(actual, expected, message)


def assert_less(actual: Any, expected: Any, message: str = "") -> AssertionResult:
    """断言小于"""
    return Assertion.assert_less(actual, expected, message)


def assert_less_equal(actual: Any, expected: Any, message: str = "") -> AssertionResult:
    """断言小于等于"""
    return Assertion.assert_less_equal(actual, expected, message)


def assert_in(item: Any, container: Any, message: str = "") -> AssertionResult:
    """断言包含"""
    return Assertion.assert_in(item, container, message)


def assert_not_in(item: Any, container: Any, message: str = "") -> AssertionResult:
    """断言不包含"""
    return Assertion.assert_not_in(item, container, message)


def assert_isinstance(
    obj: Any, expected_type: type, message: str = ""
) -> AssertionResult:
    """断言类型"""
    return Assertion.assert_isinstance(obj, expected_type, message)


def assert_hasattr(obj: Any, attr: str, message: str = "") -> AssertionResult:
    """断言有属性"""
    return Assertion.assert_hasattr(obj, attr, message)


def assert_length(obj: Any, expected_length: int, message: str = "") -> AssertionResult:
    """断言长度"""
    return Assertion.assert_length(obj, expected_length, message)


def assert_empty(obj: Any, message: str = "") -> AssertionResult:
    """断言为空"""
    return Assertion.assert_empty(obj, message)


def assert_not_empty(obj: Any, message: str = "") -> AssertionResult:
    """断言不为空"""
    return Assertion.assert_not_empty(obj, message)


def assert_raises(
    exception_type: type, func: callable, *args: Any, **kwargs: Any
) -> AssertionResult:
    """断言抛出异常"""
    return Assertion.assert_raises(exception_type, func, *args, **kwargs)

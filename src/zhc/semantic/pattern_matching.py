#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模式匹配系统 - Pattern Matching System

实现模式匹配的核心功能：
1. 模式定义和匹配
2. 解构绑定
3. 守卫表达式
4. 穷尽性检查

Phase 4 - Stage 2 - Task 11.2

作者：ZHC 开发团队
日期：2026-04-08
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, Set, Tuple
from abc import ABC, abstractmethod
from enum import Enum, auto


# ===== 模式类型枚举 =====


class PatternType(Enum):
    """模式类型"""

    WILDCARD = auto()  # 通配符 _
    VARIABLE = auto()  # 变量模式 x
    LITERAL = auto()  # 字面量模式 42, "hello"
    CONSTRUCTOR = auto()  # 构造器模式 Some(x)
    DESTRUCTURE = auto()  # 解构模式 点{x, y}
    RANGE = auto()  # 范围模式 1..10
    TUPLE = auto()  # 元组模式 (x, y)
    OR = auto()  # 或模式 x | y
    AND = auto()  # 与模式 x & y
    GUARD = auto()  # 守卫模式 x 当 x > 0


# ===== 模式基类 =====


class Pattern(ABC):
    """模式基类"""

    def __init__(self, line: int = 0, column: int = 0):
        self.line = line
        self.column = column

    @property
    @abstractmethod
    def pattern_type(self) -> PatternType:
        """模式类型"""
        pass

    @abstractmethod
    def match(self, value: Any, bindings: Dict[str, Any]) -> bool:
        """
        尝试匹配值

        Args:
            value: 要匹配的值
            bindings: 变量绑定字典（会被修改）

        Returns:
            是否匹配成功
        """
        pass

    @abstractmethod
    def get_variables(self) -> Set[str]:
        """
        获取模式中绑定的所有变量名

        Returns:
            变量名集合
        """
        pass

    def is_irrefutable(self) -> bool:
        """
        是否是不可反驳的模式（总是匹配）

        Returns:
            是否不可反驳
        """
        return False


# ===== 具体模式实现 =====


class WildcardPattern(Pattern):
    """通配符模式 _"""

    def __init__(self, line: int = 0, column: int = 0):
        super().__init__(line, column)

    @property
    def pattern_type(self) -> PatternType:
        return PatternType.WILDCARD

    def match(self, value: Any, bindings: Dict[str, Any]) -> bool:
        """匹配任何值，不绑定变量"""
        return True

    def get_variables(self) -> Set[str]:
        return set()

    def is_irrefutable(self) -> bool:
        return True

    def __str__(self):
        return "_"


class VariablePattern(Pattern):
    """变量模式 x"""

    def __init__(self, name: str, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.name = name

    @property
    def pattern_type(self) -> PatternType:
        return PatternType.VARIABLE

    def match(self, value: Any, bindings: Dict[str, Any]) -> bool:
        """绑定值到变量"""
        bindings[self.name] = value
        return True

    def get_variables(self) -> Set[str]:
        return {self.name}

    def is_irrefutable(self) -> bool:
        return True

    def __str__(self):
        return self.name


class LiteralPattern(Pattern):
    """字面量模式 42, "hello" """

    def __init__(
        self, value: Any, literal_type: str = "unknown", line: int = 0, column: int = 0
    ):
        super().__init__(line, column)
        self.value = value
        self.literal_type = literal_type  # "int", "float", "string", "bool", "char"

    @property
    def pattern_type(self) -> PatternType:
        return PatternType.LITERAL

    def match(self, value: Any, bindings: Dict[str, Any]) -> bool:
        """精确匹配字面量"""
        return self.value == value

    def get_variables(self) -> Set[str]:
        return set()

    def __str__(self):
        if isinstance(self.value, str):
            return f'"{self.value}"'
        return str(self.value)


class ConstructorPattern(Pattern):
    """构造器模式 Some(x), None"""

    def __init__(
        self,
        constructor: str,
        patterns: List[Pattern] = None,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(line, column)
        self.constructor = constructor
        self.patterns = patterns if patterns is not None else []

    @property
    def pattern_type(self) -> PatternType:
        return PatternType.CONSTRUCTOR

    def match(self, value: Any, bindings: Dict[str, Any]) -> bool:
        """匹配构造器"""
        if not isinstance(value, dict):
            return False

        if value.get("_constructor") != self.constructor:
            return False

        fields = value.get("_fields", [])
        if len(fields) != len(self.patterns):
            return False

        # 递归匹配每个字段
        for field_value, pattern in zip(fields, self.patterns):
            if not pattern.match(field_value, bindings):
                return False

        return True

    def get_variables(self) -> Set[str]:
        result = set()
        for pattern in self.patterns:
            result.update(pattern.get_variables())
        return result

    def __str__(self):
        if not self.patterns:
            return self.constructor
        args = ", ".join(str(p) for p in self.patterns)
        return f"{self.constructor}({args})"


class DestructurePattern(Pattern):
    """解构模式 点{x, y}"""

    def __init__(
        self,
        struct_name: str,
        fields: Dict[str, Pattern] = None,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(line, column)
        self.struct_name = struct_name
        self.fields = fields if fields is not None else {}

    @property
    def pattern_type(self) -> PatternType:
        return PatternType.DESTRUCTURE

    def match(self, value: Any, bindings: Dict[str, Any]) -> bool:
        """解构匹配"""
        if not isinstance(value, dict):
            return False

        if value.get("_type") != self.struct_name:
            return False

        value_fields = value.get("_fields", {})

        # 检查每个字段模式
        for field_name, pattern in self.fields.items():
            if field_name not in value_fields:
                return False

            if not pattern.match(value_fields[field_name], bindings):
                return False

        return True

    def get_variables(self) -> Set[str]:
        result = set()
        for pattern in self.fields.values():
            result.update(pattern.get_variables())
        return result

    def __str__(self):
        fields = ", ".join(f"{k}: {v}" for k, v in self.fields.items())
        return f"{self.struct_name}{{{fields}}}"


class RangePattern(Pattern):
    """范围模式 1..10"""

    def __init__(
        self,
        start: Any,
        end: Any,
        inclusive: bool = True,
        line: int = 0,
        column: int = 0,
    ):
        super().__init__(line, column)
        self.start = start
        self.end = end
        self.inclusive = inclusive  # 是否包含结束值

    @property
    def pattern_type(self) -> PatternType:
        return PatternType.RANGE

    def match(self, value: Any, bindings: Dict[str, Any]) -> bool:
        """检查值是否在范围内"""
        try:
            if self.inclusive:
                return self.start <= value <= self.end
            else:
                return self.start <= value < self.end
        except TypeError:
            return False

    def get_variables(self) -> Set[str]:
        return set()

    def __str__(self):
        if self.inclusive:
            return f"{self.start}..{self.end}"
        else:
            return f"{self.start}..<{self.end}"


class TuplePattern(Pattern):
    """元组模式 (x, y)"""

    def __init__(self, patterns: List[Pattern] = None, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.patterns = patterns if patterns is not None else []

    @property
    def pattern_type(self) -> PatternType:
        return PatternType.TUPLE

    def match(self, value: Any, bindings: Dict[str, Any]) -> bool:
        """匹配元组"""
        if not isinstance(value, (tuple, list)):
            return False

        if len(value) != len(self.patterns):
            return False

        # 递归匹配每个元素
        for elem_value, pattern in zip(value, self.patterns):
            if not pattern.match(elem_value, bindings):
                return False

        return True

    def get_variables(self) -> Set[str]:
        result = set()
        for pattern in self.patterns:
            result.update(pattern.get_variables())
        return result

    def __str__(self):
        args = ", ".join(str(p) for p in self.patterns)
        return f"({args})"


class OrPattern(Pattern):
    """或模式 x | y"""

    def __init__(self, patterns: List[Pattern] = None, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.patterns = patterns if patterns is not None else []

    @property
    def pattern_type(self) -> PatternType:
        return PatternType.OR

    def match(self, value: Any, bindings: Dict[str, Any]) -> bool:
        """任意一个模式匹配即可"""
        for pattern in self.patterns:
            new_bindings = bindings.copy()
            if pattern.match(value, new_bindings):
                bindings.update(new_bindings)
                return True
        return False

    def get_variables(self) -> Set[str]:
        # 所有分支必须绑定相同的变量
        if not self.patterns:
            return set()

        result = self.patterns[0].get_variables()
        for pattern in self.patterns[1:]:
            result &= pattern.get_variables()
        return result

    def __str__(self):
        return " | ".join(str(p) for p in self.patterns)


class AndPattern(Pattern):
    """与模式 x & y"""

    def __init__(self, patterns: List[Pattern] = None, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.patterns = patterns if patterns is not None else []

    @property
    def pattern_type(self) -> PatternType:
        return PatternType.AND

    def match(self, value: Any, bindings: Dict[str, Any]) -> bool:
        """所有模式都必须匹配"""
        for pattern in self.patterns:
            if not pattern.match(value, bindings):
                return False
        return True

    def get_variables(self) -> Set[str]:
        result = set()
        for pattern in self.patterns:
            result.update(pattern.get_variables())
        return result

    def __str__(self):
        return " & ".join(str(p) for p in self.patterns)


class GuardPattern(Pattern):
    """守卫模式 x 当 x > 0"""

    def __init__(
        self, pattern: Pattern, guard: str = "", line: int = 0, column: int = 0
    ):
        super().__init__(line, column)
        self.pattern = pattern
        self.guard = guard  # 守卫表达式（字符串表示）

    @property
    def pattern_type(self) -> PatternType:
        return PatternType.GUARD

    def match(
        self,
        value: Any,
        bindings: Dict[str, Any],
        eval_guard_fn: Optional[callable] = None,
    ) -> bool:
        """先匹配模式，再检查守卫

        Args:
            value: 要匹配的值
            bindings: 变量绑定字典（会被修改）
            eval_guard_fn: 可选的守卫求值回调，签名：
                (guard_expr: str, bindings: Dict[str, Any]) -> bool
                如果提供，则调用此回调来求值守卫表达式；
                否则直接返回 True（匹配成功但不检查守卫）。

        Returns:
            是否匹配成功（包括守卫条件）
        """
        if not self.pattern.match(value, bindings):
            return False

        # 如果有守卫表达式且有求值回调，则调用回调
        if self.guard and eval_guard_fn is not None:
            try:
                guard_result = eval_guard_fn(self.guard, bindings)
                return bool(guard_result)
            except Exception as e:
                # 守卫求值失败时，记录错误并返回 False
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"守卫表达式求值失败: {self.guard}, 错误: {e}")
                return False

        # 如果没有求值回调，直接返回 True（用于测试）
        return True

    def get_variables(self) -> Set[str]:
        return self.pattern.get_variables()

    def __str__(self):
        return f"{self.pattern} 当 {self.guard}"


# ===== 匹配分支 =====


class MatchCase:
    """匹配分支"""

    def __init__(self, pattern: Pattern, body: Any = None, guard: str = None):
        self.pattern = pattern
        self.body = body  # AST 节点（函数体）
        self.guard = guard  # 守卫表达式

    def is_wildcard(self) -> bool:
        """是否是通配符分支"""
        return isinstance(self.pattern, WildcardPattern)


# ===== 模式匹配器 =====


class PatternMatcher:
    """模式匹配器

    Attributes:
        errors: 匹配过程中的错误列表
        _eval_guard_fn: 守卫表达式求值回调（可选）
    """

    def __init__(self, eval_guard_fn: Optional[callable] = None):
        self.errors: List[str] = []
        self._eval_guard_fn = eval_guard_fn

    def match(self, value: Any, pattern: Pattern) -> Optional[Dict[str, Any]]:
        """
        匹配值和模式

        Args:
            value: 要匹配的值
            pattern: 模式

        Returns:
            如果匹配成功，返回变量绑定字典；否则返回 None
        """
        bindings: Dict[str, Any] = {}
        if pattern.match(value, bindings):
            return bindings
        return None

    def match_cases(
        self, value: Any, cases: List[MatchCase]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[MatchCase]]:
        """
        匹配值和多个分支

        Args:
            value: 要匹配的值
            cases: 匹配分支列表

        Returns:
            (变量绑定, 匹配的分支) 或 (None, None)
        """
        for case in cases:
            bindings = self.match(value, case.pattern)
            if bindings is not None:
                # 检查守卫
                if case.guard:
                    guard_result = self._evaluate_guard(case.guard, bindings)
                    if not guard_result:
                        # 守卫不满足，继续匹配下一个分支
                        continue
                return bindings, case

        return None, None

    def _evaluate_guard(self, guard_expr: str, bindings: Dict[str, Any]) -> bool:
        """求值守卫表达式

        支持两种求值方式：
        1. 如果设置了 eval_guard_fn 回调，使用回调求值
        2. 否则尝试基于绑定变量进行简单的表达式求值

        Args:
            guard_expr: 守卫表达式字符串
            bindings: 当前绑定的变量

        Returns:
            守卫条件是否满足
        """
        if self._eval_guard_fn is not None:
            try:
                return bool(self._eval_guard_fn(guard_expr, bindings))
            except Exception as e:
                self.errors.append(f"守卫表达式求值失败: {guard_expr}, 错误: {e}")
                return False

        # 内置简单求值器：支持基于绑定变量的基本比较表达式
        return self._simple_guard_eval(guard_expr, bindings)

    def _simple_guard_eval(self, expr: str, bindings: Dict[str, Any]) -> bool:
        """简单的守卫表达式求值器

        支持：
        - 变量引用（替换绑定的值）
        - 基本比较运算符（>, <, >=, <=, ==, !=）
        - 逻辑运算符（&&, ||）
        - 简单算术表达式

        Args:
            expr: 守卫表达式字符串
            bindings: 当前绑定的变量

        Returns:
            守卫条件是否满足
        """
        import re

        if not expr or not expr.strip():
            return True

        # 替换绑定的变量名为其值
        eval_expr = expr.strip()
        for var_name, var_value in bindings.items():
            # 使用正则表达式替换变量名（全词匹配）
            pattern = r"\b" + re.escape(var_name) + r"\b"
            if isinstance(var_value, str):
                # 字符串值用引号包裹
                eval_expr = re.sub(pattern, repr(var_value), eval_expr)
            else:
                eval_expr = re.sub(pattern, str(var_value), eval_expr)

        # 中文运算符替换为 Python 运算符
        op_map = {
            "并且": " and ",
            "或者": " or ",
            "大于": " > ",
            "小于": " < ",
            "大于等于": " >= ",
            "小于等于": " <= ",
            "等于": " == ",
            "不等于": " != ",
        }
        for cn_op, py_op in op_map.items():
            eval_expr = eval_expr.replace(cn_op, py_op)

        # 安全求值：限制可用的内置函数
        try:
            # 使用受限的全局命名空间进行求值
            allowed_globals = {
                "__builtins__": {
                    "abs": abs,
                    "len": len,
                    "min": min,
                    "max": max,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "str": str,
                    "True": True,
                    "False": False,
                }
            }
            result = eval(eval_expr, allowed_globals, {})
            return bool(result)
        except Exception as e:
            self.errors.append(f"守卫表达式求值失败: {expr} -> {eval_expr}, 错误: {e}")
            # 求值失败时保守地返回 True（匹配成功）
            return True

    def check_exhaustiveness(
        self, cases: List[MatchCase], type_info: Optional[Any] = None
    ) -> List[str]:
        """
        检查穷尽性

        Args:
            cases: 匹配分支列表
            type_info: 类型信息（用于检查枚举类型）

        Returns:
            未覆盖的情况列表
        """
        warnings = []

        # 检查是否有通配符分支
        has_wildcard = any(case.is_wildcard() for case in cases)

        if not has_wildcard:
            warnings.append("缺少通配符分支 _，可能存在未覆盖的情况")

        # TODO: 更精确的穷尽性检查
        # - 检查枚举类型的所有变体是否都被覆盖
        # - 检查是否有重叠的模式
        # - 检查是否有不可达的分支

        return warnings

    def check_redundancy(self, cases: List[MatchCase]) -> List[int]:
        """
        检查冗余分支

        Args:
            cases: 匹配分支列表

        Returns:
            冗余分支的索引列表
        """
        redundant = []

        for i, case in enumerate(cases):
            # 检查是否被之前的分支覆盖
            for j in range(i):
                if self._is_covered_by(case.pattern, cases[j].pattern):
                    redundant.append(i)
                    break

        return redundant

    def _is_covered_by(self, pattern: Pattern, other: Pattern) -> bool:
        """检查 pattern 是否被 other 覆盖

        覆盖规则：
        - 通配符/变量覆盖所有模式
        - 字面量模式：相同值或值在范围内覆盖
        - 构造器模式：相同构造器名 + 参数被覆盖
        - OR 模式：任一子模式被覆盖
        - Range 模式：other 的范围包含 pattern 的范围

        Args:
            pattern: 要检查的模式
            other: 覆盖模式

        Returns:
            pattern 是否被 other 覆盖
        """
        # 通配符覆盖所有模式
        if isinstance(other, WildcardPattern):
            return True

        # 变量模式覆盖所有模式
        if isinstance(other, VariablePattern):
            return True

        # 字面量模式：相同值覆盖
        if isinstance(pattern, LiteralPattern) and isinstance(other, LiteralPattern):
            return pattern.value == other.value

        # 字面量 vs OR 模式：字面量在 OR 范围内
        if isinstance(pattern, LiteralPattern) and isinstance(other, OrPattern):
            return any(self._is_covered_by(pattern, sub) for sub in other.patterns)

        # OR 模式：任一子模式被覆盖
        if isinstance(pattern, OrPattern):
            return all(self._is_covered_by(sub, other) for sub in pattern.patterns)

        # 构造器模式：相同构造器名 + 参数被覆盖
        if isinstance(pattern, ConstructorPattern) and isinstance(
            other, ConstructorPattern
        ):
            if pattern.constructor != other.constructor:
                return False
            # 递归检查参数
            if len(pattern.patterns) != len(other.patterns):
                return False
            return all(
                self._is_covered_by(p, o)
                for p, o in zip(pattern.patterns, other.patterns)
            )

        # 构造器 vs 变量模式：变量覆盖构造器
        if isinstance(pattern, ConstructorPattern) and isinstance(
            other, VariablePattern
        ):
            return True

        # 范围模式 vs 字面量模式：字面量在范围内
        if isinstance(pattern, LiteralPattern) and isinstance(other, RangePattern):
            return self._literal_in_range(pattern.value, other)

        # 范围模式 vs 范围模式：other 的范围包含 pattern 的范围
        if isinstance(pattern, RangePattern) and isinstance(other, RangePattern):
            return self._range_contains(other, pattern)

        # 元组模式 vs 元组模式：所有元素被覆盖
        if isinstance(pattern, TuplePattern) and isinstance(other, TuplePattern):
            if len(pattern.patterns) != len(other.patterns):
                return False
            return all(
                self._is_covered_by(p, o)
                for p, o in zip(pattern.patterns, other.patterns)
            )

        # 元组 vs 通配符/变量
        if isinstance(pattern, TuplePattern) and isinstance(
            other, (WildcardPattern, VariablePattern)
        ):
            return True

        # 解构模式 vs 通配符/变量
        if isinstance(pattern, DestructurePattern) and isinstance(
            other, (WildcardPattern, VariablePattern)
        ):
            return True

        # 解构模式 vs 解构模式：结构体名相同 + 所有字段被覆盖
        if isinstance(pattern, DestructurePattern) and isinstance(
            other, DestructurePattern
        ):
            if pattern.struct_name != other.struct_name:
                return False
            # 检查 other 的每个字段模式是否覆盖 pattern 对应字段
            for field_name, field_pattern in pattern.fields.items():
                if field_name not in other.fields:
                    return False
                if not self._is_covered_by(field_pattern, other.fields[field_name]):
                    return False
            return True

        return False

    def _literal_in_range(self, value: Any, range_pattern: "RangePattern") -> bool:
        """检查字面量是否在范围内

        Args:
            value: 字面量值
            range_pattern: 范围模式

        Returns:
            值是否在范围内
        """
        try:
            if range_pattern.inclusive:
                return range_pattern.start <= value <= range_pattern.end
            else:
                return range_pattern.start <= value < range_pattern.end
        except TypeError:
            return False

    def _range_contains(self, outer: "RangePattern", inner: "RangePattern") -> bool:
        """检查 outer 范围是否包含 inner 范围

        Args:
            outer: 外层范围（覆盖者）
            inner: 内层范围（被覆盖者）

        Returns:
            outer 是否包含 inner
        """
        try:
            if outer.inclusive and inner.inclusive:
                return outer.start <= inner.start and inner.end <= outer.end
            elif outer.inclusive and not inner.inclusive:
                return outer.start <= inner.start and inner.end < outer.end
            elif not outer.inclusive and inner.inclusive:
                return outer.start < inner.start and inner.end <= outer.end
            else:
                return outer.start < inner.start and inner.end < outer.end
        except TypeError:
            return False


# ===== 模式解析辅助函数 =====


def create_wildcard_pattern() -> WildcardPattern:
    """创建通配符模式"""
    return WildcardPattern()


def create_variable_pattern(name: str) -> VariablePattern:
    """创建变量模式"""
    return VariablePattern(name=name)


def create_literal_pattern(value: Any, literal_type: str = "unknown") -> LiteralPattern:
    """创建字面量模式"""
    return LiteralPattern(value=value, literal_type=literal_type)


def create_constructor_pattern(
    constructor: str, patterns: Optional[List[Pattern]] = None
) -> ConstructorPattern:
    """创建构造器模式"""
    return ConstructorPattern(constructor=constructor, patterns=patterns or [])


def create_destructure_pattern(
    struct_name: str, fields: Optional[Dict[str, Pattern]] = None
) -> DestructurePattern:
    """创建解构模式"""
    return DestructurePattern(struct_name=struct_name, fields=fields or {})


def create_range_pattern(start: Any, end: Any, inclusive: bool = True) -> RangePattern:
    """创建范围模式"""
    return RangePattern(start=start, end=end, inclusive=inclusive)


def create_tuple_pattern(patterns: Optional[List[Pattern]] = None) -> TuplePattern:
    """创建元组模式"""
    return TuplePattern(patterns=patterns or [])


def create_or_pattern(patterns: Optional[List[Pattern]] = None) -> OrPattern:
    """创建或模式"""
    return OrPattern(patterns=patterns or [])


def create_and_pattern(patterns: Optional[List[Pattern]] = None) -> AndPattern:
    """创建与模式"""
    return AndPattern(patterns=patterns or [])


def create_guard_pattern(pattern: Pattern, guard: str) -> GuardPattern:
    """创建守卫模式"""
    return GuardPattern(pattern=pattern, guard=guard)


# ===== 示例用法 =====

if __name__ == "__main__":
    print("=" * 70)
    print("模式匹配系统测试")
    print("=" * 70)

    matcher = PatternMatcher()

    # 测试 1: 通配符模式
    print("\n测试 1: 通配符模式")
    pattern = create_wildcard_pattern()
    result = matcher.match(42, pattern)
    print(f"  匹配 42: {result}")

    # 测试 2: 变量模式
    print("\n测试 2: 变量模式")
    pattern = create_variable_pattern("x")
    result = matcher.match(42, pattern)
    print(f"  匹配 42: {result}")

    # 测试 3: 字面量模式
    print("\n测试 3: 字面量模式")
    pattern = create_literal_pattern(42)
    result = matcher.match(42, pattern)
    print(f"  匹配 42: {result}")
    result = matcher.match(100, pattern)
    print(f"  匹配 100: {result}")

    # 测试 4: 构造器模式
    print("\n测试 4: 构造器模式")
    pattern = create_constructor_pattern("Some", [create_variable_pattern("x")])
    value = {"_constructor": "Some", "_fields": [42]}
    result = matcher.match(value, pattern)
    print(f"  匹配 Some(42): {result}")

    # 测试 5: 解构模式
    print("\n测试 5: 解构模式")
    pattern = create_destructure_pattern(
        "点", {"x": create_variable_pattern("x"), "y": create_variable_pattern("y")}
    )
    value = {"_type": "点", "_fields": {"x": 10, "y": 20}}
    result = matcher.match(value, pattern)
    print(f"  匹配 点{{x=10, y=20}}: {result}")

    # 测试 6: 范围模式
    print("\n测试 6: 范围模式")
    pattern = create_range_pattern(1, 10)
    result = matcher.match(5, pattern)
    print(f"  匹配 5 (1..10): {result}")
    result = matcher.match(15, pattern)
    print(f"  匹配 15 (1..10): {result}")

    # 测试 7: 元组模式
    print("\n测试 7: 元组模式")
    pattern = create_tuple_pattern(
        [create_variable_pattern("x"), create_variable_pattern("y")]
    )
    result = matcher.match((10, 20), pattern)
    print(f"  匹配 (10, 20): {result}")

    # 测试 8: 或模式
    print("\n测试 8: 或模式")
    pattern = create_or_pattern(
        [
            create_literal_pattern(1),
            create_literal_pattern(2),
            create_literal_pattern(3),
        ]
    )
    result = matcher.match(2, pattern)
    print(f"  匹配 2 (1|2|3): {result}")
    result = matcher.match(5, pattern)
    print(f"  匹配 5 (1|2|3): {result}")

    print("\n" + "=" * 70)
    print("所有测试完成")
    print("=" * 70)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模式匹配系统测试 - Pattern Matching Tests

Phase 4 - Stage 2 - Task 11.2

作者：ZHC 开发团队
日期：2026-04-08
"""

import pytest
from typing import List, Set, Dict, Any

from src.semantic.pattern_matching import (
    PatternMatcher,
    Pattern,
    WildcardPattern,
    VariablePattern,
    LiteralPattern,
    ConstructorPattern,
    DestructurePattern,
    RangePattern,
    TuplePattern,
    OrPattern,
    AndPattern,
    GuardPattern,
    MatchCase,
    create_wildcard_pattern,
    create_variable_pattern,
    create_literal_pattern,
    create_constructor_pattern,
    create_destructure_pattern,
    create_range_pattern,
    create_tuple_pattern,
    create_or_pattern,
    create_guard_pattern,
    PatternType,
)


class TestWildcardPattern:
    """通配符模式测试"""
    
    def test_match_any_value(self):
        """测试匹配任意值"""
        pattern = WildcardPattern()
        matcher = PatternMatcher()
        
        assert matcher.match(42, pattern) == {}
        assert matcher.match("hello", pattern) == {}
        assert matcher.match(None, pattern) == {}
        assert matcher.match([1, 2, 3], pattern) == {}
    
    def test_get_variables(self):
        """测试获取变量"""
        pattern = WildcardPattern()
        assert pattern.get_variables() == set()
    
    def test_is_irrefutable(self):
        """测试不可反驳性"""
        pattern = WildcardPattern()
        assert pattern.is_irrefutable() is True
    
    def test_str(self):
        """测试字符串表示"""
        pattern = WildcardPattern()
        assert str(pattern) == "_"


class TestVariablePattern:
    """变量模式测试"""
    
    def test_match_and_bind(self):
        """测试匹配并绑定"""
        pattern = VariablePattern(name="x")
        matcher = PatternMatcher()
        
        result = matcher.match(42, pattern)
        assert result == {"x": 42}
    
    def test_get_variables(self):
        """测试获取变量"""
        pattern = VariablePattern(name="value")
        assert pattern.get_variables() == {"value"}
    
    def test_is_irrefutable(self):
        """测试不可反驳性"""
        pattern = VariablePattern(name="x")
        assert pattern.is_irrefutable() is True
    
    def test_str(self):
        """测试字符串表示"""
        pattern = VariablePattern(name="x")
        assert str(pattern) == "x"


class TestLiteralPattern:
    """字面量模式测试"""
    
    def test_match_integer(self):
        """测试整数匹配"""
        pattern = LiteralPattern(value=42, literal_type="int")
        matcher = PatternMatcher()
        
        assert matcher.match(42, pattern) == {}
        assert matcher.match(100, pattern) is None
    
    def test_match_string(self):
        """测试字符串匹配"""
        pattern = LiteralPattern(value="hello", literal_type="string")
        matcher = PatternMatcher()
        
        assert matcher.match("hello", pattern) == {}
        assert matcher.match("world", pattern) is None
    
    def test_match_bool(self):
        """测试布尔匹配"""
        pattern = LiteralPattern(value=True, literal_type="bool")
        matcher = PatternMatcher()
        
        assert matcher.match(True, pattern) == {}
        assert matcher.match(False, pattern) is None
    
    def test_get_variables(self):
        """测试获取变量"""
        pattern = LiteralPattern(value=42)
        assert pattern.get_variables() == set()
    
    def test_str(self):
        """测试字符串表示"""
        pattern = LiteralPattern(value=42)
        assert str(pattern) == "42"
        
        pattern_str = LiteralPattern(value="test")
        assert str(pattern_str) == '"test"'


class TestConstructorPattern:
    """构造器模式测试"""
    
    def test_match_no_fields(self):
        """测试无字段构造器"""
        pattern = ConstructorPattern(constructor="None", patterns=[])
        matcher = PatternMatcher()
        
        value = {"_constructor": "None", "_fields": []}
        assert matcher.match(value, pattern) == {}
        
        value = {"_constructor": "Some", "_fields": []}
        assert matcher.match(value, pattern) is None
    
    def test_match_with_fields(self):
        """测试带字段构造器"""
        pattern = ConstructorPattern(
            constructor="Some",
            patterns=[VariablePattern(name="value")]
        )
        matcher = PatternMatcher()
        
        value = {"_constructor": "Some", "_fields": [42]}
        result = matcher.match(value, pattern)
        assert result == {"value": 42}
    
    def test_match_nested(self):
        """测试嵌套构造器"""
        inner = ConstructorPattern(constructor="Some", patterns=[VariablePattern(name="x")])
        outer = ConstructorPattern(constructor="Result", patterns=[inner])
        matcher = PatternMatcher()
        
        value = {
            "_constructor": "Result",
            "_fields": [
                {"_constructor": "Some", "_fields": [42]}
            ]
        }
        result = matcher.match(value, outer)
        assert result == {"x": 42}
    
    def test_get_variables(self):
        """测试获取变量"""
        pattern = ConstructorPattern(
            constructor="Pair",
            patterns=[
                VariablePattern(name="first"),
                VariablePattern(name="second")
            ]
        )
        vars = pattern.get_variables()
        assert vars == {"first", "second"}
    
    def test_str(self):
        """测试字符串表示"""
        pattern = ConstructorPattern(constructor="Some", patterns=[
            VariablePattern(name="x")
        ])
        assert str(pattern) == "Some(x)"


class TestDestructurePattern:
    """解构模式测试"""
    
    def test_match(self):
        """测试解构匹配"""
        pattern = DestructurePattern(
            struct_name="点",
            fields={
                "x": VariablePattern(name="x"),
                "y": VariablePattern(name="y")
            }
        )
        matcher = PatternMatcher()
        
        value = {
            "_type": "点",
            "_fields": {"x": 10, "y": 20}
        }
        result = matcher.match(value, pattern)
        assert result == {"x": 10, "y": 20}
    
    def test_nested_destructure(self):
        """测试嵌套解构"""
        pattern = DestructurePattern(
            struct_name="矩形",
            fields={
                "左上": DestructurePattern(
                    struct_name="点",
                    fields={
                        "x": VariablePattern(name="x1"),
                        "y": VariablePattern(name="y1")
                    }
                ),
                "右下": DestructurePattern(
                    struct_name="点",
                    fields={
                        "x": VariablePattern(name="x2"),
                        "y": VariablePattern(name="y2")
                    }
                )
            }
        )
        matcher = PatternMatcher()
        
        value = {
            "_type": "矩形",
            "_fields": {
                "左上": {"_type": "点", "_fields": {"x": 0, "y": 0}},
                "右下": {"_type": "点", "_fields": {"x": 100, "y": 100}}
            }
        }
        result = matcher.match(value, pattern)
        assert result == {"x1": 0, "y1": 0, "x2": 100, "y2": 100}
    
    def test_get_variables(self):
        """测试获取变量"""
        pattern = DestructurePattern(
            struct_name="点",
            fields={
                "x": VariablePattern(name="x"),
                "y": VariablePattern(name="y")
            }
        )
        assert pattern.get_variables() == {"x", "y"}


class TestRangePattern:
    """范围模式测试"""
    
    def test_match_inclusive(self):
        """测试包含范围"""
        pattern = RangePattern(start=1, end=10)
        matcher = PatternMatcher()
        
        assert matcher.match(1, pattern) == {}
        assert matcher.match(5, pattern) == {}
        assert matcher.match(10, pattern) == {}
        assert matcher.match(0, pattern) is None
        assert matcher.match(11, pattern) is None
    
    def test_match_exclusive(self):
        """测试不包含范围"""
        pattern = RangePattern(start=1, end=10, inclusive=False)
        matcher = PatternMatcher()
        
        # exclusive: 1 <= value < 10
        assert matcher.match(1, pattern) == {}  # 1 在范围内
        assert matcher.match(9, pattern) == {}  # 9 在范围内
        assert matcher.match(10, pattern) is None  # 10 不在范围内
    
    def test_match_string_range(self):
        """测试字符串范围"""
        pattern = RangePattern(start="a", end="z")
        matcher = PatternMatcher()
        
        assert matcher.match("m", pattern) == {}
        assert matcher.match("A", pattern) is None
    
    def test_get_variables(self):
        """测试获取变量"""
        pattern = RangePattern(start=1, end=10)
        assert pattern.get_variables() == set()
    
    def test_str(self):
        """测试字符串表示"""
        pattern = RangePattern(start=1, end=10)
        assert str(pattern) == "1..10"
        
        pattern_exclusive = RangePattern(start=1, end=10, inclusive=False)
        assert str(pattern_exclusive) == "1..<10"


class TestTuplePattern:
    """元组模式测试"""
    
    def test_match_empty_tuple(self):
        """测试空元组"""
        pattern = TuplePattern(patterns=[])
        matcher = PatternMatcher()
        
        assert matcher.match((), pattern) == {}
        assert matcher.match([], pattern) == {}
    
    def test_match_with_elements(self):
        """测试带元素的元组"""
        pattern = TuplePattern(patterns=[
            LiteralPattern(value=1),
            LiteralPattern(value=2),
            VariablePattern(name="third")
        ])
        matcher = PatternMatcher()
        
        result = matcher.match((1, 2, 3), pattern)
        assert result == {"third": 3}
    
    def test_mismatch_length(self):
        """测试长度不匹配"""
        pattern = TuplePattern(patterns=[
            LiteralPattern(value=1),
            LiteralPattern(value=2)
        ])
        matcher = PatternMatcher()
        
        assert matcher.match((1, 2, 3), pattern) is None
        assert matcher.match((1,), pattern) is None
    
    def test_get_variables(self):
        """测试获取变量"""
        pattern = TuplePattern(patterns=[
            VariablePattern(name="first"),
            VariablePattern(name="second")
        ])
        assert pattern.get_variables() == {"first", "second"}
    
    def test_str(self):
        """测试字符串表示"""
        pattern = TuplePattern(patterns=[
            VariablePattern(name="x"),
            VariablePattern(name="y")
        ])
        assert str(pattern) == "(x, y)"


class TestOrPattern:
    """或模式测试"""
    
    def test_match_first(self):
        """测试匹配第一个"""
        pattern = OrPattern(patterns=[
            LiteralPattern(value=1),
            LiteralPattern(value=2),
            LiteralPattern(value=3)
        ])
        matcher = PatternMatcher()
        
        result = matcher.match(1, pattern)
        assert result == {}
    
    def test_match_last(self):
        """测试匹配最后一个"""
        pattern = OrPattern(patterns=[
            LiteralPattern(value=1),
            LiteralPattern(value=2),
            LiteralPattern(value=3)
        ])
        matcher = PatternMatcher()
        
        result = matcher.match(3, pattern)
        assert result == {}
    
    def test_no_match(self):
        """测试不匹配"""
        pattern = OrPattern(patterns=[
            LiteralPattern(value=1),
            LiteralPattern(value=2)
        ])
        matcher = PatternMatcher()
        
        assert matcher.match(3, pattern) is None
    
    def test_get_variables(self):
        """测试获取变量（所有分支的交集）"""
        pattern = OrPattern(patterns=[
            VariablePattern(name="x"),
            VariablePattern(name="x")
        ])
        assert pattern.get_variables() == {"x"}
    
    def test_str(self):
        """测试字符串表示"""
        pattern = OrPattern(patterns=[
            LiteralPattern(value=1),
            LiteralPattern(value=2)
        ])
        assert str(pattern) == "1 | 2"


class TestAndPattern:
    """与模式测试"""
    
    def test_match_both(self):
        """测试两个都匹配"""
        pattern = AndPattern(patterns=[
            RangePattern(start=1, end=10),
            RangePattern(start=5, end=15)
        ])
        matcher = PatternMatcher()
        
        assert matcher.match(7, pattern) == {}
        assert matcher.match(1, pattern) is None  # 不满足第二个条件
    
    def test_no_match(self):
        """测试不匹配"""
        pattern = AndPattern(patterns=[
            RangePattern(start=1, end=10),
            RangePattern(start=20, end=30)
        ])
        matcher = PatternMatcher()
        
        assert matcher.match(15, pattern) is None
    
    def test_get_variables(self):
        """测试获取变量"""
        pattern = AndPattern(patterns=[
            VariablePattern(name="x"),
            VariablePattern(name="y")
        ])
        assert pattern.get_variables() == {"x", "y"}
    
    def test_str(self):
        """测试字符串表示"""
        pattern = AndPattern(patterns=[
            VariablePattern(name="x"),
            VariablePattern(name="y")
        ])
        assert str(pattern) == "x & y"


class TestGuardPattern:
    """守卫模式测试"""
    
    def test_match_with_guard(self):
        """测试带守卫的匹配"""
        pattern = GuardPattern(
            pattern=VariablePattern(name="n"),
            guard="n > 0"
        )
        matcher = PatternMatcher()
        
        # 注意：当前的守卫求值未实现，总是返回 True
        result = matcher.match(10, pattern)
        assert result == {"n": 10}
    
    def test_get_variables(self):
        """测试获取变量"""
        pattern = GuardPattern(
            pattern=VariablePattern(name="x"),
            guard="x > 0"
        )
        assert pattern.get_variables() == {"x"}
    
    def test_str(self):
        """测试字符串表示"""
        pattern = GuardPattern(
            pattern=VariablePattern(name="x"),
            guard="x > 0"
        )
        assert str(pattern) == "x 当 x > 0"


class TestPatternMatcher:
    """模式匹配器测试"""
    
    def test_match_cases(self):
        """测试匹配分支"""
        matcher = PatternMatcher()
        cases = [
            MatchCase(
                pattern=LiteralPattern(value=1),
                body="one"
            ),
            MatchCase(
                pattern=LiteralPattern(value=2),
                body="two"
            ),
            MatchCase(
                pattern=WildcardPattern(),
                body="other"
            )
        ]
        
        bindings, case = matcher.match_cases(1, cases)
        assert bindings == {}
        assert case.body == "one"
        
        bindings, case = matcher.match_cases(3, cases)
        assert bindings == {}
        assert case.body == "other"
    
    def test_match_cases_no_match(self):
        """测试无匹配"""
        matcher = PatternMatcher()
        cases = [
            MatchCase(
                pattern=LiteralPattern(value=1),
                body="one"
            )
        ]
        
        bindings, case = matcher.match_cases(2, cases)
        assert bindings is None
        assert case is None
    
    def test_check_exhaustiveness(self):
        """测试穷尽性检查"""
        matcher = PatternMatcher()
        cases = [
            MatchCase(pattern=WildcardPattern(), body="other")
        ]
        
        warnings = matcher.check_exhaustiveness(cases)
        assert len(warnings) == 0  # 有通配符，不应该有警告


class TestHelperFunctions:
    """辅助函数测试"""
    
    def test_create_wildcard_pattern(self):
        """测试创建通配符模式"""
        pattern = create_wildcard_pattern()
        assert isinstance(pattern, WildcardPattern)
    
    def test_create_variable_pattern(self):
        """测试创建变量模式"""
        pattern = create_variable_pattern("x")
        assert isinstance(pattern, VariablePattern)
        assert pattern.name == "x"
    
    def test_create_literal_pattern(self):
        """测试创建字面量模式"""
        pattern = create_literal_pattern(42)
        assert isinstance(pattern, LiteralPattern)
        assert pattern.value == 42
    
    def test_create_constructor_pattern(self):
        """测试创建构造器模式"""
        pattern = create_constructor_pattern("Some", [
            create_variable_pattern("x")
        ])
        assert isinstance(pattern, ConstructorPattern)
        assert pattern.constructor == "Some"
    
    def test_create_destructure_pattern(self):
        """测试创建解构模式"""
        pattern = create_destructure_pattern("点", {
            "x": create_variable_pattern("x")
        })
        assert isinstance(pattern, DestructurePattern)
        assert pattern.struct_name == "点"
    
    def test_create_range_pattern(self):
        """测试创建范围模式"""
        pattern = create_range_pattern(1, 10)
        assert isinstance(pattern, RangePattern)
        assert pattern.start == 1
        assert pattern.end == 10
    
    def test_create_tuple_pattern(self):
        """测试创建元组模式"""
        pattern = create_tuple_pattern([
            create_variable_pattern("x")
        ])
        assert isinstance(pattern, TuplePattern)
    
    def test_create_or_pattern(self):
        """测试创建或模式"""
        pattern = create_or_pattern([
            create_literal_pattern(1),
            create_literal_pattern(2)
        ])
        assert isinstance(pattern, OrPattern)
    
    def test_create_guard_pattern(self):
        """测试创建守卫模式"""
        pattern = create_guard_pattern(
            create_variable_pattern("x"),
            "x > 0"
        )
        assert isinstance(pattern, GuardPattern)
        assert pattern.guard == "x > 0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
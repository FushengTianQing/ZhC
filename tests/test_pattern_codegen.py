#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模式匹配代码生成器测试 - Pattern Matching Code Generator Tests

测试代码生成器的各项功能：
1. switch 语句生成
2. if-else 链生成
3. 模式条件生成
4. 变量绑定生成
5. 嵌套匹配生成

Phase 4 - Stage 2 - Task 11.2 Day 3

作者：ZHC 开发团队
日期：2026-04-08
"""

import pytest
from typing import Dict, List

from zhc.semantic.pattern_matching import (
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
)

from zhc.codegen.pattern_codegen import (
    PatternCodeGenerator,
    PatternCodeResult,
    generate_match_code,
    generate_pattern_condition,
    generate_pattern_bindings,
)


# ===== 测试 switch 语句生成 =====

class TestSwitchGeneration:
    """测试 switch 语句生成"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.generator = PatternCodeGenerator()
    
    def test_literal_patterns_use_switch(self):
        """测试字面量模式使用 switch"""
        cases = [
            MatchCase(LiteralPattern(1, "INT")),
            MatchCase(LiteralPattern(2, "INT")),
            MatchCase(LiteralPattern(3, "INT"))
        ]
        
        result = self.generator.generate_match_expression("x", cases)
        assert result.success
        assert "switch" in result.code
        assert "case 1:" in result.code
        assert "case 2:" in result.code
        assert "case 3:" in result.code
    
    def test_constructor_patterns_use_switch(self):
        """测试构造器模式使用 switch"""
        cases = [
            MatchCase(ConstructorPattern("Some", [VariablePattern("x")])),
            MatchCase(ConstructorPattern("None"))
        ]
        
        result = self.generator.generate_match_expression("opt", cases)
        assert result.success
        assert "switch" in result.code
        assert "case Some:" in result.code
        assert "case None:" in result.code
    
    def test_or_pattern_in_switch(self):
        """测试或模式在 switch 中生成多个 case 标签"""
        cases = [
            MatchCase(OrPattern([
                LiteralPattern(1, "INT"),
                LiteralPattern(2, "INT"),
                LiteralPattern(3, "INT")
            ])),
            MatchCase(WildcardPattern())
        ]
        
        result = self.generator.generate_match_expression("x", cases)
        assert result.success
        assert "switch" in result.code
        assert "case 1:" in result.code
        assert "case 2:" in result.code
        assert "case 3:" in result.code
    
    def test_guard_pattern_not_use_switch(self):
        """测试守卫模式不使用 switch"""
        cases = [
            MatchCase(GuardPattern(
                pattern=LiteralPattern(1, "INT"),
                guard="x > 0"
            )),
            MatchCase(WildcardPattern())
        ]
        
        result = self.generator.generate_match_expression("x", cases)
        assert result.success
        assert "switch" not in result.code
        assert "if" in result.code
    
    def test_range_pattern_not_use_switch(self):
        """测试范围模式不使用 switch"""
        cases = [
            MatchCase(RangePattern(1, 10)),
            MatchCase(WildcardPattern())
        ]
        
        result = self.generator.generate_match_expression("x", cases)
        assert result.success
        assert "switch" not in result.code
        assert "if" in result.code


# ===== 测试 if-else 链生成 =====

class TestIfElseGeneration:
    """测试 if-else 链生成"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.generator = PatternCodeGenerator()
    
    def test_range_pattern_if_else(self):
        """测试范围模式生成 if-else"""
        cases = [
            MatchCase(RangePattern(1, 10)),
            MatchCase(RangePattern(11, 20)),
            MatchCase(WildcardPattern())
        ]
        
        result = self.generator.generate_match_expression("n", cases)
        assert result.success
        assert "if" in result.code
        assert "else if" in result.code
        assert "else" in result.code
    
    def test_destructure_pattern_if_else(self):
        """测试解构模式生成 if-else"""
        cases = [
            MatchCase(DestructurePattern("Point", {
                "x": VariablePattern("px"),
                "y": VariablePattern("py")
            })),
            MatchCase(WildcardPattern())
        ]
        
        result = self.generator.generate_match_expression("point", cases)
        assert result.success
        assert "if" in result.code
        assert "_type == Point" in result.code
    
    def test_tuple_pattern_if_else(self):
        """测试元组模式生成 if-else"""
        cases = [
            MatchCase(TuplePattern([
                VariablePattern("a"),
                VariablePattern("b")
            ])),
            MatchCase(WildcardPattern())
        ]
        
        result = self.generator.generate_match_expression("tuple", cases)
        assert result.success
        assert "if" in result.code
        assert ".length == 2" in result.code
    
    def test_guard_pattern_if_else(self):
        """测试守卫模式生成 if-else"""
        cases = [
            MatchCase(GuardPattern(
                pattern=VariablePattern("x"),
                guard="x > 0"
            )),
            MatchCase(WildcardPattern())
        ]
        
        result = self.generator.generate_match_expression("n", cases)
        assert result.success
        assert "if" in result.code
        assert "&&" in result.code


# ===== 测试模式条件生成 =====

class TestPatternConditionGeneration:
    """测试模式条件生成"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.generator = PatternCodeGenerator()
    
    def test_wildcard_condition(self):
        """测试通配符条件"""
        condition = self.generator._generate_pattern_condition(
            WildcardPattern(), "x"
        )
        assert condition == "1"
    
    def test_variable_condition(self):
        """测试变量模式条件"""
        condition = self.generator._generate_pattern_condition(
            VariablePattern("x"), "value"
        )
        assert condition == "1"
    
    def test_literal_condition(self):
        """测试字面量条件"""
        condition = self.generator._generate_pattern_condition(
            LiteralPattern(42, "INT"), "x"
        )
        assert condition == "x == 42"
    
    def test_range_condition_inclusive(self):
        """测试范围条件（包含）"""
        condition = self.generator._generate_pattern_condition(
            RangePattern(1, 10, inclusive=True), "n"
        )
        assert "n >= 1" in condition
        assert "n <= 10" in condition
    
    def test_range_condition_exclusive(self):
        """测试范围条件（不包含）"""
        condition = self.generator._generate_pattern_condition(
            RangePattern(1, 10, inclusive=False), "n"
        )
        assert "n >= 1" in condition
        assert "n < 10" in condition
    
    def test_constructor_condition(self):
        """测试构造器条件"""
        condition = self.generator._generate_pattern_condition(
            ConstructorPattern("Some", [VariablePattern("x")]), "opt"
        )
        assert "opt._tag == Some" in condition
    
    def test_constructor_with_nested_condition(self):
        """测试嵌套构造器条件"""
        condition = self.generator._generate_pattern_condition(
            ConstructorPattern("Some", [LiteralPattern(42, "INT")]), "opt"
        )
        assert "opt._tag == Some" in condition
        assert "opt._fields[0] == 42" in condition
    
    def test_destructure_condition(self):
        """测试解构条件"""
        condition = self.generator._generate_pattern_condition(
            DestructurePattern("Point", {
                "x": VariablePattern("px"),
                "y": VariablePattern("py")
            }), "point"
        )
        assert "point._type == Point" in condition
    
    def test_destructure_with_nested_condition(self):
        """测试嵌套解构条件"""
        condition = self.generator._generate_pattern_condition(
            DestructurePattern("Point", {
                "x": LiteralPattern(10, "INT"),
                "y": VariablePattern("py")
            }), "point"
        )
        assert "point._type == Point" in condition
        assert "point.x == 10" in condition
    
    def test_tuple_condition(self):
        """测试元组条件"""
        condition = self.generator._generate_pattern_condition(
            TuplePattern([
                VariablePattern("a"),
                VariablePattern("b")
            ]), "tuple"
        )
        assert "tuple.length == 2" in condition
    
    def test_tuple_with_nested_condition(self):
        """测试嵌套元组条件"""
        condition = self.generator._generate_pattern_condition(
            TuplePattern([
                LiteralPattern(1, "INT"),
                LiteralPattern(2, "INT")
            ]), "tuple"
        )
        assert "tuple.length == 2" in condition
        assert "tuple.elements[0] == 1" in condition
        assert "tuple.elements[1] == 2" in condition
    
    def test_or_condition(self):
        """测试或模式条件"""
        condition = self.generator._generate_pattern_condition(
            OrPattern([
                LiteralPattern(1, "INT"),
                LiteralPattern(2, "INT")
            ]), "x"
        )
        assert "||" in condition
        assert "x == 1" in condition
        assert "x == 2" in condition
    
    def test_and_condition(self):
        """测试与模式条件"""
        condition = self.generator._generate_pattern_condition(
            AndPattern([
                RangePattern(1, 10),
                VariablePattern("x")
            ]), "n"
        )
        assert "&&" in condition
    
    def test_guard_condition(self):
        """测试守卫模式条件"""
        condition = self.generator._generate_pattern_condition(
            GuardPattern(
                pattern=VariablePattern("x"),
                guard="x > 0"
            ), "n"
        )
        assert "&&" in condition
        assert "(x > 0)" in condition


# ===== 测试变量绑定生成 =====

class TestBindingGeneration:
    """测试变量绑定生成"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.generator = PatternCodeGenerator()
    
    def test_variable_binding(self):
        """测试变量模式绑定"""
        bindings = self.generator._collect_bindings(
            VariablePattern("x"), "value"
        )
        assert bindings == {"x": "value"}
    
    def test_constructor_binding(self):
        """测试构造器模式绑定"""
        bindings = self.generator._collect_bindings(
            ConstructorPattern("Some", [VariablePattern("x")]), "opt"
        )
        assert bindings == {"x": "opt._fields[0]"}
    
    def test_constructor_multiple_bindings(self):
        """测试构造器模式多个绑定"""
        bindings = self.generator._collect_bindings(
            ConstructorPattern("Pair", [
                VariablePattern("a"),
                VariablePattern("b")
            ]), "pair"
        )
        assert bindings == {
            "a": "pair._fields[0]",
            "b": "pair._fields[1]"
        }
    
    def test_destructure_binding(self):
        """测试解构模式绑定"""
        bindings = self.generator._collect_bindings(
            DestructurePattern("Point", {
                "x": VariablePattern("px"),
                "y": VariablePattern("py")
            }), "point"
        )
        assert bindings == {
            "px": "point.x",
            "py": "point.y"
        }
    
    def test_tuple_binding(self):
        """测试元组模式绑定"""
        bindings = self.generator._collect_bindings(
            TuplePattern([
                VariablePattern("a"),
                VariablePattern("b")
            ]), "tuple"
        )
        assert bindings == {
            "a": "tuple.elements[0]",
            "b": "tuple.elements[1]"
        }
    
    def test_nested_binding(self):
        """测试嵌套模式绑定"""
        bindings = self.generator._collect_bindings(
            ConstructorPattern("Some", [
                TuplePattern([
                    VariablePattern("n"),
                    VariablePattern("s")
                ])
            ]), "opt"
        )
        assert bindings == {
            "n": "opt._fields[0].elements[0]",
            "s": "opt._fields[0].elements[1]"
        }
    
    def test_or_pattern_binding(self):
        """测试或模式绑定"""
        bindings = self.generator._collect_bindings(
            OrPattern([
                VariablePattern("x"),
                VariablePattern("x")
            ]), "value"
        )
        # 或模式使用第一个分支的绑定
        assert bindings == {"x": "value"}
    
    def test_and_pattern_binding(self):
        """测试与模式绑定"""
        bindings = self.generator._collect_bindings(
            AndPattern([
                VariablePattern("x"),
                VariablePattern("y")
            ]), "value"
        )
        # 与模式收集所有绑定
        assert bindings == {"x": "value", "y": "value"}
    
    def test_guard_pattern_binding(self):
        """测试守卫模式绑定"""
        bindings = self.generator._collect_bindings(
            GuardPattern(
                pattern=VariablePattern("x"),
                guard="x > 0"
            ), "value"
        )
        assert bindings == {"x": "value"}
    
    def test_binding_code_generation(self):
        """测试绑定代码生成"""
        bindings = {"x": "value", "y": "value._field"}
        code = self.generator._generate_pattern_bindings(
            VariablePattern("x"), "value"
        )
        # 实际的绑定代码生成需要从模式中收集
        assert "auto" in code or code == ""


# ===== 测试完整匹配表达式生成 =====

class TestFullMatchGeneration:
    """测试完整匹配表达式生成"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.generator = PatternCodeGenerator()
    
    def test_simple_match(self):
        """测试简单匹配"""
        cases = [
            MatchCase(LiteralPattern(1, "INT")),
            MatchCase(LiteralPattern(2, "INT")),
            MatchCase(WildcardPattern())
        ]
        
        result = self.generator.generate_match_expression("x", cases)
        assert result.success
        assert "switch" in result.code
        assert "case 1:" in result.code
        assert "case 2:" in result.code
        assert "default:" in result.code
    
    def test_option_match(self):
        """测试选项类型匹配"""
        cases = [
            MatchCase(ConstructorPattern("Some", [VariablePattern("x")])),
            MatchCase(ConstructorPattern("None"))
        ]
        
        result = self.generator.generate_match_expression("opt", cases)
        assert result.success
        assert "switch" in result.code
        assert "case Some:" in result.code
        assert "case None:" in result.code
        assert result.bindings == {}
    
    def test_enum_match(self):
        """测试枚举类型匹配"""
        cases = [
            MatchCase(ConstructorPattern("Red")),
            MatchCase(ConstructorPattern("Green")),
            MatchCase(ConstructorPattern("Blue"))
        ]
        
        result = self.generator.generate_match_expression("color", cases)
        assert result.success
        assert "switch" in result.code
        assert "case Red:" in result.code
        assert "case Green:" in result.code
        assert "case Blue:" in result.code
    
    def test_complex_match(self):
        """测试复杂匹配"""
        cases = [
            MatchCase(ConstructorPattern("Some", [
                TuplePattern([
                    VariablePattern("n"),
                    VariablePattern("s")
                ])
            ])),
            MatchCase(ConstructorPattern("None"))
        ]
        
        result = self.generator.generate_match_expression("opt", cases)
        assert result.success
        assert "switch" in result.code
        assert "case Some:" in result.code


# ===== 测试辅助函数 =====

class TestHelperFunctions:
    """测试辅助函数"""
    
    def test_generate_match_code_function(self):
        """测试 generate_match_code 便捷函数"""
        cases = [
            MatchCase(LiteralPattern(1, "INT")),
            MatchCase(WildcardPattern())
        ]
        
        result = generate_match_code("x", cases)
        assert isinstance(result, PatternCodeResult)
        assert result.success
    
    def test_generate_pattern_condition_function(self):
        """测试 generate_pattern_condition 便捷函数"""
        condition = generate_pattern_condition(
            LiteralPattern(42, "INT"), "x"
        )
        assert condition == "x == 42"
    
    def test_generate_pattern_bindings_function(self):
        """测试 generate_pattern_bindings 便捷函数"""
        bindings = generate_pattern_bindings(
            VariablePattern("x"), "value"
        )
        # 返回的是代码字符串
        assert isinstance(bindings, str)


# ===== 测试复杂场景 =====

class TestComplexScenarios:
    """测试复杂的匹配场景"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.generator = PatternCodeGenerator()
    
    def test_deeply_nested_pattern(self):
        """测试深度嵌套模式"""
        cases = [
            MatchCase(ConstructorPattern("Some", [
                ConstructorPattern("Pair", [
                    VariablePattern("a"),
                    VariablePattern("b")
                ])
            ])),
            MatchCase(ConstructorPattern("None"))
        ]
        
        result = self.generator.generate_match_expression("opt", cases)
        assert result.success
        assert "switch" in result.code
    
    def test_mixed_pattern_types(self):
        """测试混合模式类型"""
        cases = [
            MatchCase(LiteralPattern(0, "INT")),
            MatchCase(RangePattern(1, 10)),
            MatchCase(RangePattern(11, 20)),
            MatchCase(VariablePattern("x"))
        ]
        
        result = self.generator.generate_match_expression("n", cases)
        assert result.success
        # 第一个是字面量，后面是范围和变量，应该用 if-else
        assert "if" in result.code
    
    def test_multiple_guards(self):
        """测试多个守卫"""
        cases = [
            MatchCase(GuardPattern(
                pattern=RangePattern(1, 10),
                guard="x % 2 == 0"
            )),
            MatchCase(GuardPattern(
                pattern=RangePattern(1, 10),
                guard="x % 2 == 1"
            )),
            MatchCase(WildcardPattern())
        ]
        
        result = self.generator.generate_match_expression("n", cases)
        assert result.success
        assert "if" in result.code
        assert "&&" in result.code


# ===== 性能测试 =====

class TestPerformance:
    """测试性能"""
    
    def test_large_number_of_cases(self):
        """测试大量分支"""
        cases = [
            MatchCase(LiteralPattern(i, "INT"))
            for i in range(100)
        ]
        cases.append(MatchCase(WildcardPattern()))
        
        generator = PatternCodeGenerator()
        result = generator.generate_match_expression("x", cases)
        assert result.success
        assert "switch" in result.code
    
    def test_deeply_nested_bindings(self):
        """测试深度嵌套绑定"""
        # 构造深度嵌套的模式
        pattern = VariablePattern("x0")
        for i in range(10):
            pattern = ConstructorPattern(f"Level{i}", [pattern])
        
        bindings = PatternCodeGenerator()._collect_bindings(pattern, "value")
        # 应该能正确处理深度嵌套
        assert len(bindings) == 1


# ===== 边界情况测试 =====

class TestEdgeCases:
    """测试边界情况"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.generator = PatternCodeGenerator()
    
    def test_empty_cases(self):
        """测试空的分支列表"""
        result = self.generator.generate_match_expression("x", [])
        assert result.success
    
    def test_single_wildcard_case(self):
        """测试单个通配符分支"""
        cases = [MatchCase(WildcardPattern())]
        
        result = self.generator.generate_match_expression("x", cases)
        assert result.success
        assert "switch" in result.code
        assert "default:" in result.code
    
    def test_all_wildcard_cases(self):
        """测试所有分支都是通配符"""
        cases = [
            MatchCase(WildcardPattern()),
            MatchCase(WildcardPattern())
        ]
        
        result = self.generator.generate_match_expression("x", cases)
        assert result.success
    
    def test_nested_or_and_patterns(self):
        """测试嵌套的或模式和与模式"""
        pattern = OrPattern([
            AndPattern([
                LiteralPattern(1, "INT"),
                LiteralPattern(2, "INT")
            ]),
            LiteralPattern(3, "INT")
        ])
        
        condition = self.generator._generate_pattern_condition(pattern, "x")
        assert "||" in condition
        assert "&&" in condition


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
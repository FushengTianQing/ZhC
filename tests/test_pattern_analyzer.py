#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模式匹配语义分析器测试 - Pattern Matching Semantic Analyzer Tests

测试语义分析器的各项功能：
1. 类型检查
2. 穷尽性检查
3. 冗余分支检测
4. 变量绑定一致性
5. 守卫表达式分析

Phase 4 - Stage 2 - Task 11.2 Day 2

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

from zhc.semantic.pattern_analyzer import (
    PatternSemanticAnalyzer,
    PatternTypeKind,
    PatternTypeInfo,
    PatternAnalysisResult,
    analyze_match,
    create_enum_type,
    create_struct_type,
    create_tuple_type,
    create_option_type,
    create_primitive_type,
)


# ===== 测试类型系统 =====

class TestPatternTypeInfo:
    """测试类型信息"""
    
    def test_create_primitive_type(self):
        """测试创建基本类型"""
        int_type = create_primitive_type("整数型")
        assert int_type.name == "整数型"
        assert int_type.kind == PatternTypeKind.PRIMITIVE
        assert not int_type.is_enum()
        assert not int_type.is_struct()
    
    def test_create_enum_type(self):
        """测试创建枚举类型"""
        color_type = create_enum_type("颜色", ["红", "绿", "蓝"])
        assert color_type.name == "颜色"
        assert color_type.kind == PatternTypeKind.ENUM
        assert color_type.is_enum()
        assert color_type.constructors == ["红", "绿", "蓝"]
    
    def test_create_struct_type(self):
        """测试创建结构体类型"""
        point_type = create_struct_type("点", {
            "x": create_primitive_type("整数型"),
            "y": create_primitive_type("整数型")
        })
        assert point_type.name == "点"
        assert point_type.kind == PatternTypeKind.STRUCT
        assert point_type.is_struct()
        assert "x" in point_type.fields
        assert "y" in point_type.fields
    
    def test_create_tuple_type(self):
        """测试创建元组类型"""
        tuple_type = create_tuple_type([
            create_primitive_type("整数型"),
            create_primitive_type("字符串型")
        ])
        assert tuple_type.kind == PatternTypeKind.TUPLE
        assert tuple_type.is_tuple()
        assert len(tuple_type.tuple_types) == 2
    
    def test_create_option_type(self):
        """测试创建选项类型"""
        option_type = create_option_type(create_primitive_type("整数型"))
        assert option_type.name == "Option"
        assert option_type.kind == PatternTypeKind.OPTION
        assert option_type.is_option()
        assert option_type.constructors == ["Some", "None"]


# ===== 测试类型检查 =====

class TestTypeChecking:
    """测试类型检查功能"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.analyzer = PatternSemanticAnalyzer()
    
    def test_wildcard_matches_any_type(self):
        """测试通配符匹配任何类型"""
        pattern = WildcardPattern()
        int_type = create_primitive_type("整数型")
        
        result = self.analyzer._check_pattern_type(pattern, int_type)
        assert result.success
    
    def test_variable_binds_type(self):
        """测试变量模式绑定类型"""
        pattern = VariablePattern("x")
        int_type = create_primitive_type("整数型")
        
        result = self.analyzer._check_pattern_type(pattern, int_type)
        assert result.success
        assert "x" in result.bindings
        assert result.bindings["x"] == int_type
    
    def test_literal_pattern_type_check(self):
        """测试字面量模式类型检查"""
        int_type = create_primitive_type("整数型")
        
        # 正确：整数匹配整数型
        pattern1 = LiteralPattern(42, "INT")
        result1 = self.analyzer._check_pattern_type(pattern1, int_type)
        assert result1.success
        
        # 错误：字符串匹配整数型
        pattern2 = LiteralPattern("hello", "STRING")
        result2 = self.analyzer._check_pattern_type(pattern2, int_type)
        assert not result2.success
    
    def test_range_pattern_type_check(self):
        """测试范围模式类型检查"""
        int_type = create_primitive_type("整数型")
        string_type = create_primitive_type("字符串型")
        
        # 正确：范围匹配数值类型
        pattern1 = RangePattern(1, 10)
        result1 = self.analyzer._check_pattern_type(pattern1, int_type)
        assert result1.success
        
        # 错误：范围匹配字符串类型
        pattern2 = RangePattern(1, 10)
        result2 = self.analyzer._check_pattern_type(pattern2, string_type)
        assert not result2.success
    
    def test_constructor_pattern_type_check(self):
        """测试构造器模式类型检查"""
        color_type = create_enum_type("颜色", ["红", "绿", "蓝"])
        int_type = create_primitive_type("整数型")
        
        # 正确：构造器匹配枚举类型
        pattern1 = ConstructorPattern("红")
        result1 = self.analyzer._check_pattern_type(pattern1, color_type)
        assert result1.success
        
        # 错误：构造器匹配基本类型
        pattern2 = ConstructorPattern("红")
        result2 = self.analyzer._check_pattern_type(pattern2, int_type)
        assert not result2.success
        
        # 错误：不存在的构造器
        pattern3 = ConstructorPattern("黄")
        result3 = self.analyzer._check_pattern_type(pattern3, color_type)
        assert not result3.success
    
    def test_destructure_pattern_type_check(self):
        """测试解构模式类型检查"""
        point_type = create_struct_type("点", {
            "x": create_primitive_type("整数型"),
            "y": create_primitive_type("整数型")
        })
        int_type = create_primitive_type("整数型")
        
        # 正确：解构匹配结构体类型
        pattern1 = DestructurePattern("点", {
            "x": VariablePattern("a"),
            "y": VariablePattern("b")
        })
        result1 = self.analyzer._check_pattern_type(pattern1, point_type)
        assert result1.success
        
        # 错误：解构匹配基本类型
        pattern2 = DestructurePattern("点", {"x": VariablePattern("a")})
        result2 = self.analyzer._check_pattern_type(pattern2, int_type)
        assert not result2.success
        
        # 错误：不存在的字段
        pattern3 = DestructurePattern("点", {"z": VariablePattern("c")})
        result3 = self.analyzer._check_pattern_type(pattern3, point_type)
        assert not result3.success
    
    def test_tuple_pattern_type_check(self):
        """测试元组模式类型检查"""
        tuple_type = create_tuple_type([
            create_primitive_type("整数型"),
            create_primitive_type("字符串型")
        ])
        int_type = create_primitive_type("整数型")
        
        # 正确：元组模式匹配元组类型
        pattern1 = TuplePattern([
            VariablePattern("x"),
            VariablePattern("y")
        ])
        result1 = self.analyzer._check_pattern_type(pattern1, tuple_type)
        assert result1.success
        
        # 错误：元组模式匹配基本类型
        pattern2 = TuplePattern([VariablePattern("x")])
        result2 = self.analyzer._check_pattern_type(pattern2, int_type)
        assert not result2.success
        
        # 错误：元组长度不匹配
        pattern3 = TuplePattern([VariablePattern("x")])
        result3 = self.analyzer._check_pattern_type(pattern3, tuple_type)
        assert not result3.success
    
    def test_or_pattern_type_check(self):
        """测试或模式类型检查"""
        int_type = create_primitive_type("整数型")
        
        # 正确：所有分支类型兼容
        pattern1 = OrPattern([
            LiteralPattern(1, "INT"),
            LiteralPattern(2, "INT"),
            LiteralPattern(3, "INT")
        ])
        result1 = self.analyzer._check_pattern_type(pattern1, int_type)
        assert result1.success
    
    def test_and_pattern_type_check(self):
        """测试与模式类型检查"""
        int_type = create_primitive_type("整数型")
        
        # 正确：所有模式类型兼容
        pattern1 = AndPattern([
            VariablePattern("x"),
            RangePattern(1, 10)
        ])
        result1 = self.analyzer._check_pattern_type(pattern1, int_type)
        assert result1.success
    
    def test_guard_pattern_type_check(self):
        """测试守卫模式类型检查"""
        int_type = create_primitive_type("整数型")
        
        # 正确：基础模式类型兼容
        pattern1 = GuardPattern(
            pattern=VariablePattern("x"),
            guard="x > 0"
        )
        result1 = self.analyzer._check_pattern_type(pattern1, int_type)
        assert result1.success
        assert "x" in result1.bindings


# ===== 测试穷尽性检查 =====

class TestExhaustivenessChecking:
    """测试穷尽性检查功能"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.analyzer = PatternSemanticAnalyzer()
    
    def test_wildcard_is_exhaustive(self):
        """测试通配符分支确保穷尽"""
        int_type = create_primitive_type("整数型")
        
        cases = [
            MatchCase(WildcardPattern())
        ]
        
        result = self.analyzer._check_exhaustiveness(cases, int_type)
        assert not result.warnings  # 没有警告
        assert not result.missing_cases
    
    def test_variable_is_exhaustive(self):
        """测试变量分支确保穷尽"""
        int_type = create_primitive_type("整数型")
        
        cases = [
            MatchCase(VariablePattern("x"))
        ]
        
        result = self.analyzer._check_exhaustiveness(cases, int_type)
        assert not result.warnings
    
    def test_enum_missing_constructors(self):
        """测试枚举类型缺少构造器"""
        color_type = create_enum_type("颜色", ["红", "绿", "蓝"])
        
        # 只覆盖部分构造器
        cases = [
            MatchCase(ConstructorPattern("红")),
            MatchCase(ConstructorPattern("绿"))
        ]
        
        result = self.analyzer._check_exhaustiveness(cases, color_type)
        assert len(result.warnings) > 0
        assert "蓝" in result.missing_cases
    
    def test_enum_all_constructors(self):
        """测试枚举类型覆盖所有构造器"""
        color_type = create_enum_type("颜色", ["红", "绿", "蓝"])
        
        # 覆盖所有构造器
        cases = [
            MatchCase(ConstructorPattern("红")),
            MatchCase(ConstructorPattern("绿")),
            MatchCase(ConstructorPattern("蓝"))
        ]
        
        result = self.analyzer._check_exhaustiveness(cases, color_type)
        assert not result.missing_cases
    
    def test_enum_with_or_pattern(self):
        """测试或模式覆盖多个构造器"""
        color_type = create_enum_type("颜色", ["红", "绿", "蓝"])
        
        cases = [
            MatchCase(OrPattern([
                ConstructorPattern("红"),
                ConstructorPattern("绿")
            ])),
            MatchCase(ConstructorPattern("蓝"))
        ]
        
        result = self.analyzer._check_exhaustiveness(cases, color_type)
        assert not result.missing_cases
    
    def test_primitive_missing_wildcard(self):
        """测试基本类型缺少通配符"""
        int_type = create_primitive_type("整数型")
        
        cases = [
            MatchCase(LiteralPattern(1, "INT")),
            MatchCase(LiteralPattern(2, "INT"))
        ]
        
        result = self.analyzer._check_exhaustiveness(cases, int_type)
        assert len(result.warnings) > 0


# ===== 测试冗余检测 =====

class TestRedundancyChecking:
    """测试冗余分支检测功能"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.analyzer = PatternSemanticAnalyzer()
    
    def test_wildcard_covers_all(self):
        """测试通配符覆盖所有后续分支"""
        int_type = create_primitive_type("整数型")
        
        cases = [
            MatchCase(WildcardPattern()),
            MatchCase(LiteralPattern(1, "INT")),  # 冗余
            MatchCase(LiteralPattern(2, "INT"))   # 冗余
        ]
        
        result = self.analyzer._check_redundancy(cases)
        assert 1 in result.unreachable_cases
        assert 2 in result.unreachable_cases
    
    def test_variable_covers_all(self):
        """测试变量模式覆盖所有后续分支"""
        int_type = create_primitive_type("整数型")
        
        cases = [
            MatchCase(VariablePattern("x")),
            MatchCase(LiteralPattern(1, "INT"))  # 冗余
        ]
        
        result = self.analyzer._check_redundancy(cases)
        assert 1 in result.unreachable_cases
    
    def test_literal_redundancy(self):
        """测试字面量模式冗余"""
        int_type = create_primitive_type("整数型")
        
        cases = [
            MatchCase(LiteralPattern(1, "INT")),
            MatchCase(LiteralPattern(1, "INT")),  # 冗余：重复的字面量
            MatchCase(LiteralPattern(2, "INT"))
        ]
        
        result = self.analyzer._check_redundancy(cases)
        assert 1 in result.unreachable_cases
    
    def test_constructor_redundancy(self):
        """测试构造器模式冗余"""
        color_type = create_enum_type("颜色", ["红", "绿", "蓝"])
        
        cases = [
            MatchCase(ConstructorPattern("红")),
            MatchCase(ConstructorPattern("红")),  # 冗余：重复的构造器
            MatchCase(ConstructorPattern("绿"))
        ]
        
        result = self.analyzer._check_redundancy(cases)
        assert 1 in result.unreachable_cases
    
    def test_or_pattern_covers_multiple(self):
        """测试或模式覆盖多个分支"""
        int_type = create_primitive_type("整数型")
        
        cases = [
            MatchCase(OrPattern([
                LiteralPattern(1, "INT"),
                LiteralPattern(2, "INT")
            ])),
            MatchCase(LiteralPattern(1, "INT")),  # 冗余：已被或模式覆盖
            MatchCase(LiteralPattern(3, "INT"))
        ]
        
        result = self.analyzer._check_redundancy(cases)
        assert 1 in result.unreachable_cases
        assert 2 not in result.unreachable_cases  # 3 没有被覆盖


# ===== 测试变量绑定一致性 =====

class TestBindingConsistency:
    """测试变量绑定一致性检查"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.analyzer = PatternSemanticAnalyzer()
    
    def test_consistent_bindings(self):
        """测试一致的变量绑定"""
        cases = [
            MatchCase(ConstructorPattern("Some", [VariablePattern("x")])),
            MatchCase(ConstructorPattern("None"))
        ]
        
        result = self.analyzer._check_binding_consistency(cases)
        # 第一个分支绑定 x，第二个分支不绑定
        # 应该有警告，但不应该失败
        assert result.success
    
    def test_inconsistent_bindings_warning(self):
        """测试不一致的变量绑定产生警告"""
        cases = [
            MatchCase(ConstructorPattern("Some", [VariablePattern("x")])),
            MatchCase(ConstructorPattern("Some", [VariablePattern("y")])),  # 不同的变量名
            MatchCase(ConstructorPattern("None"))
        ]
        
        result = self.analyzer._check_binding_consistency(cases)
        # 应该有警告
        assert len(result.warnings) > 0


# ===== 测试完整的匹配表达式分析 =====

class TestFullMatchAnalysis:
    """测试完整的匹配表达式分析"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.analyzer = PatternSemanticAnalyzer()
    
    def test_successful_analysis(self):
        """测试成功的匹配分析"""
        color_type = create_enum_type("颜色", ["红", "绿", "蓝"])
        
        cases = [
            MatchCase(ConstructorPattern("红")),
            MatchCase(ConstructorPattern("绿")),
            MatchCase(ConstructorPattern("蓝"))
        ]
        
        result = self.analyzer.analyze_match_expression(cases, color_type)
        assert result.success
        assert not result.errors
    
    def test_analysis_with_type_errors(self):
        """测试带类型错误的分析"""
        int_type = create_primitive_type("整数型")
        
        cases = [
            MatchCase(LiteralPattern("hello", "STRING")),  # 类型错误
            MatchCase(LiteralPattern(42, "INT"))
        ]
        
        result = self.analyzer.analyze_match_expression(cases, int_type)
        assert not result.success
        assert len(result.errors) > 0
    
    def test_analysis_with_warnings(self):
        """测试带警告的分析"""
        int_type = create_primitive_type("整数型")
        
        cases = [
            MatchCase(LiteralPattern(1, "INT")),
            MatchCase(LiteralPattern(2, "INT"))
        ]
        
        result = self.analyzer.analyze_match_expression(cases, int_type)
        # 应该有穷尽性警告
        assert len(result.warnings) > 0
    
    def test_analysis_with_redundancy(self):
        """测试带冗余分支的分析"""
        int_type = create_primitive_type("整数型")
        
        cases = [
            MatchCase(WildcardPattern()),
            MatchCase(LiteralPattern(1, "INT"))  # 冗余
        ]
        
        result = self.analyzer.analyze_match_expression(cases, int_type)
        assert result.success
        assert 1 in result.unreachable_cases
    
    def test_option_type_analysis(self):
        """测试选项类型分析"""
        option_type = create_option_type(create_primitive_type("整数型"))
        
        cases = [
            MatchCase(ConstructorPattern("Some", [VariablePattern("x")])),
            MatchCase(ConstructorPattern("None"))
        ]
        
        result = self.analyzer.analyze_match_expression(cases, option_type)
        assert result.success
        assert not result.missing_cases


# ===== 测试辅助函数 =====

class TestHelperFunctions:
    """测试辅助函数"""
    
    def test_analyze_match_function(self):
        """测试 analyze_match 便捷函数"""
        color_type = create_enum_type("颜色", ["红", "绿", "蓝"])
        
        cases = [
            MatchCase(ConstructorPattern("红")),
            MatchCase(ConstructorPattern("绿")),
            MatchCase(ConstructorPattern("蓝"))
        ]
        
        result = analyze_match(cases, color_type)
        assert result.success
        assert isinstance(result, PatternAnalysisResult)
    
    def test_create_enum_type_helper(self):
        """测试 create_enum_type 辅助函数"""
        enum_type = create_enum_type("选项", ["Some", "None"])
        assert enum_type.name == "选项"
        assert enum_type.constructors == ["Some", "None"]
        assert enum_type.is_enum()
    
    def test_create_struct_type_helper(self):
        """测试 create_struct_type 辅助函数"""
        struct_type = create_struct_type("点", {
            "x": create_primitive_type("整数型"),
            "y": create_primitive_type("整数型")
        })
        assert struct_type.name == "点"
        assert struct_type.is_struct()
        assert "x" in struct_type.fields
    
    def test_create_tuple_type_helper(self):
        """测试 create_tuple_type 辅助函数"""
        tuple_type = create_tuple_type([
            create_primitive_type("整数型"),
            create_primitive_type("字符串型")
        ])
        assert tuple_type.is_tuple()
        assert len(tuple_type.tuple_types) == 2
    
    def test_create_option_type_helper(self):
        """测试 create_option_type 辅助函数"""
        option_type = create_option_type(create_primitive_type("整数型"))
        assert option_type.is_option()
        assert "Some" in option_type.constructors
        assert "None" in option_type.constructors


# ===== 测试复杂场景 =====

class TestComplexScenarios:
    """测试复杂的匹配场景"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.analyzer = PatternSemanticAnalyzer()
    
    def test_nested_pattern_analysis(self):
        """测试嵌套模式分析"""
        # 定义嵌套类型：Option<(整数, 字符串)>
        inner_tuple = create_tuple_type([
            create_primitive_type("整数型"),
            create_primitive_type("字符串型")
        ])
        option_type = create_option_type(inner_tuple)
        
        cases = [
            MatchCase(ConstructorPattern("Some", [
                TuplePattern([
                    VariablePattern("n"),
                    VariablePattern("s")
                ])
            ])),
            MatchCase(ConstructorPattern("None"))
        ]
        
        result = self.analyzer.analyze_match_expression(cases, option_type)
        assert result.success
    
    def test_guard_pattern_analysis(self):
        """测试守卫模式分析"""
        int_type = create_primitive_type("整数型")
        
        cases = [
            MatchCase(GuardPattern(
                pattern=VariablePattern("x"),
                guard="x > 0"
            )),
            MatchCase(VariablePattern("x"))
        ]
        
        result = self.analyzer.analyze_match_expression(cases, int_type)
        assert result.success
    
    def test_mixed_pattern_types(self):
        """测试混合模式类型"""
        int_type = create_primitive_type("整数型")
        
        cases = [
            MatchCase(LiteralPattern(0, "INT")),
            MatchCase(RangePattern(1, 10)),
            MatchCase(RangePattern(11, 20)),
            MatchCase(VariablePattern("x"))  # 兜底
        ]
        
        result = self.analyzer.analyze_match_expression(cases, int_type)
        assert result.success
        assert not result.missing_cases
    
    def test_deeply_nested_destructure(self):
        """测试深度嵌套的解构"""
        # 定义嵌套结构体：矩形 { 左上: 点, 右下: 点 }
        point_type = create_struct_type("点", {
            "x": create_primitive_type("整数型"),
            "y": create_primitive_type("整数型")
        })
        rect_type = create_struct_type("矩形", {
            "左上": point_type,
            "右下": point_type
        })
        
        cases = [
            MatchCase(DestructurePattern("矩形", {
                "左上": DestructurePattern("点", {
                    "x": VariablePattern("x1"),
                    "y": VariablePattern("y1")
                }),
                "右下": DestructurePattern("点", {
                    "x": VariablePattern("x2"),
                    "y": VariablePattern("y2")
                })
            }))
        ]
        
        result = self.analyzer.analyze_match_expression(cases, rect_type)
        assert result.success


# ===== 性能测试 =====

class TestPerformance:
    """测试性能"""
    
    def test_large_enum_exhaustiveness(self):
        """测试大型枚举的穷尽性检查"""
        # 创建有 100 个构造器的枚举
        constructors = [f"C{i}" for i in range(100)]
        large_enum = create_enum_type("大枚举", constructors)
        
        # 覆盖所有构造器
        cases = [
            MatchCase(ConstructorPattern(c))
            for c in constructors
        ]
        
        analyzer = PatternSemanticAnalyzer()
        result = analyzer._check_exhaustiveness(cases, large_enum)
        assert not result.missing_cases
    
    def test_many_redundant_cases(self):
        """测试大量冗余分支的检测"""
        int_type = create_primitive_type("整数型")
        
        # 第一个是通配符，后面 100 个都是冗余的
        cases = [MatchCase(WildcardPattern())]
        cases.extend([
            MatchCase(LiteralPattern(i, "INT"))
            for i in range(100)
        ])
        
        analyzer = PatternSemanticAnalyzer()
        result = analyzer._check_redundancy(cases)
        # 所有后续分支都应该是冗余的
        assert len(result.unreachable_cases) == 100


# ===== 边界情况测试 =====

class TestEdgeCases:
    """测试边界情况"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.analyzer = PatternSemanticAnalyzer()
    
    def test_empty_cases(self):
        """测试空的匹配分支列表"""
        int_type = create_primitive_type("整数型")
        
        result = self.analyzer.analyze_match_expression([], int_type)
        assert result.success  # 空列表是合法的
        assert len(result.warnings) > 0  # 但应该有警告
    
    def test_single_wildcard_case(self):
        """测试单个通配符分支"""
        int_type = create_primitive_type("整数型")
        
        cases = [MatchCase(WildcardPattern())]
        
        result = self.analyzer.analyze_match_expression(cases, int_type)
        assert result.success
        assert not result.warnings
    
    def test_unknown_type(self):
        """测试未知类型"""
        unknown_type = PatternTypeInfo("unknown", PatternTypeKind.UNKNOWN)
        
        cases = [MatchCase(VariablePattern("x"))]
        
        result = self.analyzer.analyze_match_expression(cases, unknown_type)
        assert result.success
    
    def test_nested_or_and_patterns(self):
        """测试嵌套的或模式和与模式"""
        int_type = create_primitive_type("整数型")
        
        # (1 | 2) & (2 | 3)
        pattern = AndPattern([
            OrPattern([
                LiteralPattern(1, "INT"),
                LiteralPattern(2, "INT")
            ]),
            OrPattern([
                LiteralPattern(2, "INT"),
                LiteralPattern(3, "INT")
            ])
        ])
        
        cases = [MatchCase(pattern)]
        
        result = self.analyzer.analyze_match_expression(cases, int_type)
        assert result.success


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

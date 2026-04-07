#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模式匹配语法解析器测试

作者: 阿福
日期: 2026-04-08
"""

import pytest
from zhc.semantic.pattern_parser import (
    PatternParser,
    PatternParserError,
    parse_pattern_from_string,
)
from zhc.semantic.pattern_matching import (
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
    PatternType,
)


class TestPatternParser:
    """模式匹配解析器测试"""
    
    def test_wildcard_pattern(self):
        """测试通配符模式"""
        pattern = parse_pattern_from_string("_")
        assert isinstance(pattern, WildcardPattern)
    
    def test_variable_pattern(self):
        """测试变量模式"""
        pattern = parse_pattern_from_string("x")
        assert isinstance(pattern, VariablePattern)
        assert pattern.name == "x"
    
    def test_int_literal_pattern(self):
        """测试整数字面量模式"""
        pattern = parse_pattern_from_string("42")
        assert isinstance(pattern, LiteralPattern)
        assert pattern.value == 42
    
    def test_string_literal_pattern(self):
        """测试字符串字面量模式"""
        pattern = parse_pattern_from_string('"hello"')
        assert isinstance(pattern, LiteralPattern)
        assert pattern.value == "hello"
    
    def test_bool_literal_pattern(self):
        """测试布尔字面量模式"""
        pattern = parse_pattern_from_string("真")
        assert isinstance(pattern, LiteralPattern)
        assert pattern.value is True
        
        pattern = parse_pattern_from_string("假")
        assert isinstance(pattern, LiteralPattern)
        assert pattern.value is False
    
    def test_range_pattern(self):
        """测试范围模式"""
        pattern = parse_pattern_from_string("1..10")
        assert isinstance(pattern, RangePattern)
        assert pattern.start == 1
        assert pattern.end == 10
        assert pattern.inclusive is True
    
    def test_tuple_pattern(self):
        """测试元组模式"""
        pattern = parse_pattern_from_string("(x, y)")
        assert isinstance(pattern, TuplePattern)
        assert len(pattern.patterns) == 2
        assert isinstance(pattern.patterns[0], VariablePattern)
        assert isinstance(pattern.patterns[1], VariablePattern)
    
    def test_empty_tuple_pattern(self):
        """测试空元组模式"""
        pattern = parse_pattern_from_string("()")
        assert isinstance(pattern, TuplePattern)
        assert len(pattern.patterns) == 0
    
    def test_constructor_pattern(self):
        """测试构造器模式"""
        pattern = parse_pattern_from_string("Some(x)")
        assert isinstance(pattern, ConstructorPattern)
        assert pattern.constructor == "Some"
        assert len(pattern.patterns) == 1
        assert isinstance(pattern.patterns[0], VariablePattern)
    
    def test_constructor_pattern_no_args(self):
        """测试无参数构造器模式"""
        # 注意：无参数标识符（如 None）在词法层面无法区分是变量还是构造器
        # 默认解析为变量模式，语义分析器会根据上下文判断
        pattern = parse_pattern_from_string("None")
        assert isinstance(pattern, VariablePattern)
        assert pattern.name == "None"
        # 语义分析器会根据类型信息将其识别为构造器
    
    def test_constructor_pattern_multiple_args(self):
        """测试多参数构造器模式"""
        pattern = parse_pattern_from_string("点(x, y)")
        assert isinstance(pattern, ConstructorPattern)
        assert pattern.constructor == "点"
        assert len(pattern.patterns) == 2
    
    def test_destructure_pattern(self):
        """测试解构模式"""
        pattern = parse_pattern_from_string("点{x: x, y: y}")
        assert isinstance(pattern, DestructurePattern)
        assert pattern.struct_name == "点"
        assert len(pattern.fields) == 2
        assert "x" in pattern.fields
        assert "y" in pattern.fields
    
    def test_destructure_pattern_shorthand(self):
        """测试简化解构模式"""
        pattern = parse_pattern_from_string("点{x, y}")
        assert isinstance(pattern, DestructurePattern)
        assert pattern.struct_name == "点"
        # 简化形式中，字段名作为变量名
        assert len(pattern.fields) == 2
    
    def test_or_pattern(self):
        """测试或模式"""
        pattern = parse_pattern_from_string("x | y")
        assert isinstance(pattern, OrPattern)
        assert len(pattern.patterns) == 2
        assert isinstance(pattern.patterns[0], VariablePattern)
        assert isinstance(pattern.patterns[1], VariablePattern)
    
    def test_or_pattern_multiple(self):
        """测试多重或模式"""
        pattern = parse_pattern_from_string("a | b | c")
        assert isinstance(pattern, OrPattern)
        # OrPattern 会被解析为左结合
        assert isinstance(pattern.patterns[0], OrPattern)
        assert isinstance(pattern.patterns[1], VariablePattern)
    
    def test_and_pattern(self):
        """测试与模式"""
        pattern = parse_pattern_from_string("x & y")
        assert isinstance(pattern, AndPattern)
        assert len(pattern.patterns) == 2
        assert isinstance(pattern.patterns[0], VariablePattern)
        assert isinstance(pattern.patterns[1], VariablePattern)
    
    def test_and_pattern_multiple(self):
        """测试多重与模式"""
        pattern = parse_pattern_from_string("a & b & c")
        assert isinstance(pattern, AndPattern)
        assert isinstance(pattern.patterns[0], AndPattern)
        assert isinstance(pattern.patterns[1], VariablePattern)
    
    def test_guard_pattern(self):
        """测试守卫模式"""
        pattern = parse_pattern_from_string("x 当 x > 0")
        assert isinstance(pattern, GuardPattern)
        assert isinstance(pattern.pattern, VariablePattern)
        assert "x > 0" in pattern.guard
    
    def test_guard_pattern_with_literal(self):
        """测试字面量守卫模式"""
        pattern = parse_pattern_from_string("42 当 x > 10")
        assert isinstance(pattern, GuardPattern)
        assert isinstance(pattern.pattern, LiteralPattern)
    
    def test_complex_pattern(self):
        """测试复杂模式"""
        pattern = parse_pattern_from_string("(Some(x), 1..10)")
        assert isinstance(pattern, TuplePattern)
        assert len(pattern.patterns) == 2
        assert isinstance(pattern.patterns[0], ConstructorPattern)
        assert isinstance(pattern.patterns[1], RangePattern)
    
    def test_nested_or_pattern(self):
        """测试嵌套或模式"""
        pattern = parse_pattern_from_string("(x | y)")
        assert isinstance(pattern, TuplePattern)
        assert isinstance(pattern.patterns[0], OrPattern)
    
    def test_error_unexpected_token(self):
        """测试意外 Token 错误"""
        with pytest.raises(PatternParserError):
            parse_pattern_from_string("+")
    
    def test_error_range_without_end(self):
        """测试范围模式缺少结束值"""
        # 注意：词法分析器会将 "1.." 解析为 INT_LITERAL 和 DOTDOT
        # 解析器会期望下一个 Token 是 INT_LITERAL，但到达文件末尾
        with pytest.raises(PatternParserError):
            parse_pattern_from_string("1..")
    
    def test_error_unclosed_paren(self):
        """测试未闭合括号"""
        with pytest.raises(PatternParserError):
            parse_pattern_from_string("(x")
    
    def test_error_unclosed_brace(self):
        """测试未闭合大括号"""
        with pytest.raises(PatternParserError):
            parse_pattern_from_string("点{x")
    
    def test_constructor_with_named_fields(self):
        """测试带命名字段的构造器"""
        # 注意：构造器模式不支持命名字段语法（Some(value: x))
        # 命名字段语法用于解构模式（点{x: y})
        # 这里测试解构模式
        pattern = parse_pattern_from_string("Some{x: value}")
        assert isinstance(pattern, DestructurePattern)
        assert pattern.struct_name == "Some"


class TestPatternParserIntegration:
    """模式匹配解析器集成测试"""
    
    def test_match_expression_patterns(self):
        """测试匹配表达式中的模式"""
        # 模拟匹配表达式的多个分支
        patterns = [
            parse_pattern_from_string("0"),
            parse_pattern_from_string("1..10"),
            parse_pattern_from_string("11..100"),
            parse_pattern_from_string("_"),
        ]
        
        assert len(patterns) == 4
        assert isinstance(patterns[0], LiteralPattern)
        assert isinstance(patterns[1], RangePattern)
        assert isinstance(patterns[2], RangePattern)
        assert isinstance(patterns[3], WildcardPattern)
    
    def test_option_type_patterns(self):
        """测试选项类型模式"""
        none_pattern = parse_pattern_from_string("None")
        some_pattern = parse_pattern_from_string("Some(x)")
        
        # 注意：None 在词法层面被解析为变量模式
        # 语义分析器会根据上下文将其识别为构造器
        assert isinstance(none_pattern, VariablePattern)
        assert none_pattern.name == "None"
        
        assert isinstance(some_pattern, ConstructorPattern)
        assert some_pattern.constructor == "Some"
    
    def test_list_patterns(self):
        """测试列表模式"""
        # 空列表
        empty = parse_pattern_from_string("空列表()")
        assert isinstance(empty, ConstructorPattern)
        
        # 单元素列表
        single = parse_pattern_from_string("单元素(x)")
        assert isinstance(single, ConstructorPattern)
        
        # 双元素列表
        double = parse_pattern_from_string("双元素(x, y)")
        assert isinstance(double, ConstructorPattern)
    
    def test_tree_node_patterns(self):
        """测试树节点模式"""
        # 叶子节点
        leaf = parse_pattern_from_string("叶子(value)")
        assert isinstance(leaf, ConstructorPattern)
        
        # 内部节点
        node = parse_pattern_from_string("节点(left, right)")
        assert isinstance(node, ConstructorPattern)
    
    def test_guard_with_complex_condition(self):
        """测试复杂守卫条件"""
        pattern = parse_pattern_from_string("x 当 x > 0 且 x < 100")
        assert isinstance(pattern, GuardPattern)
        assert "x > 0" in pattern.guard
        assert "且" in pattern.guard


class TestPatternParserPerformance:
    """模式匹配解析器性能测试"""
    
    def test_parse_many_patterns(self):
        """测试解析大量模式"""
        import time
        
        patterns = [
            "x",
            "42",
            "1..100",
            "(x, y, z)",
            "Some(x)",
            "点{a: x, b: y, c: z}",
            "x | y | z | w",
            "a & b & c",
            "x 当 x > 0",
        ]
        
        start = time.time()
        for _ in range(100):
            for pattern_str in patterns:
                parse_pattern_from_string(pattern_str)
        elapsed = time.time() - start
        
        # 应该在合理时间内完成
        assert elapsed < 5.0, f"性能测试失败: {elapsed:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

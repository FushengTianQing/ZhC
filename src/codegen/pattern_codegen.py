#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模式匹配代码生成器 - Pattern Matching Code Generator

将模式匹配表达式转换为 C 代码：
1. 匹配表达式转换为 switch/if-else 链
2. 模式匹配转换为条件判断和变量绑定
3. 支持所有 9 种模式类型

Phase 4 - Stage 2 - Task 11.2 Day 3

作者：ZHC 开发团队
日期：2026-04-08
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field

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


# ===== 代码生成结果 =====

@dataclass
class PatternCodeResult:
    """模式代码生成结果"""
    code: str                    # 生成的 C 代码
    bindings: Dict[str, str]     # 变量绑定（变量名 -> C 表达式）
    temp_vars: List[str]         # 临时变量列表
    success: bool = True         # 是否成功
    errors: List[str] = field(default_factory=list)


# ===== 模式匹配代码生成器 =====

class PatternCodeGenerator:
    """模式匹配代码生成器
    
    将模式匹配表达式转换为 C 代码
    
    策略：
    1. 构造器模式 → switch 语句
    2. 字面量模式 → if 条件判断
    3. 范围模式 → if 范围判断
    4. 解构模式 → 字段访问 + 递归匹配
    5. 元组模式 → 元素访问 + 递归匹配
    6. 或模式 → 多个条件判断
    7. 与模式 → 多个条件判断
    8. 守卫模式 → 模式匹配 + 守卫条件
    """
    
    def __init__(self):
        self.temp_counter = 0
        self.indent_level = 0
    
    def generate_match_expression(
        self,
        value_expr: str,
        cases: List[MatchCase],
        value_type: Optional[str] = None
    ) -> PatternCodeResult:
        """生成匹配表达式代码
        
        Args:
            value_expr: 被匹配值的 C 表达式
            cases: 匹配分支列表
            value_type: 被匹配值的类型（可选）
            
        Returns:
            代码生成结果
        """
        result = PatternCodeResult(code="", bindings={}, temp_vars=[])
        
        # 生成匹配代码
        code_lines = []
        indent = "  " * self.indent_level
        
        # 检查是否可以使用 switch 语句
        if self._can_use_switch(cases):
            code_lines.append(self._generate_switch_match(value_expr, cases))
        else:
            code_lines.append(self._generate_if_else_match(value_expr, cases))
        
        result.code = indent + "\n".join(code_lines)
        return result
    
    def _can_use_switch(self, cases: List[MatchCase]) -> bool:
        """检查是否可以使用 switch 语句
        
        条件：
        1. 所有分支都是字面量模式或构造器模式
        2. 没有守卫表达式
        3. 最后一个分支可以是通配符（作为 default）
        """
        for i, case in enumerate(cases):
            if isinstance(case.pattern, GuardPattern):
                return False
            
            # 最后一个分支可以是通配符
            if i == len(cases) - 1 and isinstance(case.pattern, WildcardPattern):
                continue
            
            if not (isinstance(case.pattern, LiteralPattern) or 
                    isinstance(case.pattern, ConstructorPattern) or
                    isinstance(case.pattern, OrPattern)):
                return False
            
            # 或模式的所有分支必须是字面量或构造器
            if isinstance(case.pattern, OrPattern):
                for sub_pattern in case.pattern.patterns:
                    if not (isinstance(sub_pattern, LiteralPattern) or 
                            isinstance(sub_pattern, ConstructorPattern)):
                        return False
        
        return True
    
    def _generate_switch_match(
        self,
        value_expr: str,
        cases: List[MatchCase]
    ) -> str:
        """生成 switch 语句匹配代码"""
        indent = "  " * self.indent_level
        inner_indent = "  " * (self.indent_level + 1)
        
        code_lines = [f"switch ({value_expr}) {{"]
        
        for case in cases:
            case_code = self._generate_switch_case(case)
            code_lines.append(inner_indent + case_code)
        
        code_lines.append(indent + "}")
        return "\n".join(code_lines)
    
    def _generate_switch_case(self, case: MatchCase) -> str:
        """生成 switch 分支代码"""
        indent = "  " * self.indent_level
        inner_indent = "  " * (self.indent_level + 1)
        
        pattern = case.pattern
        
        # 处理或模式
        if isinstance(pattern, OrPattern):
            # 多个 case 标签
            case_labels = []
            for sub_pattern in pattern.patterns:
                if isinstance(sub_pattern, LiteralPattern):
                    case_labels.append(f"case {sub_pattern.value}:")
                elif isinstance(sub_pattern, ConstructorPattern):
                    case_labels.append(f"case {sub_pattern.constructor}:")
            
            code_lines = ["\n".join(case_labels)]
            code_lines.append(inner_indent + "{")
            
            # 生成分支体
            body_code = self._generate_case_body(case)
            code_lines.append(inner_indent + "  " + body_code)
            code_lines.append(inner_indent + "  break;")
            code_lines.append(inner_indent + "}")
            
            return "\n".join(code_lines)
        
        # 单个模式
        if isinstance(pattern, LiteralPattern):
            code_lines = [f"case {pattern.value}:"]
        elif isinstance(pattern, ConstructorPattern):
            code_lines = [f"case {pattern.constructor}:"]
        else:
            # 默认分支
            code_lines = ["default:"]
        
        code_lines.append(inner_indent + "{")
        
        # 生成变量绑定
        bindings_code = self._generate_pattern_bindings(pattern, "matched_value")
        if bindings_code:
            code_lines.append(inner_indent + "  " + bindings_code)
        
        # 生成分支体
        body_code = self._generate_case_body(case)
        code_lines.append(inner_indent + "  " + body_code)
        
        code_lines.append(inner_indent + "  break;")
        code_lines.append(inner_indent + "}")
        
        return "\n".join(code_lines)
    
    def _generate_if_else_match(
        self,
        value_expr: str,
        cases: List[MatchCase]
    ) -> str:
        """生成 if-else 链匹配代码"""
        indent = "  " * self.indent_level
        inner_indent = "  " * (self.indent_level + 1)
        
        code_lines = []
        
        for i, case in enumerate(cases):
            # 生成条件判断
            condition = self._generate_pattern_condition(case.pattern, value_expr)
            
            if i == 0:
                code_lines.append(f"if ({condition}) {{")
            else:
                code_lines.append(indent + f"else if ({condition}) {{")
            
            # 生成变量绑定
            bindings_code = self._generate_pattern_bindings(case.pattern, value_expr)
            if bindings_code:
                code_lines.append(inner_indent + bindings_code)
            
            # 生成分支体
            body_code = self._generate_case_body(case)
            code_lines.append(inner_indent + body_code)
            
            code_lines.append(indent + "}")
        
        # 添加默认分支（可选）
        code_lines.append(indent + "else {")
        code_lines.append(inner_indent + "// 未匹配的情况")
        code_lines.append(indent + "}")
        
        return "\n".join(code_lines)
    
    def _generate_pattern_condition(
        self,
        pattern: Pattern,
        value_expr: str
    ) -> str:
        """生成模式匹配条件
        
        Args:
            pattern: 模式
            value_expr: 值表达式
            
        Returns:
            C 条件表达式
        """
        if isinstance(pattern, WildcardPattern):
            return "1"  # 总是匹配
        
        elif isinstance(pattern, VariablePattern):
            return "1"  # 总是匹配
        
        elif isinstance(pattern, LiteralPattern):
            return f"{value_expr} == {pattern.value}"
        
        elif isinstance(pattern, RangePattern):
            if pattern.inclusive:
                return f"{value_expr} >= {pattern.start} && {value_expr} <= {pattern.end}"
            else:
                return f"{value_expr} >= {pattern.start} && {value_expr} < {pattern.end}"
        
        elif isinstance(pattern, ConstructorPattern):
            # 检查构造器类型
            condition = f"{value_expr}._tag == {pattern.constructor}"
            
            # 递归检查子模式
            for i, sub_pattern in enumerate(pattern.patterns):
                if not isinstance(sub_pattern, WildcardPattern):
                    field_expr = f"{value_expr}._fields[{i}]"
                    sub_condition = self._generate_pattern_condition(sub_pattern, field_expr)
                    condition = f"{condition} && {sub_condition}"
            
            return condition
        
        elif isinstance(pattern, DestructurePattern):
            # 检查结构体类型
            condition = f"{value_expr}._type == {pattern.struct_name}"
            
            # 递归检查字段模式
            for field_name, field_pattern in pattern.fields.items():
                if not isinstance(field_pattern, WildcardPattern):
                    field_expr = f"{value_expr}.{field_name}"
                    sub_condition = self._generate_pattern_condition(field_pattern, field_expr)
                    condition = f"{condition} && {sub_condition}"
            
            return condition
        
        elif isinstance(pattern, TuplePattern):
            # 检查元组长度
            condition = f"{value_expr}.length == {len(pattern.patterns)}"
            
            # 递归检查元素模式
            for i, elem_pattern in enumerate(pattern.patterns):
                if not isinstance(elem_pattern, WildcardPattern):
                    elem_expr = f"{value_expr}.elements[{i}]"
                    sub_condition = self._generate_pattern_condition(elem_pattern, elem_expr)
                    condition = f"{condition} && {sub_condition}"
            
            return condition
        
        elif isinstance(pattern, OrPattern):
            # 生成多个条件，用 || 连接
            conditions = []
            for sub_pattern in pattern.patterns:
                sub_condition = self._generate_pattern_condition(sub_pattern, value_expr)
                conditions.append(sub_condition)
            
            return "(" + " || ".join(conditions) + ")"
        
        elif isinstance(pattern, AndPattern):
            # 生成多个条件，用 && 连接
            conditions = []
            for sub_pattern in pattern.patterns:
                sub_condition = self._generate_pattern_condition(sub_pattern, value_expr)
                conditions.append(sub_condition)
            
            return "(" + " && ".join(conditions) + ")"
        
        elif isinstance(pattern, GuardPattern):
            # 先匹配基础模式，再检查守卫
            base_condition = self._generate_pattern_condition(pattern.pattern, value_expr)
            guard_condition = pattern.guard  # TODO: 实际的守卫表达式转换
            
            return f"{base_condition} && ({guard_condition})"
        
        else:
            return "1"  # 默认总是匹配
    
    def _generate_pattern_bindings(
        self,
        pattern: Pattern,
        value_expr: str
    ) -> str:
        """生成模式变量绑定代码
        
        Args:
            pattern: 模式
            value_expr: 值表达式
            
        Returns:
            C 变量绑定代码
        """
        bindings = self._collect_bindings(pattern, value_expr)
        
        if not bindings:
            return ""
        
        code_lines = []
        for var_name, expr in bindings.items():
            code_lines.append(f"auto {var_name} = {expr};")
        
        return "\n".join(code_lines)
    
    def _collect_bindings(
        self,
        pattern: Pattern,
        value_expr: str
    ) -> Dict[str, str]:
        """收集模式中的变量绑定
        
        Args:
            pattern: 模式
            value_expr: 值表达式
            
        Returns:
            变量名到表达式的映射
        """
        bindings = {}
        
        if isinstance(pattern, VariablePattern):
            bindings[pattern.name] = value_expr
        
        elif isinstance(pattern, ConstructorPattern):
            for i, sub_pattern in enumerate(pattern.patterns):
                field_expr = f"{value_expr}._fields[{i}]"
                sub_bindings = self._collect_bindings(sub_pattern, field_expr)
                bindings.update(sub_bindings)
        
        elif isinstance(pattern, DestructurePattern):
            for field_name, field_pattern in pattern.fields.items():
                field_expr = f"{value_expr}.{field_name}"
                sub_bindings = self._collect_bindings(field_pattern, field_expr)
                bindings.update(sub_bindings)
        
        elif isinstance(pattern, TuplePattern):
            for i, elem_pattern in enumerate(pattern.patterns):
                elem_expr = f"{value_expr}.elements[{i}]"
                sub_bindings = self._collect_bindings(elem_pattern, elem_expr)
                bindings.update(sub_bindings)
        
        elif isinstance(pattern, OrPattern):
            # 或模式：所有分支绑定相同的变量
            # 使用第一个分支的绑定
            if pattern.patterns:
                bindings = self._collect_bindings(pattern.patterns[0], value_expr)
        
        elif isinstance(pattern, AndPattern):
            # 与模式：收集所有模式的绑定
            for sub_pattern in pattern.patterns:
                sub_bindings = self._collect_bindings(sub_pattern, value_expr)
                bindings.update(sub_bindings)
        
        elif isinstance(pattern, GuardPattern):
            # 守卫模式：收集基础模式的绑定
            bindings = self._collect_bindings(pattern.pattern, value_expr)
        
        return bindings
    
    def _generate_case_body(self, case: MatchCase) -> str:
        """生成匹配分支体
        
        Args:
            case: 匹配分支
            
        Returns:
            C 代码
        """
        # TODO: 实际的分支体生成
        # 这里需要访问 AST 来生成实际的代码
        return "// 分支体代码"
    
    def generate_pattern_check(
        self,
        pattern: Pattern,
        value_expr: str
    ) -> PatternCodeResult:
        """生成单个模式的检查代码
        
        Args:
            pattern: 模式
            value_expr: 值表达式
            
        Returns:
            代码生成结果
        """
        result = PatternCodeResult(code="", bindings={}, temp_vars=[])
        
        # 生成条件
        condition = self._generate_pattern_condition(pattern, value_expr)
        result.code = condition
        
        # 收集绑定
        result.bindings = self._collect_bindings(pattern, value_expr)
        
        return result
    
    def generate_nested_match(
        self,
        outer_pattern: Pattern,
        inner_patterns: List[Pattern],
        value_expr: str
    ) -> PatternCodeResult:
        """生成嵌套匹配代码
        
        Args:
            outer_pattern: 外层模式
            inner_patterns: 内层模式列表
            value_expr: 值表达式
            
        Returns:
            代码生成结果
        """
        result = PatternCodeResult(code="", bindings={}, temp_vars=[])
        
        indent = "  " * self.indent_level
        
        # 生成外层匹配
        outer_condition = self._generate_pattern_condition(outer_pattern, value_expr)
        
        code_lines = [f"if ({outer_condition}) {{"]
        
        # 生成外层绑定
        outer_bindings = self._generate_pattern_bindings(outer_pattern, value_expr)
        if outer_bindings:
            code_lines.append(indent + outer_bindings)
        
        # 生成内层匹配
        self.indent_level += 1
        for i, inner_pattern in enumerate(inner_patterns):
            temp_var = f"_temp_{self.temp_counter}"
            self.temp_counter += 1
            result.temp_vars.append(temp_var)
            
            # TODO: 实际的内层值表达式
            inner_value = f"{value_expr}._inner_{i}"
            
            inner_condition = self._generate_pattern_condition(inner_pattern, inner_value)
            code_lines.append(indent + f"if ({inner_condition}) {{")
            
            inner_bindings = self._generate_pattern_bindings(inner_pattern, inner_value)
            if inner_bindings:
                code_lines.append(indent + inner_bindings)
            
            code_lines.append(indent + "}")
        
        self.indent_level -= 1
        code_lines.append(indent + "}")
        
        result.code = "\n".join(code_lines)
        return result


# ===== 辅助函数 =====

def generate_match_code(
    value_expr: str,
    cases: List[MatchCase],
    value_type: Optional[str] = None
) -> PatternCodeResult:
    """生成匹配表达式代码的便捷函数"""
    generator = PatternCodeGenerator()
    return generator.generate_match_expression(value_expr, cases, value_type)


def generate_pattern_condition(pattern: Pattern, value_expr: str) -> str:
    """生成模式条件表达式的便捷函数"""
    generator = PatternCodeGenerator()
    return generator._generate_pattern_condition(pattern, value_expr)


def generate_pattern_bindings(pattern: Pattern, value_expr: str) -> str:
    """生成模式变量绑定的便捷函数"""
    generator = PatternCodeGenerator()
    return generator._generate_pattern_bindings(pattern, value_expr)


# ===== 示例用法 =====

if __name__ == "__main__":
    print("=" * 70)
    print("模式匹配代码生成器测试")
    print("=" * 70)
    
    generator = PatternCodeGenerator()
    
    # 测试 1: 字面量模式
    print("\n测试 1: 字面量模式")
    cases = [
        MatchCase(LiteralPattern(1, "INT")),
        MatchCase(LiteralPattern(2, "INT")),
        MatchCase(WildcardPattern())
    ]
    result = generator.generate_match_expression("x", cases)
    print(f"  代码:\n{result.code}")
    
    # 测试 2: 构造器模式
    print("\n测试 2: 构造器模式")
    cases = [
        MatchCase(ConstructorPattern("Some", [VariablePattern("x")])),
        MatchCase(ConstructorPattern("None"))
    ]
    result = generator.generate_match_expression("opt", cases)
    print(f"  代码:\n{result.code}")
    
    # 测试 3: 范围模式
    print("\n测试 3: 范围模式")
    cases = [
        MatchCase(RangePattern(1, 10)),
        MatchCase(RangePattern(11, 20)),
        MatchCase(WildcardPattern())
    ]
    result = generator.generate_match_expression("n", cases)
    print(f"  代码:\n{result.code}")
    
    # 测试 4: 解构模式
    print("\n测试 4: 解构模式")
    cases = [
        MatchCase(DestructurePattern("Point", {
            "x": VariablePattern("px"),
            "y": VariablePattern("py")
        }))
    ]
    result = generator.generate_match_expression("point", cases)
    print(f"  代码:\n{result.code}")
    print(f"  绑定: {result.bindings}")
    
    # 测试 5: 元组模式
    print("\n测试 5: 元组模式")
    cases = [
        MatchCase(TuplePattern([
            VariablePattern("a"),
            VariablePattern("b")
        ]))
    ]
    result = generator.generate_match_expression("tuple", cases)
    print(f"  代码:\n{result.code}")
    print(f"  绑定: {result.bindings}")
    
    # 测试 6: 或模式
    print("\n测试 6: 或模式")
    cases = [
        MatchCase(OrPattern([
            LiteralPattern(1, "INT"),
            LiteralPattern(2, "INT"),
            LiteralPattern(3, "INT")
        ])),
        MatchCase(WildcardPattern())
    ]
    result = generator.generate_match_expression("x", cases)
    print(f"  代码:\n{result.code}")
    
    # 测试 7: 守卫模式
    print("\n测试 7: 守卫模式")
    cases = [
        MatchCase(GuardPattern(
            pattern=VariablePattern("x"),
            guard="x > 0"
        )),
        MatchCase(WildcardPattern())
    ]
    result = generator.generate_match_expression("n", cases)
    print(f"  代码:\n{result.code}")
    
    print("\n" + "=" * 70)
    print("所有测试完成")
    print("=" * 70)
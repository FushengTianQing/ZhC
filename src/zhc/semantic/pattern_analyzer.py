#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模式匹配语义分析器 - Pattern Matching Semantic Analyzer

实现模式匹配的语义分析功能：
1. 类型检查
2. 穷尽性检查
3. 冗余分支检测
4. 守卫表达式分析
5. 解构绑定验证

Phase 4 - Stage 2 - Task 11.2 Day 2

作者：ZHC 开发团队
日期：2026-04-08
"""

from __future__ import annotations

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum, auto

from .pattern_matching import (
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


# ===== 类型系统 =====


class PatternTypeKind(Enum):
    """模式类型种类"""

    PRIMITIVE = auto()  # 基本类型（整数、浮点、字符串等）
    ENUM = auto()  # 枚举类型
    STRUCT = auto()  # 结构体类型
    TUPLE = auto()  # 元组类型
    ARRAY = auto()  # 数组类型
    OPTION = auto()  # 选项类型
    UNKNOWN = auto()  # 未知类型


@dataclass
class PatternTypeInfo:
    """模式类型信息"""

    name: str
    kind: PatternTypeKind
    constructors: List[str] = field(default_factory=list)  # 枚举构造器
    fields: Dict[str, "PatternTypeInfo"] = field(default_factory=dict)  # 结构体字段
    element_type: Optional["PatternTypeInfo"] = None  # 数组/选项元素类型
    tuple_types: List["PatternTypeInfo"] = field(default_factory=list)  # 元组类型

    def is_enum(self) -> bool:
        return self.kind == PatternTypeKind.ENUM

    def is_struct(self) -> bool:
        return self.kind == PatternTypeKind.STRUCT

    def is_tuple(self) -> bool:
        return self.kind == PatternTypeKind.TUPLE

    def is_option(self) -> bool:
        return self.kind == PatternTypeKind.OPTION


# ===== 分析结果 =====


@dataclass
class PatternAnalysisResult:
    """模式分析结果"""

    success: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    bindings: Dict[str, PatternTypeInfo] = field(default_factory=dict)
    unreachable_cases: List[int] = field(default_factory=list)
    missing_cases: List[str] = field(default_factory=list)


# ===== 语义分析器 =====


class PatternSemanticAnalyzer:
    """模式匹配语义分析器

    负责：
    1. 类型检查：验证模式与匹配值的类型兼容性
    2. 穷尽性检查：确保所有可能的情况都被覆盖
    3. 冗余检测：识别不可达的分支
    4. 变量绑定：收集模式中绑定的变量及其类型
    5. 守卫分析：验证守卫表达式的正确性
    """

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.type_env: Dict[str, PatternTypeInfo] = {}

    def analyze_match_expression(
        self, cases: List[MatchCase], matched_type: PatternTypeInfo
    ) -> PatternAnalysisResult:
        """分析匹配表达式

        Args:
            cases: 匹配分支列表
            matched_type: 被匹配值的类型

        Returns:
            分析结果
        """
        result = PatternAnalysisResult(success=True)

        # 1. 类型检查
        for i, case in enumerate(cases):
            type_result = self._check_pattern_type(case.pattern, matched_type)
            if not type_result.success:
                result.success = False
                result.errors.extend([f"分支 {i}: {err}" for err in type_result.errors])

        # 2. 变量绑定一致性检查
        bindings_result = self._check_binding_consistency(cases)
        if not bindings_result.success:
            result.success = False
            result.errors.extend(bindings_result.errors)
        else:
            result.bindings = bindings_result.bindings

        # 3. 穷尽性检查
        exhaustiveness = self._check_exhaustiveness(cases, matched_type)
        result.warnings.extend(exhaustiveness.warnings)
        result.missing_cases = exhaustiveness.missing_cases

        # 4. 冗余分支检测
        redundancy = self._check_redundancy(cases)
        result.unreachable_cases = redundancy.unreachable_cases
        result.warnings.extend(redundancy.warnings)

        return result

    def _check_pattern_type(
        self, pattern: Pattern, expected_type: PatternTypeInfo
    ) -> PatternAnalysisResult:
        """检查模式类型是否与期望类型匹配

        Args:
            pattern: 模式
            expected_type: 期望的类型

        Returns:
            检查结果
        """
        result = PatternAnalysisResult(success=True)

        if isinstance(pattern, WildcardPattern):
            # 通配符匹配任何类型
            pass

        elif isinstance(pattern, VariablePattern):
            # 变量模式匹配任何类型，绑定变量
            result.bindings[pattern.name] = expected_type

        elif isinstance(pattern, LiteralPattern):
            # 字面量模式：检查类型兼容性
            if not self._is_literal_type_compatible(pattern, expected_type):
                result.success = False
                result.errors.append(
                    f"字面量 {pattern.value} 与类型 {expected_type.name} 不兼容"
                )

        elif isinstance(pattern, RangePattern):
            # 范围模式：必须是数值类型
            if expected_type.kind != PatternTypeKind.PRIMITIVE:
                result.success = False
                result.errors.append(
                    f"范围模式只能用于数值类型，不能用于 {expected_type.name}"
                )
            elif expected_type.name not in (
                "整数型",
                "浮点型",
                "双精度浮点型",
                "长整数型",
                "短整数型",
            ):
                result.success = False
                result.errors.append(
                    f"范围模式只能用于数值类型，不能用于 {expected_type.name}"
                )

        elif isinstance(pattern, ConstructorPattern):
            # 构造器模式：检查构造器是否存在
            if not expected_type.is_enum() and not expected_type.is_option():
                result.success = False
                result.errors.append(
                    f"构造器模式只能用于枚举或选项类型，不能用于 {expected_type.name}"
                )
            elif pattern.constructor not in expected_type.constructors:
                result.success = False
                result.errors.append(
                    f"类型 {expected_type.name} 没有构造器 {pattern.constructor}"
                )
            else:
                # 递归检查子模式
                # 对于选项类型，子模式的类型是元素类型
                sub_type = expected_type
                if expected_type.is_option() and expected_type.element_type:
                    sub_type = expected_type.element_type

                for sub_pattern in pattern.patterns:
                    sub_result = self._check_pattern_type(sub_pattern, sub_type)
                    if not sub_result.success:
                        result.success = False
                        result.errors.extend(sub_result.errors)
                    else:
                        result.bindings.update(sub_result.bindings)

        elif isinstance(pattern, DestructurePattern):
            # 解构模式：检查结构体类型
            if not expected_type.is_struct():
                result.success = False
                result.errors.append(
                    f"解构模式只能用于结构体类型，不能用于 {expected_type.name}"
                )
            else:
                # 检查字段是否存在
                for field_name, field_pattern in pattern.fields.items():
                    if field_name not in expected_type.fields:
                        result.success = False
                        result.errors.append(
                            f"结构体 {expected_type.name} 没有字段 {field_name}"
                        )
                    else:
                        # 递归检查字段模式
                        field_type = expected_type.fields[field_name]
                        field_result = self._check_pattern_type(
                            field_pattern, field_type
                        )
                        if not field_result.success:
                            result.success = False
                            result.errors.extend(field_result.errors)

        elif isinstance(pattern, TuplePattern):
            # 元组模式：检查元组类型
            if not expected_type.is_tuple():
                result.success = False
                result.errors.append(
                    f"元组模式只能用于元组类型，不能用于 {expected_type.name}"
                )
            elif len(pattern.patterns) != len(expected_type.tuple_types):
                result.success = False
                result.errors.append(
                    f"元组长度不匹配：期望 {len(expected_type.tuple_types)}，实际 {len(pattern.patterns)}"
                )
            else:
                # 递归检查元素模式
                for elem_pattern, elem_type in zip(
                    pattern.patterns, expected_type.tuple_types
                ):
                    elem_result = self._check_pattern_type(elem_pattern, elem_type)
                    if not elem_result.success:
                        result.success = False
                        result.errors.extend(elem_result.errors)

        elif isinstance(pattern, OrPattern):
            # 或模式：所有分支必须类型兼容
            for sub_pattern in pattern.patterns:
                sub_result = self._check_pattern_type(sub_pattern, expected_type)
                if not sub_result.success:
                    result.success = False
                    result.errors.extend(sub_result.errors)

        elif isinstance(pattern, AndPattern):
            # 与模式：所有模式必须类型兼容
            for sub_pattern in pattern.patterns:
                sub_result = self._check_pattern_type(sub_pattern, expected_type)
                if not sub_result.success:
                    result.success = False
                    result.errors.extend(sub_result.errors)

        elif isinstance(pattern, GuardPattern):
            # 守卫模式：检查基础模式
            base_result = self._check_pattern_type(pattern.pattern, expected_type)
            if not base_result.success:
                result.success = False
                result.errors.extend(base_result.errors)
            else:
                result.bindings = base_result.bindings

            # TODO: 守卫表达式类型检查（需要表达式类型系统）

        return result

    def _is_literal_type_compatible(
        self, literal: LiteralPattern, type_info: PatternTypeInfo
    ) -> bool:
        """检查字面量类型是否兼容"""
        if type_info.kind != PatternTypeKind.PRIMITIVE:
            return False

        # 简化检查：根据字面量类型判断
        if literal.literal_type in ("INT", "FLOAT"):
            return type_info.name in (
                "整数型",
                "浮点型",
                "双精度浮点型",
                "长整数型",
                "短整数型",
            )
        elif literal.literal_type == "STRING":
            return type_info.name in ("字符串型", "字符型")
        elif literal.literal_type == "BOOL":
            return type_info.name in ("布尔型", "逻辑型")
        elif literal.literal_type == "CHAR":
            return type_info.name in ("字符型", "字符串型")

        return True

    def _check_binding_consistency(
        self, cases: List[MatchCase]
    ) -> PatternAnalysisResult:
        """检查变量绑定的一致性

        确保所有分支绑定相同的变量集合
        """
        result = PatternAnalysisResult(success=True)

        if not cases:
            return result

        # 收集第一个分支的变量
        first_bindings = cases[0].pattern.get_variables()
        result.bindings = {
            var: PatternTypeInfo("unknown", PatternTypeKind.UNKNOWN)
            for var in first_bindings
        }

        # 检查其他分支
        for i, case in enumerate(cases[1:], start=1):
            bindings = case.pattern.get_variables()

            # 检查变量集合是否一致
            if bindings != first_bindings:
                missing = first_bindings - bindings
                extra = bindings - first_bindings

                if missing:
                    result.warnings.append(
                        f"分支 {i} 缺少变量绑定: {', '.join(missing)}"
                    )
                if extra:
                    result.warnings.append(
                        f"分支 {i} 有额外变量绑定: {', '.join(extra)}"
                    )

        return result

    def _check_exhaustiveness(
        self, cases: List[MatchCase], matched_type: PatternTypeInfo
    ) -> PatternAnalysisResult:
        """检查穷尽性

        确保所有可能的情况都被覆盖
        """
        result = PatternAnalysisResult(success=True)

        # 检查是否有通配符分支
        has_wildcard = any(
            isinstance(case.pattern, WildcardPattern)
            or isinstance(case.pattern, VariablePattern)
            for case in cases
        )

        if has_wildcard:
            # 有通配符，一定穷尽
            return result

        # 对于枚举类型，检查所有构造器是否都被覆盖
        if matched_type.is_enum():
            covered_constructors = set()

            for case in cases:
                if isinstance(case.pattern, ConstructorPattern):
                    covered_constructors.add(case.pattern.constructor)
                elif isinstance(case.pattern, OrPattern):
                    for sub_pattern in case.pattern.patterns:
                        if isinstance(sub_pattern, ConstructorPattern):
                            covered_constructors.add(sub_pattern.constructor)

            missing_constructors = set(matched_type.constructors) - covered_constructors

            if missing_constructors:
                result.warnings.append(
                    f"缺少构造器分支: {', '.join(missing_constructors)}"
                )
                result.missing_cases = list(missing_constructors)

        # 对于其他类型，如果没有通配符，给出警告
        else:
            result.warnings.append("缺少通配符分支 _，可能存在未覆盖的情况")

        return result

    def _check_redundancy(self, cases: List[MatchCase]) -> PatternAnalysisResult:
        """检查冗余分支

        识别不可达的分支
        """
        result = PatternAnalysisResult(success=True)

        for i in range(1, len(cases)):
            # 检查当前分支是否被之前的分支覆盖
            for j in range(i):
                if self._is_pattern_covered(cases[i].pattern, cases[j].pattern):
                    result.unreachable_cases.append(i)
                    result.warnings.append(f"分支 {i} 不可达，已被分支 {j} 覆盖")
                    break

        return result

    def _is_pattern_covered(self, pattern: Pattern, covering: Pattern) -> bool:
        """检查 pattern 是否被 covering 覆盖"""
        # 通配符覆盖所有模式
        if isinstance(covering, WildcardPattern):
            return True

        # 变量模式覆盖所有模式
        if isinstance(covering, VariablePattern):
            return True

        # 字面量模式：相同值覆盖
        if isinstance(pattern, LiteralPattern) and isinstance(covering, LiteralPattern):
            return pattern.value == covering.value

        # 构造器模式：相同构造器覆盖
        if isinstance(pattern, ConstructorPattern) and isinstance(
            covering, ConstructorPattern
        ):
            if pattern.constructor != covering.constructor:
                return False

            # 检查参数
            if len(pattern.patterns) != len(covering.patterns):
                return False

            return all(
                self._is_pattern_covered(p, c)
                for p, c in zip(pattern.patterns, covering.patterns)
            )

        # 或模式：任一分支覆盖即可
        if isinstance(covering, OrPattern):
            return any(
                self._is_pattern_covered(pattern, sub) for sub in covering.patterns
            )

        # 其他情况：保守估计不覆盖
        return False


# ===== 辅助函数 =====


def analyze_match(
    cases: List[MatchCase], matched_type: PatternTypeInfo
) -> PatternAnalysisResult:
    """分析匹配表达式的便捷函数"""
    analyzer = PatternSemanticAnalyzer()
    return analyzer.analyze_match_expression(cases, matched_type)


def create_enum_type(name: str, constructors: List[str]) -> PatternTypeInfo:
    """创建枚举类型信息"""
    return PatternTypeInfo(
        name=name, kind=PatternTypeKind.ENUM, constructors=constructors
    )


def create_struct_type(
    name: str, fields: Dict[str, PatternTypeInfo]
) -> PatternTypeInfo:
    """创建结构体类型信息"""
    return PatternTypeInfo(name=name, kind=PatternTypeKind.STRUCT, fields=fields)


def create_tuple_type(types: List[PatternTypeInfo]) -> PatternTypeInfo:
    """创建元组类型信息"""
    return PatternTypeInfo(name="tuple", kind=PatternTypeKind.TUPLE, tuple_types=types)


def create_option_type(element_type: PatternTypeInfo) -> PatternTypeInfo:
    """创建选项类型信息"""
    return PatternTypeInfo(
        name="Option",
        kind=PatternTypeKind.OPTION,
        constructors=["Some", "None"],
        element_type=element_type,
    )


def create_primitive_type(name: str) -> PatternTypeInfo:
    """创建基本类型信息"""
    return PatternTypeInfo(name=name, kind=PatternTypeKind.PRIMITIVE)

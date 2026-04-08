"""
ZHC编译器 - 函数重载解析器

功能：
- 函数重载候选查找
- 参数类型匹配
- 最佳匹配选择
- 歧义检测

作者：远
日期：2026-04-03
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
from .type_checker import TypeInfo
from .scope_checker import Symbol, SymbolCategory


@dataclass
class OverloadCandidate:
    """重载候选函数"""

    symbol: Symbol  # 函数符号
    match_scores: List[int]  # 每个参数的匹配分数
    total_score: int  # 总匹配分数
    is_exact_match: bool  # 是否完全匹配
    has_conversion: bool  # 是否需要类型转换


class OverloadResolver:
    """函数重载解析器"""

    def __init__(self):
        """初始化重载解析器"""
        self.errors: List[Tuple[int, str, str]] = []
        self.warnings: List[Tuple[int, str, str]] = []

    def resolve(
        self,
        line: int,
        func_name: str,
        candidates: List[Symbol],
        arg_types: List[TypeInfo],
    ) -> Optional[Symbol]:
        """
        解析函数重载

        Args:
            line: 行号
            func_name: 函数名
            candidates: 候选函数列表
            arg_types: 参数类型列表

        Returns:
            最佳匹配函数，如果无匹配则返回None
        """
        if not candidates:
            self.errors.append((line, "未找到函数", f"未找到函数 '{func_name}'"))
            return None

        # 计算每个候选的匹配分数
        scored_candidates: List[OverloadCandidate] = []

        for candidate in candidates:
            if candidate.category != SymbolCategory.FUNCTION:
                continue

            # 检查参数数量
            if not candidate.type_info.param_types:
                # 无参数函数
                if arg_types:
                    continue
                scored_candidates.append(
                    OverloadCandidate(
                        symbol=candidate,
                        match_scores=[],
                        total_score=0,
                        is_exact_match=True,
                        has_conversion=False,
                    )
                )
                continue

            expected_params = candidate.type_info.param_types
            if len(expected_params) != len(arg_types):
                continue

            # 计算匹配分数
            match_scores = []
            total_score = 0
            is_exact_match = True
            has_conversion = False

            for expected, actual in zip(expected_params, arg_types):
                score, exact, conversion = self._compute_match_score(expected, actual)
                match_scores.append(score)
                total_score += score

                if not exact:
                    is_exact_match = False

                if conversion:
                    has_conversion = True

            scored_candidates.append(
                OverloadCandidate(
                    symbol=candidate,
                    match_scores=match_scores,
                    total_score=total_score,
                    is_exact_match=is_exact_match,
                    has_conversion=has_conversion,
                )
            )

        if not scored_candidates:
            self.errors.append(
                (
                    line,
                    "无匹配重载",
                    f"未找到匹配 '{func_name}({', '.join(str(t) for t in arg_types)})' 的重载",
                )
            )
            return None

        # 找到最佳匹配
        best = self._select_best_match(scored_candidates)

        if not best:
            # 歧义：多个候选匹配度相同
            ambiguous = [
                c
                for c in scored_candidates
                if c.total_score == scored_candidates[0].total_score
            ]
            amb_funcs = [f"'{c.symbol.name}'" for c in ambiguous]
            self.errors.append(
                (
                    line,
                    "重载歧义",
                    f"函数 '{func_name}' 调用有歧义，候选：{', '.join(amb_funcs)}",
                )
            )
            return None

        # 警告：使用了隐式转换
        if best.has_conversion:
            self.warnings.append(
                (line, "隐式类型转换", f"调用 '{func_name}' 时使用了隐式类型转换")
            )

        return best.symbol

    def _compute_match_score(
        self, expected: TypeInfo, actual: TypeInfo
    ) -> Tuple[int, bool, bool]:
        """
        计算参数匹配分数

        Args:
            expected: 期望类型
            actual: 实际类型

        Returns:
            (匹配分数, 是否完全匹配, 是否需要转换)
        """
        # 完全匹配
        if expected.equals(actual):
            return (100, True, False)

        # 数值类型转换
        if expected.is_numeric() and actual.is_numeric():
            # 计算转换代价
            if expected.is_float() and actual.is_integer():
                # 整数转浮点：无损失
                return (80, False, True)

            if expected.is_integer() and actual.is_float():
                # 浮点转整数：有损失
                return (50, False, True)

            if expected.size >= actual.size:
                # 小转大：无损失
                return (90, False, True)
            else:
                # 大转小：有损失
                return (60, False, True)

        # 指针类型转换
        if expected.is_pointer() and actual.is_pointer():
            if expected.base_type and actual.base_type:
                if expected.base_type.equals(actual.base_type):
                    # 同类型指针
                    return (95, False, False)
                elif expected.base_type.name == "空型":
                    # 转换为void*
                    return (70, False, True)
            elif expected.name == "空型指针":
                # 任意指针转void*
                return (70, False, True)

        # 数组转指针
        if expected.is_pointer() and actual.is_array():
            if expected.base_type and actual.base_type:
                if expected.base_type.equals(actual.base_type):
                    return (85, False, True)

        # 不匹配
        return (0, False, False)

    def _select_best_match(
        self, candidates: List[OverloadCandidate]
    ) -> Optional[OverloadCandidate]:
        """
        选择最佳匹配

        Args:
            candidates: 候选列表

        Returns:
            最佳候选，如果有歧义则返回None
        """
        if not candidates:
            return None

        # 按总分数排序
        sorted_candidates = sorted(
            candidates, key=lambda c: c.total_score, reverse=True
        )

        # 检查是否有唯一的最佳匹配
        if len(sorted_candidates) == 1:
            return sorted_candidates[0]

        # 检查前两名是否有明显差距
        best = sorted_candidates[0]
        second = sorted_candidates[1]

        if best.total_score > second.total_score:
            return best

        # 分数相同，检查是否有更好的精确匹配
        exact_matches = [c for c in sorted_candidates if c.is_exact_match]
        if len(exact_matches) == 1:
            return exact_matches[0]

        # 分数相同，检查是否需要转换
        no_conversion = [c for c in sorted_candidates if not c.has_conversion]
        if len(no_conversion) == 1:
            return no_conversion[0]

        # 歧义
        return None

    def check_overload_validity(
        self, line: int, new_func: Symbol, existing_funcs: List[Symbol]
    ) -> bool:
        """
        检查重载函数是否合法

        Args:
            line: 行号
            new_func: 新函数
            existing_funcs: 已存在的函数列表

        Returns:
            是否合法
        """
        # 检查参数列表是否唯一
        for existing in existing_funcs:
            if self._is_same_signature(new_func, existing):
                self.errors.append(
                    (
                        line,
                        "重复重载",
                        f"函数 '{new_func.name}' 的重载与行 {existing.line} 的函数签名相同",
                    )
                )
                return False

        return True

    def _is_same_signature(self, func1: Symbol, func2: Symbol) -> bool:
        """
        检查两个函数签名是否相同

        Args:
            func1: 函数1
            func2: 函数2

        Returns:
            是否相同
        """
        params1 = func1.type_info.param_types
        params2 = func2.type_info.param_types

        # 参数数量不同
        if len(params1) != len(params2):
            return False

        # 检查每个参数类型
        for p1, p2 in zip(params1, params2):
            if not p1.equals(p2):
                return False

        return True

    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0

    def get_errors(self) -> List[Tuple[int, str, str]]:
        """获取所有错误"""
        return self.errors

    def get_warnings(self) -> List[Tuple[int, str, str]]:
        """获取所有警告"""
        return self.warnings

    def clear(self):
        """清空错误和警告"""
        self.errors.clear()
        self.warnings.clear()

    def report(self) -> str:
        """生成重载解析报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("重载解析报告")
        lines.append("=" * 60)

        if self.errors:
            lines.append(f"\n错误 ({len(self.errors)}):")
            for line, error_type, message in self.errors:
                lines.append(f"  行 {line}: [{error_type}] {message}")
        else:
            lines.append("\n✅ 无重载解析错误")

        if self.warnings:
            lines.append(f"\n警告 ({len(self.warnings)}):")
            for line, warning_type, message in self.warnings:
                lines.append(f"  行 {line}: [{warning_type}] {message}")
        else:
            lines.append("\n✅ 无重载解析警告")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)

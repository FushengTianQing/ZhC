"""
智能提示生成器

提供编译错误的智能提示和建议，帮助用户快速定位和修复问题。

创建日期: 2026-04-09
最后更新: 2026-04-09
维护者: ZHC开发团队
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, TYPE_CHECKING
import difflib
import re

if TYPE_CHECKING:
    from .base import ZHCError, SourceLocation


@dataclass
class Suggestion:
    """
    修复建议

    包含具体的修复建议和相关信息。
    """

    message: str  # 建议消息
    kind: str = "fix"  # 建议类型: fix, hint, info
    confidence: float = 0.8  # 置信度 (0-1)
    replacement: Optional[str] = None  # 替换文本（可选）
    insert_text: Optional[str] = None  # 插入文本（可选）
    location: Optional["SourceLocation"] = None  # 建议位置

    def is_high_confidence(self) -> bool:
        """是否为高置信度建议"""
        return self.confidence >= 0.8

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message": self.message,
            "kind": self.kind,
            "confidence": self.confidence,
            "replacement": self.replacement,
            "insert_text": self.insert_text,
        }


@dataclass
class SuggestionResult:
    """
    建议结果

    包含错误的所有建议信息。
    """

    error: "ZHCError"
    suggestions: List[Suggestion] = field(default_factory=list)
    similar_symbols: List[str] = field(default_factory=list)
    documentation_links: List[str] = field(default_factory=list)

    def has_suggestions(self) -> bool:
        """是否有建议"""
        return len(self.suggestions) > 0 or len(self.similar_symbols) > 0

    def get_best_suggestion(self) -> Optional[Suggestion]:
        """获取最佳建议"""
        if not self.suggestions:
            return None
        return max(self.suggestions, key=lambda s: s.confidence)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "error_message": str(self.error),
            "suggestions": [s.to_dict() for s in self.suggestions],
            "similar_symbols": self.similar_symbols,
            "documentation_links": self.documentation_links,
        }


class SuggestionGenerator:
    """
    智能提示生成器

    根据错误类型生成智能修复建议。

    Example:
        >>> generator = SuggestionGenerator()
        >>> generator.register_symbol('计数器', 'variable')
        >>> result = generator.generate_suggestions(error)
        >>> print(result.suggestions[0].message)
    """

    def __init__(self):
        """初始化"""
        self._symbols: Dict[str, Dict[str, Any]] = {}
        self._functions: Dict[str, Dict[str, Any]] = {}
        self._types: Dict[str, Dict[str, Any]] = {}
        self._keywords: set = set()
        self._type_conversions: Dict[str, List[str]] = {}
        self._initialize_builtin_symbols()

    def _initialize_builtin_symbols(self):
        """初始化内置符号"""
        # 内置类型
        builtin_types = [
            "整数型",
            "浮点型",
            "字符型",
            "字符串型",
            "布尔型",
            "空型",
            "短整型",
            "长整型",
            "双精度浮点型",
            "无符号整数型",
        ]
        for t in builtin_types:
            self._types[t] = {"kind": "builtin_type", "name": t}

        # 内置关键字
        self._keywords = {
            "如果",
            "否则",
            "循环",
            "当",
            "返回",
            "中断",
            "继续",
            "函数",
            "类",
            "结构体",
            "公开",
            "私有",
            "保护",
            "静态",
            "常量",
            "只读",
            "自动",
            "空",
        }

        # 类型转换建议
        self._type_conversions = {
            "整数型": ["浮点型", "长整型", "字符型"],
            "浮点型": ["双精度浮点型", "整数型"],
            "字符型": ["整数型", "字符串型"],
            "字符串型": ["字符型"],
        }

    def register_symbol(self, name: str, kind: str, type_name: Optional[str] = None):
        """
        注册符号

        Args:
            name: 符号名
            kind: 符号类型 (variable, function, class, etc.)
            type_name: 类型名（可选）
        """
        self._symbols[name] = {
            "name": name,
            "kind": kind,
            "type": type_name,
        }

    def register_function(self, name: str, params: List[str], return_type: str):
        """
        注册函数

        Args:
            name: 函数名
            params: 参数类型列表
            return_type: 返回类型
        """
        self._functions[name] = {
            "name": name,
            "params": params,
            "return_type": return_type,
        }

    def register_type(self, name: str, kind: str = "user_defined"):
        """
        注册类型

        Args:
            name: 类型名
            kind: 类型种类
        """
        self._types[name] = {
            "name": name,
            "kind": kind,
        }

    def generate_suggestions(self, error: "ZHCError") -> SuggestionResult:
        """
        生成错误建议

        Args:
            error: 错误对象

        Returns:
            建议结果
        """
        result = SuggestionResult(error=error)
        error_code = error.error_code or ""

        # 根据错误代码生成建议
        if "UNDEFINED" in error_code:
            self._generate_undefined_suggestions(error, result)
        elif "TYPE_MISMATCH" in error_code or "INCOMPATIBLE" in error_code:
            self._generate_type_mismatch_suggestions(error, result)
        elif "DUPLICATE" in error_code:
            self._generate_duplicate_suggestions(error, result)
        elif "MISSING" in error_code:
            self._generate_missing_suggestions(error, result)
        elif "INVALID" in error_code:
            self._generate_invalid_suggestions(error, result)
        elif "OUT_OF_SCOPE" in error_code:
            self._generate_scope_suggestions(error, result)

        # 添加文档链接
        result.documentation_links = self._get_documentation_links(error)

        return result

    def _generate_undefined_suggestions(
        self, error: "ZHCError", result: SuggestionResult
    ):
        """生成未定义符号的建议"""
        message = error.message

        # 提取符号名
        match = re.search(r"'([^']+)'", message)
        if not match:
            return

        symbol_name = match.group(1)

        # 查找相似符号
        similar = self._find_similar_symbols(symbol_name)
        result.similar_symbols = similar

        # 生成建议
        if similar:
            best_match = similar[0]
            result.suggestions.append(
                Suggestion(
                    message=f"您是否想使用 '{best_match}'？",
                    kind="fix",
                    confidence=0.9,
                    replacement=best_match,
                )
            )

        # 检查是否为关键字
        if symbol_name in self._keywords:
            result.suggestions.append(
                Suggestion(
                    message=f"'{symbol_name}' 是关键字，请检查用法",
                    kind="hint",
                    confidence=1.0,
                )
            )

        # 检查是否需要声明
        result.suggestions.append(
            Suggestion(
                message=f"请确保 '{symbol_name}' 已声明",
                kind="hint",
                confidence=0.7,
            )
        )

    def _generate_type_mismatch_suggestions(
        self, error: "ZHCError", result: SuggestionResult
    ):
        """生成类型不匹配的建议"""
        message = error.message

        # 尝试提取类型信息
        expected_match = re.search(r"期望\s*['\"]?([^'\"，,\s]+)", message)
        actual_match = re.search(r"实际\s*['\"]?([^'\"，,\s]+)", message)

        if expected_match and actual_match:
            expected = expected_match.group(1)
            actual = actual_match.group(1)

            # 检查是否可以转换
            if actual in self._type_conversions:
                conversions = self._type_conversions[actual]
                if expected in conversions:
                    result.suggestions.append(
                        Suggestion(
                            message=f"可以使用类型转换: ({expected})值",
                            kind="fix",
                            confidence=0.8,
                        )
                    )

            # 检查是否为常见错误
            result.suggestions.append(
                Suggestion(
                    message=f"请检查表达式类型，期望 {expected}，实际 {actual}",
                    kind="hint",
                    confidence=0.7,
                )
            )

    def _generate_duplicate_suggestions(
        self, error: "ZHCError", result: SuggestionResult
    ):
        """生成重复定义的建议"""
        message = error.message

        # 提取符号名
        match = re.search(r"'([^']+)'", message)
        if match:
            symbol_name = match.group(1)
            result.suggestions.append(
                Suggestion(
                    message=f"请使用不同的名称或删除重复定义",
                    kind="hint",
                    confidence=0.8,
                )
            )
            result.suggestions.append(
                Suggestion(
                    message=f"考虑重命名为 '{symbol_name}2' 或 '{symbol_name}_新'",
                    kind="fix",
                    confidence=0.6,
                )
            )

    def _generate_missing_suggestions(
        self, error: "ZHCError", result: SuggestionResult
    ):
        """生成缺失项的建议"""
        message = error.message

        if "分号" in message or "SEMICOLON" in message.upper():
            result.suggestions.append(
                Suggestion(
                    message="在语句末尾添加分号 ';'",
                    kind="fix",
                    confidence=0.95,
                    insert_text=";",
                )
            )

        elif "括号" in message or "PAREN" in message.upper():
            result.suggestions.append(
                Suggestion(
                    message="检查括号是否匹配",
                    kind="hint",
                    confidence=0.8,
                )
            )

        elif "花括号" in message or "BRACE" in message.upper():
            result.suggestions.append(
                Suggestion(
                    message="检查花括号是否匹配",
                    kind="hint",
                    confidence=0.8,
                )
            )

        elif "返回" in message or "RETURN" in message.upper():
            result.suggestions.append(
                Suggestion(
                    message="添加返回语句",
                    kind="fix",
                    confidence=0.85,
                    insert_text="返回 0;",
                )
            )

    def _generate_invalid_suggestions(
        self, error: "ZHCError", result: SuggestionResult
    ):
        """生成无效操作的建议"""
        message = error.message

        if "赋值" in message:
            result.suggestions.append(
                Suggestion(
                    message="检查左侧是否为可赋值的变量",
                    kind="hint",
                    confidence=0.7,
                )
            )

        elif "参数" in message:
            result.suggestions.append(
                Suggestion(
                    message="检查函数参数数量和类型是否正确",
                    kind="hint",
                    confidence=0.7,
                )
            )

        elif "索引" in message or "下标" in message:
            result.suggestions.append(
                Suggestion(
                    message="检查数组索引是否在有效范围内",
                    kind="hint",
                    confidence=0.8,
                )
            )

    def _generate_scope_suggestions(self, error: "ZHCError", result: SuggestionResult):
        """生成作用域错误的建议"""
        message = error.message

        match = re.search(r"'([^']+)'", message)
        if match:
            symbol_name = match.group(1)
            result.suggestions.append(
                Suggestion(
                    message=f"'{symbol_name}' 可能不在当前作用域内",
                    kind="hint",
                    confidence=0.7,
                )
            )
            result.suggestions.append(
                Suggestion(
                    message="检查变量是否在正确的作用域中声明",
                    kind="hint",
                    confidence=0.6,
                )
            )

    def _find_similar_symbols(self, name: str, max_results: int = 5) -> List[str]:
        """
        查找相似符号

        Args:
            name: 符号名
            max_results: 最大结果数

        Returns:
            相似符号列表
        """
        all_symbols = (
            list(self._symbols.keys())
            + list(self._functions.keys())
            + list(self._types.keys())
        )

        # 使用 difflib 查找相似字符串
        similar = difflib.get_close_matches(
            name, all_symbols, n=max_results, cutoff=0.6
        )

        return similar

    def _get_documentation_links(self, error: "ZHCError") -> List[str]:
        """
        获取文档链接

        Args:
            error: 错误对象

        Returns:
            文档链接列表
        """
        error_code = error.error_code
        if not error_code:
            return []

        # 根据错误代码生成文档链接
        base_url = "https://zhc-lang.org/docs/errors"

        links = []

        if error_code.startswith("E") or error_code.startswith("SEMANTIC_"):
            links.append(f"{base_url}/{error_code}")

        if "TYPE" in error_code:
            links.append(f"{base_url}/type-system")

        if "SCOPE" in error_code:
            links.append(f"{base_url}/scope")

        return links

    def clear_symbols(self):
        """清空注册的符号"""
        self._symbols.clear()
        self._functions.clear()
        # 保留内置类型


class ErrorEnhancer:
    """
    错误增强器

    为错误添加智能提示和建议。
    """

    def __init__(self, suggestion_generator: Optional[SuggestionGenerator] = None):
        """
        初始化

        Args:
            suggestion_generator: 建议生成器
        """
        self.generator = suggestion_generator or SuggestionGenerator()

    def enhance_error(self, error: "ZHCError") -> "ZHCError":
        """
        增强错误信息

        Args:
            error: 原始错误

        Returns:
            增强后的错误
        """
        result = self.generator.generate_suggestions(error)

        if result.has_suggestions():
            best = result.get_best_suggestion()
            if best:
                # 添加建议到错误消息
                enhanced_suggestion = error.suggestion or ""
                enhanced_suggestion += f"\n提示: {best.message}"

                if best.replacement:
                    enhanced_suggestion += f"\n建议替换为: {best.replacement}"

                # 创建增强后的错误
                error.suggestion = enhanced_suggestion

        return error

    def enhance_errors(self, errors: List["ZHCError"]) -> List["ZHCError"]:
        """
        批量增强错误

        Args:
            errors: 错误列表

        Returns:
            增强后的错误列表
        """
        return [self.enhance_error(error) for error in errors]


# 导出公共API
__all__ = [
    "Suggestion",
    "SuggestionResult",
    "SuggestionGenerator",
    "ErrorEnhancer",
]

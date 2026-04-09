"""
错误解释器

提供详细的错误解释和教育性信息，帮助用户理解错误原因和修复方法。

创建日期: 2026-04-10
最后更新: 2026-04-10
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from .base import ZHCError
from .error_codes import ErrorCodeRegistry, ErrorCodeDefinition


@dataclass
class Explanation:
    """
    错误解释

    包含错误的详细解释信息。
    """

    error_code: str
    title: str
    description: str
    category: str
    severity: str
    common_causes: List[str] = field(default_factory=list)
    suggestions: List[Dict[str, Any]] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    related_errors: List[str] = field(default_factory=list)
    documentation_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "error_code": self.error_code,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "severity": self.severity,
            "common_causes": self.common_causes,
            "suggestions": self.suggestions,
            "examples": self.examples,
            "related_errors": self.related_errors,
            "documentation_url": self.documentation_url,
        }


class ErrorExplainer:
    """
    错误解释器

    为错误提供详细的解释和教育性信息。

    Example:
        >>> explainer = ErrorExplainer()
        >>> error = ZHCError("类型不匹配", error_code="E001")
        >>> explanation = explainer.explain(error)
        >>> print(explanation.title)
        类型不匹配
    """

    # 相关错误映射
    RELATED_ERRORS = {
        "E001": ["E004", "E005"],  # 类型不匹配 -> 无效类型转换、参数不匹配
        "E002": ["E003", "S012"],  # 未定义符号 -> 重复声明、变量超出作用域
        "E003": ["E002"],  # 重复声明 -> 未定义符号
        "E004": ["E001"],  # 无效类型转换 -> 类型不匹配
        "E005": ["E001", "E003"],  # 参数不匹配 -> 类型不匹配、重复声明
    }

    def __init__(self, verbose: bool = False):
        """
        初始化错误解释器

        Args:
            verbose: 是否启用详细模式
        """
        self.verbose = verbose

    def explain(self, error: ZHCError, verbose: Optional[bool] = None) -> Explanation:
        """
        生成错误详细解释

        Args:
            error: 错误对象
            verbose: 是否显示详细信息（覆盖实例设置）

        Returns:
            错误解释对象
        """
        use_verbose = verbose if verbose is not None else self.verbose
        error_code = error.error_code or "UNKNOWN"

        # 从注册表获取错误定义
        definition = ErrorCodeRegistry.get(error_code)

        if definition:
            return self._explain_from_definition(error, definition, use_verbose)
        else:
            return self._explain_unknown_error(error, use_verbose)

    def _explain_from_definition(
        self, error: ZHCError, definition: ErrorCodeDefinition, verbose: bool
    ) -> Explanation:
        """从错误代码定义生成解释"""
        # 获取相关错误
        related = self.RELATED_ERRORS.get(definition.code, [])

        explanation = Explanation(
            error_code=definition.code,
            title=definition.brief_message,
            description=self._generate_description(error, definition),
            category=definition.category,
            severity=definition.severity,
            common_causes=definition.common_causes.copy(),
            suggestions=definition.suggestions.copy(),
            examples=definition.examples.copy(),
            related_errors=related,
            documentation_url=definition.documentation_url,
        )

        return explanation

    def _explain_unknown_error(self, error: ZHCError, verbose: bool) -> Explanation:
        """为未知错误生成解释"""
        return Explanation(
            error_code="UNKNOWN",
            title=error.message,
            description=self._generate_generic_description(error),
            category="未知类别",
            severity=error.severity,
            common_causes=["请检查代码逻辑"],
            suggestions=[{"description": "检查相关代码"}],
            examples=[],
            related_errors=[],
        )

    def _generate_description(
        self, error: ZHCError, definition: ErrorCodeDefinition
    ) -> str:
        """生成错误描述"""
        parts = []

        # 基本描述
        parts.append(f"{definition.brief_message}")

        # 如果有详细消息模板，尝试格式化
        if definition.detailed_message:
            try:
                # 尝试从错误上下文获取变量
                detailed = definition.detailed_message
                parts.append(detailed)
            except Exception:
                pass

        return "\n".join(parts)

    def _generate_generic_description(self, error: ZHCError) -> str:
        """生成通用错误描述"""
        description = error.message

        if error.context:
            description += f"\n上下文: {error.context}"

        return description

    def format_explanation(
        self, explanation: Explanation, style: str = "detailed"
    ) -> str:
        """
        格式化解释为字符串

        Args:
            explanation: 错误解释
            style: 格式风格 (detailed, brief, json)

        Returns:
            格式化后的字符串
        """
        if style == "json":
            import json

            return json.dumps(explanation.to_dict(), ensure_ascii=False, indent=2)

        if style == "brief":
            return self._format_brief(explanation)

        return self._format_detailed(explanation)

    def _format_detailed(self, explanation: Explanation) -> str:
        """格式化为详细风格"""
        lines = []

        # 标题
        lines.append("=" * 60)
        lines.append(f"错误 [{explanation.error_code}]: {explanation.title}")
        lines.append("=" * 60)

        # 基本信息
        lines.append(f"类别: {explanation.category}")
        lines.append(f"严重程度: {explanation.severity}")
        lines.append("")

        # 描述
        if explanation.description:
            lines.append("描述:")
            lines.append(f"  {explanation.description}")
            lines.append("")

        # 常见原因
        if explanation.common_causes:
            lines.append("常见原因:")
            for i, cause in enumerate(explanation.common_causes, 1):
                lines.append(f"  {i}. {cause}")
            lines.append("")

        # 修复建议
        if explanation.suggestions:
            lines.append("修复建议:")
            for i, suggestion in enumerate(explanation.suggestions, 1):
                if isinstance(suggestion, dict):
                    desc = suggestion.get("description", "")
                    code = suggestion.get("code_example", "")
                    lines.append(f"  {i}. {desc}")
                    if code:
                        lines.append(f"     示例: {code}")
                else:
                    lines.append(f"  {i}. {suggestion}")
            lines.append("")

        # 正确示例
        if explanation.examples:
            lines.append("正确示例:")
            for example in explanation.examples[:3]:  # 最多显示3个
                lines.append(f"  {example}")
            lines.append("")

        # 相关错误
        if explanation.related_errors:
            lines.append(f"相关错误: {', '.join(explanation.related_errors)}")
            lines.append("")

        # 文档链接
        if explanation.documentation_url:
            lines.append(f"文档: {explanation.documentation_url}")

        # 使用提示
        lines.append("")
        lines.append(
            f"提示: 使用 'zhc --explain {explanation.error_code}' 查看此错误的详细说明"
        )

        return "\n".join(lines)

    def _format_brief(self, explanation: Explanation) -> str:
        """格式化为简洁风格"""
        return f"错误 [{explanation.error_code}]: {explanation.title}"

    def explain_code(self, error_code: str) -> Optional[Explanation]:
        """
        解释错误代码

        Args:
            error_code: 错误代码（如 E001）

        Returns:
            错误解释，如果代码不存在返回 None
        """
        definition = ErrorCodeRegistry.get(error_code)
        if not definition:
            return None

        # 创建一个虚拟错误来生成解释
        dummy_error = ZHCError(
            definition.brief_message,
            error_code=error_code,
            severity=definition.severity,
        )

        return self.explain(dummy_error)

    def get_all_error_codes(self) -> List[str]:
        """获取所有已定义的错误代码"""
        return ErrorCodeRegistry.get_all_codes()

    def get_errors_by_category(self, category: str) -> List[Explanation]:
        """按类别获取错误解释"""
        definitions = ErrorCodeRegistry.get_by_category(category)
        explanations = []

        for definition in definitions:
            dummy_error = ZHCError(
                definition.brief_message,
                error_code=definition.code,
                severity=definition.severity,
            )
            explanations.append(self.explain(dummy_error))

        return explanations


# 导出公共API
__all__ = [
    "Explanation",
    "ErrorExplainer",
]

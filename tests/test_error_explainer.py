"""
错误处理增强功能单元测试

测试 ErrorExplainer 和增强的错误格式化功能。

创建日期: 2026-04-10
最后更新: 2026-04-10
"""

import pytest
from zhc.errors import (
    SourceLocation,
    ZHCError,
    ErrorCollection,
    ErrorFormatter,
    ErrorExplainer,
    ErrorCodeRegistry,
    SuggestionGenerator,
)


# ============================================================================
# ErrorExplainer 测试
# ============================================================================


class TestErrorExplainer:
    """测试错误解释器"""

    def test_explain_known_error(self):
        """测试解释已知错误代码"""
        explainer = ErrorExplainer()
        error = ZHCError("类型不匹配", error_code="E001")

        explanation = explainer.explain(error)

        assert explanation.error_code == "E001"
        assert explanation.title == "类型不匹配"
        assert explanation.category == "类型错误"
        assert len(explanation.common_causes) > 0
        assert len(explanation.suggestions) > 0

    def test_explain_unknown_error(self):
        """测试解释未知错误代码"""
        explainer = ErrorExplainer()
        error = ZHCError("未知错误", error_code="UNKNOWN999")

        explanation = explainer.explain(error)

        assert explanation.error_code == "UNKNOWN"
        assert explanation.title == "未知错误"

    def test_format_explanation_detailed(self):
        """测试格式化详细解释"""
        explainer = ErrorExplainer()
        error = ZHCError("类型不匹配", error_code="E001")

        explanation = explainer.explain(error)
        formatted = explainer.format_explanation(explanation, style="detailed")

        assert "错误 [E001]" in formatted
        assert "类型不匹配" in formatted
        assert "类别" in formatted
        assert "常见原因" in formatted
        assert "修复建议" in formatted

    def test_format_explanation_brief(self):
        """测试格式化简洁解释"""
        explainer = ErrorExplainer()
        error = ZHCError("类型不匹配", error_code="E001")

        explanation = explainer.explain(error)
        formatted = explainer.format_explanation(explanation, style="brief")

        assert formatted == "错误 [E001]: 类型不匹配"

    def test_format_explanation_json(self):
        """测试格式化 JSON 解释"""
        explainer = ErrorExplainer()
        error = ZHCError("类型不匹配", error_code="E001")

        explanation = explainer.explain(error)
        formatted = explainer.format_explanation(explanation, style="json")

        assert '"error_code": "E001"' in formatted
        assert '"title": "类型不匹配"' in formatted

    def test_explain_code(self):
        """测试直接解释错误代码"""
        explainer = ErrorExplainer()

        explanation = explainer.explain_code("E001")

        assert explanation is not None
        assert explanation.error_code == "E001"

    def test_explain_nonexistent_code(self):
        """测试解释不存在的错误代码"""
        explainer = ErrorExplainer()

        explanation = explainer.explain_code("X999")

        assert explanation is None

    def test_get_all_error_codes(self):
        """测试获取所有错误代码"""
        explainer = ErrorExplainer()

        codes = explainer.get_all_error_codes()

        assert len(codes) > 0
        assert "E001" in codes
        assert "E002" in codes
        assert "L001" in codes
        assert "P001" in codes
        assert "S001" in codes

    def test_get_errors_by_category(self):
        """测试按类别获取错误"""
        explainer = ErrorExplainer()

        errors = explainer.get_errors_by_category("类型错误")

        assert len(errors) > 0
        for error in errors:
            assert error.category == "类型错误"


# ============================================================================
# ErrorCodeRegistry 测试
# ============================================================================


class TestErrorCodeRegistry:
    """测试错误代码注册表"""

    def test_get_existing_code(self):
        """测试获取已存在的错误代码"""
        definition = ErrorCodeRegistry.get("E001")

        assert definition is not None
        assert definition.code == "E001"
        assert definition.category == "类型错误"

    def test_get_nonexistent_code(self):
        """测试获取不存在的错误代码"""
        definition = ErrorCodeRegistry.get("X999")

        assert definition is None

    def test_has_code(self):
        """测试检查错误代码是否存在"""
        assert ErrorCodeRegistry.has("E001") is True
        assert ErrorCodeRegistry.has("X999") is False

    def test_get_by_category(self):
        """测试按类别获取错误代码"""
        definitions = ErrorCodeRegistry.get_by_category("类型错误")

        assert len(definitions) > 0
        for definition in definitions:
            assert definition.category == "类型错误"

    def test_get_all_codes(self):
        """测试获取所有错误代码"""
        codes = ErrorCodeRegistry.get_all_codes()

        assert len(codes) > 0
        assert "E001" in codes

    def test_error_code_definition_message_format(self):
        """测试错误代码定义的消息格式化"""
        definition = ErrorCodeRegistry.get("E001")

        # 测试基本消息
        message = definition.get_message()
        assert message == "类型不匹配"

        # 测试带参数的消息
        message = definition.get_message(operator="+")
        assert "类型不匹配" in message


# ============================================================================
# ErrorFormatter 增强测试
# ============================================================================


class TestEnhancedErrorFormatter:
    """测试增强的错误格式化器"""

    def test_format_error_with_smart_suggestions(self):
        """测试带智能提示的错误格式化"""
        formatter = ErrorFormatter(color_output=False)
        error = ZHCError(
            "类型不匹配",
            error_code="E001",
            location=SourceLocation("test.zhc", 10, 5),
        )

        formatted = formatter.format_error(error)

        assert "错误[E001]" in formatted
        assert "test.zhc:10:5" in formatted
        assert "--explain" in formatted  # 帮助信息

    def test_format_error_with_undefined_symbol_suggestions(self):
        """测试未定义符号的智能提示"""
        formatter = ErrorFormatter(color_output=False)
        error = ZHCError(
            "未定义的变量 '计数四'",
            error_code="E002",
            location=SourceLocation("test.zhc", 10, 5),
        )

        # 注册一些相似符号
        formatter.suggestion_generator.register_symbol("计数器", "variable")

        formatted = formatter.format_error(error)

        # 检查是否有帮助信息
        assert "--explain" in formatted

    def test_format_error_collection_with_help(self):
        """测试错误集合格式化包含帮助"""
        formatter = ErrorFormatter(color_output=False)
        errors = ErrorCollection()

        errors.add(
            ZHCError(
                "类型不匹配",
                error_code="E001",
                location=SourceLocation("test.zhc", 10, 5),
            )
        )
        errors.add(
            ZHCError(
                "未定义的变量",
                error_code="E002",
                location=SourceLocation("test.zhc", 20, 10),
            )
        )

        formatted = formatter.format_error_collection(errors)

        assert "2 个错误" in formatted
        assert "test.zhc:10:5" in formatted
        assert "test.zhc:20:10" in formatted


# ============================================================================
# 智能提示生成器测试
# ============================================================================


class TestSuggestionGenerator:
    """测试智能提示生成器"""

    def test_generate_undefined_symbol_suggestions(self):
        """测试未定义符号的建议生成"""
        generator = SuggestionGenerator()
        generator.register_symbol("计数器", "variable")
        generator.register_symbol("累加器", "variable")

        error = ZHCError("未定义的变量 '计數器'", error_code="E002")
        result = generator.generate_suggestions(error)

        # 检查是否有建议
        assert result.has_suggestions()

    def test_generate_type_mismatch_suggestions(self):
        """测试类型不匹配的建议生成"""
        generator = SuggestionGenerator()

        error = ZHCError(
            "类型不匹配: 期望 整数型，实际 字符串型",
            error_code="E001",
        )
        result = generator.generate_suggestions(error)

        # 检查是否有建议
        assert result.has_suggestions()

    def test_register_and_find_symbols(self):
        """测试符号注册和查找"""
        generator = SuggestionGenerator()

        generator.register_symbol("计数器", "variable", "整数型")
        generator.register_symbol("累加器", "variable", "整数型")

        # 模拟生成未定义符号错误
        error = ZHCError("未定义的变量 '计數器'", error_code="E002")
        result = generator.generate_suggestions(error)

        assert len(result.suggestions) > 0

    def test_documentation_links(self):
        """测试文档链接生成"""
        generator = SuggestionGenerator()

        error = ZHCError("类型不匹配", error_code="E001")
        result = generator.generate_suggestions(error)

        assert len(result.documentation_links) > 0


# ============================================================================
# 集成测试
# ============================================================================


class TestErrorEnhancementIntegration:
    """测试错误增强集成"""

    def test_full_error_flow(self):
        """测试完整的错误处理流程"""
        # 1. 创建错误
        error = ZHCError(
            "类型不匹配: 期望 整数型，实际 字符串型",
            error_code="E001",
            location=SourceLocation("test.zhc", 15, 8),
        )

        # 2. 生成解释
        explainer = ErrorExplainer()
        explanation = explainer.explain(error)

        # 3. 生成建议
        generator = SuggestionGenerator()
        suggestions = generator.generate_suggestions(error)

        # 4. 格式化输出
        formatter = ErrorFormatter(color_output=False)
        formatted_error = formatter.format_error(error)
        formatted_explanation = explainer.format_explanation(
            explanation, style="detailed"
        )

        # 验证
        assert "E001" in formatted_error
        assert formatted_explanation is not None
        assert "test.zhc:15:8" in formatted_error
        assert explanation.title == "类型不匹配"
        assert suggestions.has_suggestions()

    def test_error_code_list_command(self):
        """测试错误代码列表功能"""
        explainer = ErrorExplainer()

        codes = explainer.get_all_error_codes()

        # 验证包含主要类别的代码
        categories = {
            "类型错误": [],
            "作用域错误": [],
            "词法错误": [],
            "语法错误": [],
            "语义错误": [],
        }

        for code in codes:
            defn = ErrorCodeRegistry.get(code)
            if defn and defn.category in categories:
                categories[defn.category].append(code)

        # 验证各类别都有代码
        for category, codes_in_category in categories.items():
            assert len(codes_in_category) > 0, f"类别 {category} 没有错误代码"


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

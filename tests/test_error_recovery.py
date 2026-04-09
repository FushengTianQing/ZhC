"""
错误恢复机制单元测试

测试错误恢复策略、Parser 错误恢复、语义错误恢复等功能。

创建日期: 2026-04-10
最后更新: 2026-04-10
维护者: ZHC开发团队
"""

import pytest
from zhc.errors import ZHCError, SourceLocation, ErrorCollection
from zhc.errors.recovery import (
    RecoveryAction,
    RecoveryContext,
    ErrorRecoveryStrategy,
    CompilationAbortedError,
)
from zhc.errors.error_mode import ErrorMode, ErrorModeManager
from zhc.parser.parser_error_recovery import (
    ParserRecoveryContext,
    PlaceholderNode,
    ParserErrorRecovery,
    ParserErrorCollector,
)
from zhc.semantic.semantic_recovery import (
    PlaceholderSymbol,
    SemanticRecoveryContext,
    SemanticErrorRecovery,
    SemanticErrorCollector,
)


class TestRecoveryAction:
    """测试 RecoveryAction 枚举"""

    def test_recovery_actions(self):
        """测试恢复动作枚举值"""
        assert RecoveryAction.SKIP_TOKEN.value == 1
        assert RecoveryAction.SKIP_TO_SYNC.value == 2
        assert RecoveryAction.INSERT_TOKEN.value == 3
        assert RecoveryAction.REPLACE_TOKEN.value == 4
        assert RecoveryAction.CREATE_PLACEHOLDER.value == 5
        assert RecoveryAction.ABORT.value == 6


class TestRecoveryContext:
    """测试 RecoveryContext"""

    def test_recovery_context_creation(self):
        """测试恢复上下文创建"""
        context = RecoveryContext(
            tokens=[],
            current_idx=5,
            parser_state={"test": "value"},
            source_file="test.zhc",
        )

        assert context.current_idx == 5
        assert context.parser_state == {"test": "value"}
        assert context.source_file == "test.zhc"

    def test_recovery_context_methods(self):
        """测试恢复上下文方法"""
        context = RecoveryContext(tokens=["token1", "token2"], current_idx=0)

        assert context.get_current_token() == "token1"
        assert context.get_next_token() == "token2"

        context.current_idx = 1
        assert context.get_current_token() == "token2"
        assert context.get_next_token() is None


class TestErrorRecoveryStrategy:
    """测试 ErrorRecoveryStrategy"""

    def test_error_recovery_strategy_creation(self):
        """测试错误恢复策略创建"""
        errors = ErrorCollection()
        strategy = ErrorRecoveryStrategy(errors, max_errors=50)

        assert strategy.max_errors == 50
        assert strategy.errors is errors

    def test_max_errors_check(self):
        """测试最大错误数检查"""
        errors = ErrorCollection()
        strategy = ErrorRecoveryStrategy(errors, max_errors=2)

        # 添加 2 个错误
        errors.add(ZHCError("错误1", error_code="E001"))
        errors.add(ZHCError("错误2", error_code="E002"))

        context = RecoveryContext()
        error = ZHCError("错误3", error_code="E003")
        action = strategy.recover(error, context)

        assert action == RecoveryAction.ABORT

    def test_parser_error_recovery(self):
        """测试语法错误恢复策略"""
        errors = ErrorCollection()
        strategy = ErrorRecoveryStrategy(errors)

        # 测试缺失 Token
        error = ZHCError("缺失分号", error_code="PARSER_MISSING_TOKEN")
        context = RecoveryContext()
        action = strategy.recover(error, context)
        assert action == RecoveryAction.INSERT_TOKEN

        # 测试意外 Token
        error = ZHCError("意外的 Token", error_code="PARSER_UNEXPECTED_TOKEN")
        action = strategy.recover(error, context)
        assert action == RecoveryAction.SKIP_TO_SYNC

    def test_semantic_error_recovery(self):
        """测试语义错误恢复策略"""
        errors = ErrorCollection()
        strategy = ErrorRecoveryStrategy(errors)

        # 测试未定义符号
        error = ZHCError("未定义的变量", error_code="SEMANTIC_UNDEFINED_VARIABLE")
        context = RecoveryContext()
        action = strategy.recover(error, context)
        assert action == RecoveryAction.CREATE_PLACEHOLDER

        # 测试类型不匹配
        error = ZHCError("类型不匹配", error_code="SEMANTIC_TYPE_MISMATCH")
        action = strategy.recover(error, context)
        assert action == RecoveryAction.SKIP_TOKEN

    def test_find_sync_point(self):
        """测试查找同步点"""
        errors = ErrorCollection()
        strategy = ErrorRecoveryStrategy(errors)

        # 模拟 Token 列表
        tokens = [
            type("Token", (), {"type": "IDENTIFIER"})(),
            type("Token", (), {"type": "SEMICOLON"})(),
            type("Token", (), {"type": "IDENTIFIER"})(),
        ]

        sync_idx = strategy.find_sync_point(tokens, 0, "statement")
        assert sync_idx == 1

    def test_get_sync_type_for_error(self):
        """测试获取同步点类型"""
        errors = ErrorCollection()
        strategy = ErrorRecoveryStrategy(errors)

        error = ZHCError("声明错误", error_code="PARSER_INVALID_DECLARATION")
        assert strategy.get_sync_type_for_error(error) == "declaration"

        error = ZHCError("语句错误", error_code="PARSER_INVALID_STATEMENT")
        assert strategy.get_sync_type_for_error(error) == "statement"

        error = ZHCError("表达式错误", error_code="PARSER_INVALID_EXPRESSION")
        assert strategy.get_sync_type_for_error(error) == "expression"


class TestCompilationAbortedError:
    """测试 CompilationAbortedError"""

    def test_compilation_aborted_error(self):
        """测试编译中止异常"""
        error = CompilationAbortedError("错误数量过多")
        assert str(error) == "错误数量过多"
        assert error.message == "错误数量过多"


class TestErrorMode:
    """测试 ErrorMode 枚举"""

    def test_error_mode_values(self):
        """测试错误模式枚举值"""
        assert ErrorMode.STRICT.value == 1
        assert ErrorMode.LENIENT.value == 2
        assert ErrorMode.RECOVER.value == 3

    def test_error_mode_properties(self):
        """测试错误模式属性"""
        assert ErrorMode.STRICT.should_stop_on_error is True
        assert ErrorMode.LENIENT.should_stop_on_error is False
        assert ErrorMode.RECOVER.should_stop_on_error is False

        assert ErrorMode.STRICT.should_collect_all is False
        assert ErrorMode.LENIENT.should_collect_all is True
        assert ErrorMode.RECOVER.should_collect_all is True

        assert ErrorMode.STRICT.should_recover is False
        assert ErrorMode.LENIENT.should_recover is False
        assert ErrorMode.RECOVER.should_recover is True


class TestErrorModeManager:
    """测试 ErrorModeManager"""

    def test_error_mode_manager_creation(self):
        """测试错误模式管理器创建"""
        manager = ErrorModeManager(ErrorMode.LENIENT, max_errors=50)

        assert manager.mode == ErrorMode.LENIENT
        assert manager.config.max_errors == 50

    def test_error_mode_manager_handle_error(self):
        """测试错误处理"""
        manager = ErrorModeManager(ErrorMode.LENIENT, max_errors=10)

        error = ZHCError("测试错误", error_code="E001")
        manager.handle_error(error)

        assert manager.get_error_count() == 1
        assert manager.has_errors() is True

    def test_error_mode_manager_strict_mode(self):
        """测试严格模式"""
        manager = ErrorModeManager(ErrorMode.STRICT)

        error = ZHCError("测试错误", error_code="E001")

        with pytest.raises(ZHCError):
            manager.handle_error(error)

    def test_error_mode_manager_should_continue(self):
        """测试是否继续编译"""
        manager = ErrorModeManager(ErrorMode.LENIENT, max_errors=2)

        assert manager.should_continue() is True

        manager.handle_error(ZHCError("错误1", error_code="E001"))
        assert manager.should_continue() is True

        manager.handle_error(ZHCError("错误2", error_code="E002"))
        assert manager.should_continue() is False

    def test_error_mode_manager_abort(self):
        """测试中止编译"""
        manager = ErrorModeManager(ErrorMode.LENIENT)

        manager.abort("用户中止")
        assert manager.is_aborted() is True
        assert manager.should_continue() is False


class TestParserRecoveryContext:
    """测试 ParserRecoveryContext"""

    def test_parser_recovery_context_creation(self):
        """测试 Parser 恢复上下文创建"""
        context = ParserRecoveryContext(
            tokens=["token1", "token2"],
            current_idx=5,
            parser_state={"test": "value"},
            expected_tokens=["SEMICOLON"],
            recovery_depth=2,
            last_sync_point=3,
        )

        assert context.current_idx == 5
        assert context.parser_state == {"test": "value"}
        assert context.expected_tokens == ["SEMICOLON"]
        assert context.recovery_depth == 2
        assert context.last_sync_point == 3


class TestPlaceholderNode:
    """测试 PlaceholderNode"""

    def test_placeholder_node_creation(self):
        """测试占位节点创建"""
        node = PlaceholderNode(
            node_type="ERROR_NODE",
            line=10,
            column=5,
            error_message="语法错误",
            is_placeholder=True,
        )

        assert node.node_type == "ERROR_NODE"
        assert node.line == 10
        assert node.column == 5
        assert node.error_message == "语法错误"
        assert node.is_placeholder is True

    def test_placeholder_node_to_ast_node(self):
        """测试转换为 ASTNode"""
        node = PlaceholderNode(
            node_type="ERROR_NODE",
            line=10,
            column=5,
            error_message="语法错误",
        )

        ast_node = node.to_ast_node()
        assert ast_node.line == 10
        assert ast_node.column == 5
        assert ast_node.attributes.get("error_message") == "语法错误"
        assert ast_node.attributes.get("is_placeholder") is True


class TestParserErrorRecovery:
    """测试 ParserErrorRecovery"""

    def test_parser_error_recovery_creation(self):
        """测试 Parser 错误恢复创建"""
        errors = ErrorCollection()
        strategy = ErrorRecoveryStrategy(errors)
        parser = type("Parser", (), {"tokens": []})()

        recovery = ParserErrorRecovery(parser, strategy)
        assert recovery.parser is parser
        assert recovery.strategy is strategy
        assert recovery.get_recovery_count() == 0

    def test_parser_error_recovery_handle_error(self):
        """测试处理语法错误"""
        errors = ErrorCollection()
        strategy = ErrorRecoveryStrategy(errors)
        parser = type("Parser", (), {"tokens": []})()

        recovery = ParserErrorRecovery(parser, strategy)

        error = ZHCError(
            "缺失分号",
            location=SourceLocation(line=10, column=5),
            error_code="PARSER_MISSING_TOKEN",
        )

        # 模拟 Token 列表
        from zhc.parser.lexer import Token, TokenType

        tokens = [Token(TokenType.IDENTIFIER, "x", 10, 5)]

        result_node, new_idx = recovery.handle_error(error, tokens, 0)

        # 由于 PARSER_MISSING_TOKEN 会尝试插入 Token，但 context 中没有 expected_token
        # 所以会返回 SKIP_TOKEN，即 current_idx + 1
        assert recovery.get_recovery_count() == 1
        assert new_idx == 1  # 默认跳过 Token

    def test_parser_error_recovery_clear(self):
        """测试清空恢复状态"""
        errors = ErrorCollection()
        strategy = ErrorRecoveryStrategy(errors)
        parser = type("Parser", (), {"tokens": []})()

        recovery = ParserErrorRecovery(parser, strategy)

        error = ZHCError("错误", error_code="PARSER_ERROR")
        recovery.handle_error(error, [], 0)

        assert recovery.get_recovery_count() == 1

        recovery.clear()
        assert recovery.get_recovery_count() == 0


class TestParserErrorCollector:
    """测试 ParserErrorCollector"""

    def test_parser_error_collector_creation(self):
        """测试 Parser 错误收集器创建"""
        collector = ParserErrorCollector()

        assert collector.error_count() == 0
        assert collector.warning_count() == 0
        assert collector.has_errors() is False
        assert collector.has_warnings() is False

    def test_parser_error_collector_add_error(self):
        """测试添加错误"""
        collector = ParserErrorCollector()

        location = SourceLocation(line=10, column=5)
        error = collector.add_error(
            message="语法错误",
            location=location,
            error_code="E001",
        )

        assert collector.error_count() == 1
        assert collector.has_errors() is True
        assert error.message == "语法错误"

    def test_parser_error_collector_add_warning(self):
        """测试添加警告"""
        collector = ParserErrorCollector()

        warning = collector.add_warning(
            message="语法警告",
            error_code="W001",
        )

        assert collector.warning_count() == 1
        assert collector.has_warnings() is True
        assert warning.message == "语法警告"

    def test_parser_error_collector_get_errors_at_line(self):
        """测试获取指定行的错误"""
        collector = ParserErrorCollector()

        collector.add_error(
            message="错误1",
            location=SourceLocation(line=10, column=5),
        )
        collector.add_error(
            message="错误2",
            location=SourceLocation(line=10, column=15),
        )
        collector.add_error(
            message="错误3",
            location=SourceLocation(line=20, column=5),
        )

        errors_at_line_10 = collector.get_errors_at_line(10)
        assert len(errors_at_line_10) == 2

        errors_at_line_20 = collector.get_errors_at_line(20)
        assert len(errors_at_line_20) == 1

    def test_parser_error_collector_clear(self):
        """测试清空错误"""
        collector = ParserErrorCollector()

        collector.add_error(message="错误1")
        collector.add_warning(message="警告1")

        assert collector.error_count() == 1
        assert collector.warning_count() == 1

        collector.clear()

        assert collector.error_count() == 0
        assert collector.warning_count() == 0

    def test_parser_error_collector_summary(self):
        """测试获取错误摘要"""
        collector = ParserErrorCollector()

        assert collector.get_summary() == "无错误或警告"

        collector.add_error(message="错误1")
        collector.add_warning(message="警告1")

        summary = collector.get_summary()
        assert "1 个错误" in summary
        assert "1 个警告" in summary


class TestPlaceholderSymbol:
    """测试 PlaceholderSymbol"""

    def test_placeholder_symbol_creation(self):
        """测试占位符号创建"""
        symbol = PlaceholderSymbol(
            name="test_var",
            symbol_type="变量",
            data_type="整数型",
            is_placeholder=True,
            definition_location="10:5",
        )

        assert symbol.name == "test_var"
        assert symbol.symbol_type == "变量"
        assert symbol.data_type == "整数型"
        assert symbol.is_placeholder is True
        assert symbol.definition_location == "10:5"

    def test_placeholder_symbol_to_symbol(self):
        """测试转换为 Symbol"""
        symbol = PlaceholderSymbol(
            name="test_var",
            symbol_type="变量",
            data_type="整数型",
            definition_location="10:5",
        )

        ast_symbol = symbol.to_symbol()
        assert ast_symbol.name == "test_var"
        assert ast_symbol.symbol_type == "变量"
        assert ast_symbol.data_type == "整数型"
        assert ast_symbol.is_defined is False


class TestSemanticRecoveryContext:
    """测试 SemanticRecoveryContext"""

    def test_semantic_recovery_context_creation(self):
        """测试语义恢复上下文创建"""
        context = SemanticRecoveryContext(
            current_function="main",
            current_struct="MyStruct",
            current_scope=2,
            loop_depth=1,
            symbol_table={"x": "整数型"},
            type_hints={"y": "浮点型"},
            expected_types={"z": "字符串型"},
        )

        assert context.current_function == "main"
        assert context.current_struct == "MyStruct"
        assert context.current_scope == 2
        assert context.loop_depth == 1
        assert context.symbol_table == {"x": "整数型"}
        assert context.type_hints == {"y": "浮点型"}
        assert context.expected_types == {"z": "字符串型"}


class TestSemanticErrorRecovery:
    """测试 SemanticErrorRecovery"""

    def test_semantic_error_recovery_creation(self):
        """测试语义错误恢复创建"""
        errors = ErrorCollection()
        strategy = ErrorRecoveryStrategy(errors)
        analyzer = type("Analyzer", (), {})()

        recovery = SemanticErrorRecovery(analyzer, strategy)
        assert recovery.analyzer is analyzer
        assert recovery.strategy is strategy
        assert recovery.get_recovery_count() == 0

    def test_semantic_error_recovery_handle_undefined_symbol(self):
        """测试处理未定义符号"""
        errors = ErrorCollection()
        strategy = ErrorRecoveryStrategy(errors)
        analyzer = type("Analyzer", (), {})()

        recovery = SemanticErrorRecovery(analyzer, strategy)

        node = type("Node", (), {"line": 10, "column": 5})()
        placeholder = recovery.handle_undefined_symbol("x", node, "变量")

        assert placeholder.name == "x"
        assert placeholder.symbol_type == "变量"
        assert placeholder.data_type == "未知"
        assert placeholder.is_placeholder is True
        assert recovery.get_recovery_count() == 1

    def test_semantic_error_recovery_handle_type_mismatch(self):
        """测试处理类型不匹配"""
        errors = ErrorCollection()
        strategy = ErrorRecoveryStrategy(errors)
        analyzer = type("Analyzer", (), {})()

        recovery = SemanticErrorRecovery(analyzer, strategy)

        node = type("Node", (), {"line": 10, "column": 5})()

        # 数值类型不匹配
        result_type = recovery.handle_type_mismatch("整数型", "浮点型", node)
        assert result_type == "整数型"  # 返回期望类型

        # 指针类型不匹配
        result_type = recovery.handle_type_mismatch("int*", "float*", node)
        assert result_type == "int*"

        # 不兼容类型
        result_type = recovery.handle_type_mismatch("字符串型", "整数型", node)
        assert result_type == "未知"

        assert recovery.get_recovery_count() == 3

    def test_semantic_error_recovery_handle_duplicate_definition(self):
        """测试处理重复定义"""
        errors = ErrorCollection()
        strategy = ErrorRecoveryStrategy(errors)
        analyzer = type("Analyzer", (), {})()

        recovery = SemanticErrorRecovery(analyzer, strategy)

        node = type("Node", (), {"line": 10, "column": 5})()
        recovery.handle_duplicate_definition("x", node, "5:10")

        assert recovery.get_recovery_count() == 1

    def test_semantic_error_recovery_handle_invalid_operation(self):
        """测试处理无效操作"""
        errors = ErrorCollection()
        strategy = ErrorRecoveryStrategy(errors)
        analyzer = type("Analyzer", (), {})()

        recovery = SemanticErrorRecovery(analyzer, strategy)

        node = type("Node", (), {"line": 10, "column": 5})()

        # 算术操作
        result_type = recovery.handle_invalid_operation("+", "整数型", "浮点型", node)
        assert result_type == "浮点型"

        # 比较操作
        result_type = recovery.handle_invalid_operation("==", "整数型", "整数型", node)
        assert result_type == "布尔型"

        # 逻辑操作
        result_type = recovery.handle_invalid_operation("&&", "布尔型", "布尔型", node)
        assert result_type == "布尔型"

        # 未知操作
        result_type = recovery.handle_invalid_operation("??", "整数型", "整数型", node)
        assert result_type == "未知"

    def test_semantic_error_recovery_get_placeholder_symbol(self):
        """测试获取占位符号"""
        errors = ErrorCollection()
        strategy = ErrorRecoveryStrategy(errors)
        analyzer = type("Analyzer", (), {})()

        recovery = SemanticErrorRecovery(analyzer, strategy)

        node = type("Node", (), {"line": 10, "column": 5})()
        recovery.handle_undefined_symbol("x", node, "变量")

        placeholder = recovery.get_placeholder_symbol("x")
        assert placeholder is not None
        assert placeholder.name == "x"

        placeholder = recovery.get_placeholder_symbol("y")
        assert placeholder is None

    def test_semantic_error_recovery_clear_placeholders(self):
        """测试清空占位符号"""
        errors = ErrorCollection()
        strategy = ErrorRecoveryStrategy(errors)
        analyzer = type("Analyzer", (), {})()

        recovery = SemanticErrorRecovery(analyzer, strategy)

        node = type("Node", (), {"line": 10, "column": 5})()
        recovery.handle_undefined_symbol("x", node, "变量")
        recovery.handle_undefined_symbol("y", node, "变量")

        assert len(recovery._placeholder_symbols) == 2

        recovery.clear_placeholders()
        assert len(recovery._placeholder_symbols) == 0

    def test_semantic_error_recovery_create_recovery_context(self):
        """测试创建恢复上下文"""
        errors = ErrorCollection()
        strategy = ErrorRecoveryStrategy(errors)
        analyzer = type("Analyzer", (), {})()

        recovery = SemanticErrorRecovery(analyzer, strategy)

        context = recovery.create_recovery_context(
            current_function="main",
            current_struct="MyStruct",
        )

        assert context.current_function == "main"
        assert context.current_struct == "MyStruct"


class TestSemanticErrorCollector:
    """测试 SemanticErrorCollector"""

    def test_semantic_error_collector_creation(self):
        """测试语义错误收集器创建"""
        collector = SemanticErrorCollector()

        assert collector.error_count() == 0
        assert collector.warning_count() == 0
        assert collector.has_errors() is False
        assert collector.has_warnings() is False

    def test_semantic_error_collector_add_error(self):
        """测试添加错误"""
        collector = SemanticErrorCollector()

        location = SourceLocation(line=10, column=5)
        error = collector.add_error(
            message="语义错误",
            location=location,
            error_code="E001",
        )

        assert collector.error_count() == 1
        assert collector.has_errors() is True
        assert error.message == "语义错误"

    def test_semantic_error_collector_add_warning(self):
        """测试添加警告"""
        collector = SemanticErrorCollector()

        warning = collector.add_warning(
            message="语义警告",
            error_code="W001",
        )

        assert collector.warning_count() == 1
        assert collector.has_warnings() is True
        assert warning.message == "语义警告"

    def test_semantic_error_collector_get_errors_at(self):
        """测试获取指定位置的错误"""
        collector = SemanticErrorCollector()

        collector.add_error(
            message="错误1",
            location=SourceLocation(line=10, column=5),
        )
        collector.add_error(
            message="错误2",
            location=SourceLocation(line=10, column=5),
        )
        collector.add_error(
            message="错误3",
            location=SourceLocation(line=20, column=5),
        )

        errors_at_10_5 = collector.get_errors_at(10, 5)
        assert len(errors_at_10_5) == 2

        errors_at_20_5 = collector.get_errors_at(20, 5)
        assert len(errors_at_20_5) == 1

    def test_semantic_error_collector_clear(self):
        """测试清空错误"""
        collector = SemanticErrorCollector()

        collector.add_error(message="错误1")
        collector.add_warning(message="警告1")

        assert collector.error_count() == 1
        assert collector.warning_count() == 1

        collector.clear()

        assert collector.error_count() == 0
        assert collector.warning_count() == 0

    def test_semantic_error_collector_summary(self):
        """测试获取错误摘要"""
        collector = SemanticErrorCollector()

        assert collector.get_summary() == "无错误或警告"

        collector.add_error(message="错误1")
        collector.add_warning(message="警告1")

        summary = collector.get_summary()
        assert "1 个错误" in summary
        assert "1 个警告" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

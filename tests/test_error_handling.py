"""
异常处理单元测试

测试 ZHC 编译器统一异常处理机制。

创建日期: 2026-04-07
最后更新: 2026-04-07
维护者: ZHC开发团队
"""

import pytest
from zhc.errors import (
    SourceLocation,
    ZHCError,
    ErrorCollection,
    LexerError,
    ParserError,
    SemanticError,
    CodeGenerationError,
    illegal_character,
    unterminated_string,
    missing_token,
    unexpected_token,
    type_mismatch,
    undefined_variable,
    unsupported_feature,
)


# ============================================================================
# SourceLocation 测试
# ============================================================================

class TestSourceLocation:
    """测试源码位置信息类"""
    
    def test_basic_location(self):
        """测试基本位置信息"""
        loc = SourceLocation(file_path="test.zhc", line=10, column=5)
        assert loc.file_path == "test.zhc"
        assert loc.line == 10
        assert loc.column == 5
        assert str(loc) == "test.zhc:10:5"
    
    def test_location_without_file(self):
        """测试无文件路径的位置信息"""
        loc = SourceLocation(line=10, column=5)
        assert loc.file_path is None
        assert str(loc) == "行 10, 列 5"
    
    def test_multi_line_location(self):
        """测试多行位置信息"""
        loc = SourceLocation(
            file_path="test.zhc",
            line=10,
            column=5,
            end_line=12,
            end_column=8
        )
        assert loc.end_line == 12
        assert loc.end_column == 8
        assert str(loc) == "test.zhc:10:5-12:8"
    
    def test_to_dict(self):
        """测试转换为字典"""
        loc = SourceLocation(file_path="test.zhc", line=10, column=5)
        data = loc.to_dict()
        assert data["file_path"] == "test.zhc"
        assert data["line"] == 10
        assert data["column"] == 5


# ============================================================================
# ZHCError 测试
# ============================================================================

class TestZHCError:
    """测试异常基类"""
    
    def test_basic_error(self):
        """测试基本错误"""
        error = ZHCError("测试错误")
        assert error.message == "测试错误"
        assert str(error) == "错误: 测试错误"
    
    def test_error_with_location(self):
        """测试带位置的错误"""
        loc = SourceLocation(file_path="test.zhc", line=10, column=5)
        error = ZHCError("测试错误", location=loc)
        assert error.location == loc
        assert "test.zhc:10:5" in str(error)
    
    def test_error_with_code(self):
        """测试带错误代码的错误"""
        error = ZHCError("测试错误", error_code="E001")
        assert error.error_code == "E001"
        assert "错误[E001]" in str(error)
    
    def test_error_with_suggestion(self):
        """测试带建议的错误"""
        error = ZHCError("测试错误", suggestion="请检查代码")
        assert error.suggestion == "请检查代码"
        assert "建议: 请检查代码" in str(error)
    
    def test_error_with_context(self):
        """测试带上下文的错误"""
        error = ZHCError("测试错误", context="整数 x = @")
        assert error.context == "整数 x = @"
        assert "上下文: 整数 x = @" in str(error)
    
    def test_error_severity(self):
        """测试错误严重程度"""
        error = ZHCError("测试错误", severity=ZHCError.SEVERITY_WARNING)
        assert error.is_warning()
        assert not error.is_error()
        assert "警告" in str(error)
    
    def test_to_dict(self):
        """测试转换为字典"""
        loc = SourceLocation(file_path="test.zhc", line=10, column=5)
        error = ZHCError(
            "测试错误",
            location=loc,
            error_code="E001",
            suggestion="请检查代码"
        )
        data = error.to_dict()
        assert data["message"] == "测试错误"
        assert data["error_code"] == "E001"
        assert data["suggestion"] == "请检查代码"
        assert data["location"]["file_path"] == "test.zhc"
    
    def test_repr(self):
        """测试调试表示"""
        error = ZHCError("测试错误", error_code="E001")
        assert "ZHCError" in repr(error)
        assert "E001" in repr(error)


# ============================================================================
# LexerError 测试
# ============================================================================

class TestLexerError:
    """测试词法分析异常"""
    
    def test_basic_lexer_error(self):
        """测试基本词法错误"""
        error = LexerError("非法字符")
        assert error.message == "非法字符"
        assert isinstance(error, ZHCError)
    
    def test_lexer_error_with_character(self):
        """测试带字符信息的词法错误"""
        error = LexerError("非法字符", character='@')
        assert error.character == '@'
    
    def test_illegal_character_factory(self):
        """测试非法字符工厂函数"""
        loc = SourceLocation(file_path="test.zhc", line=10, column=5)
        error = illegal_character('@', location=loc)
        assert error.message == "非法字符 '@'"
        assert error.character == '@'
        assert error.error_code == "L001"
    
    def test_unterminated_string_factory(self):
        """测试字符串未闭合工厂函数"""
        loc = SourceLocation(file_path="test.zhc", line=10, column=5)
        error = unterminated_string(location=loc)
        assert error.message == "字符串未闭合"
        assert error.error_code == "L002"


# ============================================================================
# ParserError 测试
# ============================================================================

class TestParserError:
    """测试语法分析异常"""
    
    def test_basic_parser_error(self):
        """测试基本语法错误"""
        error = ParserError("缺少分号")
        assert error.message == "缺少分号"
        assert isinstance(error, ZHCError)
    
    def test_parser_error_with_expected_tokens(self):
        """测试带期望token的语法错误"""
        error = ParserError(
            "缺少分号",
            expected_tokens=["分号"],
            actual_token="换行"
        )
        assert error.expected_tokens == ["分号"]
        assert error.actual_token == "换行"
        assert "期望: 分号" in str(error)
        assert "实际: 换行" in str(error)
    
    def test_missing_token_factory(self):
        """测试缺少token工厂函数"""
        loc = SourceLocation(file_path="test.zhc", line=10, column=5)
        error = missing_token("分号", location=loc, actual="换行")
        assert error.message == "缺少 分号"
        assert error.error_code == "P001"
        assert error.expected_tokens == ["分号"]
    
    def test_unexpected_token_factory(self):
        """测试意外token工厂函数"""
        loc = SourceLocation(file_path="test.zhc", line=10, column=5)
        error = unexpected_token("换行", location=loc, expected=["分号"])
        assert error.message == "意外的 换行"
        assert error.error_code == "P002"
        assert error.actual_token == "换行"


# ============================================================================
# SemanticError 测试
# ============================================================================

class TestSemanticError:
    """测试语义分析异常"""
    
    def test_basic_semantic_error(self):
        """测试基本语义错误"""
        error = SemanticError("类型不匹配")
        assert error.message == "类型不匹配"
        assert isinstance(error, ZHCError)
    
    def test_semantic_error_with_types(self):
        """测试带类型信息的语义错误"""
        error = SemanticError(
            "类型不匹配",
            expected_type="整数型",
            actual_type="浮点型"
        )
        assert error.expected_type == "整数型"
        assert error.actual_type == "浮点型"
        assert "期望类型: 整数型" in str(error)
        assert "实际类型: 浮点型" in str(error)
    
    def test_type_mismatch_factory(self):
        """测试类型不匹配工厂函数"""
        loc = SourceLocation(file_path="test.zhc", line=10, column=5)
        error = type_mismatch("整数型", "浮点型", location=loc)
        assert "类型不匹配" in error.message
        assert error.error_code == "S001"
        assert error.expected_type == "整数型"
        assert error.actual_type == "浮点型"
    
    def test_undefined_variable_factory(self):
        """测试未定义变量工厂函数"""
        loc = SourceLocation(file_path="test.zhc", line=10, column=5)
        error = undefined_variable("x", location=loc)
        assert error.message == "未定义的变量 'x'"
        assert error.error_code == "S011"
        assert error.symbol_name == "x"


# ============================================================================
# CodeGenerationError 测试
# ============================================================================

class TestCodeGenerationError:
    """测试代码生成异常"""
    
    def test_basic_codegen_error(self):
        """测试基本代码生成错误"""
        error = CodeGenerationError("不支持的内联汇编")
        assert error.message == "不支持的内联汇编"
        assert isinstance(error, ZHCError)
    
    def test_codegen_error_with_backend(self):
        """测试带后端信息的代码生成错误"""
        error = CodeGenerationError(
            "不支持的内联汇编",
            target_backend="LLVM",
            feature_name="内联汇编"
        )
        assert error.target_backend == "LLVM"
        assert error.feature_name == "内联汇编"
        assert "目标后端: LLVM" in str(error)
        assert "特性: 内联汇编" in str(error)
    
    def test_unsupported_feature_factory(self):
        """测试不支持特性工厂函数"""
        loc = SourceLocation(file_path="test.zhc", line=10, column=5)
        error = unsupported_feature("内联汇编", target_backend="LLVM", location=loc)
        assert "不支持的特性" in error.message
        assert error.error_code == "C011"
        assert error.feature_name == "内联汇编"


# ============================================================================
# ErrorCollection 测试
# ============================================================================

class TestErrorCollection:
    """测试错误集合管理器"""
    
    def test_empty_collection(self):
        """测试空错误集合"""
        errors = ErrorCollection()
        assert not errors.has_errors()
        assert not errors.has_warnings()
        assert errors.error_count() == 0
        assert errors.total_count() == 0
        assert errors.summary() == "无错误或警告"
    
    def test_add_error(self):
        """测试添加错误"""
        errors = ErrorCollection()
        error = ZHCError("测试错误", severity=ZHCError.SEVERITY_ERROR)
        errors.add(error)
        assert errors.has_errors()
        assert errors.error_count() == 1
        assert errors.total_count() == 1
    
    def test_add_warning(self):
        """测试添加警告"""
        errors = ErrorCollection()
        warning = ZHCError("测试警告", severity=ZHCError.SEVERITY_WARNING)
        errors.add(warning)
        assert errors.has_warnings()
        assert errors.warning_count() == 1
        assert not errors.has_errors()
    
    def test_add_multiple_errors(self):
        """测试添加多个错误"""
        errors = ErrorCollection()
        errors.add(ZHCError("错误1", severity=ZHCError.SEVERITY_ERROR))
        errors.add(ZHCError("错误2", severity=ZHCError.SEVERITY_ERROR))
        errors.add(ZHCError("警告1", severity=ZHCError.SEVERITY_WARNING))
        assert errors.error_count() == 2
        assert errors.warning_count() == 1
        assert errors.total_count() == 3
        assert "2 个错误" in errors.summary()
        assert "1 个警告" in errors.summary()
    
    def test_get_errors(self):
        """测试获取错误列表"""
        errors = ErrorCollection()
        error1 = ZHCError("错误1", severity=ZHCError.SEVERITY_ERROR)
        error2 = ZHCError("错误2", severity=ZHCError.SEVERITY_ERROR)
        errors.add(error1)
        errors.add(error2)
        error_list = errors.get_errors()
        assert len(error_list) == 2
        assert error1 in error_list
        assert error2 in error_list
    
    def test_detailed_report(self):
        """测试详细报告"""
        errors = ErrorCollection()
        errors.add(ZHCError("错误1", severity=ZHCError.SEVERITY_ERROR))
        errors.add(ZHCError("警告1", severity=ZHCError.SEVERITY_WARNING))
        report = errors.detailed_report()
        assert "编译错误报告" in report
        assert "错误:" in report
        assert "警告:" in report
    
    def test_to_dict(self):
        """测试转换为字典"""
        errors = ErrorCollection()
        errors.add(ZHCError("错误1", severity=ZHCError.SEVERITY_ERROR))
        errors.add(ZHCError("警告1", severity=ZHCError.SEVERITY_WARNING))
        data = errors.to_dict()
        assert data["counts"]["errors"] == 1
        assert data["counts"]["warnings"] == 1
        assert len(data["errors"]) == 1
        assert len(data["warnings"]) == 1
    
    def test_clear(self):
        """测试清空错误"""
        errors = ErrorCollection()
        errors.add(ZHCError("错误1", severity=ZHCError.SEVERITY_ERROR))
        errors.clear()
        assert errors.error_count() == 0
        assert errors.total_count() == 0
    
    def test_iteration(self):
        """测试迭代"""
        errors = ErrorCollection()
        errors.add(ZHCError("错误1", severity=ZHCError.SEVERITY_ERROR))
        errors.add(ZHCError("警告1", severity=ZHCError.SEVERITY_WARNING))
        count = 0
        for error in errors:
            count += 1
        assert count == 2
    
    def test_len(self):
        """测试长度"""
        errors = ErrorCollection()
        errors.add(ZHCError("错误1", severity=ZHCError.SEVERITY_ERROR))
        errors.add(ZHCError("警告1", severity=ZHCError.SEVERITY_WARNING))
        assert len(errors) == 2
    
    def test_repr(self):
        """测试调试表示"""
        errors = ErrorCollection()
        errors.add(ZHCError("错误1", severity=ZHCError.SEVERITY_ERROR))
        errors.add(ZHCError("警告1", severity=ZHCError.SEVERITY_WARNING))
        assert "ErrorCollection" in repr(errors)
        assert "errors=1" in repr(errors)
        assert "warnings=1" in repr(errors)


# ============================================================================
# 异常继承关系测试
# ============================================================================

class TestExceptionHierarchy:
    """测试异常类继承关系"""
    
    def test_lexer_error_inherits_zhc_error(self):
        """测试 LexerError 继承自 ZHCError"""
        error = LexerError("测试")
        assert isinstance(error, ZHCError)
        assert isinstance(error, Exception)
    
    def test_parser_error_inherits_zhc_error(self):
        """测试 ParserError 继承自 ZHCError"""
        error = ParserError("测试")
        assert isinstance(error, ZHCError)
        assert isinstance(error, Exception)
    
    def test_semantic_error_inherits_zhc_error(self):
        """测试 SemanticError 继承自 ZHCError"""
        error = SemanticError("测试")
        assert isinstance(error, ZHCError)
        assert isinstance(error, Exception)
    
    def test_codegen_error_inherits_zhc_error(self):
        """测试 CodeGenerationError 继承自 ZHCError"""
        error = CodeGenerationError("测试")
        assert isinstance(error, ZHCError)
        assert isinstance(error, Exception)
    
    def test_catch_with_base_class(self):
        """测试用基类捕获所有异常"""
        errors = [
            LexerError("词法错误"),
            ParserError("语法错误"),
            SemanticError("语义错误"),
            CodeGenerationError("代码生成错误"),
        ]
        
        for error in errors:
            try:
                raise error
            except ZHCError as e:
                assert isinstance(e, ZHCError)


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
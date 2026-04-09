"""
ZHC 编译器统一异常处理模块

提供完整的异常类层次结构，用于编译器各阶段的错误处理。

模块结构:
- base.py: 异常基类和错误集合管理器
- error_codes.py: 错误代码注册表
- lexer_error.py: 词法分析异常
- parser_error.py: 语法分析异常
- semantic_error.py: 语义分析异常
- codegen_error.py: 代码生成异常
- source_context.py: 源码上下文提取器
- error_formatter.py: 错误格式化器

使用示例:
    >>> from zhc.errors import LexerError, ParserError, SemanticError
    >>> from zhc.errors import SourceLocation, ErrorCollection
    >>> from zhc.errors import SourceContextExtractor, ErrorFormatter
    >>>
    >>> # 创建错误
    >>> error = LexerError(
    ...     "非法字符 '@'",
    ...     location=SourceLocation("test.zhc", 10, 5),
    ...     error_code="L001"
    ... )
    >>>
    >>> # 收集错误
    >>> errors = ErrorCollection()
    >>> errors.add(error)
    >>> print(errors.summary())

    >>> # 使用上下文提取器
    >>> extractor = SourceContextExtractor({"test.zhc": "整数型 x = 1;"})
    >>> context = extractor.get_context(error.location)
    >>>
    >>> # 格式化错误
    >>> formatter = ErrorFormatter()
    >>> print(formatter.format_error(error, context))

创建日期: 2026-04-07
最后更新: 2026-04-09
维护者: ZHC开发团队
"""

# 导入基类
from .base import (
    SourceLocation,
    ZHCError,
    ErrorCollection,
)

# 导入源码上下文
from .source_context import (
    SourceContext,
    LineInfo,
    SourceContextExtractor,
)

# 导入错误格式化器
from .error_formatter import (
    ErrorFormatter,
    ErrorPrinter,
)

# 导入错误代码注册表
from .error_codes import (
    ErrorCodeDefinition,
    ErrorCodeRegistry,
)

# 导入词法分析异常
from .lexer_error import (
    LexerError,
    LEXER_ILLEGAL_CHARACTER,
    LEXER_UNTERMINATED_STRING,
    LEXER_UNTERMINATED_CHAR,
    LEXER_INVALID_ESCAPE_SEQUENCE,
    LEXER_UNTERMINATED_COMMENT,
    LEXER_INVALID_NUMBER_FORMAT,
    LEXER_NUMBER_OUT_OF_RANGE,
    LEXER_INVALID_FLOAT_FORMAT,
    LEXER_INVALID_HEX_FORMAT,
    LEXER_INVALID_BINARY_FORMAT,
    LEXER_INVALID_IDENTIFIER,
    LEXER_RESERVED_KEYWORD,
    LEXER_INVALID_ENCODING,
    LEXER_BOM_ERROR,
    illegal_character,
    unterminated_string,
    unterminated_comment,
    unterminated_char,
    invalid_number_format,
    invalid_identifier,
    invalid_escape_sequence,
)

# 导入语法分析异常
from .parser_error import (
    ParserError,
    PARSER_MISSING_TOKEN,
    PARSER_UNEXPECTED_TOKEN,
    PARSER_EXPECTED_IDENTIFIER,
    PARSER_EXPECTED_TYPE,
    PARSER_INVALID_DECLARATION,
    PARSER_DUPLICATE_DECLARATION,
    PARSER_MISSING_INITIALIZER,
    PARSER_INVALID_INITIALIZER,
    PARSER_INVALID_STATEMENT,
    PARSER_MISSING_SEMICOLON,
    PARSER_MISSING_BRACE,
    PARSER_UNBALANCED_PARENS,
    PARSER_UNBALANCED_BRACES,
    PARSER_INVALID_EXPRESSION,
    PARSER_MISSING_OPERAND,
    PARSER_INVALID_OPERATOR,
    PARSER_INVALID_FUNCTION,
    PARSER_MISSING_RETURN,
    PARSER_INVALID_PARAMETER,
    PARSER_INVALID_CONTROL_FLOW,
    PARSER_BREAK_OUTSIDE_LOOP,
    PARSER_CONTINUE_OUTSIDE_LOOP,
    missing_token,
    unexpected_token,
    invalid_statement,
    missing_semicolon,
    unbalanced_braces,
)

# 导入语义分析异常
from .semantic_error import (
    SemanticError,
    SEMANTIC_TYPE_MISMATCH,
    SEMANTIC_INVALID_TYPE,
    SEMANTIC_INCOMPATIBLE_TYPES,
    SEMANTIC_MISSING_TYPE,
    SEMANTIC_INVALID_CAST,
    SEMANTIC_UNDEFINED_VARIABLE,
    SEMANTIC_DUPLICATE_VARIABLE,
    SEMANTIC_VARIABLE_NOT_INITIALIZED,
    SEMANTIC_CONSTANT_MODIFICATION,
    SEMANTIC_UNDEFINED_FUNCTION,
    SEMANTIC_DUPLICATE_FUNCTION,
    SEMANTIC_INVALID_RETURN_TYPE,
    SEMANTIC_PARAMETER_MISMATCH,
    SEMANTIC_MISSING_RETURN,
    SEMANTIC_SCOPE_ERROR,
    SEMANTIC_VARIABLE_OUT_OF_SCOPE,
    SEMANTIC_INVALID_ACCESS,
    SEMANTIC_UNDEFINED_STRUCT,
    SEMANTIC_DUPLICATE_STRUCT,
    SEMANTIC_INVALID_MEMBER,
    SEMANTIC_MISSING_MEMBER,
    SEMANTIC_INVALID_ARRAY_INDEX,
    SEMANTIC_ARRAY_INDEX_OUT_OF_RANGE,
    SEMANTIC_INVALID_ARRAY_SIZE,
    SEMANTIC_NULL_POINTER,
    SEMANTIC_INVALID_POINTER_OPERATION,
    SEMANTIC_POINTER_TYPE_MISMATCH,
    type_mismatch,
    undefined_variable,
    undefined_function,
    duplicate_definition,
    invalid_member_access,
    parameter_mismatch,
)

# 导入代码生成异常
from .codegen_error import (
    CodeGenerationError,
    CODEGEN_INVALID_IR,
    CODEGEN_IR_CONVERSION_FAILED,
    CODEGEN_MISSING_IR_NODE,
    CODEGEN_IR_TYPE_MISMATCH,
    CODEGEN_UNSUPPORTED_FEATURE,
    CODEGEN_BACKEND_ERROR,
    CODEGEN_LINKER_ERROR,
    CODEGEN_OPTIMIZATION_ERROR,
    CODEGEN_UNSUPPORTED_PLATFORM,
    CODEGEN_PLATFORM_SPECIFIC_ERROR,
    CODEGEN_ABI_ERROR,
    CODEGEN_MEMORY_ALLOCATION_ERROR,
    CODEGEN_STACK_OVERFLOW,
    CODEGEN_INVALID_MEMORY_ACCESS,
    CODEGEN_OUTPUT_ERROR,
    CODEGEN_FILE_WRITE_ERROR,
    CODEGEN_INVALID_OUTPUT_FORMAT,
    unsupported_feature,
    backend_error,
    ir_conversion_failed,
    unsupported_platform,
    file_write_error,
)

# 导入 Pipeline 异常
from .pipeline_error import (
    PipelineError,
    ErrorType,  # 向后兼容枚举
    PIPELINE_FILE_NOT_FOUND,
    PIPELINE_FILE_READ_ERROR,
    PIPELINE_FILE_WRITE_ERROR,
    PIPELINE_SYNTAX_MISSING_BRACE,
    PIPELINE_SYNTAX_UNEXPECTED_TOKEN,
    PIPELINE_SYNTAX_INVALID_MODULE_DECL,
    PIPELINE_SYNTAX_INVALID_IMPORT_STMT,
    PIPELINE_SYNTAX_INVALID_VISIBILITY,
    PIPELINE_SEMANTIC_DUPLICATE_SYMBOL,
    PIPELINE_SEMANTIC_UNDEFINED_SYMBOL,
    PIPELINE_SEMANTIC_TYPE_MISMATCH,
    PIPELINE_SEMANTIC_INVALID_RETURN,
    PIPELINE_SCOPE_VIOLATION,
    PIPELINE_SCOPE_OUT_OF_SCOPE,
    PIPELINE_SCOPE_INVALID_ACCESS,
    PIPELINE_DEPENDENCY_CYCLE,
    PIPELINE_DEPENDENCY_MISSING_MODULE,
    PIPELINE_DEPENDENCY_VERSION_CONFLICT,
    PIPELINE_COMPILE_CONVERSION_FAILED,
    PIPELINE_COMPILE_UNSUPPORTED_FEATURE,
    file_not_found,
    file_read_error,
    dependency_cycle,
    missing_module,
    duplicate_symbol,
    unsupported_feature as pipeline_unsupported_feature,  # noqa: F401
)

# 导入错误恢复机制
from .recovery import (
    RecoveryAction,
    RecoveryContext,
    ErrorRecoveryStrategy,
    CompilationAbortedError,
)

# 导入错误模式管理
from .error_mode import (
    ErrorMode,
    ErrorModeConfig,
    ErrorModeManager,
    ErrorRecoveryContext,
)

# 导入智能提示生成器
from .suggestions import (
    Suggestion,
    SuggestionResult,
    SuggestionGenerator,
    ErrorEnhancer,
)


# ============================================================================
# 版本信息
# ============================================================================

__version__ = "1.0.0"
__author__ = "ZHC开发团队"


# ============================================================================
# 导出公共API
# ============================================================================

__all__ = [
    # 基类
    "SourceLocation",
    "ZHCError",
    "ErrorCollection",
    # 源码上下文
    "SourceContext",
    "LineInfo",
    "SourceContextExtractor",
    # 错误格式化
    "ErrorFormatter",
    "ErrorPrinter",
    # 错误代码注册表
    "ErrorCodeDefinition",
    "ErrorCodeRegistry",
    # 词法分析异常
    "LexerError",
    "LEXER_ILLEGAL_CHARACTER",
    "LEXER_UNTERMINATED_STRING",
    "LEXER_UNTERMINATED_CHAR",
    "LEXER_INVALID_ESCAPE_SEQUENCE",
    "LEXER_UNTERMINATED_COMMENT",
    "LEXER_INVALID_NUMBER_FORMAT",
    "LEXER_NUMBER_OUT_OF_RANGE",
    "LEXER_INVALID_FLOAT_FORMAT",
    "LEXER_INVALID_HEX_FORMAT",
    "LEXER_INVALID_BINARY_FORMAT",
    "LEXER_INVALID_IDENTIFIER",
    "LEXER_RESERVED_KEYWORD",
    "LEXER_INVALID_ENCODING",
    "LEXER_BOM_ERROR",
    "illegal_character",
    "unterminated_string",
    "unterminated_comment",
    "unterminated_char",
    "invalid_number_format",
    "invalid_identifier",
    "invalid_escape_sequence",
    # 语法分析异常
    "ParserError",
    "PARSER_MISSING_TOKEN",
    "PARSER_UNEXPECTED_TOKEN",
    "PARSER_EXPECTED_IDENTIFIER",
    "PARSER_EXPECTED_TYPE",
    "PARSER_INVALID_DECLARATION",
    "PARSER_DUPLICATE_DECLARATION",
    "PARSER_MISSING_INITIALIZER",
    "PARSER_INVALID_INITIALIZER",
    "PARSER_INVALID_STATEMENT",
    "PARSER_MISSING_SEMICOLON",
    "PARSER_MISSING_BRACE",
    "PARSER_UNBALANCED_PARENS",
    "PARSER_UNBALANCED_BRACES",
    "PARSER_INVALID_EXPRESSION",
    "PARSER_MISSING_OPERAND",
    "PARSER_INVALID_OPERATOR",
    "PARSER_INVALID_FUNCTION",
    "PARSER_MISSING_RETURN",
    "PARSER_INVALID_PARAMETER",
    "PARSER_INVALID_CONTROL_FLOW",
    "PARSER_BREAK_OUTSIDE_LOOP",
    "PARSER_CONTINUE_OUTSIDE_LOOP",
    "missing_token",
    "unexpected_token",
    "invalid_statement",
    "missing_semicolon",
    "unbalanced_braces",
    # 语义分析异常
    "SemanticError",
    "SEMANTIC_TYPE_MISMATCH",
    "SEMANTIC_INVALID_TYPE",
    "SEMANTIC_INCOMPATIBLE_TYPES",
    "SEMANTIC_MISSING_TYPE",
    "SEMANTIC_INVALID_CAST",
    "SEMANTIC_UNDEFINED_VARIABLE",
    "SEMANTIC_DUPLICATE_VARIABLE",
    "SEMANTIC_VARIABLE_NOT_INITIALIZED",
    "SEMANTIC_CONSTANT_MODIFICATION",
    "SEMANTIC_UNDEFINED_FUNCTION",
    "SEMANTIC_DUPLICATE_FUNCTION",
    "SEMANTIC_INVALID_RETURN_TYPE",
    "SEMANTIC_PARAMETER_MISMATCH",
    "SEMANTIC_MISSING_RETURN",
    "SEMANTIC_SCOPE_ERROR",
    "SEMANTIC_VARIABLE_OUT_OF_SCOPE",
    "SEMANTIC_INVALID_ACCESS",
    "SEMANTIC_UNDEFINED_STRUCT",
    "SEMANTIC_DUPLICATE_STRUCT",
    "SEMANTIC_INVALID_MEMBER",
    "SEMANTIC_MISSING_MEMBER",
    "SEMANTIC_INVALID_ARRAY_INDEX",
    "SEMANTIC_ARRAY_INDEX_OUT_OF_RANGE",
    "SEMANTIC_INVALID_ARRAY_SIZE",
    "SEMANTIC_NULL_POINTER",
    "SEMANTIC_INVALID_POINTER_OPERATION",
    "SEMANTIC_POINTER_TYPE_MISMATCH",
    "type_mismatch",
    "undefined_variable",
    "undefined_function",
    "duplicate_definition",
    "invalid_member_access",
    "parameter_mismatch",
    # 代码生成异常
    "CodeGenerationError",
    "CODEGEN_INVALID_IR",
    "CODEGEN_IR_CONVERSION_FAILED",
    "CODEGEN_MISSING_IR_NODE",
    "CODEGEN_IR_TYPE_MISMATCH",
    "CODEGEN_UNSUPPORTED_FEATURE",
    "CODEGEN_BACKEND_ERROR",
    "CODEGEN_LINKER_ERROR",
    "CODEGEN_OPTIMIZATION_ERROR",
    "CODEGEN_UNSUPPORTED_PLATFORM",
    "CODEGEN_PLATFORM_SPECIFIC_ERROR",
    "CODEGEN_ABI_ERROR",
    "CODEGEN_MEMORY_ALLOCATION_ERROR",
    "CODEGEN_STACK_OVERFLOW",
    "CODEGEN_INVALID_MEMORY_ACCESS",
    "CODEGEN_OUTPUT_ERROR",
    "CODEGEN_FILE_WRITE_ERROR",
    "CODEGEN_INVALID_OUTPUT_FORMAT",
    "unsupported_feature",
    "backend_error",
    "ir_conversion_failed",
    "unsupported_platform",
    "file_write_error",
    # Pipeline 异常
    "PipelineError",
    "ErrorType",  # 向后兼容枚举
    "PIPELINE_FILE_NOT_FOUND",
    "PIPELINE_FILE_READ_ERROR",
    "PIPELINE_FILE_WRITE_ERROR",
    "PIPELINE_SYNTAX_MISSING_BRACE",
    "PIPELINE_SYNTAX_UNEXPECTED_TOKEN",
    "PIPELINE_SYNTAX_INVALID_MODULE_DECL",
    "PIPELINE_SYNTAX_INVALID_IMPORT_STMT",
    "PIPELINE_SYNTAX_INVALID_VISIBILITY",
    "PIPELINE_SEMANTIC_DUPLICATE_SYMBOL",
    "PIPELINE_SEMANTIC_UNDEFINED_SYMBOL",
    "PIPELINE_SEMANTIC_TYPE_MISMATCH",
    "PIPELINE_SEMANTIC_INVALID_RETURN",
    "PIPELINE_SCOPE_VIOLATION",
    "PIPELINE_SCOPE_OUT_OF_SCOPE",
    "PIPELINE_SCOPE_INVALID_ACCESS",
    "PIPELINE_DEPENDENCY_CYCLE",
    "PIPELINE_DEPENDENCY_MISSING_MODULE",
    "PIPELINE_DEPENDENCY_VERSION_CONFLICT",
    "PIPELINE_COMPILE_CONVERSION_FAILED",
    "PIPELINE_COMPILE_UNSUPPORTED_FEATURE",
    "file_not_found",
    "file_read_error",
    "dependency_cycle",
    "missing_module",
    "duplicate_symbol",
    "unsupported_feature",
    # 错误恢复机制
    "RecoveryAction",
    "RecoveryContext",
    "ErrorRecoveryStrategy",
    "CompilationAbortedError",
    # 错误模式管理
    "ErrorMode",
    "ErrorModeConfig",
    "ErrorModeManager",
    "ErrorRecoveryContext",
    # 智能提示生成器
    "Suggestion",
    "SuggestionResult",
    "SuggestionGenerator",
    "ErrorEnhancer",
]

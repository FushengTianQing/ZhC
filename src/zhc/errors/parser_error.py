"""
Parser 异常类

语法分析阶段的异常定义。

创建日期: 2026-04-07
最后更新: 2026-04-07
维护者: ZHC开发团队
"""

from typing import Optional, List
from .base import ZHCError, SourceLocation


class ParserError(ZHCError):
    """
    语法分析错误

    在语法分析阶段发生的错误，例如：
    - 语法错误
    - 缺少必要的token
    - 意外的token
    - 声明错误

    Attributes:
        expected_tokens: 期望的token类型列表（可选）
        actual_token: 实际遇到的token类型（可选）
        recovery_point: 错误恢复点（可选）

    Example:
        >>> error = ParserError(
        ...     "缺少分号",
        ...     location=SourceLocation("test.zhc", 10, 20),
        ...     error_code="P001",
        ...     expected_tokens=["分号"],
        ...     actual_token="换行",
        ...     suggestion="请在语句末尾添加分号"
        ... )
    """

    def __init__(
        self,
        message: str,
        location: Optional[SourceLocation] = None,
        error_code: Optional[str] = None,
        severity: str = ZHCError.SEVERITY_ERROR,
        context: Optional[str] = None,
        suggestion: Optional[str] = None,
        expected_tokens: Optional[List[str]] = None,
        actual_token: Optional[str] = None,
        recovery_point: Optional[str] = None,
    ):
        """
        初始化语法分析错误

        Args:
            message: 错误消息
            location: 错误位置
            error_code: 错误代码
            severity: 错误严重程度
            context: 错误上下文
            suggestion: 修复建议
            expected_tokens: 期望的token类型列表
            actual_token: 实际遇到的token类型
            recovery_point: 错误恢复点
        """
        self.expected_tokens = expected_tokens or []
        self.actual_token = actual_token
        self.recovery_point = recovery_point
        super().__init__(message, location, error_code, severity, context, suggestion)

    def _format_message(self) -> str:
        """格式化错误消息，添加期望token信息"""
        base_message = super()._format_message()

        # 添加期望token信息
        if self.expected_tokens:
            expected_str = " 或 ".join(self.expected_tokens)
            base_message += f"\n期望: {expected_str}"

        # 添加实际token信息
        if self.actual_token:
            base_message += f"\n实际: {self.actual_token}"

        return base_message

    def to_dict(self) -> dict:
        """转换为字典格式"""
        data = super().to_dict()
        data.update(
            {
                "expected_tokens": self.expected_tokens,
                "actual_token": self.actual_token,
                "recovery_point": self.recovery_point,
            }
        )
        return data


# ============================================================================
# 预定义的语法错误代码
# ============================================================================

# P001-P010: Token 相关错误
PARSER_MISSING_TOKEN = "P001"  # 缺少必要的token
PARSER_UNEXPECTED_TOKEN = "P002"  # 意外的token
PARSER_EXPECTED_IDENTIFIER = "P003"  # 期望标识符
PARSER_EXPECTED_TYPE = "P004"  # 期望类型

# P011-P020: 声明相关错误
PARSER_INVALID_DECLARATION = "P011"  # 无效的声明
PARSER_DUPLICATE_DECLARATION = "P012"  # 重复的声明
PARSER_MISSING_INITIALIZER = "P013"  # 缺少初始化器
PARSER_INVALID_INITIALIZER = "P014"  # 无效的初始化器

# P021-P030: 语句相关错误
PARSER_INVALID_STATEMENT = "P021"  # 无效的语句
PARSER_MISSING_SEMICOLON = "P022"  # 缺少分号
PARSER_MISSING_BRACE = "P023"  # 缺少大括号
PARSER_UNBALANCED_PARENS = "P024"  # 括号不匹配
PARSER_UNBALANCED_BRACES = "P025"  # 大括号不匹配

# P031-P040: 表达式相关错误
PARSER_INVALID_EXPRESSION = "P031"  # 无效的表达式
PARSER_MISSING_OPERAND = "P032"  # 缺少操作数
PARSER_INVALID_OPERATOR = "P033"  # 无效的运算符

# P041-P050: 函数相关错误
PARSER_INVALID_FUNCTION = "P041"  # 无效的函数定义
PARSER_MISSING_RETURN = "P042"  # 缺少返回语句
PARSER_INVALID_PARAMETER = "P043"  # 无效的参数

# P051-P060: 控制流相关错误
PARSER_INVALID_CONTROL_FLOW = "P051"  # 无效的控制流
PARSER_BREAK_OUTSIDE_LOOP = "P052"  # break在循环外
PARSER_CONTINUE_OUTSIDE_LOOP = "P053"  # continue在循环外


# ============================================================================
# 便捷工厂函数
# ============================================================================


def missing_token(
    expected: str,
    location: Optional[SourceLocation] = None,
    actual: Optional[str] = None,
    context: Optional[str] = None,
) -> ParserError:
    """
    创建缺少token错误

    Args:
        expected: 期望的token类型
        location: 错误位置
        actual: 实际遇到的token类型
        context: 错误上下文

    Returns:
        ParserError 实例
    """
    return ParserError(
        message=f"缺少 {expected}",
        location=location,
        error_code=PARSER_MISSING_TOKEN,
        expected_tokens=[expected],
        actual_token=actual,
        context=context,
        suggestion=f"请添加 {expected}",
    )


def unexpected_token(
    token: str,
    location: Optional[SourceLocation] = None,
    expected: Optional[List[str]] = None,
    context: Optional[str] = None,
) -> ParserError:
    """
    创建意外token错误

    Args:
        token: 意外的token类型
        location: 错误位置
        expected: 期望的token类型列表
        context: 错误上下文

    Returns:
        ParserError 实例
    """
    return ParserError(
        message=f"意外的 {token}",
        location=location,
        error_code=PARSER_UNEXPECTED_TOKEN,
        expected_tokens=expected,
        actual_token=token,
        context=context,
        suggestion="请检查语法是否正确",
    )


def invalid_statement(
    statement_type: str,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> ParserError:
    """
    创建无效语句错误

    Args:
        statement_type: 语句类型
        location: 错误位置
        context: 错误上下文

    Returns:
        ParserError 实例
    """
    return ParserError(
        message=f"无效的语句: {statement_type}",
        location=location,
        error_code=PARSER_INVALID_STATEMENT,
        context=context,
        suggestion="请检查语句语法是否正确",
    )


def missing_semicolon(
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> ParserError:
    """
    创建缺少分号错误

    Args:
        location: 错误位置
        context: 错误上下文

    Returns:
        ParserError 实例
    """
    return ParserError(
        message="缺少分号",
        location=location,
        error_code=PARSER_MISSING_SEMICOLON,
        expected_tokens=["分号"],
        context=context,
        suggestion="请在语句末尾添加分号 ';'",
    )


def unbalanced_braces(
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> ParserError:
    """
    创建大括号不匹配错误

    Args:
        location: 错误位置
        context: 错误上下文

    Returns:
        ParserError 实例
    """
    return ParserError(
        message="大括号不匹配",
        location=location,
        error_code=PARSER_UNBALANCED_BRACES,
        context=context,
        suggestion="请检查大括号是否成对出现",
    )


# 导出公共API
__all__ = [
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
]

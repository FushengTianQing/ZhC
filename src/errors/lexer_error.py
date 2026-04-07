"""
Lexer 异常类

词法分析阶段的异常定义。

创建日期: 2026-04-07
最后更新: 2026-04-07
维护者: ZHC开发团队
"""

from typing import Optional
from .base import ZHCError, SourceLocation


class LexerError(ZHCError):
    """
    词法分析错误
    
    在词法分析阶段发生的错误，例如：
    - 非法字符
    - 字符串未闭合
    - 数字格式错误
    - 注释未闭合
    
    Attributes:
        character: 导致错误的字符（可选）
        token_type: 期望的token类型（可选）
    
    Example:
        >>> error = LexerError(
        ...     "非法字符 '@'",
        ...     location=SourceLocation("test.zhc", 5, 10),
        ...     error_code="L001",
        ...     character='@',
        ...     suggestion="请检查是否使用了不支持的特殊字符"
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
        character: Optional[str] = None,
        token_type: Optional[str] = None,
    ):
        """
        初始化词法分析错误
        
        Args:
            message: 错误消息
            location: 错误位置
            error_code: 错误代码
            severity: 错误严重程度
            context: 错误上下文
            suggestion: 修复建议
            character: 导致错误的字符
            token_type: 期望的token类型
        """
        self.character = character
        self.token_type = token_type
        super().__init__(message, location, error_code, severity, context, suggestion)
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        data = super().to_dict()
        data.update({
            "character": self.character,
            "token_type": self.token_type,
        })
        return data


# ============================================================================
# 预定义的词法错误代码
# ============================================================================

# L001-L010: 字符相关错误
LEXER_ILLEGAL_CHARACTER = "L001"  # 非法字符
LEXER_UNTERMINATED_STRING = "L002"  # 字符串未闭合
LEXER_UNTERMINATED_CHAR = "L003"  # 字符字面量未闭合
LEXER_INVALID_ESCAPE_SEQUENCE = "L004"  # 无效的转义序列
LEXER_UNTERMINATED_COMMENT = "L005"  # 注释未闭合

# L011-L020: 数字相关错误
LEXER_INVALID_NUMBER_FORMAT = "L011"  # 数字格式错误
LEXER_NUMBER_OUT_OF_RANGE = "L012"  # 数字超出范围
LEXER_INVALID_FLOAT_FORMAT = "L013"  # 浮点数格式错误
LEXER_INVALID_HEX_FORMAT = "L014"  # 十六进制格式错误
LEXER_INVALID_BINARY_FORMAT = "L015"  # 二进制格式错误

# L021-L030: 标识符相关错误
LEXER_INVALID_IDENTIFIER = "L021"  # 无效的标识符
LEXER_RESERVED_KEYWORD = "L022"  # 保留关键字误用

# L031-L040: 编码相关错误
LEXER_INVALID_ENCODING = "L031"  # 无效的编码
LEXER_BOM_ERROR = "L032"  # BOM标记错误


# ============================================================================
# 便捷工厂函数
# ============================================================================

def illegal_character(
    character: str,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> LexerError:
    """
    创建非法字符错误
    
    Args:
        character: 非法字符
        location: 错误位置
        context: 错误上下文
    
    Returns:
        LexerError 实例
    """
    return LexerError(
        message=f"非法字符 '{character}'",
        location=location,
        error_code=LEXER_ILLEGAL_CHARACTER,
        character=character,
        context=context,
        suggestion="请检查是否使用了不支持的特殊字符",
    )


def unterminated_string(
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> LexerError:
    """
    创建字符串未闭合错误
    
    Args:
        location: 错误位置
        context: 错误上下文
    
    Returns:
        LexerError 实例
    """
    return LexerError(
        message="字符串未闭合",
        location=location,
        error_code=LEXER_UNTERMINATED_STRING,
        context=context,
        suggestion="请检查字符串是否缺少闭合引号",
    )


def invalid_number_format(
    number_str: str,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> LexerError:
    """
    创建数字格式错误
    
    Args:
        number_str: 错误的数字字符串
        location: 错误位置
        context: 错误上下文
    
    Returns:
        LexerError 实例
    """
    return LexerError(
        message=f"无效的数字格式 '{number_str}'",
        location=location,
        error_code=LEXER_INVALID_NUMBER_FORMAT,
        context=context,
        suggestion="请检查数字格式是否正确",
    )


def invalid_identifier(
    identifier: str,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> LexerError:
    """
    创建无效标识符错误
    
    Args:
        identifier: 无效的标识符
        location: 错误位置
        context: 错误上下文
    
    Returns:
        LexerError 实例
    """
    return LexerError(
        message=f"无效的标识符 '{identifier}'",
        location=location,
        error_code=LEXER_INVALID_IDENTIFIER,
        context=context,
        suggestion="标识符必须以字母或下划线开头，只能包含字母、数字和下划线",
    )


# 导出公共API
__all__ = [
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
    "invalid_number_format",
    "invalid_identifier",
]
"""
Semantic 异常类

语义分析阶段的异常定义。

创建日期: 2026-04-07
最后更新: 2026-04-07
维护者: ZHC开发团队
"""

from typing import Optional, Dict, Any
from .base import ZHCError, SourceLocation


class SemanticError(ZHCError):
    """
    语义分析错误
    
    在语义分析阶段发生的错误，例如：
    - 类型错误
    - 未定义的变量
    - 重复定义
    - 作用域错误
    - 类型不兼容
    
    Attributes:
        symbol_name: 相关的符号名称（可选）
        expected_type: 期望的类型（可选）
        actual_type: 实际的类型（可选）
        scope_info: 作用域信息（可选）
    
    Example:
        >>> error = SemanticError(
        ...     "类型不匹配",
        ...     location=SourceLocation("test.zhc", 15, 8),
        ...     error_code="S001",
        ...     expected_type="整数型",
        ...     actual_type="浮点型",
        ...     suggestion="请进行类型转换或检查表达式类型"
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
        symbol_name: Optional[str] = None,
        expected_type: Optional[str] = None,
        actual_type: Optional[str] = None,
        scope_info: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化语义分析错误
        
        Args:
            message: 错误消息
            location: 错误位置
            error_code: 错误代码
            severity: 错误严重程度
            context: 错误上下文
            suggestion: 修复建议
            symbol_name: 相关的符号名称
            expected_type: 期望的类型
            actual_type: 实际的类型
            scope_info: 作用域信息
        """
        self.symbol_name = symbol_name
        self.expected_type = expected_type
        self.actual_type = actual_type
        self.scope_info = scope_info or {}
        super().__init__(message, location, error_code, severity, context, suggestion)
    
    def _format_message(self) -> str:
        """格式化错误消息，添加类型信息"""
        base_message = super()._format_message()
        
        # 添加符号名称
        if self.symbol_name:
            base_message += f"\n符号: {self.symbol_name}"
        
        # 添加类型信息
        if self.expected_type and self.actual_type:
            base_message += f"\n期望类型: {self.expected_type}, 实际类型: {self.actual_type}"
        elif self.expected_type:
            base_message += f"\n期望类型: {self.expected_type}"
        elif self.actual_type:
            base_message += f"\n实际类型: {self.actual_type}"
        
        return base_message
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        data = super().to_dict()
        data.update({
            "symbol_name": self.symbol_name,
            "expected_type": self.expected_type,
            "actual_type": self.actual_type,
            "scope_info": self.scope_info,
        })
        return data


# ============================================================================
# 预定义的语义错误代码
# ============================================================================

# S001-S010: 类型相关错误
SEMANTIC_TYPE_MISMATCH = "S001"  # 类型不匹配
SEMANTIC_INVALID_TYPE = "S002"  # 无效的类型
SEMANTIC_INCOMPATIBLE_TYPES = "S003"  # 类型不兼容
SEMANTIC_MISSING_TYPE = "S004"  # 缺少类型声明
SEMANTIC_INVALID_CAST = "S005"  # 无效的类型转换

# S011-S020: 变量相关错误
SEMANTIC_UNDEFINED_VARIABLE = "S011"  # 未定义的变量
SEMANTIC_DUPLICATE_VARIABLE = "S012"  # 重复定义的变量
SEMANTIC_VARIABLE_NOT_INITIALIZED = "S013"  # 变量未初始化
SEMANTIC_CONSTANT_MODIFICATION = "S014"  # 常量被修改

# S021-S030: 函数相关错误
SEMANTIC_UNDEFINED_FUNCTION = "S021"  # 未定义的函数
SEMANTIC_DUPLICATE_FUNCTION = "S022"  # 重复定义的函数
SEMANTIC_INVALID_RETURN_TYPE = "S023"  # 无效的返回类型
SEMANTIC_PARAMETER_MISMATCH = "S024"  # 参数不匹配
SEMANTIC_MISSING_RETURN = "S025"  # 缺少返回语句

# S031-S040: 作用域相关错误
SEMANTIC_SCOPE_ERROR = "S031"  # 作用域错误
SEMANTIC_VARIABLE_OUT_OF_SCOPE = "S032"  # 变量超出作用域
SEMANTIC_INVALID_ACCESS = "S033"  # 无效的访问

# S041-S050: 结构体/联合体相关错误
SEMANTIC_UNDEFINED_STRUCT = "S041"  # 未定义的结构体
SEMANTIC_DUPLICATE_STRUCT = "S042"  # 重复定义的结构体
SEMANTIC_INVALID_MEMBER = "S043"  # 无效的成员访问
SEMANTIC_MISSING_MEMBER = "S044"  # 缺少成员

# S051-S060: 数组相关错误
SEMANTIC_INVALID_ARRAY_INDEX = "S051"  # 无效的数组索引
SEMANTIC_ARRAY_INDEX_OUT_OF_RANGE = "S052"  # 数组索引越界
SEMANTIC_INVALID_ARRAY_SIZE = "S053"  # 无效的数组大小

# S061-S070: 指针相关错误
SEMANTIC_NULL_POINTER = "S061"  # 空指针错误
SEMANTIC_INVALID_POINTER_OPERATION = "S062"  # 无效的指针操作
SEMANTIC_POINTER_TYPE_MISMATCH = "S063"  # 指针类型不匹配


# ============================================================================
# 便捷工厂函数
# ============================================================================

def type_mismatch(
    expected: str,
    actual: str,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> SemanticError:
    """
    创建类型不匹配错误
    
    Args:
        expected: 期望的类型
        actual: 实际的类型
        location: 错误位置
        context: 错误上下文
    
    Returns:
        SemanticError 实例
    """
    return SemanticError(
        message=f"类型不匹配: 期望 {expected}, 实际 {actual}",
        location=location,
        error_code=SEMANTIC_TYPE_MISMATCH,
        expected_type=expected,
        actual_type=actual,
        context=context,
        suggestion="请进行类型转换或检查表达式类型",
    )


def undefined_variable(
    variable_name: str,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> SemanticError:
    """
    创建未定义变量错误
    
    Args:
        variable_name: 未定义的变量名
        location: 错误位置
        context: 错误上下文
    
    Returns:
        SemanticError 实例
    """
    return SemanticError(
        message=f"未定义的变量 '{variable_name}'",
        location=location,
        error_code=SEMANTIC_UNDEFINED_VARIABLE,
        symbol_name=variable_name,
        context=context,
        suggestion="请检查变量是否已声明，或检查作用域是否正确",
    )


def undefined_function(
    function_name: str,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> SemanticError:
    """
    创建未定义函数错误
    
    Args:
        function_name: 未定义的函数名
        location: 错误位置
        context: 错误上下文
    
    Returns:
        SemanticError 实例
    """
    return SemanticError(
        message=f"未定义的函数 '{function_name}'",
        location=location,
        error_code=SEMANTIC_UNDEFINED_FUNCTION,
        symbol_name=function_name,
        context=context,
        suggestion="请检查函数是否已声明，或检查函数名是否正确",
    )


def duplicate_definition(
    symbol_name: str,
    symbol_type: str,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> SemanticError:
    """
    创建重复定义错误
    
    Args:
        symbol_name: 重复定义的符号名
        symbol_type: 符号类型（变量/函数/结构体等）
        location: 错误位置
        context: 错误上下文
    
    Returns:
        SemanticError 实例
    """
    return SemanticError(
        message=f"重复定义的{symbol_type} '{symbol_name}'",
        location=location,
        error_code=SEMANTIC_DUPLICATE_VARIABLE if symbol_type == "变量" else SEMANTIC_DUPLICATE_FUNCTION,
        symbol_name=symbol_name,
        context=context,
        suggestion=f"请检查{symbol_type}是否已在当前作用域中定义",
    )


def invalid_member_access(
    struct_name: str,
    member_name: str,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> SemanticError:
    """
    创建无效成员访问错误
    
    Args:
        struct_name: 结构体名称
        member_name: 成员名称
        location: 错误位置
        context: 错误上下文
    
    Returns:
        SemanticError 实例
    """
    return SemanticError(
        message=f"结构体 '{struct_name}' 没有成员 '{member_name}'",
        location=location,
        error_code=SEMANTIC_INVALID_MEMBER,
        symbol_name=f"{struct_name}.{member_name}",
        context=context,
        suggestion="请检查成员名称是否正确",
    )


def parameter_mismatch(
    function_name: str,
    expected_count: int,
    actual_count: int,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> SemanticError:
    """
    创建参数不匹配错误
    
    Args:
        function_name: 函数名称
        expected_count: 期望的参数数量
        actual_count: 实际的参数数量
        location: 错误位置
        context: 错误上下文
    
    Returns:
        SemanticError 实例
    """
    return SemanticError(
        message=f"函数 '{function_name}' 参数数量不匹配: 期望 {expected_count} 个, 实际 {actual_count} 个",
        location=location,
        error_code=SEMANTIC_PARAMETER_MISMATCH,
        symbol_name=function_name,
        context=context,
        suggestion="请检查函数调用的参数数量是否正确",
    )


# 导出公共API
__all__ = [
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
]
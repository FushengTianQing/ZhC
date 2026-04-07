"""
CodeGenerator 异常类

代码生成阶段的异常定义。

创建日期: 2026-04-07
最后更新: 2026-04-07
维护者: ZHC开发团队
"""

from typing import Optional, Dict, Any
from .base import ZHCError, SourceLocation


class CodeGenerationError(ZHCError):
    """
    代码生成错误
    
    在代码生成阶段发生的错误，例如：
    - IR转换错误
    - 目标代码生成错误
    - 不支持的特性
    - 后端编译错误
    
    Attributes:
        ir_node_type: 相关的IR节点类型（可选）
        target_backend: 目标后端（可选）
        feature_name: 不支持的特性名称（可选）
        backend_error: 后端编译器的错误信息（可选）
    
    Example:
        >>> error = CodeGenerationError(
        ...     "不支持的内联汇编",
        ...     location=SourceLocation("test.zhc", 20, 5),
        ...     error_code="C001",
        ...     feature_name="内联汇编",
        ...     target_backend="LLVM",
        ...     suggestion="请使用标准C代码替代内联汇编"
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
        ir_node_type: Optional[str] = None,
        target_backend: Optional[str] = None,
        feature_name: Optional[str] = None,
        backend_error: Optional[str] = None,
    ):
        """
        初始化代码生成错误
        
        Args:
            message: 错误消息
            location: 错误位置
            error_code: 错误代码
            severity: 错误严重程度
            context: 错误上下文
            suggestion: 修复建议
            ir_node_type: 相关的IR节点类型
            target_backend: 目标后端
            feature_name: 不支持的特性名称
            backend_error: 后端编译器的错误信息
        """
        self.ir_node_type = ir_node_type
        self.target_backend = target_backend
        self.feature_name = feature_name
        self.backend_error = backend_error
        super().__init__(message, location, error_code, severity, context, suggestion)
    
    def _format_message(self) -> str:
        """格式化错误消息，添加后端信息"""
        base_message = super()._format_message()
        
        # 添加IR节点类型
        if self.ir_node_type:
            base_message += f"\nIR节点: {self.ir_node_type}"
        
        # 添加目标后端
        if self.target_backend:
            base_message += f"\n目标后端: {self.target_backend}"
        
        # 添加特性名称
        if self.feature_name:
            base_message += f"\n特性: {self.feature_name}"
        
        # 添加后端错误
        if self.backend_error:
            base_message += f"\n后端错误: {self.backend_error}"
        
        return base_message
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        data = super().to_dict()
        data.update({
            "ir_node_type": self.ir_node_type,
            "target_backend": self.target_backend,
            "feature_name": self.feature_name,
            "backend_error": self.backend_error,
        })
        return data


# ============================================================================
# 预定义的代码生成错误代码
# ============================================================================

# C001-C010: IR 相关错误
CODEGEN_INVALID_IR = "C001"  # 无效的IR节点
CODEGEN_IR_CONVERSION_FAILED = "C002"  # IR转换失败
CODEGEN_MISSING_IR_NODE = "C003"  # 缺少IR节点
CODEGEN_IR_TYPE_MISMATCH = "C004"  # IR类型不匹配

# C011-C020: 目标代码相关错误
CODEGEN_UNSUPPORTED_FEATURE = "C011"  # 不支持的特性
CODEGEN_BACKEND_ERROR = "C012"  # 后端编译错误
CODEGEN_LINKER_ERROR = "C013"  # 链接器错误
CODEGEN_OPTIMIZATION_ERROR = "C014"  # 优化错误

# C021-C030: 平台相关错误
CODEGEN_UNSUPPORTED_PLATFORM = "C021"  # 不支持的平台
CODEGEN_PLATFORM_SPECIFIC_ERROR = "C022"  # 平台特定错误
CODEGEN_ABI_ERROR = "C023"  # ABI错误

# C031-C040: 内存相关错误
CODEGEN_MEMORY_ALLOCATION_ERROR = "C031"  # 内存分配错误
CODEGEN_STACK_OVERFLOW = "C032"  # 栈溢出
CODEGEN_INVALID_MEMORY_ACCESS = "C033"  # 无效的内存访问

# C041-C050: 输出相关错误
CODEGEN_OUTPUT_ERROR = "C041"  # 输出错误
CODEGEN_FILE_WRITE_ERROR = "C042"  # 文件写入错误
CODEGEN_INVALID_OUTPUT_FORMAT = "C043"  # 无效的输出格式


# ============================================================================
# 便捷工厂函数
# ============================================================================

def unsupported_feature(
    feature_name: str,
    target_backend: Optional[str] = None,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> CodeGenerationError:
    """
    创建不支持特性错误
    
    Args:
        feature_name: 不支持的特性名称
        target_backend: 目标后端
        location: 错误位置
        context: 错误上下文
    
    Returns:
        CodeGenerationError 实例
    """
    backend_info = f" ({target_backend})" if target_backend else ""
    return CodeGenerationError(
        message=f"不支持的特性: {feature_name}{backend_info}",
        location=location,
        error_code=CODEGEN_UNSUPPORTED_FEATURE,
        feature_name=feature_name,
        target_backend=target_backend,
        context=context,
        suggestion="请使用支持的替代方案或等待后续版本支持",
    )


def backend_error(
    backend_name: str,
    error_message: str,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> CodeGenerationError:
    """
    创建后端编译错误
    
    Args:
        backend_name: 后端名称
        error_message: 后端错误信息
        location: 错误位置
        context: 错误上下文
    
    Returns:
        CodeGenerationError 实例
    """
    return CodeGenerationError(
        message=f"{backend_name} 后端编译错误",
        location=location,
        error_code=CODEGEN_BACKEND_ERROR,
        target_backend=backend_name,
        backend_error=error_message,
        context=context,
        suggestion="请检查后端编译器配置和输入代码",
    )


def ir_conversion_failed(
    ir_node_type: str,
    reason: str,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> CodeGenerationError:
    """
    创建IR转换失败错误
    
    Args:
        ir_node_type: IR节点类型
        reason: 失败原因
        location: 错误位置
        context: 错误上下文
    
    Returns:
        CodeGenerationError 实例
    """
    return CodeGenerationError(
        message=f"IR节点 '{ir_node_type}' 转换失败: {reason}",
        location=location,
        error_code=CODEGEN_IR_CONVERSION_FAILED,
        ir_node_type=ir_node_type,
        context=context,
        suggestion="请检查IR节点是否正确生成",
    )


def unsupported_platform(
    platform: str,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> CodeGenerationError:
    """
    创建不支持平台错误
    
    Args:
        platform: 平台名称
        location: 错误位置
        context: 错误上下文
    
    Returns:
        CodeGenerationError 实例
    """
    return CodeGenerationError(
        message=f"不支持的平台: {platform}",
        location=location,
        error_code=CODEGEN_UNSUPPORTED_PLATFORM,
        target_backend=platform,
        context=context,
        suggestion="请使用支持的平台或等待后续版本支持",
    )


def file_write_error(
    file_path: str,
    reason: str,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> CodeGenerationError:
    """
    创建文件写入错误
    
    Args:
        file_path: 文件路径
        reason: 失败原因
        location: 错误位置
        context: 错误上下文
    
    Returns:
        CodeGenerationError 实例
    """
    return CodeGenerationError(
        message=f"无法写入文件 '{file_path}': {reason}",
        location=location,
        error_code=CODEGEN_FILE_WRITE_ERROR,
        context=context,
        suggestion="请检查文件路径是否正确，是否有写入权限",
    )


# 导出公共API
__all__ = [
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
]
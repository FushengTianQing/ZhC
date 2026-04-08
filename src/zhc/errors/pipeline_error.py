#!/usr/bin/env python3
"""
Pipeline 错误处理器 - 用于检测和报告模块系统的各种错误

统一架构：
- PipelineError(ZHCError) - 异常基类
- 字符串错误码常量 - 如 PIPELINE_FILE_NOT_FOUND
- 便捷工厂函数 - 如 file_not_found(), dependency_cycle()
- ErrorHandler - 保持 report_error() 兼容性供 DependencyResolver 使用

从 converter/error.py 迁移，2026-04-08 标记为废弃 converter/ 目录。
架构更新：2026-04-08 22:16 - 统一到 errors 架构
"""

from typing import Optional, List, Dict, Any
from .base import ZHCError, SourceLocation, ErrorCollection


# ============================================================================
# Pipeline 错误代码常量
# ============================================================================

# P001-P010: 文件错误
PIPELINE_FILE_NOT_FOUND = "P001"  # 文件不存在
PIPELINE_FILE_READ_ERROR = "P002"  # 文件读取错误
PIPELINE_FILE_WRITE_ERROR = "P003"  # 文件写入错误

# P011-P020: 语法错误
PIPELINE_SYNTAX_MISSING_BRACE = "P011"  # 缺少花括号
PIPELINE_SYNTAX_UNEXPECTED_TOKEN = "P012"  # 意外的标记
PIPELINE_SYNTAX_INVALID_MODULE_DECL = "P013"  # 无效的模块声明
PIPELINE_SYNTAX_INVALID_IMPORT_STMT = "P014"  # 无效的导入语句
PIPELINE_SYNTAX_INVALID_VISIBILITY = "P015"  # 无效的可见性修饰符

# P021-P030: 语义错误
PIPELINE_SEMANTIC_DUPLICATE_SYMBOL = "P021"  # 符号重复定义
PIPELINE_SEMANTIC_UNDEFINED_SYMBOL = "P022"  # 未定义的符号
PIPELINE_SEMANTIC_TYPE_MISMATCH = "P023"  # 类型不匹配
PIPELINE_SEMANTIC_INVALID_RETURN = "P024"  # 无效的返回语句

# P031-P040: 作用域错误
PIPELINE_SCOPE_VIOLATION = "P031"  # 作用域违规
PIPELINE_SCOPE_OUT_OF_SCOPE = "P032"  # 超出作用域访问
PIPELINE_SCOPE_INVALID_ACCESS = "P033"  # 无效的访问控制

# P041-P050: 依赖错误
PIPELINE_DEPENDENCY_CYCLE = "P041"  # 循环依赖
PIPELINE_DEPENDENCY_MISSING_MODULE = "P042"  # 缺失的模块依赖
PIPELINE_DEPENDENCY_VERSION_CONFLICT = "P043"  # 版本冲突

# P051-P060: 编译错误
PIPELINE_COMPILE_CONVERSION_FAILED = "P051"  # 转换失败
PIPELINE_COMPILE_UNSUPPORTED_FEATURE = "P052"  # 不支持的功能


# ============================================================================
# ErrorType - 向后兼容枚举类
# ============================================================================


class ErrorType:
    """
    错误类型枚举（向后兼容）

    用于 pipeline.py 等模块的旧式接口。
    新代码应直接使用字符串常量（如 PIPELINE_FILE_NOT_FOUND）。
    """

    FILE_NOT_FOUND = PIPELINE_FILE_NOT_FOUND
    FILE_READ_ERROR = PIPELINE_FILE_READ_ERROR
    FILE_WRITE_ERROR = PIPELINE_FILE_WRITE_ERROR

    SYNTAX_MISSING_BRACE = PIPELINE_SYNTAX_MISSING_BRACE
    SYNTAX_UNEXPECTED_TOKEN = PIPELINE_SYNTAX_UNEXPECTED_TOKEN
    SYNTAX_INVALID_MODULE_DECL = PIPELINE_SYNTAX_INVALID_MODULE_DECL
    SYNTAX_INVALID_IMPORT_STMT = PIPELINE_SYNTAX_INVALID_IMPORT_STMT
    SYNTAX_INVALID_VISIBILITY = PIPELINE_SYNTAX_INVALID_VISIBILITY

    SEMANTIC_DUPLICATE_SYMBOL = PIPELINE_SEMANTIC_DUPLICATE_SYMBOL
    SEMANTIC_UNDEFINED_SYMBOL = PIPELINE_SEMANTIC_UNDEFINED_SYMBOL
    SEMANTIC_TYPE_MISMATCH = PIPELINE_SEMANTIC_TYPE_MISMATCH
    SEMANTIC_INVALID_RETURN = PIPELINE_SEMANTIC_INVALID_RETURN

    SCOPE_VIOLATION = PIPELINE_SCOPE_VIOLATION
    SCOPE_OUT_OF_SCOPE = PIPELINE_SCOPE_OUT_OF_SCOPE
    SCOPE_INVALID_ACCESS = PIPELINE_SCOPE_INVALID_ACCESS

    DEPENDENCY_CYCLE = PIPELINE_DEPENDENCY_CYCLE
    DEPENDENCY_MISSING_MODULE = PIPELINE_DEPENDENCY_MISSING_MODULE
    DEPENDENCY_VERSION_CONFLICT = PIPELINE_DEPENDENCY_VERSION_CONFLICT

    COMPILE_CONVERSION_FAILED = PIPELINE_COMPILE_CONVERSION_FAILED
    COMPILE_UNSUPPORTED_FEATURE = PIPELINE_COMPILE_UNSUPPORTED_FEATURE


# ============================================================================
# PipelineError 异常类
# ============================================================================


class PipelineError(ZHCError):
    """
    Pipeline 编译阶段错误

    用于 pipeline、依赖解析、模块系统等编译中期的错误。

    Attributes:
        module_name: 相关模块名（可选）
        cycle_info: 循环依赖信息（可选）

    Example:
        >>> error = PipelineError(
        ...     "文件不存在: test.zhc",
        ...     location=SourceLocation("main.zhc", 10, 5),
        ...     error_code=PIPELINE_FILE_NOT_FOUND,
        ...     suggestion="请检查文件路径是否正确"
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
        module_name: Optional[str] = None,
        cycle_info: Optional[List[str]] = None,
    ):
        """
        初始化 Pipeline 错误

        Args:
            message: 错误消息
            location: 错误位置
            error_code: 错误代码
            severity: 错误严重程度
            context: 错误上下文
            suggestion: 修复建议
            module_name: 相关模块名
            cycle_info: 循环依赖信息
        """
        self.module_name = module_name
        self.cycle_info = cycle_info
        super().__init__(
            message=message,
            location=location,
            error_code=error_code,
            severity=severity,
            context=context,
            suggestion=suggestion,
        )

    def to_dict(self) -> dict:
        """转换为字典格式"""
        data = super().to_dict()
        data.update(
            {
                "module_name": self.module_name,
                "cycle_info": self.cycle_info,
            }
        )
        return data


# ============================================================================
# 便捷工厂函数
# ============================================================================


def file_not_found(
    file_path: str,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> PipelineError:
    """
    创建文件不存在错误

    Args:
        file_path: 文件路径
        location: 错误位置
        context: 错误上下文

    Returns:
        PipelineError 实例
    """
    return PipelineError(
        message=f"文件不存在: {file_path}",
        location=location,
        error_code=PIPELINE_FILE_NOT_FOUND,
        context=context,
        suggestion="请检查文件路径是否正确，或确认文件是否已创建",
    )


def file_read_error(
    file_path: str,
    reason: str = "未知错误",
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> PipelineError:
    """创建文件读取错误"""
    return PipelineError(
        message=f"文件读取错误: {file_path} - {reason}",
        location=location,
        error_code=PIPELINE_FILE_READ_ERROR,
        context=context,
        suggestion="请检查文件权限或文件是否被其他程序占用",
    )


def dependency_cycle(
    cycle_modules: List[str],
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> PipelineError:
    """
    创建循环依赖错误

    Args:
        cycle_modules: 循环依赖的模块列表
        location: 错误位置
        context: 错误上下文

    Returns:
        PipelineError 实例
    """
    cycle_str = " -> ".join(cycle_modules)
    return PipelineError(
        message=f"发现循环依赖: {cycle_str}",
        location=location,
        error_code=PIPELINE_DEPENDENCY_CYCLE,
        context=context,
        suggestion="请检查模块间的导入关系，消除循环依赖",
        cycle_info=cycle_modules,
    )


def missing_module(
    module_name: str,
    imported_by: Optional[str] = None,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> PipelineError:
    """创建缺失模块错误"""
    msg = f"缺失的模块依赖: {module_name}"
    if imported_by:
        msg += f" (被 {imported_by} 导入)"
    return PipelineError(
        message=msg,
        location=location,
        error_code=PIPELINE_DEPENDENCY_MISSING_MODULE,
        context=context,
        suggestion="请确认模块已创建且路径正确",
    )


def duplicate_symbol(
    symbol: str,
    module_name: str,
    first_defined_line: int,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> PipelineError:
    """创建符号重复定义错误"""
    return PipelineError(
        message=f"符号 '{symbol}' 重复定义",
        location=location,
        error_code=PIPELINE_SEMANTIC_DUPLICATE_SYMBOL,
        context=context,
        suggestion="使用不同的符号名",
    )


def unsupported_feature(
    feature: str,
    location: Optional[SourceLocation] = None,
    context: Optional[str] = None,
) -> PipelineError:
    """创建不支持功能错误"""
    return PipelineError(
        message=f"不支持的功能: {feature}",
        location=location,
        error_code=PIPELINE_COMPILE_UNSUPPORTED_FEATURE,
        context=context,
        suggestion="请查看文档了解支持的功能列表",
    )


# ============================================================================
# ErrorHandler - 保持 report_error() 兼容性
# ============================================================================


class ErrorHandler:
    """
    Pipeline 错误处理器

    保持与 DependencyResolver.report_error() 的兼容性，
    同时支持新的统一异常架构。

    内部使用 ErrorCollection 管理错误，同时提供字符串接口。
    """

    # 错误代码映射（用于 report_error 兼容）
    _ERROR_CODE_MAP = {
        "依赖解析错误": PIPELINE_DEPENDENCY_MISSING_MODULE,
        "循环依赖错误": PIPELINE_DEPENDENCY_CYCLE,
    }

    def __init__(self, max_errors: int = 100, max_warnings: int = 200):
        """
        初始化错误处理器

        Args:
            max_errors: 最大错误数
            max_warnings: 最大警告数
        """
        self.max_errors = max_errors
        self.max_warnings = max_warnings
        self._collection = ErrorCollection()
        self._errors: List[PipelineError] = []

    def reset(self):
        """重置错误处理器"""
        self._collection.clear()
        self._errors.clear()

    def add(self, error: PipelineError) -> None:
        """
        添加错误（统一接口）

        Args:
            error: PipelineError 实例
        """
        self._collection.add(error)
        self._errors.append(error)

    def add_error(
        self,
        error_code: str,
        message: str,
        line_no: int = -1,
        column: int = -1,
        context: str = "",
        suggestion: str = "",
    ) -> bool:
        """
        添加错误（PipelineError 使用错误代码）

        Args:
            error_code: 错误代码（如 PIPELINE_FILE_NOT_FOUND）
            message: 错误消息
            line_no: 行号
            column: 列号
            context: 上下文
            suggestion: 建议

        Returns:
            是否添加成功
        """
        location = None
        if line_no > 0:
            location = SourceLocation(line=line_no, column=column)

        error = PipelineError(
            message=message,
            location=location,
            error_code=error_code,
            context=context,
            suggestion=suggestion,
        )
        self.add(error)
        return True

    def add_warning(
        self,
        error_code: str,
        message: str,
        line_no: int = -1,
        column: int = -1,
        context: str = "",
        suggestion: str = "",
    ) -> bool:
        """添加警告"""
        location = None
        if line_no > 0:
            location = SourceLocation(line=line_no, column=column)

        error = PipelineError(
            message=message,
            location=location,
            error_code=error_code,
            severity=ZHCError.SEVERITY_WARNING,
            context=context,
            suggestion=suggestion,
        )
        self.add(error)
        return True

    def report_error(
        self,
        error_type_str: str,
        message: str,
        line_no: int = -1,
        severity_str: str = "错误",
    ) -> bool:
        """
        报告错误（兼容性方法，用于 DependencyResolver）

        Args:
            error_type_str: 错误类型字符串
            message: 错误消息
            line_no: 行号
            severity_str: 严重程度字符串

        Returns:
            是否添加成功
        """
        error_code = self._ERROR_CODE_MAP.get(
            error_type_str, PIPELINE_COMPILE_UNSUPPORTED_FEATURE
        )
        severity = (
            ZHCError.SEVERITY_WARNING
            if severity_str == "警告"
            else ZHCError.SEVERITY_ERROR
        )

        location = None
        if line_no > 0:
            location = SourceLocation(line=line_no)

        error = PipelineError(
            message=message,
            location=location,
            error_code=error_code,
            severity=severity,
        )
        self.add(error)
        return True

    def has_errors(self) -> bool:
        """是否有错误"""
        return self._collection.has_errors()

    def has_fatal_errors(self) -> bool:
        """是否有致命错误"""
        return any(e.is_error() for e in self._errors)

    def get_errors(self, severity: Optional[str] = None) -> List[PipelineError]:
        """
        获取错误列表

        Args:
            severity: 过滤严重程度（可选）

        Returns:
            错误列表
        """
        if severity is None:
            return self._errors.copy()
        return [e for e in self._errors if e.severity == severity]

    def get_all_errors(self) -> List[Dict[str, Any]]:
        """获取所有错误的字典表示"""
        return [e.to_dict() for e in self._errors]

    def get_error_summary(self) -> str:
        """获取错误摘要"""
        return self._collection.summary()

    def clear(self):
        """清空所有错误记录"""
        self.reset()

    def __str__(self) -> str:
        """字符串表示"""
        return self.get_error_summary()


# ============================================================================
# SyntaxChecker 和 SemanticChecker
# ============================================================================


class SyntaxChecker:
    """语法检查器"""

    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler

    def check_module_declaration(self, line: str, line_no: int) -> bool:
        """检查模块声明语法"""
        import re

        pattern = r"^模块\s+(\w+)\s*\{$"
        match = re.match(pattern, line.strip())

        if not match:
            self.error_handler.add_error(
                PIPELINE_SYNTAX_INVALID_MODULE_DECL,
                f"无效的模块声明: {line}",
                line_no=line_no,
                context=line,
                suggestion="正确格式: '模块 模块名 {'",
            )
            return False
        return True

    def check_import_statement(self, line: str, line_no: int) -> bool:
        """检查导入语句语法"""
        import re

        pattern = r"^导入\s+(\w+)\s*;?$"
        match = re.match(pattern, line.strip())

        if not match:
            self.error_handler.add_error(
                PIPELINE_SYNTAX_INVALID_IMPORT_STMT,
                f"无效的导入语句: {line}",
                line_no=line_no,
                context=line,
                suggestion="正确格式: '导入 模块名;'",
            )
            return False
        return True

    def check_visibility_section(self, line: str, line_no: int) -> bool:
        """检查可见性区域语法"""
        valid_sections = ["公开:", "私有:", "保护:"]

        if line.strip() not in valid_sections:
            self.error_handler.add_error(
                PIPELINE_SYNTAX_INVALID_VISIBILITY,
                f"无效的可见性修饰符: {line}",
                line_no=line_no,
                context=line,
                suggestion=f"有效值: {', '.join(valid_sections)}",
            )
            return False
        return True


class SemanticChecker:
    """语义检查器"""

    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
        self.symbol_table: Dict[str, tuple] = {}  # 符号名 -> (模块名, 行号)

    def check_duplicate_symbol(
        self, symbol: str, module_name: str, line_no: int
    ) -> bool:
        """检查重复定义的符号"""
        key = f"{module_name}.{symbol}"

        if key in self.symbol_table:
            prev_module, prev_line = self.symbol_table[key]
            self.error_handler.add_error(
                PIPELINE_SEMANTIC_DUPLICATE_SYMBOL,
                f"符号 '{symbol}' 重复定义",
                line_no=line_no,
                context=f"之前定义在模块 '{prev_module}' 行 {prev_line}",
                suggestion="使用不同的符号名",
            )
            return True

        self.symbol_table[key] = (module_name, line_no)
        return False

    def check_undefined_symbol(
        self, symbol: str, module_name: str, line_no: int
    ) -> bool:
        """检查未定义的符号"""
        return False

    def reset(self):
        """重置检查器"""
        self.symbol_table.clear()


# ============================================================================
# 导出公共API
# ============================================================================

__all__ = [
    # 异常类
    "PipelineError",
    # 向后兼容枚举
    "ErrorType",
    # 错误代码
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
    # 便捷函数
    "file_not_found",
    "file_read_error",
    "dependency_cycle",
    "missing_module",
    "duplicate_symbol",
    "unsupported_feature",
    # 错误处理器
    "ErrorHandler",
    "SyntaxChecker",
    "SemanticChecker",
]

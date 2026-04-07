#!/usr/bin/env python3
"""
错误处理器 - 用于检测和报告模块系统的各种错误

错误类型：
1. 语法错误：不符合模块语法的代码
2. 语义错误：逻辑错误，如重复定义
3. 作用域错误：违反作用域规则的代码
4. 依赖错误：模块导入/导出问题
5. 编译错误：无法转换为C代码的问题
"""

from typing import List, Dict, Optional, Tuple
from enum import Enum
import re

class ErrorSeverity(Enum):
    """错误严重程度"""
    INFO = "信息"      # 信息性消息
    WARNING = "警告"   # 警告，可能有问题但不阻止编译
    ERROR = "错误"     # 错误，阻止正确编译
    FATAL = "致命错误" # 致命错误，无法继续处理

class ErrorType(Enum):
    """错误类型枚举"""
    # 语法错误
    SYNTAX_MISSING_BRACE = "缺少花括号"
    SYNTAX_UNEXPECTED_TOKEN = "意外的标记"
    SYNTAX_INVALID_MODULE_DECL = "无效的模块声明"
    SYNTAX_INVALID_IMPORT_STMT = "无效的导入语句"
    SYNTAX_INVALID_VISIBILITY = "无效的可见性修饰符"
    
    # 语义错误
    SEMANTIC_DUPLICATE_SYMBOL = "符号重复定义"
    SEMANTIC_UNDEFINED_SYMBOL = "未定义的符号"
    SEMANTIC_TYPE_MISMATCH = "类型不匹配"
    SEMANTIC_INVALID_RETURN = "无效的返回语句"
    
    # 作用域错误
    SCOPE_VIOLATION = "作用域违规"
    SCOPE_OUT_OF_SCOPE = "超出作用域访问"
    SCOPE_INVALID_ACCESS = "无效的访问控制"
    
    # 依赖错误
    DEPENDENCY_CYCLE = "循环依赖"
    DEPENDENCY_MISSING_MODULE = "缺失的模块依赖"
    DEPENDENCY_VERSION_CONFLICT = "版本冲突"
    
    # 编译错误
    COMPILE_CONVERSION_FAILED = "转换失败"
    COMPILE_UNSUPPORTED_FEATURE = "不支持的功能"

class ErrorRecord:
    """错误记录"""
    
    def __init__(self, 
                 error_type: ErrorType,
                 message: str,
                 line_no: int = -1,
                 column: int = -1,
                 severity: ErrorSeverity = ErrorSeverity.ERROR,
                 context: str = "",
                 suggestion: str = ""):
        """
        初始化错误记录
        
        Args:
            error_type: 错误类型
            message: 错误消息
            line_no: 行号
            column: 列号
            severity: 严重程度
            context: 上下文信息
            suggestion: 修复建议
        """
        self.error_type = error_type
        self.message = message
        self.line_no = line_no
        self.column = column
        self.severity = severity
        self.context = context
        self.suggestion = suggestion
        self.timestamp: Optional[float] = None  # 可以添加时间戳
        
    def __str__(self) -> str:
        """字符串表示"""
        location = f"行{self.line_no}" if self.line_no > 0 else "未知位置"
        column_info = f"列{self.column}" if self.column > 0 else ""
        
        return (f"[{self.severity.value}] {location} {column_info}: "
                f"{self.error_type.value} - {self.message}")
                
    def to_dict(self) -> Dict[str, object]:
        """转换为字典"""
        return {
            'type': self.error_type.value,
            'message': self.message,
            'line': self.line_no,
            'column': self.column,
            'severity': self.severity.value,
            'context': self.context,
            'suggestion': self.suggestion
        }

class ErrorHandler:
    """错误处理器主类"""
    
    def __init__(self, max_errors: int = 100, max_warnings: int = 200):
        """
        初始化错误处理器
        
        Args:
            max_errors: 最大错误数，超过此数停止处理
            max_warnings: 最大警告数
        """
        self.errors: List[ErrorRecord] = []
        self.max_errors = max_errors
        self.max_warnings = max_warnings
        
        # 错误统计 - 分离int和dict避免Union类型问题
        self.total_errors: int = 0
        self.total_warnings: int = 0
        self.total_infos: int = 0
        self.fatal_errors: int = 0
        self.errors_by_type: Dict[str, int] = {}
        
    def reset(self):
        """重置错误处理器"""
        self.errors.clear()
        self.total_errors = 0
        self.total_warnings = 0
        self.total_infos = 0
        self.fatal_errors = 0
        self.errors_by_type = {}
        
    def add_error(self, error_type: ErrorType, message: str, 
                  line_no: int = -1, column: int = -1,
                  context: str = "", suggestion: str = "") -> bool:
        """
        添加错误记录
        
        Returns:
            是否添加成功（如果达到最大错误数则返回False）
        """
        if self.total_errors >= self.max_errors:
            return False
            
        error = ErrorRecord(
            error_type=error_type,
            message=message,
            line_no=line_no,
            column=column,
            severity=ErrorSeverity.ERROR,
            context=context,
            suggestion=suggestion
        )
        
        self.errors.append(error)
        self._update_stats(error)
        return True
        
    def add_warning(self, error_type: ErrorType, message: str,
                   line_no: int = -1, column: int = -1,
                   context: str = "", suggestion: str = "") -> bool:
        """
        添加警告记录
        
        Returns:
            是否添加成功（如果达到最大警告数则返回False）
        """
        if self.total_warnings >= self.max_warnings:
            return False
            
        error = ErrorRecord(
            error_type=error_type,
            message=message,
            line_no=line_no,
            column=column,
            severity=ErrorSeverity.WARNING,
            context=context,
            suggestion=suggestion
        )
        
        self.errors.append(error)
        self._update_stats(error)
        return True
        
    def add_info(self, error_type: ErrorType, message: str,
                line_no: int = -1, column: int = -1,
                context: str = "", suggestion: str = "") -> bool:
        """
        添加信息记录
        """
        error = ErrorRecord(
            error_type=error_type,
            message=message,
            line_no=line_no,
            column=column,
            severity=ErrorSeverity.INFO,
            context=context,
            suggestion=suggestion
        )
        
        self.errors.append(error)
        self._update_stats(error)
        return True
        
    def add_fatal(self, error_type: ErrorType, message: str,
                 line_no: int = -1, column: int = -1,
                 context: str = "", suggestion: str = "") -> bool:
        """
        添加致命错误记录
        """
        error = ErrorRecord(
            error_type=error_type,
            message=message,
            line_no=line_no,
            column=column,
            severity=ErrorSeverity.FATAL,
            context=context,
            suggestion=suggestion
        )
        
        self.errors.append(error)
        self._update_stats(error)
        return True
    
    def report_error(self, error_type_str: str, message: str, 
                    line_no: int = -1, severity_str: str = "错误") -> bool:
        """
        报告错误（兼容性方法，用于dependency_resolver）
        
        Args:
            error_type_str: 错误类型字符串
            message: 错误消息
            line_no: 行号
            severity_str: 严重程度字符串（"信息"、"警告"、"错误"、"致命错误"）
            
        Returns:
            是否添加成功
        """
        # 将字符串转换为枚举
        if severity_str == "信息":
            severity = ErrorSeverity.INFO
        elif severity_str == "警告":
            severity = ErrorSeverity.WARNING
        elif severity_str == "致命错误":
            severity = ErrorSeverity.FATAL
        else:
            severity = ErrorSeverity.ERROR
        
        # 创建自定义错误类型 - 使用固定ErrorType避免类型不兼容
        fallback_type = ErrorType.COMPILE_UNSUPPORTED_FEATURE

        # 根据严重程度调用相应的方法
        if severity == ErrorSeverity.INFO:
            return self.add_info(fallback_type, message, line_no)
        elif severity == ErrorSeverity.WARNING:
            return self.add_warning(fallback_type, message, line_no)
        elif severity == ErrorSeverity.FATAL:
            return self.add_fatal(fallback_type, message, line_no)
        else:
            return self.add_error(fallback_type, message, line_no)
        
    def _update_stats(self, error: ErrorRecord):
        """更新统计信息"""
        error_type_str = error.error_type.value
        
        # 更新总数
        if error.severity == ErrorSeverity.ERROR:
            self.total_errors += 1
        elif error.severity == ErrorSeverity.WARNING:
            self.total_warnings += 1
        elif error.severity == ErrorSeverity.INFO:
            self.total_infos += 1
        elif error.severity == ErrorSeverity.FATAL:
            self.fatal_errors += 1
            
        # 更新类型统计
        if error_type_str not in self.errors_by_type:
            self.errors_by_type[error_type_str] = 0
        self.errors_by_type[error_type_str] += 1
        
    def has_errors(self) -> bool:
        """是否有错误"""
        return self.total_errors > 0 or self.fatal_errors > 0
        
    def has_fatal_errors(self) -> bool:
        """是否有致命错误"""
        return self.fatal_errors > 0
        
    def get_errors(self, severity: Optional[ErrorSeverity] = None) -> List[ErrorRecord]:
        """获取错误记录"""
        if severity is None:
            return self.errors.copy()
        else:
            return [e for e in self.errors if e.severity == severity]
    
    def get_all_errors(self) -> List[Dict[str, object]]:
        """获取所有错误的字典表示（兼容性方法）"""
        return [error.to_dict() for error in self.errors]
            
    def get_error_summary(self) -> str:
        """获取错误摘要"""
        summary = []
        summary.append("=" * 60)
        summary.append("错误处理摘要")
        summary.append("=" * 60)
        
        summary.append(f"\n📊 统计信息:")
        summary.append(f"  总错误数: {self.total_errors}")
        summary.append(f"  总警告数: {self.total_warnings}")
        summary.append(f"  总信息数: {self.total_infos}")
        summary.append(f"  致命错误: {self.fatal_errors}")
        
        if self.errors_by_type:
            summary.append(f"\n📋 按类型分类:")
            for error_type, count in sorted(self.errors_by_type.items()):
                summary.append(f"  {error_type}: {count}")
                
        # 显示前5个错误（如果有）
        error_records = self.get_errors(ErrorSeverity.ERROR)
        if error_records:
            summary.append(f"\n❌ 主要错误 ({min(5, len(error_records))} 个):")
            for i, error in enumerate(error_records[:5], 1):
                summary.append(f"  {i}. {error}")
                
        # 显示前3个致命错误（如果有）
        fatal_records = self.get_errors(ErrorSeverity.FATAL)
        if fatal_records:
            summary.append(f"\n💀 致命错误 ({len(fatal_records)} 个):")
            for i, error in enumerate(fatal_records, 1):
                summary.append(f"  {i}. {error}")
                
        summary.append("=" * 60)
        return '\n'.join(summary)
        
    def clear(self):
        """清空所有错误记录"""
        self.reset()
        
    def __str__(self) -> str:
        """字符串表示"""
        return self.get_error_summary()

class SyntaxChecker:
    """语法检查器"""
    
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
        
    def check_module_declaration(self, line: str, line_no: int) -> bool:
        """
        检查模块声明语法
        
        Returns:
            是否语法正确
        """
        # 模块声明的正则表达式
        pattern = r'^模块\s+(\w+)\s*\{$'
        match = re.match(pattern, line.strip())
        
        if not match:
            self.error_handler.add_error(
                ErrorType.SYNTAX_INVALID_MODULE_DECL,
                f"无效的模块声明: {line}",
                line_no,
                context=line,
                suggestion="正确格式: '模块 模块名 {'"
            )
            return False
            
        return True
        
    def check_import_statement(self, line: str, line_no: int) -> bool:
        """
        检查导入语句语法
        """
        pattern = r'^导入\s+(\w+)\s*;?$'
        match = re.match(pattern, line.strip())
        
        if not match:
            self.error_handler.add_error(
                ErrorType.SYNTAX_INVALID_IMPORT_STMT,
                f"无效的导入语句: {line}",
                line_no,
                context=line,
                suggestion="正确格式: '导入 模块名;'"
            )
            return False
            
        return True
        
    def check_visibility_section(self, line: str, line_no: int) -> bool:
        """
        检查可见性区域语法
        """
        valid_sections = ['公开:', '私有:', '保护:']
        
        if line.strip() not in valid_sections:
            self.error_handler.add_error(
                ErrorType.SYNTAX_INVALID_VISIBILITY,
                f"无效的可见性修饰符: {line}",
                line_no,
                context=line,
                suggestion=f"有效值: {', '.join(valid_sections)}"
            )
            return False
            
        return True

class SemanticChecker:
    """语义检查器"""
    
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
        self.symbol_table: Dict[str, Tuple[str, int]] = {}  # 符号名 -> (模块名, 行号)
        
    def check_duplicate_symbol(self, symbol: str, module_name: str, 
                              line_no: int) -> bool:
        """
        检查重复定义的符号
        
        Returns:
            是否重复
        """
        key = f"{module_name}.{symbol}"
        
        if key in self.symbol_table:
            prev_module, prev_line = self.symbol_table[key]
            self.error_handler.add_error(
                ErrorType.SEMANTIC_DUPLICATE_SYMBOL,
                f"符号 '{symbol}' 重复定义",
                line_no,
                context=f"之前定义在模块 '{prev_module}' 行 {prev_line}",
                suggestion="使用不同的符号名"
            )
            return True
            
        self.symbol_table[key] = (module_name, line_no)
        return False
        
    def check_undefined_symbol(self, symbol: str, module_name: str,
                              line_no: int) -> bool:
        """
        检查未定义的符号（简化版本）
        
        Returns:
            是否未定义
        """
        # 在实际实现中，需要检查符号是否在模块中定义
        # 这里只是占位实现
        return False
        
    def reset(self):
        """重置检查器"""
        self.symbol_table.clear()

def test_error_handler():
    """测试错误处理器功能"""
    print("🧪 测试错误处理器")
    print("=" * 60)
    
    handler = ErrorHandler(max_errors=5, max_warnings=5)
    
    # 添加各种类型的错误
    handler.add_error(
        ErrorType.SYNTAX_INVALID_MODULE_DECL,
        "缺少模块名",
        10,
        context="模块 {",
        suggestion="添加模块名: '模块 模块名 {'"
    )
    
    handler.add_warning(
        ErrorType.SEMANTIC_DUPLICATE_SYMBOL,
        "函数名重复",
        15,
        context="函数 加法(...",
        suggestion="使用不同的函数名"
    )
    
    handler.add_info(
        ErrorType.DEPENDENCY_MISSING_MODULE,
        "依赖模块未找到",
        20,
        context="导入 缺失模块;",
        suggestion="确保模块已定义"
    )
    
    handler.add_fatal(
        ErrorType.COMPILE_CONVERSION_FAILED,
        "无法转换复杂表达式",
        25,
        context="返回 (a + b) * c / d;",
        suggestion="简化表达式"
    )
    
    # 显示错误摘要
    print(handler.get_error_summary())
    
    # 检查状态
    print(f"\n📊 状态检查:")
    print(f"  是否有错误: {handler.has_errors()}")
    print(f"  是否有致命错误: {handler.has_fatal_errors()}")
    print(f"  错误总数: {len(handler.get_errors(ErrorSeverity.ERROR))}")
    print(f"  警告总数: {len(handler.get_errors(ErrorSeverity.WARNING))}")
    
    # 测试语法检查器
    print("\n🔍 测试语法检查器:")
    syntax_checker = SyntaxChecker(handler)
    
    test_cases = [
        ("模块 数学库 {", True),
        ("模块 {", False),  # 缺少模块名
        ("导入 工具库;", True),
        ("导入 ;", False),  # 缺少模块名
        ("公开:", True),
        ("私有:", True),
        ("无效:", False),  # 无效的可见性
    ]
    
    for line, expected in test_cases:
        if line.startswith("模块"):
            result = syntax_checker.check_module_declaration(line, 1)
        elif line.startswith("导入"):
            result = syntax_checker.check_import_statement(line, 1)
        else:
            result = syntax_checker.check_visibility_section(line, 1)
            
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{line}' -> 预期: {expected}, 实际: {result}")
        
    return True

if __name__ == "__main__":
    test_error_handler()
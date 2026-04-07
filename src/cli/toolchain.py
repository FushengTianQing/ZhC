#!/usr/bin/env python3
"""
Day 27: 工具链优化

功能：
1. 增强错误提示系统
2. 优化编译性能
3. 调试信息支持
4. 开发者工具包
"""

import sys
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ErrorLevel(Enum):
    """错误级别"""
    INFO = "信息"
    WARNING = "警告"
    ERROR = "错误"
    FATAL = "致命"


class ErrorCode(Enum):
    """错误代码"""
    # 词法错误 (1000-1999)
    LEX_UNEXPECTED_CHAR = 1001
    LEX_UNCLOSED_STRING = 1002
    LEX_INVALID_NUMBER = 1003

    # 语法错误 (2000-2999)
    SYNTAX_UNEXPECTED_TOKEN = 2001
    SYNTAX_MISSING_TOKEN = 2002
    SYNTAX_INVALID_EXPRESSION = 2003

    # 语义错误 (3000-3999)
    SEMANTIC_UNDECLARED = 3001
    SEMANTIC_REDECLARED = 3002
    SEMANTIC_TYPE_MISMATCH = 3003

    # 内存错误 (4000-4999)
    MEMORY_LEAK = 4001
    MEMORY_DOUBLE_FREE = 4002
    MEMORY_NULL_POINTER = 4003
    MEMORY_OUT_OF_BOUNDS = 4004


@dataclass
class CompilerError:
    """编译器错误"""
    code: ErrorCode
    level: ErrorLevel
    line: int
    column: int
    message: str
    suggestion: str = ""
    context: str = ""


class EnhancedErrorHandler:
    """增强的错误处理器"""

    ERROR_MESSAGES = {
        ErrorCode.LEX_UNEXPECTED_CHAR: ("意外的字符", "检查字符编码是否正确"),
        ErrorCode.LEX_UNCLOSED_STRING: ("未闭合的字符串", "确保字符串以引号结尾"),
        ErrorCode.LEX_INVALID_NUMBER: ("无效的数字", "检查数字格式是否正确"),
        ErrorCode.SYNTAX_UNEXPECTED_TOKEN: ("意外的标记", "检查语法结构是否正确"),
        ErrorCode.SYNTAX_MISSING_TOKEN: ("缺少标记", "检查是否缺少必要的关键字或符号"),
        ErrorCode.SYNTAX_INVALID_EXPRESSION: ("无效的表达式", "检查表达式语法是否正确"),
        ErrorCode.SEMANTIC_UNDECLARED: ("未声明的标识符", "先声明再使用"),
        ErrorCode.SEMANTIC_REDECLARED: ("重复声明", "标识符已被声明"),
        ErrorCode.SEMANTIC_TYPE_MISMATCH: ("类型不匹配", "检查左右两边类型是否一致"),
        ErrorCode.MEMORY_LEAK: ("可能的内存泄漏", "确保所有分配的内存都被释放"),
        ErrorCode.MEMORY_DOUBLE_FREE: ("双重释放", "内存只能被释放一次"),
        ErrorCode.MEMORY_NULL_POINTER: ("空指针解引用", "在使用指针前检查是否为空"),
        ErrorCode.MEMORY_OUT_OF_BOUNDS: ("数组越界", "检查数组索引是否在有效范围内"),
    }

    def __init__(self):
        self.errors: List[CompilerError] = []
        self.warnings: List[CompilerError] = []

    def add_error(self, code: ErrorCode, line: int, column: int = 0,
                  message: str = "", suggestion: str = ""):
        """添加错误"""
        if not message:
            msg, sugg = self.ERROR_MESSAGES.get(code, ("未知错误", ""))
            message = msg
            if not suggestion:
                suggestion = sugg

        level = self._get_level(code)
        error = CompilerError(
            code=code,
            level=level,
            line=line,
            column=column,
            message=message,
            suggestion=suggestion
        )

        if level == ErrorLevel.ERROR or level == ErrorLevel.FATAL:
            self.errors.append(error)
        else:
            self.warnings.append(error)

        return error

    def _get_level(self, code: ErrorCode) -> ErrorLevel:
        """获取错误级别"""
        if code.value < 2000:
            return ErrorLevel.ERROR
        elif code.value < 3000:
            return ErrorLevel.ERROR
        elif code.value < 4000:
            return ErrorLevel.WARNING
        else:
            return ErrorLevel.ERROR

    def format_error(self, error: CompilerError) -> str:
        """格式化错误信息"""
        lines = [
            f"{error.level.value} {error.code.name} (行 {error.line})",
            f"  {error.message}",
        ]
        if error.suggestion:
            lines.append(f"  建议: {error.suggestion}")
        return '\n'.join(lines)

    def format_summary(self) -> str:
        """格式化错误摘要"""
        lines = ["=" * 60, "编译错误摘要", "=" * 60]

        if self.errors:
            lines.append(f"\n错误 ({len(self.errors)}):")
            for err in self.errors:
                lines.append(self.format_error(err))

        if self.warnings:
            lines.append(f"\n警告 ({len(self.warnings)}):")
            for warn in self.warnings:
                lines.append(self.format_error(warn))

        if not self.errors and not self.warnings:
            lines.append("\n编译成功，无错误或警告")

        return '\n'.join(lines)

    def has_fatal_errors(self) -> bool:
        """是否有致命错误"""
        return any(e.level == ErrorLevel.FATAL for e in self.errors)


class PerformanceOptimizer:
    """性能优化器"""

    def __init__(self):
        self.stats: Dict[str, float] = {
            'lexical_time': 0.0,
            'syntax_time': 0.0,
            'semantic_time': 0.0,
            'codegen_time': 0.0,
            'total_time': 0.0,
        }

    def measure(self, phase: str, func, *args, **kwargs):
        """测量阶段执行时间"""
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start

        if phase in self.stats:
            self.stats[phase] = elapsed

        return result

    def get_report(self) -> str:
        """获取性能报告"""
        lines = [
            "=" * 60,
            "性能报告",
            "=" * 60,
        ]

        for phase, time_val in self.stats.items():
            lines.append(f"{phase}: {time_val*1000:.2f}ms")

        total = sum(self.stats.values())
        lines.append(f"总计: {total*1000:.2f}ms")

        return '\n'.join(lines)


class DebugInfoGenerator:
    """调试信息生成器"""

    def __init__(self):
        self.line_mapping: Dict[int, str] = {}
        self.symbol_table: Dict[str, Dict] = {}

    def add_line_mapping(self, line: int, filename: str):
        """添加行映射"""
        self.line_mapping[line] = filename

    def add_symbol(self, name: str, type_name: str, line: int):
        """添加符号信息"""
        self.symbol_table[name] = {
            'type': type_name,
            'line': line,
        }

    def get_symbol_info(self, name: str) -> Optional[Dict]:
        """获取符号信息"""
        return self.symbol_table.get(name)

    def generate_debug_info(self) -> str:
        """生成调试信息"""
        lines = ["// 调试信息"]

        lines.append(f"// 源文件行数: {len(self.line_mapping)}")
        lines.append(f"// 符号数: {len(self.symbol_table)}")

        return '\n'.join(lines)


# 测试
if __name__ == '__main__':
    print("=== Day 27 工具链测试 ===")

    # 测试错误处理
    print("\n--- 错误处理 ---")
    handler = EnhancedErrorHandler()
    handler.add_error(ErrorCode.SYNTAX_UNEXPECTED_TOKEN, 10, 5, suggestion="检查语法")
    handler.add_error(ErrorCode.MEMORY_LEAK, 25, suggestion="释放内存")
    handler.add_error(ErrorCode.LEX_UNCLOSED_STRING, 5)
    print(handler.format_summary())

    # 测试性能优化
    print("\n--- 性能优化 ---")
    optimizer = PerformanceOptimizer()

    def dummy_function():
        time.sleep(0.01)
        return 42

    optimizer.measure('lexical_time', dummy_function)
    print(optimizer.get_report())

    # 测试调试信息
    print("\n--- 调试信息 ---")
    debugger = DebugInfoGenerator()
    debugger.add_symbol("ptr", "int*", 10)
    debugger.add_symbol("count", "int", 15)
    print(debugger.generate_debug_info())
    print(f"ptr 信息: {debugger.get_symbol_info('ptr')}")

    print("\n=== 测试完成 ===")
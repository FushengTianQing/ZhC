#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码转换器 - 将中文模块代码转换为C代码

核心功能：
1. 模块声明转换：模块 模块名 { ... } → C头文件/源文件结构
2. 导入语句转换：导入 模块名 → #include "module_name.h"
3. 符号转换：中文符号 → 限定C符号名
4. 错误检查：语法和语义错误检测

作者：远
日期：2026-04-03

重构说明：
- 错误处理已分离到 ConversionErrorHandler
- 关注点分离：转换逻辑与错误处理解耦
"""

import os
import re
from typing import List, Dict, Tuple, Optional, Set

from .conversion_error_handler import ConversionErrorHandler
from .type_converter import TypeConverter


class ConversionType:
    """转换类型枚举（兼容性别名）"""
    MODULE_DECLARATION = "module_declaration"
    IMPORT_STATEMENT = "import_statement"
    SYMBOL_DEFINITION = "symbol_definition"
    FUNCTION_DEFINITION = "function_definition"
    VARIABLE_DEFINITION = "variable_definition"


class CodeConverter:
    """
    代码转换器主类

    职责：
    1. 中文代码到C代码的转换
    2. 模块、导入、符号的转换
    3. 类型关键字映射

    注意：错误处理已委托给 ConversionErrorHandler
    """

    def __init__(self, scope_manager=None, error_handler: ConversionErrorHandler = None):
        """
        初始化代码转换器

        Args:
            scope_manager: 作用域管理器实例，用于符号查找和可见性控制
            error_handler: 错误处理器实例，如果为None则创建默认实例
        """
        self.scope_manager = scope_manager
        self.output_lines = []
        self.conversion_stats = {
            'modules_converted': 0,
            'imports_converted': 0,
            'symbols_converted': 0,
            'errors_found': 0,
            'warnings_found': 0
        }

        # 模块映射表：模块名 -> (头文件路径, 源文件路径)
        self.module_map = {}

        # 已转换的符号缓存
        self.converted_symbols = set()

        # 错误处理器
        self._error_handler = error_handler or ConversionErrorHandler()
        
        # 类型转换器
        self._type_converter = TypeConverter()

    @property
    def errors(self) -> List[Dict]:
        """获取错误列表（兼容性别名）"""
        return self._error_handler.to_dict_list()

    @property
    def warnings(self) -> List[Dict]:
        """获取警告列表（兼容性别名）"""
        return [w.to_dict() for w in self._error_handler.get_warnings()]

    def reset(self):
        """重置转换器状态"""
        self.output_lines = []
        self.conversion_stats = {
            'modules_converted': 0,
            'imports_converted': 0,
            'symbols_converted': 0,
            'errors_found': 0,
            'warnings_found': 0
        }
        self._error_handler.clear()
        self.converted_symbols.clear()

    def add_error(self, error_type: str, message: str, line_no: int = -1):
        """
        添加错误信息（委托给错误处理器）

        Args:
            error_type: 错误类型
            message: 错误消息
            line_no: 行号
        """
        self._error_handler.add_error(error_type, message, line_no)
        self.conversion_stats['errors_found'] += 1

    def add_warning(self, warning_type: str, message: str, line_no: int = -1):
        """
        添加警告信息（委托给错误处理器）

        Args:
            warning_type: 警告类型
            message: 警告消息
            line_no: 行号
        """
        self._error_handler.add_warning(warning_type, message, line_no)
        self.conversion_stats['warnings_found'] += 1

    def convert_module_declaration(self, module_name: str, content_lines: List[str],
                                  line_no: int = -1) -> Tuple[str, str]:
        """
        转换模块声明为C代码

        Args:
            module_name: 模块名
            content_lines: 模块内容行列表
            line_no: 行号（用于错误报告）

        Returns:
            (header_code, source_code) 元组
        """
        self.conversion_stats['modules_converted'] += 1

        # 生成头文件保护宏
        guard_macro = f"__{module_name.upper()}_H__"

        # 构建头文件内容
        header_lines = [
            f"/* {module_name}模块 - 自动生成的头文件 */",
            f"#ifndef {guard_macro}",
            f"#define {guard_macro}",
            "",
            "#ifdef __cplusplus",
            'extern "C" {',
            "#endif",
            ""
        ]

        # 构建源文件内容
        source_lines = [
            f"/* {module_name}模块 - 自动生成的源文件 */",
            f'#include "{module_name}.h"',
            ""
        ]

        # 解析模块内容
        in_public_section = False
        in_private_section = False
        current_visibility = 'private'  # 默认私有

        for i, line in enumerate(content_lines, 1):
            line = line.strip()
            if not line:
                continue

            # 检查可见性区域开始
            if line == '公开:':
                current_visibility = 'public'
                in_public_section = True
                in_private_section = False
                continue
            elif line == '私有:':
                current_visibility = 'private'
                in_private_section = True
                in_public_section = False
                continue
            elif line == '保护:':
                current_visibility = 'protected'
                in_public_section = False
                in_private_section = False
                continue

            # 转换符号定义
            if current_visibility in ['public', 'private']:
                converted = self.convert_symbol_definition(
                    line, module_name, current_visibility, line_no + i
                )

                if converted:
                    if current_visibility == 'public':
                        # 公开符号添加到头文件
                        header_lines.append(converted + ';')
                    # 所有符号定义都添加到源文件
                    source_lines.append(converted + ';')

        # 结束头文件
        header_lines.extend([
            "",
            "#ifdef __cplusplus",
            "}",
            "#endif",
            "",
            f"#endif /* {guard_macro} */"
        ])

        header_code = '\n'.join(header_lines)
        source_code = '\n'.join(source_lines)

        # 记录模块映射
        self.module_map[module_name] = (f"{module_name}.h", f"{module_name}.c")

        return header_code, source_code

    def convert_import_statement(self, module_name: str, line_no: int = -1) -> str:
        """
        转换导入语句为C的#include指令

        Args:
            module_name: 要导入的模块名
            line_no: 行号

        Returns:
            C的#include指令字符串
        """
        self.conversion_stats['imports_converted'] += 1

        # 检查模块是否存在
        if module_name not in self.module_map:
            self.add_warning(
                'UNDEFINED_MODULE',
                f"模块 '{module_name}' 未定义，可能需要在其他地方定义",
                line_no
            )

        return f'#include "{module_name}.h"'

    def convert_symbol_definition(self, line: str, module_name: str,
                                 visibility: str, line_no: int = -1) -> Optional[str]:
        """
        转换符号定义（函数、变量等）

        Args:
            line: 原始代码行
            module_name: 所属模块名
            visibility: 可见性（public/private/protected）
            line_no: 行号

        Returns:
            转换后的C代码行，如果没有匹配则返回None
        """
        # 检查是否是函数定义
        func_match = re.match(r'函数\s+(\w+)\s*\((.*)\)\s*->\s*(\w+)\s*\{', line)
        if func_match:
            return self.convert_function_definition(func_match, module_name, visibility, line_no)

        # 检查是否是变量定义
        var_patterns = [
            r'(\w+型)\s+(\w+)\s*=\s*(.+);',  # 类型 变量 = 值;
            r'(\w+型)\s+(\w+)\s*;',          # 类型 变量;
        ]

        for pattern in var_patterns:
            var_match = re.match(pattern, line)
            if var_match:
                return self.convert_variable_definition(var_match, module_name, visibility, line_no)

        # 检查是否是其他声明
        if ';' in line and ('=' in line or re.search(r'\w+型', line)):
            # 可能是简化的变量声明
            return self.convert_general_declaration(line, module_name, visibility, line_no)

        # 未匹配任何模式
        self.add_warning(
            'UNKNOWN_SYNTAX',
            f"无法识别的语法: {line}",
            line_no
        )
        return None

    def convert_function_definition(self, match, module_name: str,
                                   visibility: str, line_no: int) -> str:
        """
        转换函数定义

        Args:
            match: 正则匹配对象
            module_name: 模块名
            visibility: 可见性
            line_no: 行号

        Returns:
            转换后的函数声明
        """
        func_name = match.group(1)
        params = match.group(2)
        return_type = match.group(3)

        # 转换类型
        c_return_type = self.convert_type_keyword(return_type)

        # 转换参数
        if params.strip():
            c_params = self.convert_parameter_list(params)
        else:
            c_params = 'void'

        # 生成限定函数名
        if visibility == 'public':
            qualified_name = f"{module_name}_{func_name}"
        else:
            qualified_name = f"{module_name}_{func_name}"
            # 私有函数需要static修饰
            c_return_type = f"static {c_return_type}"

        # 记录已转换的符号
        symbol_key = f"{module_name}.{func_name}"
        if symbol_key in self.converted_symbols:
            self.add_error(
                'DUPLICATE_SYMBOL',
                f"符号 '{func_name}' 重复定义",
                line_no
            )
            is_duplicate = True
        else:
            self.converted_symbols.add(symbol_key)
            is_duplicate = False

        # 只有在不是重复符号时才增加计数
        if not is_duplicate:
            self.conversion_stats['symbols_converted'] += 1

        return f"{c_return_type} {qualified_name}({c_params})"

    def convert_variable_definition(self, match, module_name: str,
                                   visibility: str, line_no: int) -> str:
        """
        转换变量定义

        Args:
            match: 正则匹配对象
            module_name: 模块名
            visibility: 可见性
            line_no: 行号

        Returns:
            转换后的变量声明
        """
        var_type = match.group(1)
        var_name = match.group(2)

        # 转换类型
        c_type = self.convert_type_keyword(var_type)

        # 生成限定变量名
        if visibility == 'public':
            qualified_name = f"{module_name}_{var_name}"
        else:
            qualified_name = f"{module_name}_{var_name}"
            # 私有变量需要static修饰
            c_type = f"static {c_type}"

        # 检查重复符号
        symbol_key = f"{module_name}.{var_name}"
        if symbol_key in self.converted_symbols:
            self.add_error(
                'DUPLICATE_SYMBOL',
                f"符号 '{var_name}' 重复定义",
                line_no
            )
            is_duplicate = True
        else:
            self.converted_symbols.add(symbol_key)
            is_duplicate = False

        # 只有在不是重复符号时才增加计数
        if not is_duplicate:
            self.conversion_stats['symbols_converted'] += 1

        # 检查是否有初始值
        if len(match.groups()) > 2 and match.group(3):
            init_value = match.group(3)
            return f"{c_type} {qualified_name} = {init_value}"
        else:
            return f"{c_type} {qualified_name}"

    def convert_general_declaration(self, line: str, module_name: str,
                                   visibility: str, line_no: int) -> str:
        """
        转换一般声明

        Args:
            line: 原始代码行
            module_name: 模块名
            visibility: 可见性
            line_no: 行号

        Returns:
            转换后的声明
        """
        # 简单的替换转换
        converted = line

        # 使用 TypeConverter 替换类型关键字
        type_keywords = self._type_converter.get_all_type_keywords()
        for zh_type, c_type in type_keywords.items():
            converted = converted.replace(zh_type, c_type)

        # 添加模块前缀
        is_duplicate = False  # 初始化变量

        if '=' in converted:
            # 变量定义，在变量名前添加模块前缀
            parts = converted.split('=')
            var_decl = parts[0].strip()

            # 查找变量名（最后一个单词）
            words = var_decl.split()
            if words:
                var_name = words[-1]
                if var_name.endswith(';'):
                    var_name = var_name[:-1]

                # 检查重复符号
                symbol_key = f"{module_name}.{var_name}"
                if symbol_key in self.converted_symbols:
                    self.add_error(
                        'DUPLICATE_SYMBOL',
                        f"符号 '{var_name}' 重复定义",
                        line_no
                    )
                    is_duplicate = True
                else:
                    self.converted_symbols.add(symbol_key)
                    is_duplicate = False

                # 添加模块前缀
                if visibility == 'public':
                    qualified_name = f"{module_name}_{var_name}"
                else:
                    qualified_name = f"{module_name}_{var_name}"
                    # 如果是私有，需要添加static
                    if words[0] != 'static':
                        words[0] = f"static {words[0]}"

                words[-1] = qualified_name + (';' if var_name.endswith(';') else '')
                parts[0] = ' '.join(words)
                converted = ' = '.join(parts)

        # 只有在不是重复符号时才增加计数
        if not is_duplicate:
            self.conversion_stats['symbols_converted'] += 1
        return converted

    def convert_type_keyword(self, zh_type: str) -> str:
        """
        转换中文类型关键字为C类型

        Args:
            zh_type: 中文类型关键字

        Returns:
            C类型关键字
        """
        return self._type_converter.convert_type(zh_type)

    def convert_parameter_list(self, params: str) -> str:
        """
        转换参数列表

        Args:
            params: 中文参数列表字符串

        Returns:
            转换后的C参数列表
        """
        return self._type_converter.convert_parameter_list(params)

    def process_file(self, input_file: str, output_header: Optional[str] = None,
                    output_source: Optional[str] = None) -> bool:
        """
        处理整个文件

        Args:
            input_file: 输入文件路径
            output_header: 输出头文件路径（可选）
            output_source: 输出源文件路径（可选）

        Returns:
            是否成功处理
        """
        self.reset()

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 确定输出文件名
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            if output_header is None:
                output_header = f"{base_name}.h"
            if output_source is None:
                output_source = f"{base_name}.c"

            # 简化的文件处理逻辑
            # TODO: 与ModuleParser集成进行完整解析
            header_lines = [
                f"/* 自动生成的头文件 - 来自 {base_name}.zhc */",
                f"#ifndef __{base_name.upper()}_H__",
                f"#define __{base_name.upper()}_H__",
                "",
                "#ifdef __cplusplus",
                'extern "C" {',
                "#endif",
                "",
                "/* 函数声明 */",
                "",
                "#ifdef __cplusplus",
                "}",
                "#endif",
                "",
                f"#endif /* __{base_name.upper()}_H__ */"
            ]

            source_lines = [
                f"/* 自动生成的源文件 - 来自 {base_name}.zhc */",
                f'#include "{base_name}.h"',
                "",
                "/* 函数定义 */",
                ""
            ]

            # 写入头文件
            with open(output_header, 'w', encoding='utf-8') as f:
                f.write('\n'.join(header_lines))

            # 写入源文件
            with open(output_source, 'w', encoding='utf-8') as f:
                f.write('\n'.join(source_lines))

            print(f"✓ 文件转换完成:")
            print(f"  输入: {input_file}")
            print(f"  输出头文件: {output_header}")
            print(f"  输出源文件: {output_source}")
            print(f"  转换统计: {self.conversion_stats}")

            # 使用错误处理器获取错误
            errors = self._error_handler.get_errors()
            warnings = self._error_handler.get_warnings()

            if errors:
                print(f"\n⚠️  发现 {len(errors)} 个错误:")
                for error in errors:
                    print(f"  行{error.line_no}: [{error.error_type}] {error.message}")

            if warnings:
                print(f"\nℹ️  发现 {len(warnings)} 个警告:")
                for warning in warnings:
                    print(f"  行{warning.line_no}: [{warning.error_type}] {warning.message}")

            return len(errors) == 0

        except Exception as e:
            self.add_error('FILE_IO', f"文件处理失败: {e}", -1)
            print(f"✗ 文件处理失败: {e}")
            return False

    def get_statistics(self) -> Dict:
        """获取转换统计信息"""
        return self.conversion_stats.copy()

    def get_errors(self) -> List[Dict]:
        """获取错误列表"""
        return [e.to_dict() for e in self._error_handler.get_errors()]

    def get_warnings(self) -> List[Dict]:
        """获取警告列表"""
        return [w.to_dict() for w in self._error_handler.get_warnings()]

    def get_error_handler(self) -> ConversionErrorHandler:
        """获取错误处理器（用于外部访问）"""
        return self._error_handler

    def __str__(self) -> str:
        """字符串表示"""
        stats = self.get_statistics()
        return (
            f"CodeConverter - "
            f"模块: {stats['modules_converted']}, "
            f"导入: {stats['imports_converted']}, "
            f"符号: {stats['symbols_converted']}, "
            f"错误: {stats['errors_found']}, "
            f"警告: {stats['warnings_found']}"
        )
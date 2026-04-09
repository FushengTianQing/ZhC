# -*- coding: utf-8 -*-
"""
预处理器模块

支持 #define、#ifdef、#ifndef、#include 等预处理指令。

作者：阿福
日期：2026-04-09
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import re
import os


class PreprocessorError(Exception):
    """预处理器错误"""

    def __init__(self, message: str, line: int = 0, file: str = None):
        self.message = message
        self.line = line
        self.file = file
        super().__init__(f"{file or '<unknown>'}:{line}: {message}")


class MacroType(Enum):
    """宏类型"""

    OBJECT = "object"  # 对象宏: #define NAME value
    FUNCTION = "function"  # 函数宏: #define NAME(args) body


@dataclass
class Macro:
    """宏定义"""

    name: str
    body: str
    macro_type: MacroType = MacroType.OBJECT
    parameters: List[str] = field(default_factory=list)
    is_variadic: bool = False  # 是否支持可变参数
    definition_line: int = 0
    definition_file: str = ""


@dataclass
class PreprocessorConfig:
    """预处理器配置"""

    include_paths: List[str] = field(default_factory=list)
    stdlib_path: str = ""  # 标准库路径
    predefined_macros: Dict[str, str] = field(default_factory=dict)
    max_include_depth: int = 100
    max_macro_depth: int = 100


class Preprocessor:
    """
    预处理器

    支持:
    - #define NAME value (对象宏)
    - #define NAME(args) body (函数宏)
    - #undef NAME
    - #ifdef NAME / #ifndef NAME / #else / #endif
    - #include "file" / #include <file>
    """

    def __init__(self, config: PreprocessorConfig = None):
        self.config = config or PreprocessorConfig()
        self.macros: Dict[str, Macro] = {}
        self.included_files: Set[str] = set()
        self.include_stack: List[str] = []
        self.current_file: str = ""
        self.current_line: int = 0

        # 初始化内置预定义宏
        self._define_object_macro("__ZHC__", "1")
        self._define_object_macro("__ZHC_VERSION__", '"0.1.0"')
        self._define_object_macro("__ZHC_MAJOR__", "0")
        self._define_object_macro("__ZHC_MINOR__", "1")
        self._define_object_macro("__ZHC_PATCH__", "0")
        self._define_object_macro("__FILE__", '"<input>"')
        self._define_object_macro("__LINE__", "0")
        self._define_object_macro("__DATE__", '"2026-04-10"')
        self._define_object_macro("__TIME__", '"00:00:00"')

        # 初始化用户预定义宏
        for name, value in self.config.predefined_macros.items():
            self._define_object_macro(name, value)

    def _define_object_macro(
        self, name: str, value: str, line: int = 0, file: str = ""
    ):
        """定义对象宏"""
        self.macros[name] = Macro(
            name=name,
            body=value,
            macro_type=MacroType.OBJECT,
            definition_line=line,
            definition_file=file,
        )

    def _define_function_macro(
        self,
        name: str,
        parameters: List[str],
        body: str,
        is_variadic: bool = False,
        line: int = 0,
        file: str = "",
    ):
        """定义函数宏"""
        self.macros[name] = Macro(
            name=name,
            body=body,
            macro_type=MacroType.FUNCTION,
            parameters=parameters,
            is_variadic=is_variadic,
            definition_line=line,
            definition_file=file,
        )

    def _undef_macro(self, name: str):
        """取消宏定义"""
        if name in self.macros:
            del self.macros[name]

    def _is_macro_defined(self, name: str) -> bool:
        """检查宏是否已定义"""
        return name in self.macros

    def _eval_elif_condition(self, condition: str) -> bool:
        """
        评估 #elif 条件表达式

        支持:
        - defined(IDENTIFIER)
        - !defined(IDENTIFIER)
        - 简单的整数表达式（宏展开后）

        Args:
            condition: 条件表达式字符串

        Returns:
            条件是否为真
        """
        condition = condition.strip()

        # 处理 defined() 操作符
        # 替换 defined(NAME) 为 1 或 0
        def replace_defined(match):
            name = match.group(1).strip()
            return "1" if self._is_macro_defined(name) else "0"

        condition = re.sub(r"defined\s*\(\s*(\w+)\s*\)", replace_defined, condition)

        # 展开宏
        condition = self._expand_text(condition)

        # 尝试评估表达式
        try:
            # 简单的整数表达式评估
            # 支持: 数字、加减乘除、比较、逻辑运算
            result = self._eval_simple_expression(condition)
            return bool(result)
        except Exception:
            # 无法评估，返回 False
            return False

    def _eval_simple_expression(self, expr: str) -> int:
        """
        评估简单的整数表达式

        支持: 数字、加减乘除模、比较运算、逻辑运算、!0/!1

        Args:
            expr: 表达式字符串

        Returns:
            表达式结果（整数）
        """
        expr = expr.strip()

        # 移除空白
        expr = re.sub(r"\s+", "", expr)

        # 处理 C 预处理器特有的 !0 = 1, !1 = 0
        expr = re.sub(r"!([01])", lambda m: ("0" if m.group(1) == "1" else "1"), expr)

        # 处理逻辑运算符（转换为 Python 语法）
        expr = re.sub(r"&&", " and ", expr)
        expr = re.sub(r"\|\|", " or ", expr)

        # 处理比较运算符
        # C 预处理器比较返回 1 或 0
        expr = re.sub(r"==", " == ", expr)
        expr = re.sub(r"!=", " != ", expr)
        expr = re.sub(r"<=", " <= ", expr)
        expr = re.sub(r">=", " >= ", expr)
        expr = re.sub(r"<", " < ", expr)
        expr = re.sub(r">", " > ", expr)

        # 安全评估：只允许数字和运算符
        # 检查表达式是否只包含安全字符
        safe_chars = set("0123456789 +-*/%<>=!&|()andor")
        if not all(c in safe_chars for c in expr):
            raise ValueError(f"不安全的表达式: {expr}")

        # 使用 Python eval（已验证安全性）
        try:
            result = eval(expr, {"__builtins__": {}}, {})
            return int(result)
        except Exception:
            return 0

    def _parse_define(self, line: str) -> Tuple[str, Macro]:
        """
        解析 #define 指令

        支持格式:
        - #define NAME value
        - #define NAME value  // 注释
        - #define NAME(args) body
        - #define NAME(args, ...) body  // 可变参数
        """
        # 移除行尾注释
        if "//" in line:
            line = line[: line.index("//")]

        line = line.strip()

        # 检查是否是函数宏
        match = re.match(r"(\w+)\s*\(([^)]*)\)\s*(.*)", line)
        if match:
            name = match.group(1)
            params_str = match.group(2).strip()
            body = match.group(3).strip()

            # 解析参数
            is_variadic = False
            parameters = []

            if params_str:
                params = [p.strip() for p in params_str.split(",")]
                for p in params:
                    if p == "...":
                        is_variadic = True
                    elif p.endswith("..."):
                        # 命名可变参数 (如 args...)
                        is_variadic = True
                        parameters.append(p[:-3].strip())
                    else:
                        parameters.append(p)

            return name, Macro(
                name=name,
                body=body,
                macro_type=MacroType.FUNCTION,
                parameters=parameters,
                is_variadic=is_variadic,
            )

        # 对象宏
        parts = line.split(None, 1)
        name = parts[0]
        body = parts[1] if len(parts) > 1 else ""

        return name, Macro(name=name, body=body, macro_type=MacroType.OBJECT)

    def _expand_macro(self, name: str, args: List[str] = None, depth: int = 0) -> str:
        """
        展开宏

        Args:
            name: 宏名称
            args: 函数宏的参数列表
            depth: 递归深度

        Returns:
            展开后的文本
        """
        if depth > self.config.max_macro_depth:
            raise PreprocessorError(
                f"宏展开深度超过限制: {name}",
                line=self.current_line,
                file=self.current_file,
            )

        if name not in self.macros:
            return name

        macro = self.macros[name]

        if macro.macro_type == MacroType.OBJECT:
            # 对象宏：直接替换并递归展开
            return self._expand_text(macro.body, depth + 1)

        elif macro.macro_type == MacroType.FUNCTION:
            if args is None:
                # 函数宏没有参数，返回原样
                return name

            # 函数宏：参数替换
            body = macro.body

            # 构建参数映射
            param_map = {}
            for i, param in enumerate(macro.parameters):
                if i < len(args):
                    param_map[param] = args[i]

            # 处理可变参数
            if macro.is_variadic:
                extra_args = args[len(macro.parameters) :]
                param_map["__VA_ARGS__"] = ", ".join(extra_args)

            # 替换参数
            for param, value in param_map.items():
                # 使用正则表达式进行单词边界替换
                body = re.sub(r"\b" + re.escape(param) + r"\b", value, body)

            # 递归展开
            return self._expand_text(body, depth + 1)

        return name

    def _expand_text(self, text: str, depth: int = 0) -> str:
        """
        展开文本中的所有宏

        Args:
            text: 输入文本
            depth: 递归深度

        Returns:
            展开后的文本
        """
        if depth > self.config.max_macro_depth:
            return text

        result = []
        i = 0

        while i < len(text):
            # 检查是否是字符串字面量
            if text[i] in "\"'":
                # 读取整个字符串，不展开其中的宏
                quote = text[i]
                result.append(quote)
                i += 1
                while i < len(text) and text[i] != quote:
                    if text[i] == "\\" and i + 1 < len(text):
                        # 转义字符
                        result.append(text[i])
                        result.append(text[i + 1])
                        i += 2
                    else:
                        result.append(text[i])
                        i += 1
                if i < len(text):
                    result.append(text[i])  # 闭合引号
                    i += 1
                continue

            # 检查是否是标识符
            if text[i].isalpha() or text[i] == "_":
                # 读取标识符
                j = i
                while j < len(text) and (text[j].isalnum() or text[j] == "_"):
                    j += 1
                identifier = text[i:j]

                # 检查是否是宏
                if identifier in self.macros:
                    macro = self.macros[identifier]

                    if macro.macro_type == MacroType.FUNCTION:
                        # 检查是否有参数列表
                        if j < len(text) and text[j] == "(":
                            # 解析参数
                            args, end_pos = self._parse_macro_args(text, j)
                            expanded = self._expand_macro(identifier, args, depth)
                            result.append(expanded)
                            i = end_pos
                        else:
                            result.append(identifier)
                            i = j
                    else:
                        # 对象宏
                        expanded = self._expand_macro(identifier, None, depth)
                        result.append(expanded)
                        i = j
                else:
                    result.append(identifier)
                    i = j
            else:
                result.append(text[i])
                i += 1

        return "".join(result)

    def _parse_macro_args(self, text: str, start: int) -> Tuple[List[str], int]:
        """
        解析宏参数列表

        Args:
            text: 输入文本
            start: 参数列表开始位置 (左括号位置)

        Returns:
            (参数列表, 结束位置)
        """
        assert text[start] == "("

        args = []
        current_arg = []
        paren_depth = 1
        i = start + 1

        while i < len(text) and paren_depth > 0:
            char = text[i]

            if char == "(":
                paren_depth += 1
                current_arg.append(char)
            elif char == ")":
                paren_depth -= 1
                if paren_depth > 0:
                    current_arg.append(char)
            elif char == "," and paren_depth == 1:
                args.append("".join(current_arg).strip())
                current_arg = []
            else:
                current_arg.append(char)

            i += 1

        # 添加最后一个参数
        if current_arg or args:
            args.append("".join(current_arg).strip())

        return args, i

    def _parse_include_path(self, content: str) -> Tuple[str, bool]:
        """
        解析 #include 指令中的路径

        Args:
            content: include 指令后的内容

        Returns:
            (文件路径, 是否是系统头文件)
        """
        content = content.strip()

        # #include <file> - 系统头文件
        if content.startswith("<") and content.endswith(">"):
            return content[1:-1], True

        # #include "file" - 本地头文件
        if content.startswith('"') and content.endswith('"'):
            return content[1:-1], False

        # 无效格式
        raise PreprocessorError(
            f"无效的 #include 语法: {content}",
            line=self.current_line,
            file=self.current_file,
        )

    def _find_include_file(self, filename: str, is_system: bool) -> Optional[str]:
        """
        查找包含文件

        Args:
            filename: 文件名
            is_system: 是否是系统头文件

        Returns:
            文件的绝对路径，如果找不到则返回 None
        """
        # 搜索路径列表
        search_paths = []

        if not is_system:
            # 本地头文件：先搜索当前文件所在目录
            if self.current_file and self.current_file != "<input>":
                current_dir = os.path.dirname(os.path.abspath(self.current_file))
                search_paths.append(current_dir)

        # 添加命令行指定的 -I 路径
        search_paths.extend(self.config.include_paths)

        # 添加标准库路径
        if self.config.stdlib_path:
            search_paths.append(self.config.stdlib_path)

        # 在搜索路径中查找文件
        for path in search_paths:
            full_path = os.path.join(path, filename)
            if os.path.isfile(full_path):
                return os.path.abspath(full_path)

        # 找不到文件
        return None

    def _check_pragma_once(self, filepath: str) -> bool:
        """
        检查文件是否已包含（通过 #pragma once 或头文件保护）

        Args:
            filepath: 文件绝对路径

        Returns:
            True 如果文件已被包含（应该跳过），False 否则
        """
        abs_path = os.path.abspath(filepath)
        return abs_path in self.included_files

    def _process_include(self, content: str) -> str:
        """
        处理 #include 指令

        Args:
            content: include 指令后的内容

        Returns:
            包含文件的内容，如果应该跳过则返回空字符串
        """
        # 检查包含深度
        if len(self.include_stack) >= self.config.max_include_depth:
            raise PreprocessorError(
                f"#include 嵌套深度超过限制 ({self.config.max_include_depth})",
                line=self.current_line,
                file=self.current_file,
            )

        # 解析路径
        try:
            filename, is_system = self._parse_include_path(content)
        except PreprocessorError:
            raise

        # 查找文件
        filepath = self._find_include_file(filename, is_system)
        if filepath is None:
            raise PreprocessorError(
                f"找不到头文件: {filename}",
                line=self.current_line,
                file=self.current_file,
            )

        # 检查循环包含
        abs_path = os.path.abspath(filepath)
        if abs_path in self.include_stack:
            raise PreprocessorError(
                f"Circular include detected: {filename}",
                line=self.current_line,
                file=self.current_file,
            )

        # 检查是否已包含（用于防止重复包含）
        if abs_path in self.included_files:
            # 文件已包含，跳过
            return ""

        # 标记为已包含
        self.included_files.add(abs_path)
        self.include_stack.append(abs_path)

        # 保存当前文件信息
        old_file = self.current_file
        old_line = self.current_line

        try:
            # 读取文件内容
            with open(filepath, "r", encoding="utf-8") as f:
                file_content = f.read()

            # 处理包含的文件
            self.current_file = filepath
            result = self.process(file_content, filepath)

            return result

        except IOError as e:
            raise PreprocessorError(
                f"无法读取头文件: {filename}: {e}",
                line=self.current_line,
                file=self.current_file,
            )
        finally:
            # 恢复当前文件信息
            self.current_file = old_file
            self.current_line = old_line
            self.include_stack.pop()

    def process(self, source: str, filename: str = "<input>") -> str:
        """
        处理源代码

        Args:
            source: 源代码
            filename: 文件名

        Returns:
            处理后的代码
        """
        self.current_file = filename
        lines = source.split("\n")
        result_lines = []

        # 条件编译栈
        condition_stack: List[Tuple[bool, bool]] = []  # (当前条件, 是否已满足)

        i = 0
        while i < len(lines):
            self.current_line = i + 1
            line = lines[i]

            # 检查是否在条件编译的非活跃分支中
            in_active_branch = all(cond for cond, _ in condition_stack)

            stripped = line.strip()

            # 处理预处理指令
            if stripped.startswith("#"):
                directive = stripped[1:].strip()

                # #define
                if directive.startswith("define"):
                    if in_active_branch:
                        define_content = directive[6:].strip()
                        name, macro = self._parse_define(define_content)
                        macro.definition_line = self.current_line
                        macro.definition_file = self.current_file
                        self.macros[name] = macro
                    i += 1
                    continue

                # #undef
                elif directive.startswith("undef"):
                    if in_active_branch:
                        name = directive[5:].strip()
                        self._undef_macro(name)
                    i += 1
                    continue

                # #if
                elif (
                    directive.startswith("if")
                    and not directive.startswith("ifdef")
                    and not directive.startswith("ifndef")
                ):
                    # #if EXPRESSION
                    if_content = directive[2:].strip()
                    is_true = self._eval_elif_condition(if_content)
                    if in_active_branch:
                        condition_stack.append((is_true, is_true))
                    else:
                        condition_stack.append((False, False))
                    i += 1
                    continue

                # #ifdef
                elif directive.startswith("ifdef"):
                    name = directive[5:].strip()
                    is_defined = self._is_macro_defined(name)
                    if in_active_branch:
                        condition_stack.append((is_defined, is_defined))
                    else:
                        condition_stack.append((False, False))
                    i += 1
                    continue

                # #ifndef
                elif directive.startswith("ifndef"):
                    name = directive[6:].strip()
                    is_defined = not self._is_macro_defined(name)
                    if in_active_branch:
                        condition_stack.append((is_defined, is_defined))
                    else:
                        condition_stack.append((False, False))
                    i += 1
                    continue

                # #else
                elif directive.startswith("else"):
                    if condition_stack:
                        current, satisfied = condition_stack.pop()
                        # 如果之前没有满足过，则取反
                        new_condition = not satisfied and all(
                            cond for cond, _ in condition_stack
                        )
                        condition_stack.append(
                            (new_condition, satisfied or new_condition)
                        )
                    i += 1
                    continue

                # #elif
                elif directive.startswith("elif"):
                    if condition_stack:
                        current, satisfied = condition_stack.pop()
                        # 只有当前面所有条件都不满足时才评估 #elif
                        if not satisfied:
                            # 解析 elif 条件（支持 defined() 操作符）
                            elif_content = directive[4:].strip()
                            is_true = self._eval_elif_condition(elif_content)
                            new_condition = is_true and all(
                                cond for cond, _ in condition_stack
                            )
                            condition_stack.append(
                                (new_condition, satisfied or is_true)
                            )
                        else:
                            # 前面已满足，#elif 条件为假
                            condition_stack.append((False, satisfied))
                    i += 1
                    continue

                # #endif
                elif directive.startswith("endif"):
                    if condition_stack:
                        condition_stack.pop()
                    i += 1
                    continue

                # #include
                elif directive.startswith("include"):
                    if in_active_branch:
                        include_content = directive[7:].strip()
                        included_content = self._process_include(include_content)
                        if included_content:
                            result_lines.append(included_content)
                    i += 1
                    continue

            # 非预处理指令：展开宏
            if in_active_branch:
                expanded = self._expand_text(line)
                result_lines.append(expanded)

            i += 1

        return "\n".join(result_lines)


def preprocess(source: str, config: PreprocessorConfig = None) -> str:
    """
    预处理便捷函数

    Args:
        source: 源代码
        config: 预处理器配置

    Returns:
        处理后的代码
    """
    preprocessor = Preprocessor(config)
    return preprocessor.process(source)

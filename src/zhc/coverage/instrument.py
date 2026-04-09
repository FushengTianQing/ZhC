#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码插桩模块

为源代码添加覆盖率追踪代码
"""

from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path


class Instrumenter:
    """代码插桩器"""

    def __init__(self):
        """初始化"""
        self.executable_lines: Dict[str, Set[int]] = {}
        self._branch_counter = 0
        self._function_counter = 0

    def instrument_file(
        self, source_path: str, output_path: Optional[str] = None
    ) -> str:
        """插桩源文件"""
        with open(source_path, "r", encoding="utf-8") as f:
            content = f.read()

        file_path = str(Path(source_path).resolve())

        # 分析可执行行
        executable_lines = self._find_executable_lines(content)
        self.executable_lines[file_path] = executable_lines

        # 添加插桩代码
        instrumented = self._add_instrumentation(content, file_path, executable_lines)

        # 写入输出文件
        if output_path is None:
            output_path = source_path + ".instrumented"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(instrumented)

        return output_path

    def instrument_source(self, source: str, file_path: str = "unknown.c") -> str:
        """插桩源代码字符串"""
        executable_lines = self._find_executable_lines(source)
        self.executable_lines[file_path] = executable_lines
        return self._add_instrumentation(source, file_path, executable_lines)

    def _find_executable_lines(self, source: str) -> Set[int]:
        """分析可执行行"""
        lines = source.split("\n")
        executable = set()

        # 跟踪代码块深度
        brace_depth = 0
        in_string = False
        in_char = False
        in_comment = False
        in_line_comment = False

        i = 0
        while i < len(source):
            char = source[i]
            next_char = source[i + 1] if i + 1 < len(source) else ""

            # 处理转义字符
            if i > 0 and source[i - 1] == "\\":
                i += 1
                continue

            # 处理注释
            if in_comment:
                if char == "*" and next_char == "/":
                    in_comment = False
                    i += 2
                    continue
                i += 1
                continue
            elif in_line_comment:
                if char == "\n":
                    in_line_comment = False
                i += 1
                continue

            # 检测注释开始
            if char == "/" and next_char == "*":
                in_comment = True
                i += 2
                continue
            elif char == "/" and next_char == "/":
                in_line_comment = True
                i += 2
                continue

            # 字符串/字符
            if char == '"' and not in_char:
                in_string = not in_string
                i += 1
                continue
            elif char == "'" and not in_string:
                in_char = not in_char
                i += 1
                continue

            # 在字符串或字符中
            if in_string or in_char:
                i += 1
                continue

            # 花括号计数
            if char == "{":
                brace_depth += 1
            elif char == "}":
                brace_depth -= 1

            i += 1

        # 重新分析，找出可执行行
        lines = source.split("\n")
        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # 跳过空行、注释、预处理指令
            if not stripped:
                continue
            if (
                stripped.startswith("//")
                or stripped.startswith("/*")
                or stripped.startswith("*")
            ):
                continue
            if stripped.startswith("#"):
                continue

            # 检查是否有可执行代码
            # 可执行语句结尾
            executable_statements = [";", "{", "}"]
            has_statement = any(stripped.endswith(s) for s in executable_statements)

            # 控制结构开头
            control_keywords = [
                "if",
                "else",
                "while",
                "for",
                "do",
                "switch",
                "case",
                "default",
                "return",
                "break",
                "continue",
                "goto",
                "try",
                "catch",
                "throw",
            ]

            is_control = any(
                stripped.startswith(kw + "(")
                or stripped.startswith(kw + " ")
                or stripped.startswith(kw + "{")
                or stripped == kw
                or stripped.startswith("if")
                or stripped.startswith("while")
                or stripped.startswith("for")
                or stripped.startswith("do")
                for kw in control_keywords
            )

            if has_statement or is_control or brace_depth > 0:
                if stripped.endswith("{") or stripped.endswith("}"):
                    pass  # 花括号单独一行不计入
                else:
                    executable.add(line_num)

        return executable

    def _add_instrumentation(
        self, source: str, file_path: str, executable_lines: Set[int]
    ) -> str:
        """添加插桩代码"""
        lines = source.split("\n")
        result = []

        # 预处理：找出所有需要插桩的位置
        instrumentation_lines: List[Tuple[int, str]] = []

        # 预处理：找出所有需要插桩的位置
        for line_num in sorted(executable_lines):
            if line_num > 0 and line_num <= len(lines):
                instrumentation_lines.append(
                    (line_num, f'_zhc_coverage_hit_line("{file_path}", {line_num});')
                )

        # 插入插桩代码
        insert_index = 0
        for line_num, code in instrumentation_lines:
            while insert_index < len(lines):
                # 计算当前行号
                current_line_num = insert_index + 1

                # 找到需要插入的位置
                if current_line_num < line_num:
                    result.append(lines[insert_index])
                    insert_index += 1
                elif current_line_num == line_num:
                    # 在这一行后添加插桩
                    result.append(lines[insert_index])

                    # 检查是否是语句结尾（以分号或花括号结尾）
                    stripped = lines[insert_index].rstrip()
                    if (
                        stripped.endswith(";")
                        or stripped.endswith("{")
                        or stripped.endswith("}")
                    ):
                        # 在行末添加注释
                        result[-1] = (
                            lines[insert_index].rstrip() + f" // COVERAGE: {code}"
                        )
                    else:
                        result.append(f"    {code}")

                    insert_index += 1
                    break
                else:
                    break

        # 添加剩余行
        while insert_index < len(lines):
            result.append(lines[insert_index])
            insert_index += 1

        return "\n".join(result)

    def get_executable_lines(self, file_path: str) -> Set[int]:
        """获取文件的可执行行"""
        return self.executable_lines.get(file_path, set())

    def get_instrumented_source(self, source: str, file_path: str = "unknown.c") -> str:
        """获取插桩后的源代码"""
        executable_lines = self._find_executable_lines(source)
        self.executable_lines[file_path] = executable_lines
        return self._add_instrumentation(source, file_path, executable_lines)


def instrument_file(source_path: str, output_path: Optional[str] = None) -> str:
    """插桩源文件"""
    instrumenter = Instrumenter()
    return instrumenter.instrument_file(source_path, output_path)


def instrument_source(source: str, file_path: str = "unknown.c") -> str:
    """插桩源代码"""
    instrumenter = Instrumenter()
    return instrumenter.instrument_source(source, file_path)

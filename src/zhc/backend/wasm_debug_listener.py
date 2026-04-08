#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZhC WASM 调试监听器 - WebAssembly 调试信息生成

将调试信息事件转换为 WASM DWARF 格式。

作者：远
日期：2026-04-08
"""

from typing import Dict, List, Optional, Any


class WASMDebugListener:
    """
    WASM 后端调试监听器

    实现 DebugListener 协议，将调试信息转换为 WASM DWARF 格式。

    WASM 调试信息使用 DWARF 格式，通过 custom sections 表示：
    - .debug_info - 编译单元信息
    - .debug_line - 行号表
    - .debug_str - 字符串表
    - .debug_abbrev - 缩写表
    """

    def __init__(self, source_file: str, module_name: str = "main"):
        """
        初始化 WASM 调试监听器

        Args:
            source_file: 源文件路径
            module_name: 模块名称
        """
        self.source_file = source_file
        self.module_name = module_name

        # 调试信息存储
        self._compile_unit: Optional[Dict] = None
        self._functions: List[Dict] = []
        self._variables: List[Dict] = []
        self._line_mappings: List[Dict] = []
        self._types: List[Dict] = []

        # WASM custom sections
        self._custom_sections: Dict[str, bytes] = {}

    # ========== DebugListener 协议实现 ==========

    def on_compile_unit(self, name: str, source_file: str, comp_dir: str) -> None:
        """
        编译单元开始事件

        Args:
            name: 编译单元名称
            source_file: 源文件路径
            comp_dir: 编译目录
        """
        self._compile_unit = {
            "name": name,
            "source_file": source_file,
            "comp_dir": comp_dir,
            "language": "DW_LANG_C99",  # WASM 使用 C99 调试信息
        }

    def on_function(
        self,
        name: str,
        start_line: int,
        end_line: int,
        start_addr: int,
        end_addr: int,
        return_type: str = "void",
        parameters: Optional[List[Dict]] = None,
    ) -> None:
        """
        函数定义事件

        Args:
            name: 函数名
            start_line: 起始行号
            end_line: 结束行号
            start_addr: 起始地址（WASM 函数索引）
            end_addr: 结束地址
            return_type: 返回类型
            parameters: 参数列表
        """
        func_info = {
            "name": name,
            "start_line": start_line,
            "end_line": end_line,
            "start_addr": start_addr,  # WASM 函数索引
            "end_addr": end_addr,
            "return_type": return_type,
            "parameters": parameters or [],
            "wasm_func_index": start_addr,  # WASM 函数索引
        }
        self._functions.append(func_info)

    def on_variable(
        self,
        name: str,
        type_name: str,
        line_number: int,
        address: int,
        is_parameter: bool = False,
    ) -> None:
        """
        变量定义事件

        Args:
            name: 变量名
            type_name: 类型名
            line_number: 定义行号
            address: 内存地址（WASM 局部变量索引）
            is_parameter: 是否为函数参数
        """
        var_info = {
            "name": name,
            "type": type_name,
            "line": line_number,
            "address": address,  # WASM 局部变量索引
            "is_parameter": is_parameter,
            "wasm_local_index": address,  # WASM 局部变量索引
        }
        self._variables.append(var_info)

    def on_line_mapping(
        self, line_number: int, address: int, column: int = 0, file_index: int = 0
    ) -> None:
        """
        行号映射事件

        Args:
            line_number: 源码行号
            address: WASM 指令偏移
            column: 列号
            file_index: 文件索引
        """
        mapping = {
            "line": line_number,
            "address": address,  # WASM 指令偏移
            "column": column,
            "file_index": file_index,
        }
        self._line_mappings.append(mapping)

    def on_type_definition(
        self,
        type_name: str,
        type_kind: str,
        byte_size: int,
        members: Optional[List[Dict]] = None,
        encoding: str = "",
    ) -> None:
        """
        类型定义事件

        Args:
            type_name: 类型名
            type_kind: 类型种类
            byte_size: 字节大小
            members: 成员列表
            encoding: 编码方式
        """
        type_info = {
            "name": type_name,
            "kind": type_kind,
            "size": byte_size,
            "members": members or [],
            "encoding": encoding,
        }
        self._types.append(type_info)

    def on_finalize(self) -> Dict[str, Any]:
        """
        完成事件

        Returns:
            WASM 调试信息字典
        """
        return {
            "compile_unit": self._compile_unit,
            "functions": self._functions,
            "variables": self._variables,
            "line_mappings": self._line_mappings,
            "types": self._types,
            "custom_sections": self._custom_sections,
        }

    def on_reset(self) -> None:
        """
        重置事件

        清空当前调试信息。
        """
        self._compile_unit = None
        self._functions.clear()
        self._variables.clear()
        self._line_mappings.clear()
        self._types.clear()
        self._custom_sections.clear()

    # ========== WASM 专用方法 ==========

    def generate_wasm_debug_sections(self) -> Dict[str, bytes]:
        """
        生成 WASM 调试 custom sections

        Returns:
            各调试段的字节序列字典
        """
        # 生成 .debug_info section
        self._custom_sections[".debug_info"] = self._generate_debug_info_section()

        # 生成 .debug_line section
        self._custom_sections[".debug_line"] = self._generate_debug_line_section()

        # 生成 .debug_str section
        self._custom_sections[".debug_str"] = self._generate_debug_str_section()

        return self._custom_sections

    def _generate_debug_info_section(self) -> bytes:
        """生成 .debug_info section"""
        # 简化实现：返回空字节
        # 实际实现需要完整的 DWARF 编码
        return b""

    def _generate_debug_line_section(self) -> bytes:
        """生成 .debug_line section"""
        # 简化实现：返回空字节
        return b""

    def _generate_debug_str_section(self) -> bytes:
        """生成 .debug_str section"""
        # 字符串表
        strings = []
        if self._compile_unit:
            strings.append(self._compile_unit["source_file"])
            strings.append(self._compile_unit["comp_dir"])

        for func in self._functions:
            strings.append(func["name"])

        for var in self._variables:
            strings.append(var["name"])

        # 拼接字符串（以 null 结尾）
        return "\x00".join(strings) + "\x00"

    def get_debug_info_summary(self) -> str:
        """获取调试信息摘要"""
        lines = [
            "WASM 调试信息摘要:",
            f"  编译单元: {self._compile_unit['name'] if self._compile_unit else 'None'}",
            f"  函数数: {len(self._functions)}",
            f"  变量数: {len(self._variables)}",
            f"  行号映射数: {len(self._line_mappings)}",
            f"  类型定义数: {len(self._types)}",
        ]
        return "\n".join(lines)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZhC LLVM 调试监听器 - LLVM IR 调试信息生成

将调试信息事件转换为 LLVM IR metadata 格式。

作者：远
日期：2026-04-08
"""

from typing import Dict, List, Optional, Any

try:
    import llvmlite.ir as ll

    LLVM_AVAILABLE = True
except ImportError:
    LLVM_AVAILABLE = False
    ll = None


class LLVMDebugListener:
    """
    LLVM 后端调试监听器

    实现 DebugListener 协议，将调试信息转换为 LLVM IR metadata。

    LLVM 调试信息使用 DWARF 格式，通过 metadata 节点表示：
    - DICompileUnit - 编译单元
    - DISubprogram - 函数
    - DILocalVariable - 局部变量
    - DILocation - 行号位置
    - DIType - 类型信息
    """

    def __init__(self, source_file: str, module_name: str = "main"):
        """
        初始化 LLVM 调试监听器

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

        # LLVM metadata 引用（如果 llvmlite 可用）
        self._metadata_nodes: Dict[str, Any] = {}

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
            "language": "DW_LANG_C",  # ZhC 使用 C 语言调试信息
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
            start_addr: 起始地址
            end_addr: 结束地址
            return_type: 返回类型
            parameters: 参数列表
        """
        func_info = {
            "name": name,
            "start_line": start_line,
            "end_line": end_line,
            "start_addr": start_addr,
            "end_addr": end_addr,
            "return_type": return_type,
            "parameters": parameters or [],
            "linkage_name": name,  # LLVM 函数名
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
            address: 内存地址
            is_parameter: 是否为函数参数
        """
        var_info = {
            "name": name,
            "type": type_name,
            "line": line_number,
            "address": address,
            "is_parameter": is_parameter,
        }
        self._variables.append(var_info)

    def on_line_mapping(
        self, line_number: int, address: int, column: int = 0, file_index: int = 0
    ) -> None:
        """
        行号映射事件

        Args:
            line_number: 源码行号
            address: 机器码地址
            column: 列号
            file_index: 文件索引
        """
        mapping = {
            "line": line_number,
            "address": address,
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
            LLVM 调试信息字典
        """
        return {
            "compile_unit": self._compile_unit,
            "functions": self._functions,
            "variables": self._variables,
            "line_mappings": self._line_mappings,
            "types": self._types,
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
        self._metadata_nodes.clear()

    # ========== LLVM 专用方法 ==========

    def generate_llvm_metadata(self, module: Any) -> Dict[str, Any]:
        """
        生成 LLVM IR metadata

        Args:
            module: LLVM Module 对象

        Returns:
            metadata 节点字典
        """
        if not LLVM_AVAILABLE or not module:
            return {}

        # 生成 DICompileUnit
        if self._compile_unit:
            self._metadata_nodes["DICompileUnit"] = self._create_compile_unit_metadata(
                module
            )

        # 生成 DISubprogram
        for func in self._functions:
            key = f"DISubprogram_{func['name']}"
            self._metadata_nodes[key] = self._create_function_metadata(module, func)

        # 生成 DILocalVariable
        for var in self._variables:
            key = f"DIVariable_{var['name']}"
            self._metadata_nodes[key] = self._create_variable_metadata(module, var)

        return self._metadata_nodes

    def _create_compile_unit_metadata(self, module: Any) -> Dict:
        """创建编译单元 metadata"""
        if not self._compile_unit:
            return {}

        return {
            "node_type": "DICompileUnit",
            "language": self._compile_unit["language"],
            "file": self._compile_unit["source_file"],
            "producer": "ZhC Compiler",
            "isOptimized": False,
            "emissionKind": "FullDebug",
        }

    def _create_function_metadata(self, module: Any, func: Dict) -> Dict:
        """创建函数 metadata"""
        return {
            "node_type": "DISubprogram",
            "name": func["name"],
            "linkageName": func["linkage_name"],
            "line": func["start_line"],
            "type": func["return_type"],
            "isLocal": False,
            "isDefinition": True,
            "scope": self._compile_unit["name"] if self._compile_unit else "",
        }

    def _create_variable_metadata(self, module: Any, var: Dict) -> Dict:
        """创建变量 metadata"""
        return {
            "node_type": "DILocalVariable"
            if not var["is_parameter"]
            else "DIParameter",
            "name": var["name"],
            "type": var["type"],
            "line": var["line"],
            "scope": "",  # 需要关联到函数
        }

    def get_debug_info_summary(self) -> str:
        """获取调试信息摘要"""
        lines = [
            "LLVM 调试信息摘要:",
            f"  编译单元: {self._compile_unit['name'] if self._compile_unit else 'None'}",
            f"  函数数: {len(self._functions)}",
            f"  变量数: {len(self._variables)}",
            f"  行号映射数: {len(self._line_mappings)}",
            f"  类型定义数: {len(self._types)}",
        ]
        return "\n".join(lines)

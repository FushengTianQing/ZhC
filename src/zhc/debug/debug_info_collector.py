# -*- coding: utf-8 -*-
"""
ZhC 调试信息收集器

收集和整理编译过程中的调试信息。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set

from .dwarf_builder import DwarfLanguage


@dataclass
class SourceLocation:
    """源码位置"""

    file: str  # 文件路径
    line: int  # 行号
    column: int = 0  # 列号

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"


@dataclass
class TypeDebugInfo:
    """类型调试信息"""

    name: str  # 类型名
    size: int  # 大小（字节）
    kind: str  # 类型种类（base, struct, array, pointer, function）
    fields: List["FieldDebugInfo"] = field(default_factory=list)  # 成员（如果是结构体）
    element_type: Optional["TypeDebugInfo"] = None  # 元素类型（如果是数组/指针）
    return_type: Optional["TypeDebugInfo"] = None  # 返回类型（如果是函数）
    param_types: List["TypeDebugInfo"] = field(
        default_factory=list
    )  # 参数类型（如果是函数）

    # 对齐信息
    alignment: int = 0  # 对齐要求


@dataclass
class FieldDebugInfo:
    """字段调试信息"""

    name: str  # 字段名
    offset: int  # 偏移
    size: int  # 大小
    type_info: TypeDebugInfo  # 类型信息
    is_bitfield: bool = False  # 是否为位域
    bit_offset: int = 0  # 位偏移
    bit_size: int = 0  # 位大小


@dataclass
class VariableDebugInfo:
    """变量调试信息"""

    name: str  # 变量名
    type_info: TypeDebugInfo  # 类型信息
    location: "VariableLocation"  # 位置信息
    scope: str  # 作用域
    is_local: bool = True  # 是否为局部变量
    is_parameter: bool = False  # 是否为参数
    is_global: bool = False  # 是否为全局变量
    declaration: Optional[SourceLocation] = None  # 声明位置


@dataclass
class VariableLocation:
    """变量位置"""

    kind: str  # 位置种类
    value: any = None  # 位置值

    # 可能的种类：
    # - "register": 寄存器编号
    # - "stack": 栈偏移
    # - "memory": 内存地址
    # - "constant": 常量值
    # - "implicit": 隐式位置（如返回值槽）

    def __str__(self) -> str:
        if self.kind == "register":
            return f"reg{self.value}"
        elif self.kind == "stack":
            return f"[sp+{self.value}]"
        elif self.kind == "memory":
            return f"0x{self.value:x}"
        elif self.kind == "constant":
            return str(self.value)
        return f"{self.kind}:{self.value}"


@dataclass
class FunctionDebugInfo:
    """函数调试信息"""

    name: str  # 函数名
    linkage_name: str  # 链接名
    return_type: TypeDebugInfo  # 返回类型
    parameters: List[VariableDebugInfo] = field(default_factory=list)  # 参数列表
    local_variables: List[VariableDebugInfo] = field(
        default_factory=list
    )  # 局部变量列表
    declaration: Optional[SourceLocation] = None  # 声明位置
    entry_pc: int = 0  # 入口地址
    end_pc: int = 0  # 结束地址

    @property
    def signature(self) -> str:
        """获取函数签名"""
        params = ", ".join(p.name for p in self.parameters)
        return f"{self.return_type.name} {self.name}({params})"


@dataclass
class CompileUnitInfo:
    """编译单元调试信息"""

    name: str  # 源文件名
    language: DwarfLanguage  # 源语言
    producer: str = "ZhC Compiler"  # 编译器
    compile_dir: str = ""  # 编译目录

    # 函数和变量
    functions: List[FunctionDebugInfo] = field(default_factory=list)
    global_variables: List[VariableDebugInfo] = field(default_factory=list)

    # 类型信息
    types: Dict[str, TypeDebugInfo] = field(default_factory=dict)

    # 行号信息
    line_table: List[SourceLocation] = field(default_factory=list)

    # 元数据
    flags: Set[str] = field(default_factory=set)  # 编译标志
    split_debug: bool = False  # 是否使用分裂调试信息


class DebugInfoCollector:
    """
    调试信息收集器

    在编译过程中收集调试信息。
    """

    def __init__(self):
        self.compile_units: List[CompileUnitInfo] = []
        self._current_unit: Optional[CompileUnitInfo] = None
        self._current_function: Optional[FunctionDebugInfo] = None
        self._type_cache: Dict[str, TypeDebugInfo] = {}

    def begin_compile_unit(
        self, name: str, language: DwarfLanguage = DwarfLanguage.ZHC
    ) -> CompileUnitInfo:
        """开始新的编译单元"""
        unit = CompileUnitInfo(name=name, language=language)
        self.compile_units.append(unit)
        self._current_unit = unit
        return unit

    def end_compile_unit(self) -> CompileUnitInfo:
        """结束当前编译单元"""
        unit = self._current_unit
        self._current_unit = None
        return unit

    def add_function(self, func: FunctionDebugInfo) -> None:
        """添加函数调试信息"""
        if self._current_unit:
            self._current_unit.functions.append(func)
        self._current_function = func

    def add_global_variable(self, var: VariableDebugInfo) -> None:
        """添加全局变量调试信息"""
        if self._current_unit:
            var.is_global = True
            self._current_unit.global_variables.append(var)

    def add_local_variable(self, var: VariableDebugInfo) -> None:
        """添加局部变量调试信息"""
        if self._current_function:
            var.is_local = True
            self._current_function.local_variables.append(var)

    def add_parameter(self, param: VariableDebugInfo) -> None:
        """添加参数调试信息"""
        if self._current_function:
            param.is_parameter = True
            self._current_function.parameters.append(param)

    def add_type(self, type_info: TypeDebugInfo) -> None:
        """添加类型调试信息"""
        if self._current_unit:
            self._current_unit.types[type_info.name] = type_info
        self._type_cache[type_info.name] = type_info

    def get_type(self, name: str) -> Optional[TypeDebugInfo]:
        """获取类型信息"""
        return self._type_cache.get(name)

    def add_line_entry(self, location: SourceLocation) -> None:
        """添加行号表条目"""
        if self._current_unit:
            self._current_unit.line_table.append(location)

    def get_functions_at_line(self, file: str, line: int) -> List[FunctionDebugInfo]:
        """获取指定行的函数"""
        if not self._current_unit:
            return []

        for func in self._current_unit.functions:
            if func.declaration and func.declaration.file == file:
                if func.declaration.line <= line <= func.declaration.line + 10:
                    return [func]

        return []

    def get_variables_at_location(
        self, file: str, line: int
    ) -> List[VariableDebugInfo]:
        """获取指定位置的变量"""
        variables = []

        if not self._current_unit:
            return variables

        # 查找当前作用域的变量
        for func in self._current_unit.functions:
            if func.declaration and func.declaration.file == file:
                # 检查是否在函数范围内
                if func.declaration.line <= line <= func.end_pc:
                    variables.extend(func.local_variables)
                    variables.extend(func.parameters)

        # 全局变量
        for var in self._current_unit.global_variables:
            if var.declaration and var.declaration.file == file:
                if var.declaration.line <= line:
                    variables.append(var)

        return variables

    def finalize(self) -> List[CompileUnitInfo]:
        """完成收集"""
        return self.compile_units

    # 便捷方法
    def create_type_info(
        self,
        name: str,
        size: int,
        kind: str = "base",
        alignment: int = 0,
    ) -> TypeDebugInfo:
        """创建类型信息"""
        return TypeDebugInfo(
            name=name,
            size=size,
            kind=kind,
            alignment=alignment or size,
        )

    def create_variable_info(
        self,
        name: str,
        type_info: TypeDebugInfo,
        location: VariableLocation,
        scope: str = "",
        is_local: bool = True,
    ) -> VariableDebugInfo:
        """创建变量信息"""
        return VariableDebugInfo(
            name=name,
            type_info=type_info,
            location=location,
            scope=scope,
            is_local=is_local,
        )

    def create_function_info(
        self,
        name: str,
        linkage_name: str,
        return_type: TypeDebugInfo,
    ) -> FunctionDebugInfo:
        """创建函数信息"""
        return FunctionDebugInfo(
            name=name,
            linkage_name=linkage_name,
            return_type=return_type,
        )

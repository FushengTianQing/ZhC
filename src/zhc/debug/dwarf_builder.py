# -*- coding: utf-8 -*-
"""
ZhC DWARF 调试信息构建器

生成 DWARF 格式的调试信息，支持 GDB 和 LLDB。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DwarfVersion(Enum):
    """DWARF 版本"""

    V2 = 2
    V3 = 3
    V4 = 4
    V5 = 5


class DwarfTag(Enum):
    """DWARF 标签"""

    COMPILE_UNIT = 0x11
    SUBPROGRAM = 0x2E
    BASE_TYPE = 0x24
    POINTER_TYPE = 0x0F
    ARRAY_TYPE = 0x01
    STRUCT_TYPE = 0x13
    MEMBER = 0x0D
    VARIABLE = 0x34
    FORMAL_PARAMETER = 0x05
    LEXICAL_BLOCK = 0x0B


class DwarfAttr(Enum):
    """DWARF 属性"""

    NAME = 0x03
    TYPE = 0x49
    LOW_PC = 0x11
    HIGH_PC = 0x12
    LANGUAGE = 0x13
    FILE = 0x03
    LINE = 0x05
    DECL_FILE = 0x3A
    DECL_LINE = 0x3B
    PRODUCER = 0x37
    LOCATION = 0x02


class DwarfLanguage(Enum):
    """DWARF 语言"""

    C = 0x0001
    C99 = 0x000C
    C11 = 0x000D
    CPP = 0x0004
    CPP11 = 0x0021
    ZHC = 0x8000  # 自定义语言 ID


@dataclass
class DebugSection:
    """
    DWARF 调试节

    包含 DWARF 数据的各个节。
    """

    name: str  # 节名称（如 .debug_info）
    data: bytes = field(default_factory=bytes)  # 节数据
    offset: int = 0  # 在文件中的偏移
    size: int = 0  # 节大小

    def add_data(self, data: bytes) -> None:
        """添加数据"""
        self.data += data
        self.size = len(self.data)


@dataclass
class DIEEntry:
    """
    Debug Information Entry (DIE)

    DWARF 调试信息条目。
    """

    tag: DwarfTag
    attributes: Dict[DwarfAttr, any] = field(default_factory=dict)
    children: List["DIEEntry"] = field(default_factory=list)

    def add_attr(self, attr: DwarfAttr, value: any) -> None:
        """添加属性"""
        self.attributes[attr] = value

    def add_child(self, child: "DIEEntry") -> None:
        """添加子节点"""
        self.children.append(child)


class DwarfBuilder:
    """
    DWARF 调试信息构建器

    构建 DWARF 格式的调试信息。
    """

    def __init__(self, version: DwarfVersion = DwarfVersion.V4):
        self.version = version
        self.sections: Dict[str, DebugSection] = {}
        self._init_sections()

    def _init_sections(self) -> None:
        """初始化 DWARF 节"""
        self.sections = {
            ".debug_abbrev": DebugSection(".debug_abbrev"),
            ".debug_info": DebugSection(".debug_info"),
            ".debug_line": DebugSection(".debug_line"),
            ".debug_str": DebugSection(".debug_str"),
            ".debug_ranges": DebugSection(".debug_ranges"),
        }

    def create_compile_unit(
        self,
        name: str,
        language: DwarfLanguage = DwarfLanguage.C,
        producer: str = "ZhC Compiler",
    ) -> DIEEntry:
        """
        创建编译单元 DIE

        Args:
            name: 源文件名
            language: 源语言
            producer: 编译器名称

        Returns:
            编译单元 DIE
        """
        cu = DIEEntry(tag=DwarfTag.COMPILE_UNIT)
        cu.add_attr(DwarfAttr.NAME, name)
        cu.add_attr(DwarfAttr.LANGUAGE, language.value)
        cu.add_attr(DwarfAttr.PRODUCER, producer)
        cu.add_attr(DwarfAttr.LOW_PC, 0)
        cu.add_attr(DwarfAttr.HIGH_PC, 0)

        return cu

    def create_subprogram(
        self,
        name: str,
        linkage_name: str,
        line: int,
        low_pc: int,
        high_pc: int,
        file: int = 1,
        return_type: Optional["DIEEntry"] = None,
    ) -> DIEEntry:
        """
        创建子程序（函数）DIE

        Args:
            name: 函数名
            linkage_name: 链接名
            line: 声明行号
            low_pc: 起始地址
            high_pc: 结束地址
            file: 文件索引
            return_type: 返回类型

        Returns:
            子程序 DIE
        """
        subprogram = DIEEntry(tag=DwarfTag.SUBPROGRAM)
        subprogram.add_attr(DwarfAttr.NAME, name)
        subprogram.add_attr(DwarfAttr.DECL_LINE, line)
        subprogram.add_attr(DwarfAttr.DECL_FILE, file)
        subprogram.add_attr(DwarfAttr.LOW_PC, low_pc)
        subprogram.add_attr(DwarfAttr.HIGH_PC, high_pc)

        if linkage_name:
            subprogram.add_attr(DwarfAttr.MIPS_LINKAGE_NAME, linkage_name)

        if return_type:
            subprogram.add_attr(DwarfAttr.TYPE, return_type)

        return subprogram

    def create_variable(
        self,
        name: str,
        line: int,
        location: str,
        die_type: Optional["DIEEntry"] = None,
        file: int = 1,
        is_local: bool = True,
    ) -> DIEEntry:
        """
        创建变量 DIE

        Args:
            name: 变量名
            line: 声明行号
            location: 位置描述（DWARF 位置表达式）
            die_type: 类型
            file: 文件索引
            is_local: 是否为局部变量

        Returns:
            变量 DIE
        """
        tag = DwarfTag.VARIABLE if not is_local else DwarfTag.VARIABLE
        variable = DIEEntry(tag=tag)
        variable.add_attr(DwarfAttr.NAME, name)
        variable.add_attr(DwarfAttr.DECL_LINE, line)
        variable.add_attr(DwarfAttr.DECL_FILE, file)
        variable.add_attr(DwarfAttr.LOCATION, location)

        if die_type:
            variable.add_attr(DwarfAttr.TYPE, die_type)

        return variable

    def create_base_type(
        self,
        name: str,
        size: int,
        encoding: int = 5,  # DW_ATE_signed
        byte_size: Optional[int] = None,
    ) -> DIEEntry:
        """
        创建基本类型 DIE

        Args:
            name: 类型名
            size: 位大小
            encoding: 编码类型
            byte_size: 字节大小

        Returns:
            基本类型 DIE
        """
        base_type = DIEEntry(tag=DwarfTag.BASE_TYPE)
        base_type.add_attr(DwarfAttr.NAME, name)
        base_type.add_attr(DwarfAttr.BYTE_SIZE, byte_size or (size // 8))
        base_type.add_attr(DwarfAttr.ENCODING, encoding)

        return base_type

    def create_pointer_type(
        self,
        base_type: "DIEEntry",
        byte_size: int = 8,
    ) -> DIEEntry:
        """
        创建指针类型 DIE

        Args:
            base_type: 指向的类型
            byte_size: 指针字节大小

        Returns:
            指针类型 DIE
        """
        ptr_type = DIEEntry(tag=DwarfTag.POINTER_TYPE)
        ptr_type.add_attr(DwarfAttr.TYPE, base_type)
        ptr_type.add_attr(DwarfAttr.BYTE_SIZE, byte_size)

        return ptr_type

    def create_struct_type(
        self,
        name: str,
        size: int,
        members: List[DIEEntry] = None,
        file: int = 1,
        line: int = 0,
    ) -> DIEEntry:
        """
        创建结构体类型 DIE

        Args:
            name: 结构体名
            size: 大小（字节）
            members: 成员列表
            file: 文件索引
            line: 声明行号

        Returns:
            结构体类型 DIE
        """
        struct = DIEEntry(tag=DwarfTag.STRUCT_TYPE)
        struct.add_attr(DwarfAttr.NAME, name)
        struct.add_attr(DwarfAttr.BYTE_SIZE, size)
        struct.add_attr(DwarfAttr.DECL_FILE, file)
        struct.add_attr(DwarfAttr.DECL_LINE, line)

        if members:
            for member in members:
                struct.add_child(member)

        return struct

    def create_member(
        self,
        name: str,
        offset: int,
        size: int,
        die_type: "DIEEntry",
        file: int = 1,
        line: int = 0,
    ) -> DIEEntry:
        """
        创建结构体成员 DIE

        Args:
            name: 成员名
            offset: 偏移
            size: 大小
            die_type: 类型
            file: 文件索引
            line: 声明行号

        Returns:
            成员 DIE
        """
        member = DIEEntry(tag=DwarfTag.MEMBER)
        member.add_attr(DwarfAttr.NAME, name)
        member.add_attr(DwarfAttr.DECL_FILE, file)
        member.add_attr(DwarfAttr.DECL_LINE, line)
        member.add_attr(DwarfAttr.TYPE, die_type)
        member.add_attr(DwarfAttr.DATA_MEMBER_LOCATION, offset)

        return member

    def build_debug_info(self, cu: DIEEntry) -> bytes:
        """
        构建 .debug_info 节数据

        Args:
            cu: 编译单元 DIE

        Returns:
            编码后的数据
        """
        # 简化的实现：实际应使用 DWARF 压缩格式
        data = bytearray()

        # 写编译单元头部
        data.extend(self._encode_uleb128(1))  # Abbreviation offset
        data.extend(self._encode_byte(4))  # Address size
        data.extend(self._encode_uleb128(1))  # Compilation unit length (placeholder)

        # 递归编码 DIE
        data.extend(self._encode_die(cu))

        return bytes(data)

    def _encode_die(self, die: DIEEntry) -> bytes:
        """编码单个 DIE"""
        data = bytearray()

        # 标签
        data.extend(self._encode_uleb128(die.tag.value))

        # 属性
        for attr, value in die.attributes.items():
            data.extend(self._encode_uleb128(attr.value))
            data.extend(self._encode_attribute_value(value))

        # 结束标记
        data.extend(self._encode_uleb128(0))

        # 子节点
        for child in die.children:
            data.extend(self._encode_die(child))

        # 子节点列表结束
        data.extend(self._encode_uleb128(0))

        return bytes(data)

    def _encode_attribute_value(self, value: any) -> bytes:
        """编码属性值"""
        # 简化的实现
        if isinstance(value, int):
            return self._encode_uleb128(value)
        elif isinstance(value, str):
            return value.encode("utf-8") + b"\x00"
        elif isinstance(value, bytes):
            return value
        return b""

    def _encode_uleb128(self, value: int) -> bytes:
        """编码 ULEB128"""
        result = bytearray()
        while True:
            byte = value & 0x7F
            value >>= 7
            if value != 0:
                byte |= 0x80
            result.append(byte)
            if value == 0:
                break
        return bytes(result)

    def _encode_byte(self, value: int) -> bytes:
        """编码单字节"""
        return bytes([value])


class DwarfGenerator:
    """
    DWARF 调试信息生成器

    高级接口，用于从 AST/IR 生成完整的 DWARF 信息。
    """

    def __init__(self, version: DwarfVersion = DwarfVersion.V4):
        self.builder = DwarfBuilder(version)
        self._type_cache: Dict[str, DIEEntry] = {}

    def generate(
        self,
        source_file: str,
        functions: List[Dict],
        global_variables: List[Dict] = None,
    ) -> Dict[str, bytes]:
        """
        生成调试信息

        Args:
            source_file: 源文件路径
            functions: 函数列表
            global_variables: 全局变量列表

        Returns:
            节名到数据的映射
        """
        # 创建编译单元
        cu = self.builder.create_compile_unit(
            name=source_file,
            language=DwarfLanguage.ZHC,
            producer="ZhC Compiler v0.1",
        )

        # 添加类型信息
        self._add_base_types(cu)

        # 添加函数信息
        for func in functions:
            self._add_function(cu, func)

        # 添加全局变量
        if global_variables:
            for var in global_variables:
                self._add_global_variable(cu, var)

        # 构建各节
        self.builder.sections[".debug_info"].data = self.builder.build_debug_info(cu)

        return {name: section.data for name, section in self.builder.sections.items()}

    def _add_base_types(self, cu: DIEEntry) -> None:
        """添加基本类型"""
        # void
        void_type = self.builder.create_base_type("void", 0, 0)
        self._type_cache["void"] = void_type
        cu.add_child(void_type)

        # int
        int_type = self.builder.create_base_type("int", 32, 5)  # signed
        self._type_cache["int"] = int_type
        cu.add_child(int_type)

        # float
        float_type = self.builder.create_base_type("float", 32, 4)  # float
        self._type_cache["float"] = float_type
        cu.add_child(float_type)

        # double
        double_type = self.builder.create_base_type("double", 64, 4)
        self._type_cache["double"] = double_type
        cu.add_child(double_type)

        # char
        char_type = self.builder.create_base_type("char", 8, 6)  # unsigned char
        self._type_cache["char"] = char_type
        cu.add_child(char_type)

    def _add_function(self, cu: DIEEntry, func: Dict) -> None:
        """添加函数信息"""
        subprogram = self.builder.create_subprogram(
            name=func.get("name", ""),
            linkage_name=func.get("linkage_name", ""),
            line=func.get("line", 1),
            low_pc=func.get("low_pc", 0),
            high_pc=func.get("high_pc", 0),
        )

        # 添加参数
        for i, param in enumerate(func.get("params", [])):
            param_die = self.builder.create_variable(
                name=param.get("name", f"arg{i}"),
                line=param.get("line", 1),
                location=f"%{i + 1}",
                is_local=False,
            )
            subprogram.add_child(param_die)

        # 添加局部变量
        for var in func.get("locals", []):
            var_die = self.builder.create_variable(
                name=var.get("name", ""),
                line=var.get("line", 1),
                location=var.get("location", ""),
                is_local=True,
            )
            subprogram.add_child(var_die)

        cu.add_child(subprogram)

    def _add_global_variable(self, cu: DIEEntry, var: Dict) -> None:
        """添加全局变量信息"""
        var_die = self.builder.create_variable(
            name=var.get("name", ""),
            line=var.get("line", 1),
            location=var.get("name", ""),
            is_local=False,
        )
        cu.add_child(var_die)

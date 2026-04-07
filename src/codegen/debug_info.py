"""
调试信息生成器

生成 DWARF 格式的调试信息，支持 GDB/LLDB 等调试器。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import IntEnum


# ==================== DWARF 标签 ====================

class DW_TAG(IntEnum):
    """DWARF 标签"""
    NULL = 0x00
    COMPILE_UNIT = 0x11
    BASE_TYPE = 0x0e
    STRUCT_TYPE = 0x13
    UNION_TYPE = 0x17
    ENUMERATION_TYPE = 0x04
    ARRAY_TYPE = 0x01
    SUBPROGRAM = 0x2e
    LEXICAL_BLOCK = 0x0b
    VARIABLE = 0x34
    FORMAL_PARAMETER = 0x05
    MEMBER = 0x0d
    POINTER_TYPE = 0x0f
    REFERENCE_TYPE = 0x10
    CONST_TYPE = 0x26
    VOLATILE_TYPE = 0x37


class DW_AT(IntEnum):
    """DWARF 属性"""
    NAME = 0x03
    BYTE_SIZE = 0x0b
    TYPE = 0x49
    LOW_PC = 0x11
    HIGH_PC = 0x12
    LANGUAGE = 0x13
    STARTS_SCOPE = 0x40
    END_SCOPE = 0x41
    LOCATION = 0x02
    EXTERNAL = 0x3f
    DECL_LINE = 0x4a
    DECL_COLUMN = 0x39
    DECL_FILE = 0x3a
    PRODUCER = 0x25
    COMP_DIR = 0x1b
    STATEMENT_LIST = 0x10
    MACINFO_FILE = 0x22
    ENCODING = 0x3e  # DW_AT_encoding
    CONST_VALUE = 0x1c  # DW_AT_const_value
    UPPER_BOUND = 0x2f  # DW_AT_upper_bound
    COUNT = 0x37  # DW_AT_count
    DATA_LOCATION = 0x50  # DW_AT_data_location


class DW_FORM(IntEnum):
    """DWARF 表单"""
    ADDR = 0x01
    STRING = 0x05
    DATA1 = 0x0b
    DATA2 = 0x0d
    DATA4 = 0x06
    DATA8 = 0x07
    EXPRLOC = 0x18
    SEC_OFFSET = 0x17


class DW_LANG(IntEnum):
    """DWARF 语言"""
    C = 0x0002
    C89 = 0x0001
    C99 = 0x000c
    C11 = 0x000d
    CPP = 0x0004
    CPP11 = 0x0021
    CPP14 = 0x0022


class DW_OP(IntEnum):
    """DWARF 操作码"""
    ADDR = 0x03
    DUP = 0x12
    DROP = 0x13
    PUSH = 0x50
    STACK_VALUE = 0x9f
    REG0 = 0x50


# ==================== 数据结构 ====================

@dataclass
class DebugLocation:
    """调试位置"""
    file: str
    line: int
    column: int = 0


@dataclass
class DebugVariable:
    """调试变量信息"""
    name: str
    type_name: str
    location: str  # 寄存器或栈位置，如 "DWORD PTR [rbp-8]"
    scope_start: int = 0
    scope_end: int = 0


@dataclass
class DebugLineEntry:
    """行号表条目"""
    address: int
    file_index: int
    line: int
    column: int
    is_stmt: bool = True
    basic_block: bool = False
    prologue_end: bool = False
    epilogue_begin: bool = False


@dataclass
class DebugInfoEntry:
    """调试信息条目 (DIE)"""
    tag: int
    attributes: Dict[int, Any] = field(default_factory=dict)
    children: List["DebugInfoEntry"] = field(default_factory=list)


@dataclass
class LineProgram:
    """行号程序"""
    directory: str
    file_name: str
    entries: List[DebugLineEntry] = field(default_factory=list)


# ==================== 调试信息生成器 ====================

class DebugInfoGenerator:
    """DWARF 调试信息生成器"""

    def __init__(self, source_file: str, output_file: str):
        self.source_file = source_file
        self.output_file = output_file
        self.line_program: Optional[LineProgram] = None
        self.root_die: Optional[DebugInfoEntry] = None
        self._current_address = 0x1000
        self._file_index = 1
        self._type_index = 1
        self._string_table: Dict[str, int] = {}
        self._abbrev_table: List[tuple] = []

    def generate(
        self,
        functions: List[Dict],
        types: List[Dict],
        variables: List[DebugVariable],
        line_mapping: Dict[int, tuple] = None
    ) -> Dict[str, Any]:
        """生成调试信息

        Args:
            functions: 函数列表，每个函数包含 name, address, size, return_type, params
            types: 类型列表，每个类型包含 name, size, kind
            variables: 变量列表
            line_mapping: 行号映射 (address -> (file, line, column))

        Returns:
            调试信息字典
        """
        # 生成行号程序
        self.line_program = self._generate_line_program(line_mapping or {})

        # 生成根 DIE（编译单元）
        self.root_die = self._generate_compile_unit_die()

        # 添加类型 DIEs
        for type_info in types:
            type_die = self._generate_type_die(type_info)
            self.root_die.children.append(type_die)

        # 添加函数 DIEs
        for func_info in functions:
            func_die = self._generate_function_die(func_info)
            self.root_die.children.append(func_die)

        # 返回调试信息
        return {
            "source_file": self.source_file,
            "output_file": self.output_file,
            "language": DW_LANG.C,
            "line_program": self._format_line_program(),
            "debug_info": self._format_debug_info(),
        }

    def _generate_line_program(self, line_mapping: Dict[int, tuple]) -> LineProgram:
        """生成行号程序"""
        import os
        directory = os.path.dirname(self.source_file)
        file_name = os.path.basename(self.source_file)

        program = LineProgram(directory=directory, file_name=file_name)

        # 按地址排序
        for address in sorted(line_mapping.keys()):
            file_path, line, column = line_mapping[address]
            entry = DebugLineEntry(
                address=address,
                file_index=self._file_index,
                line=line,
                column=column,
                is_stmt=True
            )
            program.entries.append(entry)

        return program

    def _generate_compile_unit_die(self) -> DebugInfoEntry:
        """生成编译单元 DIE"""
        import os

        die = DebugInfoEntry(tag=DW_TAG.COMPILE_UNIT)
        die.attributes[DW_AT.NAME] = self.source_file
        die.attributes[DW_AT.LANGUAGE] = DW_LANG.C
        die.attributes[DW_AT.PRODUCER] = "ZHC Compiler"
        die.attributes[DW_AT.COMP_DIR] = os.path.dirname(self.source_file) or "."
        die.attributes[DW_AT.STATEMENT_LIST] = 0  # 行号表偏移

        return die

    def _generate_type_die(self, type_info: Dict) -> DebugInfoEntry:
        """生成类型 DIE"""
        type_name = type_info.get("name", f"type_{self._type_index}")
        type_kind = type_info.get("kind", "base")
        type_size = type_info.get("size", 8)

        self._type_index += 1

        if type_kind == "base":
            die = DebugInfoEntry(tag=DW_TAG.BASE_TYPE)
            die.attributes[DW_AT.NAME] = type_name
            die.attributes[DW_AT.BYTE_SIZE] = type_size

            # 编码类型
            if type_name in ("整数型", "int"):
                die.attributes[DW_AT.ENCODING] = 0x05  # DW_ATE_signed
            elif type_name in ("浮点型", "float", "double"):
                die.attributes[DW_AT.ENCODING] = 0x04  # DW_ATE_float
            elif type_name in ("字符型", "char"):
                die.attributes[DW_AT.ENCODING] = 0x08  # DW_ATE_signed_char

        elif type_kind == "struct":
            die = DebugInfoEntry(tag=DW_TAG.STRUCT_TYPE)
            die.attributes[DW_AT.NAME] = type_name
            die.attributes[DW_AT.BYTE_SIZE] = type_size

            # 添加成员
            for member in type_info.get("members", []):
                member_die = DebugInfoEntry(tag=DW_TAG.MEMBER)
                member_die.attributes[DW_AT.NAME] = member.get("name", "")
                member_die.attributes[DW_AT.TYPE] = member.get("type", "")
                member_die.attributes[DW_AT.LOCATION] = member.get("offset", 0)
                die.children.append(member_die)

        elif type_kind == "enum":
            die = DebugInfoEntry(tag=DW_TAG.ENUMERATION_TYPE)
            die.attributes[DW_AT.NAME] = type_name
            die.attributes[DW_AT.BYTE_SIZE] = type_size

            # 添加枚举值
            for value in type_info.get("values", []):
                value_die = DebugInfoEntry(tag=0x28)  # DW_TAG enumerator
                value_die.attributes[DW_AT.NAME] = value.get("name", "")
                value_die.attributes[DW_AT.CONST_VALUE] = value.get("value", 0)
                die.children.append(value_die)

        elif type_kind == "pointer":
            die = DebugInfoEntry(tag=DW_TAG.POINTER_TYPE)
            die.attributes[DW_AT.BYTE_SIZE] = 8  # 64-bit pointer
            if "element_type" in type_info:
                die.attributes[DW_AT.TYPE] = type_info["element_type"]

        elif type_kind == "array":
            die = DebugInfoEntry(tag=DW_TAG.ARRAY_TYPE)
            die.attributes[DW_AT.BYTE_SIZE] = type_size
            if "element_type" in type_info:
                die.attributes[DW_AT.TYPE] = type_info["element_type"]

            # 添加维度
            for dim in type_info.get("dimensions", []):
                subrange_die = DebugInfoEntry(tag=0x21)  # DW_TAG_subrange_type
                subrange_die.attributes[DW_AT.UPPER_BOUND] = dim - 1  # 0-indexed upper bound
                die.children.append(subrange_die)

        else:
            die = DebugInfoEntry(tag=DW_TAG.BASE_TYPE)
            die.attributes[DW_AT.NAME] = type_name
            die.attributes[DW_AT.BYTE_SIZE] = type_size

        return die

    def _generate_function_die(self, func_info: Dict) -> DebugInfoEntry:
        """生成函数 DIE"""
        die = DebugInfoEntry(tag=DW_TAG.SUBPROGRAM)
        die.attributes[DW_AT.NAME] = func_info.get("name", "")
        die.attributes[DW_AT.DECL_LINE] = func_info.get("line", 0)
        die.attributes[DW_AT.DECL_FILE] = self._file_index

        # 函数地址范围
        address = func_info.get("address", 0)
        size = func_info.get("size", 0)
        die.attributes[DW_AT.LOW_PC] = address
        die.attributes[DW_AT.HIGH_PC] = address + size

        # 返回类型
        if "return_type" in func_info:
            die.attributes[DW_AT.TYPE] = func_info["return_type"]

        # 参数
        for param in func_info.get("params", []):
            param_die = DebugInfoEntry(tag=DW_TAG.FORMAL_PARAMETER)
            param_die.attributes[DW_AT.NAME] = param.get("name", "")
            param_die.attributes[DW_AT.TYPE] = param.get("type", "")
            param_die.attributes[DW_AT.LOCATION] = param.get("location", "")
            die.children.append(param_die)

        # 局部变量
        for var in func_info.get("variables", []):
            var_die = DebugInfoEntry(tag=DW_TAG.VARIABLE)
            var_die.attributes[DW_AT.NAME] = var.get("name", "")
            var_die.attributes[DW_AT.TYPE] = var.get("type", "")
            var_die.attributes[DW_AT.LOCATION] = var.get("location", "")
            die.children.append(var_die)

        return die

    def _format_line_program(self) -> str:
        """格式化行号程序"""
        if not self.line_program:
            return ""

        lines = []
        lines.append(f".file 1 \"{self.line_program.file_name}\"")
        lines.append(f".loc 1 0 0")
        lines.append("")
        lines.append("# 行号表")
        lines.append(f"# 目录: {self.line_program.directory}")
        lines.append(f"# 文件: {self.line_program.file_name}")

        return "\n".join(lines)

    def _format_debug_info(self) -> str:
        """格式化调试信息"""
        if not self.root_die:
            return ""

        lines = []
        lines.append("# 调试信息条目")
        lines.append(self._format_die(self.root_die, 0))

        return "\n".join(lines)

    def _format_die(self, die: DebugInfoEntry, indent: int) -> str:
        """格式化单个 DIE"""
        prefix = "  " * indent
        lines = [f"{prefix}DIE(0x{die.tag:02x}):"]

        # 格式化属性
        for attr, value in die.attributes.items():
            attr_name = self._get_attr_name(attr)
            lines.append(f"{prefix}  {attr_name} = {value}")

        # 格式化子节点
        for child in die.children:
            lines.append(self._format_die(child, indent + 1))

        return "\n".join(lines)

    def _get_attr_name(self, attr: int) -> str:
        """获取属性名称"""
        attr_names = {
            DW_AT.NAME: "DW_AT_name",
            DW_AT.BYTE_SIZE: "DW_AT_byte_size",
            DW_AT.TYPE: "DW_AT_type",
            DW_AT.LOW_PC: "DW_AT_low_pc",
            DW_AT.HIGH_PC: "DW_AT_high_pc",
            DW_AT.LANGUAGE: "DW_AT_language",
            DW_AT.LOCATION: "DW_AT_location",
            DW_AT.DECL_LINE: "DW_AT_decl_line",
            DW_AT.DECL_FILE: "DW_AT_decl_file",
            DW_AT.PRODUCER: "DW_AT_producer",
            DW_AT.COMP_DIR: "DW_AT_comp_dir",
            DW_AT.STATEMENT_LIST: "DW_AT_stmt_list",
        }
        return attr_names.get(attr, f"DW_AT(0x{attr:02x})")


class DWARFEncoder:
    """DWARF 编码器 - 将 DIE 编码为二进制格式"""

    def encode_compile_unit(self, die: DebugInfoEntry, strings: List[bytes]) -> bytes:
        """编码编译单元

        Args:
            die: 根 DIE
            strings: 字符串表

        Returns:
            编码后的字节串
        """
        # 简化实现：生成一个基础的 .debug_info 段
        result = bytearray()

        # 单元长度（4 字节）
        unit_length = 0  # 暂时设为 0，稍后更新

        # 单元头部
        result.extend(unit_length.to_bytes(4, "little"))  # 长度
        result.extend((5).to_bytes(2, "little"))  # 版本 DWARF 5
        result.extend((1).to_bytes(4, "little"))  # 调试信息偏移
        result.extend((8).to_bytes(1, "little"))  # 地址大小

        # 添加 abbreviation table offset（简化实现）
        result.extend((1).to_bytes(4, "little"))

        # 编码 DIE
        result.extend(self._encode_die(die))

        # 更新单元长度
        unit_length = len(result) - 4
        result[:4] = unit_length.to_bytes(4, "little")

        return bytes(result)

    def _encode_die(self, die: DebugInfoEntry) -> bytes:
        """编码 DIE"""
        result = bytearray()

        # 标签
        result.append(die.tag)

        # 属性（简化实现）
        for attr, value in die.attributes.items():
            result.append(attr)
            result.extend(self._encode_form_value(value))

        # 结束标记
        result.append(0)

        # 子节点
        for child in die.children:
            result.extend(self._encode_die(child))

        # 兄弟节点结束标记
        result.append(0)

        return bytes(result)

    def _encode_form_value(self, value: Any) -> bytes:
        """编码表单值"""
        if isinstance(value, str):
            return value.encode("utf-8") + b"\x00"
        elif isinstance(value, int):
            return value.to_bytes(8, "little")
        else:
            return b""


def generate_debug_info(
    source_file: str,
    output_file: str,
    functions: List[Dict],
    types: List[Dict],
    variables: List[DebugVariable],
    line_mapping: Dict[int, tuple] = None
) -> Dict[str, Any]:
    """便捷函数：生成调试信息

    Args:
        source_file: 源文件路径
        output_file: 输出文件路径
        functions: 函数列表
        types: 类型列表
        variables: 变量列表
        line_mapping: 行号映射

    Returns:
        调试信息字典
    """
    generator = DebugInfoGenerator(source_file, output_file)
    return generator.generate(functions, types, variables, line_mapping)

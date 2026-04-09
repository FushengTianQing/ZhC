# -*- coding: utf-8 -*-
"""
ZhC DWARF .debug_abbrev 节生成器

生成 DWARF 缩写表，定义调试信息条目的结构。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AbbrevKind(Enum):
    """缩写种类"""

    COMPILE_UNIT = "compile_unit"
    SUBPROGRAM = "subprogram"
    FORMAL_PARAMETER = "formal_parameter"
    VARIABLE = "variable"
    LEXICAL_BLOCK = "lexical_block"
    BASE_TYPE = "base_type"
    POINTER_TYPE = "pointer_type"
    STRUCTURE_TYPE = "structure_type"
    UNION_TYPE = "union_type"
    ENUMERATION_TYPE = "enumeration_type"
    MEMBER = "member"
    ARRAY_TYPE = "array_type"
    SUBROUTINE_TYPE = "subroutine_type"
    TYPEDEF = "typedef"
    NAMESPACE = "namespace"
    INLINED_SUBROUTINE = "inlined_subroutine"


@dataclass
class AbbrevAttr:
    """缩写属性"""

    name: int  # DW_AT_xxx
    form: int  # DW_FORM_xxx


@dataclass
class AbbrevEntry:
    """缩写条目"""

    code: int  # 缩写代码
    tag: int  # DW_TAG_xxx
    has_children: bool  # 是否有子节点
    attributes: List[AbbrevAttr] = field(default_factory=list)


class AbbreviationBuilder:
    """
    缩写构建器

    构建 DWARF 缩写表条目。
    """

    # DWARF 标准标签
    TAG_COMPILE_UNIT = 0x11
    TAG_SUBPROGRAM = 0x2E
    TAG_FORMAL_PARAMETER = 0x05
    TAG_VARIABLE = 0x34
    TAG_LEXICAL_BLOCK = 0x0B
    TAG_BASE_TYPE = 0x24
    TAG_POINTER_TYPE = 0x0F
    TAG_STRUCTURE_TYPE = 0x13
    TAG_UNION_TYPE = 0x17
    TAG_ENUMERATION_TYPE = 0x04
    TAG_MEMBER = 0x0D
    TAG_ARRAY_TYPE = 0x01
    TAG_SUBROUTINE_TYPE = 0x2B
    TAG_TYPEDEF = 0x16
    TAG_NAMESPACE = 0x39
    TAG_INLINED_SUBROUTINE = 0x1D

    # DWARF 标准属性
    AT_sibling = 0x01
    AT_location = 0x02
    AT_name = 0x03
    AT_ordering = 0x09
    AT_byte_size = 0x0B
    AT_bit_offset = 0x0C
    AT_bit_size = 0x0D
    AT_stmt_list = 0x10
    AT_low_pc = 0x11
    AT_high_pc = 0x12
    AT_language = 0x13
    AT_discr = 0x15
    AT_discr_value = 0x16
    AT_visibility = 0x17
    AT_import = 0x18
    AT_string_length = 0x19
    AT_common_reference = 0x1A
    AT_comp_dir = 0x1B
    AT_const_value = 0x1C
    AT_containing_type = 0x1D
    AT_default_value = 0x1E
    AT_decl_column = 0x39
    AT_decl_file = 0x3A
    AT_decl_line = 0x3B
    AT_encoding = 0x3E
    AT_external = 0x03
    AT_frame_base = 0x40
    AT_type = 0x49
    AT_producer = 0x25
    AT_prototyped = 0x27
    AT_return_addr = 0x2A
    AT_start_scope = 0x4C
    AT_bit_stride = 0x2E
    AT_upper_bound = 0x2F
    AT_abstract_origin = 0x31
    AT_accessibility = 0x32
    AT_addr_class = 0x33
    AT_artificial = 0x34
    AT_data_member_location = 0x38
    AT_declaration = 0x3C
    AT_discr_list = 0x3D
    AT_entry_pc = 0x52
    AT_extension = 0x63
    AT_is_optional = 0x64
    AT_lower_bound = 0x4F
    AT_priority = 0x65
    AT_segment = 0x66
    AT_specification = 0x67
    AT_static_link = 0x68
    AT_use_location = 0x6A
    AT_virtual = 0x6B
    AT_virtual_table = 0x6C

    # DWARF 标准表单
    FORM_ADDR = 0x01
    FORM_BLOCK2 = 0x03
    FORM_BLOCK4 = 0x04
    FORM_DATA2 = 0x05
    FORM_DATA4 = 0x06
    FORM_DATA8 = 0x07
    FORM_STRING = 0x08
    FORM_BLOCK = 0x09
    FORM_BLOCK1 = 0x0A
    FORM_DATA1 = 0x0B
    FORM_FLAG = 0x0C
    FORM_SDATA = 0x0D
    FORM_STRP = 0x0E
    FORM_UDATA = 0x0F
    FORM_REF_ADDR = 0x10
    FORM_REF1 = 0x11
    FORM_REF2 = 0x12
    FORM_REF4 = 0x13
    FORM_REF8 = 0x14
    FORM_REF_UDATA = 0x15
    FORM_INDIRECT = 0x16
    FORM_SEC_OFFSET = 0x17
    FORM_EXPRLOC = 0x18
    FORM_FLAG_PRESENT = 0x19
    FORM_REF_SIG8 = 0x20

    def __init__(self):
        self.entries: List[AbbrevEntry] = []
        self._code_counter = 1
        self._type_abbrevs: Dict[str, int] = {}  # 类型名 -> 缩写代码

    def add_compile_unit_abbrev(self) -> int:
        """添加编译单元缩写"""
        entry = AbbrevEntry(
            code=self._code_counter,
            tag=self.TAG_COMPILE_UNIT,
            has_children=True,
            attributes=[
                AbbrevAttr(self.AT_name, self.FORM_STRING),
                AbbrevAttr(self.AT_producer, self.FORM_STRING),
                AbbrevAttr(self.AT_comp_dir, self.FORM_STRING),
                AbbrevAttr(self.AT_language, self.FORM_DATA4),
                AbbrevAttr(self.AT_low_pc, self.FORM_ADDR),
                AbbrevAttr(self.AT_high_pc, self.FORM_ADDR),
                AbbrevAttr(self.AT_stmt_list, self.FORM_SEC_OFFSET),
            ],
        )
        self.entries.append(entry)
        self._code_counter += 1
        return entry.code

    def add_subprogram_abbrev(self) -> int:
        """添加子程序缩写"""
        entry = AbbrevEntry(
            code=self._code_counter,
            tag=self.TAG_SUBPROGRAM,
            has_children=True,
            attributes=[
                AbbrevAttr(self.AT_name, self.FORM_STRING),
                AbbrevAttr(self.AT_decl_file, self.FORM_DATA4),
                AbbrevAttr(self.AT_decl_line, self.FORM_DATA4),
                AbbrevAttr(self.AT_low_pc, self.FORM_ADDR),
                AbbrevAttr(self.AT_high_pc, self.FORM_ADDR),
                AbbrevAttr(self.AT_frame_base, self.FORM_DATA1),
                AbbrevAttr(self.AT_type, self.FORM_REF4),
                AbbrevAttr(self.AT_external, self.FORM_FLAG_PRESENT),
            ],
        )
        self.entries.append(entry)
        self._code_counter += 1
        return entry.code

    def add_formal_parameter_abbrev(self) -> int:
        """添加形式参数缩写"""
        entry = AbbrevEntry(
            code=self._code_counter,
            tag=self.TAG_FORMAL_PARAMETER,
            has_children=False,
            attributes=[
                AbbrevAttr(self.AT_name, self.FORM_STRING),
                AbbrevAttr(self.AT_decl_file, self.FORM_DATA4),
                AbbrevAttr(self.AT_decl_line, self.FORM_DATA4),
                AbbrevAttr(self.AT_location, self.FORM_EXPRLOC),
                AbbrevAttr(self.AT_type, self.FORM_REF4),
            ],
        )
        self.entries.append(entry)
        self._code_counter += 1
        return entry.code

    def add_variable_abbrev(self) -> int:
        """添加变量缩写"""
        entry = AbbrevEntry(
            code=self._code_counter,
            tag=self.TAG_VARIABLE,
            has_children=False,
            attributes=[
                AbbrevAttr(self.AT_name, self.FORM_STRING),
                AbbrevAttr(self.AT_decl_file, self.FORM_DATA4),
                AbbrevAttr(self.AT_decl_line, self.FORM_DATA4),
                AbbrevAttr(self.AT_location, self.FORM_EXPRLOC),
                AbbrevAttr(self.AT_type, self.FORM_REF4),
            ],
        )
        self.entries.append(entry)
        self._code_counter += 1
        return entry.code

    def add_lexical_block_abbrev(self) -> int:
        """添加词法块缩写"""
        entry = AbbrevEntry(
            code=self._code_counter,
            tag=self.TAG_LEXICAL_BLOCK,
            has_children=True,
            attributes=[
                AbbrevAttr(self.AT_low_pc, self.FORM_ADDR),
                AbbrevAttr(self.AT_high_pc, self.FORM_ADDR),
            ],
        )
        self.entries.append(entry)
        self._code_counter += 1
        return entry.code

    def add_base_type_abbrev(self, type_name: str) -> int:
        """添加基本类型缩写"""
        if type_name in self._type_abbrevs:
            return self._type_abbrevs[type_name]

        entry = AbbrevEntry(
            code=self._code_counter,
            tag=self.TAG_BASE_TYPE,
            has_children=False,
            attributes=[
                AbbrevAttr(self.AT_name, self.FORM_STRING),
                AbbrevAttr(self.AT_byte_size, self.FORM_DATA1),
                AbbrevAttr(self.AT_encoding, self.FORM_DATA1),
            ],
        )
        self.entries.append(entry)
        self._type_abbrevs[type_name] = entry.code
        self._code_counter += 1
        return entry.code

    def add_pointer_type_abbrev(self) -> int:
        """添加指针类型缩写"""
        entry = AbbrevEntry(
            code=self._code_counter,
            tag=self.TAG_POINTER_TYPE,
            has_children=False,
            attributes=[
                AbbrevAttr(self.AT_byte_size, self.FORM_DATA1),
                AbbrevAttr(self.AT_type, self.FORM_REF4),
            ],
        )
        self.entries.append(entry)
        self._code_counter += 1
        return entry.code

    def add_structure_type_abbrev(self, type_name: str) -> int:
        """添加结构体类型缩写"""
        if type_name in self._type_abbrevs:
            return self._type_abbrevs[type_name]

        entry = AbbrevEntry(
            code=self._code_counter,
            tag=self.TAG_STRUCTURE_TYPE,
            has_children=True,
            attributes=[
                AbbrevAttr(self.AT_name, self.FORM_STRING),
                AbbrevAttr(self.AT_byte_size, self.FORM_DATA4),
                AbbrevAttr(self.AT_decl_file, self.FORM_DATA4),
                AbbrevAttr(self.AT_decl_line, self.FORM_DATA4),
            ],
        )
        self.entries.append(entry)
        self._type_abbrevs[type_name] = entry.code
        self._code_counter += 1
        return entry.code

    def add_member_abbrev(self) -> int:
        """添加成员缩写"""
        entry = AbbrevEntry(
            code=self._code_counter,
            tag=self.TAG_MEMBER,
            has_children=False,
            attributes=[
                AbbrevAttr(self.AT_name, self.FORM_STRING),
                AbbrevAttr(self.AT_decl_file, self.FORM_DATA4),
                AbbrevAttr(self.AT_decl_line, self.FORM_DATA4),
                AbbrevAttr(self.AT_type, self.FORM_REF4),
                AbbrevAttr(self.AT_data_member_location, self.FORM_DATA4),
            ],
        )
        self.entries.append(entry)
        self._code_counter += 1
        return entry.code

    def get_abbrev_code(self, type_name: str) -> Optional[int]:
        """获取类型缩写代码"""
        return self._type_abbrevs.get(type_name)


class DebugAbbrevSection:
    """
    .debug_abbrev 节生成器

    生成 DWARF 缩写表节。
    """

    def __init__(self):
        self.builder = AbbreviationBuilder()

    def add_standard_abbreviations(self) -> None:
        """添加标准缩写"""
        self.builder.add_compile_unit_abbrev()
        self.builder.add_subprogram_abbrev()
        self.builder.add_formal_parameter_abbrev()
        self.builder.add_variable_abbrev()
        self.builder.add_lexical_block_abbrev()
        self.builder.add_base_type_abbrev("int")
        self.builder.add_base_type_abbrev("float")
        self.builder.add_base_type_abbrev("double")
        self.builder.add_base_type_abbrev("char")
        self.builder.add_base_type_abbrev("void")
        self.builder.add_pointer_type_abbrev()
        self.builder.add_structure_type_abbrev("struct")
        self.builder.add_member_abbrev()

    def build(self) -> bytes:
        """
        构建 .debug_abbrev 节数据

        Returns:
            节数据字节
        """
        data = bytearray()

        for entry in self.builder.entries:
            # 缩写代码
            data.extend(self._encode_uleb128(entry.code))

            # 标签
            data.extend(self._encode_uleb128(entry.tag))

            # 是否有子节点
            data.append(1 if entry.has_children else 0)

            # 属性
            for attr in entry.attributes:
                data.extend(self._encode_uleb128(attr.name))
                data.extend(self._encode_uleb128(attr.form))

            # 属性结束
            data.append(0)
            data.append(0)

        # 缩写表结束
        data.append(0)

        return bytes(data)

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

    def get_size(self) -> int:
        """获取节大小"""
        return len(self.build())

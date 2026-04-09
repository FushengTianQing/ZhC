# -*- coding: utf-8 -*-
"""
ZhC DWARF .debug_info 节生成器

生成 DWARF 调试信息节，包含编译单元和调试信息条目。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import struct
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

    # 类型
    ARRAY_TYPE = 0x01
    CLASS_TYPE = 0x02
    ENUMERATION_TYPE = 0x04
    MEMBER = 0x0D
    POINTER_TYPE = 0x0F
    STRUCTURE_TYPE = 0x13
    SUBROUTINE_TYPE = 0x2B
    UNION_TYPE = 0x17
    BASE_TYPE = 0x24
    CONST_TYPE = 0x26
    VOLATILE_TYPE = 0x35
    RESTRICT_TYPE = 0x37
    TYPEDEF = 0x16
    SUBPROGRAM = 0x2E
    VARIABLE = 0x34
    FORMAL_PARAMETER = 0x05
    LEXICAL_BLOCK = 0x0B
    COMPILE_UNIT = 0x11
    NAMESPACE = 0x39
    LABEL = 0x0A
    UNSPECIFIED_TYPE = 0x3B
    INLINED_SUBROUTINE = 0x1D


class DwarfAttribute(Enum):
    """DWARF 属性"""

    Sibling = 0x01
    Location = 0x02
    Name = 0x03
    Ordering = 0x09
    ByteSize = 0x0B
    BitOffset = 0x0C
    BitSize = 0x0D
    StmtList = 0x10
    LowPc = 0x11
    HighPc = 0x12
    Language = 0x13
    Discr = 0x15
    DiscrValue = 0x16
    Visibility = 0x17
    Import = 0x18
    StringLength = 0x19
    CommonReference = 0x1A
    CompDir = 0x1B
    ConstValue = 0x1C
    ContainingType = 0x1D
    DefaultValue = 0x1E
    DeclColumn = 0x39
    DeclFile = 0x3A
    DeclLine = 0x3B
    Encoding = 0x3E
    External = 0x03
    FrameBase = 0x40
    Type = 0x49
    Producer = 0x25
    Prototyped = 0x27
    ReturnAddr = 0x2A
    StartScope = 0x4C
    BitStride = 0x2E
    UpperBound = 0x2F
    AbstractOrigin = 0x31
    Accessibility = 0x32
    AddrClass = 0x33
    Artificial = 0x34
    DataMemberLocation = 0x38
    Declaration = 0x3C
    DiscrList = 0x3D
    EntryPc = 0x52
    Extension = 0x63
    IsOptional = 0x64
    LowerBound = 0x4F
    Priority = 0x65
    Segment = 0x66
    Specification = 0x67
    StaticLink = 0x68
    UseLocation = 0x6A
    Virtual = 0x6B
    VirtualTable = 0x6C


class DwarfForm(Enum):
    """DWARF 表单"""

    ADDR = 0x01
    BLOCK2 = 0x03
    BLOCK4 = 0x04
    DATA2 = 0x05
    DATA4 = 0x06
    DATA8 = 0x07
    STRING = 0x08
    BLOCK = 0x09
    BLOCK1 = 0x0A
    DATA1 = 0x0B
    FLAG = 0x0C
    SDATA = 0x0D
    STRP = 0x0E
    UDATA = 0x0F
    REF_ADDR = 0x10
    REF1 = 0x11
    REF2 = 0x12
    REF4 = 0x13
    REF8 = 0x14
    REF_UDATA = 0x15
    INDIRECT = 0x16
    SEC_OFFSET = 0x17
    EXPRLOC = 0x18
    FLAG_PRESENT = 0x19
    REF_SIG8 = 0x20


@dataclass
class AttributeSpec:
    """属性规范"""

    attribute: DwarfAttribute
    form: DwarfForm


@dataclass
class AbbreviationSpec:
    """缩写规范"""

    code: int
    tag: DwarfTag
    has_children: bool
    attributes: List[AttributeSpec] = field(default_factory=list)


@dataclass
class DIEAttribute:
    """DIE 属性值"""

    attribute: DwarfAttribute
    value: Any
    form: DwarfForm


@dataclass
class DIE:
    """Debug Information Entry"""

    tag: DwarfTag
    attributes: List[DIEAttribute] = field(default_factory=list)
    children: List["DIE"] = field(default_factory=list)

    def add_attribute(self, attr: DwarfAttribute, value: Any, form: DwarfForm) -> None:
        """添加属性"""
        self.attributes.append(DIEAttribute(attribute=attr, value=value, form=form))

    def add_child(self, child: "DIE") -> None:
        """添加子节点"""
        self.children.append(child)


class DIEBuilder:
    """
    DIE 构建器

    用于构建调试信息条目。
    """

    def create_compile_unit(
        self,
        name: str,
        low_pc: int = 0,
        high_pc: int = 0,
        language: int = 0x8000,  # ZHC 自定义
        producer: str = "ZhC Compiler",
        comp_dir: str = "",
    ) -> DIE:
        """创建编译单元 DIE"""
        cu = DIE(tag=DwarfTag.COMPILE_UNIT)
        cu.add_attribute(DwarfAttribute.Name, name, DwarfForm.STRING)
        cu.add_attribute(DwarfAttribute.LowPc, low_pc, DwarfForm.ADDR)
        cu.add_attribute(DwarfAttribute.HighPc, high_pc, DwarfForm.ADDR)
        cu.add_attribute(DwarfAttribute.Language, language, DwarfForm.DATA4)
        cu.add_attribute(DwarfAttribute.Producer, producer, DwarfForm.STRING)
        if comp_dir:
            cu.add_attribute(DwarfAttribute.CompDir, comp_dir, DwarfForm.STRING)
        return cu

    def create_subprogram(
        self,
        name: str,
        low_pc: int,
        high_pc: int,
        line: int = 0,
        decl_file: int = 0,
        return_type: Optional[DIE] = None,
        is_external: bool = False,
    ) -> DIE:
        """创建子程序 DIE"""
        sub = DIE(tag=DwarfTag.SUBPROGRAM)
        sub.add_attribute(DwarfAttribute.Name, name, DwarfForm.STRING)
        sub.add_attribute(DwarfAttribute.LowPc, low_pc, DwarfForm.ADDR)
        sub.add_attribute(DwarfAttribute.HighPc, high_pc, DwarfForm.ADDR)
        if line:
            sub.add_attribute(DwarfAttribute.DeclLine, line, DwarfForm.DATA4)
        if decl_file:
            sub.add_attribute(DwarfAttribute.DeclFile, decl_file, DwarfForm.DATA4)
        if is_external:
            sub.add_attribute(DwarfAttribute.External, True, DwarfForm.FLAG_PRESENT)
        return sub

    def create_formal_parameter(
        self,
        name: str,
        location: str,
        line: int = 0,
        type_die: Optional[DIE] = None,
    ) -> DIE:
        """创建形式参数 DIE"""
        param = DIE(tag=DwarfTag.FORMAL_PARAMETER)
        param.add_attribute(DwarfAttribute.Name, name, DwarfForm.STRING)
        param.add_attribute(DwarfAttribute.Location, location, DwarfForm.EXPRLOC)
        if line:
            param.add_attribute(DwarfAttribute.DeclLine, line, DwarfForm.DATA4)
        if type_die:
            param.add_attribute(DwarfAttribute.Type, type_die, DwarfForm.REF4)
        return param

    def create_variable(
        self,
        name: str,
        location: str,
        line: int = 0,
        decl_file: int = 0,
        type_die: Optional[DIE] = None,
        is_artificial: bool = False,
    ) -> DIE:
        """创建变量 DIE"""
        var = DIE(tag=DwarfTag.VARIABLE)
        var.add_attribute(DwarfAttribute.Name, name, DwarfForm.STRING)
        var.add_attribute(DwarfAttribute.Location, location, DwarfForm.EXPRLOC)
        if line:
            var.add_attribute(DwarfAttribute.DeclLine, line, DwarfForm.DATA4)
        if decl_file:
            var.add_attribute(DwarfAttribute.DeclFile, decl_file, DwarfForm.DATA4)
        if type_die:
            var.add_attribute(DwarfAttribute.Type, type_die, DwarfForm.REF4)
        if is_artificial:
            var.add_attribute(DwarfAttribute.Artificial, True, DwarfForm.FLAG_PRESENT)
        return var

    def create_lexical_block(
        self,
        low_pc: int,
        high_pc: int,
    ) -> DIE:
        """创建词法块 DIE"""
        block = DIE(tag=DwarfTag.LEXICAL_BLOCK)
        block.add_attribute(DwarfAttribute.LowPc, low_pc, DwarfForm.ADDR)
        block.add_attribute(DwarfAttribute.HighPc, high_pc, DwarfForm.ADDR)
        return block

    def create_base_type(
        self,
        name: str,
        byte_size: int,
        encoding: int,
    ) -> DIE:
        """创建基本类型 DIE"""
        btype = DIE(tag=DwarfTag.BASE_TYPE)
        btype.add_attribute(DwarfAttribute.Name, name, DwarfForm.STRING)
        btype.add_attribute(DwarfAttribute.ByteSize, byte_size, DwarfForm.DATA1)
        btype.add_attribute(DwarfAttribute.Encoding, encoding, DwarfForm.DATA1)
        return btype

    def create_pointer_type(
        self,
        byte_size: int,
        type_die: Optional[DIE] = None,
    ) -> DIE:
        """创建指针类型 DIE"""
        ptr = DIE(tag=DwarfTag.POINTER_TYPE)
        ptr.add_attribute(DwarfAttribute.ByteSize, byte_size, DwarfForm.DATA1)
        if type_die:
            ptr.add_attribute(DwarfAttribute.Type, type_die, DwarfForm.REF4)
        return ptr

    def create_struct_type(
        self,
        name: str,
        byte_size: int,
        decl_file: int = 0,
        decl_line: int = 0,
    ) -> DIE:
        """创建结构体类型 DIE"""
        stype = DIE(tag=DwarfTag.STRUCTURE_TYPE)
        stype.add_attribute(DwarfAttribute.Name, name, DwarfForm.STRING)
        stype.add_attribute(DwarfAttribute.ByteSize, byte_size, DwarfForm.DATA4)
        if decl_file:
            stype.add_attribute(DwarfAttribute.DeclFile, decl_file, DwarfForm.DATA4)
        if decl_line:
            stype.add_attribute(DwarfAttribute.DeclLine, decl_line, DwarfForm.DATA4)
        return stype

    def create_member(
        self,
        name: str,
        type_die: DIE,
        data_member_location: int,
        bit_size: int = 0,
        bit_offset: int = 0,
    ) -> DIE:
        """创建成员 DIE"""
        member = DIE(tag=DwarfTag.MEMBER)
        member.add_attribute(DwarfAttribute.Name, name, DwarfForm.STRING)
        member.add_attribute(DwarfAttribute.Type, type_die, DwarfForm.REF4)
        member.add_attribute(
            DwarfAttribute.DataMemberLocation, data_member_location, DwarfForm.DATA4
        )
        if bit_size:
            member.add_attribute(DwarfAttribute.BitSize, bit_size, DwarfForm.DATA4)
        if bit_offset:
            member.add_attribute(DwarfAttribute.BitOffset, bit_offset, DwarfForm.DATA4)
        return member


class CompileUnitBuilder:
    """
    编译单元构建器

    构建完整的编译单元 DIE 树。
    """

    def __init__(self):
        self.die_builder = DIEBuilder()
        self.root: Optional[DIE] = None
        self._type_cache: Dict[str, DIE] = {}

    def begin_compile_unit(
        self,
        name: str,
        producer: str = "ZhC Compiler",
        comp_dir: str = "",
    ) -> DIE:
        """开始编译单元"""
        self.root = self.die_builder.create_compile_unit(
            name=name,
            producer=producer,
            comp_dir=comp_dir,
        )
        return self.root

    def add_function(
        self,
        name: str,
        low_pc: int,
        high_pc: int,
        line: int = 0,
        is_external: bool = False,
    ) -> DIE:
        """添加函数"""
        if not self.root:
            raise RuntimeError("No active compile unit")

        func = self.die_builder.create_subprogram(
            name=name,
            low_pc=low_pc,
            high_pc=high_pc,
            line=line,
            is_external=is_external,
        )
        self.root.add_child(func)
        return func

    def add_parameter(
        self,
        parent: DIE,
        name: str,
        location: str,
        line: int = 0,
    ) -> DIE:
        """添加参数"""
        param = self.die_builder.create_formal_parameter(
            name=name,
            location=location,
            line=line,
        )
        parent.add_child(param)
        return param

    def add_variable(
        self,
        parent: DIE,
        name: str,
        location: str,
        line: int = 0,
        is_artificial: bool = False,
    ) -> DIE:
        """添加变量"""
        var = self.die_builder.create_variable(
            name=name,
            location=location,
            line=line,
            is_artificial=is_artificial,
        )
        parent.add_child(var)
        return var

    def add_lexical_block(
        self,
        parent: DIE,
        low_pc: int,
        high_pc: int,
    ) -> DIE:
        """添加词法块"""
        block = self.die_builder.create_lexical_block(
            low_pc=low_pc,
            high_pc=high_pc,
        )
        parent.add_child(block)
        return block

    def finalize(self) -> Optional[DIE]:
        """完成编译单元"""
        root = self.root
        self.root = None
        return root


class DebugInfoSection:
    """
    .debug_info 节生成器

    生成 DWARF 调试信息节。
    """

    def __init__(self, version: DwarfVersion = DwarfVersion.V4):
        self.version = version
        self.compile_units: List[DIE] = []
        self._cu_builder = CompileUnitBuilder()

    def add_compile_unit(
        self,
        name: str,
        producer: str = "ZhC Compiler",
        comp_dir: str = "",
    ) -> CompileUnitBuilder:
        """添加编译单元"""
        cu = self._cu_builder.begin_compile_unit(name, producer, comp_dir)
        self.compile_units.append(cu)
        return self._cu_builder

    def finalize_compile_unit(self) -> None:
        """完成当前编译单元"""
        self._cu_builder.finalize()

    def build(self) -> bytes:
        """
        构建 .debug_info 节数据

        Returns:
            节数据字节
        """
        data = bytearray()

        for cu in self.compile_units:
            data.extend(self._build_compile_unit(cu))

        return bytes(data)

    def _build_compile_unit(self, cu: DIE) -> bytes:
        """构建单个编译单元"""
        data = bytearray()

        # 编译单元头部（简化）
        # unit_length (4 bytes) + version (2 bytes) + debug_abbrev_offset (4 bytes) + address_size (1 byte)
        data.extend(struct.pack("<I", 0))  # unit_length placeholder
        data.extend(struct.pack("<H", self.version.value))  # version
        data.extend(struct.pack("<I", 0))  # debug_abbrev_offset
        data.extend(struct.pack("<B", 8))  # address_size

        # 编码 DIE
        data.extend(self._encode_die(cu))

        # 填充 unit_length
        length = len(data) - 4
        data[0:4] = struct.pack("<I", length)

        return bytes(data)

    def _encode_die(self, die: DIE) -> bytes:
        """编码 DIE"""
        data = bytearray()

        # 标签（简化：使用固定值）
        data.extend(self._encode_uleb128(die.tag.value))

        # 属性
        for attr in die.attributes:
            data.extend(self._encode_attribute(attr))

        # 结束标记
        data.append(0)

        # 子节点
        for child in die.children:
            data.extend(self._encode_die(child))

        # 子节点结束标记
        data.append(0)

        return bytes(data)

    def _encode_attribute(self, attr: DIEAttribute) -> bytes:
        """编码属性"""
        data = bytearray()

        # 属性代码
        data.extend(self._encode_uleb128(attr.attribute.value))

        # 属性值（简化）
        if attr.form == DwarfForm.STRING:
            if isinstance(attr.value, str):
                data.extend(attr.value.encode("utf-8"))
                data.append(0)
        elif attr.form == DwarfForm.DATA4:
            data.extend(struct.pack("<I", attr.value or 0))
        elif attr.form == DwarfForm.DATA1:
            data.extend(struct.pack("<B", attr.value or 0))
        elif attr.form == DwarfForm.ADDR:
            data.extend(struct.pack("<Q", attr.value or 0))
        elif attr.form == DwarfForm.FLAG_PRESENT:
            pass  # No value
        elif attr.form == DwarfForm.EXPRLOC:
            if isinstance(attr.value, bytes):
                data.extend(self._encode_uleb128(len(attr.value)))
                data.extend(attr.value)
            elif isinstance(attr.value, str):
                # 简化：字符串作为位置表达式
                expr = attr.value.encode("utf-8")
                data.extend(self._encode_uleb128(len(expr)))
                data.extend(expr)

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

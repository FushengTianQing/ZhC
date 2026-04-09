# -*- coding: utf-8 -*-
"""
ZhC 类型描述器

生成 DWARF 类型调试信息，支持基本类型、指针、数组、结构体等。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DwarfEncoding(Enum):
    """DWARF 基本类型编码"""

    ADDRESS = 0x01  # 地址
    BOOLEAN = 0x02  # 布尔
    COMPLEX_FLOAT = 0x03  # 复数浮点
    FLOAT = 0x04  # 浮点
    SIGNED = 0x05  # 有符号整数
    SIGNED_CHAR = 0x06  # 有符号字符
    UNSIGNED = 0x07  # 无符号整数
    UNSIGNED_CHAR = 0x08  # 无符号字符
    IMAGINARY_FLOAT = 0x09  # 虚数浮点
    PACKED_DECIMAL = 0x0A  # 打包十进制
    NUMERIC_STRING = 0x0B  # 数字字符串
    EDITED = 0x0C  # 编辑
    SIGNED_FIXED = 0x0D  # 有符号定点
    UNSIGNED_FIXED = 0x0E  # 无符号定点
    DECIMAL_FLOAT = 0x0F  # 十进制浮点
    UTF = 0x10  # UTF 字符
    UCS = 0x11  # UCS 字符
    ASCII = 0x12  # ASCII
    LO_USER = 0x80  # 用户自定义起始
    HI_USER = 0xFF  # 用户自定义结束


class TypeKind(Enum):
    """类型种类"""

    VOID = "void"
    BASIC = "basic"
    POINTER = "pointer"
    ARRAY = "array"
    STRUCT = "struct"
    UNION = "union"
    ENUM = "enum"
    FUNCTION = "function"
    TYPEDEF = "typedef"
    CONST = "const"
    VOLATILE = "volatile"
    RESTRICT = "restrict"


@dataclass
class TypeLayout:
    """类型布局信息"""

    size: int  # 字节大小
    alignment: int  # 对齐要求
    bit_size: int = 0  # 位大小
    bit_alignment: int = 0  # 位对齐

    def __post_init__(self):
        if self.bit_size == 0:
            self.bit_size = self.size * 8
        if self.bit_alignment == 0:
            self.bit_alignment = self.alignment * 8


@dataclass
class MemberInfo:
    """结构体/联合体成员信息"""

    name: str  # 成员名
    type_ref: str  # 类型引用
    offset: int  # 字节偏移
    bit_offset: int = 0  # 位偏移（位域）
    bit_size: int = 0  # 位大小（位域）
    is_bitfield: bool = False  # 是否为位域
    accessibility: str = "public"  # 访问级别


@dataclass
class TypeDebugDescriptor:
    """类型调试描述符"""

    name: str  # 类型名
    kind: TypeKind  # 类型种类
    layout: TypeLayout  # 布局信息
    encoding: Optional[DwarfEncoding] = None  # DWARF 编码（基本类型）
    base_type: Optional[str] = None  # 基础类型（指针/数组/typedef）
    element_type: Optional[str] = None  # 元素类型（数组）
    array_size: int = 0  # 数组大小
    members: List[MemberInfo] = field(default_factory=list)  # 成员列表
    return_type: Optional[str] = None  # 返回类型（函数）
    param_types: List[str] = field(default_factory=list)  # 参数类型（函数）
    decl_file: str = ""  # 声明文件
    decl_line: int = 0  # 声明行号
    is_artificial: bool = False  # 是否为编译器生成

    def get_dwarf_tag(self) -> int:
        """获取 DWARF 标签"""
        tag_map = {
            TypeKind.VOID: 0x3B,  # DW_TAG_unspecified_type
            TypeKind.BASIC: 0x24,  # DW_TAG_base_type
            TypeKind.POINTER: 0x0F,  # DW_TAG_pointer_type
            TypeKind.ARRAY: 0x01,  # DW_TAG_array_type
            TypeKind.STRUCT: 0x13,  # DW_TAG_structure_type
            TypeKind.UNION: 0x17,  # DW_TAG_union_type
            TypeKind.ENUM: 0x04,  # DW_TAG_enumeration_type
            TypeKind.FUNCTION: 0x2B,  # DW_TAG_subroutine_type
            TypeKind.TYPEDEF: 0x16,  # DW_TAG_typedef
            TypeKind.CONST: 0x26,  # DW_TAG_const_type
            TypeKind.VOLATILE: 0x35,  # DW_TAG_volatile_type
            TypeKind.RESTRICT: 0x37,  # DW_TAG_restrict_type
        }
        return tag_map.get(self.kind, 0x00)


class TypePrinter:
    """
    类型描述器

    生成 DWARF 类型调试信息。
    """

    def __init__(self):
        self.type_descriptors: Dict[str, TypeDebugDescriptor] = {}
        self._type_id_counter = 0
        self._init_builtin_types()

    def _init_builtin_types(self) -> None:
        """初始化内置类型"""
        # ZhC 中文类型名映射
        builtin_types = [
            # 整数类型
            ("整数型", 4, DwarfEncoding.SIGNED),
            ("短整数型", 2, DwarfEncoding.SIGNED),
            ("长整数型", 8, DwarfEncoding.SIGNED),
            ("字节型", 1, DwarfEncoding.UNSIGNED),
            # 浮点类型
            ("浮点型", 4, DwarfEncoding.FLOAT),
            ("双精度型", 8, DwarfEncoding.FLOAT),
            # 字符类型
            ("字符型", 1, DwarfEncoding.SIGNED_CHAR),
            ("宽字符型", 4, DwarfEncoding.UCS),
            # 布尔类型
            ("布尔型", 1, DwarfEncoding.BOOLEAN),
            # 空类型
            ("空型", 0, None),
        ]

        for name, size, encoding in builtin_types:
            layout = TypeLayout(size=size, alignment=size if size > 0 else 1)
            kind = TypeKind.VOID if name == "空型" else TypeKind.BASIC
            descriptor = TypeDebugDescriptor(
                name=name,
                kind=kind,
                layout=layout,
                encoding=encoding,
            )
            self.type_descriptors[name] = descriptor

        # C 风格类型名别名
        c_type_aliases = {
            "int": "整数型",
            "short": "短整数型",
            "long": "长整数型",
            "byte": "字节型",
            "float": "浮点型",
            "double": "双精度型",
            "char": "字符型",
            "wchar_t": "宽字符型",
            "bool": "布尔型",
            "void": "空型",
            "_Bool": "布尔型",
        }

        for alias, canonical in c_type_aliases.items():
            if canonical in self.type_descriptors:
                self.type_descriptors[alias] = self.type_descriptors[canonical]

    def register_type(self, descriptor: TypeDebugDescriptor) -> int:
        """
        注册类型描述符

        Args:
            descriptor: 类型描述符

        Returns:
            类型 ID
        """
        self._type_id_counter += 1
        self.type_descriptors[descriptor.name] = descriptor
        return self._type_id_counter

    def create_pointer_type(
        self,
        name: str,
        base_type: str,
        byte_size: int = 8,
    ) -> TypeDebugDescriptor:
        """
        创建指针类型

        Args:
            name: 类型名
            base_type: 基础类型
            byte_size: 指针大小

        Returns:
            类型描述符
        """
        layout = TypeLayout(size=byte_size, alignment=byte_size)
        descriptor = TypeDebugDescriptor(
            name=name,
            kind=TypeKind.POINTER,
            layout=layout,
            base_type=base_type,
        )
        self.register_type(descriptor)
        return descriptor

    def create_array_type(
        self,
        name: str,
        element_type: str,
        array_size: int,
        element_size: int,
    ) -> TypeDebugDescriptor:
        """
        创建数组类型

        Args:
            name: 类型名
            element_type: 元素类型
            array_size: 数组大小
            element_size: 元素大小

        Returns:
            类型描述符
        """
        total_size = array_size * element_size
        layout = TypeLayout(size=total_size, alignment=element_size)
        descriptor = TypeDebugDescriptor(
            name=name,
            kind=TypeKind.ARRAY,
            layout=layout,
            element_type=element_type,
            array_size=array_size,
        )
        self.register_type(descriptor)
        return descriptor

    def create_struct_type(
        self,
        name: str,
        members: List[MemberInfo],
        total_size: int,
        alignment: int = 8,
        decl_file: str = "",
        decl_line: int = 0,
    ) -> TypeDebugDescriptor:
        """
        创建结构体类型

        Args:
            name: 类型名
            members: 成员列表
            total_size: 总大小
            alignment: 对齐要求
            decl_file: 声明文件
            decl_line: 声明行号

        Returns:
            类型描述符
        """
        layout = TypeLayout(size=total_size, alignment=alignment)
        descriptor = TypeDebugDescriptor(
            name=name,
            kind=TypeKind.STRUCT,
            layout=layout,
            members=members,
            decl_file=decl_file,
            decl_line=decl_line,
        )
        self.register_type(descriptor)
        return descriptor

    def create_union_type(
        self,
        name: str,
        members: List[MemberInfo],
        max_size: int,
        alignment: int = 8,
    ) -> TypeDebugDescriptor:
        """
        创建联合体类型

        Args:
            name: 类型名
            members: 成员列表
            max_size: 最大成员大小
            alignment: 对齐要求

        Returns:
            类型描述符
        """
        layout = TypeLayout(size=max_size, alignment=alignment)
        descriptor = TypeDebugDescriptor(
            name=name,
            kind=TypeKind.UNION,
            layout=layout,
            members=members,
        )
        self.register_type(descriptor)
        return descriptor

    def create_enum_type(
        self,
        name: str,
        byte_size: int = 4,
        decl_file: str = "",
        decl_line: int = 0,
    ) -> TypeDebugDescriptor:
        """
        创建枚举类型

        Args:
            name: 类型名
            byte_size: 字节大小
            decl_file: 声明文件
            decl_line: 声明行号

        Returns:
            类型描述符
        """
        layout = TypeLayout(size=byte_size, alignment=byte_size)
        descriptor = TypeDebugDescriptor(
            name=name,
            kind=TypeKind.ENUM,
            layout=layout,
            decl_file=decl_file,
            decl_line=decl_line,
        )
        self.register_type(descriptor)
        return descriptor

    def create_function_type(
        self,
        name: str,
        return_type: str,
        param_types: List[str],
    ) -> TypeDebugDescriptor:
        """
        创建函数类型

        Args:
            name: 类型名
            return_type: 返回类型
            param_types: 参数类型列表

        Returns:
            类型描述符
        """
        layout = TypeLayout(size=0, alignment=1)  # 函数类型没有大小
        descriptor = TypeDebugDescriptor(
            name=name,
            kind=TypeKind.FUNCTION,
            layout=layout,
            return_type=return_type,
            param_types=param_types,
        )
        self.register_type(descriptor)
        return descriptor

    def create_typedef(
        self,
        name: str,
        base_type: str,
        decl_file: str = "",
        decl_line: int = 0,
    ) -> TypeDebugDescriptor:
        """
        创建类型别名

        Args:
            name: 类型别名
            base_type: 基础类型
            decl_file: 声明文件
            decl_line: 声明行号

        Returns:
            类型描述符
        """
        # 获取基础类型的布局
        base_desc = self.get_type(base_type)
        layout = base_desc.layout if base_desc else TypeLayout(size=0, alignment=1)

        descriptor = TypeDebugDescriptor(
            name=name,
            kind=TypeKind.TYPEDEF,
            layout=layout,
            base_type=base_type,
            decl_file=decl_file,
            decl_line=decl_line,
        )
        self.register_type(descriptor)
        return descriptor

    def get_type(self, name: str) -> Optional[TypeDebugDescriptor]:
        """获取类型描述符"""
        return self.type_descriptors.get(name)

    def get_type_size(self, name: str) -> int:
        """获取类型大小"""
        desc = self.get_type(name)
        return desc.layout.size if desc else 0

    def get_type_alignment(self, name: str) -> int:
        """获取类型对齐"""
        desc = self.get_type(name)
        return desc.layout.alignment if desc else 1

    def print_type(self, name: str) -> str:
        """
        打印类型描述

        Args:
            name: 类型名

        Returns:
            类型描述字符串
        """
        desc = self.get_type(name)
        if not desc:
            return f"<unknown type: {name}>"

        parts = [f"{desc.kind.value} {name}"]

        # 大小和对齐
        parts.append(f"  size: {desc.layout.size} bytes ({desc.layout.bit_size} bits)")
        parts.append(f"  alignment: {desc.layout.alignment} bytes")

        # 类型特定信息
        if desc.kind == TypeKind.BASIC and desc.encoding:
            parts.append(f"  encoding: {desc.encoding.name}")

        elif desc.kind == TypeKind.POINTER:
            parts.append(f"  points to: {desc.base_type}")

        elif desc.kind == TypeKind.ARRAY:
            parts.append(f"  element type: {desc.element_type}")
            parts.append(f"  array size: {desc.array_size}")

        elif desc.kind in (TypeKind.STRUCT, TypeKind.UNION):
            parts.append("  members:")
            for member in desc.members:
                offset_str = f"offset={member.offset}"
                if member.is_bitfield:
                    offset_str += f" bits={member.bit_offset}:{member.bit_size}"
                parts.append(f"    {member.name}: {member.type_ref} ({offset_str})")

        elif desc.kind == TypeKind.FUNCTION:
            params = ", ".join(desc.param_types) or "void"
            parts.append(f"  signature: {desc.return_type}({params})")

        elif desc.kind == TypeKind.TYPEDEF:
            parts.append(f"  alias for: {desc.base_type}")

        return "\n".join(parts)

    def generate_dwarf_type_info(self, name: str) -> Dict[str, Any]:
        """
        生成 DWARF 类型信息

        Args:
            name: 类型名

        Returns:
            DWARF 类型信息字典
        """
        desc = self.get_type(name)
        if not desc:
            return {}

        info = {
            "name": name,
            "tag": desc.get_dwarf_tag(),
            "byte_size": desc.layout.size,
            "alignment": desc.layout.alignment,
        }

        if desc.encoding:
            info["encoding"] = desc.encoding.value

        if desc.base_type:
            info["base_type"] = desc.base_type

        if desc.element_type:
            info["element_type"] = desc.element_type
            info["array_size"] = desc.array_size

        if desc.members:
            info["members"] = [
                {
                    "name": m.name,
                    "type": m.type_ref,
                    "offset": m.offset,
                    "bit_offset": m.bit_offset,
                    "bit_size": m.bit_size,
                    "is_bitfield": m.is_bitfield,
                }
                for m in desc.members
            ]

        if desc.return_type:
            info["return_type"] = desc.return_type
            info["param_types"] = desc.param_types

        return info

    def list_types(self) -> List[str]:
        """列出所有已注册类型"""
        return list(self.type_descriptors.keys())

    def export_types(self) -> Dict[str, Dict]:
        """导出所有类型信息"""
        return {
            name: self.generate_dwarf_type_info(name) for name in self.type_descriptors
        }

# -*- coding: utf-8 -*-
"""
ZhC 目标文件写入器

生成各种格式的目标文件（ELF、MachO、Wasm）。

作者：远
日期：2026-04-09
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, BinaryIO
from enum import IntEnum
import struct
import logging

from zhc.codegen.target_registry import OperatingSystem

logger = logging.getLogger(__name__)


# ============================================================================
# 基础类型和常量
# ============================================================================


class SectionType(IntEnum):
    """节类型"""

    NULL = 0
    PROGBITS = 1
    SYMTAB = 2
    STRTAB = 3
    RELA = 4
    HASH = 5
    DYNAMIC = 6
    NOTE = 7
    NOBITS = 8
    REL = 9
    DYNSYM = 11
    INIT_ARRAY = 14
    FINI_ARRAY = 15
    DEBUG_INFO = 0x100
    DEBUG_LINE = 0x101
    DEBUG_ABBREV = 0x102


class SymbolBinding(IntEnum):
    """符号绑定类型"""

    LOCAL = 0
    GLOBAL = 1
    WEAK = 2


class SymbolType(IntEnum):
    """符号类型"""

    NOTYPE = 0
    OBJECT = 1
    FUNC = 2
    SECTION = 3
    FILE = 4


@dataclass
class Section:
    """节描述"""

    name: str
    type: SectionType
    address: int = 0
    data: bytes = b""
    flags: int = 0
    link: int = 0
    info: int = 0
    alignment: int = 1

    # 填充后的偏移（由布局器设置）
    offset: int = 0
    size: int = 0


@dataclass
class Symbol:
    """符号描述"""

    name: str
    value: int = 0
    size: int = 0
    binding: SymbolBinding = SymbolBinding.LOCAL
    type: SymbolType = SymbolType.NOTYPE
    section_index: int = 0

    # 在符号表中的索引
    index: int = 0


@dataclass
class Relocation:
    """重定位描述"""

    offset: int
    symbol: Symbol
    type: int
    addend: int = 0
    section_index: int = 0


# ============================================================================
# 对象文件写入器基类
# ============================================================================


class ObjectWriter(ABC):
    """
    目标文件写入器基类

    所有目标文件格式写入器应继承此类。
    """

    def __init__(self):
        self.sections: Dict[str, Section] = {}
        self.symbols: Dict[str, Symbol] = {}
        self.relocations: List[Relocation] = []

    def add_section(self, section: Section) -> None:
        """添加节"""
        self.sections[section.name] = section

    def add_symbol(self, symbol: Symbol) -> None:
        """添加符号"""
        symbol.index = len(self.symbols)
        self.symbols[symbol.name] = symbol

    def add_relocation(self, reloc: Relocation) -> None:
        """添加重定位"""
        self.relocations.append(reloc)

    @abstractmethod
    def write(self, output_path: str) -> None:
        """写入目标文件"""
        pass

    @abstractmethod
    def get_format_name(self) -> str:
        """获取格式名称"""
        pass


# ============================================================================
# ELF 目标文件写入器
# ============================================================================


class ELFObjectWriter(ObjectWriter):
    """
    ELF 目标文件写入器

    生成 Linux/Unix 系统使用的 ELF 格式目标文件。
    """

    # ELF 魔数
    ELF_MAGIC = b"\x7fELF"

    # ELF 类
    ELFCLASS32 = 1
    ELFCLASS64 = 2

    # ELF 数据编码
    ELFDATA2LSB = 1  # 小端
    ELFDATA2MSB = 2  # 大端

    # ELF 类型
    ET_REL = 1  # 可重定位文件
    ET_EXEC = 2  # 可执行文件
    ET_DYN = 3  # 共享对象

    # ELF 机器类型
    EM_X86_64 = 62
    EM_AARCH64 = 183
    EM_ARM = 40
    EM_RISCV = 243

    def __init__(self, is_64bit: bool = True, is_little_endian: bool = True):
        super().__init__()
        self.is_64bit = is_64bit
        self.is_little_endian = is_little_endian

    def get_format_name(self) -> str:
        return "ELF"

    def write(self, output_path: str) -> None:
        """写入 ELF 文件"""
        with open(output_path, "wb") as f:
            # 1. 写入 ELF 头
            self._write_elf_header(f)

            # 2. 写入节内容
            self._write_section_contents(f)

            # 3. 写入节头表
            self._write_section_headers(f)

    def _write_elf_header(self, f: BinaryIO) -> None:
        """写入 ELF 头"""
        # e_ident (16 bytes)
        e_ident = bytearray(16)
        e_ident[0:4] = self.ELF_MAGIC
        e_ident[4] = self.ELFCLASS64 if self.is_64bit else self.ELFCLASS32
        e_ident[5] = self.ELFDATA2LSB if self.is_little_endian else self.ELFDATA2MSB
        e_ident[6] = 1  # ELF 版本

        f.write(bytes(e_ident))

        if self.is_64bit:
            # ELF64 头
            # e_type (2 bytes)
            f.write(struct.pack("<H", self.ET_REL))
            # e_machine (2 bytes)
            f.write(struct.pack("<H", self.EM_X86_64))
            # e_version (4 bytes)
            f.write(struct.pack("<I", 1))
            # e_entry (8 bytes)
            f.write(struct.pack("<Q", 0))
            # e_phoff (8 bytes)
            f.write(struct.pack("<Q", 0))
            # e_shoff (8 bytes) - 稍后更新
            shoff_pos = f.tell()
            f.write(struct.pack("<Q", 0))
            # e_flags (4 bytes)
            f.write(struct.pack("<I", 0))
            # e_ehsize (2 bytes)
            f.write(struct.pack("<H", 64))
            # e_phentsize (2 bytes)
            f.write(struct.pack("<H", 0))
            # e_phnum (2 bytes)
            f.write(struct.pack("<H", 0))
            # e_shentsize (2 bytes)
            f.write(struct.pack("<H", 64))
            # e_shnum (2 bytes)
            f.write(struct.pack("<H", len(self.sections) + 2))  # +null +shstrtab
            # e_shstrndx (2 bytes)
            f.write(struct.pack("<H", len(self.sections) + 1))

        else:
            # ELF32 头
            f.write(struct.pack("<H", self.ET_REL))
            f.write(struct.pack("<H", self.EM_ARM))
            f.write(struct.pack("<I", 1))
            f.write(struct.pack("<I", 0))
            f.write(struct.pack("<I", 0))
            shoff_pos = f.tell()
            f.write(struct.pack("<I", 0))
            f.write(struct.pack("<I", 0))
            f.write(struct.pack("<H", 52))
            f.write(struct.pack("<H", 0))
            f.write(struct.pack("<H", 0))
            f.write(struct.pack("<H", 40))
            f.write(struct.pack("<H", len(self.sections) + 2))
            f.write(struct.pack("<H", len(self.sections) + 1))

        # 保存 shoff 位置以便稍后更新
        self._shoff_pos = shoff_pos

    def _write_section_contents(self, f: BinaryIO) -> None:
        """写入节内容"""
        # 计算节偏移
        header_size = 64 if self.is_64bit else 52
        current_offset = header_size

        for name, section in self.sections.items():
            # 对齐
            alignment = section.alignment
            if alignment > 1:
                padding = (alignment - (current_offset % alignment)) % alignment
                f.write(b"\x00" * padding)
                current_offset += padding

            section.offset = current_offset
            section.size = len(section.data)

            f.write(section.data)
            current_offset += len(section.data)

        # 保存节头表偏移
        self._shoff = current_offset

    def _write_section_headers(self, f: BinaryIO) -> None:
        """写入节头表"""
        # 更新 e_shoff
        current_pos = f.tell()
        f.seek(self._shoff_pos)
        if self.is_64bit:
            f.write(struct.pack("<Q", self._shoff))
        else:
            f.write(struct.pack("<I", self._shoff))
        f.seek(current_pos)

        # 写入空节头
        self._write_null_section_header(f)

        # 写入各节头
        for i, (name, section) in enumerate(self.sections.items(), 1):
            self._write_section_header(f, section, i)

        # 写入 .shstrtab 节头
        self._write_shstrtab_header(f)

    def _write_null_section_header(self, f: BinaryIO) -> None:
        """写入空节头"""
        if self.is_64bit:
            f.write(b"\x00" * 64)
        else:
            f.write(b"\x00" * 40)

    def _write_section_header(self, f: BinaryIO, section: Section, index: int) -> None:
        """写入节头"""
        if self.is_64bit:
            f.write(struct.pack("<I", 0))  # sh_name (稍后更新)
            f.write(struct.pack("<I", section.type))
            f.write(struct.pack("<Q", section.flags))
            f.write(struct.pack("<Q", section.address))
            f.write(struct.pack("<Q", section.offset))
            f.write(struct.pack("<Q", section.size))
            f.write(struct.pack("<I", section.link))
            f.write(struct.pack("<I", section.info))
            f.write(struct.pack("<Q", section.alignment))
            f.write(struct.pack("<Q", 0))  # sh_entsize
        else:
            f.write(struct.pack("<I", 0))
            f.write(struct.pack("<I", section.type))
            f.write(struct.pack("<I", section.flags))
            f.write(struct.pack("<I", section.address))
            f.write(struct.pack("<I", section.offset))
            f.write(struct.pack("<I", section.size))
            f.write(struct.pack("<I", section.link))
            f.write(struct.pack("<I", section.info))
            f.write(struct.pack("<I", section.alignment))
            f.write(struct.pack("<I", 0))

    def _write_shstrtab_header(self, f: BinaryIO) -> None:
        """写入 .shstrtab 节头"""
        # 简化实现
        pass


# ============================================================================
# MachO 目标文件写入器
# ============================================================================


class MachOObjectWriter(ObjectWriter):
    """
    MachO 目标文件写入器

    生成 macOS/iOS 系统使用的 MachO 格式目标文件。
    """

    # MachO 魔数
    MH_MAGIC_64 = 0xFEEDFACF
    MH_CIGAM_64 = 0xCFFAEDFE

    # CPU 类型
    CPU_TYPE_X86_64 = 0x01000007
    CPU_TYPE_ARM64 = 0x0100000C

    # 文件类型
    MH_OBJECT = 1
    MH_EXECUTE = 2
    MH_DYLIB = 6

    def __init__(self, is_64bit: bool = True, cpu_type: int = 0x01000007):
        super().__init__()
        self.is_64bit = is_64bit
        self.cpu_type = cpu_type

    def get_format_name(self) -> str:
        return "MachO"

    def write(self, output_path: str) -> None:
        """写入 MachO 文件"""
        with open(output_path, "wb") as f:
            # 1. 写入 MachO 头
            self._write_macho_header(f)

            # 2. 写入 segment 命令
            self._write_segment_commands(f)

            # 3. 写入节内容
            self._write_section_contents(f)

            # 4. 写入符号表
            self._write_symbol_table(f)

    def _write_macho_header(self, f: BinaryIO) -> None:
        """写入 MachO 头"""
        # mach_header_64
        f.write(struct.pack("<I", self.MH_MAGIC_64))
        f.write(struct.pack("<I", self.cpu_type))
        f.write(struct.pack("<I", 0))  # cpusubtype
        f.write(struct.pack("<I", self.MH_OBJECT))
        f.write(struct.pack("<I", len(self.sections)))  # ncmds
        f.write(struct.pack("<I", 0))  # sizeofcmds
        f.write(struct.pack("<I", 0))  # flags
        f.write(struct.pack("<I", 0))  # reserved

    def _write_segment_commands(self, f: BinaryIO) -> None:
        """写入 segment 命令"""
        # 简化实现
        pass

    def _write_section_contents(self, f: BinaryIO) -> None:
        """写入节内容"""
        for name, section in self.sections.items():
            f.write(section.data)

    def _write_symbol_table(self, f: BinaryIO) -> None:
        """写入符号表"""
        # 简化实现
        pass


# ============================================================================
# WebAssembly 目标文件写入器
# ============================================================================


class WasmObjectWriter(ObjectWriter):
    """
    WebAssembly 目标文件写入器

    生成 WebAssembly 二进制格式文件。
    """

    # Wasm 魔数
    WASM_MAGIC = b"\x00asm"
    WASM_VERSION = 1

    # Section ID
    SECTION_TYPE = 1
    SECTION_IMPORT = 2
    SECTION_FUNCTION = 3
    SECTION_TABLE = 4
    SECTION_MEMORY = 5
    SECTION_GLOBAL = 6
    SECTION_EXPORT = 7
    SECTION_START = 8
    SECTION_ELEMENT = 9
    SECTION_CODE = 10
    SECTION_DATA = 11

    def __init__(self):
        super().__init__()

    def get_format_name(self) -> str:
        return "WebAssembly"

    def write(self, output_path: str) -> None:
        """写入 Wasm 文件"""
        with open(output_path, "wb") as f:
            # 1. 写入魔数和版本
            f.write(self.WASM_MAGIC)
            self._write_leb128(f, self.WASM_VERSION)

            # 2. 写入类型段
            self._write_type_section(f)

            # 3. 写入函数段
            self._write_function_section(f)

            # 4. 写入代码段
            self._write_code_section(f)

            # 5. 写入数据段
            self._write_data_section(f)

    def _write_leb128(self, f: BinaryIO, value: int, signed: bool = False) -> None:
        """写入 LEB128 编码的整数"""
        if signed:
            self._write_sleb128(f, value)
        else:
            self._write_uleb128(f, value)

    def _write_uleb128(self, f: BinaryIO, value: int) -> None:
        """写入无符号 LEB128"""
        while True:
            byte = value & 0x7F
            value >>= 7
            if value != 0:
                byte |= 0x80
            f.write(bytes([byte]))
            if value == 0:
                break

    def _write_sleb128(self, f: BinaryIO, value: int) -> None:
        """写入有符号 LEB128"""
        more = True
        while more:
            byte = value & 0x7F
            value >>= 7
            if (value == 0 and (byte & 0x40) == 0) or (
                value == -1 and (byte & 0x40) != 0
            ):
                more = False
            else:
                byte |= 0x80
            f.write(bytes([byte]))

    def _write_type_section(self, f: BinaryIO) -> None:
        """写入类型段"""
        # 简化实现
        pass

    def _write_function_section(self, f: BinaryIO) -> None:
        """写入函数段"""
        # 简化实现
        pass

    def _write_code_section(self, f: BinaryIO) -> None:
        """写入代码段"""
        # 简化实现
        pass

    def _write_data_section(self, f: BinaryIO) -> None:
        """写入数据段"""
        # 简化实现
        pass


# ============================================================================
# 工厂函数
# ============================================================================


def create_object_writer(os: OperatingSystem, is_64bit: bool = True) -> ObjectWriter:
    """
    创建适合目标操作系统的对象文件写入器

    Args:
        os: 目标操作系统
        is_64bit: 是否为 64 位

    Returns:
        对应的对象文件写入器
    """
    if os == OperatingSystem.LINUX:
        return ELFObjectWriter(is_64bit=is_64bit)
    elif os == OperatingSystem.DARWIN:
        return MachOObjectWriter(is_64bit=is_64bit)
    elif os == OperatingSystem.WINDOWS:
        # Windows 使用 COFF 格式，这里简化为 ELF
        return ELFObjectWriter(is_64bit=is_64bit)
    else:
        return ELFObjectWriter(is_64bit=is_64bit)

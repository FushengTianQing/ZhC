# -*- coding: utf-8 -*-
"""
ZhC 重定位信息管理

管理目标文件中的重定位条目，支持多种目标文件格式（ELF、MachO、COFF）。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from typing import Dict, List, Optional
import struct
import logging

from zhc.codegen.symbol_table import Symbol

logger = logging.getLogger(__name__)


# ============================================================================
# 重定位类型定义
# ============================================================================


class RelocFormat(Enum):
    """重定位格式"""

    ELF = auto()
    MACHO = auto()
    COFF = auto()
    WASM = auto()


class ELFRelocType(IntEnum):
    """ELF 重定位类型（x86_64）"""

    # 基本重定位
    R_X86_64_NONE = 0
    R_X86_64_64 = 1  # 64 位绝对地址
    R_X86_64_PC32 = 2  # 32 位 PC 相对
    R_X86_64_GOT32 = 3  # 32 位 GOT 偏移
    R_X86_64_PLT32 = 4  # 32 位 PLT 地址
    R_X86_64_COPY = 5  # 复制符号
    R_X86_64_GLOB_DAT = 6  # 创建 GOT 条目
    R_X86_64_JUMP_SLOT = 7  # 创建 PLT 条目
    R_X86_64_RELATIVE = 8  # 调整相对地址
    R_X86_64_GOTPCREL = 9  # 32 位 PC 相对 GOT
    R_X86_64_32 = 10  # 32 位绝对地址
    R_X86_64_32S = 11  # 32 位有符号绝对地址
    R_X86_64_16 = 12  # 16 位绝对地址
    R_X86_64_PC16 = 13  # 16 位 PC 相对
    R_X86_64_8 = 14  # 8 位绝对地址
    R_X86_64_PC8 = 15  # 8 位 PC 相对
    R_X86_64_IRELATIVE = 37  # 间接相对
    R_X86_64_REX_GOTPCRELX = 42  # 优化的 GOTPCREL


class ELFRelocTypeAArch64(IntEnum):
    """ELF 重定位类型（AArch64）"""

    R_AARCH64_NONE = 0
    R_AARCH64_ABS64 = 257  # 64 位绝对地址
    R_AARCH64_ABS32 = 258  # 32 位绝对地址
    R_AARCH64_ABS16 = 259  # 16 位绝对地址
    R_AARCH64_PREL64 = 260  # 64 位 PC 相对
    R_AARCH64_PREL32 = 261  # 32 位 PC 相对
    R_AARCH64_PREL16 = 262  # 16 位 PC 相对
    R_AARCH64_CALL26 = 283  # 26 位调用
    R_AARCH64_JUMP26 = 282  # 26 位跳转
    R_AARCH64_ADR_PREL_PG_HI21 = 275  # ADRP 指令
    R_AARCH64_ADD_ABS_LO12_NC = 276  # ADD 指令


class MachORelocType(IntEnum):
    """MachO 重定位类型（x86_64）"""

    # 通用类型
    X86_64_RELOC_UNSIGNED = 0  # 绝对地址
    X86_64_RELOC_SIGNED = 1  # 32 位 PC 相对
    X86_64_RELOC_BRANCH = 2  # 分支指令
    X86_64_RELOC_GOT_LOAD = 3  # GOT 加载
    X86_64_RELOC_GOT = 4  # GOT 引用
    X86_64_RELOC_SUBTRACTOR = 5  # 减法
    X86_64_RELOC_SIGNED_1 = 6  # 1 字节偏移
    X86_64_RELOC_SIGNED_2 = 7  # 2 字节偏移
    X86_64_RELOC_SIGNED_4 = 8  # 4 字节偏移
    X86_64_RELOC_TLV = 9  # 线程局部变量


class MachORelocTypeARM64(IntEnum):
    """MachO 重定位类型（ARM64）"""

    ARM64_RELOC_UNSIGNED = 0  # 绝对地址
    ARM64_RELOC_SUBTRACTOR = 1  # 减法
    ARM64_RELOC_BRANCH26 = 2  # 26 位分支
    ARM64_RELOC_PAGE21 = 3  # ADRP
    ARM64_RELOC_PAGEOFF12 = 4  # 页内偏移
    ARM64_RELOC_GOT_LOAD_PAGE21 = 5  # GOT ADRP
    ARM64_RELOC_GOT_LOAD_PAGEOFF12 = 6  # GOT 页内偏移


class COFFRelocType(IntEnum):
    """COFF 重定位类型（x86_64）"""

    IMAGE_REL_AMD64_ADDR64 = 1  # 64 位绝对地址
    IMAGE_REL_AMD64_ADDR32 = 2  # 32 位绝对地址
    IMAGE_REL_AMD64_ADDR32NB = 3  # 32 位相对地址
    IMAGE_REL_AMD64_REL32 = 4  # 32 位 PC 相对
    IMAGE_REL_AMD64_REL32_1 = 5  # 32 位 PC 相对 + 1
    IMAGE_REL_AMD64_REL32_2 = 6  # 32 位 PC 相对 + 2
    IMAGE_REL_AMD64_REL32_3 = 7  # 32 位 PC 相对 + 3
    IMAGE_REL_AMD64_REL32_4 = 8  # 32 位 PC 相对 + 4
    IMAGE_REL_AMD64_REL32_5 = 9  # 32 位 PC 相对 + 5
    IMAGE_REL_AMD64_SECTION = 10  # 节索引
    IMAGE_REL_AMD64_SECREL = 11  # 节内偏移
    IMAGE_REL_AMD64_SECREL7 = 12  # 7 位节内偏移


class WasmRelocType(IntEnum):
    """WebAssembly 重定位类型"""

    R_WASM_FUNCTION_INDEX_LEB = 0  # 函数索引
    R_WASM_TABLE_INDEX_SLEB = 1  # 表索引
    R_WASM_TABLE_INDEX_I32 = 2  # 表索引（32 位）
    R_WASM_MEMORY_ADDR_LEB = 3  # 内存地址
    R_WASM_MEMORY_ADDR_SLEB = 4  # 内存地址（有符号）
    R_WASM_MEMORY_ADDR_I32 = 5  # 内存地址（32 位）
    R_WASM_TYPE_INDEX_LEB = 6  # 类型索引
    R_WASM_GLOBAL_INDEX_LEB = 7  # 全局索引
    R_WASM_FUNCTION_OFFSET_I32 = 8  # 函数偏移
    R_WASM_SECTION_OFFSET_I32 = 9  # 节偏移


# ============================================================================
# 重定位条目
# ============================================================================


@dataclass
class RelocationEntry:
    """
    重定位条目

    表示一个需要链接器处理的重定位。
    """

    # 基本属性
    offset: int  # 重定位位置（相对于节起始）
    symbol: Symbol  # 关联的符号
    type: int  # 重定位类型（格式相关）
    format: RelocFormat  # 重定位格式

    # 附加信息
    addend: int = 0  # 附加偏移量
    section: str = ""  # 所属节名称

    # 格式相关属性
    is_pc_relative: bool = False  # 是否为 PC 相对
    size: int = 4  # 重定位大小（字节）
    is_signed: bool = False  # 是否为有符号

    # MachO 特有
    scattered: bool = False  # 是否为分散重定位

    # COFF 特有
    is_section_rel: bool = False  # 是否为节相对

    def __str__(self) -> str:
        return f"Reloc({self.offset:#x}, {self.symbol.name}, type={self.type})"


# ============================================================================
# 重定位管理器
# ============================================================================


class Relocator:
    """
    重定位管理器

    管理目标文件中的所有重定位信息，支持多种格式。

    使用方式：
        reloc = Relocator(RelocFormat.ELF)
        reloc.add_relocation(offset=0x10, symbol=main_sym, type=ELFRelocType.R_X86_64_PC32)
        entries = reloc.get_relocations_for_section(".text")
    """

    def __init__(self, format: RelocFormat = RelocFormat.ELF):
        """
        初始化重定位管理器

        Args:
            format: 重定位格式
        """
        self.format = format
        self._entries: Dict[str, List[RelocationEntry]] = {}
        self._all_entries: List[RelocationEntry] = []

    # =========================================================================
    # 添加重定位
    # =========================================================================

    def add_relocation(
        self,
        offset: int,
        symbol: Symbol,
        reloc_type: int,
        section: str = ".text",
        addend: int = 0,
        size: int = 4,
        is_pc_relative: bool = False,
    ) -> RelocationEntry:
        """
        添加重定位条目

        Args:
            offset: 重定位位置
            symbol: 关联符号
            reloc_type: 重定位类型
            section: 所属节
            addend: 附加偏移
            size: 重定位大小
            is_pc_relative: 是否为 PC 相对

        Returns:
            创建的重定位条目
        """
        entry = RelocationEntry(
            offset=offset,
            symbol=symbol,
            type=reloc_type,
            format=self.format,
            addend=addend,
            section=section,
            size=size,
            is_pc_relative=is_pc_relative,
        )

        if section not in self._entries:
            self._entries[section] = []
        self._entries[section].append(entry)
        self._all_entries.append(entry)

        return entry

    def add_elf_relocation(
        self,
        offset: int,
        symbol: Symbol,
        reloc_type: ELFRelocType,
        section: str = ".text",
        addend: int = 0,
    ) -> RelocationEntry:
        """
        添加 ELF 重定位

        Args:
            offset: 重定位位置
            symbol: 关联符号
            reloc_type: ELF 重定位类型
            section: 所属节
            addend: 附加偏移

        Returns:
            创建的重定位条目
        """
        # 根据类型确定大小和 PC 相对属性
        size_map = {
            ELFRelocType.R_X86_64_64: 8,
            ELFRelocType.R_X86_64_32: 4,
            ELFRelocType.R_X86_64_32S: 4,
            ELFRelocType.R_X86_64_PC32: 4,
            ELFRelocType.R_X86_64_16: 2,
            ELFRelocType.R_X86_64_8: 1,
        }

        pc_relative_types = {
            ELFRelocType.R_X86_64_PC32,
            ELFRelocType.R_X86_64_PC16,
            ELFRelocType.R_X86_64_PC8,
            ELFRelocType.R_X86_64_PLT32,
            ELFRelocType.R_X86_64_GOTPCREL,
        }

        return self.add_relocation(
            offset=offset,
            symbol=symbol,
            reloc_type=int(reloc_type),
            section=section,
            addend=addend,
            size=size_map.get(reloc_type, 4),
            is_pc_relative=reloc_type in pc_relative_types,
        )

    def add_macho_relocation(
        self,
        offset: int,
        symbol: Symbol,
        reloc_type: MachORelocType,
        section: str = ".text",
        addend: int = 0,
    ) -> RelocationEntry:
        """
        添加 MachO 重定位

        Args:
            offset: 重定位位置
            symbol: 关联符号
            reloc_type: MachO 重定位类型
            section: 所属节
            addend: 附加偏移

        Returns:
            创建的重定位条目
        """
        size_map = {
            MachORelocType.X86_64_RELOC_UNSIGNED: 8,
            MachORelocType.X86_64_RELOC_SIGNED: 4,
            MachORelocType.X86_64_RELOC_BRANCH: 4,
            MachORelocType.X86_64_RELOC_GOT_LOAD: 4,
        }

        pc_relative_types = {
            MachORelocType.X86_64_RELOC_SIGNED,
            MachORelocType.X86_64_RELOC_BRANCH,
            MachORelocType.X86_64_RELOC_GOT_LOAD,
        }

        return self.add_relocation(
            offset=offset,
            symbol=symbol,
            reloc_type=int(reloc_type),
            section=section,
            addend=addend,
            size=size_map.get(reloc_type, 4),
            is_pc_relative=reloc_type in pc_relative_types,
        )

    # =========================================================================
    # 查询重定位
    # =========================================================================

    def get_relocations_for_section(self, section: str) -> List[RelocationEntry]:
        """获取指定节的所有重定位"""
        return self._entries.get(section, [])

    def get_all_relocations(self) -> List[RelocationEntry]:
        """获取所有重定位"""
        return self._all_entries.copy()

    def get_sections_with_relocations(self) -> List[str]:
        """获取有重定位的所有节"""
        return list(self._entries.keys())

    def count_relocations(self, section: Optional[str] = None) -> int:
        """统计重定位数量"""
        if section:
            return len(self._entries.get(section, []))
        return len(self._all_entries)

    # =========================================================================
    # 重定位编码
    # =========================================================================

    def encode_elf_relocation(self, entry: RelocationEntry, symbol_index: int) -> bytes:
        """
        编码 ELF 重定位条目

        Args:
            entry: 重定位条目
            symbol_index: 符号索引

        Returns:
            编码后的字节
        """
        # ELF64 Rela 格式：r_offset (8) + r_info (8) + r_addend (8)
        r_offset = entry.offset
        r_info = (symbol_index << 32) | entry.type
        r_addend = entry.addend

        return struct.pack("<QQq", r_offset, r_info, r_addend)

    def encode_elf_rel(self, entry: RelocationEntry, symbol_index: int) -> bytes:
        """
        编码 ELF Rel 条目（无 addend）

        Args:
            entry: 重定位条目
            symbol_index: 符号索引

        Returns:
            编码后的字节
        """
        r_offset = entry.offset
        r_info = (symbol_index << 32) | entry.type

        return struct.pack("<QQ", r_offset, r_info)

    def encode_macho_relocation(
        self,
        entry: RelocationEntry,
        symbol_index: int,
        section_index: int,
    ) -> bytes:
        """
        编码 MachO 重定位条目

        Args:
            entry: 重定位条目
            symbol_index: 符号索引
            section_index: 节索引

        Returns:
            编码后的字节
        """
        # MachO relocation_info 结构
        # r_address (4) + r_symbolnum:24 + r_pcrel:1 + r_length:2 + r_extern:1 + r_type:4

        r_address = entry.offset

        # r_info 字段
        r_symbolnum = symbol_index if entry.symbol.is_global else section_index
        r_pcrel = 1 if entry.is_pc_relative else 0
        r_length = {1: 0, 2: 1, 4: 2, 8: 3}.get(entry.size, 2)
        r_extern = 1 if entry.symbol.is_global else 0
        r_type = entry.type

        r_info = r_symbolnum & 0xFFFFFF
        r_info |= r_pcrel << 24
        r_info |= r_length << 25
        r_info |= r_extern << 27
        r_info |= r_type << 28

        return struct.pack("<II", r_address, r_info)

    # =========================================================================
    # 重定位应用
    # =========================================================================

    def apply_relocation(
        self,
        data: bytearray,
        entry: RelocationEntry,
        symbol_address: int,
        section_address: int = 0,
    ) -> None:
        """
        应用重定位

        Args:
            data: 要修改的数据
            entry: 重定位条目
            symbol_address: 符号地址
            section_address: 节地址（用于 PC 相对计算）
        """
        if entry.format == RelocFormat.ELF:
            self._apply_elf_relocation(data, entry, symbol_address, section_address)
        elif entry.format == RelocFormat.MACHO:
            self._apply_macho_relocation(data, entry, symbol_address, section_address)
        else:
            logger.warning(f"Unsupported relocation format: {entry.format}")

    def _apply_elf_relocation(
        self,
        data: bytearray,
        entry: RelocationEntry,
        symbol_address: int,
        section_address: int,
    ) -> None:
        """应用 ELF 重定位"""
        offset = entry.offset
        addend = entry.addend

        # 计算目标值
        if entry.is_pc_relative:
            target = symbol_address + addend - (section_address + offset)
        else:
            target = symbol_address + addend

        # 写入目标值
        if entry.size == 8:
            struct.pack_into("<Q", data, offset, target)
        elif entry.size == 4:
            struct.pack_into("<I", data, offset, target & 0xFFFFFFFF)
        elif entry.size == 2:
            struct.pack_into("<H", data, offset, target & 0xFFFF)
        elif entry.size == 1:
            data[offset] = target & 0xFF

    def _apply_macho_relocation(
        self,
        data: bytearray,
        entry: RelocationEntry,
        symbol_address: int,
        section_address: int,
    ) -> None:
        """应用 MachO 重定位"""
        offset = entry.offset

        # MachO 的 PC 相对地址计算
        if entry.is_pc_relative:
            target = symbol_address - (section_address + offset + entry.size)
        else:
            target = symbol_address

        if entry.size == 8:
            struct.pack_into("<Q", data, offset, target)
        elif entry.size == 4:
            struct.pack_into("<I", data, offset, target & 0xFFFFFFFF)
        elif entry.size == 2:
            struct.pack_into("<H", data, offset, target & 0xFFFF)
        elif entry.size == 1:
            data[offset] = target & 0xFF

    # =========================================================================
    # 工具方法
    # =========================================================================

    def clear(self) -> None:
        """清空所有重定位"""
        self._entries.clear()
        self._all_entries.clear()

    def validate(self) -> List[str]:
        """
        验证重定位

        Returns:
            错误信息列表
        """
        errors = []

        for section, entries in self._entries.items():
            for entry in entries:
                # 检查偏移对齐
                if entry.size == 8 and entry.offset % 8 != 0:
                    errors.append(
                        f"Unaligned 64-bit relocation at {entry.offset:#x} in {section}"
                    )
                elif entry.size == 4 and entry.offset % 4 != 0:
                    errors.append(
                        f"Unaligned 32-bit relocation at {entry.offset:#x} in {section}"
                    )

        return errors

    def __len__(self) -> int:
        """获取重定位数量"""
        return len(self._all_entries)

    def __str__(self) -> str:
        lines = [f"Relocator ({len(self._all_entries)} relocations):"]
        for section, entries in self._entries.items():
            lines.append(f"  {section}: {len(entries)} relocations")
        return "\n".join(lines)


# ============================================================================
# 工厂函数
# ============================================================================


def create_relocator(format: RelocFormat = RelocFormat.ELF) -> Relocator:
    """
    创建重定位管理器

    Args:
        format: 重定位格式

    Returns:
        重定位管理器实例
    """
    return Relocator(format=format)


def get_default_reloc_type_for_arch(arch: str, is_call: bool = False) -> int:
    """
    获取架构的默认重定位类型

    Args:
        arch: 架构名称
        is_call: 是否为调用指令

    Returns:
        重定位类型
    """
    defaults = {
        "x86_64": {
            "call": int(ELFRelocType.R_X86_64_PLT32),
            "data": int(ELFRelocType.R_X86_64_64),
            "pc_rel": int(ELFRelocType.R_X86_64_PC32),
        },
        "aarch64": {
            "call": int(ELFRelocTypeAArch64.R_AARCH64_CALL26),
            "data": int(ELFRelocTypeAArch64.R_AARCH64_ABS64),
            "pc_rel": int(ELFRelocTypeAArch64.R_AARCH64_PREL32),
        },
    }

    arch_defaults = defaults.get(arch.lower(), defaults["x86_64"])
    return arch_defaults["call"] if is_call else arch_defaults["data"]


# ============================================================================
# 兼容层：旧版 relocater.py API 兼容
# ============================================================================


# 兼容枚举：从 RelocFormat 和具体类型派生出兼容的 RelocationType
class _RelocationTypeCompat(Enum):
    """RelocationType 兼容枚举（旧版 API）"""

    # 通用类型
    NONE = auto()
    ABS64 = auto()  # 64 位绝对地址
    ABS32 = auto()  # 32 位绝对地址
    ABS16 = auto()  # 16 位绝对地址
    REL64 = auto()  # 64 位相对地址
    REL32 = auto()  # 32 位相对地址
    REL16 = auto()  # 16 位相对地址

    # x86_64 特定
    X86_64_RELOC_UNSIGNED = auto()
    X86_64_RELOC_SIGNED = auto()
    X86_64_RELOC_BRANCH = auto()
    X86_64_RELOC_GOT_LOAD = auto()
    X86_64_RELOC_GOT = auto()
    X86_64_RELOC_SUBTRACTOR = auto()
    X86_64_RELOC_SIGNED_1 = auto()
    X86_64_RELOC_SIGNED_2 = auto()
    X86_64_RELOC_SIGNED_4 = auto()
    X86_64_RELOC_TLV = auto()

    # AArch64 特定
    AARCH64_RELOC_UNSIGNED = auto()
    AARCH64_RELOC_SUBTRACTOR = auto()
    AARCH64_RELOC_BRANCH26 = auto()
    AARCH64_RELOC_PAGE21 = auto()
    AARCH64_RELOC_PAGEOFF12 = auto()
    AARCH64_RELOC_GOT_LOAD_PAGE21 = auto()
    AARCH64_RELOC_GOT_LOAD_PAGEOFF12 = auto()
    AARCH64_RELOC_POINTER_TO_GOT = auto()
    AARCH64_RELOC_TLVP_LOAD_PAGE21 = auto()
    AARCH64_RELOC_TLVP_LOAD_PAGEOFF12 = auto()
    AARCH64_RELOC_ADDEND = auto()

    # ELF 特定
    R_X86_64_64 = auto()
    R_X86_64_PC32 = auto()
    R_X86_64_GOT32 = auto()
    R_X86_64_PLT32 = auto()
    R_X86_64_COPY = auto()
    R_X86_64_GLOB_DAT = auto()
    R_X86_64_JUMP_SLOT = auto()
    R_X86_64_RELATIVE = auto()
    R_X86_64_GOTPCREL = auto()
    R_X86_64_32 = auto()
    R_X86_64_32S = auto()

    # ARM64 ELF 特定
    R_AARCH64_ABS64 = auto()
    R_AARCH64_ABS32 = auto()
    R_AARCH64_ABS16 = auto()
    R_AARCH64_PREL64 = auto()
    R_AARCH64_PREL32 = auto()
    R_AARCH64_PREL16 = auto()
    R_AARCH64_CALL26 = auto()
    R_AARCH64_JUMP26 = auto()
    R_AARCH64_ADR_PREL_PG_HI21 = auto()
    R_AARCH64_ADR_PREL_PG_HI21_NC = auto()
    R_AARCH64_ADD_ABS_LO12_NC = auto()
    R_AARCH64_LDST8_ABS_LO12_NC = auto()
    R_AARCH64_LDST16_ABS_LO12_NC = auto()
    R_AARCH64_LDST32_ABS_LO12_NC = auto()
    R_AARCH64_LDST64_ABS_LO12_NC = auto()
    R_AARCH64_LDST128_ABS_LO12_NC = auto()

    # WebAssembly 特定
    R_WASM_FUNCTION_INDEX_LEB = auto()
    R_WASM_TABLE_INDEX_SLEB = auto()
    R_WASM_TABLE_INDEX_I32 = auto()
    R_WASM_MEMORY_ADDR_LEB = auto()
    R_WASM_MEMORY_ADDR_SLEB = auto()
    R_WASM_MEMORY_ADDR_I32 = auto()
    R_WASM_TYPE_INDEX_LEB = auto()
    R_WASM_GLOBAL_INDEX_LEB = auto()
    R_WASM_FUNCTION_OFFSET_I32 = auto()
    R_WASM_SECTION_OFFSET_I32 = auto()

    @property
    def is_absolute(self) -> bool:
        """是否为绝对重定位"""
        return self in (
            _RelocationTypeCompat.ABS64,
            _RelocationTypeCompat.ABS32,
            _RelocationTypeCompat.ABS16,
            _RelocationTypeCompat.X86_64_RELOC_UNSIGNED,
            _RelocationTypeCompat.AARCH64_RELOC_UNSIGNED,
            _RelocationTypeCompat.R_X86_64_64,
            _RelocationTypeCompat.R_AARCH64_ABS64,
            _RelocationTypeCompat.R_AARCH64_ABS32,
        )

    @property
    def is_relative(self) -> bool:
        """是否为相对重定位"""
        return self in (
            _RelocationTypeCompat.REL64,
            _RelocationTypeCompat.REL32,
            _RelocationTypeCompat.REL16,
            _RelocationTypeCompat.X86_64_RELOC_SIGNED,
            _RelocationTypeCompat.X86_64_RELOC_BRANCH,
            _RelocationTypeCompat.R_X86_64_PC32,
            _RelocationTypeCompat.R_X86_64_PLT32,
            _RelocationTypeCompat.R_AARCH64_PREL64,
            _RelocationTypeCompat.R_AARCH64_PREL32,
        )

    @property
    def is_pc_relative(self) -> bool:
        """是否为 PC 相对重定位"""
        return self.is_relative

    @property
    def size(self) -> int:
        """获取重定位大小（字节）"""
        size_map = {
            _RelocationTypeCompat.ABS64: 8,
            _RelocationTypeCompat.ABS32: 4,
            _RelocationTypeCompat.ABS16: 2,
            _RelocationTypeCompat.REL64: 8,
            _RelocationTypeCompat.REL32: 4,
            _RelocationTypeCompat.REL16: 2,
            _RelocationTypeCompat.R_X86_64_64: 8,
            _RelocationTypeCompat.R_X86_64_32: 4,
            _RelocationTypeCompat.R_X86_64_32S: 4,
            _RelocationTypeCompat.R_AARCH64_ABS64: 8,
            _RelocationTypeCompat.R_AARCH64_ABS32: 4,
        }
        return size_map.get(self, 4)


# 别名：兼容旧 API
RelocationType = _RelocationTypeCompat


# 兼容的 Relocation dataclass（基于 RelocationEntry）
@dataclass
class _RelocationCompat:
    """
    重定位条目（兼容旧版 Relocation）

    描述一个需要重定位的位置。
    """

    symbol: str  # 符号名
    type: _RelocationTypeCompat  # 重定位类型
    offset: int  # 在节中的偏移
    addend: int = 0  # 附加偏移

    # 位置信息
    section: str = ""  # 所属节名称

    # 解析后的地址
    resolved_address: Optional[int] = None

    def __str__(self) -> str:
        return f"Reloc({self.type.name}, {self.symbol}, +{self.offset}, addend={self.addend})"


# 别名：兼容旧 API
Relocation = _RelocationCompat


# RelocaterError
class RelocaterError(Exception):
    """重定位错误"""

    pass


# 架构特定的 Relocater
class X86_64Relocater(Relocator):
    """x86_64 重定位器（兼容旧 API）"""

    def add_call_relocation(self, symbol, offset):
        """添加函数调用重定位"""
        return self.add_relocation(
            offset=offset,
            symbol=symbol,  # 需要传入兼容的 symbol
            reloc_type=int(ELFRelocType.R_X86_64_PLT32),
            is_pc_relative=True,
        )

    def add_got_relocation(self, symbol, offset):
        """添加 GOT 重定位"""
        return self.add_relocation(
            offset=offset,
            symbol=symbol,
            reloc_type=int(ELFRelocType.R_X86_64_GOTPCREL),
            is_pc_relative=True,
        )

    def add_absolute_relocation(self, symbol, offset):
        """添加绝对地址重定位"""
        return self.add_relocation(
            offset=offset,
            symbol=symbol,
            reloc_type=int(ELFRelocType.R_X86_64_64),
        )


class AArch64Relocater(Relocator):
    """AArch64 重定位器（兼容旧 API）"""

    def add_call_relocation(self, symbol, offset):
        """添加函数调用重定位"""
        return self.add_relocation(
            offset=offset,
            symbol=symbol,
            reloc_type=int(ELFRelocTypeAArch64.R_AARCH64_CALL26),
        )

    def add_page_relocation(self, symbol, offset):
        """添加页面地址重定位（用于 ADRP）"""
        return self.add_relocation(
            offset=offset,
            symbol=symbol,
            reloc_type=int(ELFRelocTypeAArch64.R_AARCH64_ADR_PREL_PG_HI21),
        )

    def add_pageoff_relocation(self, symbol, offset):
        """添加页内偏移重定位（用于 ADD/LD）"""
        return self.add_relocation(
            offset=offset,
            symbol=symbol,
            reloc_type=int(ELFRelocTypeAArch64.R_AARCH64_ADD_ABS_LO12_NC),
        )

    def add_absolute_relocation(self, symbol, offset):
        """添加绝对地址重定位"""
        return self.add_relocation(
            offset=offset,
            symbol=symbol,
            reloc_type=int(ELFRelocTypeAArch64.R_AARCH64_ABS64),
        )


class WasmRelocater(Relocator):
    """WebAssembly 重定位器（兼容旧 API）"""

    def add_function_relocation(self, symbol, offset):
        """添加函数索引重定位"""
        return self.add_relocation(
            offset=offset,
            symbol=symbol,
            reloc_type=int(WasmRelocType.R_WASM_FUNCTION_INDEX_LEB),
        )

    def add_memory_relocation(self, symbol, offset):
        """添加内存地址重定位"""
        return self.add_relocation(
            offset=offset,
            symbol=symbol,
            reloc_type=int(WasmRelocType.R_WASM_MEMORY_ADDR_LEB),
        )

    def add_global_relocation(self, symbol, offset):
        """添加全局变量重定位"""
        return self.add_relocation(
            offset=offset,
            symbol=symbol,
            reloc_type=int(WasmRelocType.R_WASM_GLOBAL_INDEX_LEB),
        )


# 别名：兼容旧 API
Relocater = Relocator


# 工厂函数：兼容旧 API
def create_relocater(target: str) -> Relocator:
    """
    创建重定位器（兼容旧 API）

    Args:
        target: 目标名称

    Returns:
        重定位器实例
    """
    target_map = {
        "x86_64": X86_64Relocater,
        "x86-64": X86_64Relocater,
        "aarch64": AArch64Relocater,
        "arm64": AArch64Relocater,
        "wasm32": WasmRelocater,
        "wasm64": WasmRelocater,
    }

    relocater_class = target_map.get(target.lower(), Relocator)
    return relocater_class()

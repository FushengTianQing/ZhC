# -*- coding: utf-8 -*-
"""
ZhC DWARF .debug_line 节生成器

生成 DWARF 行号表节，建立源码行号与机器码地址的映射。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import struct
import logging

logger = logging.getLogger(__name__)


class LNSOpcode(Enum):
    """行号标准操作码"""

    COPY = 0x01
    ADVANCE_PC = 0x02
    ADVANCE_LINE = 0x03
    SET_FILE = 0x04
    SET_COLUMN = 0x05
    NEGATE_STMT = 0x06
    SET_BASIC_BLOCK = 0x07
    CONST_ADD_PC = 0x08
    FIXED_ADVANCE_PC = 0x09
    SET_PROLOGUE_END = 0x0A
    SET_EPILOGUE_BEGIN = 0x0B
    SET_ISA = 0x0C


class LNEOpcode(Enum):
    """行号扩展操作码"""

    END_SEQUENCE = 0x01
    SET_ADDRESS = 0x02
    DEFINE_FILE = 0x03
    SET_DISCRIMINATOR = 0x04


class DWARFStandardOpcode(Enum):
    """DWARF 标准操作码"""

    DW_LNS_copy = 0x01
    DW_LNS_advance_pc = 0x02
    DW_LNS_advance_line = 0x03
    DW_LNS_set_file = 0x04
    DW_LNS_set_column = 0x05
    DW_LNS_negate_stmt = 0x06
    DW_LNS_set_basic_block = 0x07
    DW_LNS_const_add_pc = 0x08
    DW_LNS_fixed_advance_pc = 0x09
    DW_LNS_set_prologue_end = 0x0A
    DW_LNS_set_epilogue_begin = 0x0B
    DW_LNS_set_isa = 0x0C


@dataclass
class FileEntry:
    """文件条目"""

    name: str  # 文件名
    directory_index: int = 0  # 目录索引
    modification_time: int = 0  # 修改时间
    file_size: int = 0  # 文件大小


@dataclass
class LineEntry:
    """行号表条目"""

    address: int  # 地址
    file_index: int  # 文件索引
    line: int  # 行号
    column: int = 0  # 列号
    is_stmt: bool = False  # 是否为语句起始
    is_basic_block: bool = False  # 是否为基本块起始
    is_prologue_end: bool = False  # 是否为序言结束
    is_epilogue_begin: bool = False  # 是否为尾声开始
    discriminator: int = 0  # 判别器
    isa: int = 0  # ISA 编号


class LineNumberProgramBuilder:
    """
    行号程序构建器

    构建 DWARF 行号程序。
    """

    def __init__(self, minimum_instruction_length: int = 1):
        self.minimum_instruction_length = minimum_instruction_length
        self.maximum_ops_per_instruction: int = 1
        self.default_is_stmt: bool = True
        self.line_base: int = -5
        self.line_range: int = 14
        self.opcode_base: int = 13

        # 状态
        self.address: int = 0
        self.op_index: int = 0
        self.file: int = 1
        self.line: int = 1
        self.column: int = 0
        self.is_stmt: bool = self.default_is_stmt
        self.basic_block: bool = False
        self._end_sequence_flag: bool = False
        self.prologue_end: bool = False
        self.epilogue_begin: bool = False
        self.isa: int = 0
        self.discriminator: int = 0

        # 文件表
        self.files: List[FileEntry] = []
        self._file_index: Dict[str, int] = {}

        # 目录表
        self.directories: List[str] = []
        self._dir_index: Dict[str, int] = {}

    def add_directory(self, path: str) -> int:
        """添加目录，返回目录索引"""
        if path not in self._dir_index:
            self.directories.append(path)
            self._dir_index[path] = len(self.directories)
        return self._dir_index[path]

    def add_file(self, name: str, directory: str = "") -> int:
        """添加文件，返回文件索引"""
        if name not in self._file_index:
            dir_index = self.add_directory(directory) if directory else 0
            entry = FileEntry(name=name, directory_index=dir_index)
            self.files.append(entry)
            self._file_index[name] = len(self.files)
        return self._file_index[name]

    def set_address(self, address: int) -> None:
        """设置当前地址"""
        self.address = address

    def advance_pc(self, op_advance: int) -> None:
        """推进地址"""
        self.address += op_advance * self.minimum_instruction_length

    def advance_line(self, delta: int) -> None:
        """推进行号"""
        self.line += delta

    def set_file(self, file_index: int) -> None:
        """设置文件"""
        self.file = file_index

    def set_column(self, column: int) -> None:
        """设置列号"""
        self.column = column

    def set_stmt(self, is_stmt: bool) -> None:
        """设置语句标志"""
        self.is_stmt = is_stmt

    def set_basic_block(self) -> None:
        """设置基本块开始"""
        self.basic_block = True

    def set_prologue_end(self) -> None:
        """设置序言结束"""
        self.prologue_end = True

    def set_epilogue_begin(self) -> None:
        """设置尾声开始"""
        self.epilogue_begin = True

    def set_isa(self, isa: int) -> None:
        """设置 ISA"""
        self.isa = isa

    def set_discriminator(self, discriminator: int) -> None:
        """设置判别器"""
        self.discriminator = discriminator

    def copy(self) -> None:
        """复制当前状态（生成行号条目）"""
        self.basic_block = False
        self.prologue_end = False
        self.epilogue_begin = False
        self.discriminator = 0

    def end_sequence(self) -> None:
        """结束序列"""
        self._end_sequence_flag = True

    def reset_sequence(self) -> None:
        """重置序列"""
        self.address = 0
        self.op_index = 0
        self.file = 1
        self.line = 1
        self.column = 0
        self.is_stmt = self.default_is_stmt
        self.basic_block = False
        self._end_sequence_flag = False
        self.prologue_end = False
        self.epilogue_begin = False
        self.isa = 0
        self.discriminator = 0


class DebugLineSection:
    """
    .debug_line 节生成器

    生成 DWARF 行号表节。
    """

    def __init__(self):
        self.programs: List[LineNumberProgramBuilder] = []
        self._current_program: Optional[LineNumberProgramBuilder] = None

    def begin_program(
        self,
        source_file: str,
        source_directory: str = "",
        minimum_instruction_length: int = 1,
    ) -> LineNumberProgramBuilder:
        """开始行号程序"""
        program = LineNumberProgramBuilder(minimum_instruction_length)
        if source_file:
            program.add_file(source_file, source_directory)
        self.programs.append(program)
        self._current_program = program
        return program

    def end_program(self) -> Optional[LineNumberProgramBuilder]:
        """结束行号程序"""
        if self._current_program:
            self._current_program.end_sequence()
        return self._current_program

    def get_current_program(self) -> Optional[LineNumberProgramBuilder]:
        """获取当前程序"""
        return self._current_program

    def build(self) -> bytes:
        """
        构建 .debug_line 节数据

        Returns:
            节数据字节
        """
        data = bytearray()

        for program in self.programs:
            data.extend(self._build_program(program))

        return bytes(data)

    def _build_program(self, program: LineNumberProgramBuilder) -> bytes:
        """构建单个行号程序"""
        data = bytearray()

        # 行号表头部
        data.extend(self._encode_header(program))

        # 行号程序
        data.extend(self._encode_program(program))

        return bytes(data)

    def _encode_header(self, program: LineNumberProgramBuilder) -> bytes:
        """编码行号表头部"""
        data = bytearray()

        # unit_length (placeholder)
        data.extend(struct.pack("<I", 0))

        # version
        data.extend(struct.pack("<H", 4))  # DWARF 4

        # header_length
        header_length = self._calculate_header_length(program)
        data.extend(struct.pack("<I", header_length))

        # minimum_instruction_length
        data.extend(struct.pack("<B", program.minimum_instruction_length))

        # maximum_operations_per_instruction (DWARF 4+)
        data.extend(struct.pack("<B", program.maximum_ops_per_instruction))

        # default_is_stmt
        data.extend(struct.pack("<B", 1 if program.default_is_stmt else 0))

        # line_base
        data.extend(struct.pack("<b", program.line_base))

        # line_range
        data.extend(struct.pack("<B", program.line_range))

        # opcode_base
        data.extend(struct.pack("<B", program.opcode_base))

        # standard_opcode_lengths
        standard_lengths = [0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1]
        for length in standard_lengths:
            data.extend(struct.pack("<B", length))

        # include_directories
        for directory in program.directories:
            data.extend(directory.encode("utf-8"))
            data.append(0)
        data.append(0)  # 目录表结束

        # file_names
        for file_entry in program.files:
            data.extend(file_entry.name.encode("utf-8"))
            data.append(0)
            data.extend(self._encode_uleb128(file_entry.directory_index))
            data.extend(self._encode_uleb128(file_entry.modification_time))
            data.extend(self._encode_uleb128(file_entry.file_size))
        data.append(0)  # 文件表结束

        return bytes(data)

    def _calculate_header_length(self, program: LineNumberProgramBuilder) -> int:
        """计算头部长度"""
        length = 0
        length += 2  # version
        length += 4  # header_length
        length += 1  # minimum_instruction_length
        length += 1  # maximum_operations_per_instruction
        length += 1  # default_is_stmt
        length += 1  # line_base
        length += 1  # line_range
        length += 1  # opcode_base
        length += 13  # standard_opcode_lengths

        # include_directories
        for directory in program.directories:
            length += len(directory) + 1
        length += 1  # end marker

        # file_names
        for file_entry in program.files:
            length += len(file_entry.name) + 1
            length += 3  # directory_index, mtime, size (ULEB128)
        length += 1  # end marker

        return length

    def _encode_program(self, program: LineNumberProgramBuilder) -> bytes:
        """编码行号程序"""
        data = bytearray()

        # 简化实现：生成基本的行号表条目
        # 实际实现应该根据行号变化生成操作码

        # DW_LNE_set_address
        data.append(0)  # 扩展操作码
        data.extend(self._encode_uleb128(9))  # 操作码长度
        data.extend(self._encode_uleb128(LNEOpcode.SET_ADDRESS.value))
        data.extend(struct.pack("<Q", 0))  # 地址

        # DW_LNS_set_prologue_end
        data.append(LNSOpcode.SET_PROLOGUE_END.value)

        # DW_LNS_copy
        data.append(LNSOpcode.COPY.value)

        # DW_LNE_end_sequence
        data.append(0)  # 扩展操作码
        data.extend(self._encode_uleb128(1))  # 操作码长度
        data.extend(self._encode_uleb128(LNEOpcode.END_SEQUENCE.value))

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

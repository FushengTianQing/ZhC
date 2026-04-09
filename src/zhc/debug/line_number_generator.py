# -*- coding: utf-8 -*-
"""
ZhC 行号表生成器

生成 DWARF 行号表，用于源码级调试。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class LineTableEntry:
    """
    行号表条目

    表示地址到源码位置的映射。
    """

    address: int  # 地址
    file_index: int  # 文件索引
    line: int  # 行号
    column: int = 0  # 列号
    discriminator: int = 0  # 判别器
    is_stmt: bool = False  # 是否为语句起始
    is_basic_block: bool = False  # 是否为基本块起始
    is_prologue_end: bool = False  # 是否为序言结束
    is_epilogue_begin: bool = False  # 是否为尾声开始
    isa: int = 0  # ISA 编号
    is_return: bool = False  # 是否为函数返回

    def __repr__(self) -> str:
        return f"LineTableEntry(addr=0x{self.address:x}, file={self.file_index}, line={self.line})"


@dataclass
class LineTable:
    """
    行号表

    包含文件信息和行号表条目。
    """

    file_names: List[str] = field(default_factory=list)  # 文件名列表
    include_directories: List[str] = field(default_factory=list)  # 包含目录
    entries: List[LineTableEntry] = field(default_factory=list)  # 条目列表

    def add_file(self, path: str) -> int:
        """添加文件，返回文件索引"""
        if path not in self.file_names:
            self.file_names.append(path)
        return self.file_names.index(path) + 1  # 索引从 1 开始

    def add_entry(self, entry: LineTableEntry) -> None:
        """添加行号表条目"""
        self.entries.append(entry)

    def get_line_for_address(self, address: int) -> Optional[LineTableEntry]:
        """根据地址获取行号"""
        # 二分查找
        left, right = 0, len(self.entries) - 1
        result = None

        while left <= right:
            mid = (left + right) // 2
            if self.entries[mid].address <= address:
                result = self.entries[mid]
                left = mid + 1
            else:
                right = mid - 1

        return result

    def get_address_for_line(self, file_index: int, line: int) -> Optional[int]:
        """根据文件索引和行号获取地址"""
        for entry in self.entries:
            if entry.file_index == file_index and entry.line == line:
                return entry.address
        return None


class LineNumberGenerator:
    """
    行号表生成器

    从 IR 或 AST 生成 DWARF 行号表。
    """

    def __init__(self):
        self.line_tables: Dict[str, LineTable] = {}  # 编译单元 -> 行号表

    def generate(
        self,
        compile_unit_name: str,
        instructions: List[Dict],
    ) -> LineTable:
        """
        生成行号表

        Args:
            compile_unit_name: 编译单元名称
            instructions: 指令列表，每条指令包含 address, file, line, column

        Returns:
            生成的行号表
        """
        line_table = LineTable()

        # 添加编译单元文件
        line_table.add_file(compile_unit_name)

        # 处理指令
        current_address = 0
        current_file = 1
        current_line = 1
        current_column = 0

        for inst in instructions:
            addr = inst.get("address", current_address)
            file_idx = inst.get("file", current_file)
            line_num = inst.get("line", current_line)
            column = inst.get("column", current_column)

            # 只在新行时添加条目
            if line_num != current_line or file_idx != current_file:
                entry = LineTableEntry(
                    address=addr,
                    file_index=file_idx,
                    line=line_num,
                    column=column,
                    is_stmt=True,  # 简化：所有条目都是语句起始
                )
                line_table.add_entry(entry)

                current_line = line_num
                current_file = file_idx
                current_column = column

            current_address = addr + inst.get("size", 4)

        self.line_tables[compile_unit_name] = line_table
        return line_table

    def add_source_line(
        self,
        compile_unit_name: str,
        address: int,
        file_index: int,
        line: int,
        column: int = 0,
    ) -> LineTableEntry:
        """
        添加源码行信息

        Args:
            compile_unit_name: 编译单元名称
            address: 地址
            file_index: 文件索引
            line: 行号
            column: 列号

        Returns:
            创建的行号表条目
        """
        if compile_unit_name not in self.line_tables:
            self.line_tables[compile_unit_name] = LineTable()
            self.line_tables[compile_unit_name].add_file(compile_unit_name)

        line_table = self.line_tables[compile_unit_name]

        entry = LineTableEntry(
            address=address,
            file_index=file_index,
            line=line,
            column=column,
        )

        line_table.add_entry(entry)
        return entry

    def build_line_table_program(self, line_table: LineTable) -> bytes:
        """
        构建行号表程序（DWARF 压缩格式）

        Args:
            line_table: 行号表

        Returns:
            压缩后的数据
        """
        # 简化的实现：生成基本的行号表程序
        data = bytearray()

        # 文件名表头
        data.extend(self._encode_uleb128(len(line_table.file_names)))
        for filename in line_table.file_names:
            data.extend(filename.encode("utf-8"))
            data.append(0)  # 目录索引
            data.extend(self._encode_uleb128(0))  # 修改时间
            data.extend(self._encode_uleb128(0))  # 长度

        # 目录表头
        data.extend(self._encode_uleb128(len(line_table.include_directories)))
        for directory in line_table.include_directories:
            data.extend(directory.encode("utf-8"))
            data.append(0)

        # 行号表条目
        data.extend(self._encode_uleb128(len(line_table.entries)))
        for entry in line_table.entries:
            data.extend(self._encode_address(entry.address))
            data.extend(self._encode_uleb128(entry.file_index))
            data.extend(self._encode_uleb128(entry.line))
            data.extend(self._encode_uleb128(entry.column))

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

    def _encode_address(self, addr: int) -> bytes:
        """编码地址（简化为 8 字节）"""
        return addr.to_bytes(8, byteorder="little")

    def get_line_table(self, compile_unit_name: str) -> Optional[LineTable]:
        """获取指定编译单元的行号表"""
        return self.line_tables.get(compile_unit_name)

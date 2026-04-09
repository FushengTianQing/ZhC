# -*- coding: utf-8 -*-
"""
ZhC DWARF .debug_str 节生成器

生成 DWARF 字符串表节，存储调试信息中的字符串常量。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class StringEntry:
    """字符串条目"""

    value: str  # 字符串值
    offset: int = 0  # 在字符串表中的偏移
    is_deduplicated: bool = False  # 是否已去重


class StringPool:
    """
    字符串池

    管理调试信息中的字符串，支持去重和偏移管理。
    """

    def __init__(self):
        self.entries: List[StringEntry] = []
        self._string_map: Dict[str, int] = {}  # 字符串 -> 偏移
        self._current_offset: int = 0

    def add_string(self, value: str) -> int:
        """
        添加字符串

        Args:
            value: 字符串值

        Returns:
            字符串在表中的偏移
        """
        if value in self._string_map:
            return self._string_map[value]

        offset = self._current_offset
        entry = StringEntry(value=value, offset=offset)
        self.entries.append(entry)
        self._string_map[value] = offset
        self._current_offset += len(value.encode("utf-8")) + 1  # +1 for null terminator

        return offset

    def get_offset(self, value: str) -> Optional[int]:
        """获取字符串偏移"""
        return self._string_map.get(value)

    def has_string(self, value: str) -> bool:
        """检查字符串是否存在"""
        return value in self._string_map

    def get_or_add(self, value: str) -> int:
        """获取或添加字符串"""
        if value in self._string_map:
            return self._string_map[value]
        return self.add_string(value)

    def get_all_strings(self) -> List[str]:
        """获取所有字符串"""
        return [entry.value for entry in self.entries]

    def get_total_size(self) -> int:
        """获取字符串表总大小"""
        return self._current_offset

    def clear(self) -> None:
        """清空字符串池"""
        self.entries.clear()
        self._string_map.clear()
        self._current_offset = 0


class DebugStrSection:
    """
    .debug_str 节生成器

    生成 DWARF 字符串表节。
    """

    def __init__(self):
        self.string_pool = StringPool()

    def add_string(self, value: str) -> int:
        """
        添加字符串

        Args:
            value: 字符串值

        Returns:
            字符串在表中的偏移
        """
        return self.string_pool.add_string(value)

    def get_offset(self, value: str) -> Optional[int]:
        """获取字符串偏移"""
        return self.string_pool.get_offset(value)

    def has_string(self, value: str) -> bool:
        """检查字符串是否存在"""
        return self.string_pool.has_string(value)

    def get_or_add(self, value: str) -> int:
        """获取或添加字符串"""
        return self.string_pool.get_or_add(value)

    def build(self) -> bytes:
        """
        构建 .debug_str 节数据

        Returns:
            节数据字节
        """
        data = bytearray()

        for entry in self.string_pool.entries:
            # 编码字符串
            encoded = entry.value.encode("utf-8")
            data.extend(encoded)
            data.append(0)  # null 终止符

        return bytes(data)

    def get_size(self) -> int:
        """获取节大小"""
        return self.string_pool.get_total_size()

    def export_strings(self) -> Dict[str, int]:
        """导出字符串映射"""
        return self.string_pool._string_map.copy()

    def add_common_strings(self) -> None:
        """添加常用字符串"""
        common_strings = [
            # ZhC 类型名
            "整数型",
            "短整数型",
            "长整数型",
            "字节型",
            "浮点型",
            "双精度型",
            "字符型",
            "宽字符型",
            "布尔型",
            "空型",
            # C 风格类型名
            "int",
            "short",
            "long",
            "byte",
            "float",
            "double",
            "char",
            "wchar_t",
            "bool",
            "void",
            # 编译器信息
            "ZhC Compiler",
            "ZhC",
            # 常用标识符
            "main",
            "return",
            "argc",
            "argv",
            "envp",
            # 文件扩展名
            ".zhc",
            ".c",
            ".h",
        ]

        for s in common_strings:
            self.add_string(s)

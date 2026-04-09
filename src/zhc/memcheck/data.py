"""
内存分析数据结构
"""

from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum
import time


class MemOpType(Enum):
    """内存操作类型"""

    ALLOC = "alloc"
    FREE = "free"
    REALLOC = "realloc"


@dataclass
class MemBlock:
    """内存块信息"""

    ptr: int
    size: int
    file: str
    line: int
    func: str
    alloc_time: int
    alloc_id: int

    @property
    def ptr_address(self) -> str:
        """返回指针地址字符串"""
        return f"0x{self.ptr:016x}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "ptr": self.ptr,
            "ptr_address": self.ptr_address,
            "size": self.size,
            "size_human": self._format_size(self.size),
            "file": self.file,
            "line": self.line,
            "func": self.func,
            "alloc_time": self.alloc_time,
            "alloc_id": self.alloc_id,
        }

    @staticmethod
    def _format_size(size: int) -> str:
        """格式化大小"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"


@dataclass
class MemOpRecord:
    """内存操作记录"""

    op_type: MemOpType
    ptr: int
    size: int
    file: str
    line: int
    func: str
    timestamp: int
    alloc_id: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "op_type": self.op_type.value,
            "ptr": self.ptr,
            "ptr_address": f"0x{self.ptr:016x}" if self.ptr else "null",
            "size": self.size,
            "file": self.file,
            "line": self.line,
            "func": self.func,
            "timestamp": self.timestamp,
            "alloc_id": self.alloc_id,
        }


@dataclass
class MemStats:
    """内存统计信息"""

    total_alloc_bytes: int = 0
    total_free_bytes: int = 0
    current_used_bytes: int = 0
    peak_used_bytes: int = 0
    alloc_count: int = 0
    free_count: int = 0
    leak_count: int = 0
    leak_bytes: int = 0
    invalid_free_count: int = 0
    double_free_count: int = 0

    @property
    def current_used(self) -> str:
        """当前使用（格式化）"""
        return self._format_size(self.current_used_bytes)

    @property
    def peak_used(self) -> str:
        """峰值使用（格式化）"""
        return self._format_size(self.peak_used_bytes)

    @property
    def total_alloc(self) -> str:
        """总分配（格式化）"""
        return self._format_size(self.total_alloc_bytes)

    @property
    def total_free(self) -> str:
        """总释放（格式化）"""
        return self._format_size(self.total_free_bytes)

    @property
    def leak_size(self) -> str:
        """泄漏大小（格式化）"""
        return self._format_size(self.leak_bytes)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_alloc_bytes": self.total_alloc_bytes,
            "total_free_bytes": self.total_free_bytes,
            "current_used_bytes": self.current_used_bytes,
            "peak_used_bytes": self.peak_used_bytes,
            "alloc_count": self.alloc_count,
            "free_count": self.free_count,
            "leak_count": self.leak_count,
            "leak_bytes": self.leak_bytes,
            "invalid_free_count": self.invalid_free_count,
            "double_free_count": self.double_free_count,
            "current_used": self.current_used,
            "peak_used": self.peak_used,
        }

    @staticmethod
    def _format_size(size: int) -> str:
        """格式化大小"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"


@dataclass
class AllocSite:
    """分配源统计"""

    file: str
    line: int
    func: str
    alloc_count: int = 0
    total_bytes: int = 0
    current_bytes: int = 0

    @property
    def location(self) -> str:
        """返回位置字符串"""
        return f"{self.file}:{self.line}"

    @property
    def current(self) -> str:
        """当前大小（格式化）"""
        return self._format_size(self.current_bytes)

    @property
    def total(self) -> str:
        """总大小（格式化）"""
        return self._format_size(self.total_bytes)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "file": self.file,
            "line": self.line,
            "func": self.func,
            "location": self.location,
            "alloc_count": self.alloc_count,
            "total_bytes": self.total_bytes,
            "current_bytes": self.current_bytes,
            "current": self.current,
            "total": self.total,
        }

    @staticmethod
    def _format_size(size: int) -> str:
        """格式化大小"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"


def get_time_ns() -> int:
    """获取当前时间（纳秒）"""
    return time.perf_counter_ns()

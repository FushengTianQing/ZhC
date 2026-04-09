"""
性能剖析数据结构
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import time


class ProfileEventType(Enum):
    """剖析事件类型"""

    ENTER = "enter"
    EXIT = "exit"


@dataclass
class FunctionProfile:
    """函数剖析记录"""

    name: str
    call_count: int = 0
    total_time_ns: int = 0
    min_time_ns: int = 0
    max_time_ns: int = 0
    last_start_time_ns: int = 0
    call_depth: int = 0
    children: List[str] = field(default_factory=list)

    @property
    def avg_time_ns(self) -> float:
        """平均执行时间（纳秒）"""
        if self.call_count == 0:
            return 0.0
        return self.total_time_ns / self.call_count

    @property
    def total_time_ms(self) -> float:
        """总执行时间（毫秒）"""
        return self.total_time_ns / 1_000_000

    @property
    def avg_time_ms(self) -> float:
        """平均执行时间（毫秒）"""
        return self.avg_time_ns / 1_000_000

    @property
    def total_time_s(self) -> float:
        """总执行时间（秒）"""
        return self.total_time_ns / 1_000_000_000

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "call_count": self.call_count,
            "total_time_ns": self.total_time_ns,
            "total_time_ms": self.total_time_ms,
            "total_time_s": self.total_time_s,
            "min_time_ns": self.min_time_ns,
            "max_time_ns": self.max_time_ns,
            "avg_time_ns": self.avg_time_ns,
            "avg_time_ms": self.avg_time_ms,
            "call_depth": self.call_depth,
            "children": self.children,
        }


@dataclass
class CallRelation:
    """调用关系记录"""

    caller: str
    callee: str
    call_count: int = 0
    total_time_ns: int = 0

    @property
    def avg_time_ns(self) -> float:
        """平均执行时间（纳秒）"""
        if self.call_count == 0:
            return 0.0
        return self.total_time_ns / self.call_count

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "caller": self.caller,
            "callee": self.callee,
            "call_count": self.call_count,
            "total_time_ns": self.total_time_ns,
            "avg_time_ns": self.avg_time_ns,
        }


@dataclass
class ProfilerStats:
    """剖析器统计信息"""

    total_calls: int = 0
    total_time_ns: int = 0
    function_count: int = 0
    relation_count: int = 0
    max_depth: int = 0
    start_time_ns: int = 0
    end_time_ns: int = 0

    @property
    def elapsed_ns(self) -> int:
        """剖析耗时（纳秒）"""
        return self.end_time_ns - self.start_time_ns

    @property
    def elapsed_ms(self) -> float:
        """剖析耗时（毫秒）"""
        return self.elapsed_ns / 1_000_000

    @property
    def elapsed_s(self) -> float:
        """剖析耗时（秒）"""
        return self.elapsed_ns / 1_000_000_000

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_calls": self.total_calls,
            "total_time_ns": self.total_time_ns,
            "function_count": self.function_count,
            "relation_count": self.relation_count,
            "max_depth": self.max_depth,
            "elapsed_ns": self.elapsed_ns,
            "elapsed_ms": self.elapsed_ms,
            "elapsed_s": self.elapsed_s,
        }


@dataclass
class ProfilerConfig:
    """剖析器配置"""

    max_functions: int = 1000
    max_relations: int = 2000
    track_call_graph: bool = True
    track_memory: bool = False
    output_file: Optional[str] = None
    min_time_ns: int = 1000  # 最小记录时间（1微秒）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "max_functions": self.max_functions,
            "max_relations": self.max_relations,
            "track_call_graph": self.track_call_graph,
            "track_memory": self.track_memory,
            "output_file": self.output_file,
            "min_time_ns": self.min_time_ns,
        }


@dataclass
class ProfileEvent:
    """剖析事件"""

    timestamp_ns: int
    event_type: ProfileEventType
    function_name: str
    call_depth: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp_ns": self.timestamp_ns,
            "event_type": self.event_type.value,
            "function_name": self.function_name,
            "call_depth": self.call_depth,
        }


def get_time_ns() -> int:
    """获取当前时间（纳秒）"""
    return time.perf_counter_ns()

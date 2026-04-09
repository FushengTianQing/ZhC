"""
断点引擎

提供断点管理的核心功能：
- 源码断点设置
- 条件断点
- 监视点
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .breakpoint_type import BreakpointType
from .line_number_generator import LineNumberGenerator


class WatchType(Enum):
    """监视类型"""

    WRITE = "write"
    READ = "read"
    ACCESS = "access"


@dataclass
class BreakpointHit:
    """断点命中信息"""

    breakpoint_id: int
    thread_id: int
    pc: int
    hit_count: int
    timestamp: float


class BreakpointEngine:
    """断点引擎"""

    def __init__(self, line_generator: Optional[LineNumberGenerator] = None):
        self._breakpoints: Dict[int, "BreakpointInfo"] = {}
        self._next_id: int = 1
        self._watchpoints: Dict[int, "WatchpointInfo"] = {}
        self._watchpoint_id_base: int = 10000
        self._line_generator = line_generator or LineNumberGenerator()
        self._address_to_breakpoint: Dict[int, int] = {}
        self._callbacks: Dict[int, List[Callable]] = {}
        self._ignore_counts: Dict[int, int] = {}
        self._conditions: Dict[int, str] = {}

    def set_source_breakpoint(
        self, file_path: str, line: int, column: Optional[int] = None
    ) -> int:
        """设置源码断点

        Args:
            file_path: 源文件路径
            line: 行号
            column: 列号（可选）

        Returns:
            断点 ID
        """
        # 查找地址
        address = self._lookup_address(file_path, line, column)
        if address is None:
            raise ValueError(f"Cannot find address for {file_path}:{line}")

        breakpoint_id = self._next_id
        self._next_id += 1

        self._breakpoints[breakpoint_id] = BreakpointInfo(
            id=breakpoint_id,
            type=BreakpointType.SOURCE_LINE,
            file_path=file_path,
            line=line,
            column=column,
            address=address,
            enabled=True,
        )

        self._address_to_breakpoint[address] = breakpoint_id

        return breakpoint_id

    def set_function_breakpoint(
        self, function_name: str, file_path: Optional[str] = None
    ) -> int:
        """设置函数断点

        Args:
            function_name: 函数名
            file_path: 文件路径（可选，用于区分重载函数）

        Returns:
            断点 ID
        """
        # 从 DWARF 信息中查找函数地址
        address = self._lookup_function_address(function_name, file_path)
        if address is None:
            raise ValueError(f"Cannot find function: {function_name}")

        breakpoint_id = self._next_id
        self._next_id += 1

        self._breakpoints[breakpoint_id] = BreakpointInfo(
            id=breakpoint_id,
            type=BreakpointType.FUNCTION,
            function_name=function_name,
            address=address,
            enabled=True,
        )

        self._address_to_breakpoint[address] = breakpoint_id

        return breakpoint_id

    def set_address_breakpoint(self, address: int) -> int:
        """设置地址断点

        Args:
            address: 目标地址

        Returns:
            断点 ID
        """
        breakpoint_id = self._next_id
        self._next_id += 1

        self._breakpoints[breakpoint_id] = BreakpointInfo(
            id=breakpoint_id, type=BreakpointType.ADDRESS, address=address, enabled=True
        )

        self._address_to_breakpoint[address] = breakpoint_id

        return breakpoint_id

    def set_watchpoint(
        self,
        variable_name: str,
        watch_type: WatchType,
        frame_context: Optional[Any] = None,
    ) -> int:
        """设置监视点

        Args:
            variable_name: 变量名
            watch_type: 监视类型
            frame_context: 帧上下文（用于获取变量地址）

        Returns:
            监视点 ID
        """
        # 获取变量地址
        var_addr = self._get_variable_address(variable_name, frame_context)
        if var_addr is None:
            raise ValueError(f"Cannot find variable: {variable_name}")

        watchpoint_id = self._watchpoint_id_base + len(self._watchpoints)

        self._watchpoints[watchpoint_id] = WatchpointInfo(
            id=watchpoint_id,
            variable_name=variable_name,
            watch_type=watch_type,
            address=var_addr,
            enabled=True,
        )

        return watchpoint_id

    def set_condition(self, breakpoint_id: int, condition: str) -> None:
        """设置断点条件

        Args:
            breakpoint_id: 断点 ID
            condition: 条件表达式
        """
        if breakpoint_id not in self._breakpoints:
            raise ValueError(f"Breakpoint {breakpoint_id} not found")

        self._conditions[breakpoint_id] = condition

    def set_ignore_count(self, breakpoint_id: int, count: int) -> None:
        """设置忽略计数

        Args:
            breakpoint_id: 断点 ID
            count: 忽略次数
        """
        if breakpoint_id not in self._breakpoints:
            raise ValueError(f"Breakpoint {breakpoint_id} not found")

        self._ignore_counts[breakpoint_id] = count

    def delete_breakpoint(self, breakpoint_id: int) -> bool:
        """删除断点

        Args:
            breakpoint_id: 断点 ID

        Returns:
            是否成功删除
        """
        if breakpoint_id in self._breakpoints:
            bp = self._breakpoints[breakpoint_id]
            if bp.address in self._address_to_breakpoint:
                del self._address_to_breakpoint[bp.address]
            del self._breakpoints[breakpoint_id]

            # 清理相关数据
            self._conditions.pop(breakpoint_id, None)
            self._ignore_counts.pop(breakpoint_id, None)
            self._callbacks.pop(breakpoint_id, None)

            return True

        return False

    def delete_watchpoint(self, watchpoint_id: int) -> bool:
        """删除监视点"""
        if watchpoint_id in self._watchpoints:
            del self._watchpoints[watchpoint_id]
            return True
        return False

    def enable_breakpoint(self, breakpoint_id: int) -> bool:
        """启用断点"""
        if breakpoint_id in self._breakpoints:
            self._breakpoints[breakpoint_id].enabled = True
            return True
        return False

    def disable_breakpoint(self, breakpoint_id: int) -> bool:
        """禁用断点"""
        if breakpoint_id in self._breakpoints:
            self._breakpoints[breakpoint_id].enabled = False
            return True
        return False

    def register_callback(
        self, breakpoint_id: int, callback: Callable[[BreakpointHit], None]
    ) -> None:
        """注册断点回调"""
        if breakpoint_id not in self._callbacks:
            self._callbacks[breakpoint_id] = []
        self._callbacks[breakpoint_id].append(callback)

    def check_breakpoint(
        self, address: int, thread_id: int, hit_count: int, timestamp: float
    ) -> Optional[BreakpointHit]:
        """检查断点是否命中

        Args:
            address: 当前地址
            thread_id: 线程 ID
            hit_count: 命中计数
            timestamp: 时间戳

        Returns:
            断点命中信息，如果未命中返回 None
        """
        breakpoint_id = self._address_to_breakpoint.get(address)
        if breakpoint_id is None:
            return None

        bp = self._breakpoints[breakpoint_id]
        if not bp.enabled:
            return None

        # 检查忽略计数
        ignore_count = self._ignore_counts.get(breakpoint_id, 0)
        if ignore_count > 0:
            self._ignore_counts[breakpoint_id] = ignore_count - 1
            return None

        # 检查条件
        condition = self._conditions.get(breakpoint_id)
        if condition:
            # 条件评估需要实际调试器支持
            # 这里简化处理
            pass

        # 触发回调
        hit = BreakpointHit(
            breakpoint_id=breakpoint_id,
            thread_id=thread_id,
            pc=address,
            hit_count=hit_count + 1,
            timestamp=timestamp,
        )

        if breakpoint_id in self._callbacks:
            for callback in self._callbacks[breakpoint_id]:
                callback(hit)

        return hit

    def get_breakpoint_info(self, breakpoint_id: int) -> Optional["BreakpointInfo"]:
        """获取断点信息"""
        return self._breakpoints.get(breakpoint_id)

    def get_all_breakpoints(self) -> List["BreakpointInfo"]:
        """获取所有断点"""
        return list(self._breakpoints.values())

    def get_all_watchpoints(self) -> List["WatchpointInfo"]:
        """获取所有监视点"""
        return list(self._watchpoints.values())

    def _lookup_address(
        self, file_path: str, line: int, column: Optional[int] = None
    ) -> Optional[int]:
        """查找源码位置对应的地址"""
        # 使用行号表查找地址
        return self._line_generator.get_address_for_line(file_path, line, column)

    def _lookup_function_address(
        self, function_name: str, file_path: Optional[str] = None
    ) -> Optional[int]:
        """查找函数对应的地址"""
        # 需要从 DWARF 信息中查询
        # 这里简化处理
        return None

    def _get_variable_address(
        self, variable_name: str, frame_context: Optional[Any] = None
    ) -> Optional[int]:
        """获取变量地址"""
        # 需要从调试上下文获取
        # 这里简化处理
        return None


@dataclass
class BreakpointInfo:
    """断点信息"""

    id: int
    type: "BreakpointType"
    address: int
    enabled: bool = True
    file_path: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    function_name: Optional[str] = None


@dataclass
class WatchpointInfo:
    """监视点信息"""

    id: int
    variable_name: str
    watch_type: WatchType
    address: int
    size: int = 8
    enabled: bool = True

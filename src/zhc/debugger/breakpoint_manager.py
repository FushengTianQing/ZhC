"""
断点管理器

提供完整的断点管理功能：
- 源码行断点
- 函数断点
- 条件断点
- 监视点
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class BreakpointType(Enum):
    """断点类型"""

    SOURCE_LINE = "source_line"  # 源码行断点
    FUNCTION = "function"  # 函数断点
    ADDRESS = "address"  # 地址断点
    WATCH_WRITE = "watch_write"  # 写监视点
    WATCH_READ = "watch_read"  # 读监视点
    WATCH_ACCESS = "watch_access"  # 访问监视点
    EXCEPTION = "exception"  # 异常断点
    SYSTEM_CALL = "system_call"  # 系统调用断点


class BreakpointState(Enum):
    """断点状态"""

    ENABLED = "enabled"
    DISABLED = "disabled"
    CONDITIONAL_FALSE = "conditional_false"
    HIT_COUNT = "hit_count"
    THREAD_SPECIFIC = "thread_specific"


@dataclass
class BreakpointCondition:
    """断点条件"""

    expression: str
    ignore_count: int = 0
    thread_id: Optional[int] = None

    def evaluate(self, frame: Any) -> bool:
        """评估条件是否满足"""
        # 条件评估将在表达式求值器中实现
        raise NotImplementedError


@dataclass
class BreakpointLocation:
    """断点位置"""

    source_file: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    address: Optional[int] = None
    column: Optional[int] = None


@dataclass
class Breakpoint:
    """断点信息"""

    id: int
    type: BreakpointType
    location: BreakpointLocation
    state: BreakpointState = BreakpointState.ENABLED
    condition: Optional[BreakpointCondition] = None
    hit_count: int = 0
    ignore_count: int = 0
    commands: List[str] = field(default_factory=list)
    thread_id: Optional[int] = None
    tasks_only: bool = False

    def __post_init__(self):
        if self.condition is None:
            self.condition = BreakpointCondition(expression="")

    @property
    def is_enabled(self) -> bool:
        return self.state == BreakpointState.ENABLED

    @property
    def is_watchpoint(self) -> bool:
        return self.type in (
            BreakpointType.WATCH_WRITE,
            BreakpointType.WATCH_READ,
            BreakpointType.WATCH_ACCESS,
        )

    def should_stop(self, hit_count: int = 0) -> bool:
        """判断是否应该停止"""
        if not self.is_enabled:
            return False

        # 检查忽略计数
        if self.ignore_count > 0:
            self.ignore_count -= 1
            return False

        # 检查命中计数条件
        if self.condition.expression:
            # 条件评估将在运行时进行
            return True

        return True

    def get_location_string(self) -> str:
        """获取位置字符串"""
        if self.location.source_file and self.location.line_number:
            return f"{self.location.source_file}:{self.location.line_number}"
        elif self.location.function_name:
            return self.location.function_name
        elif self.location.address:
            return f"*{self.location.address:#x}"
        else:
            return "<unknown>"


@dataclass
class BreakpointCommand:
    """断点命令"""

    command: str
    enabled: bool = True
    is_breakpoint_command: bool = True


@dataclass
class BreakpointCallback:
    """断点回调"""

    callback: Callable[["Breakpoint", Any], None]
    once: bool = False

    def __call__(self, bp: Breakpoint, frame: Any):
        self.callback(bp, frame)
        if self.once:
            # 一次性回调，执行后移除
            pass


class BreakpointManager:
    """断点管理器"""

    def __init__(self):
        self._breakpoints: Dict[int, Breakpoint] = {}
        self._next_id: int = 1
        self._watchpoint_id_base: int = 10000
        self._callbacks: Dict[int, List[BreakpointCallback]] = {}
        self._address_to_breakpoint: Dict[int, int] = {}

    def set_source_breakpoint(
        self,
        source_file: str,
        line: int,
        column: Optional[int] = None,
        condition: Optional[str] = None,
        ignore_count: int = 0,
        thread_id: Optional[int] = None,
    ) -> Breakpoint:
        """设置源码行断点"""
        location = BreakpointLocation(
            source_file=source_file, line_number=line, column=column
        )

        bp_condition = BreakpointCondition(
            expression=condition or "", ignore_count=ignore_count, thread_id=thread_id
        )

        bp = Breakpoint(
            id=self._next_id,
            type=BreakpointType.SOURCE_LINE,
            location=location,
            condition=bp_condition,
            thread_id=thread_id,
        )

        self._breakpoints[self._next_id] = bp
        self._next_id += 1

        return bp

    def set_function_breakpoint(
        self, function_name: str, condition: Optional[str] = None, ignore_count: int = 0
    ) -> Breakpoint:
        """设置函数断点"""
        location = BreakpointLocation(function_name=function_name)

        bp_condition = BreakpointCondition(
            expression=condition or "", ignore_count=ignore_count
        )

        bp = Breakpoint(
            id=self._next_id,
            type=BreakpointType.FUNCTION,
            location=location,
            condition=bp_condition,
        )

        self._breakpoints[self._next_id] = bp
        self._next_id += 1

        return bp

    def set_address_breakpoint(
        self, address: int, condition: Optional[str] = None
    ) -> Breakpoint:
        """设置地址断点"""
        location = BreakpointLocation(address=address)

        bp_condition = BreakpointCondition(expression=condition or "", ignore_count=0)

        bp = Breakpoint(
            id=self._next_id,
            type=BreakpointType.ADDRESS,
            location=location,
            condition=bp_condition,
        )

        self._breakpoints[self._next_id] = bp
        self._address_to_breakpoint[address] = self._next_id
        self._next_id += 1

        return bp

    def set_watchpoint(
        self,
        variable_name: str,
        watch_type: BreakpointType,
        condition: Optional[str] = None,
    ) -> Breakpoint:
        """设置监视点"""
        if watch_type not in (
            BreakpointType.WATCH_WRITE,
            BreakpointType.WATCH_READ,
            BreakpointType.WATCH_ACCESS,
        ):
            raise ValueError(f"Invalid watchpoint type: {watch_type}")

        location = BreakpointLocation(function_name=variable_name)

        bp_condition = BreakpointCondition(expression=condition or "", ignore_count=0)

        bp = Breakpoint(
            id=self._next_id, type=watch_type, location=location, condition=bp_condition
        )

        self._breakpoints[self._next_id] = bp
        self._next_id += 1

        return bp

    def set_exception_breakpoint(
        self, exception_type: Optional[str] = None, catch: bool = True
    ) -> Breakpoint:
        """设置异常断点"""
        location = BreakpointLocation(function_name=exception_type or "all")

        bp = Breakpoint(
            id=self._next_id, type=BreakpointType.EXCEPTION, location=location
        )

        self._breakpoints[self._next_id] = bp
        self._next_id += 1

        return bp

    def delete_breakpoint(self, id: int) -> bool:
        """删除断点"""
        if id in self._breakpoints:
            bp = self._breakpoints[id]

            # 如果是地址断点，清理映射
            if bp.location.address:
                addr = bp.location.address
                if addr in self._address_to_breakpoint:
                    del self._address_to_breakpoint[addr]

            # 清理回调
            if id in self._callbacks:
                del self._callbacks[id]

            del self._breakpoints[id]
            return True

        return False

    def delete_all_breakpoints(self) -> int:
        """删除所有断点"""
        count = len(self._breakpoints)
        self._breakpoints.clear()
        self._callbacks.clear()
        self._address_to_breakpoint.clear()
        return count

    def enable_breakpoint(self, id: int) -> bool:
        """启用断点"""
        if id in self._breakpoints:
            self._breakpoints[id].state = BreakpointState.ENABLED
            return True
        return False

    def disable_breakpoint(self, id: int) -> bool:
        """禁用断点"""
        if id in self._breakpoints:
            self._breakpoints[id].state = BreakpointState.DISABLED
            return True
        return False

    def toggle_breakpoint(self, id: int) -> bool:
        """切换断点状态"""
        if id in self._breakpoints:
            bp = self._breakpoints[id]
            if bp.is_enabled:
                bp.state = BreakpointState.DISABLED
            else:
                bp.state = BreakpointState.ENABLED
            return True
        return False

    def get_breakpoint(self, id: int) -> Optional[Breakpoint]:
        """获取断点"""
        return self._breakpoints.get(id)

    def get_breakpoint_at_location(
        self, source_file: str, line: int
    ) -> Optional[Breakpoint]:
        """获取指定位置的断点"""
        for bp in self._breakpoints.values():
            if (
                bp.location.source_file == source_file
                and bp.location.line_number == line
            ):
                return bp
        return None

    def get_breakpoints_by_file(self, source_file: str) -> List[Breakpoint]:
        """获取文件的所有断点"""
        return [
            bp
            for bp in self._breakpoints.values()
            if bp.location.source_file == source_file
        ]

    def get_all_breakpoints(self) -> List[Breakpoint]:
        """获取所有断点"""
        return list(self._breakpoints.values())

    def get_enabled_breakpoints(self) -> List[Breakpoint]:
        """获取所有启用的断点"""
        return [bp for bp in self._breakpoints.values() if bp.is_enabled]

    def get_watchpoints(self) -> List[Breakpoint]:
        """获取所有监视点"""
        return [bp for bp in self._breakpoints.values() if bp.is_watchpoint]

    def register_callback(
        self,
        breakpoint_id: int,
        callback: Callable[[Breakpoint, Any], None],
        once: bool = False,
    ) -> bool:
        """注册断点回调"""
        if breakpoint_id not in self._breakpoints:
            return False

        if breakpoint_id not in self._callbacks:
            self._callbacks[breakpoint_id] = []

        self._callbacks[breakpoint_id].append(
            BreakpointCallback(callback=callback, once=once)
        )
        return True

    def unregister_callback(self, breakpoint_id: int, callback: Callable) -> bool:
        """注销断点回调"""
        if breakpoint_id not in self._callbacks:
            return False

        initial_count = len(self._callbacks[breakpoint_id])
        self._callbacks[breakpoint_id] = [
            cb for cb in self._callbacks[breakpoint_id] if cb.callback != callback
        ]

        return len(self._callbacks[breakpoint_id]) < initial_count

    def trigger_breakpoint(self, breakpoint_id: int, frame: Any) -> bool:
        """触发断点"""
        if breakpoint_id not in self._breakpoints:
            return False

        bp = self._breakpoints[breakpoint_id]
        bp.hit_count += 1

        # 调用回调
        if breakpoint_id in self._callbacks:
            for cb in self._callbacks[breakpoint_id]:
                cb(bp, frame)

            # 清理一次性回调
            self._callbacks[breakpoint_id] = [
                cb for cb in self._callbacks[breakpoint_id] if not cb.once
            ]

        return bp.should_stop(bp.hit_count)

    def add_command(self, breakpoint_id: int, command: str) -> bool:
        """添加断点命令"""
        if breakpoint_id not in self._breakpoints:
            return False

        self._breakpoints[breakpoint_id].commands.append(command)
        return True

    def clear_commands(self, breakpoint_id: int) -> bool:
        """清除断点命令"""
        if breakpoint_id not in self._breakpoints:
            return False

        self._breakpoints[breakpoint_id].commands.clear()
        return True

    def modify_condition(self, breakpoint_id: int, condition: str) -> bool:
        """修改断点条件"""
        if breakpoint_id not in self._breakpoints:
            return False

        self._breakpoints[breakpoint_id].condition.expression = condition
        return True

    def modify_ignore_count(self, breakpoint_id: int, ignore_count: int) -> bool:
        """修改忽略计数"""
        if breakpoint_id not in self._breakpoints:
            return False

        self._breakpoints[breakpoint_id].ignore_count = ignore_count
        return True

    def set_thread_id(self, breakpoint_id: int, thread_id: int) -> bool:
        """设置线程特定的断点"""
        if breakpoint_id not in self._breakpoints:
            return False

        self._breakpoints[breakpoint_id].thread_id = thread_id
        self._breakpoints[breakpoint_id].tasks_only = False
        return True

    def to_gdb_commands(self) -> List[str]:
        """转换为 GDB 命令"""
        commands = []
        for bp in self._breakpoints.values():
            loc_str = bp.get_location_string()
            if bp.condition.expression:
                commands.append(f"break {loc_str} if {bp.condition.expression}")
            else:
                commands.append(f"break {loc_str}")

            if bp.ignore_count > 0:
                commands.append(f"ignore {bp.id} {bp.ignore_count}")

            for cmd in bp.commands:
                commands.append(f"commands {bp.id}")
                commands.append(cmd)
                commands.append("end")

        return commands

    def to_lldb_commands(self) -> List[str]:
        """转换为 LLDB 命令"""
        commands = []
        for bp in self._breakpoints.values():
            if bp.location.source_file and bp.location.line_number:
                loc_str = f"-f {bp.location.source_file} -l {bp.location.line_number}"
                commands.append(f"breakpoint set {loc_str}")
            elif bp.location.function_name:
                commands.append(f"breakpoint set -n {bp.location.function_name}")
            elif bp.location.address:
                commands.append(f"breakpoint set -a {bp.location.address:#x}")

            if bp.condition.expression:
                commands.append(
                    f"breakpoint modify -c '{bp.condition.expression}' {bp.id}"
                )

            if not bp.is_enabled:
                commands.append(f"breakpoint disable {bp.id}")

            for cmd in bp.commands:
                commands.append(f"breakpoint command add {bp.id}")
                commands.append(cmd)
                commands.append("DONE")

        return commands

    def __len__(self) -> int:
        return len(self._breakpoints)

    def __repr__(self) -> str:
        return f"BreakpointManager(bp_count={len(self._breakpoints)})"

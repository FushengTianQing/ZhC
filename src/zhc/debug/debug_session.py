"""
调试会话

提供完整的调试会话管理：
- 会话控制
- 断点管理
- 变量查看
- 调用栈操作
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .breakpoint_engine import BreakpointEngine, BreakpointHit, WatchType
from .variable_printer import VariablePrinter
from .stack_frame_analyzer import StackFrameAnalyzer
from .debug_info_collector import DebugInfoCollector


class SessionState(Enum):
    """会话状态"""

    STOPPED = "stopped"
    RUNNING = "running"
    STEPPING = "stepping"
    BREAKPOINT = "breakpoint"
    WATCHPOINT = "watchpoint"
    EXITED = "exited"
    TERMINATED = "terminated"


class StopReason(Enum):
    """停止原因"""

    BREAKPOINT = "breakpoint"
    WATCHPOINT = "watchpoint"
    SINGLE_STEP = "single_step"
    FUNCTION_FINISH = "function_finish"
    PROGRAM_EXIT = "program_exit"
    SIGNAL = "signal"
    EXCEPTION = "exception"
    STOPPED = "stopped"


@dataclass
class StopInfo:
    """停止信息"""

    reason: StopReason
    breakpoint_id: Optional[int] = None
    watchpoint_id: Optional[int] = None
    signal: Optional[str] = None
    message: Optional[str] = None


@dataclass
class SessionConfig:
    """会话配置"""

    auto_start: bool = False
    stop_at_entry: bool = True
    stop_on_first_breakpoint: bool = True
    max_backtrace_depth: int = 100
    max_variable_depth: int = 5
    max_array_elements: int = 100
    show_hidden_variables: bool = False
    print_pretty: bool = True


class DebugSession:
    """调试会话"""

    def __init__(
        self,
        executable: Path,
        source_root: Optional[Path] = None,
        config: Optional[SessionConfig] = None,
    ):
        self._executable = executable
        self._source_root = source_root or executable.parent
        self._config = config or SessionConfig()

        # 初始化组件
        self._debug_info: Optional[DebugInfoCollector] = None
        self._breakpoint_engine: Optional[BreakpointEngine] = None
        self._variable_printer: Optional[VariablePrinter] = None
        self._stack_analyzer: Optional[StackFrameAnalyzer] = None

        # 会话状态
        self._state = SessionState.STOPPED
        self._stop_info: Optional[StopInfo] = None
        self._current_thread_id: int = 0
        self._current_frame_id: int = 0
        self._hit_counts: Dict[int, int] = {}

        # 回调
        self._stop_callbacks: List[Callable[[StopInfo], None]] = []
        self._breakpoint_callbacks: Dict[
            int, List[Callable[[BreakpointHit], None]]
        ] = {}

    @property
    def state(self) -> SessionState:
        """获取会话状态"""
        return self._state

    @property
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._state == SessionState.RUNNING

    @property
    def is_stopped(self) -> bool:
        """检查是否已停止"""
        return self._state in (
            SessionState.STOPPED,
            SessionState.BREAKPOINT,
            SessionState.WATCHPOINT,
        )

    def initialize(self) -> bool:
        """初始化会话"""
        # 加载调试信息
        self._debug_info = DebugInfoCollector()
        # TODO: 从可执行文件加载 DWARF 信息

        # 初始化组件
        self._breakpoint_engine = BreakpointEngine()
        self._variable_printer = VariablePrinter(self._debug_info)
        self._stack_analyzer = StackFrameAnalyzer(self._debug_info)

        self._state = SessionState.STOPPED
        return True

    # ==================== 会话控制 ====================

    def run(self, args: Optional[List[str]] = None) -> None:
        """运行程序

        Args:
            args: 程序参数
        """
        if self._state != SessionState.STOPPED:
            raise RuntimeError("Cannot run: session is not stopped")

        self._state = SessionState.RUNNING

        # TODO: 实际启动调试器
        # 启动 inferior 进程
        # 设置初始断点
        # 继续执行

    def continue_exec(self) -> None:
        """继续执行"""
        if not self.is_stopped:
            raise RuntimeError("Cannot continue: program is not stopped")

        self._state = SessionState.RUNNING

        # TODO: 继续执行 inferior
        # 发送 continue 信号

    def stop(self) -> None:
        """停止程序"""
        self._state = SessionState.STOPPED

        # TODO: 停止 inferior 进程
        # 发送 interrupt 信号

    def kill(self) -> None:
        """终止程序"""
        self._state = SessionState.TERMINATED

        # TODO: 终止 inferior 进程
        # 清理资源

    def detach(self) -> None:
        """分离调试器"""
        self._state = SessionState.TERMINATED

        # TODO: 分离调试器
        # 保持进程运行

    # ==================== 单步执行 ====================

    def step(self) -> None:
        """单步进入"""
        if not self.is_stopped:
            raise RuntimeError("Cannot step: program is not stopped")

        self._state = SessionState.STEPPING

        # TODO: 执行单步（进入函数）
        # 使用 inferior.Step()

    def next(self) -> None:
        """单步跳过"""
        if not self.is_stopped:
            raise RuntimeError("Cannot step: program is not stopped")

        self._state = SessionState.STEPPING

        # TODO: 执行单步（跳过函数）
        # 使用 inferior.Next()

    def finish(self) -> None:
        """执行到函数返回"""
        if not self.is_stopped:
            raise RuntimeError("Cannot finish: program is not stopped")

        self._state = SessionState.STEPPING

        # TODO: 执行到函数返回
        # 使用 inferior.finish()

    def until(self, file: Optional[str] = None, line: Optional[int] = None) -> None:
        """执行到指定位置"""
        if not self.is_stopped:
            raise RuntimeError("Cannot continue: program is not stopped")

        # 设置临时断点 (TODO: 实际执行)
        if file and line:
            self._breakpoint_engine.set_source_breakpoint(file, line)

        self._state = SessionState.RUNNING

        # TODO: 继续执行

    # ==================== 断点管理 ====================

    def set_breakpoint(
        self, location: str, condition: Optional[str] = None, ignore_count: int = 0
    ) -> int:
        """设置断点

        Args:
            location: 断点位置 (file:line 或 function)
            condition: 条件表达式
            ignore_count: 忽略计数

        Returns:
            断点 ID
        """
        if not self._breakpoint_engine:
            raise RuntimeError("Session not initialized")

        # 解析位置
        if ":" in location:
            file, line_str = location.rsplit(":", 1)
            try:
                line = int(line_str)
                bp_id = self._breakpoint_engine.set_source_breakpoint(
                    str(self._source_root / file), line
                )
            except ValueError:
                bp_id = self._breakpoint_engine.set_function_breakpoint(location)
        else:
            bp_id = self._breakpoint_engine.set_function_breakpoint(location)

        # 设置条件
        if condition:
            self._breakpoint_engine.set_condition(bp_id, condition)

        # 设置忽略计数
        if ignore_count > 0:
            self._breakpoint_engine.set_ignore_count(bp_id, ignore_count)

        return bp_id

    def set_watchpoint(
        self, variable: str, watch_type: WatchType = WatchType.WRITE
    ) -> int:
        """设置监视点"""
        if not self._breakpoint_engine:
            raise RuntimeError("Session not initialized")

        return self._breakpoint_engine.set_watchpoint(
            variable,
            watch_type,
            frame_context=None,  # TODO: 传入帧上下文
        )

    def delete_breakpoint(self, breakpoint_id: int) -> bool:
        """删除断点"""
        if not self._breakpoint_engine:
            return False

        return self._breakpoint_engine.delete_breakpoint(breakpoint_id)

    def enable_breakpoint(self, breakpoint_id: int) -> bool:
        """启用断点"""
        if not self._breakpoint_engine:
            return False

        return self._breakpoint_engine.enable_breakpoint(breakpoint_id)

    def disable_breakpoint(self, breakpoint_id: int) -> bool:
        """禁用断点"""
        if not self._breakpoint_engine:
            return False

        return self._breakpoint_engine.disable_breakpoint(breakpoint_id)

    def list_breakpoints(self) -> List[Any]:
        """列出所有断点"""
        if not self._breakpoint_engine:
            return []

        breakpoints = self._breakpoint_engine.get_all_breakpoints()
        watchpoints = self._breakpoint_engine.get_all_watchpoints()

        return breakpoints + watchpoints

    # ==================== 变量查看 ====================

    def print_variable(self, name: str) -> str:
        """打印变量

        Args:
            name: 变量名

        Returns:
            格式化后的变量信息
        """
        if not self._variable_printer or not self.is_stopped:
            return "<not available>"

        # 获取当前帧
        frame = self._stack_analyzer.get_current_frame()
        if not frame:
            return "<no frame>"

        # 设置当前帧
        self._variable_printer.set_current_frame(frame.pc, frame.frame_pointer or 0)

        # 获取局部变量
        locals_vars = self._variable_printer.print_local_variables(None)
        for var in locals_vars:
            if var.name == name:
                return self._variable_printer.format_variable(var)

        # 获取参数
        args = self._variable_printer.print_arguments(None)
        for var in args:
            if var.name == name:
                return self._variable_printer.format_variable(var)

        return f"<variable '{name}' not found>"

    def list_locals(self) -> str:
        """列出局部变量"""
        if not self._variable_printer or not self.is_stopped:
            return "<not available>"

        frame = self._stack_analyzer.get_current_frame()
        if not frame:
            return "<no frame>"

        self._variable_printer.set_current_frame(frame.pc, frame.frame_pointer or 0)

        locals_vars = self._variable_printer.print_local_variables(None)
        return self._variable_printer.format_variable_list(locals_vars)

    def list_args(self) -> str:
        """列出函数参数"""
        if not self._variable_printer or not self.is_stopped:
            return "<not available>"

        frame = self._stack_analyzer.get_current_frame()
        if not frame:
            return "<no frame>"

        self._variable_printer.set_current_frame(frame.pc, frame.frame_pointer or 0)

        args = self._variable_printer.print_arguments(None)
        return self._variable_printer.format_variable_list(args)

    def examine_memory(self, address: int, count: int = 10) -> str:
        """查看内存

        Args:
            address: 起始地址
            count: 元素数量

        Returns:
            格式化后的内存内容
        """
        # TODO: 实现内存查看
        return "<not implemented>"

    # ==================== 调用栈 ====================

    def backtrace(self, max_depth: Optional[int] = None) -> str:
        """显示调用栈

        Args:
            max_depth: 最大深度

        Returns:
            格式化后的调用栈
        """
        if not self._stack_analyzer or not self.is_stopped:
            return "<not available>"

        if max_depth is None:
            max_depth = self._config.max_backtrace_depth

        frames = self._stack_analyzer.get_backtrace(
            thread_context=None,  # TODO: 传入线程上下文
            max_depth=max_depth,
        )

        return self._stack_analyzer.format_backtrace(frames)

    def frame(self, frame_id: int) -> str:
        """切换栈帧

        Args:
            frame_id: 帧 ID

        Returns:
            帧信息
        """
        if not self._stack_analyzer:
            return "<not available>"

        if self._stack_analyzer.select_frame(frame_id):
            self._current_frame_id = frame_id
            frame = self._stack_analyzer.get_current_frame()
            if frame:
                return self._stack_analyzer.format_frame(frame)

        return f"<frame {frame_id} not found>"

    def up(self, count: int = 1) -> str:
        """向上移动栈帧（向调用者方向）"""
        new_frame_id = self._current_frame_id + count
        return self.frame(new_frame_id)

    def down(self, count: int = 1) -> str:
        """向下移动栈帧（向被调用者方向）"""
        new_frame_id = self._current_frame_id - count
        if new_frame_id < 0:
            new_frame_id = 0
        return self.frame(new_frame_id)

    # ==================== 表达式求值 ====================

    def evaluate(self, expression: str) -> str:
        """求值表达式

        Args:
            expression: 表达式

        Returns:
            求值结果
        """
        # TODO: 实现表达式求值
        return "<not implemented>"

    # ==================== 回调管理 ====================

    def register_stop_callback(self, callback: Callable[[StopInfo], None]) -> None:
        """注册停止回调"""
        self._stop_callbacks.append(callback)

    def register_breakpoint_callback(
        self, breakpoint_id: int, callback: Callable[[BreakpointHit], None]
    ) -> None:
        """注册断点回调"""
        if breakpoint_id not in self._breakpoint_callbacks:
            self._breakpoint_callbacks[breakpoint_id] = []
        self._breakpoint_callbacks[breakpoint_id].append(callback)

    # ==================== 内部方法 ====================

    def _handle_stop(self, stop_info: StopInfo) -> None:
        """处理程序停止"""
        self._stop_info = stop_info

        if stop_info.reason == StopReason.BREAKPOINT:
            self._state = SessionState.BREAKPOINT
        elif stop_info.reason == StopReason.WATCHPOINT:
            self._state = SessionState.WATCHPOINT
        else:
            self._state = SessionState.STOPPED

        # 触发回调
        for callback in self._stop_callbacks:
            callback(stop_info)

    def _handle_breakpoint_hit(self, hit: BreakpointHit) -> None:
        """处理断点命中"""
        # 更新命中计数
        self._hit_counts[hit.breakpoint_id] = hit.hit_count

        # 触发断点回调
        if hit.breakpoint_id in self._breakpoint_callbacks:
            for callback in self._breakpoint_callbacks[hit.breakpoint_id]:
                callback(hit)

    def __repr__(self) -> str:
        return (
            f"DebugSession("
            f"executable={self._executable}, "
            f"state={self._state.value})"
        )

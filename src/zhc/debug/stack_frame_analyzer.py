"""
栈帧分析器

提供调用栈分析功能：
- Backtrace 获取
- 帧切换
- 参数查看
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .debug_info_collector import (
    DebugInfoCollector,
    FunctionDebugInfo,
    VariableDebugInfo,
    SourceLocation,
)


@dataclass
class FrameInfo:
    """栈帧信息"""

    frame_id: int
    pc: int
    return_address: Optional[int] = None
    frame_pointer: Optional[int] = None
    stack_pointer: Optional[int] = None

    # 调试信息
    function_name: Optional[str] = None
    function_linkage_name: Optional[str] = None
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    source_column: Optional[int] = None

    # 参数和局部变量
    arguments: Dict[str, Any] = field(default_factory=dict)
    locals: Dict[str, Any] = field(default_factory=dict)

    # 帧类型
    is_inlined: bool = False
    inlined_call_site: Optional[SourceLocation] = None

    @property
    def location_string(self) -> str:
        """获取位置字符串"""
        parts = []
        if self.function_name:
            parts.append(self.function_name)
        if self.source_file:
            if self.source_line:
                parts.append(f"{self.source_file}:{self.source_line}")
            else:
                parts.append(self.source_file)
        if not parts:
            parts.append(f"0x{self.pc:x}")
        return " at ".join(parts)

    @property
    def is_valid(self) -> bool:
        """检查帧是否有效"""
        return self.pc != 0


@dataclass
class InlinedFunction:
    """内联函数信息"""

    name: str
    call_site: SourceLocation
    ranges: List[Tuple[int, int]]


class StackFrameAnalyzer:
    """栈帧分析器"""

    def __init__(self, debug_info: Optional[DebugInfoCollector] = None):
        self._debug_info = debug_info
        self._frames: List[FrameInfo] = []
        self._current_frame_id: int = 0

    def get_backtrace(
        self, thread_context: Any, max_depth: int = 100
    ) -> List[FrameInfo]:
        """获取调用栈

        Args:
            thread_context: 线程上下文
            max_depth: 最大深度

        Returns:
            栈帧列表
        """
        frames = []
        current_pc = self._get_pc(thread_context)
        current_fp = self._get_frame_pointer(thread_context)
        current_sp = self._get_stack_pointer(thread_context)

        frame_id = 0

        while current_pc != 0 and frame_id < max_depth:
            # 创建帧信息
            frame = self._analyze_frame(
                frame_id=frame_id,
                pc=current_pc,
                frame_pointer=current_fp,
                stack_pointer=current_sp,
                thread_context=thread_context,
            )

            frames.append(frame)

            # 获取返回地址
            return_address = self._read_return_address(current_fp, thread_context)

            # 获取调用者帧信息
            caller_info = self._get_caller_frame(
                return_address, current_fp, thread_context
            )

            if caller_info:
                current_pc = caller_info.pc
                current_fp = caller_info.frame_pointer
                current_sp = caller_info.stack_pointer
            else:
                break

            frame_id += 1

        self._frames = frames
        return frames

    def get_frame(self, frame_id: int) -> Optional[FrameInfo]:
        """获取指定帧

        Args:
            frame_id: 帧 ID

        Returns:
            帧信息
        """
        if 0 <= frame_id < len(self._frames):
            return self._frames[frame_id]
        return None

    def select_frame(self, frame_id: int) -> bool:
        """选择帧

        Args:
            frame_id: 帧 ID

        Returns:
            是否成功
        """
        if 0 <= frame_id < len(self._frames):
            self._current_frame_id = frame_id
            return True
        return False

    def get_current_frame(self) -> Optional[FrameInfo]:
        """获取当前帧"""
        if 0 <= self._current_frame_id < len(self._frames):
            return self._frames[self._current_frame_id]
        return None

    def get_inlined_functions(self, pc: int) -> List[InlinedFunction]:
        """获取指定地址的内联函数

        Args:
            pc: 程序计数器

        Returns:
            内联函数列表
        """
        if not self._debug_info:
            return []

        func_info = self._debug_info.get_function_at_address(pc)
        if not func_info:
            return []

        result = []
        for inlined in func_info.inlined_functions:
            for start, end in inlined.ranges:
                if start <= pc <= end:
                    result.append(
                        InlinedFunction(
                            name=inlined.name,
                            call_site=inlined.call_site,
                            ranges=inlined.ranges,
                        )
                    )

        return result

    def get_function_info(self, pc: int) -> Optional[FunctionDebugInfo]:
        """获取函数信息

        Args:
            pc: 程序计数器

        Returns:
            函数调试信息
        """
        if not self._debug_info:
            return None

        return self._debug_info.get_function_at_address(pc)

    def get_call_site(self, frame: FrameInfo) -> Optional[SourceLocation]:
        """获取调用点信息

        Args:
            frame: 栈帧

        Returns:
            调用点位置
        """
        if not self._debug_info:
            return None

        # 查找调用此函数的位置
        func_info = self._debug_info.get_function_at_address(frame.pc)
        if not func_info:
            return None

        # 返回地址指向调用指令的下一条
        caller_pc = frame.return_address - 1 if frame.return_address else None

        if caller_pc:
            # 尝试从行号表获取
            location = self._debug_info.get_source_location(caller_pc)
            return location

        return None

    def _analyze_frame(
        self,
        frame_id: int,
        pc: int,
        frame_pointer: int,
        stack_pointer: int,
        thread_context: Any,
    ) -> FrameInfo:
        """分析栈帧"""
        frame = FrameInfo(
            frame_id=frame_id,
            pc=pc,
            frame_pointer=frame_pointer,
            stack_pointer=stack_pointer,
        )

        # 尝试获取函数信息
        func_info = self.get_function_info(pc)
        if func_info:
            frame.function_name = func_info.name
            frame.function_linkage_name = func_info.linkage_name

            # 获取源码位置
            location = func_info.get_source_location(pc)
            if location:
                frame.source_file = location.file
                frame.source_line = location.line
                frame.source_column = location.column

            # 获取参数
            for arg in func_info.arguments:
                value = self._read_argument(arg, frame_pointer, thread_context)
                frame.arguments[arg.name] = value

        # 检查内联函数
        inlined = self.get_inlined_functions(pc)
        if inlined:
            frame.is_inlined = True
            frame.inlined_call_site = inlined[0].call_site

        return frame

    def _get_caller_frame(
        self, return_address: int, current_fp: int, thread_context: Any
    ) -> Optional[FrameInfo]:
        """获取调用者帧"""
        if return_address == 0:
            return None

        # 从返回地址获取调用者 PC
        caller_pc = return_address

        # 从栈中获取调用者 FP
        caller_fp = self._read_memory(current_fp, 8)
        if caller_fp:
            caller_fp = int.from_bytes(caller_fp, "little")

        # 调用者 SP = FP + 8 (返回地址 + 旧 FP)
        caller_sp = current_fp + 16 if current_fp else 0

        return FrameInfo(
            frame_id=-1,  # 临时 ID
            pc=caller_pc,
            frame_pointer=caller_fp,
            stack_pointer=caller_sp,
            return_address=None,
        )

    def _read_argument(
        self, arg_info: VariableDebugInfo, frame_pointer: int, thread_context: Any
    ) -> Any:
        """读取函数参数"""
        # 需要根据参数传递约定来读取
        # 这里简化处理
        return None

    def _read_return_address(
        self, frame_pointer: int, thread_context: Any
    ) -> Optional[int]:
        """读取返回地址"""
        data = self._read_memory(frame_pointer, 8)
        if data:
            return int.from_bytes(data, "little")
        return None

    def _read_memory(self, address: int, size: int) -> Optional[bytes]:
        """读取内存"""
        # 需要实际调试器后端支持
        return None

    def _get_pc(self, thread_context: Any) -> int:
        """获取程序计数器"""
        # 需要实际调试器后端支持
        return 0

    def _get_frame_pointer(self, thread_context: Any) -> int:
        """获取帧指针"""
        # 需要实际调试器后端支持
        return 0

    def _get_stack_pointer(self, thread_context: Any) -> int:
        """获取栈指针"""
        # 需要实际调试器后端支持
        return 0

    def format_backtrace(self, frames: List[FrameInfo]) -> str:
        """格式化调用栈显示"""
        if not frames:
            return "(no stack frames)"

        lines = []
        for frame in frames:
            prefix = "#" + str(frame.frame_id).rjust(2)
            if frame.is_inlined:
                prefix += "i"  # inlined marker

            pc_str = f"0x{frame.pc:x}" if frame.pc else "?"

            if frame.function_name:
                if frame.source_file and frame.source_line:
                    location = f"{frame.source_file}:{frame.source_line}"
                    lines.append(f"{prefix}  {frame.function_name} at {location}")
                else:
                    lines.append(f"{prefix}  {frame.function_name} ({pc_str})")
            else:
                lines.append(f"{prefix}  {pc_str}")

        return "\n".join(lines)

    def format_frame(self, frame: FrameInfo) -> str:
        """格式化帧信息"""
        lines = []

        # 基本信息
        lines.append(f"Frame #{frame.frame_id}:")
        lines.append(f"  PC: 0x{frame.pc:x}" if frame.pc else "  PC: ?")

        if frame.function_name:
            lines.append(f"  Function: {frame.function_name}")
            if frame.function_linkage_name:
                lines.append(f"  Linkage name: {frame.function_linkage_name}")

        if frame.source_file:
            line_info = f"{frame.source_file}"
            if frame.source_line:
                line_info += f":{frame.source_line}"
                if frame.source_column:
                    line_info += f":{frame.source_column}"
            lines.append(f"  Source: {line_info}")

        # 指针信息
        if frame.frame_pointer:
            lines.append(f"  Frame pointer: 0x{frame.frame_pointer:x}")
        if frame.stack_pointer:
            lines.append(f"  Stack pointer: 0x{frame.stack_pointer:x}")
        if frame.return_address:
            lines.append(f"  Return address: 0x{frame.return_address:x}")

        # 内联信息
        if frame.is_inlined and frame.inlined_call_site:
            lines.append(f"  Inlined from: {frame.inlined_call_site}")

        # 参数
        if frame.arguments:
            lines.append("  Arguments:")
            for name, value in frame.arguments.items():
                lines.append(f"    {name} = {value}")

        # 局部变量
        if frame.locals:
            lines.append("  Local variables:")
            for name, value in frame.locals.items():
                lines.append(f"    {name} = {value}")

        return "\n".join(lines)

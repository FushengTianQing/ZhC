# -*- coding: utf-8 -*-
"""
异常上下文管理

管理异常传播过程中的上下文状态，包括当前异常、处理器栈、栈帧信息。

作者：远
日期：2026-04-10
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict, Any, TYPE_CHECKING
from enum import Enum

from .types import ExceptionObject

# 避免循环导入的类型检查
if TYPE_CHECKING:
    from .registry import ExceptionRegistry


class ExceptionState(Enum):
    """异常状态"""

    NONE = "none"  # 无异常
    THROWING = "throwing"  # 正在抛出
    UNWINDING = "unwinding"  # 栈展开中
    CAUGHT = "caught"  # 已捕获
    HANDLED = "handled"  # 已处理


@dataclass
class StackFrameInfo:
    """栈帧信息

    Attributes:
        function_name: 函数名称
        file_name: 文件名称
        line_number: 行号
        has_finally: 是否有 finally 块
        finally_handler: finally 处理函数
        cleanup_handlers: 清理处理器列表
        local_variables: 局部变量快照
    """

    function_name: str
    file_name: str
    line_number: int
    has_finally: bool = False
    finally_handler: Optional[Callable] = None
    cleanup_handlers: List[Callable] = field(default_factory=list)
    local_variables: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExceptionHandler:
    """异常处理器

    Attributes:
        exception_types: 捕获的异常类型列表
        variable_name: 异常变量名
        catch_block: catch 代码块
        finally_block: finally 代码块
        frame_index: 所在栈帧索引
        is_default: 是否为默认处理器
    """

    exception_types: List[str]
    variable_name: Optional[str]
    catch_block: Callable
    finally_block: Optional[Callable] = None
    frame_index: int = 0
    is_default: bool = False

    def matches(
        self, exc_type: str, registry: Optional["ExceptionRegistry"] = None
    ) -> bool:
        """检查是否匹配异常类型

        Args:
            exc_type: 异常类型名称
            registry: 异常类型注册表

        Returns:
            如果匹配返回 True
        """
        # 默认处理器匹配所有异常
        if self.is_default:
            return True

        # 精确匹配
        if exc_type in self.exception_types:
            return True

        # 子类型检查
        if registry is not None:
            for handler_type in self.exception_types:
                if registry.is_subtype(exc_type, handler_type):
                    return True

        return False


class ExceptionContext:
    """异常上下文

    管理异常传播过程中的所有状态信息。

    Example:
        >>> ctx = ExceptionContext()
        >>> ctx.push_frame(StackFrameInfo("main", "main.zhc", 1))
        >>> print(ctx.stack_frames)
        [StackFrameInfo(function_name='main', ...)]
    """

    def __init__(self):
        self.current_exception: Optional[ExceptionObject] = None
        self.state: ExceptionState = ExceptionState.NONE
        self.stack_frames: List[StackFrameInfo] = []
        self.handler_stack: List[ExceptionHandler] = []
        self._uncaught_handler: Optional[Callable] = None

    def push_frame(self, frame: StackFrameInfo) -> None:
        """压入栈帧

        Args:
            frame: 栈帧信息
        """
        self.stack_frames.append(frame)

    def pop_frame(self) -> Optional[StackFrameInfo]:
        """弹出栈帧

        Returns:
            弹出的栈帧，如果为空返回 None
        """
        if self.stack_frames:
            return self.stack_frames.pop()
        return None

    def get_current_frame(self) -> Optional[StackFrameInfo]:
        """获取当前栈帧

        Returns:
            当前栈帧，如果为空返回 None
        """
        if self.stack_frames:
            return self.stack_frames[-1]
        return None

    def find_handler(
        self, exc_type: str, registry: Optional["ExceptionRegistry"] = None
    ) -> Optional[ExceptionHandler]:
        """查找匹配的处理器

        Args:
            exc_type: 异常类型名称
            registry: 异常类型注册表

        Returns:
            匹配的处理器，如果未找到返回 None
        """
        # 从栈顶向栈底查找（LIFO 顺序）
        for handler in reversed(self.handler_stack):
            if handler.matches(exc_type, registry):
                return handler
        return None

    def register_handler(self, handler: ExceptionHandler) -> None:
        """注册异常处理器

        Args:
            handler: 异常处理器
        """
        handler.frame_index = len(self.stack_frames) - 1
        self.handler_stack.append(handler)

    def unregister_handler(self) -> Optional[ExceptionHandler]:
        """注销最近注册的处理器

        Returns:
            注销的处理器，如果为空返回 None
        """
        if self.handler_stack:
            return self.handler_stack.pop()
        return None

    def set_uncaught_handler(self, handler: Callable) -> None:
        """设置未捕获异常处理器

        Args:
            handler: 处理函数
        """
        self._uncaught_handler = handler

    def handle_uncaught(self) -> None:
        """处理未捕获异常"""
        exc = self.current_exception
        if self._uncaught_handler and exc:
            self._uncaught_handler(exc)
        else:
            # 默认处理：打印并终止
            import sys

            print(f"未捕获异常: {exc.type_name}: {exc.message}", file=sys.stderr)
            if exc.stack_trace:
                print("堆栈跟踪:", file=sys.stderr)
                for frame in exc.stack_trace[-5:]:  # 只显示最后5帧
                    print(f"  {frame}", file=sys.stderr)
            sys.exit(1)

    def capture_stack_trace(self) -> List[str]:
        """捕获当前堆栈跟踪

        Returns:
            堆栈跟踪信息列表
        """
        import traceback

        frames = traceback.format_stack()
        # 过滤掉异常处理相关的帧
        filtered = [f for f in frames if "exception" not in f.lower()]
        return filtered

    def clear(self) -> None:
        """清除上下文状态"""
        self.current_exception = None
        self.state = ExceptionState.NONE
        # 保留 stack_frames 和 handler_stack 以支持调试

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.clear()
        return False  # 不抑制异常


# 导出公共符号
__all__ = [
    "ExceptionState",
    "StackFrameInfo",
    "ExceptionHandler",
    "ExceptionContext",
]

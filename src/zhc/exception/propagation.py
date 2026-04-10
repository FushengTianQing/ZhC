# -*- coding: utf-8 -*-
"""
异常传播机制

实现异常在调用栈中的传播，包括跨函数传播、栈展开、finally 执行。

作者：远
日期：2026-04-10
"""

import sys
from typing import List, Optional, Callable, Dict

from .context import (
    ExceptionContext,
    ExceptionState,
    ExceptionHandler,
    StackFrameInfo,
)
from .types import ExceptionObject
from .registry import ExceptionRegistry


class StackUnwinder:
    """栈展开器

    负责执行栈展开过程中的清理操作。

    Attributes:
        context: 异常上下文
    """

    def __init__(self, context: ExceptionContext):
        self.context = context

    def unwind_to_handler(self, handler: ExceptionHandler) -> List[Callable]:
        """展开到指定处理器

        Args:
            handler: 目标异常处理器

        Returns:
            需要执行的 finally 块列表
        """
        self.context.state = ExceptionState.UNWINDING
        finally_blocks: List[Callable] = []

        # 获取目标帧索引
        # handler.frame_index 指向 handler 所在的栈帧
        # 我们需要展开该帧以上的所有栈帧
        target_frame_index = handler.frame_index

        # 展开栈帧，执行 finally 块
        while self.context.stack_frames:
            current_index = len(self.context.stack_frames) - 1

            # 如果已经超过目标帧，停止展开
            if current_index < target_frame_index:
                break

            frame = self.context.stack_frames[-1]

            # 执行 finally 块
            if frame.has_finally and frame.finally_handler:
                finally_blocks.append(frame.finally_handler)

            # 执行清理处理器
            for cleanup in frame.cleanup_handlers:
                cleanup()

            # 如果到达目标帧，停止展开
            if current_index == target_frame_index:
                break

            # 弹出栈帧
            self.context.pop_frame()

        return finally_blocks

    def unwind_to_top(self) -> List[Callable]:
        """展开到顶层（无处理器）

        Returns:
            需要执行的 finally 块列表
        """
        self.context.state = ExceptionState.UNWINDING
        finally_blocks: List[Callable] = []

        # 展开所有栈帧
        while self.context.stack_frames:
            frame = self.context.pop_frame()

            if frame and frame.has_finally and frame.finally_handler:
                finally_blocks.append(frame.finally_handler)

            # 执行清理处理器
            if frame:
                for cleanup in frame.cleanup_handlers:
                    cleanup()

        return finally_blocks

    def execute_finally_blocks(
        self, finally_blocks: List[Callable], in_reverse: bool = True
    ) -> None:
        """执行 finally 块

        Args:
            finally_blocks: finally 块列表
            in_reverse: 是否按逆序执行（LIFO 顺序）
        """
        if in_reverse:
            finally_blocks = list(reversed(finally_blocks))

        for block in finally_blocks:
            try:
                block()
            except Exception as e:
                # finally 块中又抛出异常，打印警告
                print(f"Warning: finally 块中抛出异常: {e}", file=sys.stderr)


class ExceptionPropagator:
    """异常传播器

    协调异常的抛出、传播和捕获。

    Example:
        >>> propagator = ExceptionPropagator()
        >>> exc = ExceptionObject("除零异常", "除数不能为零")
        >>> propagator.throw(exc)
    """

    _instance: Optional["ExceptionPropagator"] = None

    def __init__(self):
        self.context = ExceptionContext()
        self.unwinder = StackUnwinder(self.context)
        self.registry = ExceptionRegistry.instance()
        self._setup_uncaught_handler()

    @classmethod
    def instance(cls) -> "ExceptionPropagator":
        """获取单例实例

        Returns:
            ExceptionPropagator 单例
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """重置单例（主要用于测试）"""
        cls._instance = None

    def _setup_uncaught_handler(self) -> None:
        """设置未捕获异常处理器"""

        def default_handler(exc: ExceptionObject):
            print(f"未捕获异常: {exc.type_name}: {exc.message}", file=sys.stderr)
            if exc.stack_trace:
                print("堆栈跟踪:", file=sys.stderr)
                for frame in exc.stack_trace[-10:]:
                    print(f"  {frame.strip()}", file=sys.stderr)
            sys.exit(1)

        self.context.set_uncaught_handler(default_handler)

    def throw(self, exc: ExceptionObject, capture_trace: bool = True) -> None:
        """抛出异常

        Args:
            exc: 异常对象
            capture_trace: 是否捕获堆栈跟踪
        """
        # 设置当前异常
        self.context.current_exception = exc
        self.context.state = ExceptionState.THROWING

        # 捕获堆栈跟踪
        if capture_trace:
            exc.stack_trace = self.context.capture_stack_trace()

        # 查找匹配的处理器
        handler = self.context.find_handler(exc.type_name, self.registry)

        if handler:
            # 找到处理器，执行栈展开
            self._execute_catch(handler, exc)
        else:
            # 未找到处理器，向上传播
            self._propagate_to_parent(exc)

    def rethrow(self) -> None:
        """重新抛出当前异常"""
        exc = self.context.current_exception
        if not exc:
            # 没有当前异常，创建一个
            exc = ExceptionObject("异常", "重新抛出，但没有当前异常")
            self.context.current_exception = exc

        self.context.state = ExceptionState.THROWING

        # 查找处理器
        handler = self.context.find_handler(exc.type_name, self.registry)

        if handler:
            self._execute_catch(handler, exc)
        else:
            self._propagate_to_parent(exc)

    def _execute_catch(self, handler: ExceptionHandler, exc: ExceptionObject) -> None:
        """执行 catch 块

        Args:
            handler: 匹配的处理器
            exc: 异常对象
        """
        self.context.state = ExceptionState.CAUGHT

        # 展开栈帧（但不展开到目标帧的下面）
        finally_blocks = self.unwinder.unwind_to_handler(handler)

        # 执行 finally 块
        self.unwinder.execute_finally_blocks(finally_blocks)

        # 执行 catch 代码块
        try:
            if handler.variable_name:
                # 绑定异常变量到调用者上下文
                self._bind_exception_variable(handler.variable_name, exc)

            handler.catch_block()
        except Exception as e:
            # catch 块中又抛出异常
            new_exc = ExceptionObject(type_name=e.__class__.__name__, message=str(e))
            self.throw(new_exc)
        finally:
            # 执行 handler 的 finally 块
            if handler.finally_block:
                handler.finally_block()

        self.context.state = ExceptionState.HANDLED
        self.context.current_exception = None

    def _propagate_to_parent(self, exc: ExceptionObject) -> None:
        """向上传播异常

        Args:
            exc: 异常对象
        """
        # 弹出当前栈帧
        if self.context.stack_frames:
            frame = self.context.pop_frame()

            # 如果有 finally，执行它
            if frame and frame.has_finally and frame.finally_handler:
                try:
                    frame.finally_handler()
                except Exception:
                    pass  # 忽略 finally 中的异常

        if self.context.stack_frames:
            # 继续查找处理器
            handler = self.context.find_handler(exc.type_name, self.registry)
            if handler:
                self._execute_catch(handler, exc)
            else:
                self._propagate_to_parent(exc)
        else:
            # 到达顶层
            self._handle_uncaught()

    def _handle_uncaught(self) -> None:
        """处理未捕获异常"""
        finally_blocks = self.unwinder.unwind_to_top()

        # 执行所有 finally 块
        self.unwinder.execute_finally_blocks(finally_blocks)

        # 调用未捕获处理器
        self.context.handle_uncaught()

    def _bind_exception_variable(self, name: str, exc: ExceptionObject) -> None:
        """绑定异常变量

        这个方法可以被重写以支持不同的作用域绑定机制。

        Args:
            name: 变量名
            exc: 异常对象
        """
        # 默认实现只是存储在上下文中
        if not hasattr(self, "_bindings"):
            self._bindings: Dict[str, ExceptionObject] = {}
        self._bindings[name] = exc

    def get_binding(self, name: str) -> Optional[ExceptionObject]:
        """获取绑定的异常变量

        Args:
            name: 变量名

        Returns:
            异常对象
        """
        return getattr(self, "_bindings", {}).get(name)

    def push_frame(self, function_name: str, file_name: str, line_number: int) -> None:
        """记录函数入口

        Args:
            function_name: 函数名
            file_name: 文件名
            line_number: 行号
        """
        frame = StackFrameInfo(
            function_name=function_name, file_name=file_name, line_number=line_number
        )
        self.context.push_frame(frame)

    def pop_frame(self) -> None:
        """弹出函数栈帧"""
        self.context.pop_frame()

    def register_finally(self, handler: Callable) -> None:
        """注册 finally 块

        Args:
            handler: finally 处理函数
        """
        if self.context.stack_frames:
            frame = self.context.stack_frames[-1]
            frame.has_finally = True
            frame.finally_handler = handler

    def register_cleanup(self, cleanup: Callable) -> None:
        """注册清理处理器

        Args:
            cleanup: 清理函数
        """
        if self.context.stack_frames:
            frame = self.context.stack_frames[-1]
            frame.cleanup_handlers.append(cleanup)

    def enter_try(self, handlers: List[ExceptionHandler]) -> None:
        """进入 try 块

        Args:
            handlers: 异常处理器列表
        """
        for handler in handlers:
            self.context.register_handler(handler)

    def exit_try(self) -> None:
        """退出 try 块"""
        # 找到对应的 try 入口，注销所有处理器
        while self.context.handler_stack:
            handler = self.context.handler_stack[-1]
            self.context.unregister_handler()
            # 当注销了对应的 try 处理器时停止
            if handler.frame_index == len(self.context.stack_frames) - 1:
                break


# 便捷函数


def throw_exception(exc: ExceptionObject) -> None:
    """抛出异常（便捷函数）

    Args:
        exc: 异常对象
    """
    ExceptionPropagator.instance().throw(exc)


def rethrow_exception() -> None:
    """重新抛出异常（便捷函数）"""
    ExceptionPropagator.instance().rethrow()


def get_current_exception() -> Optional[ExceptionObject]:
    """获取当前异常

    Returns:
        当前异常对象
    """
    return ExceptionPropagator.instance().context.current_exception


# 导出公共符号
__all__ = [
    "StackUnwinder",
    "ExceptionPropagator",
    "throw_exception",
    "rethrow_exception",
    "get_current_exception",
]

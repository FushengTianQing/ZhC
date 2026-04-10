# -*- coding: utf-8 -*-
"""
协程支持模块 - Coroutine Support

提供协程和异步编程的核心数据结构：
1. CoroutineState - 协程状态枚举
2. CoroutineContext - 协程上下文
3. Coroutine - 协程对象
4. Channel - 通道（协程间通信）

Phase 5 - 函数式-协程支持

作者：ZHC 开发团队
日期：2026-04-10
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, Set
from enum import Enum
from datetime import datetime


class CoroutineState(Enum):
    """协程状态

    协程状态机：
    - CREATED: 创建（已创建但未启动）
    - RUNNING: 运行中（正在执行）
    - SUSPENDED: 暂停（主动让出执行权）
    - WAITING: 等待（等待 I/O 或其他协程）
    - COMPLETED: 完成（正常结束）
    - CANCELLED: 取消（被取消或有未处理异常）
    """

    CREATED = "created"  # 创建
    RUNNING = "running"  # 运行中
    SUSPENDED = "suspended"  # 暂停（yield）
    WAITING = "waiting"  # 等待（await）
    COMPLETED = "completed"  # 完成
    CANCELLED = "cancelled"  # 取消

    def __str__(self):
        return self.value


@dataclass
class CoroutineStackFrame:
    """协程栈帧

    表示协程执行过程中的一个函数调用栈帧。

    Attributes:
        function_name: 函数名
        return_address: 返回地址
        local_variables: 局部变量字典
        saved_registers: 保存的寄存器状态
    """

    function_name: str
    return_address: int = 0
    local_variables: Dict[str, Any] = field(default_factory=dict)
    saved_registers: List[Any] = field(default_factory=list)

    def __repr__(self):
        return f"StackFrame({self.function_name})"


@dataclass
class CoroutineContext:
    """协程上下文

    保存协程执行状态，包括栈帧和 upvalues。

    Attributes:
        stack: 栈帧列表
        current_frame: 当前栈帧
        upvalues: upvalue 字典
    """

    stack: List[CoroutineStackFrame] = field(default_factory=list)
    current_frame: Optional[CoroutineStackFrame] = None
    upvalues: Dict[str, Any] = field(default_factory=dict)

    def push_frame(self, frame: CoroutineStackFrame) -> None:
        """压入栈帧"""
        self.stack.append(frame)
        self.current_frame = frame

    def pop_frame(self) -> Optional[CoroutineStackFrame]:
        """弹出栈帧"""
        if self.stack:
            frame = self.stack.pop()
            self.current_frame = self.stack[-1] if self.stack else None
            return frame
        return None

    def __repr__(self):
        return f"CoroutineContext(frames={len(self.stack)})"


@dataclass
class Coroutine:
    """协程对象

    表示一个协程实例，包含协程的所有状态信息。

    Attributes:
        id: 协程 ID
        name: 协程名称
        function: 协程函数
        state: 当前状态
        context: 协程上下文
        result: 协程返回值
        exception: 协程异常
        created_at: 创建时间
        scheduled_count: 被调度次数
    """

    id: int
    name: str
    function: Callable
    state: CoroutineState
    context: CoroutineContext = field(default_factory=CoroutineContext)
    result: Optional[Any] = field(default=None)
    exception: Optional[Exception] = field(default=None)
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_count: int = 0

    def resume(self) -> Any:
        """恢复协程执行

        Returns:
            协程的执行结果

        Raises:
            RuntimeError: 如果协程状态不允许恢复
        """
        if self.state not in (
            CoroutineState.CREATED,
            CoroutineState.SUSPENDED,
            CoroutineState.WAITING,
        ):
            raise RuntimeError(f"Cannot resume coroutine in state {self.state}")
        self.state = CoroutineState.RUNNING
        self.scheduled_count += 1
        return self.result

    def suspend(self, value: Any = None) -> Any:
        """暂停协程执行

        Args:
            value: 暂停时传递的值

        Returns:
            传递的值
        """
        self.state = CoroutineState.SUSPENDED
        self.result = value
        return value

    def wait_for(self, condition: Any, timeout: Optional[float] = None) -> None:
        """等待条件满足

        Args:
            condition: 等待的条件
            timeout: 超时时间（秒）
        """
        self.state = CoroutineState.WAITING
        self.result = None

    def cancel(self, reason: Optional[str] = None) -> None:
        """取消协程

        Args:
            reason: 取消原因
        """
        self.state = CoroutineState.CANCELLED
        if reason:
            self.exception = RuntimeError(reason)

    def is_done(self) -> bool:
        """检查协程是否已结束"""
        return self.state in (
            CoroutineState.COMPLETED,
            CoroutineState.CANCELLED,
        )

    def complete(self, result: Any = None) -> None:
        """标记协程为完成

        Args:
            result: 协程结果
        """
        self.state = CoroutineState.COMPLETED
        self.result = result

    def __repr__(self):
        return f"Coroutine({self.id}, {self.name}, {self.state.value})"


@dataclass
class Channel:
    """通道 - 用于协程间通信

    支持有缓冲和无缓冲通道，提供 send/recv 操作。

    Attributes:
        id: 通道 ID
        element_type: 元素类型名
        buffer_size: 缓冲区大小（0 表示无缓冲）
        buffer: 缓冲区
        senders: 等待的发送者
        receivers: 等待的接收者
        closed: 是否已关闭
    """

    id: int
    element_type: str
    buffer_size: int = 0
    buffer: List[Any] = field(default_factory=list)
    senders: Set[Coroutine] = field(default_factory=set)
    receivers: Set[Coroutine] = field(default_factory=set)
    closed: bool = False

    def send(self, value: Any, sender: Coroutine) -> None:
        """发送值到通道

        Args:
            value: 要发送的值
            sender: 发送者协程

        Raises:
            RuntimeError: 如果通道已关闭
        """
        if self.closed:
            raise RuntimeError("Channel is closed")

        if len(self.buffer) >= self.buffer_size:
            # 缓冲区满，暂停发送者
            self.senders.add(sender)
            sender.suspend()
        else:
            self.buffer.append(value)
            self._wake_receiver()

    def recv(self, receiver: Coroutine) -> Any:
        """从通道接收值

        Args:
            receiver: 接收者协程

        Returns:
            接收到的值

        Raises:
            RuntimeError: 如果通道已关闭且为空
        """
        if self.closed and not self.buffer:
            raise RuntimeError("Channel is closed and empty")

        if not self.buffer:
            # 缓冲区空，暂停接收者
            self.receivers.add(receiver)
            receiver.suspend()
            return None

        value = self.buffer.pop(0)
        self._wake_sender()
        return value

    def close(self) -> None:
        """关闭通道"""
        self.closed = True
        # 唤醒所有等待的协程
        for coroutine in list(self.senders) + list(self.receivers):
            coroutine.resume()

    def _wake_receiver(self) -> None:
        """唤醒等待的接收者"""
        if self.receivers:
            receiver = self.receivers.pop()
            receiver.resume()

    def _wake_sender(self) -> None:
        """唤醒等待的发送者"""
        if self.senders:
            sender = self.senders.pop()
            sender.resume()

    def is_empty(self) -> bool:
        """检查通道是否为空"""
        return len(self.buffer) == 0

    def is_full(self) -> bool:
        """检查通道是否已满"""
        return len(self.buffer) >= self.buffer_size

    def __repr__(self):
        status = "closed" if self.closed else "open"
        return f"Channel({self.id}, {self.element_type}, buffer={len(self.buffer)}/{self.buffer_size}, {status})"


# 全局通道 ID 计数器
_channel_id_counter = 0


def next_channel_id() -> int:
    """获取下一个通道 ID"""
    global _channel_id_counter
    _channel_id_counter += 1
    return _channel_id_counter


__all__ = [
    "CoroutineState",
    "CoroutineStackFrame",
    "CoroutineContext",
    "Coroutine",
    "Channel",
    "next_channel_id",
]

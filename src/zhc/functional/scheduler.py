# -*- coding: utf-8 -*-
"""
协程调度器 - Coroutine Scheduler

提供协程的创建、启动、调度和管理功能。

Phase 5 - 函数式-协程支持

作者：ZHC 开发团队
日期：2026-04-10
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import logging

from .coroutine import (
    Coroutine,
    CoroutineState,
    CoroutineContext,
    Channel,
    next_channel_id,
)


logger = logging.getLogger(__name__)


@dataclass
class SchedulerStats:
    """调度器统计信息"""

    coroutines_created: int = 0
    coroutines_completed: int = 0
    coroutines_cancelled: int = 0
    total_scheduled: int = 0


class Scheduler:
    """协程调度器

    单例模式的协程调度器，负责管理所有协程的生命周期。

    Attributes:
        _instance: 单例实例
        coroutines: 协程字典（ID -> Coroutine）
        ready_queue: 就绪队列
        wait_queue: 等待队列（Coroutine -> 等待条件）
        channels: 通道字典（ID -> Channel）
        current: 当前运行的协程
        next_id: 下一个协程 ID
        stats: 统计信息
    """

    _instance: Optional["Scheduler"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.coroutines: Dict[int, Coroutine] = {}
        self.ready_queue: List[Coroutine] = []
        self.wait_queue: Dict[Coroutine, Any] = {}
        self.channels: Dict[int, Channel] = {}
        self.current: Optional[Coroutine] = None
        self.next_id: int = 1
        self.stats = SchedulerStats()

    @classmethod
    def instance(cls) -> "Scheduler":
        """获取调度器单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """重置调度器（用于测试）"""
        if cls._instance is not None:
            cls._instance._initialized = False
            cls._instance.coroutines.clear()
            cls._instance.ready_queue.clear()
            cls._instance.wait_queue.clear()
            cls._instance.channels.clear()
            cls._instance.current = None
            cls._instance.next_id = 1
            cls._instance.stats = SchedulerStats()
            cls._instance = None

    def create_coroutine(
        self, func: Callable, name: Optional[str] = None, *args, **kwargs
    ) -> Coroutine:
        """创建协程

        Args:
            func: 协程函数
            name: 协程名称（可选）
            *args: 协程函数参数
            **kwargs: 协程函数关键字参数

        Returns:
            创建的协程对象
        """
        coro = Coroutine(
            id=self.next_id,
            name=name or f"coro_{self.next_id}",
            function=func,
            state=CoroutineState.CREATED,
            context=CoroutineContext(),
        )
        self.coroutines[self.next_id] = coro
        self.next_id += 1
        self.stats.coroutines_created += 1

        logger.debug(f"Created coroutine {coro.id}: {coro.name}")
        return coro

    def start(self, coro: Coroutine) -> None:
        """启动协程

        Args:
            coro: 要启动的协程

        Raises:
            RuntimeError: 如果协程状态不是 CREATED
        """
        if coro.state != CoroutineState.CREATED:
            raise RuntimeError(f"Can only start created coroutine, got {coro.state}")

        coro.state = CoroutineState.RUNNING
        self.ready_queue.append(coro)

        logger.debug(f"Started coroutine {coro.id}: {coro.name}")

        # 如果没有当前运行的协程，开始调度
        if self.current is None:
            self.run()

    def resume(self, coro: Coroutine) -> Any:
        """恢复协程

        Args:
            coro: 要恢复的协程

        Returns:
            协程的执行结果
        """
        if coro.is_done():
            return coro.result

        coro.state = CoroutineState.RUNNING
        self.ready_queue.append(coro)

        logger.debug(f"Resumed coroutine {coro.id}: {coro.name}")

        if self.current != coro:
            self._switch_to(coro)

        return coro.result

    def suspend(self, coro: Coroutine, wait_for: Any = None) -> None:
        """挂起协程

        Args:
            coro: 要挂起的协程
            wait_for: 等待的条件（可选）
        """
        coro.state = (
            CoroutineState.SUSPENDED if wait_for is None else CoroutineState.WAITING
        )
        if wait_for is not None:
            self.wait_queue[coro] = wait_for

        logger.debug(f"Suspended coroutine {coro.id}: {coro.name}")

    def yield_control(self, coro: Coroutine, value: Any = None) -> Any:
        """协程主动让出控制权

        Args:
            coro: 要让出控制权的协程
            value: 让出时传递的值

        Returns:
            传递的值
        """
        coro.suspend(value)
        self.schedule()
        return value

    def schedule(self) -> Optional[Coroutine]:
        """调度下一个协程

        Returns:
            下一个要执行的协程，如果没有则返回 None
        """
        self.stats.total_scheduled += 1

        # 优先处理等待队列
        self._process_wait_queue()

        if self.ready_queue:
            return self.ready_queue.pop(0)
        return None

    def run(self) -> None:
        """运行调度器

        持续调度协程直到所有协程完成
        """
        logger.debug("Scheduler running...")

        while self.ready_queue or self.wait_queue:
            # 调度就绪协程
            coro = self.schedule()
            if coro:
                self.current = coro
                try:
                    # 执行协程
                    if coro.state == CoroutineState.RUNNING:
                        result = coro.function()
                        if result is not None:
                            coro.result = result
                        coro.complete()
                except Exception as e:
                    logger.error(f"Coroutine {coro.id} raised exception: {e}")
                    coro.exception = e
                    coro.state = CoroutineState.CANCELLED

                if coro.is_done():
                    self._on_coroutine_done(coro)
                elif coro.state == CoroutineState.SUSPENDED:
                    # 保持挂起状态，不放回就绪队列
                    pass
                else:
                    self.ready_queue.append(coro)

            # 处理等待队列
            self._process_wait_queue()

        self.current = None
        logger.debug("Scheduler finished")

    def _switch_to(self, target: Coroutine) -> None:
        """切换到目标协程

        Args:
            target: 目标协程
        """
        # 保存当前协程状态
        if self.current and self.current.state == CoroutineState.RUNNING:
            self.current.state = CoroutineState.SUSPENDED
            self.ready_queue.append(self.current)

        # 恢复目标协程状态
        target.state = CoroutineState.RUNNING
        self.current = target

    def _process_wait_queue(self) -> None:
        """处理等待队列"""
        for coro, condition in list(self.wait_queue.items()):
            if self._check_condition(condition):
                del self.wait_queue[coro]
                coro.state = CoroutineState.RUNNING
                self.ready_queue.append(coro)

    def _check_condition(self, condition) -> bool:
        """检查条件是否满足

        Args:
            condition: 要检查的条件

        Returns:
            条件是否满足
        """
        # 默认实现：始终返回 True
        # 子类可以重写此方法来实现更复杂的条件检查
        return True

    def _on_coroutine_done(self, coro: Coroutine) -> None:
        """协程完成回调

        Args:
            coro: 完成的协程
        """
        if coro.exception:
            logger.error(
                f"Coroutine {coro.id} ({coro.name}) failed with exception: {coro.exception}"
            )
            self.stats.coroutines_cancelled += 1
        else:
            logger.debug(
                f"Coroutine {coro.id} ({coro.name}) completed with result: {coro.result}"
            )
            self.stats.coroutines_completed += 1

        # 从协程字典中移除
        if coro.id in self.coroutines:
            del self.coroutines[coro.id]

    def create_channel(self, element_type: str, buffer_size: int = 0) -> Channel:
        """创建通道

        Args:
            element_type: 通道元素类型
            buffer_size: 缓冲区大小（0 表示无缓冲）

        Returns:
            创建的通道
        """
        channel = Channel(
            id=next_channel_id(),
            element_type=element_type,
            buffer_size=buffer_size,
        )
        self.channels[channel.id] = channel

        logger.debug(f"Created channel {channel.id}: {element_type}[{buffer_size}]")
        return channel

    def close_channel(self, channel: Channel) -> None:
        """关闭通道

        Args:
            channel: 要关闭的通道
        """
        channel.close()
        logger.debug(f"Closed channel {channel.id}")

    def get_coroutine(self, coro_id: int) -> Optional[Coroutine]:
        """获取协程

        Args:
            coro_id: 协程 ID

        Returns:
            协程对象，如果不存在则返回 None
        """
        return self.coroutines.get(coro_id)

    def get_channel(self, channel_id: int) -> Optional[Channel]:
        """获取通道

        Args:
            channel_id: 通道 ID

        Returns:
            通道对象，如果不存在则返回 None
        """
        return self.channels.get(channel_id)

    def get_stats(self) -> SchedulerStats:
        """获取调度器统计信息"""
        return self.stats

    def __repr__(self):
        return (
            f"Scheduler("
            f"coroutines={len(self.coroutines)}, "
            f"ready={len(self.ready_queue)}, "
            f"waiting={len(self.wait_queue)}, "
            f"channels={len(self.channels)})"
        )


# 全局调度器访问函数
def get_scheduler() -> Scheduler:
    """获取全局调度器实例"""
    return Scheduler.instance()

"""
性能剖析追踪器
"""

import threading
import functools
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass

from .data import (
    FunctionProfile,
    CallRelation,
    ProfilerStats,
    ProfilerConfig,
    ProfileEvent,
    ProfileEventType,
    get_time_ns,
)


@dataclass
class CallFrame:
    """调用栈帧"""

    function_name: str
    start_time_ns: int
    parent: Optional["CallFrame"] = None


class ProfilerTracker:
    """性能剖析追踪器

    用法示例：

    ```python
    from zhc.profiler import ProfilerTracker

    tracker = ProfilerTracker()
    tracker.start()

    # 追踪函数
    @tracker.profile
    def my_function():
        pass

    # 或使用上下文管理器
    with tracker.profile_scope("my_block"):
        pass

    tracker.stop()
    tracker.print_report()
    ```
    """

    def __init__(self, config: Optional[ProfilerConfig] = None):
        """初始化追踪器

        Args:
            config: 追踪器配置
        """
        self.config = config or ProfilerConfig()
        self.functions: Dict[str, FunctionProfile] = {}
        self.relations: Dict[tuple, CallRelation] = {}
        self.call_stack: List[CallFrame] = []
        self.stats = ProfilerStats()
        self._enabled = False
        self._lock = threading.Lock()
        self._events: List[ProfileEvent] = []
        self._max_events = 10000

    def start(self) -> None:
        """开始追踪"""
        with self._lock:
            if self._enabled:
                return
            self._enabled = True
            self.stats.start_time_ns = get_time_ns()

    def stop(self) -> None:
        """停止追踪"""
        with self._lock:
            if not self._enabled:
                return
            self._enabled = False
            self.stats.end_time_ns = get_time_ns()

    def reset(self) -> None:
        """重置追踪数据"""
        with self._lock:
            self.functions.clear()
            self.relations.clear()
            self.call_stack.clear()
            self.stats = ProfilerStats()
            self._events.clear()

    @property
    def is_enabled(self) -> bool:
        """是否正在追踪"""
        return self._enabled

    def enter(self, func_name: str) -> None:
        """进入函数（开始计时）"""
        if not self._enabled:
            return

        with self._lock:
            now = get_time_ns()

            # 获取或创建函数记录
            if func_name not in self.functions:
                self.functions[func_name] = FunctionProfile(
                    name=func_name,
                    min_time_ns=0xFFFFFFFFFFFFFFFF,
                )

            profile = self.functions[func_name]
            profile.call_count += 1
            profile.last_start_time_ns = now
            profile.call_depth = len(self.call_stack)

            # 记录调用关系和子函数
            if self.config.track_call_graph and self.call_stack:
                caller = self.call_stack[-1].function_name
                key = (caller, func_name)
                if key not in self.relations:
                    self.relations[key] = CallRelation(
                        caller=caller,
                        callee=func_name,
                    )
                self.relations[key].call_count += 1

                # 记录子函数关系
                parent_profile = self.functions.get(caller)
                if parent_profile and func_name not in parent_profile.children:
                    parent_profile.children.append(func_name)

            # 压入调用栈
            parent = self.call_stack[-1] if self.call_stack else None
            frame = CallFrame(func_name, now, parent)
            self.call_stack.append(frame)

            # 更新统计
            self.stats.total_calls += 1
            self.stats.function_count = len(self.functions)
            if len(self.call_stack) > self.stats.max_depth:
                self.stats.max_depth = len(self.call_stack)

            # 记录事件
            if len(self._events) < self._max_events:
                self._events.append(
                    ProfileEvent(
                        timestamp_ns=now,
                        event_type=ProfileEventType.ENTER,
                        function_name=func_name,
                        call_depth=len(self.call_stack) - 1,
                    )
                )

    def exit(self, func_name: str) -> None:
        """退出函数（结束计时）"""
        if not self._enabled:
            return

        with self._lock:
            # 弹出调用栈
            if not self.call_stack or self.call_stack[-1].function_name != func_name:
                return

            frame = self.call_stack.pop()
            now = get_time_ns()
            elapsed = now - frame.start_time_ns

            # 更新函数记录
            if func_name in self.functions:
                profile = self.functions[func_name]
                profile.total_time_ns += elapsed
                if elapsed < profile.min_time_ns:
                    profile.min_time_ns = elapsed
                if elapsed > profile.max_time_ns:
                    profile.max_time_ns = elapsed

                # 记录子函数
                if frame.parent:
                    parent_name = frame.parent.function_name
                    if parent_name not in profile.children:
                        profile.children.append(parent_name)

            # 更新调用关系时间
            if self.config.track_call_graph and self.call_stack:
                caller = self.call_stack[-1].function_name
                key = (caller, func_name)
                if key in self.relations:
                    self.relations[key].total_time_ns += elapsed

            # 更新统计
            self.stats.total_time_ns += elapsed

            # 记录事件
            if len(self._events) < self._max_events:
                self._events.append(
                    ProfileEvent(
                        timestamp_ns=now,
                        event_type=ProfileEventType.EXIT,
                        function_name=func_name,
                        call_depth=len(self.call_stack),
                    )
                )

    def profile(
        self, func: Optional[Callable] = None, *, name: Optional[str] = None
    ) -> Callable:
        """函数装饰器

        用法：
            @tracker.profile
            def my_func():
                pass

            # 或指定名称
            @tracker.profile(name="custom_name")
            def my_func():
                pass
        """

        def decorator(f: Callable) -> Callable:
            func_name = name or f.__name__

            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                self.enter(func_name)
                try:
                    return f(*args, **kwargs)
                finally:
                    self.exit(func_name)

            return wrapper

        if func is None:
            # 作为装饰器工厂使用：@tracker.profile(name="xxx")
            return decorator
        else:
            # 直接作为装饰器使用：@tracker.profile
            return decorator(func)

    def profile_scope(self, name: str):
        """代码块剖析上下文管理器

        用法：
            with tracker.profile_scope("my_block"):
                pass
        """
        return _ProfileScope(self, name)

    def get_function(self, name: str) -> Optional[FunctionProfile]:
        """获取函数记录"""
        return self.functions.get(name)

    def get_all_functions(self) -> List[FunctionProfile]:
        """获取所有函数记录"""
        return list(self.functions.values())

    def get_call_relations(self) -> List[CallRelation]:
        """获取所有调用关系"""
        return list(self.relations.values())

    def get_stats(self) -> ProfilerStats:
        """获取统计信息"""
        return self.stats

    def get_events(self) -> List[ProfileEvent]:
        """获取剖析事件列表"""
        return self._events.copy()

    def get_top_functions(self, n: int = 10) -> List[FunctionProfile]:
        """获取耗时最多的 N 个函数"""
        funcs = sorted(
            self.functions.values(), key=lambda f: f.total_time_ns, reverse=True
        )
        return funcs[:n]

    def get_call_tree(self) -> Dict[str, Any]:
        """获取调用树"""
        tree = {}

        for func_name, profile in self.functions.items():
            if profile.children:
                tree[func_name] = profile.children

        return tree


class _ProfileScope:
    """代码块剖析上下文管理器"""

    def __init__(self, tracker: ProfilerTracker, name: str):
        self.tracker = tracker
        self.name = name

    def __enter__(self):
        self.tracker.enter(self.name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tracker.exit(self.name)
        return False


# 全局追踪器实例
_global_tracker: Optional[ProfilerTracker] = None


def get_tracker() -> ProfilerTracker:
    """获取全局追踪器"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = ProfilerTracker()
    return _global_tracker


def profile_function(name: Optional[str] = None) -> Callable:
    """全局函数剖析装饰器

    用法：
        @profile_function()
        def my_func():
            pass
    """

    def decorator(func: Callable) -> Callable:
        func_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracker = get_tracker()
            tracker.enter(func_name)
            try:
                return func(*args, **kwargs)
            finally:
                tracker.exit(func_name)

        return wrapper

    return decorator


def profile_scope(name: str):
    """全局代码块剖析上下文管理器

    用法：
        with profile_scope("my_block"):
            pass
    """
    return get_tracker().profile_scope(name)

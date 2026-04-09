# -*- coding: utf-8 -*-
"""
ZhC 优化观察器

提供优化过程的监控和统计功能。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import logging

from zhc.optimization.pass_registry import PassResult

logger = logging.getLogger(__name__)


@dataclass
class OptimizationStats:
    """
    优化统计信息

    收集和汇总优化过程的统计数据。
    """

    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    # Pass 执行统计
    passes_run: List[str] = field(default_factory=list)
    passes_skipped: List[str] = field(default_factory=list)
    passes_failed: List[str] = field(default_factory=list)

    # 优化效果统计
    instructions_removed: int = 0
    instructions_added: int = 0
    functions_inlined: int = 0
    loops_unrolled: int = 0
    loops_vectorized: int = 0
    basic_blocks_merged: int = 0

    # 性能统计
    total_time_ms: float = 0.0
    pass_times_ms: Dict[str, float] = field(default_factory=dict)

    # 模块统计
    original_function_count: int = 0
    optimized_function_count: int = 0
    original_instruction_count: int = 0
    optimized_instruction_count: int = 0

    def add_pass_time(self, pass_name: str, time_ms: float) -> None:
        """添加 Pass 执行时间"""
        self.passes_run.append(pass_name)
        self.pass_times_ms[pass_name] = time_ms
        self.total_time_ms += time_ms

    def record_inline(self, count: int = 1) -> None:
        """记录内联操作"""
        self.functions_inlined += count

    def record_unroll(self, count: int = 1) -> None:
        """记录循环展开"""
        self.loops_unrolled += count

    def record_vectorize(self, count: int = 1) -> None:
        """记录循环向量化"""
        self.loops_vectorized += count

    def finish(self) -> None:
        """标记优化完成"""
        self.end_time = datetime.now()

    @property
    def duration_seconds(self) -> float:
        """优化耗时（秒）"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def optimization_ratio(self) -> float:
        """优化比率（原始指令数 / 优化后指令数）"""
        if self.optimized_instruction_count > 0:
            return self.original_instruction_count / self.optimized_instruction_count
        return 1.0

    def report(self) -> str:
        """生成优化报告"""
        lines = [
            "=" * 60,
            "Optimization Report",
            "=" * 60,
            f"Duration: {self.duration_seconds:.3f}s",
            f"Total Time: {self.total_time_ms:.2f}ms",
            "",
            "Pass Statistics:",
            f"  Passes Run: {len(self.passes_run)}",
            f"  Passes Skipped: {len(self.passes_skipped)}",
            f"  Passes Failed: {len(self.passes_failed)}",
            "",
            "Optimization Effects:",
            f"  Instructions Removed: {self.instructions_removed}",
            f"  Instructions Added: {self.instructions_added}",
            f"  Functions Inlined: {self.functions_inlined}",
            f"  Loops Unrolled: {self.loops_unrolled}",
            f"  Loops Vectorized: {self.loops_vectorized}",
            "",
            "Code Size:",
            f"  Original Instructions: {self.original_instruction_count}",
            f"  Optimized Instructions: {self.optimized_instruction_count}",
            f"  Optimization Ratio: {self.optimization_ratio:.2f}x",
            "",
            "Pass Times:",
        ]

        for pass_name, time_ms in sorted(
            self.pass_times_ms.items(), key=lambda x: x[1], reverse=True
        )[:10]:
            lines.append(f"  {pass_name}: {time_ms:.2f}ms")

        lines.append("=" * 60)
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "total_time_ms": self.total_time_ms,
            "passes_run": self.passes_run,
            "passes_skipped": self.passes_skipped,
            "passes_failed": self.passes_failed,
            "instructions_removed": self.instructions_removed,
            "instructions_added": self.instructions_added,
            "functions_inlined": self.functions_inlined,
            "loops_unrolled": self.loops_unrolled,
            "loops_vectorized": self.loops_vectorized,
            "original_instruction_count": self.original_instruction_count,
            "optimized_instruction_count": self.optimized_instruction_count,
            "optimization_ratio": self.optimization_ratio,
            "pass_times_ms": self.pass_times_ms,
        }


@dataclass
class OptimizationResult:
    """
    优化结果

    封装优化过程的最终结果。
    """

    module: Any  # 优化后的模块
    stats: OptimizationStats
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """优化是否成功"""
        return len(self.errors) == 0

    def add_error(self, message: str) -> None:
        """添加错误"""
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """添加警告"""
        self.warnings.append(message)


class OptimizationObserver:
    """
    优化观察器基类

    可以继承此类来监控优化过程。

    使用方式：
        class MyObserver(OptimizationObserver):
            def on_pass_complete(self, result, module):
                print(f"Pass {result.pass_name} completed")
                if result.changed:
                    print(f"  Changed: {result.changed}")

        observer = MyObserver()
        pm.add_observer(observer)
    """

    def on_pass_start(self, pass_name: str, module: Any) -> None:
        """Pass 开始执行"""
        pass

    def on_pass_complete(self, result: PassResult, module: Any) -> None:
        """Pass 完成执行"""
        pass

    def on_pass_error(self, result: PassResult) -> None:
        """Pass 执行出错"""
        pass

    def on_optimization_complete(self, module: Any, executions: Dict[str, Any]) -> None:
        """优化完成"""
        pass


class LoggingObserver(OptimizationObserver):
    """
    日志观察器

    将优化过程记录到日志。
    """

    def __init__(self, level: int = logging.INFO):
        self.logger = logging.getLogger("zhc.optimization")
        self.level = level
        self._pass_count = 0

    def on_pass_start(self, pass_name: str, module: Any) -> None:
        """记录 Pass 开始"""
        self._pass_count += 1
        self.logger.log(self.level, f"[{self._pass_count}] Starting pass: {pass_name}")

    def on_pass_complete(self, result: PassResult, module: Any) -> None:
        """记录 Pass 完成"""
        if result.changed:
            self.logger.log(
                self.level,
                f"[{self._pass_count}] Pass '{result.pass_name}' "
                f"changed module ({result.time_ms:.2f}ms)",
            )
        else:
            self.logger.log(
                self.level,
                f"[{self._pass_count}] Pass '{result.pass_name}' "
                f"no changes ({result.time_ms:.2f}ms)",
            )

    def on_pass_error(self, result: PassResult) -> None:
        """记录 Pass 出错"""
        self.logger.error(
            f"Pass '{result.pass_name}' failed: {result.error} "
            f"({result.time_ms:.2f}ms)"
        )


class StatsObserver(OptimizationObserver):
    """
    统计观察器

    收集优化统计数据。
    """

    def __init__(self):
        self.stats = OptimizationStats()

    def on_pass_complete(self, result: PassResult, module: Any) -> None:
        """记录 Pass 完成"""
        self.stats.add_pass_time(result.pass_name, result.time_ms)

        if not result.changed:
            self.stats.passes_skipped.append(result.pass_name)

        if result.error:
            self.stats.passes_failed.append(result.pass_name)

    def on_pass_error(self, result: PassResult) -> None:
        """记录 Pass 出错"""
        self.stats.passes_failed.append(result.pass_name)

    def get_stats(self) -> OptimizationStats:
        """获取统计信息"""
        return self.stats


class CallbackObserver(OptimizationObserver):
    """
    回调观察器

    支持通过回调函数处理优化事件。

    使用方式：
        observer = CallbackObserver()

        observer.on_pass_start = lambda name, m: print(f"Starting {name}")
        observer.on_pass_complete = lambda result, m: print(f"Completed {result.pass_name}")

        pm.add_observer(observer)
    """

    def __init__(self):
        self.on_pass_start: Optional[Callable] = None
        self.on_pass_complete: Optional[Callable] = None
        self.on_pass_error: Optional[Callable] = None
        self.on_optimization_complete: Optional[Callable] = None

    def on_pass_start(self, pass_name: str, module: Any) -> None:
        if self.on_pass_start:
            self.on_pass_start(pass_name, module)

    def on_pass_complete(self, result: PassResult, module: Any) -> None:
        if self.on_pass_complete:
            self.on_pass_complete(result, module)

    def on_pass_error(self, result: PassResult) -> None:
        if self.on_pass_error:
            self.on_pass_error(result)

    def on_optimization_complete(self, module: Any, executions: Dict[str, Any]) -> None:
        if self.on_optimization_complete:
            self.on_optimization_complete(module, executions)


class CompositeObserver(OptimizationObserver):
    """
    组合观察器

    将多个观察器组合在一起。

    使用方式：
        observer = CompositeObserver()
        observer.add(LoggingObserver())
        observer.add(StatsObserver())

        pm.add_observer(observer)
    """

    def __init__(self):
        self._observers: List[OptimizationObserver] = []

    def add(self, observer: OptimizationObserver) -> None:
        """添加观察器"""
        self._observers.append(observer)

    def remove(self, observer: OptimizationObserver) -> None:
        """移除观察器"""
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify_all(self, method_name: str, *args, **kwargs) -> None:
        """通知所有观察器"""
        for observer in self._observers:
            try:
                method = getattr(observer, method_name)
                method(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Observer {observer} error: {e}")

    def on_pass_start(self, pass_name: str, module: Any) -> None:
        self._notify_all("on_pass_start", pass_name, module)

    def on_pass_complete(self, result: PassResult, module: Any) -> None:
        self._notify_all("on_pass_complete", result, module)

    def on_pass_error(self, result: PassResult) -> None:
        self._notify_all("on_pass_error", result)

    def on_optimization_complete(self, module: Any, executions: Dict[str, Any]) -> None:
        self._notify_all("on_optimization_complete", module, executions)

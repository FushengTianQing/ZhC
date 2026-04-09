"""
内存使用追踪器
"""

import threading
import functools
import traceback
from typing import Dict, List, Optional, Callable

from .data import (
    MemBlock,
    MemStats,
    MemOpType,
    MemOpRecord,
    AllocSite,
    get_time_ns,
)


class MemTracker:
    """内存使用追踪器

    用法示例：

    ```python
    from zhc.memcheck import MemTracker

    tracker = MemTracker()
    tracker.start()

    # 追踪内存分配
    ptr = tracker.alloc(1024, "test.py", 10, "main")
    tracker.free(ptr, "test.py", 20)

    # 或使用装饰器
    @tracker.track_memory
    def my_function():
        data = [1] * 1000
        return data

    tracker.stop()
    tracker.print_report()
    ```
    """

    def __init__(self, max_history: int = 10000):
        """初始化追踪器

        Args:
            max_history: 最大历史记录数
        """
        self.max_history = max_history
        self.blocks: Dict[int, MemBlock] = {}
        self.operations: List[MemOpRecord] = []
        self.alloc_sites: Dict[tuple, AllocSite] = {}
        self.stats = MemStats()
        self._enabled = False
        self._lock = threading.Lock()
        self._current_id = 0

    def start(self) -> None:
        """开始追踪"""
        with self._lock:
            self._enabled = True

    def stop(self) -> None:
        """停止追踪"""
        with self._lock:
            self._enabled = False

    def reset(self) -> None:
        """重置追踪数据"""
        with self._lock:
            self.blocks.clear()
            self.operations.clear()
            self.alloc_sites.clear()
            self.stats = MemStats()
            self._current_id = 0

    @property
    def is_enabled(self) -> bool:
        """是否正在追踪"""
        return self._enabled

    def alloc(
        self,
        size: int,
        file: str,
        line: int,
        func: str,
    ) -> int:
        """记录内存分配

        Args:
            size: 分配大小
            file: 文件名
            line: 行号
            func: 函数名

        Returns:
            模拟的指针 ID
        """
        if not self._enabled:
            return 0

        with self._lock:
            now = get_time_ns()

            # 生成唯一指针 ID
            ptr = self._current_id + 1
            self._current_id = ptr

            # 创建内存块记录
            block = MemBlock(
                ptr=ptr,
                size=size,
                file=file,
                line=line,
                func=func,
                alloc_time=now,
                alloc_id=ptr,
            )

            self.blocks[ptr] = block

            # 更新统计
            self.stats.total_alloc_bytes += size
            self.stats.current_used_bytes += size
            self.stats.alloc_count += 1

            if self.stats.current_used_bytes > self.stats.peak_used_bytes:
                self.stats.peak_used_bytes = self.stats.current_used_bytes

            # 更新分配源统计
            site_key = (file, line, func)
            if site_key not in self.alloc_sites:
                self.alloc_sites[site_key] = AllocSite(
                    file=file,
                    line=line,
                    func=func,
                )

            site = self.alloc_sites[site_key]
            site.alloc_count += 1
            site.total_bytes += size
            site.current_bytes += size

            # 记录操作
            self._record_op(MemOpType.ALLOC, ptr, size, file, line, func, ptr)

            return ptr

    def free(
        self,
        ptr: int,
        file: str,
        line: int,
    ) -> bool:
        """记录内存释放

        Args:
            ptr: 指针 ID
            file: 文件名
            line: 行号

        Returns:
            是否成功
        """
        if not self._enabled:
            return False

        with self._lock:
            # 检查指针是否有效
            if ptr not in self.blocks:
                self.stats.invalid_free_count += 1
                self._record_op(MemOpType.FREE, ptr, 0, file, line, "free", 0)
                return False

            block = self.blocks[ptr]

            # 更新统计
            self.stats.total_free_bytes += block.size
            self.stats.current_used_bytes -= block.size
            self.stats.free_count += 1

            # 更新分配源统计
            site_key = (block.file, block.line, block.func)
            if site_key in self.alloc_sites:
                site = self.alloc_sites[site_key]
                if site.current_bytes >= block.size:
                    site.current_bytes -= block.size

            # 移除内存块
            del self.blocks[ptr]

            # 记录操作
            self._record_op(MemOpType.FREE, ptr, 0, file, line, "free", block.alloc_id)

            return True

    def realloc(
        self,
        ptr: int,
        new_size: int,
        file: str,
        line: int,
        func: str,
    ) -> int:
        """记录内存重新分配

        Args:
            ptr: 原指针 ID
            new_size: 新大小
            file: 文件名
            line: 行号
            func: 函数名

        Returns:
            新指针 ID
        """
        if not self._enabled:
            return 0

        with self._lock:
            if ptr == 0:
                return self.alloc(new_size, file, line, func)

            if new_size == 0:
                self.free(ptr, file, line)
                return 0

            # 检查原指针
            if ptr not in self.blocks:
                self.stats.invalid_free_count += 1
                return 0

            old_block = self.blocks[ptr]
            size_diff = new_size - old_block.size

            # 更新统计
            self.stats.total_alloc_bytes += max(0, size_diff)
            self.stats.total_free_bytes += max(0, -size_diff)
            self.stats.current_used_bytes += size_diff

            if self.stats.current_used_bytes > self.stats.peak_used_bytes:
                self.stats.peak_used_bytes = self.stats.current_used_bytes

            # 更新分配源统计
            site_key = (old_block.file, old_block.line, old_block.func)
            if site_key in self.alloc_sites:
                site = self.alloc_sites[site_key]
                site.total_bytes += max(0, size_diff)
                site.current_bytes += size_diff

            # 更新内存块
            old_block.size = new_size

            # 记录操作
            self._record_op(
                MemOpType.REALLOC, ptr, new_size, file, line, func, old_block.alloc_id
            )

            return ptr

    def _record_op(
        self,
        op_type: MemOpType,
        ptr: int,
        size: int,
        file: str,
        line: int,
        func: str,
        alloc_id: int,
    ) -> None:
        """记录操作"""
        if len(self.operations) >= self.max_history:
            self.operations.pop(0)

        self.operations.append(
            MemOpRecord(
                op_type=op_type,
                ptr=ptr,
                size=size,
                file=file,
                line=line,
                func=func,
                timestamp=get_time_ns(),
                alloc_id=alloc_id,
            )
        )

    def track_memory(self, func: Optional[Callable] = None) -> Callable:
        """内存追踪装饰器

        用法：
            @tracker.track_memory
            def my_func():
                pass
        """

        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                # 获取调用信息
                frame = traceback.extract_stack()[-2]
                file = frame.filename
                line = frame.lineno

                # 调用前分配
                ptr = self.alloc(0, file, line, f.__name__)

                try:
                    result = f(*args, **kwargs)
                    return result
                finally:
                    # 调用后释放
                    self.free(ptr, file, line)

            return wrapper

        if func is None:
            return decorator
        else:
            return decorator(func)

    def get_block(self, ptr: int) -> Optional[MemBlock]:
        """获取内存块信息"""
        return self.blocks.get(ptr)

    def get_all_blocks(self) -> List[MemBlock]:
        """获取所有内存块"""
        return list(self.blocks.values())

    def get_stats(self) -> MemStats:
        """获取统计信息"""
        stats = MemStats(
            total_alloc_bytes=self.stats.total_alloc_bytes,
            total_free_bytes=self.stats.total_free_bytes,
            current_used_bytes=self.stats.current_used_bytes,
            peak_used_bytes=self.stats.peak_used_bytes,
            alloc_count=self.stats.alloc_count,
            free_count=self.stats.free_count,
            leak_count=len(self.blocks),
            leak_bytes=sum(b.size for b in self.blocks.values()),
            invalid_free_count=self.stats.invalid_free_count,
            double_free_count=self.stats.double_free_count,
        )
        return stats

    def get_operations(self) -> List[MemOpRecord]:
        """获取操作记录"""
        return self.operations.copy()

    def get_alloc_sites(self) -> List[AllocSite]:
        """获取分配源统计"""
        return list(self.alloc_sites.values())

    def has_leaks(self) -> bool:
        """是否有内存泄漏"""
        return len(self.blocks) > 0

    def get_leak_count(self) -> int:
        """获取泄漏数量"""
        return len(self.blocks)

    def get_leak_bytes(self) -> int:
        """获取泄漏字节数"""
        return sum(b.size for b in self.blocks.values())

    def get_report(self, format: str = "text") -> str:
        """获取报告"""
        from .reporter import get_reporter

        reporter = get_reporter(format)
        return reporter.generate(self)


# 全局追踪器实例
_global_tracker: Optional[MemTracker] = None


def get_tracker() -> MemTracker:
    """获取全局追踪器"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = MemTracker()
    return _global_tracker


def track_alloc(size: int, file: str, line: int, func: str) -> int:
    """全局内存分配追踪"""
    return get_tracker().alloc(size, file, line, func)


def track_free(ptr: int, file: str, line: int) -> bool:
    """全局内存释放追踪"""
    return get_tracker().free(ptr, file, line)

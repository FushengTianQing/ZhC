#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调用栈追踪器 (CallStackTracer)

为内存泄漏检测提供调用栈追踪支持。
记录每次内存分配时的调用栈，以便在检测到泄漏时回溯到分配点。

作者: 阿福
日期: 2026-04-10
"""

import traceback
import threading
from typing import List, Optional, Dict
from dataclasses import dataclass, field


@dataclass
class StackFrame:
    """调用栈帧"""

    filename: str = ""
    line_number: int = 0
    function_name: str = ""
    text: str = ""

    def __str__(self) -> str:
        return (
            f'  文件 "{self.filename}", 行 {self.line_number}, 在 {self.function_name}'
        )


@dataclass
class CallStack:
    """调用栈快照"""

    frames: List[StackFrame] = field(default_factory=list)
    timestamp: float = 0.0
    alloc_ptr: int = 0
    alloc_size: int = 0

    def format(self, max_frames: int = 10) -> str:
        """格式化调用栈信息

        Args:
            max_frames: 最大显示帧数

        Returns:
            格式化的调用栈字符串
        """
        lines = [f"分配地址: {self.alloc_ptr}, 大小: {self.alloc_size} 字节"]
        shown = self.frames[:max_frames]
        for i, frame in enumerate(shown):
            lines.append(f"  #{i} {frame}")
        if len(self.frames) > max_frames:
            lines.append(f"  ... 省略 {len(self.frames) - max_frames} 帧")
        return "\n".join(lines)


class CallStackTracer:
    """调用栈追踪器

    在内存分配时捕获调用栈，用于泄漏检测时回溯分配位置。

    用法：
        tracer = CallStackTracer()

        # 在分配时记录调用栈
        stack_id = tracer.capture(alloc_ptr=0x1234, alloc_size=1024)

        # 获取调用栈信息
        stack = tracer.get_stack(stack_id)
        print(stack.format())

        # 清除已释放的记录
        tracer.release(alloc_ptr=0x1234)
    """

    def __init__(self, max_depth: int = 20, max_records: int = 10000):
        """初始化调用栈追踪器

        Args:
            max_depth: 最大栈深度
            max_records: 最大记录数量
        """
        self.max_depth = max_depth
        self.max_records = max_records
        self._stacks: Dict[int, CallStack] = {}
        self._ptr_to_stack: Dict[int, int] = {}  # alloc_ptr -> stack_id
        self._next_id: int = 1
        self._lock = threading.Lock()

    def capture(
        self, alloc_ptr: int = 0, alloc_size: int = 0, skip_frames: int = 2
    ) -> int:
        """捕获当前调用栈

        Args:
            alloc_ptr: 分配地址（用于关联）
            alloc_size: 分配大小
            skip_frames: 跳过的栈帧数量（跳过追踪器本身的调用）

        Returns:
            调用栈 ID
        """
        import time

        # 获取调用栈
        raw_stack = traceback.extract_stack()

        # 跳过追踪器本身的帧
        frames = []
        for frame in raw_stack[:-skip_frames]:
            sf = StackFrame(
                filename=frame.filename,
                line_number=frame.lineno,
                function_name=frame.name,
                text=frame.line or "",
            )
            frames.append(sf)

        # 限制深度
        if len(frames) > self.max_depth:
            frames = frames[-self.max_depth :]

        stack = CallStack(
            frames=frames,
            timestamp=time.time(),
            alloc_ptr=alloc_ptr,
            alloc_size=alloc_size,
        )

        with self._lock:
            stack_id = self._next_id
            self._next_id += 1

            self._stacks[stack_id] = stack

            if alloc_ptr:
                self._ptr_to_stack[alloc_ptr] = stack_id

            # 淘汰旧记录
            if len(self._stacks) > self.max_records:
                oldest_id = min(self._stacks.keys())
                old_stack = self._stacks.pop(oldest_id)
                if old_stack.alloc_ptr in self._ptr_to_stack:
                    del self._ptr_to_stack[old_stack.alloc_ptr]

        return stack_id

    def get_stack(self, stack_id: int) -> Optional[CallStack]:
        """获取调用栈

        Args:
            stack_id: 调用栈 ID

        Returns:
            CallStack 对象，不存在则返回 None
        """
        with self._lock:
            return self._stacks.get(stack_id)

    def get_stack_by_ptr(self, alloc_ptr: int) -> Optional[CallStack]:
        """通过分配地址获取调用栈

        Args:
            alloc_ptr: 分配地址

        Returns:
            CallStack 对象，不存在则返回 None
        """
        with self._lock:
            stack_id = self._ptr_to_stack.get(alloc_ptr)
            if stack_id:
                return self._stacks.get(stack_id)
            return None

    def release(self, alloc_ptr: int) -> bool:
        """释放分配记录（对应的内存已被释放）

        Args:
            alloc_ptr: 分配地址

        Returns:
            是否成功释放
        """
        with self._lock:
            stack_id = self._ptr_to_stack.pop(alloc_ptr, None)
            if stack_id:
                self._stacks.pop(stack_id, None)
                return True
            return False

    def get_all_stacks(self) -> List[CallStack]:
        """获取所有未释放的调用栈"""
        with self._lock:
            return list(self._stacks.values())

    def get_leak_stacks(self) -> List[CallStack]:
        """获取可能泄漏的调用栈（有关联分配地址的）"""
        with self._lock:
            return [s for s in self._stacks.values() if s.alloc_ptr != 0]

    def clear(self):
        """清空所有记录"""
        with self._lock:
            self._stacks.clear()
            self._ptr_to_stack.clear()

    def __len__(self) -> int:
        return len(self._stacks)


# 全局调用栈追踪器
_global_tracer: Optional[CallStackTracer] = None


def get_call_stack_tracer() -> CallStackTracer:
    """获取全局调用栈追踪器"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = CallStackTracer()
    return _global_tracer


# 测试
if __name__ == "__main__":
    print("=== 调用栈追踪器测试 ===")

    tracer = CallStackTracer()

    # 模拟内存分配
    ptr1 = 1001
    ptr2 = 1002

    sid1 = tracer.capture(alloc_ptr=ptr1, alloc_size=128)
    sid2 = tracer.capture(alloc_ptr=ptr2, alloc_size=256)

    # 查看调用栈
    stack1 = tracer.get_stack(sid1)
    if stack1:
        print(f"\n调用栈 1 (ptr={ptr1}):")
        print(stack1.format(max_frames=5))

    # 释放 ptr1
    tracer.release(ptr1)
    print(f"\n释放后追踪器记录数: {len(tracer)}")

    # 模拟泄漏
    leak_stacks = tracer.get_leak_stacks()
    print(f"泄漏调用栈数: {len(leak_stacks)}")
    for s in leak_stacks:
        print(f"  泄漏: ptr={s.alloc_ptr}, size={s.alloc_size}")

    print("\n=== 测试完成 ===")

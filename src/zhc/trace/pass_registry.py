# -*- coding: utf-8 -*-
"""
追踪 Pass 注册

将追踪探针注入到 IR 中。

作者：远
日期：2026-04-13
"""

from typing import List, Optional
from dataclasses import dataclass

from .schema import TraceRecord, TraceEvent, TraceEventType, TraceLevel, SourceLocation


@dataclass
class ProbePoint:
    """探针注入点"""

    function_name: str
    line: int
    event_type: TraceEventType
    var_name: Optional[str] = None
    value: Optional[str] = None


class TracePass:
    """
    追踪 Pass

    在 IR 中注入追踪探针。
    """

    def __init__(self, level: TraceLevel = TraceLevel.STANDARD):
        self.level = level
        self.record: Optional[TraceRecord] = None
        self.call_stack: List[int] = []  # 存储函数进入事件的ID

    def name(self) -> str:
        return "TracePass"

    def set_source(self, source_file: str) -> None:
        """设置源文件"""
        self.record = TraceRecord(source_file=source_file, trace_level=self.level)

    def enter_function(
        self, name: str, location: Optional[SourceLocation] = None
    ) -> int:
        """记录函数进入"""
        if self.record is None:
            return -1

        event = TraceEvent(
            id=0,
            type=TraceEventType.FUNC_ENTER,
            location=location,
            name=name,
            call_depth=len(self.call_stack),
        )

        event_id = self.record.add_event(event)
        self.call_stack.append(event_id)
        return event_id

    def exit_function(
        self,
        name: str,
        return_value: Optional[str] = None,
        location: Optional[SourceLocation] = None,
    ) -> int:
        """记录函数退出"""
        if self.record is None:
            return -1

        parent_id = self.call_stack.pop() if self.call_stack else None

        event = TraceEvent(
            id=0,
            type=TraceEventType.FUNC_EXIT,
            location=location,
            name=name,
            value=return_value,
            call_depth=len(self.call_stack),
            parent_id=parent_id,
        )

        return self.record.add_event(event)

    def assign_variable(
        self,
        name: str,
        value: str,
        value_type: Optional[str] = None,
        location: Optional[SourceLocation] = None,
    ) -> int:
        """记录变量赋值"""
        if self.record is None:
            return -1

        if self.level == TraceLevel.MINIMAL:
            return -1

        event = TraceEvent(
            id=0,
            type=TraceEventType.VAR_ASSIGN,
            location=location,
            name=name,
            value=value,
            value_type=value_type,
            call_depth=len(self.call_stack),
        )

        return self.record.add_event(event)

    def branch_taken(
        self, condition: str, taken: bool, location: Optional[SourceLocation] = None
    ) -> int:
        """记录分支"""
        if self.record is None:
            return -1

        event_type = (
            TraceEventType.BRANCH_TAKEN if taken else TraceEventType.BRANCH_SKIPPED
        )

        event = TraceEvent(
            id=0,
            type=event_type,
            location=location,
            name=condition,
            value="是" if taken else "否",
            call_depth=len(self.call_stack),
        )

        return self.record.add_event(event)

    def loop_iteration(
        self, iteration: int, location: Optional[SourceLocation] = None
    ) -> int:
        """记录循环迭代"""
        if self.record is None:
            return -1

        event = TraceEvent(
            id=0,
            type=TraceEventType.LOOP_ITER,
            location=location,
            value=str(iteration),
            call_depth=len(self.call_stack),
        )

        return self.record.add_event(event)

    def get_record(self) -> Optional[TraceRecord]:
        """获取追踪记录"""
        if self.record:
            self.record.compute_stats()
        return self.record


class TracePassManager:
    """
    追踪 Pass 管理器

    管理 TracePass 的生命周期。
    """

    def __init__(self, level: TraceLevel = TraceLevel.STANDARD):
        self.level = level
        self.pass_: TracePass = TracePass(level)

    def begin_trace(self, source_file: str) -> TracePass:
        """开始追踪"""
        self.pass_.set_source(source_file)
        return self.pass_

    def end_trace(self) -> TraceRecord:
        """结束追踪"""
        record = self.pass_.get_record()
        self.pass_ = TracePass(self.level)
        return record

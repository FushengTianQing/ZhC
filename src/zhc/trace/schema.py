# -*- coding: utf-8 -*-
"""
trace.json Schema 定义

定义执行追踪数据结构。

Schema 版本: 1.0.0

作者：远
日期：2026-04-13
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any
import json
import time


class TraceLevel(Enum):
    """追踪级别"""

    MINIMAL = "minimal"  # 仅函数调用
    STANDARD = "standard"  # 函数调用 + 变量赋值
    FULL = "full"  # 所有指令


class TraceEventType(Enum):
    """追踪事件类型"""

    # 函数事件
    FUNC_ENTER = "func_enter"
    FUNC_EXIT = "func_exit"
    FUNC_RETURN = "func_return"

    # 变量事件
    VAR_DECL = "var_decl"
    VAR_ASSIGN = "var_assign"
    VAR_READ = "var_read"

    # 控制流事件
    BRANCH_TAKEN = "branch_taken"
    BRANCH_SKIPPED = "branch_skipped"
    LOOP_ENTER = "loop_enter"
    LOOP_EXIT = "loop_exit"
    LOOP_ITER = "loop_iter"

    # 表达式事件
    EXPR_EVAL = "expr_eval"

    # 调用事件
    CALL_ENTER = "call_enter"
    CALL_EXIT = "call_exit"

    # 错误事件
    ERROR = "error"


@dataclass
class SourceLocation:
    """源码位置"""

    file: str
    line: int
    column: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TraceEvent:
    """单个追踪事件"""

    # 事件标识
    id: int  # 事件序号
    type: TraceEventType  # 事件类型

    # 源码位置
    location: Optional[SourceLocation] = None

    # 事件数据（根据类型不同）
    name: Optional[str] = None  # 函数名/变量名
    value: Optional[str] = None  # 当前值
    value_type: Optional[str] = None  # 值类型

    # 调用栈
    call_depth: int = 0  # 调用深度（用于缩进）
    parent_id: Optional[int] = None  # 父事件ID

    # 时间戳
    timestamp: float = field(default_factory=time.time)

    # 额外数据
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "id": self.id,
            "type": self.type.value,
            "call_depth": self.call_depth,
            "timestamp": self.timestamp,
        }

        if self.location:
            result["location"] = self.location.to_dict()
        if self.name:
            result["name"] = self.name
        if self.value is not None:
            result["value"] = self.value
        if self.value_type:
            result["value_type"] = self.value_type
        if self.parent_id is not None:
            result["parent_id"] = self.parent_id
        if self.extra:
            result["extra"] = self.extra

        return result


@dataclass
class TraceRecord:
    """
    完整的追踪记录

    对应一个 .zhc 文件的执行轨迹
    """

    # 元信息
    schema_version: str = "1.0.0"
    zhc_version: str = "6.0.0"
    source_file: str = ""
    trace_level: TraceLevel = TraceLevel.STANDARD
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))

    # 事件列表
    events: List[TraceEvent] = field(default_factory=list)

    # 统计信息
    stats: Dict[str, Any] = field(default_factory=dict)

    def add_event(self, event: TraceEvent) -> int:
        """添加事件，返回事件ID"""
        event.id = len(self.events)
        self.events.append(event)
        return event.id

    def compute_stats(self):
        """计算统计信息"""
        self.stats = {
            "total_events": len(self.events),
            "func_calls": sum(
                1
                for e in self.events
                if e.type in (TraceEventType.FUNC_ENTER, TraceEventType.CALL_ENTER)
            ),
            "var_assigns": sum(
                1 for e in self.events if e.type == TraceEventType.VAR_ASSIGN
            ),
            "branches": sum(
                1
                for e in self.events
                if e.type
                in (TraceEventType.BRANCH_TAKEN, TraceEventType.BRANCH_SKIPPED)
            ),
            "loops": sum(1 for e in self.events if e.type == TraceEventType.LOOP_ENTER),
            "max_call_depth": max((e.call_depth for e in self.events), default=0),
        }

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        self.compute_stats()
        return {
            "schema_version": self.schema_version,
            "zhc_version": self.zhc_version,
            "source_file": self.source_file,
            "trace_level": self.trace_level.value,
            "created_at": self.created_at,
            "stats": self.stats,
            "events": [e.to_dict() for e in self.events],
        }

    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraceRecord":
        """从字典创建"""
        record = cls(
            schema_version=data.get("schema_version", "1.0.0"),
            zhc_version=data.get("zhc_version", "6.0.0"),
            source_file=data.get("source_file", ""),
            trace_level=TraceLevel(data.get("trace_level", "standard")),
            created_at=data.get("created_at", ""),
        )

        for event_data in data.get("events", []):
            location = None
            if "location" in event_data:
                loc = event_data["location"]
                location = SourceLocation(
                    file=loc.get("file", ""),
                    line=loc.get("line", 0),
                    column=loc.get("column"),
                )

            event = TraceEvent(
                id=event_data.get("id", 0),
                type=TraceEventType(event_data.get("type", "expr_eval")),
                location=location,
                name=event_data.get("name"),
                value=event_data.get("value"),
                value_type=event_data.get("value_type"),
                call_depth=event_data.get("call_depth", 0),
                parent_id=event_data.get("parent_id"),
                timestamp=event_data.get("timestamp", time.time()),
                extra=event_data.get("extra", {}),
            )
            record.events.append(event)

        return record


# trace.json Schema 文档
TRACE_SCHEMA = """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ZHC 执行追踪数据",
  "type": "object",
  "required": ["schema_version", "events"],
  "properties": {
    "schema_version": {
      "type": "string",
      "const": "1.0.0"
    },
    "zhc_version": {
      "type": "string"
    },
    "source_file": {
      "type": "string"
    },
    "trace_level": {
      "type": "string",
      "enum": ["minimal", "standard", "full"]
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "stats": {
      "type": "object",
      "properties": {
        "total_events": { "type": "integer" },
        "func_calls": { "type": "integer" },
        "var_assigns": { "type": "integer" },
        "branches": { "type": "integer" },
        "loops": { "type": "integer" },
        "max_call_depth": { "type": "integer" }
      }
    },
    "events": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "type", "call_depth", "timestamp"],
        "properties": {
          "id": { "type": "integer" },
          "type": {
            "type": "string",
            "enum": [
              "func_enter", "func_exit", "func_return",
              "var_decl", "var_assign", "var_read",
              "branch_taken", "branch_skipped",
              "loop_enter", "loop_exit", "loop_iter",
              "expr_eval", "call_enter", "call_exit", "error"
            ]
          },
          "location": {
            "type": "object",
            "properties": {
              "file": { "type": "string" },
              "line": { "type": "integer" },
              "column": { "type": "integer" }
            }
          },
          "name": { "type": "string" },
          "value": { "type": "string" },
          "value_type": { "type": "string" },
          "call_depth": { "type": "integer" },
          "parent_id": { "type": "integer" },
          "timestamp": { "type": "number" },
          "extra": { "type": "object" }
        }
      }
    }
  }
}
"""

# -*- coding: utf-8 -*-
"""
ZHC IR - 异常处理节点定义

定义 try-catch 异常处理机制的 IR 节点。

作者：远
日期：2026-04-10
"""

from typing import List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class IRCatchHandler:
    """
    catch 处理器 IR

    Attributes:
        exception_type: 异常类型（用于类型匹配）
        variable_name: 异常变量名（捕获后绑定）
        body: 处理语句列表
        handler_label: 处理器的 IR 标签
    """

    exception_type: str  # 异常类型名称，如 "除零错误", "空指针错误"
    variable_name: str  # 异常变量名，如 "e"
    body: List[Any] = field(default_factory=list)  # 处理语句
    handler_label: str = ""  # 处理器标签，如 "catch_0"


@dataclass
class IRTryBlock:
    """
    try 块 IR

    Attributes:
        body: try 块内的语句列表
        catch_handlers: catch 处理器列表
        finally_block: finally 块（可选）
        finally_label: finally 块的标签
        try_label: try 块的标签
        exception_var: 异常对象变量名
    """

    body: List[Any] = field(default_factory=list)  # try 块内的语句
    catch_handlers: List[IRCatchHandler] = field(
        default_factory=list
    )  # catch 处理器列表
    finally_block: Optional[List[Any]] = None  # finally 块
    finally_label: str = ""  # finally 块标签
    try_label: str = ""  # try 块标签
    exception_var: str = "__exception"  # 异常对象变量名


@dataclass
class IRThrow:
    """
    throw 表达式 IR

    Attributes:
        exception: 异常对象（可以是 IRValue 或异常类型名）
        exception_type: 异常类型（可选，用于类型匹配）
        message: 异常消息（可选）
    """

    exception: Any  # 异常对象
    exception_type: Optional[str] = None  # 异常类型
    message: str = ""  # 异常消息


@dataclass
class IRExceptionContext:
    """
    异常上下文 IR

    管理一个函数或模块内的异常处理状态。

    Attributes:
        current_exception: 当前抛出的异常
        active_handlers: 当前激活的异常处理器栈
        landing_pads: landingpad 指令列表
        has_finally: 是否有 finally 块
    """

    current_exception: Optional[str] = None  # 当前异常变量
    active_handlers: List[str] = field(default_factory=list)  # 激活的处理器标签栈
    landing_pads: List[Any] = field(default_factory=list)  # landingpad 指令
    has_finally: bool = False  # 是否有 finally 块


@dataclass
class IRLandingPad:
    """
    landingpad 指令 IR

    用于 LLVM EH (Exception Handling) 机制。

    Attributes:
        result_type: 结果类型
        personality: personality 函数
        clauses: landingpad 子句列表
        result_var: 结果变量名
    """

    result_type: str = "i8*"  # 结果类型（通常是 i8*）
    personality: str = "__zhc_personality"  # personality 函数
    clauses: List[Any] = field(default_factory=list)  # 子句列表
    result_var: str = ""  # 结果变量名


@dataclass
class IRInvoke:
    """
    invoke 指令 IR

    调用函数并在异常时跳转到处理器。

    Attributes:
        function: 被调用的函数
        arguments: 参数列表
        normal_dest: 正常返回目标块
        unwind_dest: 异常跳转目标块
        result_var: 结果变量名
    """

    function: str  # 函数名
    arguments: List[Any] = field(default_factory=list)  # 参数列表
    normal_dest: str = ""  # 正常返回目标块
    unwind_dest: str = ""  # 异常跳转目标块（landingpad）
    result_var: str = ""  # 结果变量名


class ExceptionTableEntry:
    """
    异常表条目

    Attributes:
        try_start: try 块开始位置
        try_end: try 块结束位置
        handler: 处理器位置
        exception_type: 异常类型（0 表示所有异常）
        filter: 过滤器表达式
    """

    def __init__(
        self,
        try_start: int,
        try_end: int,
        handler: int,
        exception_type: int = 0,
        filter: str = "",
    ):
        self.try_start = try_start
        self.try_end = try_end
        self.handler = handler
        self.exception_type = exception_type
        self.filter = filter


class ExceptionTable:
    """
    异常表

    管理一个函数内的所有异常表条目。

    Attributes:
        entries: 异常表条目列表
    """

    def __init__(self):
        self.entries: List[ExceptionTableEntry] = []

    def add_entry(
        self,
        try_start: int,
        try_end: int,
        handler: int,
        exception_type: int = 0,
        filter: str = "",
    ):
        """添加异常表条目"""
        entry = ExceptionTableEntry(try_start, try_end, handler, exception_type, filter)
        self.entries.append(entry)

    def get_table_size(self) -> int:
        """获取异常表大小"""
        return len(self.entries)


__all__ = [
    "IRCatchHandler",
    "IRTryBlock",
    "IRThrow",
    "IRExceptionContext",
    "IRLandingPad",
    "IRInvoke",
    "ExceptionTableEntry",
    "ExceptionTable",
]

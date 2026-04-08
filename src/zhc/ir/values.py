# -*- coding: utf-8 -*-
"""
ZHC IR - IR 值定义

定义 ZHC IR 中的值类型（常量、临时变量、参数、全局变量等）。

作者：远
日期：2026-04-03
"""

from enum import Enum
from typing import Optional, Any


class ValueKind(Enum):
    """IR 值的种类"""

    CONST = "const"  # 常量（字面量）
    TEMP = "temp"  # 临时变量（编译器生成）
    VAR = "var"  # 用户变量
    PARAM = "param"  # 函数参数
    GLOBAL = "global"  # 全局变量
    LABEL = "label"  # 基本块标签
    FUNCTION = "function"  # 函数地址


class IRValue:
    """
    ZHC IR 中的值

    Attributes:
        name: 值名称（如 %0, @x, 42）
        ty: 类型（中文类型名，如"整数型"）
        kind: 值的种类
        const_value: 常量值（仅当 kind==CONST 时）
    """

    def __init__(
        self,
        name: str,
        ty: Optional[str] = None,
        kind: ValueKind = ValueKind.VAR,
        const_value: Any = None,
    ):
        self.name = name
        self.ty = ty
        self.kind = kind
        self.const_value = const_value

    def __repr__(self) -> str:
        if self.kind == ValueKind.CONST:
            return f"{self.name} ({self.const_value!r})"
        return f"{self.name}"

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other) -> bool:
        if not isinstance(other, IRValue):
            return False
        return self.name == other.name and self.kind == other.kind

    def __hash__(self) -> int:
        return hash((self.name, self.kind))

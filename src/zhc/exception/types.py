# -*- coding: utf-8 -*-
"""
异常类型系统 - 核心数据类型定义

定义异常类型、异常字段、异常对象等核心数据结构。

作者：远
日期：2026-04-10
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class ExceptionField:
    """
    异常字段定义

    Attributes:
        name: 字段名称
        type_name: 字段类型名称（如 "整数型", "字符串"）
        default_value: 默认值（可选）
    """

    name: str
    type_name: str
    default_value: Optional[Any] = None


@dataclass
class ExceptionType:
    """
    异常类型定义

    表示一个异常类型的元数据，包括名称、继承关系、字段和方法。

    Attributes:
        name: 类型名称（如 "除零异常", "空指针异常"）
        base_class: 父类名称（None 表示基类）
        fields: 字段列表
        methods: 方法名 -> 方法签名 字典
        error_code: 关联的错误码（可选）
        is_builtin: 是否为内置类型
        description: 类型描述
    """

    name: str
    base_class: Optional[str]
    fields: List[ExceptionField] = field(default_factory=list)
    methods: Dict[str, str] = field(default_factory=dict)
    error_code: Optional[str] = None
    is_builtin: bool = False
    description: str = ""

    def is_subtype_of(
        self, other: str, registry: Optional["ExceptionRegistry"] = None
    ) -> bool:
        """
        检查是否为某类型的子类型

        Args:
            other: 目标类型名称
            registry: 异常类型注册表（如果提供则进行递归检查）

        Returns:
            如果 self 是 other 的子类型返回 True
        """
        if self.name == other:
            return True

        if self.base_class is None:
            return False

        # 如果提供了注册表，进行递归检查
        if registry is not None:
            base_type = registry.lookup(self.base_class)
            if base_type is not None:
                return base_type.is_subtype_of(other, registry)

        return self.base_class == other

    def get_all_fields(
        self, registry: Optional["ExceptionRegistry"] = None
    ) -> List[ExceptionField]:
        """
        获取所有字段（包括从父类继承的字段）

        Args:
            registry: 异常类型注册表

        Returns:
            所有字段列表
        """
        all_fields = list(self.fields)

        if self.base_class and registry:
            base_type = registry.lookup(self.base_class)
            if base_type:
                all_fields = base_type.get_all_fields(registry) + all_fields

        return all_fields

    def get_field(self, name: str) -> Optional[ExceptionField]:
        """
        根据名称查找字段

        Args:
            name: 字段名称

        Returns:
            字段定义，如果不存在返回 None
        """
        for field in self.fields:
            if field.name == name:
                return field
        return None


@dataclass
class ExceptionObject:
    """
    异常对象实例

    表示运行时抛出的一个具体异常对象。

    Attributes:
        type_name: 异常类型名称
        message: 错误消息
        error_code: 错误码
        cause: 原因异常（另一个异常）
        stack_trace: 堆栈跟踪信息列表
        fields: 字段名 -> 字段值 字典
    """

    type_name: str
    message: str
    error_code: Optional[int] = None
    cause: Optional["ExceptionObject"] = None
    stack_trace: List[str] = field(default_factory=list)
    fields: Dict[str, Any] = field(default_factory=dict)

    def get_field(self, name: str) -> Any:
        """
        获取字段值

        Args:
            name: 字段名称

        Returns:
            字段值，如果不存在返回 None
        """
        return self.fields.get(name)

    def set_field(self, name: str, value: Any) -> None:
        """
        设置字段值

        Args:
            name: 字段名称
            value: 字段值
        """
        self.fields[name] = value

    def add_stack_frame(self, frame: str) -> None:
        """
        添加堆栈帧信息

        Args:
            frame: 堆栈帧描述
        """
        self.stack_trace.append(frame)

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典表示

        Returns:
            字典形式表示
        """
        result = {
            "type_name": self.type_name,
            "message": self.message,
        }
        if self.error_code is not None:
            result["error_code"] = self.error_code
        if self.cause:
            result["cause"] = self.cause.to_dict()
        if self.stack_trace:
            result["stack_trace"] = self.stack_trace
        if self.fields:
            result["fields"] = self.fields
        return result


@dataclass
class ExceptionThrowInfo:
    """
    异常抛出信息

    用于在编译时记录异常抛出相关信息。

    Attributes:
        throw_stmt: 抛出语句节点
        exception_type: 异常类型名称
        is_rethrow: 是否为重新抛出
    """

    exception_type: Optional[str] = None
    is_rethrow: bool = False


# 类型别名
ExceptionRegistry = Any  # 前向引用，避免循环导入


__all__ = [
    "ExceptionField",
    "ExceptionType",
    "ExceptionObject",
    "ExceptionThrowInfo",
]

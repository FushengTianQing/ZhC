# -*- coding: utf-8 -*-
"""
ZhC 反射 - 核心数据结构

提供运行时类型信息的核心数据结构和类型注册表。
复用 type_system/struct_layout.py 中的 StructMember/StructLayout 设计。

设计原则：
- 与现有 type_system 结构兼容
- 支持序列化（to_dict / from_dict）
- 类型注册表是编译期 + 运行时共享的

作者：远
日期：2026-04-11
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ReflectionFieldInfo:
    """反射字段信息

    复用 type_system.StructMember 的设计理念，
    增加反射特有的属性（访问修饰符、静态/常量标记等）。
    """

    name: str  # 字段名
    type_name: str  # 类型名（ZhC 类型名，如 "整数型"）
    offset: int  # 内存偏移量（字节）
    size: int  # 字段大小（字节）
    alignment: int = 4  # 对齐要求
    is_public: bool = True  # 是否公开
    is_static: bool = False  # 是否静态
    is_const: bool = False  # 是否常量

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "name": self.name,
            "type": self.type_name,
            "offset": self.offset,
            "size": self.size,
            "alignment": self.alignment,
            "is_public": self.is_public,
            "is_static": self.is_static,
            "is_const": self.is_const,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReflectionFieldInfo":
        """从字典反序列化"""
        return cls(
            name=data.get("name", ""),
            type_name=data.get("type", data.get("type_name", "")),
            offset=data.get("offset", 0),
            size=data.get("size", 0),
            alignment=data.get("alignment", 4),
            is_public=data.get("is_public", True),
            is_static=data.get("is_static", False),
            is_const=data.get("is_const", False),
        )


@dataclass
class ReflectionMethodInfo:
    """反射方法信息"""

    name: str  # 方法名
    return_type: str  # 返回类型（ZhC 类型名）
    params: List[Dict[str, str]] = field(default_factory=list)
    # [{"name": "x", "type": "整数型"}, ...]
    is_static: bool = False  # 是否静态
    is_virtual: bool = False  # 是否虚函数
    vtable_index: Optional[int] = None  # 虚表索引

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "name": self.name,
            "return_type": self.return_type,
            "params": self.params,
            "is_static": self.is_static,
            "is_virtual": self.is_virtual,
            "vtable_index": self.vtable_index,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReflectionMethodInfo":
        """从字典反序列化"""
        return cls(
            name=data.get("name", ""),
            return_type=data.get("return_type", "空型"),
            params=data.get("params", []),
            is_static=data.get("is_static", False),
            is_virtual=data.get("is_virtual", False),
            vtable_index=data.get("vtable_index"),
        )


@dataclass
class ReflectionTypeInfo:
    """反射类型信息

    包含一个类型的完整元信息，用于运行时查询。
    与 type_system.StructLayout 对齐，但增加了方法、继承等信息。
    """

    name: str  # 类型名
    size: int  # 类型大小（字节）
    alignment: int = 4  # 对齐要求
    # 类型分类
    is_class: bool = False  # 是否类
    is_struct: bool = False  # 是否结构体
    is_union: bool = False  # 是否共用体
    is_enum: bool = False  # 是否枚举
    is_primitive: bool = False  # 是否基本类型
    # 继承
    base_class: Optional[str] = None  # 父类名
    interfaces: List[str] = field(default_factory=list)  # 接口列表
    # 成员
    fields: List[ReflectionFieldInfo] = field(default_factory=list)
    methods: List[ReflectionMethodInfo] = field(default_factory=list)
    # 常量（枚举值等）
    constants: Dict[str, Any] = field(default_factory=dict)

    def get_field(self, name: str) -> Optional[ReflectionFieldInfo]:
        """按名称查找字段"""
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def get_method(self, name: str) -> Optional[ReflectionMethodInfo]:
        """按名称查找方法"""
        for m in self.methods:
            if m.name == name:
                return m
        return None

    def get_field_names(self) -> List[str]:
        """获取所有字段名"""
        return [f.name for f in self.fields]

    def get_method_names(self) -> List[str]:
        """获取所有方法名"""
        return [m.name for m in self.methods]

    def is_assignable_from(self, other: "ReflectionTypeInfo") -> bool:
        """检查是否可以从 other 类型赋值给 self 类型（继承关系）"""
        if self.name == other.name:
            return True
        # 检查继承关系
        if other.base_class:
            base_info = TypeRegistry.lookup(other.base_class)
            if base_info:
                return self.is_assignable_from(base_info)
        return False

    def get_ancestors(self) -> List[str]:
        """获取所有祖先类型名称（从父类到根类）"""
        ancestors: List[str] = []
        current = self.base_class
        visited: set = set()  # 防止循环继承
        while current and current not in visited:
            ancestors.append(current)
            visited.add(current)
            parent_info = TypeRegistry.lookup(current)
            if parent_info:
                current = parent_info.base_class
            else:
                break
        return ancestors

    def implements_interface(self, interface_name: str) -> bool:
        """检查是否实现了指定接口"""
        # 直接接口
        if interface_name in self.interfaces:
            return True
        # 通过继承的接口
        for ancestor_name in self.get_ancestors():
            ancestor_info = TypeRegistry.lookup(ancestor_name)
            if ancestor_info and interface_name in ancestor_info.interfaces:
                return True
        # 检查接口的接口（接口继承）
        for iface_name in self.interfaces:
            iface_info = TypeRegistry.lookup(iface_name)
            if iface_info and iface_info.implements_interface(interface_name):
                return True
        return False

    def get_mro(self) -> List[str]:
        """获取方法解析顺序 (Method Resolution Order)

        返回从当前类型到根类型的类型名列表，包含自身。
        """
        mro = [self.name]
        mro.extend(self.get_ancestors())
        return mro

    def is_instance_of(self, type_name: str) -> bool:
        """检查此类型是否是指定类型的实例（含继承/接口关系）"""
        if self.name == type_name:
            return True
        # 检查继承链
        if type_name in self.get_ancestors():
            return True
        # 检查接口
        return self.implements_interface(type_name)

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "name": self.name,
            "size": self.size,
            "alignment": self.alignment,
            "is_class": self.is_class,
            "is_struct": self.is_struct,
            "is_union": self.is_union,
            "is_enum": self.is_enum,
            "is_primitive": self.is_primitive,
            "base_class": self.base_class,
            "interfaces": self.interfaces,
            "fields": [f.to_dict() for f in self.fields],
            "methods": [m.to_dict() for m in self.methods],
            "constants": self.constants,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReflectionTypeInfo":
        """从字典反序列化"""
        fields = [ReflectionFieldInfo.from_dict(f) for f in data.get("fields", [])]
        methods = [ReflectionMethodInfo.from_dict(m) for m in data.get("methods", [])]
        return cls(
            name=data.get("name", ""),
            size=data.get("size", 0),
            alignment=data.get("alignment", 4),
            is_class=data.get("is_class", False),
            is_struct=data.get("is_struct", False),
            is_union=data.get("is_union", False),
            is_enum=data.get("is_enum", False),
            is_primitive=data.get("is_primitive", False),
            base_class=data.get("base_class"),
            interfaces=data.get("interfaces", []),
            fields=fields,
            methods=methods,
            constants=data.get("constants", {}),
        )


class TypeRegistry:
    """类型注册表

    编译期注册所有类型的元信息，运行时用于查询。
    线程安全（假设编译期单线程注册，运行时只读）。
    """

    _types: Dict[str, ReflectionTypeInfo] = {}

    @classmethod
    def register(cls, type_info: ReflectionTypeInfo) -> None:
        """注册类型信息"""
        cls._types[type_info.name] = type_info

    @classmethod
    def lookup(cls, name: str) -> Optional[ReflectionTypeInfo]:
        """按名称查找类型"""
        return cls._types.get(name)

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """检查类型是否已注册"""
        return name in cls._types

    @classmethod
    def get_all_types(cls) -> List[ReflectionTypeInfo]:
        """获取所有已注册类型"""
        return list(cls._types.values())

    @classmethod
    def get_subclasses(cls, base_name: str) -> List[ReflectionTypeInfo]:
        """获取指定基类的所有直接子类"""
        return [t for t in cls._types.values() if t.base_class == base_name]

    @classmethod
    def get_all_subclasses(cls, base_name: str) -> List[ReflectionTypeInfo]:
        """获取指定基类的所有子类（递归）"""
        result = []
        direct = cls.get_subclasses(base_name)
        for sub in direct:
            result.append(sub)
            result.extend(cls.get_all_subclasses(sub.name))
        return result

    @classmethod
    def clear(cls) -> None:
        """清空注册表（用于测试）"""
        cls._types.clear()

    @classmethod
    def register_primitive_types(cls) -> None:
        """注册基本类型"""
        primitives = [
            ("整数型", 4, 4),
            ("字符型", 1, 1),
            ("浮点型", 4, 4),
            ("双精度浮点型", 8, 8),
            ("逻辑型", 1, 1),
            ("长整数型", 8, 8),
            ("短整数型", 2, 2),
            ("空型", 0, 1),
            ("字符串型", 8, 8),  # 指针大小
        ]
        for name, size, alignment in primitives:
            cls.register(
                ReflectionTypeInfo(
                    name=name,
                    size=size,
                    alignment=alignment,
                    is_primitive=True,
                )
            )


# ==================== 公共 API ====================


def register_type(
    name: str,
    size: int = 0,
    alignment: int = 4,
    *,
    is_class: bool = False,
    is_struct: bool = False,
    is_union: bool = False,
    is_enum: bool = False,
    is_primitive: bool = False,
    base_class: Optional[str] = None,
    fields: Optional[List[ReflectionFieldInfo]] = None,
    methods: Optional[List[ReflectionMethodInfo]] = None,
) -> ReflectionTypeInfo:
    """便捷函数：注册类型"""
    info = ReflectionTypeInfo(
        name=name,
        size=size,
        alignment=alignment,
        is_class=is_class,
        is_struct=is_struct,
        is_union=is_union,
        is_enum=is_enum,
        is_primitive=is_primitive,
        base_class=base_class,
        fields=fields or [],
        methods=methods or [],
    )
    TypeRegistry.register(info)
    return info


def get_type_info(type_name: str) -> Optional[ReflectionTypeInfo]:
    """获取类型信息"""
    return TypeRegistry.lookup(type_name)


def get_type_name(type_name: str) -> str:
    """获取类型名称（如果已注册）"""
    info = TypeRegistry.lookup(type_name)
    return info.name if info else type_name


def get_type_size(type_name: str) -> int:
    """获取类型大小"""
    info = TypeRegistry.lookup(type_name)
    return info.size if info else 0


# 导出公共 API
__all__ = [
    "ReflectionFieldInfo",
    "ReflectionMethodInfo",
    "ReflectionTypeInfo",
    "TypeRegistry",
    "register_type",
    "get_type_info",
    "get_type_name",
    "get_type_size",
]

# -*- coding: utf-8 -*-
"""
ZhC 反射 - 运行时类型检查器

提供类型兼容性检查、继承关系验证、接口实现检查。

设计原则：
- 复用 TypeRegistry 中已注册的 ReflectionTypeInfo
- 支持多态类型检查（继承链 + 接口）
- 与 C 运行时 zhc_type_check.h 的查询逻辑一致

作者：远
日期：2026-04-11
"""

from typing import Optional, Set, List

from .type_info import TypeRegistry


class TypeHierarchy:
    """类型层次结构查询

    基于 TypeRegistry 中已注册的类型信息，提供继承关系查询。
    不维护额外的状态，所有查询通过 TypeRegistry 进行。
    """

    @staticmethod
    def get_parent(type_name: str) -> Optional[str]:
        """获取直接父类名称"""
        info = TypeRegistry.lookup(type_name)
        return info.base_class if info else None

    @staticmethod
    def get_children(type_name: str) -> List[str]:
        """获取所有直接子类"""
        return [t.name for t in TypeRegistry.get_subclasses(type_name)]

    @staticmethod
    def get_all_children(type_name: str) -> List[str]:
        """获取所有子类（递归）"""
        return [t.name for t in TypeRegistry.get_all_subclasses(type_name)]

    @staticmethod
    def get_interfaces(type_name: str) -> List[str]:
        """获取类型实现的接口列表"""
        info = TypeRegistry.lookup(type_name)
        return info.interfaces if info else []

    @staticmethod
    def is_a(subtype_name: str, supertype_name: str) -> bool:
        """检查 subtype 是否是 supertype 的子类型

        包括：
        1. 相同类型
        2. 继承关系（向上追溯）
        3. 接口实现
        """
        if subtype_name == supertype_name:
            return True

        sub_info = TypeRegistry.lookup(subtype_name)
        if sub_info is None:
            return False

        # 检查继承链
        for ancestor in sub_info.get_ancestors():
            if ancestor == supertype_name:
                return True

        # 检查接口
        if sub_info.implements_interface(supertype_name):
            return True

        return False

    @staticmethod
    def get_ancestors(type_name: str) -> List[str]:
        """获取所有祖先类型"""
        info = TypeRegistry.lookup(type_name)
        return info.get_ancestors() if info else []

    @staticmethod
    def get_common_base(type1: str, type2: str) -> Optional[str]:
        """获取两个类型的最近公共基类"""
        ancestors1: List[str] = []

        # 收集 type1 的所有祖先（包括自身）
        info1 = TypeRegistry.lookup(type1)
        if info1:
            ancestors1 = [type1] + info1.get_ancestors()

        # 从 type2 开始向上查找
        current = type2
        visited: Set[str] = set()
        while current and current not in visited:
            if current in ancestors1:
                return current
            visited.add(current)
            info = TypeRegistry.lookup(current)
            current = info.base_class if info else None

        return None


class TypeChecker:
    """运行时类型检查器

    提供类型兼容性检查的公共接口。
    所有检查基于 TypeRegistry 中注册的类型信息。
    """

    def __init__(self):
        self.hierarchy = TypeHierarchy()

    def is_type(self, obj_type_name: str, target_type_name: str) -> bool:
        """检查对象类型是否匹配目标类型

        Args:
            obj_type_name: 对象的实际类型名
            target_type_name: 要检查的目标类型名

        Returns:
            True 如果对象类型是目标类型或其子类型
        """
        return self.hierarchy.is_a(obj_type_name, target_type_name)

    def is_subtype(self, subtype_name: str, supertype_name: str) -> bool:
        """检查子类型关系"""
        return self.hierarchy.is_a(subtype_name, supertype_name)

    def implements_interface(self, type_name: str, interface_name: str) -> bool:
        """检查类型是否实现了指定接口"""
        info = TypeRegistry.lookup(type_name)
        if info is None:
            return False
        return info.implements_interface(interface_name)

    def type_equals(self, type1_name: str, type2_name: str) -> bool:
        """检查两个类型是否完全相同（不含继承）"""
        return type1_name == type2_name

    def get_common_base(self, type1_name: str, type2_name: str) -> Optional[str]:
        """获取两个类型的最近公共基类"""
        return self.hierarchy.get_common_base(type1_name, type2_name)

    def check_assignable(self, target_type: str, source_type: str) -> bool:
        """检查是否可以将 source_type 的值赋给 target_type 的变量

        规则：
        1. 相同类型可赋值
        2. 子类型可赋值给父类型（多态）
        3. 实现了接口的类型可赋值给接口类型
        """
        return self.hierarchy.is_a(source_type, target_type)

    def get_type_name(self, type_name: str) -> str:
        """获取类型名称（如果已注册）"""
        info = TypeRegistry.lookup(type_name)
        return info.name if info else type_name

    def is_primitive(self, type_name: str) -> bool:
        """检查是否是基本类型"""
        info = TypeRegistry.lookup(type_name)
        return info.is_primitive if info else False


# ==================== 公共 API ====================

# 全局实例
_type_checker = TypeChecker()


def is_type(obj_type_name: str, target_type_name: str) -> bool:
    """检查对象类型是否匹配目标类型"""
    return _type_checker.is_type(obj_type_name, target_type_name)


def is_subtype(subtype_name: str, supertype_name: str) -> bool:
    """检查子类型关系"""
    return _type_checker.is_subtype(subtype_name, supertype_name)


def implements_interface(type_name: str, interface_name: str) -> bool:
    """检查类型是否实现了指定接口"""
    return _type_checker.implements_interface(type_name, interface_name)


def type_equals(type1_name: str, type2_name: str) -> bool:
    """检查两个类型是否完全相同"""
    return _type_checker.type_equals(type1_name, type2_name)


def type_name(type_name_str: str) -> str:
    """获取类型名称"""
    return _type_checker.get_type_name(type_name_str)


def check_assignable(target_type: str, source_type: str) -> bool:
    """检查赋值兼容性"""
    return _type_checker.check_assignable(target_type, source_type)


def is_primitive(type_name_str: str) -> bool:
    """检查是否是基本类型"""
    return _type_checker.is_primitive(type_name_str)


__all__ = [
    "TypeHierarchy",
    "TypeChecker",
    "is_type",
    "is_subtype",
    "implements_interface",
    "type_equals",
    "type_name",
    "check_assignable",
    "is_primitive",
]

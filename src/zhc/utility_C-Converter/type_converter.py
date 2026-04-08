#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
类型转换器 - 中文类型关键字到C类型的映射

职责：
1. 类型关键字映射：中文类型 → C类型
2. 类型修饰符处理
3. 复合类型解析

作者：远
日期：2026-04-07
"""

from typing import Dict, Optional


class TypeConverter:
    """类型转换器 - 使用 dispatch table 模式"""

    # 基本类型映射表
    BASIC_TYPES: Dict[str, str] = {
        "整数型": "int",
        "字符型": "char",
        "浮点型": "float",
        "双精度浮点型": "double",
        "逻辑型": "_Bool",
        "长整数型": "long",
        "短整数型": "short",
        "无类型": "void",
        "有符号": "signed",
        "无符号": "unsigned",
        "字节型": "unsigned char",
        "长双精度型": "long double",
        "长长整数型": "long long",
    }

    # 复合类型关键字
    COMPOUND_TYPES = {
        "结构体": "struct",
        "共用体": "union",
        "枚举": "enum",
    }

    # 类型修饰符
    TYPE_MODIFIERS = {
        "常量": "const",
        "易变": "volatile",
        "静态": "static",
        "外部": "extern",
        "寄存器": "register",
        "自动": "auto",
    }

    def __init__(self):
        """初始化类型转换器"""
        self._custom_types: Dict[str, str] = {}

    def convert_type(self, zh_type: str) -> str:
        """
        转换中文类型关键字为C类型

        Args:
            zh_type: 中文类型关键字

        Returns:
            C类型关键字
        """
        # 检查自定义类型
        if zh_type in self._custom_types:
            return self._custom_types[zh_type]

        # 检查是否包含"中文"前缀
        if zh_type.startswith("中文"):
            base_type = zh_type[2:]
            if base_type in self.BASIC_TYPES:
                return self.BASIC_TYPES[base_type]

        # 检查基本类型
        if zh_type in self.BASIC_TYPES:
            return self.BASIC_TYPES[zh_type]

        # 检查复合类型
        if zh_type in self.COMPOUND_TYPES:
            return self.COMPOUND_TYPES[zh_type]

        # 检查类型修饰符
        if zh_type in self.TYPE_MODIFIERS:
            return self.TYPE_MODIFIERS[zh_type]

        # 未找到映射，返回原值
        return zh_type

    def convert_parameter_list(self, params: str) -> str:
        """
        转换参数列表

        Args:
            params: 中文参数列表字符串

        Returns:
            转换后的C参数列表
        """
        if not params.strip():
            return "void"

        param_parts = []
        for param in params.split(","):
            param = param.strip()
            if not param:
                continue

            words = param.split()
            if len(words) >= 2:
                param_type = self.convert_type(words[0])
                param_name = words[1]
                param_parts.append(f"{param_type} {param_name}")
            else:
                param_parts.append(param)

        return ", ".join(param_parts)

    def register_custom_type(self, zh_name: str, c_name: str) -> None:
        """
        注册自定义类型映射

        Args:
            zh_name: 中文类型名
            c_name: C类型名
        """
        self._custom_types[zh_name] = c_name

    def is_basic_type(self, type_name: str) -> bool:
        """检查是否是基本类型"""
        return type_name in self.BASIC_TYPES

    def is_compound_type(self, type_name: str) -> bool:
        """检查是否是复合类型"""
        return type_name in self.COMPOUND_TYPES

    def is_type_modifier(self, keyword: str) -> bool:
        """检查是否是类型修饰符"""
        return keyword in self.TYPE_MODIFIERS

    def get_all_type_keywords(self) -> Dict[str, str]:
        """获取所有类型关键字映射"""
        result = {}
        result.update(self.BASIC_TYPES)
        result.update(self.COMPOUND_TYPES)
        result.update(self.TYPE_MODIFIERS)
        result.update(self._custom_types)
        return result


# 模块级单例实例
_default_converter: Optional[TypeConverter] = None


def get_type_converter() -> TypeConverter:
    """获取默认类型转换器实例"""
    global _default_converter
    if _default_converter is None:
        _default_converter = TypeConverter()
    return _default_converter


def convert_type(zh_type: str) -> str:
    """
    便捷函数：转换中文类型关键字

    Args:
        zh_type: 中文类型关键字

    Returns:
        C类型关键字
    """
    return get_type_converter().convert_type(zh_type)


def convert_parameter_list(params: str) -> str:
    """
    便捷函数：转换参数列表

    Args:
        params: 中文参数列表字符串

    Returns:
        转换后的C参数列表
    """
    return get_type_converter().convert_parameter_list(params)

#!/usr/bin/env python3
"""
Day 13: 属性转换器

功能：
1. 类属性到C struct成员的转换
2. 属性类型检查和验证
3. 访问控制转换
4. 默认值处理

转换规则：
- 公开属性 -> 公开成员
- 私有属性 -> 私有成员（static或文件作用域）
- 保护属性 -> 保护成员（派生类可访问）
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class Visibility(Enum):
    """可见性枚举"""

    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"


class AttributeType(Enum):
    """属性类型枚举"""

    INSTANCE = "instance"
    CLASS_VAR = "class_var"
    CONSTANT = "constant"


# 中文类型到C类型映射
TYPE_MAPPING = {
    "整数型": "int",
    "浮点型": "float",
    "双精度浮点型": "double",
    "字符型": "char",
    "字符串型": "char*",
    "逻辑型": "int",
    "短整数型": "short",
    "长整数型": "long",
    "空型": "void",
    "无类型": "void",
}


@dataclass
class AttributeInfo:
    """属性信息"""

    name: str
    type_name: str
    c_type: str  # 转换后的C类型
    visibility: Visibility
    attribute_type: AttributeType
    line_number: int
    default_value: Optional[str] = None
    is_static: bool = False
    is_const: bool = False
    is_pointer: bool = False

    def __post_init__(self):
        # 类型转换
        if self.type_name in TYPE_MAPPING:
            self.c_type = TYPE_MAPPING[self.type_name]
        else:
            self.c_type = self.type_name

        # 检查是否是指针类型
        if "型" not in self.type_name and "*" in self.type_name:
            self.is_pointer = True


@dataclass
class StructMember:
    """struct成员信息"""

    name: str
    c_type: str
    visibility: Visibility
    is_static: bool = False
    is_const: bool = False
    default_value: Optional[str] = None
    array_size: Optional[int] = None


@dataclass
class ConversionResult:
    """转换结果"""

    struct_declaration: str
    struct_definition: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    statistics: Dict[str, int] = field(default_factory=dict)


class AttributeConverter:
    """属性转换器"""

    # 添加为类属性，供测试访问
    TYPE_MAPPING = TYPE_MAPPING

    def __init__(self):
        self.attributes: List[AttributeInfo] = []
        self.struct_members: List[StructMember] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_attribute(
        self,
        name: str,
        type_name: str,
        visibility: str = "private",
        default_value: Optional[str] = None,
        is_static: bool = False,
        is_const: bool = False,
        line_number: int = 0,
    ) -> bool:
        """添加属性"""
        # 类型检查
        if type_name not in TYPE_MAPPING and not self._is_valid_c_type(type_name):
            self.warnings.append(
                f"行{line_number}: 类型 '{type_name}' 未知，将保持原样"
            )

        # 可见性转换
        vis = self._parse_visibility(visibility)

        # 创建属性信息
        attr = AttributeInfo(
            name=name,
            type_name=type_name,
            c_type=TYPE_MAPPING.get(type_name, type_name),
            visibility=vis,
            attribute_type=AttributeType.INSTANCE,
            line_number=line_number,
            default_value=default_value,
            is_static=is_static,
            is_const=is_const,
        )

        self.attributes.append(attr)

        # 添加到struct成员列表
        member = StructMember(
            name=name,
            c_type=attr.c_type,
            visibility=vis,
            is_static=is_static,
            is_const=is_const,
            default_value=default_value,
        )
        self.struct_members.append(member)

        return True

    def convert_attribute(
        self,
        attr_info_or_name,
        type_name=None,
        visibility="private",
        default_value=None,
    ) -> StructMember:
        """转换属性 - 兼容测试接口"""
        # 支持两种调用方式：
        # 1. convert_attribute(attr_info) - 传入AttributeInfo对象
        # 2. convert_attribute(name, type, visibility, default_value) - 传入参数

        if type_name is None:
            # 方式1: 传入对象
            attr_info = attr_info_or_name
            name = attr_info.name
            type_name = attr_info.type_name
            vis = getattr(attr_info, "visibility", Visibility.PRIVATE)
            default_value = getattr(attr_info, "default_value", None)

            # 转换枚举类型
            if hasattr(vis, "value"):
                vis_str = vis.value
            else:
                vis_str = str(vis)
            visibility_map = {
                "public": Visibility.PUBLIC,
                "private": Visibility.PRIVATE,
                "protected": Visibility.PROTECTED,
            }
            vis = visibility_map.get(vis_str.lower(), Visibility.PRIVATE)
        else:
            # 方式2: 传入参数
            name = attr_info_or_name
            vis = self._parse_visibility(visibility)

        # 创建StructMember
        c_type = TYPE_MAPPING.get(type_name, type_name)
        member = StructMember(
            name=name,
            c_type=c_type,
            visibility=vis,
            is_static=getattr(attr_info_or_name, "is_static", False)
            if not isinstance(attr_info_or_name, str)
            else False,
            is_const=getattr(attr_info_or_name, "is_const", False)
            if not isinstance(attr_info_or_name, str)
            else False,
            default_value=default_value,
        )
        return member

    def _is_valid_c_type(self, type_name: str) -> bool:
        """检查是否是有效的C类型"""
        # 基本C类型
        basic_types = {"int", "float", "double", "char", "void", "short", "long"}
        if type_name in basic_types:
            return True

        # 指针类型
        if "*" in type_name:
            base_type = type_name.replace("*", "").strip()
            return base_type in basic_types or base_type in TYPE_MAPPING.values()

        return False

    def _parse_visibility(self, visibility: str) -> Visibility:
        """解析可见性"""
        if visibility in ["public", "公开", "公开:"]:
            return Visibility.PUBLIC
        elif visibility in ["protected", "保护", "保护:"]:
            return Visibility.PROTECTED
        else:  # private, 私有, 私有:
            return Visibility.PRIVATE

    def convert_to_struct_declaration(self, class_name: str) -> str:
        """转换为struct声明（头文件用）"""
        lines = []
        lines.append(f"typedef struct {class_name} {{")

        # 成员声明
        for member in self.struct_members:
            # 静态成员
            if member.is_static:
                if member.is_const:
                    lines.append(f"    static const {member.c_type} {member.name};")
                else:
                    lines.append(f"    static {member.c_type} {member.name};")
            # 普通成员
            else:
                lines.append(f"    {member.c_type} {member.name};")

        lines.append(f"}} {class_name};")
        lines.append(f"typedef struct {class_name} {class_name};")

        return "\n".join(lines)

    def convert_to_struct_definition(self, class_name: str) -> str:
        """转换为struct定义（源文件用）"""
        lines = []
        lines.append(f"/* {class_name} 成员定义 */")

        # 静态成员定义
        static_members = [m for m in self.struct_members if m.is_static]
        if static_members:
            for member in static_members:
                if member.default_value:
                    lines.append(
                        f"{member.c_type} {class_name}::{member.name} = {member.default_value};"
                    )
                else:
                    lines.append(f"{member.c_type} {class_name}::{member.name};")

        return "\n".join(lines)

    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            "total_attributes": len(self.attributes),
            "public_attributes": sum(
                1 for a in self.attributes if a.visibility == Visibility.PUBLIC
            ),
            "private_attributes": sum(
                1 for a in self.attributes if a.visibility == Visibility.PRIVATE
            ),
            "protected_attributes": sum(
                1 for a in self.attributes if a.visibility == Visibility.PROTECTED
            ),
            "static_attributes": sum(1 for a in self.attributes if a.is_static),
            "const_attributes": sum(1 for a in self.attributes if a.is_const),
        }


class ClassToStructConverter:
    """类到struct转换器"""

    def __init__(self):
        self.type_mapping = TYPE_MAPPING.copy()
        self.converter = AttributeConverter()

    def convert_attribute(
        self,
        name: str,
        type_name: str,
        visibility: str = "private",
        default_value: Optional[str] = None,
        is_static: bool = False,
        is_const: bool = False,
        line_number: int = 0,
    ) -> bool:
        """转换单个属性"""
        return self.converter.add_attribute(
            name, type_name, visibility, default_value, is_static, is_const, line_number
        )

    def convert_class(
        self, class_name: str, base_class: Optional[str] = None
    ) -> ConversionResult:
        """转换整个类"""
        result = ConversionResult(struct_declaration="", struct_definition="")

        # 生成struct声明
        result.struct_declaration = self._generate_struct_declaration(
            class_name, base_class
        )

        # 生成struct定义
        result.struct_definition = self._generate_struct_definition(class_name)

        # 填充统计信息
        result.statistics = self.converter.get_statistics()

        # 填充警告
        result.warnings = self.converter.warnings.copy()

        return result

    def _generate_struct_declaration(
        self, class_name: str, base_class: Optional[str]
    ) -> str:
        """生成struct声明"""
        lines = []

        # 添加注释
        lines.append(f"/* {class_name} 类自动生成的struct声明 */")
        lines.append(f"#ifndef __{class_name.upper()}_H__")
        lines.append(f"#define __{class_name.upper()}_H__")

        # 如果有基类，包含基类头文件
        if base_class:
            lines.append(f'#include "{base_class}.h"')

        lines.append("")
        lines.append("/* struct前置声明 */")
        lines.append(f"typedef struct {class_name} {class_name}_t;")

        lines.append("")
        lines.append(f"/* {class_name} 完整定义 */")
        lines.append(f"struct {class_name} {{")

        # 基类成员（如果是继承）
        if base_class:
            lines.append(f"    /* 基类 {base_class} 的成员 */")
            lines.append(f"    struct {base_class} base;")

        # 成员声明
        for member in self.converter.struct_members:
            if member.is_static:
                if member.is_const:
                    lines.append(f"    static const {member.c_type} {member.name};")
                else:
                    lines.append(f"    static {member.c_type} {member.name};")
            else:
                lines.append(f"    {member.c_type} {member.name};")

        lines.append("};")
        lines.append("")
        lines.append(f"typedef struct {class_name} {class_name}_t;")
        lines.append("")
        lines.append(f"#endif /* __{class_name.upper()}_H__ */")

        return "\n".join(lines)

    def _generate_struct_definition(self, class_name: str) -> str:
        """生成struct定义"""
        lines = []

        lines.append(f"/* {class_name} 成员定义 */")
        lines.append(f'#include "{class_name}.h"')
        lines.append("")

        # 静态成员定义
        static_members = [m for m in self.converter.struct_members if m.is_static]
        if static_members:
            lines.append("/* 静态成员定义 */")
            for member in static_members:
                if member.default_value:
                    lines.append(
                        f"{member.c_type} {class_name}::{member.name} = {member.default_value};"
                    )
                else:
                    lines.append(f"{member.c_type} {class_name}::{member.name};")

        return "\n".join(lines)

    def get_type_mapping(self) -> Dict[str, str]:
        """获取类型映射表"""
        return self.type_mapping.copy()

    def generate_report(self) -> str:
        """生成转换报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("类到struct转换报告")
        lines.append("=" * 60)
        lines.append("")

        # 统计信息
        stats = self.converter.get_statistics()
        lines.append("统计信息:")
        lines.append(f"  总属性数: {stats.get('total_attributes', 0)}")
        lines.append(f"  公开属性: {stats.get('public_attributes', 0)}")
        lines.append(f"  私有属性: {stats.get('private_attributes', 0)}")
        lines.append(f"  保护属性: {stats.get('protected_attributes', 0)}")
        lines.append(f"  静态属性: {stats.get('static_attributes', 0)}")
        lines.append(f"  常量属性: {stats.get('const_attributes', 0)}")
        lines.append("")

        # 警告
        if self.converter.warnings:
            lines.append("警告:")
            for warning in self.converter.warnings:
                lines.append(f"  - {warning}")
            lines.append("")

        # 错误
        if self.converter.errors:
            lines.append("错误:")
            for error in self.converter.errors:
                lines.append(f"  - {error}")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)


# 测试代码
if __name__ == "__main__":
    print("=== Day 13: 属性转换器测试 ===\n")

    # 测试1：基本转换
    print("1. 测试基本属性转换:")
    converter = ClassToStructConverter()

    converter.convert_attribute("姓名", "字符串型", "public", line_number=1)
    converter.convert_attribute("年龄", "整数型", "public", line_number=2)
    converter.convert_attribute("成绩", "浮点型", "private", "0.0", line_number=3)

    result = converter.convert_class("学生")

    print("\n--- struct声明 ---")
    print(result.struct_declaration)

    print("\n--- 统计 ---")
    for key, value in result.statistics.items():
        print(f"  {key}: {value}")

    # 测试2：继承类转换
    print("\n2. 测试继承类转换:")
    converter2 = ClassToStructConverter()

    converter2.convert_attribute("姓名", "字符串型", "public", line_number=1)
    converter2.convert_attribute("专业", "字符串型", "public", line_number=2)

    result2 = converter2.convert_class("大学生", base_class="学生")

    print("\n--- struct声明（带基类）---")
    print(result2.struct_declaration)

    # 测试3：类型映射
    print("\n3. 类型映射表:")
    for cn, c in converter.get_type_mapping().items():
        print(f"  {cn} -> {c}")

    print("\n=== Day 13 测试完成 ===")

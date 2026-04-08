#!/usr/bin/env python3
"""
Day 11: 类系统核心实现

功能：
1. 类语法解析
2. 属性和方法定义
3. 访问控制（公开/私有/保护）
4. 构造函数和析构函数

语法示例：
类 学生 {
    属性:
        字符串型 姓名;
        整数型 年龄;

    方法:
        函数 构造函数(字符串型 名, 整数型 龄) -> 空型 {
            姓名 = 名;
            年龄 = 龄;
        }

        函数 获取信息() -> 字符串型 {
            返回 "学生";
        }
}
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class Visibility(Enum):
    """可见性枚举"""

    PUBLIC = "public"  # 公开：可被外部访问
    PRIVATE = "private"  # 私有：仅类内部可访问
    PROTECTED = "protected"  # 保护：类及子类可访问


class AttributeType(Enum):
    """属性类型枚举"""

    INSTANCE = "instance"  # 实例属性
    CLASS = "class"  # 类属性（静态）
    CONSTANT = "constant"  # 常量属性


@dataclass
class AttributeInfo:
    """属性信息"""

    name: str  # 属性名
    type_name: str  # 类型名（如 整数型、字符串型）
    visibility: Visibility  # 可见性
    attribute_type: AttributeType  # 属性类型
    line_number: int  # 定义行号
    default_value: Optional[str] = None  # 默认值
    is_static: bool = False  # 是否为静态属性
    is_const: bool = False  # 是否为常量


@dataclass
class MethodInfo:
    """方法信息"""

    name: str  # 方法名
    return_type: str  # 返回类型
    parameters: List[Tuple[str, str]]  # 参数列表 [(参数名, 类型), ...]
    visibility: Visibility  # 可见性
    is_constructor: bool = False  # 是否为构造函数
    is_destructor: bool = False  # 是否为析构函数
    is_static: bool = False  # 是否为静态方法
    is_virtual: bool = False  # 是否为虚函数
    line_number: int = 0  # 定义行号


@dataclass
class ClassInfo:
    """类信息"""

    name: str  # 类名
    base_class: Optional[str] = None  # 基类名
    attributes: List[AttributeInfo] = field(default_factory=list)  # 属性列表
    methods: List[MethodInfo] = field(default_factory=list)  # 方法列表
    visibility: Visibility = Visibility.PUBLIC  # 类本身可见性
    line_number: int = 0  # 定义行号
    is_abstract: bool = False  # 是否为抽象类
    is_final: bool = False  # 是否为最终类

    def add_attribute(self, attr: AttributeInfo):
        """添加属性"""
        self.attributes.append(attr)

    def add_method(self, method: MethodInfo):
        """添加方法"""
        self.methods.append(method)

    def get_public_attributes(self) -> List[AttributeInfo]:
        """获取公开属性"""
        return [a for a in self.attributes if a.visibility == Visibility.PUBLIC]

    def get_public_methods(self) -> List[MethodInfo]:
        """获取公开方法"""
        return [m for m in self.methods if m.visibility == Visibility.PUBLIC]

    def get_constructor(self) -> Optional[MethodInfo]:
        """获取构造函数"""
        for m in self.methods:
            if m.is_constructor:
                return m
        return None


class ClassParser:
    """类解析器"""

    # 关键字模式
    CLASS_PATTERN = r"类\s+(\w+)(?:\s*:\s*(\w+))?\s*\{"
    ATTRIBUTE_PATTERN = r"(\w+型)\s+(\w+)(?:\s*=\s*([^;]+))?;"
    METHOD_PATTERN = r"函数\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*(\w+型))?\s*\{"
    CONSTRUCTOR_PATTERN = r"函数\s+构造函数\s*\(([^)]*)\)\s*->\s*空型\s*\{"
    DESTRUCTOR_PATTERN = r"函数\s+析构函数\s*\(\s*\)\s*->\s*空型\s*\{"

    def __init__(self):
        self.classes: Dict[str, ClassInfo] = {}
        self.current_class: Optional[ClassInfo] = None
        self.current_section: str = ""  # "属性" or "方法"
        self.current_visibility: Visibility = Visibility.PRIVATE  # 默认私有
        self.errors: List[str] = []

    def parse_class_declaration(self, line: str, line_num: int) -> Optional[ClassInfo]:
        """解析类声明"""
        pattern = self.CLASS_PATTERN
        match = re.search(pattern, line)

        if match:
            class_name = match.group(1)
            base_class = match.group(2)  # 可能为None

            if class_name in self.classes:
                self.errors.append(f"行{line_num}: 类 '{class_name}' 重复定义")
                return None

            class_info = ClassInfo(
                name=class_name, base_class=base_class, line_number=line_num
            )
            self.classes[class_name] = class_info
            self.current_class = class_info
            self.current_section = ""

            return class_info

        return None

    def parse_section_header(self, line: str, line_num: int) -> Optional[str]:
        """解析区域头（属性:/方法:）"""
        stripped = line.strip()

        # 处理可见性修饰符
        if stripped == "公开:":
            self.current_visibility = Visibility.PUBLIC
            return "visibility_changed"
        elif stripped == "私有:":
            self.current_visibility = Visibility.PRIVATE
            return "visibility_changed"
        elif stripped == "保护:":
            self.current_visibility = Visibility.PROTECTED
            return "visibility_changed"

        # 处理区域头
        if stripped in ["属性:", "方法:"]:
            self.current_section = stripped[:-1]  # 去掉冒号
            return self.current_section

        return None

    def parse_attribute(self, line: str, line_num: int) -> Optional[AttributeInfo]:
        """解析属性声明"""
        if not self.current_class or self.current_section != "属性":
            return None

        pattern = self.ATTRIBUTE_PATTERN
        match = re.search(pattern, line)

        if match:
            type_name = match.group(1)
            attr_name = match.group(2)
            default_value = match.group(3)

            # 使用当前可见性
            visibility = self.current_visibility

            attr = AttributeInfo(
                name=attr_name,
                type_name=type_name,
                visibility=visibility,
                attribute_type=AttributeType.INSTANCE,
                line_number=line_num,
                default_value=default_value.strip() if default_value else None,
            )

            self.current_class.add_attribute(attr)
            return attr

        return None

    def parse_method(self, line: str, line_num: int) -> Optional[MethodInfo]:
        """解析方法声明"""
        if not self.current_class or self.current_section != "方法":
            return None

        # 先检查构造函数
        match = re.search(self.CONSTRUCTOR_PATTERN, line)
        if match:
            params_str = match.group(1)
            params = self._parse_parameters(params_str)

            method = MethodInfo(
                name="构造函数",
                return_type="空型",
                parameters=params,
                visibility=Visibility.PUBLIC,
                is_constructor=True,
                line_number=line_num,
            )

            self.current_class.add_method(method)
            return method

        # 检查析构函数
        match = re.search(self.DESTRUCTOR_PATTERN, line)
        if match:
            method = MethodInfo(
                name="析构函数",
                return_type="空型",
                parameters=[],
                visibility=Visibility.PUBLIC,
                is_destructor=True,
                line_number=line_num,
            )

            self.current_class.add_method(method)
            return method

        # 普通方法
        match = re.search(self.METHOD_PATTERN, line)
        if match:
            method_name = match.group(1)
            params_str = match.group(2)
            return_type = match.group(3) or "空型"

            params = self._parse_parameters(params_str)

            # 使用当前可见性
            visibility = self.current_visibility

            method = MethodInfo(
                name=method_name,
                return_type=return_type,
                parameters=params,
                visibility=visibility,
                line_number=line_num,
            )

            self.current_class.add_method(method)
            return method

        return None

    def _parse_parameters(self, params_str: str) -> List[Tuple[str, str]]:
        """解析参数列表"""
        params: List[Tuple[str, str]] = []
        if not params_str.strip():
            return params

        # 分割参数
        param_matches = re.findall(r"(\w+型)\s+(\w+)", params_str)
        for type_name, param_name in param_matches:
            params.append((param_name, type_name))

        return params

    def parse_line(self, line: str, line_num: int):
        """解析一行代码"""
        # 跳过空行和注释
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            return

        # 解析类声明
        if self.parse_class_declaration(line, line_num):
            return

        # 解析区域头
        if self.parse_section_header(line, line_num):
            return

        # 解析属性
        if self.current_section == "属性":
            if self.parse_attribute(line, line_num):
                return

        # 解析方法
        if self.current_section == "方法":
            if self.parse_method(line, line_num):
                return

        # 检查类结束
        if stripped == "}" and self.current_class:
            self.current_class = None
            self.current_section = ""

    def parse_file(self, file_path: str) -> List[ClassInfo]:
        """解析文件中的所有类"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            self.classes.clear()
            self.current_class = None
            self.current_section = ""
            self.errors.clear()

            for i, line in enumerate(lines, 1):
                self.parse_line(line.strip(), i)

            return list(self.classes.values())

        except Exception as e:
            self.errors.append(f"解析文件失败: {e}")
            return []

    def get_class(self, class_name: str) -> Optional[ClassInfo]:
        """获取类信息"""
        return self.classes.get(class_name)

    def get_summary(self) -> str:
        """获取解析摘要"""
        summary = []
        summary.append("=== 类解析摘要 ===")
        summary.append(f"发现类数: {len(self.classes)}")
        summary.append(f"错误数: {len(self.errors)}")

        if self.errors:
            summary.append("\n错误列表:")
            for error in self.errors:
                summary.append(f"  - {error}")

        for class_name, class_info in self.classes.items():
            summary.append(f"\n类: {class_name}")
            if class_info.base_class:
                summary.append(f"  基类: {class_info.base_class}")
            summary.append(f"  属性数: {len(class_info.attributes)}")
            summary.append(f"  方法数: {len(class_info.methods)}")

            if class_info.attributes:
                pub_attrs = class_info.get_public_attributes()
                summary.append(f"  公开属性: {len(pub_attrs)}")

            if class_info.methods:
                pub_methods = class_info.get_public_methods()
                summary.append(f"  公开方法: {len(pub_methods)}")

        return "\n".join(summary)


# 测试代码
if __name__ == "__main__":
    print("=== Day 11: 类系统测试 ===\n")

    # 测试类解析
    parser = ClassParser()

    test_code = """
类 学生 {
    属性:
        字符串型 姓名;
        整数型 年龄;
        浮点型 成绩 = 0.0;

    方法:
        函数 构造函数(字符串型 名, 整数型 龄) -> 空型 {
            姓名 = 名;
            年龄 = 龄;
        }

        函数 获取信息() -> 字符串型 {
            返回 "学生";
        }

        函数 设置成绩(参数 浮点型 分) -> 空型 {
            成绩 = 分;
        }
}

类 大学生 : 学生 {
    属性:
        字符串型 专业;
        字符串型 学号;

    方法:
        函数 构造函数(字符串型 名, 整数型 龄, 字符串型 专, 字符串型 号) -> 空型 {
            姓名 = 名;
            年龄 = 龄;
            专业 = 专;
            学号 = 号;
        }
}
"""

    print("1. 解析测试代码:")
    lines = test_code.strip().split("\n")
    for i, line in enumerate(lines, 1):
        parser.parse_line(line.strip(), i)

    print("\n" + parser.get_summary())

    print("\n2. 类详情:")
    student_class = parser.get_class("学生")
    if student_class:
        print(f"   类名: {student_class.name}")
        print(f"   属性数: {len(student_class.attributes)}")
        print(f"   方法数: {len(student_class.methods)}")

        constructor = student_class.get_constructor()
        if constructor:
            print(f"   构造函数: {constructor.name}({constructor.parameters})")

    undergrad_class = parser.get_class("大学生")
    if undergrad_class:
        print("\n   大学生类:")
        print(f"   - 基类: {undergrad_class.base_class}")
        print(f"   - 属性数: {len(undergrad_class.attributes)}")
        print(f"   - 方法数: {len(undergrad_class.methods)}")

    print("\n=== Day 11 测试完成 ===")

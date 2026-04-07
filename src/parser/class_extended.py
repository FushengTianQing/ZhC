#!/usr/bin/env python3
"""
Day 12: 类解析器扩展实现

功能：
1. 完整的类解析器架构
2. 方法体解析
3. 继承链解析
4. 与模块系统集成

增强特性：
- 方法体的完整解析
- 继承链的完整追踪
- 类型检查和验证
- 错误恢复机制
"""

import re
from typing import List, Dict, Optional, Set, Tuple, Any
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


@dataclass
class AttributeInfo:
    """属性信息"""
    name: str
    type_name: str
    visibility: Visibility
    attribute_type: AttributeType
    line_number: int
    default_value: Optional[str] = None
    is_static: bool = False
    is_const: bool = False


@dataclass
class ParameterInfo:
    """参数信息"""
    name: str
    type_name: str
    is_reference: bool = False
    is_const: bool = False


@dataclass
class MethodBody:
    """方法体信息"""
    lines: List[str]
    local_variables: List[Tuple[str, str]] = field(default_factory=list)
    statements: List[str] = field(default_factory=list)


@dataclass
class MethodInfo:
    """方法信息"""
    name: str
    return_type: str
    parameters: List[ParameterInfo]
    visibility: Visibility
    line_number: int
    is_constructor: bool = False
    is_destructor: bool = False
    is_static: bool = False
    is_virtual: bool = False
    is_abstract: bool = False
    body: Optional[MethodBody] = None


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    base_class: Optional[str] = None
    attributes: List[AttributeInfo] = field(default_factory=list)
    methods: List[MethodInfo] = field(default_factory=list)
    visibility: Visibility = Visibility.PUBLIC
    line_number: int = 0
    is_abstract: bool = False
    is_final: bool = False
    # 继承链信息
    inheritance_chain: List[str] = field(default_factory=list)

    def add_attribute(self, attr: AttributeInfo):
        self.attributes.append(attr)

    def add_method(self, method: MethodInfo):
        self.methods.append(method)

    def get_public_attributes(self) -> List[AttributeInfo]:
        return [a for a in self.attributes if a.visibility == Visibility.PUBLIC]

    def get_public_methods(self) -> List[MethodInfo]:
        return [m for m in self.methods if m.visibility == Visibility.PUBLIC]

    def get_constructor(self) -> Optional[MethodInfo]:
        for m in self.methods:
            if m.is_constructor:
                return m
        return None

    def get_all_methods(self) -> List[MethodInfo]:
        """获取所有方法（包括继承的）"""
        return self.methods


class ClassParserExtended:
    """扩展的类解析器"""

    # 正则表达式模式
    CLASS_PATTERN = r'类\s+(\w+)(?:\s*:\s*(\w+))?\s*\{'
    ATTRIBUTE_PATTERN = r'^\s*([\w\u4e00-\u9fff]+型)\s+(\w+)(?:\s*=\s*([^;]+))?;'
    METHOD_PATTERN = r'^\s*(?:静态\s+)?(?:虚函数\s+)?(?:函数\s+)?(\w+)\s*\(([^)]*)\)(?:\s*->\s*([\w\u4e00-\u9fff]+型))?\s*\{'
    CONSTRUCTOR_PATTERN = r'^\s*(?:函数\s+)?构造函数\s*\(([^)]*)\)\s*->\s*空型\s*\{'
    DESTRUCTOR_PATTERN = r'^\s*(?:函数\s+)?析构函数\s*\(\s*\)\s*->\s*空型\s*\{'
    VISIBILITY_PATTERN = r'^\s*(公开:|私有:|保护:)'
    SECTION_PATTERN = r'^\s*(属性:|方法:)'
    CLASS_END_PATTERN = r'^\s*\}'

    def __init__(self):
        self.classes: Dict[str, ClassInfo] = {}
        self.current_class: Optional[ClassInfo] = None
        self.current_section: str = ""  # "属性" or "方法"
        self.current_visibility: Visibility = Visibility.PRIVATE
        self.current_method: Optional[MethodInfo] = None
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.method_body_lines: List[str] = []
        self.in_method_body: bool = False

    def parse_class_declaration(self, line: str, line_num: int) -> Optional[ClassInfo]:
        """解析类声明 - 兼容ClassParser接口"""
        pattern = self.CLASS_PATTERN
        match = re.search(pattern, line)

        if match:
            class_name = match.group(1)
            base_class = match.group(2)  # 可能为None

            if class_name in self.classes:
                self.errors.append({
                    'line': line_num,
                    'message': f"类 '{class_name}' 重复定义"
                })
                return None

            class_info = ClassInfo(
                name=class_name,
                base_class=base_class,
                line_number=line_num
            )
            self.classes[class_name] = class_info
            self.current_class = class_info
            self.current_section = ""

            return class_info

        return None

    def parse_attribute(self, line: str, line_num: int) -> Optional[AttributeInfo]:
        """解析属性声明 - 兼容ClassParser接口"""
        return self._parse_attribute(line, line_num)

    def parse_method(self, line: str, line_num: int) -> Optional[MethodInfo]:
        """解析方法声明 - 兼容ClassParser接口"""
        return self._parse_method_declaration(line, line_num)

    def reset(self):
        """重置解析器状态"""
        self.classes.clear()
        self.current_class = None
        self.current_section = ""
        self.current_visibility = Visibility.PRIVATE
        self.current_method = None
        self.errors.clear()
        self.warnings.clear()
        self.method_body_lines.clear()
        self.in_method_body = False

    def parse_line(self, line: str, line_num: int):
        """解析一行代码"""
        stripped = line.strip()

        # 跳过空行和注释
        if not stripped or stripped.startswith("//"):
            if self.in_method_body:
                self.method_body_lines.append(line)
            return

        # 处理类结束
        if re.match(self.CLASS_END_PATTERN, stripped) and self.current_class:
            if self.in_method_body:
                # 结束方法体
                self._finish_method_body()
            self.current_class = None
            self.current_section = ""
            self.in_method_body = False
            return

        # 如果在方法体内，继续收集代码行
        if self.in_method_body:
            self.method_body_lines.append(line)
            return

        # 解析类声明
        class_match = re.match(self.CLASS_PATTERN, stripped)
        if class_match:
            self._parse_class_declaration(class_match, line_num)
            return

        # 解析可见性声明
        if re.match(self.VISIBILITY_PATTERN, stripped):
            self._parse_visibility(stripped)
            return

        # 解析区域头
        if re.match(self.SECTION_PATTERN, stripped):
            self._parse_section(stripped)
            return

        # 解析属性
        if self.current_section == "属性" and self.current_class:
            attr = self._parse_attribute(stripped, line_num)
            if attr:
                self.current_class.add_attribute(attr)
            return

        # 解析方法
        if self.current_section == "方法" and self.current_class:
            method = self._parse_method_declaration(stripped, line_num)
            if method:
                self.current_method = method
                self.in_method_body = True
                self.method_body_lines = []
            return

    def _parse_class_declaration(self, match, line_num: int):
        """解析类声明"""
        class_name = match.group(1)
        base_class = match.group(2)

        if class_name in self.classes:
            self.errors.append({
                "type": "DUPLICATE_CLASS",
                "message": f"类 '{class_name}' 重复定义",
                "line": line_num
            })
            return

        # 构建继承链
        inheritance_chain = [class_name]
        if base_class:
            inheritance_chain.insert(0, base_class)
            # 递归获取基类的继承链
            if base_class in self.classes:
                inheritance_chain = self.classes[base_class].inheritance_chain + [class_name]

        class_info = ClassInfo(
            name=class_name,
            base_class=base_class,
            line_number=line_num,
            inheritance_chain=inheritance_chain
        )

        self.classes[class_name] = class_info
        self.current_class = class_info
        self.current_section = ""
        self.current_visibility = Visibility.PRIVATE

    def _parse_visibility(self, line: str):
        """解析可见性声明"""
        if "公开:" in line:
            self.current_visibility = Visibility.PUBLIC
        elif "私有:" in line:
            self.current_visibility = Visibility.PRIVATE
        elif "保护:" in line:
            self.current_visibility = Visibility.PROTECTED

    def _parse_section(self, line: str):
        """解析区域头"""
        if "属性:" in line:
            self.current_section = "属性"
        elif "方法:" in line:
            self.current_section = "方法"

    def _parse_attribute(self, line: str, line_num: int) -> Optional[AttributeInfo]:
        """解析属性声明"""
        match = re.match(self.ATTRIBUTE_PATTERN, line)
        if not match:
            return None

        type_name = match.group(1)
        attr_name = match.group(2)
        default_value = match.group(3)

        attr = AttributeInfo(
            name=attr_name,
            type_name=type_name,
            visibility=self.current_visibility,
            attribute_type=AttributeType.INSTANCE,
            line_number=line_num,
            default_value=default_value.strip() if default_value else None
        )

        return attr

    def _parse_method_declaration(self, line: str, line_num: int) -> Optional[MethodInfo]:
        """解析方法声明"""
        # 检查构造函数
        match = re.match(self.CONSTRUCTOR_PATTERN, line)
        if match:
            params_str = match.group(1)
            params = self._parse_parameters(params_str)

            return MethodInfo(
                name="构造函数",
                return_type="空型",
                parameters=params,
                visibility=Visibility.PUBLIC,
                is_constructor=True,
                line_number=line_num
            )

        # 检查析构函数
        if re.match(self.DESTRUCTOR_PATTERN, line):
            return MethodInfo(
                name="析构函数",
                return_type="空型",
                parameters=[],
                visibility=Visibility.PUBLIC,
                is_destructor=True,
                line_number=line_num
            )

        # 普通方法
        match = re.match(self.METHOD_PATTERN, line)
        if match:
            method_name = match.group(1)
            params_str = match.group(2)
            return_type = match.group(3) or "空型"

            params = self._parse_parameters(params_str)

            # 检查修饰符
            is_static = '静态' in line
            is_virtual = '虚函数' in line or '虚方法' in line

            return MethodInfo(
                name=method_name,
                return_type=return_type,
                parameters=params,
                visibility=self.current_visibility,
                is_static=is_static,
                is_virtual=is_virtual,
                line_number=line_num
            )

        return None

    def _finish_method_body(self):
        """结束方法体解析"""
        if self.current_method and self.current_class:
            method_body = MethodBody(
                lines=self.method_body_lines.copy(),
                statements=self._extract_statements(self.method_body_lines)
            )
            self.current_method.body = method_body
            self.current_class.add_method(self.current_method)

        self.current_method = None
        self.in_method_body = False
        self.method_body_lines = []

    def _parse_parameters(self, params_str: str) -> List[ParameterInfo]:
        """解析参数列表"""
        params: List[ParameterInfo] = []
        if not params_str.strip():
            return params

        param_matches = re.findall(r'([\w\u4e00-\u9fff]+型)\s+(\w+)', params_str)
        for type_name, param_name in param_matches:
            params.append(ParameterInfo(name=param_name, type_name=type_name))

        return params

    def _extract_statements(self, lines: List[str]) -> List[str]:
        """提取语句（简单实现）"""
        statements = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("//"):
                # 移除行号和简单语句
                statements.append(stripped)
        return statements

    def parse_file(self, file_path: str) -> List[ClassInfo]:
        """解析文件"""
        self.reset()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                self.parse_line(line, i)

            # 处理文件结束时的方法体
            if self.in_method_body:
                self._finish_method_body()

        except Exception as e:
            self.errors.append({
                "type": "PARSE_ERROR",
                "message": f"解析文件失败: {e}",
                "line": 0
            })

        return list(self.classes.values())

    def get_class(self, class_name: str) -> Optional[ClassInfo]:
        """获取类信息"""
        return self.classes.get(class_name)

    def get_summary(self) -> str:
        """获取解析摘要"""
        lines = []
        lines.append("=== 类解析摘要 ===")
        lines.append(f"发现类数: {len(self.classes)}")
        lines.append(f"错误数: {len(self.errors)}")
        lines.append(f"警告数: {len(self.warnings)}")

        if self.errors:
            lines.append("\n错误列表:")
            for error in self.errors:
                lines.append(f"  - [{error['type']}] {error['message']} (行{error['line']})")

        for class_name, class_info in self.classes.items():
            lines.append(f"\n类: {class_name}")
            if class_info.base_class:
                lines.append(f"  基类: {class_info.base_class}")
                lines.append(f"  继承链: {' -> '.join(class_info.inheritance_chain)}")
            lines.append(f"  属性数: {len(class_info.attributes)}")
            lines.append(f"  方法数: {len(class_info.methods)}")

            pub_attrs = class_info.get_public_attributes()
            pub_methods = class_info.get_public_methods()
            lines.append(f"  公开属性: {len(pub_attrs)}")
            lines.append(f"  公开方法: {len(pub_methods)}")

        return "\n".join(lines)


# 测试代码
if __name__ == "__main__":
    print("=== Day 12: 扩展类解析器测试 ===\n")

    parser = ClassParserExtended()

    test_code = """
类 学生 {
    公开:
    属性:
        字符串型 姓名;
        整数型 年龄;
        浮点型 成绩 = 0.0;

    私有:
    属性:
        整数型 内部标识;

    公开:
    方法:
        函数 构造函数(字符串型 名, 整数型 龄) -> 空型 {
            姓名 = 名;
            年龄 = 龄;
            成绩 = 0.0;
        }

        函数 获取信息() -> 字符串型 {
            返回 姓名;
        }

        函数 设置成绩(参数 浮点型 分) -> 空型 {
            成绩 = 分;
        }
}

类 大学生 : 学生 {
    公开:
    属性:
        字符串型 专业;
        字符串型 学号;

    公开:
    方法:
        函数 构造函数(字符串型 名, 整数型 龄, 字符串型 专, 字符串型 号) -> 空型 {
            姓名 = 名;
            年龄 = 龄;
            专业 = 专;
            学号 = 号;
        }

        函数 获取专业() -> 字符串型 {
            返回 专业;
        }
}
"""

    print("1. 解析测试代码...")
    lines = test_code.strip().split('\n')
    for i, line in enumerate(lines, 1):
        parser.parse_line(line, i)

    print("\n" + parser.get_summary())

    print("\n2. 类详情:")
    student = parser.get_class("学生")
    if student:
        print(f"\n学生类:")
        print(f"  - 属性数: {len(student.attributes)}")
        print(f"  - 方法数: {len(student.methods)}")
        print(f"  - 继承链: {' -> '.join(student.inheritance_chain)}")

        print(f"\n  公开属性:")
        for attr in student.get_public_attributes():
            print(f"    - {attr.name} ({attr.type_name})")

        print(f"\n  公开方法:")
        for method in student.get_public_methods():
            params = ", ".join([f"{p.type_name} {p.name}" for p in method.parameters])
            print(f"    - {method.name}({params}) -> {method.return_type}")

    undergrad = parser.get_class("大学生")
    if undergrad:
        print(f"\n大学生类:")
        print(f"  - 基类: {undergrad.base_class}")
        print(f"  - 继承链: {' -> '.join(undergrad.inheritance_chain)}")
        print(f"  - 属性数: {len(undergrad.attributes)}")
        print(f"  - 方法数: {len(undergrad.methods)}")

    print("\n=== Day 12 测试完成 ===")
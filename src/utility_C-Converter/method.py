#!/usr/bin/env python3
"""
Day 14: 方法转换器

功能：
1. 方法到函数的转换
2. this指针自动添加
3. 虚函数表生成
4. 静态方法和实例方法区分

转换规则：
- 方法名: 类名_方法名
- this指针: 第一个参数
- 虚函数表: 函数指针数组
"""

import re
from typing import List, Dict, Optional, Set, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field


class Visibility(Enum):
    """可见性枚举"""
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"


class MethodType(Enum):
    """方法类型枚举"""
    CONSTRUCTOR = "constructor"
    DESTRUCTOR = "destructor"
    INSTANCE = "instance"
    STATIC = "static"
    VIRTUAL = "virtual"


# 方法关键字映射
METHOD_KEYWORDS = {
    '构造函数': 'constructor',
    '析构函数': 'destructor',
    '函数': 'function'
}

# 返回类型映射
RETURN_TYPE_MAPPING = {
    '空型': 'void',
    '整数型': 'int',
    '浮点型': 'float',
    '双精度浮点型': 'double',
    '字符型': 'char',
    '字符串型': 'char*',
    '逻辑型': 'int'
}


@dataclass
class ParameterInfo:
    """参数信息"""
    name: str
    type_name: str
    c_type: str
    is_reference: bool = False
    is_const: bool = False
    default_value: Optional[str] = None


@dataclass
class MethodConversionResult:
    """方法转换结果"""
    original_name: str
    converted_name: str
    c_function_signature: str
    c_function_body: str
    is_static: bool
    is_virtual: bool
    is_constructor: bool
    is_destructor: bool
    has_this_pointer: bool
    parameters: List
    return_type: str
    errors: List[str] = field(default_factory=list)


@dataclass
class VirtualTableEntry:
    """虚函数表条目"""
    method_name: str
    method_signature: str
    is_pure_virtual: bool = False


@dataclass
class VirtualTable:
    """虚函数表"""
    class_name: str
    entries: List = field(default_factory=list)
    base_tables: List = field(default_factory=list)


class MethodConverter:
    """方法转换器"""

    def __init__(self):
        self.methods: Dict[str, MethodConversionResult] = {}
        self.virtual_tables: Dict[str, VirtualTable] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def convert_method(self, class_name: str, method_code: str,
                     visibility: str = "private",
                     is_static: bool = False,
                     is_virtual: bool = False,
                     is_constructor: bool = False,
                     is_destructor: bool = False) -> MethodConversionResult:
        """转换方法代码"""
        result = MethodConversionResult(
            original_name=method_code,
            converted_name="",
            c_function_signature="",
            c_function_body="",
            is_static=is_static,
            is_virtual=is_virtual,
            is_constructor=is_constructor,
            is_destructor=is_destructor,
            has_this_pointer=False,
            parameters=[],
            return_type=""
        )

        # 解析方法签名
        signature_parsed = self._parse_method_signature(method_code, class_name)
        if signature_parsed is None:
            result.errors.append(f"无法解析方法签名: {method_code}")
            return result

        method_name, return_type, params = signature_parsed

        # 转换方法名
        converted_name = self._convert_method_name(class_name, method_name, is_constructor, is_destructor)

        # 构建C函数签名
        c_signature, has_this = self._build_c_signature(
            converted_name, return_type, params, class_name,
            is_static, is_constructor, is_destructor
        )
        result.has_this_pointer = has_this

        # 更新结果
        result.converted_name = converted_name
        result.c_function_signature = c_signature
        result.parameters = params
        result.return_type = return_type

        # 生成方法体
        if not is_constructor and not is_destructor:
            result.c_function_body = self._convert_method_body(
                method_code, class_name, params
            )

        return result

    def _parse_method_signature(self, method_code: str, class_name: str):
        """解析方法签名"""
        # 匹配函数声明: 函数 方法名(参数) -> 返回类型
        pattern = r'函数\s+(\w+)\s*\(([^)]*)\s*(?:->\s*([\w]+))?'
        match = re.search(pattern, method_code)

        if not match:
            return None

        method_name = match.group(1)
        params_str = match.group(2)
        return_type = match.group(3) or '空型'

        # 解析参数
        params = self._parse_parameters(params_str)

        return (method_name, return_type, params)

    def _parse_parameters(self, params_str: str) -> List[ParameterInfo]:
        """解析参数列表"""
        params: List[ParameterInfo] = []
        if not params_str.strip():
            return params

        # 匹配参数: 类型 参数名
        param_pattern = r'([\w]+)\s+(\w+)'
        matches = re.findall(param_pattern, params_str)

        for type_name, param_name in matches:
            c_type = RETURN_TYPE_MAPPING.get(type_name, type_name)
            param = ParameterInfo(
                name=param_name,
                type_name=type_name,
                c_type=c_type
            )
            params.append(param)

        return params

    def _convert_method_name(self, class_name: str, method_name: str,
                            is_constructor: bool,
                            is_destructor: bool) -> str:
        """转换方法名"""
        if is_constructor:
            return f"{class_name}_constructor"
        elif is_destructor:
            return f"{class_name}_destructor"
        else:
            return f"{class_name}_{method_name}"

    def _build_c_signature(self, converted_name: str, return_type: str,
                          params: List[ParameterInfo],
                          class_name: str,
                          is_static: bool,
                          is_constructor: bool,
                          is_destructor: bool) -> Tuple[str, bool]:
        """构建C函数签名. 返回 (签名, has_this_pointer)"""
        # 返回类型
        c_return = RETURN_TYPE_MAPPING.get(return_type, return_type)

        # 构建参数列表
        param_parts = []
        has_this = False

        # 如果是实例方法或构造函数，添加this指针
        if not is_static and not is_destructor:
            param_parts.append(f"struct {class_name}* self")
            has_this = True

        # 添加其他参数
        for param in params:
            param_str = param.c_type
            if param.is_reference:
                param_str = f"{param_str}*"
            if param.is_const:
                param_str = f"const {param_str}"
            param_str = f"{param_str} {param.name}"
            param_parts.append(param_str)

        params_str = ", ".join(param_parts)

        return f"{c_return} {converted_name}({params_str})", has_this

    def _convert_method_body(self, method_code: str, class_name: str,
                           params: List[ParameterInfo]) -> str:
        """转换方法体"""
        lines = [f"/* {class_name} 方法体 */"]
        return '\n'.join(lines)


class VirtualMethodTableGenerator:
    """虚方法表生成器"""

    def __init__(self):
        self.virtual_tables: Dict[str, VirtualTable] = {}

    def create_virtual_table(self, class_name: str,
                           methods: List[str],
                           base_tables: Optional[List[Any]] = None) -> VirtualTable:
        """创建虚函数表"""
        vtable = VirtualTable(
            class_name=class_name,
            base_tables=base_tables or []
        )

        for method in methods:
            entry = VirtualTableEntry(
                method_name=method,
                method_signature=f"void ({class_name}*)(void)"
            )
            vtable.entries.append(entry)

        self.virtual_tables[class_name] = vtable
        return vtable

    def generate_vtable_struct(self, class_name_or_vtable) -> str:
        """生成虚函数表struct"""
        # 支持传入class_name或vtable对象
        if hasattr(class_name_or_vtable, 'class_name'):
            # 传入vtable对象
            vtable = class_name_or_vtable
            class_name = vtable.class_name
        else:
            # 传入class_name字符串
            class_name = class_name_or_vtable
            if class_name not in self.virtual_tables:
                return ""
            vtable = self.virtual_tables[class_name]

        lines = []

        lines.append(f"/* {class_name} 虚函数表 */")
        lines.append(f"typedef struct {class_name}_vtable {{")

        # 添加基类虚函数表
        for base_name in vtable.base_tables:
            lines.append(f"    struct {base_name}_vtable* base;")

        # 添加方法指针
        for i, entry in enumerate(vtable.entries):
            lines.append(f"    void (*method{i + 1})(struct {class_name}* self);")

        lines.append(f"}} {class_name}_vtable_t;")

        return '\n'.join(lines)

    def generate_vtable_initializer(self, class_name_or_vtable) -> str:
        """生成虚函数表初始化代码"""
        # 支持传入class_name或vtable对象
        if hasattr(class_name_or_vtable, 'class_name'):
            vtable = class_name_or_vtable
            class_name = vtable.class_name
        else:
            class_name = class_name_or_vtable
            if class_name not in self.virtual_tables:
                return ""
            vtable = self.virtual_tables[class_name]

        lines = []

        lines.append(f"/* {class_name} 虚函数表初始化 */")
        lines.append(f"static {class_name}_vtable_t {class_name}_vtable = {{")

        # 初始化方法指针
        for i, entry in enumerate(vtable.entries):
            if i > 0:
                lines.append(",")
            lines.append(f"    .method{i + 1} = {class_name}_{entry.method_name}")

        lines.append("")
        lines.append("};")

        return '\n'.join(lines)


# 测试代码
if __name__ == "__main__":
    print("=== Day 14: 方法转换器测试 ===\n")

    # 1. 测试方法转换
    print("1. 测试方法转换:")
    converter = MethodConverter()

    result = converter.convert_method(
        class_name="学生",
        method_code="函数 获取信息() -> 字符串型",
        visibility="public"
    )

    print(f"   转换名称: {result.converted_name}")
    print(f"   函数签名: {result.c_function_signature}")
    print(f"   有this指针: {result.has_this_pointer}")

    # 2. 测试构造函数
    print("\n2. 测试构造函数:")
    result2 = converter.convert_method(
        class_name="学生",
        method_code="函数 构造函数(字符串型 名) -> 空型",
        is_constructor=True
    )

    print(f"   转换名称: {result2.converted_name}")
    print(f"   函数签名: {result2.c_function_signature}")

    # 3. 测试静态方法
    print("\n3. 测试静态方法:")
    result3 = converter.convert_method(
        class_name="学生",
        method_code="函数 获取版本() -> 整数型",
        is_static=True
    )

    print(f"   转换名称: {result3.converted_name}")
    print(f"   有this指针: {result3.has_this_pointer}")
    print(f"   是静态: {result3.is_static}")

    # 4. 测试虚函数表生成器
    print("\n4. 测试虚函数表生成:")
    vtable_gen = VirtualMethodTableGenerator()
    vtable = vtable_gen.create_virtual_table(
        "学生",
        ["获取信息", "设置成绩"]
    )

    print(f"   类名: {vtable.class_name}")
    print(f"   方法数: {len(vtable.entries)}")
    for entry in vtable.entries:
        print(f"   - {entry.method_name}")

    print("\n=== Day 14 测试完成 ===")
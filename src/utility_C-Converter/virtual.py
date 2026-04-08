#!/usr/bin/env python3
"""
Day 16: 虚函数表机制与多态实现

功能：
1. 虚函数表生成
2. 动态绑定
3. 运行时类型识别(RTTI)
4. 多态调用转换
"""

import re
from typing import List, Dict, Optional, Tuple
from enum import Enum


class VirtualFunctionTable:
    """虚函数表"""
    def __init__(self, class_name: str, base_class: Optional[str] = None):
        self.class_name = class_name
        self.base_class = base_class
        self.functions: List[Dict] = []
        self.function_indices: Dict[str, int] = {}

    def add_function(self, name: str, signature: str, index: Optional[int] = None):
        """添加虚函数"""
        if index is None:
            index = len(self.functions)
        self.function_indices[name] = index
        self.functions.append({
            'name': name,
            'signature': signature,
            'index': index
        })

    def get_function_index(self, name: str) -> Optional[int]:
        """获取函数索引"""
        return self.function_indices.get(name)

    def generate_struct(self) -> str:
        """生成虚函数表struct定义"""
        lines = [
            f"/* 虚函数表: {self.class_name} */",
            f"typedef struct {self.class_name}_vtable {{",
            f"    void (**methods)(void *self);  /* 函数指针数组 */"
        ]
        for i, func in enumerate(self.functions):
            lines.append(f"    /* [{i}] {func['name']}: {func['signature']} */")
        lines.append(f"}} {self.class_name}_vtable_t;")
        return '\n'.join(lines)

    def generate_initializer(self) -> str:
        """生成虚函数表初始化代码"""
        func_pointers = []
        for func in self.functions:
            func_pointers.append(f"    (void *){self.class_name}_{func['name']}")
        if not func_pointers:
            func_pointers = ["NULL"]
        return f"static void *{self.class_name}_vtable_data[] = {{\n" + ',\n'.join(func_pointers) + "\n};"


class PolymorphismHandler:
    """多态处理器"""
    def __init__(self):
        self.vtables: Dict[str, VirtualFunctionTable] = {}
        self.rtti_enabled = True

    def register_class(self, class_name: str, base_class: Optional[str] = None) -> VirtualFunctionTable:
        """注册类并创建虚函数表"""
        vtable = VirtualFunctionTable(class_name, base_class)
        self.vtables[class_name] = vtable
        return vtable

    def register_virtual_function(self, class_name: str, func_name: str, signature: str):
        """注册虚函数"""
        if class_name not in self.vtables:
            self.register_class(class_name)
        self.vtables[class_name].add_function(func_name, signature)

    def generate_rtti_struct(self, class_name: str) -> str:
        """生成RTTI结构"""
        vtable = self.vtables.get(class_name)
        if not vtable:
            return ""

        lines = [
            f"/* RTTI: {class_name} */",
            f"typedef struct {class_name}_rtti {{",
            f"    const char *class_name;",
            f"    {vtable.class_name}_vtable_t *vtable;"
        ]
        if vtable.base_class:
            lines.append(f"    {vtable.base_class}_rtti_t *base;")
        lines.append(f"}} {class_name}_rtti_t;")
        return '\n'.join(lines)

    def generate_class_with_vtable(self, class_name: str, members: List[str]) -> str:
        """生成包含虚函数表的类struct"""
        vtable = self.vtables.get(class_name)

        lines = [
            f"/* 类: {class_name} */",
            f"typedef struct {class_name} {{"
        ]

        # RTTI字段
        if self.rtti_enabled and vtable:
            lines.append(f"    {class_name}_rtti_t *rtti;")

        # 虚函数表指针
        if vtable:
            lines.append(f"    {class_name}_vtable_t *vptr;")

        # 成员变量
        for member in members:
            lines.append(f"    {member};")

        lines.append(f"}} {class_name}_t;")
        return '\n'.join(lines)

    def get_vtable_info(self, class_name: str) -> Optional[VirtualFunctionTable]:
        """获取类的虚函数表信息"""
        return self.vtables.get(class_name)


class RTTIGenerator:
    """运行时类型识别生成器"""
    def __init__(self):
        self.class_hierarchy: Dict[str, Optional[str]] = {}
        self.virtual_functions: Dict[str, List[str]] = {}

    def register_class(self, class_name: str, base_class: Optional[str] = None):
        """注册类及其继承关系"""
        self.class_hierarchy[class_name] = base_class
        self.virtual_functions[class_name] = []

    def register_virtual_function(self, class_name: str, func_name: str):
        """注册虚函数"""
        if class_name not in self.virtual_functions:
            self.virtual_functions[class_name] = []
        if func_name not in self.virtual_functions[class_name]:
            self.virtual_functions[class_name].append(func_name)

    def get_inheritance_chain(self, class_name: str) -> List[str]:
        """获取继承链"""
        chain = []
        current: Optional[str] = class_name
        visited = set()
        while current and current not in visited:
            chain.append(current)
            visited.add(current)
            current = self.class_hierarchy.get(current)
        return chain

    def is_base_of(self, base: str, derived: str) -> bool:
        """检查base是否是derived的基类"""
        return base in self.get_inheritance_chain(derived)

    def get_common_base(self, class1: str, class2: str) -> Optional[str]:
        """获取两个类的最近公共基类"""
        chain1 = set(self.get_inheritance_chain(class1))
        chain2 = self.get_inheritance_chain(class2)
        for c in chain2:
            if c in chain1:
                return c
        return None

    def generate_type_check_macro(self) -> str:
        """生成类型检查宏"""
        lines = [
            "/* RTTI类型检查宏 */",
            "#define IS_TYPE(obj, class_name) \\",
            "    ((obj) && (obj)->rtti && \\",
            "     strcmp((obj)->rtti->class_name, #class_name) == 0)",
            "",
            "#define INSTANCE_OF(obj, class_name) IS_TYPE(obj, class_name)"
        ]
        return '\n'.join(lines)

    def generate_dynamic_dispatch(self, class_name: str, func_name: str) -> str:
        """生成动态分派代码"""
        func_index = -1
        # 尝试从virtual_functions中获取索引
        if class_name in self.virtual_functions:
            funcs = self.virtual_functions[class_name]
            if func_name in funcs:
                func_index = funcs.index(func_name)

        lines = [
            f"/* 动态分派: {class_name}.{func_name}() */",
            f"#define DISPATCH_{class_name}_{func_name}(obj) \\",
            f"    ((obj)->vptr->methods[{func_index}])"
        ]
        return '\n'.join(lines)


# 测试
if __name__ == '__main__':
    print("=== 虚函数表生成测试 ===")

    # 创建多态处理器
    handler = PolymorphismHandler()

    # 注册类
    vt_shape = handler.register_class('形状')
    vt_shape.add_function('绘制', 'void draw()')
    vt_shape.add_function('面积', 'double calc_area()')

    vt_circle = handler.register_class('圆形', '形状')
    vt_circle.add_function('绘制', 'void draw()')
    vt_circle.add_function('面积', 'double calc_area()')
    vt_circle.add_function('周长', 'double calc_perimeter()')

    # 生成代码
    print("--- 形状的虚函数表 ---")
    print(vt_shape.generate_struct())
    print()
    print(vt_shape.generate_initializer())
    print()

    print("--- 圆形的虚函数表 ---")
    print(vt_circle.generate_struct())
    print()
    print(vt_circle.generate_initializer())
    print()

    print("--- RTTI结构 ---")
    print(handler.generate_rtti_struct('形状'))
    print()
    print(handler.generate_rtti_struct('圆形'))
    print()

    print("--- 类定义（含虚表） ---")
    print(handler.generate_class_with_vtable('形状', ['int x', 'int y']))
    print()
    print(handler.generate_class_with_vtable('圆形', ['double radius']))
    print()

    # RTTI生成器测试
    print("=== RTTI生成器测试 ===")
    rtti = RTTIGenerator()
    rtti.register_class('形状')
    rtti.register_class('圆形', '形状')
    rtti.register_virtual_function('形状', '绘制')
    rtti.register_virtual_function('圆形', '绘制')

    print(f"圆形的继承链: {rtti.get_inheritance_chain('圆形')}")
    print(f"圆形是形状的子类: {rtti.is_base_of('形状', '圆形')}")
    print(f"最近公共基类: {rtti.get_common_base('圆形', '形状')}")
    print()
    print(rtti.generate_type_check_macro())

    print()
    print("=== 测试完成 ===")
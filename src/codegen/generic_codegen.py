#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泛型代码生成器 - Generic Code Generator

实现泛型的单态化（Monomorphization）：
1. 生成特化后的类型定义
2. 生成特化后的函数定义
3. 名字修饰（Name Mangling）
4. 集成到代码生成流水线

Phase 4 - Stage 2 - Task 11.1 Day 4

作者：ZHC 开发团队
日期：2026-04-08
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple, Any, TYPE_CHECKING
from dataclasses import dataclass, field

# 导入泛型系统
from ..semantic.generics import (
    TypeParameter,
    TypeConstraint,
    GenericType,
    GenericFunction,
    GenericTypeInstance,
    FunctionInstance,
    GenericManager,
    get_generic_manager,
)

# 导入代码生成器
from ..parser.ast_nodes import ASTNode

if TYPE_CHECKING:
    from .c_codegen import CCodeGenerator


# ===== 名字修饰器 =====

class NameMangler:
    """
    名字修饰器
    
    为泛型实例生成唯一的修饰名。
    
    修饰规则：
    - 泛型类型: 类型名<实参1, 实参2, ...> -> 类型名___实参1__实参2
    - 泛型函数: 函数名<实参> -> 函数名___实参
    
    示例：
    - 列表<整数型> -> 列表___整数型
    - 最大值<整数型> -> 最大值___整数型
    """
    
    # 基础类型的修饰名映射
    TYPE_MANGLE_MAP = {
        '整数型': '整数',
        '浮点型': '浮点',
        '双精度型': '双精度',
        '字符型': '字符',
        '字符串型': '字符串',
        '布尔型': '布尔',
        '字节型': '字节',
        '空型': '空',
        '长整数型': '长整数',
        '短整数型': '短整数',
    }
    
    @classmethod
    def mangle_type(cls, generic_name: str, type_args: List[str]) -> str:
        """
        修饰泛型类型名
        
        Args:
            generic_name: 泛型类型名
            type_args: 类型实参列表
            
        Returns:
            修饰后的类型名
        """
        if not type_args:
            return generic_name
        
        # 修饰每个类型实参
        mangle_args = [cls.mangle_type_name(arg) for arg in type_args]
        
        # 使用双下划线分隔
        return f"{generic_name}___{'__'.join(mangle_args)}"
    
    @classmethod
    def mangle_type_name(cls, type_name: str) -> str:
        """
        修饰单个类型名
        
        Args:
            type_name: 类型名
            
        Returns:
            修饰后的类型名
        """
        # 检查映射表
        if type_name in cls.TYPE_MANGLE_MAP:
            return cls.TYPE_MANGLE_MAP[type_name]
        
        # 处理嵌套泛型：映射<字符串型, 整数型>
        if '<' in type_name and '>' in type_name:
            base = type_name.split('<')[0]
            inner = type_name[type_name.find('<')+1:type_name.rfind('>')]
            
            # 解析内部类型
            inner_types = cls._parse_inner_types(inner)
            mangle_inners = [cls.mangle_type_name(t.strip()) for t in inner_types]
            
            return f"{base}___{'__'.join(mangle_inners)}"
        
        return type_name
    
    @classmethod
    def _parse_inner_types(cls, inner: str) -> List[str]:
        """解析嵌套泛型的内部类型"""
        types = []
        current = ""
        depth = 0
        
        for char in inner:
            if char == '<':
                depth += 1
                current += char
            elif char == '>':
                depth -= 1
                current += char
            elif char == ',' and depth == 0:
                types.append(current.strip())
                current = ""
            else:
                current += char
        
        if current.strip():
            types.append(current.strip())
        
        return types
    
    @classmethod
    def mangle_function(cls, generic_name: str, type_args: List[str]) -> str:
        """
        修饰泛型函数名
        
        Args:
            generic_name: 泛型函数名
            type_args: 类型实参列表
            
        Returns:
            修饰后的函数名
        """
        if not type_args:
            return generic_name
        
        # 修饰每个类型实参
        mangle_args = [cls.mangle_type_name(arg) for arg in type_args]
        
        # 使用双下划线分隔
        return f"{generic_name}___{'__'.join(mangle_args)}"
    
    @classmethod
    def unmangle(cls, mangled_name: str) -> Tuple[str, List[str]]:
        """
        反修饰名字
        
        Args:
            mangled_name: 修饰后的名字
            
        Returns:
            (原始名, 类型实参列表)
        """
        # 查找类型参数开始位置
        parts = mangled_name.split('___')
        
        if len(parts) == 1:
            return (mangled_name, [])
        
        original_name = parts[0]
        type_args = cls._unmangle_types(parts[1:])
        
        return (original_name, type_args)
    
    @classmethod
    def _unmangle_types(cls, parts: List[str]) -> List[str]:
        """反修饰类型"""
        # 简单的反修饰（需要更复杂的实现处理嵌套）
        REVERSE_MAP = {v: k for k, v in cls.TYPE_MANGLE_MAP.items()}
        
        result = []
        for part in parts:
            if part in REVERSE_MAP:
                result.append(REVERSE_MAP[part])
            else:
                result.append(part)
        
        return result


# ===== 泛型代码生成器 =====

@dataclass
class GeneratedType:
    """生成的类型"""
    name: str                          # 生成的类型名
    mangled_name: str                   # 修饰后的名字
    original_generic: str               # 原始泛型类型名
    type_args: List[str]                # 类型实参
    code: str                           # 生成的代码
    dependencies: List[str] = field(default_factory=list)  # 依赖的其他类型


@dataclass
class GeneratedFunction:
    """生成的函数"""
    name: str                          # 生成的函数名
    mangled_name: str                   # 修饰后的名字
    original_generic: str               # 原始泛型函数名
    type_args: List[str]                # 类型实参
    code: str                           # 生成的代码
    dependencies: List[str] = field(default_factory=list)  # 依赖的其他类型


class GenericCodeGenerator:
    """
    泛型代码生成器
    
    将泛型类型和函数实例化为具体代码。
    """
    
    def __init__(self, manager: Optional[GenericManager] = None):
        """
        初始化代码生成器
        
        Args:
            manager: 泛型管理器
        """
        self.manager = manager or get_generic_manager()
        
        # 生成的类型
        self._generated_types: Dict[str, GeneratedType] = {}
        
        # 生成的函数
        self._generated_functions: Dict[str, GeneratedFunction] = {}
        
        # 依赖图（用于拓扑排序）
        self._type_deps: Dict[str, Set[str]] = {}
        self._func_deps: Dict[str, Set[str]] = {}
        
        # 待生成的实例请求
        self._pending_types: List[Tuple[str, List[str]]] = []
        self._pending_functions: List[Tuple[str, List[str]]] = []
    
    def request_type_instantiation(
        self,
        generic_name: str,
        type_args: List[str]
    ) -> str:
        """
        请求类型实例化
        
        Args:
            generic_name: 泛型类型名
            type_args: 类型实参列表
            
        Returns:
            生成的类型名
        """
        mangled = NameMangler.mangle_type(generic_name, type_args)
        
        # 如果已经生成，直接返回
        if mangled in self._generated_types:
            return mangled
        
        # 加入待生成队列
        self._pending_types.append((generic_name, type_args))
        
        return mangled
    
    def request_function_instantiation(
        self,
        generic_name: str,
        type_args: List[str]
    ) -> str:
        """
        请求函数实例化
        
        Args:
            generic_name: 泛型函数名
            type_args: 类型实参列表
            
        Returns:
            生成的函数名
        """
        mangled = NameMangler.mangle_function(generic_name, type_args)
        
        # 如果已经生成，直接返回
        if mangled in self._generated_functions:
            return mangled
        
        # 加入待生成队列
        self._pending_functions.append((generic_name, type_args))
        
        return mangled
    
    def generate_all(self, c_generator: 'CCodeGenerator') -> None:
        """
        生成所有待处理的泛型实例
        
        Args:
            c_generator: C 代码生成器
        """
        # 生成类型
        for generic_name, type_args in self._pending_types:
            self._generate_type(generic_name, type_args, c_generator)
        
        # 生成函数
        for generic_name, type_args in self._pending_functions:
            self._generate_function(generic_name, type_args, c_generator)
        
        # 清空待处理队列
        self._pending_types.clear()
        self._pending_functions.clear()
    
    def _generate_type(
        self,
        generic_name: str,
        type_args: List[str],
        c_generator: 'CCodeGenerator'
    ) -> None:
        """
        生成泛型类型的代码
        
        Args:
            generic_name: 泛型类型名
            type_args: 类型实参列表
            c_generator: C 代码生成器
        """
        mangled = NameMangler.mangle_type(generic_name, type_args)
        
        # 检查是否已生成
        if mangled in self._generated_types:
            return
        
        # 获取泛型类型定义
        generic_type = self.manager.get_generic_type(generic_name)
        if generic_type is None:
            return
        
        # 生成类型替换映射
        type_mapping = {
            param.name: arg
            for param, arg in zip(generic_type.type_params, type_args)
        }
        
        # 生成代码
        code = self._generate_type_code(generic_type, type_mapping, c_generator)
        
        # 创建生成的类型
        generated = GeneratedType(
            name=mangled,
            mangled_name=mangled,
            original_generic=generic_name,
            type_args=type_args,
            code=code,
            dependencies=self._extract_type_dependencies(type_args)
        )
        
        self._generated_types[mangled] = generated
    
    def _generate_type_code(
        self,
        generic_type: GenericType,
        type_mapping: Dict[str, str],
        c_generator: 'CCodeGenerator'
    ) -> str:
        """
        生成泛型类型的代码
        
        Args:
            generic_type: 泛型类型定义
            type_mapping: 类型映射
            c_generator: C 代码生成器
            
        Returns:
            生成的 C 代码
        """
        mangled_name = NameMangler.mangle_type(
            generic_type.name,
            list(type_mapping.values())
        )
        
        lines = [f"// 泛型类型实例: {generic_type.name}"]
        lines.append(f"typedef struct {mangled_name} {{")
        
        # 生成成员
        for member in generic_type.members:
            # 替换类型
            member_type = self._substitute_type(member.type_name, type_mapping)
            
            # 生成成员声明
            lines.append(f"    {member_type} {member.name};")
        
        lines.append(f"}} {mangled_name};")
        
        return "\n".join(lines)
    
    def _generate_function(
        self,
        generic_name: str,
        type_args: List[str],
        c_generator: 'CCodeGenerator'
    ) -> None:
        """
        生成泛型函数的代码
        
        Args:
            generic_name: 泛型函数名
            type_args: 类型实参列表
            c_generator: C 代码生成器
        """
        mangled = NameMangler.mangle_function(generic_name, type_args)
        
        # 检查是否已生成
        if mangled in self._generated_functions:
            return
        
        # 获取泛型函数定义
        generic_funcs = self.manager.get_generic_functions(generic_name)
        if not generic_funcs:
            return
        
        # 选择匹配的泛型函数
        generic_func = None
        for gf in generic_funcs:
            if len(gf.type_params) == len(type_args):
                generic_func = gf
                break
        
        if generic_func is None:
            return
        
        # 生成类型替换映射
        type_mapping = {
            param.name: arg
            for param, arg in zip(generic_func.type_params, type_args)
        }
        
        # 生成代码
        code = self._generate_function_code(generic_func, type_mapping, c_generator)
        
        # 创建生成的函数
        generated = GeneratedFunction(
            name=mangled,
            mangled_name=mangled,
            original_generic=generic_name,
            type_args=type_args,
            code=code,
            dependencies=self._extract_type_deps(
                [p.type_name for p in generic_func.params] + [generic_func.return_type]
            )
        )
        
        self._generated_functions[mangled] = generated
    
    def _generate_function_code(
        self,
        generic_func: GenericFunction,
        type_mapping: Dict[str, str],
        c_generator: 'CCodeGenerator'
    ) -> str:
        """
        生成泛型函数的代码
        
        Args:
            generic_func: 泛型函数定义
            type_mapping: 类型映射
            c_generator: C 代码生成器
            
        Returns:
            生成的 C 代码
        """
        mangled_name = NameMangler.mangle_function(
            generic_func.name,
            list(type_mapping.values())
        )
        
        lines = [f"// 泛型函数实例: {generic_func.name}"]
        
        # 生成返回类型
        return_type = self._substitute_type(generic_func.return_type, type_mapping)
        
        # 生成参数列表
        params = []
        for p in generic_func.params:
            param_type = self._substitute_type(p.type_name, type_mapping)
            params.append(f"{param_type} {p.name}")
        
        params_str = ", ".join(params)
        
        # 生成函数签名
        lines.append(f"{return_type} {mangled_name}({params_str}) {{")
        
        # TODO: 生成函数体（需要 AST 遍历和代码生成）
        if generic_func.body is None:
            lines.append("    // 函数体需要从 AST 生成")
        else:
            lines.append("    // 函数体生成待实现")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _substitute_type(self, type_name: str, type_mapping: Dict[str, str]) -> str:
        """
        替换类型
        
        Args:
            type_name: 原始类型名
            type_mapping: 类型映射
            
        Returns:
            替换后的类型名
        """
        # 直接替换
        if type_name in type_mapping:
            return type_mapping[type_name]
        
        # 处理数组类型：T[] -> 整数型[]
        if type_name.endswith('[]'):
            base = type_name[:-2]
            if base in type_mapping:
                return f"{type_mapping[base]}[]"
        
        return type_name
    
    def _extract_type_deps(self, type_names: List[str]) -> List[str]:
        """提取类型依赖"""
        deps = []
        for type_name in type_names:
            # 提取泛型类型
            if '<' in type_name:
                base = type_name.split('<')[0]
                mangled = NameMangler.mangle_type_name(type_name)
                deps.append(mangled)
            else:
                deps.append(type_name)
        return deps
    
    def _extract_type_dependencies(self, type_args: List[str]) -> List[str]:
        """提取类型依赖"""
        return self._extract_type_deps(type_args)
    
    def get_generated_types(self) -> List[GeneratedType]:
        """获取所有生成的类型"""
        return list(self._generated_types.values())
    
    def get_generated_functions(self) -> List[GeneratedFunction]:
        """获取所有生成的函数"""
        return list(self._generated_functions.values())
    
    def generate_header(self) -> str:
        """
        生成头文件代码
        
        Returns:
            头文件代码
        """
        lines = [
            "/*",
            " * 泛型实例化头文件",
            " * 由泛型代码生成器自动生成",
            " */",
            "",
            "#ifndef ZHC_GENERICS_H",
            "#define ZHC_GENERICS_H",
            "",
        ]
        
        # 生成类型声明
        for gen_type in self._generated_types.values():
            lines.append(f"// 类型: {gen_type.original_generic}<{', '.join(gen_type.type_args)}>")
            lines.append(f"typedef struct {gen_type.mangled_name} {{")
            lines.append(f"    // 成员...");
            lines.append(f"}} {gen_type.mangled_name};")
            lines.append("")
        
        # 生成函数声明
        for gen_func in self._generated_functions.values():
            lines.append(f"// 函数: {gen_func.original_generic}<{', '.join(gen_func.type_args)}>")
            lines.append(f"// 声明待实现");
            lines.append("")
        
        lines.extend([
            "#endif /* ZHC_GENERICS_H */",
        ])
        
        return "\n".join(lines)
    
    def generate_implementation(self) -> str:
        """
        生成实现文件代码
        
        Returns:
            实现文件代码
        """
        lines = [
            "/*",
            " * 泛型实例化实现文件",
            " * 由泛型代码生成器自动生成",
            " */",
            "",
            "#include \"generics.h\"",
            "",
        ]
        
        # 生成类型定义
        for gen_type in self._generated_types.values():
            lines.append(f"// 类型: {gen_type.original_generic}<{', '.join(gen_type.type_args)}>")
            lines.append(gen_type.code)
            lines.append("")
        
        # 生成函数实现
        for gen_func in self._generated_functions.values():
            lines.append(f"// 函数: {gen_func.original_generic}<{', '.join(gen_func.type_args)}>")
            lines.append(gen_func.code)
            lines.append("")
        
        return "\n".join(lines)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'generated_types': len(self._generated_types),
            'generated_functions': len(self._generated_functions),
            'pending_types': len(self._pending_types),
            'pending_functions': len(self._pending_functions),
        }


# ===== 模块级函数 =====

def generate_generic_code(
    generic_name: str,
    type_args: List[str],
    is_function: bool = False
) -> str:
    """
    生成泛型实例的代码
    
    Args:
        generic_name: 泛型名
        type_args: 类型实参
        is_function: 是否是函数
        
    Returns:
        生成的代码
    """
    generator = GenericCodeGenerator()
    
    if is_function:
        generator.request_function_instantiation(generic_name, type_args)
    else:
        generator.request_type_instantiation(generic_name, type_args)
    
    generator.generate_all(None)  # 需要传入 c_generator
    
    if is_function:
        funcs = generator.get_generated_functions()
        if funcs:
            return funcs[0].code
    else:
        types = generator.get_generated_types()
        if types:
            return types[0].code
    
    return ""


# ===== 测试代码 =====

if __name__ == "__main__":
    print("=" * 70)
    print("测试 1: 名字修饰")
    print("=" * 70)
    
    # 测试类型修饰
    mangled_type = NameMangler.mangle_type("列表", ["整数型"])
    print(f"列表<整数型> -> {mangled_type}")
    
    mangled_pair = NameMangler.mangle_type("对", ["字符串型", "整数型"])
    print(f"对<字符串型, 整数型> -> {mangled_pair}")
    
    # 测试函数修饰
    mangled_func = NameMangler.mangle_function("最大值", ["整数型"])
    print(f"最大值<整数型> -> {mangled_func}")
    
    print("\n" + "=" * 70)
    print("测试 2: 反修饰")
    print("=" * 70)
    
    original, args = NameMangler.unmangle("列表___整数")
    print(f"列表___整数 -> {original}, {args}")
    
    print("\n" + "=" * 70)
    print("测试 3: 嵌套泛型")
    print("=" * 70)
    
    nested = NameMangler.mangle_type("映射", ["字符串型", "列表___整数"])
    print(f"映射<字符串型, 列表<整数型>> -> {nested}")
    
    print("\n" + "=" * 70)
    print("测试 4: 代码生成器")
    print("=" * 70)
    
    generator = GenericCodeGenerator()
    
    # 请求类型实例化
    generator.request_type_instantiation("列表", ["整数型"])
    generator.request_type_instantiation("对", ["字符串型", "浮点型"])
    
    # 请求函数实例化
    generator.request_function_instantiation("最大值", ["整数型"])
    
    # 生成代码（需要 AST）
    print("请求的实例化：")
    print(f"  类型: {generator.get_statistics()['pending_types']}")
    print(f"  函数: {generator.get_statistics()['pending_functions']}")
    
    # 生成头文件
    print("\n生成的头文件：")
    print(generator.generate_header())

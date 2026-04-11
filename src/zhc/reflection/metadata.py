# -*- coding: utf-8 -*-
"""
ZhC 反射 - 类型元数据生成器

从语义分析阶段收集的类型信息生成反射元数据。
复用 type_system.StructLayoutCalculator 计算字段偏移量。

职责：
1. 收集语义分析阶段的类型信息
2. 计算字段布局（偏移量、大小、对齐）
3. 生成 ReflectionTypeInfo 并注册到 TypeRegistry

作者：远
日期：2026-04-11
"""

from typing import List, Optional, Dict, TYPE_CHECKING

from ..type_system.struct_layout import (
    StructLayoutCalculator,
    StructLayout,
)
from .type_info import (
    ReflectionTypeInfo,
    ReflectionFieldInfo,
    ReflectionMethodInfo,
    TypeRegistry,
)

if TYPE_CHECKING:
    from ..semantic.semantic_analyzer import SemanticAnalyzer


class TypeMetadataGenerator:
    """类型元数据生成器

    从语义分析结果生成反射元数据。
    使用方式：
        generator = TypeMetadataGenerator()
        generator.generate_from_semantic(analyzer)
        # 或者手动注册类型
        generator.register_struct("MyStruct", [("x", "整数型"), ("y", "浮点型")])
    """

    def __init__(self, target_platform: str = "linux"):
        """
        初始化生成器

        Args:
            target_platform: 目标平台 ("linux", "windows", "macos")
        """
        self.target_platform = target_platform
        self._layout_calculator = StructLayoutCalculator(target_platform)
        self._struct_members: Dict[
            str, List[tuple]
        ] = {}  # name -> [(member_name, type_name), ...]
        self._struct_bases: Dict[str, Optional[str]] = {}  # name -> base_class_name

    def register_struct_member(
        self, struct_name: str, member_name: str, type_name: str
    ) -> None:
        """注册结构体成员（在语义分析阶段调用）"""
        if struct_name not in self._struct_members:
            self._struct_members[struct_name] = []
        self._struct_members[struct_name].append((member_name, type_name))

    def register_struct_base(self, struct_name: str, base_name: Optional[str]) -> None:
        """注册结构体基类"""
        self._struct_bases[struct_name] = base_name

    def generate_struct_type_info(
        self, struct_name: str
    ) -> Optional[ReflectionTypeInfo]:
        """为结构体生成类型信息"""
        if struct_name not in self._struct_members:
            return None

        # 计算布局
        members = self._struct_members[struct_name]
        layout = self._layout_calculator.calculate_layout(
            struct_name,
            members,
            is_packed=False,
        )

        # 构建 ReflectionFieldInfo 列表
        field_infos = []
        for i, m in enumerate(layout.members):
            # 确定访问修饰符（目前默认 public，后续可从 AST 扩展）
            field_info = ReflectionFieldInfo(
                name=m.name,
                type_name=m.type_name,
                offset=m.offset,
                size=m.size,
                alignment=m.alignment,
                is_public=True,
                is_static=False,
                is_const=False,
            )
            field_infos.append(field_info)

        # 构建 ReflectionTypeInfo
        type_info = ReflectionTypeInfo(
            name=struct_name,
            size=layout.total_size,
            alignment=layout.alignment,
            is_struct=True,
            base_class=self._struct_bases.get(struct_name),
            fields=field_infos,
            methods=[],  # 方法信息需要从语义分析收集
        )

        return type_info

    def generate_all_struct_types(self) -> List[ReflectionTypeInfo]:
        """为所有结构体生成类型信息"""
        results = []
        for struct_name in self._struct_members:
            type_info = self.generate_struct_type_info(struct_name)
            if type_info:
                results.append(type_info)
                TypeRegistry.register(type_info)
        return results

    def generate_from_semantic(self, analyzer: "SemanticAnalyzer") -> None:
        """从语义分析器生成类型元数据

        Args:
            analyzer: 已完成分析的 SemanticAnalyzer 实例
        """
        # 注册基本类型
        TypeRegistry.register_primitive_types()

        # 从符号表收集结构体信息
        for name, symbol in analyzer.symbol_table.global_scope.symbols.items():
            if symbol.symbol_type == "结构体":
                self._collect_struct_info(symbol)

        # 计算所有结构体的类型信息
        self.generate_all_struct_types()

    def _collect_struct_info(self, struct_symbol) -> None:
        """从结构体符号收集信息"""
        struct_name = struct_symbol.name

        # 收集成员
        if struct_symbol.members:
            for member in struct_symbol.members:
                member_type = member.data_type or "整数型"
                self.register_struct_member(struct_name, member.name, member_type)

        # 收集基类
        if struct_symbol.parent_struct:
            self.register_struct_base(struct_name, struct_symbol.parent_struct)

    def register_struct(
        self,
        name: str,
        members: List[tuple],  # [(member_name, type_name), ...]
        base_class: Optional[str] = None,
    ) -> ReflectionTypeInfo:
        """便捷函数：注册结构体类型

        Args:
            name: 结构体名
            members: 成员列表 [(成员名, 类型名), ...]
            base_class: 基类名

        Returns:
            生成的类型信息
        """
        # 记录成员和基类
        for member_name, member_type in members:
            self.register_struct_member(name, member_name, member_type)
        if base_class:
            self.register_struct_base(name, base_class)

        # 生成并注册
        type_info = self.generate_struct_type_info(name)
        if type_info:
            TypeRegistry.register(type_info)
            return type_info

        raise ValueError(f"无法为结构体 {name} 生成类型信息")


class ReflectionMetadataCollector:
    """反射元数据收集器

    在编译过程中收集类型信息，用于生成反射元数据表。
    这个收集器可以在 IR 生成阶段使用。
    """

    def __init__(self):
        """初始化收集器"""
        self._struct_layouts: Dict[str, StructLayout] = {}
        self._struct_methods: Dict[str, List[Dict]] = {}

    def collect_struct_layout(self, name: str, layout: StructLayout) -> None:
        """收集结构体布局"""
        self._struct_layouts[name] = layout

    def collect_struct_method(
        self,
        struct_name: str,
        method_name: str,
        return_type: str,
        param_types: List[str],
        is_static: bool = False,
        is_virtual: bool = False,
    ) -> None:
        """收集结构体方法信息"""
        if struct_name not in self._struct_methods:
            self._struct_methods[struct_name] = []

        method_info = ReflectionMethodInfo(
            name=method_name,
            return_type=return_type,
            params=[{"name": f"arg{i}", "type": t} for i, t in enumerate(param_types)],
            is_static=is_static,
            is_virtual=is_virtual,
        )
        self._struct_methods[struct_name].append(method_info)

    def generate_type_info(self, struct_name: str) -> Optional[ReflectionTypeInfo]:
        """从收集的信息生成类型信息"""
        if struct_name not in self._struct_layouts:
            return None

        layout = self._struct_layouts[struct_name]

        # 构建字段信息
        fields = [
            ReflectionFieldInfo(
                name=m.name,
                type_name=m.type_name,
                offset=m.offset,
                size=m.size,
                alignment=m.alignment,
            )
            for m in layout.members
        ]

        # 构建方法信息
        methods = self._struct_methods.get(struct_name, [])

        return ReflectionTypeInfo(
            name=struct_name,
            size=layout.total_size,
            alignment=layout.alignment,
            is_struct=True,
            fields=fields,
            methods=methods,
        )

    def get_all_type_infos(self) -> List[ReflectionTypeInfo]:
        """获取所有类型信息"""
        return [
            self.generate_type_info(name)
            for name in self._struct_layouts
            if self.generate_type_info(name) is not None
        ]


# 全局生成器实例
_metadata_generator: Optional[TypeMetadataGenerator] = None


def get_metadata_generator(target_platform: str = "linux") -> TypeMetadataGenerator:
    """获取全局元数据生成器实例"""
    global _metadata_generator
    if _metadata_generator is None:
        _metadata_generator = TypeMetadataGenerator(target_platform)
    return _metadata_generator


__all__ = [
    "TypeMetadataGenerator",
    "ReflectionMetadataCollector",
    "get_metadata_generator",
]

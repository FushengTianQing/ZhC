"""文档数据模型模块。

定义文档生成的核心数据结构：
- DocModule: 模块文档
- DocFunction: 函数文档
- DocStructure: 结构体文档
- DocField: 字段文档
- DocParameter: 参数文档
- DocEnum: 枚举文档
- DocConstant: 常量文档
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from .comment_parser import DocComment


class DocVisibility(str, Enum):
    """文档可见性。"""

    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    INTERNAL = "internal"


class DocKind(str, Enum):
    """文档类型。"""

    MODULE = "module"
    FUNCTION = "function"
    METHOD = "method"
    STRUCTURE = "structure"
    CLASS = "class"
    INTERFACE = "interface"
    ENUM = "enum"
    CONSTANT = "constant"
    VARIABLE = "variable"
    TYPE_ALIAS = "type_alias"
    NAMESPACE = "namespace"


@dataclass
class DocParameter:
    """函数参数文档。

    属性:
        name: 参数名
        type: 参数类型
        description: 参数描述
        default: 默认值
        is_optional: 是否可选
        is_variadic: 是否可变参数
    """

    name: str
    type: str = ""
    description: str = ""
    default: Optional[str] = None
    is_optional: bool = False
    is_variadic: bool = False

    def to_dict(self) -> Dict:
        """转换为字典格式。"""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "default": self.default,
            "is_optional": self.is_optional,
            "is_variadic": self.is_variadic,
        }


@dataclass
class DocReturn:
    """函数返回值文档。

    属性:
        type: 返回值类型
        description: 返回值描述
    """

    type: str = ""
    description: str = ""

    def to_dict(self) -> Dict:
        """转换为字典格式。"""
        return {
            "type": self.type,
            "description": self.description,
        }


@dataclass
class DocField:
    """结构体字段文档。

    属性:
        name: 字段名
        type: 字段类型
        description: 字段描述
        default: 默认值
    """

    name: str
    type: str = ""
    description: str = ""
    default: Optional[str] = None

    def to_dict(self) -> Dict:
        """转换为字典格式。"""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "default": self.default,
        }


@dataclass
class DocEnumMember:
    """枚举成员文档。

    属性:
        name: 成员名
        value: 成员值
        description: 成员描述
    """

    name: str
    value: Optional[str] = None
    description: str = ""

    def to_dict(self) -> Dict:
        """转换为字典格式。"""
        return {
            "name": self.name,
            "value": self.value,
            "description": self.description,
        }


@dataclass
class DocBase:
    """文档基类。"""

    name: str
    kind: DocKind = DocKind.FUNCTION  # 默认值，子类会覆盖
    description: str = ""
    comment: Optional[DocComment] = None
    visibility: DocVisibility = DocVisibility.PUBLIC
    deprecated: Optional[str] = None
    since: Optional[str] = None
    author: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    see_also: List[str] = field(default_factory=list)
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    source_column: Optional[int] = None

    def to_dict(self) -> Dict:
        """转换为字典格式。"""
        return {
            "name": self.name,
            "kind": self.kind.value,
            "description": self.description,
            "visibility": self.visibility.value,
            "deprecated": self.deprecated,
            "since": self.since,
            "author": self.author,
            "examples": self.examples,
            "notes": self.notes,
            "see_also": self.see_also,
            "source_file": self.source_file,
            "source_line": self.source_line,
            "source_column": self.source_column,
        }


@dataclass
class DocFunction(DocBase):
    """函数文档。

    属性:
        signature: 函数签名
        parameters: 参数列表
        returns: 返回值
        raises: 抛出异常列表
        is_static: 是否静态函数
        is_const: 是否常量函数
        is_async: 是否异步函数
        is_constructor: 是否构造函数
        is_destructor: 是否析构函数
    """

    signature: str = ""
    parameters: List[DocParameter] = field(default_factory=list)
    returns: Optional[DocReturn] = None
    raises: List[str] = field(default_factory=list)
    is_static: bool = False
    is_const: bool = False
    is_async: bool = False
    is_constructor: bool = False
    is_destructor: bool = False

    def __post_init__(self):
        """初始化后设置 kind。"""
        self.kind = DocKind.FUNCTION

    def get_param(self, name: str) -> Optional[DocParameter]:
        """获取指定参数。

        Args:
            name: 参数名

        Returns:
            参数对象，不存在则返回 None
        """
        for param in self.parameters:
            if param.name == name:
                return param
        return None

    def to_dict(self) -> Dict:
        """转换为字典格式。"""
        result = super().to_dict()
        result.update(
            {
                "signature": self.signature,
                "parameters": [p.to_dict() for p in self.parameters],
                "returns": self.returns.to_dict() if self.returns else None,
                "raises": self.raises,
                "is_static": self.is_static,
                "is_const": self.is_const,
                "is_async": self.is_async,
                "is_constructor": self.is_constructor,
                "is_destructor": self.is_destructor,
            }
        )
        return result


@dataclass
class DocMethod(DocFunction):
    """方法文档。"""

    def __post_init__(self):
        """初始化后设置 kind。"""
        self.kind = DocKind.METHOD


@dataclass
class DocStructure(DocBase):
    """结构体文档。

    属性:
        fields: 字段列表
        methods: 方法列表
        base_types: 基类型列表
        is_union: 是否联合体
    """

    fields: List[DocField] = field(default_factory=list)
    methods: List[DocMethod] = field(default_factory=list)
    base_types: List[str] = field(default_factory=list)
    is_union: bool = False

    def __post_init__(self):
        """初始化后设置 kind。"""
        self.kind = DocKind.STRUCTURE

    def get_field(self, name: str) -> Optional[DocField]:
        """获取指定字段。

        Args:
            name: 字段名

        Returns:
            字段对象，不存在则返回 None
        """
        for field in self.fields:
            if field.name == name:
                return field
        return None

    def get_method(self, name: str) -> Optional[DocMethod]:
        """获取指定方法。

        Args:
            name: 方法名

        Returns:
            方法对象，不存在则返回 None
        """
        for method in self.methods:
            if method.name == name:
                return method
        return None

    def to_dict(self) -> Dict:
        """转换为字典格式。"""
        result = super().to_dict()
        result.update(
            {
                "fields": [f.to_dict() for f in self.fields],
                "methods": [m.to_dict() for m in self.methods],
                "base_types": self.base_types,
                "is_union": self.is_union,
            }
        )
        return result


@dataclass
class DocClass(DocStructure):
    """类文档。"""

    def __post_init__(self):
        """初始化后设置 kind。"""
        self.kind = DocKind.CLASS


@dataclass
class DocInterface(DocBase):
    """接口文档。

    属性:
        methods: 方法签名列表
    """

    methods: List[DocMethod] = field(default_factory=list)

    def __post_init__(self):
        """初始化后设置 kind。"""
        self.kind = DocKind.INTERFACE

    def to_dict(self) -> Dict:
        """转换为字典格式。"""
        result = super().to_dict()
        result.update(
            {
                "methods": [m.to_dict() for m in self.methods],
            }
        )
        return result


@dataclass
class DocEnum(DocBase):
    """枚举文档。

    属性:
        members: 枚举成员列表
        underlying_type: 底层类型
    """

    members: List[DocEnumMember] = field(default_factory=list)
    underlying_type: str = ""

    def __post_init__(self):
        """初始化后设置 kind。"""
        self.kind = DocKind.ENUM

    def get_member(self, name: str) -> Optional[DocEnumMember]:
        """获取指定成员。

        Args:
            name: 成员名

        Returns:
            成员对象，不存在则返回 None
        """
        for member in self.members:
            if member.name == name:
                return member
        return None

    def to_dict(self) -> Dict:
        """转换为字典格式。"""
        result = super().to_dict()
        result.update(
            {
                "members": [m.to_dict() for m in self.members],
                "underlying_type": self.underlying_type,
            }
        )
        return result


@dataclass
class DocConstant(DocBase):
    """常量文档。

    属性:
        type: 常量类型
        value: 常量值
    """

    type: str = ""
    value: Optional[str] = None

    def __post_init__(self):
        """初始化后设置 kind。"""
        self.kind = DocKind.CONSTANT

    def to_dict(self) -> Dict:
        """转换为字典格式。"""
        result = super().to_dict()
        result.update(
            {
                "type": self.type,
                "value": self.value,
            }
        )
        return result


@dataclass
class DocVariable(DocBase):
    """变量文档。

    属性:
        type: 变量类型
        value: 初始值
    """

    type: str = ""
    value: Optional[str] = None

    def __post_init__(self):
        """初始化后设置 kind。"""
        self.kind = DocKind.VARIABLE

    def to_dict(self) -> Dict:
        """转换为字典格式。"""
        result = super().to_dict()
        result.update(
            {
                "type": self.type,
                "value": self.value,
            }
        )
        return result


@dataclass
class DocTypeAlias(DocBase):
    """类型别名文档。

    属性:
        target: 目标类型
    """

    target: str = ""

    def __post_init__(self):
        """初始化后设置 kind。"""
        self.kind = DocKind.TYPE_ALIAS

    def to_dict(self) -> Dict:
        """转换为字典格式。"""
        result = super().to_dict()
        result.update(
            {
                "target": self.target,
            }
        )
        return result


@dataclass
class DocModule(DocBase):
    """模块文档。

    属性:
        functions: 函数列表
        structures: 结构体列表
        classes: 类列表
        interfaces: 接口列表
        enums: 枚举列表
        constants: 常量列表
        variables: 变量列表
        type_aliases: 类型别名列表
        submodules: 子模块列表
        imports: 导入列表
    """

    functions: List[DocFunction] = field(default_factory=list)
    structures: List[DocStructure] = field(default_factory=list)
    classes: List[DocClass] = field(default_factory=list)
    interfaces: List[DocInterface] = field(default_factory=list)
    enums: List[DocEnum] = field(default_factory=list)
    constants: List[DocConstant] = field(default_factory=list)
    variables: List[DocVariable] = field(default_factory=list)
    type_aliases: List[DocTypeAlias] = field(default_factory=list)
    submodules: List[DocModule] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)

    def __post_init__(self):
        """初始化后设置 kind。"""
        self.kind = DocKind.MODULE

    def get_function(self, name: str) -> Optional[DocFunction]:
        """获取指定函数。"""
        for func in self.functions:
            if func.name == name:
                return func
        return None

    def get_structure(self, name: str) -> Optional[DocStructure]:
        """获取指定结构体。"""
        for struct in self.structures:
            if struct.name == name:
                return struct
        return None

    def get_class(self, name: str) -> Optional[DocClass]:
        """获取指定类。"""
        for cls in self.classes:
            if cls.name == name:
                return cls
        return None

    def get_enum(self, name: str) -> Optional[DocEnum]:
        """获取指定枚举。"""
        for enum in self.enums:
            if enum.name == name:
                return enum
        return None

    def get_constant(self, name: str) -> Optional[DocConstant]:
        """获取指定常量。"""
        for const in self.constants:
            if const.name == name:
                return const
        return None

    def all_functions(self) -> List[DocFunction]:
        """获取所有函数（包括子模块）。"""
        result = list(self.functions)
        for submodule in self.submodules:
            result.extend(submodule.all_functions())
        return result

    def all_structures(self) -> List[DocStructure]:
        """获取所有结构体（包括子模块）。"""
        result = list(self.structures)
        for submodule in self.submodules:
            result.extend(submodule.all_structures())
        return result

    def to_dict(self) -> Dict:
        """转换为字典格式。"""
        result = super().to_dict()
        result.update(
            {
                "functions": [f.to_dict() for f in self.functions],
                "structures": [s.to_dict() for s in self.structures],
                "classes": [c.to_dict() for c in self.classes],
                "interfaces": [i.to_dict() for i in self.interfaces],
                "enums": [e.to_dict() for e in self.enums],
                "constants": [c.to_dict() for c in self.constants],
                "variables": [v.to_dict() for v in self.variables],
                "type_aliases": [t.to_dict() for t in self.type_aliases],
                "submodules": [s.to_dict() for s in self.submodules],
                "imports": self.imports,
            }
        )
        return result


@dataclass
class DocProject:
    """项目文档。

    属性:
        name: 项目名
        version: 版本
        description: 项目描述
        modules: 模块列表
        root_module: 根模块
    """

    name: str = ""
    version: str = ""
    description: str = ""
    modules: List[DocModule] = field(default_factory=list)
    root_module: Optional[DocModule] = None

    def get_module(self, name: str) -> Optional[DocModule]:
        """获取指定模块。"""
        for module in self.modules:
            if module.name == name:
                return module
        return None

    def to_dict(self) -> Dict:
        """转换为字典格式。"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "modules": [m.to_dict() for m in self.modules],
            "root_module": self.root_module.to_dict() if self.root_module else None,
        }

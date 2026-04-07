# -*- coding: utf-8 -*-
"""
ZHC IR - 统一的 Symbol 和 Scope 定义

合并自：
- semantic/semantic_analyzer.py: Symbol, Scope, ScopeType（主语义分析）
- analyzer/scope_checker.py: SymbolCategory（符号类别枚举）

作者：远
日期：2026-04-03
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict


class SymbolCategory(Enum):
    """符号类别（来自 analyzer/scope_checker.py）"""
    VARIABLE = "variable"       # 变量
    FUNCTION = "function"       # 函数
    PARAMETER = "parameter"     # 参数
    TYPEDEF = "typedef"        # 类型定义
    STRUCT = "struct"          # 结构体
    MODULE = "module"          # 模块
    LABEL = "label"            # 标签


class ScopeType(Enum):
    """作用域类型（来自 semantic/semantic_analyzer.py）"""
    GLOBAL = "全局"
    MODULE = "模块"
    STRUCT = "结构体"
    FUNCTION = "函数"
    BLOCK = "代码块"
    LOOP = "循环"


@dataclass
class Symbol:
    """
    统一的符号信息

    合并自 semantic.Symbol 的功能字段 + scope_checker.SymbolCategory 枚举。

    字段说明：
    - name: 符号名称
    - symbol_type: 符号类型（字符串，中文，如"变量"/"函数"）
    - category: 符号类别（枚举，等价于 symbol_type）
    - data_type: 数据类型（中文类型名，如"整数型"）
    - scope_level: 作用域层级
    - is_defined: 是否已定义
    - is_used: 是否被使用
    - definition_location: 定义位置（"行:列"格式）
    - references: 引用位置列表
    - parameters: 函数参数列表（仅函数符号）
    - return_type: 函数返回类型（仅函数符号）
    - members: 结构体成员列表（仅结构体符号）
    """
    name: str = ""
    symbol_type: str = ""  # "变量"/"函数"/"参数"等（中文）
    data_type: Optional[str] = None
    scope_level: int = 0
    scope_type: ScopeType = ScopeType.GLOBAL
    is_defined: bool = False
    is_used: bool = False
    definition_location: Optional[str] = None
    references: List[str] = field(default_factory=list)

    # 函数特有
    parameters: List['Symbol'] = field(default_factory=list)
    return_type: Optional[str] = None

    # 结构体特有
    members: List['Symbol'] = field(default_factory=list)
    methods: List['Symbol'] = field(default_factory=list)
    parent_struct: Optional[str] = None

    # 类别（来自 scope_checker.Symbol）
    category: SymbolCategory = SymbolCategory.VARIABLE

    # === 兼容属性 ===

    @property
    def type_info_str(self) -> str:
        """返回类型字符串（兼容 scope_checker.Symbol）"""
        return str(self.data_type) if self.data_type else ""

    @property
    def type_info(self):
        """返回 data_type，兼容某些使用 TypeInfo 的代码"""
        return self.data_type

    @property
    def flags(self) -> Dict[str, bool]:
        """返回符号标志（兼容某些检查代码）"""
        return {
            "is_defined": self.is_defined,
            "is_used": self.is_used,
            "is_global": self.scope_type == ScopeType.GLOBAL,
        }


@dataclass
class Scope:
    """
    统一的作用域

    合并自 semantic.Scope 和 scope_checker.Scope 的功能。
    """
    scope_type: ScopeType = ScopeType.GLOBAL
    scope_name: str = ""
    parent: Optional['Scope'] = None
    symbols: Dict[str, Symbol] = field(default_factory=dict)
    level: int = 0
    children: List['Scope'] = field(default_factory=list)

    def add_symbol(self, symbol: Symbol) -> bool:
        """
        添加符号到当前作用域

        Returns:
            True 表示添加成功，False 表示符号已存在
        """
        if symbol.name in self.symbols:
            return False
        symbol.scope_level = self.level
        symbol.scope_type = self.scope_type
        self.symbols[symbol.name] = symbol
        return True

    def declare(self, symbol: Symbol):
        """声明符号（兼容 scope_checker.Scope 的 declare 方法）"""
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str) -> Optional[Symbol]:
        """
        在当前作用域及父作用域中查找符号

        Returns:
            找到的符号，或 None
        """
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """仅在当前作用域查找符号"""
        return self.symbols.get(name)

    def all_symbols(self) -> Dict[str, Symbol]:
        """递归收集当前作用域及所有子作用域的符号"""
        result = dict(self.symbols)
        for child in self.children:
            result.update(child.all_symbols())
        return result

    def get_unused_symbols(self) -> List[Symbol]:
        """获取当前作用域中未使用的符号"""
        return [s for s in self.symbols.values() if not s.is_used and s.is_defined]

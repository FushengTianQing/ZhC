# -*- coding: utf-8 -*-
"""
ZhC 作用域追踪器

追踪变量的作用域，支持嵌套作用域、函数作用域、块作用域等。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ScopeKind(Enum):
    """作用域种类"""

    GLOBAL = "global"  # 全局作用域
    FUNCTION = "function"  # 函数作用域
    BLOCK = "block"  # 块作用域
    LOOP = "loop"  # 循环作用域
    IF = "if"  # 条件作用域
    CLASS = "class"  # 类作用域
    NAMESPACE = "namespace"  # 命名空间作用域
    STRUCT = "struct"  # 结构体作用域


@dataclass
class ScopeEntry:
    """作用域条目"""

    name: str  # 名称（变量/函数名）
    kind: str  # 种类（variable/function/type/label）
    scope_id: int  # 所属作用域 ID
    declaration_line: int = 0  # 声明行号
    declaration_file: str = ""  # 声明文件
    is_definition: bool = True  # 是否为定义
    is_extern: bool = False  # 是否为外部声明
    attributes: Dict[str, Any] = field(default_factory=dict)  # 额外属性


@dataclass
class Scope:
    """
    作用域

    表示一个词法作用域。
    """

    id: int  # 作用域 ID
    kind: ScopeKind  # 作用域种类
    name: str  # 作用域名称（如函数名）
    parent: Optional["Scope"] = None  # 父作用域

    # 位置信息
    start_line: int = 0  # 起始行号
    end_line: int = 0  # 结束行号
    start_address: int = 0  # 起始地址
    end_address: int = 0  # 结束地址

    # 作用域内容
    entries: Dict[str, ScopeEntry] = field(default_factory=dict)  # 条目
    children: List["Scope"] = field(default_factory=list)  # 子作用域
    labels: Set[str] = field(default_factory=set)  # 跳转标签

    # 属性
    is_lexical: bool = True  # 是否为词法作用域
    contains_asm: bool = False  # 是否包含汇编
    has_exception: bool = False  # 是否包含异常处理

    def add_entry(self, entry: ScopeEntry) -> None:
        """添加条目"""
        entry.scope_id = self.id
        self.entries[entry.name] = entry

    def get_entry(self, name: str) -> Optional[ScopeEntry]:
        """获取条目"""
        return self.entries.get(name)

    def has_entry(self, name: str) -> bool:
        """检查条目是否存在"""
        return name in self.entries

    def add_child(self, child: "Scope") -> None:
        """添加子作用域"""
        child.parent = self
        self.children.append(child)

    def contains_line(self, line: int) -> bool:
        """检查行号是否在作用域内"""
        return self.start_line <= line <= self.end_line

    def contains_address(self, address: int) -> bool:
        """检查地址是否在作用域内"""
        return self.start_address <= address < self.end_address

    def lookup_entry(
        self, name: str, include_ancestors: bool = True
    ) -> Optional[ScopeEntry]:
        """
        查找条目

        Args:
            name: 条目名称
            include_ancestors: 是否包含祖先作用域

        Returns:
            找到的条目或 None
        """
        entry = self.entries.get(name)
        if entry:
            return entry

        if include_ancestors and self.parent:
            return self.parent.lookup_entry(name, True)

        return None

    def get_all_entries(self, include_ancestors: bool = True) -> Dict[str, ScopeEntry]:
        """
        获取所有可见条目

        Args:
            include_ancestors: 是否包含祖先作用域

        Returns:
            条目字典
        """
        result = {}

        if include_ancestors and self.parent:
            result = self.parent.get_all_entries(True).copy()

        result.update(self.entries)
        return result

    def get_variable_names(self, include_ancestors: bool = True) -> List[str]:
        """获取所有变量名"""
        entries = self.get_all_entries(include_ancestors)
        return [name for name, entry in entries.items() if entry.kind == "variable"]

    def get_function_names(self, include_ancestors: bool = True) -> List[str]:
        """获取所有函数名"""
        entries = self.get_all_entries(include_ancestors)
        return [name for name, entry in entries.items() if entry.kind == "function"]

    def get_type_names(self, include_ancestors: bool = True) -> List[str]:
        """获取所有类型名"""
        entries = self.get_all_entries(include_ancestors)
        return [name for name, entry in entries.items() if entry.kind == "type"]

    def depth(self) -> int:
        """计算作用域深度"""
        depth = 0
        scope = self.parent
        while scope:
            depth += 1
            scope = scope.parent
        return depth

    def get_root(self) -> "Scope":
        """获取根作用域"""
        scope = self
        while scope.parent:
            scope = scope.parent
        return scope

    def get_path(self) -> List["Scope"]:
        """获取从根到当前的作用域路径"""
        path = []
        scope = self
        while scope:
            path.append(scope)
            scope = scope.parent
        return list(reversed(path))


class ScopeTracker:
    """
    作用域追踪器

    在编译过程中追踪变量的作用域。
    """

    def __init__(self):
        self.root_scope: Optional[Scope] = None
        self.current_scope: Optional[Scope] = None
        self._scope_counter = 0
        self._function_scopes: Dict[str, Scope] = {}  # 函数名 -> 作用域

    def begin_scope(
        self,
        kind: ScopeKind,
        name: str = "",
        start_line: int = 0,
        end_line: int = 0,
    ) -> Scope:
        """
        开始新的作用域

        Args:
            kind: 作用域种类
            name: 作用域名称
            start_line: 起始行号
            end_line: 结束行号

        Returns:
            创建的作用域
        """
        self._scope_counter += 1
        scope = Scope(
            id=self._scope_counter,
            kind=kind,
            name=name,
            start_line=start_line,
            end_line=end_line,
        )

        if self.current_scope:
            self.current_scope.add_child(scope)
        elif not self.root_scope:
            self.root_scope = scope

        self.current_scope = scope

        # 函数作用域记录
        if kind == ScopeKind.FUNCTION:
            self._function_scopes[name] = scope

        return scope

    def end_scope(self) -> Optional[Scope]:
        """
        结束当前作用域

        Returns:
            结束的作用域
        """
        if not self.current_scope:
            return None

        scope = self.current_scope
        self.current_scope = scope.parent
        return scope

    def add_variable(
        self,
        name: str,
        declaration_line: int = 0,
        declaration_file: str = "",
        is_extern: bool = False,
        **attributes: Any,
    ) -> ScopeEntry:
        """
        添加变量

        Args:
            name: 变量名
            declaration_line: 声明行号
            declaration_file: 声明文件
            is_extern: 是否为外部声明
            **attributes: 额外属性

        Returns:
            创建的条目
        """
        if not self.current_scope:
            raise RuntimeError("No active scope")

        entry = ScopeEntry(
            name=name,
            kind="variable",
            scope_id=self.current_scope.id,
            declaration_line=declaration_line,
            declaration_file=declaration_file,
            is_extern=is_extern,
            is_definition=not is_extern,
            attributes=attributes,
        )
        self.current_scope.add_entry(entry)
        return entry

    def add_function(
        self,
        name: str,
        declaration_line: int = 0,
        declaration_file: str = "",
        is_definition: bool = True,
        **attributes: Any,
    ) -> ScopeEntry:
        """
        添加函数

        Args:
            name: 函数名
            declaration_line: 声明行号
            declaration_file: 声明文件
            is_definition: 是否为定义
            **attributes: 额外属性

        Returns:
            创建的条目
        """
        if not self.current_scope:
            raise RuntimeError("No active scope")

        entry = ScopeEntry(
            name=name,
            kind="function",
            scope_id=self.current_scope.id,
            declaration_line=declaration_line,
            declaration_file=declaration_file,
            is_definition=is_definition,
            is_extern=False,
            attributes=attributes,
        )
        self.current_scope.add_entry(entry)
        return entry

    def add_type(
        self,
        name: str,
        declaration_line: int = 0,
        declaration_file: str = "",
        **attributes: Any,
    ) -> ScopeEntry:
        """
        添加类型

        Args:
            name: 类型名
            declaration_line: 声明行号
            declaration_file: 声明文件
            **attributes: 额外属性

        Returns:
            创建的条目
        """
        if not self.current_scope:
            raise RuntimeError("No active scope")

        entry = ScopeEntry(
            name=name,
            kind="type",
            scope_id=self.current_scope.id,
            declaration_line=declaration_line,
            declaration_file=declaration_file,
            attributes=attributes,
        )
        self.current_scope.add_entry(entry)
        return entry

    def add_label(
        self,
        name: str,
        declaration_line: int = 0,
    ) -> ScopeEntry:
        """
        添加标签

        Args:
            name: 标签名
            declaration_line: 声明行号

        Returns:
            创建的条目
        """
        if not self.current_scope:
            raise RuntimeError("No active scope")

        entry = ScopeEntry(
            name=name,
            kind="label",
            scope_id=self.current_scope.id,
            declaration_line=declaration_line,
        )
        self.current_scope.add_entry(entry)
        self.current_scope.labels.add(name)
        return entry

    def lookup(
        self,
        name: str,
        include_ancestors: bool = True,
    ) -> Optional[ScopeEntry]:
        """
        查找条目

        Args:
            name: 条目名称
            include_ancestors: 是否包含祖先作用域

        Returns:
            找到的条目或 None
        """
        if not self.current_scope:
            return None

        return self.current_scope.lookup_entry(name, include_ancestors)

    def lookup_variable(self, name: str) -> Optional[ScopeEntry]:
        """查找变量"""
        entry = self.lookup(name)
        if entry and entry.kind == "variable":
            return entry
        return None

    def lookup_function(self, name: str) -> Optional[ScopeEntry]:
        """查找函数"""
        entry = self.lookup(name)
        if entry and entry.kind == "function":
            return entry
        return None

    def lookup_type(self, name: str) -> Optional[ScopeEntry]:
        """查找类型"""
        entry = self.lookup(name)
        if entry and entry.kind == "type":
            return entry
        return None

    def get_scope_at_line(self, file: str, line: int) -> Optional[Scope]:
        """
        获取指定行号的作用域

        Args:
            file: 文件名
            line: 行号

        Returns:
            作用域或 None
        """
        if not self.root_scope:
            return None

        return self._find_scope_at_line(self.root_scope, file, line)

    def _find_scope_at_line(
        self,
        scope: Scope,
        file: str,
        line: int,
    ) -> Optional[Scope]:
        """递归查找作用域"""
        if scope.start_line <= line <= scope.end_line:
            # 检查子作用域
            for child in scope.children:
                result = self._find_scope_at_line(child, file, line)
                if result:
                    return result
            return scope

        return None

    def get_scope_at_address(self, address: int) -> Optional[Scope]:
        """
        获取指定地址的作用域

        Args:
            address: 地址

        Returns:
            作用域或 None
        """
        if not self.root_scope:
            return None

        return self._find_scope_at_address(self.root_scope, address)

    def _find_scope_at_address(
        self,
        scope: Scope,
        address: int,
    ) -> Optional[Scope]:
        """递归查找作用域"""
        if scope.contains_address(address):
            # 检查子作用域
            for child in scope.children:
                result = self._find_scope_at_address(child, address)
                if result:
                    return result
            return scope

        return None

    def get_visible_variables(
        self,
        at_line: int = 0,
        at_address: int = 0,
        include_params: bool = True,
    ) -> List[ScopeEntry]:
        """
        获取可见变量

        Args:
            at_line: 指定行号
            at_address: 指定地址
            include_params: 是否包含参数

        Returns:
            可见变量列表
        """
        scope = None

        if at_address > 0:
            scope = self.get_scope_at_address(at_address)
        elif at_line > 0:
            scope = self.get_scope_at_line("", at_line)

        if not scope:
            return []

        variables = []
        for name, entry in scope.get_all_entries().items():
            if entry.kind == "variable":
                if (
                    include_params
                    or entry.kind != "variable"
                    or not entry.attributes.get("is_param", False)
                ):
                    variables.append(entry)

        return variables

    def get_function_scope(self, name: str) -> Optional[Scope]:
        """获取函数作用域"""
        return self._function_scopes.get(name)

    def get_all_function_scopes(self) -> Dict[str, Scope]:
        """获取所有函数作用域"""
        return self._function_scopes.copy()

    def get_current_scope(self) -> Optional[Scope]:
        """获取当前作用域"""
        return self.current_scope

    def get_root_scope(self) -> Optional[Scope]:
        """获取根作用域"""
        return self.root_scope

    def set_scope_range(
        self,
        scope: Optional[Scope] = None,
        start_line: int = 0,
        end_line: int = 0,
        start_address: int = 0,
        end_address: int = 0,
    ) -> None:
        """
        设置作用域范围

        Args:
            scope: 作用域（None 表示当前作用域）
            start_line: 起始行号
            end_line: 结束行号
            start_address: 起始地址
            end_address: 结束地址
        """
        target = scope or self.current_scope
        if not target:
            return

        target.start_line = start_line
        target.end_line = end_line
        target.start_address = start_address
        target.end_address = end_address

    def dump_scope_tree(self, scope: Optional[Scope] = None, indent: int = 0) -> str:
        """
        导出作用域树

        Args:
            scope: 起始作用域（None 表示根作用域）
            indent: 缩进级别

        Returns:
            格式化字符串
        """
        target = scope or self.root_scope
        if not target:
            return ""

        lines = []
        prefix = "  " * indent

        # 作用域信息
        kind_str = target.kind.value
        name_str = f' "{target.name}"' if target.name else ""
        lines.append(f"{prefix}Scope({target.id})[{kind_str}]{name_str}")

        # 变量
        if target.entries:
            for name, entry in target.entries.items():
                kind_str = entry.kind
                line_str = (
                    f":{entry.declaration_line}" if entry.declaration_line else ""
                )
                lines.append(f"{prefix}  {name} ({kind_str}){line_str}")

        # 子作用域
        for child in target.children:
            lines.append(self.dump_scope_tree(child, indent + 1))

        return "\n".join(lines)

    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        if not self.root_scope:
            return {}

        stats = {
            "total_scopes": 0,
            "global_scopes": 0,
            "function_scopes": 0,
            "block_scopes": 0,
            "total_entries": 0,
            "total_variables": 0,
            "total_functions": 0,
            "total_types": 0,
        }

        self._collect_statistics(self.root_scope, stats)
        return stats

    def _collect_statistics(self, scope: Scope, stats: Dict[str, int]) -> None:
        """收集统计信息"""
        stats["total_scopes"] += 1

        if scope.kind == ScopeKind.GLOBAL:
            stats["global_scopes"] += 1
        elif scope.kind == ScopeKind.FUNCTION:
            stats["function_scopes"] += 1
        elif scope.kind == ScopeKind.BLOCK:
            stats["block_scopes"] += 1

        stats["total_entries"] += len(scope.entries)

        for entry in scope.entries.values():
            if entry.kind == "variable":
                stats["total_variables"] += 1
            elif entry.kind == "function":
                stats["total_functions"] += 1
            elif entry.kind == "type":
                stats["total_types"] += 1

        for child in scope.children:
            self._collect_statistics(child, stats)

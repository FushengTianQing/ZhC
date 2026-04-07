"""
ZHC编译器 - 作用域检查器

功能：
- 作用域管理
- 符号可见性检查
- 变量遮蔽检测
- 符号查找

作者：远
日期：2026-04-03
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from .type_checker import TypeInfo


class SymbolCategory(Enum):
    """符号类别"""
    VARIABLE = "variable"       # 变量
    FUNCTION = "function"       # 函数
    PARAMETER = "parameter"     # 参数
    TYPEDEF = "typedef"         # 类型定义
    STRUCT = "struct"           # 结构体
    MODULE = "module"           # 模块
    LABEL = "label"             # 标签


@dataclass
class Symbol:
    """符号信息"""
    name: str                    # 符号名称
    category: SymbolCategory     # 符号类别
    type_info: TypeInfo          # 类型信息
    line: int                    # 定义行号
    is_global: bool = False      # 是否全局符号
    is_static: bool = False      # 是否静态
    is_const: bool = False       # 是否常量
    is_initialized: bool = False  # 是否已初始化
    is_used: bool = False        # 是否被使用
    scope_level: int = 0         # 作用域层级


class Scope:
    """作用域"""
    
    def __init__(self, level: int, parent: Optional['Scope'] = None):
        """
        初始化作用域
        
        Args:
            level: 作用域层级（0=全局，1=函数，2+=代码块）
            parent: 父作用域
        """
        self.level = level
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}
        self.children: List['Scope'] = []
        
        if parent:
            parent.children.append(self)
    
    def declare(self, symbol: Symbol):
        """声明符号"""
        self.symbols[symbol.name] = symbol
    
    def lookup_local(self, name: str) -> Optional[Symbol]:
        """在当前作用域查找符号"""
        return self.symbols.get(name)
    
    def lookup(self, name: str) -> Optional[Symbol]:
        """在当前及父作用域查找符号"""
        # 先在当前作用域查找
        symbol = self.symbols.get(name)
        if symbol:
            return symbol
        
        # 在父作用域查找
        if self.parent:
            return self.parent.lookup(name)
        
        return None
    
    def get_all_symbols(self) -> List[Symbol]:
        """获取当前作用域所有符号"""
        return list(self.symbols.values())
    
    def get_unused_symbols(self) -> List[Symbol]:
        """获取未使用的符号"""
        return [s for s in self.symbols.values() if not s.is_used]


class ScopeChecker:
    """作用域检查器"""
    
    def __init__(self):
        """初始化作用域检查器"""
        self.global_scope = Scope(0)
        self.current_scope = self.global_scope
        self.scope_stack: List[Scope] = [self.global_scope]
        
        self.errors: List[Tuple[int, str, str]] = []
        self.warnings: List[Tuple[int, str, str]] = []
    
    def enter_scope(self):
        """进入新作用域"""
        new_scope = Scope(
            level=self.current_scope.level + 1,
            parent=self.current_scope
        )
        self.current_scope = new_scope
        self.scope_stack.append(new_scope)
    
    def exit_scope(self) -> Scope:
        """
        退出当前作用域
        
        Returns:
            退出的作用域（用于检查未使用符号）
        """
        exited_scope = self.current_scope
        
        # 检查未使用的符号
        for symbol in exited_scope.get_unused_symbols():
            if symbol.category == SymbolCategory.VARIABLE:
                self.warnings.append((
                    symbol.line,
                    "未使用变量",
                    f"变量 '{symbol.name}' 已声明但未使用"
                ))
        
        self.scope_stack.pop()
        
        if self.scope_stack:
            self.current_scope = self.scope_stack[-1]
        else:
            self.current_scope = self.global_scope
        
        return exited_scope
    
    def declare_variable(
        self,
        line: int,
        name: str,
        type_info: TypeInfo,
        is_const: bool = False,
        is_initialized: bool = False
    ) -> bool:
        """
        声明变量
        
        Args:
            line: 行号
            name: 变量名
            type_info: 类型信息
            is_const: 是否常量
            is_initialized: 是否已初始化
        
        Returns:
            是否声明成功
        """
        # 检查是否在当前作用域已声明
        existing = self.current_scope.lookup_local(name)
        if existing:
            self.errors.append((
                line,
                "重复声明",
                f"变量 '{name}' 在当前作用域已声明（行 {existing.line}）"
            ))
            return False
        
        # 检查变量遮蔽
        shadowed = self.current_scope.parent.lookup(name) if self.current_scope.parent else None
        if shadowed:
            self.warnings.append((
                line,
                "变量遮蔽",
                f"变量 '{name}' 遮蔽了外层作用域的变量（行 {shadowed.line}）"
            ))
        
        # 声明变量
        symbol = Symbol(
            name=name,
            category=SymbolCategory.VARIABLE,
            type_info=type_info,
            line=line,
            is_global=(self.current_scope.level == 0),
            is_const=is_const,
            is_initialized=is_initialized,
            scope_level=self.current_scope.level
        )
        
        self.current_scope.declare(symbol)
        return True
    
    def declare_function(
        self,
        line: int,
        name: str,
        type_info: TypeInfo,
        is_static: bool = False
    ) -> bool:
        """
        声明函数
        
        Args:
            line: 行号
            name: 函数名
            type_info: 函数类型
            is_static: 是否静态函数
        
        Returns:
            是否声明成功
        """
        # 函数只能在全局作用域声明
        if self.current_scope.level > 0:
            self.errors.append((
                line,
                "函数声明位置错误",
                f"函数 '{name}' 只能在全局作用域声明"
            ))
            return False
        
        # 检查是否已声明
        existing = self.global_scope.lookup_local(name)
        if existing and existing.category == SymbolCategory.FUNCTION:
            self.warnings.append((
                line,
                "函数重定义",
                f"函数 '{name}' 已声明（行 {existing.line}），将被覆盖"
            ))
        
        # 声明函数
        symbol = Symbol(
            name=name,
            category=SymbolCategory.FUNCTION,
            type_info=type_info,
            line=line,
            is_global=True,
            is_static=is_static,
            scope_level=0
        )
        
        self.global_scope.declare(symbol)
        return True
    
    def declare_parameter(
        self,
        line: int,
        name: str,
        type_info: TypeInfo
    ) -> bool:
        """
        声明函数参数
        
        Args:
            line: 行号
            name: 参数名
            type_info: 类型信息
        
        Returns:
            是否声明成功
        """
        # 参数应该在函数作用域声明
        if self.current_scope.level != 1:
            self.errors.append((
                line,
                "参数声明位置错误",
                f"参数 '{name}' 应该在函数作用域声明"
            ))
            return False
        
        # 检查重复
        existing = self.current_scope.lookup_local(name)
        if existing:
            self.errors.append((
                line,
                "重复参数",
                f"参数 '{name}' 已声明（行 {existing.line}）"
            ))
            return False
        
        # 声明参数
        symbol = Symbol(
            name=name,
            category=SymbolCategory.PARAMETER,
            type_info=type_info,
            line=line,
            is_initialized=True,  # 参数默认已初始化
            scope_level=1
        )
        
        self.current_scope.declare(symbol)
        return True
    
    def lookup_symbol(self, line: int, name: str) -> Optional[Symbol]:
        """
        查找符号
        
        Args:
            line: 行号
            name: 符号名
        
        Returns:
            符号信息，如果未找到则返回None
        """
        symbol = self.current_scope.lookup(name)
        
        if not symbol:
            self.errors.append((
                line,
                "未声明符号",
                f"符号 '{name}' 未声明"
            ))
            return None
        
        # 标记为已使用
        symbol.is_used = True
        
        return symbol
    
    def check_assignable(self, line: int, name: str) -> Optional[Symbol]:
        """
        检查符号是否可赋值
        
        Args:
            line: 行号
            name: 符号名
        
        Returns:
            符号信息，如果不可赋值则返回None
        """
        symbol = self.lookup_symbol(line, name)
        
        if not symbol:
            return None
        
        # 检查是否为常量
        if symbol.is_const:
            self.errors.append((
                line,
                "常量赋值",
                f"常量 '{name}' 不能被赋值"
            ))
            return None
        
        return symbol
    
    def mark_initialized(self, name: str):
        """标记变量已初始化"""
        symbol = self.current_scope.lookup_local(name)
        if symbol:
            symbol.is_initialized = True
    
    def check_initialized(self, line: int, name: str) -> bool:
        """
        检查变量是否已初始化
        
        Args:
            line: 行号
            name: 变量名
        
        Returns:
            是否已初始化
        """
        symbol = self.current_scope.lookup(name)
        
        if not symbol:
            return False
        
        if not symbol.is_initialized:
            self.warnings.append((
                line,
                "未初始化变量",
                f"变量 '{name}' 可能未初始化"
            ))
            return False
        
        return True
    
    def declare_typedef(
        self,
        line: int,
        name: str,
        type_info: TypeInfo
    ) -> bool:
        """
        声明类型定义
        
        Args:
            line: 行号
            name: 类型名
            type_info: 类型信息
        
        Returns:
            是否声明成功
        """
        # 检查是否已存在
        existing = self.global_scope.lookup_local(name)
        if existing:
            self.errors.append((
                line,
                "类型重定义",
                f"类型 '{name}' 已定义（行 {existing.line}）"
            ))
            return False
        
        # 声明类型
        symbol = Symbol(
            name=name,
            category=SymbolCategory.TYPEDEF,
            type_info=type_info,
            line=line,
            is_global=True,
            scope_level=0
        )
        
        self.global_scope.declare(symbol)
        return True
    
    def declare_label(self, line: int, name: str) -> bool:
        """
        声明标签
        
        Args:
            line: 行号
            name: 标签名
        
        Returns:
            是否声明成功
        """
        # 标签在函数作用域声明
        if self.current_scope.level < 1:
            self.errors.append((
                line,
                "标签位置错误",
                f"标签 '{name}' 只能在函数内部声明"
            ))
            return False
        
        # 检查重复
        existing = self.current_scope.lookup_local(name)
        if existing and existing.category == SymbolCategory.LABEL:
            self.errors.append((
                line,
                "重复标签",
                f"标签 '{name}' 已声明（行 {existing.line}）"
            ))
            return False
        
        # 声明标签
        symbol = Symbol(
            name=name,
            category=SymbolCategory.LABEL,
            type_info=TypeInfo(name="标签", category=TypeInfo.__class__.__name__),
            line=line,
            scope_level=self.current_scope.level
        )
        
        self.current_scope.declare(symbol)
        return True
    
    def get_scope_level(self) -> int:
        """获取当前作用域层级"""
        return self.current_scope.level
    
    def is_global_scope(self) -> bool:
        """是否在全局作用域"""
        return self.current_scope.level == 0
    
    def is_function_scope(self) -> bool:
        """是否在函数作用域"""
        return self.current_scope.level == 1
    
    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0
    
    def get_errors(self) -> List[Tuple[int, str, str]]:
        """获取所有错误"""
        return self.errors
    
    def get_warnings(self) -> List[Tuple[int, str, str]]:
        """获取所有警告"""
        return self.warnings
    
    def clear(self):
        """清空错误和警告"""
        self.errors.clear()
        self.warnings.clear()
    
    def report(self) -> str:
        """生成作用域检查报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("作用域检查报告")
        lines.append("=" * 60)
        
        if self.errors:
            lines.append(f"\n错误 ({len(self.errors)}):")
            for line, error_type, message in self.errors:
                lines.append(f"  行 {line}: [{error_type}] {message}")
        else:
            lines.append("\n✅ 无作用域错误")
        
        if self.warnings:
            lines.append(f"\n警告 ({len(self.warnings)}):")
            for line, warning_type, message in self.warnings:
                lines.append(f"  行 {line}: [{warning_type}] {message}")
        else:
            lines.append("\n✅ 无作用域警告")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
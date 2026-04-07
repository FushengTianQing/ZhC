#!/usr/bin/env python3
"""
作用域管理器

实现四级作用域体系：
1. 全局作用域 (global): 程序级别，包含所有模块声明
2. 模块作用域 (module): 模块级别，包含模块内所有符号
3. 文件作用域 (file): 文件级别，包含文件内的静态符号
4. 块作用域 (block): 代码块级别，包含局部变量

支持可见性控制：
- 公开 (public): 对其他模块可见
- 私有 (private): 仅对当前模块可见（默认）
- 保护 (protected): 对当前模块和子模块可见
"""

from typing import List, Dict, Set, Optional
from enum import Enum

class Visibility(Enum):
    """可见性枚举"""
    PUBLIC = 'public'
    PRIVATE = 'private'
    PROTECTED = 'protected'

class ScopeType(Enum):
    """作用域类型枚举"""
    GLOBAL = 'global'
    MODULE = 'module'
    FILE = 'file'
    BLOCK = 'block'

class SymbolInfo:
    """符号信息"""
    def __init__(self, name: str, visibility: Visibility, scope_type: ScopeType, line_num: int):
        self.name = name
        self.visibility = visibility
        self.scope_type = scope_type
        self.line_num = line_num
        self.qualified_name = name  # 初始为原始名称
        
    def set_qualified_name(self, qualified: str):
        """设置限定名"""
        self.qualified_name = qualified
        
    def __str__(self) -> str:
        return f"Symbol({self.name} -> {self.qualified_name}, {self.visibility}, line:{self.line_num})"

class Scope:
    """作用域类"""
    def __init__(self, name: str, scope_type: ScopeType, parent: Optional['Scope'] = None):
        self.name = name
        self.type = scope_type
        self.parent = parent
        self.children: List[Scope] = []
        self.symbols: Dict[str, SymbolInfo] = {}
        self.depth: int = (parent.depth + 1) if parent else 0
        
    def add_symbol(self, symbol: SymbolInfo):
        """添加符号到当前作用域"""
        self.symbols[symbol.name] = symbol
        
    def find_symbol(self, symbol_name: str) -> Optional[SymbolInfo]:
        """在当前作用域查找符号"""
        return self.symbols.get(symbol_name)
        
    def lookup_symbol(self, symbol_name: str) -> Optional[SymbolInfo]:
        """在当前作用域链中查找符号（向上搜索）"""
        current: Optional[Scope] = self
        while current:
            symbol = current.find_symbol(symbol_name)
            if symbol:
                return symbol
            current = current.parent
        return None
        
    def can_see(self, symbol: SymbolInfo, from_scope: 'Scope') -> bool:
        """判断从from_scope能否看到此符号"""
        
        # 1. 如果符号在当前作用域，总是可见
        if symbol.name in self.symbols:
            return True
            
        # 2. 根据可见性规则判断
        if symbol.visibility == Visibility.PUBLIC:
            # 公开符号对所有作用域可见
            return True
            
        elif symbol.visibility == Visibility.PRIVATE:
            # 私有符号：仅对同模块内的作用域可见
            if self.type == ScopeType.MODULE:
                return from_scope.get_module() == self.get_module()
            else:
                # 对于非模块作用域，需要检查它们是否属于同一个模块
                from_module = from_scope.get_module()
                to_module = self.get_module()
                return from_module == to_module and from_module is not None
                
        elif symbol.visibility == Visibility.PROTECTED:
            # 保护符号：对同模块和子模块可见
            # TODO: 实现子模块逻辑
            return self.can_see(symbol, from_scope)  # 暂时与私有相同
            
        return False
        
    def get_module(self) -> Optional['Scope']:
        """获取所属的模块作用域"""
        current: Optional[Scope] = self
        while current:
            if current.type == ScopeType.MODULE:
                return current
            current = current.parent
        return None
        
    def get_full_path(self) -> str:
        """获取完整的作用域路径"""
        path_parts: List[str] = []
        current: Optional[Scope] = self
        
        while current:
            if current.name:
                path_parts.insert(0, current.name)
            current = current.parent
            
        return '::'.join(path_parts) if path_parts else '::'
        
    def __str__(self) -> str:
        return f"Scope({self.type.name}:{self.name}, depth:{self.depth}, symbols:{len(self.symbols)})"

class ScopeManager:
    """作用域管理器"""
    
    def __init__(self):
        self.global_scope = Scope('global', ScopeType.GLOBAL)
        self.current_scope = self.global_scope
        self.scope_stack: List[Scope] = [self.global_scope]
        
        # 模块管理
        self.modules: Dict[str, Scope] = {}
        
        # 符号表（全局）
        self.all_symbols: Dict[str, SymbolInfo] = {}
        
    def enter_scope(self, name: str, scope_type: ScopeType) -> Scope:
        """进入新作用域"""
        new_scope = Scope(name, scope_type, self.current_scope)
        self.current_scope.children.append(new_scope)
        self.current_scope = new_scope
        self.scope_stack.append(new_scope)
        
        # 如果是模块作用域，记录下来
        if scope_type == ScopeType.MODULE:
            self.modules[name] = new_scope
            print(f"进入模块作用域: {name}")
        elif scope_type == ScopeType.FILE:
            print(f"进入文件作用域: {name}")
        elif scope_type == ScopeType.BLOCK:
            print(f"进入块作用域: {name}")
            
        return new_scope
        
    def exit_scope(self) -> Scope:
        """退出当前作用域"""
        if len(self.scope_stack) > 1:
            exited = self.scope_stack.pop()
            self.current_scope = self.scope_stack[-1]
            
            # 输出调试信息
            if exited.type == ScopeType.MODULE:
                print(f"退出模块作用域: {exited.name}")
            elif exited.type == ScopeType.FILE:
                print(f"退出文件作用域: {exited.name}")
            elif exited.type == ScopeType.BLOCK:
                print(f"退出块作用域: {exited.name}")
                
            return exited
        return self.current_scope
        
    def add_symbol(self, name: str, visibility: Visibility, line_num: int) -> SymbolInfo:
        """在当前作用域添加符号"""
        
        # 创建符号信息
        symbol = SymbolInfo(name, visibility, self.current_scope.type, line_num)
        
        # 添加到当前作用域
        self.current_scope.add_symbol(symbol)
        
        # 添加到全局符号表
        self.all_symbols[name] = symbol
        
        # 根据作用域类型和可见性确定限定名
        if self.current_scope.type == ScopeType.MODULE:
            if visibility == Visibility.PUBLIC:
                # 公开符号：模块_符号名
                qualified = f"{self.current_scope.name}_{name}"
                symbol.set_qualified_name(qualified)
                print(f"添加公开模块符号: {name} -> {qualified} (行:{line_num})")
            elif visibility == Visibility.PRIVATE:
                # 私有符号：static 模块_符号名
                qualified = f"{self.current_scope.name}_{name}"
                symbol.set_qualified_name(qualified)
                print(f"添加私有模块符号: {name} -> static {qualified} (行:{line_num})")
            else:
                # 保护符号：暂时与私有相同
                qualified = f"{self.current_scope.name}_{name}"
                symbol.set_qualified_name(qualified)
                print(f"添加保护模块符号: {name} -> {qualified} (行:{line_num})")
        else:
            # 非模块作用域的符号保持原样
            print(f"添加局部符号: {name} (行:{line_num})")
            
        return symbol
        
    def lookup_symbol(self, name: str) -> Optional[SymbolInfo]:
        """查找符号（从当前作用域向上搜索）"""
        return self.current_scope.lookup_symbol(name)
        
    def resolve_import(self, module_name: str, from_module: str) -> List[str]:
        """解析模块导入，返回可访问的符号列表"""
        if module_name not in self.modules:
            print(f"错误: 模块 '{module_name}' 未找到")
            return []
            
        imported_module = self.modules[module_name]
        accessible_symbols = []
        
        # 获取导入模块中的所有符号
        for symbol_name, symbol_info in imported_module.symbols.items():
            # 判断符号是否对当前模块可见
            if imported_module.can_see(symbol_info, self.current_scope):
                accessible_symbols.append(symbol_info.qualified_name)
                
        print(f"从模块 '{module_name}' 导入 {len(accessible_symbols)} 个符号")
        return accessible_symbols
        
    def get_scope_tree(self) -> str:
        """获取作用域树形结构"""
        lines = []
        
        def print_scope(scope: Scope, depth: int):
            indent = "  " * depth
            lines.append(f"{indent}{scope}")
            
            # 打印此作用域的符号
            for symbol in scope.symbols.values():
                lines.append(f"{indent}  {symbol}")
                
            # 递归打印子作用域
            for child in scope.children:
                print_scope(child, depth + 1)
                
        print_scope(self.global_scope, 0)
        return '\n'.join(lines)
        
    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        stats = {
            'total_scopes': len(self.scope_stack),
            'total_symbols': len(self.all_symbols),
            'modules': len(self.modules),
            'public_symbols': 0,
            'private_symbols': 0,
            'protected_symbols': 0,
        }
        
        for symbol in self.all_symbols.values():
            if symbol.visibility == Visibility.PUBLIC:
                stats['public_symbols'] += 1
            elif symbol.visibility == Visibility.PRIVATE:
                stats['private_symbols'] += 1
            elif symbol.visibility == Visibility.PROTECTED:
                stats['protected_symbols'] += 1
                
        return stats

# 测试代码
if __name__ == "__main__":
    print("=== 作用域管理器测试 ===\n")
    
    # 创建作用域管理器
    manager = ScopeManager()
    
    # 测试1: 创建模块作用域
    print("测试1: 创建模块'数学库'")
    math_module = manager.enter_scope("数学库", ScopeType.MODULE)
    
    # 在模块内添加符号
    manager.add_symbol("圆周率", Visibility.PUBLIC, 10)
    manager.add_symbol("内部变量", Visibility.PRIVATE, 12)
    manager.add_symbol("保护函数", Visibility.PROTECTED, 15)
    
    # 进入文件作用域
    print("\n测试2: 在模块内创建文件作用域")
    manager.enter_scope("utils.c", ScopeType.FILE)
    
    # 添加文件级符号
    manager.add_symbol("工具函数", Visibility.PRIVATE, 20)
    
    # 进入块作用域
    print("\n测试3: 创建块作用域")
    manager.enter_scope("", ScopeType.BLOCK)
    manager.add_symbol("局部变量", Visibility.PRIVATE, 25)
    
    # 逐级退出作用域
    print("\n测试4: 逐级退出作用域")
    manager.exit_scope()  # 退出块
    manager.exit_scope()  # 退出文件
    manager.exit_scope()  # 退出模块
    
    # 显示作用域树
    print("\n=== 作用域树 ===")
    print(manager.get_scope_tree())
    
    # 显示统计信息
    print("\n=== 统计信息 ===")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
        
    print("\n测试完成！")
"""
语义分析器
Semantic Analyzer

提供语义检查、符号表管理、作用域分析等功能
检测语义错误，收集符号信息，验证类型一致性

更新: 2026-04-03 统一使用 parser.ast_nodes
"""

from __future__ import annotations

from enum import Enum
from typing import Optional, List, Dict, Set, Any
from dataclasses import dataclass, field
from datetime import datetime

from ..errors import SemanticError
from ..parser.ast_nodes import (
    ASTNode, ASTNodeType,
    ProgramNode, ModuleDeclNode, ImportDeclNode,
    FunctionDeclNode, StructDeclNode, VariableDeclNode, ParamDeclNode,
    BlockStmtNode, IfStmtNode, WhileStmtNode, ForStmtNode,
    DoWhileStmtNode, SwitchStmtNode, CaseStmtNode, DefaultStmtNode,
    BreakStmtNode, ContinueStmtNode, ReturnStmtNode, ExprStmtNode,
    GotoStmtNode, LabelStmtNode,
    EnumDeclNode, UnionDeclNode, TypedefDeclNode,
    BinaryExprNode, UnaryExprNode, AssignExprNode, CallExprNode,
    MemberExprNode, ArrayExprNode, IdentifierExprNode,
    TernaryExprNode, SizeofExprNode, CastExprNode,
    ArrayInitNode, StructInitNode,
)


class ScopeType(Enum):
    """作用域类型"""
    GLOBAL = "全局"
    MODULE = "模块"
    STRUCT = "结构体"
    FUNCTION = "函数"
    BLOCK = "代码块"
    LOOP = "循环"


@dataclass
class Symbol:
    """符号信息"""
    name: str = ""
    symbol_type: str = ""  # 变量、函数、结构体、参数等
    data_type: Optional[str] = None
    scope_level: int = 0
    scope_type: ScopeType = ScopeType.GLOBAL
    is_defined: bool = False
    is_used: bool = False
    definition_location: Optional[str] = None
    references: List[str] = field(default_factory=list)
    
    # 函数特有信息
    parameters: List['Symbol'] = field(default_factory=list)
    return_type: Optional[str] = None
    
    # 结构体特有信息
    members: List['Symbol'] = field(default_factory=list)
    methods: List['Symbol'] = field(default_factory=list)
    parent_struct: Optional[str] = None


@dataclass
class SemanticErrorInfo:
    """语义错误信息"""
    error_type: str = ""
    message: str = ""
    location: str = ""
    severity: str = "错误"  # 错误、警告、提示
    suggestions: List[str] = field(default_factory=list)
    source_file: str = ""    # 源文件路径（Phase 5 T1.1 新增）
    
    def __str__(self) -> str:
        prefix = f"{self.source_file}:" if self.source_file else ""
        return f"{prefix}{self.location}: [{self.error_type}] {self.message}"


@dataclass
class Scope:
    """作用域"""
    scope_type: ScopeType = ScopeType.GLOBAL
    scope_name: str = ""
    parent: Optional['Scope'] = None
    symbols: Dict[str, Symbol] = field(default_factory=dict)
    level: int = 0
    
    def add_symbol(self, symbol: Symbol) -> bool:
        """添加符号到当前作用域"""
        if symbol.name in self.symbols:
            return False
        symbol.scope_level = self.level
        symbol.scope_type = self.scope_type
        self.symbols[symbol.name] = symbol
        return True
    
    def lookup(self, name: str) -> Optional[Symbol]:
        """在当前作用域及父作用域中查找符号"""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None
    
    def lookup_local(self, name: str) -> Optional[Symbol]:
        """仅在当前作用域查找符号"""
        return self.symbols.get(name)


class SymbolTable:
    """符号表"""
    
    def __init__(self):
        self.global_scope = Scope(scope_type=ScopeType.GLOBAL, scope_name="全局")
        self.current_scope = self.global_scope
        self.scope_stack: List[Scope] = [self.global_scope]
        self.all_symbols: Dict[str, Symbol] = {}
    
    def enter_scope(self, scope_type: ScopeType, scope_name: str = "") -> Scope:
        """进入新作用域"""
        new_scope = Scope(
            scope_type=scope_type,
            scope_name=scope_name,
            parent=self.current_scope,
            level=self.current_scope.level + 1
        )
        self.scope_stack.append(new_scope)
        self.current_scope = new_scope
        return new_scope
    
    def exit_scope(self) -> Scope:
        """退出当前作用域"""
        if len(self.scope_stack) <= 1:
            raise SemanticError(
                "无法退出全局作用域",
                error_code="S031",
                context="作用域栈只剩全局作用域",
                suggestion="请检查作用域管理逻辑"
            )
        self.scope_stack.pop()
        self.current_scope = self.scope_stack[-1]
        return self.current_scope
    
    def add_symbol(self, symbol: Symbol) -> bool:
        """在当前作用域添加符号
        
        Phase 6 T2.2: 函数重载支持 — 同名但参数签名不同的函数允许，
        参数签名完全相同的仍然报重复定义。
        """
        existing = self.current_scope.lookup_local(symbol.name)
        if existing:
            # 函数重载：同名但参数列表不同的函数允许
            if (existing.symbol_type == "函数" and 
                symbol.symbol_type == "函数" and
                symbol.name == existing.name):
                # 检查参数签名是否不同
                existing_sig = tuple(p.data_type for p in existing.parameters)
                new_sig = tuple(p.data_type for p in symbol.parameters)
                if existing_sig != new_sig:
                    # 参数签名不同，允许重载
                    if not hasattr(existing, '_overloads'):
                        existing._overloads = [existing]
                    existing._overloads.append(symbol)
                    self.all_symbols[f"{self.current_scope.scope_name}.{symbol.name}_{len(existing._overloads)}"] = symbol
                    return True
                # 参数签名相同，不允许
                return False
            return False
        symbol.scope_level = self.current_scope.level
        symbol.scope_type = self.current_scope.scope_type
        self.current_scope.symbols[symbol.name] = symbol
        self.all_symbols[f"{self.current_scope.scope_name}.{symbol.name}"] = symbol
        return True
    
    def lookup(self, name: str) -> Optional[Symbol]:
        """查找符号"""
        return self.current_scope.lookup(name)
    
    def lookup_all(self, name: str) -> List[Symbol]:
        """查找所有同名符号（用于函数重载解析）
        
        Returns:
            同名符号列表；如果有重载则返回所有重载版本，
            否则返回包含单个符号的列表。
        """
        symbol = self.current_scope.lookup(name)
        if symbol is None:
            return []
        if hasattr(symbol, '_overloads'):
            return list(symbol._overloads)
        return [symbol]
    
    def get_unused_symbols(self) -> List[Symbol]:
        """获取未使用的符号"""
        return [s for s in self.all_symbols.values() if not s.is_used and s.is_defined]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取符号表统计信息"""
        return {
            'total_symbols': len(self.all_symbols),
            'scope_count': len(self.scope_stack),
            'current_scope': self.current_scope.scope_name,
            'symbols_by_type': self._count_symbols_by_type()
        }
    
    def _count_symbols_by_type(self) -> Dict[str, int]:
        """按类型统计符号"""
        counts: Dict[str, int] = {}
        for symbol in self.all_symbols.values():
            counts[symbol.symbol_type] = counts.get(symbol.symbol_type, 0) + 1
        return counts


class SemanticAnalyzer:
    """
    语义分析器
    
    执行语义分析，包括：
    - 符号表构建
    - 作用域分析
    - 类型检查
    - 未定义符号检测
    - 未使用符号检测
    """
    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors: List[SemanticErrorInfo] = []
        self.warnings: List[SemanticErrorInfo] = []
        self.current_function: Optional[Symbol] = None
        self.current_struct: Optional[Symbol] = None
        self.in_loop: bool = False
        self.in_switch: bool = False  # Phase 6: switch 内 break 合法
        self.source_file: str = ""  # 源文件路径（Phase 5 T1.1）
        
        # Phase 5 T2.2: 类型检查器
        self._type_checker = None  # 延迟初始化，避免循环导入
        
        # Phase 6 M3: 控制流分析开关
        self.cfg_enabled: bool = True      # 不可达代码检测
        self.uninit_enabled: bool = True   # 未初始化变量检测

        # Phase 6 M4: 标签追踪（goto 存在性检查）
        self._defined_labels: Set[str] = set()  # 当前函数内已定义的标签
        self._goto_targets: List[tuple] = []     # (label_name, line, column) 待验证的 goto

        # Phase 6 M5: 扩展分析器开关
        self.dataflow_enabled: bool = True      # 数据流分析
        self.interprocedural_enabled: bool = True  # 过程间分析
        self.alias_enabled: bool = True         # 别名分析
        self.pointer_enabled: bool = True       # 指针分析

        # Phase 7: AST 缓存管理器 — 缓存 CFG 构建结果，避免重复分析
        self._ast_cache = None  # 延迟初始化

        # Phase 7: 符号查找优化器 — 由 CLI --optimize-symbol-lookup 开关控制
        self.symbol_lookup_enabled = False
        self._symbol_lookup_optimizer = None  # 延迟初始化，bug 修复

        # Phase 8: 泛型管理器 — 管理泛型类型和函数的注册与实例化
        self._generic_manager = None  # 延迟初始化

        # Phase 8: 类型推导引擎 — Hindley-Milner 算法，作为 _infer_expr_type 后备
        self._type_inference_engine = None  # 延迟初始化

        self.stats = {
            'nodes_visited': 0,
            'symbols_added': 0,
            'errors_found': 0,
            'warnings_found': 0
        }
    
    @property
    def type_checker(self):
        """延迟获取 TypeChecker 实例（避免循环导入，Phase 7 升级为带缓存版本）"""
        if self._type_checker is None:
            from ..analyzer.type_checker_cached import TypeCheckerCached
            self._type_checker = TypeCheckerCached()
        return self._type_checker

    def _get_ast_cache(self):
        """延迟获取 AST 缓存管理器实例（避免循环导入）"""
        if self._ast_cache is None:
            from ..analyzer.ast_cache import ASTCacheManager
            self._ast_cache = ASTCacheManager()
        return self._ast_cache

    def _get_symbol_lookup_optimizer(self):
        """延迟获取符号查找优化器实例（Phase 7，开关关闭时返回 None）"""
        if not getattr(self, 'symbol_lookup_enabled', False):
            return None
        if self._symbol_lookup_optimizer is None:
            from ..analyzer.symbol_lookup_optimizer import SymbolLookupOptimizer
            self._symbol_lookup_optimizer = SymbolLookupOptimizer()
        return self._symbol_lookup_optimizer
    
    @property
    def generic_manager(self):
        """延迟获取泛型管理器实例（Phase 8）"""
        if self._generic_manager is None:
            from .generics import GenericManager
            self._generic_manager = GenericManager()
        return self._generic_manager
    
    @property
    def type_inference_engine(self):
        """延迟获取类型推导引擎实例（Phase 8，Hindley-Milner 算法）"""
        if self._type_inference_engine is None:
            from ..typeinfer.engine import TypeInferenceEngine
            self._type_inference_engine = TypeInferenceEngine()
        return self._type_inference_engine
    
    def _node_location(self, node: ASTNode) -> str:
        """获取节点的位置描述"""
        return f"{node.line}:{node.column}"
    
    def analyze(self, ast: ASTNode) -> bool:
        """分析AST树"""
        self._analyze_node(ast)
        self._check_unused_symbols()
        self._run_cfg_analysis(ast)
        return len(self.errors) == 0
    
    def analyze_file(self, ast: ASTNode, source_file: str = "") -> bool:
        """分析AST树（带源文件信息）"""
        self.source_file = source_file
        self._analyze_node(ast)
        self._check_unused_symbols()
        self._run_cfg_analysis(ast)
        return len(self.errors) == 0
    
    def _analyze_node(self, node: ASTNode) -> None:
        """分析单个节点，按 node_type 分发"""
        self.stats['nodes_visited'] += 1
        
        nt = node.node_type
        
        # 程序结构
        if nt == ASTNodeType.PROGRAM:
            self._analyze_program(node)
        elif nt == ASTNodeType.MODULE_DECL:
            self._analyze_module_decl(node)
        elif nt == ASTNodeType.IMPORT_DECL:
            pass  # 导入声明无需深入分析
        
        # 声明
        elif nt == ASTNodeType.FUNCTION_DECL:
            self._analyze_function_decl(node)
        elif nt == ASTNodeType.STRUCT_DECL:
            self._analyze_struct_decl(node)
        elif nt == ASTNodeType.VARIABLE_DECL:
            self._analyze_variable_decl(node)
        elif nt == ASTNodeType.PARAM_DECL:
            pass  # 参数由函数声明处理
        elif nt == ASTNodeType.ENUM_DECL:
            self._analyze_enum_decl(node)
        elif nt == ASTNodeType.UNION_DECL:
            self._analyze_union_decl(node)
        elif nt == ASTNodeType.TYPEDEF_DECL:
            self._analyze_typedef_decl(node)
        
        # 语句
        elif nt == ASTNodeType.BLOCK_STMT:
            self._analyze_block_stmt(node)
        elif nt == ASTNodeType.IF_STMT:
            self._analyze_if_stmt(node)
        elif nt == ASTNodeType.WHILE_STMT:
            self._analyze_while_stmt(node)
        elif nt == ASTNodeType.FOR_STMT:
            self._analyze_for_stmt(node)
        elif nt == ASTNodeType.DO_WHILE_STMT:
            self._analyze_do_while_stmt(node)
        elif nt == ASTNodeType.SWITCH_STMT:
            self._analyze_switch_stmt(node)
        elif nt == ASTNodeType.BREAK_STMT:
            self._analyze_break_stmt(node)
        elif nt == ASTNodeType.CONTINUE_STMT:
            self._analyze_continue_stmt(node)
        elif nt == ASTNodeType.RETURN_STMT:
            self._analyze_return_stmt(node)
        elif nt == ASTNodeType.EXPR_STMT:
            self._analyze_expr_stmt(node)
        elif nt == ASTNodeType.GOTO_STMT:
            self._analyze_goto_stmt(node)
        elif nt == ASTNodeType.LABEL_STMT:
            self._analyze_label_stmt(node)
        elif nt in (ASTNodeType.CASE_STMT, ASTNodeType.DEFAULT_STMT):
            # case/default 语句：递归分析子节点
            for child in node.get_children():
                self._analyze_node(child)
        
        # 表达式
        elif nt == ASTNodeType.IDENTIFIER_EXPR:
            self._analyze_identifier_expr(node)
        elif nt == ASTNodeType.ASSIGN_EXPR:
            self._analyze_assign_expr(node)
        elif nt == ASTNodeType.CALL_EXPR:
            # Phase 6 T2.1: 函数调用参数检查
            self._analyze_call_expr(node)
        elif nt in (ASTNodeType.BINARY_EXPR, ASTNodeType.UNARY_EXPR,
                     ASTNodeType.ARRAY_EXPR):
            # 复合表达式：递归分析子节点
            # Phase 5 T2.3: 标注推导类型
            result_type = self._infer_expr_type(node)
            if result_type:
                node.inferred_type = result_type.name
            for child in node.get_children():
                self._analyze_node(child)
        elif nt == ASTNodeType.MEMBER_EXPR:
            # Phase 6 M4: 成员访问专用分析
            self._analyze_member_expr(node)
        elif nt in (ASTNodeType.TERNARY_EXPR, ASTNodeType.SIZEOF_EXPR,
                     ASTNodeType.CAST_EXPR, ASTNodeType.ARRAY_INIT,
                     ASTNodeType.STRUCT_INIT):
            # 复合表达式/初始化：递归分析子节点
            for child in node.get_children():
                self._analyze_node(child)
        
        # 字面量和类型节点无需深入分析
        else:
            pass
    
    def _analyze_program(self, node: ProgramNode) -> None:
        """分析程序节点"""
        for decl in node.declarations:
            self._analyze_node(decl)
    
    def _analyze_module_decl(self, node: ModuleDeclNode) -> None:
        """分析模块声明节点"""
        self.symbol_table.enter_scope(ScopeType.MODULE, node.name)
        
        for body_node in node.body:
            self._analyze_node(body_node)
        
        self.symbol_table.exit_scope()
    
    def _analyze_function_decl(self, node: FunctionDeclNode) -> None:
        """分析函数声明节点"""
        loc = self._node_location(node)
        
        func_symbol = Symbol(
            name=node.name,
            symbol_type="函数",
            data_type=self._get_type_name(node.return_type),
            return_type=self._get_type_name(node.return_type),
            definition_location=loc,
            is_defined=True
        )
        
        for param in node.params:
            param_symbol = Symbol(
                name=param.name,
                symbol_type="参数",
                data_type=self._get_type_name(param.param_type),
                definition_location=self._node_location(param)
            )
            func_symbol.parameters.append(param_symbol)
        
        if not self.symbol_table.add_symbol(func_symbol):
            self._add_error(
                "重复定义",
                f"函数 '{node.name}' 重复定义",
                loc
            )
            # T3.3: 错误恢复 — 不 return，继续分析函数体以发现更多错误
        
        self.current_function = func_symbol
        if not self.symbol_table.lookup(node.name):
            self.stats['symbols_added'] += 1
        
        self.symbol_table.enter_scope(ScopeType.FUNCTION, node.name)
        
        for param in func_symbol.parameters:
            self.symbol_table.add_symbol(param)
        
        if node.body:
            self._analyze_node(node.body)

        # Phase 6 M4: 验证 goto 目标标签是否存在
        self._validate_goto_targets()

        self.symbol_table.exit_scope()
        self.current_function = None
        
        # Phase 8: 检查是否是泛型函数，若是则注册到 GenericManager
        self._register_generic_function(node)
    
    def _analyze_struct_decl(self, node: StructDeclNode) -> None:
        """分析结构体声明节点"""
        loc = self._node_location(node)
        
        struct_symbol = Symbol(
            name=node.name,
            symbol_type="结构体",
            definition_location=loc,
            is_defined=True
        )
        
        if not self.symbol_table.add_symbol(struct_symbol):
            self._add_error(
                "重复定义",
                f"结构体 '{node.name}' 重复定义",
                loc
            )
            # T3.3: 错误恢复 — 不 return，继续分析成员
        
        self.current_struct = struct_symbol
        if not self.symbol_table.lookup(node.name):
            self.stats['symbols_added'] += 1
        
        self.symbol_table.enter_scope(ScopeType.STRUCT, node.name)
        
        for member in node.members:
            self._analyze_node(member)
            if hasattr(member, 'name'):
                member_type = self._get_type_name(member.var_type) if hasattr(member, 'var_type') else None
                struct_symbol.members.append(
                    Symbol(name=member.name, symbol_type="成员变量", data_type=member_type)
                )
        
        self.symbol_table.exit_scope()
        self.current_struct = None
        
        # Phase 8: 检查是否是泛型类型，若是则注册到 GenericManager
        self._register_generic_type(node)
    
    def _analyze_variable_decl(self, node: VariableDeclNode) -> None:
        """分析变量声明节点"""
        loc = self._node_location(node)
        
        var_symbol = Symbol(
            name=node.name,
            symbol_type="变量",
            data_type=self._get_type_name(node.var_type),
            definition_location=loc,
            is_defined=True
        )
        
        # Phase 7: 变量遮蔽检查（从 scope_checker.py 迁移）
        parent_scope = self.symbol_table.current_scope.parent
        if parent_scope is not None:
            shadowed = parent_scope.lookup(node.name)
            if shadowed is not None:
                self._add_warning(
                    "变量遮蔽",
                    f"变量 '{node.name}' 遮蔽了外层作用域的变量（定义于 {shadowed.definition_location}）",
                    loc,
                    suggestions=[f"考虑使用不同的变量名以避免混淆"]
                )
        
        if not self.symbol_table.add_symbol(var_symbol):
            self._add_error(
                "重复定义",
                f"变量 '{node.name}' 重复定义",
                loc
            )
            return
        
        self.stats['symbols_added'] += 1
        
        # Phase 5 T2.2: 类型检查初始化表达式
        if node.init:
            from .type_utils import ast_type_to_typeinfo
            var_type_info = ast_type_to_typeinfo(node.var_type) if node.var_type else None
            init_type_info = self._infer_expr_type(node.init)
            if var_type_info and init_type_info:
                self._check_type_compat(
                    var_type_info, init_type_info, node,
                    f"初始化变量 '{node.name}'"
                )
            # 无论类型检查是否通过，都要递归分析子节点
            self._analyze_node(node.init)
    
    def _analyze_block_stmt(self, node: BlockStmtNode) -> None:
        """分析代码块"""
        self.symbol_table.enter_scope(ScopeType.BLOCK, "block")
        
        for stmt in node.statements:
            self._analyze_node(stmt)
        
        self.symbol_table.exit_scope()
    
    def _analyze_if_stmt(self, node: IfStmtNode) -> None:
        """分析如果语句"""
        if node.condition:
            self._analyze_node(node.condition)
        if node.then_branch:
            self._analyze_node(node.then_branch)
        if node.else_branch:
            self._analyze_node(node.else_branch)
    
    def _analyze_while_stmt(self, node: WhileStmtNode) -> None:
        """分析当循环"""
        old_in_loop = self.in_loop
        self.in_loop = True
        
        if node.condition:
            self._analyze_node(node.condition)
        if node.body:
            self._analyze_node(node.body)
        
        self.in_loop = old_in_loop
    
    def _analyze_for_stmt(self, node: ForStmtNode) -> None:
        """分析循环语句"""
        old_in_loop = self.in_loop
        self.in_loop = True
        
        self.symbol_table.enter_scope(ScopeType.LOOP, "for_loop")
        
        if node.init:
            self._analyze_node(node.init)
        if node.condition:
            self._analyze_node(node.condition)
        if node.update:
            self._analyze_node(node.update)
        if node.body:
            self._analyze_node(node.body)
        
        self.symbol_table.exit_scope()
        self.in_loop = old_in_loop
    
    def _analyze_break_stmt(self, node: BreakStmtNode) -> None:
        """分析跳出语句（break 在循环和 switch 中均合法）"""
        if not self.in_loop and not self.in_switch:
            self._add_error(
                "非法跳出",
                "跳出语句不在循环或选择语句中",
                self._node_location(node)
            )
    
    def _analyze_continue_stmt(self, node: ContinueStmtNode) -> None:
        """分析继续语句"""
        if not self.in_loop:
            self._add_error(
                "非法继续",
                "继续语句不在循环中",
                self._node_location(node)
            )
    
    def _analyze_return_stmt(self, node: ReturnStmtNode) -> None:
        """分析返回语句"""
        if not self.current_function:
            self._add_error(
                "非法返回",
                "返回语句不在函数中",
                self._node_location(node)
            )
            if node.value:
                self._analyze_node(node.value)
            return
        
        # Phase 5 T2.2: 检查返回值类型
        if node.value and self.current_function.return_type:
            return_type_info = self.type_checker.get_type(self.current_function.return_type)
            value_type_info = self._infer_expr_type(node.value)
            if return_type_info and value_type_info:
                self._check_type_compat(
                    return_type_info, value_type_info, node,
                    "返回值"
                )
        
        if node.value:
            self._analyze_node(node.value)
    
    def _analyze_expr_stmt(self, node: ExprStmtNode) -> None:
        """分析表达式语句"""
        self._analyze_node(node.expr)
    
    def _analyze_identifier_expr(self, node: IdentifierExprNode) -> None:
        """分析标识符表达式"""
        symbol = self.symbol_table.lookup(node.name)
        
        if not symbol:
            self._add_error(
                "未定义符号",
                f"标识符 '{node.name}' 未定义",
                self._node_location(node),
                suggestions=[
                    f"检查 '{node.name}' 的拼写",
                    "确认该变量/函数是否已在此作用域中声明"
                ]
            )
            return
        
        symbol.is_used = True
        symbol.references.append(self._node_location(node))
        
        # Phase 5 T2.3: 将推导类型标注到 AST 节点
        if symbol.data_type:
            type_info = self.type_checker.get_type(symbol.data_type)
            if type_info:
                node.inferred_type = type_info.name
        
        # Phase 7: 将符号注册到符号查找优化器（热点缓存 + 查找统计）
        # 优化器通过 _get_symbol_lookup_optimizer() 延迟初始化
        optimizer = self._get_symbol_lookup_optimizer()
        if optimizer is not None:
            scope_name = self.symbol_table.current_scope.scope_name
            optimizer.register_symbol(node.name, scope_name, symbol)
        
    def _analyze_member_expr(self, node: MemberExprNode) -> None:
        """分析成员访问表达式（Phase 6 M4）

        检查：
        1. 对象是否为结构体/共用体类型
        2. 成员名是否存在于该结构体
        3. 推导成员访问表达式的类型
        """
        loc = self._node_location(node)

        # 先递归分析子节点（对象表达式）
        if node.obj:
            self._analyze_node(node.obj)

        # 获取对象的类型名
        obj_type_name = None
        if hasattr(node.obj, 'name') and node.obj.name:
            obj_symbol = self.symbol_table.lookup(node.obj.name)
            if obj_symbol:
                obj_type_name = obj_symbol.data_type
        elif hasattr(node.obj, 'inferred_type') and node.obj.inferred_type:
            obj_type_name = node.obj.inferred_type

        member_name = node.member if hasattr(node, 'member') else None
        if not member_name:
            return

        # 检查对象是否为结构体/共用体类型
        struct_symbol = None
        if obj_type_name:
            struct_symbol = self.symbol_table.lookup(obj_type_name)

        if struct_symbol and struct_symbol.symbol_type in ("结构体", "共用体"):
            # 检查成员存在性
            member_found = None
            for m in struct_symbol.members:
                if m.name == member_name:
                    member_found = m
                    break

            if not member_found:
                # 生成相似成员建议
                available = [m.name for m in struct_symbol.members if m.name]
                suggestions = []
                if available:
                    # 简单的相似度匹配（前两个字符相同或包含关系）
                    for a in available:
                        if a.startswith(member_name[:2]) or member_name[:2] in a:
                            suggestions.append(f"是否是指 '{a}'?")
                            break
                    if not suggestions and len(available) <= 5:
                        suggestions.append(f"可用成员: {', '.join(available)}")
                    elif not suggestions:
                        suggestions.append(f"结构体 '{obj_type_name}' 有 {len(available)} 个成员")

                self._add_error(
                    "成员不存在",
                    f"结构体 '{obj_type_name}' 没有成员 '{member_name}'",
                    loc,
                    suggestions=suggestions
                )
                return

            # 标注推导类型
            if member_found.data_type:
                node.inferred_type = member_found.data_type
                return

        # 对象类型未知或非结构体类型——不报错（可能是 typedef 别名或尚未分析到的类型）
        # 尝试推导类型
        result_type = self._infer_expr_type(node)
        if result_type:
            node.inferred_type = result_type.name

    def _analyze_assign_expr(self, node: AssignExprNode) -> None:
        """分析赋值表达式（Phase 5 T2.4）"""
        # 获取目标变量的类型
        target_type = None
        if hasattr(node, 'target') and node.target:
            target_type = self._infer_expr_type(node.target)
        
        # 获取值表达式类型
        value_type = None
        if hasattr(node, 'value') and node.value:
            value_type = self._infer_expr_type(node.value)
        
        # 类型检查
        if target_type and value_type:
            target_name = ""
            if hasattr(node, 'target') and hasattr(node.target, 'name'):
                target_name = node.target.name
            self._check_type_compat(
                target_type, value_type, node,
                f"赋值给 '{target_name}'" if target_name else "赋值"
            )
        
        # 标注推导类型
        if value_type:
            node.inferred_type = value_type.name
        
        # 递归分析子节点
        for child in node.get_children():
            self._analyze_node(child)
    
    # ===== Phase 6 T2: 函数调用参数检查 =====
    
    # T2.3: 标准库可变参数函数白名单
    VARIADIC_FUNCTIONS = frozenset({
        "zhc_printf", "zhc_scanf", "zhc_fprintf", "zhc_sprintf",
        "printf", "scanf", "fprintf", "sprintf",
    })
    
    def _analyze_call_expr(self, node) -> None:
        """分析函数调用表达式（Phase 6 T2.1-T2.3）
        
        功能：
        1. 参数数量检查
        2. 参数类型匹配检查
        3. 函数重载解析（T2.2）
        4. 标准库可变参数函数豁免（T2.3）
        """
        # 获取函数名
        func_name = None
        if hasattr(node, 'callee') and hasattr(node.callee, 'name'):
            func_name = node.callee.name
        
        # 获取实际参数列表
        actual_args = list(node.args) if hasattr(node, 'args') else []
        
        # 递归分析所有子节点（参数表达式）
        for child in node.get_children():
            self._analyze_node(child)
        
        if not func_name:
            return
        
        # 标记被调用函数为"已使用"
        candidates = self.symbol_table.lookup_all(func_name)
        
        # 标记所有候选为已使用
        for c in candidates:
            c.is_used = True
        
        # 未找到声明的函数：默认不报错（外部函数）
        if not candidates:
            result_type = self._infer_expr_type(node)
            if result_type:
                node.inferred_type = result_type.name
            return
        
        # 过滤出函数类型的候选
        func_candidates = [c for c in candidates if c.symbol_type == "函数"]
        if not func_candidates:
            return
        
        # T2.3: 标准库可变参数函数 — 仅检查第一个参数
        if func_name in self.VARIADIC_FUNCTIONS:
            if len(actual_args) == 0:
                self._add_error(
                    "参数不足",
                    f"函数 '{func_name}' 至少需要 1 个参数，但提供了 0 个",
                    self._node_location(node)
                )
            # 标注返回类型
            if func_candidates[0].return_type:
                type_info = self.type_checker.get_type(func_candidates[0].return_type)
                if type_info:
                    node.inferred_type = type_info.name
            return
        
        # T2.2: 重载解析 — 如果有多个同名函数
        if len(func_candidates) > 1:
            self._resolve_overload(node, func_name, func_candidates, actual_args)
            return
        
        # 单一函数：标准参数检查
        callee_symbol = func_candidates[0]
        declared_params = callee_symbol.parameters
        return_type = callee_symbol.return_type
        
        # 标注调用表达式的返回类型
        if return_type:
            type_info = self.type_checker.get_type(return_type)
            if type_info:
                node.inferred_type = type_info.name
        
        # T2.1: 参数数量检查
        expected_count = len(declared_params)
        actual_count = len(actual_args)
        
        if actual_count != expected_count:
            if actual_count < expected_count:
                self._add_error(
                    "参数不足",
                    f"函数 '{func_name}' 期望 {expected_count} 个参数，但提供了 {actual_count} 个",
                    self._node_location(node),
                    suggestions=[
                        f"补充缺少的参数",
                        f"检查函数 '{func_name}' 的声明"
                    ]
                )
            else:
                self._add_error(
                    "参数过多",
                    f"函数 '{func_name}' 期望 {expected_count} 个参数，但提供了 {actual_count} 个",
                    self._node_location(node),
                    suggestions=[
                        f"移除多余的参数",
                        f"检查函数 '{func_name}' 的声明"
                    ]
                )
            return
        
        # T2.1: 参数类型检查（逐参数）
        for i, (declared_param, actual_arg) in enumerate(zip(declared_params, actual_args)):
            declared_type_info = self.type_checker.get_type(declared_param.data_type)
            actual_type_info = self._infer_expr_type(actual_arg)
            
            if declared_type_info and actual_type_info:
                self._check_type_compat(
                    declared_type_info, actual_type_info, actual_arg,
                    f"参数 {i+1} ('{declared_param.name}')"
                )
    
    def _resolve_overload(self, node, func_name: str, candidates: List[Symbol],
                          actual_args: list) -> None:
        """解析函数重载（Phase 6 T2.2）
        
        按参数匹配度打分：
        - 完全匹配 = 0 分
        - 隐式转换 = 1 分
        - 不匹配 = 跳过
        
        选总分最低的唯一候选。歧义则报错。
        """
        actual_count = len(actual_args)
        
        best_candidate = None
        best_score = None
        ambiguous = False
        
        for candidate in candidates:
            declared_params = candidate.parameters
            
            # 参数数量必须匹配
            if len(declared_params) != actual_count:
                continue
            
            # 计算匹配分数
            score = 0
            match_ok = True
            for i, (declared, actual_arg) in enumerate(zip(declared_params, actual_args)):
                declared_type = self.type_checker.get_type(declared.data_type)
                actual_type = self._infer_expr_type(actual_arg)
                
                if declared_type is None or actual_type is None:
                    match_ok = False
                    break
                
                # 完全匹配
                if declared_type.equals(actual_type):
                    score += 0
                # 可隐式转换
                elif actual_type.can_cast_to(declared_type):
                    score += 1
                else:
                    match_ok = False
                    break
            
            if not match_ok:
                continue
            
            if best_score is None or score < best_score:
                best_candidate = candidate
                best_score = score
                ambiguous = False
            elif score == best_score:
                ambiguous = True
        
        if ambiguous:
            self._add_error(
                "重载歧义",
                f"函数 '{func_name}' 的调用存在多个匹配的重载版本",
                self._node_location(node),
                suggestions=["明确指定参数类型以消除歧义"]
            )
            return
        
        if best_candidate is None:
            self._add_error(
                "无匹配函数",
                f"函数 '{func_name}' 没有匹配 {actual_count} 个参数的重载版本",
                self._node_location(node),
                suggestions=["检查参数数量和类型"]
            )
            return
        
        # 标注返回类型
        if best_candidate.return_type:
            type_info = self.type_checker.get_type(best_candidate.return_type)
            if type_info:
                node.inferred_type = type_info.name
        
        # 逐参数类型检查（即使是最佳匹配，隐式转换也可能产生警告）
        for i, (declared_param, actual_arg) in enumerate(zip(best_candidate.parameters, actual_args)):
            declared_type_info = self.type_checker.get_type(declared_param.data_type)
            actual_type_info = self._infer_expr_type(actual_arg)
            
            if declared_type_info and actual_type_info:
                self._check_type_compat(
                    declared_type_info, actual_type_info, actual_arg,
                    f"参数 {i+1} ('{declared_param.name}')"
                )
    
    # ===== Phase 5 T1.2 新增的节点类型处理 =====
    
    def _analyze_do_while_stmt(self, node: DoWhileStmtNode) -> None:
        """分析执行-当循环"""
        old_in_loop = self.in_loop
        self.in_loop = True
        if node.body:
            self._analyze_node(node.body)
        if node.condition:
            self._analyze_node(node.condition)
        self.in_loop = old_in_loop
    
    def _analyze_switch_stmt(self, node: SwitchStmtNode) -> None:
        """分析选择语句（Phase 6 M4: 增强）

        新增检查：
        1. case 值重复检测
        2. 缺少 default 分支警告
        """
        old_in_switch = self.in_switch
        self.in_switch = True
        if node.expr:
            self._analyze_node(node.expr)

        has_default = False
        case_values: Dict[str, int] = {}  # value_str -> 第一次出现的行号

        if node.cases:
            for case in node.cases:
                # 检查是否为 default 分支
                if case.node_type == ASTNodeType.DEFAULT_STMT:
                    has_default = True
                elif case.node_type == ASTNodeType.CASE_STMT:
                    # 检查 case 值重复
                    if hasattr(case, 'value') and case.value is not None:
                        val_str = self._get_case_value_str(case.value)
                        if val_str:
                            if val_str in case_values:
                                self._add_error(
                                    "重复 case",
                                    f"switch 中的 case 值 '{val_str}' 重复 (首次出现在第 {case_values[val_str]} 行)",
                                    self._node_location(case)
                                )
                            else:
                                case_values[val_str] = case.value.line if hasattr(case.value, 'line') else case.line

                self._analyze_node(case)

        # 警告：缺少 default 分支
        if not has_default:
            self._add_warning(
                "缺少 default",
                "switch 语句缺少 default 分支",
                self._node_location(node),
                suggestions=["添加 default 分支以处理未匹配的情况"]
            )

        self.in_switch = old_in_switch

    def _get_case_value_str(self, value_node: ASTNode) -> Optional[str]:
        """获取 case 值的字符串表示（用于重复检测）"""
        if value_node is None:
            return None
        nt = value_node.node_type
        if nt == ASTNodeType.INT_LITERAL:
            return str(getattr(value_node, 'value', ''))
        elif nt == ASTNodeType.CHAR_LITERAL:
            return str(getattr(value_node, 'value', ''))
        elif nt == ASTNodeType.STRING_LITERAL:
            return str(getattr(value_node, 'value', ''))
        elif nt == ASTNodeType.IDENTIFIER_EXPR:
            return str(getattr(value_node, 'name', ''))
        elif nt == ASTNodeType.UNARY_EXPR:
            # 处理负数字面量：-1 等
            if hasattr(value_node, 'operand') and value_node.operand:
                inner = self._get_case_value_str(value_node.operand)
                if inner is not None:
                    op = getattr(value_node, 'operator', '') or getattr(value_node, 'op', '')
                    return f"{op}{inner}"
            return None
        return None
    
    def _analyze_goto_stmt(self, node: GotoStmtNode) -> None:
        """分析goto语句（Phase 6 M4: 标签存在性检查）

        收集 goto 目标标签，在函数分析结束后统一验证标签是否存在。
        """
        if hasattr(node, 'label') and node.label:
            self._goto_targets.append((node.label, node.line, node.column))
    
    def _analyze_label_stmt(self, node: LabelStmtNode) -> None:
        """分析标签声明"""
        if hasattr(node, 'name') and node.name:
            self._defined_labels.add(node.name)
            label_symbol = Symbol(
                name=node.name,
                symbol_type="标签",
                definition_location=self._node_location(node),
                is_defined=True
            )
            if not self.symbol_table.add_symbol(label_symbol):
                self._add_error(
                    "重复定义",
                    f"标签 '{node.name}' 重复定义",
                    self._node_location(node)
                )

    def _validate_goto_targets(self) -> None:
        """验证所有 goto 的目标标签是否存在（Phase 6 M4）

        在每个函数体分析结束后调用。报告未定义的标签错误，
        然后重置标签集合和 goto 目标列表。
        """
        for label_name, line, column in self._goto_targets:
            if label_name not in self._defined_labels:
                self._add_error(
                    "未定义标签",
                    f"goto 目标标签 '{label_name}' 未定义",
                    f"{line}:{column}",
                    suggestions=[
                        f"在当前函数内添加标签 '{label_name}:'",
                        "检查标签名的拼写是否正确"
                    ]
                )
        # 重置（每个函数独立作用域）
        self._defined_labels.clear()
        self._goto_targets.clear()

    def _analyze_enum_decl(self, node: EnumDeclNode) -> None:
        """分析枚举声明"""
        if node.name:  # 具名枚举
            enum_symbol = Symbol(
                name=node.name,
                symbol_type="枚举",
                definition_location=self._node_location(node),
                is_defined=True
            )
            if not self.symbol_table.add_symbol(enum_symbol):
                self._add_error(
                    "重复定义",
                    f"枚举 '{node.name}' 重复定义",
                    self._node_location(node)
                )
                return
            self.stats['symbols_added'] += 1
        
        # 注册枚举值到当前作用域
        if hasattr(node, 'values') and node.values:
            for value_name, value_expr in node.values:
                value_symbol = Symbol(
                    name=value_name,
                    symbol_type="枚举值",
                    definition_location=self._node_location(node)
                )
                self.symbol_table.add_symbol(value_symbol)
                if value_expr:
                    self._analyze_node(value_expr)
    
    def _analyze_union_decl(self, node: UnionDeclNode) -> None:
        """分析共用体声明"""
        union_symbol = Symbol(
            name=node.name,
            symbol_type="共用体",
            definition_location=self._node_location(node),
            is_defined=True
        )
        if not self.symbol_table.add_symbol(union_symbol):
            self._add_error(
                "重复定义",
                f"共用体 '{node.name}' 重复定义",
                self._node_location(node)
            )
            return
        self.stats['symbols_added'] += 1
        
        self.symbol_table.enter_scope(ScopeType.STRUCT, node.name)
        for member in node.members:
            self._analyze_node(member)
        self.symbol_table.exit_scope()
    
    def _analyze_typedef_decl(self, node: TypedefDeclNode) -> None:
        """分析类型别名声明"""
        if hasattr(node, 'new_name') and node.new_name:
            td_symbol = Symbol(
                name=node.new_name,
                symbol_type="类型别名",
                definition_location=self._node_location(node),
                is_defined=True
            )
            if not self.symbol_table.add_symbol(td_symbol):
                self._add_error(
                    "重复定义",
                    f"类型别名 '{node.new_name}' 重复定义",
                    self._node_location(node)
                )
            else:
                self.stats['symbols_added'] += 1
            # 分析旧类型节点
            if hasattr(node, 'old_type') and node.old_type:
                self._analyze_node(node.old_type)
    
    # ===== Phase 5 T2.2-T2.4: 类型检查集成 =====
    
    # ===== Phase 8: 泛型模块集成 =====
    
    def _register_generic_function(self, node: FunctionDeclNode) -> None:
        """
        检查并注册泛型函数（Phase 8）
        
        如果节点包含 type_params 属性（泛型函数），则注册到 GenericManager。
        """
        if not hasattr(node, 'type_params') or not node.type_params:
            return
        
        try:
            from .generics import GenericFunction, TypeParameter
            
            type_params = []
            for tp in node.type_params:
                if hasattr(tp, 'name'):
                    type_params.append(TypeParameter(name=tp.name))
            
            generic_func = GenericFunction(
                name=node.name,
                type_params=type_params,
                return_type=self._get_type_name(node.return_type),
                params=[]  # 泛型函数参数类型待确定
            )
            self.generic_manager.register_generic_function(generic_func)
        except Exception as e:
            # 泛型注册失败不影响主流程
            pass
    
    def _register_generic_type(self, node: StructDeclNode) -> None:
        """
        检查并注册泛型类型（Phase 8）
        
        如果节点包含 type_params 属性（泛型类型），则注册到 GenericManager。
        """
        if not hasattr(node, 'type_params') or not node.type_params:
            return
        
        try:
            from .generics import GenericType, TypeParameter
            
            type_params = []
            for tp in node.type_params:
                if hasattr(tp, 'name'):
                    type_params.append(TypeParameter(name=tp.name))
            
            # 收集成员类型
            member_types = []
            for member in node.members:
                if hasattr(member, 'var_type'):
                    member_types.append(self._get_type_name(member.var_type))
            
            generic_type = GenericType(
                name=node.name,
                type_params=type_params,
                members=member_types
            )
            self.generic_manager.register_generic_type(generic_type)
        except Exception as e:
            # 泛型注册失败不影响主流程
            pass
    
    def _infer_expr_type(self, node: ASTNode):
        """推导表达式的类型（返回 TypeInfo 或 None）"""
        if node is None:
            return None
        
        nt = node.node_type
        
        # 字面量类型
        if nt == ASTNodeType.INT_LITERAL:
            return self.type_checker.get_type("整数型")
        elif nt == ASTNodeType.FLOAT_LITERAL:
            return self.type_checker.get_type("双精度型")
        elif nt == ASTNodeType.CHAR_LITERAL:
            return self.type_checker.get_type("字符型")
        elif nt == ASTNodeType.STRING_LITERAL:
            return self.type_checker.get_type("字符串型")
        elif nt == ASTNodeType.BOOL_LITERAL:
            return self.type_checker.get_type("逻辑型")
        elif nt == ASTNodeType.NULL_LITERAL:
            return self.type_checker.get_type("空型")
        
        # 标识符：查符号表
        elif nt == ASTNodeType.IDENTIFIER_EXPR:
            symbol = self.symbol_table.lookup(node.name) if hasattr(node, 'name') else None
            if symbol and symbol.data_type:
                return self.type_checker.get_type(symbol.data_type)
            return None
        
        # 二元表达式
        elif nt == ASTNodeType.BINARY_EXPR:
            left_type = self._infer_expr_type(node.left) if hasattr(node, 'left') else None
            right_type = self._infer_expr_type(node.right) if hasattr(node, 'right') else None
            op = node.operator if hasattr(node, 'operator') else (node.op if hasattr(node, 'op') else None)
            if left_type and right_type and op:
                self.type_checker.clear()
                result = self.type_checker.check_binary_op(
                    node.line, op, left_type, right_type
                )
                # Phase 6: 传播 TypeChecker 的运算类型错误
                for err_line, err_type, err_msg in self.type_checker.get_errors():
                    self._add_error(err_type, err_msg, self._node_location(node))
                self.type_checker.clear()
                return result
            return None
        
        # 一元表达式
        elif nt == ASTNodeType.UNARY_EXPR:
            operand_type = self._infer_expr_type(node.operand) if hasattr(node, 'operand') else None
            op = node.operator if hasattr(node, 'operator') else (node.op if hasattr(node, 'op') else None)
            if operand_type and op:
                self.type_checker.clear()
                result = self.type_checker.check_unary_op(
                    node.line, op, operand_type
                )
                for err_line, err_type, err_msg in self.type_checker.get_errors():
                    self._add_error(err_type, err_msg, self._node_location(node))
                self.type_checker.clear()
                return result
            return None
        
        # 函数调用
        elif nt == ASTNodeType.CALL_EXPR:
            # Phase 6: 从 callee 获取函数名（CallExprNode 没有 name 属性）
            func_name = None
            if hasattr(node, 'callee') and hasattr(node.callee, 'name'):
                func_name = node.callee.name
            if func_name:
                symbol = self.symbol_table.lookup(func_name)
                if symbol and symbol.return_type:
                    return self.type_checker.get_type(symbol.return_type)
            return None
        
        # 赋值表达式：返回右侧类型
        elif nt == ASTNodeType.ASSIGN_EXPR:
            if hasattr(node, 'value'):
                return self._infer_expr_type(node.value)
            return None
        
        # 成员访问：查找结构体符号，返回成员类型
        elif nt == ASTNodeType.MEMBER_EXPR:
            if hasattr(node, 'obj') and hasattr(node, 'member'):
                obj_type_name = None
                if hasattr(node.obj, 'name') and node.obj.name:
                    obj_symbol = self.symbol_table.lookup(node.obj.name)
                    if obj_symbol:
                        obj_type_name = obj_symbol.data_type
                elif hasattr(node.obj, 'inferred_type') and node.obj.inferred_type:
                    obj_type_name = node.obj.inferred_type

                if obj_type_name:
                    struct_symbol = self.symbol_table.lookup(obj_type_name)
                    if struct_symbol and struct_symbol.symbol_type in ("结构体", "共用体"):
                        for m in struct_symbol.members:
                            if m.name == node.member and m.data_type:
                                return self.type_checker.get_type(m.data_type)
            return None

        # 数组访问
        elif nt == ASTNodeType.ARRAY_EXPR:
            if hasattr(node, 'object'):
                obj_type = self._infer_expr_type(node.object)
                if obj_type and obj_type.is_array() and obj_type.base_type:
                    return obj_type.base_type
            return None
        
        # 三元表达式：返回 then/else 的公共类型
        elif nt == ASTNodeType.TERNARY_EXPR:
            then_type = self._infer_expr_type(node.then_expr) if hasattr(node, 'then_expr') else None
            else_type = self._infer_expr_type(node.else_expr) if hasattr(node, 'else_expr') else None
            return then_type or else_type
        
        # 类型转换表达式：返回目标类型
        elif nt == ASTNodeType.CAST_EXPR:
            if hasattr(node, 'target_type'):
                from .type_utils import ast_type_to_typeinfo
                return ast_type_to_typeinfo(node.target_type)
            return None
        
        # Phase 8: 后备 — 使用 Hindley-Milner 类型推导引擎
        return self._infer_with_engine(node)
    
    def _infer_with_engine(self, node: ASTNode):
        """
        使用 Hindley-Milner 引擎推导类型（Phase 8 后备机制）
        
        当 _infer_expr_type 的简单推导失败时，尝试使用约束求解引擎。
        """
        from ..typeinfer.engine import TypeEnv, BaseType, TypeVariable, FunctionType
        
        # 构建类型环境
        env = TypeEnv()
        for name, symbol in self.symbol_table.all_symbols.items():
            if symbol.data_type:
                type_ = self._symbol_to_infer_type(symbol.data_type)
                if type_:
                    env.bindings[name] = type_
        
        try:
            inferred = self.type_inference_engine.infer(node, env)
            
            # 求解约束
            if self.type_inference_engine.solve_constraints():
                return self._infer_type_to_typeinfo(inferred)
        except Exception:
            pass  # 类型推导失败，静默返回 None
        
        return None
    
    def _symbol_to_infer_type(self, data_type: str):
        """将符号表类型转换为 TypeInferenceEngine 的类型"""
        from ..typeinfer.engine import BaseType
        mapping = {
            "整数型": BaseType.INT,
            "浮点型": BaseType.FLOAT,
            "双精度型": BaseType.FLOAT,
            "字符型": BaseType.CHAR,
            "字符串型": BaseType.STRING,
            "逻辑型": BaseType.BOOL,
            "空型": BaseType.VOID,
            "布尔型": BaseType.BOOL,
        }
        return mapping.get(data_type)
    
    def _infer_type_to_typeinfo(self, type_):
        """将 TypeInferenceEngine 类型转换为 TypeInfo"""
        from ..typeinfer.engine import BaseType, TypeVariable, FunctionType, ArrayType
        
        if isinstance(type_, BaseType):
            return self.type_checker.get_type(str(type_))
        elif isinstance(type_, TypeVariable):
            if type_.instance:
                return self._infer_type_to_typeinfo(type_.instance)
            return None
        elif isinstance(type_, FunctionType):
            # 函数类型：返回返回类型
            return self._infer_type_to_typeinfo(type_.return_type)
        elif isinstance(type_, ArrayType):
            # 数组类型：返回元素类型
            return self._infer_type_to_typeinfo(type_.element_type)
        elif hasattr(type_, '__str__'):
            return self.type_checker.get_type(str(type_))
        return None
    
    def _check_type_compat(self, target_type_info, value_type_info, node: ASTNode,
                           context: str) -> None:
        """检查类型兼容性，有错误则记录到 self.errors"""
        if target_type_info is None or value_type_info is None:
            return
        
        self.type_checker.clear()
        ok = self.type_checker.check_assignment(
            node.line, target_type_info, value_type_info, context
        )
        
        if not ok:
            for err_line, err_type, err_msg in self.type_checker.get_errors():
                suggestions = self._get_type_suggestions(
                    str(target_type_info), str(value_type_info)
                )
                self._add_error(
                    "类型不匹配",
                    err_msg,
                    self._node_location(node),
                    suggestions=suggestions
                )
        else:
            # 检查是否有警告（如精度丢失）
            for warn_line, warn_type, warn_msg in self.type_checker.get_warnings():
                self._add_warning(
                    "类型警告",
                    warn_msg,
                    self._node_location(node)
                )
        
        self.type_checker.clear()
    
    def _get_type_name(self, type_node) -> Optional[str]:
        """从 AST 类型节点获取中文类型名"""
        if type_node is None:
            return None
        if hasattr(type_node, 'name'):
            return type_node.name
        return str(type_node)
    
    def _get_type_suggestions(self, target_type: str, value_type: str) -> List[str]:
        """根据类型不匹配情况生成修复建议"""
        suggestions = []
        if value_type == "空型":
            suggestions.append("空型不能赋值给非指针变量")
        elif "指针" in value_type and "指针" not in target_type:
            suggestions.append("不能将指针赋值给非指针变量")
        elif "指针" not in value_type and "指针" in target_type:
            suggestions.append("需要使用取地址运算符 & 获取指针")
        else:
            suggestions.append(f"确保表达式类型与目标类型 '{target_type}' 兼容")
        suggestions.append(f"目标类型: {target_type}, 表达式类型: {value_type}")
        return suggestions
    
    def _add_error(self, error_type: str, message: str, location: str,
                    suggestions: List[str] = None) -> None:
        """添加错误"""
        error = SemanticErrorInfo(
            error_type=error_type,
            message=message,
            location=location,
            severity="错误",
            suggestions=suggestions or [],
            source_file=self.source_file
        )
        self.errors.append(error)
        self.stats['errors_found'] += 1
    
    def _add_warning(self, error_type: str, message: str, location: str,
                     suggestions: List[str] = None) -> None:
        """添加警告"""
        warning = SemanticErrorInfo(
            error_type=error_type,
            message=message,
            location=location,
            severity="警告",
            suggestions=suggestions or [],
            source_file=self.source_file
        )
        self.warnings.append(warning)
        self.stats['warnings_found'] += 1
    
    def _check_unused_symbols(self) -> None:
        """检查未使用的符号"""
        unused = self.symbol_table.get_unused_symbols()
        
        for symbol in unused:
            if symbol.symbol_type in ["参数", "成员变量"]:
                continue
            
            self._add_warning(
                "未使用符号",
                f"{symbol.symbol_type} '{symbol.name}' 已定义但未使用",
                symbol.definition_location or ""
            )
    
    # ===== Phase 6 M3: 控制流分析集成 =====

    def _run_cfg_analysis(self, ast: ASTNode) -> None:
        """运行控制流分析（不可达代码 + 未初始化变量 + 圈复杂度 + 无限循环）

        使用 analyzer/control_flow.py 的 ControlFlowAnalyzer，
        通过 cfg_analyzer.py 适配层。
        集成全部公开方法：build_cfg、detect_unreachable_code、
        compute_cyclomatic_complexity、detect_infinite_loops。
        所有发现以警告形式报告，不阻止编译。
        """
        if not self.cfg_enabled and not self.uninit_enabled:
            return

        # 不可达代码 + 圈复杂度 + 无限循环检测
        if self.cfg_enabled:
            try:
                from .cfg_analyzer import CFGAnalyzer, find_functions, ast_to_statements
                cfg_analyzer = CFGAnalyzer()
                cfa = cfg_analyzer._get_analyzer()

                for func_decl in find_functions(ast):
                    if not func_decl.body:
                        continue

                    stmt_dicts = ast_to_statements(func_decl.body)

                    try:
                        # Phase 7: 使用缓存方法避免重复构建 CFG
                        cfg = cfa.build_cfg_cached(func_decl.name, stmt_dicts)

                        # 1. 不可达代码检测（缓存）
                        unreachable = cfa.detect_unreachable_code_cached(cfg)
                        for issue in unreachable:
                            loc = f"{issue.line_number}:0"
                            self._add_warning(
                                "不可达代码",
                                f"函数 '{func_decl.name}' 中: {issue.message}",
                                loc,
                                suggestions=[issue.suggestion]
                            )

                        # 2. 圈复杂度检测
                        complexity = cfa.compute_cyclomatic_complexity_cached(cfg)
                        if complexity > 10:
                            self._add_warning(
                                "圈复杂度",
                                f"函数 '{func_decl.name}' 的圈复杂度为 {complexity}（建议 ≤10）",
                                "0:0",
                                suggestions=["考虑拆分函数以降低复杂度", "提取复杂条件为独立函数"]
                            )
                        elif complexity > 5:
                            self._add_warning(
                                "圈复杂度",
                                f"函数 '{func_decl.name}' 的圈复杂度为 {complexity}（偏高）",
                                "0:0"
                            )

                        # 3. 无限循环检测
                        infinite_loops = cfa.detect_infinite_loops_cached(cfg)
                        for issue in infinite_loops:
                            loc = f"{issue.line_number}:0"
                            self._add_warning(
                                "无限循环",
                                f"函数 '{func_decl.name}' 中: {issue.message}",
                                loc,
                                suggestions=[issue.suggestion]
                            )

                        # 4. 支配树计算（为后续优化分析提供基础数据）
                        cfa.compute_dominance_tree_cached(cfg)

                    except Exception:
                        pass  # 单函数 CFG 分析失败不阻断

            except Exception:
                pass  # CFG 分析失败不阻断编译

        # 未初始化变量检测
        if self.uninit_enabled:
            try:
                from .cfg_analyzer import UninitAnalyzer
                uninit_analyzer = UninitAnalyzer()
                uninit_uses = uninit_analyzer.analyze(ast, self.symbol_table)
                for use in uninit_uses:
                    loc = f"{use['line']}:{use['column']}"
                    self._add_warning(
                        "未初始化变量",
                        f"变量 '{use['name']}' 可能未初始化（函数 '{use['func_name']}'）",
                        loc,
                        suggestions=[
                            f"在使用前初始化变量 '{use['name']}'",
                            f"检查变量声明时是否缺少初始化值"
                        ]
                    )
            except Exception:
                pass  # 未初始化分析失败不阻断编译

        # Phase 6 M4: 内存安全警告（空指针/越界）— 仅警告级
        self._run_memory_safety_checks(ast)

        # Phase 6 M5: 扩展分析器集成
        self._run_data_flow_analysis(ast)
        self._run_interprocedural_analysis(ast)
        self._run_alias_analysis(ast)
        self._run_pointer_analysis(ast)

    def _run_memory_safety_checks(self, ast: ASTNode) -> None:
        """运行内存安全检查（覆盖全部 8 个子检查器）

        通过 MemorySafetyAnalyzer 聚合器调用全部 8 个子检查器：
        1. NullPointerChecker - 空指针访问验证
        2. BoundsChecker - 越界检查
        3. MemoryLeakDetector - 内存泄漏
        4. UseAfterFreeChecker - 释放后使用
        5. OwnershipTracker - 所有权/借用冲突
        6. LifetimeAnalyzer - 生命周期
        7. RaceConditionDetector - 竞态条件
        8. StackAllocationAnalyzer - 栈溢出

        所有发现以警告形式报告，不阻止编译。
        """
        try:
            from .cfg_analyzer import find_functions, ast_to_statements
            from ..analyzer.memory_safety import MemorySafetyAnalyzer

            analyzer = MemorySafetyAnalyzer()

            for func_decl in find_functions(ast):
                if not func_decl.body:
                    continue

                stmt_dicts = ast_to_statements(func_decl.body)

                try:
                    result = analyzer.analyze_function(func_decl.name, stmt_dicts)
                    for issue in result.get('issues', []):
                        loc = f"{issue.get('line', 0)}:0"
                        issue_type = issue.get('type', '内存安全')
                        message = issue.get('message', '')
                        # 区分错误级别
                        if issue_type in ('不安全', 'unsafe', 'double_free', 'borrow_conflict'):
                            self._add_error(
                                "内存安全",
                                message, loc,
                                suggestions=["修复内存安全问题"]
                            )
                        else:
                            self._add_warning(
                                "内存安全",
                                message, loc
                            )
                except Exception:
                    pass  # 单函数分析失败不阻断

            # 栈溢出检查
            stack_issue = analyzer.stack_analyzer.check_stack_overflow()
            if stack_issue:
                self._add_warning(
                    "栈溢出",
                    stack_issue.message,
                    f"{stack_issue.line_number}:0",
                    suggestions=[stack_issue.suggestion]
                )

            # 竞态条件检查
            race_issues = analyzer.race_detector.detect_races()
            for issue in race_issues:
                self._add_warning(
                    "竞态条件",
                    issue.message,
                    f"{issue.line_number}:0",
                    suggestions=[issue.suggestion]
                )

        except Exception:
            pass  # 内存安全分析失败不阻断编译

    # ===== Phase 6 M5: 扩展分析器集成 =====

    def _run_data_flow_analysis(self, ast: ASTNode) -> None:
        """运行数据流分析（未初始化变量 + 未使用变量 + 污点分析 + 常量传播）

        使用 analyzer/data_flow.py 的 DataFlowAnalyzer，
        通过适配层将 AST 转为字典格式传入。
        集成全部公开方法：build_def_use_chains、analyze_live_variables、
        propagate_constants、analyze_taint_flow、detect_uninitialized_vars。
        所有发现以警告形式报告，不阻止编译。
        """
        if not self.dataflow_enabled:
            return

        try:
            from .cfg_analyzer import find_functions, ast_to_statements
            from ..analyzer.data_flow import DataFlowAnalyzer

            analyzer = DataFlowAnalyzer()

            for func_decl in find_functions(ast):
                if not func_decl.body:
                    continue

                stmt_dicts = ast_to_statements(func_decl.body)
                params = [p.name for p in func_decl.params if hasattr(p, 'name')]

                try:
                    result = analyzer.analyze_function(func_decl.name, stmt_dicts, params)

                    # 1. 未初始化变量
                    for issue in result.get('uninitialized_issues', []):
                        loc = f"{issue.line_number}:0"
                        self._add_warning(
                            "未初始化变量",
                            issue.message,
                            loc,
                            suggestions=[issue.suggestion]
                        )

                    # 2. 未使用变量
                    for var_name in result.get('unused_vars', []):
                        self._add_warning(
                            "未使用变量",
                            f"函数 '{func_decl.name}' 中变量 '{var_name}' 已定义但未使用",
                            "0:0",
                            suggestions=[f"删除未使用的变量 '{var_name}' 或使用它"]
                        )

                    # 3. 污点分析问题
                    for issue in result.get('taint_issues', []):
                        loc = f"{issue.line_number}:0"
                        if issue.severity == "error":
                            self._add_error(
                                "污点数据",
                                issue.message,
                                loc,
                                suggestions=[issue.suggestion]
                            )
                        else:
                            self._add_warning(
                                "污点数据",
                                issue.message,
                                loc,
                                suggestions=[issue.suggestion]
                            )

                    # 4. 常量传播信息（信息级，仅在找到常量时报告）
                    constants = result.get('constants', {})
                    for var_name, value in constants.items():
                        self._add_warning(
                            "常量传播",
                            f"函数 '{func_decl.name}' 中 '{var_name}' 的值可确定为常量 {value}",
                            "0:0"
                        )

                except Exception:
                    pass  # 单函数分析失败不阻断

        except Exception:
            pass

    def _run_interprocedural_analysis(self, ast: ASTNode) -> None:
        """运行过程间分析（调用图 + 递归检测 + 副作用 + 常量传播 + 上下文分析）

        使用 analyzer/interprocedural.py 的 InterproceduralAnalyzer，
        从 AST 提取函数定义并构建调用图，执行完整的过程间分析。
        所有发现以警告形式报告，不阻止编译。
        """
        if not self.interprocedural_enabled:
            return

        try:
            from .cfg_analyzer import find_functions, ast_to_statements
            from ..analyzer.interprocedural import InterproceduralAnalyzer

            ipa = InterproceduralAnalyzer()

            # 从 AST 构建函数定义列表
            func_defs = []
            for func_decl in find_functions(ast):
                func_dict = {
                    'name': func_decl.name,
                    'params': [p.name for p in func_decl.params if hasattr(p, 'name')],
                    'return_type': self._get_type_name(func_decl.return_type),
                    'param_types': [
                        self._get_type_name(p.param_type)
                        for p in func_decl.params if hasattr(p, 'param_type') and p.param_type
                    ],
                    'body': ast_to_statements(func_decl.body) if func_decl.body else []
                }
                func_defs.append(func_dict)

            if not func_defs:
                return

            # 1. 构建调用图
            ipa.build_call_graph(func_defs)

            # 2. 报告递归
            for cycle in ipa.recursion_detected:
                cycle_str = ' -> '.join(cycle)
                self._add_warning(
                    "递归调用",
                    f"检测到递归调用链: {cycle_str}",
                    "0:0",
                    suggestions=["确认递归是否有终止条件", "考虑使用迭代替代递归"]
                )

            # 3. 副作用分析：对每个函数执行副作用检测
            for func_def in func_defs:
                func_name = func_def['name']
                if func_def['body']:
                    try:
                        summary = ipa.analyze_side_effects(func_name, func_def['body'])
                        # 报告修改全局变量的函数
                        if summary.modifies_globals:
                            globals_str = ", ".join(sorted(summary.modifies_globals))
                            self._add_warning(
                                "副作用",
                                f"函数 '{func_name}' 修改全局变量: {globals_str}",
                                "0:0",
                                suggestions=["考虑通过参数传递代替直接修改全局变量"]
                            )
                        # 报告有 IO 操作的函数
                        from ..analyzer.interprocedural import SideEffect
                        if SideEffect.IO_OPERATION in summary.side_effects:
                            self._add_warning(
                                "副作用",
                                f"函数 '{func_name}' 包含 IO 操作",
                                "0:0",
                                suggestions=["确认 IO 操作是否必要"]
                            )
                    except Exception:
                        pass

            # 4. 过程间常量传播：对递归函数外的纯函数执行
            known_constants: Dict[str, Any] = {}
            for func_def in func_defs:
                func_name = func_def['name']
                if func_def['body'] and func_name not in [
                    c[0] for c in ipa.recursion_detected
                ]:
                    try:
                        propagated = ipa.propagate_constants_interprocedurally(
                            func_name, known_constants
                        )
                        known_constants.update(propagated)
                    except Exception:
                        pass

            # 5. 上下文敏感分析：对每个函数检查参数类型匹配
            for func_def in func_defs:
                func_name = func_def['name']
                if func_def['param_types']:
                    try:
                        known_types = {
                            func_def['params'][i]: func_def['param_types'][i]
                            for i in range(min(len(func_def['params']), len(func_def['param_types'])))
                        }
                        inferred = ipa.analyze_with_context(func_name, 'semantic_analysis', known_types)
                        # 如果推导出的类型与声明不一致，报告警告
                        for param, inferred_type in inferred.items():
                            if param in known_types and inferred_type != known_types[param]:
                                self._add_warning(
                                    "类型推导",
                                    f"函数 '{func_name}' 参数 '{param}' 的上下文推导类型 '{inferred_type}' 与声明类型 '{known_types[param]}' 不一致",
                                    "0:0"
                                )
                    except Exception:
                        pass

        except Exception:
            pass

    def _run_alias_analysis(self, ast: ASTNode) -> None:
        """运行别名分析（指针别名关系）

        使用 analyzer/alias_analysis.py 的 AliasAnalyzer，
        分析函数中的指针别名关系。
        检测到的别名问题以警告形式报告。
        """
        if not self.alias_enabled:
            return

        try:
            from .cfg_analyzer import find_functions, ast_to_statements
            from ..analyzer.interprocedural_alias import AliasAnalyzer

            analyzer = AliasAnalyzer()

            for func_decl in find_functions(ast):
                if not func_decl.body:
                    continue

                stmt_dicts = ast_to_statements(func_decl.body)

                try:
                    result = analyzer.analyze_function(func_decl.name, stmt_dicts)

                    # 检查别名对之间的关系，报告可疑的别名
                    ptrs = list(result.keys())
                    for i, ptr1 in enumerate(ptrs):
                        aliases = analyzer.get_all_aliases(ptr1)
                        for ptr2 in aliases:
                            # 检查是否指向相同内存但用途不同
                            alias_kind = analyzer.query_alias(ptr1, ptr2)
                            if alias_kind.value == "必须别名":
                                self._add_warning(
                                    "别名分析",
                                    f"函数 '{func_decl.name}' 中 '{ptr1}' 和 '{ptr2}' 指向同一内存（必须别名）",
                                    "0:0"
                                )

                    # 检查悬空别名（指向已释放内存的指针）
                    for ptr_name, info in result.items():
                        if info.may_point_to:
                            targets = ", ".join(sorted(info.may_point_to))
                            self._add_warning(
                                "别名分析",
                                f"函数 '{func_decl.name}' 中 '{ptr_name}' 可能指向: {targets}",
                                "0:0"
                            )

                except Exception:
                    pass  # 单函数分析失败不阻断

        except Exception:
            pass

    def _run_pointer_analysis(self, ast: ASTNode) -> None:
        """运行指针分析（空指针解引用 + 悬空指针 + 双重释放 + 智能指针 + 引用计数 + 指针运算）

        使用 analyzer/pointer_analysis.py 的 PointerAnalyzer，
        通过适配层将 AST 转为字典格式传入。
        所有发现根据严重程度报告为错误或警告。
        集成全部 5 个公开方法。
        """
        if not self.pointer_enabled:
            return

        try:
            from .cfg_analyzer import find_functions, ast_to_statements
            from ..analyzer.pointer_analysis import PointerAnalyzer

            analyzer = PointerAnalyzer()

            for func_decl in find_functions(ast):
                if not func_decl.body:
                    continue

                stmt_dicts = ast_to_statements(func_decl.body)
                params = [p for p in func_decl.params if hasattr(p, 'name')]

                try:
                    # 1. 基本指针状态分析（analyze_function）
                    issues = analyzer.analyze_function(func_decl.name, stmt_dicts)
                    for issue in issues:
                        loc = f"{issue.line_number}:0"
                        if issue.severity == "error":
                            self._add_error(
                                issue.error_type.value,
                                issue.message,
                                loc,
                                suggestions=[issue.suggestion]
                            )
                        else:
                            self._add_warning(
                                issue.error_type.value,
                                issue.message,
                                loc,
                                suggestions=[issue.suggestion]
                            )

                    # 2. 智能指针分析（analyze_smart_pointer）
                    for param in params:
                        param_type = self._get_type_name(param.param_type) if hasattr(param, 'param_type') and param.param_type else ''
                        if param_type and ('唯一指针' in param_type or 'unique_ptr' in param_type
                                            or '共享指针' in param_type or 'shared_ptr' in param_type):
                            try:
                                analyzer.analyze_smart_pointer(param.name, param_type, param.line if hasattr(param, 'line') else 0)
                            except Exception:
                                pass

                    # 3. 引用计数追踪（track_reference_count）—— 在分析器追踪到共享指针时自动启用
                    for ptr_name, info in analyzer.pointers.items():
                        if info.is_shared_ptr and info.reference_count > 1:
                            self._add_warning(
                                "引用计数",
                                f"函数 '{func_decl.name}' 中共享指针 '{ptr_name}' 引用计数为 {info.reference_count}",
                                "0:0",
                                suggestions=["确认共享所有权是否必要", "考虑使用唯一指针替代"]
                            )

                    # 4. 指针运算检查（check_pointer_arithmetic）
                    for stmt in stmt_dicts:
                        stmt_type = stmt.get('type', '')
                        line = stmt.get('line', 0)
                        # 检测指针运算（数组索引、指针加减）
                        if stmt_type == 'expression':
                            value = str(stmt.get('value', ''))
                            if any(op in value for op in ['+', '-']):
                                # 提取可能的指针名
                                for ptr_name in analyzer.pointers:
                                    if ptr_name in value and ('+' in value or '-' in value):
                                        analyzer.check_pointer_arithmetic(ptr_name, 'arithmetic', line)

                except Exception:
                    pass  # 单函数分析失败不阻断

            # 报告指针分析器新发现的问题
            for issue in analyzer.issues:
                # 避免重复报告（analyze_function 已经报告过的问题通过 PointerIssue 追踪）
                pass

        except Exception:
            pass



    def get_errors(self) -> List[SemanticErrorInfo]:
        """获取所有错误"""
        return self.errors
    
    def get_unique_errors(self) -> List[SemanticErrorInfo]:
        """获取去重后的错误列表（同一位置的同一类型只保留一个，按行号排序）"""
        seen = set()
        unique = []
        for err in self.errors:
            key = (err.location, err.error_type, err.message)
            if key not in seen:
                seen.add(key)
                unique.append(err)
        # 按位置排序
        return sorted(unique, key=lambda e: e.location)
    
    def get_warnings(self) -> List[SemanticErrorInfo]:
        """获取所有警告"""
        return self.warnings
    
    def format_errors(self) -> str:
        """格式化所有错误为标准输出（带修复建议）"""
        lines = []
        sorted_errors = sorted(self.errors, key=lambda e: e.location)
        
        for err in sorted_errors[:20]:
            lines.append(f"  {err}")
            if err.suggestions:
                for sug in err.suggestions[:2]:
                    lines.append(f"    💡 {sug}")
        
        if len(sorted_errors) > 20:
            lines.append(f"  ... 还有 {len(sorted_errors) - 20} 个错误未显示")
        
        return "\n".join(lines)
    
    def format_warnings(self) -> str:
        """格式化所有警告为标准输出"""
        lines = []
        for warn in self.warnings:
            lines.append(f"  ⚠️  {warn}")
        return "\n".join(lines)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            'symbol_table': self.symbol_table.get_statistics()
        }
    
    def print_report(self) -> None:
        """打印分析报告（包含所有分析器的综合报告）"""
        print("=" * 60)
        print("📊 语义分析报告")
        print("=" * 60)

        if self.errors:
            print(f"\n❌ 错误 ({len(self.errors)}):")
            for error in self.errors[:20]:
                print(f"  {error}")
                if error.suggestions:
                    for sug in error.suggestions[:2]:
                        print(f"    💡 {sug}")
            if len(self.errors) > 20:
                print(f"  ... 还有 {len(self.errors) - 20} 个错误未显示")

        if self.warnings:
            print(f"\n⚠️  警告 ({len(self.warnings)}):")
            for warning in self.warnings[:30]:
                print(f"  {warning}")
            if len(self.warnings) > 30:
                print(f"  ... 还有 {len(self.warnings) - 30} 个警告未显示")

        print(f"\n📈 统计:")
        print(f"  访问节点: {self.stats['nodes_visited']}")
        print(f"  添加符号: {self.stats['symbols_added']}")
        print(f"  错误数: {self.stats['errors_found']}")
        print(f"  警告数: {self.stats['warnings_found']}")

        symbol_stats = self.symbol_table.get_statistics()
        print(f"\n🗃️  符号表:")
        print(f"  总符号数: {symbol_stats['total_symbols']}")
        print(f"  作用域数: {symbol_stats['scope_count']}")
        print(f"  符号类型: {symbol_stats['symbols_by_type']}")

        # 各分析器独立报告（如果有数据）
        self._print_analyzer_reports()

        print("=" * 60)

        if self.errors:
            print("❌ 分析失败")
        else:
            print("✅ 分析成功")
        print("=" * 60)

    def _print_analyzer_reports(self) -> None:
        """打印各分析器的独立报告摘要"""
        report_printed = False

        # 数据流分析报告
        try:
            from ..analyzer.data_flow import DataFlowAnalyzer
            # 检查是否有数据流分析结果（通过检查是否有 taint 相关警告）
            taint_warnings = [w for w in self.warnings if w.error_type == "污点数据"]
            uninit_warnings = [w for w in self.warnings if w.error_type == "未初始化变量"]
            unused_warnings = [w for w in self.warnings if w.error_type == "未使用变量"]
            if taint_warnings or uninit_warnings or unused_warnings:
                print(f"\n📋 数据流分析:")
                if uninit_warnings:
                    print(f"  未初始化变量: {len(uninit_warnings)} 个")
                if unused_warnings:
                    print(f"  未使用变量: {len(unused_warnings)} 个")
                if taint_warnings:
                    print(f"  污点问题: {len(taint_warnings)} 个")
                report_printed = True
        except Exception:
            pass

        # 指针分析报告
        try:
            ptr_warnings = [w for w in self.warnings if w.error_type in (
                "空指针解引用", "悬空指针解引用", "无效释放", "双重释放", "无效指针操作"
            )]
            ptr_errors = [e for e in self.errors if e.error_type in (
                "空指针解引用", "悬空指针解引用", "无效释放", "双重释放"
            )]
            if ptr_warnings or ptr_errors:
                print(f"\n📋 指针分析:")
                print(f"  错误: {len(ptr_errors)} 个, 警告: {len(ptr_warnings)} 个")
                report_printed = True
        except Exception:
            pass

        # 内存安全报告
        try:
            mem_warnings = [w for w in self.warnings if w.error_type == "内存安全"]
            mem_errors = [e for e in self.errors if e.error_type == "内存安全"]
            if mem_warnings or mem_errors:
                print(f"\n📋 内存安全:")
                print(f"  错误: {len(mem_errors)} 个, 警告: {len(mem_warnings)} 个")
                report_printed = True
        except Exception:
            pass

        # 控制流报告
        try:
            cfg_warnings = [w for w in self.warnings if w.error_type in (
                "不可达代码", "无限循环", "圈复杂度"
            )]
            if cfg_warnings:
                print(f"\n📋 控制流分析:")
                for error_type in ("不可达代码", "无限循环", "圈复杂度"):
                    count = len([w for w in cfg_warnings if w.error_type == error_type])
                    if count:
                        print(f"  {error_type}: {count} 个")
                report_printed = True
        except Exception:
            pass

        # 过程间分析报告
        try:
            ip_warnings = [w for w in self.warnings if w.error_type in (
                "递归调用", "副作用", "类型推导"
            )]
            if ip_warnings:
                print(f"\n📋 过程间分析:")
                for error_type in ("递归调用", "副作用", "类型推导"):
                    count = len([w for w in ip_warnings if w.error_type == error_type])
                    if count:
                        print(f"  {error_type}: {count} 个")
                report_printed = True
        except Exception:
            pass

        # 别名分析报告
        try:
            alias_warnings = [w for w in self.warnings if w.error_type == "别名分析"]
            if alias_warnings:
                print(f"\n📋 别名分析:")
                print(f"  别名关系: {len(alias_warnings)} 个")
                report_printed = True
        except Exception:
            pass

        return report_printed

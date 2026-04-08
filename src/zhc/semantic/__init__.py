"""
语义分析模块
Semantic Analysis Module

提供语义检查、符号表管理、作用域分析等功能
"""

from .semantic_analyzer import (
    SemanticAnalyzer,
    SemanticError,
    SymbolTable,
    Symbol,
    ScopeType,
)

from .cfg_analyzer import CFGAnalyzer, UninitAnalyzer

# Phase 7 M0: 新的统一 Symbol/Scope 兼容别名
from ..ir.symbol import (
    Symbol as IRSymbol,
    Scope as IRScope,
    ScopeType as IRScopeType,
    SymbolCategory as IRSymbolCategory,
)

__all__ = [
    "SemanticAnalyzer",
    "SemanticError",
    "SymbolTable",
    "Symbol",
    "ScopeType",
    "CFGAnalyzer",
    "UninitAnalyzer",
    # Phase 7 M0 兼容别名
    "IRSymbol",
    "IRScope",
    "IRScopeType",
    "IRSymbolCategory",
]

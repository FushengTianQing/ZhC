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

# 数组语义分析器
from .array_analyzer import (
    ArraySemanticAnalyzer,
    ArrayAnalysisResult,
    ArrayTypeValidator,
)

# 语义错误恢复
from .semantic_recovery import (
    PlaceholderSymbol,
    SemanticRecoveryContext,
    SemanticErrorRecovery,
    SemanticErrorCollector,
)

__all__ = [
    # 核心语义分析
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
    # 数组分析
    "ArraySemanticAnalyzer",
    "ArrayAnalysisResult",
    "ArrayTypeValidator",
    # 语义错误恢复
    "PlaceholderSymbol",
    "SemanticRecoveryContext",
    "SemanticErrorRecovery",
    "SemanticErrorCollector",
]

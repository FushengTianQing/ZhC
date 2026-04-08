"""
ZHC编译器 - 语义分析模块

功能：
- 类型检查
- 作用域检查
- 函数重载解析
- 完整语义分析
- 数据流分析
- 控制流分析
- 内存安全分析
- 过程间分析（P0级新增）
- 别名分析（P0级新增）
- 指针分析（P0级新增）

作者：远
日期：2026-04-03
"""

from .type_checker import TypeChecker, TypeInfo, TypeCategory
from .scope_checker import ScopeChecker, Scope, Symbol, SymbolCategory
from .overload_resolver import OverloadResolver, OverloadCandidate

# analyzer/semantic_analyzer.py 已废弃（门面层冗余），实际使用 semantic/semantic_analyzer.py
# from .semantic_analyzer import SemanticAnalyzer, AnalysisResult
from .data_flow import DataFlowAnalyzer, DefUseChain, LiveVarInfo, TaintInfo
from .control_flow import ControlFlowAnalyzer, ControlFlowGraph, CFGNode, BasicBlock
from .memory_safety import (
    MemorySafetyAnalyzer,
    NullPointerChecker,
    MemoryLeakDetector,
    BoundsChecker,
    SafetyLevel,
    SafetyIssue,
)

# P0级新增模块
from .interprocedural import InterproceduralAnalyzer, FunctionSummary, CallGraph

# 别名分析模块已合并到 interprocedural_alias.py
from .interprocedural_alias import (
    AliasAnalyzer,
    AliasInfo,
    AliasSet,
    AliasKind,  # 兼容旧版 API
    InterproceduralAliasAnalyzer,
    AllocationSite,
    PointsToSet,  # 新版 API
    FunctionAliasInfo,
    CallSite,
)
from .pointer_analysis import PointerAnalyzer, PointerInfo, PointerState, PointerError

# P1级新增模块：性能优化
from .ast_cache import ASTCacheManager, CacheType, CacheEntry, ASTCacheStatistics
from .type_checker_cached import TypeCheckerCached
from .control_flow_cached import ControlFlowAnalyzerCached
from .symbol_lookup_optimizer import SymbolLookupOptimizer
from .incremental_ast_updater import (
    IncrementalASTUpdater,
    ASTDiffCalculator,
    DiffType,
    ASTDiff,
    EditOperation,
    TreeEditDistance,
)

__all__ = [
    # 类型检查
    "TypeChecker",
    "TypeInfo",
    "TypeCategory",
    # 作用域检查
    "ScopeChecker",
    "Scope",
    "Symbol",
    "SymbolCategory",
    # 重载解析
    "OverloadResolver",
    "OverloadCandidate",
    # 语义分析 (moved to semantic/semantic_analyzer.py)
    # 'SemanticAnalyzer',
    # 'AnalysisResult',
    # 数据流分析
    "DataFlowAnalyzer",
    "DefUseChain",
    "LiveVarInfo",
    "TaintInfo",
    # 控制流分析
    "ControlFlowAnalyzer",
    "ControlFlowGraph",
    "CFGNode",
    "BasicBlock",
    # 内存安全分析
    "MemorySafetyAnalyzer",
    "NullPointerChecker",
    "MemoryLeakDetector",
    "BoundsChecker",
    "SafetyLevel",
    "SafetyIssue",
    # P0级新增：过程间分析
    "InterproceduralAnalyzer",
    "FunctionSummary",
    "CallGraph",
    # P0级新增：别名分析（已合并到 interprocedural_alias）
    "AliasAnalyzer",
    "AliasInfo",
    "AliasSet",
    "AliasKind",
    "InterproceduralAliasAnalyzer",
    "AllocationSite",
    "PointsToSet",
    "FunctionAliasInfo",
    "CallSite",
    # P0级新增：指针分析
    "PointerAnalyzer",
    "PointerInfo",
    "PointerState",
    "PointerError",
    # P1级新增：性能优化
    "ASTCacheManager",
    "CacheType",
    "CacheEntry",
    "ASTCacheStatistics",
    "TypeCheckerCached",
    "ControlFlowAnalyzerCached",
    "SymbolLookupOptimizer",
    # P1级新增：增量AST更新
    "IncrementalASTUpdater",
    "ASTDiffCalculator",
    "DiffType",
    "ASTDiff",
    "EditOperation",
    "TreeEditDistance",
]

__version__ = "1.4.0"

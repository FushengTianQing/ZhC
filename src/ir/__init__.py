# -*- coding: utf-8 -*-
"""
ZHC IR 中间表示模块

提供 ZHC IR 的核心数据结构定义。
"""

from .symbol import (
    Symbol,
    Scope,
    ScopeType,
    SymbolCategory,
)
from .types import ZHCTy
from .opcodes import Opcode
from .values import IRValue, ValueKind
from .instructions import IRInstruction, IRBasicBlock
from .program import IRProgram, IRFunction, IRGlobalVar, IRStructDef
from .ir_generator import IRGenerator
from .c_backend import CBackend
from .printer import IRPrinter
from .optimizer import ConstantFolding, DeadCodeElimination, PassManager, OptimizationPass
from .ir_verifier import IRVerifier, VerificationError
from .ssa import SSABuilder, DominatorTree, DominanceFrontier, VersionedValue, PhiNode, build_ssa
from .dataflow import (
    DataFlowResult,
    DataFlowAnalysis,
    LivenessAnalysis,
    ReachingDefinitionsAnalysis,
    AvailableExpressionsAnalysis,
    Definition,
    Expression,
    analyze_liveness,
    analyze_reaching_definitions,
    analyze_available_expressions,
)
from .loop_optimizer import (
    LoopInfo,
    NaturalLoopDetection,
    LoopInvariantCodeMotion,
    StrengthReduction,
    LoopOptimizer,
    detect_loops,
    optimize_loops,
)
from .inline_optimizer import (
    InlineCost,
    InlineCostModel,
    FunctionInliner,
    InlineOptimizer,
    inline_functions,
)
from .register_allocator import (
    RegisterKind,
    Register,
    VirtualRegister,
    LiveInterval,
    AllocationResult,
    TargetArchitecture,
    LinearScanRegisterAllocator,
    GraphColorRegisterAllocator,
    simple_allocate,
)

__all__ = [
    # Symbol 系统
    "Symbol",
    "Scope",
    "ScopeType",
    "SymbolCategory",
    # 类型
    "ZHCTy",
    # 操作码
    "Opcode",
    # 值
    "IRValue",
    "ValueKind",
    # 指令和基本块
    "IRInstruction",
    "IRBasicBlock",
    # 程序结构
    "IRProgram",
    "IRFunction",
    "IRGlobalVar",
    "IRStructDef",
    # 生成器
    "IRGenerator",
    "CBackend",
    # 打印器
    "IRPrinter",
    # 优化器
    "ConstantFolding",
    "DeadCodeElimination",
    "PassManager",
    "OptimizationPass",
    # 验证器
    "IRVerifier",
    "VerificationError",
    # SSA 构建
    "SSABuilder",
    "DominatorTree",
    "DominanceFrontier",
    "VersionedValue",
    "PhiNode",
    "build_ssa",
    # 数据流分析
    "DataFlowResult",
    "DataFlowAnalysis",
    "LivenessAnalysis",
    "ReachingDefinitionsAnalysis",
    "AvailableExpressionsAnalysis",
    "Definition",
    "Expression",
    "analyze_liveness",
    "analyze_reaching_definitions",
    "analyze_available_expressions",
    # 循环优化
    "LoopInfo",
    "NaturalLoopDetection",
    "LoopInvariantCodeMotion",
    "StrengthReduction",
    "LoopOptimizer",
    "detect_loops",
    "optimize_loops",
    # 内联优化
    "InlineCost",
    "InlineCostModel",
    "FunctionInliner",
    "InlineOptimizer",
    "inline_functions",
    # 寄存器分配
    "RegisterKind",
    "Register",
    "VirtualRegister",
    "LiveInterval",
    "AllocationResult",
    "TargetArchitecture",
    "LinearScanRegisterAllocator",
    "GraphColorRegisterAllocator",
    "simple_allocate",
]

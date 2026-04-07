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
]

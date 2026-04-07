"""
优化模块
Optimization Module

提供常量折叠、死代码消除、循环优化等优化功能
"""

from .constant_fold import ConstantPropagator, propagate_constants, LatticeValue, ConstantType
from .dead_code_elim import DeadCodeEliminator, DeadCodeType, eliminate_dead_code
from .function_inline import FunctionInliner
from .loop_optimizer import LoopOptimizer

__all__ = [
    # 常量传播
    'ConstantPropagator',
    'propagate_constants',
    'LatticeValue',
    'ConstantType',
    # 死代码消除
    'DeadCodeEliminator',
    'DeadCodeType',
    'eliminate_dead_code',
    # 函数内联
    'FunctionInliner',
    # 循环优化
    'LoopOptimizer',
]
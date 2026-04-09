"""
类型推导模块
Type Inference Module

提供类型推导、类型检查、类型统一等功能
"""

from .engine import TypeInferenceEngine, TypeConstraint, TypeVariable, TypeEnv
from .auto_inference import (
    AutoTypeInferencer,
    InferenceResult,
    infer_auto_type,
    infer_function_return,
)

__all__ = [
    "TypeInferenceEngine",
    "TypeConstraint",
    "TypeVariable",
    "TypeEnv",
    "AutoTypeInferencer",
    "InferenceResult",
    "infer_auto_type",
    "infer_function_return",
]

# -*- coding: utf-8 -*-
"""
ZHC IR - 类型系统

提供 ZHCTy 作为 TypeInfo 的别名，供 IR 层使用。
TypeInfo 的定义保留在 analyzer/type_checker.py，不做迁移，避免破坏现有代码。

作者：远
日期：2026-04-03
"""

# TypeInfo 的别名，供 IR 层使用
# 避免在 ir/ 模块中直接引用 analyzer/ 的具体类，保持一定的独立性
from ..analyzer.type_checker import TypeInfo as ZHCTy

__all__ = ["ZHCTy"]

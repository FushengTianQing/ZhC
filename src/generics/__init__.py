"""
中文C语言泛型支持模块
Generic Programming Support for ZHC Language

提供泛型类型、泛型函数和泛型类的解析与实例化
"""

__version__ = '1.0.0'
__author__ = '中文C编译器团队'

from .generic_parser import GenericParser, GenericType, GenericFunction
from .generic_instantiator import GenericInstantiator

__all__ = [
    'GenericParser',
    'GenericType',
    'GenericFunction',
    'GenericInstantiator'
]
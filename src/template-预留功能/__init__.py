"""
中文C语言字符串模板模块
String Template Engine for ZHC Language

提供字符串模板的解析、编译和执行功能
"""

__version__ = '1.0.0'
__author__ = '中文C编译器团队'

from .template_engine import (
    TemplateEngine,
    TemplateVariable,
    TemplateBlock,
    TemplateCache,
    TemplateBlockType
)

__all__ = [
    'TemplateEngine',
    'TemplateVariable',
    'TemplateBlock',
    'TemplateCache',
    'TemplateBlockType'
]
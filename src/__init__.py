"""
zhc - 中文C预处理器

提供中文C代码到标准C代码的转换功能。

模块结构：
- parser: 解析器模块（模块、类、内存语法解析）
- converter: 转换器模块（代码、属性、方法转换）
- analyzer: 分析器模块（依赖、性能、内存安全）
- compiler: 编译器模块（流水线、缓存、优化）
- types: 类型系统模块（虚函数、运算符重载、智能指针）
- cli: 命令行工具
- lib: 标准库
"""

__version__ = "3.0.0"
__author__ = "中文C编译器项目组"

# 导出公共API
from .cli import main
from .keywords import M

__all__ = ["main", "M", "__version__"]
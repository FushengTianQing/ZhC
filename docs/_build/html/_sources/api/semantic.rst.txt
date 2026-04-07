语义分析模块
============

.. module:: src.semantic
   :synopsis: ZHC 语义分析模块

概述
----

语义分析模块负责类型检查、作用域分析和符号解析。

主要组件：

- **SemanticAnalyzer**: 主语义分析器
- **SymbolTable**: 符号表管理
- **TypeChecker**: 类型检查器

SemanticAnalyzer
----------------

.. autoclass:: src.semantic.analyzer.SemanticAnalyzer
   :members:
   :undoc-members:
   :show-inheritance:

SymbolTable
-----------

.. autoclass:: src.semantic.symbol_table.SymbolTable
   :members:
   :undoc-members:
   :show-inheritance:

Symbol
~~~~~~

.. autoclass:: src.semantic.symbol_table.Symbol
   :members:
   :undoc-members:
   :show-inheritance:

TypeChecker
-----------

.. autoclass:: src.semantic.type_checker.TypeChecker
   :members:
   :undoc-members:
   :show-inheritance:

类型系统
--------

Type
~~~~

.. autoclass:: src.semantic.types.Type
   :members:
   :undoc-members:
   :show-inheritance:

PrimitiveType
~~~~~~~~~~~~~

.. autoclass:: src.semantic.types.PrimitiveType
   :members:
   :undoc-members:
   :show-inheritance:

CompositeType
~~~~~~~~~~~~~

.. autoclass:: src.semantic.types.CompositeType
   :members:
   :undoc-members:
   :show-inheritance:

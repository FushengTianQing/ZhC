解析器模块
==========

.. module:: src.parser
   :synopsis: ZHC 解析器模块

概述
----

解析器模块负责将 ZHC 源代码转换为抽象语法树（AST）。

主要组件：

- **Lexer**: 词法分析器，将源代码转换为 Token 序列
- **Parser**: 语法分析器，构建 AST
- **AST Nodes**: 各种 AST 节点类型

Lexer
-----

.. autoclass:: src.parser.lexer.Lexer
   :members:
   :undoc-members:
   :show-inheritance:

Token 类型
~~~~~~~~~~

.. autoclass:: src.parser.lexer.Token
   :members:
   :undoc-members:
   :show-inheritance:

.. autodata:: src.parser.lexer.TokenType
   :members:

Parser
------

.. autoclass:: src.parser.parser.Parser
   :members:
   :undoc-members:
   :show-inheritance:

AST 节点
--------

基础节点
~~~~~~~~

.. autoclass:: src.parser.ast.ASTNode
   :members:
   :undoc-members:
   :show-inheritance:

表达式节点
~~~~~~~~~~

.. autoclass:: src.parser.ast.Expression
   :members:
   :undoc-members:
   :show-inheritance:

语句节点
~~~~~~~~

.. autoclass:: src.parser.ast.Statement
   :members:
   :undoc-members:
   :show-inheritance:

声明节点
~~~~~~~~

.. autoclass:: src.parser.ast.Declaration
   :members:
   :undoc-members:
   :show-inheritance:

API 参考
========

本节提供 ZHC 编译器的完整 API 参考。

核心模块
--------

.. toctree::
   :maxdepth: 2

   compiler
   parser
   semantic
   ir
   codegen

公共 API
--------

ZHC 提供以下公共 API：

CompilationResult
~~~~~~~~~~~~~~~~~

.. autoclass:: src.api.result.CompilationResult
   :members:
   :show-inheritance:

CompilationStats
~~~~~~~~~~~~~~~~

.. autoclass:: src.api.stats.CompilationStats
   :members:
   :show-inheritance:

CompilerConfig
~~~~~~~~~~~~~~

.. autoclass:: src.config.CompilerConfig
   :members:
   :show-inheritance:

配置分组
--------

SemanticConfig
~~~~~~~~~~~~~~

.. autoclass:: src.config.SemanticConfig
   :members:
   :show-inheritance:

OutputConfig
~~~~~~~~~~~~

.. autoclass:: src.config.OutputConfig
   :members:
   :show-inheritance:

CacheConfig
~~~~~~~~~~~

.. autoclass:: src.config.CacheConfig
   :members:
   :show-inheritance:

ProfileConfig
~~~~~~~~~~~~~

.. autoclass:: src.config.ProfileConfig
   :members:
   :show-inheritance:

工具模块
--------

file_utils
~~~~~~~~~~

.. automodule:: src.utils.file_utils
   :members:

string_utils
~~~~~~~~~~~~

.. automodule:: src.utils.string_utils
   :members:

error_utils
~~~~~~~~~~~

.. automodule:: src.utils.error_utils
   :members:

异常类
------

ZHCError
~~~~~~~~

.. autoclass:: src.errors.base.ZHCError
   :members:
   :show-inheritance:

LexerError
~~~~~~~~~~

.. autoclass:: src.errors.lexer_error.LexerError
   :members:
   :show-inheritance:

ParserError
~~~~~~~~~~~

.. autoclass:: src.errors.parser_error.ParserError
   :members:
   :show-inheritance:

SemanticError
~~~~~~~~~~~~~

.. autoclass:: src.errors.semantic_error.SemanticError
   :members:
   :show-inheritance:

CodeGenerationError
~~~~~~~~~~~~~~~~~~~

.. autoclass:: src.errors.codegen_error.CodeGenerationError
   :members:
   :show-inheritance:
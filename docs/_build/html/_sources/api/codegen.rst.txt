代码生成模块
============

.. module:: src.codegen
   :synopsis: ZHC 代码生成模块

概述
----

代码生成模块负责将 IR 转换为目标代码。

支持的后端：

- **C CodeGen**: 生成标准 C 代码
- **LLVM CodeGen**: 生成 LLVM IR（未来）
- **WASM CodeGen**: 生成 WebAssembly（未来）

CCodeGenerator
--------------

.. autoclass:: src.codegen.c_codegen.CCodeGenerator
   :members:
   :undoc-members:
   :show-inheritance:

CodeGenVisitor
~~~~~~~~~~~~~~

.. autoclass:: src.codegen.codegen_visitor.CodeGenVisitor
   :members:
   :undoc-members:
   :show-inheritance:

模板管理
--------

TemplateEngine
~~~~~~~~~~~~~~

.. autoclass:: src.codegen.template_engine.TemplateEngine
   :members:
   :undoc-members:
   :show-inheritance:

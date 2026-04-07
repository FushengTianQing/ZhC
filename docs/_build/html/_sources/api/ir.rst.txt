IR 中间表示模块
==============

.. module:: src.ir
   :synopsis: ZHC IR 中间表示模块

概述
----

IR 模块负责生成和管理中间表示代码。

主要组件：

- **IRGenerator**: IR 生成器
- **IROptimizer**: IR 优化器
- **IR Nodes**: IR 节点类型

IRGenerator
-----------

.. autoclass:: src.ir.ir_generator.IRGenerator
   :members:
   :undoc-members:
   :show-inheritance:

IROptimizer
-----------

.. autoclass:: src.ir.ir_optimizer.IROptimizer
   :members:
   :undoc-members:
   :show-inheritance:

IR Nodes
--------

IRNode
~~~~~~

.. autoclass:: src.ir.ir_node.IRNode
   :members:
   :undoc-members:
   :show-inheritance:

IRInstruction
~~~~~~~~~~~~~

.. autoclass:: src.ir.ir_node.IRInstruction
   :members:
   :undoc-members:
   :show-inheritance:

BasicBlock
~~~~~~~~~~

.. autoclass:: src.ir.basic_block.BasicBlock
   :members:
   :undoc-members:
   :show-inheritance:

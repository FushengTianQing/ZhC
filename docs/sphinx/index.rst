.. ZHC 文档 documentation master file

ZHC 中文C编译器
====================================

欢迎使用 ZHC 文档！

ZHC（中文C）是一个将中文语法C代码编译为标准C代码的编译器。

.. toctree::
   :maxdepth: 2
   :caption: 目录:

   简介 <self>
   guides/getting_started
   guides/developer_guide
   api/index
   reference/index

.. toctree::
   :maxdepth: 1
   :caption: 资源:

   GitHub 仓库 <https://github.com/FushengTianQing/ZhC>
   问题反馈 <https://github.com/FushengTianQing/ZhC/issues>

概述
----

ZHC 编译器的主要特性：

* **完整编译流水线**：词法分析 → 语法分析 → 语义分析 → 代码生成
* **中文语法支持**：支持中文关键字、变量名、函数名
* **模块系统**：支持多文件模块项目编译
* **性能优化**：增量编译、缓存、并行处理
* **IR 中间表示**：支持 IR 优化和多种后端

快速开始
--------

.. code-block:: bash

    # 安装
    pip install zhc

    # 编译单个文件
    zhc compile main.zhc -o main.c

    # 编译项目
    zhc compile --project main.zhc -o build/

.. code-block:: c
   :caption: main.zhc

   // ZHC 示例程序
   整数型 主函数() {
       中文整数型 消息 = 42;
       打印("你好，ZHC！答案是 %d\n", 消息);
       返回 0;
   }

.. code-block:: c
   :caption: main.c (生成的标准C代码)

   #include <stdio.h>

   int main() {
       int message = 42;
       printf("你好，ZHC！答案是 %d\n", message);
       return 0;
   }

索引和表格
----------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. image:: https://img.shields.io/badge/Python-3.8+-blue.svg
   :target: https://www.python.org/

.. image:: https://img.shields.io/badge/License-MIT-green.svg
   :target: https://opensource.org/licenses/MIT

快速开始
=========

本指南将帮助你在 5 分钟内上手 ZHC 编译器。

安装
----

确保你已安装 Python 3.8 或更高版本：

.. code-block:: bash

    python --version

使用 pip 安装 ZHC：

.. code-block:: bash

    pip install zhc

或者从源码安装：

.. code-block:: bash

    git clone https://github.com/FushengTianQing/ZhC.git
    cd ZhC
    pip install -e .

第一个程序
----------

创建你的第一个 ZHC 程序：

.. code-block:: c

   // hello.zhc
   整数型 主函数() {
       中文整数型 名字 = 42;
       打印("你好，ZHC！\n");
       返回 0;
   }

编译并运行：

.. code-block:: bash

    zhc compile hello.zhc -o hello.c
    gcc hello.c -o hello
    ./hello

输出：

.. code-block:: text

    你好，ZHC！

基础语法
--------

变量声明
~~~~~~~~

.. code-block:: c

   // 基本类型
   中文整数型 a = 10;           // 整数
   中文浮点型 b = 3.14;         // 浮点数
   中文字符型 c = 'x';          // 字符
   中文逻辑型 flag = 真;        // 布尔值

   // 常量
   中文常量 中文整数型 MAX = 100;

函数定义
~~~~~~~~

.. code-block:: c

   整数型 加法(整数型 a, 整数型 b) {
       返回 a + b;
   }

   空型 打印消息(中文字符型 消息[]) {
       打印("%s\n", 消息);
   }

控制流
~~~~~~

.. code-block:: c

   // 条件语句
   如果 (a > b) {
       打印("a 更大\n");
   } 否则 {
       打印("b 更大\n");
   }

   // 循环
   中文整数型 i = 0;
   当 (i < 10) {
       打印("%d\n", i);
       i = i + 1;
   }

模块导入
--------

.. code-block:: c

   // 导入标准库
   导入 <标准io>
   导入 <字符串>

   // 使用导入的函数
   整数型 主函数() {
       中文字符型 消息[] = "你好";
       整数型 长度 = 字符串长度(消息);
       打印("长度: %d\n", 长度);
       返回 0;
   }

高级特性
--------

泛型
~~~~

.. code-block:: c

   泛型 T 取最大值(泛型 T a, 泛型 T b) {
       如果 (a > b) {
           返回 a;
       }
       返回 b;
   }

   整数型 主函数() {
       中文整数型 x = 取最大值<中文整数型>(10, 20);
       中文浮点型 y = 取最大值<中文浮点型>(3.14, 2.71);
       返回 0;
   }

模板
~~~~

.. code-block:: c

   模板<类型名 T, 整数型 N>
   结构体 数组 {
       T 数据[N];
       整数型 长度;
   };

命令行工具
-----------

ZHC 提供完整的命令行工具：

.. code-block:: bash

    # 编译文件
    zhc compile input.zhc -o output.c

    # 编译项目
    zhc compile --project main.zhc -o build/

    # 查看帮助
    zhc --help

    # 查看版本
    zhc --version

编译选项
~~~~~~~~

=============== =============================================
选项            说明
=============== =============================================
``-o, --output`` 设置输出目录
``--project``   编译为项目（支持模块导入）
``-v, --verbose`` 详细输出
``-Werror``    将警告视为错误
``--profile``  启用性能分析
``--ir``       使用 IR 后端
=============== =============================================

下一步
------

* 阅读 :doc:`../guides/developer_guide` 了解开发指南
* 查看 :doc:`../api/index` 了解 API 文档
* 浏览 :doc:`../reference/index` 查看参考手册

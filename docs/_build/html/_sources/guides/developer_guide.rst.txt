开发者指南
============

本指南面向 ZHC 编译器的开发者，介绍如何参与项目开发。

开发环境搭建
------------

系统要求
~~~~~~~~

- Python 3.8 或更高版本
- Git
- Make（可选，用于构建脚本）

克隆仓库
~~~~~~~~

.. code-block:: bash

    git clone https://github.com/FushengTianQing/ZhC.git
    cd ZhC

安装依赖
~~~~~~~~

.. code-block:: bash

    # 创建虚拟环境（推荐）
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # 或 venv\Scripts\activate  # Windows

    # 安装开发依赖
    pip install -e ".[dev]"

    # 安装文档依赖
    pip install sphinx sphinx-rtd-theme myst-parser

验证安装
~~~~~~~~

.. code-block:: bash

    # 运行测试
    pytest

    # 检查代码风格
    black --check src/
    ruff check src/

    # 运行编译器
    python -m src --version

项目结构
--------

.. code-block:: text

    ZhC/
    ├── src/                  # 源代码
    │   ├── __init__.py       # 包入口
    │   ├── __main__.py       # CLI 入口
    │   ├── cli.py            # 命令行工具
    │   ├── parser/           # 解析器模块
    │   ├── semantic/         # 语义分析模块
    │   ├── ir/               # IR 中间表示
    │   ├── codegen/          # 代码生成模块
    │   ├── api/              # 公共 API
    │   ├── config/           # 配置管理
    │   ├── utils/            # 工具函数
    │   └── errors/           # 异常类
    ├── tests/                # 测试代码
    ├── docs/                 # 文档
    ├── examples/             # 示例代码
    ├── scripts/              # 构建脚本
    ├── pyproject.toml        # 项目配置
    └── README.md             # 项目说明

核心模块
--------

编译流水线
~~~~~~~~~~

ZHC 编译器采用经典的编译流水线架构：

.. code-block:: text

    源代码 → 词法分析 → 语法分析 → 语义分析 → IR → 代码生成 → 目标代码

各阶段职责：

1. **词法分析 (Lexer)**: 将源代码转换为 Token 序列
2. **语法分析 (Parser)**: 构建 AST（抽象语法树）
3. **语义分析 (Semantic)**: 类型检查、作用域分析、符号解析
4. **IR 生成**: 生成中间表示
5. **代码生成 (Codegen)**: 生成目标代码（C/LLVM/WASM）

关键文件
~~~~~~~~

- ``src/cli.py``: 主编译器入口，包含 ``ZHCCompiler`` 类
- ``src/parser/parser.py``: 语法解析器
- ``src/semantic/analyzer.py``: 语义分析器
- ``src/ir/ir_generator.py``: IR 生成器
- ``src/codegen/c_codegen.py``: C 代码生成器

代码编写规范
------------

代码风格
~~~~~~~~

ZHC 使用以下代码风格工具：

- **Black**: 代码格式化
- **Ruff**: 代码检查
- **MyPy**: 类型检查

配置文件：

- ``pyproject.toml``: Black 和 Ruff 配置
- ``mypy.ini``: MyPy 配置

格式化代码
^^^^^^^^^^

.. code-block:: bash

    # 格式化所有代码
    black src/ tests/

    # 检查格式（不修改）
    black --check src/ tests/

代码检查
^^^^^^^^

.. code-block:: bash

    # 运行 Ruff 检查
    ruff check src/ tests/

    # 自动修复
    ruff check --fix src/ tests/

类型检查
^^^^^^^^

.. code-block:: bash

    # 运行 MyPy
    mypy src/

命名规范
~~~~~~~~

- **类名**: PascalCase（如 ``CompilationResult``）
- **函数名**: snake_case（如 ``compile_single_file``）
- **变量名**: snake_case（如 ``input_file``）
- **常量名**: UPPER_SNAKE_CASE（如 ``MAX_RETRIES``）
- **私有成员**: 前缀 ``_``（如 ``_run_semantic_check``）

文档规范
~~~~~~~~

使用 Google 风格的 docstring：

.. code-block:: python

    def compile_single_file(
        self, input_file: Path, output_dir: Optional[Path] = None
    ) -> CompilationResult:
        """编译单个文件（AST 模式）。

        Args:
            input_file: 输入文件路径。
            output_dir: 输出目录路径，默认为输入文件所在目录。

        Returns:
            CompilationResult: 编译结果对象。

        Raises:
            FileNotFoundError: 输入文件不存在。
            CompilationError: 编译过程中出错。

        Example:
            >>> compiler = ZHCCompiler()
            >>> result = compiler.compile_single_file(Path("main.zhc"))
            >>> print(result.success)
            True
        """
        ...

测试编写指南
------------

测试框架
~~~~~~~~

ZHC 使用 pytest 作为测试框架。

运行测试
^^^^^^^^

.. code-block:: bash

    # 运行所有测试
    pytest

    # 运行特定测试文件
    pytest tests/test_parser.py

    # 运行特定测试类
    pytest tests/test_parser.py::TestLexer

    # 运行特定测试方法
    pytest tests/test_parser.py::TestLexer::test_basic_tokens

    # 显示详细输出
    pytest -v

    # 显示覆盖率
    pytest --cov=src --cov-report=html

测试结构
~~~~~~~~

.. code-block:: text

    tests/
    ├── conftest.py           # 测试配置和 fixtures
    ├── test_parser.py        # 解析器测试
    ├── test_semantic.py      # 语义分析测试
    ├── test_ir.py            # IR 测试
    ├── test_codegen.py       # 代码生成测试
    ├── test_cli.py           # CLI 测试
    └── fixtures/             # 测试数据

编写测试
^^^^^^^^

.. code-block:: python

    import pytest
    from pathlib import Path
    from zhpp.parser import Parser
    from zhpp.semantic import SemanticAnalyzer


    class TestParser:
        """解析器测试类。"""

        def setup_method(self):
            """每个测试方法前的初始化。"""
            self.parser = Parser()

        def test_basic_tokens(self):
            """测试基本 Token 解析。"""
            code = "整数型 x = 10;"
            tokens = self.parser.tokenize(code)
            assert len(tokens) > 0
            assert tokens[0].type == "INTEGER_TYPE"

        def test_function_definition(self):
            """测试函数定义解析。"""
            code = """
            整数型 加法(整数型 a, 整数型 b) {
                返回 a + b;
            }
            """
            ast = self.parser.parse(code)
            assert ast.type == "FunctionDefinition"
            assert ast.name == "加法"

        @pytest.mark.parametrize("code,expected", [
            ("整数型 x = 1;", "INTEGER_TYPE"),
            ("浮点型 y = 2.0;", "FLOAT_TYPE"),
            ("字符型 c = 'a';", "CHAR_TYPE"),
        ])
        def test_type_keywords(self, code: str, expected: str):
            """测试类型关键字（参数化测试）。"""
            tokens = self.parser.tokenize(code)
            assert tokens[0].type == expected


    class TestSemanticAnalyzer:
        """语义分析器测试类。"""

        def test_type_checking(self):
            """测试类型检查。"""
            code = "整数型 x = 10; 浮点型 y = x;"
            # 应该报错：类型不匹配
            with pytest.raises(SemanticError):
                analyzer = SemanticAnalyzer()
                analyzer.analyze(code)

使用 fixtures
^^^^^^^^^^^^

.. code-block:: python

    # conftest.py
    import pytest
    from pathlib import Path
    from zhpp.cli import ZHCCompiler


    @pytest.fixture
    def compiler():
        """提供编译器实例。"""
        return ZHCCompiler()


    @pytest.fixture
    def sample_file(tmp_path):
        """提供示例文件。"""
        file = tmp_path / "test.zhc"
        file.write_text("整数型 主函数() { 返回 0; }")
        return file


    # test_cli.py
    def test_compile_file(compiler, sample_file):
        """使用 fixtures 测试文件编译。"""
        result = compiler.compile_single_file(sample_file)
        assert result.success

调试技巧
--------

日志调试
~~~~~~~~

启用详细日志：

.. code-block:: bash

    # CLI 调试
    zhc compile main.zhc -v

    # Python 调试
    import logging
    logging.basicConfig(level=logging.DEBUG)

断点调试
~~~~~~~~

使用 pdb 调试：

.. code-block:: python

    # 在代码中插入断点
    import pdb; pdb.set_trace()

    # 或使用 breakpoint()（Python 3.7+）
    breakpoint()

IDE 调试
^^^^^^^^

- VSCode: 使用 Python 扩展的调试功能
- PyCharm: 内置调试器

常见调试场景
^^^^^^^^^^^^

1. **解析错误**: 检查 Token 序列和 AST 结构
2. **语义错误**: 检查符号表和类型信息
3. **代码生成错误**: 检查 IR 和目标代码

常见问题解答（FAQ）
------------------

Q1: 如何添加新的关键字？
~~~~~~~~~~~~~~~~~~~~~~~~

**A**: 在 ``src/keywords.py`` 中添加：

.. code-block:: python

    M = {
        # 现有关键字...
        "新关键字": "new_keyword",
    }

然后更新解析器和语义分析器。

Q2: 如何添加新的代码生成后端？
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**A**: 在 ``src/codegen/`` 中创建新模块：

.. code-block:: python

    # src/codegen/wasm_codegen.py
    class WasmCodeGenerator:
        def generate(self, ir_node) -> str:
            # 实现 WASM 代码生成
            ...

然后在 ``src/cli.py`` 中注册：

.. code-block:: python

    def compile_with_backend(self, backend: str):
        if backend == "wasm":
            generator = WasmCodeGenerator()
            ...

Q3: 如何处理编译错误？
~~~~~~~~~~~~~~~~~~~~~~

**A**: 使用 ``CompilationResult`` 对象：

.. code-block:: python

    result = compiler.compile_single_file(file)
    if not result.success:
        for error in result.errors:
            print(f"错误: {error}")
        # 或抛出异常
        raise CompilationError(result.errors)

Q4: 如何运行性能测试？
~~~~~~~~~~~~~~~~~~~~~~

**A**: 使用 ``--profile`` 选项：

.. code-block:: bash

    zhc compile main.zhc --profile

或使用 Python profiler：

.. code-block:: python

    import cProfile
    cProfile.run("compiler.compile_single_file(file)")

Q5: 如何贡献代码？
~~~~~~~~~~~~~~~~~~

**A**: 参见 :doc:`../guides/contributing` 贡献指南。

1. Fork 仓库
2. 创建特性分支
3. 编写代码和测试
4. 提交 Pull Request

Q6: 如何更新文档？
~~~~~~~~~~~~~~~~~~

**A**: 修改 ``docs/`` 目录下的文件：

- ``docs/sphinx/``: Sphinx 文档
- ``docs/*.md``: Markdown 文档

构建文档：

.. code-block:: bash

    python scripts/build_docs.py

Q7: 如何处理依赖问题？
~~~~~~~~~~~~~~~~~~~~~~

**A**: 检查 ``pyproject.toml`` 中的依赖版本：

.. code-block:: bash

    # 查看依赖
    pip list

    # 更新依赖
    pip install --upgrade -e ".[dev]"

Q8: 如何调试测试失败？
~~~~~~~~~~~~~~~~~~~~~~

**A**: 使用 pytest 的调试选项：

.. code-block:: bash

    # 显示详细输出
    pytest -v --tb=long

    # 只运行失败的测试
    pytest --lf

    # 进入 pdb 调试
    pytest --pdb

Q9: 如何添加新的测试？
~~~~~~~~~~~~~~~~~~~~~~

**A**: 在 ``tests/`` 中创建测试文件：

.. code-block:: python

    # tests/test_new_feature.py
    import pytest


    class TestNewFeature:
        def test_basic(self):
            # 测试基本功能
            ...

Q10: 如何处理类型检查错误？
~~~~~~~~~~~~~~~~~~~~~~~~~~

**A**: 使用 MyPy 检查：

.. code-block:: bash

    mypy src/

常见错误：

- 缺少类型注解
- 类型不匹配
- Optional 类型未处理

下一步
------

- 阅读 :doc:`../api/index` 了解 API 文档
- 查看 :doc:`../reference/index` 查看参考手册
- 参见 :doc:`../guides/contributing` 了解贡献流程
# 贡献指南

感谢你对中国C编译器（ZHC）项目的兴趣！我们欢迎各种形式的贡献，包括但不限于代码、文档、问题反馈和功能建议。

---

## 目录

1. [行为准则](#行为准则)
2. [入门指南](#入门指南)
3. [开发环境](#开发环境)
4. [代码规范](#代码规范)
5. [提交流程](#提交流流程)
6. [Pull Request 指南](#pull-request-指南)
7. [Issue 指南](#issue-指南)
8. [文档贡献](#文档贡献)
9. [测试指南](#测试指南)
10. [版本发布](#版本发布)

---

## 行为准则

我们承诺为所有参与者提供一个友好、安全的环境。请遵守以下准则：

- **尊重他人**：使用包容性语言，尊重不同的观点和经验
- **专业态度**：对建设性反馈保持开放和接受的态度
- **协作精神**：优先考虑社区的整体利益，而不是个人利益

任何违反行为准则的行为都将被严肃处理。

---

## 入门指南

### Fork 项目

1. 点击 GitHub 页面右上角的 **Fork** 按钮
2. 克隆你的 fork 到本地：

```bash
git clone https://github.com/<your-username>/ZhC.git
cd ZhC
```

### 添加上游仓库

```bash
git remote add upstream https://github.com/FushengTianQing/ZhC.git
```

### 创建特性分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

---

## 开发环境

### 系统要求

- Python 3.8 或更高版本
- Git
- 推荐使用 macOS / Linux

### 安装依赖

```bash
# 克隆仓库后
cd ZhC

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装项目
pip install -e ".[dev]"

# 安装额外依赖
pip install sphinx sphinx-rtd-theme myst-parser
```

### 验证安装

```bash
# 运行测试
pytest

# 检查代码风格
black --check src/ tests/
ruff check src/ tests/

# 启动编译器
python3 -m src --version
```

---

## 代码规范

### 代码格式化

我们使用 **Black** 进行代码格式化：

```bash
# 格式化所有代码
black src/ tests/

# 检查格式（不修改）
black --check src/ tests/
```

### 代码检查

我们使用 **Ruff** 进行代码检查：

```bash
# 检查所有问题
ruff check src/ tests/

# 自动修复
ruff check --fix src/ tests/
```

### 类型检查

我们使用 **MyPy** 进行类型检查：

```bash
# 运行类型检查
mypy src/

# 检查配置文件
cat mypy.ini
```

### 命名规范

| 类型 | 规范 | 示例 |
|:-----|:-----|:-----|
| 类名 | PascalCase | `CompilationResult` |
| 函数名 | snake_case | `compile_single_file` |
| 变量名 | snake_case | `input_file` |
| 常量名 | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| 私有成员 | 前缀 `_` | `_run_semantic_check` |

### Docstring 规范

使用 Google 风格的 docstring：

```python
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
```

---

## 提交流程

### Commit 规范

我们使用 **Conventional Commits** 规范：

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### 类型 (type)

- `feat`: 新功能
- `fix`: 错误修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `ci`: CI/CD 相关
- `chore`: 其他杂项

### 示例

```bash
# 新功能
git commit -m "feat(cli): 添加 IR 后端支持"

# 错误修复
git commit -m "fix(parser): 修复字符串解析错误"

# 文档更新
git commit -m "docs: 更新 API 文档"

# 重构
git commit -m "refactor(api): 重构 CompilationResult"
```

### 提交前检查

```bash
# 1. 运行所有测试
pytest

# 2. 检查代码风格
black --check src/ tests/
ruff check src/ tests/

# 3. 类型检查
mypy src/

# 4. 构建文档
python3 scripts/build_docs.py
```

---

## Pull Request 指南

### 创建 PR

1. **标题格式**：`[TYPE] 简短描述`

   示例：`[FEAT] 添加泛型支持` 或 `[FIX] 修复内存泄漏`

2. **描述内容**：

   ```markdown
   ## 描述
   <!-- 简要说明这个 PR 做了什么 -->

   ## 解决的问题
   <!-- 链接到相关 Issue，如：Closes #123 -->

   ## 测试
   <!-- 说明你如何测试了这个更改 -->

   - [ ] 添加了新测试
   - [ ] 现有测试通过
   - [ ] 手动测试通过
   ```

### PR 检查清单

- [ ] 代码遵循项目代码规范
- [ ] 添加了必要的测试
- [ ] 所有测试通过
- [ ] 文档已更新（如需要）
- [ ] Commit 信息符合规范

### Review 流程

1. 至少需要一个 Reviewer 批准
2. 所有 CI 检查通过
3. 没有未解决的评论

---

## Issue 指南

### 创建 Issue

在创建 Issue 之前，请先搜索是否已存在类似的问题。

### Bug Report

使用以下模板：

```markdown
## Bug 描述
<!-- 清晰描述问题 -->

## 重现步骤
1.
2.
3.

## 预期行为
<!-- 描述应该发生什么 -->

## 实际行为
<!-- 描述实际发生了什么 -->

## 环境信息
- OS: [e.g., macOS 14.0]
- Python 版本: [e.g., 3.9.6]
- ZHC 版本: [e.g., 3.0.0]

## 相关代码
<!-- 如果有，添加相关代码片段 -->

## 日志输出
<!-- 添加错误日志 -->
```

### Feature Request

使用以下模板：

```markdown
## 功能描述
<!-- 简要描述你希望添加的功能 -->

## 使用场景
<!-- 描述这个功能将如何被使用 -->

## 可能的解决方案
<!-- 如果有，描述你设想的实现方式 -->

## 替代方案
<!-- 如果有，描述其他可能的解决方案 -->

## 其他信息
<!-- 任何其他相关的信息 -->
```

---

## 文档贡献

### 文档类型

- **API 文档**：在 docstring 中编写，使用 Sphinx autodoc
- **指南文档**：在 `docs/sphinx/guides/` 中添加
- **参考文档**：在 `docs/sphinx/reference/` 中添加
- **架构文档**：在 `docs/ARCHITECTURE.md` 中更新

### 构建文档

```bash
# 构建 HTML 文档
python3 scripts/build_docs.py

# 启动本地服务器查看
python3 scripts/build_docs.py --serve
```

---

## 测试指南

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_parser.py

# 运行带覆盖率报告
pytest --cov=src --cov-report=html

# 查看覆盖率
open htmlcov/index.html
```

### 编写测试

```python
import pytest
from pathlib import Path
from zhpp.cli import ZHCCompiler


class TestCompiler:
    """编译器测试类。"""

    def setup_method(self):
        """每个测试方法前的初始化。"""
        self.compiler = ZHCCompiler()

    def test_compile_simple(self, tmp_path):
        """测试简单文件编译。"""
        # 创建测试文件
        file = tmp_path / "test.zhc"
        file.write_text("整数型 主函数() { 返回 0; }")

        # 编译
        result = self.compiler.compile_single_file(file)

        # 验证
        assert result.success
        assert len(result.output_files) > 0

    @pytest.mark.parametrize("code,expected", [
        ("整数型 x = 1;", "INTEGER_TYPE"),
        ("浮点型 y = 2.0;", "FLOAT_TYPE"),
    ])
    def test_type_keywords(self, code: str, expected: str):
        """参数化测试类型关键字。"""
        # ...
```

---

## 版本发布

### 版本号规则

我们使用语义化版本 (SemVer)：

```
主版本号.次版本号.修订号
  MAJOR    MINOR    PATCH
```

- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的功能增加
- **PATCH**: 向后兼容的错误修复

### 发布流程

1. 更新 `CHANGELOG.md`
2. 更新 `__version__` 在 `src/__init__.py`
3. 创建 Git tag
4. 推送到 GitHub

---

## 联系方式

如果你有任何问题，可以通过以下方式联系我们：

- GitHub Issues: https://github.com/FushengTianQing/ZhC/issues
- 项目讨论: https://github.com/FushengTianQing/ZhC/discussions

---

感谢你的贡献！🎉
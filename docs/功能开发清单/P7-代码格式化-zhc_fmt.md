# P7-代码格式化-自动代码格式化 开发分析文档

## 基本信息

| 字段 | 内容 |
|------|------|
| **优先级** | P7 |
| **功能模块** | 代码格式化 |
| **功能名称** | zhc fmt 工具 |
| **文档版本** | 1.0.0 |
| **创建日期** | 2026-04-10 |
| **预计工时** | 约 2-3 周 |

---

## 1. 功能概述

`zhc fmt` 是一个自动代码格式化工具，用于统一 ZhC 代码风格，提高代码可读性和一致性。该工具类似于 Go 的 `gofmt` 或 Rust 的 `rustfmt`。

### 1.1 核心目标

- 自动格式化代码，保持一致的代码风格
- 支持配置化格式化规则
- 支持部分格式化（指定文件或目录）
- 支持检查模式（仅检查不修改）
- 与编辑器集成

### 1.2 设计原则

| 原则 | 描述 |
|------|------|
| **无配置** | 默认提供最佳实践，减少配置负担 |
| **确定性** | 相同输入产生相同输出 |
| **快速** | 格式化速度快，支持增量格式化 |
| **安全** | 保留注释，不改变语义 |

---

## 2. 详细设计

### 2.1 命令行接口

```bash
# 基本用法
zhc fmt [选项] [文件/目录...]

# 格式化单个文件
zhc fmt main.zhc

# 格式化整个目录
zhc fmt src/

# 检查模式（不修改，返回退出码）
zhc fmt --check src/

# diff 模式（显示差异）
zhc fmt --diff src/

# 指定配置文件
zhc fmt --config .zhcfmt.toml main.zhc

# 格式化到标准输出
zhc fmt --stdout main.zhc

# 忽略文件
zhc fmt --exclude "*.generated.zhc" src/
```

### 2.2 配置文件

```toml
# .zhcfmt.toml 或 zhcfmt.toml

[general]
# 缩进类型: "space" 或 "tab"
indent_type = "space"
# 缩进宽度
indent_width = 4
# 行尾: "lf" 或 "crlf"
line_ending = "lf"
# 最大行长度
max_line_length = 100

[spacing]
# 大括号前的空格
brace_space = true
# 操作符周围的空格
operator_space = true
# 逗号后的空格
comma_space = true
# 冒号后的空格（类型注解）
colon_space = true

[blank_lines]
# 函数之间的空行数
between_functions = 2
# 结构体之间的空行数
between_structs = 1
# 块之间的空行数
between_blocks = 1
# 文件开头的空行
file_start = 0
# 文件末尾的空行
file_end = 1

[alignment]
# 赋值对齐
align_assignment = true
# 变量声明对齐
align_variable = true
# 注释对齐
align_comments = false

[formatting]
# if-else 链的格式化
if_else_chain = "one_line"  # "one_line", "each_on_new_line"
# for 循环的格式化
for_loop = "compact"  # "compact", "expanded"
# 函数签名换行
function_signature = "allow_break"  # "single_line", "allow_break"
```

### 2.3 格式化规则

#### 2.3.1 缩进规则

```zhc
# 基础缩进
函数 主函数() -> 整数
    变量 x = 10
    如果 x > 0 则
        打印行("正数")
    结束
结束

# 嵌套缩进
函数 复杂函数() -> 整数
    对于 i 从 0 到 10 执行
        如果 i % 2 == 0 则
            打印行("偶数")
        否则
            打印行("奇数")
        结束
    结束
    返回 0
结束
```

#### 2.3.2 空格规则

```zhc
# 操作符周围的空格
变量 a = b + c * d
变量 result = (x - y) / z

# 类型注解冒号后的空格
变量 name: 字符串 = "hello"
函数 打印(消息: 字符串) -> 空类型

# 逗号后的空格
函数 调用(a: 整数, b: 浮点数, c: 字符串)

# 大括号前的空格
结构体 点
    x: 浮点数
    y: 浮点数
结束

# 大括号后的换行
函数 示例()
    变量 x = 10
    如果 x > 0 则
        打印行("正数")
    结束
结束
```

#### 2.3.3 空行规则

```zhc
# 函数之间两个空行
函数 第一个函数()
    # ...
结束


函数 第二个函数()
    # ...
结束

# 块之间一个空行
函数 复杂函数()
    # 第一块
    变量 x = 10
    如果 x > 0 则
        打印行("正数")
    结束

    # 第二块
    变量 y = 20
    当 y > 0 执行
        y = y - 1
    结束
结束
```

#### 2.3.4 换行规则

```zhc
# 长行换行（超过 100 字符）
函数 长参数函数(
    参数一: 整数,
    参数二: 字符串,
    参数三: 浮点数,
    参数四: 布尔
) -> 整数
    返回 0
结束

# 链式调用换行
变量 结果 = 对象
    .方法一(参数一)
    .方法二(参数二)
    .方法三(参数三)

# 复杂表达式换行
变量 结果 = 非常长的变量名 +
    另一个变量名 *
    第三个变量名 -
    第四个变量名
```

### 2.4 核心实现

```python
# src/zhc/fmt/formatter.py

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum, auto

class IndentType(Enum):
    SPACE = auto()
    TAB = auto()

@dataclass
class FormatConfig:
    """格式化配置"""
    indent_type: IndentType = IndentType.SPACE
    indent_width: int = 4
    max_line_length: int = 100
    brace_space: bool = True
    operator_space: bool = True
    comma_space: bool = True
    between_functions: int = 2
    between_structs: int = 1
    between_blocks: int = 1

class ZhCFormatter:
    """ZhC 代码格式化器"""

    def __init__(self, config: Optional[FormatConfig] = None):
        self.config = config or FormatConfig()
        self.indent_char = " " if self.config.indent_type == IndentType.SPACE else "\t"
        self.current_indent = 0

    def format(self, source: str) -> str:
        """格式化源代码"""
        # 1. 解析 AST
        ast = self._parse(source)

        # 2. 遍历 AST 并格式化
        lines = self._format_ast(ast)

        # 3. 处理空行
        lines = self._add_blank_lines(lines)

        # 4. 处理换行
        lines = self._break_long_lines(lines)

        return "\n".join(lines)

    def _format_ast(self, ast: ASTNode) -> List[str]:
        """格式化 AST 节点"""
        lines = []

        for node in ast.children:
            if isinstance(node, FunctionDecl):
                lines.extend(self._format_function(node))
            elif isinstance(node, StructDecl):
                lines.extend(self._format_struct(node))
            elif isinstance(node, EnumDecl):
                lines.extend(self._format_enum(node))
            elif isinstance(node, ImportDecl):
                lines.extend(self._format_import(node))
            elif isinstance(node, Statement):
                lines.extend(self._format_statement(node))

        return lines

    def _format_function(self, func: FunctionDecl) -> List[str]:
        """格式化函数声明"""
        lines = []

        # 函数签名
        sig = self._format_function_signature(func)
        lines.append(sig)

        # 函数体
        self.current_indent += 1
        for stmt in func.body.statements:
            lines.extend(self._format_statement(stmt))
        self.current_indent -= 1

        # 结束关键字
        lines.append(self._indent() + "结束")

        return lines

    def _format_function_signature(self, func: FunctionDecl) -> str:
        """格式化函数签名"""
        # 处理参数列表换行
        if len(func.params) > 3:
            return self._format_multiline_signature(func)
        else:
            return self._format_single_line_signature(func)

    def _format_multiline_signature(self, func: FunctionDecl) -> str:
        """格式化多行函数签名"""
        lines = []
        lines.append(self._indent() + "函数 " + func.name + "(")

        self.current_indent += 1
        for i, param in enumerate(func.params):
            param_str = self._format_parameter(param)
            if i < len(func.params) - 1:
                param_str += ","
            lines.append(self._indent() + param_str)
        self.current_indent -= 1

        ret_type = f" -> {func.return_type}" if func.return_type else ""
        lines.append(self._indent() + ")" + ret_type)

        return "\n".join(lines)

    def _format_statement(self, stmt: Statement) -> List[str]:
        """格式化语句"""
        if isinstance(stmt, IfStatement):
            return self._format_if(stmt)
        elif isinstance(stmt, WhileStatement):
            return self._format_while(stmt)
        elif isinstance(stmt, ForStatement):
            return self._format_for(stmt)
        elif isinstance(stmt, VariableDecl):
            return [self._indent() + self._format_variable_decl(stmt)]
        elif isinstance(stmt, ReturnStatement):
            return [self._indent() + self._format_return(stmt)]
        elif isinstance(stmt, ExpressionStatement):
            return [self._indent() + self._format_expression(stmt.expr) + ";"]

    def _format_if(self, if_stmt: IfStatement) -> List[str]:
        """格式化 if 语句"""
        lines = []

        # if 条件
        cond = self._format_expression(if_stmt.condition)
        lines.append(self._indent() + f"如果 {cond} 则")

        # then 块
        self.current_indent += 1
        for stmt in if_stmt.then_body.statements:
            lines.extend(self._format_statement(stmt))
        self.current_indent -= 1

        # else 块
        if if_stmt.else_body:
            lines.append(self._indent() + "否则")
            self.current_indent += 1
            for stmt in if_stmt.else_body.statements:
                lines.extend(self._format_statement(stmt))
            self.current_indent -= 1

        lines.append(self._indent() + "结束")

        return lines

    def _indent(self) -> str:
        """生成当前缩进"""
        return self.indent_char * (self.current_indent * self.config.indent_width)

    def _format_expression(self, expr: Expression) -> str:
        """格式化表达式"""
        if isinstance(expr, BinaryExpr):
            left = self._format_expression(expr.left)
            right = self._format_expression(expr.right)
            op = expr.operator
            if self.config.operator_space:
                return f"{left} {op} {right}"
            else:
                return f"{left}{op}{right}"
        elif isinstance(expr, FunctionCall):
            args = ", ".join(self._format_expression(a) for a in expr.args)
            return f"{expr.name}({args})"
        elif isinstance(expr, Identifier):
            return expr.name
        elif isinstance(expr, Literal):
            return str(expr.value)
```

### 2.5 增量格式化

```python
# src/zhc/fmt/incremental.py

class IncrementalFormatter:
    """增量格式化器，只格式化修改的部分"""

    def __init__(self, formatter: ZhCFormatter):
        self.formatter = formatter
        self.cache: Dict[str, str] = {}

    def format_file(self, path: str, content: str) -> str:
        """格式化单个文件"""
        # 检查缓存
        if path in self.cache:
            cached = self.cache[path]
            if cached == content:
                return content  # 未修改

        # 格式化
        formatted = self.formatter.format(content)

        # 更新缓存
        self.cache[path] = formatted

        return formatted

    def format_diff(self, old_content: str, new_content: str) -> List[Edit]:
        """计算格式化差异"""
        old_formatted = self.formatter.format(old_content)
        new_formatted = self.formatter.format(new_content)

        return self._compute_diff(old_formatted, new_formatted)
```

---

## 3. 实现方案

### 3.1 第一阶段：基础格式化

1. **配置系统**
   - TOML 配置解析
   - 默认配置

2. **基本格式化**
   - 缩进处理
   - 空格处理
   - 换行处理

3. **命令行工具**
   - 文件读写
   - 批量处理

### 3.2 第二阶段：高级格式化

1. **AST 感知格式化**
   - 基于 AST 的格式化
   - 保留注释

2. **长行处理**
   - 智能换行
   - 表达式拆分

3. **检查模式**
   - diff 输出
   - CI 集成

### 3.3 第三阶段：编辑器集成

1. **VS Code 集成**
2. **Vim/Emacs 集成**
3. **LSP 格式化**

---

## 4. 测试策略

### 4.1 单元测试

```python
# tests/test_formatter.py

def test_basic_indentation():
    formatter = ZhCFormatter()
    source = """
函数 主函数()
变量 x = 10
如果 x > 0 则
打印行("正数")
结束
结束
"""
    expected = """
函数 主函数()
    变量 x = 10
    如果 x > 0 则
        打印行("正数")
    结束
结束
"""
    assert formatter.format(source) == expected

def test_multiline_function_signature():
    formatter = ZhCFormatter()
    source = """
函数 长函数(参数一: 整数, 参数二: 字符串, 参数三: 浮点数, 参数四: 布尔) -> 整数
    返回 0
结束
"""
    result = formatter.format(source)
    assert "参数一: 整数," in result
    assert "参数二: 字符串," in result
    assert "参数三: 浮点数," in result
    assert "参数四: 布尔" in result
```

### 4.2 集成测试

```bash
# 测试命令行
zhc fmt --check test_files/

# 测试配置文件
zhc fmt --config .zhcfmt.toml src/
```

---

## 5. 参考资料

- [gofmt](https://pkg.go.dev/cmd/gofmt)
- [rustfmt](https://github.com/rust-lang/rustfmt)
- [prettier](https://prettier.io/)
- [black](https://black.readthedocs.io/)

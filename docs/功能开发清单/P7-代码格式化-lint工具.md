# P7-代码格式化-代码风格检查 开发分析文档

## 基本信息

| 字段 | 内容 |
|------|------|
| **优先级** | P7 |
| **功能模块** | 代码格式化 |
| **功能名称** | lint 工具 |
| **文档版本** | 1.0.0 |
| **创建日期** | 2026-04-10 |
| **预计工时** | 约 2-3 周 |

---

## 1. 功能概述

`zhc lint` 是一个静态代码分析工具，用于检测 ZhC 代码中的潜在问题、风格违规和常见错误。

### 1.1 核心目标

- 检测代码风格问题
- 发现潜在错误
- 提供自动修复建议
- 支持自定义规则
- CI/CD 集成

### 1.2 检查类别

| 类别 | 描述 | 示例 |
|------|------|------|
| **错误** | 确定的问题 | 未使用的变量、类型错误 |
| **警告** | 潜在问题 | 未使用的导入、复杂条件 |
| **风格** | 代码风格 | 命名规范、缩进问题 |
| **复杂度** | 代码复杂度 | 过长函数、嵌套过深 |
| **安全** | 安全隐患 | 敏感信息泄露、不安全操作 |

---

## 2. 详细设计

### 2.1 命令行接口

```bash
# 基本用法
zhc lint [选项] [文件/目录...]

# 检查单个文件
zhc lint main.zhc

# 检查整个目录
zhc lint src/

# 指定规则
zhc lint --rules unused,complexity src/

# 自动修复
zhc lint --fix src/

# 输出格式
zhc lint --format json src/
zhc lint --format checkstyle src/
zhc lint --format github src/  # GitHub Actions 格式

# 配置文件
zhc lint --config .zhclint.toml src/

# 忽略规则
zhc lint --ignore unused-variable src/

# 严格模式（警告视为错误）
zhc lint --strict src/
```

### 2.2 配置文件

```toml
# .zhclint.toml

[general]
# 严格模式
strict = false
# 最大警告数
max_warnings = 100
# 最大错误数
max_errors = 50

[rules]
# 启用的规则
enabled = [
    "unused-variable",
    "unused-import",
    "naming-convention",
    "function-length",
    "cyclomatic-complexity",
]

# 禁用的规则
disabled = [
    "magic-number",
]

# 规则配置
[rules.config]
# 函数最大行数
function-max-lines = 50
# 圈复杂度阈值
cyclomatic-complexity = 10
# 最大嵌套深度
max-nesting-depth = 4
# 命名规范
naming-convention = "snake_case"  # "snake_case", "camelCase", "PascalCase"

[ignore]
# 忽略的文件模式
files = [
    "*.generated.zhc",
    "vendor/**",
]
# 忽略的目录
directories = [
    "node_modules",
    "dist",
]
```

### 2.3 内置规则

#### 2.3.1 未使用检查

| 规则 ID | 描述 | 严重性 |
|---------|------|--------|
| `unused-variable` | 未使用的变量 | 警告 |
| `unused-import` | 未使用的导入 | 警告 |
| `unused-parameter` | 未使用的参数 | 警告 |
| `unused-function` | 未使用的函数 | 警告 |
| `unused-struct` | 未使用的结构体 | 警告 |

#### 2.3.2 命名规范

| 规则 ID | 描述 | 严重性 |
|---------|------|--------|
| `naming-variable` | 变量命名规范 | 风格 |
| `naming-function` | 函数命名规范 | 风格 |
| `naming-struct` | 结构体命名规范 | 风格 |
| `naming-constant` | 常量命名规范 | 风格 |

#### 2.3.3 复杂度检查

| 规则 ID | 描述 | 严重性 |
|---------|------|--------|
| `function-length` | 函数过长 | 警告 |
| `cyclomatic-complexity` | 圈复杂度过高 | 警告 |
| `nesting-depth` | 嵌套过深 | 警告 |
| `parameter-count` | 参数过多 | 警告 |

#### 2.3.4 代码质量

| 规则 ID | 描述 | 严重性 |
|---------|------|--------|
| `magic-number` | 魔法数字 | 风格 |
| `duplicate-code` | 重复代码 | 警告 |
| `dead-code` | 死代码 | 错误 |
| `empty-block` | 空代码块 | 警告 |

#### 2.3.5 安全检查

| 规则 ID | 描述 | 严重性 |
|---------|------|--------|
| `hardcoded-secret` | 硬编码密钥 | 错误 |
| `unsafe-operation` | 不安全操作 | 警告 |
| `sql-injection` | SQL 注入风险 | 错误 |

### 2.4 核心实现

```python
# src/zhc/lint/linter.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum, auto
import re

class Severity(Enum):
    ERROR = auto()
    WARNING = auto()
    STYLE = auto()
    INFO = auto()

@dataclass
class Diagnostic:
    """诊断信息"""
    rule_id: str
    message: str
    severity: Severity
    file: str
    line: int
    column: int
    end_line: int
    end_column: int
    fix: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)

@dataclass
class LintConfig:
    """Lint 配置"""
    enabled_rules: Set[str] = field(default_factory=lambda: {
        "unused-variable",
        "unused-import",
        "naming-convention",
        "function-length",
        "cyclomatic-complexity",
    })
    disabled_rules: Set[str] = field(default_factory=set)
    rule_configs: Dict[str, dict] = field(default_factory=dict)
    strict: bool = False

class ZhCLinter:
    """ZhC 代码检查器"""

    def __init__(self, config: Optional[LintConfig] = None):
        self.config = config or LintConfig()
        self.rules = self._load_rules()
        self.diagnostics: List[Diagnostic] = []

    def lint(self, source: str, file_path: str) -> List[Diagnostic]:
        """检查源代码"""
        self.diagnostics = []

        # 1. 解析 AST
        try:
            ast = self._parse(source)
        except ParseError as e:
            self.diagnostics.append(Diagnostic(
                rule_id="parse-error",
                message=f"语法错误: {e.message}",
                severity=Severity.ERROR,
                file=file_path,
                line=e.line,
                column=e.column,
                end_line=e.line,
                end_column=e.column + e.length,
            ))
            return self.diagnostics

        # 2. 收集符号信息
        symbols = self._collect_symbols(ast)

        # 3. 运行规则检查
        for rule in self.rules:
            if rule.id in self.config.enabled_rules:
                rule.check(ast, symbols, self.diagnostics, file_path)

        # 4. 排序诊断信息
        self.diagnostics.sort(key=lambda d: (d.file, d.line, d.column))

        return self.diagnostics

    def _load_rules(self) -> List[LintRule]:
        """加载检查规则"""
        return [
            UnusedVariableRule(),
            UnusedImportRule(),
            NamingConventionRule(),
            FunctionLengthRule(),
            CyclomaticComplexityRule(),
            NestingDepthRule(),
            MagicNumberRule(),
            EmptyBlockRule(),
            HardcodedSecretRule(),
        ]


class LintRule:
    """检查规则基类"""

    id: str
    description: str
    default_severity: Severity

    def check(self, ast: ASTNode, symbols: SymbolTable,
              diagnostics: List[Diagnostic], file_path: str):
        """执行检查"""
        raise NotImplementedError


class UnusedVariableRule(LintRule):
    """未使用变量检查"""

    id = "unused-variable"
    description = "检测声明但未使用的变量"
    default_severity = Severity.WARNING

    def check(self, ast: ASTNode, symbols: SymbolTable,
              diagnostics: List[Diagnostic], file_path: str):
        for var in symbols.variables:
            if not var.is_used and not var.name.startswith("_"):
                diagnostics.append(Diagnostic(
                    rule_id=self.id,
                    message=f"变量 '{var.name}' 已声明但未使用",
                    severity=self.default_severity,
                    file=file_path,
                    line=var.line,
                    column=var.column,
                    end_line=var.line,
                    end_column=var.column + len(var.name),
                    fix=f"移除未使用的变量 '{var.name}'",
                ))


class NamingConventionRule(LintRule):
    """命名规范检查"""

    id = "naming-convention"
    description = "检查命名是否符合规范"
    default_severity = Severity.STYLE

    # 中文命名规范
    CHINESE_PATTERN = re.compile(r'^[\u4e00-\u9fa5][\u4e00-\u9fa5_a-zA-Z0-9]*$')
    SNAKE_CASE_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')
    CAMEL_CASE_PATTERN = re.compile(r'^[a-z][a-zA-Z0-9]*$')
    PASCAL_CASE_PATTERN = re.compile(r'^[A-Z][a-zA-Z0-9]*$')

    def check(self, ast: ASTNode, symbols: SymbolTable,
              diagnostics: List[Diagnostic], file_path: str):
        convention = self.config.get("naming-convention", "snake_case")

        for func in symbols.functions:
            if not self._is_valid_name(func.name, convention):
                diagnostics.append(Diagnostic(
                    rule_id=self.id,
                    message=f"函数名 '{func.name}' 不符合命名规范 ({convention})",
                    severity=self.default_severity,
                    file=file_path,
                    line=func.line,
                    column=func.column,
                    end_line=func.line,
                    end_column=func.column + len(func.name),
                    suggestions=[self._suggest_name(func.name, convention)],
                ))

    def _is_valid_name(self, name: str, convention: str) -> bool:
        """检查名称是否符合规范"""
        # 中文名称始终有效
        if self.CHINESE_PATTERN.match(name):
            return True

        patterns = {
            "snake_case": self.SNAKE_CASE_PATTERN,
            "camelCase": self.CAMEL_CASE_PATTERN,
            "PascalCase": self.PASCAL_CASE_PATTERN,
        }
        return patterns[convention].match(name) is not None


class FunctionLengthRule(LintRule):
    """函数长度检查"""

    id = "function-length"
    description = "检查函数是否过长"
    default_severity = Severity.WARNING

    def check(self, ast: ASTNode, symbols: SymbolTable,
              diagnostics: List[Diagnostic], file_path: str):
        max_lines = self.config.get("function-max-lines", 50)

        for func in symbols.functions:
            lines = func.end_line - func.start_line + 1
            if lines > max_lines:
                diagnostics.append(Diagnostic(
                    rule_id=self.id,
                    message=f"函数 '{func.name}' 过长 ({lines} 行，建议不超过 {max_lines} 行)",
                    severity=self.default_severity,
                    file=file_path,
                    line=func.start_line,
                    column=1,
                    end_line=func.end_line,
                    end_column=1,
                    fix="考虑将函数拆分为更小的函数",
                ))


class CyclomaticComplexityRule(LintRule):
    """圈复杂度检查"""

    id = "cyclomatic-complexity"
    description = "检查代码复杂度"
    default_severity = Severity.WARNING

    def check(self, ast: ASTNode, symbols: SymbolTable,
              diagnostics: List[Diagnostic], file_path: str):
        threshold = self.config.get("cyclomatic-complexity", 10)

        for func in symbols.functions:
            complexity = self._calculate_complexity(func.ast_node)
            if complexity > threshold:
                diagnostics.append(Diagnostic(
                    rule_id=self.id,
                    message=f"函数 '{func.name}' 圈复杂度过高 ({complexity}，建议不超过 {threshold})",
                    severity=self.default_severity,
                    file=file_path,
                    line=func.start_line,
                    column=1,
                    end_line=func.start_line,
                    end_column=len(func.name) + 1,
                    fix="考虑简化条件逻辑或拆分函数",
                ))

    def _calculate_complexity(self, node: ASTNode) -> int:
        """计算圈复杂度"""
        complexity = 1  # 基础复杂度

        for child in node.walk():
            if isinstance(child, IfStatement):
                complexity += 1
            elif isinstance(child, WhileStatement):
                complexity += 1
            elif isinstance(child, ForStatement):
                complexity += 1
            elif isinstance(child, BinaryExpr) and child.operator in ("&&", "||"):
                complexity += 1

        return complexity


class HardcodedSecretRule(LintRule):
    """硬编码密钥检查"""

    id = "hardcoded-secret"
    description = "检测硬编码的敏感信息"
    default_severity = Severity.ERROR

    SECRET_PATTERNS = [
        (re.compile(r'["\'](?:password|passwd|pwd)["\']\s*[:=]\s*["\'][^"\']+["\']', re.I), "密码"),
        (re.compile(r'["\'](?:api[_-]?key|apikey)["\']\s*[:=]\s*["\'][^"\']+["\']', re.I), "API 密钥"),
        (re.compile(r'["\'](?:secret|token)["\']\s*[:=]\s*["\'][^"\']+["\']', re.I), "密钥/令牌"),
    ]

    def check(self, ast: ASTNode, symbols: SymbolTable,
              diagnostics: List[Diagnostic], file_path: str):
        for node in ast.walk():
            if isinstance(node, StringLiteral):
                for pattern, name in self.SECRET_PATTERNS:
                    if pattern.search(node.value):
                        diagnostics.append(Diagnostic(
                            rule_id=self.id,
                            message=f"检测到硬编码的{name}，请使用环境变量或配置文件",
                            severity=self.default_severity,
                            file=file_path,
                            line=node.line,
                            column=node.column,
                            end_line=node.line,
                            end_column=node.column + len(node.value) + 2,
                            fix="将敏感信息移至环境变量或配置文件",
                        ))
```

### 2.5 输出格式

```python
# src/zhc/lint/output.py

class OutputFormatter:
    """输出格式化器"""

    @staticmethod
    def format_text(diagnostics: List[Diagnostic]) -> str:
        """文本格式"""
        lines = []
        for d in diagnostics:
            severity = d.severity.name
            lines.append(f"{d.file}:{d.line}:{d.column}: {severity}: {d.message} ({d.rule_id})")
        return "\n".join(lines)

    @staticmethod
    def format_json(diagnostics: List[Diagnostic]) -> str:
        """JSON 格式"""
        import json
        return json.dumps([{
            "ruleId": d.rule_id,
            "message": d.message,
            "severity": d.severity.name.lower(),
            "file": d.file,
            "line": d.line,
            "column": d.column,
            "endLine": d.end_line,
            "endColumn": d.end_column,
            "fix": d.fix,
        } for d in diagnostics], indent=2)

    @staticmethod
    def format_checkstyle(diagnostics: List[Diagnostic]) -> str:
        """Checkstyle XML 格式"""
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append('<checkstyle version="8.0">')

        # 按文件分组
        by_file = {}
        for d in diagnostics:
            if d.file not in by_file:
                by_file[d.file] = []
            by_file[d.file].append(d)

        for file, file_diags in by_file.items():
            lines.append(f'  <file name="{file}">')
            for d in file_diags:
                lines.append(f'    <error line="{d.line}" column="{d.column}" '
                           f'severity="{d.severity.name.lower()}" '
                           f'message="{d.message}" source="zhc.{d.rule_id}"/>')
            lines.append('  </file>')

        lines.append('</checkstyle>')
        return "\n".join(lines)

    @staticmethod
    def format_github(diagnostics: List[Diagnostic]) -> str:
        """GitHub Actions 格式"""
        lines = []
        for d in diagnostics:
            # GitHub Actions 注释格式
            lines.append(f"::{d.severity.name.lower()} file={d.file},line={d.line},"
                        f"col={d.column}::{d.message}")
        return "\n".join(lines)
```

---

## 3. 实现方案

### 3.1 第一阶段：基础检查

1. **规则框架**
   - 规则注册
   - 配置解析

2. **基础规则**
   - 未使用变量
   - 未使用导入
   - 命名规范

3. **命令行工具**
   - 文件扫描
   - 输出格式

### 3.2 第二阶段：高级检查

1. **复杂度分析**
   - 圈复杂度
   - 嵌套深度

2. **安全检查**
   - 敏感信息检测
   - 不安全操作

3. **自动修复**
   - 简单修复
   - 建议生成

### 3.3 第三阶段：集成

1. **CI/CD 集成**
2. **编辑器集成**
3. **Git hooks**

---

## 4. 参考资料

- [ESLint](https://eslint.org/)
- [pylint](https://pylint.org/)
- [golangci-lint](https://golangci-lint.run/)
- [Clippy](https://github.com/rust-lang/rust-clippy)

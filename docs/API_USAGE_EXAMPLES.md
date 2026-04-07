# ZHC 编译器公共 API 使用指南

本文档描述 ZHC 编译器的公共 API 接口，提供使用示例和最佳实践。

## 目录

1. [快速开始](#快速开始)
2. [核心 API](#核心-api)
3. [配置选项](#配置选项)
4. [编译流程](#编译流程)
5. [高级功能](#高级功能)
6. [API 设计问题与改进计划](#api-设计问题与改进计划)

---

## 快速开始

### 基本用法

```python
from pathlib import Path
from zhc.cli import ZHCCompiler, CompilerConfig

# 创建编译器实例
compiler = ZHCCompiler()

# 编译单个文件
success = compiler.compile_single_file(Path("hello.zhc"))
print(f"编译{'成功' if success else '失败'}")
```

### 带配置的编译

```python
from zhc.cli import ZHCCompiler, CompilerConfig

# 创建配置
config = CompilerConfig(
    verbose=True,           # 详细输出
    skip_semantic=False,    # 执行语义验证
    warning_level="all",    # 显示所有警告
    enable_cache=True,      # 启用缓存
)

# 使用配置创建编译器
compiler = ZHCCompiler(config=config)

# 编译文件
success = compiler.compile_single_file(
    input_file=Path("main.zhc"),
    output_dir=Path("build/")
)
```

---

## 核心 API

### ZHCCompiler 类

ZHCCompiler 是编译器的主入口类，负责协调整个编译流程。

#### 构造函数

```python
ZHCCompiler(config: Optional[CompilerConfig] = None)
```

**参数**:
- `config`: 编译器配置对象，如果为 None 则使用默认配置

#### 方法

##### compile_single_file

编译单个 .zhc 文件。

```python
def compile_single_file(
    self, 
    input_file: Path, 
    output_dir: Optional[Path] = None
) -> bool
```

**参数**:
- `input_file`: 输入的 .zhc 文件路径
- `output_dir`: 输出目录（None 则输出到同目录）

**返回**: 编译是否成功 (bool)

**示例**:
```python
from pathlib import Path
from zhc.cli import ZHCCompiler

compiler = ZHCCompiler()

# 编译到同目录
success = compiler.compile_single_file(Path("hello.zhc"))

# 编译到指定目录
success = compiler.compile_single_file(
    Path("hello.zhc"), 
    Path("output/")
)
```

##### compile_module_project

编译模块项目（多文件）。

```python
def compile_module_project(
    self, 
    input_file: Path, 
    output_dir: Optional[Path] = None
) -> bool
```

**参数**:
- `input_file`: 项目入口文件
- `output_dir`: 输出目录

**返回**: 编译是否成功 (bool)

**示例**:
```python
from pathlib import Path
from zhc.cli import ZHCCompiler

compiler = ZHCCompiler()
success = compiler.compile_module_project(Path("main.zhc"))
```

##### clean_cache

清理编译缓存。

```python
def clean_cache(self) -> None
```

**示例**:
```python
compiler = ZHCCompiler()
compiler.clean_cache()
print("缓存已清理")
```

##### show_stats

显示编译统计信息。

```python
def show_stats(self) -> None
```

**示例**:
```python
compiler = ZHCCompiler()
compiler.compile_single_file(Path("main.zhc"))
compiler.show_stats()
```

**输出示例**:
```
📊 编译统计:
  文件数: 1
  总行数: 42
  耗时: 0.15秒
```

---

### CompilerConfig 类

编译器配置类，用于自定义编译行为。

#### 构造函数

```python
CompilerConfig(
    verbose: bool = False,
    use_ast: bool = True,
    skip_semantic: bool = False,
    warning_level: str = "normal",
    no_uninit: bool = False,
    no_unreachable: bool = False,
    no_dataflow: bool = False,
    no_interprocedural: bool = False,
    no_alias: bool = False,
    no_pointer: bool = False,
    optimize_symbol_lookup: bool = False,
    profile: bool = False,
    backend: str = "ast",
    dump_ir: bool = False,
    optimize_ir: bool = True,
    enable_cache: bool = True,
)
```

#### 配置参数详解

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `verbose` | bool | False | 启用详细输出 |
| `use_ast` | bool | True | 使用 AST 编译路径 |
| `skip_semantic` | bool | False | 跳过语义验证 |
| `warning_level` | str | "normal" | 警告级别: none/normal/all/error |
| `no_uninit` | bool | False | 禁用未初始化变量检查 |
| `no_unreachable` | bool | False | 禁用不可达代码检测 |
| `no_dataflow` | bool | False | 禁用数据流分析 |
| `no_interprocedural` | bool | False | 禁用过程间分析 |
| `no_alias` | bool | False | 禁用别名分析 |
| `no_pointer` | bool | False | 禁用指针分析 |
| `optimize_symbol_lookup` | bool | False | 启用符号查找优化器 |
| `profile` | bool | False | 启用性能分析 |
| `backend` | str | "ast" | 代码生成后端: ast/ir |
| `dump_ir` | bool | False | 输出 IR 中间表示 |
| `optimize_ir` | bool | True | 启用 IR 优化 |
| `enable_cache` | bool | True | 启用编译缓存 |

#### 工厂方法

```python
@classmethod
def from_args(cls, args: argparse.Namespace) -> "CompilerConfig"
```

从命令行参数创建配置。

**示例**:
```python
import argparse
from zhc.cli import CompilerConfig

# 模拟命令行参数
parser = argparse.ArgumentParser()
parser.add_argument("--verbose", action="store_true")
parser.add_argument("--skip-semantic", action="store_true")
# ... 其他参数

args = parser.parse_args(["--verbose"])
config = CompilerConfig.from_args(args)
```

---

## 编译流程

### 单文件编译流程

```
源代码 (.zhc)
    ↓
词法分析 (Lexer)
    ↓
语法分析 (Parser) → AST
    ↓
语义验证 (SemanticAnalyzer)
    ↓
代码生成 (CCodeGenerator)
    ↓
输出文件 (.c)
```

### 模块项目编译流程

```
项目入口 (.zhc)
    ↓
解析所有模块文件
    ↓
构建依赖图 (DependencyResolver)
    ↓
检测循环依赖
    ↓
计算编译顺序 (拓扑排序)
    ↓
依次编译各模块
    ↓
生成 Makefile
    ↓
生成编译报告
```

---

## 高级功能

### 1. 编译缓存

启用缓存可以加速重复编译：

```python
config = CompilerConfig(enable_cache=True)
compiler = ZHCCompiler(config=config)

# 第一次编译
compiler.compile_single_file(Path("main.zhc"))

# 第二次编译（使用缓存）
compiler.compile_single_file(Path("main.zhc"))
```

### 2. 增量编译

使用 CompilationPipeline 进行增量编译：

```python
from zhc.compiler.pipeline import CompilationPipeline

pipeline = CompilationPipeline(enable_cache=True)

# 增量编译
success = pipeline.incremental_compile(
    source_files=["main.zhc", "utils.zhc"],
    output_name="app"
)
```

### 3. 性能分析

启用性能分析可以查看各编译阶段耗时：

```python
config = CompilerConfig(profile=True)
compiler = ZHCCompiler(config=config)
compiler.compile_single_file(Path("main.zhc"))
```

### 4. IR 中间表示

使用 IR 后端进行代码生成：

```python
config = CompilerConfig(
    backend="ir",
    dump_ir=True,      # 输出 IR
    optimize_ir=True,  # 启用 IR 优化
)
compiler = ZHCCompiler(config=config)
compiler.compile_single_file(Path("main.zhc"))
```

---

## API 设计问题与改进计划

### 当前问题

#### 1. 返回值不统一

**问题**: 所有编译方法都返回 `bool`，无法获取详细编译结果。

```python
# 当前
success = compiler.compile_single_file(Path("main.zhc"))
# 只知道成功/失败，不知道生成了什么文件、有多少警告等
```

**改进方案**: 创建 `CompilationResult` 数据类。

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CompilationResult:
    """编译结果"""
    success: bool
    output_files: List[Path]
    errors: List[str]
    warnings: List[str]
    stats: Dict[str, Any]
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0
```

#### 2. 配置参数过多

**问题**: `CompilerConfig` 和 `CompilationPipeline` 构造函数参数过多（14-16个）。

**改进方案**: 使用配置分组和 builder 模式。

```python
from dataclasses import dataclass, field

@dataclass
class SemanticConfig:
    """语义分析配置"""
    enabled: bool = True
    check_uninit: bool = True
    check_unreachable: bool = True
    check_dataflow: bool = True
    check_interprocedural: bool = True
    check_alias: bool = True
    check_pointer: bool = True

@dataclass
class CompilerConfig:
    """编译器配置"""
    verbose: bool = False
    warning_level: str = "normal"
    enable_cache: bool = True
    semantic: SemanticConfig = field(default_factory=SemanticConfig)
    # ...
```

#### 3. 类型注解不完整

**问题**: 部分方法缺少完整的类型注解。

**改进方案**: 添加完整的类型注解。

```python
def compile_single_file(
    self, 
    input_file: Path, 
    output_dir: Optional[Path] = None
) -> CompilationResult:  # 改进后的返回类型
    ...
```

#### 4. 统计信息类型不安全

**问题**: `self.stats` 使用 Dict，无法保证类型安全。

**改进方案**: 使用 dataclass。

```python
@dataclass
class CompilationStats:
    """编译统计"""
    files_processed: int = 0
    total_lines: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    start_time: float = field(default_factory=time.time)
    
    @property
    def elapsed_time(self) -> float:
        return time.time() - self.start_time
```

### 改进计划

| 阶段 | 任务 | 优先级 |
|------|------|--------|
| Phase 1 | 创建 `CompilationResult` 数据类 | P0 |
| Phase 2 | 创建 `CompilationStats` 数据类 | P0 |
| Phase 3 | 重构 `CompilerConfig` 使用配置分组 | P1 |
| Phase 4 | 更新所有方法的返回类型 | P1 |
| Phase 5 | 添加完整的类型注解 | P2 |
| Phase 6 | 编写单元测试验证 API | P2 |

---

## 常见问题

### Q: 如何禁用语义验证？

```python
config = CompilerConfig(skip_semantic=True)
compiler = ZHCCompiler(config=config)
```

### Q: 如何启用详细输出？

```python
config = CompilerConfig(verbose=True)
compiler = ZHCCompiler(config=config)
```

### Q: 如何清理缓存？

```python
compiler = ZHCCompiler()
compiler.clean_cache()
```

### Q: 如何查看编译统计？

```python
config = CompilerConfig(verbose=True)
compiler = ZHCCompiler(config=config)
compiler.compile_single_file(Path("main.zhc"))
compiler.show_stats()
```

---

## 附录

### 完整示例

```python
#!/usr/bin/env python3
"""ZHC 编译器使用示例"""

from pathlib import Path
from zhc.cli import ZHCCompiler, CompilerConfig

def main():
    # 创建配置
    config = CompilerConfig(
        verbose=True,
        warning_level="all",
        enable_cache=True,
        profile=True,
    )
    
    # 创建编译器
    compiler = ZHCCompiler(config=config)
    
    # 编译单文件
    input_file = Path("hello.zhc")
    if not input_file.exists():
        print(f"文件不存在: {input_file}")
        return 1
    
    success = compiler.compile_single_file(input_file)
    
    # 显示统计
    compiler.show_stats()
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
```

---

*文档版本: 1.0*  
*最后更新: 2026-04-07*

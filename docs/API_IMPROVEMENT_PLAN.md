# ZHC 编译器 API 设计改进方案

**文档版本**: 1.0  
**创建日期**: 2026-04-07  
**作者**: 远  
**状态**: Task 5.3 进行中

---

## 目录

1. [当前 API 分析](#当前-api-分析)
2. [设计问题清单](#设计问题清单)
3. [改进方案](#改进方案)
4. [实施计划](#实施计划)
5. [风险评估](#风险评估)

---

## 当前 API 分析

### 核心 API 类

#### 1. ZHCCompiler (src/cli.py)

**职责**: 编译器主入口，协调编译流程

**公共方法**:
- `compile_single_file(input_file, output_dir) -> bool`
- `compile_module_project(input_file, output_dir) -> bool`
- `clean_cache() -> None`
- `show_stats() -> None`

**私有方法**:
- `_parse_source(content, input_file)`
- `_run_semantic_check(ast, input_file) -> bool`
- `_generate_code(ast)`
- `_resolve_output_path(input_file, output_dir) -> Path`

**内部状态**:
- `config: CompilerConfig`
- `cache: CompilationCache`
- `pipeline: CompilationPipeline`
- `performance_monitor: PerformanceMonitor`
- `stats: Dict[str, Any]`

#### 2. CompilerConfig (src/cli.py)

**职责**: 编译器配置管理

**构造函数参数** (14个):
```python
def __init__(
    self,
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

**工厂方法**:
- `from_args(args: argparse.Namespace) -> CompilerConfig`

#### 3. CompilationPipeline (src/compiler/pipeline.py)

**职责**: 集成编译流水线

**构造函数参数** (11个):
```python
def __init__(
    self,
    cache_dir: str = ".zhc_cache",
    enable_cache: bool = True,
    skip_semantic: bool = False,
    warning_level: str = 'normal',
    no_uninit: bool = False,
    no_unreachable: bool = False,
    no_dataflow: bool = False,
    no_interprocedural: bool = False,
    no_alias: bool = False,
    no_pointer: bool = False,
    optimize_symbol_lookup: bool = False,
)
```

**公共方法**:
- `process_file(filepath, is_main) -> Optional[Dict[str, Any]]`
- `compile_project(source_files, output_name) -> bool`
- `incremental_compile(source_files, output_name) -> bool`

**内部状态**:
- `stats: Dict[str, Any]`
- `file_hash_cache: Dict[str, str]`
- `compilation_cache: Dict[str, Any]`

---

## 设计问题清单

### P0 - 高优先级问题

#### 问题 1: 返回值不统一，缺少详细信息

**现状**:
```python
success = compiler.compile_single_file(Path("main.zhc"))
# 只返回 bool，无法获取：
# - 生成的文件路径
# - 错误/警告详情
# - 编译统计
# - 性能数据
```

**影响**:
- 用户无法获取编译结果详情
- 无法进行错误处理和报告
- 无法集成到其他工具链

**评分**: 严重性 9/10，影响面 8/10

#### 问题 2: 统计信息类型不安全

**现状**:
```python
self.stats = {
    'files_processed': 0,
    'total_lines': 0,
    'cache_hits': 0,
    'cache_misses': 0,
    'start_time': time.time(),
}
```

**影响**:
- 无法保证类型安全
- 无法添加计算属性
- 无法进行类型检查

**评分**: 严重性 7/10，影响面 6/10

#### 问题 3: 配置参数过多

**现状**:
- `CompilerConfig.__init__`: 14 个参数
- `CompilationPipeline.__init__`: 11 个参数

**影响**:
- 构造函数调用复杂
- 参数顺序容易出错
- 难以扩展新配置

**评分**: 严重性 8/10，影响面 7/10

### P1 - 中优先级问题

#### 问题 4: 类型注解不完整

**现状**:
```python
def _parse_source(self, content: str, input_file: Path):
    # 返回类型未标注
    return parse_source(content)

def _generate_code(self, ast):
    # 参数类型未标注
    # 返回类型未标注
    ...
```

**影响**:
- IDE 无法提供类型提示
- 无法进行静态类型检查
- 文档不完整

**评分**: 严重性 6/10，影响面 8/10

#### 问题 5: 配置参数重复

**现状**:
- `CompilerConfig` 和 `CompilationPipeline` 有相同的参数：
  - `skip_semantic`
  - `warning_level`
  - `no_uninit`, `no_unreachable`, `no_dataflow`, ...
  - `optimize_symbol_lookup`

**影响**:
- 参数传递冗余
- 维护成本高
- 容易出现不一致

**评分**: 严重性 6/10，影响面 5/10

#### 问题 6: 缺少配置验证

**现状**:
```python
config = CompilerConfig(warning_level="invalid")  # 无验证
config = CompilerConfig(backend="unknown")        # 无验证
```

**影响**:
- 无效配置可能导致运行时错误
- 无法提前发现问题

**评分**: 严重性 5/10，影响面 4/10

### P2 - 低优先级问题

#### 问题 7: 缺少 API 文档字符串

**现状**:
- 部分方法缺少文档字符串
- 参数说明不完整
- 返回值说明不完整

**影响**:
- IDE 无法显示完整文档
- 用户难以理解 API

**评分**: 严重性 4/10，影响面 6/10

#### 问题 8: 缺少错误处理机制

**现状**:
```python
def compile_single_file(self, input_file: Path, ...) -> bool:
    try:
        ...
    except Exception as e:
        self._handle_compile_error(e, input_file)
        return False
```

**影响**:
- 异常信息丢失
- 无法区分错误类型
- 无法进行精确错误处理

**评分**: 严重性 5/10，影响面 3/10

---

## 改进方案

### 方案 1: 创建 CompilationResult 数据类

**目标**: 统一编译结果返回值

**设计**:
```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

@dataclass
class CompilationResult:
    """编译结果数据类
    
    包含编译的完整结果信息，包括成功状态、输出文件、错误、警告和统计。
    """
    
    # 基本信息
    success: bool
    input_file: Path
    
    # 输出信息
    output_files: List[Path] = field(default_factory=list)
    
    # 错误和警告
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # 统计信息
    stats: Dict[str, Any] = field(default_factory=dict)
    
    # 性能数据
    elapsed_time: float = 0.0
    
    @property
    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0
    
    @property
    def error_count(self) -> int:
        """错误数量"""
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        """警告数量"""
        return len(self.warnings)
    
    def summary(self) -> str:
        """生成摘要字符串"""
        status = "✅ 成功" if self.success else "❌ 失败"
        parts = [
            f"{status}: {self.input_file}",
            f"输出: {len(self.output_files)} 个文件",
            f"错误: {self.error_count}",
            f"警告: {self.warning_count}",
            f"耗时: {self.elapsed_time:.2f}s",
        ]
        return "\n".join(parts)
```

**使用示例**:
```python
result = compiler.compile_single_file(Path("main.zhc"))

if result.success:
    print(f"编译成功，输出文件: {result.output_files}")
else:
    print(f"编译失败，错误: {result.errors}")

print(result.summary())
```

**实施步骤**:
1. 创建 `src/api/result.py` 文件
2. 定义 `CompilationResult` 数据类
3. 更新 `ZHCCompiler.compile_single_file()` 返回类型
4. 更新 `CompilationPipeline.process_file()` 返回类型
5. 编写单元测试

### 方案 2: 创建 CompilationStats 数据类

**目标**: 类型安全的统计信息

**设计**:
```python
from dataclasses import dataclass, field
import time

@dataclass
class CompilationStats:
    """编译统计数据类
    
    类型安全的编译统计信息，包含计算属性。
    """
    
    # 文件统计
    files_processed: int = 0
    total_lines: int = 0
    
    # 缓存统计
    cache_hits: int = 0
    cache_misses: int = 0
    
    # 时间统计
    start_time: float = field(default_factory=time.time)
    
    # 解析统计
    parsed_files: int = 0
    converted_files: int = 0
    dependency_analyzed: int = 0
    
    @property
    def elapsed_time(self) -> float:
        """已用时间（秒）"""
        return time.time() - self.start_time
    
    @property
    def cache_hit_rate(self) -> float:
        """缓存命中率（百分比）"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return (self.cache_hits / total) * 100
    
    @property
    def avg_lines_per_file(self) -> float:
        """平均每文件行数"""
        if self.files_processed == 0:
            return 0.0
        return self.total_lines / self.files_processed
    
    @property
    def files_per_second(self) -> float:
        """文件处理吞吐量"""
        if self.elapsed_time == 0:
            return 0.0
        return self.files_processed / self.elapsed_time
    
    def reset(self) -> None:
        """重置统计"""
        self.files_processed = 0
        self.total_lines = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.parsed_files = 0
        self.converted_files = 0
        self.dependency_analyzed = 0
        self.start_time = time.time()
    
    def summary(self) -> str:
        """生成统计摘要"""
        return f"""
📊 编译统计:
  文件数: {self.files_processed}
  总行数: {self.total_lines}
  缓存命中率: {self.cache_hit_rate:.1f}%
  平均行数/文件: {self.avg_lines_per_file:.1f}
  处理速度: {self.files_per_second:.2f} 文件/秒
  耗时: {self.elapsed_time:.2f}秒
"""
```

**实施步骤**:
1. 创建 `src/api/stats.py` 文件
2. 定义 `CompilationStats` 数据类
3. 更新 `ZHCCompiler.stats` 类型
4. 更新 `CompilationPipeline.stats` 类型
5. 编写单元测试

### 方案 3: 重构 CompilerConfig 使用配置分组

**目标**: 减少构造函数参数，提高可维护性

**设计**:
```python
from dataclasses import dataclass, field
from typing import Literal

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
    optimize_symbol_lookup: bool = False

@dataclass
class OutputConfig:
    """输出配置"""
    verbose: bool = False
    warning_level: Literal["none", "normal", "all", "error"] = "normal"
    backend: Literal["ast", "ir"] = "ast"
    dump_ir: bool = False
    optimize_ir: bool = True

@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    cache_dir: str = ".zhc_cache"
    max_size_mb: int = 100

@dataclass
class ProfileConfig:
    """性能分析配置"""
    enabled: bool = False
    measure_codegen: bool = True
    measure_semantic: bool = True

@dataclass
class CompilerConfig:
    """编译器配置（重构版）
    
    使用配置分组，减少构造函数参数，提高可维护性。
    """
    
    # 输出配置
    output: OutputConfig = field(default_factory=OutputConfig)
    
    # 语义分析配置
    semantic: SemanticConfig = field(default_factory=SemanticConfig)
    
    # 缓存配置
    cache: CacheConfig = field(default_factory=CacheConfig)
    
    # 性能分析配置
    profile: ProfileConfig = field(default_factory=ProfileConfig)
    
    # 兼容性属性（保持向后兼容）
    @property
    def verbose(self) -> bool:
        return self.output.verbose
    
    @property
    def warning_level(self) -> str:
        return self.output.warning_level
    
    @property
    def skip_semantic(self) -> bool:
        return not self.semantic.enabled
    
    @property
    def enable_cache(self) -> bool:
        return self.cache.enabled
    
    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "CompilerConfig":
        """从命令行参数创建配置"""
        return cls(
            output=OutputConfig(
                verbose=args.verbose,
                warning_level=args.warning_level,
            ),
            semantic=SemanticConfig(
                enabled=not args.skip_semantic,
                check_uninit=not args.no_uninit,
                check_unreachable=not args.no_unreachable,
                check_dataflow=not args.no_dataflow,
                check_interprocedural=not args.no_interprocedural,
                check_alias=not args.no_alias,
                check_pointer=not args.no_pointer,
                optimize_symbol_lookup=args.optimize_symbol_lookup,
            ),
            cache=CacheConfig(
                enabled=True,  # 默认启用
            ),
            profile=ProfileConfig(
                enabled=args.profile,
            ),
        )
```

**使用示例**:
```python
# 新方式（推荐）
config = CompilerConfig(
    output=OutputConfig(verbose=True, warning_level="all"),
    semantic=SemanticConfig(enabled=True, check_uninit=False),
)

# 旧方式（向后兼容）
config = CompilerConfig()
config.verbose = True  # 通过兼容性属性访问
```

**实施步骤**:
1. 创建 `src/api/config.py` 文件
2. 定义配置分组数据类
3. 重构 `CompilerConfig`
4. 更新 `ZHCCompiler` 使用新配置
5. 保持向后兼容性
6. 编写单元测试

### 方案 4: 添加完整类型注解

**目标**: 提高类型安全性，改善 IDE 支持

**设计**:
```python
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

class ZHCCompiler:
    """中文C编译器主类"""
    
    def __init__(self, config: Optional[CompilerConfig] = None) -> None:
        ...
    
    def compile_single_file(
        self, 
        input_file: Path, 
        output_dir: Optional[Path] = None
    ) -> CompilationResult:
        ...
    
    def compile_module_project(
        self, 
        input_file: Path, 
        output_dir: Optional[Path] = None
    ) -> CompilationResult:
        ...
    
    def clean_cache(self) -> None:
        ...
    
    def show_stats(self) -> CompilationStats:
        ...
    
    # 私有方法
    def _parse_source(
        self, 
        content: str, 
        input_file: Path
    ) -> Tuple[Any, List[str]]:
        """返回 (ast, errors)"""
        ...
    
    def _run_semantic_check(
        self, 
        ast: Any, 
        input_file: Path
    ) -> Tuple[bool, List[str], List[str]]:
        """返回 (success, errors, warnings)"""
        ...
    
    def _generate_code(
        self, 
        ast: Any
    ) -> Optional[str]:
        """返回 C 代码字符串或 None"""
        ...
```

**实施步骤**:
1. 为所有公共方法添加类型注解
2. 为所有私有方法添加类型注解
3. 使用 `typing` 模块的类型
4. 运行 mypy 类型检查
5. 修复类型错误

### 方案 5: 创建 API 模块

**目标**: 统一 API 导入路径

**设计**:
```
src/api/
├── __init__.py          # 统一导出
├── result.py            # CompilationResult
├── stats.py             # CompilationStats
├── config.py            # CompilerConfig + 配置分组
├── compiler.py          # ZHCCompiler（可选迁移）
└── exceptions.py        # 自定义异常类
```

**`src/api/__init__.py`**:
```python
"""ZHC 编译器公共 API"""

from .result import CompilationResult
from .stats import CompilationStats
from .config import (
    CompilerConfig,
    SemanticConfig,
    OutputConfig,
    CacheConfig,
    ProfileConfig,
)

# 可选：迁移 ZHCCompiler
# from .compiler import ZHCCompiler

__all__ = [
    "CompilationResult",
    "CompilationStats",
    "CompilerConfig",
    "SemanticConfig",
    "OutputConfig",
    "CacheConfig",
    "ProfileConfig",
]
```

**使用示例**:
```python
# 新导入方式
from zhc.api import CompilationResult, CompilerConfig

# 旧导入方式（保持兼容）
from zhc.cli import ZHCCompiler, CompilerConfig
```

---

## 实施计划

### Phase 1: 创建数据类 (P0)

**时间**: 2-3 天

**任务**:
1. 创建 `src/api/result.py` - CompilationResult
2. 创建 `src/api/stats.py` - CompilationStats
3. 编写单元测试
4. 验证类型安全

**验收标准**:
- 所有数据类通过单元测试
- mypy 类型检查通过
- 文档字符串完整

### Phase 2: 重构配置 (P1)

**时间**: 3-4 天

**任务**:
1. 创建 `src/api/config.py` - 配置分组
2. 重构 `CompilerConfig`
3. 保持向后兼容性
4. 更新 `ZHCCompiler` 使用新配置
5. 编写单元测试

**验收标准**:
- 新配置 API 可用
- 旧 API 保持兼容
- 所有测试通过

### Phase 3: 更新返回类型 (P1)

**时间**: 2-3 天

**任务**:
1. 更新 `compile_single_file()` 返回 CompilationResult
2. 更新 `compile_module_project()` 返回 CompilationResult
3. 更新 `show_stats()` 返回 CompilationStats
4. 更新 `CompilationPipeline` 方法
5. 编写单元测试

**验收标准**:
- 所有编译方法返回 CompilationResult
- 类型注解完整
- 测试覆盖率 > 80%

### Phase 4: 添加类型注解 (P2)

**时间**: 2-3 天

**任务**:
1. 为所有公共方法添加类型注解
2. 为所有私有方法添加类型注解
3. 运行 mypy 类型检查
4. 修复类型错误
5. 添加类型注解测试

**验收标准**:
- mypy 类型检查通过
- 所有方法有类型注解
- 类型覆盖率 > 90%

### Phase 5: 创建 API 模块 (P2)

**时间**: 1-2 天

**任务**:
1. 创建 `src/api/` 目录
2. 创建 `__init__.py` 统一导出
3. 创建 `exceptions.py` 自定义异常
4. 更新文档
5. 编写使用示例

**验收标准**:
- API 模块可用
- 导入路径统一
- 文档完整

---

## 风险评估

### 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 向后兼容性破坏 | 高 | 中 | 保持旧 API，添加兼容性属性 |
| 类型注解错误 | 中 | 低 | 使用 mypy 检查，编写测试 |
| 性能下降 | 低 | 低 | 使用 dataclass，性能测试 |
| 测试覆盖不足 | 中 | 中 | 编写完整单元测试 |

### 进度风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 时间估算不准 | 中 | 中 | 分阶段实施，及时调整 |
| 依赖模块未完成 | 低 | 低 | 先完成数据类，再更新方法 |
| 文档更新滞后 | 低 | 中 | 同步更新文档 |

---

## 附录

### A. 当前 API 复杂度分析

| 类/方法 | 参数数量 | 返回类型 | 复杂度评分 |
|---------|----------|----------|------------|
| `CompilerConfig.__init__` | 14 | None | 8/10 |
| `CompilationPipeline.__init__` | 11 | None | 7/10 |
| `compile_single_file` | 2 | bool | 3/10 |
| `compile_module_project` | 2 | bool | 3/10 |
| `process_file` | 2 | Dict | 5/10 |

### B. 改进后 API 复杂度预期

| 类/方法 | 参数数量 | 返回类型 | 复杂度评分 |
|---------|----------|----------|------------|
| `CompilerConfig.__init__` | 4 | None | 3/10 |
| `CompilationPipeline.__init__` | 4 | None | 3/10 |
| `compile_single_file` | 2 | CompilationResult | 2/10 |
| `compile_module_project` | 2 | CompilationResult | 2/10 |
| `process_file` | 2 | CompilationResult | 2/10 |

### C. 参考资源

- Python dataclasses: https://docs.python.org/3/library/dataclasses.html
- Type hints: https://docs.python.org/3/library/typing.html
- mypy: https://mypy.readthedocs.io/

---

*文档版本: 1.0*  
*最后更新: 2026-04-07*
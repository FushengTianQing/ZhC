# Phase 7: IR 中间表示与代码优化 — 执行计划 v3.0

> 版本：v3.0（基于代码库实测修正）
> 创建时间：2026-04-03
> 修正基线：v2.0 文档 + 代码库实测
> 项目路径：`/Users/yuan/Projects/zhc/`

---

## 现状澄清（v3.0 修正）

### Symbol 体系只有两套，不是三套

| 体系 | 文件 | 用途 | IR 统一相关 |
|------|------|------|------------|
| **第一套** | `semantic/semantic_analyzer.py` | 主语义分析器，在用 | ✅ 相关 |
| **第二套** | `analyzer/scope_checker.py` | 独立作用域检查，`analyzer/__init__.py` 已标注"已废弃" | ✅ 相关 |
| **parser 内部** | `parser/scope.py` | 纯语法分析阶段用，专注模块可见性（public/private/protected）和限定名 | ❌ 无关 |

**结论**：IR Symbol 统一只需要处理前两套。parser/scope.py 是 parser 自己用的，IR 层不依赖它。

---

## 待修复的真实 Bug（必须 M0 阶段修复）

### Bug 1：`semantic_analyzer.py` 第 669-688 行死代码

**位置**：`src/semantic/semantic_analyzer.py`

**问题**：`_analyze_identifier_expr` 方法内有一段永远执行不到的重复代码（第 669-688 行），原因是第 651 行已有 `return`，但后面又重复了 `if not symbol:` 检查和后续逻辑。这段死代码在每次分析标识符时都会被"执行"前的检查拦截。

**修复**：删除第 669-688 行的重复代码。

### Bug 2：`semantic_analyzer.py` 第 281 行 AttributeError

**位置**：`src/semantic/semantic_analyzer.py` 第 281 行

**问题**：
- `__init__` 第 253 行有 `self.symbol_lookup_enabled = False`
- 但没有 `self._symbol_lookup_optimizer = None`
- 第 281 行 `if self._symbol_lookup_optimizer is None` 会抛 `AttributeError`

**修复**：在 `__init__` 中添加 `self._symbol_lookup_optimizer = None`（紧跟在 `self.symbol_lookup_enabled = False` 之后）。

---

## 里程碑总览

| 里程碑 | 名称 | 核心交付 | 依赖 |
|---------|------|---------|------|
| **M0** | Symbol 体系统一 + Bug 修复 | 统一的 `ir/symbol.py` + 2 个 bug 修复 | 无 |
| **M1** | ZHC IR 定义 | 35+ 操作码 + IR 数据结构 | M0 |
| **M2** | AST → IR 生成器 | 42 个 visit 方法 | M1 |
| **M3** | IR → C 后端 + 映射表提取 | `ir/mappings.py` + `ir/c_backend.py` | M1 |
| **M4** | IR 验证器 | 7 项合法性检查 | M1 |
| **M5** | IR 优化 Pass | 常量折叠 + 死代码消除 | M2+M3 |
| **M6** | Pipeline 集成 + CLI | `--backend ir/ast` + `--dump-ir` 等 | M2-M5 |
| **M7** | 测试 + 文档 + 清理 | 153+ 新测试 + 技术债务清理 | M0-M6 |

**推荐顺序**：M0 → M1 → M4 → M2 → M3 → M5 → M6 → M7

---

## M0：Symbol 体系统一 + Bug 修复

### M0.1：创建 `src/ir/` 包

创建以下文件：

```
src/ir/
├── __init__.py          # 导出 Symbol, Scope, ScopeType, SymbolCategory, ZHCTy
├── symbol.py            # 统一 Symbol + Scope + SymbolCategory + ScopeType
└── types.py            # ZHCTy = TypeInfo 别名
```

**注意**：本步骤**不创建** `mappings.py`、`opcodes.py`、`ir_generator.py` 等 M1+ 文件，避免与后续里程碑冲突。

---

### M0.2：定义统一 Symbol 类（`ir/symbol.py`）

**设计**：
- 以 `semantic/semantic_analyzer.py` 的 Symbol 为基础（功能最全）
- 合并 `scope_checker.py` 的 `SymbolCategory` 枚举
- 保留 `semantic Symbol` 的所有字段（parameters/members/return_type 等）
- 提供 `symbol_type` 属性兼容 scope_checker 的 `category` 字段

```python
from enum import Enum

class SymbolCategory(Enum):
    VARIABLE = "variable"
    FUNCTION = "function"
    PARAMETER = "parameter"
    TYPEDEF = "typedef"
    STRUCT = "struct"
    MODULE = "module"
    LABEL = "label"

class ScopeType(Enum):
    GLOBAL = "全局"
    MODULE = "模块"
    STRUCT = "结构体"
    FUNCTION = "函数"
    BLOCK = "代码块"
    LOOP = "循环"

@dataclass
class Symbol:
    name: str
    symbol_type: str           # "变量"/"函数"/"参数"等（中文）
    data_type: Optional[str]   # 中文类型名
    # ... 其他字段参考 semantic/Symbol
```

---

### M0.3：定义统一 Scope 类（`ir/symbol.py`）

```python
@dataclass
class Scope:
    scope_type: ScopeType
    scope_name: str
    parent: Optional['Scope']
    symbols: Dict[str, Symbol]
    level: int
    children: List['Scope'] = field(default_factory=list)

    def add_symbol(self, symbol: Symbol) -> bool: ...
    def lookup(self, name: str) -> Optional[Symbol]: ...
    def lookup_local(self, name: str) -> Optional[Symbol]: ...
```

---

### M0.4：定义 `ZHCTy` 类型别名（`ir/types.py`）

```python
# ir/types.py
# TypeInfo 的别名，供 IR 层使用
from ..analyzer.type_checker import TypeInfo as ZHCTy
```

**原则**：`TypeInfo` 定义保留在 `analyzer/type_checker.py` 不动，`ir/types.py` 仅做别名引入，避免迁移风险。

---

### M0.5：修复 Bug 1 — 删除死代码

**文件**：`src/semantic/semantic_analyzer.py`

删除 `_analyze_identifier_expr` 方法内第 669-688 行的重复代码（整块删除）。

---

### M0.6：修复 Bug 2 — 初始化 `_symbol_lookup_optimizer`

**文件**：`src/semantic/semantic_analyzer.py`

在 `__init__` 的 `self.symbol_lookup_enabled = False` 之后添加：

```python
self._symbol_lookup_optimizer = None  # 延迟初始化，bug 修复
```

---

### M0.7：建立兼容层

**文件**：`semantic/__init__.py` 和 `analyzer/__init__.py`

添加兼容别名，使现有代码可渐进迁移：

```python
# semantic/__init__.py
from .semantic_analyzer import Symbol as LegacySymbol, Scope as LegacyScope
# 新的统一 Symbol/Scope 从 ir.symbol 导入
from ..ir.symbol import Symbol, Scope, ScopeType, SymbolCategory
```

```python
# analyzer/__init__.py
# 原有导出保持不变（向后兼容）
# 新增别名指向 ir.symbol
from ..ir.symbol import Symbol as IRSymbol, Scope as IRScope
```

---

### M0.8：验收标准

| # | 验收条件 |
|---|---------|
| 1 | `ir/symbol.py` 可正常 import（无循环依赖） |
| 2 | `ir/types.py` 的 `ZHCTy` 是 `TypeInfo` 的别名 |
| 3 | Bug 1 死代码已删除（grep 验证第 669-688 行不存在） |
| 4 | Bug 2 已修复（`python3 -c "from zhc.semantic.semantic_analyzer import SemanticAnalyzer; s = SemanticAnalyzer(); print('_symbol_lookup_optimizer' in dir(s))"` 输出 True） |
| 5 | 现有 586+ 测试零回归（`python3 -m pytest tests/ -x -q` 全通过） |

---

## M1：ZHC IR 定义

### M1.1：创建 IR 核心文件

```
src/ir/
├── opcodes.py        # Opcode 枚举（35+ 操作码）
├── values.py         # IRValue, ValueKind
├── instructions.py   # IRInstruction, IRBasicBlock
├── program.py        # IRProgram, IRFunction, IRGlobalVar, IRStructDef
└── printer.py       # IRPrinter
```

### M1.2：Opcode 设计（35+ 个）

| 类别 | 操作码 |
|------|--------|
| 算术 | ADD, SUB, MUL, DIV, MOD, NEG |
| 比较 | EQ, NE, LT, LE, GT, GE |
| 位运算 | AND, OR, XOR, NOT, SHL, SHR |
| 逻辑 | L_AND, L_OR, L_NOT |
| 内存 | ALLOC, LOAD, STORE, GETPTR, GEP |
| 控制流 | JMP, JZ, RET, CALL, SWITCH |
| 转换 | ZEXT, SEXT, TRUNC, BITCAST |
| 其他 | CONST, PHI, NOP |

每个 Opcode 包含：`name`, `category`, `chinese`, `is_terminator`, `has_result`。

### M1.3：验收标准

| # | 验收条件 |
|---|---------|
| 1 | `Opcode` 枚举包含 35+ 个值，每个有 category/chinese |
| 2 | `IRValue`, `IRInstruction`, `IRBasicBlock`, `IRFunction`, `IRProgram` 全部可实例化 |
| 3 | `IRPrinter` 可输出可读 IR 文本 |
| 4 | `tests/test_ir_definition.py`（20+ 测试）全通过 |

---

## M2：AST → IR 生成器

### M2.1：创建 `ir/ir_generator.py`

42 个 visit 方法，P0 优先：

| 优先级 | 节点 | IR 翻译 |
|--------|------|---------|
| P0 | ProgramNode | 创建 IRProgram |
| P0 | FunctionDeclNode | 创建 IRFunction + entry 块 |
| P0 | VariableDeclNode | ALLOC + STORE |
| P0 | ParamDeclNode | PARAM IRValue |
| P0 | BlockStmtNode | 递归翻译 |
| P0 | ReturnStmtNode | RET |
| P1 | BinaryExprNode | 对应操作码 |
| P1 | CallExprNode | CALL |
| ... | ... | ... |

### M2.2：参考 CCodeGenerator

`codegen/c_codegen.py` 有 47 个 visit 方法，覆盖全部 AST 节点，作为 IR 生成逻辑的参照。

### M2.3：验收标准

| # | 验收条件 |
|---|---------|
| 1 | 42 个 AST 节点均有对应 visit 方法 |
| 2 | 简单程序（变量 + 函数 + return）可完整翻译为 IR |
| 3 | `IRPrinter` 输出可读 |
| 4 | `tests/test_ir_generator.py`（35+ 测试）全通过 |

---

## M3：IR → C 后端 + 映射表提取

### M3.0：从 `c_codegen.py` 提取映射表（独立步骤）

**源**：`src/codegen/c_codegen.py` 第 35-100 行

**目标**：`src/ir/mappings.py`

```python
# ir/mappings.py
TYPE_MAP = { '整数型': 'int', ... }       # 5 个映射表
MODIFIER_MAP = { '常量': 'const', ... }
FUNCTION_NAME_MAP = { '主函数': 'main', ... }
INCLUDE_MAP = { ... }
STDLIB_FUNC_MAP = { ... }
```

**修改**：`c_codegen.py` 改为 `from ..ir.mappings import TYPE_MAP, ...`

### M3.1：创建 `ir/c_backend.py`

基本块展平算法，将 IR 基本块展平为线性 C 代码。

### M3.2：验收标准

| # | 验收条件 |
|---|---------|
| 1 | `c_codegen.py` 通过 `from ..ir.mappings import ...` 使用映射表 |
| 2 | 简单 IR 程序生成可编译的 C 代码 |
| 3 | `tests/test_c_backend.py`（25+ 测试）全通过 |

---

## M4：IR 验证器

### M4.1：创建 `ir/ir_verifier.py`

7 项检查：

| 检查 | 内容 |
|------|------|
| V1 | RET 指令在函数末尾 |
| V2 | JZ/JMP 目标基本块存在 |
| V3 | ALLOC 结果被使用 |
| V4 | CALL 参数数量匹配函数签名 |
| V5 | 类型转换合法性 |
| V6 | 无未定义的基本块引用 |
| V7 | phi 节点参数数量与前驱数量匹配 |

### M4.2：验收标准

| # | 验收条件 |
|---|---------|
| 1 | 所有 7 项检查均实现 |
| 2 | 非法 IR 可被检测并报告 |
| 3 | `tests/test_ir_verifier.py`（18+ 测试）全通过 |

---

## M5：IR 优化 Pass

### M5.1：创建 `ir/optimizer.py`

```python
class OptimizationPass(ABC):
    @abstractmethod
    def name(self) -> str: ...
    @abstractmethod
    def run(self, ir: IRProgram) -> IRProgram: ...

class PassManager:
    def register(self, pass_: OptimizationPass) -> 'PassManager': ...
    def run(self, ir: IRProgram) -> IRProgram: ...

class ConstantFolding(OptimizationPass): ...
class DeadCodeElimination(OptimizationPass): ...
```

### M5.2：验收标准

| # | 验收条件 |
|---|---------|
| 1 | `PassManager` 支持注册和执行 Pass |
| 2 | ConstantFolding 折叠常量表达式 |
| 3 | DeadCodeElimination 删除不可达块 |
| 4 | 优化后 IR 通过 IRVerifier |
| 5 | `tests/test_ir_optimizer.py`（25+ 测试）全通过 |

---

## M6：Pipeline 集成 + CLI

### M6.1：修改 `cli.py`

新增参数：
- `--backend ir|ast`（默认 `ast`）
- `--dump-ir`
- `--no-optimize`
- `-O0/-O1/-O2`

### M6.2：修改 `compiler/pipeline.py`

在语义验证后、C 代码生成前，插入 IR 生成步骤（两处入口：单文件和项目模式）。

### M6.3：验收标准

| # | 验收条件 |
|---|---------|
| 1 | `--backend ast` 现有 586+ 测试全通过 |
| 2 | `--backend ir --dump-ir` 正确输出 IR 文本 |
| 3 | `-O0/-O1/-O2` 正确控制优化级别 |
| 4 | `tests/test_pipeline_ir.py`（15+ 测试）全通过 |

---

## M7：测试 + 文档 + 清理

### M7.1：测试（153+ 个）

| 测试文件 | 数量 | 覆盖 |
|----------|------|------|
| `test_ir_symbol.py` | 15+ | Symbol/Scope |
| `test_ir_definition.py` | 20+ | IR 数据结构 |
| `test_ir_generator.py` | 35+ | AST→IR |
| `test_c_backend.py` | 25+ | IR→C |
| `test_ir_verifier.py` | 18+ | 验证器 |
| `test_ir_optimizer.py` | 25+ | 优化 Pass |
| `test_pipeline_ir.py` | 15+ | Pipeline 集成 |

### M7.2：技术债务清理

| 债务 | 修复 |
|------|------|
| TD1 | Bug 1 死代码（M0.5 已修复） |
| TD2 | Bug 2 未初始化（M0.6 已修复） |
| TD3 | `opt/__init__.py` 补全导出 FunctionInliner + LoopOptimizer |
| TD4 | `analyzer/performance.py` 过期 day2/day3 引用 |

### M7.3：验收标准

| # | 验收条件 |
|---|---------|
| 1 | 153+ 新测试全通过 |
| 2 | 586+ 现有测试零回归 |
| 3 | 技术债务 TD1-TD4 全部修复 |
| 4 | 无 lint 错误 |
| 5 | ARCHITECTURE.md 更新 |

---

## 执行顺序与依赖

```
M0（Symbol 统一 + 2 Bug 修复）
├── M1（IR 定义）
│    ├── M4（IR 验证器）
│    ├── M2（AST→IR 生成器）
│    └── M3（IR→C 后端 + 映射表）
│         └── M5（IR 优化 Pass）
│              └── M6（Pipeline 集成 + CLI）
└── M7（测试 + 文档 + 清理）
```

---

*Phase 7 v3.0 执行计划。基于代码库实测，排除无关内容，聚焦真实问题。*

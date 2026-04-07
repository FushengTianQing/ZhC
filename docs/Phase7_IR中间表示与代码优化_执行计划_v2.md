# Phase 7: IR 中间表示与代码优化 — 执行计划 v2.0

> 版本：v2.0（基于代码库深度审查优化）
> 创建时间：2026-04-03
> 更新时间：2026-04-03
> 项目路径：`/Users/yuan/Projects/zhc/`
> 前置依赖：Phase 6 全部完成 + Phase 7 旧任务（缓存/增量/性能/符号查找）✅
> 审查基线：全量代码库扫描（120+ 源文件）

---

## v1.0 → v2.0 变更摘要

### 新增发现（代码审查揭示的问题）

| # | 发现 | v1.0 处理 | v2.0 修正 | 影响范围 |
|---|------|-----------|-----------|----------|
| **D1** | **Scope 有三重定义**：`analyzer/scope_checker.py`、`semantic/semantic_analyzer.py`、`parser/scope.py` 各自定义不兼容的 Scope 类 | 仅提及两套 Symbol 体系 | 扩大为三套 Scope 统一 | M0 |
| **D2** | **`semantic.Symbol.data_type` 是字符串**（`Optional[str]`），但 v1.0 的统一 Symbol 欲用 `ZHCTy` 强类型——替换所有 `data_type` 访问点影响 `semantic_analyzer.py` 的 2128 行代码 | 未评估迁移成本 | M0 分两阶段：先定义新类+兼容层，再渐进迁移；预估工时从 6-8h 上调至 **8-12h** | M0 |
| **D3** | **`opt/` 模块已存在 4 个优化器**（`constant_fold.py` 23.8KB、`dead_code_elim.py` 19.4KB、`function_inline.py` 15.5KB、`loop_optimizer.py` 15.1KB），全部直接操作 **AST** 而非 IR | 完全未提及 | 新增 M5.5 适配层：评估现有 AST 优化器的 IR 迁移可行性；明确 `opt/` 与 `ir/optimizer.py` 的关系 | M5 |
| **D4** | **`opt/__init__.py` 未导出 `function_inline` 和 `loop_optimizer`**——这两个优化器处于半完成状态 | 未发现 | 记录为技术债务，M7 统一处理 | M5/M7 |
| **D5** | **`analyzer/` 已有 `__init__.py` 导出兼容层**（第 23 行明确注释 `semantic_analyzer.py` 已废弃）——说明此前已有架构整理意识 | 未利用此信息 | M0 迁移时优先保持 `analyzer/__init__.py` 和 `semantic/__init__.py` 的公共 API 不变 | M0 |
| **D6** | **`semantic/semantic_analyzer.py` 有 `_symbol_lookup_optimizer` 属性但 `__init__` 中未初始化**（第 281 行直接 `self._symbol_lookup_optimizer`，但 `__init__` 中未声明） | 未发现 | 记录为 bug，M0 一并修复 | M0 |
| **D7** | **`performance.py` 有过期引用**（`from ..day2.module_parser`），5 个测试被 skip | 未发现 | M7 技术债务清单中记录 | M7 |
| **D8** | **`parser/scope.py` 有独立的 Symbol + Scope 定义**（与 `scope_checker.py` 完全独立），被 parser 内部使用 | 完全未覆盖 | M0 需要考虑 parser 层 Scope 是否也纳入统一 | M0 |
| **D9** | **映射表耦合在 `c_codegen.py` 中**：`TYPE_MAP`、`MODIFIER_MAP`、`FUNCTION_NAME_MAP`、`INCLUDE_MAP`、`STDLIB_FUNC_MAP` 全部定义在同一文件 | 仅说"从 c_codegen.py 导入" | 提取到独立模块 `ir/mappings.py`，供 `c_codegen.py` 和 `ir/c_backend.py` 共同使用 | M3/M6 |
| **D10** | **`pipeline.py` 实际 742 行**（v1.0 估计 150 行） | 工时估计偏低 | M6 工时从 3-4h 上调至 **5-6h** | M6 |
| **D11** | **Phase 7 旧任务已完成**：AST 缓存、增量 AST 更新、性能分析、符号查找优化器（均在 `analyzer/` 下） | 完全未提及 | 新增§0.5"Phase 7 已完成工作"章节，明确 IR 层与这些已完成模块的关系 | 全局 |

---

## 零、现状基线

### 0.1 当前编译流程

```
.zhc 源码 → Lexer → Parser → AST
                              ↓
                     SemanticAnalyzer（AST 上分析）
                       ├── 符号表构建（SymbolTable + Scope 链）
                       ├── 作用域分析
                       ├── 类型检查（延迟加载 TypeCheckerCached）
                       ├── 函数参数/重载检查
                       ├── 控制流分析（CFG/未初始化/不可达）
                       ├── 数据流/过程间/别名/指针分析
                       ├── 7 个分析器开关
                       ├── AST 缓存（Phase 7 已完成）
                       ├── 增量 AST 更新（Phase 7 已完成）
                       ├── 性能分析（Phase 7 已完成）
                       └── 符号查找优化（Phase 7 已完成）
                              ↓
                     CCodeGenerator（直接读 AST）→ C 代码
                              ↓
                     clang → 可执行文件
```

### 0.2 关键代码文件基线（v2.0 审查修正）

| 文件 | 实际行数 | 职责 | Phase 7 影响 |
|------|---------|------|-------------|
| `src/zhpp/codegen/c_codegen.py` | **624** | AST→C 代码生成（47 个 visit 方法） | **重大改造**：映射表提取 + 作为 IR→C 后端参照 |
| `src/zhpp/semantic/semantic_analyzer.py` | **2128** | 主分析器（含 Symbol/Scope/SymbolTable/SemanticError） | **中度**：Symbol 兼容迁移 + 传入 Symbol 信息给 IR 生成器 |
| `src/zhpp/compiler/pipeline.py` | **742** | 集成编译流水线（单文件 + 项目模式） | **改造**：插入 IR 生成和优化步骤（两处入口） |
| `src/zhpp/cli.py` | **376** | CLI 入口（单文件 + 模块项目） | 新增 `--backend` / `--no-optimize` / `--dump-ir` 等参数 |
| `src/zhpp/analyzer/scope_checker.py` | **521** | 第二套 Symbol/Scope/ScopeChecker | **整合**：合并到统一 Symbol 体系 |
| `src/zhpp/parser/scope.py` | **~440** | 第三套 Symbol/Scope（parser 内部） | **评估**：是否纳入统一 |
| `src/zhpp/analyzer/type_checker.py` | **711** | TypeInfo + TypeChecker + TypeCategory | **中度**：TypeInfo 迁移到 `ir/types.py` |
| `src/zhpp/parser/ast_nodes.py` | **1523** | 37 个具体 AST 节点类 + ASTVisitor 基类 | **无修改**：IR 生成器通过 ASTVisitor 访问 |
| `src/zhpp/opt/` | **~74KB** | 4 个 AST 级优化器（常量传播/死代码消除/函数内联/循环优化） | **评估**：IR 适配可行性 |

### 0.3 三套 Symbol + Scope 体系现状（v2.0 完整版）

| 特征 | `semantic.Symbol` | `scope_checker.Symbol` | `parser.scope.Symbol` |
|------|-------------------|------------------------|----------------------|
| 位置 | `semantic/semantic_analyzer.py:43` | `analyzer/scope_checker.py:32` | `parser/scope.py` |
| 分类 | 字符串 `symbol_type: str`（"变量"/"函数"等） | 枚举 `SymbolCategory`（7 种） | 枚举 `SymbolCategory`（独立定义） |
| 类型 | `data_type: Optional[str]` | `type_info: TypeInfo`（强类型） | `type_info: TypeInfo`（强类型） |
| 作用域 | 自定义 Scope（@dataclass，有 ScopeType 枚举） | 自定义 Scope（普通类，有 level/parent/children） | 自定义 Scope（普通类，有 name/scope_type） |
| 使用范围 | SemanticAnalyzer 全流程（2128 行） | ScopeChecker + OverloadResolver | Parser 内部（parser.py / class_.py） |
| 重载 | 有（parameters 列表） | 无 | 无 |
| 导出路径 | `semantic/__init__.py` 导出 | `analyzer/__init__.py` 导出 | 未导出（parser 内部） |
| 测试引用 | 6 个测试文件直接导入 | 2 个测试文件直接导入 | 无外部引用 |

### 0.4 TypeInfo 依赖面

TypeInfo 定义于 `analyzer/type_checker.py:31`，被以下模块引用：

| 模块 | 引用方式 |
|------|---------|
| `analyzer/scope_checker.py` | `from .type_checker import TypeInfo`（Symbol.type_info 字段） |
| `analyzer/type_checker_cached.py` | `from .type_checker import TypeChecker, TypeInfo, TypeCategory` |
| `analyzer/overload_resolver.py` | `from .type_checker import TypeInfo` |
| `analyzer/ast_cache.py` | `_type_cache: Dict[int, Any]  # node_id -> TypeInfo` |
| `semantic/semantic_analyzer.py` | 延迟初始化 `TypeCheckerCached()`（间接使用 TypeInfo） |
| `analyzer/__init__.py` | `from .type_checker import TypeChecker, TypeInfo, TypeCategory`（公共导出） |
| `tests/test_semantic_analyzer.py` | `from zhpp.analyzer import TypeInfo`（测试直接导入） |
| `tests/test_ast_semantic_type.py` | `from zhpp.analyzer import TypeInfo` |

**迁移风险**：TypeInfo 被 `analyzer/__init__.py` 作为公共 API 导出，直接迁移定义会破坏测试代码和外部依赖。需保留兼容别名。

### 0.5 Phase 7 已完成工作（v2.0 新增）

以下功能已在 Phase 7 旧任务中完成，位于 `analyzer/` 目录：

| 模块 | 文件 | 功能 | CLI 开关 |
|------|------|------|----------|
| AST 缓存 | `analyzer/ast_cache.py` (16.9KB) | AST 节点分析结果缓存 | 自动启用 |
| 增量 AST 更新 | `analyzer/incremental_ast_updater.py` (17.0KB) | 同文件两轮编译间 AST diff | 自动启用 |
| 性能分析 | `analyzer/performance.py` (12.9KB) | 各编译阶段耗时测量 | `--profile` |
| 符号查找优化 | `analyzer/symbol_lookup_optimizer.py` (14.4KB) | 热点缓存 + O(1) 查找 | `--optimize-symbol-lookup` |
| 缓存类型检查 | `analyzer/type_checker_cached.py` (10.5KB) | 带缓存的 TypeChecker | SemanticAnalyzer 内部使用 |
| 缓存控制流 | `analyzer/control_flow_cached.py` (12.7KB) | 带缓存的 CFG 构建 | SemanticAnalyzer 内部使用 |

**IR 层与这些模块的关系**：
- IR 层**不需要迁移**这些已完成模块
- IR 生成器可直接复用 AST 缓存和增量更新（AST 变化检测→仅重新生成受影响函数的 IR）
- IR 优化 Pass 可参考 `opt/constant_fold.py` 和 `opt/dead_code_elim.py` 的算法实现

### 0.6 IR 缺口清单（确认）

| # | 缺口 | 状态 |
|---|------|------|
| IR-1 | ZHC IR 定义（指令集、基本块、函数表示） | ❌ 不存在 |
| IR-2 | AST → IR 生成器 | ❌ 不存在 |
| IR-3 | IR → C 后端 | ❌ 不存在（当前 CCodeGenerator 直读 AST） |
| IR-4 | IR 优化 Pass | ❌ 不存在（`opt/` 下有 AST 级优化器，非 IR 级） |
| IR-5 | IR 验证器 | ❌ 不存在 |
| IR-6 | 映射表独立模块 | ❌ 不存在（耦合在 `c_codegen.py` 中） |

---

## 一、目标架构

### 1.1 Phase 7 完成后的编译流程

```
.zhc 源码 → Lexer → Parser → AST
                              ↓
                     SemanticAnalyzer（AST 上分析，保持不变）
                              ↓
                     IRGenerator（AST → IR）         ← 新增
                              ↓
                           ZHC IR                     ← 新增
                              ↓
                     IRVerifier（合法性检查）          ← 新增
                              ↓
                     Optimizer（IR 优化 Pass）         ← 新增
                              ↓
                           ZHC IR'（优化后）
                              ↓
                     CBackend（IR → C）               ← 新增（替代 CCodeGenerator 的直接 AST 读取）
                              ↓
                          C 代码
                              ↓
                     clang → 可执行文件
```

### 1.2 兼容策略

Phase 7 **不删除** CCodeGenerator。新增 `--backend` 参数：

- `--backend ir`（默认，Phase 7 完成后）：AST → IR → 验证 → 优化 → C
- `--backend ast`（兼容模式）：AST → C 直连（现有路径）

这保证现有 586+ 测试不会因 Phase 7 而失败。

### 1.3 映射表解耦（v2.0 新增）

将 `c_codegen.py` 中的 5 个映射表提取到独立模块 `ir/mappings.py`：

```
c_codegen.py（当前）──TYPE_MAP, MODIFIER_MAP, FUNCTION_NAME_MAP, INCLUDE_MAP, STDLIB_FUNC_MAP
       ↓ 提取
ir/mappings.py ──────── 统一定义
       ↓ 导入
c_codegen.py ────────── 复用
ir/c_backend.py ──────── 复用
```

---

## 二、里程碑总览（v2.0 修正）

| 里程碑 | 名称 | v1.0 工时 | v2.0 工时 | 变更原因 | 依赖 | 核心交付 |
|--------|------|-----------|-----------|----------|------|----------|
| **M0** | Symbol 体系统一 | 6-8h | **8-12h** | 三套 Scope 统一 + 2128 行 semantic_analyzer 迁移 + bug 修复 | 无 | 统一的 `ir/symbol.py` + 兼容层 |
| **M1** | ZHC IR 定义 | 8-12h | 8-12h | 不变 | M0 | `ir/` 目录 + IR 指令集 + IR 数据结构 |
| **M2** | AST → IR 生成器 | 12-16h | **10-14h** | ASTVisitor 基类完善，参考 CCodeGenerator 的 47 个 visit 方法 | M1 | `ir/ir_generator.py` |
| **M3** | IR → C 后端 | 6-8h | **8-10h** | 新增映射表提取步骤 + 基本块展平复杂度 | M1 | `ir/c_backend.py` + `ir/mappings.py` |
| **M4** | IR 验证器 | 3-4h | 3-4h | 不变 | M1 | `ir/ir_verifier.py` |
| **M5** | IR 优化 Pass | 6-8h | **8-10h** | 新增现有 `opt/` 优化器评估 + 适配层设计 | M1 | `ir/optimizer.py` + 2-3 个 Pass |
| **M6** | Pipeline 集成 + CLI | 3-4h | **5-6h** | pipeline.py 实际 742 行 + 两处入口（单文件/模块项目） | M2-M5 | pipeline.py 改造 + CLI 参数 |
| **M7** | 测试 + 文档 + 清理 | 4-6h | **6-8h** | 新增技术债务修复（D6 bug + D7 过期引用 + D4 未导出优化器） | M0-M6 | 全量测试 + 迁移文档 |
| | **合计** | **48-66h** | **56-72h** | +8h | | 约 **7-9 个工作日** |

---

## 三、M0：Symbol 体系统一（v2.0 扩展）

### 3.1 目标

合并三套 Symbol/Scope 体系为统一版本，同时修复已知 bug。

### 3.2 v2.0 新增决策

| 决策点 | v1.0 | v2.0 | 理由 |
|--------|------|------|------|
| Scope 统一范围 | 两套（semantic + scope_checker） | **三套**（semantic + scope_checker + parser） | parser/scope.py 有独立 Symbol/Scope 定义 |
| parser Scope 迁移策略 | 未考虑 | **不迁移 parser 内部 Scope**，仅统一公共 API | parser 的 Scope 仅在语法分析阶段使用，IR 层不依赖它；强制迁移风险高收益低 |
| 迁移策略 | "保留旧类名作为别名" | **分两阶段**：阶段 A 定义新类+兼容别名；阶段 B 渐进替换 semantic_analyzer.py 中的使用 | semantic_analyzer.py 有 2128 行，一次性替换风险太高 |
| bug 修复 | 未发现 | **修复** `semantic_analyzer.py` 中 `_symbol_lookup_optimizer` 未初始化 bug | 第 281 行直接 `self._symbol_lookup_optimizer = None`，但 `__init__` 中未声明 |

### 3.3 执行步骤（v2.0 修正）

#### 步骤 M0.1：创建 `src/zhpp/ir/` 包

```
src/zhpp/ir/
├── __init__.py          # 导出 Symbol, Scope, TypeInfo, SymbolCategory 等
├── symbol.py            # 统一的 Symbol + Scope + SymbolCategory 定义
├── types.py             # ZHCTy 类型体系（重新设计，兼容 TypeInfo）
├── mappings.py          # TYPE_MAP, MODIFIER_MAP 等（从 c_codegen.py 提取，M3 详细设计）
└── opcodes.py           # IR 操作码枚举（M1 依赖，提前预留空文件）
```

#### 步骤 M0.2：定义统一 Symbol 类

文件：`src/zhpp/ir/symbol.py`

**设计要点**：
- 合并 `scope_checker.Symbol` 的 `SymbolCategory` 枚举 + `TypeInfo` 强类型
- 保留 `semantic.Symbol` 的 `parameters`/`members`/`return_type` 等函数/结构体特有字段
- 提供 `symbol_type`（字符串）和 `data_type`（字符串）作为 `@property` 兼容接口
- `ZHCTy` 作为 `TypeInfo` 的轻量包装，内部可直接持有 `TypeInfo` 实例

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict

class SymbolCategory(Enum):
    """统一的符号类别枚举"""
    VARIABLE = "variable"
    FUNCTION = "function"
    PARAMETER = "parameter"
    TYPEDEF = "typedef"
    STRUCT = "struct"
    MODULE = "module"
    LABEL = "label"
    ENUM = "enum"        # v2.0 新增
    UNION = "union"      # v2.0 新增

@dataclass
class Symbol:
    """统一的符号信息"""
    name: str
    category: SymbolCategory
    type_info: Optional['TypeInfo'] = None  # 兼容：允许 None
    line: int = 0
    is_global: bool = False
    is_static: bool = False
    is_const: bool = False
    is_initialized: bool = False
    is_used: bool = False
    scope_level: int = 0

    # 函数特有
    parameters: List['Symbol'] = field(default_factory=list)
    return_type: Optional[str] = None       # 保持字符串，与 semantic.Symbol 兼容

    # 结构体特有
    members: List['Symbol'] = field(default_factory=list)
    methods: List['Symbol'] = field(default_factory=list)  # v2.0 从 semantic.Symbol 补充
    parent_struct: Optional[str] = None

    # === 兼容 semantic.Symbol 的属性 ===
    @property
    def symbol_type(self) -> str:
        return self.category.value

    @property
    def data_type(self) -> Optional[str]:
        if self.type_info:
            return str(self.type_info)
        return self.return_type  # 函数返回类型回退

    @property
    def definition_location(self) -> str:
        return f"{self.line}:0"

    # === 兼容 scope_checker.Symbol 的属性 ===
    @property
    def type_info_str(self) -> str:
        """返回类型字符串（scope_checker 兼容）"""
        return str(self.type_info) if self.type_info else ""
```

#### 步骤 M0.3：定义统一 Scope 类

```python
class ScopeType(Enum):
    """作用域类型枚举（从 semantic.ScopeType 迁移）"""
    GLOBAL = "全局"
    MODULE = "模块"
    STRUCT = "结构体"
    FUNCTION = "函数"
    BLOCK = "代码块"
    LOOP = "循环"

@dataclass
class Scope:
    """统一的作用域"""
    scope_type: ScopeType = ScopeType.GLOBAL
    scope_name: str = ""
    parent: Optional['Scope'] = None
    symbols: Dict[str, Symbol] = field(default_factory=dict)
    level: int = 0
    children: List['Scope'] = field(default_factory=list)

    def add_symbol(self, symbol: Symbol) -> bool:
        """添加符号（semantic 兼容）"""
        if symbol.name in self.symbols:
            return False
        symbol.scope_level = self.level
        self.symbols[symbol.name] = symbol
        if self.parent:
            self.parent.children.append(self)  # v2.0: 自动维护 children
        return True

    def declare(self, symbol: Symbol):
        """声明符号（scope_checker 兼容）"""
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str) -> Optional[Symbol]:
        """查找符号（当前 + 父作用域）"""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """仅在当前作用域查找"""
        return self.symbols.get(name)

    def all_symbols(self) -> Dict[str, Symbol]:
        """递归收集所有符号"""
        result = dict(self.symbols)
        for child in self.children:
            result.update(child.all_symbols())
        return result
```

#### 步骤 M0.4：修复已知 bug

修复 `semantic/semantic_analyzer.py` 第 281 行：

```python
# 当前（有 bug）：
def _get_symbol_lookup_optimizer(self):
    if not getattr(self, 'symbol_lookup_enabled', False):
        return None
    if self._symbol_lookup_optimizer is None:  # ← __init__ 中未声明此属性

# 修复：在 __init__ 中添加
self._symbol_lookup_optimizer = None  # 在 self.symbol_lookup_enabled = False 之后
```

#### 步骤 M0.5：阶段 A — 创建兼容别名

在 `analyzer/__init__.py` 和 `semantic/__init__.py` 中添加兼容导入：

```python
# analyzer/__init__.py — 添加兼容别名
from ..ir.symbol import Symbol as IRSymbol, Scope as IRScope, SymbolCategory as IRSymbolCategory

# 保留旧名称作为别名（渐进迁移）
# _LegacySymbol = scope_checker.Symbol  # 已被 ir.symbol.Symbol 替代
```

**注意**：阶段 A **不修改** `semantic_analyzer.py` 内部的 Symbol 使用。仅确保新 Symbol 类可被导入且 API 兼容。

#### 步骤 M0.6：阶段 B — 渐进迁移 semantic_analyzer.py

分批替换 `semantic_analyzer.py` 中的 `Symbol` 和 `Scope` 使用：

1. **Batch 1**：`SymbolTable` 类（第 111-208 行）— 替换 Scope 引用
2. **Batch 2**：`SemanticAnalyzer.__init__`（第 222-260 行）— 替换字段类型
3. **Batch 3**：`_analyze_*` 方法中的 Symbol 创建 — 替换 `Symbol()` 构造调用
4. **Batch 4**：验证所有测试通过

每批替换后运行全量测试，确保不回归。

#### 步骤 M0.7：迁移 scope_checker.py

- 删除 `scope_checker.py` 中的 `Symbol`、`SymbolCategory`、`Scope` 定义
- 改为从 `ir.symbol` 导入
- `TypeInfo` 暂不从 `type_checker.py` 迁出（留到 M0.8）

#### 步骤 M0.8：TypeInfo 迁移（可选，低优先级）

- 在 `ir/types.py` 中定义 `ZHCTy` 作为 `TypeInfo` 的别名
- `type_checker.py` 中的 `TypeInfo` 定义保留原位
- `ir/types.py` 仅做 `from ..analyzer.type_checker import TypeInfo as ZHCTy`
- 这样 `ir/` 模块使用 `ZHCTy`，`analyzer/` 模块继续使用 `TypeInfo`，两边是同一个类

**v2.0 建议**：M0.8 作为**可选步骤**，不在 M0 验收的必须路径上。如果时间紧张，可推迟到 M7。

#### 步骤 M0.9：parser Scope 评估结论

**决策：不迁移 parser/scope.py**。

理由：
1. `parser/scope.py` 的 Symbol 和 Scope 仅在 parser 内部使用（`parser.py`、`class_.py`、`class_extended.py`），不暴露给外部
2. parser 层的 Scope 在语法分析阶段创建，与 semantic 层的 Scope 生命周期不同
3. IR 生成器不依赖 parser 层的 Scope
4. 强制迁移风险高（parser.py 有 52.2KB），收益低

### 3.4 验收标准（v2.0 修正）

- [ ] `src/zhpp/ir/symbol.py` 和 `src/zhpp/ir/types.py` 定义完成
- [ ] 统一 Symbol 类同时兼容 `semantic.Symbol` 和 `scope_checker.Symbol` 的 API
- [ ] 统一 Scope 类同时兼容 `semantic.Scope` 和 `scope_checker.Scope` 的 API
- [ ] `semantic_analyzer.py` 的 `_symbol_lookup_optimizer` bug 已修复
- [ ] `semantic/__init__.py` 和 `analyzer/__init__.py` 的公共 API 保持不变
- [ ] 旧测试（586+）全部通过（兼容路径）
- [ ] 新增 `tests/test_ir_symbol.py`（15+ 测试：Symbol 创建、Scope 链、兼容属性）

### 3.5 风险（v2.0 修正）

| 风险 | 缓解 |
|------|------|
| semantic_analyzer.py 2128 行迁移破坏现有测试 | 分批替换 + 每批运行全量测试 |
| TypeChecker 依赖 TypeInfo 旧路径 | `ir/types.py` 做别名而非迁移定义 |
| parser/scope.py 不迁移导致三套 Scope 并存 | 明确标注 parser Scope 为"内部使用"，不纳入公共 API |

---

## 四、M1：ZHC IR 定义

> 与 v1.0 基本一致，仅做小幅修正。

### 4.1 目标

定义 ZHC IR 的完整指令集、数据结构和程序表示。

### 4.2 设计原则（v2.0 补充）

| 原则 | 说明 |
|------|------|
| **非严格 SSA** | 变量可多次赋值，用 `ALLOC` + `STORE` 代替 phi 节点 |
| **类型保留** | IR 指令携带类型信息，不做类型擦除 |
| **中文友好** | IR 调试输出可显示中文操作码名 |
| **可扩展** | 使用枚举 + dataclass，新增指令只需添加枚举值 |
| **与 AST 节点 1:1 覆盖** | 确保 37 个 AST 节点类型 + 5 个类型节点均有对应 IR 翻译路径 |

### 4.3 IR 操作码设计

> 与 v1.0 一致（30+ 操作码），此处不重复列出。参见 v1.0 §4.4。

### 4.4 IR 包结构（v2.0 修正）

```
src/zhpp/ir/
├── __init__.py          # 导出所有公共 API
├── symbol.py            # M0: 统一 Symbol + Scope
├── types.py             # M0: ZHCTy / TypeInfo 别名
├── mappings.py          # M0/M3: TYPE_MAP 等映射表
├── opcodes.py           # M1: 操作码枚举
├── values.py            # M1: IRValue, ValueKind
├── instructions.py      # M1: IRInstruction, IRBasicBlock
├── program.py           # M1: IRProgram, IRFunction, IRGlobalVar, IRStructDef
├── printer.py           # M1: IR 文本打印器
├── ir_generator.py      # M2: AST→IR 生成器（占位）
├── c_backend.py         # M3: IR→C 后端（占位）
├── ir_verifier.py       # M4: IR 验证器（占位）
└── optimizer.py         # M5: PassManager + 优化 Pass（占位）
```

### 4.5 验收标准

- [ ] `src/zhpp/ir/` 包完整创建，包含 14 个模块
- [ ] `Opcode` 枚举包含 30+ 操作码，每个有 category 和中文名
- [ ] `IRValue`, `IRInstruction`, `IRBasicBlock`, `IRFunction`, `IRProgram` 全部定义
- [ ] `IRPrinter` 可输出可读的 IR 文本
- [ ] 新增 `tests/test_ir_definition.py`（20+ 测试）

---

## 五、M2：AST → IR 生成器（v2.0 修正）

### 5.1 目标

将 AST 完整翻译为 ZHC IR，覆盖所有 AST 节点类型。

### 5.2 v2.0 修正

| 修正点 | v1.0 | v2.0 |
|--------|------|------|
| AST 节点覆盖 | "40+ 种" | 明确为 **37 个具体节点类 + 5 个类型节点 = 42 个 visit 方法** |
| 参照基准 | "参照 CCodeGenerator" | CCodeGenerator 有 **47 个 visit 方法**（含 5 个类型节点），完全覆盖 ASTVisitor 的 42 个抽象方法 |
| 函数调用约定 | "使用 mangling 名" | 具体化：`_resolve_function_name()` 复用 `FUNCTION_NAME_MAP` + `STDLIB_FUNC_MAP` |
| IR 生成器输入 | `symbol_table: SymbolTable` | v2.0 改为 `symbol_table: Optional[SymbolTable] = None`，允许在无语义分析时也能生成 IR（调试用） |

### 5.3 visit 方法对照表（v2.0 新增）

| 优先级 | AST 节点 | IR 翻译 | CCodeGenerator 参考 |
|--------|----------|---------|-------------------|
| P0-核心 | `ProgramNode` | 创建 `IRProgram` | `visit_program` |
| P0-核心 | `FunctionDeclNode` | 创建 `IRFunction` + entry 块 | `visit_function_decl` |
| P0-核心 | `VariableDeclNode` | `ALLOC` + 可选 `STORE` | `visit_variable_decl` |
| P0-核心 | `ParamDeclNode` | 创建 PARAM `IRValue` | `visit_param_decl` |
| P0-核心 | `BlockStmtNode` | 递归翻译 | `visit_block_stmt` |
| P0-核心 | `ReturnStmtNode` | `RET` | `visit_return_stmt` |
| P1-表达式 | `BinaryExprNode` | 对应算术/比较/逻辑操作码 | `visit_binary_expr` |
| P1-表达式 | `UnaryExprNode` | `NEG` / `L_NOT` / `NOT` | `visit_unary_expr` |
| P1-表达式 | `AssignExprNode` | `STORE` | `visit_assign_expr` |
| P1-表达式 | `CallExprNode` | `CALL` | `visit_call_expr` |
| P1-表达式 | `IdentifierExprNode` | `LOAD` 或直接引用 | `visit_identifier_expr` |
| P1-表达式 | `IntLiteralNode` | `CONST` | `visit_int_literal` |
| P1-表达式 | `FloatLiteralNode` | `CONST` | `visit_float_literal` |
| P1-表达式 | `StringLiteralNode` | `CONST` + `GLOBAL_ADDR`（字符串池） | `visit_string_literal` |
| P1-表达式 | `BoolLiteralNode` | `CONST` | `visit_bool_literal` |
| P1-表达式 | `CharLiteralNode` | `CONST` | `visit_char_literal` |
| P1-表达式 | `NullLiteralNode` | `CONST`（零值指针） | `visit_null_literal` |
| P2-控制流 | `IfStmtNode` | `JZ`/`JMP` + 新基本块 | `visit_if_stmt` |
| P2-控制流 | `WhileStmtNode` | 循环头 + 循环体 + `JZ` | `visit_while_stmt` |
| P2-控制流 | `ForStmtNode` | 初始化 + 条件 + 更新 + 循环体 | `visit_for_stmt` |
| P2-控制流 | `DoWhileStmtNode` | 先执行后判断 | `visit_do_while_stmt` |
| P2-控制流 | `SwitchStmtNode` | `SWITCH` + case 基本块 | `visit_switch_stmt` |
| P2-控制流 | `CaseStmtNode` | case 基本块 | `visit_case_stmt` |
| P2-控制流 | `DefaultStmtNode` | default 基本块 | `visit_default_stmt` |
| P2-控制流 | `BreakStmtNode` | `JMP` 到循环出口 | `visit_break_stmt` |
| P2-控制流 | `ContinueStmtNode` | `JMP` 到循环条件 | `visit_continue_stmt` |
| P2-控制流 | `GotoStmtNode` | `JMP` 到标签 | `visit_goto_stmt` |
| P2-控制流 | `LabelStmtNode` | 标签基本块 | `visit_label_stmt` |
| P3-高级 | `StructDeclNode` | `IRStructDef` | `visit_struct_decl` |
| P3-高级 | `EnumDeclNode` | 常量序列 | `visit_enum_decl` |
| P3-高级 | `UnionDeclNode` | `IRStructDef`（union 标记） | `visit_union_decl` |
| P3-高级 | `TypedefDeclNode` | 类型别名记录 | `visit_typedef_decl` |
| P3-高级 | `MemberExprNode` | `GET_PTR` + `LOAD` | `visit_member_expr` |
| P3-高级 | `ArrayExprNode` | `GET_PTR` + `LOAD` | `visit_array_expr` |
| P3-高级 | `CastExprNode` | `CAST` | `visit_cast_expr` |
| P3-高级 | `SizeofExprNode` | `SIZEOF` | `visit_sizeof_expr` |
| P3-高级 | `TernaryExprNode` | 条件分支 + phi 模拟 | `visit_ternary_expr` |
| P3-高级 | `ArrayInitNode` | `ALLOC` + `STORE` 序列 | `visit_array_init` |
| P3-高级 | `StructInitNode` | `ALLOC` + `STORE` 序列 | `visit_struct_init` |
| P4-模块 | `ModuleDeclNode` | 模块信息记录 | `visit_module_decl` |
| P4-模块 | `ImportDeclNode` | extern 函数声明 | `visit_import_decl` |
| P4-类型 | `PrimitiveTypeNode` | `ZHCTy` 映射 | `visit_primitive_type` |
| P4-类型 | `PointerTypeNode` | `ZHCTy`（pointer） | `visit_pointer_type` |
| P4-类型 | `ArrayTypeNode` | `ZHCTy`（array） | `visit_array_type` |
| P4-类型 | `FunctionTypeNode` | `ZHCTy`（function） | `visit_function_type` |
| P4-类型 | `StructTypeNode` | `ZHCTy`（struct） | `visit_struct_type` |
| P4-语句 | `ExprStmtNode` | 翻译表达式 + 丢弃结果 | `visit_expr_stmt` |

### 5.4 验收标准（v2.0 修正）

- [ ] 所有 42 个 AST 节点类均有对应的 visit 方法
- [ ] 语义分析后的简单程序可完整翻译为 IR
- [ ] IR 打印器可输出正确的 IR 文本
- [ ] 控制流结构（if/while/for/do-while/switch/嵌套）正确生成基本块
- [ ] 新增 `tests/test_ir_generator.py`（35+ 测试）
  - P0 核心节点：6 个测试
  - P1 表达式节点：8 个测试
  - P2 控制流节点：8 个测试（含嵌套）
  - P3 高级特性：8 个测试
  - P4 模块/类型：5 个测试

---

## 六、M3：IR → C 后端（v2.0 修正）

### 6.1 目标

从 ZHC IR 生成可编译的 C 代码，功能上与现有 CCodeGenerator 等价。

### 6.2 v2.0 新增：映射表提取

#### 步骤 M3.0：提取映射表到 `ir/mappings.py`

将 `c_codegen.py` 中的 5 个映射表提取到独立模块：

```python
# src/zhpp/ir/mappings.py

# 中文类型 -> C 类型映射（11 个条目）
TYPE_MAP = {
    '整数型': 'int', '浮点型': 'float', '字符型': 'char',
    '布尔型': '_Bool', '空型': 'void', '无类型': 'void',
    '字符串型': 'char*', '字节型': 'unsigned char',
    '双精度浮点型': 'double', '逻辑型': '_Bool',
    '长整数型': 'long', '短整数型': 'short',
}

# 中文修饰符 -> C 修饰符（8 个条目）
MODIFIER_MAP = {
    '常量': 'const', '静态': 'static', '易变': 'volatile',
    '外部': 'extern', '内联': 'inline', '无符号': 'unsigned',
    '有符号': 'signed', '注册': 'register',
}

# 特殊函数名映射（2 个条目）
FUNCTION_NAME_MAP = {'主函数': 'main', '主程序': 'main'}

# 标准 include 映射（16 个条目）
INCLUDE_MAP = { ... }  # 同 c_codegen.py

# C 标准库函数名映射（16 个条目）
STDLIB_FUNC_MAP = { ... }  # 同 c_codegen.py
```

修改 `c_codegen.py`：
```python
# 改为从 ir.mappings 导入（保持向后兼容）
from ..ir.mappings import TYPE_MAP, MODIFIER_MAP, FUNCTION_NAME_MAP, INCLUDE_MAP, STDLIB_FUNC_MAP
```

### 6.3 CBackend 设计

文件：`src/zhpp/ir/c_backend.py`

- 基本块展平算法（模式 B，推荐）
- 中文函数名解析：复用 `ir/mappings.py` 中的映射表
- `#include` 自动推断（根据 CALL 指令中引用的函数名 + `INCLUDE_MAP`）

### 6.4 验收标准（v2.0 修正）

- [ ] 所有 IR 操作码均有翻译逻辑
- [ ] `ir/mappings.py` 从 `c_codegen.py` 成功提取，`c_codegen.py` 通过导入复用
- [ ] 简单 C 程序经 AST→IR→C 后可正确编译运行
- [ ] 生成的 C 代码可读性接近现有 CCodeGenerator 的输出
- [ ] 新增 `tests/test_c_backend.py`（25+ 测试）
- [ ] 与 CCodeGenerator 的输出做**语义等价**对比

---

## 七、M4：IR 验证器

> 与 v1.0 一致，此处不重复。参见 v1.0 §七。

新增检查项（v2.0 补充）：

| 检查 | 说明 |
|------|------|
| 中文函数名解析 | CALL 指令中的函数名必须能被 `STDLIB_FUNC_MAP` 或 `FUNCTION_NAME_MAP` 解析，或为用户定义函数 |
| 结构体成员访问 | GET_PTR 指令引用的结构体必须在 IRProgram.structs 中定义 |

---

## 八、M5：IR 优化 Pass（v2.0 扩展）

### 8.1 目标

建立 IR 优化框架，实现 2-3 个实用的优化 Pass，评估现有 AST 优化器的迁移可行性。

### 8.2 v2.0 新增：现有 `opt/` 模块评估

#### 现有优化器清单

| 优化器 | 文件 | 大小 | 操作对象 | 导出状态 | IR 迁移可行性 |
|--------|------|------|----------|----------|---------------|
| `ConstantPropagator` | `opt/constant_fold.py` | 23.8KB | AST | ✅ 已导出 | **高**：算法可直接移植到 IR 指令 |
| `DeadCodeEliminator` | `opt/dead_code_elim.py` | 19.4KB | AST | ✅ 已导出 | **高**：CFG 可达性分析可直接复用 |
| `FunctionInliner` | `opt/function_inline.py` | 15.5KB | AST | ❌ 未导出 | **中**：需要 IR 级的函数体复制 |
| `LoopOptimizer` | `opt/loop_optimizer.py` | 15.1KB | AST | ❌ 未导出 | **低**：循环检测在 IR CFG 上更自然，但实现复杂 |

#### 步骤 M5.5：适配层设计

```python
# src/zhpp/ir/optimizer.py

class OptimizationPass(ABC):
    """优化 Pass 基类"""
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def run(self, ir: IRProgram) -> IRProgram: ...


class PassManager:
    """优化 Pass 管理器"""
    def __init__(self):
        self.passes: List[OptimizationPass] = []

    def register(self, pass_: OptimizationPass) -> 'PassManager': ...
    def run(self, ir: IRProgram) -> IRProgram: ...


# === IR 级优化 Pass ===

class ConstantFolding(OptimizationPass):
    """常量折叠（参考 opt/constant_fold.py 的 LatticeValue 算法）"""
    def run(self, ir: IRProgram) -> IRProgram: ...

class DeadCodeElimination(OptimizationPass):
    """死代码消除（参考 opt/dead_code_elim.py 的 VarLiveness 算法）"""
    def run(self, ir: IRProgram) -> IRProgram: ...

class ConstantPropagation(OptimizationPass):
    """常量传播（可选）"""
    def run(self, ir: IRProgram) -> IRProgram: ...
```

#### 与现有 `opt/` 的关系决策

**v2.0 决策**：`ir/optimizer.py` 中的 Pass 是**全新的 IR 级实现**，不复用 `opt/` 的代码，但参考其算法思路。理由：
1. 操作对象不同（IR 指令 vs AST 节点），直接复用代码会导致混乱
2. IR 的扁平三地址码结构使优化算法实现更简单
3. `opt/` 下的 AST 优化器在 `--backend ast` 模式下仍然有用，不应废弃

**长期规划**（Phase 8+）：当 IR 路径成为默认路径后，可考虑将 `opt/` 的 AST 优化器标记为 deprecated。

### 8.3 验收标准（v2.0 修正）

- [ ] `PassManager` 支持注册和执行任意 Pass
- [ ] ConstantFolding 正确折叠常量表达式
- [ ] DeadCodeElimination 正确删除不可达块
- [ ] 优化后的 IR 仍通过 IRVerifier 验证
- [ ] 新增 `tests/test_ir_optimizer.py`（25+ 测试）
  - ConstantFolding: 8 个测试
  - DeadCodeElimination: 8 个测试
  - ConstantPropagation: 5 个测试（如果实现）
  - 组合 Pass 测试: 4 个测试

---

## 九、M6：Pipeline 集成 + CLI（v2.0 修正）

### 9.1 v2.0 修正

| 修正点 | v1.0 | v2.0 |
|--------|------|------|
| pipeline.py 复杂度 | 估计 150 行 | 实际 **742 行**，有单文件 `process_file()` 和项目 `compile_project()` 两个入口 |
| 改造范围 | 仅 pipeline.py | pipeline.py + cli.py（两处都有编译入口） |
| IR 插入点 | 未明确 | 单文件：`cli.py:compile_single_file()` 的步骤 3 后；项目模式：`pipeline.py:process_file()` 的步骤 3 后 |

### 9.2 Pipeline 改造（两处入口）

#### 入口 1：单文件模式（`cli.py:compile_single_file`）

```python
# 当前（cli.py:186-194）：
# 3. 代码生成
def run_codegen():
    g = CCodeGenerator()
    return g.generate(ast)

# 改造后：
def run_codegen():
    if self.backend == "ir":
        from .ir.ir_generator import IRGenerator
        from .ir.ir_verifier import IRVerifier
        from .ir.optimizer import PassManager
        from .ir.c_backend import CBackend

        gen = IRGenerator(symbol_table=validator.symbol_table if not self.skip_semantic else None)
        ir = gen.generate(ast)

        if self.dump_ir:
            print(IRPrinter().print(ir))

        verifier = IRVerifier()
        errors = verifier.verify(ir)
        if errors:
            for e in errors:
                print(f"  IR 验证错误: {e}")
            return None  # 或返回错误标记

        if self.optimize:
            pm = PassManager()
            pm.register(ConstantFolding())
            pm.register(DeadCodeElimination())
            ir = pm.run(ir)

        backend = CBackend()
        return backend.generate(ir)
    else:
        g = CCodeGenerator()
        return g.generate(ast)
```

#### 入口 2：项目模式（`pipeline.py:process_file`）

```python
# 在 pipeline.py:process_file() 的步骤 3（语义验证）和步骤 4（C 代码生成）之间插入 IR 层
# 当前 pipeline.py:397-401：
# 4. C 代码生成 (AST → C)
from ..codegen import CCodeGenerator
generator = CCodeGenerator()
c_code = generator.generate(ast)

# 改造后：与单文件模式类似，增加 backend 判断分支
```

### 9.3 CLI 参数（v2.0 修正）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--backend ir\|ast` | `ir` | 选择代码生成后端 |
| `--no-optimize` | 关闭 | 禁用 IR 优化 Pass |
| `--dump-ir` | 关闭 | 打印 IR 到 stdout |
| `-O0` / `-O1` / `-O2` | `-O1` | 优化级别 |
| `--ir-output PATH` | 关闭 | 将 IR 保存到文件（v2.0 改名，避免与 --dump-ir 混淆） |

### 9.4 验收标准（v2.0 修正）

- [ ] Pipeline 单文件和项目模式均支持 `--backend ir` 和 `--backend ast`
- [ ] `--dump-ir` 正确输出 IR 文本
- [ ] `-O0` / `-O1` / `-O2` 正确控制优化级别
- [ ] 现有测试（`--backend ast`）全部通过
- [ ] 新增 IR 路径端到端测试（`tests/test_pipeline_ir.py`，15+ 测试）

---

## 十、M7：测试 + 文档 + 清理（v2.0 扩展）

### 10.1 测试计划（v2.0 修正）

| 测试文件 | v1.0 测试数 | v2.0 测试数 | 覆盖范围 |
|----------|------------|------------|----------|
| `tests/test_ir_symbol.py` | 10+ | **15+** | 统一 Symbol/Scope + 兼容属性 |
| `tests/test_ir_definition.py` | 20+ | **20+** | IR 数据结构定义 |
| `tests/test_ir_generator.py` | 30+ | **35+** | AST→IR 翻译（按 P0-P4 优先级） |
| `tests/test_c_backend.py` | 20+ | **25+** | IR→C 代码生成 + 映射表 |
| `tests/test_ir_verifier.py` | 15+ | **18+** | IR 验证器 + 新增检查项 |
| `tests/test_ir_optimizer.py` | 20+ | **25+** | 优化 Pass |
| `tests/test_pipeline_ir.py` | 10+ | **15+** | Pipeline 集成（单文件 + 项目模式） |
| **新增合计** | **125+** | **153+** | |

### 10.2 技术债务清理（v2.0 新增）

| # | 债务 | 位置 | 修复内容 |
|---|------|------|----------|
| TD1 | `_symbol_lookup_optimizer` 未初始化 | `semantic/semantic_analyzer.py:281` | M0 已修复 |
| TD2 | `performance.py` 过期引用 | `analyzer/performance.py` | 修复 `from ..day2.module_parser` → 正确路径 |
| TD3 | `opt/__init__.py` 未导出两个优化器 | `opt/__init__.py` | 添加 `FunctionInliner` 和 `LoopOptimizer` 导出 |
| TD4 | 5 个 performance 测试被 skip | `tests/` | 修复过期引用后取消 skip |
| TD5 | `scope_checker.py` 旧 Symbol 定义（M0 迁移后） | `analyzer/scope_checker.py` | M0 阶段 B 完成后删除旧定义 |

### 10.3 文档更新

| 文档 | 更新内容 |
|------|----------|
| `ARCHITECTURE.md` | 更新编译流程图，标注 IR 层 |
| Phase 7 执行计划 | 标记完成状态 |
| IR 设计文档（新建） | IR 指令集参考手册 |

### 10.4 验收标准

- [ ] 新增 153+ 测试，全部通过
- [ ] 现有 586+ 测试零回归
- [ ] 技术债务 TD1-TD5 全部修复
- [ ] ARCHITECTURE.md 更新
- [ ] 无 lint 错误

---

## 十一、文件变更总清单（v2.0 修正）

### 新建文件

| 文件 | 里程碑 | 说明 |
|------|--------|------|
| `src/zhpp/ir/__init__.py` | M0 | IR 包入口 |
| `src/zhpp/ir/symbol.py` | M0 | 统一 Symbol + Scope + SymbolCategory |
| `src/zhpp/ir/types.py` | M0 | ZHCTy 类型体系（TypeInfo 别名） |
| `src/zhpp/ir/mappings.py` | M0/M3 | 映射表提取（TYPE_MAP 等 5 个） |
| `src/zhpp/ir/opcodes.py` | M1 | 操作码枚举（30+） |
| `src/zhpp/ir/values.py` | M1 | IRValue, ValueKind |
| `src/zhpp/ir/instructions.py` | M1 | IRInstruction + IRBasicBlock |
| `src/zhpp/ir/program.py` | M1 | IRProgram + IRFunction + IRGlobalVar + IRStructDef |
| `src/zhpp/ir/printer.py` | M1 | IR 文本打印器 |
| `src/zhpp/ir/ir_generator.py` | M2 | AST→IR 生成器 |
| `src/zhpp/ir/c_backend.py` | M3 | IR→C 后端 |
| `src/zhpp/ir/ir_verifier.py` | M4 | IR 验证器 |
| `src/zhpp/ir/optimizer.py` | M5 | PassManager + 3 个优化 Pass |
| `tests/test_ir_symbol.py` | M0 | Symbol 测试 |
| `tests/test_ir_definition.py` | M1 | IR 定义测试 |
| `tests/test_ir_generator.py` | M2 | IR 生成器测试 |
| `tests/test_c_backend.py` | M3 | C 后端测试 |
| `tests/test_ir_verifier.py` | M4 | 验证器测试 |
| `tests/test_ir_optimizer.py` | M5 | 优化器测试 |
| `tests/test_pipeline_ir.py` | M6 | Pipeline 集成测试 |

### 修改文件

| 文件 | 里程碑 | 修改内容 |
|------|--------|----------|
| `src/zhpp/semantic/semantic_analyzer.py` | M0 | Symbol/Scope 导入迁移 + bug 修复（TD1） |
| `src/zhpp/semantic/__init__.py` | M0 | 更新导出（添加兼容别名） |
| `src/zhpp/analyzer/scope_checker.py` | M0 | 删除旧 Symbol/Scope/ScopeCategory 定义，改为导入 |
| `src/zhpp/analyzer/__init__.py` | M0 | 更新导出（兼容层） |
| `src/zhpp/codegen/c_codegen.py` | M3 | 映射表改为从 `ir/mappings.py` 导入 |
| `src/zhpp/compiler/pipeline.py` | M6 | 插入 IR 生成/验证/优化/后端步骤 |
| `src/zhpp/cli.py` | M6 | 新增 CLI 参数 + IR 编译路径 |
| `src/zhpp/analyzer/performance.py` | M7 | 修复过期引用（TD2） |
| `src/zhpp/opt/__init__.py` | M7 | 补全导出（TD3） |
| `ARCHITECTURE.md` | M7 | 更新架构图 |

### 不修改文件

| 文件 | 理由 |
|------|------|
| `src/zhpp/parser/scope.py` | parser 内部使用，不纳入公共 API 统一 |
| `src/zhpp/parser/*.py` | IR 生成器通过 ASTVisitor 访问，不修改 parser |
| `src/zhpp/opt/*.py` | 现有 AST 优化器保持不变，IR 优化器是独立实现 |

---

## 十二、执行顺序与依赖图（v2.0 修正）

```
M0 (Symbol 统一 + bug 修复 + 映射表提取)
 ├── M1 (IR 定义)
 │    ├── M4 (IR 验证器)        ← M2 之前实现，开发过程中边写边验证
 │    ├── M2 (AST→IR 生成器)    ← 核心工作量
 │    ├── M3 (IR→C 后端 + 映射表)  ← 依赖 M1，可与 M2 部分并行
 │    └── M5 (IR 优化 Pass + opt/评估)
 │         └── M6 (Pipeline 集成 + CLI)
 └── M7 (测试 + 技术债务 + 文档)
```

**推荐执行顺序**：M0 → M1 → M4 → M2 → M3 → M5 → M6 → M7

**v2.0 变化**：
- M0 工作量增加（三套 Scope + bug 修复 + 映射表提取），但仍是第一步
- M3 新增映射表提取步骤（M3.0），可与 M1 并行准备
- M5 新增 opt/ 评估步骤（M5.5），在实现优化 Pass 之前完成
- M7 新增技术债务修复（TD1-TD5），纳入验收标准

---

## 十三、风险矩阵（v2.0 修正）

| 风险 | 概率 | 影响 | v2.0 缓解措施 |
|------|------|------|---------------|
| semantic_analyzer.py 迁移破坏 2128 行代码 | **高** | **高** | 分 4 批渐进迁移 + 每批全量测试 |
| AST→IR 翻译遗漏节点 | 中 | 中 | 42 个 visit 方法对照表（§5.3），逐一勾选 |
| IR→C 生成质量下降 | 低 | 中 | CCodeGenerator 作为参照基准 |
| 现有 586+ 测试需要适配 | 中 | 中 | `--backend ast` 兼容路径 |
| 三套 Scope 统一复杂度 | **中** | **高** | parser Scope 不迁移，仅统一 semantic + scope_checker |
| 映射表提取破坏 c_codegen.py | 低 | 中 | 仅改 import 来源，不改变量内容 |
| IR 优化器与现有 opt/ 混淆 | 中 | 低 | 明确文档：`opt/` = AST 级，`ir/optimizer.py` = IR 级 |
| pipeline.py 742 行改造引入 bug | 中 | 中 | 两处入口分别测试 + 端到端测试 |

---

## 十四、Phase 8 展望

Phase 7 完成后，编译器具备：
- 完整的 IR 中间表示层
- AST → IR → 验证 → 优化 → C 五阶段编译
- IR 级优化能力（常量折叠 + 死代码消除 + 可选常量传播）
- IR 合法性验证
- 统一的 Symbol 体系（semantic + scope_checker）
- 独立的映射表模块
- 已清理的技术债务

**Phase 8 候选方向**：
1. **LLVM 后端** — IR → LLVM IR → 机器码（原生性能）
2. **WASM 后端** — IR → WASM（浏览器运行）
3. **高级优化 Pass** — 将 `opt/function_inline.py` 和 `opt/loop_optimizer.py` 移植到 IR 级
4. **模块级 IR 链接** — 多文件编译时的跨模块优化
5. **增量 IR 编译** — 基于已有的 AST 缓存 + 增量更新 → 增量 IR 生成
6. **废弃 AST 直连路径** — 在 IR 路径稳定后，移除 `--backend ast` 兼容模式

---

## 附录 A：代码审查数据来源

本 v2.0 执行计划基于以下代码审查数据：

| 审查项 | 工具 | 覆盖范围 |
|--------|------|----------|
| 项目目录结构 | `search_file` | 120+ 源文件 |
| Scope 定义 | `grep "class\s+Scope\b"` | 4 个定义（3 活跃 + 1 文档） |
| TypeInfo 引用 | `grep "TypeInfo"` | 95+ 匹配，8 个文件 |
| SemanticAnalyzer 实例化 | `grep "SemanticAnalyzer("` | 54+ 匹配，15 个文件 |
| AST 节点类 | `read_file ast_nodes.py` | 37 个具体类 + 5 个类型类 |
| CCodeGenerator visit 方法 | `grep "def\s+visit_"` | 47 个 visit 方法 |
| 映射表定义 | `read_file c_codegen.py` | 5 个映射表（56 个条目） |
| opt/ 模块 | `read_file opt/__init__.py` + 类搜索 | 4 个优化器，2 个未导出 |
| pipeline.py | `read_file pipeline.py` | 742 行，两个编译入口 |
| cli.py | `read_file cli.py` | 376 行，单文件 + 模块项目 |

---

*Phase 7 v2.0 执行计划。基于全量代码库审查优化。等待实施。*

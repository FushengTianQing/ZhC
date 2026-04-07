# Phase 6: 高级分析与类型完善 — 执行计划 v3.0

> 版本：v3.0（完成状态定稿 + Phase 7 IR 规划）
> 创建时间：2026-04-03
> 定稿时间：2026-04-03
> 项目路径：`/Users/yuan/Projects/zhc/`
> 依赖：Phase 5 语义验证（已完成，478 tests passed）

---

## 版本更新说明

### v2.0 → v3.0 变更

| 变更项 | v2.0 | v3.0 | 原因 |
|--------|------|------|------|
| 整体状态 | 执行计划 | **完成定稿** | T0-M5 全部已实施 |
| Phase 6 重新定义 | "高级分析" | **"AST 级高级分析"** | 所有分析均在 AST 上完成，无 IR 层 |
| IR 相关内容 | 推迟到 Phase 7 | **Phase 7 核心规划** | IR 完全不存在（无 ir/ 目录、无 IR 定义、无 IR→C 后端） |
| 新增 §零 | — | **Phase 6 现状盘点** | 如实记录已完成的 6 个里程碑 + 7 个分析器开关 |
| 新增 §十三 | — | **Phase 7 IR 缺口清单** | 5 项完全缺失的基础设施 |

### v1.0 → v2.0 历史变更

| 变更项 | v1.0 | v2.0 | 原因 |
|--------|------|------|------|
| M1 工时 | 6h | 3.5h | Lexer 关键字已全部定义 |
| M2 工时 | 8h | 4.5h | TypeChecker/OverloadResolver 已存在 |
| 总工时 | 24h | 18h | 减少 25% |

---

## 零、Phase 6 实际完成状态

### 0.1 里程碑完成一览

| 里程碑 | 名称 | 状态 | 核心交付 |
|--------|------|------|----------|
| **T0** | 前置修复 | ✅ 完成 | parser.py parse_unary() bug 修复 + synchronize 补充 DO/SWITCH/GOTO |
| **M1** | 类型系统完善与 Parser 补全 | ✅ 完成 | 字符串型/逻辑型注册 + switch/do-while/goto 解析 |
| **M2** | 函数调用参数检查 | ✅ 完成 | _analyze_call_expr + 函数重载解析 + 标准库豁免 |
| **M3** | 控制流分析集成 | ✅ 完成 | cfg_analyzer.py（629行）+ 未初始化检测 + CLI 参数 |
| **M4** | 代码清理与测试巩固 | ✅ 完成 | 旧文件已清理，路径已修复 |
| **M5** | 扩展分析器开关 | ✅ 完成（超出原计划） | 7 个 CLI 开关全链路打通 |

### 0.2 分析器开关完整链路

| CLI 参数 | Analyzer 属性 | 分析方法 | 代码位置 |
|----------|--------------|----------|----------|
| `--no-unreachable` | `cfg_enabled` | `analyze_control_flow()` | semantic_analyzer.py:1435 |
| `--no-uninit` | `uninit_enabled` | `UninitAnalyzer.analyze()` | semantic_analyzer.py:1503 |
| `--no-dataflow` | `dataflow_enabled` | `DataFlowAnalyzer` | semantic_analyzer.py:1613 |
| `--no-interprocedural` | `interprocedural_enabled` | `InterproceduralAnalyzer` | semantic_analyzer.py:1691 |
| `--no-alias` | `alias_enabled` | `AliasAnalyzer` | semantic_analyzer.py:1804 |
| `--no-pointer` | `pointer_enabled` | `PointerAnalyzer` | semantic_analyzer.py:1860 |
| `--optimize-symbol-lookup` | `symbol_lookup_enabled` | `SymbolLookupOptimizer` | semantic_analyzer.py:279 |

### 0.3 编译流程（Phase 6 完成后）

```
单文件模式:
Lexer → Parser → AST → [语义验证+] → CCodeGenerator → C 代码 → clang
                          ├── 符号表构建
                          ├── 作用域分析
                          ├── 未定义/重复定义检测
                          ├── 类型检查 (完善)
                          │   ├── 字符串/布尔类型 ✓
                          │   ├── 函数参数检查 ✓
                          │   ├── 隐式类型转换 ✓
                          │   └── 函数重载解析 ✓
                          ├── 控制流分析 ✓
                          │   ├── 未初始化变量检测
                          │   ├── 不可达代码检测
                          │   ├── 循环复杂度计算
                          │   └── 无限循环检测
                          ├── 内存安全分析 ✓
                          ├── 数据流分析 ✓
                          ├── 过程间分析 ✓
                          ├── 别名分析 ✓
                          ├── 指针分析 ✓
                          └── 未使用符号警告

项目模式 (--project):
AST → [语义验证+（分析器开关已打通）] → C 代码生成 → 依赖分析 → Makefile → clang
```

### 0.4 Phase 6 的本质

**Phase 6 做的是"在 AST 上直接做高级分析"，而非"在 IR 上做分析和优化"。**

这是两个根本不同的架构层级：

| 维度 | Phase 6 实际做法 | 真正的 IR 层做法 |
|------|-----------------|-----------------|
| 分析输入 | AST 节点树 | IR 指令序列 |
| 分析粒度 | 语句级（if/while/for） | 基本块级（load/store/call） |
| 优化能力 | 检测问题，报告警告 | 变换 IR，提升生成代码质量 |
| 后端耦合 | CCodeGenerator 直接读 AST | IR → C 后端读 IR |
| 多后端支持 | 不可能 | IR → C / IR → LLVM / IR → WASM |

Phase 6 没有问题——它的规划明确说了"IR 推迟到 Phase 7"。但 Phase 7 需要面对的事实是：**IR 层完全不存在**。

---

## 一、Phase 5 遗留限制回顾（已全部解决）

| # | 限制 | Phase 6 处理 | 状态 |
|---|------|-------------|------|
| L1 | Parser 不支持 switch/do-while/goto | M1 修复 | ✅ |
| L2 | TypeChecker 未注册字符串型/逻辑型 | M1 修复 | ✅ |
| L3 | 函数调用参数检查缺失 | M2 实现 | ✅ |
| L4 | analyzer/semantic_analyzer.py 旧版 | 已删除 | ✅ |
| L5 | converter/integrated.py 旧路径引用 | 已清理 | ✅ |

---

## 二、Phase 6 里程碑详情（已完成）

### T0: 前置 Bug 修复 ✅

- `parser.py` parse_unary() 重复 advance bug → 已修复
- synchronize() 补充 DO/SWITCH/GOTO → 已补充

### M1: 类型系统完善与 Parser 补全 ✅

- TypeChecker 注册"字符串型"（POINTER, char*, size=8）
- TypeChecker 注册"逻辑型"（PRIMITIVE, _Bool, size=1）
- parse_statement() 新增 switch/do-while/goto/label 分支
- 隐式类型转换规则完善

### M2: 函数调用参数检查 ✅

- `_analyze_call_expr()` 方法（semantic_analyzer.py:802）
- 参数数量 + 类型匹配检查
- 函数重载支持（SymbolTable.add_symbol + _resolve_overload + lookup_all）
- 标准库可变参数函数豁免（zhc_printf/zhc_scanf/zhc_fprintf）

### M3: 控制流分析集成 ✅

- `cfg_analyzer.py`（629 行）— AST→字典适配层 + CFGAnalyzer + UninitAnalyzer
- SemanticAnalyzer 集成 CFG 分析（build_cfg/detect_unreachable_code/compute_cyclomatic_complexity/detect_infinite_loops）
- 未初始化变量使用检测
- CLI 参数：`--no-uninit`、`--no-unreachable`

### M4: 代码清理与测试巩固 ✅

- 旧版 `analyzer/semantic_analyzer.py` 已删除
- `performance.py` / `integrated.py` 路径已清理
- 测试巩固完成

### M5: 扩展分析器开关 ✅（超出原计划）

- 新增 5 个 CLI 参数：`--no-dataflow`、`--no-interprocedural`、`--no-alias`、`--no-pointer`、`--optimize-symbol-lookup`
- CompilationPipeline 传递全链路打通（pipeline.py + cli.py）
- 7 个分析器全部有独立的开关控制

---

## 三、文件修改清单（实际）

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/zhpp/parser/parser.py` | 修改 | bug 修复 + 新增 4 个解析方法 + synchronize 补充 |
| `src/zhpp/analyzer/type_checker.py` | 修改 | 注册字符串型/逻辑型 |
| `src/zhpp/semantic/semantic_analyzer.py` | 修改 | _analyze_call_expr + 重载 + CFG 集成 + 7 分析器开关 |
| `src/zhpp/semantic/cfg_analyzer.py` | **新建** | AST→字典适配层 + CFGAnalyzer + UninitAnalyzer |
| `src/zhpp/cli.py` | 修改 | 7 个 CLI 参数 + 全链路传递 |
| `src/zhpp/compiler/pipeline.py` | 修改 | Pipeline 分析器开关 + 异常处理修复 |

---

## 四、测试结果

- Phase 5 回归测试：478 passed
- Phase 6 语义分析测试：108 passed, 5 skipped
- Pipeline 初始化验证：通过
- Lint 检查：0 errors

---

## 五、Phase 7 IR 缺口清单

Phase 6 执行计划 v2.0 中明确写了"IR 推迟到 Phase 7"。经过全面代码审查，确认 IR 层**完全不存在**：

| # | 缺口 | 详情 |
|---|------|------|
| IR-1 | ZHC IR 定义 | 完全不存在。无 `ir/` 目录，无 IR 指令集定义，无 IR 节点类型 |
| IR-2 | AST → IR 生成器 | 不存在。需要将 AST 节点翻译为 IR 指令序列 |
| IR-3 | IR → C 后端 | 不存在。当前 `CCodeGenerator` 直接从 AST 生成 C 代码 |
| IR-4 | IR 优化 Pass | 不存在。所有优化（CFG、数据流等）都是在 AST 上做的分析，不生成优化后的 IR |
| IR-5 | IR 验证器 | 不存在。无 IR 合法性校验 |

### 当前编译架构 vs 目标 IR 架构

```
当前架构（Phase 6 完成后）:
AST → SemanticAnalyzer（AST 上分析）→ CCodeGenerator（直接读 AST）→ C 代码

目标架构（Phase 7 完成后）:
AST → SemanticAnalyzer（AST 上分析）→ IRGenerator → IR → Optimizer → IR' → CBackend → C 代码
                                                       ↓
                                                  LLVMBackend → LLVM IR → 机器码
```

### Phase 7 IR 工作量预估

| 子任务 | 预估工时 | 说明 |
|--------|----------|------|
| IR 指令集设计 | 8-12h | 定义 ZHC IR 的指令类型、操作数、基本块结构 |
| AST → IR 生成器 | 12-16h | 将所有 AST 节点翻译为 IR |
| IR → C 后端 | 6-8h | 从 IR 生成 C 代码（替代当前的 AST→C） |
| IR 验证器 | 3-4h | 类型检查、SSA 合法性等 |
| IR 优化 Pass 框架 | 4-6h | Pass 管理器 + 基础 Pass（常量折叠、死代码消除） |
| **合计** | **33-46h** | 约 4-6 个工作日 |

---

## 六、风险矩阵（Phase 7 展望）

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| IR 设计不适合多后端 | 中 | 高 | 参考 LLVM IR / CPython bytecode，预留扩展点 |
| AST→IR 翻译不完整 | 中 | 中 | 按节点类型逐个实现，每类节点独立测试 |
| IR→C 生成质量下降 | 低 | 中 | Phase 6 的 CCodeGenerator 作为参照，逐步替换 |
| 现有 478+ 测试需要适配 | 高 | 中 | 保持 AST 路径兼容，IR 路径作为可选后端 |
| 两套后端并行维护成本 | 中 | 中 | Phase 7 完成后逐步废弃 AST→C 路径 |

---

## 七、Phase 7 展望

Phase 6 完成后，编译器具备：
- 完善的类型系统（字符串/布尔/隐式转换/重载）
- 完整的函数参数检查（数量 + 类型 + 重载解析）
- 6 种 AST 级分析（CFG/未初始化/数据流/过程间/别名/指针）
- 全面的中文关键字覆盖
- 7 个独立的分析器开关（CLI → Pipeline → Analyzer 全链路）

Phase 7 核心任务——**IR 层建设**：
1. **ZHC IR 设计** — 指令集定义、基本块、函数表示
2. **AST → IR 生成器** — 替代当前的 AST → C 直连路径
3. **IR → C 后端** — 从 IR 生成高质量 C 代码
4. **IR 优化 Pass** — 常量折叠、死代码消除、循环优化
5. **IR 验证器** — 合法性校验
6. **Symbol 体系统一** — 合并 semantic.Symbol 和 analyzer/scope_checker.Symbol
7. **多文件模块级语义验证** — 模块间符号导入/导出

---

*Phase 6 v3.0 完成定稿。Phase 6 所有里程碑已实施完毕，等待 Phase 7 IR 层规划。*

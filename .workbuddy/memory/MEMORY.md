# ZhC 项目长期记忆

## 项目概况
- **ZhC**: 中文编程语言编译器（ZHC = 中文C）
- **包名**: zhc（内部导入用 `from zhc.xxx`）
- **源码结构**: src/ 目录作为 zhc 包根，通过 __main__.py 入口运行
- **GitHub**: https://github.com/FushengTianQing/ZhC (private, main分支)
- **质量评分**: 70/100 [B+中等偏上] (2026-04-08)

## 核心架构
- **编译流水线**: 词法(Lexer) → 语法(Parser) → 语义(Semantic/Analyzer) → IR → Codegen(C/LLVM/WASM)
- **核心模块**: parser, semantic, analyzer, ir, codegen
- **高级特性**: 泛型(generics), 模板(template), 增量AST, 并行编译
- **设计模式**: ASTVisitor, dispatch table, 状态机, 命令模式, 工厂方法, Dataclass

## 重要发现
1. **模块导入**: `from zhc.xxx` 导入需要将 src/ 注册到 sys.modules
2. **测试框架**: pytest 测试中每个 Test 类可能有独立 setup 方法
3. **开发工具路径**: Black/Ruff/Pytest 在 `/Users/yuan/Library/Python/3.9/bin/`

## Phase 3 工程化建设 (2026-04-07 ~ 2026-04-08)
- **文档体系**: Sphinx 文档系统、API 参考、开发者指南、架构文档
- **DevOps 流程**: CI/CD 增强、Issue/PR 模板、自动化发布、CHANGELOG 自动化
- **示例代码**: 7 个完整示例

## Phase 4 高级能力建设 (2026-04-08)

### Stage 1: 编译器优化技术 ✅ 已完成
- Task 8.1: SSA 构建实现（支配树、Phi 节点）
- Task 8.2: 数据流分析框架（活跃变量、到达定义、可用表达式）
- Task 8.3: 循环优化（LICM、强度削减）
- Task 8.4: 内联优化（成本模型、函数内联）

### Stage 2: 高级语言特性 ✅ 已完成
- Task 11.1: 泛型编程支持（113 passed）
- Task 11.2: 模式匹配实现（87 passed）
- Task 11.3: 异步编程支持（79 passed）

### Stage 3: 工具链生态 ✅ 已完成
- Task 14.1: Language Server Protocol 实现（65 passed）
- Task 14.2: 调试信息生成（40 passed）
- Task 14.3: 静态分析框架

## 新增模块 (2026-04-08)
- `src/ir/ssa.py` - SSA 构建
- `src/ir/dominator.py` - Lengauer-Tarjan 支配树算法 (O(N α(N)))
- `src/ir/dataflow.py` - 数据流分析
- `src/ir/loop_optimizer.py` - 循环优化
- `src/ir/inline_optimizer.py` - 内联优化
- `src/ir/register_allocator.py` - 寄存器分配算法（线性扫描、图着色）✅ 已从 codegen 迁移
- `src/analyzer/interprocedural_alias.py` - 过程间别名分析（已合并 alias_analysis.py）
- `src/backend/` - 后端模块 ✅ 新建
  - `__init__.py` - 后端模块初始化
  - `allocator_interface.py` - 统一寄存器分配接口（支持多后端）
- `src/codegen/register_allocator.py` - 废弃包装器（向后兼容）
- `src/codegen/allocator_interface.py` - 废弃包装器（向后兼容）
- `src/utils/` - 工具模块（file_utils, string_utils, error_utils）
- `src/semantic/generics.py` - 泛型类型系统
- `src/semantic/pattern_matching.py` - 模式匹配系统
- `src/semantic/async_system.py` - 异步编程系统
- `src/lsp/` - LSP 协议实现
- `src/debug/` - DWARF 调试信息生成

## 寄存器分配器新架构 (2026-04-08)
- **IR 层** (`zhc.ir.register_allocator`): 线性扫描、图着色等核心算法
- **后端层** (`zhc.backend.allocator_interface`): 统一 API，支持 x86-64/ARM64/WASM/LLVM
- **废弃模块** (`zhc.codegen.*`): 仅用于向后兼容，会触发 DeprecationWarning

## 已删除模块 (2026-04-08)
- `src/analyzer/alias_analysis.py` - 已合并到 `interprocedural_alias.py`

## 用户偏好
- **远**: 项目负责人，关注代码质量和团队技术提升
- 工作日期: 初次见面 2026-04-01

## LLVM & WASM 后端集成方案
- **文档**: `docs/LLVM_WASM_BACKEND_INTEGRATION_PLAN.md`
- **LLVM 技术选型**: `llvmlite>=0.39.0`（LLVM 12 绑定）
- **WASM 技术选型**: `wasm-tools`（Rust 实现）+ Python subprocess
- **现状差距**:
  - `LLVMPrinter`（`src/ir/llvm_backend.py`）仅为文本生成器，输出 .ll 文本而非真正 bitcode
  - `WASMBackend`（`src/backend/wasm_backend.py`）仅为 Emscripten wrapper，非原生 WASM 生成
  - `llvm_backend.py` 有 bug：第 142/152 行引用 `Instruction` 应为 `IRInstruction`
- **实施计划**: 阶段1(LLVM, 1-2周) → 阶段2(WASM原生, 3-5周) → 阶段3(集成, 6周)

## 测试覆盖 (2026-04-08)
- **本周新增测试**: 
  - `tests/test_dataflow.py` - 33 passed
  - `tests/test_loop_optimizer.py` - 25 passed
  - `tests/test_inline_optimizer.py` - 31 passed
  - `tests/test_utils.py` - 39 passed
  - `tests/test_dominator.py` - 20 passed (Lengauer-Tarjan 算法)
  - `tests/benchmarks/test_dominator_performance.py` - 5 passed (性能对比)
  - `tests/test_alias_analysis.py` - 24 passed (过程间别名分析)
- **CI 覆盖率门禁**: 15% → 25% (本周更新)

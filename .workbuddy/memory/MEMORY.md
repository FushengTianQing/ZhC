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
- `src/ir/loop_unroller.py` - 循环展开优化 ✅ 新增
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

## C 重写方案分析 (2026-04-08)
- 报告路径: `docs/C重写方案分析报告.md`
- 结论: 不建议全量重写，建议增量 C 扩展（lexer + IR 优化层）
- 工期: 8 周（分 5 阶段）
- 技术选型: CFFI（非 Python C API）

## LLVM & WASM 后端集成方案 (2026-04-08)

### 技术选型
- **LLVM**: `llvmlite>=0.39.0`（LLVM 12 绑定）
- **WASM**: `wasm-tools`（Rust 实现）+ Python subprocess

### 现状差距
- `LLVMPrinter`（`src/ir/llvm_backend.py`）仅为文本生成器，输出 .ll 文本而非真正 bitcode
- `WASMBackend`（`src/backend/wasm_backend.py`）仅为 Emscripten wrapper，非原生 WASM 生成
- `llvm_backend.py` 有 bug：第 142/152 行引用 `Instruction` 应为 `IRInstruction`

### LLVM 集成详细方案（5 阶段，约 9.5 天）
1. **阶段 1**: 修复 LLVMPrinter bug（0.5 天）
   - `src/ir/llvm_backend.py` 第 142/152 行：`Instruction` → `IRInstruction`

2. **阶段 2**: 实现 LLVMBackend 类（3 天）
   - 创建 `src/backend/llvm_backend.py`
   - 使用 llvmlite API 生成真正的 LLVM IR
   - 支持 bitcode 输出和 JIT 执行

3. **阶段 3**: 类型映射（1 天）
   - ZhC 类型 → LLVM 类型映射表
   - 整数、浮点、数组、结构体、指针

4. **阶段 4**: 指令生成（2 天）
   - ZhC IR Opcode → LLVM IR 指令映射
   - 算术、逻辑、控制流、函数调用

5. **阶段 5**: JIT 执行（2 天）
   - 实现即时执行引擎
   - CLI 接口：`zhc --llvm --jit program.zhc`

### 目录结构
```
src/backend/
├── llvm_backend.py      # LLVM 后端主类
├── llvm_type_mapper.py  # 类型映射
├── llvm_instruction.py  # 指令生成
└── llvm_jit.py          # JIT 执行引擎
```

### WASM 集成方案（阶段 2，3-5 周）
- 原生 WASM 生成（不依赖 Emscripten）
- 使用 `wasm-tools` 进行二进制编码
- 支持 WASM MVP 特性

### 实施计划
- 阶段 1: LLVM 集成（1-2 周）
- 阶段 2: WASM 原生生成（3-5 周）
- 阶段 3: 集成测试（6 周）

### 关键架构认知
- **C Backend 不是真正的后端**: `c_backend.py` 和 `c_codegen.py` 都是代码生成器，需要 gcc/clang 才能生成机器码
- **LLVM 后端架构**: 前端 → IR → 中间优化 → 后端（指令选择 → 寄存器分配 → 代码发射）
- **GCC vs LLVM**: LLVM 模块化、现代架构、活跃社区，更适合新项目集成

## 测试覆盖 (2026-04-08)
- **本周新增测试**: 
  - `tests/test_dataflow.py` - 33 passed
  - `tests/test_loop_optimizer.py` - 25 passed
  - `tests/test_loop_unroller.py` - 20 passed ✅ 新增
  - `tests/test_inline_optimizer.py` - 31 passed
  - `tests/test_utils.py` - 39 passed
  - `tests/test_dominator.py` - 20 passed (Lengauer-Tarjan 算法)
  - `tests/benchmarks/test_dominator_performance.py` - 5 passed (性能对比)
  - `tests/test_alias_analysis.py` - 24 passed (过程间别名分析)
  - `tests/test_ast_validator.py` - 35 passed (AST 验证器)
  - `tests/test_memory_safety.py` - 34 passed (内存安全)
- **CI 覆盖率门禁**: 15% → 25% (本周更新)

## P2 级别任务进度 (2026-04-08)
- ✅ TASK-P2-001: AST 验证器 - 已完成
  - 文件: `src/parser/ast_validator.py`, `tests/test_ast_validator.py`
  - 功能: 结构完整性、类型一致性、语义约束、边界条件检查
  - 覆盖率: 89.52%
- ✅ TASK-P2-002: 内存安全检查测试 - 已完成
  - 文件: `tests/test_memory_safety.py`
  - 功能: 空指针检查、内存泄漏、缓冲区溢出、释放后使用、所有权追踪、生命周期分析
  - 测试: 34 passed
- ✅ TASK-P2-003: 循环展开优化 - 已完成
  - 文件: `src/ir/loop_unroller.py`, `tests/test_loop_unroller.py`
  - 功能: 完全展开、部分展开、展开决策分析
  - 测试: 20 passed
- ✅ TASK-P2-004: 调试信息生成 - 已完成
  - 文件: `src/debug/debug_generator.py`, `src/codegen/c_debug_listener.py`, `src/debugger/gdb_zhc.py`
  - 功能: DWARF 行号/变量/类型信息生成、GDB/LLDB 调试支持
  - 测试: 40 passed

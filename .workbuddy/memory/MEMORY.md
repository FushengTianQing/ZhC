# ZhC 项目长期记忆

## 项目概况
- **ZhC**: 中文编程语言编译器（ZHC = 中文C）
- **包名**: zhpp（内部导入用 `from zhpp.xxx`），pyproject.toml 中声明为 zhc
- **源码结构**: src/ 目录作为 zhpp 包根，通过 __main__.py 入口运行 (`python -m src.__main__`)
- **GitHub**: https://github.com/FushengTianQing/ZhC (private, main分支)
- **质量评分**: 70/100 [B+中等偏上] (2026-04-08)

## 关键技术架构
- **编译流水线**: 词法(Lexer) → 语法(Parser) → 语义(Semantic/Analyzer) → IR → Codegen(C/LLVM/WASM)
- **核心模块**: parser, semantic, analyzer(类型/作用域/重载/数据流/控制流/内存安全), ir, codegen
- **高级特性**: 泛型(generics), 模板(template), 增量AST, 并行编译
- **设计模式**: ASTVisitor, dispatch table, 状态机, 命令模式, 工厂方法, Dataclass

## 重要发现与解决方案
1. **模块导入问题**: `from zhpp.xxx` 导入需要将 src/ 注册为 sys.modules["zhpp"]。conftest.py 和 __main__.py 都必须做此注册。
2. **测试框架**: pytest 测试中每个 Test 类可能有独立 setup 方法，修复时需检查所有类而非只改模块级配置。
3. **SemanticAnalyzer 已迁移**: 从 zhpp.analyzer 迁移到 zhpp.semantic，API 也从 analyze_xxx() 改为统一 analyze() 入口。
4. **开发工具路径**: Black/Ruff/Pytest 在 `/Users/yuan/Library/Python/3.9/bin/`，系统 Python 是 `/usr/bin/python3` (3.9.6)

## 用户偏好
- 远: 项目负责人，关注代码质量和团队技术提升
- 工作日期: 初次见面 2026-04-01

## Week 5 重构成果（2026-04-07 ~ 2026-04-08）
- **质量评分**: 65/100 → 70/100 (+5) ✅
- **圈复杂度**: 9.5 → 8.0 (-1.5) ✅
- **高复杂度函数**: 36 → 33 (-3) ✅
- **平均函数长度**: 47.3 → 42.3 (-5.0) ✅
- **测试通过**: 1064 passed ✅
- **覆盖率**: 51.86%（下降，需补充测试）

**重构模式应用**:
- Dispatch Table 模式（optimizer, ir_generator）
- 状态机模式（class_extended）
- 命令模式（cli/main）
- 工厂方法模式（cli）
- Dataclass 模式（config, error）

**新增模块**:
- `src/api/` - API 模块（CompilationResult, CompilationStats）
- `src/utils/` - 工具模块（file_utils, string_utils, error_utils）

**详细报告**: `docs/WEEK5_REFACTOR_SUMMARY.md`

## Phase 3 工程化建设成果（2026-04-08）
- **文档体系**: Sphinx 文档系统、API 参考、开发者指南、架构文档
- **DevOps 流程**: CI/CD 增强、Issue/PR 模板、自动化发布、CHANGELOG 自动化
- **示例代码**: 6 个完整示例（hello, functions, classes, generic, template, package_manager）

**Week 6 文档体系**:
- Sphinx 文档配置（autodoc, napoleon, myst_parser）
- 架构文档更新（Mermaid 图表：流水线、依赖关系、数据流）
- 开发者指南（环境搭建、代码规范、测试、调试、FAQ）
- 贡献指南（CONTRIBUTING.md，含 Issue/PR 模板）
- 示例代码完善（examples/README.md + 3 个新示例）

**Week 7 DevOps 流程**:
- CI/CD 增强（缓存策略、并行测试、安全扫描、文档构建）
- Issue 模板（bug_report, feature_request, question）
- PR 模板（检查清单、破坏性变更说明）
- 发布工作流（release.yml，版本检查、CHANGELOG 生成）
- CHANGELOG 自动化（generate_changelog.py，支持 conventional commits）

**详细计划**: `docs/PHASE3_TASK_PLAN.md`

## Phase 4 高级能力建设规划（2026-04-08）
- **文档位置**: `docs/PHASE4_TASK_PLAN.md`
- **计划周期**: 2026-04-15 ~ 2026-07-15（3个月）
- **三个方向**: 编译器优化、高级语言特性、工具链生态

**Stage 1 (Week 8) - 编译器优化技术 ✅ 已完成**:
- Task 8.1: SSA 构建实现 ✅
  - 支配树、支配边界、Phi 节点、变量重命名
  - 18 个单元测试全部通过
- Task 8.2: 数据流分析框架 ✅
  - 活跃变量分析、到达定义分析、可用表达式分析
- Task 8.3: 循环优化实现 ✅
  - 自然循环检测、循环不变代码外提、强度削减
- Task 8.4: 内联优化 ✅
  - 内联成本模型、函数内联器

**Stage 2 (Week 11-13) - 高级语言特性**:
- Task 11.1: 泛型编程支持（4天）
- Task 11.2: 模式匹配实现（3天）
- Task 11.3: 异步编程支持（3天）

**Stage 3 (Week 14-16) - 工具链生态**:
- Task 14.1: Language Server Protocol 实现（5天）
- Task 14.2: 调试信息生成（3天）
- Task 14.3: 静态分析框架（3天）

**新增模块** (2026-04-08):
- `src/ir/ssa.py` - SSA 构建（支配树、Phi 节点）
- `src/ir/dataflow.py` - 数据流分析（活跃变量、到达定义、可用表达式）
- `src/ir/loop_optimizer.py` - 循环优化（LICM、强度削减）
- `src/ir/inline_optimizer.py` - 内联优化（成本模型、函数内联）
- `src/semantic/generics.py` - 泛型类型系统（TypeParameter, GenericType, GenericFunction, TypeConstraint）
- `src/semantic/generic_parser.py` - 泛型语法解析（TypeNode, GenericTypeDeclNode, GenericFunctionDeclNode）
- `src/semantic/generic_instantiator.py` - 泛型实例化（类型/函数实例化、类型推导）
- `src/codegen/generic_codegen.py` - 泛型代码生成（名字修饰、单态化）
- `src/semantic/pattern_matching.py` - 模式匹配系统（9 种模式类型、PatternMatcher）
- `src/semantic/pattern_parser.py` - 模式匹配语法解析器（PatternParser）

## Phase 4 Stage 2 - 高级语言特性（2026-04-08）
- **文档位置**: `docs/PHASE4_TASK_PLAN.md`
- **计划周期**: 2026-04-15 ~ 2026-07-15（3个月）
- **三个方向**: 编译器优化、高级语言特性、工具链生态

**Stage 1 (Week 8) - 编译器优化技术 ✅ 已完成**:
- Task 8.1: SSA 构建实现 ✅
  - 支配树、支配边界、Phi 节点、变量重命名
  - 18 个单元测试全部通过
- Task 8.2: 数据流分析框架 ✅
  - 活跃变量分析、到达定义分析、可用表达式分析
- Task 8.3: 循环优化实现 ✅
  - 自然循环检测、循环不变代码外提、强度削减
- Task 8.4: 内联优化 ✅
  - 内联成本模型、函数内联器

**Stage 2 (Week 11-13) - 高级语言特性 ✅ 已完成**:
- Task 11.1: 泛型编程支持 ✅
  - Day 1: 泛型类型系统设计（generics.py, GENERICS_DESIGN.md）
  - Day 2: 泛型解析（lexer.py 扩展, generic_parser.py）
  - Day 3: 泛型实例化（generic_instantiator.py）
  - Day 4: 代码生成（generic_codegen.py）
  - 测试覆盖: 113 passed
- Task 11.2: 模式匹配实现 ✅
  - Day 1: 模式匹配语法设计（pattern_matching.py, pattern_parser.py, lexer.py 扩展）
  - Day 2: 模式匹配语义分析（pattern_analyzer.py）
  - Day 3: 模式匹配代码生成（pattern_codegen.py）
  - 测试覆盖: 87 passed
- Task 11.3: 异步编程支持 ✅
  - Day 1: 异步语法设计（async_parser.py, async_system.py）
  - Day 2: 异步语义分析（async_analyzer.py）
  - Day 3: 异步代码生成（async_codegen.py）
  - 测试覆盖: 79 passed

**泛型系统设计** (2026-04-08):
- **核心类**: TypeParameter, GenericType, GenericFunction, TypeConstraint
- **预定义约束**: 可比较、可相等、可加、可打印、数值型
- **语法支持**: `泛型类型 列表<类型 T>`, `泛型函数 T 最大值<类型 T: 可比较>`
- **实例化**: GenericInstantiator, InstantiationContext, GenericTypeInferrer
- **代码生成**: NameMangler（名字修饰）, GenericCodeGenerator（单态化）
- **测试覆盖**: 113 个测试用例全部通过（24+34+21+34）

**模式匹配系统设计** (2026-04-08):
- **核心类**: Pattern 基类 + 9 种具体模式
- **模式类型**: 通配符(_)、变量(x)、字面量(42/"hello")、构造器(Some(x))、解构(点{x,y})、范围(1..10)、元组((x,y))、或(|)、与(&)、守卫(当)
- **语法解析器**: PatternParser（pattern_parser.py）
- **语义分析**: PatternAnalyzer（pattern_analyzer.py）
- **代码生成**: PatternCodeGenerator（pattern_codegen.py）
- **测试覆盖**: 87 个测试用例全部通过（55+32）
- **新增文件**: src/semantic/pattern_matching.py, src/semantic/pattern_parser.py, src/semantic/pattern_analyzer.py

**异步编程系统设计** (2026-04-08):
- **核心类**: AsyncFunctionType, FutureType, AsyncAnalyzer
- **语法支持**: `异步 函数`, `等待`, `承诺`, `未来型`
- **解析器**: AsyncParser（async_parser.py）
- **语义分析**: AsyncAnalyzer（async_system.py）
- **代码生成**: AsyncCodeGenerator（async_codegen.py）
- **测试覆盖**: 79 个测试用例全部通过（17+30+32）
- **新增文件**: src/semantic/async_parser.py, src/semantic/async_system.py

## Phase 4 Stage 3 - 工具链生态（2026-04-08）

**Task 14.1: Language Server Protocol 实现 ✅ 已完成**

**Day 1: LSP 协议实现**:
- `src/lsp/protocol.py` - LSP 协议类型定义
- `src/lsp/jsonrpc.py` - JSON-RPC 2.0 实现
- `src/lsp/server.py` - Language Server 主实现
- 65 个单元测试全部通过

**Day 2: 代码补全**:
- Document 符号表解析（函数、结构体、类、枚举、变量）
- 上下文分析（类型声明、成员访问、点操作符）
- 代码补全增强（类型补全、成员补全、方法补全）
- 符号表实时更新

**Day 3: 诊断和悬停**:
- 悬停功能增强（符号表信息、关键字文档）
- 诊断功能增强（词法错误、括号匹配、语法结构、未使用变量检查）

**Day 4: 导航和重构**:
- 转到定义（符号表查找）
- 查找引用（所有出现位置）
- 重命名（生成所有引用更改）

**Day 5: VSCode 扩展和文档**:
- `editors/vscode/` - VSCode 扩展（package.json, extension.ts, 语法高亮）
- `docs/LSP_GUIDE.md` - LSP 使用指南

**LSP 模块文件**:
- `src/lsp/__init__.py` - 模块入口
- `src/lsp/protocol.py` - 协议类型（Position, Range, Diagnostic, CompletionItem, Hover 等）
- `src/lsp/jsonrpc.py` - JSON-RPC 通信（JSONRPCServer, JSONRPCClient, Transport）
- `src/lsp/server.py` - Language Server（代码补全、诊断、悬停、导航、重命名）

**测试文件**:
- `tests/test_lsp_protocol.py` - 26 个协议类型测试
- `tests/test_lsp_jsonrpc.py` - 16 个 JSON-RPC 测试
- `tests/test_lsp_server.py` - 23 个服务器测试
- **总计**: 65 个测试全部通过

**Task 14.2: 调试信息生成 ✅ 已完成**

**Day 1: DWARF 格式研究**:
- `src/debug/debug_generator.py` (998行) - DWARF 调试信息生成器
  - DW_TAG, DW_AT, DW_FORM, DW_LANG, DW_OP 枚举
  - 数据类: SourceLocation, AddressRange, CompileUnit
  - 核心类: LineNumberTable, DebugSymbolTable, TypeInfoGenerator, DWARFGenerator, DebugInfoGenerator
  - 完整的中文符号支持

**Day 2-3: 调试信息生成和集成**:
- 模块整合：发现并解决 `src/codegen/debug_info.py` 和 `src/debug/debug_generator.py` 重复问题
- 创建 `src/codegen/debug_integration.py` - 集成层（DebugInfoManager）
- 更新编译器配置：DebugConfig 类，debug_enabled 属性
- 更新 CLI：`-g/--debug` 命令行参数
- 更新 CCodeGenerator：集成 debug_manager

**Day 4: 事件驱动架构重构**:
- 创建 `src/debug/debug_listener.py` - DebugListener 协议接口
- 创建 `src/debug/debug_manager.py` - DebugManager 事件管理器
- 重构 `DebugInfoManager` 为 `CDebugListener`（`src/codegen/c_debug_listener.py`）
- 更新 CCodeGenerator 使用事件驱动方式
- 删除旧的 `src/codegen/debug_integration.py`

**调试信息模块文件**:
- `src/debug/debug_generator.py` - DWARF 调试信息生成器（核心，998行）
- `src/debug/debug_listener.py` - DebugListener 协议接口
- `src/debug/debug_manager.py` - DebugManager 事件管理器
- `src/codegen/c_debug_listener.py` - C 后端调试监听器
- `tests/test_debug_generator.py` - 22 个调试信息测试
- `tests/test_debug_event_driven.py` - 18 个事件驱动架构测试
- `docs/DEBUG_GUIDE.md` - 调试指南（GDB/LLDB 使用）
- `examples/debug_example.zhc` - 调试示例程序
- **总计**: 40 个测试全部通过

**架构优势**:
- 支持多后端扩展（C、LLVM、WASM）
- 统一事件接口，易于添加新后端
- 解耦编译器与调试信息生成

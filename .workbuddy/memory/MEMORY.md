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

**Stage 2 (Week 11-13) - 高级语言特性 🚧 进行中**:
- Task 11.1: 泛型编程支持 ✅ Day 1-2 完成
  - Day 1: 泛型类型系统设计（generics.py, GENERICS_DESIGN.md）
  - Day 2: 泛型解析（lexer.py 扩展, generic_parser.py）
  - Day 3: 泛型实例化（类型/函数实例化）
  - Day 4: 代码生成（单态化实现）
- Task 11.2: 模式匹配实现（3天）
- Task 11.3: 异步编程支持（3天）

**泛型系统设计** (2026-04-08):
- **核心类**: TypeParameter, GenericType, GenericFunction, TypeConstraint
- **预定义约束**: 可比较、可相等、可加、可打印、数值型
- **语法支持**: `泛型类型 列表<类型 T>`, `泛型函数 T 最大值<类型 T: 可比较>`
- **测试覆盖**: 58 个测试用例全部通过

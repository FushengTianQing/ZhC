# ZhC 项目长期记忆

## 项目概况
- **ZhC**: 中文编程语言编译器（ZHC = 中文C）
- **包名**: zhpp（内部导入用 `from zhpp.xxx`），pyproject.toml 中声明为 zhc
- **源码结构**: src/ 目录作为 zhpp 包根，通过 __main__.py 入口运行 (`python -m src.__main__`)
- **GitHub**: https://github.com/FushengTianQing/ZhC (private, main分支)
- **质量评分**: 65/100 [B中等] (2026-04-07)

## 关键技术架构
- **编译流水线**: 词法(Lexer) → 语法(Parser) → 语义(Semantic/Analyzer) → IR → Codegen(C/LLVM/WASM)
- **核心模块**: parser, semantic, analyzer(类型/作用域/重载/数据流/控制流/内存安全), ir, codegen
- **高级特性**: 泛型(generics), 模板(template), 增量AST, 并行编译
- **设计模式**: ASTVisitor, dispatch table (c_backend.py重构后), CompilerConfig (cli.py重构后)

## 重要发现与解决方案
1. **模块导入问题**: `from zhpp.xxx` 导入需要将 src/ 注册为 sys.modules["zhpp"]。conftest.py 和 __main__.py 都必须做此注册。
2. **测试框架**: pytest 测试中每个 Test 类可能有独立 setup 方法，修复时需检查所有类而非只改模块级配置。
3. **SemanticAnalyzer 已迁移**: 从 zhpp.analyzer 迁移到 zhpp.semantic，API 也从 analyze_xxx() 改为统一 analyze() 入口。
4. **开发工具路径**: Black/Ruff/Pytest 在 `/Users/yuan/Library/Python/3.9/bin/`，系统 Python 是 `/usr/bin/python3` (3.9.6)

## 用户偏好
- 远: 项目负责人，关注代码质量和团队技术提升
- 工作日期: 初次见面 2026-04-01

## Week 5 重构计划（2026-04-07）
- **目标**: 降低圈复杂度，消除代码重复，改善API设计，提升类型注解覆盖率
- **高复杂度函数**: 36个（目标 <20）
- **平均圈复杂度**: 8.5（目标 <8）
- **类型注解覆盖率**: ~40%（目标 90%+）
- **重构优先级**: P0(optimizer/ir_generator/class_extended/cli/main) → P1(长函数) → P2(大文件拆分)
- **详细计划**: `docs/REFACTOR_PRIORITY_LIST.md`

# 下一步计划：P1 单元测试 + P2 重构

**日期**: 2026-04-07  
**状态**: 规划中  
**基于**: 质量评估 60/100 [B中等]，P0 已完成，P1/P2 测试已修复通过 (124 tests)

---

## 当前状态总结

### ✅ 已完成
- P0 语义分析修复 — 全部通过
- P1/P2 性能优化模块 — 5个测试文件重写为 pytest 格式（124 passed）
- cli.py / c_backend.py 重构 — 复杂度显著降低
- 测试框架统一修复 — conftest.py + 导入路径统一

### 📊 当前测试覆盖情况

| 模块 | 文件 | 现有测试数 | 覆盖率估计 | 缺失的关键功能 |
|------|------|-----------|-----------|---------------|
| **ir_generator** | test_ir_generator.py | 9 (~30%) | ~30% | for/do-while/switch/break-continue/嵌套控制流/三元表达式/函数调用 |
| **parser** (parser.py) | test_parser.py | ~20 | ~25% | do-while/switch/goto/label/函数指针声明/typedef/复杂表达式链/错误恢复边界 |
| **optimizer** (compiler/) | test_optimizer_enhanced.py + test_ir_optimizer.py | ~30 | ~40% | IncrementalOptimizer完整流程/ConcurrentCompiler线程安全/get_affected_files级联 |

---

## P1: 为高复杂度模块编写单元测试

### 目标
将 ir_generator、parser、optimizer 的核心模块测试覆盖率从 **30% 提升到 70%+**

### 1.1 `test_ir_generator.py` 扩展 (+35 tests)

**当前**: 9 个基础测试（空程序、函数、if、while、二元表达式等）

**新增测试类**:

| 测试类 | 目标数 | 覆盖功能 |
|--------|--------|---------|
| `TestEvalExpr` | 12 | _eval_expr 的每种字面量(INT/FLOAT/STRING/CHAR/BOOL/NULL)、二元表达式(+-*/%)、一元表达式(NEG/NOT)、赋值、函数调用、成员访问、数组访问、三元表达式、类型转换 |
| `TestForLoopIR` | 8 | for循环的4个基本块结构、update块正确性、break/continue目标栈、嵌套for、空body、无初始化/无条件 |
| `TestDoWhileLoopIR` | 5 | do-while的3个基本块、条件在body之后、break/continue正确性 |
| `TestSwitchIR` | 4 | switch的基本块结构、case处理、break目标、default |
| `TestBreakContinue` | 6 | 单层break/continue、嵌套循环中break/continue、switch中break、无目标时行为 |
| `TestFunctionDetails` | 5 | 参数→PARAM指令、返回类型、主函数名映射、多函数程序、全局变量ALLOC |
| `TestNestedControlFlow` | 4 | if+while嵌套、for+if嵌套、多重else、深层嵌套(3层+) |
| `TempVariableGeneration` | 3 | 临时变量计数递增、不同类型temp、跨block不重复 |

**预计新增**: ~47 个测试 → 总计 ~56 个

### 1.2 `test_parser.py` 扩展 (+40 tests)

**当前**: ~20 个测试（lexer基础 + parser基础 + 错误恢复）

**新增测试类**:

| 测试类 | 目标数 | 覆盖功能 |
|--------|--------|---------|
| `TestDoWhileParsing` | 4 | do-while完整语法、缺当关键字恢复、缺分号恢复 |
| `TestSwitchParsing` | 5 | switch-case-default完整语法、case语句体、default位置 |
| `TestGotoLabelParsing` | 3 | goto标签、label声明、前后向引用 |
| `TestFunctionPointer` | 5 | 函数指针声明 `整数型 (*名字)(参数)`、作为变量类型、作为参数类型、多层指针 |
| `TestTypedefParsing` | 3 | typedef别名声明、用于变量类型、链式typedef |
| `TestComplexExpressions` | 8 | 优先级正确性：`a+b*c` vs `(a+b)*c`、赋值右结合、后缀++/--、成员访问链 `obj.member`、数组 `arr[i][j]`、函数调用 `f(a)(b)`、类型转换 `(int)x` |
| `TestUnionEnumParsing` | 3 | 共用体声明、匿名枚举、枚举值带初始值 |
| `ErrorRecoveryEdgeCases` | 6 | 连续错误恢复、嵌套结构中错误、缺失右大括号、异常token在表达式内、错误累积不崩溃 |
| `TestParseTypeSystem` | 6 | 基本类型(12种)、指针类型(多级*)、数组类型、函数类型、结构体类型、自定义类型标识符 |

**预计新增**: ~43 个测试 → 总计 ~63 个

### 1.3 `test_compiler_optimizer.py` 新建 (+30 tests)

**注意**: 现有 test_optimizer_enhanced.py 测试的是 `zhpp.opt.*` 模块（死代码消除/常量传播），而 `src/compiler/optimizer.py` 是**另一个** optimizer（PerformanceMonitor/AlgorithmOptimizer/IncrementalOptimizer/ConcurrentCompiler），目前**几乎无 pytest 测试**！

**新增测试文件: `tests/test_compiler_optimizer.py`**

| 测试类 | 目标数 | 覆盖功能 |
|--------|--------|---------|
| `TestPerformanceMonitor` | 8 | 阶段计时(start/end)、内存记录(psutil可用/不可用)、CPU使用率、get_summary结构、print_report输出、多阶段累计 |
| `TestAlgorithmOptimizer` | 10 | 依赖图压缩(传递闭包)、节点层级计算(BFS拓扑)、冗余依赖移除、层级排序、环形依赖、空图、单节点、链状图、星状图 |
| `TestConcurrentCompiler` | 5 | 线程池并发编译、进程池模式、异常任务不影响其他、空文件列表、结果字典完整性 |
| `TestIncrementalOptimizer` | 8 | 文件变更检测(mtime对比)、新增/修改/未变/删除分类、反向依赖BFS影响分析、优化重编译编排、依赖图变更传播、缓存系统交互 |

**预计新增**: ~31 个测试

### P1 验收标准
- [ ] ir_generator 测试 ≥ 50 个，覆盖所有控制流和表达式类型
- [ ] parser 测试 ≥ 55 个，覆盖所有语法结构和错误恢复路径
- [ ] compiler/optimizer 测试 ≥ 25 个，覆盖4个类的核心方法
- [ ] 全部 pytest 通过，0 failure
- [ ] 完整套件无回归 (422+ passed)

---

## P2: 重构 Top 5 高复杂度文件

### 排序（按复杂度）

| # | 文件 | 当前列数 | 目标列数 | 核心问题 |
|---|------|---------|---------|---------|
| 1 | `src/ir/ir_generator.py` | 25 | ≤15 | `_eval_expr` 142行 if-elif 链；控制流方法各 40-59 行 |
| 2 | `src/compiler/optimizer.py` | 23 | ≤14 | 类职责过多(4个class在一个文件)；`pipeline_parallel_compile` 48行 |
| 3 | `src/converter/integrated.py` | 20 | ≤10 | `process_single_file` 125行(做太多事)；`_extract_module_content` 启发式字符串匹配 |
| 4 | `src/parser/parser.py` | 18 | ≤12 | 1455行的巨型文件；`parse_declaration` 72行 if-elif；表达式解析器可拆分 |
| 5 | `src/parser/ast_nodes.py` | (数据) | - | 1523行但全是数据类，优先级最低 |

### 2.1 `ir_generator.py` 重构 — 拆分 `_eval_expr`

**策略**: 将 `_eval_expr` 的 142 行 if-elif 链拆分为独立方法

```
_eval_expr(node)  → 分派到:
├── _eval_literal(node)        # 字面量: INT/FLOAT/STRING/CHAR/BOOL/NULL
├── _eval_identifier(node)    # 标识符 → LOAD
├── _eval_binary(node)         # 二元运算
├── _eval_unary(node)          # 一元运算
├── _eval_assignment(node)     # 赋值
├── _eval_call(node)           # 函数调用
├── _eval_member(node)        # 成员访问
├── _eval_array(node)         # 数组访问
├── _eval_ternary(node)       # 三元表达式 (最复杂，保留一定长度)
└── _eval_cast(node)          # 类型转换
```

**控制流方法重构**: 将 visit_for_stmt (59行) 中的 4 块创建提取为 `_create_for_loop_blocks()` 辅助方法

### 2.2 `optimizer.py` 重构 — 按类拆分

**策略**: 将 4 个 class 拆分为独立文件

```
src/compiler/
├── optimizer/
│   ├── __init__.py              # 导出
│   ├── performance_monitor.py   # PerformanceMonitor (L46-197)
│   ├── algorithm_optimizer.py    # AlgorithmOptimizer (L199-367)
│   ├── concurrent_compiler.py    # ConcurrentCompiler (L369-461)
│   └── incremental_optimizer.py  # IncrementalOptimizer (L463-591)
```

### 2.3 `integrated.py` 重构 — SRP 拆分

**策略**: 将 `process_single_file` (125行) 拒分为步骤方法

```
process_single_file(file, output_dir):
    ├── _read_source(file) → lines
    ├── _parse_lines(lines) → parse_errors, summary
    ├── _convert_modules(modules) → header_code, source_code
    ├── _handle_imports(imports) → import_code
    ├── _write_output(header_code, source_code)
    └── _update_stats()
```

### 2.4 `parser.py` 重构 — 拆分表达式解析器

**策略**: 将 parser.py 中 L1154-L1351 的表达式解析器拆为 `expressions.py`（已存在但可能需增强）

将超长的 `parse_declaration` (L287-358) 用 lookup table 替代 if-elif 链：

```python
DECLARATION_PARSERS = {
    TokenType.MODULE:      'parse_module_decl',
    TokenType.IMPORT:      'parse_import_decl',
    TokenType.STRUCT:      '_parse_struct_or_var',  # lookahead
    TokenType.UNION:       '_parse_union_or_var',
    TokenType.ENUM:        '_parse_enum_or_var',
    TokenType.TYPEDEF:      'parse_typedef_decl',
    TokenType.FUNCTION:    'parse_function_decl_with_type',  # 类型前缀函数
    TokenType.CONST:       'parse_const_decl',
    # ... 类型关键字
}
```

### P2 验收标准
- [ ] ir_generator 最大函数 ≤ 40 行
- [ ] optimizer.py 拆分为 4 个文件
- [ ] integrated.py 最大函数 ≤ 35 行
- [ ] parser.py 使用 dispatch table 替代声明解析的 if-elif 链
- [ ] 所有重构后现有测试仍通过 (422+ passed)
- [ ] 质量评分从 60 → 65+

---

## 执行顺序建议

```
Week 1 (本周):
  ├── P1: ir_generator 测试扩展 (+47 tests) ← 最重要，核心模块
  ├── P1: compiler/optimizer 测试新建 (+31 tests)
  └── P2: ir_generator.py 重构 _eval_expr

Week 2:
  ├── P1: parser 测试扩展 (+43 tests)
  ├── P2: optimizer.py 按类拆分
  ├── P2: integrated.py SRP 拆分
  └── P2: parser.py dispatch table 重构

里程碑: 测试总数 422 → 550+, 质量评分 60 → 65+
```

---

## 风险与注意事项

1. **test_optimizer_enhanced.py** 测试的是 `zhpp.opt.*` 模块（死代码消除/常量传播），不是 `src/compiler/optimizer.py`。需要确认这些 `zhpp.opt.*` 模块是否真实存在，如果不存在那些测试就是假的。
2. **parser.py** 的 `test_parser.py` 还是 unittest 格式（有 `run_tests()` 和 `if __name__`），之前没改它。这次扩展时一并改为 pytest。
3. **integrated.py** 引用了 `..day2.module_parser` 和 `.scope_manager`，需要确认这些模块是否存在且 API 匹配。

---

*最后更新: 2026-04-07 by 阿福*

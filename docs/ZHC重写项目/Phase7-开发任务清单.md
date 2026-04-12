# Phase 7：优化与完善 — 开发任务清单

**版本**: v2.0  
**所属阶段**: Phase 7（持续迭代）  
**前置阶段**: Phase 2 完成即可启动优化，Phase 6（多语言前端）完成后全面进入
**文档目的**: 直接指导程序员进行开发，包含操作步骤、代码示例、验收标准  
**基于文档**: `12-项目规模与工时估算.md`、`15-重构任务执行清单.md`

---

## 📋 v2.0 修订说明

本版本修订基于[Phase1-5专家优化分析报告.md](./Phase1-5专家优化分析报告.md)的分析，更新以下内容：

| # | 修订内容 |
|:---:|:---|
| 依赖调整 | Phase 7 不再要求 Phase 5（安全执行框架）完成，Phase 2 完成后即可启动性能优化 |
| 指标调整 | 新增 Phase 3-6 引入的新模块的覆盖率指标（泛型/EH/Pattern/SmartPtr/追踪/AI/沙箱） |
| 测试标准 | 与 Python 版 3511 测试对齐的交叉验证要求 |

---

## 7.0 阶段概述

### 目标

Phase 7 不是传统意义上的「开发阶段」，而是**持续迭代的质量保障与性能优化**阶段。在 Phase 1-6 完成核心功能的基础上，Phase 7 聚焦于：

1. **编译性能优化**：编译速度逼近 Clang 水平
2. **测试覆盖率提升**：从功能可用到质量可靠（≥80% 目标）
3. **文档体系完善**：用户手册 + API 文档 + 教程
4. **Bug 修复与稳定性**：持续修复缺陷，提升可靠性
5. **社区反馈迭代**：基于用户反馈的功能改进
6. **Python 版交叉验证**：与 Python 版 3511 测试对齐，确保 C++ 版行为一致

### 核心原则

- **数据驱动**：所有优化必须有基准测试数据支撑
- **回归保护**：每次优化后全量回归测试，零回归
- **渐进式**：每月一个迭代周期，持续交付
- **Python 版对齐**：新增的 C++ 测试用例与 Python 版测试行为交叉验证

---

## T7.1：编译性能优化

**工时**: 持续（每月 20h）  
**依赖**: Phase 2 完成  
**交付物**: 性能基准测试套件 + 优化记录

### 1.1 建立编译性能基准

**首次工时**: 20h  
**交付物**: `benchmarks/compile_bench/` + 性能数据

```cpp
// benchmarks/compile_bench/BenchmarkRunner.cpp

#include <benchmark/benchmark.h>
#include "zhc/Driver.h"

using namespace zhc;

// 基准1：词法分析吞吐量
static void BM_Lexer_Throughput(benchmark::State &State) {
    std::string Source = generateLargeSource(State.range(0));
    for (auto _ : State) {
        Lexer L(Source, Diags);
        while (L.nextToken().isNot(TokenKind::EOF))
            ;
        benchmark::DoNotOptimize(L);
    }
    State.SetItemsProcessed(State.iterations() * State.range(0));
}
BENCHMARK(BM_Lexer_Throughput)->Arg(1000)->Arg(10000)->Arg(100000);

// 基准2：Parser 吞吐量
static void BM_Parser_Throughput(benchmark::State &State) {
    std::string Source = generateProgramWithNFunctions(State.range(0));
    for (auto _ : State) {
        auto Tokens = lex(Source);
        Parser P(Tokens, Diags);
        auto *TU = P.parseTranslationUnit();
        benchmark::DoNotOptimize(TU);
    }
}
BENCHMARK(BM_Parser_Throughput)->Arg(10)->Arg(100)->Arg(1000);

// 基准3：语义分析吞吐量
static void BM_Sema_Throughput(benchmark::State &State) {
    auto *TU = parseFile("benchmarks/fixtures/complex_program.zhc");
    for (auto _ : State) {
        Sema S(Diags, SymTab);
        S.Analyze(TU);
    }
}
BENCHMARK(BM_Sema_Throughput);

// 基准4：IR 生成吞吐量
static void BM_CodeGen_Throughput(benchmark::State &State) {
    auto *TU = parseAndAnalyze("benchmarks/fixtures/complex_program.zhc");
    for (auto _ : State) {
        CodeGen CG(Context, Diags, TM);
        auto Mod = CG.codegen(TU);
        benchmark::DoNotOptimize(Mod.get());
    }
}
BENCHMARK(BM_CodeGen_Throughput);

// 基准5：端到端编译时间
static void BM_EndToEnd_Compile(benchmark::State &State) {
    for (auto _ : State) {
        Driver D;
        D.compileFile("benchmarks/fixtures/fibonacci.zhc",
                      CompilationOptions());
    }
}
BENCHMARK(BM_EndToEnd_Compile);

BENCHMARK_MAIN();
```

### 1.2 性能优化目标

| 指标 | 目标值 | 测量方式 |
|:---|:---:|:---|
| **编译速度** | ≤ Clang 1.5x | 同文件编译时间对比 |
| **内存占用** | ≤ Clang 2x |峰值 RSS 对比 |
| **Lexer 吞吐** | ≥ 100MB/s | 大文件词法分析 |
| **Parser 吞吐** | ≥ 50K LOC/s | 函数密集文件 |
| **IR 生成** | ≥ 10K 函数/s | 函数密集文件 |

### 1.3 已知优化方向

```cpp
// 优化1：Lexer 缓冲区预取
class Lexer {
    // 优化前：逐字符读取
    // 优化后：按行预取，减少 IO 调用
    llvm::StringRef LineBuffer;
    void prefetchLine();
};

// 优化2：Parser 零拷贝 AST 节点
// 使用 Arena 分配器，所有 AST 节点在连续内存上
class ASTContext {
    llvm::BumpPtrAllocator Allocator;
public:
    template<typename T, typename... Args>
    T *allocate(Args&&... args) {
        return new (Allocator.Allocate<T>()) T(std::forward<Args>(args)...);
    }
};

// 优化3：符号表哈希优化
// 使用 llvm::DenseMap 替代 std::unordered_map
llvm::DenseMap<llvm::StringRef, Symbol*> SymbolTable;

// 优化4：IR 生成惰性类型映射
// 缓存已映射的 LLVM Type，避免重复映射
llvm::DenseMap<QualType, llvm::Type*> TypeCache;

// 优化5：并行编译（多翻译单元）
// 使用 ThreadPool 并行编译多个文件
llvm::ThreadPool Pool;
for (auto &File : InputFiles) {
    Pool.async([&]() { compileFile(File); });
}
Pool.wait();
```

### 1.4 性能回归检测

```bash
# 每次提交自动运行基准测试
# benchmarks/scripts/check_regression.sh

#!/bin/bash
OLD_BENCH=$(cat benchmarks/results/previous.json)
NEW_BENCH=$(./build/benchmarks/compile_bench --benchmark_format=json)

# 检查是否有 >10% 的性能退化
python3 benchmarks/scripts/compare_benchmarks.py \
    "$OLD_BENCH" "$NEW_BENCH" \
    --threshold 0.10 \
    --report benchmarks/results/regression_report.md
```

### 1.5 验收标准

```bash
# 运行基准测试
./build/benchmarks/compile_bench
# 所有基准 ≥ 目标值

# 对比 Clang
zhc compile fibonacci.zhc -o fib_zhc
clang fibonacci.c -o fib_clang
# 编译时间比 ≤ 1.5x
```

---

## T7.2：测试覆盖率提升

**工时**: 持续（每月 16h）  
**依赖**: Phase 2 完成  
**交付物**: 覆盖率报告 + 新增测试用例

### 2.1 覆盖率目标

| 模块 | 当前覆盖率 | 目标覆盖率 | 优先级 |
|:---|:---:|:---:|:---:|
| Lexer | - | ≥ 95% | 🔴 高 |
| Parser | - | ≥ 90% | 🔴 高 |
| Sema | - | ≥ 85% | 🔴 高 |
| CodeGen | - | ≥ 80% | 🟠 中 |
| Runtime | - | ≥ 90% | 🟠 中 |
| Diagnostics | - | ≥ 85% | 🟡 低 |
| **总体** | - | **≥ 80%** | 🔴 高 |

### 2.2 覆盖率收集配置

```cmake
# test/CMakeLists.txt — 覆盖率支持

option(ENABLE_COVERAGE "Enable code coverage" OFF)

if(ENABLE_COVERAGE)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} --coverage")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} --coverage")

    # 生成覆盖率报告
    add_custom_target(coverage
        COMMAND lcov --capture --directory . --output-file coverage.info
        COMMAND lcov --remove coverage.info '/usr/*' '*/third_party/*' '*/test/*' --output-file coverage.info
        COMMAND genhtml coverage.info --output-directory coverage_report
        COMMAND echo "Coverage report: coverage_report/index.html"
        DEPENDS zhc_tests
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
    )
endif()
```

### 2.3 测试用例补充策略

```cpp
// 每个模块的测试清单（按优先级）

// === Lexer 测试补充 ===
// 1. 边界条件：空文件、超长行、全中文文件
// 2. 错误恢复：非法 UTF-8、不完整字符串、非法转义
// 3. 性能：100K 行文件词法分析不崩溃

// === Parser 测试补充 ===
// 1. 错误恢复：缺失分号、括号不匹配、多余逗号
// 2. 边界条件：空函数、嵌套结构体、深递归表达式
// 3. 全中文程序：所有中文关键词至少一个测试

// === Sema 测试补充 ===
// 1. E0 安全特性：边界检查、溢出检测、空指针
// 2. 类型转换：隐式/显式转换、不兼容类型报错
// 3. 作用域：变量隐藏、前向引用、全局变量

// === CodeGen 测试补充 ===
// 1. IR 验证：所有生成函数通过 verifyFunction
// 2. 调试信息：DWARF 信息正确
// 3. 链接：多文件链接、静态库链接

class CoverageTest : public ::testing::Test {
    // 专门为提升覆盖率设计的测试
};

// 测试：Lexer 错误恢复
TEST_F(CoverageTest, LexerErrorRecovery) {
    // 非法字符后继续词法分析
    auto Tokens = lex("int \xFF x = 5;");
    // 应产生 Error Token + 恢复后续分析
    EXPECT_GT(Tokens.size(), 2);
}

// 测试：Parser 深嵌套
TEST_F(CoverageTest, ParserDeepNesting) {
    // 50层嵌套的 if
    std::string Source = "int main() {";
    for (int i = 0; i < 50; i++)
        Source += "if (1) {";
    for (int i = 0; i < 50; i++)
        Source += "}";
    Source += " return 0; }";
    auto *TU = parse(Source);
    EXPECT_NE(TU, nullptr);
}
```

### 2.4 每月覆盖率检查

```bash
# scripts/coverage_check.sh

#!/bin/bash
cd cpp/build
cmake .. -DENABLE_COVERAGE=ON
ninja zhc_tests
ctest --output-on-failure
ninja coverage

# 解析覆盖率数据
TOTAL=$(grep "overall" coverage_report/index.html | grep -oP '\d+\.\d+')
echo "Total coverage: ${TOTAL}%"

# 低于 80% 则告警
if (( $(echo "$TOTAL < 80.0" | bc -l) )); then
    echo "⚠️ 覆盖率低于 80%，需要补充测试用例"
    exit 1
fi
```

### 2.5 验收标准

```bash
# 生成覆盖率报告
ninja coverage
# 总覆盖率 ≥ 80%
# 各模块 ≥ 目标值
```

---

## T7.3：文档体系完善

**工时**: 持续（每版本 16h）  
**依赖**: 各 Phase 完成  
**交付物**: 用户手册 + API 文档 + 教程

### 3.1 文档体系结构

```
docs/
├── user-guide/              # 用户手册
│   ├── getting-started.md   # 快速开始
│   ├── installation.md      # 安装指南
│   ├── cli-reference.md     # CLI 参数参考
│   ├── language-spec.md     # 语言规范（中文C语法）
│   ├── type-system.md       # 类型系统说明
│   ├── safety-features.md   # 安全特性手册
│   ├── ai-features.md       # AI 功能使用指南
│   ├── multilang.md         # 多语言编译指南
│   └── troubleshooting.md   # 常见问题
├── api/                     # API 文档
│   ├── lexer-api.md         # Lexer API
│   ├── parser-api.md        # Parser API
│   ├── sema-api.md          # Sema API
│   ├── codegen-api.md       # CodeGen API
│   ├── runtime-api.md       # 运行时 API
│   └── plugin-api.md        # 插件 API
├── tutorials/               # 教程
│   ├── hello-world.md       # Hello World
│   ├── variables-types.md   # 变量与类型
│   ├── control-flow.md      # 控制流
│   ├── functions.md         # 函数
│   ├── structs.md           # 结构体
│   ├── pointers.md          # 指针
│   ├── generics.md          # 泛型
│   ├── ai-assisted.md       # AI 辅助编程
│   └── compile-python.md    # 编译 Python
└── internals/               # 内部设计文档
    ├── architecture.md      # 编译器架构
    ├── ast-design.md        # AST 设计
    ├── ir-design.md         # IR 设计
    ├── backend-design.md    # 后端设计
    └── security-model.md    # 安全模型
```

### 3.2 用户手册编写规范

```markdown
<!-- 文档模板 docs/user-guide/template.md -->

# [功能名称]

## 概述
[一句话描述功能]

## 语法
```zhc
[语法示例]
```

## 参数
| 参数 | 类型 | 必需 | 说明 |
|:---|:---|:---:|:---|
| ... | ... | ... | ... |

## 示例
### 基本用法
```zhc
[代码示例]
```

### 高级用法
```zhc
[代码示例]
```

## 注意事项
- [注意事项1]
- [注意事项2]

## 相关文档
- [链接1]
- [链接2]
```

### 3.3 API 文档自动生成

```bash
# 使用 Doxygen 从 C++ 头文件生成 API 文档

# Doxyfile 配置
PROJECT_NAME = "ZhC Compiler"
INPUT = include/zhc/
OUTPUT_DIRECTORY = docs/api/
GENERATE_HTML = YES
GENERATE_XML = YES
EXTRACT_ALL = YES
RECURSIVE = YES

# 生成命令
doxygen Doxyfile
```

### 3.4 教程编写标准

每个教程必须包含：
1. **学习目标**（明确列出要掌握的知识点）
2. **前置知识**（需要先完成的教程）
3. **完整代码**（可直接编译运行）
4. **逐行解释**（关键行有中文注释）
5. **练习题**（1-3 道动手练习）

### 3.5 验收标准

```bash
# 检查文档完整性
python3 scripts/check_docs.py docs/
# 所有模板已填充
# 无断链
# 代码示例可编译运行
```

---

## T7.4：Bug 修复与稳定性

**工时**: 持续（每月 20h）  
**依赖**: 各 Phase 完成  
**交付物**: Bug 修复记录 + 稳定性报告

### 4.1 Bug 分类与优先级

| 优先级 | 定义 | 响应时间 | 修复时间 |
|:---:|:---|:---:|:---:|
| **P0** | 编译器崩溃/数据丢失 | < 4h | < 24h |
| **P1** | 编译错误/运行时错误 | < 24h | < 1 周 |
| **P2** | 性能退化/功能缺失 | < 1 周 | < 2 周 |
| **P3** | 文档错误/体验不佳 | < 2 周 | 下版本 |

### 4.2 Bug 修复流程

```
1. 报告（GitHub Issue）
   └→ 分类（P0/P1/P2/P3）
      └→ 分配（开发者）
         └→ 复现（最小化测试用例）
            └→ 修复（代码修改）
               └→ 测试（单元测试 + 回归测试）
                  └→ Code Review
                     └→ 合并 + 关闭 Issue
```

### 4.3 最小化测试用例生成

```bash
# scripts/reduce_testcase.sh
# 使用 C-Reduce 自动最小化崩溃测试用例

creduce --tidy ./reduce_test.sh crash_test.zhc

# reduce_test.sh:
#!/bin/bash
zhc compile crash_test.zhc -o /dev/null 2>/dev/null
# 如果崩溃（退出码非0），则保留此用例
exit $?
```

### 4.4 稳定性指标

| 指标 | 目标值 | 测量方式 |
|:---|:---:|:---|
| **Bug 密度** | < 1 bug/KLOC | Issue 数 / 代码行数 |
| **崩溃率** | < 0.1% | fuzzing 测试 |
| **回归率** | 0% | 每次提交全量测试 |
| **修复时间** | P0 < 24h | Issue 统计 |

### 4.5 Fuzzing 测试

```cpp
// test/fuzz/lexer_fuzz.cpp
#include <fuzzer/FuzzedDataProvider.h>

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    FuzzedDataProvider Provider(Data, Size);
    std::string Source = Provider.ConsumeRemainingBytesAsString();

    // 尝试词法分析，不应崩溃
    try {
        zhc::Lexer L(Source, Diags);
        while (L.nextToken().isNot(zhc::TokenKind::EOF))
            ;
    } catch (...) {
        // 词法分析不应抛异常
        __builtin_trap();
    }
    return 0;
}
```

```cpp
// test/fuzz/parser_fuzz.cpp
extern "C" int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    std::string Source(reinterpret_cast<const char*>(Data), Size);

    // 尝试解析，不应崩溃
    try {
        auto Tokens = lex(Source);
        zhc::Parser P(Tokens, Diags);
        auto *TU = P.parseTranslationUnit();
        // 解析结果可能为空（语法错误），但不应崩溃
        (void)TU;
    } catch (...) {
        __builtin_trap();
    }
    return 0;
}
```

### 4.6 验收标准

```bash
# 运行 fuzzing 测试（24小时）
./build/test/fuzz/lexer_fuzz -max_total_time=86400
./build/test/fuzz/parser_fuzz -max_total_time=86400
# 零崩溃

# 全量回归测试
ctest --output-on-failure
# 零失败
```

---

## T7.5：社区反馈迭代

**工时**: 持续（每月 12h）  
**依赖**: 用户使用  
**交付物**: 反馈收集 + 功能改进

### 5.1 反馈收集渠道

| 渠道 | 地址 | 监控频率 |
|:---|:---|:---:|
| GitHub Issues | `github.com/zhc-lang/zhc/issues` | 每日 |
| GitHub Discussions | `github.com/zhc-lang/zhc/discussions` | 每周 |
| 用户邮件 | `feedback@zhc-lang.org` | 每周 |
| 编程社区 | 知乎/V2EX/CSDN | 每月 |

### 5.2 反馈处理流程

```
1. 收集反馈
   └→ 分类（Bug / 功能请求 / 文档改进 / 体验优化）
      └→ 评估（影响范围 × 实现难度 → 优先级）
         └→ 排期（纳入月度迭代计划）
            └→ 实施（按 Phase 1-6 的开发规范）
               └→ 验证（用户确认问题解决）
```

### 5.3 月度迭代计划模板

```markdown
# [YYYY-MM] 月度迭代计划

## 本月目标
- [ ] 修复 P0/P1 Bug N 个
- [ ] 性能优化 X%
- [ ] 新增测试用例 N 个
- [ ] 文档更新 N 篇

## 任务清单
| # | 任务 | 类型 | 优先级 | 工时 | 负责 |
|:---:|:---|:---:|:---:|:---:|:---:|
| 1 | ... | Bug | P1 | 4h | ... |
| 2 | ... | 优化 | P2 | 8h | ... |
| 3 | ... | 文档 | P3 | 4h | ... |

## 上月回顾
- 完成任务：N/M
- 新增 Bug：N 个
- 覆盖率变化：X% → Y%
- 编译速度变化：Ams → Bms
```

### 5.4 验收标准

```bash
# 每月检查
# - P0 Bug 全部关闭
# - P1 Bug 修复率 ≥ 80%
# - 用户满意度 ≥ 4.0/5.0
```

---

## T7.6：发布准备

**工时**: 40h（一次性）  
**依赖**: Phase 1-6 全部完成  
**交付物**: v1.0 发布包

### 6.1 发布检查清单

```markdown
# v1.0 发布检查清单

## 功能完整性
- [ ] ZHC 编译：`.zhc` → 可执行文件
- [ ] C 编译：`.c` → 可执行文件
- [ ] Python 编译：`.py` → 可执行文件
- [ ] 混合编译：`.zhc` + `.c` + `.py` → 可执行文件
- [ ] 可视化追踪：`--trace` 生成 trace.html
- [ ] AI 错误解释：`-ai` 生成中文错误解释
- [ ] AI 自动修复：`-ai-auto-fix` 自动修复编译错误
- [ ] AI 可信监控：`-ai-monitor` 安全检查
- [ ] E0 安全特性：空指针/边界/溢出/生命周期
- [ ] E1 语言增强：穷举 switch / Result 类型
- [ ] E2 模块系统：模块定义/导入/可见性

## 质量指标
- [ ] 测试覆盖率 ≥ 80%
- [ ] 全量测试通过（0 failed）
- [ ] Fuzzing 零崩溃（24h）
- [ ] 编译速度 ≤ Clang 1.5x
- [ ] Valgrind 零泄漏（Python 运行时）
- [ ] P0 Bug 数 = 0
- [ ] P1 Bug 数 < 5

## 文档完整性
- [ ] 用户手册完整
- [ ] API 文档完整
- [ ] 教程 ≥ 10 篇
- [ ] CLI --help 输出完整

## 平台支持
- [ ] macOS (arm64 + x86_64)
- [ ] Linux (x86_64)
- [ ] Windows (x86_64, 预留)

## 发布包内容
- [ ] 二进制文件（zhc）
- [ ] 运行时库（zhc_rt.a / zhc_python_stdlib.a）
- [ ] 头文件（zhc_rt.h / zhc_python_stdlib.h）
- [ ] 标准库源码
- [ ] 示例程序（≥ 10 个）
- [ ] CHANGELOG.md
- [ ] LICENSE
```

### 6.2 发布包构建

```bash
# scripts/build_release.sh

#!/bin/bash
VERSION="1.0.0"
PLATFORM=$(uname -s)-$(uname -m)

# 构建
mkdir -p build-release && cd build-release
cmake .. -DCMAKE_BUILD_TYPE=Release \
         -DLLVM_DIR=$(llvm-config --cmakedir) \
         -DENABLE_COVERAGE=OFF
ninja

# 运行全量测试
ctest --output-on-failure

# 打包
mkdir -p zhc-${VERSION}-${PLATFORM}
cp build-release/bin/zhc zhc-${VERSION}-${PLATFORM}/
cp -r runtime/ zhc-${VERSION}-${PLATFORM}/
cp -r include/ zhc-${VERSION}-${PLATFORM}/
cp -r examples/ zhc-${VERSION}-${PLATFORM}/
cp README.md CHANGELOG.md LICENSE zhc-${VERSION}-${PLATFORM}/

tar czf zhc-${VERSION}-${PLATFORM}.tar.gz zhc-${VERSION}-${PLATFORM}/
echo "Release package: zhc-${VERSION}-${PLATFORM}.tar.gz"
```

### 6.3 验收标准

```bash
# 发布前最终验收
# 1. 全量测试通过
ctest --output-on-failure
# 2. Fuzzing 零崩溃
# 3. 编译速度达标
# 4. 覆盖率 ≥ 80%
# 5. 文档无断链
# 6. 发布包可安装运行
```

---

## 7.1 Phase 7 Go/No-Go 检查点

### 检查点：v1.0 发布验收

| 检查项 | 验收命令 | 通过标准 |
|:---|:---|:---|
| **编译速度** | `time zhc compile fibonacci.zhc` | ≤ Clang 1.5x |
| **测试覆盖率** | `ninja coverage` | ≥ 80% |
| **Bug 密度** | Issue 统计 | < 1 bug/KLOC |
| **崩溃率** | Fuzzing 24h | 零崩溃 |
| **用户满意度** | 用户调研 | ≥ 4.0/5.0 |
| **文档完整性** | 检查脚本 | 无断链，代码可运行 |
| **平台支持** | 三平台编译 | macOS + Linux 通过 |

**量化标准**：
- 编译速度 ≤ Clang 1.5x
- 测试覆盖率 ≥ 80%
- P0 Bug 数 = 0
- 至少 1 位外部用户试用并给出反馈

**如未通过**：
- 延期发布，集中修复问题
- 编译速度 > Clang 2x 则不许发布

---

## 7.2 持续改进指标仪表盘

| 指标 | 目标值 | 测量频率 | 当前值 |
|:---|:---:|:---:|:---:|
| 编译速度 | ≤ Clang 1.5x | 每日 | - |
| 测试覆盖率 | ≥ 80% | 每周 | - |
| Bug 密度 | < 1/KLOC | 每月 | - |
| P0 Bug 数 | 0 | 实时 | - |
| Fuzzing 崩溃 | 0 | 每日 | - |
| 用户满意度 | ≥ 4.0 | 每月 | - |
| 文档完整度 | 100% | 每版本 | - |

---

## 7.3 参考资料

| 资料 | 路径 | 用途 |
|:---|:---|:---|
| Google Benchmark | `github.com/google/benchmark` | 性能基准测试框架 |
| C-Reduce | `github.com/csmith-project/creduce` | 测试用例最小化 |
| libFuzzer | LLVM 内置 | Fuzzing 框架 |
| Doxygen | `doxygen.nl` | API 文档生成 |
| lcov | `github.com/linux-test-project/lcov` | 覆盖率收集 |
| Clang 性能数据 | Clang 自身基准 | 编译速度对比基线 |

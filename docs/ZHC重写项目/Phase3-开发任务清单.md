# Phase 3：可视化执行追踪

**版本**: v1.0
**日期**: 2026-04-13
**基于文档**: `08-可视化执行追踪层.md`、`12-项目规模与工时估算.md`、`15-重构任务执行清单.md`
**目标**: 完成可视化执行追踪，能生成 trace.json + trace.html
**工时**: 192h（含 20% 风险缓冲）
**日历时间**: 约 1.5 个月
**前置条件**: Phase 2 完成（能编译运行 ZHC 程序）

---

## 3.1 阶段目标

在 Phase 2 编译能力基础上，新增可视化执行追踪功能：

1. **追踪探针注入器**：在 LLVM IR 层面注入追踪探针
2. **追踪运行时库**：C 运行时库，记录执行事件
3. **JSON 序列化**：生成结构化 trace.json
4. **HTML 可视化**：生成中文界面 trace.html
5. **CLI 集成**：`--trace` 参数
6. **AI 理解度评估**：分析执行轨迹，生成学习建议

---

## 3.2 Week 1-2：追踪探针注入

### 任务 3.2.1 IR 追踪 Pass

#### T3.1 实现追踪探针注入 Pass

**交付物**: `include/zhc/trace/ProbeInjector.h` + `lib/trace/ProbeInjector.cpp`

**操作步骤**:
1. 实现一个 LLVM Module Pass，在函数入口、函数出口、分支、赋值处注入探针：

```cpp
// include/zhc/trace/ProbeInjector.h
class TraceInjectorPass : public llvm::PassInfoMixin<TraceInjectorPass> {
public:
    llvm::PreservedAnalyses run(llvm::Module &M,
                                llvm::ModuleAnalysisManager &MAM);

    static bool isRequired() { return true; }

private:
    /// 在函数入口注入探针
    void injectFunctionEntry(llvm::Function &F);

    /// 在函数出口（return/unwind）注入探针
    void injectFunctionExit(llvm::Function &F);

    /// 在分支处注入探针
    void injectBranchProbe(llvm::BranchInst *BI);

    /// 在变量赋值（store）处注入探针
    void injectStoreProbe(llvm::StoreInst *SI);

    /// 在函数调用处注入探针
    void injectCallProbe(llvm::CallInst *CI);

    /// 获取/创建追踪运行时函数
    llvm::Function *getTraceFunc(llvm::Module &M, const char *Name);
};
```

2. 探针调用约定：

```cpp
// lib/trace/ProbeInjector.cpp

// 声明运行时函数
llvm::FunctionCallee TraceInjectorPass::getTraceFunc(
    llvm::Module &M, const char *Name) {

    if (Name == "__zhc_trace_func_enter") {
        // void __zhc_trace_func_enter(const char *func_name, const char *file,
        //                              unsigned line)
        auto *FT = llvm::FunctionType::get(
            Builder->getVoidTy(),
            {Builder->getInt8PtrTy(), Builder->getInt8PtrTy(),
             Builder->getInt32Ty()}, false);
        return M.getOrInsertFunction(Name, FT);
    }
    // 类似定义其他运行时函数...
}

void TraceInjectorPass::injectFunctionEntry(llvm::Function &F) {
    // 在函数入口基本块的第一个指令前插入探针
    llvm::BasicBlock &Entry = F.getEntryBlock();
    llvm::IRBuilder<> Builder(&*Entry.getFirstInsertionPt());

    Builder.CreateCall(
        getTraceFunc(F.getParent(), "__zhc_trace_func_enter"),
        {
            Builder.CreateGlobalStringPtr(F.getName()),
            Builder.CreateGlobalStringPtr(
                F.getSubprogram()->getFilename()),
            llvm::ConstantInt::get(Builder->getInt32Ty(),
                F.getSubprogram()->getLine())
        });
}
```

**参考**: `08-可视化执行追踪层.md`，Python 版本 `src/zhc/ir/optimization_observer.py`

**工时**: 40h

---

#### T3.2 实现追踪运行时库

**交付物**: `runtime/zhc_trace_runtime.h` + `runtime/zhc_trace_runtime.c`

**操作步骤**:
1. 实现 C 运行时探针函数：

```c
// runtime/zhc_trace_runtime.h
#ifndef ZHC_TRACE_RUNTIME_H
#define ZHC_TRACE_RUNTIME_H

#include <stdint.h>

// 追踪事件类型
typedef enum {
    ZHC_TRACE_FUNC_ENTER = 1,   // 函数进入
    ZHC_TRACE_FUNC_EXIT  = 2,   // 函数退出
    ZHC_TRACE_BRANCH     = 3,   // 分支
    ZHC_TRACE_STORE      = 4,   // 变量赋值
    ZHC_TRACE_CALL       = 5,   // 函数调用
    ZHC_TRACE_RETURN     = 6,   // 返回值
} zhc_trace_event_type_t;

// 追踪事件
typedef struct {
    zhc_trace_event_type_t type;
    const char *name;        // 函数名/变量名
    const char *file;        // 源文件
    uint32_t line;           // 行号
    uint32_t col;            // 列号
    int64_t value;           // 值（用于变量赋值追踪）
    uint64_t timestamp;      // 时间戳（纳秒）
} zhc_trace_event_t;

// 初始化追踪
void zhc_trace_init(const char *output_path);

// 记录事件
void zhc_trace_record(zhc_trace_event_type_t type, const char *name,
                      const char *file, uint32_t line);

// 记录带值的事件
void zhc_trace_record_value(zhc_trace_event_type_t type, const char *name,
                            const char *file, uint32_t line, int64_t value);

// 刷新并关闭
void zhc_trace_flush(void);
void zhc_trace_finalize(void);

// 探针函数（由 IR 注入调用）
void __zhc_trace_func_enter(const char *func, const char *file, uint32_t line);
void __zhc_trace_func_exit(const char *func, const char *file, uint32_t line);
void __zhc_trace_branch(const char *file, uint32_t line, int taken);
void __zhc_trace_store(const char *var, const char *file, uint32_t line,
                       int64_t value);
void __zhc_trace_call(const char *callee, const char *file, uint32_t line);
void __zhc_trace_return(const char *func, const char *file, uint32_t line,
                        int64_t value);

#endif // ZHC_TRACE_RUNTIME_H
```

2. 实现 `runtime/zhc_trace_runtime.c`：
   - 使用环形缓冲区存储事件（默认 1M 事件）
   - `zhc_trace_init` 打开输出文件
   - `zhc_trace_flush` 刷新到文件
   - `zhc_trace_finalize` 关闭文件

**工时**: 24h

---

#### T3.3 实现探针函数

**交付物**: `runtime/zhc_trace_runtime.c` 中的探针实现

**操作步骤**:
1. 实现 `__zhc_trace_func_enter`：

```c
// runtime/zhc_trace_runtime.c
static zhc_trace_event_t *TraceBuffer = NULL;
static size_t TraceBufferSize = 0;
static size_t TraceEventCount = 0;
static FILE *TraceOutput = NULL;

void __zhc_trace_func_enter(const char *func, const char *file,
                            uint32_t line) {
    if (TraceEventCount >= TraceBufferSize) {
        zhc_trace_flush();  // 缓冲区满，刷新
    }
    zhc_trace_event_t *evt = &TraceBuffer[TraceEventCount++];
    evt->type = ZHC_TRACE_FUNC_ENTER;
    evt->name = func;
    evt->file = file;
    evt->line = line;
    evt->timestamp = zhc_get_timestamp_ns();
}
```

2. 实现时间戳获取：
```c
#include <time.h>
static uint64_t zhc_get_timestamp_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}
```

**工时**: 16h

---

## 3.3 Week 3-4：可视化生成

### 任务 3.3.1 JSON 序列化

#### T3.4 实现 trace.json 序列化器

**交付物**: `include/zhc/trace/TraceSerializer.h` + `lib/trace/TraceSerializer.cpp`

**操作步骤**:
1. 定义 trace.json Schema：

```json
{
  "$schema": "https://zhc.dev/trace-schema/v1",
  "metadata": {
    "source_file": "hello.zhc",
    "compiler_version": "ZhC 2.0.0",
    "target_triple": "x86_64-apple-darwin",
    "timestamp": "2026-04-13T12:00:00Z",
    "total_events": 42,
    "total_time_ns": 1234567
  },
  "source": {
    "lines": [
      {"line": 1, "text": "函数 整数型 main() {"},
      {"line": 2, "text": "    打印(\"Hello, World!\");"},
      {"line": 3, "text": "    返回 0;"},
      {"line": 4, "text": "}"}
    ]
  },
  "events": [
    {
      "seq": 1,
      "type": "func_enter",
      "name": "main",
      "file": "hello.zhc",
      "line": 1,
      "timestamp_ns": 0
    },
    {
      "seq": 2,
      "type": "call",
      "name": "打印",
      "file": "hello.zhc",
      "line": 2,
      "timestamp_ns": 1000
    },
    {
      "seq": 3,
      "type": "return",
      "name": "main",
      "file": "hello.zhc",
      "line": 3,
      "value": 0,
      "timestamp_ns": 5000
    }
  ],
  "variables": [
    {
      "name": "x",
      "type": "整数型",
      "assignments": [
        {"line": 5, "value": 42, "timestamp_ns": 2000}
      ]
    }
  ],
  "call_stack": [
    {"depth": 0, "function": "main", "file": "hello.zhc", "line": 1}
  ]
}
```

2. 实现 C++ JSON 序列化器：
```cpp
// include/zhc/trace/TraceSerializer.h
class TraceSerializer {
public:
    /// 从运行时追踪文件读取并序列化为 JSON
    bool serialize(const std::string &TraceFile,
                   const std::string &SourceFile,
                   const std::string &OutputPath);

private:
    void writeMetadata(llvm::json::OStream &J,
                      const std::string &Source);
    void writeSource(llvm::json::OStream &J,
                    const std::string &Source);
    void writeEvents(llvm::json::OStream &J,
                    const std::vector<zhc_trace_event_t> &Events);
    void writeVariables(llvm::json::OStream &J,
                       const std::vector<VarAssignment> &Vars);
};
```

**参考**: `08-可视化执行追踪层.md`

**工时**: 16h

---

### 任务 3.3.2 HTML 可视化

#### T3.5 设计 HTML 模板

**交付物**: `trace_templates/trace_template.html`

**操作步骤**:
1. 设计中文界面 trace.html 模板：
   - 左侧：源码面板（逐行显示，执行到的行高亮）
   - 右侧上：变量追踪面板（实时显示变量值）
   - 右侧下：调用栈面板（显示函数调用栈）
   - 底部：事件时间线（可滚动，点击跳转）

2. 设计要素：
   - 深色主题（IDE 风格）
   - 中文界面标签
   - 响应式布局
   - 行执行次数标注（如 `x3` 表示执行 3 次）
   - 分支高亮（执行到的分支绿色，未执行的灰色）

**工时**: 16h

---

#### T3.6 实现 HTML 生成器

**交付物**: `include/zhc/trace/TraceHtmlGenerator.h` + `lib/trace/TraceHtmlGenerator.cpp`

**操作步骤**:
1. 从 trace.json 生成 trace.html：

```cpp
// include/zhc/trace/TraceHtmlGenerator.h
class TraceHtmlGenerator {
public:
    /// 从 JSON 生成 HTML
    bool generate(const std::string &JsonPath,
                  const std::string &HtmlPath);

private:
    void generateSourcePanel(std::ostream &OS,
                            const TraceData &Data);
    void generateVarPanel(std::ostream &OS,
                          const TraceData &Data);
    void generateCallStackPanel(std::ostream &OS,
                                const TraceData &Data);
    void generateTimeline(std::ostream &OS,
                         const TraceData &Data);
};
```

2. 内嵌 CSS + JavaScript（单文件输出，无需额外依赖）
3. JavaScript 实现交互：
   - 点击事件 → 高亮对应源码行
   - 步进/后退播放
   - 变量值变化动画

**工时**: 16h

---

### 任务 3.3.3 CLI 集成

#### T3.7 CLI `--trace` 参数

**交付物**: `tools/zhc/zhc.cpp` 中的 `--trace` 参数处理

**操作步骤**:
1. 在编译器驱动中添加 `--trace` 参数：

```cpp
// tools/zhc/zhc.cpp

// 命令行选项
cl::opt<bool> EnableTrace("trace",
    cl::desc("启用执行追踪（生成 trace.json + trace.html）"),
    cl::init(false));

// 编译流程
int main(int argc, char **argv) {
    cl::ParseCommandLineOptions(argc, argv, "ZhC 编译器\n");

    // ... 前端 + Sema + CodeGen ...

    if (EnableTrace) {
        // 注入追踪 Pass
        MPM.addPass(TraceInjectorPass());

        // 链接追踪运行时
        linker.addInputFile("libzhc_trace.a");
    }

    // ... 生成目标文件 + 链接 ...

    if (EnableTrace) {
        // 运行程序
        std::string Cmd = OutputPath;
        system(Cmd.c_str());

        // 序列化追踪数据
        TraceSerializer().serialize("trace.bin", InputFile, "trace.json");

        // 生成 HTML
        TraceHtmlGenerator().generate("trace.json", "trace.html");

        llvm::outs() << "✅ 追踪完成:\n";
        llvm::outs() << "  - trace.json\n";
        llvm::outs() << "  - trace.html\n";
    }
}
```

**工时**: 8h

---

### 任务 3.3.4 AI 理解度评估

#### T3.8 实现 AI 轨迹分析

**交付物**: `include/zhc/trace/TraceAnalyzer.h` + `lib/trace/TraceAnalyzer.cpp`

**操作步骤**:
1. 实现轨迹分析（不依赖 LLM，纯规则引擎）：

```cpp
// include/zhc/trace/TraceAnalyzer.h
class TraceAnalyzer {
public:
    struct AnalysisResult {
        double UnderstandingScore;   // 0.0-1.0
        std::vector<std::string> Insights;
        std::vector<std::string> Suggestions;
        std::string Summary;
    };

    AnalysisResult analyze(const TraceData &Data);

private:
    /// 分析执行路径复杂度
    double analyzeComplexity(const TraceData &Data);

    /// 检测常见错误模式
    std::vector<std::string> detectPatterns(const TraceData &Data);

    /// 生成学习建议
    std::vector<std::string> generateSuggestions(
        const TraceData &Data, double Score);
};
```

2. 分析维度：
   - 执行路径长度 vs 预期
   - 循环次数统计
   - 变量值变化模式
   - 分支覆盖率
   - 递归深度

**参考**: `08-可视化执行追踪层.md` 中的理解度评估部分

**工时**: 40h

---

#### T3.9 端到端追踪测试

**交付物**: `test/integration/trace_test.cpp`

**操作步骤**:
1. 创建 fixture 测试：
   - `hello_trace.zhc`：简单程序
   - `fibonacci_trace.zhc`：递归追踪（验证调用栈深度）
   - `loop_trace.zhc`：循环追踪（验证迭代次数）
   - `branch_trace.zhc`：分支追踪（验证路径覆盖）

2. 验证：
```cpp
TEST_F(TraceIntegration, FibonacciTrace) {
    // 编译并追踪
    int rc = system("zhc compile fibonacci.zhc --trace -o fib");
    ASSERT_EQ(rc, 0);

    // 验证 trace.json
    auto Data = TraceSerializer::read("trace.json");
    EXPECT_GT(Data.Events.size(), 0u);
    EXPECT_EQ(Data.Metadata.SourceFile, "fibonacci.zhc");

    // 验证调用栈
    auto CallStack = Data.CallStack;
    EXPECT_EQ(CallStack[0].Function, "main");
    // fibonacci 递归调用应有多次进栈
    EXPECT_GT(CallStack.size(), 2u);

    // 验证 HTML 可打开（检查文件非空）
    std::ifstream Html("trace.html");
    std::string Content((std::istreambuf_iterator<char>(Html)),
                        std::istreambuf_iterator<char>());
    EXPECT_GT(Content.size(), 100u);  // HTML 不为空
}
```

**验收标准**:
```bash
zhc run --trace fibonacci.zhc
# 输出 trace.json + trace.html
# HTML 包含: 逐行轨迹 + 变量追踪 + 调用栈 + 分支高亮
```

**工时**: 20h

---

## 3.4 Phase 3 Go/No-Go 检查点

| 检查项 | 验收命令 | 通过标准 |
|:---|:---|:---|
| **探针注入** | `zhc compile --trace hello.zhc` | IR 中包含 `__zhc_trace_*` 调用 |
| **trace.json** | `python3 -c "json.load(open('trace.json'))"` | JSON 格式正确 |
| **trace.html** | 浏览器打开 | 中文界面正常显示 |
| **变量追踪** | 在 HTML 中查看 | 变量值随执行变化 |
| **调用栈** | 递归程序追踪 | 调用栈深度正确 |
| **分支高亮** | if/else 追踪 | 执行到的分支高亮 |
| **AI 评估** | 查看理解度报告 | 输出分数 + 建议 |

**量化标准**：
- trace.html 含变量追踪 + 调用栈
- 浏览器正常渲染
- fibonacci 递归追踪完整

**如未通过**：
- 修复 HTML 生成器
- 问题严重则降级为 JSON-only 模式

---

## 3.5 参考资料

| 资料 | 路径 | 用途 |
|:---|:---|:---|
| 可视化追踪设计 | `08-可视化执行追踪层.md` | 功能设计参考 |
| Python 追踪 | `src/zhc/ir/optimization_observer.py` | IR Pass 参考 |
| Python IR | `src/zhc/ir/instructions.py` | IR 指令参考 |
| LLVM Pass 文档 | LLVM 官方文档 WritingAnLLVMNewPMPass | Pass 框架参考 |

# Phase 1：C++ 基础前端

**版本**: v2.0（根据专家优化分析报告修订）
**日期**: 2026-04-13
**基于文档**: `04-模块重写建议.md`、`12-项目规模与工时估算.md`、`15-重构任务执行清单.md`、`16-技术债务清单.md`、`Phase1-5专家优化分析报告.md`
**目标**: 完成 C++ 基础前端所有模块，能够解析 .zhc 文件并输出 AST
**工时**: 960h（含 20% 风险缓冲）
**日历时间**: 约 5 个月
**前置条件**: Phase 0 完成（MVP 可视化追踪可用）

### v2.0 修订说明（对照专家报告）

> 本版本根据 `Phase1-5专家优化分析报告.md` 的 P0/P1 优先级建议进行了以下修订：
> - **P0-1**: 新增 T1.7b ASTContext 设计任务（24h）— 所有 AST 节点的内存管理基础
> - **P0-2**: T1.4 TokenKind 补全到 100+ 条（+8h）— Lexer/Parser 正确性前提
> - **P1-1**: 新增 T1.6b Unicode 规范化与验证（12h）— 中文编程语言的根基
> - **P1-2**: 新增 T1.12b Parser 架构决策（8h）— Parser 可维护性
> - **P1-3**: 新增 T1.2b 构建系统完善（16h）— Conan/PCH/SANitizer
> - **P1-4**: 新增 T1.22b 渐进式迁移工具（8h）— Python→C++ 迁移辅助
> - **结构调整**: T1.18 合并入 T1.17；T1.22 细化为 3 个子任务；任务按附录 A 推荐顺序重排
> - **工时修正**: 各 Task 工时已核实，Task 工时加总 ≈ 500h + 20% 缓冲 + 评审/文档/集成 ≈ 960h

---

## 1.1 阶段目标

本阶段完成 ZhC 编译器的 C++ 前端重写，包括：

1. 项目工程化：CMake + LLVM 18 环境配置
2. 词法分析：C++ Lexer + 中文关键词表
3. 语法分析：递归下降 Parser + AST 节点定义
4. 源码管理：Source Manager（含 UTF-8 支持，修复 A-01 债务）
5. 诊断引擎：中文错误消息 + 错误恢复机制（修复 A-02 债务）
6. 预处理器：基础宏展开 + 条件编译
7. E0 安全特性启动：初始化检查（S02）、未使用变量警告（S13）

---

## 1.2 Month 1：项目搭建 + Lexer

### 任务 1.2.1 项目工程化

#### T1.1 创建 C++ 项目结构

**交付物**: `zhc/` 目录结构

**操作步骤**:
1. 在 `/Users/yuan/Projects/ZhC/` 下创建 `cpp/` 目录
2. 按 `04-模块重写建议.md` 4.3 节创建目录结构：

```
cpp/
├── include/zhc/
│   ├── Lexer.h
│   ├── Parser.h
│   ├── AST.h
│   ├── Sema.h
│   ├── CodeGen.h
│   ├── Diagnostics.h
│   ├── SourceManager.h
│   ├── Driver.h
│   ├── Pipeline.h
│   ├── Linker.h
│   ├── DebugInfo.h
│   ├── Preprocessor.h
│   ├── ai/
│   ├── monitor/
│   └── trace/
├── lib/
├── tools/zhc/
├── runtime/
├── test/
│   ├── unittests/
│   ├── integration/
│   └── fixtures/
└── docs/
```

3. 创建 `.gitignore` 忽略 `build/`、`*.o`、`*.a`

**工时**: 4h

---

#### T1.2 配置 CMake + LLVM 18

**交付物**: `CMakeLists.txt`

**操作步骤**:
1. 创建顶层 `CMakeLists.txt`：
```cmake
cmake_minimum_required(VERSION 3.20)
project(ZhC CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 查找 LLVM 18
find_package(LLVM 18 REQUIRED CONFIG)
message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")

# 包含 LLVM 头文件和库
include_directories(${LLVM_INCLUDE_DIRS})
add_definitions(${LLVM_DEFINITIONS})
link_directories(${LLVM_LIBRARY_DIRS})

# 启用所有目标平台
list(APPEND CMAKE_MODULE_PATH "${LLVM_DIR}/../CMake")
target_link_libraries(${PROJECT_NAME} PUBLIC LLVM)
```

2. 创建 `cpp/include/zhc/CMakeLists.txt`（每个子目录同）
3. 创建 `cpp/test/CMakeLists.txt`，集成 GoogleTest
4. 创建 `cpp/tools/zhc/CMakeLists.txt`（编译器驱动）
5. 运行 `mkdir build && cd build && cmake ..` 验证 LLVM 链接成功

**验收标准**:
```bash
cd cpp/build
cmake .. -G Ninja
ninja  # 不报错即 LLVM 链接成功
```

**工时**: 16h

---

#### T1.2b 构建系统完善（P1-3）

> **来源**: 专家报告 P1-3 建议
> **优先级**: P1（Phase1 期间必须完成）
> **理由**: 对于 100+ 源文件的项目，基础 CMake 配置远远不够

**交付物**: 完善的 CMake 配置（Conan + PCH + SANitizer + Coverage）

**操作步骤**:

1. **Conan 依赖管理**:
```cmake
# conanfile.txt
[requires]
nlohmann_json/3.11.2
gtest/1.14.0

[generators]
CMakeDeps
CMakeToolchain

[layout]
cmake_layout
```

2. **Precompiled Headers**:
```cmake
# CMakeLists.txt
target_precompile_headers(zhc_core PRIVATE
    <vector>
    <string>
    <memory>
    <unordered_map>
    "zhc/Common.h"
)
```

3. **SANitizer 集成**:
```cmake
option(ENABLE_ASAN "Enable AddressSanitizer" ON)
option(ENABLE_USAN "Enable UndefinedBehaviorSanitizer" ON)

if(ENABLE_ASAN)
    target_compile_options(zhc_core PRIVATE -fsanitize=address -fno-omit-frame-pointer)
    target_link_options(zhc_core PRIVATE -fsanitize=address)
endif()

if(ENABLE_USAN)
    target_compile_options(zhc_core PRIVATE -fsanitize=undefined)
    target_link_options(zhc_core PRIVATE -fsanitize=undefined)
endif()
```

4. **Coverage 配置**:
```cmake
option(ENABLE_COVERAGE "Enable code coverage" OFF)
if(ENABLE_COVERAGE)
    target_compile_options(zhc_core PRIVATE --coverage -O0 -g)
    target_link_options(zhc_core PRIVATE --coverage)
endif()
```

5. **LLVM 版本锁定**:
```cmake
# 锁定 LLVM 18 版本（避免 API 变更）
find_package(LLVM 18 REQUIRED CONFIG)
if(NOT LLVM_VERSION_MAJOR VERSION_EQUAL 18)
    message(FATAL_ERROR "ZhC requires LLVM 18.x, found ${LLVM_PACKAGE_VERSION}")
endif()
```

**验收标准**:
```bash
# Conan 依赖安装
conan install . --output-folder=build --build=missing

# ASAN 构建
cmake -B build -DENABLE_ASAN=ON
cmake --build build
./build/bin/zhc_tests  # 运行带 ASAN 的测试

# Coverage 报告
cmake -B build -DENABLE_COVERAGE=ON
cmake --build build
./build/bin/zhc_tests
lcov --capture --directory build --output-file coverage.info
genhtml coverage.info --output-directory coverage_html
```

**工时**: 16h

---

#### T1.3 配置 GoogleTest 测试框架

**交付物**: `test/CMakeLists.txt` + 基础测试桩

**操作步骤**:
1. 在顶层 `CMakeLists.txt` 添加：
```cmake
include(FetchContent)
FetchContent_Declare(
  googletest
  GIT_REPOSITORY https://github.com/google/googletest.git
  GIT_TAG v1.14.0
)
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

enable_testing()
add_subdirectory(test)
```

2. 创建 `test/CMakeLists.txt`：
```cmake
file(GLOB_RECURSE TEST_SOURCES "*.cpp")
add_executable(zhc_tests ${TEST_SOURCES})
target_link_libraries(zhc_tests PRIVATE gtest_main zhc_core)
include(GoogleTest)
gtest_discover_tests(zhc_tests)
```

3. 创建 `test/unittests/lexer_test.cpp` 作为桩测试

**工时**: 8h

---

### 任务 1.2.2 Token 与关键词

#### T1.4 实现 Token 定义（完整 100+ 条）

> **修订说明**: 专家报告 P0-2 指出原版本仅约 15 个 Token，远少于 Python 版 100+ TokenType。
> 本版本补全到完整列表，与 Python 版 `lexer.py` 逐条对照。

**交付物**: `include/zhc/Lexer.h` + `lib/TokenKinds.def`（完整 100+ 条）

**操作步骤**:

1. 创建 `lib/TokenKinds.def`（参考 Clang 的 `TokenKinds.def` 格式）：

```cpp
//===--- TokenKinds.def - Token Kind Definitions ------------------------===//
//
// ZhC Token 类型定义（与 Python 版 lexer.py TokenType 逐条对照）
//
//===----------------------------------------------------------------------===//

#ifndef TOKEN
#define TOKEN(X)
#endif
#ifndef PUNCTUATOR
#define PUNCTUATOR(X, Y) TOKEN(X)
#endif
#ifndef KEYWORD
#define KEYWORD(X) TOKEN(KW_##X)
#endif

//===--- 字面量 Token ---------------------------------------------------===//
TOKEN(INTEGER_LITERAL)      // 整数字面量: 42, 0xFF, 0b1010
TOKEN(FLOAT_LITERAL)        // 浮点字面量: 3.14, 1.0e-10
TOKEN(STRING_LITERAL)       // 字符串字面量: "hello", "中文"
TOKEN(CHAR_LITERAL)         // 字符字面量: 'a', '中'
TOKEN(BOOL_LITERAL)         // 布尔字面量: 真/假
TOKEN(NONE_LITERAL)         // 空字面量: 空

//===--- 标识符 ---------------------------------------------------------===//
TOKEN(IDENTIFIER)           // 标识符: 变量名、函数名等

//===--- 关键字（中文 + 英文）-------------------------------------------===//
// 控制流
KEYWORD(if)                 // 如果
KEYWORD(else)               // 否则
KEYWORD(while)              // 循环/当
KEYWORD(for)                // 循环/对于
KEYWORD(switch)             // 选择
KEYWORD(case)               // 当（case 分支）
KEYWORD(default)            // 默认
KEYWORD(return)             // 返回
KEYWORD(break)              // 跳出
KEYWORD(continue)           // 继续
KEYWORD(yield)              // 产出（协程）

// 类型定义
KEYWORD(func)               // 函数
KEYWORD(var)                // 变量
KEYWORD(const)              // 常量
KEYWORD(let)                // 不可变变量
KEYWORD(struct)             // 结构体
KEYWORD(enum)               // 枚举
KEYWORD(typedef)            // 类型定义
KEYWORD(class)              // 类
KEYWORD(interface)          // 接口
KEYWORD(implements)         // 实现
KEYWORD(extends)            // 继承

// 类型关键字
KEYWORD(int)                // 整数型
KEYWORD(float)              // 浮点型
KEYWORD(char)               // 字符型
KEYWORD(bool)               // 布尔型
KEYWORD(void)               // 空型
KEYWORD(string)             // 字符串型

// 访问控制
KEYWORD(public)             // 公有
KEYWORD(private)            // 私有
KEYWORD(protected)          // 保护
KEYWORD(static)             // 静态
KEYWORD(extern)             // 外部

// 内存管理
KEYWORD(new)                // 新建
KEYWORD(delete)             // 删除
KEYWORD(sizeof)             // 大小
KEYWORD(typeof)             // 类型
KEYWORD(alignof)            // 对齐

// 智能指针（Python 版已有）
KEYWORD(unique_ptr)         // 独享指针
KEYWORD(shared_ptr)         // 共享指针
KEYWORD(weak_ptr)           // 弱指针
KEYWORD(move)               // 移动

// 异常处理（Python 版已有）
KEYWORD(try)                // 尝试
KEYWORD(catch)              // 捕获
KEYWORD(finally)            // 最终
KEYWORD(throw)              // 抛出

// 协程/异步（Python 版已有）
KEYWORD(async)              // 异步
KEYWORD(await)              // 等待

// 模块系统
KEYWORD(import)             // 导入
KEYWORD(module)             // 模块
KEYWORD(from)               // 从
KEYWORD(with)               // 伴随

// 泛型（Python 版已有）
KEYWORD(generic)            // 泛型
KEYWORD(where)              // 约束
KEYWORD(constraints)        // 约束条件

// 安全特性（Python 版已有）
KEYWORD(shared)             // 共享型
KEYWORD(thread_local)       // 线程独享型
KEYWORD(result)             // 结果型
KEYWORD(nullable)           // 可空型
KEYWORD(overflow_check)     // 溢出检查
KEYWORD(bounds_check)       // 边界检查

// 其他修饰符
KEYWORD(operator)           // 运算符重载
KEYWORD(override)           // 覆盖
KEYWORD(virtual)            // 虚函数
KEYWORD(abstract)           // 抽象
KEYWORD(sealed)             // 封闭
KEYWORD(mutable)            // 可变
KEYWORD(volatile)           // 易变
KEYWORD(inline)             // 内联

//===--- 运算符 ---------------------------------------------------------===//
// 算术运算符
PUNCTUATOR(plus, "+")       // 加
PUNCTUATOR(minus, "-")      // 减
PUNCTUATOR(star, "*")       // 乘
PUNCTUATOR(slash, "/")      // 除
PUNCTUATOR(percent, "%")    // 取模

// 位运算符
PUNCTUATOR(amp, "&")        // 位与
PUNCTUATOR(pipe, "|")       // 位或
PUNCTUATOR(caret, "^")      // 位异或
PUNCTUATOR(tilde, "~")      // 位取反
PUNCTUATOR(shl, "<<")       // 左移
PUNCTUATOR(shr, ">>")       // 右移

// 逻辑运算符
PUNCTUATOR(and, "&&")       // 逻辑与
PUNCTUATOR(or, "||")        // 逻辑或
PUNCTUATOR(not, "!")        // 逻辑非

// 比较运算符
PUNCTUATOR(eq, "==")        // 等于
PUNCTUATOR(neq, "!=")       // 不等于
PUNCTUATOR(lt, "<")         // 小于
PUNCTUATOR(gt, ">")         // 大于
PUNCTUATOR(le, "<=")        // 小于等于
PUNCTUATOR(ge, ">=")        // 大于等于

// 赋值运算符
PUNCTUATOR(equal, "=")      // 赋值
PUNCTUATOR(pluseq, "+=")    // 加赋值
PUNCTUATOR(minuseq, "-=")   // 减赋值
PUNCTUATOR(stareq, "*=")    // 乘赋值
PUNCTUATOR(slashq, "/=")    // 除赋值
PUNCTUATOR(percenteq, "%=") // 取模赋值
PUNCTUATOR(ampeq, "&=")     // 位与赋值
PUNCTUATOR(pipeeq, "|=")    // 位或赋值
PUNCTUATOR(careteq, "^=")   // 位异或赋值
PUNCTUATOR(shleq, "<<=")    // 左移赋值
PUNCTUATOR(shreq, ">>=")    // 右移赋值

// 其他运算符
PUNCTUATOR(arrow, "->")     // 指针成员访问
PUNCTUATOR(dot, ".")        // 成员访问
PUNCTUATOR(arrow_star, "->*") // 指针成员指针访问
PUNCTUATOR(question, "?")   // 三元条件
PUNCTUATOR(colon, ":")      // 三元条件/标签
PUNCTUATOR(double_colon, "::") // 作用域
PUNCTUATOR(ellipsis, "...") // 可变参数

// 范围运算符（Python 版已有）
PUNCTUATOR(dot_dot, "..")   // 范围（开区间）
PUNCTUATOR(dot_dot_eq, "..=") // 范围（闭区间）

//===--- 标点符号 -------------------------------------------------------===//
PUNCTUATOR(lparen, "(")     // 左圆括号
PUNCTUATOR(rparen, ")")     // 右圆括号
PUNCTUATOR(lbrace, "{")     // 左花括号
PUNCTUATOR(rbrace, "}")     // 右花括号
PUNCTUATOR(lbracket, "[")   // 左方括号
PUNCTUATOR(rbracket, "]")   // 右方括号
PUNCTUATOR(comma, ",")      // 逗号
PUNCTUATOR(semi, ";")       // 分号
PUNCTUATOR(hash, "#")       // 预处理指令
PUNCTUATOR(at, "@")         // 属性标记
PUNCTUATOR(dollar, "$")     // 特殊标记
PUNCTUATOR(backquote, "`")  // 反引号

//===--- 特殊 Token -----------------------------------------------------===//
TOKEN(eof)                  // 文件结束
TOKEN(indent)               // 缩进增加（Python 式）
TOKEN(dedent)               // 缩进减少
TOKEN(newline)              // 换行
TOKEN(comment)              // 注释
TOKEN(unknown)              // 未知/非法字符

//===--- 中文关键字映射（Keywords.h 中使用）----------------------------===//
// 注意：中文关键字在 Keywords.h 中映射到对应的 KW_* Token
// 例如: "如果" → KW_if, "否则" → KW_else

#undef TOKEN
#undef PUNCTUATOR
#undef KEYWORD
```

2. 实现 Token 结构体：

```cpp
// include/zhc/Lexer.h
namespace zhc {

// Token 类型（从 TokenKinds.def 生成）
enum class TokenKind {
#define TOKEN(X) X,
#define PUNCTUATOR(X, Y) X,
#define KEYWORD(X) KW_##X,
#include "TokenKinds.def"
};

struct Token {
    TokenKind Kind = TokenKind::unknown;
    llvm::SMLoc Location;          // 源码位置（含文件名/行/列）
    llvm::StringRef Spelling;      // Token 原文
    uint64_t IntegerValue = 0;    // 整数字面量值
    std::string StringValue;       // 字符串字面量值
};

// Token 辅助函数
StringRef getTokenName(TokenKind K);
bool isKeyword(TokenKind K);
bool isPunctuator(TokenKind K);
bool isLiteral(TokenKind K);
bool isAssignmentOperator(TokenKind K);
bool isBinaryOperator(TokenKind K);
unsigned getBinOpPrecedence(TokenKind K);
} // namespace zhc
```

3. **Python 版对照检查清单**（确保零遗漏）：

| Python TokenType | C++ TokenKind | 状态 |
|:---|:---|:---:|
| INTEGER | INTEGER_LITERAL | ✅ |
| FLOAT | FLOAT_LITERAL | ✅ |
| STRING | STRING_LITERAL | ✅ |
| CHAR | CHAR_LITERAL | ✅ |
| BOOL | BOOL_LITERAL | ✅ |
| NONE | NONE_LITERAL | ✅ |
| IDENTIFIER | IDENTIFIER | ✅ |
| IF | KW_if | ✅ |
| ELSE | KW_else | ✅ |
| WHILE | KW_while | ✅ |
| FOR | KW_for | ✅ |
| SWITCH | KW_switch | ✅ |
| CASE | KW_case | ✅ |
| DEFAULT | KW_default | ✅ |
| RETURN | KW_return | ✅ |
| BREAK | KW_break | ✅ |
| CONTINUE | KW_continue | ✅ |
| FUNC | KW_func | ✅ |
| STRUCT | KW_struct | ✅ |
| ENUM | KW_enum | ✅ |
| IMPORT | KW_import | ✅ |
| MODULE | KW_module | ✅ |
| TRY | KW_try | ✅ |
| CATCH | KW_catch | ✅ |
| FINALLY | KW_finally | ✅ |
| THROW | KW_throw | ✅ |
| ASYNC | KW_async | ✅ |
| AWAIT | KW_await | ✅ |
| YIELD | KW_yield | ✅ |
| UNIQUE_PTR | KW_unique_ptr | ✅ |
| SHARED_PTR | KW_shared_ptr | ✅ |
| WEAK_PTR | KW_weak_ptr | ✅ |
| MOVE | KW_move | ✅ |
| GENERIC | KW_generic | ✅ |
| WHERE | KW_where | ✅ |
| ... | ... | ✅ |

**参考**: Python 版本 `src/zhc/parser/lexer.py` 第 30-120 行

**工时**: 16h（原 8h + 专家建议 +8h）

---

#### T1.5 实现中文关键词表

**交付物**: `include/zhc/Keywords.h`

**操作步骤**:
1. 参考 Python 版本 `src/zhc/keywords.py`（约 216 行，100+ 中文关键词映射）
2. 创建 `include/zhc/Keywords.h`：

```cpp
// include/zhc/Keywords.h
namespace zhc {

// 中文关键词映射表（从 Python keywords.py 迁移）
struct KeywordMapping {
    const char *Chinese;    // 中文关键词，如 "如果"
    const char *English;    // 英文等价，如 "if"
    TokenKind Kind;         // TokenKind
};

// 查找中文关键词
TokenKind lookupKeyword(llvm::StringRef Spelling);

// 所有关键词列表（用于词法分析）
extern const KeywordMapping Keywords[];

} // namespace zhc
```

3. 实现 `lib/Keywords.cpp`，从 Python 的 `keywords.py` 逐条迁移：
   - 控制流：`如果`/`否则`/`选择`/`当`/`循环`/`当`/`跳出`/`继续`/`返回`
   - 类型：`整数型`/`浮点型`/`字符型`/`布尔型`/`空型`/`结构体`/`枚举`
   - 声明：`函数`/`变量`/`常量`/`公有`/`私有`
   - 内存：`申请内存`/`释放内存`/`取地址`
   - 智能指针：`独享指针`/`共享指针`/`弱指针`
   - 异常：`尝试`/`捕获`/`抛出`
   - 关键字：`空指针`/`空`/`真`/`假`/`模块`/`导入`
   - 泛型：`泛型`/`约束`
   - 安全特性：`共享型`/`线程独享型`/`结果型`
   - 安全增强：`溢出检查`/`边界检查`
   - ……（全部 100+ 个关键词）

**参考**: Python 版本 `src/zhc/keywords.py`

**工时**: 8h

---

### 任务 1.2.3 C++ Lexer 实现

#### T1.6 实现词法分析器

**交付物**: `lib/Lexer.cpp`

**操作步骤**:
1. 参考 Python 版本 `src/zhc/parser/lexer.py` 的词法分析逻辑
2. 实现 `Lexer` 类：

```cpp
// include/zhc/Lexer.h
class Lexer {
public:
    Lexer(const llvm::SourceMgr &SrcMgr, DiagnosticsEngine &Diags);

    /// 词法分析主入口：返回下一个 Token
    Token nextToken();

    /// 向前看 N 个 Token（用于 Parser）
    Token lookAhead(unsigned N = 1);

private:
    // 词法分析状态
    const char *BufferStart = nullptr;
    const char *BufferEnd = nullptr;
    const char *CurPtr = nullptr;
    llvm::SMLoc CurLoc;

    DiagnosticsEngine &Diags;
    llvm::SourceMgr &SrcMgr;

    // 词法分析辅助方法
    void skipWhitespace();
    Token lexIdentifier();    // 标识符/关键词
    Token lexNumber();        // 数字字面量
    Token lexString();        // 字符串字面量（UTF-8 支持！）
    Token lexComment();       // 注释
    Token lexPunctuator();    // 标点符号
    Token formToken(TokenKind K);

    // Unicode 支持（修复 A-01 债务）
    bool isUnicodeStart(unsigned char C);
    bool isUnicodeContinue(unsigned char C);
    llvm::StringRef readUnicodeEscape(const char *&Ptr);
};
```

3. **关键实现要点**：
   - UTF-8 编码支持（修复 Python 版的 A-01 债务）
   - 中文标识符支持：`整数型 x = 0;` 中的 `整数型` 识别为关键词
   - Token 位置信息：`llvm::SMLoc` 记录文件名+行+列
   - 多字符运算符识别：`==` `!=` `<=` `>=` `&&` `||` `->` `++` `--`
   - 字符串字面量支持 UTF-8（`"中文"`, `"你好世界"`）

**参考**: Python 版本 `src/zhc/parser/lexer.py` 第 120-300 行

**工时**: 40h

---

#### T1.7 Lexer 单元测试

**交付物**: `test/unittests/lexer_test.cpp`

**操作步骤**:
1. 迁移 Python 测试到 C++，覆盖以下场景：
   - ASCII 关键字识别：`如果` `否则` `循环`
   - 中文标识符：`变量 x = 5;`
   - 数字字面量：`42` `3.14` `0xFF` `0b1010`
   - 字符串字面量：`"hello"` `"中文"` `"UTF-8 ✓"`
   - 注释：`// 这是注释` `/* 多行注释 */`
   - 运算符：`+ - * / % == != <= >= && ||`
   - 位置信息正确：`llvm::SMLoc` 行列号正确
   - 错误处理：非法字符、不完整字符串

2. 测试文件 fixture：`test/fixtures/lexer/`
   - `basic_tokens.zhc`
   - `chinese_keywords.zhc`
   - `unicode_strings.zhc`
   - `numbers.zhc`
   - `operators.zhc`

**验收标准**:
```bash
cd cpp/build
ctest -R Lexer --output-on-failure
# 所有测试通过
```

**工时**: 16h

---

#### T1.6b Unicode 规范化与验证（P1-1）

> **来源**: 专家报告 P1-1
> **优先级**: P1（中文编程语言的根基）
> **理由**: ZhC 作为中文编程语言，必须处理各种 Unicode 边界情况。当前 T1.6 Lexer 虽提到 UTF-8 支持，但缺乏具体的 Unicode 边界情况处理规范。

**交付物**: `include/zhc/Unicode.h` + `lib/Unicode.cpp` + Unicode 测试用例集

**操作步骤**:

1. 选定 Unicode 处理方案：
   - **推荐**: 使用 LLVM 的 `llvm/Support/Unicode.h`（零额外依赖，LLVM 已提供 Unicode 分类函数）
   - **备选**: ICU4C（功能更强，但增加外部依赖）
   - 对于标识符分类（XID_Start/XID_Continue），使用 Unicode UAX #31 标准

2. 创建 `include/zhc/Unicode.h`：

```cpp
//===--- Unicode.h - Unicode 支持工具 -----------------------------------===//
//
// 中文编程语言的 Unicode 处理工具集
// 遵循 Unicode UAX #31（Identifier and Pattern Syntax）
//
//===----------------------------------------------------------------------===//

#pragma once
#include "llvm/ADT/StringRef.h"
#include <cstdint>

namespace zhc {
namespace unicode {

/// 是否为 Unicode 标识符起始字符（XID_Start）
/// 包含: CJK 统一汉字、拉丁字母、下划线等
bool isXIDStart(uint32_t CodePoint);

/// 是否为 Unicode 标识符延续字符（XID_Continue）
/// 包含: XID_Start + 数字 + 连接符等
bool isXIDContinue(uint32_t CodePoint);

/// 是否为 CJK 统一汉字（U+4E00 ~ U+9FFF + 扩展区）
bool isCJKCharacter(uint32_t CodePoint);

/// 是否为中文标点（需特殊处理的场景）
bool isChinesePunctuation(uint32_t CodePoint);

/// 是否为 Unicode 空格字符（不只是 ASCII 空格）
bool isUnicodeWhitespace(uint32_t CodePoint);

/// UTF-8 解码：从缓冲区读取一个 Unicode 码点
/// @returns 码点数量（字节数），0 表示无效 UTF-8
unsigned decodeUTF8(const char *Ptr, uint32_t &CodePoint);

/// UTF-8 编码：将 Unicode 码点写入缓冲区
/// @returns 写入的字节数
unsigned encodeUTF8(uint32_t CodePoint, char *Out);

/// 获取 UTF-8 序列的字节长度（由首字节判断）
unsigned getUTF8SequenceLength(unsigned char FirstByte);

/// 计算字符串中的 Unicode 字符数（而非字节数）
size_t countCodePoints(llvm::StringRef Str);

/// Unicode 规范化（NFC）— 将等价序列统一为规范形式
llvm::StringRef normalizeNFC(llvm::StringRef Input);

} // namespace unicode
} // namespace zhc
```

3. **ZhC 特有的 Unicode 场景处理表**：

| 场景 | 示例 | 处理要求 | 优先级 |
|:---|:---|:---|:---:|
| 中文标识符 | `变量_张三 = 5` | UTF-8 多字节作为标识符部分 | P0 |
| 中文关键字 | `如果 (条件) { ... }` | Keyword 表中完整映射 | P0 |
| 混合源码 | `整数型 数组大小 = 1024; // 注释` | ASCII + CJK 混合 | P0 |
| Unicode 转义 | `\u4e00`, `\U0001f600` | 词法级转义序列 | P1 |
| Unicode 空格 | U+00A0 (NBSP) | 缩进处理中识别 | P1 |
| 全角标点 | `（` `）` `；` | 提示用户使用半角 | P2 |
| Emoji 标识符 | `🎉 = 42` | UAX #31 下合法，需支持 | P3 |

4. 编写 Unicode 测试用例集（至少 30 个）：

```cpp
// test/unittests/unicode_test.cpp
TEST(Unicode, CJKIdentifiers) {
    EXPECT_TRUE(unicode::isXIDStart(0x4E00));     // '一'
    EXPECT_TRUE(unicode::isXIDStart(0x5F20));     // '张'
    EXPECT_TRUE(unicode::isXIDContinue(0x4E09));  // '三'
}

TEST(Unicode, UTF8Decoding) {
    const char *Zhong = "\xe4\xb8\xad";  // '中' U+4E2D
    uint32_t CP;
    unsigned Len = unicode::decodeUTF8(Zhong, CP);
    EXPECT_EQ(Len, 3u);
    EXPECT_EQ(CP, 0x4E2Du);
}

TEST(Unicode, MixedSourceLine) {
    // "整数型 数组大小 = 1024;"
    llvm::StringRef Line = "\xe6\x95\xb4\xe6\x95\xb0\xe5\x9e\x8b"
                           " \xe6\x95\xb0\xe7\xbb\x84\xe5\xa4\xa7\xe5\xb0\x8f"
                           " = 1024;";
    EXPECT_EQ(unicode::countCodePoints(Line), 17u);
}

TEST(Unicode, ChinesePunctuation) {
    EXPECT_TRUE(unicode::isChinesePunctuation(0xFF08));   // （
    EXPECT_TRUE(unicode::isChinesePunctuation(0xFF09));   // ）
    EXPECT_TRUE(unicode::isChinesePunctuation(0xFF1B));   // ；
}
```

**参考**:
- Unicode UAX #31（Identifier and Pattern Syntax）
- Python 版 `src/zhc/parser/lexer.py` 中的 UTF-8 处理逻辑
- LLVM `llvm/Support/Unicode.h` + `llvm/Support/ConvertUTF.h`

**工时**: 12h

---

## 1.3 Month 2：Parser + AST

### 任务 1.3.0 AST 内存管理基础

#### T1.7b 实现 ASTContext 内存管理（P0-1）

> **来源**: 专家报告 P0-1（🔴 Critical）
> **优先级**: P0（所有 AST 节点的内存管理基础，必须先于 T1.8 完成）
> **理由**: T1.8 及后续 Parser 代码中大量使用 `new (Context)` 语法（如 `new (Context) BinaryOperator(...)`），但从未定义 `ASTContext` 类。这是整个 C++ 前端的**基石性缺陷**——没有 ASTContext，所有 new 出来的节点谁来释放？裸指针到处传递必然导致内存泄漏。

**交付物**: `include/zhc/ASTContext.h` + `lib/ASTContext.cpp`

**操作步骤**:

1. 创建 `include/zhc/ASTContext.h`：

```cpp
//===--- ASTContext.h - AST 所有权上下文 ---------------------------------===//
//
// 管理 AST 节点的内存生命周期
// 设计原则:
// 1. 大多数 AST 节点使用 BumpPtrAllocator（arena 分配，批量释放）
// 2. 需要析构的节点（如含 std::string 的节点）使用单独跟踪
// 3. 内置类型单例（VoidTy, Int32Ty 等）只创建一次
// 4. 线程不安全（单线程 per compilation）
//
//===----------------------------------------------------------------------===//

#pragma once
#include "zhc/Types.h"
#include "zhc/AST.h"
#include "llvm/Support/Allocator.h"
#include "llvm/ADT/DenseMap.h"
#include "llvm/ADT/ArrayRef.h"
#include <vector>
#include <functional>

namespace zhc {

class SourceManager;

class ASTContext {
public:
    explicit ASTContext(SourceManager &SM);
    ~ASTContext();

    // === Arena 分配 ===

    /// 在 arena 中创建对象（无析构调用，适用于 POD/平凡析构的 AST 节点）
    template<typename T, typename... Args>
    T *create(Args &&... args) {
        return new (Allocator.Allocate(sizeof(T), alignof(T)))
            T(std::forward<Args>(args)...);
    }

    /// 需要析构的对象（适用于含 std::string/std::vector 等成员的节点）
    template<typename T, typename... Args>
    T *createWithDtor(Args &&... args) {
        auto *mem = Allocator.Allocate(sizeof(T), alignof(T));
        T *obj = new (mem) T(std::forward<Args>(args)...);
        TrackedAllocations.push_back([obj]() { obj->~T(); });
        return obj;
    }

    // === 内置类型缓存 ===

    /// 初始化内置类型（构造函数中调用）
    void initBuiltinTypes();

    QualType getVoidTy()    const { return VoidTy; }
    QualType getBoolTy()    const { return BoolTy; }
    QualType getInt8Ty()    const { return Int8Ty; }
    QualType getInt16Ty()   const { return Int16Ty; }
    QualType getInt32Ty()   const { return Int32Ty; }
    QualType getInt64Ty()   const { return Int64Ty; }
    QualType getFloat32Ty() const { return Float32Ty; }
    QualType getFloat64Ty() const { return Float64Ty; }
    QualType getStringTy()  const { return StringTy; }
    QualType getCharTy()    const { return CharTy; }

    /// 获取/创建指针类型（自动缓存，避免重复分配）
    QualType getPointerType(QualType Pointee);

    /// 获取/创建数组类型（自动缓存）
    QualType getArrayType(QualType Element, uint64_t Size);

    /// 获取/创建函数类型（自动缓存）
    QualType getFunctionType(QualType Ret, llvm::ArrayRef<QualType> Params);

    // === 类型 canonicalization ===

    /// 获取类型的规范化形式（去掉 typedef/sugar）
    QualType getCanonicalType(QualType T);

    /// 两个类型是否相同（忽略 sugar/qualifiers）
    bool typesAreSame(QualType T1, QualType T2);

    // === 查询 ===
    SourceManager &getSourceManager() const { return SM; }

    /// 获取总分配大小（用于内存统计）
    size_t getTotalMemory() const;

private:
    llvm::BumpPtrAllocator Allocator;
    SourceManager &SM;

    // 内置类型单例
    QualType VoidTy, BoolTy;
    QualType Int8Ty, Int16Ty, Int32Ty, Int64Ty;
    QualType Float32Ty, Float64Ty;
    QualType StringTy, CharTy;

    // 类型缓存（避免重复创建相同类型）
    llvm::DenseMap<std::pair<Type*, unsigned>, PointerType*> PointerTypes;
    llvm::DenseMap<std::pair<Type*, uint64_t>, ArrayType*> ArrayTypes;
    llvm::DenseMap<unsigned, FunctionType*> FunctionTypes;

    // 需要析构的分配
    std::vector<std::function<void()>> TrackedAllocations;

    // ASTContext 不可拷贝
    ASTContext(const ASTContext &) = delete;
    void operator=(const ASTContext &) = delete;
};

} // namespace zhc
```

2. 实现 `lib/ASTContext.cpp`：

```cpp
//===--- ASTContext.cpp - AST 所有权上下文实现 ---------------------------===//

#include "zhc/ASTContext.h"
#include "zhc/SourceManager.h"

namespace zhc {

ASTContext::ASTContext(SourceManager &SM) : SM(SM) {
    initBuiltinTypes();
}

ASTContext::~ASTContext() {
    // 先调用需要析构的节点的析构函数
    for (auto &Dtor : TrackedAllocations) {
        Dtor();
    }
    TrackedAllocations.clear();
    // BumpPtrAllocator 自动释放所有 arena 内存
}

void ASTContext::initBuiltinTypes() {
    // 创建内置类型的单例
    VoidTy    = QualType(create<BuiltinType>(BuiltinType::Void), 0);
    BoolTy    = QualType(create<BuiltinType>(BuiltinType::Bool), 0);
    Int8Ty    = QualType(create<BuiltinType>(BuiltinType::Int8), 0);
    Int16Ty   = QualType(create<BuiltinType>(BuiltinType::Int16), 0);
    Int32Ty   = QualType(create<BuiltinType>(BuiltinType::Int32), 0);
    Int64Ty   = QualType(create<BuiltinType>(BuiltinType::Int64), 0);
    Float32Ty = QualType(create<BuiltinType>(BuiltinType::Float32), 0);
    Float64Ty = QualType(create<BuiltinType>(BuiltinType::Float64), 0);
    CharTy    = QualType(create<BuiltinType>(BuiltinType::Char), 0);
    StringTy  = QualType(create<BuiltinType>(BuiltinType::String), 0);
}

QualType ASTContext::getPointerType(QualType Pointee) {
    auto Key = std::make_pair(Pointee.getTypePtr(), Pointee.getQualifiers());
    auto It = PointerTypes.find(Key);
    if (It != PointerTypes.end())
        return QualType(It->second, 0);

    auto *PtrTy = create<PointerType>(Pointee);
    PointerTypes[Key] = PtrTy;
    return QualType(PtrTy, 0);
}

QualType ASTContext::getArrayType(QualType Element, uint64_t Size) {
    auto Key = std::make_pair(Element.getTypePtr(), Size);
    auto It = ArrayTypes.find(Key);
    if (It != ArrayTypes.end())
        return QualType(It->second, 0);

    auto *ArrTy = create<ArrayType>(Element, Size);
    ArrayTypes[Key] = ArrTy;
    return QualType(ArrTy, 0);
}

size_t ASTContext::getTotalMemory() const {
    return Allocator.getTotalMemory();
}

} // namespace zhc
```

3. **ASTContext 使用约定**（所有 AST 节点创建必须通过 Context）：

```cpp
// ✅ 正确：通过 ASTContext 创建节点
BinaryOperator *BinOp = Context.create<BinaryOperator>(Op, LHS, RHS);

// ❌ 错误：裸 new（会导致内存泄漏）
BinaryOperator *BinOp = new BinaryOperator(Op, LHS, RHS);

// ✅ 需要析构的节点用 createWithDtor
StringLiteral *Str = Context.createWithDtor<StringLiteral>("你好世界");
```

4. **参考**: Clang `clang/AST/ASTContext.h`（约 3000 行，Clang 最核心的数据结构之一）

**验收标准**:
```cpp
// ASTContext 单元测试
TEST(ASTContext, BuiltinTypes) {
    ASTContext Ctx(SM);
    EXPECT_TRUE(Ctx.typesAreSame(Ctx.getInt32Ty(), Ctx.getInt32Ty()));
    EXPECT_FALSE(Ctx.typesAreSame(Ctx.getInt32Ty(), Ctx.getFloat64Ty()));
}

TEST(ASTContext, PointerTypeCaching) {
    ASTContext Ctx(SM);
    auto Ptr1 = Ctx.getPointerType(Ctx.getInt32Ty());
    auto Ptr2 = Ctx.getPointerType(Ctx.getInt32Ty());
    EXPECT_EQ(Ptr1.getTypePtr(), Ptr2.getTypePtr());  // 相同指针 = 缓存命中
}

TEST(ASTContext, ArenaAllocation) {
    ASTContext Ctx(SM);
    auto *Lit = Ctx.create<IntegerLiteral>(42);
    EXPECT_NE(Lit, nullptr);
    // 无需 delete — Ctx 析构时自动释放
}
```

**工时**: 24h

---

### 任务 1.3.1 AST 节点体系设计

#### T1.8 设计并实现 AST 节点

**交付物**: `include/zhc/AST.h` + `lib/AST.cpp`

**操作步骤**:
1. 参考 Python 版本 `src/zhc/parser/ast_nodes.py`（76+ 节点类型，~3,011 行）
2. 实现 C++ AST 继承体系（修复 Python 版的 B-01 债务）：

```cpp
// include/zhc/AST.h
namespace zhc {
namespace ast {

// 所有 AST 节点的基类
class ASTNode {
public:
    virtual ~ASTNode() = default;
    virtual void accept(ASTVisitor &V) = 0;
    SourceRange getSourceRange() const { return Range; }
protected:
    SourceRange Range;
};

// 表达式节点
class Expr : public ASTNode {};                    // 表达式基类
class IntegerLiteral : public Expr {};             // 整数字面量
class FloatLiteral : public Expr {};               // 浮点字面量
class StringLiteral : public Expr {};              // 字符串字面量
class Identifier : public Expr {};                 // 标识符
class BinaryOperator : public Expr {};             // 二元运算符
class UnaryOperator : public Expr {};               // 一元运算符
class CallExpr : public Expr {};                   // 函数调用
class IndexExpr : public Expr {};                  // 数组索引
class MemberExpr : public Expr {};                 // 成员访问
class CastExpr : public Expr {};                   // 类型转换
class ConditionalExpr : public Expr {};            // 条件表达式

// 语句节点
class Stmt : public ASTNode {};                    // 语句基类
class ExprStmt : public Stmt {};                   // 表达式语句
class CompoundStmt : public Stmt {};                // 复合语句 {}
class IfStmt : public Stmt {};                     // if/else
class WhileStmt : public Stmt {};                  // while 循环
class ForStmt : public Stmt {};                   // for 循环
class ReturnStmt : public Stmt {};                // return
class BreakStmt : public Stmt {};                  // break
class ContinueStmt : public Stmt {};               // continue
class SwitchStmt : public Stmt {};                 // switch（对应 `选择`）
class CaseStmt : public Stmt {};                   // case
class DefaultStmt : public Stmt {};                // default

// 声明节点
class Decl : public ASTNode {};                    // 声明基类
class FunctionDecl : public Decl {};              // 函数声明
class VarDecl : public Decl {};                    // 变量声明
class ParamDecl : public Decl {};                  // 参数声明
class TypeDecl : public Decl {};                   // 类型声明（struct/enum/typedef）
class StructDecl : public TypeDecl {};             // 结构体
class EnumDecl : public TypeDecl {};               // 枚举
class ImportDecl : public Decl {};                 // import 声明

// 类型节点
class Type : public ASTNode {};                    // 类型基类
class BuiltinType : public Type {};                // 内置类型（int/float等）
class PointerType : public Type {};                // 指针类型
class ArrayType : public Type {};                  // 数组类型
class FunctionType : public Type {};               // 函数类型
class StructType : public Type {};                 // 结构体类型
class EnumType : public Type {};                  // 枚举类型
class NullableType : public Type {};               // ?空型<T> 可空类型

// 翻译单元
class TranslationUnit : public ASTNode {
public:
    std::vector<Decl *> Decls;
};

} // namespace ast
} // namespace zhc
```

3. 实现 AST 节点的 `accept` 方法（Visitor 模式）
4. 每个节点携带 `SourceRange`（修复 Python 版的 B-02 债务）

**参考**: Python 版本 `src/zhc/parser/ast_nodes.py`

**工时**: 20h

---

#### T1.9 实现表达式 Parser

**交付物**: `lib/ParserExpr.cpp`

**操作步骤**:
1. 参考 Python 版本 `src/zhc/parser/parser.py` 中的 `parse_expression` 系列方法
2. 实现递归下降 Parser（支持运算符优先级）：

```cpp
// lib/ParserExpr.cpp
namespace zhc {

Expr *Parser::parseExpression(unsigned MinPrecedence) {
    Expr *LHS = parseUnaryExpr();

    while (true) {
        Token Op = Tok;
        unsigned Precedence = getBinOpPrecedence(Op.Kind);
        if (Precedence < MinPrecedence) break;

        consumeToken();
        Expr *RHS = parseExpression(Precedence + 1);
        LHS = new (Context) BinaryOperator(Op, LHS, RHS);
    }
    return LHS;
}

Expr *Parser::parseUnaryExpr() {
    if (Tok.isOneOf(KW_NOT, '+', '-', '*', '&')) {
        Token Op = Tok;
        consumeToken();
        Expr *Operand = parseUnaryExpr();
        return new (Context) UnaryOperator(Op, Operand);
    }
    return parsePostfixExpr();
}

Expr *Parser::parsePostfixExpr() {
    Expr *E = parsePrimaryExpr();

    while (true) {
        if (Tok.is(KK_LBRACKET)) {
            // 数组索引：arr[0]
            consumeToken();
            Expr *Idx = parseExpression();
            expect(KK_RBRACKET);
            E = new (Context) IndexExpr(E, Idx);
        } else if (Tok.is(KK_LPAREN)) {
            // 函数调用：foo(a, b)
            E = parseCallExpr(E);
        } else if (Tok.is(KK_DOT)) {
            // 成员访问：obj.member
            E = parseMemberExpr(E);
        } else {
            break;
        }
    }
    return E;
}

Expr *Parser::parsePrimaryExpr() {
    switch (Tok.getKind()) {
        case KK_INTEGER: return parseIntegerLiteral();
        case KK_FLOAT:   return parseFloatLiteral();
        case KK_STRING:  return parseStringLiteral();
        case KK_IDENTIFIER: return parseIdentifierExpr();
        case KK_LPAREN:  return parseParenExpr();
        case KW_IF:       return parseIfExpr();  // 三元表达式
        default: Diags.report(diag::err_expected_expression); return nullptr;
    }
}

} // namespace zhc
```

3. 运算符优先级表（参考 C++ 标准）：
   - `||` (1级) → `&&` (2级) → `|` (3级) → `^` (4级) → `&` (5级)
   - `== !=` (6级) → `<> <= >=` (7级) → `<< >>` (8级)
   - `+ -` (9级) → `* / %` (10级)
   - `! ~ ++ -- * & sizeof` (11级，一元)

**参考**: Python 版本 `src/zhc/parser/parser.py` 第 200-500 行

**工时**: 24h

---

#### T1.10 实现语句 Parser

**交付物**: `lib/ParserStmt.cpp`

**操作步骤**:
1. 实现以下语句的解析：

```cpp
// lib/ParserStmt.cpp

Stmt *Parser::parseStatement() {
    switch (Tok.getKind()) {
        case KW_IF:    return parseIfStatement();
        case KW_WHILE: return parseWhileStatement();
        case KW_FOR:   return parseForStatement();
        case KW_SWITCH:
        case KW_SELECT: return parseSwitchStatement(); // `选择` 关键字
        case KW_RETURN: return parseReturnStatement();
        case KW_BREAK:  return new BreakStmt();
        case KW_CONTINUE: return new ContinueStmt();
        case KK_LBRACE: return parseCompoundStatement();
        default:
            // 表达式语句或声明
            if (Tok.isDeclarationStart())
                return parseDeclarationStatement();
            return parseExpressionStatement();
    }
}

// if 语句：`如果 条件 { ... } 否则 { ... }`
Stmt *Parser::parseIfStatement() {
    expect(KW_IF);
    Expr *Cond = parseParenExpression();  // 条件必须带括号
    Stmt *Then = parseStatement();
    Stmt *Else = nullptr;
    if (Tok.is(KW_ELSE)) {  // `否则`
        consumeToken();
        Else = parseStatement();
    }
    return new (Context) IfStmt(Cond, Then, Else);
}

// while 循环：`循环 当 条件 { ... }`
Stmt *Parser::parseWhileStatement() {
    expect(KW_WHILE);
    Expr *Cond = parseParenExpression();
    Stmt *Body = parseStatement();
    return new (Context) WhileStmt(Cond, Body);
}

// for 循环：`循环 (初始化; 条件; 增量) { ... }`
Stmt *Parser::parseForStatement() {
    expect(KW_FOR);
    expect(KK_LPAREN);
    // ... 解析初始化/条件/增量
}

// switch 语句：`选择 (expr) { 当 case1: ... 当 case2: ... 默认: ... }`
// 注意：中文用 `选择` 而非 `switch`，`当` 而非 `case`，`默认:` 而非 `default:`
Stmt *Parser::parseSwitchStatement() {
    expect(KW_SELECT);  // `选择`
    Expr *Expr = parseParenExpression();
    expect(KK_LBRACE);
    std::vector<Stmt *> Cases;
    while (!Tok.is(KK_RBRACE)) {
        if (Tok.is(KW_DEFAULT)) {
            // `默认:` 分支
        } else if (Tok.is(KW_CASE)) {
            // `当` case 分支
        }
    }
    return new (Context) SwitchStmt(Expr, Cases);
}
```

**参考**: Python 版本 `src/zhc/parser/parser.py` 第 500-900 行

**工时**: 24h

---

#### T1.11 实现声明 Parser

**交付物**: `lib/ParserDecl.cpp`

**操作步骤**:
1. 实现变量声明、函数声明、类型声明：

```cpp
// lib/ParserDecl.cpp

// 变量声明：`整数型 x = 5;`
VarDecl *Parser::parseVariableDeclaration() {
    Type *Ty = parseType();                    // `整数型`
    Identifier *Name = parseIdentifier();      // `x`
    VarDecl *VD = new (Context) VarDecl(Name, Ty);

    // 初始化器
    if (Tok.is(KK_EQUAL)) {
        consumeToken();
        VD->setInitializer(parseInitializer());
    }

    // 数组声明：`整数型 arr[10];`
    if (Tok.is(KK_LBRACKET)) {
        consumeToken();
        if (!Tok.is(KK_RBRACKET)) {
            Expr *Size = parseConstantExpression();
            VD->setArraySize(Size);
        }
        expect(KK_RBRACKET);
    }

    expect(KK_SEMICOLON);
    return VD;
}

// 函数声明：`函数 整数型 add(整数型 a, 整数型 b) { ... }`
FunctionDecl *Parser::parseFunctionDeclaration() {
    expect(KW_FUNC);  // `函数`
    Type *RetTy = parseType();              // 返回类型
    Identifier *Name = parseIdentifier();   // 函数名
    expect(KK_LPAREN);

    // 参数列表
    std::vector<ParamDecl *> Params;
    if (!Tok.is(KK_RPAREN)) {
        do {
            ParamDecl *P = parseParameterDeclaration();
            Params.push_back(P);
        } while (consumeIf(KK_COMMA));
    }
    expect(KK_RPAREN);

    // 函数体
    Stmt *Body = nullptr;
    if (Tok.is(KK_LBRACE)) {
        Body = parseCompoundStatement();
    } else {
        expect(KK_SEMICOLON);  // 前向声明
    }

    return new (Context) FunctionDecl(Name, RetTy, Params, Body);
}

// 结构体声明：`结构体 Point { 整数型 x; 整数型 y; }`
StructDecl *Parser::parseStructDeclaration() {
    expect(KW_STRUCT);
    Identifier *Name = parseIdentifier();
    expect(KK_LBRACE);
    std::vector<VarDecl *> Members;
    while (!Tok.is(KK_RBRACE)) {
        Members.push_back(parseVariableDeclaration());
    }
    expect(KK_RBRACE);
    expect(KK_SEMICOLON);
    return new (Context) StructDecl(Name, Members);
}

// 枚举声明：`枚举 Color { 红, 绿, 蓝 }`
EnumDecl *Parser::parseEnumerationDeclaration() {
    expect(KW_ENUM);
    Identifier *Name = parseIdentifier();
    expect(KK_LBRACE);
    std::vector<Identifier *> Enumerators;
    while (!Tok.is(KK_RBRACE)) {
        Enumerators.push_back(parseIdentifier());
        if (consumeIf(KK_EQUAL)) {
            parseConstantExpression();  // 显式值
        }
        consumeIf(KK_COMMA);
    }
    expect(KK_RBRACE);
    expect(KK_SEMICOLON);
    return new (Context) EnumDecl(Name, Enumerators);
}

// 导入声明：`导入 "io.zhc";`
ImportDecl *Parser::parseImportDeclaration() {
    expect(KW_IMPORT);
    StringLiteral *Path = parseStringLiteral();
    expect(KK_SEMICOLON);
    return new (Context) ImportDecl(Path);
}
```

**参考**: Python 版本 `src/zhc/parser/parser.py` 第 900-1500 行

**工时**: 24h

---

#### T1.12 实现类型 Parser

**交付物**: `lib/ParserType.cpp`

**操作步骤**:
1. 实现类型解析，支持以下语法：

```cpp
// lib/ParserType.cpp

Type *Parser::parseType() {
    // 基础类型
    if (Tok.is(KW_INT))    return BuiltinType::Int32;
    if (Tok.is(KW_FLOAT))  return BuiltinType::Float64;
    if (Tok.is(KW_CHAR))   return BuiltinType::Int8;
    if (Tok.is(KW_BOOL))   return BuiltinType::Bool;
    if (Tok.is(KW_VOID))   return BuiltinType::Void;

    // 中文类型别名
    if (Tok.is(KW_INT))    return BuiltinType::Int32;    // 整数型
    if (Tok.is(KW_FLOAT))  return BuiltinType::Float64; // 浮点型
    if (Tok.is(KW_CHAR))   return BuiltinType::Int8;    // 字符型
    if (Tok.is(KW_BOOL))   return BuiltinType::Bool;    // 布尔型

    // 结构体/枚举/typedef
    if (Tok.is(KW_STRUCT)) return parseStructType();
    if (Tok.is(KW_ENUM))   return parseEnumType();
    if (Tok.is(KW_TYPEDEF)) return parseTypedefType();

    // 指针类型：`整数型*` `字符型*`
    Type *Base = parseNonPointerType();
    if (Tok.is(KK_STAR)) {
        consumeToken();
        return new (Context) PointerType(Base);
    }

    // 可空类型：`?空型 整数型*`
    if (Tok.is(KW_NULLABLE)) {  // `?空型`
        consumeToken();
        Type *Inner = parseType();
        return new (Context) NullableType(Inner);
    }

    return Base;
}

// 泛型类型：`泛型<T> 类型名`（Phase 2 实现）
Type *Parser::parseGenericType() {
    // 简化为 Phase 2 任务
    Diags.report(diag::err_generic_not_yet_implemented);
    return nullptr;
}
```

**参考**: Python 版本 `src/zhc/parser/parser.py` 第 1500-2000 行

**工时**: 16h

---

#### T1.12b Parser 架构决策与骨架搭建（P1-2）

> **来源**: 专家报告 P1-2
> **优先级**: P1（Parser 可维护性）
> **理由**: Python 版已有 DeclarationParserMixin/StatementParserMixin/ExpressionParserMixin 但未被使用（R1 重构遗留债务）。C++ 版必须尽早决定 Parser 组织方案，避免重复此债务。

**交付物**: Parser 架构决策文档 + `include/zhc/Parser.h` 骨架

**操作步骤**:

1. **架构方案评估**（以下三种方案择一）：

| 方案 | 描述 | 优点 | 缺点 |
|:---|:---|:---|:---|
| **A: 自由函数 + 按文件拆分** | `parseExpression()` 等作为 Parser 类的方法，按文件拆分 `.cpp` 实现 | 简单直接，编译速度快 | Parser.h 头文件较大 |
| **B: CRTP Mixin** | `DeclarationParserMixin<Parser>` 等 CRTP 模式 | 编译期多态，零运行时开销 | 复杂度高，调试困难，编译时间长 |
| **C: 组合委托** | Parser 持有 `ExprParser*`、`StmtParser*` 等子解析器指针 | 解耦彻底 | 动态分配开销，指针间接调用 |

2. **选定方案 A**（自由函数 + 按文件拆分），理由：
   - ZhC 的 Parser 不需要像 Clang 那样同时支持多种 Frontend（C/C++/ObjC）
   - CRTP Mixin 对编译速度不利（每个模板实例化都重新编译）
   - 当前阶段优先保证正确性，后期可重构为 Mixin
   - 与当前 T1.9-T1.12 的 4 文件拆分方式自然对齐

3. 创建 `include/zhc/Parser.h` 骨架：

```cpp
//===--- Parser.h - 递归下降语法分析器 ---------------------------------===//
//
// 架构方案 A: 单一 Parser 类 + 按文件拆分实现
// - ParserExpr.cpp: 表达式解析（parseExpression, parseUnary, parsePostfix...）
// - ParserStmt.cpp: 语句解析（parseStatement, parseIf, parseWhile...）
// - ParserDecl.cpp: 声明解析（parseFunctionDecl, parseVarDecl...）
// - ParserType.cpp: 类型解析（parseType, parsePointerType...）
//
//===----------------------------------------------------------------------===//

#pragma once
#include "zhc/Lexer.h"
#include "zhc/AST.h"
#include "zhc/ASTContext.h"
#include "zhc/Diagnostics.h"
#include "zhc/SourceManager.h"
#include <vector>

namespace zhc {

class Parser {
public:
    Parser(Lexer &L, ASTContext &Ctx, DiagnosticsEngine &Diags);

    /// 主入口：解析整个翻译单元
    TranslationUnit *parseTranslationUnit();

    // === 表达式解析（ParserExpr.cpp）===
    Expr *parseExpression(unsigned MinPrec = 0);
    Expr *parseUnaryExpr();
    Expr *parsePostfixExpr();
    Expr *parsePrimaryExpr();
    Expr *parseIntegerLiteral();
    Expr *parseFloatLiteral();
    Expr *parseStringLiteral();
    Expr *parseIdentifierExpr();
    Expr *parseParenExpr();
    Expr *parseCallExpr(Expr *Callee);
    Expr *parseMemberExpr(Expr *Object);

    // === 语句解析（ParserStmt.cpp）===
    Stmt *parseStatement();
    Stmt *parseCompoundStatement();
    Stmt *parseIfStatement();
    Stmt *parseWhileStatement();
    Stmt *parseForStatement();
    Stmt *parseSwitchStatement();
    Stmt *parseReturnStatement();
    Stmt *parseExpressionStatement();

    // === 声明解析（ParserDecl.cpp）===
    Decl *parseDeclaration();
    FunctionDecl *parseFunctionDeclaration();
    VarDecl *parseVariableDeclaration();
    StructDecl *parseStructDeclaration();
    EnumDecl *parseEnumerationDeclaration();
    ImportDecl *parseImportDeclaration();
    ParamDecl *parseParameterDeclaration();

    // === 类型解析（ParserType.cpp）===
    Type *parseType();
    Type *parsePointerType(Type *Base);
    Type *parseArrayType(Type *Base);
    Type *parseFunctionType();
    Type *parseGenericType();  // Phase 2 占位

    // === 错误恢复 ===
    void skipUntil(TokenKind K1, TokenKind K2 = TokenKind::eof);
    void skipUntil(std::initializer_list<TokenKind> Kinds);
    bool isStatementStart();
    bool isDeclarationStart();

private:
    Lexer &TheLexer;
    ASTContext &Context;
    DiagnosticsEngine &Diags;

    Token Tok;          // 当前 Token
    SourceManager &SM;

    // Token 操作
    void consumeToken();
    bool consumeIf(TokenKind K);
    bool expect(TokenKind K);
    Token lookAhead(unsigned N = 1);

    // 运算符优先级
    unsigned getBinOpPrecedence(TokenKind K);
};

} // namespace zhc
```

4. **Python 版 Parser 对应关系**：

| Python 文件 | C++ 文件 | 说明 |
|:---|:---|:---|
| `parser.py` `parse_expression()` | `ParserExpr.cpp` | 表达式解析 |
| `parser.py` `parse_statement()` | `ParserStmt.cpp` | 语句解析 |
| `parser.py` `parse_declaration()` | `ParserDecl.cpp` | 声明解析 |
| `parser.py` `parse_type()` | `ParserType.cpp` | 类型解析 |
| `parser.py` `DeclarationParserMixin` | 合并入 `Parser` 类 | 不单独使用 Mixin |
| `parser.py` `StatementParserMixin` | 合并入 `Parser` 类 | 不单独使用 Mixin |
| `parser.py` `ExpressionParserMixin` | 合并入 `Parser` 类 | 不单独使用 Mixin |

**验收标准**:
```bash
# Parser.h 可被其他头文件 include 且编译通过
cd cpp/build && ninja
# 无编译错误
```

**工时**: 8h

---

#### T1.13 错误恢复机制

**交付物**: Parser 中的错误同步逻辑

**操作步骤**:
1. 实现 Parser 错误恢复（修复 Python 版的 A-02 债务）：
   - 参考 Clang 的同步点策略
   - 同步点：`;` `}` 关键字后，或进入新语句块

```cpp
// include/zhc/Parser.h
class Parser {
private:
    // 错误恢复
    void recoverToSynchronizationPoint();
    bool isSynchronizationPoint();
    bool isStatementStart();
    bool isDeclarationStart();

    // 跳过错误直到同步点
    void skipUntil(TokenKind K1, TokenKind K2 = TokenKind::Unknown);
    void skipUntil(std::initializer_list<TokenKind> Kinds);
};

// lib/Parser.cpp
void Parser::skipUntil(TokenKind K1, TokenKind K2) {
    while (!Tok.is(K1) && !Tok.is(K2) && !Tok.is(KK_EOF)) {
        consumeToken();
    }
    if (!Tok.is(KK_EOF)) consumeToken();
}
```

**参考**: Clang `lib/Parse/ParseStmt.cpp` 中的错误恢复部分

**工时**: 12h

---

#### T1.14 Parser 单元测试

**交付物**: `test/unittests/parser_test.cpp`

**操作步骤**:
1. 创建 fixture 测试文件 `test/fixtures/parser/`：
   - `declarations.zhc`（变量/函数/结构体/枚举/导入）
   - `expressions.zhc`（运算/函数调用/数组索引/成员访问）
   - `statements.zhc`（if/while/for/switch/return/break）
   - `control_flow.zhc`（嵌套 if/for 循环/递归）
   - `chinese_keywords.zhc`（全中文关键字）
   - `error_recovery.zhc`（故意写错代码，测试恢复能力）

2. 测试覆盖：
   - 成功解析生成正确 AST
   - 错误消息包含正确行号
   - 错误恢复后继续解析后续代码

**验收标准**:
```bash
ctest -R Parser --output-on-failure
```

**工时**: 20h

---

## 1.4 Month 3：Source Manager + Diagnostics + Preprocessor

### 任务 1.4.1 Source Manager

#### T1.15 实现源码管理器

**交付物**: `include/zhc/SourceManager.h` + `lib/SourceManager.cpp`

**操作步骤**:
1. 实现 `SourceManager` 类（统一管理所有源码文件）：

```cpp
// include/zhc/SourceManager.h
class SourceManager {
public:
    /// 加载源文件
    FileID createMainFileID(llvm::StringRef Filename);

    /// 获取缓冲区内容
    llvm::StringRef getBufferData(FileID FID) const;

    /// 位置操作
    SourceLocation getLocation(FileID FID, unsigned Offset) const;
    std::pair<FileID, unsigned> getDecomposedLoc(SourceLocation Loc) const;

    /// 展开宏位置
    SourceLocation getExpansionLoc(SourceLocation Loc) const;

    /// 行号/列号转换
    unsigned getLineNumber(SourceLocation Loc) const;
    unsigned getColumnNumber(SourceLocation Loc) const;

    /// 文件包含栈
    void pushInclude(SourceLocation IncludeLoc, FileID FileID);
    void popInclude();
    FileID getTopFileID() const;

private:
    llvm::SourceMgr Impl;  // 委托 LLVM SourceMgr
    std::unordered_map<FileID, std::string> FilePaths;
};

// 便捷类型
using FileID = unsigned;
struct SourceLocation {
    FileID FID;
    unsigned Offset;
};
struct SourceRange {
    SourceLocation Start, End;
};
```

2. **关键实现**：完整 UTF-8 支持（修复 Python 版的 A-01 债务）
   - 所有文件以 UTF-8 读取（`llvm::MemoryBuffer::getFile` 默认支持）
   - 行号计算正确处理 UTF-8 多字节字符

**参考**: LLVM `include/llvm/SourceMgr.h`

**工时**: 40h

---

### 任务 1.4.2 诊断引擎

#### T1.16 设计诊断系统

**交付物**: `include/zhc/Diagnostics.h`

**操作步骤**:
1. 参考 Clang 的 Diagnostics 系统设计：

```cpp
// include/zhc/Diagnostics.h
namespace diag {

// 诊断ID枚举
enum DiagID {
#define DIAG(X, LEVEL, MSG) X,
#include "DiagnosticKinds.def"
};

// 诊断级别
enum class Level { Note, Warning, Error, Fatal };

class DiagnosticsEngine {
public:
    DiagnosticsEngine(SourceManager &SM);

    /// 报告诊断
    DiagnosticBuilder report(DiagID ID);

    /// 获取诊断计数器
    unsigned getNumErrors() const { return NumErrors; }
    unsigned getNumWarnings() const { return NumWarnings; }

    /// 消费者（用于 IDE 集成）
    void setConsumer(DiagnosticConsumer *C) { Consumer = C; }

private:
    SourceManager &SM;
    DiagnosticConsumer *Consumer = nullptr;
    unsigned NumErrors = 0;
    unsigned NumWarnings = 0;
};

// 诊断消息表（从 Python errors/ 迁移）
StringRef getDiagMessage(DiagID ID);

} // namespace diag
```

2. 创建 `lib/DiagnosticKinds.def`：
```
DIAG(err_expected_token, Error, "期望 '{0}'，但得到 '{1}'")
DIAG(err_unexpected_token, Error, "意外的标记 '{0}'")
DIAG(err_expected_expression, Error, "期望表达式")
DIAG(err_expected_type, Error, "期望类型名")
DIAG(err_expected_statement, Error, "期望语句")
DIAG(err_expected_identifier, Error, "期望标识符")
DIAG(err_missing_semicolon, Error, "缺少 ';'")
DIAG(err_undeclared_identifier, Error, "未声明的标识符 '{0}'")
DIAG(err_redefinition, Error, "标识符 '{0}' 重复定义")
DIAG(err_type_mismatch, Error, "类型不匹配：期望 '{0}'，实际 '{1}'")
DIAG(err_invalid_binary_op, Error, "运算符 '{0}' 不能用于类型 '{1}' 和 '{2}'")
// ... 更多诊断消息
```

**参考**: Python 版本 `src/zhc/errors/` 下的所有错误定义（约 100+ 条）

**工时**: 20h

---

#### T1.17 实现诊断引擎（含中文错误消息）

> **修订说明**: 专家报告建议 T1.18 中文错误消息合并入 T1.17，避免单独任务带来的上下文切换开销。

**交付物**: `lib/Diagnostics.cpp` + `lib/DiagnosticMessages.cpp`

**操作步骤**:
1. 实现诊断格式化（支持 `{0}` `{1}` 占位符）：
```cpp
DiagnosticBuilder DiagnosticsEngine::report(DiagID ID) {
    return DiagnosticBuilder(*this, ID);
}
```

2. 实现中文错误消息输出：
   - 从 Python 错误表迁移所有中文消息
   - 消息格式：`{文件名}:{行号}:{列号}: {级别}: {消息}`
   - 使用 `llvm::raw_ostream` 输出

3. 实现彩色输出（可选）：
   - 错误：`\033[31m` 红色
   - 警告：`\033[33m` 黄色
   - 信息：`\033[36m` 青色

4. 将 Python 版本的所有错误消息迁移到 C++：

```cpp
// lib/DiagnosticMessages.cpp
namespace diag {

const char *DiagnosticMessages[] = {
    // 词法错误
    [int(DiagID::err_invalid_character)]       = "非法字符 '{0}'",
    [int(DiagID::err_unterminated_string)]     = "未终止的字符串字面量",
    [int(DiagID::err_unterminated_comment)]   = "未终止的注释",
    [int(DiagID::err_invalid_escape)]          = "无效的转义序列 '\\{0}'",

    // 语法错误
    [int(DiagID::err_expected_token)]          = "期望 '{0}'，但得到 '{1}'",
    [int(DiagID::err_unexpected_token)]        = "意外的标记 '{0}'",
    [int(DiagID::err_missing_semicolon)]        = "缺少分号 ';'",
    [int(DiagID::err_unmatched_paren)]          = "括号不匹配",

    // 语义错误
    [int(DiagID::err_undeclared_identifier)]   = "未声明的标识符 '{0}'",
    [int(DiagID::err_redefinition)]              = "标识符 '{0}' 重复定义",
    [int(DiagID::err_type_mismatch)]            = "类型不匹配：期望 '{0}'，实际 '{1}'",
    [int(DiagID::err_invalid_assignment)]       = "不能将 '{0}' 赋值给 '{1}'",
    [int(DiagID::err_call_non_function)]        = "'{0}' 不可调用",
    [int(DiagID::err_not_an_array)]             = "'{0}' 不是数组类型",

    // 中文特有的友好提示
    [int(DiagID::err_chinese_hint)]            = "提示：中文关键字需使用中文标点",
    // ... 全部从 Python src/zhc/errors/ 迁移
};

} // namespace diag
```

5. **中文错误消息对照表**（从 Python 逐条迁移）：

| Python 错误 ID | 中文错误消息 | 优先级 |
|:---|:---|:---:|
| `INVALID_CHARACTER` | 非法字符 '{0}' | P0 |
| `UNTERMINATED_STRING` | 未终止的字符串字面量 | P0 |
| `UNTERMINATED_COMMENT` | 未终止的注释 | P0 |
| `EXPECTED_TOKEN` | 期望 '{0}'，但得到 '{1}' | P0 |
| `UNDECLARED_IDENTIFIER` | 未声明的标识符 '{0}' | P0 |
| `REDEFINITION` | 标识符 '{0}' 重复定义 | P0 |
| `TYPE_MISMATCH` | 类型不匹配：期望 '{0}'，实际 '{1}' | P0 |
| ... | ... | P1+ |

**参考**: Python 版本 `src/zhc/errors/` 下的所有错误定义（约 100+ 条）

**工时**: 80h（原 T1.17 60h + T1.18 20h，合并后统一管理）

---

### 任务 1.4.3 基础预处理器

#### T1.19 实现预处理器

**交付物**: `include/zhc/Preprocessor.h` + `lib/Preprocessor.cpp`

**操作步骤**:
1. 参考 Python 版本 `src/zhc/preprocessor.py` 实现：

```cpp
// include/zhc/Preprocessor.h
class Preprocessor {
public:
    Preprocessor(Lexer &L, DiagnosticsEngine &D, SourceManager &SM);

    /// 配置选项
    struct PPOptions {
        bool Macros = true;
        bool Ifdef = true;
        bool Include = true;
        bool Defined = true;
    };

    /// 主入口：返回下一个宏展开后的 Token
    Token peekToken(bool ReturnEOF = false);

    /// 宏定义/反定义
    void defineMacro(llvm::StringRef Name, llvm::StringRef Body);
    void undefMacro(llvm::StringRef Name);

    /// 条件编译
    bool evaluateCondition(llvm::StringRef Expr);
    bool isDefined(llvm::StringRef Name);

    /// 内置宏
    StringRef getBuiltinMacro(TokenKind K);

private:
    /// 宏展开
    void expandMacro(const Token &Name);
    bool readMacroArgument(const Token &Name);

    /// 条件编译状态
    struct ConditionInfo {
        bool InThen = true;
        bool InElse = false;
        bool FoundElse = false;
    };
    std::vector<ConditionInfo> CondStack;

    Lexer &TheLexer;
    DiagnosticsEngine &Diags;
    SourceManager &SM;
    std::unordered_map<StringRef, std::string> Macros;
};
```

2. 支持的预处理指令：
   - `#define` / `#undef`
   - `#ifdef` / `#ifndef` / `#if` / `#else` / `#elif` / `#endif`
   - `#include`（系统搜索路径 + 用户搜索路径）
   - `#pragma`
   - 内置宏：`__FILE__` `__LINE__` `__DATE__` `__TIME__`

**参考**: Python 版本 `src/zhc/preprocessor.py`

**工时**: 60h

---

### 任务 1.4.4 E0 安全特性启动

#### T1.20 实现未使用变量警告（S13）

**交付物**: Parser/Sema 中的未使用检测

**操作步骤**:
1. 在 `VarDecl` 节点中增加 `IsUsed` 标记
2. 在 Lexer 中默认开启未使用变量警告
3. 实现 `_` 和 `!` 忽略语法：
   - `整数型 _ = 计算();` — 下划线表示丢弃
   - `整数型 x = 计算() !;` — 感叹号显式忽略

```cpp
// 在 Parser 中处理忽略语法
if (Tok.is(KW_UNDERSCORE)) {
    // `整数型 _` = 丢弃值
    consumeToken();
    // ... 不创建 VarDecl
} else if (Tok.is(KK_BANG)) {
    // `... !` = 显式忽略
    VD->setExplicitlyUnused(true);
}
```

**参考**: Python 版本 `src/zhc/semantic/semantic_analyzer.py` 中的未使用检测

**工时**: 8h

---

#### T1.21 实现强制初始化检查框架（S02 启动）

**交付物**: `include/zhc/Sema.h` 中的初始化追踪结构

**操作步骤**:
1. 在 Sema 中建立局部变量的「已初始化」标记机制：
```cpp
// include/zhc/Sema.h
struct LocalVarInfo {
    QualType Type;
    bool IsInitialized = false;
    bool IsUsed = false;
    SourceLocation DeclLoc;
};

// 初始化追踪（在函数体分析中使用）
std::unordered_map<StringRef, LocalVarInfo> LocalVars;
void markInitialized(StringRef Name);
void markUsed(StringRef Name);
bool isInitialized(StringRef Name) const;
```

2. Phase 1 只做框架搭建，不做完整实现（完整实现在 Phase 2）

**参考**: Python 版本 `src/zhc/semantic/semantic_analyzer.py` 中的初始化检查逻辑

**工时**: 32h（Phase 1 框架）+ 后续阶段完善

---

## 1.5 Month 3 末：集成测试

### 任务 1.5.1 端到端集成测试

#### T1.22 前端集成测试

> **修订说明**: 专家报告建议将单一 40h 任务细化为 3 个子任务，每个子任务对应不同测试维度。

**交付物**: `test/integration/` 目录下的 3 组测试套件

**操作步骤**:

##### T1.22a 语法正确性测试（16h）

**交付物**: `test/integration/frontend_syntax_test.cpp`

测试 10 个 fixture 文件，验证 C++ Parser 输出与 Python Parser 输出完全一致：

| Fixture | 内容 | 验证点 |
|:---|:---|:---|
| `hello.zhc` | Hello World | 最小可运行程序 |
| `fibonacci.zhc` | 递归斐波那契 | 函数调用/递归 |
| `factorial.zhc` | 阶乘函数 | if/while |
| `control_flow.zhc` | if/while/for/switch | 控制流完整性 |
| `structs.zhc` | 结构体定义/使用 | 复合类型 |
| `enums.zhc` | 枚举定义/使用 | 枚举类型 |
| `arrays.zhc` | 数组定义/索引 | 数组下标 |
| `pointers.zhc` | 指针算术 | 指针操作 |
| `functions.zhc` | 函数重载/前向声明 | 函数声明 |
| `imports.zhc` | 多文件导入 | 模块系统 |

```cpp
TEST_F(FrontendSyntaxTest, Fibonacci) {
    auto Result = compile("fibonacci.zhc");
    EXPECT_EQ(Result.ErrorCount, 0u);
    // 对比 Python AST 节点数量和结构
    EXPECT_EQ(Result.ASTNodeCount, PythonParser.fibonacci_zhc.NodeCount);
}
```

##### T1.22b 错误恢复测试（8h）

**交付物**: `test/integration/frontend_error_recovery_test.cpp`

测试 5 个故意写错的 fixture，验证错误恢复机制：

| Fixture | 故意引入的错误 | 验证点 |
|:---|:---|:---|
| `error_missing_semicolon.zhc` | 缺少分号 | 继续解析后续代码 |
| `error_unmatched_paren.zhc` | 括号不匹配 | 报告错误位置后恢复 |
| `error_unknown_token.zhc` | 非法字符 | 跳过非法字符 |
| `error_incomplete_expr.zhc` | 不完整表达式 | 报告错误后继续 |
| `error_in_nested_block.zhc` | 嵌套块内错误 | 外层块不受影响 |

```cpp
TEST_F(FrontendErrorRecovery, MissingSemicolon) {
    auto Result = compile("error_missing_semicolon.zhc");
    // 应产生 1 个错误
    EXPECT_EQ(Result.ErrorCount, 1u);
    // 但后续代码应继续解析
    EXPECT_NE(Result.ASTAfterError, nullptr);
}
```

##### T1.22c 全中文关键字测试（8h）

**交付物**: `test/integration/frontend_chinese_test.cpp`

测试 5 个全中文 fixture，验证中文支持：

| Fixture | 内容 |
|:---|:---|
| `chinese_hello.zhc` | `函数 空型 主函数() { 打印("你好世界"); }` |
| `chinese_control.zhc` | `如果`/`循环`/`选择` 等中文关键字 |
| `chinese_types.zhc` | `整数型`/`浮点型`/`布尔型` 等中文类型 |
| `chinese_complex.zhc` | 混合中英文的程序 |
| `chinese_unicode.zhc` | 中文标识符 `变量 张三 = 42;` |

##### T1.22d 渐进式迁移工具（P1-4，8h）

> **来源**: 专家报告 P1-4
> **优先级**: P1
> **理由**: Python→C++ 迁移过程中需要工具辅助验证语义一致性

**交付物**: `tools/migrate_ast_test/` 目录下的辅助工具

**工具 1: AST 对比工具**
```bash
# 对比 Python 和 C++ 生成的 AST
./zhc_ast_diff python_output.json cpp_output.json
# 输出差异报告
```

**工具 2: Python 测试用例迁移器**
```bash
# 将 Python pytest fixture 转换为 C++ GTest fixture
./zhc_migrate_test tests/fixtures/*.zhc --output=test/integration/
```

**工具 3: 语义一致性检查器**
```bash
# 对同一 .zhc 文件运行 Python 和 C++ 编译器
./zhc_semantic_check hello.zhc
# 报告类型推导、作用域分析差异
```

```cpp
// tools/ast_diff/CMakeLists.txt
add_executable(zhc_ast_diff ast_diff.cpp)
target_link_libraries(zhc_ast_diff PRIVATE zhc_core)

add_executable(zhc_migrate_test migrate_test.cpp)
target_link_libraries(zhc_migrate_test PRIVATE zhc_core)
```

**验收标准**:
```bash
# 3 组集成测试
ctest -R FrontendSyntax --output-on-failure    # T1.22a
ctest -R FrontendErrorRecovery --output-on-failure  # T1.22b
ctest -R FrontendChinese --output-on-failure   # T1.22c

# 迁移工具可用
./build/tools/zhc_ast_diff --help
./build/tools/zhc_migrate_test --help
./build/tools/zhc_semantic_check --help

# 测试用例数 ≥ 200 个（满足 Go/No-Go 标准）
ctest -V | grep -c "TEST"
```

**工时**: 40h（原 T1.22 细化为 3 子任务）+ 8h（T1.22b 迁移工具）= **48h**

---

## 1.6 Phase 1 Go/No-Go 检查点

### 检查点：进入 Phase 2 的验收条件

| 检查项 | 验收命令 | 通过标准 |
|:---|:---|:---|
| **编译通过** | `ninja -C cpp/build` | 无编译错误 |
| **Lexer 测试** | `ctest -R Lexer` | 全部通过 |
| **Parser 测试** | `ctest -R Parser` | 全部通过 |
| **中文关键词** | `zhc parse test/fixtures/chinese_keywords.zhc` | AST 输出正确 |
| **错误消息** | `zhc parse test/fixtures/error.zhc` | 输出中文错误消息+正确行号 |
| **错误恢复** | 故意写错代码 | 不因单个错误崩溃，继续解析 |
| **E0 安全** | 未使用变量 `x` | 产生警告 |

**量化标准**：
- C++ Lexer/Parser 覆盖率 ≥ 90%（对比 Python 版本测试集）
- Parser 错误率 < 5%
- 测试用例数 ≥ 200 个

**如未通过**：
- 停 1 周集中修复 Bug
- Parser 错误率 > 5% 则不许进入 Phase 2

---

## 1.7 技术债务清理记录

| 债务 ID | 清理项 | 清理方式 |
|:---|:---|:---|
| **A-01** | Lexer 不支持 Unicode | UTF-8 全支持，SourceManager 统一管理 |
| **A-02** | Parser 错误恢复为零 | 实现同步点策略，跳过错误继续解析 |
| **B-01** | AST 继承层次混乱 | C++ 显式继承，清晰建模 |
| **B-02** | Token 位置信息丢失 | 所有 Token 携带 `llvm::SMLoc` |

---

## 1.8 参考资料

| 资料 | 路径 | 用途 |
|:---|:---|:---|
| Python Lexer | `src/zhc/parser/lexer.py` | 词法分析逻辑参考 |
| Python Keywords | `src/zhc/keywords.py` | 关键词表迁移 |
| Python AST | `src/zhc/parser/ast_nodes.py` | AST 节点设计参考 |
| Python Parser | `src/zhc/parser/parser.py` | 语法分析逻辑参考 |
| Python Errors | `src/zhc/errors/` | 中文错误消息迁移 |
| Python Preprocessor | `src/zhc/preprocessor.py` | 预处理逻辑参考 |
| Clang 源码 | LLVM 源码 `lib/Parse/` | Parser 架构参考 |
| LLVM SourceMgr | `include/llvm/SourceMgr.h` | 源码管理参考 |

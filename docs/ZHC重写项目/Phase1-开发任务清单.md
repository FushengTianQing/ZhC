# Phase 1：C++ 基础前端

**版本**: v1.0
**日期**: 2026-04-13
**基于文档**: `04-模块重写建议.md`、`12-项目规模与工时估算.md`、`15-重构任务执行清单.md`、`16-技术债务清单.md`
**目标**: 完成 C++ 基础前端所有模块，能够解析 .zhc 文件并输出 AST
**工时**: 960h（含 20% 风险缓冲）
**日历时间**: 约 5 个月
**前置条件**: Phase 0 完成（MVP 可视化追踪可用）

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

#### T1.4 实现 Token 定义

**交付物**: `include/zhc/Lexer.h` 中的 Token 相关类型

**操作步骤**:
1. 参考 Python 版本 `src/zhc/lexer.py` 中的 `TokenType` 枚举（~50 个 token 类型）
2. 实现 C++ 版本：

```cpp
// include/zhc/Lexer.h
namespace zhc {

// Token 类型
enum class TokenKind {
#define TOKEN(X) X,
#include "TokenKinds.def"
};

// TokenKind 定义（生成宏）
#define TOKEN(X) X,
#define PUNCTUATOR(X, Y) X,
#define KEYWORD(X) KW_##X,
#include "TokenKinds.def"

struct Token {
    TokenKind Kind = TokenKind::Unknown;
    llvm::SMLoc Location;          // 源码位置（含文件名/行/列）
    llvm::StringRef Spelling;      // Token 原文
    uint64_t IntegerValue = 0;    // 整数字面量值
    std::string StringValue;       // 字符串字面量值
};

// Token 辅助函数
StringRef getTokenName(TokenKind K);
bool isKeyword(TokenKind K);
bool isPunctuator(TokenKind K);
} // namespace zhc
```

3. 创建 `lib/TokenKinds.def`（参考 Clang 的 `TokenKinds.def` 格式）
4. 确保 Token 携带 `SourceLocation`（修复 B-02 债务的基础）

**参考**: Python 版本 `src/zhc/parser/lexer.py` 第 30-120 行

**工时**: 8h

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

## 1.3 Month 2：Parser + AST

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

#### T1.17 实现诊断引擎

**交付物**: `lib/Diagnostics.cpp`

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

**参考**: Python 版本 `src/zhc/errors/` 下的消息文件

**工时**: 60h（含中文错误消息迁移）

---

#### T1.18 中文错误消息表

**交付物**: `lib/DiagnosticMessages.cpp`

**操作步骤**:
1. 将 Python 版本的所有错误消息迁移到 C++：

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
    // ... 更多消息
};

} // namespace diag
```

**工时**: 20h（中文消息迁移）

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

**交付物**: `test/integration/frontend_integration_test.cpp`

**操作步骤**:
1. 创建端到端测试 fixture：
   - `hello.zhc`：经典 Hello World
   - `fibonacci.zhc`：递归斐波那契
   - `complex_expressions.zhc`：复杂表达式求值
   - `control_flow.zhc`：if/while/for/switch 完整测试
   - `chinese_programs.zhc`：全中文关键字程序

2. 测试流程：
```cpp
TEST_F(FrontendIntegration, HelloWorld) {
    // 1. 词法分析
    Lexer L(SourceMgr, Diags);
    std::vector<Token> Tokens;
    while (L.peekToken().isNot(KK_EOF)) {
        Tokens.push_back(L.nextToken());
    }
    EXPECT_GT(Tokens.size(), 0);

    // 2. 语法分析
    Parser P(Tokens, Diags);
    TranslationUnit *TU = P.parseTranslationUnit();
    EXPECT_NE(TU, nullptr);
    EXPECT_EQ(Diags.getNumErrors(), 0u);

    // 3. AST 打印（验证结构正确）
    ASTPrinter Printer;
    TU->accept(Printer);
}
```

**验收标准**:
```bash
ctest -R Frontend --output-on-failure
# 全部通过
```

**工时**: 40h

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

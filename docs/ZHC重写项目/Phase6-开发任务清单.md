# Phase 6：多语言前端（C + Python）— 开发任务清单

**版本**: v2.0  
**所属阶段**: Phase 6（1.5 个月 / 192h 含缓冲）  
**前置阶段**: Phase 2 完成（编译能力可用）即可启动；Phase 5（安全执行框架）为可选增强
**文档目的**: 直接指导程序员进行开发，包含操作步骤、代码示例、验收标准  
**基于文档**: `14-多语言前端扩展.md`、`12-项目规模与工时估算.md`、`15-重构任务执行清单.md`

---

## 📋 v2.0 修订说明

本版本修订基于[Phase1-5专家优化分析报告.md](./Phase1-5专家优化分析报告.md)的分析，更新以下内容：

| # | 修订内容 |
|:---:|:---|
| 依赖调整 | Phase 5 已重新定位为"安全执行框架"，独立于 Phase 4，Phase 6 可在 Phase 2 完成后启动 |
| 工时调整 | 总工时保持 224h（无缓冲）/ 192h（Phase 6 预算不含 E2）/ 280h（含 E2 模块系统） |

---

## 6.0 阶段概述

### 目标

在 Phase 2 完成的基础编译器上，新增 **C 前端** 和 **Python 前端**，实现 `.zhc` + `.c` + `.py` 三种语言共享语义分析 + IR 优化 + LLVM 后端的统一编译流水线。

> **前置依赖说明**：Phase 6 可在 Phase 2 完成后启动。Phase 5（安全执行框架）为可选增强，如需对多语言代码进行安全检查，可在 Phase 5 完成后集成。

### 核心价值

| 前端 | 战略价值 |
|:---|:---|
| **C 前端** | 复用 LLVM 200+ 优化 Pass；统一多语言工具链；为 Python 前端铺路 |
| **Python 前端** | 编译 Python 为机器码（10~100x 加速）；零依赖二进制部署；代码保护 |

### 核心模块

| 模块 | 文件 | 工时 | 说明 |
|:---|:---|:---:|:---|
| 语言检测器 | `zhc_language_detector.cpp/h` | 8h | 根据文件扩展名/内容自动识别语言 |
| C Lexer | `zhc_c_lexer.cpp/h` | 4h | C 语言词法分析 |
| C Parser | `zhc_c_parser.cpp/h` | 12h | C 语言语法分析 |
| C→ZHC AST 桥接 | `zhc_c_ast_bridge.cpp/h` | 16h | C AST 转换为 ZHC 通用 AST |
| C 前端测试 | `test/c_frontend_test.cpp` | 8h | C 前端单元+集成测试 |
| Python 类型映射 | `zhc_python_type_mapping.cpp/h` | 8h | Python→ZHC 类型转换 |
| Python 内置函数映射 | `zhc_python_builtins.cpp/h` | 16h | Python 内置函数→C/ZHC 函数 |
| Python Parser | `zhc_python_parser.cpp/h` | 40h | Python 语法分析（核心） |
| Python stdlib C 实现 | `zhc_python_stdlib.c/h` | 24h | PyObject/PyList/PyDict/PyString 运行时 |
| Python 前端测试 | `test/python_frontend_test.cpp` | 16h | Python 前端测试 |
| 多语言统一测试 | `test/multilang_test.cpp` | 16h | 三语言混合编译测试 |
| E2 模块系统 | `zhc_module.cpp/h` | 56h | `模块` 关键字+可见性控制 |

**总工时**: 224h（无缓冲）/ 192h（Phase 6 预算不含 E2）/ 280h（含 E2 模块系统）

> **说明**: E2 模块系统（S12, 56h）按 `15-重构任务执行清单.md` 归入 Phase 6，但可与多语言前端并行开发。模块系统是 Python `import` 的基础，建议优先完成。

---

## T6.1：语言检测器

**工时**: 8h  
**依赖**: 无  
**交付物**: `include/zhc/Frontend/LanguageDetector.h` + `lib/Frontend/LanguageDetector.cpp`

### 1.1 头文件设计

```cpp
// include/zhc/Frontend/LanguageDetector.h
#pragma once

#include "llvm/ADT/StringRef.h"
#include "llvm/ADT/StringMap.h"

namespace zhc {
namespace frontend {

/// 支持的源语言
enum class SourceLanguage {
    ZHC,      // .zhc 中文C
    C,        // .c / .h 标准C
    CPP,      // .cpp / .hpp C++（预留，v2.0）
    Python,   // .py Python
    Unknown   // 无法识别
};

/// 语言检测结果
struct DetectionResult {
    SourceLanguage Language = SourceLanguage::Unknown;
    std::string Dialect;      // "c11", "c17", "python3"
    std::string ErrorMessage; // 检测失败原因
};

/// 语言检测器：根据文件扩展名和内容确定源语言
class LanguageDetector {
public:
    /// 根据文件扩展名检测
    static DetectionResult detectByExtension(llvm::StringRef FilePath);

    /// 根据文件内容检测（shebang、编码标记等）
    static DetectionResult detectByContent(llvm::StringRef Content);

    /// 综合检测（先扩展名，后内容）
    static DetectionResult detect(llvm::StringRef FilePath,
                                  llvm::StringRef Content = "");

    /// 获取语言的默认方言
    static llvm::StringRef getDefaultDialect(SourceLanguage Lang);

    /// 语言名称字符串
    static llvm::StringRef getLanguageName(SourceLanguage Lang);

private:
    /// 扩展名→语言映射表
    static const llvm::StringMap<SourceLanguage> ExtensionMap;
};

} // namespace frontend
} // namespace zhc
```

### 1.2 实现要点

```cpp
// lib/Frontend/LanguageDetector.cpp

const llvm::StringMap<SourceLanguage> LanguageDetector::ExtensionMap = {
    {".zhc",  SourceLanguage::ZHC},
    {".c",    SourceLanguage::C},
    {".h",    SourceLanguage::C},
    {".py",   SourceLanguage::Python},
    // 预留
    {".cpp",  SourceLanguage::CPP},
    {".hpp",  SourceLanguage::CPP},
    {".cc",   SourceLanguage::CPP},
};

DetectionResult LanguageDetector::detectByExtension(llvm::StringRef Path) {
    // 提取扩展名（支持 .zhc 这类非标准扩展）
    auto DotPos = Path.rfind('.');
    if (DotPos == llvm::StringRef::npos)
        return {SourceLanguage::Unknown, "", "无文件扩展名"};

    llvm::StringRef Ext = Path.substr(DotPos);
    auto It = ExtensionMap.find(Ext.lower());
    if (It != ExtensionMap.end())
        return {It->second, getDefaultDialect(It->second), ""};

    return {SourceLanguage::Unknown, "", "未知的文件扩展名: " + Ext.str()};
}

DetectionResult LanguageDetector::detectByContent(llvm::StringRef Content) {
    // 检查 shebang: #!/usr/bin/env python3
    if (Content.startswith("#!/usr/bin/env python"))
        return {SourceLanguage::Python, "python3", ""};
    if (Content.startswith("#!/usr/bin/python"))
        return {SourceLanguage::Python, "python3", ""};

    // 检查中文关键词密度（区分 ZHC 和 C）
    int ChineseKeywordCount = 0;
    for (auto &KW : {"函数", "变量", "如果", "否则", "循环", "返回", "整数型", "浮点型"})
        if (Content.contains(KW)) ChineseKeywordCount++;
    if (ChineseKeywordCount >= 3)
        return {SourceLanguage::ZHC, "zhc1", ""};

    return {SourceLanguage::Unknown, "", "无法从内容确定语言"};
}
```

### 1.3 验收标准

```bash
ctest -R LanguageDetector --output-on-failure
# 测试用例：
# - hello.zhc → ZHC
# - utils.c → C
# - hello.py → Python
# - noext → Unknown
# - shebang检测 python3
# - 中文关键词密度检测
```

---

## T6.2：C Lexer（词法分析器）

**工时**: 4h  
**依赖**: T6.1  
**交付物**: `include/zhc/Frontend/CLexer.h` + `lib/Frontend/CLexer.cpp`

### 2.1 头文件设计

```cpp
// include/zhc/Frontend/CLexer.h
#pragma once

#include "zhc/Lexer.h"  // 复用 ZHC 的 Token 基础结构
#include "llvm/ADT/StringMap.h"

namespace zhc {
namespace frontend {

/// C 语言 Token 额外类型
enum class CTokenKind {
    // C 特有关键词
    KW_AUTO, KW_BREAK, KW_CASE, KW_CHAR, KW_CONST, KW_CONTINUE,
    KW_DEFAULT, KW_DO, KW_DOUBLE, KW_ELSE, KW_ENUM, KW_EXTERN,
    KW_FLOAT, KW_FOR, KW_GOTO, KW_IF, KW_INLINE, KW_INT,
    KW_LONG, KW_REGISTER, KW_RESTRICT, KW_RETURN, KW_SHORT,
    KW_SIGNED, KW_SIZEOF, KW_STATIC, KW_STRUCT, KW_SWITCH,
    KW_TYPEDEF, KW_UNION, KW_UNSIGNED, KW_VOID, KW_VOLATILE,
    KW_WHILE,
    // C99
    KW__BOOL, KW__COMPLEX, KW__IMAGINARY,
    // C11
    KW__THREAD_LOCAL, KW__ALIGNAS, KW__ALIGNOF, KW__ATOMIC,
    KW__STATIC_ASSERT, KW__NORETURN,
    // C 预处理器指令（整行作为 Token）
    PP_INCLUDE, PP_DEFINE, PP_UNDEF, PP_IFDEF, PP_IFNDEF,
    PP_IF, PP_ELIF, PP_ELSE, PP_ENDIF, PP_PRAGMA,
};

/// C Lexer：将 C 源码词法分析为 Token 流
class CLexer {
public:
    CLexer(const llvm::SourceMgr &SrcMgr, DiagnosticsEngine &Diags);

    /// 词法分析主入口
    Token nextToken();

    /// 向前看
    Token lookAhead(unsigned N = 1);

private:
    const char *BufferStart = nullptr;
    const char *BufferEnd = nullptr;
    const char *CurPtr = nullptr;
    DiagnosticsEngine &Diags;

    Token lexIdentifier();
    Token lexNumber();
    Token lexString();
    Token lexCharLiteral();
    Token lexPreprocessorDirective();  // #include, #define 等
    Token lexComment();

    /// C 关键词查找
    static const llvm::StringMap<CTokenKind> CKeywords;
};

} // namespace frontend
} // namespace zhc
```

### 2.2 C 关键词表

```cpp
// lib/Frontend/CLexer.cpp

const llvm::StringMap<CTokenKind> CLexer::CKeywords = {
    // C11/C17 标准关键词
    {"auto", CTokenKind::KW_AUTO}, {"break", CTokenKind::KW_BREAK},
    {"case", CTokenKind::KW_CASE}, {"char", CTokenKind::KW_CHAR},
    {"const", CTokenKind::KW_CONST}, {"continue", CTokenKind::KW_CONTINUE},
    {"default", CTokenKind::KW_DEFAULT}, {"do", CTokenKind::KW_DO},
    {"double", CTokenKind::KW_DOUBLE}, {"else", CTokenKind::KW_ELSE},
    {"enum", CTokenKind::KW_ENUM}, {"extern", CTokenKind::KW_EXTERN},
    {"float", CTokenKind::KW_FLOAT}, {"for", CTokenKind::KW_FOR},
    {"goto", CTokenKind::KW_GOTO}, {"if", CTokenKind::KW_IF},
    {"inline", CTokenKind::KW_INLINE}, {"int", CTokenKind::KW_INT},
    {"long", CTokenKind::KW_LONG}, {"register", CTokenKind::KW_REGISTER},
    {"restrict", CTokenKind::KW_RESTRICT}, {"return", CTokenKind::KW_RETURN},
    {"short", CTokenKind::KW_SHORT}, {"signed", CTokenKind::KW_SIGNED},
    {"sizeof", CTokenKind::KW_SIZEOF}, {"static", CTokenKind::KW_STATIC},
    {"struct", CTokenKind::KW_STRUCT}, {"switch", CTokenKind::KW_SWITCH},
    {"typedef", CTokenKind::KW_TYPEDEF}, {"union", CTokenKind::KW_UNION},
    {"unsigned", CTokenKind::KW_UNSIGNED}, {"void", CTokenKind::KW_VOID},
    {"volatile", CTokenKind::KW_VOLATILE}, {"while", CTokenKind::KW_WHILE},
    // C99
    {"_Bool", CTokenKind::KW__BOOL},
    {"_Complex", CTokenKind::KW__COMPLEX},
    // C11
    {"_Thread_local", CTokenKind::KW__THREAD_LOCAL},
    {"_Alignas", CTokenKind::KW__ALIGNAS},
    {"_Alignof", CTokenKind::KW__ALIGNOF},
    {"_Atomic", CTokenKind::KW__ATOMIC},
    {"_Static_assert", CTokenKind::KW__STATIC_ASSERT},
    {"_Noreturn", CTokenKind::KW__NORETURN},
};
```

### 2.3 实现要点

- **复用 ZHC Lexer 的基础设施**：Token 结构、SourceLocation、DiagnosticsEngine
- **C 特有处理**：预处理器指令（`#include`/`#define`）、`sizeof` 运算符、字符字面量 `'a'`
- **不支持**：C 预处理器在 C 前端中直接透传给 Phase 1 的 `Preprocessor` 处理

### 2.4 验收标准

```bash
ctest -R CLexer --output-on-failure
# 测试用例：
# - C 关键词识别（int, void, struct, typedef）
# - 数字字面量（42, 3.14, 0xFF, 0b1010, 123LL, 3.14f）
# - 字符串/字符字面量
# - 预处理器指令（#include, #define）
# - sizeof 运算符
```

---

## T6.3：C Parser（语法分析器）

**工时**: 12h  
**依赖**: T6.2  
**交付物**: `include/zhc/Frontend/CParser.h` + `lib/Frontend/CParser.cpp`

### 3.1 头文件设计

```cpp
// include/zhc/Frontend/CParser.h
#pragma once

#include "zhc/AST.h"
#include "zhc/Frontend/CLexer.h"

namespace zhc {
namespace frontend {

/// C Parser：将 C Token 流解析为 C AST
///
/// 设计原则：
/// - 输出 C 特有的中间 AST（CASTR）
/// - 后续由 CAstBridge 转换为 ZHC 通用 AST
/// - 不直接复用 ZHC Parser（语法差异太大）
class CParser {
public:
    CParser(CLexer &Lexer, DiagnosticsEngine &Diags);

    /// 解析翻译单元
    TranslationUnit *parseTranslationUnit();

private:
    CLexer &Lex;
    DiagnosticsEngine &Diags;
    Token CurTok;

    void consumeToken();
    bool expect(TokenKind K);

    // 声明解析
    Decl *parseDeclaration();
    FunctionDecl *parseFunctionDefinition();
    VarDecl *parseGlobalVariable();
    StructDecl *parseStructDeclaration();
    EnumDecl *parseEnumDeclaration();
    TypedefDecl *parseTypedefDeclaration();

    // 语句解析
    Stmt *parseStatement();
    Stmt *parseIfStatement();
    Stmt *parseWhileStatement();
    Stmt *parseForStatement();
    Stmt *parseSwitchStatement();
    Stmt *parseReturnStatement();
    Stmt *parseDoWhileStatement();

    // 表达式解析（递归下降）
    Expr *parseExpression();
    Expr *parseAssignmentExpr();
    Expr *parseBinaryExpr(unsigned MinPrec);
    Expr *parseUnaryExpr();
    Expr *parsePostfixExpr();
    Expr *parsePrimaryExpr();

    // 类型解析
    Type *parseType();
    Type *parsePointerType(Type *Base);
    Type *parseArrayType(Type *Base);
    Type *parseFunctionType(Type *Ret);

    // C 特有
    Expr *parseSizeofExpr();
    Expr *parseCastExpr();
    Decl *parseForwardDeclaration();
};

} // namespace frontend
} // namespace zhc
```

### 3.2 实现要点

```cpp
// lib/Frontend/CParser.cpp

TranslationUnit *CParser::parseTranslationUnit() {
    std::vector<Decl *> Decls;
    while (CurTok.isNot(TokenKind::EOF)) {
        if (CurTok.is(CTokenKind::PP_INCLUDE)) {
            // 预处理器指令 → ImportDecl
            Decls.push_back(parseIncludeDirective());
        } else if (CurTok.isOneOf(CTokenKind::KW_STRUCT,
                                   CTokenKind::KW_UNION,
                                   CTokenKind::KW_ENUM,
                                   CTokenKind::KW_TYPEDEF)) {
            Decls.push_back(parseDeclaration());
        } else {
            // 函数定义或全局变量
            Decls.push_back(parseTopLevelDeclaration());
        }
    }
    return new (Context) TranslationUnit(Decls);
}

// sizeof 表达式：C 特有
Expr *CParser::parseSizeofExpr() {
    consumeToken(); // sizeof
    expect(TokenKind::LParen);
    if (isTypeStart()) {
        Type *Ty = parseType();
        expect(TokenKind::RParen);
        return new (Context) SizeofExpr(Ty);
    } else {
        Expr *E = parseExpression();
        expect(TokenKind::RParen);
        return new (Context) SizeofExpr(E);
    }
}
```

### 3.3 C 与 ZHC 语法差异对照

| C 语法 | ZHC 语法 | 桥接处理 |
|:---|:---|:---|
| `int x = 5;` | `整数型 x = 5;` | 类型映射 |
| `void foo(int a)` | `函数 空型 foo(整数型 a)` | 关键词映射 |
| `if (cond) {}` | `如果 (cond) {}` | 关键词映射 |
| `while (cond) {}` | `循环 当 (cond) {}` | 关键词映射 |
| `for (init;cond;inc) {}` | `循环 (init;cond;inc) {}` | 关键词映射 |
| `switch/case/default` | `选择/当/默认` | 关键词映射 |
| `struct Point { ... };` | `结构体 Point { ... };` | 关键词映射 |
| `sizeof(x)` | ZHC 无直接等价 | 桥接时转为 `类型大小(x)` |
| `typedef int BOOL;` | ZHC 无 typedef | 桥接时创建类型别名 |
| `#include <stdio.h>` | `导入 "stdio.zhc"` | 路径重映射 |

### 3.4 验收标准

```bash
ctest -R CParser --output-on-failure
# 测试用例：
# - hello.c → AST 正确
# - fibonacci.c → 递归函数解析
# - struct_point.c → 结构体解析
# - typedef.c → 类型别名解析
# - sizeof.c → sizeof 表达式解析
# - forward_decl.c → 前向声明解析
```

---

## T6.4：C→ZHC AST 桥接器

**工时**: 16h  
**依赖**: T6.3  
**交付物**: `include/zhc/Frontend/CAstBridge.h` + `lib/Frontend/CAstBridge.cpp`

### 4.1 头文件设计

```cpp
// include/zhc/Frontend/CAstBridge.h
#pragma once

#include "zhc/AST.h"

namespace zhc {
namespace frontend {

/// C 类型名 → ZHC 类型名映射
static const llvm::StringMap<llvm::StringRef> CTypeToZHC = {
    {"int",       "整数型"},
    {"char",      "字符型"},
    {"float",     "浮点型"},
    {"double",    "双精度浮点型"},
    {"void",      "空型"},
    {"long",      "长整数型"},
    {"short",     "短整数型"},
    {"signed",    "有符号整数型"},
    {"unsigned",  "无符号整数型"},
    {"_Bool",     "逻辑型"},
    // stdint.h 类型
    {"int8_t",    "整数型"},
    {"int16_t",   "整数型"},
    {"int32_t",   "长整数型"},
    {"int64_t",   "长长整数型"},
    {"uint8_t",   "无符号整数型"},
    {"size_t",    "无符号长整数型"},
    {"FILE",      "文件型"},
};

/// C AST → ZHC 通用 AST 桥接器
///
/// 设计原则：
/// - 输入：CParser 生成的 C AST
/// - 输出：与 ZHC Parser 输出完全一致的 AST 节点
/// - 后续流水线（语义分析、IR 生成、后端）完全无感知
class CAstBridge {
public:
    CAstBridge(DiagnosticsEngine &Diags) : Diags(Diags) {}

    /// 执行 C AST → ZHC AST 转换
    TranslationUnit *transform(TranslationUnit *C_AST);

private:
    DiagnosticsEngine &Diags;

    // 声明转换
    FunctionDecl *transformFunction(FunctionDecl *CFunc);
    VarDecl *transformGlobalVariable(VarDecl *CVar);
    StructDecl *transformStruct(StructDecl *CStruct);
    EnumDecl *transformEnum(EnumDecl *CEnum);
    TypedefDecl *transformTypedef(TypedefDecl *CTypedef);
    ImportDecl *transformInclude(ImportDecl *CInclude);

    // 语句转换
    Stmt *transformStatement(Stmt *CStmt);
    Stmt *transformIfStmt(IfStmt *CIf);
    Stmt *transformWhileStmt(WhileStmt *CWhile);
    Stmt *transformForStmt(ForStmt *CFor);
    Stmt *transformSwitchStmt(SwitchStmt *CSwitch);
    Stmt *transformDoWhileStmt(Stmt *CDoWhile); // C特有→转换为while+if

    // 表达式转换
    Expr *transformExpression(Expr *CExpr);
    Expr *transformSizeofExpr(SizeofExpr *CSizeof); // → ZHC 内置调用

    // 类型转换
    QualType transformType(QualType CType);
};

} // namespace frontend
} // namespace zhc
```

### 4.2 核心转换实现

```cpp
// lib/Frontend/CAstBridge.cpp

TranslationUnit *CAstBridge::transform(TranslationUnit *C_TU) {
    std::vector<Decl *> ZHCDecls;

    for (Decl *D : C_TU->getDecls()) {
        if (auto *FD = dyn_cast<FunctionDecl>(D))
            ZHCDecls.push_back(transformFunction(FD));
        else if (auto *VD = dyn_cast<VarDecl>(D))
            ZHCDecls.push_back(transformGlobalVariable(VD));
        else if (auto *SD = dyn_cast<StructDecl>(D))
            ZHCDecls.push_back(transformStruct(SD));
        else if (auto *ED = dyn_cast<EnumDecl>(D))
            ZHCDecls.push_back(transformEnum(ED));
        else if (auto *TD = dyn_cast<TypedefDecl>(D))
            ZHCDecls.push_back(transformTypedef(TD));
        else if (auto *ID = dyn_cast<ImportDecl>(D))
            ZHCDecls.push_back(transformInclude(ID));
    }

    return new (Context) TranslationUnit(ZHCDecls);
}

FunctionDecl *CAstBridge::transformFunction(FunctionDecl *CFunc) {
    // 返回类型转换
    QualType RetTy = transformType(CFunc->getReturnType());

    // 参数转换
    std::vector<ParamDecl *> Params;
    for (auto *P : CFunc->getParams())
        Params.push_back(transformParam(P));

    // 函数体转换（递归）
    Stmt *Body = nullptr;
    if (CFunc->getBody())
        Body = transformStatement(CFunc->getBody());

    // 创建 ZHC FunctionDecl（与 ZHC Parser 输出完全一致）
    return new (Context) FunctionDecl(
        CFunc->getName(), RetTy, Params, Body);
}

QualType CAstBridge::transformType(QualType CType) {
    // 指针类型：int* → 整数型*
    if (auto *PT = dyn_cast<PointerType>(CType.getType())) {
        QualType Inner = transformType(PT->getPointeeType());
        return QualType(new (Context) PointerType(Inner));
    }
    // 数组类型：int[10] → 整数型[10]
    if (auto *AT = dyn_cast<ArrayType>(CType.getType())) {
        QualType Elem = transformType(AT->getElementType());
        return QualType(new (Context) ArrayType(Elem, AT->getSize()));
    }
    // 基础类型映射
    if (auto *BT = dyn_cast<BuiltinType>(CType.getType())) {
        llvm::StringRef ZHCName = CTypeToZHC.lookup(BT->getName());
        if (!ZHCName.empty())
            return getBuiltinType(ZHCName);
        // 未映射类型保留原名
        Diags.report(diag::warn_unmapped_c_type, BT->getName());
        return CType;
    }
    return CType;
}

Stmt *CAstBridge::transformDoWhileStmt(Stmt *CDoWhile) {
    // C 的 do-while 在 ZHC 中没有直接等价
    // 转换策略：do { body } while(cond) → { body; while(cond) { body } }
    // 这是一种保守但正确的转换
    auto *Body = /* 提取 body */;
    auto *Cond = /* 提取 cond */;
    return new (Context) CompoundStmt({
        Body,
        new (Context) WhileStmt(Cond, Body)
    });
}
```

### 4.3 #include 路径重映射

```cpp
ImportDecl *CAstBridge::transformInclude(ImportDecl *CInclude) {
    llvm::StringRef Path = CInclude->getPath();

    // 标准 C 头文件 → ZHC 等价模块
    static const llvm::StringMap<llvm::StringRef> CHeaderToZHC = {
        {"stdio.h",   "标准输入输出"},
        {"stdlib.h",  "标准库"},
        {"string.h",  "字符串"},
        {"math.h",    "数学"},
        {"time.h",    "时间"},
        {"ctype.h",   "字符处理"},
        {"assert.h",  "断言"},
        {"stdbool.h", "布尔型"},
        {"stdint.h",  "整数类型"},
    };

    llvm::StringRef ZHCModule = CHeaderToZHC.lookup(Path);
    if (!ZHCModule.empty())
        return new (Context) ImportDecl(ZHCModule);

    // 用户头文件：保留原路径但改扩展名
    if (Path.endswith(".h")) {
        std::string ZHCPath = Path.substr(0, Path.size() - 2).str() + ".zhc";
        return new (Context) ImportDecl(ZHCPath);
    }

    return CInclude;
}
```

### 4.4 验收标准

```bash
ctest -R CAstBridge --output-on-failure
# 测试用例：
# - int foo(int a) → 整数型 foo(整数型 a)
# - char* → 字符型*
# - int[10] → 整数型[10]
# - struct Point → 结构体 Point
# - #include <stdio.h> → 导入 "标准输入输出"
# - do-while → while 转换
# - sizeof(int) → 内置调用
```

---

## T6.5：C 前端集成测试

**工时**: 8h  
**依赖**: T6.2, T6.3, T6.4  
**交付物**: `test/integration/c_frontend_test.cpp`

### 5.1 测试用例设计

```cpp
// test/integration/c_frontend_test.cpp

class CFrontendTest : public ::testing::Test {
protected:
    void compileAndRun(llvm::StringRef Source, llvm::StringRef ExpectedOutput) {
        // 1. 语言检测
        auto Lang = LanguageDetector::detectByExtension("test.c");
        ASSERT_EQ(Lang.Language, SourceLanguage::C);

        // 2. C Lexer
        CLexer CLex(SrcMgr, Diags);
        std::vector<Token> Tokens;
        while (CLex.peekToken().isNot(TokenKind::EOF))
            Tokens.push_back(CLex.nextToken());

        // 3. C Parser
        CParser CP(CLex, Diags);
        TranslationUnit *C_AST = CP.parseTranslationUnit();
        ASSERT_NE(C_AST, nullptr);

        // 4. C→ZHC AST 桥接
        CAstBridge Bridge(Diags);
        TranslationUnit *ZHC_AST = Bridge.transform(C_AST);
        ASSERT_NE(ZHC_AST, nullptr);

        // 5. 共用语义分析 + IR 生成 + 后端
        Sema.Analyze(ZHC_AST);
        auto Mod = CG.codegen(ZHC_AST);
        ASSERT_TRUE(verifyModule(*Mod));

        // 6. 链接运行
        auto Output = linkAndRun(*Mod);
        EXPECT_EQ(Output, ExpectedOutput);
    }
};

TEST_F(CFrontendTest, HelloWorld) {
    compileAndRun(
        "#include <stdio.h>\n"
        "int main() { printf(\"Hello, World!\\n\"); return 0; }",
        "Hello, World!\n");
}

TEST_F(CFrontendTest, Fibonacci) {
    compileAndRun(
        "int fib(int n) {"
        "  if (n <= 1) return n;"
        "  return fib(n-1) + fib(n-2);"
        "}"
        "int main() { printf(\"%d\", fib(10)); return 0; }",
        "55");
}

TEST_F(CFrontendTest, StructUsage) {
    compileAndRun(
        "struct Point { int x; int y; };"
        "int main() {"
        "  struct Point p = {3, 4};"
        "  return p.x + p.y;"
        "}",
        "7");
}
```

### 5.2 测试 fixture 文件

| 文件 | 内容 |
|:---|:---|
| `test/fixtures/c/hello.c` | Hello World |
| `test/fixtures/c/fibonacci.c` | 递归斐波那契 |
| `test/fixtures/c/struct.c` | 结构体使用 |
| `test/fixtures/c/typedef.c` | typedef 使用 |
| `test/fixtures/c/pointer.c` | 指针操作 |
| `test/fixtures/c/array.c` | 数组操作 |

### 5.3 验收标准

```bash
ctest -R CFrontend --output-on-failure
# 全部通过
```

---

## T6.6：Python 类型映射

**工时**: 8h  
**依赖**: 无  
**交付物**: `include/zhc/Frontend/PythonTypeMapping.h` + `lib/Frontend/PythonTypeMapping.cpp`

### 6.1 头文件设计

```cpp
// include/zhc/Frontend/PythonTypeMapping.h
#pragma once

#include "zhc/Types.h"
#include "llvm/ADT/StringMap.h"

namespace zhc {
namespace frontend {

/// Python 类型 → ZHC 类型映射表
static const llvm::StringMap<llvm::StringRef> PythonTypeToZHC = {
    // 基础类型（可静态映射）
    {"int",    "长整数型"},        // Python int → C long long (64位)
    {"float",  "双精度浮点型"},    // Python float → C double
    {"bool",   "逻辑型"},          // Python bool → C _Bool
    {"None",   "空型"},            // Python None → C void*

    // 字符串（UTF-8 指针）
    {"str",    "PyString*"},       // → 自定义结构体

    // 复合类型（需要运行时实现）
    {"list",   "PyList*"},         // → 自定义结构体
    {"tuple",  "PyTuple*"},        // → 自定义结构体
    {"dict",   "PyDict*"},         // → 自定义结构体
    {"set",    "PySet*"},          // → 自定义结构体

    // 特殊类型
    {"object", "PyObject*"},       // 一切皆对象
    {"bytes",  "字符型*"},         // Python bytes → C char*
    {"type",   "PyType*"},         // 类型对象
};

/// Python 动态特性处理策略
enum class DynamicStrategy {
    StaticInfer,        // 尽力静态推导
    RuntimeCheck,       // 运行时类型检查兜底
    VTable,             // 函数指针表模拟多态
    HashTable,          // __dict__ 哈希表模拟动态属性
    RestrictedEval,     // 受限 eval/exec
};

/// 动态特性策略映射
static const llvm::StringMap<DynamicStrategy> DynamicFeatureStrategies = {
    {"变量类型动态",  DynamicStrategy::StaticInfer},
    {"多态/鸭子类型", DynamicStrategy::VTable},
    {"属性动态添加",  DynamicStrategy::HashTable},
    {"eval/exec",     DynamicStrategy::RestrictedEval},
};

/// Python 类型映射器
class PythonTypeMapper {
public:
    PythonTypeMapper(TypeContext &Ctx) : Context(Ctx) {}

    /// 映射 Python 类型到 ZHC QualType
    QualType mapType(llvm::StringRef PythonType);

    /// 推导 Python 表达式的 ZHC 类型
    QualType inferExprType(llvm::StringRef Expr);

    /// 检查是否为可直接映射的基础类型
    bool isDirectlyMappable(llvm::StringRef PythonType);

private:
    TypeContext &Context;
};

} // namespace frontend
} // namespace zhc
```

### 6.2 实现要点

```cpp
// lib/Frontend/PythonTypeMapping.cpp

QualType PythonTypeMapper::mapType(llvm::StringRef PyType) {
    // 基础类型直接映射
    llvm::StringRef ZHCName = PythonTypeToZHC.lookup(PyType);
    if (!ZHCName.empty() && !ZHCName.contains("*")) {
        return Context.getBuiltinType(ZHCName);
    }

    // PyObject 派生类型（PyString*, PyList*, ...）
    if (ZHCName.endswith("*")) {
        // 返回指向自定义结构体的指针类型
        llvm::StringRef StructName = ZHCName.substr(0, ZHCName.size() - 1);
        return Context.getPointerType(Context.getStructType(StructName));
    }

    // 未知类型 → PyObject*（通用对象指针）
    return Context.getPointerType(Context.getStructType("PyObject"));
}

bool PythonTypeMapper::isDirectlyMappable(llvm::StringRef PyType) {
    // int, float, bool 可以直接映射为 C 类型
    return PyType == "int" || PyType == "float" || PyType == "bool";
}
```

### 6.3 验收标准

```bash
ctest -R PythonTypeMapping --output-on-failure
# 测试用例：
# - int → 长整数型
# - float → 双精度浮点型
# - str → PyString*
# - list → PyList*
# - unknown → PyObject*
```

---

## T6.7：Python 内置函数映射

**工时**: 16h  
**依赖**: T6.6  
**交付物**: `include/zhc/Frontend/PythonBuiltins.h` + `lib/Frontend/PythonBuiltins.cpp`

### 7.1 头文件设计

```cpp
// include/zhc/Frontend/PythonBuiltins.h
#pragma once

#include "llvm/ADT/StringMap.h"

namespace zhc {
namespace frontend {

/// Python 内置函数 → ZHC/C 函数映射
struct BuiltinMapping {
    llvm::StringRef PythonName;    // Python 函数名
    llvm::StringRef ZHCName;       // ZHC 等价函数名
    llvm::StringRef CType;         // C 实现函数签名
    bool NeedsRuntime;             // 是否需要 C 运行时实现
};

/// 直接映射（ZHC 有等价实现）
static const BuiltinMapping DirectMappings[] = {
    {"print",  "打印",     "zhc_print",     false},
    {"abs",    "绝对值",   "zhc_abs",       false},
    {"min",    "最小值",   "zhc_min",       false},
    {"max",    "最大值",   "zhc_max",       false},
    {"len",    "长度",     "zhc_len",       true},
    {"chr",    "字符码转字符", "zhc_chr",   false},
    {"ord",    "字符转码点",   "zhc_ord",   false},
    {"round",  "四舍五入",   "zhc_round",   false},
    {"pow",    "幂函数",     "zhc_pow",     false},
    {"hex",    "转十六进制", "zhc_hex",     false},
    {"oct",    "转八进制",   "zhc_oct",     false},
    {"bin",    "转二进制",   "zhc_bin",     false},
    {"int",    "整数型转换",  "zhc_py_int", true},
    {"float",  "浮点型转换",  "zhc_py_float", true},
    {"str",    "字符串转换",  "zhc_py_str", true},
    {"bool",   "逻辑型转换",  "zhc_py_bool", true},
};

/// 需要 C 库实现的映射
static const BuiltinMapping RuntimeMappings[] = {
    {"input",     "zhc_input",     "PyObject* zhc_input(PyObject* prompt)",    true},
    {"open",      "zhc_fopen",     "PyObject* zhc_fopen(PyObject* path, PyObject* mode)", true},
    {"range",     "zhc_range",     "PyObject* zhc_range(Py_ssize_t start, Py_ssize_t stop, Py_ssize_t step)", true},
    {"enumerate", "zhc_enumerate", "PyObject* zhc_enumerate(PyObject* iterable)", true},
    {"zip",       "zhc_zip",       "PyObject* zhc_zip(PyObject* a, PyObject* b)", true},
    {"map",       "zhc_map",       "PyObject* zhc_map(PyObject* func, PyObject* iter)", true},
    {"filter",    "zhc_filter",    "PyObject* zhc_filter(PyObject* func, PyObject* iter)", true},
    {"isinstance","zhc_is_instance","int zhc_is_instance(PyObject* obj, const char* type_name)", true},
    {"hasattr",   "zhc_has_attr",  "int zhc_has_attr(PyObject* obj, const char* name)", true},
    {"getattr",   "zhc_get_attr",  "PyObject* zhc_get_attr(PyObject* obj, const char* name)", true},
    {"setattr",   "zhc_set_attr",  "int zhc_set_attr(PyObject* obj, const char* name, PyObject* val)", true},
};

/// Python 内置函数映射器
class PythonBuiltinMapper {
public:
    /// 查找 Python 内置函数的 ZHC 等价
    const BuiltinMapping *lookup(llvm::StringRef PythonFuncName);

    /// 检查是否为 Python 内置函数
    bool isBuiltin(llvm::StringRef FuncName);

    /// 获取所有需要运行时实现的函数列表
    static llvm::SmallVector<llvm::StringRef, 16> getRuntimeFunctions();
};

} // namespace frontend
} // namespace zhc
```

### 7.2 实现要点

```cpp
// lib/Frontend/PythonBuiltins.cpp

const BuiltinMapping *PythonBuiltinMapper::lookup(llvm::StringRef Name) {
    // 先查直接映射
    for (auto &M : DirectMappings)
        if (M.PythonName == Name) return &M;
    // 再查运行时映射
    for (auto &M : RuntimeMappings)
        if (M.PythonName == Name) return &M;
    return nullptr;
}

llvm::SmallVector<llvm::StringRef, 16>
PythonBuiltinMapper::getRuntimeFunctions() {
    llvm::SmallVector<llvm::StringRef, 16> Result;
    for (auto &M : RuntimeMappings)
        if (M.NeedsRuntime) Result.push_back(M.CType);
    return Result;
}
```

### 7.3 验收标准

```bash
ctest -R PythonBuiltins --output-on-failure
# 测试用例：
# - print → 打印（直接映射）
# - input → zhc_input（运行时映射）
# - unknown_func → nullptr
# - 运行时函数列表正确
```

---

## T6.8：Python Parser（核心）

**工时**: 40h  
**依赖**: T6.6, T6.7  
**交付物**: `include/zhc/Frontend/PythonParser.h` + `lib/Frontend/PythonParser.cpp`

### 8.1 头文件设计

```cpp
// include/zhc/Frontend/PythonParser.h
#pragma once

#include "zhc/AST.h"
#include "zhc/Frontend/PythonTypeMapping.h"
#include "zhc/Frontend/PythonBuiltins.h"

namespace zhc {
namespace frontend {

/// Python 语法特有 AST 节点（在桥接时转换为 ZHC AST）
class PyListCompExpr;     // 列表推导 → 循环
class PyGeneratorExpr;    // 生成器 → 协程
class PyWithStmt;         // with 语句 → 初始化/清理
class PyYieldExpr;        // yield → 协程挂起
class PyDecorators;       // 装饰器（v1.0 不支持）

/// Python Parser：将 Python 源码解析为 AST
///
/// v1.0 支持范围：
/// ✅ 变量声明与基本类型（int, float, str, bool, list, dict）
/// ✅ 函数定义与调用
/// ✅ if/elif/else 条件判断
/// ✅ for/while 循环（支持 range()）
/// ✅ return 语句
/// ✅ print() / input()
/// ✅ 基本运算符
/// ✅ 字符串操作
/// ✅ 列表操作
/// ✅ 注释
/// ⚠️ 动态类型变量（尽力推导，运行时类型检查兜底）
/// ❌ import / from（需要模块系统，Phase 6 T6.12）
/// ❌ class 继承（v1.0 暂不支持）
/// ❌ 生成器 / yield（v1.0 暂不支持）
/// ❌ 装饰器（v1.0 暂不支持）
/// ❌ with 语句（v1.0 暂不支持）
class PythonParser {
public:
    PythonParser(DiagnosticsEngine &Diags,
                 PythonTypeMapper &TypeMapper,
                 PythonBuiltinMapper &BuiltinMapper);

    /// 解析 Python 源文件
    TranslationUnit *parse(llvm::StringRef Source, llvm::StringRef FilePath);

private:
    DiagnosticsEngine &Diags;
    PythonTypeMapper &TypeMapper;
    PythonBuiltinMapper &BuiltinMapper;

    // 缩进栈（Python 靠缩进确定代码块）
    std::vector<unsigned> IndentStack;
    unsigned CurrentIndent = 0;

    // 类型推导
    llvm::StringMap<QualType> VariableTypes;  // 变量类型推导结果

    // 解析方法
    TranslationUnit *parseModule();
    FunctionDecl *parseFunctionDef();
    VarDecl *parseAssignment();
    Stmt *parseStatement();
    Stmt *parseIfStatement();
    Stmt *parseForStatement();
    Stmt *parseWhileStatement();
    Expr *parseExpression();
    Expr *parseListLiteral();       // [1, 2, 3]
    Expr *parseDictLiteral();       // {"key": "value"}
    Expr *parseTupleLiteral();      // (1, 2, 3)
    Expr *parseStringInterpolation(); // f"Hello {name}"
    Expr *parseSubscription();      // arr[index]
    Expr *parseAttributeAccess();   // obj.attr

    // 缩进处理
    bool handleIndentation();
    unsigned computeIndentLevel(llvm::StringRef Line);
    bool isAtIndentLevel(unsigned Level);

    // 类型推导辅助
    QualType inferTypeFromValue(Expr *Value);
    QualType inferTypeFromName(llvm::StringRef VarName, Expr *Value);
};

} // namespace frontend
} // namespace zhc
```

### 8.2 核心实现

```cpp
// lib/Frontend/PythonParser.cpp

TranslationUnit *PythonParser::parseModule() {
    std::vector<Decl *> Decls;
    while (!isEOF()) {
        skipBlankLines();
        if (isEOF()) break;

        // 根据首关键词分发
        if (peekKeyword("def"))
            Decls.push_back(parseFunctionDef());
        else if (peekKeyword("class"))
            Diags.report(diag::err_python_unsupported, "class 继承");
        else if (peekKeyword("import") || peekKeyword("from"))
            Diags.report(diag::err_python_unsupported, "import（需要模块系统）");
        else
            Decls.push_back(parseAssignment()); // 模块级变量
    }
    return new (Context) TranslationUnit(Decls);
}

FunctionDecl *PythonParser::parseFunctionDef() {
    consumeKeyword("def");
    llvm::StringRef Name = parseIdentifier();
    expect('(');

    // 参数列表
    std::vector<ParamDecl *> Params;
    while (!peek(')')) {
        llvm::StringRef ParamName = parseIdentifier();
        QualType ParamTy = QualType();  // Python 无类型标注 → 延迟推导

        // 类型标注（可选）：def foo(x: int, y: float)
        if (consumeIf(':')) {
            llvm::StringRef TypeAnnotation = parseIdentifier();
            ParamTy = TypeMapper.mapType(TypeAnnotation);
        }

        Params.push_back(new (Context) ParamDecl(ParamName, ParamTy));
        consumeIf(',');
    }
    expect(')');

    // 返回类型标注（可选）：def foo() -> int
    QualType RetTy = QualType();
    if (consumeIf('-')) {
        expect('>');
        llvm::StringRef RetAnnotation = parseIdentifier();
        RetTy = TypeMapper.mapType(RetAnnotation);
    }

    expect(':');

    // 函数体（缩进块）
    increaseIndent();
    Stmt *Body = parseBlock();
    decreaseIndent();

    // 推导返回类型（如果没有标注）
    if (RetTy.isNull())
        RetTy = inferReturnType(Body);

    return new (Context) FunctionDecl(Name, RetTy, Params, Body);
}

// 列表推导：[expr for x in iterable if condition]
// → 转换为循环：
//   result = []
//   for x in iterable:
//       if condition:
//           result.append(expr)
Expr *PythonParser::parseListComprehension() {
    consume('[');
    Expr *Value = parseExpression();
    expectKeyword("for");
    llvm::StringRef Var = parseIdentifier();
    expectKeyword("in");
    Expr *Iterable = parseExpression();

    // 可选 if 条件
    Expr *Condition = nullptr;
    if (peekKeyword("if")) {
        consumeKeyword("if");
        Condition = parseExpression();
    }
    expect(']');

    // 转换为 ZHC 循环
    // TODO: 在 CAstBridge 中实现
    return new (Context) ListCompExpr(Value, Var, Iterable, Condition);
}
```

### 8.3 缩进处理

```cpp
unsigned PythonParser::computeIndentLevel(llvm::StringRef Line) {
    unsigned Indent = 0;
    for (char C : Line) {
        if (C == ' ') Indent++;
        else if (C == '\t') Indent += 4;  // tab = 4 spaces
        else break;
    }
    return Indent;
}

bool PythonParser::handleIndentation() {
    unsigned NewIndent = computeIndentLevel(currentLine());

    if (NewIndent > CurrentIndent) {
        // 增加缩进 → 进入新块
        if (NewIndent != CurrentIndent + 4) {
            // Python 要求缩进一致
            Diags.report(diag::err_inconsistent_indent);
            return false;
        }
        IndentStack.push_back(CurrentIndent);
        CurrentIndent = NewIndent;
    } else if (NewIndent < CurrentIndent) {
        // 减少缩进 → 退出块
        while (!IndentStack.empty() && IndentStack.back() > NewIndent) {
            IndentStack.pop_back();
        }
        if (IndentStack.empty() && NewIndent > 0) {
            Diags.report(diag::err_unindent_no_match);
            return false;
        }
        CurrentIndent = NewIndent;
    }
    return true;
}
```

### 8.4 验收标准

```bash
ctest -R PythonParser --output-on-failure
# 测试用例：
# - hello.py → Hello World
# - fibonacci.py → 递归
# - types.py → 类型推导（int, float, str, bool）
# - list_ops.py → 列表操作
# - dict_ops.py → 字典操作
# - for_range.py → for + range
# - if_elif_else.py → 条件判断
# - function_def.py → 函数定义与调用
# - 缩进错误检测
# - 不支持特性报错（class, import, yield）
```

---

## T6.9：Python C 运行时库

**工时**: 24h  
**依赖**: T6.6, T6.7  
**交付物**: `runtime/zhc_python_stdlib.h` + `runtime/zhc_python_stdlib.c`

### 9.1 头文件设计

```c
/* runtime/zhc_python_stdlib.h
 * Python 内置类型的 C 实现
 * 策略：一切皆对象 + 引用计数
 */

#ifndef ZHC_PYTHON_STDLIB_H
#define ZHC_PYTHON_STDLIB_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ====== PyObject 基类 ====== */

typedef struct PyTypeObject PyTypeObject;

typedef struct PyObject {
    PyTypeObject *ob_type;    // 类型对象
    int ob_refcnt;            // 引用计数
} PyObject;

/* 引用计数宏 */
#define Py_INCREF(op)   ((op)->ob_refcnt++)
#define Py_DECREF(op) do { \
    if (--((op)->ob_refcnt) <= 0) \
        PyObject_Free((PyObject*)(op)); \
} while(0)

#define Py_XDECREF(op) do { if ((op) != NULL) Py_DECREF(op); } while(0)

/* 类型对象 */
struct PyTypeObject {
    const char *tp_name;           // 类型名称 "list", "dict", "str"
    size_t tp_basicsize;           // 基础大小
    void (*tp_dealloc)(PyObject*); // 析构函数
};

/* 全局类型对象 */
extern PyTypeObject PyList_Type;
extern PyTypeObject PyDict_Type;
extern PyTypeObject PyStr_Type;
extern PyTypeObject PyTuple_Type;
extern PyTypeObject PySet_Type;
extern PyTypeObject PyInt_Type;
extern PyTypeObject PyFloat_Type;
extern PyTypeObject PyBool_Type;
extern PyTypeObject PyNone_Type;

/* PyObject 通用操作 */
void PyObject_Free(PyObject *obj);
const char* PyObject_TypeName(PyObject *obj);

/* ====== PyInt 整数对象 ====== */

typedef struct {
    PyObject ob_base;
    int64_t value;
} PyInt;

PyInt*    PyInt_FromLong(int64_t val);
int64_t   PyInt_AsLong(PyObject *obj);

/* ====== PyFloat 浮点对象 ====== */

typedef struct {
    PyObject ob_base;
    double value;
} PyFloat;

PyFloat*  PyFloat_FromDouble(double val);
double    PyFloat_AsDouble(PyObject *obj);

/* ====== PyBool 布尔对象 ====== */

typedef struct {
    PyObject ob_base;
    bool value;
} PyBool;

extern PyBool Py_True;   // 单例
extern PyBool Py_False;  // 单例
#define Py_RETURN_TRUE  return (PyObject*)&Py_True
#define Py_RETURN_FALSE return (PyObject*)&Py_False

/* ====== PyNone 空对象 ====== */

typedef struct {
    PyObject ob_base;
} PyNone;

extern PyNone Py_None;   // 单例
#define Py_RETURN_NONE return (PyObject*)&Py_None

/* ====== PyString 字符串对象 ====== */

typedef struct {
    PyObject ob_base;
    char *data;           // UTF-8 编码
    size_t length;        // 字符数
    size_t hash;          // 缓存的哈希值
} PyString;

PyString* PyString_FromString(const char *str);
PyString* PyString_FromFormat(const char *fmt, ...);
const char* PyString_AsUTF8(PyObject *obj);
size_t     PyString_Length(PyObject *obj);

/* ====== PyList 列表对象 ====== */

typedef struct {
    PyObject ob_base;
    PyObject **items;     // 元素数组
    size_t allocated;     // 已分配容量
    size_t size;          // 实际元素数
} PyList;

PyList*    PyList_New(size_t initial_size);
int        PyList_Append(PyObject *list, PyObject *item);
PyObject*  PyList_GetItem(PyObject *list, size_t index);
int        PyList_SetItem(PyObject *list, size_t index, PyObject *item);
size_t     PyList_Size(PyObject *list);
PyList*    PyList_Slice(PyObject *list, size_t start, size_t stop, size_t step);

/* ====== PyDict 字典对象 ====== */

typedef struct PyDictEntry {
    PyObject *key;
    PyObject *value;
    struct PyDictEntry *next;  // 哈希冲突链
} PyDictEntry;

typedef struct {
    PyObject ob_base;
    PyDictEntry **entries;   // 哈希表
    size_t table_size;        // 哈希表大小
    size_t num_entries;       // 条目数
} PyDict;

PyDict*    PyDict_New(void);
PyObject*  PyDict_GetItem(PyObject *dict, PyObject *key);
int        PyDict_SetItem(PyObject *dict, PyObject *key, PyObject *value);
size_t     PyDict_Size(PyObject *dict);

/* ====== PyTuple 元组对象 ====== */

typedef struct {
    PyObject ob_base;
    PyObject **items;
    size_t size;
} PyTuple;

PyTuple*   PyTuple_New(size_t size);
PyObject*  PyTuple_GetItem(PyObject *tuple, size_t index);

/* ====== Python 内置函数 C 实现 ====== */

PyObject* zhc_input(PyObject *prompt);
PyObject* zhc_range(int64_t start, int64_t stop, int64_t step);
int       zhc_is_instance(PyObject *obj, const char *type_name);
int       zhc_has_attr(PyObject *obj, const char *name);
PyObject* zhc_get_attr(PyObject *obj, const char *name);
int       zhc_set_attr(PyObject *obj, const char *name, PyObject *val);

/* 打印函数 */
void zhc_print_int(int64_t val);
void zhc_print_float(double val);
void zhc_print_str(const char *val);
void zhc_print_bool(bool val);
void zhc_print_list(PyObject *list);
void zhc_print_dict(PyObject *dict);

/* 长度 */
size_t zhc_len(PyObject *obj);

#ifdef __cplusplus
}
#endif

#endif /* ZHC_PYTHON_STDLIB_H */
```

### 9.2 核心实现

```c
/* runtime/zhc_python_stdlib.c */

#include "zhc_python_stdlib.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/* ====== PyObject 通用操作 ====== */

void PyObject_Free(PyObject *obj) {
    if (!obj) return;
    if (obj->ob_type && obj->ob_type->tp_dealloc)
        obj->ob_type->tp_dealloc(obj);
    else
        free(obj);
}

const char* PyObject_TypeName(PyObject *obj) {
    return obj && obj->ob_type ? obj->ob_type->tp_name : "unknown";
}

/* ====== PyInt 实现 ====== */

static void PyInt_Dealloc(PyObject *obj) { free(obj); }

PyTypeObject PyInt_Type = {
    .tp_name = "int",
    .tp_basicsize = sizeof(PyInt),
    .tp_dealloc = PyInt_Dealloc,
};

PyInt* PyInt_FromLong(int64_t val) {
    PyInt *obj = (PyInt*)malloc(sizeof(PyInt));
    obj->ob_base.ob_type = &PyInt_Type;
    obj->ob_base.ob_refcnt = 1;
    obj->value = val;
    return obj;
}

int64_t PyInt_AsLong(PyObject *obj) {
    if (obj->ob_type == &PyInt_Type)
        return ((PyInt*)obj)->value;
    return 0; // 类型错误
}

/* ====== PyList 实现 ====== */

static void PyList_Dealloc(PyObject *obj) {
    PyList *list = (PyList*)obj;
    // 释放所有元素（DECREF）
    for (size_t i = 0; i < list->size; i++)
        Py_XDECREF(list->items[i]);
    free(list->items);
    free(list);
}

PyTypeObject PyList_Type = {
    .tp_name = "list",
    .tp_basicsize = sizeof(PyList),
    .tp_dealloc = PyList_Dealloc,
};

PyList* PyList_New(size_t initial_size) {
    PyList *list = (PyList*)malloc(sizeof(PyList));
    list->ob_base.ob_type = &PyList_Type;
    list->ob_base.ob_refcnt = 1;
    list->allocated = initial_size > 0 ? initial_size : 4;
    list->items = (PyObject**)calloc(list->allocated, sizeof(PyObject*));
    list->size = 0;
    return list;
}

int PyList_Append(PyObject *obj, PyObject *item) {
    PyList *list = (PyList*)obj;
    if (list->size >= list->allocated) {
        list->allocated *= 2;
        list->items = (PyObject**)realloc(list->items,
            list->allocated * sizeof(PyObject*));
    }
    Py_INCREF(item);
    list->items[list->size++] = item;
    return 0;
}

/* ====== zhc_range 实现 ====== */

PyObject* zhc_range(int64_t start, int64_t stop, int64_t step) {
    if (step == 0) return NULL;
    size_t count = (stop - start) / step;
    if ((stop - start) * step < 0) count = 0; // 无效范围

    PyList *list = PyList_New(count);
    for (size_t i = 0; i < count; i++) {
        PyInt *val = PyInt_FromLong(start + (int64_t)i * step);
        PyList_Append((PyObject*)list, (PyObject*)val);
        Py_DECREF(val);
    }
    return (PyObject*)list;
}

/* ====== zhc_input 实现 ====== */

PyObject* zhc_input(PyObject *prompt) {
    if (prompt) {
        const char *str = PyString_AsUTF8(prompt);
        if (str) printf("%s", str);
    }
    fflush(stdout);

    char buffer[1024];
    if (fgets(buffer, sizeof(buffer), stdin) == NULL)
        return (PyObject*)PyString_FromString("");

    // 去除末尾换行
    size_t len = strlen(buffer);
    if (len > 0 && buffer[len-1] == '\n') buffer[len-1] = '\0';

    return (PyObject*)PyString_FromString(buffer);
}
```

### 9.3 验收标准

```bash
ctest -R PythonStdlib --output-on-failure
# 测试用例：
# - PyInt 创建/取值/DECREF
# - PyString UTF-8 创建/取值
# - PyList 创建/Append/GetItem/Slice
# - PyDict 创建/SetItem/GetItem
# - zhc_range(0, 10, 1) → [0,1,...,9]
# - 引用计数正确（无内存泄漏）
# - 大列表扩容正确
```

---

## T6.10：Python 前端测试

**工时**: 16h  
**依赖**: T6.6, T6.7, T6.8, T6.9  
**交付物**: `test/integration/python_frontend_test.cpp`

### 10.1 测试 fixture 文件

| 文件 | 内容 |
|:---|:---|
| `test/fixtures/python/hello.py` | `print("Hello, World!")` |
| `test/fixtures/python/fibonacci.py` | 递归斐波那契 |
| `test/fixtures/python/types.py` | 类型推导测试 |
| `test/fixtures/python/list_ops.py` | 列表 append/slice/len |
| `test/fixtures/python/dict_ops.py` | 字典 get/set |
| `test/fixtures/python/for_range.py` | `for i in range(10)` |
| `test/fixtures/python/if_elif.py` | if/elif/else |
| `test/fixtures/python/function.py` | 函数定义+调用 |

### 10.2 测试代码

```cpp
// test/integration/python_frontend_test.cpp

class PythonFrontendTest : public ::testing::Test {
protected:
    void compilePythonAndRun(llvm::StringRef Source,
                              llvm::StringRef ExpectedOutput) {
        // 1. Python Parser
        PythonTypeMapper TypeMapper(TypeCtx);
        PythonBuiltinMapper BuiltinMapper;
        PythonParser Parser(Diags, TypeMapper, BuiltinMapper);
        TranslationUnit *AST = Parser.parse(Source, "test.py");
        ASSERT_NE(AST, nullptr);

        // 2. 共用语义分析 + IR 生成
        Sema.Analyze(AST);
        auto Mod = CG.codegen(AST);

        // 3. 链接 Python 运行时库
        linkWithRuntime(*Mod, "zhc_python_stdlib");

        // 4. 运行并检查输出
        auto Output = linkAndRun(*Mod);
        EXPECT_EQ(Output, ExpectedOutput);
    }
};

TEST_F(PythonFrontendTest, HelloWorld) {
    compilePythonAndRun("print(\"Hello, World!\")", "Hello, World!\n");
}

TEST_F(PythonFrontendTest, Fibonacci) {
    compilePythonAndRun(
        "def fib(n):\n"
        "    if n <= 1:\n"
        "        return n\n"
        "    return fib(n-1) + fib(n-2)\n"
        "\n"
        "print(fib(10))",
        "55\n");
}

TEST_F(PythonFrontendTest, ForRange) {
    compilePythonAndRun(
        "for i in range(5):\n"
        "    print(i)",
        "0\n1\n2\n3\n4\n");
}

TEST_F(PythonFrontendTest, ListAppend) {
    compilePythonAndRun(
        "x = []\n"
        "x.append(1)\n"
        "x.append(2)\n"
        "print(len(x))",
        "2\n");
}
```

### 10.3 验收标准

```bash
ctest -R PythonFrontend --output-on-failure
# 全部通过
```

---

## T6.11：多语言统一测试（端到端）

**工时**: 16h  
**依赖**: T6.5, T6.10  
**交付物**: `test/integration/multilang_test.cpp`

### 11.1 多语言编译流水线集成

```cpp
// test/integration/multilang_test.cpp

class MultilangTest : public ::testing::Test {
protected:
    CompilationPipeline Pipeline;

    void compileAndRun(llvm::StringRef FilePath,
                       llvm::StringRef ExpectedOutput) {
        auto Result = Pipeline.compileFile(FilePath);
        ASSERT_TRUE(Result.Success);
        auto Output = execute(Result.ExecutablePath);
        EXPECT_EQ(Output, ExpectedOutput);
    }
};

// 测试1：ZHC 文件编译运行
TEST_F(MultilangTest, ZHCFile) {
    compileAndRun("test/fixtures/multilang/hello.zhc", "Hello from ZHC\n");
}

// 测试2：C 文件编译运行
TEST_F(MultilangTest, CFile) {
    compileAndRun("test/fixtures/multilang/hello.c", "Hello from C\n");
}

// 测试3：Python 文件编译运行
TEST_F(MultilangTest, PythonFile) {
    compileAndRun("test/fixtures/multilang/hello.py", "Hello from Python\n");
}

// 测试4：混合编译（ZHC + C）
TEST_F(MultilangTest, MixedZHCC) {
    // main.zhc 调用 utils.c 中定义的函数
    compileAndRun("test/fixtures/multilang/main_plus_utils",
                  "Result: 42\n");
}

// 测试5：语言自动检测
TEST_F(MultilangTest, AutoDetection) {
    auto Lang1 = LanguageDetector::detect("hello.zhc", "");
    EXPECT_EQ(Lang1.Language, SourceLanguage::ZHC);

    auto Lang2 = LanguageDetector::detect("hello.c", "");
    EXPECT_EQ(Lang2.Language, SourceLanguage::C);

    auto Lang3 = LanguageDetector::detect("hello.py", "");
    EXPECT_EQ(Lang3.Language, SourceLanguage::Python);
}

// 测试6：统一语义分析（三语言共享）
TEST_F(MultilangTest, SharedSemanticAnalysis) {
    // 三种语言写的相同逻辑，语义分析结果应一致
    // hello.zhc: 函数 整数型 add(整数型 a, 整数型 b) { 返回 a + b; }
    // hello.c:   int add(int a, int b) { return a + b; }
    // hello.py:  def add(a, b): return a + b
    // 三者 Sema 分析后，函数签名应映射为相同 LLVM 类型
}
```

### 11.2 测试 fixture 文件

```
test/fixtures/multilang/
├── hello.zhc        # ZHC Hello World
├── hello.c          # C Hello World
├── hello.py         # Python Hello World
├── main_plus_utils/ # 混合编译
│   ├── main.zhc     # 调用 C 函数
│   └── utils.c      # C 工具函数
└── shared_logic/    # 三语言相同逻辑
    ├── logic.zhc
    ├── logic.c
    └── logic.py
```

### 11.3 验收标准

```bash
ctest -R Multilang --output-on-failure
# 全部通过，包括：
# - .zhc 编译运行
# - .c 编译运行
# - .py 编译运行
# - 混合编译成功
# - 语言自动检测正确
```

---

## T6.12：E2 模块系统

**工时**: 56h  
**依赖**: Phase 2 符号表 + 作用域  
**交付物**: `include/zhc/Module.h` + `lib/Module.cpp` + `include/zhc/SemaModule.cpp`

### 12.1 模块系统设计

```cpp
// include/zhc/Module.h
#pragma once

#include "llvm/ADT/StringMap.h"
#include "llvm/ADT/DenseSet.h"

namespace zhc {

/// 模块可见性
enum class Visibility {
    Public,     // 公有 — 可被其他模块访问
    Private,    // 私有 — 仅模块内部可见
    Internal,   // 内部 — 仅同一包内可见
};

/// 模块声明
class ModuleDecl : public Decl {
public:
    llvm::StringRef getName() const { return Name; }
    llvm::ArrayRef<Decl*> getDeclarations() const { return Decls; }

    /// 导出符号列表
    llvm::ArrayRef<llvm::StringRef> getExportedSymbols() const;

private:
    llvm::StringRef Name;
    std::vector<Decl*> Decls;
    llvm::StringMap<Visibility> SymbolVisibility;
};

/// 模块管理器
class ModuleManager {
public:
    /// 加载模块
    ModuleDecl *loadModule(llvm::StringRef Name, llvm::StringRef Path);

    /// 查找模块
    ModuleDecl *findModule(llvm::StringRef Name);

    /// 解析导入声明
    bool resolveImport(ImportDecl *Import, SymbolTable &SymTab);

    /// 检测循环依赖
    bool detectCircularDependency(llvm::StringRef ModuleName);

    /// 获取模块依赖图
    llvm::StringMap<llvm::SmallVector<llvm::StringRef, 4>>
    getDependencyGraph();

private:
    llvm::StringMap<std::unique_ptr<ModuleDecl>> LoadedModules;
    llvm::StringMap<llvm::StringRef> ModulePaths;  // 模块名→文件路径

    /// 正在加载的模块（用于检测循环依赖）
    llvm::DenseSet<llvm::StringRef> LoadingModules;
};

} // namespace zhc
```

### 12.2 模块语法

```zhc
// 模块定义：mymodule.zhc
模块 我的模块

// 公有声明（可被其他模块导入）
公有 函数 整数型 add(整数型 a, 整数型 b) {
    返回 a + b;
}

公有 常量 整数型 VERSION = 1;

// 私有声明（仅模块内部可见）
私有 函数 空型 helper() {
    打印("内部函数");
}

// 导入其他模块
导入 "other_module.zhc"
```

### 12.3 循环依赖检测

```cpp
// lib/Module.cpp

bool ModuleManager::detectCircularDependency(llvm::StringRef ModuleName) {
    // DFS 检测环
    llvm::DenseSet<llvm::StringRef> Visited;
    llvm::DenseSet<llvm::StringRef> InStack;

    std::function<bool(llvm::StringRef)> DFS = [&](llvm::StringRef Name) -> bool {
        if (InStack.count(Name)) return true;  // 发现环
        if (Visited.count(Name)) return false; // 已访问，无环

        Visited.insert(Name);
        InStack.insert(Name);

        if (auto *Mod = findModule(Name)) {
            for (auto *D : Mod->getDeclarations()) {
                if (auto *Import = dyn_cast<ImportDecl>(D)) {
                    if (DFS(Import->getModuleName()))
                        return true;
                }
            }
        }

        InStack.erase(Name);
        return false;
    };

    return DFS(ModuleName);
}
```

### 12.4 验收标准

```bash
ctest -R Module --output-on-failure
# 测试用例：
# - 简单模块定义+导入
# - 公有/私有可见性
# - 循环依赖检测（A→B→A 报错）
# - 模块缓存（不重复加载）
# - Python import → 模块系统桥接
```

---

## 6.1 Phase 6 Go/No-Go 检查点

### 检查点：多语言前端完成验收

| 检查项 | 验收命令 | 通过标准 |
|:---|:---|:---|
| **C 文件编译** | `zhc compile hello.c -o hello_c && ./hello_c` | 运行正确 |
| **Python 文件编译** | `zhc compile hello.py -o hello_py && ./hello_py` | 运行正确 |
| **混合编译** | `zhc compile main.zhc utils.c -o app && ./app` | 运行正确 |
| **语言检测** | `.zhc/.c/.py` 自动检测 | 语言识别正确 |
| **C 类型映射** | `int*` → `整数型*` | 类型桥接无误 |
| **Python 运行时** | 引用计数 + 列表/字典/字符串 | 无内存泄漏 |
| **模块系统** | 模块定义+导入+可见性 | 编译正确 |
| **循环依赖** | A→B→A | 编译报错 |

**量化标准**：
- `.zhc/.c/.py` 各 ≥ 3 个用例编译运行正确
- 混合编译 ≥ 1 个用例通过
- Python 运行时 Valgrind 零泄漏
- 模块系统循环依赖 100% 检出

**如未通过**：
- 停 1 周修复 Bug
- Python 运行时泄漏需全部修复后方可通过

---

## 6.2 参考资料

| 资料 | 路径 | 用途 |
|:---|:---|:---|
| 多语言前端扩展 | `docs/ZHC重写项目/14-多语言前端扩展.md` | 架构设计参考 |
| Python 类型映射 | `14-多语言前端扩展.md` 14.3.2 节 | 类型映射表 |
| Python 内置函数 | `14-多语言前端扩展.md` 14.3.3 节 | 函数映射表 |
| Python 运行时 | `14-多语言前端扩展.md` 14.4 节 | C 运行时设计 |
| 多语言路由 | `14-多语言前端扩展.md` 14.5 节 | 编译流水线路由 |
| CPython 源码 | `github.com/python/cpython` | PyObject 设计参考 |
| Clang C Parser | LLVM 源码 `lib/Parse/` | C Parser 参考 |

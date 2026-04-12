# Phase 2：语义分析与代码生成

**版本**: v2.0（根据专家优化分析报告修订）
**日期**: 2026-04-13
**基于文档**: `04-模块重写建议.md`、`11-LLVM集成方案.md`、`12-项目规模与工时估算.md`、`15-重构任务执行清单.md`、`18-超越C的增强特性.md`、`Phase1-5专家优化分析报告.md`
**目标**: 完成语义分析 + LLVM IR 生成，能编译运行真实 ZHC 程序
**工时**: ~1,650h（含 20% 风险缓冲 + 新增特性）
**日历时间**: 约 6-7 个月
**前置条件**: Phase 1 完成（C++ 前端可用）

### v2.0 修订说明（对照专家报告）

> 本版本根据 `Phase1-5专家优化分析报告.md` 的 P2 优先级建议进行了以下修订：
> - **P2-01**: 工时调整 +52%（1232h → ~1650h），各 Task 工时上调
> - **P2-02**: 补充泛型系统（G.01-G.07）迁移任务（152h）— Python 版已有完整实现
> - **P2-03**: 补充异常处理（EH）任务（104h）— try/catch/finally/throw + landingpad IR
> - **P2-04**: 补充模式匹配（M.01-M.05）任务（96h）— Pattern 类型 + 语义分析 + 枚举降级
> - **P2-05**: 补充智能指针/RAII 类型检查（72h）— UniquePtr/SharedPtr/WeakPtr 类型系统
> - **结构调整**: 建议拆分为 Phase2a（Sema）+ Phase2b（CodeGen），降低风险集中度
> - **工时修正**: 各 Task 工时已按专家建议上调，Task 工时加总 ≈ 1100h + 新增 424h + 20% 缓冲 ≈ 1650h

---

## 2.1 阶段目标

本阶段是整个项目的核心，完成语义分析和 LLVM IR 代码生成：

1. **类型系统**：QualType + 类型层次 + 类型检查 + **泛型类型**
2. **符号表与作用域**：符号管理 + 作用域链
3. **语义分析器**：声明/表达式/语句的完整语义分析 + **异常处理分析** + **模式匹配分析**
4. **LLVM IR 生成**：表达式/语句/函数的 IR 翻译 + **EH IR** + **Pattern IR**
5. **调试信息**：DWARF v5 调试信息生成
6. **链接器集成**：LLD 链接器封装（建议移至 Phase3）
7. **E0 安全特性完成**：空指针安全、边界检查、溢出检测、生命周期分析、NULL 处理 + **智能指针类型检查**
8. **E1 语言增强**：穷举 switch、Result 类型、格式化安全检查 + **泛型单态化**

---

## 2.2 Month 4：符号表 + 类型系统

### 任务 2.2.1 类型系统

#### T2.1 设计类型系统（含泛型基础）

> **修订说明**: 工时从 30h 调整为 48h（专家建议），需设计 QualType/Type 派生体系/TypeContext/类型 canonicalization + 泛型类型基础。

**交付物**: `include/zhc/Types.h` + 泛型类型基础定义

**操作步骤**:
1. 实现类型层次（参考 `04-模块重写建议.md` 4.4.3 节）：

```cpp
// include/zhc/Types.h
namespace zhc {

// 基础类型 Kind
enum class TypeKind {
    Void, Bool, Char, Short, Int, Long, LongLong,
    Float, Double, LongDouble,
    Pointer, Array, Function, Struct, Union, Enum,
    Vector, Atomic, Complex
};

// QualType：限定的类型（带 const/volatile/restrict）
class QualType {
public:
    QualType() : T(nullptr), Q(0) {}
    QualType(Type *T, unsigned Q = 0) : T(T), Q(Q) {}

    Type *getType() const { return T; }
    unsigned getQualifiers() const { return Q; }

    bool isNull() const { return T == nullptr; }
    bool hasConst() const { return Q & 1; }
    bool hasVolatile() const { return Q & 2; }

    QualType withConst() const { return QualType(T, Q | 1); }
    QualType withVolatile() const { return QualType(T, Q | 2); }

    bool operator==(QualType Other) const { return T == Other.T && Q == Other.Q; }
    bool operator!=(QualType Other) const { return !(*this == Other); }

private:
    Type *T;
    unsigned Q;  // bitmask: 1=const, 2=volatile, 4=restrict, 8=atomic
};

// Type 基类
class Type {
public:
    virtual ~Type() = default;
    TypeKind getKind() const { return Kind; }

    virtual bool isInteger() const;
    virtual bool isFloatingPoint() const;
    virtual bool isScalar() const;
    virtual bool isPointer() const;
    virtual bool isArray() const;
    virtual bool isFunction() const;
    virtual bool isRecord() const;   // struct/union
    virtual bool isEnum() const;

    virtual std::string toString() const;

protected:
    explicit Type(TypeKind K) : Kind(K) {}
    TypeKind Kind;
};

// 基础类型（int/float/char/void/bool）
class BuiltinType : public Type {
public:
    static bool classof(const Type *T) { return T->getKind() == TypeKind::Int; }

    enum BuiltinKind { Void=0, Bool, Char, Short, Int, Long, LongLong,
                        Float, Double, LongDouble };
    BuiltinType(BuiltinKind K) : Type(TypeKind::Int), Kind(K) {}
    BuiltinKind getKind() const { return Kind; }

    std::string toString() const override;
private:
    BuiltinKind Kind;
};

// 指针类型
class PointerType : public Type {
public:
    static bool classof(const Type *T) { return T->getKind() == TypeKind::Pointer; }
    PointerType(QualType Pointee) : Type(TypeKind::Pointer), PointeeType(Pointee) {}
    QualType getPointeeType() const { return PointeeType; }
private:
    QualType PointeeType;
};

// 数组类型
class ArrayType : public Type {
public:
    static bool classof(const Type *T) { return T->getKind() == TypeKind::Array; }
    ArrayType(QualType Element, uint64_t Size)
        : Type(TypeKind::Array), ElementType(Element), Size(Size) {}
    ArrayType(QualType Element)  // VLA
        : Type(TypeKind::Array), ElementType(Element), Size(~0ULL) {}
    QualType getElementType() const { return ElementType; }
    uint64_t getSize() const { return Size; }
    bool hasKnownSize() const { return Size != ~0ULL; }
private:
    QualType ElementType;
    uint64_t Size;
};

// 函数类型
class FunctionType : public Type {
public:
    static bool classof(const Type *T) { return T->getKind() == TypeKind::Function; }
    FunctionType(QualType Ret, ArrayRef<QualType> Params, bool VarArg)
        : Type(TypeKind::Function), ReturnType(Ret), Params(Params), IsVarArg(VarArg) {}
    QualType getReturnType() const { return ReturnType; }
    ArrayRef<QualType> getParamTypes() const { return Params; }
    bool isVarArg() const { return IsVarArg; }
private:
    QualType ReturnType;
    std::vector<QualType> Params;
    bool IsVarArg;
};

// 结构体类型
class RecordType : public Type {
public:
    static bool classof(const Type *T) { return T->getKind() == TypeKind::Struct; }
    RecordType(StructDecl *Decl) : Type(TypeKind::Struct), Decl(Decl) {}
    StructDecl *getDecl() const { return Decl; }
private:
    StructDecl *Decl;
};

// 枚举类型
class EnumType : public Type {
public:
    static bool classof(const Type *T) { return T->getKind() == TypeKind::Enum; }
    EnumType(EnumDecl *Decl) : Type(TypeKind::Enum), Decl(Decl) {}
    EnumDecl *getDecl() const { return Decl; }
private:
    EnumDecl *Decl;
};

// 可空类型 ?空型<T>（E0 安全特性 S01）
class NullableType : public Type {
public:
    static bool classof(const Type *T) { return T->getKind() == TypeKind::Nullable; }
    NullableType(QualType Inner) : Type(TypeKind::Nullable), InnerType(Inner) {}
    QualType getInnerType() const { return InnerType; }
private:
    QualType InnerType;
};

} // namespace zhc
```

2. 创建类型上下文（用于类型比较和转换）：
```cpp
class TypeContext {
public:
    bool isSameType(QualType T1, QualType T2) const;
    bool isCompatible(QualType Dst, QualType Src) const;
    struct ConversionResult { bool Valid; CastKind Kind; };
    ConversionResult canImplicitlyConvert(Expr *From, QualType To) const;
    QualType usualArithmeticConversions(QualType, QualType);
};
```

**参考**: `04-模块重写建议.md` 4.4.3 节，`src/zhc/type_system/` Python 版本

**工时**: 48h（原 30h，专家建议上调 — 需含类型 canonicalization + 泛型类型基础）

---

#### T2.2 实现类型检查器

**交付物**: `include/zhc/TypeChecker.h` + `lib/TypeChecker.cpp`

**操作步骤**:
1. 实现类型检查的核心逻辑：

```cpp
// include/zhc/TypeChecker.h
class TypeChecker {
public:
    TypeChecker(Sema &S) : Sema(S) {}

    /// 检查二元运算符类型
    QualType checkBinaryOperator(BinaryOperator *BO);

    /// 检查一元运算符类型
    QualType checkUnaryOperator(UnaryOperator *UO);

    /// 检查函数调用
    QualType checkCallExpr(CallExpr *CE, FunctionDecl *FD);

    /// 检查数组索引
    QualType checkArrayAccess(IndexExpr *IE);

    /// 检查赋值
    bool checkAssignment(Expr *LHS, Expr *RHS);

    /// 检查类型转换
    bool checkCast(Expr *E, QualType TargetTy);

private:
    Sema &Sema;
    DiagnosticsEngine &Diags;
};
```

2. 实现类型转换规则：
   - `int + float` → `float`
   - `int * int` → `int`
   - `bool && bool` → `bool`
   - 指针算术：`ptr + int` → `ptr`
   - 下标转换：`arr[n]` → `*(arr + n)`

**参考**: Python 版本 `src/zhc/type_system/type_checker.py`

**工时**: 120h（原 80h，专家建议上调 — 需含隐式转换规则 20+ 条、重载决议、模板参数推导）

---

#### T2.3 实现类型推导

**交付物**: `include/zhc/TypeInference.h` + `lib/TypeInference.cpp`

**操作步骤**:
1. 实现局部类型推导：

```cpp
// include/zhc/TypeInference.h
class TypeInference {
public:
    TypeInference(TypeContext &Ctx) : Context(Ctx) {}

    /// 推导变量声明类型
    QualType inferVarDeclType(VarDecl *VD);

    /// 推导函数返回类型
    QualType inferReturnType(ReturnStmt *RS);

    /// 推导泛型实例化（Phase 2 后期）
    QualType inferGenericCall(CallExpr *CE, FunctionDecl *FD);

private:
    TypeContext &Context;
    /// 处理 const 传播
    QualType propagateConst(Expr *E);
};
```

**参考**: Python 版本 `src/zhc/semantic/type_inference.py`

**工时**: 40h

---

#### T2.3a 泛型类型系统（P2-02，G.01-G.02 迁移）

> **来源**: 专家报告 P2-02（🔴 Critical）— Python 版已有完整泛型实现（G.01-G.07，177 测试全通过）
> **优先级**: P2（语言核心特性）
> **理由**: ZhC 的 `泛型<T>` 语法是语言核心特性，类型系统如果没有泛型，`std::vector<T>`、`Result<T,E>` 等都无法表示

**交付物**: `include/zhc/GenericTypes.h` + `lib/GenericTypes.cpp`

**操作步骤**:

1. 定义泛型类型节点：

```cpp
// include/zhc/GenericTypes.h
namespace zhc {

/// 泛型类型参数（如 `泛型<T>` 中的 T）
class TypeParameter {
public:
    StringRef Name;            // 参数名（T, K, V 等）
    SourceLocation Loc;
    QualType Constraint;       // where 约束（可选）
    unsigned Index;            // 参数位置（0, 1, 2...）
};

/// 泛型声明（函数/结构体上的泛型参数列表）
class GenericDecl {
public:
    llvm::ArrayRef<TypeParameter> getTypeParameters() const { return TypeParams; }
    void addTypeParameter(TypeParameter TP);

    /// 获取约束子句
    llvm::ArrayRef<Expr*> getConstraints() const { return Constraints; }

private:
    std::vector<TypeParameter> TypeParams;
    std::vector<Expr*> Constraints;     // where 子句
    Decl *UnderlyingDecl;                // 关联的函数/结构体声明
};

/// 泛型类型实例（如 `List<整数型>`）
class GenericTypeInst : public Type {
public:
    static bool classof(const Type *T) { return T->getKind() == TypeKind::Generic; }

    GenericDecl *getGenericDecl() const { return GenDecl; }
    llvm::ArrayRef<QualType> getTypeArgs() const { return TypeArgs; }

    /// 获取 mangled name（用于 IR 生成）
    std::string getMangledName() const;

private:
    GenericDecl *GenDecl;
    std::vector<QualType> TypeArgs;
};

/// 单态化引擎（将泛型实例化为具体类型）
class Monomorphizer {
public:
    Monomorphizer(ASTContext &Ctx, Sema &S) : Ctx(Ctx), S(S) {}

    /// 将泛型函数/类型实例化为具体版本
    /// @returns 实例化后的声明（使用缓存避免重复实例化）
    Decl *instantiate(GenericDecl *GD, llvm::ArrayRef<QualType> TypeArgs);

    /// 检查约束是否满足
    bool checkConstraints(GenericDecl *GD, llvm::ArrayRef<QualType> TypeArgs);

private:
    ASTContext &Ctx;
    Sema &S;

    /// 实例化缓存：mangled name → 实例化后的 Decl
    llvm::DenseMap<std::string, Decl*> InstanceCache;

    /// 深拷贝 AST 节点并替换类型参数
    Decl *deepCloneAndSubstitute(Decl *D,
                                  llvm::DenseMap<StringRef, QualType> &SubstMap);
};

} // namespace zhc
```

2. **Python 版对照**:

| Python 模块 | C++ 对应 | 行数 |
|:---|:---|:---:|
| `generics.py` `GenericResolver` | `GenericDecl` + 约束解析 | ~600 |
| `generics.py` `Monomorphizer` | `Monomorphizer` 类 | ~800 |
| `generics.py` 深拷贝逻辑 | `deepCloneAndSubstitute` | ~400 |

**参考**: Python 版 `src/zhc/semantic/generics.py`（2888 行）

**工时**: 32h

---

#### T2.3b 泛型约束解析（P2-02）

**交付物**: `lib/GenericConstraints.cpp`

**操作步骤**:

1. 实现 `where` 子句解析和约束检查：

```cpp
// lib/GenericConstraints.cpp
namespace zhc {

/// 解析 where 子句中的约束
/// 示例: `泛型<T> 其中 T : 可比较 { ... }`
bool GenericConstraintSolver::solve(GenericDecl *GD,
                                     ArrayRef<QualType> TypeArgs) {
    for (auto *Constraint : GD->getConstraints()) {
        if (!checkConstraint(Constraint, TypeArgs))
            return false;
    }
    return true;
}

/// 约束类型:
/// - 类型约束: T : SomeTrait（T 必须实现某 trait/接口）
/// - 等值约束: T == 具体类型（T 必须是某具体类型）
/// - 复合约束: T : A + B（T 必须同时满足多个约束）
bool GenericConstraintSolver::checkConstraint(Expr *Constraint,
                                               ArrayRef<QualType> Args) {
    // ... 约束检查实现
}

} // namespace zhc
```

**参考**: Python 版 `src/zhc/semantic/generics.py` 中的约束解析逻辑

**工时**: 24h

---

### 任务 2.2.2 符号表与作用域

#### T2.4 实现符号表

**交付物**: `include/zhc/SymbolTable.h` + `lib/SymbolTable.cpp`

**操作步骤**:
1. 实现符号表和作用域链（参考 `04-模块重写建议.md` 4.4.2 节）：

```cpp
// include/zhc/SymbolTable.h
namespace zhc {

struct Symbol {
    enum Kind {
        Function, Variable, Type, Enum, Struct, Union,
        Parameter, Label, EnumConstant, Module
    };
    Kind kind;
    StringRef Name;
    QualType Type;
    Decl *Declaration = nullptr;
    Scope *DefinedIn = nullptr;
    bool IsDefined = false;
    bool IsReferenced = false;
    bool IsExtern = false;
    bool IsStatic = false;
    SourceLocation Loc;
};

class SymbolTable {
public:
    SymbolTable() : CurScope(nullptr) {}

    /// 进入新作用域
    Scope *enterScope(ScopeKind K);

    /// 退出当前作用域
    void exitScope();

    /// 当前作用域
    Scope *currentScope() const { return CurScope; }

    /// 查找符号（沿作用域链向上）
    Symbol *lookup(StringRef Name);

    /// 在当前作用域插入符号
    bool insert(StringRef Name, Symbol *S);

    /// 在指定作用域插入符号
    bool insertInto(Scope *S, StringRef Name, Symbol *Sym);

    /// 标记符号已定义
    void markDefined(StringRef Name);

    /// 标记符号已引用
    void markReferenced(StringRef Name);

private:
    Scope *CurScope;
    std::vector<Scope*> ScopeStack;
};

} // namespace zhc
```

2. 实现作用域类型：
```cpp
enum class ScopeKind { Global, Namespace, Class, Function, Block };
class Scope {
public:
    ScopeKind Kind;
    Scope *Parent = nullptr;
    std::unordered_map<StringRef, Symbol*> Symbols;
    std::vector<Scope*> Children;
};
```

**参考**: Python 版本 `src/zhc/semantic/symbol_table.py`

**工时**: 40h

---

#### T2.5 实现作用域链

**交付物**: `include/zhc/Scope.h` + `lib/Scope.cpp`

**操作步骤**:
1. 实现作用域链管理：

```cpp
class ScopeChain {
public:
    void enterScope(Scope *S);
    void exitScope();
    Symbol *lookup(llvm::StringRef Name);

    /// 查找所有层级的同名符号
    std::vector<Symbol*> lookupAll(llvm::StringRef Name);

    /// 检查符号是否在内部作用域隐藏了外部同名符号
    bool hidesSymbol(llvm::StringRef Name);

private:
    std::vector<Scope*> Scopes;
};
```

2. 作用域层级：
   - 全局作用域（所有顶层声明）
   - 函数作用域（函数参数 + 函数体局部变量）
   - 块作用域（`{}` 内的局部变量）
   - 类作用域（结构体成员）
   - 标签作用域（`case` 标签，仅在 switch 内）

**工时**: 20h

---

#### T2.6 类型系统测试

**交付物**: `test/unittests/type_test.cpp`

**操作步骤**:
1. 覆盖以下场景：
   - 基础类型：`整数型` `浮点型` `字符型` `布尔型` `空型`
   - 指针类型：`整数型*` `字符型**`
   - 数组类型：`整数型[10]` `整数型[]`（VLA）
   - 函数类型：返回类型 + 参数类型
   - 结构体/枚举类型
   - 可空类型：`?空型 整数型*`
   - 类型转换：`整数型` ↔ `浮点型`（隐式 + 显式）
   - 类型不匹配报错

**验收标准**:
```bash
ctest -R Type --output-on-failure
```

**工时**: 20h

---

## 2.3 Month 5：语义分析器

### 任务 2.3.1 语义分析器

#### T2.7 声明分析

**交付物**: `lib/SemaDecl.cpp`

**操作步骤**:
1. 实现函数体外的声明分析：

```cpp
// lib/SemaDecl.cpp
namespace zhc {

void Sema::analyzeTranslationUnit(TranslationUnitDecl *TU) {
    // 阶段1：处理所有顶层声明（函数原型、类型定义、变量声明）
    for (Decl *D : TU->getDecls()) {
        if (auto *FD = dyn_cast<FunctionDecl>(D))
            analyzeFunctionDecl(FD);
        else if (auto *VD = dyn_cast<VarDecl>(D))
            analyzeVarDecl(VD);
        else if (auto *SD = dyn_cast<StructDecl>(D))
            analyzeStructDecl(SD);
        else if (auto *ED = dyn_cast<EnumDecl>(D))
            analyzeEnumDecl(ED);
    }

    // 阶段2：验证所有函数定义体（函数原型检查在第一阶段）
    for (Decl *D : TU->getDecls()) {
        if (auto *FD = dyn_cast<FunctionDecl>(D))
            if (FD->getBody())
                analyzeFunctionBody(FD);
    }
}

FunctionDecl *Sema::analyzeFunctionDecl(FunctionDecl *FD) {
    // 1. 检查函数名是否重复
    if (SymbolTable.lookup(FD->getName()))
        Diags.report(diag::err_redefinition, FD->getName());

    // 2. 将参数加入符号表（带初始值标记）
    for (auto *P : FD->getParams()) {
        // 参数默认已初始化
        markInitialized(P->getName());
    }

    // 3. 如果有函数体，延迟到第二阶段分析
    if (FD->getBody()) {
        // 记录下来，待 analyzeFunctionBody 处理
        PendingFunctions.push_back(FD);
    }

    // 4. 注册符号
    SymbolTable.insert(FD->getName(), Symbol::Function);

    return FD;
}

VarDecl *Sema::analyzeVarDecl(VarDecl *VD) {
    // 1. 检查是否重复声明
    if (SymbolTable.lookup(VD->getName()))
        Diags.report(diag::err_redefinition, VD->getName());

    // 2. 检查类型
    QualType T = VD->getType();
    if (T.isNull())
        T = inferType(VD->getInitializer());

    // 3. 检查初始化器类型匹配
    if (Expr *Init = VD->getInitializer()) {
        QualType InitTy = analyzeExpr(Init);
        if (!TypeContext.isCompatible(T, InitTy))
            Diags.report(diag::err_type_mismatch, T, InitTy);
        markInitialized(VD->getName());
    }

    // 4. 注册符号
    SymbolTable.insert(VD->getName(), Symbol::Variable);

    return VD;
}

} // namespace zhc
```

**参考**: Python 版本 `src/zhc/semantic/semantic_analyzer.py` 第 200-500 行

**工时**: 64h（原 40h，专家建议上调 — 需含两遍分析、属性推导、链接规格）

---

#### T2.8 表达式分析

**交付物**: `lib/SemaExpr.cpp`

> **修订说明**: 工时从 40h 调整为 64h（专家建议），需含常量折叠、LValue/RValue 区分、ODR 检查。

**操作步骤**:
1. 实现表达式语义分析：

```cpp
// lib/SemaExpr.cpp
QualType Sema::analyzeExpr(Expr *E) {
    if (auto *IL = dyn_cast<IntegerLiteral>(E)) return BuiltinType::Int32;
    if (auto *FL = dyn_cast<FloatLiteral>(E)) return BuiltinType::Float64;
    if (auto *SL = dyn_cast<StringLiteral>(E)) return PointerType(BuiltinType::Int8);
    if (auto *ID = dyn_cast<Identifier>(E)) return analyzeIdentifier(ID);
    if (auto *BO = dyn_cast<BinaryOperator>(E)) return analyzeBinaryOperator(BO);
    if (auto *UO = dyn_cast<UnaryOperator>(E)) return analyzeUnaryOperator(UO);
    if (auto *CE = dyn_cast<CallExpr>(E)) return analyzeCallExpr(CE);
    if (auto *IE = dyn_cast<IndexExpr>(E)) return analyzeIndexExpr(IE);
    if (auto *Cond = dyn_cast<ConditionalExpr>(E)) return analyzeConditionalExpr(Cond);
    return QualType();
}

QualType Sema::analyzeIdentifier(Identifier *ID) {
    Symbol *Sym = SymbolTable.lookup(ID->getName());
    if (!Sym) {
        Diags.report(diag::err_undeclared_identifier, ID->getName());
        return QualType();
    }
    markReferenced(ID->getName());
    return Sym->Type;
}

QualType Sema::analyzeBinaryOperator(BinaryOperator *BO) {
    QualType LHS = analyzeExpr(BO->getLHS());
    QualType RHS = analyzeExpr(BO->getRHS());

    switch (BO->getOp()) {
        case BO_Add: case BO_Sub: case BO_Mul: case BO_Div:
            // 算术运算类型检查
            return TypeContext.usualArithmeticConversions(LHS, RHS);
        case BO_LT: case BO_GT: case BO_LE: case BO_GE:
        case BO_EQ: case BO_NE:
            // 比较运算 → bool
            return QualType(BuiltinType::Bool);
        case BO_Assign:
            if (!TypeContext.isCompatible(LHS, RHS))
                Diags.report(diag::err_type_mismatch, LHS, RHS);
            return LHS;
        case BO_And: case BO_Or:
            return QualType(BuiltinType::Bool);
        default:
            Diags.report(diag::err_invalid_binary_op, BO->getOpName());
            return QualType();
    }
}

QualType Sema::analyzeCallExpr(CallExpr *CE) {
    Expr *Callee = CE->getCallee();
    QualType CalleeTy = analyzeExpr(Callee);

    if (!CalleeTy->isFunction()) {
        Diags.report(diag::err_call_non_function);
        return QualType();
    }

    FunctionType *FT = cast<FunctionType>(CalleeTy.getType());
    auto Params = FT->getParamTypes();
    auto Args = CE->getArgs();

    // 参数数量检查
    if (Params.size() != Args.size() && !FT->isVarArg())
        Diags.report(diag::err_argument_count_mismatch);

    // 参数类型检查
    for (size_t i = 0; i < Args.size(); ++i) {
        QualType ArgTy = analyzeExpr(Args[i]);
        if (i < Params.size() && !TypeContext.canImplicitlyConvert(Args[i], Params[i]))
            Diags.report(diag::err_argument_type_mismatch, i);
    }

    return FT->getReturnType();
}
```

**参考**: Python 版本 `src/zhc/semantic/semantic_analyzer.py` 第 500-1000 行

**工时**: 64h（原 40h，专家建议上调）

---

#### T2.9 语句分析

**交付物**: `lib/SemaStmt.cpp`

> **修订说明**: 工时从 40h 调整为 56h（专家建议），需含控制流完整性检查、case 穿越、goto 跨作用域。

**操作步骤**:
1. 实现语句语义分析：

```cpp
// lib/SemaStmt.cpp
void Sema::analyzeStmt(Stmt *S) {
    if (auto *ES = dyn_cast<ExprStmt>(S)) analyzeExpr(ES->getExpr());
    else if (auto *CS = dyn_cast<CompoundStmt>(S)) analyzeCompoundStmt(CS);
    else if (auto *IS = dyn_cast<IfStmt>(S)) analyzeIfStmt(IS);
    else if (auto *WS = dyn_cast<WhileStmt>(S)) analyzeWhileStmt(WS);
    else if (auto *FS = dyn_cast<ForStmt>(S)) analyzeForStmt(FS);
    else if (auto *RS = dyn_cast<ReturnStmt>(S)) analyzeReturnStmt(RS);
    else if (auto *SS = dyn_cast<SwitchStmt>(S)) analyzeSwitchStmt(SS);
}

void Sema::analyzeCompoundStmt(CompoundStmt *CS) {
    enterScope(ScopeKind::Block);
    for (Stmt *S : CS->getStmts())
        analyzeStmt(S);
    exitScope();
}

void Sema::analyzeIfStmt(IfStmt *IS) {
    QualType CondTy = analyzeExpr(IS->getCond());
    if (!CondTy->isScalar())
        Diags.report(diag::err_cond_not_scalar);

    analyzeStmt(IS->getThen());
    if (Stmt *Else = IS->getElse())
        analyzeStmt(Else);
}

void Sema::analyzeWhileStmt(WhileStmt *WS) {
    QualType CondTy = analyzeExpr(WS->getCond());
    analyzeStmt(WS->getBody());
}

void Sema::analyzeReturnStmt(ReturnStmt *RS) {
    QualType ExpectedRetTy = CurrentFunction->getReturnType();
    if (Expr *RetExpr = RS->getRetValue()) {
        QualType ActualTy = analyzeExpr(RetExpr);
        if (!TypeContext.isCompatible(ExpectedRetTy, ActualTy))
            Diags.report(diag::err_return_type_mismatch);
    } else {
        if (!ExpectedRetTy->isVoid())
            Diags.report(diag::err_return_value_required);
    }
}

void Sema::analyzeSwitchStmt(SwitchStmt *SS) {
    QualType SwitchTy = analyzeExpr(SS->getCondition());
    SS->setConditionType(SwitchTy);
    analyzeStmt(SS->getBody());
}
```

**工时**: 56h（原 40h，专家建议上调）

---

#### T2.9e 异常处理语义分析（P2-03）

> **来源**: 专家报告 P2-03（🔴 Critical）— Python 版已有完整 EH 实现（5 阶段全部完成）
> **优先级**: P2（语言核心特性）
> **理由**: ZhC 有 `尝试/捕获/最终/抛出` 语法，必须在语义分析阶段处理

**交付物**: `lib/SemaException.cpp`

**操作步骤**:

1. 实现异常处理的语义分析：

```cpp
// lib/SemaException.cpp
namespace zhc {

/// 分析 try/catch/finally 语句
void Sema::analyzeTryStmt(TryStmt *TS) {
    // 1. 分析 try 块
    enterScope(ScopeKind::Try);
    analyzeStmt(TS->getTryBlock());
    exitScope();

    // 2. 分析 catch 子句
    for (auto *CS : TS->getCatchClauses()) {
        enterScope(ScopeKind::Catch);
        // 检查异常类型是否已定义
        QualType CatchTy = analyzeType(CS->getExceptionType());
        if (!CatchTy->isRecordType())
            Diags.report(diag::err_catch_non_class_type);

        // 注册 catch 变量
        SymbolTable.insert(CS->getVariableName(),
                          Symbol{Symbol::Variable, CS->getVariableName(), CatchTy});

        analyzeStmt(CS->getHandlerBlock());
        exitScope();
    }

    // 3. 分析 finally 块（如果存在）
    if (Stmt *Finally = TS->getFinallyBlock()) {
        analyzeStmt(Finally);
    }
}

/// 分析 throw 语句
void Sema::analyzeThrowStmt(ThrowStmt *TS) {
    QualType ThrowTy = analyzeExpr(TS->getExpression());

    // 检查 throw 表达式类型
    if (ThrowTy->isVoid() || ThrowTy->isIncomplete())
        Diags.report(diag::err_throw_incomplete_type);

    // 记录当前函数的 throw 类型（用于异常规格检查）
    CurrentFunction->addThrowType(ThrowTy);
}

} // namespace zhc
```

2. **Python 版对照**:

| Python 功能 | C++ 对应 | 状态 |
|:---|:---|:---:|
| `exception/` 6 文件 | `SemaException.cpp` | 迁移 |
| `ExceptionType` / `ExceptionObject` | 异常类型系统 | 新增 |
| `ExceptionRegistry` | 异常注册表 | 迁移 |
| try/catch/finally 语义 | `analyzeTryStmt` | 迁移 |
| throw 语义 | `analyzeThrowStmt` | 迁移 |

**参考**: Python 版 `src/zhc/exception/` 目录（6 文件）

**工时**: 32h

---

#### T2.9g 泛型实例化语义分析（P2-02）

> **来源**: 专家报告 P2-02（泛型 G.03 迁移）
> **优先级**: P2

**交付物**: `lib/SemaGeneric.cpp`

**操作步骤**:

1. 实现泛型调用的语义分析和单态化触发：

```cpp
// lib/SemaGeneric.cpp
namespace zhc {

/// 分析泛型函数调用
QualType Sema::analyzeGenericCall(CallExpr *CE, GenericDecl *GD) {
    // 1. 从调用参数推导类型参数
    llvm::DenseMap<StringRef, QualType> DeducedTypes;
    deduceTypeArguments(GD, CE->getArguments(), DeducedTypes);

    // 2. 检查约束
    if (!Mono.checkConstraints(GD, getDeducedTypesAsArray(DeducedTypes))) {
        Diags.report(diag::err_generic_constraint_not_satisfied);
        return QualType();
    }

    // 3. 触发单态化
    Decl *Instantiated = Mono.instantiate(GD, getDeducedTypesAsArray(DeducedTypes));

    // 4. 分析实例化后的函数体（递归）
    if (auto *FD = dyn_cast<FunctionDecl>(Instantiated)) {
        analyzeFunctionBody(FD);
        return FD->getReturnType();
    }

    return QualType();
}

} // namespace zhc
```

**参考**: Python 版 `src/zhc/semantic/generics.py` 中的 Sema 集成逻辑

**工时**: 40h

---

#### T2.9p 模式匹配语义分析（P2-04，M.01-M.02 迁移）

> **来源**: 专家报告 P2-04（🟡 Major）
> **优先级**: P2（E1 语言增强）
> **理由**: Python 版已有 M.01-M.09 共 9 个阶段的完整 Pattern 实现

**交付物**: `lib/SemaPattern.cpp`

**操作步骤**:

1. 实现 Pattern 类型和语义分析：

```cpp
// lib/SemaPattern.cpp
namespace zhc {

/// Pattern 基础类型（M.01）
enum class PatternKind {
    Wildcard,       // _ （匹配任意值）
    Literal,        // 42, "hello", true
    Variable,       // x （绑定变量）
    Constructor,    // Some(x), Point{x, y}
    Tuple,          // (a, b, c)
    Range,          // 0..10
    Or,             // A | B
    Guard,          // pattern if condition
};

/// 穷举性检查（M.02）
class ExhaustivenessChecker {
public:
    /// 检查 match 表达式是否穷举
    bool isExhaustive(MatchExpr *ME);

    /// 检查是否存在冗余模式
    bool hasRedundantPatterns(MatchExpr *ME);

    /// 计算缺失的模式
    std::vector<Pattern*> getMissingPatterns(QualType MatchedType,
                                              ArrayRef<Pattern*> Existing);
};

/// 冗余检测（M.04）
class RedundancyChecker {
public:
    /// 检查模式 arm 是否不可达
    bool isUnreachable(unsigned ArmIndex, MatchExpr *ME);
};

} // namespace zhc
```

2. **Phase2 实现范围**: M.01（Pattern 类型）+ M.02（穷举/冗余检测）+ M.05（枚举 Switch 降级）
   - 其余 M.03-M.09 推迟到 Phase2.x

**参考**: Python 版 `src/zhc/semantic/pattern_matching.py`（964 行）

**工时**: 96h

---

#### T2.9s 智能指针/RAII 类型检查（P2-05）

> **来源**: 专家报告 P2-05（🟡 Major）
> **优先级**: P2（E0 安全特性的类型基础）
> **理由**: Python 版已有完整的 smart_ptr 类型系统（UniquePtr/SharedPtr/WeakPtr）

**交付物**: `lib/SemaSmartPointer.cpp`

**操作步骤**:

1. 实现智能指针类型检查：

```cpp
// lib/SemaSmartPointer.cpp
namespace zhc {

/// 检查独享指针语义（不可拷贝，仅可移动）
bool Sema::checkUniquePtrSemantics(VarDecl *VD) {
    // 1. 检查是否被拷贝（应报错）
    // 2. 检查是否被移动（允许，原指针变空）
    // 3. 检查作用域结束时自动释放
    return true;
}

/// 检查共享指针语义（引用计数）
bool Sema::checkSharedPtrSemantics(VarDecl *VD) {
    // 1. 允许拷贝（引用计数 +1）
    // 2. 允许移动
    // 3. 引用计数为 0 时自动释放
    return true;
}

/// 检查弱指针语义（不拥有，仅观察）
bool Sema::checkWeakPtrSemantics(VarDecl *VD) {
    // 1. 不增加引用计数
    // 2. lock() 返回 SharedPtr 或空
    return true;
}

/// 检查移动语义
bool Sema::checkMoveSemantics(Expr *Source, Expr *Target) {
    // 1. 移动后源对象不可使用
    // 2. 检查移动后的使用（use-after-move）
    return true;
}

} // namespace zhc
```

2. **Python 版对照**:

| Python 模块 | C++ 对应 | 行数 |
|:---|:---|:---:|
| `memory/smart_ptr.py` | SmartPtr 类型检查 | ~400 |
| `type_system/smart_ptr.py` | SmartPtr 类型检查 | ~300 |
| `memory/raii.py` | RAII 语义分析 | ~500 |

**参考**: Python 版 `src/zhc/memory/smart_ptr.py` + `src/zhc/type_system/smart_ptr.py`

**工时**: 72h

---

#### T2.10 函数重载解析

**交付物**: `include/zhc/OverloadResolver.h` + `lib/OverloadResolver.cpp`

**操作步骤**:
1. 实现 C++ 风格的重载解析：

```cpp
class OverloadResolver {
public:
    /// 解析函数重载
    FunctionDecl *resolve(
        llvm::StringRef Name,
        const llvm::SmallVectorImpl<Expr*> &Args,
        ScopeChain &Scope);

private:
    /// 计算隐式转换距离
    int conversionDistance(QualType From, QualType To);

    /// 选择最佳候选
    FunctionDecl *selectBest(
        const std::vector<FunctionDecl*> &Candidates,
        const llvm::SmallVectorImpl<Expr*> &Args);
};
```

**工时**: 20h

---

#### T2.11 逃逸分析

**交付物**: `include/zhc/EscapeAnalysis.h` + `lib/EscapeAnalysis.cpp`

**操作步骤**:
1. 实现变量逃逸分析：

```cpp
class EscapeAnalysis {
public:
    enum EscapeLevel { Local, Function, Global, Parameter };
    struct EscapeInfo {
        EscapeLevel Level;
        llvm::SmallVector<llvm::StringRef, 4> EscapePoints;
    };
    EscapeInfo analyze(const VarDecl *VD);

private:
    void visitExpr(Expr *E);
    void visitReturnStmt(ReturnStmt *RS);
    void visitCallExpr(CallExpr *CE);
};
```

**工时**: 20h

---

#### T2.12 语义分析测试

**交付物**: `test/unittests/sema_test.cpp`

**操作步骤**:
1. 覆盖以下场景：
   - 函数调用类型检查
   - 隐式类型转换
   - 未声明标识符报错
   - 重复定义报错
   - return 语句类型匹配
   - break/continue 作用域检查

**验收标准**:
```bash
ctest -R Sema --output-on-failure
```

**工时**: 40h

---

## 2.4 Month 6：LLVM IR 生成

### 任务 2.4.1 LLVM IR 生成器框架

#### T2.13 实现 LLVM IR 生成器框架

**交付物**: `include/zhc/CodeGen.h` + `lib/CodeGen.cpp`

**操作步骤**:
1. 实现 IR 生成器核心框架（参考 `11-LLVM集成方案.md`）：

```cpp
// include/zhc/CodeGen.h
class CodeGen {
public:
    CodeGen(llvm::LLVMContext &Ctx, DiagnosticsEngine &Diags,
            const TargetMachine *TM);

    /// 生成翻译单元的 IR
    std::unique_ptr<llvm::Module> codegen(TranslationUnitDecl *TU);

    /// 获取生成的模块
    llvm::Module *getModule() { return TheModule.get(); }

private:
    llvm::LLVMContext &Context;
    DiagnosticsEngine &Diags;
    std::unique_ptr<llvm::Module> TheModule;
    std::unique_ptr<IRBuilder<>> Builder;
    const TargetMachine *Target;

    /// 类型映射：ZhC Type → LLVM Type
    llvm::Type *mapType(QualType QT);

    /// 值映射：ZhC Expr → LLVM Value
    llvm::Value *mapValue(Expr *E);

    /// 符号映射：ZhC Decl → LLVM Alloca/Global
    std::unordered_map<StringRef, llvm::Value*> Locals;
    std::unordered_map<StringRef, llvm::GlobalValue*> Globals;
};
```

2. 初始化 LLVM PassManager（参考 `11-LLVM集成方案.md` 11.2 节）：

```cpp
// lib/CodeGen.cpp
CodeGen::CodeGen(LLVMContext &Ctx, DiagnosticsEngine &D,
                 const TargetMachine *TM)
    : Context(Ctx), Diags(D), Target(TM) {

    TheModule = std::make_unique<Module>("ZhC Module", Context);
    TheModule->setDataLayout(TM->createDataLayout());
    TheModule->setTargetTriple(TM->getTargetTriple().str());

    Builder = std::make_unique<IRBuilder<>>(Context);
}
```

**参考**: `11-LLVM集成方案.md` 11.2 节，`src/zhc/ir_generator.py` Python 版本

**工时**: 56h（原 40h，专家建议上调 — 需含 LLVM Module/DataLayout/TargetMachine 初始化）

---

#### T2.14 表达式 IR 生成

**交付物**: `lib/CodeGenExpr.cpp`

> **修订说明**: 工时从 40h 调整为 64h（专家建议），需含 100+ opcode 映射、SSA 构造。

**操作步骤**:
1. 实现所有表达式类型的 IR 生成：

```cpp
// lib/CodeGenExpr.cpp

llvm::Value *CodeGen::codegenExpr(Expr *E) {
    if (auto *IL = dyn_cast<IntegerLiteral>(E))
        return codegenIntegerLiteral(IL);
    if (auto *FL = dyn_cast<FloatLiteral>(E))
        return codegenFloatLiteral(FL);
    if (auto *SL = dyn_cast<StringLiteral>(E))
        return codegenStringLiteral(SL);
    if (auto *ID = dyn_cast<Identifier>(E))
        return codegenIdentifier(ID);
    if (auto *BO = dyn_cast<BinaryOperator>(E))
        return codegenBinaryOperator(BO);
    if (auto *UO = dyn_cast<UnaryOperator>(E))
        return codegenUnaryOperator(UO);
    if (auto *CE = dyn_cast<CallExpr>(E))
        return codegenCallExpr(CE);
    if (auto *IE = dyn_cast<IndexExpr>(E))
        return codegenIndexExpr(IE);
    if (auto *Cond = dyn_cast<ConditionalExpr>(E))
        return codegenConditionalExpr(Cond);
    llvm_unreachable("未实现的表达式类型");
}

llvm::Value *CodeGen::codegenBinaryOperator(BinaryOperator *BO) {
    llvm::Value *LHS = codegenExpr(BO->getLHS());
    llvm::Value *RHS = codegenExpr(BO->getRHS());

    switch (BO->getOp()) {
        case BO_Add: return Builder->CreateNSWAdd(LHS, RHS);
        case BO_Sub: return Builder->CreateNSWSub(LHS, RHS);
        case BO_Mul: return Builder->CreateNSWMul(LHS, RHS);
        case BO_Div: return Builder->CreateSDiv(LHS, RHS);  // 有符号除法
        case BO_LT:  return Builder->CreateICmpSLT(LHS, RHS);
        case BO_GT:  return Builder->CreateICmpSGT(LHS, RHS);
        case BO_EQ:  return Builder->CreateICmpEQ(LHS, RHS);
        case BO_NE:  return Builder->CreateICmpNE(LHS, RHS);
        case BO_And: return Builder->CreateAnd(LHS, RHS);
        case BO_Or:  return Builder->CreateOr(LHS, RHS);
        case BO_Assign:
            // 先 store 再返回 LHS（因为 ZhC 赋值表达式有值）
            Builder->CreateStore(RHS, mapValue(BO->getLHS()));
            return LHS;
        default:
            Diags.report(diag::err_unsupported_operator);
            return llvm::UndefValue::get(LHS->getType());
    }
}

llvm::Value *CodeGen::codegenIndexExpr(IndexExpr *IE) {
    llvm::Value *Base = codegenExpr(IE->getBase());
    llvm::Value *Idx = codegenExpr(IE->getIndex());

    // 将基指针转换为 llvm::Value* 后 gep
    auto *GEPI = Builder->CreateInBoundsGEP(
        mapType(IE->getBase()->getType()), Base, Idx);
    return Builder->CreateLoad(mapType(IE->getType()), GEPI);
}
```

**参考**: Python 版本 `src/zhc/ir_generator.py` 第 300-800 行

**工时**: 40h

---

#### T2.15 语句 IR 生成

**交付物**: `lib/CodeGenStmt.cpp`

**操作步骤**:
1. 实现所有语句类型的 IR 生成：

```cpp
// lib/CodeGenStmt.cpp

llvm::Value *CodeGen::codegenStmt(Stmt *S) {
    if (auto *ES = dyn_cast<ExprStmt>(S))
        return codegenExpr(ES->getExpr());
    if (auto *CS = dyn_cast<CompoundStmt>(S))
        return codegenCompoundStmt(CS);
    if (auto *IS = dyn_cast<IfStmt>(S))
        return codegenIfStmt(IS);
    if (auto *WS = dyn_cast<WhileStmt>(S))
        return codegenWhileStmt(WS);
    if (auto *FS = dyn_cast<ForStmt>(S))
        return codegenForStmt(FS);
    if (auto *RS = dyn_cast<ReturnStmt>(S))
        return codegenReturnStmt(RS);
    if (auto *BS = dyn_cast<BreakStmt>(S))
        return codegenBreakStmt(BS);
    if (auto *CS = dyn_cast<ContinueStmt>(S))
        return codegenContinueStmt(CS);
    if (auto *SS = dyn_cast<SwitchStmt>(S))
        return codegenSwitchStmt(SS);
    return nullptr;
}

llvm::Value *CodeGen::codegenIfStmt(IfStmt *IS) {
    llvm::Value *Cond = codegenExpr(IS->getCond());

    // 创建基本块
    llvm::Function *F = Builder->GetInsertBlock()->getParent();
    llvm::BasicBlock *ThenBB = llvm::BasicBlock::Create(Context, "if.then", F);
    llvm::BasicBlock *ElseBB = llvm::BasicBlock::Create(Context, "if.else", F);
    llvm::BasicBlock *MergeBB = llvm::BasicBlock::Create(Context, "if.end", F);

    Builder->CreateCondBr(Cond, ThenBB, ElseBB);

    // Then 块
    Builder->SetInsertPoint(ThenBB);
    codegenStmt(IS->getThen());
    Builder->CreateBr(MergeBB);

    // Else 块
    Builder->SetInsertPoint(ElseBB);
    if (Stmt *Else = IS->getElse())
        codegenStmt(Else);
    Builder->CreateBr(MergeBB);

    Builder->SetInsertPoint(MergeBB);
    return nullptr;
}

llvm::Value *CodeGen::codegenWhileStmt(WhileStmt *WS) {
    llvm::Function *F = Builder->GetInsertBlock()->getParent();
    llvm::BasicBlock *CondBB = llvm::BasicBlock::Create(Context, "while.cond", F);
    llvm::BasicBlock *BodyBB = llvm::BasicBlock::Create(Context, "while.body", F);
    llvm::BasicBlock *EndBB = llvm::BasicBlock::Create(Context, "while.end", F);

    // 保存跳转目标（用于 break/continue）
    LoopStack.push_back({CondBB, EndBB, BodyBB});

    Builder->CreateBr(CondBB);
    Builder->SetInsertPoint(CondBB);
    llvm::Value *Cond = codegenExpr(WS->getCond());
    Builder->CreateCondBr(Cond, BodyBB, EndBB);

    Builder->SetInsertPoint(BodyBB);
    codegenStmt(WS->getBody());
    Builder->CreateBr(CondBB);

    Builder->SetInsertPoint(EndBB);
    LoopStack.pop_back();
    return nullptr;
}

llvm::Value *CodeGen::codegenReturnStmt(ReturnStmt *RS) {
    if (Expr *Ret = RS->getRetValue()) {
        llvm::Value *V = codegenExpr(Ret);
        Builder->CreateRet(V);
    } else {
        Builder->CreateRetVoid();
    }
    return nullptr;
}
```

**工时**: 64h（原 40h，专家建议上调 — 需含控制流 IR、EH pad、cleanuppad）

---

#### T2.15e 异常处理 IR 生成（P2-03）

> **来源**: 专家报告 P2-03（🔴 Critical）
> **优先级**: P2（语言核心特性）
> **理由**: Python 版已有完整的 EH IR 生成（landingpad/personality/invoke/catchswitch）

**交付物**: `lib/CodeGenException.cpp`

**操作步骤**:

1. 实现异常处理的 LLVM IR 生成：

```cpp
// lib/CodeGenException.cpp
namespace zhc {

/// 生成 try/catch 的 IR
void CodeGen::codegenTryStmt(TryStmt *TS) {
    llvm::Function *F = Builder->GetInsertBlock()->getParent();

    // 1. 创建 landing pad 基本块
    llvm::BasicBlock *TryBB = llvm::BasicBlock::Create(Context, "try", F);
    llvm::BasicBlock *CatchBB = llvm::BasicBlock::Create(Context, "catch", F);
    llvm::BasicBlock *FinallyBB = llvm::BasicBlock::Create(Context, "finally", F);
    llvm::BasicBlock *ContBB = llvm::BasicBlock::Create(Context "try.cont", F);

    // 2. 在 try 块中使用 invoke（而非 call）
    Builder->CreateBr(TryBB);
    Builder->SetInsertPoint(TryBB);
    // 所有函数调用改用 invoke，指定 unwind 目标为 CatchBB
    codegenStmtWithInvoke(TS->getTryBlock(), CatchBB);
    Builder->CreateBr(FinallyBB);

    // 3. 生成 catch 块（使用 landingpad + catchswitch）
    Builder->SetInsertPoint(CatchBB);
    codegenCatchClauses(TS->getCatchClauses(), FinallyBB);

    // 4. 生成 finally 块
    Builder->SetInsertPoint(FinallyBB);
    if (TS->getFinallyBlock())
        codegenStmt(TS->getFinallyBlock());
    Builder->CreateBr(ContBB);

    Builder->SetInsertPoint(ContBB);
}

/// 生成 throw 的 IR
void CodeGen::codegenThrowStmt(ThrowStmt *TS) {
    llvm::Value *ExceptionObj = codegenExpr(TS->getExpression());

    // 调用 __zhc_throw(exception_obj)
    llvm::Function *ThrowFn = getRuntimeFunction("__zhc_throw");
    Builder->CreateCall(ThrowFn, {ExceptionObj});

    // throw 之后不可达
    Builder->CreateUnreachable();
}

} // namespace zhc
```

2. **LLVM EH 指令对照**（Python 版 → C++ 版）:

| Python llvmlite 指令 | C++ LLVM IR 指令 | 说明 |
|:---|:---|:---|
| `builder.invoke()` | `Builder->CreateInvoke()` | 带异常处理的调用 |
| `builder.landingpad()` | `Builder->CreateLandingPad()` | 异常捕获平台 |
| `builder.catchswitch()` | 常规基本块路由 | catch 分发 |
| `builder.catchret()` | `Builder->CreateCatchRet()` | catch 返回 |

**参考**: Python 版 `src/zhc/ir_generator.py` 中的 EH IR 生成逻辑

**工时**: 40h

---

#### T2.14g 泛型 IR 生成（P2-02）

> **来源**: 专家报告 P2-02（泛型 G.04-G.05 迁移）

**交付物**: `lib/CodeGenGeneric.cpp`

**操作步骤**:

1. 实现泛型实例化的 IR 生成：

```cpp
// lib/CodeGenGeneric.cpp
namespace zhc {

/// 生成单态化后的函数 IR
void CodeGen::codegenGenericFunction(FunctionDecl *FD, GenericDecl *GD,
                                      ArrayRef<QualType> TypeArgs) {
    // 1. 计算 mangled name（如 _Z4sortIiEviPT_）
    std::string MangledName = getMangledName(GD, TypeArgs);

    // 2. 创建 LLVM 函数（使用具体类型替代类型参数）
    llvm::FunctionType *FTy = mapGenericFunctionType(FD, TypeArgs);
    llvm::Function *F = llvm::Function::Create(
        FTy, llvm::Function::ExternalLinkage, MangledName, TheModule.get());

    // 3. 生成函数体 IR（类型参数已替换为具体类型）
    codegenFunctionBody(FD, F);
}

} // namespace zhc
```

**参考**: Python 版 `src/zhc/ir/ir_generator.py` 中的泛型 IR 方法 + `backend/generic_strategies.py`

**工时**: 32h

**交付物**: `lib/CodeGenFunc.cpp`

**操作步骤**:
1. 实现函数定义的 IR 生成：

```cpp
// lib/CodeGenFunc.cpp

llvm::Function *CodeGen::codegenFunction(FunctionDecl *FD) {
    // 1. 映射函数类型
    llvm::FunctionType *FTy = cast<llvm::FunctionType>(
        mapType(QualType(FD->getType())));

    // 2. 创建函数
    llvm::Function *F = llvm::Function::Create(
        FTy, llvm::Function::ExternalLinkage,
        FD->getName(), TheModule.get());

    // 3. 设置参数名称
    unsigned i = 0;
    for (auto &Arg : F->args())
        Arg.setName(FD->getParam(i++)->getName());

    // 4. 创建入口基本块
    llvm::BasicBlock *EntryBB = llvm::BasicBlock::Create(Context, "entry", F);
    Builder->SetInsertPoint(EntryBB);

    // 5. 将实参绑定到 alloca
    unsigned ArgIdx = 0;
    for (auto &Arg : F->args()) {
        llvm::AllocaInst *Alloca = Builder->CreateAlloca(
            Arg.getType(), nullptr, Arg.getName());
        Builder->CreateStore(&Arg, Alloca);
        Locals[Arg.getName()] = Alloca;
        ArgIdx++;
    }

    // 6. 设置当前函数上下文
    CurrentFunction = FD;

    // 7. 生成函数体
    if (CompoundStmt *Body = FD->getBody())
        codegenCompoundStmt(Body);

    // 8. 如果没有显式 return，添加隐式 return void
    if (FD->getReturnType()->isVoid() &&
        Builder->GetInsertBlock()->getTerminator() == nullptr)
        Builder->CreateRetVoid();

    // 9. 验证函数 IR
    llvm::verifyFunction(*F);

    CurrentFunction = nullptr;
    return F;
}

llvm::Value *CodeGen::codegenIdentifier(Identifier *ID) {
    StringRef Name = ID->getName();

    if (llvm::Value *V = Locals.lookup(Name))
        return Builder->CreateLoad(V->getType()->getPointerElementType(), V, Name);

    if (llvm::GlobalValue *GV = Globals.lookup(Name))
        return GV;

    llvm::Function *F = TheModule->getFunction(Name);
    if (F) {
        Globals[Name] = F;
        return F;
    }

    Diags.report(diag::err_undeclared_identifier, Name);
    return llvm::UndefValue::get(Builder->getInt32Ty());
}
```

**工时**: 56h（原 40h，专家建议上调 — 需含调用约定、ABI 对齐、vararg）

**交付物**: `include/zhc/DebugInfo.h` + `lib/DebugInfo.cpp`

**操作步骤**:
1. 实现 DWARF v5 调试信息（参考 `11-LLVM集成方案.md` 11.6-11.7 节）：

```cpp
// include/zhc/DebugInfo.h
class DWARFGenerator {
public:
    DWARFGenerator(llvm::Module *M, SourceManager &SM);

    /// 为翻译单元生成调试信息
    void emitCompilationUnit(TranslationUnitDecl *TU);

    /// 为函数生成调试信息
    void emitFunction(FunctionDecl *FD, llvm::Function *IRFunc);

    /// 为变量生成调试信息
    void emitVariable(VarDecl *VD, llvm::Value *IRValue);

    /// 生成行号表
    void emitLineTable(const SourceManager &SM);

private:
    llvm::Module *TheModule;
    SourceManager &SM;
    llvm::DwarfDebug *DwarfDebug;  // LLVM 的 DWARF 生成辅助
    llvm::DIScope *CU;             // 编译单元
};
```

**参考**: `11-LLVM集成方案.md` 11.6 节，Clang `lib/CodeGen/CGDebugInfo.cpp`

**工时**: 96h（原 80h，专家建议上调 — DWARF v5 非常复杂，Clang CGDebugInfo.cpp 有 4000+ 行）

---

#### T2.18 LLD 链接器集成

> **修订说明**: 专家报告建议将 LLD 移至 Phase3（P3-4），但保持当前位置以便灵活安排。Phase2 验收标准（能编译运行 fibonacci）实际上只需系统 `cc/ld` 即可。

**交付物**: `include/zhc/Linker.h` + `lib/Linker.cpp`

**操作步骤**:
1. 实现 LLD 链接器封装：

```cpp
// include/zhh/Linker.h
class Linker {
public:
    Linker();

    void addInputFile(llvm::StringRef Path);
    void addObjectFile(llvm::MemoryBufferRef Obj);

    struct Options {
        llvm::Triple TargetTriple;
        llvm::StringRef OutputPath;
        llvm::StringRef EntrySymbol = "_main";
        bool StripDebug = false;
        bool LTO = false;
        bool WholeProgram = false;
        llvm::SmallVector<StringRef, 8> LibraryPaths;
        llvm::SmallVector<StringRef, 8> Libraries;
    };

    bool link(const Options &Opts, raw_ostream &DiagOutput);

private:
    std::vector<std::string> InputFiles;
    std::vector<llvm::MemoryBufferRef> ObjectFiles;
};
```

2. 支持的链接目标：
   - macOS: Mach-O (`ld64.lld`)
   - Linux: ELF (`ld.lld`)
   - Windows: COFF (`lld-link`)
   - WebAssembly: WASM (`wasm-ld`)

**参考**: `11-LLVM集成方案.md` 11.5 节

**工时**: 60h

---

### 任务 2.4.3 E0 安全特性（编译期检查）

#### T2.19 实现空指针安全（S01, S07）

**交付物**: `?空型<T>` 类型系统 + 强制空检查

**操作步骤**:
1. 在 `Types.h` 中，`NullableType` 已于 T2.1 实现
2. 在 `TypeChecker.cpp` 中实现空解引用检查：

```cpp
// lib/TypeChecker.cpp

// 对可空指针的解引用检查
QualType TypeChecker::checkNullableDeref(Expr *E, QualType T) {
    if (auto *NT = dyn_cast<NullableType>(T.getType())) {
        // 直接对 ?空型 解引用 → 错误
        Diags.report(diag::err_nullable_deref,
            "可空类型必须先检查空状态");
        return QualType();
    }
    return T;
}

// 调用返回 ?空型 的函数时
QualType TypeChecker::checkNullableCall(CallExpr *CE) {
    QualType RetTy = checkCallExpr(CE, ...);
    if (auto *NT = dyn_cast<NullableType>(RetTy.getType())) {
        // 调用方必须处理空返回值
        Diags.report(diag::err_unhandled_nullable,
            "函数 '{0}' 返回可空类型 '{1}'，调用处必须处理空情况",
            CE->getCalleeName(), RetTy);
    }
    return RetTy;
}
```

3. 在 `?` 语法糖处理中（`ParserExpr.cpp`）：
   - `nullable_ptr ?` 展开为 `if (ptr == 空指针) return ...`
   - Sema 验证展开后的控制流

**参考**: `18-超越C的增强特性.md` 18.2.1 节和 18.2.7 节

**工时**: 80h（S01 + S07）

---

#### T2.20 实现数组边界检查（S03）

**交付物**: 边界断言 IR 生成

**操作步骤**:
1. 在 `CodeGenExpr.cpp` 的 `codegenIndexExpr` 中添加边界检查：

```cpp
// lib/CodeGenExpr.cpp
llvm::Value *CodeGen::codegenIndexExpr(IndexExpr *IE) {
    llvm::Value *Base = codegenExpr(IE->getBase());
    llvm::Value *Idx = codegenExpr(IE->getIndex());

    // 获取数组大小（如果已知）
    QualType BaseTy = IE->getBase()->getType();
    if (auto *AT = dyn_cast<ArrayType>(BaseTy.getType())) {
        if (AT->hasKnownSize()) {
            uint64_t Size = AT->getSize();
            // 静态检查：编译期越界报错
            if (auto *CI = dyn_cast<IntegerLiteral>(IE->getIndex())) {
                if (CI->getValue() >= Size)
                    Diags.report(diag::err_array_out_of_bounds,
                        CI->getValue(), Size);
            }
            // 动态检查：生成运行时断言
            llvm::Value *SizeV = llvm::ConstantInt::get(
                Idx->getType(), Size);
            llvm::Value *Cmp = Builder->CreateICmpUGE(Idx, SizeV);
            llvm::Function *AssertFn = getBoundsCheckFunction();
            Builder->CreateCall(AssertFn, {Cmp,
                Builder->CreateLoad(Builder->getInt32Ty(),
                    getLocationValue(IE))});
        }
    }

    // GEP + Load
    auto *GEPI = Builder->CreateInBoundsGEP(
        mapType(BaseTy), Base, Idx);
    return Builder->CreateLoad(
        mapType(IE->getType()), GEPI);
}
```

**参考**: `18-超越C的增强特性.md` 18.2.3 节

**工时**: 48h（S03）

---

#### T2.21 实现整数溢出检测（S04）

**交付物**: 溢出检查 IR 生成

**操作步骤**:
1. 在 `CodeGenExpr.cpp` 的算术运算中注入溢出检查：

```cpp
// lib/CodeGenExpr.cpp

llvm::Value *CodeGen::codegenBinaryOperator(BinaryOperator *BO) {
    llvm::Value *LHS = codegenExpr(BO->getLHS());
    llvm::Value *RHS = codegenExpr(BO->getRHS());

    switch (BO->getOp()) {
        case BO_Add: {
            if (OverflowMode == OverflowMode::Check) {
                auto *I = Builder->CreateNSWAdd(LHS, RHS);
                I->setHasNoSignedWrap(false);
                // 注入溢出检测
                llvm::Value *Overflow = Builder->CreateCall(
                    getOverflowCheckIntrinsic("add.with.overflow",
                        LHS->getType()), {LHS, RHS});
                Builder->CreateCondBr(
                    Builder->CreateExtractValue(Overflow, 1),
                    createOverflowTrapBB(),  // 溢出陷阱
                    getNextBB());
                return Builder->CreateExtractValue(Overflow, 0);
            }
            return Builder->CreateNSWAdd(LHS, RHS);
        }
        case BO_Sub: {
            if (OverflowMode == OverflowMode::Check) {
                auto *I = Builder->CreateNSWSub(LHS, RHS);
                llvm::Value *Overflow = Builder->CreateCall(
                    getOverflowCheckIntrinsic("sub.with.overflow",
                        LHS->getType()), {LHS, RHS});
                // ... 类似 Add
            }
            return Builder->CreateNSWSub(LHS, RHS);
        }
        // ... Mul, Div 同理
    }
}
```

2. 支持编译选项：`--overflow=wrap`（补码环绕）、`--overflow=saturate`（饱和）、`--overflow=panic`（默认，检测）

**参考**: `18-超越C的增强特性.md` 18.2.4 节

**工时**: 32h（S04）

---

#### T2.22 实现释放后使用和悬垂指针检测（S05, S06）

**交付物**: 生命周期分析 + RAII

**操作步骤**:
1. 实现生命周期分析（在 `SemaStmt.cpp` 中）：

```cpp
// lib/SemaStmt.cpp

// 跟踪指针生命周期
struct LifetimeInfo {
    QualType PointeeType;
    bool IsAllocated = false;    // 是否已分配
    bool IsReturned = false;     // 是否被返回
    bool IsFreed = false;        // 是否已释放
    SourceLocation AllocLoc;      // 分配位置
};

std::unordered_map<StringRef, LifetimeInfo> PointerLifetimes;

void Sema::analyzeAllocation(CallExpr *CE) {
    // 申请内存() 调用
    StringRef Name = CE->getCalleeName();
    if (Name == "申请内存" || Name == "malloc") {
        StringRef Var = getAssignedVariable(CE);
        if (!Var.empty()) {
            PointerLifetimes[Var].IsAllocated = true;
            PointerLifetimes[Var].AllocLoc = CE->getLocation();
        }
    }
}

void Sema::analyzeFree(CallExpr *CE) {
    // 释放内存() 调用
    if (CE->getCalleeName() == "释放内存") {
        StringRef Var = getFreedPointer(CE);
        if (!Var.empty()) {
            PointerLifetimes[Var].IsFreed = true;
            // 检查释放后是否还有使用
            checkUseAfterFree(Var);
        }
    }
}

void Sema::analyzeReturn(ReturnStmt *RS) {
    if (Expr *Ret = RS->getRetValue()) {
        // 检查返回指针是否来自堆分配
        StringRef Ptr = getReturnedPointer(Ret);
        if (!Ptr.empty()) {
            if (!PointerLifetimes[Ptr].IsAllocated) {
                Diags.report(diag::err_dangling_return,
                    "返回了非堆分配的局部变量指针");
            }
        }
    }
}
```

**参考**: `18-超越C的增强特性.md` 18.2.5 和 18.2.6 节

**工时**: 104h（S05=40h + S06=64h）

---

#### T2.23 实现穷举 switch（S08）

**交付物**: 穷举检查 Sema Pass

**操作步骤**:
1. 在 `SemaStmt.cpp` 中实现穷举检查：

```cpp
// lib/SemaStmt.cpp

void Sema::analyzeSwitchStmt(SwitchStmt *SS) {
    QualType SwitchTy = analyzeExpr(SS->getCondition());

    // 获取枚举的所有成员
    std::vector<Identifier*> CoveredCases;
    std::vector<Identifier*> AllEnums;

    if (auto *ET = dyn_cast<EnumType>(SwitchTy.getType())) {
        // 枚举 switch：获取所有枚举值
        EnumDecl *ED = ET->getDecl();
        for (auto *EC : ED->getEnumerators())
            AllEnums.push_back(EC->getName());

        // 检查覆盖情况
        for (auto *C : SS->getCases()) {
            if (auto *CI = dyn_cast<CaseInfo>(C)) {
                Identifier *CaseName = CI->getValue();
                if (std::find(CoveredCases.begin(), CoveredCases.end(), CaseName)
                        == CoveredCases.end())
                    CoveredCases.push_back(CaseName);
            }
        }

        // 检查是否穷举（无 default 且不完整）
        bool HasDefault = SS->hasDefaultCase();
        bool IsComplete = (CoveredCases.size() == AllEnums.size());

        if (!HasDefault && !IsComplete) {
            std::vector<Identifier*> Missing;
            for (auto *E : AllEnums)
                if (std::find(CoveredCases.begin(), CoveredCases.end(), E)
                        == CoveredCases.end())
                    Missing.push_back(E);

            Diags.report(diag::warn_non_exhaustive_switch,
                "选择 语句未穷举，缺少: " + joinNames(Missing));
        }
    }
}
```

**参考**: `18-超越C的增强特性.md` 18.3.1 节

**工时**: 24h（S08）

---

#### T2.24 实现 Result 类型（S09）

**交付物**: `结果型<T, E>` 类型系统 + 匹配表达式

**操作步骤**:
1. 实现 `结果型` 类型：

```cpp
// include/zhc/Types.h

// 结果型 Result<T, E>（E1 安全特性 S09）
class ResultType : public Type {
public:
    static bool classof(const Type *T) { return T->getKind() == TypeKind::Result; }
    ResultType(QualType OkTy, QualType ErrTy)
        : Type(TypeKind::Result), OkType(OkTy), ErrType(ErrTy) {}
    QualType getOkType() const { return OkType; }
    QualType getErrType() const { return ErrType; }
private:
    QualType OkType;
    QualType ErrType;
};
```

2. 实现匹配表达式：
```cpp
// 匹配表达式：匹配 r { 情况 正常(值): ... 情况 错误(原因): ... }
Expr *Parser::parseMatchExpr() {
    expect(KW_MATCH);  // `匹配`
    Expr *Cond = parseExpression();
    expect(KK_LBRACE);
    std::vector<MatchArm*> Arms;
    while (!Tok.is(KK_RBRACE)) {
        expect(KW_CASE_NORMAL);  // `情况 正常`
        Pattern *P = parsePattern();
        expect(KK_COLON);
        Stmt *Body = parseStatement();
        Arms.push_back(new MatchArm(P, Body));
    }
    expect(KK_RBRACE);
    return new MatchExpr(Cond, Arms);
}
```

**参考**: `18-超越C的增强特性.md` 18.3.2 节

**工时**: 40h（S09）

---

#### T2.25 实现格式化安全检查（S11）

**交付物**: 格式化检查 Sema Pass

**操作步骤**:
1. 在 `SemaExpr.cpp` 中实现：

```cpp
// lib/SemaExpr.cpp

void Sema::analyzePrintCall(CallExpr *CE) {
    // 检查 打印("...", args...) 的格式串匹配
    auto Args = CE->getArgs();
    if (Args.empty()) return;

    StringLiteral *Format = dyn_cast<StringLiteral>(Args[0]);
    if (!Format) return;

    StringRef Fmt = Format->getValue();
    unsigned ExpectedArgs = countPlaceholders(Fmt);  // 统计 {}
    unsigned ActualArgs = Args.size() - 1;

    if (ExpectedArgs != ActualArgs)
        Diags.report(diag::err_format_arg_count_mismatch,
            ExpectedArgs, ActualArgs);

    // 检查每个占位符的类型
    for (unsigned i = 1; i < Args.size(); ++i) {
        QualType ArgTy = analyzeExpr(Args[i]);
        if (!isFormatCompatible(ArgTy, getPlaceholderType(Fmt, i)))
            Diags.report(diag::err_format_type_mismatch, i);
    }
}
```

**参考**: `18-超越C的增强特性.md` 18.3.4 节

**工时**: 24h（S11）

---

## 2.5 Month 6 末：端到端测试

### 任务 2.5.1 端到端测试

#### T2.26 编译运行测试程序

**交付物**: `test/integration/codegen_test.cpp`

**操作步骤**:
1. 创建 fixture 测试程序：
   - `hello.zhc`：标准输出
   - `fibonacci_recursive.zhc`：递归函数
   - `array_bounds.zhc`：数组边界测试
   - `switch_exhaustive.zhc`：穷举 switch
   - `nullable_ptr.zhc`：空指针安全
   - `overflow.zhc`：溢出检测

2. 测试流程：
```cpp
TEST_F(CodeGenIntegration, FibonacciRecursive) {
    // 1. 解析
    auto TU = parseFile("fibonacci.zhc");
    // 2. 语义分析
    Sema.Analyze(TU);
    // 3. IR 生成
    auto Mod = CG.codegen(TU.get());
    // 4. 验证 IR
    EXPECT_TRUE(verifyModule(*Mod));
    // 5. 目标文件生成
    CG.emitObjectFile("fibonacci.o");
    // 6. 链接并运行
    linkAndRun("fibonacci.o", expected_output);
}
```

**验收标准**:
```bash
# 能编译运行 fibonacci（递归）
zhc compile test/fixtures/fibonacci.zhc -o fibonacci
./fibonacci
# 输出: 0 1 1 2 3 5 8 13 21 34

# 调试信息可用
zhc compile test/fixtures/fibonacci.zhc -g -o fibonacci
lldb fibonacci
(lldb) break set --name fibonacci
(lldb) run
# lldb 断点命中
```

**工时**: 40h

---

## 2.6 Phase 2 Go/No-Go 检查点

| 检查项 | 验收命令 | 通过标准 |
|:---|:---|:---|
| **编译通过** | `ninja -C cpp/build` | 无编译错误 |
| **符号表测试** | `ctest -R Symbol` | 全部通过 |
| **类型检查测试** | `ctest -R Type` | 全部通过 |
| **Sema 测试** | `ctest -R Sema` | 全部通过 |
| **IR 生成测试** | `ctest -R CodeGen` | 全部通过 |
| **fibonacci 递归** | `zhc compile fibonacci.zhc && ./fibonacci` | 输出正确 |
| **DWARF 调试** | `lldb fibonacci` 可断点 | lldb 能调试 |
| **E0 边界检查** | `arr[100] = 0;` (数组 10) | 编译错误 |
| **E0 溢出检测** | `x = INT_MAX + 1` | 编译警告 |
| **E1 穷举 switch** | 枚举 switch 漏分支 | 编译警告 |
| **泛型测试** | `ctest -R Generic` | 全部通过（核心用例） |
| **EH 测试** | `ctest -R Exception` | try/catch/finally 正确 |
| **Pattern 测试** | `ctest -R Pattern` | 穷举检查正确 |
| **SmartPtr 测试** | `ctest -R SmartPtr` | 类型检查正确 |

**量化标准**：
- 能编译运行 fibonacci（递归版本）
- lldb 可调试
- E0 安全特性全部可触发
- 泛型核心用例通过（对应 Python 版 177 个测试中的核心 35 个）
- 异常处理 try/catch/finally 语义正确
- 模式匹配穷举检查正确

**如未通过**：
- 停 2 周修 CodeGen Bug
- 必要时加人工 Code Review

---

## 2.7 技术债务清理记录

| 债务 ID | 清理项 | 清理方式 |
|:---|:---|:---|
| **A-03** | 闭包类型推导崩溃 | 两阶段语义分析 |
| **A-04** | 泛型实例化内存泄漏 | C++ unique_ptr/shared_ptr |
| **A-06** | 异常处理 IR 不完整 | 参考 Clang EH IR + LLVM landingpad |
| **B-03** | 符号表不支持向前引用 | 两遍语义分析 |
| **B-04** | const 传播不完整 | LLVM GVN Pass 自动处理 |

---

## 2.8 参考资料

| 资料 | 路径 | 用途 |
|:---|:---|:---|
| Python IR Generator | `src/zhc/ir_generator.py` | IR 生成逻辑参考 |
| Python Type Checker | `src/zhc/type_system/` | 类型检查逻辑参考 |
| Python Sema | `src/zhc/semantic/semantic_analyzer.py` | 语义分析参考 |
| Python Pattern | `src/zhc/semantic/pattern_analyzer.py` | 穷举检查参考（Python 已有实现） |
| Python Bounds | `src/zhc/type_system/array_checker.py` | 边界检查参考（Python 已有实现） |
| LLVM 文档 | `docs/LLVM集成方案.md` | LLVM API 参考 |
| Clang CGDebugInfo | LLVM 源码 `lib/CodeGen/CGDebugInfo.cpp` | DWARF 生成参考 |
| Clang CGException | LLVM 源码 `lib/CodeGen/CGException.cpp` | EH IR 参考 |

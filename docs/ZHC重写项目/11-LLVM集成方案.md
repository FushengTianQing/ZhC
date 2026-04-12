# 第十一章：LLVM 集成方案

**版本**: v2.0 | **日期**: 2026-04-12

---

## 11.1 集成架构

```
ZhC 编译器
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│                    ZhC 前端 (C++)                          │
│  Lexer → Parser → AST → Sema → CodeGen                   │
└──────────────────────┬────────────────────────────────────┘
                       │ LLVM C++ API
                       ▼
              llvm::Module (内存中)
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLVM Core (LLVM 18)                      │
│                                                             │
│  PassManager → New PassManager → 优化 Pass                  │
│    ├─ ScalarOpts     → instcombine, gvn, dce...           │
│    ├─ Vectorize      → loop-vectorize, slp-vectorize       │
│    ├─ IPO           → inline, mergefunc, globalopt         │
│    └─ LTO           → link-time optimization               │
│                                                             │
│  TargetMachine → x86_64 / ARM64 / RISC-V / WASM...        │
│    └─ CodeGen → ISel → RA → Sched → MCInst → .o          │
└──────────────────────┬────────────────────────────────────┘
                       │
                       ▼
              LLD 链接器
                       │
                       ▼
              可执行文件 / 共享库
```

---

## 11.2 关键集成点

```cpp
// 使用 LLVM C++ API 生成 LLVM IR
#include "llvm/IR/LLVMContext.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/Verifier.h"
#include "llvm/IR/PassManager.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Target/TargetMachine.h"

// 优化 Pass 管道
llvm::PassBuilder PB;
llvm::LoopAnalysisManager LAM;
llvm::FunctionAnalysisManager FAM;
llvm::CGSCCAnalysisManager CGAM;
llvm::ModuleAnalysisManager MAM;

PB.registerModuleAnalyses(MAM);
PB.registerCGSCCAnalyses(CGAM);
PB.registerFunctionAnalyses(FAM);
PB.registerLoopAnalyses(LAM);
PB.crossRegisterProxies(LAM, FAM, CGAM, MAM);

// 构建优化管道
llvm::ModulePassManager MPM = 
    PB.buildPerModuleDefaultPipeline(llvm::OptimizationLevel::O2);

// 执行优化
MPM.run(*TheModule, MAM);

// 目标代码生成
std::unique_ptr<llvm::TargetMachine> TM = 
    Target->createTargetMachine(Triple, CPU, Features, Options);

llvm::legacy::PassManager CodeGenPasses;
TM->addPassesToEmitFile(CodeGenPasses, Out, nullptr,
    llvm::CGFT_ObjectFile);
CodeGenPasses.run(*TheModule);
```

---

## 11.3 目标后端覆盖（60+ LLVM Target）

| 类别 | 目标平台 |
|:---|:---|
| **主流桌面** | X86, X86_64, ARM, AArch64 |
| **嵌入式** | ARM (Thumb), MIPS, PowerPC, RISC-V |
| **移动** | ARM64, AArch64, iOS (arm64-apple-ios) |
| **GPU** | NVPTX (CUDA), AMDGPU (ROCm) |
| **Web** | WebAssembly (wasm32-unknown-unknown) |
| **专用** | Hexagon, SystemZ, Lanai, MSP430, SPARC, VE |

---

## 11.4 与 LLVM 生态的协作方式

| 协作方式 | 说明 |
|:---|:---|
| **作为 LLVM 子项目** | 提交到 llvm-project，成为官方前端之一 |
| **独立仓库** | 独立维护，通过 LLVM API 版本兼容 |
| **教育项目** | 不提交到 LLVM 官方，保持独立发展 |


---

## 11.5 LLD 链接器集成详解

### 11.5.1 LLD 支持的目标格式

| 目标格式 | 平台 | 支持状态 |
|:---|:---|:---:|
| **ELF** | Linux, FreeBSD, Android | ✅ 完全支持 |
| **COFF** | Windows | ✅ 完全支持 |
| **Mach-O** | macOS, iOS | ✅ 完全支持 |
| **WebAssembly** | WASI | ✅ 完全支持 |
| **MinGW** | Windows (GCC 兼容) | ⚠️ 部分支持 |

### 11.5.2 LLD 核心功能

```cpp
// LLD 集成关键功能
class LinkerIntegration {
public:
    // 链接选项
    struct LinkOptions {
        llvm::Triple Target;
        llvm::StringRef OutputPath;
        llvm::StringRef Entry = "_main";
        bool StripDebug = false;
        bool LTO = false;           // 链接时优化
        bool WholeProgram = false;  // 全程序优化
        bool Pic = true;             // 位置无关代码
        bool Shared = false;         // 共享库
        llvm::SmallVector<StringRef, 8> LibraryPaths;
        llvm::SmallVector<StringRef, 8> Libraries;
        llvm::SmallVector<StringRef, 8> Undefined;
    };
    
    // 主要链接功能
    bool link(LinkOptions Opts);
    
    // LTO 链接
    bool linkWithLTO(LinkOptions Opts);
    
    // 薄 LTO（ThinLTO）
    bool linkWithThinLTO(LinkOptions Opts);
};
```

---

## 11.6 调试信息生成详解

### 11.6.1 DWARF 版本支持

| 版本 | 特性 | ZhC 支持 |
|:---|:---|:---:|
| **DWARF 2** | 基础调试信息 | ✅ |
| **DWARF 3** | 完整类型引用 | ✅ |
| **DWARF 4** | 压缩重定位 | ⚠️ 基础 |
| **DWARF 5** | UTF-8、分组引用、改进的位置描述 | 🆕 目标 |

### 11.6.2 DWARF 5 新特性实现

```cpp
// DWARF 5 关键特性实现

class DWARF5Generator {
public:
    // UTF-8 字符串支持 (DW_FORM_strx)
    void emitString(const std::string &Str);
    
    // 分组引用 (DW_FORM_addrx)
    void emitAddressIndex(uint32_t AddrIndex);
    
    // 整数范围编码 (DW_FORM_loclistx)
    void emitLocationList(uint8_t *Data, size_t Size);
    
    // 非续体字符串 (DW_FORM_line_strp)
    void emitLineString(uint32_t Offset);
    
    // 调试宏 (DWARF 5 新增)
    void emitMacroTable(const MacroTable &Macros);
    
    // 调试属性 (DWARF 5 新增)
    void emitDebugNames(const NameTable &Names);
    void emitDebugCuIndex(const CompileUnitIndex &Index);
};
```

### 11.6.3 变量位置描述

| 操作码 | 说明 | 示例 |
|:---|:---|:---|
| `DW_OP_addr` | 绝对地址 | `DW_OP_addr(0x400800)` |
| `DW_OP_fbreg` | 帧基址相对 | `DW_OP_fbreg(-8)` |
| `DW_OP_breg0-31` | 寄存器相对 | `DW_OP_breg6(0)` |
| `DW_OP_deref` | 解引用 | `DW_OP_deref` |
| `DW_OP_plus` | 加法 | `DW_OP_plus` |
| `DW_OP_consts` | 常量 | `DW_OP_consts(5)` |

---

## 11.7 PassManager 优化管道详解

### 11.7.1 优化级别对应管道

| 级别 | 优化 Pass | 适用场景 |
|:---|:---|:---|
| **-O0** | 无 | 调试模式 |
| **-O1** | 基础优化 | 快速编译 |
| **-O2** | 标准优化 | 发布版本（默认） |
| **-O3** | 激进优化 | 极致性能 |
| **-Os** | 大小优化 | 嵌入式 |
| **-Oz** | 最小化 | 资源受限 |

### 11.7.2 主要优化 Pass 分类

```cpp
// 标量优化
PM.addPass(InstCombinePass());        // 指令合并
PM.addPass(GVNPass());                // 全局值编号
PM.addPass(SCCPPass());              // 稀疏条件常量传播
PM.addPass(DCEPass());               // 死代码消除
PM.addPass(ADCEPass());              // 激进死代码消除
PM.addPass(SROAPass("sroa"));         // 标量替换聚合变量

// 循环优化
PM.addPass(LoopRotatePass());         // 循环旋转
PM.addPass(LoopUnrollPass());         // 循环展开
PM.addPass(LoopVectorizePass());     // 循环向量化
PM.addPass(LICMPass());              // 循环不变量外提

// 过程间优化
PM.addPass(AlwaysInlinePass());       // 强制内联
PM.addPass(MergeFunctionsPass());    // 函数合并
PM.addPass(GlobalDCEPass());         // 全局死代码消除
```

---

## 11.8 JIT 编译集成

### 11.8.1 ORC JIT 核心功能

| 功能 | 说明 | 状态 |
|:---|:---|:---:|
| **惰性编译** | 按需编译函数 | ✅ |
| **远程 JIT** | 跨进程编译 | ✅ |
| **自定义目标** | 自定义执行引擎 | ✅ |
| **符号解析** | 运行时符号绑定 | ✅ |
| **内存管理** | 编译结果缓存 | ✅ |

### 11.8.2 ORC JIT 使用示例

```cpp
// ORC JIT 编译
#include <llvm/ExecutionEngine/Orc/OrcEPC.h>
#include <llvm/ExecutionEngine/Orc/ThreadSafeModule.h>

class JITCompiler {
public:
    // 初始化 JIT
    llvm::Expected<std::unique_ptr<JITCompiler>> Create();
    
    // 添加模块
    llvm::Error addModule(llvm::ThreadSafeModule TSM);
    
    // 查找符号
    llvm::Expected<llvm::JITEvaluatedSymbol> lookup(llvm::StringRef Name);
    
    // 执行函数
    template<typename FuncTy>
    auto execute(llvm::StringRef Name, auto... Args) {
        auto Sym = lookup(Name);
        auto *Func = (FuncTy*)Sym->getAddress();
        return Func(Args...);
    }
};
```

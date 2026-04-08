# ZHC 编译器架构设计文档

**版本**: v10.0  
**更新日期**: 2026-04-08  
**架构师**: 远

---

## 编译流水线架构图

```mermaid
flowchart TB
    subgraph 输入
        A[.zhc 源文件]
    end

    subgraph 词法分析
        B[Lexer<br/>Token 分词]
    end

    subgraph 语法分析
        C[Parser<br/>AST 构建]
    end

    subgraph 语义分析
        D[SemanticAnalyzer<br/>类型检查 + 作用域]
    end

    subgraph IR 生成
        E[IRGenerator<br/>AST → IR]
    end

    subgraph 优化
        F[IROptimizer<br/>常量折叠 + DCE]
    end

    subgraph 代码生成
        G[CBackend<br/>IR → C]
    end

    subgraph 输出
        H[.c 文件]
        I[可执行文件]
    end

    A --> B --> C --> D --> E --> F --> G
    G --> H
    H --> I

    style A fill:#e1f5fe
    style H fill:#c8e6c9
    style I fill:#a5d6a7
```

### 阶段详细说明

| 阶段 | 组件 | 输入 | 输出 | 主要功能 |
|:-----|:-----|:-----|:-----|:---------|
| 词法分析 | Lexer | 源代码 | Token 序列 | 识别关键字、标识符、运算符 |
| 语法分析 | Parser | Token 序列 | AST | 构建抽象语法树 |
| 语义分析 | SemanticAnalyzer | AST | 带类型的 AST | 类型检查、作用域分析、符号解析 |
| IR 生成 | IRGenerator | AST | ZHC IR | 生成中间表示 |
| 优化 | IROptimizer | ZHC IR | 优化后的 IR | 常量折叠、死代码消除 |
| 代码生成 | CBackend | IR | C 代码 | 生成目标代码 |

---

## 一、架构概述

ZHC（中文C编译器）采用模块化架构设计，将编译过程分解为多个独立的子模块，每个模块负责特定的功能领域。

### 设计原则

1. **单一职责**：每个子模块只负责一个明确的功能领域
2. **松耦合**：模块间通过明确的接口通信，降低依赖关系
3. **高内聚**：相关功能集中在一个模块内
4. **可扩展**：易于添加新功能或替换现有实现
5. **可测试**：每个模块都可以独立测试

---

## 二、目录结构

```
src/
├── __init__.py              # 包入口，导出公共API
├── __main__.py              # CLI入口点
├── cli.py                   # 主命令行接口
├── cli_parser.py            # CLI 参数解析器
├── config.py                # 配置管理
├── keywords.py              # 中文关键词映射表
│
├── parser/                  # 解析器模块 (14 files)
│   ├── module.py           # 模块语法解析
│   ├── class_.py           # 类语法解析
│   ├── class_extended.py   # 扩展类解析器
│   ├── memory.py           # 内存语法解析
│   ├── scope.py            # 作用域管理
│   └── smart_pointer.py    # 智能指针解析
│
├── semantic/                # 语义分析模块 (13 files)
│   ├── semantic_analyzer.py    # 主语义分析器 (84KB)
│   ├── symbol_table_optimized.py # 优化的符号表
│   ├── type_utils.py           # 类型工具
│   ├── generics.py             # 泛型语义分析
│   ├── generic_parser.py       # 泛型解析
│   ├── generic_instantiator.py # 泛型实例化
│   ├── pattern_matching.py     # 模式匹配
│   ├── pattern_parser.py       # 模式解析
│   ├── pattern_analyzer.py     # 模式分析
│   ├── cfg_analyzer.py         # CFG 分析
│   ├── async_system.py         # 异步系统
│   └── async_parser.py         # 异步解析
│
├── ir/                      # IR 中间表示模块 (22 files)
│   ├── [核心 IR]
│   ├── symbol.py, types.py, opcodes.py, values.py
│   ├── instructions.py, program.py, printer.py
│   ├── ir_generator.py, ir_verifier.py, optimizer.py
│   ├── mappings.py, c_backend.py, llvm_backend.py
│   ├── [优化器]
│   ├── dataflow.py, dominator.py, ssa.py
│   ├── inline_optimizer.py, loop_optimizer.py, loop_unroller.py
│   ├── optimization_hints.py, register_allocator.py
│   └── allocator_interface.py
│
├── codegen/                 # 代码生成模块 (8 files)
│   ├── c_codegen.py            # C 代码生成器
│   ├── c_debug_listener.py     # 调试监听器
│   ├── async_codegen.py        # 异步代码生成
│   ├── generic_codegen.py      # 泛型代码生成
│   ├── pattern_codegen.py      # 模式匹配代码生成
│   ├── register_allocator.py   # 寄存器分配
│   └── allocator_interface.py  # 分配器接口
│
├── converter/               # 转换器模块 (12 files)
│   ├── code.py             # 代码转换器
│   ├── error.py            # 错误处理器
│   ├── integrated.py       # 集成转换器
│   ├── attribute.py        # 属性转换器
│   ├── method.py           # 方法转换器
│   ├── inheritance.py      # 继承转换器
│   ├── virtual.py          # 虚函数转换器
│   ├── operator.py         # 运算符重载
│   └── memory.py           # 内存语法转换器
│
├── analysis/                # 分析器模块 (9 files)
│   ├── base_analyzer.py        # 分析器基类
│   ├── analyzer_scheduler.py   # 分析调度器
│   ├── complexity_analyzer.py  # 复杂度分析
│   ├── null_pointer_analyzer.py # 空指针分析
│   ├── resource_leak_analyzer.py # 资源泄漏分析
│   ├── unused_variable_analyzer.py # 未使用变量分析
│   ├── report_generator.py     # 报告生成器
│   └── ast_utils.py            # AST 工具
│
├── analyzer/                # 旧分析器模块 (17 files)
│   ├── dependency.py       # 依赖关系分析
│   ├── performance.py      # 性能分析器
│   └── memory_safety.py    # 内存安全分析
│
├── compiler/                # 编译器模块 (13 files)
│   ├── pipeline.py         # 编译流水线
│   ├── cache.py            # 缓存系统
│   └── optimizer.py        # 性能优化器
│
├── type_system/             # 类型系统
│   └── smart_ptr.py        # 智能指针实现
│
├── typeinfer/               # 类型推导模块
│
├── generics/                # 泛型系统 (3 files)
│   ├── generic_parser.py       # 泛型解析
│   └── generic_instantiator.py # 泛型实例化
│
├── backend/                 # 后端模块
├── opt/                     # 优化模块
├── lsp/                     # Language Server Protocol
├── debugger/                # 调试器模块
├── debug/                   # 调试工具
├── tool/                    # 工具模块
├── template/                # 模板模块
├── package/                 # 包管理模块
│
├── cli/                     # 命令行子模块
│   ├── main.py             # 主命令处理
│   └── toolchain.py        # 工具链管理
│
├── api/                     # API 模块
│   ├── CompilationResult   # 编译结果
│   └── CompilationStats    # 编译统计
│
├── utils/                   # 工具模块
│   ├── file_utils.py       # 文件工具
│   ├── string_utils.py     # 字符串工具
│   └── error_utils.py      # 错误工具
│
├── errors/                  # 错误模块
│
├── config/                  # 配置模块
│
└── lib/                     # 标准库
    ├── __init__.py
    ├── stdio.c             # 标准输入输出库
    └── zhc_stdio.h         # 头文件
```

---

## 三、核心模块详解

### 3.1 解析器模块 (parser/)

**职责**：将中文C源码解析为内部数据结构

#### 关键类

| 类名 | 文件 | 职责 |
|:---|:---|:---|
| ModuleParser | module.py | 解析模块声明、导入语句、可见性控制 |
| ClassParser | class_.py | 解析类声明、属性、方法 |
| ClassParserExtended | class_extended.py | 扩展类解析，支持继承、多态 |
| MemoryParser | memory.py | 解析内存管理语法（申请、释放等） |
| ScopeManager | scope.py | 管理符号作用域和可见性 |

#### 数据流
```
中文源码 → 词法分析 → 语法分析 → AST/中间表示
```

---

### 3.2 转换器模块 (converter/)

**职责**：将解析后的中文语法转换为标准C代码

#### 关键类

| 类名 | 文件 | 职责 |
|:---|:---|:---|
| CodeConverter | code.py | 通用代码转换器 |
| AttributeConverter | attribute.py | 类属性转换（中文类型→C类型） |
| MethodConverter | method.py | 方法转换（this指针、函数签名） |
| InheritanceConverter | inheritance.py | 继承关系转换（struct嵌套） |
| VirtualMethodTableGenerator | method.py | 虚函数表生成 |
| ErrorHandler | error.py | 错误收集、分类、报告 |

#### 转换规则

**类到struct映射**：
```python
中文语法                      →  C代码
─────────────────────────────────────────
类 学生 {                    →  typedef struct 学生_t {
    整数型 年龄;              →      int 年龄;
    字符串型 姓名;            →      char* 姓名;
}                            →  } 学生;
```

**方法转换规则**：
```python
中文方法                      →  C函数
─────────────────────────────────────────
函数 获取信息() -> 字符串型   →  char* 学生_获取信息(struct 学生* self)
静态 函数 计数() -> 整数型    →  int 学生_计数()  # 无this指针
虚函数 绘制() -> 空型         →  void 绘制(struct 形状* self)
```

---

### 3.3 语义分析模块 (semantic/)

**职责**：类型检查、作用域分析、符号解析、泛型处理、模式匹配

#### 关键类

| 类名 | 文件 | 职责 |
|:---|:---|:---|
| SemanticAnalyzer | semantic_analyzer.py | 主语义分析器，类型检查、作用域管理 |
| SymbolTable | symbol_table_optimized.py | 优化的符号表实现 |
| GenericAnalyzer | generics.py | 泛型语义分析 |
| GenericInstantiator | generic_instantiator.py | 泛型实例化 |
| PatternMatcher | pattern_matching.py | 模式匹配实现 |
| CFGAnalyzer | cfg_analyzer.py | 控制流图分析 |
| AsyncAnalyzer | async_system.py | 异步系统语义分析 |

#### 数据流
```
AST → SemanticAnalyzer → 带类型的 AST → IRGenerator
```

---

### 3.4 分析器模块 (analyzer/ + analysis/)

**职责**：分析代码质量、依赖关系、性能特征、内存安全

#### analyzer/ 关键类

| 类名 | 文件 | 职责 |
|:---|:---|:---|
| DependencyResolver | dependency.py | 模块依赖解析、循环检测、拓扑排序 |
| PerformanceAnalyzer | performance.py | 性能测量、基准测试、优化建议 |
| MemorySafetyAnalyzer | memory_safety.py | 内存泄漏检测、越界检查 |

#### analysis/ 关键类

| 类名 | 文件 | 职责 |
|:---|:---|:---|
| BaseAnalyzer | base_analyzer.py | 分析器基类 |
| AnalyzerScheduler | analyzer_scheduler.py | 分析任务调度 |
| ComplexityAnalyzer | complexity_analyzer.py | 代码复杂度分析 |
| NullPointerAnalyzer | null_pointer_analyzer.py | 空指针检测 |
| ResourceLeakAnalyzer | resource_leak_analyzer.py | 资源泄漏检测 |
| UnusedVariableAnalyzer | unused_variable_analyzer.py | 未使用变量检测 |
| ReportGenerator | report_generator.py | 分析报告生成 |

#### 依赖解析算法

使用Kahn算法进行拓扑排序，确保编译顺序正确：
```python
1. 构建依赖图（有向无环图）
2. 检测循环依赖（DFS算法）
3. 拓扑排序（Kahn算法）
4. 生成编译顺序
```

---

### 3.5 编译器模块 (compiler/)

**职责**：协调各模块完成完整的编译流程

#### 关键类

| 类名 | 文件 | 职责 |
|:---|:---|:---|
| IntegrationPipeline | pipeline.py | 完整编译流水线 |
| CompileCache | cache.py | 基于内容哈希的缓存系统 |
| PerformanceOptimizer | optimizer.py | 编译性能优化 |

#### 编译流程

```
源文件 (.zhc)
    ↓
[词法分析] Lexer
    ↓
[语法分析] Parser → AST
    ↓
[语义分析] SemanticAnalyzer → 类型化 AST
    ↓
[IR 生成] IRGenerator → ZHC IR
    ↓
[IR 优化] Optimizer（常量折叠/DCE/函数内联/循环优化）
    ↓
[代码生成] CBackend/CodeGenerator → .c 文件
    ↓
[C编译] clang/gcc 编译为可执行文件
```

---

### 3.6 代码生成模块 (codegen/)

**职责**：将 AST 或 IR 转换为目标代码（C/其他）

#### 关键类

| 类名 | 文件 | 职责 |
|:---|:---|:---|
| CCodegen | c_codegen.py | 主 C 代码生成器 |
| CDebugListener | c_debug_listener.py | 调试信息生成 |
| AsyncCodegen | async_codegen.py | 异步代码生成 |
| GenericCodegen | generic_codegen.py | 泛型代码生成 |
| PatternCodegen | pattern_codegen.py | 模式匹配代码生成 |
| RegisterAllocator | register_allocator.py | 寄存器分配 |

#### 代码生成流程

```
类型化 AST → CCodegen.visit_*() → C 代码
    ↓
IR → CBackend → C 代码
```

---

### 3.7 类型系统 (types/ + type_system/ + typeinfer/ + generics/)

**职责**：实现高级类型系统特性

#### 智能指针

```python
中文语法:
    智能指针<整数型> ptr = 申请智能<整数型>(42);
    
C代码:
    int* ptr = malloc(sizeof(int));
    *ptr = 42;
    // 自动添加析构逻辑
```

#### 泛型系统

```python
中文语法:
    泛型<类型参数> 函数 最大值(泛型<类型参数> a, 泛型<类型参数> b) {
        返回 a > b ? a : b;
    }
    
C代码:
    #define 最大值(T, a, b) ((a) > (b) ? (a) : (b))
```

---

### 3.8 IR 中间表示 (ir/)

**职责**：Phase 7 新增的 IR 层，为代码优化提供中间表示基础。

```
src/ir/
├── symbol.py         # 统一 Symbol + Scope + SymbolCategory
├── types.py          # ZHCTy = TypeInfo 别名
├── opcodes.py        # 35+ 操作码（算术/比较/位运算/内存/控制流/转换）
├── values.py         # IRValue, ValueKind
├── instructions.py   # IRInstruction, IRBasicBlock
├── program.py       # IRProgram, IRFunction, IRGlobalVar, IRStructDef
├── printer.py        # IRPrinter
├── ir_generator.py   # AST → IR 生成器（42 个 visit 方法）
├── c_backend.py     # IR → C 后端（基本块展平算法）
├── ir_verifier.py    # 7 项 IR 合法性检查
├── optimizer.py      # ConstantFolding + DeadCodeElimination + PassManager
└── mappings.py      # TYPE_MAP / FUNCTION_NAME_MAP 等（从 codegen/c_codegen.py 提取）
```

#### 编译流程（Phase 7）

```
.zhc 源码 → Lexer → Parser → AST
                           ↓
                  SemanticAnalyzer（AST 分析）
                           ↓
                     IRGenerator（AST → IR）
                           ↓
                        ZHC IR
                           ↓
                      IRVerifier（7 项检查）
                           ↓
                    Optimizer（常量折叠/死代码消除）
                           ↓
                        IR'
                           ↓
                       CBackend（IR → C）
                           ↓
                        C 代码 → clang → 可执行文件
```

#### IR 模块完整文件列表

```
src/ir/
├── __init__.py              # 模块入口
├── symbol.py                # 统一 Symbol + Scope + SymbolCategory
├── types.py                 # ZHCTy = TypeInfo 别名
├── opcodes.py                # 35+ 操作码（算术/比较/位运算/内存/控制流/转换）
├── values.py                # IRValue, ValueKind
├── instructions.py          # IRInstruction, IRBasicBlock
├── program.py               # IRProgram, IRFunction, IRGlobalVar, IRStructDef
├── printer.py               # IRPrinter
├── ir_generator.py          # AST → IR 生成器（42 个 visit 方法）
├── ir_verifier.py           # 7 项 IR 合法性检查
├── optimizer.py             # ConstantFolding + DeadCodeElimination + PassManager
├── mappings.py              # TYPE_MAP / FUNCTION_NAME_MAP 等
├── c_backend.py             # IR → C 后端（基本块展平算法）
├── llvm_backend.py          # IR → LLVM 后端（可选）
│
├── [优化器模块]
├── dataflow.py              # 数据流分析框架
├── dominator.py             # 支配树分析
├── ssa.py                    # 静态单赋值形式转换
├── inline_optimizer.py      # 函数内联优化
├── loop_optimizer.py         # 循环优化
├── loop_unroller.py         # 循环展开
├── optimization_hints.py     # 优化提示
├── register_allocator.py    # 寄存器分配
│
└── [代码生成]
    └── allocator_interface.py  # 分配器接口
```

#### CLI 参数（Phase 7）

| 参数 | 默认 | 说明 |
|------|------|------|
| `--backend ir\|ast` | ast | 选择后端 |
| `--dump-ir` | 关闭 | 打印 IR |
| `--no-optimize` | 关闭 | 禁用优化 Pass |

---

### 3.9 后端模块 (backend/)

**职责**：多后端代码生成，支持 C、LLVM IR、WASM

```
src/backend/
├── __init__.py
├── allocator_interface.py   # 分配器接口
├── llvm_backend.py          # LLVM IR 后端
├── llvm_instruction.py      # LLVM 指令生成器
├── llvm_jit.py              # LLVM JIT 执行引擎
├── llvm_type_mapper.py      # LLVM 类型映射器
└── wasm_backend.py          # WASM 后端（实验性）
```

#### 3.9.1 LLVM 后端

**核心组件**：

| 组件 | 文件 | 职责 |
|:---|:---|:---|
| LLVMBackend | llvm_backend.py | ZHC IR → LLVM IR 主编译器 |
| LLVMTypeMapper | llvm_type_mapper.py | ZhC 类型 → LLVM 类型映射 |
| LLVMInstructionGenerator | llvm_instruction.py | ZhC Opcode → LLVM 指令生成 |
| LLVMJIT | llvm_jit.py | JIT 即时编译与执行 |

**类型映射**：

```python
# ZhC 类型 → LLVM 类型
ZHCT_TO_LLVM = {
    "整数型": "i32",
    "长整数型": "i64",
    "短整数型": "i16",
    "字节型": "i8",
    "浮点型": "float",
    "双精度浮点型": "double",
    "字符型": "i8",
    "布尔型": "i1",
    "空型": "void",
}
```

**指令映射**：

| 类别 | ZhC Opcode | LLVM 指令 |
|:---|:---|:---|
| 算术 | ADD, SUB, MUL, DIV, MOD | add, sub, mul, sdiv, srem |
| 比较 | EQ, NE, LT, LE, GT, GE | icmp eq/ne/slt/sle/sgt/sge |
| 位运算 | AND, OR, XOR, NOT, SHL, SHR | and, or, xor, not, shl, shr |
| 内存 | ALLOC, LOAD, STORE, GEP | alloca, load, store, getelementptr |
| 控制流 | JMP, JZ, RET, CALL, PHI | br, br, ret, call, phi |
| 转换 | ZEXT, SEXT, TRUNC, BITCAST | zext, sext, trunc, bitcast |

#### 3.9.2 LLVM JIT 执行引擎

**功能**：
- 即时编译 ZHC IR 到原生机器码
- 支持 Python 调用编译后的函数
- 支持优化级别控制 (O0-O3)

**使用示例**：

```python
from zhc.backend.llvm_jit import LLVMJIT, jit_compile_and_run

# 方式1: 便捷函数
result = jit_compile_and_run(ir_program, "main", 42)

# 方式2: 完整控制
jit = LLVMJIT(opt_level=2)
jit.compile(ir_program)
func = jit.get_function("main")
result = func(42)

# 获取 LLVM IR 文本
llvm_ir = jit.get_llvm_ir()
```

#### 3.9.3 编译后端对比

| 后端 | 输出 | 优化 | JIT | 适用场景 |
|:---|:---|:---|:---|:---|
| CBackend | .c 文件 | 中等 | 否 | 跨平台、调试、gcc/clang 工具链 |
| LLVMBackend | .ll/.bc | 高 | 是 | 高性能、原生执行、即时编译 |
| WASMBackend | .wasm | 中等 | 否 | Web 部署、浏览器运行 |

#### 3.9.4 编译流程对比

```
                    ┌─────────────────┐
                    │   ZHC IR        │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ CBackend │  │   LLVM   │  │   WASM   │
        └────┬─────┘  └────┬─────┘  └────┬─────┘
             │             │             │
             ▼             ▼             ▼
          .c 文件      .ll/.bc       .wasm
             │             │             │
             ▼             ▼             ▼
        gcc/clang      llc/opt      浏览器运行
             │             │
             ▼             ▼
        可执行文件    原生机器码
```

---

### 3.9 命令行模块 (cli/)

**职责**：提供用户友好的命令行接口

#### 主要命令

```bash
# 编译单文件
python3 -m src.__main__ hello.zhc

# 编译项目
python3 -m src.__main__ build project/

# 清理缓存
python3 -m src.__main__ clean --cache

# 性能分析
python3 -m src.__main__ profile input.zhc

# 生成文档
python3 -m src.__main__ doc api/
```

---

## 四、数据流与依赖关系

### 4.1 模块依赖关系图

```mermaid
flowchart TB
    subgraph 前端
        CLI[CLI 入口<br/>cli.py]
        KW[关键词映射<br/>keywords.py]
    end

    subgraph 核心
        PP[Parser<br/>parser/]
        SA[SemanticAnalyzer<br/>semantic/]
        IR[IRGenerator<br/>ir/]
        CG[CodeGenerator<br/>codegen/]
    end

    subgraph 支持
        AP[API 模块<br/>api/]
        CFG[配置模块<br/>config/]
        UT[工具模块<br/>utils/]
        ERR[错误模块<br/>errors/]
    end

    CLI --> PP
    CLI --> SA
    CLI --> IR
    CLI --> CG
    CLI --> AP
    CLI --> CFG

    KW --> PP
    KW --> SA

    PP --> SA
    SA --> IR
    IR --> CG

    SA --> ERR
    CG --> ERR
    UT --> CFG

    style CLI fill:#ff9800,color:#fff
    style PP fill:#2196f3,color:#fff
    style SA fill:#4caf50,color:#fff
    style IR fill:#9c27b0,color:#fff
    style CG fill:#f44336,color:#fff
```

### 4.2 编译数据流

```mermaid
sequenceDiagram
    participant User as 用户
    participant CLI as CLI
    participant Lexer as 词法分析
    participant Parser as 语法分析
    participant Semantic as 语义分析
    participant IR as IR 生成
    participant Codegen as 代码生成
    participant Output as 输出

    User->>CLI: 编译 hello.zhc
    CLI->>Lexer: 源代码
    Lexer->>Parser: Token 序列
    Parser->>Semantic: AST
    Semantic->>IR: 带类型的 AST
    IR->>Codegen: ZHC IR
    Codegen->>Output: .c 文件
    Output-->>User: 编译完成

    Note over Lexer,Output: 错误处理：任意阶段失败都返回 CompilationResult
```

### 4.3 API 数据流

```mermaid
flowchart LR
    subgraph 输入层
        CLI[CLI 入口]
        API[API 入口]
    end

    subgraph 配置层
        CC[CompilerConfig]
        SC[SemanticConfig]
        OC[OutputConfig]
        CAC[CacheConfig]
    end

    subgraph 结果层
        CR[CompilationResult]
        CS[CompilationStats]
    end

    CLI --> CC
    API --> CC
    CC --> SC
    CC --> OC
    CC --> CAC
    SC --> CR
    OC --> CR
    CAC --> CS

    style CR fill:#4caf50,color:#fff
    style CS fill:#2196f3,color:#fff
```

---

## 五、扩展指南

### 5.1 添加新的解析器

1. 在 `parser/` 目录下创建新文件
2. 实现解析器类，继承基础解析器接口
3. 在 `__init__.py` 中导出新类
4. 编写单元测试（tests/test_suite*/）

**示例**：
```python
# parser/new_feature.py
from zhc.parser.base import BaseParser

class NewFeatureParser(BaseParser):
    def parse(self, source: str) -> ASTNode:
        # 实现解析逻辑
        pass
```

### 5.2 添加新的转换器

1. 在 `converter/` 目录下创建新文件
2. 实现转换器类，包含中文→C的映射逻辑
3. 注册到集成转换器
4. 添加单元测试

### 5.3 添加新的分析器

1. 在 `analyzer/` 目录下创建新文件
2. 实现分析逻辑
3. 集成到编译流水线
4. 添加性能测试

---

## 六、性能优化策略

### 6.1 编译缓存

**缓存键**: 文件内容哈希 + 依赖哈希  
**缓存内容**: 转换后的C代码  
**命中率**: 60-80%（增量编译）

### 6.2 并发编译

**策略**: 独立模块并行编译  
**加速比**: 2-4倍（多核CPU）  
**依赖**: 拓扑排序确保正确性

### 6.3 内存优化

**对象池**: 复用AST节点  
**延迟加载**: 按需解析模块  
**内存映射**: 大文件使用mmap

---

## 七、测试策略

### 7.1 测试套件组织

```
tests/
├── conftest.py              # pytest配置
├── test_suite1_types.py     # 类型系统测试
├── test_suite2_control.py   # 流程控制测试
├── test_suite3_funcs.py     # 函数测试
├── test_suite8/             # 类系统完整测试
│   ├── test_class_system_complete.py
│   ├── test_module_conversion.py
│   └── ...
└── test_suite10/            # 高级特性测试
```

### 7.2 测试覆盖率

- **单元测试**: 95%+代码覆盖
- **集成测试**: 关键路径100%覆盖
- **性能测试**: 基准测试套件

---

## 八、未来规划

### Phase 4 (计划中)

1. **类型推导系统**
   - 自动类型推导
   - 泛型支持

2. **元编程支持**
   - 编译时计算
   - 代码生成

3. **跨平台支持**
   - Windows/Linux/macOS
   - 嵌入式平台

4. **IDE集成**
   - VSCode插件
   - 语法高亮
   - 代码补全

---

## 九、附录

### A. 中文关键词完整列表

参见 `src/keywords.py`，共258个关键词。

### B. API参考文档

- 在线文档: https://zhc.readthedocs.io
- 本地生成: `python3 -m src.__main__ doc api/`

### C. 贡献指南

参见 `CONTRIBUTING.md`

---

**文档维护者**: 远  
**最后更新**: 2026-04-08

---

## 十、Phase 1-5 架构演进记录

### Phase 1: 项目初始化
- **时间**: 2026-03
- **主要变化**:
  - 创建基础项目结构
  - 实现词法分析器 (Lexer)
  - 实现基础语法分析器 (Parser)

### Phase 2: 类系统支持
- **时间**: 2026-03
- **主要变化**:
  - 添加类语法解析 (`parser/class_.py`)
  - 实现继承转换 (`converter/inheritance.py`)
  - 添加虚函数支持 (`converter/virtual.py`)
  - 添加运算符重载 (`converter/operator.py`)

### Phase 3: 模块系统
- **时间**: 2026-03
- **主要变化**:
  - 实现模块解析 (`parser/module.py`)
  - 实现导入/导出机制
  - 添加作用域管理 (`parser/scope.py`)
  - 实现依赖解析 (`analyzer/dependency.py`)

### Phase 4: 内存安全增强
- **时间**: 2026-03
- **主要变化**:
  - 添加内存语法解析 (`parser/memory.py`)
  - 实现内存安全分析 (`analyzer/memory_safety.py`)
  - 添加智能指针支持 (`types/smart_ptr.py`)
  - 实现内存转换 (`converter/memory.py`)

### Phase 5: 重构与优化
- **时间**: 2026-04-07 ~ 2026-04-08
- **主要变化**:
  - 创建统一 API 模块 (`src/api/`)
  - 重构配置系统 (Configuration Groups 模式)
  - 引入 Dispatch Table 模式
  - 优化圈复杂度 (9.5 → 8.0)
  - 质量评分提升 (65 → 70)
  - **新增模块**:
    - `src/api/` - API 模块 (CompilationResult, CompilationStats)
    - `src/utils/` - 工具模块 (file_utils, string_utils, error_utils)

### Phase 6: 文档体系（进行中）
- **时间**: 2026-04-08
- **主要变化**:
  - 配置 Sphinx 文档系统
  - 创建 API 参考文档
  - 编写开发者指南
  - 完善架构文档

### Phase 7: IR 中间表示层（已完成）
- **时间**: 2026-04-08
- **主要变化**:
  - 新增 IR 中间表示层 (`src/ir/`, 22 files)
  - 实现 IRGenerator（AST → IR，42 个 visit 方法）
  - 实现 IRVerifier（7 项合法性检查）
  - 实现 IROptimizer（常量折叠、死代码消除、PassManager）
  - 实现 CBackend（IR → C，基本块展平算法）
  - 新增高级优化器：
    - dataflow.py - 数据流分析框架
    - dominator.py - 支配树分析
    - ssa.py - 静态单赋值形式转换
    - inline_optimizer.py - 函数内联优化
    - loop_optimizer.py - 循环优化
    - loop_unroller.py - 循环展开
  - 新增 CLI 参数：`--backend ir|ast`, `--dump-ir`, `--no-optimize`

### Phase 8: 语义分析增强（已完成）
- **时间**: 2026-04-08
- **主要变化**:
  - 扩展语义分析模块 (`src/semantic/`, 13 files)
  - 实现泛型语义分析 (`generics.py`, `generic_parser.py`, `generic_instantiator.py`)
  - 实现模式匹配 (`pattern_matching.py`, `pattern_parser.py`, `pattern_analyzer.py`)
  - 实现 CFG 分析 (`cfg_analyzer.py`)
  - 实现异步系统语义分析 (`async_system.py`, `async_parser.py`)
  - 优化符号表 (`symbol_table_optimized.py`)

### Phase 9: 代码生成增强（已完成）
- **时间**: 2026-04-08
- **主要变化**:
  - 扩展代码生成模块 (`src/codegen/`, 8 files)
  - 实现异步代码生成 (`async_codegen.py`)
  - 实现泛型代码生成 (`generic_codegen.py`)
  - 实现模式匹配代码生成 (`pattern_codegen.py`)
  - 实现寄存器分配 (`register_allocator.py`)
  - 添加调试监听器 (`c_debug_listener.py`)

### Phase 10: 分析器扩展（已完成）
- **时间**: 2026-04-08
- **主要变化**:
  - 新增分析模块 (`src/analysis/`, 9 files)
  - 实现复杂度分析 (`complexity_analyzer.py`)
  - 实现空指针检测 (`null_pointer_analyzer.py`)
  - 实现资源泄漏检测 (`resource_leak_analyzer.py`)
  - 实现未使用变量检测 (`unused_variable_analyzer.py`)
  - 实现分析调度器 (`analyzer_scheduler.py`)
  - 实现报告生成器 (`report_generator.py`)

### Phase 11: DevOps 流程（计划中）
- **时间**: 2026-04-08 之后
- **计划变化**:
  - 增强 CI/CD 流程
  - 添加 Issue/PR 模板
  - 实现自动化发布
  - 添加 CHANGELOG 自动生成
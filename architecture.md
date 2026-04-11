# ZhC 架构文档

**中文 C 编译器 (ZhC Compiler)** - 编译到 LLVM IR

*最后更新: 2026-04-11*

---

## 1. 系统概览

ZhC 是一个用 Python 实现的中文 C 编译器，将中文 C 代码编译到 LLVM IR，可输出原生机器码。

### 技术栈
- **Python 3.14.3** + **llvmlite 0.47.0**
- **LLVM IR** 作为中间表示
- **C 运行时库** 提供标准库支持

### 项目规模
| 指标 | 数量 |
|------|------|
| Python 源文件 | 323 |
| Python 代码行数 | ~135,000 |
| 测试文件 | 143 |
| 测试用例 | 3330 |
| C/H 运行时文件 | 39 |

---

## 2. 编译流水线

```
源代码 (.zhc)
     │
     ▼
┌─────────┐
│  Lexer  │  词法分析 → Token 序列
└─────────┘
     │
     ▼
┌─────────┐
│  Parser │  语法分析 → AST
└─────────┘
     │
     ▼
┌──────────────────┐
│ SemanticAnalyzer │  语义分析 → 带类型的 AST + 符号表
└──────────────────┘
     │
     ▼
┌────────────────┐
│  IRGenerator   │  IR 生成 → ZhC IR (中间表示)
└────────────────┘
     │
     ▼
┌─────────────────┐
│  IROptimizer    │  IR 优化 (常量折叠、死代码消除、函数内联、循环优化)
└─────────────────┘
     │
     ▼
┌──────────────────┐
│  LLVMBackend     │  LLVM IR 生成 → 原生机器码
└──────────────────┘
     │
     ▼
   可执行文件
```

---

## 3. 核心模块

### 3.1 解析器 (Parser)

| 模块 | 路径 | 功能 |
|------|------|------|
| Lexer | `parser/lexer.py` | 词法分析，识别 Token |
| Parser | `parser/parser.py` | 语法分析，构建 AST |
| AST Nodes | `parser/ast_nodes.py` | AST 节点类型定义 |

### 3.2 语义分析 (Semantic)

| 模块 | 路径 | 功能 |
|------|------|------|
| SemanticAnalyzer | `semantic/semantic_analyzer.py` | 类型检查、作用域分析、符号解析 |

### 3.3 中间表示 (IR)

| 模块 | 路径 | 功能 |
|------|------|------|
| IRGenerator | `ir/ir_generator.py` | AST → IR 转换 |
| Opcodes | `ir/opcodes.py` | IR 操作码定义 |
| Cast | `ir/cast.py` | LLVM 风格类型转换节点 |

### 3.4 后端 (Backend)

| 模块 | 路径 | 功能 |
|------|------|------|
| LLVM Backend | `backend/llvm_backend.py` | LLVM IR 代码生成 |
| 指令策略 | `backend/llvm_instruction_strategy.py` | LLVM 指令编译策略 |
| 类型检查策略 | `backend/type_check_strategies.py` | 反射类型检查编译策略 |
| 反射策略 | `backend/reflection_strategies.py` | 反射操作编译策略 |

### 3.5 反射系统 (Reflection)

| 模块 | 路径 | 功能 |
|------|------|------|
| TypeInfo | `reflection/type_info.py` | 类型元数据 (ReflectionTypeInfo, FieldInfo, MethodInfo) |
| TypeCheck | `reflection/type_check.py` | 运行时类型检查 (is_type, is_subtype, implements_interface) |
| TypeCast | `reflection/type_cast.py` | 类型转换 (safe_cast, dynamic_cast, CastResult) |
| Metadata | `reflection/metadata.py` | 反射元数据收集器 |

### 3.6 类型系统 (Type System)

| 模块 | 路径 | 功能 |
|------|------|------|
| 基础类型 | `type_system/primitives.py` | 基础类型定义 |
| 函数指针 | `type_system/function_pointer.py` | 函数指针类型支持 |
| 智能指针 | `type_system/smart_ptr.py` | 智能指针类型检查 |
| 结构体布局 | `type_system/struct_layout.py` | 结构体内存布局计算 |

### 3.7 高级特性

| 特性 | 路径 | 状态 |
|------|------|------|
| 异常处理 | `exception/` | ✅ 已完成 |
| 闭包 | `functional/` | ✅ 已完成 |
| 协程 | `functional/coroutine.py` | ✅ 已完成 |
| 内存管理 | `memory/` | ✅ 已完成 (UniquePtr, SharedPtr, WeakPtr) |
| RAII | `memory/raii.py` | ✅ 已完成 |
| 模式匹配 | 待定 | 🔄 开发中 |
| 泛型 | `generics/` | 🔄 开发中 |

---

## 4. 编译后端

### 4.1 LLVM 后端

使用 `llvmlite` 库生成 LLVM IR，支持：
- 原生机器码生成
- JIT 即时编译
- 高级优化 (LTO, IPO)

### 4.2 后端策略模式

```
CompilationContext
    │
    ├── ArithmeticStrategy (add, sub, mul, div, mod)
    ├── ComparisonStrategy (eq, ne, lt, le, gt, ge)
    ├── LogicalStrategy (and, or, not)
    ├── BitwiseStrategy (and, or, xor, shl, shr)
    ├── MemoryStrategy (alloc, load, store, gep)
    ├── BranchStrategy (br, cond_br, switch)
    ├── CallStrategy (call, ret)
    ├── CastStrategy (zext, sext, trunc, bitcast)
    ├── TypeCheckStrategy (is_type, is_subtype, implements_interface)
    └── ReflectionStrategy (get_type_info, get_type_name, etc.)
```

---

## 5. C 运行时库

位于 `lib/` 目录：

| 文件 | 功能 |
|------|------|
| `zhc_stdio.h/c` | 标准输入输出 |
| `zhc_math.h/c` | 数学函数 |
| `zhc_string.h/c` | 字符串操作 |
| `zhc_memory.h/c` | 内存管理 |
| `zhc_exception.h/c` | 异常处理 |
| `zhc_coroutine.h/c` | 协程支持 |
| `zhc_smart_ptr.h/c` | 智能指针 |
| `zhc_reflection.h/c` | 反射元数据 |
| `zhc_type_check.h/c` | 类型检查运行时 |
| `zhc_dynamic_cast.h/c` | 动态类型转换 |
| `zhc_net.h/c` | 网络库 |

---

## 6. 反射系统架构

```
┌─────────────────────────────────────────────────────┐
│                   反射 API 层                         │
│  is_type(), is_subtype(), implements_interface()    │
│  safe_cast(), dynamic_cast(), require_type()         │
│  get_type_info(), get_field(), get_method()           │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                 CastResult 模式                       │
│  success: bool, result: T, error: Optional[str]      │
│  unwrap(), unwrap_or(), is_ok(), is_err()            │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│               IR 指令层 (LLVM 风格)                   │
│  IRSafeCastInst, IRDynamicCastInst, IRIsTypeInst    │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│               后端编译策略层                          │
│  SafeCastStrategy, DynamicCastStrategy,             │
│  IsTypeStrategy, IsSubtypeStrategy, etc.           │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│               C 运行时层                             │
│  zhc_type_check.h/c, zhc_dynamic_cast.h/c           │
│  zhc_reflection.h/c                                 │
└─────────────────────────────────────────────────────┘
```

---

## 7. 关键字映射

ZhC 支持 258 个中文关键字，覆盖：
- 基础类型 (`整数型`, `浮点型`, `字符型`, `布尔型`)
- 控制流 (`如果`, `否则`, `当`, `循环`, `返回`)
- 函数 (`函数`, `主函数`, `公开`, `私有`)
- 内存管理 (`申请`, `释放`, `移动`)
- 异常处理 (`尝试`, `捕获`, `抛出`, `最终`)
- 反射 (`是类型`, `转为`, `是子类型`, `实现接口`)
- 模块系统 (`模块`, `导入`, `导出`)

---

## 8. 文件结构

```
ZhC/
├── src/zhc/                    # 编译器源码
│   ├── parser/                  # 词法/语法分析
│   ├── semantic/               # 语义分析
│   ├── ir/                     # 中间表示
│   ├── backend/                # LLVM 后端
│   ├── reflection/             # 反射系统 (P5)
│   ├── type_system/            # 类型系统
│   ├── memory/                 # 内存管理
│   ├── exception/              # 异常处理
│   ├── functional/             # 函数式特性 (闭包/协程)
│   ├── lib/                    # C 运行时库
│   ├── cli/                    # 命令行工具
│   └── utils/                  # 工具函数
├── tests/                      # 测试套件 (143 files, 3330 tests)
├── docs/                       # 文档
├── examples/                   # 示例代码
└── scripts/                    # 辅助脚本
```

---

## 9. 开发约定

### 9.1 命名规范
- 类名: `PascalCase` (如 `SemanticAnalyzer`)
- 方法名: `snake_case` (如 `analyze_node`)
- 常量: `UPPER_SNAKE_CASE` (如 `MAX_RECURSION_DEPTH`)
- 中文关键字: 全小写 (如 `整数型`, `如果`)

### 9.2 模块扩展模式
新增模块时需同步更新：
1. `keywords.py` - 关键字映射
2. `opcodes.py` - IR 操作码
3. `ast_nodes.py` - AST 节点类型
4. `parser/parser.py` - 解析逻辑
5. `semantic/semantic_analyzer.py` - 语义分析
6. `ir/ir_generator.py` - IR 生成
7. `backend/*strategies.py` - 后端策略
8. `lib/zhc_*.h/c` - C 运行时
9. `tests/` - 单元测试

---

## 10. 测试框架

```
tests/
├── test_parser_*.py           # 解析器测试
├── test_semantic_*.py        # 语义分析测试
├── test_ir_*.py             # IR 测试
├── test_backend_*.py        # 后端测试
├── test_reflection.py        # 反射测试
├── test_type_check.py        # 类型检查测试
├── test_dynamic_cast.py      # 动态转换测试
└── test_integration_*.py    # 集成测试
```

测试运行: `python3 -m pytest tests/ -v`

---

*架构文档 - ZhC 中文 C 编译器*

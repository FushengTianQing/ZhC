# ZhC 中文 C 编译器

**用中文写 C 程序！🚀** 


### 🧬 完整反射系统 (P5)
- **运行时类型检查**: `是类型()`, `是子类型()`, `实现接口()`
- **动态类型转换**: `as`/`is` 表达式, `转为()`, `安全转换()`, `动态转换()`
- **类型元数据**: `获取类型信息()`, `获取字段()`, `获取方法()`
- **CastResult 模式**: 类似 C++23 `std::expected`，类型安全的错误处理

### 🔧 智能内存管理
- **独享指针 (UniquePtr)**: 独占所有权，自动释放
- **共享指针 (SharedPtr)**: 引用计数，共享所有权
- **弱指针 (WeakPtr)**: 打破循环引用
- **RAII**: 析构函数、作用域守卫、清理栈

### ⚡ 高级语言特性
- **异常处理**: `尝试`/`捕获`/`抛出`/`最终`，支持自定义异常类
- **闭包**: Lambda 表达式、Upvalue 捕获
- **协程**: `async`/`await`/`spawn`/`yield`/`channel`
- **函数指针**: 完整的函数指针类型系统
- **模式匹配** ✅: 结构化模式匹配（守卫求值/冗余检测/枚举Switch降级/Range/Tuple/Destructure）
- **泛型** ✅: 泛型类型系统（解析/单态化/约束推导/嵌套递归/177 测试全通过）
- **复杂类型**: 复数运算、定点数运算
- **SIMD 向量化**: x86 SSE/AVX, ARM NEON, RISC-V VVW, WASM 四平台

### 🚀 高性能编译
- **多后端支持**: C/GCC/Clang/LLVM/WASM 五种后端
- **IR 优化**: 常量折叠、死代码消除、函数内联、循环优化（SSA/数据流）
- **智能缓存**: 增量编译，重复编译提速 60-80%
- **策略模式后端**: `CompilationContext` + 10+ 策略类，扩展新指令只需新增策略

### 📚 完全中文友好
- **258 个中文关键字**: 覆盖 C 语言全部功能
- **中文标准库**: `打印()`, `申请()`, `释放()`, `连接网络()` 等
- **中文错误信息**: 精确的错误定位和修复建议

### 🛠 完整工具链
- **DWARF 调试信息**: 完整的调试信息生成（debug_info/debug_line/debug_abbrev/debug_str）
- **GDB/LLDB 集成**: 调试器协议支持
- **LSP 协议**: JSON-RPC + Language Server 完整协议栈
- **包管理系统**: 依赖解析/版本控制/仓库管理
- **内存检查**: 泄漏检测 + 调用栈追踪
- **覆盖率分析**: 代码覆盖率工具
- **性能分析**: Profiler 性能分析器
- **文档生成**: Sphinx API 文档
- **交叉编译**: 多平台交叉编译支持

---

## 快速开始

### 安装

```bash
# 从源码安装
git clone https://github.com/FushengTianQing/ZhC.git
cd ZhC
pip install -e .
```

## 编译流水线

```
┌──────────────────────────────────────────────────────────────────┐
│                      ZhC 编译流水线                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  源码 (.zhc)                                                     │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────┐    Token 序列                                   │
│  │   Lexer     │ ──────────►                                     │
│  └─────────────┘                                                │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────┐    AST (76 种节点类型)                          │
│  │   Parser    │ ──────────►                                     │
│  └─────────────┘                                                │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────────┐    带类型的 AST + 符号表                    │
│  │ SemanticAnalyzer │ ──────────►                                │
│  │  (15 个子模块)    │                                            │
│  └──────────────────┘                                            │
│       │                                                          │
│       ▼                                                          │
│  ┌────────────────┐    ZHC IR (中间表示)                         │
│  │  IRGenerator   │ ──────────►  (60+ 操作码)                   │
│  └────────────────┘                                               │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────┐                                             │
│  │  IROptimizer     │  常量折叠/死代码消除/内联/循环优化          │
│  │  (SSA/数据流)   │                                             │
│  └─────────────────┘                                            │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────────┐                                            │
│  │   LLVMBackend    │ ──► LLVM IR ──► 原生机器码                 │
│  │  (策略模式)      │                                            │
│  └──────────────────┘                                            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

| 阶段 | 组件 | 功能 |
|------|------|------|
| 词法分析 | Lexer | 识别 258 个中文关键字、标识符、运算符 |
| 语法分析 | Parser (Mixin 架构) | 构建 76 种 AST 节点 |
| 语义分析 | SemanticAnalyzer (15 子模块) | 类型检查、作用域分析、泛型解析 |
| IR 生成 | IRGenerator | 生成 60+ 操作码的中间表示 |
| IR 优化 | IROptimizer | 常量折叠、死代码消除、内联、循环优化 |
| 代码生成 | LLVMBackend (策略模式) | LLVM IR → C/GCC/Clang/WASM 原生码 |

---

## 项目结构

```
ZhC/
├── src/zhc/                    # 编译器源码 (323 Python 文件, ~135K 行)
│   ├── parser/                  # 词法/语法分析 (15 文件)
│   │   ├── lexer.py             # 词法分析器
│   │   ├── parser.py            # 语法分析器 (Mixin 架构)
│   │   ├── ast_nodes.py         # 76 个 AST 节点类
│   │   └── ...                  # scope/class/memory/module_alias 等
│   ├── semantic/               # 语义分析 (15 文件)
│   │   ├── semantic_analyzer.py # 主语义分析器
│   │   ├── generics.py          # 泛型系统
│   │   ├── pattern_matching.py  # 模式匹配
│   │   ├── cfg_analyzer.py      # 控制流分析
│   │   └── ...                  # async_system/type_check 等
│   ├── ir/                      # 中间表示 (22 文件)
│   │   ├── ir_generator.py      # IR 生成器
│   │   ├── opcodes.py           # 60+ 操作码定义
│   │   ├── ssa.py               # SSA 构造
│   │   ├── dataflow.py          # 数据流分析
│   │   ├── inline_optimizer.py  # 内联优化
│   │   ├── loop_optimizer.py    # 循环优化
│   │   └── ...
│   ├── backend/                # 后端/代码生成 (31 文件, 策略模式)
│   │   ├── llvm_backend.py      # LLVM 后端
│   │   ├── llvm_instruction_strategy.py  # 策略模式指令
│   │   ├── compilation_context.py        # 编译上下文
│   │   └── ...                  # 各特性 strategy 文件
│   ├── reflection/             # 反射系统 (P5, 4 文件)
│   ├── type_system/            # 类型系统 (9 文件)
│   ├── memory/                 # 内存管理 (4 文件)
│   ├── exception/              # 异常处理 (6 文件)
│   ├── functional/             # 闭包/协程 (5 文件)
│   ├── analyzer/               # 静态分析器套件 (16 文件)
│   ├── codegen/                # 代码生成器 (11 文件)
│   ├── debug/                  # DWARF 调试信息 (20 文件)
│   ├── debugger/               # GDB/LLDB 支持 (9 文件)
│   ├── simd/                   # SIMD 向量化 (13 文件)
│   ├── optimization/           # 优化 pass 系统 (7 文件)
│   ├── compiler/               # 编译流水线/缓存 (12 文件)
│   ├── cross/                  # 交叉编译支持 (10 文件)
│   ├── errors/                 # 错误处理体系 (14 文件)
│   ├── lsp/                    # Language Server Protocol (4 文件)
│   ├── package/                # 包管理系统 (24 文件)
│   ├── coverage/               # 覆盖率工具 (5 文件)
│   ├── memcheck/               # 内存检查 (6 文件)
│   ├── profiler/               # 性能分析 (5 文件)
│   ├── doc/                    # 文档生成 (5 文件)
│   ├── cli/                    # 命令行工具
│   ├── lib/                    # C 运行时库 (39 文件)
│   │   ├── zhc_stdio.h         # 标准输入输出
│   │   ├── zhc_string.h/c      # 字符串操作
│   │   ├── zhc_math.h          # 数学函数
│   │   ├── zhc_exception.h/c   # 异常处理运行时
│   │   ├── zhc_coroutine.h/c   # 协程调度
│   │   ├── zhc_closure.h/c     # 闭包运行时
│   │   ├── zhc_smart_ptr.h/c   # 智能指针运行时
│   │   ├── zhc_reflection.h/c  # 反射元数据
│   │   ├── zhc_net.h           # 网络通信
│   │   └── ...                 # encoding/complex/fixed/memcheck 等
│   └── utils/                  # 工具函数
├── tests/                      # 测试套件 (143 文件, 3511 测试)
├── docs/                       # 开发路线图文档 (302 文件)
├── examples/                   # 示例代码
├── scripts/                    # 辅助脚本
├── architecture.md             # 系统架构详解
└── CHANGELOG.md                # 版本更新日志
```

---

## 设计模式

ZhC 在架构中广泛运用了经典设计模式，确保代码的可扩展性和可维护性：

| 模式 | 应用位置 | 说明 |
|------|----------|------|
| **策略模式** | `backend/*_strategies.py` | 后端指令解耦，新增指令只需添加策略类 |
| **访问者模式** | `ASTNode` + `ASTVisitor` | 标准 AST 遍历规范 |
| **Mixin 模式** | Parser (declarations/statements/expressions) | 大文件按职责拆分 |
| **Dispatch Table** | Parser / 语义分析 | 替代大 if-elif 链，分发高效 |
| **命令模式** | CLI 命令处理 | 命令解耦，易扩展 |
| **工厂方法** | 后端管理器 / 指令工厂 | 类型安全的对象创建 |
| **Dataclass 配置** | `config.py` 分组配置 | 现代类型安全配置 |
| **观察者模式** | `optimization_observer.py` | 优化过程可观测 |
| **注册表模式** | `pass_registry` / opcode 定义 | 可扩展的 pass 注册 |

---

## 高级特性示例

### 异常处理

```zhc
尝试 {
    可能抛出异常();
} 捕获 (异常 e) {
    打印("捕获异常: %s\n", e.消息);
} 最终 {
    清理资源();
}
```

### 智能指针

```zhc
指针 = 新建 独享指针[整数型](42);
共享指针 = 新建 共享指针[整数型](100);

函数(共享指针);  # 引用计数 +1
# 函数返回后引用计数 -1

弱指针 = 创建 弱指针(共享指针);
如果 (弱指针.已过期) {
    打印("资源已释放\n");
}
```

### 协程

```zhc
协程 异步任务(整数型 参数) {
    打印("开始任务 %d\n", 参数);
    暂停;
    打印("恢复任务 %d\n", 参数);
    返回 结果;
}
```

### 函数指针

```zhc
整数型 (*回调)(整数型, 整数型) = 加法;

整数型 加法(整数型 a, 整数型 b) {
    返回 a + b;
}

整数型 计算(整数型 x, 整数型 y, 整数型 (*op)(整数型, 整数型)) {
    返回 op(x, y);
}
```

---

## 命令行工具

```bash
# 编译单个文件
zhc compile 文件.zhc -o 输出目录

# 指定后端 (c/gcc/clang/llvm/wasm)
zhc compile 文件.zhc --backend llvm

# 打印 IR
zhc compile 文件.zhc --dump-ir

# 查看帮助
zhc --help

# 运行测试
python3 -m pytest tests/ -v
```

---

## 版本时间线

```
v0.1 (2026-03)    → 基础结构 / Lexer / Parser
v0.2 (2026-03)    → 类语法 / 继承 / 虚函数 / 运算符重载
v0.3 (2026-03)    → 模块系统 / 导入导出 / 作用域管理
v0.4 (2026-03)    → 内存安全分析 / 智能指针
v0.5 (2026-04-07) → Week5 重构 / Dispatch Table / 状态机 / 命令模式
v0.6 (2026-04-08) → 统一 API / IR 后端 / 配置分组 / 覆盖率 57%
v0.7 (2026-04-09) → 异常处理 / 闭包 / 协程 / 网络库
v0.8 (2026-04-10) → 泛型系统 G.01~G.07 / 内存管理全完成
v0.9 (2026-04-11) → 模式匹配 M.01~M.09 / 测试 3511 passed
v0.10 (当前)       → 反射系统 (P5) / 完整特性集
```

---

## 贡献指南

欢迎贡献代码！详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feat/新功能`)
3. 提交更改 (`git commit -m 'feat: 添加新功能'`)
4. 推送分支 (`git push origin feat/新功能`)
5. 创建 Pull Request

---

**开始用中文写 C 程序吧！🚀**

*最后更新: 2026-04-11*

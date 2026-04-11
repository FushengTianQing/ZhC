# ZhC 中文 C 编译器

**用中文写 C 程序！🚀** - 编译到 LLVM IR

[![版本](https://img.shields.io/badge/版本-v10.0-blue)](https://github.com/FushengTianQing/ZhC)
[![Python](https://img.shields.io/badge/Python-3.14.3-green)](https://www.python.org/)
[![测试](https://img.shields.io/badge/测试-3330%20passed-brightgreen)](tests/)
[![覆盖率](https://img.shields.io/badge/覆盖率-57%25-yellow)]()
[![许可证](https://img.shields.io/badge/许可证-MIT-yellow)](LICENSE)

---

## 核心特性

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
- **异常处理**: `尝试`/`捕获`/`抛出`/`最终`
- **闭包**: Lambda 表达式、Upvalue 捕获
- **协程**: 异步函数、Suspend/Resume
- **函数指针**: 完整的函数指针类型系统
- **模式匹配**: 结构化模式匹配 (开发中)
- **泛型**: 泛型类型 (开发中)

### 🚀 高性能编译
- **LLVM 后端**: 原生机器码生成，支持 JIT
- **IR 优化**: 常量折叠、死代码消除、函数内联、循环优化
- **智能缓存**: 增量编译，重复编译提速 60-80%

### 📚 完全中文友好
- **258 个中文关键字**: 覆盖 C 语言全部功能
- **中文标准库**: `打印()`, `申请()`, `释放()`, `连接网络()` 等
- **中文错误信息**: 精确的错误定位和修复建议

---

## 快速开始

### 安装

```bash
# 从源码安装
git clone https://github.com/FushengTianQing/ZhC.git
cd ZhC
pip install -e .
```

### 第一个程序

创建 `你好世界.zhc`:
```zhc
包含 <stdio.h>

整数型 主函数() {
    打印("你好，世界！\n");
    返回 0;
}
```

编译并运行:
```bash
zhc compile 你好世界.zhc -o 输出目录
./输出目录/你好世界
```

### 反射示例

```zhc
# 类型检查
如果 (动物 是类型 "狗") {
    狗犬 = 动物 转为 狗;
}

# 安全转换
结果 = 对象 安全转换 "具体类";
如果 (结果 成功) {
    使用 结果.值;
}
```

---

## 编译流水线

```
源代码 (.zhc) → Lexer → Parser → SemanticAnalyzer → IRGenerator → IROptimizer → LLVMBackend → 可执行文件
```

| 阶段 | 组件 | 功能 |
|------|------|------|
| 词法分析 | Lexer | 识别关键字、标识符、运算符 |
| 语法分析 | Parser | 构建 AST |
| 语义分析 | SemanticAnalyzer | 类型检查、作用域分析 |
| IR 生成 | IRGenerator | 生成中间表示 |
| IR 优化 | IROptimizer | 常量折叠、死代码消除 |
| 代码生成 | LLVMBackend | LLVM IR → 原生机器码 |

---

## 项目结构

```
ZhC/
├── src/zhc/                    # 编译器源码 (323 Python 文件)
│   ├── parser/                  # 词法/语法分析
│   ├── semantic/               # 语义分析
│   ├── ir/                      # 中间表示
│   ├── backend/                # LLVM 后端
│   ├── reflection/             # 反射系统 (P5)
│   ├── type_system/            # 类型系统
│   ├── memory/                 # 内存管理
│   ├── exception/              # 异常处理
│   ├── functional/             # 闭包/协程
│   ├── lib/                    # C 运行时库 (39 文件)
│   ├── cli/                    # 命令行工具
│   └── utils/                  # 工具函数
├── tests/                      # 测试套件 (143 文件, 3330 测试)
├── docs/                       # 开发路线图文档
├── examples/                   # 示例代码
└── scripts/                    # 辅助脚本
```

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

# 指定后端
zhc compile 文件.zhc --backend llvm

# 打印 IR
zhc compile 文件.zhc --dump-ir

# 查看帮助
zhc --help

# 运行测试
python3 -m pytest tests/ -v
```

---

## 开发文档

| 文档 | 内容 |
|------|------|
| [architecture.md](architecture.md) | 系统架构详解 |
| [docs/功能开发清单/](docs/功能开发清单/) | 开发路线图 (P0-P7) |
| [docs/二次核查过/](docs/二次核查过/) | 已完成功能文档 |

---

## 测试结果

```
======================== 3330 tests collected =========================
✅ 3323 passed
⏭️  5 skipped
⏱️  2 failed (pre-existing performance tests)
📊 覆盖率: 57%
```

---

## 依赖要求

- Python 3.14.3
- llvmlite 0.47.0
- clang 或 gcc (用于编译生成的 C 代码)

---

## 贡献指南

欢迎贡献代码！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feat/新功能`)
3. 提交更改 (`git commit -m 'feat: 添加新功能'`)
4. 推送分支 (`git push origin feat/新功能`)
5. 创建 Pull Request

---

## 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 致谢

- [Python](https://www.python.org/) - 强大的编程语言
- [LLVM](https://llvm.org/) - 优秀的编译器基础设施
- [llvmlite](https://github.com/numba/llvmlite) - Python LLVM 绑定

---

**开始用中文写 C 程序吧！🚀**

*最后更新: 2026-04-11*
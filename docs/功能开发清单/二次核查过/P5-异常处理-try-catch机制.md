# P5-异常处理-try-catch机制

> **优先级**: P5
> **功能模块**: 异常处理
> **功能名称**: try-catch 机制
> **创建日期**: 2026-04-10
> **状态**: 规划中

## 1. 功能概述

实现中文语法的 `尝试-捕获` 异常处理机制，允许程序捕获和处理运行时错误，提高代码的健壮性和可维护性。

### 1.1 目标

- 提供结构化的异常处理语法
- 支持多类型异常捕获
- 支持 finally 清理逻辑
- 与现有错误处理系统集成

### 1.2 语法设计

```zhc
尝试 {
    // 可能抛出异常的代码
    整数型 结果 = 计算(输入);
} 捕获 (异常类型1 错误) {
    // 处理特定类型异常
    打印("错误: " + 错误.消息);
} 捕获 (异常类型2 错误) {
    // 处理另一种异常
    错误.打印详细信息();
} 默认 {
    // 处理其他所有异常
    打印("未知错误");
} 最终 {
    // 清理代码，始终执行
    关闭资源();
}
```

### 1.3 参考实现

- **C++**: `try-catch` 块 + 异常表
- **Java**: 编译时异常检查 + 栈展开
- **Python**: 异常对象传播机制

---

## 2. 现有项目分析

### 2.1 相关模块

| 模块 | 路径 | 现有功能 |
|------|------|----------|
| 错误处理 | `src/zhc/errors/` | 错误代码定义、格式化 |
| 语义分析 | `src/zhc/semantic/` | 类型检查、作用域管理 |
| IR 生成 | `src/zhc/ir/` | 中间表示构建 |
| 代码生成 | `src/zhc/codegen/` | LLVM IR 生成 |

### 2.2 现有错误处理

```python
# src/zhc/errors/error_codes.py
class ErrorCodeDefinition:
    code: str
    category: str
    severity: str
    brief_message: str
    detailed_message: str
```

### 2.3 缺失功能

- ❌ 异常类型层次结构
- ❌ try-catch 语法支持
- ❌ 异常传播机制
- ❌ 栈展开（stack unwinding）

---

## 3. 技术实现方案

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      源代码层                                │
│  尝试 { ... } 捕获 (异常 e) { ... }                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     解析器层                                 │
│  TryStmt, CatchClause, FinallyClause AST 节点                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     语义分析层                               │
│  - 异常类型检查                                              │
│  - 捕获类型匹配验证                                          │
│  - 作用域分析                                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      IR 层                                  │
│  - ExceptionBlock IR 节点                                    │
│  - Exception handling intrinsics                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     代码生成层                               │
│  - LLVM: invoke + landingpad                                │
│  - Native: setjmp/longjmp 或 SJLJ                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     运行时库                                 │
│  - libzhc_exception.h/c                                      │
│  - 异常对象分配/销毁                                          │
│  - 栈展开回调                                                │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 IR 设计

```python
# src/zhc/ir/nodes/exception.py

class IRTryBlock(IRNode):
    """try 块 IR"""
    body: List[IRNode]
    catch_handlers: List[IRCatchHandler]
    finally_block: Optional[IRNode]

class IRCatchHandler(IRNode):
    """catch 处理器 IR"""
    exception_type: Type
    variable_name: str
    body: List[IRNode]

class IRThrow(IRNode):
    """throw 表达式 IR"""
    exception: IRNode
    exception_type: Optional[Type]
```

### 3.3 关键算法

#### 3.3.1 异常传播算法

```
1. 抛出异常时，设置当前异常对象
2. 从当前栈帧向上查找最近的 try 块
3. 如果找到：
   a. 比较异常类型与 catch 类型列表
   b. 匹配则跳转到对应 catch 块
   c. 不匹配则继续向上传播
4. 如果未找到：
   a. 执行顶层默认处理器
   b. 终止程序并输出错误信息
```

#### 3.3.2 栈展开算法

```
1. 保存所有寄存器状态
2. 调用栈展开回调（destructor）
3. 释放局部对象（调用析构函数）
4. 恢复上一栈帧状态
5. 跳转到 catch 块
```

---

## 4. 实现计划

### 4.1 第一阶段：IR 层支持

**文件变更**:
- `src/zhc/ir/nodes/exception.py` (新建)
- `src/zhc/ir/__init__.py` (更新)

**任务**:
- [ ] 定义 `IRTryBlock`、`IRCatchHandler`、`IRThrow` IR 节点
- [ ] 实现 `IRExceptionContext` 管理异常状态
- [ ] 添加异常相关指令到 IR builder

### 4.2 第二阶段：解析器支持

**文件变更**:
- `src/zhc/parser/lexer.py` (更新)
- `src/zhc/parser/parser.py` (更新)

**任务**:
- [ ] 添加关键字：`尝试`, `捕获`, `默认`, `最终`, `抛出`
- [ ] 实现 `parse_try_statement()` 方法
- [ ] 处理嵌套 try-catch

### 4.3 第三阶段：语义分析

**文件变更**:
- `src/zhc/semantic/checker.py` (更新)

**任务**:
- [ ] 异常类型检查
- [ ] catch 子句类型匹配验证
- [ ] 异常变量作用域分析
- [ ] 禁止在 finally 中 return（警告）

### 4.4 第四阶段：代码生成

**文件变更**:
- `src/zhc/codegen/llvm_backend.py` (更新)

**任务**:
- [ ] LLVM EH intrinsics 集成
- [ ] landingpad 指令生成
- [ ] resume 指令生成
- [ ] 异常表生成

### 4.5 第五阶段：运行时库

**文件变更**:
- `src/zhc/lib/zhc_exception.h` (新建)
- `src/zhc/lib/zhc_exception.c` (新建)
- `src/zhc/lib/exception_zhc.zhc` (新建)

**任务**:
- [ ] 异常对象结构体定义
- [ ] 异常分配/释放函数
- [ ] 栈展开实现
- [ ] 默认异常处理器

---

## 5. API 设计

### 5.1 Python API

```python
# src/zhc/exception/__init__.py

from .exceptions import (
    ZhCException,
    ExceptionHandler,
    try_except,
)

# 使用上下文管理器
with try_except(NullPointerError) as ctx:
    ctx.try_block(lambda: do_something())
    ctx.catch(NullPointerError, lambda e: handle_null(e))

# 手动抛出异常
raise_exception(ErrorCode.E001, "Custom message")
```

### 5.2 C API

```c
// src/zhc/lib/zhc_exception.h

typedef struct ZhCException {
    int error_code;
    char* message;
    void* context;
} ZhCException;

void zhc_throw(int error_code, const char* message);
int zhc_catch(ZhCException* e, int* caught);
```

---

## 6. 测试计划

### 6.1 单元测试

| 测试用例 | 描述 |
|----------|------|
| `test_try_basic` | 基本 try-catch |
| `test_try_multiple_catch` | 多类型 catch |
| `test_try_finally` | finally 清理 |
| `test_try_nested` | 嵌套 try-catch |
| `test_throw_basic` | 基本 throw |
| `test_throw_with_object` | 抛出异常对象 |
| `test_catch_type_matching` | 类型匹配 |
| `test_catch_order` | catch 顺序 |

### 6.2 集成测试

| 测试用例 | 描述 |
|----------|------|
| `test_exception_propagation` | 异常跨函数传播 |
| `test_resource_cleanup` | 资源正确清理 |
| `test_exception_in_constructor` | 构造函数异常 |

---

## 7. 验收标准

- [ ] 支持 `尝试-捕获-默认-最终` 语法
- [ ] 支持多类型异常捕获
- [ ] finally 块始终执行
- [ ] 异常可以跨函数传播
- [ ] 运行时开销 < 5%（无异常时）
- [ ] 生成可调试的异常堆栈
- [ ] 所有单元测试通过
- [ ] 集成测试通过

---

## 8. 风险与挑战

| 风险 | 应对策略 |
|------|----------|
| LLVM EH 复杂性 | 参考 clang 的实现模式 |
| 栈展开性能 | 使用 zero-cost exception 机制 |
| 与析构函数交互 | 确保 RAII 资源正确释放 |
| 嵌套异常 | 使用异常嵌套计数 |

---

## 9. 后续规划

本模块依赖以下模块：
- **P5-异常处理-异常类型系统**: 定义内置异常类型
- **P5-异常处理-异常传播**: 完善异常传播机制

本模块支持以下模块：
- **P5-内存管理-RAII模式**: 异常时自动清理资源
- **P5-函数式-协程支持**: 协程的取消和超时

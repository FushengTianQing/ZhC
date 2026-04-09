# P0-预处理器-#ifdef条件编译

## 基本信息

- **优先级**: P0
- **功能模块**: 预处理器
- **功能名称**: #ifdef/#ifndef 条件编译
- **创建时间**: 2026-04-09

## 功能概述

支持条件编译指令，根据条件决定是否编译特定代码块。

## 语法规格

### C 语言参考

```c
#ifdef IDENTIFIER    // 如果宏已定义
#endif

#ifndef IDENTIFIER   // 如果宏未定义
#endif

#if EXPRESSION      // 如果表达式为真（非零）
#endif

#if defined(IDENTIFIER)  // 等价于 #ifdef
#endif

#if !defined(IDENTIFIER) // 等价于 #ifndef
#endif

// 组合条件
#if defined(A) && !defined(B)
#endif
```

### ZhC 目标语法

```
#ifdef IDENTIFIER
    // 代码块1
#else
    // 代码块2
#endif

#ifndef IDENTIFIER
    // 代码块1
#endif
```

## 功能描述

### 核心行为

1. **#ifdef IDENTIFIER**
   - 检查标识符是否被定义（通过 #define）
   - 已定义：编译后续代码块
   - 未定义：跳过直到 #endif 或 #else

2. **#ifndef IDENTIFIER**
   - #ifdef 的反向逻辑
   - 未定义时编译，已定义时跳过

3. **#else / #elif**
   - 提供条件分支
   - 支持嵌套

4. **#endif**
   - 标记条件编译块的结束

### 组合操作符

- `defined(IDENTIFIER)` - 检查宏是否定义
- 可以组合多个条件：`#if defined(A) || defined(B)`

## 技术实现

### 文件位置

`src/zhc/compiler/preprocessor.py`（新建或扩展）

### 数据结构

```python
@dataclass
class ConditionalBlock:
    start_line: int
    start_col: int
    end_line: Optional[int]
    else_line: Optional[int]
    branches: list[ConditionalBranch]
    current_branch: int = 0

@dataclass
class ConditionalBranch:
    condition: ConditionType  # IfDef | IfNDef | IfExpr
    identifier: Optional[str]
    expression: Optional[str]  # 对于 #if
    enabled: bool
    body: list[Token]

class Preprocessor:
    def __init__(self, ...):
        self.macros: dict[str, Macro] = {}
        self.conditional_stack: list[ConditionalBlock] = []
        self.inactive_branch: bool = False
```

### 核心算法

```python
def _process_ifdef(self, identifier: str, negate: bool) -> bool:
    """处理 #ifdef/#ifndef 指令"""
    defined = identifier in self.macros
    result = defined if not negate else not defined

    # 记录条件块
    block = ConditionalBlock(
        start_line=self._current_line,
        branches=[ConditionalBranch(condition='ifdef', identifier=identifier)],
        enabled=result
    )
    self.conditional_stack.append(block)

    # 设置非活跃状态
    if not result:
        self.inactive_branch = True
        self._skip_to_endif()

    return result

def _skip_to_endif(self):
    """跳过多余代码直到 #endif"""
    # 在词法阶段，条件编译块内的 token 被标记为 skip
    # 在解析阶段，根据条件决定是否包含
    pass
```

## 实现步骤

### 阶段 1：基础框架

1. 创建 `ConditionalBlock` 数据结构
2. 在 `Preprocessor` 类中添加 `conditional_stack`
3. 解析 `#ifdef` / `#ifndef` 指令
4. 实现基本的条件判断逻辑

### 阶段 2：分支处理

1. 添加 `#else` / `#elif` 支持
2. 正确处理嵌套的条件编译块
3. 在 `#endif` 时弹出堆栈

### 阶段 3：高级条件

1. 实现 `defined()` 操作符
2. 支持组合条件 `&&` `||` `!`
3. 支持 `#if EXPRESSION` 整数表达式

### 阶段 4：测试验证

1. 编写单元测试覆盖各种场景
2. 测试嵌套条件编译
3. 测试与 #define 的交互

## 测试用例

```zhc
#define DEBUG_MODE 1

#ifdef DEBUG_MODE
    putln("Debug: 调试模式已启用")
#endif

#ifndef PRODUCTION
    putln("Warning: 非生产环境")
#else
    putln("Production build")
#endif

#if defined(DEBUG_MODE) && !defined(PRODUCTION)
    putln("Development environment")
#endif
```

## 依赖关系

- **前置依赖**: P0-预处理器-#define宏定义（必须先实现宏定义）
- **可选扩展**: P0-预处理器-#include头文件处理
- **后续功能**: 其他预处理器功能

## 状态

- [ ] 待开发

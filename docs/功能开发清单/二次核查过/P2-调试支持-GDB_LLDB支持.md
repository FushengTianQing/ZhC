# P2-调试支持-GDB_LLDB支持

## 基本信息

| 字段 | 值 |
|------|-----|
| **优先级** | P2 |
| **功能模块** | 调试支持 |
| **功能名称** | GDB/LLDB 支持 |
| **依赖项** | DWARF 调试信息 |
| **预计工时** | 2-3 周 |

---

## 1. 开发内容分析

### 1.1 目标概述

实现 GDB 和 LLDB 调试器的完整支持，使开发者能够使用主流调试工具对 ZhC 程序进行源码级调试。

### 1.2 技术背景

#### 调试器对比
| 特性 | GDB | LLDB |
|------|-----|------|
| 平台 | Linux/Unix | macOS/Linux |
| DWARF 支持 | DWARF 2-5 | DWARF 2-5 |
| Python API | ✅ | ✅ |
| 表达式求值 | GDB 内置 | Clang AST |

#### 调试器接口
```
┌─────────────────────────────────────────────────────────┐
│                    Debugger Interface                    │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Breakpoint  │  │  Stepping    │  │  Variables   │   │
│  │ (断点管理)    │  │ (单步执行)   │  │ (变量查看)   │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Backtrace   │  │  Memory      │  │  Expressions │   │
│  │ (调用栈)     │  │ (内存查看)   │  │ (表达式求值) │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 1.3 需求分析

#### 核心需求
1. **断点支持**：源码行断点、函数断点、条件断点
2. **单步执行**：step into、step over、step out
3. **变量查看**：局部变量、全局变量、表达式求值
4. **调用栈**：backtrace、frame 切换

---

## 2. 实现方案

### 2.1 文件结构

```
src/zhc/debugger/
├── __init__.py
├── gdb_support.py           # GDB 支持
├── lldb_support.py          # LLDB 支持
├── breakpoint_manager.py    # 断点管理
├── variable_inspector.py    # 变量检查器
├── expression_evaluator.py  # 表达式求值器
└── pretty_printer.py        # 变量美化打印
```

### 2.2 核心接口设计

#### GDB 支持模块
```python
# src/zhc/debugger/gdb_support.py
class GDBSupport:
    """GDB 调试器支持"""

    @staticmethod
    def generate_gdb_init() -> str:
        """生成 .gdbinit 配置"""
        return """
# ZhC GDB 配置
set print pretty on
set print array on
set print array-indexes on

# 加载 ZhC 美化打印器
source /usr/share/zhc/gdb/zhc_pretty_printers.py
"""

    @staticmethod
    def register_pretty_printers(gdb):
        """注册变量美化打印器"""
        pp = gdb.printing.RegexpCollectionPrettyPrinter("zhc")
        pp.add_printer('string', '^zhc_string$', ZHCStringPrinter)
        pp.add_printer('array', '^zhc_array', ZHCArrayPrinter)
        pp.add_printer('map', '^zhc_map', ZHCMapPrinter)
        gdb.printing.register_pretty_printer(None, pp)
```

#### LLDB 支持模块
```python
# src/zhc/debugger/lldb_support.py
class LLDBSupport:
    """LLDB 调试器支持"""

    @staticmethod
    def generate_lldb_init() -> str:
        """生成 .lldbinit 配置"""
        return """
# ZhC LLDB 配置
settings set target.x86-disassembly-flavor intel
settings set stop-disassembly-display always

# 加载 ZhC 数据格式化器
command script import /usr/share/zhc/lldb/zhc_formatters.py
"""

    @staticmethod
    def register_formatters(debugger):
        """注册数据格式化器"""
        category = debugger.CreateCategory("zhc")
        category.AddTypeSummary(
            lldb.SBTypeNameSpecifier("zhc_string"),
            lldb.SBTypeSummary.CreateWithScriptBody(
                "return zhc_string_summary(valobj)"
            )
        )
```

### 2.3 美化打印器

#### 字符串打印器
```python
class ZHCStringPrinter:
    """ZhC 字符串美化打印器"""

    def __init__(self, val):
        self.val = val

    def to_string(self):
        # 读取字符串内容
        data = self.val['data']
        length = int(self.val['length'])
        return f'"{data.string(length)}"'

    def display_hint(self):
        return 'string'
```

#### 数组打印器
```python
class ZHCArrayPrinter:
    """ZhC 数组美化打印器"""

    def __init__(self, val):
        self.val = val

    def children(self):
        data = self.val['data']
        length = int(self.val['length'])
        for i in range(length):
            yield f'[{i}]', data[i]

    def to_string(self):
        return f"zhc_array<{self.val.type.template_args[0]}>"

    def display_hint(self):
        return 'array'
```

---

## 3. 详细实现计划

### 3.1 Phase 1: GDB 集成 (3-4 天)

- 生成 GDB 兼容的 DWARF 信息
- 实现 GDB 美化打印器
- 编写 GDB 调试脚本

### 3.2 Phase 2: LLDB 集成 (3-4 天)

- 生成 LLDB 兼容的 DWARF 信息
- 实现 LLDB 数据格式化器
- 编写 LLDB 调试脚本

### 3.3 Phase 3: 调试辅助工具 (2-3 天)

- 调试信息验证工具
- 调试器启动脚本生成

---

## 4. 验收标准

- [ ] GDB 可以正确设置断点
- [ ] LLDB 可以正确设置断点
- [ ] 变量美化打印正常工作
- [ ] 调用栈显示正确

---

*文档创建时间: 2026-04-09*
*负责人: 编译器团队*
*版本: 1.0*

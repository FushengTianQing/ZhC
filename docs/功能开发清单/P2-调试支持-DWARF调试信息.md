# P2-调试支持-DWARF调试信息

## 基本信息

| 字段 | 值 |
|------|-----|
| **优先级** | P2 |
| **功能模块** | 调试支持 |
| **功能名称** | DWARF 调试信息 |
| **依赖项** | LLVM IR 生成、目标代码生成 |
| **预计工时** | 4-5 周 |

---

## 1. 开发内容分析

### 1.1 目标概述

实现 DWARF（Debugging With Attributed Record Formats）调试信息生成功能，使编译器能够生成完整的调试信息，支持源码级调试。

### 1.2 技术背景

#### DWARF 版本
| 版本 | 特点 | 用途 |
|------|------|------|
| DWARF 2 | 基础调试信息 | 旧系统 |
| DWARF 3 | 结构体继承支持 | 广泛使用 |
| DWARF 4 | 增强表达力 | 主流版本 |
| DWARF 5 | 现代化重构 | 最新标准 |

#### DWARF 数据结构
```
CU (Compilation Unit)
├── TU (Type Unit)
├── DIE (Debug Information Entry)
│   ├── DW_TAG_variable
│   ├── DW_TAG_subprogram
│   ├── DW_TAG_structure_type
│   └── ...
└── .debug_info section
```

### 1.3 需求分析

#### 核心需求
1. **行号信息**：源码到机器码的映射
2. **变量信息**：变量的位置和作用域
3. **类型信息**：复杂类型的描述
4. **调用栈信息**：函数调用关系

---

## 2. 实现方案

### 2.1 核心架构

```
┌─────────────────────────────────────────────────────────┐
│                    DebugInfoGenerator                    │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  DIBuilder   │  │ DISubprogram │  │ DIVariable   │   │
│  │ (调试信息构建) │ │ (函数信息)   │  │ (变量信息)    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ DICompositeType│ │ DIBasicType │  │ DIScope      │   │
│  │ (复合类型)    │  │ (基本类型)   │  │ (作用域)     │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 2.2 文件结构

```
src/zhc/debug/
├── __init__.py
├── dwarf_builder.py         # DWARF 构建器
├── debug_info_collector.py  # 调试信息收集器
├── line_number_generator.py # 行号生成器
├── type_printer.py          # 类型描述器
├── variable_location.py    # 变量位置追踪
├── scope_tracker.py         # 作用域追踪
└── sections/
    ├── __init__.py
    ├── debug_info.py        # .debug_info
    ├── debug_abbrev.py      # .debug_abbrev
    ├── debug_line.py        # .debug_line
    └── debug_str.py         # .debug_str
```

### 2.3 核心接口设计

#### DwarfBuilder 类
```python
class DwarfBuilder:
    """DWARF 调试信息构建器"""

    def __init__(self, cu: CompilationUnit):
        self.cu = cu
        self.di_builder = DIBuilder()
        self.type_cache = {}

    def create_compile_unit(self, source: str) -> DICompileUnit:
        """创建编译单元"""
        return self.di_builder.create_compile_unit(
            language=DW_LANG_C,
            filename=source,
            producer="ZhC Compiler",
            is_optimized=False,
            flags="",
            runtime_version=0
        )

    def create_subprogram(self, func: Function) -> DISubprogram:
        """创建函数调试信息"""
        subprogram = self.di_builder.create_function(
            scope=self.cu.file,
            name=func.name,
            linkage_name=func.mangled_name,
            file=self.cu.file,
            line=func.line_number,
            type=self._get_function_type(func),
            flags=DINode.FLAG_PROTECTED,
        )
        return subprogram

    def create_variable(self, var: Variable) -> DIVariable:
        """创建变量调试信息"""
        return self.di_builder.create_variable(
            name=var.name,
            scope=var.scope,
            file=var.file,
            line=var.line,
            type=self._get_variable_type(var),
        )
```

---

## 3. 详细实现计划

### 3.1 Phase 1: 行号信息生成 (3-4 天)

```python
class LineNumberGenerator:
    """行号生成器"""

    def generate(self, ir: IRModule) -> DebugLineSection:
        """生成行号表"""
        section = DebugLineSection()

        for func in ir.functions:
            sequence = self._create_line_sequence(func)
            section.add_sequence(sequence)

        return section

    def _create_line_sequence(self, func: Function) -> LineSequence:
        """为函数创建行号序列"""
        # 基本块 → 行号映射
        block_lines = self._map_blocks_to_lines(func)

        # 生成地址映射表
        addr_map = []
        for block in func.blocks:
            for inst in block.instructions:
                if inst.has_debug_location():
                    addr_map.append(LineEntry(
                        address=inst.address,
                        file=inst.location.file,
                        line=inst.location.line,
                        column=inst.location.column,
                    ))

        return LineSequence(entries=addr_map)
```

### 3.2 Phase 2: 变量位置追踪 (4-5 天)

```python
class VariableLocationTracker:
    """变量位置追踪"""

    def track_variable(self, var: Variable,
                       scope: Scope) -> VariableLocation:
        """追踪变量位置"""
        # 1. 查找变量定义
        def_site = self._find_definition_site(var, scope)

        # 2. 追踪变量生命周期
        live_ranges = self._compute_live_ranges(var, scope)

        # 3. 确定存储位置
        location = self._determine_storage(var, live_ranges)

        return VariableLocation(
            name=var.name,
            type=self._get_debug_type(var.type),
            locations=live_ranges,
            is_optimized=self.options.optimize,
        )

    def _determine_storage(self, var: Variable,
                          live_ranges: List[LiveRange]) -> StorageLocation:
        """确定存储位置"""
        if var.is_constant:
            return ConstantLocation(value=var.constant_value)

        if var.is_global:
            return GlobalLocation(name=var.mangled_name)

        # 局部变量
        if self._fits_in_register(live_ranges):
            return RegisterLocation(reg=self._allocate_reg(var))

        return StackLocation(offset=self._allocate_stack_slot(var))
```

### 3.3 Phase 3: 类型描述 (3-4 天)

```python
class TypeDebugInfoGenerator:
    """类型调试信息生成器"""

    def generate_struct_type(self, struct: StructType) -> DICompositeType:
        """生成结构体类型信息"""
        elements = []
        for field in struct.fields:
            elements.append(self.di_builder.create_member(
                name=field.name,
                scope=struct.scope,
                file=field.file,
                line=field.line,
                type=self._get_debug_type(field.type),
                size_in_bits=field.size * 8,
                offset_in_bits=field.offset * 8,
                flags=DINode.FLAG_PUBLIC,
            ))

        return self.di_builder.create_struct_type(
            scope=struct.scope,
            name=struct.name,
            file=struct.file,
            line=struct.line,
            size_in_bits=struct.size * 8,
            flags=DINode.FLAG_APPENDED,
            elements=elements,
        )
```

---

## 4. 验收标准

- [ ] 生成有效的 DWARF 信息
- [ ] 支持 GDB 和 LLDB
- [ ] 行号信息准确
- [ ] 变量位置正确

---

*文档创建时间: 2026-04-09*
*负责人: 编译器团队*
*版本: 1.0*

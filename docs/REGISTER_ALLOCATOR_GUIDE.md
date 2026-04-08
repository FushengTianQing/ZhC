# 寄存器分配器使用指南

## 概述

ZhC 编译器提供了统一的寄存器分配接口，支持多种后端（x86-64、ARM64、WASM、LLVM）。

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                   统一寄存器分配器                        │
│              UnifiedRegisterAllocator                    │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ 线性扫描     │  │ 图着色      │  │ 简单分配    │   │
│  │ LinearScan  │  │ GraphColor  │  │ Simple      │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │ x86-64   │  │ ARM64    │  │ WASM     │  │ LLVM   ││
│  └──────────┘  └──────────┘  └──────────┘  └────────┘│
└─────────────────────────────────────────────────────────┘
```

### 模块位置

| 模块 | 路径 | 说明 |
|------|------|------|
| 寄存器分配算法 | `zhc.ir.register_allocator` | 线性扫描、图着色等核心算法 |
| 后端适配接口 | `zhc.backend.allocator_interface` | 统一 API，支持多后端 |
| 废弃模块（兼容） | `zhc.codegen.*` | 仅用于向后兼容，请勿新代码使用 |

## 快速开始

### 1. 使用工厂函数创建分配器

```python
# 推荐：从 zhc.backend 导入
from zhc.backend import create_allocator, AllocationStrategy

# 创建 x86-64 分配器（线性扫描）
allocator = create_allocator("x86_64", AllocationStrategy.LINEAR_SCAN)

# 创建 ARM64 分配器（图着色）
allocator = create_allocator("arm64", AllocationStrategy.GRAPH_COLOR)

# 创建 WASM 分配器（无寄存器）
allocator = create_allocator("wasm")

# 废弃路径（仅向后兼容）
from zhc.codegen import create_allocator, AllocationStrategy
```

### 2. 准备指令数据

```python
from zhc.backend import Instruction

instructions = [
    Instruction(id=0, opcode="add", defs=[0], uses=[], live_out={0, 1}),
    Instruction(id=1, opcode="sub", defs=[1], uses=[0], live_out={0, 1}),
    Instruction(id=2, opcode="mul", defs=[2], uses=[1], live_out={0, 1, 2}),
    Instruction(id=3, opcode="call", defs=[], uses=[0, 1, 2], live_out=set()),
]
```

### 3. 执行分配

```python
# 执行寄存器分配
result = allocator.allocate(instructions)

# 检查结果
print(f"成功: {result.success}")
print(f"分配数: {len(result.allocations)}")
print(f"溢出数: {len(result.spills)}")
```

### 4. 获取分配结果

```python
# 获取虚拟寄存器对应的物理寄存器
for vreg_id in range(3):
    if allocator.is_spilled(vreg_id):
        slot = allocator.get_spill_slot(vreg_id)
        print(f"v{vreg_id} -> [spill slot {slot}]")
    else:
        reg_name = allocator.get_register_name(vreg_id)
        print(f"v{vreg_id} -> {reg_name}")
```

## 后端集成示例

### C 后端集成

```python
from zhc.backend import X86_64RegisterAllocator, AllocationStrategy

class OptimizedCCodeGenerator:
    """带寄存器分配优化的 C 代码生成器"""

    def __init__(self):
        self.allocator = X86_64RegisterAllocator(AllocationStrategy.LINEAR_SCAN)

    def generate_function(self, func_ir):
        """生成函数代码"""
        # 1. 从 IR 提取指令
        instructions = self._extract_instructions(func_ir)

        # 2. 执行寄存器分配
        result = self.allocator.allocate(instructions)

        # 3. 生成 C 代码（使用分配结果）
        code = self._generate_with_allocation(func_ir, result)

        return code

    def _generate_with_allocation(self, func_ir, alloc_result):
        """使用分配结果生成代码"""
        lines = []

        # 生成局部变量声明
        for vreg_id, reg in alloc_result.allocations.items():
            lines.append(f"// v{vreg_id} -> {reg.name}")

        # 生成溢出变量
        for vreg_id in alloc_result.spills:
            lines.append(f"int spill_{vreg_id}; // spilled")

        return "\n".join(lines)
```

### LLVM 后端集成

```python
from zhc.backend import LLVMRegisterAllocator, AllocationStrategy

class LLVMBackend:
    """LLVM 后端"""

    def __init__(self):
        # LLVM 有自己的寄存器分配器，这里只做接口
        self.allocator = LLVMRegisterAllocator(AllocationStrategy.NONE)

    def generate_llvm_ir(self, func_ir):
        """生成 LLVM IR"""
        # LLVM 会处理寄存器分配
        # 这里只生成 IR，不进行分配
        pass
```

### WASM 后端集成

```python
from zhc.backend import WASMRegisterAllocator

class WASMBackend:
    """WebAssembly 后端"""

    def __init__(self):
        # WASM 使用局部变量，不使用寄存器
        self.allocator = WASMRegisterAllocator()

    def generate_wasm(self, func_ir):
        """生成 WASM 代码"""
        # 1. 提取指令
        instructions = self._extract_instructions(func_ir)

        # 2. 分配局部变量（WASM 的"寄存器"）
        result = self.allocator.allocate(instructions)

        # 3. 生成 WASM 文本格式
        lines = ["(func $main"]

        # 声明局部变量
        for vreg_id in range(self._count_virtual_regs(func_ir)):
            lines.append(f"  (local ${vreg_id} i32)")

        # 生成指令
        for instr in func_ir.instructions:
            wasm_instr = self._translate_instruction(instr)
            lines.append(f"  {wasm_instr}")

        lines.append(")")
        return "\n".join(lines)
```

## 分配策略选择

| 策略 | 复杂度 | 适用场景 | 优点 | 缺点 |
|------|--------|----------|------|------|
| LINEAR_SCAN | O(n log n) | JIT 编译 | 快速，适合实时编译 | 分配质量一般 |
| GRAPH_COLOR | NP 完全 | AOT 编译 | 分配质量高 | 编译时间长 |
| SIMPLE | O(n) | 原型开发 | 极快 | 全部溢出 |
| NONE | - | LLVM/WASM | 依赖后端 | 无优化 |

## 高级用法

### 直接使用 IR 层算法

```python
# 直接使用线性扫描算法
from zhc.ir import LinearScanRegisterAllocator, simple_allocate

instructions = [
    {'def': [0], 'use': [], 'live_out': {0, 1}},
    {'def': [1], 'use': [0], 'live_out': {0, 1}},
]

result = simple_allocate(instructions, num_regs=8)
print(f"成功: {result.success}")
```

### 自定义后端能力

```python
from zhc.backend import UnifiedRegisterAllocator, BackendCapabilities, AllocationStrategy

# 定义自定义后端
custom_caps = BackendCapabilities(
    name="riscv64",
    max_int_regs=32,      # x0-x31
    max_float_regs=32,    # f0-f31
    has_callee_saved=True,
    stack_alignment=16
)

allocator = UnifiedRegisterAllocator(
    strategy=AllocationStrategy.LINEAR_SCAN,
    backend_caps=custom_caps
)
```

### 生成溢出代码

```python
# 检查是否溢出
if allocator.is_spilled(vreg_id):
    # 生成加载代码
    load_code = allocator.generate_spill_code(vreg_id, position=10, is_load=True)
    print(load_code)  # "mov eax, [rbp-8]"

    # 生成存储代码
    store_code = allocator.generate_spill_code(vreg_id, position=15, is_load=False)
    print(store_code)  # "mov [rbp-8], eax"
```

### 批量分配

```python
from zhc.backend import register_for_all_backends, Instruction

instructions = [
    Instruction(id=0, opcode="add", defs=[0], uses=[], live_out={0}),
    Instruction(id=1, opcode="sub", defs=[1], uses=[0], live_out={1}),
]

# 一次性获取所有映射
allocation_map, spill_map = register_for_all_backends(instructions, backend="x86_64")

print("寄存器映射:", allocation_map)
print("溢出映射:", spill_map)
```

## 性能建议

1. **JIT 编译**: 使用 `LINEAR_SCAN` 策略
2. **AOT 编译**: 使用 `GRAPH_COLOR` 策略
3. **LLVM 后端**: 使用 `NONE` 策略（让 LLVM 处理）
4. **WASM 后端**: 使用 `NONE` 策略（使用局部变量）

## 测试

```bash
# 运行寄存器分配器测试
python3 -m pytest tests/test_register_allocator.py -v

# 运行统一接口测试
python3 src/backend/allocator_interface.py
```

## 迁移指南

如果您的代码从 `zhc.codegen` 导入，请更新导入路径：

### 旧代码（废弃）

```python
from zhc.codegen import LinearScanRegisterAllocator
from zhc.codegen import create_allocator, X86_64RegisterAllocator
```

### 新代码（推荐）

```python
# IR 层：直接使用算法
from zhc.ir import LinearScanRegisterAllocator, simple_allocate

# 后端层：使用统一接口
from zhc.backend import create_allocator, X86_64RegisterAllocator
```

## 参考

- [Linear Scan Register Allocation](https://dl.acm.org/doi/10.1145/330249.330250)
- [Graph Coloring Register Allocation](https://en.wikipedia.org/wiki/Register_allocation#Graph-coloring_allocation)
- [LLVM Register Allocator](https://llvm.org/docs/CodeGenerator.html#register-allocator)

# P6-ARM-ARM架构支持 开发分析文档

## 基本信息

| 字段 | 内容 |
|------|------|
| **优先级** | P6 |
| **功能模块** | ARM (Advanced RISC Machines) |
| **功能名称** | ARM 原生代码生成 |
| **文档版本** | 1.0.0 |
| **创建日期** | 2026-04-10 |
| **预计工时** | 约 4-6 周 |

---

## 1. 功能概述

ARM 架构是当今最广泛使用的处理器架构之一，涵盖从嵌入式设备到移动设备再到服务器。本模块实现 ZhC 编译器对 ARM 架构的原生代码生成支持，包括 32 位 ARM (ARMv7) 和 64 位 ARM (ARMv8/AArch64)。

### 1.1 核心目标

- 支持 ARMv7-A (32 位) 和 ARMv8-A (64 位) 架构
- 生成高效的原生机器码
- 利用 ARM 特有的优化指令（NEON、SVE）
- 支持跨平台交叉编译

### 1.2 目标平台

| 架构 | 典型设备 | 市场份额 |
|------|----------|----------|
| ARMv7-A (32-bit) | 树莓派、旧款手机、嵌入式 | 约 30% |
| ARMv8-A (AArch64) | iPhone、Android、M1/M2 Mac、服务器 | 约 70% |

---

## 2. 技术背景

### 2.1 ARM 架构特点

```
┌─────────────────────────────────────────────────────────────┐
│                    ARM 架构特点                              │
├─────────────────────────────────────────────────────────────┤
│  Load/Store 架构    │ 所有运算在寄存器中进行，内存需显式加载    │
│  条件执行           │ 大多数指令可条件执行 (ARMv7)             │
│  多寄存器操作       │ LDM/STM 可一次操作多个寄存器             │
│  向量扩展           │ NEON (128-bit), SVE (可变长度)          │
│  Thumb 指令集       │ 16 位压缩指令 (ARMv7)                   │
│  AAPCS 调用约定     │ ARM Architecture Procedure Call Std    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 寄存器对比

| ARMv7 (32-bit) | ARMv8 (64-bit) | 用途 |
|----------------|----------------|------|
| R0-R3 | X0-X7 | 参数/返回值 |
| R4-R11 | X19-X28 | 被调用者保存 |
| R12 (IP) | X16-X17 | 临时寄存器 |
| SP (R13) | SP (X31) | 栈指针 |
| LR (R14) | LR (X30) | 链接寄存器 |
| PC (R15) | PC | 程序计数器 |
| - | X8 | 间接返回值 |
| - | X18 | 平台寄存器 |
| Q0-Q15 | V0-V31 | NEON/SIMD |

### 2.3 调用约定 (AAPCS64)

```
参数传递规则:
┌─────────────────────────────────────────────────────────────┐
│  X0-X7   │ 前 8 个整数/指针参数                              │
│  V0-V7   │ 前 8 个浮点参数                                   │
│  栈      │ 超过 8 个参数后使用栈传递                         │
│  X8      │ 大结构体返回地址                                  │
│  X0      │ 整数返回值                                        │
│  V0      │ 浮点返回值                                        │
│  X19-X28 │ 被调用者保存 (必须恢复)                           │
│  X0-X18  │ 调用者保存 (可自由使用)                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 详细设计

### 3.1 模块架构

```
src/zhc/backend/arm/
├── __init__.py                 # 模块导出
├── arm_backend.py              # ARM 后端基类
├── armv7_backend.py            # ARMv7 (32-bit) 后端
├── armv8_backend.py            # ARMv8 (64-bit) 后端
├── arm_assembler.py            # 汇编器
├── arm_encoder.py              # 指令编码器
├── arm_register_allocator.py   # 寄存器分配器
├── arm_instruction_selector.py # 指令选择器
├── arm_peephole.py             # 窥孔优化
├── arm_abi.py                  # ABI 实现
├── neon/                       # NEON 向量扩展
│   ├── __init__.py
│   ├── neon_emitter.py         # NEON 指令发射
│   └── neon_patterns.py        # NEON 模式匹配
└── sve/                        # SVE 可伸缩向量扩展
    ├── __init__.py
    └── sve_emitter.py          # SVE 指令发射
```

### 3.2 ARM 后端核心类

#### 3.2.1 ARMBackend 基类

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set
from enum import Enum, auto

class ARMVariant(Enum):
    ARMV7 = auto()      # 32-bit ARM
    ARMV8_32 = auto()   # AArch32 (ARMv8 32-bit mode)
    ARMV8_64 = auto()   # AArch64 (64-bit)

@dataclass
class ARMOptions:
    """ARM 编译选项"""
    variant: ARMVariant = ARMVariant.ARMV8_64
    enable_neon: bool = True          # 启用 NEON
    enable_sve: bool = False          # 启用 SVE
    enable_thumb: bool = False        # 启用 Thumb 指令集
    cpu: str = "generic"              # 目标 CPU
    arch: str = "armv8-a"             # 目标架构
    fpu: str = "neon-fp-armv8"        # FPU 类型
    float_abi: str = "hard"           # 浮点 ABI

class ARMBackend(BackendBase, ABC):
    """ARM 后端抽象基类"""

    def __init__(self, options: ARMOptions):
        self.options = options
        self.reg_allocator = ARMRegisterAllocator(options)
        self.inst_selector = ARMInstructionSelector(options)
        self.assembler = ARMAssembler(options)
        self.peephole = ARMPeepholeOptimizer(options)

    @abstractmethod
    def emit_prologue(self, func: Function) -> List[ARMInstruction]:
        """生成函数序言"""
        pass

    @abstractmethod
    def emit_epilogue(self, func: Function) -> List[ARMInstruction]:
        """生成函数尾声"""
        pass

    @abstractmethod
    def emit_call(self, target: str, args: List[Operand]) -> List[ARMInstruction]:
        """生成函数调用"""
        pass

    def compile_function(self, func: IRFunction) -> ARMFunction:
        """编译单个函数"""
        # 1. 指令选择
        instructions = self.inst_selector.select(func)

        # 2. 寄存器分配
        allocated = self.reg_allocator.allocate(instructions)

        # 3. 窥孔优化
        optimized = self.peephole.optimize(allocated)

        # 4. 汇编
        return self.assembler.assemble(optimized)
```

#### 3.2.2 ARMv8 (AArch64) 后端

```python
class ARMv8Backend(ARMBackend):
    """ARMv8 (AArch64) 后端"""

    def __init__(self, options: ARMOptions):
        super().__init__(options)
        self.variant = ARMVariant.ARMV8_64

    def emit_prologue(self, func: Function) -> List[ARMInstruction]:
        """生成 AArch64 函数序言"""
        instructions = []

        # 保存帧指针和链接寄存器
        instructions.append(
            ARMInstruction("stp", [X29, X30, "[sp, #-16]!"])
        )

        # 设置新的帧指针
        instructions.append(
            ARMInstruction("mov", [X29, SP])
        )

        # 分配栈空间
        stack_size = self._calculate_stack_size(func)
        if stack_size > 0:
            instructions.append(
                ARMInstruction("sub", [SP, SP, f"#{stack_size}"])
            )

        # 保存被调用者保存寄存器
        saved_regs = self.reg_allocator.get_callee_saved(func)
        for reg in saved_regs:
            instructions.append(
                ARMInstruction("str", [reg, "[sp, #offset]"])
            )

        return instructions

    def emit_epilogue(self, func: Function) -> List[ARMInstruction]:
        """生成 AArch64 函数尾声"""
        instructions = []

        # 恢复被调用者保存寄存器
        saved_regs = self.reg_allocator.get_callee_saved(func)
        for reg in reversed(saved_regs):
            instructions.append(
                ARMInstruction("ldr", [reg, "[sp, #offset]"])
            )

        # 恢复栈指针
        stack_size = self._calculate_stack_size(func)
        if stack_size > 0:
            instructions.append(
                ARMInstruction("add", [SP, SP, f"#{stack_size}"])
            )

        # 恢复帧指针和链接寄存器
        instructions.append(
            ARMInstruction("ldp", [X29, X30, "[sp], #16"])
        )

        # 返回
        instructions.append(ARMInstruction("ret", []))

        return instructions

    def emit_call(self, target: str, args: List[Operand]) -> List[ARMInstruction]:
        """生成 AArch64 函数调用"""
        instructions = []

        # 参数传递
        for i, arg in enumerate(args[:8]):
            reg = X[i] if arg.is_integer() else V[i]
            instructions.append(
                ARMInstruction("mov", [reg, arg])
            )

        # 栈参数
        for i, arg in enumerate(args[8:], start=8):
            instructions.append(
                ARMInstruction("str", [arg, "[sp, #offset]"])
            )

        # 调用
        instructions.append(
            ARMInstruction("bl", [target])
        )

        return instructions
```

### 3.3 指令选择

```python
class ARMInstructionSelector:
    """ARM 指令选择器"""

    def __init__(self, options: ARMOptions):
        self.options = options
        self.patterns = self._load_patterns()

    def select(self, ir_func: IRFunction) -> List[SelectionDAG]:
        """将 IR 转换为选择 DAG"""
        dag = SelectionDAG()

        for block in ir_func.blocks:
            for inst in block.instructions:
                dag.extend(self._select_instruction(inst))

        return dag

    def _select_instruction(self, inst: IRInstruction) -> List[SelectionNode]:
        """选择单条指令的实现"""
        opcode = inst.opcode

        if opcode == IROpcode.ADD:
            return self._select_add(inst)
        elif opcode == IROpcode.MUL:
            return self._select_mul(inst)
        elif opcode == IROpcode.LOAD:
            return self._select_load(inst)
        elif opcode == IROpcode.STORE:
            return self._select_store(inst)
        elif opcode == IROpcode.BRANCH:
            return self._select_branch(inst)
        # ... 其他指令

    def _select_add(self, inst: IRInstruction) -> List[SelectionNode]:
        """选择加法指令"""
        # ARM 的 add 指令支持立即数和移位操作数
        lhs, rhs = inst.operands

        if rhs.is_constant() and self._is_imm12(rhs.value):
            # add rd, rn, #imm12
            return [SelectionNode("add", [inst.dest, lhs, rhs])]
        else:
            # add rd, rn, rm
            return [SelectionNode("add", [inst.dest, lhs, rhs])]

    def _select_mul(self, inst: IRInstruction) -> List[SelectionNode]:
        """选择乘法指令"""
        # ARM 有多种乘法指令
        lhs, rhs = inst.operands

        if self.options.enable_neon and inst.type.is_vector():
            # 使用 NEON 向量乘法
            return [SelectionNode("fmul", [inst.dest, lhs, rhs], is_neon=True)]

        # 普通乘法
        return [SelectionNode("mul", [inst.dest, lhs, rhs])]
```

### 3.4 寄存器分配

```python
class ARMRegisterAllocator:
    """ARM 寄存器分配器"""

    # AArch64 寄存器分类
    GENERAL_REGS = [f"x{i}" for i in range(31)]  # X0-X30
    FLOAT_REGS = [f"v{i}" for i in range(32)]    # V0-V31

    # 调用约定
    ARG_REGS = ["x0", "x1", "x2", "x3", "x4", "x5", "x6", "x7"]
    CALLEE_SAVED = ["x19", "x20", "x21", "x22", "x23", "x24", "x25", "x26", "x27", "x28"]
    CALLER_SAVED = ["x0", "x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8", "x9", "x10", "x11", "x12", "x13", "x14", "x15", "x16", "x17", "x18"]

    def __init__(self, options: ARMOptions):
        self.options = options
        self.used_regs: Set[str] = set()
        self.live_ranges: Dict[str, LiveRange] = {}

    def allocate(self, dag: SelectionDAG) -> List[ARMInstruction]:
        """线性扫描寄存器分配"""
        # 1. 计算活跃区间
        self._compute_live_ranges(dag)

        # 2. 按区间起点排序
        sorted_ranges = sorted(
            self.live_ranges.values(),
            key=lambda r: r.start
        )

        # 3. 分配寄存器
        active: List[LiveRange] = []
        free_regs = list(self.GENERAL_REGS)

        for interval in sorted_ranges:
            # 过滤已结束的区间
            self._expire_old_intervals(active, interval.start)

            if len(active) == len(self.GENERAL_REGS):
                # 需要溢出
                self._spill_at_interval(interval, active)
            else:
                # 分配寄存器
                reg = free_regs.pop()
                interval.reg = reg
                active.append(interval)

        return self._rewrite_instructions(dag)

    def _spill_at_interval(self, interval: LiveRange, active: List[LiveRange]):
        """将区间溢出到栈"""
        # 选择一个活跃区间溢出
        spill = max(active, key=lambda r: r.end)

        if spill.end > interval.end:
            # 溢出 spill
            interval.reg = spill.reg
            spill.reg = None
            spill.spill_slot = self._allocate_spill_slot()
            active.remove(spill)
            active.append(interval)
        else:
            # 溢出当前区间
            interval.spill_slot = self._allocate_spill_slot()
```

### 3.5 NEON 向量支持

```python
class NEONEmitter:
    """NEON 指令发射器"""

    def __init__(self, options: ARMOptions):
        self.options = options

    def emit_vector_add(self, dest: str, src1: str, src2: str,
                        element_type: str = "f32") -> ARMInstruction:
        """发射向量加法"""
        # fadd v0.4s, v1.4s, v2.4s (4 个 32 位浮点)
        suffix = self._get_neon_suffix(element_type)
        return ARMInstruction(f"fadd", [dest, src1, src2], suffix=suffix)

    def emit_vector_load(self, dest: str, addr: str,
                         count: int = 4, element_type: str = "f32") -> ARMInstruction:
        """发射向量加载"""
        # ld1 {v0.4s}, [x1]
        suffix = f"{count}{element_type[0]}"
        return ARMInstruction("ld1", [f"{{{dest}.{suffix}}}", f"[{addr}]"])

    def emit_vector_store(self, src: str, addr: str,
                          count: int = 4, element_type: str = "f32") -> ARMInstruction:
        """发射向量存储"""
        suffix = f"{count}{element_type[0]}"
        return ARMInstruction("st1", [f"{{{src}.{suffix}}}", f"[{addr}]"])

    def emit_vector_dot_product(self, dest: str, src1: str, src2: str,
                                accum: str = None) -> ARMInstruction:
        """发射向量点积 (ARMv8.2+)"""
        if accum:
            # fmla v0.4s, v1.4s, v2.4s (累加)
            return ARMInstruction("fmla", [dest, src1, src2])
        else:
            # 需要先清零再累加
            return [
                ARMInstruction("movi", [dest, "#0"]),
                ARMInstruction("fmla", [dest, src1, src2]),
            ]
```

---

## 4. 实现方案

### 4.1 第一阶段：基础框架

1. **定义 ARM 指令集**
   - ARMv8 基础指令
   - 指令编码格式
   - 操作数类型

2. **实现汇编器**
   - 指令编码器
   - 重定位处理
   - ELF 目标文件生成

3. **基本代码生成**
   - 函数序言/尾声
   - 算术运算
   - 内存访问

### 4.2 第二阶段：完整支持

1. **控制流**
   - 条件分支
   - 循环
   - switch 语句

2. **函数调用**
   - 参数传递
   - 返回值
   - 尾调用优化

3. **复杂类型**
   - 结构体
   - 数组
   - 字符串

### 4.3 第三阶段：优化

1. **指令调度**
   - 流水线优化
   - 延迟槽填充

2. **窥孔优化**
   - 冗余加载消除
   - 常量折叠

3. **NEON 向量化**
   - 自动向量化
   - SIMD 模式识别

### 4.4 第四阶段：ARMv7 支持

1. **Thumb 指令集**
   - Thumb-2 支持
   - 模式切换

2. **条件执行**
   - IT 块生成
   - 条件码优化

---

## 5. 类型映射

### 5.1 中文类型 → ARM 类型

| ZhC 类型 | ARM 类型 | 寄存器 | 字节大小 |
|----------|----------|--------|----------|
| 整数型 | int32_t | W0-W30 | 4 |
| 长整数型 | int64_t | X0-X30 | 8 |
| 浮点型 | float | S0-S31 | 4 |
| 双精度型 | double | D0-D31 | 8 |
| 字符型 | uint32_t | W 寄存器 | 4 |
| 布尔型 | uint8_t | W 寄存器 | 1 |
| 指针型 | void* | X 寄存器 | 8 |

### 5.2 NEON 向量类型

| ZhC 类型 | NEON 类型 | 寄存器 | 元素数 |
|----------|-----------|--------|--------|
| 浮点数组[4] | float32x4_t | V0-V31 | 4 |
| 浮点数组[8] | float32x8_t | V0-V31 (pair) | 8 |
| 整数数组[4] | int32x4_t | V0-V31 | 4 |
| 整数数组[8] | int32x8_t | V0-V31 (pair) | 8 |

---

## 6. 测试策略

### 6.1 单元测试

| 测试类别 | 测试内容 | 测试用例数 |
|----------|----------|------------|
| 指令编码 | 所有指令的正确编码 | ~200 |
| 寄存器分配 | 分配正确性 | ~50 |
| 函数调用 | 参数传递 | ~40 |
| 控制流 | 分支和循环 | ~60 |

### 6.2 集成测试

```python
def test_arm_cross_compile():
    """测试交叉编译"""
    # 在 x86 主机上编译 ARM 代码
    zhc compile input.zhc --target arm64 -o output

    # 使用 QEMU 运行
    result = qemu_run("output", args=["test"])
    assert result.exit_code == 0
```

### 6.3 性能基准测试

- 使用 `perf` 工具测量性能
- 与 GCC/Clang 生成的代码对比
- NEON 向量化效果测试

---

## 7. 已知限制和风险

### 7.1 架构限制

| 限制 | 影响 | 缓解方案 |
|------|------|----------|
| 32 位地址空间 | ARMv7 最大 4GB 内存 | 建议使用 ARMv8 |
| 条件执行复杂 | ARMv7 条件执行与 ARMv8 不同 | 分架构处理 |
| NEON 版本差异 | 不同 ARM 版本 NEON 能力不同 | 运行时检测 |

### 7.2 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| ABI 兼容性 | 低 | 高 | 严格遵循 AAPCS |
| 指令编码错误 | 中 | 高 | 使用 LLVM 作为参考 |
| 性能回归 | 中 | 中 | 建立性能基准 |

---

## 8. 参考资料

- [ARM Architecture Reference Manual](https://developer.arm.com/documentation/)
- [AAPCS64 Specification](https://github.com/ARM-software/abi-aa)
- [NEON Intrinsics Reference](https://developer.arm.com/architectures/instruction-sets/intrinsics/)
- [LLVM ARM Backend](https://llvm.org/docs/CodeGenerator.html#arm-backend)

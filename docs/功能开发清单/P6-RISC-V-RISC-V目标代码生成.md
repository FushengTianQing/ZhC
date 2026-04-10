# P6-RISC-V-RISC-V目标代码生成 开发分析文档

## 基本信息

| 字段 | 内容 |
|------|------|
| **优先级** | P6 |
| **功能模块** | RISC-V |
| **功能名称** | RISC-V 架构支持 |
| **文档版本** | 1.0.0 |
| **创建日期** | 2026-04-10 |
| **预计工时** | 约 4-5 周 |

---

## 1. 功能概述

RISC-V 是一个开放的指令集架构 (ISA)，近年来在嵌入式系统、物联网、服务器和高性能计算领域迅速普及。作为完全开放的 ISA，RISC-V 为 ZhC 编译器提供了重要的目标平台支持。

### 1.1 核心目标

- 支持 RISC-V 32 位 (RV32) 和 64 位 (RV64) 架构
- 支持标准扩展：M (乘法)、A (原子)、F (单精度浮点)、D (双精度浮点)、C (压缩)
- 生成高效的目标代码
- 支持嵌入式和通用计算场景

### 1.2 RISC-V 优势

| 特性 | 描述 |
|------|------|
| **开放标准** | 无许可费用，指令集完全开放 |
| **模块化设计** | 基础 + 扩展，可按需选择 |
| **简洁设计** | 易于理解和实现 |
| **广泛支持** | GCC, LLVM, Linux, GCC 等生态完善 |
| **新兴生态** | 物联网、加速器、服务器等领域快速发展 |

---

## 2. 技术背景

### 2.1 RISC-V 架构特点

```
┌─────────────────────────────────────────────────────────────┐
│                    RISC-V 架构特点                            │
├─────────────────────────────────────────────────────────────┤
│  Load/Store 架构   │ 运算指令仅操作寄存器                     │
│  固定指令长度       │ 32 位基础指令，可选 16/48/64 位扩展       │
│  通用寄存器        │ 32 个整数寄存器 + PC                      │
│  可选浮点寄存器     │ 32 个 (F/D 扩展)                        │
│  无条件跳转        │ 专用跳转指令，无需延迟槽                    │
│  精简设计          │ 基础指令少于 50 条                        │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 寄存器约定 (RV64GC)

| 寄存器 | 别名 | 用途 | 保存者 |
|--------|------|------|--------|
| x0 | zero | 硬编码为 0 | - |
| x1 | ra | 返回地址 | 调用者保存 |
| x2 | sp | 栈指针 | 被调用者保存 |
| x3 | gp | 全局指针 | - |
| x4 | tp | 线程指针 | - |
| x5-x7 | t0-t2 | 临时寄存器 | 调用者保存 |
| x8 | s0/fp | 保存寄存器/帧指针 | 被调用者保存 |
| x9 | s1 | 保存寄存器 | 被调用者保存 |
| x10-x17 | a0-a7 | 函数参数/返回值 | 调用者保存 |
| x18-x27 | s2-s11 | 保存寄存器 | 被调用者保存 |
| x28-x31 | t3-t6 | 临时寄存器 | 调用者保存 |
| f0-f7 | ft0-ft7 | 浮点临时 | 调用者保存 |
| f8-f9 | fs0-fs1 | 浮点保存 | 被调用者保存 |
| f10-f17 | fa0-fa7 | 浮点参数/返回值 | 调用者保存 |
| f28-f31 | fs2-fs11 | 浮点保存 | 被调用者保存 |

### 2.3 RISC-V 扩展

| 扩展 | 描述 | 重要性 |
|------|------|--------|
| M | 整数乘除法 | 必需 |
| A | 原子操作 | 推荐 |
| F | 单精度浮点 | 推荐 |
| D | 双精度浮点 | 推荐 |
| C | 压缩指令 (16-bit) | 优化体积 |
| V | 向量操作 | 未来扩展 |
| Zicsr | 控制状态寄存器 | 调试必需 |
| Zifencei | 指令 fence | 内存模型必需 |

---

## 3. 详细设计

### 3.1 模块架构

```
src/zhc/backend/riscv/
├── __init__.py                 # 模块导出
├── riscv_backend.py            # RISC-V 后端主类
├── riscv_assembler.py          # 汇编器
├── riscv_encoder.py            # 指令编码器
├── riscv_register_allocator.py # 寄存器分配器
├── riscv_instruction_selector.py # 指令选择器
├── riscv_peephole.py           # 窥孔优化
├── riscv_abi.py               # ABI 实现
├── riscv_elf.py               # ELF 目标文件生成
├── riscv_csr.py               # CSR 操作
├── riscv_atomics.py           # 原子操作支持
├── riscv_vector.py            # 向量扩展 (V)
└── riscv_float.py             # 浮点运算
```

### 3.2 RISC-V 后端核心类

```python
@dataclass
class RISC VOptions:
    """RISC-V 编译选项"""
    xlen: int = 64                       # 32 或 64
    extensions: Set[str] = field(
        default_factory=lambda: {'m', 'a', 'f', 'd', 'c'}
    )
    arch: str = "rv64gc"                # 目标架构
    enable_compressed: bool = True       # 启用压缩指令
    enable_pulp: bool = False           # 启用 PULP 扩展
    enable_vext: bool = False           # 启用向量扩展
    code_model: str = "medium"           # 代码模型
    pic: bool = True                    # 位置无关代码

class RISC VBackend(BackendBase):
    """RISC-V 后端"""

    def __init__(self, options: RISC VOptions):
        self.options = options
        self.reg_allocator = RISC VRegisterAllocator(options)
        self.inst_selector = RISC VInstructionSelector(options)
        self.assembler = RISC VAssembler(options)

    def compile_function(self, func: IRFunction) -> RISC VFunction:
        """编译单个函数"""
        # 1. 指令选择
        instructions = self.inst_selector.select(func)

        # 2. 寄存器分配
        allocated = self.reg_allocator.allocate(instructions)

        # 3. 窥孔优化
        optimized = self._peephole.optimize(allocated)

        # 4. 生成机器码
        return self.assembler.assemble(optimized)
```

### 3.3 指令选择器

```python
class RISC VInstructionSelector:
    """RISC-V 指令选择器"""

    # RISC-V 指令格式
    # R 类型: opcode(7) | rd(5) | funct3(3) | rs1(5) | rs2(5) | funct7(7)
    # I 类型: opcode(7) | rd(5) | funct3(3) | rs1(5) | imm12(12)
    # S 类型: opcode(7) | imm[4:0](5) | funct3(3) | rs1(5) | rs2(5) | imm[11:5](7)
    # U 类型: opcode(7) | rd(5) | imm31:12(20)
    # J 类型: opcode(7) | imm[19:12](8) | imm[11](1) | imm[10:1](10) | imm[20](1) | rd(5) | imm[30:21](10)

    def _select_add(self, inst: IRInstruction) -> List[SelectionNode]:
        """选择加法指令"""
        dest, lhs, rhs = inst.dest, inst.operands[0], inst.operands[1]

        if rhs.is_constant() and self._is_legal_imm(rhs.value):
            # addi rd, rs1, imm
            return [SelectionNode("addi", [dest, lhs, rhs])]
        elif rhs.is_register():
            # add rd, rs1, rs2
            return [SelectionNode("add", [dest, lhs, rhs])]
        else:
            # 加载大常量到临时寄存器
            nodes = [
                SelectionNode("lui", [dest, self._upper_imm(rhs.value)]),
                SelectionNode("addi", [dest, dest, self._lower_imm(rhs.value)]),
            ]
            return nodes

    def _select_load(self, inst: IRInstruction) -> List[SelectionNode]:
        """选择加载指令"""
        dest, base, offset = inst.dest, inst.operands[0], inst.operands[1]

        # 根据加载类型选择指令
        if inst.mem_type == 'byte':
            return [SelectionNode("lb", [dest, base, offset])]
        elif inst.mem_type == 'half':
            return [SelectionNode("lh", [dest, base, offset])]
        elif inst.mem_type == 'word':
            if self.options.xlen == 64:
                return [SelectionNode("ld", [dest, base, offset])]
            else:
                return [SelectionNode("lw", [dest, base, offset])]
        elif inst.mem_type == 'float':
            if inst.f_type == 'single':
                return [SelectionNode("flw", [dest, base, offset])]
            else:
                return [SelectionNode("fld", [dest, base, offset])]

    def _select_branch(self, inst: IRInstruction) -> List[SelectionNode]:
        """选择分支指令"""
        cond = inst.cond
        target = inst.target

        if cond == IRBranchCond.EQ:
            return [SelectionNode("beq", [inst.src1, inst.src2, target])]
        elif cond == IRBranchCond.NE:
            return [SelectionNode("bne", [inst.src1, inst.src2, target])]
        elif cond == IRBranchCond.LT:
            return [SelectionNode("blt", [inst.src1, inst.src2, target])]
        elif cond == IRBranchCond.ULT:
            return [SelectionNode("bltu", [inst.src1, inst.src2, target])]
        # ... 其他条件分支
```

### 3.4 寄存器分配

```python
class RISC VRegisterAllocator:
    """RISC-V 寄存器分配器"""

    # 整数寄存器
    INT_REGS = [f"x{i}" for i in range(32)]
    INT_REGS_NAMES = ['zero', 'ra', 'sp', 'gp', 'tp'] + \
                     [f't{i}' for i in range(7)] + \
                     ['s0', 's1'] + \
                     [f'a{i}' for i in range(8)] + \
                     [f's{i}' for i in range(2, 12)] + \
                     [f't{i}' for i in range(3, 7)]

    # 浮点寄存器
    FP_REGS = [f"f{i}" for i in range(32)]

    # 调用约定
    ARG_REGS = ["a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7"]
    RETURN_REGS = ["a0", "a1"]
    CALLEE_SAVED = ["s0", "s1"] + [f"s{i}" for i in range(2, 12)]
    FP_CALLEE_SAVED = ["fs0", "fs1"] + [f"fs{i}" for i in range(2, 12)]

    def allocate(self, dag: SelectionDAG) -> List[RISC VInstruction]:
        """线性扫描寄存器分配"""
        # 类似 ARM 的实现
        pass
```

### 3.5 压缩指令支持

```python
class CompressedInstructionEmitter:
    """RVC (RISC-V Compressed) 指令发射器"""

    # 压缩指令映射
    EXPAND_TO_COMPRESSED = {
        'addw': 'c.addw',      # 需要 RV64C
        'sub': 'c.sub',
        'and': 'c.and',
        'or': 'c.or',
        'xor': 'c.xor',
        'lw': 'c.lw',
        'ld': 'c.ld',          # RV64C
        'sw': 'c.sw',
        'sd': 'c.sd',          # RV64C
        'jalr': 'c.jalr',
        'jr': 'c.jr',
        'jal': 'c.j',
        'j': 'c.j',
        'beq': 'c.beqz',
        'bne': 'c.bnez',
    }

    def try_compress(self, inst: RISC VInstruction) -> Optional[RISC VInstruction]:
        """尝试将指令压缩为 16 位"""
        # 检查是否满足压缩条件
        if not self.options.enable_compressed:
            return None

        if inst.mnemonic not in self.EXPAND_TO_COMPRESSED:
            return None

        # 检查操作数是否满足压缩约束
        if not self._can_compress(inst):
            return None

        # 转换为压缩指令
        return self._compress(inst)
```

---

## 4. 实现方案

### 4.1 第一阶段：基础框架

1. **定义 RISC-V 指令集**
   - 基础指令 (I)
   - 整数乘除 (M)
   - 压缩指令 (C)

2. **实现汇编器**
   - 指令编码
   - ELF 目标文件

3. **基本代码生成**
   - 函数序言/尾声
   - 算术运算
   - 内存访问

### 4.2 第二阶段：完整支持

1. **函数调用**
   - 参数传递
   - 返回值
   - 尾调用

2. **浮点支持**
   - F 扩展
   - D 扩展

3. **原子操作**
   - A 扩展
   - 同步原语

### 4.3 第三阶段：优化

1. **压缩指令**
   - 自动压缩
   - 体积优化

2. **窥孔优化**
   - 冗余消除
   - 立即数优化

3. **指令调度**
   - 流水线优化

### 4.4 第四阶段：高级扩展

1. **向量扩展 (V)**
   - 向量指令支持
   - 自动向量化

2. **位操作扩展**
   - Zbb, Zbc 等

---

## 5. 类型映射

### 5.1 中文类型 → RISC-V 类型

| ZhC 类型 | RISC-V 类型 | 寄存器 | 字节大小 |
|----------|-------------|--------|----------|
| 整数型 | int32_t | x 寄存器 | 4 |
| 长整数型 | int64_t | x 寄存器 (RV64) | 8 |
| 浮点型 | float | f 寄存器 | 4 |
| 双精度型 | double | f 寄存器 | 8 |
| 字符型 | uint32_t | x 寄存器 | 4 |
| 布尔型 | uint8_t | x 寄存器 | 1 |
| 指针型 | void* | x 寄存器 | 8 (RV64) |

### 5.2 特殊类型映射

```python
class RISC VTypeMapper:
    """RISC-V 类型映射器"""

    def map_type(self, zhc_type: Type) -> RISC VType:
        if isinstance(zhc_type, IntegerType):
            if zhc_type.width <= 32:
                return RISC VType.I32 if self.options.xlen == 32 else RISC VType.I64
            else:
                return RISC VType.I64
        elif isinstance(zhc_type, FloatType):
            if zhc_type.width == 32:
                return RISC VType.F32
            else:
                return RISC VType.F64
        elif isinstance(zhc_type, PointerType):
            return RISC VType.I64 if self.options.xlen == 64 else RISC VType.I32
        elif isinstance(zhc_type, BoolType):
            return RISC VType.I8
        else:
            raise UnsupportedTypeError(zhc_type)
```

---

## 6. 测试策略

### 6.1 单元测试

| 测试类别 | 测试内容 | 测试用例数 |
|----------|----------|------------|
| 指令编码 | 所有指令的正确编码 | ~150 |
| 寄存器分配 | 分配正确性 | ~40 |
| 函数调用 | 参数传递 | ~30 |
| 压缩指令 | 压缩/解压缩 | ~50 |

### 6.2 集成测试

```python
def test_riscv_elf_output():
    """测试 ELF 文件生成"""
    result = zhc.compile("test.zhc", target="riscv64")
    elf = ELFFile(result.binary)

    assert elf.machine == EM_RISCV
    assert elf.arch == "rv64gc"

def test_riscv_spike_run():
    """使用 Spike 模拟器测试"""
    zhc.compile("test.zhc", target="riscv64", output="test")
    result = spike_run("test", args=["arg1"])
    assert result.exit_code == 0
```

---

## 7. 参考资料

- [RISC-V ISA Specification](https://riscv.org/technical/specifications/)
- [RISC-V Assembly Programmer's Manual](https://github.com/riscv/riscv-asm-manual)
- [RISC-V ELF Specification](https://github.com/riscv/riscv-elf-psabi-doc)
- [Spike RISC-V Simulator](https://github.com/riscv-software-src/riscv-isa-sim)
- [LLVM RISC-V Backend](https://llvm.org/docs/CodeGenerator.html#id8)

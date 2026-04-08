# LLVM 与 WASM 后端集成方案

> 文档版本：1.0
> 创建日期：2026-04-08
> 作者：远
> 目标：为 ZhC 编译器设计完整的 LLVM 和 WebAssembly 后端集成路径

---

## 一、现状分析

### 1.1 现有后端资产

| 后端 | 文件位置 | 成熟度 | 局限性 |
|------|----------|--------|--------|
| **CBackend** | `src/ir/c_backend.py` | ✅ 完整 | 依赖外部 C 编译器，无 JIT |
| **LLVMPrinter** | `src/ir/llvm_backend.py` | ⚠️ 存疑 | 文本格式 `.ll` 生成器，有 bug；无 bitcode；未集成 llvmlite |
| **WASMBackend** | `src/backend/wasm_backend.py` | ⚠️ 存疑 | 仅为 Emscripten wrapper；非原生 WASM 生成 |

### 1.2 核心差距

**LLVM 方向：**
- `LLVMPrinter` 输出的是 LLVM IR **文本**（`.ll`），不是真正的 LLVM bitcode
- 没有调用任何 LLVM C API（llvmlite）
- 无法做 JIT 编译、无法链接多个模块、无法做 LLVM 原生优化
- `llvm_backend.py` 第 142、152 行存在 bug：引用 `Instruction` 应为 `IRInstruction`

**WASM 方向：**
- 现有 `WASMBackend` 是对 `emcc` 的包装，非原生生成
- 无法在编译器内部生成 WASM 指令
- 缺少 WASM 专用的类型系统和指令映射
- 生成的 WASM 无法脱离 Emscripten 独立运行

---

## 二、目标架构

### 2.1 后端层次全景

```
ZhC 源代码
    │
    ▼
┌─────────────────┐
│  Lexer / Parser │  ← 已有
└────────┬────────┘
         ▼
┌─────────────────┐
│  Semantic/Type  │  ← 已有
└────────┬────────┘
         ▼
┌─────────────────┐
│      IR         │  ← 已有（IRProgram / IRFunction / IRBasicBlock / IRInstruction）
└────────┬────────┘
         │
    ┌────┴────┬───────────┐
    ▼         ▼           ▼
┌────────┐ ┌────────┐ ┌──────────────┐
│CBackend│ │LLVMBack │ │  WASMBackend │
│ (已有) │ │  (新建) │ │    (新建)    │
└───┬────┘ └────┬───┘ └──────┬───────┘
    ▼           ▼            ▼
   .c        .ll/.bc       .wasm
    │           │            │
    ▼           ▼            ▼
  gcc/clang   llvm-link   (native)
              llvm-opt
               lli(JIT)
```

### 2.2 LLVM 后端目标能力

1. **文本 LLVM IR 输出**（`.ll`）— 修复+增强现有 `LLVMPrinter`
2. **LLVM Bitcode 输出**（`.bc`）— 通过 llvmlite 生成真正的 bitcode
3. **JIT 编译执行** — 使用 llvmlite 的 JIT 编译器直接运行 IR
4. **原生优化 Pass** — 通过 llvmlite 调用 LLVM 优化流水线（`-O2`, `-O3`）
5. **多模块链接** — 支持 LLVM linker 链接多个 `.bc` 文件

### 2.3 WASM 后端目标能力

1. **WASM Text Format 输出**（`.wat`）— 可读的 WASM 文本格式
2. **原生 WASM Binary 输出**（`.wasm`）— 二进制格式，无需 Emscripten
3. **Browser/Node.js 直接运行** — 生成的 `.wasm` 可直接在浏览器或 Node 中运行
4. **Emscripten 可选集成** — 作为高级优化选项（`--emcc`）而非唯一路径

---

## 三、技术方案

### 3.1 LLVM 后端技术选型

**选型结论：使用 `llvmlite`（LLVM 12）**

| 方案 | 优点 | 缺点 |
|------|------|------|
| `llvmlite` | 纯 Python，安装简单；与 LLVM 12 绑定稳定；pytest 生态支持 | Python 独有 |
| `python-llvm` | 成熟 | LLVM 版本老旧（LLVM 3.x），多年未更新 |
| `numba` (内部 LLVM) | JIT 能力强 | 不可独立控制 LLVM 版本 |
| 自行绑定 LLVM C API | 完全可控 | 工期不可控，涉及 C FFI |

**`llvmlite` 依赖：**
```
llvmlite>=0.39.0  # Python 3.8+
llvm>=12.0.0      # 系统级依赖（macOS: brew install llvm）
```

**中文类型 → LLVM 类型映射（扩展现有 `ZHCT_TO_LLVM`）：**

```python
ZHCT_TO_LLVM = {
    # 基础类型
    "整数型": "i32",       "i32": "i32",      "i64": "i64",
    "字节型": "i8",         "i8": "i8",        "i16": "i16",
    "字符型": "i8",
    "布尔型": "i1",
    "浮点型": "float",      "单精度浮点型": "float",
    "双精度浮点型": "double",
    "空型": "void",
    # 指针/数组
    "字符串型": "i8*",
    # 结构体：需要按名称查找 layout
    # 泛型：需要具体化后映射
}
```

### 3.2 WASM 后端技术选型

**选型结论：使用 `wasm-tools`（Rust 实现）+ Python bindings**

| 方案 | 优点 | 缺点 |
|------|------|------|
| `wasm-tools` (Rust) | 权威实现，W3C 维护；支持 wat↔wasm 互转；活跃开发 | 需要系统级安装 |
| `watson` | 纯 Python | 功能有限，不支持二进制生成 |
| `wasmtime` Python binding | 支持 JIT | 主要用于运行，非生成 |
| `Emscripten`（现有） | 成熟 | 笨重；不是 WASM 生成器，是 C→WASM 工具链 |

**WASM 二进制生成路径：**
```
ZHC IR → WAT (text) → wasm-tools encode → .wasm (binary)
```

**WASM 类型映射：**

| ZHC 类型 | WASM 价值类型 | WASM 存储类型 |
|----------|--------------|--------------|
| 整数型 / i32 | `i32` | `i32.store` |
| 字节型 / i8 | `i32` | `i32.store8` |
| 布尔型 | `i32` | `i32.store` |
| 字符型 | `i32` | `i32.store` |
| 浮点型 / float | `f32` | `f32.store` |
| 双精度浮点型 / double | `f64` | `f64.store` |
| 字符串型 | `i32` (ptr+len) | 内存布局 |
| 数组 | `i32` (linear memory) | 指针+长度 |

**WASM 指令集覆盖（优先级排序）：**

| 阶段 | 覆盖指令 | 优先级 |
|------|----------|--------|
| P0 | i32/f32/f64 算术、比较、load/store、call、br/br_if、return | P0 必须 |
| P1 | i64 算术、select、local.get/set/te录tee、global.get/set | P1 重要 |
| P2 | memory.size/memory.grow、ref.func、table（函数引用） | P2 完善 |
| P3 | SIMD (v128)、原子操作、异常处理 | P3 高级 |

---

## 四、LLVM 后端实现方案

### 4.1 目录结构

```
src/
  ir/
    llvm_backend.py       ← 重写为 LLVMBackend 类（替换现有的 LLVMPrinter）
    llvm_types.py         ← 新增：LLVM 类型映射器
    llvm_values.py        ← 新增：LLVM Value 包装器
    llvm_module.py        ← 新增：LLVMLink 类，IRProgram → llvmlite Module
    llvm_jit.py           ← 新增：JIT 编译器
    llvm_optimize.py      ← 新增：LLVM 优化 Pass 集成
    wasm_backend.py       ← 新增：WASMBackend（原生，非 Emscripten wrapper）
    wasm_ir.py            ← 新增：WASM IR 定义（指令、函数、模块）
    wasm_codegen.py       ← 新增：WASM 代码生成器（ZHC IR → WAT）
    wasm_binary.py        ← 新增：WAT → WASM 二进制编码器
```

### 4.2 LLVMBackend 类设计

```python
# src/ir/llvm_backend.py（重写）

from llvmlite import ir, binding, llvm
from llvmlite.ir import Module, Function, IRBuilder

class LLVMBackend:
    """
    ZHC IR → LLVM IR/Bitcode/JIT 编译器后端

    支持三种输出模式：
    - text: 输出人类可读的 .ll LLVM IR 文本
    - bitcode: 输出 LLVM bitcode (.bc)
    - jit: 直接 JIT 编译执行
    """

    def __init__(self, optimization_level: int = 2):
        self.module = ir.Module(name="zhc_module")
        self.optimization_level = optimization_level
        self._named_types: Dict[str, ir.Type] = {}
        self._named_values: Dict[str, ir.Value] = {}
        self._string_constants: List[Tuple[str, ir.GlobalValue]] = []

    def generate(self, ir_program: IRProgram) -> str:
        """生成 LLVM IR 文本（兼容现有接口）"""
        self._create_types(ir_program)
        self._create_globals(ir_program)
        self._create_functions(ir_program)
        return str(self.module)

    def generate_bitcode(self, ir_program: IRProgram) -> bytes:
        """生成 LLVM Bitcode"""
        text_ir = self.generate(ir_program)
        return self._compile_to_bitcode(text_ir)

    def jit_execute(self, ir_program: IRProgram, entry_func: str):
        """JIT 编译并执行入口函数"""
        # 使用 llvmlite 的 JITCompiler
        binding.initialize()
        binding.initialize_native_target()
        # ... 完整的 JIT 编译流程
```

### 4.3 关键实现细节

#### 4.3.1 类型转换（`llvm_types.py`）

```python
# 中文类型 → llvmlite.ir.Type
def zhc_type_to_llvm(zhc_ty: str, ctx: ir.Context) -> ir.Type:
    table = {
        "整数型": ir.IntType(32),
        "字节型": ir.IntType(8),
        "布尔型": ir.IntType(1),
        "浮点型": ir.FloatType(),
        "双精度浮点型": ir.DoubleType(),
        "空型": ir.VoidType(),
        "字符串型": ir.PointerType(ir.IntType(8)),
    }
    if zhc_ty in table:
        return table[zhc_ty]
    if zhc_ty.startswith("i"):
        width = int(zhc_ty[1:])
        return ir.IntType(width)
    # 结构体类型：按名称查找或创建 opaque 类型
    return ir.IntType(32)  # 默认

# 结构体 layout 需要从 analyzer 层获取
def resolve_struct_layout(struct_name: str) -> List[ir.Type]:
    # 从 analyzer/semantic 层获取结构体成员类型
    ...
```

#### 4.3.2 函数生成（`llvm_module.py`）

```python
def _emit_function(self, ir_func: IRFunction) -> ir.Function:
    func_type = ir.FunctionType(
        return_type=zhc_type_to_llvm(ir_func.return_type, self.ctx),
        args=[zhc_type_to_llvm(p.ty, self.ctx) for p in ir_func.params],
    )
    func = ir.Function(self.module, func_type, name=ir_func.name)
    # 为每个基本块创建 LLVM block
    for bb in ir_func.basic_blocks:
        llvm_bb = func.append_basic_block(name=bb.label)
        with ir.IRBuilder(llvm_bb) as builder:
            self._emit_block(bb, builder)
    return func
```

#### 4.3.3 JIT 执行（`llvm_jit.py`）

```python
def jit_compile_and_run(self, ir_program: IRProgram,
                         entry: str,
                         args: List[Any]) -> Any:
    binding.initialize()
    binding.initialize_native_target()
    binding.initialize_native_asmprinter()

    # 将 ZHC IR 编译为 LLVM bitcode
    bc = self.generate_bitcode(ir_program)

    # 创建 JIT 编译器
    target = binding.Target.from_default_triple()
    target_machine = target.create_target_machine()
    backing_mod = binding.parse_assembly(str(ir.Module("")))
    jit = binding.create_jit_compilerManager(backing_mod)

    # 编译并执行
    compiled = jit.add_module(bc)
    entry_ptr = compiled.get_function_address(entry)
    # ... 调用 entry_ptr
```

### 4.4 LLVM IR 文本生成器修复

现有 `LLVMPrinter` 需修复 bug 并增强：

| 问题 | 修复方案 |
|------|----------|
| 第 142、152 行引用 `Instruction` 未定义 | 改为 `IRInstruction` |
| 缺少 `NEG`（取负）指令生成 | 实现 `_gen_neg` |
| 缺少 `AND/OR/XOR/NOT/SHL/SHR` 位运算 | 添加 `_gen_bitwise` |
| 缺少 `ZEXT/SEXT/TRUNC` 转换指令 | 添加 `_gen_cast` |
| 缺少 `SWITCH/PHI` 指令 | 添加 `_gen_switch/_gen_phi` |
| `source_filename` / `target triple` 为空 | 设置合理默认值 |
| 没有 `define dso_local` 等函数属性 | 添加 Windows/macOS/Linux 兼容属性 |

---

## 五、WASM 后端实现方案

### 5.1 设计原则

1. **不依赖 Emscripten** — 原生生成 WASM 二进制格式
2. **线性内存模型** — WASM 只能操作线性内存，无原生指针
3. **可选 Emscripten** — 通过 `--backend=emcc` flag 启用，作为高级优化路径
4. **分阶段实现** — P0 基础功能 → P1 完整功能 → P2 优化

### 5.2 WASM IR 定义（`wasm_ir.py`）

```python
# WASM 指令（与 ZHC IR Opcode 对应）
class WASMOp(Enum):
    # 算术
    I32_ADD = "i32.add"
    I32_SUB = "i32.sub"
    I32_MUL = "i32.mul"
    I32_DIV_S = "i32.div_s"
    I32_REM_S = "i32.rem_s"
    # ... 对应 ZHC IR 的每条 Opcode

# WASM 模块结构
@dataclass
class WASMFunc:
    name: str
    params: List[WASMType]     # 价值类型
    results: List[WASMType]    # 返回类型
    locals: List[WASMType]     # 局部变量
    body: List[WASMInstr]      # 指令序列

@dataclass
class WASMModule:
    types: List[FuncType]       # type section
    funcs: List[WASMFunc]       # func section
    mems: List[MemoryType]      # memory section
    globals: List[WASMGlobal]    # global section
    exports: List[WASMExport]    # export section
    start: Optional[int]        # start section
```

### 5.3 WAT → WASM 二进制编码（`wasm_binary.py`）

使用 `wasm-tools` 子命令或手写 LEUV 编码：

```python
import subprocess
from pathlib import Path

def wat2wasm(wat_text: str, output_path: Path) -> bytes:
    """将 WAT 文本转换为 WASM 二进制"""
    # 方案 A: wasm-tools（推荐）
    result = subprocess.run(
        ["wasm-tools", "parse", "-o", str(output_path)],
        input=wat_text, text=True, capture_output=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"wasm-tools failed: {result.stderr}")
    return output_path.read_bytes()

# 手动 LEUV 编码（无外部依赖时备用）
def encode_leb128(val: int) -> bytes:
    """无符号 LEB128 编码"""
    result = bytearray()
    while True:
        byte = val & 0x7f
        val >>= 7
        if val != 0:
            byte |= 0x80
        result.append(byte)
        if val == 0:
            break
    return bytes(result)
```

### 5.4 ZHC IR → WAT 转换（`wasm_codegen.py`）

```python
class WASMCodeGenerator:
    """
    ZHC IR → WebAssembly Text Format (WAT) 代码生成器

    映射规则：
    - ZHC 整数型 → i32
    - ZHC 浮点型 → f32
    - ZHC 双精度浮点型 → f64
    - ZHC 布尔型 → i32 (0=false, 1=true)
    - ZHC 字符型 → i32 (Unicode codepoint)
    - ZHC 字符串型 → (i32 ptr, i32 len) 配对
    - ZHC 数组 → linear memory 连续区域
    """

    def __init__(self):
        self.lines: List[str] = []
        self._indent = 0

    def generate(self, ir: IRProgram) -> str:
        self._emit("(module")
        self._emit_type_section(ir)
        self._emit_func_section(ir)
        self._emit_memory_section()
        self._emit_export_section(ir)
        self._emit("(end)")
        return "\n".join(self.lines)

    # ZHC IR Opcode → WASM 指令映射
    _OP_MAP = {
        Opcode.ADD: "i32.add",
        Opcode.SUB: "i32.sub",
        Opcode.MUL: "i32.mul",
        Opcode.DIV: "i32.div_s",
        Opcode.MOD: "i32.rem_s",
        Opcode.LT: "i32.lt_s",
        Opcode.GT: "i32.gt_s",
        # ... 完整映射
    }

    def _gen_function(self, func: IRFunction):
        """生成单个函数"""
        params = " ".join(["(param $p{i} i32)" for i in range(len(func.params))])
        results = "(result i32)" if func.return_type not in ("空型", "void") else ""
        self._emit(f"(func ${func.name} {params} {results}")

        # 生成局部变量声明
        for bb in func.basic_blocks:
            for instr in bb.instructions:
                if instr.opcode == Opcode.ALLOC:
                    self._emit(f"  (local ${instr.operands[0].name} i32)")

        # 生成指令
        for bb in func.basic_blocks:
            self._gen_block(bb)

        self._emit(")")

    def _gen_block(self, bb: IRBasicBlock):
        """生成基本块"""
        self._emit(f"  (block ${bb.label}")
        for instr in bb.instructions:
            self._gen_instruction(instr)
        self._emit(")")
```

### 5.5 调用链整合

```
CLI --backend=llvm
    │
    ▼
pipeline.py
    │
    ▼
IRGenerator (已有)
    │
    ▼
LLVMBackend.generate(ir)        ← 新接口
    │                           返回 text/bitcode/jit 结果
    ▼
输出 .ll / .bc / 直接执行
```

```
CLI --backend=wasm
    │
    ▼
pipeline.py
    │
    ▼
IRGenerator (已有)
    │
    ▼
WASMBackend.generate(ir)         ← 新接口
    │
    ├─ WASMCodeGenerator.generate() → WAT 文本
    │
    └─ wasm-tools encode → .wasm 二进制
    │
    ▼
输出 .wat / .wasm
```

---

## 六、实施计划

### 阶段 1：LLVM 后端完善（第 1-2 周）

| 任务 | 描述 | 优先级 | 工作量 |
|------|------|--------|--------|
| T1.1 | 修复 `LLVMPrinter` bug（142/152 行 `Instruction` → `IRInstruction`） | P0 | 0.5d |
| T1.2 | 添加缺失 opcode 支持（NEG/BITWISE/CAST/SWITCH/PHI） | P0 | 1d |
| T1.3 | 实现 `LLVMBackend` 类（基于 llvmlite） | P0 | 3d |
| T1.4 | 实现 `llvm_types.py`（类型映射） | P0 | 1d |
| T1.5 | 实现 `llvm_jit.py`（JIT 编译器） | P1 | 2d |
| T1.6 | 实现 `llvm_optimize.py`（LLVM Pass 集成） | P1 | 1d |
| T1.7 | 添加 CLI `--backend=llvm [--emit=ll\|bc\|jit]` | P0 | 0.5d |
| T1.8 | 编写测试 `tests/test_llvm_backend.py`（50+ cases） | P0 | 1d |

### 阶段 2：WASM 后端原生实现（第 3-5 周）

| 任务 | 描述 | 优先级 | 工作量 |
|------|------|--------|--------|
| T2.1 | 实现 `wasm_ir.py`（WASM 模块/函数/指令定义） | P0 | 1d |
| T2.2 | 实现 `wasm_codegen.py`（ZHC IR → WAT 生成器） | P0 | 4d |
| T2.3 | 实现 `wasm_binary.py`（WAT → WASM 编码器） | P0 | 2d |
| T2.4 | 实现 `WASMBackend` 主类（整合以上模块） | P0 | 1d |
| T2.5 | 添加 CLI `--backend=wasm [--emit=wat\|wasm]` | P0 | 0.5d |
| T2.6 | 支持 Emscripten 集成（`--backend=emcc` 备选路径） | P1 | 2d |
| T2.7 | 编写测试 `tests/test_wasm_backend.py`（50+ cases） | P0 | 2d |

### 阶段 3：集成与工具链（第 6 周）

| 任务 | 描述 | 优先级 | 工作量 |
|------|------|--------|--------|
| T3.1 | CLI 统一后端调度（`--backend` 参数扩展） | P0 | 0.5d |
| T3.2 | 统一输出格式（`.ll` / `.bc` / `.wasm` / `.wat`） | P0 | 0.5d |
| T3.3 | 更新文档（`docs/backends/` 目录） | P1 | 1d |
| T3.4 | 添加 benchmark（LLVM vs C 后端性能对比） | P1 | 1d |
| T3.5 | 添加 `scripts/wasm-preview.py`（浏览器预览工具） | P2 | 1d |

---

## 七、依赖清单

### 7.1 Python 依赖

```toml
# pyproject.toml 新增依赖
dependencies = [
    # LLVM 后端
    "llvmlite>=0.39.0",
    # WASM 后端（可选）
    "wasm-tools>=1.0.0",  # 系统级工具，通过 subprocess 调用
]
```

### 7.2 系统依赖

```bash
# macOS
brew install llvm@15 wasm-tools

# Ubuntu/Debian
apt install llvm-15 llvm-15-dev wasm-tools

# Windows (WSL recommended)
wsl --install  # then use Ubuntu instructions
```

### 7.3 最低环境要求

- Python 3.9+
- LLVM 12+（通过 llvmlite 绑定）
- wasm-tools 1.0+（用于 WASM 二进制生成）

---

## 八、已知风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| llvmlite 与系统 LLVM 版本不匹配 | 运行时 crash | 使用 conda/mamba 安装匹配版本的 llvmlite |
| WASM binary encoding 实现复杂 | 工期超支 | 优先使用 wasm-tools 子命令；手写编码作为备用 |
| 现有 LLVMPrinter 客户依赖 | 重写可能破坏现有流程 | 通过 `--backend=llvm --emit=text` 提供旧接口兼容 |
| 中文类型→WASM 类型映射不完整 | 运行时错误 | P0 阶段只支持基础类型；结构体/数组 P1 实现 |
| LLVM JIT 在 macOS ARM 上行为异常 | 执行结果不对 | 添加 architecture 检测；使用 llvm-jit 的 CPU-specific 配置 |

---

## 九、测试策略

### 9.1 LLVM 后端测试

```python
def test_llvm_arithmetic():
    """算术运算：ZHC IR → LLVM IR → JIT 执行"""
    ir = build_ir_for("整数型 a = 10; 整数型 b = 20; 整数型 c = a + b * 2;")
    backend = LLVMBackend()
    result = backend.jit_execute(ir, "main")
    assert result == 50  # 10 + 20*2

def test_llvm_bitcode_roundtrip():
    """Bitcode: 生成 → 反序列化 → 验证等价性"""
    ...

def test_llvm_opt_pipeline():
    """优化: 验证 LLVM 优化 Pass 实际生效"""
    ...
```

### 9.2 WASM 后端测试

```python
def test_wasm_add():
    """加法: ZHC IR → WAT → WASM binary → 执行"""
    ir = build_ir_for("整数型 a = 10; 整数型 b = 20; 整数型 c = a + b;")
    backend = WASMBackend()
    wasm_bytes = backend.generate(ir, emit="wasm")
    result = run_wasm(wasm_bytes, "main")
    assert result == 30

def test_wat_text_output():
    """WAT 输出可读性验证"""
    ...
```

---

## 十、CLI 接口设计

```bash
# LLVM 后端
zhc compile main.zhc --backend=llvm              # 默认输出 .ll 文本
zhc compile main.zhc --backend=llvm --emit=ll    # 输出 .ll
zhc compile main.zhc --backend=llvm --emit=bc   # 输出 .bc bitcode
zhc compile main.zhc --backend=llvm --emit=jit  # JIT 执行
zhc compile main.zhc --backend=llvm -O3         # LLVM 优化级别

# WASM 后端
zhc compile main.zhc --backend=wasm             # 默认输出 .wasm
zhc compile main.zhc --backend=wasm --emit=wat  # 输出 .wat 文本
zhc compile main.zhc --backend=wasm --emit=wasm # 输出 .wasm 二进制
zhc compile main.zhc --backend=emcc             # Emscripten 路径（备选）

# 原 C 后端（保留）
zhc compile main.zhc --backend=c                 # 输出 .c
```

# P6-WASM-WebAssembly优化 开发分析文档

## 基本信息

| 字段 | 内容 |
|------|------|
| **优先级** | P6 |
| **功能模块** | WASM (WebAssembly) |
| **功能名称** | WebAssembly 特定优化 |
| **文档版本** | 1.0.0 |
| **创建日期** | 2026-04-10 |
| **预计工时** | 约 3-4 周 |

---

## 1. 功能概述

WebAssembly（WASM）是 ZhC 编译器的重要目标平台。本模块专注于为 WASM 后端实现特定的代码优化，使生成的 WASM 代码具有更小的体积和更好的运行时性能。

### 1.1 核心目标

- 生成符合 WASM 规范的紧凑、高效字节码
- 实现 WASM 特有的优化策略
- 支持与 JavaScript 环境的无缝互操作
- 提供 WASM 运行时的最佳性能

---

## 2. 技术背景

### 2.1 WebAssembly 特性分析

| 特性 | 描述 | 对编译器的影响 |
|------|------|----------------|
| **线性内存** | WASM 使用 32 位线性内存模型，最大 4GB | 需要特殊处理指针和数组访问 |
| **类型限制** | 仅支持 i32/i64/f32/f64 四种基本类型 | 中文类型系统需要映射到这些类型 |
| **栈式架构** | WASM 是栈式虚拟机，指令无寄存器 | 需要将寄存器分配转换为栈操作 |
| **调用约定** | 使用栈传递参数，限制参数数量 | 函数调用需要特殊处理 |
| **尾调用** | WASM 1.0 不支持尾调用优化 | 递归函数需要特殊处理 |

### 2.2 WASM 与 LLVM IR 的差异

```
LLVM IR                          WASM
─────────────────────────────    ─────────────────────────────
无限寄存器                       栈式操作数栈
复杂控制流（switch, phi）        结构化控制流（block, loop, if）
任意指针运算                     限制的内存操作
完整 C/C++ 类型系统               有限类型系统
多返回值                         通过线性内存模拟
```

---

## 3. 详细设计

### 3.1 模块架构

```
src/zhc/backend/wasm/
├── __init__.py                 # 模块导出
├── wasm_backend.py             # WASM 后端主类
├── wasm_module.py              # WASM 模块定义
├── wasm_function.py            # 函数定义和翻译
├── wasm_optimizer.py           # WASM 特定优化
├── wasm_emit.py                # 字节码生成器
├── wasm_intrinsics.py          # 内置函数映射
├── wasm_validation.py          # WASM 验证器
└── js互操作/
    ├── js_import.py            # JS 导入处理
    ├── js_export.py            # JS 导出处理
    └── wasm_bindings.py        # 绑定生成器
```

### 3.2 WASM 后端核心类

#### 3.2.1 WASMBackend

```python
class WASMBackend(BackendBase):
    """WebAssembly 后端"""

    def __init__(self, options: WASMOptions):
        self.target = Target.WASM
        self.options = options
        self.module = WASMModule()
        self.intrinsics = WASMIntrinsics()
        self.validator = WASMValidator()

    # 核心方法
    def emit_module(self, ir_module: IRModule) -> bytes:
        """生成 WASM 二进制字节码"""

    def emit_text_format(self, ir_module: IRModule) -> str:
        """生成 WAT (WebAssembly Text) 格式"""

    def optimize(self, module: WASMModule) -> WASMModule:
        """应用 WASM 特定优化"""
```

#### 3.2.2 WASM 模块结构

```python
@dataclass
class WASMModule:
    """WASM 模块结构"""
    version: int = 1                    # WASM 版本
    types: List[WASMType] = field(default_factory=list)
    functions: List[WASMFunction] = field(default_factory=list)
    tables: List[WASMTable] = field(default_factory=list)
    memories: List[WASMMemory] = field(default_factory=list)
    globals: List[WASMGlobal] = field(default_factory=list)
    exports: List[WASMExport] = field(default_factory=list)
    imports: List[WASMImport] = field(default_factory=list)
    data: List[WASMData] = field(default_factory=list)
    start: Optional[int] = None
```

### 3.3 WASM 特定优化策略

#### 3.3.1 体积优化 (Size Optimization)

| 优化项 | 描述 | 预期收益 |
|--------|------|----------|
| **Bytecode Splitting** | 将代码分为热路径和冷路径 | 减少加载时间 |
| **Constant Folding** | 编译时常量折叠 | 减少运行时计算 |
| **Dead Code Elimination** | 移除未使用代码 | 减少代码体积 |
| **Function Inlining** | 小函数内联 | 减少调用开销 |
| **Type Specialized** | 泛型特化 | 生成更小的泛型代码 |

#### 3.3.2 性能优化 (Performance Optimization)

| 优化项 | 描述 | 预期收益 |
|--------|------|----------|
| **Local Get/Set Optimization** | 减少局部变量访问 | 减少字节码指令 |
| **Memory Imms** | 使用 memory.copy/memory.fill | 利用原生实现 |
| **Trapping vs NaN** | 正确处理陷阱 vs 返回 NaN | 提高数学运算效率 |
| **SIMD Utilization** | 使用 WASM SIMD 指令 | 加速向量运算 |
| **Bulk Operations** | 使用 bulk memory 操作 | 提高大数据传输效率 |

#### 3.3.3 优化器实现

```python
class WASMOptimizer:
    """WASM 特定优化器"""

    def __init__(self, level: OptimizationLevel):
        self.level = level
        self.passes = self._get_passes()

    def _get_passes(self) -> List[OptimizationPass]:
        return [
            ConstantFoldingPass(),
            DeadCodeEliminationPass(),
            LocalOptimizationPass(),
            BlockFlatteningPass(),
            GCOpcodeInsertionPass(),     # 垃圾回收提示
            NaNCanonicalizationPass(),    # NaN 规范化
            SignExtensionOptPass(),       # 符号扩展优化
            DropUnrefLocalsPass(),        # 丢弃未引用局部变量
            DCEPass(),                    # 最终死代码消除
        ]

    def run(self, module: WASMModule) -> WASMModule:
        for pass_ in self.passes:
            module = pass_.transform(module)
        return module
```

### 3.4 类型映射

#### 3.4.1 中文类型 → WASM 类型

| ZhC 类型 | WASM 类型 | 字节大小 | 备注 |
|----------|-----------|----------|------|
| 整数型 | i32 | 4 | 32 位有符号整数 |
| 长整数型 | i64 | 8 | 64 位有符号整数 |
| 浮点型 | f32 | 4 | 32 位浮点数 |
| 双精度型 | f64 | 8 | 64 位浮点数 |
| 字符型 | i32 | 4 | Unicode 码点 |
| 布尔型 | i32 | 4 | 0 或 1 |
| 指针型 | i32 | 4 | WASM 内存地址 |
| 数组型 | i32 | 4 | 数组引用（指针） |
| 结构体型 | i32 | 4 | 结构体引用（指针） |
| 空类型 | - | - | void 对应空栈 |

#### 3.4.2 特殊类型映射策略

```python
class WASMTypeMapper:
    """WASM 类型映射器"""

    def map_type(self, zhc_type: Type) -> WASMType:
        if isinstance(zhc_type, BoolType):
            return WASMType.i32  # WASM 没有布尔类型
        elif isinstance(zhc_type, ArrayType):
            return WASMType.i32  # 数组通过指针引用
        elif isinstance(zhc_type, StructType):
            return WASMType.i32  # 结构体通过指针引用
        elif isinstance(zhc_type, WideCharType):
            return WASMType.i32  # 宽字符映射为 Unicode 码点
        else:
            return self._map_primitive(zhc_type)

    def _map_primitive(self, zhc_type: Type) -> WASMType:
        type_map = {
            '整数型': WASMType.i32,
            '长整数型': WASMType.i64,
            '浮点型': WASMType.f32,
            '双精度型': WASMType.f64,
            '字符型': WASMType.i32,
        }
        return type_map.get(str(zhc_type), WASMType.i32)
```

### 3.5 控制流翻译

WASM 使用结构化控制流，需要将 LLVM IR 的控制流图转换为 WASM 的 block/loop/if 结构。

```python
class ControlFlowTranslator:
    """控制流翻译器"""

    def translate_function(self, func: Function) -> WASMFunction:
        # 1. 构建控制流图
        cfg = ControlFlowGraph.build(func)

        # 2. 识别循环和分支结构
        loops = self._identify_loops(cfg)
        branches = self._identify_branches(cfg)

        # 3. 转换为结构化控制流
        structured = self._structure_control_flow(cfg, loops, branches)

        # 4. 生成 WASM 指令
        return self._emit_wasm(structured)

    def _identify_loops(self, cfg):
        """识别自然循环"""
        # 使用 dominance frontier 算法
        pass

    def _structure_control_flow(self, cfg, loops, branches):
        """将控制流图结构化"""
        # 使用 Tarjan 算法找强连通分量
        pass
```

---

## 4. 实现方案

### 4.1 第一阶段：基础框架

1. **创建 WASM 后端框架**
   - 实现 `WASMBackend` 基类
   - 定义 `WASMModule`、`WASMFunction` 等数据结构
   - 实现基本的模块输出功能

2. **实现类型映射**
   - ZhC 类型 → WASM 类型映射
   - 支持基本类型和指针类型

3. **基本代码生成**
   - 函数翻译
   - 基本表达式翻译
   - 简单控制流（if/while）

### 4.2 第二阶段：完整翻译

1. **完整控制流翻译**
   - 结构化控制流转换
   - 支持 switch/match 语句
   - 支持 break/continue

2. **复杂类型支持**
   - 数组类型
   - 结构体类型
   - 字符串类型

3. **函数调用约定**
   - 参数传递
   - 返回值处理
   - 尾调用处理（如果支持）

### 4.3 第三阶段：优化

1. **字节码优化**
   - 实现所有优化 pass
   - 优化级别支持（-O0, -O1, -Oz）

2. **验证和调试**
   - WASM 验证器集成
   - WAT 格式输出
   - 调试信息支持

### 4.4 第四阶段：互操作

1. **JS/WASM 互操作**
   - 导入 JS 函数
   - 导出 WASM 函数
   - 内存共享

2. **类型绑定**
   - 自动绑定生成
   - TypeScript 定义生成

---

## 5. API 设计

### 5.1 命令行接口

```bash
# 编译为 WASM
zhc compile input.zhc --target wasm -o output.wasm

# 编译为 WAT (文本格式)
zhc compile input.zhc --target wasm --emit-asm -o output.wat

# 带优化的编译
zhc compile input.zhc --target wasm -O2 -o output.wasm

# 体积优化 (最高压缩率)
zhc compile input.zhc --target wasm -Oz -o output.wasm

# 指定入口函数
zhc compile input.zhc --target wasm --entry main -o output.wasm
```

### 5.2 编程接口

```python
from zhc.backend.wasm import WASMBackend, WASMOptions

# 配置选项
options = WASMOptions(
    optimization_level=2,          # 优化级别
    emit_debug_info=False,          # 是否输出调试信息
    enable_simd=False,             # 是否启用 SIMD
    memory_pages=16,               # 初始内存页数 (64KB/page)
    max_memory_pages=256,          # 最大内存页数
    enable_threads=False,          # 是否启用多线程
    js_imports=['console', 'document'],  # JS 导入模块
    js_exports=['_start'],        # 导出的函数
)

# 创建后端
backend = WASMBackend(options)

# 编译
result = backend.compile(ir_module)
result.write_to_file('output.wasm')

# 获取 WAT 输出
wat = result.emit_wat()
```

---

## 6. 测试策略

### 6.1 单元测试

| 测试类别 | 测试内容 | 测试用例数 |
|----------|----------|------------|
| 类型映射 | 所有类型的正确映射 | ~50 |
| 控制流翻译 | if/while/for/switch | ~100 |
| 表达式翻译 | 算术/逻辑/位运算 | ~80 |
| 函数调用 | 参数/返回值/递归 | ~40 |
| 优化器 | 各优化 pass 的正确性 | ~60 |

### 6.2 集成测试

- 使用 `wabt` (WebAssembly Binary Toolkit) 验证生成的字节码
- 使用 `v8` / `spidermonkey` 运行生成的 WASM
- 与现有测试套件集成

### 6.3 性能基准测试

```python
# 性能测试用例
BENCHMARKS = [
    'fibonacci_recursive',
    'matrix_multiplication',
    'sorting_algorithms',
    'string_processing',
    'numerical_integration',
]

def benchmark_wasm():
    """比较 WASM 输出与本地 LLVM 后端的性能"""
    results = {}
    for name in BENCHMARKS:
        llvm_time = measure_llvm(name)
        wasm_time = measure_wasm(name)
        results[name] = {
            'llvm_ms': llvm_time,
            'wasm_ms': wasm_time,
            'ratio': wasm_time / llvm_time,
        }
    return results
```

---

## 7. 已知限制和风险

### 7.1 WASM 1.0 限制

| 限制 | 影响 | 缓解方案 |
|------|------|----------|
| 无尾调用优化 | 深层递归可能导致栈溢出 | 编译期警告 + 迭代改写建议 |
| 无异常处理 | 错误处理受限 | 使用错误码或 setjmp/longjmp 模拟 |
| 固定参数寄存器 | 函数参数超过 4 个效率低 | 通过内存传递大参数 |
| 4GB 内存限制 | 无法分配大于 4GB | 编译期警告 |

### 7.2 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| WASM 规范变更 | 低 | 中 | 使用稳定的 API，隔离规范依赖 |
| 浏览器兼容性问题 | 中 | 中 | 提供 polyfill 和特性检测 |
| 优化算法复杂度 | 中 | 中 | 分阶段实现，充分测试 |
| 性能回归 | 中 | 高 | 建立性能基准，持续监控 |

---

## 8. 后续扩展

### 8.1 WASM 2.0 支持

- 异常处理
- 垃圾回收 (GC)
- 引用类型
- 尾调用

### 8.2 高级特性

- WebAssembly System Interface (WASI) 支持
- WASM SIMD 指令支持
- Threads/Atomics 支持
- GC 优化

---

## 9. 参考资料

- [WebAssembly Specification](https://webassembly.github.io/spec/)
- [WASM Text Format Specification](https://webassembly.github.io/spec/text/)
- [Emscripten Toolchain](https://emscripten.org/)
- [wabt - WebAssembly Binary Toolkit](https://github.com/WebAssembly/wabt)
- [Binaryen - WebAssembly compiler infrastructure](https://github.com/WebAssembly/binaryen)

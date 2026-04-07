# Phase 8 规划：IR 多后端 + 插件系统

> 版本：v0.1（初步分析）
> 日期：2026-04-03
> 状态：规划中

---

## 一、现状基线

### 1.1 现有编译路径

```
.zhc → Lexer → Parser → AST
                       ↓
              SemanticAnalyzer（语义分析）
                       ↓
                    IRGenerator
                       ↓
                     ZHC IR
                       ↓
              ┌──┬────────┬──────────┐
              ↓   ↓        ↓
           C后端  LLVM后端  WASM后端（规划中）
              ↓        ↓         ↓
              C代码   LLVM IR   WASM字节码
              ↓
           clang   llvm-as   ...
              ↓
           可执行文件   汇编   浏览器运行

```

### 1.2 现有 IR 后端

| 后端 | 文件 | 状态 |
|------|------|------|
| C 后端 | `ir/c_backend.py` | Phase 7 M3 已完成 |
| LLVM 后端 | 无 | **待规划** |
| WASM 后端 | 无 | Phase 8 探索 |

---

## 二、IR 多后端设计

### 2.1 后端接口抽象

```python
# ir/backends/backend.py

class IRBackend(ABC):
    """IR 后端基类"""
    
    @abstractmethod
    def generate(self, ir: IRProgram) -> OutputArtifact:
        """生成目标代码/字节码"""
        pass
    
    @abstractmethod
    def get_output_type(self) -> OutputType:
        pass


class OutputArtifact:
    """编译产物"""
    type: OutputType  # 可执行文件/汇编/LLVM IR/WASM/库文件
    data: bytes | str
    format: str  # "elf"/"mach-o"/"wasm"/"ll"/"bc"


class OutputType(Enum):
    EXECUTABLE = "executable"
    LLVM_IR = "llvm_ir"
    LLVM_BC = "llvm_bc"
    WASM = "wasm"
    LIBRARY = "library"
    ASSEMBLY = "asm"
```

### 2.2 LLVM 后端设计

#### 2.2.1 目标

生成 LLVM IR 或目标文件（.o/.bc/.ll）

#### 2.2.2 可行性

| 因素 | 评估 |
|------|------|
| LLVM 绑定可用性 | llvmlite（纯 Python）、llvmlite 不支持代码生成，仅用于 IR 操作 |
| llvmlite 不支持目标代码生成 |
| ctypes / cffi | 可调用 clang 工具链 |
| 方案 | 通过子进程调用 `clang -S -emit-llvm -o test.ll test.c 生成 LLVM IR |

**结论**：llvmlite 只能解析/分析 LLVM IR，不能生成目标代码。正确方案是通过现有 CBackend 生成 C 代码，再用 `clang -S -emit-llvm` 转为 LLVM IR，或直接用 `clang -c` 编译到 .o/.bc。

### 2.3 多后端 CLI 参数

```bash
--backend llvm    # 输出 LLVM IR (.ll)
--backend wasm   # 输出 WASM
--backend obj     # 输出目标文件 (.o)

# 示例
python3 -m src.__main__ input.zhc --backend llvm -o output.ll
python3 -m src.__main__ input.zhc --backend wasm -o output.wasm
```

---

## 三、WASM 后端可行性分析

### 3.1 方案 A：ZHC IR → C → Emscripten → WASM

```
.zhc → IRGenerator → CBackend → C代码 → Emscripten (emcc) → .wasm
```

**优点**：利用现有 C 后端，无需重写 WASM 生成逻辑
**缺点**：需要安装 Emscripten 工具链

### 3.2 方案 B：ZHC IR → WASM 字节码（直接生成）

```
.zhc → IRGenerator → IR → WASMBackend → .wasm
```

**优点**：原生 WASM 产物，无 C 依赖
**缺点**：WASM 指令集庞大（100+ 操作码），生成器开发工作量大

### 3.3 推荐方案

**近期**：方案 A（利用现有 C 后端 + Emscripten）
**中期**：方案 B（Phase 9+）

---

## 四、C 插件系统设计

### 4.1 背景

用户问的是"C 的库如何对接"。现有方案：
- 通过 `#include` 头文件方式接入 C 库（已有 `#include` 映射表）

### 4.2 插件系统架构

```
插件注册表（PluginRegistry）
├── 路径：~/.zhc/plugins/（用户插件目录）
├── 内置：zhc_stdio.h / zhc_stdlib.h
└── 第三方：用户 .so/.dylib 插件

插件接口（PluginProtocol）：
  - name, version, description
  - on_compile(source) → ModifiedSource
  - provides_symbols: Dict[str, str]  # 提供的符号
  - requires: List[str]  # 依赖其他插件
```

### 4.3 插件发现流程

```
1. 解析 import 语句
2. 查询插件注册表
3. 找到则加载插件
4. 找不到则 fallback 到 include 路径
```

### 4.4 内置插件：标准库插件

| 插件 | 提供符号 | 状态 |
|------|---------|------|
| stdio | 打印/输入/文件操作 | 已有（stdio.zhc） |
| stdlib | malloc/free/stdlib | 已有（stdlib.zhc） |
| string | 字符串函数 | 已有（string.zhc） |
| math | 数学函数 | 已有（math.zhc） |

---

## 五、LLVM 工具链集成

### 5.1 现有集成方式

| 工具 | 用途 | 现状 |
|------|------|------|
| clang | C 代码编译 | 已有（编译生成的可执行文件） |
| clang -S -emit-llvm | 生成 .ll | 可用 |
| lld | 链接 .o 文件 | 可用 |
| llc | .ll → 目标文件 | 需要验证 |

### 5.2 LLVM IR 生成路径

```
.zhc
  → AST → IR → CBackend → C代码
                          ↓
                    clang -S -emit-llvm
                          ↓
                       .ll 文件
                          ↓
                       lld 链接
                          ↓
                     可执行文件
```

---

## 六、待用户决策

1. **LLVM 后端**：是否需要？
2. **WASM 插件**：是否需要？
3. **插件系统**：需要哪些 C 库？
4. **优先级**：多后端 vs 插件系统 vs 其他

---

*Phase 8 初步分析，待补充细节*

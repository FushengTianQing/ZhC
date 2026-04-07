# Phase 7: IR 中间表示与代码优化 — 执行计划 v1.0

> 版本：v1.0
> 创建时间：2026-04-03
> 项目路径：`/Users/yuan/Projects/zhc/`
> 前置依赖：Phase 6 全部完成（T0-M5，586+ tests passed）

---

## 版本说明

### 文档定位

本文档是 Phase 7 的**完整执行计划**，包含目标架构、里程碑拆分、每个步骤的具体执行指令、文件变更清单、测试策略和验收标准。

### Phase 7 核心目标

**在 AST 和 C 代码之间插入 IR 中间层，使编译器从 `AST → C` 直连变为 `AST → IR → C`，为后续多后端支持和 IR 级优化奠定基础。**

### 不做什么

- 不做 LLVM 后端（Phase 8+ 考虑）
- 不做 WASM 后端
- 不废弃现有的 AST → C 路径（Phase 7 完成后可选废弃）

---

## 零、现状基线

### 0.1 当前编译流程

```
.zhc 源码 → Lexer → Parser → AST
                              ↓
                     SemanticAnalyzer（AST 上分析）
                       ├── 符号表构建
                       ├── 作用域分析
                       ├── 类型检查
                       ├── 函数参数/重载检查
                       ├── 控制流分析（CFG/未初始化/不可达）
                       ├── 数据流/过程间/别名/指针分析
                       └── 7 个分析器开关
                              ↓
                     CCodeGenerator（直接读 AST）→ C 代码
                              ↓
                     clang → 可执行文件
```

### 0.2 关键代码文件基线

| 文件 | 行数 | 职责 | Phase 7 影响 |
|------|------|------|-------------|
| `src/zhpp/codegen/c_codegen.py` | 623 | AST→C 代码生成（ASTVisitor） | **重大改造**：将作为 IR→C 后端的参照 |
| `src/zhpp/semantic/semantic_analyzer.py` | 2127 | 主分析器（含 7 个子分析器） | 小幅：传入 Symbol 信息给 IR 生成器 |
| `src/zhpp/compiler/pipeline.py` | ~150 | 编译流水线 | **改造**：插入 IR 生成和优化步骤 |
| `src/zhpp/cli.py` | ~350 | CLI 入口 | 新增 `--ir` / `--no-optimize` 等参数 |
| `src/zhpp/analyzer/scope_checker.py` | 520 | 第二套 Symbol/Scope | **整合**：合并到统一 Symbol 体系 |

### 0.3 两套 Symbol 体系现状

| 特征 | `semantic.Symbol` | `scope_checker.Symbol` |
|------|-------------------|----------------------|
| 位置 | `semantic/semantic_analyzer.py:43` | `analyzer/scope_checker.py:32` |
| 分类 | 字符串（"变量"/"函数"等） | 枚举 `SymbolCategory` |
| 类型 | `Optional[str]` | `TypeInfo`（强类型） |
| 使用范围 | SemanticAnalyzer 全流程 | ScopeChecker + TypeChecker |
| 重载 | 有（parameters 列表） | 无 |
| 作用域 | 自定义 Scope 类 | 自定义 Scope 类 |

### 0.4 IR 缺口清单（确认）

| # | 缺口 | 状态 |
|---|------|------|
| IR-1 | ZHC IR 定义（指令集、基本块、函数表示） | ❌ 不存在 |
| IR-2 | AST → IR 生成器 | ❌ 不存在 |
| IR-3 | IR → C 后端 | ❌ 不存在（当前 CCodeGenerator 直读 AST） |
| IR-4 | IR 优化 Pass | ❌ 不存在 |
| IR-5 | IR 验证器 | ❌ 不存在 |

---

## 一、目标架构

### 1.1 Phase 7 完成后的编译流程

```
.zhc 源码 → Lexer → Parser → AST
                              ↓
                     SemanticAnalyzer（AST 上分析，保持不变）
                              ↓
                     IRGenerator（AST → IR）         ← 新增
                              ↓
                           ZHC IR                     ← 新增
                              ↓
                     Optimizer（IR 优化 Pass）         ← 新增
                              ↓
                           ZHC IR'（优化后）
                              ↓
                     CBackend（IR → C）               ← 新增（替代 CCodeGenerator 的直接 AST 读取）
                              ↓
                          C 代码
                              ↓
                     clang → 可执行文件
```

### 1.2 兼容策略

Phase 7 **不删除** CCodeGenerator。新增 `--backend` 参数：

- `--backend ir`（默认，Phase 7 完成后）：AST → IR → 优化 → C
- `--backend ast`（兼容模式）：AST → C 直连（现有路径）

这保证现有 586+ 测试不会因 Phase 7 而失败。

---

## 二、里程碑总览

| 里程碑 | 名称 | 预估工时 | 依赖 | 核心交付 |
|--------|------|----------|------|----------|
| **M0** | Symbol 体系统一 | 6-8h | 无 | 统一的 `ir/symbol.py` |
| **M1** | ZHC IR 定义 | 8-12h | M0 | `ir/` 目录 + IR 指令集 + IR 数据结构 |
| **M2** | AST → IR 生成器 | 12-16h | M1 | `ir/ir_generator.py` |
| **M3** | IR → C 后端 | 6-8h | M1 | `ir/c_backend.py` |
| **M4** | IR 验证器 | 3-4h | M1 | `ir/ir_verifier.py` |
| **M5** | IR 优化 Pass 框架 + 基础 Pass | 6-8h | M1 | `ir/optimizer.py` + 2-3 个 Pass |
| **M6** | Pipeline 集成 + CLI | 3-4h | M2-M5 | pipeline.py 改造 + CLI 参数 |
| **M7** | 测试 + 文档 + 清理 | 4-6h | M0-M6 | 全量测试 + 迁移文档 |
| | **合计** | **48-66h** | | 约 6-8 个工作日 |

---

## 三、M0：Symbol 体系统一

### 3.1 目标

合并 `semantic.Symbol` 和 `scope_checker.Symbol` 为一套统一的 Symbol 体系，作为 IR 的类型信息基础。

### 3.2 设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 分类方式 | 采用 `scope_checker.SymbolCategory` 枚举 | 类型安全，避免字符串拼写错误 |
| 类型信息 | 采用 `TypeInfo` 强类型 | 比 `Optional[str]` 更精确 |
| 作用域 | 采用 `semantic.Scope` 类 | 功能更完整（有 scope_type, lookup 链） |
| 位置 | `src/zhpp/ir/symbol.py` | 放在 IR 包中，后续 IR 生成器直接使用 |

### 3.3 执行步骤

#### 步骤 M0.1：创建 `src/zhpp/ir/` 包

```
src/zhpp/ir/
├── __init__.py          # 导出 Symbol, Scope, TypeInfo 等
├── symbol.py            # 统一的 Symbol + Scope 定义
├── types.py             # TypeInfo + ZHCTy 类型体系（从 scope_checker 迁移）
└── opcodes.py           # IR 操作码枚举（M1 依赖，提前预留）
```

#### 步骤 M0.2：定义统一 Symbol 类

文件：`src/zhpp/ir/symbol.py`

```python
@dataclass
class Symbol:
    """统一的符号信息"""
    name: str
    category: SymbolCategory    # 枚举：VARIABLE/FUNCTION/PARAMETER/TYPEDEF/STRUCT/MODULE/LABEL
    type_info: 'ZHCTy'          # 统一类型表示
    line: int = 0
    is_global: bool = False
    is_static: bool = False
    is_const: bool = False
    is_initialized: bool = False
    is_used: bool = False
    scope_level: int = 0

    # 函数特有
    parameters: List['Symbol'] = field(default_factory=list)
    return_type: Optional['ZHCTy'] = None

    # 结构体特有
    members: List['Symbol'] = field(default_factory=list)
    parent_struct: Optional[str] = None

    # 兼容旧代码
    @property
    def symbol_type(self) -> str:
        return self.category.value

    @property
    def data_type(self) -> Optional[str]:
        return str(self.type_info) if self.type_info else None
```

#### 步骤 M0.3：定义统一 Scope 类

```python
class Scope:
    def __init__(self, level: int, parent: Optional['Scope'] = None,
                 scope_type: str = "global"):
        self.level = level
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}
        self.children: List['Scope'] = []
        self.scope_type = scope_type  # "global" / "function" / "block" / "struct"

    def declare(self, symbol: Symbol) -> bool: ...
    def lookup(self, name: str) -> Optional[Symbol]: ...
    def lookup_local(self, name: str) -> Optional[Symbol]: ...
    def all_symbols(self) -> Dict[str, Symbol]: ...  # 递归收集
```

#### 步骤 M0.4：迁移 semantic_analyzer.py

- 导入 `ir.symbol` 中的 Symbol 和 Scope
- 保留旧 `Symbol` 类作为 `LegacySymbol`（添加 `@deprecated` 注释），旧代码暂不改动
- 新代码路径使用新 Symbol
- `_analyze_call_expr` / `build_symbol_table` 等方法逐步迁移

#### 步骤 M0.5：迁移 scope_checker.py

- 删除 `scope_checker.py` 中的 Symbol / SymbolCategory / Scope 定义
- 改为从 `ir.symbol` 导入
- `TypeInfo` 迁移到 `ir/types.py`

#### 步骤 M0.6：迁移 type_checker.py

- `TypeInfo` 引用改为从 `ir.types` 导入
- 保留兼容别名

### 3.4 验收标准

- [ ] `src/zhpp/ir/symbol.py` 和 `src/zhpp/ir/types.py` 定义完成
- [ ] `semantic_analyzer.py` 和 `scope_checker.py` 均可导入新 Symbol
- [ ] 旧测试（586+）全部通过（兼容路径）
- [ ] 新增 `tests/test_ir_symbol.py`（10+ 测试）

### 3.5 风险

| 风险 | 缓解 |
|------|------|
| 迁移破坏现有测试 | 保留旧类名作为别名，逐步迁移 |
| TypeChecker 依赖 TypeInfo 旧路径 | `ir/types.py` 导出兼容接口 |

---

## 四、M1：ZHC IR 定义

### 4.1 目标

定义 ZHC IR 的完整指令集、数据结构和程序表示。这是整个 Phase 7 的基石。

### 4.2 设计原则

| 原则 | 说明 |
|------|------|
| **SSA 友好** | IR 基本块内每个变量只赋值一次，便于优化 Pass |
| **类型保留** | IR 指令携带类型信息，不做类型擦除 |
| **中文友好** | IR 调试输出可显示中文操作码名 |
| **可扩展** | 使用枚举 + dataclass，新增指令只需添加枚举值 |

### 4.3 IR 核心概念

```
IRProgram
├── functions: List[IRFunction]
│   ├── name: str                    # 函数名
│   ├── params: List[IRValue]        # 参数
│   ├── return_type: ZHCTy           # 返回类型
│   └── basic_blocks: List[IRBasicBlock]
│       ├── label: str               # "entry", "bb1", "bb2", ...
│       └── instructions: List[IRInstruction]
│           ├── opcode: Opcode       # ADD, LOAD, STORE, CALL, ...
│           ├── operands: List[IRValue]  # 操作数
│           └── result: Optional[IRValue]  # 目标值
├── globals: List[IRGlobalVar]       # 全局变量
└── structs: List[IRStructDef]       # 结构体定义
```

### 4.4 IR 操作码设计

#### 算术运算
| 操作码 | 操作数 | 结果 | 说明 |
|--------|--------|------|------|
| `ADD` | a, b | a+b | 整数/浮点加法 |
| `SUB` | a, b | a-b | 减法 |
| `MUL` | a, b | a*b | 乘法 |
| `DIV` | a, b | a/b | 除法（整数/浮点） |
| `MOD` | a, b | a%b | 取模 |
| `NEG` | a | -a | 取负 |

#### 比较运算
| 操作码 | 操作数 | 结果 | 说明 |
|--------|--------|------|------|
| `EQ` | a, b | a==b | 等于 |
| `NE` | a, b | a!=b | 不等于 |
| `LT` | a, b | a<b | 小于 |
| `LE` | a, b | a<=b | 小于等于 |
| `GT` | a, b | a>b | 大于 |
| `GE` | a, b | a>=b | 大于等于 |

#### 位运算
| 操作码 | 操作数 | 结果 | 说明 |
|--------|--------|------|------|
| `AND` | a, b | a&b | 位与 |
| `OR` | a, b | a\|b | 位或 |
| `XOR` | a, b | a^b | 位异或 |
| `NOT` | a | ~a | 位取反 |
| `SHL` | a, b | a<<b | 左移 |
| `SHR` | a, b | a>>b | 右移 |

#### 逻辑运算
| 操作码 | 操作数 | 结果 | 说明 |
|--------|--------|------|------|
| `L_AND` | a, b | a&&b | 逻辑与 |
| `L_OR` | a, b | a\|\|b | 逻辑或 |
| `L_NOT` | a | !a | 逻辑非 |

#### 内存操作
| 操作码 | 操作数 | 结果 | 说明 |
|--------|--------|------|------|
| `LOAD` | addr, type | value | 从地址读取 |
| `STORE` | value, addr | — | 写入地址 |
| `ALLOC` | type | ptr | 局部变量分配（栈） |
| `GLOBAL_ADDR` | name | ptr | 全局变量地址 |
| `GET_PTR` | base, offset, type | ptr | 取成员/数组元素地址 |
| `CONST` | value, type | value | 常量值 |

#### 控制流
| 操作码 | 操作数 | 结果 | 说明 |
|--------|--------|------|------|
| `JMP` | target_label | — | 无条件跳转 |
| `JZ` | cond, label | — | 条件跳转（零则跳） |
| `JNZ` | cond, label | — | 条件跳转（非零则跳） |
| `CALL` | func, args... | ret_val | 函数调用 |
| `RET` | value | — | 函数返回 |
| `SWITCH` | value, cases... | — | switch 跳转表 |

#### 转换
| 操作码 | 操作数 | 结果 | 说明 |
|--------|--------|------|------|
| `CAST` | value, target_type | value | 类型转换 |
| `SIZEOF` | type | int | 取类型大小 |

### 4.5 IR Value 定义

```python
@dataclass
class IRValue:
    """IR 中的值（操作数/结果）"""
    name: str           # 变量名或常量描述
    ty: ZHCTy           # 类型
    kind: ValueKind     # VAR / CONST / TEMP / PARAM

class ValueKind(Enum):
    VAR = "var"         # 命名变量
    CONST = "const"     # 常量
    TEMP = "temp"       # 临时值（%0, %1, ...）
    PARAM = "param"     # 函数参数
```

### 4.6 执行步骤

#### 步骤 M1.1：创建 IR 包结构

```
src/zhpp/ir/
├── __init__.py
├── symbol.py           # M0 已创建
├── types.py            # M0 已创建
├── opcodes.py          # 操作码枚举
├── values.py           # IRValue, ValueKind, IRSlot
├── instructions.py     # IRInstruction, IRBasicBlock
├── program.py          # IRProgram, IRFunction, IRGlobalVar, IRStructDef
├── printer.py          # IR 文本打印器（调试用）
└── ir_generator.py     # 占位（M2 实现）
```

#### 步骤 M1.2：实现操作码枚举

文件：`src/zhpp/ir/opcodes.py`

- 定义 `Opcode` 枚举，包含上述所有操作码
- 每个操作码有 `category` 属性（ARITH/COMPARE/BITWISE/LOGIC/MEMORY/CONTROL/CONVERT）
- 每个操作码有中文显示名（调试用）

#### 步骤 M1.3：实现 IRValue

文件：`src/zhpp/ir/values.py`

- `ValueKind` 枚举
- `IRValue` dataclass
- `IRSlot` dataclass（表示内存槽位，用于 ALLOC/STORE）

#### 步骤 M1.4：实现 IRInstruction

文件：`src/zhpp/ir/instructions.py`

- `IRInstruction` dataclass：`opcode`, `operands: List[IRValue]`, `result: Optional[IRValue]`, `metadata: Dict`
- `IRBasicBlock` dataclass：`label: str`, `instructions: List[IRInstruction]`, `successors: List[str]`, `predecessors: List[str]`
- 基本块的 CFG 关系维护

#### 步骤 M1.5：实现 IRProgram

文件：`src/zhpp/ir/program.py`

- `IRProgram`：顶层容器
- `IRFunction`：函数（参数 + 基本块链 + 返回类型）
- `IRGlobalVar`：全局变量声明
- `IRStructDef`：结构体类型定义

#### 步骤 M1.6：实现 IR 打印器

文件：`src/zhpp/ir/printer.py`

- `IRPrinter` 类，将 IRProgram 转为可读文本
- 输出格式示例：

```
function 主函数() -> 整数型:
  entry:
    %0 = ALLOC 整数型
    STORE 0, %0
    %1 = LOAD %0, 整数型
    RET %1
```

### 4.7 验收标准

- [ ] `src/zhpp/ir/` 包完整创建，包含 7 个模块
- [ ] `Opcode` 枚举包含 30+ 操作码，每个有 category 和中文名
- [ ] `IRValue`, `IRInstruction`, `IRBasicBlock`, `IRFunction`, `IRProgram` 全部定义
- [ ] `IRPrinter` 可输出可读的 IR 文本
- [ ] 新增 `tests/test_ir_definition.py`（20+ 测试：操作码分类、Value 创建、BasicBlock 链接等）

### 4.8 风险

| 风险 | 缓解 |
|------|------|
| 操作码设计遗漏 | Phase 2 有完整关键字覆盖，逐一对应 |
| SSA 过于复杂 | Phase 7 先做"非严格 SSA"，变量可多次赋值，用 `ALLOC` + `STORE` 代替 phi 节点 |

---

## 五、M2：AST → IR 生成器

### 5.1 目标

将 AST 完整翻译为 ZHC IR，覆盖所有 AST 节点类型。

### 5.2 设计

```
IRGenerator:
    input:  ProgramNode (AST)
    output: IRProgram (ZHC IR)
    strategy: ASTVisitor 模式（与 CCodeGenerator 一致）
```

### 5.3 执行步骤

#### 步骤 M2.1：IRGenerator 骨架

文件：`src/zhpp/ir/ir_generator.py`

```python
class IRGenerator(ASTVisitor):
    def __init__(self, symbol_table: SymbolTable):
        self.module = IRProgram()
        self.current_function: Optional[IRFunction] = None
        self.current_block: Optional[IRBasicBlock] = None
        self.temp_counter = 0
        self.symbol_table = symbol_table

    def generate(self, ast: ProgramNode) -> IRProgram:
        ast.accept(self)
        return self.module

    def _new_temp(self, ty: ZHCTy) -> IRValue:
        """创建新的临时变量"""
        name = f"%{self.temp_counter}"
        self.temp_counter += 1
        return IRValue(name=name, ty=ty, kind=ValueKind.TEMP)

    def _emit(self, opcode: Opcode, operands, result=None) -> IRInstruction:
        """向当前基本块发射一条指令"""
        instr = IRInstruction(opcode=opcode, operands=operands, result=result)
        self.current_block.instructions.append(instr)
        return instr
```

#### 步骤 M2.2：顶层翻译

按 AST 节点类型逐一实现 visit 方法：

**第一优先级（核心）：**
- `visit_program` → 创建 IRProgram，遍历子节点
- `visit_function_decl` → 创建 IRFunction，创建 entry 基本块，翻译函数体
- `visit_variable_decl` → `ALLOC` + 可选 `STORE`（初始化值）
- `visit_param_decl` → 创建 PARAM 类型的 IRValue
- `visit_block_stmt` → 递归翻译语句
- `visit_return_stmt` → `RET` 指令

**第二优先级（表达式）：**
- `visit_binary_expr` → 翻译左右操作数 + 对应操作码
- `visit_unary_expr` → `NEG` / `L_NOT` / `NOT`
- `visit_assign_expr` → `STORE`（目标 + 值）
- `visit_call_expr` → `CALL` 指令
- `visit_identifier_expr` → `LOAD` 或直接引用
- `visit_int_literal` / `visit_float_literal` / `visit_string_literal` / `visit_bool_literal` → `CONST`

**第三优先级（控制流）：**
- `visit_if_stmt` → JZ/JMP + 新基本块（then/else/merge）
- `visit_while_stmt` → 循环头 + 循环体 + 条件跳转
- `visit_for_stmt` → 初始化 + 条件 + 更新 + 循环体
- `visit_do_while_stmt` → 先执行后判断
- `visit_switch_stmt` → SWITCH 指令 + case 基本块
- `visit_break_stmt` / `visit_continue_stmt` → JMP 到目标块
- `visit_goto_stmt` / `visit_label_stmt` → GOTO + 标签基本块

**第四优先级（高级特性）：**
- `visit_struct_decl` → IRStructDef
- `visit_enum_decl` → 常量序列
- `visit_member_expr` → GET_PTR + LOAD
- `visit_array_expr` → GET_PTR + LOAD
- `visit_cast_expr` → CAST 指令
- `visit_sizeof_expr` → SIZEOF 指令
- `visit_ternary_expr` → 条件分支 + phi 模拟
- `visit_array_init` / `visit_struct_init` → ALLOC + STORE 序列
- `visit_typedef_decl` → 类型别名记录
- `visit_union_decl` → IRStructDef（标记为 union）
- `visit_import_decl` / `visit_module_decl` → 模块信息

#### 步骤 M2.3：函数调用约定

- 普通函数：`CALL func_name, arg1, arg2, ...`
- 标准库函数：标记 `extern`，不生成 IR 函数体
- 函数重载：使用 mangling 名（参数类型后缀）
- 可变参数：标记 `variadic=True`

#### 步骤 M2.4：基本块划分规则

- 每个函数至少有 `entry` 和 `exit` 两个基本块
- 控制流分支点（if/while/for/switch）创建新的基本块
- 每个基本块以 terminator 指令结尾（JMP/JZ/JNZ/RET/SWITCH）
- 基本 block 的 predecessors/successors 自动维护

### 5.4 验收标准

- [ ] 所有 40+ 种 AST 节点均有对应的 visit 方法
- [ ] 语义分析后的简单程序可完整翻译为 IR
- [ ] IR 打印器可输出正确的 IR 文本
- [ ] 控制流结构（if/while/for/switch/循环嵌套）正确生成基本块
- [ ] 新增 `tests/test_ir_generator.py`（30+ 测试）
  - 每种 AST 节点至少 1 个正向测试
  - 控制流结构测试：嵌套 if、while 循环、for 循环、switch
  - 函数调用测试：递归、标准库调用、重载

### 5.5 风险

| 风险 | 缓解 |
|------|------|
| AST 节点遗漏 | 参照 CCodeGenerator 的 48 个 visit 方法清单，逐一对照 |
| 复杂控制流翻译 | 先实现 if/while，再实现 for/switch/do-while，逐步增加 |
| 全局变量跨函数 | Phase 7 先用 GLOBAL_ADDR 指令直接引用，不做复杂跨模块分析 |

---

## 六、M3：IR → C 后端

### 6.1 目标

从 ZHC IR 生成可编译的 C 代码，功能上与现有 CCodeGenerator 等价。

### 6.2 设计

文件：`src/zhpp/ir/c_backend.py`

```python
class CBackend:
    """IR -> C 代码生成器"""

    def __init__(self):
        self.output_lines: List[str] = []
        self.indent = 0
        self.temp_counter = 0
        self.label_counter = 0

    def generate(self, ir: IRProgram) -> str:
        """从 IR 生成完整的 C 代码"""
        # 1. 输出 #include
        # 2. 输出结构体定义
        # 3. 输出全局变量声明
        # 4. 逐个输出函数定义
        return "\n".join(self.output_lines)

    def _emit_function(self, func: IRFunction):
        """将 IR 函数翻译为 C 函数"""
        # 函数签名
        # 基本块 → C 代码（用 goto 和 label 表示基本块）
        # 或：将基本块展平为 C 语句（更可读）

    def _emit_instruction(self, instr: IRInstruction) -> str:
        """将单条 IR 指令翻译为 C 语句"""
        # CONST → 字面量
        # ADD/SUB/MUL/DIV → a + b
        # LOAD/STORE → 变量读写
        # CALL → 函数调用
        # JZ/JMP → if/goto
        # RET → return
```

### 6.3 代码生成策略

**基本块处理**：两种模式可选

- **模式 A（goto 模式）**：每个基本块变成一个 `label: { ... }` + goto 跳转。忠实于 IR 结构，但 C 代码可读性差。
- **模式 B（展平模式）**：将线性基本块合并，只在实际需要分支时才用 goto/if。C 代码更可读，推荐此模式。

推荐：**默认模式 B，通过参数可选模式 A**。

### 6.4 执行步骤

#### 步骤 M3.1：CBackend 骨架

文件：`src/zhpp/ir/c_backend.py`

- `generate(ir: IRProgram) -> str` 入口
- `#include` 自动推断（根据 CALL 指令中引用的函数名）
- 全局变量声明
- 结构体定义

#### 步骤 M3.2：函数翻译

- 函数签名生成（类型 + 参数名）
- 基本块展平算法：
  1. 如果基本块只有一个前驱且前驱只有它一个后继 → 合并
  2. 保留分支/合并基本块的独立性
  3. 用 `if (...) { ... }` 替代 JZ + label
  4. 用 `goto label` 替代 JMP

#### 步骤 M3.3：指令翻译

逐操作码实现翻译逻辑：

- `CONST` → 字面量表达式
- `ALLOC` → 局部变量声明（`int _t0;`）
- `LOAD` → 变量引用
- `STORE` → 赋值
- `ADD/SUB/MUL/DIV/MOD` → 二元运算表达式
- `NEG/NOT/L_NOT` → 一元运算表达式
- `EQ/NE/LT/LE/GT/GE` → 比较表达式
- `CAST` → C 类型转换 `(type)expr`
- `CALL` → 函数调用表达式
- `RET` → `return expr;`
- `JMP/JZ/JNZ` → `goto` / `if`
- `SIZEOF` → `sizeof(type)`
- `GET_PTR` → `&base[offset]` 或 `&base.member`
- `GLOBAL_ADDR` → 直接引用全局变量名

#### 步骤 M3.4：中文函数名映射

复用 `c_codegen.py` 中的映射表：

```python
from zhpp.codegen.c_codegen import TYPE_MAP, MODIFIER_MAP, FUNCTION_NAME_MAP, STDLIB_FUNC_MAP
```

### 6.5 验收标准

- [ ] 所有 IR 操作码均有翻译逻辑
- [ ] 简单 C 程序经 AST→IR→C 后可正确编译运行
- [ ] 生成的 C 代码可读性接近现有 CCodeGenerator 的输出
- [ ] 新增 `tests/test_c_backend.py`（20+ 测试）
- [ ] 与 CCodeGenerator 的输出做**语义等价**对比（不要求文本完全一致）

### 6.6 风险

| 风险 | 缓解 |
|------|------|
| 生成的 C 代码不可编译 | 基本块展平必须正确处理分支合并 |
| 与 CCodeGenerator 输出差异大 | 只要求语义等价，不要求文本一致 |
| 复杂表达式嵌套 | IR 是扁平的三地址码，C 表达式自然简单 |

---

## 七、M4：IR 验证器

### 7.1 目标

在 IR 生成后、优化前，验证 IR 的合法性和一致性。

### 7.2 设计

文件：`src/zhpp/ir/ir_verifier.py`

```python
class IRVerifier:
    """IR 合法性验证器"""

    def verify(self, ir: IRProgram) -> List[VerificationError]:
        errors = []
        errors.extend(self._verify_types(ir))
        errors.extend(self._verify_control_flow(ir))
        errors.extend(self._verify_values(ir))
        return errors
```

### 7.3 检查项

| 检查 | 说明 |
|------|------|
| 类型一致性 | 操作数类型与操作码兼容（不能对浮点数做位运算） |
| 值定义 | 每个使用的 IRValue 必须在此前定义或为参数/全局 |
| 基本块终止 | 每个基本块必须以 terminator（JMP/JZ/JNZ/RET/SWITCH）结尾 |
| 控制流完整性 | 每个基本块的跳转目标必须存在 |
| 入口块 | 每个函数必须有 `entry` 基本块 |
| 无孤儿块 | 所有基本块必须从 entry 可达 |
| 函数返回 | 非空函数的每条路径必须到达 RET |

### 7.4 执行步骤

#### 步骤 M4.1：实现基础检查

- 类型一致性检查
- 值定义检查
- 基本块终止检查

#### 步骤 M4.2：实现控制流检查

- 跳转目标存在性
- 入口块检查
- 可达性分析（从 entry 出发 BFS/DFS）

#### 步骤 M4.3：实现函数完整性检查

- 返回路径检查
- 参数数量匹配

### 7.5 验收标准

- [ ] 7 项检查全部实现
- [ ] 对合法 IR 返回空错误列表
- [ ] 对非法 IR 返回有意义的错误描述
- [ ] 新增 `tests/test_ir_verifier.py`（15+ 测试，覆盖每项检查）

---

## 八、M5：IR 优化 Pass 框架 + 基础 Pass

### 8.1 目标

建立 IR 优化框架，实现 2-3 个实用的优化 Pass。

### 8.2 设计

文件：`src/zhpp/ir/optimizer.py`

```python
class OptimizationPass(ABC):
    """优化 Pass 基类"""
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def run(self, ir: IRProgram) -> IRProgram: ...


class PassManager:
    """优化 Pass 管理器"""
    def __init__(self):
        self.passes: List[OptimizationPass] = []

    def register(self, pass_: OptimizationPass) -> 'PassManager': ...
    def run(self, ir: IRProgram) -> IRProgram: ...  # 按序执行所有 Pass
```

### 8.3 基础 Pass

#### Pass 1：常量折叠（ConstantFolding）

将编译期可计算的常量表达式折叠。

```
优化前:  %1 = CONST 3, int
         %2 = CONST 5, int
         %3 = ADD %1, %2         → 结果 %3 = 8
优化后:  %3 = CONST 8, int
```

适用操作码：ADD/SUB/MUL/DIV/MOD/NEG/NOT/CAST/SIZEOF

#### Pass 2：死代码消除（DeadCodeElimination）

删除不可达的基本块和无用的指令。

```
优化前:
  bb1:
    JMP bb3
  bb2:              ← 不可达
    STORE 1, %0
    JMP bb3
  bb3:
    RET %0

优化后:
  bb1:
    JMP bb3
  bb3:
    RET %0
```

- 不可达基本块消除（基于 CFG 可达性）
- 无用指令消除（结果不被使用的纯计算指令）

#### Pass 3：常量传播（ConstantPropagation）（可选）

将已知的常量值传播到使用点。

```
优化前:  %0 = CONST 42, int
         %1 = ALLOC int
         STORE %0, %1
         %2 = LOAD %1, int     → 已知 %2 = 42
         %3 = ADD %2, 1        → 可进一步常量折叠为 43
```

### 8.4 执行步骤

#### 步骤 M5.1：实现 PassManager

- 注册、执行、日志记录
- 每个 Pass 执行前后可输出变更统计

#### 步骤 M5.2：实现 ConstantFolding

- 遍历所有基本块的所有指令
- 识别 `CONST op CONST` 模式
- 在安全的前提下执行运算（注意除零、溢出）
- 替换为新的 CONST 指令
- 迭代直到无新折叠（fixpoint）

#### 步骤 M5.3：实现 DeadCodeElimination

- CFG 可达性分析，标记不可达块
- 删除不可达块
- 使用-定义分析，删除结果未被使用的纯计算指令

#### 步骤 M5.4：（可选）实现 ConstantPropagation

- 维护已知常量值的映射
- 前向传播到使用点
- 与 ConstantFolding 配合形成优化链

### 8.5 验收标准

- [ ] `PassManager` 支持注册和执行任意 Pass
- [ ] ConstantFolding 正确折叠 +3 5 → 8 等
- [ ] DeadCodeElimination 正确删除不可达块
- [ ] 优化后的 IR 仍通过 IRVerifier 验证
- [ ] 新增 `tests/test_ir_optimizer.py`（20+ 测试）
  - 每个 Pass 至少 5 个测试
  - 组合 Pass 测试（先传播再折叠再消除）

---

## 九、M6：Pipeline 集成 + CLI

### 9.1 目标

将 IR 层完整集成到编译流水线，提供 CLI 控制参数。

### 9.2 Pipeline 改造

```
当前 Pipeline (pipeline.py):
    ast = parse(source)
    semantic_errors = analyze(ast)
    c_code = generate_c(ast)         # CCodeGenerator
    return c_code

目标 Pipeline:
    ast = parse(source)
    semantic_errors = analyze(ast)
    if backend == "ir":
        ir = generate_ir(ast)         # IRGenerator
        verify_ir(ir)                 # IRVerifier
        if optimize:
            ir = optimize(ir)         # PassManager
        c_code = emit_c(ir)           # CBackend
    else:
        c_code = generate_c(ast)      # CCodeGenerator（兼容）
    return c_code
```

### 9.3 执行步骤

#### 步骤 M6.1：改造 pipeline.py

- 新增 `backend` 参数（"ir" / "ast"，默认 "ir"）
- 新增 `optimize` 参数（bool，默认 True）
- IR 路径：analyze → IRGenerator → IRVerifier → PassManager → CBackend
- AST 路径：analyze → CCodeGenerator（保持不变）

#### 步骤 M6.2：新增 CLI 参数

文件：`src/zhpp/cli.py`

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--backend ir\|ast` | `ir` | 选择代码生成后端 |
| `--no-optimize` | 关闭 | 禁用 IR 优化 Pass |
| `--dump-ir` | 关闭 | 打印 IR 到 stdout |
| `--dump-ir-file PATH` | 关闭 | 将 IR 保存到文件 |
| `-O0` / `-O1` / `-O2` | `-O1` | 优化级别（O0=无优化, O1=基础, O2=全部） |

#### 步骤 M6.3：端到端测试

- `zhc hello.zhc` → 使用 IR 后端编译运行
- `zhc --backend ast hello.zhc` → 使用 AST 后端编译运行
- `zhc --dump-ir hello.zhc` → 打印 IR
- `zhc -O0 hello.zhc` → 无优化编译

### 9.4 验收标准

- [ ] Pipeline 支持 `--backend ir` 和 `--backend ast`
- [ ] `--dump-ir` 正确输出 IR 文本
- [ ] `-O0` / `-O1` / `-O2` 正确控制优化级别
- [ ] 现有测试（`--backend ast`）全部通过
- [ ] 新增 IR 路径端到端测试（`tests/test_pipeline_ir.py`）

---

## 十、M7：测试 + 文档 + 清理

### 10.1 测试计划

| 测试文件 | 测试数 | 覆盖范围 |
|----------|--------|----------|
| `tests/test_ir_symbol.py` | 10+ | 统一 Symbol/Scope |
| `tests/test_ir_definition.py` | 20+ | IR 数据结构定义 |
| `tests/test_ir_generator.py` | 30+ | AST→IR 翻译 |
| `tests/test_c_backend.py` | 20+ | IR→C 代码生成 |
| `tests/test_ir_verifier.py` | 15+ | IR 验证器 |
| `tests/test_ir_optimizer.py` | 20+ | 优化 Pass |
| `tests/test_pipeline_ir.py` | 10+ | Pipeline 集成 |
| **新增合计** | **125+** | |

### 10.2 回归测试

- 所有现有测试（586+）使用 `--backend ast` 运行 → 必须全部通过
- 选择 50+ 个代表性测试用例使用 `--backend ir` 运行 → 语义等价验证

### 10.3 文档更新

| 文档 | 更新内容 |
|------|----------|
| `ARCHITECTURE.md` | 更新编译流程图，标注 IR 层 |
| Phase 7 执行计划 | 标记完成状态 |
| IR 设计文档（新建） | IR 指令集参考手册 |

### 10.4 清理

- M0 完成后：删除 `scope_checker.py` 中旧 Symbol 定义
- M6 完成后：CCodeGenerator 标记为 `@deprecated`（不删除）
- 无用导入清理

### 10.5 验收标准

- [ ] 新增 125+ 测试，全部通过
- [ ] 现有 586+ 测试零回归
- [ ] ARCHITECTURE.md 更新
- [ ] 无 lint 错误

---

## 十一、文件变更总清单

### 新建文件

| 文件 | 里程碑 | 说明 |
|------|--------|------|
| `src/zhpp/ir/__init__.py` | M0 | IR 包入口 |
| `src/zhpp/ir/symbol.py` | M0 | 统一 Symbol + Scope |
| `src/zhpp/ir/types.py` | M0 | ZHCTy 类型体系 |
| `src/zhpp/ir/opcodes.py` | M1 | 操作码枚举 |
| `src/zhpp/ir/values.py` | M1 | IRValue 定义 |
| `src/zhpp/ir/instructions.py` | M1 | IRInstruction + IRBasicBlock |
| `src/zhpp/ir/program.py` | M1 | IRProgram + IRFunction |
| `src/zhpp/ir/printer.py` | M1 | IR 文本打印器 |
| `src/zhpp/ir/ir_generator.py` | M2 | AST→IR 生成器 |
| `src/zhpp/ir/c_backend.py` | M3 | IR→C 后端 |
| `src/zhpp/ir/ir_verifier.py` | M4 | IR 验证器 |
| `src/zhpp/ir/optimizer.py` | M5 | PassManager + 优化 Pass |
| `tests/test_ir_symbol.py` | M0 | Symbol 测试 |
| `tests/test_ir_definition.py` | M1 | IR 定义测试 |
| `tests/test_ir_generator.py` | M2 | IR 生成器测试 |
| `tests/test_c_backend.py` | M3 | C 后端测试 |
| `tests/test_ir_verifier.py` | M4 | 验证器测试 |
| `tests/test_ir_optimizer.py` | M5 | 优化器测试 |
| `tests/test_pipeline_ir.py` | M6 | Pipeline 集成测试 |

### 修改文件

| 文件 | 里程碑 | 修改内容 |
|------|--------|----------|
| `src/zhpp/semantic/semantic_analyzer.py` | M0 | Symbol 导入迁移 |
| `src/zhpp/analyzer/scope_checker.py` | M0 | 删除旧 Symbol 定义，改为导入 |
| `src/zhpp/analyzer/type_checker.py` | M0 | TypeInfo 导入路径迁移 |
| `src/zhpp/compiler/pipeline.py` | M6 | 插入 IR 生成/优化/后端步骤 |
| `src/zhpp/cli.py` | M6 | 新增 CLI 参数 |
| `ARCHITECTURE.md` | M7 | 更新架构图 |

---

## 十二、执行顺序与依赖图

```
M0 (Symbol 统一)
 ├── M1 (IR 定义)
 │    ├── M2 (AST→IR 生成器)
 │    │    └── M6 (Pipeline 集成)
 │    ├── M3 (IR→C 后端)
 │    │    └── M6 (Pipeline 集成)
 │    ├── M4 (IR 验证器)
 │    │    └── M6 (Pipeline 集成)
 │    └── M5 (IR 优化 Pass)
 │         └── M6 (Pipeline 集成)
 └── M7 (测试 + 文档)
```

**推荐执行顺序**：M0 → M1 → M4 → M2 → M3 → M5 → M6 → M7

理由：
1. M0 先行，为 M1 提供统一的类型基础
2. M1 先行，所有后续里程碑依赖 IR 定义
3. M4（验证器）在 M2 之前实现，这样 M2 开发过程中可以边写边验证
4. M2 和 M3 可并行（M2 产出的 IR 即是 M3 的输入）
5. M5 在 M2/M3 之后，需要完整的 IR 生成才能测试优化
6. M6 最后集成
7. M7 收尾

---

## 十三、风险矩阵

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| IR 设计不适合多后端 | 低 | 高 | 参考 LLVM IR / CPython bytecode，预留扩展点 |
| AST→IR 翻译遗漏节点 | 中 | 中 | 参照 CCodeGenerator 的 48 个 visit 方法，逐一对照 |
| IR→C 生成质量下降 | 低 | 中 | CCodeGenerator 作为参照基准 |
| 现有 586+ 测试需要适配 | 中 | 中 | `--backend ast` 兼容路径，不破坏现有测试 |
| SSA 复杂度超出预期 | 中 | 中 | 放弃严格 SSA，用 ALLOC+STORE 替代 phi 节点 |
| 两套后端并行维护成本 | 低 | 低 | Phase 7 完成后再考虑废弃 AST 路径 |
| Symbol 迁移破坏现有代码 | 中 | 中 | 保留旧类作为别名，渐进迁移 |

---

## 十四、Phase 8 展望

Phase 7 完成后，编译器具备：
- 完整的 IR 中间表示层
- AST → IR → C 三阶段编译
- IR 级优化能力（常量折叠 + 死代码消除 + 可选常量传播）
- IR 合法性验证
- 统一的 Symbol 体系

**Phase 8 候选方向**：
1. **LLVM 后端** — IR → LLVM IR → 机器码（原生性能）
2. **WASM 后端** — IR → WASM（浏览器运行）
3. **高级优化 Pass** — 循环展开、内联、公共子表达式消除
4. **模块级 IR 链接** — 多文件编译时的跨模块优化
5. **增量编译** — 基于已有的 AST 缓存 + IR 缓存

---

*Phase 7 v1.0 执行计划。等待实施。*

# ZhC 多语言前端扩展规划执行文档

> **文档版本**：v1.0
> **编制日期**：2026-04-12
> **编制人**：AI 助手
> **项目**：ZhC 中文C编译器
> **目标**：扩展支持标准 C 和 Python 编程语言

---

## 一、项目背景

### 1.1 ZhC 现状

| 维度 | 详情 |
|:---|:---|
| **项目名称** | ZhC（中文C编译器） |
| **版本** | v6.0.0 |
| **编译器语言** | Python 3.10+ |
| **源语言** | ZHC（中文C语法） |
| **编译目标** | LLVM IR → 机器码 |
| **核心依赖** | llvmlite ≥ 0.47.0 |
| **源码规模** | ~100+ Python 模块 |
| **测试覆盖** | 143 个测试文件，3330 个用例 |
| **C 运行时库** | 39 个 C/H 运行时文件 |

### 1.2 当前编译流水线

```
.zhc 源文件
    ↓
[ ZHC Lexer ]        ← 中文关键词映射（keywords.py，258个关键词）
    ↓
[ ZHC Parser ]       ← 手写递归下降，生成 AST
    ↓
[ Semantic Analyzer ] ← 类型检查、作用域分析
    ↓
[ IR Generator ]     ← AST → ZHC IR（自定义中间表示）
    ↓
[ IR Optimizer ]     ← 常量折叠、死代码消除等优化 Pass
    ↓
[ LLVM Backend ]     ← IR → LLVM IR → 机器码
    ↓
可执行文件
```

### 1.3 扩展目标

本次扩展旨在不改变现有编译流水线核心的前提下，**新增 C 和 Python 两个前端**，使 ZhC 成为多语言编译器基础设施。

---

## 二、扩展方案：技术实现

### 2.1 整体架构设计

```
                        ┌──────────────────────────────────────┐
                        │         ZhC Compiler Core            │
                        │                                      │
                        │  · 语义分析（Semantic Analyzer）       │
                        │  · IR 生成器（IR Generator）          │
                        │  · IR 优化器（IROptimizer）          │
                        │  · LLVM 后端（LLVM Backend）          │
                        │  · C 运行时库（lib/）                │
                        └──────────────┬───────────────────────┘
                                       │
               ┌───────────────────────┼───────────────────────┐
               │                       │                       │
        ┌──────▼──────┐        ┌──────▼──────┐        ┌──────▼──────┐
        │  ZHC 前端   │        │   C 前端    │        │ Python 前端 │
        │  (已有)     │        │  (新增)     │        │   (新增)    │
        ├─────────────┤        ├─────────────┤        ├─────────────┤
        │ keywords.py│        │ stdlib.c    │        │ stdlib.c    │
        │ lexer.py   │        │ parser.py   │        │ parser.py   │
        │ parser.py  │        │ ast_bridge.py        │ type_map.py │
        │            │        │             │        │ builtin.py  │
        └─────────────┘        └─────────────┘        └─────────────┘

输入输出：
  .zhc 文件 → 机器码    （已有）
  .c 文件  → 机器码    （新增 C 前端）
  .py 文件 → 机器码    （新增 Python 前端）
```

### 2.2 编译器流水线改造

#### 2.2.1 新增前端路由层

在 `compiler/pipeline.py` 中增加语言检测和前端路由：

```python
# src/zhc/compiler/pipeline.py

class CompilationPipeline:
    """多语言编译流水线"""

    FRONTENDS = {
        "zhc": "zhc_frontend.ZhcFrontend",
        "c": "zhc_c_frontend.CFrontend",
        "python": "zhc_python_frontend.PythonFrontend",
    }

    def __init__(self, backend="llvm"):
        self.semantic_analyzer = SemanticAnalyzer()
        self.ir_generator = IRGenerator()
        self.ir_optimizer = IROptimizer()
        self.backend = self._create_backend(backend)

    def run(self, source: str, source_path: str, lang: str = "auto") -> CompileResult:
        """执行编译流水线

        Args:
            source: 源代码内容
            source_path: 源文件路径
            lang: 语言模式 - "zhc" | "c" | "python" | "auto"

        Returns:
            编译结果（包含输出、诊断信息等）
        """
        # ① 语言检测
        if lang == "auto":
            lang = LanguageDetector.detect(source_path, source)

        # ② 前端路由
        frontend = self._get_frontend(lang)
        ast = frontend.parse(source)

        # ③ 后续流水线复用（无需改动）
        typed_ast = self.semantic_analyzer.analyze(ast)
        ir = self.ir_generator.generate(typed_ast)
        optimized_ir = self.ir_optimizer.optimize(ir)

        return self.backend.compile(optimized_ir)

    def _get_frontend(self, lang: str):
        if lang == "zhc":
            return ZhcFrontend()          # 已有
        elif lang == "c":
            return CFrontend()             # 新增
        elif lang == "python":
            return PythonFrontend()         # 新增
        else:
            raise BackendError(f"不支持的语言: {lang}")
```

#### 2.2.2 语言自动检测器

```python
# src/zhc/lang_detector.py

import os

class LanguageDetector:
    """自动检测源文件语言类型"""

    EXTENSION_MAP = {
        ".zhc": "zhc",
        ".c": "c",
        ".h": "c",
        ".py": "python",
    }

    FIRST_LINE_HINTS = {
        "int": "c",           # int main() {
        "def": "python",     # def foo():
        "整数型": "zhc",      # 整数型 主函数()
        "整数型": "zhc",      # 中文关键词
    }

    @classmethod
    def detect(cls, source_path: str, source: str) -> str:
        """检测语言类型

        优先级：① 文件扩展名 → ② 首行关键词检测
        """
        # ① 扩展名检测（最可靠）
        _, ext = os.path.splitext(source_path.lower())
        if ext in cls.EXTENSION_MAP:
            return cls.EXTENSION_MAP[ext]

        # ② 首行关键词检测
        first_line = source.strip().split("\n")[0]
        for hint, lang in cls.FIRST_LINE_HINTS.items():
            if hint in first_line:
                return lang

        # ③ 默认使用 ZHC（向后兼容）
        return "zhc"
```

### 2.3 C 前端实现方案

#### 2.3.1 目录结构

```
src/zhc_c/                          # C 前端包（新增）
├── __init__.py
├── tokens.py                       # C Token 类型定义
├── lexer.py                       # C 词法分析器
├── parser.py                      # C 语法分析器
├── ast_bridge.py                  # C AST → ZHC 通用 AST 桥接器
└── keywords.py                    # C 关键词表
```

#### 2.3.2 C 关键词表

```python
# src/zhc_c/keywords.py

C_KEYWORDS = {
    # C11/C17 标准关键词
    "auto": "auto",
    "break": "break",
    "case": "case",
    "char": "char",
    "const": "const",
    "continue": "continue",
    "default": "default",
    "do": "do",
    "double": "double",
    "else": "else",
    "enum": "enum",
    "extern": "extern",
    "float": "float",
    "for": "for",
    "goto": "goto",
    "if": "if",
    "inline": "inline",
    "int": "int",
    "long": "long",
    "register": "register",
    "restrict": "restrict",
    "return": "return",
    "short": "short",
    "signed": "signed",
    "sizeof": "sizeof",
    "static": "static",
    "struct": "struct",
    "switch": "switch",
    "typedef": "typedef",
    "union": "union",
    "unsigned": "unsigned",
    "void": "void",
    "volatile": "volatile",
    "while": "while",

    # C99 布尔类型
    "_Bool": "_Bool",

    # C99 复数类型
    "_Complex": "_Complex",
    "_Imaginary": "_Imaginary",

    # C11 线程局部存储
    "_Thread_local": "_Thread_local",

    # C11 对齐
    "_Alignas": "_Alignas",
    "_Alignof": "_Alignof",
    "_Atomic": "_Atomic",
    "_Static_assert": "_Static_assert",
    "_Noreturn": "_Noreturn",

    # 扩展关键词（GCC/Clang）
    "__builtin_va_list": "__builtin_va_list",
    "__attribute__": "__attribute__",
    "__restrict": "__restrict",
    "__inline": "__inline",
}
```

#### 2.3.3 C Lexer（词法分析器）

```python
# src/zhc_c/lexer.py
# 设计与 ZHC Lexer 接口完全一致，内部处理英文关键词

from .tokens import CTokenType, Token

class CLexer:
    """C 语言词法分析器

    与 ZHC Lexer 接口一致：
        lexer.tokenize(source) → List[Token]
        Token(name, value, line, column)
    """

    def __init__(self):
        self.keywords = C_KEYWORDS   # 英文关键词表

    def tokenize(self, source: str) -> list[Token]:
        """将 C 源代码转换为 Token 序列"""
        # 实现与 ZHC Lexer 相同的分词逻辑
        # · 识别数字字面量（十进制、八进制、十六进制、浮点数、科学计数）
        # · 识别字符串字面量（含转义序列）
        # · 识别标识符和关键词
        # · 识别运算符和分隔符
        # · 跳过 C 风格注释 // 和 /* */
        # · 保留预处理器指令 #include, #define 等（透传到输出）
        pass
```

#### 2.3.4 C Parser + AST 桥接

**核心思路：C AST → ZHC 通用 AST**

这是 C 前端最关键的部分。C Parser 将 C 代码解析为中间 AST，然后通过桥接器转换为 ZHC 编译器的通用 AST 节点，后续流水线完全复用。

```python
# src/zhc_c/ast_bridge.py

from zhc.parser.ast_nodes import (
    ProgramNode, FunctionDeclNode, VariableDeclNode,
    BlockStmtNode, IfStmtNode, WhileStmtNode, ForStmtNode,
    ReturnStmtNode, BreakStmtNode, ContinueStmtNode,
    BinaryExprNode, UnaryExprNode, CallExprNode,
    PrimitiveTypeNode, PointerTypeNode, ArrayTypeNode,
    StructTypeNode, IdentifierExprNode,
    IntLiteralNode, FloatLiteralNode, StringLiteralNode,
)

# C 类型名 → ZHC 类型名的映射
C_TYPE_TO_ZHC = {
    "int": "整数型",
    "char": "字符型",
    "float": "浮点型",
    "double": "双精度浮点型",
    "void": "空型",
    "long": "长整数型",
    "short": "短整数型",
    "signed": "有符号整数型",
    "unsigned": "无符号整数型",
    "_Bool": "逻辑型",
    "int8_t": "整数型",        # stdint.h 类型映射
    "int16_t": "整数型",
    "int32_t": "长整数型",
    "int64_t": "长长整数型",
    "uint8_t": "无符号整数型",
    "size_t": "无符号长整数型",
    "ssize_t": "长整数型",
    "FILE": "文件型",          # stdio.h
    "FILE*": "文件型*",
}

class CAstBridge:
    """C AST → ZHC 通用 AST 桥接器

    设计原则：
    - 输入：C Parser 生成的中间 AST
    - 输出：与 ZHC Parser 输出一致的 AST 节点
    - 后续流水线（语义分析、IR生成、后端）完全无感知
    """

    def transform(self, c_ast) -> ProgramNode:
        """执行 C AST → ZHC AST 转换"""
        # 函数声明转换
        for func in c_ast.functions:
            zhc_func = self._transform_function(func)

        # 变量声明转换
        for var in c_ast.globals:
            zhc_var = self._transform_global_variable(var)

        # 结构体/枚举/联合体转换
        for decl in c_ast.types:
            zhc_type = self._transform_type_decl(decl)

        return ProgramNode(declarations=[...])

    def _transform_function(self, c_func) -> FunctionDeclNode:
        """函数声明转换

        C:  int add(int a, int b) { return a + b; }
        ZHC: 整数型 add(整数型 a, 整数型 b) {
                  返回 a + b;
              }
        """
        return_type = self._transform_type(c_func.return_type)
        params = [self._transform_param(p) for p in c_func.params]
        body = self._transform_statement(c_func.body)

        return FunctionDeclNode(
            name=c_func.name,
            return_type=return_type,
            params=params,
            body=body,
        )

    def _transform_type(self, c_type) -> ASTNode:
        """C 类型 → ZHC 类型

        处理：
        - 基础类型（int → 整数型）
        - 指针类型（int* → 整数型*）
        - 数组类型（int[10] → 整数型[10]）
        - const/volatile 修饰符
        """
        if isinstance(c_type, PointerType):
            base = self._transform_type(c_type.base_type)
            return PointerTypeNode(base)
        elif isinstance(c_type, ArrayType):
            base = self._transform_type(c_type.base_type)
            return ArrayTypeNode(base, c_type.size)
        else:
            zhc_name = C_TYPE_TO_ZHC.get(c_type.name, c_type.name)
            return PrimitiveTypeNode(zhc_name)
```

### 2.4 Python 前端实现方案

#### 2.4.1 目录结构

```
src/zhc_python/                          # Python 前端包（新增）
├── __init__.py
├── tokens.py                           # Python Token 定义
├── lexer.py                            # Python 词法分析器
├── parser.py                           # Python → ZHC AST 转换器
├── type_mapping.py                     # Python 类型 → ZHC 类型映射
├── type_inference.py                    # Python 动态类型静态推导
├── builtin_mappings.py                  # Python 内置函数映射表
├── transformers.py                      # 高级语法转换器
│                                        #   · 列表推导 → 循环
│                                        #   · 生成器 → 协程
│                                        #   · with 语句 → 初始化/清理
└── stdlib/                            # Python 标准库模拟（用 ZHC/C 实现）
    ├── builtins.py                     # __builtins__ 映射
    ├── list.py                         # list 类型
    ├── dict.py                         # dict 类型
    └── str.py                          # str 类型
```

#### 2.4.2 Python 类型系统 → ZHC 类型系统

```python
# src/zhc_python/type_mapping.py

PYTHON_TYPE_TO_ZHC = {
    # 基础类型（可静态映射）
    "int": "长整数型",           # Python int → C long long（64位）
    "float": "双精度浮点型",    # Python float → C double
    "bool": "逻辑型",           # Python bool → C _Bool
    "None": "空型",             # Python None → C void*

    # 字符串（UTF-8 指针）
    "str": "结构体 PyString*",  # Python str → 自定义 PyString 结构体

    # 复合类型（需要运行时实现）
    "list": "结构体 PyList*",   # Python list → 自定义结构体
    "tuple": "结构体 PyTuple*", # Python tuple → 自定义结构体
    "dict": "结构体 PyDict*",   # Python dict → 自定义结构体
    "set": "结构体 PySet*",     # Python set → 自定义结构体

    # 特殊类型
    "object": "结构体 PyObject*",  # 一切皆对象
    "bytes": "字符型*",            # Python bytes → C char*
    "type": "结构体 PyType*",      # 类型对象
}

# Python 动态特性处理策略
DYNAMIC_FEATURE_STRATEGIES = {
    "变量类型动态": "尽力静态推导 + 运行时类型检查兜底（zhc_type_check）",
    "多态/鸭子类型": "编译时检测调用链 + 函数指针表（vtable）模拟",
    "属性动态添加": "__dict__ 哈希表模拟（性能损耗 3~5x）",
    "eval/exec": "受限支持（静态可分析的表达式/语句）",
    "运行时生成代码": "不支持（__code__ 对象编译时拒绝）",
    "GIL": "无 GIL，直接编译为多线程（用户需手动处理同步）",
    "垃圾回收": "引用计数（retain/release）替代 GC",
}
```

#### 2.4.3 Python 内置函数映射

```python
# src/zhc_python/builtin_mappings.py

# Python 内置函数 → ZHC/C 函数映射
# 优先级：直接映射 > C实现 > Python stub

BUILTIN_FUNCTION_MAP = {
    # 直接映射（ZHC/C 有等价实现）
    "print": "打印",
    "abs": "绝对值",
    "min": "最小值",
    "max": "最大值",
    "len": "长度",
    "chr": "字符码转字符",
    "ord": "字符转码点",
    "round": "四舍五入",
    "pow": "幂函数",
    "hex": "转十六进制",
    "oct": "转八进制",
    "bin": "转二进制",

    # 需要 C 库实现
    "input": "zhc_input",          # → 标准输入读取
    "open": "zhc_fopen",           # → stdio fopen
    "range": "zhc_range",          # → 生成数组/迭代器
    "enumerate": "zhc_enumerate",  # → 索引+值对
    "zip": "zhc_zip",              # → 合并迭代器
    "map": "zhc_map",               # → 函数映射
    "filter": "zhc_filter",        # → 函数过滤
    "sorted": "zhc_排序",           # → 排序算法

    # Python 语义重新实现
    "int": "zhc_py_int",            # 宽松类型转换
    "str": "zhc_py_str",            # 统一字符串
    "float": "zhc_py_float",
    "list": "zhc_py_list",
    "dict": "zhc_py_dict",
    "bool": "zhc_py_bool",
    "isinstance": "zhc_is_instance",     # 运行时类型检查
    "hasattr": "zhc_has_attr",            # 属性存在性检查
    "getattr": "zhc_get_attr",            # 动态属性获取
    "setattr": "zhc_set_attr",            # 动态属性设置
    "type": "zhc_get_type",               # 获取类型对象
    "id": "zhc_id",                       # 对象标识
    "hash": "zhc_hash",                   # 哈希值
    "repr": "zhc_repr",                   # 字符串表示
}

# 每个 zhc_xxx 函数需对应 C 实现，详见 src/zhc/lib/zhc_python_stdlib.c
```

#### 2.4.4 Python Parser（Python → ZHC AST 转换器）

```python
# src/zhc_python/parser.py

"""
Python 语法分析器

实现策略：
1. 利用 Python 标准库 ast 模块解析 Python 源码
2. 遍历 Python AST，转换为等价的 ZHC AST
3. Python 特有语法（列表推导、with、lambda 等）展开为等价 ZHC 代码

核心转换对照表：

  Python                     ZHC
  ─────────────────────────────────────────────
  def f(x):                  类型 f(类型 x) {
  x = 10                     类型 x = 10;
  print(x)                   打印(x);
  if x > 0:                  如果 (x > 0) {
  for i in range(n):         循环 (整数型 i = 0; i < n; i++) {
  while True:                判断 (1) {
  [x*2 for x in lst]         循环展开（见下方）
  lambda x: x*2              ({x} -> x*2)
  try: / except:             尝试 { } 捕获 { }
  class Foo:                 结构体 Foo {
"""

import ast
from typing import Optional

from zhc.parser.ast_nodes import (
    ProgramNode, FunctionDeclNode, VariableDeclNode,
    BlockStmtNode, IfStmtNode, WhileStmtNode, ForStmtNode,
    ReturnStmtNode, BinaryExprNode, CallExprNode,
    PrimitiveTypeNode, PointerTypeNode,
    IdentifierExprNode, IntLiteralNode, StringLiteralNode,
)
from .type_mapping import PYTHON_TYPE_TO_ZHC, DYNAMIC_FEATURE_STRATEGIES
from .type_inference import TypeInferrer
from .builtin_mappings import BUILTIN_FUNCTION_MAP


class PythonToZhcTransformer(ast.NodeVisitor):
    """Python AST → ZHC AST 转换器"""

    def __init__(self):
        self.type_inferrer = TypeInferrer()
        self.current_scope = []
        self.functions = []
        self.globals = []
        self.structs = []     # 类定义 → 结构体
        self.type_map = dict(PYTHON_TYPE_TO_ZHC)

    # ──────────────── 顶层结构 ────────────────

    def visit_Module(self, node: ast.Module) -> ProgramNode:
        """模块 → 程序"""
        stmts = [self.visit(stmt) for stmt in node.body]
        return ProgramNode(declarations=stmts, line=1, column=0)

    # ──────────────── 函数定义 ────────────────

    def visit_FunctionDef(self, node: ast.FunctionDef) -> FunctionDeclNode:
        """函数定义

        Python: def add(a, b=10) -> int:
        ZHC:    长整数型 add(长整数型 a, 长整数型 b) {
        """
        # ① 推导参数类型
        params = []
        for i, arg in enumerate(node.args.args):
            inferred = self.type_inferrer.infer(arg, node.args.defaults)
            param_type = self._resolve_type(inferred)
            params.append(ParamDeclNode(
                name=arg.arg,
                param_type=param_type,
                default_value=None,  # 默认参数需特殊处理
            ))

        # ② 推导返回类型
        return_type = self.type_inferrer.infer_return_type(node)
        zhc_return_type = self._resolve_type(return_type)

        # ③ 函数体
        body_stmts = [self.visit(stmt) for stmt in node.body]
        body = BlockStmtNode(statements=body_stmts)

        return FunctionDeclNode(
            name=node.name,
            return_type=zhc_return_type,
            params=params,
            body=body,
            line=node.lineno,
        )

    # ──────────────── 循环语句 ────────────────

    def visit_For(self, node: ast.For) -> ASTNode:
        """for 循环转换

        两种模式：
        ① for i in range(n):     → 索引循环（高效）
        ② for item in iterable:   → 迭代器循环（用索引模拟）
        """
        # 模式①：range() 循环 → 直接转换为 ZHC for
        if isinstance(node.iter, ast.Call):
            if isinstance(node.iter.func, ast.Name):
                if node.iter.func.id == "range":
                    return self._transform_range_for(node)

        # 模式②：一般迭代 → 转换为 while + 索引
        return self._transform_iterator_for(node)

    def _transform_range_for(self, node: ast.For) -> ForStmtNode:
        """range() 循环优化

        Python: for i in range(start, stop, step):
        ZHC:    循环 (整数型 i = start; i < stop; i += step) { }
        """
        args = node.iter.args
        iter_var = node.target.id if isinstance(node.target, ast.Name) else "_i"

        # 提取 range 参数
        if len(args) == 1:         # range(stop)
            init = IntLiteralNode(0)
            stop = self.visit(args[0])
            step = IntLiteralNode(1)
        elif len(args) == 2:       # range(start, stop)
            init = self.visit(args[0])
            stop = self.visit(args[1])
            step = IntLiteralNode(1)
        else:                       # range(start, stop, step)
            init = self.visit(args[0])
            stop = self.visit(args[1])
            step = self.visit(args[2])

        # 循环体（含用户代码）
        body_stmts = []
        if isinstance(node.target, ast.Name):
            body_stmts.append(AssignExprNode(
                left=IdentifierExprNode(node.target.id),
                right=IdentifierExprNode(iter_var),
            ))
        for stmt in node.body:
            body_stmts.append(self.visit(stmt))

        return ForStmtNode(
            init=VariableDeclNode(name=iter_var, var_type=PrimitiveTypeNode("整数型"), init=init),
            condition=BinaryExprNode("<", IdentifierExprNode(iter_var), stop),
            update=BinaryExprNode("+=", IdentifierExprNode(iter_var), step),
            body=BlockStmtNode(statements=body_stmts),
        )

    def _transform_iterator_for(self, node: ast.For) -> WhileStmtNode:
        """通用迭代器循环（用索引模拟）

        Python: for item in mylist:
        ZHC:    {
                    整数型 _len = 长度(mylist);
                    整数型 _i = 0;
                    判断 (_i < _len) {
                        类型 item = mylist[_i];
                        // 用户代码
                        _i = _i + 1;
                    }
                }
        """
        iter_var = self._gensym("_iter")
        len_var = self._gensym("_len")
        idx_var = self._gensym("_i")

        iter_expr = self.visit(node.iter)
        iter_type = self.type_inferrer.infer_expr(node.iter)
        item_type = self._resolve_type(iter_type)

        body_stmts = [
            # item = mylist[_i]
            VariableDeclNode(
                name=node.target.id if isinstance(node.target, ast.Name) else "_item",
                var_type=item_type,
                init=ArrayExprNode(iter_expr, IdentifierExprNode(idx_var)),
            ),
        ]
        for stmt in node.body:
            body_stmts.append(self.visit(stmt))
        body_stmts.append(AssignExprNode(
            left=IdentifierExprNode(idx_var),
            right=BinaryExprNode("+", IdentifierExprNode(idx_var), IntLiteralNode(1)),
        ))

        return BlockStmtNode(statements=[
            VariableDeclNode(name=len_var, var_type=PrimitiveTypeNode("无符号长整数型"), init=CallExprNode("长度", [iter_expr])),
            VariableDeclNode(name=idx_var, var_type=PrimitiveTypeNode("整数型"), init=IntLiteralNode(0)),
            WhileStmtNode(
                condition=BinaryExprNode("<", IdentifierExprNode(idx_var), IdentifierExprNode(len_var)),
                body=BlockStmtNode(statements=body_stmts),
            ),
        ])

    # ──────────────── 列表推导 ────────────────

    def visit_ListComp(self, node: ast.ListComp) -> ASTNode:
        """列表推导 → 循环展开

        Python: [x*2 for x in range(10) if x > 5]
        ZHC:    {
                    结构体 PyList* 结果 = zhc_py_list_create(10);
                    循环 (整数型 _i = 0; _i < 10; _i++) {
                        整数型 x = _i;
                        如果 (x > 5) {
                            整数型 _val = x * 2;
                            zhc_list_append(结果, &_val);
                        }
                    }
                    返回 结果;
                }
        """
        return self._expand_list_comp(node)

    # ──────────────── 类定义 ────────────────

    def visit_ClassDef(self, node: ast.ClassDef) -> StructDeclNode:
        """类定义 → 结构体

        映射规则：
        - 数据属性 → 结构体字段
        - 方法 → 结构体方法（独立函数 + vtable）
        - __init__ → 构造函数
        - __str__ → toString 方法
        - 实例属性 → 运行时通过 __dict__ 模拟
        - 多态 → vtable（函数指针表）
        """
        fields = []    # 结构体字段
        methods = []  # 结构体方法
        vtable = []   # vtable 函数指针

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method = self._transform_class_method(item, node.name)
                methods.append(method)
                vtable.append(method.name)
            elif isinstance(item, ast.AnnAssign):   # 带类型注解的属性
                field = self._transform_class_field(item)
                fields.append(field)

        # 生成 vtable 类型
        vtable_type = self._create_vtable_type(node.name, vtable)

        return StructDeclNode(
            name=node.name,
            fields=fields + [vtable_type],
            methods=methods,
        )

    # ──────────────── 辅助方法 ────────────────

    def _resolve_type(self, python_type: str) -> PrimitiveTypeNode:
        """Python 类型名 → ZHC 类型节点"""
        zhc_name = self.type_map.get(python_type, "结构体 PyObject*")
        return PrimitiveTypeNode(zhc_name)

    def _gensym(self, prefix: str = "_tmp") -> str:
        """生成唯一临时变量名"""
        self._counter = getattr(self, "_counter", 0) + 1
        return f"{prefix}{self._counter}"

    def visit_Call(self, node: ast.Call) -> CallExprNode:
        """函数调用转换

        · Python 内置函数 → ZHC 函数名
        · 普通函数调用 → 直接映射
        """
        if isinstance(node.func, ast.Name):
            zhc_name = BUILTIN_FUNCTION_MAP.get(node.func.id, node.func.id)
        else:
            zhc_name = self.visit(node.func)

        args = [self.visit(arg) for arg in node.args]
        return CallExprNode(function=zhc_name, arguments=args)
```

#### 2.4.5 Python 标准库 C 实现

```c
/* src/zhc/lib/zhc_python_stdlib.c
 *
 * Python 内置类型的 C 实现
 *
 * 策略：
 * · 一切皆对象：所有 Python 值都是 PyObject* 指针
 * · 引用计数：Py_INCREF / Py_DECREF 管理生命周期
 * · UTF-8 字符串：使用标准 C 库 mbstate 处理多字节
 */

#include "zhc_python_stdlib.h"
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <locale.h>

/* ────────────────── PyObject 基类 ────────────────── */

typedef struct PyObject {
    PyTypeObject* ob_type;    // 类型对象指针
    int ob_refcnt;            // 引用计数
} PyObject;

#define Py_INCREF(op)   ((op)->ob_refcnt++)
#define Py_DECREF(op)  do { if (--((op)->ob_refcnt) <= 0) PyObject_Free(op); } while(0)

/* ────────────────── PyList 实现 ────────────────── */

typedef struct {
    PyObject ob_base;
    PyObject** items;         // 元素指针数组
    Py_ssize_t allocated;     // 已分配槽数
    Py_ssize_t size;          // 实际元素数
} PyList;

PyTypeObject PyList_Type;

PyObject* zhc_list_create(Py_ssize_t initial_size) {
    PyList* list = PyObject_Malloc(sizeof(PyList));
    list->ob_base.ob_type = &PyList_Type;
    list->ob_base.ob_refcnt = 1;
    list->allocated = initial_size > 0 ? initial_size : 4;
    list->size = 0;
    list->items = PyObject_Malloc(list->allocated * sizeof(PyObject*));
    return (PyObject*)list;
}

Py_ssize_t zhc_len(PyObject* obj) {
    if (obj->ob_type == &PyList_Type) {
        return ((PyList*)obj)->size;
    }
    return -1;  // TypeError
}

int zhc_list_append(PyObject* obj, PyObject* item) {
    PyList* list = (PyList*)obj;
    if (list->size >= list->allocated) {
        list->allocated *= 2;
        list->items = PyObject_Realloc(list->items, list->allocated * sizeof(PyObject*));
    }
    list->items[list->size++] = item;
    Py_INCREF(item);
    return 0;
}

/* ────────────────── PyDict 实现 ────────────────── */

typedef struct PyDictEntry {
    PyObject* key;
    PyObject* value;
    Py_hash_t hash;
    char state;  // 0=empty, 1=active, 2=deleted
} PyDictEntry;

typedef struct {
    PyObject ob_base;
    PyDictEntry* entries;
    Py_ssize_t size;        // 实际键值对数
    Py_ssize_t allocated;   // 哈希表大小
} PyDict;

PyObject* zhc_dict_create(void) { /* 类似实现 */ }
PyObject* zhc_dict_get(PyObject* dict, PyObject* key) { /* 哈希查找 */ }
int zhc_dict_set(PyObject* dict, PyObject* key, PyObject* value) { /* 插入 */ }
int zhc_dict_contains(PyObject* dict, PyObject* key) { /* 成员检查 */ }

/* ────────────────── PyString 实现 ────────────────── */

typedef struct {
    PyObject ob_base;
    char* data;              // UTF-8 编码
    Py_ssize_t length;       // 字符数（非字节数）
    Py_ssize_t hash;        // 缓存的哈希值
} PyString;

PyObject* zhc_py_str(PyObject* obj) {
    // 将任意 Python 对象转为字符串表示
}

/* ────────────────── Python 内置函数包装 ────────────────── */

PyObject* zhc_input(PyObject* prompt) {
    if (prompt != NULL && prompt != Py_None) {
        打印("%s", zhc_string_data(prompt));
    }
    char buf[1024];
    scanf("%1023s", buf);  // 简化实现
    return zhc_py_str_from_c(buf);
}

PyObject* zhc_range(Py_ssize_t start, Py_ssize_t stop, Py_ssize_t step) {
    // 生成列表：range(start, stop, step) → [start, start+step, ...]
    Py_ssize_t n = (stop - start + step - 1) / step;
    PyObject* result = zhc_list_create(n);
    for (Py_ssize_t i = 0; i < n; i++) {
        zhc_list_append(result, zhc_py_int_from_long(start + i * step));
    }
    return result;
}

/* ────────────────── 类型检查 ────────────────── */

int zhc_is_instance(PyObject* obj, const char* type_name) {
    return strcmp(obj->ob_type->tp_name, type_name) == 0;
}

/* ────────────────── 类型对象定义 ────────────────── */

typedef struct PyTypeObject {
    const char* tp_name;
    Py_ssize_t tp_basicsize;
    // ... 其他类型字段
} PyTypeObject;

PyTypeObject PyList_Type = {
    .tp_name = "list",
    .tp_basicsize = sizeof(PyList),
};

PyTypeObject PyDict_Type = {
    .tp_name = "dict",
    .tp_basicsize = sizeof(PyDict),
};

PyTypeObject PyStr_Type = {
    .tp_name = "str",
    .tp_basicsize = sizeof(PyString),
};
```

---

## 三、扩展意义与价值分析

### 3.1 为什么做 C 前端：技术验证 + 实用补充

#### 3.1.1 C 前端的核心价值

**① 复用 LLVM 优化流水线**

ZhC 的 LLVM 后端包含完整的优化 Pass（死代码消除、常量折叠、循环展开、内联等）。为 C 添加前端后，**C 代码也能享受同等的优化能力**。

```
GCC/Clang:    C → 目标机器码（各自独立的优化）
ZhC (C前端):  C → ZHC IR → LLVM 优化 Pass → 机器码

如果 ZhC 的优化流水线比 GCC/Clang 更强（或有特色优化），
C 前端就有独立的实用价值。
```

**② 统一多语言工具链**

开发者只需要安装 ZhC 即可编译 `.zhc`、`.c`、`.py` 三种源文件，无需为每种语言配置独立的编译环境。

**③ 为 Python 前端铺路**

C 前端实现成本低，可以作为"多前端架构"的技术验证和开发模式演练。C 前端成功后，Python 前端复用相同的设计模式，开发效率更高。

#### 3.1.2 C 前端的局限性

必须承认：**GCC 和 Clang 在 C 编译领域已经非常成熟**。ZhC 的 C 前端在编译速度、兼容性、调试信息方面很难全面超越。

C 前端的真实定位：

| 场景 | 适用性 |
|:---|:---|
| 标准 C 程序 | ⚠️ 建议用 GCC/Clang |
| 与 ZHC 库混合编译 | ✅ **非常适合**（统一的 ABI） |
| 教学/实验编译器 | ✅ **适合**（代码可读性强） |
| 性能关键代码 | ⚠️ 建议用 GCC/Clang |
| 需要完整 C 标准库 | ⚠️ 需要额外实现 |

**结论：C 前端是"锦上添花"，不是核心卖点。**

---

### 3.2 为什么做 Python 前端：战略级投入

#### 3.2.1 Python 的三大痛点

| 痛点 | 描述 | ZhC 能解决的程度 |
|:---|:---|:---|
| **速度慢** | CPython 是解释执行，比 C 慢 10~100x | ✅ **核心解决**：编译到机器码，提速 10~100x |
| **依赖解释器** | 部署需要安装 Python 运行时 | ✅ **核心解决**：编译为独立二进制，零依赖 |
| **无法编译发布** | .py 文件无法编译为单文件可执行文件 | ✅ **核心解决**：编译后是原生二进制 |
| **代码泄露** | .py 文件容易被反编译 | ✅ **部分解决**：机器码反编译难度远高于字节码 |
| **GIL 限制多线程** | 全局解释器锁阻止真正并行 | ✅ **核心解决**：编译后无 GIL |

#### 3.2.2 实际应用场景

```
┌─────────────────────────────────────────────────────────────────┐
│  场景一：性能关键代码加速                                          │
│                                                                 │
│  Python 写业务逻辑 → ZhC 编译热点函数为机器码 → 通过 FFI 调用       │
│                                                                 │
│  例：游戏引擎的物理计算、图像处理的像素操作、实时数据分析           │
│  收益：Python 开发效率 + C 级别执行性能                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  场景二：嵌入式 / 边缘计算部署                                      │
│                                                                 │
│  Python 脚本 → 编译为 ARM/x86 无依赖二进制 → 烧录到 IoT 设备        │
│                                                                 │
│  例：树莓派、工业控制器、嵌入式设备（无法安装 Python 解释器）         │
│  收益：不用为每个设备交叉编译 Python 运行时                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  场景三：代码保护 / 闭源分发                                        │
│                                                                 │
│  Python 源码 → 编译为机器码 → 分发给用户                            │
│                                                                 │
│  例：商业 Python 软件、API 密钥保护、算法保护                       │
│  收益：机器码反编译难度远高于 .pyc 或 PyArmor 加密                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  场景四：跨平台统一编译工具链                                       │
│                                                                 │
│  同一套 ZhC 工具链：                                             │
│    .zhc → 机器码  （中文编程场景）                                  │
│    .c   → 机器码  （性能/系统编程）                                  │
│    .py  → 机器码  （应用逻辑/脚本）                                  │
│                                                                 │
│  收益：开发者掌握一个工具，编译三种语言                              │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.2.3 多前端架构的真实收益

```
一次投入，三种语言共享：

    语义分析引擎      × 1 → C / Chinese C / Python 共用
    IR 生成器         × 1 → C / Chinese C / Python 共用
    IR 优化器         × 1 → C / Chinese C / Python 共用
    LLVM 后端         × 1 → C / Chinese C / Python 共用
    C 运行时库        × 1 → C / Chinese C / Python 共用
    工具链（CLI/调试） × 1 → C / Chinese C / Python 共用

对比独立编译器方案：
    GCC + 中文C编译器 + Python编译器(PyOxide/Cython)
    = 3x 开发成本 + 3x 维护成本 + 不兼容的 ABI

多前端架构：
    ZhC Core + ZHC/C/Python 前端
    = 1x 核心 + 轻量前端 = 极低维护成本 + 统一 ABI
```

#### 3.2.4 与现有 Python 编译方案的对比

| 方案 | 速度提升 | 零依赖 | 单文件 | 代码保护 | 实现难度 |
|:---|:---:|:---:|:---:|:---:|:---:|
| **CPython** | 1x（基准） | ❌ | ❌ | ❌ | — |
| **Cython** | 2~30x | ❌ | ⚠️ | ⚠️ | ⭐⭐ |
| **PyInstaller** | 1x（纯打包） | ❌ | ✅ | ❌ | ⭐ |
| **Nuitka** | 1~10x | ⚠️ | ✅ | ⚠️ | ⭐⭐⭐ |
| **PyOxide** | 5~50x | ✅ | ✅ | ⚠️ | ⭐⭐⭐ |
| **ZhC Python前端**（本文方案） | **10~100x** | **✅** | **✅** | **✅** | ⭐⭐⭐⭐⭐ |

**注**：现有方案的"零依赖"通常是指不需要用户安装 Python，但仍然需要 Python 动态库（.dll/.so）。ZhC 编译的二进制是真正的静态链接、零外部依赖。

---

## 四、执行计划

### 4.1 工作量估算

| 阶段 | 任务 | 优先级 | 预估工时 | 产出物 |
|:---:|:---|:---:|:---:|:---|
| **预研** | pipeline.py 前端路由改造 | 🔴 P0 | 3h | pipeline.py |
| **预研** | CLI `--lang` 参数支持 | 🔴 P0 | 1h | cli.py |
| **C前端** | C Lexer + Keywords | 🟠 P1 | 4h | lexer.py, keywords.py |
| **C前端** | C Parser + AST桥接 | 🟠 P1 | 12h | parser.py, ast_bridge.py |
| **C前端** | C 前端测试 | 🟡 P2 | 4h | tests/test_c_frontend.py |
| **C前端** | C 前端文档 | 🟡 P2 | 2h | docs/C_FRONTEND_DESIGN.md |
| **Py前端** | Python 类型映射 + 内置函数映射 | 🟠 P1 | 8h | type_mapping.py, builtin_mappings.py |
| **Py前端** | Python 类型推导引擎 | 🟠 P1 | 6h | type_inference.py |
| **Py前端** | Python Parser（核心） | 🔴 P0 | 20h | parser.py（Python→ZHC转换） |
| **Py前端** | Python stdlib C 实现 | 🟠 P1 | 16h | zhc_python_stdlib.c |
| **Py前端** | IR 扩展（Python特有指令） | 🟡 P2 | 6h | instructions.py |
| **Py前端** | Python 前端测试 | 🟡 P2 | 8h | tests/test_python_frontend.py |
| **Py前端** | Python 前端文档 | 🟡 P2 | 4h | docs/PYTHON_FRONTEND_DESIGN.md |
| | **合计** | | **~94h（约3~4周）** | |

### 4.2 分阶段执行路线

```
阶段一：C 语言前端（热身阶段）
════════════════════════════════════════
预计工期：约 1 周

  Day 1
    ├─ pipeline.py 前端路由改造
    └─ CLI --lang 参数支持

  Day 2~4
    ├─ C Lexer + Keywords
    └─ C Parser + AST 桥接（核心）

  Day 5
    └─ C 前端测试 + 文档

  里程碑：zhc compile hello.c -o hello 可以成功编译标准 C 程序


阶段二：Python 前端（核心阶段）
════════════════════════════════════════
预计工期：约 2~3 周

  Week 2
    ├─ Python 类型映射 + 内置函数映射
    ├─ Python 类型推导引擎
    └─ Python stdlib C 实现（list/dict/str）

  Week 3
    └─ Python Parser（Python→ZHC AST 转换）

  Week 4
    ├─ IR 扩展（Python 特有指令）
    ├─ Python 前端测试
    └─ Python stdlib 扩展

  里程碑：zhc compile hello.py -o hello 可以成功编译并运行简单 Python 程序


阶段三：完善与优化（持续）
════════════════════════════════════════
  · Python 标准库扩展（按需增加 os, sys, re, json...）
  · Python 性能优化（内联、SIMD 向量化）
  · Python 第三方包支持评估
  · 语言互操作（.zhc 调用 .py，.py 调用 .c）
  · WebAssembly 后端（Python → WASM？）
```

---

## 五、风险分析

### 5.1 风险矩阵

| 风险项 | 级别 | 影响 | 应对策略 |
|:---|:---:|:---:|:---|
| Python 动态类型与静态 IR 冲突 | 🔴 高 | 某些 Python 代码无法编译 | 采用"尽力推导 + 运行时类型检查"兜底；明确标注支持的 Python 子集 |
| Python stdlib 工程量巨大 | 🟠 中高 | 无法在短期内完整支持 | 分阶段实施：先支持核心子集（list/dict/str/print/input），按需扩展 |
| C 前端价值不明显 | 🟡 中 | 投入产出比低 | 将 C 前端定位为"技术验证"和"工具链统一"，不过度投入 |
| Python 第三方包（NumPy等）不支持 | 🟡 中 | 使用场景受限 | 明确标注支持范围为"纯 Python 业务代码"，不建议用于科学计算 |
| 维护成本上升 | 🟠 中高 | 三个前端一致性难以保证 | 严格复用统一 AST 接口；前端只负责解析，语义分析之后全部共用 |
| LLVM 版本升级导致兼容问题 | 🟢 低 | 少量适配工作 | 已有版本管理机制，每次 LLVM 升级做兼容性测试 |

### 5.2 Python 支持范围（诚实界定）

**✅ 完全支持（v1.0）**

```
变量声明与基本类型（int, float, str, bool, list, dict）
函数定义与调用
if/elif/else 条件判断
for/while 循环（支持 range()）
return 语句
print() / input()
基本运算符（+ - * / % == != < > and or not）
字符串操作（+ 拼接，[] 索引，in 判断）
列表操作（append, len, 切片）
注释（# 单行，""" 多行）
```

**⚠️ 需要运行时检查（v1.0）**

```
动态类型变量（尽力推导，运行时类型检查）
动态属性赋值（使用 __dict__ 模拟）
eval() / exec()（仅支持静态可分析的部分）
```

**❌ 暂不支持（v1.0，后续评估）**

```
import / from（需要完整的模块系统）
class 继承（多态需要更复杂的 vtable 实现）
生成器 / yield（协程已有基础设施，可扩展）
装饰器（语法糖，可较容易支持）
with 语句（需上下文管理器协议）
异常类型层次（try/except/raise 已支持）
线程 / asyncio（需要 GIL 模拟或忽略）
正则表达式 re 模块
网络请求 http 模块
NumPy / Pandas / TensorFlow 等 C 扩展依赖
```

---

## 六、结论

### 6.1 一句话总结

> **C 前端是技术练手，为 Python 前端铺路；Python 前端是战略投入，是 ZhC 真正形成差异化护城河的核心。**

### 6.2 推荐执行顺序

```
第一优先：C 前端（快速产出，验证架构）
  → 约 1 周，获得"同时编译 C 和 ZHC"的能力

第二优先：Python 前端核心（最大价值）
  → 约 2~3 周，获得"Python 编译为机器码"的能力

第三优先：Python stdlib 扩展（持续完善）
  → 按需扩展，不断扩大支持的 Python 代码范围
```

### 6.3 最终目标

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│   一套 ZhC 工具链 = 编译三种语言 → 共享同一优化引擎             │
│                                                                │
│   .zhc  →  机器码   （中文编程 / 教学 / 特色语法）              │
│   .c    →  机器码   （系统编程 / 性能关键 / FFI 绑定）          │
│   .py   →  机器码   （应用逻辑 / 快速开发 / 零依赖部署）         │
│                                                                │
│   全部共享：语义分析 × IR 优化 × LLVM 后端 × 运行时库          │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 附录

### A. 相关文件清单

```
新增文件（按阶段）

阶段一（C前端）：
  src/zhc/lang_detector.py          ← 语言自动检测
  src/zhc_c/__init__.py             ← C 前端包入口
  src/zhc_c/tokens.py               ← C Token 定义
  src/zhc_c/lexer.py                ← C 词法分析器
  src/zhc_c/keywords.py             ← C 关键词表
  src/zhc_c/parser.py               ← C 语法分析器
  src/zhc_c/ast_bridge.py           ← C AST → ZHC AST 桥接
  tests/test_c_frontend.py          ← C 前端测试
  docs/C_FRONTEND_DESIGN.md         ← C 前端设计文档

阶段二（Python前端）：
  src/zhc_python/__init__.py         ← Python 前端包入口
  src/zhc_python/tokens.py           ← Python Token 定义
  src/zhc_python/lexer.py            ← Python 词法分析器
  src/zhc_python/parser.py           ← Python → ZHC AST 转换器
  src/zhc_python/type_mapping.py     ← Python → ZHC 类型映射
  src/zhc_python/type_inference.py   ← Python 类型推导
  src/zhc_python/builtin_mappings.py← Python 内置函数映射
  src/zhc_python/transformers.py     ← 高级语法转换器
  src/zhc/lib/zhc_python_stdlib.c    ← Python 内置类型 C 实现
  src/zhc/lib/zhc_python_stdlib.h    ← C 头文件
  tests/test_python_frontend.py      ← Python 前端测试
  docs/PYTHON_FRONTEND_DESIGN.md    ← Python 前端设计文档

修改文件：
  src/zhc/compiler/pipeline.py      ← 增加前端路由
  src/zhc/cli/main.py                ← --lang 参数
  src/zhc/ir/instructions.py        ← 增加 Python 特有指令（可选）
```

### B. 参考资料

| 资源 | 用途 |
|:---|:---|
| `src/zhc/parser/lexer.py` | ZHC Lexer 实现参考 |
| `src/zhc/parser/ast_nodes.py` | ZHC AST 节点定义 |
| `src/zhc/ir/ir_generator.py` | IR 生成器实现参考 |
| `src/zhc/backend/llvm_backend.py` | LLVM 后端实现参考 |
| Python 标准库 `ast` 模块文档 | Python AST 节点类型参考 |
| llvmlite 0.47.0 文档 | LLVM IR 操作参考 |

### C. 版本历史

| 版本 | 日期 | 修改内容 |
|:---:|:---|:---|
| v1.0 | 2026-04-12 | 初始版本：包含 C 和 Python 前端完整方案 |

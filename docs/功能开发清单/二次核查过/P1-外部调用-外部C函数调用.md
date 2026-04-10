# P1 外部调用 - 外部 C 函数调用

## 功能概述

**功能名称**：外部 C 函数调用  
**优先级**：P1  
**功能模块**：外部调用  
**创建日期**：2026-04-09

---

## 1. 需求分析

### 1.1 当前状态

ZhC 编译器目前的外部函数支持：
- 内置函数（`printf`, `scanf` 等）硬编码在编译器中
- 缺少通用的外部函数声明机制
- 无法调用用户自定义的 C 库函数
- 缺少 C 头文件导入支持

**现有相关代码**：
- `src/zhc/backend/llvm_instruction_strategy.py`：`CallStrategy` 处理函数调用
- `src/zhc/backend/compilation_context.py`：编译上下文

### 1.2 目标状态

实现完整的 C 函数外部调用支持：

```zhc
// 声明外部 C 函数
外部 "C" {
    整数型 系统调用(整数型 命令);
    无类型 退出程序(整数型 状态码);
    整数型 获取环境变量(字符指针型 名称, 字符指针型 缓冲, 整数型 大小);
}

// 使用外部函数
整数型 主函数() {
    整数型 结果 = 系统调用(0);
    退出程序(结果);
    返回 0;
}
```

**功能目标**：
1. 支持外部函数声明语法
2. 支持 C ABI 兼容的函数调用
3. 支持动态链接库函数调用
4. 支持系统调用接口
5. 支持回调函数（C 调用 ZhC 函数）

---

## 2. 技术方案

### 2.1 模块架构

```
src/zhc/
├── parser/
│   ├── ast_nodes.py           # 增强：外部函数声明 AST
│   └── parser.py              # 增强：外部块语法解析
├── semantic/
│   └── external_resolver.py   # 新增：外部函数解析器
├── backend/
│   ├── external_linker.py     # 新增：外部链接器
│   ├── c_abi.py               # 新增：C ABI 兼容层
│   └── llvm_backend.py        # 增强：外部函数调用
├── ir/
│   └── instructions.py        # 增强：外部调用指令
└── ffi/
    ├── c_types.py             # 新增：C 类型映射
    └── c_callbacks.py         # 新增：C 回调支持
```

### 2.2 核心组件设计

#### 2.2.1 AST 节点设计

**修改文件**：`src/zhc/parser/ast_nodes.py`

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ExternalBlockNode(ASTNode):
    """
    外部块节点
    
    语法：
        外部 "C" {
            函数声明1;
            函数声明2;
        }
    
    例如：
        外部 "C" {
            整数型 系统调用(整数型 命令);
            无类型 退出程序(整数型 状态码);
        }
    """
    language: str                          # 外部语言（"C"）
    declarations: List['FunctionDeclNode']  # 函数声明列表
    
    def __post_init__(self):
        self.node_type = NodeType.EXTERNAL_BLOCK
    
    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_external_block(self)


@dataclass
class ExternalFunctionDeclNode(ASTNode):
    """
    外部函数声明节点
    
    语法：返回类型 函数名(参数列表)
    
    例如：
        整数型 系统调用(整数型 命令);
    """
    name: str                              # 函数名
    return_type: 'TypeNode'                # 返回类型
    parameters: List['ParameterNode']       # 参数列表
    c_name: Optional[str] = None           # C 函数名（可选，用于名称修饰）
    library: Optional[str] = None          # 所属库（可选）
    
    def __post_init__(self):
        self.node_type = NodeType.EXTERNAL_FUNCTION_DECL
    
    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_external_function_decl(self)


@dataclass
class ExternalCallNode(ASTNode):
    """
    外部函数调用节点
    
    语法：外部函数名(参数列表)
    
    例如：
        系统调用(0)
        退出程序(状态码)
    """
    function_name: str                      # 函数名
    arguments: List['ExpressionNode']       # 参数列表
    external_info: Optional['ExternalFunctionInfo'] = None  # 外部函数信息
    
    def __post_init__(self):
        self.node_type = NodeType.EXTERNAL_CALL
    
    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_external_call(self)
```

#### 2.2.2 语法解析器增强

**修改文件**：`src/zhc/parser/parser.py`

```python
class Parser:
    # ... 现有代码 ...
    
    def parse_external_block(self) -> ExternalBlockNode:
        """
        解析外部块
        
        语法：
            外部 "C" {
                函数声明;
            }
        """
        # 匹配 "外部"
        self.expect(TokenType.EXTERNAL)
        
        # 匹配语言字符串
        language_token = self.expect(TokenType.STRING)
        language = language_token.value.strip('"')
        
        # 目前只支持 "C"
        if language != "C":
            self.error(f"不支持的外部语言: {language}，目前仅支持 C")
        
        # 匹配 "{"
        self.expect(TokenType.LBRACE)
        
        # 解析函数声明列表
        declarations = []
        while self.current_token.type != TokenType.RBRACE:
            decl = self.parse_external_function_decl()
            declarations.append(decl)
        
        # 匹配 "}"
        self.expect(TokenType.RBRACE)
        
        return ExternalBlockNode(
            language=language,
            declarations=declarations,
            line=self.current_token.line,
            column=self.current_token.column
        )
    
    def parse_external_function_decl(self) -> ExternalFunctionDeclNode:
        """
        解析外部函数声明
        
        语法：返回类型 函数名(参数列表);
        """
        # 解析返回类型
        return_type = self.parse_type()
        
        # 解析函数名
        name_token = self.expect(TokenType.IDENTIFIER)
        name = name_token.value
        
        # 匹配 "("
        self.expect(TokenType.LPAREN)
        
        # 解析参数列表
        parameters = self.parse_parameter_list()
        
        # 匹配 ")"
        self.expect(TokenType.RPAREN)
        
        # 匹配 ";"
        self.expect(TokenType.SEMICOLON)
        
        return ExternalFunctionDeclNode(
            name=name,
            return_type=return_type,
            parameters=parameters,
            line=self.current_token.line,
            column=self.current_token.column
        )
```

#### 2.2.3 C 类型映射

**新增文件**：`src/zhc/ffi/c_types.py`

```python
"""
C 类型映射

提供 ZhC 类型与 C 类型的映射关系
"""

from dataclasses import dataclass
from typing import Dict, Optional
import llvmlite.ir as ll

@dataclass
class CTypeInfo:
    """C 类型信息"""
    c_type: str           # C 类型名
    llvm_type: ll.Type    # LLVM 类型
    size: int             # 字节大小
    alignment: int        # 对齐要求


class CTypeMapper:
    """C 类型映射器"""
    
    # ZhC 类型到 C 类型的映射
    ZHC_TO_C_TYPE_MAP: Dict[str, str] = {
        "整数型": "int",
        "短整型": "short",
        "长整型": "long",
        "字符型": "char",
        "浮点型": "float",
        "双精度浮点型": "double",
        "无类型": "void",
        "布尔型": "int",  # C 没有原生 bool，使用 int
        "字符串型": "const char*",
        "字符指针型": "char*",
        "无符号整数型": "unsigned int",
        "无符号短整型": "unsigned short",
        "无符号长整型": "unsigned long",
        "无符号字符型": "unsigned char",
    }
    
    # C 类型到 LLVM 类型的映射
    C_TO_LLVM_TYPE_MAP: Dict[str, ll.Type] = {
        "int": ll.IntType(32),
        "short": ll.IntType(16),
        "long": ll.IntType(64),
        "char": ll.IntType(8),
        "float": ll.FloatType(),
        "double": ll.DoubleType(),
        "void": ll.VoidType(),
        "unsigned int": ll.IntType(32),
        "unsigned short": ll.IntType(16),
        "unsigned long": ll.IntType(64),
        "unsigned char": ll.IntType(8),
    }
    
    @classmethod
    def zhc_to_c(cls, zhc_type: str) -> str:
        """将 ZhC 类型转换为 C 类型"""
        return cls.ZHC_TO_C_TYPE_MAP.get(zhc_type, zhc_type)
    
    @classmethod
    def c_to_llvm(cls, c_type: str) -> ll.Type:
        """将 C 类型转换为 LLVM 类型"""
        # 处理指针类型
        if c_type.endswith('*'):
            base_type = c_type.rstrip('*').strip()
            base_llvm = cls.c_to_llvm(base_type)
            return ll.PointerType(base_llvm)
        
        # 处理 const 修饰符
        c_type = c_type.replace('const', '').strip()
        
        return cls.C_TO_LLVM_TYPE_MAP.get(c_type, ll.IntType(32))
    
    @classmethod
    def zhc_to_llvm(cls, zhc_type: str) -> ll.Type:
        """将 ZhC 类型转换为 LLVM 类型"""
        c_type = cls.zhc_to_c(zhc_type)
        return cls.c_to_llvm(c_type)
    
    @classmethod
    def get_c_type_info(cls, c_type: str) -> CTypeInfo:
        """获取 C 类型信息"""
        llvm_type = cls.c_to_llvm(c_type)
        
        # 计算大小和对齐
        size = cls._get_type_size(llvm_type)
        alignment = cls._get_type_alignment(llvm_type)
        
        return CTypeInfo(
            c_type=c_type,
            llvm_type=llvm_type,
            size=size,
            alignment=alignment
        )
    
    @staticmethod
    def _get_type_size(llvm_type: ll.Type) -> int:
        """获取 LLVM 类型大小"""
        if isinstance(llvm_type, ll.IntType):
            return llvm_type.width // 8
        elif isinstance(llvm_type, ll.FloatType):
            return 4
        elif isinstance(llvm_type, ll.DoubleType):
            return 8
        elif isinstance(llvm_type, ll.PointerType):
            return 8  # 64位指针
        elif isinstance(llvm_type, ll.VoidType):
            return 0
        else:
            return 8  # 默认
    
    @staticmethod
    def _get_type_alignment(llvm_type: ll.Type) -> int:
        """获取 LLVM 类型对齐"""
        size = CTypeMapper._get_type_size(llvm_type)
        # 对齐通常等于大小，但最大为 8
        return min(size, 8) if size > 0 else 1
```

#### 2.2.4 外部函数解析器

**新增文件**：`src/zhc/semantic/external_resolver.py`

```python
"""
外部函数解析器

解析和管理外部函数声明
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import llvmlite.ir as ll

@dataclass
class ExternalFunctionInfo:
    """外部函数信息"""
    name: str                    # ZhC 函数名
    c_name: str                  # C 函数名
    return_type: str             # 返回类型
    param_types: List[str]       # 参数类型列表
    param_names: List[str]       # 参数名列表
    library: Optional[str]       # 所属库
    llvm_type: ll.FunctionType   # LLVM 函数类型


class ExternalFunctionResolver:
    """外部函数解析器"""
    
    def __init__(self):
        self.functions: Dict[str, ExternalFunctionInfo] = {}
        self._libraries: Dict[str, bool] = {}  # 库名 -> 是否已链接
    
    def register_external_function(
        self,
        decl: 'ExternalFunctionDeclNode',
        c_type_mapper: 'CTypeMapper'
    ) -> ExternalFunctionInfo:
        """
        注册外部函数
        
        Args:
            decl: 外部函数声明节点
            c_type_mapper: C 类型映射器
        
        Returns:
            外部函数信息
        """
        # 获取函数名
        name = decl.name
        c_name = decl.c_name or name  # 如果没有指定 C 名称，使用 ZhC 名称
        
        # 获取返回类型
        return_type = decl.return_type.type_name
        
        # 获取参数类型和名称
        param_types = [p.type_node.type_name for p in decl.parameters]
        param_names = [p.name for p in decl.parameters]
        
        # 构建 LLVM 函数类型
        llvm_return = c_type_mapper.zhc_to_llvm(return_type)
        llvm_params = [c_type_mapper.zhc_to_llvm(pt) for pt in param_types]
        llvm_func_type = ll.FunctionType(llvm_return, llvm_params)
        
        # 创建函数信息
        func_info = ExternalFunctionInfo(
            name=name,
            c_name=c_name,
            return_type=return_type,
            param_types=param_types,
            param_names=param_names,
            library=decl.library,
            llvm_type=llvm_func_type
        )
        
        # 注册到字典
        self.functions[name] = func_info
        
        return func_info
    
    def get_function_info(self, name: str) -> Optional[ExternalFunctionInfo]:
        """获取外部函数信息"""
        return self.functions.get(name)
    
    def is_external_function(self, name: str) -> bool:
        """判断是否为外部函数"""
        return name in self.functions
    
    def get_all_libraries(self) -> List[str]:
        """获取所有需要的库"""
        libraries = set()
        for func_info in self.functions.values():
            if func_info.library:
                libraries.add(func_info.library)
        return list(libraries)
```

#### 2.2.5 外部链接器

**新增文件**：`src/zhc/backend/external_linker.py`

```python
"""
外部链接器

处理外部函数的链接和调用
"""

from typing import Dict, List, Optional
import llvmlite.ir as ll

class ExternalLinker:
    """外部链接器"""
    
    def __init__(self, module: ll.Module):
        self.module = module
        self._declared_functions: Dict[str, ll.Function] = {}
    
    def declare_external_function(
        self, 
        func_info: 'ExternalFunctionInfo'
    ) -> ll.Function:
        """
        声明外部函数
        
        LLVM IR：
            declare ReturnType @func_name(ParamTypes)
        """
        # 检查是否已声明
        if func_info.c_name in self._declared_functions:
            return self._declared_functions[func_info.c_name]
        
        # 创建函数声明
        func = self.module.get_or_insert_function(
            func_info.c_name,
            func_info.llvm_type
        )
        
        # 设置外部链接
        func.linkage = 'external'
        
        # 设置调用约定（C 调用约定）
        func.calling_convention = 'ccc'
        
        # 缓存
        self._declared_functions[func_info.c_name] = func
        
        return func
    
    def link_library(self, library_name: str):
        """
        链接外部库
        
        在 LLVM IR 中添加库依赖
        """
        # 添加库依赖元数据
        # 注意：这需要链接器支持
        pass
    
    def generate_call(
        self,
        builder: ll.IRBuilder,
        func_info: 'ExternalFunctionInfo',
        args: List[ll.Value]
    ) -> ll.Value:
        """
        生成外部函数调用
        
        LLVM IR：
            %result = call ReturnType @func_name(ParamTypes args)
        """
        # 获取函数
        func = self._declared_functions.get(func_info.c_name)
        if not func:
            func = self.declare_external_function(func_info)
        
        # 生成调用
        result = builder.call(
            func,
            args,
            name="external_call_result"
        )
        
        return result


class SystemCallInterface:
    """系统调用接口"""
    
    # 常见系统调用号（Linux x86_64）
    SYSCALL_NUMBERS = {
        "read": 0,
        "write": 1,
        "open": 2,
        "close": 3,
        "exit": 60,
    }
    
    def __init__(self, backend):
        self.backend = backend
    
    def generate_syscall(
        self,
        builder: ll.IRBuilder,
        syscall_name: str,
        args: List[ll.Value]
    ) -> ll.Value:
        """
        生成系统调用
        
        LLVM IR：
            %result = call i64 asm "syscall", ... (...)
        """
        import llvmlite.ir as ll
        
        # 获取系统调用号
        syscall_num = self.SYSCALL_NUMBERS.get(syscall_name)
        if syscall_num is None:
            raise ValueError(f"未知的系统调用: {syscall_name}")
        
        # 创建内联汇编
        # 注意：这是 Linux x86_64 的系统调用约定
        asm_type = ll.FunctionType(ll.IntType(64), [ll.IntType(64)] * len(args))
        
        # 内联汇编字符串
        asm_str = "syscall"
        constraints = "={rax},{rax},{rdi},{rsi},{rdx}"[:len(args) * 2 + 3]
        
        # 创建内联汇编调用
        asm_func = ll.InlineAsm.get(
            asm_type,
            asm_str,
            constraints
        )
        
        # 准备参数
        syscall_num_const = ll.Constant(ll.IntType(64), syscall_num)
        all_args = [syscall_num_const] + args
        
        # 生成调用
        result = builder.call(asm_func, all_args)
        
        return result
```

#### 2.2.6 C ABI 兼容层

**新增文件**：`src/zhc/backend/c_abi.py`

```python
"""
C ABI 兼容层

确保 ZhC 函数调用符合 C ABI 规范
"""

from typing import List, Tuple
import llvmlite.ir as ll

class CABILayer:
    """C ABI 兼容层"""
    
    def __init__(self, target_platform: str = "linux"):
        self.target_platform = target_platform
    
    def get_calling_convention(self) -> str:
        """
        获取调用约定
        
        Returns:
            调用约定名称
        """
        if self.target_platform == "windows":
            return "stdcall"  # Windows 使用 stdcall
        else:
            return "ccc"  # Linux/macOS 使用 C 调用约定
    
    def classify_argument(
        self, 
        llvm_type: ll.Type
    ) -> Tuple[str, List[int]]:
        """
        对参数类型进行分类（System V AMD64 ABI）
        
        Args:
            llvm_type: LLVM 类型
        
        Returns:
            (分类, 寄存器列表)
        """
        # 基本类型
        if isinstance(llvm_type, ll.IntType):
            if llvm_type.width <= 64:
                return ("INTEGER", [])
        
        # 浮点类型
        if isinstance(llvm_type, (ll.FloatType, ll.DoubleType)):
            return ("SSE", [])
        
        # 指针类型
        if isinstance(llvm_type, ll.PointerType):
            return ("INTEGER", [])
        
        # 结构体类型（需要更复杂的分类）
        if isinstance(llvm_type, ll.LiteralStructType):
            return self._classify_struct(llvm_type)
        
        # 默认：通过内存传递
        return ("MEMORY", [])
    
    def _classify_struct(
        self, 
        struct_type: ll.LiteralStructType
    ) -> Tuple[str, List[int]]:
        """对结构体类型进行分类"""
        # 简化处理：小结构体通过寄存器传递，大结构体通过内存传递
        size = struct_type.width // 8 if hasattr(struct_type, 'width') else 0
        
        if size <= 16:
            # 小结构体：尝试通过寄存器传递
            return ("INTEGER", [])
        else:
            # 大结构体：通过内存传递
            return ("MEMORY", [])
    
    def prepare_arguments(
        self, 
        args: List[ll.Value],
        builder: ll.IRBuilder
    ) -> List[ll.Value]:
        """
        准备函数调用参数
        
        根据调用约定调整参数传递方式
        
        Args:
            args: 原始参数列表
            builder: IR 构建器
        
        Returns:
            调整后的参数列表
        """
        prepared_args = []
        
        for arg in args:
            classification, _ = self.classify_argument(arg.type)
            
            if classification == "MEMORY":
                # 通过内存传递：分配栈空间
                alloca = builder.alloca(arg.type)
                builder.store(arg, alloca)
                prepared_args.append(alloca)
            else:
                # 通过寄存器传递：直接使用
                prepared_args.append(arg)
        
        return prepared_args
    
    def create_callback_wrapper(
        self,
        zhc_func: ll.Function,
        c_signature: ll.FunctionType,
        module: ll.Module
    ) -> ll.Function:
        """
        创建回调包装器
        
        允许 C 代码调用 ZhC 函数
        
        Args:
            zhc_func: ZhC 函数
            c_signature: C 函数签名
            module: LLVM 模块
        
        Returns:
            包装器函数
        """
        # 创建包装器函数
        wrapper_name = f"{zhc_func.name}_callback_wrapper"
        wrapper = ll.Function(module, c_signature, name=wrapper_name)
        
        # 设置调用约定
        wrapper.calling_convention = self.get_calling_convention()
        
        # 创建基本块
        entry = wrapper.append_basic_block(name="entry")
        builder = ll.IRBuilder(entry)
        
        # 调用 ZhC 函数
        args = list(wrapper.args)
        result = builder.call(zhc_func, args)
        
        # 返回结果
        if c_signature.return_type != ll.VoidType():
            builder.ret(result)
        else:
            builder.ret_void()
        
        return wrapper
```

### 2.3 编译流程集成

```python
class LLVMBackend:
    # ... 现有代码 ...
    
    def __init__(self):
        # ... 现有初始化 ...
        
        # 初始化外部调用组件
        self.external_resolver = ExternalFunctionResolver()
        self.external_linker = ExternalLinker(self.module)
        self.c_abi = CABILayer(self.target_platform)
        self.c_type_mapper = CTypeMapper()
    
    def compile_external_block(self, node: 'ExternalBlockNode'):
        """编译外部块"""
        
        for decl in node.declarations:
            # 注册外部函数
            func_info = self.external_resolver.register_external_function(
                decl,
                self.c_type_mapper
            )
            
            # 声明外部函数
            self.external_linker.declare_external_function(func_info)
    
    def compile_external_call(
        self, 
        node: 'ExternalCallNode',
        builder: ll.IRBuilder
    ) -> ll.Value:
        """编译外部函数调用"""
        
        # 获取函数信息
        func_info = self.external_resolver.get_function_info(node.function_name)
        if not func_info:
            raise ValueError(f"未声明的外部函数: {node.function_name}")
        
        # 编译参数
        args = []
        for arg_node in node.arguments:
            arg_value = self.compile_expression(arg_node, builder)
            args.append(arg_value)
        
        # 准备参数（根据 ABI）
        prepared_args = self.c_abi.prepare_arguments(args, builder)
        
        # 生成调用
        result = self.external_linker.generate_call(
            builder,
            func_info,
            prepared_args
        )
        
        return result
```

---

## 3. 实现步骤

### Step 1: AST 节点设计（预计 1 小时）

1. 在 `ast_nodes.py` 添加外部函数相关节点
2. 在 `NodeType` 枚举添加节点类型
3. 在 `ASTVisitor` 添加访问方法
4. 编写单元测试

### Step 2: 词法分析器增强（预计 0.5 小时）

1. 在 `keywords.py` 添加"外部"关键字
2. 在 `lexer.py` 添加 `TokenType.EXTERNAL`
3. 编写测试

### Step 3: 语法解析器增强（预计 1.5 小时）

1. 在 `parser.py` 添加外部块解析
2. 添加外部函数声明解析
3. 编写测试

### Step 4: C 类型映射实现（预计 1.5 小时）

1. 创建 `ffi/c_types.py`
2. 实现 ZhC 到 C 类型映射
3. 实现 C 到 LLVM 类型映射
4. 编写测试

### Step 5: 外部函数解析器实现（预计 1.5 小时）

1. 创建 `semantic/external_resolver.py`
2. 实现外部函数注册
3. 实现函数信息查询
4. 编写测试

### Step 6: 外部链接器实现（预计 2 小时）

1. 创建 `backend/external_linker.py`
2. 实现外部函数声明
3. 实现外部函数调用生成
4. 编写测试

### Step 7: C ABI 兼容层实现（预计 2 小时）

1. 创建 `backend/c_abi.py`
2. 实现参数分类
3. 实现参数准备
4. 实现回调包装器
5. 编写测试

### Step 8: 后端集成（预计 2 小时）

1. 修改 `llvm_backend.py`
2. 集成外部调用组件
3. 实现外部块编译
4. 实现外部调用编译
5. 编写测试

### Step 9: 端到端测试（预计 1.5 小时）

1. 测试外部函数声明
2. 测试外部函数调用
3. 测试系统调用
4. 测试回调函数

---

## 4. 测试计划

### 4.1 单元测试

```python
# tests/ffi/test_c_types.py

def test_zhc_to_c_type_mapping():
    """测试 ZhC 到 C 类型映射"""
    assert CTypeMapper.zhc_to_c("整数型") == "int"
    assert CTypeMapper.zhc_to_c("浮点型") == "float"
    assert CTypeMapper.zhc_to_c("字符串型") == "const char*"

def test_c_to_llvm_type_mapping():
    """测试 C 到 LLVM 类型映射"""
    assert CTypeMapper.c_to_llvm("int") == ll.IntType(32)
    assert CTypeMapper.c_to_llvm("float") == ll.FloatType()
    assert CTypeMapper.c_to_llvm("char*").is_pointer
```

### 4.2 外部函数解析测试

```python
# tests/semantic/test_external_resolver.py

def test_external_function_registration():
    """测试外部函数注册"""
    resolver = ExternalFunctionResolver()
    
    # 创建测试声明
    decl = ExternalFunctionDeclNode(
        name="系统调用",
        return_type=TypeNode("整数型"),
        parameters=[ParameterNode("命令", TypeNode("整数型"))]
    )
    
    func_info = resolver.register_external_function(decl, CTypeMapper())
    
    assert func_info.name == "系统调用"
    assert func_info.c_name == "系统调用"
    assert func_info.return_type == "整数型"
    assert len(func_info.param_types) == 1
```

### 4.3 集成测试

```zhc
// tests/fixtures/external_call.zhc

外部 "C" {
    整数型 系统调用(整数型 命令);
    无类型 退出程序(整数型 状态码);
    整数型 写入(整数型 文件描述符, 字符指针型 缓冲, 整数型 长度);
}

整数型 主函数() {
    整数型 结果 = 系统调用(0);
    
    字符串型 消息 = "Hello from ZhC!\n";
    写入(1, 消息, 18);
    
    退出程序(结果);
    返回 0;
}
```

### 4.4 LLVM IR 验证

```llvm
; 验证生成的 LLVM IR

; 外部函数声明
declare i32 @系统调用(i32)
declare void @退出程序(i32)
declare i32 @写入(i32, i8*, i32)

define i32 @主函数() {
entry:
    ; 系统调用(0)
    %result = call i32 @系统调用(i32 0)
    
    ; 写入(1, 消息, 18)
    %message = getelementptr [19 x i8], [19 x i8]* @message_str, i32 0, i32 0
    %write_result = call i32 @写入(i32 1, i8* %message, i32 18)
    
    ; 退出程序(结果)
    call void @退出程序(i32 %result)
    
    ret i32 0
}

@message_str = global [19 x i8] c"Hello from ZhC!\0A\00"
```

---

## 5. 验收标准

1. ✅ 支持外部函数声明语法
2. ✅ 支持 C ABI 兼容的函数调用
3. ✅ 支持动态链接库函数调用
4. ✅ 支持系统调用接口
5. ✅ 支持回调函数（C 调用 ZhC 函数）
6. ✅ 生成正确的 LLVM IR
7. ✅ 单元测试覆盖率 ≥ 80%

---

## 6. 风险与依赖

### 6.1 风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 平台 ABI 差异 | 高 | 根据目标平台选择 ABI |
| 函数签名不匹配 | 高 | 严格类型检查 |
| 库依赖管理 | 中 | 支持库路径配置 |

### 6.2 依赖

- 依赖 LLVM 外部函数声明
- 依赖 C 标准库
- 依赖系统调用接口

---

## 7. 后续优化

1. 支持更多外部语言（Python、Rust）
2. 自动生成 C 绑定
3. FFI 安全检查
4. 跨语言异常处理

---

**文档版本**：v1.0  
**最后更新**：2026-04-09  
**负责人**：ZhC 开发团队
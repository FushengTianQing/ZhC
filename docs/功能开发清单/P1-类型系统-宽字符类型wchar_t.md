# P1 类型系统 - 宽字符类型 wchar_t

## 功能概述

**功能名称**：宽字符类型 wchar_t  
**优先级**：P1  
**功能模块**：类型系统  
**创建日期**：2026-04-09

---

## 1. 需求分析

### 1.1 当前状态

ZhC 编译器目前字符类型支持：
- `字符型`：对应 C 的 `char`（1字节）
- UTF-8 字符串处理（`src/zhc/utils/utf8_utils.py`）

**缺少的功能**：
- 宽字符类型 `wchar_t`（2或4字节）
- 宽字符串类型 `wchar_t*`
- 宽字符常量 `L'字'`
- 宽字符串常量 `L"宽字符串"`
- 宽字符输入输出函数

### 1.2 目标状态

实现完整的宽字符类型支持：

```zhc
// 宽字符声明
宽字符型 中文字符 = '中';  // 存储 Unicode 码点

// 宽字符串
宽字符串型 中文文本 = "你好世界";

// 宽字符数组
宽字符型[10] 字符数组;

// 宽字符函数
整数型 主函数() {
    宽字符型 字 = '汉';
    宽字符串型 文本 = "中文编程";
    
    输出宽字符(字);
    输出宽字符串(文本);
    
    返回 0;
}
```

**功能目标**：
1. 支持 `宽字符型` 类型（对应 `wchar_t`）
2. 支持 `宽字符串型` 类型（对应 `wchar_t*`）
3. 支持宽字符常量语法
4. 支持宽字符串常量语法
5. 支持宽字符输入输出函数
6. 正确处理 Unicode 字符

---

## 2. 技术方案

### 2.1 模块架构

```
src/zhc/
├── parser/
│   ├── lexer.py               # 增强：宽字符词法分析
│   ├── ast_nodes.py           # 增强：宽字符 AST 节点
│   └── parser.py              # 增强：宽字符语法解析
├── backend/
│   ├── type_system.py         # 增强：宽字符类型映射
│   └── llvm_backend.py        # 增强：宽字符 LLVM 生成
├── stdlib/
│   └── wchar.py               # 新增：宽字符标准库函数
└── utils/
    └── unicode_utils.py       # 新增：Unicode 处理工具
```

### 2.2 核心组件设计

#### 2.2.1 宽字符类型定义

**修改文件**：`src/zhc/backend/type_system.py`

```python
from typing import Dict, Optional
import llvmlite.ir as ll

class TypeMapper:
    # ... 现有类型映射 ...
    
    # 宽字符类型映射
    WCHAR_TYPE_MAP = {
        "宽字符型": {
            "llvm_type": ll.IntType(32),  # wchar_t 在大多数平台是 32位
            "c_type": "wchar_t",
            "size": 4,  # 字节
            "signed": True,
        },
        "宽字符串型": {
            "llvm_type": ll.PointerType(ll.IntType(32)),  # wchar_t*
            "c_type": "wchar_t*",
            "size": 8,  # 指针大小
        },
    }
    
    def to_llvm_wchar(self) -> ll.IntType:
        """获取宽字符 LLVM 类型"""
        # 根据目标平台选择 wchar_t 大小
        # Windows: 16位 (UTF-16)
        # Linux/macOS: 32位 (UTF-32)
        
        if self.target_platform == "windows":
            return ll.IntType(16)
        else:
            return ll.IntType(32)
    
    def to_llvm_wstring(self) -> ll.PointerType:
        """获取宽字符串 LLVM 类型"""
        wchar_type = self.to_llvm_wchar()
        return ll.PointerType(wchar_type)
```

#### 2.2.2 词法分析器增强

**修改文件**：`src/zhc/parser/lexer.py`

```python
class Lexer:
    # ... 现有代码 ...
    
    def scan_wide_char_literal(self) -> Token:
        """
        扫描宽字符常量
        
        语法：L'字符' 或 宽'字符'
        
        例如：
            L'中'
            宽'汉'
        """
        # 匹配 L 或 宽
        if self.current_char == 'L':
            self.advance()
        elif self.match_keyword("宽"):
            self.consume_keyword("宽")
        
        # 匹配单引号
        self.expect("'")
        
        # 扫描字符内容
        char_content = self.scan_char_content()
        
        # 匹配结束单引号
        self.expect("'")
        
        # 获取 Unicode 码点
        unicode_codepoint = self.get_unicode_codepoint(char_content)
        
        return Token(
            type=TokenType.WIDE_CHAR_LITERAL,
            value=unicode_codepoint,
            literal=char_content,
            line=self.line,
            column=self.column
        )
    
    def scan_wide_string_literal(self) -> Token:
        """
        扫描宽字符串常量
        
        语法：L"字符串" 或 宽"字符串"
        
        例如：
            L"你好世界"
            宽"中文编程"
        """
        # 匹配 L 或 宽
        if self.current_char == 'L':
            self.advance()
        elif self.match_keyword("宽"):
            self.consume_keyword("宽")
        
        # 匹配双引号
        self.expect('"')
        
        # 扫描字符串内容
        string_content = self.scan_string_content()
        
        # 匹配结束双引号
        self.expect('"')
        
        # 转换为宽字符串（UTF-32 编码）
        wide_string = self.convert_to_wide_string(string_content)
        
        return Token(
            type=TokenType.WIDE_STRING_LITERAL,
            value=wide_string,
            literal=string_content,
            line=self.line,
            column=self.column
        )
    
    def get_unicode_codepoint(self, char: str) -> int:
        """获取字符的 Unicode 码点"""
        if len(char) == 1:
            return ord(char)
        elif char.startswith('\\'):
            # 处理转义序列
            return self.parse_escape_sequence(char)
        else:
            # 多字节字符（如中文）
            return ord(char[0])
    
    def convert_to_wide_string(self, string: str) -> List[int]:
        """将字符串转换为宽字符串（Unicode 码点列表）"""
        return [ord(c) for c in string]
```

#### 2.2.3 AST 节点设计

**修改文件**：`src/zhc/parser/ast_nodes.py`

```python
from dataclasses import dataclass
from typing import List

@dataclass
class WideCharLiteralNode(ASTNode):
    """
    宽字符常量节点
    
    语法：L'字符' 或 宽'字符'
    
    例如：
        L'中'  -> Unicode 码点 20013
        宽'汉' -> Unicode 码点 27721
    """
    char_value: str       # 字符内容
    unicode_codepoint: int  # Unicode 码点
    
    def __post_init__(self):
        self.node_type = NodeType.WIDE_CHAR_LITERAL
    
    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_wide_char_literal(self)


@dataclass
class WideStringLiteralNode(ASTNode):
    """
    宽字符串常量节点
    
    语法：L"字符串" 或 宽"字符串"
    
    例如：
        L"你好" -> [20320, 22909]
        宽"中文" -> [20013, 25991]
    """
    string_value: str           # 字符串内容
    unicode_codepoints: List[int]  # Unicode 码点列表
    
    def __post_init__(self):
        self.node_type = NodeType.WIDE_STRING_LITERAL
    
    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_wide_string_literal(self)


@dataclass
class WideCharTypeNode(ASTNode):
    """
    宽字符类型节点
    
    语法：宽字符型
    """
    type_name: str = "宽字符型"
    
    def __post_init__(self):
        self.node_type = NodeType.WIDE_CHAR_TYPE
    
    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_wide_char_type(self)


@dataclass
class WideStringTypeNode(ASTNode):
    """
    宽字符串类型节点
    
    语法：宽字符串型
    """
    type_name: str = "宽字符串型"
    
    def __post_init__(self):
        self.node_type = NodeType.WIDE_STRING_TYPE
    
    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_wide_string_type(self)
```

#### 2.2.4 语法解析器增强

**修改文件**：`src/zhc/parser/parser.py`

```python
class Parser:
    # ... 现有代码 ...
    
    def parse_wide_char_literal(self) -> WideCharLiteralNode:
        """解析宽字符常量"""
        token = self.current_token
        
        if token.type != TokenType.WIDE_CHAR_LITERAL:
            self.error("期望宽字符常量")
        
        self.advance()
        
        return WideCharLiteralNode(
            char_value=token.literal,
            unicode_codepoint=token.value,
            line=token.line,
            column=token.column
        )
    
    def parse_wide_string_literal(self) -> WideStringLiteralNode:
        """解析宽字符串常量"""
        token = self.current_token
        
        if token.type != TokenType.WIDE_STRING_LITERAL:
            self.error("期望宽字符串常量")
        
        self.advance()
        
        return WideStringLiteralNode(
            string_value=token.literal,
            unicode_codepoints=token.value,
            line=token.line,
            column=token.column
        )
    
    def parse_wide_char_type(self) -> WideCharTypeNode:
        """解析宽字符类型"""
        self.expect(TokenType.WIDE_CHAR)
        return WideCharTypeNode()
    
    def parse_wide_string_type(self) -> WideStringTypeNode:
        """解析宽字符串类型"""
        self.expect(TokenType.WIDE_STRING)
        return WideStringTypeNode()
```

#### 2.2.5 LLVM 后端实现

**修改文件**：`src/zhc/backend/llvm_backend.py`

```python
class LLVMBackend:
    # ... 现有代码 ...
    
    def compile_wide_char_literal(
        self, 
        node: WideCharLiteralNode, 
        builder: ll.IRBuilder
    ) -> ll.Value:
        """
        编译宽字符常量
        
        LLVM IR：
            %wchar = i32 20013  ; '中' 的 Unicode 码点
        """
        wchar_type = self.type_mapper.to_llvm_wchar()
        return ll.Constant(wchar_type, node.unicode_codepoint)
    
    def compile_wide_string_literal(
        self, 
        node: WideStringLiteralNode, 
        module: ll.Module
    ) -> ll.Value:
        """
        编译宽字符串常量
        
        LLVM IR：
            @wide_str = global [4 x i32] [i32 20320, i32 22909, i32 0]
        """
        wchar_type = self.type_mapper.to_llvm_wchar()
        
        # 添加 null 终止符
        codepoints = node.unicode_codepoints + [0]
        
        # 创建数组类型
        array_type = ll.ArrayType(len(codepoints), wchar_type)
        
        # 创建常量数组
        constants = [ll.Constant(wchar_type, cp) for cp in codepoints]
        array_constant = ll.Constant(array_type, constants)
        
        # 创建全局变量
        global_var = ll.GlobalVariable(
            module, 
            array_type, 
            name=self.new_global_name("wide_str")
        )
        global_var.global_constant = True
        global_var.initializer = array_constant
        
        # 返回指针
        return builder.bitcast(
            global_var,
            ll.PointerType(wchar_type),
            name="wide_str_ptr"
        )
```

#### 2.2.6 宽字符标准库函数

**新增文件**：`src/zhc/stdlib/wchar.py`

```python
"""
宽字符标准库函数

提供宽字符输入输出、字符串操作等函数
"""

import llvmlite.ir as ll
from typing import List

class WideCharStdLib:
    """宽字符标准库"""
    
    def __init__(self, backend):
        self.backend = backend
        self.module = backend.module
    
    def declare_wchar_functions(self):
        """声明宽字符标准库函数"""
        
        # 输出宽字符
        self.declare_wprintf()
        
        # 输出宽字符串
        self.declare_wputs()
        
        # 宽字符串长度
        self.declare_wcslen()
        
        # 宽字符串复制
        self.declare_wcscpy()
        
        # 宽字符串比较
        self.declare_wcscmp()
    
    def declare_wprintf(self):
        """
        声明 wprintf 函数
        
        C 签名：int wprintf(const wchar_t* format, ...)
        """
        wchar_type = self.backend.type_mapper.to_llvm_wchar()
        wchar_ptr_type = ll.PointerType(wchar_type)
        
        # wprintf(format, ...) -> int
        wprintf_type = ll.FunctionType(
            ll.IntType(32),
            [wchar_ptr_type],
            var_arg=True
        )
        
        self.module.get_or_insert_function("wprintf", wprintf_type)
    
    def declare_wputs(self):
        """
        声明 wputs 函数
        
        C 签名：int wputs(const wchar_t* str)
        """
        wchar_type = self.backend.type_mapper.to_llvm_wchar()
        wchar_ptr_type = ll.PointerType(wchar_type)
        
        wputs_type = ll.FunctionType(
            ll.IntType(32),
            [wchar_ptr_type]
        )
        
        self.module.get_or_insert_function("wputs", wputs_type)
    
    def declare_wcslen(self):
        """
        声明 wcslen 函数
        
        C 签名：size_t wcslen(const wchar_t* str)
        """
        wchar_type = self.backend.type_mapper.to_llvm_wchar()
        wchar_ptr_type = ll.PointerType(wchar_type)
        
        wcslen_type = ll.FunctionType(
            ll.IntType(64),  # size_t
            [wchar_ptr_type]
        )
        
        self.module.get_or_insert_function("wcslen", wcslen_type)
    
    def declare_wcscpy(self):
        """
        声明 wcscpy 函数
        
        C 签名：wchar_t* wcscpy(wchar_t* dest, const wchar_t* src)
        """
        wchar_type = self.backend.type_mapper.to_llvm_wchar()
        wchar_ptr_type = ll.PointerType(wchar_type)
        
        wcscpy_type = ll.FunctionType(
            wchar_ptr_type,
            [wchar_ptr_type, wchar_ptr_type]
        )
        
        self.module.get_or_insert_function("wcscpy", wcscpy_type)
    
    def declare_wcscmp(self):
        """
        声明 wcscmp 函数
        
        C 签名：int wcscmp(const wchar_t* s1, const wchar_t* s2)
        """
        wchar_type = self.backend.type_mapper.to_llvm_wchar()
        wchar_ptr_type = ll.PointerType(wchar_type)
        
        wcscmp_type = ll.FunctionType(
            ll.IntType(32),
            [wchar_ptr_type, wchar_ptr_type]
        )
        
        self.module.get_or_insert_function("wcscmp", wcscmp_type)


# ZhC 内置宽字符函数
class ZhCWideCharFunctions:
    """ZhC 内置宽字符函数"""
    
    @staticmethod
    def 输出宽字符(builder, wchar_value, wprintf_func):
        """
        输出宽字符
        
        ZhC 语法：输出宽字符(字符)
        """
        # 创建宽字符字符串 "%lc"
        format_str = ...  # "%lc" 的宽字符串
        
        builder.call(wprintf_func, [format_str, wchar_value])
    
    @staticmethod
    def 输出宽字符串(builder, wstr_ptr, wprintf_func):
        """
        输出宽字符串
        
        ZhC 语法：输出宽字符串(文本)
        """
        # 创建宽字符串格式 "%ls"
        format_str = ...  # "%ls" 的宽字符串
        
        builder.call(wprintf_func, [format_str, wstr_ptr])
    
    @staticmethod
    def 宽字符串长度(builder, wstr_ptr, wcslen_func):
        """
        获取宽字符串长度
        
        ZhC 语法：宽字符串长度(文本)
        """
        return builder.call(wcslen_func, [wstr_ptr])
```

### 2.3 Unicode 处理工具

**新增文件**：`src/zhc/utils/unicode_utils.py`

```python
"""
Unicode 处理工具

提供 Unicode 字符处理、编码转换等功能
"""

from typing import List, Tuple

class UnicodeUtils:
    """Unicode 处理工具类"""
    
    @staticmethod
    def char_to_codepoint(char: str) -> int:
        """
        将字符转换为 Unicode 码点
        
        Args:
            char: 单个字符
        
        Returns:
            Unicode 码点
        """
        return ord(char)
    
    @staticmethod
    def codepoint_to_char(codepoint: int) -> str:
        """
        将 Unicode 码点转换为字符
        
        Args:
            codepoint: Unicode 码点
        
        Returns:
            字符
        """
        return chr(codepoint)
    
    @staticmethod
    def string_to_codepoints(string: str) -> List[int]:
        """
        将字符串转换为 Unicode 码点列表
        
        Args:
            string: 字符串
        
        Returns:
            Unicode 码点列表
        """
        return [ord(c) for c in string]
    
    @staticmethod
    def codepoints_to_string(codepoints: List[int]) -> str:
        """
        将 Unicode 码点列表转换为字符串
        
        Args:
            codepoints: Unicode 码点列表
        
        Returns:
            字符串
        """
        return ''.join(chr(cp) for cp in codepoints)
    
    @staticmethod
    def is_chinese_char(char: str) -> bool:
        """
        判断是否为中文字符
        
        Args:
            char: 字符
        
        Returns:
            是否为中文
        """
        codepoint = ord(char)
        
        # CJK 统一汉字范围
        return (
            0x4E00 <= codepoint <= 0x9FFF or  # 基本汉字
            0x3400 <= codepoint <= 0x4DBF or  # 扩展A
            0x20000 <= codepoint <= 0x2A6DF or  # 扩展B
            0x2A700 <= codepoint <= 0x2B73F or  # 扩展C
            0x2B740 <= codepoint <= 0x2B81F or  # 扩展D
            0x2B820 <= codepoint <= 0x2CEAF    # 扩展E
        )
    
    @staticmethod
    def get_char_name(codepoint: int) -> str:
        """
        获取 Unicode 字符名称
        
        Args:
            codepoint: Unicode 码点
        
        Returns:
            字符名称
        """
        # 使用 unicodedata 模块
        import unicodedata
        try:
            return unicodedata.name(chr(codepoint))
        except ValueError:
            return f"U+{codepoint:04X}"
    
    @staticmethod
    def get_char_category(codepoint: int) -> str:
        """
        获取 Unicode 字符类别
        
        Args:
            codepoint: Unicode 码点
        
        Returns:
            字符类别（如 'Lo' 表示汉字）
        """
        import unicodedata
        return unicodedata.category(chr(codepoint))
```

---

## 3. 实现步骤

### Step 1: 类型系统增强（预计 1 小时）

1. 在 `type_system.py` 添加宽字符类型映射
2. 实现 `to_llvm_wchar()` 方法
3. 实现 `to_llvm_wstring()` 方法
4. 编写单元测试

### Step 2: 词法分析器增强（预计 1.5 小时）

1. 在 `lexer.py` 添加宽字符扫描
2. 实现 `scan_wide_char_literal()` 方法
3. 实现 `scan_wide_string_literal()` 方法
4. 编写测试

### Step 3: AST 节点设计（预计 1 小时）

1. 在 `ast_nodes.py` 添加宽字符节点
2. 在 `NodeType` 枚举添加节点类型
3. 在 `ASTVisitor` 添加访问方法
4. 编写测试

### Step 4: 语法解析器增强（预计 1 小时）

1. 在 `parser.py` 添加宽字符解析
2. 实现宽字符常量解析
3. 实现宽字符串常量解析
4. 编写测试

### Step 5: LLVM 后端实现（预计 2 小时）

1. 在 `llvm_backend.py` 添加宽字符编译
2. 实现宽字符常量编译
3. 实现宽字符串常量编译
4. 编写测试

### Step 6: Unicode 工具实现（预计 1 小时）

1. 创建 `unicode_utils.py`
2. 实现 Unicode 码点转换
3. 实现中文字符判断
4. 编写测试

### Step 7: 标准库函数实现（预计 2 小时）

1. 创建 `stdlib/wchar.py`
2. 声明宽字符标准库函数
3. 实现 ZhC 内置宽字符函数
4. 编写测试

### Step 8: 端到端测试（预计 1.5 小时）

1. 测试宽字符声明和赋值
2. 测试宽字符串操作
3. 测试宽字符输入输出
4. 测试中文字符处理

---

## 4. 测试计划

### 4.1 单元测试

```python
# tests/utils/test_unicode_utils.py

def test_char_to_codepoint():
    """测试字符到码点转换"""
    assert UnicodeUtils.char_to_codepoint('中') == 20013
    assert UnicodeUtils.char_to_codepoint('A') == 65

def test_string_to_codepoints():
    """测试字符串到码点列表转换"""
    codepoints = UnicodeUtils.string_to_codepoints("你好")
    assert codepoints == [20320, 22909]

def test_is_chinese_char():
    """测试中文字符判断"""
    assert UnicodeUtils.is_chinese_char('中') == True
    assert UnicodeUtils.is_chinese_char('A') == False
```

### 4.2 词法分析测试

```python
# tests/parser/test_wide_char_lexer.py

def test_wide_char_literal_scanning():
    """测试宽字符常量扫描"""
    lexer = Lexer("L'中'")
    token = lexer.scan_wide_char_literal()
    
    assert token.type == TokenType.WIDE_CHAR_LITERAL
    assert token.value == 20013
    assert token.literal == '中'

def test_wide_string_literal_scanning():
    """测试宽字符串常量扫描"""
    lexer = Lexer("L\"你好世界\"")
    token = lexer.scan_wide_string_literal()
    
    assert token.type == TokenType.WIDE_STRING_LITERAL
    assert token.value == [20320, 22909, 19990, 30028]
```

### 4.3 类型映射测试

```python
# tests/backend/test_wchar_type.py

def test_wchar_type_mapping():
    """测试宽字符类型映射"""
    mapper = TypeMapper()
    wchar_type = mapper.to_llvm_wchar()
    
    # Linux/macOS: 32位
    assert wchar_type.width == 32

def test_wstring_type_mapping():
    """测试宽字符串类型映射"""
    mapper = TypeMapper()
    wstr_type = mapper.to_llvm_wstring()
    
    assert wstr_type.is_pointer
    assert wstr_type.pointee.width == 32
```

### 4.4 集成测试

```zhc
// tests/fixtures/wide_char.zhc

整数型 主函数() {
    宽字符型 字 = '中';
    宽字符串型 文本 = "你好世界";
    
    输出宽字符(字);
    输出宽字符串(文本);
    
    自动 长度 = 宽字符串长度(文本);
    输出("字符串长度: %d\n", 长度);
    
    返回 0;
}
```

### 4.5 LLVM IR 验证

```llvm
; 验证生成的 LLVM IR

@wide_str = global [5 x i32] [i32 20320, i32 22909, i32 19990, i32 30028, i32 0]

define i32 @主函数() {
entry:
    %字 = alloca i32
    store i32 20013, i32* %字
    
    %文本 = getelementptr [5 x i32], [5 x i32]* @wide_str, i32 0, i32 0
    
    ; 输出宽字符
    %wchar_loaded = load i32, i32* %字
    call void @输出宽字符(i32 %wchar_loaded)
    
    ; 输出宽字符串
    call void @输出宽字符串(i32* %文本)
    
    ; 宽字符串长度
    %length = call i64 @wcslen(i32* %文本)
    
    ret i32 0
}
```

---

## 5. 验收标准

1. ✅ 支持 `宽字符型` 类型声明
2. ✅ 支持 `宽字符串型` 类型声明
3. ✅ 支持宽字符常量语法 `L'字'`
4. ✅ 支持宽字符串常量语法 `L"文本"`
5. ✅ 正确处理 Unicode 字符
6. ✅ 支持宽字符输入输出函数
7. ✅ 生成正确的 LLVM IR
8. ✅ 单元测试覆盖率 ≥ 80%

---

## 6. 风险与依赖

### 6.1 风险

| 飍险 | 影响 | 缓解措施 |
|------|------|----------|
| 平台 wchar_t 大小差异 | 高 | 根据目标平台选择大小 |
| Unicode 字符范围 | 中 | 支持完整 Unicode 范围 |
| 宽字符编码问题 | 高 | 使用 UTF-32 编码 |

### 6.2 依赖

- 依赖现有类型系统
- 依赖 LLVM 整数类型
- 依赖 C 标准库宽字符函数

---

## 7. 后续优化

1. 宽字符编码转换（UTF-16/UTF-32）
2. 宽字符流输入输出
3. 宽字符正则表达式
4. 宽字符本地化支持

---

**文档版本**：v1.0  
**最后更新**：2026-04-09  
**负责人**：ZhC 开发团队
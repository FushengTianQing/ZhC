# P0-字符编码-UTF-8 字符串处理

## 功能概述

**优先级**: P0  
**功能模块**: 字符编码  
**功能名称**: UTF-8 字符串处理  
**功能描述**: 完整支持 UTF-8 编码，正确处理中文字符  
**预估工时**: 3天  
**依赖项**: 无  
**状态**: 待开发

---

## 1. 需求分析

### 1.1 功能目标

确保 ZhC 编译器完整支持 UTF-8 编码，能够正确处理：
1. UTF-8 编码的源代码文件
2. 字符串字面量中的中文字符
3. 字符字面量中的中文字符（宽字符）
4. 标识符中的中文字符（已支持）

**示例**:
```zhc
// UTF-8 源代码文件
整数型 主函数() {
    字符串型 消息 = "你好，世界！";  // 中文字符串
    字符型 中文字符 = '中';          // 中文字符（宽字符）
    
    打印("%s\n", 消息);
    返回 0;
}
```

### 1.2 UTF-8 编码规范

UTF-8 是一种变长编码：
- 1字节: ASCII 字符 (0x00-0x7F)
- 2字节: 0x80-0x7FF (如部分欧洲字符)
- 3字节: 0x800-0xFFFF (如中文字符)
- 4字节: 0x10000-0x10FFFF (如 emoji)

**中文字符编码范围**:
- 基本汉字: U+4E00 - U+9FFF (3字节编码)
- 扩展A: U+3400 - U+4DBF
- 扩展B-F: 更大范围

### 1.3 边界情况

| 边界情况 | 处理方式 |
|---------|---------|
| 无效 UTF-8 序列 | 报错：无效的 UTF-8 编码 |
| 截断的 UTF-8 序列 | 报错：不完整的 UTF-8 字符 |
| 混合编码文件 | 报错或警告：编码不一致 |
| BOM 标记 | 自动识别并跳过 |
| emoji 字符 | 正常处理（4字节） |

---

## 2. 当前代码分析

### 2.1 相关文件

| 文件路径 | 作用 |
|---------|-----|
| `src/zhc/parser/lexer.py` | 词法分析器，处理字符串字面量 |
| `src/zhc/compiler/` | 编译器入口，读取源文件 |
| `src/zhc/backend/` | 后端代码生成，处理字符串常量 |

### 2.2 当前实现状态

#### lexer.py 中的标识符处理（已支持中文）

```python
def read_identifier(self) -> Token:
    """读取标识符"""
    # ...
    while self.current_char() and (
        self.current_char().isalnum()
        or self.current_char() == "_"
        or "\u4e00" <= self.current_char() <= "\u9fff"  # 已支持中文
    ):
        value += self.advance()
    # ...
```

#### lexer.py 中的字符串处理（存在问题）

```python
def read_string(self) -> Token:
    """读取字符串字面量"""
    # ...
    while self.current_char() and self.current_char() != quote:
        # ...
        else:
            value += self.advance()  # 问题：逐字节读取，可能截断 UTF-8
    # ...
```

**问题**: 
1. `advance()` 方法逐字节读取，可能截断 UTF-8 多字节字符
2. 字符串中的中文字符可能被错误处理
3. 字符字面量 `'中'` 可能被错误解析

---

## 3. 实现方案

### 3.1 设计决策

**核心问题**: 如何正确处理 UTF-8 多字节字符？

**选项 A**: 修改 `advance()` 方法，自动读取完整 UTF-8 字符
**选项 B**: 在字符串读取时，检测并读取完整 UTF-8 序列
**选项 C**: 使用 Python 的内置 UTF-8 支持（源文件已 UTF-8 编码）

**选择**: 选项 C + 增强 B

**理由**:
1. Python 3 默认使用 UTF-8，源文件读取时已正确解码
2. `self.source` 是 Python 字符串，每个字符已经是 Unicode 字符
3. 只需确保字符串读取时不截断字符

### 3.2 修改位置

**文件**: `src/zhc/parser/lexer.py`  
**方法**: `read_string()`, `read_identifier()`, `current_char()`

### 3.3 实现步骤

#### 步骤1：确认 Python 字符串处理

Python 3 中，字符串已经是 Unicode，`self.source[self.pos]` 返回的是单个 Unicode 字符（不是字节）。因此：

```python
# 当前实现
def current_char(self) -> Optional[str]:
    if self.pos >= len(self.source):
        return None
    return self.source[self.pos]  # 返回 Unicode 字符，不是字节
```

**结论**: 当前实现已经正确处理 UTF-8 字符（因为 Python 3 字符串是 Unicode）。

#### 步骤2：验证字符串读取

```python
def read_string(self) -> Token:
    """读取字符串字面量"""
    # ...
    while self.current_char() and self.current_char() != quote:
        if self.current_char() == "\\":
            # 转义处理...
        else:
            value += self.advance()  # 正确：advance() 返回 Unicode 字符
    # ...
```

**结论**: 字符串读取已正确处理 UTF-8。

#### 步骤3：添加 UTF-8 验证

虽然 Python 自动处理 UTF-8，但需要添加验证逻辑，确保：
1. 源文件是有效的 UTF-8
2. 字符串中的字符是有效的 Unicode

```python
def read_string(self) -> Token:
    """读取字符串字面量"""
    start_line = self.line
    start_column = self.column
    quote = self.advance()
    value = ""
    is_char = quote == "'"

    while self.current_char() and self.current_char() != quote:
        if self.current_char() == "\\":
            # 转义处理...
        else:
            char = self.advance()
            # 新增：验证字符有效性
            if not self._is_valid_unicode(char):
                error = invalid_unicode_character(
                    character=char,
                    location=SourceLocation(line=self.line, column=self.column - 1)
                )
                self.errors.append(error)
            value += char
    # ...
```

#### 步骤4：添加辅助方法

```python
def _is_valid_unicode(self, char: str) -> bool:
    """检查字符是否是有效的 Unicode 字符
    
    Args:
        char: 单个字符
        
    Returns:
        是否有效
    """
    # 检查是否是有效的 Unicode 字符
    try:
        char.encode('utf-8')
        return True
    except UnicodeEncodeError:
        return False
```

### 3.4 源文件读取验证

**文件**: `src/zhc/compiler/` 或编译器入口

```python
def read_source_file(file_path: str) -> str:
    """读取源文件，验证 UTF-8 编码
    
    Args:
        file_path: 源文件路径
        
    Returns:
        源代码字符串
        
    Raises:
        CompilerError: 如果文件编码无效
    """
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            # utf-8-sig 自动处理 BOM
            source = f.read()
        return source
    except UnicodeDecodeError as e:
        raise CompilerError(
            error_code="E001",
            message=f"源文件编码错误: {e}",
            location=SourceLocation(file_path=file_path, line=1, column=1)
        )
```

### 3.5 完整修改清单

| 序号 | 文件 | 修改内容 |
|-----|------|---------|
| 1 | `src/zhc/parser/lexer.py` | 添加 `_is_valid_unicode()` 方法 |
| 2 | `src/zhc/parser/lexer.py` | 在 `read_string()` 中添加字符验证 |
| 3 | `src/zhc/compiler/` | 添加源文件 UTF-8 验证 |
| 4 | `src/zhc/errors/` | 添加 `invalid_unicode_character()` 错误 |

---

## 4. 测试用例

### 4.1 正常情况测试

```zhc
// 测试文件: tests/test_utf8_string.zhc

整数型 主函数() {
    // 中文字符串
    字符串型 s1 = "你好，世界！";
    字符串型 s2 = "中文编程语言";
    
    // 混合字符串
    字符串型 s3 = "Hello 你好 World 世界";
    
    // emoji 测试
    字符串型 s4 = "表情符号 😀 🎉 🚀";
    
    打印("%s\n", s1);
    打印("%s\n", s3);
    打印("%s\n", s4);
    
    返回 0;
}
```

### 4.2 字符字面量测试

```zhc
// 测试文件: tests/test_utf8_char.zhc

整数型 主函数() {
    // 中文字符（宽字符）
    字符型 c1 = '中';
    字符型 c2 = '文';
    
    // 注意：普通 char 类型可能无法存储中文字符
    // 需要宽字符类型 wchar_t
    
    返回 0;
}
```

### 4.3 边界情况测试

```zhc
// 测试文件: tests/test_utf8_edge.zhc

整数型 主函数() {
    // 空字符串
    字符串型 s1 = "";
    
    // 单字符
    字符串型 s2 = "中";
    
    // 长字符串
    字符串型 s3 = "这是一段很长的中文文字，用于测试 UTF-8 处理能力。";
    
    // 特殊字符
    字符串型 s4 = "特殊字符：© ® ™ € £ ¥";
    
    返回 0;
}
```

---

## 5. 后端处理

### 5.1 LLVM 后端

LLVM IR 中字符串常量的处理：

```llvm
; 中文字符串 "你好"
@.str = private constant [7: i8] c"\xe4\xbd\xa0\xe5\xa5\xbd\x00"
```

**注意**: LLVM IR 使用 UTF-8 字节序列表示字符串。

### 5.2 C 后端

C 代码中字符串常量的处理：

```c
// 中文字符串 "你好"
const char* str = "你好";  // C 编译器自动处理 UTF-8
```

---

## 6. 实现优先级

### 6.1 开发顺序

1. **第一步**: 验证当前 lexer 的 UTF-8 处理能力
2. **第二步**: 添加源文件 UTF-8 验证
3. **第三步**: 添加字符有效性检查
4. **第四步**: 编写测试用例
5. **第五步**: 测试验证

### 6.2 预估时间

| 步骤 | 预估时间 |
|-----|---------|
| 验证当前实现 | 30分钟 |
| 添加源文件验证 | 1小时 |
| 添加字符检查 | 1小时 |
| 编写测试用例 | 2小时 |
| 测试验证 | 1小时 |
| **总计** | **5.5小时** |

---

## 7. 验收标准

- [ ] UTF-8 源文件正确读取
- [ ] 中文字符串正确解析
- [ ] 混合字符串（中英文）正确处理
- [ ] emoji 字符正确处理
- [ ] 无效 UTF-8 序列报错
- [ ] 所有测试用例通过

---

## 8. 相关文档

- UTF-8 编码规范: RFC 3629
- Unicode 标准: https://unicode.org
- Python 3 Unicode 支持: https://docs.python.org/3/howto/unicode.html

---

**创建日期**: 2026-04-09  
**最后更新**: 2026-04-09
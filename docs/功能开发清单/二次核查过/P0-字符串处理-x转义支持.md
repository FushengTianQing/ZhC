# P0-字符串处理-\x 转义支持

## 功能概述

**优先级**: P0  
**功能模块**: 字符串处理  
**功能名称**: \x 转义支持  
**功能描述**: 支持十六进制转义序列 `\xNN`  
**预估工时**: 1天  
**依赖项**: 无  
**状态**: 待开发

---

## 1. 需求分析

### 1.1 功能目标

在字符串和字符字面量中支持十六进制转义序列 `\xNN`，其中 `NN` 是1-2位十六进制数字。

**示例**:
```zhc
字符串型 s = "\x41\x42\x43";  // 等价于 "ABC"
字符型 c = '\x0A';            // 等价于 '\n' (换行符)
字符串型 hex = "\xFF";        // 255号字符
```

### 1.2 C语言标准参考

根据C标准（ISO/IEC 9899）：
- `\x` 后跟十六进制数字序列
- 十六进制数字：`0-9`, `a-f`, `A-F`
- 数字序列长度不限，但实际值必须在字符范围内
- 对于普通字符：值范围 0-255
- 对于宽字符：值范围取决于 `wchar_t` 大小

### 1.3 边界情况

| 边界情况 | 处理方式 |
|---------|---------|
| `\x` 后无数字 | 报错：缺少十六进制数字 |
| `\x` 后只有1位数字 | 正常解析，如 `\xA` = 10 |
| `\x` 后超过2位数字 | 解析所有有效数字，但警告可能溢出 |
| `\xFF` 在字符串中 | 正常解析为字节 255 |
| `\x00` | 解析为空字符（字符串终止符） |
| 大小写混合 `\xAB` | 正常解析 |

---

## 2. 当前代码分析

### 2.1 相关文件

| 文件路径 | 作用 |
|---------|-----|
| `src/zhc/parser/lexer.py` | 词法分析器，处理字符串字面量 |
| `src/zhc/errors/lexer_error.py` | 词法错误定义 |

### 2.2 当前实现（lexer.py 第378-425行）

```python
def read_string(self) -> Token:
    """读取字符串字面量或字符字面量"""
    # ... 
    while self.current_char() and self.current_char() != quote:
        if self.current_char() == "\\":
            self.advance()  # \
            char = self.current_char()
            if char == "n":
                value += "\n"
            elif char == "t":
                value += "\t"
            elif char == "\\":
                value += "\\"
            elif char == "0":
                value += "\0"
            elif char == quote:
                value += quote
            else:
                value += char  # 当前：直接添加字符，不处理 \x
            self.advance()
        else:
            value += self.advance()
    # ...
```

**问题**: 当前实现不支持 `\x` 十六进制转义，`\x41` 会被解析为字符 `x` 和 `4` 和 `1`。

---

## 3. 实现方案

### 3.1 修改位置

**文件**: `src/zhc/parser/lexer.py`  
**方法**: `read_string()`  
**行号**: 386-402（转义序列处理部分）

### 3.2 实现步骤

#### 步骤1：添加十六进制转义处理逻辑

在 `read_string()` 方法的转义处理部分添加 `\x` 分支：

```python
def read_string(self) -> Token:
    """读取字符串字面量或字符字面量"""
    start_line = self.line
    start_column = self.column
    quote = self.advance()  # ' 或 "
    value = ""
    is_char = quote == "'"

    while self.current_char() and self.current_char() != quote:
        if self.current_char() == "\\":
            self.advance()  # 消费 \
            char = self.current_char()
            
            # 新增：处理 \x 十六进制转义
            if char == "x":
                self.advance()  # 消费 x
                hex_value = self._read_hex_escape()
                if hex_value is not None:
                    value += chr(hex_value)
                else:
                    # 报错：缺少十六进制数字
                    error = invalid_escape_sequence(
                        sequence="\\x",
                        location=SourceLocation(line=self.line, column=self.column - 2)
                    )
                    self.errors.append(error)
                continue
            
            # 原有转义处理
            if char == "n":
                value += "\n"
            elif char == "t":
                value += "\t"
            elif char == "\\":
                value += "\\"
            elif char == "0":
                value += "\0"
            elif char == quote:
                value += quote
            else:
                value += char
            self.advance()
        else:
            value += self.advance()
    # ... 后续代码不变
```

#### 步骤2：添加辅助方法 `_read_hex_escape()`

```python
def _read_hex_escape(self) -> Optional[int]:
    """读取十六进制转义序列
    
    \x 后跟1-2位十六进制数字
    
    Returns:
        十六进制值，如果无效则返回 None
    """
    hex_digits = ""
    
    # 读取最多2位十六进制数字
    for _ in range(2):
        char = self.current_char()
        if char and char.lower() in "0123456789abcdef":
            hex_digits += char
            self.advance()
        else:
            break
    
    if not hex_digits:
        return None  # 缺少十六进制数字
    
    try:
        value = int(hex_digits, 16)
        # 检查是否在有效范围内（0-255 对于普通字符）
        if value > 255:
            # 警告：值可能溢出，但仍接受
            pass
        return value
    except ValueError:
        return None
```

#### 步骤3：添加错误类型

**文件**: `src/zhc/errors/lexer_error.py`

```python
def invalid_escape_sequence(
    sequence: str,
    location: SourceLocation,
    suggestion: str = "使用有效的转义序列，如 \\n, \\t, \\xNN"
) -> LexerError:
    """无效的转义序列错误"""
    return LexerError(
        error_code="E002",
        message=f"无效的转义序列 '{sequence}'",
        location=location,
        character=sequence,
        suggestion=suggestion,
    )
```

### 3.3 完整修改清单

| 序号 | 文件 | 修改内容 |
|-----|------|---------|
| 1 | `src/zhc/parser/lexer.py` | 在 `read_string()` 中添加 `\x` 处理分支 |
| 2 | `src/zhc/parser/lexer.py` | 添加 `_read_hex_escape()` 辅助方法 |
| 3 | `src/zhc/errors/lexer_error.py` | 添加 `invalid_escape_sequence()` 错误函数 |

---

## 4. 测试用例

### 4.1 正常情况测试

```zhc
// 测试文件: tests/test_x_escape.zhc

整数型 主函数() {
    // 基本测试
    字符串型 s1 = "\x41";       // 应解析为 "A"
    字符串型 s2 = "\x41\x42";   // 应解析为 "AB"
    字符串型 s3 = "\xAB";       // 应解析为字节 171
    
    // 单字符测试
    字符型 c1 = '\x0A';         // 应解析为换行符
    字符型 c2 = '\xFF';         // 应解析为字节 255
    
    // 混合测试
    字符串型 s4 = "Hello\x20World";  // 应解析为 "Hello World"
    
    打印("%s\n", s1);
    打印("%s\n", s2);
    返回 0;
}
```

### 4.2 边界情况测试

```zhc
// 测试文件: tests/test_x_escape_edge.zhc

整数型 主函数() {
    // 单位十六进制
    字符串型 s1 = "\xA";    // 应解析为字节 10
    
    // 大小写混合
    字符串型 s2 = "\xaB";   // 应解析为字节 171
    
    // 空字符
    字符串型 s3 = "\x00";   // 应解析为空字符
    
    返回 0;
}
```

### 4.3 错误情况测试

```zhc
// 测试文件: tests/test_x_escape_error.zhc

整数型 主函数() {
    // 错误：\x 后无数字
    字符串型 s1 = "\x";     // 应报错
    
    返回 0;
}
```

**预期错误输出**:
```
error[E002]: 无效的转义序列 '\x'
  --> tests/test_x_escape_error.zhc:4:20
   |
4 |     字符串型 s1 = "\x";     // 应报错
   |                    ^^ 无效的转义序列
   |
   = 建议: 使用有效的转义序列，如 \n, \t, \xNN
```

---

## 5. 实现优先级

### 5.1 开发顺序

1. **第一步**: 添加 `_read_hex_escape()` 辅助方法
2. **第二步**: 在 `read_string()` 中添加 `\x` 处理分支
3. **第三步**: 添加错误类型
4. **第四步**: 编写测试用例
5. **第五步**: 运行测试验证

### 5.2 预估时间

| 步骤 | 预估时间 |
|-----|---------|
| 添加辅助方法 | 15分钟 |
| 修改转义处理 | 20分钟 |
| 添加错误类型 | 10分钟 |
| 编写测试用例 | 20分钟 |
| 测试验证 | 15分钟 |
| **总计** | **80分钟** |

---

## 6. 验收标准

- [ ] `\xNN` 格式正确解析为对应字符
- [ ] `\x` 后无数字时报错
- [ ] 单位十六进制 `\xN` 正常工作
- [ ] 大小写混合 `\xAB` 正常工作
- [ ] 所有测试用例通过
- [ ] 无回归问题（原有转义序列仍正常工作）

---

## 7. 相关文档

- C语言标准 ISO/IEC 9899 - 6.4.4.4 字符常量
- 现有代码: `src/zhc/parser/lexer.py`
- 错误处理: `src/zhc/errors/lexer_error.py`

---

**创建日期**: 2026-04-09  
**最后更新**: 2026-04-09
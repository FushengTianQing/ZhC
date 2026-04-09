# P0-字符串处理-ANSI 转义序列

## 功能概述

**优先级**: P0  
**功能模块**: 字符串处理  
**功能名称**: ANSI 转义序列  
**功能描述**: 支持终端 ANSI 控制序列，实现彩色输出  
**预估工时**: 1天  
**依赖项**: 序号1 (\x 转义支持)  
**状态**: 待开发

---

## 1. 需求分析

### 1.1 功能目标

在字符串字面量中支持 ANSI 转义序列（Terminal Escape Sequences），使 ZhC 程序能够在终端输出彩色文字、移动光标、清屏等。

**示例**:
```zhc
字符串型 red_text = "\x1b[31m红色文字\x1b[0m";
字符串型 green_text = "\x1b[32m绿色文字\x1b[0m";
字符串型 bold_text = "\x1b[1m粗体文字\x1b[0m";
```

### 1.2 ANSI 转义序列标准

ANSI 转义序列以 `\x1b[` (十六进制) 或 `\033[` (八进制) 开头，后跟控制参数和终止字符。

#### 常见格式

```
\x1b[参数m      - SGR (Select Graphic Rendition) 设置文本属性
\x1b[行;列H     - 光标位置
\x1b[2J         - 清屏
\x1b[K          - 清除行
\x1b[?25l       - 隐藏光标
\x1b[?25h       - 显示光标
```

#### SGR 参数（最常用）

| 参数 | 效果 |
|-----|------|
| 0 | 重置/正常 |
| 1 | 粗体 |
| 2 | 暗淡 |
| 4 | 下划线 |
| 5 | 闪烁 |
| 7 | 反色 |
| 30-37 | 前景色（黑红绿黄蓝紫青白） |
| 40-47 | 背景色 |
| 90-97 | 亮前景色 |
| 100-107 | 亮背景色 |

### 1.3 颜色代码

```
前景色（30-37）:
  30 = 黑, 31 = 红, 32 = 绿, 33 = 黄
  34 = 蓝, 35 = 紫, 36 = 青, 37 = 白

前景色（90-97）:
  90 = 黑, 91 = 红, 92 = 绿, 93 = 黄
  94 = 蓝, 95 = 紫, 96 = 青, 97 = 白
```

---

## 2. 当前代码分析

### 2.1 相关文件

| 文件路径 | 作用 |
|---------|-----|
| `src/zhc/parser/lexer.py` | 词法分析器，处理字符串字面量 |
| `src/zhc/backend/` | 后端代码生成（可能需要处理 ANSI 序列） |

### 2.2 当前实现限制

当前 lexer 的 `read_string()` 方法处理转义序列时：
- 支持 `\n`, `\t`, `\\`, `\0`
- 不支持 ANSI 转义序列
- `\x1b[31m` 会被错误解析

---

## 3. 实现方案

### 3.1 设计决策

**问题**: ANSI 转义序列如何处理？

**选项 A**: 在词法分析阶段直接解析，将 `\x1b[` 转换为实际的 ESC 字符
**选项 B**: 保持原始形式，在后端或运行时处理

**选择**: 选项 A

**理由**:
1. ANSI 转义序列本质上是 `\x1b` + `[` + 参数 + 终止符
2. 一旦 lexer 识别 `\x1b[`，后面的内容直到 `m`（或其他终止符）都是序列的一部分
3. 直接转换更简单，代码生成时无需特殊处理

### 3.2 修改位置

**文件**: `src/zhc/parser/lexer.py`  
**方法**: `read_string()` 和新增辅助方法

### 3.3 实现步骤

#### 步骤1：添加 ANSI 转义序列识别

在 `read_string()` 方法中，检测 `\x1b[` 模式并调用专用处理函数：

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
            
            # 优先级1: \x 十六进制（已实现）
            if char == "x":
                self.advance()  # 消费 x
                hex_value = self._read_hex_escape()
                if hex_value is not None:
                    value += chr(hex_value)
                else:
                    error = invalid_escape_sequence(...)
                    self.errors.append(error)
                continue
            
            # 新增：优先级2: ANSI 转义序列 \x1b[
            if char == "x" and self._is_ansi_sequence_start():
                ansi_seq = self._read_ansi_sequence()
                if ansi_seq:
                    value += ansi_seq
                continue
            
            # 原有转义处理...
            # ...
        else:
            value += self.advance()
    # ...
```

#### 步骤2：添加 ANSI 序列处理辅助方法

```python
def _is_ansi_sequence_start(self) -> bool:
    """检查 \x 是否是 ANSI 转义序列的开始
    
    ANSI 序列格式: \x1b[... 或 \x1b[...]
    """
    # 需要回溯检查前面的 x 是否与 1b 组成 \x1b
    # 由于我们已经消费了 x，需要检查前面的字符
    # 更简单的方法是：在调用前检查 peek 是否为 '1' 后跟 'b'
    pos = self.pos
    if self.pos < len(self.source) - 2:
        return (self.source[self.pos] == '1' and 
                self.source[self.pos + 1] == 'b')
    return False

def _read_ansi_sequence(self) -> str:
    """读取完整的 ANSI 转义序列
    
    读取格式: \x1b[参数m
    其中终止符可以是: m, H, J, K, f, A, B, C, D, E, G, n, s, u
    
    Returns:
        完整的 ANSI 转义序列字符串
    """
    result = "\x1b"
    
    # 消费 1b
    self.advance()  # 1
    self.advance()  # b
    
    # 消费 [
    if self.current_char() == '[':
        result += self.advance()
    else:
        return result  # 不完整的序列
    
    # 读取参数和终止符
    # ANSI 序列终止符: m, H, J, K, f, A, B, C, D, E, G, n, s, u
    terminators = {'m', 'H', 'J', 'K', 'f', 'A', 'B', 'C', 'D', 'E', 'G', 'n', 's', 'u'}
    
    while self.current_char():
        char = self.current_char()
        
        # 检查是否为终止符
        if char in terminators:
            result += self.advance()
            break
        
        # 有效字符: 数字、分号
        if char.isdigit() or char == ';':
            result += self.advance()
        else:
            # 无效字符，停止解析
            break
    
    return result
```

### 3.4 完整修改清单

| 序号 | 文件 | 修改内容 |
|-----|------|---------|
| 1 | `src/zhc/parser/lexer.py` | 修改 `read_string()` 添加 ANSI 检测 |
| 2 | `src/zhc/parser/lexer.py` | 添加 `_is_ansi_sequence_start()` |
| 3 | `src/zhc/parser/lexer.py` | 添加 `_read_ansi_sequence()` |

---

## 4. 测试用例

### 4.1 正常情况测试

```zhc
// 测试文件: tests/test_ansi_escape.zhc

整数型 主函数() {
    // 颜色测试
    字符串型 red = "\x1b[31m红色\x1b[0m";
    字符串型 green = "\x1b[32m绿色\x1b[0m";
    字符串型 blue = "\x1b[34m蓝色\x1b[0m";
    
    // 样式测试
    字符串型 bold = "\x1b[1m粗体\x1b[0m";
    字符串型 underline = "\x1b[4m下划线\x1b[0m";
    字符串型 blink = "\x1b[5m闪烁\x1b[0m";
    
    // 组合测试
    字符串型 combo = "\x1b[1;31;47m粗体红色白底\x1b[0m";
    
    // 亮色测试
    字符串型 bright_red = "\x1b[91m亮红色\x1b[0m";
    
    打印("%s\n", red);
    打印("%s\n", green);
    打印("%s\n", combo);
    
    返回 0;
}
```

### 4.2 光标控制测试

```zhc
// 测试文件: tests/test_ansi_cursor.zhc

整数型 主函数() {
    // 光标位置: 行5, 列10
    字符串型 cursor_pos = "\x1b[5;10H";
    
    // 清屏
    字符串型 clear_screen = "\x1b[2J";
    
    // 清除行
    字符串型 clear_line = "\x1b[K";
    
    // 隐藏/显示光标
    字符串型 hide_cursor = "\x1b[?25l";
    字符串型 show_cursor = "\x1b[?25h";
    
    打印("%s正在清除屏幕...\n", clear_screen);
    打印("%s光标移动到 (5,10)\n", cursor_pos);
    
    返回 0;
}
```

### 4.3 预期输出

运行上述测试应显示彩色终端输出（取决于终端支持）。

---

## 5. 实现优先级

### 5.1 依赖关系

本功能依赖 `\x` 转义支持（序号1），因为 ANSI 转义序列的起始 `\x1b` 就是 `\x` 的一种应用。

### 5.2 开发顺序

1. **第一步**: 确认 `\x` 转义已实现
2. **第二步**: 添加 ANSI 序列识别逻辑
3. **第三步**: 添加辅助方法
4. **第四步**: 编写测试用例
5. **第五步**: 运行测试验证

### 5.3 预估时间

| 步骤 | 预估时间 |
|-----|---------|
| 确认依赖完成 | 5分钟 |
| 添加 ANSI 检测逻辑 | 15分钟 |
| 添加辅助方法 | 20分钟 |
| 编写测试用例 | 30分钟 |
| 测试验证 | 20分钟 |
| **总计** | **90分钟** |

---

## 6. 验收标准

- [ ] `\x1b[31m` 正确解析为 ANSI 颜色序列
- [ ] 多种颜色（前景色、背景色、亮色）正常工作
- [ ] 样式（粗体、下划线、闪烁）正常工作
- [ ] 光标控制序列正常工作
- [ ] 所有测试用例通过
- [ ] 与 `\x` 转义无冲突

---

## 7. 高级功能（可选）

### 7.1 ZhC 语法糖

```zhc
// 可选：添加 ZhC 专用的颜色语法
字符串型 red = #[红色] "红色文字" #[];    // 语法糖
字符串型 bold_red = #[红色;加粗] "文字" #[];
```

### 7.2 运行时检测

```zhc
// 检测终端是否支持颜色
布尔型 支持颜色 = 终端支持颜色();
如果 (支持颜色) {
    打印("%s红色文字%s\n", 红色开始(), 颜色重置());
}
```

---

## 8. 相关文档

- ANSI escape code: https://en.wikipedia.org/wiki/ANSI_escape_code
- ECMA-48 标准
- 现有代码: `src/zhc/parser/lexer.py`

---

**创建日期**: 2026-04-09  
**最后更新**: 2026-04-09
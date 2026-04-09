# P0-预处理器-#define 宏定义

## 功能概述

**优先级**: P0  
**功能模块**: 预处理器  
**功能名称**: #define 宏定义  
**功能描述**: 支持简单的宏定义和宏展开  
**预估工时**: 3天  
**依赖项**: 无  
**状态**: 待开发

---

## 1. 需求分析

### 1.1 功能目标

实现 C 预处理器风格的宏定义功能：

1. **简单宏定义**: `#define 名称 替换文本`
2. **带参数宏**: `#define 名称(参数) 替换文本`
3. **宏取消**: `#undef 名称`

**示例**:
```zhc
// 简单宏定义
#define MAX_SIZE 100
#define VERSION "1.0.0"

// 带参数宏
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define SQUARE(x) ((x) * (x))

// 使用宏
整数型 数组[MAX_SIZE];
打印("版本：%s\n", VERSION);
整数型 最大值 = MAX(10, 20);
```

### 1.2 宏定义规范

根据 C 标准（ISO/IEC 9899）：

| 特性 | 说明 |
|-----|------|
| 宏名 | 由字母、数字、下划线组成，首字符不能是数字 |
| 替换文本 | 可以是任意文本，包括表达式、语句片段 |
| 参数宏 | 参数列表用逗号分隔，替换时参数会被展开 |
| 字符串化 | `#参数` 将参数转为字符串 |
| 连接 | `参数##参数` 连接两个参数 |
| 条件宏 | `#ifdef`, `#ifndef`, `#if`, `#else`, `#endif` |

### 1.3 边界情况

| 边界情况 | 处理方式 |
|---------|---------|
| 宏重定义 | 报错或警告（取决于严格程度） |
| 宏未定义 | 使用时报错 |
| 递归宏 | 报错或停止展开 |
| 宏参数缺失 | 报错 |
| 宏参数过多 | 报错或忽略多余参数 |
| 空宏 | `#define EMPTY` 有效，替换为空 |

---

## 2. 当前代码分析

### 2.1 相关文件

| 文件路径 | 作用 |
|---------|-----|
| `src/zhc/parser/lexer.py` | 词法分析器 |
| `src/zhc/compiler/pipeline.py` | 编译流水线 |
| `src/zhc/parser/` | 解析器模块 |

### 2.2 当前实现状态

**现状**: ZhC 目前没有预处理器实现。

**编译流程**:
```
源代码 → Lexer → Parser → AST → 后端 → 目标代码
```

**需要添加**:
```
源代码 → 预处理器 → Lexer → Parser → AST → 后端 → 目标代码
```

---

## 3. 实现方案

### 3.1 设计决策

**问题**: 预处理器应该放在哪里？

**选项 A**: 在 lexer 之前，作为独立的预处理阶段
**选项 B**: 在 lexer 中处理，识别 `#` 开头的行
**选项 C**: 在 parser 中处理，作为特殊的语法节点

**选择**: 选项 A

**理由**:
1. 与 C 语言预处理器行为一致
2. 预处理是文本级别的操作，不涉及语法
3. 可以独立测试和调试
4. 便于后续添加更多预处理指令

### 3.2 模块设计

#### 文件结构

```
src/zhc/preprocessor/
├── __init__.py
├── preprocessor.py      # 主预处理器类
├── macro.py             # 宏定义和展开
├── directive.py         # 预处理指令解析
├── condition.py         # 条件编译处理
├── include.py           # #include 处理
└── errors.py            # 预处理器错误
```

### 3.3 实现步骤

#### 步骤1：创建预处理器模块

```python
# src/zhc/preprocessor/preprocessor.py

"""
预处理器 - Preprocessor

处理预处理指令：
- #define 宏定义
- #undef 宏取消
- #ifdef/#ifndef 条件编译
- #include 头文件包含
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Macro:
    """宏定义"""
    name: str
    params: Optional[List[str]]  # 参数列表（None 表示无参数宏）
    body: str                     # 替换文本
    is_function: bool             # 是否是函数宏
    
class Preprocessor:
    """预处理器"""
    
    def __init__(self, source: str, file_path: Optional[str] = None):
        """初始化预处理器
        
        Args:
            source: 源代码字符串
            file_path: 源文件路径（用于 #include）
        """
        self.source = source
        self.file_path = file_path
        self.macros: Dict[str, Macro] = {}
        self.include_paths: List[str] = []
        self.output_lines: List[str] = []
        self.errors: List[str] = []
        
    def preprocess(self) -> str:
        """执行预处理
        
        Returns:
            预处理后的源代码
        """
        lines = self.source.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # 检查是否是预处理指令
            if stripped.startswith('#'):
                self._process_directive(stripped, line_num)
            else:
                # 展开宏
                expanded = self._expand_macros(line)
                self.output_lines.append(expanded)
        
        return '\n'.join(self.output_lines)
    
    def _process_directive(self, line: str, line_num: int):
        """处理预处理指令"""
        # 移除 # 前缀
        directive = line[1:].strip()
        
        # 解析指令类型
        if directive.startswith('define'):
            self._process_define(directive, line_num)
        elif directive.startswith('undef'):
            self._process_undef(directive, line_num)
        elif directive.startswith('ifdef'):
            self._process_ifdef(directive, line_num)
        elif directive.startswith('ifndef'):
            self._process_ifndef(directive, line_num)
        elif directive.startswith('include'):
            self._process_include(directive, line_num)
        else:
            self.errors.append(f"未知的预处理指令：{line} (行 {line_num})")
    
    def _process_define(self, directive: str, line_num: int):
        """处理 #define 指令"""
        # 格式：define NAME value 或 define NAME(params) value
        parts = directive[6:].strip()  # 移除 'define'
        
        if not parts:
            self.errors.append(f"#define 缺少宏名 (行 {line_num})")
            return
        
        # 解析宏名和参数
        name_end = parts.find('(')
        if name_end == -1:
            # 无参数宏
            name_end = parts.find(' ')
            if name_end == -1:
                name_end = len(parts)
            
            name = parts[:name_end].strip()
            body = parts[name_end:].strip() if name_end < len(parts) else ""
            
            macro = Macro(name=name, params=None, body=body, is_function=False)
        else:
            # 有参数宏
            name = parts[:name_end].strip()
            
            # 解析参数
            param_end = parts.find(')', name_end)
            if param_end == -1:
                self.errors.append(f"#define 参数列表未闭合 (行 {line_num})")
                return
            
            param_str = parts[name_end+1:param_end]
            params = [p.strip() for p in param_str.split(',') if p.strip()]
            
            body = parts[param_end+1:].strip()
            
            macro = Macro(name=name, params=params, body=body, is_function=True)
        
        # 检查重定义
        if name in self.macros:
            self.errors.append(f"宏 '{name}' 重定义 (行 {line_num})")
        
        self.macros[name] = macro
    
    def _process_undef(self, directive: str, line_num: int):
        """处理 #undef 指令"""
        name = directive[5:].strip()  # 移除 'undef'
        
        if not name:
            self.errors.append(f"#undef 缺少宏名 (行 {line_num})")
            return
        
        if name in self.macros:
            del self.macros[name]
        else:
            # 未定义的宏，可以忽略或警告
            pass
    
    def _expand_macros(self, line: str) -> str:
        """展开行中的宏"""
        result = line
        
        # 按宏名长度排序（最长优先）
        sorted_macros = sorted(self.macros.keys(), key=len, reverse=True)
        
        for name in sorted_macros:
            macro = self.macros[name]
            
            if macro.is_function:
                # 函数宏展开
                result = self._expand_function_macro(result, macro)
            else:
                # 简单宏展开
                result = result.replace(name, macro.body)
        
        return result
    
    def _expand_function_macro(self, text: str, macro: Macro) -> str:
        """展开函数宏"""
        import re
        
        # 匹配宏调用：NAME(args)
        pattern = r'\b' + macro.name + r'\s*\(([^)]*)\)'
        
        def replace(match):
            args_str = match.group(1)
            args = [a.strip() for a in args_str.split(',') if a.strip()]
            
            # 检查参数数量
            if len(args) != len(macro.params):
                self.errors.append(f"宏 '{macro.name}' 参数数量不匹配")
                return match.group(0)  # 保持原样
            
            # 替换参数
            body = macro.body
            for param, arg in zip(macro.params, args):
                body = body.replace(param, arg)
            
            return body
        
        return re.sub(pattern, replace, text)
```

#### 步骤2：集成到编译流水线

```python
# src/zhc/compiler/pipeline.py

from ..preprocessor.preprocessor import Preprocessor

class CompilationPipeline:
    """集成编译流水线"""
    
    def compile(self, source: str, file_path: str) -> str:
        """编译源代码
        
        Args:
            source: 源代码字符串
            file_path: 源文件路径
            
        Returns:
            目标代码
        """
        # 新增：预处理阶段
        preprocessor = Preprocessor(source, file_path)
        preprocessed = preprocessor.preprocess()
        
        if preprocessor.errors:
            for error in preprocessor.errors:
                self.error_handler.report_error(error)
            return None
        
        # 词法分析
        lexer = Lexer(preprocessed)
        tokens = lexer.tokenize()
        
        # ... 后续阶段 ...
```

### 3.4 完整修改清单

| 序号 | 文件 | 修改内容 |
|-----|------|---------|
| 1 | `src/zhc/preprocessor/__init__.py` | 创建模块 |
| 2 | `src/zhc/preprocessor/preprocessor.py` | 主预处理器类 |
| 3 | `src/zhc/preprocessor/macro.py` | 宏定义和展开 |
| 4 | `src/zhc/preprocessor/directive.py` | 指令解析 |
| 5 | `src/zhc/preprocessor/errors.py` | 预处理器错误 |
| 6 | `src/zhc/compiler/pipeline.py` | 集成预处理阶段 |

---

## 4. 测试用例

### 4.1 简单宏测试

```zhc
// 测试文件: tests/test_define_simple.zhc

#define MAX_SIZE 100
#define VERSION "1.0.0"
#define DEBUG

整数型 主函数() {
    整数型 数组[MAX_SIZE];
    打印("版本：%s\n", VERSION);
    
    #ifdef DEBUG
    打印("调试模式\n");
    #endif
    
    返回 0;
}
```

**预期预处理结果**:
```c
整数型 主函数() {
    整数型 数组[100];
    打印("版本：%s\n", "1.0.0");
    
    打印("调试模式\n");
    
    返回 0;
}
```

### 4.2 函数宏测试

```zhc
// 测试文件: tests/test_define_function.zhc

#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define SQUARE(x) ((x) * (x))

整数型 主函数() {
    整数型 x = 10;
    整数型 y = 20;
    
    整数型 最大值 = MAX(x, y);
    整数型 最小值 = MIN(x, y);
    整数型 平方 = SQUARE(x);
    
    打印("最大：%d，最小：%d，平方：%d\n", 最大值, 最小值, 平方);
    
    返回 0;
}
```

**预期预处理结果**:
```c
整数型 主函数() {
    整数型 x = 10;
    整数型 y = 20;
    
    整数型 最大值 = ((x) > (y) ? (x) : (y));
    整数型 最小值 = ((x) < (y) ? (x) : (y));
    整数型 平方 = ((x) * (x));
    
    打印("最大：%d，最小：%d，平方：%d\n", 最大值, 最小值, 平方);
    
    返回 0;
}
```

### 4.3 错误情况测试

```zhc
// 测试文件: tests/test_define_error.zhc

#define MAX(a, b) ((a) > (b) ? (a) : (b))

整数型 主函数() {
    // 错误：参数数量不匹配
    整数型 x = MAX(10);  // 应报错
    
    返回 0;
}
```

---

## 5. 实现优先级

### 5.1 开发顺序

1. **第一步**: 创建预处理器模块结构
2. **第二步**: 实现 `#define` 指令解析
3. **第三步**: 实现宏展开逻辑
4. **第四步**: 实现函数宏展开
5. **第五步**: 集成到编译流水线
6. **第六步**: 编写测试用例
7. **第七步**: 测试验证

### 5.2 预估时间

| 步骤 | 预估时间 |
|-----|---------|
| 创建模块结构 | 30分钟 |
| 实现 #define 解析 | 1小时 |
| 实现宏展开 | 1小时 |
| 实现函数宏 | 1.5小时 |
| 集成到流水线 | 1小时 |
| 编写测试用例 | 1小时 |
| 测试验证 | 1小时 |
| **总计** | **7小时** |

---

## 6. 验收标准

- [ ] 简单宏定义正确解析
- [ ] 简单宏展开正确
- [ ] 函数宏定义正确解析
- [ ] 函数宏展开正确
- [ ] `#undef` 正常工作
- [ ] 宏重定义报错
- [ ] 参数数量不匹配报错
- [ ] 所有测试用例通过

---

## 7. 后续扩展

### 7.1 高级宏特性

- 字符串化操作符 `#`
- 连接操作符 `##`
- 可变参数宏 `...`
- 预定义宏（如 `__FILE__`, `__LINE__`）

### 7.2 ZhC 特有宏

```zhc
// ZhC 特有预定义宏
#define __ZHC_VERSION__ "1.0.0"
#define __ZHC_LANGUAGE__ "中文"
#define __ZHONGWEN__ 1
```

---

## 8. 相关文档

- C 预处理器规范: ISO/IEC 9899 - 6.10
- GCC 预处理器文档: https://gcc.gnu.org/onlinedocs/cpp/
- 现有编译流程: `src/zhc/compiler/pipeline.py`

---

**创建日期**: 2026-04-09  
**最后更新**: 2026-04-09
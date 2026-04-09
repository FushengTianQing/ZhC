# P0-预处理器-#include头文件

## 基本信息

- **优先级**: P0
- **功能模块**: 预处理器
- **功能名称**: #include 头文件包含
- **创建时间**: 2026-04-09

## 功能概述

支持头文件包含指令，将外部文件内容插入到当前源文件中。

## 语法规格

### C 语言参考

```c
#include <stdio.h>      // 系统头文件，从系统路径搜索
#include "myheader.h"   // 用户头文件，先从当前目录搜索
#include "utils/helper.h"  // 相对路径
```

### ZhC 目标语法

```
#include <标准库头文件>
#include "用户头文件.zh"
#include "路径/文件.zh"
```

## 功能描述

### 核心行为

1. **尖括号形式 `#include <file>`**
   - 从标准库路径搜索
   - 用于系统/标准库头文件
   - 搜索路径：编译器内置路径

2. **双引号形式 `#include "file"`**
   - 先从当前文件所在目录搜索
   - 未找到时，再从标准路径搜索
   - 用于用户自定义头文件

3. **路径解析**
   - 支持相对路径：`"utils/helper.zh"`
   - 支持绝对路径：`"/usr/local/include/lib.zh"`
   - 路径分隔符：`/`（统一使用正斜杠）

4. **包含保护**
   - 防止重复包含同一文件
   - 通常配合 `#ifndef` / `#define` / `#endif` 使用

### 搜索路径优先级

```
1. 当前文件所在目录（仅双引号形式）
2. 命令行指定的 -I 路径
3. 编译器内置标准库路径
```

## 技术实现

### 文件位置

`src/zhc/compiler/preprocessor.py`（新建或扩展）

### 数据结构

```python
@dataclass
class IncludeInfo:
    source_file: str           # 包含此指令的源文件
    include_file: str          # 被包含的文件路径
    search_type: IncludeType   # SYSTEM | USER
    resolved_path: Optional[str]  # 解析后的绝对路径
    line_number: int           # 指令所在行号

class IncludeType(Enum):
    SYSTEM = "system"  # <file>
    USER = "user"      # "file"

class Preprocessor:
    def __init__(self, ...):
        self.include_paths: list[str] = []  # 搜索路径列表
        self.included_files: set[str] = set()  # 已包含文件（防重复）
        self.include_stack: list[str] = []  # 包含栈（检测循环包含）
```

### 核心算法

```python
def _process_include(self, include_str: str, include_type: IncludeType) -> Optional[str]:
    """处理 #include 指令"""
    # 1. 解析文件路径
    file_path = include_str.strip('"<>"')

    # 2. 检测循环包含
    if file_path in self.include_stack:
        raise PreprocessorError(f"Circular include detected: {file_path}")

    # 3. 解析实际路径
    resolved = self._resolve_include_path(file_path, include_type)
    if resolved is None:
        raise PreprocessorError(f"Include file not found: {file_path}")

    # 4. 检查是否已包含
    if resolved in self.included_files:
        return None  # 跳过已包含文件

    # 5. 读取并处理文件
    self.include_stack.append(file_path)
    self.included_files.add(resolved)

    content = self._read_file(resolved)
    processed = self._process_file(content, resolved)

    self.include_stack.pop()

    return processed

def _resolve_include_path(self, file_path: str, include_type: IncludeType) -> Optional[str]:
    """解析包含路径"""
    search_paths = []

    if include_type == IncludeType.USER:
        # 当前文件所在目录
        current_dir = os.path.dirname(self.current_file)
        search_paths.append(current_dir)

    # 添加 -I 指定的路径
    search_paths.extend(self.include_paths)

    # 添加标准库路径
    search_paths.append(self.stdlib_path)

    # 按顺序搜索
    for base in search_paths:
        full_path = os.path.join(base, file_path)
        if os.path.isfile(full_path):
            return os.path.abspath(full_path)

    return None
```

## 实现步骤

### 阶段 1：基础框架

1. 创建 `IncludeInfo` 数据结构
2. 在 `Preprocessor` 类中添加 `include_paths` 和 `included_files`
3. 解析 `#include` 指令语法
4. 实现基本的文件读取

### 阶段 2：路径解析

1. 实现双引号形式的当前目录搜索
2. 实现尖括号形式的系统路径搜索
3. 支持命令行 `-I` 参数添加搜索路径
4. 处理相对路径和绝对路径

### 阶段 3：包含保护

1. 实现已包含文件集合检查
2. 实现包含栈检测循环包含
3. 支持传统的 `#ifndef` 保护模式

### 阶段 4：错误处理

1. 文件不存在错误
2. 循环包含错误
3. 权限错误
4. 路径解析错误

## 测试用例

### 基本包含

```zhc
// main.zh
#include "utils.zh"
#include <stdlib.zh>

// utils.zh
函数 辅助功能() {
    返回 1
}
```

### 包含保护

```zhc
// header.zh
#ifndef HEADER_ZH
#define HEADER_ZH

常量 版本 = "1.0"

#endif

// main.zh
#include "header.zh"
#include "header.zh"  // 第二次包含会被跳过
```

### 循环包含检测

```zhc
// a.zh
#include "b.zh"

// b.zh
#include "a.zh"  // 错误：检测到循环包含
```

## 依赖关系

- **前置依赖**: P0-预处理器-#define宏定义（包含保护需要）
- **前置依赖**: P0-预处理器-#ifdef条件编译（包含保护需要）
- **后续功能**: 标准库头文件系统

## 配置选项

```python
# 编译器配置
class CompilerConfig:
    include_paths: list[str] = []  # -I 路径
    stdlib_path: str = "/usr/local/lib/zhc/std"  # 标准库路径
    max_include_depth: int = 100  # 最大包含深度
```

## 状态

- [ ] 待开发
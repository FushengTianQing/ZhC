# ZhC 调试指南

本文档介绍如何使用 GDB/LLDB 调试 ZhC 编译的程序。

## 目录

1. [调试信息生成](#调试信息生成)
2. [GDB 调试](#gdb-调试)
3. [LLDB 调试](#lldb-调试)
4. [调试技巧](#调试技巧)
5. [常见问题](#常见问题)

---

## 调试信息生成

### 编译时启用调试信息

使用 `-g` 或 `--debug` 选项编译 ZhC 程序：

```bash
# 编译带调试信息的程序
zhc compile -g source.zhc -o output

# 或使用完整选项
zhc compile --debug --output=output source.zhc
```

### 调试信息格式

ZhC 生成 DWARF 5 格式的调试信息，包含：

- **行号信息** (.debug_line): 源码行号与机器码地址映射
- **符号信息** (.debug_info): 函数、变量、类型定义
- **缩写表** (.debug_abbrev): DIE 缩写定义
- **字符串表** (.debug_str): 字符串常量

### 调试信息内容

生成的调试信息包括：

| 类型 | DWARF 标签 | 说明 |
|------|-----------|------|
| 编译单元 | DW_TAG_compile_unit | 整个源文件 |
| 函数 | DW_TAG_subprogram | 函数定义 |
| 参数 | DW_TAG_formal_parameter | 函数参数 |
| 变量 | DW_TAG_variable | 局部/全局变量 |
| 基本类型 | DW_TAG_base_type | 整数、浮点、字符 |
| 结构体 | DW_TAG_structure_type | 结构体定义 |
| 成员 | DW_TAG_member | 结构体成员 |
| 枚举 | DW_TAG_enumeration_type | 枚举类型 |
| 数组 | DW_TAG_array_type | 数组类型 |
| 指针 | DW_TAG_pointer_type | 指针类型 |

---

## GDB 调试

### 启动调试

```bash
# 启动 GDB
gdb ./output

# 或直接带参数启动
gdb --args ./output arg1 arg2
```

### 常用命令

#### 断点操作

```gdb
# 在函数入口设置断点
break 函数名
break main

# 在源码行设置断点
break source.zhc:10

# 在地址设置断点
break *0x400500

# 查看断点列表
info breakpoints

# 删除断点
delete 1
delete  # 删除所有断点

# 禁用/启用断点
disable 1
enable 1
```

#### 执行控制

```gdb
# 运行程序
run

# 继续执行
continue

# 单步执行（进入函数）
step

# 单步执行（不进入函数）
next

# 执行到当前函数返回
finish

# 执行到指定行
until 20
```

#### 查看信息

```gdb
# 查看源码
list
list 函数名
list 10,20

# 查看变量
print 变量名
print *指针
print 数组[0]

# 查看局部变量
info locals

# 查看函数参数
info args

# 查看调用栈
backtrace
bt full  # 包含局部变量

# 切换栈帧
frame 1
up
down
```

#### 内存查看

```gdb
# 查看内存
x/10x 0x400500  # 10 个十六进制值
x/10i $pc       # 10 条指令
x/s 字符串指针   # 字符串

# 查看寄存器
info registers
print $rax
```

### ZhC 特定调试

#### 中文函数名

```gdb
# ZhC 支持中文函数名
break 主函数
break 计算总和

# 查看中文变量
print 计数器
print 结果
```

#### 中文类型

```gdb
# 查看中文类型变量
print 点.x
print 点.y

# 查看结构体
ptype 点
```

---

## LLDB 调试

### 启动调试

```bash
# 启动 LLDB
lldb ./output

# 或带参数启动
lldb ./output arg1 arg2
```

### 常用命令

LLDB 命令与 GDB 类似，但语法略有不同：

#### 断点操作

```lldb
# 设置断点
breakpoint set --name 函数名
breakpoint set --file source.zhc --line 10

# 简写形式
b 函数名
b source.zhc:10

# 查看断点
breakpoint list

# 删除断点
breakpoint delete 1
```

#### 执行控制

```lldb
# 运行程序
run

# 继续执行
continue
c

# 单步执行
step
s

next
n

# 执行到返回
finish
```

#### 查看信息

```lldb
# 查看源码
source list
frame select  # 显示当前位置

# 查看变量
frame variable
frame variable 变量名

# 查看调用栈
thread backtrace
bt

# 切换栈帧
frame select 1
up
down
```

---

## 调试技巧

### 条件断点

```gdb
# 条件断点
break 函数名 if 变量 > 10
break source.zhc:20 if 计数器 == 5

# LLDB
breakpoint set --name 函数名 --condition '变量 > 10'
```

### 监视点

```gdb
# 监视变量变化
watch 变量名

# 监视内存地址
watch *0x400500
```

### 日志断点

不暂停执行，只打印信息：

```gdb
# GDB: 使用 commands
break 函数名
commands
  printf "进入函数，参数=%d\n", 参数
  continue
end

# LLDB: 使用 breakpoint command add
breakpoint set --name 函数名
breakpoint command add
> expr -- 参数
> continue
> DONE
```

### 调试优化代码

即使编译时启用了优化，仍可调试：

```bash
# 保留调试信息但启用优化
zhc compile -g -O2 source.zhc -o output
```

注意：
- 部分变量可能被优化掉
- 行号可能不准确
- 执行顺序可能改变

---

## 常见问题

### Q: 调试器找不到源文件

**原因**: 源文件路径不正确或已移动

**解决**:

```gdb
# 设置源文件路径
directory /path/to/source

# 或替换路径
set substitute-path /old/path /new/path
```

### Q: 变量显示 "optimized out"

**原因**: 编译器优化导致变量被移除

**解决**:
- 使用 `-O0` 编译（无优化）
- 或在关键位置使用 `volatile` 关键字

### Q: 中文显示乱码

**原因**: 终端编码设置不正确

**解决**:

```bash
# 设置终端编码为 UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# macOS
export LANG=zh_CN.UTF-8
```

### Q: 断点不命中

**原因**: 函数被内联或优化

**解决**:

```gdb
# 查看函数是否被内联
info functions 函数名

# 禁用内联编译
zhc compile -g -fno-inline source.zhc -o output
```

### Q: DWARF 版本不兼容

**原因**: 调试器不支持 DWARF 5

**解决**:

```bash
# 检查调试器 DWARF 支持
gdb --version  # GDB 10+ 支持 DWARF 5
lldb --version # LLDB 12+ 支持 DWARF 5

# 使用 DWARF 4（如果需要）
zhc compile -g --dwarf-version=4 source.zhc -o output
```

---

## 调试示例

### 示例程序

```zhc
// debug_example.zhc
函数 主函数() {
    变量 计数器 = 0
    变量 总和 = 0
    
    循环 (计数器 从 1 到 10) {
        总和 = 总和 + 计数器
    }
    
    打印("总和 = ", 总和)
    返回 总和
}
```

### 调试步骤

```bash
# 1. 编译带调试信息
zhc compile -g debug_example.zhc -o debug_example

# 2. 启动 GDB
gdb ./debug_example

# 3. 设置断点
(gdb) break 主函数
(gdb) break debug_example.zhc:6

# 4. 运行程序
(gdb) run

# 5. 单步执行
(gdb) step
(gdb) next

# 6. 查看变量
(gdb) print 计数器
(gdb) print 总和

# 7. 继续执行
(gdb) continue

# 8. 查看结果
(gdb) print 总和
$1 = 55
```

---

## 进阶调试

### 多线程调试

```gdb
# 查看线程
info threads

# 切换线程
thread 2

# 在所有线程设置断点
set breakpoint pending on
break 函数名
```

### 远程调试

```bash
# 目标机器启动 gdbserver
gdbserver :1234 ./output

# 本地机器连接
gdb ./output
(gdb) target remote 目标IP:1234
```

### 核心转储调试

```bash
# 启用核心转储
ulimit -c unlimited

# 程序崩溃后
gdb ./output core

# 分析崩溃位置
(gdb) bt
(gdb) frame 0
(gdb) info locals
```

---

## 参考资源

- [GDB 官方文档](https://sourceware.org/gdb/documentation/)
- [LLDB 官方文档](https://lldb.llvm.org/use/tutorial.html)
- [DWARF 标准](https://dwarfstd.org/)
- [ZhC 语言参考](./LANGUAGE_REFERENCE.md)

---

**创建日期**: 2026-04-08
**最后更新**: 2026-04-08
**维护者**: ZHC 开发团队
# -*- coding: utf-8 -*-
"""
ZHC IR - 映射表

中文关键字/类型 → C 关键字/类型 的映射表。
从 codegen/c_codegen.py 提取，供 IR→C 后端和 AST→C 代码生成器共同使用。

作者：远
日期：2026-04-03
"""

# 中文类型 -> C 类型映射
TYPE_MAP = {
    "整数型": "int",
    "浮点型": "float",
    "字符型": "char",
    "布尔型": "_Bool",
    "空型": "void",
    "无类型": "void",
    "字符串型": "char*",
    "字节型": "unsigned char",
    "双精度浮点型": "double",
    "逻辑型": "_Bool",
    "长整数型": "long",
    "短整数型": "short",
}

# 中文修饰符 -> C 修饰符
MODIFIER_MAP = {
    "常量": "const",
    "静态": "static",
    "易变": "volatile",
    "外部": "extern",
    "内联": "inline",
    "无符号": "unsigned",
    "有符号": "signed",
    "注册": "register",
}

# 特殊函数名映射（中文函数名 -> C 函数名）
FUNCTION_NAME_MAP = {
    "主函数": "main",
    "主程序": "main",
}

# 标准 include 映射（根据模块名 -> include 指令）
INCLUDE_MAP = {
    "标准输入输出": "#include <stdio.h>",
    "stdio": "#include <stdio.h>",
    "标准库": "#include <stdlib.h>",
    "stdlib": "#include <stdlib.h>",
    "字符串": "#include <string.h>",
    "string": "#include <string.h>",
    "数学": "#include <math.h>",
    "math": "#include <math.h>",
    "时间": "#include <time.h>",
    "time": "#include <time.h>",
    "字符处理": "#include <ctype.h>",
    "ctype": "#include <ctype.h>",
    "断言": "#include <assert.h>",
    "assert": "#include <assert.h>",
    "标准布尔": "#include <stdbool.h>",
    "stdbool": "#include <stdbool.h>",
}

# C 标准库函数名映射（中文函数名 -> C 函数名）
STDLIB_FUNC_MAP = {
    "打印": "printf",
    "输入": "scanf",
    "输出字符": "putchar",
    "输入字符": "getchar",
    "打印字符串": "puts",
    "打开文件": "fopen",
    "关闭文件": "fclose",
    "字符串长度": "strlen",
    "字符串复制": "strcpy",
    "申请": "malloc",
    "释放": "free",
    "退出程序": "exit",
    "平方根": "sqrt",
    "幂函数": "pow",
    "绝对值": "abs",
}


def resolve_type(zhc_type: str) -> str:
    """解析中文类型为 C 类型"""
    # 处理指针类型（如 "整数型*"）
    if zhc_type.endswith("*"):
        base_type = zhc_type[:-1].strip()
        return resolve_type(base_type) + "*"

    # 处理数组类型（如 "整数型[10]"）
    if zhc_type.endswith("]"):
        import re

        match = re.match(r"(.+)\[(\d+)\]$", zhc_type)
        if match:
            base_type = match.group(1)
            size = match.group(2)
            return f"{resolve_type(base_type)}[{size}]"

    return TYPE_MAP.get(zhc_type, zhc_type)


def resolve_function_name(name: str) -> str:
    """解析中文函数名为 C 函数名"""
    # 先查 STDLIB_FUNC_MAP（标准库函数）
    if name in STDLIB_FUNC_MAP:
        return STDLIB_FUNC_MAP[name]
    # 再查 FUNCTION_NAME_MAP（特殊函数）
    if name in FUNCTION_NAME_MAP:
        return FUNCTION_NAME_MAP[name]
    return name


def resolve_modifier(modifier: str) -> str:
    """解析中文修饰符为 C 修饰符"""
    return MODIFIER_MAP.get(modifier, modifier)


def resolve_include(module_name: str) -> str:
    """解析模块名为 include 指令"""
    return INCLUDE_MAP.get(module_name, f"/* unknown module: {module_name} */")

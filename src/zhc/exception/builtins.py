# -*- coding: utf-8 -*-
"""
内置异常类型定义

提供内置异常类型的详细信息，包括错误码、描述等。

作者：远
日期：2026-04-10
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


# 错误码前缀定义
ERROR_CODE_PREFIX = "E"


@dataclass
class BuiltinExceptionInfo:
    """
    内置异常详细信息

    Attributes:
        name: 异常类型名称
        error_code: 错误码（数字部分）
        full_code: 完整错误码（如 E001）
        description: 异常描述
        common_causes: 常见原因列表
        suggestions: 修复建议列表
    """

    name: str
    error_code: int
    description: str
    common_causes: List[str]
    suggestions: List[str]


# 内置异常详细信息注册表
BUILTIN_EXCEPTIONS: Dict[str, BuiltinExceptionInfo] = {
    # ===== Error 分支 =====
    "错误": BuiltinExceptionInfo(
        name="错误",
        error_code=1000,
        description="所有不可恢复错误的基类",
        common_causes=["系统级故障", "硬件错误", "严重资源耗尽"],
        suggestions=["检查系统状态", "查看系统日志", "可能需要重启程序"],
    ),
    "内存错误": BuiltinExceptionInfo(
        name="内存错误",
        error_code=1001,
        description="内存分配或访问错误",
        common_causes=[
            "尝试分配过大的内存",
            "内存耗尽",
            "访问已释放的内存",
            "重复释放内存",
        ],
        suggestions=[
            "检查内存使用量",
            "释放不必要的内存",
            "修复内存泄漏",
        ],
    ),
    "栈溢出错误": BuiltinExceptionInfo(
        name="栈溢出错误",
        error_code=1002,
        description="栈空间耗尽，通常由递归过深导致",
        common_causes=[
            "无限递归",
            "递归深度过大",
            "栈帧过大（大型局部变量）",
        ],
        suggestions=[
            "检查递归终止条件",
            "减少递归深度",
            "将大型局部变量改为堆分配",
        ],
    ),
    "系统错误": BuiltinExceptionInfo(
        name="系统错误",
        error_code=1003,
        description="系统级错误",
        common_causes=[
            "系统调用失败",
            "权限不足",
            "资源不可用",
        ],
        suggestions=[
            "检查系统资源状态",
            "确认程序权限",
            "查看系统错误日志",
        ],
    ),
    # ===== Exception 分支 =====
    "异常": BuiltinExceptionInfo(
        name="异常",
        error_code=2000,
        description="所有异常类型的基类",
        common_causes=["各种错误条件"],
        suggestions=["查看具体异常类型"],
    ),
    "运行时异常": BuiltinExceptionInfo(
        name="运行时异常",
        error_code=2001,
        description="运行时逻辑错误",
        common_causes=["程序逻辑错误", "非法操作"],
        suggestions=["检查代码逻辑", "添加输入验证"],
    ),
    "空指针异常": BuiltinExceptionInfo(
        name="空指针异常",
        error_code=2002,
        description="空指针访问错误",
        common_causes=[
            "返回空指针的函数未检查",
            "初始化失败",
            "删除后未置空",
        ],
        suggestions=[
            "在使用前检查指针是否为null",
            "确保初始化成功",
            "使用智能指针",
        ],
    ),
    "数组越界异常": BuiltinExceptionInfo(
        name="数组越界异常",
        error_code=2003,
        description="数组索引超出有效范围",
        common_causes=[
            "循环边界计算错误",
            "未检查数组长度",
            "索引计算错误",
        ],
        suggestions=[
            "使用安全的容器类",
            "添加边界检查",
            "使用迭代器代替索引",
        ],
    ),
    "类型转换异常": BuiltinExceptionInfo(
        name="类型转换异常",
        error_code=2004,
        description="类型转换失败",
        common_causes=[
            "不兼容的类型转换",
            "窄化转换丢失数据",
            "误用类型转换",
        ],
        suggestions=[
            "使用安全的类型转换",
            "先检查类型兼容性",
            "考虑使用变体类型",
        ],
    ),
    # ===== IO 异常 =====
    "输入输出异常": BuiltinExceptionInfo(
        name="输入输出异常",
        error_code=3000,
        description="IO 操作错误",
        common_causes=[
            "文件不存在",
            "权限不足",
            "磁盘满",
            "设备未就绪",
        ],
        suggestions=[
            "检查文件路径",
            "确认权限设置",
            "检查磁盘空间",
        ],
    ),
    "文件未找到异常": BuiltinExceptionInfo(
        name="文件未找到异常",
        error_code=3001,
        description="请求的文件不存在",
        common_causes=[
            "文件路径错误",
            "文件被删除",
            "工作目录错误",
        ],
        suggestions=[
            "检查文件路径拼写",
            "确认文件存在",
            "使用绝对路径",
        ],
    ),
    "文件权限异常": BuiltinExceptionInfo(
        name="文件权限异常",
        error_code=3002,
        description="文件访问权限不足",
        common_causes=[
            "文件设为只读",
            "当前用户无权限",
            "目录无写权限",
        ],
        suggestions=[
            "修改文件权限",
            "以更高权限运行",
            "使用有权限的目录",
        ],
    ),
    # ===== 算术异常 =====
    "算术异常": BuiltinExceptionInfo(
        name="算术异常",
        error_code=4000,
        description="算术运算错误",
        common_causes=[
            "除零操作",
            "数值溢出",
            "无效的数学运算",
        ],
        suggestions=[
            "检查运算操作数",
            "添加溢出检测",
            "使用大数类型",
        ],
    ),
    "除零异常": BuiltinExceptionInfo(
        name="除零异常",
        error_code=4001,
        description="除数为零",
        common_causes=[
            "除数变量未初始化",
            "除数在某些情况下为零",
            "除数被意外设置为零",
        ],
        suggestions=[
            "在除法前检查除数",
            "添加除数范围检查",
            "使用默认值处理零",
        ],
    ),
    "溢出异常": BuiltinExceptionInfo(
        name="溢出异常",
        error_code=4002,
        description="数值运算结果超出类型范围",
        common_causes=[
            "数值超出类型表示范围",
            "累加/累减操作未检查边界",
            "类型选择过小",
        ],
        suggestions=[
            "使用更大范围的类型",
            "添加溢出检查",
            "使用饱和运算",
        ],
    ),
}


def get_exception_info(name: str) -> Optional[BuiltinExceptionInfo]:
    """
    获取内置异常详细信息

    Args:
        name: 异常类型名称

    Returns:
        异常详细信息，如果不存在返回 None
    """
    return BUILTIN_EXCEPTIONS.get(name)


def get_error_code(name: str) -> Optional[str]:
    """
    获取异常的完整错误码

    Args:
        name: 异常类型名称

    Returns:
        完整错误码（如 E001），如果不存在返回 None
    """
    info = BUILTIN_EXCEPTIONS.get(name)
    if info:
        return f"E{info.error_code:04d}"
    return None


def get_all_exception_names() -> List[str]:
    """
    获取所有内置异常类型名称

    Returns:
        异常类型名称列表
    """
    return list(BUILTIN_EXCEPTIONS.keys())


def lookup_by_error_code(code: str) -> Optional[str]:
    """
    根据错误码查找异常类型名称

    Args:
        code: 完整错误码（如 E001）

    Returns:
        异常类型名称，如果不存在返回 None
    """
    if not code.startswith("E"):
        return None

    try:
        num = int(code[1:])
        for name, info in BUILTIN_EXCEPTIONS.items():
            if info.error_code == num:
                return name
    except ValueError:
        pass

    return None


__all__ = [
    "BuiltinExceptionInfo",
    "BUILTIN_EXCEPTIONS",
    "get_exception_info",
    "get_error_code",
    "get_all_exception_names",
    "lookup_by_error_code",
]

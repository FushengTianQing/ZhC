# -*- coding: utf-8 -*-
"""
ZHC IR - 操作码定义

定义 ZHC IR 的所有操作码。

设计原则：
- 非严格 SSA：变量可多次赋值，用 ALLOC + STORE 代替 phi 节点
- 类型保留：IR 指令携带类型信息
- 中文友好：每个操作码有中文名称

作者：远
日期：2026-04-03
"""

from enum import Enum
from ..errors import CodeGenerationError


class Opcode(Enum):
    """
    ZHC IR 操作码

    每个操作码包含：
    - name: 操作码名称
    - category: 所属类别（算术/比较/位运算/逻辑/内存/控制流/转换/其他）
    - chinese: 中文名称
    - is_terminator: 是否是终止指令（用于基本块末尾）
    - has_result: 是否产生结果值
    """

    # ========== 算术运算 ==========
    ADD = ("add", "算术", "加法", False, True)    # +
    SUB = ("sub", "算术", "减法", False, True)    # -
    MUL = ("mul", "算术", "乘法", False, True)    # *
    DIV = ("div", "算术", "除法", False, True)    # /
    MOD = ("mod", "算术", "取模", False, True)    # %
    NEG = ("neg", "算术", "取负", False, True)    # 一元负

    # ========== 比较运算 ==========
    EQ = ("eq", "比较", "等于", False, True)      # ==
    NE = ("ne", "比较", "不等于", False, True)    # !=
    LT = ("lt", "比较", "小于", False, True)      # <
    LE = ("le", "比较", "小于等于", False, True)  # <=
    GT = ("gt", "比较", "大于", False, True)      # >
    GE = ("ge", "比较", "大于等于", False, True)  # >=

    # ========== 位运算 ==========
    AND = ("and", "位运算", "按位与", False, True)   # &
    OR = ("or", "位运算", "按位或", False, True)    # |
    XOR = ("xor", "位运算", "按位异或", False, True) # ^
    NOT = ("not", "位运算", "按位取反", False, True) # ~
    SHL = ("shl", "位运算", "左移", False, True)   # <<
    SHR = ("shr", "位运算", "右移", False, True)    # >>

    # ========== 逻辑运算 ==========
    L_AND = ("l_and", "逻辑", "逻辑与", False, True)  # &&
    L_OR = ("l_or", "逻辑", "逻辑或", False, True)   # ||
    L_NOT = ("l_not", "逻辑", "逻辑非", False, True)  # !

    # ========== 内存操作 ==========
    ALLOC = ("alloc", "内存", "分配内存", False, True)    # 分配局部变量
    LOAD = ("load", "内存", "加载", False, True)           # 从内存加载
    STORE = ("store", "内存", "存储", False, False)        # 存储到内存
    GETPTR = ("getptr", "内存", "获取指针", False, True)  # 获取结构体/数组成员指针
    GEP = ("gep", "内存", "指针运算", False, True)        # GetElementPtr，数组索引

    # ========== 控制流 ==========
    JMP = ("jmp", "控制流", "跳转", True, False)          # 无条件跳转
    JZ = ("jz", "控制流", "条件跳转", True, False)         # 条件跳转（if）
    RET = ("ret", "控制流", "返回", True, False)           # 函数返回
    CALL = ("call", "控制流", "函数调用", False, True)      # 函数调用
    SWITCH = ("switch", "控制流", "分支跳转", True, False)  # switch 多分支
    PHI = ("phi", "控制流", "phi节点", False, True)        # SSA phi 节点

    # ========== 类型转换 ==========
    ZEXT = ("zext", "转换", "零扩展", False, True)    # 零扩展（无符号扩展）
    SEXT = ("sext", "转换", "符号扩展", False, True) # 符号扩展
    TRUNC = ("trunc", "转换", "截断", False, True)   # 截断
    BITCAST = ("bitcast", "转换", "位转换", False, True)  # 位类型转换
    INT2PTR = ("int2ptr", "转换", "整数到指针", False, True)   # 整数转指针
    PTR2INT = ("ptr2int", "转换", "指针到整数", False, True)   # 指针转整数

    # ========== 其他 ==========
    CONST = ("const", "其他", "常量", False, True)     # 常量值
    NOP = ("nop", "其他", "空操作", False, False)     # 空操作
    GLOBAL = ("global", "其他", "全局变量", False, True)  # 全局变量地址
    ARG = ("arg", "其他", "函数参数", False, True)       # 函数参数

    @property
    def name(self) -> str:
        return self.value[0]

    @property
    def category(self) -> str:
        return self.value[1]

    @property
    def chinese(self) -> str:
        return self.value[2]

    @property
    def is_terminator(self) -> bool:
        return self.value[3]

    @property
    def has_result(self) -> bool:
        return self.value[4]

    @classmethod
    def from_name(cls, name: str) -> 'Opcode':
        """根据名称查找操作码"""
        for op in cls:
            if op.name == name:
                return op
        raise CodeGenerationError(
            f"未知的操作码: {name}",
            error_code="C001",
            context=f"操作码名称: {name}",
            suggestion="请检查操作码名称是否正确"
        )

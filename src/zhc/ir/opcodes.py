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
    ADD = ("add", "算术", "加法", False, True)  # +
    SUB = ("sub", "算术", "减法", False, True)  # -
    MUL = ("mul", "算术", "乘法", False, True)  # *
    DIV = ("div", "算术", "除法", False, True)  # /
    MOD = ("mod", "算术", "取模", False, True)  # %
    NEG = ("neg", "算术", "取负", False, True)  # 一元负

    # ========== 比较运算 ==========
    EQ = ("eq", "比较", "等于", False, True)  # ==
    NE = ("ne", "比较", "不等于", False, True)  # !=
    LT = ("lt", "比较", "小于", False, True)  # <
    LE = ("le", "比较", "小于等于", False, True)  # <=
    GT = ("gt", "比较", "大于", False, True)  # >
    GE = ("ge", "比较", "大于等于", False, True)  # >=

    # ========== 位运算 ==========
    AND = ("and", "位运算", "按位与", False, True)  # &
    OR = ("or", "位运算", "按位或", False, True)  # |
    XOR = ("xor", "位运算", "按位异或", False, True)  # ^
    NOT = ("not", "位运算", "按位取反", False, True)  # ~
    SHL = ("shl", "位运算", "左移", False, True)  # <<
    SHR = ("shr", "位运算", "右移", False, True)  # >>

    # ========== 逻辑运算 ==========
    L_AND = ("l_and", "逻辑", "逻辑与", False, True)  # &&
    L_OR = ("l_or", "逻辑", "逻辑或", False, True)  # ||
    L_NOT = ("l_not", "逻辑", "逻辑非", False, True)  # !

    # ========== 内存操作 ==========
    ALLOC = ("alloc", "内存", "分配内存", False, True)  # 分配局部变量
    LOAD = ("load", "内存", "加载", False, True)  # 从内存加载
    STORE = ("store", "内存", "存储", False, False)  # 存储到内存
    GETPTR = ("getptr", "内存", "获取指针", False, True)  # 获取结构体/数组成员指针
    GEP = ("gep", "内存", "指针运算", False, True)  # GetElementPtr，数组索引

    # ========== 控制流 ==========
    JMP = ("jmp", "控制流", "跳转", True, False)  # 无条件跳转
    JZ = ("jz", "控制流", "条件跳转", True, False)  # 条件跳转（if）
    RET = ("ret", "控制流", "返回", True, False)  # 函数返回
    CALL = ("call", "控制流", "函数调用", False, True)  # 函数调用
    SWITCH = ("switch", "控制流", "分支跳转", True, False)  # switch 多分支
    PHI = ("phi", "控制流", "phi节点", False, True)  # SSA phi 节点

    # ========== 类型转换 ==========
    ZEXT = ("zext", "转换", "零扩展", False, True)  # 零扩展（无符号扩展）
    SEXT = ("sext", "转换", "符号扩展", False, True)  # 符号扩展
    TRUNC = ("trunc", "转换", "截断", False, True)  # 截断
    BITCAST = ("bitcast", "转换", "位转换", False, True)  # 位类型转换
    INT2PTR = ("int2ptr", "转换", "整数到指针", False, True)  # 整数转指针
    PTR2INT = ("ptr2int", "转换", "指针到整数", False, True)  # 指针转整数

    # ========== 异常处理 ==========
    TRY = ("try", "异常处理", "尝试块", False, False)  # try 块开始
    CATCH = ("catch", "异常处理", "捕获块", True, False)  # catch 处理器
    THROW = ("throw", "异常处理", "抛出异常", True, False)  # 抛出异常
    RESUME = ("resume", "异常处理", "恢复异常", True, False)  # 恢复异常
    LANDINGPAD = ("landingpad", "异常处理", "着陆垫", False, True)  # landingpad 指令
    INVOKE = ("invoke", "异常处理", "调用并捕获", False, True)  # 调用并设置异常处理

    # ========== 闭包/函数式 ==========
    CLOSURE_CREATE = ("closure_create", "闭包", "创建闭包", False, True)  # 创建闭包
    CLOSURE_CALL = ("closure_call", "闭包", "闭包调用", False, True)  # 调用闭包
    UPVALUE_GET = ("upvalue_get", "闭包", "获取Upvalue", False, True)  # 获取 upvalue
    UPVALUE_SET = ("upvalue_set", "闭包", "设置Upvalue", False, False)  # 设置 upvalue
    LAMBDA = ("lambda", "闭包", "Lambda表达式", False, True)  # Lambda 表达式

    # ========== 协程/异步 ==========
    COROUTINE_CREATE = ("coroutine_create", "协程", "创建协程", False, True)  # 创建协程
    COROUTINE_RESUME = ("coroutine_resume", "协程", "恢复协程", False, True)  # 恢复协程
    COROUTINE_YIELD = (
        "coroutine_yield",
        "协程",
        "协程让出",
        True,
        False,
    )  # 协程让出（终止指令）
    COROUTINE_AWAIT = ("coroutine_await", "协程", "等待协程", False, True)  # 等待协程
    COROUTINE_SPAWN = ("coroutine_spawn", "协程", "启动协程", False, True)  # 启动协程
    COROUTINE_COMPLETE = (
        "coroutine_complete",
        "协程",
        "协程完成",
        False,
        True,
    )  # 协程完成检查
    CHANNEL_CREATE = ("channel_create", "协程", "创建通道", False, True)  # 创建通道
    CHANNEL_SEND = ("channel_send", "协程", "通道发送", False, False)  # 通道发送
    CHANNEL_RECV = ("channel_recv", "协程", "通道接收", False, True)  # 通道接收

    # ========== 内存管理 ==========
    SMART_PTR_CREATE = ("smart_ptr_create", "内存管理", "创建智能指针", False, True)
    SMART_PTR_GET = ("smart_ptr_get", "内存管理", "获取智能指针值", False, True)
    SMART_PTR_RESET = ("smart_ptr_reset", "内存管理", "重置智能指针", False, False)
    SMART_PTR_RELEASE = ("smart_ptr_release", "内存管理", "释放智能指针", False, False)
    SMART_PTR_USE_COUNT = ("smart_ptr_use_count", "内存管理", "引用计数", False, True)
    MOVE = ("move", "内存管理", "移动语义", False, True)
    SCOPE_PUSH = ("scope_push", "内存管理", "进入作用域", False, False)
    SCOPE_POP = ("scope_pop", "内存管理", "退出作用域", False, False)
    DESTRUCTOR_CALL = ("destructor_call", "内存管理", "调用析构函数", False, False)

    # ========== 反射 ==========
    TYPE_INFO_GET = (
        "type_info_get",
        "反射",
        "获取类型信息",
        False,
        True,
    )  # 获取类型信息
    TYPE_INFO_NAME = (
        "type_info_name",
        "反射",
        "获取类型名称",
        False,
        True,
    )  # 获取类型名称
    TYPE_INFO_SIZE = (
        "type_info_size",
        "反射",
        "获取类型大小",
        False,
        True,
    )  # 获取类型大小
    TYPE_INFO_FIELDS = (
        "type_info_fields",
        "反射",
        "获取字段列表",
        False,
        True,
    )  # 获取字段列表
    TYPE_INFO_METHODS = (
        "type_info_methods",
        "反射",
        "获取方法列表",
        False,
        True,
    )  # 获取方法列表
    TYPE_INFO_BASE = ("type_info_base", "反射", "获取父类", False, True)  # 获取父类
    FIELD_GET = ("field_get", "反射", "获取字段信息", False, True)  # 获取字段信息
    FIELD_GET_VALUE = (
        "field_get_value",
        "反射",
        "获取字段值",
        False,
        True,
    )  # 动态获取字段值
    FIELD_SET_VALUE = (
        "field_set_value",
        "反射",
        "设置字段值",
        False,
        False,
    )  # 动态设置字段值

    # ========== 运行时类型检查 ==========
    IS_TYPE = ("is_type", "类型检查", "类型检查", False, True)  # 检查对象是否为指定类型
    IS_SUBTYPE = ("is_subtype", "类型检查", "子类型检查", False, True)  # 检查子类型关系
    IMPL_IFACE = ("impl_iface", "类型检查", "接口实现检查", False, True)  # 检查接口实现
    TYPE_EQUALS = (
        "type_equals",
        "类型检查",
        "类型相等检查",
        False,
        True,
    )  # 检查类型是否相同
    SAFE_CAST = ("safe_cast", "类型检查", "安全转换", False, True)  # 安全类型转换
    DYNAMIC_CAST = ("dynamic_cast", "类型检查", "动态转换", False, True)  # 动态类型转换
    CHECK_ASSIGNABLE = (
        "check_assignable",
        "类型检查",
        "赋值兼容检查",
        False,
        True,
    )  # 检查赋值兼容性
    IS_PRIMITIVE = (
        "is_primitive",
        "类型检查",
        "基本类型检查",
        False,
        True,
    )  # 检查是否基本类型

    # ========== 其他 ==========
    CONST = ("const", "其他", "常量", False, True)  # 常量值
    NOP = ("nop", "其他", "空操作", False, False)  # 空操作
    GLOBAL = ("global", "其他", "全局变量", False, True)  # 全局变量地址
    ARG = ("arg", "其他", "函数参数", False, True)  # 函数参数

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
    def from_name(cls, name: str) -> "Opcode":
        """根据名称查找操作码"""
        for op in cls:
            if op.name == name:
                return op
        raise CodeGenerationError(
            f"未知的操作码: {name}",
            error_code="C001",
            context=f"操作码名称: {name}",
            suggestion="请检查操作码名称是否正确",
        )

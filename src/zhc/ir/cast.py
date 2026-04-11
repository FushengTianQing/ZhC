# -*- coding: utf-8 -*-
"""
ZhC IR - 类型转换节点定义

LLVM 风格的类型转换指令继承体系：

    IRInstruction          ← 通用基类
    └── IRCastInst         ← 类型转换基类
        ├── IRSafeCastInst     ← 安全转换（as 表达式）
        ├── IRDynamicCastInst  ← 动态转换（失败抛异常）
        └── IRIsTypeInst       ← 类型检查（is 表达式）

设计原则：
- 每个具体指令有类型安全的访问接口
- 兼容通用 IRInstruction（通过 __init__ 自动注册 opcode）
- 方便 IR 优化 pass 进行类型分发

作者：远
日期：2026-04-11
"""

from typing import Optional
from .opcodes import Opcode
from .values import IRValue, ValueKind


class IRCastInst:
    """类型转换指令基类（LLVM CastInst 风格）

    提供所有类型转换指令的公共接口。

    Attributes:
        source: 源操作数
        target_type_name: 目标类型名（字符串常量）
        result: 结果值
    """

    # 子类必须设置
    _opcode: Opcode = None  # type: ignore

    def __init__(self, source: IRValue, target_type_name: str, result: IRValue):
        self.source = source
        self.target_type_name = target_type_name
        self.result = result
        # 兼容通用 IRInstruction 接口
        self._type_const = IRValue(
            target_type_name,
            "字符串型",
            ValueKind.CONST,
            const_value=target_type_name,
        )

    @property
    def opcode(self) -> Opcode:
        return self._opcode

    @property
    def operands(self) -> list:
        """兼容通用 IRInstruction 接口"""
        return [self.source, self._type_const]

    @property
    def results(self) -> list:
        """兼容通用 IRInstruction 接口"""
        return [self.result]

    def is_terminator(self) -> bool:
        return False

    def get_source_type(self) -> str:
        """获取源值的类型"""
        return self.source.ty

    def get_target_type(self) -> str:
        """获取目标类型名"""
        return self.target_type_name

    def __repr__(self) -> str:
        return (
            f"{self.result} = {self._opcode.name} "
            f'{self.source}, "{self.target_type_name}"'
        )


class IRSafeCastInst(IRCastInst):
    """安全类型转换指令（as 表达式）

    LLVM 风格对应：类似 BitCastInst + null 检查

    运行时行为：
    - 类型兼容 → 返回对象本身
    - 类型不兼容 → 返回 null
    - 源为 null → 返回 null

    IR 表示：
        %result = SAFE_CAST %source, "目标类型"
    """

    _opcode = Opcode.SAFE_CAST

    def __init__(
        self, source: IRValue, target_type_name: str, result: Optional[IRValue] = None
    ):
        # 如果没有提供 result，自动创建临时变量
        if result is None:
            result = IRValue(
                f"%safe_cast_{id(source)}",
                target_type_name,
                ValueKind.TEMP,
            )
        super().__init__(source, target_type_name, result)

    def get_result_type(self) -> str:
        """安全转换结果是可选类型"""
        return self.target_type_name


class IRDynamicCastInst(IRCastInst):
    """动态类型转换指令

    LLVM 风格对应：类似 dynamic_cast + 异常抛出

    运行时行为：
    - 类型兼容 → 返回对象本身
    - 类型不兼容 → 抛出 TypeCastError
    - 源为 null → 返回 null

    IR 表示：
        %result = DYNAMIC_CAST %source, "目标类型"
    """

    _opcode = Opcode.DYNAMIC_CAST

    def __init__(
        self,
        source: IRValue,
        target_type_name: str,
        result: Optional[IRValue] = None,
        error_type: str = "INVALID_CAST",
    ):
        if result is None:
            result = IRValue(
                f"%dyn_cast_{id(source)}",
                target_type_name,
                ValueKind.TEMP,
            )
        super().__init__(source, target_type_name, result)
        self.error_type = error_type  # 错误类型，用于代码生成

    def get_error_type(self) -> str:
        """获取失败时的错误类型"""
        return self.error_type


class IRIsTypeInst(IRCastInst):
    """类型检查指令（is 表达式）

    LLVM 风格对应：类似 ICmpInst + type_id 比较

    运行时行为：
    - 对象是指定类型（或子类型）→ 返回 true
    - 否则 → 返回 false

    IR 表示：
        %result = IS_TYPE %source, "目标类型"
    """

    _opcode = Opcode.IS_TYPE

    def __init__(
        self, source: IRValue, target_type_name: str, result: Optional[IRValue] = None
    ):
        if result is None:
            result = IRValue(
                f"%is_type_{id(source)}",
                "布尔型",
                ValueKind.TEMP,
            )
        super().__init__(source, target_type_name, result)

    def get_result_type(self) -> str:
        """类型检查结果总是布尔型"""
        return "布尔型"


# =============================================================================
# 辅助函数
# =============================================================================


def is_cast_instruction(instr) -> bool:
    """检查是否是类型转换指令"""
    return isinstance(instr, IRCastInst)


def get_cast_instruction(instr) -> Optional[IRCastInst]:
    """从通用指令中提取类型转换指令

    支持两种输入：
    1. 已经是 IRCastInst 子类
    2. 通用 IRInstruction，opcode 为 SAFE_CAST/DYNAMIC_CAST/IS_TYPE
    """
    if isinstance(instr, IRCastInst):
        return instr

    # 检查通用 IRInstruction 的 opcode
    if hasattr(instr, "opcode") and hasattr(instr, "operands"):
        op = instr.opcode
        if op in (Opcode.SAFE_CAST, Opcode.DYNAMIC_CAST, Opcode.IS_TYPE):
            # 从通用指令构造具体指令
            operands = instr.operands
            results = instr.result if hasattr(instr, "result") else []
            if len(operands) >= 2 and results:
                source = operands[0]
                type_const = operands[1]
                result = results[0]
                target_type = (
                    type_const.const_value
                    if hasattr(type_const, "const_value")
                    else str(type_const)
                )

                if op == Opcode.SAFE_CAST:
                    return IRSafeCastInst(source, target_type, result)
                elif op == Opcode.DYNAMIC_CAST:
                    return IRDynamicCastInst(source, target_type, result)
                elif op == Opcode.IS_TYPE:
                    return IRIsTypeInst(source, target_type, result)

    return None


__all__ = [
    "IRCastInst",
    "IRSafeCastInst",
    "IRDynamicCastInst",
    "IRIsTypeInst",
    "is_cast_instruction",
    "get_cast_instruction",
]

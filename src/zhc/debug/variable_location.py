# -*- coding: utf-8 -*-
"""
ZhC 变量位置追踪器

追踪变量的生命周期和存储位置，支持寄存器、栈帧、内存等。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LocationKind(Enum):
    """位置种类"""

    REGISTER = "register"  # 寄存器
    STACK = "stack"  # 栈帧偏移
    MEMORY = "memory"  # 内存地址
    CONSTANT = "constant"  # 常量值
    COMPOSITE = "composite"  # 复合位置（多寄存器/多内存）
    OPTIMIZED = "optimized"  # 被优化掉了
    IMPORTED = "imported"  # 从外部导入


@dataclass
class LiveRange:
    """
    活跃区间

    表示变量在某个地址范围内是活跃的。
    """

    start: int  # 起始地址
    end: int  # 结束地址
    location: "VariableLocation"  # 该区间内的位置

    def contains(self, address: int) -> bool:
        """检查地址是否在活跃区间内"""
        return self.start <= address < self.end

    def overlaps(self, other: "LiveRange") -> bool:
        """检查是否与另一个活跃区间重叠"""
        return self.start < other.end and other.start < self.end

    def merge(self, other: "LiveRange") -> "LiveRange":
        """合并两个相邻或重叠的活跃区间"""
        if not self.overlaps(other) and self.end != other.start:
            raise ValueError("Cannot merge non-adjacent ranges")
        return LiveRange(
            start=min(self.start, other.start),
            end=max(self.end, other.end),
            location=self.location,
        )


@dataclass
class VariableLocation:
    """
    变量位置

    描述变量的存储位置。
    """

    kind: LocationKind  # 位置种类
    value: any = None  # 位置值

    # 寄存器信息
    register_number: Optional[int] = None  # 寄存器编号
    register_name: Optional[str] = None  # 寄存器名

    # 栈帧信息
    frame_offset: Optional[int] = None  # 帧内偏移
    base_register: str = "rbp"  # 基址寄存器

    # 内存信息
    memory_address: Optional[int] = None  # 内存地址
    segment_selector: Optional[int] = None  # 段选择子

    # 复合位置
    sub_locations: List["VariableLocation"] = field(default_factory=list)

    # 元数据
    is_shadowed: bool = False  # 是否被其他变量遮蔽
    optimization_note: str = ""  # 优化说明

    def __str__(self) -> str:
        """格式化输出"""
        if self.kind == LocationKind.REGISTER:
            if self.register_name:
                return f"${self.register_name}"
            return f"%reg{self.register_number}"

        elif self.kind == LocationKind.STACK:
            sign = "+" if self.frame_offset >= 0 else ""
            base = self.base_register or "rbp"
            return f"[{base}{sign}{self.frame_offset}]"

        elif self.kind == LocationKind.MEMORY:
            if self.memory_address:
                return f"0x{self.memory_address:x}"
            return f"[seg{self.segment_selector}:?]"

        elif self.kind == LocationKind.CONSTANT:
            return str(self.value)

        elif self.kind == LocationKind.COMPOSITE:
            parts = [str(loc) for loc in self.sub_locations]
            return "{" + ", ".join(parts) + "}"

        elif self.kind == LocationKind.OPTIMIZED:
            return f"<optimized out: {self.optimization_note}>"

        elif self.kind == LocationKind.IMPORTED:
            return f"<imported: {self.value}>"

        return f"<unknown: {self.kind}>"

    @classmethod
    def in_register(
        cls, register_number: int, register_name: str = ""
    ) -> "VariableLocation":
        """创建寄存器位置"""
        return cls(
            kind=LocationKind.REGISTER,
            value=register_number,
            register_number=register_number,
            register_name=register_name,
        )

    @classmethod
    def on_stack(cls, offset: int, base_register: str = "rbp") -> "VariableLocation":
        """创建栈位置"""
        return cls(
            kind=LocationKind.STACK,
            value=offset,
            frame_offset=offset,
            base_register=base_register,
        )

    @classmethod
    def in_memory(cls, address: int) -> "VariableLocation":
        """创建内存位置"""
        return cls(
            kind=LocationKind.MEMORY,
            value=address,
            memory_address=address,
        )

    @classmethod
    def constant(cls, value: any) -> "VariableLocation":
        """创建常量位置"""
        return cls(
            kind=LocationKind.CONSTANT,
            value=value,
        )

    @classmethod
    def optimized(cls, note: str = "") -> "VariableLocation":
        """创建优化掉的位置"""
        return cls(
            kind=LocationKind.OPTIMIZED,
            optimization_note=note,
        )


@dataclass
class VariableDebugLocation:
    """
    变量调试位置

    包含变量的完整位置信息，包括活跃区间。
    """

    name: str  # 变量名
    type_name: str  # 类型名
    declaration_address: Optional[int] = None  # 声明地址
    declaration_line: int = 0  # 声明行号
    declaration_file: str = ""  # 声明文件

    # 位置信息
    locations: List[VariableLocation] = field(default_factory=list)  # 位置列表
    live_ranges: List[LiveRange] = field(default_factory=list)  # 活跃区间

    # 作用域
    scope_start: int = 0  # 作用域起始
    scope_end: int = 0  # 作用域结束

    # 属性
    is_parameter: bool = False  # 是否为参数
    is_global: bool = False  # 是否为全局变量
    is_static: bool = False  # 是否为静态变量
    is_const: bool = False  # 是否为常量
    is_volatile: bool = False  # 是否为易失性

    # DWARF 位置表达式
    location_expression: Optional[bytes] = None

    def get_location_at(self, address: int) -> Optional[VariableLocation]:
        """获取指定地址处的变量位置"""
        for range in self.live_ranges:
            if range.contains(address):
                return range.location
        return None

    def is_live_at(self, address: int) -> bool:
        """检查变量在指定地址是否活跃"""
        for range in self.live_ranges:
            if range.contains(address):
                return True
        return False

    def split_at(
        self, address: int
    ) -> Tuple["VariableDebugLocation", "VariableDebugLocation"]:
        """在指定地址分割活跃区间"""
        before_ranges = []
        after_ranges = []

        for range in self.live_ranges:
            if range.end <= address:
                before_ranges.append(range)
            elif range.start >= address:
                after_ranges.append(range)
            else:
                # 分割当前区间
                before_ranges.append(
                    LiveRange(
                        start=range.start,
                        end=address,
                        location=range.location,
                    )
                )
                after_ranges.append(
                    LiveRange(
                        start=address,
                        end=range.end,
                        location=range.location,
                    )
                )

        before = VariableDebugLocation(
            name=self.name,
            type_name=self.type_name,
            declaration_address=self.declaration_address,
            declaration_line=self.declaration_line,
            declaration_file=self.declaration_file,
            live_ranges=before_ranges,
            scope_start=self.scope_start,
            scope_end=address,
            is_parameter=self.is_parameter,
            is_global=self.is_global,
            is_static=self.is_static,
        )

        after = VariableDebugLocation(
            name=self.name,
            type_name=self.type_name,
            declaration_address=self.declaration_address,
            declaration_line=self.declaration_line,
            declaration_file=self.declaration_file,
            live_ranges=after_ranges,
            scope_start=address,
            scope_end=self.scope_end,
            is_parameter=self.is_parameter,
            is_global=self.is_global,
            is_static=self.is_static,
        )

        return before, after


class VariableLocationTracker:
    """
    变量位置追踪器

    追踪变量的生命周期和存储位置。
    """

    def __init__(self):
        self.variables: Dict[str, VariableDebugLocation] = {}
        self._allocated_registers: Set[int] = set()
        self._allocated_stack_slots: Dict[int, str] = {}  # offset -> var_name

    def register_variable(
        self,
        name: str,
        type_name: str,
        is_parameter: bool = False,
        is_global: bool = False,
        is_static: bool = False,
        is_const: bool = False,
        is_volatile: bool = False,
    ) -> VariableDebugLocation:
        """
        注册变量

        Args:
            name: 变量名
            type_name: 类型名
            is_parameter: 是否为参数
            is_global: 是否为全局变量
            is_static: 是否为静态变量
            is_const: 是否为常量
            is_volatile: 是否为易失性

        Returns:
            变量调试位置
        """
        var_location = VariableDebugLocation(
            name=name,
            type_name=type_name,
            is_parameter=is_parameter,
            is_global=is_global,
            is_static=is_static,
            is_const=is_const,
            is_volatile=is_volatile,
        )
        self.variables[name] = var_location
        return var_location

    def assign_register(
        self,
        name: str,
        register_number: int,
        register_name: str = "",
        start: int = 0,
        end: int = 0,
    ) -> None:
        """
        分配寄存器

        Args:
            name: 变量名
            register_number: 寄存器编号
            register_name: 寄存器名
            start: 起始地址
            end: 结束地址
        """
        if name not in self.variables:
            self.register_variable(name, "unknown")

        var = self.variables[name]
        location = VariableLocation.in_register(register_number, register_name)
        var.locations.append(location)

        if start > 0 and end > 0:
            live_range = LiveRange(start=start, end=end, location=location)
            var.live_ranges.append(live_range)

        self._allocated_registers.add(register_number)

    def assign_stack_slot(
        self,
        name: str,
        offset: int,
        base_register: str = "rbp",
        start: int = 0,
        end: int = 0,
    ) -> None:
        """
        分配栈槽

        Args:
            name: 变量名
            offset: 偏移量
            base_register: 基址寄存器
            start: 起始地址
            end: 结束地址
        """
        if name not in self.variables:
            self.register_variable(name, "unknown")

        var = self.variables[name]
        location = VariableLocation.on_stack(offset, base_register)
        var.locations.append(location)

        if start > 0 and end > 0:
            live_range = LiveRange(start=start, end=end, location=location)
            var.live_ranges.append(live_range)

        self._allocated_stack_slots[offset] = name

    def assign_memory(
        self,
        name: str,
        address: int,
        start: int = 0,
        end: int = 0,
    ) -> None:
        """
        分配内存

        Args:
            name: 变量名
            address: 内存地址
            start: 起始地址
            end: 结束地址
        """
        if name not in self.variables:
            self.register_variable(name, "unknown")

        var = self.variables[name]
        location = VariableLocation.in_memory(address)
        var.locations.append(location)

        if start > 0 and end > 0:
            live_range = LiveRange(start=start, end=end, location=location)
            var.live_ranges.append(live_range)

    def mark_optimized(
        self,
        name: str,
        note: str = "",
    ) -> None:
        """
        标记为优化掉

        Args:
            name: 变量名
            note: 说明
        """
        if name not in self.variables:
            self.register_variable(name, "unknown")

        var = self.variables[name]
        location = VariableLocation.optimized(note)
        var.locations.append(location)

    def set_scope(self, name: str, start: int, end: int) -> None:
        """
        设置作用域

        Args:
            name: 变量名
            start: 起始地址
            end: 结束地址
        """
        if name in self.variables:
            var = self.variables[name]
            var.scope_start = start
            var.scope_end = end

    def get_variable(self, name: str) -> Optional[VariableDebugLocation]:
        """获取变量"""
        return self.variables.get(name)

    def get_variables_at(self, address: int) -> List[VariableDebugLocation]:
        """获取指定地址处活跃的变量"""
        result = []
        for var in self.variables.values():
            if var.is_live_at(address):
                result.append(var)
        return result

    def get_parameter_at(self, address: int) -> List[VariableDebugLocation]:
        """获取指定地址处的参数"""
        result = []
        for var in self.variables.values():
            if var.is_parameter and var.is_live_at(address):
                result.append(var)
        return result

    def get_allocated_registers(self) -> Set[int]:
        """获取已分配的寄存器"""
        return self._allocated_registers.copy()

    def get_available_register(self) -> Optional[int]:
        """获取可用寄存器"""
        # 常用的 caller-saved 寄存器
        caller_saved = [0, 1, 2, 3, 4, 5, 6, 7]  # rax, rcx, rdx, rsi, rdi, r8, r9, r10
        for reg in caller_saved:
            if reg not in self._allocated_registers:
                return reg
        return None

    def generate_location_expression(self, location: VariableLocation) -> bytes:
        """
        生成 DWARF 位置表达式

        Args:
            location: 变量位置

        Returns:
            位置表达式字节
        """
        expr = bytearray()

        if location.kind == LocationKind.REGISTER:
            # DW_OP_reg0 - DW_OP_reg31
            if location.register_number is not None and location.register_number < 32:
                expr.append(0x50 + location.register_number)  # DW_OP_reg0
            else:
                # DW_OP_breg0 for larger register numbers
                expr.append(0x70 + (location.register_number % 32))  # DW_OP_breg0
                self._encode_sleb128(expr, 0)

        elif location.kind == LocationKind.STACK:
            # DW_OP_fbreg - frame base relative
            expr.append(0x91)  # DW_OP_fbreg
            self._encode_sleb128(expr, location.frame_offset or 0)

        elif location.kind == LocationKind.MEMORY:
            # DW_OP_addr
            expr.append(0x03)  # DW_OP_addr
            if location.memory_address:
                expr.extend(location.memory_address.to_bytes(8, "little"))

        elif location.kind == LocationKind.CONSTANT:
            # DW_OP_constu
            expr.append(0x32)  # DW_OP_constu
            self._encode_uleb128(expr, location.value or 0)

        elif location.kind == LocationKind.OPTIMIZED:
            # DW_OP_stack_value
            expr.append(0x13)  # DW_OP_stack_value

        return bytes(expr)

    def _encode_uleb128(self, buffer: bytearray, value: int) -> None:
        """编码 ULEB128"""
        while True:
            byte = value & 0x7F
            value >>= 7
            if value != 0:
                byte |= 0x80
            buffer.append(byte)
            if value == 0:
                break

    def _encode_sleb128(self, buffer: bytearray, value: int) -> None:
        """编码 SLEB128"""
        while True:
            byte = value & 0x7F
            value >>= 7
            # 检查符号位
            if (value == 0 and (byte & 0x40) == 0) or (
                value == -1 and (byte & 0x40) != 0
            ):
                buffer.append(byte)
                break
            byte |= 0x80
            buffer.append(byte)

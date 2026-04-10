# -*- coding: utf-8 -*-
"""
定点数类型定义 - Fixed-Point Type

支持 C99 定点数类型：
- _Fract (小数类型): 短定点小数、长定点小数、无符号定点小数
- _Accum (累加器类型): 短定点累加、长定点累加、无符号定点累加

定点数表示：
- Qm.n 格式：m 位整数（含符号）+ n 位小数
- 例如 Q1.7: 1位符号 + 7位小数 = 8位总宽度

作者：远
日期：2026-04-10
"""

from dataclasses import dataclass
from enum import Enum


class FixedPointFormat(Enum):
    """定点数格式"""

    # _Fract (小数) - 有符号
    FRACT_HALF = ("_Fract", 1, 7, True)  # 0.7 格式 (半精度小数)
    FRACT = ("_Fract", 1, 15, True)  # 1.15 格式
    LONG_FRACT = ("_Long_Fract", 1, 31, True)  # 1.31 格式

    # _Accum (累加器) - 有符号
    ACCUM_SHORT = ("_Accum", 8, 8, True)  # 8.8 格式
    ACCUM = ("_Accum", 16, 16, True)  # 16.16 格式
    LONG_ACCUM = ("_Long_Accum", 32, 32, True)  # 32.32 格式

    # 无符号版本
    FRACT_U = ("_Fract_U", 0, 8, False)  # 0.8 格式 (无符号小数)
    ACCUM_U = ("_Accum_U", 8, 8, False)  # 8.8 格式 (无符号累加)

    @property
    def name_str(self) -> str:
        """格式化名称"""
        return self.value[0]

    @property
    def int_bits(self) -> int:
        """整数位（含符号位）"""
        return self.value[1]

    @property
    def frac_bits(self) -> int:
        """小数位"""
        return self.value[2]

    @property
    def is_signed(self) -> bool:
        """是否有符号"""
        return self.value[3]

    @property
    def total_bits(self) -> int:
        """总位宽"""
        return self.int_bits + self.frac_bits

    @property
    def scale_factor(self) -> int:
        """缩放因子：2^frac_bits"""
        return 1 << self.frac_bits


@dataclass
class FixedPointType:
    """定点数类型

    属性：
    - name: 类型名称
    - total_bits: 总位宽
    - int_bits: 整数位（含符号位）
    - frac_bits: 小数位
    - is_signed: 是否有符号
    """

    name: str
    total_bits: int
    int_bits: int
    frac_bits: int
    is_signed: bool

    @classmethod
    def from_format(cls, format: FixedPointFormat) -> "FixedPointType":
        """从格式创建类型"""
        name, int_bits, frac_bits, is_signed = format.value
        total_bits = int_bits + frac_bits
        return cls(name, total_bits, int_bits, frac_bits, is_signed)

    @classmethod
    def fract_half(cls) -> "FixedPointType":
        """半精度小数 _Fract (Q0.7)"""
        return cls.from_format(FixedPointFormat.FRACT_HALF)

    @classmethod
    def fract(cls) -> "FixedPointType":
        """标准小数 _Fract (Q1.15)"""
        return cls.from_format(FixedPointFormat.FRACT)

    @classmethod
    def long_fract(cls) -> "FixedPointType":
        """长小数 _Long_Fract (Q1.31)"""
        return cls.from_format(FixedPointFormat.LONG_FRACT)

    @classmethod
    def accum_short(cls) -> "FixedPointType":
        """短累加 _Accum (Q8.8)"""
        return cls.from_format(FixedPointFormat.ACCUM_SHORT)

    @classmethod
    def accum(cls) -> "FixedPointType":
        """标准累加 _Accum (Q16.16)"""
        return cls.from_format(FixedPointFormat.ACCUM)

    @classmethod
    def long_accum(cls) -> "FixedPointType":
        """长累加 _Long_Accum (Q32.32)"""
        return cls.from_format(FixedPointFormat.LONG_ACCUM)

    @classmethod
    def fract_u(cls) -> "FixedPointType":
        """无符号小数 _Fract_U (Q0.8)"""
        return cls.from_format(FixedPointFormat.FRACT_U)

    @classmethod
    def accum_u(cls) -> "FixedPointType":
        """无符号累加 _Accum_U (Q8.8)"""
        return cls.from_format(FixedPointFormat.ACCUM_U)

    @property
    def scale_factor(self) -> int:
        """缩放因子：2^frac_bits"""
        return 1 << self.frac_bits

    @property
    def max_value(self) -> float:
        """最大值"""
        if self.is_signed:
            # 有符号：范围是 -(2^(int_bits-1)) 到 (2^(int_bits-1) - 1/2^frac_bits)
            int_max = 1 << (self.int_bits - 1)
            frac_max = 1.0 / self.scale_factor
            return int_max - frac_max
        else:
            # 无符号：范围是 0 到 (2^total_bits - 1) / 2^frac_bits
            # 例如 Q0.8: (2^8 - 1) / 2^8 = 255/256 ≈ 0.996
            return ((1 << self.total_bits) - 1) / self.scale_factor

    @property
    def min_value(self) -> float:
        """最小值"""
        if self.is_signed:
            return -(1 << (self.int_bits - 1))
        else:
            return 0.0

    @property
    def lsb(self) -> float:
        """最小精度单位 (1 LSB)"""
        return 1.0 / self.scale_factor

    @property
    def lsb_value(self) -> int:
        """1 LSB 对应的原始整数值"""
        return 1

    def __str__(self) -> str:
        return self.name


@dataclass
class FixedPointValue:
    """定点数值"""

    raw: int  # 原始整数值
    ftype: FixedPointType  # 类型

    @classmethod
    def from_float(cls, value: float, ftype: FixedPointType) -> "FixedPointValue":
        """从浮点数创建定点数

        Args:
            value: 浮点数值
            ftype: 定点数类型

        Returns:
            对应的定点数值
        """
        # 缩放
        scaled = value * ftype.scale_factor
        # 四舍五入
        scaled = round(scaled)
        # 限制范围
        max_raw = (
            (1 << ftype.total_bits) - 1
            if not ftype.is_signed
            else (1 << (ftype.total_bits - 1)) - 1
        )
        min_raw = 0 if not ftype.is_signed else -(1 << (ftype.total_bits - 1))
        scaled = max(min_raw, min(max_raw, scaled))
        return cls(scaled, ftype)

    @classmethod
    def from_int(cls, value: int, ftype: FixedPointType) -> "FixedPointValue":
        """从整数创建定点数

        Args:
            value: 整数值
            ftype: 定点数类型

        Returns:
            对应的定点数值（整数部分）
        """
        # 整数直接作为定点数的整数部分
        scaled = value << ftype.frac_bits
        return cls(scaled, ftype)

    def to_float(self) -> float:
        """转换为浮点数"""
        return self.raw / self.ftype.scale_factor

    def to_int(self) -> int:
        """转换为整数（截断小数部分）"""
        if self.ftype.is_signed:
            # 算术右移保留符号
            return self.raw >> self.ftype.frac_bits
        else:
            return self.raw >> self.ftype.frac_bits

    def __add__(self, other: "FixedPointValue") -> "FixedPointValue":
        """加法"""
        result = self._align_frac_bits(other)
        return FixedPointValue(self.raw + result.raw, self.ftype)

    def __sub__(self, other: "FixedPointValue") -> "FixedPointValue":
        """减法"""
        result = self._align_frac_bits(other)
        return FixedPointValue(self.raw - result.raw, self.ftype)

    def __mul__(self, other: "FixedPointValue") -> "FixedPointValue":
        """乘法（返回相同精度类型）

        定点乘法：两个 Qm.n 格式相乘，结果还是 Qm.n 格式
        乘积需要右移 n 位（n 是小数位数）来恢复正确的缩放
        """
        product = self.raw * other.raw
        # 乘积右移以对齐小数位（使用当前格式的小数位）
        # 两个 Qm.n 相乘后是 Q2m.2n，右移 n 位得到 Qm.n
        shift_bits = self.ftype.frac_bits
        aligned_product = product >> shift_bits
        # 限制范围
        max_raw = (
            (1 << self.ftype.total_bits) - 1
            if not self.ftype.is_signed
            else (1 << (self.ftype.total_bits - 1)) - 1
        )
        min_raw = 0 if not self.ftype.is_signed else -(1 << (self.ftype.total_bits - 1))
        aligned_product = max(min_raw, min(max_raw, aligned_product))
        return FixedPointValue(aligned_product, self.ftype)

    def __truediv__(self, other: "FixedPointValue") -> "FixedPointValue":
        """除法"""
        if other.raw == 0:
            raise ZeroDivisionError("定点数除法：除数不能为零")
        # 被除数左移以对齐小数位
        dividend = self.raw << self.ftype.frac_bits
        result = dividend // other.raw
        return FixedPointValue(result, self.ftype)

    def shift_left(self, bits: int) -> "FixedPointValue":
        """左移（乘以 2^bits）"""
        return FixedPointValue(self.raw << bits, self.ftype)

    def shift_right(self, bits: int) -> "FixedPointValue":
        """右移（除以 2^bits）"""
        if self.ftype.is_signed:
            # 算术右移
            result = self.raw >> bits
        else:
            result = self.raw >> bits
        return FixedPointValue(result, self.ftype)

    def _align_frac_bits(self, other: "FixedPointValue") -> "FixedPointValue":
        """对齐小数位"""
        if self.ftype.frac_bits == other.ftype.frac_bits:
            return other
        # 需要对齐
        diff = self.ftype.frac_bits - other.ftype.frac_bits
        if diff > 0:
            # other 需要左移
            return FixedPointValue(other.raw << diff, self.ftype)
        else:
            # self 需要左移（返回 other 格式）
            return FixedPointValue(self.raw << (-diff), other.ftype)

    def __str__(self) -> str:
        return f"{self.to_float():.6f} (0x{self.raw:08x})"

    def __repr__(self) -> str:
        return f"FixedPointValue(raw={self.raw}, ftype={self.ftype.name})"


# 预定义的定点数类型
短定点小数 = FixedPointType.fract_half()
标准定点小数 = FixedPointType.fract()
长定点小数 = FixedPointType.long_fract()
短定点累加 = FixedPointType.accum_short()
标准定点累加 = FixedPointType.accum()
长定点累加 = FixedPointType.long_accum()
无符号定点小数 = FixedPointType.fract_u()
无符号定点累加 = FixedPointType.accum_u()

__all__ = [
    "FixedPointFormat",
    "FixedPointType",
    "FixedPointValue",
    "短定点小数",
    "标准定点小数",
    "长定点小数",
    "短定点累加",
    "标准定点累加",
    "长定点累加",
    "无符号定点小数",
    "无符号定点累加",
]

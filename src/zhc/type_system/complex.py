# -*- coding: utf-8 -*-
"""
复数类型定义 - Complex Type

支持 C99 复数类型：
- 浮点复数 (float _Complex)
- 双精度复数 (double _Complex)
- 长双精度复数 (long double _Complex)

作者：远
日期：2026-04-10
"""

from dataclasses import dataclass
from enum import Enum


class ComplexElementType(Enum):
    """复数元素类型"""

    FLOAT = "浮点型"  # float
    DOUBLE = "双精度型"  # double
    LONG_DOUBLE = "长双精度型"  # long double

    @property
    def c_name(self) -> str:
        """C 语言类型名"""
        names = {
            ComplexElementType.FLOAT: "float",
            ComplexElementType.DOUBLE: "double",
            ComplexElementType.LONG_DOUBLE: "long double",
        }
        return names[self]

    @property
    def size(self) -> int:
        """类型大小（字节）"""
        sizes = {
            ComplexElementType.FLOAT: 4,
            ComplexElementType.DOUBLE: 8,
            ComplexElementType.LONG_DOUBLE: 16,
        }
        return sizes[self]

    @property
    def zhc_name(self) -> str:
        """中文类型名"""
        return self.value


@dataclass
class ComplexType:
    """复数类型"""

    element_type: ComplexElementType

    @property
    def name(self) -> str:
        """类型名称"""
        return f"{self.element_type.zhc_name}复数"

    @property
    def c_name(self) -> str:
        """C 语言类型名"""
        return f"{self.element_type.c_name} _Complex"

    @property
    def size(self) -> int:
        """复数大小（字节）"""
        return self.element_type.size * 2  # 实部 + 虚部

    @property
    def alignment(self) -> int:
        """对齐要求"""
        return self.element_type.size

    def __str__(self) -> str:
        return self.name


@dataclass
class ComplexValue:
    """复数值"""

    real: float
    imag: float
    element_type: ComplexElementType = ComplexElementType.DOUBLE

    @classmethod
    def from_complex(
        cls, z: complex, element_type: ComplexElementType = ComplexElementType.DOUBLE
    ) -> "ComplexValue":
        """从 Python complex 创建复数值"""
        return cls(z.real, z.imag, element_type)

    @classmethod
    def from_polar(
        cls,
        r: float,
        theta: float,
        element_type: ComplexElementType = ComplexElementType.DOUBLE,
    ) -> "ComplexValue":
        """从极坐标创建复数值"""
        import math

        return cls(r * math.cos(theta), r * math.sin(theta), element_type)

    def to_complex(self) -> complex:
        """转换为 Python complex"""
        return complex(self.real, self.imag)

    @property
    def magnitude(self) -> float:
        """模 |z|"""
        import math

        return math.sqrt(self.real**2 + self.imag**2)

    @property
    def phase(self) -> float:
        """幅角 arg(z)"""
        import math

        return math.atan2(self.imag, self.real)

    def conjugate(self) -> "ComplexValue":
        """共轭复数 z* = a - bi"""
        return ComplexValue(self.real, -self.imag, self.element_type)

    # 算术运算
    def __add__(self, other: "ComplexValue") -> "ComplexValue":
        """加法 (a+bi) + (c+di) = (a+c) + (b+d)i"""
        return ComplexValue(
            self.real + other.real, self.imag + other.imag, self._promote_type(other)
        )

    def __sub__(self, other: "ComplexValue") -> "ComplexValue":
        """减法 (a+bi) - (c+di) = (a-c) + (b-d)i"""
        return ComplexValue(
            self.real - other.real, self.imag - other.imag, self._promote_type(other)
        )

    def __mul__(self, other: "ComplexValue") -> "ComplexValue":
        """乘法 (a+bi)(c+di) = (ac-bd) + (ad+bc)i"""
        return ComplexValue(
            self.real * other.real - self.imag * other.imag,
            self.real * other.imag + self.imag * other.real,
            self._promote_type(other),
        )

    def __truediv__(self, other: "ComplexValue") -> "ComplexValue":
        """除法 (a+bi)/(c+di) = [(ac+bd) + (bc-ad)i] / (c²+d²)"""
        denom = other.real**2 + other.imag**2
        if denom == 0:
            raise ZeroDivisionError("复数除法：除数不能为零")
        return ComplexValue(
            (self.real * other.real + self.imag * other.imag) / denom,
            (self.imag * other.real - self.real * other.imag) / denom,
            self._promote_type(other),
        )

    # 与实数的运算
    def __radd__(self, other: float) -> "ComplexValue":
        return self + ComplexValue(other, 0.0, self.element_type)

    def __rsub__(self, other: float) -> "ComplexValue":
        return ComplexValue(other, 0.0, self.element_type) - self

    def __rmul__(self, other: float) -> "ComplexValue":
        return self * ComplexValue(other, 0.0, self.element_type)

    def __rtruediv__(self, other: float) -> "ComplexValue":
        return ComplexValue(other, 0.0, self.element_type) / self

    def __neg__(self) -> "ComplexValue":
        """取负 -z"""
        return ComplexValue(-self.real, -self.imag, self.element_type)

    def __pos__(self) -> "ComplexValue":
        """取正 +z"""
        return ComplexValue(self.real, self.imag, self.element_type)

    def _promote_type(self, other) -> ComplexElementType:
        """类型提升：选择精度更高的元素类型"""
        type_order = [
            ComplexElementType.FLOAT,
            ComplexElementType.DOUBLE,
            ComplexElementType.LONG_DOUBLE,
        ]
        self_idx = type_order.index(self.element_type)
        if isinstance(other, ComplexValue):
            other_idx = type_order.index(other.element_type)
        else:
            # 实数默认当作 DOUBLE 处理
            other_idx = type_order.index(ComplexElementType.DOUBLE)
        return type_order[max(self_idx, other_idx)]

    def __str__(self) -> str:
        if self.imag >= 0:
            return f"{self.real}+{self.imag}i"
        else:
            return f"{self.real}{self.imag}i"

    def __repr__(self) -> str:
        return f"ComplexValue({self.real}, {self.imag}, {self.element_type.zhc_name})"


# 预定义的复数类型
浮点复数型 = ComplexType(ComplexElementType.FLOAT)
双精度复数型 = ComplexType(ComplexElementType.DOUBLE)
长双精度复数型 = ComplexType(ComplexElementType.LONG_DOUBLE)

__all__ = [
    "ComplexElementType",
    "ComplexType",
    "ComplexValue",
    "浮点复数型",
    "双精度复数型",
    "长双精度复数型",
]

# -*- coding: utf-8 -*-
"""
复数数学函数 - Complex Math Functions

实现复数的数学运算函数：
- 平方根 sqrt
- 指数 exp
- 对数 log
- 幂函数 pow
- 三角函数 sin, cos, tan
- 双曲函数 sinh, cosh, tanh
- 极坐标转换

作者：远
日期：2026-04-10
"""

import math
from typing import Union
from .complex import ComplexValue, ComplexElementType


def complex_sqrt(z: ComplexValue) -> ComplexValue:
    """复数平方根 sqrt(z)

    使用极坐标计算：
    sqrt(r*e^(iθ)) = sqrt(r)*e^(iθ/2)
    """
    r = z.magnitude
    theta = z.phase
    sqrt_r = math.sqrt(r)
    return ComplexValue(
        sqrt_r * math.cos(theta / 2), sqrt_r * math.sin(theta / 2), z.element_type
    )


def complex_exp(z: ComplexValue) -> ComplexValue:
    """复数指数 e^z

    e^(a+bi) = e^a * (cos(b) + i*sin(b))
    """
    exp_real = math.exp(z.real)
    return ComplexValue(
        exp_real * math.cos(z.imag), exp_real * math.sin(z.imag), z.element_type
    )


def complex_log(z: ComplexValue) -> ComplexValue:
    """复数自然对数 ln(z)

    ln(r*e^(iθ)) = ln(r) + i*θ
    """
    if z.real == 0 and z.imag == 0:
        raise ValueError("复数对数：不能对零取对数")
    return ComplexValue(math.log(z.magnitude), z.phase, z.element_type)


def complex_log10(z: ComplexValue) -> ComplexValue:
    """复数常用对数 log10(z)"""
    ln_z = complex_log(z)
    return ComplexValue(
        ln_z.real / math.log(10), ln_z.imag / math.log(10), z.element_type
    )


def complex_pow(z: ComplexValue, n: Union[ComplexValue, float]) -> ComplexValue:
    """复数幂函数 pow(z, n)

    z^n = (r*e^(iθ))^n = r^n * e^(i*n*θ)
    """
    if isinstance(n, ComplexValue):
        # z^n = e^(n*ln(z))
        return complex_exp(complex_mul(n, complex_log(z)))
    else:
        r = z.magnitude
        theta = z.phase
        new_r = r**n
        new_theta = theta * n
        return ComplexValue(
            new_r * math.cos(new_theta),
            new_r * math.sin(new_theta),
            z.element_type,
        )


def complex_sin(z: ComplexValue) -> ComplexValue:
    """复数正弦 sin(z)

    sin(x+yi) = sin(x)*cosh(y) + i*cos(x)*sinh(y)
    """
    return ComplexValue(
        math.sin(z.real) * math.cosh(z.imag),
        math.cos(z.real) * math.sinh(z.imag),
        z.element_type,
    )


def complex_cos(z: ComplexValue) -> ComplexValue:
    """复数余弦 cos(z)

    cos(x+yi) = cos(x)*cosh(y) - i*sin(x)*sinh(y)
    """
    return ComplexValue(
        math.cos(z.real) * math.cosh(z.imag),
        -math.sin(z.real) * math.sinh(z.imag),
        z.element_type,
    )


def complex_tan(z: ComplexValue) -> ComplexValue:
    """复数正切 tan(z) = sin(z)/cos(z)"""
    cos_z = complex_cos(z)
    if cos_z.real == 0 and cos_z.imag == 0:
        raise ValueError("复数正切：结果未定义（cos(z)=0）")
    return complex_div(complex_sin(z), cos_z)


def complex_sinh(z: ComplexValue) -> ComplexValue:
    """复数双曲正弦 sinh(z)

    sinh(x+yi) = sinh(x)*cos(y) + i*cosh(x)*sin(y)
    """
    return ComplexValue(
        math.sinh(z.real) * math.cos(z.imag),
        math.cosh(z.real) * math.sin(z.imag),
        z.element_type,
    )


def complex_cosh(z: ComplexValue) -> ComplexValue:
    """复数双曲余弦 cosh(z)

    cosh(x+yi) = cosh(x)*cos(y) + i*sinh(x)*sin(y)
    """
    return ComplexValue(
        math.cosh(z.real) * math.cos(z.imag),
        math.sinh(z.real) * math.sin(z.imag),
        z.element_type,
    )


def complex_tanh(z: ComplexValue) -> ComplexValue:
    """复数双曲正切 tanh(z) = sinh(z)/cosh(z)"""
    cosh_z = complex_cosh(z)
    if cosh_z.real == 0 and cosh_z.imag == 0:
        raise ValueError("复数双曲正切：结果未定义（cosh(z)=0）")
    return complex_div(complex_sinh(z), cosh_z)


def complex_asin(z: ComplexValue) -> ComplexValue:
    """复数反正弦 asin(z) = -i*ln(sqrt(1-z²) + i*z)"""
    i = ComplexValue(0, 1, z.element_type)
    one = ComplexValue(1, 0, z.element_type)
    sqrt_term = complex_sqrt(complex_sub(complex_mul(z, z), one))
    return complex_mul(
        ComplexValue(0, -1, z.element_type),
        complex_log(complex_add(sqrt_term, complex_mul(i, z))),
    )


def complex_acos(z: ComplexValue) -> ComplexValue:
    """复数反余弦 acos(z) = -i*ln(z + i*sqrt(1-z²))"""
    i = ComplexValue(0, 1, z.element_type)
    one = ComplexValue(1, 0, z.element_type)
    sqrt_term = complex_sqrt(complex_sub(one, complex_mul(z, z)))
    return complex_mul(
        ComplexValue(0, -1, z.element_type),
        complex_log(complex_add(z, complex_mul(i, sqrt_term))),
    )


def complex_atan(z: ComplexValue) -> ComplexValue:
    """复数反正切 atan(z) = (ln(1+i*z) - ln(1-i*z)) / (2*i)"""
    i = ComplexValue(0, 1, z.element_type)
    one = ComplexValue(1, 0, z.element_type)
    two_i = ComplexValue(0, 2, z.element_type)
    ln1 = complex_log(complex_add(one, complex_mul(i, z)))
    ln2 = complex_log(complex_sub(one, complex_mul(i, z)))
    return complex_div(complex_sub(ln1, ln2), two_i)


def complex_asinh(z: ComplexValue) -> ComplexValue:
    """复数反双曲正弦 asinh(z) = ln(z + sqrt(1+z²))"""
    one = ComplexValue(1, 0, z.element_type)
    sqrt_term = complex_sqrt(complex_add(complex_mul(z, z), one))
    return complex_log(complex_add(z, sqrt_term))


def complex_acosh(z: ComplexValue) -> ComplexValue:
    """复数反双曲余弦 acosh(z) = ln(z + sqrt(z+1)*sqrt(z-1))"""
    one = ComplexValue(1, 0, z.element_type)
    sqrt_z_plus_1 = complex_sqrt(complex_add(z, one))
    sqrt_z_minus_1 = complex_sqrt(complex_sub(z, one))
    return complex_log(complex_add(z, complex_mul(sqrt_z_plus_1, sqrt_z_minus_1)))


def complex_atanh(z: ComplexValue) -> ComplexValue:
    """复数反双曲正切 atanh(z) = (ln(1+z) - ln(1-z)) / 2"""
    one = ComplexValue(1, 0, z.element_type)
    two = ComplexValue(2, 0, z.element_type)
    ln1 = complex_log(complex_add(one, z))
    ln2 = complex_log(complex_sub(one, z))
    return complex_div(complex_sub(ln1, ln2), two)


# 辅助函数：复数加减乘除
def complex_add(a: ComplexValue, b: ComplexValue) -> ComplexValue:
    """复数加法"""
    return a + b


def complex_sub(a: ComplexValue, b: ComplexValue) -> ComplexValue:
    """复数减法"""
    return a - b


def complex_mul(a: ComplexValue, b: ComplexValue) -> ComplexValue:
    """复数乘法"""
    return a * b


def complex_div(a: ComplexValue, b: ComplexValue) -> ComplexValue:
    """复数除法"""
    return a / b


def complex_neg(z: ComplexValue) -> ComplexValue:
    """复数取负"""
    return -z


def complex_conj(z: ComplexValue) -> ComplexValue:
    """复数共轭"""
    return z.conjugate()


def complex_abs(z: ComplexValue) -> float:
    """复数模（绝对值）"""
    return z.magnitude


def complex_arg(z: ComplexValue) -> float:
    """复数幅角"""
    return z.phase


def complex_polar(
    r: float, theta: float, element_type: ComplexElementType = ComplexElementType.DOUBLE
) -> ComplexValue:
    """从极坐标创建复数"""
    return ComplexValue.from_polar(r, theta, element_type)


__all__ = [
    # 基本运算
    "complex_add",
    "complex_sub",
    "complex_mul",
    "complex_div",
    "complex_neg",
    "complex_conj",
    "complex_abs",
    "complex_arg",
    "complex_polar",
    # 数学函数
    "complex_sqrt",
    "complex_exp",
    "complex_log",
    "complex_log10",
    "complex_pow",
    "complex_sin",
    "complex_cos",
    "complex_tan",
    "complex_sinh",
    "complex_cosh",
    "complex_tanh",
    "complex_asin",
    "complex_acos",
    "complex_atan",
    "complex_asinh",
    "complex_acosh",
    "complex_atanh",
]

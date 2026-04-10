# -*- coding: utf-8 -*-
"""
复数类型单元测试

测试复数类型的各个方面：
- 类型创建
- 算术运算
- 数学函数
- 解析器支持

作者：远
日期：2026-04-10
"""

import pytest
import math

from zhc.type_system import (
    ComplexValue,
    ComplexElementType,
    浮点复数型,
    双精度复数型,
    长双精度复数型,
)
from zhc.type_system.complex_math import (
    complex_sqrt,
    complex_exp,
    complex_log,
    complex_sin,
    complex_cos,
    complex_add,
    complex_sub,
    complex_mul,
    complex_div,
    complex_conj,
    complex_abs,
    complex_arg,
)


class TestComplexValue:
    """测试复数值"""

    def test_create_complex_value(self):
        """测试创建复数值"""
        z = ComplexValue(3.0, 4.0)
        assert z.real == 3.0
        assert z.imag == 4.0
        assert z.element_type == ComplexElementType.DOUBLE

    def test_complex_to_polar(self):
        """测试转换为极坐标"""
        z = ComplexValue(3.0, 4.0)
        assert abs(z.magnitude - 5.0) < 1e-10
        assert abs(z.phase - math.atan2(4.0, 3.0)) < 1e-10

    def test_complex_conjugate(self):
        """测试共轭复数"""
        z = ComplexValue(3.0, 4.0)
        conj = z.conjugate()
        assert conj.real == 3.0
        assert conj.imag == -4.0

    def test_complex_add(self):
        """测试复数加法"""
        a = ComplexValue(1.0, 2.0)
        b = ComplexValue(3.0, 4.0)
        c = a + b
        assert c.real == 4.0
        assert c.imag == 6.0

    def test_complex_sub(self):
        """测试复数减法"""
        a = ComplexValue(7.0, 5.0)
        b = ComplexValue(3.0, 4.0)
        c = a - b
        assert c.real == 4.0
        assert c.imag == 1.0

    def test_complex_mul(self):
        """测试复数乘法 (1+2i)(3+4i) = -5+10i"""
        a = ComplexValue(1.0, 2.0)
        b = ComplexValue(3.0, 4.0)
        c = a * b
        assert c.real == -5.0
        assert c.imag == 10.0

    def test_complex_div(self):
        """测试复数除法 (1+2i)/(3+4i)"""
        a = ComplexValue(1.0, 2.0)
        b = ComplexValue(3.0, 4.0)
        c = a / b
        # (1+2i)/(3+4i) = (1*3+2*4 + (2*3-1*4)i) / 25 = 11/25 + 2/25i
        assert abs(c.real - 11.0 / 25.0) < 1e-10
        assert abs(c.imag - 2.0 / 25.0) < 1e-10

    def test_complex_neg(self):
        """测试复数取负"""
        z = ComplexValue(3.0, 4.0)
        neg = -z
        assert neg.real == -3.0
        assert neg.imag == -4.0

    def test_real_number_operations(self):
        """测试与实数的运算"""
        z = ComplexValue(3.0, 4.0)
        # 复数 + 实数
        result = z + 2.0
        assert result.real == 5.0
        assert result.imag == 4.0
        # 复数 * 实数
        result = z * 2.0
        assert result.real == 6.0
        assert result.imag == 8.0


class TestComplexType:
    """测试复数类型"""

    def test_float_complex_type(self):
        """测试浮点复数类型"""
        zhc_type = 浮点复数型
        assert zhc_type.element_type == ComplexElementType.FLOAT
        assert zhc_type.size == 8  # 2 * 4 bytes
        assert "浮点" in zhc_type.name

    def test_double_complex_type(self):
        """测试双精度复数类型"""
        zhc_type = 双精度复数型
        assert zhc_type.element_type == ComplexElementType.DOUBLE
        assert zhc_type.size == 16  # 2 * 8 bytes
        assert "双精度" in zhc_type.name

    def test_long_double_complex_type(self):
        """测试长双精度复数类型"""
        zhc_type = 长双精度复数型
        assert zhc_type.element_type == ComplexElementType.LONG_DOUBLE
        assert zhc_type.size == 32  # 2 * 16 bytes


class TestComplexMath:
    """测试复数数学函数"""

    def test_complex_sqrt(self):
        """测试复数平方根 sqrt(1+i)

        sqrt(1+i) 的极坐标形式:
        - r = sqrt(1^2 + 1^2) = sqrt(2)
        - theta = atan2(1, 1) = pi/4
        - sqrt(z) = sqrt(r) * e^(i*theta/2) = sqrt(sqrt(2)) * (cos(pi/8) + i*sin(pi/8))
        """
        z = ComplexValue(1.0, 1.0)
        sqrt_z = complex_sqrt(z)
        # sqrt(r) = sqrt(sqrt(2)) = 2^(1/4) ≈ 1.1892
        r = math.sqrt(2)
        sqrt_r = math.sqrt(r)
        # theta/2 = pi/8 ≈ 0.3927
        theta_half = math.pi / 8
        expected_real = sqrt_r * math.cos(theta_half)
        expected_imag = sqrt_r * math.sin(theta_half)
        assert abs(sqrt_z.real - expected_real) < 1e-5
        assert abs(sqrt_z.imag - expected_imag) < 1e-5

    def test_complex_exp(self):
        """测试复数指数 e^(i*pi) = -1"""
        z = ComplexValue(0.0, math.pi)
        exp_z = complex_exp(z)
        assert abs(exp_z.real - (-1.0)) < 1e-10
        assert abs(exp_z.imag) < 1e-10

    def test_complex_log(self):
        """测试复数对数 log(-1) = i*pi"""
        z = ComplexValue(-1.0, 0.0)
        log_z = complex_log(z)
        assert abs(log_z.real - 0.0) < 1e-10
        assert abs(log_z.imag - math.pi) < 1e-10

    def test_complex_sin(self):
        """测试复数正弦 sin(i) = i*sinh(1)"""
        z = ComplexValue(0.0, 1.0)
        sin_z = complex_sin(z)
        assert abs(sin_z.real) < 1e-10
        assert abs(sin_z.imag - math.sinh(1.0)) < 1e-10

    def test_complex_cos(self):
        """测试复数余弦 cos(i) = cosh(1)"""
        z = ComplexValue(0.0, 1.0)
        cos_z = complex_cos(z)
        assert abs(cos_z.real - math.cosh(1.0)) < 1e-10
        assert abs(cos_z.imag) < 1e-10

    def test_complex_add(self):
        """测试 complex_add 函数"""
        a = ComplexValue(1.0, 2.0)
        b = ComplexValue(3.0, 4.0)
        c = complex_add(a, b)
        assert c.real == 4.0
        assert c.imag == 6.0

    def test_complex_sub(self):
        """测试 complex_sub 函数"""
        a = ComplexValue(7.0, 5.0)
        b = ComplexValue(3.0, 4.0)
        c = complex_sub(a, b)
        assert c.real == 4.0
        assert c.imag == 1.0

    def test_complex_mul(self):
        """测试 complex_mul 函数"""
        a = ComplexValue(1.0, 2.0)
        b = ComplexValue(3.0, 4.0)
        c = complex_mul(a, b)
        assert c.real == -5.0
        assert c.imag == 10.0

    def test_complex_div(self):
        """测试 complex_div 函数"""
        a = ComplexValue(1.0, 2.0)
        b = ComplexValue(3.0, 4.0)
        c = complex_div(a, b)
        assert abs(c.real - 11.0 / 25.0) < 1e-10
        assert abs(c.imag - 2.0 / 25.0) < 1e-10

    def test_complex_conj(self):
        """测试 complex_conj 函数"""
        z = ComplexValue(3.0, 4.0)
        conj = complex_conj(z)
        assert conj.real == 3.0
        assert conj.imag == -4.0

    def test_complex_abs(self):
        """测试 complex_abs 函数"""
        z = ComplexValue(3.0, 4.0)
        assert abs(complex_abs(z) - 5.0) < 1e-10

    def test_complex_arg(self):
        """测试 complex_arg 函数"""
        z = ComplexValue(1.0, 1.0)
        expected = math.pi / 4  # 45度
        assert abs(complex_arg(z) - expected) < 1e-10


class TestComplexParser:
    """测试复数类型解析"""

    def test_complex_type_parsing(self):
        """测试复数类型解析"""
        from zhc.parser.lexer import Lexer, TokenType
        from zhc.parser.parser import Parser

        code = "双精度复数型 z;"
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        # 验证 lexer 正确识别复数关键字
        token_types = [t.type for t in tokens]
        assert TokenType.COMPLEX in token_types

        # 验证 parser 能够解析
        parser = Parser(tokens)
        _ast = parser.parse()
        assert len(parser.errors) == 0

    def test_complex_literal_parsing(self):
        """测试复数字面量解析"""
        from zhc.parser.lexer import Lexer
        from zhc.parser.parser import Parser

        # 测试虚数字面量
        code = "双精度复数型 z = 4.0i;"
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        # 验证 '4.0i' 被识别为 FLOAT_LITERAL
        float_tokens = [t for t in tokens if t.type.name == "FLOAT_LITERAL"]
        assert len(float_tokens) > 0

        parser = Parser(tokens)
        _ast = parser.parse()
        assert len(parser.errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

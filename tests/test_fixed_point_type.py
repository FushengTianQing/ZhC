# -*- coding: utf-8 -*-
"""
定点数类型单元测试

测试定点数类型的各个方面：
- 类型创建
- 格式定义
- 算术运算
- 转换

作者：远
日期：2026-04-10
"""

import pytest

from zhc.type_system import (
    FixedPointValue,
    FixedPointType,
    短定点小数,
    标准定点小数,
    长定点小数,
    短定点累加,
    标准定点累加,
    长定点累加,
    无符号定点小数,
    无符号定点累加,
)


class TestFixedPointFormat:
    """测试定点数格式"""

    def test_fract_half_format(self):
        """测试半精度小数格式 Q0.7"""
        fp = FixedPointType.fract_half()
        assert fp.total_bits == 8
        assert fp.frac_bits == 7
        assert fp.int_bits == 1
        assert fp.is_signed is True
        assert fp.scale_factor == 128

    def test_fract_format(self):
        """测试标准小数格式 Q1.15"""
        fp = FixedPointType.fract()
        assert fp.total_bits == 16
        assert fp.frac_bits == 15
        assert fp.int_bits == 1
        assert fp.is_signed is True

    def test_long_fract_format(self):
        """测试长小数格式 Q1.31"""
        fp = FixedPointType.long_fract()
        assert fp.total_bits == 32
        assert fp.frac_bits == 31

    def test_accum_formats(self):
        """测试累加器格式"""
        # 短累加 Q8.8
        acc_short = FixedPointType.accum_short()
        assert acc_short.total_bits == 16
        assert acc_short.frac_bits == 8
        assert acc_short.int_bits == 8

        # 标准累加 Q16.16
        acc = FixedPointType.accum()
        assert acc.total_bits == 32
        assert acc.frac_bits == 16
        assert acc.int_bits == 16

        # 长累加 Q32.32
        long_acc = FixedPointType.long_accum()
        assert long_acc.total_bits == 64
        assert long_acc.frac_bits == 32
        assert long_acc.int_bits == 32


class TestFixedPointValue:
    """测试定点数值"""

    def test_from_float(self):
        """测试从浮点数创建定点数"""
        fp = FixedPointType.fract()  # Q1.15
        fv = FixedPointValue.from_float(0.5, fp)

        # 0.5 * 32768 = 16384
        assert fv.raw == 16384
        assert fv.to_float() == 0.5

    def test_from_int(self):
        """测试从整数创建定点数"""
        fp = FixedPointType.fract()  # Q1.15
        fv = FixedPointValue.from_int(3, fp)

        # 3 << 15 = 98304
        assert fv.raw == 98304
        assert fv.to_int() == 3

    def test_fract_addition(self):
        """测试定点数加法 0.25 + 0.5 = 0.75"""
        fp = FixedPointType.fract()
        a = FixedPointValue.from_float(0.25, fp)
        b = FixedPointValue.from_float(0.5, fp)
        c = a + b

        assert abs(c.to_float() - 0.75) < 0.001

    def test_fract_subtraction(self):
        """测试定点数减法 0.75 - 0.25 = 0.5"""
        fp = FixedPointType.fract()
        a = FixedPointValue.from_float(0.75, fp)
        b = FixedPointValue.from_float(0.25, fp)
        c = a - b

        assert abs(c.to_float() - 0.5) < 0.001

    def test_fract_multiplication(self):
        """测试定点数乘法 0.5 * 0.5 = 0.25"""
        fp = FixedPointType.fract()
        a = FixedPointValue.from_float(0.5, fp)
        b = FixedPointValue.from_float(0.5, fp)
        c = a * b

        # 由于定点数精度限制，接受一定误差
        assert abs(c.to_float() - 0.25) < 0.01

    def test_fract_division(self):
        """测试定点数除法 0.5 / 0.25 = 2"""
        fp = FixedPointType.fract()
        a = FixedPointValue.from_float(0.5, fp)
        b = FixedPointValue.from_float(0.25, fp)
        c = a / b

        assert abs(c.to_float() - 2.0) < 0.1

    def test_shift_left(self):
        """测试左移（乘以 2^n）"""
        fp = FixedPointType.fract()
        fv = FixedPointValue.from_float(0.5, fp)
        shifted = fv.shift_left(2)

        # 0.5 * 4 = 2.0
        assert abs(shifted.to_float() - 2.0) < 0.001

    def test_shift_right(self):
        """测试右移（除以 2^n）

        Q1.15 格式范围是 -1.0 到 ~0.9999，所以用 0.5 测试
        """
        fp = FixedPointType.fract()
        fv = FixedPointValue.from_float(0.5, fp)
        shifted = fv.shift_right(1)

        # 0.5 / 2 = 0.25
        assert abs(shifted.to_float() - 0.25) < 0.01


class TestFixedPointRanges:
    """测试定点数范围"""

    def test_fract_range(self):
        """测试小数类型范围"""
        fp = FixedPointType.fract()  # Q1.15
        assert fp.min_value == -1.0
        assert fp.max_value < 1.0
        assert fp.max_value > 0.99

    def test_accum_range(self):
        """测试累加器类型范围"""
        fp = FixedPointType.accum()  # Q16.16
        assert fp.min_value == -32768.0
        assert fp.max_value > 32767.0

    def test_unsigned_range(self):
        """测试无符号类型范围"""
        fp = FixedPointType.fract_u()  # Q0.8
        assert fp.min_value == 0.0
        # Q0.8: 0 位整数 + 8 位小数 = 8 位无符号
        # 最大值 = (2^8 - 1) / 2^8 = 255/256 ≈ 0.99609375
        assert fp.max_value > 0.99
        assert fp.max_value < 1.0


class TestPredefinedTypes:
    """测试预定义类型"""

    def test_short_fract(self):
        """测试短定点小数"""
        assert 短定点小数.name == "_Fract"
        assert 短定点小数.total_bits == 8

    def test_standard_fract(self):
        """测试标准定点小数"""
        assert 标准定点小数.name == "_Fract"
        assert 标准定点小数.total_bits == 16

    def test_long_fract(self):
        """测试长定点小数"""
        assert 长定点小数.total_bits == 32

    def test_short_accum(self):
        """测试短定点累加"""
        assert 短定点累加.total_bits == 16

    def test_standard_accum(self):
        """测试标准定点累加"""
        assert 标准定点累加.total_bits == 32

    def test_long_accum(self):
        """测试长定点累加"""
        assert 长定点累加.total_bits == 64

    def test_unsigned_fract(self):
        """测试无符号定点小数"""
        assert 无符号定点小数.is_signed is False
        assert 无符号定点小数.total_bits == 8

    def test_unsigned_accum(self):
        """测试无符号定点累加"""
        assert 无符号定点累加.is_signed is False
        assert 无符号定点累加.total_bits == 16


class TestFixedPointParser:
    """测试定点数类型解析"""

    def test_fixed_point_type_parsing(self):
        """测试定点数类型解析"""
        from zhc.parser.lexer import Lexer, TokenType
        from zhc.parser.parser import Parser

        code = "定点小数 x;"
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        # 验证 lexer 正确识别定点数关键字
        token_types = [t.type for t in tokens]
        assert TokenType.FIXED_POINT in token_types

        # 验证 parser 能够解析
        parser = Parser(tokens)
        _ast = parser.parse()
        assert len(parser.errors) == 0

    def test_accum_type_parsing(self):
        """测试累加器类型解析"""
        from zhc.parser.lexer import Lexer
        from zhc.parser.parser import Parser

        code = "定点累加 y;"
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        parser = Parser(tokens)
        _ast = parser.parse()
        assert len(parser.errors) == 0

    def test_short_accum_parsing(self):
        """测试短定点累加类型解析"""
        from zhc.parser.lexer import Lexer
        from zhc.parser.parser import Parser

        code = "短定点累加 z;"
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        parser = Parser(tokens)
        _ast = parser.parse()
        assert len(parser.errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

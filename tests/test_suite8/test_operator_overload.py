#!/usr/bin/env python3
"""
Day 17: 运算符重载测试
"""

import sys
import os

from zhpp.converter.operator import (
    OperatorType, OperatorOverloadInfo, OperatorOverloadParser,
    OperatorOverloadGenerator, CHINESE_OPERATOR_MAP, OPERATOR_TO_C_FUNC
)


def test_operator_type_enum():
    """测试1: 运算符类型枚举"""
    assert OperatorType.ADD.value == "+"
    assert OperatorType.EQ.value == "=="
    assert OperatorType.NOT.value == "!"
    print('✓ 测试1: 运算符类型枚举')


def test_chinese_operator_map():
    """测试2: 中文运算符映射"""
    assert CHINESE_OPERATOR_MAP["加"] == OperatorType.ADD
    assert CHINESE_OPERATOR_MAP["乘"] == OperatorType.MUL
    assert CHINESE_OPERATOR_MAP["等于"] == OperatorType.EQ
    assert CHINESE_OPERATOR_MAP["非"] == OperatorType.NOT
    print('✓ 测试2: 中文运算符映射')


def test_operator_to_c_func():
    """测试3: 运算符到C函数映射"""
    assert OPERATOR_TO_C_FUNC[OperatorType.ADD] == ("add", "obj1 + obj2", True)
    assert OPERATOR_TO_C_FUNC[OperatorType.NEG] == ("neg", "-obj", False)
    assert OPERATOR_TO_C_FUNC[OperatorType.EQ] == ("equals", "obj1 == obj2", True)
    print('✓ 测试3: 运算符到C函数映射')


def test_operator_overload_info():
    """测试4: 运算符重载信息"""
    info = OperatorOverloadInfo('向量', OperatorType.ADD, 'add', '向量')
    assert info.class_name == '向量'
    assert info.operator == OperatorType.ADD
    assert info.get_c_function_name() == '向量_operator_add'
    print('✓ 测试4: 运算符重载信息')


def test_operator_overload_parser():
    """测试5: 运算符重载解析器"""
    parser = OperatorOverloadParser()
    parser.set_current_class('矩阵')

    # 解析加法运算符
    line = "操作符 加(矩阵) -> 矩阵"
    info = parser.parse_operator_declaration(line, 1)
    assert info is not None
    assert info.operator == OperatorType.ADD

    # 解析相等运算符
    line2 = "操作符 等于(矩阵) -> 整数型"
    info2 = parser.parse_operator_declaration(line2, 2)
    assert info2 is not None
    assert info2.operator == OperatorType.EQ

    overloads = parser.get_class_overloads('矩阵')
    assert len(overloads) == 2
    print('✓ 测试5: 运算符重载解析器')


def test_operator_overload_generator():
    """测试6: 运算符重载生成器"""
    generator = OperatorOverloadGenerator()

    # 注册运算符重载
    generator.register_overload('复数', OperatorType.ADD, '复数')
    generator.register_overload('复数', OperatorType.SUB, '复数')
    generator.register_overload('复数', OperatorType.MUL, '复数')

    header = generator.generate_header('复数')
    assert '复数' in header
    assert 'operator_add' in header
    assert 'operator_sub' in header
    assert 'operator_mul' in header
    print('✓ 测试6: 运算符重载生成器')


def test_binary_vs_unary():
    """测试7: 二元vs一元运算符"""
    generator = OperatorOverloadGenerator()
    generator.register_overload('整数', OperatorType.NEG)  # 一元
    generator.register_overload('整数', OperatorType.NOT)  # 一元
    generator.register_overload('整数', OperatorType.ADD)  # 二元

    header = generator.generate_header('整数')
    assert 'operator_neg' in header
    assert 'operator_add' in header
    print('✓ 测试7: 二元vs一元运算符')


def test_multiple_classes():
    """测试8: 多类运算符重载"""
    generator = OperatorOverloadGenerator()

    generator.register_overload('向量', OperatorType.ADD, '向量')
    generator.register_overload('向量', OperatorType.MUL, 'double')
    generator.register_overload('矩阵', OperatorType.ADD, '矩阵')
    generator.register_overload('矩阵', OperatorType.MUL, '矩阵')

    vec_header = generator.generate_header('向量')
    mat_header = generator.generate_header('矩阵')

    assert '向量_operator_add' in vec_header
    assert '向量_operator_mul' in vec_header
    assert '矩阵_operator_add' in mat_header
    assert '矩阵_operator_mul' in mat_header
    print('✓ 测试8: 多类运算符重载')


if __name__ == '__main__':
    print("=" * 60)
    print("Day 17 运算符重载测试")
    print("=" * 60)

    test_operator_type_enum()
    test_chinese_operator_map()
    test_operator_to_c_func()
    test_operator_overload_info()
    test_operator_overload_parser()
    test_operator_overload_generator()
    test_binary_vs_unary()
    test_multiple_classes()

    print("=" * 60)
    print("测试: 8, 通过: 8")
    print("🎉 全部通过")
    print("=" * 60)
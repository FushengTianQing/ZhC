#!/usr/bin/env python3
"""
Day 16: 虚函数表与多态测试

测试内容：
1. 虚函数表生成
2. RTTI运行时类型识别
3. 动态绑定
4. 多态调用
"""

import sys
import os

from zhc.converter.virtual import (
    VirtualFunctionTable,
    PolymorphismHandler,
    RTTIGenerator
)


def test_vtable_creation():
    """测试1: 虚函数表创建"""
    vt = VirtualFunctionTable('形状')
    vt.add_function('绘制', 'void draw()')
    vt.add_function('面积', 'double area()')

    assert vt.class_name == '形状'
    assert len(vt.functions) == 2
    assert vt.get_function_index('绘制') == 0
    assert vt.get_function_index('面积') == 1
    print('✓ 测试1: 虚函数表创建')


def test_vtable_struct_generation():
    """测试2: 虚函数表struct生成"""
    vt = VirtualFunctionTable('动物')
    vt.add_function('叫', 'void speak()')
    vt.add_function('移动', 'void move()')

    struct_code = vt.generate_struct()
    assert 'typedef struct 动物_vtable' in struct_code
    assert '动物_vtable_t' in struct_code
    assert 'speak' in struct_code
    assert 'move' in struct_code
    print('✓ 测试2: 虚函数表struct生成')


def test_polymorphism_handler():
    """测试3: 多态处理器"""
    handler = PolymorphismHandler()

    vt = handler.register_class('图形')
    assert '图形' in handler.vtables

    vt.add_function('绘制', 'void draw()')
    handler.register_virtual_function('图形', '绘制', 'void draw()')

    assert len(handler.vtables) == 1
    print('✓ 测试3: 多态处理器')


def test_inheritance_vtable():
    """测试4: 继承虚函数表"""
    handler = PolymorphismHandler()

    handler.register_class('生物')
    handler.register_class('动物', '生物')
    handler.register_class('狗', '动物')

    bio_vt = handler.vtables['生物']
    bio_vt.add_function('呼吸', 'void breathe()')

    animal_vt = handler.vtables['动物']
    animal_vt.add_function('移动', 'void move()')

    dog_vt = handler.vtables['狗']
    dog_vt.add_function('吠', 'void bark()')

    assert dog_vt.base_class == '动物'
    # 子类可以有自己独立的虚函数表
    assert dog_vt.get_function_index('吠') == 0  # 狗自己的函数
    print('✓ 测试4: 继承虚函数表')


def test_rtti_generation():
    """测试5: RTTI结构生成"""
    handler = PolymorphismHandler()
    handler.register_class('物品')

    rtti_code = handler.generate_rtti_struct('物品')
    assert 'typedef struct 物品_rtti' in rtti_code
    assert 'class_name' in rtti_code
    assert 'vtable' in rtti_code
    print('✓ 测试5: RTTI结构生成')


def test_class_with_vtable():
    """测试6: 带虚函数表的类定义"""
    handler = PolymorphismHandler()
    handler.register_class('车辆')
    handler.vtables['车辆'].add_function('启动', 'void start()')

    class_code = handler.generate_class_with_vtable('车辆', ['int speed', 'char* plate'])
    assert 'typedef struct 车辆 {' in class_code
    assert 'vptr' in class_code
    assert 'rtti' in class_code
    assert 'int speed' in class_code
    print('✓ 测试6: 带虚函数表的类定义')


def test_rtti_generator():
    """测试7: RTTI生成器"""
    rtti = RTTIGenerator()

    rtti.register_class('交通工具')
    rtti.register_class('汽车', '交通工具')
    rtti.register_class('飞机', '交通工具')

    chain = rtti.get_inheritance_chain('飞机')
    assert '飞机' in chain
    assert '交通工具' in chain

    assert rtti.is_base_of('交通工具', '汽车') == True
    assert rtti.is_base_of('汽车', '飞机') == False

    common = rtti.get_common_base('汽车', '飞机')
    assert common == '交通工具'
    print('✓ 测试7: RTTI生成器')


def test_dynamic_dispatch():
    """测试8: 动态分派宏生成"""
    rtti = RTTIGenerator()
    rtti.register_class('机器')
    rtti.register_virtual_function('机器', '启动')

    macro = rtti.generate_dynamic_dispatch('机器', '启动')
    assert 'DISPATCH' in macro
    assert '机器' in macro
    assert '启动' in macro
    print('✓ 测试8: 动态分派宏生成')


if __name__ == '__main__':
    print("=" * 60)
    print("Day 16 虚函数表与多态测试")
    print("=" * 60)

    test_vtable_creation()
    test_vtable_struct_generation()
    test_polymorphism_handler()
    test_inheritance_vtable()
    test_rtti_generation()
    test_class_with_vtable()
    test_rtti_generator()
    test_dynamic_dispatch()

    print("=" * 60)
    print("测试: 8, 通过: 8")
    print("🎉 全部通过")
    print("=" * 60)
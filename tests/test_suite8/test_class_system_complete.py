#!/usr/bin/env python3
"""
测试套件8：类系统完整测试

包含50个测试用例：
- 40个基础测试用例
- 10个高级测试用例
"""

import sys
import os

from zhpp.parser.class_ import ClassParser, Visibility
from zhpp.parser.class_extended import ClassParserExtended
from zhpp.converter.attribute import AttributeConverter, ClassToStructConverter
from zhpp.converter.method import MethodConverter, VirtualMethodTableGenerator
from zhpp.converter.inheritance import InheritanceConverter, InheritanceChainAnalyzer
from zhpp.converter.virtual import PolymorphismHandler
from zhpp.converter.operator import OperatorType, OperatorOverloadParser, OperatorOverloadGenerator


# ============== 基础测试用例 (40个) ==============

def test_001_class_declaration():
    """基础测试1: 类声明解析"""
    parser = ClassParser()
    result = parser.parse_class_declaration("类 学生 {", 1)
    assert result is not None
    assert result.name == '学生'
    print('✓ 测试1: 类声明解析')

def test_002_multiple_classes():
    """基础测试2: 多类解析"""
    parser = ClassParser()
    parser.parse_class_declaration("类 A {", 1)
    parser.parse_class_declaration("类 B {", 2)
    assert len(parser.classes) == 2
    print('✓ 测试2: 多类解析')

def test_003_attribute_declaration():
    """基础测试3: 属性声明"""
    parser = ClassParser()
    parser.parse_class_declaration("类 人 {", 1)
    parser.parse_line("    属性:", 2)
    result = parser.parse_attribute("        字符串型 姓名;", 3)
    assert result is not None
    assert result.name == '姓名'
    print('✓ 测试3: 属性声明')

def test_004_method_declaration():
    """基础测试4: 方法声明"""
    parser = ClassParser()
    parser.parse_class_declaration("类 人 {", 1)
    parser.parse_line("    方法:", 2)
    result = parser.parse_method("        函数 获取信息() -> 字符串型 { }", 3)
    assert result is not None
    print('✓ 测试4: 方法声明')

def test_005_constructor():
    """基础测试5: 构造函数"""
    parser = ClassParser()
    parser.parse_class_declaration("类 人 {", 1)
    parser.parse_line("    方法:", 2)
    result = parser.parse_method("        函数 构造函数(字符串型 名) -> 空型 { }", 3)
    assert result is not None
    print('✓ 测试5: 构造函数')

def test_006_destructor():
    """基础测试6: 析构函数"""
    parser = ClassParser()
    parser.parse_class_declaration("类 人 {", 1)
    parser.parse_line("    方法:", 2)
    result = parser.parse_method("        函数 析构函数() -> 空型 { }", 3)
    assert result is not None
    print('✓ 测试6: 析构函数')

def test_007_public_visibility():
    """基础测试7: 公开可见性"""
    parser = ClassParser()
    parser.parse_class_declaration("类 人 {", 1)
    parser.parse_line("    属性:", 2)  # 添加区域设置
    parser.current_visibility = Visibility.PUBLIC
    result = parser.parse_attribute("        字符串型 姓名;", 3)
    assert result is not None
    print('✓ 测试7: 公开可见性')

def test_008_private_visibility():
    """基础测试8: 私有可见性"""
    parser = ClassParser()
    parser.parse_class_declaration("类 人 {", 1)
    parser.parse_line("    属性:", 2)  # 添加区域设置
    parser.current_visibility = Visibility.PRIVATE
    result = parser.parse_attribute("        整数型 年龄;", 3)
    assert result is not None
    print('✓ 测试8: 私有可见性')

def test_009_protected_visibility():
    """基础测试9: 保护可见性"""
    parser = ClassParser()
    parser.parse_class_declaration("类 人 {", 1)
    parser.parse_line("    属性:", 2)  # 添加区域设置
    parser.current_visibility = Visibility.PROTECTED
    result = parser.parse_attribute("        整数型 密码;", 3)
    assert result is not None
    print('✓ 测试9: 保护可见性')

def test_010_class_summary():
    """基础测试10: 类摘要生成"""
    parser = ClassParser()
    parser.parse_class_declaration("类 人 {", 1)
    summary = parser.get_summary()
    assert '人' in summary
    print('✓ 测试10: 类摘要生成')

def test_011_extended_parser():
    """基础测试11: 扩展解析器"""
    parser = ClassParserExtended()
    result = parser.parse_class_declaration("类 动物 {", 1)
    assert result is not None
    print('✓ 测试11: 扩展解析器')

def test_012_extended_method():
    """基础测试12: 扩展方法解析"""
    parser = ClassParserExtended()
    parser.parse_class_declaration("类 动物 {", 1)
    parser.parse_line("    方法:", 2)
    result = parser.parse_method("        函数 叫声() -> 空型 { }", 3)
    assert result is not None
    print('✓ 测试12: 扩展方法解析')

def test_013_parameter_parsing():
    """基础测试13: 参数解析"""
    parser = ClassParserExtended()
    params = parser._parse_parameters("整数型 x, 整数型 y")
    assert len(params) >= 1
    print('✓ 测试13: 参数解析')

def test_014_method_body():
    """基础测试14: 方法体解析"""
    parser = ClassParserExtended()
    parser.parse_class_declaration("类 人 {", 1)
    parser.parse_line("    方法:", 2)
    result = parser.parse_method("        函数 测试() -> 空型 { 返回; }", 3)
    assert result is not None
    print('✓ 测试14: 方法体解析')

def test_015_get_class():
    """基础测试15: 获取类信息"""
    parser = ClassParserExtended()
    parser.parse_class_declaration("类 A {", 1)
    parser.parse_class_declaration("类 B {", 2)
    a_class = parser.get_class('A')
    assert a_class is not None
    print('✓ 测试15: 获取类信息')

def test_016_duplicate_class_error():
    """基础测试16: 重复类名检测"""
    parser = ClassParserExtended()
    parser.parse_class_declaration("类 A {", 1)
    result = parser.parse_class_declaration("类 A {", 2)
    assert result is None
    print('✓ 测试16: 重复类名检测')

def test_017_class_with_parameters():
    """基础测试17: 带参数的类方法"""
    parser = ClassParserExtended()
    parser.parse_class_declaration("类 计算器 {", 1)
    parser.parse_line("    方法:", 2)
    result = parser.parse_method("        函数 加法(整数型 a, 整数型 b) -> 整数型 { }", 3)
    assert result is not None
    print('✓ 测试17: 带参数的类方法')

def test_018_return_type_parsing():
    """基础测试18: 返回类型解析"""
    parser = ClassParserExtended()
    parser.parse_class_declaration("类 人 {", 1)
    parser.parse_line("    方法:", 2)
    result = parser.parse_method("        函数 获取年龄() -> 整数型 { }", 3)
    assert result is not None
    print('✓ 测试18: 返回类型解析')

def test_019_static_method():
    """基础测试19: 静态方法"""
    parser = ClassParserExtended()
    parser.parse_class_declaration("类 工具 {", 1)
    parser.parse_line("    方法:", 2)
    result = parser.parse_method("        静态 函数 获取版本() -> 整数型 { }", 3)
    assert result is not None
    print('✓ 测试19: 静态方法')

def test_020_virtual_method():
    """基础测试20: 虚方法"""
    parser = ClassParserExtended()
    parser.parse_class_declaration("类 形状 {", 1)
    parser.parse_line("    方法:", 2)
    result = parser.parse_method("        虚函数 绘制() -> 空型 { }", 3)
    assert result is not None
    print('✓ 测试20: 虚方法')

def test_021_attribute_converter():
    """基础测试21: 属性转换器"""
    converter = AttributeConverter()
    result = converter.convert_attribute('姓名', '字符串型', 'public')
    assert result is not None
    print('✓ 测试21: 属性转换器')

def test_022_type_mapping():
    """基础测试22: 类型映射"""
    converter = AttributeConverter()
    assert converter.TYPE_MAPPING['整数型'] == 'int'
    assert converter.TYPE_MAPPING['浮点型'] == 'float'
    print('✓ 测试22: 类型映射')

def test_023_private_attribute():
    """基础测试23: 私有属性转换"""
    converter = AttributeConverter()
    result = converter.convert_attribute('密码', '字符串型', 'private')
    assert result is not None
    print('✓ 测试23: 私有属性转换')

def test_024_attribute_with_default():
    """基础测试24: 带默认值的属性"""
    converter = AttributeConverter()
    result = converter.convert_attribute('年龄', '整数型', 'public', '0')
    assert result is not None
    print('✓ 测试24: 带默认值的属性')

def test_025_class_to_struct():
    """基础测试25: 类到struct转换"""
    converter = ClassToStructConverter()
    converter.convert_attribute('x', '整数型', 'public')
    result = converter.convert_class('点')
    assert '点_t' in result.struct_declaration
    print('✓ 测试25: 类到struct转换')

def test_026_struct_declaration():
    """基础测试26: struct声明生成"""
    converter = ClassToStructConverter()
    converter.convert_attribute('名称', '字符串型', 'public')
    result = converter.convert_class('物品')
    assert 'typedef struct' in result.struct_declaration
    print('✓ 测试26: struct声明生成')

def test_027_multiple_attributes():
    """基础测试27: 多属性转换"""
    converter = ClassToStructConverter()
    converter.convert_attribute('x', '整数型', 'public')
    converter.convert_attribute('y', '整数型', 'public')
    result = converter.convert_class('坐标')
    assert result.statistics['total_attributes'] == 2
    print('✓ 测试27: 多属性转换')

def test_028_statistics():
    """基础测试28: 统计信息"""
    converter = ClassToStructConverter()
    converter.convert_attribute('a', '整数型', 'public')
    converter.convert_attribute('b', '整数型', 'private')
    result = converter.convert_class('测试')
    assert result.statistics['public_attributes'] >= 1
    print('✓ 测试28: 统计信息')

def test_029_unknown_type_warning():
    """基础测试29: 未知类型警告"""
    converter = AttributeConverter()
    result = converter.convert_attribute('数据', '自定义型', 'public')
    assert result is not None
    print('✓ 测试29: 未知类型警告')

def test_030_conversion_report():
    """基础测试30: 转换报告"""
    converter = ClassToStructConverter()
    converter.convert_attribute('名称', '字符串型', 'public')
    result = converter.convert_class('物品')
    report = converter.generate_report()
    assert len(report) > 0
    print('✓ 测试30: 转换报告')

def test_031_method_converter():
    """基础测试31: 方法转换器"""
    converter = MethodConverter()
    result = converter.convert_method('人', '函数 获取信息() -> 字符串型')
    assert result is not None
    print('✓ 测试31: 方法转换器')

def test_032_c_signature():
    """基础测试32: C函数签名"""
    converter = MethodConverter()
    result = converter.convert_method('人', '函数 获取年龄() -> 整数型')
    assert result is not None
    print('✓ 测试32: C函数签名')

def test_033_this_pointer():
    """基础测试33: this指针"""
    converter = MethodConverter()
    result = converter.convert_method('人', '函数 获取信息() -> 字符串型')
    assert result.has_this_pointer == True
    print('✓ 测试33: this指针')

def test_034_static_method_no_this():
    """基础测试34: 静态方法无this"""
    converter = MethodConverter()
    result = converter.convert_method('工具', '函数 获取版本() -> 整数型', is_static=True)
    assert result.has_this_pointer == False
    print('✓ 测试34: 静态方法无this')

def test_035_method_name_conversion():
    """基础测试35: 方法名转换"""
    converter = MethodConverter()
    result = converter.convert_method('数学', '函数 加法(整数型 a, 整数型 b) -> 整数型')
    assert result is not None
    print('✓ 测试35: 方法名转换')

def test_036_vtable_generator():
    """基础测试36: 虚表生成器"""
    gen = VirtualMethodTableGenerator()
    vtable = gen.create_virtual_table('形状', ['绘制', '面积'])
    assert vtable is not None
    print('✓ 测试36: 虚表生成器')

def test_037_vtable_struct():
    """基础测试37: 虚表struct生成"""
    gen = VirtualMethodTableGenerator()
    vtable = gen.create_virtual_table('形状', ['绘制'])
    struct_code = gen.generate_vtable_struct(vtable)
    assert '形状_vtable_t' in struct_code
    print('✓ 测试37: 虚表struct生成')

def test_038_vtable_initializer():
    """基础测试38: 虚表初始化生成"""
    gen = VirtualMethodTableGenerator()
    vtable = gen.create_virtual_table('形状', ['绘制'])
    init_code = gen.generate_vtable_initializer(vtable)
    assert '形状_vtable' in init_code
    print('✓ 测试38: 虚表初始化生成')

def test_039_parameter_info():
    """基础测试39: 参数信息"""
    converter = MethodConverter()
    result = converter.convert_method('测试', '函数 方法(整数型 a)')
    assert len(result.parameters) >= 1
    print('✓ 测试39: 参数信息')

def test_040_constructor_conversion():
    """基础测试40: 构造函数转换"""
    converter = MethodConverter()
    result = converter.convert_method('人', '函数 构造函数(字符串型 名) -> 空型', is_constructor=True)
    assert result is not None
    print('✓ 测试40: 构造函数转换')

# ============== 高级测试用例 (10个) ==============

def test_041_inheritance_single():
    """高级测试41: 单继承"""
    converter = InheritanceConverter()
    converter.add_class('学生', None, ['char* 姓名'])
    converter.add_class('大学生', '学生', ['char* 专业'])
    struct_def, _ = converter.convert_inheritance('大学生')
    assert 'struct 学生 base' in struct_def
    print('✓ 测试41: 单继承')

def test_042_inheritance_chain():
    """高级测试42: 继承链"""
    analyzer = InheritanceChainAnalyzer()
    analyzer.analyze({'人': None, '学生': '人', '大学生': '学生'})
    chain = analyzer.get_chain('大学生')
    assert len(chain) == 3
    print('✓ 测试42: 继承链')

def test_043_common_ancestor():
    """高级测试43: 最近公共祖先"""
    analyzer = InheritanceChainAnalyzer()
    analyzer.analyze({'A': None, 'B': 'A', 'C': 'A', 'D': 'B'})
    ancestor = analyzer.get_common_ancestor('C', 'D')
    assert ancestor == 'A'
    print('✓ 测试43: 最近公共祖先')

def test_044_polymorphism_handler():
    """高级测试44: 多态处理器"""
    handler = PolymorphismHandler()
    vt = handler.register_class('形状')
    vt.add_function('绘制', 'void draw()')
    assert handler.get_vtable_info('形状') is not None
    print('✓ 测试44: 多态处理器')

def test_045_vtable_inheritance():
    """高级测试45: 虚表继承"""
    handler = PolymorphismHandler()
    handler.register_class('形状')
    handler.register_class('圆形', '形状')
    vtable = handler.get_vtable_info('圆形')
    assert vtable is not None
    print('✓ 测试45: 虚表继承')

def test_046_rtti_struct():
    """高级测试46: RTTI结构生成"""
    handler = PolymorphismHandler()
    handler.register_class('物品')
    rtti_code = handler.generate_rtti_struct('物品')
    assert '物品_rtti_t' in rtti_code
    print('✓ 测试46: RTTI结构生成')

def test_047_class_with_vtable():
    """高级测试47: 带虚表的类定义"""
    handler = PolymorphismHandler()
    handler.register_class('形状')
    handler.vtables['形状'].add_function('绘制', 'void draw()')
    class_code = handler.generate_class_with_vtable('形状', ['int x', 'int y'])
    assert '形状_t' in class_code
    print('✓ 测试47: 带虚表的类定义')

def test_048_operator_overload():
    """高级测试48: 运算符重载"""
    parser = OperatorOverloadParser()
    parser.set_current_class('向量')
    info = parser.parse_operator_declaration("操作符 加(向量) -> 向量", 1)
    assert info is not None
    print('✓ 测试48: 运算符重载')

def test_049_operator_generator():
    """高级测试49: 运算符生成器"""
    generator = OperatorOverloadGenerator()
    generator.register_overload('复数', OperatorType.ADD, '复数')
    header = generator.generate_header('复数')
    assert '复数' in header
    print('✓ 测试49: 运算符生成器')

def test_050_complete_class_system():
    """高级测试50: 完整类系统集成"""
    parser = ClassParserExtended()
    parser.parse_class_declaration("类 形状 {", 1)
    parser.parse_line("    公开:", 2)
    parser.parse_line("    属性:", 3)
    parser.parse_attribute("        整数型 x;", 4)
    parser.parse_line("    方法:", 5)
    parser.parse_method("        函数 绘制() -> 空型 { }", 6)
    assert parser.get_class('形状') is not None
    print('✓ 测试50: 完整类系统集成')


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("测试套件8：类系统完整测试 (50个测试用例)")
    print("=" * 70)

    tests = [
        test_001_class_declaration,
        test_002_multiple_classes,
        test_003_attribute_declaration,
        test_004_method_declaration,
        test_005_constructor,
        test_006_destructor,
        test_007_public_visibility,
        test_008_private_visibility,
        test_009_protected_visibility,
        test_010_class_summary,
        test_011_extended_parser,
        test_012_extended_method,
        test_013_parameter_parsing,
        test_014_method_body,
        test_015_get_class,
        test_016_duplicate_class_error,
        test_017_class_with_parameters,
        test_018_return_type_parsing,
        test_019_static_method,
        test_020_virtual_method,
        test_021_attribute_converter,
        test_022_type_mapping,
        test_023_private_attribute,
        test_024_attribute_with_default,
        test_025_class_to_struct,
        test_026_struct_declaration,
        test_027_multiple_attributes,
        test_028_statistics,
        test_029_unknown_type_warning,
        test_030_conversion_report,
        test_031_method_converter,
        test_032_c_signature,
        test_033_this_pointer,
        test_034_static_method_no_this,
        test_035_method_name_conversion,
        test_036_vtable_generator,
        test_037_vtable_struct,
        test_038_vtable_initializer,
        test_039_parameter_info,
        test_040_constructor_conversion,
        test_041_inheritance_single,
        test_042_inheritance_chain,
        test_043_common_ancestor,
        test_044_polymorphism_handler,
        test_045_vtable_inheritance,
        test_046_rtti_struct,
        test_047_class_with_vtable,
        test_048_operator_overload,
        test_049_operator_generator,
        test_050_complete_class_system,
    ]

    passed = 0
    failed = 0
    errors = []
    for i, test in enumerate(tests, 1):
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            errors.append(f"测试{i}: {test.__name__} - {e}")
            print(f"✗ 测试{i}: {test.__name__} 失败 - {e}")

    print("=" * 70)
    print(f"测试总数: {len(tests)}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print("=" * 70)

    if failed == 0:
        print("🎉 所有测试通过！测试套件8通过率100%")
    else:
        print("失败的测试:")
        for err in errors:
            print(f"  - {err}")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
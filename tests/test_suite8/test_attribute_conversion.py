#!/usr/bin/env python3
"""
测试套件8：属性转换测试

测试属性转换器的功能：
1. 类型映射测试
2. 可见性转换测试
3. 默认值处理测试
4. 继承成员测试
"""

import sys
import unittest
from pathlib import Path

from zhc.converter.attribute import (
    AttributeConverter, ClassToStructConverter, TYPE_MAPPING,
    Visibility, AttributeType
)


class TestTypeMapping(unittest.TestCase):
    """类型映射测试"""

    def test_001_basic_types(self):
        """测试1：基本类型映射"""
        self.assertEqual(TYPE_MAPPING['整数型'], 'int')
        self.assertEqual(TYPE_MAPPING['浮点型'], 'float')
        self.assertEqual(TYPE_MAPPING['字符型'], 'char')
        self.assertEqual(TYPE_MAPPING['字符串型'], 'char*')
        print("✓ 测试1：基本类型映射通过")

    def test_002_extended_types(self):
        """测试2：扩展类型映射"""
        self.assertEqual(TYPE_MAPPING['双精度浮点型'], 'double')
        self.assertEqual(TYPE_MAPPING['短整数型'], 'short')
        self.assertEqual(TYPE_MAPPING['长整数型'], 'long')
        self.assertEqual(TYPE_MAPPING['逻辑型'], 'int')
        print("✓ 测试2：扩展类型映射通过")

    def test_003_type_mapping_completeness(self):
        """测试3：类型映射完整性"""
        required_types = [
            '整数型', '浮点型', '双精度浮点型', '字符型', '字符串型',
            '逻辑型', '短整数型', '长整数型', '空型', '无类型'
        ]
        for t in required_types:
            self.assertIn(t, TYPE_MAPPING)
        print("✓ 测试3：类型映射完整性通过")


class TestAttributeConversion(unittest.TestCase):
    """属性转换测试"""

    def test_004_public_attribute(self):
        """测试4：公开属性转换"""
        converter = ClassToStructConverter()
        converter.convert_attribute("姓名", "字符串型", "public", line_number=1)

        self.assertEqual(len(converter.converter.attributes), 1)
        attr = converter.converter.attributes[0]
        self.assertEqual(attr.name, "姓名")
        self.assertEqual(attr.c_type, "char*")
        self.assertEqual(attr.visibility, Visibility.PUBLIC)
        print("✓ 测试4：公开属性转换通过")

    def test_005_private_attribute(self):
        """测试5：私有属性转换"""
        converter = ClassToStructConverter()
        converter.convert_attribute("内部数据", "整数型", "private", line_number=1)

        attr = converter.converter.attributes[0]
        self.assertEqual(attr.visibility, Visibility.PRIVATE)
        print("✓ 测试5：私有属性转换通过")

    def test_006_protected_attribute(self):
        """测试6：保护属性转换"""
        converter = ClassToStructConverter()
        converter.convert_attribute("保护数据", "整数型", "protected", line_number=1)

        attr = converter.converter.attributes[0]
        self.assertEqual(attr.visibility, Visibility.PROTECTED)
        print("✓ 测试6：保护属性转换通过")

    def test_007_default_value(self):
        """测试7：默认值处理"""
        converter = ClassToStructConverter()
        converter.convert_attribute("成绩", "浮点型", "private", "0.0", line_number=1)

        attr = converter.converter.attributes[0]
        self.assertEqual(attr.default_value, "0.0")
        print("✓ 测试7：默认值处理通过")

    def test_008_multiple_attributes(self):
        """测试8：多属性转换"""
        converter = ClassToStructConverter()
        converter.convert_attribute("姓名", "字符串型", "public", line_number=1)
        converter.convert_attribute("年龄", "整数型", "public", line_number=2)
        converter.convert_attribute("成绩", "浮点型", "private", "0.0", line_number=3)

        self.assertEqual(len(converter.converter.attributes), 3)
        stats = converter.converter.get_statistics()
        self.assertEqual(stats['total_attributes'], 3)
        self.assertEqual(stats['public_attributes'], 2)
        self.assertEqual(stats['private_attributes'], 1)
        print("✓ 测试8：多属性转换通过")


class TestStructGeneration(unittest.TestCase):
    """struct生成测试"""

    def test_009_struct_declaration(self):
        """测试9：struct声明生成"""
        converter = ClassToStructConverter()
        converter.convert_attribute("姓名", "字符串型", "public", line_number=1)
        converter.convert_attribute("年龄", "整数型", "public", line_number=2)

        result = converter.convert_class("学生")

        self.assertIn("struct 学生", result.struct_declaration)
        self.assertIn("char* 姓名", result.struct_declaration)
        self.assertIn("int 年龄", result.struct_declaration)
        self.assertIn("#ifndef", result.struct_declaration)
        self.assertIn("#endif", result.struct_declaration)
        print("✓ 测试9：struct声明生成通过")

    def test_010_struct_with_inheritance(self):
        """测试10：带继承的struct生成"""
        converter = ClassToStructConverter()
        converter.convert_attribute("专业", "字符串型", "public", line_number=1)

        result = converter.convert_class("大学生", base_class="学生")

        self.assertIn("struct 大学生", result.struct_declaration)
        self.assertIn("struct 学生 base", result.struct_declaration)
        self.assertIn('#include "学生.h"', result.struct_declaration)
        print("✓ 测试10：继承struct生成通过")

    def test_011_struct_definition(self):
        """测试11：struct定义生成"""
        converter = ClassToStructConverter()
        converter.convert_attribute("版本", "整数型", "private", "1", line_number=1)
        converter.convert_attribute("名称", "字符串型", "public", line_number=2)

        result = converter.convert_class("配置")

        self.assertIn("#include", result.struct_definition)
        print("✓ 测试11：struct定义生成通过")


class TestVisibilityConversion(unittest.TestCase):
    """可见性转换测试"""

    def test_012_public_keyword(self):
        """测试12：公开关键字识别"""
        converter = AttributeConverter()
        converter.add_attribute("公开数据", "整数型", "public", line_number=1)

        self.assertEqual(converter.attributes[0].visibility, Visibility.PUBLIC)
        print("✓ 测试12：公开关键字识别通过")

    def test_013_private_keyword(self):
        """测试13：私有关键字识别"""
        converter = AttributeConverter()
        converter.add_attribute("私有数据", "整数型", "private", line_number=1)

        self.assertEqual(converter.attributes[0].visibility, Visibility.PRIVATE)
        print("✓ 测试13：私有关键字识别通过")

    def test_014_protected_keyword(self):
        """测试14：保护关键字识别"""
        converter = AttributeConverter()
        converter.add_attribute("保护数据", "整数型", "protected", line_number=1)

        self.assertEqual(converter.attributes[0].visibility, Visibility.PROTECTED)
        print("✓ 测试14：保护关键字识别通过")

    def test_015_chinese_keywords(self):
        """测试15：中文关键字识别"""
        converter = AttributeConverter()
        converter.add_attribute("数据1", "整数型", "公开", line_number=1)
        converter.add_attribute("数据2", "整数型", "私有", line_number=2)
        converter.add_attribute("数据3", "整数型", "保护", line_number=3)

        self.assertEqual(converter.attributes[0].visibility, Visibility.PUBLIC)
        self.assertEqual(converter.attributes[1].visibility, Visibility.PRIVATE)
        self.assertEqual(converter.attributes[2].visibility, Visibility.PROTECTED)
        print("✓ 测试15：中文关键字识别通过")


class TestStatistics(unittest.TestCase):
    """统计测试"""

    def test_016_statistics_calculation(self):
        """测试16：统计计算"""
        converter = ClassToStructConverter()
        converter.convert_attribute("公开1", "整数型", "public", line_number=1)
        converter.convert_attribute("公开2", "浮点型", "public", line_number=2)
        converter.convert_attribute("私有1", "字符串型", "private", line_number=3)
        converter.convert_attribute("保护1", "整数型", "protected", line_number=4)
        converter.convert_attribute("静态1", "整数型", "private", is_static=True, line_number=5)

        stats = converter.converter.get_statistics()

        self.assertEqual(stats['total_attributes'], 5)
        self.assertEqual(stats['public_attributes'], 2)
        self.assertEqual(stats['private_attributes'], 2)
        self.assertEqual(stats['protected_attributes'], 1)
        self.assertEqual(stats['static_attributes'], 1)
        print("✓ 测试16：统计计算通过")


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("开始运行属性转换测试")
    print("=" * 70)
    print()

    suite = unittest.TestSuite()

    test_classes = [
        TestTypeMapping,
        TestAttributeConversion,
        TestStructGeneration,
        TestVisibilityConversion,
        TestStatistics
    ]

    for test_class in test_classes:
        tests = unittest.makeSuite(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 70)
    print("属性转换测试总结：")
    print("=" * 70)
    print(f"  运行测试: {result.testsRun}")
    print(f"  通过测试: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败测试: {len(result.failures)}")
    print(f"  错误测试: {len(result.errors)}")

    if result.wasSuccessful():
        print()
        print("🎉 所有测试通过！属性转换验证完成！")
    else:
        print()
        print("⚠️  有测试失败")

    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
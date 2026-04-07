#!/usr/bin/env python3
"""
测试套件8：方法转换测试
"""

import sys
import unittest
from pathlib import Path


from zhc.converter.method import (
    MethodConverter, VirtualMethodTableGenerator,
    MethodConversionResult, ParameterInfo
)


class TestMethodConversion(unittest.TestCase):
    """方法转换测试"""

    def test_001_basic_method_conversion(self):
        """测试1：基本方法转换"""
        converter = MethodConverter()
        result = converter.convert_method("学生", "函数 获取信息() -> 字符串型")

        self.assertEqual(result.converted_name, "学生_获取信息")
        self.assertIn("学生_获取信息", result.c_function_signature)
        print("✓ 测试1：基本方法转换通过")

    def test_002_constructor_conversion(self):
        """测试2：构造函数转换"""
        converter = MethodConverter()
        result = converter.convert_method(
            "学生",
            "函数 构造函数(字符串型 名) -> 空型",
            is_constructor=True
        )

        self.assertEqual(result.converted_name, "学生_constructor")
        self.assertTrue(result.is_constructor)
        self.assertTrue(result.has_this_pointer)
        print("✓ 测试2：构造函数转换通过")

    def test_003_static_method_conversion(self):
        """测试3：静态方法转换（无this指针）"""
        converter = MethodConverter()
        result = converter.convert_method(
            "学生",
            "函数 获取版本() -> 整数型",
            is_static=True
        )

        self.assertEqual(result.converted_name, "学生_获取版本")
        self.assertTrue(result.is_static)
        self.assertFalse(result.has_this_pointer)
        print("✓ 测试3：静态方法转换通过")

    def test_004_method_with_parameters(self):
        """测试4：带参数的方法转换"""
        converter = MethodConverter()
        result = converter.convert_method(
            "学生",
            "函数 设置成绩(浮点型 分) -> 空型"
        )

        self.assertEqual(result.converted_name, "学生_设置成绩")
        self.assertEqual(len(result.parameters), 1)
        self.assertEqual(result.parameters[0].name, "分")
        print("✓ 测试4：带参数方法转换通过")

    def test_005_parameter_types(self):
        """测试5：参数类型映射"""
        converter = MethodConverter()
        result = converter.convert_method(
            "学生",
            "函数 方法(整数型 a, 浮点型 b, 字符串型 c) -> 空型"
        )

        self.assertEqual(len(result.parameters), 3)
        self.assertEqual(result.parameters[0].c_type, "int")
        self.assertEqual(result.parameters[1].c_type, "float")
        self.assertEqual(result.parameters[2].c_type, "char*")
        print("✓ 测试5：参数类型映射通过")

    def test_006_visibility_in_signature(self):
        """测试6：可见性（影响签名中的self）"""
        converter = MethodConverter()

        # 私有方法
        result1 = converter.convert_method("类", "函数 私有方法() -> 空型")
        self.assertTrue(result1.has_this_pointer)

        # 公开方法
        result2 = converter.convert_method("类", "函数 公开方法() -> 空型", visibility="public")
        self.assertTrue(result2.has_this_pointer)
        print("✓ 测试6：可见性签名通过")

    def test_007_virtual_table_generation(self):
        """测试7：虚函数表生成"""
        gen = VirtualMethodTableGenerator()
        vtable = gen.create_virtual_table("形状", ["绘制", "移动"])

        self.assertEqual(vtable.class_name, "形状")
        self.assertEqual(len(vtable.entries), 2)
        self.assertEqual(vtable.entries[0].method_name, "绘制")
        self.assertEqual(vtable.entries[1].method_name, "移动")
        print("✓ 测试7：虚函数表生成通过")

    def test_008_vtable_struct_generation(self):
        """测试8：虚函数表struct生成"""
        gen = VirtualMethodTableGenerator()
        vtable = gen.create_virtual_table("形状", ["绘制", "移动"])
        struct_code = gen.generate_vtable_struct("形状")

        self.assertIn("typedef struct 形状_vtable", struct_code)
        self.assertIn("void (*method1)(struct 形状* self)", struct_code)
        print("✓ 测试8：虚函数表struct生成通过")


def run_tests():
    """运行测试"""
    print("=" * 60)
    print("方法转换测试")
    print("=" * 60)

    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(TestMethodConversion))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 60)
    print(f"运行: {result.testsRun}, 通过: {result.testsRun - len(result.failures)}")
    if result.wasSuccessful():
        print("🎉 所有测试通过")
    print("=" * 60)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
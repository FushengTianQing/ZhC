#!/usr/bin/env python3
"""
测试套件8：类系统测试

测试类系统的核心功能：
1. 类声明测试
2. 属性访问测试
3. 方法调用测试
4. 继承测试
5. 多态测试
"""

import sys
import os
import tempfile
import unittest
from pathlib import Path

from zhc.parser.class_ import (
    ClassParser, ClassInfo, AttributeInfo, MethodInfo, Visibility
)
from zhc.parser.class_extended import ClassParserExtended


class TestClassDeclaration(unittest.TestCase):
    """类声明测试"""

    def test_001_basic_class_declaration(self):
        """测试1：基本类声明"""
        parser = ClassParser()

        code = """
类 学生 {
    属性:
        字符串型 姓名;

    方法:
        函数 获取信息() -> 字符串型 {
            返回 姓名;
        }
}
"""
        lines = code.strip().split('\n')
        for i, line in enumerate(lines, 1):
            parser.parse_line(line.strip(), i)

        self.assertIn('学生', parser.classes)
        student = parser.classes['学生']
        self.assertEqual(student.name, '学生')
        print("✓ 测试1：基本类声明通过")

    def test_002_class_with_inheritance(self):
        """测试2：带继承的类声明"""
        parser = ClassParser()

        code = """
类 大学生 : 学生 {
    属性:
        字符串型 专业;
}
"""
        lines = code.strip().split('\n')
        for i, line in enumerate(lines, 1):
            parser.parse_line(line.strip(), i)

        self.assertIn('大学生', parser.classes)
        undergrad = parser.classes['大学生']
        self.assertEqual(undergrad.base_class, '学生')
        print("✓ 测试2：继承类声明通过")

    def test_003_duplicate_class_error(self):
        """测试3：重复类声明错误"""
        parser = ClassParser()

        code = """
类 学生 {
    属性:
        字符串型 姓名;
}

类 学生 {
    属性:
        整数型 年龄;
}
"""
        lines = code.strip().split('\n')
        for i, line in enumerate(lines, 1):
            parser.parse_line(line.strip(), i)

        # 应该产生错误
        self.assertGreater(len(parser.errors), 0)
        print("✓ 测试3：重复类声明错误处理通过")

    def test_004_visibility_public(self):
        """测试4：公开可见性"""
        parser = ClassParser()

        code = """
类 测试 {
    公开:
    属性:
        字符串型 公开属性;
}
"""
        lines = code.strip().split('\n')
        for i, line in enumerate(lines, 1):
            parser.parse_line(line.strip(), i)

        test_class = parser.classes['测试']
        self.assertEqual(len(test_class.attributes), 1)
        attr = test_class.attributes[0]
        self.assertEqual(attr.visibility, Visibility.PUBLIC)
        print("✓ 测试4：公开可见性通过")

    def test_005_visibility_private(self):
        """测试5：私有可见性"""
        parser = ClassParser()

        code = """
类 测试 {
    私有:
    属性:
        整数型 私有属性;
}
"""
        lines = code.strip().split('\n')
        for i, line in enumerate(lines, 1):
            parser.parse_line(line.strip(), i)

        test_class = parser.classes['测试']
        self.assertEqual(len(test_class.attributes), 1)
        attr = test_class.attributes[0]
        self.assertEqual(attr.visibility, Visibility.PRIVATE)
        print("✓ 测试5：私有可见性通过")


class TestAttributeAccess(unittest.TestCase):
    """属性访问测试"""

    def test_006_attribute_with_default_value(self):
        """测试6：带默认值的属性"""
        parser = ClassParser()

        code = """
类 学生 {
    属性:
        浮点型 成绩 = 0.0;
}
"""
        lines = code.strip().split('\n')
        for i, line in enumerate(lines, 1):
            parser.parse_line(line.strip(), i)

        test_class = parser.classes['学生']
        self.assertEqual(len(test_class.attributes), 1)
        attr = test_class.attributes[0]
        self.assertEqual(attr.default_value, "0.0")
        print("✓ 测试6：默认值属性通过")

    def test_007_multiple_attributes(self):
        """测试7：多个属性"""
        parser = ClassParser()

        code = """
类 学生 {
    属性:
        字符串型 姓名;
        整数型 年龄;
        浮点型 成绩;
}
"""
        lines = code.strip().split('\n')
        for i, line in enumerate(lines, 1):
            parser.parse_line(line.strip(), i)

        test_class = parser.classes['学生']
        self.assertEqual(len(test_class.attributes), 3)
        print("✓ 测试7：多属性测试通过")

    def test_008_public_attributes(self):
        """测试8：公开属性获取"""
        parser = ClassParser()

        code = """
类 学生 {
    公开:
    属性:
        字符串型 姓名;
        整数型 年龄;

    私有:
    属性:
        浮点型 成绩;
}
"""
        lines = code.strip().split('\n')
        for i, line in enumerate(lines, 1):
            parser.parse_line(line.strip(), i)

        test_class = parser.classes['学生']
        pub_attrs = test_class.get_public_attributes()
        self.assertEqual(len(pub_attrs), 2)
        print("✓ 测试8：公开属性获取通过")


class TestMethodCall(unittest.TestCase):
    """方法调用测试"""

    def test_009_method_with_parameters(self):
        """测试9：带参数的方法"""
        parser = ClassParser()

        code = """
类 学生 {
    方法:
        函数 设置成绩(参数 浮点型 分) -> 空型 {
            成绩 = 分;
        }
}
"""
        lines = code.strip().split('\n')
        for i, line in enumerate(lines, 1):
            parser.parse_line(line.strip(), i)

        test_class = parser.classes['学生']
        self.assertEqual(len(test_class.methods), 1)
        method = test_class.methods[0]
        self.assertEqual(method.name, "设置成绩")
        self.assertEqual(len(method.parameters), 1)
        print("✓ 测试9：带参数方法通过")

    def test_010_constructor(self):
        """测试10：构造函数"""
        parser = ClassParser()

        code = """
类 学生 {
    方法:
        函数 构造函数(字符串型 名, 整数型 龄) -> 空型 {
            姓名 = 名;
            年龄 = 龄;
        }
}
"""
        lines = code.strip().split('\n')
        for i, line in enumerate(lines, 1):
            parser.parse_line(line.strip(), i)

        test_class = parser.classes['学生']
        constructor = test_class.get_constructor()
        self.assertIsNotNone(constructor)
        self.assertEqual(len(constructor.parameters), 2)
        print("✓ 测试10：构造函数测试通过")


class TestInheritance(unittest.TestCase):
    """继承测试"""

    def test_011_single_inheritance(self):
        """测试11：单继承"""
        parser = ClassParser()

        code = """
类 大学生 : 学生 {
    属性:
        字符串型 专业;
}
"""
        lines = code.strip().split('\n')
        for i, line in enumerate(lines, 1):
            parser.parse_line(line.strip(), i)

        self.assertIn('大学生', parser.classes)
        undergrad = parser.classes['大学生']
        self.assertEqual(undergrad.base_class, '学生')
        print("✓ 测试11：单继承测试通过")

    def test_012_inheritance_chain(self):
        """测试12：继承链"""
        parser = ClassParserExtended()

        code = """
类 人类 {
    属性:
        字符串型 姓名;
}

类 学生 : 人类 {
    属性:
        整数型 年龄;
}

类 大学生 : 学生 {
    属性:
        字符串型 专业;
}
"""
        lines = code.strip().split('\n')
        for i, line in enumerate(lines, 1):
            parser.parse_line(line.strip(), i)

        undergrad = parser.classes['大学生']
        self.assertEqual(len(undergrad.inheritance_chain), 3)
        self.assertEqual(undergrad.inheritance_chain[0], '人类')
        self.assertEqual(undergrad.inheritance_chain[1], '学生')
        self.assertEqual(undergrad.inheritance_chain[2], '大学生')
        print("✓ 测试12：继承链测试通过")

    def test_013_derived_class_attributes(self):
        """测试13：派生类属性"""
        parser = ClassParser()

        code = """
类 学生 {
    属性:
        字符串型 姓名;

    方法:
        函数 获取信息() -> 字符串型 {
            返回 姓名;
        }
}

类 大学生 : 学生 {
    属性:
        字符串型 专业;
}
"""
        lines = code.strip().split('\n')
        for i, line in enumerate(lines, 1):
            parser.parse_line(line.strip(), i)

        undergrad = parser.classes['大学生']
        # 派生类有自己的属性
        self.assertEqual(len(undergrad.attributes), 1)
        self.assertEqual(undergrad.attributes[0].name, '专业')
        print("✓ 测试13：派生类属性测试通过")


class TestExtendedParser(unittest.TestCase):
    """扩展解析器测试"""

    def test_014_extended_parser_basic(self):
        """测试14：扩展解析器基本功能"""
        parser = ClassParserExtended()

        code = """
类 学生 {
    公开:
    属性:
        字符串型 姓名;
        整数型 年龄;

    方法:
        函数 获取信息() -> 字符串型 {
            返回 姓名;
        }
}
"""
        lines = code.strip().split('\n')
        for i, line in enumerate(lines, 1):
            parser.parse_line(line.strip(), i)

        self.assertIn('学生', parser.classes)
        student = parser.classes['学生']
        self.assertEqual(len(student.attributes), 2)
        self.assertEqual(len(student.methods), 1)
        print("✓ 测试14：扩展解析器基本功能通过")

    def test_015_extended_parser_with_body(self):
        """测试15：扩展解析器方法体"""
        parser = ClassParserExtended()

        code = """
类 学生 {
    方法:
        函数 获取信息() -> 字符串型 {
            返回 姓名;
        }
}
"""
        lines = code.strip().split('\n')
        for i, line in enumerate(lines, 1):
            parser.parse_line(line.strip(), i)

        student = parser.classes['学生']
        method = student.methods[0]
        self.assertIsNotNone(method.body)
        self.assertGreater(len(method.body.lines), 0)
        print("✓ 测试15：扩展解析器方法体通过")

    def test_016_extended_parser_inheritance(self):
        """测试16：扩展解析器继承"""
        parser = ClassParserExtended()

        code = """
类 大学生 : 学生 {
    属性:
        字符串型 专业;
}
"""
        lines = code.strip().split('\n')
        for i, line in enumerate(lines, 1):
            parser.parse_line(line.strip(), i)

        undergrad = parser.classes['大学生']
        self.assertEqual(undergrad.base_class, '学生')
        self.assertIn('学生', undergrad.inheritance_chain)
        print("✓ 测试16：扩展解析器继承通过")


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("开始运行测试套件8：类系统测试")
    print("=" * 70)
    print()

    suite = unittest.TestSuite()

    test_classes = [
        TestClassDeclaration,
        TestAttributeAccess,
        TestMethodCall,
        TestInheritance,
        TestExtendedParser
    ]

    for test_class in test_classes:
        tests = unittest.makeSuite(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 70)
    print("测试套件8总结：")
    print("=" * 70)
    print(f"  运行测试: {result.testsRun}")
    print(f"  通过测试: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败测试: {len(result.failures)}")
    print(f"  错误测试: {len(result.errors)}")

    if result.wasSuccessful():
        print()
        print("🎉 所有测试通过！测试套件8通过率100%")
    else:
        print()
        print("⚠️  有测试失败，请检查上述输出")

    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
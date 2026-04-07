#!/usr/bin/env python3
"""
Day 8 高级模块特性测试

测试模块别名、条件编译和版本控制功能
"""

import sys
import unittest
from pathlib import Path

from zhpp.parser.module_alias import (
    ModuleAliasManager, ConditionalCompiler, VersionManager,
    VersionInfo, VersionComparator, ModuleAlias,
    ConditionType
)


class TestModuleAlias(unittest.TestCase):
    """模块别名测试"""

    def test_001_add_alias(self):
        """测试1：添加模块别名"""
        manager = ModuleAliasManager()
        result = manager.add_alias("数学库", "M", 1)

        self.assertTrue(result)
        self.assertEqual(manager.get_original_name("M"), "数学库")
        print("✓ 测试1：添加模块别名通过")

    def test_002_multiple_aliases(self):
        """测试2：同一模块多个别名"""
        manager = ModuleAliasManager()
        manager.add_alias("数学库", "M", 1)
        manager.add_alias("数学库", "Math", 2)

        aliases = manager.get_all_aliases("数学库")
        self.assertEqual(len(aliases), 2)
        self.assertIn("M", aliases)
        self.assertIn("Math", aliases)
        print("✓ 测试2：多别名测试通过")

    def test_003_duplicate_alias(self):
        """测试3：重复别名检测"""
        manager = ModuleAliasManager()
        manager.add_alias("数学库", "M", 1)
        result = manager.add_alias("工具库", "M", 2)

        self.assertFalse(result)  # 应该失败
        print("✓ 测试3：重复别名检测通过")

    def test_004_resolve_alias(self):
        """测试4：别名解析"""
        manager = ModuleAliasManager()
        manager.add_alias("数学库", "M", 1)

        # 解析别名
        resolved = manager.resolve_module_name("M")
        self.assertEqual(resolved, "数学库")

        # 解析普通模块名
        resolved = manager.resolve_module_name("工具库")
        self.assertEqual(resolved, "工具库")
        print("✓ 测试4：别名解析通过")

    def test_005_remove_alias(self):
        """测试5：移除别名"""
        manager = ModuleAliasManager()
        manager.add_alias("数学库", "M", 1)
        result = manager.remove_alias("M")

        self.assertTrue(result)
        self.assertIsNone(manager.get_original_name("M"))
        print("✓ 测试5：移除别名通过")

    def test_006_is_alias(self):
        """测试6：别名检查"""
        manager = ModuleAliasManager()
        manager.add_alias("数学库", "M", 1)

        self.assertTrue(manager.is_alias("M"))
        self.assertFalse(manager.is_alias("数学库"))
        self.assertFalse(manager.is_alias("不存在的模块"))
        print("✓ 测试6：别名检查通过")


class TestConditionalCompilation(unittest.TestCase):
    """条件编译测试"""

    def test_007_define_symbol(self):
        """测试7：定义符号"""
        compiler = ConditionalCompiler()
        compiler.define_symbol("调试模式")

        self.assertTrue(compiler.is_defined("调试模式"))
        self.assertFalse(compiler.is_defined("发行版"))
        print("✓ 测试7：定义符号通过")

    def test_008_undefine_symbol(self):
        """测试8：取消定义符号"""
        compiler = ConditionalCompiler()
        compiler.define_symbol("调试模式")
        compiler.undefine_symbol("调试模式")

        self.assertFalse(compiler.is_defined("调试模式"))
        print("✓ 测试8：取消定义符号通过")

    def test_009_evaluate_defined(self):
        """测试9：评估已定义条件"""
        compiler = ConditionalCompiler()
        compiler.define_symbol("调试模式")

        result = compiler.evaluate_condition(ConditionType.DEFINED, "调试模式")
        self.assertTrue(result)

        result = compiler.evaluate_condition(ConditionType.NOT_DEFINED, "调试模式")
        self.assertFalse(result)
        print("✓ 测试9：评估已定义条件通过")

    def test_010_process_simple_block(self):
        """测试10：处理简单条件块"""
        compiler = ConditionalCompiler()
        compiler.define_symbol("调试模式")

        code = """
模块 测试 {
    公开:
        函数 测试() {
            打印("Hello");
        }
}
"""
        result = compiler.process_conditional_block(code)
        self.assertIn("打印", result)
        print("✓ 测试10：处理简单条件块通过")


class TestVersionManagement(unittest.TestCase):
    """版本管理测试"""

    def test_011_parse_version(self):
        """测试11：解析版本字符串"""
        v = VersionInfo.parse("1.2.3")
        self.assertEqual(v.major, 1)
        self.assertEqual(v.minor, 2)
        self.assertEqual(v.patch, 3)
        print("✓ 测试11：解析版本字符串通过")

    def test_012_parse_version_without_patch(self):
        """测试12：解析不带patch的版本"""
        v = VersionInfo.parse("1.2")
        self.assertEqual(v.major, 1)
        self.assertEqual(v.minor, 2)
        self.assertEqual(v.patch, 0)
        print("✓ 测试12：解析不带patch版本通过")

    def test_013_version_comparison(self):
        """测试13：版本比较"""
        v1 = VersionInfo.parse("1.2.3")
        v2 = VersionInfo.parse("1.3.0")
        v3 = VersionInfo.parse("2.0.0")

        self.assertTrue(v1 < v2)
        self.assertTrue(v1 < v3)
        self.assertTrue(v2 < v3)
        self.assertTrue(v1 <= v1)
        self.assertTrue(v1 >= v1)
        print("✓ 测试13：版本比较通过")

    def test_014_version_comparator(self):
        """测试14：版本比较器"""
        self.assertTrue(VersionComparator.compare("1.2.3", ">=", "1.0.0"))
        self.assertTrue(VersionComparator.compare("1.2.3", "<=", "2.0.0"))
        self.assertTrue(VersionComparator.compare("1.2.3", "==", "1.2.3"))
        self.assertFalse(VersionComparator.compare("1.2.3", "!=", "1.2.3"))
        print("✓ 测试14：版本比较器通过")

    def test_015_register_version(self):
        """测试15：注册模块版本"""
        manager = VersionManager()
        manager.register_module_version("数学库", "1.2.3")

        version = manager.get_module_version("数学库")
        self.assertIsNotNone(version)
        self.assertEqual(str(version), "1.2.3")
        print("✓ 测试15：注册模块版本通过")

    def test_016_version_constraint(self):
        """测试16：版本约束检查"""
        manager = VersionManager()
        manager.register_module_version("数学库", "1.2.3")
        manager.set_version_constraint("数学库", ">= 1.0.0")

        self.assertTrue(manager.check_version_compatibility("数学库", ">= 1.0.0"))
        self.assertTrue(manager.check_version_compatibility("数学库", "<= 2.0.0"))
        self.assertFalse(manager.check_version_compatibility("数学库", ">= 2.0.0"))
        print("✓ 测试16：版本约束检查通过")

    def test_017_version_statistics(self):
        """测试17：版本统计"""
        manager = VersionManager()
        manager.register_module_version("数学库", "1.2.3")
        manager.register_module_version("工具库", "2.0.0")
        manager.register_module_version("网络库", "1.5.0")

        stats = manager.get_statistics()
        self.assertEqual(stats['total_modules'], 3)
        self.assertIn("数学库", stats['modules'])
        print("✓ 测试17：版本统计通过")


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def test_018_full_alias_workflow(self):
        """测试18：完整别名工作流"""
        # 创建别名管理器
        manager = ModuleAliasManager()

        # 添加别名
        manager.add_alias("数学库", "M", 1)
        manager.add_alias("数学库", "Math", 2)
        manager.add_alias("工具库", "Utils", 3)

        # 解析并使用
        self.assertEqual(manager.resolve_module_name("M"), "数学库")
        self.assertEqual(manager.resolve_module_name("Math"), "数学库")
        self.assertEqual(manager.resolve_module_name("Utils"), "工具库")

        # 验证原始模块名
        self.assertEqual(manager.get_all_aliases("数学库"), ["M", "Math"])
        print("✓ 测试18：完整别名工作流通过")

    def test_019_full_version_workflow(self):
        """测试19：完整版本管理工作流"""
        manager = VersionManager()

        # 注册版本
        manager.register_module_version("数学库", "1.2.3")
        manager.register_module_version("工具库", "2.0.0")
        manager.register_module_version("网络库", "1.0.0-beta")

        # 设置约束
        manager.set_version_constraint("数学库", ">= 1.0.0")
        manager.set_version_constraint("工具库", ">= 2.0.0")

        # 验证兼容
        self.assertTrue(manager.check_version_compatibility("数学库", ">= 1.0.0"))
        self.assertTrue(manager.check_version_compatibility("工具库", ">= 2.0.0"))
        self.assertFalse(manager.check_version_compatibility("工具库", ">= 3.0.0"))
        print("✓ 测试19：完整版本管理工作流通过")

    def test_020_combined_advanced_features(self):
        """测试20：组合高级特性"""
        alias_manager = ModuleAliasManager()
        version_manager = VersionManager()
        compiler = ConditionalCompiler()

        # 设置环境
        alias_manager.add_alias("数学库", "M", 1)
        compiler.define_symbol("高性能")

        # 注册版本
        version_manager.register_module_version("数学库", "1.2.3")

        # 验证
        self.assertTrue(alias_manager.is_alias("M"))
        self.assertTrue(compiler.is_defined("高性能"))
        self.assertTrue(version_manager.check_version_compatibility("数学库", ">= 1.0.0"))

        print("✓ 测试20：组合高级特性通过")


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("开始运行 Day 8 高级模块特性测试")
    print("=" * 70)
    print()

    # 创建测试套件
    suite = unittest.TestSuite()

    test_classes = [
        TestModuleAlias,
        TestConditionalCompilation,
        TestVersionManagement,
        TestIntegration
    ]

    for test_class in test_classes:
        tests = unittest.makeSuite(test_class)
        suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出总结
    print()
    print("=" * 70)
    print("Day 8 高级模块特性测试总结：")
    print("=" * 70)
    print(f"  运行测试: {result.testsRun}")
    print(f"  通过测试: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败测试: {len(result.failures)}")
    print(f"  错误测试: {len(result.errors)}")

    if result.wasSuccessful():
        print()
        print("🎉 所有测试通过！高级模块特性验证完成！")
    else:
        print()
        print("⚠️  有测试失败，请检查上述输出")

    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
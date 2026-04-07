#!/usr/bin/env python3
"""
泛型支持测试套件
Generic Programming Tests

测试泛型类型、泛型函数的解析和实例化
"""

import unittest
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from zhc.generics.generic_parser import (
    GenericParser,
    GenericType,
    GenericFunction,
    TypeParameter,
    GenericConstraint
)
from zhc.generics.generic_instantiator import (
    GenericInstantiator,
    InstantiatedType,
    InstantiatedFunction
)


class TestTypeParameter(unittest.TestCase):
    """测试类型参数"""
    
    def test_type_parameter_creation(self):
        """测试类型参数创建"""
        param = TypeParameter(name="T")
        self.assertEqual(param.name, "T")
        self.assertEqual(param.constraints, [])
        self.assertIsNone(param.default_type)
    
    def test_type_parameter_with_constraints(self):
        """测试带约束的类型参数"""
        param = TypeParameter(
            name="T",
            constraints=[GenericConstraint.NUMBER, GenericConstraint.COMPARABLE]
        )
        self.assertEqual(param.name, "T")
        self.assertEqual(len(param.constraints), 2)
        self.assertTrue(param.has_constraint(GenericConstraint.NUMBER))
        self.assertTrue(param.has_constraint(GenericConstraint.COMPARABLE))
        self.assertFalse(param.has_constraint(GenericConstraint.ADDABLE))
    
    def test_type_parameter_to_c_code(self):
        """测试类型参数转C代码"""
        param = TypeParameter(name="T")
        c_code = param.to_c_code()
        self.assertIn("类型参数", c_code)
        self.assertIn("T", c_code)


class TestGenericType(unittest.TestCase):
    """测试泛型类型"""
    
    def setUp(self):
        """测试前准备"""
        self.type_params = [
            TypeParameter(name="T"),
            TypeParameter(name="U", constraints=[GenericConstraint.NUMBER])
        ]
        self.generic_type = GenericType(
            name="列表",
            type_params=self.type_params,
            body="T 数据[100];\n整数型 长度;"
        )
    
    def test_generic_type_creation(self):
        """测试泛型类型创建"""
        self.assertEqual(self.generic_type.name, "列表")
        self.assertEqual(len(self.generic_type.type_params), 2)
        self.assertIn("数据", self.generic_type.body)
    
    def test_get_type_param_names(self):
        """测试获取类型参数名"""
        names = self.generic_type.get_type_param_names()
        self.assertEqual(names, ["T", "U"])
    
    def test_instantiate_type(self):
        """测试类型实例化"""
        type_args = {"T": "整数型", "U": "浮点型"}
        code = self.generic_type.instantiate(type_args)
        
        self.assertIn("整数型", code)
        self.assertIn("数据", code)
        self.assertNotIn("T 数据", code)


class TestGenericFunction(unittest.TestCase):
    """测试泛型函数"""
    
    def setUp(self):
        """测试前准备"""
        self.type_params = [
            TypeParameter(name="T", constraints=[GenericConstraint.COMPARABLE])
        ]
        self.generic_func = GenericFunction(
            name="最大值",
            return_type="T",
            type_params=self.type_params,
            parameters=[("T", "a"), ("T", "b")],
            body="如果 (a > b) {\n返回 a;\n} 否则 {\n返回 b;\n}"
        )
    
    def test_generic_function_creation(self):
        """测试泛型函数创建"""
        self.assertEqual(self.generic_func.name, "最大值")
        self.assertEqual(self.generic_func.return_type, "T")
        self.assertEqual(len(self.generic_func.parameters), 2)
    
    def test_get_type_param_names(self):
        """测试获取类型参数名"""
        names = self.generic_func.get_type_param_names()
        self.assertEqual(names, ["T"])
    
    def test_instantiate_function(self):
        """测试函数实例化"""
        type_args = {"T": "整数型"}
        code = self.generic_func.instantiate(type_args)
        
        self.assertIn("整数型", code)
        self.assertIn("最大值", code)
        self.assertIn("a", code)
        self.assertIn("b", code)


class TestGenericParser(unittest.TestCase):
    """测试泛型解析器"""
    
    def setUp(self):
        """测试前准备"""
        self.parser = GenericParser()
    
    def test_parse_generic_type(self):
        """测试解析泛型类型"""
        code = """
泛型类型 列表<类型 T> {
    T 数据[100];
    整数型 长度;
}
"""
        generic_type = self.parser.parse_generic_type(code)
        
        self.assertIsNotNone(generic_type)
        self.assertEqual(generic_type.name, "列表")
        self.assertEqual(len(generic_type.type_params), 1)
        self.assertEqual(generic_type.type_params[0].name, "T")
    
    def test_parse_generic_type_with_constraints(self):
        """测试解析带约束的泛型类型"""
        code = """
泛型类型 数值容器<类型 T: 数值类型> {
    T 值;
}
"""
        generic_type = self.parser.parse_generic_type(code)
        
        self.assertIsNotNone(generic_type)
        self.assertEqual(generic_type.name, "数值容器")
        self.assertEqual(len(generic_type.type_params), 1)
        self.assertTrue(
            generic_type.type_params[0].has_constraint(GenericConstraint.NUMBER)
        )
    
    def test_parse_generic_function(self):
        """测试解析泛型函数"""
        code = """
泛型函数 T 最大值<类型 T>(T a, T b) {
    如果 (a > b) {
        返回 a;
    } 否则 {
        返回 b;
    }
}
"""
        generic_func = self.parser.parse_generic_function(code)
        
        self.assertIsNotNone(generic_func)
        self.assertEqual(generic_func.name, "最大值")
        self.assertEqual(generic_func.return_type, "T")
        self.assertEqual(len(generic_func.parameters), 2)
    
    def test_parse_type_parameters(self):
        """测试解析类型参数"""
        params_str = "类型 T, 类型 U: 数值类型"
        type_params = self.parser._parse_type_parameters(params_str)
        
        self.assertEqual(len(type_params), 2)
        self.assertEqual(type_params[0].name, "T")
        self.assertEqual(type_params[1].name, "U")
        self.assertTrue(type_params[1].has_constraint(GenericConstraint.NUMBER))
    
    def test_parse_parameters(self):
        """测试解析函数参数"""
        args_str = "T a, T b, 整数型 c"
        parameters = self.parser._parse_parameters(args_str)
        
        self.assertEqual(len(parameters), 3)
        self.assertEqual(parameters[0], ("T", "a"))
        self.assertEqual(parameters[1], ("T", "b"))
        self.assertEqual(parameters[2], ("整数型", "c"))
    
    def test_get_all_generic_names(self):
        """测试获取所有泛型名称"""
        # 先解析一些定义
        self.parser.parse_generic_type(
            "泛型类型 列表<类型 T> { T 数据[100]; }"
        )
        self.parser.parse_generic_function(
            "泛型函数 T 最大值<类型 T>(T a, T b) { 返回 a; }"
        )
        
        type_names, func_names = self.parser.get_all_generic_names()
        
        self.assertIn("列表", type_names)
        self.assertIn("最大值", func_names)


class TestGenericInstantiator(unittest.TestCase):
    """测试泛型实例化器"""
    
    def setUp(self):
        """测试前准备"""
        self.instantiator = GenericInstantiator()
        
        # 创建测试用的泛型定义
        self.generic_type = GenericType(
            name="列表",
            type_params=[TypeParameter(name="T")],
            body="T 数据[100];\n整数型 长度;"
        )
        
        self.generic_func = GenericFunction(
            name="最大值",
            return_type="T",
            type_params=[TypeParameter(name="T")],
            parameters=[("T", "a"), ("T", "b")],
            body="如果 (a > b) { 返回 a; } 否则 { 返回 b; }"
        )
    
    def test_instantiate_type(self):
        """测试实例化泛型类型"""
        type_args = {"T": "整数型"}
        inst_type = self.instantiator.instantiate_type(self.generic_type, type_args)
        
        self.assertIsNotNone(inst_type)
        self.assertEqual(inst_type.original_name, "列表")
        self.assertEqual(inst_type.instantiated_name, "列表_整数型")
        self.assertIn("整数型", inst_type.code)
    
    def test_instantiate_function(self):
        """测试实例化泛型函数"""
        type_args = {"T": "浮点型"}
        inst_func = self.instantiator.instantiate_function(self.generic_func, type_args)
        
        self.assertIsNotNone(inst_func)
        self.assertEqual(inst_func.original_name, "最大值")
        self.assertEqual(inst_func.instantiated_name, "最大值_浮点型")
        self.assertIn("浮点型", inst_func.code)
    
    def test_parse_type_application(self):
        """测试解析类型应用"""
        type_expr = "列表<整数型>"
        generic_name, type_args = self.instantiator.parse_type_application(type_expr)
        
        self.assertEqual(generic_name, "列表")
        self.assertIn("T", type_args)
        self.assertEqual(type_args["T"], "整数型")
    
    def test_parse_multi_param_application(self):
        """测试解析多参数类型应用"""
        type_expr = "字典<字符串型, 整数型>"
        generic_name, type_args = self.instantiator.parse_type_application(type_expr)
        
        self.assertEqual(generic_name, "字典")
        self.assertIn("T", type_args)
        self.assertIn("U", type_args)
        self.assertEqual(type_args["T"], "字符串型")
        self.assertEqual(type_args["U"], "整数型")
    
    def test_get_instantiated_name(self):
        """测试获取实例化名称"""
        name = self.instantiator.get_instantiated_name("列表", {"T": "整数型"})
        self.assertEqual(name, "列表_整数型")
    
    def test_is_instantiated(self):
        """测试检查是否已实例化"""
        type_args = {"T": "整数型"}
        
        # 实例化前
        self.assertFalse(self.instantiator.is_instantiated("列表_整数型"))
        
        # 实例化
        self.instantiator.instantiate_type(self.generic_type, type_args)
        
        # 实例化后
        self.assertTrue(self.instantiator.is_instantiated("列表_整数型"))
    
    def test_generate_c_code(self):
        """测试生成C代码"""
        # 实例化一些类型和函数
        self.instantiator.instantiate_type(self.generic_type, {"T": "整数型"})
        self.instantiator.instantiate_function(self.generic_func, {"T": "浮点型"})
        
        code = self.instantiator.generate_c_code()
        
        self.assertIn("结构体 列表_整数型", code)
        self.assertIn("浮点型", code)
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        # 实例化一些类型和函数
        self.instantiator.instantiate_type(self.generic_type, {"T": "整数型"})
        self.instantiator.instantiate_function(self.generic_func, {"T": "浮点型"})
        
        stats = self.instantiator.get_statistics()
        
        self.assertEqual(stats['instantiated_types'], 1)
        self.assertEqual(stats['instantiated_functions'], 1)
        self.assertEqual(stats['total'], 2)


class TestGenericConstraints(unittest.TestCase):
    """测试泛型约束"""
    
    def test_number_constraint(self):
        """测试数值类型约束"""
        parser = GenericParser()
        
        # 测试数值类型
        self.assertTrue(parser._check_constraint("整数型", GenericConstraint.NUMBER))
        self.assertTrue(parser._check_constraint("浮点型", GenericConstraint.NUMBER))
        
        # 测试非数值类型
        self.assertFalse(parser._check_constraint("字符串型", GenericConstraint.NUMBER))
    
    def test_comparable_constraint(self):
        """测试可比较约束"""
        parser = GenericParser()
        
        # 所有类型都应该可比较（简化实现）
        self.assertTrue(parser._check_constraint("整数型", GenericConstraint.COMPARABLE))
        self.assertTrue(parser._check_constraint("字符串型", GenericConstraint.COMPARABLE))
    
    def test_addable_constraint(self):
        """测试可加法约束"""
        parser = GenericParser()
        
        # 测试可加法类型
        self.assertTrue(parser._check_constraint("整数型", GenericConstraint.ADDABLE))
        self.assertTrue(parser._check_constraint("字符串型", GenericConstraint.ADDABLE))
        
        # 测试不可加法类型
        self.assertFalse(parser._check_constraint("布尔型", GenericConstraint.ADDABLE))


class TestGenericTypeIntegration(unittest.TestCase):
    """测试泛型类型集成"""
    
    def test_complete_workflow(self):
        """测试完整工作流"""
        # 1. 创建解析器
        parser = GenericParser()
        
        # 2. 解析泛型定义
        type_code = """
泛型类型 列表<类型 T> {
    T 数据[100];
    整数型 长度;
}
"""
        generic_type = parser.parse_generic_type(type_code)
        self.assertIsNotNone(generic_type)
        
        # 3. 创建实例化器
        instantiator = GenericInstantiator()
        
        # 4. 实例化类型
        inst_type = instantiator.instantiate_type(generic_type, {"T": "整数型"})
        self.assertIsNotNone(inst_type)
        
        # 5. 生成代码
        code = instantiator.generate_c_code()
        self.assertIn("列表_整数型", code)
        self.assertIn("整数型", code)


class TestGenericFunctionIntegration(unittest.TestCase):
    """测试泛型函数集成"""
    
    def test_complete_workflow(self):
        """测试完整工作流"""
        # 1. 创建解析器
        parser = GenericParser()
        
        # 2. 解析泛型函数
        func_code = """
泛型函数 T 最大值<类型 T>(T a, T b) {
    如果 (a > b) {
        返回 a;
    } 否则 {
        返回 b;
    }
}
"""
        generic_func = parser.parse_generic_function(func_code)
        self.assertIsNotNone(generic_func)
        
        # 3. 创建实例化器
        instantiator = GenericInstantiator()
        
        # 4. 实例化函数
        inst_func = instantiator.instantiate_function(generic_func, {"T": "浮点型"})
        self.assertIsNotNone(inst_func)
        
        # 5. 生成代码
        code = instantiator.generate_c_code()
        self.assertIn("最大值_浮点型", code)
        self.assertIn("浮点型", code)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestTypeParameter))
    suite.addTests(loader.loadTestsFromTestCase(TestGenericType))
    suite.addTests(loader.loadTestsFromTestCase(TestGenericFunction))
    suite.addTests(loader.loadTestsFromTestCase(TestGenericParser))
    suite.addTests(loader.loadTestsFromTestCase(TestGenericInstantiator))
    suite.addTests(loader.loadTestsFromTestCase(TestGenericConstraints))
    suite.addTests(loader.loadTestsFromTestCase(TestGenericTypeIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestGenericFunctionIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 显示结果
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    print(f"✅ 通过: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ 失败: {len(result.failures)}")
    print(f"⚠️  错误: {len(result.errors)}")
    print(f"📋 总计: {result.testsRun}")
    print("=" * 60)
    
    if result.wasSuccessful():
        print("🎉 所有测试通过！")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
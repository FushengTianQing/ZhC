"""
ZHC编译器 - 语义分析系统测试

测试范围：
- 类型检查器（TypeChecker）
- 作用域检查器（ScopeChecker）
- 函数重载解析器（OverloadResolver）
- 语义分析器（SemanticAnalyzer）

作者：远
日期：2026-04-03
"""

import unittest
import sys
from pathlib import Path

# 添加src路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zhpp.analyzer import (
    TypeChecker, TypeInfo, TypeCategory,
    ScopeChecker, Symbol, SymbolCategory,
    OverloadResolver,
    SemanticAnalyzer, AnalysisResult
)


class TestTypeChecker(unittest.TestCase):
    """类型检查器测试"""
    
    def setUp(self):
        """测试初始化"""
        self.checker = TypeChecker()
    
    def test_builtin_types(self):
        """测试内置类型"""
        # 整数类型
        int_type = self.checker.get_type("整数型")
        self.assertIsNotNone(int_type)
        self.assertEqual(int_type.name, "整数型")
        self.assertEqual(int_type.size, 4)
        self.assertTrue(int_type.is_numeric())
        self.assertTrue(int_type.is_integer())
        
        # 浮点类型
        float_type = self.checker.get_type("浮点型")
        self.assertIsNotNone(float_type)
        self.assertEqual(float_type.size, 4)
        self.assertTrue(float_type.is_numeric())
        self.assertTrue(float_type.is_float())
        
        # 空类型
        void_type = self.checker.get_type("空型")
        self.assertIsNotNone(void_type)
        self.assertTrue(void_type.is_void())
    
    def test_type_decl_check(self):
        """测试类型声明检查"""
        # 有效类型
        valid_type = self.checker.check_type_decl(1, "整数型", "x")
        self.assertIsNotNone(valid_type)
        
        # 无效类型
        invalid_type = self.checker.check_type_decl(2, "未知类型", "y")
        self.assertIsNone(invalid_type)
        self.assertTrue(self.checker.has_errors())
    
    def test_assignment_check(self):
        """测试赋值类型检查"""
        int_type = self.checker.get_type("整数型")
        float_type = self.checker.get_type("浮点型")
        
        # 相同类型赋值
        self.assertTrue(self.checker.check_assignment(1, int_type, int_type))
        
        # 数值类型转换（整数转浮点无精度丢失）
        self.assertTrue(self.checker.check_assignment(2, float_type, int_type))
        # 注意：整数转浮点不会产生警告，只有浮点转整数才会
        
        # 浮点转整数（有精度丢失）
        self.checker.clear()
        self.assertTrue(self.checker.check_assignment(3, int_type, float_type))
        self.assertTrue(self.checker.has_warnings())  # 精度丢失警告
        
        # 不兼容类型
        void_type = self.checker.get_type("空型")
        self.assertFalse(self.checker.check_assignment(4, int_type, void_type))
    
    def test_binary_operations(self):
        """测试二元运算"""
        int_type = self.checker.get_type("整数型")
        float_type = self.checker.get_type("浮点型")
        
        # 算术运算
        result = self.checker.check_binary_op(1, "+", int_type, int_type)
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "整数型")
        
        result = self.checker.check_binary_op(2, "*", int_type, float_type)
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "浮点型")
        
        # 比较运算
        result = self.checker.check_binary_op(3, "==", int_type, int_type)
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "整数型")
    
    def test_unary_operations(self):
        """测试一元运算"""
        int_type = self.checker.get_type("整数型")
        
        # 算术一元运算
        result = self.checker.check_unary_op(1, "-", int_type)
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "整数型")
        
        # 逻辑非
        result = self.checker.check_unary_op(2, "!", int_type)
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "整数型")
    
    def test_pointer_type(self):
        """测试指针类型"""
        int_type = self.checker.get_type("整数型")
        ptr_type = self.checker.create_pointer_type(int_type)
        
        self.assertIsNotNone(ptr_type)
        self.assertTrue(ptr_type.is_pointer())
        self.assertEqual(ptr_type.base_type, int_type)
        self.assertEqual(ptr_type.size, 8)
    
    def test_array_type(self):
        """测试数组类型"""
        int_type = self.checker.get_type("整数型")
        array_type = self.checker.create_array_type(int_type, 10)
        
        self.assertIsNotNone(array_type)
        self.assertTrue(array_type.is_array())
        self.assertEqual(array_type.array_size, 10)
        self.assertEqual(array_type.base_type, int_type)
        self.assertEqual(array_type.size, 40)  # 4 * 10
    
    def test_function_type(self):
        """测试函数类型"""
        int_type = self.checker.get_type("整数型")
        float_type = self.checker.get_type("浮点型")
        
        func_type = self.checker.create_function_type(int_type, [int_type, float_type])
        
        self.assertIsNotNone(func_type)
        self.assertTrue(func_type.is_function())
        self.assertEqual(func_type.return_type, int_type)
        self.assertEqual(len(func_type.param_types), 2)


class TestScopeChecker(unittest.TestCase):
    """作用域检查器测试"""
    
    def setUp(self):
        """测试初始化"""
        self.checker = ScopeChecker()
    
    def test_variable_declaration(self):
        """测试变量声明"""
        int_type = TypeInfo(
            name="整数型",
            category=TypeCategory.PRIMITIVE,
            size=4
        )
        
        # 成功声明
        self.assertTrue(self.checker.declare_variable(1, "x", int_type))
        
        # 重复声明
        self.assertFalse(self.checker.declare_variable(2, "x", int_type))
        self.assertTrue(self.checker.has_errors())
    
    def test_variable_shadowing(self):
        """测试变量遮蔽"""
        int_type = TypeInfo(
            name="整数型",
            category=TypeCategory.PRIMITIVE,
            size=4
        )
        
        # 全局变量
        self.assertTrue(self.checker.declare_variable(1, "x", int_type))
        
        # 进入新作用域
        self.checker.enter_scope()
        
        # 遮蔽变量
        self.assertTrue(self.checker.declare_variable(2, "x", int_type))
        self.assertTrue(self.checker.has_warnings())
    
    def test_scope_stack(self):
        """测试作用域栈"""
        # 全局作用域
        self.assertEqual(self.checker.get_scope_level(), 0)
        self.assertTrue(self.checker.is_global_scope())
        
        # 进入函数作用域
        self.checker.enter_scope()
        self.assertEqual(self.checker.get_scope_level(), 1)
        self.assertTrue(self.checker.is_function_scope())
        
        # 进入代码块作用域
        self.checker.enter_scope()
        self.assertEqual(self.checker.get_scope_level(), 2)
        
        # 退出作用域
        self.checker.exit_scope()
        self.assertEqual(self.checker.get_scope_level(), 1)
        
        self.checker.exit_scope()
        self.assertEqual(self.checker.get_scope_level(), 0)
    
    def test_symbol_lookup(self):
        """测试符号查找"""
        int_type = TypeInfo(
            name="整数型",
            category=TypeCategory.PRIMITIVE,
            size=4
        )
        
        # 声明变量
        self.assertTrue(self.checker.declare_variable(1, "x", int_type))
        
        # 查找变量
        symbol = self.checker.lookup_symbol(2, "x")
        self.assertIsNotNone(symbol)
        self.assertEqual(symbol.name, "x")
        
        # 查找未声明变量
        symbol = self.checker.lookup_symbol(3, "y")
        self.assertIsNone(symbol)
        self.assertTrue(self.checker.has_errors())
    
    def test_const_assignment(self):
        """测试常量赋值"""
        int_type = TypeInfo(
            name="整数型",
            category=TypeCategory.PRIMITIVE,
            size=4
        )
        
        # 声明常量
        self.assertTrue(self.checker.declare_variable(1, "PI", int_type, is_const=True))
        
        # 尝试赋值
        symbol = self.checker.check_assignable(2, "PI")
        self.assertIsNone(symbol)
        self.assertTrue(self.checker.has_errors())


class TestOverloadResolver(unittest.TestCase):
    """函数重载解析器测试"""
    
    def setUp(self):
        """测试初始化"""
        self.resolver = OverloadResolver()
        self.int_type = TypeInfo(
            name="整数型",
            category=TypeCategory.PRIMITIVE,
            size=4
        )
        self.float_type = TypeInfo(
            name="浮点型",
            category=TypeCategory.PRIMITIVE,
            size=4
        )
    
    def test_single_candidate(self):
        """测试单个候选函数"""
        # 创建函数类型
        func_type = TypeInfo(
            name="func",
            category=TypeCategory.FUNCTION,
            return_type=self.int_type,
            param_types=[self.int_type]
        )
        
        # 创建函数符号
        func_symbol = Symbol(
            name="func",
            category=SymbolCategory.FUNCTION,
            type_info=func_type,
            line=1
        )
        
        # 解析调用
        result = self.resolver.resolve(2, "func", [func_symbol], [self.int_type])
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "func")
    
    def test_overload_resolution(self):
        """测试重载解析"""
        # 创建两个重载函数
        func1_type = TypeInfo(
            name="func",
            category=TypeCategory.FUNCTION,
            return_type=self.int_type,
            param_types=[self.int_type]
        )
        
        func2_type = TypeInfo(
            name="func",
            category=TypeCategory.FUNCTION,
            return_type=self.int_type,
            param_types=[self.float_type]
        )
        
        func1_symbol = Symbol(
            name="func",
            category=SymbolCategory.FUNCTION,
            type_info=func1_type,
            line=1
        )
        
        func2_symbol = Symbol(
            name="func",
            category=SymbolCategory.FUNCTION,
            type_info=func2_type,
            line=2
        )
        
        # 调用整数版本
        result = self.resolver.resolve(3, "func", [func1_symbol, func2_symbol], [self.int_type])
        self.assertIsNotNone(result)
        self.assertEqual(result.line, 1)  # 选择func1
        
        # 调用浮点版本
        self.resolver.clear()
        result = self.resolver.resolve(4, "func", [func1_symbol, func2_symbol], [self.float_type])
        self.assertIsNotNone(result)
        self.assertEqual(result.line, 2)  # 选择func2
    
    def test_no_match(self):
        """测试无匹配"""
        func_type = TypeInfo(
            name="func",
            category=TypeCategory.FUNCTION,
            return_type=self.int_type,
            param_types=[self.int_type]
        )
        
        func_symbol = Symbol(
            name="func",
            category=SymbolCategory.FUNCTION,
            type_info=func_type,
            line=1
        )
        
        # 无匹配调用（参数数量不匹配）
        result = self.resolver.resolve(2, "func", [func_symbol], [])
        self.assertIsNone(result)
        self.assertTrue(self.resolver.has_errors())


class TestSemanticAnalyzer(unittest.TestCase):
    """语义分析器测试"""
    
    def setUp(self):
        """测试初始化"""
        self.analyzer = SemanticAnalyzer()
    
    def test_variable_decl_analysis(self):
        """测试变量声明分析"""
        # 有效声明
        result = self.analyzer.analyze_variable_decl(1, "整数型", "x")
        self.assertTrue(result.success)
        
        # 无效类型
        result = self.analyzer.analyze_variable_decl(2, "未知类型", "y")
        self.assertFalse(result.success)
    
    def test_variable_with_init(self):
        """测试带初始化的变量声明"""
        int_type = self.analyzer.get_type("整数型")
        
        # 类型匹配的初始化
        result = self.analyzer.analyze_variable_decl(
            1, "整数型", "x", init_expr_type=int_type
        )
        self.assertTrue(result.success)
        
        # 类型不匹配的初始化
        void_type = self.analyzer.get_type("空型")
        result = self.analyzer.analyze_variable_decl(
            2, "整数型", "y", init_expr_type=void_type
        )
        self.assertFalse(result.success)
    
    def test_function_decl_analysis(self):
        """测试函数声明分析"""
        int_type = self.analyzer.get_type("整数型")
        
        # 简单函数
        result = self.analyzer.analyze_function_decl(
            1, "add", int_type, [("a", int_type), ("b", int_type)]
        )
        self.assertTrue(result.success)
        
        # 退出函数作用域
        self.analyzer.exit_scope()
    
    def test_assignment_analysis(self):
        """测试赋值分析"""
        # 声明变量
        result = self.analyzer.analyze_variable_decl(1, "整数型", "x")
        self.assertTrue(result.success)
        
        int_type = self.analyzer.get_type("整数型")
        
        # 有效赋值
        result = self.analyzer.analyze_assignment(2, "x", int_type)
        self.assertTrue(result.success)
        
        # 无效赋值（变量未声明）
        result = self.analyzer.analyze_assignment(3, "y", int_type)
        self.assertFalse(result.success)
    
    def test_binary_expr_analysis(self):
        """测试二元表达式分析"""
        int_type = self.analyzer.get_type("整数型")
        float_type = self.analyzer.get_type("浮点型")
        
        # 整数运算
        result = self.analyzer.analyze_binary_expr(1, "+", int_type, int_type)
        self.assertTrue(result.success)
        
        # 混合运算
        result = self.analyzer.analyze_binary_expr(2, "*", int_type, float_type)
        self.assertTrue(result.success)
    
    def test_report_generation(self):
        """测试报告生成"""
        # 产生一些错误和警告
        self.analyzer.analyze_variable_decl(1, "未知类型", "x")
        
        # 生成报告
        report = self.analyzer.report()
        self.assertIsNotNone(report)
        self.assertIn("语义分析报告", report)
        self.assertIn("错误", report)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_complete_analysis(self):
        """测试完整分析流程"""
        analyzer = SemanticAnalyzer()
        
        # 1. 声明变量
        result = analyzer.analyze_variable_decl(1, "整数型", "count")
        self.assertTrue(result.success)
        
        # 2. 声明函数
        int_type = analyzer.get_type("整数型")
        result = analyzer.analyze_function_decl(
            2, "add", int_type, [("a", int_type), ("b", int_type)]
        )
        self.assertTrue(result.success)
        
        # 3. 在函数内声明局部变量
        analyzer.enter_scope()
        result = analyzer.analyze_variable_decl(3, "整数型", "result")
        self.assertTrue(result.success)
        
        # 4. 退出作用域
        analyzer.exit_scope()  # result
        analyzer.exit_scope()  # add函数
        
        # 5. 检查最终状态
        self.assertFalse(analyzer.has_errors())
        
        # 6. 生成报告
        report = analyzer.report()
        self.assertIn("✅ 无语义错误", report)


def run_tests():
    """运行所有测试"""
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestTypeChecker))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestScopeChecker))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestOverloadResolver))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSemanticAnalyzer))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印摘要
    print("\n" + "=" * 70)
    print("测试摘要")
    print("=" * 70)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
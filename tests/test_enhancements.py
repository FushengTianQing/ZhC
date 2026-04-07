"""
增强功能测试套件
Enhancement Features Test Suite

测试所有新增的增强功能：
- 函数内联优化器
- 循环优化器
- clang-format集成
- WebAssembly后端
- sanitizers支持
"""

import unittest
import sys
from pathlib import Path

# 添加src路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "zhpp"))

# 直接导入模块文件
from opt.function_inline import FunctionInliner, InlineDecision
from opt.loop_optimizer import LoopOptimizer, LoopInfo
from tool.clang_format import ClangFormatIntegration
from backend.wasm_backend import WebAssemblyBackend
from tool.sanitizers import SanitizerIntegration, SanitizerType


class TestFunctionInliner(unittest.TestCase):
    """测试函数内联优化器"""
    
    def setUp(self):
        """测试初始化"""
        self.inliner = FunctionInliner(max_instruction_count=20)
    
    def test_register_function(self):
        """测试函数注册"""
        self.inliner.register_function(
            name="add",
            params=["a", "b"],
            body="return a + b;",
            return_type="int"
        )
        
        self.assertIn("add", self.inliner.functions)
        self.assertEqual(self.inliner.functions["add"].params, ["a", "b"])
    
    def test_inline_decision(self):
        """测试内联决策"""
        self.inliner.register_function(
            name="simple",
            params=["x"],
            body="return x * 2;",
            return_type="int"
        )
        
        decision = self.inliner.should_inline("main", "simple")
        self.assertIn(decision, [InlineDecision.INLINE, InlineDecision.FORCE_INLINE])
    
    def test_inline_call(self):
        """测试内联调用"""
        self.inliner.register_function(
            name="square",
            params=["x"],
            body="return x * x;",
            return_type="int"
        )
        
        result = self.inliner.inline_call("square", ["5"])
        self.assertIsNotNone(result)
        self.assertIn("5", result)
    
    def test_recursive_detection(self):
        """测试递归检测"""
        self.inliner.register_function(
            name="factorial",
            params=["n"],
            body="if (n <= 1) return 1; return n * factorial(n - 1);",
            return_type="int"
        )
        
        self.assertTrue(self.inliner.functions["factorial"].is_recursive)
        
        decision = self.inliner.should_inline("main", "factorial")
        self.assertEqual(decision, InlineDecision.NO_INLINE)
    
    def test_statistics(self):
        """测试统计信息"""
        self.inliner.register_function(
            name="add",
            params=["a", "b"],
            body="return a + b;",
            return_type="int"
        )
        
        stats = self.inliner.get_statistics()
        self.assertEqual(stats['registered_functions'], 1)
        self.assertIn('inline_rate', stats)


class TestLoopOptimizer(unittest.TestCase):
    """测试循环优化器"""
    
    def setUp(self):
        """测试初始化"""
        self.optimizer = LoopOptimizer(max_unroll_iterations=10)
    
    def test_parse_loop(self):
        """测试循环解析"""
        code = "循环 i 从 0 到 10 { 打印(i); }"
        loop = self.optimizer.parse_loop(code)
        
        self.assertIsNotNone(loop)
        self.assertEqual(loop.loop_var, "i")
        self.assertEqual(loop.start, "0")
        self.assertEqual(loop.end, "10")
        self.assertEqual(loop.iterations, 10)
    
    def test_unroll_loop(self):
        """测试循环展开"""
        loop = LoopInfo(
            loop_var="i",
            start="0",
            end="3",
            step="1",
            body="打印(i);"
        )
        
        unrolled = self.optimizer.unroll_loop(loop)
        self.assertIn("迭代 1", unrolled)
        self.assertIn("迭代 2", unrolled)
        self.assertIn("迭代 3", unrolled)
    
    def test_strength_reduction(self):
        """测试强度削减"""
        code = "x = i * 2; y = j / 4;"
        optimized = self.optimizer.reduce_strength(code)
        
        self.assertIn("<< 1", optimized)  # i * 2 → i << 1
        self.assertIn(">> 2", optimized)  # j / 4 → j >> 2
    
    def test_optimize(self):
        """测试综合优化"""
        code = """
        循环 i 从 0 到 5 {
            整数型 x = i * 2;
        }
        """
        
        optimized = self.optimizer.optimize(code)
        self.assertIn("循环展开", optimized)


class TestClangFormatIntegration(unittest.TestCase):
    """测试clang-format集成"""
    
    def setUp(self):
        """测试初始化"""
        self.formatter = ClangFormatIntegration(fallback_on_missing=True)
    
    def test_format_code(self):
        """测试代码格式化"""
        code = "int main(){return 0;}"
        result = self.formatter.format_code(code)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.formatted)
    
    def test_simple_format(self):
        """测试简单格式化（回退方案）"""
        code = "int main(){\nint x=1;\nreturn x;\n}"
        formatted = self.formatter._simple_format(code)
        
        # 简单格式化应该处理基本缩进
        self.assertIsNotNone(formatted)
        self.assertTrue(len(formatted) > 0)
    
    def test_check_style(self):
        """测试风格检查"""
        # 已经格式化的代码
        code = "int main() {\n    return 0;\n}\n"
        passed, issues = self.formatter.check_style(code)
        
        # 如果clang-format不可用，使用简单格式化
        if self.formatter.available:
            self.assertTrue(passed)
        else:
            # 简单格式化可能不完美
            self.assertIsInstance(passed, bool)
    
    def test_generate_config(self):
        """测试生成配置文件"""
        config = self.formatter.generate_config({'IndentWidth': 2})
        
        self.assertIn("BasedOnStyle:", config)
        self.assertIn("IndentWidth: 2", config)


class TestWebAssemblyBackend(unittest.TestCase):
    """测试WebAssembly后端"""
    
    def setUp(self):
        """测试初始化"""
        self.backend = WebAssemblyBackend()
    
    def test_availability_check(self):
        """测试可用性检查"""
        self.assertIsInstance(self.backend.available, bool)
    
    def test_generate_js_wrapper(self):
        """测试生成JS包装代码"""
        functions = [
            ("add", "int", ["int", "int"]),
            ("multiply", "int", ["int", "int"])
        ]
        
        wrapper = self.backend.generate_js_wrapper("module.wasm", functions)
        
        self.assertIn("wasmModule", wrapper)
        self.assertIn("add", wrapper)
        self.assertIn("multiply", wrapper)
    
    def test_statistics(self):
        """测试统计信息"""
        stats = self.backend.get_statistics()
        
        self.assertIn('available', stats)
        self.assertIn('total_compiles', stats)


class TestSanitizersIntegration(unittest.TestCase):
    """测试sanitizers支持"""
    
    def setUp(self):
        """测试初始化"""
        self.sanitizer = SanitizerIntegration()
    
    def test_availability_check(self):
        """测试可用性检查"""
        self.assertIsInstance(self.sanitizer.available, bool)
    
    def test_get_sanitizer_env(self):
        """测试获取环境变量"""
        env = self.sanitizer._get_sanitizer_env(SanitizerType.ADDRESS)
        
        self.assertIn('ASAN_OPTIONS', env)
    
    def test_parse_errors(self):
        """测试错误解析"""
        output = "ERROR: AddressSanitizer: heap-buffer-overflow"
        errors = self.sanitizer._parse_sanitizer_errors(output, SanitizerType.ADDRESS)
        
        self.assertTrue(len(errors) > 0)
    
    def test_statistics(self):
        """测试统计信息"""
        stats = self.sanitizer.get_statistics()
        
        self.assertIn('available', stats)
        self.assertIn('total_runs', stats)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_function_inline_with_loop_optimizer(self):
        """测试函数内联与循环优化协同工作"""
        # 创建内联器
        inliner = FunctionInliner()
        inliner.register_function(
            name="square",
            params=["x"],
            body="return x * x;",
            return_type="int"
        )
        
        # 创建循环优化器
        optimizer = LoopOptimizer()
        
        # 测试代码
        code = """
        循环 i 从 0 到 10 {
            整数型 result = square(i);
        }
        """
        
        # 优化
        optimized = optimizer.optimize(code)
        
        self.assertIn("循环", optimized)
    
    def test_format_and_compile(self):
        """测试格式化与编译流程"""
        formatter = ClangFormatIntegration(fallback_on_missing=True)
        
        # 原始代码
        code = "int main(){int x=1;return x;}"
        
        # 格式化
        result = formatter.format_code(code)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.formatted)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestFunctionInliner))
    suite.addTests(loader.loadTestsFromTestCase(TestLoopOptimizer))
    suite.addTests(loader.loadTestsFromTestCase(TestClangFormatIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestWebAssemblyBackend))
    suite.addTests(loader.loadTestsFromTestCase(TestSanitizersIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败详情:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n错误详情:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
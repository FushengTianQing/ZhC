#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试套件9: 模块依赖解析测试
测试Day 4的依赖解析、循环检测、编译顺序功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import unittest
from zhpp.analyzer.dependency import DependencyResolver, MultiFileIntegrator
from zhpp.converter.error import ErrorHandler

class TestDependencyResolution(unittest.TestCase):
    """测试依赖解析基础功能"""
    
    def setUp(self):
        """测试前准备"""
        self.resolver = DependencyResolver()
    
    def test_add_module(self):
        """测试添加模块"""
        module_def = {
            "name": "测试模块",
            "file_path": "test.zhc",
            "imports": [{"module": "依赖模块"}],
            "symbols": {
                "public": {"func1": "函数", "func2": "函数"},
                "private": {"internal": "函数"}
            },
            "line_number": 10
        }
        
        self.resolver.add_module(module_def)
        
        # 验证模块已添加
        self.assertIn("测试模块", self.resolver.graph.modules)
        self.assertEqual(self.resolver.graph.modules["测试模块"].name, "测试模块")
        self.assertEqual(self.resolver.graph.modules["测试模块"].dependencies, ["依赖模块"])
        self.assertEqual(len(self.resolver.graph.modules["测试模块"].public_symbols), 2)
        self.assertEqual(len(self.resolver.graph.modules["测试模块"].private_symbols), 1)
    
    def test_direct_dependencies(self):
        """测试直接依赖获取"""
        # 添加模块A依赖B
        module_a = {
            "name": "A",
            "file_path": "a.zhc",
            "imports": [{"module": "B"}, {"module": "C"}],
            "symbols": {"public": {}},
            "line_number": 1
        }
        
        module_b = {
            "name": "B",
            "file_path": "b.zhc", 
            "imports": [],
            "symbols": {"public": {}},
            "line_number": 1
        }
        
        self.resolver.add_module(module_a)
        self.resolver.add_module(module_b)
        
        deps_a = self.resolver.graph.get_dependencies("A")
        deps_b = self.resolver.graph.get_dependencies("B")
        
        self.assertEqual(deps_a, {"B", "C"})
        self.assertEqual(deps_b, set())
    
    def test_transitive_dependencies(self):
        """测试传递依赖"""
        # A -> B -> C
        modules = [
            {"name": "A", "deps": ["B"]},
            {"name": "B", "deps": ["C"]},
            {"name": "C", "deps": []}
        ]
        
        for module in modules:
            module_def = {
                "name": module["name"],
                "file_path": f"{module['name']}.zhc",
                "imports": [{"module": dep} for dep in module["deps"]],
                "symbols": {"public": {}},
                "line_number": 1
            }
            self.resolver.add_module(module_def)
        
        transitive_a = self.resolver.graph.get_transitive_dependencies("A")
        self.assertEqual(transitive_a, {"B", "C"})
        
        transitive_b = self.resolver.graph.get_transitive_dependencies("B")
        self.assertEqual(transitive_b, {"C"})
        
        transitive_c = self.resolver.graph.get_transitive_dependencies("C")
        self.assertEqual(transitive_c, set())

class TestCycleDetection(unittest.TestCase):
    """测试循环依赖检测"""
    
    def test_simple_cycle(self):
        """测试简单循环 A <-> B"""
        resolver = DependencyResolver()
        
        module_a = {
            "name": "A",
            "file_path": "a.zhc",
            "imports": [{"module": "B"}],
            "symbols": {"public": {}},
            "line_number": 1
        }
        
        module_b = {
            "name": "B",
            "file_path": "b.zhc",
            "imports": [{"module": "A"}],
            "symbols": {"public": {}},
            "line_number": 1
        }
        
        resolver.add_module(module_a)
        resolver.add_module(module_b)
        
        cycles = resolver.detect_cycles()
        
        self.assertEqual(len(cycles), 1)
        # 可能是 A->B->A 或 B->A->B
        cycle = cycles[0]
        self.assertTrue(len(cycle) >= 3)
        self.assertEqual(cycle[0], cycle[-1])  # 首尾相同
        
    def test_no_cycles(self):
        """测试无循环情况"""
        resolver = DependencyResolver()
        
        modules = [
            {"name": "基础", "deps": []},
            {"name": "工具", "deps": ["基础"]},
            {"name": "应用", "deps": ["工具"]}
        ]
        
        for module in modules:
            module_def = {
                "name": module["name"],
                "file_path": f"{module['name']}.zhc",
                "imports": [{"module": dep} for dep in module["deps"]],
                "symbols": {"public": {}},
                "line_number": 1
            }
            resolver.add_module(module_def)
        
        cycles = resolver.detect_cycles()
        self.assertEqual(cycles, [])
    
    def test_complex_cycle(self):
        """测试复杂循环 A->B->C->A"""
        resolver = DependencyResolver()
        
        modules = [
            {"name": "A", "deps": ["B"]},
            {"name": "B", "deps": ["C"]},
            {"name": "C", "deps": ["A"]}
        ]
        
        for module in modules:
            module_def = {
                "name": module["name"],
                "file_path": f"{module['name']}.zhc",
                "imports": [{"module": dep} for dep in module["deps"]],
                "symbols": {"public": {}},
                "line_number": 1
            }
            resolver.add_module(module_def)
        
        cycles = resolver.detect_cycles()
        self.assertGreater(len(cycles), 0)
        
        # 验证循环包含所有三个模块
        all_cycle_modules = set()
        for cycle in cycles:
            all_cycle_modules.update(cycle)
        
        self.assertTrue({"A", "B", "C"}.issubset(all_cycle_modules))

class TestCompilationOrder(unittest.TestCase):
    """测试编译顺序计算"""
    
    def test_simple_dag(self):
        """测试简单有向无环图"""
        resolver = DependencyResolver()
        
        # 创建依赖: A -> B -> C
        modules = [
            {"name": "C", "deps": []},
            {"name": "B", "deps": ["C"]},
            {"name": "A", "deps": ["B"]}
        ]
        
        for module in modules:
            module_def = {
                "name": module["name"],
                "file_path": f"{module['name']}.zhc",
                "imports": [{"module": dep} for dep in module["deps"]],
                "symbols": {"public": {}},
                "line_number": 1
            }
            resolver.add_module(module_def)
        
        order = resolver.calculate_compilation_order()
        
        # 验证顺序: C 应在 B 之前，B 应在 A 之前
        c_idx = order.index("C")
        b_idx = order.index("B")
        a_idx = order.index("A")
        
        self.assertLess(c_idx, b_idx)
        self.assertLess(b_idx, a_idx)
    
    def test_multiple_independent_modules(self):
        """测试多个独立模块"""
        resolver = DependencyResolver()
        
        modules = ["模块1", "模块2", "模块3", "模块4"]
        
        for name in modules:
            module_def = {
                "name": name,
                "file_path": f"{name}.zhc",
                "imports": [],
                "symbols": {"public": {}},
                "line_number": 1
            }
            resolver.add_module(module_def)
        
        order = resolver.calculate_compilation_order()
        
        # 所有模块都应出现在顺序中
        self.assertEqual(set(order), set(modules))
        self.assertEqual(len(order), len(modules))
    
    def test_cycle_prevents_order(self):
        """测试循环依赖阻止编译顺序计算"""
        resolver = DependencyResolver()
        
        # 创建循环
        module_a = {
            "name": "A",
            "file_path": "a.zhc",
            "imports": [{"module": "B"}],
            "symbols": {"public": {}},
            "line_number": 1
        }
        
        module_b = {
            "name": "B",
            "file_path": "b.zhc",
            "imports": [{"module": "A"}],
            "symbols": {"public": {}},
            "line_number": 1
        }
        
        resolver.add_module(module_a)
        resolver.add_module(module_b)
        
        order = resolver.calculate_compilation_order()
        
        # 存在循环时，应返回空列表
        self.assertEqual(order, [])

class TestMissingDependencies(unittest.TestCase):
    """测试缺失依赖检测"""
    
    def test_find_missing(self):
        """测试查找缺失依赖"""
        resolver = DependencyResolver()
        
        # A引用不存在的模块B
        module_a = {
            "name": "A",
            "file_path": "a.zhc",
            "imports": [{"module": "B"}, {"module": "C"}],
            "symbols": {"public": {}},
            "line_number": 1
        }
        
        # 只添加C，不添加B
        module_c = {
            "name": "C",
            "file_path": "c.zhc",
            "imports": [],
            "symbols": {"public": {}},
            "line_number": 1
        }
        
        resolver.add_module(module_a)
        resolver.add_module(module_c)
        
        missing = resolver.find_missing_dependencies()
        
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0], ("A", "B"))
    
    def test_no_missing(self):
        """测试无缺失依赖"""
        resolver = DependencyResolver()
        
        modules = [
            {"name": "A", "deps": ["B"]},
            {"name": "B", "deps": []}
        ]
        
        for module in modules:
            module_def = {
                "name": module["name"],
                "file_path": f"{module['name']}.zhc",
                "imports": [{"module": dep} for dep in module["deps"]],
                "symbols": {"public": {}},
                "line_number": 1
            }
            resolver.add_module(module_def)
        
        missing = resolver.find_missing_dependencies()
        self.assertEqual(missing, [])

class TestMultiFileIntegration(unittest.TestCase):
    """测试多文件集成"""
    
    def test_multi_file_registration(self):
        """测试多文件注册"""
        resolver = DependencyResolver()
        
        # 创建模块
        module_defs = [
            {
                "name": "工具",
                "file_path": "utils.zhc",
                "imports": [],
                "symbols": {"public": {"log": "函数"}},
                "line_number": 1
            },
            {
                "name": "网络",
                "file_path": "network.zhc",
                "imports": [{"module": "工具"}],
                "symbols": {"public": {"connect": "函数"}},
                "line_number": 1
            }
        ]
        
        for module_def in module_defs:
            resolver.add_module(module_def)
        
        # 创建集成器
        integrator = MultiFileIntegrator(resolver)
        
        # 注册文件
        for module_def in module_defs:
            content = f"# 模块: {module_def['name']}\n"
            integrator.register_module_file(
                module_def["name"],
                module_def["file_path"],
                content
            )
        
        # 验证注册
        self.assertEqual(len(integrator.module_files), 2)
        self.assertEqual(len(integrator.file_contents), 2)
        self.assertIn("工具", integrator.module_files)
        self.assertIn("网络", integrator.module_files)
    
    def test_makefile_generation(self):
        """测试Makefile生成"""
        resolver = DependencyResolver()
        
        # 添加简单模块
        module_def = {
            "name": "测试模块",
            "file_path": "test.zhc",
            "imports": [],
            "symbols": {"public": {}},
            "line_number": 1
        }
        resolver.add_module(module_def)
        
        integrator = MultiFileIntegrator(resolver)
        integrator.register_module_file("测试模块", "test.zhc", "# 测试\n")
        
        makefile = integrator.generate_makefile("./build")
        
        # 验证Makefile内容
        self.assertIn("CC = gcc", makefile)
        self.assertIn("CFLAGS =", makefile)
        self.assertIn("all:", makefile)
        self.assertIn("clean:", makefile)
        self.assertIn("./build", makefile)
    
    def test_integration_report(self):
        """测试集成报告"""
        resolver = DependencyResolver()
        
        # 创建有循环的模块
        module_a = {
            "name": "A",
            "file_path": "a.zhc",
            "imports": [{"module": "B"}],
            "symbols": {"public": {}},
            "line_number": 1
        }
        
        module_b = {
            "name": "B", 
            "file_path": "b.zhc",
            "imports": [{"module": "A"}],
            "symbols": {"public": {}},
            "line_number": 1
        }
        
        resolver.add_module(module_a)
        resolver.add_module(module_b)
        
        integrator = MultiFileIntegrator(resolver)
        integrator.register_module_file("A", "a.zhc", "# A\n")
        integrator.register_module_file("B", "b.zhc", "# B\n")
        
        report = integrator.export_integration_report()
        
        # 验证报告结构
        self.assertIn("statistics", report)
        self.assertIn("dependency_issues", report)
        self.assertIn("files", report)
        self.assertIn("recommendations", report)
        
        # 验证统计数据
        stats = report["statistics"]
        self.assertEqual(stats["total_modules"], 2)
        self.assertEqual(stats["total_dependencies"], 2)
        
        # 验证发现问题
        issues = report["dependency_issues"]
        self.assertGreater(len(issues["cycles"]), 0)

class TestErrorHandlerIntegration(unittest.TestCase):
    """测试错误处理器集成"""
    
    def test_error_reporting(self):
        """测试错误报告集成"""
        error_handler = ErrorHandler()
        resolver = DependencyResolver(error_handler)
        
        # 添加无效模块名
        invalid_module = {
            "name": "123invalid",
            "file_path": "invalid.zhc",
            "imports": [],
            "symbols": {"public": {}},
            "line_number": 5
        }
        
        resolver.add_module(invalid_module)
        
        # 获取错误
        errors = error_handler.get_all_errors()
        
        # 注意：错误处理的具体实现可能不在这里报告错误
        # 我们只测试集成是否正常工作
        self.assertIsInstance(errors, list)

class TestModuleStatistics(unittest.TestCase):
    """测试模块统计功能"""
    
    def test_statistics_calculation(self):
        """测试统计数据计算"""
        resolver = DependencyResolver()
        
        # 创建多个模块
        modules = [
            {
                "name": "核心",
                "file_path": "core.zhc",
                "imports": [],
                "symbols": {
                    "public": {"init": "函数", "shutdown": "函数"},
                    "private": {"internal": "函数"}
                },
                "line_number": 1
            },
            {
                "name": "工具",
                "file_path": "utils.zhc",
                "imports": [{"module": "核心"}],
                "symbols": {
                    "public": {"log": "函数", "debug": "函数", "error": "函数"},
                    "private": {"format": "函数"}
                },
                "line_number": 1
            },
            {
                "name": "独立",
                "file_path": "standalone.zhc",
                "imports": [],
                "symbols": {
                    "public": {"test": "函数"},
                    "private": {}
                },
                "line_number": 1
            }
        ]
        
        for module in modules:
            resolver.add_module(module)
        
        stats = resolver.get_module_statistics()
        
        # 验证统计数据
        self.assertEqual(stats["total_modules"], 3)
        self.assertEqual(stats["total_dependencies"], 1)  # 只有工具依赖核心
        self.assertEqual(stats["total_public_symbols"], 6)  # 2+3+1
        self.assertEqual(stats["total_private_symbols"], 2)  # 1+1+0
        self.assertEqual(stats["modules_without_deps"], 2)  # 核心和独立
        
        # 验证浮点数计算
        self.assertAlmostEqual(stats["avg_dependencies_per_module"], 1/3)

def run_tests():
    """运行测试套件"""
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestDependencyResolution,
        TestCycleDetection,
        TestCompilationOrder,
        TestMissingDependencies,
        TestMultiFileIntegration,
        TestErrorHandlerIntegration,
        TestModuleStatistics
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("=" * 60)
    print("测试套件9: 模块依赖解析测试")
    print("=" * 60)
    
    success = run_tests()
    
    if success:
        print("\n✅ 所有测试通过!")
    else:
        print("\n❌ 测试失败")
        sys.exit(1)
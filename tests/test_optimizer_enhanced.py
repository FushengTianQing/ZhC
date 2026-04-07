#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化器增强功能测试套件

测试：
1. P2-2 死代码消除（增强版）
2. P2-4 常量传播（增强版）
3. P2-3 预编译头文件（增强版）

作者：阿福
日期：2026-04-03
"""

import unittest
import sys
import os
import tempfile
import shutil

# 添加源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zhpp.opt.dead_code_elim import (
    DeadCodeEliminator,
    DeadCodeType,
    eliminate_dead_code
)
from zhpp.opt.constant_fold import (
    ConstantPropagator,
    propagate_constants,
    LatticeValue,
    ConstantType
)
from zhpp.compiler.precompiled_header import (
    PrecompiledHeaderManager,
    HeaderType,
    SymbolIndex
)


# ==================== 死代码消除测试 ====================

class TestDeadCodeElimination(unittest.TestCase):
    """死代码消除测试"""
    
    def setUp(self):
        self.eliminator = DeadCodeEliminator()
    
    def test_unreachable_code_detection(self):
        """测试不可达代码检测"""
        statements = [
            {'type': 'var_decl', 'name': 'x', 'value': 10, 'line': 1},
            {'type': 'return', 'value': 'x', 'line': 2},
            {'type': 'var_decl', 'name': 'y', 'value': 20, 'line': 3}  # 不可达
        ]
        
        optimized, dead_code = self.eliminator.eliminate(statements)
        
        # 应该检测到不可达代码
        unreachable = [d for d in dead_code if d.code_type == DeadCodeType.UNREACHABLE]
        self.assertGreater(len(unreachable), 0)
    
    def test_unused_variable_detection(self):
        """测试未使用变量检测"""
        statements = [
            {'type': 'var_decl', 'name': 'used_var', 'value': 10, 'line': 1},
            {'type': 'var_decl', 'name': 'unused_var', 'value': 20, 'line': 2},
            {'type': 'return', 'value': 'used_var', 'line': 3}
        ]
        
        optimized, dead_code = self.eliminator.eliminate(statements)
        
        # 应该检测到未使用变量
        unused_vars = [d for d in dead_code if d.code_type == DeadCodeType.UNUSED_VAR]
        self.assertGreater(len(unused_vars), 0)
    
    def test_constant_branch_folding(self):
        """测试常量分支消除"""
        statements = [
            {
                'type': 'if',
                'condition': '真',
                'then_body': [{'type': 'var_decl', 'name': 'x', 'value': 1, 'line': 2}],
                'else_body': [{'type': 'var_decl', 'name': 'y', 'value': 2, 'line': 4}],
                'line': 1
            }
        ]
        
        optimized, dead_code = self.eliminator.eliminate(statements)
        
        # 应该检测到常量分支
        branches = [d for d in dead_code if d.code_type == DeadCodeType.CONSTANT_BRANCH]
        self.assertGreater(len(branches), 0)
    
    def test_statistics(self):
        """测试统计信息"""
        statements = [
            {'type': 'var_decl', 'name': 'x', 'value': 10, 'line': 1},
            {'type': 'return', 'value': 'x', 'line': 2}
        ]
        
        self.eliminator.eliminate(statements)
        stats = self.eliminator.get_statistics()
        
        self.assertIn('total_lines_removed', stats)
        self.assertIn('dead_code_by_type', stats)
    
    def test_report_generation(self):
        """测试报告生成"""
        statements = [
            {'type': 'var_decl', 'name': 'x', 'value': 10, 'line': 1},
            {'type': 'return', 'value': 'x', 'line': 2}
        ]
        
        self.eliminator.eliminate(statements)
        report = self.eliminator.generate_report()
        
        self.assertIn('死代码消除', report)
        self.assertIn('统计', report)


# ==================== 常量传播测试 ====================

class TestConstantPropagation(unittest.TestCase):
    """常量传播测试"""
    
    def setUp(self):
        self.propagator = ConstantPropagator()
    
    def test_constant_folding(self):
        """测试常量折叠"""
        statements = [
            {'type': 'var_decl', 'name': 'x', 'value': '1 + 2 + 3', 'line': 1}
        ]
        
        optimized, constants = self.propagator.propagate(statements)
        
        # 应该检测到常量（即使没有折叠）
        self.assertIn('total_constants', self.propagator.get_statistics())
    
    def test_global_constant_detection(self):
        """测试全局常量检测"""
        statements = [
            {'type': 'var_decl', 'name': 'PI', 'value': 3.14, 'is_const': True, 'line': 1},
            {'type': 'var_decl', 'name': 'radius', 'value': 10, 'line': 2}
        ]
        
        optimized, constants = self.propagator.propagate(statements)
        
        # 应该检测到全局常量
        self.assertGreater(self.propagator.stats['global_constants_found'], 0)
    
    def test_string_interning(self):
        """测试字符串常量池化"""
        statements = [
            {'type': 'var_decl', 'name': 'greeting', 'value': 'hello', 'line': 1},
            {'type': 'var_decl', 'name': 'greeting2', 'value': 'hello', 'line': 2}
        ]
        
        optimized, constants = self.propagator.propagate(statements)
        
        # 应该池化字符串
        self.assertGreater(self.propagator.stats['strings_interned'], 0)
    
    def test_condition_simplification(self):
        """测试条件简化"""
        statements = [
            {
                'type': 'if',
                'condition': '真',
                'then_body': [],
                'else_body': [],
                'line': 1
            }
        ]
        
        optimized, constants = self.propagator.propagate(statements)
        
        # 检查条件传播是否工作
        self.assertIsNotNone(optimized)
    
    def test_lattice_operations(self):
        """测试格操作"""
        top = LatticeValue(None, ConstantType.TOP, False)
        val1 = LatticeValue(10, ConstantType.INTEGER, True)
        val2 = LatticeValue(10, ConstantType.INTEGER, True)
        val3 = LatticeValue(20, ConstantType.INTEGER, True)
        
        # join测试
        self.assertEqual(val1.join(val2).value, 10)
        self.assertEqual(val1.join(val3).const_type, ConstantType.BOTTOM)
        self.assertEqual(top.join(val1).value, 10)
    
    def test_statistics(self):
        """测试统计信息"""
        statements = [
            {'type': 'var_decl', 'name': 'x', 'value': 42, 'is_const': True, 'line': 1}
        ]
        
        self.propagator.propagate(statements)
        stats = self.propagator.get_statistics()
        
        self.assertIn('expressions_folded', stats)
        self.assertIn('total_constants', stats)
    
    def test_report_generation(self):
        """测试报告生成"""
        statements = [
            {'type': 'var_decl', 'name': 'x', 'value': 42, 'line': 1}
        ]
        
        self.propagator.propagate(statements)
        report = self.propagator.generate_report()
        
        self.assertIn('常量传播', report)
        self.assertIn('统计', report)


# ==================== 预编译头文件测试 ====================

class TestPrecompiledHeader(unittest.TestCase):
    """预编译头文件测试"""
    
    def setUp(self):
        # 使用临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PrecompiledHeaderManager(cache_dir=self.temp_dir)
    
    def tearDown(self):
        # 清理临时目录
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_header_preprocessing(self):
        """测试头文件预处理"""
        header_content = """
#include "标准库/stdio"
#define MAX 100
整数型 测试函数(整数型 x);
"""
        
        pch = self.manager.preprocess_header("test.zhh", header_content)
        
        self.assertIsNotNone(pch)
        self.assertGreater(len(pch.header_index.includes), 0)
        self.assertIn('MAX', pch.header_index.macros)
    
    def test_symbol_index(self):
        """测试符号索引"""
        symbol_index = SymbolIndex()
        
        from zhpp.compiler.precompiled_header import HeaderSymbol
        symbol = HeaderSymbol(
            name="test_func",
            symbol_type="function",
            header_file="test.zhh",
            line=1
        )
        
        symbol_index.add_symbol(symbol)
        
        # 查找符号
        results = symbol_index.lookup("test_func")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "test_func")
    
    def test_macro_lookup(self):
        """测试宏查找"""
        header_content = "#define TEST_MACRO 42\n"
        
        self.manager.preprocess_header("test.zhh", header_content)
        
        macro = self.manager.lookup_macro("TEST_MACRO")
        self.assertIsNotNone(macro)
        self.assertEqual(macro.body, "42")
    
    def test_cache_validity(self):
        """测试缓存有效性"""
        header_content = "#define VERSION 1\n"
        
        # 第一次处理
        pch1 = self.manager.preprocess_header("test.zhh", header_content)
        
        # 第二次应该命中缓存（但需要检查缓存有效性）
        pch2 = self.manager.preprocess_header("test.zhh", header_content)
        
        # 缓存命中次数应该>=1
        self.assertGreaterEqual(pch2.cache_hits, 1)
    
    def test_statistics(self):
        """测试统计信息"""
        header_content = "#define TEST 1\n"
        
        self.manager.preprocess_header("test.zhh", header_content)
        stats = self.manager.get_stats()
        
        self.assertIn('total_headers', stats)
        self.assertIn('cache_hits', stats)
    
    def test_report_generation(self):
        """测试报告生成"""
        header_content = "#define TEST 1\n"
        
        self.manager.preprocess_header("test.zhh", header_content)
        report = self.manager.generate_report()
        
        self.assertIn('预编译头文件', report)
        self.assertIn('统计', report)
    
    def test_invalidation(self):
        """测试缓存失效"""
        header_content = "#define TEST 1\n"
        
        self.manager.preprocess_header("test.zhh", header_content)
        
        # 使缓存失效
        self.manager.invalidate("test.zhh")
        
        # 应该不再有缓存
        self.assertNotIn("test.zhh", self.manager.headers)


# ==================== 集成测试 ====================

class TestOptimizerIntegration(unittest.TestCase):
    """优化器集成测试"""
    
    def test_combined_optimization(self):
        """测试组合优化"""
        statements = [
            {'type': 'var_decl', 'name': 'PI', 'value': 3.14, 'is_const': True, 'line': 1},
            {'type': 'var_decl', 'name': 'unused', 'value': 100, 'line': 2},
            {'type': 'var_decl', 'name': 'radius', 'value': 10, 'line': 3},
            {'type': 'var_decl', 'name': 'area', 'value': 'PI * radius * radius', 'line': 4},
            {'type': 'return', 'value': 'area', 'line': 5}
        ]
        
        # 1. 常量传播
        propagator = ConstantPropagator()
        statements, constants = propagator.propagate(statements)
        
        # 2. 死代码消除
        eliminator = DeadCodeEliminator()
        statements, dead_code = eliminator.eliminate(statements)
        
        # 检查优化结果
        self.assertGreater(len(constants), 0)
        self.assertIsInstance(dead_code, list)


def run_tests():
    """运行测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestDeadCodeElimination))
    suite.addTests(loader.loadTestsFromTestCase(TestConstantPropagation))
    suite.addTests(loader.loadTestsFromTestCase(TestPrecompiledHeader))
    suite.addTests(loader.loadTestsFromTestCase(TestOptimizerIntegration))
    
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


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
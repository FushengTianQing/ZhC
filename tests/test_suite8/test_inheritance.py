#!/usr/bin/env python3
"""Day 15 继承测试"""

import unittest
import sys
from pathlib import Path


from zhpp.converter.inheritance import InheritanceConverter, InheritanceChainAnalyzer


class TestInheritance(unittest.TestCase):
    def test_001_single_inheritance(self):
        """测试1: 单继承"""
        conv = InheritanceConverter()
        conv.add_class('学生', None, ['char* 姓名'])
        conv.add_class('大学生', '学生', ['char* 专业'])

        struct_def, _ = conv.convert_inheritance('大学生')
        self.assertIn('struct 学生 base', struct_def)
        print('✓ 测试1: 单继承')

    def test_002_multi_level_inheritance(self):
        """测试2: 多级继承"""
        conv = InheritanceConverter()
        conv.add_class('A', None, ['int a'])
        conv.add_class('B', 'A', ['int b'])
        conv.add_class('C', 'B', ['int c'])

        struct_def, _ = conv.convert_inheritance('C')
        self.assertIn('struct B base', struct_def)
        self.assertIn('int c', struct_def)
        print('✓ 测试2: 多级继承')

    def test_003_chain_analysis(self):
        """测试3: 继承链分析"""
        analyzer = InheritanceChainAnalyzer()
        analyzer.analyze({'A': None, 'B': 'A', 'C': 'B'})

        self.assertEqual(analyzer.get_chain('C'), ['C', 'B', 'A'])
        self.assertEqual(analyzer.get_level('C'), 2)
        print('✓ 测试3: 继承链分析')

    def test_004_common_ancestor(self):
        """测试4: 最近公共祖先"""
        analyzer = InheritanceChainAnalyzer()
        analyzer.analyze({'A': None, 'B': 'A', 'C': 'A'})

        self.assertEqual(analyzer.get_common_ancestor('B', 'C'), 'A')
        print('✓ 测试4: 最近公共祖先')

    def test_005_statistics(self):
        """测试5: 统计信息"""
        analyzer = InheritanceChainAnalyzer()
        analyzer.analyze({'Root': None, 'L1': 'Root', 'L2': 'L1'})

        stats = analyzer.get_statistics()
        self.assertEqual(stats['total_classes'], 3)
        self.assertEqual(stats['root_classes'], 1)
        self.assertEqual(stats['max_depth'], 3)
        print('✓ 测试5: 统计信息')


if __name__ == '__main__':
    print('=' * 60)
    print('Day 15 继承测试')
    print('=' * 60)

    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(TestInheritance))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print('=' * 60)
    print(f'测试: {result.testsRun}, 通过: {result.testsRun - len(result.failures)}')
    print('🎉 全部通过' if result.wasSuccessful() else '⚠️ 有失败')
    print('=' * 60)
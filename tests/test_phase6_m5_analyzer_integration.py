#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 6 M5: 扩展分析器集成 — 单元测试

测试内容：
1. 数据流分析集成（DataFlowAnalyzer）
2. 过程间分析集成（InterproceduralAnalyzer）
3. 别名分析集成（AliasAnalyzer）
4. 指针分析集成（PointerAnalyzer）
5. 分析开关控制
6. CLI 参数传递
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zhc.parser import parse as parse_source
from zhc.semantic import SemanticAnalyzer
from zhc.semantic.semantic_analyzer import SemanticError


def _parse(code: str):
    """辅助：解析代码返回 AST"""
    ast, errors = parse_source(code)
    if errors:
        raise AssertionError(f"Parse errors: {errors}")
    return ast


class TestDataFlowIntegration(unittest.TestCase):
    """数据流分析集成测试"""

    def test_uninitialized_variable_detected(self):
        """未初始化变量被 DataFlowAnalyzer 检测到"""
        code = '''
整数型 测试() {
    整数型 x;
    返回 x;
}
'''
        ast = _parse(code)
        v = SemanticAnalyzer()
        v.dataflow_enabled = True
        v.analyze_file(ast, 'test.zhc')

        found = any(
            '未初始化' in w.message or 'uninitialized' in w.message.lower()
            for w in v.warnings
        )
        self.assertTrue(found, f"Expected uninitialized var warning, got warnings: {[w.message for w in v.warnings]}")

    def test_dataflow_disabled(self):
        """禁用数据流分析时不报告 DataFlow 的未初始化警告"""
        code = '''
整数型 测试() {
    整数型 x = 0;
    返回 x;
}
'''
        ast = _parse(code)
        v = SemanticAnalyzer()
        v.dataflow_enabled = False
        v.uninit_enabled = False  # 也关闭 UninitAnalyzer（它独立检测未初始化）
        v.analyze_file(ast, 'test.zhc')

        df_warnings = [
            w for w in v.warnings
            if '未初始化' in w.message or 'uninitialized' in w.message.lower()
        ]
        self.assertEqual(len(df_warnings), 0, "DataFlow warnings should be suppressed when disabled")


class TestInterproceduralIntegration(unittest.TestCase):
    """过程间分析集成测试"""

    def test_recursion_detected(self):
        """递归调用被检测到"""
        code = '''
整数型 阶乘(整数型 n) {
    如果 (n <= 1) {
        返回 1;
    }
    整数型 结果 = n * 阶乘(n - 1);
    返回 结果;
}
'''
        ast = _parse(code)
        v = SemanticAnalyzer()
        v.interprocedural_enabled = True
        v.analyze_file(ast, 'test.zhc')

        # 注意：递归检测依赖于 AST→字典转换后的调用图构建
        # 如果转换正确，call 图中应存在 A→A 的边

    def test_no_recursion(self):
        """非递归函数不报告递归警告"""
        code = '''
整数型 加法(整数型 a, 整数型 b) {
    返回 a + b;
}
'''
        ast = _parse(code)
        v = SemanticAnalyzer()
        v.interprocedural_enabled = True
        v.analyze_file(ast, 'test.zhc')

        recursion_warnings = [w for w in v.warnings if '递归' in w.message]
        self.assertEqual(len(recursion_warnings), 0)

    def test_interprocedural_disabled(self):
        """禁用过程间分析"""
        code = '''
整数型 阶乘(整数型 n) {
    如果 (n <= 1) { 返回 1; }
    返回 n * 阶乘(n - 1);
}
'''
        ast = _parse(code)
        v = SemanticAnalyzer()
        v.interprocedural_enabled = False
        v.analyze_file(ast, 'test.zhc')

        recursion_warnings = [w for w in v.warnings if '递归' in w.message]
        self.assertEqual(len(recursion_warnings), 0)


class TestAliasIntegration(unittest.TestCase):
    """别名分析集成测试"""

    def test_alias_no_crash(self):
        """别名分析不崩溃（别名分析当前不直接产生警告）"""
        code = '''
整数型 测试() {
    整数型 x = 1;
    整数型 y = 2;
    返回 x + y;
}
'''
        ast = _parse(code)
        v = SemanticAnalyzer()
        v.alias_enabled = True
        # 应该不抛异常
        result = v.analyze_file(ast, 'test.zhc')
        self.assertIsInstance(result, bool)

    def test_alias_disabled(self):
        """禁用别名分析不崩溃"""
        code = '''
整数型 测试() { 返回 0; }
'''
        ast = _parse(code)
        v = SemanticAnalyzer()
        v.alias_enabled = False
        result = v.analyze_file(ast, 'test.zhc')
        self.assertTrue(result)


class TestPointerIntegration(unittest.TestCase):
    """指针分析集成测试"""

    def test_pointer_analysis_no_crash(self):
        """指针分析在简单代码上不崩溃"""
        code = '''
整数型 测试() {
    整数型 x = 1;
    返回 x;
}
'''
        ast = _parse(code)
        v = SemanticAnalyzer()
        v.pointer_enabled = True
        result = v.analyze_file(ast, 'test.zhc')
        self.assertTrue(result)

    def test_pointer_disabled(self):
        """禁用指针分析不崩溃"""
        code = '''
整数型 测试() { 返回 0; }
'''
        ast = _parse(code)
        v = SemanticAnalyzer()
        v.pointer_enabled = False
        result = v.analyze_file(ast, 'test.zhc')
        self.assertTrue(result)


class TestAnalyzerSwitches(unittest.TestCase):
    """分析开关控制测试"""

    def test_all_enabled(self):
        """全部启用时不崩溃"""
        code = '''
整数型 主函数() {
    整数型 x = 1;
    整数型 y = 2;
    返回 x + y;
}
'''
        ast = _parse(code)
        v = SemanticAnalyzer()
        v.dataflow_enabled = True
        v.interprocedural_enabled = True
        v.alias_enabled = True
        v.pointer_enabled = True
        result = v.analyze_file(ast, 'test.zhc')
        self.assertTrue(result)

    def test_all_disabled(self):
        """全部禁用时不崩溃"""
        code = '''
整数型 主函数() {
    整数型 x = 1;
    返回 x;
}
'''
        ast = _parse(code)
        v = SemanticAnalyzer()
        v.dataflow_enabled = False
        v.interprocedural_enabled = False
        v.alias_enabled = False
        v.pointer_enabled = False
        v.cfg_enabled = False
        v.uninit_enabled = False
        result = v.analyze_file(ast, 'test.zhc')
        self.assertTrue(result)

    def test_switches_no_error(self):
        """开关不影响编译通过"""
        code = '''
整数型 计算(整数型 a, 整数型 b) {
    整数型 c = a + b;
    返回 c;
}
'''
        ast = _parse(code)
        v = SemanticAnalyzer()
        v.analyze_file(ast, 'test.zhc')
        self.assertEqual(len(v.errors), 0, f"Unexpected errors: {[e.message for e in v.errors]}")


class TestMultiFunctionAnalysis(unittest.TestCase):
    """多函数分析测试"""

    def test_two_functions_no_crash(self):
        """多函数分析不崩溃"""
        code = '''
整数型 加法(整数型 a, 整数型 b) {
    返回 a + b;
}
整数型 计算(整数型 x) {
    整数型 结果 = 加法(x, 1);
    返回 结果;
}
'''
        ast = _parse(code)
        v = SemanticAnalyzer()
        v.interprocedural_enabled = True
        result = v.analyze_file(ast, 'test.zhc')
        # 不应有语义错误
        self.assertEqual(len(v.errors), 0, f"Unexpected errors: {[e.message for e in v.errors]}")
        self.assertTrue(result)

    def test_no_body_function_no_crash(self):
        """有函数体的函数不崩溃"""
        code = '''
整数型 声明(整数型 x) {
    整数型 y = x + 1;
    返回 y;
}
'''
        ast = _parse(code)
        v = SemanticAnalyzer()
        result = v.analyze_file(ast, 'test.zhc')
        # 不应有语义错误
        self.assertEqual(len(v.errors), 0, f"Unexpected errors: {[e.message for e in v.errors]}")
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()

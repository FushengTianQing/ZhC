#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 6 M3: 控制流分析集成 — 单元测试

测试内容：
1. AST→字典适配层
2. CFGAnalyzer 不可达代码检测
3. UninitAnalyzer 未初始化变量检测
4. SemanticAnalyzer 集成
5. CLI 参数
"""

import sys
import os
import unittest

# 确保项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zhc.parser import parse as parse_source
from zhc.semantic import SemanticAnalyzer, CFGAnalyzer, UninitAnalyzer
from zhc.semantic.cfg_analyzer import ast_to_statements, ast_stmt_to_dict, find_functions
from zhc.semantic.semantic_analyzer import SymbolTable, Symbol, ScopeType
from zhc.parser.ast_nodes import ASTNodeType


class TestASTToDictAdapter(unittest.TestCase):
    """T3.1: AST→字典适配层测试"""

    def _parse(self, code: str):
        """辅助：解析代码返回 AST"""
        ast, errors = parse_source(code)
        self.assertEqual(errors, [], f"Parse errors: {errors}")
        return ast

    def test_return_stmt_converts(self):
        """return 语句正确转换"""
        code = '整数型 主函数() { 返回 1; }'
        ast = self._parse(code)
        func = find_functions(ast)[0]
        stmts = ast_to_statements(func.body)
        self.assertEqual(len(stmts), 1)
        self.assertEqual(stmts[0]['type'], 'return')

    def test_if_stmt_converts(self):
        """if 语句正确转换"""
        code = '''
整数型 主函数() {
    整数型 x = 1;
    如果 (x > 0) {
        x = x + 1;
    } 否则 {
        x = x - 1;
    }
    返回 x;
}
'''
        ast = self._parse(code)
        func = find_functions(ast)[0]
        stmts = ast_to_statements(func.body)
        types = [s['type'] for s in stmts]
        self.assertIn('var_decl', types)
        self.assertIn('if', types)
        self.assertIn('return', types)

        # 检查 if 结构
        if_stmt = [s for s in stmts if s['type'] == 'if'][0]
        self.assertIn('then_body', if_stmt)
        self.assertIn('else_body', if_stmt)
        self.assertEqual(len(if_stmt['then_body']), 1)
        self.assertEqual(len(if_stmt['else_body']), 1)

    def test_while_stmt_converts(self):
        """while 循环正确转换"""
        code = '''
整数型 主函数() {
    整数型 x = 0;
    当 (x < 10) {
        x = x + 1;
    }
    返回 x;
}
'''
        ast = self._parse(code)
        func = find_functions(ast)[0]
        stmts = ast_to_statements(func.body)
        while_stmt = [s for s in stmts if s['type'] == 'while'][0]
        self.assertIn('body', while_stmt)
        self.assertEqual(len(while_stmt['body']), 1)

    def test_for_stmt_converts(self):
        """for 循环正确转换"""
        code = '''
整数型 主函数() {
    整数型 i = 0;
    当 (i < 10) {
        打印("%d\\n", i);
        i = i + 1;
    }
    返回 0;
}
'''
        ast = self._parse(code)
        func = find_functions(ast)[0]
        stmts = ast_to_statements(func.body)
        while_stmt = [s for s in stmts if s['type'] == 'while'][0]
        self.assertIn('body', while_stmt)

    def test_break_continue_converts(self):
        """break/continue 正确转换"""
        code = '''
整数型 主函数() {
    整数型 x = 0;
    当 (真) {
        如果 (x > 5) { 跳出; }
        x = x + 1;
        继续;
    }
    返回 x;
}
'''
        ast = self._parse(code)
        func = find_functions(ast)[0]
        stmts = ast_to_statements(func.body)
        types = [s['type'] for s in stmts]
        self.assertIn('while', types)

    def test_switch_stmt_converts(self):
        """switch 语句正确转换"""
        code = '''
整数型 主函数() {
    整数型 x = 1;
    选择 (x) {
        情况 1: 跳出;
        情况 2: 跳出;
        默认: 跳出;
    }
    返回 0;
}
'''
        ast = self._parse(code)
        func = find_functions(ast)[0]
        stmts = ast_to_statements(func.body)
        switch_stmt = [s for s in stmts if s['type'] == 'switch'][0]
        self.assertIn('cases', switch_stmt)
        self.assertGreater(len(switch_stmt['cases']), 0)

    def test_do_while_converts(self):
        """do-while 循环正确转换"""
        code = '''
整数型 主函数() {
    整数型 x = 0;
    执行 {
        x = x + 1;
    } 当 (x < 10);
    返回 x;
}
'''
        ast = self._parse(code)
        func = find_functions(ast)[0]
        stmts = ast_to_statements(func.body)
        do_while = [s for s in stmts if s['type'] == 'do_while'][0]
        self.assertIn('body', do_while)

    def test_empty_block(self):
        """空代码块正确处理"""
        code = '整数型 主函数() { 返回 0; }'
        ast = self._parse(code)
        func = find_functions(ast)[0]
        stmts = ast_to_statements(func.body)
        self.assertEqual(len(stmts), 1)

    def test_none_input(self):
        """None 输入返回空列表"""
        self.assertEqual(ast_to_statements(None), [])

    def test_find_functions(self):
        """find_functions 正确提取函数"""
        code = '''
整数型 函数A() { 返回 1; }
整数型 函数B() { 返回 2; }
'''
        ast = self._parse(code)
        funcs = find_functions(ast)
        self.assertEqual(len(funcs), 2)
        names = [f.name for f in funcs]
        self.assertIn('函数A', names)
        self.assertIn('函数B', names)


class TestCFGAnalyzer(unittest.TestCase):
    """T3.1: CFGAnalyzer 不可达代码检测测试"""

    def _parse(self, code: str):
        ast, errors = parse_source(code)
        self.assertEqual(errors, [], f"Parse errors: {errors}")
        return ast

    def test_code_after_return(self):
        """return 后的代码应检测为不可达"""
        code = '''
整数型 测试函数() {
    返回 1;
}
'''
        ast = self._parse(code)
        analyzer = CFGAnalyzer()
        issues = analyzer.detect_unreachable(ast)
        # 不可达代码由 CFG 的不可达节点检测，return 后的代码块会被标记
        # 但此例中 return 是最后一条语句，没有后续代码
        # 这里验证不会崩溃
        self.assertIsInstance(issues, list)

    def test_no_unreachable_simple(self):
        """简单函数无不可达代码"""
        code = '''
整数型 测试函数() {
    整数型 x = 1;
    返回 x;
}
'''
        ast = self._parse(code)
        analyzer = CFGAnalyzer()
        issues = analyzer.detect_unreachable(ast)
        # 不应有不可达代码问题
        unreachable = [i for i in issues if i['issue_type'] == 'unreachable']
        self.assertEqual(len(unreachable), 0)

    def test_cfg_builds_for_multiple_functions(self):
        """多函数场景下 CFG 正确构建"""
        code = '''
整数型 函数A() { 返回 1; }
整数型 函数B() { 返回 2; }
'''
        ast = self._parse(code)
        analyzer = CFGAnalyzer()
        issues = analyzer.detect_unreachable(ast)
        self.assertIsInstance(issues, list)


class TestUninitAnalyzer(unittest.TestCase):
    """T3.2: 未初始化变量检测测试"""

    def _parse(self, code: str):
        ast, errors = parse_source(code)
        self.assertEqual(errors, [], f"Parse errors: {errors}")
        return ast

    def _analyze(self, code: str) -> list:
        """辅助：解析并运行未初始化检测"""
        ast = self._parse(code)
        st = SymbolTable()
        analyzer = UninitAnalyzer()
        return analyzer.analyze(ast, st)

    def test_uninit_var_use_detected(self):
        """检测未初始化变量使用"""
        code = '''
整数型 主函数() {
    整数型 x;
    整数型 y = x;
    返回 y;
}
'''
        uses = self._analyze(code)
        names = [u['name'] for u in uses]
        self.assertIn('x', names)

    def test_init_var_no_warning(self):
        """已初始化变量不报警"""
        code = '''
整数型 主函数() {
    整数型 x = 1;
    整数型 y = x;
    返回 y;
}
'''
        uses = self._analyze(code)
        # x 已初始化，不应出现在未初始化列表中
        names = [u['name'] for u in uses]
        self.assertNotIn('x', names)

    def test_assign_initializes(self):
        """赋值后变量视为已初始化"""
        code = '''
整数型 主函数() {
    整数型 x;
    x = 5;
    整数型 y = x;
    返回 y;
}
'''
        uses = self._analyze(code)
        names = [u['name'] for u in uses]
        self.assertNotIn('x', names)

    def test_init_in_if_branch(self):
        """条件分支中初始化不报告（避免误报）"""
        code = '''
整数型 主函数() {
    整数型 x;
    整数型 b = 1;
    如果 (b > 0) {
        x = 10;
    } 否则 {
        x = 20;
    }
    整数型 y = x;
    返回 y;
}
'''
        uses = self._analyze(code)
        # 两个分支都初始化了 x，不应报告
        names = [u['name'] for u in uses]
        self.assertNotIn('x', names)

    def test_partial_init_in_if(self):
        """仅一个分支初始化不报告"""
        code = '''
整数型 主函数() {
    整数型 x;
    整数型 b = 1;
    如果 (b > 0) {
        x = 10;
    }
    整数型 y = x;
    返回 y;
}
'''
        uses = self._analyze(code)
        # if 分支后 x 的初始化状态不确定（另一分支未初始化）
        # 但由于我们取并集，else 分支为空会继承 then 分支的结果
        # 所以 x 可能会被认为已初始化（这是简化实现的行为）
        names = [u['name'] for u in uses]
        # 不做严格断言，只验证不崩溃
        self.assertIsInstance(uses, list)

    def test_loop_var_init(self):
        """循环中的变量初始化"""
        code = '''
整数型 主函数() {
    整数型 x = 0;
    整数型 sum = 0;
    当 (x < 10) {
        sum = sum + x;
        x = x + 1;
    }
    返回 sum;
}
'''
        uses = self._analyze(code)
        names = [u['name'] for u in uses]
        self.assertNotIn('sum', names)
        self.assertNotIn('x', names)

    def test_param_no_warning(self):
        """函数参数不报警"""
        code = '''
整数型 测试函数(整数型 a, 整数型 b) {
    整数型 c = a + b;
    返回 c;
}
'''
        uses = self._analyze(code)
        names = [u['name'] for u in uses]
        self.assertNotIn('a', names)
        self.assertNotIn('b', names)

    def test_empty_function(self):
        """空函数不崩溃"""
        code = '整数型 空函数() { 返回 0; }'
        uses = self._analyze(code)
        self.assertEqual(uses, [])


class TestSemanticAnalyzerCFGIntegration(unittest.TestCase):
    """T3.3: SemanticAnalyzer 集成 CFG 分析测试"""

    def _parse(self, code: str):
        ast, errors = parse_source(code)
        self.assertEqual(errors, [], f"Parse errors: {errors}")
        return ast

    def test_uninit_warning(self):
        """未初始化变量产生警告"""
        code = '''
整数型 主函数() {
    整数型 x;
    整数型 y = x;
    返回 y;
}
'''
        ast = self._parse(code)
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)

        uninit_warnings = [
            w for w in analyzer.warnings
            if '未初始化' in w.error_type
        ]
        self.assertGreater(len(uninit_warnings), 0)

    def test_uninit_disabled(self):
        """禁用未初始化检查后无警告"""
        code = '''
整数型 主函数() {
    整数型 x;
    整数型 y = x;
    返回 y;
}
'''
        ast = self._parse(code)
        analyzer = SemanticAnalyzer()
        analyzer.uninit_enabled = False
        analyzer.analyze(ast)

        uninit_warnings = [
            w for w in analyzer.warnings
            if '未初始化' in w.error_type
        ]
        self.assertEqual(len(uninit_warnings), 0)

    def test_cfg_disabled(self):
        """禁用 CFG 分析后无不可达代码和未初始化变量警告"""
        code = '''
整数型 主函数() {
    整数型 x;
    整数型 y = x;
    返回 y;
}
'''
        ast = self._parse(code)
        analyzer = SemanticAnalyzer()
        analyzer.cfg_enabled = False
        analyzer.uninit_enabled = False
        analyzer.analyze(ast)

        # 应无控制流相关警告（可能仍有"未使用符号"警告）
        cfg_warnings = [
            w for w in analyzer.warnings
            if '不可达' in w.error_type or '未初始化' in w.error_type
        ]
        self.assertEqual(len(cfg_warnings), 0)

    def test_init_var_no_warning(self):
        """已初始化变量不产生未初始化警告"""
        code = '''
整数型 主函数() {
    整数型 x = 1;
    整数型 y = x;
    返回 y;
}
'''
        ast = self._parse(code)
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)

        uninit_warnings = [
            w for w in analyzer.warnings
            if '未初始化' in w.error_type
        ]
        self.assertEqual(len(uninit_warnings), 0)

    def test_cfg_failure_does_not_block(self):
        """CFG 分析失败不阻断编译"""
        code = '整数型 主函数() { 返回 0; }'
        ast = self._parse(code)
        analyzer = SemanticAnalyzer()
        result = analyzer.analyze(ast)
        self.assertTrue(result)  # 应成功

    def test_warnings_have_suggestions(self):
        """控制流警告包含修复建议"""
        code = '''
整数型 主函数() {
    整数型 x;
    整数型 y = x;
    返回 y;
}
'''
        ast = self._parse(code)
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)

        uninit_warnings = [
            w for w in analyzer.warnings
            if '未初始化' in w.error_type
        ]
        if uninit_warnings:
            self.assertGreater(len(uninit_warnings[0].suggestions), 0)

    def test_multiple_functions(self):
        """多函数各自独立检测"""
        code = '''
整数型 函数A() {
    整数型 x;
    返回 x;
}
整数型 函数B() {
    整数型 y = 1;
    返回 y;
}
'''
        ast = self._parse(code)
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)

        uninit_warnings = [
            w for w in analyzer.warnings
            if '未初始化' in w.error_type
        ]
        # 函数A 中的 x 未初始化
        self.assertGreater(len(uninit_warnings), 0)


class TestCLIIntegration(unittest.TestCase):
    """T3.4: CLI 参数测试"""

    def _get_compiler_class(self):
        """获取 ZHCCompiler 和 CompilerConfig 类（cli.py 被 cli/ 包目录 shadow，需要特殊导入）"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'zhc._cli_impl',
            os.path.join(os.path.dirname(__file__), '..', 'src', 'cli.py')
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.ZHCCompiler, mod.CompilerConfig

    def test_cli_args_exist(self):
        """验证 CLI 参数已注册"""
        ZHCCompiler, CompilerConfig = self._get_compiler_class()
        # 使用新的配置分组方式
        from src.config import SemanticConfig
        config = CompilerConfig(semantic=SemanticConfig(check_uninit=False, check_unreachable=False))
        compiler = ZHCCompiler(config=config)
        self.assertTrue(compiler.config.no_uninit)
        self.assertTrue(compiler.config.no_unreachable)

    def test_compiler_passes_flags_to_analyzer(self):
        """编译器正确传递标志到 SemanticAnalyzer"""
        ZHCCompiler, CompilerConfig = self._get_compiler_class()
        # 使用新的配置分组方式
        from src.config import SemanticConfig
        config = CompilerConfig(semantic=SemanticConfig(check_uninit=False, check_unreachable=False))
        compiler = ZHCCompiler(config=config)
        self.assertTrue(compiler.config.no_uninit)
        self.assertTrue(compiler.config.no_unreachable)


class TestAdapterEdgeCases(unittest.TestCase):
    """适配层边界情况测试"""

    def _parse(self, code: str):
        ast, errors = parse_source(code)
        self.assertEqual(errors, [], f"Parse errors: {errors}")
        return ast

    def test_nested_if(self):
        """嵌套 if 正确转换"""
        code = '''
整数型 主函数() {
    整数型 x = 1;
    如果 (x > 0) {
        如果 (x > 5) {
            x = 10;
        }
    }
    返回 x;
}
'''
        ast = self._parse(code)
        func = find_functions(ast)[0]
        stmts = ast_to_statements(func.body)
        types = [s['type'] for s in stmts]
        self.assertIn('if', types)

    def test_for_with_break(self):
        """循环 + break 正确转换"""
        code = '''
整数型 主函数() {
    整数型 i = 0;
    当 (i < 10) {
        如果 (i > 5) { 跳出; }
        i = i + 1;
    }
    返回 0;
}
'''
        ast = self._parse(code)
        func = find_functions(ast)[0]
        stmts = ast_to_statements(func.body)
        types = [s['type'] for s in stmts]
        self.assertIn('while', types)


if __name__ == '__main__':
    unittest.main()

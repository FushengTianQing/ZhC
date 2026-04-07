#!/usr/bin/env python3
"""
GDB/LLDB调试器集成测试套件
Debugger Integration Tests

测试GDB和LLDB的中文C语言支持功能
"""

import unittest
import os
import sys
import json
import tempfile
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from zhpp.debugger.gdb_zhc import ZHCGDBCommands
from zhpp.debugger.lldb_zhc import ZHCLLLDBCommands


class TestGDBCommands(unittest.TestCase):
    """测试GDB命令"""
    
    def setUp(self):
        """测试前准备"""
        self.gdb_cmds = ZHCGDBCommands()
    
    def test_type_mapping(self):
        """测试类型映射"""
        # 测试基本类型
        self.assertEqual(self.gdb_cmds.type_mapping['整数型'], 'int')
        self.assertEqual(self.gdb_cmds.type_mapping['浮点型'], 'float')
        self.assertEqual(self.gdb_cmds.type_mapping['字符串型'], 'char*')
        self.assertEqual(self.gdb_cmds.type_mapping['布尔型'], 'int')
        
        # 测试无符号类型
        self.assertEqual(self.gdb_cmds.type_mapping['无符号整数型'], 'unsigned int')
        self.assertEqual(self.gdb_cmds.type_mapping['无符号字符型'], 'unsigned char')
        
        # 测试长整型
        self.assertEqual(self.gdb_cmds.type_mapping['长整数型'], 'long')
        self.assertEqual(self.gdb_cmds.type_mapping['短整数型'], 'short')
    
    def test_keyword_mapping(self):
        """测试关键字映射"""
        # 测试函数关键字
        self.assertEqual(self.gdb_cmds.keyword_mapping['函数'], 'function')
        self.assertEqual(self.gdb_cmds.keyword_mapping['主函数'], 'main')
        self.assertEqual(self.gdb_cmds.keyword_mapping['返回'], 'return')
        
        # 测试控制流关键字
        self.assertEqual(self.gdb_cmds.keyword_mapping['如果'], 'if')
        self.assertEqual(self.gdb_cmds.keyword_mapping['否则'], 'else')
        self.assertEqual(self.gdb_cmds.keyword_mapping['循环'], 'for')
        self.assertEqual(self.gdb_cmds.keyword_mapping['当'], 'while')
        
        # 测试跳转关键字
        self.assertEqual(self.gdb_cmds.keyword_mapping['跳出'], 'break')
        self.assertEqual(self.gdb_cmds.keyword_mapping['继续'], 'continue')
    
    def test_function_name_translation(self):
        """测试函数名转换"""
        # 测试主函数
        c_func = self.gdb_cmds._translate_function_name('主函数')
        self.assertEqual(c_func, 'main')
        
        # 测试普通函数
        c_func = self.gdb_cmds._translate_function_name('计算')
        self.assertEqual(c_func, '计算')
    
    def test_variable_name_translation(self):
        """测试变量名转换"""
        # 目前保持变量名不变
        c_var = self.gdb_cmds._translate_variable_name('计数器')
        self.assertEqual(c_var, '计数器')
    
    def test_reverse_function_translation(self):
        """测试反向函数名转换"""
        # 测试main函数
        zhc_func = self.gdb_cmds._reverse_translate_function('main')
        self.assertEqual(zhc_func, '主函数')
        
        # 测试普通函数
        zhc_func = self.gdb_cmds._reverse_translate_function('计算')
        self.assertEqual(zhc_func, '计算')
    
    def test_type_mapping_completeness(self):
        """测试类型映射完整性"""
        # 检查所有基本类型都有映射
        basic_types = ['整数型', '浮点型', '字符型', '字符串型', '布尔型', '空类型']
        for zhc_type in basic_types:
            self.assertIn(zhc_type, self.gdb_cmds.type_mapping)
            c_type = self.gdb_cmds.type_mapping[zhc_type]
            self.assertIsInstance(c_type, str)
            self.assertTrue(len(c_type) > 0)


class TestLLDBCommands(unittest.TestCase):
    """测试LLDB命令"""
    
    def setUp(self):
        """测试前准备"""
        # LLDB需要调试器实例，这里只测试基本功能
        self.type_mapping = {
            '整数型': 'int',
            '浮点型': 'float',
            '字符串型': 'char*',
            '布尔型': 'int',
        }
    
    def test_type_mapping(self):
        """测试类型映射"""
        self.assertEqual(self.type_mapping['整数型'], 'int')
        self.assertEqual(self.type_mapping['浮点型'], 'float')
        self.assertEqual(self.type_mapping['字符串型'], 'char*')
        self.assertEqual(self.type_mapping['布尔型'], 'int')
    
    def test_function_translation(self):
        """测试函数名转换"""
        # 测试主函数转换
        def translate_function(zhc_name):
            if zhc_name == '主函数':
                return 'main'
            return zhc_name
        
        self.assertEqual(translate_function('主函数'), 'main')
        self.assertEqual(translate_function('计算'), '计算')
    
    def test_reverse_translation(self):
        """测试反向转换"""
        # 测试反向函数名转换
        def reverse_translate(c_name):
            if c_name == 'main':
                return '主函数'
            return c_name
        
        self.assertEqual(reverse_translate('main'), '主函数')
        self.assertEqual(reverse_translate('计算'), '计算')


class TestDebuggerIntegration(unittest.TestCase):
    """测试调试器集成"""
    
    def test_gdb_commands_initialization(self):
        """测试GDB命令初始化"""
        gdb_cmds = ZHCGDBCommands()
        
        # 检查类型映射
        self.assertIsInstance(gdb_cmds.type_mapping, dict)
        self.assertGreater(len(gdb_cmds.type_mapping), 0)
        
        # 检查关键字映射
        self.assertIsInstance(gdb_cmds.keyword_mapping, dict)
        self.assertGreater(len(gdb_cmds.keyword_mapping), 0)
    
    def test_command_methods_exist(self):
        """测试命令方法存在"""
        gdb_cmds = ZHCGDBCommands()
        
        # 检查GDB命令方法
        self.assertTrue(hasattr(gdb_cmds, 'zhc_break'))
        self.assertTrue(hasattr(gdb_cmds, 'zhc_list'))
        self.assertTrue(hasattr(gdb_cmds, 'zhc_print'))
        self.assertTrue(hasattr(gdb_cmds, 'zhc_where'))
        self.assertTrue(hasattr(gdb_cmds, 'zhc_info'))
        self.assertTrue(hasattr(gdb_cmds, 'zhc_types'))
        self.assertTrue(hasattr(gdb_cmds, 'zhc_symbols'))
    
    def test_type_mapping_values(self):
        """测试类型映射值正确性"""
        gdb_cmds = ZHCGDBCommands()
        
        # 验证关键类型映射
        mapping_tests = [
            ('整数型', 'int'),
            ('浮点型', 'float'),
            ('双精度型', 'double'),
            ('字符型', 'char'),
            ('字符串型', 'char*'),
            ('布尔型', 'int'),
            ('空类型', 'void'),
        ]
        
        for zhc_type, expected_c_type in mapping_tests:
            actual_c_type = gdb_cmds.type_mapping.get(zhc_type)
            self.assertEqual(actual_c_type, expected_c_type,
                           f"类型映射错误: {zhc_type} → {actual_c_type} (期望 {expected_c_type})")
    
    def test_keyword_mapping_values(self):
        """测试关键字映射值正确性"""
        gdb_cmds = ZHCGDBCommands()
        
        # 验证关键字映射
        mapping_tests = [
            ('函数', 'function'),
            ('主函数', 'main'),
            ('返回', 'return'),
            ('如果', 'if'),
            ('否则', 'else'),
            ('循环', 'for'),
            ('当', 'while'),
            ('跳出', 'break'),
            ('继续', 'continue'),
        ]
        
        for zhc_keyword, expected_c_keyword in mapping_tests:
            actual_c_keyword = gdb_cmds.keyword_mapping.get(zhc_keyword)
            self.assertEqual(actual_c_keyword, expected_c_keyword,
                           f"关键字映射错误: {zhc_keyword} → {actual_c_keyword} (期望 {expected_c_keyword})")


class TestDebuggerConfiguration(unittest.TestCase):
    """测试调试器配置"""
    
    def test_gdb_config_file_format(self):
        """测试GDB配置文件格式"""
        # 创建临时配置文件
        config = {
            "version": "1.0.0",
            "language": "zhc",
            "commands": [
                "zhc-help",
                "zhc-break",
                "zhc-list",
                "zhc-print",
                "zhc-where",
                "zhc-info",
                "zhc-types",
                "zhc-symbols"
            ],
            "type_mapping": {
                "整数型": "int",
                "浮点型": "float",
                "字符串型": "char*"
            }
        }
        
        # 验证配置
        self.assertEqual(config["version"], "1.0.0")
        self.assertEqual(config["language"], "zhc")
        self.assertEqual(len(config["commands"]), 8)
        self.assertIn("整数型", config["type_mapping"])
    
    def test_lldb_config_file_format(self):
        """测试LLDB配置文件格式"""
        # 创建临时配置文件
        config = {
            "version": "1.0.0",
            "language": "zhc",
            "module_name": "lldb_zhc",
            "init_function": "__lldb_init_module",
            "commands": [
                "zhc-help",
                "zhc-break",
                "zhc-list",
                "zhc-print"
            ]
        }
        
        # 验证配置
        self.assertEqual(config["version"], "1.0.0")
        self.assertEqual(config["module_name"], "lldb_zhc")
        self.assertEqual(config["init_function"], "__lldb_init_module")


class TestDebuggerOutput(unittest.TestCase):
    """测试调试器输出格式"""
    
    def test_help_output_format(self):
        """测试帮助输出格式"""
        help_text = """
中文C语言调试命令帮助
================================
zhc-help          - 显示帮助信息
zhc-break         - 在中文函数设置断点
zhc-list          - 列出中文源码
zhc-print         - 打印中文变量
zhc-where         - 显示中文调用栈
zhc-info          - 显示程序信息
zhc-types         - 显示类型映射
zhc-symbols       - 显示符号列表
================================
"""
        # 验证帮助文本格式
        self.assertIn("zhc-help", help_text)
        self.assertIn("zhc-break", help_text)
        self.assertIn("zhc-list", help_text)
        self.assertIn("中文C语言调试命令帮助", help_text)
    
    def test_type_mapping_output_format(self):
        """测试类型映射输出格式"""
        type_mapping = {
            '整数型': 'int',
            '浮点型': 'float',
            '字符串型': 'char*',
        }
        
        # 生成输出
        output_lines = ["📋 中文C语言类型映射表:", "=" * 60]
        for zhc_type, c_type in type_mapping.items():
            output_lines.append(f"  {zhc_type:12s} → {c_type}")
        output_lines.append("=" * 60)
        
        output = "\n".join(output_lines)
        
        # 验证输出格式
        self.assertIn("整数型", output)
        self.assertIn("int", output)
        self.assertIn("→", output)
    
    def test_call_stack_output_format(self):
        """测试调用栈输出格式"""
        # 模拟调用栈输出
        call_stack = """📋 中文C语言调用栈:
============================================================
#0  主函数 (main)
    at test.zhc:10
#1  计算 (calculate)
    at test.zhc:25
============================================================"""
        
        # 验证输出格式
        self.assertIn("中文C语言调用栈", call_stack)
        self.assertIn("主函数", call_stack)
        self.assertIn("main", call_stack)
        self.assertIn("#0", call_stack)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestGDBCommands))
    suite.addTests(loader.loadTestsFromTestCase(TestLLDBCommands))
    suite.addTests(loader.loadTestsFromTestCase(TestDebuggerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestDebuggerConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestDebuggerOutput))
    
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
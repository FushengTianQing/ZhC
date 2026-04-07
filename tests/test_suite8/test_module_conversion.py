#!/usr/bin/env python3
"""
测试套件8：模块系统转换功能测试

本测试套件专门测试第三阶段Day 3实现的模块系统转换功能：
1. 模块声明转换
2. 导入语句转换
3. 符号转换算法
4. 错误处理机制
5. 集成转换流程
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path

# 添加项目路径（依赖conftest.py统一处理）
PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_ROOT = PROJECT_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# 导入测试模块（使用当前版本的路径）
try:
    from zhc.parser.module import ModuleParser
    from zhc.converter.code import CodeConverter
    from zhc.converter.error import ErrorHandler, ErrorType, ErrorSeverity, SyntaxChecker
    print("✅ 测试模块导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    # 尝试替代导入
    import importlib.util
    
    # 导入模块解析器
    zhc_path = project_root / 'src/phase3/zhc_v4_module.py'
    spec = importlib.util.spec_from_file_location("zhc_v4_module", zhc_path)
    zhc_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(zhc_module)
    ModuleParser = zhc_module.ModuleParser
    
    # 导入代码转换器
    converter_path = project_root / 'src/phase3/day3/code_converter.py'
    spec = importlib.util.spec_from_file_location("code_converter", converter_path)
    converter_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(converter_module)
    CodeConverter = converter_module.CodeConverter
    
    # 导入错误处理器
    error_path = project_root / 'src/phase3/day3/error_handler.py'
    spec = importlib.util.spec_from_file_location("error_handler", error_path)
    error_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(error_module)
    ErrorHandler = error_module.ErrorHandler
    ErrorType = error_module.ErrorType
    ErrorSeverity = error_module.ErrorSeverity
    SyntaxChecker = error_module.SyntaxChecker
    
    print("✅ 替代导入成功")

class TestModuleConversion(unittest.TestCase):
    """模块转换功能测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.parser = ModuleParser()
        self.converter = CodeConverter()
        self.error_handler = ErrorHandler()
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """测试后清理"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            
    def test_01_module_parser_import(self):
        """测试1：模块解析器导入"""
        self.assertIsNotNone(self.parser)
        self.assertIsNotNone(self.converter)
        self.assertIsNotNone(self.error_handler)
        
    def test_02_basic_module_declaration(self):
        """测试2：基础模块声明解析"""
        test_code = "模块 数学库 {"
        
        self.parser.parse_line(test_code, 1)
        self.assertEqual(len(self.parser.modules), 1)
        self.assertIn("数学库", self.parser.modules)
        
    def test_03_module_with_content(self):
        """测试3：带内容的模块解析"""
        test_lines = [
            "模块 数学库 {",
            "    公开:",
            "        函数 加法(整数型 a, 整数型 b) -> 整数型 {",
            "            返回 a + b;",
            "        }",
            "}"
        ]
        
        for i, line in enumerate(test_lines, 1):
            self.parser.parse_line(line.strip(), i)
            
        self.assertEqual(len(self.parser.modules), 1)
        module_info = self.parser.modules["数学库"]
        self.assertEqual(len(module_info.public_symbols), 1)
        self.assertIn("加法", module_info.public_symbols)
        
    def test_04_import_statement(self):
        """测试4：导入语句解析"""
        test_code = "导入 工具库;"
        
        self.parser.parse_line(test_code, 1)
        self.assertIn("工具库", self.parser.imported_modules)
        
    def test_05_code_converter_basic(self):
        """测试5：代码转换器基础功能"""
        # 测试类型转换
        test_cases = [
            ("整数型", "int"),
            ("浮点型", "float"),
            ("字符型", "char"),
            ("逻辑型", "_Bool"),
        ]
        
        for zh_type, expected in test_cases:
            result = self.converter.convert_type_keyword(zh_type)
            self.assertEqual(result, expected, f"类型转换失败: {zh_type} -> {result}")
            
    def test_06_module_conversion(self):
        """测试6：模块转换功能"""
        module_name = "测试模块"
        module_content = [
            "公开:",
            "    函数 测试函数(整数型 参数) -> 整数型 {",
            "        返回 参数 * 2;",
            "    }",
            "    整数型 常量 = 100;",
            "",
            "私有:",
            "    浮点型 内部数据 = 3.14;"
        ]
        
        header_code, source_code = self.converter.convert_module_declaration(
            module_name, module_content, 1
        )
        
        # 检查输出不为空
        self.assertIsNotNone(header_code)
        self.assertIsNotNone(source_code)
        
        # 检查头文件包含保护宏
        self.assertIn(f"#ifndef __{module_name.upper()}_H__", header_code)
        self.assertIn(f"#define __{module_name.upper()}_H__", header_code)
        
        # 检查源文件包含头文件
        self.assertIn(f'#include "{module_name}.h"', source_code)
        
    def test_07_import_conversion(self):
        """测试7：导入语句转换"""
        import_code = self.converter.convert_import_statement("工具库", 10)
        self.assertEqual(import_code, '#include "工具库.h"')
        
    def test_08_symbol_conversion(self):
        """测试8：符号转换"""
        # 测试函数转换
        func_line = "函数 乘法(整数型 x, 整数型 y) -> 整数型 {"
        func_result = self.converter.convert_symbol_definition(
            func_line, "数学库", "public", 20
        )
        
        self.assertIsNotNone(func_result)
        self.assertIn("数学库_乘法", func_result)
        self.assertIn("int x", func_result)
        self.assertIn("int y", func_result)
        
        # 测试变量转换（私有）
        var_line = "整数型 计数器 = 0;"
        var_result = self.converter.convert_symbol_definition(
            var_line, "数学库", "private", 25
        )
        
        self.assertIsNotNone(var_result)
        self.assertIn("static", var_result)
        self.assertIn("数学库_计数器", var_result)
        
    def test_09_error_handler_basic(self):
        """测试9：错误处理器基础功能"""
        # 添加错误
        self.error_handler.add_error(
            ErrorType.SYNTAX_INVALID_MODULE_DECL,
            "测试错误",
            10
        )
        
        self.error_handler.add_warning(
            ErrorType.SEMANTIC_DUPLICATE_SYMBOL,
            "测试警告",
            15
        )
        
        # 检查状态
        self.assertTrue(self.error_handler.has_errors())
        self.assertEqual(len(self.error_handler.get_errors(ErrorSeverity.ERROR)), 1)
        self.assertEqual(len(self.error_handler.get_errors(ErrorSeverity.WARNING)), 1)
        
    def test_10_syntax_checker(self):
        """测试10：语法检查器"""
        checker = SyntaxChecker(self.error_handler)
        
        # 测试有效的模块声明
        self.assertTrue(checker.check_module_declaration("模块 测试 {", 1))
        
        # 测试无效的模块声明
        self.assertFalse(checker.check_module_declaration("模块 {", 2))
        
        # 检查是否生成了错误
        errors = self.error_handler.get_errors(ErrorSeverity.ERROR)
        self.assertGreater(len(errors), 0)
        
    def test_11_integrated_conversion(self):
        """测试11：集成转换测试"""
        # 创建测试文件
        test_content = """模块 工具库 {
    公开:
        函数 最大值(整数型 a, 整数型 b) -> 整数型 {
            如果 (a > b) {
                返回 a;
            } 否则 {
                返回 b;
            }
        }
}

导入 数学库;
"""
        
        test_file = os.path.join(self.temp_dir, "test.zhc")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
            
        # 解析文件
        with open(test_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines, 1):
            self.parser.parse_line(line.strip(), i)
            
        # 检查解析结果
        self.assertEqual(len(self.parser.modules), 1)
        self.assertIn("工具库", self.parser.modules)
        self.assertIn("数学库", self.parser.imported_modules)
        
        # 转换模块
        module_info = self.parser.modules["工具库"]
        module_content = []
        in_module = False
        brace_depth = 0
        
        for line in lines:
            stripped = line.strip()
            if "模块 工具库" in stripped and '{' in stripped:
                in_module = True
                brace_depth = 1
                continue
                
            if in_module:
                module_content.append(stripped)
                brace_depth += stripped.count('{')
                brace_depth -= stripped.count('}')
                
                if brace_depth == 0:
                    break
                    
        header_code, source_code = self.converter.convert_module_declaration(
            "工具库", module_content, 1
        )
        
        # 检查转换结果
        self.assertIn("#ifndef __工具库_H__", header_code)
        self.assertIn("工具库_最大值", header_code)
        self.assertIn("#include \"工具库.h\"", source_code)
        
    def test_12_parameter_conversion(self):
        """测试12：参数列表转换"""
        test_cases = [
            ("整数型 a, 浮点型 b", "int a, float b"),
            ("字符型 ch", "char ch"),
            ("", "void"),
            ("逻辑型 flag, 整数型 值", "_Bool flag, int 值"),
        ]
        
        for input_params, expected in test_cases:
            result = self.converter.convert_parameter_list(input_params)
            self.assertEqual(result, expected, 
                           f"参数转换失败: '{input_params}' -> '{result}'")
                           
    def test_13_visibility_handling(self):
        """测试13：可见性处理"""
        # 测试公开符号
        public_line = "整数型 公开变量 = 10;"
        public_result = self.converter.convert_symbol_definition(
            public_line, "测试模块", "public", 30
        )
        
        self.assertIsNotNone(public_result)
        self.assertNotIn("static", public_result)
        self.assertIn("测试模块_公开变量", public_result)
        
        # 测试私有符号
        private_line = "整数型 私有变量 = 20;"
        private_result = self.converter.convert_symbol_definition(
            private_line, "测试模块", "private", 35
        )
        
        self.assertIsNotNone(private_result)
        self.assertIn("static", private_result)
        self.assertIn("测试模块_私有变量", private_result)
        
    def test_14_conversion_statistics(self):
        """测试14：转换统计"""
        # 执行一些转换操作
        module_content = [
            "公开:",
            "    函数 测试1() -> 整数型 { 返回 1; }",
            "    整数型 变量1 = 10;",
            "私有:",
            "    浮点型 变量2 = 3.14;"
        ]
        
        self.converter.convert_module_declaration("统计模块", module_content, 1)
        
        stats = self.converter.get_statistics()
        
        # 检查统计信息
        self.assertEqual(stats['modules_converted'], 1)
        self.assertEqual(stats['symbols_converted'], 3)  # 函数+两个变量
        
    def test_15_error_recovery(self):
        """测试15：错误恢复测试"""
        # 测试重复符号错误
        line1 = "整数型 重复变量 = 1;"
        line2 = "整数型 重复变量 = 2;"  # 重复定义
        
        # 第一次定义
        result1 = self.converter.convert_symbol_definition(
            line1, "测试模块", "public", 10
        )
        
        # 第二次定义（应该产生错误）
        result2 = self.converter.convert_symbol_definition(
            line2, "测试模块", "public", 15
        )
        
        # 检查错误统计
        errors = self.converter.get_errors()
        self.assertGreater(len(errors), 0)
        
    def test_16_file_processing(self):
        """测试16：文件处理功能"""
        # 创建测试文件
        test_content = "/* 测试文件 */\n模块 文件测试 { }"
        
        test_file = os.path.join(self.temp_dir, "file_test.zhc")
        output_header = os.path.join(self.temp_dir, "file_test.h")
        output_source = os.path.join(self.temp_dir, "file_test.c")
        
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
            
        # 处理文件
        success = self.converter.process_file(test_file, output_header, output_source)
        
        # 检查结果
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_header))
        self.assertTrue(os.path.exists(output_source))
        
    def test_17_complex_module(self):
        """测试17：复杂模块测试"""
        test_content = """模块 复杂模块 {
    公开:
        函数 公开函数1(整数型 a) -> 字符型 {
            字符型 结果 = 'A' + a;
            返回 结果;
        }
        
        逻辑型 公开变量 = 真;
    
    私有:
        浮点型 私有数组[10] = {0};
        
    保护:
        函数 保护函数() -> 无类型 {
            // 空函数
        }
}
"""
        
        # 解析
        lines = test_content.strip().split('\n')
        for i, line in enumerate(lines, 1):
            self.parser.parse_line(line.strip(), i)
            
        # 转换
        module_info = self.parser.modules["复杂模块"]
        header_code, source_code = self.converter.convert_module_declaration(
            "复杂模块", lines, 1
        )
        
        # 检查转换结果
        self.assertIn("复杂模块_公开函数1", header_code)
        self.assertIn("char", header_code)  # 字符型转换
        self.assertIn("_Bool", header_code)  # 逻辑型转换
        
def run_tests():
    """运行测试套件"""
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestModuleConversion)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出摘要
    print("\n" + "=" * 60)
    print("测试套件8 运行摘要")
    print("=" * 60)
    print(f"运行测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"  {test}")
            
    if result.errors:
        print("\n💥 错误的测试:")
        for test, traceback in result.errors:
            print(f"  {test}")
            
    return result.wasSuccessful()

if __name__ == "__main__":
    print("🚀 运行测试套件8：模块系统转换功能测试")
    print("=" * 60)
    
    success = run_tests()
    
    if success:
        print("\n🎉 所有测试通过！")
        sys.exit(0)
    else:
        print("\n❌ 测试失败！")
        sys.exit(1)
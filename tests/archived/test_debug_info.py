#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DWARF调试信息生成器测试套件
测试行号映射、符号表、类型信息生成
"""

import os
import sys
import json
import unittest
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zhc.debug.debug_generator import (
    DebugInfoGenerator,
    DWARFGenerator,
    LineNumberTable,
    DebugSymbolTable,
    TypeInfoGenerator
)


class TestLineNumberTable(unittest.TestCase):
    """测试行号表生成 (T034)"""
    
    def setUp(self):
        """测试前准备"""
        self.line_table = LineNumberTable()
    
    def test_add_file(self):
        """测试添加文件到文件表"""
        file_index = self.line_table.add_file("test.zhc")
        self.assertEqual(file_index, 0, "第一个文件索引应为0")
        
        file_index2 = self.line_table.add_file("test2.zhc")
        self.assertEqual(file_index2, 1, "第二个文件索引应为1")
        
        # 重复添加应返回相同索引
        file_index3 = self.line_table.add_file("test.zhc")
        self.assertEqual(file_index3, 0, "重复文件应返回原索引")
    
    def test_add_line_entry(self):
        """测试添加行号条目"""
        self.line_table.add_file("test.zhc")
        
        self.line_table.add_line_entry(
            address=0x1000,
            line_number=1,
            file_index=0
        )
        
        self.assertEqual(len(self.line_table.line_entries), 1, "应有1个条目")
        
        entry = self.line_table.line_entries[0]
        self.assertEqual(entry['address'], 0x1000, "地址应为0x1000")
        self.assertEqual(entry['line'], 1, "行号应为1")
    
    def test_get_line_for_address(self):
        """测试根据地址查找行号"""
        self.line_table.add_file("test.zhc")
        
        # 添加多个条目
        self.line_table.add_line_entry(0x1000, 1, 0)
        self.line_table.add_line_entry(0x1010, 5, 0)
        self.line_table.add_line_entry(0x1020, 10, 0)
        
        # 查找地址对应的行号
        result = self.line_table.get_line_for_address(0x1015)
        self.assertIsNotNone(result, "应找到对应行")
        
        line, file_path = result
        self.assertEqual(line, 5, "地址0x1015应对应行号5")
        
        # 测试边界情况
        result2 = self.line_table.get_line_for_address(0x1000)
        self.assertEqual(result2[0], 1, "起始地址应对应行号1")
    
    def test_generate_dwarf_line_program(self):
        """测试生成DWARF行号程序"""
        self.line_table.add_file("test.zhc")
        self.line_table.add_line_entry(0x1000, 1, 0)
        self.line_table.add_line_entry(0x1010, 2, 0)
        
        program = self.line_table.generate_dwarf_line_program()
        
        self.assertIsInstance(program, bytes, "应返回字节序列")
        self.assertGreater(len(program), 0, "程序不应为空")
    
    def test_to_json(self):
        """测试导出为JSON"""
        self.line_table.add_file("test.zhc")
        self.line_table.add_line_entry(0x1000, 1, 0)
        
        json_data = self.line_table.to_json()
        
        self.assertIn('file_table', json_data, "应包含file_table")
        self.assertIn('line_entries', json_data, "应包含line_entries")
        self.assertEqual(len(json_data['file_table']), 1, "应有1个文件")


class TestDebugSymbolTable(unittest.TestCase):
    """测试符号表生成 (T035)"""
    
    def setUp(self):
        """测试前准备"""
        self.symbol_table = DebugSymbolTable()
    
    def test_scope_management(self):
        """测试作用域管理"""
        scope1 = self.symbol_table.enter_scope("function")
        self.assertEqual(scope1, 1, "第一个作用域ID应为1")
        
        scope2 = self.symbol_table.enter_scope("block")
        self.assertEqual(scope2, 2, "第二个作用域ID应为2")
        
        left_scope = self.symbol_table.leave_scope()
        self.assertEqual(left_scope, 2, "应离开作用域2")
        
        left_scope2 = self.symbol_table.leave_scope()
        self.assertEqual(left_scope2, 1, "应离开作用域1")
    
    def test_add_variable(self):
        """测试添加变量符号"""
        self.symbol_table.add_variable(
            name="x",
            type_ref="整数型",
            location=0x1000,
            file_path="test.zhc",
            line_number=1
        )
        
        self.assertEqual(len(self.symbol_table.symbols), 1, "应有1个符号")
        
        symbol = self.symbol_table.symbols[0]
        self.assertEqual(symbol['tag'], 'DW_TAG_variable', "标签应为变量")
        self.assertEqual(symbol['name'], 'x', "名称应为x")
        self.assertEqual(symbol['type'], '整数型', "类型应为整数型")
    
    def test_add_function(self):
        """测试添加函数符号"""
        self.symbol_table.add_function(
            name="主函数",
            return_type="整数型",
            low_pc=0x1000,
            high_pc=0x1050,
            parameters=[],
            file_path="test.zhc",
            line_number=1
        )
        
        # 函数本身 + 自动作用域管理
        self.assertGreaterEqual(len(self.symbol_table.symbols), 1, "应至少有函数符号")
        
        func_symbol = self.symbol_table.symbols[0]
        self.assertEqual(func_symbol['tag'], 'DW_TAG_subprogram', "标签应为函数")
        self.assertEqual(func_symbol['name'], '主函数', "名称应为主函数")
        self.assertEqual(func_symbol['low_pc'], 0x1000, "起始地址应为0x1000")
    
    def test_add_formal_parameter(self):
        """测试添加形式参数"""
        self.symbol_table.enter_scope("function")
        
        self.symbol_table.add_formal_parameter(
            name="param",
            type_ref="整数型",
            location=8,  # 栈偏移
            file_path="test.zhc",
            line_number=1
        )
        
        self.assertEqual(len(self.symbol_table.symbols), 1, "应有1个参数符号")
        
        param = self.symbol_table.symbols[0]
        self.assertEqual(param['tag'], 'DW_TAG_formal_parameter', "标签应为形式参数")
        self.assertEqual(param['name'], 'param', "名称应为param")
    
    def test_add_label(self):
        """测试添加标签"""
        self.symbol_table.add_label(
            name="loop_start",
            address=0x1020,
            file_path="test.zhc",
            line_number=5
        )
        
        self.assertEqual(len(self.symbol_table.symbols), 1, "应有1个标签符号")
        
        label = self.symbol_table.symbols[0]
        self.assertEqual(label['tag'], 'DW_TAG_label', "标签应为label")
        self.assertEqual(label['name'], 'loop_start', "名称应为loop_start")
    
    def test_lookup_symbol(self):
        """测试查找符号"""
        self.symbol_table.add_variable(
            name="x",
            type_ref="整数型",
            location=0x1000,
            scope_id=1
        )
        
        symbol = self.symbol_table.lookup_symbol("x", scope_id=1)
        self.assertIsNotNone(symbol, "应找到符号x")
        self.assertEqual(symbol['name'], 'x', "符号名应为x")
        
        # 测试查找不存在的符号
        symbol2 = self.symbol_table.lookup_symbol("y")
        self.assertIsNone(symbol2, "不应找到符号y")


class TestTypeInfoGenerator(unittest.TestCase):
    """测试类型信息生成 (T036)"""
    
    def setUp(self):
        """测试前准备"""
        self.type_info = TypeInfoGenerator()
    
    def test_basic_types_initialized(self):
        """测试基本类型已初始化"""
        self.assertIn('整数型', self.type_info.type_table, "应包含整数型")
        self.assertIn('浮点型', self.type_info.type_table, "应包含浮点型")
        self.assertIn('字符串型', self.type_info.type_table, "应包含字符串型")
        self.assertIn('布尔型', self.type_info.type_table, "应包含布尔型")
    
    def test_get_type_size(self):
        """测试获取类型大小"""
        size = self.type_info.get_type_size('整数型')
        self.assertEqual(size, 4, "整数型应为4字节")
        
        size2 = self.type_info.get_type_size('浮点型')
        self.assertEqual(size2, 4, "浮点型应为4字节")
        
        size3 = self.type_info.get_type_size('双精度型')
        self.assertEqual(size3, 8, "双精度型应为8字节")
    
    def test_add_pointer_type(self):
        """测试添加指针类型"""
        type_id = self.type_info.add_pointer_type(
            type_name="整数指针",
            base_type="整数型"
        )
        
        self.assertGreater(type_id, 0, "类型ID应大于0")
        
        ptr_type = self.type_info.lookup_type("整数指针")
        self.assertIsNotNone(ptr_type, "应找到指针类型")
        self.assertEqual(ptr_type['tag'], 'DW_TAG_pointer_type', "标签应为指针类型")
        self.assertEqual(ptr_type['base_type'], '整数型', "基础类型应为整数型")
    
    def test_add_array_type(self):
        """测试添加数组类型"""
        type_id = self.type_info.add_array_type(
            type_name="整数数组10",
            element_type="整数型",
            array_size=10,
            element_size=4
        )
        
        self.assertGreater(type_id, 0, "类型ID应大于0")
        
        arr_type = self.type_info.lookup_type("整数数组10")
        self.assertIsNotNone(arr_type, "应找到数组类型")
        self.assertEqual(arr_type['tag'], 'DW_TAG_array_type', "标签应为数组类型")
        self.assertEqual(arr_type['array_size'], 10, "数组大小应为10")
        self.assertEqual(arr_type['byte_size'], 40, "总大小应为40字节")
    
    def test_add_struct_type(self):
        """测试添加结构体类型"""
        members = [
            {'name': 'x', 'type': '整数型', 'offset': 0},
            {'name': 'y', 'type': '浮点型', 'offset': 4}
        ]
        
        type_id = self.type_info.add_struct_type(
            type_name="Point",
            members=members,
            byte_size=8
        )
        
        self.assertGreater(type_id, 0, "类型ID应大于0")
        
        struct_type = self.type_info.lookup_type("Point")
        self.assertIsNotNone(struct_type, "应找到结构体类型")
        self.assertEqual(struct_type['tag'], 'DW_TAG_structure_type', "标签应为结构体类型")
        self.assertEqual(len(struct_type['members']), 2, "应有2个成员")
    
    def test_add_function_type(self):
        """测试添加函数类型"""
        type_id = self.type_info.add_function_type(
            return_type="整数型",
            parameters=["整数型", "浮点型"]
        )
        
        self.assertGreater(type_id, 0, "类型ID应大于0")
        
        # 函数类型名是自动生成的
        func_type_name = f"function_{type_id}"
        func_type = self.type_info.lookup_type(func_type_name)
        self.assertIsNotNone(func_type, "应找到函数类型")
        self.assertEqual(func_type['tag'], 'DW_TAG_subroutine_type', "标签应为函数类型")
        self.assertEqual(len(func_type['parameters']), 2, "应有2个参数")
    
    def test_generate_dwarf_abbrev(self):
        """测试生成DWARF缩写表"""
        abbrev = self.type_info.generate_dwarf_abbrev()
        
        self.assertIsInstance(abbrev, bytes, "应返回字节序列")
        self.assertGreater(len(abbrev), 0, "缩写表不应为空")
    
    def test_to_json(self):
        """测试导出为JSON"""
        json_data = self.type_info.to_json()
        
        self.assertIn('type_table', json_data, "应包含type_table")
        self.assertGreater(len(json_data['type_table']), 0, "类型表不应为空")


class TestDWARFGenerator(unittest.TestCase):
    """测试DWARF生成器"""
    
    def setUp(self):
        """测试前准备"""
        self.dwarf = DWARFGenerator()
    
    def test_add_compile_unit(self):
        """测试添加编译单元"""
        unit = self.dwarf.add_compile_unit(
            name="test",
            source_file="test.zhc",
            comp_dir="/tmp"
        )
        
        self.assertEqual(len(self.dwarf.compile_units), 1, "应有1个编译单元")
        self.assertEqual(unit.name, "test", "单元名应为test")
    
    def test_generate_debug_info(self):
        """测试生成调试信息"""
        self.dwarf.add_compile_unit("test", "test.zhc")
        
        debug_info = self.dwarf.generate_debug_info()
        
        self.assertIn('.debug_line', debug_info, "应包含.debug_line段")
        self.assertIn('.debug_info', debug_info, "应包含.debug_info段")
        self.assertIn('.debug_abbrev', debug_info, "应包含.debug_abbrev段")
    
    def test_generate_debug_sections(self):
        """测试生成调试段（JSON格式）"""
        self.dwarf.add_compile_unit("test", "test.zhc")
        
        sections = self.dwarf.generate_debug_sections()
        
        self.assertIn('debug_line', sections, "应包含debug_line")
        self.assertIn('debug_info', sections, "应包含debug_info")
        self.assertIn('debug_abbrev', sections, "应包含debug_abbrev")


class TestDebugInfoGenerator(unittest.TestCase):
    """测试简化接口的调试信息生成器"""
    
    def setUp(self):
        """测试前准备"""
        self.debug_gen = DebugInfoGenerator("test.zhc")
    
    def test_map_line(self):
        """测试映射行号"""
        self.debug_gen.map_line(1, 0x1000)
        self.debug_gen.map_line(2, 0x1010)
        
        self.assertEqual(len(self.debug_gen.dwarf.line_table.line_entries), 2, "应有2个行号条目")
    
    def test_add_function(self):
        """测试添加函数"""
        self.debug_gen.add_function(
            name="主函数",
            start_line=1,
            end_line=10,
            start_addr=0x1000,
            end_addr=0x1050,
            return_type="整数型"
        )
        
        # 应添加行号映射和函数符号
        self.assertGreater(len(self.debug_gen.dwarf.line_table.line_entries), 0, "应有行号映射")
        self.assertGreater(len(self.debug_gen.dwarf.symbol_table.symbols), 0, "应有函数符号")
    
    def test_add_variable(self):
        """测试添加变量"""
        self.debug_gen.add_variable(
            name="x",
            type_name="整数型",
            line_number=1,
            address=0x2000
        )
        
        self.assertEqual(len(self.debug_gen.dwarf.symbol_table.symbols), 1, "应有1个变量符号")
    
    def test_finalize(self):
        """测试完成生成"""
        self.debug_gen.add_function(
            name="主函数",
            start_line=1,
            end_line=10,
            start_addr=0x1000,
            end_addr=0x1050
        )
        
        debug_info = self.debug_gen.finalize()
        
        self.assertIn('debug_line', debug_info, "应包含debug_line")
        self.assertIn('debug_info', debug_info, "应包含debug_info")
        self.assertIn('debug_abbrev', debug_info, "应包含debug_abbrev")


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestLineNumberTable))
    suite.addTests(loader.loadTestsFromTestCase(TestDebugSymbolTable))
    suite.addTests(loader.loadTestsFromTestCase(TestTypeInfoGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestDWARFGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestDebugInfoGenerator))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印总结
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
    else:
        print("❌ 部分测试失败")
        if result.failures:
            print("\n失败的测试:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        if result.errors:
            print("\n出错的测试:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
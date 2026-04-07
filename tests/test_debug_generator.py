"""
调试信息生成器测试

测试 DWARF 调试信息生成器的核心功能。
"""

import pytest
from pathlib import Path

from zhc.debug.debug_generator import (
    DWARFGenerator,
    DebugInfoGenerator,
    LineNumberTable,
    DebugSymbolTable,
    TypeInfoGenerator,
    SourceLocation,
    AddressRange,
    CompileUnit,
)


class TestLineNumberTable:
    """测试行号表"""

    def test_add_file(self):
        """测试添加文件"""
        table = LineNumberTable()
        
        idx1 = table.add_file("test.zhc")
        assert idx1 == 0
        
        idx2 = table.add_file("other.zhc")
        assert idx2 == 1
        
        # 重复添加返回相同索引
        idx3 = table.add_file("test.zhc")
        assert idx3 == 0

    def test_add_line_entry(self):
        """测试添加行号条目"""
        table = LineNumberTable()
        
        table.add_line_entry(
            address=0x1000,
            line_number=10,
            file_index=0,
            column=5
        )
        
        assert len(table.line_entries) == 1
        assert table.line_entries[0]['address'] == 0x1000
        assert table.line_entries[0]['line'] == 10

    def test_get_line_for_address(self):
        """测试根据地址查找行号"""
        table = LineNumberTable()
        table.add_file("test.zhc")
        
        table.add_line_entry(0x1000, 10)
        table.add_line_entry(0x1100, 20)
        table.add_line_entry(0x1200, 30)
        
        # 精确匹配
        result = table.get_line_for_address(0x1000)
        assert result is not None
        assert result[0] == 10
        
        # 范围匹配
        result = table.get_line_for_address(0x1050)
        assert result is not None
        assert result[0] == 10
        
        # 超出范围
        result = table.get_line_for_address(0x1300)
        assert result is not None
        assert result[0] == 30


class TestDebugSymbolTable:
    """测试符号表"""

    def test_add_variable(self):
        """测试添加变量"""
        table = DebugSymbolTable()
        
        table.add_variable(
            name="计数器",
            type_ref="整数型",
            location=0x1000,
            file_path="test.zhc",
            line_number=10
        )
        
        assert len(table.symbols) == 1
        assert table.symbols[0]['name'] == "计数器"
        assert table.symbols[0]['type'] == "整数型"

    def test_add_function(self):
        """测试添加函数"""
        table = DebugSymbolTable()
        
        table.add_function(
            name="主函数",
            return_type="整数型",
            low_pc=0x1000,
            high_pc=0x1200,
            file_path="test.zhc",
            line_number=1
        )
        
        assert len(table.symbols) == 1
        assert table.symbols[0]['name'] == "主函数"
        assert table.symbols[0]['tag'] == 'DW_TAG_subprogram'

    def test_lookup_symbol(self):
        """测试符号查找"""
        table = DebugSymbolTable()
        
        table.add_variable("x", "int", 0x1000, "test.zhc", 1)
        table.add_variable("y", "int", 0x2000, "test.zhc", 2)
        
        result = table.lookup_symbol("x")
        assert result is not None
        assert result['name'] == "x"
        
        result = table.lookup_symbol("z")
        assert result is None


class TestTypeInfoGenerator:
    """测试类型信息生成器"""

    def test_add_base_type(self):
        """测试添加基本类型"""
        gen = TypeInfoGenerator()
        
        # TypeInfoGenerator 在初始化时预定义了基本类型
        # 检查预定义的 "整数型" 类型
        assert "整数型" in gen.type_table
        assert gen.type_table["整数型"]['name'] == "整数型"
        assert gen.type_table["整数型"]['byte_size'] == 4
        
        # 添加自定义基本类型
        gen.add_type(
            type_name="自定义整数",
            type_tag="DW_TAG_base_type",
            byte_size=8,
            encoding="DW_ATE_signed"
        )
        
        assert "自定义整数" in gen.type_table
        assert gen.type_table["自定义整数"]['byte_size'] == 8

    def test_add_struct_type(self):
        """测试添加结构体类型"""
        gen = TypeInfoGenerator()
        
        # 参数顺序: type_name, members, byte_size
        gen.add_struct_type(
            type_name="点",
            members=[
                {'name': 'x', 'type': 'int', 'offset': 0},
                {'name': 'y', 'type': 'int', 'offset': 8},
            ],
            byte_size=16
        )
        
        assert "点" in gen.type_table
        assert gen.type_table["点"]['name'] == "点"
        assert len(gen.type_table["点"]['members']) == 2


class TestDWARFGenerator:
    """测试 DWARF 生成器"""

    def test_generator_creation(self):
        """测试生成器创建"""
        gen = DWARFGenerator()
        
        assert gen.line_table is not None
        assert gen.symbol_table is not None
        assert gen.type_info is not None

    def test_add_compile_unit(self):
        """测试添加编译单元"""
        gen = DWARFGenerator()
        
        unit = gen.add_compile_unit(
            name="main",
            source_file="main.zhc",
            comp_dir="/path/to/project"
        )
        
        assert len(gen.compile_units) == 1
        assert unit.name == "main"

    def test_generate_debug_info(self):
        """测试生成调试信息"""
        gen = DWARFGenerator()
        
        gen.add_compile_unit("main", "main.zhc")
        gen.line_table.add_line_entry(0x1000, 10)
        gen.symbol_table.add_variable("x", "int", 0x1000, "main.zhc", 10)
        
        result = gen.generate_debug_info()
        
        assert '.debug_line' in result
        assert '.debug_info' in result
        assert '.debug_abbrev' in result


class TestDebugInfoGenerator:
    """测试高级调试信息生成器"""

    def test_generator_creation(self):
        """测试生成器创建"""
        gen = DebugInfoGenerator("test.zhc", "test.debug.json")
        
        assert gen.source_file == "test.zhc"
        assert gen.output_file == "test.debug.json"
        assert gen.dwarf is not None

    def test_add_function(self):
        """测试添加函数"""
        gen = DebugInfoGenerator("test.zhc", "test.debug.json")
        
        gen.add_function(
            name="主函数",
            start_line=1,
            end_line=10,
            start_addr=0x1000,
            end_addr=0x1200,
            return_type="整数型"
        )
        
        assert len(gen.dwarf.symbol_table.symbols) == 1

    def test_add_variable(self):
        """测试添加变量"""
        gen = DebugInfoGenerator("test.zhc", "test.debug.json")
        
        gen.add_variable(
            name="计数器",
            type_name="整数型",
            line_number=5,
            address=0x2000
        )
        
        assert len(gen.dwarf.symbol_table.symbols) == 1

    def test_map_line(self):
        """测试行号映射"""
        gen = DebugInfoGenerator("test.zhc", "test.debug.json")
        
        gen.map_line(10, 0x1000)
        gen.map_line(20, 0x1100)
        
        assert len(gen.dwarf.line_table.line_entries) == 2

    def test_finalize(self):
        """测试完成生成"""
        gen = DebugInfoGenerator("test.zhc", "test.debug.json")
        
        gen.add_function("main", 1, 10, 0x1000, 0x1200)
        gen.add_variable("x", "int", 5, 0x2000)
        
        result = gen.finalize()
        
        assert 'debug_line' in result
        assert 'debug_info' in result


class TestChineseSymbols:
    """测试中文符号支持"""

    def test_chinese_function_name(self):
        """测试中文函数名"""
        table = DebugSymbolTable()
        
        table.add_function(
            name="计算总和",
            return_type="整数型",
            low_pc=0x1000,
            high_pc=0x1200,
            file_path="计算.zhc",
            line_number=1
        )
        
        assert table.symbols[0]['name'] == "计算总和"

    def test_chinese_variable_name(self):
        """测试中文变量名"""
        table = DebugSymbolTable()
        
        table.add_variable(
            name="计数器",
            type_ref="整数型",
            location=0x1000,
            file_path="测试.zhc",
            line_number=10
        )
        
        assert table.symbols[0]['name'] == "计数器"

    def test_chinese_type_name(self):
        """测试中文类型名"""
        gen = TypeInfoGenerator()
        
        # TypeInfoGenerator 在初始化时预定义了中文类型名
        # 检查预定义的中文类型
        assert "整数型" in gen.type_table
        assert "浮点型" in gen.type_table
        assert gen.type_table["整数型"]['name'] == "整数型"
        assert gen.type_table["浮点型"]['name'] == "浮点型"
        
        # 添加自定义中文类型
        gen.add_type(
            type_name="自定义类型",
            type_tag="DW_TAG_base_type",
            byte_size=4,
            encoding="DW_ATE_signed"
        )
        
        assert "自定义类型" in gen.type_table
        assert gen.type_table["自定义类型"]['name'] == "自定义类型"


class TestDataStructures:
    """测试数据结构"""

    def test_source_location(self):
        """测试源码位置"""
        loc = SourceLocation("test.zhc", 10, 5)
        
        assert loc.file_path == "test.zhc"
        assert loc.line_number == 10
        assert loc.column_number == 5
        
        d = loc.to_dict()
        assert d['file'] == "test.zhc"
        assert d['line'] == 10

    def test_address_range(self):
        """测试地址范围"""
        range_ = AddressRange(0x1000, 0x1200)
        
        assert range_.contains(0x1000)
        assert range_.contains(0x1100)
        assert not range_.contains(0x1200)
        assert not range_.contains(0x0FFF)

    def test_compile_unit(self):
        """测试编译单元"""
        unit = CompileUnit(
            name="main",
            language="zhc",
            comp_dir="/path/to/project"
        )
        
        assert unit.name == "main"
        assert unit.language == "zhc"
        assert unit.producer == "zhc-1.0.0"
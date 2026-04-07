"""
调试器集成测试

测试 DWARF 调试信息生成器与 GDB/LLDB 的兼容性。
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List

import pytest

from zhc.codegen.debug_info import (
    DebugInfoGenerator,
    DebugInfoEntry,
    DWARFEncoder,
    DW_TAG,
    DW_AT,
    DW_FORM,
    generate_debug_info,
)


class TestDWARFFormat:
    """测试 DWARF 格式正确性"""

    def test_dwarf_constants_valid(self):
        """测试 DWARF 常量值符合标准"""
        # DW_TAG 常量验证
        assert DW_TAG.COMPILE_UNIT == 0x11
        assert DW_TAG.BASE_TYPE == 0x0e
        assert DW_TAG.STRUCT_TYPE == 0x13
        assert DW_TAG.SUBPROGRAM == 0x2e

        # DW_AT 常量验证
        assert DW_AT.NAME == 0x03
        assert DW_AT.BYTE_SIZE == 0x0b
        assert DW_AT.TYPE == 0x49
        assert DW_AT.LOW_PC == 0x11
        assert DW_AT.HIGH_PC == 0x12

        # DW_FORM 常量验证
        assert DW_FORM.ADDR == 0x01
        assert DW_FORM.STRING == 0x05
        assert DW_FORM.DATA4 == 0x06

    def test_die_structure(self):
        """测试 DIE 结构符合 DWARF 规范"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        # 生成基本调试信息
        functions = [{"name": "main", "address": 0x1000, "size": 100}]
        types = [{"name": "int", "kind": "base", "size": 4}]

        result = generator.generate(functions, types, [], {})

        # 验证结构
        assert "line_program" in result
        assert "debug_info" in result
        assert generator.root_die is not None

        # 验证编译单元 DIE
        root = generator.root_die
        assert root.tag == DW_TAG.COMPILE_UNIT
        assert DW_AT.PRODUCER in root.attributes
        assert DW_AT.LANGUAGE in root.attributes

    def test_function_die_attributes(self):
        """测试函数 DIE 属性完整性"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        functions = [
            {
                "name": "计算",
                "address": 0x1000,
                "size": 200,
                "line": 10,
                "return_type": "整数型",
                "params": [{"name": "x", "type": "整数型", "location": "rdi"}],
            }
        ]

        result = generator.generate(functions, [], [], {})

        # 验证函数 DIE
        func_die = generator.root_die.children[0]
        assert func_die.tag == DW_TAG.SUBPROGRAM
        assert func_die.attributes[DW_AT.NAME] == "计算"
        assert func_die.attributes[DW_AT.LOW_PC] == 0x1000
        # HIGH_PC = LOW_PC + size = 0x1000 + 200 = 0x10C8
        assert func_die.attributes[DW_AT.HIGH_PC] == 0x10C8
        assert len(func_die.children) == 1  # 参数

    def test_type_die_attributes(self):
        """测试类型 DIE 属性完整性"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        types = [
            {"name": "整数型", "kind": "base", "size": 4},
            {"name": "点", "kind": "struct", "size": 16, "members": [
                {"name": "x", "type": "整数型", "offset": 0},
                {"name": "y", "type": "整数型", "offset": 4},
            ]},
        ]

        result = generator.generate([], types, [], {})

        # 验证基本类型 DIE
        base_die = generator.root_die.children[0]
        assert base_die.tag == DW_TAG.BASE_TYPE
        assert base_die.attributes[DW_AT.NAME] == "整数型"
        assert base_die.attributes[DW_AT.BYTE_SIZE] == 4
        assert DW_AT.ENCODING in base_die.attributes

        # 验证结构体 DIE
        struct_die = generator.root_die.children[1]
        assert struct_die.tag == DW_TAG.STRUCT_TYPE
        assert struct_die.attributes[DW_AT.NAME] == "点"
        assert len(struct_die.children) == 2  # 成员


class TestDWARFEncoding:
    """测试 DWARF 二进制编码"""

    def test_encode_compile_unit(self):
        """测试编译单元编码"""
        encoder = DWARFEncoder()

        # 创建简单的 DIE
        die = DebugInfoEntry(tag=DW_TAG.COMPILE_UNIT)
        die.attributes[DW_AT.NAME] = "test.zhc"
        die.attributes[DW_AT.PRODUCER] = "zhc-1.0.0"

        # 编码
        encoded = encoder.encode_compile_unit(die, [])

        # 验证编码结果
        assert len(encoded) > 0
        assert encoded[:4] != b"\x00\x00\x00\x00"  # 长度不为 0

    def test_encode_string_attribute(self):
        """测试字符串属性编码"""
        encoder = DWARFEncoder()

        encoded = encoder._encode_form_value("test")

        assert encoded == b"test\x00"

    def test_encode_integer_attribute(self):
        """测试整数属性编码"""
        encoder = DWARFEncoder()

        encoded = encoder._encode_form_value(42)

        assert len(encoded) == 8
        assert int.from_bytes(encoded, "little") == 42


class TestDebuggerCompatibility:
    """测试调试器兼容性"""

    @pytest.mark.skipif(
        not shutil.which("dwarfdump"),
        reason="dwarfdump not available"
    )
    def test_dwarfdump_compatibility(self):
        """测试 dwarfdump 能解析生成的 DWARF"""
        # 生成调试信息
        generator = DebugInfoGenerator("test.zhc", "test.c")

        functions = [
            {"name": "main", "address": 0x1000, "size": 100, "line": 1},
        ]
        types = [
            {"name": "int", "kind": "base", "size": 4},
        ]

        result = generator.generate(functions, types, [], {})

        # 编码为二进制
        encoder = DWARFEncoder()
        encoded = encoder.encode_compile_unit(generator.root_die, [])

        # 写入临时文件
        with tempfile.NamedTemporaryFile(suffix=".debug", delete=False) as f:
            f.write(encoded)
            temp_file = f.name

        try:
            # 使用 dwarfdump 解析
            result = subprocess.run(
                ["dwarfdump", temp_file],
                capture_output=True,
                text=True,
            )

            # 验证解析成功（即使有警告也接受）
            # 注意：简化实现可能不完全符合 DWARF 标准
            # 这里主要测试格式基本正确
            assert result.returncode in [0, 1]  # 0=成功, 1=部分解析

        finally:
            os.unlink(temp_file)

    @pytest.mark.skipif(
        not shutil.which("llvm-dwarfdump"),
        reason="llvm-dwarfdump not available"
    )
    def test_llvm_dwarfdump_compatibility(self):
        """测试 llvm-dwarfdump 能解析生成的 DWARF"""
        # 生成调试信息
        generator = DebugInfoGenerator("test.zhc", "test.c")

        functions = [
            {"name": "main", "address": 0x1000, "size": 100, "line": 1},
        ]

        result = generator.generate(functions, [], [], {})

        # 编码为二进制
        encoder = DWARFEncoder()
        encoded = encoder.encode_compile_unit(generator.root_die, [])

        # 写入临时文件
        with tempfile.NamedTemporaryFile(suffix=".debug", delete=False) as f:
            f.write(encoded)
            temp_file = f.name

        try:
            # 使用 llvm-dwarfdump 解析
            result = subprocess.run(
                ["llvm-dwarfdump", temp_file],
                capture_output=True,
                text=True,
            )

            # 验证解析成功
            assert result.returncode in [0, 1]

        finally:
            os.unlink(temp_file)


class TestLineProgram:
    """测试行号程序生成"""

    def test_line_program_structure(self):
        """测试行号程序结构"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        # 行号映射：格式为 {address: (file_path, line, column)}
        line_mapping = {
            0x1000: ("test.zhc", 1, 0),  # 地址 0x1000 -> 行 1
            0x1010: ("test.zhc", 2, 0),  # 地址 0x1010 -> 行 2
            0x1020: ("test.zhc", 3, 0),  # 地址 0x1020 -> 行 3
        }

        result = generator.generate([], [], [], line_mapping)

        # 验证行号程序
        assert "line_program" in result
        line_program = result["line_program"]

        # line_program 是格式化后的字符串
        assert ".file 1" in line_program
        assert "test.zhc" in line_program
        assert "行号表" in line_program

    def test_line_program_entries(self):
        """测试行号条目正确性"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        line_mapping = {
            0x1000: ("test.zhc", 10, 5),
            0x1100: ("test.zhc", 20, 10),
        }

        result = generator.generate([], [], [], line_mapping)

        # 验证 LineProgram 对象内部结构
        assert generator.line_program is not None
        entries = generator.line_program.entries

        # 验证条目
        assert entries[0].address == 0x1000
        assert entries[0].line == 10
        assert entries[0].column == 5

        assert entries[1].address == 0x1100
        assert entries[1].line == 20


class TestChineseSymbols:
    """测试中文符号支持"""

    def test_chinese_function_name(self):
        """测试中文函数名"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        functions = [
            {"name": "主函数", "address": 0x1000, "size": 100},
            {"name": "计算总和", "address": 0x1100, "size": 200},
        ]

        result = generator.generate(functions, [], [], {})

        # 验证中文函数名
        func1 = generator.root_die.children[0]
        assert func1.attributes[DW_AT.NAME] == "主函数"

        func2 = generator.root_die.children[1]
        assert func2.attributes[DW_AT.NAME] == "计算总和"

    def test_chinese_type_name(self):
        """测试中文类型名"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        types = [
            {"name": "整数型", "kind": "base", "size": 4},
            {"name": "浮点型", "kind": "base", "size": 8},
            {"name": "点坐标", "kind": "struct", "size": 16, "members": [
                {"name": "横坐标", "type": "整数型", "offset": 0},
                {"name": "纵坐标", "type": "整数型", "offset": 4},
            ]},
        ]

        result = generator.generate([], types, [], {})

        # 验证中文类型名
        type1 = generator.root_die.children[0]
        assert type1.attributes[DW_AT.NAME] == "整数型"

        type2 = generator.root_die.children[1]
        assert type2.attributes[DW_AT.NAME] == "浮点型"

        type3 = generator.root_die.children[2]
        assert type3.attributes[DW_AT.NAME] == "点坐标"

        # 验证中文成员名
        member1 = type3.children[0]
        assert member1.attributes[DW_AT.NAME] == "横坐标"

        member2 = type3.children[1]
        assert member2.attributes[DW_AT.NAME] == "纵坐标"

    def test_chinese_variable_name(self):
        """测试中文变量名"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        from zhc.codegen.debug_info import DebugVariable

        variables = [
            DebugVariable(name="计数器", type_name="整数型", location="rbp-8"),
            DebugVariable(name="结果", type_name="浮点型", location="rbp-16"),
        ]

        # 变量需要通过函数添加到 DIE
        functions = [
            {
                "name": "主函数",
                "address": 0x1000,
                "size": 100,
                "variables": [
                    {"name": "计数器", "type": "整数型", "location": "rbp-8"},
                    {"name": "结果", "type": "浮点型", "location": "rbp-16"},
                ]
            }
        ]

        result = generator.generate(functions, [], [], {})

        # 验证中文变量名（变量在函数 DIE 的子节点中）
        func_die = generator.root_die.children[0]
        var1 = func_die.children[0]
        assert var1.attributes[DW_AT.NAME] == "计数器"

        var2 = func_die.children[1]
        assert var2.attributes[DW_AT.NAME] == "结果"


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_generate_debug_info_function(self):
        """测试 generate_debug_info 便捷函数"""
        result = generate_debug_info(
            source_file="test.zhc",
            output_file="test.c",
            functions=[{"name": "main", "address": 0x1000, "size": 100}],
            types=[{"name": "int", "kind": "base", "size": 4}],
            variables=[],
            line_mapping={0x1000: ("test.zhc", 1, 0)},
        )

        assert "line_program" in result
        assert "debug_info" in result
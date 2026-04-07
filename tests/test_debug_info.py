"""
调试信息生成器测试
"""

import pytest
from zhc.codegen.debug_info import (
    DebugInfoGenerator,
    DWARFEncoder,
    DebugLocation,
    DebugVariable,
    DebugLineEntry,
    DebugInfoEntry,
    DW_TAG,
    DW_AT,
    DW_LANG,
    generate_debug_info
)


class TestDebugInfoGenerator:
    """调试信息生成器测试"""

    def test_generator_creation(self):
        """测试生成器创建"""
        generator = DebugInfoGenerator("test.zhc", "test.c")
        assert generator.source_file == "test.zhc"
        assert generator.output_file == "test.c"

    def test_generate_empty(self):
        """测试空调试信息生成"""
        generator = DebugInfoGenerator("test.zhc", "test.c")
        result = generator.generate([], [], [], {})

        assert result["source_file"] == "test.zhc"
        assert result["output_file"] == "test.c"
        assert result["language"] == DW_LANG.C

    def test_generate_line_program(self):
        """测试行号程序生成"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        line_mapping = {
            0x1000: ("test.zhc", 1, 0),
            0x1010: ("test.zhc", 2, 0),
            0x1020: ("test.zhc", 3, 0),
        }

        result = generator.generate([], [], [], line_mapping)

        assert "line_program" in result
        assert generator.line_program is not None
        assert len(generator.line_program.entries) == 3

    def test_generate_base_type(self):
        """测试基本类型 DIE 生成"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        types = [
            {"name": "整数型", "kind": "base", "size": 4},
            {"name": "浮点型", "kind": "base", "size": 8},
            {"name": "字符型", "kind": "base", "size": 1},
        ]

        result = generator.generate([], types, [], {})

        assert generator.root_die is not None
        assert len(generator.root_die.children) == 3

        # 检查第一个类型
        type_die = generator.root_die.children[0]
        assert type_die.tag == DW_TAG.BASE_TYPE
        assert type_die.attributes[DW_AT.NAME] == "整数型"
        assert type_die.attributes[DW_AT.BYTE_SIZE] == 4

    def test_generate_struct_type(self):
        """测试结构体类型 DIE 生成"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        types = [
            {
                "name": "点",
                "kind": "struct",
                "size": 16,
                "members": [
                    {"name": "x", "type": "整数型", "offset": 0},
                    {"name": "y", "type": "整数型", "offset": 8},
                ]
            }
        ]

        result = generator.generate([], types, [], {})

        assert generator.root_die is not None
        assert len(generator.root_die.children) == 1

        struct_die = generator.root_die.children[0]
        assert struct_die.tag == DW_TAG.STRUCT_TYPE
        assert struct_die.attributes[DW_AT.NAME] == "点"
        assert len(struct_die.children) == 2

    def test_generate_enum_type(self):
        """测试枚举类型 DIE 生成"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        types = [
            {
                "name": "颜色",
                "kind": "enum",
                "size": 4,
                "values": [
                    {"name": "红", "value": 0},
                    {"name": "绿", "value": 1},
                    {"name": "蓝", "value": 2},
                ]
            }
        ]

        result = generator.generate([], types, [], {})

        enum_die = generator.root_die.children[0]
        assert enum_die.tag == DW_TAG.ENUMERATION_TYPE
        assert enum_die.attributes[DW_AT.NAME] == "颜色"
        assert len(enum_die.children) == 3

    def test_generate_pointer_type(self):
        """测试指针类型 DIE 生成"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        types = [
            {
                "name": "整数型指针",
                "kind": "pointer",
                "element_type": "整数型"
            }
        ]

        result = generator.generate([], types, [], {})

        ptr_die = generator.root_die.children[0]
        assert ptr_die.tag == DW_TAG.POINTER_TYPE
        assert ptr_die.attributes[DW_AT.BYTE_SIZE] == 8

    def test_generate_array_type(self):
        """测试数组类型 DIE 生成"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        types = [
            {
                "name": "整数数组",
                "kind": "array",
                "size": 40,
                "element_type": "整数型",
                "dimensions": [10]
            }
        ]

        result = generator.generate([], types, [], {})

        array_die = generator.root_die.children[0]
        assert array_die.tag == DW_TAG.ARRAY_TYPE
        assert len(array_die.children) == 1  # 维度

    def test_generate_function(self):
        """测试函数 DIE 生成"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        functions = [
            {
                "name": "加法",
                "address": 0x1000,
                "size": 0x50,
                "line": 1,
                "return_type": "整数型",
                "params": [
                    {"name": "a", "type": "整数型", "location": "rdi"},
                    {"name": "b", "type": "整数型", "location": "rsi"},
                ],
                "variables": [
                    {"name": "结果", "type": "整数型", "location": "[rbp-8]"},
                ]
            }
        ]

        result = generator.generate(functions, [], [], {})

        func_die = generator.root_die.children[0]
        assert func_die.tag == DW_TAG.SUBPROGRAM
        assert func_die.attributes[DW_AT.NAME] == "加法"
        assert func_die.attributes[DW_AT.LOW_PC] == 0x1000
        assert func_die.attributes[DW_AT.HIGH_PC] == 0x1050
        assert len(func_die.children) == 3  # 2 params + 1 variable

    def test_generate_multiple_functions(self):
        """测试多个函数 DIE 生成"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        functions = [
            {"name": "函数1", "address": 0x1000, "size": 0x50, "line": 1},
            {"name": "函数2", "address": 0x2000, "size": 0x30, "line": 10},
            {"name": "函数3", "address": 0x3000, "size": 0x40, "line": 20},
        ]

        result = generator.generate(functions, [], [], {})

        assert len(generator.root_die.children) == 3


class TestDWARFEncoder:
    """DWARF 编码器测试"""

    def test_encoder_creation(self):
        """测试编码器创建"""
        encoder = DWARFEncoder()
        assert encoder is not None

    def test_encode_die(self):
        """测试 DIE 编码"""
        encoder = DWARFEncoder()

        die = DebugInfoEntry(tag=DW_TAG.BASE_TYPE)
        die.attributes[DW_AT.NAME] = "整数型"
        die.attributes[DW_AT.BYTE_SIZE] = 4

        encoded = encoder._encode_die(die)
        assert isinstance(encoded, bytes)
        assert len(encoded) > 0

    def test_encode_compile_unit(self):
        """测试编译单元编码"""
        encoder = DWARFEncoder()

        die = DebugInfoEntry(tag=DW_TAG.COMPILE_UNIT)
        die.attributes[DW_AT.NAME] = "test.zhc"
        die.attributes[DW_AT.LANGUAGE] = DW_LANG.C

        encoded = encoder.encode_compile_unit(die, [])
        assert isinstance(encoded, bytes)
        assert len(encoded) > 0

    def test_encode_form_value_string(self):
        """测试字符串表单值编码"""
        encoder = DWARFEncoder()

        encoded = encoder._encode_form_value("test")
        assert encoded == b"test\x00"

    def test_encode_form_value_int(self):
        """测试整数表单值编码"""
        encoder = DWARFEncoder()

        encoded = encoder._encode_form_value(42)
        assert len(encoded) == 8


class TestDebugDataStructures:
    """调试数据结构测试"""

    def test_debug_location(self):
        """测试调试位置"""
        loc = DebugLocation(file="test.zhc", line=10, column=5)
        assert loc.file == "test.zhc"
        assert loc.line == 10
        assert loc.column == 5

    def test_debug_variable(self):
        """测试调试变量"""
        var = DebugVariable(
            name="x",
            type_name="整数型",
            location="[rbp-8]",
            scope_start=0x1000,
            scope_end=0x1050
        )
        assert var.name == "x"
        assert var.type_name == "整数型"
        assert var.location == "[rbp-8]"

    def test_debug_line_entry(self):
        """测试行号表条目"""
        entry = DebugLineEntry(
            address=0x1000,
            file_index=1,
            line=10,
            column=0,
            is_stmt=True
        )
        assert entry.address == 0x1000
        assert entry.line == 10
        assert entry.is_stmt is True

    def test_debug_info_entry(self):
        """测试调试信息条目"""
        die = DebugInfoEntry(tag=DW_TAG.SUBPROGRAM)
        die.attributes[DW_AT.NAME] = "函数"
        die.attributes[DW_AT.LOW_PC] = 0x1000

        child = DebugInfoEntry(tag=DW_TAG.VARIABLE)
        child.attributes[DW_AT.NAME] = "x"
        die.children.append(child)

        assert die.tag == DW_TAG.SUBPROGRAM
        assert die.attributes[DW_AT.NAME] == "函数"
        assert len(die.children) == 1


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_generate_debug_info(self):
        """测试便捷函数"""
        result = generate_debug_info(
            source_file="test.zhc",
            output_file="test.c",
            functions=[
                {"name": "主函数", "address": 0x1000, "size": 0x50, "line": 1}
            ],
            types=[
                {"name": "整数型", "kind": "base", "size": 4}
            ],
            variables=[],
            line_mapping={0x1000: ("test.zhc", 1, 0)}
        )

        assert result["source_file"] == "test.zhc"
        assert result["language"] == DW_LANG.C


class TestIntegration:
    """集成测试"""

    def test_full_debug_info_generation(self):
        """测试完整调试信息生成"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        # 定义类型
        types = [
            {"name": "整数型", "kind": "base", "size": 4},
            {"name": "浮点型", "kind": "base", "size": 8},
            {
                "name": "点",
                "kind": "struct",
                "size": 16,
                "members": [
                    {"name": "x", "type": "浮点型", "offset": 0},
                    {"name": "y", "type": "浮点型", "offset": 8},
                ]
            }
        ]

        # 定义函数
        functions = [
            {
                "name": "计算距离",
                "address": 0x1000,
                "size": 0x100,
                "line": 1,
                "return_type": "浮点型",
                "params": [
                    {"name": "p1", "type": "点", "location": "rdi"},
                    {"name": "p2", "type": "点", "location": "rsi"},
                ],
                "variables": [
                    {"name": "dx", "type": "浮点型", "location": "[rbp-8]"},
                    {"name": "dy", "type": "浮点型", "location": "[rbp-16]"},
                ]
            }
        ]

        # 行号映射
        line_mapping = {
            0x1000: ("test.zhc", 1, 0),  # 函数开始
            0x1010: ("test.zhc", 2, 0),  # dx = p2.x - p1.x
            0x1020: ("test.zhc", 3, 0),  # dy = p2.y - p1.y
            0x1030: ("test.zhc", 4, 0),  # 返回 sqrt(dx*dx + dy*dy)
        }

        # 生成调试信息
        result = generator.generate(functions, types, [], line_mapping)

        # 验证结果
        assert result["source_file"] == "test.zhc"
        assert result["language"] == DW_LANG.C
        assert "line_program" in result
        assert "debug_info" in result

        # 验证行号程序
        assert generator.line_program is not None
        assert len(generator.line_program.entries) == 4

        # 验证 DIE 树
        assert generator.root_die is not None
        assert len(generator.root_die.children) == 4  # 3 types + 1 function

    def test_complex_type_hierarchy(self):
        """测试复杂类型层次结构"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        types = [
            {"name": "整数型", "kind": "base", "size": 4},
            {
                "name": "节点",
                "kind": "struct",
                "size": 24,
                "members": [
                    {"name": "值", "type": "整数型", "offset": 0},
                    {"name": "左", "type": "节点指针", "offset": 8},
                    {"name": "右", "type": "节点指针", "offset": 16},
                ]
            },
            {
                "name": "节点指针",
                "kind": "pointer",
                "element_type": "节点"
            }
        ]

        result = generator.generate([], types, [], {})

        assert len(generator.root_die.children) == 3


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_function(self):
        """测试空函数"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        functions = [
            {"name": "空函数", "address": 0x1000, "size": 0, "line": 1}
        ]

        result = generator.generate(functions, [], [], {})
        assert len(generator.root_die.children) == 1

    def test_function_with_no_params(self):
        """测试无参数函数"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        functions = [
            {"name": "无参函数", "address": 0x1000, "size": 0x50, "line": 1}
        ]

        result = generator.generate(functions, [], [], {})

        func_die = generator.root_die.children[0]
        assert len(func_die.children) == 0

    def test_nested_structs(self):
        """测试嵌套结构体"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        types = [
            {"name": "整数型", "kind": "base", "size": 4},
            {
                "name": "内部",
                "kind": "struct",
                "size": 4,
                "members": [
                    {"name": "值", "type": "整数型", "offset": 0}
                ]
            },
            {
                "name": "外部",
                "kind": "struct",
                "size": 8,
                "members": [
                    {"name": "内部值", "type": "内部", "offset": 0}
                ]
            }
        ]

        result = generator.generate([], types, [], {})
        assert len(generator.root_die.children) == 3

    def test_large_line_mapping(self):
        """测试大行号映射"""
        generator = DebugInfoGenerator("test.zhc", "test.c")

        # 生成 1000 行映射
        line_mapping = {
            0x1000 + i * 0x10: ("test.zhc", i + 1, 0)
            for i in range(1000)
        }

        result = generator.generate([], [], [], line_mapping)

        assert len(generator.line_program.entries) == 1000

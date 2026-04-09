# -*- coding: utf-8 -*-
"""
测试 DWARF 调试信息模块

作者：远
日期：2026-04-09
"""

import pytest
import sys
from pathlib import Path

# 添加 src 目录到路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestTypePrinter:
    """测试类型描述器"""

    def test_builtin_types(self):
        """测试内置类型"""
        from zhc.debug.type_printer import TypePrinter

        printer = TypePrinter()

        # 检查内置类型
        assert printer.get_type("整数型") is not None
        assert printer.get_type("浮点型") is not None
        assert printer.get_type("字符型") is not None
        assert printer.get_type("空型") is not None

        # 检查类型大小
        assert printer.get_type_size("整数型") == 4
        assert printer.get_type_size("双精度型") == 8
        assert printer.get_type_size("字节型") == 1

    def test_pointer_type(self):
        """测试指针类型"""
        from zhc.debug.type_printer import TypePrinter

        printer = TypePrinter()

        ptr_type = printer.create_pointer_type(
            name="ptr_int",
            base_type="整数型",
            byte_size=8,
        )

        assert ptr_type.kind.value == "pointer"
        assert ptr_type.base_type == "整数型"
        assert ptr_type.layout.size == 8

    def test_struct_type(self):
        """测试结构体类型"""
        from zhc.debug.type_printer import TypePrinter, MemberInfo

        printer = TypePrinter()

        members = [
            MemberInfo(name="x", type_ref="整数型", offset=0),
            MemberInfo(name="y", type_ref="整数型", offset=4),
        ]

        struct_type = printer.create_struct_type(
            name="点",
            members=members,
            total_size=8,
        )

        assert struct_type.kind.value == "struct"
        assert len(struct_type.members) == 2

    def test_array_type(self):
        """测试数组类型"""
        from zhc.debug.type_printer import TypePrinter

        printer = TypePrinter()

        array_type = printer.create_array_type(
            name="数组",
            element_type="整数型",
            array_size=10,
            element_size=4,
        )

        assert array_type.kind.value == "array"
        assert array_type.element_type == "整数型"
        assert array_type.array_size == 10
        assert array_type.layout.size == 40

    def test_type_info_generation(self):
        """测试 DWARF 类型信息生成"""
        from zhc.debug.type_printer import TypePrinter

        printer = TypePrinter()

        info = printer.generate_dwarf_type_info("整数型")

        assert info["name"] == "整数型"
        assert "byte_size" in info
        assert "encoding" in info


class TestVariableLocation:
    """测试变量位置追踪"""

    def test_register_location(self):
        """测试寄存器位置"""
        from zhc.debug.variable_location import (
            VariableLocation,
            LocationKind,
        )

        loc = VariableLocation.in_register(0, "rax")

        assert loc.kind == LocationKind.REGISTER
        assert loc.register_number == 0
        assert loc.register_name == "rax"
        assert str(loc) == "$rax"

    def test_stack_location(self):
        """测试栈位置"""
        from zhc.debug.variable_location import VariableLocation, LocationKind

        loc = VariableLocation.on_stack(-8, "rbp")

        assert loc.kind == LocationKind.STACK
        assert loc.frame_offset == -8
        assert str(loc) == "[rbp-8]"

    def test_memory_location(self):
        """测试内存位置"""
        from zhc.debug.variable_location import VariableLocation, LocationKind

        loc = VariableLocation.in_memory(0x1000)

        assert loc.kind == LocationKind.MEMORY
        assert loc.memory_address == 0x1000
        assert "0x1000" in str(loc)

    def test_live_range(self):
        """测试活跃区间"""
        from zhc.debug.variable_location import LiveRange, VariableLocation

        loc = VariableLocation.in_register(0, "rax")
        range1 = LiveRange(start=0x100, end=0x200, location=loc)

        assert range1.contains(0x150)
        assert not range1.contains(0x300)

    def test_location_tracker(self):
        """测试位置追踪器"""
        from zhc.debug.variable_location import VariableLocationTracker

        tracker = VariableLocationTracker()

        # 注册变量
        tracker.register_variable("x", "整数型")
        tracker.assign_register("x", 0, "rax", start=0x100, end=0x200)

        var = tracker.get_variable("x")
        assert var is not None
        assert var.name == "x"

        # 检查活跃区间
        assert var.is_live_at(0x150)
        assert not var.is_live_at(0x300)

    def test_location_expression(self):
        """测试位置表达式生成"""
        from zhc.debug.variable_location import (
            VariableLocationTracker,
            VariableLocation,
        )

        tracker = VariableLocationTracker()

        loc = VariableLocation.on_stack(-8, "rbp")
        expr = tracker.generate_location_expression(loc)

        # 检查是否为有效的字节
        assert isinstance(expr, bytes)
        assert len(expr) > 0


class TestScopeTracker:
    """测试作用域追踪"""

    def test_scope_lifecycle(self):
        """测试作用域生命周期"""
        from zhc.debug.scope_tracker import ScopeTracker, ScopeKind

        tracker = ScopeTracker()

        # 开始全局作用域
        global_scope = tracker.begin_scope(ScopeKind.GLOBAL, "global")

        # 开始函数作用域
        func_scope = tracker.begin_scope(
            ScopeKind.FUNCTION, "main", start_line=1, end_line=100
        )

        # 检查当前作用域
        assert tracker.get_current_scope() == func_scope
        assert tracker.get_current_scope().parent == global_scope

        # 结束函数作用域
        tracker.end_scope()

        # 结束全局作用域
        tracker.end_scope()

        assert tracker.get_current_scope() is None

    def test_variable_declaration(self):
        """测试变量声明"""
        from zhc.debug.scope_tracker import ScopeTracker, ScopeKind

        tracker = ScopeTracker()
        tracker.begin_scope(ScopeKind.GLOBAL, "global")

        # 添加变量
        entry = tracker.add_variable("x", declaration_line=1)
        assert entry.name == "x"
        assert entry.kind == "variable"

        # 添加函数
        func_entry = tracker.add_function("main", declaration_line=5)
        assert func_entry.name == "main"
        assert func_entry.kind == "function"

    def test_variable_lookup(self):
        """测试变量查找"""
        from zhc.debug.scope_tracker import ScopeTracker, ScopeKind

        tracker = ScopeTracker()
        tracker.begin_scope(ScopeKind.GLOBAL, "global")
        tracker.add_variable("global_var", declaration_line=1)

        # 嵌套作用域
        tracker.begin_scope(ScopeKind.BLOCK, "block", start_line=5, end_line=20)
        tracker.add_variable("local_var", declaration_line=10)

        # 查找局部变量
        local = tracker.lookup_variable("local_var")
        assert local is not None
        assert local.name == "local_var"

        # 查找全局变量（应该能找到）
        global_var = tracker.lookup_variable("global_var")
        assert global_var is not None
        assert global_var.name == "global_var"

    def test_scope_statistics(self):
        """测试作用域统计"""
        from zhc.debug.scope_tracker import ScopeTracker, ScopeKind

        tracker = ScopeTracker()
        tracker.begin_scope(ScopeKind.GLOBAL, "global")
        tracker.add_variable("x", declaration_line=1)

        tracker.begin_scope(ScopeKind.FUNCTION, "main", start_line=5, end_line=20)
        tracker.add_variable("y", declaration_line=10)
        tracker.add_function("foo", declaration_line=15)

        stats = tracker.get_statistics()

        assert stats["total_scopes"] == 2
        assert stats["total_variables"] == 2
        assert stats["total_functions"] == 1

    def test_scope_tree_dump(self):
        """测试作用域树导出"""
        from zhc.debug.scope_tracker import ScopeTracker, ScopeKind

        tracker = ScopeTracker()
        tracker.begin_scope(ScopeKind.GLOBAL, "global")
        tracker.add_variable("x", declaration_line=1)

        tracker.begin_scope(ScopeKind.FUNCTION, "main")
        tracker.add_variable("y", declaration_line=5)

        dump = tracker.dump_scope_tree()

        assert "global" in dump
        assert "main" in dump
        assert "x" in dump
        assert "y" in dump


class TestDebugSections:
    """测试 DWARF 调试节"""

    def test_debug_info_section(self):
        """测试 .debug_info 节"""
        from zhc.debug.sections.debug_info import (
            DebugInfoSection,
            DwarfVersion,
        )

        section = DebugInfoSection(DwarfVersion.V4)

        # 添加编译单元
        builder = section.add_compile_unit(
            name="test.zhc",
            producer="ZhC Compiler",
        )

        # 添加函数
        func = builder.add_function(
            name="main",
            low_pc=0x1000,
            high_pc=0x1100,
            line=1,
        )

        # 添加参数
        builder.add_parameter(func, "argc", "%rdi", line=1)
        builder.add_parameter(func, "argv", "%rsi", line=1)

        section.finalize_compile_unit()

        # 构建节数据
        data = section.build()
        assert len(data) > 0

    def test_debug_abbrev_section(self):
        """测试 .debug_abbrev 节"""
        from zhc.debug.sections.debug_abbrev import DebugAbbrevSection

        section = DebugAbbrevSection()

        # 添加标准缩写
        section.add_standard_abbreviations()

        # 构建节数据
        data = section.build()
        assert len(data) > 0

    def test_debug_line_section(self):
        """测试 .debug_line 节"""
        from zhc.debug.sections.debug_line import DebugLineSection

        section = DebugLineSection()

        # 开始行号程序
        program = section.begin_program("test.zhc", minimum_instruction_length=1)

        # 添加文件
        file_idx = program.add_file("test.zhc", "/path/to")
        assert file_idx == 1

        section.end_program()

        # 构建节数据
        data = section.build()
        assert len(data) > 0

    def test_debug_str_section(self):
        """测试 .debug_str 节"""
        from zhc.debug.sections.debug_str import DebugStrSection

        section = DebugStrSection()

        # 添加字符串
        offset1 = section.add_string("test")
        section.add_string("hello")
        offset3 = section.add_string("test")  # 重复字符串

        # 检查去重
        assert offset1 == offset3  # 相同字符串应返回相同偏移

        # 添加常用字符串
        section.add_common_strings()

        # 构建节数据
        data = section.build()
        assert len(data) > 0


class TestDebugModulesIntegration:
    """测试调试模块集成"""

    def test_full_debug_info_generation(self):
        """测试完整的调试信息生成流程"""
        from zhc.debug.type_printer import TypePrinter
        from zhc.debug.scope_tracker import ScopeTracker, ScopeKind
        from zhc.debug.variable_location import VariableLocationTracker
        from zhc.debug.sections.debug_info import DebugInfoSection
        from zhc.debug.sections.debug_abbrev import DebugAbbrevSection

        # 1. 创建类型
        type_printer = TypePrinter()
        type_printer.create_struct_type(
            name="点",
            members=[],
            total_size=8,
        )

        # 2. 创建作用域追踪
        scope_tracker = ScopeTracker()
        scope_tracker.begin_scope(ScopeKind.GLOBAL, "global")
        scope_tracker.add_variable("global_var", declaration_line=1)

        scope_tracker.begin_scope(ScopeKind.FUNCTION, "main", start_line=1, end_line=20)
        scope_tracker.add_variable("local_var", declaration_line=5)
        scope_tracker.add_function("main", declaration_line=1)

        # 3. 创建变量位置追踪
        location_tracker = VariableLocationTracker()
        location_tracker.register_variable("local_var", "整数型")
        location_tracker.assign_stack_slot(
            "local_var", -8, "rbp", start=0x100, end=0x200
        )

        # 4. 生成 DWARF 节
        info_section = DebugInfoSection()
        builder = info_section.add_compile_unit("main.zhc")
        func = builder.add_function("main", 0x1000, 0x1100, 1)
        builder.add_variable(func, "local_var", "%rbp-8", 5)

        abbrev_section = DebugAbbrevSection()
        abbrev_section.add_standard_abbreviations()

        # 验证
        assert info_section.build() is not None
        assert abbrev_section.build() is not None

    def test_module_import(self):
        """测试模块导入"""
        from zhc.debug import (
            TypePrinter,
            VariableLocationTracker,
            ScopeTracker,
            DebugInfoSection,
            DebugAbbrevSection,
            DebugLineSection,
            DebugStrSection,
        )

        # 确保所有新模块都可以导入
        assert TypePrinter is not None
        assert VariableLocationTracker is not None
        assert ScopeTracker is not None
        assert DebugInfoSection is not None
        assert DebugAbbrevSection is not None
        assert DebugLineSection is not None
        assert DebugStrSection is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

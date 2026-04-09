"""
P2 功能测试：debug 模块

测试 DWARF 调试信息收集、行号生成、断点引擎等模块。
"""

import pytest
from unittest.mock import patch

# debug 模块
from zhc.debug.debug_info_collector import (
    DebugInfoCollector,
)
from zhc.debug.line_number_generator import (
    LineNumberGenerator,
    LineTable,
    LineTableEntry,
)
from zhc.debug.breakpoint_engine import (
    BreakpointEngine,
)
from zhc.debug.variable_printer import (
    VariablePrinter,
)
from zhc.debug.stack_frame_analyzer import (
    StackFrameAnalyzer,
    FrameInfo,
)


class TestDebugInfoCollector:
    """调试信息收集器测试"""

    def test_collector_init(self):
        """测试收集器初始化"""
        collector = DebugInfoCollector()
        assert len(collector.compile_units) == 0

    def test_begin_compile_unit(self):
        """测试开始编译单元"""
        collector = DebugInfoCollector()
        unit = collector.begin_compile_unit(
            name="test.zhc",
            language=None,  # 使用默认语言
        )

        assert len(collector.compile_units) == 1
        assert collector._current_unit == unit

    def test_end_compile_unit(self):
        """测试结束编译单元"""
        collector = DebugInfoCollector()
        collector.begin_compile_unit(name="test.zhc")
        unit = collector.end_compile_unit()

        assert unit is not None
        assert collector._current_unit is None

    def test_add_function(self):
        """测试添加函数"""
        collector = DebugInfoCollector()

        collector.begin_compile_unit(name="test.zhc")
        func = collector.create_function_info(
            name="main",
            linkage_name="_main",
            return_type=None,  # 使用默认
        )
        collector.add_function(func)

        assert len(collector.compile_units[0].functions) == 1


class TestLineTable:
    """行号表测试"""

    def test_line_table_init(self):
        """测试行号表初始化"""
        table = LineTable()
        assert len(table.file_names) == 0
        assert len(table.entries) == 0

    def test_add_file(self):
        """测试添加源文件"""
        table = LineTable()
        file_index = table.add_file("test.zhc")

        assert file_index >= 1  # 索引从 1 开始
        assert len(table.file_names) == 1

    def test_add_entry(self):
        """测试添加行信息"""
        table = LineTable()
        file_index = table.add_file("test.zhc")

        entry = LineTableEntry(
            address=0x1000, file_index=file_index, line=1, is_stmt=True
        )
        table.add_entry(entry)

        assert len(table.entries) == 1
        assert table.entries[0].line == 1
        assert table.entries[0].address == 0x1000

    def test_get_line_for_address(self):
        """测试获取地址对应的行号"""
        table = LineTable()
        file_index = table.add_file("test.zhc")

        table.add_entry(LineTableEntry(address=0x1000, file_index=file_index, line=1))
        table.add_entry(LineTableEntry(address=0x1010, file_index=file_index, line=2))
        table.add_entry(LineTableEntry(address=0x1020, file_index=file_index, line=3))

        result = table.get_line_for_address(0x1005)
        assert result is not None
        assert result.line == 1

        result = table.get_line_for_address(0x1015)
        assert result is not None
        assert result.line == 2

    def test_get_address_for_line(self):
        """测试获取行号对应的地址"""
        table = LineTable()
        file_index = table.add_file("test.zhc")

        table.add_entry(LineTableEntry(address=0x1000, file_index=file_index, line=1))
        table.add_entry(LineTableEntry(address=0x1010, file_index=file_index, line=2))

        address = table.get_address_for_line(file_index, 1)
        assert address == 0x1000

        address = table.get_address_for_line(file_index, 2)
        assert address == 0x1010


class TestLineNumberGenerator:
    """行号生成器测试"""

    def test_generator_init(self):
        """测试生成器初始化"""
        generator = LineNumberGenerator()
        assert len(generator.line_tables) == 0

    def test_generate(self):
        """测试生成行号表"""
        generator = LineNumberGenerator()

        instructions = [
            {"address": 0x1000, "file": 1, "line": 1, "column": 0},
            {"address": 0x1010, "file": 1, "line": 2, "column": 0},
            {"address": 0x1020, "file": 1, "line": 3, "column": 0},
        ]

        table = generator.generate("test.zhc", instructions)

        assert table is not None
        # 第一条指令可能被跳过（地址为0会被跳过）
        assert len(table.entries) >= 2


class TestBreakpointEngine:
    """断点引擎测试"""

    def test_engine_init(self):
        """测试引擎初始化"""
        engine = BreakpointEngine()
        assert len(engine._breakpoints) == 0

    def test_set_source_breakpoint(self):
        """测试设置源码断点"""
        engine = BreakpointEngine()

        with patch.object(engine, "_lookup_address", return_value=0x1000):
            bp_id = engine.set_source_breakpoint("test.zhc", 10)

        assert bp_id == 1
        assert 1 in engine._breakpoints

    def test_set_function_breakpoint(self):
        """测试设置函数断点"""
        engine = BreakpointEngine()

        with patch.object(engine, "_lookup_function_address", return_value=0x2000):
            bp_id = engine.set_function_breakpoint("main")

        assert bp_id == 1

    def test_enable_disable(self):
        """测试启用/禁用断点"""
        engine = BreakpointEngine()

        with patch.object(engine, "_lookup_address", return_value=0x1000):
            bp_id = engine.set_source_breakpoint("test.zhc", 10)

        assert engine.disable_breakpoint(bp_id) is True
        assert engine._breakpoints[bp_id].enabled is False

        assert engine.enable_breakpoint(bp_id) is True
        assert engine._breakpoints[bp_id].enabled is True

    def test_delete_breakpoint(self):
        """测试删除断点"""
        engine = BreakpointEngine()

        with patch.object(engine, "_lookup_address", return_value=0x1000):
            bp_id = engine.set_source_breakpoint("test.zhc", 10)

        assert engine.delete_breakpoint(bp_id) is True
        assert bp_id not in engine._breakpoints

    def test_set_condition(self):
        """测试设置断点条件"""
        engine = BreakpointEngine()

        with patch.object(engine, "_lookup_address", return_value=0x1000):
            bp_id = engine.set_source_breakpoint("test.zhc", 10)

        engine.set_condition(bp_id, "x > 10")

        assert engine._conditions[bp_id] == "x > 10"

    def test_check_breakpoint(self):
        """测试检查断点命中"""
        engine = BreakpointEngine()

        with patch.object(engine, "_lookup_address", return_value=0x1000):
            bp_id = engine.set_source_breakpoint("test.zhc", 10)

        # 首次检查应命中
        hit = engine.check_breakpoint(0x1000, 1, 0, 1.0)
        assert hit is not None
        assert hit.breakpoint_id == bp_id
        assert hit.hit_count == 1


class TestVariablePrinter:
    """变量打印器测试"""

    def test_printer_init(self):
        """测试打印器初始化"""
        printer = VariablePrinter()
        assert printer._debug_info is None

    def test_printer_with_collector(self):
        """测试带收集器的打印器"""
        collector = DebugInfoCollector()
        printer = VariablePrinter(collector)
        assert printer._debug_info == collector

    def test_set_current_frame(self):
        """测试设置当前帧"""
        printer = VariablePrinter()
        printer.set_current_frame(0x1000, 0xFFFF)

        assert printer._current_frame_pc == 0x1000
        assert printer._frame_base == 0xFFFF


class TestStackFrameAnalyzer:
    """栈帧分析器测试"""

    def test_analyzer_init(self):
        """测试分析器初始化"""
        analyzer = StackFrameAnalyzer()
        assert len(analyzer._frames) == 0

    def test_analyzer_with_collector(self):
        """测试带收集器的分析器"""
        collector = DebugInfoCollector()
        analyzer = StackFrameAnalyzer(collector)
        assert analyzer._debug_info == collector

    def test_frame_info_location_string(self):
        """测试帧信息位置字符串"""
        frame = FrameInfo(
            frame_id=0,
            pc=0x1000,
            function_name="main",
            source_file="test.zhc",
            source_line=10,
        )

        loc = frame.location_string
        assert "main" in loc
        assert "test.zhc:10" in loc

    def test_frame_info_no_info(self):
        """测试无信息的帧"""
        frame = FrameInfo(frame_id=0, pc=0)

        loc = frame.location_string
        # PC 为 0 时位置可能为空
        assert loc is not None

    def test_select_frame(self):
        """测试选择帧"""
        analyzer = StackFrameAnalyzer()

        # 模拟一些帧
        frame1 = FrameInfo(frame_id=0, pc=0x1000)
        frame2 = FrameInfo(frame_id=1, pc=0x2000)
        analyzer._frames = [frame1, frame2]

        assert analyzer.select_frame(1) is True
        assert analyzer.get_current_frame() == frame2

        assert analyzer.select_frame(999) is False

    def test_format_backtrace(self):
        """测试格式化调用栈"""
        analyzer = StackFrameAnalyzer()

        frames = [
            FrameInfo(
                frame_id=0,
                pc=0x1000,
                function_name="main",
                source_file="test.zhc",
                source_line=10,
            ),
            FrameInfo(
                frame_id=1,
                pc=0x2000,
                function_name="foo",
                source_file="test.zhc",
                source_line=20,
            ),
        ]

        result = analyzer.format_backtrace(frames)

        assert "main" in result
        assert "foo" in result

    def test_format_frame(self):
        """测试格式化帧信息"""
        analyzer = StackFrameAnalyzer()

        frame = FrameInfo(
            frame_id=0,
            pc=0x1000,
            function_name="main",
            source_file="test.zhc",
            source_line=10,
            frame_pointer=0xFF00,
            stack_pointer=0xFE00,
        )

        result = analyzer.format_frame(frame)

        assert "Frame #0" in result
        assert "0x1000" in result
        assert "main" in result


class TestDebugModuleIntegration:
    """debug 模块集成测试"""

    def test_full_debug_flow(self):
        """测试完整调试流程"""
        # 1. 创建收集器
        collector = DebugInfoCollector()
        collector.begin_compile_unit(name="test.zhc")

        func = collector.create_function_info(
            name="main", linkage_name="_main", return_type=None
        )
        func.ranges = [(0x1000, 0x2000)]
        collector.add_function(func)

        # 2. 创建行号表
        line_table = LineTable()
        file_index = line_table.add_file("test.zhc")
        line_table.add_entry(
            LineTableEntry(address=0x1000, file_index=file_index, line=1)
        )
        line_table.add_entry(
            LineTableEntry(address=0x1500, file_index=file_index, line=10)
        )

        # 3. 创建断点引擎
        engine = BreakpointEngine()

        with patch.object(engine, "_lookup_address", return_value=0x1500):
            bp_id = engine.set_source_breakpoint("test.zhc", 10)
        assert bp_id == 1

        # 4. 创建变量打印器
        _ = VariablePrinter(collector)

        # 5. 创建栈帧分析器
        _ = StackFrameAnalyzer(collector)

        # 验证流程完整性
        assert len(collector.compile_units[0].functions) == 1
        assert len(line_table.entries) == 2
        assert len(engine._breakpoints) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

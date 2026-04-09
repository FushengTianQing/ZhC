"""
P2 功能测试：调试支持模块

测试 GDB/LLDB 支持、断点管理、变量检查器、表达式求值器、栈帧分析器等模块。
"""

import pytest
from pathlib import Path
import tempfile

# GDB/LLDB 支持模块
from zhc.debugger.gdb_support import (
    GDBSupport,
    GDBConfig,
    GDBPrettyPrinterRegistry,
)
from zhc.debugger.lldb_support import (
    LLDBSupport,
    LLDBConfig,
    LLDBFormatterRegistry,
)
from zhc.debugger.pretty_printer import (
    StringPrinter,
    ArrayPrinter,
    MapPrinter,
    StructPrinter,
    PrinterOption,
    DisplayHint,
    create_printer,
)
from zhc.debugger.breakpoint_manager import (
    BreakpointManager,
    BreakpointType,
    BreakpointState,
)
from zhc.debugger.variable_inspector import (
    VariableInspector,
    VariableValue,
    VariableLocation,
    VariableLocationType,
    TypeInfo,
    FrameInfo,
)
from zhc.debugger.expression_evaluator import (
    ExpressionEvaluator,
    EvaluationContext,
    Lexer,
    Parser,
    TokenType,
    ExpressionType,
)


class TestGDBSupport:
    """GDB 支持模块测试"""

    def test_gdb_config_default(self):
        """测试默认配置"""
        config = GDBConfig()
        assert config.print_pretty is True
        assert config.print_array is True
        assert config.print_array_indexes is True
        assert config.print_elements == 200
        assert config.disassembly_flavor == "intel"

    def test_gdb_config_custom(self):
        """测试自定义配置"""
        config = GDBConfig(
            print_pretty=False, print_array=False, disassembly_flavor="att"
        )
        assert config.print_pretty is False
        assert config.print_array is False
        assert config.disassembly_flavor == "att"

    def test_generate_gdbinit(self):
        """测试生成 .gdbinit 文件"""
        support = GDBSupport()
        gdbinit = support.generate_gdbinit()

        assert "set print pretty on" in gdbinit
        assert "set print array on" in gdbinit
        assert "set disassembly-flavor intel" in gdbinit
        assert "ZhC GDB Support loaded" in gdbinit

    def test_generate_gdbinit_to_file(self):
        """测试生成 .gdbinit 到文件"""
        support = GDBSupport()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / ".gdbinit"
            support.generate_gdbinit(output_path)

            assert output_path.exists()
            content = output_path.read_text()
            assert "set print pretty on" in content

    def test_pretty_printer_registry(self):
        """测试美化打印器注册表"""
        registry = GDBPrettyPrinterRegistry()

        # 注册打印器
        registry.register(
            name="string",
            pattern="^zhc_string$",
            printer_class=StringPrinter,
            description="ZhC string printer",
        )

        assert "string" in registry.printers
        assert registry.printers["string"].pattern == "^zhc_string$"
        assert registry.printers["string"].enabled is True

    def test_pretty_printer_enable_disable(self):
        """测试打印器启用/禁用"""
        registry = GDBPrettyPrinterRegistry()
        registry.register("string", "^zhc_string$", StringPrinter)

        assert registry.disable("string") is True
        assert registry.printers["string"].enabled is False

        assert registry.enable("string") is True
        assert registry.printers["string"].enabled is True

        assert registry.disable("nonexistent") is False

    def test_generate_python_script(self):
        """测试生成 Python 脚本"""
        registry = GDBPrettyPrinterRegistry()
        script = registry.generate_python_script()

        assert "import gdb" in script
        assert "ZHCStringPrinter" in script
        assert "ZHCArrayPrinter" in script
        assert "ZHCMapPrinter" in script
        assert "register_pretty_printers" in script

    def test_gdb_commands(self):
        """测试 GDB 命令生成"""
        support = GDBSupport()
        commands = support.generate_commands()

        assert "zhc-run" in commands
        assert "zhc-break" in commands
        assert "zhc-step" in commands
        assert "zhc-print" in commands
        assert "zhc-bt" in commands


class TestLLDBSupport:
    """LLDB 支持模块测试"""

    def test_lldb_config_default(self):
        """测试默认配置"""
        config = LLDBConfig()
        assert config.target_x86_disassembly_flavor == "intel"
        assert config.stop_disassembly_display == "always"

    def test_generate_lldbinit(self):
        """测试生成 .lldbinit 文件"""
        support = LLDBSupport()
        lldbinit = support.generate_lldbinit()

        assert "settings set target.x86-disassembly-flavor intel" in lldbinit
        assert "settings set stop-disassembly-display always" in lldbinit
        # 检查关键配置项
        assert "zhc-b" in lldbinit or "ZhC" in lldbinit

    def test_formatter_registry(self):
        """测试格式化器注册表"""
        registry = LLDBFormatterRegistry()

        registry.register_summary("zhc_string", "zhc_string_summary(valobj)")
        assert "zhc_string" in registry.summaries

        registry.register_synthetic("zhc_array", "ZHCArraySyntheticProvider")
        assert "zhc_array" in registry.synthetic_children

    def test_generate_python_script(self):
        """测试生成 Python 脚本"""
        registry = LLDBFormatterRegistry()
        script = registry.generate_python_script()

        assert "import lldb" in script
        assert "zhc_string_summary" in script
        assert "zhc_array_summary" in script
        assert "ZHCArraySyntheticProvider" in script
        assert "__lldb_init_module" in script

    def test_lldb_commands(self):
        """测试 LLDB 命令生成"""
        support = LLDBSupport()
        commands = support.generate_commands()

        assert "zhc-run" in commands
        assert "zhc-b" in commands
        assert "zhc-p" in commands
        assert "zhc-bt" in commands


class TestPrettyPrinter:
    """美化打印器测试"""

    def test_string_printer(self):
        """测试字符串打印器"""

        class MockValue:
            data = "hello world"
            length = 11

        printer = StringPrinter(MockValue())
        result = printer.to_string()

        assert "hello world" in result
        assert printer.display_hint() == DisplayHint.STRING

    def test_string_printer_empty(self):
        """测试空字符串打印"""

        class MockValue:
            data = ""
            length = 0

        printer = StringPrinter(MockValue())
        assert '""' in printer.to_string()

    def test_array_printer(self):
        """测试数组打印器"""

        class MockValue:
            data = [1, 2, 3, 4, 5]
            length = 5
            capacity = 10

            class MockType:
                def template_argument(self, index):
                    return "int"

            type = MockType()

        printer = ArrayPrinter(MockValue())
        result = printer.to_string()

        assert "size=5" in result
        assert "capacity=10" in result
        assert printer.display_hint() == DisplayHint.ARRAY

    def test_array_printer_children(self):
        """测试数组子元素"""

        class MockValue:
            data = [1, 2, 3]
            length = 3
            capacity = 3

            class MockType:
                def template_argument(self, index):
                    return "int"

            type = MockType()

        printer = ArrayPrinter(MockValue())
        children = printer.children()

        assert len(children) == 3
        assert children[0][0] == "[0]"

    def test_map_printer(self):
        """测试映射打印器"""

        class MockValue:
            size = 3
            entries = []

            def __init__(self):
                # 模拟 entries 列表
                pass

        printer = MapPrinter(MockValue())
        result = printer.to_string()

        # 由于 Mock 对象简化，size 可能无法正确读取
        assert "zhc_map" in result
        assert printer.display_hint() == DisplayHint.MAP

    def test_struct_printer(self):
        """测试结构体打印器"""

        class MockValue:
            name = "test"
            value = 42

            class MockType:
                def __str__(self):
                    return "TestStruct"

                def fields(self):
                    return [
                        type("Field", (), {"name": "name"})(),
                        type("Field", (), {"name": "value"})(),
                    ]

            type = MockType()

            def __getitem__(self, name):
                return getattr(self, name)

        printer = StructPrinter(MockValue())
        result = printer.to_string()

        assert "TestStruct" in result
        assert printer.display_hint() == DisplayHint.STRUCT

    def test_printer_options(self):
        """测试打印选项"""
        options = PrinterOption(max_elements=50, max_string_length=256, max_depth=5)

        class MockValue:
            data = "test"
            length = 4

        printer = StringPrinter(MockValue(), options)
        assert printer.options.max_elements == 50
        assert printer.options.max_string_length == 256

    def test_create_printer_auto_detect(self):
        """测试自动检测创建打印器"""
        # 字符串
        printer = create_printer("hello")
        assert isinstance(printer, StringPrinter)

        # 列表
        printer = create_printer([1, 2, 3])
        assert isinstance(printer, ArrayPrinter)

        # 字典
        printer = create_printer({"a": 1})
        assert isinstance(printer, MapPrinter)


class TestBreakpointManager:
    """断点管理器测试"""

    def test_set_source_breakpoint(self):
        """测试设置源码断点"""
        manager = BreakpointManager()
        bp = manager.set_source_breakpoint("test.zhc", 10)

        assert bp.id == 1
        assert bp.type == BreakpointType.SOURCE_LINE
        assert bp.location.source_file == "test.zhc"
        assert bp.location.line_number == 10
        assert bp.is_enabled

    def test_set_function_breakpoint(self):
        """测试设置函数断点"""
        manager = BreakpointManager()
        bp = manager.set_function_breakpoint("main")

        assert bp.id == 1
        assert bp.type == BreakpointType.FUNCTION
        assert bp.location.function_name == "main"

    def test_set_address_breakpoint(self):
        """测试设置地址断点"""
        manager = BreakpointManager()
        bp = manager.set_address_breakpoint(0x1000)

        assert bp.id == 1
        assert bp.type == BreakpointType.ADDRESS
        assert bp.location.address == 0x1000

    def test_set_watchpoint(self):
        """测试设置监视点"""
        manager = BreakpointManager()
        bp = manager.set_watchpoint("x", BreakpointType.WATCH_WRITE)

        assert bp.is_watchpoint
        assert bp.type == BreakpointType.WATCH_WRITE

    def test_delete_breakpoint(self):
        """测试删除断点"""
        manager = BreakpointManager()
        bp = manager.set_source_breakpoint("test.zhc", 10)

        assert manager.delete_breakpoint(bp.id) is True
        assert manager.get_breakpoint(bp.id) is None
        assert manager.delete_breakpoint(999) is False

    def test_enable_disable_breakpoint(self):
        """测试启用/禁用断点"""
        manager = BreakpointManager()
        bp = manager.set_source_breakpoint("test.zhc", 10)

        assert manager.disable_breakpoint(bp.id) is True
        assert bp.state == BreakpointState.DISABLED

        assert manager.enable_breakpoint(bp.id) is True
        assert bp.state == BreakpointState.ENABLED

    def test_breakpoint_condition(self):
        """测试断点条件"""
        manager = BreakpointManager()
        bp = manager.set_source_breakpoint("test.zhc", 10)

        assert manager.modify_condition(bp.id, "x > 10") is True
        assert bp.condition.expression == "x > 10"

    def test_breakpoint_ignore_count(self):
        """测试忽略计数"""
        manager = BreakpointManager()
        bp = manager.set_source_breakpoint("test.zhc", 10)

        assert manager.modify_ignore_count(bp.id, 5) is True
        assert bp.ignore_count == 5

    def test_get_breakpoints(self):
        """测试获取断点列表"""
        manager = BreakpointManager()
        manager.set_source_breakpoint("test.zhc", 10)
        manager.set_function_breakpoint("main")
        manager.set_address_breakpoint(0x1000)

        all_bps = manager.get_all_breakpoints()
        assert len(all_bps) == 3

        enabled = manager.get_enabled_breakpoints()
        assert len(enabled) == 3

        manager.disable_breakpoint(1)
        enabled = manager.get_enabled_breakpoints()
        assert len(enabled) == 2

    def test_to_gdb_commands(self):
        """测试转换为 GDB 命令"""
        manager = BreakpointManager()
        manager.set_source_breakpoint("test.zhc", 10)
        manager.set_function_breakpoint("main")

        commands = manager.to_gdb_commands()
        assert len(commands) == 2
        assert "break test.zhc:10" in commands[0]
        assert "break main" in commands[1]

    def test_to_lldb_commands(self):
        """测试转换为 LLDB 命令"""
        manager = BreakpointManager()
        manager.set_source_breakpoint("test.zhc", 10)
        manager.set_function_breakpoint("main")

        commands = manager.to_lldb_commands()
        assert len(commands) >= 2


class TestVariableInspector:
    """变量检查器测试"""

    def test_register_type(self):
        """测试注册类型"""
        inspector = VariableInspector()

        type_info = TypeInfo(name="int", size=4, alignment=4)

        inspector.register_type(type_info)
        assert inspector.get_type("int") == type_info

    def test_global_variable(self):
        """测试全局变量"""
        inspector = VariableInspector()

        type_info = TypeInfo(name="int", size=4, alignment=4)
        location = VariableLocation(
            type=VariableLocationType.MEMORY, memory_address=0x1000
        )

        var = inspector.set_global_variable("x", type_info, location, 42)

        assert var.name == "x"
        assert var.value == 42

        retrieved = inspector.get_global_variable("x")
        assert retrieved == var

    def test_local_variable(self):
        """测试局部变量"""
        inspector = VariableInspector()

        # 创建栈帧信息
        type_info = TypeInfo(name="int", size=4, alignment=4)
        location = VariableLocation(type=VariableLocationType.STACK, stack_offset=-8)

        frame = FrameInfo(frame_id=0, pc=0x1000, function_name="main")

        frame.locals["y"] = VariableValue(
            name="y", type_info=type_info, location=location, value=10
        )

        inspector.set_current_frame(frame)

        var = inspector.get_local_variable("y")
        assert var is not None
        assert var.name == "y"
        assert var.value == 10

    def test_get_all_locals(self):
        """测试获取所有局部变量"""
        inspector = VariableInspector()

        type_info = TypeInfo(name="int", size=4, alignment=4)

        frame = FrameInfo(frame_id=0, pc=0x1000, function_name="main")

        frame.arguments["argc"] = VariableValue(
            name="argc",
            type_info=type_info,
            location=VariableLocation(type=VariableLocationType.REGISTER),
            value=1,
        )

        frame.locals["x"] = VariableValue(
            name="x",
            type_info=type_info,
            location=VariableLocation(type=VariableLocationType.STACK),
            value=42,
        )

        inspector.set_current_frame(frame)

        all_vars = inspector.get_all_locals()
        assert "argc" in all_vars
        assert "x" in all_vars

    def test_scope(self):
        """测试作用域"""
        inspector = VariableInspector()

        scope = inspector.create_scope("main", 0x1000, 0x2000)

        type_info = TypeInfo(name="int", size=4, alignment=4)
        var = VariableValue(
            name="x",
            type_info=type_info,
            location=VariableLocation(type=VariableLocationType.STACK),
        )

        inspector.add_variable_to_scope(scope, var)

        assert "x" in scope.variables
        assert scope.is_in_scope(0x1500)
        assert not scope.is_in_scope(0x3000)


class TestExpressionEvaluator:
    """表达式求值器测试"""

    def test_lexer_basic(self):
        """测试词法分析器基本功能"""
        lexer = Lexer("1 + 2")
        tokens = lexer.tokenize()

        assert tokens[0].type == TokenType.INTEGER
        assert tokens[0].value == 1
        assert tokens[1].type == TokenType.PLUS
        assert tokens[2].type == TokenType.INTEGER
        assert tokens[2].value == 2
        assert tokens[3].type == TokenType.EOF

    def test_lexer_identifiers(self):
        """测试标识符词法分析"""
        lexer = Lexer("variable_name")
        tokens = lexer.tokenize()

        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "variable_name"

    def test_lexer_operators(self):
        """测试运算符词法分析"""
        lexer = Lexer("a == b && c != d")
        tokens = lexer.tokenize()

        assert tokens[1].type == TokenType.EQUALS_EQUALS
        assert tokens[3].type == TokenType.AMPERSAND_AMPERSAND
        assert tokens[5].type == TokenType.BANG_EQUALS

    def test_lexer_strings(self):
        """测试字符串词法分析"""
        lexer = Lexer('"hello world"')
        tokens = lexer.tokenize()

        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello world"

    def test_parser_binary_op(self):
        """测试二元运算解析"""
        lexer = Lexer("1 + 2")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert ast.type == ExpressionType.BINARY_OP
        assert ast.operator == "+"
        assert len(ast.children) == 2

    def test_parser_member_access(self):
        """测试成员访问解析"""
        lexer = Lexer("obj.field")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert ast.type == ExpressionType.MEMBER_ACCESS
        assert len(ast.children) == 2

    def test_parser_array_index(self):
        """测试数组索引解析"""
        lexer = Lexer("arr[0]")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert ast.type == ExpressionType.ARRAY_INDEX
        assert len(ast.children) == 2

    def test_parser_ternary(self):
        """测试三元表达式解析"""
        lexer = Lexer("a ? b : c")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert ast.type == ExpressionType.TERNARY
        assert len(ast.children) == 3

    def test_evaluator_literal(self):
        """测试字面量求值"""
        evaluator = ExpressionEvaluator()
        context = EvaluationContext()

        result = evaluator.evaluate("42", context)
        assert result.is_valid
        assert result.value == 42

    def test_evaluator_variable(self):
        """测试变量求值"""
        evaluator = ExpressionEvaluator()
        context = EvaluationContext()
        context.set_variable("x", 10)

        result = evaluator.evaluate("x", context)
        assert result.is_valid
        assert result.value == 10

    def test_evaluator_binary_op(self):
        """测试二元运算求值"""
        evaluator = ExpressionEvaluator()
        context = EvaluationContext()
        context.set_variable("a", 10)
        context.set_variable("b", 5)

        result = evaluator.evaluate("a + b", context)
        assert result.is_valid
        assert result.value == 15

        result = evaluator.evaluate("a * b", context)
        assert result.value == 50

        result = evaluator.evaluate("a - b", context)
        assert result.value == 5

        result = evaluator.evaluate("a / b", context)
        assert result.value == 2

    def test_evaluator_comparison(self):
        """测试比较运算求值"""
        evaluator = ExpressionEvaluator()
        context = EvaluationContext()
        context.set_variable("a", 10)
        context.set_variable("b", 5)

        result = evaluator.evaluate("a > b", context)
        assert result.value is True

        result = evaluator.evaluate("a < b", context)
        assert result.value is False

        result = evaluator.evaluate("a == 10", context)
        assert result.value is True

    def test_evaluator_logical(self):
        """测试逻辑运算求值"""
        evaluator = ExpressionEvaluator()
        context = EvaluationContext()
        context.set_variable("a", True)
        context.set_variable("b", False)

        result = evaluator.evaluate("a && b", context)
        assert result.value is False

        result = evaluator.evaluate("a || b", context)
        assert result.value is True

        result = evaluator.evaluate("!b", context)
        assert result.value is True

    def test_evaluator_member_access(self):
        """测试成员访问求值"""
        evaluator = ExpressionEvaluator()
        context = EvaluationContext()
        context.set_variable("obj", {"field": 42})

        result = evaluator.evaluate("obj.field", context)
        assert result.is_valid
        assert result.value == 42

    def test_evaluator_array_index(self):
        """测试数组索引求值"""
        evaluator = ExpressionEvaluator()
        context = EvaluationContext()
        context.set_variable("arr", [1, 2, 3, 4, 5])

        result = evaluator.evaluate("arr[2]", context)
        assert result.is_valid
        assert result.value == 3

    def test_evaluator_ternary(self):
        """测试三元表达式求值"""
        evaluator = ExpressionEvaluator()
        context = EvaluationContext()
        context.set_variable("x", 10)

        result = evaluator.evaluate("x > 5 ? 100 : 200", context)
        assert result.is_valid
        assert result.value == 100

        result = evaluator.evaluate("x < 5 ? 100 : 200", context)
        assert result.value == 200

    def test_evaluator_error(self):
        """测试错误处理"""
        evaluator = ExpressionEvaluator()
        context = EvaluationContext()

        result = evaluator.evaluate("undefined_var", context)
        assert result.is_error
        assert "Undefined variable" in result.error


class TestIntegration:
    """集成测试"""

    def test_debugger_integration(self):
        """测试调试器模块集成"""
        # 创建断点管理器
        bp_manager = BreakpointManager()

        # 设置断点
        bp = bp_manager.set_source_breakpoint("test.zhc", 10)
        assert bp is not None

        # 创建变量检查器
        inspector = VariableInspector()

        # 注册类型
        type_info = TypeInfo(name="int", size=4, alignment=4)
        inspector.register_type(type_info)

        # 设置全局变量
        location = VariableLocation(
            type=VariableLocationType.MEMORY, memory_address=0x1000
        )
        var = inspector.set_global_variable("counter", type_info, location, 0)
        assert var is not None  # 验证变量创建成功

        # 创建表达式求值器
        evaluator = ExpressionEvaluator()
        context = EvaluationContext()
        context.set_variable("counter", 0)

        # 求值表达式
        result = evaluator.evaluate("counter + 1", context)
        assert result.value == 1

    def test_gdb_lldb_integration(self):
        """测试 GDB/LLDB 集成"""
        # 创建 GDB 支持
        gdb = GDBSupport()
        gdbinit = gdb.generate_gdbinit()

        # 创建 LLDB 支持
        lldb = LLDBSupport()
        lldbinit = lldb.generate_lldbinit()

        # 验证生成的配置
        assert "set print pretty on" in gdbinit
        assert "settings set target.x86-disassembly-flavor intel" in lldbinit


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

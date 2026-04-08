"""
LLDB调试器中文C语言支持
LLDB Integration for ZHC Language

提供LLDB Python API命令，支持中文C语言调试
"""

try:
    import lldb

    LLDB_AVAILABLE = True
except ImportError:
    LLDB_AVAILABLE = False

    # 创建模拟的lldb模块用于测试
    class MockLLDB:
        class SBDebugger:
            pass

        class SBCommandReturnObject:
            def AppendMessage(self, msg):
                pass

        class SBCommandInterpreter:
            pass

    lldb = MockLLDB()

from typing import Dict


class ZHCLLLDBCommands:
    """LLDB中文C语言命令集合"""

    def __init__(self, debugger: lldb.SBDebugger):
        """
        初始化LLDB命令

        Args:
            debugger: LLDB调试器实例
        """
        self.debugger = debugger
        self.interpreter = debugger.GetCommandInterpreter()

        self.type_mapping: Dict[str, str] = {
            # 基本类型映射
            "整数型": "int",
            "浮点型": "float",
            "双精度型": "double",
            "字符型": "char",
            "字符串型": "char*",
            "布尔型": "int",
            "空类型": "void",
            # 无符号类型
            "无符号整数型": "unsigned int",
            "无符号字符型": "unsigned char",
            # 长整型
            "长整数型": "long",
            "短整数型": "short",
        }

        self.keyword_mapping: Dict[str, str] = {
            # 关键字映射
            "函数": "function",
            "主函数": "main",
            "返回": "return",
            "如果": "if",
            "否则": "else",
            "循环": "for",
            "当": "while",
            "跳出": "break",
            "继续": "continue",
            "类": "class",
            "继承": "inherits",
            "公开": "public",
            "私有": "private",
            "保护": "protected",
            "模块": "module",
            "导入": "import",
        }

    def register_commands(self):
        """注册所有LLDB命令"""
        # 注册zhc-help命令
        self.interpreter.HandleCommand(
            "command script add -f lldb_zhc.zhc_help zhc-help"
        )

        # 注册zhc-break命令
        self.interpreter.HandleCommand(
            "command script add -f lldb_zhc.zhc_break zhc-break"
        )

        # 注册zhc-list命令
        self.interpreter.HandleCommand(
            "command script add -f lldb_zhc.zhc_list zhc-list"
        )

        # 注册zhc-print命令
        self.interpreter.HandleCommand(
            "command script add -f lldb_zhc.zhc_print zhc-print"
        )

        # 注册zhc-where命令
        self.interpreter.HandleCommand(
            "command script add -f lldb_zhc.zhc_where zhc-where"
        )

        # 注册zhc-info命令
        self.interpreter.HandleCommand(
            "command script add -f lldb_zhc.zhc_info zhc-info"
        )

        # 注册zhc-types命令
        self.interpreter.HandleCommand(
            "command script add -f lldb_zhc.zhc_types zhc-types"
        )

        # 注册zhc-symbols命令
        self.interpreter.HandleCommand(
            "command script add -f lldb_zhc.zhc_symbols zhc-symbols"
        )

        print("✅ LLDB中文C语言命令注册完成")

    def zhc_break(self, function_name: str, debugger: lldb.SBDebugger):
        """
        在中文函数设置断点

        Args:
            function_name: 中文函数名
            debugger: LLDB调试器实例
        """
        # 转换为C函数名
        c_func = self._translate_function_name(function_name)

        # 获取目标
        target = debugger.GetSelectedTarget()
        if not target:
            print("❌ 没有选中的目标")
            return

        # 设置断点
        breakpoint = target.BreakpointCreateByName(c_func)

        if breakpoint.IsValid():
            print(f"✅ 在函数 '{function_name}' ({c_func}) 设置断点成功")
            print(f"   断点ID: {breakpoint.GetID()}")
        else:
            print("❌ 设置断点失败")

    def zhc_list(self, debugger: lldb.SBDebugger):
        """
        列出中文源码

        Args:
            debugger: LLDB调试器实例
        """
        # 获取当前线程和帧
        process = debugger.GetSelectedTarget().GetProcess()
        thread = process.GetSelectedThread()
        frame = thread.GetSelectedFrame()

        if not frame:
            print("❌ 没有选中的帧")
            return

        # 获取行号和文件
        line_entry = frame.GetLineEntry()
        if not line_entry:
            print("❌ 无法获取行号信息")
            return

        file_spec = line_entry.GetFileSpec()
        line_number = line_entry.GetLine()

        print(f"📄 当前位置: {file_spec.filename}:{line_number}")

        # 使用source命令显示源码
        result = lldb.SBCommandReturnObject()
        self.interpreter.HandleCommand(
            f"source list -f {file_spec.filename} -l {line_number - 5} -c 10", result
        )

        if result.Succeeded():
            print(result.GetOutput())
        else:
            print("❌ 无法列出源码")

    def zhc_print(self, var_name: str, debugger: lldb.SBDebugger):
        """
        打印中文变量

        Args:
            var_name: 中文变量名
            debugger: LLDB调试器实例
        """
        # 转换变量名
        c_var = self._translate_variable_name(var_name)

        # 获取当前帧
        process = debugger.GetSelectedTarget().GetProcess()
        thread = process.GetSelectedThread()
        frame = thread.GetSelectedFrame()

        if not frame:
            print("❌ 没有选中的帧")
            return

        # 查找变量
        var_list = frame.GetVariables(True, True, True, True)

        for var in var_list:
            if var.GetName() == c_var:
                print(f"📦 {var_name} ({c_var}):")
                print(f"   类型: {var.GetTypeName()}")
                print(f"   值: {var.GetValue()}")
                return

        print(f"❌ 变量 '{var_name}' 未找到")

    def zhc_where(self, debugger: lldb.SBDebugger):
        """
        显示中文调用栈

        Args:
            debugger: LLDB调试器实例
        """
        # 获取当前线程
        process = debugger.GetSelectedTarget().GetProcess()
        thread = process.GetSelectedThread()

        if not thread:
            print("❌ 没有选中的线程")
            return

        print("📋 中文C语言调用栈:")
        print("=" * 60)

        for i in range(thread.GetNumFrames()):
            frame = thread.GetFrameAtIndex(i)
            func_name = frame.GetFunctionName()

            # 转换函数名
            zhc_func = self._reverse_translate_function(func_name or "???")

            # 获取文件和行号
            line_entry = frame.GetLineEntry()
            if line_entry:
                file_spec = line_entry.GetFileSpec()
                line_number = line_entry.GetLine()
                print(f"#{i}  {zhc_func} ({func_name})")
                print(f"    at {file_spec.filename}:{line_number}")
            else:
                print(f"#{i}  {zhc_func} ({func_name})")

        print("=" * 60)

    def zhc_info(self, debugger: lldb.SBDebugger):
        """
        显示程序信息

        Args:
            debugger: LLDB调试器实例
        """
        print("📊 中文C程序信息:")
        print("=" * 60)

        target = debugger.GetSelectedTarget()
        if not target:
            print("❌ 没有选中的目标")
            return

        # 显示目标信息
        print(f"目标: {target.GetFileSpec().filename}")
        print(f"架构: {target.GetTriple()}")

        # 显示进程信息
        process = target.GetProcess()
        if process.IsValid():
            print(f"进程ID: {process.GetProcessID()}")
            print(f"进程状态: {process.GetState()}")

            # 显示线程信息
            print(f"\n线程数: {process.GetNumThreads()}")
            for i in range(process.GetNumThreads()):
                thread = process.GetThreadAtIndex(i)
                print(f"  线程 #{i}: {thread.GetThreadID()}")

        # 显示断点信息
        print(f"\n断点数: {target.GetNumBreakpoints()}")
        for i in range(target.GetNumBreakpoints()):
            bp = target.GetBreakpointAtIndex(i)
            print(f"  断点 #{bp.GetID()}: {bp.GetNumLocations()} 个位置")

        print("=" * 60)

    def zhc_types(self):
        """显示类型映射"""
        print("📋 中文C语言类型映射表:")
        print("=" * 60)
        for zhc_type, c_type in self.type_mapping.items():
            print(f"  {zhc_type:12s} → {c_type}")
        print("=" * 60)

    def zhc_symbols(self, debugger: lldb.SBDebugger):
        """
        显示符号列表

        Args:
            debugger: LLDB调试器实例
        """
        print("📋 程序符号列表:")
        print("=" * 60)

        target = debugger.GetSelectedTarget()
        if not target:
            print("❌ 没有选中的目标")
            return

        # 获取所有模块
        for i in range(target.GetNumModules()):
            module = target.GetModuleAtIndex(i)
            print(f"\n模块: {module.GetFileSpec().filename}")

            # 获取符号表
            num_symbols = module.GetNumSymbols()
            print(f"符号数: {num_symbols}")

            # 显示前20个符号
            count = 0
            for j in range(num_symbols):
                if count >= 20:
                    print("  ... (更多符号省略)")
                    break

                symbol = module.GetSymbolAtIndex(j)
                name = symbol.GetName()
                if name:
                    sym_type = symbol.GetType()
                    print(f"  {name}: {sym_type}")
                    count += 1

        print("=" * 60)

    def _translate_function_name(self, zhc_name: str) -> str:
        """
        转换中文函数名为C函数名

        Args:
            zhc_name: 中文函数名

        Returns:
            C函数名
        """
        if zhc_name == "主函数":
            return "main"
        return zhc_name

    def _translate_variable_name(self, zhc_name: str) -> str:
        """
        转换中文变量名为C变量名

        Args:
            zhc_name: 中文变量名

        Returns:
            C变量名
        """
        return zhc_name

    def _reverse_translate_function(self, c_name: str) -> str:
        """
        反向转换C函数名为中文函数名

        Args:
            c_name: C函数名

        Returns:
            中文函数名
        """
        if c_name == "main":
            return "主函数"
        return c_name


def zhc_help(
    debugger: lldb.SBDebugger,
    command: str,
    result: lldb.SBCommandReturnObject,
    internal_dict: dict,
):
    """zhc-help命令实现"""
    result.AppendMessage("""
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

示例:
  zhc-break 主函数    # 在main函数设置断点
  zhc-print 计数器    # 打印变量计数器的值
  zhc-where          # 显示调用栈
""")


def zhc_break(
    debugger: lldb.SBDebugger,
    command: str,
    result: lldb.SBCommandReturnObject,
    internal_dict: dict,
):
    """zhc-break命令实现"""
    if not command.strip():
        result.AppendMessage("用法: zhc-break <中文函数名>")
        result.AppendMessage("示例: zhc-break 主函数")
        return

    cmds = ZHCLLLDBCommands(debugger)
    cmds.zhc_break(command.strip(), debugger)


def zhc_list(
    debugger: lldb.SBDebugger,
    command: str,
    result: lldb.SBCommandReturnObject,
    internal_dict: dict,
):
    """zhc-list命令实现"""
    cmds = ZHCLLLDBCommands(debugger)
    cmds.zhc_list(debugger)


def zhc_print(
    debugger: lldb.SBDebugger,
    command: str,
    result: lldb.SBCommandReturnObject,
    internal_dict: dict,
):
    """zhc-print命令实现"""
    if not command.strip():
        result.AppendMessage("用法: zhc-print <中文变量名>")
        result.AppendMessage("示例: zhc-print 计数器")
        return

    cmds = ZHCLLLDBCommands(debugger)
    cmds.zhc_print(command.strip(), debugger)


def zhc_where(
    debugger: lldb.SBDebugger,
    command: str,
    result: lldb.SBCommandReturnObject,
    internal_dict: dict,
):
    """zhc-where命令实现"""
    cmds = ZHCLLLDBCommands(debugger)
    cmds.zhc_where(debugger)


def zhc_info(
    debugger: lldb.SBDebugger,
    command: str,
    result: lldb.SBCommandReturnObject,
    internal_dict: dict,
):
    """zhc-info命令实现"""
    cmds = ZHCLLLDBCommands(debugger)
    cmds.zhc_info(debugger)


def zhc_types(
    debugger: lldb.SBDebugger,
    command: str,
    result: lldb.SBCommandReturnObject,
    internal_dict: dict,
):
    """zhc-types命令实现"""
    cmds = ZHCLLLDBCommands(debugger)
    cmds.zhc_types()


def zhc_symbols(
    debugger: lldb.SBDebugger,
    command: str,
    result: lldb.SBCommandReturnObject,
    internal_dict: dict,
):
    """zhc-symbols命令实现"""
    cmds = ZHCLLLDBCommands(debugger)
    cmds.zhc_symbols(debugger)


# LLDB插件初始化函数
def __lldb_init_module(debugger: lldb.SBDebugger, internal_dict: dict):
    """
    LLDB插件初始化函数

    Args:
        debugger: LLDB调试器实例
        internal_dict: 内部字典
    """
    print("🎉 LLDB中文C语言插件加载中...")

    # 注册命令
    debugger.HandleCommand("command script add -f lldb_zhc.zhc_help zhc-help")
    debugger.HandleCommand("command script add -f lldb_zhc.zhc_break zhc-break")
    debugger.HandleCommand("command script add -f lldb_zhc.zhc_list zhc-list")
    debugger.HandleCommand("command script add -f lldb_zhc.zhc_print zhc-print")
    debugger.HandleCommand("command script add -f lldb_zhc.zhc_where zhc-where")
    debugger.HandleCommand("command script add -f lldb_zhc.zhc_info zhc-info")
    debugger.HandleCommand("command script add -f lldb_zhc.zhc_types zhc-types")
    debugger.HandleCommand("command script add -f lldb_zhc.zhc_symbols zhc-symbols")

    print("✅ LLDB中文C语言插件加载成功！")
    print("💡 输入 'zhc-help' 查看帮助信息")

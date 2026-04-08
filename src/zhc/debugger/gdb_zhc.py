"""
GDB调试器中文C语言支持
GDB Integration for ZHC Language

提供GDB Python API命令，支持中文C语言调试
"""

try:
    import gdb

    GDB_AVAILABLE = True
except ImportError:
    GDB_AVAILABLE = False

    # 创建模拟的gdb模块用于测试
    class MockGDB:
        class Command:
            def __init__(self, name, category):
                pass

        class error(Exception):
            pass

        COMMAND_BREAKPOINTS = 0
        COMMAND_FILES = 1
        COMMAND_DATA = 2
        COMMAND_STACK = 3
        COMMAND_STATUS = 4
        COMMAND_SUPPORT = 5

        @staticmethod
        def execute(cmd, to_string=False):
            return ""

        @staticmethod
        def selected_frame():
            return None

    gdb = MockGDB()

from typing import Dict, Optional


class ZHCGDBCommands:
    """GDB中文C语言命令集合"""

    def __init__(self):
        """初始化GDB命令"""
        self.source_files: Dict[str, str] = {}  # zhc文件映射
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
        """注册所有GDB命令"""
        # 注册zhc命令
        gdb.execute("""
            define zhc-help
            echo 中文C语言调试命令帮助\\n
            echo ================================\\n
            echo zhc-help          - 显示帮助信息\\n
            echo zhc-break         - 在中文函数设置断点\\n
            echo zhc-list          - 列出中文源码\\n
            echo zhc-print         - 打印中文变量\\n
            echo zhc-where         - 显示中文调用栈\\n
            echo zhc-info          - 显示程序信息\\n
            echo zhc-types         - 显示类型映射\\n
            echo zhc-symbols       - 显示符号列表\\n
            echo ================================\\n
            end
        """)

        # 注册zhc-break命令
        gdb.execute("""
            define zhc-break
            echo 设置断点命令\\n
            echo 用法: zhc-break <中文函数名>\\n
            echo 示例: zhc-break 主函数\\n
            end
        """)

        # 注册zhc-list命令
        gdb.execute("""
            define zhc-list
            echo 列出源码命令\\n
            echo 用法: zhc-list [行号]\\n
            end
        """)

        # 注册zhc-print命令
        gdb.execute("""
            define zhc-print
            echo 打印变量命令\\n
            echo 用法: zhc-print <中文变量名>\\n
            end
        """)

        print("✅ GDB中文C语言命令注册完成")

    def zhc_break(self, function_name: str):
        """
        在中文函数设置断点

        Args:
            function_name: 中文函数名（如"主函数"）
        """
        # 转换为C函数名
        c_func = self._translate_function_name(function_name)

        try:
            # 设置断点
            gdb.execute(f"break {c_func}")
            print(f"✅ 在函数 '{function_name}' ({c_func}) 设置断点成功")
        except gdb.error as e:
            print(f"❌ 设置断点失败: {e}")

    def zhc_list(self, start_line: Optional[int] = None, count: int = 10):
        """
        列出中文源码

        Args:
            start_line: 起始行号（可选）
            count: 显示行数
        """
        try:
            if start_line:
                gdb.execute(f"list {start_line},{start_line + count - 1}")
            else:
                gdb.execute("list")
        except gdb.error as e:
            print(f"❌ 列出源码失败: {e}")

    def zhc_print(self, var_name: str):
        """
        打印中文变量

        Args:
            var_name: 中文变量名
        """
        # 转换变量名
        c_var = self._translate_variable_name(var_name)

        try:
            # 打印变量
            result = gdb.execute(f"print {c_var}", to_string=True)
            print(result)
        except gdb.error as e:
            print(f"❌ 打印变量失败: {e}")

    def zhc_where(self):
        """显示中文调用栈"""
        try:
            # 获取调用栈
            frame = gdb.selected_frame()

            print("📋 中文C语言调用栈:")
            print("=" * 60)

            frame_num = 0
            while frame:
                func_name = frame.name()
                sal = frame.find_sal()

                # 转换函数名
                zhc_func = self._reverse_translate_function(func_name)

                # 显示信息
                print(f"#{frame_num}  {zhc_func} ({func_name})")
                if sal.symtab:
                    print(f"    at {sal.symtab.filename}:{sal.line}")

                frame = frame.older()
                frame_num += 1

            print("=" * 60)
        except gdb.error as e:
            print(f"❌ 获取调用栈失败: {e}")

    def zhc_info(self):
        """显示程序信息"""
        try:
            print("📊 中文C程序信息:")
            print("=" * 60)

            # 显示执行状态
            print(f"程序状态: {gdb.execute('info program', to_string=True).strip()}")

            # 显示断点
            print("\n断点列表:")
            print(gdb.execute("info breakpoints", to_string=True))

            # 显示线程
            print("\n线程信息:")
            print(gdb.execute("info threads", to_string=True))

            print("=" * 60)
        except gdb.error as e:
            print(f"❌ 获取程序信息失败: {e}")

    def zhc_types(self):
        """显示类型映射"""
        print("📋 中文C语言类型映射表:")
        print("=" * 60)
        for zhc_type, c_type in self.type_mapping.items():
            print(f"  {zhc_type:12s} → {c_type}")
        print("=" * 60)

    def zhc_symbols(self):
        """显示符号列表"""
        try:
            print("📋 程序符号列表:")
            print("=" * 60)

            # 获取所有函数
            symbols = gdb.execute("info functions", to_string=True)

            # 过滤并显示
            for line in symbols.split("\n"):
                if line.strip():
                    print(f"  {line}")

            print("=" * 60)
        except gdb.error as e:
            print(f"❌ 获取符号列表失败: {e}")

    def _translate_function_name(self, zhc_name: str) -> str:
        """
        转换中文函数名为C函数名

        Args:
            zhc_name: 中文函数名

        Returns:
            C函数名
        """
        # 特殊处理
        if zhc_name == "主函数":
            return "main"

        # 其他函数名保持不变（或添加前缀）
        return zhc_name

    def _translate_variable_name(self, zhc_name: str) -> str:
        """
        转换中文变量名为C变量名

        Args:
            zhc_name: 中文变量名

        Returns:
            C变量名
        """
        # 目前保持变量名不变
        return zhc_name

    def _reverse_translate_function(self, c_name: str) -> str:
        """
        反向转换C函数名为中文函数名

        Args:
            c_name: C函数名

        Returns:
            中文函数名
        """
        # 特殊处理
        if c_name == "main":
            return "主函数"

        # 其他函数名保持不变
        return c_name


class ZHCGDBPlugin:
    """GDB插件主类"""

    def __init__(self):
        """初始化插件"""
        self.commands = ZHCGDBCommands()
        self._register_all()

    def _register_all(self):
        """注册所有功能"""
        try:
            self.commands.register_commands()
            print("🎉 GDB中文C语言插件加载成功！")
            print("💡 输入 'zhc-help' 查看帮助信息")
        except Exception as e:
            print(f"❌ 插件加载失败: {e}")


# Python命令类
class ZHCBreakCommand(gdb.Command):
    """zhc-break命令"""

    def __init__(self):
        super().__init__("zhc-break", gdb.COMMAND_BREAKPOINTS)
        self.cmds = ZHCGDBCommands()

    def invoke(self, arg: str, from_tty: bool):
        """执行命令"""
        if not arg:
            print("用法: zhc-break <中文函数名>")
            print("示例: zhc-break 主函数")
            return

        self.cmds.zhc_break(arg.strip())


class ZHCListCommand(gdb.Command):
    """zhc-list命令"""

    def __init__(self):
        super().__init__("zhc-list", gdb.COMMAND_FILES)
        self.cmds = ZHCGDBCommands()

    def invoke(self, arg: str, from_tty: bool):
        """执行命令"""
        try:
            start_line = int(arg.strip()) if arg else None
            self.cmds.zhc_list(start_line)
        except ValueError:
            print("用法: zhc-list [行号]")
            print("示例: zhc-list 10")


class ZHCPrintCommand(gdb.Command):
    """zhc-print命令"""

    def __init__(self):
        super().__init__("zhc-print", gdb.COMMAND_DATA)
        self.cmds = ZHCGDBCommands()

    def invoke(self, arg: str, from_tty: bool):
        """执行命令"""
        if not arg:
            print("用法: zhc-print <中文变量名>")
            print("示例: zhc-print 计数器")
            return

        self.cmds.zhc_print(arg.strip())


class ZHCWhereCommand(gdb.Command):
    """zhc-where命令"""

    def __init__(self):
        super().__init__("zhc-where", gdb.COMMAND_STACK)
        self.cmds = ZHCGDBCommands()

    def invoke(self, arg: str, from_tty: bool):
        """执行命令"""
        self.cmds.zhc_where()


class ZHCInfoCommand(gdb.Command):
    """zhc-info命令"""

    def __init__(self):
        super().__init__("zhc-info", gdb.COMMAND_STATUS)
        self.cmds = ZHCGDBCommands()

    def invoke(self, arg: str, from_tty: bool):
        """执行命令"""
        self.cmds.zhc_info()


class ZHCTypesCommand(gdb.Command):
    """zhc-types命令"""

    def __init__(self):
        super().__init__("zhc-types", gdb.COMMAND_STATUS)
        self.cmds = ZHCGDBCommands()

    def invoke(self, arg: str, from_tty: bool):
        """执行命令"""
        self.cmds.zhc_types()


class ZHCSymbolsCommand(gdb.Command):
    """zhc-symbols命令"""

    def __init__(self):
        super().__init__("zhc-symbols", gdb.COMMAND_STATUS)
        self.cmds = ZHCGDBCommands()

    def invoke(self, arg: str, from_tty: bool):
        """执行命令"""
        self.cmds.zhc_symbols()


class ZHCHelpCommand(gdb.Command):
    """zhc-help命令"""

    def __init__(self):
        super().__init__("zhc-help", gdb.COMMAND_SUPPORT)

    def invoke(self, arg: str, from_tty: bool):
        """执行命令"""
        print("""
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


# 注册所有命令
def register_zhc_commands():
    """注册所有中文C语言命令"""
    ZHCHelpCommand()
    ZHCBreakCommand()
    ZHCListCommand()
    ZHCPrintCommand()
    ZHCWhereCommand()
    ZHCInfoCommand()
    ZHCTypesCommand()
    ZHCSymbolsCommand()

    print("✅ 所有GDB命令注册完成")


# 初始化
try:
    register_zhc_commands()
except NameError:
    # 不在GDB环境中
    pass

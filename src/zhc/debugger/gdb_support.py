"""
GDB 调试器支持模块

提供 GDB 兼容的调试功能：
- 生成 .gdbinit 配置
- 注册美化打印器
- 调试器命令集成
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol


class GDBCommand(Enum):
    """GDB 命令类型"""

    BREAK = "break"
    DELETE = "delete"
    RUN = "run"
    CONTINUE = "continue"
    STEP = "step"
    NEXT = "next"
    FINISH = "finish"
    PRINT = "print"
    BACKTRACE = "backtrace"
    INFO = "info"


@dataclass
class GDBConfig:
    """GDB 配置选项"""

    print_pretty: bool = True
    print_array: bool = True
    print_array_indexes: bool = True
    print_elements: int = 200
    print_repeats: int = 10
    disassembly_flavor: str = "intel"
    stop_at_entry: bool = False
    auto_load_scripts: bool = True


class PrettyPrinter(Protocol):
    """美化打印器协议"""

    def __init__(self, val: Any):
        """初始化打印器"""
        ...

    def to_string(self) -> str:
        """转换为字符串表示"""
        ...

    def children(self) -> Optional[List[tuple]]:
        """返回子元素（可选）"""
        ...

    def display_hint(self) -> str:
        """返回显示提示"""
        ...


@dataclass
class PrinterInfo:
    """打印器信息"""

    name: str
    pattern: str
    printer_class: type
    enabled: bool = True
    description: str = ""


class GDBPrettyPrinterRegistry:
    """GDB 美化打印器注册表"""

    def __init__(self, name: str = "zhc"):
        self.name = name
        self.printers: Dict[str, PrinterInfo] = {}

    def register(
        self, name: str, pattern: str, printer_class: type, description: str = ""
    ) -> None:
        """注册打印器"""
        self.printers[name] = PrinterInfo(
            name=name,
            pattern=pattern,
            printer_class=printer_class,
            description=description,
        )

    def unregister(self, name: str) -> bool:
        """注销打印器"""
        if name in self.printers:
            del self.printers[name]
            return True
        return False

    def enable(self, name: str) -> bool:
        """启用打印器"""
        if name in self.printers:
            self.printers[name].enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        """禁用打印器"""
        if name in self.printers:
            self.printers[name].enabled = False
            return True
        return False

    def generate_python_script(self) -> str:
        """生成 GDB Python 脚本"""
        script = '''"""
ZhC GDB 美化打印器
自动生成 - 请勿手动修改
"""

import gdb
from typing import Any, Optional, List


class ZHCStringPrinter:
    """ZhC 字符串美化打印器"""

    def __init__(self, val: gdb.Value):
        self.val = val

    def to_string(self) -> str:
        try:
            data = self.val['data']
            length = int(self.val['length'])
            if length == 0:
                return '""'
            # 读取字符串内容
            result = data.string(length=length)
            return f'"{result}"'
        except Exception as e:
            return f"<error: {e}>"

    def display_hint(self) -> str:
        return 'string'


class ZHCArrayPrinter:
    """ZhC 数组美化打印器"""

    def __init__(self, val: gdb.Value):
        self.val = val

    def to_string(self) -> str:
        try:
            length = int(self.val['length'])
            capacity = int(self.val['capacity'])
            elem_type = self.val.type.template_argument(0)
            return f"zhc_array<{elem_type}> [size={length}, capacity={capacity}]"
        except Exception:
            return "zhc_array"

    def children(self) -> List[tuple]:
        try:
            data = self.val['data']
            length = int(self.val['length'])
            result = []
            for i in range(min(length, 100)):  # 限制显示数量
                result.append((f"[{i}]", data[i]))
            if length > 100:
                result.append(("...", f"<{length - 100} more elements>"))
            return result
        except Exception:
            return []

    def display_hint(self) -> str:
        return 'array'


class ZHCMapPrinter:
    """ZhC 映射美化打印器"""

    def __init__(self, val: gdb.Value):
        self.val = val

    def to_string(self) -> str:
        try:
            size = int(self.val['size'])
            return f"zhc_map [size={size}]"
        except Exception:
            return "zhc_map"

    def children(self) -> List[tuple]:
        try:
            # 简化实现，实际需要遍历哈希表
            entries = self.val['entries']
            size = int(self.val['size'])
            result = []
            count = 0
            for i in range(min(size, 50)):
                entry = entries[i]
                if entry['occupied']:
                    key = entry['key']
                    value = entry['value']
                    result.append((f"[{key}]", value))
                    count += 1
            if size > 50:
                result.append(("...", f"<{size - 50} more entries>"))
            return result
        except Exception:
            return []

    def display_hint(self) -> str:
        return 'map'


class ZHCStructPrinter:
    """ZhC 结构体美化打印器"""

    def __init__(self, val: gdb.Value):
        self.val = val

    def to_string(self) -> str:
        type_name = str(self.val.type)
        return f"{type_name}"

    def children(self) -> List[tuple]:
        result = []
        for field in self.val.type.fields():
            result.append((field.name, self.val[field.name]))
        return result

    def display_hint(self) -> str:
        return 'struct'


def build_pretty_printer():
    """构建美化打印器集合"""
    pp = gdb.printing.RegexpCollectionPrettyPrinter("zhc")

    # 注册打印器
    pp.add_printer('string', r'^zhc_string$', ZHCStringPrinter)
    pp.add_printer('array', r'^zhc_array', ZHCArrayPrinter)
    pp.add_printer('map', r'^zhc_map', ZHCMapPrinter)
    pp.add_printer('struct', r'^zhc_struct', ZHCStructPrinter)

    return pp


def register_pretty_printers():
    """注册美化打印器到 GDB"""
    gdb.printing.register_pretty_printer(
        gdb.current_objfile(),
        build_pretty_printer()
    )


# 自动注册
register_pretty_printers()
'''
        return script


class GDBSupport:
    """GDB 调试器支持"""

    def __init__(self, config: Optional[GDBConfig] = None):
        self.config = config or GDBConfig()
        self.registry = GDBPrettyPrinterRegistry()
        self._setup_default_printers()

    def _setup_default_printers(self) -> None:
        """设置默认打印器"""
        # 这些将在生成的脚本中实现
        pass

    def generate_gdbinit(self, output_path: Optional[Path] = None) -> str:
        """生成 .gdbinit 配置文件"""
        config = self.config

        gdbinit = f"""# ZhC GDB 配置文件
# 自动生成 - 请勿手动修改

# 打印设置
set print pretty {"on" if config.print_pretty else "off"}
set print array {"on" if config.print_array else "off"}
set print array-indexes {"on" if config.print_array_indexes else "off"}
set print elements {config.print_elements}
set print repeats {config.print_repeats}

# 反汇编风格
set disassembly-flavor {config.disassembly_flavor}

# 自动加载脚本
{"set auto-load safe-path /" if config.auto_load_scripts else "# set auto-load safe-path /"}

# ZhC 美化打印器
# source /usr/share/zhc/gdb/zhc_pretty_printers.py

# 断点命令
define zhc-break
    break $arg0
end

define zhc-list
    info breakpoints
end

define zhc-delete
    delete $arg0
end

# 变量查看命令
define zhc-print
    print $arg0
end

define zhc-locals
    info locals
end

define zhc-args
    info args
end

# 调用栈命令
define zhc-bt
    backtrace
end

define zhc-frame
    frame $arg0
end

# 帮助信息
define zhc-help
    echo ZhC GDB Commands:\\n
    echo   zhc-break <loc>  - 设置断点\\n
    echo   zhc-list         - 列出断点\\n
    echo   zhc-delete <n>   - 删除断点\\n
    echo   zhc-print <var>  - 打印变量\\n
    echo   zhc-locals       - 显示局部变量\\n
    echo   zhc-args         - 显示函数参数\\n
    echo   zhc-bt           - 显示调用栈\\n
    echo   zhc-frame <n>    - 切换栈帧\\n
end

# 启动提示
echo ZhC GDB Support loaded. Type 'zhc-help' for commands.\\n
"""

        if output_path:
            output_path.write_text(gdbinit)

        return gdbinit

    def generate_pretty_printers(self, output_path: Optional[Path] = None) -> str:
        """生成美化打印器 Python 脚本"""
        script = self.registry.generate_python_script()

        if output_path:
            output_path.write_text(script)

        return script

    def generate_commands(self) -> Dict[str, str]:
        """生成自定义 GDB 命令"""
        return {
            "zhc-run": "启动程序调试",
            "zhc-break": "设置断点",
            "zhc-step": "单步进入",
            "zhc-next": "单步跳过",
            "zhc-print": "打印变量",
            "zhc-bt": "显示调用栈",
            "zhc-help": "显示帮助",
        }

    def create_debug_script(
        self, executable: Path, breakpoints: List[tuple], commands: List[str]
    ) -> str:
        """创建调试脚本"""
        script_lines = [
            "# ZhC 调试脚本",
            f"# 可执行文件: {executable}",
            "",
            f"file {executable}",
        ]

        # 添加断点
        for i, (location, condition) in enumerate(breakpoints):
            if condition:
                script_lines.append(f"break {location} if {condition}")
            else:
                script_lines.append(f"break {location}")

        # 添加命令
        script_lines.extend(commands)

        return "\n".join(script_lines)

    @staticmethod
    def check_gdb_available() -> bool:
        """检查 GDB 是否可用"""
        import shutil

        return shutil.which("gdb") is not None

    @staticmethod
    def get_gdb_version() -> Optional[str]:
        """获取 GDB 版本"""
        import subprocess

        try:
            result = subprocess.run(
                ["gdb", "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                # 提取版本号
                first_line = result.stdout.split("\n")[0]
                return first_line
        except Exception:
            pass
        return None

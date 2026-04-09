"""
LLDB 调试器支持模块

提供 LLDB 兼容的调试功能：
- 生成 .lldbinit 配置
- 注册数据格式化器
- 调试器命令集成
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol


class LLDBCommand(Enum):
    """LLDB 命令类型"""

    BREAKPOINT_SET = "breakpoint set"
    BREAKPOINT_DELETE = "breakpoint delete"
    RUN = "run"
    CONTINUE = "continue"
    STEP = "thread step-in"
    NEXT = "thread step-over"
    FINISH = "thread step-out"
    PRINT = "frame variable"
    BACKTRACE = "thread backtrace"
    FRAME_SELECT = "frame select"


@dataclass
class LLDBConfig:
    """LLDB 配置选项"""

    disassembly_flavor: str = "intel"
    stop_disassembly_display: str = "always"
    stop_line_count_after: int = 3
    stop_line_count_before: int = 3
    auto_load_scripts: bool = True
    target_x86_disassembly_flavor: str = "intel"


class DataFormatter(Protocol):
    """数据格式化器协议"""

    def format(self, valobj: Any) -> str:
        """格式化值对象"""
        ...


@dataclass
class FormatterInfo:
    """格式化器信息"""

    type_name: str
    formatter: DataFormatter
    enabled: bool = True
    is_regex: bool = False
    description: str = ""


class LLDBFormatterRegistry:
    """LLDB 数据格式化器注册表"""

    def __init__(self):
        self.formatters: Dict[str, FormatterInfo] = {}
        self.summaries: Dict[str, str] = {}
        self.synthetic_children: Dict[str, str] = {}

    def register_summary(
        self, type_name: str, summary_script: str, is_regex: bool = False
    ) -> None:
        """注册类型摘要"""
        self.summaries[type_name] = summary_script

    def register_synthetic(
        self, type_name: str, provider_script: str, is_regex: bool = False
    ) -> None:
        """注册合成子元素提供器"""
        self.synthetic_children[type_name] = provider_script

    def generate_python_script(self) -> str:
        """生成 LLDB Python 脚本"""
        script = '''"""
ZhC LLDB 数据格式化器
自动生成 - 请勿手动修改
"""

import lldb


def zhc_string_summary(valobj, internal_dict):
    """ZhC 字符串摘要"""
    try:
        length = valobj.GetChildMemberWithName("length").GetValueAsUnsigned()
        if length == 0:
            return '""'

        data = valobj.GetChildMemberWithName("data")
        error = lldb.SBError()
        string_data = data.GetPointeeData(0, length)
        result = string_data.GetString(error, 0)

        if error.Success():
            return f'"{result}"'
        else:
            return f'<error: {error}>'
    except Exception as e:
        return f'<error: {e}>'


def zhc_array_summary(valobj, internal_dict):
    """ZhC 数组摘要"""
    try:
        length = valobj.GetChildMemberWithName("length").GetValueAsUnsigned()
        capacity = valobj.GetChildMemberWithName("capacity").GetValueAsUnsigned()
        return f"size={length}, capacity={capacity}"
    except Exception:
        return "array"


def zhc_map_summary(valobj, internal_dict):
    """ZhC 映射摘要"""
    try:
        size = valobj.GetChildMemberWithName("size").GetValueAsUnsigned()
        return f"size={size}"
    except Exception:
        return "map"


class ZHCArraySyntheticProvider:
    """ZhC 数组合成子元素提供器"""

    def __init__(self, valobj, internal_dict):
        self.valobj = valobj
        self.update()

    def num_children(self):
        return min(self.length, 100)  # 限制显示数量

    def get_child_index(self, name):
        try:
            return int(name.lstrip("[").rstrip("]"))
        except ValueError:
            return -1

    def get_child_at_index(self, index):
        if index < 0 or index >= self.length:
            return None

        data = self.valobj.GetChildMemberWithName("data")
        return data.GetChildAtIndex(index)

    def update(self):
        self.length = self.valobj.GetChildMemberWithName("length").GetValueAsUnsigned()
        self.capacity = self.valobj.GetChildMemberWithName("capacity").GetValueAsUnsigned()


class ZHCMapSyntheticProvider:
    """ZhC 映射合成子元素提供器"""

    def __init__(self, valobj, internal_dict):
        self.valobj = valobj
        self.update()

    def num_children(self):
        return min(self.size, 50)  # 限制显示数量

    def get_child_index(self, name):
        try:
            return int(name.lstrip("[").rstrip("]"))
        except ValueError:
            return -1

    def get_child_at_index(self, index):
        if index < 0 or index >= self.size:
            return None

        entries = self.valobj.GetChildMemberWithName("entries")
        return entries.GetChildAtIndex(index)

    def update(self):
        self.size = self.valobj.GetChildMemberWithName("size").GetValueAsUnsigned()


def __lldb_init_module(debugger, internal_dict):
    """LLDB 模块初始化"""
    # 创建 ZhC 类别
    category = debugger.CreateCategory("zhc")
    category.SetEnabled(True)

    # 注册字符串摘要
    category.AddTypeSummary(
        lldb.SBTypeNameSpecifier("zhc_string"),
        lldb.SBTypeSummary.CreateWithScriptBody(
            "return zhc_string_summary(valobj, internal_dict)"
        )
    )

    # 注册数组摘要和合成子元素
    array_regex = lldb.SBTypeNameSpecifier("zhc_array", True)  # is_regex=True
    category.AddTypeSummary(
        array_regex,
        lldb.SBTypeSummary.CreateWithScriptBody(
            "return zhc_array_summary(valobj, internal_dict)"
        )
    )
    category.AddTypeSynthetic(
        array_regex,
        lldb.SBTypeSynthetic.CreateWithClassName(
            "__main__.ZHCArraySyntheticProvider"
        )
    )

    # 注册映射摘要和合成子元素
    map_regex = lldb.SBTypeNameSpecifier("zhc_map", True)
    category.AddTypeSummary(
        map_regex,
        lldb.SBTypeSummary.CreateWithScriptBody(
            "return zhc_map_summary(valobj, internal_dict)"
        )
    )
    category.AddTypeSynthetic(
        map_regex,
        lldb.SBTypeSynthetic.CreateWithClassName(
            "__main__.ZHCMapSyntheticProvider"
        )
    )

    print("ZhC LLDB Support loaded.")
'''
        return script


class LLDBSupport:
    """LLDB 调试器支持"""

    def __init__(self, config: Optional[LLDBConfig] = None):
        self.config = config or LLDBConfig()
        self.registry = LLDBFormatterRegistry()

    def generate_lldbinit(self, output_path: Optional[Path] = None) -> str:
        """生成 .lldbinit 配置文件"""
        config = self.config

        lldbinit = f"""# ZhC LLDB 配置文件
# 自动生成 - 请勿手动修改

# 反汇编设置
settings set target.x86-disassembly-flavor {config.target_x86_disassembly_flavor}
settings set stop-disassembly-display {config.stop_disassembly_display}
settings set stop-disassembly-count-after {config.stop_line_count_after}
settings set stop-disassembly-count-before {config.stop_line_count_before}

# 自动加载脚本
{"# settings set target.load-script-from-symbol-file true" if config.auto_load_scripts else ""}

# ZhC 数据格式化器
# command script import /usr/share/zhc/lldb/zhc_formatters.py

# 自定义命令
command alias zhc-b breakpoint set -f %1 -l %2
command alias zhc-bt thread backtrace
command alias zhc-p frame variable %1
command alias zhc-locals frame variable --no-args
command alias zhc-args frame variable --no-locals

# 启动提示
settings set prompt "(zhc-lldb) "

# 帮助命令
command script add -f lldb_mylab.help zhc-help

# 启动提示
echo ZhC LLDB Support loaded.
"""

        if output_path:
            output_path.write_text(lldbinit)

        return lldbinit

    def generate_formatters(self, output_path: Optional[Path] = None) -> str:
        """生成数据格式化器 Python 脚本"""
        script = self.registry.generate_python_script()

        if output_path:
            output_path.write_text(script)

        return script

    def generate_commands(self) -> Dict[str, str]:
        """生成自定义 LLDB 命令"""
        return {
            "zhc-run": "启动程序调试",
            "zhc-b": "设置断点 (zhc-b <file> <line>)",
            "zhc-step": "单步进入",
            "zhc-next": "单步跳过",
            "zhc-p": "打印变量",
            "zhc-bt": "显示调用栈",
            "zhc-locals": "显示局部变量",
            "zhc-args": "显示函数参数",
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
            f"target create {executable}",
        ]

        # 添加断点
        for i, (location, condition) in enumerate(breakpoints):
            if ":" in location:
                file, line = location.split(":")
                script_lines.append(f"breakpoint set -f {file} -l {line}")
            else:
                script_lines.append(f"breakpoint set -n {location}")

            if condition:
                # LLDB 条件断点
                bp_id = i + 1
                script_lines.append(f"breakpoint modify -c '{condition}' {bp_id}")

        # 添加命令
        script_lines.extend(commands)

        return "\n".join(script_lines)

    @staticmethod
    def check_lldb_available() -> bool:
        """检查 LLDB 是否可用"""
        import shutil

        return shutil.which("lldb") is not None

    @staticmethod
    def get_lldb_version() -> Optional[str]:
        """获取 LLDB 版本"""
        import subprocess

        try:
            result = subprocess.run(
                ["lldb", "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    @staticmethod
    def is_lldb_on_macos() -> bool:
        """检查是否在 macOS 上使用 LLDB"""
        import platform

        return platform.system() == "Darwin"

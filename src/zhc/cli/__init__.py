"""
命令行工具模块

包含：
- main: 主命令入口
- toolchain: 工具链

注意：ZHCCompiler 在 zhc.cli 模块（zhc/cli.py），由于包优先于模块，
需要使用 importlib 加载。
"""

from pathlib import Path

# 动态加载 zhc.cli（zhc/cli.py），因为包 zhc.cli/ 会遮盖模块
_cli_py_path = Path(__file__).parent.parent / "cli.py"

# 读取 cli.py 内容并执行，设置正确的 __package__
_cli_code = _cli_py_path.read_text(encoding="utf-8")
_exec_globals = {
    "__name__": "zhc.cli",
    "__package__": "zhc",
    "__file__": str(_cli_py_path),
}
exec(compile(_cli_code, str(_cli_py_path), "exec"), _exec_globals)

# 导出 ZHCCompiler 和 main
ZHCCompiler = _exec_globals["ZHCCompiler"]
main = _exec_globals["main"]

__all__ = ["ZHCCompiler", "main"]

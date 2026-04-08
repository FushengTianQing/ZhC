#!/usr/bin/env python3
"""ZHC 编译器入口点 — 将 src 目录注册为 zhc 包后加载 cli.py"""

import sys
import types
from pathlib import Path


def _ensure_zhc_package():
    """确保 zhc 包已注册到 sys.modules。

    项目内部模块通过 'from zhc.xxx import ...' 或相对导入互相引用，
    因此需要在加载 cli.py 前将 src 目录作为 'zhc' 包注入 sys.modules。
    """
    if "zhc" in sys.modules:
        return

    src_dir = Path(__file__).resolve().parent
    src_dir_str = str(src_dir)

    # 将 src 目录加入 sys.path（确保 from zhc.xxx 能找到）
    if src_dir_str not in sys.path:
        sys.path.insert(0, src_dir_str)

    # 创建一个包对象代表 zhc
    pkg = types.ModuleType("zhc")
    pkg.__path__ = [src_dir_str]
    pkg.__package__ = "zhc"
    pkg.__file__ = str(src_dir / "__init__.py")
    sys.modules["zhc"] = pkg


def main():
    """命令行入口"""
    _ensure_zhc_package()

    # 加载 cli.py
    cli_path = Path(__file__).parent / "cli.py"
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "zhc.cli", str(cli_path), submodule_search_locations=[]
    )
    cli_module = importlib.util.module_from_spec(spec)
    cli_module.__package__ = "zhc"
    cli_module.__name__ = "zhc.cli"
    sys.modules["zhc.cli"] = cli_module
    spec.loader.exec_module(cli_module)
    return cli_module.main()


if __name__ == "__main__":
    sys.exit(main())

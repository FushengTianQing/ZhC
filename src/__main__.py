#!/usr/bin/env python3
"""ZHC 编译器入口点 — 将 src 目录注册为 zhpp 包后加载 cli.py"""

import sys
from pathlib import Path


def _ensure_zhpp_package():
    """确保 zhpp 包已注册到 sys.modules。

    项目内部模块通过 'from zhpp.xxx import ...' 或相对导入互相引用，
    因此需要在加载 cli.py 前将 src 目录作为 'zhpp' 包注入 sys.modules。
    """
    if "zhpp" in sys.modules:
        return

    src_dir = Path(__file__).resolve().parent

    # 将 src 目录加入 sys.path（确保 from zhpp.xxx 能找到）
    src_dir_str = str(src_dir)
    if src_dir_str not in sys.path:
        sys.path.insert(0, src_dir_str)

    # 创建一个包对象代表 zhpp
    import types

    pkg = types.ModuleType("zhpp")
    pkg.__path__ = [src_dir_str]
    pkg.__package__ = "zhpp"
    pkg.__file__ = str(src_dir / "__init__.py")
    sys.modules["zhpp"] = pkg

    # 也用别名 zhc 注册（兼容 pyproject.toml 中的声明）
    if "zhc" not in sys.modules:
        zhc_pkg = types.ModuleType("zhc")
        zhc_pkg.__path__ = [src_dir_str]
        zhc_pkg.__package__ = "zhc"
        zhc_pkg.__file__ = str(src_dir / "__init__.py")
        sys.modules["zhc"] = zhc_pkg


def main():
    """命令行入口"""
    _ensure_zhpp_package()

    # 加载 cli.py
    cli_path = Path(__file__).parent / "cli.py"
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "zhpp.cli", str(cli_path), submodule_search_locations=[]
    )
    cli_module = importlib.util.module_from_spec(spec)
    cli_module.__package__ = "zhpp"
    cli_module.__name__ = "zhpp.cli"
    sys.modules["zhpp.cli"] = cli_module
    spec.loader.exec_module(cli_module)
    return cli_module.main()


if __name__ == "__main__":
    sys.exit(main())

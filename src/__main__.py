#!/usr/bin/env python3
"""zhpp 包入口点"""

import sys
from pathlib import Path

def main():
    """命令行入口"""
    # 直接加载 cli.py 文件（避免与 cli/ 包冲突）
    cli_path = Path(__file__).parent / "cli.py"
    import importlib.util
    spec = importlib.util.spec_from_file_location("zhpp_cli_module", str(cli_path),
                                                   submodule_search_locations=[])
    cli_module = importlib.util.module_from_spec(spec)
    # 设置包上下文，让相对导入 (.keywords) 工作
    cli_module.__package__ = "zhpp"
    sys.modules["zhpp_cli_module"] = cli_module
    spec.loader.exec_module(cli_module)
    return cli_module.main()

if __name__ == '__main__':
    sys.exit(main())

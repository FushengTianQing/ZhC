"""
pytest 配置文件

配置测试环境和共享 fixtures。
"""

import sys
import types
from pathlib import Path

# 确保可以导入 src/zhpp
SRC_ROOT = Path(__file__).resolve().parent.parent / "src"
SRC_ROOT_STR = str(SRC_ROOT)
if SRC_ROOT_STR not in sys.path:
    sys.path.insert(0, SRC_ROOT_STR)

# 将 src 目录作为 zhpp 包注册到 sys.modules
# 项目内部模块统一使用 "from zhpp.xxx import ..." 的导入方式
if "zhpp" not in sys.modules:
    _zhpp_pkg = types.ModuleType("zhpp")
    _zhpp_pkg.__path__ = [SRC_ROOT_STR]
    _zhpp_pkg.__package__ = "zhpp"
    _zhpp_pkg.__file__ = str(SRC_ROOT / "__init__.py")
    sys.modules["zhpp"] = _zhpp_pkg

# 兼容 pyproject.toml 中声明的 zhc 包名
if "zhc" not in sys.modules:
    _zhc_pkg = types.ModuleType("zhc")
    _zhc_pkg.__path__ = [SRC_ROOT_STR]
    _zhc_pkg.__package__ = "zhc"
    _zhc_pkg.__file__ = str(SRC_ROOT / "__init__.py")
    sys.modules["zhc"] = _zhc_pkg
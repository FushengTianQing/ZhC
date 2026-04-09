"""
pytest 配置文件

配置测试环境和共享 fixtures。
"""

import sys
from pathlib import Path

# 确保可以导入 src（作为 zhc 包）
SRC_ROOT = Path(__file__).resolve().parent.parent / "src"
SRC_ROOT_STR = str(SRC_ROOT)
if SRC_ROOT_STR not in sys.path:
    sys.path.insert(0, SRC_ROOT_STR)

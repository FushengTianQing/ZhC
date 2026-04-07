"""
pytest 配置文件

配置测试环境和共享 fixtures。
"""

import sys
from pathlib import Path

# 确保可以导入 src/zhpp
SRC_ROOT = Path(__file__).parent.parent / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
# -*- coding: utf-8 -*-
"""
ZhC 优化级别定义

定义编译器支持的优化级别，从 O0（无优化）到 Oz（极致大小优化）。

优化级别说明：
- O0: 调试级别，保留完整调试信息，编译最快
- O1: 基础优化，快速编译，少量优化
- O2: 标准优化，平衡编译速度和性能（推荐）
- O3: 激进优化，最大性能，可能增加代码大小
- Os: 大小优化，优先代码大小
- Oz: 极致大小优化，最小代码

作者：远
日期：2026-04-09
"""

from enum import Enum
from dataclasses import dataclass
from typing import List


@dataclass
class OptimizationLevelInfo:
    """优化级别详细信息"""

    level: "OptimizationLevel"
    name: str
    display_name: str
    description: str
    typical_speedup: str  # 相对于 O0 的典型加速比
    typical_size: str  # 相对于 O0 的典型大小变化

    def __str__(self) -> str:
        return f"{self.display_name}: {self.description}"


class OptimizationLevel(Enum):
    """
    编译器优化级别枚举

    使用方式：
        level = OptimizationLevel.O2
        if level >= OptimizationLevel.O2:
            # 应用 O2 及以上优化
    """

    O0 = 0  # 无优化 - 快速编译，保留调试信息
    O1 = 1  # 基本优化 - 快速编译，少量优化
    O2 = 2  # 标准优化 - 平衡编译速度和性能（推荐）
    O3 = 3  # 激进优化 - 最大性能
    Os = 4  # 大小优化 - 优先代码大小
    Oz = 5  # 极致大小优化 - 最小代码

    def __ge__(self, other: "OptimizationLevel") -> bool:
        """比较优化级别是否大于等于"""
        return self.value >= other.value

    def __gt__(self, other: "OptimizationLevel") -> bool:
        """比较优化级别是否大于"""
        return self.value > other.value

    def __le__(self, other: "OptimizationLevel") -> bool:
        """比较优化级别是否小于等于"""
        return self.value <= other.value

    def __lt__(self, other: "OptimizationLevel") -> bool:
        """比较优化级别是否小于"""
        return self.value < other.value

    @property
    def info(self) -> OptimizationLevelInfo:
        """获取优化级别详细信息"""
        return OPTIMIZATION_LEVELS[self]

    @property
    def is_debug(self) -> bool:
        """是否为调试级别（O0）"""
        return self == OptimizationLevel.O0

    @property
    def is_size_optimization(self) -> bool:
        """是否为大小优化级别（Os 或 Oz）"""
        return self in (OptimizationLevel.Os, OptimizationLevel.Oz)

    @property
    def is_speed_optimization(self) -> bool:
        """是否为速度优化级别（O1-O3）"""
        return self in (
            OptimizationLevel.O1,
            OptimizationLevel.O2,
            OptimizationLevel.O3,
        )

    @property
    def passes_hint(self) -> List[str]:
        """获取该优化级别使用的 Pass 列表提示"""
        return OPTIMIZATION_PASS_HINTS.get(self, [])


# 优化级别详细信息
OPTIMIZATION_LEVELS = {
    OptimizationLevel.O0: OptimizationLevelInfo(
        level=OptimizationLevel.O0,
        name="O0",
        display_name="O0 (Debug)",
        description="无优化，保留调试信息，编译最快",
        typical_speedup="1x",
        typical_size="1x",
    ),
    OptimizationLevel.O1: OptimizationLevelInfo(
        level=OptimizationLevel.O1,
        name="O1",
        display_name="O1 (Fast)",
        description="基本优化，快速编译，少量优化",
        typical_speedup="1.5-2x",
        typical_size="~1x",
    ),
    OptimizationLevel.O2: OptimizationLevelInfo(
        level=OptimizationLevel.O2,
        name="O2",
        display_name="O2 (Balanced)",
        description="标准优化，平衡编译速度和性能（推荐）",
        typical_speedup="2-4x",
        typical_size="~1.1x",
    ),
    OptimizationLevel.O3: OptimizationLevelInfo(
        level=OptimizationLevel.O3,
        name="O3",
        display_name="O3 (Aggressive)",
        description="激进优化，最大性能，可能增加代码大小",
        typical_speedup="3-8x",
        typical_size="~1.2x",
    ),
    OptimizationLevel.Os: OptimizationLevelInfo(
        level=OptimizationLevel.Os,
        name="Os",
        display_name="Os (Size)",
        description="大小优化，优先代码大小",
        typical_speedup="1.5-3x",
        typical_size="~0.7x",
    ),
    OptimizationLevel.Oz: OptimizationLevelInfo(
        level=OptimizationLevel.Oz,
        name="Oz",
        display_name="Oz (MinSize)",
        description="极致大小优化，最小代码",
        typical_speedup="1.5-3x",
        typical_size="~0.6x",
    ),
}

# 各优化级别使用的 Pass 列表提示
# 详细实现见 pass_config.py
OPTIMIZATION_PASS_HINTS = {
    OptimizationLevel.O0: [
        "no-op",
        "verify",
    ],
    OptimizationLevel.O1: [
        "inline",
        "mem2reg",
        "early-cse",
        "gvn",
        "dce",
    ],
    OptimizationLevel.O2: [
        "inline",
        "mem2reg",
        "loop-rotate",
        "licm",
        "loop-unswitch",
        "indvars",
        "gvn",
        "sccp",
        "dce",
        "adce",
        "reassociate",
        "simplifycfg",
        "mergeret",
    ],
    OptimizationLevel.O3: [
        "inline",
        "mem2reg",
        "loop-rotate",
        "licm",
        "loop-unswitch",
        "indvars",
        "gvn",
        "sccp",
        "dce",
        "adce",
        "reassociate",
        "simplifycfg",
        "mergeret",
        "loop-unroll",
        "loop-vectorize",
        "slp-vectorize",
        "gvn-hoist",
        "aggressive-dce",
        "function-attrs",
    ],
    OptimizationLevel.Os: [
        "inline",
        "mem2reg",
        "loop-rotate",
        "gvn",
        "dce",
        "adce",
        "simplifycfg",
        "mergefunc",
        "constmerge",
    ],
    OptimizationLevel.Oz: [
        "inline",
        "mem2reg",
        "gvn",
        "dce",
        "adce",
        "simplifycfg",
        "mergefunc",
        "constmerge",
        "globalopt",
    ],
}


def parse_optimization_level(level_str: str) -> OptimizationLevel:
    """
    从字符串解析优化级别

    Args:
        level_str: 优化级别字符串，如 "O2", "O3", "s", "z"

    Returns:
        对应的 OptimizationLevel 枚举值

    Raises:
        ValueError: 无法解析的优化级别
    """
    level_str = level_str.lower().strip()

    # 处理数字
    if level_str.isdigit():
        level_int = int(level_str)
        for level in OptimizationLevel:
            if level.value == level_int:
                return level
        raise ValueError(f"未知的优化级别值: {level_int}")

    # 处理字符串名称
    level_map = {
        "o0": OptimizationLevel.O0,
        "o1": OptimizationLevel.O1,
        "o2": OptimizationLevel.O2,
        "o3": OptimizationLevel.O3,
        "os": OptimizationLevel.Os,
        "oz": OptimizationLevel.Oz,
        "0": OptimizationLevel.O0,
        "1": OptimizationLevel.O1,
        "2": OptimizationLevel.O2,
        "3": OptimizationLevel.O3,
        "s": OptimizationLevel.Os,
        "z": OptimizationLevel.Oz,
        "size": OptimizationLevel.Os,
        "minsize": OptimizationLevel.Oz,
        "none": OptimizationLevel.O0,
        "fast": OptimizationLevel.O3,
    }

    if level_str in level_map:
        return level_map[level_str]

    raise ValueError(f"无法解析优化级别: {level_str}")

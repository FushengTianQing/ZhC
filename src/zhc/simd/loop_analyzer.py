# -*- coding: utf-8 -*-
"""
ZhC 循环分析器

分析循环结构，识别归纳变量和依赖关系，判断循环是否可向量化。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class InductionType(Enum):
    """归纳变量类型"""

    INT = "int"  # 整数归纳变量
    FLOAT = "float"  # 浮点归纳变量
    POINTER = "pointer"  # 指针归纳变量
    UNKNOWN = "unknown"


@dataclass
class InductionVariable:
    """
    归纳变量信息

    表示循环中的归纳变量及其属性。
    """

    name: str  # 变量名
    var_type: InductionType  # 变量类型
    step_value: Optional[float] = None  # 步进值
    start_value: Optional[float] = None  # 起始值
    base_ptr: Optional[str] = None  # 基础指针（如果是指针归纳）

    def __repr__(self) -> str:
        return f"InductionVariable({self.name}, step={self.step_value})"


@dataclass
class Loop:
    """
    循环结构信息

    描述一个分析过的循环及其属性。
    """

    header_block: str  # 循环头基本块
    latch_block: str  # 循环 latch 基本块
    exit_block: str  # 退出基本块

    # 循环范围
    trip_count: Optional[int] = None  # 循环次数（如果已知）
    trip_count_estimate: Optional[int] = None  # 循环次数估计

    # 归纳变量
    induction_vars: List[InductionVariable] = field(default_factory=list)  # 主归纳变量
    all_induction_vars: List[InductionVariable] = field(
        default_factory=list
    )  # 所有归纳变量

    # 循环体内的指令信息
    num_instructions: int = 0  # 指令数
    num_loads: int = 0  # 加载数
    num_stores: int = 0  # 存储数

    # 可向量化性分析
    is_vectorizable: bool = True  # 是否可向量化
    vectorization_issues: List[str] = field(default_factory=list)  # 向量化问题列表
    dependencies: List[Tuple[str, str]] = field(default_factory=list)  # 依赖关系

    # 循环不变代码
    loop_invariant_code: List[str] = field(default_factory=list)  # 循环不变代码

    def add_issue(self, issue: str) -> None:
        """添加向量化问题"""
        self.vectorization_issues.append(issue)
        if issue in ("has_recurrence", "has_unknown_dependencies"):
            self.is_vectorizable = False

    def get_trip_count_hint(self) -> str:
        """获取循环次数提示"""
        if self.trip_count is not None:
            return f"exact={self.trip_count}"
        elif self.trip_count_estimate is not None:
            return f"estimate={self.trip_count_estimate}"
        else:
            return "unknown"


@dataclass
class LoopInfo:
    """
    循环分析结果

    包含函数中所有循环的分析结果。
    """

    loops: List[Loop] = field(default_factory=list)  # 所有循环
    max_nesting_depth: int = 0  # 最大嵌套深度
    vectorizable_loops: List[Loop] = field(default_factory=list)  # 可向量化循环

    def add_loop(self, loop: Loop) -> None:
        """添加循环"""
        self.loops.append(loop)
        if loop.is_vectorizable:
            self.vectorizable_loops.append(loop)


class LoopAnalyzer:
    """
    循环分析器

    分析函数中的循环结构，识别归纳变量和依赖关系。
    """

    @classmethod
    def analyze(cls, func_body: str) -> LoopInfo:
        """
        分析函数体中的循环

        Args:
            func_body: 函数体代码

        Returns:
            循环分析结果
        """
        info = LoopInfo()

        # 简单的基于文本的分析
        # 在实际实现中，应该基于 LLVM IR 分析
        lines = func_body.split("\n")
        loop_stack = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 检测循环开始
            if (
                stripped.startswith("循环 ")
                or stripped.startswith("for ")
                or stripped.startswith("while ")
            ):
                # 尝试提取循环信息
                loop = cls._analyze_loop_header(stripped, i)
                if loop:
                    loop_stack.append(loop)

            # 检测循环体结束
            elif "}" in stripped and loop_stack:
                # 结束当前循环
                completed_loop = loop_stack.pop()
                if completed_loop.is_vectorizable:
                    info.vectorizable_loops.append(completed_loop)
                info.loops.append(completed_loop)

        info.max_nesting_depth = cls._calculate_max_depth(info.loops)

        return info

    @classmethod
    def _analyze_loop_header(cls, header: str, line_num: int) -> Optional[Loop]:
        """分析循环头部"""
        # 简化实现：基于语法分析
        loop = Loop(
            header_block=f"entry_{line_num}",
            latch_block=f"latch_{line_num}",
            exit_block=f"exit_{line_num}",
        )

        # 尝试识别归纳变量
        # 格式: 循环 i 从 0 到 n，步长 1
        if "从" in header and "到" in header:
            try:
                # 简单提取循环变量
                if "i" in header:
                    loop.induction_vars.append(
                        InductionVariable(
                            name="i",
                            var_type=InductionType.INT,
                            step_value=1.0,
                        )
                    )
            except Exception:
                pass

        # 检查循环次数
        for num in range(2, 1000):
            if f"到 {num}" in header or f"到{num}" in header:
                loop.trip_count_estimate = num
                break

        # 简化分析：假设可向量化
        loop.is_vectorizable = True

        return loop

    @classmethod
    def _calculate_max_depth(cls, loops: List[Loop]) -> int:
        """计算最大嵌套深度"""
        # 简化实现
        return len(loops)

    @classmethod
    def check_vectorization_feasibility(cls, loop: Loop) -> Tuple[bool, List[str]]:
        """
        检查循环是否可向量化

        Args:
            loop: 循环信息

        Returns:
            (是否可向量化, 问题列表)
        """
        issues = []

        # 检查基本可向量化条件
        if not loop.induction_vars:
            issues.append("no_induction_variable")

        # 检查循环次数
        if loop.trip_count == 0:
            issues.append("zero_trip_loop")

        # 检查依赖关系
        if loop.dependencies:
            issues.append("has_dependencies")

        # 检查向量长度
        if loop.trip_count and loop.trip_count < 4:
            issues.append("trip_count_too_small")

        is_vectorizable = len(issues) == 0

        return is_vectorizable, issues

    @classmethod
    def find_induction_variables(cls, loop: Loop) -> List[InductionVariable]:
        """
        查找循环中的归纳变量

        Args:
            loop: 循环信息

        Returns:
            归纳变量列表
        """
        # 简化实现
        return loop.induction_vars

    @classmethod
    def compute_trip_count(cls, loop: Loop) -> Optional[int]:
        """
        计算循环次数

        Args:
            loop: 循环信息

        Returns:
            循环次数，如果无法计算返回 None
        """
        if loop.trip_count is not None:
            return loop.trip_count

        if loop.trip_count_estimate is not None:
            return loop.trip_count_estimate

        # 尝试从归纳变量推断
        for ind_var in loop.induction_vars:
            if ind_var.step_value and ind_var.start_value is not None:
                # 假设结束值为 trip_count * step + start
                pass

        return None

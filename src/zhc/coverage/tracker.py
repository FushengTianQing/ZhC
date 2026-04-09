#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
覆盖率追踪器

追踪代码执行过程中的覆盖率数据
"""

import atexit
import threading
from typing import Dict, List, Optional, Set
from .data import ProjectCoverage


class CoverageTracker:
    """覆盖率追踪器"""

    _instance: Optional["CoverageTracker"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "CoverageTracker":
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化"""
        if self._initialized:
            return
        self._initialized = True

        self.coverage = ProjectCoverage()
        self.enabled = False
        self._current_file: Optional[str] = None
        self._current_function: Optional[str] = None
        self._branch_counter = 0
        self._function_counter = 0
        self._line_hits: Dict[str, Set[int]] = {}
        self._branch_hits: Dict[str, Dict[str, bool]] = {}
        self._function_hits: Dict[str, Dict[str, int]] = {}

        # 注册退出时保存
        atexit.register(self._on_exit)

    def start(self) -> None:
        """开始追踪"""
        self.enabled = True

    def stop(self) -> None:
        """停止追踪"""
        self.enabled = False

    def reset(self) -> None:
        """重置覆盖率数据"""
        self.coverage = ProjectCoverage()
        self._line_hits.clear()
        self._branch_hits.clear()
        self._function_hits.clear()
        self._branch_counter = 0
        self._function_counter = 0

    def register_file(self, file_path: str, executable_lines: List[int] = None) -> None:
        """注册文件"""
        file_cov = self.coverage.add_file(file_path)
        if executable_lines:
            for line in executable_lines:
                file_cov.add_line(line, is_executable=True)

    def register_function(
        self, file_path: str, function_name: str, start_line: int, end_line: int
    ) -> None:
        """注册函数"""
        file_cov = self.coverage.get_file(file_path)
        if file_cov:
            file_cov.add_function(function_name, start_line, end_line)

    def register_branch(self, file_path: str, line_number: int) -> str:
        """注册分支，返回分支ID"""
        branch_id = f"branch_{self._branch_counter}"
        self._branch_counter += 1

        file_cov = self.coverage.get_file(file_path)
        if file_cov:
            file_cov.add_branch(branch_id, line_number)

        return branch_id

    def hit_line(self, file_path: str, line_number: int) -> None:
        """记录行执行"""
        if not self.enabled:
            return

        file_cov = self.coverage.get_file(file_path)
        if file_cov:
            file_cov.hit_line(line_number)

        # 记录到本地缓存
        if file_path not in self._line_hits:
            self._line_hits[file_path] = set()
        self._line_hits[file_path].add(line_number)

    def hit_branch(self, file_path: str, branch_id: str, taken: bool) -> None:
        """记录分支执行"""
        if not self.enabled:
            return

        file_cov = self.coverage.get_file(file_path)
        if file_cov:
            if taken:
                file_cov.hit_branch_true(branch_id)
            else:
                file_cov.hit_branch_false(branch_id)

        # 记录到本地缓存
        if file_path not in self._branch_hits:
            self._branch_hits[file_path] = {}
        self._branch_hits[file_path][branch_id] = True

    def hit_function(self, file_path: str, function_name: str) -> None:
        """记录函数调用"""
        if not self.enabled:
            return

        file_cov = self.coverage.get_file(file_path)
        if file_cov:
            file_cov.hit_function(function_name)

        # 记录到本地缓存
        if file_path not in self._function_hits:
            self._function_hits[file_path] = {}
        if function_name not in self._function_hits[file_path]:
            self._function_hits[file_path][function_name] = 0
        self._function_hits[file_path][function_name] += 1

    def get_coverage(self) -> ProjectCoverage:
        """获取覆盖率数据"""
        return self.coverage

    def get_line_coverage_rate(self) -> float:
        """获取行覆盖率"""
        return self.coverage.line_coverage_rate

    def get_branch_coverage_rate(self) -> float:
        """获取分支覆盖率"""
        return self.coverage.branch_coverage_rate

    def get_function_coverage_rate(self) -> float:
        """获取函数覆盖率"""
        return self.coverage.function_coverage_rate

    def _on_exit(self) -> None:
        """退出时处理"""
        if self.enabled:
            self.stop()

    def merge(self, other: "CoverageTracker") -> None:
        """合并另一个追踪器的数据"""
        for file_path, file_cov in other.coverage.files.items():
            my_file = self.coverage.get_file(file_path)
            if my_file is None:
                my_file = self.coverage.add_file(file_path)

            # 合并行覆盖率
            for line_num, line_cov in file_cov.lines.items():
                if line_num not in my_file.lines:
                    my_file.lines[line_num] = line_cov
                else:
                    my_file.lines[line_num].hit_count += line_cov.hit_count

            # 合并分支覆盖率
            for branch_id, branch_cov in file_cov.branches.items():
                if branch_id not in my_file.branches:
                    my_file.branches[branch_id] = branch_cov
                else:
                    my_file.branches[branch_id].true_hits += branch_cov.true_hits
                    my_file.branches[branch_id].false_hits += branch_cov.false_hits

            # 合并函数覆盖率
            for func_name, func_cov in file_cov.functions.items():
                if func_name not in my_file.functions:
                    my_file.functions[func_name] = func_cov
                else:
                    my_file.functions[func_name].hit_count += func_cov.hit_count


# 全局追踪器实例
_tracker: Optional[CoverageTracker] = None


def get_tracker() -> CoverageTracker:
    """获取全局追踪器"""
    global _tracker
    if _tracker is None:
        _tracker = CoverageTracker()
    return _tracker


def start_coverage() -> None:
    """开始覆盖率追踪"""
    get_tracker().start()


def stop_coverage() -> None:
    """停止覆盖率追踪"""
    get_tracker().stop()


def reset_coverage() -> None:
    """重置覆盖率数据"""
    get_tracker().reset()


def get_coverage() -> ProjectCoverage:
    """获取覆盖率数据"""
    return get_tracker().get_coverage()

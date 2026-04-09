#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
覆盖率数据结构

定义覆盖率追踪所需的数据结构
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum
import json


class CoverageType(Enum):
    """覆盖率类型"""

    LINE = "line"  # 行覆盖率
    BRANCH = "branch"  # 分支覆盖率
    FUNCTION = "function"  # 函数覆盖率


@dataclass
class LineCoverage:
    """行覆盖率数据"""

    line_number: int
    hit_count: int = 0
    is_executable: bool = True

    @property
    def is_covered(self) -> bool:
        """是否被覆盖"""
        return self.hit_count > 0


@dataclass
class BranchCoverage:
    """分支覆盖率数据"""

    branch_id: str
    line_number: int
    true_hits: int = 0
    false_hits: int = 0

    @property
    def total_hits(self) -> int:
        """总命中次数"""
        return self.true_hits + self.false_hits

    @property
    def is_covered(self) -> bool:
        """是否被覆盖（两个分支都被执行过）"""
        return self.true_hits > 0 and self.false_hits > 0

    @property
    def partial_coverage(self) -> bool:
        """部分覆盖"""
        return (self.true_hits > 0) != (self.false_hits > 0)


@dataclass
class FunctionCoverage:
    """函数覆盖率数据"""

    function_name: str
    start_line: int
    end_line: int
    hit_count: int = 0

    @property
    def is_covered(self) -> bool:
        """是否被覆盖"""
        return self.hit_count > 0


@dataclass
class FileCoverage:
    """文件覆盖率数据"""

    file_path: str
    lines: Dict[int, LineCoverage] = field(default_factory=dict)
    branches: Dict[str, BranchCoverage] = field(default_factory=dict)
    functions: Dict[str, FunctionCoverage] = field(default_factory=dict)

    @property
    def total_lines(self) -> int:
        """总可执行行数"""
        return sum(1 for line in self.lines.values() if line.is_executable)

    @property
    def covered_lines(self) -> int:
        """已覆盖行数"""
        return sum(1 for line in self.lines.values() if line.is_covered)

    @property
    def line_coverage_rate(self) -> float:
        """行覆盖率"""
        total = self.total_lines
        if total == 0:
            return 1.0
        return self.covered_lines / total

    @property
    def total_branches(self) -> int:
        """总分支数"""
        return len(self.branches) * 2  # 每个分支有两个方向

    @property
    def covered_branches(self) -> int:
        """已覆盖分支数"""
        covered = 0
        for branch in self.branches.values():
            if branch.true_hits > 0:
                covered += 1
            if branch.false_hits > 0:
                covered += 1
        return covered

    @property
    def branch_coverage_rate(self) -> float:
        """分支覆盖率"""
        total = self.total_branches
        if total == 0:
            return 1.0
        return self.covered_branches / total

    @property
    def total_functions(self) -> int:
        """总函数数"""
        return len(self.functions)

    @property
    def covered_functions(self) -> int:
        """已覆盖函数数"""
        return sum(1 for func in self.functions.values() if func.is_covered)

    @property
    def function_coverage_rate(self) -> float:
        """函数覆盖率"""
        total = self.total_functions
        if total == 0:
            return 1.0
        return self.covered_functions / total

    def add_line(self, line_number: int, is_executable: bool = True) -> None:
        """添加行"""
        if line_number not in self.lines:
            self.lines[line_number] = LineCoverage(
                line_number=line_number, is_executable=is_executable
            )

    def hit_line(self, line_number: int) -> None:
        """记录行执行"""
        if line_number in self.lines:
            self.lines[line_number].hit_count += 1

    def add_branch(self, branch_id: str, line_number: int) -> None:
        """添加分支"""
        if branch_id not in self.branches:
            self.branches[branch_id] = BranchCoverage(
                branch_id=branch_id, line_number=line_number
            )

    def hit_branch_true(self, branch_id: str) -> None:
        """记录分支 true 路径"""
        if branch_id in self.branches:
            self.branches[branch_id].true_hits += 1

    def hit_branch_false(self, branch_id: str) -> None:
        """记录分支 false 路径"""
        if branch_id in self.branches:
            self.branches[branch_id].false_hits += 1

    def add_function(self, function_name: str, start_line: int, end_line: int) -> None:
        """添加函数"""
        if function_name not in self.functions:
            self.functions[function_name] = FunctionCoverage(
                function_name=function_name, start_line=start_line, end_line=end_line
            )

    def hit_function(self, function_name: str) -> None:
        """记录函数调用"""
        if function_name in self.functions:
            self.functions[function_name].hit_count += 1

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "file_path": self.file_path,
            "line_coverage": {
                "total": self.total_lines,
                "covered": self.covered_lines,
                "rate": self.line_coverage_rate,
                "lines": {
                    str(line.line_number): {
                        "hit_count": line.hit_count,
                        "is_executable": line.is_executable,
                    }
                    for line in self.lines.values()
                },
            },
            "branch_coverage": {
                "total": self.total_branches,
                "covered": self.covered_branches,
                "rate": self.branch_coverage_rate,
                "branches": {
                    branch.branch_id: {
                        "line": branch.line_number,
                        "true_hits": branch.true_hits,
                        "false_hits": branch.false_hits,
                    }
                    for branch in self.branches.values()
                },
            },
            "function_coverage": {
                "total": self.total_functions,
                "covered": self.covered_functions,
                "rate": self.function_coverage_rate,
                "functions": {
                    func.function_name: {
                        "start_line": func.start_line,
                        "end_line": func.end_line,
                        "hit_count": func.hit_count,
                    }
                    for func in self.functions.values()
                },
            },
        }


@dataclass
class ProjectCoverage:
    """项目覆盖率数据"""

    files: Dict[str, FileCoverage] = field(default_factory=dict)

    def add_file(self, file_path: str) -> FileCoverage:
        """添加文件"""
        if file_path not in self.files:
            self.files[file_path] = FileCoverage(file_path=file_path)
        return self.files[file_path]

    def get_file(self, file_path: str) -> Optional[FileCoverage]:
        """获取文件覆盖率"""
        return self.files.get(file_path)

    @property
    def total_lines(self) -> int:
        """总可执行行数"""
        return sum(f.total_lines for f in self.files.values())

    @property
    def covered_lines(self) -> int:
        """已覆盖行数"""
        return sum(f.covered_lines for f in self.files.values())

    @property
    def line_coverage_rate(self) -> float:
        """行覆盖率"""
        total = self.total_lines
        if total == 0:
            return 1.0
        return self.covered_lines / total

    @property
    def total_branches(self) -> int:
        """总分支数"""
        return sum(f.total_branches for f in self.files.values())

    @property
    def covered_branches(self) -> int:
        """已覆盖分支数"""
        return sum(f.covered_branches for f in self.files.values())

    @property
    def branch_coverage_rate(self) -> float:
        """分支覆盖率"""
        total = self.total_branches
        if total == 0:
            return 1.0
        return self.covered_branches / total

    @property
    def total_functions(self) -> int:
        """总函数数"""
        return sum(f.total_functions for f in self.files.values())

    @property
    def covered_functions(self) -> int:
        """已覆盖函数数"""
        return sum(f.covered_functions for f in self.files.values())

    @property
    def function_coverage_rate(self) -> float:
        """函数覆盖率"""
        total = self.total_functions
        if total == 0:
            return 1.0
        return self.covered_functions / total

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "summary": {
                "line_coverage": {
                    "total": self.total_lines,
                    "covered": self.covered_lines,
                    "rate": self.line_coverage_rate,
                },
                "branch_coverage": {
                    "total": self.total_branches,
                    "covered": self.covered_branches,
                    "rate": self.branch_coverage_rate,
                },
                "function_coverage": {
                    "total": self.total_functions,
                    "covered": self.covered_functions,
                    "rate": self.function_coverage_rate,
                },
            },
            "files": {path: file.to_dict() for path, file in self.files.items()},
        }

    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

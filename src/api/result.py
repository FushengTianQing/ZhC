#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编译结果数据类

包含编译的完整结果信息，包括成功状态、输出文件、错误、警告和统计。

作者：远
日期：2026-04-07
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class CompilationResult:
    """编译结果数据类

    包含编译的完整结果信息，包括成功状态、输出文件、错误、警告和统计。

    Attributes:
        success: 编译是否成功
        input_file: 输入文件路径
        output_files: 输出文件列表
        errors: 错误消息列表
        warnings: 警告消息列表
        stats: 编译统计信息
        elapsed_time: 编译耗时（秒）

    Example:
        >>> result = compiler.compile_single_file(Path("main.zhc"))
        >>> if result.success:
        ...     print(f"编译成功，输出文件: {result.output_files}")
        ... else:
        ...     print(f"编译失败，错误: {result.errors}")
    """

    # 基本信息
    success: bool
    input_file: Path

    # 输出信息
    output_files: List[Path] = field(default_factory=list)

    # 错误和警告
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # 统计信息
    stats: Dict[str, Any] = field(default_factory=dict)

    # 性能数据
    elapsed_time: float = 0.0

    @property
    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0

    @property
    def error_count(self) -> int:
        """错误数量"""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """警告数量"""
        return len(self.warnings)

    def summary(self) -> str:
        """生成摘要字符串

        Returns:
            编译结果的摘要字符串
        """
        status = "✅ 成功" if self.success else "❌ 失败"
        parts = [
            f"{status}: {self.input_file}",
            f"输出: {len(self.output_files)} 个文件",
            f"错误: {self.error_count}",
            f"警告: {self.warning_count}",
            f"耗时: {self.elapsed_time:.2f}s",
        ]
        return "\n".join(parts)

    def __str__(self) -> str:
        """字符串表示"""
        return self.summary()

    @classmethod
    def success_result(
        cls,
        input_file: Path,
        output_files: List[Path],
        elapsed_time: float = 0.0,
        stats: Optional[Dict[str, Any]] = None,
    ) -> "CompilationResult":
        """创建成功的编译结果

        Args:
            input_file: 输入文件路径
            output_files: 输出文件列表
            elapsed_time: 编译耗时
            stats: 编译统计信息

        Returns:
            成功的 CompilationResult 实例
        """
        return cls(
            success=True,
            input_file=input_file,
            output_files=output_files,
            elapsed_time=elapsed_time,
            stats=stats or {},
        )

    @classmethod
    def failure_result(
        cls,
        input_file: Path,
        errors: List[str],
        warnings: Optional[List[str]] = None,
        elapsed_time: float = 0.0,
    ) -> "CompilationResult":
        """创建失败的编译结果

        Args:
            input_file: 输入文件路径
            errors: 错误消息列表
            warnings: 警告消息列表
            elapsed_time: 编译耗时

        Returns:
            失败的 CompilationResult 实例
        """
        return cls(
            success=False,
            input_file=input_file,
            errors=errors,
            warnings=warnings or [],
            elapsed_time=elapsed_time,
        )

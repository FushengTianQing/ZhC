#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZhC Clang 后端 - Clang/LLVM 工具链集成

继承自 CBackend，使用 Clang 编译器。
支持直接输出 LLVM IR。

作者：远
日期：2026-04-08
"""

import subprocess
from pathlib import Path
from typing import Optional, List

from .c_backend import CBackend
from .base import (
    CompileOptions,
    CompileResult,
    OutputFormat,
    BackendCapabilities,
)


class ClangBackend(CBackend):
    """
    Clang 后端

    使用 Clang 编译器进行编译。
    支持直接输出 LLVM IR。

    特性：
    - 支持输出 LLVM IR (-emit-llvm)
    - 支持更多警告选项
    - 支持静态分析
    """

    def __init__(self, clang_path: str = "clang"):
        """
        初始化 Clang 后端

        Args:
            clang_path: Clang 路径
        """
        super().__init__(compiler=clang_path)

    @property
    def name(self) -> str:
        return "clang"

    @property
    def description(self) -> str:
        return f"Clang 后端 ({self.compiler})"

    @property
    def capabilities(self) -> BackendCapabilities:
        base = super().capabilities
        return BackendCapabilities(
            supports_jit=False,
            supports_debug=True,
            supports_optimization=True,
            supports_cross_compile=True,
            supports_lto=True,
            target_platforms=[
                "x86_64-linux",
                "x86_64-macos",
                "x86_64-windows",
                "arm-linux",
                "aarch64-linux",
                "aarch64-macos",
                "wasm32",
            ],
            output_formats=[
                OutputFormat.C,
                OutputFormat.OBJECT,
                OutputFormat.EXECUTABLE,
                OutputFormat.STATIC_LIB,
                OutputFormat.SHARED_LIB,
                OutputFormat.LLVM_IR,  # Clang 特有
                OutputFormat.LLVM_BC,  # Clang 特有
                OutputFormat.ASSEMBLY,
            ],
            required_tools=[self.compiler],
        )

    def compile(
        self,
        ir,
        output_path: Path,
        options: Optional[CompileOptions] = None,
    ) -> CompileResult:
        """
        使用 Clang 编译

        支持 emit_llvm 选项直接输出 LLVM IR。
        """
        options = options or CompileOptions()

        # Clang 特定选项
        extra_flags = [
            "-Weverything",
            "-Wno-documentation",
            "-Wno-padded",
        ]

        if options.extra_flags:
            extra_flags.extend(options.extra_flags)

        options.extra_flags = extra_flags

        # 输出 LLVM IR
        if options.emit_llvm:
            return self._emit_llvm(ir, output_path, options)

        return super().compile(ir, output_path, options)

    def _emit_llvm(
        self,
        ir,
        output_path: Path,
        options: CompileOptions,
    ) -> CompileResult:
        """
        输出 LLVM IR

        Args:
            ir: IR 程序
            output_path: 输出路径
            options: 编译选项

        Returns:
            CompileResult: 编译结果
        """
        # 先生成 C 代码
        c_code = self._generate_c_code(ir)
        c_file = output_path.with_suffix(".c")
        c_file.write_text(c_code)

        # 使用 Clang 输出 LLVM IR
        cmd = [
            self.compiler,
            f"-{options.optimization_level}",
            "-S",  # 输出汇编（LLVM IR）
            "-emit-llvm",
            "-o", str(output_path.with_suffix(".ll")),
            str(c_file),
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

            errors = []
            warnings = []

            if proc.stderr:
                for line in proc.stderr.splitlines():
                    if "error" in line.lower():
                        errors.append(line)
                    elif "warning" in line.lower():
                        warnings.append(line)

            output_file = output_path.with_suffix(".ll")

            return CompileResult(
                success=proc.returncode == 0,
                output_files=[output_file] if proc.returncode == 0 else [],
                errors=errors,
                warnings=warnings,
                exit_code=proc.returncode,
            )

        except FileNotFoundError:
            raise ToolNotFoundError(
                self.compiler,
                "请安装 Clang",
            )

    def get_supported_targets(self) -> List[str]:
        """获取 Clang 支持的目标平台"""
        return self.capabilities.target_platforms
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZhC GCC 后端 - GCC 工具链集成

继承自 CBackend，使用 GCC 编译器。

作者：远
日期：2026-04-08
"""

from pathlib import Path
from typing import Optional, List

from .c_backend import CBackend
from .base import (
    CompileOptions,
    CompileResult,
    BackendCapabilities,
)


class GCCBackend(CBackend):
    """
    GCC 后端

    使用 GCC 编译器进行编译。

    支持的目标平台：
    - x86_64-linux
    - arm-linux-gnueabihf
    - aarch64-linux-gnu
    - riscv64-linux-gnu
    """

    def __init__(self, gcc_path: str = "gcc"):
        """
        初始化 GCC 后端

        Args:
            gcc_path: GCC 路径（可以是交叉编译器，如 arm-linux-gnueabihf-gcc）
        """
        super().__init__(compiler=gcc_path)

    @property
    def name(self) -> str:
        return "gcc"

    @property
    def description(self) -> str:
        return f"GCC 后端 ({self.compiler})"

    @property
    def capabilities(self) -> BackendCapabilities:
        base = super().capabilities
        return BackendCapabilities(
            supports_jit=base.supports_jit,
            supports_debug=True,
            supports_optimization=True,
            supports_cross_compile=True,
            supports_lto=True,  # GCC 支持 LTO
            target_platforms=[
                "x86_64-linux",
                "i686-linux",
                "arm-linux-gnueabihf",
                "arm-linux-gnueabi",
                "aarch64-linux-gnu",
                "riscv64-linux-gnu",
                "riscv32-linux-gnu",
            ],
            output_formats=base.output_formats,
            required_tools=[self.compiler, "ar", "ld"],
        )

    def get_supported_targets(self) -> List[str]:
        """获取 GCC 支持的目标平台"""
        return self.capabilities.target_platforms

    def compile(
        self,
        ir,
        output_path: Path,
        options: Optional[CompileOptions] = None,
    ) -> CompileResult:
        """使用 GCC 编译"""
        options = options or CompileOptions()

        # GCC 特定选项
        extra_flags = [
            "-pedantic",
            "-Wall",
            "-Wextra",
        ]

        if options.extra_flags:
            extra_flags.extend(options.extra_flags)

        options.extra_flags = extra_flags

        return super().compile(ir, output_path, options)

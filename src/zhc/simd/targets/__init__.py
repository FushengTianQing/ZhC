# -*- coding: utf-8 -*-
"""
ZhC SIMD 目标平台模块

提供各平台的 SIMD 指令集支持。

支持的平台：
- x86: SSE/AVX/AVX-512
- ARM: NEON/SVE
- RISC-V: RVV
- WebAssembly: SIMD128

作者：远
日期：2026-04-09
"""

from .x86_simd import X86SIMDTarget
from .arm_neon import ARMNeonTarget
from .riscv_rvv import RiscVRVVTarget
from .wasm_simd import WasmSIMDTarget

__all__ = [
    "X86SIMDTarget",
    "ARMNeonTarget",
    "RiscVRVVTarget",
    "WasmSIMDTarget",
    "get_simd_target",
]


def get_simd_target(target_arch: str):
    """
    获取 SIMD 目标实例

    Args:
        target_arch: 目标架构

    Returns:
        对应的 SIMD 目标实例
    """
    arch_lower = target_arch.lower()

    if (
        "avx512" in arch_lower
        or "avx" in arch_lower
        or "sse" in arch_lower
        or "x86" in arch_lower
    ):
        return X86SIMDTarget(target_arch)
    elif (
        "neon" in arch_lower
        or "sve" in arch_lower
        or "aarch64" in arch_lower
        or "arm" in arch_lower
    ):
        return ARMNeonTarget(target_arch)
    elif "rvv" in arch_lower or "riscv" in arch_lower:
        return RiscVRVVTarget(target_arch)
    elif "wasm" in arch_lower:
        return WasmSIMDTarget(target_arch)
    else:
        # 默认使用通用实现
        return X86SIMDTarget("generic")

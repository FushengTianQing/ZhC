#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZhC 后端管理器 - 统一管理所有编译后端

提供后端注册、发现、选择功能。

使用方式：
    from zhc.backend import BackendManager

    # 获取可用后端列表
    backends = BackendManager.list_available()

    # 自动选择最佳后端
    backend = BackendManager.auto_select()

    # 获取指定后端
    llvm = BackendManager.get("llvm")

作者：远
日期：2026-04-08
"""

from typing import Dict, List, Optional

from .base import BackendBase, BackendError


class BackendManager:
    """
    后端管理器

    统一管理所有编译后端，提供：
    - 后端注册
    - 后端发现
    - 自动选择
    - 版本查询
    """

    _backends: Dict[str, BackendBase] = {}
    _initialized: bool = False

    @classmethod
    def register(cls, backend: BackendBase) -> None:
        """
        注册后端

        Args:
            backend: 后端实例
        """
        cls._backends[backend.name] = backend

    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        注销后端

        Args:
            name: 后端名称

        Returns:
            bool: 是否成功注销
        """
        if name in cls._backends:
            del cls._backends[name]
            return True
        return False

    @classmethod
    def get(cls, name: str) -> Optional[BackendBase]:
        """
        获取后端

        Args:
            name: 后端名称

        Returns:
            BackendBase: 后端实例，不存在返回 None
        """
        cls._ensure_initialized()
        return cls._backends.get(name)

    @classmethod
    def get_or_raise(cls, name: str) -> BackendBase:
        """
        获取后端，不存在则抛出异常

        Args:
            name: 后端名称

        Returns:
            BackendBase: 后端实例

        Raises:
            BackendError: 后端不存在
        """
        backend = cls.get(name)
        if backend is None:
            raise BackendError(f"后端不存在: {name}")
        return backend

    @classmethod
    def list_all(cls) -> List[str]:
        """
        列出所有已注册的后端

        Returns:
            List[str]: 后端名称列表
        """
        cls._ensure_initialized()
        return list(cls._backends.keys())

    @classmethod
    def list_available(cls) -> List[str]:
        """
        列出所有可用的后端

        Returns:
            List[str]: 可用后端名称列表
        """
        cls._ensure_initialized()
        return [
            name for name, backend in cls._backends.items() if backend.is_available()
        ]

    @classmethod
    def auto_select(
        cls,
        target: Optional[str] = None,
        prefer_llvm: bool = True,
    ) -> BackendBase:
        """
        自动选择最佳后端

        选择优先级：
        1. 如果目标是 WASM，选择 WASM 后端
        2. 如果 LLVM 可用且 prefer_llvm=True，选择 LLVM
        3. 如果 Clang 可用，选择 Clang
        4. 否则选择 GCC

        Args:
            target: 目标平台
            prefer_llvm: 是否优先选择 LLVM

        Returns:
            BackendBase: 选中的后端

        Raises:
            BackendError: 没有可用的后端
        """
        cls._ensure_initialized()

        # WASM 目标
        if target == "wasm" or (target and "wasm" in target):
            wasm = cls.get("wasm")
            if wasm and wasm.is_available():
                return wasm

        # LLVM 优先
        if prefer_llvm:
            llvm = cls.get("llvm")
            if llvm and llvm.is_available():
                return llvm

        # Clang
        clang = cls.get("clang")
        if clang and clang.is_available():
            return clang

        # GCC
        gcc = cls.get("gcc")
        if gcc and gcc.is_available():
            return gcc

        # 任何可用的后端
        available = cls.list_available()
        if available:
            return cls.get(available[0])

        raise BackendError("没有可用的编译后端")

    @classmethod
    def get_backend_info(cls) -> Dict[str, Dict]:
        """
        获取所有后端信息

        Returns:
            Dict: 后端信息字典
        """
        cls._ensure_initialized()

        info = {}
        for name, backend in cls._backends.items():
            info[name] = {
                "name": backend.name,
                "description": backend.description,
                "available": backend.is_available(),
                "version": backend.get_version(),
                "capabilities": {
                    "supports_jit": backend.capabilities.supports_jit,
                    "supports_debug": backend.capabilities.supports_debug,
                    "supports_optimization": backend.capabilities.supports_optimization,
                    "supports_cross_compile": backend.capabilities.supports_cross_compile,
                    "target_platforms": backend.capabilities.target_platforms,
                    "output_formats": [
                        f.value for f in backend.capabilities.output_formats
                    ],
                },
            }

        return info

    @classmethod
    def _ensure_initialized(cls) -> None:
        """确保后端已初始化"""
        if cls._initialized:
            return

        cls._initialize_backends()
        cls._initialized = True

    @classmethod
    def _initialize_backends(cls) -> None:
        """初始化所有内置后端"""
        # GCC 后端
        try:
            from .gcc_backend import GCCBackend

            cls.register(GCCBackend())
        except Exception:
            pass

        # Clang 后端
        try:
            from .clang_backend import ClangBackend

            cls.register(ClangBackend())
        except Exception:
            pass

        # LLVM 后端
        try:
            from .llvm_backend import LLVMBackend

            cls.register(LLVMBackend())
        except Exception:
            pass

        # LLVM 后端 - 重构版本（并行注册，用于对比测试）
        try:
            from .llvm_backend_refactored import LLVMBackend as LLVMBackendRefactored

            # 使用自定义名称避免与原版冲突
            backend = LLVMBackendRefactored()
            cls._backends["llvm-refactored"] = backend
        except Exception:
            pass

        # C 后端 - 重构版本（并行注册，用于对比测试）
        try:
            from .c_backend_refactored import CBackend as CBackendRefactored

            backend = CBackendRefactored()
            cls._backends["c-refactored"] = backend
        except Exception:
            pass

        # WASM 后端
        try:
            from .wasm_backend import WebAssemblyBackend

            cls.register(WebAssemblyBackend())
        except Exception:
            pass

    @classmethod
    def reset(cls) -> None:
        """重置管理器（用于测试）"""
        cls._backends.clear()
        cls._initialized = False


def get_backend(name: str) -> BackendBase:
    """
    获取后端的便捷函数

    Args:
        name: 后端名称

    Returns:
        BackendBase: 后端实例
    """
    return BackendManager.get_or_raise(name)


def get_available_backends() -> List[str]:
    """
    获取可用后端列表的便捷函数

    Returns:
        List[str]: 可用后端名称列表
    """
    return BackendManager.list_available()

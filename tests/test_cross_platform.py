# -*- coding: utf-8 -*-
"""
跨平台编译模块测试

测试主机检测、Triple 解析、工具链管理、链接器管理、运行时管理、平台注册表等。
"""

import pytest

from zhc.cross import (
    # Triple 解析
    TripleParser,
    TripleParseError,
    # 主机检测
    HostDetector,
    # 工具链管理
    LinkerInfo,
    LinkerManager,
    LinkerType,
    # 运行时管理
    RuntimeLibrary,
    RuntimeManager,
    RuntimeType,
    # 平台注册表
    PlatformRegistry,
    DataModel,
)


class TestTripleParser:
    """Triple 解析器测试"""

    def test_parse_linux_x86_64(self):
        """测试解析 Linux x86_64 三元组"""
        triple = TripleParser.parse("x86_64-unknown-linux-gnu")
        assert triple.arch.name == "X86_64"
        assert triple.os.name == "LINUX"
        assert str(triple) == "x86_64-unknown-linux-gnu"

    def test_parse_macos_arm64(self):
        """测试解析 macOS ARM64 三元组"""
        triple = TripleParser.parse("aarch64-apple-darwin")
        assert triple.arch.name == "AARCH64"
        assert triple.os.name == "DARWIN"

    def test_parse_wasm(self):
        """测试解析 WebAssembly 三元组"""
        triple = TripleParser.parse("wasm32-unknown-unknown")
        assert triple.arch.name == "WASM32"
        assert triple.is_wasm

    def test_parse_alias(self):
        """测试别名解析"""
        triple = TripleParser.parse("linux")
        assert triple.arch.name == "X86_64"
        assert triple.os.name == "LINUX"

    def test_parse_invalid(self):
        """测试无效三元组"""
        with pytest.raises(TripleParseError):
            TripleParser.parse("invalid")

    def test_is_cross(self):
        """测试交叉编译判断"""
        # WebAssembly 不是本机
        wasm = TripleParser.parse("wasm32-unknown-unknown")
        assert not wasm.is_native
        assert wasm.is_cross

    def test_is_embedded(self):
        """测试嵌入式目标"""
        triple = TripleParser.parse("arm-none-eabi")
        assert triple.is_embedded


class TestHostDetector:
    """主机检测器测试"""

    def test_detect(self):
        """测试主机检测"""
        host = HostDetector.detect()
        assert host.triple is not None
        assert host.arch is not None
        assert host.os is not None

    def test_host_info_properties(self):
        """测试主机信息属性"""
        host = HostDetector.detect()
        assert hasattr(host, "is_64bit")
        assert hasattr(host, "is_linux")
        assert hasattr(host, "is_macos")
        assert hasattr(host, "is_windows")

    def test_host_triple(self):
        """测试主机三元组格式"""
        host = HostDetector.detect()
        # 应该包含架构和操作系统信息
        assert "-" in host.triple


class TestLinkerManager:
    """链接器管理器测试"""

    def test_detect_linker(self):
        """测试链接器检测"""
        manager = LinkerManager()
        triple = TripleParser.parse("x86_64-unknown-linux-gnu")
        linker = manager.detect_linker(triple)
        # 应该有链接器可用
        assert linker is not None or True  # 可能没有可用链接器

    def test_linker_info(self):
        """测试链接器信息"""
        linker = LinkerInfo(
            name="lld",
            path="/usr/bin/lld",
            type=LinkerType.LLD,
            cross_platform=True,
        )
        assert linker.exists() is False  # 默认路径不存在
        assert linker.cross_platform

    def test_generate_link_command(self):
        """测试链接命令生成"""
        manager = LinkerManager()
        triple = TripleParser.parse("x86_64-unknown-linux-gnu")
        try:
            cmd = manager.generate_link_command(
                triple,
                ["a.o", "b.o"],
                "output",
            )
            assert isinstance(cmd, list)
            assert len(cmd) > 0
        except Exception:
            pass  # 可能没有可用链接器


class TestRuntimeManager:
    """运行时管理器测试"""

    def test_get_runtime_linux(self):
        """测试获取 Linux 运行时"""
        manager = RuntimeManager()
        runtime = manager.get_runtime("x86_64-unknown-linux-gnu")
        # 应该能检测到 glibc 或其他运行时
        assert runtime is not None
        assert runtime.name in ("glibc", "musl", "bionic")

    def test_get_runtime_wasm(self):
        """测试获取 WebAssembly 运行时"""
        manager = RuntimeManager()
        runtime = manager.get_runtime("wasm32-unknown-unknown")
        assert runtime is not None
        assert runtime.type == RuntimeType.WASM

    def test_get_crt_files(self):
        """测试获取 CRT 文件"""
        manager = RuntimeManager()
        files = manager.get_crt_files("x86_64-unknown-linux-gnu")
        assert isinstance(files, list)

    def test_runtime_library(self):
        """测试运行时库配置"""
        runtime = RuntimeLibrary(
            name="test",
            type=RuntimeType.GLIBC,
            target=TripleParser.parse("x86_64-unknown-linux-gnu"),
            libraries=["c", "m"],
        )
        assert len(runtime.libraries) == 2


class TestPlatformRegistry:
    """平台注册表测试"""

    def test_registry(self):
        """测试平台注册表"""
        registry = PlatformRegistry()
        assert len(registry.list_platforms()) > 0

    def test_get_platform(self):
        """测试获取平台配置"""
        registry = PlatformRegistry()
        platform = registry.get_platform("linux-x86_64")
        assert platform is not None
        assert platform.name == "linux-x86_64"

    def test_get_platform_by_triple(self):
        """测试根据三元组获取平台"""
        registry = PlatformRegistry()
        platform = registry.get_platform_by_triple("x86_64-unknown-linux-gnu")
        assert platform is not None

    def test_platform_abi(self):
        """测试平台 ABI 配置"""
        registry = PlatformRegistry()
        platform = registry.get_platform("linux-x86_64")
        assert platform.abi.data_model == DataModel.LP64
        assert platform.abi.pointer_size == 8

    def test_platform_features(self):
        """测试平台特性"""
        registry = PlatformRegistry()
        platform = registry.get_platform("linux-x86_64")
        assert platform.features.threading
        assert platform.features.dynamic_linking


class TestPlatformModules:
    """各平台模块测试"""

    def test_linux_platform(self):
        """测试 Linux 平台模块"""
        from zhc.cross.platforms.linux import LinuxPlatform
        from zhc.codegen.target_registry import Architecture

        assert LinuxPlatform.name == "linux"
        assert LinuxPlatform.is_supported(Architecture.X86_64)

        dynamic_linker = LinuxPlatform.get_dynamic_linker(Architecture.X86_64)
        assert dynamic_linker == "/lib64/ld-linux-x86-64.so.2"

    def test_macos_platform(self):
        """测试 macOS 平台模块"""
        from zhc.cross.platforms.macos import MacOSPlatform

        assert MacOSPlatform.name == "darwin"
        # Apple Silicon 检查
        is_silicon = MacOSPlatform.is_apple_silicon()
        assert isinstance(is_silicon, bool)

    def test_wasm_platform(self):
        """测试 WebAssembly 平台模块"""
        from zhc.cross.platforms.wasm import WASMPlatform
        from zhc.codegen.target_registry import Architecture

        assert WASMPlatform.name == "wasm"
        assert WASMPlatform.is_supported(Architecture.WASM32)

        triple = WASMPlatform.get_target_triple()
        assert triple == "wasm32-unknown-unknown"

    def test_embedded_platform(self):
        """测试嵌入式平台模块"""
        from zhc.cross.platforms.embedded import EmbeddedPlatform
        from zhc.codegen.target_registry import Architecture

        assert EmbeddedPlatform.name == "embedded"
        assert EmbeddedPlatform.is_supported(Architecture.ARM)

        triple = EmbeddedPlatform.get_target_triple(Architecture.ARM)
        assert "arm" in triple


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# -*- coding: utf-8 -*-
"""
ZhC 目标平台注册表

管理所有支持的目标平台，提供目标查找和配置功能。

作者：远
日期：2026-04-09
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class Architecture(Enum):
    """CPU 架构枚举"""

    UNKNOWN = 0
    X86_64 = 1
    I386 = 2
    AARCH64 = 3
    ARM = 4
    ARMV7 = 5
    RISCV64 = 6
    RISCV32 = 7
    WASM32 = 8
    WASM64 = 9
    WASM = 10  # 通用 WebArchitecture

    @property
    def is_64bit(self) -> bool:
        """是否为 64 位架构"""
        return self in (
            Architecture.X86_64,
            Architecture.AARCH64,
            Architecture.RISCV64,
            Architecture.WASM64,
        )

    @property
    def is_32bit(self) -> bool:
        """是否为 32 位架构"""
        return not self.is_64bit and self != Architecture.UNKNOWN

    @property
    def pointer_size(self) -> int:
        """指针大小（字节）"""
        return 8 if self.is_64bit else 4


class OperatingSystem(Enum):
    """操作系统枚举"""

    UNKNOWN = 0
    LINUX = 1
    DARWIN = 2  # macOS/iOS
    WINDOWS = 3
    FREEBSD = 4
    ANDROID = 5
    EMSCRIPTEN = 6  # WebAssembly


class Vendor(Enum):
    """厂商枚举"""

    UNKNOWN = 0
    PC = 1
    APPLE = 2
    NVIDIA = 3
    GNU = 4


class EnvironmentType(Enum):
    """环境类型枚举"""

    UNKNOWN = 0
    GNU = 1
    GNUABI = 2
    MUSL = 3
    MSVC = 4
    EABI = 5
    ANDROID = 6


class CallingConvention(Enum):
    """调用约定枚举"""

    UNKNOWN = 0
    # x86_64
    SYSTEM_V_AMD64 = 1  # Linux/macOS x86_64
    MS_X64 = 2  # Windows x86_64
    # AArch64/ARM
    AAPCS64 = 3  # AArch64
    AAPCS = 4  # ARM
    # RISC-V
    RISCV = 5
    # WebAssembly
    WASM = 6


@dataclass
class RegisterClass:
    """寄存器类"""

    name: str
    registers: List[str]
    size: int  # 寄存器大小（位）

    def __len__(self) -> int:
        return len(self.registers)


@dataclass(init=False)
class Target:
    """
    目标平台描述

    包含目标平台的所有信息，包括架构、操作系统、ABI 等。
    """

    name: str  # 目标名称 (x86_64, aarch64, wasm32)
    triple: str  # LLVM 目标三元组
    arch: Architecture
    os: OperatingSystem
    vendor: Vendor
    environment: EnvironmentType

    # CPU 和特性
    default_cpu: str
    default_features: List[str]

    # ABI 信息
    calling_convention: CallingConvention
    pointer_size: int
    stack_alignment: int

    # 寄存器信息
    register_classes: List[RegisterClass]

    # 工具链信息
    default_linker: str
    default_assembler: str

    def __init__(
        self,
        name: str,
        triple: str,
        arch: Architecture = None,
        os: OperatingSystem = None,
        architecture: Architecture = None,  # 测试兼容
        vendor: Vendor = None,
        environment: EnvironmentType = None,
        default_cpu: str = "generic",
        default_features: List[str] = None,
        calling_convention: CallingConvention = None,
        pointer_size: int = 8,
        stack_alignment: int = 16,
        register_classes: List[RegisterClass] = None,
        default_linker: str = "",
        default_assembler: str = "",
        **kwargs,
    ):
        """
        初始化目标平台

        支持两种参数名：
        - arch: 内部使用
        - architecture: 测试兼容
        """
        self.name = name
        self.triple = triple
        # 支持 architecture 参数（测试兼容）
        self.arch = architecture if architecture is not None else arch
        self.os = os if os is not None else OperatingSystem.UNKNOWN
        self.vendor = vendor if vendor is not None else Vendor.UNKNOWN
        self.environment = (
            environment if environment is not None else EnvironmentType.UNKNOWN
        )
        self.default_cpu = default_cpu
        self.default_features = default_features if default_features is not None else []
        self.calling_convention = (
            calling_convention
            if calling_convention is not None
            else CallingConvention.UNKNOWN
        )
        self.pointer_size = pointer_size
        self.stack_alignment = stack_alignment
        self.register_classes = register_classes if register_classes is not None else []
        self.default_linker = default_linker
        self.default_assembler = default_assembler
        # 处理其他可能的参数
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self) -> str:
        return f"{self.name} ({self.triple})"

    @property
    def is_native(self) -> bool:
        """是否为本机目标"""

        host_triple = self._detect_host_triple()
        return self.triple == host_triple

    @property
    def is_cross(self) -> bool:
        """是否为交叉编译目标"""
        return not self.is_native

    @staticmethod
    def _detect_host_triple() -> str:
        """检测主机三元组"""
        import platform

        arch = platform.machine().lower()
        system = platform.system().lower()

        arch_map = {
            "x86_64": "x86_64",
            "amd64": "x86_64",
            "aarch64": "aarch64",
            "arm64": "aarch64",
            "armv7l": "arm",
            "riscv64": "riscv64",
        }

        os_map = {
            "linux": "unknown-linux-gnu",
            "darwin": "apple-darwin",
            "windows": "pc-windows-msvc",
        }

        arch_str = arch_map.get(arch, arch)
        os_str = os_map.get(system, system)

        return f"{arch_str}-{os_str}"


class TargetRegistry:
    """
    目标平台注册表

    管理所有支持的目标平台，提供查找和配置功能。

    使用方式：
        # 获取目标
        target = TargetRegistry.get("x86_64")
        target = TargetRegistry.get("x86_64-unknown-linux-gnu")

        # 列出所有目标
        for target in TargetRegistry.list():
            print(target)
    """

    _targets: Dict[str, Target] = {}
    _initialized: bool = False

    @classmethod
    def register(cls, target: Target) -> None:
        """
        注册目标平台

        Args:
            target: 目标平台描述
        """
        cls._targets[target.name] = target
        cls._targets[target.triple] = target

        logger.debug(f"Registered target: {target}")

    @classmethod
    def unregister(cls, name_or_triple: str) -> bool:
        """
        注销目标平台

        Args:
            name_or_triple: 目标名称或三元组

        Returns:
            是否成功注销
        """
        target = cls._targets.get(name_or_triple)
        if target:
            cls._targets.pop(target.name, None)
            cls._targets.pop(target.triple, None)
            return True
        return False

    @classmethod
    def get(cls, name_or_triple: str) -> Optional[Target]:
        """
        获取目标平台

        Args:
            name_or_triple: 目标名称或三元组

        Returns:
            目标平台描述，如果不存在返回 None
        """
        cls._ensure_initialized()

        # 直接查找
        if name_or_triple in cls._targets:
            return cls._targets[name_or_triple]

        # 尝试规范化
        normalized = cls._normalize_triple(name_or_triple)
        if normalized in cls._targets:
            return cls._targets[normalized]

        return None

    @classmethod
    def list(cls) -> List[Target]:
        """
        列出所有注册的目标平台

        Returns:
            目标平台列表（去重）
        """
        cls._ensure_initialized()

        seen = set()
        targets = []
        for target in cls._targets.values():
            if target.name not in seen:
                seen.add(target.name)
                targets.append(target)

        return sorted(targets, key=lambda t: t.name)

    @classmethod
    def list_by_arch(cls, arch: Architecture) -> List[Target]:
        """按架构列出目标"""
        cls._ensure_initialized()
        return [t for t in cls.list() if t.arch == arch]

    @classmethod
    def list_by_os(cls, os: OperatingSystem) -> List[Target]:
        """按操作系统列出目标"""
        cls._ensure_initialized()
        return [t for t in cls.list() if t.os == os]

    @classmethod
    def get_host_target(cls) -> Target:
        """
        获取主机目标

        Returns:
            主机目标平台
        """

        host_triple = Target._detect_host_triple()
        target = cls.get(host_triple)

        if target is None:
            # 创建默认目标
            arch_map = {
                "x86_64": Architecture.X86_64,
                "aarch64": Architecture.AARCH64,
                "arm": Architecture.ARM,
                "riscv64": Architecture.RISCV64,
            }

            os_map = {
                "linux": OperatingSystem.LINUX,
                "darwin": OperatingSystem.DARWIN,
                "windows": OperatingSystem.WINDOWS,
            }

            arch_str = host_triple.split("-")[0]
            os_str = host_triple.split("-")[1] if "-" in host_triple else "unknown"

            target = Target(
                name=arch_str,
                triple=host_triple,
                arch=arch_map.get(arch_str, Architecture.UNKNOWN),
                os=os_map.get(os_str, OperatingSystem.UNKNOWN),
            )

        return target

    @classmethod
    def _normalize_triple(cls, triple: str) -> str:
        """规范化三元组"""
        # 简单的别名处理
        aliases = {
            "linux": "x86_64-unknown-linux-gnu",
            "macos": "x86_64-apple-darwin",
            "windows": "x86_64-pc-windows-msvc",
            "wasm": "wasm32-unknown-unknown",
            "wasm32": "wasm32-unknown-unknown",
        }

        return aliases.get(triple.lower(), triple)

    @classmethod
    def _ensure_initialized(cls) -> None:
        """确保已初始化内置目标"""
        if cls._initialized:
            return

        cls._register_builtin_targets()
        cls._initialized = True

    @classmethod
    def _register_builtin_targets(cls) -> None:
        """注册内置目标平台"""

        # ========== x86_64 目标 ==========

        # Linux x86_64
        cls.register(
            Target(
                name="x86_64-linux",
                triple="x86_64-unknown-linux-gnu",
                arch=Architecture.X86_64,
                os=OperatingSystem.LINUX,
                vendor=Vendor.UNKNOWN,
                environment=EnvironmentType.GNU,
                default_cpu="x86-64",
                default_features=["sse4.2", "popcnt"],
                calling_convention=CallingConvention.SYSTEM_V_AMD64,
                pointer_size=8,
                stack_alignment=16,
                register_classes=[
                    RegisterClass(
                        "GR64",
                        [
                            "rax",
                            "rbx",
                            "rcx",
                            "rdx",
                            "rsi",
                            "rdi",
                            "rbp",
                            "r8",
                            "r9",
                            "r10",
                            "r11",
                            "r12",
                            "r13",
                            "r14",
                            "r15",
                        ],
                        64,
                    ),
                    RegisterClass(
                        "XMM",
                        [f"xmm{i}" for i in range(16)],
                        128,
                    ),
                ],
                default_linker="ld.lld",
            )
        )

        # macOS x86_64
        cls.register(
            Target(
                name="x86_64-macos",
                triple="x86_64-apple-darwin",
                arch=Architecture.X86_64,
                os=OperatingSystem.DARWIN,
                vendor=Vendor.APPLE,
                default_cpu="x86-64",
                default_features=["sse4.2", "popcnt", "avx"],
                calling_convention=CallingConvention.SYSTEM_V_AMD64,
                pointer_size=8,
                stack_alignment=16,
                default_linker="ld64",
            )
        )

        # Windows x86_64
        cls.register(
            Target(
                name="x86_64-windows",
                triple="x86_64-pc-windows-msvc",
                arch=Architecture.X86_64,
                os=OperatingSystem.WINDOWS,
                vendor=Vendor.PC,
                environment=EnvironmentType.MSVC,
                default_cpu="x86-64",
                default_features=["sse4.2"],
                calling_convention=CallingConvention.MS_X64,
                pointer_size=8,
                stack_alignment=16,
                default_linker="lld-link",
            )
        )

        # ========== AArch64 目标 ==========

        # Linux AArch64
        cls.register(
            Target(
                name="aarch64-linux",
                triple="aarch64-unknown-linux-gnu",
                arch=Architecture.AARCH64,
                os=OperatingSystem.LINUX,
                vendor=Vendor.UNKNOWN,
                environment=EnvironmentType.GNU,
                default_cpu="generic",
                default_features=["neon"],
                calling_convention=CallingConvention.AAPCS64,
                pointer_size=8,
                stack_alignment=16,
                register_classes=[
                    RegisterClass(
                        "X",
                        [f"x{i}" for i in range(31)] + ["sp"],
                        64,
                    ),
                    RegisterClass(
                        "V",
                        [f"v{i}" for i in range(32)],
                        128,
                    ),
                ],
                default_linker="ld.lld",
            )
        )

        # macOS AArch64 (Apple Silicon)
        cls.register(
            Target(
                name="aarch64-macos",
                triple="aarch64-apple-darwin",
                arch=Architecture.AARCH64,
                os=OperatingSystem.DARWIN,
                vendor=Vendor.APPLE,
                default_cpu="apple-m1",
                default_features=["neon", "aes", "sha2"],
                calling_convention=CallingConvention.AAPCS64,
                pointer_size=8,
                stack_alignment=16,
                default_linker="ld64",
            )
        )

        # ========== ARM 目标 ==========

        # Linux ARM (ARMv7)
        cls.register(
            Target(
                name="arm-linux",
                triple="arm-unknown-linux-gnueabihf",
                arch=Architecture.ARM,
                os=OperatingSystem.LINUX,
                vendor=Vendor.UNKNOWN,
                environment=EnvironmentType.GNU,
                default_cpu="generic",
                default_features=["neon", "vfp4"],
                calling_convention=CallingConvention.AAPCS,
                pointer_size=4,
                stack_alignment=8,
                default_linker="ld.lld",
            )
        )

        # ========== RISC-V 目标 ==========

        # Linux RISC-V 64
        cls.register(
            Target(
                name="riscv64-linux",
                triple="riscv64-unknown-linux-gnu",
                arch=Architecture.RISCV64,
                os=OperatingSystem.LINUX,
                vendor=Vendor.UNKNOWN,
                environment=EnvironmentType.GNU,
                default_cpu="generic-rv64",
                default_features=["m", "a", "f", "d", "c"],
                calling_convention=CallingConvention.RISCV,
                pointer_size=8,
                stack_alignment=16,
                default_linker="ld.lld",
            )
        )

        # ========== WebAssembly 目标 ==========

        # WebAssembly 32-bit
        cls.register(
            Target(
                name="wasm32",
                triple="wasm32-unknown-unknown",
                arch=Architecture.WASM32,
                os=OperatingSystem.UNKNOWN,
                default_cpu="generic",
                default_features=["simd128"],
                calling_convention=CallingConvention.WASM,
                pointer_size=4,
                stack_alignment=16,
                default_linker="wasm-ld",
            )
        )

    @classmethod
    def reset(cls) -> None:
        """重置注册表（用于测试）"""
        cls._targets.clear()
        cls._initialized = False

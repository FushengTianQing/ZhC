# -*- coding: utf-8 -*-
"""
ZhC 嵌入式平台配置

提供嵌入式平台的特定配置，包括 ARM、RISC-V、AVR 等。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from zhc.codegen.target_registry import (
    Architecture,
    OperatingSystem,
)


@dataclass
class EmbeddedABI:
    """嵌入式 ABI 配置"""

    # 架构特定配置
    arch: Architecture

    # 数据模型
    pointer_size: int = 4
    int_size: int = 4
    float_size: int = 4

    # 对齐
    alignment: int = 4
    stack_alignment: int = 8

    # 特性
    thumb_mode: bool = False
    hard_float: bool = False
    soft_float: bool = True

    # 调用约定
    calling_convention: str = "default"


@dataclass
class EmbeddedPlatform:
    """
    嵌入式平台配置

    提供嵌入式平台的完整配置。
    """

    name = "embedded"
    os_type = OperatingSystem.UNKNOWN

    # 支持的架构
    supported_archs = [
        Architecture.ARM,
        Architecture.ARMV7,
        Architecture.AARCH64,
        Architecture.RISCV32,
        Architecture.RISCV64,
        Architecture.X86_64,  # x86 嵌入式（如 x86 实时系统）
        Architecture.I386,  # 32位 x86
    ]

    # 常见嵌入式配置
    embedded_configs: Dict[Architecture, Dict] = field(
        default_factory=lambda: {
            Architecture.ARM: {
                "name": "arm-embedded",
                "abi": "eabi",
                "features": ["thumb", "soft_float"],
                "linker_script": True,
                "bare_metal": True,
            },
            Architecture.ARMV7: {
                "name": "armv7-embedded",
                "abi": "eabihf",
                "features": ["thumb", "hard_float", "neon"],
                "linker_script": True,
                "bare_metal": True,
            },
            Architecture.AARCH64: {
                "name": "aarch64-embedded",
                "abi": "aapcs",
                "features": ["neon"],
                "linker_script": True,
                "bare_metal": True,
            },
            Architecture.RISCV32: {
                "name": "riscv32-embedded",
                "abi": "ilp32",
                "features": ["m", "a"],
                "linker_script": True,
                "bare_metal": True,
            },
            Architecture.RISCV64: {
                "name": "riscv64-embedded",
                "abi": "lp64",
                "features": ["m", "a"],
                "linker_script": True,
                "bare_metal": True,
            },
        }
    )

    @classmethod
    def is_supported(cls, arch: Architecture) -> bool:
        """检查架构是否支持"""
        return arch in cls.supported_archs

    @classmethod
    def get_config(cls, arch: Architecture) -> Optional[Dict]:
        """获取架构配置"""
        return cls.embedded_configs.get(arch)

    @classmethod
    def get_target_triple(
        cls, arch: Architecture, vendor: str = "none", env: str = "eabi"
    ) -> str:
        """获取目标三元组"""
        arch_str = arch.name.lower()

        # 特殊处理
        if arch == Architecture.ARMV7:
            arch_str = "armv7"

        return f"{arch_str}-{vendor}-{env}"

    @classmethod
    def get_compiler_flags(
        cls, arch: Architecture, options: Optional[Dict] = None
    ) -> List[str]:
        """获取编译器标志"""
        config = cls.get_config(arch)
        if not config:
            return []

        flags = [
            "-ffreestanding",
            "-fno-builtin",
            "-fno-stack-protector",
            "-nostdlib",
        ]

        # 架构特定标志
        if arch in (Architecture.ARM, Architecture.ARMV7):
            flags.append("-mthumb")

            if arch == Architecture.ARMV7:
                flags.extend(
                    ["-mcpu=cortex-m4", "-mfloat-abi=hard", "-mfpu=fpv4-sp-d16"]
                )
            else:
                flags.extend(["-mcpu=cortex-m3", "-mfloat-abi=soft"])

        elif arch == Architecture.RISCV32:
            flags.extend(["-march=rv32imac", "-mabi=ilp32"])

        elif arch == Architecture.RISCV64:
            flags.extend(["-march=rv64imac", "-mabi=lp64"])

        elif arch == Architecture.AARCH64:
            flags.extend(["-mcpu=cortex-a53"])

        # 自定义选项
        if options:
            if options.get("thumb"):
                flags.append("-mthumb")
            if options.get("hard_float"):
                flags.append("-mfloat-abi=hard")
            if options.get("soft_float"):
                flags.append("-mfloat-abi=soft")

        return flags

    @classmethod
    def get_linker_flags(
        cls, arch: Architecture, linker_script: Optional[str] = None
    ) -> List[str]:
        """获取链接器标志"""
        flags = [
            "-nostdlib",
            "-nostartfiles",
            "--gc-sections",
        ]

        # 链接器脚本
        if linker_script:
            flags.extend(["-T", linker_script])

        # 架构特定标志
        if arch in (Architecture.ARM, Architecture.ARMV7):
            flags.append("-mthumbelf")

        return flags

    @classmethod
    def get_crt_files(cls, arch: Architecture) -> List[str]:
        """获取 CRT 文件"""
        return [
            "crt0.o",
            "crti.o",
            "crtn.o",
        ]

    @classmethod
    def get_system_libs(cls, arch: Architecture) -> List[str]:
        """获取系统库"""
        libs = ["c"]

        if arch in (Architecture.ARM, Architecture.ARMV7):
            libs.extend(["gcc", "nosys"])

        return libs

    @classmethod
    def get_linker_script(cls, arch: Architecture) -> Optional[str]:
        """获取默认链接器脚本"""
        scripts = {
            Architecture.ARM: "arm-none-eabi.ld",
            Architecture.ARMV7: "armv7em-none-eabi.ld",
            Architecture.RISCV32: "riscv32-unknown-elf.ld",
            Architecture.RISCV64: "riscv64-unknown-elf.ld",
        }
        return scripts.get(arch)

    @classmethod
    def get_memory_config(cls, arch: Architecture) -> Dict[str, int]:
        """获取内存配置"""
        # 默认内存配置
        configs = {
            Architecture.ARM: {
                "flash_size": 0x80000,  # 512KB
                "ram_size": 0x20000,  # 128KB
                "flash_start": 0x08000000,
                "ram_start": 0x20000000,
            },
            Architecture.ARMV7: {
                "flash_size": 0x100000,  # 1MB
                "ram_size": 0x40000,  # 256KB
                "flash_start": 0x08000000,
                "ram_start": 0x20000000,
            },
            Architecture.RISCV32: {
                "flash_size": 0x80000,  # 512KB
                "ram_size": 0x20000,  # 128KB
                "flash_start": 0x20000000,
                "ram_start": 0x80000000,
            },
        }
        return configs.get(arch, {})

    @classmethod
    def get_board_config(cls, arch: Architecture, board: str = "generic") -> Dict:
        """获取开发板配置"""
        # 常见开发板配置
        boards = {
            "stm32f4": {
                "arch": Architecture.ARMV7,
                "cpu": "cortex-m4",
                "fpu": "fpv4-sp-d16",
                "flash": 0x100000,
                "ram": 0x20000,
            },
            "stm32l4": {
                "arch": Architecture.ARMV7,
                "cpu": "cortex-m4",
                "fpu": "fpv4-sp-d16",
                "flash": 0x80000,
                "ram": 0x40000,
            },
            "nrf52840": {
                "arch": Architecture.ARM,
                "cpu": "cortex-m4",
                "fpu": "fpv4-sp-d16",
                "flash": 0x100000,
                "ram": 0x40000,
            },
            "esp32": {
                "arch": Architecture.ARM,
                "cpu": "esp32",
                "flash": 0x400000,
                "ram": 0x80000,
            },
        }

        return boards.get(
            board,
            {
                "arch": arch,
                "cpu": "generic",
                "flash": 0x80000,
                "ram": 0x20000,
            },
        )

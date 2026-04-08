#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
寄存器分配器基类和统一接口

提供抽象基类和统一 API，供所有后端（C/LLVM/WASM）使用。

作者：阿福
日期：2026-04-08
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

# 类型检查时导入，运行时延迟导入
if TYPE_CHECKING:
    from zhc.ir.register_allocator import AllocationResult


# 延迟导入，避免循环依赖
def _get_allocator_classes():
    """延迟导入分配器类"""
    from zhc.ir.register_allocator import (
        Register,
        RegisterKind,
        VirtualRegister,
        LiveInterval,
        AllocationResult,
        TargetArchitecture,
        LinearScanRegisterAllocator,
        GraphColorRegisterAllocator,
    )

    return (
        Register,
        RegisterKind,
        VirtualRegister,
        LiveInterval,
        AllocationResult,
        TargetArchitecture,
        LinearScanRegisterAllocator,
        GraphColorRegisterAllocator,
    )


class AllocationStrategy(Enum):
    """分配策略"""

    LINEAR_SCAN = "linear_scan"  # 线性扫描（快速，适合 JIT）
    GRAPH_COLOR = "graph_color"  # 图着色（更优，但慢）
    SIMPLE = "simple"  # 简单分配（溢出所有）
    NONE = "none"  # 不分配（依赖目标后端）


@dataclass
class Instruction:
    """中间表示指令（用于寄存器分配）"""

    id: int  # 指令 ID
    opcode: str  # 操作码
    defs: List[int] = field(default_factory=list)  # 定义列表（虚拟寄存器 ID）
    uses: List[int] = field(default_factory=list)  # 使用列表
    live_out: Set[int] = field(default_factory=set)  # 活跃变量


@dataclass
class BackendCapabilities:
    """后端能力描述"""

    name: str  # 后端名称（如 "x86_64", "arm64", "wasm"）
    max_int_regs: int = 16  # 最大整数寄存器数
    max_float_regs: int = 16  # 最大浮点寄存器数
    has_callee_saved: bool = True  # 是否有 callee-saved 寄存器
    has_vector_regs: bool = False  # 是否有向量寄存器
    stack_alignment: int = 16  # 栈对齐要求


class RegisterAllocator(ABC):
    """
    寄存器分配器抽象基类

    所有后端寄存器分配器必须实现此接口。
    """

    @abstractmethod
    def set_backend_capabilities(self, caps: BackendCapabilities):
        """设置后端能力"""
        pass

    @abstractmethod
    def allocate(self, instructions: List[Instruction]) -> "AllocationResult":
        """
        执行寄存器分配

        Args:
            instructions: 指令列表

        Returns:
            分配结果
        """
        pass

    @abstractmethod
    def get_register_name(self, virtual_reg_id: int) -> str:
        """
        获取虚拟寄存器对应的物理寄存器名称

        Args:
            virtual_reg_id: 虚拟寄存器 ID

        Returns:
            物理寄存器名称（如 "eax", "r8"）
        """
        pass


class UnifiedRegisterAllocator(RegisterAllocator):
    """
    统一寄存器分配器

    支持多种分配策略，可配置到不同后端。
    """

    def __init__(
        self,
        strategy: AllocationStrategy = AllocationStrategy.LINEAR_SCAN,
        backend_caps: Optional[BackendCapabilities] = None,
    ):
        """
        初始化统一寄存器分配器

        Args:
            strategy: 分配策略
            backend_caps: 后端能力描述
        """
        self.strategy = strategy
        self.backend_caps = backend_caps or BackendCapabilities(name="generic")

        # 延迟导入
        (_, _, _, _, _, _, LinearScanRegisterAllocator, GraphColorRegisterAllocator) = (
            _get_allocator_classes()
        )

        # 选择底层实现
        if strategy == AllocationStrategy.LINEAR_SCAN:
            num_regs = self.backend_caps.max_int_regs
            self._allocator = LinearScanRegisterAllocator(num_regs=num_regs)
        elif strategy == AllocationStrategy.GRAPH_COLOR:
            num_regs = self.backend_caps.max_int_regs
            self._allocator = GraphColorRegisterAllocator(num_regs=num_regs)
        else:
            self._allocator = None

        # 分配映射
        self._allocation_map: Dict[int, str] = {}
        self._spill_map: Dict[int, int] = {}

    def set_backend_capabilities(self, caps: BackendCapabilities):
        """设置后端能力"""
        self.backend_caps = caps
        # 延迟导入
        (_, _, _, _, _, _, LinearScanRegisterAllocator, GraphColorRegisterAllocator) = (
            _get_allocator_classes()
        )
        # 重新创建分配器
        if self.strategy == AllocationStrategy.LINEAR_SCAN:
            self._allocator = LinearScanRegisterAllocator(num_regs=caps.max_int_regs)
        elif self.strategy == AllocationStrategy.GRAPH_COLOR:
            self._allocator = GraphColorRegisterAllocator(num_regs=caps.max_int_regs)

    def allocate(self, instructions: List[Instruction]) -> "AllocationResult":
        """执行寄存器分配"""
        if self._allocator is None:
            # SIMPLE 或 NONE 策略：返回空结果
            (_, _, _, _, AllocationResult, _, _, _) = _get_allocator_classes()
            return AllocationResult(success=True)

        # 转换为内部格式
        ir_instructions = self._to_internal_format(instructions)

        # 执行分配
        result = self._allocator.allocate(ir_instructions)

        # 转换为映射
        self._allocation_map.clear()
        self._spill_map.clear()

        for vreg_id, reg in result.allocations.items():
            self._allocation_map[vreg_id] = reg.name

        for vreg_id in result.spills:
            self._spill_map[vreg_id] = len(self._spill_map)

        return result

    def _to_internal_format(self, instructions: List[Instruction]) -> List[dict]:
        """转换为内部指令格式"""
        result = []
        for instr in instructions:
            result.append(
                {"def": instr.defs, "use": instr.uses, "live_out": instr.live_out}
            )
        return result

    def get_register_name(self, virtual_reg_id: int) -> str:
        """获取物理寄存器名称"""
        return self._allocation_map.get(virtual_reg_id, "")

    def is_spilled(self, virtual_reg_id: int) -> bool:
        """检查虚拟寄存器是否被溢出"""
        return virtual_reg_id in self._spill_map

    def get_spill_slot(self, virtual_reg_id: int) -> Optional[int]:
        """获取溢出槽编号"""
        return self._spill_map.get(virtual_reg_id)

    def generate_spill_code(self, vreg_id: int, position: int, is_load: bool) -> str:
        """
        生成溢出代码

        Args:
            vreg_id: 虚拟寄存器 ID
            position: 指令位置
            is_load: True=加载, False=存储

        Returns:
            汇编代码片段
        """
        if not self.is_spilled(vreg_id):
            return ""

        slot = self.get_spill_slot(vreg_id)
        reg_name = self._allocation_map.get(vreg_id, "tmp")

        # 根据后端生成代码
        if self.backend_caps.name in ("x86_64", "amd64"):
            spill_addr = f"[rbp-{slot * 8}]"
        elif self.backend_caps.name == "arm64":
            spill_addr = f"[sp, #{slot * 8}]"
        elif self.backend_caps.name == "wasm":
            # WASM 使用本地变量，无需溢出
            return ""
        else:
            spill_addr = f"[sp+{slot * 8}]"

        if is_load:
            return f"mov {reg_name}, {spill_addr}"
        else:
            return f"mov {spill_addr}, {reg_name}"


# ==================== 后端特定分配器 ====================


class X86_64RegisterAllocator(UnifiedRegisterAllocator):
    """x86-64 专用寄存器分配器"""

    def __init__(self, strategy: AllocationStrategy = AllocationStrategy.LINEAR_SCAN):
        caps = BackendCapabilities(
            name="x86_64",
            max_int_regs=16,  # rax, rcx, rdx, rbx, rsp, rbp, rsi, rdi, r8-r15
            max_float_regs=16,  # xmm0-xmm15
            has_callee_saved=True,
            stack_alignment=16,
        )
        super().__init__(strategy, caps)


class Arm64RegisterAllocator(UnifiedRegisterAllocator):
    """ARM64 专用寄存器分配器"""

    def __init__(self, strategy: AllocationStrategy = AllocationStrategy.LINEAR_SCAN):
        caps = BackendCapabilities(
            name="arm64",
            max_int_regs=32,  # x0-x31
            max_float_regs=32,  # v0-v31
            has_callee_saved=True,
            stack_alignment=16,
        )
        super().__init__(strategy, caps)


class WASMRegisterAllocator(UnifiedRegisterAllocator):
    """WebAssembly 专用寄存器分配器

    WASM 使用无寄存器的虚拟机模型，
    但可以使用局部变量（local）作为"寄存器"。
    """

    def __init__(self, strategy: AllocationStrategy = AllocationStrategy.NONE):
        caps = BackendCapabilities(
            name="wasm",
            max_int_regs=0,  # WASM 不使用寄存器
            max_float_regs=0,
            has_callee_saved=False,
            stack_alignment=16,
        )
        super().__init__(strategy, caps)


class LLVMRegisterAllocator(UnifiedRegisterAllocator):
    """LLVM 后端寄存器分配器

    LLVM 本身有强大的寄存器分配器，
    这里提供接口用于与 LLVM 交互。
    """

    def __init__(self, strategy: AllocationStrategy = AllocationStrategy.NONE):
        # LLVM 会处理寄存器分配
        caps = BackendCapabilities(
            name="llvm",
            max_int_regs=32,
            max_float_regs=32,
            has_callee_saved=True,
            has_vector_regs=True,
            stack_alignment=16,
        )
        super().__init__(strategy, caps)


# ==================== 工厂函数 ====================


def create_allocator(
    backend: str, strategy: AllocationStrategy = AllocationStrategy.LINEAR_SCAN
) -> RegisterAllocator:
    """
    创建后端特定的寄存器分配器

    Args:
        backend: 后端名称 ("x86_64", "arm64", "wasm", "llvm")
        strategy: 分配策略

    Returns:
        寄存器分配器实例
    """
    allocators = {
        "x86_64": X86_64RegisterAllocator,
        "amd64": X86_64RegisterAllocator,
        "arm64": Arm64RegisterAllocator,
        "aarch64": Arm64RegisterAllocator,
        "wasm": WASMRegisterAllocator,
        "webassembly": WASMRegisterAllocator,
        "llvm": LLVMRegisterAllocator,
    }

    allocator_class = allocators.get(backend.lower())
    if allocator_class is None:
        raise ValueError(f"Unknown backend: {backend}")

    return allocator_class(strategy)


def register_for_all_backends(
    instructions: List[Instruction], backend: str = "x86_64"
) -> Tuple[Dict[int, str], Dict[int, int]]:
    """
    为所有后端执行寄存器分配的便捷函数

    Args:
        instructions: 指令列表
        backend: 目标后端

    Returns:
        (寄存器映射, 溢出槽映射)
    """
    allocator = create_allocator(backend)
    allocator.allocate(instructions)

    allocation_map = {}
    spill_map = {}

    for vreg_id in range(max(instr.id for instr in instructions) + 1):
        if allocator.is_spilled(vreg_id):
            spill_map[vreg_id] = allocator.get_spill_slot(vreg_id)
        else:
            reg_name = allocator.get_register_name(vreg_id)
            if reg_name:
                allocation_map[vreg_id] = reg_name

    return allocation_map, spill_map


# 测试代码
if __name__ == "__main__":
    print("=== 统一寄存器分配器测试 ===\n")

    # 创建 x86-64 分配器
    allocator = create_allocator("x86_64")
    print(f"创建分配器: {allocator.backend_caps.name}")
    print(f"整数寄存器数: {allocator.backend_caps.max_int_regs}")

    # 创建指令
    instructions = [
        Instruction(id=0, opcode="add", defs=[0], uses=[], live_out={0, 1}),
        Instruction(id=1, opcode="sub", defs=[1], uses=[0], live_out={0, 1}),
        Instruction(id=2, opcode="mul", defs=[2], uses=[1], live_out={0, 1, 2}),
        Instruction(id=3, opcode="call", defs=[], uses=[0, 1, 2], live_out=set()),
    ]

    # 执行分配
    result = allocator.allocate(instructions)
    print("\n分配结果:")
    print(f"  成功: {result.success}")
    print(f"  分配数: {len(result.allocations)}")
    print(f"  溢出数: {len(result.spills)}")

    # 打印分配映射
    print("\n寄存器映射:")
    for vreg_id in range(3):
        if allocator.is_spilled(vreg_id):
            print(f"  v{vreg_id} -> [spill slot {allocator.get_spill_slot(vreg_id)}]")
        else:
            reg_name = allocator.get_register_name(vreg_id)
            print(f"  v{vreg_id} -> {reg_name}")

    # 测试 WASM 后端
    print("\n--- WASM 后端 ---")
    wasm_allocator = create_allocator("wasm")
    print(f"创建分配器: {wasm_allocator.backend_caps.name}")
    print(f"整数寄存器数: {wasm_allocator.backend_caps.max_int_regs}")

    print("\n=== 测试完成 ===")

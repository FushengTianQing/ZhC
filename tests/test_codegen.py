# -*- coding: utf-8 -*-
"""
ZhC 代码生成模块测试

测试内容：
- 目标 Lowering (target_lower.py)
- 指令选择器 (instruction_selector.py)
- 寄存器分配器 (register_allocator.py)
- 栈帧布局 (frame_lower.py)
- 重定位 (relocator.py)
- 符号表 (symbol_table.py)

作者：远
日期：2026-04-09
"""


# ============================================================================
# Target Lowering 测试
# ============================================================================


class TestTargetLowering:
    """Target Lowering 测试"""

    def test_target_lowering_import(self):
        """测试 TargetLowering 模块导入"""
        from zhc.codegen.target_lower import (
            TargetLowering,
            X86_64TargetLowering,
            AArch64TargetLowering,
            WasmTargetLowering,
        )

        assert TargetLowering is not None
        assert X86_64TargetLowering is not None
        assert AArch64TargetLowering is not None
        assert WasmTargetLowering is not None

    def test_lowered_function_creation(self):
        """测试 LoweredFunction 创建"""
        from zhc.codegen.target_lower import LoweredFunction

        func = LoweredFunction(
            name="test_func",
            return_type="i32",
            params=[("i32", "x"), ("i64", "y")],
        )

        assert func.name == "test_func"
        assert func.return_type == "i32"
        assert len(func.params) == 2
        assert func.params[0] == ("i32", "x")
        assert str(func) == "i32 test_func(i32 x, i64 y)"

    def test_lowered_module_creation(self):
        """测试 LoweredModule 创建"""
        from zhc.codegen.target_lower import LoweredModule, LoweredFunction

        module = LoweredModule(name="test_module")
        func = LoweredFunction(name="func1", return_type="void")
        module.add_function(func)

        assert module.name == "test_module"
        assert module.get_function("func1") is func
        assert module.get_function("nonexistent") is None

    def test_x86_64_target_lowering(self):
        """测试 x86_64 目标 Lowering"""
        from zhc.codegen.target_lower import X86_64TargetLowering
        from zhc.codegen.target_registry import Target, Architecture, OperatingSystem

        target = Target(
            name="x86_64",
            architecture=Architecture.X86_64,
            os=OperatingSystem.LINUX,
            triple="x86_64-unknown-linux-gnu",
        )

        lowering = X86_64TargetLowering(target)
        assert lowering.target is target

    def test_aarch64_target_lowering(self):
        """测试 AArch64 目标 Lowering"""
        from zhc.codegen.target_lower import AArch64TargetLowering
        from zhc.codegen.target_registry import Target, Architecture, OperatingSystem

        target = Target(
            name="aarch64",
            architecture=Architecture.AARCH64,
            os=OperatingSystem.LINUX,
            triple="aarch64-unknown-linux-gnu",
        )

        lowering = AArch64TargetLowering(target)
        assert lowering.target is target

    def test_wasm_target_lowering(self):
        """测试 WebAssembly 目标 Lowering"""
        from zhc.codegen.target_lower import WasmTargetLowering
        from zhc.codegen.target_registry import Target, Architecture, OperatingSystem

        target = Target(
            name="wasm32",
            architecture=Architecture.WASM,
            os=OperatingSystem.UNKNOWN,
            triple="wasm32-unknown-unknown",
        )

        lowering = WasmTargetLowering(target)
        assert lowering.target is target


# ============================================================================
# Instruction Selector 测试
# ============================================================================


class TestInstructionSelector:
    """Instruction Selector 测试"""

    def test_instruction_selector_import(self):
        """测试 InstructionSelector 模块导入"""
        from zhc.codegen.instruction_selector import (
            InstructionSelector,
            X86_64InstructionSelector,
            AArch64InstructionSelector,
        )

        assert InstructionSelector is not None
        assert X86_64InstructionSelector is not None
        assert AArch64InstructionSelector is not None

    def test_sdnode_creation(self):
        """测试 SDNode 创建"""
        from zhc.codegen.instruction_selector import SDNode, ISDOpcode

        node = SDNode(opcode=ISDOpcode.ADD, operands=[], result_type="i64", id=1)
        assert node.opcode == ISDOpcode.ADD
        assert node.result_type == "i64"
        assert node.id == 1

    def test_operand_creation(self):
        """测试 Operand 创建"""
        from zhc.codegen.instruction_selector import Operand, OperandType

        reg = Operand(OperandType.REGISTER, "rax", size=64)
        imm = Operand(OperandType.IMMEDIATE, 42, size=32)
        mem = Operand(OperandType.MEMORY, "[rbp-8]", size=64)

        assert reg.is_register()
        assert imm.is_immediate()
        assert mem.is_memory()
        assert str(reg) == "%rax"
        assert str(imm) == "$42"
        assert str(mem) == "[[rbp-8]]"

    def test_machine_instruction_creation(self):
        """测试 MachineInstruction 创建"""
        from zhc.codegen.instruction_selector import (
            MachineInstruction,
            Operand,
            OperandType,
            OpcodeClass,
        )

        inst = MachineInstruction(
            opcode="ADD",
            operands=[
                Operand(OperandType.REGISTER, "rax"),
                Operand(OperandType.REGISTER, "rbx"),
            ],
            opcode_class=OpcodeClass.ARITHMETIC,
        )

        assert inst.opcode == "ADD"
        assert len(inst.operands) == 2
        assert inst.opcode_class == OpcodeClass.ARITHMETIC
        assert str(inst) == "ADD %rax, %rbx"

    def test_instruction_selector_select(self):
        """测试指令选择"""
        from zhc.codegen.instruction_selector import (
            InstructionSelector,
            ISDOpcode,
        )

        selector = InstructionSelector()

        # 创建简单的 DAG
        const1 = selector.create_node(ISDOpcode.Constant, value=10)
        const2 = selector.create_node(ISDOpcode.Constant, value=20)
        add_node = selector.create_node(ISDOpcode.ADD, const1, const2)

        # 选择指令
        instructions = selector.select([add_node])

        assert len(instructions) > 0
        assert any(inst.opcode == "ADD" for inst in instructions)

    def test_x86_64_instruction_selector(self):
        """测试 x86_64 指令选择器"""
        from zhc.codegen.instruction_selector import (
            X86_64InstructionSelector,
            ISDOpcode,
        )

        selector = X86_64InstructionSelector()

        # 测试 ADD 指令选择
        const1 = selector.create_node(ISDOpcode.Constant, value=10)
        const2 = selector.create_node(ISDOpcode.Constant, value=20)
        add_node = selector.create_node(ISDOpcode.ADD, const1, const2)

        instructions = selector.select([add_node])
        assert any(inst.opcode == "ADD" for inst in instructions)

    def test_aarch64_instruction_selector(self):
        """测试 AArch64 指令选择器"""
        from zhc.codegen.instruction_selector import (
            AArch64InstructionSelector,
            ISDOpcode,
        )

        selector = AArch64InstructionSelector()

        # 测试 ADD 指令选择
        const1 = selector.create_node(ISDOpcode.Constant, value=10)
        const2 = selector.create_node(ISDOpcode.Constant, value=20)
        add_node = selector.create_node(ISDOpcode.ADD, const1, const2)

        instructions = selector.select([add_node])
        assert any(inst.opcode == "ADD" for inst in instructions)


# ============================================================================
# Register Allocator 测试
# ============================================================================


class TestRegisterAllocator:
    """Register Allocator 测试"""

    def test_register_allocator_import(self):
        """测试 RegisterAllocator 模块导入"""
        from zhc.codegen.register_allocator import (
            RegisterAllocator,
            LinearScanRegisterAllocator,
            GraphColoringRegisterAllocator,
        )

        assert RegisterAllocator is not None
        assert LinearScanRegisterAllocator is not None
        assert GraphColoringRegisterAllocator is not None

    def test_register_creation(self):
        """测试 Register 创建"""
        from zhc.codegen.register_allocator import Register, RegisterClass

        reg = Register(
            name="rax",
            class_=RegisterClass.GENERAL,
            size=64,
            aliases=["eax", "ax", "al"],
        )

        assert reg.name == "rax"
        assert reg.class_ == RegisterClass.GENERAL
        assert reg.size == 64
        assert "eax" in reg.aliases
        assert str(reg) == "%rax"

    def test_virtual_register_creation(self):
        """测试 VirtualRegister 创建"""
        from zhc.codegen.register_allocator import VirtualRegister, RegisterClass

        vreg = VirtualRegister(id=0, class_=RegisterClass.GENERAL, size=64)

        assert vreg.id == 0
        assert vreg.class_ == RegisterClass.GENERAL
        assert vreg.size == 64
        assert not vreg.is_allocated
        assert not vreg.is_spilled
        assert str(vreg) == "v0"

    def test_live_interval_creation(self):
        """测试 LiveInterval 创建"""
        from zhc.codegen.register_allocator import (
            LiveInterval,
            VirtualRegister,
            RegisterClass,
        )

        vreg = VirtualRegister(id=0, class_=RegisterClass.GENERAL, size=64)
        interval = LiveInterval(vreg=vreg, start=0, end=10)

        assert interval.vreg is vreg
        assert interval.start == 0
        assert interval.end == 10
        assert interval.contains(5)
        assert not interval.contains(15)

    def test_live_interval_overlap(self):
        """测试 LiveInterval 重叠检测"""
        from zhc.codegen.register_allocator import (
            LiveInterval,
            VirtualRegister,
            RegisterClass,
        )

        vreg1 = VirtualRegister(id=0, class_=RegisterClass.GENERAL, size=64)
        vreg2 = VirtualRegister(id=1, class_=RegisterClass.GENERAL, size=64)

        interval1 = LiveInterval(vreg=vreg1, start=0, end=10)
        interval2 = LiveInterval(vreg=vreg2, start=5, end=15)
        interval3 = LiveInterval(vreg=vreg2, start=11, end=20)

        assert interval1.overlaps(interval2)
        assert not interval1.overlaps(interval3)

    def test_create_x86_64_registers(self):
        """测试 x86_64 寄存器创建"""
        from zhc.codegen.register_allocator import (
            create_x86_64_registers,
        )

        registers = create_x86_64_registers()

        assert len(registers) > 0
        assert any(r.name == "rax" for r in registers)
        assert any(r.name == "rbx" for r in registers)

        # 检查 rbx 是 callee-saved
        rbx = next(r for r in registers if r.name == "rbx")
        assert rbx.is_callee_saved

    def test_create_aarch64_registers(self):
        """测试 AArch64 寄存器创建"""
        from zhc.codegen.register_allocator import (
            create_aarch64_registers,
        )

        registers = create_aarch64_registers()

        assert len(registers) > 0
        assert any(r.name == "x0" for r in registers)
        assert any(r.name == "x1" for r in registers)

    def test_linear_scan_allocator(self):
        """测试线性扫描寄存器分配器"""
        from zhc.codegen.register_allocator import (
            LinearScanRegisterAllocator,
            RegisterClass,
            create_x86_64_registers,
        )

        registers = create_x86_64_registers()
        allocator = LinearScanRegisterAllocator(registers)

        # 创建虚拟寄存器
        vreg1 = allocator.create_vreg(RegisterClass.GENERAL, 64)
        vreg2 = allocator.create_vreg(RegisterClass.GENERAL, 64)

        # 添加活跃区间（不重叠）
        allocator.add_live_interval(vreg1, 0, 5)
        allocator.add_live_interval(vreg2, 6, 10)

        # 执行分配
        success = allocator.allocate()

        assert success
        assert allocator.get_assignment(vreg1.id) is not None
        assert allocator.get_assignment(vreg2.id) is not None

    def test_linear_scan_allocator_with_spill(self):
        """测试线性扫描寄存器分配器（溢出场景）"""
        from zhc.codegen.register_allocator import (
            LinearScanRegisterAllocator,
            RegisterClass,
            create_x86_64_registers,
        )

        registers = create_x86_64_registers()
        allocator = LinearScanRegisterAllocator(registers)

        # 创建大量虚拟寄存器（超过物理寄存器数量）
        # x86_64 有 14 个可分配通用寄存器（16 - rbp - rsp）
        # 我们创建 20 个虚拟寄存器，每个活跃区间为 [i, i+10]
        # 这样在位置 10 时，会有 11 个虚拟寄存器同时活跃，超过 14 个
        # 但为了确保溢出，我们使用更长的区间
        vregs = []
        for i in range(20):
            vreg = allocator.create_vreg(RegisterClass.GENERAL, 64)
            vregs.append(vreg)
            # 使用更长的活跃区间，确保同时活跃的数量超过物理寄存器数量
            allocator.add_live_interval(vreg, i, i + 15)

        # 执行分配
        success = allocator.allocate()

        # 应该有溢出（因为同时活跃的虚拟寄存器数量超过物理寄存器数量）
        assert not success
        assert len(allocator.spill_slots) > 0

    def test_graph_coloring_allocator(self):
        """测试图着色寄存器分配器"""
        from zhc.codegen.register_allocator import (
            GraphColoringRegisterAllocator,
            RegisterClass,
            create_x86_64_registers,
        )

        registers = create_x86_64_registers()
        allocator = GraphColoringRegisterAllocator(registers)

        # 创建虚拟寄存器
        vreg1 = allocator.create_vreg(RegisterClass.GENERAL, 64)
        vreg2 = allocator.create_vreg(RegisterClass.GENERAL, 64)

        # 添加活跃区间（不重叠）
        allocator.add_live_interval(vreg1, 0, 5)
        allocator.add_live_interval(vreg2, 6, 10)

        # 执行分配
        success = allocator.allocate()

        assert success
        assert allocator.get_assignment(vreg1.id) is not None
        assert allocator.get_assignment(vreg2.id) is not None

    def test_register_allocator_factory(self):
        """测试寄存器分配器工厂函数"""
        from zhc.codegen.register_allocator import create_register_allocator

        # 测试线性扫描
        allocator_ls = create_register_allocator("x86_64", "linear_scan")
        assert allocator_ls is not None

        # 测试图着色
        allocator_gc = create_register_allocator("x86_64", "graph_coloring")
        assert allocator_gc is not None

        # 测试 AArch64
        allocator_arm = create_register_allocator("aarch64", "linear_scan")
        assert allocator_arm is not None


# ============================================================================
# Frame Lower 测试
# ============================================================================


class TestFrameLower:
    """Frame Lower 测试"""

    def test_frame_lower_import(self):
        """测试 FrameLower 模块导入"""
        from zhc.codegen.frame_lower import (
            FrameLower,
            FrameInfo,
        )

        assert FrameLower is not None
        assert FrameInfo is not None

    def test_frame_info_creation(self):
        """测试 FrameInfo 创建"""
        from zhc.codegen.frame_lower import FrameInfo

        frame = FrameInfo(
            name="test_func",
            return_type="i32",
            params=[("i32", "x"), ("i64", "y")],
        )

        assert frame.name == "test_func"
        assert frame.return_type == "i32"
        assert len(frame.params) == 2


# ============================================================================
# Relocater 测试
# ============================================================================


class TestRelocater:
    """Relocater 测试"""

    def test_relocater_import(self):
        """测试 Relocater 模块导入"""
        from zhc.codegen.relocator import (
            Relocater,
            Relocation,
            RelocationType,
        )

        assert Relocater is not None
        assert Relocation is not None
        assert RelocationType is not None

    def test_relocation_creation(self):
        """测试 Relocation 创建"""
        from zhc.codegen.relocator import Relocation, RelocationType

        reloc = Relocation(
            symbol="test_func",
            type=RelocationType.ABS64,
            offset=0x1000,
            addend=0,
        )

        assert reloc.symbol == "test_func"
        assert reloc.type == RelocationType.ABS64
        assert reloc.offset == 0x1000


# ============================================================================
# Symbol Table 测试
# ============================================================================


class TestSymbolTable:
    """Symbol Table 测试"""

    def test_symbol_table_import(self):
        """测试 SymbolTable 模块导入"""
        from zhc.codegen.symbol_table import (
            SymbolTable,
            Symbol,
            SymbolKind,
        )

        assert SymbolTable is not None
        assert Symbol is not None
        assert SymbolKind is not None

    def test_symbol_creation(self):
        """测试 Symbol 创建"""
        from zhc.codegen.symbol_table import Symbol, SymbolKind

        symbol = Symbol(
            name="test_func",
            kind=SymbolKind.FUNCTION,
            size=64,
            is_global=True,
        )

        assert symbol.name == "test_func"
        assert symbol.kind == SymbolKind.FUNCTION
        assert symbol.size == 64
        assert symbol.is_global

    def test_symbol_table_operations(self):
        """测试 SymbolTable 操作"""
        from zhc.codegen.symbol_table import SymbolTable, Symbol, SymbolKind

        table = SymbolTable()

        # 添加符号
        symbol = Symbol(
            name="test_func",
            kind=SymbolKind.FUNCTION,
            size=64,
            is_global=True,
        )
        table.add_symbol(symbol)

        # 获取符号
        retrieved = table.get_symbol("test_func")
        assert retrieved is symbol

        # 检查符号存在
        assert table.has_symbol("test_func")
        assert not table.has_symbol("nonexistent")


# ============================================================================
# 集成测试
# ============================================================================


class TestCodegenIntegration:
    """代码生成集成测试"""

    def test_codegen_module_import(self):
        """测试 codegen 模块完整导入"""
        from zhc.codegen import (
            TargetLower,
            InstructionSelector,
            RegisterAllocator,
            FrameLower,
            Relocater,
            SymbolTable,
        )

        # 验证所有类都可导入
        assert TargetLower is not None
        assert InstructionSelector is not None
        assert RegisterAllocator is not None
        assert FrameLower is not None
        assert Relocater is not None
        assert SymbolTable is not None

    def test_x86_64_codegen_pipeline(self):
        """测试 x86_64 代码生成流程"""
        from zhc.codegen.target_lower import X86_64TargetLowering
        from zhc.codegen.instruction_selector import X86_64InstructionSelector
        from zhc.codegen.register_allocator import create_x86_64_registers
        from zhc.codegen.target_registry import Target, Architecture, OperatingSystem

        # 创建目标
        target = Target(
            name="x86_64",
            architecture=Architecture.X86_64,
            os=OperatingSystem.LINUX,
            triple="x86_64-unknown-linux-gnu",
        )

        # 创建各阶段组件
        lowering = X86_64TargetLowering(target)
        selector = X86_64InstructionSelector()
        registers = create_x86_64_registers()
        # allocator = LinearScanRegisterAllocator(registers)  # TODO: 后续集成测试

        # 验证组件创建成功
        assert lowering.target is target
        assert selector.target_name == "x86_64"
        assert len(registers) > 0

    def test_aarch64_codegen_pipeline(self):
        """测试 AArch64 代码生成流程"""
        from zhc.codegen.target_lower import AArch64TargetLowering
        from zhc.codegen.instruction_selector import AArch64InstructionSelector
        from zhc.codegen.register_allocator import create_aarch64_registers
        from zhc.codegen.target_registry import Target, Architecture, OperatingSystem

        # 创建目标
        target = Target(
            name="aarch64",
            architecture=Architecture.AARCH64,
            os=OperatingSystem.LINUX,
            triple="aarch64-unknown-linux-gnu",
        )

        # 创建各阶段组件
        lowering = AArch64TargetLowering(target)
        selector = AArch64InstructionSelector()
        registers = create_aarch64_registers()
        # allocator = LinearScanRegisterAllocator(registers)  # TODO: 后续集成测试

        # 验证组件创建成功
        assert lowering.target is target
        assert selector.target_name == "aarch64"
        assert len(registers) > 0

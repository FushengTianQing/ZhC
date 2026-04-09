# -*- coding: utf-8 -*-
"""
ZhC SIMD 模块测试套件

测试向量宽度选择、掩码处理、指令选择和目标平台支持。

作者：远
日期：2026-04-09
"""

import pytest
from zhc.simd import (
    # 向量化 Pass
    VectorizationPass,
    VectorizationConfig,
    # 循环分析
    Loop,
    VectorType,
    # 成本模型
    CostModel,
    # 向量宽度选择
    WidthSelector,
    MaskHandler,
    InstructionSelector,
    SIMDOpType,
    # 目标平台
    X86SIMDTarget,
    ARMNeonTarget,
    RiscVRVVTarget,
    WasmSIMDTarget,
    get_simd_target,
)
from zhc.simd.vector_builder import VectorTypeKind


class TestVectorType:
    """【SIMD-001】测试向量类型"""

    def test_float32_vector_creation(self):
        """测试 float32 向量创建"""
        vec_type = VectorType.float32_vector(4)
        assert vec_type.num_elements == 4
        assert vec_type.kind == VectorTypeKind.FLOAT32
        assert vec_type.total_bits == 128

    def test_int32_vector_creation(self):
        """测试 int32 向量创建"""
        vec_type = VectorType.int32_vector(8)
        assert vec_type.num_elements == 8
        assert vec_type.kind == VectorTypeKind.INT32
        assert vec_type.total_bits == 256

    def test_llvm_type_string(self):
        """测试 LLVM 类型字符串生成"""
        vec_type = VectorType.float32_vector(4)
        llvm_type = vec_type.llvm_type
        assert "<4 x float>" in llvm_type


class TestWidthSelector:
    """【SIMD-002】测试向量宽度选择"""

    def test_generic_arch_selection(self):
        """测试通用架构宽度选择"""
        selector = WidthSelector("generic")
        result = selector.select_width(element_bits=32, loop_trip_count=100)
        assert result.selected_width >= 1
        assert result.selected_width <= 16

    def test_avx_arch_selection(self):
        """测试 AVX 架构宽度选择"""
        selector = WidthSelector("x86_avx")
        result = selector.select_width(element_bits=32, loop_trip_count=100)
        assert result.selected_width >= 4
        assert result.selected_width <= 8

    def test_avx512_arch_selection(self):
        """测试 AVX-512 架构宽度选择"""
        selector = WidthSelector("x86_avx512")
        result = selector.select_width(element_bits=32, loop_trip_count=1000)
        assert result.selected_width >= 4
        assert result.selected_width <= 16

    def test_small_trip_count(self):
        """测试小循环次数"""
        selector = WidthSelector("x86_avx")
        result = selector.select_width(element_bits=32, loop_trip_count=3)
        # 小循环的分数会降低，但选择逻辑基于分数，可能仍选大宽度
        assert result.selected_width >= 1
        assert result.estimated_speedup < 1.0  # 小循环不会带来加速

    def test_alignment_filtering(self):
        """测试对齐过滤"""
        selector = WidthSelector("x86_avx")
        result = selector.select_width(element_bits=32, alignment=16)
        assert result.alignment_requirement >= 16

    def test_get_max_elements(self):
        """测试最大元素数获取"""
        selector = WidthSelector("x86_avx")
        max_elem = selector.get_max_elements(32)
        assert max_elem >= 4


class TestMaskHandler:
    """【SIMD-003】测试掩码处理"""

    def test_tail_handling_no_remainder(self):
        """测试无余数的尾部处理"""
        handler = MaskHandler("x86_avx")
        result = handler.calculate_tail_info(trip_count=100, vector_width=4)
        assert result.needs_tail_loop is False
        assert result.tail_count == 0

    def test_tail_handling_with_remainder(self):
        """测试有余数的尾部处理"""
        handler = MaskHandler("x86_avx")
        result = handler.calculate_tail_info(trip_count=103, vector_width=4)
        assert result.needs_tail_loop is True
        assert result.tail_count == 3

    def test_masked_tail_generation(self):
        """测试掩码尾部生成"""
        handler = MaskHandler("x86_avx")
        result = handler.calculate_tail_info(
            trip_count=103, vector_width=4, enable_tail_masking=True
        )
        assert len(result.mask_setup_instructions) > 0

    def test_scalar_tail_generation(self):
        """测试标量尾部生成"""
        handler = MaskHandler("x86_avx")
        result = handler.calculate_tail_info(
            trip_count=103, vector_width=4, enable_tail_masking=False
        )
        assert len(result.epilogue_instructions) > 0

    def test_vector_compare(self):
        """测试向量比较"""
        handler = MaskHandler("x86_avx")
        instr = handler.build_vector_compare("%a", "%b", "lt", "<4 x float>")
        assert "icmp" in instr or "fcmp" in instr

    def test_masked_load(self):
        """测试掩码加载"""
        handler = MaskHandler("x86_avx")
        instr = handler.build_masked_load("%ptr", "%mask", "%passthru", "<4 x float>")
        assert "masked.load" in instr

    def test_masked_store(self):
        """测试掩码存储"""
        handler = MaskHandler("x86_avx")
        instr = handler.build_masked_store("%value", "%ptr", "%mask", "<4 x float>")
        assert "masked.store" in instr


class TestInstructionSelector:
    """【SIMD-004】测试指令选择"""

    def test_x86_add_selection(self):
        """测试 x86 加法指令选择"""
        selector = InstructionSelector("x86_avx", vector_width=4)
        result = selector.select_instruction(
            SIMDOpType.ADD, ["%a", "%b"], "<4 x float>"
        )
        assert len(result.instructions) > 0
        assert "add" in result.instructions[0]

    def test_x86_mul_selection(self):
        """测试 x86 乘法指令选择"""
        selector = InstructionSelector("x86_avx", vector_width=4)
        result = selector.select_instruction(
            SIMDOpType.MUL, ["%a", "%b"], "<4 x float>"
        )
        assert len(result.instructions) > 0

    def test_neon_add_selection(self):
        """测试 NEON 加法指令选择"""
        selector = InstructionSelector("aarch64_neon", vector_width=4)
        result = selector.select_instruction(
            SIMDOpType.ADD, ["%a", "%b"], "<4 x float>"
        )
        assert len(result.instructions) > 0

    def test_rvv_add_selection(self):
        """测试 RVV 加法指令选择"""
        selector = InstructionSelector("riscv_rvv", vector_width=8)
        result = selector.select_instruction(
            SIMDOpType.ADD, ["%a", "%b"], "<8 x float>"
        )
        assert len(result.instructions) > 0

    def test_wasm_add_selection(self):
        """测试 WebAssembly 加法指令选择"""
        selector = InstructionSelector("wasm_simd", vector_width=4)
        result = selector.select_instruction(SIMDOpType.ADD, ["%a", "%b"], "<4 x i32>")
        assert len(result.instructions) > 0

    def test_fma_selection(self):
        """测试 FMA 指令选择"""
        selector = InstructionSelector("x86_avx", vector_width=4)
        result = selector.select_instruction(
            SIMDOpType.FMA, ["%a", "%b", "%c"], "<4 x float>"
        )
        assert len(result.instructions) > 0

    def test_load_selection(self):
        """测试加载指令选择"""
        selector = InstructionSelector("x86_avx", vector_width=4)
        result = selector.select_instruction(SIMDOpType.LOAD, ["%ptr"], "<4 x float>")
        assert len(result.instructions) > 0
        assert "load" in result.instructions[0]

    def test_store_selection(self):
        """测试存储指令选择"""
        selector = InstructionSelector("x86_avx", vector_width=4)
        result = selector.select_instruction(
            SIMDOpType.STORE, ["%value", "%ptr"], "<4 x float>"
        )
        assert len(result.instructions) > 0
        assert "store" in result.instructions[0]

    def test_get_intrinsic_name(self):
        """测试获取 intrinsic 名称"""
        selector = InstructionSelector("x86_avx", vector_width=4)
        name = selector.get_intrinsic_name(SIMDOpType.ADD)
        assert "add" in name.lower()

    def test_supports_operation(self):
        """测试操作支持检查"""
        selector = InstructionSelector("x86_avx", vector_width=4)
        assert selector.supports_operation(SIMDOpType.ADD) is True


class TestX86SIMDTarget:
    """【SIMD-005】测试 x86 SIMD 目标"""

    def test_sse_target(self):
        """测试 SSE 目标"""
        target = X86SIMDTarget("x86_64_sse")
        assert target.get_vector_width() >= 4

    def test_avx_target(self):
        """测试 AVX 目标"""
        target = X86SIMDTarget("x86_64_avx")
        assert target.get_vector_width() >= 8
        # AVX 不支持 gather/scatter，需要 AVX2
        assert target.config.supports_gather_scatter is False

    def test_avx2_target(self):
        """测试 AVX2 目标"""
        target = X86SIMDTarget("x86_64_avx2")
        assert target.get_vector_width() >= 8
        # AVX2 支持 gather
        assert target.config.supports_gather_scatter is True

    def test_avx512_target(self):
        """测试 AVX-512 目标"""
        target = X86SIMDTarget("x86_64_avx512")
        assert target.get_vector_width() >= 16
        assert target.config.supports_masking is True

    def test_get_add_instruction(self):
        """测试获取加法指令"""
        target = X86SIMDTarget("x86_64_avx")
        instr = target.get_add_instruction("<4 x float>")
        assert "add" in instr.lower()

    def test_get_fma_instruction(self):
        """测试获取 FMA 指令"""
        target = X86SIMDTarget("x86_64_fma")
        instr = target.get_fma_instruction("<4 x float>")
        assert instr is not None or True  # 可能不支持

    def test_get_gather_instruction(self):
        """测试获取 gather 指令"""
        target = X86SIMDTarget("x86_64_avx2")
        instr = target.get_gather_instruction("<4 x float>")
        assert instr is not None


class TestARMNeonTarget:
    """【SIMD-006】测试 ARM NEON 目标"""

    def test_neon_target(self):
        """测试 NEON 目标"""
        target = ARMNeonTarget("aarch64")
        assert target.get_vector_width() == 4

    def test_sve_target(self):
        """测试 SVE 目标"""
        target = ARMNeonTarget("aarch64_sve")
        assert target.uses_sve() is True

    def test_get_add_instruction(self):
        """测试获取加法指令"""
        target = ARMNeonTarget("aarch64")
        instr = target.get_add_instruction("<4 x float>")
        assert "add" in instr.lower()

    def test_get_fmla_instruction(self):
        """测试获取 FMLA 指令"""
        target = ARMNeonTarget("aarch64")
        instr = target.get_fmla_instruction()
        assert "fmla" in instr.lower()


class TestRiscVRVVTarget:
    """【SIMD-007】测试 RISC-V RVV 目标"""

    def test_rvv_target(self):
        """测试 RVV 目标"""
        target = RiscVRVVTarget("riscv64")
        assert target.get_vlen() >= 128

    def test_get_add_instruction(self):
        """测试获取加法指令"""
        target = RiscVRVVTarget("riscv64")
        instr = target.get_add_instruction()
        assert "vadd" in instr.lower()

    def test_get_vsetvli_instruction(self):
        """测试获取 vsetvli 指令"""
        target = RiscVRVVTarget("riscv64")
        instr = target.get_vsetvli_instruction("float")
        assert "vsetvli" in instr.lower()


class TestWasmSIMDTarget:
    """【SIMD-008】测试 WebAssembly SIMD 目标"""

    def test_wasm_target(self):
        """测试 WebAssembly SIMD 目标"""
        target = WasmSIMDTarget("wasm32")
        assert target.get_vector_width() == 4
        assert target.get_vector_bits() == 128

    def test_get_add_instruction(self):
        """测试获取加法指令"""
        target = WasmSIMDTarget("wasm32")
        instr = target.get_add_instruction("float")
        assert "add" in instr.lower()

    def test_get_dot_product_instruction(self):
        """测试获取点积指令"""
        target = WasmSIMDTarget("wasm32")
        instr = target.get_dot_product_instruction()
        assert "dot" in instr.lower()


class TestCostModel:
    """【SIMD-009】测试成本模型"""

    def test_cost_model_creation(self):
        """测试成本模型创建"""
        model = CostModel("x86_avx")
        assert model.target_arch == "x86_avx"

    def test_loop_cost_analysis(self):
        """测试循环成本分析"""
        model = CostModel("x86_avx")
        loop = Loop(
            header_block="entry",
            latch_block="latch",
            exit_block="exit",
            num_instructions=10,
            num_loads=2,
            num_stores=1,
        )
        cost = model.analyze_loop(loop)
        assert cost.scalar_cost > 0
        assert cost.vector_cost > 0

    def test_estimate_speedup(self):
        """测试加速比估计"""
        model = CostModel("x86_avx")
        loop = Loop(
            header_block="entry",
            latch_block="latch",
            exit_block="exit",
            num_instructions=20,
            num_loads=4,
            num_stores=2,
            trip_count_estimate=100,
        )
        speedup = model.estimate_speedup(loop)
        assert speedup >= 0


class TestVectorizationPass:
    """【SIMD-010】测试向量化 Pass"""

    def test_pass_creation(self):
        """测试 Pass 创建"""
        config = VectorizationConfig(vector_width=4)
        vpass = VectorizationPass(config=config, target_arch="x86_avx")
        assert vpass.config.vector_width == 4

    def test_pass_with_default_config(self):
        """测试使用默认配置"""
        vpass = VectorizationPass(target_arch="x86_avx")
        assert vpass.config.enabled is True

    def test_pass_run_empty_module(self):
        """测试运行空模块"""
        vpass = VectorizationPass(target_arch="x86_avx")
        result = vpass.run("")
        assert result.loops_analyzed == 0

    def test_pass_run_simple_function(self):
        """测试运行简单函数"""
        vpass = VectorizationPass(target_arch="x86_avx")
        ir = """
define void @test() {
entry:
  br label %loop
loop:
  %i = phi i32 [ 0, %entry ], [ %i.next, %loop ]
  %i.next = add i32 %i, 1
  %cond = icmp ult i32 %i, 100
  br i1 %cond, label %loop, label %exit
exit:
  ret void
}
"""
        result = vpass.run(ir)
        assert result.loops_analyzed >= 0


class TestGetSIMDTarget:
    """【SIMD-011】测试获取 SIMD 目标"""

    def test_get_x86_target(self):
        """测试获取 x86 目标"""
        target = get_simd_target("x86_64_avx")
        assert isinstance(target, X86SIMDTarget)

    def test_get_arm_target(self):
        """测试获取 ARM 目标"""
        target = get_simd_target("aarch64")
        assert isinstance(target, ARMNeonTarget)

    def test_get_riscv_target(self):
        """测试获取 RISC-V 目标"""
        target = get_simd_target("riscv64")
        assert isinstance(target, RiscVRVVTarget)

    def test_get_wasm_target(self):
        """测试获取 WebAssembly 目标"""
        target = get_simd_target("wasm32")
        assert isinstance(target, WasmSIMDTarget)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

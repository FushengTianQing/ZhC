# -*- coding: utf-8 -*-
"""
ZhC 后端模块单元测试

测试重构后的后端组件。

作者：远
日期：2026-04-09
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import tempfile

from zhc.backend.type_system import TypeMapper, get_type_mapper
from zhc.backend.compiler_runner import (
    CompilerRunner,
    CompilerConfig,
    CompilerOutput,
    TemporaryFileManager,
)
from zhc.backend.compile_cache import CompileCache, CachedBackend
from zhc.backend.llvm_instruction_strategy import (
    InstructionStrategyFactory,
    AddStrategy,
    SubStrategy,
    Opcode,
    # 新增策略
    LAndStrategy,
    LOrStrategy,
    LNotStrategy,
    SwitchStrategy,
    PhiStrategy,
    GetPtrStrategy,
    GepStrategy,
    Int2PtrStrategy,
    Ptr2IntStrategy,
    ConstStrategy,
    NopStrategy,
    GlobalStrategy,
    ArgStrategy,
)


class TestTypeMapper:
    """测试类型映射器"""

    def test_to_c_basic_types(self):
        """测试基本类型映射到 C"""
        mapper = TypeMapper()

        assert mapper.to_c("整数型") == "int"
        assert mapper.to_c("浮点型") == "float"
        assert mapper.to_c("双精度浮点型") == "double"
        assert mapper.to_c("字符型") == "char"
        assert mapper.to_c("空类型") == "void"

    def test_to_c_pointer_types(self):
        """测试指针类型映射"""
        mapper = TypeMapper()

        assert mapper.to_c("整数型*") == "int*"
        assert mapper.to_c("字符型*") == "char*"

    def test_to_c_unknown_type(self):
        """测试未知类型"""
        mapper = TypeMapper()

        # 未知类型返回原值
        assert mapper.to_c("custom_type") == "custom_type"

    def test_get_type_info(self):
        """测试获取类型信息"""
        mapper = TypeMapper()

        info = mapper.get_type_info("整数型")

        assert info.zhc_type == "整数型"
        assert info.c_type == "int"
        assert info.size_bits == 32
        assert info.is_signed == True
        assert info.is_float == False

    def test_get_type_mapper_singleton(self):
        """测试全局类型映射器"""
        mapper1 = get_type_mapper()
        mapper2 = get_type_mapper()

        assert mapper1 is mapper2


class TestCompilerRunner:
    """测试编译器运行器"""

    def test_config_creation(self):
        """测试配置创建"""
        config = CompilerConfig(
            executable="gcc",
            default_flags=["-O2", "-Wall"],
        )

        assert config.executable == "gcc"
        assert "-O2" in config.default_flags

    def test_output_creation(self):
        """测试输出创建"""
        output = CompilerOutput(
            stdout="test stdout",
            stderr="test stderr",
            returncode=0,
            duration_seconds=1.5,
        )

        assert output.stdout == "test stdout"
        assert output.returncode == 0

    @patch("subprocess.run")
    def test_check_available_success(self, mock_run):
        """测试编译器可用检查（成功）"""
        mock_run.return_value = MagicMock(returncode=0)

        config = CompilerConfig(executable="gcc")
        runner = CompilerRunner(config)

        assert runner.check_available() == True

    @patch("subprocess.run")
    def test_check_available_failure(self, mock_run):
        """测试编译器可用检查（失败）"""
        mock_run.side_effect = FileNotFoundError()

        config = CompilerConfig(executable="nonexistent_compiler")
        runner = CompilerRunner(config)

        assert runner.check_available() == False

    def test_parse_output_errors(self):
        """测试错误解析"""
        runner = CompilerRunner(CompilerConfig(executable="gcc"))

        output = CompilerOutput(
            stdout="",
            stderr="error: undefined reference to 'main'\nwarning: unused variable",
            returncode=1,
            duration_seconds=1.0,
        )

        errors, warnings = runner.parse_output(output)

        assert len(errors) == 1
        assert "undefined reference" in errors[0]
        assert len(warnings) == 1
        assert "unused variable" in warnings[0]


class TestTemporaryFileManager:
    """测试临时文件管理器"""

    def test_create_temp_file(self):
        """测试创建临时文件"""
        with TemporaryFileManager() as manager:
            temp_file = manager.create_temp_file(suffix=".c")

            assert temp_file.exists()
            assert temp_file.suffix == ".c"

        # 退出后应该被删除
        assert not temp_file.exists()

    def test_keep_temp_files(self):
        """测试保留临时文件"""
        with TemporaryFileManager(keep_temp=True) as manager:
            temp_file = manager.create_temp_file(suffix=".c")

        # 应该保留
        assert temp_file.exists()

        # 手动清理
        temp_file.unlink()


class TestCompileCache:
    """测试编译缓存"""

    def test_compute_hash(self):
        """测试哈希计算"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CompileCache(cache_dir=Path(tmpdir))

            hash1 = cache.compute_hash("content1", {"opt": "O2"})
            hash2 = cache.compute_hash("content1", {"opt": "O2"})
            hash3 = cache.compute_hash("content2", {"opt": "O2"})

            # 相同内容应该产生相同哈希
            assert hash1 == hash2

            # 不同内容应该产生不同哈希
            assert hash1 != hash3

    def test_put_and_get(self):
        """测试存储和获取"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CompileCache(cache_dir=Path(tmpdir))

            # 创建测试文件
            test_file = Path(tmpdir) / "test_output.o"
            test_file.write_text("test content")

            # 存储到缓存
            cache_key = "test_key"
            cache.put(
                cache_key=cache_key,
                input_hash="input_hash",
                output_path=test_file,
            )

            # 从缓存获取
            cached_path = cache.get(cache_key)

            assert cached_path == test_file

    def test_get_stats(self):
        """测试统计信息"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CompileCache(cache_dir=Path(tmpdir))

            stats = cache.get_stats()

            assert "entries" in stats
            assert "total_size_mb" in stats
            assert "usage_percent" in stats

    def test_clear(self):
        """测试清空缓存"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CompileCache(cache_dir=Path(tmpdir))

            # 创建测试文件
            test_file = Path(tmpdir) / "test_output.o"
            test_file.write_text("test content")

            # 存储到缓存
            cache.put("test_key", "hash", test_file)

            # 清空
            cache.clear()

            # 应该无法获取
            assert cache.get("test_key") is None


class TestInstructionStrategyFactory:
    """测试指令策略工厂"""

    def test_get_strategy_add(self):
        """测试获取加法策略"""
        strategy = InstructionStrategyFactory.get_strategy(Opcode.ADD)

        assert strategy is not None
        assert isinstance(strategy, AddStrategy)
        assert strategy.opcode == Opcode.ADD

    def test_get_strategy_sub(self):
        """测试获取减法策略"""
        strategy = InstructionStrategyFactory.get_strategy(Opcode.SUB)

        assert strategy is not None
        assert isinstance(strategy, SubStrategy)
        assert strategy.opcode == Opcode.SUB

    def test_get_strategy_unknown(self):
        """测试获取未知策略"""
        # PHI 指令可能没有实现，但我们只检查不会抛出异常
        InstructionStrategyFactory.get_strategy(Opcode.PHI)

    def test_register_custom_strategy(self):
        """测试注册自定义策略"""
        # 保存原始策略
        original_strategy = InstructionStrategyFactory.get_strategy(Opcode.ADD)

        # 创建自定义策略
        class CustomAddStrategy(AddStrategy):
            pass

        custom = CustomAddStrategy()
        InstructionStrategyFactory.register(custom)

        # 获取策略 - 应该返回自定义策略
        strategy = InstructionStrategyFactory.get_strategy(Opcode.ADD)

        # 注意：CustomAddStrategy 的 opcode 是继承自 AddStrategy 的 ADD
        # 所以它会覆盖原来的 AddStrategy
        assert strategy is custom

        # 恢复原始策略
        if original_strategy is not None:
            InstructionStrategyFactory.register(original_strategy)


class TestLogicalStrategies:
    """测试逻辑运算策略"""

    def test_land_strategy(self):
        """测试逻辑与策略"""
        strategy = InstructionStrategyFactory.get_strategy(Opcode.L_AND)

        assert strategy is not None
        assert isinstance(strategy, LAndStrategy)
        assert strategy.opcode == Opcode.L_AND

    def test_lor_strategy(self):
        """测试逻辑或策略"""
        strategy = InstructionStrategyFactory.get_strategy(Opcode.L_OR)

        assert strategy is not None
        assert isinstance(strategy, LOrStrategy)
        assert strategy.opcode == Opcode.L_OR

    def test_lnot_strategy(self):
        """测试逻辑非策略"""
        strategy = InstructionStrategyFactory.get_strategy(Opcode.L_NOT)

        assert strategy is not None
        assert isinstance(strategy, LNotStrategy)
        assert strategy.opcode == Opcode.L_NOT


class TestControlFlowStrategies:
    """测试控制流指令策略"""

    def test_switch_strategy(self):
        """测试 Switch 分支跳转策略"""
        strategy = InstructionStrategyFactory.get_strategy(Opcode.SWITCH)

        assert strategy is not None
        assert isinstance(strategy, SwitchStrategy)
        assert strategy.opcode == Opcode.SWITCH

    def test_phi_strategy(self):
        """测试 PHI 节点策略"""
        strategy = InstructionStrategyFactory.get_strategy(Opcode.PHI)

        assert strategy is not None
        assert isinstance(strategy, PhiStrategy)
        assert strategy.opcode == Opcode.PHI


class TestMemoryPointerStrategies:
    """测试内存指针运算策略"""

    def test_getptr_strategy(self):
        """测试 GETPTR 策略"""
        strategy = InstructionStrategyFactory.get_strategy(Opcode.GETPTR)

        assert strategy is not None
        assert isinstance(strategy, GetPtrStrategy)
        assert strategy.opcode == Opcode.GETPTR

    def test_gep_strategy(self):
        """测试 GEP 指针运算策略"""
        strategy = InstructionStrategyFactory.get_strategy(Opcode.GEP)

        assert strategy is not None
        assert isinstance(strategy, GepStrategy)
        assert strategy.opcode == Opcode.GEP


class TestConversionStrategies:
    """测试类型转换策略"""

    def test_int2ptr_strategy(self):
        """测试整数转指针策略"""
        strategy = InstructionStrategyFactory.get_strategy(Opcode.INT2PTR)

        assert strategy is not None
        assert isinstance(strategy, Int2PtrStrategy)
        assert strategy.opcode == Opcode.INT2PTR

    def test_ptr2int_strategy(self):
        """测试指针转整数策略"""
        strategy = InstructionStrategyFactory.get_strategy(Opcode.PTR2INT)

        assert strategy is not None
        assert isinstance(strategy, Ptr2IntStrategy)
        assert strategy.opcode == Opcode.PTR2INT


class TestOtherStrategies:
    """测试其他指令策略"""

    def test_const_strategy(self):
        """测试常量策略"""
        strategy = InstructionStrategyFactory.get_strategy(Opcode.CONST)

        assert strategy is not None
        assert isinstance(strategy, ConstStrategy)
        assert strategy.opcode == Opcode.CONST

    def test_nop_strategy(self):
        """测试空操作策略"""
        strategy = InstructionStrategyFactory.get_strategy(Opcode.NOP)

        assert strategy is not None
        assert isinstance(strategy, NopStrategy)
        assert strategy.opcode == Opcode.NOP

    def test_global_strategy(self):
        """测试全局变量策略"""
        strategy = InstructionStrategyFactory.get_strategy(Opcode.GLOBAL)

        assert strategy is not None
        assert isinstance(strategy, GlobalStrategy)
        assert strategy.opcode == Opcode.GLOBAL

    def test_arg_strategy(self):
        """测试函数参数策略"""
        strategy = InstructionStrategyFactory.get_strategy(Opcode.ARG)

        assert strategy is not None
        assert isinstance(strategy, ArgStrategy)
        assert strategy.opcode == Opcode.ARG


class TestAllOpcodesCovered:
    """测试所有操作码都被覆盖"""

    def test_all_arithmetic_covered(self):
        """测试算术指令都已实现"""
        arithmetic_ops = [
            Opcode.ADD,
            Opcode.SUB,
            Opcode.MUL,
            Opcode.DIV,
            Opcode.MOD,
            Opcode.NEG,
        ]

        for op in arithmetic_ops:
            strategy = InstructionStrategyFactory.get_strategy(op)
            assert strategy is not None, f"算术指令 {op.name} 未实现"

    def test_all_comparison_covered(self):
        """测试比较指令都已实现"""
        comparison_ops = [
            Opcode.EQ,
            Opcode.NE,
            Opcode.LT,
            Opcode.LE,
            Opcode.GT,
            Opcode.GE,
        ]

        for op in comparison_ops:
            strategy = InstructionStrategyFactory.get_strategy(op)
            assert strategy is not None, f"比较指令 {op.name} 未实现"

    def test_all_logical_covered(self):
        """测试逻辑指令都已实现"""
        logical_ops = [Opcode.L_AND, Opcode.L_OR, Opcode.L_NOT]

        for op in logical_ops:
            strategy = InstructionStrategyFactory.get_strategy(op)
            assert strategy is not None, f"逻辑指令 {op.name} 未实现"

    def test_all_bitwise_covered(self):
        """测试位运算指令都已实现"""
        bitwise_ops = [
            Opcode.AND,
            Opcode.OR,
            Opcode.XOR,
            Opcode.NOT,
            Opcode.SHL,
            Opcode.SHR,
        ]

        for op in bitwise_ops:
            strategy = InstructionStrategyFactory.get_strategy(op)
            assert strategy is not None, f"位运算指令 {op.name} 未实现"

    def test_all_memory_covered(self):
        """测试内存指令都已实现"""
        memory_ops = [
            Opcode.ALLOC,
            Opcode.LOAD,
            Opcode.STORE,
            Opcode.GETPTR,
            Opcode.GEP,
        ]

        for op in memory_ops:
            strategy = InstructionStrategyFactory.get_strategy(op)
            assert strategy is not None, f"内存指令 {op.name} 未实现"

    def test_all_control_flow_covered(self):
        """测试控制流指令都已实现"""
        control_flow_ops = [
            Opcode.JMP,
            Opcode.JZ,
            Opcode.RET,
            Opcode.CALL,
            Opcode.SWITCH,
            Opcode.PHI,
        ]

        for op in control_flow_ops:
            strategy = InstructionStrategyFactory.get_strategy(op)
            assert strategy is not None, f"控制流指令 {op.name} 未实现"

    def test_all_conversion_covered(self):
        """测试类型转换指令都已实现"""
        conversion_ops = [
            Opcode.ZEXT,
            Opcode.SEXT,
            Opcode.TRUNC,
            Opcode.BITCAST,
            Opcode.INT2PTR,
            Opcode.PTR2INT,
        ]

        for op in conversion_ops:
            strategy = InstructionStrategyFactory.get_strategy(op)
            assert strategy is not None, f"类型转换指令 {op.name} 未实现"

    def test_all_other_covered(self):
        """测试其他指令都已实现"""
        other_ops = [Opcode.CONST, Opcode.NOP, Opcode.GLOBAL, Opcode.ARG]

        for op in other_ops:
            strategy = InstructionStrategyFactory.get_strategy(op)
            assert strategy is not None, f"其他指令 {op.name} 未实现"


class TestCachedBackend:
    """测试缓存后端装饰器"""

    def test_cached_backend_wrapper(self):
        """测试缓存后端包装"""
        # 创建模拟后端
        mock_backend = Mock()
        mock_backend.name = "test_backend"
        mock_backend.compile = Mock(
            return_value=Mock(
                success=True,
                output_files=[Path("/tmp/test.o")],
            )
        )

        # 创建缓存
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CompileCache(cache_dir=Path(tmpdir))

            # 创建缓存后端
            cached_backend = CachedBackend(mock_backend, cache)

            # 测试属性代理
            assert cached_backend.name == "test_backend"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

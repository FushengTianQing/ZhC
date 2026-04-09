# -*- coding: utf-8 -*-
"""
ZhC 优化Pass集成测试

测试完整的优化管道，包括：
- PassManager 完整流程
- 优化级别配置
- Pass 依赖管理
- 优化统计

运行：
    python -m pytest tests/test_optimization_pipeline.py -v

作者：远
日期：2026-04-09
"""

import pytest
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zhc.optimization.pass_manager import PassManager, PassState
from zhc.optimization.pass_registry import PassRegistry
from zhc.optimization.optimization_levels import OptimizationLevel
from zhc.optimization.pass_config import StandardPassConfig
from zhc.optimization.optimization_observer import (
    OptimizationObserver,
    StatsObserver,
    LoggingObserver,
)


# =============================================================================
# 测试辅助类
# =============================================================================


class MockModule:
    """模拟LLVM模块用于测试"""

    def __init__(self):
        self.functions = []
        self.name = "test_module"

    def __str__(self):
        return f"Module({self.name})"


class MockFunction:
    """模拟LLVM函数用于测试"""

    def __init__(self, name="test_func", is_declaration=False):
        self.name = name
        self.is_declaration = is_declaration
        self.blocks = []

    def __str__(self):
        return f"Function({self.name})"


class MockBlock:
    """模拟LLVM基本块用于测试"""

    def __init__(self, name="entry"):
        self.name = name
        self.instructions = []


class MockInstruction:
    """模拟LLVM指令用于测试"""

    def __init__(self, opcode, operands=None):
        self.opcode = opcode
        self.operands = operands or []
        self.name = str(opcode)

    def __str__(self):
        return f"{self.opcode}"


def create_test_module():
    """创建测试模块"""
    module = MockModule()

    # 创建几个测试函数
    for i in range(3):
        func = MockFunction(f"test_func_{i}")
        block = MockBlock("entry")

        # 添加一些指令
        block.instructions.append(MockInstruction("add", []))
        block.instructions.append(MockInstruction("ret", []))

        func.blocks.append(block)
        module.functions.append(func)

    return module


# =============================================================================
# PassManager 集成测试
# =============================================================================


class TestPassManagerIntegration:
    """PassManager 集成测试"""

    def test_full_optimization_pipeline(self):
        """测试完整优化管道"""
        module = create_test_module()

        # 创建 PassManager
        pm = PassManager(module, OptimizationLevel.O2)

        # 验证管道配置
        assert pm.level == OptimizationLevel.O2
        assert len(pm.pipeline.passes) > 0

        # 运行优化
        result = pm.run()

        # 验证结果
        assert result is module
        assert len(pm.executions) > 0

    def test_all_optimization_levels(self):
        """测试所有优化级别"""
        for level in OptimizationLevel:
            module = create_test_module()
            pm = PassManager(module, level)

            # 验证管道配置
            assert pm.level == level
            assert len(pm.pipeline.passes) > 0

            # 运行优化
            result = pm.run()
            assert result is module

    def test_pass_execution_order(self):
        """测试Pass执行顺序"""
        module = create_test_module()
        pm = PassManager(module, OptimizationLevel.O2)

        # 运行优化
        pm.run()

        # 获取执行顺序
        execution_order = pm.get_execution_order()
        assert len(execution_order) > 0

        # 验证拓扑排序（gvn应该在mem2reg之后）
        if "gvn" in execution_order and "mem2reg" in execution_order:
            gvn_idx = execution_order.index("gvn")
            mem2reg_idx = execution_order.index("mem2reg")
            assert mem2reg_idx < gvn_idx

    def test_pass_state_tracking(self):
        """测试Pass状态跟踪"""
        module = create_test_module()
        pm = PassManager(module, OptimizationLevel.O0)

        # 运行优化
        pm.run()

        # 检查执行状态
        for pass_name, execution in pm.executions.items():
            assert execution.state in [
                PassState.COMPLETED,
                PassState.FAILED,
                PassState.SKIPPED,
            ]

    def test_statistics_collection(self):
        """测试统计信息收集"""
        module = create_test_module()
        pm = PassManager(module, OptimizationLevel.O2)

        # 运行优化
        pm.run()

        # 获取统计信息
        stats = pm.get_stats()

        assert isinstance(stats, dict)
        assert "total_passes" in stats
        assert "completed" in stats
        assert "failed" in stats
        assert "skipped" in stats
        assert "level" in stats
        assert stats["level"] == "O2"

    def test_custom_pass_addition(self):
        """测试自定义Pass添加"""
        module = create_test_module()
        pm = PassManager(module, OptimizationLevel.O0)

        # 添加自定义Pass
        pm.add_pass("dce")
        pm.add_pass("gvn")

        # 验证添加成功
        pass_names = [p.name for p in pm.pipeline.passes]
        assert "dce" in pass_names
        assert "gvn" in pass_names

    def test_pass_disable_enable(self):
        """测试Pass禁用和启用"""
        module = create_test_module()
        pm = PassManager(module, OptimizationLevel.O2)

        # 禁用inline
        pm.disable_pass("inline")

        # 验证禁用
        inline_pass = next((p for p in pm.pipeline.passes if p.name == "inline"), None)
        assert inline_pass is not None
        assert inline_pass.enabled is False

        # 重新启用
        pm.enable_pass("inline")
        assert inline_pass.enabled is True


# =============================================================================
# Observer 集成测试
# =============================================================================


class TestObserverIntegration:
    """Observer 集成测试"""

    def test_stats_observer(self):
        """测试统计观察器"""
        module = create_test_module()
        pm = PassManager(module, OptimizationLevel.O0)

        # 添加统计观察器
        stats_observer = StatsObserver()
        pm.add_observer(stats_observer)

        # 运行优化
        pm.run()

        # 获取统计信息
        stats = stats_observer.get_stats()
        assert stats is not None
        # O0只有no-op和verify，可能全部被跳过
        assert isinstance(stats.passes_run, list)

    def test_logging_observer(self):
        """测试日志观察器"""
        module = create_test_module()
        pm = PassManager(module, OptimizationLevel.O0)

        # 添加日志观察器
        logging_observer = LoggingObserver()
        pm.add_observer(logging_observer)

        # 运行优化（不应该抛出异常）
        result = pm.run()
        assert result is module

    def test_multiple_observers(self):
        """测试多个观察器"""
        module = create_test_module()
        pm = PassManager(module, OptimizationLevel.O0)

        # 添加多个观察器
        stats_observer = StatsObserver()
        logging_observer = LoggingObserver()

        pm.add_observer(stats_observer)
        pm.add_observer(logging_observer)

        # 运行优化
        pm.run()

        # 验证观察器都工作
        assert isinstance(stats_observer.get_stats().passes_run, list)


# =============================================================================
# 优化级别配置测试
# =============================================================================


class TestOptimizationLevelConfig:
    """优化级别配置测试"""

    def test_o0_configuration(self):
        """测试O0配置"""
        passes = StandardPassConfig.get_passes_for_level(OptimizationLevel.O0)

        assert "no-op" in passes
        assert "verify" in passes
        assert len(passes) == 2

    def test_o1_configuration(self):
        """测试O1配置"""
        passes = StandardPassConfig.get_passes_for_level(OptimizationLevel.O1)

        assert "inline" in passes
        assert "mem2reg" in passes
        assert "gvn" in passes
        assert "dce" in passes

    def test_o2_configuration(self):
        """测试O2配置"""
        passes = StandardPassConfig.get_passes_for_level(OptimizationLevel.O2)

        assert "inline" in passes
        assert "loop-rotate" in passes
        assert "licm" in passes
        assert "gvn" in passes
        assert "sccp" in passes

    def test_o3_configuration(self):
        """测试O3配置"""
        o2_passes = StandardPassConfig.get_passes_for_level(OptimizationLevel.O2)
        o3_passes = StandardPassConfig.get_passes_for_level(OptimizationLevel.O3)

        # O3应该包含O2的所有Pass
        for pass_name in o2_passes:
            assert pass_name in o3_passes

        # O3应该有额外的Pass
        assert "loop-unroll" in o3_passes
        assert "loop-vectorize" in o3_passes

    def test_os_configuration(self):
        """测试Os配置"""
        passes = StandardPassConfig.get_passes_for_level(OptimizationLevel.Os)

        assert "inline" in passes
        assert "mergefunc" in passes
        assert "constmerge" in passes

    def test_oz_configuration(self):
        """测试Oz配置"""
        passes = StandardPassConfig.get_passes_for_level(OptimizationLevel.Oz)

        assert "inline" in passes
        assert "globalopt" in passes


# =============================================================================
# PassRegistry 集成测试
# =============================================================================


class TestPassRegistryIntegration:
    """PassRegistry 集成测试"""

    def test_all_standard_passes_registered(self):
        """测试所有标准Pass已注册"""
        standard_passes = [
            "no-op",
            "verify",
            "inline",
            "mem2reg",
            "early-cse",
            "gvn",
            "dce",
            "adce",
            "sccp",
            "simplifycfg",
            "mergeret",
            "reassociate",
            "loop-rotate",
            "licm",
            "loop-unswitch",
            "indvars",
            "loop-unroll",
            "loop-vectorize",
            "slp-vectorize",
            "gvn-hoist",
            "aggressive-dce",
            "function-attrs",
            "mergefunc",
            "constmerge",
            "globalopt",
        ]

        for pass_name in standard_passes:
            info = PassRegistry.get_info(pass_name)
            assert info is not None, f"{pass_name} not registered"

    def test_pass_dependencies(self):
        """测试Pass依赖关系"""
        # gvn应该依赖mem2reg
        gvn_info = PassRegistry.get_info("gvn")
        assert "mem2reg" in gvn_info.required_passes

        # inline应该依赖mem2reg
        inline_info = PassRegistry.get_info("inline")
        assert "mem2reg" in inline_info.required_passes

    def test_pass_types(self):
        """测试Pass类型"""
        from zhc.optimization.pass_registry import PassType

        # UTILITY 类型
        no_op_info = PassRegistry.get_info("no-op")
        assert no_op_info.pass_type == PassType.UTILITY

        # TRANSFORM 类型
        dce_info = PassRegistry.get_info("dce")
        assert dce_info.pass_type == PassType.TRANSFORM

        # ANALYSIS 类型
        function_attrs_info = PassRegistry.get_info("function-attrs")
        assert function_attrs_info.pass_type == PassType.ANALYSIS


# =============================================================================
# 性能和边界测试
# =============================================================================


class TestPerformanceAndEdgeCases:
    """性能和边界测试"""

    def test_empty_module(self):
        """测试空模块"""
        module = MockModule()
        pm = PassManager(module, OptimizationLevel.O2)

        # 运行优化
        result = pm.run()
        assert result is module

    def test_module_with_no_functions(self):
        """测试没有函数的模块"""
        module = MockModule()
        pm = PassManager(module, OptimizationLevel.O2)

        # 运行优化
        result = pm.run()
        assert result is module

    def test_large_pipeline(self):
        """测试大型管道"""
        module = create_test_module()
        pm = PassManager(module, OptimizationLevel.O3)

        # O3有更多Pass
        assert len(pm.pipeline.passes) > 10

        # 运行优化
        result = pm.run()
        assert result is module


# =============================================================================
# 运行测试
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

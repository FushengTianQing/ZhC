# -*- coding: utf-8 -*-
"""
ZhC Pass 管理器

管理优化 Pass 的执行流程，协调 Pass 之间的依赖关系。

核心功能：
- Pass 管道执行
- 依赖管理
- 分析结果缓存
- 错误恢复

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable, Set
from enum import Enum
import logging
import time

from zhc.optimization.optimization_levels import OptimizationLevel
from zhc.optimization.pass_config import (
    PassPipeline,
    StandardPassConfig,
)
from zhc.optimization.pass_registry import (
    PassRegistry,
    PassType,
    PassInfo,
    PassResult,
)

logger = logging.getLogger(__name__)


class PassState(Enum):
    """Pass 执行状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PassExecution:
    """Pass 执行记录"""

    name: str
    state: PassState = PassState.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[PassResult] = None

    @property
    def duration_ms(self) -> float:
        """执行耗时（毫秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0


class AnalysisCache:
    """分析结果缓存"""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._invalidated: Set[str] = set()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存的分析结果"""
        if key in self._invalidated:
            return None
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """设置缓存的分析结果"""
        if key not in self._invalidated:
            self._cache[key] = value

    def invalidate(self, key: str) -> None:
        """使缓存失效"""
        self._invalidated.add(key)

    def invalidate_all(self) -> None:
        """使所有缓存失效"""
        self._invalidated.update(self._cache.keys())

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._invalidated.clear()


class PassManager:
    """
    Pass 管理器

    管理优化 Pass 的执行，包括：
    - Pass 管道构建
    - Pass 顺序执行
    - 依赖管理
    - 分析结果缓存
    - 错误处理

    使用方式：
        # 基本用法
        pm = PassManager(module, OptimizationLevel.O2)
        optimized_module = pm.run()

        # 自定义管道
        pm = PassManager(module)
        pm.add_pass("inline", threshold=128)
        pm.add_pass("dce")
        optimized_module = pm.run()

        # 获取优化统计
        stats = pm.get_stats()
        print(stats)
    """

    def __init__(
        self,
        module: Optional[Any] = None,
        level: OptimizationLevel = OptimizationLevel.O2,
    ):
        """
        初始化 Pass 管理器

        Args:
            module: LLVM 模块（ll.Module）
            level: 优化级别
        """
        self.module = module
        self.level = level
        self.pipeline: PassPipeline = StandardPassConfig.create_pipeline(level)
        self.analysis_cache = AnalysisCache()
        self.executions: Dict[str, PassExecution] = {}
        self.observers: List[Callable] = []
        self._running = False
        self._initialize_passes()

    def _initialize_passes(self) -> None:
        """初始化内置 Pass 注册"""
        # 注册标准 Pass（如果尚未注册）
        self._register_standard_passes()

    def _register_standard_passes(self) -> None:
        """注册标准 Pass"""
        standard_passes = [
            (
                "no-op",
                PassType.UTILITY,
                "无操作 Pass，用于占位",
            ),
            (
                "verify",
                PassType.UTILITY,
                "验证 IR 正确性",
            ),
            (
                "inline",
                PassType.TRANSFORM,
                "函数内联",
                ["mem2reg"],
                ["dce", "gvn"],
            ),
            (
                "mem2reg",
                PassType.TRANSFORM,
                "内存到寄存器提升",
            ),
            (
                "early-cse",
                PassType.TRANSFORM,
                "早期公共子表达式消除",
                [],
                ["gvn"],
            ),
            (
                "gvn",
                PassType.TRANSFORM,
                "全局值编号",
                ["mem2reg"],
            ),
            (
                "dce",
                PassType.TRANSFORM,
                "死代码消除",
            ),
            (
                "adce",
                PassType.TRANSFORM,
                "主动死代码消除",
            ),
            (
                "sccp",
                PassType.TRANSFORM,
                "稀疏条件常量传播",
                ["mem2reg"],
            ),
            (
                "simplifycfg",
                PassType.TRANSFORM,
                "简化控制流",
            ),
            (
                "mergeret",
                PassType.TRANSFORM,
                "合并 return",
            ),
            (
                "reassociate",
                PassType.TRANSFORM,
                "重结合",
            ),
            (
                "loop-rotate",
                PassType.TRANSFORM,
                "循环旋转",
            ),
            (
                "licm",
                PassType.TRANSFORM,
                "循环不变代码移动",
                ["loop-rotate"],
            ),
            (
                "loop-unswitch",
                PassType.TRANSFORM,
                "循环条件转换",
            ),
            (
                "indvars",
                PassType.TRANSFORM,
                "归纳变量简化",
            ),
            (
                "loop-unroll",
                PassType.TRANSFORM,
                "循环展开",
            ),
            (
                "loop-vectorize",
                PassType.TRANSFORM,
                "循环向量化",
            ),
            (
                "slp-vectorize",
                PassType.TRANSFORM,
                "SLP 向量化",
            ),
            (
                "gvn-hoist",
                PassType.TRANSFORM,
                "GVN 提升",
            ),
            (
                "aggressive-dce",
                PassType.TRANSFORM,
                "激进死代码消除",
            ),
            (
                "function-attrs",
                PassType.ANALYSIS,
                "函数属性推断",
            ),
            (
                "mergefunc",
                PassType.TRANSFORM,
                "函数合并",
            ),
            (
                "constmerge",
                PassType.TRANSFORM,
                "常量合并",
            ),
            (
                "globalopt",
                PassType.TRANSFORM,
                "全局变量优化",
            ),
        ]

        for pass_def in standard_passes:
            name, pass_type, desc = pass_def[0], pass_def[1], pass_def[2]
            if PassRegistry.get_info(name) is None:
                required = pass_def[3] if len(pass_def) > 3 else []
                invalidated = pass_def[4] if len(pass_def) > 4 else []
                PassRegistry.register(
                    name=name,
                    pass_type=pass_type,
                    description=desc,
                    required_passes=required,
                    invalidated_passes=invalidated,
                )

    def set_module(self, module: Any) -> None:
        """设置要优化的模块"""
        self.module = module
        self.analysis_cache.clear()

    def set_level(self, level: OptimizationLevel) -> None:
        """设置优化级别"""
        self.level = level
        self.pipeline = StandardPassConfig.create_pipeline(level)

    def add_pass(self, name: str, **params) -> "PassManager":
        """
        添加 Pass 到管道

        Args:
            name: Pass 名称
            **params: Pass 参数

        Returns:
            self（支持链式调用）
        """
        self.pipeline.add_pass(name, **params)
        return self

    def remove_pass(self, name: str) -> bool:
        """
        从管道移除 Pass

        Args:
            name: Pass 名称

        Returns:
            是否成功移除
        """
        for i, p in enumerate(self.pipeline.passes):
            if p.name == name:
                self.pipeline.passes.pop(i)
                return True
        return False

    def disable_pass(self, name: str) -> None:
        """禁用指定的 Pass"""
        for p in self.pipeline.passes:
            if p.name == name:
                p.enabled = False

    def enable_pass(self, name: str) -> None:
        """启用指定的 Pass"""
        for p in self.pipeline.passes:
            if p.name == name:
                p.enabled = True

    def add_observer(self, observer: Callable) -> None:
        """添加优化观察器"""
        self.observers.append(observer)

    def remove_observer(self, observer: Callable) -> None:
        """移除优化观察器"""
        if observer in self.observers:
            self.observers.remove(observer)

    def run(self) -> Any:
        """
        执行优化管道

        Returns:
            优化后的模块
        """
        if self.module is None:
            raise ValueError("Module is not set")

        if self._running:
            raise RuntimeError("PassManager is already running")

        self._running = True
        start_time = time.time()

        try:
            # 获取要执行的 Pass 列表
            pass_names = self.pipeline.get_enabled_passes()

            # 拓扑排序确保依赖正确
            sorted_names = PassRegistry.topological_sort(pass_names)

            logger.info(f"Running optimization pipeline: {sorted_names}")

            # 执行每个 Pass
            for pass_name in sorted_names:
                self._run_pass(pass_name)

            # 通知观察器优化完成
            self._notify_completion()

            logger.info(
                f"Optimization completed in {(time.time() - start_time) * 1000:.2f}ms"
            )

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise

        finally:
            self._running = False

        return self.module

    def _run_pass(self, name: str) -> Optional[PassResult]:
        """
        执行单个 Pass

        Args:
            name: Pass 名称

        Returns:
            Pass 执行结果
        """
        # 创建执行记录
        execution = PassExecution(name=name)
        self.executions[name] = execution

        # 检查 Pass 是否存在
        info = PassRegistry.get_info(name)
        if info is None:
            logger.warning(f"Unknown pass: {name}, skipping")
            execution.state = PassState.SKIPPED
            return None

        # 检查依赖是否满足
        if not self._check_dependencies(info):
            logger.warning(f"Pass {name} dependencies not satisfied, skipping")
            execution.state = PassState.SKIPPED
            return None

        # 执行前使分析结果失效
        for invalidated in info.invalidated_passes:
            self.analysis_cache.invalidate(invalidated)

        # 创建 Pass 实例
        pass_instance = PassRegistry.create(name)
        if pass_instance is None:
            # 使用默认处理（pass-through）
            logger.debug(f"No implementation for pass {name}, treating as no-op")
            execution.state = PassState.COMPLETED
            return PassResult(pass_name=name, changed=False)

        # 开始执行
        execution.state = PassState.RUNNING
        execution.start_time = time.time()

        # 通知观察器
        self._notify_pass_start(name)

        try:
            # 执行 Pass
            if hasattr(pass_instance, "run"):
                changed = pass_instance.run(self.module)
            elif hasattr(pass_instance, "run_pass"):
                changed = pass_instance.run_pass(self.module)
            else:
                # 假设 Pass 直接修改模块
                changed = True

            # 完成执行
            execution.end_time = time.time()
            execution.state = PassState.COMPLETED

            result = PassResult(
                pass_name=name,
                changed=changed,
                time_ms=execution.duration_ms,
            )
            execution.result = result

            # 缓存分析结果
            if info.pass_type == PassType.ANALYSIS and changed:
                self.analysis_cache.set(name, changed)

            # 通知观察器
            self._notify_pass_complete(result)

            return result

        except Exception as e:
            execution.end_time = time.time()
            execution.state = PassState.FAILED

            result = PassResult(
                pass_name=name,
                changed=False,
                time_ms=execution.duration_ms,
                error=str(e),
            )
            execution.result = result

            # 通知观察器
            self._notify_pass_error(result)

            logger.error(f"Pass {name} failed: {e}")
            raise

    def _check_dependencies(self, info: PassInfo) -> bool:
        """检查 Pass 依赖是否满足"""
        for dep in info.required_passes:
            if dep not in self.executions:
                return False
            if self.executions[dep].state != PassState.COMPLETED:
                return False
        return True

    def _notify_pass_start(self, pass_name: str) -> None:
        """通知观察器 Pass 开始"""
        for observer in self.observers:
            try:
                observer.on_pass_start(pass_name, self.module)
            except Exception as e:
                logger.warning(f"Observer error in on_pass_start: {e}")

    def _notify_pass_complete(self, result: PassResult) -> None:
        """通知观察器 Pass 完成"""
        for observer in self.observers:
            try:
                observer.on_pass_complete(result, self.module)
            except Exception as e:
                logger.warning(f"Observer error in on_pass_complete: {e}")

    def _notify_pass_error(self, result: PassResult) -> None:
        """通知观察器 Pass 出错"""
        for observer in self.observers:
            try:
                if hasattr(observer, "on_pass_error"):
                    observer.on_pass_error(result)
            except Exception as e:
                logger.warning(f"Observer error in on_pass_error: {e}")

    def _notify_completion(self) -> None:
        """通知观察器优化完成"""
        for observer in self.observers:
            try:
                observer.on_optimization_complete(self.module, self.executions)
            except Exception as e:
                logger.warning(f"Observer error in on_optimization_complete: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取优化统计信息

        Returns:
            统计信息字典
        """
        total_time = sum(e.duration_ms for e in self.executions.values())
        completed = sum(
            1 for e in self.executions.values() if e.state == PassState.COMPLETED
        )
        failed = sum(1 for e in self.executions.values() if e.state == PassState.FAILED)
        skipped = sum(
            1 for e in self.executions.values() if e.state == PassState.SKIPPED
        )
        changed = sum(
            1 for e in self.executions.values() if e.result and e.result.changed
        )

        return {
            "total_time_ms": total_time,
            "total_passes": len(self.executions),
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "changed": changed,
            "level": self.level.name,
            "passes": [
                {
                    "name": name,
                    "state": exec.state.value,
                    "duration_ms": exec.duration_ms,
                    "changed": exec.result.changed if exec.result else False,
                }
                for name, exec in self.executions.items()
            ],
        }

    def get_execution_order(self) -> List[str]:
        """获取 Pass 执行顺序"""
        return list(self.executions.keys())


class OptimizationPipeline:
    """
    优化管道构建器

    提供流畅的 API 来构建自定义优化管道。

    使用方式：
        pipeline = (
            OptimizationPipeline()
            .with_level(OptimizationLevel.O2)
            .add("inline", threshold=128)
            .remove("loop-vectorize")
            .add_after("inline", "dce")
            .run(module)
        )
    """

    def __init__(self, module: Optional[Any] = None):
        self._module = module
        self._level = OptimizationLevel.O2
        self._adds: List[str] = []
        self._removes: Set[str] = set()
        self._modifies: Dict[str, Dict] = {}

    def with_level(self, level: OptimizationLevel) -> "OptimizationPipeline":
        """设置优化级别"""
        self._level = level
        return self

    def add(self, pass_name: str, **params) -> "OptimizationPipeline":
        """添加 Pass"""
        self._adds.append(pass_name)
        if params:
            self._modifies[pass_name] = params
        return self

    def remove(self, pass_name: str) -> "OptimizationPipeline":
        """移除 Pass"""
        self._removes.add(pass_name)
        return self

    def add_after(
        self, after_pass: str, pass_name: str, **params
    ) -> "OptimizationPipeline":
        """在指定 Pass 之后添加 Pass"""
        self._adds.append(f"{after_pass}+{pass_name}")
        if params:
            self._modifies[pass_name] = params
        return self

    def modify(self, pass_name: str, **params) -> "OptimizationPipeline":
        """修改 Pass 参数"""
        self._modifies[pass_name] = params
        return self

    def run(self, module: Optional[Any] = None) -> Any:
        """执行优化管道"""
        if module is not None:
            self._module = module

        if self._module is None:
            raise ValueError("Module is not set")

        # 创建 Pass 管理器
        pm = PassManager(self._module, self._level)

        # 应用修改
        for pass_name in self._removes:
            pm.remove_pass(pass_name)

        for pass_name in self._adds:
            if "+" not in pass_name:
                params = self._modifies.get(pass_name, {})
                pm.add_pass(pass_name, **params)

        return pm.run()

    def build(self) -> PassManager:
        """构建 Pass 管理器（但不执行）"""
        pm = PassManager(self._module, self._level)

        for pass_name in self._removes:
            pm.remove_pass(pass_name)

        for pass_name in self._adds:
            if "+" not in pass_name:
                params = self._modifies.get(pass_name, {})
                pm.add_pass(pass_name, **params)

        return pm

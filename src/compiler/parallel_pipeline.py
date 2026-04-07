#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并行编译流水线 - Parallel Compilation Pipeline

功能：
1. 利用多核CPU加速编译
2. 按依赖层级并行编译
3. 支持线程池和进程池
4. 动态负载均衡

性能优化：
- 模块间依赖解析后可并行编译
- 同一层级的模块并行处理
- 使用Future跟踪编译进度
- 自动检测CPU核心数

作者：远
日期：2026-04-03
"""

import os
import time
import hashlib
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import threading

# 导入现有编译流水线
from .pipeline import CompilationPipeline


class ParallelStrategy(Enum):
    """并行策略"""
    THREAD = "thread"           # 线程池（适合I/O密集型）
    PROCESS = "process"          # 进程池（适合CPU密集型）
    AUTO = "auto"               # 自动选择


@dataclass
class ModuleInfo:
    """模块信息"""
    name: str
    file_path: str
    dependencies: List[str] = field(default_factory=list)
    level: int = 0  # 编译层级
    priority: int = 0  # 优先级
    size: int = 0  # 文件大小（字节）
    compile_time: float = 0.0  # 预计编译时间


@dataclass
class CompilationResult:
    """编译结果"""
    module_name: str
    success: bool
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    compile_time: float = 0.0
    cached: bool = False


@dataclass
class ParallelStats:
    """并行编译统计"""
    total_modules: int = 0
    cached_modules: int = 0
    parallel_modules: int = 0
    total_time: float = 0.0
    speedup: float = 0.0
    cpu_utilization: float = 0.0
    level_distribution: Dict[int, int] = field(default_factory=dict)


class CompilationLayerCalculator:
    """编译层级计算器

    使用改进的Kahn算法计算模块的编译层级:
    - Level 0: 无依赖的模块
    - Level N: 依赖模块的最高层级 + 1
    """

    def __init__(self):
        self.module_levels: Dict[str, int] = {}
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_graph: Dict[str, Set[str]] = defaultdict(set)

    def add_module(self, module_name: str, dependencies: List[str]):
        """添加模块及其依赖"""
        self.dependency_graph[module_name] = set(dependencies)
        for dep in dependencies:
            self.reverse_graph[dep].add(module_name)

    def compute_levels(self) -> Dict[str, int]:
        """
        计算所有模块的编译层级

        Returns:
            模块名 -> 层级 的字典
        """
        # 找出所有入度为0的节点（无依赖的模块）
        in_degree = {m: len(deps) for m, deps in self.dependency_graph.items()}
        zero_degree = [m for m, d in in_degree.items() if d == 0]

        # BFS计算层级
        while zero_degree:
            current = zero_degree.pop(0)
            current_level = self.module_levels.get(current, 0)

            # 更新当前模块的层级
            self.module_levels[current] = current_level

            # 处理当前模块的后继节点
            for successor in self.reverse_graph[current]:
                in_degree[successor] -= 1

                # 更新后继节点的层级
                successor_level = current_level + 1
                if successor_level > self.module_levels.get(successor, 0):
                    self.module_levels[successor] = successor_level

                # 如果入度变为0，加入队列
                if in_degree[successor] == 0:
                    zero_degree.append(successor)

        # 处理孤立的模块（没有依赖也没有被依赖）
        for module in self.dependency_graph:
            if module not in self.module_levels:
                self.module_levels[module] = 0

        return self.module_levels

    def get_layers(self) -> List[List[str]]:
        """
        获取分层的模块列表

        Returns:
            按层级分组的模块列表 [[level0_modules], [level1_modules], ...]
        """
        levels = self.compute_levels()

        # 按层级分组
        layers = defaultdict(list)
        for module, level in levels.items():
            layers[level].append(module)

        # 转换为列表
        return [layers[i] for i in sorted(layers.keys())]


class ParallelCompilationPipeline:
    """并行编译流水线

    核心策略：
    1. 使用依赖分析确定编译顺序
    2. 按编译层级分组
    3. 同一层级的模块并行编译
    4. 使用线程池或进程池执行
    """

    def __init__(
        self,
        max_workers: int = None,
        strategy: ParallelStrategy = ParallelStrategy.AUTO,
        enable_cache: bool = True
    ):
        """
        初始化并行编译流水线

        Args:
            max_workers: 最大工作线程数（默认=CPU核心数）
            strategy: 并行策略
            enable_cache: 是否启用缓存
        """
        # 自动选择最佳工作线程数
        if max_workers is None:
            self.max_workers = os.cpu_count() or 4
        else:
            self.max_workers = max_workers

        # 选择并行策略
        if strategy == ParallelStrategy.AUTO:
            # 默认使用进程池（适合CPU密集型）
            self.strategy = ParallelStrategy.PROCESS
        else:
            self.strategy = strategy

        # 创建执行器
        self._create_executor()

        # 初始化底层编译流水线
        self.base_pipeline = CompilationPipeline(enable_cache=enable_cache)

        # 线程锁（用于线程安全）
        self._lock = threading.Lock()

        # 模块信息
        self.modules: Dict[str, ModuleInfo] = {}

        # 统计信息
        self.stats = ParallelStats()

        # 编译层级计算器
        self.layer_calculator = CompilationLayerCalculator()

    def _create_executor(self):
        """创建执行器"""
        if self.strategy == ParallelStrategy.THREAD:
            self.executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix="zhc_parallel"
            )
            self._executor_type = "thread"
        else:
            self.executor = concurrent.futures.ProcessPoolExecutor(
                max_workers=self.max_workers
            )
            self._executor_type = "process"

    def add_module(
        self,
        module_name: str,
        file_path: str,
        dependencies: List[str] = None
    ):
        """
        添加模块

        Args:
            module_name: 模块名
            file_path: 文件路径
            dependencies: 依赖列表
        """
        dependencies = dependencies or []

        # 获取文件大小
        file_size = 0
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)

        module_info = ModuleInfo(
            name=module_name,
            file_path=file_path,
            dependencies=dependencies,
            size=file_size,
            priority=0
        )

        with self._lock:
            self.modules[module_name] = module_info
            self.layer_calculator.add_module(module_name, dependencies)

    def _compile_single_module(
        self,
        module_name: str,
        force: bool = False
    ) -> CompilationResult:
        """
        编译单个模块

        Args:
            module_name: 模块名
            force: 是否强制重新编译

        Returns:
            编译结果
        """
        if module_name not in self.modules:
            return CompilationResult(
                module_name=module_name,
                success=False,
                error_message=f"模块不存在: {module_name}"
            )

        module_info = self.modules[module_name]
        start_time = time.time()

        try:
            # 检查缓存
            if not force:
                cache_key = self._get_cache_key(module_info.file_path)
                cached = self._get_from_cache(cache_key)
                if cached:
                    return CompilationResult(
                        module_name=module_name,
                        success=True,
                        output_path=cached.get('output_path'),
                        compile_time=time.time() - start_time,
                        cached=True
                    )

            # 使用底层流水线编译
            filepath = Path(module_info.file_path)
            result = self.base_pipeline.process_file(filepath)

            if result:
                compile_time = time.time() - start_time

                # 保存到缓存
                if self.base_pipeline.enable_cache:
                    self._save_to_cache(
                        self._get_cache_key(module_info.file_path),
                        {
                            'output_path': str(result.get('c_filepath', '')),
                            'module_name': module_name
                        }
                    )

                return CompilationResult(
                    module_name=module_name,
                    success=True,
                    output_path=str(result.get('c_filepath', '')),
                    compile_time=compile_time
                )
            else:
                return CompilationResult(
                    module_name=module_name,
                    success=False,
                    error_message="编译失败",
                    compile_time=time.time() - start_time
                )

        except Exception as e:
            return CompilationResult(
                module_name=module_name,
                success=False,
                error_message=str(e),
                compile_time=time.time() - start_time
            )

    def _compile_layer_parallel(
        self,
        layer_modules: List[str],
        force: bool = False
    ) -> Dict[str, CompilationResult]:
        """
        并行编译同一层级的模块

        Args:
            layer_modules: 同层级的模块列表
            force: 是否强制重新编译

        Returns:
            模块名 -> 编译结果 的字典
        """
        results = {}

        # 提交所有任务
        futures = {}
        for module_name in layer_modules:
            future = self.executor.submit(
                self._compile_single_module,
                module_name,
                force
            )
            futures[future] = module_name

        # 等待所有任务完成
        for future in concurrent.futures.as_completed(futures):
            module_name = futures[future]
            try:
                results[module_name] = future.result()
            except Exception as e:
                results[module_name] = CompilationResult(
                    module_name=module_name,
                    success=False,
                    error_message=str(e)
                )

        return results

    def compile_parallel(
        self,
        force: bool = False,
        show_progress: bool = True
    ) -> Dict[str, CompilationResult]:
        """
        并行编译所有模块

        Args:
            force: 是否强制重新编译
            show_progress: 是否显示进度

        Returns:
            模块名 -> 编译结果 的字典
        """
        if not self.modules:
            return {}

        start_time = time.time()
        all_results = {}

        # 计算编译层级
        layers = self.layer_calculator.get_layers()

        if show_progress:
            print(f"📊 并行编译计划:")
            print(f"   工作线程: {self.max_workers} ({self._executor_type})")
            print(f"   模块总数: {len(self.modules)}")
            print(f"   编译层级: {len(layers)}")
            for i, layer in enumerate(layers):
                print(f"   Level {i}: {len(layer)} 个模块")
            print()

        # 按层级编译
        total_modules = len(self.modules)
        compiled_modules = 0

        for level, layer_modules in enumerate(layers):
            if show_progress:
                print(f"🔄 编译 Level {level} ({len(layer_modules)} 个模块)...")

            level_start = time.time()

            # 并行编译当前层级
            level_results = self._compile_layer_parallel(layer_modules, force)
            all_results.update(level_results)

            level_time = time.time() - level_start
            compiled_modules += len(layer_modules)

            if show_progress:
                success_count = sum(1 for r in level_results.values() if r.success)
                print(f"   完成: {success_count}/{len(layer_modules)} "
                      f"({level_time:.2f}s)")

        # 统计
        total_time = time.time() - start_time
        self.stats.total_modules = total_modules
        self.stats.cached_modules = sum(1 for r in all_results.values() if r.cached)
        self.stats.total_time = total_time

        # 计算加速比（与串行编译对比）
        serial_time = sum(r.compile_time for r in all_results.values())
        if total_time > 0:
            self.stats.speedup = serial_time / total_time

        # CPU利用率
        if total_time > 0 and self.max_workers > 0:
            ideal_time = serial_time / self.max_workers
            self.stats.cpu_utilization = ideal_time / total_time * 100

        if show_progress:
            self._print_stats()

        return all_results

    def compile_sequential(self) -> Dict[str, CompilationResult]:
        """
        串行编译（用于对比）

        Returns:
            模块名 -> 编译结果 的字典
        """
        results = {}
        layers = self.layer_calculator.get_layers()

        for layer_modules in layers:
            for module_name in layer_modules:
                results[module_name] = self._compile_single_module(module_name)

        return results

    def _get_cache_key(self, file_path: str) -> str:
        """获取缓存键"""
        file_hash = hashlib.md5(file_path.encode()).hexdigest()
        return f"parallel_compile_{file_hash}"

    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """从缓存获取"""
        return self.base_pipeline._get_from_cache(cache_key)

    def _save_to_cache(self, cache_key: str, data: Dict):
        """保存到缓存"""
        self.base_pipeline._save_to_cache(cache_key, data)

    def _print_stats(self):
        """打印统计信息"""
        print()
        print("=" * 60)
        print("并行编译统计")
        print("=" * 60)
        print(f"  总模块数: {self.stats.total_modules}")
        print(f"  缓存命中: {self.stats.cached_modules}")
        print(f"  总耗时: {self.stats.total_time:.2f}s")
        print(f"  加速比: {self.stats.speedup:.2f}x")
        print(f"  CPU利用率: {self.stats.cpu_utilization:.1f}%")
        print(f"  工作线程: {self.max_workers}")
        print("=" * 60)

    def get_stats_report(self) -> str:
        """生成统计报告"""
        lines = [
            "=" * 60,
            "并行编译统计报告",
            "=" * 60,
            "",
            f"执行器类型: {self._executor_type}",
            f"工作线程数: {self.max_workers}",
            "",
            f"总模块数: {self.stats.total_modules}",
            f"缓存命中: {self.stats.cached_modules}",
            f"并行编译: {self.stats.parallel_modules}",
            "",
            f"总耗时: {self.stats.total_time:.2f}s",
            f"加速比: {self.stats.speedup:.2f}x",
            f"CPU利用率: {self.stats.cpu_utilization:.1f}%",
            "",
            "编译层级分布:",
        ]

        for level, count in sorted(self.stats.level_distribution.items()):
            lines.append(f"  Level {level}: {count} 个模块")

        lines.extend(["", "=" * 60])
        return "\n".join(lines)

    def shutdown(self):
        """关闭执行器"""
        self.executor.shutdown(wait=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


class AdaptiveParallelPipeline(ParallelCompilationPipeline):
    """
    自适应并行编译流水线

    特性：
    1. 根据系统负载动态调整工作线程数
    2. 根据模块大小调整优先级
    3. 支持热模块（频繁编译）加速
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 模块编译频率统计
        self.compile_frequency: Dict[str, int] = defaultdict(int)

        # 热点模块（编译频率高的模块）
        self.hot_modules: Set[str] = set()

        # 锁
        self._freq_lock = threading.Lock()

    def add_module(self, module_name: str, file_path: str, dependencies: List[str] = None):
        """添加模块（带频率统计）"""
        super().add_module(module_name, file_path, dependencies)

        # 更新编译频率
        with self._freq_lock:
            self.compile_frequency[module_name] += 1

            # 更新热点模块
            if self.compile_frequency[module_name] > 3:
                self.hot_modules.add(module_name)

    def _compute_module_priority(self, module_name: str) -> int:
        """
        计算模块优先级

        优先级因素：
        1. 编译频率（越频繁优先级越高）
        2. 文件大小（越小优先级越高）
        3. 依赖数量（越少优先级越高）
        """
        if module_name not in self.modules:
            return 0

        module = self.modules[module_name]

        # 编译频率分数
        freq_score = min(self.compile_frequency.get(module_name, 0) * 10, 50)

        # 文件大小分数（越小越高）
        size_score = max(0, 100 - module.size // 1024)

        # 依赖数量分数（越少越高）
        dep_score = max(0, 50 - len(module.dependencies) * 10)

        # 是否是热点模块
        hot_score = 20 if module_name in self.hot_modules else 0

        return freq_score + size_score + dep_score + hot_score

    def _sort_layer_by_priority(self, layer_modules: List[str]) -> List[str]:
        """
        按优先级排序同层级的模块

        Args:
            layer_modules: 同层级的模块列表

        Returns:
            按优先级排序的模块列表
        """
        return sorted(
            layer_modules,
            key=lambda m: self._compute_module_priority(m),
            reverse=True
        )

    def compile_parallel_adaptive(
        self,
        force: bool = False,
        show_progress: bool = True
    ) -> Dict[str, CompilationResult]:
        """
        自适应并行编译

        Args:
            force: 是否强制重新编译
            show_progress: 是否显示进度

        Returns:
            模块名 -> 编译结果 的字典
        """
        if not self.modules:
            return {}

        start_time = time.time()
        all_results = {}

        # 计算编译层级
        layers = self.layer_calculator.get_layers()

        if show_progress:
            print(f"📊 自适应并行编译计划:")
            print(f"   工作线程: {self.max_workers} ({self._executor_type})")
            print(f"   模块总数: {len(self.modules)}")
            print(f"   热点模块: {len(self.hot_modules)}")
            print(f"   编译层级: {len(layers)}")
            print()

        # 按层级编译
        for level, layer_modules in enumerate(layers):
            if show_progress:
                print(f"🔄 编译 Level {level} ({len(layer_modules)} 个模块)...")

            # 按优先级排序
            sorted_modules = self._sort_layer_by_priority(layer_modules)

            level_start = time.time()
            level_results = self._compile_layer_parallel(sorted_modules, force)
            all_results.update(level_results)

            level_time = time.time() - level_start

            if show_progress:
                success_count = sum(1 for r in level_results.values() if r.success)
                print(f"   完成: {success_count}/{len(layer_modules)} "
                      f"({level_time:.2f}s)")

        # 更新统计
        total_time = time.time() - start_time
        self.stats.total_modules = len(self.modules)
        self.stats.total_time = total_time

        if show_progress:
            self._print_stats()

        return all_results


# 兼容性别名
ParallelPipeline = ParallelCompilationPipeline
AdaptivePipeline = AdaptiveParallelPipeline
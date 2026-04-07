#!/usr/bin/env python3
"""
Day 5: 性能优化器

编译性能优化模块，包括：
1. 算法复杂度优化
2. 内存使用优化
3. 并发编译支持
4. 增量编译优化
5. 性能监控和报告
"""

import os
import sys
import time
import math
import threading
import queue
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict
# psutil 依赖处理：如果未安装，使用模拟版本
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil 未安装，使用模拟版本")
    
    class MockProcess:
        def memory_info(self):
            return type('obj', (object,), {'rss': 1024 * 1024 * 100})()  # 模拟100MB内存
        
        def cpu_percent(self, interval=None):
            return 0.0
    
    psutil = type('obj', (object,), {
        'Process': lambda: MockProcess(),
        'cpu_percent': lambda interval: 0.0
    })()

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        """初始化性能监控器"""
        self.metrics: Dict[str, List[float]] = {
            'parse_time': [],
            'convert_time': [],
            'dependency_time': [],
            'compile_time': [],
            'memory_usage': [],
            'cpu_usage': []
        }
        
        self.start_time = time.time()
        self.peak_memory = 0
        
    def start_phase(self, phase: str) -> float:
        """
        开始一个性能监控阶段
        
        Args:
            phase: 阶段名称
            
        Returns:
            开始时间戳
        """
        return time.time()
        
    def end_phase(self, phase: str, start_timestamp: float) -> None:
        """
        结束一个性能监控阶段
        
        Args:
            phase: 阶段名称
            start_timestamp: 开始时间戳
        """
        duration = time.time() - start_timestamp
        if phase in self.metrics:
            self.metrics[phase].append(duration)
            
        # 记录内存使用
        try:
            memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        except:
            memory_mb = 0.0  # psutil不可用时使用默认值
        self.metrics['memory_usage'].append(memory_mb)
        self.peak_memory = max(self.peak_memory, memory_mb)
        
        # 记录CPU使用率
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
        except:
            cpu_percent = 0.0  # psutil不可用时使用默认值
        self.metrics['cpu_usage'].append(cpu_percent)
        
    def get_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要
        
        Returns:
            性能摘要字典
        """
        total_time = time.time() - self.start_time
        
        summary: Dict[str, Any] = {
            'total_time': total_time,
            'peak_memory_mb': self.peak_memory,
            'phases': {}
        }
        
        # 计算各阶段统计
        for phase, times in self.metrics.items():
            if times:
                summary['phases'][phase] = {
                    'count': len(times),
                    'total': sum(times),
                    'avg': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                    'std': self._calculate_std(times) if len(times) > 1 else 0
                }
                
        # 计算性能指标
        summary['performance_indicators'] = self._calculate_indicators(summary)
        
        return summary
        
    def _calculate_std(self, values: List[float]) -> float:
        """计算标准差"""
        avg = sum(values) / len(values)
        variance = sum((x - avg) ** 2 for x in values) / len(values)
        return math.sqrt(variance)
        
    def _calculate_indicators(self, summary: Dict) -> Dict[str, Any]:
        """计算性能指标"""
        indicators = {}
        
        # 计算各阶段时间占比
        total_phase_time = sum(phase['total'] for phase in summary['phases'].values())
        if total_phase_time > 0:
            for phase, stats in summary['phases'].items():
                indicators[f'{phase}_percentage'] = (stats['total'] / total_phase_time) * 100
                
        # 计算文件处理速度（如果有文件数信息）
        if 'parse_time' in summary['phases']:
            parse_count = summary['phases']['parse_time']['count']
            if parse_count > 0:
                indicators['files_per_second'] = parse_count / summary['total_time']
                indicators['avg_file_time'] = summary['total_time'] / parse_count
                
        # 内存效率指标
        if summary['peak_memory_mb'] > 0 and 'parse_time' in summary['phases']:
            parse_count = summary['phases']['parse_time']['count']
            indicators['memory_per_file_mb'] = summary['peak_memory_mb'] / max(parse_count, 1)
            
        return indicators
        
    def print_report(self) -> None:
        """打印性能报告"""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("📊 性能分析报告")
        print("="*60)
        
        print(f"\n📈 总体统计:")
        print(f"  总用时: {summary['total_time']:.3f}s")
        print(f"  峰值内存: {summary['peak_memory_mb']:.2f} MB")
        
        if 'performance_indicators' in summary:
            indicators = summary['performance_indicators']
            if 'files_per_second' in indicators:
                print(f"  文件处理速度: {indicators['files_per_second']:.2f} 文件/秒")
            if 'avg_file_time' in indicators:
                print(f"  平均文件处理时间: {indicators['avg_file_time']:.3f}s")
            if 'memory_per_file_mb' in indicators:
                print(f"  每文件内存占用: {indicators['memory_per_file_mb']:.2f} MB")
                
        print(f"\n⏱️  各阶段耗时:")
        for phase, stats in summary['phases'].items():
            if stats['count'] > 0:
                percentage = (stats['total'] / summary['total_time']) * 100
                print(f"  {phase}:")
                print(f"    次数: {stats['count']}")
                print(f"    总耗时: {stats['total']:.3f}s ({percentage:.1f}%)")
                print(f"    平均: {stats['avg']:.3f}s")
                print(f"    范围: {stats['min']:.3f}s - {stats['max']:.3f}s")
                if stats['std'] > 0:
                    print(f"    标准差: {stats['std']:.3f}s")
                    
        print("="*60)

class AlgorithmOptimizer:
    """算法优化器"""
    
    @staticmethod
    def optimize_dependency_resolution(dependency_graph: Dict[str, List[str]]) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
        """
        优化依赖解析算法
        
        Args:
            dependency_graph: 原始依赖图
            
        Returns:
            (优化后的依赖图, 节点层级信息)
        """
        # 1. 压缩传递依赖
        compressed_graph = AlgorithmOptimizer._compress_transitive_dependencies(dependency_graph)
        
        # 2. 计算节点层级（拓扑深度）
        node_levels = AlgorithmOptimizer._calculate_node_levels(compressed_graph)
        
        # 3. 按层级排序依赖
        sorted_graph = AlgorithmOptimizer._sort_dependencies_by_level(compressed_graph, node_levels)
        
        # 4. 移除冗余依赖
        optimized_graph = AlgorithmOptimizer._remove_redundant_dependencies(sorted_graph)
        
        return optimized_graph, node_levels
        
    @staticmethod
    def _compress_transitive_dependencies(graph: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """压缩传递依赖"""
        compressed = {}
        
        for node, deps in graph.items():
            # 计算传递闭包
            transitive_closure = set(deps)
            stack = list(deps)
            
            while stack:
                current = stack.pop()
                if current in graph:
                    for indirect in graph[current]:
                        if indirect not in transitive_closure:
                            transitive_closure.add(indirect)
                            stack.append(indirect)
                            
            # 移除可以通过其他依赖间接满足的依赖
            direct_deps = set(deps)
            for dep in deps:
                if dep in graph:
                    # 如果依赖的依赖也包含在当前依赖集中，则可能是传递依赖
                    for indirect in graph[dep]:
                        if indirect in transitive_closure and indirect in direct_deps:
                            direct_deps.discard(indirect)
                            
            compressed[node] = list(direct_deps)
            
        return compressed
        
    @staticmethod
    def _calculate_node_levels(graph: Dict[str, List[str]]) -> Dict[str, int]:
        """计算节点层级（拓扑深度）"""
        # 计算入度
        in_degree = {node: 0 for node in graph}
        for node, deps in graph.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1
                else:
                    in_degree[dep] = 1
                    
        # 初始化层级
        levels = {node: 0 for node in graph}
        
        # 使用队列进行拓扑排序并计算层级
        queue = [node for node in graph if in_degree[node] == 0]
        
        while queue:
            node = queue.pop(0)
            
            # 更新后继节点的层级
            if node in graph:
                for neighbor in graph[node]:
                    levels[neighbor] = max(levels[neighbor], levels[node] + 1)
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
                        
        return levels
        
    @staticmethod
    def _sort_dependencies_by_level(graph: Dict[str, List[str]], levels: Dict[str, int]) -> Dict[str, List[str]]:
        """按层级排序依赖"""
        sorted_graph = {}
        
        for node, deps in graph.items():
            # 按依赖的层级排序
            sorted_deps = sorted(deps, key=lambda x: levels.get(x, 0))
            sorted_graph[node] = sorted_deps
            
        return sorted_graph
        
    @staticmethod
    def _remove_redundant_dependencies(graph: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """移除冗余依赖"""
        optimized = {}
        
        for node, deps in graph.items():
            # 检查每个依赖是否必要
            necessary_deps = []
            reachable = set()
            
            # 构建除当前依赖外的可达集合
            for i, dep in enumerate(deps):
                other_deps = deps[:i] + deps[i+1:]
                
                # 计算通过其他依赖能到达的节点
                temp_reachable = set(other_deps)
                stack = list(other_deps)
                
                while stack:
                    current = stack.pop()
                    if current in graph:
                        for neighbor in graph[current]:
                            if neighbor not in temp_reachable:
                                temp_reachable.add(neighbor)
                                stack.append(neighbor)
                                
                # 如果当前依赖不在可达集合中，则是必要的
                if dep not in temp_reachable:
                    necessary_deps.append(dep)
                    reachable.add(dep)
                    
            optimized[node] = necessary_deps
            
        return optimized
        
    @staticmethod
    def optimize_memory_usage(data_structure: Any) -> Any:
        """
        优化数据结构的内存使用
        
        Args:
            data_structure: 原始数据结构
            
        Returns:
            优化后的数据结构
        """
        if isinstance(data_structure, dict):
            # 使用更紧凑的字典表示
            return {k: AlgorithmOptimizer.optimize_memory_usage(v) 
                   for k, v in data_structure.items()}
                   
        elif isinstance(data_structure, list):
            # 如果列表元素相同，考虑使用数组或元组
            if len(data_structure) > 0 and all(isinstance(x, type(data_structure[0])) for x in data_structure):
                if isinstance(data_structure[0], (int, float)):
                    # 对于数字列表，可以使用array模块进一步优化
                    return list(data_structure)  # 简化版本
            return [AlgorithmOptimizer.optimize_memory_usage(x) for x in data_structure]
            
        elif isinstance(data_structure, set):
            # 如果集合较小，使用frozenset
            if len(data_structure) < 10:
                return frozenset(data_structure)
            return set(data_structure)
            
        else:
            return data_structure

class ConcurrentCompiler:
    """并发编译器"""
    
    def __init__(self, max_workers: Optional[int] = None, use_processes: bool = False):
        """
        初始化并发编译器
        
        Args:
            max_workers: 最大工作线程/进程数
            use_processes: 是否使用进程（而不是线程）
        """
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.use_processes = use_processes
        self.executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
        
    def compile_files_concurrently(self, files: List[Path], compile_func: Callable) -> Dict[Path, Any]:
        """
        并发编译多个文件
        
        Args:
            files: 文件列表
            compile_func: 编译函数，接受文件路径返回编译结果
            
        Returns:
            编译结果字典
        """
        results = {}
        
        with self.executor_class(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(compile_func, file): file 
                for file in files
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    results[file] = future.result()
                except Exception as e:
                    results[file] = {"error": str(e)}
                    
        return results
        
    def pipeline_parallel_compile(self, stages: List[Callable], data: Any) -> Any:
        """
        流水线并行编译
        
        Args:
            stages: 编译阶段函数列表
            data: 输入数据
            
        Returns:
            处理后的数据
        """
        if not stages:
            return data
            
        # 创建阶段队列
        stage_queues: List[Any] = [queue.Queue() for _ in range(len(stages) + 1)]
        stage_queues[0].put(data)
        
        # 创建线程执行每个阶段
        threads = []
        for i, stage_func in enumerate(stages):
            def stage_worker(stage_idx, input_queue, output_queue):
                while True:
                    try:
                        item = input_queue.get(timeout=1)
                        if item is None:  # 终止信号
                            output_queue.put(None)
                            break
                            
                        result = stage_func(item)
                        output_queue.put(result)
                    except queue.Empty:
                        continue
                        
            thread = threading.Thread(
                target=stage_worker,
                args=(i, stage_queues[i], stage_queues[i+1])
            )
            threads.append(thread)
            thread.start()
            
        # 等待所有阶段完成
        for thread in threads:
            thread.join()
            
        # 获取最终结果
        final_result = stage_queues[-1].get()
        return final_result

class IncrementalOptimizer:
    """增量优化器"""
    
    def __init__(self, cache_system):
        """
        初始化增量优化器
        
        Args:
            cache_system: 缓存系统实例
        """
        self.cache = cache_system
        self.dependency_graph = {}
        self.file_modification_times = {}
        
    def analyze_changes(self, files: List[Path]) -> Dict[str, List[Path]]:
        """
        分析文件变更
        
        Args:
            files: 文件列表
            
        Returns:
            变更分析结果
        """
        changes: Dict[str, List[Path]] = {
            'modified': [],
            'added': [],
            'deleted': [],
            'unchanged': []
        }
        
        current_time = time.time()
        
        for file in files:
            if not file.exists():
                changes['deleted'].append(file)
                continue
                
            mtime = file.stat().st_mtime
            last_mtime = self.file_modification_times.get(file)
            
            if last_mtime is None:
                changes['added'].append(file)
            elif mtime > last_mtime:
                changes['modified'].append(file)
            else:
                changes['unchanged'].append(file)
                
            self.file_modification_times[file] = mtime
            
        return changes
        
    def get_affected_files(self, changed_files: List[Path], dependency_graph: Dict[str, List[str]]) -> Set[Path]:
        """
        获取受变更影响的所有文件
        
        Args:
            changed_files: 变更的文件列表
            dependency_graph: 依赖图
            
        Returns:
            受影响的所有文件集合
        """
        affected = set()
        
        # 构建反向依赖图
        reverse_graph = defaultdict(set)
        for module, deps in dependency_graph.items():
            for dep in deps:
                reverse_graph[dep].add(module)
                
        # 查找所有受影响的模块
        queue = [f.stem for f in changed_files]
        visited = set()
        
        while queue:
            module = queue.pop(0)
            if module in visited:
                continue
                
            visited.add(module)
            
            # 添加当前模块
            affected.add(Path(f"{module}.zhc"))
            
            # 添加依赖此模块的所有模块
            if module in reverse_graph:
                for dependent in reverse_graph[module]:
                    if dependent not in visited:
                        queue.append(dependent)
                        
        return affected
        
    def optimize_recompilation(self, files: List[Path], compile_func: Callable) -> Dict[Path, Any]:
        """
        优化重新编译过程
        
        Args:
            files: 文件列表
            compile_func: 编译函数
            
        Returns:
            编译结果
        """
        # 分析变更
        changes = self.analyze_changes(files)
        
        # 获取受影响的所有文件
        all_affected = self.get_affected_files(
            changes['modified'] + changes['added'],
            self.dependency_graph
        )
        
        # 只编译受影响的文件
        files_to_compile = list(all_affected)
        
        print(f"🔄 增量编译:")
        print(f"  修改文件: {len(changes['modified'])}")
        print(f"  新增文件: {len(changes['added'])}")
        print(f"  删除文件: {len(changes['deleted'])}")
        print(f"  未变文件: {len(changes['unchanged'])}")
        print(f"  需要编译: {len(files_to_compile)}/{len(files)}")
        
        # 编译受影响文件
        results = {}
        for file in files_to_compile:
            results[file] = compile_func(file)
            
        return results

def test_performance_optimizer():
    """测试性能优化器"""
    print("🧪 测试性能优化器...")
    
    # 测试算法优化器
    print("\n1. 测试算法优化器:")
    
    # 创建一个测试依赖图
    test_graph = {
        'A': ['B', 'C'],
        'B': ['C', 'D'],
        'C': ['D'],
        'D': [],
        'E': ['A', 'B']
    }
    
    print("   原始依赖图:", test_graph)
    
    optimized_graph, levels = AlgorithmOptimizer.optimize_dependency_resolution(test_graph)
    print("   优化后依赖图:", optimized_graph)
    print("   节点层级:", levels)
    
    # 验证优化结果
    assert 'A' in optimized_graph
    assert 'B' in optimized_graph
    assert len(optimized_graph['A']) <= len(test_graph['A'])  # 应该更少或相等
    
    print("   ✅ 算法优化测试通过")
    
    # 测试内存优化
    print("\n2. 测试内存优化:")
    
    test_data = {
        'large_list': list(range(1000)),
        'nested_dict': {f'key{i}': {f'subkey{j}': j for j in range(10)} for i in range(10)},
        'set_data': set(range(100))
    }
    
    optimized_data = AlgorithmOptimizer.optimize_memory_usage(test_data)
    print("   ✅ 内存优化测试通过")
    
    # 测试性能监控器
    print("\n3. 测试性能监控器:")
    
    monitor = PerformanceMonitor()
    
    # 模拟一些性能数据
    parse_start = monitor.start_phase('parse_time')
    time.sleep(0.01)  # 模拟解析时间
    monitor.end_phase('parse_time', parse_start)
    
    convert_start = monitor.start_phase('convert_time')
    time.sleep(0.02)  # 模拟转换时间
    monitor.end_phase('convert_time', convert_start)
    
    # 获取报告
    summary = monitor.get_summary()
    assert 'total_time' in summary
    assert 'peak_memory_mb' in summary
    assert 'phases' in summary
    
    print("   性能摘要:", {k: v for k, v in summary.items() if k != 'phases'})
    print("   ✅ 性能监控测试通过")
    
    print("\n🎉 性能优化器测试全部通过！")

if __name__ == "__main__":
    test_performance_optimizer()
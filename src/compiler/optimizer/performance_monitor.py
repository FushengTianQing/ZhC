# -*- coding: utf-8 -*-
"""
PerformanceMonitor: 性能监控器

提供编译各阶段的性能计时、内存/CPU监控和报告生成。
"""

import time
import math
from typing import Dict, List, Any

# psutil 依赖处理：如果未安装，使用模拟版本
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil 未安装，使用模拟版本")

    class MockProcess:
        def memory_info(self):
            return type('obj', (object,), {'rss': 1024 * 1024 * 100})()

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
            memory_mb = 0.0
        self.metrics['memory_usage'].append(memory_mb)
        self.peak_memory = max(self.peak_memory, memory_mb)

        # 记录CPU使用率
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
        except:
            cpu_percent = 0.0
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

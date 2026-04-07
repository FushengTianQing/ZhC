#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编译性能监控系统 - Compilation Performance Monitor

功能：
1. 编译各阶段性能计时
2. 内存使用监控
3. 性能数据收集和分析
4. 性能报告生成

作者：远
日期：2026-04-07
"""

import time
import math
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

# psutil 依赖处理
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    
    class MockProcess:
        def memory_info(self):
            return type('obj', (object,), {'rss': 1024 * 1024 * 100})()
        
        def cpu_percent(self, interval=None):
            return 0.0
    
    psutil = type('obj', (object,), {
        'Process': lambda: MockProcess(),
        'cpu_percent': lambda interval: 0.0
    })()


@dataclass
class PhaseMetrics:
    """编译阶段性能指标"""
    name: str
    start_time: float = 0.0
    end_time: float = 0.0
    memory_start: int = 0
    memory_end: int = 0
    cpu_percent: float = 0.0
    items_processed: int = 0
    
    @property
    def elapsed_ms(self) -> float:
        """耗时（毫秒）"""
        return (self.end_time - self.start_time) * 1000
    
    @property
    def elapsed_s(self) -> float:
        """耗时（秒）"""
        return self.end_time - self.start_time
    
    @property
    def memory_delta_mb(self) -> float:
        """内存变化（MB）"""
        return (self.memory_end - self.memory_start) / 1024 / 1024
    
    @property
    def throughput(self) -> float:
        """吞吐量（项/秒）"""
        if self.elapsed_s > 0 and self.items_processed > 0:
            return self.items_processed / self.elapsed_s
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'elapsed_ms': round(self.elapsed_ms, 3),
            'elapsed_s': round(self.elapsed_s, 6),
            'memory_delta_mb': round(self.memory_delta_mb, 3),
            'cpu_percent': round(self.cpu_percent, 2),
            'items_processed': self.items_processed,
            'throughput': round(self.throughput, 2)
        }


@dataclass
class CompilationMetrics:
    """编译性能指标集合"""
    source_file: str = ""
    source_size_bytes: int = 0
    source_lines: int = 0
    
    # 各阶段指标
    lexer: Optional[PhaseMetrics] = None
    parser: Optional[PhaseMetrics] = None
    semantic: Optional[PhaseMetrics] = None
    codegen: Optional[PhaseMetrics] = None
    
    # 总体指标
    total_time_s: float = 0.0
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    
    # 时间戳
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def total_time_ms(self) -> float:
        return self.total_time_s * 1000
    
    def get_phase_times(self) -> Dict[str, float]:
        """获取各阶段时间（毫秒）"""
        times = {}
        if self.lexer:
            times['lexer'] = self.lexer.elapsed_ms
        if self.parser:
            times['parser'] = self.parser.elapsed_ms
        if self.semantic:
            times['semantic'] = self.semantic.elapsed_ms
        if self.codegen:
            times['codegen'] = self.codegen.elapsed_ms
        return times
    
    def get_phase_percentages(self) -> Dict[str, float]:
        """获取各阶段时间占比"""
        times = self.get_phase_times()
        total = sum(times.values())
        if total == 0:
            return {}
        return {k: (v / total * 100) for k, v in times.items()}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_file': self.source_file,
            'source_size_bytes': self.source_size_bytes,
            'source_lines': self.source_lines,
            'lexer': self.lexer.to_dict() if self.lexer else None,
            'parser': self.parser.to_dict() if self.parser else None,
            'semantic': self.semantic.to_dict() if self.semantic else None,
            'codegen': self.codegen.to_dict() if self.codegen else None,
            'total_time_s': round(self.total_time_s, 6),
            'total_time_ms': round(self.total_time_ms, 3),
            'peak_memory_mb': round(self.peak_memory_mb, 3),
            'avg_cpu_percent': round(self.avg_cpu_percent, 2),
            'phase_times': self.get_phase_times(),
            'phase_percentages': self.get_phase_percentages(),
            'timestamp': self.timestamp
        }


class CompilationPerformanceMonitor:
    """编译性能监控器
    
    使用方式：
    ```python
    monitor = CompilationPerformanceMonitor()
    
    # 开始编译
    monitor.start_compilation("test.zhc", source_code)
    
    # 词法分析
    with monitor.phase("lexer") as m:
        tokens = lexer.tokenize(source_code)
        m.items_processed = len(tokens)
    
    # 语法分析
    with monitor.phase("parser") as m:
        ast = parser.parse(tokens)
        m.items_processed = 1
    
    # 语义分析
    with monitor.phase("semantic") as m:
        analyzer.analyze(ast)
        m.items_processed = 1
    
    # 代码生成
    with monitor.phase("codegen") as m:
        code = codegen.generate(ast)
        m.items_processed = 1
    
    # 结束编译
    metrics = monitor.end_compilation()
    ```
    """
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.current_metrics: Optional[CompilationMetrics] = None
        self.current_phase: Optional[PhaseMetrics] = None
        self._phase_stack: List[PhaseMetrics] = []
        self._cpu_samples: List[float] = []
    
    def start_compilation(self, source_file: str, source_code: str = "") -> None:
        """开始编译监控"""
        if not self.enabled:
            return
        
        self.current_metrics = CompilationMetrics(
            source_file=source_file,
            source_size_bytes=len(source_code),
            source_lines=source_code.count('\n') + 1 if source_code else 0
        )
        self._cpu_samples = []
    
    @contextmanager
    def phase(self, phase_name: str):
        """编译阶段上下文管理器"""
        if not self.enabled or not self.current_metrics:
            yield PhaseMetrics(name=phase_name)
            return
        
        # 创建阶段指标
        metrics = PhaseMetrics(
            name=phase_name,
            start_time=time.perf_counter(),
            memory_start=self._get_memory_usage()
        )
        
        self._phase_stack.append(metrics)
        
        try:
            yield metrics
        finally:
            # 结束阶段
            metrics.end_time = time.perf_counter()
            metrics.memory_end = self._get_memory_usage()
            metrics.cpu_percent = self._get_cpu_percent()
            
            # 记录到编译指标
            if phase_name == "lexer":
                self.current_metrics.lexer = metrics
            elif phase_name == "parser":
                self.current_metrics.parser = metrics
            elif phase_name == "semantic":
                self.current_metrics.semantic = metrics
            elif phase_name == "codegen":
                self.current_metrics.codegen = metrics
            
            self._phase_stack.pop()
            
            # 更新峰值内存
            if self.current_metrics:
                self.current_metrics.peak_memory_mb = max(
                    self.current_metrics.peak_memory_mb,
                    metrics.memory_end / 1024 / 1024
                )
    
    def end_compilation(self) -> Optional[CompilationMetrics]:
        """结束编译监控"""
        if not self.enabled or not self.current_metrics:
            return None
        
        # 计算总时间
        phase_times = self.current_metrics.get_phase_times()
        self.current_metrics.total_time_s = sum(t / 1000 for t in phase_times.values())
        
        # 计算平均 CPU 使用率
        if self._cpu_samples:
            self.current_metrics.avg_cpu_percent = sum(self._cpu_samples) / len(self._cpu_samples)
        
        metrics = self.current_metrics
        self.current_metrics = None
        self._cpu_samples = []
        
        return metrics
    
    def _get_memory_usage(self) -> int:
        """获取当前内存使用（字节）"""
        try:
            return psutil.Process().memory_info().rss
        except:
            return 0
    
    def _get_cpu_percent(self) -> float:
        """获取 CPU 使用率"""
        try:
            cpu = psutil.cpu_percent(interval=0.01)
            self._cpu_samples.append(cpu)
            return cpu
        except:
            return 0.0


class PerformanceReportGenerator:
    """性能报告生成器"""
    
    @staticmethod
    def generate_text_report(metrics: CompilationMetrics) -> str:
        """生成文本格式报告"""
        lines = []
        lines.append("=" * 70)
        lines.append("📊 编译性能报告")
        lines.append("=" * 70)
        
        # 源文件信息
        lines.append(f"\n📄 源文件: {metrics.source_file}")
        lines.append(f"   大小: {metrics.source_size_bytes} 字节")
        lines.append(f"   行数: {metrics.source_lines}")
        
        # 总体统计
        lines.append(f"\n📈 总体统计:")
        lines.append(f"   总耗时: {metrics.total_time_ms:.3f} ms")
        lines.append(f"   峰值内存: {metrics.peak_memory_mb:.2f} MB")
        lines.append(f"   平均 CPU: {metrics.avg_cpu_percent:.1f}%")
        
        # 各阶段耗时
        lines.append(f"\n⏱️  各阶段耗时:")
        phase_times = metrics.get_phase_times()
        phase_percentages = metrics.get_phase_percentages()
        
        for phase_name in ['lexer', 'parser', 'semantic', 'codegen']:
            if phase_name in phase_times:
                time_ms = phase_times[phase_name]
                percentage = phase_percentages.get(phase_name, 0)
                phase_metrics = getattr(metrics, phase_name)
                
                lines.append(f"   {phase_name.upper():10s}: {time_ms:8.3f} ms ({percentage:5.1f}%)")
                if phase_metrics and phase_metrics.items_processed > 0:
                    lines.append(f"              吞吐量: {phase_metrics.throughput:.2f} 项/秒")
        
        # 性能分布图
        lines.append(f"\n📊 性能分布:")
        lines.append(PerformanceReportGenerator._generate_bar_chart(phase_percentages))
        
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    @staticmethod
    def _generate_bar_chart(percentages: Dict[str, float], width: int = 50) -> str:
        """生成柱状图"""
        lines = []
        for phase_name in ['lexer', 'parser', 'semantic', 'codegen']:
            if phase_name in percentages:
                percentage = percentages[phase_name]
                bar_width = int(percentage / 100 * width)
                bar = "█" * bar_width + "░" * (width - bar_width)
                lines.append(f"   {phase_name.upper():10s} {bar} {percentage:5.1f}%")
        return "\n".join(lines)
    
    @staticmethod
    def generate_json_report(metrics: CompilationMetrics) -> str:
        """生成 JSON 格式报告"""
        return json.dumps(metrics.to_dict(), indent=2, ensure_ascii=False)
    
    @staticmethod
    def generate_markdown_report(metrics: CompilationMetrics) -> str:
        """生成 Markdown 格式报告"""
        lines = []
        lines.append("# 编译性能报告")
        lines.append(f"\n**生成时间**: {metrics.timestamp}")
        lines.append(f"**源文件**: `{metrics.source_file}`")
        
        lines.append("\n## 源文件信息")
        lines.append(f"- 文件大小: {metrics.source_size_bytes} 字节")
        lines.append(f"- 代码行数: {metrics.source_lines}")
        
        lines.append("\n## 总体统计")
        lines.append(f"| 指标 | 值 |")
        lines.append(f"|------|------|")
        lines.append(f"| 总耗时 | {metrics.total_time_ms:.3f} ms |")
        lines.append(f"| 峰值内存 | {metrics.peak_memory_mb:.2f} MB |")
        lines.append(f"| 平均 CPU | {metrics.avg_cpu_percent:.1f}% |")
        
        lines.append("\n## 各阶段耗时")
        lines.append(f"| 阶段 | 耗时 (ms) | 占比 | 吞吐量 |")
        lines.append(f"|------|-----------|------|--------|")
        
        phase_times = metrics.get_phase_times()
        phase_percentages = metrics.get_phase_percentages()
        
        for phase_name in ['lexer', 'parser', 'semantic', 'codegen']:
            if phase_name in phase_times:
                time_ms = phase_times[phase_name]
                percentage = phase_percentages.get(phase_name, 0)
                phase_metrics = getattr(metrics, phase_name)
                throughput = f"{phase_metrics.throughput:.2f}" if phase_metrics else "-"
                
                lines.append(f"| {phase_name.upper()} | {time_ms:.3f} | {percentage:.1f}% | {throughput} |")
        
        return "\n".join(lines)


# 全局性能监控器实例
_global_monitor: Optional[CompilationPerformanceMonitor] = None


def get_performance_monitor(enabled: bool = True) -> CompilationPerformanceMonitor:
    """获取全局性能监控器"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = CompilationPerformanceMonitor(enabled=enabled)
    return _global_monitor


def reset_performance_monitor() -> None:
    """重置全局性能监控器"""
    global _global_monitor
    _global_monitor = None
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编译性能监控测试 - Compilation Performance Monitor Test

测试目标：
1. 验证性能监控器功能正确
2. 验证各阶段计时准确
3. 验证报告生成正确
4. 验收标准：所有测试通过

作者：远
日期：2026-04-07
"""

import pytest
import time
import sys
from pathlib import Path

# 注册 zhc 包
src_path = Path(__file__).parent.parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path.parent))
    import src
    sys.modules["zhc"] = sys.modules["src"]

from zhc.compiler.performance_monitor import (
    CompilationPerformanceMonitor,
    CompilationMetrics,
    PhaseMetrics,
    PerformanceReportGenerator
)


class TestCompilationPerformanceMonitor:
    """编译性能监控测试"""
    
    @pytest.fixture
    def monitor(self):
        """创建性能监控器"""
        return CompilationPerformanceMonitor(enabled=True)
    
    def test_start_compilation(self, monitor):
        """测试开始编译监控"""
        source_code = "函数 主函数() { 返回 0; }"
        monitor.start_compilation("test.zhc", source_code)
        
        assert monitor.current_metrics is not None
        assert monitor.current_metrics.source_file == "test.zhc"
        assert monitor.current_metrics.source_size_bytes == len(source_code)
        assert monitor.current_metrics.source_lines == 1
        
        print(f"\n开始编译监控测试:")
        print(f"  源文件: {monitor.current_metrics.source_file}")
        print(f"  大小: {monitor.current_metrics.source_size_bytes} 字节")
        print(f"  行数: {monitor.current_metrics.source_lines}")
    
    def test_phase_context_manager(self, monitor):
        """测试阶段上下文管理器"""
        source_code = "测试代码"
        monitor.start_compilation("test.zhc", source_code)
        
        # 测试词法分析阶段
        with monitor.phase("lexer") as m:
            time.sleep(0.001)  # 模拟处理
            m.items_processed = 10
        
        assert monitor.current_metrics.lexer is not None
        assert monitor.current_metrics.lexer.elapsed_ms > 0
        assert monitor.current_metrics.lexer.items_processed == 10
        
        print(f"\n阶段上下文管理器测试:")
        print(f"  阶段: lexer")
        print(f"  耗时: {monitor.current_metrics.lexer.elapsed_ms:.3f} ms")
        print(f"  处理项: {monitor.current_metrics.lexer.items_processed}")
        print(f"  吞吐量: {monitor.current_metrics.lexer.throughput:.2f} 项/秒")
    
    def test_all_phases(self, monitor):
        """测试所有编译阶段"""
        source_code = "函数 主函数() { 返回 0; }"
        monitor.start_compilation("test.zhc", source_code)
        
        # 词法分析
        with monitor.phase("lexer") as m:
            time.sleep(0.001)
            m.items_processed = 10
        
        # 语法分析
        with monitor.phase("parser") as m:
            time.sleep(0.002)
            m.items_processed = 1
        
        # 语义分析
        with monitor.phase("semantic") as m:
            time.sleep(0.001)
            m.items_processed = 1
        
        # 代码生成
        with monitor.phase("codegen") as m:
            time.sleep(0.0005)
            m.items_processed = 1
        
        # 结束编译
        metrics = monitor.end_compilation()
        
        assert metrics is not None
        assert metrics.lexer is not None
        assert metrics.parser is not None
        assert metrics.semantic is not None
        assert metrics.codegen is not None
        assert metrics.total_time_ms > 0
        
        print(f"\n所有阶段测试:")
        print(f"  Lexer: {metrics.lexer.elapsed_ms:.3f} ms")
        print(f"  Parser: {metrics.parser.elapsed_ms:.3f} ms")
        print(f"  Semantic: {metrics.semantic.elapsed_ms:.3f} ms")
        print(f"  CodeGen: {metrics.codegen.elapsed_ms:.3f} ms")
        print(f"  总耗时: {metrics.total_time_ms:.3f} ms")
    
    def test_phase_percentages(self, monitor):
        """测试阶段占比计算"""
        source_code = "测试"
        monitor.start_compilation("test.zhc", source_code)
        
        with monitor.phase("lexer") as m:
            time.sleep(0.01)
            m.items_processed = 1
        
        with monitor.phase("parser") as m:
            time.sleep(0.02)
            m.items_processed = 1
        
        metrics = monitor.end_compilation()
        
        percentages = metrics.get_phase_percentages()
        
        assert 'lexer' in percentages
        assert 'parser' in percentages
        assert abs(percentages['lexer'] + percentages['parser'] - 100) < 1  # 允许 1% 误差
        
        print(f"\n阶段占比测试:")
        for phase, pct in percentages.items():
            print(f"  {phase}: {pct:.1f}%")
    
    def test_report_generation(self, monitor):
        """测试报告生成"""
        source_code = "函数 主函数() { 返回 0; }"
        monitor.start_compilation("test.zhc", source_code)
        
        with monitor.phase("lexer") as m:
            time.sleep(0.001)
            m.items_processed = 10
        
        with monitor.phase("parser") as m:
            time.sleep(0.002)
            m.items_processed = 1
        
        metrics = monitor.end_compilation()
        
        # 生成文本报告
        text_report = PerformanceReportGenerator.generate_text_report(metrics)
        assert "编译性能报告" in text_report
        assert "test.zhc" in text_report
        
        # 生成 JSON 报告
        json_report = PerformanceReportGenerator.generate_json_report(metrics)
        assert '"source_file": "test.zhc"' in json_report
        
        # 生成 Markdown 报告
        md_report = PerformanceReportGenerator.generate_markdown_report(metrics)
        assert "# 编译性能报告" in md_report
        assert "test.zhc" in md_report
        
        print(f"\n报告生成测试:")
        print(f"  文本报告长度: {len(text_report)} 字符")
        print(f"  JSON 报告长度: {len(json_report)} 字符")
        print(f"  Markdown 报告长度: {len(md_report)} 字符")
    
    def test_disabled_monitor(self):
        """测试禁用监控"""
        monitor = CompilationPerformanceMonitor(enabled=False)
        
        source_code = "测试"
        monitor.start_compilation("test.zhc", source_code)
        
        # 禁用时不应该记录
        with monitor.phase("lexer") as m:
            time.sleep(0.001)
            m.items_processed = 10
        
        metrics = monitor.end_compilation()
        
        # 禁用时返回 None
        assert metrics is None
        
        print(f"\n禁用监控测试:")
        print(f"  返回值: {metrics}")
    
    def test_metrics_to_dict(self, monitor):
        """测试指标序列化"""
        source_code = "测试"
        monitor.start_compilation("test.zhc", source_code)
        
        with monitor.phase("lexer") as m:
            time.sleep(0.001)
            m.items_processed = 10
        
        metrics = monitor.end_compilation()
        
        # 序列化为字典
        data = metrics.to_dict()
        
        assert isinstance(data, dict)
        assert 'source_file' in data
        assert 'lexer' in data
        assert 'total_time_ms' in data
        assert 'phase_times' in data
        assert 'phase_percentages' in data
        
        print(f"\n指标序列化测试:")
        print(f"  字典键: {list(data.keys())}")
    
    def test_memory_tracking(self, monitor):
        """测试内存追踪"""
        source_code = "测试" * 1000  # 较大源码
        monitor.start_compilation("test.zhc", source_code)
        
        with monitor.phase("lexer") as m:
            # 创建一些对象模拟内存分配
            data = [i for i in range(10000)]
            m.items_processed = len(data)
        
        metrics = monitor.end_compilation()
        
        assert metrics.peak_memory_mb > 0
        
        print(f"\n内存追踪测试:")
        print(f"  峰值内存: {metrics.peak_memory_mb:.2f} MB")


class TestPhaseMetrics:
    """阶段指标测试"""
    
    def test_phase_metrics_creation(self):
        """测试阶段指标创建"""
        metrics = PhaseMetrics(
            name="test",
            start_time=time.perf_counter(),
            end_time=time.perf_counter() + 0.001,
            items_processed=100
        )
        
        assert metrics.name == "test"
        assert metrics.elapsed_ms > 0
        assert metrics.throughput > 0
        
        print(f"\n阶段指标创建测试:")
        print(f"  名称: {metrics.name}")
        print(f"  耗时: {metrics.elapsed_ms:.3f} ms")
        print(f"  吞吐量: {metrics.throughput:.2f} 项/秒")
    
    def test_phase_metrics_to_dict(self):
        """测试阶段指标序列化"""
        metrics = PhaseMetrics(
            name="test",
            start_time=time.perf_counter(),
            end_time=time.perf_counter() + 0.001,
            items_processed=100
        )
        
        data = metrics.to_dict()
        
        assert isinstance(data, dict)
        assert data['name'] == "test"
        assert 'elapsed_ms' in data
        assert 'throughput' in data
        
        print(f"\n阶段指标序列化测试:")
        print(f"  字典: {data}")


# ===== 运行测试 =====

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
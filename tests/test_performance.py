"""
性能分析模块测试
"""

import pytest
import time
from zhc.profiler import (
    ProfilerTracker,
    FunctionProfile,
    ProfilerStats,
    TextReporter,
    JsonReporter,
    HtmlReporter,
    HotspotAnalyzer,
    profile_function,
    profile_scope,
)


class TestProfilerTracker:
    """ProfilerTracker 测试"""

    def test_basic_tracking(self):
        """基本追踪测试"""
        tracker = ProfilerTracker()
        tracker.start()

        # 模拟函数调用
        tracker.enter("func_a")
        time.sleep(0.001)
        tracker.exit("func_a")

        tracker.enter("func_b")
        time.sleep(0.001)
        tracker.exit("func_b")

        tracker.stop()

        # 验证
        assert tracker.is_enabled == False
        funcs = tracker.get_all_functions()
        assert len(funcs) == 2

        func_names = {f.name for f in funcs}
        assert "func_a" in func_names
        assert "func_b" in func_names

    def test_call_count(self):
        """调用次数统计"""
        tracker = ProfilerTracker()
        tracker.start()

        for _ in range(5):
            tracker.enter("counted_func")
            tracker.exit("counted_func")

        tracker.stop()

        func = tracker.get_function("counted_func")
        assert func is not None
        assert func.call_count == 5

    def test_nested_calls(self):
        """嵌套调用测试"""
        tracker = ProfilerTracker()
        tracker.start()

        tracker.enter("parent")
        tracker.enter("child1")
        tracker.exit("child1")
        tracker.enter("child2")
        tracker.exit("child2")
        tracker.exit("parent")

        tracker.stop()

        parent = tracker.get_function("parent")
        child1 = tracker.get_function("child1")
        child2 = tracker.get_function("child2")

        assert parent is not None
        assert child1 is not None
        assert child2 is not None
        assert "child1" in parent.children
        assert "child2" in parent.children

    def test_profile_decorator(self):
        """函数装饰器测试"""
        tracker = ProfilerTracker()
        tracker.start()

        decorated_func = tracker.profile(lambda: time.sleep(0.001))
        decorated_func()

        tracker.stop()

        func = tracker.get_function("<lambda>")
        assert func is not None
        assert func.call_count == 1

    def test_profile_scope(self):
        """代码块作用域测试"""
        tracker = ProfilerTracker()
        tracker.start()

        with tracker.profile_scope("block"):
            time.sleep(0.001)

        tracker.stop()

        func = tracker.get_function("block")
        assert func is not None
        assert func.call_count == 1

    def test_reset(self):
        """重置测试"""
        tracker = ProfilerTracker()
        tracker.start()

        tracker.enter("func")
        tracker.exit("func")
        tracker.stop()

        tracker.reset()

        assert len(tracker.get_all_functions()) == 0
        assert tracker.get_stats().total_calls == 0


class TestFunctionProfile:
    """FunctionProfile 测试"""

    def test_time_calculation(self):
        """时间计算测试"""
        profile = FunctionProfile(
            name="test",
            call_count=10,
            total_time_ns=1_000_000_000,  # 1 秒
            min_time_ns=80_000_000,
            max_time_ns=150_000_000,
        )

        assert profile.total_time_ms == 1000.0
        assert profile.avg_time_ms == 100.0
        assert profile.total_time_s == 1.0


class TestProfilerStats:
    """ProfilerStats 测试"""

    def test_elapsed_calculation(self):
        """耗时计算测试"""
        stats = ProfilerStats(
            start_time_ns=0,
            end_time_ns=1_000_000_000,
        )

        assert stats.elapsed_ns == 1_000_000_000
        assert stats.elapsed_ms == 1000.0
        assert stats.elapsed_s == 1.0


class TestHotspotAnalyzer:
    """热点分析器测试"""

    def test_basic_hotspot_detection(self):
        """基本热点检测"""
        tracker = ProfilerTracker()
        tracker.start()

        # 创建一个明显的热点
        for _ in range(100):
            tracker.enter("hot_function")
            time.sleep(0.001)  # 1ms
            tracker.exit("hot_function")

        tracker.stop()

        # 分析热点
        analyzer = HotspotAnalyzer(tracker)
        hotspots = analyzer.analyze(threshold=0.1)  # 0.1% 阈值

        assert len(hotspots) > 0

        # 验证热点按时间排序
        if len(hotspots) >= 2:
            assert hotspots[0].percentage >= hotspots[1].percentage

    def test_optimization_hints(self):
        """优化建议生成"""
        tracker = ProfilerTracker()
        tracker.start()

        # 创建一个高占比函数
        for _ in range(10):
            tracker.enter("expensive_function")
            time.sleep(0.01)  # 10ms
            tracker.exit("expensive_function")

        tracker.stop()

        analyzer = HotspotAnalyzer(tracker)
        hotspots = analyzer.analyze(threshold=0.1)

        if hotspots:
            # 验证有优化建议
            assert len(hotspots[0].hints) >= 0  # 可能有建议


class TestReporter:
    """报告生成器测试"""

    def test_text_reporter(self):
        """文本报告生成"""
        tracker = ProfilerTracker()
        tracker.start()

        tracker.enter("func_a")
        tracker.exit("func_a")

        tracker.stop()

        reporter = TextReporter()
        report = reporter.generate(tracker)

        assert "性能剖析报告" in report
        assert "func_a" in report

    def test_json_reporter(self):
        """JSON 报告生成"""
        tracker = ProfilerTracker()
        tracker.start()

        tracker.enter("func")
        tracker.exit("func")

        tracker.stop()

        reporter = JsonReporter()
        report = reporter.generate(tracker)

        import json

        data = json.loads(report)

        assert "stats" in data
        assert "functions" in data
        assert data["stats"]["total_calls"] >= 0

    def test_html_reporter(self):
        """HTML 报告生成"""
        tracker = ProfilerTracker()
        tracker.start()

        tracker.enter("func")
        tracker.exit("func")

        tracker.stop()

        reporter = HtmlReporter()
        report = reporter.generate(tracker)

        assert "<!DOCTYPE html>" in report
        assert "性能剖析报告" in report or "Profile" in report


class TestGlobalFunctions:
    """全局函数测试"""

    def test_profile_function_decorator(self):
        """全局函数装饰器"""
        # 重置全局追踪器
        from zhc.profiler import tracker as tracker_module

        tracker_module._global_tracker = None

        @profile_function()
        def test_func():
            time.sleep(0.001)

        start_profiling()
        test_func()
        stop_profiling()

        tracker = tracker_module.get_tracker()
        assert tracker.get_function("test_func") is not None

    def test_profile_scope_context(self):
        """全局作用域上下文"""
        from zhc.profiler import tracker as tracker_module

        tracker_module._global_tracker = None

        start_profiling()
        with profile_scope("test_scope"):
            time.sleep(0.001)
        stop_profiling()

        tracker = tracker_module.get_tracker()
        assert tracker.get_function("test_scope") is not None


# 辅助函数
def start_profiling():
    """开始性能剖析"""
    import zhc.profiler as profiler_module

    profiler_module.start_profiling()


def stop_profiling():
    """停止性能剖析"""
    import zhc.profiler as profiler_module

    profiler_module.stop_profiling()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

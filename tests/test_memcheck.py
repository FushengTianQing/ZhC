"""
内存分析模块测试
"""

import pytest
from zhc.memcheck import (
    MemTracker,
    MemBlock,
    MemStats,
    AllocSite,
    TextReporter,
    JsonReporter,
    HtmlReporter,
    LeakDetector,
    track_alloc,
)


class TestMemTracker:
    """MemTracker 测试"""

    def test_basic_allocation(self):
        """基本分配测试"""
        tracker = MemTracker()
        tracker.start()

        ptr = tracker.alloc(1024, "test.py", 10, "test_func")

        assert ptr > 0
        assert tracker.stats.alloc_count == 1
        assert tracker.stats.total_alloc_bytes == 1024
        assert tracker.stats.current_used_bytes == 1024

        tracker.stop()

    def test_basic_free(self):
        """基本释放测试"""
        tracker = MemTracker()
        tracker.start()

        ptr = tracker.alloc(1024, "test.py", 10, "test_func")
        success = tracker.free(ptr, "test.py", 20)

        assert success
        assert tracker.stats.free_count == 1
        assert tracker.stats.current_used_bytes == 0

        tracker.stop()

    def test_invalid_free(self):
        """无效释放测试"""
        tracker = MemTracker()
        tracker.start()

        success = tracker.free(9999, "test.py", 20)

        assert not success
        assert tracker.stats.invalid_free_count == 1

        tracker.stop()

    def test_multiple_allocations(self):
        """多次分配测试"""
        tracker = MemTracker()
        tracker.start()

        ptrs = []
        for i in range(5):
            ptr = tracker.alloc((i + 1) * 100, "test.py", 10 + i, "test_func")
            ptrs.append(ptr)

        assert len(ptrs) == 5
        assert tracker.stats.alloc_count == 5
        assert tracker.stats.current_used_bytes == 1500  # 100+200+300+400+500

        tracker.stop()

    def test_leak_detection(self):
        """泄漏检测测试"""
        tracker = MemTracker()
        tracker.start()

        # 分配但不释放
        tracker.alloc(100, "test.py", 10, "leak_func")
        tracker.alloc(200, "test.py", 20, "leak_func")

        tracker.stop()

        assert tracker.has_leaks()
        assert tracker.get_leak_count() == 2
        assert tracker.get_leak_bytes() == 300

    def test_realloc(self):
        """重新分配测试"""
        tracker = MemTracker()
        tracker.start()

        ptr = tracker.alloc(100, "test.py", 10, "test_func")
        new_ptr = tracker.realloc(ptr, 200, "test.py", 20, "test_func")

        assert new_ptr == ptr  # 指针不变
        assert tracker.stats.current_used_bytes == 200

        tracker.stop()

    def test_reset(self):
        """重置测试"""
        tracker = MemTracker()
        tracker.start()

        tracker.alloc(100, "test.py", 10, "test_func")
        tracker.stop()

        tracker.reset()

        assert tracker.stats.alloc_count == 0
        assert tracker.stats.current_used_bytes == 0
        assert len(tracker.get_all_blocks()) == 0

    def test_alloc_sites(self):
        """分配源统计测试"""
        tracker = MemTracker()
        tracker.start()

        # 相同位置的分配会合并统计
        tracker.alloc(100, "file1.py", 10, "func_a")
        tracker.alloc(200, "file1.py", 10, "func_a")  # 同一位置
        tracker.alloc(300, "file2.py", 30, "func_b")

        tracker.stop()

        sites = tracker.get_alloc_sites()
        assert len(sites) == 2  # func_a (同一位置) + func_b

        # 查找 func_a 的统计
        func_a_site = next((s for s in sites if s.func == "func_a"), None)
        assert func_a_site is not None
        assert func_a_site.alloc_count == 2
        assert func_a_site.total_bytes == 300
        assert func_a_site.current_bytes == 300


class TestMemBlock:
    """MemBlock 测试"""

    def test_ptr_address(self):
        """指针地址格式化"""
        block = MemBlock(
            ptr=0x1234567890,
            size=1024,
            file="test.py",
            line=10,
            func="test_func",
            alloc_time=0,
            alloc_id=1,
        )

        assert block.ptr_address == "0x0000001234567890"

    def test_to_dict(self):
        """转换为字典"""
        block = MemBlock(
            ptr=100,
            size=1024,
            file="test.py",
            line=10,
            func="test_func",
            alloc_time=1234567890,
            alloc_id=1,
        )

        data = block.to_dict()
        assert data["ptr"] == 100
        assert data["size"] == 1024
        assert data["file"] == "test.py"


class TestMemStats:
    """MemStats 测试"""

    def test_formatted_properties(self):
        """格式化属性测试"""
        stats = MemStats(
            total_alloc_bytes=2048,
            total_free_bytes=1024,
            current_used_bytes=1024,
            peak_used_bytes=2048,
            leak_count=1,
            leak_bytes=1024,
        )

        assert stats.current_used == "1.00 KB"
        assert stats.peak_used == "2.00 KB"
        assert stats.total_alloc == "2.00 KB"


class TestAllocSite:
    """AllocSite 测试"""

    def test_location(self):
        """位置格式化"""
        site = AllocSite(
            file="test.py",
            line=100,
            func="test_func",
        )

        assert site.location == "test.py:100"


class TestLeakDetector:
    """LeakDetector 测试"""

    def test_no_leaks(self):
        """无泄漏测试"""
        tracker = MemTracker()
        tracker.start()

        ptr = tracker.alloc(100, "test.py", 10, "test_func")
        tracker.free(ptr, "test.py", 20)

        tracker.stop()

        detector = LeakDetector(tracker)
        leaks = detector.detect()

        assert len(leaks) == 0

    def test_leak_detection(self):
        """泄漏检测测试"""
        tracker = MemTracker()
        tracker.start()

        # 创建泄漏
        tracker.alloc(100, "test.py", 10, "leak_func")
        tracker.alloc(1024 * 1024, "test.py", 20, "big_leak")

        tracker.stop()

        detector = LeakDetector(tracker)
        leaks = detector.detect()

        assert len(leaks) == 2

        # 验证按严重程度排序
        assert leaks[0].severity in ["critical", "high", "medium", "low"]

    def test_summary(self):
        """摘要统计测试"""
        tracker = MemTracker()
        tracker.start()

        tracker.alloc(1024, "test.py", 10, "leak_func")
        tracker.alloc(1024 * 1024, "test.py", 20, "big_leak")

        tracker.stop()

        detector = LeakDetector(tracker)
        detector.detect()

        summary = detector.get_summary()
        assert summary["total_leaks"] == 2
        assert summary["total_leak_bytes"] == 1024 + 1024 * 1024

    def test_json_report(self):
        """JSON 报告测试"""
        tracker = MemTracker()
        tracker.start()

        tracker.alloc(100, "test.py", 10, "leak_func")

        tracker.stop()

        detector = LeakDetector(tracker)
        detector.detect()

        report = detector.get_json_report()
        assert "summary" in report
        assert "leaks" in report


class TestReporter:
    """报告生成器测试"""

    def test_text_reporter(self):
        """文本报告生成"""
        tracker = MemTracker()
        tracker.start()

        tracker.alloc(100, "test.py", 10, "test_func")
        tracker.alloc(200, "test.py", 20, "test_func")

        tracker.stop()

        reporter = TextReporter()
        report = reporter.generate(tracker)

        assert "内存使用报告" in report
        assert "test_func" in report or "泄漏" in report

    def test_json_reporter(self):
        """JSON 报告生成"""
        tracker = MemTracker()
        tracker.start()

        tracker.alloc(100, "test.py", 10, "test_func")

        tracker.stop()

        reporter = JsonReporter()
        report = reporter.generate(tracker)

        import json

        data = json.loads(report)

        assert "stats" in data
        assert data["stats"]["alloc_count"] == 1

    def test_html_reporter(self):
        """HTML 报告生成"""
        tracker = MemTracker()
        tracker.start()

        tracker.alloc(100, "test.py", 10, "test_func")

        tracker.stop()

        reporter = HtmlReporter()
        report = reporter.generate(tracker)

        assert "<!DOCTYPE html>" in report
        assert "内存使用报告" in report or "Memory" in report


class TestGlobalFunctions:
    """全局函数测试"""

    def test_global_tracking(self):
        """全局追踪函数"""
        # 重置全局追踪器
        from zhc.memcheck import tracker as tracker_module

        tracker_module._global_tracker = None

        from zhc.memcheck import start_tracking, stop_tracking, reset_tracking

        start_tracking()
        ptr = track_alloc(100, "test.py", 10, "test_func")
        stop_tracking()

        tracker = tracker_module.get_tracker()
        assert tracker.stats.alloc_count == 1
        assert ptr > 0  # 验证分配成功

        reset_tracking()
        assert tracker.stats.alloc_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
覆盖率模块测试
"""

import tempfile
import os

from zhc.coverage import (
    # 数据结构
    LineCoverage,
    BranchCoverage,
    FunctionCoverage,
    FileCoverage,
    ProjectCoverage,
    # 追踪器
    CoverageTracker,
    start_coverage,
    stop_coverage,
    reset_coverage,
    get_coverage,
    # 插桩
    Instrumenter,
    TextReporter,
    JsonReporter,
    HtmlReporter,
    MarkdownReporter,
    generate_report,
    save_report,
)


class TestLineCoverage:
    """行覆盖率测试"""

    def test_line_coverage_creation(self):
        """测试行覆盖率创建"""
        line = LineCoverage(line_number=10, hit_count=5)
        assert line.line_number == 10
        assert line.hit_count == 5
        assert line.is_covered

    def test_line_not_covered(self):
        """测试未覆盖行"""
        line = LineCoverage(line_number=10, hit_count=0)
        assert not line.is_covered


class TestBranchCoverage:
    """分支覆盖率测试"""

    def test_branch_coverage_creation(self):
        """测试分支覆盖率创建"""
        branch = BranchCoverage(branch_id="b1", line_number=10)
        assert branch.branch_id == "b1"
        assert branch.line_number == 10
        assert branch.total_hits == 0
        assert not branch.is_covered

    def test_branch_partial_coverage(self):
        """测试部分覆盖"""
        branch = BranchCoverage(branch_id="b1", line_number=10, true_hits=5)
        assert branch.partial_coverage
        assert not branch.is_covered

    def test_branch_full_coverage(self):
        """测试完全覆盖"""
        branch = BranchCoverage(
            branch_id="b1", line_number=10, true_hits=5, false_hits=3
        )
        assert branch.is_covered
        assert not branch.partial_coverage


class TestFunctionCoverage:
    """函数覆盖率测试"""

    def test_function_coverage_creation(self):
        """测试函数覆盖率创建"""
        func = FunctionCoverage(function_name="main", start_line=1, end_line=100)
        assert func.function_name == "main"
        assert func.start_line == 1
        assert func.end_line == 100
        assert not func.is_covered

    def test_function_covered(self):
        """测试已覆盖函数"""
        func = FunctionCoverage(
            function_name="main", start_line=1, end_line=100, hit_count=10
        )
        assert func.is_covered


class TestFileCoverage:
    """文件覆盖率测试"""

    def test_file_coverage_creation(self):
        """测试文件覆盖率创建"""
        file_cov = FileCoverage(file_path="/test.c")
        assert file_cov.file_path == "/test.c"
        assert file_cov.total_lines == 0
        assert file_cov.line_coverage_rate == 1.0  # 无行时为 100%

    def test_file_coverage_add_line(self):
        """测试添加行"""
        file_cov = FileCoverage(file_path="/test.c")
        file_cov.add_line(10)
        file_cov.add_line(20)

        assert file_cov.total_lines == 2
        assert file_cov.covered_lines == 0
        assert file_cov.line_coverage_rate == 0.0

    def test_file_coverage_hit_line(self):
        """测试行命中"""
        file_cov = FileCoverage(file_path="/test.c")
        file_cov.add_line(10)
        file_cov.add_line(20)
        file_cov.hit_line(10)

        assert file_cov.covered_lines == 1
        assert file_cov.line_coverage_rate == 0.5

    def test_file_coverage_branch(self):
        """测试分支覆盖率"""
        file_cov = FileCoverage(file_path="/test.c")
        file_cov.add_branch("b1", 10)
        file_cov.add_branch("b2", 20)

        assert file_cov.total_branches == 4  # 2 个分支 * 2 个方向

        file_cov.hit_branch_true("b1")
        file_cov.hit_branch_false("b1")

        assert file_cov.covered_branches == 2
        assert file_cov.branch_coverage_rate == 0.5

    def test_file_coverage_function(self):
        """测试函数覆盖率"""
        file_cov = FileCoverage(file_path="/test.c")
        file_cov.add_function("main", 1, 50)
        file_cov.add_function("helper", 51, 100)

        assert file_cov.total_functions == 2

        file_cov.hit_function("main")

        assert file_cov.covered_functions == 1
        assert file_cov.function_coverage_rate == 0.5

    def test_file_coverage_to_dict(self):
        """测试转换为字典"""
        file_cov = FileCoverage(file_path="/test.c")
        file_cov.add_line(10)
        file_cov.hit_line(10)

        data = file_cov.to_dict()
        assert data["file_path"] == "/test.c"
        assert data["line_coverage"]["total"] == 1
        assert data["line_coverage"]["covered"] == 1


class TestProjectCoverage:
    """项目覆盖率测试"""

    def test_project_coverage_creation(self):
        """测试项目覆盖率创建"""
        proj = ProjectCoverage()
        assert proj.total_lines == 0

    def test_project_coverage_add_file(self):
        """测试添加文件"""
        proj = ProjectCoverage()
        file1 = proj.add_file("/test1.c")
        proj.add_file("/test2.c")

        assert len(proj.files) == 2
        assert proj.get_file("/test1.c") is file1

    def test_project_coverage_summary(self):
        """测试项目覆盖率汇总"""
        proj = ProjectCoverage()

        file1 = proj.add_file("/test1.c")
        file1.add_line(10)
        file1.add_line(20)
        file1.hit_line(10)

        file2 = proj.add_file("/test2.c")
        file2.add_line(30)
        file2.hit_line(30)

        assert proj.total_lines == 3
        assert proj.covered_lines == 2
        assert abs(proj.line_coverage_rate - 2 / 3) < 0.001


class TestCoverageTracker:
    """覆盖率追踪器测试"""

    def test_tracker_singleton(self):
        """测试单例模式"""
        tracker1 = CoverageTracker()
        tracker2 = CoverageTracker()
        assert tracker1 is tracker2

    def test_tracker_start_stop(self):
        """测试开始/停止"""
        tracker = CoverageTracker()
        tracker.reset()

        assert not tracker.enabled
        tracker.start()
        assert tracker.enabled
        tracker.stop()
        assert not tracker.enabled

    def test_tracker_hit_line(self):
        """测试行命中追踪"""
        tracker = CoverageTracker()
        tracker.reset()
        tracker.register_file("/test.c", [10, 20, 30])
        tracker.start()

        tracker.hit_line("/test.c", 10)
        tracker.hit_line("/test.c", 10)
        tracker.stop()

        cov = tracker.get_coverage()
        file_cov = cov.get_file("/test.c")
        assert file_cov is not None
        assert file_cov.lines[10].hit_count == 2


class TestInstrumenter:
    """代码插桩器测试"""

    def test_find_executable_lines(self):
        """测试可执行行分析"""
        instrumenter = Instrumenter()

        source = """
int main() {
    int x = 1;
    int y = 2;
    return x + y;
}
"""
        lines = instrumenter._find_executable_lines(source)
        # 应该包含赋值和返回语句
        assert len(lines) > 0

    def test_instrument_source(self):
        """测试源代码插桩"""
        instrumenter = Instrumenter()

        source = """
int main() {
    int x = 1;
    return x;
}
"""
        instrumented = instrumenter.instrument_source(source, "test.c")

        # 插桩后的代码应该包含追踪代码
        assert "test.c" in instrumented or "COVERAGE" in instrumented


class TestReporters:
    """报告器测试"""

    def _create_sample_coverage(self) -> ProjectCoverage:
        """创建示例覆盖率数据"""
        proj = ProjectCoverage()

        file1 = proj.add_file("/src/main.c")
        file1.add_line(10)
        file1.add_line(20)
        file1.add_line(30)
        file1.hit_line(10)
        file1.hit_line(20)

        file1.add_function("main", 1, 50)
        file1.hit_function("main")

        file1.add_branch("b1", 15)
        file1.hit_branch_true("b1")
        file1.hit_branch_false("b1")

        return proj

    def test_text_reporter(self):
        """测试文本报告器"""
        proj = self._create_sample_coverage()
        reporter = TextReporter()
        report = reporter.generate(proj)

        assert "覆盖率报告" in report
        assert "行覆盖率" in report

    def test_json_reporter(self):
        """测试 JSON 报告器"""
        proj = self._create_sample_coverage()
        reporter = JsonReporter()
        report = reporter.generate(proj)

        import json

        data = json.loads(report)
        assert "summary" in data
        assert "files" in data

    def test_html_reporter(self):
        """测试 HTML 报告器"""
        proj = self._create_sample_coverage()
        reporter = HtmlReporter()
        report = reporter.generate(proj)

        assert "<!DOCTYPE html>" in report
        assert "覆盖率报告" in report

    def test_markdown_reporter(self):
        """测试 Markdown 报告器"""
        proj = self._create_sample_coverage()
        reporter = MarkdownReporter()
        report = reporter.generate(proj)

        assert "# 📊 覆盖率报告" in report
        assert "| 指标 |" in report

    def test_generate_report(self):
        """测试生成报告"""
        proj = self._create_sample_coverage()

        text_report = generate_report(proj, "text")
        assert "覆盖率报告" in text_report

        json_report = generate_report(proj, "json")
        assert '"summary"' in json_report

    def test_save_report(self):
        """测试保存报告"""
        proj = self._create_sample_coverage()

        with tempfile.TemporaryDirectory() as tmpdir:
            # 保存文本报告
            text_path = os.path.join(tmpdir, "coverage.txt")
            save_report(proj, text_path)
            assert os.path.exists(text_path)

            # 保存 HTML 报告
            html_path = os.path.join(tmpdir, "coverage.html")
            save_report(proj, html_path)
            assert os.path.exists(html_path)

            # 保存 JSON 报告
            json_path = os.path.join(tmpdir, "coverage.json")
            save_report(proj, json_path)
            assert os.path.exists(json_path)


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_start_stop_coverage(self):
        """测试开始/停止覆盖率"""
        reset_coverage()

        start_coverage()
        cov = get_coverage()
        assert cov is not None

        stop_coverage()

    def test_reset_coverage(self):
        """测试重置覆盖率"""
        reset_coverage()
        cov = get_coverage()
        assert cov.total_lines == 0

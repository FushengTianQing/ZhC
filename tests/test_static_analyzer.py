"""
静态分析框架测试

Phase 4 - Stage 3 - Task 14.3
"""

import pytest
from typing import List, Dict, Any

from zhc.analysis.base_analyzer import (
    StaticAnalyzer,
    AnalysisResult,
    SourceLocation,
    Severity,
    ASTWalker,
)
from zhc.analysis.analyzer_scheduler import AnalysisScheduler, AnalysisStats
from zhc.analysis.report_generator import ReportGenerator


# ========== 测试辅助类 ==========

class MockAnalyzer(StaticAnalyzer):
    """测试用模拟分析器"""
    
    @property
    def name(self) -> str:
        return "mock_analyzer"
    
    def analyze(self, ast: Any, context: Dict[str, Any]) -> List[AnalysisResult]:
        results = []
        # 生成一些测试结果
        results.append(self.add_result(
            message="测试警告",
            location=SourceLocation("test.zhc", 10, 5),
            severity=Severity.WARNING
        ))
        results.append(self.add_result(
            message="测试错误",
            location=SourceLocation("test.zhc", 20, 10),
            severity=Severity.ERROR
        ))
        return results


class MockASTNode:
    """测试用模拟 AST 节点"""
    
    def __init__(self, name: str, node_type: str, children: List['MockASTNode'] = None):
        self.name = name
        self.node_type = node_type
        self.children = children or []
    
    def walk(self):
        """模拟 walk 方法"""
        nodes = [self]
        for child in self.children:
            nodes.extend(child.walk())
        return nodes


# ========== 测试基础类 ==========

class TestAnalysisResult:
    """测试分析结果"""
    
    def test_result_creation(self):
        """测试结果创建"""
        location = SourceLocation("test.zhc", 10, 5)
        result = AnalysisResult(
            analyzer="test",
            severity=Severity.WARNING,
            message="测试消息",
            location=location
        )
        
        assert result.analyzer == "test"
        assert result.severity == Severity.WARNING
        assert result.message == "测试消息"
        assert result.location.line == 10
    
    def test_result_to_dict(self):
        """测试结果转字典"""
        location = SourceLocation("test.zhc", 10, 5)
        result = AnalysisResult(
            analyzer="test",
            severity=Severity.WARNING,
            message="测试消息",
            location=location
        )
        
        d = result.to_dict()
        assert d['analyzer'] == "test"
        assert d['severity'] == "warning"
        assert d['message'] == "测试消息"
    
    def test_result_str(self):
        """测试结果字符串"""
        location = SourceLocation("test.zhc", 10, 5)
        result = AnalysisResult(
            analyzer="test",
            severity=Severity.WARNING,
            message="测试消息",
            location=location,
            suggestion="建议内容"
        )
        
        s = str(result)
        assert "WARNING" in s
        assert "测试消息" in s
        assert "建议内容" in s


class TestSourceLocation:
    """测试源码位置"""
    
    def test_location_creation(self):
        """测试位置创建"""
        loc = SourceLocation("test.zhc", 10, 5)
        
        assert loc.file_path == "test.zhc"
        assert loc.line == 10
        assert loc.column == 5
    
    def test_location_str(self):
        """测试位置字符串"""
        loc = SourceLocation("test.zhc", 10, 5)
        assert str(loc) == "test.zhc:10:5"
        
        loc2 = SourceLocation("test.zhc", 10, 5, 20, 10)
        assert "20" in str(loc2)
    
    def test_location_dict(self):
        """测试位置转字典"""
        loc = SourceLocation("test.zhc", 10, 5)
        d = loc.to_dict()
        
        assert d['file'] == "test.zhc"
        assert d['line'] == 10


class TestSeverity:
    """测试严重程度枚举"""
    
    def test_severity_values(self):
        """测试严重程度值"""
        assert Severity.ERROR.value == "error"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"
        assert Severity.HINT.value == "hint"


# ========== 测试调度器 ==========

class TestAnalysisScheduler:
    """测试分析调度器"""
    
    def test_scheduler_creation(self):
        """测试调度器创建"""
        scheduler = AnalysisScheduler()
        
        assert scheduler is not None
        assert len(scheduler.analyzers) == 0
    
    def test_register_analyzer(self):
        """测试注册分析器"""
        scheduler = AnalysisScheduler()
        analyzer = MockAnalyzer()
        
        scheduler.register(analyzer)
        
        assert len(scheduler.analyzers) == 1
        assert analyzer.name in scheduler.analyzer_names
    
    def test_unregister_analyzer(self):
        """测试注销分析器"""
        scheduler = AnalysisScheduler()
        analyzer = MockAnalyzer()
        scheduler.register(analyzer)
        
        result = scheduler.unregister(analyzer.name)
        
        assert result is True
        assert len(scheduler.analyzers) == 0
    
    def test_enable_disable_analyzer(self):
        """测试启用/禁用分析器"""
        scheduler = AnalysisScheduler()
        analyzer = MockAnalyzer()
        scheduler.register(analyzer)
        
        scheduler.disable_analyzer(analyzer.name)
        assert scheduler.is_enabled(analyzer.name) is False
        
        scheduler.enable_analyzer(analyzer.name)
        assert scheduler.is_enabled(analyzer.name) is True
    
    def test_run_all_analyzers(self):
        """测试运行所有分析器"""
        scheduler = AnalysisScheduler()
        scheduler.register(MockAnalyzer())
        
        results = scheduler.run_all(MockASTNode("root", "Program"))
        
        assert "mock_analyzer" in results
        assert len(results["mock_analyzer"]) == 2
    
    def test_get_all_results(self):
        """测试获取所有结果"""
        scheduler = AnalysisScheduler()
        scheduler.register(MockAnalyzer())
        
        scheduler.run_all(MockASTNode("root", "Program"))
        all_results = scheduler.get_all_results()
        
        assert len(all_results) == 2
    
    def test_filter_by_severity(self):
        """测试按严重程度过滤"""
        scheduler = AnalysisScheduler()
        scheduler.register(MockAnalyzer())
        
        scheduler.run_all(MockASTNode("root", "Program"))
        
        errors = scheduler.filter_by_severity(Severity.ERROR)
        warnings = scheduler.filter_by_severity(Severity.WARNING)
        
        assert len(errors) == 1
        assert len(warnings) == 1
    
    def test_has_errors(self):
        """测试是否有错误"""
        scheduler = AnalysisScheduler()
        scheduler.register(MockAnalyzer())
        
        scheduler.run_all(MockASTNode("root", "Program"))
        
        assert scheduler.has_errors() is True
    
    def test_stats(self):
        """测试统计信息"""
        scheduler = AnalysisScheduler()
        scheduler.register(MockAnalyzer())
        
        scheduler.run_all(MockASTNode("root", "Program"))
        
        assert scheduler.stats.total_analyzers == 1
        assert scheduler.stats.total_issues == 2
        assert scheduler.stats.errors == 1
        assert scheduler.stats.warnings == 1


# ========== 测试 AST 遍历器 ==========

class TestASTWalker:
    """测试 AST 遍历器"""
    
    def test_walker_creation(self):
        """测试遍历器创建"""
        node = MockASTNode("root", "Program")
        walker = ASTWalker(node)
        
        assert walker.ast == node
    
    def test_walk(self):
        """测试遍历"""
        child1 = MockASTNode("child1", "Type")
        child2 = MockASTNode("child2", "Type")
        root = MockASTNode("root", "Program", [child1, child2])
        
        walker = ASTWalker(root)
        nodes = walker.walk()
        
        # ASTWalker 遍历所有属性，包括方法。过滤掉方法，只保留节点
        actual_nodes = [n for n in nodes if isinstance(n, MockASTNode)]
        assert len(actual_nodes) == 3
    
    def test_find_nodes(self):
        """测试查找节点"""
        child = MockASTNode("child", "FunctionDecl")
        root = MockASTNode("root", "Program", [child])
        
        walker = ASTWalker(root)
        # find_nodes 期望 type 类型参数，使用 MockASTNode 类
        nodes = walker.find_nodes(MockASTNode)
        
        assert len(nodes) == 2  # root + child


# ========== 测试报告生成器 ==========

class TestReportGenerator:
    """测试报告生成器"""
    
    def test_generator_creation(self):
        """测试生成器创建"""
        scheduler = AnalysisScheduler()
        scheduler.register(MockAnalyzer())
        scheduler.run_all(MockASTNode("root", "Program"))
        
        generator = ReportGenerator(scheduler.results, scheduler.stats)
        
        assert generator is not None
    
    def test_generate_text(self):
        """测试生成文本报告"""
        scheduler = AnalysisScheduler()
        scheduler.register(MockAnalyzer())
        scheduler.run_all(MockASTNode("root", "Program"))
        
        generator = ReportGenerator(scheduler.results, scheduler.stats)
        report = generator.generate_text()
        
        assert "静态分析报告" in report
        assert "总问题数" in report
    
    def test_generate_markdown(self):
        """测试生成 Markdown 报告"""
        scheduler = AnalysisScheduler()
        scheduler.register(MockAnalyzer())
        scheduler.run_all(MockASTNode("root", "Program"))
        
        generator = ReportGenerator(scheduler.results, scheduler.stats)
        report = generator.generate_markdown()
        
        assert "# 静态分析报告" in report
        assert "## 统计摘要" in report
    
    def test_generate_json(self):
        """测试生成 JSON 报告"""
        scheduler = AnalysisScheduler()
        scheduler.register(MockAnalyzer())
        scheduler.run_all(MockASTNode("root", "Program"))
        
        generator = ReportGenerator(scheduler.results, scheduler.stats)
        report = generator.generate_json()
        
        import json
        data = json.loads(report)
        
        assert "stats" in data
        assert "results" in data
    
    def test_generate_html(self):
        """测试生成 HTML 报告"""
        scheduler = AnalysisScheduler()
        scheduler.register(MockAnalyzer())
        scheduler.run_all(MockASTNode("root", "Program"))
        
        generator = ReportGenerator(scheduler.results, scheduler.stats)
        report = generator.generate_html()
        
        assert "<!DOCTYPE html>" in report
        assert "静态分析报告" in report


# ========== 测试内置分析器 ==========

class TestBuiltinAnalyzers:
    """测试内置分析器导入"""
    
    def test_import_analyzers(self):
        """测试导入内置分析器"""
        from zhc.analysis import (
            UnusedVariableAnalyzer,
            NullPointerAnalyzer,
            ResourceLeakAnalyzer,
            ComplexityAnalyzer,
        )
        
        assert UnusedVariableAnalyzer is not None
        assert NullPointerAnalyzer is not None
        assert ResourceLeakAnalyzer is not None
        assert ComplexityAnalyzer is not None
    
    def test_create_default_scheduler(self):
        """测试创建默认调度器"""
        from zhc.analysis import create_default_scheduler
        
        scheduler = create_default_scheduler()
        
        assert len(scheduler.analyzers) == 7
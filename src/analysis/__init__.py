"""
静态分析框架

提供代码质量检查、安全漏洞检测等功能。

Phase 4 - Stage 3 - Task 14.3
"""

from zhc.analysis.base_analyzer import (
    StaticAnalyzer,
    AnalysisResult,
    SourceLocation,
    Severity,
    ASTWalker,
    get_node_location,
    get_node_name,
)

from zhc.analysis.analyzer_scheduler import (
    AnalysisScheduler,
    AnalysisStats,
)

from zhc.analysis.unused_variable_analyzer import UnusedVariableAnalyzer
from zhc.analysis.null_pointer_analyzer import NullPointerAnalyzer, DivisionByZeroAnalyzer
from zhc.analysis.resource_leak_analyzer import ResourceLeakAnalyzer
from zhc.analysis.complexity_analyzer import ComplexityAnalyzer, CodeSmellAnalyzer, DeadCodeAnalyzer
from zhc.analysis.report_generator import ReportGenerator

__all__ = [
    # 基础类
    'StaticAnalyzer',
    'AnalysisResult',
    'SourceLocation',
    'Severity',
    'ASTWalker',
    
    # 调度器
    'AnalysisScheduler',
    'AnalysisStats',
    
    # 内置分析器
    'UnusedVariableAnalyzer',
    'NullPointerAnalyzer',
    'DivisionByZeroAnalyzer',
    'ResourceLeakAnalyzer',
    'ComplexityAnalyzer',
    'CodeSmellAnalyzer',
    'DeadCodeAnalyzer',
    
    # 报告生成
    'ReportGenerator',
    
    # 工具函数
    'get_node_location',
    'get_node_name',
]


def create_default_scheduler() -> AnalysisScheduler:
    """
    创建默认的分析调度器
    
    注册所有内置分析器。
    
    Returns:
        配置好的 AnalysisScheduler 实例
    """
    scheduler = AnalysisScheduler()
    
    # 注册内置分析器
    scheduler.register(UnusedVariableAnalyzer())
    scheduler.register(NullPointerAnalyzer())
    scheduler.register(DivisionByZeroAnalyzer())
    scheduler.register(ResourceLeakAnalyzer())
    scheduler.register(ComplexityAnalyzer())
    scheduler.register(CodeSmellAnalyzer())
    scheduler.register(DeadCodeAnalyzer())
    
    return scheduler
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

    # 分析器工厂函数
    'create_default_scheduler',
    'create_security_analyzers',
    'create_quality_analyzers',
    'create_security_scheduler',
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


def create_security_analyzers() -> list:
    """
    创建安全分析器（默认启用，会阻止编译）

    这些分析器检测关键安全漏洞，发现错误时会阻止编译。

    Returns:
        安全分析器列表
    """
    return [
        DivisionByZeroAnalyzer(),    # ERROR 级别：除零错误
        NullPointerAnalyzer(),       # WARNING 级别：空指针检测
        ResourceLeakAnalyzer(),      # WARNING 级别：资源泄漏检测
    ]


def create_quality_analyzers() -> list:
    """
    创建质量分析器（--analyze 启用，不阻止编译）

    这些分析器用于代码质量检查，仅生成报告，不阻止编译。

    Returns:
        质量分析器列表
    """
    return [
        UnusedVariableAnalyzer(),    # WARNING 级别
        ComplexityAnalyzer(),         # INFO 级别
        CodeSmellAnalyzer(),         # INFO 级别
        DeadCodeAnalyzer(),          # WARNING 级别
    ]


def create_security_scheduler() -> AnalysisScheduler:
    """
    创建安全分析调度器（默认启用）

    用于编译流程中的安全检查，发现错误会阻止编译。

    Returns:
        配置好的 AnalysisScheduler 实例（仅包含安全分析器）
    """
    scheduler = AnalysisScheduler()

    # 注册安全分析器
    for analyzer in create_security_analyzers():
        scheduler.register(analyzer)

    return scheduler
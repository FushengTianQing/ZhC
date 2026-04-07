"""
静态分析调度器

协调多个分析器的执行，生成分析报告。

Phase 4 - Stage 3 - Task 14.3
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from zhc.analysis.base_analyzer import (
    StaticAnalyzer,
    AnalysisResult,
    Severity,
)


@dataclass
class AnalysisStats:
    """分析统计信息"""
    total_analyzers: int = 0
    total_issues: int = 0
    errors: int = 0
    warnings: int = 0
    infos: int = 0
    hints: int = 0
    execution_time: float = 0.0
    analyzer_times: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_analyzers': self.total_analyzers,
            'total_issues': self.total_issues,
            'errors': self.errors,
            'warnings': self.warnings,
            'infos': self.infos,
            'hints': self.hints,
            'execution_time': self.execution_time,
            'analyzer_times': self.analyzer_times
        }


class AnalysisScheduler:
    """
    静态分析调度器
    
    管理和协调多个静态分析器的执行。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化调度器
        
        Args:
            config: 调度器配置
        """
        self.config = config or {}
        self._analyzers: List[StaticAnalyzer] = []
        self._enabled_analyzers: Dict[str, bool] = {}
        self._results: Dict[str, List[AnalysisResult]] = {}
        self._stats = AnalysisStats()
    
    def register(self, analyzer: StaticAnalyzer) -> None:
        """
        注册分析器
        
        Args:
            analyzer: 静态分析器实例
        """
        if analyzer not in self._analyzers:
            self._analyzers.append(analyzer)
            self._enabled_analyzers[analyzer.name] = True
    
    def unregister(self, analyzer_name: str) -> bool:
        """
        注销分析器
        
        Args:
            analyzer_name: 分析器名称
            
        Returns:
            是否成功注销
        """
        for i, analyzer in enumerate(self._analyzers):
            if analyzer.name == analyzer_name:
                self._analyzers.pop(i)
                self._enabled_analyzers.pop(analyzer_name, None)
                return True
        return False
    
    def enable_analyzer(self, analyzer_name: str) -> None:
        """启用分析器"""
        self._enabled_analyzers[analyzer_name] = True
    
    def disable_analyzer(self, analyzer_name: str) -> None:
        """禁用分析器"""
        self._enabled_analyzers[analyzer_name] = False
    
    def is_enabled(self, analyzer_name: str) -> bool:
        """检查分析器是否启用"""
        return self._enabled_analyzers.get(analyzer_name, False)
    
    def get_analyzer(self, analyzer_name: str) -> Optional[StaticAnalyzer]:
        """获取分析器实例"""
        for analyzer in self._analyzers:
            if analyzer.name == analyzer_name:
                return analyzer
        return None
    
    def run_all(self, 
                ast: Any, 
                context: Optional[Dict[str, Any]] = None,
                parallel: bool = False) -> Dict[str, List[AnalysisResult]]:
        """
        运行所有启用的分析器
        
        Args:
            ast: AST 节点或 AST 树
            context: 分析上下文
            parallel: 是否并行执行
            
        Returns:
            分析结果字典 {分析器名称: 结果列表}
        """
        start_time = time.time()
        context = context or {}
        self._results.clear()
        self._stats = AnalysisStats()
        
        enabled = [a for a in self._analyzers if self.is_enabled(a.name)]
        self._stats.total_analyzers = len(enabled)
        
        if parallel:
            self._run_parallel(enabled, ast, context)
        else:
            self._run_sequential(enabled, ast, context)
        
        # 统计结果
        self._collect_stats()
        self._stats.execution_time = time.time() - start_time
        
        return self._results
    
    def _run_sequential(self, 
                       analyzers: List[StaticAnalyzer],
                       ast: Any,
                       context: Dict[str, Any]) -> None:
        """顺序执行分析器"""
        for analyzer in analyzers:
            start = time.time()
            try:
                results = analyzer.analyze(ast, context)
                self._results[analyzer.name] = results
            except Exception as e:
                # 分析器执行失败，记录错误
                self._results[analyzer.name] = []
                print(f"分析器 {analyzer.name} 执行失败: {e}")
            
            self._stats.analyzer_times[analyzer.name] = time.time() - start
    
    def _run_parallel(self,
                     analyzers: List[StaticAnalyzer],
                     ast: Any,
                     context: Dict[str, Any]) -> None:
        """并行执行分析器"""
        with ThreadPoolExecutor(max_workers=self.config.get('max_workers', 4)) as executor:
            futures = {}
            for analyzer in analyzers:
                future = executor.submit(analyzer.analyze, ast, context)
                futures[future] = analyzer
            
            for future in as_completed(futures):
                analyzer = futures[future]
                start = time.time()
                try:
                    results = future.result()
                    self._results[analyzer.name] = results
                except Exception as e:
                    self._results[analyzer.name] = []
                    print(f"分析器 {analyzer.name} 执行失败: {e}")
                
                self._stats.analyzer_times[analyzer.name] = time.time() - start
    
    def _collect_stats(self) -> None:
        """收集统计信息"""
        for results in self._results.values():
            for result in results:
                self._stats.total_issues += 1
                
                if result.severity == Severity.ERROR:
                    self._stats.errors += 1
                elif result.severity == Severity.WARNING:
                    self._stats.warnings += 1
                elif result.severity == Severity.INFO:
                    self._stats.infos += 1
                elif result.severity == Severity.HINT:
                    self._stats.hints += 1
    
    @property
    def results(self) -> Dict[str, List[AnalysisResult]]:
        """获取分析结果"""
        return self._results
    
    @property
    def stats(self) -> AnalysisStats:
        """获取统计信息"""
        return self._stats
    
    def get_all_results(self) -> List[AnalysisResult]:
        """获取所有分析结果的扁平列表"""
        all_results = []
        for results in self._results.values():
            all_results.extend(results)
        return all_results
    
    def filter_by_severity(self, severity: Severity) -> List[AnalysisResult]:
        """
        按严重程度过滤结果
        
        Args:
            severity: 严重程度
            
        Returns:
            过滤后的结果列表
        """
        return [r for r in self.get_all_results() if r.severity == severity]
    
    def filter_by_analyzer(self, analyzer_name: str) -> List[AnalysisResult]:
        """
        按分析器过滤结果
        
        Args:
            analyzer_name: 分析器名称
            
        Returns:
            过滤后的结果列表
        """
        return self._results.get(analyzer_name, [])
    
    def has_errors(self) -> bool:
        """是否有错误"""
        return self._stats.errors > 0
    
    def has_warnings(self) -> bool:
        """是否有警告"""
        return self._stats.warnings > 0
    
    @property
    def analyzers(self) -> List[StaticAnalyzer]:
        """获取所有注册的分析器"""
        return list(self._analyzers)
    
    @property
    def analyzer_names(self) -> List[str]:
        """获取所有分析器名称"""
        return [a.name for a in self._analyzers]
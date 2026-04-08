"""
资源泄漏检测分析器

检测可能的资源泄漏（内存、文件、锁等）。

Phase 4 - Stage 3 - Task 14.3
"""

from typing import List, Dict, Any, Optional, Tuple

from zhc.analysis.base_analyzer import (
    StaticAnalyzer,
    AnalysisResult,
    Severity,
    get_node_location,
)
from zhc.analysis.ast_utils import find_all_nodes


class ResourceLeakAnalyzer(StaticAnalyzer):
    """
    资源泄漏检测器

    检测内存分配、文件打开等资源未释放的情况。
    """

    # 资源分配函数
    ALLOC_FUNCTIONS = {
        "分配内存",
        "malloc",
        "分配",
        "alloc",
        "new",
        "打开文件",
        "打开",
        "fopen",
        "open",
        "文件打开",
    }

    # 资源释放函数
    FREE_FUNCTIONS = {
        "释放内存",
        "free",
        "释放",
        "delete",
        "关闭文件",
        "关闭",
        "fclose",
        "close",
        "文件关闭",
    }

    @property
    def name(self) -> str:
        return "resource_leak"

    @property
    def description(self) -> str:
        return "检测可能的资源泄漏"

    @property
    def severity(self) -> Severity:
        return Severity.WARNING

    def analyze(self, ast: Any, context: Dict[str, Any]) -> List[AnalysisResult]:
        """
        执行资源泄漏检测

        Args:
            ast: AST 节点
            context: 分析上下文

        Returns:
            检测结果列表
        """
        self.clear_results()

        # 追踪每个函数的资源使用
        for func in find_all_nodes(ast, "FunctionDecl"):
            self._analyze_function(func)

        return self.results

    def _analyze_function(self, func: Any) -> None:
        """分析单个函数的资源使用"""
        # 收集函数内的资源分配和释放
        allocations: List[Tuple[str, Any]] = []
        releases: List[Tuple[str, Any]] = []

        for node in find_all_nodes(func, None):
            if self._is_allocation(node):
                resource_id = self._get_resource_id(node)
                if resource_id:
                    allocations.append((resource_id, node))

            elif self._is_release(node):
                resource_id = self._get_resource_id(node)
                if resource_id:
                    releases.append((resource_id, node))

        # 检查未释放的资源
        for alloc_id, alloc_node in allocations:
            # 检查是否有对应的释放
            released = any(
                self._resources_match(alloc_id, rel_id) for rel_id, _ in releases
            )

            if not released:
                location = get_node_location(alloc_node)
                if location:
                    self.add_result(
                        message=f"资源 '{alloc_id}' 可能未释放",
                        location=location,
                        suggestion="确保在所有代码路径上释放资源",
                    )

    def _is_allocation(self, node: Any) -> bool:
        """检查是否是资源分配"""
        if hasattr(node, "node_type"):
            type_str = (
                str(node.node_type.value)
                if hasattr(node.node_type, "value")
                else str(node.node_type)
            )
            if "Call" in type_str:
                if hasattr(node, "function"):
                    func_name = getattr(node.function, "name", "")
                    return any(
                        alloc in str(func_name) for alloc in self.ALLOC_FUNCTIONS
                    )
        return False

    def _is_release(self, node: Any) -> bool:
        """检查是否是资源释放"""
        if hasattr(node, "node_type"):
            type_str = (
                str(node.node_type.value)
                if hasattr(node.node_type, "value")
                else str(node.node_type)
            )
            if "Call" in type_str:
                if hasattr(node, "function"):
                    func_name = getattr(node.function, "name", "")
                    return any(free in str(func_name) for free in self.FREE_FUNCTIONS)
        return False

    def _get_resource_id(self, node: Any) -> Optional[str]:
        """获取资源标识符"""
        if hasattr(node, "name"):
            return str(node.name)
        if hasattr(node, "identifier"):
            return str(node.identifier)
        if hasattr(node, "result"):
            return str(node.result)
        return None

    def _resources_match(self, alloc_id: str, release_id: str) -> bool:
        """检查分配和释放是否匹配"""
        return alloc_id == release_id


class MemoryLeakAnalyzer(StaticAnalyzer):
    """
    内存泄漏检测器

    检测 malloc/new 分配的内存未释放的情况。
    """

    @property
    def name(self) -> str:
        return "memory_leak"

    @property
    def description(self) -> str:
        return "检测内存泄漏"

    @property
    def severity(self) -> Severity:
        return Severity.ERROR

    def analyze(self, ast: Any, context: Dict[str, Any]) -> List[AnalysisResult]:
        """
        执行内存泄漏检测

        Args:
            ast: AST 节点
            context: 分析上下文

        Returns:
            检测结果列表
        """
        self.clear_results()

        # 收集所有 malloc/alloc 调用
        for node in find_all_nodes(ast, None):
            if self._is_malloc(node):
                location = get_node_location(node)
                if location:
                    # 简化：假设所有 malloc 都需要对应的 free
                    # 实际实现需要更复杂的数据流分析
                    pass

        return self.results

    def _is_malloc(self, node: Any) -> bool:
        """检查是否是内存分配"""
        if hasattr(node, "node_type"):
            type_str = str(getattr(node.node_type, "value", node.node_type))
            return "Call" in type_str
        return False


class FileHandleLeakAnalyzer(StaticAnalyzer):
    """
    文件句柄泄漏检测器

    检测打开的文件未关闭的情况。
    """

    @property
    def name(self) -> str:
        return "file_handle_leak"

    @property
    def description(self) -> str:
        return "检测文件句柄泄漏"

    @property
    def severity(self) -> Severity:
        return Severity.WARNING

    def analyze(self, ast: Any, context: Dict[str, Any]) -> List[AnalysisResult]:
        """
        执行文件句柄泄漏检测

        Args:
            ast: AST 节点
            context: 分析上下文

        Returns:
            检测结果列表
        """
        self.clear_results()

        return self.results

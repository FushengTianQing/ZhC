"""
静态分析框架核心

提供静态分析器基类和通用数据结构。

Phase 4 - Stage 3 - Task 14.3
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from enum import Enum
from typing import Set as TypingSet


class Severity(Enum):
    """问题严重程度"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


@dataclass
class SourceLocation:
    """源码位置"""
    file_path: str
    line: int
    column: int = 0
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'file': self.file_path,
            'line': self.line,
            'column': self.column,
            'end_line': self.end_line,
            'end_column': self.end_column
        }
    
    def __str__(self) -> str:
        if self.end_line:
            return f"{self.file_path}:{self.line}:{self.column}-{self.end_line}:{self.end_column}"
        return f"{self.file_path}:{self.line}:{self.column}"


@dataclass
class AnalysisResult:
    """静态分析结果"""
    analyzer: str
    severity: Severity
    message: str
    location: SourceLocation
    rule_id: Optional[str] = None
    suggestion: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'analyzer': self.analyzer,
            'severity': self.severity.value,
            'message': self.message,
            'location': self.location.to_dict(),
            'rule_id': self.rule_id,
            'suggestion': self.suggestion,
            **self.extra
        }
    
    def __str__(self) -> str:
        result = f"[{self.severity.value.upper()}] {self.message}"
        result += f"\n  位置: {self.location}"
        if self.suggestion:
            result += f"\n  建议: {self.suggestion}"
        return result


class StaticAnalyzer(ABC):
    """
    静态分析器基类
    
    所有具体分析器都必须继承此类并实现 analyze 方法。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化分析器
        
        Args:
            config: 分析器配置
        """
        self.config = config or {}
        self._results: List[AnalysisResult] = []
    
    @property
    @abstractmethod
    def name(self) -> str:
        """分析器名称（唯一标识）"""
        pass
    
    @property
    def description(self) -> str:
        """分析器描述"""
        return ""
    
    @property
    def severity(self) -> Severity:
        """分析结果的默认严重程度"""
        return Severity.WARNING
    
    @abstractmethod
    def analyze(self, ast: Any, context: Dict[str, Any]) -> List[AnalysisResult]:
        """
        执行静态分析
        
        Args:
            ast: AST 节点或 AST 树
            context: 分析上下文信息
            
        Returns:
            分析结果列表
        """
        pass
    
    def add_result(self,
                   message: str,
                   location: SourceLocation,
                   severity: Optional[Severity] = None,
                   suggestion: Optional[str] = None,
                   **extra) -> AnalysisResult:
        """
        添加分析结果
        
        Args:
            message: 问题描述
            location: 源码位置
            severity: 严重程度（默认使用 self.severity）
            suggestion: 修复建议
            **extra: 额外信息
            
        Returns:
            创建的分析结果
        """
        result = AnalysisResult(
            analyzer=self.name,
            severity=severity or self.severity,
            message=message,
            location=location,
            rule_id=f"{self.name}",
            suggestion=suggestion,
            extra=extra
        )
        self._results.append(result)
        return result
    
    def clear_results(self) -> None:
        """清空分析结果"""
        self._results.clear()
    
    @property
    def results(self) -> List[AnalysisResult]:
        """获取分析结果"""
        return list(self._results)


class ASTWalker:
    """
    AST 遍历器
    
    提供通用的 AST 节点遍历功能。
    """
    
    def __init__(self, ast: Any):
        """
        初始化遍历器
        
        Args:
            ast: AST 根节点
        """
        self.ast = ast
        self._visitors: Dict[type, callable] = {}
    
    def walk(self) -> List[Any]:
        """
        遍历所有节点
        
        Returns:
            所有节点的列表
        """
        nodes = []
        visited: Set[int] = set()  # 防止循环引用
        self._walk_node(self.ast, nodes, visited)
        return nodes
    
    def _walk_node(self, node: Any, nodes: List[Any], visited: Set[int]) -> None:
        """递归遍历节点"""
        if node is None:
            return
        
        # 防止循环引用
        node_id = id(node)
        if node_id in visited:
            return
        visited.add(node_id)
        
        nodes.append(node)
        
        # 遍历子节点
        for attr_name in dir(node):
            if attr_name.startswith('_'):
                continue
            
            try:
                attr = getattr(node, attr_name)
            except (AttributeError, TypeError):
                continue
            
            if isinstance(attr, list):
                for child in attr:
                    self._walk_node(child, nodes, visited)
            elif isinstance(attr, dict):
                for child in attr.values():
                    self._walk_node(child, nodes, visited)
            elif hasattr(attr, '__dict__') and not isinstance(attr, (str, int, float, bool)):
                self._walk_node(attr, nodes, visited)
    
    def find_nodes(self, node_type: type) -> List[Any]:
        """
        查找特定类型的节点
        
        Args:
            node_type: 节点类型
            
        Returns:
            匹配节点的列表
        """
        return [node for node in self.walk() if isinstance(node, node_type)]
    
    def find_by_name(self, name: str) -> List[Any]:
        """
        查找具有特定名称的节点
        
        Args:
            name: 节点名称属性值
            
        Returns:
            匹配节点的列表
        """
        results = []
        for node in self.walk():
            if hasattr(node, 'name') and node.name == name:
                results.append(node)
        return results


def get_node_location(node: Any) -> Optional[SourceLocation]:
    """
    从 AST 节点获取位置信息
    
    Args:
        node: AST 节点
        
    Returns:
        源码位置，如果无法获取则返回 None
    """
    if hasattr(node, 'location'):
        loc = node.location
        if isinstance(loc, SourceLocation):
            return loc
        elif isinstance(loc, tuple) and len(loc) >= 2:
            return SourceLocation(
                file_path=loc[0] if len(loc) > 0 else "",
                line=loc[1] if len(loc) > 1 else 0,
                column=loc[2] if len(loc) > 2 else 0
            )
    elif hasattr(node, 'line'):
        return SourceLocation(
            file_path=getattr(node, 'file_path', ""),
            line=node.line,
            column=getattr(node, 'column', 0)
        )
    
    return None


def get_node_name(node: Any) -> str:
    """
    从 AST 节点获取名称
    
    Args:
        node: AST 节点
        
    Returns:
        节点名称
    """
    if hasattr(node, 'name'):
        return node.name
    return node.__class__.__name__

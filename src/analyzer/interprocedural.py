#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
过程间分析器 - Interprocedural Analyzer

功能：
1. 函数调用图构建（Call Graph）
2. 过程间常量传播
3. 过程间类型推导
4. 函数副作用分析
5. 上下文敏感分析

作者：远
日期：2026-04-03
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class CallType(Enum):
    """调用类型"""
    DIRECT = "直接调用"      # 直接函数调用：func()
    INDIRECT = "间接调用"   # 函数指针调用：ptr()
    VIRTUAL = "虚函数调用"  # 多态调用：obj.method()
    INTRINSIC = "内置调用"  # 内置函数：zhc_printf()


class SideEffect(Enum):
    """副作用类型"""
    READ_GLOBAL = "读取全局变量"
    WRITE_GLOBAL = "写入全局变量"
    READ_MEMORY = "读取内存"
    WRITE_MEMORY = "写入内存"
    IO_OPERATION = "IO操作"
    EXCEPTION = "可能抛出异常"
    UNKNOWN = "未知"


@dataclass
class CallSite:
    """调用点"""
    caller: str              # 调用者函数名
    callee: str              # 被调用者函数名
    line_number: int         # 调用位置行号
    call_type: CallType      # 调用类型
    arguments: List[str] = field(default_factory=list)  # 实参列表
    return_value: Optional[str] = None  # 返回值接收变量
    context: str = ""        # 调用上下文


@dataclass
class FunctionSummary:
    """函数摘要"""
    name: str                          # 函数名
    parameters: List[str] = field(default_factory=list)  # 参数列表
    return_type: Optional[str] = None  # 返回类型
    
    # 副作用信息
    side_effects: Set[SideEffect] = field(default_factory=set)
    modifies_globals: Set[str] = field(default_factory=set)  # 修改的全局变量
    reads_globals: Set[str] = field(default_factory=set)     # 读取的全局变量
    
    # 类型信息
    parameter_types: List[str] = field(default_factory=list)
    
    # 常量传播信息
    constant_params: Dict[int, Any] = field(default_factory=dict)  # 参数索引 -> 常量值
    
    # 是否纯函数（无副作用）
    is_pure: bool = False
    
    # 是否已分析
    is_analyzed: bool = False


@dataclass
class CallGraph:
    """调用图"""
    nodes: Dict[str, Set[str]] = field(default_factory=dict)  # 函数 -> 调用的函数集合
    reverse_nodes: Dict[str, Set[str]] = field(default_factory=dict)  # 函数 -> 被谁调用
    call_sites: Dict[str, List[CallSite]] = field(default_factory=list)  # 函数 -> 调用点列表
    
    def add_edge(self, caller: str, callee: str):
        """添加调用边"""
        if caller not in self.nodes:
            self.nodes[caller] = set()
        self.nodes[caller].add(callee)
        
        if callee not in self.reverse_nodes:
            self.reverse_nodes[callee] = set()
        self.reverse_nodes[callee].add(caller)
    
    def get_callees(self, func: str) -> Set[str]:
        """获取函数调用的所有函数"""
        return self.nodes.get(func, set())
    
    def get_callers(self, func: str) -> Set[str]:
        """获取调用该函数的所有函数"""
        return self.reverse_nodes.get(func, set())


class InterproceduralAnalyzer:
    """过程间分析器"""
    
    def __init__(self):
        self.call_graph = CallGraph()
        self.function_summaries: Dict[str, FunctionSummary] = {}
        self.call_sites: List[CallSite] = []
        self.recursion_detected: List[List[str]] = []
        
    # ==================== 调用图构建 ====================
    
    def build_call_graph(self, functions: List[dict]) -> CallGraph:
        """
        构建调用图
        
        Args:
            functions: 函数定义列表
        
        Returns:
            调用图
        """
        # 第一遍：收集所有函数定义
        for func in functions:
            func_name = func.get('name', '')
            if not func_name:
                continue
            
            # 创建函数摘要
            summary = FunctionSummary(
                name=func_name,
                parameters=func.get('params', []),
                return_type=func.get('return_type'),
                parameter_types=func.get('param_types', [])
            )
            self.function_summaries[func_name] = summary
            
            # 初始化调用图节点
            if func_name not in self.call_graph.nodes:
                self.call_graph.nodes[func_name] = set()
        
        # 第二遍：分析函数体中的调用
        for func in functions:
            func_name = func.get('name', '')
            if not func_name:
                continue
            
            statements = func.get('body', [])
            self._analyze_function_calls(func_name, statements)
        
        # 检测递归
        self._detect_recursion()
        
        return self.call_graph
    
    def _analyze_function_calls(self, func_name: str, statements: List[dict]):
        """分析函数体中的调用"""
        for stmt in statements:
            stmt_type = stmt.get('type', '')
            line = stmt.get('line', 0)
            
            # 函数调用
            if stmt_type == 'call':
                callee = stmt.get('function', '')
                if callee:
                    call_site = CallSite(
                        caller=func_name,
                        callee=callee,
                        line_number=line,
                        call_type=CallType.DIRECT,
                        arguments=stmt.get('args', []),
                        return_value=stmt.get('result')
                    )
                    self.call_sites.append(call_site)
                    self.call_graph.add_edge(func_name, callee)
            
            # 递归分析嵌套语句
            if 'body' in stmt:
                self._analyze_function_calls(func_name, stmt['body'])
            
            if 'then_body' in stmt:
                self._analyze_function_calls(func_name, stmt['then_body'])
            
            if 'else_body' in stmt:
                self._analyze_function_calls(func_name, stmt['else_body'])
    
    def _detect_recursion(self):
        """检测递归调用"""
        visited = set()
        recursion_stack = []
        
        for func in self.call_graph.nodes:
            if func not in visited:
                self._dfs_recursion(func, visited, recursion_stack, [])
    
    def _dfs_recursion(self, func: str, visited: Set, stack: List, path: List):
        """深度优先搜索检测递归"""
        if func in stack:
            # 找到循环
            cycle_start = stack.index(func)
            cycle = stack[cycle_start:] + [func]
            self.recursion_detected.append(cycle)
            return
        
        if func in visited:
            return
        
        visited.add(func)
        stack.append(func)
        path.append(func)
        
        for callee in self.call_graph.get_callees(func):
            self._dfs_recursion(callee, visited, stack, path)
        
        stack.pop()
        path.pop()
    
    # ==================== 副作用分析 ====================
    
    def analyze_side_effects(self, func_name: str, statements: List[dict]) -> FunctionSummary:
        """
        分析函数副作用
        
        Args:
            func_name: 函数名
            statements: 函数体
        
        Returns:
            函数摘要
        """
        summary = self.function_summaries.get(func_name)
        if not summary:
            summary = FunctionSummary(name=func_name)
            self.function_summaries[func_name] = summary
        
        # 分析语句
        self._analyze_side_effects_in_statements(func_name, statements, summary)
        
        # 判断是否纯函数
        summary.is_pure = len(summary.side_effects) == 0 and len(summary.modifies_globals) == 0
        summary.is_analyzed = True
        
        return summary
    
    def _analyze_side_effects_in_statements(
        self,
        func_name: str,
        statements: List[dict],
        summary: FunctionSummary
    ):
        """分析语句中的副作用"""
        for stmt in statements:
            stmt_type = stmt.get('type', '')
            
            # 全局变量访问
            if stmt_type in ('read_global', 'write_global'):
                var_name = stmt.get('name', '')
                if stmt_type == 'read_global':
                    summary.reads_globals.add(var_name)
                    summary.side_effects.add(SideEffect.READ_GLOBAL)
                else:
                    summary.modifies_globals.add(var_name)
                    summary.side_effects.add(SideEffect.WRITE_GLOBAL)
            
            # 内存操作
            if stmt_type in ('dereference', 'pointer_write'):
                summary.side_effects.add(SideEffect.READ_MEMORY if 'read' in stmt_type else SideEffect.WRITE_MEMORY)
            
            # IO操作
            if stmt_type == 'call':
                callee = stmt.get('function', '')
                # 内置函数通常有IO副作用
                if callee in ['zhc_printf', 'zhc_read_int', 'zhc_read_string']:
                    summary.side_effects.add(SideEffect.IO_OPERATION)
            
            # 递归分析
            if 'body' in stmt:
                self._analyze_side_effects_in_statements(func_name, stmt['body'], summary)
    
    # ==================== 过程间常量传播 ====================
    
    def propagate_constants_interprocedurally(
        self,
        func_name: str,
        constants: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        过程间常量传播
        
        Args:
            func_name: 函数名
            constants: 已知常量（参数值）
        
        Returns:
            传播后的常量信息
        """
        summary = self.function_summaries.get(func_name)
        if not summary:
            return constants
        
        # 获取调用该函数的所有位置
        callers = self.call_graph.get_callers(func_name)
        
        propagated = {}
        for caller in callers:
            # 获取调用点的实参
            for site in self.call_sites:
                if site.caller == caller and site.callee == func_name:
                    # 传播常量参数
                    for i, arg in enumerate(site.arguments):
                        if arg in constants:
                            propagated[f"param_{i}"] = constants[arg]
        
        return propagated
    
    # ==================== 类型推导 ====================
    
    def infer_return_type(self, func_name: str) -> Optional[str]:
        """
        推导函数返回类型
        
        Args:
            func_name: 函数名
        
        Returns:
            推导的返回类型
        """
        summary = self.function_summaries.get(func_name)
        if not summary or summary.return_type:
            return summary.return_type if summary else None
        
        # 分析所有调用点的返回值使用
        return_types = set()
        for site in self.call_sites:
            if site.callee == func_name and site.return_value:
                # 根据返回值的使用推断类型
                # 这里简化处理，实际需要更复杂的类型推导
                pass
        
        return summary.return_type
    
    # ==================== 上下文敏感分析 ====================
    
    def analyze_with_context(
        self,
        func_name: str,
        context: str,
        known_types: Dict[str, str]
    ) -> Dict[str, str]:
        """
        上下文敏感分析
        
        Args:
            func_name: 函数名
            context: 调用上下文
            known_types: 已知类型信息
        
        Returns:
            分析得到的类型信息
        """
        summary = self.function_summaries.get(func_name)
        if not summary:
            return {}
        
        # 简化实现：根据上下文调整参数类型
        inferred_types = {}
        for i, param in enumerate(summary.parameters):
            param_type = summary.parameter_types[i] if i < len(summary.parameter_types) else None
            if param_type:
                inferred_types[param] = param_type
        
        return inferred_types
    
    # ==================== 报告生成 ====================
    
    def generate_report(self) -> str:
        """生成分析报告"""
        lines = [
            "=" * 70,
            "过程间分析报告",
            "=" * 70,
            ""
        ]
        
        # 调用图统计
        lines.append("调用图统计：")
        lines.append(f"  函数数：{len(self.call_graph.nodes)}")
        lines.append(f"  调用边数：{sum(len(v) for v in self.call_graph.nodes.values())}")
        lines.append("")
        
        # 递归检测
        if self.recursion_detected:
            lines.append("递归调用：")
            for cycle in self.recursion_detected:
                lines.append(f"  {' -> '.join(cycle)}")
            lines.append("")
        
        # 函数摘要
        lines.append("函数摘要：")
        for name, summary in self.function_summaries.items():
            lines.append(f"\n  函数：{name}")
            lines.append(f"    参数：{', '.join(summary.parameters)}")
            lines.append(f"    返回类型：{summary.return_type or '未知'}")
            lines.append(f"    纯函数：{'是' if summary.is_pure else '否'}")
            if summary.side_effects:
                effects = [e.value for e in summary.side_effects]
                lines.append(f"    副作用：{', '.join(effects)}")
            if summary.modifies_globals:
                lines.append(f"    修改全局变量：{', '.join(summary.modifies_globals)}")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)


# 测试代码
if __name__ == '__main__':
    print("=== 过程间分析器测试 ===\n")
    
    analyzer = InterproceduralAnalyzer()
    
    # 测试函数定义
    test_functions = [
        {
            'name': '主函数',
            'params': [],
            'return_type': '整数型',
            'body': [
                {'type': 'var_decl', 'name': 'x', 'value': 10, 'line': 2},
                {'type': 'call', 'function': '计算', 'args': ['x'], 'result': 'y', 'line': 3},
                {'type': 'return', 'value': 'y', 'line': 4}
            ]
        },
        {
            'name': '计算',
            'params': ['n'],
            'param_types': ['整数型'],
            'return_type': '整数型',
            'body': [
                {'type': 'if', 'condition': 'n <= 1', 'line': 7,
                 'then_body': [{'type': 'return', 'value': 'n', 'line': 8}],
                 'else_body': [
                     {'type': 'call', 'function': '计算', 'args': ['n - 1'], 'result': 'r', 'line': 10},
                     {'type': 'return', 'value': 'n * r', 'line': 11}
                 ]}
            ]
        }
    ]
    
    # 构建调用图
    cg = analyzer.build_call_graph(test_functions)
    print(f"调用图节点数：{len(cg.nodes)}")
    print(f"调用边：")
    for caller, callees in cg.nodes.items():
        print(f"  {caller} -> {', '.join(callees) if callees else '无'}")
    
    # 检测递归
    if analyzer.recursion_detected:
        print(f"\n检测到递归：")
        for cycle in analyzer.recursion_detected:
            print(f"  {' -> '.join(cycle)}")
    
    # 分析副作用
    print("\n副作用分析：")
    for func in test_functions:
        summary = analyzer.analyze_side_effects(func['name'], func['body'])
        print(f"  {func['name']}: 纯函数={summary.is_pure}")
    
    # 生成报告
    print("\n" + analyzer.generate_report())
    
    print("\n=== 测试完成 ===")
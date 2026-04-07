#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
过程间别名分析器 - Interprocedural Alias Analyzer

功能：
1. 跨函数指针别名追踪
2. 函数调用图分析
3. 参数别名传播
4. 返回值别名追踪
5. 全局变量别名分析

算法：
- 基于调用图的数据流分析
- 迭代求解直到不动点
- 支持 Andersen 风格的包含分析

作者：阿福
日期：2026-04-08
"""

from typing import Dict, List, Optional, Set, Tuple, FrozenSet
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class AliasKind(Enum):
    """别名类型"""
    MUST_ALIAS = "必须别名"       # 确定别名
    MAY_ALIAS = "可能别名"        # 可能别名
    NO_ALIAS = "非别名"           # 确定非别名
    UNKNOWN = "未知"


@dataclass
class AllocationSite:
    """分配点信息"""
    id: int                      # 分配点ID
    function: str                # 所在函数
    line: int                    # 行号
    is_heap: bool = False        # 是否堆分配
    is_param: bool = False       # 是否参数
    is_global: bool = False      # 是否全局变量
    var_name: str = ""           # 变量名
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, AllocationSite):
            return self.id == other.id
        return False


@dataclass
class PointsToSet:
    """指向集合"""
    targets: Set[AllocationSite] = field(default_factory=set)
    
    def add(self, site: AllocationSite):
        self.targets.add(site)
    
    def update(self, other: 'PointsToSet'):
        self.targets.update(other.targets)
    
    def may_point_to(self, site: AllocationSite) -> bool:
        return site in self.targets
    
    def copy(self) -> 'PointsToSet':
        return PointsToSet(self.targets.copy())
    
    def __len__(self):
        return len(self.targets)
    
    def __iter__(self):
        return iter(self.targets)


@dataclass
class FunctionAliasInfo:
    """函数别名信息"""
    name: str                                    # 函数名
    params: List[str] = field(default_factory=list)  # 参数列表
    param_sites: Dict[str, AllocationSite] = field(default_factory=dict)  # 参数分配点
    local_vars: Set[str] = field(default_factory=set)  # 局部变量
    points_to: Dict[str, PointsToSet] = field(default_factory=dict)  # 变量指向集合
    return_sites: Set[AllocationSite] = field(default_factory=set)  # 返回值可能的分配点
    calls: List[Tuple[str, Dict[str, str]]] = field(default_factory=list)  # 调用其他函数 (callee, arg_map)
    called_by: Set[str] = field(default_factory=set)  # 被哪些函数调用
    
    def get_points_to(self, var: str) -> PointsToSet:
        if var not in self.points_to:
            self.points_to[var] = PointsToSet()
        return self.points_to[var]


@dataclass 
class CallSite:
    """调用点信息"""
    id: int                      # 调用点ID
    caller: str                  # 调用函数
    callee: str                  # 被调函数
    line: int                    # 行号
    arg_mapping: Dict[str, str]  # 实参到形参映射 {形参: 实参}
    return_var: Optional[str]    # 返回值存储变量
    
    def __hash__(self):
        return hash(self.id)


class InterproceduralAliasAnalyzer:
    """过程间别名分析器"""
    
    def __init__(self):
        # 分配点管理
        self.alloc_site_counter = 0
        self.allocation_sites: Dict[int, AllocationSite] = {}
        
        # 函数信息
        self.functions: Dict[str, FunctionAliasInfo] = {}
        
        # 调用图
        self.call_sites: Dict[int, CallSite] = {}
        self.call_site_counter = 0
        
        # 全局变量
        self.global_vars: Set[str] = set()
        self.global_sites: Dict[str, AllocationSite] = {}
        
        # 别名缓存
        self.alias_cache: Dict[Tuple[str, str], AliasKind] = {}
        
        # 工作列表（用于迭代求解）
        self.worklist: Set[str] = set()
    
    # ==================== 分配点管理 ====================
    
    def new_allocation_site(
        self,
        function: str,
        line: int,
        var_name: str = "",
        is_heap: bool = False,
        is_param: bool = False,
        is_global: bool = False
    ) -> AllocationSite:
        """创建新的分配点"""
        self.alloc_site_counter += 1
        site = AllocationSite(
            id=self.alloc_site_counter,
            function=function,
            line=line,
            var_name=var_name,
            is_heap=is_heap,
            is_param=is_param,
            is_global=is_global
        )
        self.allocation_sites[site.id] = site
        return site
    
    def get_allocation_site(self, site_id: int) -> Optional[AllocationSite]:
        """获取分配点"""
        return self.allocation_sites.get(site_id)
    
    # ==================== 函数管理 ====================
    
    def register_function(
        self,
        name: str,
        params: List[str] = None
    ) -> FunctionAliasInfo:
        """注册函数"""
        if name in self.functions:
            return self.functions[name]
        
        func_info = FunctionAliasInfo(name=name, params=params or [])
        self.functions[name] = func_info
        
        # 为参数创建分配点
        for param in func_info.params:
            site = self.new_allocation_site(
                function=name,
                line=0,
                var_name=param,
                is_param=True
            )
            func_info.param_sites[param] = site
            func_info.points_to[param] = PointsToSet({site})
        
        return func_info
    
    def get_function(self, name: str) -> Optional[FunctionAliasInfo]:
        """获取函数信息"""
        return self.functions.get(name)
    
    # ==================== 全局变量管理 ====================
    
    def register_global_var(self, var_name: str, line: int = 0) -> AllocationSite:
        """注册全局变量"""
        self.global_vars.add(var_name)
        
        if var_name not in self.global_sites:
            site = self.new_allocation_site(
                function="<global>",
                line=line,
                var_name=var_name,
                is_global=True
            )
            self.global_sites[var_name] = site
        
        return self.global_sites[var_name]
    
    # ==================== 调用图构建 ====================
    
    def add_call(
        self,
        caller: str,
        callee: str,
        line: int,
        arg_mapping: Dict[str, str],
        return_var: Optional[str] = None
    ) -> CallSite:
        """添加函数调用"""
        self.call_site_counter += 1
        call_site = CallSite(
            id=self.call_site_counter,
            caller=caller,
            callee=callee,
            line=line,
            arg_mapping=arg_mapping,
            return_var=return_var
        )
        self.call_sites[call_site.id] = call_site
        
        # 更新函数调用关系
        if caller in self.functions:
            self.functions[caller].calls.append((callee, arg_mapping))
        if callee in self.functions:
            self.functions[callee].called_by.add(caller)
        
        # 添加到工作列表
        self.worklist.add(caller)
        self.worklist.add(callee)
        
        return call_site
    
    # ==================== 指针赋值处理 ====================
    
    def process_address_of(
        self,
        function: str,
        ptr_var: str,
        target_var: str,
        line: int
    ):
        """处理取地址操作: ptr = &target"""
        func_info = self.register_function(function)
        
        # 为目标变量创建分配点（如果还没有）
        site = self.new_allocation_site(
            function=function,
            line=line,
            var_name=target_var,
            is_heap=False
        )
        
        # 更新指针的指向集合
        if ptr_var not in func_info.points_to:
            func_info.points_to[ptr_var] = PointsToSet()
        func_info.points_to[ptr_var].add(site)
        
        self.worklist.add(function)
    
    def process_pointer_assign(
        self,
        function: str,
        target_ptr: str,
        source_ptr: str,
        line: int
    ):
        """处理指针赋值: target = source"""
        func_info = self.register_function(function)
        
        # 确保两个变量都有指向集合
        if target_ptr not in func_info.points_to:
            func_info.points_to[target_ptr] = PointsToSet()
        if source_ptr not in func_info.points_to:
            func_info.points_to[source_ptr] = PointsToSet()
        
        # target 指向 source 指向的所有对象
        func_info.points_to[target_ptr].update(func_info.points_to[source_ptr])
        
        self.worklist.add(function)
    
    def process_heap_alloc(
        self,
        function: str,
        ptr_var: str,
        line: int
    ):
        """处理堆分配: ptr = new/malloc"""
        func_info = self.register_function(function)
        
        # 创建堆分配点
        site = self.new_allocation_site(
            function=function,
            line=line,
            var_name=ptr_var,
            is_heap=True
        )
        
        if ptr_var not in func_info.points_to:
            func_info.points_to[ptr_var] = PointsToSet()
        func_info.points_to[ptr_var].add(site)
        
        self.worklist.add(function)
    
    # ==================== 过程间分析 ====================
    
    def propagate_at_call(
        self,
        call_site: CallSite
    ) -> bool:
        """
        在调用点传播别名信息
        
        Returns:
            是否有变化
        """
        caller_info = self.functions.get(call_site.caller)
        callee_info = self.functions.get(call_site.callee)
        
        if not caller_info or not callee_info:
            return False
        
        changed = False
        
        # 1. 实参到形参的别名传播
        for formal_param, actual_arg in call_site.arg_mapping.items():
            if formal_param in callee_info.param_sites:
                param_site = callee_info.param_sites[formal_param]
                
                # 获取实参的指向集合
                if actual_arg in caller_info.points_to:
                    actual_pts = caller_info.points_to[actual_arg]
                    
                    # 形参指向实参指向的对象
                    if formal_param not in callee_info.points_to:
                        callee_info.points_to[formal_param] = PointsToSet()
                    
                    old_size = len(callee_info.points_to[formal_param])
                    callee_info.points_to[formal_param].update(actual_pts)
                    
                    if len(callee_info.points_to[formal_param]) > old_size:
                        changed = True
        
        # 2. 返回值的别名传播
        if call_site.return_var and callee_info.return_sites:
            if call_site.return_var not in caller_info.points_to:
                caller_info.points_to[call_site.return_var] = PointsToSet()
            
            old_size = len(caller_info.points_to[call_site.return_var])
            caller_info.points_to[call_site.return_var].targets.update(callee_info.return_sites)
            
            if len(caller_info.points_to[call_site.return_var]) > old_size:
                changed = True
        
        return changed
    
    def propagate_at_return(
        self,
        function: str,
        return_var: str,
        line: int
    ):
        """处理返回值"""
        func_info = self.functions.get(function)
        if not func_info:
            return
        
        # 记录返回值可能的分配点
        if return_var in func_info.points_to:
            func_info.return_sites.update(func_info.points_to[return_var].targets)
        
        self.worklist.add(function)
    
    def solve(self, max_iterations: int = 100) -> bool:
        """
        迭代求解直到不动点
        
        Args:
            max_iterations: 最大迭代次数
        
        Returns:
            是否收敛
        """
        for iteration in range(max_iterations):
            if not self.worklist:
                return True
            
            changed = False
            current_worklist = self.worklist.copy()
            self.worklist.clear()
            
            # 处理所有调用点
            for call_site in self.call_sites.values():
                if self.propagate_at_call(call_site):
                    changed = True
            
            if not changed:
                return True
        
        return False
    
    # ==================== 别名查询 ====================
    
    def query_alias(
        self,
        function: str,
        ptr1: str,
        ptr2: str
    ) -> AliasKind:
        """
        查询两个指针的别名关系
        
        Args:
            function: 所在函数
            ptr1: 指针1
            ptr2: 指针2
        
        Returns:
            别名类型
        """
        cache_key = (f"{function}:{ptr1}", f"{function}:{ptr2}")
        if cache_key in self.alias_cache:
            return self.alias_cache[cache_key]
        
        func_info = self.functions.get(function)
        if not func_info:
            return AliasKind.UNKNOWN
        
        pts1 = func_info.points_to.get(ptr1)
        pts2 = func_info.points_to.get(ptr2)
        
        if not pts1 or not pts2:
            return AliasKind.UNKNOWN
        
        # 计算交集
        intersection = pts1.targets & pts2.targets
        
        if not intersection:
            result = AliasKind.NO_ALIAS
        elif len(intersection) == 1 and len(pts1.targets) == 1 and len(pts2.targets) == 1:
            result = AliasKind.MUST_ALIAS
        else:
            result = AliasKind.MAY_ALIAS
        
        self.alias_cache[cache_key] = result
        return result
    
    def get_all_aliases(
        self,
        function: str,
        ptr: str
    ) -> Set[str]:
        """
        获取指针的所有可能别名
        
        Args:
            function: 所在函数
            ptr: 指针名
        
        Returns:
            别名集合
        """
        func_info = self.functions.get(function)
        if not func_info:
            return set()
        
        pts = func_info.points_to.get(ptr)
        if not pts:
            return set()
        
        aliases = set()
        for var, var_pts in func_info.points_to.items():
            if var == ptr:
                continue
            if var_pts.targets & pts.targets:
                aliases.add(var)
        
        return aliases
    
    def get_points_to_set(
        self,
        function: str,
        ptr: str
    ) -> Set[AllocationSite]:
        """
        获取指针的指向集合
        
        Args:
            function: 所在函数
            ptr: 指针名
        
        Returns:
            指向的分配点集合
        """
        func_info = self.functions.get(function)
        if not func_info:
            return set()
        
        pts = func_info.points_to.get(ptr)
        return pts.targets if pts else set()
    
    # ==================== 报告生成 ====================
    
    def generate_report(self) -> str:
        """生成别名分析报告"""
        lines = [
            "=" * 70,
            "过程间别名分析报告",
            "=" * 70,
            ""
        ]
        
        # 统计信息
        lines.append("统计信息：")
        lines.append(f"  函数数：{len(self.functions)}")
        lines.append(f"  分配点数：{len(self.allocation_sites)}")
        lines.append(f"  调用点数：{len(self.call_sites)}")
        lines.append(f"  全局变量数：{len(self.global_vars)}")
        lines.append("")
        
        # 函数信息
        for func_name, func_info in self.functions.items():
            lines.append(f"函数 {func_name}：")
            lines.append(f"  参数：{', '.join(func_info.params) if func_info.params else '无'}")
            lines.append(f"  局部变量：{', '.join(sorted(func_info.local_vars)) if func_info.local_vars else '无'}")
            lines.append(f"  调用函数：{', '.join(c for c, _ in func_info.calls) if func_info.calls else '无'}")
            lines.append(f"  被调用者：{', '.join(func_info.called_by) if func_info.called_by else '无'}")
            
            # 指向信息
            if func_info.points_to:
                lines.append("  指向信息：")
                for var, pts in sorted(func_info.points_to.items()):
                    targets = [f"site_{s.id}" for s in pts.targets]
                    lines.append(f"    {var} -> {{{', '.join(targets)}}}")
            
            lines.append("")
        
        # 调用图
        if self.call_sites:
            lines.append("调用图：")
            for call_site in self.call_sites.values():
                args = ', '.join(f"{k}={v}" for k, v in call_site.arg_mapping.items())
                ret = f" -> {call_site.return_var}" if call_site.return_var else ""
                lines.append(f"  {call_site.caller} -> {call_site.callee}({args}){ret}")
            lines.append("")
        
        # 分配点信息
        if self.allocation_sites:
            lines.append("分配点：")
            for site_id, site in self.allocation_sites.items():
                kind = []
                if site.is_heap:
                    kind.append("堆")
                if site.is_param:
                    kind.append("参数")
                if site.is_global:
                    kind.append("全局")
                kind_str = f" ({'+'.join(kind)})" if kind else ""
                lines.append(f"  site_{site_id}: {site.function}:{site.line} {site.var_name}{kind_str}")
            lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)

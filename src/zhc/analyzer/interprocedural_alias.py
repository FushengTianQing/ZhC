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

兼容层：
- AliasAnalyzer: 兼容旧版单函数分析 API
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


class AliasKind(Enum):
    """别名类型"""

    MUST_ALIAS = "必须别名"  # 确定别名
    MAY_ALIAS = "可能别名"  # 可能别名
    NO_ALIAS = "非别名"  # 确定非别名
    UNKNOWN = "未知"


# ==================== 数据结构 ====================


@dataclass
class AllocationSite:
    """分配点信息"""

    id: int  # 分配点ID
    function: str  # 所在函数
    line: int  # 行号
    is_heap: bool = False  # 是否堆分配
    is_param: bool = False  # 是否参数
    is_global: bool = False  # 是否全局变量
    var_name: str = ""  # 变量名

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

    def update(self, other: "PointsToSet"):
        self.targets.update(other.targets)

    def may_point_to(self, site: AllocationSite) -> bool:
        return site in self.targets

    def copy(self) -> "PointsToSet":
        return PointsToSet(self.targets.copy())

    def __len__(self):
        return len(self.targets)

    def __iter__(self):
        return iter(self.targets)


@dataclass
class FunctionAliasInfo:
    """函数别名信息"""

    name: str  # 函数名
    params: List[str] = field(default_factory=list)  # 参数列表
    param_sites: Dict[str, AllocationSite] = field(default_factory=dict)  # 参数分配点
    local_vars: Set[str] = field(default_factory=set)  # 局部变量
    points_to: Dict[str, PointsToSet] = field(default_factory=dict)  # 变量指向集合
    return_sites: Set[AllocationSite] = field(default_factory=set)  # 返回值可能的分配点
    calls: List[Tuple[str, Dict[str, str]]] = field(
        default_factory=list
    )  # 调用其他函数 (callee, arg_map)
    called_by: Set[str] = field(default_factory=set)  # 被哪些函数调用

    def get_points_to(self, var: str) -> PointsToSet:
        if var not in self.points_to:
            self.points_to[var] = PointsToSet()
        return self.points_to[var]


@dataclass
class CallSite:
    """调用点信息"""

    id: int  # 调用点ID
    caller: str  # 调用函数
    callee: str  # 被调函数
    line: int  # 行号
    arg_mapping: Dict[str, str]  # 实参到形参映射 {形参: 实参}
    return_var: Optional[str]  # 返回值存储变量

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
        is_global: bool = False,
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
            is_global=is_global,
        )
        self.allocation_sites[site.id] = site
        return site

    def get_allocation_site(self, site_id: int) -> Optional[AllocationSite]:
        """获取分配点"""
        return self.allocation_sites.get(site_id)

    # ==================== 函数管理 ====================

    def register_function(
        self, name: str, params: List[str] = None
    ) -> FunctionAliasInfo:
        """注册函数"""
        if name in self.functions:
            return self.functions[name]

        func_info = FunctionAliasInfo(name=name, params=params or [])
        self.functions[name] = func_info

        # 为参数创建分配点
        for param in func_info.params:
            site = self.new_allocation_site(
                function=name, line=0, var_name=param, is_param=True
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
                function="<global>", line=line, var_name=var_name, is_global=True
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
        return_var: Optional[str] = None,
    ) -> CallSite:
        """添加函数调用"""
        self.call_site_counter += 1
        call_site = CallSite(
            id=self.call_site_counter,
            caller=caller,
            callee=callee,
            line=line,
            arg_mapping=arg_mapping,
            return_var=return_var,
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
        self, function: str, ptr_var: str, target_var: str, line: int
    ):
        """处理取地址操作: ptr = &target"""
        func_info = self.register_function(function)

        # 为目标变量创建分配点（如果还没有）
        site = self.new_allocation_site(
            function=function, line=line, var_name=target_var, is_heap=False
        )

        # 更新指针的指向集合
        if ptr_var not in func_info.points_to:
            func_info.points_to[ptr_var] = PointsToSet()
        func_info.points_to[ptr_var].add(site)

        self.worklist.add(function)

    def process_pointer_assign(
        self, function: str, target_ptr: str, source_ptr: str, line: int
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

    def process_heap_alloc(self, function: str, ptr_var: str, line: int):
        """处理堆分配: ptr = new/malloc"""
        func_info = self.register_function(function)

        # 创建堆分配点
        site = self.new_allocation_site(
            function=function, line=line, var_name=ptr_var, is_heap=True
        )

        if ptr_var not in func_info.points_to:
            func_info.points_to[ptr_var] = PointsToSet()
        func_info.points_to[ptr_var].add(site)

        self.worklist.add(function)

    # ==================== 过程间分析 ====================

    def propagate_at_call(self, call_site: CallSite) -> bool:
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
                callee_info.param_sites[formal_param]

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
            caller_info.points_to[call_site.return_var].targets.update(
                callee_info.return_sites
            )

            if len(caller_info.points_to[call_site.return_var]) > old_size:
                changed = True

        return changed

    def propagate_at_return(self, function: str, return_var: str, line: int):
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
            self.worklist.copy()
            self.worklist.clear()

            # 处理所有调用点
            for call_site in self.call_sites.values():
                if self.propagate_at_call(call_site):
                    changed = True

            if not changed:
                return True

        return False

    # ==================== 别名查询 ====================

    def query_alias(self, function: str, ptr1: str, ptr2: str) -> AliasKind:
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
        elif (
            len(intersection) == 1 and len(pts1.targets) == 1 and len(pts2.targets) == 1
        ):
            result = AliasKind.MUST_ALIAS
        else:
            result = AliasKind.MAY_ALIAS

        self.alias_cache[cache_key] = result
        return result

    def get_all_aliases(self, function: str, ptr: str) -> Set[str]:
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

    def get_points_to_set(self, function: str, ptr: str) -> Set[AllocationSite]:
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
        lines = ["=" * 70, "过程间别名分析报告", "=" * 70, ""]

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
            lines.append(
                f"  参数：{', '.join(func_info.params) if func_info.params else '无'}"
            )
            lines.append(
                f"  局部变量：{', '.join(sorted(func_info.local_vars)) if func_info.local_vars else '无'}"
            )
            lines.append(
                f"  调用函数：{', '.join(c for c, _ in func_info.calls) if func_info.calls else '无'}"
            )
            lines.append(
                f"  被调用者：{', '.join(func_info.called_by) if func_info.called_by else '无'}"
            )

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
                args = ", ".join(f"{k}={v}" for k, v in call_site.arg_mapping.items())
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
                lines.append(
                    f"  site_{site_id}: {site.function}:{site.line} {site.var_name}{kind_str}"
                )
            lines.append("")

        lines.append("=" * 70)

        return "\n".join(lines)


# ==================== 兼容层：旧版 API ====================


@dataclass
class AliasSet:
    """
    别名集合（兼容旧版 API）

    表示一组可能指向同一内存位置的指针。
    """

    pointers: Set[str] = field(default_factory=set)
    allocation_site: Optional[int] = None
    is_heap: bool = False

    def add_pointer(self, ptr_name: str):
        """添加指针到别名集"""
        self.pointers.add(ptr_name)

    def merge_with(self, other: "AliasSet"):
        """合并另一个别名集"""
        self.pointers.update(other.pointers)
        if other.allocation_site:
            self.allocation_site = other.allocation_site
        self.is_heap = self.is_heap or other.is_heap

    def may_alias(self, ptr_name: str) -> bool:
        """检查指针是否可能在别名集中"""
        return ptr_name in self.pointers

    def __str__(self) -> str:
        ptrs = ", ".join(sorted(self.pointers)) if self.pointers else "空"
        site = f" (位置{self.allocation_site})" if self.allocation_site else ""
        return f"{{{ptrs}}}{site}"


@dataclass
class AliasInfo:
    """
    别名信息（兼容旧版 API）

    存储单个指针的别名相关信息。
    """

    pointer: str
    alias_sets: List[AliasSet] = field(default_factory=list)
    may_point_to: Set[str] = field(default_factory=set)
    must_point_to: Optional[str] = None

    def add_target(self, target: str, is_must: bool = False):
        """添加可能指向的目标"""
        self.may_point_to.add(target)
        if is_must:
            self.must_point_to = target

    def may_alias(self, other_ptr: str) -> AliasKind:
        """检查与另一个指针的别名关系"""
        if self.must_point_to and other_ptr in self.may_point_to:
            if self.must_point_to == other_ptr:
                return AliasKind.MUST_ALIAS

        if other_ptr in self.may_point_to:
            return AliasKind.MAY_ALIAS

        return AliasKind.NO_ALIAS


class AliasAnalyzer:
    """
    别名分析器（兼容旧版 API）

    提供单函数别名分析接口，内部使用 InterproceduralAliasAnalyzer 实现。
    此类保持向后兼容，新代码应直接使用 InterproceduralAliasAnalyzer。
    """

    def __init__(self):
        self._analyzer = InterproceduralAliasAnalyzer()
        self.alias_sets: Dict[str, AliasSet] = {}
        self.pointer_info: Dict[str, AliasInfo] = {}
        self.allocations: Dict[str, int] = {}
        self.pointer_assignments: List[Tuple[str, str, int]] = []
        self._current_function: str = ""
        self._alloc_site_counter = 0

    def analyze_function(
        self, func_name: str, statements: List[dict]
    ) -> Dict[str, AliasInfo]:
        """
        分析函数中的指针别名

        Args:
            func_name: 函数名
            statements: 函数体

        Returns:
            指针名到别名信息的映射
        """
        self._current_function = func_name
        self._analyzer.register_function(func_name)

        # 第一遍：收集分配点
        self._collect_allocation_sites(statements)

        # 第二遍：分析指针赋值
        self._analyze_pointer_assignments(statements)

        # 第三遍：计算别名集合
        self._compute_alias_sets()

        return self.pointer_info

    def _collect_allocation_sites(self, statements: List[dict]):
        """收集分配点"""
        for stmt in statements:
            stmt_type = stmt.get("type", "")
            stmt.get("line", 0)
            var_name = stmt.get("name", "")

            # 指针声明
            if stmt_type == "var_decl" and self._is_pointer_type(
                stmt.get("data_type", "")
            ):
                if var_name not in self.pointer_info:
                    self.pointer_info[var_name] = AliasInfo(pointer=var_name)

            # 地址分配（取地址运算）
            if stmt_type == "assign" and "&" in str(stmt.get("value", "")):
                self._alloc_site_counter += 1
                self.allocations[var_name] = self._alloc_site_counter

                alias_set = AliasSet(
                    pointers={var_name},
                    allocation_site=self._alloc_site_counter,
                    is_heap=False,
                )
                self.alias_sets[f"site_{self._alloc_site_counter}"] = alias_set

                if var_name not in self.pointer_info:
                    self.pointer_info[var_name] = AliasInfo(pointer=var_name)
                self.pointer_info[var_name].alias_sets.append(alias_set)

            # 动态分配
            if "新建" in stmt_type or "alloc" in stmt_type:
                self._alloc_site_counter += 1
                self.allocations[var_name] = self._alloc_site_counter

                alias_set = AliasSet(
                    pointers={var_name},
                    allocation_site=self._alloc_site_counter,
                    is_heap=True,
                )
                self.alias_sets[f"site_{self._alloc_site_counter}"] = alias_set

                if var_name not in self.pointer_info:
                    self.pointer_info[var_name] = AliasInfo(pointer=var_name)
                self.pointer_info[var_name].alias_sets.append(alias_set)

            # 递归分析
            if "body" in stmt:
                self._collect_allocation_sites(stmt["body"])
            if "then_body" in stmt:
                self._collect_allocation_sites(stmt["then_body"])
            if "else_body" in stmt:
                self._collect_allocation_sites(stmt["else_body"])

    def _analyze_pointer_assignments(self, statements: List[dict]):
        """分析指针赋值"""
        for stmt in statements:
            stmt_type = stmt.get("type", "")
            line = stmt.get("line", 0)

            if stmt_type == "assign":
                target = stmt.get("name", "")
                value = str(stmt.get("value", ""))

                is_ptr_assignment = (
                    self._is_pointer(target)
                    or self._is_address_of(value)
                    or target in self.pointer_info
                    or value in self.pointer_info
                )

                if is_ptr_assignment:
                    if target not in self.pointer_info:
                        self.pointer_info[target] = AliasInfo(pointer=target)
                    self.pointer_assignments.append((target, value, line))

            if "body" in stmt:
                self._analyze_pointer_assignments(stmt["body"])
            if "then_body" in stmt:
                self._analyze_pointer_assignments(stmt["then_body"])
            if "else_body" in stmt:
                self._analyze_pointer_assignments(stmt["else_body"])

    def _is_pointer(self, var_name: str) -> bool:
        return var_name in self.pointer_info or var_name in self.allocations

    def _is_address_of(self, expr: str) -> bool:
        return "&" in expr

    def _compute_alias_sets(self):
        """计算别名集合"""
        for ptr, target, line in self.pointer_assignments:
            if ptr not in self.pointer_info:
                self.pointer_info[ptr] = AliasInfo(pointer=ptr)

            info = self.pointer_info[ptr]

            if target.startswith("&"):
                var_name = target[1:].strip()
                info.add_target(var_name, is_must=True)

                if var_name in self.allocations:
                    site_id = self.allocations[var_name]
                    alias_set = self.alias_sets.get(f"site_{site_id}")
                    if alias_set:
                        alias_set.add_pointer(ptr)
                        if alias_set not in info.alias_sets:
                            info.alias_sets.append(alias_set)
                else:
                    self._alloc_site_counter += 1
                    self.allocations[var_name] = self._alloc_site_counter
                    alias_set = AliasSet(
                        pointers={var_name, ptr},
                        allocation_site=self._alloc_site_counter,
                        is_heap=False,
                    )
                    self.alias_sets[f"site_{self._alloc_site_counter}"] = alias_set
                    info.alias_sets.append(alias_set)
            else:
                info.add_target(target)

                if target in self.pointer_info:
                    target_info = self.pointer_info[target]
                    for alias_set in target_info.alias_sets:
                        alias_set.add_pointer(ptr)
                        if alias_set not in info.alias_sets:
                            info.alias_sets.append(alias_set)
                    info.may_point_to.update(target_info.may_point_to)
                    if target_info.must_point_to:
                        info.must_point_to = target_info.must_point_to
                else:
                    if target.isidentifier() or all(
                        c.isalnum() or "\u4e00" <= c <= "\u9fff" for c in target
                    ):
                        if target not in self.allocations:
                            self._alloc_site_counter += 1
                            self.allocations[target] = self._alloc_site_counter

                        site_id = self.allocations[target]
                        alias_set = self.alias_sets.get(f"site_{site_id}")
                        if alias_set:
                            alias_set.add_pointer(ptr)
                            if alias_set not in info.alias_sets:
                                info.alias_sets.append(alias_set)
                        else:
                            self._alloc_site_counter += 1
                            self.allocations[target] = self._alloc_site_counter
                            new_alias_set = AliasSet(
                                pointers={target, ptr},
                                allocation_site=self._alloc_site_counter,
                                is_heap=False,
                            )
                            self.alias_sets[f"site_{self._alloc_site_counter}"] = (
                                new_alias_set
                            )
                            info.alias_sets.append(new_alias_set)

    def _is_pointer_type(self, type_name: str) -> bool:
        return "指针" in type_name or "*" in type_name or "Ptr" in type_name

    def query_alias(self, ptr1: str, ptr2: str) -> AliasKind:
        """
        查询两个指针的别名关系

        Args:
            ptr1: 指针1
            ptr2: 指针2

        Returns:
            别名类型
        """
        info1 = self.pointer_info.get(ptr1)
        info2 = self.pointer_info.get(ptr2)

        if not info1 or not info2:
            return AliasKind.UNKNOWN

        for alias_set in info1.alias_sets:
            if alias_set.may_alias(ptr2):
                if (
                    info1.must_point_to
                    and info2.must_point_to
                    and info1.must_point_to == info2.must_point_to
                ):
                    return AliasKind.MUST_ALIAS
                return AliasKind.MAY_ALIAS

        return AliasKind.NO_ALIAS

    def get_all_aliases(self, ptr_name: str) -> Set[str]:
        """
        获取指针的所有可能别名

        Args:
            ptr_name: 指针名

        Returns:
            别名集合
        """
        info = self.pointer_info.get(ptr_name)
        if not info:
            return set()

        aliases = set()
        for alias_set in info.alias_sets:
            aliases.update(alias_set.pointers)

        aliases.discard(ptr_name)
        return aliases

    def get_points_to_set(self, ptr_name: str) -> Set[str]:
        """
        获取指针可能指向的变量集合

        Args:
            ptr_name: 指针名

        Returns:
            指向集合
        """
        info = self.pointer_info.get(ptr_name)
        return info.may_point_to if info else set()

    def propagate_aliases(
        self, func_name: str, caller_aliases: Dict[str, AliasInfo]
    ) -> Dict[str, AliasInfo]:
        """
        传播别名信息到被调用函数

        Args:
            func_name: 被调用函数名
            caller_aliases: 调用者的别名信息

        Returns:
            传播后的别名信息
        """
        propagated = {}

        for ptr, info in caller_aliases.items():
            propagated[ptr] = AliasInfo(
                pointer=info.pointer,
                alias_sets=info.alias_sets.copy(),
                may_point_to=info.may_point_to.copy(),
                must_point_to=info.must_point_to,
            )

        return propagated

    def generate_report(self) -> str:
        """生成别名分析报告"""
        lines = ["=" * 70, "别名分析报告", "=" * 70, ""]

        lines.append("统计信息：")
        lines.append(f"  分配点数：{len(self.alias_sets)}")
        lines.append(f"  指针数：{len(self.pointer_info)}")
        lines.append("")

        if self.alias_sets:
            lines.append("别名集合：")
            for site_id, alias_set in self.alias_sets.items():
                lines.append(f"  {site_id}: {alias_set}")
            lines.append("")

        if self.pointer_info:
            lines.append("指针指向：")
            for ptr_name, info in self.pointer_info.items():
                must = f" -> {info.must_point_to}" if info.must_point_to else ""
                may = (
                    ", ".join(sorted(info.may_point_to)) if info.may_point_to else "无"
                )
                lines.append(f"  {ptr_name}: {must} (可能: {may})")
            lines.append("")

        if len(self.pointer_info) > 1:
            lines.append("别名关系：")
            ptrs = list(self.pointer_info.keys())
            for i, ptr1 in enumerate(ptrs):
                for ptr2 in ptrs[i + 1 :]:
                    alias_kind = self.query_alias(ptr1, ptr2)
                    if alias_kind != AliasKind.NO_ALIAS:
                        lines.append(f"  {ptr1} 和 {ptr2}: {alias_kind.value}")
            lines.append("")

        lines.append("=" * 70)

        return "\n".join(lines)

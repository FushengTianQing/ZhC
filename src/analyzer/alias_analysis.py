#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
别名分析器 - Alias Analyzer

功能：
1. 指针别名分析
2. 别名集合计算
3. 别名传播
4. 非别名推导

作者：远
日期：2026-04-03
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


class AliasKind(Enum):
    """别名类型"""
    MUST_ALIAS = "必须别名"       # 确定别名
    MAY_ALIAS = "可能别名"        # 可能别名
    NO_ALIAS = "非别名"           # 确定非别名
    UNKNOWN = "未知"


@dataclass
class AliasSet:
    """别名集合"""
    pointers: Set[str] = field(default_factory=set)  # 可能指向同一内存位置的指针
    allocation_site: Optional[int] = None             # 分配点
    is_heap: bool = False                             # 是否堆分配
    
    def add_pointer(self, ptr_name: str):
        """添加指针到别名集"""
        self.pointers.add(ptr_name)
    
    def merge_with(self, other: 'AliasSet'):
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
    """别名信息"""
    pointer: str
    alias_sets: List[AliasSet] = field(default_factory=list)
    may_point_to: Set[str] = field(default_factory=set)  # 可能指向的变量
    must_point_to: Optional[str] = None                 # 确定指向的变量
    
    def add_target(self, target: str, is_must: bool = False):
        """添加可能指向的目标"""
        self.may_point_to.add(target)
        if is_must:
            self.must_point_to = target
    
    def may_alias(self, other_ptr: str) -> AliasKind:
        """检查与另一个指针的别名关系"""
        # 检查是否确定别名
        if self.must_point_to and other_ptr in self.may_point_to:
            if self.must_point_to == other_ptr:
                return AliasKind.MUST_ALIAS
        
        # 检查是否可能别名
        if other_ptr in self.may_point_to:
            return AliasKind.MAY_ALIAS
        
        return AliasKind.NO_ALIAS


class AliasAnalyzer:
    """别名分析器"""
    
    def __init__(self):
        self.alias_sets: Dict[str, AliasSet] = {}  # 分配点 -> 别名集
        self.pointer_info: Dict[str, AliasInfo] = {}  # 指针名 -> 别名信息
        self.allocations: Dict[str, int] = {}  # 变量名 -> 分配行号
        self.pointer_assignments: List[Tuple[str, str, int]] = []  # (指针, 目标, 行号)
        
        self.alloc_site_counter = 0  # 分配点计数器
    
    # ==================== 别名分析 ====================
    
    def analyze_function(self, func_name: str, statements: List[dict]) -> Dict[str, AliasInfo]:
        """
        分析函数中的指针别名
        
        Args:
            func_name: 函数名
            statements: 函数体
        
        Returns:
            指针名到别名信息的映射
        """
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
            stmt_type = stmt.get('type', '')
            line = stmt.get('line', 0)
            var_name = stmt.get('name', '')
            
            # 指针声明（声明但不一定初始化）
            if stmt_type == 'var_decl' and self._is_pointer_type(stmt.get('data_type', '')):
                if var_name not in self.pointer_info:
                    self.pointer_info[var_name] = AliasInfo(pointer=var_name)
            
            # 地址分配（取地址运算）
            if stmt_type == 'assign' and '&' in str(stmt.get('value', '')):
                self.alloc_site_counter += 1
                self.allocations[var_name] = self.alloc_site_counter
                
                # 创建新的别名集
                alias_set = AliasSet(
                    pointers={var_name},
                    allocation_site=self.alloc_site_counter,
                    is_heap=False
                )
                self.alias_sets[f"site_{self.alloc_site_counter}"] = alias_set
                
                # 注册指针信息
                if var_name not in self.pointer_info:
                    self.pointer_info[var_name] = AliasInfo(pointer=var_name)
                self.pointer_info[var_name].alias_sets.append(alias_set)
            
            # 动态分配（新建、分配）
            if '新建' in stmt_type or 'alloc' in stmt_type:
                self.alloc_site_counter += 1
                self.allocations[var_name] = self.alloc_site_counter
                
                alias_set = AliasSet(
                    pointers={var_name},
                    allocation_site=self.alloc_site_counter,
                    is_heap=True
                )
                self.alias_sets[f"site_{self.alloc_site_counter}"] = alias_set
                
                # 注册指针信息
                if var_name not in self.pointer_info:
                    self.pointer_info[var_name] = AliasInfo(pointer=var_name)
                self.pointer_info[var_name].alias_sets.append(alias_set)
            
            # 递归分析
            if 'body' in stmt:
                self._collect_allocation_sites(stmt['body'])
            if 'then_body' in stmt:
                self._collect_allocation_sites(stmt['then_body'])
            if 'else_body' in stmt:
                self._collect_allocation_sites(stmt['else_body'])
    
    def _analyze_pointer_assignments(self, statements: List[dict]):
        """分析指针赋值"""
        for stmt in statements:
            stmt_type = stmt.get('type', '')
            line = stmt.get('line', 0)
            
            # 指针赋值
            if stmt_type == 'assign':
                target = stmt.get('name', '')
                value = str(stmt.get('value', ''))
                
                # 检查是否是指针赋值（赋值目标或值中包含指针相关操作）
                is_ptr_assignment = (
                    self._is_pointer(target) or 
                    self._is_address_of(value) or
                    target in self.pointer_info or
                    value in self.pointer_info
                )
                
                if is_ptr_assignment:
                    # 确保目标在pointer_info中
                    if target not in self.pointer_info:
                        self.pointer_info[target] = AliasInfo(pointer=target)
                    self.pointer_assignments.append((target, value, line))
            
            # 递归分析
            if 'body' in stmt:
                self._analyze_pointer_assignments(stmt['body'])
            if 'then_body' in stmt:
                self._analyze_pointer_assignments(stmt['then_body'])
            if 'else_body' in stmt:
                self._analyze_pointer_assignments(stmt['else_body'])
    
    def _is_pointer(self, var_name: str) -> bool:
        """检查变量是否是指针"""
        return var_name in self.pointer_info or var_name in self.allocations
    
    def _is_address_of(self, expr: str) -> bool:
        """检查表达式是否是取地址运算"""
        return '&' in expr
    
    def _compute_alias_sets(self):
        """计算别名集合"""
        # 基于流不敏感的别名分析
        for ptr, target, line in self.pointer_assignments:
            # 初始化指针信息
            if ptr not in self.pointer_info:
                self.pointer_info[ptr] = AliasInfo(pointer=ptr)
            
            info = self.pointer_info[ptr]
            
            # 分析赋值目标
            if target.startswith('&'):
                # 取地址运算：ptr = &x
                var_name = target[1:].strip()
                info.add_target(var_name, is_must=True)
                
                # 更新别名集
                if var_name in self.allocations:
                    site_id = self.allocations[var_name]
                    alias_set = self.alias_sets.get(f"site_{site_id}")
                    if alias_set:
                        alias_set.add_pointer(ptr)
                        if alias_set not in info.alias_sets:
                            info.alias_sets.append(alias_set)
                else:
                    # 创建新的别名集
                    self.alloc_site_counter += 1
                    self.allocations[var_name] = self.alloc_site_counter
                    alias_set = AliasSet(
                        pointers={var_name, ptr},
                        allocation_site=self.alloc_site_counter,
                        is_heap=False
                    )
                    self.alias_sets[f"site_{self.alloc_site_counter}"] = alias_set
                    info.alias_sets.append(alias_set)
            else:
                # 指针赋值：ptr1 = ptr2
                # 两个指针可能别名
                info.add_target(target)
                
                # 如果target是指针名（不是表达式），则传播别名
                if target in self.pointer_info:
                    target_info = self.pointer_info[target]
                    for alias_set in target_info.alias_sets:
                        alias_set.add_pointer(ptr)
                        if alias_set not in info.alias_sets:
                            info.alias_sets.append(alias_set)
                    # 复制指向集合
                    info.may_point_to.update(target_info.may_point_to)
                    if target_info.must_point_to:
                        info.must_point_to = target_info.must_point_to
                else:
                    # target可能是变量名或其他表达式
                    # 如果target本身是一个变量名，创建新的别名关系
                    if target.isidentifier() or all(c.isalnum() or '\u4e00' <= c <= '\u9fff' for c in target):
                        if target not in self.allocations:
                            self.alloc_site_counter += 1
                            self.allocations[target] = self.alloc_site_counter
                        
                        site_id = self.allocations[target]
                        alias_set = self.alias_sets.get(f"site_{site_id}")
                        if alias_set:
                            alias_set.add_pointer(ptr)
                            if alias_set not in info.alias_sets:
                                info.alias_sets.append(alias_set)
                        else:
                            # 创建新的别名集
                            self.alloc_site_counter += 1
                            self.allocations[target] = self.alloc_site_counter
                            new_alias_set = AliasSet(
                                pointers={target, ptr},
                                allocation_site=self.alloc_site_counter,
                                is_heap=False
                            )
                            self.alias_sets[f"site_{self.alloc_site_counter}"] = new_alias_set
                            info.alias_sets.append(new_alias_set)
    
    def _is_pointer_type(self, type_name: str) -> bool:
        """检查类型是否是指针类型"""
        return '指针' in type_name or '*' in type_name or 'Ptr' in type_name
    
    # ==================== 别名查询 ====================
    
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
        
        # 检查是否在同一个别名集中
        for alias_set in info1.alias_sets:
            if alias_set.may_alias(ptr2):
                # 进一步检查是否必须别名
                if (info1.must_point_to and info2.must_point_to and 
                    info1.must_point_to == info2.must_point_to):
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
        
        aliases.discard(ptr_name)  # 排除自身
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
    
    # ==================== 别名传播 ====================
    
    def propagate_aliases(self, func_name: str, caller_aliases: Dict[str, AliasInfo]) -> Dict[str, AliasInfo]:
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
            # 简化：直接复制别名信息
            propagated[ptr] = AliasInfo(
                pointer=info.pointer,
                alias_sets=info.alias_sets.copy(),
                may_point_to=info.may_point_to.copy(),
                must_point_to=info.must_point_to
            )
        
        return propagated
    
    # ==================== 报告生成 ====================
    
    def generate_report(self) -> str:
        """生成别名分析报告"""
        lines = [
            "=" * 70,
            "别名分析报告",
            "=" * 70,
            ""
        ]
        
        # 统计信息
        lines.append("统计信息：")
        lines.append(f"  分配点数：{len(self.alias_sets)}")
        lines.append(f"  指针数：{len(self.pointer_info)}")
        lines.append("")
        
        # 别名集合
        if self.alias_sets:
            lines.append("别名集合：")
            for site_id, alias_set in self.alias_sets.items():
                lines.append(f"  {site_id}: {alias_set}")
            lines.append("")
        
        # 指针信息
        if self.pointer_info:
            lines.append("指针指向：")
            for ptr_name, info in self.pointer_info.items():
                must = f" -> {info.must_point_to}" if info.must_point_to else ""
                may = ", ".join(sorted(info.may_point_to)) if info.may_point_to else "无"
                lines.append(f"  {ptr_name}: {must} (可能: {may})")
            lines.append("")
        
        # 别名对
        if len(self.pointer_info) > 1:
            lines.append("别名关系：")
            ptrs = list(self.pointer_info.keys())
            for i, ptr1 in enumerate(ptrs):
                for ptr2 in ptrs[i+1:]:
                    alias_kind = self.query_alias(ptr1, ptr2)
                    if alias_kind != AliasKind.NO_ALIAS:
                        lines.append(f"  {ptr1} 和 {ptr2}: {alias_kind.value}")
            lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)


# 测试代码
if __name__ == '__main__':
    print("=== 别名分析器测试 ===\n")
    
    analyzer = AliasAnalyzer()
    
    # 测试代码
    test_statements = [
        {'type': 'var_decl', 'name': 'x', 'line': 1},
        {'type': 'assign', 'name': 'p1', 'value': '&x', 'line': 2},
        {'type': 'assign', 'name': 'p2', 'value': '&x', 'line': 3},
        {'type': 'assign', 'name': 'p3', 'value': 'p1', 'line': 4},
        {'type': '新建', 'name': 'p4', 'line': 5},
        {'type': 'assign', 'name': 'p5', 'value': 'p4', 'line': 6},
    ]
    
    # 分析
    result = analyzer.analyze_function('test_func', test_statements)
    
    # 查询别名关系
    print("别名查询：")
    print(f"  p1 和 p2: {analyzer.query_alias('p1', 'p2').value}")
    print(f"  p1 和 p3: {analyzer.query_alias('p1', 'p3').value}")
    print(f"  p4 和 p5: {analyzer.query_alias('p4', 'p5').value}")
    print(f"  p1 和 p4: {analyzer.query_alias('p1', 'p4').value}")
    
    # 获取别名集合
    print(f"\np1 的所有别名：{analyzer.get_all_aliases('p1')}")
    print(f"p4 的所有别名：{analyzer.get_all_aliases('p4')}")
    
    # 生成报告
    print("\n" + analyzer.generate_report())
    
    print("\n=== 测试完成 ===")
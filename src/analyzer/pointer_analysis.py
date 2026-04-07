#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指针分析器 - Pointer Analyzer

功能：
1. 指针类型检查
2. 空指针解引用检测
3. 悬空指针检测
4. 指针运算安全检查
5. 智能指针分析

作者：远
日期：2026-04-03
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


class PointerState(Enum):
    """指针状态"""
    NULL = "空指针"           # 明确为空
    VALID = "有效指针"         # 确定有效
    MAYBE_NULL = "可能为空"   # 可能为空
    DANGLING = "悬空指针"     # 已释放
    UNKNOWN = "未知"


class PointerError(Enum):
    """指针错误类型"""
    NULL_DEREFERENCE = "空指针解引用"
    DANGLING_DEREFERENCE = "悬空指针解引用"
    INVALID_FREE = "无效释放"
    DOUBLE_FREE = "双重释放"
    INVALID_POINTER = "无效指针操作"
    ARRAY_BOUNDS = "数组越界"


@dataclass
class PointerInfo:
    """指针信息"""
    name: str
    state: PointerState = PointerState.UNKNOWN
    target_type: Optional[str] = None       # 指向类型
    allocation_line: Optional[int] = None   # 分配位置
    free_line: Optional[int] = None         # 释放位置
    null_check_lines: List[int] = field(default_factory=list)  # 空检查位置
    dereference_lines: List[int] = field(default_factory=list)  # 解引用位置
    
    # 智能指针信息
    is_smart_pointer: bool = False
    is_unique_ptr: bool = False
    is_shared_ptr: bool = False
    reference_count: int = 0
    
    def mark_allocated(self, line: int):
        """标记为已分配"""
        self.state = PointerState.VALID
        self.allocation_line = line
    
    def mark_freed(self, line: int):
        """标记为已释放"""
        self.state = PointerState.DANGLING
        self.free_line = line
    
    def mark_null_checked(self, line: int):
        """标记为已做空检查"""
        self.null_check_lines.append(line)
        if self.state == PointerState.MAYBE_NULL:
            # 空检查后，假设非空分支有效
            self.state = PointerState.VALID
    
    def mark_dereferenced(self, line: int):
        """标记为已解引用"""
        self.dereference_lines.append(line)


@dataclass
class PointerIssue:
    """指针问题"""
    error_type: PointerError
    pointer_name: str
    line_number: int
    message: str
    severity: str  # "error", "warning", "info"
    suggestion: str


class PointerAnalyzer:
    """指针分析器"""
    
    def __init__(self):
        self.pointers: Dict[str, PointerInfo] = {}
        self.issues: List[PointerIssue] = []
        self.pointer_flows: Dict[str, List[Tuple[int, str]]] = {}  # 指针流向
        
    # ==================== 指针状态分析 ====================
    
    def analyze_function(self, func_name: str, statements: List[dict]) -> List[PointerIssue]:
        """
        分析函数中的指针使用
        
        Args:
            func_name: 函数名
            statements: 函数体
        
        Returns:
            发现的指针问题列表
        """
        # 分析语句
        self._analyze_statements(func_name, statements)
        
        # 检查指针问题
        self._check_pointer_issues()
        
        return self.issues
    
    def _analyze_statements(self, func_name: str, statements: List[dict]):
        """分析语句中的指针操作"""
        for stmt in statements:
            stmt_type = stmt.get('type', '')
            line = stmt.get('line', 0)
            var_name = stmt.get('name', '')
            
            # 指针声明
            if stmt_type == 'var_decl':
                if self._is_pointer_type(stmt.get('data_type', '')):
                    self._register_pointer(var_name, line)
            
            # 内存分配
            if '新建' in stmt_type or 'alloc' in stmt_type:
                if var_name not in self.pointers:
                    self._register_pointer(var_name, line)
                self.pointers[var_name].mark_allocated(line)
                
                self._track_flow(var_name, line, 'allocate')
            
            # 内存释放
            if '删除' in stmt_type or 'free' in stmt_type:
                self._track_flow(var_name, line, 'free')
                if var_name in self.pointers:
                    # 检查双重释放
                    if self.pointers[var_name].state == PointerState.DANGLING:
                        self.issues.append(PointerIssue(
                            error_type=PointerError.DOUBLE_FREE,
                            pointer_name=var_name,
                            line_number=line,
                            message=f"指针 '{var_name}' 被双重释放",
                            severity="error",
                            suggestion="检查逻辑，确保只释放一次"
                        ))
                    self.pointers[var_name].mark_freed(line)
            
            # 空指针检查
            if stmt_type == 'if' and '空指针' in str(stmt.get('condition', '')):
                checked_ptr = self._extract_checked_pointer(stmt.get('condition', ''))
                if checked_ptr and checked_ptr in self.pointers:
                    self.pointers[checked_ptr].mark_null_checked(line)
            
            # 指针解引用
            if self._has_dereference(stmt):
                dereferenced_ptr = self._extract_dereferenced_pointer(stmt)
                if dereferenced_ptr:
                    if dereferenced_ptr in self.pointers:
                        self.pointers[dereferenced_ptr].mark_dereferenced(line)
                    self._track_flow(dereferenced_ptr, line, 'dereference')
            
            # 递归分析
            if 'body' in stmt:
                self._analyze_statements(func_name, stmt['body'])
            if 'then_body' in stmt:
                self._analyze_statements(func_name, stmt['then_body'])
            if 'else_body' in stmt:
                self._analyze_statements(func_name, stmt['else_body'])
    
    def _register_pointer(self, name: str, line: int):
        """注册指针变量"""
        if name not in self.pointers:
            self.pointers[name] = PointerInfo(
                name=name,
                state=PointerState.MAYBE_NULL  # 初始状态：可能为空
            )
    
    def _track_flow(self, ptr_name: str, line: int, operation: str):
        """追踪指针流向"""
        if ptr_name not in self.pointer_flows:
            self.pointer_flows[ptr_name] = []
        self.pointer_flows[ptr_name].append((line, operation))
    
    def _is_pointer_type(self, type_name: str) -> bool:
        """检查类型是否是指针类型"""
        return '指针' in type_name or '*' in type_name or 'Ptr' in type_name
    
    def _has_dereference(self, stmt: dict) -> bool:
        """检查语句是否包含解引用"""
        # 检查表达式中的解引用
        value = str(stmt.get('value', ''))
        condition = str(stmt.get('condition', ''))
        return '*' in value or '*' in condition
    
    def _extract_checked_pointer(self, condition: str) -> Optional[str]:
        """从条件中提取被检查的指针"""
        # 简化：假设条件形如 "ptr != 空指针" 或 "ptr == 空指针"
        import re
        match = re.search(r'(\w+)\s*[!=]=\s*空指针', condition)
        return match.group(1) if match else None
    
    def _extract_dereferenced_pointer(self, stmt: dict) -> Optional[str]:
        """从语句中提取被解引用的指针"""
        # 简化实现
        value = str(stmt.get('value', ''))
        if value.startswith('*'):
            return value[1:].strip()
        return None
    
    # ==================== 指针问题检查 ====================
    
    def _check_pointer_issues(self):
        """检查所有指针问题"""
        for ptr_name, info in self.pointers.items():
            # 检查空指针解引用
            self._check_null_dereference(ptr_name, info)
            
            # 检查悬空指针解引用
            self._check_dangling_dereference(ptr_name, info)
            
            # 检查内存泄漏
            self._check_memory_leak(ptr_name, info)
    
    def _check_null_dereference(self, ptr_name: str, info: PointerInfo):
        """检查空指针解引用"""
        for deref_line in info.dereference_lines:
            # 检查解引用前是否有空检查
            has_null_check_before = any(
                check_line < deref_line for check_line in info.null_check_lines
            )
            
            if info.state == PointerState.NULL:
                # 确定空指针解引用
                self.issues.append(PointerIssue(
                    error_type=PointerError.NULL_DEREFERENCE,
                    pointer_name=ptr_name,
                    line_number=deref_line,
                    message=f"空指针 '{ptr_name}' 在行 {deref_line} 被解引用",
                    severity="error",
                    suggestion="添加空指针检查或确保指针非空"
                ))
            elif info.state == PointerState.MAYBE_NULL and not has_null_check_before:
                # 可能为空的指针解引用，且无检查
                self.issues.append(PointerIssue(
                    error_type=PointerError.NULL_DEREFERENCE,
                    pointer_name=ptr_name,
                    line_number=deref_line,
                    message=f"指针 '{ptr_name}' 可能为空，在解引用前未检查",
                    severity="warning",
                    suggestion="添加空指针检查: if (ptr != 空指针)"
                ))
    
    def _check_dangling_dereference(self, ptr_name: str, info: PointerInfo):
        """检查悬空指针解引用"""
        if info.state != PointerState.DANGLING:
            return
        
        for deref_line in info.dereference_lines:
            if deref_line > (info.free_line or 0):
                self.issues.append(PointerIssue(
                    error_type=PointerError.DANGLING_DEREFERENCE,
                    pointer_name=ptr_name,
                    line_number=deref_line,
                    message=f"悬空指针 '{ptr_name}' 在释放后被解引用",
                    severity="error",
                    suggestion="释放后将指针置空或避免在释放后使用"
                ))
    
    def _check_memory_leak(self, ptr_name: str, info: PointerInfo):
        """检查内存泄漏"""
        if info.allocation_line and not info.free_line:
            # 已分配但未释放
            # 注意：这不一定是错误（可能返回指针等）
            self.issues.append(PointerIssue(
                error_type=PointerError.INVALID_FREE,
                pointer_name=ptr_name,
                line_number=info.allocation_line,
                message=f"指针 '{ptr_name}' 在行 {info.allocation_line} 分配但未释放",
                severity="info",
                suggestion="检查是否需要释放或指针所有权转移"
            ))
    
    # ==================== 智能指针分析 ====================
    
    def analyze_smart_pointer(self, ptr_name: str, ptr_type: str, line: int):
        """
        分析智能指针
        
        Args:
            ptr_name: 指针名
            ptr_type: 指针类型
            line: 行号
        """
        if ptr_name not in self.pointers:
            self.pointers[ptr_name] = PointerInfo(name=ptr_name)
        
        info = self.pointers[ptr_name]
        info.is_smart_pointer = True
        
        if '唯一指针' in ptr_type or 'unique_ptr' in ptr_type.lower():
            info.is_unique_ptr = True
        elif '共享指针' in ptr_type or 'shared_ptr' in ptr_type.lower():
            info.is_shared_ptr = True
            info.reference_count = 1
    
    def track_reference_count(self, ptr_name: str, delta: int, line: int):
        """追踪引用计数"""
        if ptr_name in self.pointers and self.pointers[ptr_name].is_shared_ptr:
            self.pointers[ptr_name].reference_count += delta
            
            if self.pointers[ptr_name].reference_count < 0:
                self.issues.append(PointerIssue(
                    error_type=PointerError.INVALID_POINTER,
                    pointer_name=ptr_name,
                    line_number=line,
                    message=f"共享指针 '{ptr_name}' 引用计数为负",
                    severity="error",
                    suggestion="检查引用计数管理逻辑"
                ))
    
    # ==================== 指针运算检查 ====================
    
    def check_pointer_arithmetic(self, ptr_name: str, operation: str, line: int):
        """
        检查指针运算安全性
        
        Args:
            ptr_name: 指针名
            operation: 运算类型
            line: 行号
        """
        # 简化：基本检查
        if ptr_name not in self.pointers:
            return
        
        info = self.pointers[ptr_name]
        if info.state == PointerState.DANGLING:
            self.issues.append(PointerIssue(
                error_type=PointerError.INVALID_POINTER,
                pointer_name=ptr_name,
                line_number=line,
                message=f"对悬空指针 '{ptr_name}' 进行指针运算",
                severity="error",
                suggestion="避免对悬空指针进行运算"
            ))
    
    # ==================== 报告生成 ====================
    
    def generate_report(self) -> str:
        """生成指针分析报告"""
        lines = [
            "=" * 70,
            "指针分析报告",
            "=" * 70,
            ""
        ]
        
        # 统计信息
        lines.append("统计信息：")
        lines.append(f"  指针总数：{len(self.pointers)}")
        lines.append(f"  问题数：{len(self.issues)}")
        lines.append("")
        
        # 指针状态
        if self.pointers:
            lines.append("指针状态：")
            for ptr_name, info in self.pointers.items():
                smart = " (智能指针)" if info.is_smart_pointer else ""
                lines.append(f"  {ptr_name}: {info.state.value}{smart}")
                if info.allocation_line:
                    lines.append(f"    分配于行 {info.allocation_line}")
                if info.free_line:
                    lines.append(f"    释放于行 {info.free_line}")
                if info.null_check_lines:
                    lines.append(f"    空检查：行 {', '.join(map(str, info.null_check_lines))}")
            lines.append("")
        
        # 问题列表
        if self.issues:
            lines.append("发现问题：")
            for issue in self.issues:
                icon = "❌" if issue.severity == "error" else "⚠️" if issue.severity == "warning" else "ℹ️"
                lines.append(f"  {icon} 行{issue.line_number}: {issue.message}")
                lines.append(f"     建议：{issue.suggestion}")
            lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)


# 测试代码
if __name__ == '__main__':
    print("=== 指针分析器测试 ===\n")
    
    analyzer = PointerAnalyzer()
    
    # 测试代码
    test_statements = [
        {'type': 'var_decl', 'name': 'p1', 'data_type': '整数型指针', 'line': 1},
        {'type': '新建', 'name': 'p1', 'line': 2},
        {'type': 'if', 'condition': 'p1 != 空指针', 'line': 3,
         'then_body': [
             {'type': 'assign', 'name': 'x', 'value': '*p1', 'line': 4}
         ]},
        {'type': '删除', 'name': 'p1', 'line': 5},
        {'type': 'assign', 'name': 'y', 'value': '*p1', 'line': 6},  # 悬空指针解引用
    ]
    
    # 分析
    issues = analyzer.analyze_function('test_func', test_statements)
    
    # 输出问题
    print(f"发现 {len(issues)} 个问题：")
    for issue in issues:
        print(f"  [{issue.severity}] 行{issue.line_number}: {issue.message}")
    
    # 生成报告
    print("\n" + analyzer.generate_report())
    
    print("\n=== 测试完成 ===")
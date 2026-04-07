#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
死代码消除优化器（增强版）
Dead Code Elimination Optimizer Enhanced

消除永远不会执行的代码，减少代码体积和提升性能

增强功能：
1. 数据流驱动的死代码检测
2. 过程间分析
3. 条件常量传播
4. 未使用函数消除
5. 死存储消除
6. 聚合优化

作者：阿福
日期：2026-04-03
"""

from typing import Set, List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DeadCodeType(Enum):
    """死代码类型"""
    UNREACHABLE = "不可达代码"
    UNUSED_VAR = "未使用变量"
    UNUSED_FUNC = "未使用函数"
    DEAD_STORE = "死存储"
    CONSTANT_BRANCH = "常量分支"
    EMPTY_BLOCK = "空代码块"
    REDUNDANT_CODE = "冗余代码"


@dataclass
class DeadCodeInfo:
    """死代码信息"""
    code_type: DeadCodeType
    reason: str
    location: str
    line_start: int
    line_end: int
    can_remove: bool = True
    impact_score: int = 1  # 影响分数（越大越重要）
    suggestion: str = ""


@dataclass
class VarLiveness:
    """变量活跃性信息"""
    var_name: str
    defined_at: Set[int] = field(default_factory=set)
    used_at: Set[int] = field(default_factory=set)
    last_def: int = -1
    last_use: int = -1
    
    def is_live_at(self, line: int) -> bool:
        """检查变量在某行是否活跃"""
        if line in self.used_at:
            return True
        if self.last_def >= 0 and line > self.last_def:
            return line <= self.last_use if self.last_use >= 0 else False
        return False
    
    def is_unused(self) -> bool:
        """检查变量是否未使用"""
        return len(self.used_at) == 0


class DataFlowContext:
    """数据流上下文"""
    
    def __init__(self):
        self.var_liveness: Dict[str, VarLiveness] = {}
        self.reachable_lines: Set[int] = set()
        self.active_vars: Dict[int, Set[str]] = {}  # line -> active vars
        self.def_use_chains: Dict[str, List[Tuple[int, int]]] = {}  # var -> [(def_line, use_line)]
    
    def mark_definition(self, var_name: str, line: int):
        """标记变量定义"""
        if var_name not in self.var_liveness:
            self.var_liveness[var_name] = VarLiveness(var_name)
        self.var_liveness[var_name].defined_at.add(line)
        self.var_liveness[var_name].last_def = line
    
    def mark_use(self, var_name: str, line: int):
        """标记变量使用"""
        if var_name not in self.var_liveness:
            self.var_liveness[var_name] = VarLiveness(var_name)
        self.var_liveness[var_name].used_at.add(line)
        self.var_liveness[var_name].last_use = line
    
    def mark_reachable(self, line: int):
        """标记行可达"""
        self.reachable_lines.add(line)
    
    def is_reachable(self, line: int) -> bool:
        """检查行是否可达"""
        return line in self.reachable_lines


class DeadCodeEliminator:
    """死代码消除优化器（增强版）"""
    
    def __init__(self):
        self.eliminated_count = 0
        self.dead_code_list: List[DeadCodeInfo] = []
        self.context = DataFlowContext()
        self.stats = {
            'branches_removed': 0,
            'unreachable_removed': 0,
            'unused_vars_removed': 0,
            'unused_funcs_removed': 0,
            'dead_stores_removed': 0,
            'empty_blocks_removed': 0,
            'total_lines_removed': 0
        }
        self.preserve_symbols: Set[str] = set()  # 需要保留的符号（如入口点、导出函数）
        self.call_graph: Dict[str, Set[str]] = {}  # 函数调用图
    
    def set_preserve_symbols(self, symbols: Set[str]):
        """设置需要保留的符号"""
        self.preserve_symbols = symbols
    
    def eliminate(self, statements: List[dict]) -> Tuple[List[dict], List[DeadCodeInfo]]:
        """
        消除死代码（主入口）
        
        Args:
            statements: 语句列表（AST节点字典形式）
        
        Returns:
            优化后的语句列表和死代码信息列表
        """
        # 第一遍：数据流分析
        self._analyze_data_flow(statements)
        
        # 第二遍：构建调用图
        self._build_call_graph(statements)
        
        # 第三遍：检测并消除死代码
        optimized = self._eliminate_dead_code_v2(statements)
        
        # 第四遍：清理未使用函数
        optimized = self._eliminate_unused_functions(optimized)
        
        return optimized, self.dead_code_list
    
    def _analyze_data_flow(self, statements: List[dict]):
        """数据流分析"""
        reachable = True
        
        for i, stmt in enumerate(statements):
            line = stmt.get('line', i + 1)
            stmt_type = stmt.get('type', '')
            
            if reachable:
                self.context.mark_reachable(line)
            
            # 分析变量定义
            if stmt_type in ('var_decl', 'assign'):
                var_name = stmt.get('name', '')
                if var_name:
                    self.context.mark_definition(var_name, line)
            
            # 分析变量使用
            used_vars = self._extract_used_vars(stmt)
            for var_name in used_vars:
                self.context.mark_use(var_name, line)
            
            # return 之后的代码不可达
            if stmt_type == 'return' and reachable:
                reachable = False
    
    def _build_call_graph(self, statements: List[dict]):
        """构建函数调用图"""
        for stmt in statements:
            if stmt.get('type') == 'function_decl':
                func_name = stmt.get('name', '')
                if func_name:
                    if func_name not in self.call_graph:
                        self.call_graph[func_name] = set()
                    
                    # 分析函数体中的调用
                    body = stmt.get('body', [])
                    for body_stmt in body:
                        if body_stmt.get('type') == 'call':
                            called_func = body_stmt.get('function', '')
                            if called_func:
                                self.call_graph[func_name].add(called_func)
    
    def _eliminate_dead_code_v2(self, statements: List[dict]) -> List[dict]:
        """消除死代码（增强版）"""
        optimized = []
        reachable = True
        
        for i, stmt in enumerate(statements):
            line = stmt.get('line', i + 1)
            stmt_type = stmt.get('type', '')
            
            # 检查可达性
            if not reachable:
                self._mark_dead_code(
                    DeadCodeType.UNREACHABLE,
                    stmt_type,
                    f"return语句后的不可达代码",
                    line, line
                )
                self.stats['unreachable_removed'] += 1
                continue
            
            # 检查条件分支
            if stmt_type == 'if':
                stmt = self._optimize_if_branch(stmt, line)
                if stmt is None:
                    continue
            
            # 检查空代码块
            if stmt_type == 'block' and not stmt.get('statements', []):
                self._mark_dead_code(
                    DeadCodeType.EMPTY_BLOCK,
                    "代码块",
                    "空代码块",
                    line, line
                )
                self.stats['empty_blocks_removed'] += 1
                continue
            
            # 检查未使用变量
            if stmt_type == 'var_decl':
                var_name = stmt.get('name', '')
                if var_name and var_name in self.context.var_liveness:
                    if self.context.var_liveness[var_name].is_unused():
                        # 检查是否有副作用（如调用构造函数）
                        init = stmt.get('value')
                        if not self._has_side_effect(init):
                            self._mark_dead_code(
                                DeadCodeType.UNUSED_VAR,
                                f"变量 '{var_name}'",
                                f"变量已定义但从未使用",
                                line, line,
                                suggestion=f"删除变量 '{var_name}'"
                            )
                            self.stats['unused_vars_removed'] += 1
                            continue
            
            # 检查死存储
            if stmt_type == 'assign':
                var_name = stmt.get('name', '')
                if var_name and var_name in self.context.var_liveness:
                    liveness = self.context.var_liveness[var_name]
                    # 如果赋值后没有使用，且下次赋值前也没有使用
                    if self._is_dead_store(var_name, line, statements[i:]):
                        self._mark_dead_code(
                            DeadCodeType.DEAD_STORE,
                            f"赋值 '{var_name}'",
                            f"赋值后未被使用",
                            line, line,
                            suggestion=f"删除或使用变量 '{var_name}'"
                        )
                        self.stats['dead_stores_removed'] += 1
                        # 保留语句但不执行赋值（简化处理：跳过）
                        continue
            
            optimized.append(stmt)
            
            # return 后标记不可达
            if stmt_type == 'return':
                reachable = False
        
        return optimized
    
    def _optimize_if_branch(self, stmt: dict, line: int) -> Optional[dict]:
        """优化if分支"""
        condition = stmt.get('condition', '')
        
        # 检查条件是否为常量
        const_value = self._evaluate_constant_condition(condition)
        
        if const_value is True:
            # 条件永远为真
            self._mark_dead_code(
                DeadCodeType.CONSTANT_BRANCH,
                "if语句",
                f"条件永远为真，消除else分支",
                line, line
            )
            self.stats['branches_removed'] += 1
            # 只保留then分支
            then_body = stmt.get('then_body', [])
            if then_body:
                return {'type': 'block', 'statements': then_body, 'line': line}
            return None
        
        elif const_value is False:
            # 条件永远为假
            self._mark_dead_code(
                DeadCodeType.CONSTANT_BRANCH,
                "if语句",
                f"条件永远为假，消除then分支",
                line, line
            )
            self.stats['branches_removed'] += 1
            # 只保留else分支
            else_body = stmt.get('else_body', [])
            if else_body:
                return {'type': 'block', 'statements': else_body, 'line': line}
            return None
        
        return stmt
    
    def _eliminate_unused_functions(self, statements: List[dict]) -> List[dict]:
        """消除未使用的函数"""
        # 找到所有被调用的函数
        called_funcs = set()
        for callers in self.call_graph.values():
            called_funcs.update(callers)
        
        # 主函数和导出函数需要保留
        required_funcs = self.preserve_symbols | {'主函数', 'main'}
        
        optimized = []
        for stmt in statements:
            if stmt.get('type') == 'function_decl':
                func_name = stmt.get('name', '')
                
                # 检查是否被需要
                if func_name not in called_funcs and func_name not in required_funcs:
                    self._mark_dead_code(
                        DeadCodeType.UNUSED_FUNC,
                        f"函数 '{func_name}'",
                        f"函数已定义但从未被调用",
                        stmt.get('line', 0), stmt.get('line', 0),
                        suggestion=f"删除函数 '{func_name}' 或标记为导出"
                    )
                    self.stats['unused_funcs_removed'] += 1
                    continue
            
            optimized.append(stmt)
        
        return optimized
    
    def _evaluate_constant_condition(self, condition: Any) -> Optional[bool]:
        """评估常量条件"""
        if isinstance(condition, bool):
            return condition
        if isinstance(condition, (int, float)):
            return condition != 0
        if isinstance(condition, str):
            # 检查是否是字面量
            condition_lower = condition.lower()
            if condition_lower in ('真', 'true', '1'):
                return True
            if condition_lower in ('假', 'false', '0'):
                return False
        return None
    
    def _extract_used_vars(self, stmt: dict) -> List[str]:
        """提取语句中使用的变量"""
        used = []
        
        # 直接引用的变量
        if 'name' in stmt and stmt.get('type') in ('read', 'use'):
            used.append(stmt['name'])
        
        # 表达式中的变量
        if 'value' in stmt:
            expr = str(stmt['value'])
            # 简化：提取标识符
            import re
            pattern = r'[a-zA-Z_\u4e00-\u9fff][a-zA-Z0-9_\u4e00-\u9fff]*'
            used.extend(re.findall(pattern, expr))
        
        # 条件中的变量
        if 'condition' in stmt:
            expr = str(stmt['condition'])
            import re
            pattern = r'[a-zA-Z_\u4e00-\u9fff][a-zA-Z0-9_\u4e00-\u9fff]*'
            used.extend(re.findall(pattern, expr))
        
        return list(set(used))  # 去重
    
    def _has_side_effect(self, expr: Any) -> bool:
        """检查表达式是否有副作用"""
        if expr is None:
            return False
        
        # 函数调用有副作用
        if isinstance(expr, dict) and expr.get('type') == 'call':
            return True
        
        # 包含new/delete有副作用
        expr_str = str(expr)
        if '新建' in expr_str or '删除' in expr_str or 'new' in expr_str:
            return True
        
        return False
    
    def _is_dead_store(self, var_name: str, line: int, remaining_stmts: List[dict]) -> bool:
        """检查是否是死存储"""
        liveness = self.context.var_liveness.get(var_name)
        if not liveness:
            return False
        
        # 如果变量后续还有使用，不是死存储
        for use_line in liveness.used_at:
            if use_line > line:
                return False
        
        # 如果变量在后续还有定义，检查中间是否有使用
        for def_line in liveness.defined_at:
            if def_line > line:
                # 两次定义之间是否有使用
                for use_line in liveness.used_at:
                    if line < use_line < def_line:
                        return False
        
        return True
    
    def _mark_dead_code(
        self,
        code_type: DeadCodeType,
        node_type: str,
        reason: str,
        line_start: int,
        line_end: int,
        can_remove: bool = True,
        suggestion: str = ""
    ):
        """标记死代码"""
        info = DeadCodeInfo(
            code_type=code_type,
            reason=reason,
            location=f"行{line_start}",
            line_start=line_start,
            line_end=line_end,
            can_remove=can_remove,
            suggestion=suggestion
        )
        self.dead_code_list.append(info)
        self.eliminated_count += 1
        self.stats['total_lines_removed'] += (line_end - line_start + 1)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            'total_eliminated': self.eliminated_count,
            'dead_code_by_type': {
                code_type.value: sum(1 for d in self.dead_code_list if d.code_type == code_type)
                for code_type in DeadCodeType
            },
            'dead_code_list': [
                {
      'type': info.code_type.value,
                    'reason': info.reason,
                    'location': info.location,
                    'suggestion': info.suggestion
                }
                for info in self.dead_code_list[:20]
            ]
        }
    
    def generate_report(self) -> str:
        """生成优化报告"""
        lines = [
            "=" * 70,
            "死代码消除优化报告",
            "=" * 70,
            "",
            "📈 统计:",
            f"  消除分支: {self.stats['branches_removed']}",
            f"  消除不可达代码: {self.stats['unreachable_removed']}",
            f"  消除未使用变量: {self.stats['unused_vars_removed']}",
            f"  消除未使用函数: {self.stats['unused_funcs_removed']}",
            f"  消除死存储: {self.stats['dead_stores_removed']}",
            f"  消除空代码块: {self.stats['empty_blocks_removed']}",
            f"  总计消除行数: {self.stats['total_lines_removed']}",
            "",
        ]
        
        if self.dead_code_list:
            lines.append("🗑️  死代码详情:")
            lines.append("-" * 70)
            for info in self.dead_code_list[:20]:
                icon = {
                    DeadCodeType.UNREACHABLE: "❌",
                    DeadCodeType.UNUSED_VAR: "⚠️",
                    DeadCodeType.UNUSED_FUNC: "⚠️",
                    DeadCodeType.DEAD_STORE: "📦",
                    DeadCodeType.CONSTANT_BRANCH: "🔀",
                    DeadCodeType.EMPTY_BLOCK: "📭",
                    DeadCodeType.REDUNDANT_CODE: "♻️"
                }.get(info.code_type, "🗑️")
                
                lines.append(f"  {icon} [{info.code_type.value}] 行{info.line_start}: {info.reason}")
                if info.suggestion:
                    lines.append(f"      💡 {info.suggestion}")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)


# 便捷函数
def eliminate_dead_code(statements: List[dict], preserve: Set[str] = None) -> Tuple[List[dict], List[DeadCodeInfo]]:
    """
    消除死代码的便捷函数
    
    Args:
        statements: 语句列表
        preserve: 需要保留的符号集合
    
    Returns:
        优化后的语句列表和死代码信息列表
    """
    eliminator = DeadCodeEliminator()
    if preserve:
        eliminator.set_preserve_symbols(preserve)
    return eliminator.eliminate(statements)


# 测试
if __name__ == '__main__':
    print("=== 死代码消除测试 ===\n")
    
    test_statements = [
        {'type': 'var_decl', 'name': 'x', 'value': 10, 'line': 1},
        {'type': 'var_decl', 'name': 'y', 'value': 20, 'line': 2},  # 未使用
        {'type': 'var_decl', 'name': 'z', 'line': 3},
        {'type': 'assign', 'name': 'z', 'value': 'x', 'line': 4},
        {'type': 'return', 'value': 'z', 'line': 5},
        {'type': 'var_decl', 'name': 'after_return', 'line': 6},  # 不可达
        {'type': 'function_decl', 'name': 'unused_func', 'body': [], 'line': 7}  # 未使用
    ]
    
    eliminator = DeadCodeEliminator()
    eliminator.set_preserve_symbols({'主函数'})
    
    optimized, dead_code = eliminator.eliminate(test_statements)
    
    print(f"原始语句数: {len(test_statements)}")
    print(f"优化后语句数: {len(optimized)}")
    print(f"消除死代码数: {len(dead_code)}")
    print()
    
    print(eliminator.generate_report())
    
    print("\n=== 测试完成 ===")
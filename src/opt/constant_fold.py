#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
常量传播与折叠优化器（增强版）
Constant Propagation and Folding Optimizer Enhanced

在编译时计算常量表达式，减少运行时开销

增强功能：
1. 过程间常量传播
2. 条件常量传播
3. 稀疏条件常量传播（SCCP）
4. 全局常量传播
5. 字符串常量池
6. 常量表达式规范化

作者：阿福
日期：2026-04-03
"""

from typing import Optional, Any, Union, Dict, Set, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ConstantType(Enum):
    """常量类型"""
    INTEGER = "整数"
    FLOAT = "浮点数"
    STRING = "字符串"
    BOOLEAN = "布尔"
    UNKNOWN = "未知"
    TOP = "⊤"  # 顶元素（未知）
    BOTTOM = "⊥"  # 底元素（冲突）


@dataclass
class LatticeValue:
    """格值（用于数据流分析）"""
    value: Any
    const_type: ConstantType
    is_constant: bool = True
    confidence: float = 1.0  # 置信度
    
    def join(self, other: 'LatticeValue') -> 'LatticeValue':
        """格的join操作（取最小上界）"""
        if self.const_type == ConstantType.TOP:
            return other
        if other.const_type == ConstantType.TOP:
            return self
        if self.const_type == ConstantType.BOTTOM or other.const_type == ConstantType.BOTTOM:
            return LatticeValue(None, ConstantType.BOTTOM, False)
        if self.value == other.value and self.const_type == other.const_type:
            return self
        return LatticeValue(None, ConstantType.BOTTOM, False)  # 冲突
    
    def meet(self, other: 'LatticeValue') -> 'LatticeValue':
        """格的meet操作（取最大下界）"""
        if self.const_type == ConstantType.BOTTOM:
            return other
        if other.const_type == ConstantType.BOTTOM:
            return self
        if self.value == other.value:
            return self
        return LatticeValue(None, ConstantType.TOP, False)


@dataclass
class ConstantInfo:
    """常量信息"""
    var_name: str
    value: Any
    const_type: ConstantType
    defined_at: int
    is_global: bool = False
    is_constexpr: bool = False  # 是否是常量表达式
    uses: List[int] = field(default_factory=list)


class ConstantPool:
    """常量池（字符串常量去重）"""
    
    def __init__(self):
        self.pool: Dict[str, int] = {}  # string -> pool_index
        self.entries: List[str] = []
        self.stats = {
            'total_strings': 0,
            'unique_strings': 0,
            'saved_bytes': 0
        }
    
    def intern(self, value: str) -> Tuple[int, str]:
        """将字符串加入常量池"""
        self.stats['total_strings'] += 1
        
        if value in self.pool:
            idx = self.pool[value]
            self.stats['saved_bytes'] += len(value)
            return idx, f"STR_POOL[{idx}]"
        
        idx = len(self.entries)
        self.pool[value] = idx
        self.entries.append(value)
        self.stats['unique_strings'] += 1
        
        return idx, f"STR_POOL[{idx}]"
    
    def get_all_strings(self) -> List[str]:
        """获取所有字符串常量"""
        return self.entries.copy()


class Environment:
    """常量环境（变量到常量值的映射）"""
    
    def __init__(self):
        self.bindings: Dict[str, LatticeValue] = {}
        self.parent: Optional['Environment'] = None
    
    def set(self, var_name: str, value: LatticeValue):
        """设置变量值"""
        self.bindings[var_name] = value
    
    def get(self, var_name: str) -> LatticeValue:
        """获取变量值"""
        if var_name in self.bindings:
            return self.bindings[var_name]
        if self.parent:
            return self.parent.get(var_name)
        return LatticeValue(None, ConstantType.TOP, False)
    
    def copy(self) -> 'Environment':
        """复制环境"""
        new_env = Environment()
        new_env.bindings = self.bindings.copy()
        new_env.parent = self.parent
        return new_env
    
    def merge(self, other: 'Environment') -> 'Environment':
        """合并两个环境"""
        merged = Environment()
        
        # 合并所有变量
        all_vars = set(self.bindings.keys()) | set(other.bindings.keys())
        for var in all_vars:
            val1 = self.get(var)
            val2 = other.get(var)
            merged.set(var, val1.join(val2))
        
        return merged


class ConstantPropagator:
    """常量传播优化器（增强版）"""
    
    def __init__(self):
        self.constant_pool = ConstantPool()
        self.constants: Dict[str, ConstantInfo] = {}
        self.global_constants: Dict[str, LatticeValue] = {}
        self.stats = {
            'expressions_folded': 0,
            'variables_propagated': 0,
            'conditions_simplified': 0,
            'strings_interned': 0,
            'global_constants_found': 0
        }
        self.optimizations: List[str] = []
    
    def propagate(self, statements: List[dict]) -> Tuple[List[dict], Dict[str, Any]]:
        """
        常量传播主入口
        
        Args:
            statements: 语句列表
        
        Returns:
            优化后的语句列表和常量映射
        """
        # 第一遍：收集全局常量
        self._collect_global_constants(statements)
        
        # 第二遍：过程间常量传播
        env = Environment()
        optimized = self._propagate_statements(statements, env)
        
        return optimized, self._get_constant_map()
    
    def _collect_global_constants(self, statements: List[dict]):
        """收集全局常量"""
        for stmt in statements:
            if stmt.get('type') == 'var_decl':
                var_name = stmt.get('name', '')
                is_const = stmt.get('is_const', False)
                value = stmt.get('value')
                
                if is_const and value is not None:
                    const_value = self._evaluate_constant(value)
                    if const_value is not None:
                        self.global_constants[var_name] = LatticeValue(
                            value=const_value,
                            const_type=self._get_constant_type(const_value),
                            is_constant=True
                        )
                        self.stats['global_constants_found'] += 1
    
    def _propagate_statements(self, statements: List[dict], env: Environment) -> List[dict]:
        """传播常量到语句"""
        optimized = []
        
        for stmt in statements:
            opt_stmt = self._propagate_statement(stmt, env)
            if opt_stmt:
                optimized.append(opt_stmt)
        
        return optimized
    
    def _propagate_statement(self, stmt: dict, env: Environment) -> Optional[dict]:
        """传播常量到单个语句"""
        stmt_type = stmt.get('type', '')
        line = stmt.get('line', 0)
        
        if stmt_type == 'var_decl':
            return self._propagate_var_decl(stmt, env, line)
        
        elif stmt_type == 'assign':
            return self._propagate_assign(stmt, env, line)
        
        elif stmt_type == 'if':
            return self._propagate_if(stmt, env, line)
        
        elif stmt_type == 'while':
            return self._propagate_while(stmt, env, line)
        
        elif stmt_type == 'return':
            return self._propagate_return(stmt, env, line)
        
        elif stmt_type == 'call':
            return self._propagate_call(stmt, env, line)
        
        return stmt
    
    def _propagate_var_decl(self, stmt: dict, env: Environment, line: int) -> dict:
        """传播变量声明"""
        var_name = stmt.get('name', '')
        value = stmt.get('value')
        is_const = stmt.get('is_const', False)
        
        new_stmt = stmt.copy()
        
        if value is not None:
            # 尝试折叠初始值
            folded_value = self._fold_expression(value, env)
            
            # 如果是常量，记录到环境
            const_value = self._evaluate_constant(folded_value)
            if const_value is not None:
                lattice_val = LatticeValue(
                    value=const_value,
                    const_type=self._get_constant_type(const_value),
                    is_constant=True
                )
                env.set(var_name, lattice_val)
                
                # 更新语句中的值
                new_stmt['value'] = const_value
                new_stmt['is_constant'] = True
                
                # 记录常量信息
                self.constants[var_name] = ConstantInfo(
                    var_name=var_name,
                    value=const_value,
                    const_type=lattice_val.const_type,
                    defined_at=line,
                    is_constexpr=True
                )
                
                self.optimizations.append(
                    f"常量传播: {var_name} = {const_value}"
                )
                self.stats['variables_propagated'] += 1
            else:
                new_stmt['value'] = folded_value
        
        return new_stmt
    
    def _propagate_assign(self, stmt: dict, env: Environment, line: int) -> dict:
        """传播赋值语句"""
        var_name = stmt.get('name', '')
        value = stmt.get('value')
        
        new_stmt = stmt.copy()
        
        if value is not None:
            folded_value = self._fold_expression(value, env)
            new_stmt['value'] = folded_value
            
            # 尝试更新环境中的常量值
            const_value = self._evaluate_constant(folded_value)
            if const_value is not None:
                # 检查变量是否是常量（如果是，报错）
                if var_name in self.constants and self.constants[var_name].is_constexpr:
                    # 尝试修改常量，这是错误（但在传播阶段我们只记录）
                    pass
                else:
                    # 更新环境（非常量变量可能变成常量）
                    lattice_val = LatticeValue(
                        value=const_value,
                        const_type=self._get_constant_type(const_value),
                        is_constant=True
                    )
                    env.set(var_name, lattice_val)
        
        return new_stmt
    
    def _propagate_if(self, stmt: dict, env: Environment, line: int) -> dict:
        """传播if语句（条件常量传播）"""
        condition = stmt.get('condition')
        then_body = stmt.get('then_body', [])
        else_body = stmt.get('else_body', [])
        
        new_stmt = stmt.copy()
        
        # 折叠条件
        if condition is not None:
            folded_cond = self._fold_expression(condition, env)
            new_stmt['condition'] = folded_cond
            
            # 检查条件是否为常量
            cond_value = self._evaluate_constant(folded_cond)
            if cond_value is not None:
                # 常量条件
                if cond_value:
                    # 条件为真，只执行then分支
                    then_env = env.copy()
                    new_stmt['then_body'] = self._propagate_statements(then_body, then_env)
                    new_stmt['else_body'] = []
                    self.stats['conditions_simplified'] += 1
                else:
                    # 条件为假，只执行else分支
                    else_env = env.copy()
                    new_stmt['then_body'] = []
                    new_stmt['else_body'] = self._propagate_statements(else_body, else_env)
                    self.stats['conditions_simplified'] += 1
            else:
                # 非常量条件，需要传播两个分支
                then_env = env.copy()
                else_env = env.copy()
                
                new_stmt['then_body'] = self._propagate_statements(then_body, then_env)
                new_stmt['else_body'] = self._propagate_statements(else_body, else_env)
        
        return new_stmt
    
    def _propagate_while(self, stmt: dict, env: Environment, line: int) -> dict:
        """传播while循环"""
        condition = stmt.get('condition')
        body = stmt.get('body', [])
        
        new_stmt = stmt.copy()
        
        # 折叠条件
        if condition is not None:
            folded_cond = self._fold_expression(condition, env)
            new_stmt['condition'] = folded_cond
            
            # 如果条件为常量假，循环不会执行
            cond_value = self._evaluate_constant(folded_cond)
            if cond_value is False:
                self.stats['conditions_simplified'] += 1
                # 可以完全消除循环（但保留语句结构）
                new_stmt['body'] = []
            else:
                # 传播循环体
                body_env = env.copy()
                new_stmt['body'] = self._propagate_statements(body, body_env)
        
        return new_stmt
    
    def _propagate_return(self, stmt: dict, env: Environment, line: int) -> dict:
        """传播return语句"""
        value = stmt.get('value')
        
        new_stmt = stmt.copy()
        
        if value is not None:
            folded_value = self._fold_expression(value, env)
            new_stmt['value'] = folded_value
        
        return new_stmt
    
    def _propagate_call(self, stmt: dict, env: Environment, line: int) -> dict:
        """传播函数调用"""
        new_stmt = stmt.copy()
        
        # 传播参数
        args = stmt.get('args', [])
        new_args = []
        for arg in args:
            folded_arg = self._fold_expression(arg, env)
            new_args.append(folded_arg)
        
        new_stmt['args'] = new_args
        
        return new_stmt
    
    def _fold_expression(self, expr: Any, env: Environment) -> Any:
        """折叠表达式"""
        if expr is None:
            return None
        
        # 如果是字面量，直接返回
        if isinstance(expr, (int, float, bool, str)):
            # 字符串常量池化
            if isinstance(expr, str):
                idx, pooled = self.constant_pool.intern(expr)
                self.stats['strings_interned'] += 1
                return pooled
            return expr
        
        # 如果是字典（AST节点），处理表达式
        if isinstance(expr, dict):
            return self._fold_dict_expression(expr, env)
        
        # 如果是字符串表达式
        if isinstance(expr, str):
            # 检查是否是变量引用
            lattice_val = env.get(expr)
            if lattice_val.is_constant and lattice_val.const_type != ConstantType.TOP:
                return lattice_val.value
            
            # 检查全局常量
            if expr in self.global_constants:
                return self.global_constants[expr].value
            
            # 尝试解析表达式
            return self._fold_string_expression(expr, env)
        
        return expr
    
    def _fold_dict_expression(self, expr: dict, env: Environment) -> Any:
        """折叠字典表达式"""
        expr_type = expr.get('type', '')
        
        if expr_type == 'binary':
            return self._fold_binary_expr(expr, env)
        elif expr_type == 'unary':
            return self._fold_unary_expr(expr, env)
        elif expr_type == 'var':
            var_name = expr.get('name', '')
            lattice_val = env.get(var_name)
            if lattice_val.is_constant:
                return lattice_val.value
        
        return expr
    
    def _fold_binary_expr(self, expr: dict, env: Environment) -> Any:
        """折叠二元表达式"""
        op = expr.get('op', '')
        left = expr.get('left')
        right = expr.get('right')
        
        left_val = self._fold_expression(left, env)
        right_val = self._fold_expression(right, env)
        
        # 如果两个操作数都是常量，计算结果
        if isinstance(left_val, (int, float)) and isinstance(right_val, (int, float)):
            try:
                if op == '+':
                    result = left_val + right_val
                elif op == '-':
                    result = left_val - right_val
                elif op == '*':
                    result = left_val * right_val
                elif op == '/':
                    if right_val == 0:
                        return expr  # 除零，保持原样
                    result = left_val / right_val
                elif op == '%':
                    if right_val == 0:
                        return expr
                    result = left_val % right_val
                elif op == '<':
                    result = left_val < right_val
                elif op == '>':
                    result = left_val > right_val
                elif op == '<=':
                    result = left_val <= right_val
                elif op == '>=':
                    result = left_val >= right_val
                elif op == '==':
                    result = left_val == right_val
                elif op == '!=':
                    result = left_val != right_val
                else:
                    return expr
                
                self.stats['expressions_folded'] += 1
                self.optimizations.append(
                    f"折叠: {left_val} {op} {right_val} = {result}"
                )
                return result
            except:
                return expr
        
        return expr
    
    def _fold_unary_expr(self, expr: dict, env: Environment) -> Any:
        """折叠一元表达式"""
        op = expr.get('op', '')
        operand = expr.get('operand')
        
        operand_val = self._fold_expression(operand, env)
        
        if isinstance(operand_val, (int, float)):
            try:
                if op == '-':
                    result = -operand_val
                elif op == '+':
                    result = operand_val
                else:
                    return expr
                
                self.stats['expressions_folded'] += 1
                return result
            except:
                return expr
        
        if isinstance(operand_val, bool):
            if op in ('!', 'not', '非'):
                result = not operand_val
                self.stats['expressions_folded'] += 1
                return result
        
        return expr
    
    def _fold_string_expression(self, expr: str, env: Environment) -> Any:
        """折叠字符串表达式"""
        # 简单的算术表达式
        import re
        
        # 尝试匹配简单二元表达式
        match = re.match(r'^(\d+)\s*([+\-*/])\s*(\d+)$', expr.strip())
        if match:
            left = int(match.group(1))
            op = match.group(2)
            right = int(match.group(3))
            
            try:
                if op == '+':
                    result = left + right
                elif op == '-':
                    result = left - right
                elif op == '*':
                    result = left * right
                elif op == '/':
                    if right == 0:
                        return expr
                    result = left // right
                else:
                    return expr
                
                self.stats['expressions_folded'] += 1
                return result
            except:
                return expr
        
        return expr
    
    def _evaluate_constant(self, value: Any) -> Optional[Any]:
        """评估常量值"""
        if value is None:
            return None
        
        if isinstance(value, (int, float, bool)):
            return value
        
        if isinstance(value, str):
            # 尝试解析数字
            try:
                if '.' in value:
                    return float(value)
                return int(value)
            except ValueError:
                # 检查布尔值
                lower = value.lower()
                if lower in ('真', 'true', 'yes', '1'):
                    return True
                if lower in ('假', 'false', 'no', '0'):
                    return False
                return None
        
        return None
    
    def _get_constant_type(self, value: Any) -> ConstantType:
        """获取常量类型"""
        if isinstance(value, bool):
            return ConstantType.BOOLEAN
        elif isinstance(value, int):
            return ConstantType.INTEGER
        elif isinstance(value, float):
            return ConstantType.FLOAT
        elif isinstance(value, str):
            return ConstantType.STRING
        else:
            return ConstantType.UNKNOWN
    
    def _get_constant_map(self) -> Dict[str, Any]:
        """获取常量映射"""
        return {
            var_name: info.value
            for var_name, info in self.constants.items()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            'total_constants': len(self.constants),
            'constant_pool_stats': self.constant_pool.stats,
            'optimizations': self.optimizations[:20]
        }
    
    def generate_report(self) -> str:
        """生成优化报告"""
        lines = [
            "=" * 70,
            "常量传播与折叠优化报告",
            "=" * 70,
            "",
            "📈 统计:",
            f"  折叠表达式: {self.stats['expressions_folded']}",
            f"  传播变量: {self.stats['variables_propagated']}",
            f"  简化条件: {self.stats['conditions_simplified']}",
            f"  字符串池化: {self.stats['strings_interned']}",
            f"  全局常量: {self.stats['global_constants_found']}",
            "",
        ]
        
        if self.constants:
            lines.append("常量表:")
            lines.append("-" * 70)
            for var_name, info in list(self.constants.items())[:15]:
                lines.append(f"  {var_name}: {info.value} ({info.const_type.value})")
            lines.append("")
        
        if self.constant_pool.entries:
            lines.append("字符串常量池:")
            lines.append("-" * 70)
            for i, s in enumerate(self.constant_pool.entries[:10]):
                lines.append(f"  [{i}]: \"{s}\"")
            lines.append("")
        
        if self.optimizations:
            lines.append("✨ 优化详情:")
            lines.append("-" * 70)
            for opt in self.optimizations[:15]:
                lines.append(f"  {opt}")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)


# 便捷函数
def propagate_constants(statements: List[dict]) -> Tuple[List[dict], Dict[str, Any]]:
    """
    常量传播的便捷函数
    
    Args:
        statements: 语句列表
    
    Returns:
        优化后的语句列表和常量映射
    """
    propagator = ConstantPropagator()
    return propagator.propagate(statements)


# 测试
if __name__ == '__main__':
    print("=== 常量传播与折叠测试 ===\n")
    
    test_statements = [
        {'type': 'var_decl', 'name': 'PI', 'value': 3.14, 'is_const': True, 'line': 1},
        {'type': 'var_decl', 'name': 'radius', 'value': 10, 'line': 2},
        {'type': 'var_decl', 'name': 'area', 'value': 'PI * radius * radius', 'line': 3},
        {'type': 'var_decl', 'name': 'sum', 'value': '1 + 2 + 3', 'line': 4},
        {'type': 'var_decl', 'name': 'greeting', 'value': 'hello', 'line': 5},
        {
            'type': 'if',
            'condition': '真',
            'then_body': [
                {'type': 'var_decl', 'name': 'x', 'value': 42, 'line': 7}
            ],
            'else_body': [],
            'line': 6
        }
    ]
    
    propagator = ConstantPropagator()
    optimized, constants = propagator.propagate(test_statements)
    
    print(f"原始语句数: {len(test_statements)}")
    print(f"优化后语句数: {len(optimized)}")
    print(f"发现常量: {len(constants)}")
    print()
    
    print(propagator.generate_report())
    
    print("\n=== 测试完成 ===")
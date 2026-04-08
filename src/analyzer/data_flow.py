#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据流分析器 - Data Flow Analyzer

功能：
1. 定义-使用链（Def-Use Chain）
2. 活跃变量分析（Live Variables）
3. 可达定义分析（Reaching Definitions）
4. 常量传播（Constant Propagation）
5. 污点分析（Taint Analysis）

作者：阿福
日期：2026-04-03
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


class VarState(Enum):
    """变量状态"""

    UNDEFINED = "undefined"  # 未定义
    DEFINED = "defined"  # 已定义
    USED = "used"  # 已使用
    CONSTANT = "constant"  # 常量
    TAINTED = "tainted"  # 污染


@dataclass
class Definition:
    """定义点"""

    var_name: str
    line_number: int
    value: Optional[str] = None  # 值（如果已知）
    is_constant: bool = False
    source: str = "unknown"  # 来源（用于污点分析）


@dataclass
class Use:
    """使用点"""

    var_name: str
    line_number: int
    use_type: str  # "read", "write", "call", "return"


@dataclass
class DefUseChain:
    """定义-使用链"""

    var_name: str
    definitions: List[Definition] = field(default_factory=list)
    uses: List[Use] = field(default_factory=list)

    def add_definition(self, definition: Definition):
        """添加定义"""
        self.definitions.append(definition)

    def add_use(self, use: Use):
        """添加使用"""
        self.uses.append(use)

    def get_reaching_defs(self, use_line: int) -> List[Definition]:
        """获取到达某使用点的定义"""
        reaching = []
        for defn in self.definitions:
            if defn.line_number < use_line:
                # 检查是否被后续定义覆盖
                is_killed = False
                for other_def in self.definitions:
                    if (
                        other_def.line_number > defn.line_number
                        and other_def.line_number < use_line
                    ):
                        is_killed = True
                        break
                if not is_killed:
                    reaching.append(defn)
        return reaching


@dataclass
class LiveVarInfo:
    """活跃变量信息"""

    var_name: str
    defined_at: int
    last_used_at: Optional[int] = None
    is_live_at_exit: bool = False


@dataclass
class TaintInfo:
    """污点信息"""

    var_name: str
    taint_source: str
    tainted_lines: List[int]
    sanitize_lines: List[int] = field(default_factory=list)
    is_sanitized: bool = False


@dataclass
class DataFlowIssue:
    """数据流问题"""

    issue_type: str
    message: str
    var_name: str
    line_number: int
    severity: str  # "error", "warning", "info"
    suggestion: str


class SymbolTable:
    """符号表（用于数据流分析）"""

    def __init__(self):
        self.symbols: Dict[str, VarState] = {}
        self.values: Dict[str, Optional[str]] = {}
        self.taint_sources: Dict[str, str] = {}

    def define(
        self, var_name: str, value: Optional[str] = None, source: str = "unknown"
    ):
        """定义变量"""
        self.symbols[var_name] = VarState.DEFINED
        self.values[var_name] = value
        if source != "unknown":
            self.taint_sources[var_name] = source

    def use(self, var_name: str):
        """使用变量"""
        if var_name in self.symbols:
            self.symbols[var_name] = VarState.USED

    def is_defined(self, var_name: str) -> bool:
        """检查变量是否已定义"""
        return var_name in self.symbols and self.symbols[var_name] in (
            VarState.DEFINED,
            VarState.USED,
            VarState.CONSTANT,
            VarState.TAINTED,
        )

    def get_value(self, var_name: str) -> Optional[str]:
        """获取变量值"""
        return self.values.get(var_name)

    def set_constant(self, var_name: str, value: str):
        """设置为常量"""
        self.symbols[var_name] = VarState.CONSTANT
        self.values[var_name] = value

    def set_tainted(self, var_name: str, source: str):
        """设置为污染"""
        self.symbols[var_name] = VarState.TAINTED
        self.taint_sources[var_name] = source


class DataFlowAnalyzer:
    """数据流分析器"""

    def __init__(self):
        self.def_use_chains: Dict[str, DefUseChain] = {}
        self.live_vars: Dict[str, LiveVarInfo] = {}
        self.taint_info: Dict[str, TaintInfo] = {}
        self.symbol_table = SymbolTable()
        self.issues: List[DataFlowIssue] = []
        self.constants: Dict[str, str] = {}
        # 默认污点源：用户输入相关函数
        self.taint_sources: Set[str] = set()

    # ==================== 定义-使用链分析 ====================

    def build_def_use_chains(self, statements: List[dict]) -> Dict[str, DefUseChain]:
        """构建定义-使用链

        Args:
            statements: 语句列表

        Returns:
            变量名到Def-Use链的映射
        """
        chains: Dict[str, DefUseChain] = {}

        for stmt in statements:
            stmt_type = stmt.get("type", "")
            line = stmt.get("line", 0)

            # 变量定义
            if stmt_type in ("var_decl", "assign"):
                var_name = stmt.get("name", "")
                if not var_name:
                    continue

                if var_name not in chains:
                    chains[var_name] = DefUseChain(var_name)

                value = stmt.get("value")
                is_const = stmt.get("is_const", False)

                chains[var_name].add_definition(
                    Definition(
                        var_name=var_name,
                        line_number=line,
                        value=str(value) if value else None,
                        is_constant=is_const,
                    )
                )

            # 变量使用
            elif stmt_type in ("read", "call", "return"):
                vars_used = self._extract_used_vars(stmt)
                for var_name in vars_used:
                    if var_name not in chains:
                        chains[var_name] = DefUseChain(var_name)

                    chains[var_name].add_use(
                        Use(var_name=var_name, line_number=line, use_type=stmt_type)
                    )

            # 条件表达式中的变量使用
            elif stmt_type == "if":
                condition = stmt.get("condition", "")
                vars_used = self._extract_vars_from_expr(condition)
                for var_name in vars_used:
                    if var_name not in chains:
                        chains[var_name] = DefUseChain(var_name)
                    chains[var_name].add_use(
                        Use(var_name=var_name, line_number=line, use_type="condition")
                    )

        self.def_use_chains = chains
        return chains

    def _extract_used_vars(self, stmt: dict) -> List[str]:
        """从语句中提取使用的变量"""
        used = []

        # 直接使用的变量
        if "name" in stmt:
            used.append(stmt["name"])

        # 表达式中的变量
        if "value" in stmt:
            used.extend(self._extract_vars_from_expr(str(stmt["value"])))

        # 参数列表
        if "args" in stmt:
            for arg in stmt["args"]:
                used.extend(self._extract_vars_from_expr(str(arg)))

        return used

    def _extract_vars_from_expr(self, expr: str) -> List[str]:
        """从表达式中提取变量名（简化实现）"""
        # 简化：通过正则表达式提取标识符
        import re

        # 匹配中文和英文标识符
        pattern = r"[a-zA-Z_\u4e00-\u9fff][a-zA-Z0-9_\u4e00-\u9fff]*"
        matches = re.findall(pattern, expr)

        # 过滤关键字
        keywords = {
            "如果",
            "否则",
            "循环",
            "当",
            "返回",
            "整数型",
            "浮点型",
            "字符型",
            "布尔型",
            "空指针",
            "真",
            "假",
        }

        return [m for m in matches if m not in keywords]

    # ==================== 活跃变量分析 ====================

    def analyze_live_variables(
        self, statements: List[dict], params: List[str] = None
    ) -> Dict[str, LiveVarInfo]:
        """活跃变量分析

        Args:
            statements: 语句列表
            params: 参数列表

        Returns:
            变量名到活跃信息的映射
        """
        live_vars: Dict[str, LiveVarInfo] = {}

        # 参数视为在入口处定义
        if params:
            for param in params:
                live_vars[param] = LiveVarInfo(var_name=param, defined_at=0)

        # 后向遍历：从出口到入口
        for stmt in reversed(statements):
            stmt_type = stmt.get("type", "")
            line = stmt.get("line", 0)

            # 变量定义/赋值
            if stmt_type in ("var_decl", "assign"):
                var_name = stmt.get("name", "")
                if not var_name:
                    continue

                if var_name not in live_vars:
                    live_vars[var_name] = LiveVarInfo(
                        var_name=var_name, defined_at=line
                    )
                else:
                    # 更新最后使用位置
                    live_vars[var_name].last_used_at = line

        # 二次遍历：标记活跃性
        for var_name, info in live_vars.items():
            # 如果变量在定义后还有使用，则活跃
            info.is_live_at_exit = info.last_used_at is not None

        self.live_vars = live_vars
        return live_vars

    def get_unused_variables(self) -> List[str]:
        """获取未使用的变量"""
        unused = []
        for var_name, info in self.live_vars.items():
            if info.last_used_at is None:
                unused.append(var_name)
        return unused

    # ==================== 常量传播 ====================

    def propagate_constants(
        self, statements: List[dict]
    ) -> Tuple[List[dict], Dict[str, str]]:
        """常量传播优化

        Args:
            statements: 语句列表

        Returns:
            优化后的语句列表和常量映射
        """
        constants: Dict[str, str] = {}
        optimized = []

        for stmt in statements:
            stmt_type = stmt.get("type", "")

            # 检查常量定义
            if stmt_type == "var_decl":
                var_name = stmt.get("name", "")
                value = stmt.get("value")
                is_const = stmt.get("is_const", False)

                # 如果是常量或有字面量初始化，记录
                if is_const and value is not None:
                    constants[var_name] = str(value)
                    self.symbol_table.set_constant(var_name, str(value))

                optimized.append(stmt)

            # 传播常量到表达式
            elif stmt_type in ("assign", "return", "call"):
                # 替换表达式中的常量
                new_stmt = stmt.copy()
                if "value" in new_stmt:
                    for const_name, const_value in constants.items():
                        # 简化替换
                        if const_name in str(new_stmt["value"]):
                            new_stmt["optimized"] = True
                            new_stmt["constant_value"] = const_value

                optimized.append(new_stmt)

            else:
                optimized.append(stmt)

        self.constants = constants
        return optimized, constants

    def is_constant_foldable(self, expr: str) -> bool:
        """检查表达式是否可折叠为常量"""
        # 简化：检查是否只包含常量
        vars_in_expr = self._extract_vars_from_expr(expr)

        for var_name in vars_in_expr:
            if var_name not in self.constants:
                return False

        return True

    # ==================== 污点分析 ====================

    def define_taint_sources(self, sources: List[str]):
        """定义污点源

        Args:
            sources: 污点源函数/变量列表（如用户输入、文件读取等）
        """
        self.taint_sources = set(sources)

    def analyze_taint_flow(
        self, statements: List[dict], sink_functions: List[str] = None
    ) -> List[DataFlowIssue]:
        """污点分析

        Args:
            statements: 语句列表
            sink_functions: 汇点函数列表（如数据库查询、系统调用等）

        Returns:
            污点问题列表
        """
        if sink_functions is None:
            sink_functions = ["执行", "系统", "查询数据库"]

        issues = []
        tainted_vars: Dict[str, TaintInfo] = {}

        for stmt in statements:
            stmt_type = stmt.get("type", "")
            line = stmt.get("line", 0)

            # 检查污点源
            if stmt_type == "call":
                func_name = stmt.get("function", "")

                # 如果调用污点源函数
                if func_name in self.taint_sources:
                    # 返回值被污染
                    result_var = stmt.get("result", "")
                    if result_var:
                        tainted_vars[result_var] = TaintInfo(
                            var_name=result_var,
                            taint_source=func_name,
                            tainted_lines=[line],
                        )
                        self.symbol_table.set_tainted(result_var, func_name)

                # 如果调用汇点函数，检查参数是否污染
                elif func_name in sink_functions:
                    args = stmt.get("args", [])
                    for arg in args:
                        vars_in_arg = self._extract_vars_from_expr(str(arg))
                        for var_name in vars_in_arg:
                            if var_name in tainted_vars:
                                issues.append(
                                    DataFlowIssue(
                                        issue_type="taint",
                                        message=f"污点数据从 '{tainted_vars[var_name].taint_source}' 流向汇点 '{func_name}'",
                                        var_name=var_name,
                                        line_number=line,
                                        severity="warning",
                                        suggestion="在使用前进行输入验证或清理",
                                    )
                                )

            # 赋值传播污点
            elif stmt_type == "assign":
                target = stmt.get("name", "")
                value = stmt.get("value", "")

                vars_in_value = self._extract_vars_from_expr(str(value))
                for var_name in vars_in_value:
                    if var_name in tainted_vars:
                        # 传播污点
                        if target not in tainted_vars:
                            tainted_vars[target] = TaintInfo(
                                var_name=target,
                                taint_source=tainted_vars[var_name].taint_source,
                                tainted_lines=[line],
                            )
                        else:
                            tainted_vars[target].tainted_lines.append(line)

                        self.symbol_table.set_tainted(
                            target, tainted_vars[var_name].taint_source
                        )

            # 清理污点（简化：调用特定清理函数）
            elif stmt_type == "call":
                func_name = stmt.get("function", "")
                if "清理" in func_name or "sanitize" in func_name.lower():
                    args = stmt.get("args", [])
                    for arg in args:
                        if arg in tainted_vars:
                            tainted_vars[arg].is_sanitized = True

        self.taint_info = tainted_vars
        self.issues.extend(issues)
        return issues

    # ==================== 未初始化变量检测 ====================

    def detect_uninitialized_vars(self, statements: List[dict]) -> List[DataFlowIssue]:
        """检测未初始化变量使用"""
        issues = []
        defined_vars: Set[str] = set()
        initialized_vars: Set[str] = set()

        for stmt in statements:
            stmt_type = stmt.get("type", "")
            line = stmt.get("line", 0)

            # 变量声明（未初始化）
            if stmt_type == "var_decl":
                var_name = stmt.get("name", "")
                defined_vars.add(var_name)

                if stmt.get("value") is not None:
                    initialized_vars.add(var_name)

            # 赋值（初始化）
            elif stmt_type == "assign":
                var_name = stmt.get("name", "")
                initialized_vars.add(var_name)

            # 使用检查
            elif stmt_type in ("read", "call", "return"):
                used_vars = self._extract_used_vars(stmt)
                for var_name in used_vars:
                    if var_name in defined_vars and var_name not in initialized_vars:
                        issues.append(
                            DataFlowIssue(
                                issue_type="uninitialized",
                                message=f"变量 '{var_name}' 未初始化就被使用",
                                var_name=var_name,
                                line_number=line,
                                severity="error",
                                suggestion="在使用前初始化变量",
                            )
                        )

        return issues

    # ==================== 报告生成 ====================

    def generate_report(self) -> str:
        """生成数据流分析报告"""
        lines = [
            "=" * 70,
            "数据流分析报告",
            "=" * 70,
            "",
        ]

        # 定义-使用链统计
        lines.append("定义-使用链统计：")
        lines.append("-" * 70)
        for var_name, chain in self.def_use_chains.items():
            def_count = len(chain.definitions)
            use_count = len(chain.uses)
            lines.append(f"  {var_name}: 定义{def_count}次, 使用{use_count}次")
        lines.append("")

        # 活跃变量
        lines.append("活跃变量分析：")
        lines.append("-" * 70)
        unused = self.get_unused_variables()
        if unused:
            lines.append(f"  未使用变量: {', '.join(unused)}")
        else:
            lines.append("  所有变量均被使用")
        lines.append("")

        # 常量传播
        if self.constants:
            lines.append("常量传播：")
            lines.append("-" * 70)
            for var_name, value in self.constants.items():
                lines.append(f"  {var_name} = {value}")
            lines.append("")

        # 污点分析
        if self.taint_info:
            lines.append("污点分析：")
            lines.append("-" * 70)
            for var_name, info in self.taint_info.items():
                status = "已清理" if info.is_sanitized else "未清理"
                lines.append(f"  {var_name}: 污点源={info.taint_source}, 状态={status}")
            lines.append("")

        # 问题列表
        if self.issues:
            lines.append("数据流问题：")
            lines.append("-" * 70)
            for issue in self.issues:
                icon = "❌" if issue.severity == "error" else "⚠️"
                lines.append(f"  {icon} 行{issue.line_number}: {issue.message}")
            lines.append("")

        lines.append("=" * 70)

        return "\n".join(lines)

    def analyze_function(
        self, func_name: str, statements: List[dict], params: List[str] = None
    ) -> dict:
        """完整的函数数据流分析

        Args:
            func_name: 函数名
            statements: 语句列表
            params: 参数列表

        Returns:
            分析结果字典
        """
        result = {
            "function": func_name,
            "def_use_chains": {},
            "live_variables": {},
            "constants": {},
            "taint_issues": [],
            "uninitialized_issues": [],
            "unused_vars": [],
        }

        # 1. 构建定义-使用链
        result["def_use_chains"] = self.build_def_use_chains(statements)

        # 2. 活跃变量分析
        result["live_variables"] = self.analyze_live_variables(statements, params)
        result["unused_vars"] = self.get_unused_variables()

        # 3. 常量传播
        _, result["constants"] = self.propagate_constants(statements)

        # 4. 未初始化变量检测
        result["uninitialized_issues"] = self.detect_uninitialized_vars(statements)

        # 5. 污点分析（自动使用默认污点源或用户定义的污点源）
        if not self.taint_sources:
            # 默认污点源：用户输入相关函数
            self.taint_sources = {
                "读取输入",
                "接收数据",
                "zhc_read_int",
                "zhc_read_float",
                "zhc_read_char",
                "zhc_read_string",
            }
        result["taint_issues"] = self.analyze_taint_flow(statements)

        return result


# 测试代码
if __name__ == "__main__":
    print("=== 数据流分析器测试 ===\n")

    analyzer = DataFlowAnalyzer()

    # 定义污点源
    analyzer.define_taint_sources(["读取输入", "接收数据"])

    # 测试语句
    test_statements = [
        {"type": "var_decl", "name": "x", "value": 10, "line": 1},
        {"type": "var_decl", "name": "y", "line": 2},  # 未初始化
        {"type": "assign", "name": "y", "value": "x + 5", "line": 3},
        {"type": "var_decl", "name": "input", "line": 4},
        {"type": "call", "function": "读取输入", "result": "input", "line": 5},
        {"type": "call", "function": "执行", "args": ["input"], "line": 6},  # 污点流
        {"type": "return", "value": "y", "line": 7},
    ]

    # 完整分析
    result = analyzer.analyze_function("test_func", test_statements, params=["x"])

    print(f"函数: {result['function']}")
    print(f"定义-使用链: {len(result['def_use_chains'])}个变量")
    print(f"未使用变量: {result['unused_vars']}")
    print(f"常量: {result['constants']}")
    print(f"未初始化问题: {len(result['uninitialized_issues'])}个")
    print(f"污点问题: {len(result['taint_issues'])}个")
    print()

    print(analyzer.generate_report())

    print("\n=== 测试完成 ===")

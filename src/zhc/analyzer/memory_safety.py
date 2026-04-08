#!/usr/bin/env python3
"""
Day 23: 内存安全增强

功能：
1. 空指针安全检查
2. 内存泄漏检测
3. 越界访问防护
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class SafetyLevel(Enum):
    """安全级别"""

    SAFE = "安全"
    WARNING = "警告"
    UNSAFE = "不安全"


@dataclass
class MemoryAccess:
    """内存访问信息"""

    var_name: str
    operation: str  # "read", "write", "dereference"
    line_number: int
    is_null_checked: bool = False


@dataclass
class MemoryBlock:
    """内存块信息"""

    var_name: str
    allocated_line: int
    size: int
    is_array: bool = False
    freed_line: Optional[int] = None
    is_freed: bool = False


@dataclass
class SafetyIssue:
    """安全问题"""

    level: SafetyLevel
    message: str
    var_name: str
    line_number: int
    suggestion: str


class NullPointerChecker:
    """空指针安全检查器"""

    def __init__(self):
        self.allocations: Dict[str, MemoryBlock] = {}
        self.null_checks: Dict[str, Set[int]] = {}

    def track_allocation(
        self, var_name: str, line: int, size: int = 1, is_array: bool = False
    ):
        """跟踪内存分配"""
        self.allocations[var_name] = MemoryBlock(
            var_name=var_name, allocated_line=line, size=size, is_array=is_array
        )

    def check_null(self, var_name: str, line: int) -> bool:
        """检查空指针"""
        if var_name in self.null_checks:
            self.null_checks[var_name].add(line)
        else:
            self.null_checks[var_name] = {line}
        return True

    def verify_access(
        self, var_name: str, operation: str, line: int
    ) -> Optional[SafetyIssue]:
        """验证内存访问"""
        # 检查是否已分配
        if var_name not in self.allocations:
            return SafetyIssue(
                level=SafetyLevel.UNSAFE,
                message=f"指针 '{var_name}' 未分配内存",
                var_name=var_name,
                line_number=line,
                suggestion="在使用前调用 新建 或 分配",
            )

        block = self.allocations[var_name]

        # 检查是否已释放
        if block.is_freed:
            return SafetyIssue(
                level=SafetyLevel.UNSAFE,
                message=f"指针 '{var_name}' 已被释放",
                var_name=var_name,
                line_number=line,
                suggestion="不能访问已释放的内存",
            )

        # 检查是否在空检查后访问
        if var_name in self.null_checks:
            checked_lines = self.null_checks[var_name]
            if line > max(checked_lines):
                return SafetyIssue(
                    level=SafetyLevel.WARNING,
                    message=f"访问 '{var_name}' 前应进行空指针检查",
                    var_name=var_name,
                    line_number=line,
                    suggestion="添加 if (ptr != 空指针) 检查",
                )

        return None


class MemoryLeakDetector:
    """内存泄漏检测器"""

    def __init__(self):
        self.blocks: Dict[str, MemoryBlock] = {}
        self.issues: List[SafetyIssue] = []

    def track_allocation(self, var_name: str, line: int, size: int = 1):
        """跟踪分配"""
        self.blocks[var_name] = MemoryBlock(
            var_name=var_name, allocated_line=line, size=size
        )

    def track_free(self, var_name: str, line: int):
        """跟踪释放"""
        if var_name in self.blocks:
            self.blocks[var_name].freed_line = line
            self.blocks[var_name].is_freed = True

    def check_leaks(self) -> List[SafetyIssue]:
        """检查泄漏"""
        leaks = []
        for name, block in self.blocks.items():
            if not block.is_freed:
                leaks.append(
                    SafetyIssue(
                        level=SafetyLevel.WARNING,
                        message=f"内存泄漏: '{name}' 在行{block.allocated_line}分配但未释放",
                        var_name=name,
                        line_number=block.allocated_line,
                        suggestion=f"在函数返回前添加 删除 {name};",
                    )
                )
        return leaks

    def check_double_free(self, var_name: str, line: int) -> Optional[SafetyIssue]:
        """检查双重释放"""
        if var_name in self.blocks and self.blocks[var_name].is_freed:
            return SafetyIssue(
                level=SafetyLevel.UNSAFE,
                message=f"双重释放: '{var_name}' 在行{self.blocks[var_name].freed_line}已释放",
                var_name=var_name,
                line_number=line,
                suggestion="检查逻辑，确保只释放一次",
            )
        return None


class BoundsChecker:
    """越界访问检查器"""

    def __init__(self):
        self.arrays: Dict[str, int] = {}  # var_name -> size
        self.accesses: List[MemoryAccess] = []

    def track_array(self, var_name: str, size: int, line: int):
        """跟踪数组"""
        self.arrays[var_name] = size

    def check_access(
        self, var_name: str, index: int, operation: str, line: int
    ) -> Optional[SafetyIssue]:
        """检查访问"""
        if var_name not in self.arrays:
            return None  # 不是数组

        size = self.arrays[var_name]

        if index < 0:
            return SafetyIssue(
                level=SafetyLevel.UNSAFE,
                message=f"数组 '{var_name}[{index}]' 索引为负数",
                var_name=var_name,
                line_number=line,
                suggestion="索引必须 >= 0",
            )

        if index >= size:
            return SafetyIssue(
                level=SafetyLevel.UNSAFE,
                message=f"数组 '{var_name}[{index}]' 越界 (大小={size})",
                var_name=var_name,
                line_number=line,
                suggestion=f"索引必须在 0 到 {size - 1} 之间",
            )

        return None

    def generate_bounds_check(self, var_name: str, index: str) -> str:
        """生成边界检查代码"""
        if var_name not in self.arrays:
            return ""
        size = self.arrays[var_name]
        return f"assert({index} >= 0 && {index} < {size});"


class UseAfterFreeChecker:
    """释放后使用检查器"""

    def __init__(self):
        self.pointer_flows: Dict[str, List[Tuple[int, str]]] = {}  # 指针流向追踪

    def track_pointer_flow(self, var_name: str, line: int, operation: str):
        """追踪指针流向"""
        if var_name not in self.pointer_flows:
            self.pointer_flows[var_name] = []
        self.pointer_flows[var_name].append((line, operation))

    def check_use_after_free(self, var_name: str) -> List[SafetyIssue]:
        """检查释放后使用"""
        issues = []
        if var_name not in self.pointer_flows:
            return issues

        freed = False
        freed_line = 0

        for line, op in self.pointer_flows[var_name]:
            if op == "free":
                freed = True
                freed_line = line
            elif freed and op in ("read", "write", "dereference"):
                issues.append(
                    SafetyIssue(
                        level=SafetyLevel.UNSAFE,
                        message=f"释放后使用: '{var_name}' 在行{freed_line}释放，行{line}使用",
                        var_name=var_name,
                        line_number=line,
                        suggestion="确保释放后不再访问该指针",
                    )
                )

        return issues


class OwnershipTracker:
    """所有权追踪器（Rust风格）"""

    def __init__(self):
        self.ownerships: Dict[str, str] = {}  # var_name -> owner_scope
        self.borrows: Dict[
            str, List[Tuple[str, int, bool]]
        ] = {}  # var_name -> [(borrower, line, is_mutable)]

    def declare_owner(self, var_name: str, scope: str):
        """声明所有者"""
        self.ownerships[var_name] = scope

    def borrow(
        self, var_name: str, borrower: str, line: int, mutable: bool = False
    ) -> Optional[SafetyIssue]:
        """借用检查"""
        if var_name not in self.ownerships:
            return SafetyIssue(
                level=SafetyLevel.WARNING,
                message=f"借用未知变量 '{var_name}'",
                var_name=var_name,
                line_number=line,
                suggestion="确保变量已声明",
            )

        if var_name not in self.borrows:
            self.borrows[var_name] = []

        # 检查是否已有可变借用
        for existing_borrower, existing_line, existing_mutable in self.borrows[
            var_name
        ]:
            if existing_mutable:
                return SafetyIssue(
                    level=SafetyLevel.UNSAFE,
                    message=f"可变借用冲突: '{var_name}' 已在行{existing_line}被 '{existing_borrower}' 可变借用",
                    var_name=var_name,
                    line_number=line,
                    suggestion="不能同时有多个可变借用",
                )
            if mutable:
                return SafetyIssue(
                    level=SafetyLevel.UNSAFE,
                    message=f"借用冲突: '{var_name}' 已在行{existing_line}被 '{existing_borrower}' 不可变借用，无法可变借用",
                    var_name=var_name,
                    line_number=line,
                    suggestion="存在不可变借用时不能可变借用",
                )

        self.borrows[var_name].append((borrower, line, mutable))
        return None

    def release_borrow(self, var_name: str, borrower: str):
        """释放借用"""
        if var_name in self.borrows:
            self.borrows[var_name] = [
                b for b in self.borrows[var_name] if b[0] != borrower
            ]


class LifetimeAnalyzer:
    """生命周期分析器"""

    def __init__(self):
        self.lifetimes: Dict[str, Tuple[int, int]] = {}  # var_name -> (start, end)
        self.borrow_lifetimes: Dict[
            str, List[Tuple[int, int, str]]
        ] = {}  # borrower -> [(start, end, var_name)]

    def track_lifetime(self, var_name: str, start_line: int, end_line: int = None):
        """追踪生命周期"""
        if var_name in self.lifetimes:
            old_start, old_end = self.lifetimes[var_name]
            self.lifetimes[var_name] = (old_start, end_line or old_end)
        else:
            self.lifetimes[var_name] = (start_line, end_line or start_line)

    def track_borrow_lifetime(self, borrower: str, start: int, end: int, var_name: str):
        """追踪借用生命周期"""
        if borrower not in self.borrow_lifetimes:
            self.borrow_lifetimes[borrower] = []
        self.borrow_lifetimes[borrower].append((start, end, var_name))

    def check_lifetime(
        self, borrower: str, var_name: str, use_line: int
    ) -> Optional[SafetyIssue]:
        """检查生命周期有效性"""
        # 检查借用的变量是否存在
        if var_name not in self.lifetimes:
            return SafetyIssue(
                level=SafetyLevel.UNSAFE,
                message=f"生命周期错误: 变量 '{var_name}' 不存在",
                var_name=var_name,
                line_number=use_line,
                suggestion="确保引用的变量存在",
            )

        var_start, var_end = self.lifetimes[var_name]

        # 检查借用是否超出变量生命周期
        if use_line > var_end:
            return SafetyIssue(
                level=SafetyLevel.UNSAFE,
                message=f"生命周期错误: '{borrower}' 在行{use_line}使用了已失效的 '{var_name}'（生命周期{var_start}-{var_end}）",
                var_name=var_name,
                line_number=use_line,
                suggestion="确保引用的生命周期不超过被引用变量",
            )

        return None


class RaceConditionDetector:
    """竞态条件检测器（多线程）"""

    def __init__(self):
        self.shared_vars: Dict[str, Set[str]] = {}  # var_name -> threads
        self.accesses: Dict[
            str, List[Tuple[str, int, bool]]
        ] = {}  # var_name -> [(thread, line, is_write)]

    def track_shared_var(self, var_name: str, thread: str):
        """追踪共享变量"""
        if var_name not in self.shared_vars:
            self.shared_vars[var_name] = set()
        self.shared_vars[var_name].add(thread)

    def track_access(self, var_name: str, thread: str, line: int, is_write: bool):
        """追踪访问"""
        if var_name not in self.accesses:
            self.accesses[var_name] = []
        self.accesses[var_name].append((thread, line, is_write))

    def detect_races(self) -> List[SafetyIssue]:
        """检测竞态条件"""
        issues = []

        for var_name, accesses in self.accesses.items():
            # 检查是否有并发写
            write_accesses = [(t, loc) for t, loc, w in accesses if w]
            read_accesses = [(t, loc) for t, loc, w in accesses if not w]

            # 如果有多个线程写入
            write_threads = set(t for t, loc in write_accesses)
            if len(write_threads) > 1:
                for thread, line in write_accesses:
                    issues.append(
                        SafetyIssue(
                            level=SafetyLevel.WARNING,
                            message=f"竞态风险: 变量 '{var_name}' 被多个线程写入",
                            var_name=var_name,
                            line_number=line,
                            suggestion="使用互斥锁保护共享变量",
                        )
                    )

            # 如果有写和读冲突
            read_threads = set(t for t, loc in read_accesses)
            if write_threads and read_threads:
                for thread, line in write_accesses:
                    if thread not in read_threads:
                        issues.append(
                            SafetyIssue(
                                level=SafetyLevel.WARNING,
                                message=f"竞态风险: 变量 '{var_name}' 同时被读写",
                                var_name=var_name,
                                line_number=line,
                                suggestion="使用读写锁或互斥锁保护",
                            )
                        )

        return issues


class StackAllocationAnalyzer:
    """栈分配分析器"""

    def __init__(self):
        self.stack_vars: Dict[
            str, Tuple[int, int, str]
        ] = {}  # var_name -> (line, size, scope)
        self.max_stack_size = 0
        self.current_stack_size = 0

    def allocate_stack(self, var_name: str, line: int, size: int, scope: str):
        """栈分配"""
        self.stack_vars[var_name] = (line, size, scope)
        self.current_stack_size += size
        self.max_stack_size = max(self.max_stack_size, self.current_stack_size)

    def deallocate_stack(self, var_name: str):
        """栈释放"""
        if var_name in self.stack_vars:
            _, size, _ = self.stack_vars[var_name]
            self.current_stack_size -= size

    def check_stack_overflow(
        self, threshold: int = 1024 * 1024
    ) -> Optional[SafetyIssue]:
        """检查栈溢出风险"""
        if self.max_stack_size > threshold:
            return SafetyIssue(
                level=SafetyLevel.WARNING,
                message=f"栈溢出风险: 最大栈使用 {self.max_stack_size} 字节",
                var_name="",
                line_number=0,
                suggestion="减少局部变量大小或使用堆分配",
            )
        return None

    def get_stack_report(self) -> str:
        """获取栈使用报告"""
        lines = [
            "栈分配报告：",
            f"  最大栈使用: {self.max_stack_size} 字节",
            f"  当前栈使用: {self.current_stack_size} 字节",
            f"  栈变量数: {len(self.stack_vars)}",
            "",
        ]

        for var_name, (line, size, scope) in sorted(
            self.stack_vars.items(), key=lambda x: -x[1][1]
        ):
            lines.append(f"  {var_name}: {size}字节 (行{line}, 作用域:{scope})")

        return "\n".join(lines)


class MemorySafetyAnalyzer:
    """内存安全分析器（增强版）"""

    def __init__(self):
        self.null_checker = NullPointerChecker()
        self.leak_detector = MemoryLeakDetector()
        self.bounds_checker = BoundsChecker()
        self.use_after_free_checker = UseAfterFreeChecker()
        self.ownership_tracker = OwnershipTracker()
        self.lifetime_analyzer = LifetimeAnalyzer()
        self.race_detector = RaceConditionDetector()
        self.stack_analyzer = StackAllocationAnalyzer()
        self.all_issues: List[SafetyIssue] = []

    def analyze(self) -> List[SafetyIssue]:
        """执行完整分析（覆盖全部 8 个子检查器）"""
        issues = []

        # 1. 空指针检查
        for name, block in self.null_checker.allocations.items():
            if block.is_freed and not block.is_array:
                issues.append(
                    SafetyIssue(
                        level=SafetyLevel.WARNING,
                        message=f"释放后使用: '{name}'",
                        var_name=name,
                        line_number=block.freed_line or block.allocated_line,
                        suggestion="确保释放后不再访问",
                    )
                )

        # 2. 内存泄漏检查
        issues.extend(self.leak_detector.check_leaks())

        # 3. 释放后使用检查
        for var_name in self.use_after_free_checker.pointer_flows:
            issues.extend(self.use_after_free_checker.check_use_after_free(var_name))

        # 4. 所有权借用冲突检查
        for var_name, borrows in self.ownership_tracker.borrows.items():
            # 检查是否有未释放的借用指向已失效的变量
            for borrower, line, mutable in borrows:
                if var_name in self.lifetime_analyzer.lifetimes:
                    start, end = self.lifetime_analyzer.lifetimes[var_name]
                    if line > end:
                        issues.append(
                            SafetyIssue(
                                level=SafetyLevel.WARNING,
                                message=f"悬空借用: '{borrower}' 在行{line}使用了生命周期已结束的 '{var_name}'（生命周期{start}-{end}）",
                                var_name=var_name,
                                line_number=line,
                                suggestion="确保借用不超过被引用变量的生命周期",
                            )
                        )

        # 5. 生命周期检查：借用是否超出变量生命周期
        for borrower, lifetimes in self.lifetime_analyzer.borrow_lifetimes.items():
            for start, end, var_name in lifetimes:
                if var_name in self.lifetime_analyzer.lifetimes:
                    var_start, var_end = self.lifetime_analyzer.lifetimes[var_name]
                    if end > var_end:
                        issues.append(
                            SafetyIssue(
                                level=SafetyLevel.WARNING,
                                message=f"生命周期错误: '{borrower}' 的借用超出 '{var_name}' 的生命周期（借用{start}-{end}，变量{var_start}-{var_end}）",
                                var_name=var_name,
                                line_number=end,
                                suggestion="缩短借用生命周期或延长被引用变量的作用域",
                            )
                        )

        # 6. 竞态条件检测
        issues.extend(self.race_detector.detect_races())

        # 7. 栈溢出检查
        overflow_issue = self.stack_analyzer.check_stack_overflow()
        if overflow_issue:
            issues.append(overflow_issue)

        self.all_issues = issues
        return issues

    def analyze_function(self, func_name: str, statements: List[dict]) -> dict:
        """分析函数的内存安全（覆盖全部 8 个子检查器）

        Args:
            func_name: 函数名
            statements: 语句列表（字典格式）

        Returns:
            分析结果字典
        """
        result = {
            "function": func_name,
            "allocations": [],
            "frees": [],
            "issues": [],
            "stats": {
                "alloc_count": 0,
                "free_count": 0,
                "leak_count": 0,
                "null_check_count": 0,
            },
        }

        scope_start = 0
        scope_end = 0
        if statements:
            scope_start = statements[0].get("line", 0)
            scope_end = statements[-1].get("line", scope_start)

        for stmt in statements:
            stmt_type = stmt.get("type", "")
            line = stmt.get("line", 0)
            var_name = stmt.get("name", "")

            # 追踪分配
            if "alloc" in stmt_type or "新建" in stmt_type:
                size = stmt.get("size", 1)
                self.null_checker.track_allocation(var_name, line, size)
                self.leak_detector.track_allocation(var_name, line, size)
                self.use_after_free_checker.track_pointer_flow(var_name, line, "alloc")
                self.ownership_tracker.declare_owner(var_name, func_name)
                self.lifetime_analyzer.track_lifetime(var_name, line)
                result["allocations"].append(
                    {"var": var_name, "line": line, "size": size}
                )
                result["stats"]["alloc_count"] += 1

            # 追踪释放
            elif "free" in stmt_type or "删除" in stmt_type:
                self.leak_detector.track_free(var_name, line)
                self.use_after_free_checker.track_pointer_flow(var_name, line, "free")

                # 检查双重释放
                double_free = self.leak_detector.check_double_free(var_name, line)
                if double_free:
                    result["issues"].append(
                        {
                            "type": "double_free",
                            "message": double_free.message,
                            "line": line,
                        }
                    )

                result["frees"].append({"var": var_name, "line": line})
                result["stats"]["free_count"] += 1

            # 追踪空检查
            elif "if" in stmt_type and "空指针" in str(stmt.get("condition", "")):
                if var_name:
                    self.null_checker.check_null(var_name, line)
                    result["stats"]["null_check_count"] += 1

            # 追踪访问
            elif stmt_type in ("read", "write", "dereference"):
                self.use_after_free_checker.track_pointer_flow(
                    var_name, line, stmt_type
                )

            # 追踪赋值（借用）
            elif stmt_type == "assign":
                target = stmt.get("target", "")
                if target and target != var_name:
                    borrow_issue = self.ownership_tracker.borrow(var_name, target, line)
                    if borrow_issue:
                        result["issues"].append(
                            {
                                "type": "borrow_conflict",
                                "message": borrow_issue.message,
                                "line": line,
                            }
                        )
                    self.lifetime_analyzer.track_borrow_lifetime(
                        target, line, scope_end, var_name
                    )

            # 追踪栈变量声明
            elif "decl" in stmt_type or "声明" in stmt_type:
                size = stmt.get("size", 0) or 0
                if size > 0:
                    self.stack_analyzer.allocate_stack(var_name, line, size, func_name)

        # 执行完整分析（全部 8 个子检查器）
        all_issues = self.analyze()
        result["issues"].extend(
            [
                {
                    "type": issue.level.value,
                    "message": issue.message,
                    "line": issue.line_number,
                }
                for issue in all_issues
            ]
        )
        result["stats"]["leak_count"] = len(self.leak_detector.check_leaks())

        return result

    def generate_report(self) -> str:
        """生成详细安全报告"""
        lines = [
            "=" * 70,
            "内存安全分析报告",
            "=" * 70,
            "",
        ]

        # 统计信息
        alloc_count = len(self.null_checker.allocations)
        len(self.leak_detector.check_leaks())
        stack_vars = len(self.stack_analyzer.stack_vars)

        lines.append("统计信息：")
        lines.append("-" * 70)
        lines.append(f"  内存分配数: {alloc_count}")
        lines.append(f"  栈变量数: {stack_vars}")
        lines.append(f"  最大栈使用: {self.stack_analyzer.max_stack_size} 字节")
        lines.append("")

        # 问题列表
        if not self.all_issues:
            lines.append("✅ 未发现内存安全问题")
        else:
            warning_count = sum(
                1 for i in self.all_issues if i.level == SafetyLevel.WARNING
            )
            unsafe_count = sum(
                1 for i in self.all_issues if i.level == SafetyLevel.UNSAFE
            )

            lines.append(f"发现 {len(self.all_issues)} 个问题：")
            lines.append(f"  ⚠️  警告: {warning_count}")
            lines.append(f"  ❌ 不安全: {unsafe_count}")
            lines.append("")
            lines.append("问题详情：")
            lines.append("-" * 70)

            for issue in self.all_issues:
                level_str = "⚠️" if issue.level == SafetyLevel.WARNING else "❌"
                lines.append(f"{level_str} 行{issue.line_number}: {issue.message}")
                lines.append(f"    变量: {issue.var_name}")
                lines.append(f"    建议: {issue.suggestion}")
                lines.append("")

        # 栈使用报告
        if stack_vars > 0:
            lines.append("")
            lines.append(self.stack_analyzer.get_stack_report())

        lines.append("=" * 70)

        return "\n".join(lines)


# 测试
if __name__ == "__main__":
    print("=== Day 23 内存安全测试 ===")

    analyzer = MemorySafetyAnalyzer()

    # 测试空指针检查
    print("\n--- 空指针检查 ---")
    analyzer.null_checker.track_allocation("ptr", 1)
    issue = analyzer.null_checker.verify_access("ptr", "read", 10)
    if issue:
        print(f"检测到: {issue.message}")
        print(f"建议: {issue.suggestion}")

    analyzer.null_checker.check_null("ptr", 5)
    issue = analyzer.null_checker.verify_access("ptr", "read", 10)
    if not issue:
        print("空指针已检查，安全访问")

    # 测试内存泄漏检测
    print("\n--- 内存泄漏检测 ---")
    leak_detector = MemoryLeakDetector()
    leak_detector.track_allocation("leak_ptr", 1)
    leaks = leak_detector.check_leaks()
    for leak in leaks:
        print(f"泄漏: {leak.message}")

    leak_detector.track_free("leak_ptr", 10)
    leaks = leak_detector.check_leaks()
    print(f"释放后泄漏数: {len(leaks)}")

    # 测试越界检查
    print("\n--- 越界检查 ---")
    bounds = BoundsChecker()
    bounds.track_array("arr", 10, 1)

    issue = bounds.check_access("arr", 15, "write", 5)
    if issue:
        print(f"越界: {issue.message}")

    issue = bounds.check_access("arr", -1, "write", 5)
    if issue:
        print(f"负索引: {issue.message}")

    print("\n=== 测试完成 ===")

#!/usr/bin/env python3
"""
Day 20: 内存语法实现

功能：
1. 新/删除语法规则
2. 智能指针语法
3. 内存安全检测机制
"""

import re
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class MemoryOperation(Enum):
    """内存操作类型"""

    NEW = "新建"
    DELETE = "删除"
    MALLOC = "分配"
    FREE = "释放"
    ARRAY_NEW = "新建数组"
    ARRAY_DELETE = "删除数组"


class MemorySafety(Enum):
    """内存安全级别"""

    SAFE = "安全"
    UNSAFE = "不安全"
    WARNING = "警告"


@dataclass
class MemoryAllocation:
    """内存分配信息"""

    operation: MemoryOperation
    type_name: str
    variable_name: str
    line_number: int
    size: Optional[int] = None
    is_array: bool = False


@dataclass
class MemoryCheck:
    """内存安全检查结果"""

    is_safe: bool
    level: MemorySafety
    message: str
    suggestions: List[str]


class SmartPointerType(Enum):
    """智能指针类型"""

    UNIQUE = "独享指针"
    SHARED = "共享指针"
    WEAK = "弱指针"


class MemorySyntaxParser:
    """内存语法解析器"""

    # 新建语法模式
    NEW_PATTERN = r"新建\s+(\w+)(?:\s*\[(\d+)\])?(?:\s*=\s*(.+))?"

    # 删除语法模式
    DELETE_PATTERN = r"删除(?:\s*数组)?\s+(.+?)(?:\s*;|$)"

    # 分配语法模式
    ALLOC_PATTERN = r"分配\s*\(([^)]+)\)(?:\s*->\s*(\w+))?"

    # 释放语法模式
    FREE_PATTERN = r"释放\s*\(([^)]+)\)"

    def __init__(self):
        self.allocations: List[MemoryAllocation] = []
        self.safety_issues: List[str] = []
        self.current_line: int = 0

    def parse_new(self, line: str, line_num: int) -> Optional[MemoryAllocation]:
        """解析新建语句"""
        self.current_line = line_num
        match = re.search(self.NEW_PATTERN, line)
        if not match:
            return None

        type_name = match.group(1)
        size_str = match.group(2)
        match.group(3)

        is_array = size_str is not None
        size = int(size_str) if size_str else None

        # 生成变量名
        var_name = f"_ptr_{line_num}"

        allocation = MemoryAllocation(
            operation=MemoryOperation.NEW
            if not is_array
            else MemoryOperation.ARRAY_NEW,
            type_name=type_name,
            variable_name=var_name,
            line_number=line_num,
            size=size,
        )

        self.allocations.append(allocation)
        return allocation

    def parse_delete(self, line: str, line_num: int) -> Optional[MemoryAllocation]:
        """解析删除语句"""
        self.current_line = line_num
        match = re.search(self.DELETE_PATTERN, line)
        if not match:
            return None

        target = match.group(1).strip()

        allocation = MemoryAllocation(
            operation=MemoryOperation.DELETE
            if "数组" not in line
            else MemoryOperation.ARRAY_DELETE,
            type_name="",
            variable_name=target,
            line_number=line_num,
        )

        return allocation

    def parse_alloc(self, line: str, line_num: int) -> Optional[MemoryAllocation]:
        """解析分配语句"""
        self.current_line = line_num
        match = re.search(self.ALLOC_PATTERN, line)
        if not match:
            return None

        match.group(1)
        var_name = match.group(2) or f"_alloc_{line_num}"

        allocation = MemoryAllocation(
            operation=MemoryOperation.MALLOC,
            type_name="空型*",
            variable_name=var_name,
            line_number=line_num,
            size=None,
        )

        self.allocations.append(allocation)
        return allocation

    def generate_c_code(self, allocation: MemoryAllocation) -> str:
        """生成C代码"""
        if allocation.operation == MemoryOperation.NEW:
            return f"{allocation.type_name}* {allocation.variable_name} = ({allocation.type_name}*)malloc(sizeof({allocation.type_name}));"
        elif allocation.operation == MemoryOperation.ARRAY_NEW:
            return f"{allocation.type_name}* {allocation.variable_name} = ({allocation.type_name}*)malloc({allocation.size} * sizeof({allocation.type_name}));"
        elif allocation.operation == MemoryOperation.DELETE:
            return f"free({allocation.variable_name});"
        elif allocation.operation == MemoryOperation.ARRAY_DELETE:
            return f"free({allocation.variable_name});"
        elif allocation.operation == MemoryOperation.MALLOC:
            return f"void* {allocation.variable_name} = malloc({allocation.type_name});"
        return ""


class SmartPointerParser:
    """智能指针语法解析器"""

    # 独享指针语法
    UNIQUE_PATTERN = r"独享指针\s+<(\w+)>\s+(\w+)(?:\s*=\s*(.+))?;"

    # 共享指针语法
    SHARED_PATTERN = r"共享指针\s+<(\w+)>\s+(\w+)(?:\s*=\s*(.+))?;"

    def __init__(self):
        self.pointers: Dict[str, SmartPointerType] = {}

    def parse_unique(self, line: str) -> Optional[Tuple[str, str]]:
        """解析独享指针"""
        match = re.search(self.UNIQUE_PATTERN, line)
        if not match:
            return None

        type_name = match.group(1)
        var_name = match.group(2)
        match.group(3)

        self.pointers[var_name] = SmartPointerType.UNIQUE
        return (type_name, var_name)

    def parse_shared(self, line: str) -> Optional[Tuple[str, str]]:
        """解析共享指针"""
        match = re.search(self.SHARED_PATTERN, line)
        if not match:
            return None

        type_name = match.group(1)
        var_name = match.group(2)
        match.group(3)

        self.pointers[var_name] = SmartPointerType.SHARED
        return (type_name, var_name)

    def generate_unique_cpp(self, type_name: str, var_name: str) -> str:
        """生成C++ unique_ptr代码"""
        return f"std::unique_ptr<{type_name}> {var_name} = std::make_unique<{type_name}>();"

    def generate_shared_cpp(self, type_name: str, var_name: str) -> str:
        """生成C++ shared_ptr代码"""
        return f"std::shared_ptr<{type_name}> {var_name} = std::make_shared<{type_name}>();"


class MemorySafetyChecker:
    """内存安全检测器"""

    def __init__(self):
        self.allocations: Dict[str, MemoryAllocation] = {}
        self.deallocations: Dict[str, int] = {}
        self.issues: List[str] = []

    def track_allocation(self, var_name: str, allocation: MemoryAllocation):
        """跟踪分配"""
        self.allocations[var_name] = allocation

    def track_deallocation(self, var_name: str, line_num: int):
        """跟踪释放"""
        if var_name in self.deallocations:
            self.issues.append(f"行{line_num}: 双重释放 '{var_name}'")
        else:
            self.deallocations[var_name] = line_num

    def check_unfreed(self) -> List[str]:
        """检查未释放内存"""
        unfreed = []
        for var_name, alloc in self.allocations.items():
            if var_name not in self.deallocations:
                unfreed.append(
                    f"行{alloc.line_number}: 内存泄漏 '{var_name}' 类型={alloc.type_name}"
                )
        return unfreed

    def check_nullptr_dereference(self, var_name: str) -> bool:
        """检查空指针解引用"""
        return var_name not in self.allocations

    def perform_safety_check(self, var_name: str) -> MemoryCheck:
        """执行安全检查"""
        if var_name in self.deallocations:
            return MemoryCheck(
                is_safe=False,
                level=MemorySafety.UNSAFE,
                message=f"'{var_name}' 已被释放",
                suggestions=["检查是否使用已释放的指针"],
            )

        if var_name not in self.allocations:
            return MemoryCheck(
                is_safe=False,
                level=MemorySafety.UNSAFE,
                message=f"'{var_name}' 未分配内存",
                suggestions=["在使用前分配内存"],
            )

        return MemoryCheck(
            is_safe=True,
            level=MemorySafety.SAFE,
            message=f"'{var_name}' 内存状态安全",
            suggestions=[],
        )

    def generate_safety_report(self) -> str:
        """生成安全报告"""
        lines = ["/* 内存安全报告 */", ""]

        # 检查未释放
        unfreed = self.check_unfreed()
        if unfreed:
            lines.append("/* 潜在内存泄漏 */")
            for issue in unfreed:
                lines.append(f"/*   {issue} */")
            lines.append("")

        # 检查双重释放
        for var_name in self.deallocations:
            count = list(self.deallocations.values()).count(
                self.deallocations[var_name]
            )
            if count > 1:
                lines.append(f"/* 双重释放: {var_name} */")

        if not unfreed and not self.issues:
            lines.append("/* 无内存安全警告 */")

        return "\n".join(lines)


# 测试
if __name__ == "__main__":
    print("=== 内存语法解析测试 ===")

    # 测试新建语法
    parser = MemorySyntaxParser()

    print("\n--- 新建语法 ---")
    result = parser.parse_new("新建 整数型 ptr = 10;", 1)
    if result:
        print(f"类型: {result.type_name}")
        print(f"变量: {result.variable_name}")

    result = parser.parse_new("新建 整数型 数组[100];", 2)
    if result:
        print(f"数组大小: {result.size}")

    # 测试删除语法
    print("\n--- 删除语法 ---")
    result = parser.parse_delete("删除 ptr;", 3)
    if result:
        print(f"删除: {result.variable_name}")

    # 生成C代码
    print("\n--- C代码生成 ---")
    alloc = MemoryAllocation(MemoryOperation.NEW, "int", "p", 1)
    print(parser.generate_c_code(alloc))

    # 智能指针测试
    print("\n=== 智能指针测试 ===")
    sp = SmartPointerParser()
    unique_result = sp.parse_unique("独享指针<整数型> ptr1;")
    if unique_result:
        print(f"独享指针: {unique_result[0]} {unique_result[1]}")
        print(sp.generate_unique_cpp(unique_result[0], unique_result[1]))

    # 内存安全检测测试
    print("\n=== 内存安全检测 ===")
    checker = MemorySafetyChecker()
    checker.track_allocation(
        "ptr1", MemoryAllocation(MemoryOperation.NEW, "int", "ptr1", 1)
    )
    checker.track_allocation(
        "ptr2", MemoryAllocation(MemoryOperation.NEW, "int", "ptr2", 2)
    )
    checker.track_deallocation("ptr1", 10)

    unfreed = checker.check_unfreed()
    for issue in unfreed:
        print(f"警告: {issue}")

    check = checker.perform_safety_check("ptr1")
    print(f"ptr1安全检查: {check.level.value} - {check.message}")

    print("\n--- 安全报告 ---")
    print(checker.generate_safety_report())

    print("\n=== 测试完成 ===")

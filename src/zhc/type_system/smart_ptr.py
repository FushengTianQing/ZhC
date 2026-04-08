#!/usr/bin/env python3
"""
Day 22: 智能指针实现

功能：
1. 智能指针转换规则
2. 引用计数机制
3. 循环引用检测
"""

import re
from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass


class PointerType(Enum):
    """指针类型"""

    UNIQUE = "独享指针"
    SHARED = "共享指针"
    WEAK = "弱指针"


@dataclass
class SmartPointerInfo:
    """智能指针信息"""

    var_name: str
    type_name: str
    pointer_type: PointerType
    target_type: str
    ref_count: int = 1
    references: Optional[List[str]] = None  # 指向此指针的其他指针
    line_created: int = 0

    def __post_init__(self):
        if self.references is None:
            self.references = []

    def _ensure_references(self) -> List[str]:
        """确保references不为None"""
        if self.references is None:
            self.references = []
        return self.references


class ReferenceCountManager:
    """引用计数管理器"""

    def __init__(self):
        self.pointers: Dict[str, SmartPointerInfo] = {}
        self.ownership: Dict[str, Set[str]] = {}  # ptr -> set of refs to it

    def register(
        self,
        var_name: str,
        type_name: str,
        pointer_type: PointerType,
        target_type: str,
        line: int,
    ) -> SmartPointerInfo:
        """注册智能指针"""
        info = SmartPointerInfo(
            var_name=var_name,
            type_name=type_name,
            pointer_type=pointer_type,
            target_type=target_type,
            line_created=line,
        )
        self.pointers[var_name] = info
        if var_name not in self.ownership:
            self.ownership[var_name] = set()
        return info

    def add_reference(self, from_ptr: str, to_ptr: str):
        """添加引用关系"""
        if to_ptr in self.pointers:
            refs = self.pointers[to_ptr]._ensure_references()
            refs.append(from_ptr)
            self.pointers[to_ptr].ref_count += 1
            if to_ptr in self.ownership:
                self.ownership[to_ptr].add(from_ptr)

    def release(self, var_name: str) -> bool:
        """释放引用，返回是否应该删除对象"""
        if var_name not in self.pointers:
            return False

        info = self.pointers[var_name]
        info.ref_count -= 1

        # 如果是独享指针，立即释放
        if info.pointer_type == PointerType.UNIQUE:
            return True

        # 如果引用计数为0，释放对象
        return info.ref_count <= 0

    def get_ref_count(self, var_name: str) -> int:
        """获取引用计数"""
        if var_name not in self.pointers:
            return 0
        return self.pointers[var_name].ref_count

    def detect_cycles(self) -> List[List[str]]:
        """检测循环引用"""
        cycles = []
        visited: Set[str] = set()
        path: List[str] = []

        def dfs(ptr: str, path_set: Set[str]):
            if ptr in path_set:
                # 发现循环
                cycle_start = path.index(ptr)
                cycle = path[cycle_start:] + [ptr]
                cycles.append(cycle)
                return

            if ptr in visited:
                return

            visited.add(ptr)
            path.append(ptr)
            path_set.add(ptr)

            if ptr in self.ownership:
                for ref in self.ownership[ptr]:
                    if ref in self.pointers:
                        dfs(ref, path_set.copy())

            path.pop()

        for ptr in self.pointers:
            if ptr not in visited:
                dfs(ptr, set())

        return cycles


class SmartPointerConverter:
    """智能指针转换器"""

    # 独享指针模式: 独享指针<类型> 变量名;
    UNIQUE_PATTERN = r"独享指针<(\w+)>\s+(\w+)\s*;"

    # 共享指针模式: 共享指针<类型> 变量名;
    SHARED_PATTERN = r"共享指针<(\w+)>\s+(\w+)\s*;"

    # 弱指针模式: 弱指针<类型> 变量名;
    WEAK_PATTERN = r"弱指针<(\w+)>\s+(\w+)\s*;"

    def __init__(self):
        self.ref_manager = ReferenceCountManager()
        self.converted_code: List[str] = []
        self.errors: List[str] = []

    def parse_and_convert(self, line: str, line_num: int) -> Optional[str]:
        """解析并转换智能指针"""
        # 独享指针
        match = re.search(self.UNIQUE_PATTERN, line)
        if match:
            target_type = match.group(1)
            var_name = match.group(2)
            return self._convert_unique(target_type, var_name, line_num)

        # 共享指针
        match = re.search(self.SHARED_PATTERN, line)
        if match:
            target_type = match.group(1)
            var_name = match.group(2)
            return self._convert_shared(target_type, var_name, line_num)

        # 弱指针
        match = re.search(self.WEAK_PATTERN, line)
        if match:
            target_type = match.group(1)
            var_name = match.group(2)
            return self._convert_weak(target_type, var_name, line_num)

        return None

    def _convert_unique(self, target_type: str, var_name: str, line_num: int) -> str:
        """转换独享指针"""
        self.ref_manager.register(
            var_name, "独享指针", PointerType.UNIQUE, target_type, line_num
        )
        self.converted_code.append(f"/* 独享指针: {var_name} */")
        return f"std::unique_ptr<{target_type}> {var_name} = std::make_unique<{target_type}>();"

    def _convert_shared(self, target_type: str, var_name: str, line_num: int) -> str:
        """转换共享指针"""
        self.ref_manager.register(
            var_name, "共享指针", PointerType.SHARED, target_type, line_num
        )
        self.converted_code.append(f"/* 共享指针: {var_name} (ref_count=1) */")
        return f"std::shared_ptr<{target_type}> {var_name} = std::make_shared<{target_type}>();"

    def _convert_weak(self, target_type: str, var_name: str, line_num: int) -> str:
        """转换弱指针"""
        self.ref_manager.register(
            var_name, "弱指针", PointerType.WEAK, target_type, line_num
        )
        self.converted_code.append(f"/* 弱指针: {var_name} (不增加引用计数) */")
        return f"std::weak_ptr<{target_type}> {var_name};"

    def add_reference(self, from_ptr: str, to_ptr: str):
        """添加指针引用"""
        self.ref_manager.add_reference(from_ptr, to_ptr)

    def release_pointer(self, var_name: str) -> str:
        """释放指针"""
        should_free = self.ref_manager.release(var_name)
        if should_free:
            self.converted_code.append(f"/* 释放: {var_name} */")
            return f"/* {var_name} 将被自动释放 */"
        return f"/* {var_name} 引用计数减1，当前: {self.ref_manager.get_ref_count(var_name)} */"

    def check_cycles(self) -> List[List[str]]:
        """检查循环引用"""
        return self.ref_manager.detect_cycles()

    def generate_header(self) -> str:
        """生成包含头文件"""
        return """#include <memory>  // std::unique_ptr, std::shared_ptr, std::weak_ptr
#include <utility>  // std::move
"""

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        unique_count = sum(
            1
            for p in self.ref_manager.pointers.values()
            if p.pointer_type == PointerType.UNIQUE
        )
        shared_count = sum(
            1
            for p in self.ref_manager.pointers.values()
            if p.pointer_type == PointerType.SHARED
        )
        weak_count = sum(
            1
            for p in self.ref_manager.pointers.values()
            if p.pointer_type == PointerType.WEAK
        )

        return {
            "total": len(self.ref_manager.pointers),
            "unique": unique_count,
            "shared": shared_count,
            "weak": weak_count,
        }


# 测试
if __name__ == "__main__":
    print("=== Day 22 智能指针测试 ===")

    converter = SmartPointerConverter()

    # 测试独享指针
    print("\n--- 独享指针 ---")
    code = converter.parse_and_convert("独享指针<整数型> ptr;", 1)
    print("输入: 独享指针<整数型> ptr;")
    print(f"输出: {code}")

    # 测试共享指针
    print("\n--- 共享指针 ---")
    code = converter.parse_and_convert("共享指针<整数型> shared;", 2)
    print("输入: 共享指针<整数型> shared;")
    print(f"输出: {code}")

    # 测试弱指针
    print("\n--- 弱指针 ---")
    code = converter.parse_and_convert("弱指针<整数型> weak;", 3)
    print("输入: 弱指针<整数型> weak;")
    print(f"输出: {code}")

    # 测试引用计数
    print("\n--- 引用计数 ---")
    converter.add_reference("ptr2", "shared")
    print("添加引用: ptr2 -> shared")
    print(f"shared引用计数: {converter.ref_manager.get_ref_count('shared')}")

    # 测试释放
    print("\n--- 释放 ---")
    msg = converter.release_pointer("shared")
    print(f"释放shared: {msg}")

    # 检查循环引用
    print("\n--- 循环引用检测 ---")
    cycles = converter.check_cycles()
    print(f"检测到循环: {len(cycles)} 个")

    # 统计
    print("\n--- 统计 ---")
    stats = converter.get_statistics()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\n=== 测试完成 ===")

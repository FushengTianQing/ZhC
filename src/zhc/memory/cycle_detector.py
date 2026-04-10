#!/usr/bin/env python3
"""
循环引用检测器

检测共享指针之间的循环引用
"""

from typing import Set, List, Optional
from .smart_ptr import SharedPtr, ControlBlock


class CycleDetector:
    """循环引用检测器"""

    def __init__(self):
        self.visited: Set[int] = set()
        self.path: List[int] = []

    def detect(self, shared_ptr: SharedPtr) -> bool:
        """
        检测是否存在循环引用

        Args:
            shared_ptr: 要检测的共享指针

        Returns:
            True 如果存在循环引用，False 否则
        """
        self.visited.clear()
        self.path.clear()
        return self._dfs(shared_ptr._control, [])

    def _dfs(self, control: Optional[ControlBlock], path: List[int]) -> bool:
        """
        深度优先搜索检测环

        Args:
            control: 当前控制块
            path: 当前路径（控制块 ID 列表）

        Returns:
            True 如果发现环，False 否则
        """
        if control is None:
            return False

        control_id = id(control)

        # 检查是否在当前路径中（发现环）
        if control_id in path:
            return True

        # 已经访问过，跳过
        if control_id in self.visited:
            return False

        self.visited.add(control_id)
        path.append(control_id)

        # 检查控制块引用的对象中的 shared_ptr
        if hasattr(control.object, "__dict__"):
            for attr_value in control.object.__dict__.values():
                if isinstance(attr_value, SharedPtr):
                    if self._dfs(attr_value._control, path[:]):
                        return True

        return False

    def find_cycle_path(self, shared_ptr: SharedPtr) -> List[int]:
        """
        找到循环引用的路径

        Args:
            shared_ptr: 要检测的共享指针

        Returns:
            循环路径（控制块 ID 列表），如果没有循环则返回空列表
        """
        self.visited.clear()
        self.path.clear()
        result = []
        self._find_path_dfs(shared_ptr._control, [], result)
        return result

    def _find_path_dfs(
        self, control: Optional[ControlBlock], path: List[int], result: List[int]
    ) -> bool:
        """
        深度优先搜索找到循环路径

        Args:
            control: 当前控制块
            path: 当前路径
            result: 输出结果

        Returns:
            True 如果找到环
        """
        if control is None:
            return False

        control_id = id(control)

        # 发现环
        if control_id in path:
            cycle_start = path.index(control_id)
            result.extend(path[cycle_start:])
            result.append(control_id)
            return True

        if control_id in self.visited:
            return False

        self.visited.add(control_id)
        path.append(control_id)

        if hasattr(control.object, "__dict__"):
            for attr_value in control.object.__dict__.values():
                if isinstance(attr_value, SharedPtr):
                    if self._find_path_dfs(attr_value._control, path[:], result):
                        return True

        return False


# 测试
if __name__ == "__main__":
    print("=== 循环引用检测器测试 ===\n")

    from .smart_ptr import SharedPtr

    # 创建一个简单的对象
    class Node:
        def __init__(self, name):
            self.name = name
            self.next = None

        def __repr__(self):
            return f"Node({self.name})"

    # 测试无循环引用
    print("--- 无循环引用测试 ---")
    node1 = Node("node1")
    sptr1 = SharedPtr.make(node1)

    detector = CycleDetector()
    has_cycle = detector.detect(sptr1)
    print(f"检测到循环引用: {has_cycle}")

    # 测试有循环引用
    print("\n--- 循环引用测试 ---")
    node2 = Node("node2")
    node3 = Node("node3")

    sptr2 = SharedPtr.make(node2)
    sptr3 = SharedPtr.make(node3)

    # 创建循环: node2 -> node3 -> node2
    node2.next = sptr3
    node3.next = sptr2

    has_cycle = detector.detect(sptr2)
    print(f"检测到循环引用: {has_cycle}")

    if has_cycle:
        cycle_path = detector.find_cycle_path(sptr2)
        print(f"循环路径长度: {len(cycle_path)}")

    print("\n=== 测试完成 ===")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAII (Resource Acquisition Is Initialization) 核心实现

提供：
1. DestructorInfo - 析构函数信息
2. CleanupStack - 清理栈（自动调用析构函数）
3. ScopeGuard - 作用域守卫

作者: 阿福
日期: 2026-04-10
"""

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Any, Dict
from enum import Enum


class CleanupPriority(Enum):
    """清理优先级"""

    HIGH = 0  # 高优先级（如文件句柄）
    NORMAL = 1  # 正常优先级（如内存）
    LOW = 2  # 低优先级（如日志）


@dataclass
class DestructorInfo:
    """析构函数信息

    记录对象的析构函数及其调用上下文。

    属性：
        obj_id: 对象唯一标识
        destructor: 析构函数（可调用对象）
        priority: 清理优先级
        scope_id: 所属作用域ID
        is_called: 析构函数是否已被调用
        metadata: 额外元数据（如类型名、变量名）
    """

    obj_id: str
    destructor: Callable[[], None]
    priority: CleanupPriority = CleanupPriority.NORMAL
    scope_id: int = 0
    is_called: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def call(self) -> bool:
        """调用析构函数

        返回：
            True 如果成功调用，False 如果已调用过
        """
        if self.is_called:
            return False
        try:
            self.destructor()
            self.is_called = True
            return True
        except Exception as e:
            # 记录错误但不抛出，确保其他析构函数仍能执行
            self.metadata["error"] = str(e)
            self.is_called = True  # 标记为已尝试
            return False


class CleanupStack:
    """清理栈

    管理作用域内的析构函数调用。当作用域退出时，按优先级和注册顺序的逆序调用析构函数。

    用法：
        stack = CleanupStack()
        stack.push(destructor_info)
        # ... 作用域代码 ...
        stack.pop_all()  # 自动调用所有析构函数
    """

    def __init__(self):
        self._stack: List[DestructorInfo] = []
        self._scope_counter: int = 0
        self._current_scope: int = 0

    def enter_scope(self) -> int:
        """进入新作用域

        返回：
            新作用域ID
        """
        self._scope_counter += 1
        self._current_scope = self._scope_counter
        return self._current_scope

    def exit_scope(self) -> List[DestructorInfo]:
        """退出当前作用域

        调用当前作用域内所有析构函数，并返回已处理的析构函数列表。

        返回：
            已处理的析构函数列表
        """
        scope_id = self._current_scope
        called = []

        # 从栈顶向下查找当前作用域的析构函数
        i = len(self._stack) - 1
        while i >= 0:
            info = self._stack[i]
            if info.scope_id == scope_id:
                if info.call():
                    called.append(info)
                self._stack.pop(i)
            i -= 1

        # 恢复到上一作用域
        if self._stack:
            self._current_scope = self._stack[-1].scope_id
        else:
            self._current_scope = 0

        return called

    def push(
        self,
        destructor: Callable[[], None],
        priority: CleanupPriority = CleanupPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DestructorInfo:
        """注册析构函数

        参数：
            destructor: 析构函数
            priority: 清理优先级
            metadata: 额外元数据

        返回：
            创建的 DestructorInfo 对象
        """
        obj_id = f"obj_{len(self._stack)}_{id(destructor)}"
        info = DestructorInfo(
            obj_id=obj_id,
            destructor=destructor,
            priority=priority,
            scope_id=self._current_scope,
            metadata=metadata or {},
        )

        # 按优先级插入（高优先级在前）
        inserted = False
        for i, existing in enumerate(self._stack):
            if (
                existing.scope_id == self._current_scope
                and priority.value < existing.priority.value
            ):
                self._stack.insert(i, info)
                inserted = True
                break

        if not inserted:
            self._stack.append(info)

        return info

    def pop_all(self) -> List[DestructorInfo]:
        """调用所有析构函数并清空栈

        返回：
            已处理的析构函数列表
        """
        called = []

        # 按优先级排序后调用
        sorted_stack = sorted(self._stack, key=lambda x: x.priority.value)
        for info in sorted_stack:
            if info.call():
                called.append(info)

        self._stack.clear()
        self._current_scope = 0
        return called

    def remove(self, obj_id: str) -> Optional[DestructorInfo]:
        """移除指定对象的析构函数（不调用）

        参数：
            obj_id: 对象ID

        返回：
            被移除的 DestructorInfo，如果不存在则返回 None
        """
        for i, info in enumerate(self._stack):
            if info.obj_id == obj_id:
                return self._stack.pop(i)
        return None

    def __len__(self) -> int:
        return len(self._stack)

    def __enter__(self):
        """支持 with 语句"""
        self.enter_scope()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持 with 语句"""
        self.exit_scope()
        return False  # 不抑制异常


class ScopeGuard:
    """作用域守卫

    RAII 模式的核心实现，确保资源在作用域退出时自动释放。

    用法：
        # 方式1：装饰器
        @scope_guard
        def cleanup():
            print("清理资源")

        # 方式2：with 语句
        with ScopeGuard(lambda: print("清理资源")):
            # ... 代码 ...
            pass  # 退出时自动调用清理函数

        # 方式3：手动控制
        guard = ScopeGuard(lambda: print("清理"))
        # ... 代码 ...
        guard.dismiss()  # 取消清理
    """

    def __init__(
        self,
        cleanup_func: Callable[[], None],
        priority: CleanupPriority = CleanupPriority.NORMAL,
        stack: Optional[CleanupStack] = None,
    ):
        """初始化作用域守卫

        参数：
            cleanup_func: 清理函数
            priority: 清理优先级
            stack: 使用的清理栈（None 则使用全局栈）
        """
        self._cleanup_func = cleanup_func
        self._priority = priority
        self._dismissed = False
        self._called = False
        self._stack = stack
        self._info: Optional[DestructorInfo] = None

        # 注册到清理栈
        if self._stack:
            self._info = self._stack.push(cleanup_func, priority)

    def dismiss(self):
        """取消清理

        调用此方法后，作用域退出时不会执行清理函数。
        """
        self._dismissed = True
        if self._info and self._stack:
            self._stack.remove(self._info.obj_id)

    def force_call(self):
        """强制调用清理函数"""
        if not self._called:
            self._cleanup_func()
            self._called = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._dismissed and not self._called:
            self._cleanup_func()
            self._called = True
        return False  # 不抑制异常

    def __del__(self):
        """析构时确保清理"""
        if not self._dismissed and not self._called:
            try:
                self._cleanup_func()
                self._called = True
            except Exception:
                pass  # 忽略析构时的异常


def scope_guard(func: Callable[[], None]) -> ScopeGuard:
    """作用域守卫装饰器

    用法：
        @scope_guard
        def cleanup():
            close_file()
    """
    return ScopeGuard(func)


# 全局清理栈
_global_cleanup_stack: Optional[CleanupStack] = None


def get_global_cleanup_stack() -> CleanupStack:
    """获取全局清理栈"""
    global _global_cleanup_stack
    if _global_cleanup_stack is None:
        _global_cleanup_stack = CleanupStack()
    return _global_cleanup_stack


class DestructorRegistry:
    """析构函数注册表

    管理所有类型的析构函数，支持自定义类型的析构函数注册和查询。

    用法：
        registry = DestructorRegistry()
        registry.register("MyClass", my_class_destructor)
        destructor = registry.get("MyClass")
    """

    def __init__(self):
        self._destructors: Dict[str, Callable[[Any], None]] = {}
        self._type_info: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        type_name: str,
        destructor: Callable[[Any], None],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """注册类型的析构函数

        参数：
            type_name: 类型名
            destructor: 析构函数（接受对象实例作为参数）
            metadata: 类型元数据
        """
        self._destructors[type_name] = destructor
        self._type_info[type_name] = metadata or {}

    def unregister(self, type_name: str) -> bool:
        """取消注册类型的析构函数

        参数：
            type_name: 类型名

        返回：
            True 如果成功取消，False 如果类型不存在
        """
        if type_name in self._destructors:
            del self._destructors[type_name]
            del self._type_info[type_name]
            return True
        return False

    def get(self, type_name: str) -> Optional[Callable[[Any], None]]:
        """获取类型的析构函数

        参数：
            type_name: 类型名

        返回：
            析构函数，如果不存在则返回 None
        """
        return self._destructors.get(type_name)

    def has(self, type_name: str) -> bool:
        """检查类型是否已注册析构函数"""
        return type_name in self._destructors

    def get_type_info(self, type_name: str) -> Optional[Dict[str, Any]]:
        """获取类型元数据"""
        return self._type_info.get(type_name)

    def create_instance_destructor(
        self, type_name: str, instance: Any
    ) -> Optional[DestructorInfo]:
        """为实例创建析构函数信息

        参数：
            type_name: 类型名
            instance: 对象实例

        返回：
            DestructorInfo 对象，如果类型未注册则返回 None
        """
        destructor = self.get(type_name)
        if destructor is None:
            return None

        obj_id = f"{type_name}_{id(instance)}"
        return DestructorInfo(
            obj_id=obj_id,
            destructor=lambda: destructor(instance),
            metadata={"type_name": type_name},
        )

    def list_registered_types(self) -> List[str]:
        """列出所有已注册的类型"""
        return list(self._destructors.keys())


# 全局析构函数注册表
_global_destructor_registry: Optional[DestructorRegistry] = None


def get_global_destructor_registry() -> DestructorRegistry:
    """获取全局析构函数注册表"""
    global _global_destructor_registry
    if _global_destructor_registry is None:
        _global_destructor_registry = DestructorRegistry()
    return _global_destructor_registry


# 测试
if __name__ == "__main__":
    print("=== RAII 核心测试 ===")

    # 测试 CleanupStack
    print("\n--- CleanupStack 测试 ---")
    stack = CleanupStack()

    scope1 = stack.enter_scope()
    print(f"进入作用域 {scope1}")

    stack.push(lambda: print("  清理对象 A"), metadata={"name": "A"})
    stack.push(
        lambda: print("  清理对象 B"),
        priority=CleanupPriority.HIGH,
        metadata={"name": "B"},
    )
    stack.push(lambda: print("  清理对象 C"), metadata={"name": "C"})

    print(f"栈大小: {len(stack)}")
    called = stack.exit_scope()
    print(f"已调用 {len(called)} 个析构函数")

    # 测试 ScopeGuard
    print("\n--- ScopeGuard 测试 ---")
    with ScopeGuard(lambda: print("  作用域退出清理")):
        print("  作用域内代码")
    print("  作用域已退出")

    # 测试 dismiss
    print("\n--- ScopeGuard.dismiss 测试 ---")
    guard = ScopeGuard(lambda: print("  这不应该被打印"))
    guard.dismiss()
    del guard  # 触发 __del__
    print("  guard 已删除（清理被取消）")

    # 测试 DestructorRegistry
    print("\n--- DestructorRegistry 测试 ---")
    registry = DestructorRegistry()

    def my_class_destructor(obj):
        print(f"  销毁 MyObject: {obj.name}")

    registry.register("MyClass", my_class_destructor, {"fields": ["name"]})

    class MyObject:
        def __init__(self, name):
            self.name = name

    obj = MyObject("test")
    info = registry.create_instance_destructor("MyClass", obj)
    if info:
        info.call()

    print(f"已注册类型: {registry.list_registered_types()}")

    print("\n=== 测试完成 ===")

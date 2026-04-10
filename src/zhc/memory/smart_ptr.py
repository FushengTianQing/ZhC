#!/usr/bin/env python3
"""
智能指针运行时实现

提供类似 C++ unique_ptr/shared_ptr/weak_ptr 的功能
"""

from dataclasses import dataclass
from typing import TypeVar, Generic, Optional, Callable, Any

T = TypeVar("T")


@dataclass
class ControlBlock:
    """控制块 - 管理引用计数"""

    object: Any  # 管理的对象
    ref_count: int = 1  # 共享引用计数
    weak_count: int = 0  # 弱引用计数
    deleter: Optional[Callable] = None  # 自定义删除器
    type_info: Optional[str] = None  # 类型信息

    def add_ref(self) -> int:
        """增加引用计数"""
        self.ref_count += 1
        return self.ref_count

    def release(self) -> int:
        """减少引用计数，返回剩余计数"""
        self.ref_count -= 1
        if self.ref_count <= 0:
            self._destroy_object()
            self._release_weak()
        return self.ref_count

    def add_weak_ref(self) -> int:
        """增加弱引用计数"""
        self.weak_count += 1
        return self.weak_count

    def release_weak(self) -> int:
        """减少弱引用计数"""
        self.weak_count -= 1
        if self.weak_count <= 0 and self.ref_count <= 0:
            self._destroy_control_block()
        return self.weak_count

    def _destroy_object(self) -> None:
        """销毁对象"""
        if self.deleter:
            self.deleter(self.object)
        elif self.object:
            # 尝试调用析构函数
            if hasattr(self.object, "__del__"):
                try:
                    self.object.__del__()
                except Exception:
                    pass
        self.object = None

    def _release_weak(self) -> None:
        """释放弱引用"""
        if self.weak_count <= 0:
            self._destroy_control_block()

    def _destroy_control_block(self) -> None:
        """销毁控制块自身"""
        self.object = None
        self.deleter = None


@dataclass
class UniquePtr(Generic[T]):
    """独享指针 - 独占所有权"""

    _ptr: Optional[Any] = None
    _deleter: Optional[Callable] = None

    @classmethod
    def make(cls, value: T, deleter: Optional[Callable] = None) -> "UniquePtr[T]":
        """创建独享指针"""
        ptr = cls()
        ptr._ptr = value
        ptr._deleter = deleter or (lambda x: None)
        return ptr

    def get(self) -> Optional[T]:
        """获取裸指针"""
        return self._ptr

    def release(self) -> Optional[T]:
        """释放所有权，返回裸指针"""
        ptr = self._ptr
        self._ptr = None
        return ptr

    def reset(self, new_ptr: Optional[T] = None) -> None:
        """重置指针"""
        if self._ptr is not None:
            if self._deleter:
                self._deleter(self._ptr)
        self._ptr = new_ptr

    def swap(self, other: "UniquePtr[T]") -> None:
        """交换所有权"""
        self._ptr, other._ptr = other._ptr, self._ptr
        self._deleter, other._deleter = other._deleter, self._deleter

    def __enter__(self) -> Optional[T]:
        return self._ptr

    def __exit__(self, *args) -> None:
        self.reset()

    def __bool__(self) -> bool:
        return self._ptr is not None

    def __del__(self) -> None:
        self.reset()

    def __repr__(self) -> str:
        return f"UniquePtr({self._ptr!r})"


@dataclass
class SharedPtr(Generic[T]):
    """共享指针 - 共享所有权"""

    _ptr: Optional[Any] = None
    _control: Optional[ControlBlock] = None

    @classmethod
    def make(cls, value: T, deleter: Optional[Callable] = None) -> "SharedPtr[T]":
        """创建共享指针"""
        ptr = cls()
        ptr._ptr = value
        ptr._control = ControlBlock(
            object=value,
            deleter=deleter,
            type_info=type(value).__name__ if value else None,
        )
        return ptr

    @classmethod
    def from_existing(cls, ptr: Any, control: ControlBlock) -> "SharedPtr[T]":
        """从已有指针创建（增加引用计数）"""
        shared = cls()
        shared._ptr = ptr
        shared._control = control
        control.add_ref()
        return shared

    def get(self) -> Optional[T]:
        """获取裸指针"""
        return self._ptr

    def ref_count(self) -> int:
        """获取引用计数"""
        return self._control.ref_count if self._control else 0

    def reset(
        self, new_ptr: Optional[T] = None, deleter: Optional[Callable] = None
    ) -> None:
        """重置指针"""
        if self._control:
            self._control.release()
        if new_ptr is not None:
            self._ptr = new_ptr
            self._control = ControlBlock(object=new_ptr, deleter=deleter)
        else:
            self._ptr = None
            self._control = None

    def to_weak(self) -> "WeakPtr[T]":
        """转换为弱指针"""
        return WeakPtr.make(self._ptr, self._control)

    def __bool__(self) -> bool:
        return self._ptr is not None

    def __del__(self) -> None:
        if self._control:
            self._control.release()

    def __copy__(self) -> "SharedPtr[T]":
        """浅拷贝 - 增加引用计数"""
        return SharedPtr.from_existing(self._ptr, self._control)

    def __repr__(self) -> str:
        ref_cnt = self.ref_count() if self._control else 0
        return f"SharedPtr({self._ptr!r}, ref_count={ref_cnt})"


@dataclass
class WeakPtr(Generic[T]):
    """弱指针 - 不拥有所有权"""

    _ptr: Optional[Any] = None
    _control: Optional[ControlBlock] = None

    @classmethod
    def make(cls, ptr: Any, control: ControlBlock) -> "WeakPtr[T]":
        """创建弱指针"""
        weak = cls()
        weak._ptr = ptr
        weak._control = control
        control.add_weak_ref()
        return weak

    def lock(self) -> Optional[SharedPtr[T]]:
        """升级为共享指针"""
        if self.expired():
            return None
        return SharedPtr.from_existing(self._ptr, self._control)

    def expired(self) -> bool:
        """检查对象是否已销毁"""
        return self._control is None or self._control.ref_count <= 0

    def ref_count(self) -> int:
        """获取引用计数"""
        return self._control.ref_count if self._control else 0

    def reset(self) -> None:
        """重置弱指针"""
        if self._control:
            self._control.release_weak()
        self._ptr = None
        self._control = None

    def __del__(self) -> None:
        self.reset()

    def __repr__(self) -> str:
        expired = self.expired()
        return f"WeakPtr(expired={expired})"


# 测试
if __name__ == "__main__":
    print("=== 智能指针测试 ===\n")

    # 测试 UniquePtr
    print("--- UniquePtr 测试 ---")
    uptr = UniquePtr.make(42)
    print(f"创建: {uptr}")
    print(f"获取值: {uptr.get()}")
    print(f"释放所有权: {uptr.release()}")
    print(f"释放后: {uptr}")

    # 测试 SharedPtr
    print("\n--- SharedPtr 测试 ---")
    sptr1 = SharedPtr.make(100)
    print(f"创建 sptr1: {sptr1}")

    sptr2 = sptr1.__copy__()  # 共享所有权
    print(f"复制 sptr2: {sptr2}")
    print(f"sptr1 引用计数: {sptr1.ref_count()}")

    sptr3 = SharedPtr.from_existing(sptr1._ptr, sptr1._control)
    print(f"sptr3 引用计数: {sptr3.ref_count()}")

    # 测试 WeakPtr
    print("\n--- WeakPtr 测试 ---")
    wptr = sptr1.to_weak()
    print(f"创建弱指针: {wptr}")
    print(f"是否过期: {wptr.expired()}")

    locked = wptr.lock()
    print(f"锁定后: {locked}")

    # 释放所有共享指针
    print("\n--- 释放测试 ---")
    sptr1.reset()
    print(f"sptr1.reset() 后，sptr2 引用计数: {sptr2.ref_count()}")
    sptr2.reset()
    sptr3.reset()
    print(f"所有共享指针释放后，弱指针是否过期: {wptr.expired()}")

    print("\n=== 测试完成 ===")

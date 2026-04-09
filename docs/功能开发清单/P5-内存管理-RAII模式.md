# P5-内存管理-RAII模式

> **优先级**: P5
> **功能模块**: 内存管理
> **功能名称**: RAII 模式
> **创建日期**: 2026-04-10
> **状态**: 规划中

## 1. 功能概述

实现资源获取即初始化（Resource Acquisition Is Initialization）模式，确保资源在构造时获取、在析构时释放，支持文件、锁、连接等资源的自动管理。

### 1.1 目标

- 支持构造函数/析构函数语法
- 支持 RAII 资源管理模式
- 支持与异常处理的集成
- 支持作用域绑定的资源管理

### 1.2 语法设计

```zhc
// 资源类定义
类 文件资源 {
    私有:
        句柄 文件句柄;
        字符串 文件名;
    
    公共:
        构造函数(字符串 文件名) {
            本.文件名 = 文件名;
            本.文件句柄 = 打开文件(文件名);
            打印("打开文件: " + 文件名);
        }
        
        析构函数() {
            如果 (本.文件句柄 != 空) {
                关闭文件(本.文件句柄);
                打印("关闭文件: " + 本.文件名);
            }
        }
        
        函数 读取(整数型 大小) -> 字节数组 {
            返回 文件读取(本.文件句柄, 大小);
        }
}

// RAII 使用 - 作用域结束自动释放
函数 示例1() {
    打印("开始");
    {
        文件资源 文件("test.txt");
        字节数组 数据 = 文件.读取(100);
        // 文件在作用域结束时自动关闭
    }
    打印("结束");  // 文件已关闭
}

// 互斥锁 RAII
类 互斥锁管理器 {
    私有:
        互斥锁 锁;
    
    公共:
        构造函数() {
            锁.加锁();
        }
        
        析构函数() {
            锁.解锁();
        }
}

函数 线程安全操作() {
    互斥锁管理器 锁;  // 自动加锁
    // ... 临界区代码 ...
    // 作用域结束自动解锁
}

// 作用域锁（更简洁的语法）
函数 作用域锁示例() {
    打印("进入临界区");
    
    作用域锁定 锁(互斥锁);  // 自动加锁
    
    // ... 临界区代码 ...
    
    // 作用域结束自动解锁
    打印("退出临界区");
}

// 唯一资源（move 语义）
函数 move 示例() {
    文件资源 文件1("a.txt");
    文件资源 文件2 = 移动(文件1);  // 所有权转移，文件1析构
    // 此时只有文件2持有资源
}
// 文件2析构时关闭文件
```

---

## 2. 现有项目分析

### 2.1 相关模块

| 模块 | 路径 | 现有功能 |
|------|------|----------|
| 内存管理 | `src/zhc/memcheck/` | 内存追踪 |
| 智能指针 | `src/zhc/type_system/smart_ptr.py` | 资源管理 |
| 类型系统 | `src/zhc/type_system/` | 类定义 |

### 2.2 缺失功能

- ❌ 析构函数支持
- ❌ 作用域资源管理
- ❌ 移动语义
- ❌ 自动资源清理

---

## 3. 技术实现方案

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      RAII 系统                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐      ┌─────────────────┐            │
│  │ DestructorInfo  │      │ ScopeGuard      │            │
│  │ - method_ptr    │      │ - enter()       │            │
│  │ - object        │      │ - exit()        │            │
│  └─────────────────┘      └─────────────────┘            │
│           │                        │                        │
│           ▼                        ▼                        │
│  ┌─────────────────┐      ┌─────────────────┐            │
│  │ CleanupStack    │      │ ResourceWrapper  │            │
│  │ - push()       │      │ - acquire()      │            │
│  │ - pop()        │      │ - release()      │            │
│  │ - unwind()     │      └─────────────────┘            │
│  └─────────────────┘                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 核心数据结构

```python
# src/zhc/memory/raii.py

from dataclasses import dataclass, field
from typing import List, Callable, Any, Optional
from enum import Enum

@dataclass
class DestructorInfo:
    """析构函数信息"""
    object_ref: Any              # 对象引用
    destructor: Callable          # 析构函数
    priority: int = 0           # 优先级（LIFO）

@dataclass
class CleanupStack:
    """清理栈 - 用于栈展开时的资源清理"""
    _stack: List[DestructorInfo] = field(default_factory=list)
    
    def push(self, info: DestructorInfo) -> None:
        """压入析构函数"""
        self._stack.append(info)
    
    def pop(self) -> Optional[DestructorInfo]:
        """弹出析构函数"""
        if self._stack:
            return self._stack.pop()
        return None
    
    def unwind(self) -> None:
        """展开清理栈（倒序执行析构函数）"""
        while self._stack:
            info = self.pop()
            if info:
                try:
                    info.destructor(info.object_ref)
                except Exception as e:
                    # 记录析构函数中的错误，但不阻止其他清理
                    pass
    
    def clear(self) -> None:
        """清空清理栈"""
        self._stack.clear()

# 全局清理栈
_global_cleanup_stack = CleanupStack()

@dataclass
class ScopeGuard:
    """作用域守卫 - RAII 模式实现"""
    _cleanup: Callable
    _active: bool = True
    
    @classmethod
    def create(cls, cleanup: Callable) -> 'ScopeGuard':
        """创建作用域守卫"""
        return cls(_cleanup=cleanup)
    
    def release(self) -> None:
        """提前释放（禁用清理）"""
        self._active = False
    
    def __enter__(self) -> 'ScopeGuard':
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._active:
            self._cleanup()
    
    def __del__(self) -> None:
        if self._active:
            self._cleanup()

@dataclass
class ResourceWrapper:
    """资源包装器"""
    _resource: Any
    _acquired: bool = False
    _acquire: Optional[Callable] = None
    _release: Optional[Callable] = None
    
    @classmethod
    def wrap(cls, resource: Any, 
             acquire: Callable = None, 
             release: Callable = None) -> 'ResourceWrapper':
        """包装资源"""
        wrapper = cls(_resource=resource)
        wrapper._acquire = acquire or (lambda r: None)
        wrapper._release = release or (lambda r: None)
        return wrapper
    
    def acquire(self) -> None:
        """获取资源"""
        if not self._acquired:
            self._acquire(self._resource)
            self._acquired = True
    
    def release(self) -> None:
        """释放资源"""
        if self._acquired:
            self._release(self._resource)
            self._acquired = False
    
    def __enter__(self) -> Any:
        self.acquire()
        return self._resource
    
    def __exit__(self, *args) -> None:
        self.release()
    
    def __del__(self) -> None:
        self.release()

@dataclass  
class LockGuard:
    """锁守卫 - 互斥锁 RAII"""
    _lock: Any
    _acquired: bool = False
    
    @classmethod
    def create(cls, lock: Any) -> 'LockGuard':
        """创建锁守卫"""
        guard = cls(_lock=lock)
        lock.acquire()
        guard._acquired = True
        return guard
    
    def unlock(self) -> None:
        """提前解锁"""
        if self._acquired:
            self._lock.release()
            self._acquired = False
    
    def __enter__(self) -> 'LockGuard':
        return self
    
    def __exit__(self, *args) -> None:
        self.unlock()
    
    def __del__(self) -> None:
        self.unlock()
```

### 3.3 析构函数注册

```python
class DestructorRegistry:
    """析构函数注册表"""
    
    _registry: dict = {}  # type_name -> [destructor_methods]
    
    @classmethod
    def register(cls, type_name: str, destructor: Callable) -> None:
        """注册析构函数"""
        if type_name not in cls._registry:
            cls._registry[type_name] = []
        cls._registry[type_name].append(destructor)
    
    @classmethod
    def get_destructors(cls, type_name: str) -> List[Callable]:
        """获取析构函数列表"""
        return cls._registry.get(type_name, [])
    
    @classmethod
    def call_destructor(cls, obj: Any) -> None:
        """调用对象的析构函数"""
        type_name = type(obj).__name__
        for destructor in cls.get_destructors(type_name):
            try:
                destructor(obj)
            except Exception as e:
                pass  # 记录错误但不阻止
```

### 3.4 异常安全

```python
class ExceptionSafeScope:
    """异常安全作用域"""
    
    def __init__(self):
        self._guards: List[ScopeGuard] = []
    
    def add(self, cleanup: Callable) -> ScopeGuard:
        """添加清理函数"""
        guard = ScopeGuard.create(cleanup)
        self._guards.append(guard)
        return guard
    
    def release_all(self) -> None:
        """释放所有守卫（提前退出）"""
        for guard in reversed(self._guards):
            guard.release()
        self._guards.clear()
    
    def __enter__(self) -> 'ExceptionSafeScope':
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            # 发生异常，清理所有资源
            self._guards.clear()
        else:
            # 正常退出
            self._guards.clear()
```

---

## 4. 实现计划

### 4.1 第一阶段：核心实现

**文件变更**:
- `src/zhc/memory/raii.py` (新建)

**任务**:
- [ ] 实现 `DestructorInfo` 类
- [ ] 实现 `CleanupStack` 类
- [ ] 实现 `ScopeGuard` 类
- [ ] 实现 `ResourceWrapper` 类

### 4.2 第二阶段：析构函数支持

**文件变更**:
- `src/zhc/memory/destructor_registry.py` (新建)

**任务**:
- [ ] 实现析构函数注册表
- [ ] 实现析构函数调用机制

### 4.3 第三阶段：语法支持

**文件变更**:
- `src/zhc/parser/lexer.py` (更新)
- `src/zhc/parser/parser.py` (更新)

**任务**:
- [ ] 添加 `析构函数`、`移动` 关键字
- [ ] 解析析构函数语法
- [ ] 解析移动语义

### 4.4 第四阶段：语义分析

**文件变更**:
- `src/zhc/semantic/raii_checker.py` (新建)

**任务**:
- [ ] 析构函数检查
- [ ] 资源生命周期分析
- [ ] 移动语义检查

### 4.5 第五阶段：代码生成

**文件变更**:
- `src/zhc/codegen/llvm_backend.py` (更新)

**任务**:
- [ ] 生成析构函数调用
- [ ] 生成资源清理代码
- [ ] 生成栈展开代码

---

## 5. 验收标准

- [ ] 支持析构函数
- [ ] 支持作用域资源管理
- [ ] 支持自动资源清理
- [ ] 与异常处理集成
- [ ] 支持移动语义
- [ ] 所有单元测试通过

# -*- coding: utf-8 -*-
"""
闭包支持模块 - Closure Support

提供闭包和 Lambda 表达式的核心数据结构：
1. CaptureMode - 变量捕获模式
2. Upvalue - 被捕获的变量
3. ClosureType - 闭包类型
4. ClosureEnvironment - 闭包环境

Phase 5 - 函数式-闭包支持

作者：ZHC 开发团队
日期：2026-04-10
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class CaptureMode(Enum):
    """变量捕获模式

    描述变量如何被闭包捕获：
    - REFERENCE: 引用捕获 - 闭包可以直接修改原变量
    - VALUE: 值捕获 - 闭包获得变量的拷贝，原变量修改不受影响
    - CONST_REF: 常量引用 - 闭包获得只读引用
    """

    REFERENCE = "reference"  # 引用捕获（可修改）
    VALUE = "value"  # 值捕获（不可修改）
    CONST_REF = "const_ref"  # 常量引用

    def __str__(self):
        return self.value


@dataclass
class Upvalue:
    """Upvalue 定义 - 表示被捕获的变量

    Attributes:
        name: 变量名
        type_name: 类型名
        mode: 捕获模式
        index: 在闭包环境中的索引
        is_mutable: 是否可变
    """

    name: str
    type_name: str
    mode: CaptureMode
    index: int
    is_mutable: bool = False

    def __repr__(self):
        return f"Upvalue({self.name}: {self.type_name}, mode={self.mode.value}, index={self.index})"


@dataclass
class ClosureType:
    """闭包类型

    描述一个闭包的类型签名和捕获信息。

    Attributes:
        name: 类型名称（可选，用于调试）
        param_types: 参数类型列表
        return_type: 返回类型
        upvalues: 捕获的变量列表
        environment_size: 环境大小
    """

    name: Optional[str] = None
    param_types: List[str] = field(default_factory=list)
    return_type: str = "空型"
    upvalues: List[Upvalue] = field(default_factory=list)
    environment_size: int = 0

    def get_signature(self) -> str:
        """获取函数签名字符串"""
        params = ", ".join(self.param_types) if self.param_types else "void"
        return f"({params}) -> {self.return_type}"

    def get_capture_signature(self) -> str:
        """获取捕获签名字符串"""
        if not self.upvalues:
            return ""
        captures = []
        for uv in self.upvalues:
            mode_str = {
                CaptureMode.REFERENCE: "&",
                CaptureMode.VALUE: "=",
                CaptureMode.CONST_REF: "&const",
            }.get(uv.mode, "?")
            captures.append(f"{mode_str}{uv.name}")
        return ", ".join(captures)

    def __repr__(self):
        sig = self.get_signature()
        cap = self.get_capture_signature()
        if cap:
            return f"ClosureType({sig} captures=[{cap}]])"
        return f"ClosureType({sig})"


@dataclass
class ClosureEnvironment:
    """闭包环境 - 运行时闭包捕获变量的存储

    管理闭包运行时所需的所有 upvalue。

    Attributes:
        upvalues: upvalue 定义列表
        values: 运行时值字典 {name: value}
    """

    upvalues: List[Upvalue] = field(default_factory=list)
    values: Dict[str, Any] = field(default_factory=dict)

    def get(self, name: str) -> Optional[Any]:
        """获取 upvalue 的值

        Args:
            name: 变量名

        Returns:
            变量的值，如果不存在返回 None
        """
        return self.values.get(name)

    def set(self, name: str, value: Any) -> bool:
        """设置 upvalue 的值

        Args:
            name: 变量名
            value: 新值

        Returns:
            是否设置成功（不可变变量不能被修改）

        Raises:
            ValueError: 如果尝试修改不可变变量
        """
        for uv in self.upvalues:
            if uv.name == name:
                if not uv.is_mutable:
                    raise ValueError(f"Cannot modify immutable upvalue: {name}")
                self.values[name] = value
                return True
        return False

    def allocate(self, name: str, value: Any) -> Optional[Upvalue]:
        """在环境中分配一个新的 upvalue

        Args:
            name: 变量名
            value: 初始值

        Returns:
            创建的 Upvalue，如果已存在则返回 None
        """
        # 检查是否已存在
        for uv in self.upvalues:
            if uv.name == name:
                return None

        # 创建新的 upvalue
        index = len(self.upvalues)
        upvalue = Upvalue(
            name=name,
            type_name=type(value).__name__,
            mode=CaptureMode.VALUE,
            index=index,
            is_mutable=True,
        )
        self.upvalues.append(upvalue)
        self.values[name] = value
        self.environment_size = len(self.upvalues)
        return upvalue

    def __repr__(self):
        return f"ClosureEnvironment({len(self.upvalues)} upvalues)"


@dataclass
class ClosureContext:
    """闭包上下文 - 编译时闭包信息

    用于在编译过程中传递闭包相关的信息。

    Attributes:
        closure_type: 闭包类型信息
        captured_vars: 被捕获的变量集合
        is_nested: 是否是嵌套闭包
        outer_closure: 外层闭包引用（如果是嵌套闭包）
    """

    closure_type: ClosureType = field(default_factory=ClosureType)
    captured_vars: Dict[str, Upvalue] = field(default_factory=dict)
    is_nested: bool = False
    outer_closure: Optional["ClosureContext"] = None

    def add_capture(self, name: str, upvalue: Upvalue):
        """添加捕获变量

        Args:
            name: 变量名
            upvalue: upvalue 信息
        """
        self.captured_vars[name] = upvalue
        self.closure_type.upvalues.append(upvalue)
        self.closure_type.environment_size = len(self.closure_type.upvalues)

    def has_capture(self, name: str) -> bool:
        """检查是否捕获了某个变量

        Args:
            name: 变量名

        Returns:
            是否捕获
        """
        return name in self.captured_vars

    def get_capture(self, name: str) -> Optional[Upvalue]:
        """获取捕获的变量信息

        Args:
            name: 变量名

        Returns:
            Upvalue 信息，如果不存在返回 None
        """
        return self.captured_vars.get(name)

    def __repr__(self):
        return f"ClosureContext({self.closure_type.get_signature()}, {len(self.captured_vars)} captures)"


# ===== 辅助函数 =====


def create_upvalue(
    name: str,
    type_name: str,
    mode: CaptureMode = CaptureMode.VALUE,
    is_mutable: bool = False,
) -> Upvalue:
    """创建 Upvalue 的便捷函数

    Args:
        name: 变量名
        type_name: 类型名
        mode: 捕获模式
        is_mutable: 是否可变

    Returns:
        新的 Upvalue
    """
    return Upvalue(
        name=name,
        type_name=type_name,
        mode=mode,
        index=0,  # 索引后续由环境分配
        is_mutable=is_mutable,
    )


def create_closure_type(
    param_types: List[str],
    return_type: str,
    name: Optional[str] = None,
) -> ClosureType:
    """创建 ClosureType 的便捷函数

    Args:
        param_types: 参数类型列表
        return_type: 返回类型
        name: 类型名称（可选）

    Returns:
        新的 ClosureType
    """
    return ClosureType(
        name=name,
        param_types=param_types,
        return_type=return_type,
    )


def create_closure_environment() -> ClosureEnvironment:
    """创建 ClosureEnvironment 的便捷函数

    Returns:
        新的 ClosureEnvironment
    """
    return ClosureEnvironment()


# ===== 测试代码 =====

if __name__ == "__main__":
    print("=" * 70)
    print("闭包支持模块测试")
    print("=" * 70)

    # 测试 1: Upvalue
    print("\n测试 1: Upvalue 创建")
    uv1 = create_upvalue("count", "整数型", CaptureMode.REFERENCE, is_mutable=True)
    uv2 = create_upvalue("name", "字符串型", CaptureMode.VALUE, is_mutable=False)
    print(f"  uv1: {uv1}")
    print(f"  uv2: {uv2}")

    # 测试 2: ClosureType
    print("\n测试 2: ClosureType 创建")
    closure_type = create_closure_type(
        param_types=["整数型", "整数型"],
        return_type="整数型",
        name="加法闭包",
    )
    closure_type.upvalues.append(uv1)
    closure_type.environment_size = 1
    print(f"  {closure_type}")
    print(f"  签名: {closure_type.get_signature()}")
    print(f"  捕获: {closure_type.get_capture_signature()}")

    # 测试 3: ClosureEnvironment
    print("\n测试 3: ClosureEnvironment")
    env = create_closure_environment()
    env.allocate("count", 0)
    env.allocate("name", "test")
    print(f"  {env}")
    print(f"  count = {env.get('count')}")
    print(f"  name = {env.get('name')}")

    # 测试修改可变 upvalue
    env.set("count", 10)
    print(f"  修改后 count = {env.get('count')}")

    # 测试修改不可变 upvalue
    try:
        env.set("name", "new_name")
    except ValueError as e:
        print(f"  预期错误: {e}")

    # 测试 4: ClosureContext
    print("\n测试 4: ClosureContext")
    ctx = ClosureContext()
    ctx.add_capture("count", uv1)
    print(f"  {ctx}")
    print(f"  has capture 'count': {ctx.has_capture('count')}")
    print(f"  has capture 'name': {ctx.has_capture('name')}")

    print("\n" + "=" * 70)
    print("所有测试完成")
    print("=" * 70)

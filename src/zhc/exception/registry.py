# -*- coding: utf-8 -*-
"""
异常类型注册表

管理所有异常类型的注册、查询和子类型检查。

作者：远
日期：2026-04-10
"""

from typing import Dict, List, Optional, Set
from .types import ExceptionType, ExceptionField


class ExceptionRegistry:
    """
    异常类型注册表（单例模式）

    管理所有异常类型的注册和查询，支持类型层次结构。

    Example:
        >>> registry = ExceptionRegistry.instance()
        >>> exc_type = registry.lookup("除零异常")
        >>> print(exc_type.name)
        除零异常
        >>> print(registry.is_subtype("除零异常", "算术异常"))
        True
    """

    _instance: Optional["ExceptionRegistry"] = None
    _types: Dict[str, ExceptionType] = {}
    _initialized: bool = False

    def __init__(self):
        """初始化注册表（仅通过 instance() 调用）"""
        if ExceptionRegistry._instance is not None:
            raise RuntimeError("ExceptionRegistry 是单例，请使用 instance() 方法")
        self._types: Dict[str, ExceptionType] = {}

    @classmethod
    def instance(cls) -> "ExceptionRegistry":
        """
        获取 ExceptionRegistry 单例实例

        Returns:
            ExceptionRegistry 实例
        """
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._register_builtins()
            cls._initialized = True
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """
        重置注册表（主要用于测试）

        Warning:
            此方法仅用于测试，勿在生产环境调用
        """
        cls._instance = None
        cls._types = {}
        cls._initialized = False

    def register(self, exc_type: ExceptionType) -> None:
        """
        注册异常类型

        Args:
            exc_type: 异常类型定义

        Raises:
            ValueError: 如果类型已注册或基类不存在
        """
        if exc_type.name in self._types:
            raise ValueError(f"异常类型 '{exc_type.name}' 已注册")

        # 检查基类是否存在（如果指定了基类）
        if exc_type.base_class is not None:
            if exc_type.base_class not in self._types:
                raise ValueError(
                    f"异常类型 '{exc_type.name}' 的基类 '{exc_type.base_class}' 不存在"
                )
            # 检查是否形成循环继承
            if self._would_create_cycle(exc_type.name, exc_type.base_class):
                raise ValueError(f"异常类型 '{exc_type.name}' 会导致循环继承")

        self._types[exc_type.name] = exc_type

    def _would_create_cycle(self, type_name: str, base_class: str) -> bool:
        """
        检查添加此类型是否会导致循环继承

        Args:
            type_name: 新类型名称
            base_class: 基类名称

        Returns:
            如果会形成循环返回 True
        """
        visited: Set[str] = set()
        current = base_class

        while current is not None:
            if current == type_name:
                return True
            if current in visited:
                return False  # 已经检查过，不会有环
            visited.add(current)
            t = self._types.get(current)
            if t is None:
                return False
            current = t.base_class

        return False

    def lookup(self, name: str) -> Optional[ExceptionType]:
        """
        根据名称查找异常类型

        Args:
            name: 异常类型名称

        Returns:
            异常类型定义，如果不存在返回 None
        """
        return self._types.get(name)

    def is_subtype(self, subtype: str, supertype: str) -> bool:
        """
        检查子类型关系

        Args:
            subtype: 子类型名称
            supertype: 父类型名称

        Returns:
            如果 subtype 是 supertype 的子类型返回 True
        """
        if subtype == supertype:
            return True

        exc = self._types.get(subtype)
        if exc is None:
            return False

        # 直接基类检查
        if exc.base_class == supertype:
            return True

        # 递归检查祖先类
        current = exc.base_class
        visited: Set[str] = set()

        while current is not None:
            if current in visited:
                return False  # 防止循环
            visited.add(current)

            t = self._types.get(current)
            if t is None:
                return False
            if t.base_class == supertype:
                return True
            current = t.base_class

        return False

    def get_all_subtypes(self, type_name: str) -> List[str]:
        """
        获取指定类型的所有子类型

        Args:
            type_name: 类型名称

        Returns:
            所有子类型的名称列表
        """
        result: List[str] = []
        for name, exc_type in self._types.items():
            if self.is_subtype(name, type_name) and name != type_name:
                result.append(name)
        return result

    def get_type_hierarchy(self) -> Dict[str, List[str]]:
        """
        获取异常类型层次结构

        Returns:
            类型名称 -> 直接子类型列表 的字典
        """
        hierarchy: Dict[str, List[str]] = {"异常": []}  # 基类

        for name, exc_type in self._types.items():
            if exc_type.base_class is None:
                if name != "异常":
                    hierarchy["异常"].append(name)
            else:
                if exc_type.base_class not in hierarchy:
                    hierarchy[exc_type.base_class] = []
                hierarchy[exc_type.base_class].append(name)

        return hierarchy

    def list_all_types(self) -> List[str]:
        """
        列出所有已注册的异常类型

        Returns:
            类型名称列表
        """
        return list(self._types.keys())

    def list_builtin_types(self) -> List[str]:
        """
        列出所有内置异常类型

        Returns:
            内置类型名称列表
        """
        return [name for name, exc_type in self._types.items() if exc_type.is_builtin]

    def _register_builtins(self) -> None:
        """
        注册内置异常类型层次

        内置层次结构：
        异常 (基类)
        ├── 错误 (不可恢复)
        │   ├── 内存错误
        │   ├── 栈溢出错误
        │   └── 系统错误
        │
        └── 异常 (可恢复)
            ├── 运行时异常
            │   ├── 空指针异常
            │   ├── 数组越界异常
            │   └── 类型转换异常
            │
            ├── 输入输出异常
            │   ├── 文件未找到异常
            │   └── 文件权限异常
            │
            └── 算术异常
                ├── 除零异常
                └── 溢出异常
        """
        # ===== 顶层基类 =====
        self.register(
            ExceptionType(
                name="异常",
                base_class=None,
                fields=[
                    ExceptionField("消息", "字符串"),
                    ExceptionField("错误码", "整数型"),
                ],
                methods={"打印": "函数 -> 无"},
                is_builtin=True,
                description="所有异常类型的基类",
            )
        )

        # ===== Error 分支（不可恢复） =====
        self.register(
            ExceptionType(
                name="错误",
                base_class="异常",
                fields=[],
                is_builtin=True,
                description="不可恢复的错误",
            )
        )

        self.register(
            ExceptionType(
                name="内存错误",
                base_class="错误",
                fields=[],
                is_builtin=True,
                description="内存分配或访问错误",
            )
        )

        self.register(
            ExceptionType(
                name="栈溢出错误",
                base_class="错误",
                fields=[
                    ExceptionField("栈大小", "整数型"),
                ],
                is_builtin=True,
                description="栈溢出错误",
            )
        )

        self.register(
            ExceptionType(
                name="系统错误",
                base_class="错误",
                fields=[
                    ExceptionField("系统错误码", "整数型"),
                ],
                is_builtin=True,
                description="系统级错误",
            )
        )

        # ===== Exception 分支（可恢复） =====
        self.register(
            ExceptionType(
                name="运行时异常",
                base_class="异常",
                fields=[],
                is_builtin=True,
                description="运行时逻辑错误",
            )
        )

        self.register(
            ExceptionType(
                name="空指针异常",
                base_class="运行时异常",
                fields=[
                    ExceptionField("变量名", "字符串"),
                ],
                is_builtin=True,
                description="空指针访问错误",
            )
        )

        self.register(
            ExceptionType(
                name="数组越界异常",
                base_class="运行时异常",
                fields=[
                    ExceptionField("数组长度", "整数型"),
                    ExceptionField("访问索引", "整数型"),
                ],
                is_builtin=True,
                description="数组索引越界",
            )
        )

        self.register(
            ExceptionType(
                name="类型转换异常",
                base_class="运行时异常",
                fields=[
                    ExceptionField("源类型", "字符串"),
                    ExceptionField("目标类型", "字符串"),
                ],
                is_builtin=True,
                description="类型转换失败",
            )
        )

        # ===== IO 异常 =====
        self.register(
            ExceptionType(
                name="输入输出异常",
                base_class="异常",
                fields=[
                    ExceptionField("文件路径", "字符串"),
                ],
                is_builtin=True,
                description="IO 操作错误",
            )
        )

        self.register(
            ExceptionType(
                name="文件未找到异常",
                base_class="输入输出异常",
                fields=[
                    ExceptionField("文件路径", "字符串"),
                ],
                is_builtin=True,
                description="文件不存在",
            )
        )

        self.register(
            ExceptionType(
                name="文件权限异常",
                base_class="输入输出异常",
                fields=[
                    ExceptionField("文件路径", "字符串"),
                    ExceptionField("所需权限", "字符串"),
                ],
                is_builtin=True,
                description="文件权限不足",
            )
        )

        # ===== 算术异常 =====
        self.register(
            ExceptionType(
                name="算术异常",
                base_class="异常",
                fields=[],
                is_builtin=True,
                description="算术运算错误",
            )
        )

        self.register(
            ExceptionType(
                name="除零异常",
                base_class="算术异常",
                fields=[
                    ExceptionField("分子", "浮点型"),
                    ExceptionField("分母", "浮点型"),
                ],
                is_builtin=True,
                description="除数为零",
            )
        )

        self.register(
            ExceptionType(
                name="溢出异常",
                base_class="算术异常",
                fields=[
                    ExceptionField("操作", "字符串"),
                    ExceptionField("值", "整数型"),
                ],
                is_builtin=True,
                description="数值溢出",
            )
        )


def get_exception_class(name: str) -> Optional[ExceptionType]:
    """
    获取异常类型定义（便捷函数）

    Args:
        name: 异常类型名称

    Returns:
        异常类型定义
    """
    return ExceptionRegistry.instance().lookup(name)


def is_exception_type(name: str) -> bool:
    """
    检查是否为已注册的异常类型

    Args:
        name: 类型名称

    Returns:
        如果是已注册的异常类型返回 True
    """
    return ExceptionRegistry.instance().lookup(name) is not None


__all__ = [
    "ExceptionRegistry",
    "get_exception_class",
    "is_exception_type",
]

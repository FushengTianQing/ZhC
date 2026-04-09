# -*- coding: utf-8 -*-
"""
ZhC Pass 注册表

管理所有可用的优化 Pass，支持动态注册和查询。

设计模式：
- 注册表模式：集中管理 Pass 实例
- 工厂模式：根据名称创建 Pass
- 单例模式：全局只有一个注册表

作者：远
日期：2026-04-09
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Optional, Any, Set
import logging

logger = logging.getLogger(__name__)


class PassType(Enum):
    """
    Pass 类型枚举

    - Analysis: 分析 Pass，只分析代码不修改
    - Transform: 转换 Pass，修改代码
    - Utility: 工具 Pass，辅助功能
    """

    ANALYSIS = "analysis"
    TRANSFORM = "transform"
    UTILITY = "utility"


@dataclass
class PassInfo:
    """
    Pass 信息描述

    包含 Pass 的元数据和依赖关系。
    """

    name: str
    pass_type: PassType
    description: str
    required_passes: List[str] = field(default_factory=list)
    invalidated_passes: List[str] = field(default_factory=list)
    supports_o0: bool = True  # 是否支持 O0 级别
    supports_o1: bool = True
    supports_o2: bool = True
    supports_o3: bool = True
    supports_os: bool = True
    supports_oz: bool = True

    def supports_level(self, level_name: str) -> bool:
        """检查 Pass 是否支持指定的优化级别"""
        attr_name = f"supports_{level_name.lower()}"
        return getattr(self, attr_name, True)


@dataclass
class PassResult:
    """Pass 执行结果"""

    pass_name: str
    changed: bool
    modified_functions: List[str] = field(default_factory=list)
    modified_instructions: int = 0
    time_ms: float = 0.0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        """Pass 是否成功执行"""
        return self.error is None


class PassRegistry:
    """
    全局 Pass 注册表

    管理所有可用的优化 Pass，支持注册、查询、创建。

    使用方式：
        # 注册 Pass
        PassRegistry.register("dce", PassType.TRANSFORM, "死代码消除",
                              required_passes=["mem2reg"])

        # 获取 Pass 信息
        info = PassRegistry.get_info("dce")

        # 创建 Pass 实例
        pass_instance = PassRegistry.create("dce")
    """

    _instance: Optional["PassRegistry"] = None
    _passes: Dict[str, PassInfo] = {}
    _pass_factories: Dict[str, Callable] = {}
    _initialized: bool = False

    def __new__(cls) -> "PassRegistry":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "PassRegistry":
        """获取注册表单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def register(
        cls,
        name: str,
        pass_type: PassType,
        description: str,
        factory: Optional[Callable] = None,
        required_passes: Optional[List[str]] = None,
        invalidated_passes: Optional[List[str]] = None,
        level_support: Optional[Dict[str, bool]] = None,
    ) -> None:
        """
        注册一个 Pass

        Args:
            name: Pass 名称
            pass_type: Pass 类型
            description: Pass 描述
            factory: Pass 工厂函数，用于创建 Pass 实例
            required_passes: 需要先运行的 Pass 列表
            invalidated_passes: 会使此 Pass 分析结果失效的 Pass 列表
            level_support: 支持的优化级别 {"o0": True, "o1": True, ...}
        """
        info = PassInfo(
            name=name,
            pass_type=pass_type,
            description=description,
            required_passes=required_passes or [],
            invalidated_passes=invalidated_passes or [],
        )

        # 设置级别支持
        if level_support:
            for level, supported in level_support.items():
                attr_name = f"supports_{level.lower()}"
                if hasattr(info, attr_name):
                    setattr(info, attr_name, supported)

        cls._passes[name] = info

        if factory:
            cls._pass_factories[name] = factory

        logger.debug(f"Registered pass: {name} ({pass_type.value})")

    @classmethod
    def register_pass(
        cls,
        name: str,
        pass_type: PassType,
        description: str,
        required_passes: Optional[List[str]] = None,
        invalidated_passes: Optional[List[str]] = None,
    ) -> Callable:
        """
        装饰器：注册 Pass

        使用方式：
            @PassRegistry.register_pass("my_pass", PassType.TRANSFORM, "我的 Pass")
            class MyPass:
                def run(self, module):
                    ...
        """

        def decorator(pass_class_or_func: Callable) -> Callable:
            cls.register(
                name=name,
                pass_type=pass_type,
                description=description,
                factory=pass_class_or_func,
                required_passes=required_passes,
                invalidated_passes=invalidated_passes,
            )
            return pass_class_or_func

        return decorator

    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        注销一个 Pass

        Args:
            name: Pass 名称

        Returns:
            是否成功注销
        """
        if name in cls._passes:
            del cls._passes[name]
            if name in cls._pass_factories:
                del cls._pass_factories[name]
            logger.debug(f"Unregistered pass: {name}")
            return True
        return False

    @classmethod
    def get_info(cls, name: str) -> Optional[PassInfo]:
        """
        获取 Pass 信息

        Args:
            name: Pass 名称

        Returns:
            Pass 信息，如果不存在返回 None
        """
        return cls._passes.get(name)

    @classmethod
    def create(cls, name: str) -> Optional[Any]:
        """
        创建 Pass 实例

        Args:
            name: Pass 名称

        Returns:
            Pass 实例，如果不存在返回 None
        """
        factory = cls._pass_factories.get(name)
        if factory:
            try:
                return factory()
            except Exception as e:
                logger.error(f"Failed to create pass {name}: {e}")
                return None
        return None

    @classmethod
    def list_passes(
        cls,
        pass_type: Optional[PassType] = None,
        min_level: Optional[str] = None,
    ) -> List[str]:
        """
        列出所有注册的 Pass

        Args:
            pass_type: 按类型过滤
            min_level: 最小优化级别（如 "o2"）

        Returns:
            符合条件的 Pass 名称列表
        """
        passes = list(cls._passes.keys())

        if pass_type:
            passes = [
                name for name in passes if cls._passes[name].pass_type == pass_type
            ]

        if min_level:
            passes = [
                name for name in passes if cls._passes[name].supports_level(min_level)
            ]

        return sorted(passes)

    @classmethod
    def get_passes_by_type(cls, pass_type: PassType) -> Dict[str, PassInfo]:
        """获取指定类型的所有 Pass"""
        return {
            name: info
            for name, info in cls._passes.items()
            if info.pass_type == pass_type
        }

    @classmethod
    def get_pass_dependencies(cls, name: str) -> Set[str]:
        """
        获取 Pass 的所有依赖（包括传递依赖）

        Args:
            name: Pass 名称

        Returns:
            依赖的 Pass 名称集合
        """
        info = cls._passes.get(name)
        if not info:
            return set()

        dependencies = set(info.required_passes)
        for dep_name in info.required_passes:
            dependencies.update(cls.get_pass_dependencies(dep_name))

        return dependencies

    @classmethod
    def topological_sort(cls, pass_names: List[str]) -> List[str]:
        """
        对 Pass 列表进行拓扑排序

        确保依赖的 Pass 在被依赖的 Pass 之前执行。

        Args:
            pass_names: Pass 名称列表

        Returns:
            排序后的 Pass 名称列表
        """
        visited: Set[str] = set()
        result: List[str] = []

        def visit(name: str):
            if name in visited:
                return
            visited.add(name)

            info = cls._passes.get(name)
            if info:
                for dep in info.required_passes:
                    if dep in pass_names:
                        visit(dep)

            result.append(name)

        for name in pass_names:
            visit(name)

        return result

    @classmethod
    def reset(cls) -> None:
        """重置注册表（用于测试）"""
        cls._passes.clear()
        cls._pass_factories.clear()
        cls._initialized = False
        logger.debug("Pass registry reset")

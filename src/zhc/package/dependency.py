#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖解析器

使用回溯算法解析依赖关系，处理版本冲突
"""

from typing import Dict, List, Set, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

from .version import Version, VersionConstraint
from .errors import (
    DependencyConflictError,
    CyclicDependencyError,
    PackageNotFoundError,
    VersionNotFoundError,
)

if TYPE_CHECKING:
    from .repository import PackageRepository


@dataclass
class ResolvedDependency:
    """已解析的依赖"""

    name: str
    version: Version
    source: Optional[str]
    dependencies: Dict[str, "ResolvedDependency"] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "version": str(self.version),
            "source": self.source,
            "dependencies": {
                name: dep.to_dict() for name, dep in self.dependencies.items()
            },
        }

    def flatten(self) -> Dict[str, Version]:
        """展平为字典（包名 -> 版本）"""
        result: Dict[str, Version] = {}
        self._flatten_recursive(result)
        return result

    def _flatten_recursive(self, result: Dict[str, Version]):
        """递归展平"""
        if self.name not in result:
            result[self.name] = self.version
        for dep in self.dependencies.values():
            dep._flatten_recursive(result)


class DependencyResolver:
    """依赖解析器

    使用深度优先搜索解析依赖关系，检测循环依赖和版本冲突
    """

    def __init__(self, repository: "PackageRepository"):
        """初始化依赖解析器

        Args:
            repository: 包仓库接口
        """
        self.repository = repository
        self.resolved: Dict[str, ResolvedDependency] = {}
        self.conflicts: List[tuple] = []  # (name, required, resolved)

    def resolve(
        self,
        dependencies: Dict[str, str],
        dev_dependencies: Dict[str, str] = None,
    ) -> Dict[str, ResolvedDependency]:
        """解析依赖关系

        Args:
            dependencies: 直接依赖字典 {包名: 版本约束}
            dev_dependencies: 开发依赖字典

        Returns:
            解析后的依赖树

        Raises:
            DependencyConflictError: 版本冲突
            CyclicDependencyError: 循环依赖
        """
        # 清空之前的结果
        self.resolved.clear()
        self.conflicts.clear()

        # 合并所有依赖
        all_deps = dependencies.copy()
        if dev_dependencies:
            all_deps.update(dev_dependencies)

        # 解析每个依赖
        visited: Set[str] = set()
        for name, constraint in all_deps.items():
            self._resolve_dependency(name, constraint, visited, set())

        # 检查是否有冲突
        if self.conflicts:
            raise DependencyConflictError(self.conflicts)

        return self.resolved

    def _resolve_dependency(
        self,
        name: str,
        constraint_str: str,
        visited: Set[str],
        in_stack: Set[str],
    ):
        """递归解析依赖

        Args:
            name: 包名
            constraint_str: 版本约束字符串
            visited: 已访问的包集合
            in_stack: 当前调用栈中的包（用于检测循环依赖）

        Raises:
            CyclicDependencyError: 循环依赖
            PackageNotFoundError: 包不存在
            VersionNotFoundError: 版本不存在
        """
        # 检测循环依赖
        if name in in_stack:
            raise CyclicDependencyError(list(in_stack) + [name])

        # 检查是否已经解析
        if name in self.resolved:
            existing = self.resolved[name]
            version_constraint = VersionConstraint(constraint_str)

            # 检查版本是否兼容
            if not version_constraint.matches(existing.version):
                self.conflicts.append((name, constraint_str, str(existing.version)))
            return

        # 已经处理过（无冲突），跳过
        if name in visited:
            return

        visited.add(name)
        in_stack.add(name)

        try:
            # 从仓库查询可用版本
            available_versions = self.repository.get_versions(name)
            if not available_versions:
                raise PackageNotFoundError(name)

            # 选择满足约束的最新版本
            version_constraint = VersionConstraint(constraint_str)
            selected_version = self._select_version(
                available_versions, version_constraint
            )

            if not selected_version:
                raise VersionNotFoundError(name, constraint_str)

            # 创建解析结果
            resolved_dep = ResolvedDependency(
                name=name,
                version=selected_version,
                source=self.repository.get_source(name, selected_version),
            )

            # 注册到已解析列表
            self.resolved[name] = resolved_dep

            # 获取该包的依赖
            package_deps = self.repository.get_dependencies(name, selected_version)

            # 递归解析传递依赖
            for dep_name, dep_constraint in package_deps.items():
                self._resolve_dependency(
                    dep_name, dep_constraint, visited, in_stack.copy()
                )
                if dep_name in self.resolved:
                    resolved_dep.dependencies[dep_name] = self.resolved[dep_name]

        finally:
            in_stack.remove(name)

    def _select_version(
        self,
        available_versions: List[Version],
        constraint: VersionConstraint,
    ) -> Optional[Version]:
        """选择满足约束的最新版本

        Args:
            available_versions: 可用版本列表
            constraint: 版本约束

        Returns:
            选中的版本，如果没有满足约束的版本返回 None
        """
        # 按版本号降序排序
        sorted_versions = sorted(available_versions, reverse=True)

        for version in sorted_versions:
            if constraint.matches(version):
                return version

        return None

    def get_dependency_tree(self) -> Dict[str, any]:
        """获取依赖树（用于可视化）

        Returns:
            依赖树字典
        """
        tree = {}
        for name, dep in self.resolved.items():
            tree[name] = {
                "version": str(dep.version),
                "source": dep.source,
                "dependencies": list(dep.dependencies.keys()),
            }
        return tree

    def get_flat_list(self) -> List[Dict[str, any]]:
        """获取扁平依赖列表

        Returns:
            依赖列表
        """
        return [
            {
                "name": dep.name,
                "version": str(dep.version),
                "source": dep.source,
            }
            for dep in self.resolved.values()
        ]


class MockRepository:
    """模拟仓库（用于测试）"""

    def __init__(self, packages: Dict[str, Dict[str, Dict[str, str]]]):
        """初始化模拟仓库

        Args:
            packages: 包数据
            格式: {
                "包名": {
                    "版本号": {
                        "依赖名": "版本约束"
                    }
                }
            }
        """
        self.packages = packages

    def get_versions(self, name: str) -> List[Version]:
        """获取包的所有版本"""
        if name not in self.packages:
            return []
        return [Version.parse(v) for v in self.packages[name].keys()]

    def get_dependencies(self, name: str, version: Version) -> Dict[str, str]:
        """获取包的依赖"""
        if name not in self.packages:
            return {}
        version_str = str(version)
        if version_str not in self.packages[name]:
            return {}
        return self.packages[name][version_str]

    def get_source(self, name: str, version: Version) -> Optional[str]:
        """获取包来源"""
        return f"https://mock.registry/{name}/{version}"

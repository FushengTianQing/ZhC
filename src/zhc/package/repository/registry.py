#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仓库注册表

管理多个仓库，支持优先级和搜索
"""

from typing import Dict, List, Optional
from pathlib import Path
import json

from .base import PackageRepository, PackageMetadata, PackageSearchResult
from ..version import Version
from ..errors import PackageNotFoundError


class RepositoryRegistry:
    """仓库注册表

    管理多个仓库，支持：
    - 按优先级查询
    - 多仓库搜索
    - 仓库配置持久化
    """

    def __init__(self, config_path: Optional[Path] = None):
        """初始化仓库注册表

        Args:
            config_path: 配置文件路径（可选）
        """
        self._repositories: Dict[str, PackageRepository] = {}
        self._priorities: Dict[str, int] = {}  # 仓库名 -> 优先级（数字越小优先级越高）
        self._config_path = config_path

        if config_path and config_path.exists():
            self._load_config()

    def add_repository(
        self,
        name: str,
        repository: PackageRepository,
        priority: int = 100,
    ) -> None:
        """添加仓库

        Args:
            name: 仓库名称
            repository: 仓库实例
            priority: 优先级（数字越小优先级越高，默认 100）
        """
        self._repositories[name] = repository
        self._priorities[name] = priority

    def remove_repository(self, name: str) -> bool:
        """移除仓库

        Args:
            name: 仓库名称

        Returns:
            是否成功移除
        """
        if name in self._repositories:
            del self._repositories[name]
            del self._priorities[name]
            return True
        return False

    def get_repository(self, name: str) -> Optional[PackageRepository]:
        """获取仓库

        Args:
            name: 仓库名称

        Returns:
            仓库实例，不存在返回 None
        """
        return self._repositories.get(name)

    def list_repositories(self) -> List[str]:
        """列出所有仓库名称

        Returns:
            仓库名称列表（按优先级排序）
        """
        return sorted(
            self._repositories.keys(), key=lambda x: self._priorities.get(x, 100)
        )

    def get_versions(self, package_name: str) -> List[Version]:
        """从所有仓库获取包版本

        按优先级顺序查询仓库

        Args:
            package_name: 包名

        Returns:
            版本列表（合并去重）
        """
        all_versions: set = set()

        for name in self.list_repositories():
            repo = self._repositories[name]
            try:
                versions = repo.get_versions(package_name)
                all_versions.update(versions)
            except Exception:
                continue

        return sorted(all_versions, reverse=True)

    def get_metadata(self, package_name: str, version: Version) -> PackageMetadata:
        """获取包元数据

        按优先级顺序查询仓库

        Args:
            package_name: 包名
            version: 版本

        Returns:
            包元数据

        Raises:
            PackageNotFoundError: 包不存在
        """
        for name in self.list_repositories():
            repo = self._repositories[name]
            try:
                metadata = repo.get_metadata(package_name, version)
                if metadata:
                    return metadata
            except Exception:
                continue

        raise PackageNotFoundError(f"包 {package_name}@{version} 不存在")

    def get_dependencies(self, package_name: str, version: Version) -> Dict[str, str]:
        """获取包依赖

        Args:
            package_name: 包名
            version: 版本

        Returns:
            依赖字典
        """
        metadata = self.get_metadata(package_name, version)
        return metadata.dependencies

    def download(
        self,
        package_name: str,
        version: Version,
        target_path: Path,
        repository_name: Optional[str] = None,
    ) -> Path:
        """下载包

        Args:
            package_name: 包名
            version: 版本
            target_path: 目标路径
            repository_name: 指定仓库名称（可选）

        Returns:
            下载的文件路径

        Raises:
            PackageNotFoundError: 包不存在
        """
        if repository_name:
            repo = self._repositories.get(repository_name)
            if not repo:
                raise PackageNotFoundError(f"仓库 {repository_name} 不存在")
            return repo.download(package_name, version, target_path)

        # 按优先级尝试下载
        for name in self.list_repositories():
            repo = self._repositories[name]
            try:
                if repo.exists(package_name, version):
                    return repo.download(package_name, version, target_path)
            except Exception:
                continue

        raise PackageNotFoundError(f"包 {package_name}@{version} 不存在")

    def search(self, query: str) -> List[PackageSearchResult]:
        """搜索包

        从所有仓库搜索，合并结果

        Args:
            query: 搜索关键词

        Returns:
            搜索结果列表
        """
        all_results: Dict[str, PackageSearchResult] = {}

        for name in self.list_repositories():
            repo = self._repositories[name]
            try:
                results = repo.search(query)
                for result in results:
                    # 相同包名保留优先级高的仓库结果
                    if result.name not in all_results:
                        all_results[result.name] = result
            except Exception:
                continue

        return list(all_results.values())

    def exists(self, package_name: str, version: Optional[Version] = None) -> bool:
        """检查包是否存在

        Args:
            package_name: 包名
            version: 版本（可选）

        Returns:
            是否存在
        """
        for name in self.list_repositories():
            repo = self._repositories[name]
            try:
                if repo.exists(package_name, version):
                    return True
            except Exception:
                continue

        return False

    def save_config(self) -> None:
        """保存配置到文件"""
        if not self._config_path:
            return

        config = {
            "repositories": [
                {
                    "name": name,
                    "url": repo.url,
                    "priority": self._priorities.get(name, 100),
                }
                for name, repo in self._repositories.items()
            ]
        }

        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def _load_config(self) -> None:
        """从文件加载配置"""
        if not self._config_path or not self._config_path.exists():
            return

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            # 注意：这里只加载配置，不创建仓库实例
            # 仓库实例需要外部创建并添加
            self._loaded_config = config.get("repositories", [])
        except Exception:
            self._loaded_config = []

    def get_config(self) -> List[dict]:
        """获取配置列表

        Returns:
            仓库配置列表
        """
        return [
            {
                "name": name,
                "url": repo.url,
                "priority": self._priorities.get(name, 100),
            }
            for name, repo in self._repositories.items()
        ]

    def __len__(self) -> int:
        return len(self._repositories)

    def __contains__(self, name: str) -> bool:
        return name in self._repositories

    def __repr__(self) -> str:
        repos = ", ".join(self.list_repositories())
        return f"RepositoryRegistry({repos})"

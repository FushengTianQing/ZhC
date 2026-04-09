#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
包仓库基类

定义统一的仓库接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from ..version import Version


@dataclass
class PackageMetadata:
    """包元数据"""

    name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    dependencies: Dict[str, str] = None
    download_url: Optional[str] = None
    sha256: Optional[str] = None
    published_at: Optional[datetime] = None
    downloads: Optional[int] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = {}

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "homepage": self.homepage,
            "repository": self.repository,
            "dependencies": self.dependencies,
            "downloadUrl": self.download_url,
            "sha256": self.sha256,
            "publishedAt": self.published_at.isoformat() if self.published_at else None,
            "downloads": self.downloads,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PackageMetadata":
        """从字典创建"""
        published_at = data.get("publishedAt")
        if published_at and isinstance(published_at, str):
            published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))

        return cls(
            name=data["name"],
            version=data["version"],
            description=data.get("description"),
            author=data.get("author"),
            license=data.get("license"),
            homepage=data.get("homepage"),
            repository=data.get("repository"),
            dependencies=data.get("dependencies", {}),
            download_url=data.get("downloadUrl"),
            sha256=data.get("sha256"),
            published_at=published_at,
            downloads=data.get("downloads"),
        )


@dataclass
class PackageSearchResult:
    """包搜索结果"""

    name: str
    description: Optional[str]
    version: str
    author: Optional[str]
    downloads: Optional[int]


class PackageRepository(ABC):
    """包仓库基类"""

    def __init__(self, url: str):
        self.url = url
        self.name = self._extract_name(url)

    @abstractmethod
    def get_versions(self, package_name: str) -> List[Version]:
        """获取包的所有可用版本

        Args:
            package_name: 包名

        Returns:
            版本列表（降序排列）
        """
        pass

    @abstractmethod
    def get_metadata(
        self, package_name: str, version: Version
    ) -> Optional[PackageMetadata]:
        """获取包元数据

        Args:
            package_name: 包名
            version: 版本

        Returns:
            包元数据，不存在返回 None
        """
        pass

    @abstractmethod
    def get_dependencies(self, package_name: str, version: Version) -> Dict[str, str]:
        """获取包依赖

        Args:
            package_name: 包名
            version: 版本

        Returns:
            依赖字典 {包名: 版本约束}
        """
        pass

    @abstractmethod
    def download(self, package_name: str, version: Version, target_path: Path) -> Path:
        """下载包到目标路径

        Args:
            package_name: 包名
            version: 版本
            target_path: 目标路径

        Returns:
            下载的文件路径
        """
        pass

    @abstractmethod
    def search(self, query: str) -> List[PackageSearchResult]:
        """搜索包

        Args:
            query: 搜索关键词

        Returns:
            搜索结果列表
        """
        pass

    @abstractmethod
    def exists(self, package_name: str, version: Optional[Version] = None) -> bool:
        """检查包是否存在

        Args:
            package_name: 包名
            version: 版本（可选）

        Returns:
            是否存在
        """
        pass

    def get_source(self, package_name: str, version: Version) -> str:
        """获取包来源

        Args:
            package_name: 包名
            version: 版本

        Returns:
            来源 URL
        """
        return self.url

    def _extract_name(self, url: str) -> str:
        """从 URL 提取仓库名称

        Args:
            url: URL

        Returns:
            仓库名称
        """
        if "://" in url:
            return url.split("://")[1].split("/")[0]
        return url.split("/")[0]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

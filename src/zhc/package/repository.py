#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
包仓库接口

定义包仓库的抽象接口和默认实现
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass
import json

from .version import Version


@dataclass
class PackageMetadata:
    """包元数据"""

    name: str
    version: Version
    description: str = ""
    author: str = ""
    license: str = "MIT"
    dependencies: Dict[str, str] = None
    source_url: str = ""
    download_url: str = ""
    checksum: str = ""

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = {}

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "version": str(self.version),
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "dependencies": self.dependencies,
            "source_url": self.source_url,
            "download_url": self.download_url,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PackageMetadata":
        """从字典创建"""
        return cls(
            name=data["name"],
            version=Version.parse(data["version"]),
            description=data.get("description", ""),
            author=data.get("author", ""),
            license=data.get("license", "MIT"),
            dependencies=data.get("dependencies", {}),
            source_url=data.get("source_url", ""),
            download_url=data.get("download_url", ""),
            checksum=data.get("checksum", ""),
        )


class PackageRepository(ABC):
    """包仓库抽象接口"""

    @abstractmethod
    def get_versions(self, name: str) -> List[Version]:
        """获取包的所有可用版本

        Args:
            name: 包名

        Returns:
            版本列表
        """
        pass

    @abstractmethod
    def get_dependencies(self, name: str, version: Version) -> Dict[str, str]:
        """获取包的依赖

        Args:
            name: 包名
            version: 版本

        Returns:
            依赖字典 {包名: 版本约束}
        """
        pass

    @abstractmethod
    def get_source(self, name: str, version: Version) -> Optional[str]:
        """获取包来源

        Args:
            name: 包名
            version: 版本

        Returns:
            来源 URL 或 None
        """
        pass

    @abstractmethod
    def download(self, name: str, version: Version, target_dir: Path) -> bool:
        """下载包到指定目录

        Args:
            name: 包名
            version: 版本
            target_dir: 目标目录

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    def get_metadata(self, name: str, version: Version) -> Optional[PackageMetadata]:
        """获取包元数据

        Args:
            name: 包名
            version: 版本

        Returns:
            包元数据，如果不存在返回 None
        """
        pass


class DefaultRepository(PackageRepository):
    """默认仓库实现

    从远程仓库获取包信息
    """

    def __init__(self, registry_url: str = "https://registry.zhc-lang.org"):
        """初始化默认仓库

        Args:
            registry_url: 仓库 URL
        """
        self.registry_url = registry_url
        self._cache: Dict[str, List[Version]] = {}
        self._metadata_cache: Dict[str, PackageMetadata] = {}

    def get_versions(self, name: str) -> List[Version]:
        """获取包的所有可用版本"""
        # 检查缓存
        if name in self._cache:
            return self._cache[name]

        # 从远程仓库获取（模拟）
        # 实际应该调用远程 API
        versions = self._fetch_versions_from_remote(name)
        self._cache[name] = versions
        return versions

    def get_dependencies(self, name: str, version: Version) -> Dict[str, str]:
        """获取包的依赖"""
        metadata = self.get_metadata(name, version)
        if metadata:
            return metadata.dependencies
        return {}

    def get_source(self, name: str, version: Version) -> Optional[str]:
        """获取包来源"""
        metadata = self.get_metadata(name, version)
        if metadata:
            return metadata.source_url
        return f"{self.registry_url}/{name}/{version}"

    def download(self, name: str, version: Version, target_dir: Path) -> bool:
        """下载包到指定目录"""
        try:
            # 实际应该从远程下载
            # 这里模拟下载过程
            target_dir.mkdir(parents=True, exist_ok=True)

            # 创建 package.json
            metadata = self.get_metadata(name, version)
            if metadata:
                pkg_json = target_dir / "package.json"
                with open(pkg_json, "w", encoding="utf-8") as f:
                    json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)

            return True
        except Exception:
            return False

    def get_metadata(self, name: str, version: Version) -> Optional[PackageMetadata]:
        """获取包元数据"""
        cache_key = f"{name}@{version}"
        if cache_key in self._metadata_cache:
            return self._metadata_cache[cache_key]

        # 从远程仓库获取（模拟）
        metadata = self._fetch_metadata_from_remote(name, version)
        if metadata:
            self._metadata_cache[cache_key] = metadata
        return metadata

    def _fetch_versions_from_remote(self, name: str) -> List[Version]:
        """从远程仓库获取版本列表（模拟）"""
        # 实际应该调用远程 API
        # 这里返回空列表
        return []

    def _fetch_metadata_from_remote(
        self, name: str, version: Version
    ) -> Optional[PackageMetadata]:
        """从远程仓库获取元数据（模拟）"""
        # 实际应该调用远程 API
        return None


class LocalRepository(PackageRepository):
    """本地仓库

    从本地目录读取包信息
    """

    def __init__(self, local_path: Path):
        """初始化本地仓库

        Args:
            local_path: 本地仓库路径
        """
        self.local_path = local_path
        self._cache: Dict[str, List[Version]] = {}

    def get_versions(self, name: str) -> List[Version]:
        """获取包的所有可用版本"""
        if name in self._cache:
            return self._cache[name]

        pkg_dir = self.local_path / name
        if not pkg_dir.exists():
            return []

        versions = []
        for version_dir in pkg_dir.iterdir():
            if version_dir.is_dir():
                try:
                    version = Version.parse(version_dir.name)
                    versions.append(version)
                except Exception:
                    continue

        self._cache[name] = versions
        return versions

    def get_dependencies(self, name: str, version: Version) -> Dict[str, str]:
        """获取包的依赖"""
        metadata = self.get_metadata(name, version)
        if metadata:
            return metadata.dependencies
        return {}

    def get_source(self, name: str, version: Version) -> Optional[str]:
        """获取包来源"""
        pkg_dir = self.local_path / name / str(version)
        if pkg_dir.exists():
            return f"file://{pkg_dir}"
        return None

    def download(self, name: str, version: Version, target_dir: Path) -> bool:
        """下载包到指定目录（从本地复制）"""
        import shutil

        source_dir = self.local_path / name / str(version)
        if not source_dir.exists():
            return False

        try:
            shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
            return True
        except Exception:
            return False

    def get_metadata(self, name: str, version: Version) -> Optional[PackageMetadata]:
        """获取包元数据"""
        pkg_dir = self.local_path / name / str(version)
        pkg_json = pkg_dir / "package.json"

        if not pkg_json.exists():
            return None

        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            return PackageMetadata.from_dict(data)
        except Exception:
            return None

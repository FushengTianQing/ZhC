#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
包索引管理

管理包的元数据索引
"""

from typing import Dict, List, Optional
from pathlib import Path
import json
from dataclasses import dataclass, field

from .base import PackageSearchResult
from ..version import Version


@dataclass
class IndexEntry:
    """索引条目"""

    name: str
    versions: Dict[str, dict] = field(default_factory=dict)

    def add_version(self, version: str, metadata: dict) -> None:
        """添加版本

        Args:
            version: 版本字符串
            metadata: 元数据
        """
        self.versions[version] = metadata

    def remove_version(self, version: str) -> bool:
        """移除版本

        Args:
            version: 版本字符串

        Returns:
            是否成功移除
        """
        if version in self.versions:
            del self.versions[version]
            return True
        return False

    def get_latest_version(self) -> Optional[str]:
        """获取最新版本

        Returns:
            最新版本字符串
        """
        if not self.versions:
            return None

        try:
            versions = [Version.parse(v) for v in self.versions.keys()]
            return str(max(versions))
        except Exception:
            return max(self.versions.keys()) if self.versions else None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "versions": self.versions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "IndexEntry":
        """从字典创建"""
        entry = cls(name=data["name"])
        entry.versions = data.get("versions", {})
        return entry


class PackageIndex:
    """包索引

    管理包的元数据索引
    """

    def __init__(self, index_path: Optional[Path] = None):
        """初始化包索引

        Args:
            index_path: 索引文件路径（可选）
        """
        self._index: Dict[str, IndexEntry] = {}
        self._index_path = index_path

        if index_path and index_path.exists():
            self._load_index()

    def add_package(self, name: str, version: str, metadata: dict) -> None:
        """添加包

        Args:
            name: 包名
            version: 版本
            metadata: 元数据
        """
        if name not in self._index:
            self._index[name] = IndexEntry(name=name)

        self._index[name].add_version(version, metadata)

    def remove_package(self, name: str, version: Optional[str] = None) -> bool:
        """移除包

        Args:
            name: 包名
            version: 版本（可选，不指定则移除整个包）

        Returns:
            是否成功移除
        """
        if name not in self._index:
            return False

        if version:
            return self._index[name].remove_version(version)
        else:
            del self._index[name]
            return True

    def get_package(self, name: str) -> Optional[IndexEntry]:
        """获取包索引条目

        Args:
            name: 包名

        Returns:
            索引条目，不存在返回 None
        """
        return self._index.get(name)

    def get_versions(self, name: str) -> List[str]:
        """获取包的所有版本

        Args:
            name: 包名

        Returns:
            版本列表
        """
        entry = self._index.get(name)
        if not entry:
            return []

        try:
            versions = [Version.parse(v) for v in entry.versions.keys()]
            return [str(v) for v in sorted(versions, reverse=True)]
        except Exception:
            return sorted(entry.versions.keys(), reverse=True)

    def get_metadata(self, name: str, version: str) -> Optional[dict]:
        """获取包元数据

        Args:
            name: 包名
            version: 版本

        Returns:
            元数据字典
        """
        entry = self._index.get(name)
        if not entry:
            return None

        return entry.versions.get(version)

    def get_latest_version(self, name: str) -> Optional[str]:
        """获取包的最新版本

        Args:
            name: 包名

        Returns:
            最新版本字符串
        """
        entry = self._index.get(name)
        if not entry:
            return None

        return entry.get_latest_version()

    def search(self, query: str) -> List[PackageSearchResult]:
        """搜索包

        Args:
            query: 搜索关键词

        Returns:
            搜索结果列表
        """
        results = []
        query_lower = query.lower()

        for name, entry in self._index.items():
            # 检查名称匹配
            if query_lower not in name.lower():
                continue

            # 获取最新版本信息
            latest_version = entry.get_latest_version()
            if not latest_version:
                continue

            version_data = entry.versions.get(latest_version, {})

            results.append(
                PackageSearchResult(
                    name=name,
                    description=version_data.get("description"),
                    version=latest_version,
                    author=version_data.get("author"),
                    downloads=version_data.get("downloads"),
                )
            )

        return results

    def exists(self, name: str, version: Optional[str] = None) -> bool:
        """检查包是否存在

        Args:
            name: 包名
            version: 版本（可选）

        Returns:
            是否存在
        """
        if name not in self._index:
            return False

        if version:
            return version in self._index[name].versions

        return True

    def list_packages(self) -> List[str]:
        """列出所有包名

        Returns:
            包名列表
        """
        return sorted(self._index.keys())

    def save(self) -> None:
        """保存索引到文件"""
        if not self._index_path:
            return

        data = {
            "packages": {name: entry.to_dict() for name, entry in self._index.items()}
        }

        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_index(self) -> None:
        """从文件加载索引"""
        if not self._index_path or not self._index_path.exists():
            return

        try:
            with open(self._index_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for name, entry_data in data.get("packages", {}).items():
                self._index[name] = IndexEntry.from_dict(entry_data)
        except Exception:
            pass

    def __len__(self) -> int:
        return len(self._index)

    def __contains__(self, name: str) -> bool:
        return name in self._index

    def __repr__(self) -> str:
        return f"PackageIndex({len(self)} packages)"

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地仓库实现

从文件系统加载包
"""

from typing import Dict, List, Optional
from pathlib import Path
import json
import zipfile
import shutil
from datetime import datetime

from .base import PackageRepository, PackageMetadata, PackageSearchResult
from ..version import Version
from ..errors import PackageNotFoundError, NetworkError


class LocalRepository(PackageRepository):
    """本地仓库"""

    def __init__(self, path: Path):
        """初始化本地仓库

        Args:
            path: 本地仓库路径
        """
        super().__init__(str(path))
        self.path = Path(path)
        self.index_path = self.path / "index.json"
        self.packages_dir = self.path / "packages"

        # 加载索引
        self._index = self._load_index()

    def _load_index(self) -> Dict:
        """加载包索引"""
        if self.index_path.exists():
            with open(self.index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"packages": {}}

    def _save_index(self) -> None:
        """保存包索引"""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2, ensure_ascii=False)

    def get_versions(self, package_name: str) -> List[Version]:
        """获取包的所有版本"""
        packages = self._index.get("packages", {})
        package_data = packages.get(package_name, {})
        versions = package_data.get("versions", {})

        return sorted([Version.parse(v) for v in versions.keys()], reverse=True)

    def get_metadata(
        self, package_name: str, version: Version
    ) -> Optional[PackageMetadata]:
        """获取包元数据"""
        packages = self._index.get("packages", {})
        package_data = packages.get(package_name, {})
        version_data = package_data.get("versions", {}).get(str(version))

        if not version_data:
            return None

        return PackageMetadata(
            name=package_name,
            version=str(version),
            description=version_data.get("description"),
            author=version_data.get("author"),
            license=version_data.get("license"),
            homepage=version_data.get("homepage"),
            repository=version_data.get("repository"),
            dependencies=version_data.get("dependencies", {}),
            download_url=version_data.get("downloadUrl"),
            sha256=version_data.get("sha256"),
            published_at=version_data.get("publishedAt"),
            downloads=version_data.get("downloads"),
        )

    def get_dependencies(self, package_name: str, version: Version) -> Dict[str, str]:
        """获取包依赖"""
        metadata = self.get_metadata(package_name, version)
        if not metadata:
            return {}
        return metadata.dependencies

    def download(self, package_name: str, version: Version, target_path: Path) -> Path:
        """下载包到目标路径"""
        package_dir = self.packages_dir / package_name / str(version)
        archive_path = package_dir / f"{package_name}-{version}.zip"

        if not archive_path.exists():
            raise PackageNotFoundError(f"包文件 {package_name} {version} 不存在")

        target_path.mkdir(parents=True, exist_ok=True)

        # 解压到目标路径
        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(target_path)
        except zipfile.BadZipFile:
            raise NetworkError(f"包文件 {package_name} {version} 损坏")

        return target_path

    def search(self, query: str) -> List[PackageSearchResult]:
        """搜索包"""
        results = []
        packages = self._index.get("packages", {})

        query_lower = query.lower()

        for name, package_data in packages.items():
            # 检查名称匹配
            if query_lower not in name.lower():
                continue

            # 获取最新版本信息
            versions = package_data.get("versions", {})
            if not versions:
                continue

            try:
                latest_version = str(max([Version.parse(v) for v in versions.keys()]))
            except Exception:
                latest_version = max(versions.keys())

            version_data = versions[latest_version]

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

    def exists(self, package_name: str, version: Optional[Version] = None) -> bool:
        """检查包是否存在"""
        packages = self._index.get("packages", {})

        if package_name not in packages:
            return False

        if version is None:
            return True

        package_versions = packages[package_name].get("versions", {})
        return str(version) in package_versions

    def register_package(
        self,
        package_name: str,
        version: Version,
        metadata: dict,
        archive_path: Path,
    ) -> None:
        """注册包

        Args:
            package_name: 包名
            version: 版本
            metadata: 元数据
            archive_path: 包文件路径
        """
        if "packages" not in self._index:
            self._index["packages"] = {}

        if package_name not in self._index["packages"]:
            self._index["packages"][package_name] = {"versions": {}}

        self._index["packages"][package_name]["versions"][str(version)] = {
            "description": metadata.get("description", ""),
            "author": metadata.get("author", ""),
            "license": metadata.get("license", "MIT"),
            "homepage": metadata.get("homepage", ""),
            "repository": metadata.get("repository", ""),
            "dependencies": metadata.get("dependencies", {}),
            "downloadUrl": f"{self.packages_dir}/{package_name}/{version}/{package_name}-{version}.zip",
            "sha256": metadata.get("sha256", ""),
            "publishedAt": datetime.now().isoformat(),
            "downloads": 0,
        }

        # 复制包文件到仓库
        package_dir = self.packages_dir / package_name / str(version)
        package_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(archive_path, package_dir / f"{package_name}-{version}.zip")

        self._save_index()

    def get_source(self, package_name: str, version: Version) -> str:
        """获取包来源"""
        return f"file://{self.path / package_name / str(version)}"

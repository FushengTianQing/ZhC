#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
远程仓库实现

通过 HTTP/HTTPS 访问远程仓库
"""

from typing import Dict, List, Optional
from pathlib import Path
import hashlib

from .base import PackageRepository, PackageMetadata, PackageSearchResult
from ..version import Version
from ..errors import NetworkError, PackageNotFoundError

# requests 是可选依赖
try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class RemoteRepository(PackageRepository):
    """远程仓库"""

    def __init__(
        self,
        url: str,
        auth_token: Optional[str] = None,
        timeout: int = 30,
    ):
        """初始化远程仓库

        Args:
            url: 仓库 URL
            auth_token: 认证 Token（可选）
            timeout: 超时时间（秒）
        """
        super().__init__(url)
        self.auth_token = auth_token
        self.timeout = timeout
        self.session = self._create_session() if REQUESTS_AVAILABLE else None

    def _create_session(self):
        """创建 HTTP 会话"""
        if not REQUESTS_AVAILABLE:
            raise NetworkError("requests 库未安装，请运行 pip install requests")

        session = requests.Session()
        session.timeout = self.timeout

        if self.auth_token:
            session.headers["Authorization"] = f"Bearer {self.auth_token}"

        session.headers["User-Agent"] = "ZHC-Package-Manager/1.0"
        return session

    def get_versions(self, package_name: str) -> List[Version]:
        """获取包的所有可用版本"""
        if not self.session:
            raise NetworkError("HTTP 会话未初始化")

        try:
            response = self.session.get(f"{self.url}/packages/{package_name}")
            response.raise_for_status()
            data = response.json()

            versions = [Version.parse(v) for v in data.get("versions", [])]
            return sorted(versions, reverse=True)

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return []
            raise NetworkError(f"获取版本失败: {e}", url=self.url)
        except requests.RequestException as e:
            raise NetworkError(f"网络请求失败: {e}", url=self.url)

    def get_metadata(
        self, package_name: str, version: Version
    ) -> Optional[PackageMetadata]:
        """获取包元数据"""
        if not self.session:
            raise NetworkError("HTTP 会话未初始化")

        try:
            response = self.session.get(f"{self.url}/packages/{package_name}/{version}")
            response.raise_for_status()
            data = response.json()

            return PackageMetadata(
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
                published_at=data.get("publishedAt"),
                downloads=data.get("downloads"),
            )

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise NetworkError(f"获取元数据失败: {e}", url=self.url)
        except requests.RequestException as e:
            raise NetworkError(f"网络请求失败: {e}", url=self.url)

    def get_dependencies(self, package_name: str, version: Version) -> Dict[str, str]:
        """获取包依赖"""
        metadata = self.get_metadata(package_name, version)
        if not metadata:
            return {}
        return metadata.dependencies

    def download(self, package_name: str, version: Version, target_path: Path) -> Path:
        """下载包到目标路径"""
        if not self.session:
            raise NetworkError("HTTP 会话未初始化")

        metadata = self.get_metadata(package_name, version)

        if not metadata:
            raise PackageNotFoundError(f"包 {package_name} {version} 不存在")

        if not metadata.download_url:
            raise NetworkError(
                f"包 {package_name} {version} 没有下载链接", url=self.url
            )

        target_path.mkdir(parents=True, exist_ok=True)
        target_file = target_path / f"{package_name}-{version}.zip"

        try:
            response = self.session.get(metadata.download_url, stream=True)
            response.raise_for_status()

            with open(target_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # 验证哈希
            if metadata.sha256:
                self._verify_hash(target_file, metadata.sha256)

            return target_file

        except requests.HTTPError as e:
            raise NetworkError(f"下载失败: {e}", url=metadata.download_url)
        except requests.RequestException as e:
            raise NetworkError(f"网络请求失败: {e}", url=metadata.download_url)

    def _verify_hash(self, file_path: Path, expected_hash: str) -> None:
        """验证文件哈希"""
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)

        actual_hash = sha256.hexdigest()

        if actual_hash != expected_hash:
            raise NetworkError(
                f"文件哈希验证失败: 期望 {expected_hash[:8]}..., 实际 {actual_hash[:8]}..."
            )

    def search(self, query: str) -> List[PackageSearchResult]:
        """搜索包"""
        if not self.session:
            raise NetworkError("HTTP 会话未初始化")

        try:
            response = self.session.get(f"{self.url}/search", params={"q": query})
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append(
                    PackageSearchResult(
                        name=item["name"],
                        description=item.get("description"),
                        version=item["version"],
                        author=item.get("author"),
                        downloads=item.get("downloads"),
                    )
                )

            return results

        except requests.HTTPError as e:
            raise NetworkError(f"搜索失败: {e}", url=self.url)
        except requests.RequestException as e:
            raise NetworkError(f"网络请求失败: {e}", url=self.url)

    def exists(self, package_name: str, version: Optional[Version] = None) -> bool:
        """检查包是否存在"""
        try:
            if version is None:
                response = self.session.get(f"{self.url}/packages/{package_name}")
                return response.status_code == 200
            else:
                metadata = self.get_metadata(package_name, version)
                return metadata is not None
        except (PackageNotFoundError, NetworkError):
            return False

    def set_auth_token(self, token: str) -> None:
        """设置认证 Token

        Args:
            token: 认证 Token
        """
        self.auth_token = token
        if self.session:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def get_source(self, package_name: str, version: Version) -> str:
        """获取包来源"""
        return f"{self.url}/packages/{package_name}/{version}"

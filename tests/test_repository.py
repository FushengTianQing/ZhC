#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
包仓库模块测试
"""

import tempfile
from pathlib import Path

from zhc.package.repository import (
    PackageMetadata,
    PackageSearchResult,
    RepositoryRegistry,
    AuthManager,
    AuthConfig,
    AuthType,
    PackageIndex,
    IndexEntry,
    LocalRepository,
)
from zhc.package.version import Version


class TestPackageMetadata:
    """PackageMetadata 测试"""

    def test_create_metadata(self):
        """测试创建元数据"""
        metadata = PackageMetadata(
            name="test-package",
            version="1.0.0",
            description="测试包",
            author="Test Author",
        )

        assert metadata.name == "test-package"
        assert metadata.version == "1.0.0"
        assert metadata.description == "测试包"
        assert metadata.author == "Test Author"
        assert metadata.dependencies == {}

    def test_metadata_to_dict(self):
        """测试转换为字典"""
        metadata = PackageMetadata(
            name="test-package",
            version="1.0.0",
            description="测试包",
        )

        data = metadata.to_dict()
        assert data["name"] == "test-package"
        assert data["version"] == "1.0.0"
        assert data["description"] == "测试包"

    def test_metadata_from_dict(self):
        """测试从字典创建"""
        data = {
            "name": "test-package",
            "version": "1.0.0",
            "description": "测试包",
            "author": "Test Author",
        }

        metadata = PackageMetadata.from_dict(data)
        assert metadata.name == "test-package"
        assert metadata.version == "1.0.0"
        assert metadata.description == "测试包"
        assert metadata.author == "Test Author"


class TestPackageSearchResult:
    """PackageSearchResult 测试"""

    def test_create_search_result(self):
        """测试创建搜索结果"""
        result = PackageSearchResult(
            name="test-package",
            description="测试包",
            version="1.0.0",
            author="Test Author",
            downloads=1000,
        )

        assert result.name == "test-package"
        assert result.description == "测试包"
        assert result.version == "1.0.0"
        assert result.author == "Test Author"
        assert result.downloads == 1000


class TestRepositoryRegistry:
    """RepositoryRegistry 测试"""

    def test_create_registry(self):
        """测试创建注册表"""
        registry = RepositoryRegistry()
        assert len(registry) == 0

    def test_add_repository(self):
        """测试添加仓库"""
        registry = RepositoryRegistry()
        repo = LocalRepository(Path("/tmp/test-repo"))
        registry.add_repository("test", repo)

        assert "test" in registry
        assert len(registry) == 1

    def test_remove_repository(self):
        """测试移除仓库"""
        registry = RepositoryRegistry()
        repo = LocalRepository(Path("/tmp/test-repo"))
        registry.add_repository("test", repo)

        assert registry.remove_repository("test") is True
        assert "test" not in registry
        assert len(registry) == 0

    def test_list_repositories(self):
        """测试列出仓库"""
        registry = RepositoryRegistry()
        repo1 = LocalRepository(Path("/tmp/test-repo1"))
        repo2 = LocalRepository(Path("/tmp/test-repo2"))

        registry.add_repository("repo1", repo1, priority=10)
        registry.add_repository("repo2", repo2, priority=5)

        repos = registry.list_repositories()
        assert repos == ["repo2", "repo1"]  # 按优先级排序

    def test_get_repository(self):
        """测试获取仓库"""
        registry = RepositoryRegistry()
        repo = LocalRepository(Path("/tmp/test-repo"))
        registry.add_repository("test", repo)

        retrieved = registry.get_repository("test")
        assert retrieved is repo


class TestAuthManager:
    """AuthManager 测试"""

    def test_create_auth_manager(self):
        """测试创建认证管理器"""
        manager = AuthManager()
        assert len(manager) == 0

    def test_set_token_auth(self):
        """测试设置 Token 认证"""
        manager = AuthManager()
        manager.set_token_auth("test-repo", "test-token")

        assert manager.has_auth("test-repo")
        auth_config = manager.get_auth("test-repo")
        assert auth_config.auth_type == AuthType.TOKEN
        assert auth_config.credentials["token"] == "test-token"

    def test_set_basic_auth(self):
        """测试设置 Basic 认证"""
        manager = AuthManager()
        manager.set_basic_auth("test-repo", "user", "pass")

        assert manager.has_auth("test-repo")
        auth_config = manager.get_auth("test-repo")
        assert auth_config.auth_type == AuthType.BASIC
        assert auth_config.credentials["username"] == "user"
        assert auth_config.credentials["password"] == "pass"

    def test_set_api_key_auth(self):
        """测试设置 API Key 认证"""
        manager = AuthManager()
        manager.set_api_key_auth("test-repo", "api-key-123")

        assert manager.has_auth("test-repo")
        auth_config = manager.get_auth("test-repo")
        assert auth_config.auth_type == AuthType.API_KEY
        assert auth_config.credentials["api_key"] == "api-key-123"

    def test_remove_auth(self):
        """测试移除认证"""
        manager = AuthManager()
        manager.set_token_auth("test-repo", "test-token")

        assert manager.remove_auth("test-repo") is True
        assert not manager.has_auth("test-repo")

    def test_get_auth_header_token(self):
        """测试获取 Token 认证头"""
        manager = AuthManager()
        manager.set_token_auth("test-repo", "test-token")

        header = manager.get_auth_header("test-repo")
        assert header == {"Authorization": "Bearer test-token"}

    def test_get_auth_header_basic(self):
        """测试获取 Basic 认证头"""
        manager = AuthManager()
        manager.set_basic_auth("test-repo", "user", "pass")

        header = manager.get_auth_header("test-repo")
        assert "Authorization" in header
        assert header["Authorization"].startswith("Basic ")


class TestPackageIndex:
    """PackageIndex 测试"""

    def test_create_index(self):
        """测试创建索引"""
        index = PackageIndex()
        assert len(index) == 0

    def test_add_package(self):
        """测试添加包"""
        index = PackageIndex()
        index.add_package("test-package", "1.0.0", {"description": "测试包"})

        assert "test-package" in index
        assert index.exists("test-package")
        assert index.exists("test-package", "1.0.0")

    def test_remove_package(self):
        """测试移除包"""
        index = PackageIndex()
        index.add_package("test-package", "1.0.0", {"description": "测试包"})

        assert index.remove_package("test-package") is True
        assert not index.exists("test-package")

    def test_remove_version(self):
        """测试移除版本"""
        index = PackageIndex()
        index.add_package("test-package", "1.0.0", {"description": "测试包"})
        index.add_package("test-package", "2.0.0", {"description": "测试包 v2"})

        assert index.remove_package("test-package", "1.0.0") is True
        assert not index.exists("test-package", "1.0.0")
        assert index.exists("test-package", "2.0.0")

    def test_get_versions(self):
        """测试获取版本列表"""
        index = PackageIndex()
        index.add_package("test-package", "1.0.0", {})
        index.add_package("test-package", "2.0.0", {})
        index.add_package("test-package", "1.5.0", {})

        versions = index.get_versions("test-package")
        assert versions == ["2.0.0", "1.5.0", "1.0.0"]

    def test_get_metadata(self):
        """测试获取元数据"""
        index = PackageIndex()
        metadata = {"description": "测试包", "author": "Test"}
        index.add_package("test-package", "1.0.0", metadata)

        result = index.get_metadata("test-package", "1.0.0")
        assert result == metadata

    def test_get_latest_version(self):
        """测试获取最新版本"""
        index = PackageIndex()
        index.add_package("test-package", "1.0.0", {})
        index.add_package("test-package", "2.0.0", {})
        index.add_package("test-package", "1.5.0", {})

        latest = index.get_latest_version("test-package")
        assert latest == "2.0.0"

    def test_search(self):
        """测试搜索包"""
        index = PackageIndex()
        index.add_package("network-lib", "1.0.0", {"description": "网络库"})
        index.add_package("network-tools", "2.0.0", {"description": "网络工具"})
        index.add_package("math-lib", "1.0.0", {"description": "数学库"})

        results = index.search("network")
        assert len(results) == 2
        assert any(r.name == "network-lib" for r in results)
        assert any(r.name == "network-tools" for r in results)

    def test_list_packages(self):
        """测试列出所有包"""
        index = PackageIndex()
        index.add_package("pkg-a", "1.0.0", {})
        index.add_package("pkg-b", "1.0.0", {})
        index.add_package("pkg-c", "1.0.0", {})

        packages = index.list_packages()
        assert packages == ["pkg-a", "pkg-b", "pkg-c"]


class TestLocalRepository:
    """LocalRepository 测试"""

    def test_create_local_repository(self):
        """测试创建本地仓库"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = LocalRepository(Path(tmp_dir))
            assert repo.url == tmp_dir
            # name 是从 URL 提取的，对于本地路径可能是路径的一部分
            assert isinstance(repo.name, str)

    def test_get_versions_empty(self, tmp_path):
        """测试获取空仓库的版本"""
        repo = LocalRepository(tmp_path)
        versions = repo.get_versions("non-existent")
        assert versions == []

    def test_register_and_get_versions(self, tmp_path):
        """测试注册包并获取版本"""
        repo = LocalRepository(tmp_path)

        # 创建一个假的包文件
        archive_path = tmp_path / "test-1.0.0.zip"
        archive_path.write_bytes(b"fake zip content")

        repo.register_package(
            "test-package",
            Version.parse("1.0.0"),
            {"description": "测试包", "author": "Test"},
            archive_path,
        )

        versions = repo.get_versions("test-package")
        assert len(versions) == 1
        assert versions[0] == Version.parse("1.0.0")

    def test_exists(self, tmp_path):
        """测试检查包是否存在"""
        repo = LocalRepository(tmp_path)

        # 创建一个假的包文件
        archive_path = tmp_path / "test-1.0.0.zip"
        archive_path.write_bytes(b"fake zip content")

        repo.register_package(
            "test-package",
            Version.parse("1.0.0"),
            {},
            archive_path,
        )

        assert repo.exists("test-package") is True
        assert repo.exists("test-package", Version.parse("1.0.0")) is True
        assert repo.exists("non-existent") is False

    def test_search(self, tmp_path):
        """测试搜索包"""
        repo = LocalRepository(tmp_path)

        # 创建包
        archive_path = tmp_path / "network-lib-1.0.0.zip"
        archive_path.write_bytes(b"fake zip content")

        repo.register_package(
            "network-lib",
            Version.parse("1.0.0"),
            {"description": "网络库"},
            archive_path,
        )

        results = repo.search("network")
        assert len(results) == 1
        assert results[0].name == "network-lib"

    def test_get_metadata(self, tmp_path):
        """测试获取元数据"""
        repo = LocalRepository(tmp_path)

        archive_path = tmp_path / "test-1.0.0.zip"
        archive_path.write_bytes(b"fake zip content")

        repo.register_package(
            "test-package",
            Version.parse("1.0.0"),
            {"description": "测试包", "author": "Test"},
            archive_path,
        )

        metadata = repo.get_metadata("test-package", Version.parse("1.0.0"))
        assert metadata is not None
        assert metadata.name == "test-package"
        assert metadata.description == "测试包"
        assert metadata.author == "Test"


class TestIndexEntry:
    """IndexEntry 测试"""

    def test_create_entry(self):
        """测试创建索引条目"""
        entry = IndexEntry(name="test-package")
        assert entry.name == "test-package"
        assert entry.versions == {}

    def test_add_version(self):
        """测试添加版本"""
        entry = IndexEntry(name="test-package")
        entry.add_version("1.0.0", {"description": "v1"})

        assert "1.0.0" in entry.versions
        assert entry.versions["1.0.0"]["description"] == "v1"

    def test_remove_version(self):
        """测试移除版本"""
        entry = IndexEntry(name="test-package")
        entry.add_version("1.0.0", {})
        entry.add_version("2.0.0", {})

        assert entry.remove_version("1.0.0") is True
        assert "1.0.0" not in entry.versions
        assert "2.0.0" in entry.versions

    def test_get_latest_version(self):
        """测试获取最新版本"""
        entry = IndexEntry(name="test-package")
        entry.add_version("1.0.0", {})
        entry.add_version("2.0.0", {})
        entry.add_version("1.5.0", {})

        latest = entry.get_latest_version()
        assert latest == "2.0.0"

    def test_to_dict(self):
        """测试转换为字典"""
        entry = IndexEntry(name="test-package")
        entry.add_version("1.0.0", {"description": "v1"})

        data = entry.to_dict()
        assert data["name"] == "test-package"
        assert "1.0.0" in data["versions"]

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "name": "test-package",
            "versions": {
                "1.0.0": {"description": "v1"},
                "2.0.0": {"description": "v2"},
            },
        }

        entry = IndexEntry.from_dict(data)
        assert entry.name == "test-package"
        assert "1.0.0" in entry.versions
        assert "2.0.0" in entry.versions


class TestAuthConfig:
    """AuthConfig 测试"""

    def test_token_auth_header(self):
        """测试 Token 认证头"""
        config = AuthConfig(
            auth_type=AuthType.TOKEN,
            credentials={"token": "test-token"},
        )

        header = config.get_auth_header()
        assert header == {"Authorization": "Bearer test-token"}

    def test_basic_auth_header(self):
        """测试 Basic 认证头"""
        config = AuthConfig(
            auth_type=AuthType.BASIC,
            credentials={"username": "user", "password": "pass"},
        )

        header = config.get_auth_header()
        assert "Authorization" in header
        assert header["Authorization"].startswith("Basic ")

    def test_api_key_auth_header(self):
        """测试 API Key 认证头"""
        config = AuthConfig(
            auth_type=AuthType.API_KEY,
            credentials={"api_key": "key123", "key_name": "X-API-Key"},
        )

        header = config.get_auth_header()
        assert header == {"X-API-Key": "key123"}

    def test_none_auth_header(self):
        """测试无认证头"""
        config = AuthConfig(
            auth_type=AuthType.NONE,
            credentials={},
        )

        header = config.get_auth_header()
        assert header is None

    def test_is_valid(self):
        """测试认证有效性"""
        # 有效配置
        config = AuthConfig(
            auth_type=AuthType.TOKEN,
            credentials={"token": "test-token"},
        )
        assert config.is_valid() is True

        # 无效配置（空凭证）
        config = AuthConfig(
            auth_type=AuthType.TOKEN,
            credentials={},
        )
        assert config.is_valid() is False

        # NONE 类型总是有效
        config = AuthConfig(
            auth_type=AuthType.NONE,
            credentials={},
        )
        assert config.is_valid() is True

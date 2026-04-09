#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
包管理器测试

测试 P4-包管理-包依赖管理 功能
"""

import pytest
import json

from zhc.package import (
    # 版本管理
    Version,
    VersionConstraint,
    parse_version,
    parse_constraint,
    ProjectConfig,
    DependencyResolver,
    MockRepository,
    # 锁定文件
    Lockfile,
    LockedPackage,
    # 错误定义
    PackageNotFoundError,
    VersionNotFoundError,
    DependencyConflictError,
    CyclicDependencyError,
    InvalidVersionError,
    InvalidConstraintError,
)


class TestVersion:
    """版本解析测试"""

    def test_version_parsing(self):
        """测试版本解析"""
        v1 = Version.parse("1.2.3")
        assert v1.major == 1
        assert v1.minor == 2
        assert v1.patch == 3
        assert v1.prerelease is None

    def test_version_parsing_with_prerelease(self):
        """测试预发布版本解析"""
        v2 = Version.parse("2.0.0-beta")
        assert v2.major == 2
        assert v2.minor == 0
        assert v2.patch == 0
        assert v2.prerelease == "beta"

    def test_version_parsing_with_prerelease_number(self):
        """测试带数字的预发布版本"""
        v3 = Version.parse("1.0.0-alpha.1")
        assert v3.prerelease == "alpha.1"

    def test_version_comparison(self):
        """测试版本比较"""
        v1 = Version.parse("1.2.3")
        v2 = Version.parse("1.2.4")
        v3 = Version.parse("2.0.0")

        assert v1 < v2
        assert v2 < v3
        assert v1 < v3

    def test_version_equality(self):
        """测试版本相等"""
        v1 = Version.parse("1.2.3")
        v2 = Version.parse("1.2.3")
        v3 = Version.parse("1.2.4")

        assert v1 == v2
        assert v1 != v3

    def test_version_prerelease_comparison(self):
        """测试预发布版本比较"""
        v1 = Version.parse("1.0.0-alpha")
        v2 = Version.parse("1.0.0-beta")
        v3 = Version.parse("1.0.0")

        assert v1 < v2  # alpha < beta
        assert v2 < v3  # beta < release
        assert v1 < v3  # alpha < release

    def test_version_bump(self):
        """测试版本号提升"""
        v = Version.parse("1.2.3")

        assert str(v.bump_major()) == "2.0.0"
        assert str(v.bump_minor()) == "1.3.0"
        assert str(v.bump_patch()) == "1.2.4"

    def test_version_to_string(self):
        """测试版本转字符串"""
        v1 = Version.parse("1.2.3")
        v2 = Version.parse("2.0.0-beta")

        assert str(v1) == "1.2.3"
        assert str(v2) == "2.0.0-beta"

    def test_version_invalid_format(self):
        """测试无效版本格式"""
        with pytest.raises(InvalidVersionError):
            Version.parse("1.2")
        with pytest.raises(InvalidVersionError):
            Version.parse("invalid")
        with pytest.raises(InvalidVersionError):
            Version.parse("1.2.3.4")


class TestVersionConstraint:
    """版本约束测试"""

    def test_constraint_caret(self):
        """测试 ^ 约束（兼容版本）"""
        constraint = VersionConstraint("^1.2.3")

        assert constraint.matches(Version.parse("1.2.3"))
        assert constraint.matches(Version.parse("1.3.0"))
        assert constraint.matches(Version.parse("1.9.9"))
        assert not constraint.matches(Version.parse("2.0.0"))
        assert not constraint.matches(Version.parse("1.2.2"))

    def test_constraint_tilde(self):
        """测试 ~ 约束（近似版本）"""
        constraint = VersionConstraint("~1.2.3")

        assert constraint.matches(Version.parse("1.2.3"))
        assert constraint.matches(Version.parse("1.2.9"))
        assert not constraint.matches(Version.parse("1.3.0"))
        assert not constraint.matches(Version.parse("2.0.0"))

    def test_constraint_greater_than_or_equal(self):
        """测试 >= 约束"""
        constraint = VersionConstraint(">=1.2.3")

        assert constraint.matches(Version.parse("1.2.3"))
        assert constraint.matches(Version.parse("1.2.4"))
        assert constraint.matches(Version.parse("2.0.0"))
        assert not constraint.matches(Version.parse("1.2.2"))

    def test_constraint_less_than(self):
        """测试 < 约束"""
        constraint = VersionConstraint("<2.0.0")

        assert constraint.matches(Version.parse("1.9.9"))
        assert constraint.matches(Version.parse("0.0.1"))
        assert not constraint.matches(Version.parse("2.0.0"))
        assert not constraint.matches(Version.parse("2.0.1"))

    def test_constraint_exact(self):
        """测试精确版本约束"""
        constraint = VersionConstraint("1.2.3")

        assert constraint.matches(Version.parse("1.2.3"))
        assert not constraint.matches(Version.parse("1.2.4"))
        assert not constraint.matches(Version.parse("1.2.2"))

    def test_constraint_combined(self):
        """测试组合约束"""
        constraint = VersionConstraint(">=1.0.0 <2.0.0")

        assert constraint.matches(Version.parse("1.0.0"))
        assert constraint.matches(Version.parse("1.5.0"))
        assert not constraint.matches(Version.parse("0.9.9"))
        assert not constraint.matches(Version.parse("2.0.0"))

    def test_constraint_invalid_format(self):
        """测试无效约束格式"""
        with pytest.raises(InvalidConstraintError):
            VersionConstraint("invalid")


class TestProjectConfig:
    """项目配置测试"""

    def test_config_creation(self, tmp_path):
        """测试配置创建"""
        config = ProjectConfig(
            name="测试项目",
            version="1.0.0",
            description="一个测试项目",
            author="测试作者",
        )

        assert config.name == "测试项目"
        assert config.version == "1.0.0"

    def test_config_save_and_load(self, tmp_path):
        """测试配置保存和加载"""
        config = ProjectConfig(
            name="测试项目",
            version="1.0.0",
            description="一个测试项目",
            author="测试作者",
            dependencies={"网络库": "^2.0.0", "日志工具": "~1.2.3"},
            dev_dependencies={"测试框架": "^1.0.0"},
        )

        # 保存配置
        config_path = tmp_path / "zhc.json"
        config.to_file(config_path)

        # 加载配置
        loaded_config = ProjectConfig.from_file(config_path)

        assert loaded_config.name == config.name
        assert loaded_config.version == config.version
        assert loaded_config.dependencies == config.dependencies
        assert loaded_config.dev_dependencies == config.dev_dependencies

    def test_config_add_dependency(self):
        """测试添加依赖"""
        config = ProjectConfig(name="测试项目", version="1.0.0")

        config.add_dependency("网络库", "^2.0.0")
        assert "网络库" in config.dependencies

        config.add_dependency("测试框架", "^1.0.0", dev=True)
        assert "测试框架" in config.dev_dependencies

    def test_config_remove_dependency(self):
        """测试移除依赖"""
        config = ProjectConfig(
            name="测试项目",
            version="1.0.0",
            dependencies={"网络库": "^2.0.0"},
            dev_dependencies={"测试框架": "^1.0.0"},
        )

        assert config.remove_dependency("网络库")
        assert "网络库" not in config.dependencies

        assert config.remove_dependency("测试框架", dev=True)
        assert "测试框架" not in config.dev_dependencies

    def test_config_get_all_dependencies(self):
        """测试获取所有依赖"""
        config = ProjectConfig(
            name="测试项目",
            version="1.0.0",
            dependencies={"网络库": "^2.0.0"},
            dev_dependencies={"测试框架": "^1.0.0"},
        )

        all_deps = config.get_all_dependencies()
        assert len(all_deps) == 2
        assert "网络库" in all_deps
        assert "测试框架" in all_deps

    def test_config_missing_required_fields(self, tmp_path):
        """测试缺少必填字段"""
        # 缺少 name
        config_data = {"version": "1.0.0"}
        config_path = tmp_path / "zhc.json"
        with open(config_path, "w") as f:
            json.dump(config_data, f)

        with pytest.raises(Exception):
            ProjectConfig.from_file(config_path)


class TestDependencyResolver:
    """依赖解析器测试"""

    def test_simple_dependency_resolution(self):
        """测试简单依赖解析"""
        mock_repo = MockRepository(
            {
                "网络库": {
                    "1.0.0": {},
                    "2.0.0": {},
                }
            }
        )

        resolver = DependencyResolver(mock_repo)
        resolved = resolver.resolve({"网络库": "^2.0.0"})

        assert "网络库" in resolved
        assert resolved["网络库"].version == Version.parse("2.0.0")

    def test_transitive_dependency_resolution(self):
        """测试传递依赖解析"""
        mock_repo = MockRepository(
            {
                "网络库": {
                    "2.0.0": {"日志工具": "^1.0.0"},
                },
                "日志工具": {
                    "1.0.0": {},
                    "1.5.0": {},
                },
            }
        )

        resolver = DependencyResolver(mock_repo)
        resolved = resolver.resolve({"网络库": "^2.0.0"})

        assert "网络库" in resolved
        assert "日志工具" in resolved
        assert resolved["日志工具"].version == Version.parse("1.5.0")

    def test_version_conflict_detection(self):
        """测试版本冲突检测"""
        mock_repo = MockRepository(
            {
                "网络库": {
                    "2.0.0": {"日志工具": "^1.0.0"},
                },
                "数据库": {
                    "1.0.0": {"日志工具": "^2.0.0"},
                },
                "日志工具": {
                    "1.0.0": {},
                    "2.0.0": {},
                },
            }
        )

        resolver = DependencyResolver(mock_repo)

        with pytest.raises(DependencyConflictError):
            resolver.resolve(
                {"网络库": "^2.0.0", "数据库": "^1.0.0"},
            )

    def test_cyclic_dependency_detection(self):
        """测试循环依赖检测"""
        mock_repo = MockRepository(
            {
                "包A": {
                    "1.0.0": {"包B": "^1.0.0"},
                },
                "包B": {
                    "1.0.0": {"包A": "^1.0.0"},
                },
            }
        )

        resolver = DependencyResolver(mock_repo)

        with pytest.raises(CyclicDependencyError):
            resolver.resolve({"包A": "^1.0.0"})

    def test_package_not_found(self):
        """测试包不存在"""
        mock_repo = MockRepository({})

        resolver = DependencyResolver(mock_repo)

        with pytest.raises(PackageNotFoundError):
            resolver.resolve({"不存在的包": "^1.0.0"})

    def test_version_not_found(self):
        """测试版本不存在"""
        mock_repo = MockRepository(
            {
                "网络库": {
                    "1.0.0": {},
                },
            }
        )

        resolver = DependencyResolver(mock_repo)

        with pytest.raises(VersionNotFoundError):
            resolver.resolve({"网络库": "^2.0.0"})


class TestLockfile:
    """锁定文件测试"""

    def test_lockfile_creation(self):
        """测试锁定文件创建"""
        lockfile = Lockfile()

        assert lockfile.version == "1.0"
        assert len(lockfile.packages) == 0

    def test_lockfile_from_resolved(self):
        """测试从解析结果创建锁定文件"""
        mock_repo = MockRepository(
            {
                "网络库": {
                    "2.0.0": {"日志工具": "^1.0.0"},
                },
                "日志工具": {
                    "1.5.0": {},
                },
            }
        )

        resolver = DependencyResolver(mock_repo)
        resolved = resolver.resolve({"网络库": "^2.0.0"})

        lockfile = Lockfile.from_resolved(resolved)

        assert "网络库" in lockfile.packages
        assert "日志工具" in lockfile.packages
        assert lockfile.packages["网络库"].version == Version.parse("2.0.0")

    def test_lockfile_save_and_load(self, tmp_path):
        """测试锁定文件保存和加载"""
        lockfile = Lockfile()
        lockfile.add_package(
            LockedPackage(
                name="网络库",
                version=Version.parse("2.0.0"),
                source="https://registry.zhc-lang.org/网络库/2.0.0",
            )
        )

        # 保存锁定文件
        lockfile_path = tmp_path / "zhc.lock"
        lockfile.to_file(lockfile_path)

        # 加载锁定文件
        loaded_lockfile = Lockfile.from_file(lockfile_path)

        assert "网络库" in loaded_lockfile.packages
        assert loaded_lockfile.packages["网络库"].version == Version.parse("2.0.0")

    def test_lockfile_has_package(self):
        """测试检查包是否存在"""
        lockfile = Lockfile()
        lockfile.add_package(
            LockedPackage(
                name="网络库",
                version=Version.parse("2.0.0"),
            )
        )

        assert lockfile.has_package("网络库")
        assert not lockfile.has_package("日志工具")

    def test_lockfile_remove_package(self):
        """测试移除包"""
        lockfile = Lockfile()
        lockfile.add_package(
            LockedPackage(
                name="网络库",
                version=Version.parse("2.0.0"),
            )
        )

        assert lockfile.remove_package("网络库")
        assert not lockfile.has_package("网络库")
        assert not lockfile.remove_package("网络库")  # 不存在


class TestIntegration:
    """集成测试"""

    def test_full_workflow(self, tmp_path):
        """测试完整工作流程"""
        # 1. 创建项目配置
        config = ProjectConfig(
            name="测试项目",
            version="1.0.0",
            dependencies={"网络库": "^2.0.0"},
        )

        config_path = tmp_path / "zhc.json"
        config.to_file(config_path)

        # 2. 创建模拟仓库
        mock_repo = MockRepository(
            {
                "网络库": {
                    "2.0.0": {"日志工具": "^1.0.0"},
                },
                "日志工具": {
                    "1.5.0": {},
                },
            }
        )

        # 3. 解析依赖
        resolver = DependencyResolver(mock_repo)
        resolved = resolver.resolve(config.dependencies)

        assert len(resolved) == 2
        assert "网络库" in resolved
        assert "日志工具" in resolved

        # 4. 创建锁定文件
        lockfile = Lockfile.from_resolved(resolved)

        lockfile_path = tmp_path / "zhc.lock"
        lockfile.to_file(lockfile_path)

        # 5. 验证锁定文件
        assert lockfile_path.exists()
        loaded_lockfile = Lockfile.from_file(lockfile_path)
        assert len(loaded_lockfile.packages) == 2

    def test_version_constraint_workflow(self):
        """测试版本约束工作流程"""
        # 测试各种版本约束
        test_cases = [
            ("^1.2.3", "1.2.3", True),
            ("^1.2.3", "1.9.9", True),
            ("^1.2.3", "2.0.0", False),
            ("~1.2.3", "1.2.9", True),
            (">=1.0.0 <2.0.0", "1.5.0", True),
            (">=1.0.0 <2.0.0", "2.0.0", False),
        ]

        for constraint_str, version_str, expected in test_cases:
            constraint = parse_constraint(constraint_str)
            version = parse_version(version_str)
            assert constraint.matches(version) == expected, (
                f"约束 {constraint_str} 对版本 {version_str} " f"期望 {expected}"
            )

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本控制管理器

提供版本升级、发布、验证等功能
"""

import json
from typing import Optional, List
from pathlib import Path

from .version import Version, PrereleaseType
from .errors import PackageError


class VersionError(PackageError):
    """版本控制错误"""

    pass


class VersionControl:
    """版本控制管理器

    提供版本升级、发布、验证等功能
    """

    def __init__(self, project_root: Path):
        """初始化版本控制管理器

        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root
        self.config_path = project_root / "zhc.json"
        self.changelog_path = project_root / "CHANGELOG.md"

        # 加载当前版本
        self.current_version = self._load_version()

    def _load_version(self) -> Version:
        """从配置文件加载版本

        Returns:
            当前版本

        Raises:
            VersionError: 配置文件不存在或版本格式无效
        """
        if not self.config_path.exists():
            # 配置文件不存在，创建默认配置文件
            self.init_version("0.1.0")
            return Version.parse("0.1.0")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise VersionError(f"配置文件 JSON 格式错误: {e}", str(self.config_path))
        except Exception as e:
            raise VersionError(f"读取配置文件失败: {e}", str(self.config_path))

        if "version" not in data:
            # 配置文件缺少版本字段，添加默认版本
            data["version"] = "0.1.0"
            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
            return Version.parse("0.1.0")

        try:
            return Version.parse(data["version"])
        except Exception as e:
            raise VersionError(f"版本格式无效: {e}", str(self.config_path))

    def _save_version(self, version: Version):
        """保存版本到配置文件

        Args:
            version: 要保存的版本

        Raises:
            VersionError: 配置文件写入失败
        """
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise VersionError(f"读取配置文件失败: {e}", str(self.config_path))

        data["version"] = str(version)

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise VersionError(f"写入配置文件失败: {e}", str(self.config_path))

        self.current_version = version

    def bump(
        self,
        level: str,
        prerelease_type: Optional[PrereleaseType] = None,
    ) -> Version:
        """升级版本

        Args:
            level: 升级级别 (major, minor, patch, prerelease)
            prerelease_type: 预发布类型（仅 prerelease 级别需要）

        Returns:
            新版本号

        Raises:
            VersionError: 版本升级失败
        """
        if level == "major":
            new_version = self.current_version.bump_major()
        elif level == "minor":
            new_version = self.current_version.bump_minor()
        elif level == "patch":
            new_version = self.current_version.bump_patch()
        elif level == "prerelease":
            if not prerelease_type:
                raise VersionError("预发布版本需要指定类型", "")
            new_version = self.current_version.bump_prerelease(prerelease_type)
        else:
            raise VersionError(f"未知的升级级别: {level}", "")

        # 验证版本升级（预发布版本除外）
        # 注意：从正式版本到预发布版本是允许的（例如 1.0.0 → 1.0.0-beta.0）
        if level != "prerelease" and new_version <= self.current_version:
            raise VersionError(
                f"版本号不能回退: {self.current_version} → {new_version}",
                "",
            )

        # 保存新版本
        self._save_version(new_version)

        return new_version

    def release(
        self,
        message: Optional[str] = None,
        push: bool = False,
    ) -> str:
        """发布版本

        Args:
            message: 发布消息
            push: 是否推送到远程仓库

        Returns:
            Git 标签名

        Raises:
            VersionError: 发布失败
        """
        from .git_utils import GitUtils
        from .changelog import ChangelogGenerator

        version = self.current_version

        # 如果是预发布版本，先转换为正式版本
        if version.prerelease:
            version = version.to_release()
            self._save_version(version)

        # 创建 Git 标签
        tag_name = f"v{version}"

        git = GitUtils(self.project_root)

        # 检查标签是否已存在
        if git.tag_exists(tag_name):
            raise VersionError(f"标签 {tag_name} 已存在", "")

        # 生成 CHANGELOG
        generator = ChangelogGenerator(self.project_root)
        generator.generate(version, message)

        # 提交变更
        git.commit(f"chore: 发布版本 {version}")

        # 创建标签
        git.create_tag(tag_name, message or f"Release {version}")

        # 推送
        if push:
            git.push()
            git.push_tag(tag_name)

        return tag_name

    def validate_version(self, version_str: str) -> bool:
        """验证版本号格式

        Args:
            version_str: 版本字符串

        Returns:
            是否有效
        """
        try:
            Version.parse(version_str)
            return True
        except Exception:
            return False

    def compare_versions(self, v1: str, v2: str) -> int:
        """比较两个版本

        Args:
            v1: 第一个版本字符串
            v2: 第二个版本字符串

        Returns:
            -1: v1 < v2
            0: v1 == v2
            1: v1 > v2
        """
        version1 = Version.parse(v1)
        version2 = Version.parse(v2)

        if version1 < version2:
            return -1
        elif version1 > version2:
            return 1
        else:
            return 0

    def get_version_history(self) -> List[Version]:
        """获取版本历史

        Returns:
            版本列表（按从新到旧排序）
        """
        from .git_utils import GitUtils

        git = GitUtils(self.project_root)
        tags = git.get_tags()

        versions = []
        for tag in tags:
            if tag.startswith("v"):
                try:
                    version = Version.parse(tag[1:])
                    versions.append(version)
                except Exception:
                    continue

        return sorted(versions, reverse=True)

    def init_version(self, initial_version: str = "0.1.0"):
        """初始化版本

        Args:
            initial_version: 初始版本号

        Raises:
            VersionError: 初始化失败
        """
        if self.config_path.exists():
            # 配置文件已存在，更新版本
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                raise VersionError(f"读取配置文件失败: {e}", str(self.config_path))

            # 确保配置文件有必要的字段
            if "name" not in data:
                data["name"] = self.project_root.name
            data["version"] = initial_version

            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                raise VersionError(f"写入配置文件失败: {e}", str(self.config_path))

            self.current_version = Version.parse(initial_version)
        else:
            # 创建新的配置文件
            config = {
                "name": self.project_root.name,
                "version": initial_version,
                "description": "",
                "author": "",
                "dependencies": {},
                "devDependencies": {},
                "license": "MIT",
            }

            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            except Exception as e:
                raise VersionError(f"创建配置文件失败: {e}", str(self.config_path))

            self.current_version = Version.parse(initial_version)

            self.current_version = Version.parse(initial_version)

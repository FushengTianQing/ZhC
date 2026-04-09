#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHANGELOG 自动生成器

根据 Git 提交记录生成变更日志
"""

from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

from .version import Version


@dataclass
class Commit:
    """Git 提交"""

    hash: str
    message: str
    author: str
    date: datetime


class ChangelogGenerator:
    """CHANGELOG 生成器

    根据 Git 提交记录生成变更日志
    """

    # 提交类型映射
    TYPE_MAP = {
        "feat": "新功能",
        "fix": "问题修复",
        "docs": "文档更新",
        "style": "代码格式",
        "refactor": "代码重构",
        "perf": "性能优化",
        "test": "测试相关",
        "chore": "构建/工具",
        "ci": "CI/CD",
    }

    def __init__(self, project_root: Path):
        """初始化 CHANGELOG 生成器

        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root
        self.changelog_path = project_root / "CHANGELOG.md"

    def generate(
        self,
        version: Version,
        message: Optional[str] = None,
    ):
        """生成 CHANGELOG

        Args:
            version: 版本号
            message: 发布消息
        """
        from .git_utils import GitUtils

        git = GitUtils(self.project_root)

        # 获取上一个版本的标签
        last_tag = git.get_last_tag()

        # 获取提交记录
        commits = git.get_commits(last_tag)

        # 分类提交
        categorized = self._categorize_commits(commits)

        # 生成内容
        content = self._format_changelog(version, categorized, message)

        # 写入文件
        self._write_changelog(content)

    def _categorize_commits(
        self,
        commits: List[Commit],
    ) -> Dict[str, List[Commit]]:
        """分类提交记录

        Args:
            commits: 提交列表

        Returns:
            分类后的提交字典
        """
        categorized: Dict[str, List[Commit]] = {}

        for commit in commits:
            # 提取类型（格式: type: message）
            if ":" in commit.message:
                commit_type = commit.message.split(":")[0].strip()

                # 提取作用域（格式: type(scope): message）
                if "(" in commit_type:
                    commit_type = commit_type.split("(")[0]

                if commit_type in self.TYPE_MAP:
                    category = self.TYPE_MAP[commit_type]
                else:
                    category = "其他"
            else:
                category = "其他"

            if category not in categorized:
                categorized[category] = []

            categorized[category].append(commit)

        return categorized

    def _format_changelog(
        self,
        version: Version,
        categorized: Dict[str, List[Commit]],
        message: Optional[str],
    ) -> str:
        """格式化 CHANGELOG

        Args:
            version: 版本号
            categorized: 分类后的提交
            message: 发布消息

        Returns:
            CHANGELOG 内容
        """
        lines = []

        # 版本标题
        date_str = datetime.now().strftime("%Y-%m-%d")
        lines.append(f"## [{version}] - {date_str}")
        lines.append("")

        # 发布说明
        if message:
            lines.append(message)
            lines.append("")

        # 分类变更
        for category, commits in categorized.items():
            if not commits:
                continue

            lines.append(f"### {category}")
            lines.append("")

            for commit in commits:
                # 提取消息（移除类型前缀）
                msg = commit.message
                if ":" in msg:
                    msg = msg.split(":", 1)[1].strip()

                lines.append(f"- {msg} ([{commit.hash[:7]}])")

            lines.append("")

        return "\n".join(lines)

    def _write_changelog(self, content: str):
        """写入 CHANGELOG 文件

        Args:
            content: CHANGELOG 内容
        """
        if self.changelog_path.exists():
            # 读取现有内容
            with open(self.changelog_path, "r", encoding="utf-8") as f:
                existing = f.read()

            # 插入新内容（在第一个版本标题之前）
            if "## [" in existing:
                parts = existing.split("## [", 1)
                new_content = parts[0] + content + "\n## [" + parts[1]
            else:
                new_content = existing + "\n\n" + content
        else:
            # 创建新文件
            header = "# CHANGELOG\n\n所有重要的变更都将记录在此文件中。\n\n"
            new_content = header + content

        with open(self.changelog_path, "w", encoding="utf-8") as f:
            f.write(new_content)

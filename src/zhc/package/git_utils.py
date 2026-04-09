#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git 工具函数

提供 Git 操作的封装
"""

import subprocess
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from .changelog import Commit


class GitError(Exception):
    """Git 操作错误"""

    pass


class GitUtils:
    """Git 工具类

    提供 Git 操作的封装
    """

    def __init__(self, project_root: Path):
        """初始化 Git 工具

        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root

    def _run_git_command(
        self,
        args: List[str],
        check: bool = True,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess:
        """运行 Git 命令

        Args:
            args: Git 命令参数
            check: 是否检查返回码
            capture_output: 是否捕获输出

        Returns:
            命令执行结果

        Raises:
            GitError: Git 命令执行失败
        """
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.project_root,
                check=check,
                capture_output=capture_output,
                text=True,
            )
            return result
        except subprocess.CalledProcessError as e:
            raise GitError(f"Git 命令执行失败: {' '.join(args)}\n{e.stderr}")
        except FileNotFoundError:
            raise GitError("Git 未安装或不在 PATH 中")

    def is_git_repo(self) -> bool:
        """检查是否为 Git 仓库

        Returns:
            是否为 Git 仓库
        """
        try:
            self._run_git_command(["rev-parse", "--git-dir"], check=True)
            return True
        except GitError:
            return False

    def commit(self, message: str):
        """Git 提交

        Args:
            message: 提交消息

        Raises:
            GitError: 提交失败
        """
        # 添加所有文件
        self._run_git_command(["add", "."])

        # 提交
        self._run_git_command(["commit", "-m", message])

    def create_tag(self, tag_name: str, message: str):
        """创建 Git 标签

        Args:
            tag_name: 标签名
            message: 标签消息

        Raises:
            GitError: 创建标签失败
        """
        self._run_git_command(["tag", "-a", tag_name, "-m", message])

    def push(self):
        """推送代码到远程仓库

        Raises:
            GitError: 推送失败
        """
        self._run_git_command(["push"])

    def push_tag(self, tag_name: str):
        """推送标签到远程仓库

        Args:
            tag_name: 标签名

        Raises:
            GitError: 推送失败
        """
        self._run_git_command(["push", "origin", tag_name])

    def tag_exists(self, tag_name: str) -> bool:
        """检查标签是否存在

        Args:
            tag_name: 标签名

        Returns:
            标签是否存在
        """
        result = self._run_git_command(["tag", "-l", tag_name])
        return tag_name in result.stdout

    def get_tags(self) -> List[str]:
        """获取所有 Git 标签

        Returns:
            标签列表
        """
        result = self._run_git_command(["tag", "-l"])
        tags = result.stdout.strip().split("\n")
        return [tag for tag in tags if tag]

    def get_last_tag(self) -> Optional[str]:
        """获取上一个版本标签

        Returns:
            上一个版本标签，如果没有则返回 None
        """
        result = self._run_git_command(
            ["describe", "--tags", "--abbrev=0", "HEAD^"],
            check=False,
        )

        if result.returncode == 0:
            return result.stdout.strip()

        return None

    def get_commits(self, since_tag: Optional[str] = None) -> List[Commit]:
        """获取提交记录

        Args:
            since_tag: 从哪个标签开始（不包含）

        Returns:
            提交列表
        """
        if since_tag:
            cmd = ["log", f"{since_tag}..HEAD", "--pretty=format:%H|%s|%an|%ai"]
        else:
            cmd = ["log", "--pretty=format:%H|%s|%an|%ai"]

        result = self._run_git_command(cmd)

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            parts = line.split("|")
            if len(parts) >= 4:
                try:
                    # 解析日期：格式为 "2026-04-10 00:24:53 +0800"
                    date_str = parts[3]
                    # 移除时区信息，只保留日期时间
                    date_str = date_str.replace(" ", "T", 1).split("+")[0].split("-")[0]
                    # 实际上，我们直接使用原始字符串
                    # 简单处理：将空格替换为 T，然后解析
                    date_str = parts[3].replace(" ", "T", 1)
                    # 移除时区信息（+0800）
                    if "+" in date_str:
                        date_str = date_str.split("+")[0]
                    elif date_str.count("-") > 2:
                        # 处理负时区
                        last_dash = date_str.rfind("-")
                        date_str = date_str[:last_dash]

                    date = datetime.fromisoformat(date_str)

                    commits.append(
                        Commit(
                            hash=parts[0],
                            message=parts[1],
                            author=parts[2],
                            date=date,
                        )
                    )
                except (ValueError, IndexError):
                    # 跳过解析失败的提交
                    continue

        return commits

    def get_current_branch(self) -> str:
        """获取当前分支名

        Returns:
            当前分支名

        Raises:
            GitError: 获取失败
        """
        result = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
        return result.stdout.strip()

    def get_remote_url(self) -> Optional[str]:
        """获取远程仓库 URL

        Returns:
            远程仓库 URL，如果没有则返回 None
        """
        result = self._run_git_command(["remote", "get-url", "origin"], check=False)

        if result.returncode == 0:
            return result.stdout.strip()

        return None

    def has_uncommitted_changes(self) -> bool:
        """检查是否有未提交的更改

        Returns:
            是否有未提交的更改
        """
        result = self._run_git_command(["status", "--porcelain"])
        return bool(result.stdout.strip())

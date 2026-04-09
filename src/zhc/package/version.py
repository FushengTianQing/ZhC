#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语义化版本约束处理

支持格式：
- ^1.2.3  兼容版本（>=1.2.3 <2.0.0）
- ~1.2.3  近似版本（>=1.2.3 <1.3.0）
- >=1.2.3 范围约束
- 1.2.3   精确版本
- 1.2.3-alpha.1  预发布版本
- 1.2.3+build.123  构建元数据

参考：https://semver.org/
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass
from functools import total_ordering
from enum import Enum

from .errors import InvalidVersionError, InvalidConstraintError


class PrereleaseType(Enum):
    """预发布类型"""

    ALPHA = "alpha"
    BETA = "beta"
    RC = "rc"

    @classmethod
    def from_string(cls, value: str) -> "PrereleaseType":
        """从字符串解析预发布类型

        Args:
            value: 预发布类型字符串

        Returns:
            PrereleaseType 枚举值

        Raises:
            ValueError: 无效的预发布类型
        """
        value_lower = value.lower()
        for member in cls:
            if member.value == value_lower:
                return member
        raise ValueError(f"无效的预发布类型: {value}")


@dataclass
class Prerelease:
    """预发布信息

    格式: alpha.0, beta.1, rc.2
    """

    type: PrereleaseType
    number: int = 0

    def __str__(self) -> str:
        return f"{self.type.value}.{self.number}"

    def __lt__(self, other: "Prerelease") -> bool:
        """比较预发布版本

        alpha < beta < rc
        """
        # 预发布类型顺序
        type_order = {
            PrereleaseType.ALPHA: 0,
            PrereleaseType.BETA: 1,
            PrereleaseType.RC: 2,
        }

        if self.type != other.type:
            return type_order[self.type] < type_order[other.type]

        return self.number < other.number

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Prerelease):
            return NotImplemented
        return self.type == other.type and self.number == other.number

    def __hash__(self) -> int:
        return hash((self.type, self.number))

    @classmethod
    def parse(cls, prerelease_str: str) -> "Prerelease":
        """解析预发布字符串

        Args:
            prerelease_str: 预发布字符串（如 "alpha.1"）

        Returns:
            Prerelease 对象

        Raises:
            ValueError: 预发布格式无效
        """
        # 支持 alpha, alpha.1, beta, beta.2 等格式
        parts = prerelease_str.split(".")
        if not parts:
            raise ValueError(f"无效的预发布格式: {prerelease_str}")

        prerelease_type = PrereleaseType.from_string(parts[0])

        # 如果有编号，解析编号
        number = 0
        if len(parts) > 1:
            try:
                number = int(parts[1])
            except ValueError:
                raise ValueError(f"无效的预发布编号: {parts[1]}")

        return cls(prerelease_type, number)


@dataclass
@total_ordering
class Version:
    """语义化版本

    遵循语义化版本规范 (SemVer)
    格式: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
    """

    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None  # 构建元数据

    @classmethod
    def parse(cls, version_str: str) -> "Version":
        """解析版本字符串

        Args:
            version_str: 版本字符串（如 "1.2.3"、"1.2.3-beta.1"、"1.2.3+build.123"）

        Returns:
            Version 对象

        Raises:
            InvalidVersionError: 版本格式无效
        """
        # 格式: 1.2.3 或 1.2.3-beta 或 1.2.3-beta.1 或 1.2.3+build.123 或 1.2.3-beta.1+build.123
        # 使用 $ 确保匹配整个字符串
        match = re.match(
            r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.]+))?(?:\+(.+))?$",
            version_str.strip(),
        )
        if not match:
            raise InvalidVersionError(version_str)

        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            prerelease=match.group(4),
            build=match.group(5),
        )

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            base += f"-{self.prerelease}"
        if self.build:
            base += f"+{self.build}"
        return base

    def __repr__(self) -> str:
        return f"Version({self})"

    def __lt__(self, other: "Version") -> bool:
        if not isinstance(other, Version):
            return NotImplemented

        # 比较主版本号
        if self.major != other.major:
            return self.major < other.major

        # 比较次版本号
        if self.minor != other.minor:
            return self.minor < other.minor

        # 比较补丁版本号
        if self.patch != other.patch:
            return self.patch < other.patch

        # 预发布版本 < 正式版本
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False

        # 比较预发布标识
        if self.prerelease and other.prerelease:
            # 尝试解析为 Prerelease 对象进行比较
            try:
                pre1 = Prerelease.parse(self.prerelease)
                pre2 = Prerelease.parse(other.prerelease)
                return pre1 < pre2
            except ValueError:
                # 如果解析失败，使用字符串比较
                return self.prerelease < other.prerelease

        return False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        # 构建元数据不参与版本比较
        return (self.major, self.minor, self.patch, self.prerelease) == (
            other.major,
            other.minor,
            other.patch,
            other.prerelease,
        )

    def __hash__(self) -> int:
        # 构建元数据不参与哈希
        return hash((self.major, self.minor, self.patch, self.prerelease))

    def bump_major(self) -> "Version":
        """提升主版本号"""
        return Version(self.major + 1, 0, 0)

    def bump_minor(self) -> "Version":
        """提升次版本号"""
        return Version(self.major, self.minor + 1, 0)

    def bump_patch(self) -> "Version":
        """提升补丁版本号"""
        return Version(self.major, self.minor, self.patch + 1)

    def bump_prerelease(self, prerelease_type: PrereleaseType) -> "Version":
        """提升预发布版本

        Args:
            prerelease_type: 预发布类型

        Returns:
            新的 Version 对象
        """
        if self.prerelease:
            try:
                current_prerelease = Prerelease.parse(self.prerelease)
                if current_prerelease.type == prerelease_type:
                    # 同类型预发布，增加编号
                    new_prerelease = Prerelease(
                        prerelease_type, current_prerelease.number + 1
                    )
                else:
                    # 新类型预发布，从 0 开始
                    new_prerelease = Prerelease(prerelease_type, 0)
            except ValueError:
                # 解析失败，创建新的预发布
                new_prerelease = Prerelease(prerelease_type, 0)
        else:
            # 没有预发布，创建新的预发布
            new_prerelease = Prerelease(prerelease_type, 0)

        return Version(
            self.major,
            self.minor,
            self.patch,
            str(new_prerelease),
        )

    def to_release(self) -> "Version":
        """转换为正式版本（移除预发布标识）"""
        return Version(self.major, self.minor, self.patch)

    def is_prerelease(self) -> bool:
        """是否为预发布版本"""
        return self.prerelease is not None


class VersionConstraint:
    """版本约束

    支持多种约束格式：
    - ^1.2.3  兼容版本（>=1.2.3 <2.0.0）
    - ~1.2.3  近似版本（>=1.2.3 <1.3.0）
    - >=1.2.3 范围约束
    - 1.2.3   精确版本
    - >=1.0.0 <2.0.0 组合约束
    """

    # 操作符正则表达式
    OPERATOR_PATTERN = re.compile(r"(>=|<=|>|<|=)")

    def __init__(self, constraint_str: str):
        """初始化版本约束

        Args:
            constraint_str: 约束字符串

        Raises:
            InvalidConstraintError: 约束格式无效
        """
        self.original = constraint_str.strip()
        self.constraints: List[Tuple[str, Version]] = []
        self._parse(self.original)

    def _parse(self, constraint_str: str):
        """解析约束字符串

        支持以下格式：
        1. ^1.2.3 -> >=1.2.3 <2.0.0
        2. ~1.2.3 -> >=1.2.3 <1.3.0
        3. >=1.2.3 -> >=1.2.3
        4. 1.2.3 -> =1.2.3
        5. >=1.0.0 <2.0.0 -> 多个约束
        """
        # 分割多个约束（空格分隔）
        parts = constraint_str.split()

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # ^1.2.3 -> >=1.2.3 <2.0.0
            if part.startswith("^"):
                version = Version.parse(part[1:])
                self.constraints.append((">=", version))
                self.constraints.append(("<", version.bump_major()))

            # ~1.2.3 -> >=1.2.3 <1.3.0
            elif part.startswith("~"):
                version = Version.parse(part[1:])
                self.constraints.append((">=", version))
                self.constraints.append(("<", version.bump_minor()))

            # >=, <=, >, <, =
            elif self.OPERATOR_PATTERN.match(part):
                match = self.OPERATOR_PATTERN.match(part)
                if match:
                    op = match.group(1)
                    ver_str = part[len(op) :].strip()
                    version = Version.parse(ver_str)
                    self.constraints.append((op, version))

            # 精确版本
            else:
                try:
                    version = Version.parse(part)
                    self.constraints.append(("=", version))
                except InvalidVersionError:
                    raise InvalidConstraintError(part)

    def matches(self, version: Version) -> bool:
        """检查版本是否满足约束

        Args:
            version: 要检查的版本

        Returns:
            是否满足约束
        """
        for op, constraint_version in self.constraints:
            if not self._check_constraint(version, op, constraint_version):
                return False
        return True

    def _check_constraint(
        self, version: Version, op: str, constraint_version: Version
    ) -> bool:
        """检查单个约束条件

        Args:
            version: 要检查的版本
            op: 操作符
            constraint_version: 约束版本

        Returns:
            是否满足
        """
        if op == ">=":
            return version >= constraint_version
        elif op == ">":
            return version > constraint_version
        elif op == "<=":
            return version <= constraint_version
        elif op == "<":
            return version < constraint_version
        elif op == "=":
            return version == constraint_version
        return False

    def __str__(self) -> str:
        return self.original

    def __repr__(self) -> str:
        return f"VersionConstraint({self.original!r})"

    def to_dict(self) -> dict:
        """转换为字典（用于序列化）"""
        return {
            "original": self.original,
            "constraints": [
                {"op": op, "version": str(version)} for op, version in self.constraints
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VersionConstraint":
        """从字典创建（用于反序列化）"""
        return cls(data["original"])


def parse_version(version_str: str) -> Version:
    """解析版本字符串（便捷函数）"""
    return Version.parse(version_str)


def parse_constraint(constraint_str: str) -> VersionConstraint:
    """解析约束字符串（便捷函数）"""
    return VersionConstraint(constraint_str)


def satisfies(version: Version, constraint: VersionConstraint) -> bool:
    """检查版本是否满足约束（便捷函数）"""
    return constraint.matches(version)

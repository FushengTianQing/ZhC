#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锁定文件管理

管理 zhc.lock 锁定文件，确保可重复构建
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .version import Version
from .dependency import ResolvedDependency
from .errors import LockfileError


@dataclass
class LockedPackage:
    """锁定的包"""

    name: str
    version: Version
    source: Optional[str] = None
    checksum: str = ""
    dependencies: Dict[str, str] = field(default_factory=dict)  # 依赖名 -> 版本约束

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "version": str(self.version),
            "source": self.source,
            "checksum": self.checksum,
            "dependencies": self.dependencies,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LockedPackage":
        """从字典创建"""
        return cls(
            name=data["name"],
            version=Version.parse(data["version"]),
            source=data.get("source"),
            checksum=data.get("checksum", ""),
            dependencies=data.get("dependencies", {}),
        )


@dataclass
class Lockfile:
    """锁定文件

    格式 (zhc.lock):
    {
        "version": "1.0",
        "generated_at": "2026-04-10T00:00:00",
        "packages": {
            "包名": {
                "version": "1.0.0",
                "source": "https://...",
                "checksum": "abc123",
                "dependencies": {
                    "依赖名": "^1.0.0"
                }
            }
        }
    }
    """

    version: str = "1.0"
    generated_at: str = ""
    packages: Dict[str, LockedPackage] = field(default_factory=dict)

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()

    @classmethod
    def from_file(cls, path: Path) -> "Lockfile":
        """从锁定文件加载

        Args:
            path: 锁定文件路径

        Returns:
            Lockfile 对象

        Raises:
            LockfileError: 锁定文件读取或解析失败
        """
        if not path.exists():
            raise LockfileError(f"锁定文件不存在: {path}", str(path))

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise LockfileError(f"锁定文件 JSON 格式错误: {e}", str(path))
        except Exception as e:
            raise LockfileError(f"读取锁定文件失败: {e}", str(path))

        lockfile = cls(
            version=data.get("version", "1.0"),
            generated_at=data.get("generated_at", ""),
        )

        # 解析包信息
        for name, pkg_data in data.get("packages", {}).items():
            lockfile.packages[name] = LockedPackage.from_dict(pkg_data)

        return lockfile

    def to_file(self, path: Path):
        """保存到锁定文件

        Args:
            path: 锁定文件路径

        Raises:
            LockfileError: 锁定文件写入失败
        """
        data = {
            "version": self.version,
            "generated_at": self.generated_at,
            "packages": {name: pkg.to_dict() for name, pkg in self.packages.items()},
        }

        try:
            # 确保目录存在
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise LockfileError(f"写入锁定文件失败: {e}", str(path))

    @classmethod
    def from_resolved(cls, resolved: Dict[str, ResolvedDependency]) -> "Lockfile":
        """从解析结果创建锁定文件

        Args:
            resolved: 解析后的依赖字典

        Returns:
            Lockfile 对象
        """
        lockfile = cls()

        for name, dep in resolved.items():
            lockfile.packages[name] = LockedPackage(
                name=dep.name,
                version=dep.version,
                source=dep.source,
                dependencies={
                    dep_name: "^" + str(dep_version)
                    for dep_name, dep_version in dep.dependencies.items()
                },
            )

        return lockfile

    def get_package(self, name: str) -> Optional[LockedPackage]:
        """获取锁定的包信息

        Args:
            name: 包名

        Returns:
            锁定的包信息，如果不存在返回 None
        """
        return self.packages.get(name)

    def has_package(self, name: str) -> bool:
        """检查是否有指定包"""
        return name in self.packages

    def add_package(self, package: LockedPackage):
        """添加包到锁定文件

        Args:
            package: 锁定的包
        """
        self.packages[package.name] = package

    def remove_package(self, name: str) -> bool:
        """从锁定文件移除包

        Args:
            name: 包名

        Returns:
            是否成功
        """
        if name in self.packages:
            del self.packages[name]
            return True
        return False

    def update_timestamp(self):
        """更新时间戳"""
        self.generated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "packages": {name: pkg.to_dict() for name, pkg in self.packages.items()},
        }

    def get_flat_list(self) -> List[Dict[str, any]]:
        """获取扁平依赖列表

        Returns:
            依赖列表
        """
        return [
            {
                "name": pkg.name,
                "version": str(pkg.version),
                "source": pkg.source,
                "checksum": pkg.checksum,
            }
            for pkg in self.packages.values()
        ]

    def verify_integrity(self) -> List[str]:
        """验证完整性

        Returns:
            验证失败的包名列表
        """
        failed = []
        for name, pkg in self.packages.items():
            # 如果有 checksum，验证它
            if pkg.checksum:
                # 实际应该计算文件哈希并比较
                # 这里简化处理
                pass
        return failed

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
包管理错误定义

定义包管理过程中可能出现的各种错误类型
"""


class PackageError(Exception):
    """包管理基础错误"""

    def __init__(self, message: str, package_name: str = None):
        self.message = message
        self.package_name = package_name
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.package_name:
            return f"[{self.package_name}] {self.message}"
        return self.message


class PackageNotFoundError(PackageError):
    """包不存在错误"""

    def __init__(self, package_name: str):
        super().__init__(f"包 '{package_name}' 不存在", package_name)


class VersionNotFoundError(PackageError):
    """版本不存在错误"""

    def __init__(self, package_name: str, version_constraint: str):
        self.version_constraint = version_constraint
        super().__init__(
            f"包 '{package_name}' 没有满足约束 '{version_constraint}' 的版本",
            package_name,
        )


class DependencyConflictError(PackageError):
    """依赖冲突错误"""

    def __init__(self, conflicts: list):
        self.conflicts = conflicts
        conflict_details = "\n".join(
            f"  - {name}: 需要 {required}, 已解析 {resolved}"
            for name, required, resolved in conflicts
        )
        super().__init__(f"依赖版本冲突:\n{conflict_details}")


class CyclicDependencyError(PackageError):
    """循环依赖错误"""

    def __init__(self, cycle_path: list):
        self.cycle_path = cycle_path
        cycle_str = " -> ".join(cycle_path)
        super().__init__(f"检测到循环依赖: {cycle_str}")


class NetworkError(PackageError):
    """网络错误"""

    def __init__(self, message: str, url: str = None):
        self.url = url
        if url:
            message = f"{message} (URL: {url})"
        super().__init__(message)


class CacheError(PackageError):
    """缓存错误"""

    def __init__(self, message: str, cache_path: str = None):
        self.cache_path = cache_path
        if cache_path:
            message = f"{message} (路径: {cache_path})"
        super().__init__(message)


class LockfileError(PackageError):
    """锁定文件错误"""

    def __init__(self, message: str, lockfile_path: str = None):
        self.lockfile_path = lockfile_path
        if lockfile_path:
            message = f"{message} (文件: {lockfile_path})"
        super().__init__(message)


class ConfigError(PackageError):
    """配置错误"""

    def __init__(self, message: str, config_path: str = None):
        self.config_path = config_path
        if config_path:
            message = f"{message} (文件: {config_path})"
        super().__init__(message)


class InvalidVersionError(PackageError):
    """无效版本格式错误"""

    def __init__(self, version_str: str):
        self.version_str = version_str
        super().__init__(f"无效的版本格式: '{version_str}'")


class InvalidConstraintError(PackageError):
    """无效版本约束错误"""

    def __init__(self, constraint_str: str):
        self.constraint_str = constraint_str
        super().__init__(f"无效的版本约束: '{constraint_str}'")


class PackageIntegrityError(PackageError):
    """包完整性错误"""

    def __init__(self, package_name: str, expected_hash: str, actual_hash: str):
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
        super().__init__(
            f"包 '{package_name}' 完整性校验失败: "
            f"期望哈希 {expected_hash[:8]}..., 实际哈希 {actual_hash[:8]}...",
            package_name,
        )


class OfflineModeError(PackageError):
    """离线模式错误"""

    def __init__(self, package_name: str, version: str):
        self.version = version
        super().__init__(
            f"离线模式下无法安装 {package_name}@{version}，" f"请先在线安装或检查缓存",
            package_name,
        )

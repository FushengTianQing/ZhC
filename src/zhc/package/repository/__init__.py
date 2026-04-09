#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
包仓库模块

提供包仓库的接口和实现：
- base: 仓库基类和数据类
- registry: 仓库注册表
- auth: 认证管理
- index: 包索引管理
- local: 本地仓库实现
- remote: 远程仓库实现
"""

from .base import (
    PackageRepository,
    PackageMetadata,
    PackageSearchResult,
)
from .registry import RepositoryRegistry
from .auth import AuthManager, AuthConfig, AuthType
from .index import PackageIndex, IndexEntry
from .local import LocalRepository
from .remote import RemoteRepository

__all__ = [
    # 基类
    "PackageRepository",
    "PackageMetadata",
    "PackageSearchResult",
    # 注册表
    "RepositoryRegistry",
    # 认证
    "AuthManager",
    "AuthConfig",
    "AuthType",
    # 索引
    "PackageIndex",
    "IndexEntry",
    # 仓库实现
    "LocalRepository",
    "RemoteRepository",
]

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地缓存

管理已下载的包缓存，支持：
- 缓存存储
- 缓存检索
- 缓存清理
- 缓存统计
"""

import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from .version import Version
from .errors import CacheError


@dataclass
class CacheEntry:
    """缓存条目"""

    name: str
    version: Version
    path: Path
    size: int = 0
    created_at: str = ""
    checksum: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if self.path.exists() and self.size == 0:
            self.size = self._calculate_size()

    def _calculate_size(self) -> int:
        """计算目录大小"""
        total = 0
        if self.path.is_dir():
            for file in self.path.rglob("*"):
                if file.is_file():
                    total += file.stat().st_size
        return total

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "version": str(self.version),
            "path": str(self.path),
            "size": self.size,
            "created_at": self.created_at,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CacheEntry":
        """从字典创建"""
        return cls(
            name=data["name"],
            version=Version.parse(data["version"]),
            path=Path(data["path"]),
            size=data.get("size", 0),
            created_at=data.get("created_at", ""),
            checksum=data.get("checksum", ""),
        )

    def is_valid(self) -> bool:
        """检查缓存是否有效"""
        return self.path.exists() and self.path.is_dir()


class PackageCache:
    """包缓存管理器

    管理已下载包的本地缓存
    """

    def __init__(self, cache_dir: Path = None):
        """初始化包缓存

        Args:
            cache_dir: 缓存目录（默认 ~/.zhc/cache）
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".zhc" / "cache"

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._index_file = self.cache_dir / "index.json"
        self._index: Dict[str, CacheEntry] = {}
        self._load_index()

    def _load_index(self):
        """加载缓存索引"""
        if self._index_file.exists():
            try:
                with open(self._index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for key, entry_data in data.items():
                    self._index[key] = CacheEntry.from_dict(entry_data)
            except Exception:
                # 索引文件损坏，忽略
                self._index = {}

    def _save_index(self):
        """保存缓存索引"""
        try:
            data = {key: entry.to_dict() for key, entry in self._index.items()}
            with open(self._index_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise CacheError(f"保存缓存索引失败: {e}", str(self._index_file))

    def _get_cache_key(self, name: str, version: Version) -> str:
        """获取缓存键"""
        return f"{name}@{version}"

    def get_path(self, name: str, version: Version) -> Path:
        """获取缓存路径

        Args:
            name: 包名
            version: 版本

        Returns:
            缓存路径
        """
        return self.cache_dir / name / str(version)

    def has(self, name: str, version: Version) -> bool:
        """检查缓存是否存在

        Args:
            name: 包名
            version: 版本

        Returns:
            是否存在
        """
        key = self._get_cache_key(name, version)
        if key not in self._index:
            return False
        return self._index[key].is_valid()

    def get(self, name: str, version: Version) -> Optional[CacheEntry]:
        """获取缓存条目

        Args:
            name: 包名
            version: 版本

        Returns:
            缓存条目，如果不存在返回 None
        """
        key = self._get_cache_key(name, version)
        entry = self._index.get(key)
        if entry and entry.is_valid():
            return entry
        return None

    def add(self, name: str, version: Version, source_path: Path) -> CacheEntry:
        """添加到缓存

        Args:
            name: 包名
            version: 版本
            source_path: 源路径

        Returns:
            缓存条目

        Raises:
            CacheError: 缓存操作失败
        """
        cache_path = self.get_path(name, version)

        try:
            # 复制到缓存目录
            if cache_path.exists():
                shutil.rmtree(cache_path)
            shutil.copytree(source_path, cache_path)

            # 创建缓存条目
            entry = CacheEntry(
                name=name,
                version=version,
                path=cache_path,
            )

            # 计算校验和
            entry.checksum = self._calculate_checksum(cache_path)

            # 更新索引
            key = self._get_cache_key(name, version)
            self._index[key] = entry
            self._save_index()

            return entry

        except Exception as e:
            raise CacheError(f"添加缓存失败: {e}", str(cache_path))

    def remove(self, name: str, version: Version) -> bool:
        """移除缓存

        Args:
            name: 包名
            version: 版本

        Returns:
            是否成功
        """
        key = self._get_cache_key(name, version)
        entry = self._index.get(key)

        if not entry:
            return False

        try:
            # 删除缓存目录
            if entry.path.exists():
                shutil.rmtree(entry.path)

            # 从索引中移除
            del self._index[key]
            self._save_index()

            return True

        except Exception:
            return False

    def clear(self):
        """清空所有缓存"""
        try:
            # 删除所有缓存目录
            for entry in self._index.values():
                if entry.path.exists():
                    shutil.rmtree(entry.path)

            # 清空索引
            self._index.clear()
            self._save_index()

        except Exception as e:
            raise CacheError(f"清空缓存失败: {e}", str(self.cache_dir))

    def get_stats(self) -> Dict[str, any]:
        """获取缓存统计信息

        Returns:
            统计信息字典
        """
        total_size = 0
        valid_count = 0
        invalid_count = 0

        for entry in self._index.values():
            if entry.is_valid():
                valid_count += 1
                total_size += entry.size
            else:
                invalid_count += 1

        return {
            "total_packages": valid_count,
            "invalid_packages": invalid_count,
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir),
        }

    def cleanup_invalid(self) -> int:
        """清理无效缓存

        Returns:
            清理的缓存数量
        """
        to_remove = []

        for key, entry in self._index.items():
            if not entry.is_valid():
                to_remove.append(key)

        for key in to_remove:
            del self._index[key]

        if to_remove:
            self._save_index()

        return len(to_remove)

    def list_packages(self) -> List[Dict[str, any]]:
        """列出所有缓存的包

        Returns:
            包列表
        """
        result = []
        for entry in self._index.values():
            if entry.is_valid():
                result.append(
                    {
                        "name": entry.name,
                        "version": str(entry.version),
                        "size": entry.size,
                        "created_at": entry.created_at,
                    }
                )
        return result

    def _calculate_checksum(self, path: Path) -> str:
        """计算目录校验和"""
        hasher = hashlib.sha256()

        if path.is_dir():
            for file in sorted(path.rglob("*")):
                if file.is_file():
                    hasher.update(str(file.relative_to(path)).encode())
                    with open(file, "rb") as f:
                        hasher.update(f.read())
        elif path.is_file():
            with open(path, "rb") as f:
                hasher.update(f.read())

        return hasher.hexdigest()[:16]

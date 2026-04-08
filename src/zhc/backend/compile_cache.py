# -*- coding: utf-8 -*-
"""
ZhC 编译缓存 - 提升重复编译性能

提供编译结果缓存，避免重复编译。

作者：远
日期：2026-04-09
"""

import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str  # 缓存键
    input_hash: str  # 输入内容的哈希
    output_path: Path  # 输出文件路径
    created_at: float  # 创建时间戳
    size_bytes: int  # 输出文件大小
    metadata: Dict[str, Any] = field(default_factory=dict)


class CompileCache:
    """
    编译缓存

    提供编译结果的缓存和检索功能。

    使用方式：
        cache = CompileCache(cache_dir=Path(".zhc/cache"))

        # 检查缓存
        cached = cache.get(ir_hash, options_hash)
        if cached:
            return cached

        # 编译并缓存
        result = compile(...)
        cache.put(ir_hash, options_hash, result)
    """

    CACHE_VERSION = 1  # 缓存版本，用于失效旧缓存

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        max_size_mb: int = 500,
        ttl_seconds: int = 86400 * 7,  # 7天
    ):
        """
        初始化编译缓存

        Args:
            cache_dir: 缓存目录
            max_size_mb: 最大缓存大小（MB）
            ttl_seconds: 缓存过期时间（秒）
        """
        self.cache_dir = cache_dir or Path.home() / ".zhc" / "cache"
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.ttl_seconds = ttl_seconds

        # 确保缓存目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 缓存索引文件
        self.index_file = self.cache_dir / "cache_index.json"
        self.index: Dict[str, CacheEntry] = {}

        # 加载索引
        self._load_index()

    def _load_index(self) -> None:
        """加载缓存索引"""
        if not self.index_file.exists():
            return

        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for key, entry_data in data.items():
                self.index[key] = CacheEntry(
                    key=key,
                    input_hash=entry_data["input_hash"],
                    output_path=Path(entry_data["output_path"]),
                    created_at=entry_data["created_at"],
                    size_bytes=entry_data["size_bytes"],
                    metadata=entry_data.get("metadata", {}),
                )
        except Exception as e:
            logger.warning(f"加载缓存索引失败: {e}")
            self.index = {}

    def _save_index(self) -> None:
        """保存缓存索引"""
        try:
            data = {}
            for key, entry in self.index.items():
                data[key] = {
                    "input_hash": entry.input_hash,
                    "output_path": str(entry.output_path),
                    "created_at": entry.created_at,
                    "size_bytes": entry.size_bytes,
                    "metadata": entry.metadata,
                }

            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"保存缓存索引失败: {e}")

    def compute_hash(self, content: str, options: Dict[str, Any]) -> str:
        """
        计算缓存键

        Args:
            content: 输入内容（如 IR 文本）
            options: 编译选项

        Returns:
            str: 缓存键
        """
        # 合并内容和选项
        combined = (
            content + json.dumps(options, sort_keys=True) + str(self.CACHE_VERSION)
        )

        # 计算哈希
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:32]

    def get(self, cache_key: str) -> Optional[Path]:
        """
        获取缓存结果

        Args:
            cache_key: 缓存键

        Returns:
            Optional[Path]: 缓存的输出文件路径，不存在返回 None
        """
        entry = self.index.get(cache_key)

        if not entry:
            return None

        # 检查是否过期
        if time.time() - entry.created_at > self.ttl_seconds:
            self._remove_entry(cache_key)
            return None

        # 检查输出文件是否存在
        if not entry.output_path.exists():
            self._remove_entry(cache_key)
            return None

        logger.debug(f"缓存命中: {cache_key}")
        return entry.output_path

    def put(
        self,
        cache_key: str,
        input_hash: str,
        output_path: Path,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        存储编译结果到缓存

        Args:
            cache_key: 缓存键
            input_hash: 输入内容哈希
            output_path: 输出文件路径
            metadata: 元数据
        """
        # 检查输出文件是否存在
        if not output_path.exists():
            logger.warning(f"输出文件不存在: {output_path}")
            return

        # 获取文件大小
        size_bytes = output_path.stat().st_size

        # 创建缓存条目
        entry = CacheEntry(
            key=cache_key,
            input_hash=input_hash,
            output_path=output_path,
            created_at=time.time(),
            size_bytes=size_bytes,
            metadata=metadata or {},
        )

        # 添加到索引
        self.index[cache_key] = entry

        # 检查缓存大小
        self._check_size_limit()

        # 保存索引
        self._save_index()

        logger.debug(f"缓存存储: {cache_key} -> {output_path}")

    def _remove_entry(self, cache_key: str) -> None:
        """移除缓存条目"""
        if cache_key in self.index:
            del self.index[cache_key]
            self._save_index()

    def _check_size_limit(self) -> None:
        """检查缓存大小限制"""
        total_size = sum(e.size_bytes for e in self.index.values())

        if total_size > self.max_size_bytes:
            # 按时间排序，删除最旧的条目
            sorted_entries = sorted(self.index.items(), key=lambda x: x[1].created_at)

            # 删除直到满足大小限制
            for key, entry in sorted_entries:
                if total_size <= self.max_size_bytes * 0.8:  # 保留 80%
                    break

                # 删除文件
                try:
                    if entry.output_path.exists():
                        entry.output_path.unlink()
                except Exception:
                    pass

                # 更新总大小
                total_size -= entry.size_bytes

                # 从索引中移除
                del self.index[key]

            self._save_index()

    def clear(self) -> None:
        """清空缓存"""
        for entry in self.index.values():
            try:
                if entry.output_path.exists():
                    entry.output_path.unlink()
            except Exception:
                pass

        self.index.clear()
        self._save_index()

        logger.info("缓存已清空")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_size = sum(e.size_bytes for e in self.index.values())

        return {
            "entries": len(self.index),
            "total_size_mb": total_size / (1024 * 1024),
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "usage_percent": (total_size / self.max_size_bytes) * 100,
        }


class CachedBackend:
    """
    带缓存的编译后端装饰器

    为任何后端添加缓存功能。

    使用方式：
        backend = LLVMBackend()
        cached_backend = CachedBackend(backend, cache_dir=Path(".zhc/cache"))

        result = cached_backend.compile(ir, output_path, options)
    """

    def __init__(self, backend: Any, cache: Optional[CompileCache] = None):
        """
        初始化缓存后端

        Args:
            backend: 原始后端
            cache: 编译缓存实例
        """
        self.backend = backend
        self.cache = cache or CompileCache()

    def compile(
        self,
        ir: Any,
        output_path: Path,
        options: Optional[Any] = None,
    ) -> Any:
        """
        编译（带缓存）

        Args:
            ir: IR 程序
            output_path: 输出路径
            options: 编译选项

        Returns:
            CompileResult: 编译结果
        """
        # 计算缓存键
        ir_content = str(ir)  # IR 的字符串表示
        options_dict = {
            "optimization_level": getattr(options, "optimization_level", "O2"),
            "debug": getattr(options, "debug", False),
            "target": getattr(options, "target", None),
            "output_format": str(getattr(options, "output_format", "exe")),
        }

        cache_key = self.cache.compute_hash(ir_content, options_dict)

        # 检查缓存
        cached_path = self.cache.get(cache_key)
        if cached_path and cached_path.exists():
            from .base import CompileResult

            return CompileResult(
                success=True,
                output_files=[cached_path],
                metadata={"cached": True},
            )

        # 执行编译
        result = self.backend.compile(ir, output_path, options)

        # 缓存结果
        if result.success and result.output_files:
            self.cache.put(
                cache_key=cache_key,
                input_hash=hashlib.sha256(ir_content.encode()).hexdigest(),
                output_path=result.output_files[0],
                metadata={"backend": self.backend.name},
            )

        return result

    def __getattr__(self, name):
        """代理其他属性到原始后端"""
        return getattr(self.backend, name)

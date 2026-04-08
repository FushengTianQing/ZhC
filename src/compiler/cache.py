#!/usr/bin/env python3
"""
Day 5: 编译缓存系统

高性能编译缓存系统，支持：
1. 文件内容哈希缓存
2. 编译结果缓存
3. 依赖关系缓存
4. 增量编译支持
5. 缓存一致性维护
"""

import time
import json
import hashlib
import pickle
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    data: Any
    timestamp: float
    size: int
    hits: int = 0
    dependencies: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "key": self.key,
            "timestamp": self.timestamp,
            "size": self.size,
            "hits": self.hits,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "CacheEntry":
        """从字典创建"""
        return cls(
            key=data["key"],
            data=None,  # 实际数据需要单独加载
            timestamp=data["timestamp"],
            size=data["size"],
            hits=data["hits"],
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {}),
        )


class CompilationCache:
    """编译缓存系统"""

    def __init__(self, cache_dir: str = ".zhc_cache", max_size_mb: int = 1024):
        """
        初始化缓存系统

        Args:
            cache_dir: 缓存目录
            max_size_mb: 最大缓存大小（MB）
        """
        self.cache_dir = Path(cache_dir)
        self.max_size = max_size_mb * 1024 * 1024  # 转换为字节

        # 缓存索引
        self.index_file = self.cache_dir / "cache_index.json"
        self.cache_entries: Dict[str, CacheEntry] = {}

        # 统计信息
        self.stats = {
            "total_hits": 0,
            "total_misses": 0,
            "total_saves": 0,
            "total_evictions": 0,
            "current_size": 0,
            "max_size": self.max_size,
        }

        # 初始化缓存目录和索引
        self._initialize_cache()

    def _initialize_cache(self) -> None:
        """初始化缓存目录和索引"""
        # 创建缓存目录
        self.cache_dir.mkdir(exist_ok=True)

        # 加载缓存索引
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    index_data = json.load(f)

                for key, entry_data in index_data.items():
                    entry = CacheEntry.from_dict(entry_data)
                    self.cache_entries[key] = entry
                    self.stats["current_size"] += entry.size

                print(f"📦 加载缓存索引: {len(self.cache_entries)} 个条目")
            except Exception as e:
                print(f"⚠️ 加载缓存索引失败: {e}")
                self.cache_entries = {}
        else:
            print("📦 创建新的缓存索引")

    def _save_index(self) -> None:
        """保存缓存索引"""
        index_data = {}
        for key, entry in self.cache_entries.items():
            index_data[key] = entry.to_dict()

        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)

    def _make_cache_key(self, category: str, *args) -> str:
        """
        生成缓存键

        Args:
            category: 缓存类别（parse, convert, dependency等）
            *args: 其他参数

        Returns:
            缓存键
        """
        # 对所有参数进行哈希
        key_str = f"{category}:{':'.join(str(arg) for arg in args)}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_data_file(self, key: str) -> Path:
        """获取数据文件路径"""
        # 使用前2个字符作为子目录，避免单个目录文件过多
        subdir = key[:2]
        data_dir = self.cache_dir / "data" / subdir
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / f"{key}.dat"

    def _evict_if_needed(self, new_entry_size: int) -> None:
        """
        如果需要，驱逐缓存条目

        使用LRU（最近最少使用）策略
        """
        available_space = self.max_size - self.stats["current_size"]

        if available_space >= new_entry_size:
            return  # 有足够空间

        # 按使用频率和大小排序（分数 = hits / size）
        entries = list(self.cache_entries.items())
        entries.sort(key=lambda x: x[1].hits / max(x[1].size, 1))

        while available_space < new_entry_size and entries:
            # 移除分数最低的条目
            key, entry = entries.pop(0)

            # 删除数据文件
            data_file = self._get_data_file(key)
            if data_file.exists():
                data_file.unlink()

            # 从索引中移除
            del self.cache_entries[key]
            self.stats["current_size"] -= entry.size
            self.stats["total_evictions"] += 1
            available_space = self.max_size - self.stats["current_size"]

            print(
                f"  🗑️  驱逐缓存: {key[:8]}... (命中: {entry.hits}, 大小: {entry.size} B)"
            )

    def get(self, category: str, *args) -> Optional[Any]:
        """
        从缓存获取数据

        Args:
            category: 缓存类别
            *args: 缓存参数

        Returns:
            缓存数据，如果未命中则返回None
        """
        key = self._make_cache_key(category, *args)

        if key not in self.cache_entries:
            self.stats["total_misses"] += 1
            return None

        # 检查数据文件是否存在
        data_file = self._get_data_file(key)
        if not data_file.exists():
            # 数据文件丢失，移除索引条目
            del self.cache_entries[key]
            self.stats["current_size"] -= self.cache_entries[key].size
            self.stats["total_misses"] += 1
            self._save_index()
            return None

        try:
            # 加载数据
            with open(data_file, "rb") as f:
                data = pickle.load(f)

            # 更新命中统计
            entry = self.cache_entries[key]
            entry.hits += 1
            entry.timestamp = time.time()
            self.cache_entries[key] = entry

            self.stats["total_hits"] += 1
            return data

        except Exception as e:
            print(f"⚠️ 读取缓存数据失败: {e}")
            self.stats["total_misses"] += 1
            return None

    def put(
        self,
        category: str,
        data: Any,
        *args,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        保存数据到缓存

        Args:
            category: 缓存类别
            data: 要缓存的数据
            *args: 缓存参数
            dependencies: 依赖关系列表
            metadata: 元数据

        Returns:
            缓存键
        """
        key = self._make_cache_key(category, *args)

        # 序列化数据以计算大小
        try:
            serialized = pickle.dumps(data)
            entry_size = len(serialized)
        except Exception as e:
            print(f"⚠️ 序列化缓存数据失败: {e}")
            return key

        # 检查是否需要驱逐旧缓存
        self._evict_if_needed(entry_size)

        # 创建缓存条目
        entry = CacheEntry(
            key=key,
            data=None,  # 数据单独存储
            timestamp=time.time(),
            size=entry_size,
            hits=0,
            dependencies=dependencies or [],
            metadata=metadata or {},
        )

        # 保存数据到文件
        data_file = self._get_data_file(key)
        try:
            with open(data_file, "wb") as f:
                pickle.dump(data, f)

            # 更新索引
            self.cache_entries[key] = entry
            self.stats["current_size"] += entry_size
            self.stats["total_saves"] += 1

            # 保存索引
            self._save_index()

            return key

        except Exception as e:
            print(f"⚠️ 保存缓存数据失败: {e}")
            return key

    def invalidate(self, category: str, *args) -> bool:
        """
        使缓存条目失效

        Args:
            category: 缓存类别
            *args: 缓存参数

        Returns:
            是否成功失效
        """
        key = self._make_cache_key(category, *args)

        if key not in self.cache_entries:
            return False

        # 删除数据文件
        data_file = self._get_data_file(key)
        if data_file.exists():
            data_file.unlink()

        # 从索引中移除
        self.stats["current_size"] -= self.cache_entries[key].size
        del self.cache_entries[key]

        # 保存索引
        self._save_index()

        return True

    def invalidate_dependencies(self, filepath: str) -> int:
        """
        使依赖于此文件的所有缓存条目失效

        Args:
            filepath: 文件路径

        Returns:
            失效的缓存条目数
        """
        invalidated = 0

        for key, entry in list(self.cache_entries.items()):
            if entry.dependencies and filepath in entry.dependencies:
                if self.invalidate_by_key(key):
                    invalidated += 1

        return invalidated

    def invalidate_by_key(self, key: str) -> bool:
        """通过键使缓存失效"""
        if key not in self.cache_entries:
            return False

        data_file = self._get_data_file(key)
        if data_file.exists():
            data_file.unlink()

        self.stats["current_size"] -= self.cache_entries[key].size
        del self.cache_entries[key]
        self._save_index()

        return True

    def clear(self) -> None:
        """清空所有缓存"""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(exist_ok=True)

        self.cache_entries.clear()
        self.stats["current_size"] = 0
        self._save_index()
        print("🧹 已清空所有缓存")

    def cleanup_old_entries(self, days: int = 30) -> int:
        """
        清理旧的缓存条目

        Args:
            days: 保留天数

        Returns:
            清理的条目数
        """
        cutoff_time = time.time() - (days * 24 * 3600)
        cleaned = 0

        for key, entry in list(self.cache_entries.items()):
            if entry.timestamp < cutoff_time and entry.hits == 0:
                if self.invalidate_by_key(key):
                    cleaned += 1

        print(f"🧹 清理了 {cleaned} 个旧缓存条目")
        return cleaned

    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        hit_rate: float = 0.0
        if self.stats["total_hits"] + self.stats["total_misses"] > 0:
            hit_rate = (
                self.stats["total_hits"]
                / (self.stats["total_hits"] + self.stats["total_misses"])
                * 100
            )

        return {
            **self.stats,
            "entries_count": len(self.cache_entries),
            "hit_rate_percent": hit_rate,
            "cache_dir": str(self.cache_dir),
            "space_used_percent": (self.stats["current_size"] / self.max_size) * 100
            if self.max_size > 0
            else 0,
        }

    def print_stats(self) -> None:
        """打印缓存统计信息"""
        stats = self.get_stats()

        print("\n📊 缓存系统统计:")
        print(f"  条目数量: {stats['entries_count']}")
        print(f"  命中次数: {stats['total_hits']}")
        print(f"  未中次数: {stats['total_misses']}")
        print(f"  命中率: {stats['hit_rate_percent']:.1f}%")
        print(f"  保存次数: {stats['total_saves']}")
        print(f"  驱逐次数: {stats['total_evictions']}")
        print(f"  当前大小: {stats['current_size'] / 1024 / 1024:.2f} MB")
        print(f"  最大大小: {stats['max_size'] / 1024 / 1024:.2f} MB")
        print(f"  使用率: {stats['space_used_percent']:.1f}%")
        print(f"  缓存目录: {stats['cache_dir']}")


class FileHashCache:
    """文件哈希缓存"""

    def __init__(self, cache: CompilationCache):
        """
        初始化文件哈希缓存

        Args:
            cache: 编译缓存实例
        """
        self.cache = cache

    def get_file_hash(self, filepath: Path) -> str:
        """
        获取文件哈希值（带缓存）

        Args:
            filepath: 文件路径

        Returns:
            文件哈希值
        """
        # 首先检查缓存
        cached_hash = self.cache.get(
            "file_hash", str(filepath), filepath.stat().st_mtime
        )
        if cached_hash:
            return cached_hash

        # 计算文件哈希
        hasher = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                # 分块读取大文件
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            file_hash = hasher.hexdigest()

            # 保存到缓存
            self.cache.put(
                "file_hash", file_hash, str(filepath), filepath.stat().st_mtime
            )

            return file_hash
        except Exception as e:
            print(f"⚠️ 计算文件哈希失败: {e}")
            return ""

    def is_file_changed(self, filepath: Path, last_hash: str) -> bool:
        """
        检查文件是否已更改

        Args:
            filepath: 文件路径
            last_hash: 上次的哈希值

        Returns:
            文件是否已更改
        """
        current_hash = self.get_file_hash(filepath)
        return current_hash != last_hash


def test_cache_system():
    """测试缓存系统"""
    print("🧪 测试缓存系统...")

    # 创建缓存实例
    cache = CompilationCache(max_size_mb=10)

    # 测试基本功能
    test_data = {"name": "test", "value": 42, "list": [1, 2, 3]}

    # 保存数据
    key = cache.put("test", test_data, "arg1", "arg2")
    print(f"  ✅ 保存数据: {key[:8]}...")

    # 获取数据（应该命中）
    retrieved = cache.get("test", "arg1", "arg2")
    assert retrieved == test_data, "获取的数据不匹配"
    print(f"  ✅ 缓存命中: {retrieved}")

    # 获取不存在的数据（应该未中）
    missed = cache.get("test", "nonexistent")
    assert missed is None, "应该未命中"
    print("  ✅ 缓存未中: None")

    # 测试失效功能
    cache.invalidate("test", "arg1", "arg2")
    after_invalidate = cache.get("test", "arg1", "arg2")
    assert after_invalidate is None, "失效后应该未命中"
    print("  ✅ 缓存失效成功")

    # 测试统计
    stats = cache.get_stats()
    assert stats["total_hits"] == 1
    assert stats["total_misses"] == 1
    assert stats["total_saves"] == 1
    print("  ✅ 统计信息正确")

    # 测试文件哈希缓存
    file_cache = FileHashCache(cache)
    test_file = Path("test_cache.txt")

    try:
        # 创建测试文件
        test_file.write_text("Hello, Cache!")

        # 获取哈希
        hash1 = file_cache.get_file_hash(test_file)
        print(f"  ✅ 文件哈希1: {hash1[:8]}...")

        # 再次获取应该从缓存获取
        hash2 = file_cache.get_file_hash(test_file)
        assert hash1 == hash2, "哈希值应该相同"
        print(f"  ✅ 文件哈希2: {hash2[:8]}... (缓存)")

        # 修改文件
        test_file.write_text("Hello, Modified Cache!")

        # 检查文件是否已更改
        changed = file_cache.is_file_changed(test_file, hash1)
        assert changed, "文件应该已更改"
        print("  ✅ 检测到文件更改")

    finally:
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()

    # 打印最终统计
    cache.print_stats()
    print("🎉 缓存系统测试通过！")


if __name__ == "__main__":
    test_cache_system()

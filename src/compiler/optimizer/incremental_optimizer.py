# -*- coding: utf-8 -*-
"""
IncrementalOptimizer: 增量优化器

提供文件变更检测、受影响文件分析和增量重编译优化。
"""

import time
from pathlib import Path
from typing import Dict, List, Set, Any
from collections import defaultdict


class IncrementalOptimizer:
    """增量优化器"""

    def __init__(self, cache_system):
        """
        初始化增量优化器

        Args:
            cache_system: 缓存系统实例
        """
        self.cache = cache_system
        self.dependency_graph = {}
        self.file_modification_times = {}

    def analyze_changes(self, files: List[Path]) -> Dict[str, List[Path]]:
        """
        分析文件变更

        Args:
            files: 文件列表

        Returns:
            变更分析结果
        """
        changes: Dict[str, List[Path]] = {
            'modified': [],
            'added': [],
            'deleted': [],
            'unchanged': []
        }

        current_time = time.time()

        for file in files:
            if not file.exists():
                changes['deleted'].append(file)
                continue

            mtime = file.stat().st_mtime
            last_mtime = self.file_modification_times.get(file)

            if last_mtime is None:
                changes['added'].append(file)
            elif mtime > last_mtime:
                changes['modified'].append(file)
            else:
                changes['unchanged'].append(file)

            self.file_modification_times[file] = mtime

        return changes

    def get_affected_files(self, changed_files: List[Path], dependency_graph: Dict[str, List[str]]) -> Set[Path]:
        """
        获取受变更影响的所有文件

        Args:
            changed_files: 变更的文件列表
            dependency_graph: 依赖图

        Returns:
            受影响的所有文件集合
        """
        affected = set()

        # 构建反向依赖图
        reverse_graph = defaultdict(set)
        for module, deps in dependency_graph.items():
            for dep in deps:
                reverse_graph[dep].add(module)

        # 查找所有受影响的模块
        queue = [f.stem for f in changed_files]
        visited = set()

        while queue:
            module = queue.pop(0)
            if module in visited:
                continue

            visited.add(module)

            # 添加当前模块
            affected.add(Path(f"{module}.zhc"))

            # 添加依赖此模块的所有模块
            if module in reverse_graph:
                for dependent in reverse_graph[module]:
                    if dependent not in visited:
                        queue.append(dependent)

        return affected

    def optimize_recompilation(self, files: List[Path], compile_func) -> Dict[Path, Any]:
        """
        优化重新编译过程

        Args:
            files: 文件列表
            compile_func: 编译函数

        Returns:
            编译结果
        """
        # 分析变更
        changes = self.analyze_changes(files)

        # 获取受影响的所有文件
        all_affected = self.get_affected_files(
            changes['modified'] + changes['added'],
            self.dependency_graph
        )

        # 只编译受影响的文件
        files_to_compile = list(all_affected)

        print(f"🔄 增量编译:")
        print(f"  修改文件: {len(changes['modified'])}")
        print(f"  新增文件: {len(changes['added'])}")
        print(f"  删除文件: {len(changes['deleted'])}")
        print(f"  未变文件: {len(changes['unchanged'])}")
        print(f"  需要编译: {len(files_to_compile)}/{len(files)}")

        # 编译受影响文件
        results = {}
        for file in files_to_compile:
            results[file] = compile_func(file)

        return results

# -*- coding: utf-8 -*-
"""
AlgorithmOptimizer: 算法优化器

提供依赖图优化（压缩传递依赖、层级计算、冗余依赖移除）和内存使用优化。
"""

from typing import Dict, List, Tuple, Any


class AlgorithmOptimizer:
    """算法优化器"""

    @staticmethod
    def optimize_dependency_resolution(dependency_graph: Dict[str, List[str]]) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
        """
        优化依赖解析算法

        Args:
            dependency_graph: 原始依赖图

        Returns:
            (优化后的依赖图, 节点层级信息)
        """
        # 1. 压缩传递依赖
        compressed_graph = AlgorithmOptimizer._compress_transitive_dependencies(dependency_graph)

        # 2. 计算节点层级（拓扑深度）
        node_levels = AlgorithmOptimizer._calculate_node_levels(compressed_graph)

        # 3. 按层级排序依赖
        sorted_graph = AlgorithmOptimizer._sort_dependencies_by_level(compressed_graph, node_levels)

        # 4. 移除冗余依赖
        optimized_graph = AlgorithmOptimizer._remove_redundant_dependencies(sorted_graph)

        return optimized_graph, node_levels

    @staticmethod
    def _compress_transitive_dependencies(graph: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """压缩传递依赖"""
        compressed = {}

        for node, deps in graph.items():
            # 计算传递闭包
            transitive_closure = set(deps)
            stack = list(deps)

            while stack:
                current = stack.pop()
                if current in graph:
                    for indirect in graph[current]:
                        if indirect not in transitive_closure:
                            transitive_closure.add(indirect)
                            stack.append(indirect)

            # 移除可以通过其他依赖间接满足的依赖
            direct_deps = set(deps)
            for dep in deps:
                if dep in graph:
                    for indirect in graph[dep]:
                        if indirect in transitive_closure and indirect in direct_deps:
                            direct_deps.discard(indirect)

            compressed[node] = list(direct_deps)

        return compressed

    @staticmethod
    def _calculate_node_levels(graph: Dict[str, List[str]]) -> Dict[str, int]:
        """计算节点层级（拓扑深度）"""
        # 计算入度
        in_degree = {node: 0 for node in graph}
        for node, deps in graph.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1
                else:
                    in_degree[dep] = 1

        # 初始化层级
        levels = {node: 0 for node in graph}

        # 使用队列进行拓扑排序并计算层级
        queue = [node for node in graph if in_degree[node] == 0]

        while queue:
            node = queue.pop(0)

            # 更新后继节点的层级
            if node in graph:
                for neighbor in graph[node]:
                    levels[neighbor] = max(levels[neighbor], levels[node] + 1)
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        return levels

    @staticmethod
    def _sort_dependencies_by_level(graph: Dict[str, List[str]], levels: Dict[str, int]) -> Dict[str, List[str]]:
        """按层级排序依赖"""
        sorted_graph = {}

        for node, deps in graph.items():
            # 按依赖的层级排序
            sorted_deps = sorted(deps, key=lambda x: levels.get(x, 0))
            sorted_graph[node] = sorted_deps

        return sorted_graph

    @staticmethod
    def _remove_redundant_dependencies(graph: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """移除冗余依赖"""
        optimized = {}

        for node, deps in graph.items():
            # 检查每个依赖是否必要
            necessary_deps = []
            reachable = set()

            # 构建除当前依赖外的可达集合
            for i, dep in enumerate(deps):
                other_deps = deps[:i] + deps[i+1:]

                # 计算通过其他依赖能到达的节点
                temp_reachable = set(other_deps)
                stack = list(other_deps)

                while stack:
                    current = stack.pop()
                    if current in graph:
                        for neighbor in graph[current]:
                            if neighbor not in temp_reachable:
                                temp_reachable.add(neighbor)
                                stack.append(neighbor)

                # 如果当前依赖不在可达集合中，则是必要的
                if dep not in temp_reachable:
                    necessary_deps.append(dep)
                    reachable.add(dep)

            optimized[node] = necessary_deps

        return optimized

    @staticmethod
    def optimize_memory_usage(data_structure: Any) -> Any:
        """
        优化数据结构的内存使用

        Args:
            data_structure: 原始数据结构

        Returns:
            优化后的数据结构
        """
        if isinstance(data_structure, dict):
            return {k: AlgorithmOptimizer.optimize_memory_usage(v)
                   for k, v in data_structure.items()}

        elif isinstance(data_structure, list):
            if len(data_structure) > 0 and all(isinstance(x, type(data_structure[0])) for x in data_structure):
                if isinstance(data_structure[0], (int, float)):
                    return list(data_structure)
            return [AlgorithmOptimizer.optimize_memory_usage(x) for x in data_structure]

        elif isinstance(data_structure, set):
            if len(data_structure) < 10:
                return frozenset(data_structure)
            return set(data_structure)

        else:
            return data_structure

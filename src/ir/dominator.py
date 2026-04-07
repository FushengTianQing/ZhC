#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZhC IR - Lengauer-Tarjan 支配树算法

实现 O(N α(N)) 复杂度的支配树构建算法。
Lengauer-Tarjan 算法比迭代算法更快，特别适合大型控制流图。

作者: 阿福
日期: 2026-04-08

参考文献:
    Lengauer, T., & Tarjan, R. E. (1979). 
    A fast algorithm for finding dominators in a flowgraph.
    ACM Transactions on Programming Languages and Systems, 1(1), 121-141.
"""

from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict


class LengauerTarjanDominator:
    """
    Lengauer-Tarjan 支配树算法实现
    
    时间复杂度: O(N α(N))，其中 α 是反阿克曼函数
    空间复杂度: O(N)
    
    使用方法:
        builder = LengauerTarjanDominator()
        builder.build(entry_block, all_blocks)
        idom = builder.get_immediate_dominators()
    """
    
    def __init__(self):
        # DFS 编号相关
        self.vertex: List[str] = []  # DFS 编号 -> 基本块标签
        self.dfs_num: Dict[str, int] = {}  # 基本块标签 -> DFS 编号
        
        # 半支配者和支配者
        self.semi: Dict[str, str] = {}  # 基本块 -> 半支配者
        self.idom: Dict[str, str] = {}  # 基本块 -> 直接支配者
        self.ancestor: Dict[str, str] = {}  # 并查集祖先
        self.label: Dict[str, str] = {}  # 并查集标签
        
        # 辅助数据结构
        self.parent: Dict[str, str] = {}  # DFS 树中的父节点
        self.bucket: Dict[str, Set[str]] = defaultdict(set)  # 半支配者相同的节点集合
        
        # 控制流图
        self.pred: Dict[str, List[str]] = defaultdict(list)  # 前驱
        self.succ: Dict[str, List[str]] = defaultdict(list)  # 后继
        
        # 支配树结构
        self.dom_children: Dict[str, List[str]] = defaultdict(list)  # 支配树子节点
        self.dom_depth: Dict[str, int] = {}  # 支配树深度
    
    def build(
        self,
        entry: str,
        blocks: Dict[str, Tuple[List[str], List[str]]]
    ) -> Dict[str, str]:
        """
        构建支配树
        
        Args:
            entry: 入口基本块标签
            blocks: 基本块字典 {label: (predecessors, successors)}
        
        Returns:
            直接支配者字典 {block: immediate_dominator}
        """
        # 初始化
        self._initialize(entry, blocks)
        
        # 步骤 1: DFS 遍历，编号所有节点
        self._dfs(entry)
        
        # 步骤 2: 计算半支配者
        # 按逆 DFS 顺序处理
        for i in range(len(self.vertex) - 1, 0, -1):
            w = self.vertex[i]
            
            # 计算半支配者
            for v in self.pred[w]:
                # 只处理可达节点
                if v not in self.dfs_num:
                    continue
                u = self._eval(v)
                if self.dfs_num[self.semi[u]] < self.dfs_num[self.semi[w]]:
                    self.semi[w] = self.semi[u]
            
            # 将 w 加入 semi[w] 的 bucket
            self.bucket[self.semi[w]].add(w)
            
            # 链接 parent[w] 到并查集
            self._link(self.parent[w], w)
            
            # 处理 bucket[parent[w]]
            for v in list(self.bucket[self.parent[w]]):
                u = self._eval(v)
                if self.semi[u] == self.semi[v]:
                    self.idom[v] = self.parent[w]
                else:
                    self.idom[v] = u
        
        # 步骤 3: 计算支配者
        for i in range(1, len(self.vertex)):
            w = self.vertex[i]
            if w in self.idom and w in self.idom[w] and self.idom[w] != self.semi[w]:
                self.idom[w] = self.idom[self.idom[w]]
        
        # 入口节点支配自己
        self.idom[entry] = entry
        
        # 构建支配树结构
        self._build_dom_tree(entry)
        
        return dict(self.idom)
    
    def _initialize(self, entry: str, blocks: Dict[str, Tuple[List[str], List[str]]]):
        """初始化数据结构"""
        self.vertex.clear()
        self.dfs_num.clear()
        self.semi.clear()
        self.idom.clear()
        self.ancestor.clear()
        self.label.clear()
        self.parent.clear()
        self.bucket.clear()
        self.pred.clear()
        self.succ.clear()
        self.dom_children.clear()
        self.dom_depth.clear()
        
        # 构建前驱后继图
        for label, (preds, succs) in blocks.items():
            self.pred[label] = list(preds)
            self.succ[label] = list(succs)
    
    def _dfs(self, entry: str):
        """DFS 遍历，编号所有节点"""
        stack = [entry]
        visited = set()
        
        while stack:
            v = stack.pop()
            
            if v in visited:
                continue
            
            visited.add(v)
            
            # 分配 DFS 编号
            n = len(self.vertex)
            self.dfs_num[v] = n
            self.vertex.append(v)
            
            # 初始化半支配者为自身
            self.semi[v] = v
            self.label[v] = v
            self.ancestor[v] = None
            
            # 遍历后继
            for w in self.succ[v]:
                if w not in visited:
                    self.parent[w] = v
                    stack.append(w)
    
    def _compress(self, v: str):
        """压缩并查集路径"""
        # 检查节点是否在并查集中
        if v not in self.ancestor:
            return
        if self.ancestor[v] is None:
            return
        if self.ancestor[self.ancestor[v]] is None:
            return

        self._compress(self.ancestor[v])

        if self.ancestor[v] in self.dfs_num and self.ancestor[self.ancestor[v]] in self.dfs_num:
            if self.dfs_num[self.semi[self.label[self.ancestor[v]]]] < self.dfs_num[self.semi[self.label[v]]]:
                self.label[v] = self.label[self.ancestor[v]]

        if self.ancestor[self.ancestor[v]] in self.ancestor:
            self.ancestor[v] = self.ancestor[self.ancestor[v]]

    def _eval(self, v: str) -> str:
        """评估并查集"""
        # 检查节点是否在并查集中
        if v not in self.ancestor:
            return v
        if self.ancestor[v] is None:
            return self.label[v]

        self._compress(v)

        if self.ancestor[v] in self.dfs_num and self.ancestor[v] in self.label:
            if self.dfs_num[self.semi[self.label[self.ancestor[v]]]] >= self.dfs_num[self.semi[self.label[v]]]:
                return self.label[v]

        if self.ancestor[v] in self.label:
            return self.label[self.ancestor[v]]

        return v
    
    def _link(self, v: str, w: str):
        """链接两个节点"""
        self.ancestor[w] = v
    
    def _build_dom_tree(self, entry: str):
        """构建支配树结构"""
        # 设置入口深度
        self.dom_depth[entry] = 0

        # 按 DFS 顺序遍历顶点列表，确保父节点先被处理
        for node in self.vertex:
            if node == entry:
                continue
            parent = self.idom.get(node)
            if parent and parent != node:
                self.dom_children[parent].append(node)
                self.dom_depth[node] = self.dom_depth.get(parent, 0) + 1
    
    def get_immediate_dominators(self) -> Dict[str, str]:
        """获取直接支配者字典"""
        return dict(self.idom)
    
    def get_dominator_tree(self) -> Dict[str, List[str]]:
        """获取支配树（子节点列表）"""
        return dict(self.dom_children)
    
    def get_dominator_depth(self) -> Dict[str, int]:
        """获取支配树深度"""
        return dict(self.dom_depth)
    
    def dominates(self, a: str, b: str) -> bool:
        """检查 a 是否支配 b"""
        # a 支配 b 当且仅当 a 在 b 的支配链上
        current = b
        while current != self.idom.get(current):
            if current == a:
                return True
            current = self.idom.get(current)
            if current is None:
                break
        return current == a
    
    def get_dominators(self, block: str) -> Set[str]:
        """获取 block 的所有支配者"""
        doms = {block}
        current = block
        while current != self.idom.get(current):
            parent = self.idom.get(current)
            if parent is None or parent == current:
                break
            doms.add(parent)
            current = parent
        return doms


def build_dominator_tree_iterative(
    entry: str,
    blocks: Dict[str, Tuple[List[str], List[str]]]
) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
    """
    使用迭代算法构建支配树（简单但较慢）
    
    时间复杂度: O(N²) 最坏情况，但实践中通常很快收敛
    
    Args:
        entry: 入口基本块标签
        blocks: 基本块字典 {label: (predecessors, successors)}
    
    Returns:
        (idom, dom_children): 直接支配者和支配树子节点
    """
    # 初始化
    idom = {entry: entry}
    doms = {entry: {entry}}
    
    # 所有基本块
    all_blocks = set(blocks.keys())
    
    # 迭代直到收敛
    changed = True
    max_iterations = 100
    iteration = 0
    
    while changed and iteration < max_iterations:
        changed = False
        iteration += 1
        
        for block in all_blocks:
            if block == entry:
                continue
            
            # 获取前驱
            preds = blocks[block][0]
            if not preds:
                continue
            
            # 计算新的支配集合
            new_doms = None
            for pred in preds:
                if pred in doms:
                    if new_doms is None:
                        new_doms = doms[pred].copy()
                    else:
                        new_doms &= doms[pred]
            
            if new_doms is None:
                new_doms = {block}
            else:
                new_doms.add(block)
            
            # 检查是否变化
            if doms.get(block) != new_doms:
                doms[block] = new_doms
                changed = True
    
    # 计算直接支配者
    dom_children = defaultdict(list)
    for block in all_blocks:
        if block == entry:
            continue
        
        # 直接支配者是支配集合中深度最大的
        block_doms = doms.get(block, {block}) - {block}
        if block_doms:
            # 选择深度最大的（最接近的）
            idom[block] = max(block_doms, key=lambda x: len(doms.get(x, {x})))
            dom_children[idom[block]].append(block)
        else:
            idom[block] = entry
            dom_children[entry].append(block)
    
    return idom, dict(dom_children)
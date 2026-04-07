#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量AST更新器 - Incremental AST Updater

功能：
1. 计算新旧AST的差异（树编辑距离）
2. 只更新变化的部分AST
3. 复用未变化的子树

基于 parser.ast_nodes.ASTNode（统一AST体系），
不再自定义AST节点类。

性能优化：
- 避免全量重新解析
- 复用现有节点
- 增量更新缓存

作者：远
日期：2026-04-03
更新：2026-04-03 统一使用 parser.ast_nodes.ASTNode
"""

from typing import List, Dict, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from enum import Enum

# 使用统一AST体系
from ..parser.ast_nodes import ASTNode, ASTNodeType


class DiffType(Enum):
    """差异类型"""
    UPDATE = "update"      # 更新节点
    INSERT = "insert"      # 插入节点
    DELETE = "delete"      # 删除节点
    MOVE = "move"         # 移动节点
    KEEP = "keep"         # 保持不变


@dataclass
class ASTDiff:
    """AST差异"""
    diff_type: DiffType
    node_id: str
    old_node: Optional[ASTNode] = None
    new_node: Optional[ASTNode] = None
    parent_id: Optional[str] = None
    position: int = 0  # 在父节点中的位置
    children_diff: List['ASTDiff'] = field(default_factory=list)
    
    def __str__(self) -> str:
        if self.diff_type == DiffType.KEEP:
            return f"KEEP {self.node_id}"
        elif self.diff_type == DiffType.UPDATE:
            old_type = self.old_node.node_type.name if self.old_node else "?"
            new_type = self.new_node.node_type.name if self.new_node else "?"
            return f"UPDATE {self.node_id}: {old_type} -> {new_type}"
        elif self.diff_type == DiffType.INSERT:
            new_type = self.new_node.node_type.name if self.new_node else "?"
            return f"INSERT {new_type} @ {self.parent_id}[{self.position}]"
        elif self.diff_type == DiffType.DELETE:
            old_type = self.old_node.node_type.name if self.old_node else "?"
            return f"DELETE {old_type} ({self.node_id})"
        elif self.diff_type == DiffType.MOVE:
            return f"MOVE {self.node_id} to {self.parent_id}[{self.position}]"
        return f"UNKNOWN {self.node_id}"


@dataclass
class EditOperation:
    """编辑操作"""
    operation: str  # 'insert', 'delete', 'relabel', 'keep'
    old_node: Optional[ASTNode]
    new_node: Optional[ASTNode]
    cost: int = 1


class TreeEditDistance:
    """树编辑距离计算器
    
    使用动态规划计算两棵树的最小编辑距离
    算法复杂度: O(n^3), n为节点数
    
    基于 ASTNode.get_children() 和 ASTNode.get_hash() 工作。
    """
    
    # 操作成本
    INSERT_COST = 1
    DELETE_COST = 1
    UPDATE_COST = 1  # 标签/值改变
    
    def __init__(self):
        self.cache: Dict[Tuple[str, str], int] = {}
        self.edit_script: List[EditOperation] = []
    
    def compute_distance(self, old_node: Optional[ASTNode], 
                        new_node: Optional[ASTNode]) -> int:
        """计算树编辑距离"""
        if old_node is None and new_node is None:
            return 0
        
        if old_node is None:
            return self._subtree_cost(new_node, self.INSERT_COST)
        
        if new_node is None:
            return self._subtree_cost(old_node, self.DELETE_COST)
        
        return self._compute_recursive(old_node, new_node)
    
    def _compute_recursive(self, old_node: ASTNode, new_node: ASTNode) -> int:
        """递归计算编辑距离（带缓存）"""
        key = (old_node.node_id, new_node.node_id)
        
        if key in self.cache:
            return self.cache[key]
        
        # 如果节点类型不同，需要替换
        if old_node.node_type != new_node.node_type:
            cost = self._subtree_cost(old_node, self.DELETE_COST)
            cost += self._subtree_cost(new_node, self.INSERT_COST)
            self.cache[key] = cost
            return cost
        
        # 节点类型相同，用哈希判断是否完全相同
        if old_node.get_hash() == new_node.get_hash():
            self.cache[key] = 0
            return 0
        
        # 哈希不同，计算子树距离
        cost = self._compute_child_distance(
            old_node.get_children(), 
            new_node.get_children()
        )
        
        # 即使子节点距离为0，本节点内容已变，至少需要 UPDATE_COST
        cost = max(cost, self.UPDATE_COST)
        
        self.cache[key] = cost
        return cost
    
    def _subtree_cost(self, node: Optional[ASTNode], operation_cost: int) -> int:
        """计算子树的操作成本"""
        if node is None:
            return 0
        
        cost = operation_cost
        for child in node.get_children():
            cost += self._subtree_cost(child, operation_cost)
        
        return cost
    
    def _compute_child_distance(self, old_children: List[ASTNode],
                                new_children: List[ASTNode]) -> int:
        """计算子节点列表的距离（动态规划）"""
        if not old_children:
            return len(new_children) * self.INSERT_COST
        
        if not new_children:
            return len(old_children) * self.DELETE_COST
        
        n = len(old_children)
        m = len(new_children)
        
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        
        for i in range(n + 1):
            dp[i][0] = i * self.DELETE_COST
        for j in range(m + 1):
            dp[0][j] = j * self.INSERT_COST
        
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                old_child = old_children[i - 1]
                new_child = new_children[j - 1]
                
                match_cost = self._compute_recursive(old_child, new_child)
                dp[i][j] = min(
                    dp[i - 1][j - 1] + match_cost,
                    dp[i - 1][j] + self.DELETE_COST,
                    dp[i][j - 1] + self.INSERT_COST
                )
        
        return dp[n][m]
    
    def get_edit_script(self, old_node: Optional[ASTNode],
                        new_node: Optional[ASTNode]) -> List[EditOperation]:
        """获取编辑脚本"""
        self.edit_script.clear()
        self._compute_edit_script_recursive(old_node, new_node)
        return self.edit_script
    
    def _compute_edit_script_recursive(self, old_node: Optional[ASTNode],
                                       new_node: Optional[ASTNode]):
        """递归生成编辑脚本"""
        if old_node is None and new_node is None:
            return
        
        if old_node is None:
            self._insert_subtree(new_node)
            return
        
        if new_node is None:
            self._delete_subtree(old_node)
            return
        
        if old_node.node_type != new_node.node_type:
            self._delete_subtree(old_node)
            self._insert_subtree(new_node)
            return
        
        self.edit_script.append(EditOperation('relabel', old_node, new_node, 0))
        self._match_children(old_node.get_children(), new_node.get_children())
    
    def _insert_subtree(self, node: Optional[ASTNode]):
        if node is None:
            return
        for child in node.get_children():
            self._insert_subtree(child)
        self.edit_script.append(EditOperation('insert', None, node, self.INSERT_COST))
    
    def _delete_subtree(self, node: Optional[ASTNode]):
        if node is None:
            return
        for child in node.get_children():
            self._delete_subtree(child)
        self.edit_script.append(EditOperation('delete', node, None, self.DELETE_COST))
    
    def _match_children(self, old_children: List[ASTNode],
                       new_children: List[ASTNode]):
        """匹配子节点"""
        n = len(old_children)
        m = len(new_children)
        
        dist = [[0] * m for _ in range(n)]
        for i in range(n):
            for j in range(m):
                dist[i][j] = self._compute_recursive(old_children[i], new_children[j])
        
        used_old: Set[int] = set()
        used_new: Set[int] = set()
        
        # 优先匹配距离为0的节点（完全相同）
        for i in range(n):
            for j in range(m):
                if dist[i][j] == 0 and i not in used_old and j not in used_new:
                    self._compute_edit_script_recursive(old_children[i], new_children[j])
                    used_old.add(i)
                    used_new.add(j)
        
        # 处理剩余节点
        old_remaining = [old_children[i] for i in range(n) if i not in used_old]
        new_remaining = [new_children[j] for j in range(m) if j not in used_new]
        
        for old_child in old_remaining:
            self._delete_subtree(old_child)
        for new_child in new_remaining:
            self._insert_subtree(new_child)


class IncrementalASTUpdater:
    """增量AST更新器
    
    核心功能：
    1. 计算新旧AST的差异
    2. 生成最小编辑序列
    3. 只更新变化的部分
    
    基于 parser.ast_nodes.ASTNode 工作。
    通过 ASTNode.get_children() 遍历子节点，
    通过 ASTNode.get_hash() 判断节点是否变化，
    通过 ASTNode.parent 追溯父节点。
    """
    
    def __init__(self):
        self.tree_edit_distance = TreeEditDistance()
        self.diffs: List[ASTDiff] = []
        self.node_map: Dict[str, ASTNode] = {}
    
    def compute_diff(self, old_ast: ASTNode, new_ast: ASTNode) -> List[ASTDiff]:
        """计算新旧AST的差异"""
        self.diffs.clear()
        self.node_map.clear()
        self._build_node_map(old_ast)
        self._compute_diff_recursive(old_ast, new_ast, None, 0)
        return self.diffs
    
    def _build_node_map(self, node: Optional[ASTNode]):
        """构建 node_id -> ASTNode 映射"""
        if node is None:
            return
        self.node_map[node.node_id] = node
        for child in node.get_children():
            self._build_node_map(child)
    
    def _compute_diff_recursive(self, old_node: Optional[ASTNode],
                                new_node: Optional[ASTNode],
                                parent_id: Optional[str],
                                position: int):
        """递归计算差异"""
        if old_node is None and new_node is None:
            return
        
        if old_node is None:
            diff = ASTDiff(
                diff_type=DiffType.INSERT,
                node_id=new_node.node_id,
                new_node=new_node,
                parent_id=parent_id,
                position=position
            )
            self.diffs.append(diff)
            self._add_children_diff(new_node)
            return
        
        if new_node is None:
            diff = ASTDiff(
                diff_type=DiffType.DELETE,
                node_id=old_node.node_id,
                old_node=old_node,
                parent_id=parent_id,
                position=position
            )
            self.diffs.append(diff)
            return
        
        # 比较节点类型
        if old_node.node_type != new_node.node_type:
            diff = ASTDiff(
                diff_type=DiffType.UPDATE,
                node_id=old_node.node_id,
                old_node=old_node,
                new_node=new_node,
                parent_id=parent_id,
                position=position
            )
            self.diffs.append(diff)
            return
        
        # 比较节点哈希
        if old_node.get_hash() != new_node.get_hash():
            diff = ASTDiff(
                diff_type=DiffType.UPDATE,
                node_id=old_node.node_id,
                old_node=old_node,
                new_node=new_node,
                parent_id=parent_id,
                position=position
            )
            self.diffs.append(diff)
        
        # 比较子节点
        old_children = old_node.get_children()
        new_children = new_node.get_children()
        self._compute_children_diff(old_children, new_children, old_node.node_id)
    
    def _compute_children_diff(self, old_children: List[ASTNode],
                               new_children: List[ASTNode],
                               parent_id: str):
        """计算子节点的差异"""
        # 使用哈希来匹配新旧子节点（而非简单的 node_type 映射）
        old_by_hash: Dict[str, ASTNode] = {}
        new_by_hash: Dict[str, ASTNode] = {}
        
        for child in old_children:
            old_by_hash[child.get_hash()] = child
        for child in new_children:
            new_by_hash[child.get_hash()] = child
        
        old_hashes = set(old_by_hash.keys())
        new_hashes = set(new_by_hash.keys())
        
        # 保持不变的节点
        kept_hashes = old_hashes & new_hashes
        
        # 新增的节点
        for i, new_child in enumerate(new_children):
            if new_child.get_hash() not in old_hashes:
                diff = ASTDiff(
                    diff_type=DiffType.INSERT,
                    node_id=new_child.node_id,
                    new_node=new_child,
                    parent_id=parent_id,
                    position=i
                )
                self.diffs.append(diff)
                self._add_children_diff(new_child)
        
        # 删除的节点
        deleted_children = [
            child for child in old_children 
            if child.get_hash() not in new_hashes
        ]
        for old_child in deleted_children:
            diff = ASTDiff(
                diff_type=DiffType.DELETE,
                node_id=old_child.node_id,
                old_node=old_child,
                parent_id=parent_id,
                position=0
            )
            self.diffs.append(diff)
    
    def _add_children_diff(self, node: Optional[ASTNode]):
        """添加子节点的差异（INSERT递归）"""
        if node is None:
            return
        for i, child in enumerate(node.get_children()):
            diff = ASTDiff(
                diff_type=DiffType.INSERT,
                node_id=child.node_id,
                new_node=child,
                parent_id=node.node_id,
                position=i
            )
            self.diffs.append(diff)
            self._add_children_diff(child)
    
    def apply_diff(self, root: ASTNode, diffs: List[ASTDiff]) -> ASTNode:
        """应用差异到AST"""
        self.node_map.clear()
        self._build_node_map(root)
        
        for diff in diffs:
            if diff.diff_type == DiffType.UPDATE:
                self._apply_update(diff)
            elif diff.diff_type == DiffType.INSERT:
                self._apply_insert(diff)
            elif diff.diff_type == DiffType.DELETE:
                self._apply_delete(diff)
        
        return root
    
    def _apply_update(self, diff: ASTDiff):
        """应用更新 — 标记已变化的节点"""
        node = self.node_map.get(diff.node_id)
        if node is None or diff.new_node is None:
            return
        
        # 通过 attributes 标记节点已更新（保留节点对象引用）
        node.set_attribute('_dirty', True)
        node.set_attribute('_new_hash', diff.new_node.get_hash())
    
    def _apply_insert(self, diff: ASTDiff):
        """应用插入"""
        if diff.new_node is None:
            return
        
        parent = self.node_map.get(diff.parent_id) if diff.parent_id else None
        if parent is None:
            return
        
        # 设置parent引用
        diff.new_node.parent = parent
        
        # 通过 attributes 标记父节点需要重新构建子列表
        parent.set_attribute('_children_modified', True)
    
    def _apply_delete(self, diff: ASTDiff):
        """应用删除"""
        node = self.node_map.get(diff.node_id)
        if node is None:
            return
        
        # 标记父节点需要重新构建子列表
        if node.parent is not None:
            node.parent.set_attribute('_children_modified', True)
    
    def get_update_statistics(self, diffs: List[ASTDiff]) -> Dict[str, int]:
        """获取更新统计"""
        stats = {
            'update': 0,
            'insert': 0,
            'delete': 0,
            'move': 0,
            'keep': 0,
        }
        
        for diff in diffs:
            stats[diff.diff_type.value] = stats.get(diff.diff_type.value, 0) + 1
        
        return stats
    
    def generate_report(self, diffs: List[ASTDiff]) -> str:
        """生成差异报告"""
        stats = self.get_update_statistics(diffs)
        
        lines = [
            "=" * 60,
            "AST增量更新报告",
            "=" * 60,
            "",
            f"总差异数: {len(diffs)}",
            "",
            "差异统计:",
            f"  更新: {stats['update']}",
            f"  插入: {stats['insert']}",
            f"  删除: {stats['delete']}",
            f"  移动: {stats['move']}",
            f"  保持: {stats['keep']}",
            "",
            "详细差异:",
            "-" * 60,
        ]
        
        for diff in diffs:
            if diff.diff_type != DiffType.KEEP:
                lines.append(f"  {diff}")
        
        lines.extend(["", "=" * 60])
        return "\n".join(lines)


# 兼容性别名
ASTDiffCalculator = IncrementalASTUpdater

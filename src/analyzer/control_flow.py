#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
控制流分析器 - Control Flow Analyzer

功能：
1. 构建控制流图（CFG）
2. 分析基本块
3. 检测不可达代码
4. 识别循环结构
5. 计算复杂度指标

作者：阿福
日期：2026-04-03
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

# graphviz 是可选依赖，用于可视化
try:
    from graphviz import Digraph
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False
    Digraph = None


class NodeType(Enum):
    """控制流节点类型"""
    ENTRY = "entry"         # 入口节点
    EXIT = "exit"          # 出口节点
    BASIC_BLOCK = "basic"  # 基本块
    BRANCH = "branch"      # 分支节点
    LOOP = "loop"          # 循环节点
    MERGE = "merge"        # 合并节点


class EdgeType(Enum):
    """控制流边类型"""
    NORMAL = "normal"      # 正常流
    TRUE = "true"          # 条件为真
    FALSE = "false"        # 条件为假
    LOOP_BACK = "loop"     # 循环回边
    BREAK = "break"        # break语句
    CONTINUE = "continue"  # continue语句
    RETURN = "return"      # return语句


@dataclass
class BasicBlock:
    """基本块"""
    id: str
    statements: List[dict] = field(default_factory=list)
    start_line: int = 0
    end_line: int = 0
    is_reachable: bool = True
    dominates: Set[str] = field(default_factory=set)
    post_dominates: Set[str] = field(default_factory=set)
    
    def add_statement(self, stmt: dict):
        """添加语句"""
        self.statements.append(stmt)
        if not self.start_line:
            self.start_line = stmt.get('line', 0)
        self.end_line = stmt.get('line', 0)
    
    def is_empty(self) -> bool:
        """是否为空基本块"""
        return len(self.statements) == 0


@dataclass
class CFGNode:
    """控制流图节点"""
    id: str
    node_type: NodeType
    basic_block: Optional[BasicBlock] = None
    successors: List[Tuple[str, EdgeType]] = field(default_factory=list)
    predecessors: List[Tuple[str, EdgeType]] = field(default_factory=list)
    
    def add_successor(self, node_id: str, edge_type: EdgeType):
        """添加后继节点"""
        self.successors.append((node_id, edge_type))
    
    def add_predecessor(self, node_id: str, edge_type: EdgeType):
        """添加前驱节点"""
        self.predecessors.append((node_id, edge_type))


@dataclass
class LoopInfo:
    """循环信息"""
    header_id: str           # 循环头节点
    body_ids: Set[str]       # 循环体节点
    back_edge_from: str      # 回边起点
    nesting_level: int       # 嵌套层级
    is_infinite: bool = False  # 是否无限循环


@dataclass
class FlowIssue:
    """控制流问题"""
    issue_type: str
    message: str
    line_number: int
    severity: str  # "error", "warning", "info"
    suggestion: str


class ControlFlowGraph:
    """控制流图"""
    
    def __init__(self, func_name: str):
        self.func_name = func_name
        self.nodes: Dict[str, CFGNode] = {}
        self.entry_id: Optional[str] = None
        self.exit_id: Optional[str] = None
        self.loops: List[LoopInfo] = []
        self.issues: List[FlowIssue] = []
        self._node_counter = 0
    
    def create_node(self, node_type: NodeType, basic_block: Optional[BasicBlock] = None) -> str:
        """创建节点"""
        node_id = f"n{self._node_counter}"
        self._node_counter += 1
        
        node = CFGNode(
            id=node_id,
            node_type=node_type,
            basic_block=basic_block
        )
        self.nodes[node_id] = node
        return node_id
    
    def add_edge(self, from_id: str, to_id: str, edge_type: EdgeType):
        """添加边"""
        if from_id in self.nodes and to_id in self.nodes:
            self.nodes[from_id].add_successor(to_id, edge_type)
            self.nodes[to_id].add_predecessor(from_id, edge_type)
    
    def get_node(self, node_id: str) -> Optional[CFGNode]:
        """获取节点"""
        return self.nodes.get(node_id)
    
    def get_successors(self, node_id: str) -> List[str]:
        """获取后继节点"""
        if node_id in self.nodes:
            return [sid for sid, _ in self.nodes[node_id].successors]
        return []
    
    def get_predecessors(self, node_id: str) -> List[str]:
        """获取前驱节点"""
        if node_id in self.nodes:
            return [pid for pid, _ in self.nodes[node_id].predecessors]
        return []


class ControlFlowAnalyzer:
    """控制流分析器"""
    
    def __init__(self):
        self.cfgs: Dict[str, ControlFlowGraph] = {}
        self.current_cfg: Optional[ControlFlowGraph] = None
        self.issues: List[FlowIssue] = []
    
    # ==================== CFG构建 ====================
    
    def build_cfg(self, func_name: str, statements: List[dict]) -> ControlFlowGraph:
        """构建控制流图
        
        Args:
            func_name: 函数名
            statements: 语句列表（AST节点字典）
        
        Returns:
            控制流图
        """
        cfg = ControlFlowGraph(func_name)
        self.current_cfg = cfg
        
        # 创建入口和出口节点
        cfg.entry_id = cfg.create_node(NodeType.ENTRY)
        cfg.exit_id = cfg.create_node(NodeType.EXIT)
        
        # 构建基本块
        current_block = BasicBlock(id=cfg.create_node(NodeType.BASIC_BLOCK))
        cfg.nodes[current_block.id].basic_block = current_block
        
        # 从入口连接到第一个基本块
        cfg.add_edge(cfg.entry_id, current_block.id, EdgeType.NORMAL)
        
        # 处理语句
        current_block = self._process_statements(cfg, statements, current_block, cfg.exit_id)
        
        # 如果当前块不是出口，连接到出口
        if current_block and current_block.id in cfg.nodes:
            if not any(sid == cfg.exit_id for sid in cfg.get_successors(current_block.id)):
                cfg.add_edge(current_block.id, cfg.exit_id, EdgeType.NORMAL)
        
        self.cfgs[func_name] = cfg
        return cfg
    
    def _process_statements(
        self,
        cfg: ControlFlowGraph,
        statements: List[dict],
        current_block: BasicBlock,
        exit_id: str
    ) -> Optional[BasicBlock]:
        """处理语句序列"""
        for stmt in statements:
            stmt_type = stmt.get('type', '')
            
            if stmt_type == 'if':
                current_block = self._process_if(cfg, stmt, current_block, exit_id)
            elif stmt_type == 'while':
                current_block = self._process_while(cfg, stmt, current_block, exit_id)
            elif stmt_type == 'for':
                current_block = self._process_for(cfg, stmt, current_block, exit_id)
            elif stmt_type == 'return':
                self._process_return(cfg, stmt, current_block, exit_id)
                return None  # return后不可达
            elif stmt_type == 'break':
                self._process_break(cfg, stmt, current_block)
                return None  # break后不可达
            elif stmt_type == 'continue':
                self._process_continue(cfg, stmt, current_block)
                return None  # continue后不可达
            else:
                # 普通语句，加入当前基本块
                current_block.add_statement(stmt)
        
        return current_block
    
    def _process_if(
        self,
        cfg: ControlFlowGraph,
        stmt: dict,
        current_block: BasicBlock,
        exit_id: str
    ) -> BasicBlock:
        """处理if语句"""
        # 当前块结束，创建分支节点
        branch_node_id = cfg.create_node(NodeType.BRANCH)
        cfg.add_edge(current_block.id, branch_node_id, EdgeType.NORMAL)
        
        # 创建then分支
        then_block = BasicBlock(id=cfg.create_node(NodeType.BASIC_BLOCK))
        cfg.nodes[then_block.id].basic_block = then_block
        cfg.add_edge(branch_node_id, then_block.id, EdgeType.TRUE)
        
        # 处理then语句
        then_stmts = stmt.get('then_body', [])
        then_block = self._process_statements(cfg, then_stmts, then_block, exit_id)
        
        # 创建else分支（如果存在）
        else_block = None
        if 'else_body' in stmt and stmt['else_body']:
            else_block = BasicBlock(id=cfg.create_node(NodeType.BASIC_BLOCK))
            cfg.nodes[else_block.id].basic_block = else_block
            cfg.add_edge(branch_node_id, else_block.id, EdgeType.FALSE)
            else_block = self._process_statements(cfg, stmt['else_body'], else_block, exit_id)
        
        # 创建合并节点
        merge_block = BasicBlock(id=cfg.create_node(NodeType.MERGE))
        cfg.nodes[merge_block.id].basic_block = merge_block
        
        if then_block:
            cfg.add_edge(then_block.id, merge_block.id, EdgeType.NORMAL)
        if else_block:
            cfg.add_edge(else_block.id, merge_block.id, EdgeType.NORMAL)
        elif branch_node_id:
            # 没有else，直接从分支节点连接到合并节点
            cfg.add_edge(branch_node_id, merge_block.id, EdgeType.FALSE)
        
        return merge_block
    
    def _process_while(
        self,
        cfg: ControlFlowGraph,
        stmt: dict,
        current_block: BasicBlock,
        exit_id: str
    ) -> BasicBlock:
        """处理while循环"""
        # 创建循环头节点
        loop_header_id = cfg.create_node(NodeType.LOOP)
        cfg.add_edge(current_block.id, loop_header_id, EdgeType.NORMAL)
        
        # 创建循环体
        loop_body = BasicBlock(id=cfg.create_node(NodeType.BASIC_BLOCK))
        cfg.nodes[loop_body.id].basic_block = loop_body
        cfg.add_edge(loop_header_id, loop_body.id, EdgeType.TRUE)
        
        # 处理循环体
        body_stmts = stmt.get('body', [])
        loop_body = self._process_statements(cfg, body_stmts, loop_body, exit_id)
        
        # 回边：从循环体回到循环头
        if loop_body:
            cfg.add_edge(loop_body.id, loop_header_id, EdgeType.LOOP_BACK)
        
        # 循环退出后的基本块
        exit_block = BasicBlock(id=cfg.create_node(NodeType.BASIC_BLOCK))
        cfg.nodes[exit_block.id].basic_block = exit_block
        cfg.add_edge(loop_header_id, exit_block.id, EdgeType.FALSE)
        
        # 记录循环信息
        loop_info = LoopInfo(
            header_id=loop_header_id,
            body_ids={loop_body.id} if loop_body else set(),
            back_edge_from=loop_body.id if loop_body else "",
            nesting_level=1  # 简化：不追踪嵌套
        )
        cfg.loops.append(loop_info)
        
        return exit_block
    
    def _process_for(
        self,
        cfg: ControlFlowGraph,
        stmt: dict,
        current_block: BasicBlock,
        exit_id: str
    ) -> BasicBlock:
        """处理for循环（简化为while）"""
        # 添加初始化语句到当前块
        if 'init' in stmt:
            current_block.add_statement(stmt['init'])
        
        # 创建循环头
        loop_header_id = cfg.create_node(NodeType.LOOP)
        cfg.add_edge(current_block.id, loop_header_id, EdgeType.NORMAL)
        
        # 创建循环体
        loop_body = BasicBlock(id=cfg.create_node(NodeType.BASIC_BLOCK))
        cfg.nodes[loop_body.id].basic_block = loop_body
        cfg.add_edge(loop_header_id, loop_body.id, EdgeType.TRUE)
        
        # 处理循环体
        body_stmts = stmt.get('body', [])
        loop_body = self._process_statements(cfg, body_stmts, loop_body, exit_id)
        
        # 添加迭代语句（在循环体末尾）
        if 'update' in stmt and loop_body:
            loop_body.add_statement(stmt['update'])
        
        # 回边
        if loop_body:
            cfg.add_edge(loop_body.id, loop_header_id, EdgeType.LOOP_BACK)
        
        # 循环退出
        exit_block = BasicBlock(id=cfg.create_node(NodeType.BASIC_BLOCK))
        cfg.nodes[exit_block.id].basic_block = exit_block
        cfg.add_edge(loop_header_id, exit_block.id, EdgeType.FALSE)
        
        # 记录循环信息
        loop_info = LoopInfo(
            header_id=loop_header_id,
            body_ids={loop_body.id} if loop_body else set(),
            back_edge_from=loop_body.id if loop_body else "",
            nesting_level=1
        )
        cfg.loops.append(loop_info)
        
        return exit_block
    
    def _process_return(
        self,
        cfg: ControlFlowGraph,
        stmt: dict,
        current_block: BasicBlock,
        exit_id: str
    ):
        """处理return语句"""
        current_block.add_statement(stmt)
        cfg.add_edge(current_block.id, exit_id, EdgeType.RETURN)
    
    def _process_break(
        self,
        cfg: ControlFlowGraph,
        stmt: dict,
        current_block: BasicBlock
    ):
        """处理break语句"""
        current_block.add_statement(stmt)
        # 实际实现中需要找到最近的循环退出点
        # 这里简化处理
        cfg.issues.append(FlowIssue(
            issue_type="break",
            message="break语句跳出循环",
            line_number=stmt.get('line', 0),
            severity="info",
            suggestion=""
        ))
    
    def _process_continue(
        self,
        cfg: ControlFlowGraph,
        stmt: dict,
        current_block: BasicBlock
    ):
        """处理continue语句"""
        current_block.add_statement(stmt)
        # 实际实现中需要跳回循环头
        cfg.issues.append(FlowIssue(
            issue_type="continue",
            message="continue语句跳到下一次迭代",
            line_number=stmt.get('line', 0),
            severity="info",
            suggestion=""
        ))
    
    # ==================== 分析算法 ====================
    
    def detect_unreachable_code(self, cfg: ControlFlowGraph) -> List[FlowIssue]:
        """检测不可达代码
        
        通过从入口节点进行DFS遍历，标记所有可达节点。
        未被标记的节点即为不可达。
        """
        reachable = set()
        stack = [cfg.entry_id]
        
        while stack:
            node_id = stack.pop()
            if node_id in reachable:
                continue
            
            reachable.add(node_id)
            stack.extend(cfg.get_successors(node_id))
        
        issues = []
        for node_id, node in cfg.nodes.items():
            if node_id not in reachable and node.node_type == NodeType.BASIC_BLOCK:
                if node.basic_block and not node.basic_block.is_empty():
                    issues.append(FlowIssue(
                        issue_type="unreachable",
                        message=f"不可达代码块（行{node.basic_block.start_line}-{node.basic_block.end_line}）",
                        line_number=node.basic_block.start_line,
                        severity="warning",
                        suggestion="删除或检查控制流逻辑"
                    ))
                node.basic_block.is_reachable = False if node.basic_block else False
        
        return issues
    
    def compute_cyclomatic_complexity(self, cfg: ControlFlowGraph) -> int:
        """计算圈复杂度
        
        公式：M = E - N + 2P
        E: 边数
        N: 节点数
        P: 连通分量数（通常为1）
        """
        edges = 0
        for node in cfg.nodes.values():
            edges += len(node.successors)
        
        nodes = len(cfg.nodes)
        
        # 简化：假设单一连通分量
        complexity = edges - nodes + 2
        
        return max(1, complexity)  # 最小为1
    
    def detect_infinite_loops(self, cfg: ControlFlowGraph) -> List[FlowIssue]:
        """检测无限循环
        
        无限循环条件：
        1. 循环头没有退出边（没有FALSE边）
        2. 或退出条件恒为假
        """
        issues = []
        
        for loop in cfg.loops:
            loop_header = cfg.get_node(loop.header_id)
            if not loop_header:
                continue
            
            # 检查是否有退出边
            has_exit = any(et == EdgeType.FALSE for _, et in loop_header.successors)
            
            if not has_exit:
                loop.is_infinite = True
                issues.append(FlowIssue(
                    issue_type="infinite_loop",
                    message="检测到可能的无限循环",
                    line_number=loop_header.basic_block.start_line if loop_header.basic_block else 0,
                    severity="warning",
                    suggestion="确保循环有退出条件"
                ))
        
        return issues
    
    def compute_dominance_tree(self, cfg: ControlFlowGraph) -> Dict[str, Set[str]]:
        """计算支配树
        
        节点A支配节点B，如果从入口到B的所有路径都经过A。
        """
        # 简化的支配树计算（使用迭代算法）
        dominators = {node_id: set(cfg.nodes.keys()) for node_id in cfg.nodes}
        dominators[cfg.entry_id] = {cfg.entry_id}
        
        changed = True
        while changed:
            changed = False
            for node_id in cfg.nodes:
                if node_id == cfg.entry_id:
                    continue
                
                preds = cfg.get_predecessors(node_id)
                if preds:
                    new_dom = set.intersection(*[dominators[p] for p in preds])
                    new_dom.add(node_id)
                    
                    if new_dom != dominators[node_id]:
                        dominators[node_id] = new_dom
                        changed = True
        
        # 转换为每个节点支配哪些节点
        dominates = {node_id: set() for node_id in cfg.nodes}
        for node_id, dom_set in dominators.items():
            for dominated in dom_set:
                if dominated != node_id and dominated in cfg.nodes:
                    cfg.nodes[dominated].dominates.add(node_id)
        
        return dominates
    
    # ==================== 报告生成 ====================
    
    def generate_report(self, cfg: ControlFlowGraph) -> str:
        """生成控制流分析报告"""
        lines = [
            "=" * 70,
            f"控制流分析报告 - {cfg.func_name}",
            "=" * 70,
            "",
            "基本统计：",
            f"  节点数：{len(cfg.nodes)}",
            f"  循环数：{len(cfg.loops)}",
            f"  圈复杂度：{self.compute_cyclomatic_complexity(cfg)}",
            "",
        ]
        
        # 不可达代码检测
        unreachable = self.detect_unreachable_code(cfg)
        if unreachable:
            lines.append("不可达代码：")
            lines.append("-" * 70)
            for issue in unreachable:
                lines.append(f"  ⚠ 行{issue.line_number}: {issue.message}")
            lines.append("")
        
        # 无限循环检测
        infinite = self.detect_infinite_loops(cfg)
        if infinite:
            lines.append("循环警告：")
            lines.append("-" * 70)
            for issue in infinite:
                lines.append(f"  ⚠ 行{issue.line_number}: {issue.message}")
            lines.append("")
        
        # 复杂度警告
        complexity = self.compute_cyclomatic_complexity(cfg)
        if complexity > 10:
            lines.append(f"复杂度警告：圈复杂度 {complexity} 过高（建议≤10）")
            lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def export_dot(self, cfg: ControlFlowGraph, output_path: str) -> str:
        """导出为DOT格式（Graphviz）"""
        dot_lines = [
            f'digraph "{cfg.func_name}" {{',
            '    rankdir=TB;',
            '    node [shape=box];',
            '',
        ]
        
        # 添加节点
        for node_id, node in cfg.nodes.items():
            label = node.node_type.value
            if node.basic_block:
                label = f"BB({node.basic_block.start_line})"
            
            style = ""
            if node.node_type == NodeType.ENTRY:
                style = ' [style=filled fillcolor=green]'
            elif node.node_type == NodeType.EXIT:
                style = ' [style=filled fillcolor=red]'
            elif not node.basic_block or not node.basic_block.is_reachable:
                style = ' [style=filled fillcolor=gray]'
            
            dot_lines.append(f'    "{node_id}" [label="{label}"]{style};')
        
        dot_lines.append('')
        
        # 添加边
        for node_id, node in cfg.nodes.items():
            for succ_id, edge_type in node.successors:
                label = edge_type.value
                dot_lines.append(f'    "{node_id}" -> "{succ_id}" [label="{label}"];')
        
        dot_lines.append('}')
        
        dot_content = "\n".join(dot_lines)
        
        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dot_content)
        
        return dot_content


# 测试代码
if __name__ == '__main__':
    print("=== 控制流分析器测试 ===\n")
    
    analyzer = ControlFlowAnalyzer()
    
    # 测试简单函数
    test_statements = [
        {'type': 'var_decl', 'name': 'x', 'line': 1},
        {'type': 'var_decl', 'name': 'y', 'line': 2},
        {
            'type': 'if',
            'condition': 'x > 0',
            'then_body': [
                {'type': 'assign', 'name': 'y', 'line': 4}
            ],
            'else_body': [
                {'type': 'assign', 'name': 'y', 'line': 6}
            ],
            'line': 3
        },
        {'type': 'return', 'value': 'y', 'line': 8}
    ]
    
    cfg = analyzer.build_cfg('test_func', test_statements)
    
    print(f"节点数：{len(cfg.nodes)}")
    print(f"循环数：{len(cfg.loops)}")
    print(f"圈复杂度：{analyzer.compute_cyclomatic_complexity(cfg)}")
    print()
    
    print(analyzer.generate_report(cfg))
    
    print("\n=== 测试完成 ===")
# Phase 4 高级能力建设 - 任务执行清单

**计划周期**: 2026-04-15 ~ 2026-07-15（3个月）
**当前状态**: Stage 2 进行中（Task 11.1 泛型编程 ✅ 已完成）
**前置条件**: Phase 1-3 已完成（测试覆盖率 > 50%, CI/CD 流程建立, 文档体系完善）

---

## 📋 总体规划

Phase 4 分为三个主要方向，按优先级和依赖关系分阶段实施：

| 阶段 | 时间 | 重点方向 | 目标 |
|:-----|:-----|:---------|:-----|
| Stage 1 | Week 8-10 | 编译器优化技术 | IR 优化能力提升 |
| Stage 2 | Week 11-13 | 高级语言特性 | 泛型/模式匹配支持 |
| Stage 3 | Week 14-16 | 工具链生态 | IDE 集成和调试支持 |

---

## 🎯 Stage 1: 编译器优化技术（Week 8-10）

### Task 8.1: SSA 构建实现
**优先级**: P0 | **预计时间**: 3天 | **状态**: 待开始

#### 背景知识
SSA（Static Single Assignment）是一种中间表示形式，每个变量只被赋值一次，便于进行各种优化分析。

#### 具体任务

**Day 1: 理论学习与设计**
- [ ] 学习 SSA 构建算法（Cytron 算法）
- [ ] 分析现有 IR 结构，设计 SSA 扩展方案
- [ ] 编写设计文档 `docs/SSA_DESIGN.md`
- [ ] 定义 SSA IR 节点类型

**Day 2: 核心实现**
- [ ] 实现 Dominance Tree 构建（支配树）
- [ ] 实现 Dominance Frontier 计算（支配边界）
- [ ] 实现 Phi 节点插入算法
- [ ] 实现变量重命名算法

**Day 3: 测试与集成**
- [ ] 编写 SSA 构建单元测试
- [ ] 集成到现有 IR Pipeline
- [ ] 添加 SSA 可视化工具
- [ ] 性能基准测试

#### 技术实现

```python
# src/ir/ssa.py

from dataclasses import dataclass
from typing import Dict, List, Set
from .ir_node import IRNode, IRInstruction

@dataclass
class PhiNode(IRInstruction):
    """SSA Phi 节点"""
    result: str           # 结果变量
    operands: Dict[str, str]  # {predecessor_block: variable}
    
    def __str__(self):
        ops = ", ".join(f"[{block}]: {var}" for block, var in self.operands.items())
        return f"{self.result} = phi({ops})"


class SSABuilder:
    """SSA 构建器"""
    
    def __init__(self, function: IRFunction):
        self.function = function
        self.dominators: Dict[BasicBlock, Set[BasicBlock]] = {}
        self.dominance_frontier: Dict[BasicBlock, Set[BasicBlock]] = {}
        self.phi_nodes: Dict[BasicBlock, List[PhiNode]] = {}
    
    def build(self) -> None:
        """构建 SSA 形式"""
        # Step 1: 计算支配关系
        self._compute_dominators()
        
        # Step 2: 计算支配边界
        self._compute_dominance_frontier()
        
        # Step 3: 插入 Phi 节点
        self._insert_phi_nodes()
        
        # Step 4: 变量重命名
        self._rename_variables()
    
    def _compute_dominators(self) -> None:
        """计算支配关系（使用迭代数据流算法）"""
        entry = self.function.entry_block
        self.dominators[entry] = {entry}
        
        # 初始化其他块的支配集合为所有块
        all_blocks = set(self.function.blocks)
        for block in self.function.blocks:
            if block != entry:
                self.dominators[block] = all_blocks.copy()
        
        # 迭代直到收敛
        changed = True
        while changed:
            changed = False
            for block in self.function.blocks:
                if block == entry:
                    continue
                
                # 新的支配集合 = 所有前驱支配集合的交集 ∪ {block}
                preds = block.predecessors
                if not preds:
                    continue
                
                new_dom = {block}
                new_dom.update(set.intersection(*[self.dominators[p] for p in preds]))
                
                if new_dom != self.dominators[block]:
                    self.dominators[block] = new_dom
                    changed = True
    
    def _compute_dominance_frontier(self) -> None:
        """计算支配边界"""
        for block in self.function.blocks:
            self.dominance_frontier[block] = set()
        
        for block in self.function.blocks:
            if len(block.predecessors) >= 2:
                for pred in block.predecessors:
                    runner = pred
                    while runner not in self.dominators[block] - {block}:
                        self.dominance_frontier[runner].add(block)
                        runner = self._immediate_dominator(runner)
    
    def _immediate_dominator(self, block: BasicBlock) -> Optional[BasicBlock]:
        """获取直接支配节点"""
        doms = self.dominators[block] - {block}
        for d in doms:
            if all(d not in self.dominators[other] or other == d 
                   for other in doms if other != d):
                return d
        return None
    
    def _insert_phi_nodes(self) -> None:
        """在支配边界插入 Phi 节点"""
        # 收集所有定义的变量
        globals_vars = set()
        for block in self.function.blocks:
            for inst in block.instructions:
                if inst.defines_variable():
                    globals_vars.add(inst.result)
        
        # 为每个全局变量插入 Phi 节点
        for var in globals_vars:
            worklist = [block for block in self.function.blocks 
                       if any(inst.result == var for inst in block.instructions)]
            
            while worklist:
                block = worklist.pop()
                for df_block in self.dominance_frontier[block]:
                    if var not in self.phi_nodes.get(df_block, {}):
                        # 插入 Phi 节点
                        phi = PhiNode(
                            result=var,
                            operands={pred: var for pred in df_block.predecessors}
                        )
                        if df_block not in self.phi_nodes:
                            self.phi_nodes[df_block] = []
                        self.phi_nodes[df_block].append(phi)
                        worklist.append(df_block)
    
    def _rename_variables(self) -> None:
        """变量重命名（递归遍历支配树）"""
        counter: Dict[str, int] = {}
        stack: Dict[str, List[str]] = {}
        
        def new_name(old_name: str) -> str:
            """生成新变量名"""
            if old_name not in counter:
                counter[old_name] = 0
            else:
                counter[old_name] += 1
            
            new_var = f"{old_name}_{counter[old_name]}"
            if old_name not in stack:
                stack[old_name] = []
            stack[old_name].append(new_var)
            return new_var
        
        def rename_block(block: BasicBlock):
            """重命名块中的变量"""
            # 处理 Phi 节点
            for phi in self.phi_nodes.get(block, []):
                phi.result = new_name(phi.result)
            
            # 处理普通指令
            for inst in block.instructions:
                # 替换使用
                for use in inst.uses:
                    if use in stack and stack[use]:
                        inst.replace_use(use, stack[use][-1])
                
                # 定义新变量
                if inst.defines_variable():
                    inst.result = new_name(inst.result)
            
            # 更新后继块的 Phi 节点
            for succ in block.successors:
                for phi in self.phi_nodes.get(succ, []):
                    if block in phi.operands:
                        old_var = phi.operands[block]
                        if old_var in stack and stack[old_var]:
                            phi.operands[block] = stack[old_var][-1]
            
            # 递归处理支配树子节点
            for child in self._dominator_tree_children(block):
                rename_block(child)
            
            # 弹出栈中的变量
            for inst in block.instructions:
                if inst.defines_variable():
                    base_name = inst.result.rsplit('_', 1)[0]
                    if base_name in stack:
                        stack[base_name].pop()
        
        rename_block(self.function.entry_block)
```

#### 产出物
- `src/ir/ssa.py` - SSA 构建实现
- `tests/test_ssa.py` - 单元测试
- `docs/SSA_DESIGN.md` - 设计文档

#### 验收标准
- [ ] SSA 构建正确性测试通过
- [ ] 支配树计算正确
- [ ] Phi 节点插入位置正确
- [ ] 变量重命名无冲突

---

### Task 8.2: 数据流分析框架
**优先级**: P0 | **预计时间**: 3天 | **状态**: 待开始

#### 具体任务

**Day 1: 框架设计**
- [ ] 设计通用数据流分析框架
- [ ] 定义数据流值类型
- [ ] 实现工作列表算法
- [ ] 编写框架文档

**Day 2: 活跃变量分析**
- [ ] 实现活跃变量分析（Liveness Analysis）
- [ ] 实现到达定值分析（Reaching Definitions）
- [ ] 实现可用表达式分析（Available Expressions）
- [ ] 编写测试用例

**Day 3: 集成应用**
- [ ] 使用活跃变量分析优化寄存器分配
- [ ] 使用到达定值分析检测未初始化变量
- [ ] 使用可用表达式分析消除公共子表达式
- [ ] 性能评估

#### 技术实现

```python
# src/ir/dataflow.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar, Dict, Set, List
from .ir_node import IRInstruction, BasicBlock

T = TypeVar('T')

class DataFlowAnalysis(ABC, Generic[T]):
    """数据流分析基类"""
    
    def __init__(self, function: IRFunction):
        self.function = function
        self.in_values: Dict[BasicBlock, T] = {}
        self.out_values: Dict[BasicBlock, T] = {}
    
    @abstractmethod
    def initial_value(self) -> T:
        """返回初始数据流值"""
        pass
    
    @abstractmethod
    def entry_value(self) -> T:
        """返回入口块的数据流值"""
        pass
    
    @abstractmethod
    def meet(self, values: List[T]) -> T:
        """汇合操作（交集或并集）"""
        pass
    
    @abstractmethod
    def transfer(self, block: BasicBlock, in_value: T) -> T:
        """传递函数"""
        pass
    
    def analyze(self) -> None:
        """执行数据流分析（工作列表算法）"""
        # 初始化
        for block in self.function.blocks:
            self.in_values[block] = self.initial_value()
            self.out_values[block] = self.initial_value()
        
        self.in_values[self.function.entry_block] = self.entry_value()
        
        # 工作列表
        worklist = list(self.function.blocks)
        
        while worklist:
            block = worklist.pop(0)
            
            # 汇合前驱的输出
            if block.predecessors:
                pred_outs = [self.out_values[pred] for pred in block.predecessors]
                self.in_values[block] = self.meet(pred_outs)
            
            # 应用传递函数
            new_out = self.transfer(block, self.in_values[block])
            
            # 如果输出改变，将后继加入工作列表
            if new_out != self.out_values[block]:
                self.out_values[block] = new_out
                worklist.extend(block.successors)


class LivenessAnalysis(DataFlowAnalysis[Set[str]]):
    """活跃变量分析"""
    
    def initial_value(self) -> Set[str]:
        return set()
    
    def entry_value(self) -> Set[str]:
        return set()
    
    def meet(self, values: List[Set[str]]) -> Set[str]:
        """活跃变量使用并集"""
        result = set()
        for v in values:
            result.update(v)
        return result
    
    def transfer(self, block: BasicBlock, in_value: Set[str]) -> Set[str]:
        """传递函数：out = use ∪ (in - def)"""
        # 计算块的 def 和 use
        use = set()
        def_vars = set()
        
        # 逆序遍历指令
        for inst in reversed(block.instructions):
            # 先处理定义（因为逆序）
            if inst.defines_variable():
                def_vars.add(inst.result)
                use.discard(inst.result)
            
            # 再处理使用
            for use_var in inst.uses:
                if use_var not in def_vars:
                    use.add(use_var)
        
        # out = use ∪ (in - def)
        return use | (in_value - def_vars)
    
    def is_live_at(self, var: str, block: BasicBlock, inst_index: int) -> bool:
        """检查变量在某个程序点是否活跃"""
        # 从指令位置向前检查
        for i in range(inst_index, len(block.instructions)):
            inst = block.instructions[i]
            if var in inst.uses:
                return True
            if inst.defines_variable() and inst.result == var:
                return False
        
        # 检查块的输出
        return var in self.out_values[block]


class ReachingDefinitions(DataFlowAnalysis[Set[Tuple[str, int]]]):
    """到达定值分析"""
    
    def initial_value(self) -> Set[Tuple[str, int]]:
        return set()
    
    def entry_value(self) -> Set[Tuple[str, int]]:
        return set()
    
    def meet(self, values: List[Set[Tuple[str, int]]]) -> Set[Tuple[str, int]]:
        """到达定值使用并集"""
        result = set()
        for v in values:
            result.update(v)
        return result
    
    def transfer(self, block: BasicBlock, in_value: Set[Tuple[str, int]]) -> Set[Tuple[str, int]]:
        """传递函数：out = gen ∪ (in - kill)"""
        gen = set()
        kill = set()
        
        for i, inst in enumerate(block.instructions):
            if inst.defines_variable():
                # 生成新的定值
                gen.add((inst.result, block.id, i))
                # 杀死该变量的其他定值
                kill.update(d for d in in_value if d[0] == inst.result)
        
        return gen | (in_value - kill)
```

#### 产出物
- `src/ir/dataflow.py` - 数据流分析框架
- `src/ir/analyses.py` - 具体分析实现
- `tests/test_dataflow.py` - 单元测试

#### 验收标准
- [ ] 活跃变量分析正确性测试通过
- [ ] 到达定值分析正确性测试通过
- [ ] 可用表达式分析正确性测试通过
- [ ] 分析结果可用于优化

---

### Task 8.3: 循环优化实现
**优先级**: P1 | **预计时间**: 2天 | **状态**: 待开始

#### 具体任务

**Day 1: 循环识别**
- [ ] 实现自然循环识别算法
- [ ] 实现循环嵌套层次计算
- [ ] 实现循环不变量检测
- [ ] 编写测试用例

**Day 2: 循环优化**
- [ ] 实现循环不变量外提（Loop Invariant Code Motion）
- [ ] 实现强度削减（Strength Reduction）
- [ ] 实现归纳变量优化（Induction Variable Elimination）
- [ ] 性能评估

#### 技术实现

```python
# src/ir/loop_opt.py

from dataclasses import dataclass
from typing import Set, List, Optional
from .ir_node import BasicBlock, IRInstruction

@dataclass
class Loop:
    """循环结构"""
    header: BasicBlock          # 循环头
    body: Set[BasicBlock]       # 循环体
    back_edge: tuple            # 回边 (source, target)
    parent: Optional['Loop']    # 父循环
    children: List['Loop']      # 嵌套子循环
    depth: int                  # 嵌套深度
    
    @property
    def is_innermost(self) -> bool:
        """是否是最内层循环"""
        return len(self.children) == 0


class LoopDetector:
    """循环检测器"""
    
    def __init__(self, function: IRFunction):
        self.function = function
        self.loops: List[Loop] = []
        self.loop_headers: Set[BasicBlock] = set()
    
    def detect(self) -> List[Loop]:
        """检测所有自然循环"""
        # Step 1: 找到所有回边
        back_edges = self._find_back_edges()
        
        # Step 2: 对每个回边构建自然循环
        for source, target in back_edges:
            loop_body = self._build_natural_loop(source, target)
            loop = Loop(
                header=target,
                body=loop_body,
                back_edge=(source, target),
                parent=None,
                children=[],
                depth=0
            )
            self.loops.append(loop)
            self.loop_headers.add(target)
        
        # Step 3: 构建循环嵌套关系
        self._build_loop_nesting()
        
        return self.loops
    
    def _find_back_edges(self) -> List[tuple]:
        """找到所有回边（使用支配关系）"""
        back_edges = []
        
        # 计算支配关系
        dominators = self._compute_dominators()
        
        for block in self.function.blocks:
            for succ in block.successors:
                # 如果 succ 支配 block，则是回边
                if succ in dominators[block]:
                    back_edges.append((block, succ))
        
        return back_edges
    
    def _build_natural_loop(self, back_edge_source: BasicBlock, 
                           back_edge_target: BasicBlock) -> Set[BasicBlock]:
        """构建自然循环"""
        loop_body = {back_edge_target}
        worklist = [back_edge_source]
        
        while worklist:
            block = worklist.pop()
            if block not in loop_body:
                loop_body.add(block)
                worklist.extend(block.predecessors)
        
        return loop_body
    
    def _build_loop_nesting(self) -> None:
        """构建循环嵌套关系"""
        # 按循环体大小排序（大的在外层）
        self.loops.sort(key=lambda l: len(l.body), reverse=True)
        
        for i, outer in enumerate(self.loops):
            for inner in self.loops[i+1:]:
                if inner.body <= outer.body:
                    inner.parent = outer
                    outer.children.append(inner)
                    inner.depth = outer.depth + 1


class LoopInvariantCodeMotion:
    """循环不变量外提"""
    
    def __init__(self, loop: Loop, liveness: LivenessAnalysis):
        self.loop = loop
        self.liveness = liveness
    
    def optimize(self) -> int:
        """执行循环不变量外提，返回外提的指令数"""
        moved_count = 0
        
        # 找到所有循环不变量
        invariants = self._find_loop_invariants()
        
        # 外提到循环前置块
        preheader = self._get_or_create_preheader()
        
        for inst, block in invariants:
            if self._is_safe_to_move(inst, block):
                # 从原位置移除
                block.instructions.remove(inst)
                # 插入到前置块
                preheader.instructions.append(inst)
                moved_count += 1
        
        return moved_count
    
    def _find_loop_invariants(self) -> List[tuple]:
        """找到所有循环不变量指令"""
        invariants = []
        
        for block in self.loop.body:
            for inst in block.instructions:
                if self._is_loop_invariant(inst):
                    invariants.append((inst, block))
        
        return invariants
    
    def _is_loop_invariant(self, inst: IRInstruction) -> bool:
        """检查指令是否是循环不变量"""
        # 所有操作数都不在循环中被定义
        for use in inst.uses:
            # 检查 use 是否在循环中被定义
            for block in self.loop.body:
                for def_inst in block.instructions:
                    if def_inst.defines_variable() and def_inst.result == use:
                        return False
        return True
    
    def _is_safe_to_move(self, inst: IRInstruction, block: BasicBlock) -> bool:
        """检查是否可以安全外提"""
        # 条件1: 指令支配所有出口
        # 条件2: 指令没有副作用
        # 条件3: 指令在循环中唯一
        
        if inst.has_side_effects():
            return False
        
        # 检查是否在循环中唯一
        for b in self.loop.body:
            for i in b.instructions:
                if i == inst:
                    continue
                if i.is_same_operation(inst):
                    return False
        
        return True
    
    def _get_or_create_preheader(self) -> BasicBlock:
        """获取或创建循环前置块"""
        # 查找现有的前置块
        for pred in self.loop.header.predecessors:
            if pred not in self.loop.body:
                return pred
        
        # 创建新的前置块
        preheader = BasicBlock(id=f"{self.loop.header.id}_preheader")
        # ... 连接逻辑
        return preheader
```

#### 产出物
- `src/ir/loop_opt.py` - 循环优化实现
- `tests/test_loop_opt.py` - 单元测试

#### 验收标准
- [ ] 循环识别正确性测试通过
- [ ] 循环不变量外提正确
- [ ] 强度削减正确
- [ ] 性能提升 > 10%

---

### Task 8.4: 内联优化
**优先级**: P1 | **预计时间**: 2天 | **状态**: 待开始

#### 具体任务

**Day 1: 内联决策**
- [ ] 实现函数调用图构建
- [ ] 实现内联成本模型
- [ ] 实现启发式内联决策
- [ ] 编写测试用例

**Day 2: 内联实现**
- [ ] 实现函数内联转换
- [ ] 处理递归调用
- [ ] 处理参数传递和返回值
- [ ] 性能评估

#### 技术实现

```python
# src/ir/inline.py

from dataclasses import dataclass
from typing import Dict, Set, List, Optional
from .ir_node import IRFunction, IRCall

@dataclass
class InlineCost:
    """内联成本模型"""
    instruction_count: int      # 指令数量
    call_overhead: int          # 调用开销
    code_size_growth: int       # 代码增长
    estimated_speedup: float    # 预计加速比
    
    @property
    def benefit(self) -> float:
        """内联收益"""
        return self.estimated_speedup - self.code_size_growth * 0.01


class InlineDecision:
    """内联决策器"""
    
    def __init__(self, call_graph: CallGraph):
        self.call_graph = call_graph
        self.inline_threshold = 100  # 指令数阈值
        self.max_growth = 2.0        # 最大代码增长倍数
    
    def should_inline(self, caller: IRFunction, callee: IRFunction) -> bool:
        """决定是否内联"""
        cost = self._estimate_cost(caller, callee)
        
        # 启发式规则
        if cost.instruction_count > self.inline_threshold:
            return False
        
        if cost.benefit <= 0:
            return False
        
        # 递归函数不内联
        if self._is_recursive(callee):
            return False
        
        # 热点函数优先内联
        if self._is_hot(callee):
            return True
        
        return cost.benefit > 0.5
    
    def _estimate_cost(self, caller: IRFunction, callee: IRFunction) -> InlineCost:
        """估算内联成本"""
        inst_count = len(callee.instructions)
        call_overhead = 5  # 假设调用开销为 5 条指令
        
        # 预计加速比（基于调用频率）
        call_freq = self.call_graph.get_call_frequency(caller, callee)
        estimated_speedup = call_freq * call_overhead / max(inst_count, 1)
        
        # 代码增长
        code_growth = inst_count - call_overhead
        
        return InlineCost(
            instruction_count=inst_count,
            call_overhead=call_overhead,
            code_size_growth=code_growth,
            estimated_speedup=estimated_speedup
        )


class Inliner:
    """函数内联器"""
    
    def __init__(self, function: IRFunction, decision: InlineDecision):
        self.function = function
        self.decision = decision
    
    def inline_calls(self) -> int:
        """内联所有合适的调用，返回内联次数"""
        inlined_count = 0
        
        for block in self.function.blocks:
            new_instructions = []
            
            for inst in block.instructions:
                if isinstance(inst, IRCall):
                    callee = self._get_callee(inst)
                    if callee and self.decision.should_inline(self.function, callee):
                        # 内联调用
                        inlined_code = self._inline_call(inst, callee)
                        new_instructions.extend(inlined_code)
                        inlined_count += 1
                    else:
                        new_instructions.append(inst)
                else:
                    new_instructions.append(inst)
            
            block.instructions = new_instructions
        
        return inlined_count
    
    def _inline_call(self, call: IRCall, callee: IRFunction) -> List[IRInstruction]:
        """内联单个函数调用"""
        inlined = []
        
        # Step 1: 参数映射
        param_map = {}
        for param, arg in zip(callee.params, call.args):
            param_map[param.name] = arg
        
        # Step 2: 复制函数体
        for block in callee.blocks:
            for inst in block.instructions:
                # 克隆指令并替换参数
                new_inst = inst.clone()
                new_inst.replace_uses(param_map)
                inlined.append(new_inst)
        
        # Step 3: 处理返回值
        # ... 将 return 替换为赋值
        
        return inlined
```

#### 产出物
- `src/ir/inline.py` - 内联优化实现
- `tests/test_inline.py` - 单元测试

#### 验收标准
- [ ] 内联决策合理
- [ ] 内联转换正确
- [ ] 代码增长可控
- [ ] 性能提升 > 5%

---

## 🎯 Stage 2: 高级语言特性（Week 11-13）

### Task 11.1: 泛型编程支持
**优先级**: P0 | **预计时间**: 4天 | **状态**: ✅ 已完成

#### 具体任务

**Day 1: 泛型类型系统设计** ✅
- [x] 设计泛型类型表示
- [x] 设计类型参数化机制
- [x] 设计类型约束系统
- [x] 编写设计文档

**Day 2: 泛型解析** ✅
- [x] 扩展词法分析器支持泛型语法
- [x] 扩展语法分析器解析泛型声明
- [x] 实现类型参数绑定
- [x] 编写测试用例

**Day 3: 泛型实例化** ✅
- [x] 实现泛型类型实例化
- [x] 实现泛型函数实例化
- [x] 实现类型推导
- [x] 处理泛型约束检查

**Day 4: 代码生成** ✅
- [x] 泛型代码生成策略
- [x] 单态化实现
- [x] 泛型优化
- [x] 性能评估

#### 技术实现

```python
# src/semantic/generics.py

from dataclasses import dataclass
from typing import List, Dict, Optional, TypeVar, Generic
from .types import Type

@dataclass
class TypeParameter:
    """类型参数"""
    name: str
    constraints: List['TypeConstraint']
    default: Optional[Type] = None


@dataclass
class TypeConstraint:
    """类型约束"""
    name: str  # 约束名称，如 'Comparable', 'Numeric'
    methods: List[str]  # 要求的方法


class GenericType(Type):
    """泛型类型"""
    
    def __init__(self, name: str, type_params: List[TypeParameter]):
        super().__init__(name)
        self.type_params = type_params
        self.instantiations: Dict[tuple, Type] = {}
    
    def instantiate(self, type_args: List[Type]) -> Type:
        """实例化泛型类型"""
        # 检查参数数量
        if len(type_args) != len(self.type_params):
            raise TypeError(
                f"泛型类型 {self.name} 需要 {len(self.type_params)} 个类型参数，"
                f"但提供了 {len(type_args)} 个"
            )
        
        # 检查约束
        for param, arg in zip(self.type_params, type_args):
            if not self._satisfies_constraints(arg, param.constraints):
                raise TypeError(
                    f"类型 {arg} 不满足约束 {param.name}"
                )
        
        # 缓存实例化结果
        key = tuple(type_args)
        if key not in self.instantiations:
            # 创建实例化类型
            instantiated = self._create_instance(type_args)
            self.instantiations[key] = instantiated
        
        return self.instantiations[key]
    
    def _satisfies_constraints(self, type: Type, constraints: List[TypeConstraint]) -> bool:
        """检查类型是否满足约束"""
        for constraint in constraints:
            if not self._check_constraint(type, constraint):
                return False
        return True
    
    def _check_constraint(self, type: Type, constraint: TypeConstraint) -> bool:
        """检查单个约束"""
        # 检查类型是否实现了要求的方法
        for method in constraint.methods:
            if not type.has_method(method):
                return False
        return True


class GenericFunction:
    """泛型函数"""
    
    def __init__(self, name: str, type_params: List[TypeParameter], 
                 params: List['Parameter'], return_type: Type):
        self.name = name
        self.type_params = type_params
        self.params = params
        self.return_type = return_type
        self.instantiations: Dict[tuple, 'Function'] = {}
    
    def instantiate(self, type_args: List[Type], context: 'SemanticContext') -> 'Function':
        """实例化泛型函数"""
        # 类型推导
        if not type_args:
            type_args = self._infer_type_args(context)
        
        # 检查约束
        for param, arg in zip(self.type_params, type_args):
            if not self._check_constraints(arg, param.constraints):
                raise TypeError(f"类型 {arg} 不满足约束")
        
        # 缓存
        key = tuple(type_args)
        if key not in self.instantiations:
            instantiated = self._create_instance(type_args, context)
            self.instantiations[key] = instantiated
        
        return self.instantiations[key]
    
    def _infer_type_args(self, context: 'SemanticContext') -> List[Type]:
        """从上下文推导类型参数"""
        # 使用 Hindley-Milner 类型推导算法
        # ...
        pass


# 示例用法
"""
// 泛型类型定义
泛型类型 列表<类型 T> {
    T 数据[100];
    整数型 长度;
}

// 泛型函数定义
泛型函数 T 最大值<类型 T: 可比较>(T a, T b) {
    如果 (a > b) {
        返回 a;
    } 否则 {
        返回 b;
    }
}

// 使用
列表<整数型> 整数列表;
列表<字符串型> 字符串列表;

整数型 m = 最大值<整数型>(10, 20);
字符串型 s = 最大值<字符串型>("hello", "world");
"""
```

#### 产出物
- `src/semantic/generics.py` - 泛型系统实现 ✅
- `src/parser/generic_parser.py` - 泛型语法解析 ✅
- `src/semantic/generic_instantiator.py` - 泛型实例化 ✅
- `src/codegen/generic_codegen.py` - 泛型代码生成 ✅
- `tests/test_generics.py` - 单元测试 ✅
- `tests/test_generic_parser.py` - 解析测试 ✅
- `tests/test_generic_instantiator.py` - 实例化测试 ✅
- `tests/test_generic_codegen.py` - 代码生成测试 ✅
- `examples/generic.zhc` - 示例代码 ✅

#### 验收标准
- [x] 泛型类型解析正确
- [x] 泛型函数解析正确
- [x] 类型约束检查正确
- [x] 代码生成正确
- [x] 性能可接受

---

### Task 11.2: 模式匹配实现
**优先级**: P1 | **预计时间**: 3天 | **状态**: 待开始

#### 具体任务

**Day 1: 模式匹配语法**
- [ ] 设计模式匹配语法
- [ ] 扩展词法分析器
- [ ] 扩展语法分析器
- [ ] 编写测试用例

**Day 2: 模式匹配语义**
- [ ] 实现模式匹配算法
- [ ] 实现解构绑定
- [ ] 实现守卫表达式
- [ ] 实现穷尽性检查

**Day 3: 代码生成**
- [ ] 模式匹配代码生成
- [ ] 优化决策树
- [ ] 性能评估

#### 技术实现

```python
# src/semantic/pattern_matching.py

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

@dataclass
class Pattern(ABC):
    """模式基类"""
    
    @abstractmethod
    def match(self, value: Any, bindings: Dict[str, Any]) -> bool:
        """尝试匹配值，返回是否匹配并更新绑定"""
        pass


@dataclass
class WildcardPattern(Pattern):
    """通配符模式 _"""
    
    def match(self, value: Any, bindings: Dict[str, Any]) -> bool:
        return True  # 匹配任何值，不绑定


@dataclass
class VariablePattern(Pattern):
    """变量模式 x"""
    name: str
    
    def match(self, value: Any, bindings: Dict[str, Any]) -> bool:
        bindings[self.name] = value
        return True


@dataclass
class LiteralPattern(Pattern):
    """字面量模式 42, "hello" """
    value: Any
    
    def match(self, value: Any, bindings: Dict[str, Any]) -> bool:
        return self.value == value


@dataclass
class ConstructorPattern(Pattern):
    """构造器模式 Some(x), None """
    constructor: str
    patterns: List[Pattern]
    
    def match(self, value: Any, bindings: Dict[str, Any]) -> bool:
        if not isinstance(value, dict) or value.get('_constructor') != self.constructor:
            return False
        
        fields = value.get('_fields', [])
        if len(fields) != len(self.patterns):
            return False
        
        for pattern, field_value in zip(self.patterns, fields):
            if not pattern.match(field_value, bindings):
                return False
        
        return True


@dataclass
class TuplePattern(Pattern):
    """元组模式 (x, y, z)"""
    patterns: List[Pattern]
    
    def match(self, value: Any, bindings: Dict[str, Any]) -> bool:
        if not isinstance(value, tuple) or len(value) != len(self.patterns):
            return False
        
        for pattern, element in zip(self.patterns, value):
            if not pattern.match(element, bindings):
                return False
        
        return True


@dataclass
class GuardedPattern(Pattern):
    """守卫模式 x when x > 0"""
    pattern: Pattern
    guard: 'Expression'
    
    def match(self, value: Any, bindings: Dict[str, Any]) -> bool:
        if not self.pattern.match(value, bindings):
            return False
        
        # 评估守卫表达式
        return self._evaluate_guard(self.guard, bindings)
    
    def _evaluate_guard(self, guard: 'Expression', bindings: Dict[str, Any]) -> bool:
        """评估守卫表达式"""
        # 替换变量为绑定值
        # 评估表达式
        # 返回布尔结果
        pass


class PatternMatcher:
    """模式匹配器"""
    
    def __init__(self, value: Any, cases: List[tuple]):
        """
        Args:
            value: 要匹配的值
            cases: [(pattern, body), ...] 匹配分支列表
        """
        self.value = value
        self.cases = cases
    
    def match(self) -> Optional[Any]:
        """执行模式匹配"""
        for pattern, body in self.cases:
            bindings = {}
            if pattern.match(self.value, bindings):
                # 执行对应的 body
                return self._execute_body(body, bindings)
        
        # 没有匹配
        raise MatchError(f"No pattern matched for value: {self.value}")
    
    def _execute_body(self, body: 'Expression', bindings: Dict[str, Any]) -> Any:
        """执行匹配分支的代码体"""
        # 在绑定环境下执行代码
        pass


class ExhaustivenessChecker:
    """穷尽性检查器"""
    
    def check(self, patterns: List[Pattern], type: Type) -> bool:
        """检查模式匹配是否穷尽"""
        # 构建模式矩阵
        # 检查是否覆盖所有可能值
        # 返回是否穷尽
        pass


# 示例用法
"""
// 模式匹配语法
函数 描述(整数型 x) -> 字符串型 {
    匹配 x {
        当 0 => "零"
        当 n 当 n < 0 => "负数"
        当 n 当 n > 0 且 n < 10 => "个位正数"
        当 _ => "其他"
    }
}

// 解构绑定
结构体 点 {
    整数型 x;
    整数型 y;
}

函数 距离原点(点 p) -> 整数型 {
    匹配 p {
        当 点{x: 0, y: 0} => 0
        当 点{x, y} => x * x + y * y
    }
}
"""
```

#### 产出物
- `src/semantic/pattern_matching.py` - 模式匹配实现
- `tests/test_pattern_matching.py` - 单元测试

#### 验收标准
- [ ] 模式匹配语法解析正确
- [ ] 模式匹配语义正确
- [ ] 穷尽性检查正确
- [ ] 代码生成正确

---

### Task 11.3: 异步编程支持
**优先级**: P2 | **预计时间**: 3天 | **状态**: 待开始

#### 具体任务

**Day 1: 异步语法设计**
- [ ] 设计 async/await 语法
- [ ] 设计 Future 类型
- [ ] 设计任务调度模型
- [ ] 编写设计文档

**Day 2: 异步语义分析**
- [ ] 实现异步函数类型检查
- [ ] 实现 await 表达式检查
- [ ] 实现异步调用链分析
- [ ] 编写测试用例

**Day 3: 异步代码生成**
- [ ] 实现状态机生成
- [ ] 实现 Promise/Future 运行时
- [ ] 实现任务调度器
- [ ] 性能评估

#### 技术实现

```python
# src/semantic/async_analysis.py

from dataclasses import dataclass
from typing import List, Optional, Set
from .types import Type

@dataclass
class AsyncFunctionType(Type):
    """异步函数类型"""
    params: List[Type]
    return_type: Type
    
    @property
    def future_type(self) -> Type:
        """返回 Future 类型"""
        return FutureType(self.return_type)


@dataclass
class FutureType(Type):
    """Future 类型"""
    value_type: Type


class AsyncAnalyzer:
    """异步分析器"""
    
    def __init__(self):
        self.async_functions: Set[str] = set()
    
    def analyze_function(self, func: 'Function') -> None:
        """分析函数是否是异步的"""
        if self._contains_await(func):
            self.async_functions.add(func.name)
            func.is_async = True
    
    def _contains_await(self, func: 'Function') -> bool:
        """检查函数是否包含 await"""
        for block in func.blocks:
            for inst in block.instructions:
                if self._is_await(inst):
                    return True
        return False
    
    def check_await_usage(self, await_expr: 'AwaitExpression') -> Type:
        """检查 await 表达式"""
        # await 只能在 async 函数中使用
        if not self._in_async_function():
            raise SemanticError("await 只能在 async 函数中使用")
        
        # 检查 await 的表达式类型
        expr_type = self._get_expression_type(await_expr.expression)
        
        if not isinstance(expr_type, FutureType):
            raise SemanticError(f"不能 await 非 Future 类型: {expr_type}")
        
        return expr_type.value_type


# 示例用法
"""
// 异步函数定义
异步 函数 获取数据(字符串型 url) -> 字符串型 {
    等待 网络请求(url)
}

// 异步调用
异步 函数 主函数() -> 空型 {
    字符串型 数据 = 等待 获取数据("https://example.com");
    打印(数据);
}
"""
```

#### 产出物
- `src/semantic/async_analysis.py` - 异步分析实现
- `src/codegen/async_codegen.py` - 异步代码生成
- `tests/test_async.py` - 单元测试

#### 验收标准
- [ ] 异步语法解析正确
- [ ] 异步类型检查正确
- [ ] 状态机生成正确
- [ ] 运行时正确

---

## 🎯 Stage 3: 工具链生态（Week 14-16）

### Task 14.1: Language Server Protocol 实现
**优先级**: P0 | **预计时间**: 5天 | **状态**: 待开始

#### 具体任务

**Day 1: LSP 协议实现**
- [ ] 实现 LSP 协议消息解析
- [ ] 实现 JSON-RPC 通信
- [ ] 实现基础 LSP 服务器
- [ ] 编写测试用例

**Day 2: 代码补全**
- [ ] 实现上下文分析
- [ ] 实现关键字补全
- [ ] 实现变量/函数补全
- [ ] 实现类型补全

**Day 3: 诊断和悬停**
- [ ] 实现实时诊断
- [ ] 实现悬停提示
- [ ] 实现签名帮助
- [ ] 性能优化

**Day 4: 导航和重构**
- [ ] 实现转到定义
- [ ] 实现查找引用
- [ ] 实现重命名
- [ ] 实现代码操作

**Day 5: 集成测试**
- [ ] VSCode 扩展开发
- [ ] 集成测试
- [ ] 性能优化
- [ ] 文档编写

#### 技术实现

```python
# src/lsp/server.py

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class Position:
    """位置"""
    line: int
    character: int


@dataclass
class Range:
    """范围"""
    start: Position
    end: Position


@dataclass
class Diagnostic:
    """诊断信息"""
    range: Range
    severity: int  # 1=Error, 2=Warning, 3=Information, 4=Hint
    message: str
    source: str = "zhc"


class LanguageServer:
    """ZHC Language Server"""
    
    def __init__(self):
        self.documents: Dict[str, str] = {}
        self.diagnostics: Dict[str, List[Diagnostic]] = {}
    
    def handle_request(self, request: Dict) -> Dict:
        """处理 LSP 请求"""
        method = request.get('method')
        params = request.get('params', {})
        
        handlers = {
            'initialize': self._handle_initialize,
            'textDocument/didOpen': self._handle_document_open,
            'textDocument/didChange': self._handle_document_change,
            'textDocument/completion': self._handle_completion,
            'textDocument/hover': self._handle_hover,
            'textDocument/definition': self._handle_definition,
            'textDocument/references': self._handle_references,
            'textDocument/rename': self._handle_rename,
        }
        
        handler = handlers.get(method)
        if handler:
            return handler(params)
        
        return {}
    
    def _handle_initialize(self, params: Dict) -> Dict:
        """初始化"""
        return {
            'capabilities': {
                'textDocumentSync': 1,  # Full sync
                'completionProvider': {
                    'triggerCharacters': ['.'],
                    'resolveProvider': False
                },
                'hoverProvider': True,
                'definitionProvider': True,
                'referencesProvider': True,
                'renameProvider': True,
                'diagnosticProvider': {
                    'interFileDependencies': False,
                    'workspaceDiagnostics': False
                }
            }
        }
    
    def _handle_document_open(self, params: Dict) -> Dict:
        """文档打开"""
        uri = params['textDocument']['uri']
        text = params['textDocument']['text']
        self.documents[uri] = text
        
        # 发布诊断
        diagnostics = self._compute_diagnostics(uri, text)
        self.diagnostics[uri] = diagnostics
        
        return {
            'uri': uri,
            'diagnostics': [d.__dict__ for d in diagnostics]
        }
    
    def _handle_completion(self, params: Dict) -> Dict:
        """代码补全"""
        uri = params['textDocument']['uri']
        position = Position(**params['position'])
        
        text = self.documents.get(uri, '')
        completions = self._get_completions(text, position)
        
        return {
            'isIncomplete': False,
            'items': completions
        }
    
    def _get_completions(self, text: str, position: Position) -> List[Dict]:
        """获取补全项"""
        # 获取当前行
        lines = text.split('\n')
        if position.line >= len(lines):
            return []
        
        line = lines[position.line]
        prefix = line[:position.character]
        
        completions = []
        
        # 关键字补全
        keywords = ['整数型', '浮点型', '字符型', '如果', '否则', '当', '返回']
        for kw in keywords:
            if kw.startswith(prefix):
                completions.append({
                    'label': kw,
                    'kind': 14,  # Keyword
                    'detail': f'关键字 {kw}'
                })
        
        # 变量/函数补全
        # ... 从符号表获取
        
        return completions
    
    def _handle_hover(self, params: Dict) -> Dict:
        """悬停提示"""
        uri = params['textDocument']['uri']
        position = Position(**params['position'])
        
        text = self.documents.get(uri, '')
        hover_info = self._get_hover_info(text, position)
        
        if hover_info:
            return {
                'contents': hover_info,
                'range': None
            }
        
        return {}
    
    def _get_hover_info(self, text: str, position: Position) -> Optional[str]:
        """获取悬停信息"""
        # 获取符号信息
        # 返回类型、文档等
        pass
    
    def _compute_diagnostics(self, uri: str, text: str) -> List[Diagnostic]:
        """计算诊断信息"""
        diagnostics = []
        
        try:
            # 编译代码
            compiler = ZHCCompiler()
            result = compiler.compile(text)
            
            # 转换错误为诊断
            for error in result.errors:
                diagnostic = Diagnostic(
                    range=Range(
                        start=Position(line=error.line, character=error.column),
                        end=Position(line=error.line, character=error.column + 1)
                    ),
                    severity=1,  # Error
                    message=error.message,
                    source='zhc'
                )
                diagnostics.append(diagnostic)
        
        except Exception as e:
            pass
        
        return diagnostics
```

#### 产出物
- `src/lsp/` - LSP 实现
- `editors/vscode/` - VSCode 扩展
- `tests/test_lsp.py` - 单元测试
- `docs/LSP_GUIDE.md` - 使用指南

#### 验收标准
- [ ] LSP 协议实现完整
- [ ] 代码补全正常工作
- [ ] 诊断实时更新
- [ ] VSCode 扩展可用

---

### Task 14.2: 调试信息生成
**优先级**: P1 | **预计时间**: 3天 | **状态**: 待开始

#### 具体任务

**Day 1: DWARF 格式研究**
- [ ] 学习 DWARF 调试格式
- [ ] 分析 DWARF 生成工具
- [ ] 设计调试信息结构
- [ ] 编写设计文档

**Day 2: 调试信息生成**
- [ ] 实现行号信息生成
- [ ] 实现变量信息生成
- [ ] 实现函数信息生成
- [ ] 实现类型信息生成

**Day 3: 调试器集成**
- [ ] 测试 GDB 调试
- [ ] 测试 LLDB 调试
- [ ] 编写调试指南
- [ ] 性能评估

#### 技术实现

```python
# src/codegen/debug_info.py

from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class DebugLocation:
    """调试位置"""
    file: str
    line: int
    column: int


@dataclass
class DebugVariable:
    """调试变量信息"""
    name: str
    type: str
    location: str  # 寄存器或栈位置
    scope_start: int
    scope_end: int


class DWARFGenerator:
    """DWARF 调试信息生成器"""
    
    def __init__(self):
        self.compilation_units: List[Dict] = []
    
    def generate(self, source_file: str, ast: 'AST') -> bytes:
        """生成 DWARF 调试信息"""
        # 创建编译单元
        cu = self._create_compilation_unit(source_file)
        
        # 生成行号信息
        cu['line_program'] = self._generate_line_program(source_file, ast)
        
        # 生成调试信息条目 (DIE)
        cu['dies'] = self._generate_dies(ast)
        
        self.compilation_units.append(cu)
        
        # 编码为 DWARF 格式
        return self._encode_dwarf()
    
    def _generate_line_program(self, source_file: str, ast: 'AST') -> Dict:
        """生成行号程序"""
        line_program = {
            'file': source_file,
            'entries': []
        }
        
        # 遍历 AST，记录每个节点的行号
        for node in ast.walk():
            if hasattr(node, 'line'):
                entry = {
                    'address': node.address,  # 代码地址
                    'line': node.line,
                    'column': node.column,
                    'is_stmt': True,  # 是语句开始
                    'basic_block': node.is_basic_block
                }
                line_program['entries'].append(entry)
        
        return line_program
    
    def _generate_dies(self, ast: 'AST') -> List[Dict]:
        """生成调试信息条目"""
        dies = []
        
        # 编译单元 DIE
        cu_die = {
            'tag': 'DW_TAG_compile_unit',
            'attributes': {
                'DW_AT_name': ast.source_file,
                'DW_AT_language': 'DW_LANG_C',
            },
            'children': []
        }
        
        # 函数 DIEs
        for func in ast.functions:
            func_die = self._generate_function_die(func)
            cu_die['children'].append(func_die)
        
        # 类型 DIEs
        for type_def in ast.types:
            type_die = self._generate_type_die(type_def)
            cu_die['children'].append(type_die)
        
        dies.append(cu_die)
        return dies
    
    def _generate_function_die(self, func: 'Function') -> Dict:
        """生成函数 DIE"""
        die = {
            'tag': 'DW_TAG_subprogram',
            'attributes': {
                'DW_AT_name': func.name,
                'DW_AT_type': func.return_type,
                'DW_AT_low_pc': func.address,
                'DW_AT_high_pc': func.address + func.size,
            },
            'children': []
        }
        
        # 参数 DIEs
        for param in func.params:
            param_die = {
                'tag': 'DW_TAG_formal_parameter',
                'attributes': {
                    'DW_AT_name': param.name,
                    'DW_AT_type': param.type,
                }
            }
            die['children'].append(param_die)
        
        # 局部变量 DIEs
        for var in func.local_vars:
            var_die = {
                'tag': 'DW_TAG_variable',
                'attributes': {
                    'DW_AT_name': var.name,
                    'DW_AT_type': var.type,
                    'DW_AT_location': var.location,
                }
            }
            die['children'].append(var_die)
        
        return die
    
    def _encode_dwarf(self) -> bytes:
        """编码为 DWARF 格式"""
        # 实际实现需要使用 DWARF 编码库
        # 或直接生成 ELF 格式的调试段
        pass
```

#### 产出物
- `src/codegen/debug_info.py` - 调试信息生成
- `docs/DEBUG_GUIDE.md` - 调试指南
- `tests/test_debug_info.py` - 单元测试

#### 验收标准
- [ ] DWARF 格式正确
- [ ] GDB 可加载调试信息
- [ ] LLDB 可加载调试信息
- [ ] 源码级调试可用

---

### Task 14.3: 静态分析框架
**优先级**: P2 | **预计时间**: 3天 | **状态**: 待开始

#### 具体任务

**Day 1: 分析框架设计**
- [ ] 设计静态分析框架
- [ ] 定义分析接口
- [ ] 实现分析调度器
- [ ] 编写设计文档

**Day 2: 内置分析器**
- [ ] 实现未使用变量检测
- [ ] 实现可能的空指针检测
- [ ] 实现资源泄漏检测
- [ ] 实现代码复杂度分析

**Day 3: 集成与报告**
- [ ] 实现分析报告生成
- [ ] 集成到 CI/CD
- [ ] 编写使用指南
- [ ] 性能优化

#### 技术实现

```python
# src/analysis/static_analyzer.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class AnalysisResult:
    """分析结果"""
    analyzer: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    location: 'SourceLocation'
    suggestion: Optional[str] = None


class StaticAnalyzer(ABC):
    """静态分析器基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """分析器名称"""
        pass
    
    @abstractmethod
    def analyze(self, ast: 'AST') -> List[AnalysisResult]:
        """执行分析"""
        pass


class UnusedVariableAnalyzer(StaticAnalyzer):
    """未使用变量分析器"""
    
    @property
    def name(self) -> str:
        return "unused_variable"
    
    def analyze(self, ast: 'AST') -> List[AnalysisResult]:
        results = []
        
        # 收集所有定义的变量
        defined_vars = {}
        for node in ast.walk():
            if isinstance(node, VariableDeclaration):
                defined_vars[node.name] = node
        
        # 收集所有使用的变量
        used_vars = set()
        for node in ast.walk():
            if isinstance(node, VariableReference):
                used_vars.add(node.name)
        
        # 找出未使用的变量
        for var_name, var_node in defined_vars.items():
            if var_name not in used_vars:
                result = AnalysisResult(
                    analyzer=self.name,
                    severity='warning',
                    message=f"变量 '{var_name}' 已定义但从未使用",
                    location=var_node.location,
                    suggestion=f"考虑删除未使用的变量 '{var_name}'"
                )
                results.append(result)
        
        return results


class NullPointerAnalyzer(StaticAnalyzer):
    """空指针分析器"""
    
    @property
    def name(self) -> str:
        return "null_pointer"
    
    def analyze(self, ast: 'AST') -> List[AnalysisResult]:
        results = []
        
        # 使用数据流分析追踪指针可能为空的位置
        for node in ast.walk():
            if isinstance(node, PointerDereference):
                # 检查指针是否可能为空
                if self._may_be_null(node.pointer, node):
                    result = AnalysisResult(
                        analyzer=self.name,
                        severity='warning',
                        message=f"指针 '{node.pointer.name}' 可能为空",
                        location=node.location,
                        suggestion="在使用前检查指针是否为空"
                    )
                    results.append(result)
        
        return results
    
    def _may_be_null(self, pointer: 'Variable', location: 'ASTNode') -> bool:
        """检查指针在某个位置是否可能为空"""
        # 使用数据流分析
        # ...
        pass


class ResourceLeakAnalyzer(StaticAnalyzer):
    """资源泄漏分析器"""
    
    @property
    def name(self) -> str:
        return "resource_leak"
    
    def analyze(self, ast: 'AST') -> List[AnalysisResult]:
        results = []
        
        # 追踪资源分配和释放
        allocated = {}
        
        for node in ast.walk():
            if isinstance(node, ResourceAllocation):
                allocated[node.resource_id] = node
            
            elif isinstance(node, ResourceRelease):
                allocated.pop(node.resource_id, None)
        
        # 检查未释放的资源
        for resource_id, alloc_node in allocated.items():
            result = AnalysisResult(
                analyzer=self.name,
                severity='error',
                message=f"资源 '{resource_id}' 未释放，可能导致泄漏",
                location=alloc_node.location,
                suggestion="确保在所有路径上释放资源"
            )
            results.append(result)
        
        return results


class AnalysisScheduler:
    """分析调度器"""
    
    def __init__(self):
        self.analyzers: List[StaticAnalyzer] = []
    
    def register(self, analyzer: StaticAnalyzer) -> None:
        """注册分析器"""
        self.analyzers.append(analyzer)
    
    def run_all(self, ast: 'AST') -> Dict[str, List[AnalysisResult]]:
        """运行所有分析器"""
        results = {}
        
        for analyzer in self.analyzers:
            results[analyzer.name] = analyzer.analyze(ast)
        
        return results
    
    def generate_report(self, results: Dict[str, List[AnalysisResult]]) -> str:
        """生成分析报告"""
        lines = ["# 静态分析报告\n"]
        
        total_issues = sum(len(r) for r in results.values())
        lines.append(f"总计发现 {total_issues} 个问题\n")
        
        for analyzer_name, analyzer_results in results.items():
            if analyzer_results:
                lines.append(f"\n## {analyzer_name}\n")
                for result in analyzer_results:
                    lines.append(f"- [{result.severity}] {result.message}")
                    lines.append(f"  位置: {result.location}")
                    if result.suggestion:
                        lines.append(f"  建议: {result.suggestion}")
        
        return "\n".join(lines)
```

#### 产出物
- `src/analysis/` - 静态分析框架
- `tests/test_static_analysis.py` - 单元测试
- `docs/STATIC_ANALYSIS.md` - 使用指南

#### 验收标准
- [ ] 分析框架可用
- [ ] 内置分析器正确
- [ ] 报告格式清晰
- [ ] 可扩展新分析器

---

## 📊 Phase 4 成功指标

### 技术指标

| 指标 | Week 7 结束 | Week 10 目标 | Week 13 目标 | Week 16 目标 |
|------|------------|-------------|-------------|-------------|
| IR 优化能力 | 基础 | SSA + 数据流 | 循环优化 | 内联优化 |
| 语言特性 | 泛型基础 | 完整泛型 | 模式匹配 | 异步支持 |
| 工具支持 | CLI | CLI + 文档 | LSP 基础 | 完整 LSP + 调试 |
| 测试覆盖率 | 51.86% | 55% | 60% | 65% |
| 文档完整性 | 80% | 85% | 90% | 95% |

### 质量指标

- **代码质量**: 评分 > 75/100
- **性能**: 编译速度提升 > 20%
- **可用性**: IDE 支持完整
- **可维护性**: 文档完整，测试充分

---

## 📅 执行计划

### Week 8-10: 编译器优化技术
- Task 8.1: SSA 构建（3天）
- Task 8.2: 数据流分析（3天）
- Task 8.3: 循环优化（2天）
- Task 8.4: 内联优化（2天）

### Week 11-13: 高级语言特性
- Task 11.1: 泛型编程（4天）
- Task 11.2: 模式匹配（3天）
- Task 11.3: 异步编程（3天）

### Week 14-16: 工具链生态
- Task 14.1: LSP 实现（5天）
- Task 14.2: 调试信息（3天）
- Task 14.3: 静态分析（3天）

---

## 🎓 学习资源

### 编译器优化
1. **《Engineering a Compiler》(2nd Ed)** - Keith Cooper
   - 第 8-10 章：数据流分析
   - 第 13 章：指令调度
   - 第 14 章：寄存器分配

2. **《Advanced Compiler Design and Implementation》** - Steven Muchnick
   - SSA 构建算法
   - 循环优化技术
   - 内联策略

### 语言设计
1. **《Types and Programming Languages》** - Benjamin Pierce
   - 类型系统理论
   - 泛型类型

2. **《Programming Language Pragmatics》** - Michael Scott
   - 模式匹配
   - 异常处理

### 工具开发
1. **Language Server Protocol Specification**
   - https://microsoft.github.io/language-server-protocol/

2. **DWARF Debugging Standard**
   - https://dwarfstd.org/

---

**创建日期**: 2026-04-08
**最后更新**: 2026-04-08
**维护者**: ZHC 开发团队
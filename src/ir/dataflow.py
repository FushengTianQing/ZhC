# -*- coding: utf-8 -*-
"""
ZHC IR - 数据流分析框架

本模块实现了经典的静态数据流分析算法，这些算法是编译器优化的基础。

================================================================================
数据流分析简介
================================================================================

数据流分析是一种静态分析技术，用于收集程序中数据如何流动的信息。
它通过分析程序的控制流图（CFG），在编译时推断程序的运行时行为。

核心概念：
- 控制流图（CFG）：程序的基本块和它们之间的跳转关系
- 数据流值：在程序点上可能的程序状态抽象
- 数据流方程：描述数据如何在程序点之间流动的规则
- 不动点迭代：通过反复应用方程直到收敛来求解

================================================================================
数据流分析的分类
================================================================================

1. 按方向分类：
   - 前向分析（Forward Analysis）：信息从程序入口流向出口
     * 到达定义分析
     * 可用表达式分析
     * 活跃表达式分析
   
   - 后向分析（Backward Analysis）：信息从程序出口流向入口
     * 活跃变量分析
     * 可达定义分析

2. 按格结构分类：
   - May 分析（可能分析）：保守估计，可能包含额外元素
     * 使用并集（∪）合并路径
     * 到达定义分析
   
   - Must 分析（必然分析）：精确估计，只包含确定元素
     * 使用交集（∩）合并路径
     * 可用表达式分析

3. 按格方向分类：
   - 向上格（Increasing Semilattice）：从底向上增长
   - 向下格（Decreasing Semilattice）：从顶向下减少

================================================================================
数据流分析框架
================================================================================

通用数据流方程形式：

前向分析：
  IN[B]  = join(P in pred(B)) OUT[P]    // 合并前驱的出口
  OUT[B] = transfer(B, IN[B])           // 通过传递函数

后向分析：
  OUT[B] = join(S in succ(B)) IN[S]     // 合并后继的入口
  IN[B]  = transfer(B, OUT[B])          // 通过传递函数

其中：
- join：合并操作（并集或交集）
- transfer：传递函数，描述基本块如何转换数据流值

================================================================================
收敛性分析
================================================================================

数据流分析算法保证收敛，因为：
1. 格是有限高度的（有限宽度或有限高度）
2. 每次迭代只增加（或减少）格中的值
3. 格有上界（或下界）

时间复杂度：O(n^2 * h)，其中 n 是基本块数量，h 是格高度
实际中通常很快收敛，因为格高度通常很小。

================================================================================
实现的分析算法
================================================================================

1. 活跃变量分析（Liveness Analysis）
   - 方向：后向
   - 类型：May 分析
   - 用途：寄存器分配、死代码消除
   
2. 到达定义分析（Reaching Definitions）
   - 方向：前向
   - 类型：May 分析
   - 用途：常量传播、复制传播
   
3. 可用表达式分析（Available Expressions）
   - 方向：前向
   - 类型：Must 分析
   - 用途：公共子表达式消除

作者：远
日期：2026-04-08
"""

from typing import Dict, Set, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass

from .instructions import IRBasicBlock, IRInstruction
from .program import IRFunction
from .values import IRValue, ValueKind
from .opcodes import Opcode


# =============================================================================
# 数据流分析基类
# =============================================================================

@dataclass
class DataFlowResult:
    """数据流分析结果
    
    存储数据流分析的输出，包括每个基本块的入口/出口状态，
    以及分析是否收敛和迭代次数。
    
    属性：
        in_state: 基本块标签到入口状态的映射。入口状态表示进入该基本块时的
                  数据流值集合。例如，活跃变量分析中 in_state[B] 表示进入
                  基本块 B 时活跃的变量集合。
        out_state: 基本块标签到出口状态的映射。出口状态表示离开该基本块时的
                  数据流值集合。
        converged: 分析是否收敛。如果在 max_iterations 次迭代内状态不再变化，
                   则收敛；否则可能需要增加迭代次数或检查数据流方程。
        iterations: 实际迭代次数。如果较小（如 < 10），通常表示数据流方程
                    较简单，程序结构不复杂。
    """
    # 基本块标签 -> 入口状态
    in_state: Dict[str, Set[str]]
    # 基本块标签 -> 出口状态
    out_state: Dict[str, Set[str]]
    # 是否收敛
    converged: bool
    # 迭代次数
    iterations: int


class DataFlowAnalysis:
    """
    数据流分析基类
    
    提供通用的数据流分析框架，支持前向和后向分析模式。
    子类需要实现 analyze() 方法和具体的传递函数。
    
    框架设计：
    1. 初始化阶段：构建控制流图，计算基本块的 gen/kill 或 use/def 集合
    2. 迭代阶段：反复应用数据流方程，直到收敛或达到最大迭代次数
    3. 结果阶段：返回包含所有基本块状态的 DataFlowResult
    
    使用示例：
        analysis = LivenessAnalysis(function)
        result = analysis.analyze()
        # 检查 result.in_state[block_label] 获取活跃变量
    
    注意：
    - 不同的分析使用不同的迭代方向和合并操作
    - 基类不直接实现具体算法，子类负责定义数据流方程
    """

    def __init__(self, function: IRFunction):
        """初始化分析器
        
        Args:
            function: 要分析的 IR 函数
        """
        self.function = function

        # 基本块标签 -> 基本块
        self.blocks: Dict[str, IRBasicBlock] = {}
        for bb in function.basic_blocks:
            self.blocks[bb.label] = bb

        # 分析结果
        self.result: Optional[DataFlowResult] = None

    def analyze(self, max_iterations: int = 100) -> DataFlowResult:
        """
        执行数据流分析
        
        子类必须实现此方法。
        
        Args:
            max_iterations: 最大迭代次数，防止无限循环
            
        Returns:
            分析结果 DataFlowResult
            
        Raises:
            NotImplementedError: 子类未实现时抛出
        """
        raise NotImplementedError

    def _get_predecessors(self, block_label: str) -> List[str]:
        """获取前驱基本块的标签列表
        
        前驱块是指控制流可能跳转到当前块的块。
        用于前向数据流分析中合并来自前驱的输出状态。
        
        Args:
            block_label: 目标基本块的标签
            
        Returns:
            前驱块的标签列表，可能为空列表
        """
        block = self.blocks.get(block_label)
        return block.predecessors if block else []

    def _get_successors(self, block_label: str) -> List[str]:
        """获取后继基本块的标签列表
        
        后继块是指当前块的控制流可能跳转到的块。
        用于后向数据流分析中合并来自后继的输入状态。
        
        Args:
            block_label: 源基本块的标签
            
        Returns:
            后继块的标签列表，可能为空列表
        """
        block = self.blocks.get(block_label)
        return block.successors if block else []


# =============================================================================
# 活跃变量分析
# =============================================================================

class LivenessAnalysis(DataFlowAnalysis):
    """
    活跃变量分析（后向数据流分析）
    
    ================================================================================
    理论背景
    ================================================================================
    
    活跃变量的定义：
    变量 v 在程序点 p 是活跃的（live），当且仅当存在一条从 p 到程序出口的
    执行路径，在该路径上 v 被使用，且在 v 被使用之前没有被重新定义。
    
    形式化定义：
    - v 在 p 点活跃 ⟺ ∃ 路径 p → ... → use(v) → ... → exit
      使得路径上没有任何 def(v)（重新定义）
    
    ================================================================================
    为什么需要活跃变量分析？
    ================================================================================
    
    1. 寄存器分配：
       - 只有活跃的变量需要分配寄存器
       - 非活跃变量可以复用寄存器
       
    2. 死代码消除：
       - 如果一个赋值语句的结果在后续没有被使用，则该赋值是死代码
       - 例：x = 5; ...（x 之后不再活跃）→ 可以删除 x = 5
       
    3. 存储优化：
       - 如果变量在寄存器分配后不再活跃，可以写回内存或释放寄存器
    
    4. 指令调度：
       - 确保活跃变量的值不被覆盖
    
    ================================================================================
    数据流方程
    ================================================================================
    
    后向分析框架：
    
    OUT[B] = ⋃ IN[S]  for S ∈ succ(B)
              ↑                    ↑
           后继的入口并集      后继的入口状态
           
    IN[B]  = use[B] ⋃ (OUT[B] - def[B])
              ↑    ↑          ↑      ↑
           使用的  OUT中被定义    在B中定义的
           变量   的变量被移除    变量
    
    方程解释：
    - OUT[B]：离开 B 时的活跃变量 = 所有后继入口的活跃变量的并集
    - IN[B]：进入 B 时的活跃变量 = B 中使用的变量 加上（离开 B 时的活跃变量中
              没有在 B 中被定义的变量）
    
    ================================================================================
    def/use 集合
    ================================================================================
    
    对于基本块 B：
    
    def[B]：B 中定义的变量集合（可能被重新定义）
      = { v | ∃ 指令 i ∈ B 使得 i 定义 v，且 v 在 i 之前没有在 B 中被定义 }
    
    use[B]：B 中"提前"使用的变量集合（在定义之前使用）
      = { v | ∃ 指令 i ∈ B 使得 i 使用 v，且 v 在 i 之前没有在 B 中被定义 }
    
    计算算法（正向扫描）：
      defined = ∅
      used = ∅
      for each instruction i in B:
          for each operand x in i.operands:
              if x ∉ defined:
                  used = used ∪ {x}  // 提前使用
          for each result y in i.results:
              defined = defined ∪ {y}  // 定义
    
    ================================================================================
    迭代算法
    ================================================================================
    
    初始化：
      for each block B:
          IN[B] = ∅
          OUT[B] = ∅
    
    迭代：
      repeat
          changed = false
          for each block B (in reverse postorder):
              OUT[B] = ⋃ IN[S] for S in succ(B)
              NEW_IN = use[B] ⋃ (OUT[B] - def[B])
              if NEW_IN ≠ IN[B]:
                  changed = true
                  IN[B] = NEW_IN
      until not changed
    
    ================================================================================
    格结构
    ================================================================================
    
    格：活跃变量集合的幂集 P(Vars)
    偏序：集合包含关系 ⊆
    底：∅（所有变量都不活跃）
    顶：Vars（所有变量都活跃）
    合并操作：并集 ∪
    
    这是向上收敛的格（monotone increasing）。
    
    ================================================================================
    复杂度分析
    ================================================================================
    
    时间复杂度：O(n * m * k)
    - n: 基本块数量
    - m: 平均基本块大小（指令数）
    - k: 变量数量
    - 实际中 k 通常较小，因为会收敛
    
    空间复杂度：O(n * k)
    - 存储每个基本块的 IN/OUT 状态
    """

    def __init__(self, function: IRFunction):
        """初始化活跃变量分析器
        
        Args:
            function: 要分析的 IR 函数
        """
        super().__init__(function)

        # 基本块标签 -> 定义的变量集合 (def[B])
        self.def_sets: Dict[str, Set[str]] = defaultdict(set)
        # 基本块标签 -> 使用的变量集合 (use[B])
        self.use_sets: Dict[str, Set[str]] = defaultdict(set)

        # 计算每个基本块的 def 和 use 集合
        self._compute_def_use_sets()

    def _compute_def_use_sets(self):
        """计算每个基本块的 def 和 use 集合
        
        使用正向扫描算法：
        - 维护一个 defined 集合，记录当前块中已定义的变量
        - 对于每个操作数，如果变量不在 defined 中，则加入 use
        - 对于每个结果，加入 defined
        
        这种算法确保了 use 集合只包含"提前使用"的变量。
        """
        for label, block in self.blocks.items():
            # 已定义的变量（在当前块中）
            defined: Set[str] = set()
            # 使用的变量（在定义前使用）
            used: Set[str] = set()

            for instr in block.instructions:
                # 处理操作数（使用）
                for operand in instr.operands:
                    if isinstance(operand, IRValue):
                        var_name = self._extract_variable_name(operand)
                        # 只有在变量尚未被定义时才计入 use
                        if var_name and var_name not in defined:
                            used.add(var_name)

                # 处理结果（定义）
                for result in instr.result:
                    if isinstance(result, IRValue):
                        var_name = self._extract_variable_name(result)
                        if var_name:
                            defined.add(var_name)

            self.def_sets[label] = defined
            self.use_sets[label] = used

    def _extract_variable_name(self, value: IRValue) -> Optional[str]:
        """从 IRValue 中提取变量名
        
        处理 IR 值的命名约定：
        - %var → var（临时变量）
        - @var → var（命名变量）
        
        Args:
            value: IR 值对象
            
        Returns:
            提取的变量名（不含前缀），如果不是变量则返回 None
        """
        if value.kind == ValueKind.VAR or value.kind == ValueKind.TEMP:
            name = value.name
            if name.startswith('%'):
                name = name[1:]
            return name
        return None

    def analyze(self, max_iterations: int = 100) -> DataFlowResult:
        """
        执行活跃变量分析
        
        使用后向数据流分析，从出口向入口传播。
        算法采用逆后序遍历以加速收敛。
        
        数据流方程：
        - OUT[B] = ⋃ IN[S]  for S ∈ succ(B)
        - IN[B]  = use[B] ⋃ (OUT[B] - def[B])
        
        Args:
            max_iterations: 最大迭代次数，防止不收敛的情况
            
        Returns:
            DataFlowResult: 包含每个基本块入口/出口活跃变量集合
        """
        # 初始化：所有基本块的 IN 和 OUT 都为空集
        in_state: Dict[str, Set[str]] = {label: set() for label in self.blocks}
        out_state: Dict[str, Set[str]] = {label: set() for label in self.blocks}

        # 按逆后序遍历（提高收敛速度）
        # 逆后序确保我们在处理一个块之前已经处理了它的所有后继
        rpo_order = self._reverse_postorder()

        converged = False
        iterations = 0

        for iteration in range(max_iterations):
            iterations = iteration + 1
            changed = False

            # 按逆后序遍历所有基本块
            for label in rpo_order:
                # OUT[B] = ⋃ IN[S] for S ∈ succ(B)
                # 合并所有后继块的入口状态
                new_out: Set[str] = set()
                for succ in self._get_successors(label):
                    new_out |= in_state[succ]

                # IN[B] = use[B] ⋃ (OUT[B] - def[B])
                # 使用的变量 + （离开时活跃但未在块中定义的变量）
                new_in = self.use_sets[label] | (new_out - self.def_sets[label])

                # 检查是否变化
                if new_in != in_state[label] or new_out != out_state[label]:
                    changed = True

                in_state[label] = new_in
                out_state[label] = new_out

            if not changed:
                converged = True
                break

        self.result = DataFlowResult(
            in_state=in_state,
            out_state=out_state,
            converged=converged,
            iterations=iterations
        )

        return self.result

    def _reverse_postorder(self) -> List[str]:
        """计算逆后序遍历顺序
        
        后序遍历：先遍历所有后继，再处理当前节点
        逆后序：反转后序，得到 DAG 的拓扑序
        
        对于后向分析，逆后序确保：
        - 在处理一个块之前，其所有后继已经处理完毕
        - 这减少了迭代次数，加速收敛
        
        算法：
        1. 从入口块开始 DFS
        2. 访问所有后继后才将当前块加入顺序
        3. 最后反转顺序
        """
        visited: Set[str] = set()
        order: List[str] = []

        def dfs(label: str):
            if label in visited:
                return
            visited.add(label)

            for succ in self._get_successors(label):
                dfs(succ)

            order.append(label)

        # 从入口块开始
        if self.function.entry_block:
            dfs(self.function.entry_block.label)

        # 逆序：得到逆后序
        order.reverse()
        return order

    def is_live_at(self, block_label: str, var_name: str) -> bool:
        """
        检查变量在基本块入口是否活跃
        
        Args:
            block_label: 基本块标签
            var_name: 变量名（不含 % 前缀）
            
        Returns:
            如果变量在入口活跃则返回 True
        """
        if not self.result:
            return False
        return var_name in self.result.in_state.get(block_label, set())

    def get_live_variables(self, block_label: str) -> Set[str]:
        """获取基本块入口的活跃变量集合
        
        Args:
            block_label: 基本块标签
            
        Returns:
            入口处活跃的变量名集合
        """
        if not self.result:
            return set()
        return self.result.in_state.get(block_label, set())


# =============================================================================
# 到达定义分析
# =============================================================================

@dataclass
class Definition:
    """变量定义
    
    表示程序中的一个变量定义位置，用于跟踪定义的传播。
    
    属性：
        variable: 变量名（不含 % 前缀）
        block_label: 定义所在的基本块标签
        instruction_index: 指令在基本块中的索引（从 0 开始）
        
    示例：
        Definition("x", "block1", 3) 表示 "在 block1 的第 3 条指令处定义了 x"
    
    用途：
        - 唯一标识程序中的每个定义点
        - 用于判断某个定义是否"到达"某个程序点
        - 用于常量传播、复制传播等优化
    """
    variable: str  # 变量名
    block_label: str  # 定义所在的基本块
    instruction_index: int  # 指令在基本块中的索引

    def __repr__(self) -> str:
        """字符串表示，格式为: variable@block:index"""
        return f"{self.variable}@{self.block_label}:{self.instruction_index}"

    def __eq__(self, other) -> bool:
        """两个定义相等当且仅当变量、块、索引都相同"""
        if not isinstance(other, Definition):
            return False
        return (self.variable == other.variable and
                self.block_label == other.block_label and
                self.instruction_index == other.instruction_index)

    def __hash__(self) -> int:
        """支持将 Definition 用于集合和字典"""
        return hash((self.variable, self.block_label, self.instruction_index))


class ReachingDefinitionsAnalysis(DataFlowAnalysis):
    """
    到达定义分析（前向数据流分析）
    
    ================================================================================
    理论背景
    ================================================================================
    
    到达定义的定义：
    定义 d（程序中某个变量被赋值的位置）"到达"程序点 p，当且仅当：
    - 存在一条从 d 到 p 的路径
    - 在该路径上，该变量没有被重新定义
    
    形式化：
    d: v = ... 到达 p ⟺ ∃ 路径 d → ... → p，使得路径上没有其他 v 的定义
    
    ================================================================================
    为什么需要到达定义分析？
    ================================================================================
    
    1. 常量传播：
       - 如果所有到达某点的 v 的定义都是 v = c（c 是常量）
       - 则可以将 v 替换为 c
       
    2. 复制传播：
       - 如果所有到达某点的 v 的定义都是 v = w
       - 则可以将 v 替换为 w（如果 w 在该点活跃）
       
    3. 未初始化变量检测：
       - 如果某个定义没有到达某点，说明变量可能未初始化
       - 用于错误检测
       
    4. 别名分析基础：
       - 间接引用的分析需要知道哪些定义可能影响指针解引用
    
    ================================================================================
    数据流方程（前向分析）
    ================================================================================
    
    IN[B]  = ⋃ OUT[P]  for P ∈ pred(B)    // 从所有前驱合并
    OUT[B] = gen[B] ⋃ (IN[B] - kill[B])  // 生成新定义，移除被杀死的
    
    gen[B]：B 中生成的定义集合
      = { d | d 在 B 中定义，且 d 之后没有 v 的重新定义 }
    
    kill[B]：B 中杀死的定义集合
      = { d | d 是 v 的定义，但 B 中有 v 的新定义 }
    
    ================================================================================
    gen/kill 集合的计算
    ================================================================================
    
    对于每个变量 v：
    - v 的所有定义构成一个"定义组"
    - B 中对 v 的定义会 kill 同一组中的所有其他定义
    - B 中对 v 的定义会 gen 自身
    
    算法（正向扫描）：
      generated = ∅
      killed = ∅
      for each instruction i in B (in order):
          if i defines v:
              generated = generated ∪ {d_i}      // d_i 是 i 对 v 的定义
              killed = killed ∪ {d | d 定义 v, d ≠ d_i}  // 杀死其他 v 的定义
    
    ================================================================================
    初始化
    ================================================================================
    
    入口块：IN[entry] = ∅  // 假设没有预定义
    其他块：IN[B] = {所有定义}  // 保守估计
    
    说明：
    - May 分析使用乐观初始化（假设所有定义都可能到达）
    - 迭代会逐步移除不相关的定义
    
    ================================================================================
    格结构
    ================================================================================
    
    格：定义的幂集 P(Definitions)
    偏序：集合包含关系 ⊆
    底：∅
    顶：{所有定义}
    合并操作：并集 ∪
    
    这是向上收敛的格（monotone increasing）。
    
    ================================================================================
    与活跃变量分析的比较
    ================================================================================
    
    | 特性           | 活跃变量      | 到达定义        |
    |---------------|--------------|----------------|
    | 分析方向       | 后向         | 前向            |
    | 合并操作       | 并集 ∪       | 并集 ∪          |
    | 传递函数       | IN = use∪... | OUT = gen∪...  |
    | 初始化         | ∅            | 全部（may）     |
    | 底             | ∅            | ∅              |
    | 用途           | 寄存器分配    | 常量传播        |
    """
    
    # ================================================================================
    # 实现说明
    # ================================================================================
    # 
    # 当前实现使用字符串表示定义，但这有局限性：
    # 1. 空间开销较大
    # 2. 解析开销
    #
    # 更高效的实现应该：
    # 1. 使用 Definition 对象直接存储
    # 2. 重写集合操作以处理 Definition 对象
    # 3. 使用位向量压缩（如果变量数量固定且较少）

    def __init__(self, function: IRFunction):
        """初始化到达定义分析器
        
        Args:
            function: 要分析的 IR 函数
        """
        super().__init__(function)

        # 基本块标签 -> 生成的定义集合 (gen[B])
        self.gen_sets: Dict[str, Set[Definition]] = defaultdict(set)
        # 基本块标签 -> 杀死的定义集合 (kill[B])
        self.kill_sets: Dict[str, Set[Definition]] = defaultdict(set)

        # 所有定义
        self.all_definitions: Set[Definition] = set()

        # 计算每个基本块的 gen 和 kill 集合
        self._compute_gen_kill_sets()

    def _compute_gen_kill_sets(self):
        """计算每个基本块的 gen 和 kill 集合
        
        算法分为两遍：
        第一遍：收集所有定义（建立全局定义组）
        第二遍：计算每个块的 gen/kill
        """
        # 首先收集所有定义
        for label, block in self.blocks.items():
            for idx, instr in enumerate(block.instructions):
                for result in instr.result:
                    if isinstance(result, IRValue):
                        var_name = self._extract_variable_name(result)
                        if var_name:
                            defn = Definition(
                                variable=var_name,
                                block_label=label,
                                instruction_index=idx
                            )
                            self.all_definitions.add(defn)

        # 计算每个基本块的 gen 和 kill
        for label, block in self.blocks.items():
            generated: Set[Definition] = set()
            killed: Set[Definition] = set()

            for idx, instr in enumerate(block.instructions):
                for result in instr.result:
                    if isinstance(result, IRValue):
                        var_name = self._extract_variable_name(result)
                        if var_name:
                            # 新定义
                            defn = Definition(
                                variable=var_name,
                                block_label=label,
                                instruction_index=idx
                            )
                            generated.add(defn)

                            # 杀死其他同名变量的定义（同一组）
                            for other_def in self.all_definitions:
                                if other_def.variable == var_name and other_def != defn:
                                    killed.add(other_def)

            self.gen_sets[label] = generated
            self.kill_sets[label] = killed

    def _extract_variable_name(self, value: IRValue) -> Optional[str]:
        """从 IRValue 中提取变量名"""
        if value.kind == ValueKind.VAR or value.kind == ValueKind.TEMP:
            name = value.name
            if name.startswith('%'):
                name = name[1:]
            return name
        return None

    def analyze(self, max_iterations: int = 100) -> DataFlowResult:
        """
        执行到达定义分析
        
        使用前向数据流分析，从入口向出口传播。
        
        数据流方程：
        - IN[B]  = ⋃ OUT[P] for P ∈ pred(B)
        - OUT[B] = gen[B] ⋃ (IN[B] - kill[B])
        
        Args:
            max_iterations: 最大迭代次数
            
        Returns:
            DataFlowResult: 包含每个基本块入口/出口的定义集合
        """
        # 初始化
        in_state: Dict[str, Set[str]] = {}
        out_state: Dict[str, Set[str]] = {}

        for label in self.blocks:
            if label == self.function.entry_block.label:
                # 入口块：从空集开始
                in_state[label] = set()
            else:
                # 其他块：初始化为所有定义（May 分析的乐观初始化）
                in_state[label] = {str(d) for d in self.all_definitions}
            out_state[label] = {str(d) for d in self.gen_sets[label]}

        # 按后序遍历
        po_order = self._postorder()

        converged = False
        iterations = 0

        for iteration in range(max_iterations):
            iterations = iteration + 1
            changed = False

            for label in po_order:
                # IN[B] = ⋃ OUT[P] for P ∈ pred(B)
                new_in: Set[str] = set()
                preds = self._get_predecessors(label)
                if preds:
                    for pred in preds:
                        new_in |= out_state[pred]
                else:
                    # 入口块
                    new_in = set()

                # OUT[B] = gen[B] ⋃ (IN[B] - kill[B])
                new_out = {str(d) for d in self.gen_sets[label]}
                for def_str in new_in:
                    # 检查是否被杀死
                    defn = self._parse_definition(def_str)
                    if defn and defn not in self.kill_sets[label]:
                        new_out.add(def_str)

                # 检查是否变化
                if new_in != in_state[label] or new_out != out_state[label]:
                    changed = True

                in_state[label] = new_in
                out_state[label] = new_out

            if not changed:
                converged = True
                break

        self.result = DataFlowResult(
            in_state=in_state,
            out_state=out_state,
            converged=converged,
            iterations=iterations
        )

        return self.result

    def _postorder(self) -> List[str]:
        """计算后序遍历顺序
        
        后序遍历：先遍历所有前驱，再处理当前节点
        对于前向分析，按后序处理可以较早收敛
        """
        visited: Set[str] = set()
        order: List[str] = []

        def dfs(label: str):
            if label in visited:
                return
            visited.add(label)

            for pred in self._get_predecessors(label):
                dfs(pred)

            order.append(label)

        # 从所有块开始
        for label in self.blocks:
            dfs(label)

        return order

    def _parse_definition(self, def_str: str) -> Optional[Definition]:
        """解析定义字符串
        
        字符串格式：variable@block:index
        
        Args:
            def_str: 定义字符串
            
        Returns:
            解析后的 Definition 对象，或 None（解析失败）
        """
        try:
            # 格式: variable@block:index
            parts = def_str.split('@')
            if len(parts) != 2:
                return None

            variable = parts[0]
            rest = parts[1].split(':')
            if len(rest) != 2:
                return None

            block_label = rest[0]
            instruction_index = int(rest[1])

            return Definition(
                variable=variable,
                block_label=block_label,
                instruction_index=instruction_index
            )
        except:
            return None

    def get_reaching_definitions(self, block_label: str, var_name: str) -> Set[Definition]:
        """
        获取到达某个基本块入口的变量定义
        
        Args:
            block_label: 基本块标签
            var_name: 变量名（不含 % 前缀）
            
        Returns:
            到达该点的该变量的所有定义集合
        """
        if not self.result:
            return set()

        definitions: Set[Definition] = set()
        for def_str in self.result.in_state.get(block_label, set()):
            defn = self._parse_definition(def_str)
            if defn and defn.variable == var_name:
                definitions.add(defn)

        return definitions


# =============================================================================
# 可用表达式分析
# =============================================================================

@dataclass
class Expression:
    """表达式
    
    表示程序中的一个二元表达式，用于可用表达式分析。
    
    属性：
        operator: 操作符名称（如 "ADD", "MUL", "LT"）
        operands: 操作数元组（变量名或常量）
        
    示例：
        Expression("ADD", ("x", "y")) 表示 x + y
        Expression("LT", ("a", "b")) 表示 a < b
        
    用途：
        - 跟踪哪些表达式已经被计算过
        - 识别公共子表达式
        - 优化重复计算
    """
    operator: str  # 操作符
    operands: Tuple[str, ...]  # 操作数

    def __repr__(self) -> str:
        """字符串表示，格式为: operator(op1, op2)"""
        operands_str = ", ".join(self.operands)
        return f"{self.operator}({operands_str})"

    def __eq__(self, other) -> bool:
        """两个表达式相等当且仅当操作符和操作数都相同"""
        if not isinstance(other, Expression):
            return False
        return self.operator == other.operator and self.operands == other.operands

    def __hash__(self) -> int:
        """支持将 Expression 用于集合和字典"""
        return hash((self.operator, self.operands))


class AvailableExpressionsAnalysis(DataFlowAnalysis):
    """
    可用表达式分析（前向数据流分析）
    
    ================================================================================
    理论背景
    ================================================================================
    
    可用表达式的定义：
    表达式 e 在程序点 p 是可用的（available），当且仅当：
    - 从程序入口到 p 的所有路径上都计算了 e
    - 在最后一次计算 e 之后，e 的操作数都没有被重新定义
    
    形式化：
    e 在 p 点可用 ⟺ ∀ 路径 entry → ... → p：
                      ∃ 计算点 c，使得 c 在路径上，且路径上 c → p 没有 e 操作数的定义
    
    ================================================================================
    为什么需要可用表达式分析？
    ================================================================================
    
    1. 公共子表达式消除（CSE）：
       - 如果表达式 e 在 p 点可用
       - 且在 p 点需要计算 e
       - 则可以直接使用之前的计算结果，无需重新计算
       
    2. 强度削减：
       - 识别重复计算的表达式
       - 优化为更高效的计算方式
       
    3. 死代码消除：
       - 如果一个表达式的结果不再可用
       - 且没有被使用，则该计算是死代码
    
    ================================================================================
    数据流方程（前向分析）
    ================================================================================
    
    IN[B]  = ⋂ OUT[P]  for P ∈ pred(B)    // 所有前驱的交集
    OUT[B] = gen[B] ⋃ (IN[B] - kill[B])  // 生成新表达式，移除被杀死的
    
    注意：这是 Must 分析，使用交集（∩）而非并集（∪）
    
    gen[B]：B 中生成的表达式集合
      = { e | e 在 B 中被计算，且 e 的操作数在 B 中没有被重新定义 }
    
    kill[B]：B 中杀死的表达式集合
      = { e | e 的某个操作数在 B 中被重新定义 }
    
    ================================================================================
    gen/kill 集合的计算
    ================================================================================
    
    对于基本块 B：
    
    第一遍：收集所有表达式
      all_exprs = { e | e 在程序中被计算 }
    
    第二遍：计算 gen 和 kill
      generated = ∅
      killed = ∅
      defined_vars = ∅
      
      for each instruction i in B (in order):
          if i computes e:
              generated = generated ∪ {e}
          
          if i defines v:
              defined_vars = defined_vars ∪ {v}
              killed = killed ∪ {e | e ∈ all_exprs, v ∈ operands(e)}
      
      gen[B] = generated
      kill[B] = killed
    
    ================================================================================
    初始化
    ================================================================================
    
    入口块：IN[entry] = ∅  // 没有可用表达式
    其他块：IN[B] = {所有表达式}  // 保守初始化
    
    注意：Must 分析的初始化是乐观的（假设所有表达式都可用）
    迭代会逐步移除不满足条件的表达式
    
    ================================================================================
    格结构
    ================================================================================
    
    格：表达式的幂集 P(Expressions)
    偏序：集合包含关系 ⊆
    底：∅
    顶：{所有表达式}
    合并操作：交集 ∩（Must 分析）
    
    这是向下收敛的格（monotone decreasing）。
    
    ================================================================================
    与到达定义分析的比较
    ================================================================================
    
    | 特性           | 到达定义        | 可用表达式      |
    |---------------|----------------|----------------|
    | 分析方向       | 前向           | 前向            |
    | 分析类型       | May            | Must            |
    | 合并操作       | 并集 ∪         | 交集 ∩          |
    | 初始化         | 全部           | ∅               |
    | 用途           | 常量传播       | 公共子表达式消除 |
    
    ================================================================================
    复杂度分析
    ================================================================================
    
    时间复杂度：O(n * m * e)
    - n: 基本块数量
    - m: 平均基本块大小（指令数）
    - e: 表达式数量
    - 实际中 e 通常较小，因为会收敛
    
    空间复杂度：O(n * e)
    - 存储每个基本块的 IN/OUT 状态
    """

    def __init__(self, function: IRFunction):
        """初始化可用表达式分析器
        
        Args:
            function: 要分析的 IR 函数
        """
        super().__init__(function)

        # 基本块标签 -> 生成的表达式集合 (gen[B])
        self.gen_sets: Dict[str, Set[Expression]] = defaultdict(set)
        # 基本块标签 -> 杀死的表达式集合 (kill[B])
        self.kill_sets: Dict[str, Set[Expression]] = defaultdict(set)

        # 所有表达式（全局）
        self.all_expressions: Set[Expression] = set()

        # 计算每个基本块的 gen 和 kill 集合
        self._compute_gen_kill_sets()

    def _compute_gen_kill_sets(self):
        """计算每个基本块的 gen 和 kill 集合
        
        算法分为两遍：
        第一遍：收集程序中所有表达式
        第二遍：计算每个块的 gen/kill
        """
        # 首先收集所有表达式
        for label, block in self.blocks.items():
            for instr in block.instructions:
                expr = self._extract_expression(instr)
                if expr:
                    self.all_expressions.add(expr)

        # 计算每个基本块的 gen 和 kill
        for label, block in self.blocks.items():
            generated: Set[Expression] = set()
            killed: Set[Expression] = set()

            # 记录当前块中定义的变量
            defined_vars: Set[str] = set()

            for instr in block.instructions:
                # 提取表达式
                expr = self._extract_expression(instr)
                if expr:
                    generated.add(expr)

                # 提取定义的变量
                for result in instr.result:
                    if isinstance(result, IRValue):
                        var_name = self._extract_variable_name(result)
                        if var_name:
                            defined_vars.add(var_name)

            # 杀死包含已定义变量的表达式
            for expr in self.all_expressions:
                for operand in expr.operands:
                    if operand in defined_vars:
                        killed.add(expr)
                        break

            self.gen_sets[label] = generated
            self.kill_sets[label] = killed

    def _extract_expression(self, instr: IRInstruction) -> Optional[Expression]:
        """从指令中提取表达式
        
        只提取二元运算和比较运算的表达式。
        
        Args:
            instr: IR 指令
            
        Returns:
            提取的表达式，如果不是二元运算则返回 None
        """
        # 只处理二元运算和比较运算
        if instr.opcode in [
            Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.DIV, Opcode.MOD,
            Opcode.AND, Opcode.OR, Opcode.XOR,
            Opcode.EQ, Opcode.NE, Opcode.LT, Opcode.LE, Opcode.GT, Opcode.GE
        ]:
            if len(instr.operands) >= 2:
                operands = []
                for op in instr.operands[:2]:
                    if isinstance(op, IRValue):
                        var_name = self._extract_variable_name(op)
                        if var_name:
                            operands.append(var_name)
                        else:
                            operands.append(op.name)
                    else:
                        operands.append(str(op))

                if len(operands) == 2:
                    return Expression(
                        operator=instr.opcode.name,
                        operands=tuple(operands)
                    )

        return None

    def _extract_variable_name(self, value: IRValue) -> Optional[str]:
        """从 IRValue 中提取变量名"""
        if value.kind == ValueKind.VAR or value.kind == ValueKind.TEMP:
            name = value.name
            if name.startswith('%'):
                name = name[1:]
            return name
        return None

    def analyze(self, max_iterations: int = 100) -> DataFlowResult:
        """
        执行可用表达式分析
        
        使用前向数据流分析，从入口向出口传播。
        
        数据流方程（Must 分析）：
        - IN[B]  = ⋂ OUT[P] for P ∈ pred(B)    // 交集
        - OUT[B] = gen[B] ⋃ (IN[B] - kill[B])
        
        Args:
            max_iterations: 最大迭代次数
            
        Returns:
            DataFlowResult: 包含每个基本块入口/出口的可用表达式集合
        """
        # 初始化
        in_state: Dict[str, Set[str]] = {}
        out_state: Dict[str, Set[str]] = {}

        for label in self.blocks:
            if label == self.function.entry_block.label:
                # 入口块：从空集开始
                in_state[label] = set()
            else:
                # 其他块：初始化为所有表达式（Must 分析的乐观初始化）
                in_state[label] = {str(e) for e in self.all_expressions}
            out_state[label] = {str(e) for e in self.gen_sets[label]}

        # 按后序遍历
        po_order = self._postorder()

        converged = False
        iterations = 0

        for iteration in range(max_iterations):
            iterations = iteration + 1
            changed = False

            for label in po_order:
                # IN[B] = ⋂ OUT[P] for P ∈ pred(B)
                new_in: Set[str] = set()
                preds = self._get_predecessors(label)
                if preds:
                    # 对于 must 分析，使用交集
                    first = True
                    for pred in preds:
                        if first:
                            new_in = out_state[pred].copy()
                            first = False
                        else:
                            new_in &= out_state[pred]
                else:
                    # 入口块
                    new_in = set()

                # OUT[B] = gen[B] ⋃ (IN[B] - kill[B])
                new_out = {str(e) for e in self.gen_sets[label]}
                for expr_str in new_in:
                    # 检查是否被杀死
                    expr = self._parse_expression(expr_str)
                    if expr and expr not in self.kill_sets[label]:
                        new_out.add(expr_str)

                # 检查是否变化
                if new_in != in_state[label] or new_out != out_state[label]:
                    changed = True

                in_state[label] = new_in
                out_state[label] = new_out

            if not changed:
                converged = True
                break

        self.result = DataFlowResult(
            in_state=in_state,
            out_state=out_state,
            converged=converged,
            iterations=iterations
        )

        return self.result

    def _postorder(self) -> List[str]:
        """计算后序遍历顺序
        
        后序遍历：先遍历所有前驱，再处理当前节点
        对于前向分析，按后序处理可以较早收敛
        """
        visited: Set[str] = set()
        order: List[str] = []

        def dfs(label: str):
            if label in visited:
                return
            visited.add(label)

            for pred in self._get_predecessors(label):
                dfs(pred)

            order.append(label)

        for label in self.blocks:
            dfs(label)

        return order

    def _parse_expression(self, expr_str: str) -> Optional[Expression]:
        """解析表达式字符串
        
        字符串格式：operator(op1, op2)
        
        Args:
            expr_str: 表达式字符串
            
        Returns:
            解析后的 Expression 对象，或 None（解析失败）
        """
        try:
            # 格式: operator(op1, op2)
            parts = expr_str.split('(')
            if len(parts) != 2:
                return None

            operator = parts[0]
            operands_str = parts[1].rstrip(')')
            operands = tuple(op.strip() for op in operands_str.split(','))

            return Expression(operator=operator, operands=operands)
        except:
            return None

    def is_available(self, block_label: str, expr: Expression) -> bool:
        """
        检查表达式在基本块入口是否可用
        
        Args:
            block_label: 基本块标签
            expr: 表达式
            
        Returns:
            如果表达式在入口可用则返回 True
        """
        if not self.result:
            return False
        return str(expr) in self.result.in_state.get(block_label, set())


# =============================================================================
# 便捷函数
# =============================================================================

def analyze_liveness(function: IRFunction) -> DataFlowResult:
    """
    便捷函数：执行活跃变量分析

    Args:
        function: IR 函数

    Returns:
        分析结果
    """
    analysis = LivenessAnalysis(function)
    return analysis.analyze()


def analyze_reaching_definitions(function: IRFunction) -> DataFlowResult:
    """
    便捷函数：执行到达定义分析

    Args:
        function: IR 函数

    Returns:
        分析结果
    """
    analysis = ReachingDefinitionsAnalysis(function)
    return analysis.analyze()


def analyze_available_expressions(function: IRFunction) -> DataFlowResult:
    """
    便捷函数：执行可用表达式分析

    Args:
        function: IR 函数

    Returns:
        分析结果
    """
    analysis = AvailableExpressionsAnalysis(function)
    return analysis.analyze()

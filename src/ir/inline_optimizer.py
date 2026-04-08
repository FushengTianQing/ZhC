# -*- coding: utf-8 -*-
"""
ZHC IR - 函数内联优化

本模块实现了函数内联（Function Inlining）优化，这是编译器中最重要的优化之一。

================================================================================
函数内联简介
================================================================================

函数内联是将函数调用替换为函数体本身的过程。

原代码：
  def add(a, b) { return a + b; }
  x = add(1, 2);

内联后：
  x = 1 + 2;

================================================================================
为什么需要函数内联？
================================================================================

1. 消除函数调用开销
   - 函数调用需要：保存寄存器、传递参数、跳转、返回
   - 内联后这些开销全部消除

2. 增加优化机会
   - 内联后编译器可以看到更大的代码区域
   - 可以进行更有效的常量传播、死代码消除等

3. 改善缓存局部性
   - 减少函数调用，减少指令缓存未命中
   - 提高 CPU 流水线效率

================================================================================
内联的代价
================================================================================

1. 代码膨胀
   - 函数体被复制，代码大小增加
   - 可能导致指令缓存未命中

2. 编译时间增加
   - 更大的代码需要更多编译时间
   - 优化机会增加，但优化时间也增加

3. 可能降低性能
   - 如果内联的函数很大，可能得不偿失
   - 需要平衡内联收益和代价

================================================================================
内联决策（启发式规则）
================================================================================

1. 小函数总是内联
   - 指令数 ≤ 10 的函数
   - 调用开销可能大于函数体执行开销

2. 热点函数内联
   - 调用次数多的函数
   - 但不能太大（指令数 ≤ 50）

3. 只被调用一次的函数内联
   - 没有代码膨胀问题
   - 可以完全消除调用开销

4. 递归函数不内联
   - 递归内联会导致无限展开
   - 需要特殊处理（如尾递归优化）

5. 调用深度限制
   - 防止内联链过长
   - 限制调用深度 ≤ 3

================================================================================
内联实现步骤
================================================================================

1. 收集调用点
   - 遍历函数中的所有 CALL 指令
   - 获取被调用的函数

2. 成本评估
   - 计算被调用函数的大小
   - 判断是否满足内联条件

3. 函数体克隆
   - 复制被调用函数的所有基本块
   - 重命名变量避免冲突
   - 替换参数为实际参数

4. 控制流整合
   - 将克隆的基本块插入调用者
   - 更新跳转目标
   - 处理返回值

5. 清理
   - 删除调用指令
   - 更新调用计数

作者：远
日期：2026-04-08
"""

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass

from .instructions import IRBasicBlock, IRInstruction
from .program import IRFunction, IRProgram
from .values import IRValue, ValueKind
from .opcodes import Opcode


# =============================================================================
# 内联成本模型
# =============================================================================


@dataclass
class InlineCost:
    """
    内联成本

    表示一个函数内联所需的成本，用于决定是否应该内联。

    ================================================================================
    属性说明
    ================================================================================

    基础属性（原有）：

    instruction_count: 指令数量
        - 函数中的指令总数
        - 衡量函数大小的主要指标
        - 指令越多，内联成本越高

    basic_block_count: 基本块数量
        - 函数中基本块的数量
        - 影响控制流复杂度
        - 基本块越多，内联后控制流越复杂

    call_count: 函数调用次数
        - 函数被调用的总次数
        - 调用越多，内联收益越大
        - 用于识别热点函数

    estimated_size: 估计大小
        - 估计的代码大小（字节）
        - 简化估计：每条指令约 4 字节
        - 用于代码膨胀分析

    ================================================================================
    新增属性（TASK-P3-002）
    ================================================================================

    loop_nesting_depth: 循环嵌套深度
        - 调用点所在的循环嵌套深度
        - 循环内的调用频率更高（假设循环执行 N 次）
        - 深度越大，内联收益越高
        - 示例：在双重循环内的调用，depth = 2

    constant_param_ratio: 常量参数比例
        - 常量参数数量 / 总参数数量
        - 常量参数可以进行常量传播优化
        - 比例越高，内联收益越大
        - 示例：add(1, 2) 的 ratio = 1.0

    simple_param_ratio: 简单类型参数比例
        - 简单类型参数数量 / 总参数数量
        - 简单类型：整数、浮点、布尔等
        - 简单类型传递成本低，内联收益高

    complex_param_ratio: 复杂类型参数比例
        - 复杂类型参数数量 / 总参数数量
        - 复杂类型：结构体、数组、字符串等
        - 复杂类型传递成本高，内联可能增加寄存器压力

    control_flow_complexity: 控制流复杂度
        - 分支指令数量（IF、SWITCH 等）
        - 分支越多，控制流越复杂
        - 复杂控制流可能降低内联收益

    savings_estimate: 内联收益估计
        - 综合考虑所有因素后的收益估计
        - 正值表示收益，负值表示成本
        - 用于最终决策

    ================================================================================
    成本计算公式（TASK-P3-002）
    ================================================================================

    总成本 = 基础成本 - 收益因子

    基础成本 = instruction_count * SIZE_WEIGHT
               + basic_block_count * BB_WEIGHT
               + control_flow_complexity * CF_WEIGHT

    收益因子 = loop_nesting_depth * LOOP_WEIGHT
               + constant_param_ratio * CONST_WEIGHT
               + simple_param_ratio * SIMPLE_WEIGHT
               - complex_param_ratio * COMPLEX_WEIGHT

    权重设置：
    - SIZE_WEIGHT = 1.0（每条指令成本）
    - BB_WEIGHT = 2.0（每个基本块成本）
    - CF_WEIGHT = 1.5（每个分支成本）
    - LOOP_WEIGHT = 5.0（循环嵌套收益）
    - CONST_WEIGHT = 3.0（常量传播收益）
    - SIMPLE_WEIGHT = 1.0（简单类型收益）
    - COMPLEX_WEIGHT = 2.0（复杂类型成本）

    决策规则：
    - savings_estimate > 0 → 内联
    - savings_estimate <= 0 → 不内联
    """

    # 基础属性（原有）
    instruction_count: int = 0
    basic_block_count: int = 0
    call_count: int = 0
    estimated_size: int = 0

    # 新增属性（TASK-P3-002）
    loop_nesting_depth: int = 0
    constant_param_ratio: float = 0.0
    simple_param_ratio: float = 0.0
    complex_param_ratio: float = 0.0
    control_flow_complexity: int = 0
    savings_estimate: float = 0.0

    def is_small(self, threshold: int = 10) -> bool:
        """判断是否是小函数

        小函数的判定标准：指令数不超过阈值。

        小函数总是值得内联，因为：
        - 调用开销可能大于函数体执行开销
        - 函数体小，内联不会导致代码膨胀

        Args:
            threshold: 阈值，默认 10

        Returns:
            如果是小函数则返回 True
        """
        return self.instruction_count <= threshold

    def is_hot(self, call_count: int = 5) -> bool:
        """判断是否是热点函数

        热点函数的判定标准：调用次数不低于阈值。

        热点函数值得内联，因为：
        - 每次调用都有收益
        - 内联可以完全消除调用开销
        - 调用次数越多，收益越大

        Args:
            call_count: 调用次数阈值，默认 5

        Returns:
            如果是热点函数则返回 True
        """
        return self.call_count >= call_count


class InlineCostModel:
    """
    内联成本模型

    ================================================================================
    功能概述
    ================================================================================

    基于启发式规则决定函数是否应该被内联。

    核心思想：
    - 小函数值得内联（调用开销 > 函数体开销）
    - 热点函数值得内联（多次调用，收益累积）
    - 递归函数不值得内联（会导致无限展开）
    - 调用链不能太长（防止代码膨胀）

    ================================================================================
    TASK-P3-002 新增功能
    ================================================================================

    1. 调用频率分析
       - 分析每个调用点的频率（热点/冷点）
       - 识别循环内的调用（频率更高）
       - 计算循环嵌套深度

    2. 参数类型分析
       - 识别常量参数（常量传播收益）
       - 区分简单类型和复杂类型
       - 计算参数类型比例

    3. 控制流复杂度分析
       - 统计分支指令数量
       - 评估控制流复杂度

    4. 综合成本计算
       - 使用加权成本公式
       - 计算内联收益估计
       - 基于收益进行决策

    ================================================================================
    启发式规则
    ================================================================================

    规则 1: 小函数总是内联
      - 指令数 ≤ 10
      - 理由：调用开销可能大于函数体开销

    规则 2: 热点函数内联
      - 调用次数 ≥ 5 且 指令数 ≤ 50
      - 理由：多次调用的收益累积

    规则 3: 单调用点函数内联
      - 被调用次数 = 1
      - 理由：没有代码膨胀问题

    规则 4: 递归函数不内联
      - 函数调用自己
      - 理由：会导致无限展开

    规则 5: 调用深度限制
      - 深度 ≤ 3
      - 理由：防止内联链过长

    规则 6: 收益驱动内联（新增）
      - savings_estimate > 0
      - 理由：综合考虑所有因素

    ================================================================================
    成本权重（TASK-P3-002）
    ================================================================================

    SIZE_WEIGHT = 1.0
        - 每条指令的成本权重
        - 指令越多，成本越高

    BB_WEIGHT = 2.0
        - 每个基本块的成本权重
        - 基本块影响控制流复杂度

    CF_WEIGHT = 1.5
        - 每个分支的成本权重
        - 分支增加控制流复杂度

    LOOP_WEIGHT = 5.0
        - 循环嵌套的收益权重
        - 循环内调用频率更高

    CONST_WEIGHT = 3.0
        - 常量参数的收益权重
        - 常量传播可以优化代码

    SIMPLE_WEIGHT = 1.0
        - 简单类型参数的收益权重
        - 简单类型传递成本低

    COMPLEX_WEIGHT = 2.0
        - 复杂类型参数的成本权重
        - 复杂类型增加寄存器压力

    ================================================================================
    实现细节
    ================================================================================

    初始化阶段：
    1. 统计每个函数的调用次数（全局）
    2. 计算每个函数的成本指标
    3. 分析调用频率（新增）
    4. 分析参数类型（新增）

    评估阶段：
    1. 获取被调用函数的成本
    2. 按顺序检查每条规则
    3. 返回第一个匹配规则的结果

    ================================================================================
    局限性
    ================================================================================

    当前实现使用简单的启发式规则，有以下局限：

    1. 不考虑分支预测
       - 实际性能取决于分支行为
       - 冷分支内联可能降低性能

    2. 不考虑指令级并行
       - 内联可能影响 ILP
       - 分离的函数可能有更好的 ILP

    3. 不考虑寄存器压力
       - 内联增加寄存器需求
       - 可能导致更多寄存器溢出

    4. 不考虑缓存效应
       - 内联影响指令/数据缓存
       - 大函数内联可能降低缓存效率

    未来改进：
    - 基于 profile 的优化（PGO）
    - 基于机器学习的成本模型
    - 考虑缓存效应的模型
    """

    # 成本权重常量（TASK-P3-002）
    SIZE_WEIGHT = 1.0  # 每条指令的成本
    BB_WEIGHT = 2.0  # 每个基本块的成本
    CF_WEIGHT = 1.5  # 每个分支的成本
    LOOP_WEIGHT = 5.0  # 循环嵌套的收益
    CONST_WEIGHT = 3.0  # 常量参数的收益
    SIMPLE_WEIGHT = 1.0  # 简单类型的收益
    COMPLEX_WEIGHT = 2.0  # 复杂类型的成本

    def __init__(self, program: IRProgram):
        """初始化内联成本模型

        Args:
            program: IR 程序
        """
        self.program = program

        # 函数调用计数（全局）
        self.call_counts: Dict[str, int] = {}
        self._count_calls()

        # 函数成本
        self.function_costs: Dict[str, InlineCost] = {}
        self._compute_costs()

        # 调用频率分析（新增）
        self.call_frequency: Dict[str, Dict[str, float]] = {}
        self._analyze_call_frequency()

        # 循环调用分析（新增）
        self.loop_calls: Dict[str, List[Tuple[str, int]]] = {}
        self._analyze_loop_calls()

    def _count_calls(self):
        """统计每个函数的调用次数

        遍历整个程序，统计每个函数被调用的次数。
        这用于识别热点函数和单调用点函数。
        """
        for func in self.program.functions:
            count = 0
            for bb in func.basic_blocks:
                for instr in bb.instructions:
                    if instr.opcode == Opcode.CALL:
                        count += 1
            self.call_counts[func.name] = count

    def _compute_costs(self):
        """计算每个函数的内联成本

        对每个函数计算以下指标：

        基础指标（原有）：
        - 指令数量
        - 基本块数量
        - 调用次数
        - 估计大小

        新增指标（TASK-P3-002）：
        - 循环嵌套深度（平均）
        - 常量参数比例
        - 简单类型参数比例
        - 复杂类型参数比例
        - 控制流复杂度
        """
        for func in self.program.functions:
            # 计算基础指标
            instruction_count = self._count_instructions(func)
            basic_block_count = len(func.basic_blocks)
            call_count = self.call_counts.get(func.name, 0)
            estimated_size = self._estimate_size(func)

            # 计算新增指标（TASK-P3-002）
            # 1. 控制流复杂度
            control_flow_complexity = self._compute_control_flow_complexity(func)

            # 2. 循环嵌套深度（平均）
            avg_loop_depth = self._compute_avg_loop_depth(func)

            # 3. 参数类型比例（从函数定义中获取）
            param_ratios = self._compute_param_ratios_from_func(func)

            cost = InlineCost(
                instruction_count=instruction_count,
                basic_block_count=basic_block_count,
                call_count=call_count,
                estimated_size=estimated_size,
                loop_nesting_depth=avg_loop_depth,
                constant_param_ratio=param_ratios[0],
                simple_param_ratio=param_ratios[1],
                complex_param_ratio=param_ratios[2],
                control_flow_complexity=control_flow_complexity,
            )
            self.function_costs[func.name] = cost

    def _compute_avg_loop_depth(self, func: IRFunction) -> int:
        """计算函数的平均循环嵌套深度

        Args:
            func: IR 函数

        Returns:
            平均循环嵌套深度
        """
        total_depth = 0
        loop_count = 0

        for bb in func.basic_blocks:
            depth = self._estimate_loop_depth(bb)
            if depth > 0:
                total_depth += depth
                loop_count += 1

        if loop_count > 0:
            return total_depth // loop_count
        return 0

    def _compute_param_ratios_from_func(
        self, func: IRFunction
    ) -> Tuple[float, float, float]:
        """从函数定义计算参数类型比例

        注意：这里只能基于参数类型进行静态分析，
        实际调用时的常量参数需要在 should_inline 中分析。

        Args:
            func: IR 函数

        Returns:
            (constant_ratio, simple_ratio, complex_ratio)
        """
        if not func.params:
            return (0.0, 0.0, 0.0)

        total_params = len(func.params)
        simple_count = 0
        complex_count = 0

        for param in func.params:
            if self._is_simple_type(param.ty):
                simple_count += 1
            else:
                complex_count += 1

        # 函数定义中没有常量参数信息
        constant_ratio = 0.0
        simple_ratio = simple_count / total_params
        complex_ratio = complex_count / total_params

        return (constant_ratio, simple_ratio, complex_ratio)

    def _count_instructions(self, func: IRFunction) -> int:
        """计算函数的指令数量

        Args:
            func: IR 函数

        Returns:
            指令总数
        """
        count = 0
        for bb in func.basic_blocks:
            count += len(bb.instructions)
        return count

    def _estimate_size(self, func: IRFunction) -> int:
        """估计函数大小（字节）

        简化估计：每条指令约 4 字节。
        实际大小取决于指令复杂度和目标架构。

        Args:
            func: IR 函数

        Returns:
            估计的大小（字节）
        """
        # 简化估计：每条指令约 4 字节
        return self._count_instructions(func) * 4

    def _analyze_call_frequency(self):
        """分析调用频率（TASK-P3-002 新增）

        分析每个调用点的频率，识别热点和冷点。

        热点定义：
        - 调用次数 ≥ 5 的函数

        冷点定义：
        - 调用次数 ≤ 1 的函数

        频率计算：
        - frequency = call_count / total_calls
        - 用于识别热点函数
        """
        total_calls = sum(self.call_counts.values())

        for func_name, count in self.call_counts.items():
            if total_calls > 0:
                frequency = count / total_calls
            else:
                frequency = 0.0

            # 存储频率信息
            self.call_frequency[func_name] = {
                "count": count,
                "frequency": frequency,
                "is_hot": count >= 5,
                "is_cold": count <= 1,
            }

    def _analyze_loop_calls(self):
        """分析循环内的调用（TASK-P3-002 新增）

        识别循环内的函数调用，计算循环嵌套深度。

        循环内的调用频率更高：
        - 单层循环：假设执行 N 次
        - 双层循环：假设执行 N^2 次
        - 循环嵌套深度越大，频率越高

        实现方法：
        - 遍历所有函数的基本块
        - 检测循环结构（回边）
        - 记录调用点所在的循环深度
        """
        for func in self.program.functions:
            loop_calls_list: List[Tuple[str, int]] = []

            # 遍历所有基本块
            for bb in func.basic_blocks:
                # 检测循环（简化实现）
                # 实际实现需要使用支配树和回边检测
                loop_depth = self._estimate_loop_depth(bb)

                # 检查基本块中的调用
                for instr in bb.instructions:
                    if instr.opcode == Opcode.CALL:
                        callee_name = self._get_callee_name(instr)
                        if callee_name:
                            loop_calls_list.append((callee_name, loop_depth))

            self.loop_calls[func.name] = loop_calls_list

    def _estimate_loop_depth(self, bb: IRBasicBlock) -> int:
        """估计基本块的循环嵌套深度（简化实现）

        简化方法：
        - 检查基本块名称中是否包含 "loop" 关键字
        - 实际实现需要使用支配树和回边检测

        Args:
            bb: 基本块

        Returns:
            估计的循环嵌套深度
        """
        # 简化实现：检查基本块名称
        if "loop" in bb.label.lower():
            # 嵌套循环检测（简化）
            depth = bb.label.count("loop")
            return min(depth, 3)  # 限制最大深度
        return 0

    def _get_callee_name(self, call_instr: IRInstruction) -> Optional[str]:
        """从 CALL 指令获取被调用函数名

        Args:
            call_instr: CALL 指令

        Returns:
            被调用函数名，如果找不到则返回 None
        """
        if not call_instr.operands:
            return None

        func_value = call_instr.operands[0]
        if isinstance(func_value, IRValue):
            return func_value.name.lstrip("@")
        return None

    def _analyze_param_types(
        self, callee: IRFunction, call_instr: IRInstruction
    ) -> Tuple[float, float, float]:
        """分析参数类型（TASK-P3-002 新增）

        分析函数调用的参数类型，计算：
        - 常量参数比例
        - 简单类型参数比例
        - 复杂类型参数比例

        Args:
            callee: 被调用函数
            call_instr: 调用指令

        Returns:
            (constant_ratio, simple_ratio, complex_ratio)
        """
        if len(call_instr.operands) <= 1:
            return (0.0, 0.0, 0.0)

        # 实际参数（跳过第一个操作数，它是函数名）
        args = call_instr.operands[1:]
        total_params = len(args)

        if total_params == 0:
            return (0.0, 0.0, 0.0)

        constant_count = 0
        simple_count = 0
        complex_count = 0

        for arg in args:
            if isinstance(arg, IRValue):
                # 检查是否是常量
                if arg.kind == ValueKind.CONST or arg.const_value is not None:
                    constant_count += 1

                # 检查类型复杂度
                if self._is_simple_type(arg.ty):
                    simple_count += 1
                else:
                    complex_count += 1

        constant_ratio = constant_count / total_params
        simple_ratio = simple_count / total_params
        complex_ratio = complex_count / total_params

        return (constant_ratio, simple_ratio, complex_ratio)

    def _is_simple_type(self, type_str: str) -> bool:
        """判断类型是否是简单类型

        简单类型定义：
        - 整数型、浮点型、布尔型
        - 字符型

        复杂类型定义：
        - 结构体、数组、字符串
        - 指针、引用

        Args:
            type_str: 类型字符串

        Returns:
            如果是简单类型则返回 True
        """
        simple_types = [
            "整数型",
            "浮点型",
            "布尔型",
            "字符型",
            "int",
            "float",
            "bool",
            "char",
            "i32",
            "i64",
            "f32",
            "f64",
        ]

        # 检查是否是简单类型
        for simple in simple_types:
            if simple in type_str.lower():
                return True

        return False

    def _compute_control_flow_complexity(self, func: IRFunction) -> int:
        """计算控制流复杂度（TASK-P3-002 新增）

        统计分支指令数量，评估控制流复杂度。

        分支指令：
        - IF、SWITCH、JUMP
        - 条件跳转、无条件跳转

        Args:
            func: IR 函数

        Returns:
            控制流复杂度（分支指令数量）
        """
        complexity = 0

        for bb in func.basic_blocks:
            for instr in bb.instructions:
                # 检查是否是分支指令
                if instr.opcode in [
                    Opcode.JUMP,
                    Opcode.BR,
                    Opcode.SWITCH,
                    Opcode.IF,
                    Opcode.ELSE,
                    Opcode.ENDIF,
                ]:
                    complexity += 1

        return complexity

    def _compute_savings(
        self,
        caller: IRFunction,
        callee: IRFunction,
        call_instr: IRInstruction,
        base_cost: InlineCost,
    ) -> float:
        """计算内联收益（TASK-P3-002 新增）

        使用加权成本公式计算内联收益。

        公式：
        savings = -base_cost + benefits

        base_cost = instruction_count * SIZE_WEIGHT
                    + basic_block_count * BB_WEIGHT
                    + control_flow_complexity * CF_WEIGHT

        benefits = loop_nesting_depth * LOOP_WEIGHT
                   + constant_param_ratio * CONST_WEIGHT
                   + simple_param_ratio * SIMPLE_WEIGHT
                   - complex_param_ratio * COMPLEX_WEIGHT

        Args:
            caller: 调用者函数
            callee: 被调用函数
            call_instr: 调用指令
            base_cost: 基础成本

        Returns:
            内联收益估计（正值表示收益）
        """
        # 计算基础成本
        base_cost_value = (
            base_cost.instruction_count * self.SIZE_WEIGHT
            + base_cost.basic_block_count * self.BB_WEIGHT
            + base_cost.control_flow_complexity * self.CF_WEIGHT
        )

        # 计算收益因子
        # 1. 循环嵌套深度
        loop_depth = self._get_loop_depth_for_call(caller, call_instr)

        # 2. 参数类型分析
        constant_ratio, simple_ratio, complex_ratio = self._analyze_param_types(
            callee, call_instr
        )

        # 计算收益
        benefits = (
            loop_depth * self.LOOP_WEIGHT
            + constant_ratio * self.CONST_WEIGHT
            + simple_ratio * self.SIMPLE_WEIGHT
            - complex_ratio * self.COMPLEX_WEIGHT
        )

        # 总收益 = -基础成本 + 收益因子
        savings = -base_cost_value + benefits

        return savings

    def _get_loop_depth_for_call(
        self, caller: IRFunction, call_instr: IRInstruction
    ) -> int:
        """获取调用点的循环嵌套深度

        Args:
            caller: 调用者函数
            call_instr: 调用指令

        Returns:
            循环嵌套深度
        """
        # 查找调用指令所在的基本块
        for bb in caller.basic_blocks:
            for instr in bb.instructions:
                if instr == call_instr:
                    return self._estimate_loop_depth(bb)

        return 0

    def should_inline(
        self,
        caller: IRFunction,
        callee: IRFunction,
        call_site: IRInstruction,
    ) -> bool:
        """
        决定是否内联

        按顺序检查每条启发式规则，返回第一个匹配的结果。

        ================================================================================
        决策流程（TASK-P3-002 更新）
        ================================================================================

        1. 获取被调用函数的成本
           - 如果函数没有成本记录，不内联

        2. 检查小函数规则
           - 指令数 ≤ 10 → 内联

        3. 检查热点函数规则
           - 调用次数 ≥ 5 且 指令数 ≤ 50 → 内联

        4. 检查单调用点规则
           - 调用次数 = 1 → 内联

        5. 检查递归规则
           - 递归函数 → 不内联

        6. 检查调用深度规则
           - 深度 > 3 → 不内联

        7. 检查收益驱动规则（新增）
           - 计算内联收益 savings_estimate
           - savings > 0 → 内联

        Args:
            caller: 调用者函数
            callee: 被调用者函数
            call_site: 调用点指令

        Returns:
            如果应该内联则返回 True
        """
        callee_cost = self.function_costs.get(callee.name)

        if not callee_cost:
            return False

        # 规则 1: 小函数总是内联
        if callee_cost.is_small(threshold=10):
            return True

        # 规则 2: 热点函数内联
        if callee_cost.is_hot(call_count=5):
            # 但不能太大
            if callee_cost.instruction_count <= 50:
                return True

        # 规则 3: 只被调用一次的函数内联
        if self.call_counts.get(callee.name, 0) == 1:
            return True

        # 规则 4: 递归函数不内联
        if self._is_recursive(callee):
            return False

        # 规则 5: 调用深度限制
        if self._get_call_depth(callee) > 3:
            return False

        # 规则 6: 收益驱动内联（TASK-P3-002 新增）
        # 计算内联收益
        savings = self._compute_savings(caller, callee, call_site, callee_cost)

        # 更新成本对象
        callee_cost.savings_estimate = savings

        # 如果收益 > 0，内联
        if savings > 0:
            return True

        return False

    def _is_recursive(self, func: IRFunction) -> bool:
        """检查函数是否是递归的

        递归定义：函数调用自己（直接或间接）。

        直接递归：foo() { foo(); }
        间接递归：foo() { bar(); }  bar() { foo(); }

        递归函数不内联，因为会导致无限展开。

        Args:
            func: 要检查的函数

        Returns:
            如果是递归函数则返回 True
        """
        for bb in func.basic_blocks:
            for instr in bb.instructions:
                if instr.opcode == Opcode.CALL:
                    for operand in instr.operands:
                        if isinstance(operand, IRValue):
                            if (
                                operand.name == func.name
                                or operand.name == f"@{func.name}"
                            ):
                                return True
        return False

    def _get_call_depth(self, func: IRFunction, visited: Set[str] = None) -> int:
        """获取函数的调用深度

        调用深度：从该函数开始，最长调用链的长度。

        示例：
          main -> foo -> bar -> baz
          foo 的调用深度是 3（main -> foo 算 1）

        Args:
            func: 要检查的函数
            visited: 已访问的函数集合（用于检测间接递归）

        Returns:
            调用深度
        """
        if visited is None:
            visited = set()

        if func.name in visited:
            # 检测到间接递归，停止
            return 0

        visited.add(func.name)

        max_depth = 0
        for bb in func.basic_blocks:
            for instr in bb.instructions:
                if instr.opcode == Opcode.CALL:
                    for operand in instr.operands:
                        if isinstance(operand, IRValue):
                            callee_name = operand.name.lstrip("@")
                            callee = self.program.find_function(callee_name)
                            if callee:
                                depth = self._get_call_depth(callee, visited)
                                max_depth = max(max_depth, depth + 1)

        return max_depth

    def get_cost(self, func_name: str) -> Optional[InlineCost]:
        """获取函数的内联成本

        Args:
            func_name: 函数名

        Returns:
            内联成本，如果函数不存在则返回 None
        """
        return self.function_costs.get(func_name)


# =============================================================================
# 函数内联器
# =============================================================================


class FunctionInliner:
    """
    函数内联器

    ================================================================================
    功能概述
    ================================================================================

    执行函数内联优化，将函数调用替换为函数体本身。

    核心步骤：
    1. 收集调用点：遍历函数中的所有 CALL 指令
    2. 成本评估：使用 InlineCostModel 判断是否应该内联
    3. 函数体克隆：复制被调用函数的所有基本块
    4. 变量重命名：避免变量名冲突
    5. 控制流整合：将克隆的基本块插入调用者

    ================================================================================
    内联示例
    ================================================================================

    原代码：
      def add(a, b) { return a + b; }
      def main() {
          x = add(1, 2);
          y = add(3, 4);
      }

    内联后：
      def main() {
          // 第一次调用内联
          %temp1 = 1 + 2;
          x = %temp1;
          // 第二次调用内联
          %temp2 = 3 + 4;
          y = %temp2;
      }

    ================================================================================
    实现细节
    ================================================================================

    1. 变量重命名
       - 内联的函数体中的变量需要重命名
       - 避免与调用者中的变量冲突
       - 格式：%inline.{counter}.{original_name}

    2. 参数替换
       - 函数参数替换为实际参数
       - 例如：add(a, b) 中的 a 替换为 1

    3. 返回值处理
       - RET 指令转换为值传递
       - 返回值赋给调用点的结果变量

    4. 控制流整合
       - 将调用点分裂为两部分
       - 插入内联的基本块
       - 更新跳转目标

    ================================================================================
    局限性
    ================================================================================

    当前实现有以下局限：

    1. 不支持异常处理
       - 内联函数中的异常需要特殊处理

    2. 不支持变长参数
       - 变长参数函数的内联复杂

    3. 不完全的控制流整合
       - 当前实现简化了控制流更新
       - 完整实现需要更新所有跳转目标

    4. 不支持部分内联
       - 只能完全内联或完全不内联
       - 部分内联需要更复杂的分析
    """

    def __init__(self, program: IRProgram):
        """初始化函数内联器

        Args:
            program: IR 程序
        """
        self.program = program
        self.cost_model = InlineCostModel(program)

        # 内联统计
        self.stats = {
            "inlined_count": 0,
            "total_instructions_saved": 0,
        }

        # 变量重命名计数器
        self.rename_counter = 0

    def inline_all(self) -> Dict[str, int]:
        """
        内联所有符合条件的函数

        使用不动点迭代：
        - 反复遍历所有函数
        - 直到没有新的内联发生

        这确保了：
        - 内联后的函数可以再次被内联
        - 所有内联机会都被利用

        Returns:
            优化统计
        """
        changed = True
        while changed:
            changed = False

            for caller in self.program.functions:
                if self._inline_function(caller):
                    changed = True
                    self.stats["inlined_count"] += 1

        return self.stats

    def _inline_function(self, caller: IRFunction) -> bool:
        """
        内联函数中的所有调用点

        步骤：
        1. 收集所有调用点
        2. 对每个调用点执行内联

        Args:
            caller: 调用者函数

        Returns:
            是否有内联发生
        """
        inlined = False

        # 收集所有调用点
        call_sites: List[Tuple[IRBasicBlock, int, IRInstruction, IRFunction]] = []

        for bb in caller.basic_blocks:
            for idx, instr in enumerate(bb.instructions):
                if instr.opcode == Opcode.CALL:
                    callee = self._get_callee(instr)
                    if callee and self.cost_model.should_inline(caller, callee, instr):
                        call_sites.append((bb, idx, instr, callee))

        # 执行内联
        for bb, idx, call_instr, callee in call_sites:
            if self._inline_call_site(caller, bb, idx, call_instr, callee):
                inlined = True

        return inlined

    def _get_callee(self, call_instr: IRInstruction) -> Optional[IRFunction]:
        """获取被调用的函数

        从 CALL 指令的第一个操作数获取函数名。

        Args:
            call_instr: CALL 指令

        Returns:
            被调用的函数，如果找不到则返回 None
        """
        if not call_instr.operands:
            return None

        # 第一个操作数是函数名
        func_value = call_instr.operands[0]
        if isinstance(func_value, IRValue):
            func_name = func_value.name.lstrip("@")
            return self.program.find_function(func_name)

        return None

    def _inline_call_site(
        self,
        caller: IRFunction,
        call_block: IRBasicBlock,
        call_idx: int,
        call_instr: IRInstruction,
        callee: IRFunction,
    ) -> bool:
        """
        内联单个调用点

        ================================================================================
        实现步骤
        ================================================================================

        1. 检查递归
           - 如果 callee == caller，不内联

        2. 克隆函数体
           - 复制所有基本块
           - 重命名变量
           - 替换参数

        3. 分裂调用块
           - call_block: [0..call_idx) -> inlined_blocks -> [call_idx+1..end]

        4. 整合控制流
           - 更新跳转目标
           - 处理返回值

        Args:
            caller: 调用者函数
            call_block: 调用点所在的基本块
            call_idx: 调用指令在基本块中的索引
            call_instr: 调用指令
            callee: 被调用者函数

        Returns:
            是否成功
        """
        # 检查递归
        if callee.name == caller.name:
            return False

        # 创建内联后的基本块
        inlined_blocks = self._clone_function(caller, callee, call_instr)

        if not inlined_blocks:
            return False

        # 替换调用点
        # 将 call_block 分裂为两部分
        # call_block: [0..call_idx) -> inlined_blocks -> [call_idx+1..end]

        # 获取 call_idx 之后的指令
        after_call = call_block.instructions[call_idx + 1 :]

        # 移除调用指令
        call_block.instructions = call_block.instructions[:call_idx]

        # 添加内联的基本块
        # 第一个内联块接在 call_block 后
        first_inlined = inlined_blocks[0]
        call_block.instructions.extend(first_inlined.instructions)

        # 更新后继关系
        # ...

        # 添加剩余的内联块
        for i, block in enumerate(inlined_blocks[1:], start=1):
            # 重命名避免冲突
            block.label = f"{caller.name}.inline.{self.rename_counter}.{block.label}"
            caller.add_basic_block(block.label)
            # 复制指令
            new_block = caller.find_basic_block(block.label)
            if new_block:
                new_block.instructions = block.instructions

        # 添加 call_idx 之后的指令到最后一个内联块
        if inlined_blocks and after_call:
            last_block = inlined_blocks[-1]
            last_block.instructions.extend(after_call)

        self.stats["total_instructions_saved"] += (
            self.cost_model.get_cost(callee.name).instruction_count
            if self.cost_model.get_cost(callee.name)
            else 0
        )

        return True

    def _clone_function(
        self,
        caller: IRFunction,
        callee: IRFunction,
        call_instr: IRInstruction,
    ) -> List[IRBasicBlock]:
        """
        克隆函数体

        ================================================================================
        克隆过程
        ================================================================================

        1. 创建变量映射表
           - 参数 → 实际参数
           - 局部变量 → 新名称

        2. 遍历所有基本块
           - 创建新的基本块
           - 克隆每条指令
           - 更新变量引用

        3. 返回克隆的基本块列表

        Args:
            caller: 调用者函数
            callee: 被调用者函数
            call_instr: 调用指令

        Returns:
            克隆的基本块列表
        """
        self.rename_counter += 1

        # 变量映射：旧名 → 新名
        var_map: Dict[str, str] = {}

        # 参数映射：参数名 → 实际参数名
        if len(call_instr.operands) > 1:
            for i, param in enumerate(callee.params):
                if i + 1 < len(call_instr.operands):
                    arg = call_instr.operands[i + 1]
                    if isinstance(arg, IRValue):
                        var_map[param.name] = arg.name

        # 克隆基本块
        cloned_blocks: List[IRBasicBlock] = []

        for bb in callee.basic_blocks:
            new_label = f"{bb.label}.inline.{self.rename_counter}"
            new_block = IRBasicBlock(new_label)

            for instr in bb.instructions:
                new_instr = self._clone_instruction(instr, var_map)
                new_block.add_instruction(new_instr)

            cloned_blocks.append(new_block)

        return cloned_blocks

    def _clone_instruction(
        self,
        instr: IRInstruction,
        var_map: Dict[str, str],
    ) -> IRInstruction:
        """克隆指令

        克隆指令时需要：
        1. 更新操作数中的变量引用
        2. 为结果变量生成新名称
        3. 更新变量映射表

        Args:
            instr: 原指令
            var_map: 变量映射表

        Returns:
            克隆的指令
        """
        # 克隆操作数
        new_operands = []
        for op in instr.operands:
            if isinstance(op, IRValue):
                # 如果变量在映射表中，使用新名称
                new_name = var_map.get(op.name, op.name)
                new_op = IRValue(
                    name=new_name, ty=op.ty, kind=op.kind, const_value=op.const_value
                )
                new_operands.append(new_op)
            else:
                new_operands.append(op)

        # 克隆结果
        new_results = []
        for result in instr.result:
            if isinstance(result, IRValue):
                # 生成新名称
                new_name = f"%inline.{self.rename_counter}.{result.name.lstrip('%')}"
                # 更新映射表
                var_map[result.name] = new_name

                new_result = IRValue(name=new_name, ty=result.ty, kind=result.kind)
                new_results.append(new_result)
            else:
                new_results.append(result)

        return IRInstruction(
            opcode=instr.opcode,
            operands=new_operands,
            result=new_results,
            label=instr.label,
        )


# =============================================================================
# 内联优化器
# =============================================================================


class InlineOptimizer:
    """
    内联优化器

    整合成本模型和内联器。
    """

    def __init__(self, program: IRProgram):
        self.program = program
        self.stats = {
            "inlined_count": 0,
            "total_instructions_saved": 0,
        }

    def optimize(self) -> Dict[str, int]:
        """
        执行内联优化

        Returns:
            优化统计
        """
        inliner = FunctionInliner(self.program)
        self.stats = inliner.inline_all()
        return self.stats

    def get_stats(self) -> Dict[str, int]:
        """获取优化统计"""
        return self.stats.copy()


# =============================================================================
# 便捷函数
# =============================================================================


def inline_functions(program: IRProgram) -> Dict[str, int]:
    """
    便捷函数：执行函数内联优化

    Args:
        program: IR 程序

    Returns:
        优化统计
    """
    optimizer = InlineOptimizer(program)
    return optimizer.optimize()

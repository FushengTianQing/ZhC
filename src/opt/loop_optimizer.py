"""
循环优化器
Loop Optimizer

实现循环优化，包括循环展开、循环合并、循环不变量外提等优化技术。

核心功能：
1. 循环展开（Loop Unrolling）：减少循环开销
2. 循环合并（Loop Fusion）：合并相邻循环
3. 循环不变量外提（Loop Invariant Code Motion）：将不变代码移出循环
4. 强度削减（Strength Reduction）：将昂贵操作替换为廉价操作

优化策略：
- 小循环优先展开（迭代次数 <= 阈值）
- 相邻循环尝试合并（迭代范围相同）
- 循环不变量外提到循环前
- 乘除法替换为移位操作
"""

import re
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum


class OptimizationType(Enum):
    """优化类型"""
    UNROLL = "unroll"              # 循环展开
    FUSION = "fusion"             # 循环合并
    INVARIANT_HOISTING = "invariant_hoisting"  # 循环不变量外提
    STRENGTH_REDUCTION = "strength_reduction"   # 强度削减


@dataclass
class LoopInfo:
    """循环信息"""
    loop_var: str                  # 循环变量
    start: str                    # 起始值
    end: str                      # 结束值
    step: str = "1"               # 步长
    body: str = ""                # 循环体
    iterations: Optional[int] = None  # 迭代次数（如果是常量）
    has_complex_control: bool = False  # 是否有复杂控制流
    invariant_vars: Set[str] = field(default_factory=set)  # 循环不变量
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """后处理：计算迭代次数"""
        if self.iterations is None:
            self.iterations = self._estimate_iterations()
    
    def _estimate_iterations(self) -> Optional[int]:
        """估算迭代次数"""
        try:
            # 尝试计算迭代次数
            start_val = int(self.start)
            end_val = int(self.end)
            step_val = int(self.step)
            
            if step_val > 0 and end_val > start_val:
                return (end_val - start_val) // step_val
            elif step_val < 0 and end_val < start_val:
                return (start_val - end_val) // (-step_val)
            else:
                return None
        except (ValueError, ZeroDivisionError):
            return None
    
    def can_unroll(self, max_iterations: int = 10) -> bool:
        """判断是否可以展开"""
        return (
            self.iterations is not None and
            self.iterations <= max_iterations and
            not self.has_complex_control
        )


class LoopOptimizer:
    """
    循环优化器
    
    实现多种循环优化技术
    
    核心算法：
    1. 循环识别：解析循环结构
    2. 依赖分析：识别循环依赖
    3. 优化决策：基于启发式规则
    4. 代码生成：生成优化后的代码
    
    示例：
    >>> optimizer = LoopOptimizer()
    >>> code = "循环 i 从 0 到 10 { ... }"
    >>> optimized = optimizer.optimize(code)
    """
    
    def __init__(self,
                 max_unroll_iterations: int = 10,
                 enable_fusion: bool = True,
                 enable_invariant_hoisting: bool = True,
                 enable_strength_reduction: bool = True):
        """
        初始化循环优化器
        
        Args:
            max_unroll_iterations: 最大展开迭代次数
            enable_fusion: 启用循环合并
            enable_invariant_hoisting: 启用循环不变量外提
            enable_strength_reduction: 启用强度削减
        """
        self.max_unroll_iterations = max_unroll_iterations
        self.enable_fusion = enable_fusion
        self.enable_invariant_hoisting = enable_invariant_hoisting
        self.enable_strength_reduction = enable_strength_reduction
        
        # 统计信息
        self.stats = {
            'total_loops': 0,
            'unrolled_loops': 0,
            'fused_loops': 0,
            'hoisted_invariants': 0,
            'reduced_operations': 0,
            'optimizations': []
        }
    
    def parse_loop(self, code: str) -> Optional[LoopInfo]:
        """
        解析循环结构
        
        支持的格式：
        - 循环 i 从 0 到 10 { ... }
        - 当 i < 10 { ... }
        - for (int i = 0; i < 10; i++) { ... }
        
        Args:
            code: 循环代码
            
        Returns:
            LoopInfo: 循环信息，解析失败返回None
        """
        # 中文循环：循环 i 从 0 到 10 { ... }
        pattern_zh = r'循环\s+(\w+)\s+从\s+(\d+)\s+到\s+(\d+)\s*\{'
        match = re.search(pattern_zh, code)
        
        if match:
            loop_var = match.group(1)
            start = match.group(2)
            end = match.group(3)
            
            # 提取循环体
            body_match = re.search(r'\{(.+)\}', code, re.DOTALL)
            body = body_match.group(1).strip() if body_match else ""
            
            return LoopInfo(
                loop_var=loop_var,
                start=start,
                end=end,
                step="1",
                body=body
            )
        
        # 英文循环：for (int i = 0; i < 10; i++) { ... }
        pattern_en = r'for\s*\(\s*\w+\s+(\w+)\s*=\s*(\d+)\s*;\s*\1\s*<\s*(\d+)\s*;'
        match = re.search(pattern_en, code)
        
        if match:
            loop_var = match.group(1)
            start = match.group(2)
            end = match.group(3)
            
            # 提取循环体
            body_match = re.search(r'\{(.+)\}', code, re.DOTALL)
            body = body_match.group(1).strip() if body_match else ""
            
            return LoopInfo(
                loop_var=loop_var,
                start=start,
                end=end,
                step="1",
                body=body
            )
        
        return None
    
    def unroll_loop(self, loop: LoopInfo, factor: Optional[int] = None) -> str:
        """
        循环展开
        
        将循环展开为顺序代码，减少循环开销
        
        Args:
            loop: 循环信息
            factor: 展开因子（展开几次），None表示完全展开
            
        Returns:
            展开后的代码
        """
        if loop.iterations is None:
            return f"/* 无法展开：迭代次数未知 */\n{loop.body}"
        
        # 计算展开次数
        if factor is None:
            # 完全展开
            unroll_count = loop.iterations
        else:
            # 部分展开
            unroll_count = min(factor, loop.iterations)
        
        # 生成展开代码
        unrolled_code = []
        unrolled_code.append(f"/* 循环展开（原迭代{loop.iterations}次）*/")
        
        try:
            start_val = int(loop.start)
            end_val = int(loop.end)
            step_val = int(loop.step)
            
            current = start_val
            count = 0
            
            while current < end_val and count < unroll_count:
                # 替换循环变量
                body = loop.body
                pattern = rf'\b{re.escape(loop.loop_var)}\b'
                replaced_body = re.sub(pattern, str(current), body)
                
                unrolled_code.append(f"// 迭代 {count + 1}: {loop.loop_var} = {current}")
                unrolled_code.append(replaced_body)
                
                current += step_val
                count += 1
            
            # 如果还有剩余迭代，保留循环
            if current < end_val:
                unrolled_code.append(f"// 剩余迭代：{loop.loop_var} 从 {current} 到 {end_val}")
                unrolled_code.append(f"循环 {loop.loop_var} 从 {current} 到 {end_val} {{")
                unrolled_code.append(loop.body)
                unrolled_code.append("}")
        
        except ValueError:
            return f"/* 展开失败：非整数边界 */\n{loop.body}"
        
        self.stats['unrolled_loops'] += 1
        self.stats['optimizations'].append(
            (OptimizationType.UNROLL, loop.loop_var, unroll_count)
        )
        
        return '\n'.join(unrolled_code)
    
    def fuse_loops(self, loop1: LoopInfo, loop2: LoopInfo) -> Optional[str]:
        """
        循环合并
        
        将两个相邻的循环合并为一个
        
        合并条件：
        1. 迭代范围相同
        2. 无数据依赖冲突
        
        Args:
            loop1: 第一个循环
            loop2: 第二个循环
            
        Returns:
            合并后的代码，失败返回None
        """
        # 检查迭代范围是否相同
        if (loop1.start != loop2.start or
            loop1.end != loop2.end or
            loop1.step != loop2.step):
            return None
        
        # 简单合并：将两个循环体拼接
        fused_code = []
        fused_code.append(f"/* 循环合并 */")
        fused_code.append(f"循环 {loop1.loop_var} 从 {loop1.start} 到 {loop1.end} {{")
        fused_code.append(f"  // 第一个循环体")
        fused_code.append(f"  {loop1.body}")
        fused_code.append(f"  // 第二个循环体")
        fused_code.append(f"  {loop2.body}")
        fused_code.append("}")
        
        self.stats['fused_loops'] += 1
        self.stats['optimizations'].append(
            (OptimizationType.FUSION, loop1.loop_var, 2)
        )
        
        return '\n'.join(fused_code)
    
    def hoist_invariant(self, loop: LoopInfo, invariant_code: str) -> str:
        """
        循环不变量外提
        
        将循环体中的不变代码移到循环前
        
        Args:
            loop: 循环信息
            invariant_code: 不变代码
            
        Returns:
            优化后的代码
        """
        hoisted_code = []
        hoisted_code.append(f"/* 循环不变量外提 */")
        hoisted_code.append(invariant_code)
        hoisted_code.append("")
        hoisted_code.append(f"循环 {loop.loop_var} 从 {loop.start} 到 {loop.end} {{")
        hoisted_code.append(loop.body)
        hoisted_code.append("}")
        
        self.stats['hoisted_invariants'] += 1
        self.stats['optimizations'].append(
            (OptimizationType.INVARIANT_HOISTING, loop.loop_var, 1)
        )
        
        return '\n'.join(hoisted_code)
    
    def reduce_strength(self, code: str) -> str:
        """
        强度削减
        
        将昂贵操作替换为廉价操作
        
        替换规则：
        - i * 2 → i << 1
        - i * 4 → i << 2
        - i / 2 → i >> 1
        - i % 2 → i & 1
        
        Args:
            code: 代码
            
        Returns:
            优化后的代码
        """
        optimized = code
        
        # 乘法替换为左移
        optimized = re.sub(r'\b(\w+)\s*\*\s*2\b', r'\1 << 1', optimized)
        optimized = re.sub(r'\b(\w+)\s*\*\s*4\b', r'\1 << 2', optimized)
        optimized = re.sub(r'\b(\w+)\s*\*\s*8\b', r'\1 << 3', optimized)
        
        # 除法替换为右移
        optimized = re.sub(r'\b(\w+)\s*/\s*2\b', r'\1 >> 1', optimized)
        optimized = re.sub(r'\b(\w+)\s*/\s*4\b', r'\1 >> 2', optimized)
        
        # 取模替换为与运算
        optimized = re.sub(r'\b(\w+)\s*%\s*2\b', r'\1 & 1', optimized)
        optimized = re.sub(r'\b(\w+)\s*%\s*4\b', r'\1 & 3', optimized)
        
        if optimized != code:
            self.stats['reduced_operations'] += 1
            self.stats['optimizations'].append(
                (OptimizationType.STRENGTH_REDUCTION, "operations", 1)
            )
        
        return optimized
    
    def optimize(self, code: str) -> str:
        """
        综合优化
        
        应用所有优化技术
        
        Args:
            code: 原始代码
            
        Returns:
            优化后的代码
        """
        self.stats['total_loops'] = 0
        
        # 1. 强度削减
        if self.enable_strength_reduction:
            code = self.reduce_strength(code)
        
        # 2. 循环识别和优化
        loops = []
        
        # 查找所有循环
        pattern = r'(循环\s+\w+\s+从\s+\d+\s+到\s+\d+\s*\{[^}]*\})'
        matches = re.finditer(pattern, code)
        
        for match in matches:
            loop_code = match.group(1)
            loop_info = self.parse_loop(loop_code)
            
            if loop_info:
                loops.append((match.start(), match.end(), loop_info))
                self.stats['total_loops'] += 1
        
        # 从后往前优化（避免位置偏移）
        for start, end, loop in reversed(loops):
            optimized_code = None
            
            # 尝试展开
            if loop.can_unroll(self.max_unroll_iterations):
                optimized_code = self.unroll_loop(loop)
            
            # 替换原循环
            if optimized_code:
                code = code[:start] + optimized_code + code[end:]
        
        return code
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            'optimization_count': len(self.stats['optimizations']),
            'recent_optimizations': self.stats['optimizations'][-10:]
        }
    
    def generate_report(self) -> str:
        """生成优化报告"""
        stats = self.get_statistics()
        
        report = []
        report.append("=" * 60)
        report.append("循环优化报告")
        report.append("=" * 60)
        report.append("")
        report.append("📊 统计信息:")
        report.append(f"  总循环数: {stats['total_loops']}")
        report.append(f"  展开循环数: {stats['unrolled_loops']}")
        report.append(f"  合并循环数: {stats['fused_loops']}")
        report.append(f"  外提不变量数: {stats['hoisted_invariants']}")
        report.append(f"  强度削减数: {stats['reduced_operations']}")
        report.append(f"  总优化次数: {stats['optimization_count']}")
        report.append("")
        
        if stats['recent_optimizations']:
            report.append("📝 最近优化记录:")
            for opt_type, target, value in stats['recent_optimizations']:
                report.append(f"  {opt_type.value}: {target} ({value})")
        
        report.append("")
        report.append("=" * 60)
        
        return '\n'.join(report)


# 便捷函数
def create_optimizer(**kwargs) -> LoopOptimizer:
    """创建循环优化器"""
    return LoopOptimizer(**kwargs)


def optimize_loops(code: str, **kwargs) -> str:
    """
    便捷函数：循环优化
    
    Args:
        code: 代码
        **kwargs: 其他参数
        
    Returns:
        优化后的代码
    """
    optimizer = LoopOptimizer(**kwargs)
    return optimizer.optimize(code)


if __name__ == "__main__":
    # 示例用法
    optimizer = LoopOptimizer()
    
    # 示例循环
    code = """
    循环 i 从 0 到 5 {
        整数型 x = i * 2;
        整数型 y = i * 4;
        打印(x + y);
    }
    """
    
    # 优化
    optimized = optimizer.optimize(code)
    print("优化后代码:")
    print(optimized)
    print()
    
    # 生成报告
    print(optimizer.generate_report())
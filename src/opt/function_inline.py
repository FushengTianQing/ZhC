"""
函数内联优化器
Function Inlining Optimizer

实现函数内联优化，将函数调用替换为函数体，减少调用开销。

核心功能：
1. 内联决策：基于启发式规则判断是否内联
2. 函数体复制：正确处理参数替换和返回值
3. 递归检测：避免无限内联递归函数
4. 成本估算：基于函数大小和调用频率的优化决策

内联策略：
- 小函数优先（指令数 <= 阈值）
- 频繁调用的函数优先
- 避免内联递归函数
- 避免内联复杂控制流
"""

import re
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum


class InlineDecision(Enum):
    """内联决策"""
    INLINE = "inline"              # 内联
    NO_INLINE = "no_inline"        # 不内联
    FORCE_INLINE = "force_inline"  # 强制内联
    NEVER_INLINE = "never_inline"  # 永不内联


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str                      # 函数名
    params: List[str]              # 参数列表
    body: str                      # 函数体
    return_type: str               # 返回类型
    instruction_count: int = 0     # 指令数
    call_count: int = 0            # 调用次数
    is_recursive: bool = False     # 是否递归
    has_complex_control_flow: bool = False  # 是否有复杂控制流
    metadata: Dict = field(default_factory=dict)  # 元数据
    
    def __post_init__(self):
        """后处理：计算指令数"""
        if self.instruction_count == 0:
            self.instruction_count = self._estimate_instruction_count()
    
    def _estimate_instruction_count(self) -> int:
        """估算指令数"""
        # 简单估算：统计语句数量
        lines = [line.strip() for line in self.body.split('\n') if line.strip()]
        # 排除空行和注释
        code_lines = [line for line in lines if line and not line.startswith('//')]
        return len(code_lines)


@dataclass
class CallSite:
    """调用点信息"""
    caller: str           # 调用者函数名
    callee: str           # 被调用函数名
    arguments: List[str]  # 实参列表
    location: Tuple[int, int]  # 调用位置（行号，列号）
    context: str          # 调用上下文（调用点代码）
    metadata: Dict = field(default_factory=dict)


class FunctionInliner:
    """
    函数内联优化器
    
    实现函数内联优化，将函数调用替换为函数体
    
    核心算法：
    1. 收集函数信息：解析函数定义
    2. 分析调用关系：构建调用图
    3. 内联决策：基于启发式规则
    4. 执行内联：参数替换、函数体复制
    
    示例：
    >>> inliner = FunctionInliner()
    >>> inliner.register_function("add", ["a", "b"], "return a + b;", "int")
    >>> inlined = inliner.inline_call("add", ["x", "y"])
    >>> print(inlined)  # "x + y"
    """
    
    def __init__(self,
                 max_instruction_count: int = 20,
                 max_recursion_depth: int = 5,
                 inline_threshold: float = 1.5):
        """
        初始化内联器
        
        Args:
            max_instruction_count: 最大指令数阈值（超过则不内联）
            max_recursion_depth: 最大递归深度
            inline_threshold: 内联阈值（收益/成本比）
        """
        self.max_instruction_count = max_instruction_count
        self.max_recursion_depth = max_recursion_depth
        self.inline_threshold = inline_threshold
        
        # 函数注册表
        self.functions: Dict[str, FunctionInfo] = {}
        
        # 调用图
        self.call_graph: Dict[str, Set[str]] = {}
        
        # 内联历史
        self.inline_history: List[Tuple[str, str, InlineDecision]] = []
        
        # 统计信息
        self.stats = {
            'total_calls': 0,
            'inlined_calls': 0,
            'failed_inlines': 0,
            'recursive_skips': 0,
            'complex_control_skips': 0
        }
    
    def register_function(self,
                         name: str,
                         params: List[str],
                         body: str,
                         return_type: str,
                         metadata: Optional[Dict] = None) -> None:
        """
        注册函数
        
        Args:
            name: 函数名
            params: 参数列表
            body: 函数体
            return_type: 返回类型
            metadata: 元数据
        """
        func_info = FunctionInfo(
            name=name,
            params=params,
            body=body,
            return_type=return_type,
            metadata=metadata or {}
        )
        
        self.functions[name] = func_info
        
        # 分析函数特性
        self._analyze_function_characteristics(name)
    
    def _analyze_function_characteristics(self, name: str) -> None:
        """分析函数特性"""
        if name not in self.functions:
            return
        
        func = self.functions[name]
        
        # 检测递归
        func.is_recursive = self._detect_recursion(name)
        
        # 检测复杂控制流
        func.has_complex_control_flow = self._has_complex_control_flow(func.body)
        
        # 更新调用图
        self._update_call_graph(name, func.body)
    
    def _detect_recursion(self, name: str) -> bool:
        """检测递归函数"""
        if name not in self.functions:
            return False
        
        func = self.functions[name]
        
        # 简单检测：函数体中是否包含函数名
        # 注意：这只是启发式检测，可能有误报
        pattern = rf'\b{name}\s*\('
        return bool(re.search(pattern, func.body))
    
    def _has_complex_control_flow(self, body: str) -> bool:
        """检测复杂控制流"""
        # 检测多层嵌套循环
        loop_depth = 0
        max_depth = 0
        
        for line in body.split('\n'):
            line = line.strip()
            if re.match(r'\b(当|循环|for|while)\b', line):
                loop_depth += 1
                max_depth = max(max_depth, loop_depth)
            elif re.match(r'\b(循环结束|end|}|)', line):
                loop_depth = max(0, loop_depth - 1)
        
        # 嵌套层数 >= 3 认为是复杂控制流
        return max_depth >= 3
    
    def _update_call_graph(self, name: str, body: str) -> None:
        """更新调用图"""
        if name not in self.call_graph:
            self.call_graph[name] = set()
        
        # 提取函数调用
        # 简单模式：匹配函数调用
        pattern = r'\b([a-zA-Z_\u4e00-\u9fa5]+)\s*\([^)]*\)'
        matches = re.findall(pattern, body)
        
        for callee in matches:
            # 排除关键字
            if callee not in ['如果', '否则', '当', '循环', '返回', 'if', 'else', 'while', 'for', 'return']:
                self.call_graph[name].add(callee)
    
    def should_inline(self,
                     caller: str,
                     callee: str,
                     call_site: Optional[CallSite] = None) -> InlineDecision:
        """
        判断是否应该内联
        
        决策规则：
        1. 函数不存在：不内联
        2. 强制内联标记：内联
        3. 永不内联标记：不内联
        4. 递归函数：不内联（避免无限展开）
        5. 指令数过大：不内联
        6. 复杂控制流：不内联
        7. 收益/成本比大于阈值：内联
        
        Args:
            caller: 调用者函数名
            callee: 被调用函数名
            call_site: 调用点信息
            
        Returns:
            InlineDecision: 内联决策
        """
        # 函数不存在
        if callee not in self.functions:
            return InlineDecision.NEVER_INLINE
        
        func = self.functions[callee]
        
        # 强制内联标记
        if func.metadata.get('always_inline', False):
            return InlineDecision.FORCE_INLINE
        
        # 永不内联标记
        if func.metadata.get('no_inline', False):
            return InlineDecision.NEVER_INLINE
        
        # 递归函数（避免无限展开）
        if func.is_recursive:
            self.stats['recursive_skips'] += 1
            return InlineDecision.NO_INLINE
        
        # 指令数过大
        if func.instruction_count > self.max_instruction_count:
            return InlineDecision.NO_INLINE
        
        # 复杂控制流
        if func.has_complex_control_flow:
            self.stats['complex_control_skips'] += 1
            return InlineDecision.NO_INLINE
        
        # 计算收益/成本比
        # 收益 = 调用次数 * 调用开销
        # 成本 = 函数体大小
        call_overhead = 5  # 假设调用开销为5条指令
        benefit = func.call_count * call_overhead
        cost = func.instruction_count
        
        if cost == 0:
            return InlineDecision.INLINE
        
        # 小函数未被调用过也默认内联（内联成本几乎为零）
        if func.call_count == 0 and cost <= self.max_instruction_count:
            return InlineDecision.INLINE
        
        ratio = benefit / cost
        
        if ratio >= self.inline_threshold:
            return InlineDecision.INLINE
        
        return InlineDecision.NO_INLINE
    
    def inline_call(self,
                   callee: str,
                   arguments: List[str],
                   result_var: Optional[str] = None) -> Optional[str]:
        """
        内联函数调用
        
        Args:
            callee: 被调用函数名
            arguments: 实参列表
            result_var: 结果变量名（用于存储返回值）
            
        Returns:
            内联后的代码，失败返回None
        """
        if callee not in self.functions:
            return None
        
        func = self.functions[callee]
        
        # 参数检查
        if len(arguments) != len(func.params):
            return None
        
        # 参数替换映射
        param_map = dict(zip(func.params, arguments))
        
        # 函数体复制
        inlined_body = func.body
        
        # 参数替换
        for param, arg in param_map.items():
            # 使用正则表达式替换（单词边界）
            pattern = rf'\b{re.escape(param)}\b'
            inlined_body = re.sub(pattern, arg, inlined_body)
        
        # 处理返回值
        if result_var and func.return_type != '空型':
            # 替换 return 语句为赋值
            # return expr; -> result_var = expr;
            return_pattern = r'返回\s+(.+?);?'
            inlined_body = re.sub(return_pattern, f'{result_var} = \\1;', inlined_body)
        
        # 移除函数包装（如果有的话）
        # 简单处理：直接返回函数体
        return inlined_body.strip()
    
    def optimize_function(self, func_name: str, code: str) -> str:
        """
        优化函数：内联所有可内联的调用
        
        Args:
            func_name: 函数名
            code: 函数代码
            
        Returns:
            优化后的代码
        """
        # 找出所有函数调用
        pattern = r'([a-zA-Z_\u4e00-\u9fa5]+)\s*\(([^)]*)\)'
        matches = list(re.finditer(pattern, code))
        
        # 从后往前替换（避免位置偏移）
        for match in reversed(matches):
            callee = match.group(1)
            args_str = match.group(2)
            
            # 跳过关键字
            if callee in ['如果', '否则', '当', '循环', '返回', 'if', 'else', 'while', 'for', 'return']:
                continue
            
            # 解析参数
            arguments = [arg.strip() for arg in args_str.split(',') if arg.strip()]
            
            # 内联决策
            decision = self.should_inline(func_name, callee)
            
            if decision in [InlineDecision.INLINE, InlineDecision.FORCE_INLINE]:
                # 执行内联
                inlined = self.inline_call(callee, arguments)
                
                if inlined:
                    # 替换调用点
                    start, end = match.start(), match.end()
                    code = code[:start] + inlined + code[end:]
                    
                    # 更新统计
                    self.stats['inlined_calls'] += 1
                    self.inline_history.append((func_name, callee, decision))
        
        self.stats['total_calls'] += len(matches)
        
        return code
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            'registered_functions': len(self.functions),
            'inline_rate': (
                self.stats['inlined_calls'] / max(1, self.stats['total_calls'])
            ),
            'history': self.inline_history[-10:]  # 最近10条记录
        }
    
    def generate_report(self) -> str:
        """生成优化报告"""
        stats = self.get_statistics()
        
        report = []
        report.append("=" * 60)
        report.append("函数内联优化报告")
        report.append("=" * 60)
        report.append("")
        report.append("📊 统计信息:")
        report.append(f"  注册函数数: {stats['registered_functions']}")
        report.append(f"  总调用次数: {stats['total_calls']}")
        report.append(f"  内联成功数: {stats['inlined_calls']}")
        report.append(f"  内联失败数: {stats['failed_inlines']}")
        report.append(f"  递归跳过数: {stats['recursive_skips']}")
        report.append(f"  复杂控制跳过: {stats['complex_control_skips']}")
        report.append(f"  内联率: {stats['inline_rate']:.1%}")
        report.append("")
        
        if stats['history']:
            report.append("📝 最近内联记录:")
            for caller, callee, decision in stats['history']:
                report.append(f"  {caller} → {callee}: {decision.value}")
        
        report.append("")
        report.append("=" * 60)
        
        return '\n'.join(report)


# 便捷函数
def create_inliner(**kwargs) -> FunctionInliner:
    """创建内联器"""
    return FunctionInliner(**kwargs)


def inline_function(caller_code: str,
                    functions: Dict[str, Tuple[List[str], str, str]],
                    **kwargs) -> str:
    """
    便捷函数：内联优化
    
    Args:
        caller_code: 调用者代码
        functions: 函数字典 {name: (params, body, return_type)}
        **kwargs: 其他参数
        
    Returns:
        优化后的代码
    """
    inliner = FunctionInliner(**kwargs)
    
    # 注册函数
    for name, (params, body, return_type) in functions.items():
        inliner.register_function(name, params, body, return_type)
    
    # 优化代码
    return inliner.optimize_function('main', caller_code)


if __name__ == "__main__":
    # 示例用法
    inliner = FunctionInliner()
    
    # 注册简单函数
    inliner.register_function(
        name="add",
        params=["a", "b"],
        body="return a + b;",
        return_type="int"
    )
    
    inliner.register_function(
        name="square",
        params=["x"],
        body="return x * x;",
        return_type="int"
    )
    
    # 内联调用
    result = inliner.inline_call("add", ["10", "20"])
    print(f"内联结果: {result}")
    
    # 优化函数
    code = """
    整数型 result = add(10, 20);
    整数型 value = square(5);
    """
    
    optimized = inliner.optimize_function("main", code)
    print(f"优化后代码:\n{optimized}")
    
    # 生成报告
    print(inliner.generate_report())
# -*- coding: utf-8 -*-
"""
ZHC IR - 优化提示系统

本模块提供统一的优化提示接口，支持多个后端（C、LLVM）应用优化提示。

================================================================================
优化提示简介
================================================================================

优化提示是编译器用来指导优化的额外信息。不同的后端有不同的优化提示机制：

1. C 后端（GCC/Clang）
   - `inline` 关键字：建议内联
   - `__attribute__((always_inline))`：强制内联
   - `__attribute__((hot))`：热点函数，优化寄存器分配
   - `__attribute__((cold))`：冷点函数，优化代码布局
   - `__attribute__((noreturn))`：不返回函数

2. LLVM 后端
   - `alwaysinline` 属性：强制内联
   - `hot` 属性：热点函数
   - `cold` 属性：冷点函数
   - `noreturn` 属性：不返回函数
   - `optsize` 属性：优化代码大小
   - `minsize` 属性：最小化代码大小

================================================================================
优化提示类型
================================================================================

OptimizationHint 枚举定义了所有支持的优化提示：

- INLINE: 建议内联（小函数）
- ALWAYS_INLINE: 强制内联（单调用点函数）
- HOT: 热点函数（调用频率高）
- COLD: 冷点函数（调用频率低）
- NORETURN: 不返回函数
- OPTSIZE: 优化代码大小
- MINSIZE: 最小化代码大小

================================================================================
使用示例
================================================================================

```python
from zhc.ir.optimization_hints import OptimizationHintAnalyzer

# 分析 IR 程序
analyzer = OptimizationHintAnalyzer(program)
hints = analyzer.analyze()

# 获取某个函数的优化提示
func_hints = hints.get_function_hints("add_numbers")

# 应用到 C 后端
c_backend = CBackend()
c_backend.apply_hints(hints)

# 应用到 LLVM 后端
llvm_backend = LLVMBackend()
llvm_backend.apply_hints(hints)
```

作者：远
日期：2026-04-08
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum, auto

from .program import IRProgram, IRFunction
from .instructions import IRInstruction
from .opcodes import Opcode


# =============================================================================
# 优化提示类型
# =============================================================================

class OptimizationHint(Enum):
    """优化提示类型
    
    每种提示对应不同的优化策略：
    
    INLINE: 建议内联
        - 适用：小函数（指令数 ≤ 10）
        - C 后端：添加 `inline` 关键字
        - LLVM 后端：不添加属性（LLVM 会自动判断）
    
    ALWAYS_INLINE: 强制内联
        - 适用：单调用点函数
        - C 后端：添加 `__attribute__((always_inline))`
        - LLVM 后端：添加 `alwaysinline` 属性
    
    HOT: 热点函数
        - 适用：调用频率高的函数（≥ 5 次）
        - C 后端：添加 `__attribute__((hot))`
        - LLVM 后端：添加 `hot` 属性
    
    COLD: 冷点函数
        - 适用：调用频率低的函数（≤ 1 次）
        - C 后端：添加 `__attribute__((cold))`
        - LLVM 后端：添加 `cold` 属性
    
    NORETURN: 不返回函数
        - 适用：函数没有 RET 指令
        - C 后端：添加 `__attribute__((noreturn))`
        - LLVM 后端：添加 `noreturn` 属性
    
    OPTSIZE: 优化代码大小
        - 适用：大函数（指令数 > 100）
        - C 后端：添加 `__attribute__((optimize("Os")))`
        - LLVM 后端：添加 `optsize` 属性
    
    MINSIZE: 最小化代码大小
        - 适用：非常大的函数（指令数 > 200）
        - C 后端：添加 `__attribute__((optimize("Oz")))`
        - LLVM 后端：添加 `minsize` 属性
    """
    INLINE = auto()
    ALWAYS_INLINE = auto()
    HOT = auto()
    COLD = auto()
    NORETURN = auto()
    OPTSIZE = auto()
    MINSIZE = auto()


# =============================================================================
# 优化提示数据结构
# =============================================================================

@dataclass
class FunctionOptimizationHints:
    """函数优化提示
    
    存储一个函数的所有优化提示。
    
    Attributes:
        function_name: 函数名
        hints: 优化提示集合
        reason: 每个提示的原因（字典）
        confidence: 每个提示的置信度（0.0-1.0）
    
    示例：
        hints = FunctionOptimizationHints(
            function_name="add_numbers",
            hints={OptimizationHint.INLINE, OptimizationHint.HOT},
            reason={
                OptimizationHint.INLINE: "小函数（5 条指令）",
                OptimizationHint.HOT: "调用 10 次",
            },
            confidence={
                OptimizationHint.INLINE: 0.9,
                OptimizationHint.HOT: 0.8,
            }
        )
    """
    function_name: str
    hints: Set[OptimizationHint]
    reason: Dict[OptimizationHint, str]
    confidence: Dict[OptimizationHint, float]
    
    def has_hint(self, hint: OptimizationHint) -> bool:
        """检查是否有某个提示
        
        Args:
            hint: 优化提示
            
        Returns:
            如果有该提示则返回 True
        """
        return hint in self.hints
    
    def get_reason(self, hint: OptimizationHint) -> Optional[str]:
        """获取某个提示的原因
        
        Args:
            hint: 优化提示
            
        Returns:
            原因字符串，如果没有则返回 None
        """
        return self.reason.get(hint)
    
    def get_confidence(self, hint: OptimizationHint) -> float:
        """获取某个提示的置信度
        
        Args:
            hint: 优化提示
            
        Returns:
            置信度（0.0-1.0），如果没有则返回 0.0
        """
        return self.confidence.get(hint, 0.0)


@dataclass
class ProgramOptimizationHints:
    """程序优化提示
    
    存储整个程序的所有优化提示。
    
    Attributes:
        function_hints: 函数优化提示字典（函数名 → FunctionOptimizationHints）
    
    示例：
        program_hints = ProgramOptimizationHints(
            function_hints={
                "add_numbers": FunctionOptimizationHints(...),
                "main": FunctionOptimizationHints(...),
            }
        )
    """
    function_hints: Dict[str, FunctionOptimizationHints]
    
    def get_function_hints(self, func_name: str) -> Optional[FunctionOptimizationHints]:
        """获取某个函数的优化提示
        
        Args:
            func_name: 函数名
            
        Returns:
            函数优化提示，如果不存在则返回 None
        """
        return self.function_hints.get(func_name)
    
    def has_function_hints(self, func_name: str) -> bool:
        """检查某个函数是否有优化提示
        
        Args:
            func_name: 函数名
            
        Returns:
            如果有优化提示则返回 True
        """
        return func_name in self.function_hints


# =============================================================================
# 优化提示分析器
# =============================================================================

class OptimizationHintAnalyzer:
    """优化提示分析器
    
    分析 IR 程序，识别优化机会，生成优化提示。
    
    ================================================================================
    分析策略
    ================================================================================
    
    1. 小函数识别
       - 指令数 ≤ 10 → INLINE
       - 理由：调用开销可能大于函数体开销
    
    2. 单调用点函数识别
       - 调用次数 = 1 → ALWAYS_INLINE
       - 理由：没有代码膨胀问题
    
    3. 热点函数识别
       - 调用次数 ≥ 5 → HOT
       - 理由：频繁调用，优化寄存器分配
    
    4. 冷点函数识别
       - 调用次数 ≤ 1 且不是单调用点 → COLD
       - 理由：很少调用，优化代码布局
    
    5. 不返回函数识别
       - 没有 RET 指令 → NORETURN
       - 理由：函数不会返回
    
    6. 大函数识别
       - 指令数 > 100 → OPTSIZE
       - 指令数 > 200 → MINSIZE
       - 理由：优化代码大小
    
    ================================================================================
    使用示例
    ================================================================================
    
    ```python
    analyzer = OptimizationHintAnalyzer(program)
    hints = analyzer.analyze()
    
    # 查看某个函数的提示
    func_hints = hints.get_function_hints("add_numbers")
    if func_hints and func_hints.has_hint(OptimizationHint.INLINE):
        print(f"建议内联：{func_hints.get_reason(OptimizationHint.INLINE)}")
    ```
    """
    
    # 分析阈值
    SMALL_FUNCTION_THRESHOLD = 10      # 小函数阈值（指令数）
    HOT_FUNCTION_THRESHOLD = 5         # 热点函数阈值（调用次数）
    COLD_FUNCTION_THRESHOLD = 1        # 冷点函数阈值（调用次数）
    LARGE_FUNCTION_THRESHOLD = 100     # 大函数阈值（指令数）
    VERY_LARGE_FUNCTION_THRESHOLD = 200 # 超大函数阈值（指令数）
    
    def __init__(self, program: IRProgram):
        """初始化优化提示分析器
        
        Args:
            program: IR 程序
        """
        self.program = program
        
        # 函数调用计数
        self.call_counts: Dict[str, int] = {}
        self._count_calls()
    
    def _count_calls(self):
        """统计每个函数的调用次数
        
        遍历整个程序，统计每个函数被调用的次数。
        """
        # 初始化计数
        for func in self.program.functions:
            self.call_counts[func.name] = 0
        
        # 统计调用
        for func in self.program.functions:
            for bb in func.basic_blocks:
                for instr in bb.instructions:
                    if instr.opcode == Opcode.CALL:
                        callee_name = self._get_callee_name(instr)
                        if callee_name and callee_name in self.call_counts:
                            self.call_counts[callee_name] += 1
    
    def _get_callee_name(self, call_instr: IRInstruction) -> Optional[str]:
        """从 CALL 指令获取被调用函数名
        
        Args:
            call_instr: CALL 指令
            
        Returns:
            被调用函数名，如果找不到则返回 None
        """
        if not call_instr.operands:
            return None
        
        # 第一个操作数是函数名
        from .values import IRValue
        func_value = call_instr.operands[0]
        if isinstance(func_value, IRValue):
            return func_value.name.lstrip('@')
        return None
    
    def analyze(self) -> ProgramOptimizationHints:
        """分析程序，生成优化提示
        
        Returns:
            程序优化提示
        """
        function_hints: Dict[str, FunctionOptimizationHints] = {}
        
        for func in self.program.functions:
            hints = self._analyze_function(func)
            if hints.hints:  # 只存储有提示的函数
                function_hints[func.name] = hints
        
        return ProgramOptimizationHints(function_hints=function_hints)
    
    def _analyze_function(self, func: IRFunction) -> FunctionOptimizationHints:
        """分析单个函数
        
        Args:
            func: IR 函数
            
        Returns:
            函数优化提示
        """
        hints: Set[OptimizationHint] = set()
        reason: Dict[OptimizationHint, str] = {}
        confidence: Dict[OptimizationHint, float] = {}
        
        # 1. 计算指令数
        instruction_count = self._count_instructions(func)
        
        # 2. 小函数识别
        if instruction_count <= self.SMALL_FUNCTION_THRESHOLD:
            hints.add(OptimizationHint.INLINE)
            reason[OptimizationHint.INLINE] = f"小函数（{instruction_count} 条指令）"
            confidence[OptimizationHint.INLINE] = 0.9
        
        # 3. 单调用点函数识别
        call_count = self.call_counts.get(func.name, 0)
        if call_count == 1:
            hints.add(OptimizationHint.ALWAYS_INLINE)
            reason[OptimizationHint.ALWAYS_INLINE] = "单调用点函数"
            confidence[OptimizationHint.ALWAYS_INLINE] = 0.95
        
        # 4. 热点函数识别
        if call_count >= self.HOT_FUNCTION_THRESHOLD:
            hints.add(OptimizationHint.HOT)
            reason[OptimizationHint.HOT] = f"热点函数（调用 {call_count} 次）"
            confidence[OptimizationHint.HOT] = 0.8
        
        # 5. 冷点函数识别（排除单调用点）
        if call_count <= self.COLD_FUNCTION_THRESHOLD and call_count != 1:
            hints.add(OptimizationHint.COLD)
            reason[OptimizationHint.COLD] = f"冷点函数（调用 {call_count} 次）"
            confidence[OptimizationHint.COLD] = 0.7
        
        # 6. 不返回函数识别
        if not self._has_return(func):
            hints.add(OptimizationHint.NORETURN)
            reason[OptimizationHint.NORETURN] = "不返回函数"
            confidence[OptimizationHint.NORETURN] = 0.95
        
        # 7. 大函数识别
        if instruction_count > self.LARGE_FUNCTION_THRESHOLD:
            hints.add(OptimizationHint.OPTSIZE)
            reason[OptimizationHint.OPTSIZE] = f"大函数（{instruction_count} 条指令）"
            confidence[OptimizationHint.OPTSIZE] = 0.6
        
        if instruction_count > self.VERY_LARGE_FUNCTION_THRESHOLD:
            hints.add(OptimizationHint.MINSIZE)
            reason[OptimizationHint.MINSIZE] = f"超大函数（{instruction_count} 条指令）"
            confidence[OptimizationHint.MINSIZE] = 0.5
        
        return FunctionOptimizationHints(
            function_name=func.name,
            hints=hints,
            reason=reason,
            confidence=confidence
        )
    
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
    
    def _has_return(self, func: IRFunction) -> bool:
        """检查函数是否有返回指令
        
        Args:
            func: IR 函数
            
        Returns:
            如果有返回指令则返回 True
        """
        for bb in func.basic_blocks:
            for instr in bb.instructions:
                if instr.opcode == Opcode.RET:
                    return True
        return False


# =============================================================================
# 后端适配器
# =============================================================================

class CBackendHintAdapter:
    """C 后端优化提示适配器
    
    将优化提示转换为 C 代码的优化提示语法。
    
    ================================================================================
    C 优化提示语法
    ================================================================================
    
    GCC/Clang 支持以下优化提示：
    
    1. `inline` 关键字
       - 语法：`inline int add(int a, int b)`
       - 作用：建议编译器内联该函数
    
    2. `__attribute__((always_inline))`
       - 语法：`inline __attribute__((always_inline)) int add(int a, int b)`
       - 作用：强制编译器内联该函数
    
    3. `__attribute__((hot))`
       - 语法：`__attribute__((hot)) int add(int a, int b)`
       - 作用：标记为热点函数，优化寄存器分配
    
    4. `__attribute__((cold))`
       - 语法：`__attribute__((cold)) int add(int a, int b)`
       - 作用：标记为冷点函数，优化代码布局
    
    5. `__attribute__((noreturn))`
       - 语法：`__attribute__((noreturn)) void exit(int status)`
       - 作用：标记为不返回函数
    
    6. `__attribute__((optimize("Os")))`
       - 语法：`__attribute__((optimize("Os"))) int large_func()`
       - 作用：优化代码大小
    
    ================================================================================
    使用示例
    ================================================================================
    
    ```python
    adapter = CBackendHintAdapter()
    
    # 获取函数声明前缀
    prefix = adapter.get_function_prefix(func_hints)
    # 输出：'inline __attribute__((hot)) '
    
    # 生成完整函数声明
    declaration = adapter.generate_function_declaration(func_name, func_hints, return_type, params)
    # 输出：'inline __attribute__((hot)) int add(int a, int b)'
    ```
    """
    
    def get_function_prefix(self, hints: FunctionOptimizationHints) -> str:
        """获取函数声明前缀
        
        根据优化提示生成函数声明前缀。
        
        Args:
            hints: 函数优化提示
            
        Returns:
            函数声明前缀字符串
        """
        parts: List[str] = []
        attributes: List[str] = []
        
        # inline 关键字
        if hints.has_hint(OptimizationHint.INLINE):
            parts.append("inline")
        
        if hints.has_hint(OptimizationHint.ALWAYS_INLINE):
            parts.append("inline")
            attributes.append("always_inline")
        
        # 其他属性
        if hints.has_hint(OptimizationHint.HOT):
            attributes.append("hot")
        
        if hints.has_hint(OptimizationHint.COLD):
            attributes.append("cold")
        
        if hints.has_hint(OptimizationHint.NORETURN):
            attributes.append("noreturn")
        
        if hints.has_hint(OptimizationHint.OPTSIZE):
            attributes.append('optimize("Os")')
        
        if hints.has_hint(OptimizationHint.MINSIZE):
            attributes.append('optimize("Oz")')
        
        # 组合属性
        if attributes:
            attr_str = " ".join(attributes)
            parts.append(f"__attribute__(({attr_str}))")
        
        # 组合前缀
        if parts:
            return " ".join(parts) + " "
        
        return ""
    
    def generate_function_declaration(
        self,
        func_name: str,
        hints: FunctionOptimizationHints,
        return_type: str,
        params: str
    ) -> str:
        """生成完整函数声明
        
        Args:
            func_name: 函数名
            hints: 函数优化提示
            return_type: 返回类型
            params: 参数列表
            
        Returns:
            完整函数声明字符串
        """
        prefix = self.get_function_prefix(hints)
        return f"{prefix}{return_type} {func_name}({params})"


class LLVMBackendHintAdapter:
    """LLVM 后端优化提示适配器
    
    将优化提示转换为 LLVM IR 的函数属性。
    
    ================================================================================
    LLVM 函数属性
    ================================================================================
    
    LLVM 支持以下函数属性：
    
    1. `alwaysinline`
       - 语法：`define alwaysinline i32 @add(i32 %a, i32 %b)`
       - 作用：强制内联
    
    2. `hot`
       - 语法：`define hot i32 @add(i32 %a, i32 %b)`
       - 作用：热点函数
    
    3. `cold`
       - 语法：`define cold i32 @add(i32 %a, i32 %b)`
       - 作用：冷点函数
    
    4. `noreturn`
       - 语法：`define noreturn void @exit(i32 %status)`
       - 作用：不返回函数
    
    5. `optsize`
       - 语法：`define optsize i32 @large_func()`
       - 作用：优化代码大小
    
    6. `minsize`
       - 语法：`define minsize i32 @very_large_func()`
       - 作用：最小化代码大小
    
    ================================================================================
    使用示例
    ================================================================================
    
    ```python
    adapter = LLVMBackendHintAdapter()
    
    # 获取 LLVM 属性列表
    attrs = adapter.get_llvm_attributes(func_hints)
    # 输出：['alwaysinline', 'hot']
    
    # 应用到 LLVM 函数
    llvm_func.attributes.add('alwaysinline')
    llvm_func.attributes.add('hot')
    ```
    """
    
    # OptimizationHint → LLVM 属性名映射
    HINT_TO_LLVM_ATTR: Dict[OptimizationHint, str] = {
        OptimizationHint.ALWAYS_INLINE: "alwaysinline",
        OptimizationHint.HOT: "hot",
        OptimizationHint.COLD: "cold",
        OptimizationHint.NORETURN: "noreturn",
        OptimizationHint.OPTSIZE: "optsize",
        OptimizationHint.MINSIZE: "minsize",
    }
    
    def get_llvm_attributes(self, hints: FunctionOptimizationHints) -> List[str]:
        """获取 LLVM 属性列表
        
        Args:
            hints: 函数优化提示
            
        Returns:
            LLVM 属性名列表
        """
        attrs: List[str] = []
        
        for hint in hints.hints:
            if hint in self.HINT_TO_LLVM_ATTR:
                attrs.append(self.HINT_TO_LLVM_ATTR[hint])
        
        return attrs
    
    def apply_to_llvm_function(self, llvm_func, hints: FunctionOptimizationHints):
        """应用优化提示到 LLVM 函数
        
        Args:
            llvm_func: LLVM 函数对象（llvmlite.ir.Function）
            hints: 函数优化提示
        """
        attrs = self.get_llvm_attributes(hints)
        
        for attr in attrs:
            # llvmlite 的函数属性添加方式
            # 注意：llvmlite 使用不同的属性添加 API
            # 这里提供通用的接口，实际使用时需要根据 llvmlite 版本调整
            try:
                # 尝试使用 llvmlite 的属性 API
                if hasattr(llvm_func, 'attributes'):
                    llvm_func.attributes.add(attr)
            except Exception:
                # 如果失败，跳过（某些属性可能不被支持）
                pass


# =============================================================================
# 便捷函数
# =============================================================================

def analyze_optimization_hints(program: IRProgram) -> ProgramOptimizationHints:
    """便捷函数：分析优化提示
    
    Args:
        program: IR 程序
        
    Returns:
        程序优化提示
    """
    analyzer = OptimizationHintAnalyzer(program)
    return analyzer.analyze()


def get_c_function_prefix(hints: FunctionOptimizationHints) -> str:
    """便捷函数：获取 C 函数声明前缀
    
    Args:
        hints: 函数优化提示
        
    Returns:
        C 函数声明前缀
    """
    adapter = CBackendHintAdapter()
    return adapter.get_function_prefix(hints)


def get_llvm_attributes(hints: FunctionOptimizationHints) -> List[str]:
    """便捷函数：获取 LLVM 属性列表
    
    Args:
        hints: 函数优化提示
        
    Returns:
        LLVM 属性名列表
    """
    adapter = LLVMBackendHintAdapter()
    return adapter.get_llvm_attributes(hints)
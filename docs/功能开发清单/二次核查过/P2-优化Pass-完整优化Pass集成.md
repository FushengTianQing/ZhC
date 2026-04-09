# P2-优化Pass-完整优化Pass集成

## 基本信息

| 字段 | 值 |
|------|-----|
| **优先级** | P2 |
| **功能模块** | 优化 Pass |
| **功能名称** | 完整优化 Pass 集成 |
| **依赖项** | LLVM IR 生成完成 |
| **预计工时** | 3-4 周 |

---

## 1. 开发内容分析

### 1.1 目标概述

集成 LLVM 标准优化 Pass 管道，实现从高层 IR 到目标代码的高效优化流程。该功能将把 ZhC 编译器从"功能正确"提升到"性能优秀"的水平。

### 1.2 技术背景

#### LLVM Pass 管道架构
```
ZhC IR → LLVM IR → Pass Manager → 优化 Pass → 优化后 IR → 代码生成
```

#### Pass 类型分类
| 类型 | 作用 | 示例 |
|------|------|------|
| **Analysis Pass** | 分析代码特性 | DominatorTree, AliasAnalysis |
| **Transform Pass** | 转换/优化代码 | GVN, SCCP, DCE |
| **Utility Pass** | 辅助功能 | PrintModule, ViewCFG |

### 1.3 需求分析

#### 核心需求
1. **Pass 管理器集成**：使用 LLVM 17+ 的新 Pass Manager
2. **分层优化**：支持 O0/O1/O2/O3/Os 不同优化级别
3. **模块化设计**：可配置启用/禁用特定 Pass
4. **优化诊断**：输出优化统计和决策信息

#### 用户场景
```cpp
// 用户期望的用法
zhc -O3 input.zhc -o output.o

// 或通过 API
compiler.set_optimization_level(OptimizationLevel.O3)
compiler.add_pass(OptimizationPass.GVN)
compiler.run()
```

---

## 2. 实现方案

### 2.1 核心架构

```
┌─────────────────────────────────────────────────────────┐
│                   OptimizationPipeline                   │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ PassManager │  │  PassConfig │  │ PassBuilder │    │
│  │             │  │             │  │             │    │
│  │ - Analysis  │  │ - Standard  │  │ - NewPM     │    │
│  │ - Transform │  │ - Codegen   │  │ - Legacy    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
├─────────────────────────────────────────────────────────┤
│                     Optimization Levels                  │
│  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐    │
│  │  O0   │ │  O1   │ │  O2   │ │  O3   │ │  Os   │    │
│  │ 快速  │ │ 基础  │ │ 平衡  │ │ 最大  │ │ 大小  │    │
│  └───────┘ └───────┘ └───────┘ └───────┘ └───────┘    │
└─────────────────────────────────────────────────────────┘
```

### 2.2 文件结构

```
src/zhc/optimization/
├── __init__.py
├── pass_manager.py          # Pass 管理器
├── pass_config.py           # Pass 配置
├── pass_builder.py          # Pass 构建器
├── optimization_levels.py   # 优化级别定义
├── pass_registry.py         # Pass 注册表
└── optimization_observer.py # 优化观察器
```

### 2.3 核心接口设计

#### PassManager 类
```python
class PassManager:
    """LLVM Pass 管理器封装"""

    def __init__(self, module: ll.Module, level: OptimizationLevel):
        self.module = module
        self.level = level
        self.pm = self._build_pass_manager()

    def run(self) -> ll.Module:
        """运行优化管道"""
        self.pm.run(self.module)
        return self.module

    def _build_pass_manager(self) -> llvm.PassManager:
        """根据优化级别构建 Pass 管道"""
        ...

    def add_pass(self, pass_type: PassType) -> 'PassManager':
        """添加自定义 Pass"""
        ...

    def invalidate_analysis(self, analysis: AnalysisType):
        """使分析结果失效"""
        ...
```

#### OptimizationLevel 枚举
```python
from enum import Enum

class OptimizationLevel(Enum):
    O0 = 0  # 无优化 - 快速编译，保留调试信息
    O1 = 1  # 基本优化 - 快速编译，少量优化
    O2 = 2  # 标准优化 - 平衡编译速度和性能
    O3 = 3  # 激进优化 - 最大性能
    Os = 4  # 大小优化 - 优先代码大小
    Oz = 5  # 极致大小优化 - 最小代码
```

### 2.4 优化级别配置

#### O0 - 调试级别
```python
O0_PASSES = [
    # 仅保留必要的 passes，保证语义正确
    'no-op',           # 无操作 Pass
    'verify',          # 验证 IR 正确性
]
```

#### O1 - 快速优化
```python
O1_PASSES = [
    'inline',          # 简单内联
    'mem2reg',         # 内存到寄存器
    'early-cse',       # 早期 CSE
    'gvn',             # 全局值编号
    'dce',             # 死代码消除
]
```

#### O2 - 标准优化（推荐）
```python
O2_PASSES = [
    'inline',          # 内联
    'mem2reg',
    'loop-rotate',     # 循环展开基础
    'licm',            # 循环不变代码移动
    'loop-unswitch',   # 循环条件转换
    'indvars',         # 归纳变量简化
    'gvn',
    'sccp',            # 稀疏条件常量传播
    'dce',
    'adce',            # 主动 DCE
    'reassociate',     # 重结合
    'simplifycfg',     # 简化控制流
    '合并ret',         # 合并 return
]
```

#### O3 - 激进优化
```python
O3_PASSES = O2_PASSES + [
    'loop-unroll',     # 循环展开
    'loop-vectorize',  # 循环向量化
    'slp-vectorize',   # SLP 向量化
    'gvn-hoist',       # GVN 提升
    'aggressive-dce',  # 激进死代码消除
    'function-attrs',   # 函数属性推断
]
```

#### Os/Oz - 大小优化
```python
OS_PASSES = O2_PASSES + [
    'dwarf场所-生成',   # 调试信息优化
    '函数整合',        # 函数合并
    '常量合并',        # 常量合并
]
```

---

## 3. 详细实现计划

### 3.1 Phase 1: Pass 管理器基础 (3-4 天)

#### 任务 1.1: PassManager 核心实现
```python
# src/zhc/optimization/pass_manager.py
class PassManager:
    def __init__(self, module: ll.Module, level: OptimizationLevel):
        self.module = module
        self.level = level
        self.passes = []
        self._build_passes()

    def _build_passes(self):
        """根据优化级别构建 Pass 列表"""
        if self.level == OptimizationLevel.O0:
            self._build_o0_passes()
        elif self.level == OptimizationLevel.O1:
            self._build_o1_passes()
        # ...

    def run(self) -> ll.Module:
        """执行优化"""
        for pass_func in self.passes:
            pass_func(self.module)
        return self.module
```

#### 任务 1.2: 优化级别定义
```python
# src/zhc/optimization/optimization_levels.py
class OptimizationLevel(Enum):
    O0 = ("O0", 0, "无优化，保留调试信息")
    O1 = ("O1", 1, "基本优化，快速编译")
    O2 = ("O2", 2, "标准优化，平衡性能")
    O3 = ("O3", 3, "激进优化，最大性能")
    Os = ("Os", 4, "大小优化")
    Oz = ("Oz", 5, "极致大小优化")
```

#### 任务 1.3: Pass 注册表
```python
# src/zhc/optimization/pass_registry.py
class PassRegistry:
    """全局 Pass 注册表"""

    _passes: Dict[str, 'PassInfo'] = {}

    @classmethod
    def register(cls, name: str, pass_type: PassType,
                 transform: Callable, analysis: List[str] = None):
        """注册 Pass"""
        cls._passes[name] = PassInfo(
            name=name,
            pass_type=pass_type,
            transform=transform,
            required_analysis=analysis or []
        )

    @classmethod
    def get(cls, name: str) -> 'PassInfo':
        return cls._passes.get(name)
```

### 3.2 Phase 2: 标准优化 Pass 实现 (5-6 天)

#### 任务 2.1: 内联优化
```python
def inline_pass(module: ll.Module):
    """函数内联 Pass

    策略：
    1. 分析函数调用点
    2. 计算内联收益（大小、调用开销）
    3. 执行内联转换
    4. 更新调用图

    阈值配置：
    - 递归函数默认不内联
    - 阈值可配置（默认 255 字节）
    """
    cg = CallGraph.build(module)
    for call_site in cg.call_sites:
        callee = call_site.callee
        if should_inline(call_site, callee):
            inline_function(call_site)
```

#### 任务 2.2: 死代码消除 (DCE)
```python
def dce_pass(module: ll.Module):
    """死代码消除 Pass

    消除策略：
    1. 识别无副作用的指令
    2. 递归标记未使用的结果
    3. 删除死指令和基本块

    特殊情况处理：
    - 调试 intrinsic 函数
    - 副作用 intrinsics
    - volatile 操作
    """
    dead = find_dead_instructions(module)
    for inst in dead:
        inst.erase_from_parent()
```

#### 任务 2.3: 全局值编号 (GVN)
```python
def gvn_pass(module: ll.Module):
    """GVN - 全局值编号 Pass

    等价性检测：
    1. 构造值编号表
    2. 查找等价表达式
    3. 替换冗余计算
    4. 传播可用加载

    支持的表达式类型：
    - 算术运算
    - 逻辑运算
    - 比较运算
    - 内存加载
    """
    gvn = GVNAnalysis()
    for func in module.functions:
        gvn.process_function(func)
```

#### 任务 2.4: 循环优化
```python
def loop_optimize_pass(module: ll.Module):
    """循环优化套件

    包含的优化：
    1. 循环不变代码移动 (LICM)
    2. 归纳变量简化
    3. 循环展开
    4. 循环合并

    触发条件：
    - 循环至少有 1 次迭代
    - 循环体内的不变代码可安全移动
    """
    loop_info = LoopAnalysis(module)
    for loop in loop_info.loops:
        licm(loop)          # 不变代码移动
        simplify_indvars(loop)  # 归纳变量简化
```

### 3.3 Phase 3: 高级优化 (4-5 天)

#### 任务 3.1: 链接时优化 (LTO)
```python
def lto_pass(module_list: List[ll.Module]):
    """链接时优化

    能力：
    1. 跨模块内联
    2. 跨模块常量传播
    3. 死代码消除
    4. 符号重整

    模式：
    - Full LTO: 所有模块一起优化
    - Thin LTO: 独立优化 + 有限合并
    """
    if config.lto_mode == 'full':
        link_modules(module_list)
        optimize_combined()
    elif config.lto_mode == 'thin':
        thin_link_and_optimize(module_list)
```

#### 任务 3.2: 过程间优化 (IPO)
```python
def ipo_pass(module: ll.Module):
    """过程间分析优化

    分析范围：
    1. 全局变量访问分析
    2. 参数别名分析
    3. 函数副作用分析
    4. 常量传播分析

    优化机会：
    - 函数克隆
    - 参数提升
    - 死参数消除
    """
    ipa = InterProceduralAnalysis(module)
    for func in module.functions:
        if ipa.can_specialize(func):
            specialize_function(func, ipa.analysis)
```

### 3.4 Phase 4: 优化诊断与工具 (2-3 天)

#### 任务 4.1: 优化统计
```python
class OptimizationStats:
    """优化统计收集器"""

    def __init__(self):
        self.passes_run = []
        self.instructions_removed = 0
        self.instructions_added = 0
        self.functions_inlined = 0
        self.loops_unrolled = 0
        self.vectorized_loops = 0

    def report(self) -> str:
        """生成优化报告"""
        return f"""
=== Optimization Report ===
Passes Run: {len(self.passes_run)}
Instructions Removed: {self.instructions_removed}
Instructions Added: {self.instructions_added}
Functions Inlined: {self.functions_inlined}
Loops Unrolled: {self.loops_unrolled}
Vectorized Loops: {self.vectorized_loops}
"""
```

#### 任务 4.2: 优化通过日志
```python
def optimization_observer(pass_name: str, result: PassResult):
    """优化观察器回调"""
    if result.changed:
        log.info(f"[{pass_name}] Modified module:")
        for func in result.modified_functions:
            log.info(f"  - {func.name}: {result.changes[func]}")
```

---

## 4. API 设计

### 4.1 编译器 API 扩展
```python
# src/zhc/compiler.py
class Compiler:
    def set_optimization_level(self, level: OptimizationLevel):
        """设置优化级别"""
        self.optimization_level = level

    def add_optimization_pass(self, pass_name: str):
        """添加额外优化 Pass"""
        self.extra_passes.append(pass_name)

    def disable_optimization(self, pass_name: str):
        """禁用特定 Pass"""
        self.disabled_passes.add(pass_name)

    def get_optimization_stats(self) -> OptimizationStats:
        """获取优化统计"""
        return self.optimizer.stats
```

### 4.2 命令行接口
```bash
# 优化级别
zhc -O0 input.zhc      # 快速编译
zhc -O1 input.zhc      # 基础优化
zhc -O2 input.zhc      # 推荐优化
zhc -O3 input.zhc      # 最大优化
zhc -Os input.zhc      # 优化大小

# 调试优化
zhc -O3 -Rpass=loop-vectorize input.zhc  # 显示向量化决策

# Pass 列表
zhc -O3 -mllvm -debug-pass=Structure input.zhc
```

### 4.3 配置文件
```yaml
# zhc.yaml
optimization:
  level: O2
  passes:
    enable:
      - inline
      - gvn
      - loop-rotate
    disable:
      - loop-vectorize  # 禁用向量化
  thresholds:
    inline_threshold: 255
    unroll_count: 4
  diagnostics:
    print_passes: true
    print_stats: true
```

---

## 5. 测试计划

### 5.1 单元测试
```python
def test_pass_manager_basic():
    """测试 Pass 管理器基本功能"""
    code = """
    func int add(int a, int b) {
        return a + b;
    }
    """
    module = compile_to_llvm(code)
    pm = PassManager(module, OptimizationLevel.O2)
    optimized = pm.run()
    assert optimized is not None

def test_optimization_levels():
    """测试各优化级别"""
    for level in OptimizationLevel:
        pm = PassManager(module, level)
        result = pm.run()
        assert result.is_valid()

def test_inline_pass():
    """测试内联 Pass"""
    code = """
    func int helper(int x) { return x * 2; }
    func int main() {
        int a = helper(5);
        return a;
    }
    """
    # 验证 helper 被内联
    optimized = run_optimization(code, [InlinePass()])
    assert 'helper' not in optimized or is_inlined(optimized)
```

### 5.2 集成测试
```python
def test_optimization_pipeline():
    """测试完整优化管道"""
    test_cases = [
        'microbenchmarks/sieve.zhc',
        'microbenchmarks/matrix_multiply.zhc',
        'realworld/quicksort.zhc',
    ]

    for case in test_cases:
        result = compile_and_optimize(case, level=OptimizationLevel.O3)
        assert result.is_valid()
        assert result.execution_time < baseline * 0.5
```

### 5.3 性能基准测试
```python
def benchmark_optimization_levels():
    """对比各优化级别性能"""
    results = {}
    for level in [O1, O2, O3]:
        time = measure_execution(optimize(code, level))
        results[level] = time

    assert results[O3] < results[O1]  # O3 应该比 O1 快
```

---

## 6. 风险与挑战

### 6.1 技术风险
| 风险 | 影响 | 缓解策略 |
|------|------|----------|
| LLVM 版本兼容性 | 中 | 使用 llvmlite 版本检测 |
| 优化导致调试困难 | 高 | O0 保留完整调试信息 |
| 编译时间增加 | 中 | 支持增量优化 |

### 6.2 已知限制
1. **并行编译**：多线程 Pass 执行需要额外同步
2. **大型模块**：超大型模块优化可能内存不足
3. **特定平台**：某些 Pass 可能不支持某些目标

---

## 7. 验收标准

### 7.1 功能验收
- [ ] 所有优化级别 (O0-Oz) 正常工作
- [ ] Pass 可以单独启用/禁用
- [ ] 优化统计准确报告
- [ ] 命令行接口完整

### 7.2 性能验收
- [ ] O3 优化比 O1 快至少 20%
- [ ] 关键优化 Pass 正确执行
- [ ] 无性能回归

### 7.3 质量验收
- [ ] 优化后 IR 语义保持一致
- [ ] 生成的代码无运行时错误
- [ ] 测试覆盖率达到 80%+

---

## 8. 后续规划

本功能完成后，将进入以下阶段：
1. **P2-SIMD-SIMD指令生成** - 利用本功能的向量化基础
2. **P2-调试支持** - 需要 O0 级别配合调试信息生成

---

*文档创建时间: 2026-04-09*
*负责人: 编译器团队*
*版本: 1.0*

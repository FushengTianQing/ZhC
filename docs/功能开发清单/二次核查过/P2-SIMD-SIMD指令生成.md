# P2-SIMD-SIMD指令生成

## 基本信息

| 字段 | 值 |
|------|-----|
| **优先级** | P2 |
| **功能模块** | SIMD |
| **功能名称** | SIMD 指令生成 |
| **依赖项** | LLVM IR 生成、优化 Pass |
| **预计工时** | 4-5 周 |

---

## 1. 开发内容分析

### 1.1 目标概述

实现自动向量化功能，使编译器能够识别可并行的数据操作并生成高效的 SIMD（Single Instruction Multiple Data）指令，显著提升计算密集型程序的性能。

### 1.2 技术背景

#### SIMD 指令集
| 架构 | 指令集 | 向量宽度 | 典型操作 |
|------|--------|----------|----------|
| x86_64 | SSE4.2/AVX/AVX-512 | 128/256/512 位 | 整数/浮点向量运算 |
| AArch64 | NEON | 128 位 | 整数/浮点/定点向量运算 |
| ARM | NEON | 64/128 位 | 与 AArch64 类似 |
| RISC-V | RVV | 可变 128-2048 位 | 向量扩展 |
| WebAssembly | SIMD | 128 位 | WebAssembly SIMD128 |

#### 向量化流程
```
标量 IR → 循环分析 → 向量化计划 → 向量类型转换 → SIMD 指令生成
   ↓
[1,2,3,4] + [5,6,7,8] = [6,8,10,12]  // 一次操作处理多个数据
```

### 1.3 需求分析

#### 核心需求
1. **自动向量化**：识别可向量化的循环和数据模式
2. **多指令集支持**：支持 SSE/AVX/NEON/RVV/SIMD128
3. **向量化策略**：提供多种向量化策略选择
4. **性能优化**：最小化向量化的开销

#### 用户场景
```cpp
// 用户期望：编译器自动使用 SIMD
void vector_add(float* a, float* b, float* c, int n) {
    for (int i = 0; i < n; i++) {
        c[i] = a[i] + b[i];  // 自动向量化为 SIMD 加法
    }
}

// 使用 SIMD intrinsic（显式）
void vector_add_simd(float* a, float* b, float* c, int n) {
    for (int i = 0; i < n; i += 4) {
        __m128 va = _mm_loadu_ps(&a[i]);
        __m128 vb = _mm_loadu_ps(&b[i]);
        __m128 vc = _mm_add_ps(va, vb);
        _mm_storeu_ps(&c[i], vc);
    }
}
```

---

## 2. 实现方案

### 2.1 核心架构

```
┌─────────────────────────────────────────────────────────┐
│                    VectorizationPass                     │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ LoopAnalyzer │  │VectorBuilder │  │ISelGenerator │   │
│  │ (循环分析)    │  │ (向量化构建) │  │ (指令选择)    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ CostModel    │  │ WidthSelector│  │ MaskHandler  │   │
│  │ (成本模型)    │  │ (宽度选择)   │  │ (掩码处理)    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
├─────────────────────────────────────────────────────────┤
│                    Target Vector Units                   │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │
│  │ SSE/AVX│ │ NEON   │ │  RVV   │ │SIMD128 │           │
│  └────────┘ └────────┘ └────────┘ └────────┘           │
└─────────────────────────────────────────────────────────┘
```

### 2.2 文件结构

```
src/zhc/simd/
├── __init__.py
├── vectorization_pass.py     # 向量化 Pass
├── loop_analyzer.py          # 循环分析器
├── vector_builder.py          # 向量化 IR 构建
├── cost_model.py             # 成本模型
├── width_selector.py          # 向量宽度选择
├── mask_handler.py            # 掩码处理
├── simd_intrinsics.py         # SIMD intrinsic
├── instruction_selector.py    # SIMD 指令选择
├── targets/
│   ├── __init__.py
│   ├── x86_simd.py           # x86 SSE/AVX
│   ├── arm_neon.py            # ARM NEON
│   ├── riscv_rvv.py           # RISC-V RVV
│   └── wasm_simd.py           # WebAssembly SIMD
└── vector_types.py            # 向量类型定义
```

### 2.3 核心接口设计

#### VectorizationPass 类
```python
class VectorizationPass:
    """向量化优化 Pass"""

    def __init__(self, target: Target):
        self.target = target
        self.vector_width = self._get_max_vector_width(target)
        self.cost_model = CostModel(target)

    def run(self, module: ll.Module) -> bool:
        """运行向量化 Pass"""
        changed = False

        for func in module.functions:
            loop_info = LoopAnalyzer.analyze(func)
            for loop in loop_info.loops:
                if self._is_vectorizable(loop):
                    if self.cost_model.vectorization_benefit(loop) > 0:
                        self._vectorize_loop(loop)
                        changed = True

        return changed

    def _is_vectorizable(self, loop: Loop) -> bool:
        """检查循环是否可向量化"""
        return (
            self._has_simple_induction(loop) and
            self._has_uniform_addressing(loop) and
            not self._has_dependencies(loop) and
            self._has_legal_vectorizable_body(loop)
        )
```

#### CostModel 类
```python
class CostModel:
    """向量化成本模型"""

    def __init__(self, target: Target):
        self.target = target
        self.vector_unit_costs = self._load_costs(target)

    def vectorization_benefit(self, loop: Loop) -> float:
        """计算向量化收益"""
        scalar_cost = self._estimate_scalar_cost(loop)
        vector_cost = self._estimate_vector_cost(loop)

        # 收益 = 标量成本 / 向量成本
        benefit = scalar_cost / max(vector_cost, 1)

        # 应用因子
        benefit *= self._get_vectorization_factor(loop)

        return benefit
```

### 2.4 向量类型定义

```python
# src/zhc/simd/vector_types.py
@dataclass
class VectorType:
    """向量类型"""
    element_type: ll.Type              # 元素类型
    num_elements: int                  # 元素数量
    total_bits: int                    # 总位数

    @classmethod
    def float32x4(cls):
        return cls(ll.FloatType(), 4, 128)

    @classmethod
    def int32x4(cls):
        return cls(ll.IntType(32), 4, 128)
```

---

## 3. 详细实现计划

### 3.1 Phase 1: 循环分析 (4-5 天)

- 循环检测与分类
- 归纳变量识别
- 依赖分析
- 向量化可行性检查

### 3.2 Phase 2: 向量化 IR 构建 (5-6 天)

- 向量化类型转换
- 向量化加载/存储
- 向量化算术运算
- 掩码处理

### 3.3 Phase 3: SIMD 指令选择 (5-6 天)

- x86 SSE/AVX 指令选择
- ARM NEON 指令选择
- RISC-V RVV 指令选择
- WebAssembly SIMD 指令选择

### 3.4 Phase 4: 高级向量化策略 (3-4 天)

- 循环展开向量化
- 条件执行向量化
- SLP 向量化

### 3.5 Phase 5: Intrinsic 函数 (2-3 天)

- SIMD Intrinsic 定义
- Intrinsic 到指令映射

---

## 4. API 设计

### 4.1 命令行接口
```bash
# 启用向量化
zhc -O3 -fvectorize input.zhc -o output

# 显式设置向量宽度
zhc -O3 -vectorize -vector-width=4 input.zhc

# 调试向量化决策
zhc -O3 -Rpass=loop-vectorize input.zhc
```

### 4.2 配置文件
```yaml
simd:
  enabled: true
  vector_width: auto
  force_vectorize: false
  enable_masks: true
```

---

## 5. 测试计划

### 5.1 单元测试
- 循环分析测试
- 向量类型测试
- 指令选择测试

### 5.2 集成测试
- 向量化正确性测试
- 性能基准测试

---

## 6. 验收标准

- [ ] 基本的循环向量化工作正常
- [ ] 支持 x86 SSE/AVX、ARM NEON
- [ ] 向量化代码比标量代码快至少 2x
- [ ] 边界条件正确处理

---

*文档创建时间: 2026-04-09*
*负责人: 编译器团队*
*版本: 1.0*

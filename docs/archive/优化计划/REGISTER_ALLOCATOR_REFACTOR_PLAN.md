# 寄存器分配器重构方案

## ✅ 已完成（2026-04-08）

重构已成功执行，所有测试通过（37 passed）。

### 实施结果

| 阶段 | 任务 | 状态 |
|------|------|------|
| Phase 1 | 移动文件到正确位置 | ✅ 完成 |
| Phase 2 | 更新导入路径 | ✅ 完成 |
| Phase 3 | 更新测试 | ✅ 完成 |
| Phase 4 | 废弃 codegen 模块 | ✅ 完成 |
| Phase 5 | 文档更新 | ✅ 完成 |

### 新架构

```
src/
├── ir/                       # 中间表示层（IR 层优化）
│   ├── ssa.py               # SSA 构建
│   ├── dominator.py         # 支配树算法
│   ├── dataflow.py          # 数据流分析
│   ├── loop_optimizer.py    # 循环优化
│   ├── inline_optimizer.py  # 内联优化
│   └── register_allocator.py # 寄存器分配 ✅ 已迁移
│
├── backend/                  # 后端层（代码生成）
│   ├── __init__.py          # 后端模块初始化 ✅ 新建
│   └── allocator_interface.py # 后端适配接口 ✅ 已迁移
│
└── codegen/                  # 临时模块（已废弃）
    ├── __init__.py          # 废弃警告 + 重新导出 ✅ 已更新
    ├── register_allocator.py # 废弃包装器 ✅ 已更新
    └── allocator_interface.py # 废弃包装器 ✅ 已更新
```

---

## 背景

当前寄存器分配器位于 `src/codegen/` 模块，但根据 LLVM/WASM 后端集成计划，`codegen` 模块将被废弃，改用 `backend` 架构。需要将寄存器分配器迁移到合适的位置。

## 问题分析

### 当前架构问题

1. **模块定位不清**：寄存器分配是 IR 层优化，不应该属于代码生成层
2. **依赖关系混乱**：`codegen` 模块依赖 `zhc.parser`，导致循环导入
3. **迁移成本高**：废弃 `codegen` 时需要修改所有导入路径

### 理想架构

```
src/
├── ir/                       # 中间表示层（IR 层优化）
│   ├── ssa.py               # SSA 构建
│   ├── dominator.py         # 支配树算法
│   ├── dataflow.py          # 数据流分析
│   ├── loop_optimizer.py    # 循环优化
│   ├── inline_optimizer.py  # 内联优化
│   └── register_allocator.py # 寄存器分配 ← 移到这里
│
├── backend/                  # 后端层（代码生成）
│   ├── base.py              # 后端基类
│   ├── c_backend.py         # C 后端
│   ├── llvm_backend.py      # LLVM 后端
│   ├── wasm_backend.py      # WASM 后端
│   └── allocator_interface.py # 后端适配接口
│
└── codegen/                  # 临时模块（将被废弃）
    └── c_codegen.py         # 旧 C 代码生成器
```

## 重构步骤

### Phase 1: 移动寄存器分配器到 IR 层

```bash
# 移动文件
mv src/codegen/register_allocator.py src/ir/register_allocator.py
mv src/codegen/allocator_interface.py src/backend/allocator_interface.py

# 更新导入路径
# 所有 from zhc.codegen.register_allocator import ...
# 改为 from zhc.ir.register_allocator import ...
```

### Phase 2: 更新模块依赖

**src/ir/register_allocator.py**
- 无外部依赖，纯算法实现
- 只依赖标准库和 dataclasses

**src/backend/allocator_interface.py**
- 依赖 `zhc.ir.register_allocator`
- 提供后端适配层

### Phase 3: 更新测试

```bash
# 移动测试文件
mv tests/test_register_allocator.py tests/test_ir_register_allocator.py

# 更新导入路径
```

### Phase 4: 废弃 codegen 模块

```python
# src/codegen/__init__.py
import warnings

warnings.warn(
    "codegen 模块已废弃，请使用 zhc.ir.register_allocator 或 zhc.backend.*",
    DeprecationWarning,
    stacklevel=2
)

# 保持向后兼容
from zhc.ir.register_allocator import *
```

## 依赖关系图

### 重构前

```
codegen/
├── register_allocator.py
│   └── (无外部依赖)
├── allocator_interface.py
│   └── → register_allocator.py
└── c_codegen.py
    └── → zhc.parser.ast_nodes (循环依赖风险)
```

### 重构后

```
ir/
└── register_allocator.py
    └── (无外部依赖，纯算法)

backend/
├── allocator_interface.py
│   └── → zhc.ir.register_allocator
├── c_backend.py
│   └── → allocator_interface.py
├── llvm_backend.py
│   └── → allocator_interface.py
└── wasm_backend.py
    └── → allocator_interface.py
```

## API 变化

### 旧 API（废弃）

```python
from zhc.codegen import LinearScanRegisterAllocator
from zhc.codegen import create_allocator
```

### 新 API

```python
# IR 层：直接使用算法
from zhc.ir.register_allocator import LinearScanRegisterAllocator

# 后端层：使用适配接口
from zhc.backend.allocator_interface import create_allocator
```

## 兼容性保证

### 过渡期（1-2 个版本）

```python
# src/codegen/__init__.py
import warnings
from zhc.ir.register_allocator import *

warnings.warn(
    "从 zhc.codegen 导入寄存器分配器已废弃，"
    "请使用 zhc.ir.register_allocator",
    DeprecationWarning,
    stacklevel=2
)
```

### 正式版本

- 完全移除 `codegen` 模块
- 所有导入路径更新为 `zhc.ir.*` 或 `zhc.backend.*`

## 测试计划

### 单元测试

```bash
# IR 层测试
pytest tests/test_ir_register_allocator.py -v

# 后端适配测试
pytest tests/test_backend_allocator.py -v
```

### 集成测试

```bash
# C 后端集成
pytest tests/test_c_backend.py -v

# LLVM 后端集成
pytest tests/test_llvm_backend.py -v

# WASM 后端集成
pytest tests/test_wasm_backend.py -v
```

## 时间表

| 阶段 | 任务 | 时间 |
|------|------|------|
| Phase 1 | 移动文件到正确位置 | 1 天 |
| Phase 2 | 更新导入路径 | 1 天 |
| Phase 3 | 更新测试 | 1 天 |
| Phase 4 | 废弃 codegen 模块 | 1 天 |
| Phase 5 | 文档更新 | 0.5 天 |

**总计**: 4.5 天

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 导入路径变化 | 中 | 提供过渡期兼容层 |
| 测试失败 | 低 | 先更新测试再移动 |
| 文档过时 | 低 | 同步更新文档 |

## 结论

将寄存器分配器从 `codegen` 移动到 `ir` 模块是正确的架构决策：

1. **清晰的分层**：IR 层优化 vs 后端代码生成
2. **避免循环依赖**：IR 层不依赖 parser
3. **易于迁移**：废弃 codegen 时不受影响
4. **符合编译器架构**：SSA、数据流、寄存器分配都是 IR 层优化

建议立即执行重构，避免技术债务积累。
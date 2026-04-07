# Task 5.4 类型注解提升计划

**创建日期**: 2026-04-07  
**当前覆盖率**: 66.8% (C 及格)  
**目标覆盖率**: 90%+ (A 优秀)

---

## 当前状态

### 统计结果

| 指标 | 当前值 | 目标值 | 差距 |
|------|--------|--------|------|
| 函数覆盖率 | 71.1% (86/121) | 90%+ | +19% |
| 方法覆盖率 | 66.5% (1295/1947) | 90%+ | +24% |
| 参数覆盖率 | 96.1% (2344/2439) | 95%+ | ✅ 已达成 |
| 返回值覆盖率 | 68.8% (1423/2068) | 90%+ | +22% |
| **总体覆盖率** | **66.8%** | **90%+** | **+23%** |

### 主要问题

1. **方法类型注解不足** - 652 个方法缺少类型注解
2. **返回值类型注解不足** - 645 个返回值缺少类型注解
3. **核心模块优先级**:
   - `parser/lexer.py` - 181 个类型错误
   - `ir/ir_generator.py` - 47 个类型错误
   - `opt/loop_optimizer.py` - 18 个类型错误

---

## 提升计划

### Phase 1: 核心 API 优先（高优先级）

**目标**: 确保公共 API 完全类型注解

**任务**:
1. ✅ `src/cli.py` - ZHCCompiler, CompilerConfig 完全类型注解
2. ✅ `src/compiler/__init__.py` - 公共 API 完全类型注解
3. ✅ `src/compiler/pipeline.py` - CompilationPipeline 完全类型注解
4. ⏸️ `src/semantic/` - 语义分析模块完全类型注解
5. ⏸️ `src/codegen/` - 代码生成模块完全类型注解

**预期提升**: +5% (66.8% → 72%)

### Phase 2: 核心模块优化（中优先级）

**目标**: 修复核心模块的类型错误

**任务**:
1. ⏸️ `src/parser/lexer.py` - 修复 181 个类型错误
2. ⏸️ `src/ir/ir_generator.py` - 修复 47 个类型错误
3. ⏸️ `src/ir/opcodes.py` - 修复类型注解
4. ⏸️ `src/ir/llvm_backend.py` - 修复类型注解

**预期提升**: +10% (72% → 82%)

### Phase 3: 辅助模块完善（低优先级）

**目标**: 完善其他模块的类型注解

**任务**:
1. ⏸️ `src/opt/` - 优化器模块类型注解
2. ⏸️ `src/template/` - 模板引擎类型注解
3. ⏸️ `src/utils/` - 工具模块类型注解
4. ⏸️ `src/tool/` - 工具模块类型注解

**预期提升**: +8% (82% → 90%)

---

## 快速修复策略

### 1. 使用 `# type: ignore` 忽略已知错误

对于不影响功能的类型错误，可以使用 `# type: ignore` 暂时忽略：

```python
# 忽略特定错误类型
result = some_function()  # type: ignore[union-attr]

# 忽略所有错误
result = some_function()  # type: ignore
```

### 2. 使用 `cast()` 强制类型转换

对于确定类型的变量，可以使用 `cast()` 强制转换：

```python
from typing import cast

# 强制类型转换
value = cast(str, optional_value) + "suffix"
```

### 3. 添加默认值避免 Optional 问题

```python
# 避免 None 值
name = filepath.stem or "unknown"

# 使用空字符串替代 None
path = str(filepath) if filepath else ""
```

### 4. 使用 `# type: ignore` 注释批量修复

```bash
# 为所有错误添加忽略注释
mypy src/ --ignore-missing-imports | grep "error:" | \
  awk -F: '{print $1 ":" $2 ": error:"} {print "  # type: ignore"}' >> fix.log
```

---

## 验收标准

| 指标 | Week 5 结束 | Week 6 目标 | Week 7 目标 |
|------|------------|------------|------------|
| 函数覆盖率 | 71.1% | 85% | 95% |
| 方法覆盖率 | 66.5% | 80% | 90% |
| 参数覆盖率 | 96.1% | 97% | 98% |
| 返回值覆盖率 | 68.8% | 82% | 90% |
| **总体覆盖率** | **66.8%** | **82%** | **90%** |
| **评分** | **C** | **B** | **A** |

---

## 工具使用

### 类型注解覆盖率检查

```bash
# 运行覆盖率检查
python scripts/type_coverage_check.py

# 只检查 src 目录
python scripts/type_coverage_check.py src

# 检查特定文件
python scripts/type_coverage_check.py src/cli.py
```

### MyPy 类型检查

```bash
# 检查所有类型错误
mypy src --ignore-missing-imports

# 检查特定文件
mypy src/cli.py --ignore-missing-imports

# 显示详细错误
mypy src --ignore-missing-imports --show-traceback

# 生成错误报告
mypy src --ignore-missing-imports --no-error-summary | tee mypy_errors.txt
```

---

## 备注

- Task 5.4 已完成核心 API 的类型注解
- 其他模块的类型注解将在后续迭代中逐步完善
- Task 5.5 (代码审查和重构PR) 将在 Task 5.4 基础上进行

---

*最后更新: 2026-04-07*
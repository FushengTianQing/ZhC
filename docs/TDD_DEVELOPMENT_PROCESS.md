# TDD 开发流程指南

> 测试驱动开发（Test-Driven Development）实践指南
> 创建日期: 2026-04-07 | 维护者: ZHC开发团队

---

## 📋 核心原则

**"先写测试，再写代码"** - TDD 的核心思想是先定义期望的行为，再实现功能。

### 三步循环（Red-Green-Refactor）

1. **🔴 Red（红灯）** - 编写失败的测试
   - 先写测试代码，定义期望的行为
   - 运行测试，确认测试失败（红灯）
   - 失败意味着测试有效，能检测缺失的功能

2. **🟢 Green（绿灯）** - 编写最小代码使测试通过
   - 编写最简单的代码让测试通过
   - 不要过度设计，目标是让测试变绿
   - 可以用硬编码、简单实现等"作弊"手段

3. **🔵 Refactor（重构）** - 优化代码结构
   - 测试通过后，重构代码提高质量
   - 重构时测试保持绿灯，确保功能不变
   - 消除重复代码、优化设计、提高可读性

---

## 🛠️ ZHC 项目 TDD 实践流程

### 1. 新功能开发流程

```bash
# Step 1: 创建测试文件
touch tests/test_new_feature.py

# Step 2: 编写测试（红灯阶段）
# 在 test_new_feature.py 中编写测试代码
# pytest tests/test_new_feature.py -v  # 确认失败

# Step 3: 实现功能（绿灯阶段）
# 在 src/ 中实现功能代码
# pytest tests/test_new_feature.py -v  # 确认通过

# Step 4: 重构优化
# 优化代码结构，保持测试通过
# pytest tests/test_new_feature.py -v  # 确认仍然通过

# Step 5: 完整质量检查
black --check src/ tests/
ruff check src/ tests/
mypy src/
pytest tests/ -v --cov=src
```

### 2. Bug 修复流程

```bash
# Step 1: 编写失败的测试（重现 Bug）
# 在 tests/test_bug_fix.py 中编写测试，重现 Bug
pytest tests/test_bug_fix.py -v  # 确认失败（红灯）

# Step 2: 修复 Bug（绿灯阶段）
# 修改 src/ 中的代码修复 Bug
pytest tests/test_bug_fix.py -v  # 确认通过（绿灯）

# Step 3: 验证其他测试不受影响
pytest tests/ -v  # 确认所有测试通过

# Step 4: 重构优化（可选）
# 如果修复代码需要优化，进行重构
pytest tests/ -v  # 确认仍然通过
```

### 3. 重构流程

```bash
# Step 1: 确认现有测试全部通过
pytest tests/ -v  # 绿灯状态

# Step 2: 重构代码
# 修改 src/ 中的代码结构

# Step 3: 每次小改动后验证
pytest tests/ -v  # 确认仍然绿灯

# Step 4: 如果红灯，立即回退
# 重构过程中测试失败，说明破坏了功能
# 回退代码，重新思考重构方案

# Step 5: 完成重构后完整检查
black --check src/ tests/
ruff check src/ tests/
mypy src/
pytest tests/ -v --cov=src
```

---

## 📝 测试编写规范

### 测试文件命名

- 文件名: `test_<模块名>.py` 或 `<模块名>_test.py`
- 类名: `Test<功能名>`
- 函数名: `test_<具体场景>`

### 测试结构（AAA 模式）

```python
def test_parser_handles_chinese_keywords():
    # Arrange（准备）- 设置测试数据
    source_code = "整数 变量名 = 42;"
    
    # Act（执行）- 执行被测试的代码
    result = parser.parse(source_code)
    
    # Assert（断言）- 验证结果
    assert result.is_valid
    assert result.type == "integer_declaration"
```

### 测试覆盖场景

每个功能至少需要以下测试：

1. **正常场景** - 功能正常工作的典型用例
2. **边界场景** - 边界值、空值、极端情况
3. **异常场景** - 错误输入、异常处理
4. **集成场景** - 与其他模块的交互

---

## ✅ 提交前检查清单

每次提交代码前，必须完成以下检查：

```bash
# 1. 格式检查
black --check src/ tests/ scripts/

# 2. Linting 检查
ruff check src/ tests/ scripts/

# 3. 类型检查
mypy src/

# 4. 测试检查（覆盖率 ≥ 60%）
pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=60

# 5. 如果所有检查通过，提交代码
git add .
git commit -m "描述性提交信息"
git push
```

---

## 🚫 常见错误与避免方法

### ❌ 错误 1: 先写代码，后补测试

**问题**: 测试变成"验证代码"而非"定义行为"，容易遗漏边界情况。

**正确做法**: 先写测试，让测试驱动设计。

### ❌ 错误 2: 测试通过后不重构

**问题**: 代码质量停留在"最小实现"水平，难以维护。

**正确做法**: 绿灯后立即重构，提高代码质量。

### ❌ 错误 3: 重构时一次性改动太大

**问题**: 大改动容易引入 Bug，难以定位问题。

**正确做法**: 小步重构，每次改动后验证测试。

### ❌ 错误 4: 测试代码质量差

**问题**: 测试代码难以维护，成为负担而非资产。

**正确做法**: 测试代码也要遵循编码规范，保持清晰可读。

---

## 📊 测试覆盖率目标

| Phase | 覆盖率目标 | 说明 |
|-------|-----------|------|
| Phase 1 | ≥ 60% | 基础覆盖率，核心模块优先 |
| Phase 2 | ≥ 70% | 提高覆盖率，补充边界测试 |
| Phase 3 | ≥ 80% | 高覆盖率，全面测试 |
| Phase 4+ | ≥ 90% | 生产级覆盖率 |

---

## 🔗 相关文档

- [代码审查清单](./CODE_REVIEW_CHECKLIST.md)
- [团队技术提升计划](./TEAM_TECH_IMPROVEMENT_PLAN.md)
- [项目架构文档](./ARCHITECTURE.md)

---

## 📚 参考资料

- [Test-Driven Development: By Example](https://www.oreilly.com/library/view/test-driven-development/0321146530/) - Kent Beck
- [Python Testing with pytest](https://pragprog.com/titles/bopytest/python-testing-with-pytest/) - Brian Okken
- [pytest 官方文档](https://docs.pytest.org/)

---

> **记住**: TDD 不是为了写测试，而是为了通过测试驱动更好的设计。
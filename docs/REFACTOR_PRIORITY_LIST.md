# ZHC 代码重构优先级列表

**生成日期**: 2026-04-07  
**分析工具**: `scripts/quality_check.py`  
**质量评分**: 65/100 [B 中等]

---

## 📊 总体统计

| 指标 | 当前值 | 目标值 | 状态 |
|-----|--------|--------|------|
| 文件数 | 119 | - | - |
| 总行数 | 43,819 | - | - |
| 代码行数 | 29,926 | - | - |
| 函数数量 | 2,027 | - | - |
| 类数量 | 395 | - | - |
| 平均最大函数长度 | 43.1 行 | <30 行 | ⚠️ 需改进 |
| 平均最大圈复杂度 | 8.5 | <8 | ⚠️ 需改进 |
| 高复杂度函数数 | 36 | <20 | ⚠️ 需改进 |
| 问题总数 | 441 | <100 | ⚠️ 需改进 |

---

## 🔴 P0: 高优先级重构（圈复杂度 > 15）

### 1. `src/ir/optimizer.py` - 圈复杂度 23

**问题描述**: 
- `_try_fold()` 方法包含大量 if-elif 分支，处理不同操作符
- 每个操作符类型都需要单独处理，导致复杂度累积

**重构方案**:
```python
# 当前代码（复杂度 23）
def _try_fold(self, instr: IRInstruction):
    if op == Opcode.ADD:
        return vals[0] + vals[1]
    if op == Opcode.SUB:
        return vals[0] - vals[1]
    # ... 14 个分支

# 重构后（复杂度 < 5）
OPERATOR_FUNCTIONS = {
    Opcode.ADD: lambda a, b: a + b,
    Opcode.SUB: lambda a, b: a - b,
    Opcode.MUL: lambda a, b: a * b,
    # ...
}

def _try_fold(self, instr: IRInstruction):
    op_func = OPERATOR_FUNCTIONS.get(instr.opcode)
    if op_func:
        return op_func(*vals)
    return None
```

**预计工作量**: 2小时  
**影响范围**: IR 优化模块  
**风险等级**: 低（纯重构，不改变行为）

---

### 2. `src/ir/ir_generator.py` - 圈复杂度 17

**问题描述**:
- `_eval_expr()` 方法包含大量类型判断和分支
- 表达式求值逻辑集中在一个方法中

**重构方案**:
```python
# 当前代码（复杂度 17）
def _eval_expr(self, node: ASTNode):
    if nt == 'INT_LITERAL':
        return self._eval_literal(node, '整数型', ...)
    if nt == 'FLOAT_LITERAL':
        return self._eval_literal(node, '双精度浮点型', ...)
    # ... 12 个分支

# 重构后（使用 dispatch table）
EVALUATORS = {
    'INT_LITERAL': '_eval_int_literal',
    'FLOAT_LITERAL': '_eval_float_literal',
    'BINARY_EXPR': '_eval_binary',
    # ...
}

def _eval_expr(self, node: ASTNode):
    evaluator_name = EVALUATORS.get(node.node_type.name)
    if evaluator_name:
        return getattr(self, evaluator_name)(node)
    return None
```

**预计工作量**: 3小时  
**影响范围**: IR 生成模块  
**风险等级**: 中（需要充分测试）

---

### 3. `src/parser/class_extended.py` - 圈复杂度 17

**问题描述**:
- `parse_line()` 方法包含大量条件判断
- 状态管理复杂（current_class, current_section, in_method_body）

**重构方案**:
```python
# 当前代码（复杂度 17）
def parse_line(self, line: str, line_num: int):
    if re.match(self.CLASS_END_PATTERN, stripped):
        # ...
    if self.in_method_body:
        # ...
    if class_match:
        # ...
    if re.match(self.VISIBILITY_PATTERN, stripped):
        # ...
    # ... 多个分支

# 重构后（状态机模式）
class ParseState(Enum):
    IDLE = "idle"
    IN_CLASS = "in_class"
    IN_METHOD_BODY = "in_method_body"

def parse_line(self, line: str, line_num: int):
    handlers = {
        ParseState.IDLE: self._parse_idle,
        ParseState.IN_CLASS: self._parse_in_class,
        ParseState.IN_METHOD_BODY: self._parse_in_method_body,
    }
    handlers[self.state](line, line_num)
```

**预计工作量**: 4小时  
**影响范围**: 类解析器模块  
**风险等级**: 中（需要重新测试解析器）

---

### 4. `src/cli/main.py` - 圈复杂度 16

**问题描述**:
- 命令行参数处理逻辑复杂
- 多个子命令的处理逻辑交织

**重构方案**:
```python
# 当前代码（复杂度 16）
def main():
    args = parser.parse_args()
    if args.command == 'init':
        # ...
    elif args.command == 'build':
        # ...
    # ... 多个分支

# 重构后（命令模式）
class CommandHandler(ABC):
    @abstractmethod
    def execute(self, args): pass

class InitCommand(CommandHandler):
    def execute(self, args): ...

COMMAND_HANDLERS = {
    'init': InitCommand(),
    'build': BuildCommand(),
    # ...
}

def main():
    args = parser.parse_args()
    handler = COMMAND_HANDLERS.get(args.command)
    if handler:
        handler.execute(args)
```

**预计工作量**: 3小时  
**影响范围**: CLI 模块  
**风险等级**: 低（外部接口不变）

---

## 🟡 P1: 中优先级重构（函数长度 > 50 行）

### 5. `src/converter/error.py` - 最长函数 76 行

**问题**: `ErrorRecord.__init__()` 参数过多，初始化逻辑复杂

**重构方案**:
- 使用 `@dataclass` 简化初始化
- 提取验证逻辑到单独方法

**预计工作量**: 1小时

---

### 6. `src/cli.py` - 最长函数 61 行

**问题**: 单个函数处理多个子命令，逻辑冗长

**重构方案**:
- 拆分为多个子命令处理函数
- 使用命令模式（同 main.py）

**预计工作量**: 2小时

---

### 7. `src/generics/generic_parser.py` - 最长函数 54 行

**问题**: 泛型参数解析逻辑复杂

**重构方案**:
- 提取参数解析逻辑到独立函数
- 使用递归下降解析器

**预计工作量**: 3小时

---

## 🟢 P2: 低优先级重构（文件过大 > 500 行）

### 8. `src/converter/code.py` - 647 行

**问题**: 文件过长，职责不清晰

**重构方案**:
- 拆分为 `code_converter.py` 和 `code_generator.py`
- 提取符号转换逻辑到 `symbol_converter.py`

**预计工作量**: 4小时

---

### 9. `src/cli.py` - 588 行

**问题**: CLI 逻辑和工具函数混杂

**重构方案**:
- 拆分为 `cli_parser.py` 和 `cli_commands.py`
- 提取工具函数到 `cli_utils.py`

**预计工作量**: 3小时

---

### 10. `src/converter/error.py` - 537 行

**问题**: 错误类型定义和处理逻辑混杂

**重构方案**:
- 拆分为 `error_types.py` 和 `error_handler.py`
- 提取错误格式化逻辑到 `error_formatter.py`

**预计工作量**: 2小时

---

## 📋 重构执行计划

### Week 5 Day 1-2: P0 高优先级
- [ ] Task 5.1.1: 重构 `optimizer.py` (2h)
- [ ] Task 5.1.2: 重构 `ir_generator.py` (3h)
- [ ] Task 5.1.3: 重构 `class_extended.py` (4h)
- [ ] Task 5.1.4: 重构 `cli/main.py` (3h)

### Week 5 Day 3-4: P1 中优先级
- [ ] Task 5.2.1: 重构 `converter/error.py` 函数 (1h)
- [ ] Task 5.2.2: 重构 `cli.py` 函数 (2h)
- [ ] Task 5.2.3: 重构 `generic_parser.py` (3h)

### Week 5 Day 5-6: P2 低优先级
- [ ] Task 5.3.1: 拆分 `converter/code.py` (4h)
- [ ] Task 5.3.2: 拆分 `cli.py` (3h)
- [ ] Task 5.3.3: 拆分 `converter/error.py` (2h)

---

## ✅ 验收标准

### 代码质量指标
- [ ] 平均圈复杂度 < 8
- [ ] 高复杂度函数数 < 20
- [ ] 平均函数长度 < 30 行
- [ ] 问题总数 < 100

### 测试要求
- [ ] 所有现有测试通过
- [ ] 新增重构相关单元测试
- [ ] 测试覆盖率 ≥ 60.95%（不下降）

### 文档要求
- [ ] 更新相关模块文档
- [ ] 记录重构决策和理由
- [ ] 更新 API 文档（如有变更）

---

## 📝 备注

1. **重构原则**:
   - 小步快跑，每次只重构一个函数/模块
   - 保持测试通过，确保行为不变
   - 及时提交，便于回滚

2. **风险评估**:
   - P0 重构风险较低，主要是简化逻辑
   - P1 重构需要充分测试
   - P2 重构涉及文件拆分，需要更新导入

3. **依赖关系**:
   - 先完成 P0，再进行 P1 和 P2
   - 同一优先级内可并行执行
   - 注意模块间的依赖关系

---

**创建日期**: 2026-04-07  
**负责人**: ZHC 开发团队  
**预计完成**: 2026-04-14

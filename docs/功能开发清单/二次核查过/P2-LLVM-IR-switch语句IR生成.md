# P2-LLVM-IR-switch语句IR生成

## 任务概览

| 属性 | 内容 |
|------|------|
| **优先级** | P2 |
| **功能模块** | LLVM IR |
| **功能名称** | switch 语句 IR 生成 |
| **任务类型** | 新功能实现 |
| **预计工时** | 6-8 小时 |
| **前置依赖** | P2-LLVM-IR-数组索引GEP指令（可选） |

---

## 1. 当前实现分析

### 1.1 现有代码位置

```
src/zhc/backend/llvm_instruction_strategy.py  (SwitchStrategy 类)
src/zhc/ir/opcodes.py                         (Opcode.SWITCH 定义)
src/zhc/ir/instructions.py                    (Switch 指令定义)
src/zhc/ir/ir_generator.py                    (Switch IR 生成)
```

### 1.2 现有实现

#### SwitchStrategy（第 361-390 行）

```python
class SwitchStrategy(InstructionStrategy):
    """
    Switch 多分支跳转策略

    使用方式：
        switch %val, %default, [val1, %label1], [val2, %label2], ...
    """

    opcode = Opcode.SWITCH

    def compile(self, builder, instr, context):
        # 获取条件值
        val = context.get_value(instr.operands[0])

        # 获取默认目标块
        default_label = str(instr.operands[1])
        default_block = context.get_block(default_label)

        # 收集所有 case 分支
        cases = []
        for i in range(2, len(instr.operands), 2):
            if i + 1 < len(instr.operands):
                case_val = context.get_value(instr.operands[i])
                case_label = str(instr.operands[i + 1])
                case_block = context.get_block(case_label)
                cases.append((case_val, case_block))

        # 创建 switch 指令
        builder.switch(val, default_block, cases)
        return None
```

#### IR 生成器实现（ir_generator.py 第 1009-1041 行）

```python
def visit_switch_stmt(self, node: SwitchStmtNode):
    """switch 语句"""
    self._ensure_block()
    old_switch = self._in_switch
    self._in_switch = True

    self._eval_expr(node.expr)

    end_bb = IRBasicBlock(self._new_bb_label("switch_end"))
    self.current_function.basic_blocks.append(end_bb)
    self._push_break_target(end_bb.label)

    # 处理 case
    if node.cases:
        for case in node.cases:
            case.accept(self)

    self._pop_break_target()
    self._in_switch = old_switch

    if self.current_block and not self.current_block.is_terminated():
        self._emit(Opcode.JMP, [end_bb.label])

    self._switch_block(end_bb)

def visit_case_stmt(self, node: CaseStmtNode):
    """case 语句"""
    # case 不生成独立基本块，由 switch_stmt 处理
    pass

def visit_default_stmt(self, node: DefaultStmtNode):
    """default 语句"""
    pass
```

### 1.3 现有问题分析

| 问题 ID | 严重程度 | 问题描述 |
|---------|----------|----------|
| SW-001 | 🔴 高 | case 语句生成逻辑不完整 - `visit_case_stmt` 和 `visit_default_stmt` 为空实现 |
| SW-002 | 🔴 高 | 缺少 case 跳转目标块的正确关联 |
| SW-003 | 🟡 中 | switch 指令操作数格式不明确 |
| SW-004 | 🟡 中 | 缺少 fall-through（贯穿）语义支持 |
| SW-005 | 🟢 低 | 范围 case（case 1...5）未支持 |

---

## 2. 详细技术方案

### 2.1 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                 ZhC 源代码 - switch 语句                     │
│                                                             │
│  switch (x) {                                              │
│      case 1: a = 1; break;                                 │
│      case 2: a = 2; break;                                │
│      default: a = 0;                                       │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 IR 生成器 - visit_switch_stmt               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. 评估 switch 表达式                                  │    │
│  │ 2. 创建 end_bb（合并块）                               │    │
│  │ 3. 为每个 case 创建独立基本块                           │    │
│  │ 4. 生成 switch IR 指令                                │    │
│  │ 5. 处理 case 体的代码生成                              │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 SwitchStrategy - LLVM IR                    │
│                                                             │
│  entry:                                                    │
│    %cond = ...                                              │
│    switch i32 %cond, label %.default [                     │
│        i32 1, label %.case1,                               │
│        i32 2, label %.case2                                │
│    ]                                                        │
│                                                             │
│  .case1:           ; case 1 的基本块                         │
│    store i32 1, i32* %a                                     │
│    br label %.switch_end                                    │
│                                                             │
│  .case2:           ; case 2 的基本块                         │
│    store i32 2, i32* %a                                     │
│    br label %.switch_end                                    │
│                                                             │
│  .default:         ; 默认基本块                              │
│    store i32 0, i32* %a                                     │
│    br label %.switch_end                                    │
│                                                             │
│  .switch_end:      ; 合并点                                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心数据结构

#### 2.2.1 Switch 指令定义

```python
# src/zhc/ir/instructions.py

class SwitchInstr(Instruction):
    """Switch 多分支跳转指令

    操作数格式：
        operands[0]: 条件值
        operands[1]: 默认目标标签
        operands[2n]: case 值
        operands[2n+1]: case 目标标签
    """

    def __init__(self, cond: 'Value', default_label: str,
                 cases: List[Tuple[int, str]]):
        """
        Args:
            cond: 条件值
            default_label: 默认分支标签
            cases: [(case_value, target_label), ...]
        """
        super().__init__(Opcode.SWITCH)
        self._operands = [cond, default_label]
        for val, label in cases:
            self._operands.extend([val, label])

    @property
    def condition(self) -> 'Value':
        return self._operands[0]

    @property
    def default_label(self) -> str:
        return str(self._operands[1])

    @property
    def case_branches(self) -> List[Tuple[Any, str]]:
        """返回所有 case 分支 [(value, label), ...]"""
        cases = []
        for i in range(2, len(self._operands), 2):
            if i + 1 < len(self._operands):
                cases.append((self._operands[i], str(self._operands[i + 1])))
        return cases
```

#### 2.2.2 Case 语句节点

```python
# src/zhc/ast/nodes.py

@dataclass
class CaseStmtNode(ASTNode):
    """Case 语句节点"""
    value: Any                          # case 值
    statements: List['ASTNode']         # case 体的语句
    target_label: str = None            # 关联的目标基本块标签

    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_case_stmt(self)


@dataclass
class DefaultStmtNode(ASTNode):
    """Default 语句节点"""
    statements: List['ASTNode']         # default 体的语句
    target_label: str = None            # 关联的目标基本块标签

    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_default_stmt(self)
```

### 2.3 IR 生成器增强

```python
def visit_switch_stmt(self, node: SwitchStmtNode):
    """switch 语句 - 完整实现"""
    self._ensure_block()

    # 保存上下文
    old_switch = self._in_switch
    old_break = self._break_target
    self._in_switch = True

    # 1. 评估 switch 表达式
    cond_value = self._eval_expr(node.expr)
    cond_type = cond_value.type

    # 2. 创建基本块
    end_bb = IRBasicBlock(self._new_bb_label("switch_end"))
    self.current_function.basic_blocks.append(end_bb)

    # 3. 为每个 case/default 创建基本块
    case_blocks = {}  # label -> basic_block
    for i, case in enumerate(node.cases):
        if isinstance(case, CaseStmtNode):
            case_label = self._new_bb_label(f"case_{case.value}")
        else:  # DefaultStmtNode
            case_label = self._new_bb_label("default")
        case_bb = IRBasicBlock(case_label)
        self.current_function.basic_blocks.append(case_bb)
        case_blocks[case_label] = case_bb

    # 4. 确定默认分支
    default_label = "default" if "default" in case_blocks else end_bb.label
    default_block = case_blocks.get(default_label, end_bb)

    # 5. 收集所有 case 分支
    switch_cases = []
    for case in node.cases:
        if isinstance(case, CaseStmtNode):
            # 创建 case 值常量
            case_value = self._make_constant(cond_type, case.value)
            target_label = None
            for lbl, bb in case_blocks.items():
                if lbl.startswith(f"case_{case.value}"):
                    target_label = lbl
                    break
            if target_label:
                switch_cases.append((case_value, target_label))

    # 6. 发射 switch 指令
    self._emit(Opcode.SWITCH, [cond_value, default_label] +
               [item for pair in switch_cases for item in pair])

    # 7. 处理每个 case 的语句体
    for case in node.cases:
        case.accept(self)

    # 8. 恢复上下文
    self._in_switch = old_switch
    self._pop_break_target()

    # 9. 跳转到 end_bb（如果当前块未终止）
    if self.current_block and not self.current_block.is_terminated():
        self._emit(Opcode.JMP, [end_bb.label])

    # 10. 设置当前块为 end_bb
    self._switch_block(end_bb)


def visit_case_stmt(self, node: CaseStmtNode):
    """Case 语句 - 生成 case 基本块的代码"""
    # 找到对应的基本块
    target_label = node.target_label
    if not target_label:
        # 创建标签
        target_label = self._new_bb_label(f"case_{node.value}")

    if target_label not in [bb.label for bb in self.current_function.basic_blocks]:
        # 创建新基本块
        case_bb = IRBasicBlock(target_label)
        self.current_function.basic_blocks.append(case_bb)

    case_bb = self.current_function.find_basic_block(target_label)
    self._switch_block(case_bb)

    # 生成 case 体的代码
    self._push_break_target(self._get_switch_end_label())
    for stmt in node.statements:
        stmt.accept(self)
    self._pop_break_target()

    # 检查是否需要 break（fall-through 处理）
    has_break = any(isinstance(s, BreakStmtNode) for s in node.statements)
    if not has_break:
        # fall-through: 跳转到 end_bb
        self._emit(Opcode.JMP, [self._get_switch_end_label()])


def visit_default_stmt(self, node: DefaultStmtNode):
    """Default 语句 - 生成 default 基本块的代码"""
    target_label = self._new_bb_label("default")

    if target_label not in [bb.label for bb in self.current_function.basic_blocks]:
        default_bb = IRBasicBlock(target_label)
        self.current_function.basic_blocks.append(default_bb)

    default_bb = self.current_function.find_basic_block(target_label)
    self._switch_block(default_bb)

    # 生成 default 体的代码
    self._push_break_target(self._get_switch_end_label())
    for stmt in node.statements:
        stmt.accept(self)
    self._pop_break_target()

    # 检查是否需要 break
    has_break = any(isinstance(s, BreakStmtNode) for s in node.statements)
    if not has_break:
        self._emit(Opcode.JMP, [self._get_switch_end_label()])
```

### 2.4 SwitchStrategy 增强

```python
class EnhancedSwitchStrategy(InstructionStrategy):
    """
    增强型 Switch 多分支跳转策略

    改进点：
    1. 支持整数和字符类型
    2. 优化 case 排序（用于二分查找）
    3. 支持稀疏/密集 switch 优化提示
    """

    opcode = Opcode.SWITCH

    def compile(self, builder, instr, context):
        # 获取条件值
        cond = context.get_value(instr.operands[0])

        # 获取默认目标块
        default_label = str(instr.operands[1])
        default_block = context.get_block(default_label)

        # 收集所有 case 分支
        cases = []
        for i in range(2, len(instr.operands), 2):
            if i + 1 < len(instr.operands):
                case_val = self._resolve_case_value(
                    instr.operands[i], cond.type, context
                )
                case_label = str(instr.operands[i + 1])
                case_block = context.get_block(case_label)
                if case_block:
                    cases.append((case_val, case_block))

        # 创建 switch 指令
        builder.switch(cond, default_block, cases)
        return None

    def _resolve_case_value(self, operand, cond_type, context):
        """解析 case 值，确保类型匹配"""
        if isinstance(operand, int):
            # 创建整数常量
            return context.builder.context.get_constant(
                cond_type, operand
            )
        elif isinstance(operand, str):
            # 字符常量
            return context.builder.context.get_constant(
                cond_type, ord(operand)
            )
        else:
            return context.get_value(operand)
```

### 2.5 LLVM IR 生成示例

#### 输入：ZhC 源代码

```zhc
switch (grade) {
    case 90: rank = "A"; break;
    case 80: rank = "B"; break;
    case 70: rank = "C"; break;
    default: rank = "F";
}
```

#### 输出：LLVM IR

```llvm
; 主函数入口
define i8* @grade_to_rank(i32 %grade) {
entry:
  %cond = alloca i32
  store i32 %grade, i32* %cond
  %rank = alloca i8*
  br label %switch_main

; Switch 主块
switch_main:
  %grade_val = load i32, i32* %cond
  switch i32 %grade_val, label %.default [
    i32 90, label %.case_90
    i32 80, label %.case_80
    i32 70, label %.case_70
  ]

; case 90
.case_90:
  store i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str.A, i32 0, i32 0), i8** %rank
  br label %.switch_end

; case 80
.case_80:
  store i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str.B, i32 0, i32 0), i8** %rank
  br label %.switch_end

; case 70
.case_70:
  store i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str.C, i32 0, i32 0), i8** %rank
  br label %.switch_end

; default
.default:
  store i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str.F, i32 0, i32 0), i8** %rank
  br label %.switch_end

; Switch 结束
.switch_end:
  %result = load i8*, i8** %rank
  ret i8* %result
}
```

---

## 3. 实现计划

### 3.1 阶段划分

| 阶段 | 内容 | 工时 |
|------|------|------|
| Phase 1 | Case/Default 节点定义完善 | 1h |
| Phase 2 | IR 生成器增强 | 2h |
| Phase 3 | SwitchStrategy 增强 | 1h |
| Phase 4 | 单元测试编写 | 1h |
| Phase 5 | 集成测试与调试 | 2h |

### 3.2 代码变更清单

| 文件 | 变更类型 | 描述 |
|------|----------|------|
| `src/zhc/ast/nodes.py` | 修改 | 完善 CaseStmtNode, DefaultStmtNode |
| `src/zhc/ir/instructions.py` | 修改 | 完善 SwitchInstr 类 |
| `src/zhc/ir/ir_generator.py` | 修改 | 实现完整的 switch IR 生成逻辑 |
| `src/zhc/backend/llvm_instruction_strategy.py` | 修改 | 增强 SwitchStrategy |
| `tests/test_switch.py` | 新增 | switch 语句测试用例 |

---

## 4. 测试计划

### 4.1 单元测试用例

```python
def test_simple_switch():
    """测试简单 switch"""
    code = """
    let x = 1;
    switch (x) {
        case 1: result = "one";
        case 2: result = "two";
        default: result = "other";
    }
    """

def test_switch_with_break():
    """测试带 break 的 switch"""
    # 每个 case 后有 break，正确跳转到 end

def test_switch_fallthrough():
    """测试 fall-through 语义"""
    # 没有 break 的 case 应该 fall-through

def test_switch_nested():
    """测试嵌套 switch"""
    # switch 内嵌套 switch

def test_switch_expr():
    """测试表达式作为 switch 条件"""
    # switch (a + b * c)
```

### 4.2 集成测试场景

| 测试场景 | 输入代码 | 验证点 |
|----------|----------|--------|
| 基本 switch | `switch(x) { case 1: a; }` | 生成正确的 switch IR |
| 多 case | `switch(x) { case 1: a; case 2: b; }` | 所有 case 分支正确 |
| default 分支 | `switch(x) { default: a; }` | default 标签正确 |
| break 语句 | 带 break 的各个 case | 正确跳转到 end_bb |
| fall-through | case 后无 break | 正确贯穿到下一个 case |
| 嵌套结构 | 嵌套 if/switch | CFG 正确 |

---

## 5. 预期成果

### 5.1 功能成果

- [x] 详细的开发内容分析文档
- [ ] 完整的 switch IR 生成逻辑
- [ ] 正确的 case/default 跳转
- [ ] 支持 break/fall-through 语义
- [ ] 全面的测试覆盖

### 5.2 技术指标

| 指标 | 目标值 |
|------|--------|
| switch IR 生成正确率 | 100% |
| case 跳转正确率 | 100% |
| fall-through 语义正确率 | 100% |
| 单元测试覆盖率 | >90% |

### 5.3 文档输出

- 本分析文档
- switch 语句使用文档
- 测试用例文档

---

## 6. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| case 值类型不一致 | 高 | 在语义分析阶段添加类型检查 |
| CFG 生成复杂 | 中 | 分步骤实现，先支持简单场景 |
| fall-through 语义歧义 | 中 | 明确 fall-through 规则，添加警告 |

---

## 7. 参考资料

- [LLVM Language Reference - Switch Instruction](https://llvm.org/docs/LangRef.html#switch-instruction)
- [llvmlite Switch Builder](https://llvmlite.readthedocs.io/)
- ZhC 项目现有 `llvm_instruction_strategy.py` 实现
- ZhC 项目现有 `ir_generator.py` 实现

---

**文档版本**: 1.0
**创建日期**: 2026-04-09
**负责人**: AI Compiler Expert
**状态**: 待执行

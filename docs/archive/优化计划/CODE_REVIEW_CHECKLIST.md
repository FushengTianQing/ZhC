# ZHC 代码审查清单

## 📋 审查前自查

开发者在提交PR前，请确认：

- [ ] 代码符合项目编码规范
- [ ] 所有新功能都有对应的单元测试
- [ ] 测试覆盖率没有下降
- [ ] 代码通过 `ruff check` 检查
- [ ] 代码通过 `black --check` 格式检查
- [ ] 代码通过 `mypy` 类型检查
- [ ] 文档字符串（docstring）完整且准确
- [ ] Commit message 符合规范

---

## 🔍 代码质量检查项

### 功能正确性
- [ ] **逻辑正确**: 代码实现了预期功能，无逻辑错误
- [ ] **边界条件**: 处理了所有边界情况（空值、极值、异常输入）
- [ ] **错误处理**: 异常处理完整，不会吞掉重要错误
- [ ] **资源管理**: 文件、连接等资源正确释放
- [ ] **线程安全**: 如涉及并发，确保线程安全

### 代码可读性
- [ ] **命名清晰**: 变量名、函数名表达意图明确
- [ ] **方法简短**: 单个方法不超过30行（复杂算法除外）
- [ ] **职责单一**: 每个函数/类只做一件事
- [ ] **注释适当**: 必要处有注释，无冗余注释
- [ ] **结构清晰**: 缩进、空行、分组合理

### 性能考量
- [ ] **时间复杂度**: 算法复杂度合理，无明显性能瓶颈
- [ ] **空间效率**: 无不必要的内存分配或复制
- [ ] **I/O优化**: 减少不必要的文件/网络操作
- [ ] **热点优化**: 对热路径有性能考虑

### 安全性
- [ ] **输入验证**: 外部输入经过验证和清理
- [ ] **注入防护**: 无SQL注入、命令注入等漏洞
- [ ] **敏感数据**: 密码、token等不硬编码在代码中
- [ ] **权限检查**: 操作前验证用户权限

---

## 🧪 测试审查

### 单元测试要求
```python
# ✅ 好的测试示例
def test_parse_function_with_params(self):
    """测试带参数的函数解析"""
    # Given - 准备测试数据
    code = "整数型 加法(整数型 a, 整数型 b) { 返回 a + b; }"
    
    # When - 执行被测操作
    ast, errors = parse(code)
    
    # Then - 验证结果
    self.assertEqual(len(errors), 0)
    self.assertEqual(len(ast.declarations), 1)
    
    func = ast.declarations[0]
    self.assertIsInstance(func, FunctionDeclNode)
    self.assertEqual(func.name, "加法")
    self.assertEqual(len(func.params), 2)
```

**必须包含的测试场景**:
- [ ] 正常输入（Happy Path）
- [ ] 边界条件（Boundary）
- [ ] 异常输入（Invalid Input）
- [ ] 空/None 处理
- [ ] 并发安全（如适用）

**测试命名规范**:
```
test_<功能>_<场景>_<期望结果>
test_parse_function_valid_input_returns_correct_ast
test_type_check_incompatible_types_reports_error
test_codegen_handles_empty_program_gracefully
```

---

## 📐 架构/设计审查

### 设计原则检查
- [ ] **SRP**: 单一职责原则 - 类/模块职责单一
- [ ] **OCP**: 开闭原则 - 对扩展开放，对修改关闭
- [ ] **LSP**: 里氏替换原则 - 子类可以替换父类
- [ ] **ISP**: 接口隔离原则 - 接口精简
- [ ] **DIP**: 依赖倒置原则 - 依赖抽象不依赖具体

### 模块化检查
- [ ] **耦合度低**: 模块间依赖最小化
- [ ] **内聚性高**: 相关功能聚合在一起
- [ ] **接口清晰**: 公共API定义明确
- [ ] **依赖方向**: 依赖方向合理（高层→低层）

### 扩展性评估
- [ ] 新增功能是否容易添加
- [ ] 是否支持插件/扩展机制
- [ ] 配置是否灵活可配置

---

## 📝 文档审查

### 代码内文档
```python
def parse_expression(self) -> ASTNode:
    """解析表达式
    
    实现递归下降解析器，按照以下优先级处理：
    1. 赋值表达式 (= += -= *= /= %=)
    2. 逻辑或 (||)
    3. 逻辑与 (&&)
    4. 相等性 (== !=)
    5. 比较 (< > <= >=)
    6. 加减 (+ -)
    7. 乘除 (* / %)
    8. 一元运算 (- ! ~ ++ -- & *)
    
    Args:
        无显式参数（使用self.tokens）
        
    Returns:
        ASTNode: 表达式AST节点
        
    Raises:
        ParseError: 语法错误时抛出
        
    Example:
        >>> parser = Parser(tokens)
        >>> ast = parser.parse_expression()
        >>> print(ast.type)
        'BinaryExprNode'
    """
```

**检查项**:
- [ ] 所有公共API都有docstring
- [ ] 参数和返回值说明清晰
- [ ] 异常情况文档化
- [ ] 使用示例准确有效
- [ ] 复杂算法有时间/空间复杂度说明

---

## ⚠️ 常见问题模式

### ❌ 反模式（避免）

#### 1. 魔法数字
```python
# ❌ 差
if status == 3:
    ...

# ✅ 好
COMPLETED_STATUS = 3
if status == COMPLETED_STATUS:
    ...
```

#### 2. 过深的嵌套
```python
# ❌ 差
if condition1:
    if condition2:
        for item in items:
            if item.valid:
                process(item)

# ✅ 好 - 提前返回
if not condition1:
    return
if not condition2:
    return
for item in items:
    if not item.valid:
        continue
    process(item)
```

#### 3. 异常吞没
```python
# ❌ 差
try:
    risky_operation()
except:
    pass  # 静默忽略所有错误

# ✅ 好 - 记录并重新抛出
try:
    risky_operation()
except SpecificError as e:
    logger.error(f"操作失败: {e}")
    raise  # 或者转换为业务异常后抛出
```

#### 4. 全局状态
```python
# ❌ 差
global_cache = {}

def get_data(key):
    global global_cache
    if key in global_cache:
        return global_cache[key]
    ...

# ✅ 好 - 依赖注入
class DataService:
    def __init__(self, cache=None):
        self._cache = cache or {}
    
    def get_data(self, key):
        if key in self._cache:
            return self._cache[key]
        ...
```

---

## ✅ 审查通过标准

### 可以合并（LGTM）的条件：
1. 所有MUST项全部满足
2. SHOULD项最多1项未满足（需说明原因）
3. 无严重安全问题
4. 无明显的逻辑错误
5. 测试充分覆盖新增/修改的代码
6. 文档更新完整

### 需要修改的条件：
- 有任何MUST项未满足
- 存在安全漏洞
- 逻辑错误或边界条件遗漏
- 测试不足
- 性能严重退化

### 拒绝合并的情况：
- 多个SHOULD项未满足
- 架构设计不合理
- 代码风格严重偏离规范
- 缺少必要文档

---

## 🔄 审查流程

### 标准流程
```
开发者提交 PR 
    ↓
自动CI运行（~5分钟）
    ↓
CI通过 → 分配Reviewer
    ↓
Review（24小时内完成）
    ↓
├─ LGTM → 可合并
├─ Request Changes → 开发者修改 → 重新Review
└─ Comment → 讨论解决
```

### Reviewer职责
1. **及时响应**: 收到PR后24小时内开始Review
2. **全面检查**: 按此清单逐项检查
3. **建设性反馈**: 指出问题的同时提供改进建议
4. **关注成长**: 帮助团队成员提升技能
5. **尊重作者**: 评论专业友善，聚焦代码本身

---

**版本**: v1.0  
**最后更新**: 2026-04-07
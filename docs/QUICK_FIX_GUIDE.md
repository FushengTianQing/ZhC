# ZHC 代码质量快速改进指南

## 📊 当前状态（2026-04-07）

### 总体评分: 60/100 [B 中等]

| 指标 | 当前值 | 目标值 | 状态 |
|------|--------|--------|------|
| 文件数 | 106 | - | ✅ |
| 总代码行数 | 27,635 | - | ✅ |
| 函数数量 | 1,872 | - | ✅ |
| 平均最大函数长度 | **47.3行** | ≤30行 | ⚠️ 需改进 |
| 平均圈复杂度 | **9.5** | ≤8 | ⚠️ 接近阈值 |
| 类型注解覆盖率 | 计算异常 | ≥80% | ❌ 需大幅提升 |

---

## 🔴 关键问题清单 (Top 10)

### 1. 高复杂度文件（需要重构）

| 文件 | 复杂度 | 建议 |
|------|--------|------|
| `ir/c_backend.py` | **36** | 拆分为多个策略类 |
| `cli.py` | **32** | 提取命令处理器 |
| `ir/ir_generator.py` | **25** | 分离visit方法到独立模块 |
| `optimizer.py` | **23** | 使用Visitor模式分离优化pass |
| `integrated.py` | **20** | 简化流程逻辑 |

### 2. 过长函数（需要拆分）

| 文件/函数 | 行数 | 建议 |
|-----------|------|------|
| `cli.py` run_codegen | **170行** | 拆分为5-8个子函数 |
| `generic_parser.py` | **54行** | 提取解析逻辑 |
| `attribute.py` | **44行** | 分离属性处理 |
| `error.py` | 文件537行 | 按错误类型拆分模块 |

### 3. 缺失文档字符串
- **402个函数**缺少docstring
- 主要集中在CLI和工具模块

---

## 🛠️ 改进方案

### Phase 1: 快速修复（1周内完成）

#### 任务1: 降低高复杂度函数

**目标**: 将所有函数复杂度降至15以下

**示例：重构 cli.py**

```python
# ❌ 重构前：单个大函数，复杂度32
def compile_project(args):
    if args.command == 'build':
        # ... 50行构建逻辑
    elif args.command == 'run':
        # ... 50行运行逻辑
    elif args.command == 'test':
        # ... 30行测试逻辑
    elif args.command == 'clean':
        # ... 20行清理逻辑
    # ... 更多分支

# ✅ 重构后：使用命令模式，每个函数<10复杂度
class CommandHandler(ABC):
    @abstractmethod
    def execute(self, args): ...

class BuildCommand(CommandHandler):
    def execute(self, args):
        """执行构建"""
        self._parse_config(args)
        self._compile_sources()
        self._link_output()

class RunCommand(CommandHandler):
    def execute(self, args):
        """执行运行"""
        self._build_if_needed(args)
        self._execute_binary()

# 命令分发器（复杂度~3）
COMMAND_HANDLERS = {
    'build': BuildCommand(),
    'run': RunCommand(),
    'test': TestCommand(),
    'clean': CleanCommand(),
}

def compile_project(args):
    handler = COMMAND_HANDLERS.get(args.command)
    if not handler:
        raise ValueError(f"未知命令: {args.command}")
    return handler.execute(args)
```

#### 任务2: 拆分过长函数

**模式：提取方法**

```python
# ❌ 重构前：170行的函数
def run_codegen(self, source_path, output_path, options):
    # 1. 参数验证 (20行)
    # 2. 词法分析 (30行)
    # 3. 语法分析 (40行)
    # 4. 语义分析 (35行)
    # 5. IR生成 (25行)
    # 6. 代码生成 (20行)
    
# ✅ 重构后：主协调器 + 子任务
def run_codegen(self, source_path, output_path, options):
    """编译流水线入口"""
    config = self._validate_and_parse_options(source_path, output_path, options)
    tokens = self._tokenize_source(config.source_path)
    ast = self._parse_tokens(tokens)
    self._semantic_check(ast)
    ir = self._generate_ir(ast)
    code = self._emit_code(ir, config.target_lang)
    self._write_output(code, config.output_path)

def _validate_and_parse_options(self, source_path, output_path, options):
    """参数验证和配置构建"""
    # 20行验证逻辑
    return CompileConfig(...)

def _tokenize_source(self, source_path):
    """词法分析阶段"""
    # 30行词法分析
    return tokens

# ... 其他子方法
```

#### 任务3: 补充文档字符串

**模板：**

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """简短描述函数功能
    
    详细说明（如果需要）：
    - 要点1
    - 要点2
    
    Args:
        param1: 参数1的说明
        param2: 参数2的说明
        
    Returns:
        返回值的说明
        
    Raises:
        ErrorType: 什么情况下抛出此错误
        
    Example:
        >>> result = function_name(value1, value2)
        >>> print(result)
        expected_output
        
    Note:
        注意事项、性能提示等
    """
```

**批量添加脚本：**

```bash
# 查找所有缺少docstring的公共函数
grep -rn "def [a-z_]*(" src/ --include="*.py" | \
  grep -v "__" | \
  while read line; do
    func_name=$(echo $line | grep -oP "def \K[a-z_]+")
    file=$(echo $line | cut -d: -f1)
    line_num=$(echo $line | cut -d: -f2)
    echo "$file:$line_num - $func_name"
  done > missing_docs.txt
```

---

### Phase 2: 中期改进（2-4周）

#### 1. 建立测试体系

**优先级排序：**
1. 核心Parser（最高优先级）
2. TypeChecker
3. Lexer
4. CodeGenerator

**测试模板：**

```python
import pytest
from zhpp.parser import Parser, Lexer

class TestLexer:
    """词法分析器测试套件"""
    
    def test_integer_literal(self):
        """测试整数字面量识别"""
        tokens = Lexer("整数型 x = 42").tokenize()
        assert tokens[0].type == TokenType.INT
        assert tokens[3].value == "42"
    
    def test_chinese_keywords(self):
        """测试中文关键字识别"""
        tokens = Lexer("如果 (x > 0)").tokenize()
        assert tokens[0].type == TokenType.IF


class TestParserErrorRecovery:
    """解析器错误恢复测试"""
    
    def test_missing_semicolon(self):
        """测试缺失分号的恢复能力"""
        code = """
        整数型 x = 10
        整数型 y = 20  // 缺少分号
        整数型 z = 30
        """
        parser = Parser(Lexer(code).tokenize())
        ast = parser.parse()
        
        # 应该成功解析所有声明
        assert len(ast.declarations) == 3
        assert parser.has_errors()  # 但记录了错误
    
    def test_unbalanced_braces(self):
        """测试不平衡括号的恢复"""
        code = "整数型 主函数() { 如果 (x { 打印(x)"
        parser = Parser(Lexer(code).tokenize())
        ast = parser.parse()
        
        # 应该优雅处理，不崩溃
        assert ast is not None
        assert parser.has_errors()


class TestTypeChecker:
    """类型检查器测试"""
    
    def test_numeric_compatibility(self):
        """测试数值类型兼容性"""
        tc = TypeChecker()
        int_type = tc.get_type("整数型")
        float_type = tc.get_type("浮点型")
        
        assert int_type.can_cast_to(float_type) == True
        assert float_type.can_cast_to(int_type) == True  # 有警告但合法
    
    def test_pointer_arithmetic_error(self):
        """测试指针算术错误检测"""
        tc = TypeChecker()
        ptr_type = tc.create_pointer_type(tc.get_type("整数型"))
        
        result = tc.check_binary_op(
            line=1,
            op="+",
            left_type=ptr_type,
            right_type=ptr_type
        )
        # 指针+指针应该报错
        assert result is None
        assert tc.has_errors()
```

#### 2. 引入类型注解

**分步实施计划：**

**Week 1-2**: 公共API
```python
# 为所有对外暴露的接口添加类型注解
def parse(source: str) -> Tuple[ProgramNode, List[Error]]:
    """解析源代码为AST"""
    ...

def generate_code(ast: ProgramNode, target: str = 'c') -> str:
    """从AST生成目标代码"""
    ...
```

**Week 3-4**: 内部实现
```python
# 为内部方法添加完整注解
class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.pos: int = 0
    
    def parse_expression(self) -> ASTNode:
        """解析表达式 -> AST节点"""
        ...
```

---

### Phase 3: 长期建设（持续进行）

#### 1. CI/CD自动化

**`.github/workflows/quality.yml`:**
```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: pip install -e ".[dev]"
      
      - name: Quality check
        run: python scripts/quality_check.py src --json > report.json
      
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: quality-report
          path: report.json
      
      - name: Check threshold
        run: |
          SCORE=$(jq '.score' report.json)
          if [ "$SCORE" -lt 60 ]; then
            echo "::warning::Quality score $SCORE below threshold 60"
            exit 1
          fi
```

#### 2. 代码审查规范

**PR模板：**
```markdown
## 变更概述
简要描述本次变更的内容和目的

## 变更类型
- [ ] Bug修复
- [ ] 新功能
- [ ] 重构
- [ ] 文档更新

## 测试情况
- [ ] 新增单元测试
- [ ] 测试通过
- [ ] 覆盖率未下降

## 质量检查
- [ ] 代码通过 ruff check
- [ ] 代码通过 black --check  
- [ ] 函数长度 < 30行
- [ ] 圈复杂度 < 10
- [ ] 有完整的docstring

## 影响范围
列出可能受影响的模块和功能
```

---

## 📈 进度跟踪表

### Week 1 目标

| 任务 | 负责人 | 状态 | 完成日期 |
|------|--------|------|----------|
| 重构 cli.py（复杂度32→<15） | TBD | ⬜ | |
| 重构 ir/c_backend.py（36→<20） | TBD | ⬜ | |
| 拆分 cli.py 的 run_codegen（170→<50） | TBD | ⬜ | |
| 补充核心模块的 docstring（100个） | TBD | ⬜ | |
| 创建基础测试用例（20个） | TBD | ⬜ | |

### 成功标准

**Week 1 结束时达到：**
- ✅ 无复杂度>20的函数
- ✅ 无超过80行的函数
- ✅ 公共API 100%有文档字符串
- ✅ 至少20个核心单元测试
- ✅ 质量评分提升至65+

---

## 🆘 遇到困难？

### 常见问题FAQ

**Q: 重构会不会引入新Bug？**
A: 
1. 先写测试再重构（TDD）
2. 小步提交，每步都可回退
3. 利用Git分支保护

**Q: 时间不够怎么办？**
A: 
1. 优先处理Top 5高复杂度函数
2. 只为新代码加docstring和类型注解
3. 每天固定1小时技术债务时间

**Q: 如何说服团队配合？**
A: 
1. 展示质量报告数据
2. 说明长期维护成本
3. 从自己的代码开始做起

---

## 📞 获取帮助

- **代码质量问题**: 查看 `CODE_REVIEW_CHECKLIST.md`
- **重构建议**: 参考 `TEAM_TECH_IMPROVEMENT_PLAN.md`
- **工具使用**: 运行 `python scripts/quality_check.py --help`

---

**版本**: v1.0  
**创建日期**: 2026-04-07  
**基于数据**: quality_check.py 扫描结果
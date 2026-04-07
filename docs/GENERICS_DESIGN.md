# 泛型编程系统设计文档

**版本**: 1.0  
**日期**: 2026-04-08  
**作者**: ZHC 开发团队  
**状态**: 设计阶段

---

## 1. 概述

本文档描述 ZhC 编译器的泛型编程系统设计，包括泛型类型、泛型函数、类型约束和单态化实现。

### 1.1 设计目标

- **类型安全**: 编译时检查泛型类型约束
- **性能优化**: 通过单态化实现零开销抽象
- **易用性**: 提供简洁直观的泛型语法
- **可扩展**: 支持用户自定义类型约束

### 1.2 术语定义

- **类型参数**: 泛型定义中的占位符类型（如 `T`）
- **类型实参**: 实例化泛型时提供的具体类型
- **类型约束**: 对类型参数的限制条件
- **单态化**: 将泛型代码展开为具体类型的代码

---

## 2. 语法设计

### 2.1 泛型类型语法

```zhc
// 泛型结构体
泛型类型 列表<类型 T> {
    T 数据[100];
    整数型 长度;
}

// 多类型参数
泛型类型 映射<类型 K, 类型 V> {
    K 键[100];
    V 值[100];
    整数型 数量;
}

// 带默认类型参数
泛型类型 容器<类型 T = 整数型> {
    T 值;
}
```

### 2.2 泛型函数语法

```zhc
// 基本泛型函数
泛型函数 T 最大值<类型 T>(T a, T b) {
    如果 (a > b) {
        返回 a;
    } 否则 {
        返回 b;
    }
}

// 带约束的泛型函数
泛型函数 T 排序<类型 T: 可比较>(T 数组[], 整数型 长度) {
    // 排序实现
}

// 多类型参数
泛型函数 (K, V) 创建对<类型 K, 类型 V>(K 键, V 值) {
    返回 (键, 值);
}
```

### 2.3 类型约束语法

```zhc
// 定义类型约束
约束 可比较 {
    运算符 <(自身, 自身) -> 逻辑型;
    运算符 >(自身, 自身) -> 逻辑型;
    运算符 ==(自身, 自身) -> 逻辑型;
}

约束 可打印 {
    函数 转字符串(自身) -> 字符串型;
}

// 组合约束
约束 可排序: 可比较, 可打印 {
    // 继承多个约束
}
```

### 2.4 泛型实例化

```zhc
// 显式实例化
列表<整数型> 整数列表;
映射<字符串型, 整数型> 字典;

// 类型推导
整数型 m = 最大值(10, 20);  // 推导为 最大值<整数型>
字符串型 s = 最大值("hello", "world");  // 推导为 最大值<字符串型>
```

---

## 3. 类型系统设计

### 3.1 核心类型表示

```python
@dataclass
class TypeParameter:
    """类型参数"""
    name: str                              # 参数名（如 'T'）
    constraints: List[TypeConstraint]      # 约束列表
    default: Optional[Type] = None         # 默认类型
    variance: Variance = Variance.INVARIANT # 变性（协变/逆变/不变）


@dataclass
class GenericType(Type):
    """泛型类型"""
    name: str                              # 类型名
    type_params: List[TypeParameter]       # 类型参数列表
    instantiations: Dict[tuple, Type]      # 实例化缓存
    definition: Optional[ASTNode] = None   # 类型定义AST


@dataclass
class GenericFunction:
    """泛型函数"""
    name: str
    type_params: List[TypeParameter]       # 类型参数
    params: List[Parameter]                # 函数参数
    return_type: Type                      # 返回类型
    instantiations: Dict[tuple, Function]  # 实例化缓存
    body: Optional[ASTNode] = None         # 函数体AST
```

### 3.2 类型约束系统

```python
@dataclass
class TypeConstraint:
    """类型约束"""
    name: str                              # 约束名
    required_methods: List[MethodSignature] # 要求的方法
    required_operators: List[OperatorSignature] # 要求的运算符
    super_constraints: List[TypeConstraint] = None  # 父约束


@dataclass
class MethodSignature:
    """方法签名"""
    name: str
    params: List[Type]
    return_type: Type


@dataclass
class OperatorSignature:
    """运算符签名"""
    operator: str
    left_type: Type  # '自身' 表示类型参数
    right_type: Type
    return_type: Type
```

### 3.3 类型推导算法

使用 **Hindley-Milner 类型推导** 算法：

1. **类型变量生成**: 为每个未知类型生成唯一类型变量
2. **约束收集**: 遍历AST收集类型约束
3. **合一求解**: 解约束方程组
4. **泛化**: 识别泛型类型参数

```python
class TypeInferencer:
    """类型推导器"""
    
    def infer_generic_type_args(
        self, 
        func: GenericFunction,
        call_args: List[Type]
    ) -> List[Type]:
        """推导泛型函数的类型实参"""
        
        # Step 1: 生成类型变量
        type_vars = {
            param.name: TypeVariable(param.name)
            for param in func.type_params
        }
        
        # Step 2: 收集约束
        constraints = []
        for param, arg_type in zip(func.params, call_args):
            param_type = self._substitute_type_vars(
                param.type, type_vars
            )
            constraints.append((param_type, arg_type))
        
        # Step 3: 合一求解
        substitution = self._unify(constraints)
        
        # Step 4: 提取类型实参
        type_args = [
            substitution.get(param.name, param.default)
            for param in func.type_params
        ]
        
        return type_args
```

---

## 4. 语义分析

### 4.1 泛型类型检查

```python
class GenericTypeChecker:
    """泛型类型检查器"""
    
    def check_generic_instantiation(
        self,
        generic_type: GenericType,
        type_args: List[Type]
    ) -> Type:
        """检查泛型实例化"""
        
        # 1. 检查参数数量
        if len(type_args) != len(generic_type.type_params):
            raise TypeError(
                f"泛型类型 {generic_type.name} 需要 "
                f"{len(generic_type.type_params)} 个类型参数，"
                f"但提供了 {len(type_args)} 个"
            )
        
        # 2. 检查类型约束
        for param, arg in zip(generic_type.type_params, type_args):
            if not self._satisfies_constraints(arg, param.constraints):
                raise TypeError(
                    f"类型 {arg} 不满足约束 {param.name}"
                )
        
        # 3. 检查变性
        for param, arg in zip(generic_type.type_params, type_args):
            if not self._check_variance(param, arg):
                raise TypeError(
                    f"类型参数 {param.name} 的变性不匹配"
                )
        
        # 4. 返回实例化类型
        return generic_type.instantiate(type_args)
```

### 4.2 约束检查

```python
def _satisfies_constraints(
    self,
    type: Type,
    constraints: List[TypeConstraint]
) -> bool:
    """检查类型是否满足所有约束"""
    
    for constraint in constraints:
        # 检查方法
        for method in constraint.required_methods:
            if not type.has_method(method.name, method.params, method.return_type):
                return False
        
        # 检查运算符
        for op in constraint.required_operators:
            if not type.has_operator(op.operator, op.return_type):
                return False
        
        # 检查父约束
        if constraint.super_constraints:
            if not self._satisfies_constraints(type, constraint.super_constraints):
                return False
    
    return True
```

---

## 5. 代码生成（单态化）

### 5.1 单态化策略

**策略**: 编译时实例化（类似 C++ 模板）

```python
class Monomorphizer:
    """单态化器"""
    
    def monomorphize_generic_function(
        self,
        func: GenericFunction,
        type_args: List[Type]
    ) -> Function:
        """单态化泛型函数"""
        
        # 1. 检查缓存
        cache_key = tuple(type_args)
        if cache_key in func.instantiations:
            return func.instantiations[cache_key]
        
        # 2. 创建类型映射
        type_map = {
            param.name: arg
            for param, arg in zip(func.type_params, type_args)
        }
        
        # 3. 克隆函数体
        specialized_body = self._clone_and_substitute(
            func.body, type_map
        )
        
        # 4. 创建特化函数
        specialized_func = Function(
            name=self._mangled_name(func.name, type_args),
            params=self._substitute_params(func.params, type_map),
            return_type=self._substitute_type(func.return_type, type_map),
            body=specialized_body
        )
        
        # 5. 缓存
        func.instantiations[cache_key] = specialized_func
        
        return specialized_func
    
    def _mangled_name(self, name: str, type_args: List[Type]) -> str:
        """生成名称修饰"""
        # 例如: 最大值<整数型> -> _Z7最大值IiE
        type_suffix = "_".join(str(arg) for arg in type_args)
        return f"{name}__{type_suffix}"
```

### 5.2 代码展开示例

**泛型代码**:
```zhc
泛型函数 T 最大值<类型 T>(T a, T b) {
    如果 (a > b) {
        返回 a;
    } 否则 {
        返回 b;
    }
}

整数型 x = 最大值(10, 20);
```

**展开后**:
```zhc
函数 整数型 最大值__整数型(整数型 a, 整数型 b) {
    如果 (a > b) {
        返回 a;
    } 否则 {
        返回 b;
    }
}

整数型 x = 最大值__整数型(10, 20);
```

---

## 6. 实现计划

### 6.1 Phase 1: 核心类型系统（Day 1）

**任务**:
- [ ] 实现 `TypeParameter` 类
- [ ] 实现 `GenericType` 类
- [ ] 实现 `GenericFunction` 类
- [ ] 实现 `TypeConstraint` 类
- [ ] 编写单元测试

**产出物**:
- `src/semantic/generics.py` - 泛型类型系统
- `tests/test_generics_types.py` - 类型系统测试

### 6.2 Phase 2: 语法解析（Day 2）

**任务**:
- [ ] 扩展词法分析器（新增关键字：泛型类型、泛型函数、约束）
- [ ] 扩展语法分析器（解析泛型声明）
- [ ] 实现 AST 节点
- [ ] 编写解析测试

**产出物**:
- `src/lexer/generic_lexer.py` - 词法扩展
- `src/parser/generic_parser.py` - 语法扩展
- `tests/test_generics_parsing.py` - 解析测试

### 6.3 Phase 3: 语义分析（Day 3）

**任务**:
- [ ] 实现类型推导算法
- [ ] 实现约束检查
- [ ] 实现泛型实例化
- [ ] 编写语义测试

**产出物**:
- `src/semantic/generic_analyzer.py` - 语义分析
- `tests/test_generics_semantic.py` - 语义测试

### 6.4 Phase 4: 代码生成（Day 4）

**任务**:
- [ ] 实现单态化器
- [ ] 实现名称修饰
- [ ] 实现代码展开
- [ ] 性能测试

**产出物**:
- `src/codegen/generic_codegen.py` - 代码生成
- `tests/test_generics_codegen.py` - 代码生成测试
- `examples/generics.zhc` - 示例代码

---

## 7. 测试策略

### 7.1 单元测试

```python
def test_generic_type_instantiation():
    """测试泛型类型实例化"""
    # 创建泛型类型 列表<T>
    list_type = GenericType(
        name="列表",
        type_params=[TypeParameter(name="T", constraints=[])]
    )
    
    # 实例化为 列表<整数型>
    int_list = list_type.instantiate([IntType()])
    
    assert int_list.name == "列表<整数型>"
    assert int_list.type_args == [IntType()]


def test_generic_function_inference():
    """测试泛型函数类型推导"""
    # 创建泛型函数 最大值<T>(T, T) -> T
    max_func = GenericFunction(
        name="最大值",
        type_params=[TypeParameter(name="T", constraints=[Comparable()])],
        params=[
            Parameter(name="a", type=TypeVariable("T")),
            Parameter(name="b", type=TypeVariable("T"))
        ],
        return_type=TypeVariable("T")
    )
    
    # 推导类型实参
    inferencer = TypeInferencer()
    type_args = inferencer.infer_generic_type_args(
        max_func,
        [IntType(), IntType()]
    )
    
    assert type_args == [IntType()]


def test_constraint_checking():
    """测试约束检查"""
    # 定义约束 可比较
    comparable = TypeConstraint(
        name="可比较",
        required_operators=[
            OperatorSignature(operator="<", return_type=BoolType())
        ]
    )
    
    # 检查整数型满足约束
    checker = GenericTypeChecker()
    assert checker._satisfies_constraints(IntType(), [comparable])
    
    # 检查空型不满足约束
    assert not checker._satisfies_constraints(VoidType(), [comparable])
```

### 7.2 集成测试

```zhc
// tests/integration/test_generics.zhc

// 测试泛型类型
泛型类型 盒子<类型 T> {
    T 值;
}

函数 测试盒子() {
    盒子<整数型> 整数盒子;
    整数盒子.值 = 42;
    
    盒子<字符串型> 字符串盒子;
    字符串盒子.值 = "hello";
}

// 测试泛型函数
泛型函数 T 交换<类型 T>(T a, T b) -> (T, T) {
    返回 (b, a);
}

函数 测试交换() {
    (整数型, 整数型) 对 = 交换(10, 20);
    断言(对.第一 == 20);
    断言(对.第二 == 10);
}

// 测试类型约束
约束 可加 {
    运算符 +(自身, 自身) -> 自身;
}

泛型函数 T 求和<类型 T: 可加>(T 数组[], 整数型 长度) -> T {
    T 总和 = 0;
    对于 (整数型 i = 0; i < 长度; i++) {
        总和 = 总和 + 数组[i];
    }
    返回 总和;
}

函数 测试求和() {
    整数型 数组[] = {1, 2, 3, 4, 5};
    整数型 总和 = 求和(数组, 5);
    断言(总和 == 15);
}
```

---

## 8. 性能优化

### 8.1 实例化缓存

```python
class GenericType:
    def instantiate(self, type_args: List[Type]) -> Type:
        # 使用缓存避免重复实例化
        cache_key = tuple(type_args)
        if cache_key not in self.instantiations:
            self.instantiations[cache_key] = self._create_instance(type_args)
        return self.instantiations[cache_key]
```

### 8.2 延迟实例化

只在真正使用时才实例化泛型：

```python
class Monomorphizer:
    def __init__(self):
        self.pending_instantiations = []
    
    def schedule_instantiation(self, func: GenericFunction, type_args: List[Type]):
        """延迟实例化"""
        self.pending_instantiations.append((func, type_args))
    
    def flush(self):
        """批量实例化"""
        for func, type_args in self.pending_instantiations:
            self.monomorphize_generic_function(func, type_args)
        self.pending_instantiations.clear()
```

### 8.3 代码膨胀控制

```python
class Monomorphizer:
    def __init__(self, max_instances: int = 100):
        self.max_instances = max_instances
        self.instance_count = {}
    
    def should_inline(self, func: GenericFunction, type_args: List[Type]) -> bool:
        """判断是否应该实例化"""
        key = func.name
        count = self.instance_count.get(key, 0)
        
        if count >= self.max_instances:
            # 超过限制，生成警告
            logger.warning(
                f"泛型函数 {func.name} 实例化次数过多 ({count})，"
                f"可能导致代码膨胀"
            )
            return False
        
        self.instance_count[key] = count + 1
        return True
```

---

## 9. 错误处理

### 9.1 错误类型

```python
class GenericError(CompilerError):
    """泛型相关错误"""
    pass


class TypeParameterMismatchError(GenericError):
    """类型参数数量不匹配"""
    pass


class ConstraintViolationError(GenericError):
    """约束违反错误"""
    pass


class TypeInferenceError(GenericError):
    """类型推导失败"""
    pass
```

### 9.2 错误示例

```zhc
// 错误示例 1: 类型参数数量不匹配
泛型类型 对<类型 K, 类型 V> {
    K 键;
    V 值;
}

对<整数型> 错误对;  // 错误: 需要 2 个类型参数

// 错误示例 2: 约束违反
约束 可比较 {
    运算符 <(自身, 自身) -> 逻辑型;
}

泛型函数 T 最大值<类型 T: 可比较>(T a, T b) -> T {
    // ...
}

结构体 点 {
    整数型 x;
    整数型 y;
}

点 p1 = {x: 1, y: 2};
点 p2 = {x: 3, y: 4};
点 最大点 = 最大值(p1, p2);  // 错误: 点 不满足 可比较 约束

// 错误示例 3: 类型推导失败
泛型函数 T 创建<类型 T>() -> T {
    返回 0;  // 错误: 无法推导 T 的类型
}
```

---

## 10. 未来扩展

### 10.1 高级特性

- **高阶类型**: 支持类型构造器作为参数
- **类型族**: 关联类型
- **存在类型**: 隐藏具体类型

### 10.2 性能优化

- **增量单态化**: 只重新实例化修改的部分
- **并行实例化**: 多线程实例化泛型
- **缓存持久化**: 将实例化结果保存到磁盘

---

## 11. 参考资料

1. **《Types and Programming Languages》** - Benjamin C. Pierce
   - 第 22-26 章: 类型参数和多态

2. **《Advanced Topics in Types and Programming Languages》**
   - 第 1 章: 类型约束

3. **Rust 泛型设计**
   - Trait 系统
   - 单态化实现

4. **C++ 模板设计**
   - 模板实例化
   - SFINAE

---

**创建日期**: 2026-04-08  
**最后更新**: 2026-04-08  
**维护者**: ZHC 开发团队
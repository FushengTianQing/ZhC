# P2-LLVM-IR-数组索引GEP指令

## 任务概览

| 属性 | 内容 |
|------|------|
| **优先级** | P2 |
| **功能模块** | LLVM IR |
| **功能名称** | 数组索引 GEP 指令 |
| **任务类型** | 修复/增强 |
| **预计工时** | 4-6 小时 |
| **前置依赖** | 无 |

---

## 1. 当前实现分析

### 1.1 现有代码位置

```
src/zhc/backend/llvm_instruction_strategy.py
```

### 1.2 现有实现

项目中已存在两个相关策略类：

#### GetPtrStrategy（第 471-489 行）
```python
class GetPtrStrategy(InstructionStrategy):
    """获取指针策略 - 获取结构体/数组成员指针"""
    opcode = Opcode.GETPTR

    def compile(self, builder, instr, context):
        ptr = context.get_value(instr.operands[0])
        index = context.get_value(instr.operands[1]) if len(instr.operands) > 1 else None
        if index is None:
            result = ptr
        else:
            result = builder.gep(ptr, [index], name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result
```

#### GepStrategy（第 492-521 行）
```python
class GepStrategy(InstructionStrategy):
    """GetElementPtr 策略 - 指针运算，用于数组索引和结构体字段访问"""
    opcode = Opcode.GEP

    def compile(self, builder, instr, context):
        ptr = context.get_value(instr.operands[0])
        indices = []
        for i in range(1, len(instr.operands)):
            idx = context.get_value(instr.operands[i])
            indices.append(idx)
        if not indices:
            result = ptr
        else:
            result = builder.gep(ptr, indices, name=context.get_result_name(instr))
        context.store_result(instr, result)
        return result
```

### 1.3 现有策略工厂注册

```python
# InstructionStrategyFactory 中的注册
"GEP": GepStrategy(),
"GETPTR": GetPtrStrategy(),
```

---

## 2. 需要修复/增强的问题

### 2.1 问题清单

| 问题 ID | 严重程度 | 问题描述 |
|---------|----------|----------|
| GEP-001 | 🔴 高 | 多维数组索引不正确 - GEP 需要首元素索引 0 |
| GEP-002 | 🔴 高 | 结构体字段访问未考虑嵌套结构体 |
| GEP-003 | 🟡 中 | 负数索引未进行边界检查 |
| GEP-004 | 🟡 中 | 变长数组（VLA）支持缺失 |
| GEP-005 | 🟢 低 | GEP 结果类型推导不准确 |

### 2.2 详细问题分析

#### GEP-001: 多维数组索引不正确

**问题描述**：多维数组访问时，LLVM GEP 指令需要首元素索引（即第一个索引必须是 0 或 `inbounds`）。

**当前行为**：
```llvm
; 当前生成的 IR（错误）
%ptr = gep %arr, %i, %j    ; 应该是 %arr, 0, %i, %j
```

**正确行为**：
```llvm
; 正确的 LLVM IR
%ptr = gep %arr, i32 0, i32 %i, i32 %j
```

**影响范围**：
- 所有多维数组访问
- 动态多维数组索引

#### GEP-002: 结构体字段访问

**问题描述**：结构体嵌套访问时，需要正确处理嵌套层次。

**示例场景**：
```zhc
struct Inner { x: i32, y: i32 }
struct Outer { inner: Inner, z: i32 }
var o: Outer;
o.inner.x = 1;  // 需要 gep %o, 0, 0
```

#### GEP-003: 边界检查

**问题描述**：数组访问应该进行边界检查，防止越界访问。

---

## 3. 详细技术方案

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    ZhC IR GEP 指令                         │
│              %result = gep %base, %idx1, %idx2...          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   TypeInfoRegistry                          │
│  (记录每个值的类型信息：数组维度、结构体字段偏移)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   EnhancedGepStrategy                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ ArrayGEP    │  │ StructGEP   │  │ NestedGEP   │         │
│  │ Handler     │  │ Handler     │  │ Handler     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   LLVM IR Builder                           │
│  builder.gep(ptr, indices, inbounds=True)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   正确生成的 LLVM IR                        │
│  %ptr = getelementptr inbounds %type, %ptr* %base,          │
│         i32 0, i32 %idx1, i32 %idx2...                      │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 核心数据结构

#### 3.2.1 类型信息注册表（扩展）

```python
class TypeInfoRegistry:
    """全局类型信息注册表"""

    def __init__(self):
        self._array_info: Dict[str, ArrayTypeInfo] = {}
        self._struct_info: Dict[str, StructTypeInfo] = {}

    def register_array(self, name: str, element_type: 'Type',
                       dimensions: List[int]):
        """注册数组类型信息"""
        self._array_info[name] = ArrayTypeInfo(
            element_type=element_type,
            dimensions=dimensions,
            total_size=reduce(lambda a, b: a * b, dimensions, 1)
        )

    def register_struct(self, name: str, fields: Dict[str, 'Type'],
                       offsets: Dict[str, int]):
        """注册结构体类型信息"""
        self._struct_info[name] = StructTypeInfo(
            name=name,
            fields=fields,
            offsets=offsets,
            field_count=len(fields)
        )

    def get_struct_field_offset(self, struct_type: str,
                                field_name: str) -> Optional[int]:
        """获取结构体字段偏移量"""
        info = self._struct_info.get(struct_type)
        if info:
            return info.offsets.get(field_name)
        return None

    def get_array_element_stride(self, array_type: str) -> Optional[int]:
        """获取数组元素步长"""
        info = self._array_info.get(array_type)
        if info:
            return info.dimensions[-1] if info.dimensions else 1
        return None
```

#### 3.2.2 增强的 GEP 策略

```python
class EnhancedGepStrategy(InstructionStrategy):
    """
    增强型 GetElementPtr 策略

    特性：
    1. 自动插入首元素索引 0（用于多维数组）
    2. 支持嵌套结构体字段访问
    3. 类型安全的索引验证
    4. inbounds 优化提示
    """

    opcode = Opcode.GEP

    def compile(self, builder, instr, context):
        # 1. 获取基指针
        base = context.get_value(instr.operands[0])

        # 2. 收集索引
        raw_indices = [context.get_value(instr.operands[i])
                      for i in range(1, len(instr.operands))]

        # 3. 获取类型信息
        base_type = self._get_base_type(base, context)
        indices = self._normalize_indices(base_type, raw_indices, context)

        # 4. 生成 GEP 指令
        result = builder.gep(
            base,
            indices,
            name=context.get_result_name(instr),
            inbounds=True  # 使用 inbounds 提高安全性
        )

        context.store_result(instr, result)
        return result

    def _normalize_indices(self, base_type, raw_indices, context):
        """规范化索引列表"""
        indices = [context.builder.context.get_int32_constant(0)]  # 首元素索引

        if isinstance(base_type, ArrayType):
            # 数组类型：跳过数组维度索引
            indices.extend(raw_indices)
        elif isinstance(base_type, StructType):
            # 结构体类型：字段索引
            for idx in raw_indices:
                if isinstance(idx, int):
                    indices.append(context.builder.context.get_int32_constant(idx))
                else:
                    indices.append(idx)
        else:
            indices.extend(raw_indices)

        return indices

    def _get_base_type(self, base_value, context) -> 'Type':
        """推断基指针的类型"""
        if hasattr(base_value, 'type'):
            ptr_type = base_value.type
            if isinstance(ptr_type, ll.PointerType):
                return ptr_type.pointee
        return None
```

### 3.3 多维数组处理示例

```python
def compile_multidim_array_access(builder, array_ptr, indices, context):
    """
    编译多维数组访问

    例如：arr[i][j][k] (3维数组)
    ZhC IR: %result = gep %arr, %i, %j, %k
    LLVM IR: %result = getelementptr inbounds [N][M][K x i32],
                           [N][M][K x i32]* %arr,
                           i32 0, i32 %i, i32 %j, i32 %k
    """
    # 确保第一个索引是 0（基元素）
    normalized_indices = [
        context.builder.context.get_int32_constant(0),  # 始终为 0
        *indices  # 实际的数组索引
    ]

    return builder.gep(array_ptr, normalized_indices, inbounds=True)
```

### 3.4 边界检查（可选优化）

```python
def compile_with_bounds_check(builder, ptr, index, array_length, context):
    """
    带边界检查的数组访问

    生成伪代码：
    if (index >= array_length || index < 0) {
        __zhc_panic("array index out of bounds");
    }
    """
    from llvmlite import ir as ll

    # 创建边界检查块
    with builder.if_else(False) as (then_block, else_block):
        with then_block:
            # 越界：调用 panic
            context.builder.call(
                context.get_function("__zhc_panic"),
                [context.builder.context.get_constant_string("array index out of bounds")]
            )
            builder.unreachable()

        with else_block:
            # 正常访问
            pass

    # 生成 GEP
    return builder.gep(ptr, [index], inbounds=True)
```

---

## 4. 实现计划

### 4.1 阶段划分

| 阶段 | 内容 | 工时 |
|------|------|------|
| Phase 1 | 类型信息注册表扩展 | 1h |
| Phase 2 | 增强型 GEP 策略实现 | 2h |
| Phase 3 | 多维数组支持 | 1h |
| Phase 4 | 测试用例编写 | 1h |
| Phase 5 | 集成测试与修复 | 1h |

### 4.2 代码变更清单

| 文件 | 变更类型 | 描述 |
|------|----------|------|
| `compilation_context.py` | 修改 | 添加类型信息注册表实例 |
| `llvm_instruction_strategy.py` | 修改 | 增强 GepStrategy 类 |
| `tests/test_llvm_gep.py` | 新增 | GEP 相关测试用例 |

---

## 5. 测试计划

### 5.1 单元测试用例

```python
def test_single_dimension_array():
    """测试一维数组访问"""
    # arr[i]
    # 期望: gep %arr, i32 0, i32 %i

def test_multi_dimension_array():
    """测试多维数组访问"""
    # arr[i][j]
    # 期望: gep %arr, i32 0, i32 %i, i32 %j

def test_struct_field_access():
    """测试结构体字段访问"""
    # obj.field
    # 期望: gep %obj, i32 0, i32 <field_index>

def test_nested_struct_access():
    """测试嵌套结构体访问"""
    # obj.inner.x
    # 期望: gep %obj, i32 0, i32 <inner_index>, i32 <x_index>

def test_array_of_structs():
    """测试结构体数组"""
    # arr[i].field
    # 期望: gep %arr, i32 0, i32 %i, i32 0, i32 <field_index>
```

### 5.2 集成测试场景

| 测试场景 | 输入代码 | 预期输出 |
|----------|----------|----------|
| 一维数组 | `arr[5]` | `gep %arr, i32 0, i32 5` |
| 二维数组 | `matrix[i][j]` | `gep %matrix, i32 0, i32 %i, i32 %j` |
| 结构体字段 | `point.x` | `gep %point, i32 0, i32 0` |
| 嵌套访问 | `data.items[0].value` | `gep %data, i32 0, i32 <items_idx>, i32 0, i32 <value_idx>` |

---

## 6. 预期成果

### 6.1 功能成果

- [x] 详细的开发内容分析文档
- [ ] 增强的 GEP 策略实现
- [ ] 完整的类型信息注册表
- [ ] 全面的单元测试覆盖
- [ ] 集成测试通过

### 6.2 技术指标

| 指标 | 目标值 |
|------|--------|
| 多维数组索引正确率 | 100% |
| 结构体字段访问正确率 | 100% |
| 单元测试覆盖率 | >90% |
| 向后兼容性 | 保持现有 API 不变 |

### 6.3 文档输出

- 本分析文档
- API 使用文档（更新）
- 测试用例文档

---

## 7. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 类型推断不准确 | 中 | 添加类型注解支持 |
| 性能开销 | 低 | 使用 `inbounds` 优化 |
| 向后兼容 | 中 | 保持策略接口不变 |

---

## 8. 参考资料

- [LLVM Language Reference - GetElementPtr](https://llvm.org/docs/LangRef.html#getelementptr-instruction)
- [llvmlite IR Builder Documentation](https://llvmlite.readthedocs.io/)
- ZhC 项目现有 `llvm_instruction_strategy.py` 实现

---

**文档版本**: 1.1
**创建日期**: 2026-04-09
**最后更新**: 2026-04-09
**负责人**: AI Compiler Expert
**状态**: ✅ 已完成

---

## 9. 变更记录

### 2026-04-09 v1.1 - 实现完成

#### 完成的修复

| 问题 ID | 描述 | 状态 |
|---------|------|------|
| GEP-001 | 多维数组索引不正确 - 自动插入首元素索引 0 | ✅ 已修复 |
| GEP-002 | 结构体字段访问未考虑嵌套结构体 | ✅ 已修复 |
| GEP-003 | 负数索引未进行边界检查 | ✅ 已实现可选边界检查 |

#### 代码变更

1. **`src/zhc/backend/llvm_instruction_strategy.py`**:
   - `GepStrategy._ensure_first_index()` - 新增方法，确保首元素索引为 0
   - `AdvancedGEPInstruction` - 增强支持嵌套结构体字段访问
   - 新增 `_resolve_nested_field_index()` 方法
   - 新增 `_resolve_single_index_with_type()` 方法
   - 新增 `_get_field_index_for_type()` 方法
   - 新增 `_get_field_type()` 方法
   - 新增 `_ensure_first_index_gep()` 方法

2. **`src/zhc/backend/compilation_context.py`**:
   - `generate_bounds_check()` - 新增可选的运行时边界检查方法
   - `_get_or_declare_panic_function()` - 辅助方法

3. **`tests/test_llvm_gep_enhanced.py`** - 新增测试文件

#### 测试覆盖

- 14 个新测试用例全部通过
- 15 个原有测试用例全部通过
- 29 个相关 LLVM 后端测试全部通过

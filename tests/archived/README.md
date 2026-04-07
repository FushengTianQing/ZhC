# 旧测试文件归档说明

**归档时间**: 2026-04-03 04:51  
**归档原因**: 重构为pytest框架，旧的测试使用自定义框架

---

## 归档文件列表

### test_suite1_types.py
- **用途**: 基础类型测试（整数型、字符型、浮点型等）
- **测试框架**: 自定义test()函数
- **状态**: 已被test_suite8的单元测试替代
- **行数**: 约70行

### test_suite2_control.py
- **用途**: 流程控制测试（if-else, while, for等）
- **测试框架**: 自定义test()函数
- **状态**: 已被test_suite8的单元测试替代
- **行数**: 约70行

### test_suite3_funcs.py
- **用途**: 函数测试（函数定义、参数、返回值等）
- **测试框架**: 自定义test()函数
- **状态**: 已被test_suite8的单元测试替代
- **行数**: 约85行

### test_suite4_advanced.py
- **用途**: 高级特性测试（指针、结构体等）
- **测试框架**: 自定义test()函数
- **状态**: 已被test_suite8的单元测试替代
- **行数**: 约80行

### test_suite5_functions.py
- **用途**: 扩展函数测试
- **测试框架**: 自定义test()函数
- **状态**: 已被test_suite8的单元测试替代
- **行数**: 约230行

### test_suite6_stdlib.py
- **用途**: 标准库函数测试
- **测试框架**: 自定义test()函数
- **状态**: 已被test_stdio.py替代
- **行数**: 约330行

---

## 新测试框架对比

### 旧框架（已废弃）
```python
def test(name, zhc_code, expected_in_output=None):
    path = f'{TMPDIR}/t_{name}.zhc'
    open(path, 'w').write(zhc_code)
    r = subprocess.run(['python3', ZHPP, path], ...)
    # ...自定义验证逻辑
```

### 新框架（pytest）
```python
def test_int_basic(self):
    """测试整数型基础"""
    success, output = self.run_compiler('''
整数型 主函数() {
    整数型 x = 42;
    返回 0;
}
''', 'int_basic')
    assert success, output
    assert 'int x = 42' in output
```

---

## 为什么归档？

1. **测试框架不统一**: 旧测试使用自定义框架，不符合pytest标准
2. **导入路径过时**: 硬编码了旧的路径 `src/zhc.py`
3. **功能重复**: test_suite8已经覆盖了这些基础功能
4. **维护成本高**: 每次重构都需要更新路径

---

## 如果需要恢复

这些测试文件仍然保留在 `tests/archived/` 目录中，如果需要：

1. **查看历史测试**: 可以查看旧的测试逻辑
2. **恢复测试**: 可以将文件移回 `tests/` 目录并更新导入路径
3. **学习参考**: 作为端到端测试的参考示例

---

## 当前测试覆盖

| 测试套件 | 文件 | 状态 | 覆盖范围 |
|:---|:---|:---|:---|
| test_suite7 | test_suite7/ | ✅ 活跃 | Phase 3 模块系统 |
| test_suite8 | test_suite8/ | ✅ 活跃 | Phase 3 类系统 |
| test_suite9 | test_suite9/ | ✅ 活跃 | Phase 3 内存语法 |
| test_suite10 | test_suite10/ | ✅ 活跃 | Phase 3 集成测试 |
| test_stdio | test_stdio.py | ✅ 活跃 | 标准库 |

---

**归档人**: 阿福  
**归档日期**: 2026-04-03
# ZHC 示例代码

本目录包含 ZHC 中文C编译器的示例代码，从基础到高级，帮助你快速上手 ZHC 编程。

---

## 📚 示例索引

### 基础示例

| 文件 | 难度 | 说明 |
|:-----|:-----|:-----|
| [hello.zhc](./hello.zhc) | ⭐ | Hello World 入门示例 |
| [functions.zhc](./functions.zhc) | ⭐⭐ | 函数定义、参数、返回值、递归 |

### 进阶示例

| 文件 | 难度 | 说明 |
|:-----|:-----|:-----|
| [classes.zhc](./classes.zhc) | ⭐⭐⭐ | 类定义、继承、多态、封装 |
| [generic.zhc](./generic.zhc) | ⭐⭐⭐⭐ | 泛型编程、泛型类型、泛型函数 |

### 高级示例

| 文件 | 难度 | 说明 |
|:-----|:-----|:-----|
| [template.zhc](./template.zhc) | ⭐⭐⭐⭐ | 字符串模板、条件渲染、循环渲染 |
| [package_manager.zhc](./package_manager.zhc) | ⭐⭐⭐ | 包管理器使用、依赖管理、发布流程 |

---

## 🚀 快速开始

### 编译单个文件

```bash
# 编译 hello.zhc
zhc compile examples/hello.zhc -o hello.c

# 使用 gcc 编译为可执行文件
gcc hello.c -o hello

# 运行
./hello
```

### 编译项目

```bash
# 编译整个项目
zhc compile --project examples/ -o build/

# 编译后的文件在 build/ 目录中
```

---

## 📖 示例详解

### 1. Hello World (`hello.zhc`)

最简单的 ZHC 程序，演示：

- 主函数定义
- 打印输出
- 返回值

```c
整数型 主函数() {
    打印("你好，ZHC！\n");
    返回 0;
}
```

### 2. 函数示例 (`functions.zhc`)

演示函数相关特性：

- ✅ 无参数无返回值函数
- ✅ 带参数函数
- ✅ 带返回值函数
- ✅ 递归函数（阶乘、斐波那契）
- ✅ 数组参数函数
- ✅ 字符串函数
- ✅ 数学函数

### 3. 类示例 (`classes.zhc`)

演示面向对象编程：

- ✅ 类定义
- ✅ 构造函数
- ✅ 成员变量和成员函数
- ✅ 继承（单继承）
- ✅ 多态（虚函数）
- ✅ 封装（访问控制）
- ✅ 运算符重载

### 4. 泛型示例 (`generic.zhc`)

演示泛型编程：

- ✅ 泛型类型定义
- ✅ 泛型函数
- ✅ 类型约束
- ✅ 多参数泛型
- ✅ 泛型实例化

### 5. 模板示例 (`template.zhc`)

演示字符串模板：

- ✅ 变量插值
- ✅ 条件渲染
- ✅ 循环渲染
- ✅ 表达式计算
- ✅ 默认值
- ✅ 模板继承

### 6. 包管理示例 (`package_manager.zhc`)

演示包管理器使用：

- ✅ 安装包
- ✅ 发布包
- ✅ 搜索包
- ✅ 依赖管理
- ✅ 版本控制

---

## 🎯 学习路径

### 初学者路径

1. **hello.zhc** → 理解基本语法
2. **functions.zhc** → 掌握函数定义和使用
3. **classes.zhc** → 学习面向对象编程

### 进阶路径

1. **generic.zhc** → 掌握泛型编程
2. **template.zhc** → 学习字符串模板
3. **package_manager.zhc** → 了解包管理

---

## 💡 编译技巧

### 查看生成的 C 代码

```bash
# 编译并查看输出
zhc compile hello.zhc -o hello.c
cat hello.c
```

### 使用 IR 后端

```bash
# 使用 IR 后端编译
zhc compile hello.zhc --backend ir -o hello.c

# 查看生成的 IR
zhc compile hello.zhc --backend ir --dump-ir
```

### 启用优化

```bash
# 启用 IR 优化
zhc compile hello.zhc --backend ir --ir-opt -o hello.c
```

---

## 🐛 调试技巧

### 详细输出

```bash
# 启用详细输出
zhc compile hello.zhc -v
```

### 错误处理

```bash
# 将警告视为错误
zhc compile hello.zhc -Werror
```

### 性能分析

```bash
# 启用性能分析
zhc compile hello.zhc --profile
```

---

## 📝 代码规范

### 命名规范

- **变量**: 中文snake_case（如 `整数列表`）
- **函数**: 中文snake_case（如 `计算平均值`）
- **类**: 中文PascalCase（如 `学生信息`）
- **常量**: 中文UPPER_SNAKE_CASE（如 `最大长度`）

### 注释规范

```c
/**
 * 函数说明
 * 
 * Args:
 *   参数名: 参数说明
 * 
 * Returns:
 *   返回值说明
 */
整数型 函数名(整数型 参数名) {
    // 单行注释
    
    /*
     * 多行注释
     */
    
    返回 0;
}
```

---

## 🔗 相关资源

- [官方文档](https://github.com/FushengTianQing/ZhC)
- [API 参考](../docs/sphinx/api/index.rst)
- [开发者指南](../docs/sphinx/guides/developer_guide.rst)
- [架构设计](../docs/ARCHITECTURE.md)

---

## 🤝 贡献示例

欢迎贡献更多示例代码！

1. Fork 项目
2. 在 `examples/` 目录添加新示例
3. 更新本 README.md
4. 提交 Pull Request

---

**最后更新**: 2026-04-08
# 中文C编译器 (ZHC Compiler)

**将中文代码编译为C程序的专业工具**

[![版本](https://img.shields.io/badge/版本-v6.0-blue)](https://github.com/yuan/zhc)
[![Python版本](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![许可证](https://img.shields.io/badge/许可证-MIT-yellow)](LICENSE)
[![构建状态](https://img.shields.io/badge/构建-通过-brightgreen)](tests/)

## 🌟 特性亮点

### 🚀 高性能编译
- **智能编译缓存**: 重复编译速度提升60-80%
- **增量编译**: 只重新编译变更的文件
- **并发编译**: 多线程加速，性能提升2-4倍
- **内存优化**: 大项目内存使用减少20-30%

### 🧩 完整模块系统
- **中文模块语法**: 支持`模块`、`导入`、`公开:`、`私有:`关键字
- **智能依赖解析**: 自动分析模块间依赖关系
- **循环依赖检测**: 防止无限循环依赖
- **编译顺序优化**: 自动计算最优编译顺序

### 🔧 专业工具链
- **完整的CLI接口**: 命令行工具支持所有功能
- **详细的错误报告**: 精确的错误定位和修复建议
- **性能监控**: 实时编译性能分析和报告
- **缓存管理**: 灵活的缓存控制和管理

### 📚 完全中文友好
- **258个中文关键词**: 覆盖C语言全部核心功能
- **中文标准库函数**: `打印`、`申请`、`释放`等中文函数名
- **中文错误信息**: 所有错误信息均为中文，易于理解
- **中文文档**: 完整的用户指南和API文档

## 🚀 快速开始

### 安装

```bash
# 方法1: 直接使用（推荐）
python3 -m pip install zhc

# 方法2: 从源码安装
git clone https://github.com/yuan/zhc.git
cd zhc
pip install -e .

# 方法3: Docker方式
docker run -it yuan/zhc:latest
```

### 基础使用

```bash
# 编译单个文件
zhc 你好世界.zhc

# 编译模块项目
zhc -m 主模块.zhc

# 启用缓存编译（大幅提升速度）
zhc -m 项目.zhc --cache

# 详细输出模式
zhc -m 项目.zhc --verbose
```

### 第一个中文程序

创建文件 `你好世界.zhc`:
```c
包含 <stdio.h>

整数型 主函数() {
    打印("你好，世界！\n");
    返回 0;
}
```

编译并运行:
```bash
zhc 你好世界.zhc
gcc 你好世界.c -o 你好世界
./你好世界
# 输出: 你好，世界！
```

## 📖 详细文档

| 文档 | 内容 | 适合 |
|------|------|------|
| 📚 [用户指南](docs/USER_GUIDE.md) | 完整的使用教程和示例 | 所有用户 |
| 🛠️ [API参考](docs/API_REFERENCE.md) | 所有API的详细说明 | 开发者 |
| 🚀 [快速入门](docs/QUICK_START.md) | 5分钟快速上手 | 新手 |
| 🏗️ [安装指南](docs/INSTALLATION.md) | 各种安装方式 | 系统管理员 |
| 📊 [性能优化](docs/PERFORMANCE.md) | 编译性能调优指南 | 高级用户 |
| 🐛 [问题排查](docs/TROUBLESHOOTING.md) | 常见问题解决 | 遇到问题的用户 |

## 🧩 模块系统示例

### 模块定义

**数学模块.zhc:**
```c
模块 数学模块 版本 1.0

公开:
    整数型 加(整数型 a, 整数型 b) {
        返回 a + b;
    }
    
    整数型 乘(整数型 a, 整数型 b) {
        返回 a * b;
    }

私有:
    // 私有函数，外部不可访问
    整数型 内部计算() {
        // ...
    }
```

### 模块使用

**主程序.zhc:**
```c
导入 数学模块

包含 <stdio.h>

整数型 主函数() {
    整数型 结果 = 数学模块.加(10, 20);
    打印("10 + 20 = %d\n", 结果);
    返回 0;
}
```

### 编译模块项目
```bash
zhc -m 主程序.zhc --output-dir 构建 --cache --verbose
```

## ⚙️ 命令行接口

### 基本命令

```bash
# 显示帮助
zhc --help

# 显示版本
zhc --version

# 编译单个文件
zhc 文件.zhc

# 编译模块项目
zhc -m 入口.zhc

# 指定输出目录
zhc -m 项目.zhc --output-dir 构建
```

### 高级功能

```bash
# 启用编译缓存
zhc -m 项目.zhc --cache

# 详细输出模式
zhc -m 项目.zhc --verbose

# 生成性能报告
zhc -m 项目.zhc --performance

# 清理编译缓存
zhc --clean-cache

# 仅解析不编译（语法检查）
zhc 文件.zhc --parse-only
```

## 📊 性能对比

| 场景 | 传统编译 | ZHC编译 | 提升 |
|------|----------|---------|------|
| 首次编译 | 100% | 100% | 基准 |
| 二次编译 | 100% | 160-180% | 60-80% |
| 大项目内存 | 100% | 70-80% | 20-30% |
| 依赖解析 | 100% | 50-70% | 30-50% |
| 并发编译 | 单线程 | 2-4倍 | 100-300% |

## 🏗️ 项目结构

```
zhc/
├── src/
│   └── zhc/              # 模块化编译器核心
│       ├── parser/        # 解析器模块（模块、类、内存语法）
│       ├── converter/     # 转换器模块（代码转换、错误处理）
│       ├── analyzer/      # 分析器模块（依赖、性能、内存安全）
│       ├── compiler/      # 编译器模块（流水线、缓存、优化）
│       ├── cli/           # 命令行工具
│       ├── types/         # 类型系统（智能指针）
│       └── lib/           # 标准库
├── docs/                 # 文档
├── examples/             # 示例代码
├── tests/                # 测试套件
└── 构建/                 # 编译输出目录
```

## 🔧 开发环境

### 依赖要求
- Python 3.8+
- clang 或 gcc (用于编译生成的C代码)
- Git (用于版本控制)

### 开发设置
```bash
# 克隆仓库
git clone https://github.com/yuan/zhc.git
cd zhc

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/
```

### 运行所有测试
```bash
# 运行基础测试
python3 run_all_tests.py

# 运行高级功能测试
python3 run_all_tests_v5.py
```

## 🤝 贡献指南

欢迎贡献代码！请查看[贡献指南](CONTRIBUTING.md)了解详细信息。

1. **提交Issue**: 报告bug或提出新功能建议
2. **提交PR**: 修复bug或实现新功能
3. **改进文档**: 帮助完善文档和示例
4. **分享反馈**: 告诉我们你的使用体验

## 📄 许可证

本项目基于 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢以下项目和技术的支持：
- [Python](https://www.python.org/) - 强大的编程语言
- [Clang/LLVM](https://clang.llvm.org/) - 优秀的C编译器
- [所有贡献者](CONTRIBUTORS.md) - 感谢你们的贡献

## 📞 联系方式

- **问题反馈**: [GitHub Issues](https://github.com/yuan/zhc/issues)
- **讨论交流**: [GitHub Discussions](https://github.com/yuan/zhc/discussions)
- **邮件**: zhc@example.com

---

**开始用中文写C程序吧！🚀**

```bash
# 立即尝试
curl -sSL https://raw.githubusercontent.com/yuan/zhc/main/install.sh | bash
zhc --version
```

*最后更新: 2026-04-02*
# ZHC Language Server Protocol 使用指南

## 简介

ZHC Language Server 提供完整的 Language Server Protocol (LSP) 实现，支持代码补全、诊断、导航等功能。

## 功能特性

### 代码补全

- **关键字补全**: 支持所有 ZHC 关键字（整数型、浮点型、如果、当、函数等）
- **类型补全**: 支持所有内置类型（整数型、浮点型、字符串型、布尔型等）
- **符号补全**: 支持文档中定义的函数、变量、类、结构体、枚举
- **内置函数补全**: 支持内置函数（打印、读取、长度、获取、设置等）
- **上下文感知**: 根据当前上下文提供不同的补全建议

### 诊断

- **词法错误**: 检测词法分析错误
- **括号匹配**: 检测括号不匹配、未闭合等问题
- **语法结构**: 检测函数返回类型缺失、空结构体等问题
- **未使用变量**: 检测可能未被使用的变量（警告）

### 悬停

- **关键字文档**: 提供关键字的详细文档和示例
- **符号信息**: 显示符号的类型和定义位置

### 导航

- **转到定义**: 跳转到符号的定义位置
- **查找引用**: 查找符号的所有引用位置

### 重构

- **重命名**: 重命名符号并更新所有引用

## 安装

### VSCode 扩展

1. 安装 ZHC Language Server:
   ```bash
   pip install zhc
   ```

2. 安装 VSCode 扩展:
   ```bash
   cd editors/vscode
   npm install
   npm run compile
   ```

3. 在 VSCode 中安装扩展:
   - 打开 VSCode
   - 按 `Cmd+Shift+P` 打开命令面板
   - 输入 "Extensions: Install from VSIX"
   - 选择 `zhc-language-server-0.1.0.vsix`

### 配置

在 VSCode 设置中配置 Language Server:

```json
{
  "zhc.languageServer.path": "zhc-lsp",
  "zhc.languageServer.args": [],
  "zhc.trace.server": "off"
}
```

## 使用方法

### 启动 Language Server

```bash
# 直接运行
python -m zhc.lsp.server

# 或使用命令行工具
zhc-lsp
```

### VSCode 中使用

1. 打开 `.zhc` 文件
2. Language Server 自动启动
3. 开始编写代码，享受智能补全和诊断

### 功能演示

#### 代码补全

```zhc
函数 计算总和(整数型 a, 整数型 b) -> 整数型 {
    // 输入 "整" 会自动补全为 "整数型"
    整数型 结果 = a + b;
    返回 结果;
}
```

#### 诊断

```zhc
函数 测试() {
    // 错误: 未闭合的括号
    整数型 x = (1 + 2;
}
```

#### 悬停

将鼠标悬停在关键字或符号上，会显示详细文档。

#### 转到定义

1. 将光标放在符号上
2. 按 `F12` 或右键选择 "Go to Definition"
3. 跳转到符号的定义位置

#### 查找引用

1. 将光标放在符号上
2. 按 `Shift+F12` 或右键选择 "Find All References"
3. 显示所有引用位置

#### 重命名

1. 将光标放在符号上
2. 按 `F2` 或右键选择 "Rename Symbol"
3. 输入新名称
4. 所有引用自动更新

## API 参考

### LanguageServer 类

```python
from zhc.lsp.server import LanguageServer

# 创建服务器
server = LanguageServer()

# 运行服务器
server.run()
```

### 协议类型

```python
from zhc.lsp.protocol import (
    Position, Range, Location, Diagnostic,
    CompletionItem, Hover, SignatureHelp
)

# 创建位置
pos = Position(line=0, character=0)

# 创建范围
range = Range(start=pos, end=Position(line=0, character=10))

# 创建诊断
diag = Diagnostic(
    range=range,
    severity=DiagnosticSeverity.ERROR,
    message="语法错误"
)
```

### JSON-RPC

```python
from zhc.lsp.jsonrpc import JSONRPCServer, JSONRPCClient

# 创建服务器
server = JSONRPCServer()

# 注册处理器
server.register_handler("initialize", handle_initialize)

# 运行服务器
server.run()
```

## 性能优化

### 缓存策略

- 符号表缓存: 文档打开时解析符号表，更改时更新
- 诊断缓存: 文档更改时重新计算诊断

### 增量更新

- 文档更改时只更新受影响的部分
- 符号表增量更新

### 并行处理

- 多文档并行诊断
- 补全请求并行处理

## 故障排除

### Language Server 无法启动

1. 检查 Python 环境:
   ```bash
   python --version
   pip show zhc
   ```

2. 检查 Language Server 路径:
   ```bash
   which zhc-lsp
   ```

3. 检查 VSCode 配置:
   ```json
   {
     "zhc.languageServer.path": "/path/to/zhc-lsp"
   }
   ```

### 补全不工作

1. 检查文件类型是否为 `.zhc`
2. 检查 Language Server 是否运行
3. 检查 VSCode 输出面板是否有错误

### 诊断不显示

1. 检查文档是否已打开
2. 检查 Language Server 是否发送诊断
3. 检查 VSCode 问题面板

## 贡献

欢迎贡献代码和反馈！

- GitHub: https://github.com/FushengTianQing/ZhC
- Issue: https://github.com/FushengTianQing/ZhC/issues

## 许可证

MIT License
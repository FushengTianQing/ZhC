# P6-WASM-WASI接口支持 开发分析文档

## 基本信息

| 字段 | 内容 |
|------|------|
| **优先级** | P6 |
| **功能模块** | WASM (WebAssembly) |
| **功能名称** | WASI 接口支持 |
| **文档版本** | 1.0.0 |
| **创建日期** | 2026-04-10 |
| **预计工时** | 约 2-3 周 |

---

## 1. 功能概述

WASI (WebAssembly System Interface) 为 WebAssembly 提供了一套标准化的系统接口，使 WASM 模块能够在服务器、边缘计算和嵌入式设备上安全地访问操作系统资源。

### 1.1 核心目标

- 实现 ZhC 程序对标准系统调用的访问能力
- 支持文件系统、网络、时钟、随机数等系统资源
- 提供与 WASI 标准完全兼容的接口实现
- 支持无浏览器环境的 WASM 运行

### 1.2 WASI 与 JavaScript 的区别

| 特性 | JS 环境 | WASI 环境 |
|------|---------|-----------|
| 文件系统 | 受限的 IndexedDB/FS API | 完整 POSIX 文件系统访问 |
| 网络 | WebSocket/HTTP Fetch | 完整 Sockets API |
| 时钟 | 受限 Date API | 完整时钟 API |
| 随机数 | crypto.getRandomValues | 完整随机数生成器 |
| 环境变量 | 不可用 | 完全支持 |
| 进程管理 | 不可用 | 基础支持 |

---

## 2. 技术背景

### 2.1 WASI 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      ZhC 程序代码                            │
│  文件操作 │ 网络请求 │ 时钟函数 │ 随机数 │ 环境变量 │ 进程   │
└───────────────────────┬─────────────────────────────────────┘
                        │ ZhC 标准库调用
┌───────────────────────▼─────────────────────────────────────┐
│                    ZhC WASI 运行时绑定                        │
│  标准输入输出 │ 文件句柄 │ 网络套接字 │ 时钟 │ 随机数      │
└───────────────────────┬─────────────────────────────────────┘
                        │ WASI ABI 调用
┌───────────────────────▼─────────────────────────────────────┐
│                    WASI Interface Types                      │
│        (由 witx 或 .wit 文件定义接口契约)                    │
└───────────────────────┬─────────────────────────────────────┘
                        │ WASM 导入/导出
┌───────────────────────▼─────────────────────────────────────┐
│                    WASI Runtime (Wasmtime/wasm3)              │
│              处理系统调用 │ 内存管理 │ 权限控制                 │
└─────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    Host System                               │
│              Linux │ macOS │ Windows │ Browser               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 WASI 组件

| 组件 | 描述 | 状态 |
|------|------|------|
| **WASI Core** | 核心系统接口（fd, path, clock, random） | 稳定 |
| **WASI Sockets** | 网络编程接口 | 稳定 |
| **WASI Filesystem** | 文件系统访问 | 稳定 |
| **WASI CLI** | 命令行界面 | 草稿 |
| **WASI HTTP** | HTTP 客户端/服务器 | 草稿 |

### 2.3 WASI 的设计原则

1. ** Capability-based Security ** - 每个资源访问都需要显式授权
2. ** Sandbox ** - 模块只能访问明确授予的能力
3. ** Portability ** - 跨平台一致性
4. ** Composability ** - 模块可组合运行

---

## 3. 详细设计

### 3.1 模块架构

```
src/zhc/wasi/
├── __init__.py                 # 模块导出
├── wasi_runtime.py            # WASI 运行时接口
├── wasi_bindings.py           # 自动绑定生成
├── wasi_stubs.py              # WASI 桩函数
├── wasi_types.py              # WASI 类型定义
├── wasi_validator.py          # 权限验证
├── wasi_error.py              # 错误处理
├── sys/
│   ├── __init__.py
│   ├── file.zhc               # 文件操作标准库
│   ├── net.zhc                # 网络编程标准库
│   ├── time.zhc               # 时间相关标准库
│   ├── random.zhc             # 随机数标准库
│   └── env.zhc                # 环境变量标准库
└── tools/
    ├── wasi_runner.py         # WASI 运行工具
    └── wasmtime_integration.py # Wasmtime 集成
```

### 3.2 WASI 核心接口映射

#### 3.2.1 文件操作 (WASI Filesystem)

```python
# src/zhc/wasi/sys/file.zhc

# 标准库模块：zhc.wasi.file

# 中文 API 设计
函数 打开文件(路径: 字符串, 模式: 整数) -> 整数
    # 模式: 0=只读, 1=只写, 2=读写
    # 返回文件描述符

函数 读取文件(文件描述符: 整数, 缓冲区: 字节数组, 长度: 整数) -> 整数
    # 返回实际读取字节数

函数 写入文件(文件描述符: 整数, 数据: 字节数组) -> 整数
    # 返回实际写入字节数

函数 关闭文件(文件描述符: 整数) -> 整数

函数 文件偏移(文件描述符: 整数) -> 整数

函数 设置文件偏移(文件描述符: 整数, 偏移: 整数, 起始位置: 整数) -> 整数
    # 起始位置: 0=起始, 1=当前, 2=末尾

函数 文件状态(路径: 字符串) -> 文件状态
    # 返回文件元信息

结构体 文件状态
    大小: 整数
    修改时间: 整数
    类型: 整数  # 0=未知, 1=块设备, 2=字符设备, 3=目录, 4=普通文件, 5=套接字

函数 创建目录(路径: 字符串) -> 整数
函数 删除文件(路径: 字符串) -> 整数
函数 重命名(旧路径: 字符串, 新路径: 字符串) -> 整数
函数 复制文件(源路径: 字符串, 目标路径: 字符串) -> 整数
```

#### 3.2.2 时钟操作 (WASI Clock)

```python
# src/zhc/wasi/sys/time.zhc

# 中文 API 设计
命名空间 zhc.wasi.time

常量 CLOCK_MONOTONIC = 0      # 单调时钟
常量 CLOCK_REALTIME = 1       # 实时时钟 (墙上时间)
常量 CLOCK_PROCESS_CPUTIME = 2 # 进程 CPU 时间
常量 CLOCK_THREAD_CPUTIME = 3  # 线程 CPU 时间

函数 获取时间(时钟类型: 整数) -> 时间戳
    # 返回纳秒级时间戳

结构体 时间戳
    秒: 整数
    纳秒: 整数

函数 睡眠(毫秒: 整数) -> 整数
    # 精度取决于运行时实现
```

#### 3.2.3 随机数 (WASI Random)

```python
# src/zhc/wasi/sys/random.zhc

# 中文 API 设计
命名空间 zhc.wasi.random

函数 获取随机字节(缓冲区: 字节数组) -> 整数
    # 使用加密安全的随机数源

函数 获取随机整数() -> 整数
    # 返回 32 位随机整数

函数 获取随机长整数() -> 长整数
    # 返回 64 位随机整数

函数 获取随机浮点数() -> 浮点数
    # 返回 [0, 1) 范围内的均匀分布浮点数
```

#### 3.2.4 环境变量 (WASI Environment)

```python
# src/zhc/wasi/sys/env.zhc

# 中文 API 设计
命名空间 zhc.wasi.env

函数 获取环境变量(名称: 字符串) -> 字符串
    # 返回环境变量值，不存在返回空字符串

函数 设置环境变量(名称: 字符串, 值: 字符串) -> 整数
    # 部分运行时可能不支持

函数 删除环境变量(名称: 字符串) -> 整数

函数 获取所有环境变量() -> 映射[字符串, 字符串]

函数 获取程序参数() -> 字符串数组
    # 返回命令行参数列表
```

#### 3.2.5 标准输入输出

```python
# 标准 I/O 集成

常量 STDIN_FILENO = 0   # 标准输入
常量 STDOUT_FILENO = 1  # 标准输出
常量 STDERR_FILENO = 2  # 标准错误

函数 打印(内容: 字符串) -> 整数
函数 打印行(内容: 字符串) -> 整数
函数 读取行() -> 字符串
函数 读取字符() -> 整数  # 返回 Unicode 码点
```

### 3.3 WASI 绑定生成器

```python
class WASIBindingGenerator:
    """WASI 绑定自动生成器"""

    def __init__(self, target: WASIRuntime):
        self.target = target
        self.witx_parser = WITXParser()

    def generate_bindings(self, witx_path: str) -> str:
        """从 WITX 规范文件生成绑定代码"""
        spec = self.witx_parser.parse(witx_path)
        return self._generate_stub_code(spec)

    def _generate_stub_code(self, spec: WITXSpec) -> str:
        """生成 ZhC 桩函数代码"""
        code_parts = [
            "# 自动生成的 WASI 绑定",
            "# 生成时间: " + datetime.now().isoformat(),
            "",
        ]

        for func in spec.functions:
            code_parts.append(self._generate_function(func))

        return "\n".join(code_parts)

    def _generate_function(self, func: WITXFunction) -> str:
        """生成单个函数绑定"""
        params = ", ".join(
            f"{p.name}: {self._map_type(p.type)}"
            for p in func.params
        )
        ret_type = self._map_type(func.result_type)

        return f"""
函数 {func.name}({params}) -> {ret_type}
    # {func.doc}
    外部导入 "wasi_snapshot_preview1" "{func.name}"
"""
```

### 3.4 权限验证

```python
@dataclass
class WASICapability:
    """WASI 能力描述"""
    kind: CapabilityKind
    path: Optional[str] = None
    fd: Optional[int] = None

class WASIValidator:
    """WASI 权限验证器"""

    def __init__(self, allowed_capabilities: List[WASICapability]):
        self.allowed = allowed_capabilities
        self.granted_fds: Dict[int, WASICapability] = {}

    def validate_fd_read(self, fd: int, offset: int, size: int) -> bool:
        """验证文件描述符读权限"""
        if fd not in self.granted_fds:
            return False
        cap = self.granted_fds[fd]
        return cap.kind in (CapabilityKind.FD_READ, CapabilityKind.FD_READWRITE)

    def validate_path_access(self, path: str, access: PathAccess) -> bool:
        """验证路径访问权限"""
        for cap in self.allowed:
            if cap.kind == CapabilityKind.PATH_READ and access == PathAccess.READ:
                if self._path_matches(path, cap.path):
                    return True
        return False

    def grant_fd(self, fd: int, cap: WASICapability):
        """授予文件描述符能力"""
        self.granted_fds[fd] = cap
```

---

## 4. 实现方案

### 4.1 第一阶段：基础框架

1. **定义 WASI 类型系统**
   - 实现 WASI 核心类型
   - 错误码定义
   - 文件描述符系统

2. **实现桩函数**
   - 生成 WASI 导入声明
   - 链接到标准 WASI 实现

3. **基础文件 I/O**
   - open/close/read/write
   - seek/tell

### 4.2 第二阶段：系统功能

1. **时钟和随机数**
   - 实现 clock_gettime
   - 实现 random_get

2. **环境变量**
   - getenv/setenv
   - argv 处理

3. **标准 I/O**
   - print/println 内置函数
   - stdin 读取

### 4.3 第三阶段：高级功能

1. **完整文件系统支持**
   - mkdir/rmdir
   - rename/unlink
   - stat/fstat

2. **网络功能（可选）**
   - socket 创建
   - connect/accept
   - send/recv

### 4.4 第四阶段：集成和测试

1. **Wasmtime 集成**
   - 运行器工具
   - 权限配置

2. **测试套件**
   - WASI 兼容性测试
   - 权限隔离测试

---

## 5. API 设计

### 5.1 命令行接口

```bash
# 使用 WASI 运行 ZhC 程序
zhc run input.zhc --target wasi [选项]

# 选项
--dir <path>              # 允许访问的目录 (可多次指定)
--env <VAR=value>         # 环境变量
--mapdir <guest>=<host>   # 目录映射
--forward <signal>        # 信号转发

# 示例
zhc run input.zhc --target wasi --dir /tmp --env HOME=/tmp
```

### 5.2 编程接口

```python
from zhc.wasi import WASIRuntime, WASICapabilities

# 创建运行时配置
caps = WASICapabilities(
    allowed_dirs=['/tmp/data', './'],
    allowed_env=['HOME', 'USER'],
    max_memory_pages=256,
    stderr_enabled=True,
)

# 创建 WASI 运行时
runtime = WASIRuntime(capabilities=caps)

# 运行编译后的 WASM
result = runtime.run('program.wasm', args=['arg1', 'arg2'])

print(result.stdout)
print(result.stderr)
print(result.exit_code)
```

---

## 6. ZhC 标准库集成

### 6.1 文件操作标准库

```zhc
# src/zhc/lib/wasi/file.zhc

导入 zhc.wasi.file.{打开文件, 读取文件, 写入文件, 关闭文件}
导入 zhc.wasi.file.{创建目录, 删除文件, 重命名}
导入 zhc.wasi.file.{文件状态, 文件是否存在}

函数 读取整个文件(路径: 字符串) -> 字节数组
    变量 文件描述符 = 打开文件(路径, 只读)
    如果 文件描述符 < 0 则
        返回 空字节数组
    结束

    变量 状态 = 文件状态(路径)
    变量 内容 = 新建 字节数组(状态.大小)

    变量 长度 = 读取文件(文件描述符, 内容, 内容.长度)
    关闭文件(文件描述符)

    返回 内容[0:长度]
结束

函数 写入整个文件(路径: 字符串, 内容: 字节数组) -> 布尔
    变量 文件描述符 = 打开文件(路径, 只写)
    如果 文件描述符 < 0 则
        返回 假
    结束

    变量 长度 = 写入文件(文件描述符, 内容)
    关闭文件(文件描述符)

    返回 长度 == 内容.长度
结束
```

### 6.2 控制台 I/O 标准库

```zhc
# src/zhc/lib/std/io.zhc (WASI 版本)

导入 zhc.wasi.{打印, 打印行, 读取行}

函数 主函数() -> 整数
    打印行("你好，世界！")

    打印("请输入您的名字: ")
    变量 名字 = 读取行()

    打印行("欢迎, " + 名字 + "!")

    返回 0
结束
```

---

## 7. 测试策略

### 7.1 单元测试

| 测试类别 | 测试内容 | 测试用例数 |
|----------|----------|------------|
| 文件操作 | open/read/write/close | ~30 |
| 时钟 | clock_gettime | ~10 |
| 随机数 | random_get | ~15 |
| 环境变量 | getenv/setenv | ~10 |
| 错误处理 | 各种错误场景 | ~20 |

### 7.2 集成测试

```python
def test_wasi_file_io():
    """测试完整文件 I/O 操作"""
    # 创建测试文件
    # 写入内容
    # 读取验证
    # 清理

def test_wasi_permissions():
    """测试权限隔离"""
    # 尝试访问未授权目录
    # 验证被拒绝
```

---

## 8. 已知限制和风险

### 8.1 WASI 限制

| 限制 | 影响 | 缓解方案 |
|------|------|----------|
| 能力安全模型 | 需要显式授权 | 提供清晰的错误提示 |
| 文件系统沙箱 | 无法访问所有文件 | 配置允许列表 |
| 无完整 POSIX | 部分 API 不兼容 | 提供 ZhC 标准库抽象 |
| 不同运行时差异 | Wasmtime/WAMR 等实现不同 | 测试多个运行时 |

### 8.2 兼容性考虑

- Wasmtime: 最完整的 WASI 实现
- wasm3: 轻量级，WASI 支持有限
- WAMR: 嵌入式优化，WASI 支持在发展中
- browser: 使用 WASI polyfill

---

## 9. 参考资料

- [WASI Specification](https://github.com/WebAssembly/WASI)
- [WASI API Reference](https://docs.wasmtime.dev/wasi.html)
- [Witx Specification](https://github.com/WebAssembly/witx)
- [Wasmtime Documentation](https://docs.wasmtime.dev/)
- [WASI Capability Permissions](https://github.com/WebAssembly/WASI/blob/main/Proposals/wasi-Capability-Oriented-Programming.md)

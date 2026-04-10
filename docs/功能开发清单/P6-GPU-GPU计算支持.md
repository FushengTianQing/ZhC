# P6-GPU-GPU计算支持 开发分析文档

## 基本信息

| 字段 | 内容 |
|------|------|
| **优先级** | P6 |
| **功能模块** | GPU (图形处理器) |
| **功能名称** | CUDA/OpenCL 支持 |
| **文档版本** | 1.0.0 |
| **创建日期** | 2026-04-10 |
| **预计工时** | 约 6-8 周 |

---

## 1. 功能概述

GPU 计算支持使 ZhC 程序能够利用图形处理器的并行计算能力执行高性能计算任务。本模块支持 CUDA (NVIDIA) 和 OpenCL (跨平台) 两种主流 GPU 计算框架。

### 1.1 核心目标

- 提供简洁的中文 GPU 编程 API
- 支持 CUDA (NVIDIA GPU) 和 OpenCL (跨平台)
- 实现自动 GPU 代码生成
- 提供标准库级别的 GPU 操作支持

### 1.2 目标场景

| 场景 | 描述 | 性能提升 |
|------|------|----------|
| 向量运算 | 大规模向量加法、乘法 | 100-1000x |
| 矩阵运算 | 矩阵乘法、卷积 | 50-500x |
| 深度学习 | 神经网络推理/训练 | 10-100x |
| 科学计算 | Monte Carlo、傅里叶变换 | 20-200x |
| 图像处理 | 滤波、变换、识别 | 20-100x |

---

## 2. 技术背景

### 2.1 GPU 编程模型

```
┌─────────────────────────────────────────────────────────────┐
│                    GPU 编程模型                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  主机 (CPU)                      设备 (GPU)                   │
│  ┌─────────────┐                ┌─────────────────────────┐ │
│  │  内存分配   │ ──────────────>│  设备内存               │ │
│  │  数据传输   │                │  ┌─────┬─────┬─────┐   │ │
│  │  内核启动   │ ──────────────>│  │thread│thread│ ...│   │ │
│  │  结果回收   │ <──────────────│  ├─────┼─────┼─────┤   │ │
│  │             │                │  │thread│thread│ ...│   │ │
│  └─────────────┘                │  └─────┴─────┴─────┘   │ │
│                                 │       Grid (网格)       │ │
│  ┌─────────────┐                │  ┌─────────────────────┐ │ │
│  │  同步等待   │ ──────────────>│  │  Block 0 │ Block 1 │ │ │
│  └─────────────┘                │  └─────────────────────┘ │ │
│                                 └─────────────────────────┘ │
│                                                              │
│  层次结构: Grid > Block > Thread                             │
│  典型配置: Grid(256, 256), Block(16, 16, 8)                  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 CUDA vs OpenCL 对比

| 特性 | CUDA | OpenCL |
|------|------|--------|
| 厂商支持 | 仅 NVIDIA | Intel, AMD, NVIDIA, Apple |
| 成熟度 | 成熟稳定 | 较为碎片化 |
| 性能优化 | 深度优化 | 依赖厂商实现 |
| API 复杂度 | 较简洁 | 较复杂 |
| 跨平台 | 仅 Windows/Linux/macOS | 全平台 |
| 工具链 | Nsight, nvcc | Intel GPA, AMD GPU Profiler |

---

## 3. 详细设计

### 3.1 模块架构

```
src/zhc/gpu/
├── __init__.py                 # 模块导出
├── gpu_backend.py              # GPU 后端基类
├── cuda/
│   ├── __init__.py
│   ├── cuda_backend.py         # CUDA 后端
│   ├── cuda_codegen.py         # CUDA 代码生成
│   ├── cuda_runtime.py         # CUDA 运行时
│   ├── cuda_module.py          # CUDA 模块管理
│   ├── cuda_memory.py          # CUDA 内存管理
│   └── ptx_emitter.py          # PTX 汇编生成
├── opencl/
│   ├── __init__.py
│   ├── opencl_backend.py       # OpenCL 后端
│   ├── opencl_codegen.py      # OpenCL 代码生成
│   ├── opencl_runtime.py      # OpenCL 运行时
│   └── spirv_emitter.py       # SPIR-V 生成
├── common/
│   ├── __init__.py
│   ├── gpu_abi.py             # GPU ABI 定义
│   ├── gpu_types.py           # GPU 类型系统
│   ├── gpu_intrinsics.py      # GPU 内在函数
│   └── gpu_optimizer.py       # GPU 优化
└── standard/
    ├── __init__.py
    ├── vector_ops.zhc          # 向量运算标准库
    ├── matrix_ops.zhc         # 矩阵运算标准库
    ├── reduce_ops.zhc         # 归约运算标准库
    └── parallel_algo.zhc       # 并行算法
```

### 3.2 GPU 编程 API 设计

#### 3.2.1 中文 CUDA 编程 API

```zhc
# src/zhc/lib/gpu/cuda.zhc

导入 zhc.gpu.cuda.{获取设备数, 获取设备, 创建设备内存}
导入 zhc.gpu.cuda.{复制到设备, 复制到主机, 同步设备}
导入 zhc.gpu.cuda.{加载内核, 启动内核}

# 设备管理
函数 获取GPU设备(编号: 整数) -> 设备句柄
    # 获取指定编号的 GPU 设备
    外部 "cuda" "cuda_get_device"

函数 获取GPU设备数() -> 整数
    # 返回可用的 GPU 数量
    外部 "cuda" "cuda_get_device_count"

函数 获取设备名称(设备: 设备句柄) -> 字符串
    外部 "cuda" "cuda_get_device_name"

函数 获取设备内存(设备: 设备句柄) -> 内存信息
    结构体 内存信息
        总内存: 长整数
        可用内存: 长整数
    结束
    外部 "cuda" "cuda_get_mem_info"

# 内存管理
函数 创建设备内存(大小: 长整数) -> 内存指针
    外部 "cuda" "cuda_malloc"

函数 释放设备内存(指针: 内存指针) -> 整数
    外部 "cuda" "cuda_free"

函数 复制数据到设备(目标: 内存指针, 源: 指针, 大小: 长整数) -> 整数
    外部 "cuda" "cuda_memcpy_host_to_device"

函数 复制数据到主机(目标: 指针, 源: 内存指针, 大小: 长整数) -> 整数
    外部 "cuda" "cuda_memcpy_device_to_host"

函数 复制数据设备到设备(目标: 内存指针, 源: 内存指针, 大小: 长整数) -> 整数
    外部 "cuda" "cuda_memcpy_device_to_device"

函数 内存集(指针: 内存指针, 值: 整数, 大小: 长整数) -> 整数
    外部 "cuda" "cuda_memset"

# 内核执行
函数 同步设备(设备: 设备句柄) -> 整数
    # 等待设备上所有操作完成
    外部 "cuda" "cuda_device_synchronize"

函数 设置设备(设备: 设备句柄) -> 整数
    外部 "cuda" "cuda_set_device"

结构体 执行配置
    网格维度X: 整数
    网格维度Y: 整数
    网格维度Z: 整数
    块维度X: 整数
    块维度Y: 整数
    块维度Z: 整数
    共享内存大小: 整数
    流: 整数  # 0 表示默认流
结束
```

#### 3.2.2 并行内核语法

```zhc
# 并行内核定义语法
内核 向量加法(结果: 指针[浮点数], A: 指针[浮点数], B: 指针[浮点数], N: 整数)
    # 获取线程索引
    变量 线程索引 = 获取全局线程索引()
    变量 块索引 = 获取块索引()

    # 边界检查
    如果 线程索引 >= N 则
        返回
    结束

    # 执行计算
    结果[线程索引] = A[线程索引] + B[线程索引]
结束

# 调用内核
函数 主函数() -> 整数
    变量 N = 1000000
    变量 大小 = N * 类型大小(浮点数)

    # 分配内存
    变量 主机A = 申请主机内存(大小)
    变量 主机B = 申请主机内存(大小)
    变量 主机结果 = 申请主机内存(大小)

    # 初始化数据
    对于 I 从 0 到 N - 1 执行
        主机A[I] = 1.0
        主机B[I] = 2.0
    结束

    # 复制到设备
    变量 设备A = 创建设备内存(大小)
    变量 设备B = 创建设备内存(大小)
    变量 设备结果 = 创建设备内存(大小)
    复制数据到设备(设备A, 主机A, 大小)
    复制数据到设备(设备B, 主机B, 大小)

    # 执行配置
    变量 配置 = 新建 执行配置
    配置.网格维度X = (N + 255) / 256
    配置.块维度X = 256

    # 启动内核
    启动内核 向量加法(配置, 设备结果, 设备A, 设备B, N)

    # 同步并复制结果
    同步设备(0)
    复制数据到主机(主机结果, 设备结果, 大小)

    # 清理
    释放设备内存(设备A)
    释放设备内存(设备B)
    释放设备内存(设备结果)

    打印行("完成！前10个结果: ")
    对于 I 从 0 到 10 执行
        打印行(主机结果[I])
    结束

    返回 0
结束
```

### 3.3 GPU 代码生成器

```python
class GPUCodegenBase(ABC):
    """GPU 代码生成器基类"""

    def __init__(self, options: GPUOptions):
        self.options = options
        self.ir_rewriter = GPUIRRewriter()
        self.intrinsics = GPUIntrinsics()

    @abstractmethod
    def generate_kernel(self, kernel: GPUKernel) -> str:
        """生成内核代码"""
        pass

    @abstractmethod
    def generate_launch_code(self, kernel: GPUKernel,
                             config: LaunchConfig) -> str:
        """生成内核启动代码"""
        pass

    def transform_ir(self, ir: IRModule) -> GPUIRModule:
        """将 IR 转换为 GPU IR"""
        gpu_ir = GPUIRModule()

        for func in ir.functions:
            if func.is_kernel:
                gpu_ir.kernels.append(self._transform_kernel(func))
            else:
                gpu_ir.host_functions.append(func)

        return gpu_ir


class CUDACodegen(GPUCodegenBase):
    """CUDA 代码生成器"""

    def generate_kernel(self, kernel: GPUKernel) -> str:
        """生成 CUDA C++ 内核代码"""
        lines = [
            f"// GPU Kernel: {kernel.name}",
            f"extern \"C\" __global__ void {kernel.name}(",
            self._generate_parameters(kernel.params),
            ") {",
            "",
        ]

        # 生成线程索引获取代码
        lines.extend(self._generate_thread_idx())

        # 生成主体代码
        lines.extend(self._generate_body(kernel))

        lines.append("}")
        return "\n".join(lines)

    def _generate_thread_idx(self) -> List[str]:
        """生成线程索引代码"""
        return [
            "    int tid = blockIdx.x * blockDim.x + threadIdx.x;",
            "    int blockId = blockIdx.x;",
            "    int threadId = threadIdx.x;",
        ]

    def _generate_parameters(self, params: List[GPUParameter]) -> str:
        """生成参数声明"""
        param_strs = []
        for p in params:
            cuda_type = self._map_type(p.type)
            if p.is_pointer:
                const = "const " if p.is_const else ""
                pointer = self._get_pointer_qualifier(p)
                param_strs.append(f"        {const}{cuda_type}* {pointer}{p.name}")
            else:
                param_strs.append(f"        {cuda_type} {p.name}")
        return ",\n".join(param_strs)
```

### 3.4 GPU 内在函数

```python
class GPUIntrinsics:
    """GPU 内在函数定义"""

    # CUDA 内在函数
    CUDA_INTRINSICS = {
        # 线程索引
        'get_global_thread_idx': ('threadIdx.x + blockIdx.x * blockDim.x', 'int'),
        'get_block_idx': ('blockIdx.x', 'int'),
        'get_thread_idx': ('threadIdx.x', 'int'),
        'get_block_dim': ('blockDim.x', 'int'),
        'get_grid_dim': ('gridDim.x', 'int'),

        # 同步
        'syncthreads': ('__syncthreads()', None),
        'threadfence': ('__threadfence()', None),
        'threadfence_block': ('__threadfence_block()', None),

        # 原子操作
        'atomic_add_f32': ('atomicAdd', 'float'),
        'atomic_add_f64': ('atomicAdd', 'double'),
        'atomic_cas': ('atomicCAS', 'int'),
        'atomic_exch': ('atomicExch', 'int'),

        # Warp 级别
        'shuffle_xor': ('__shfl_xor_sync', 'int'),
        'shuffle_up': ('__shfl_up_sync', 'int'),
        'shuffle_down': ('__shfl_down_sync', 'int'),
        'ballot': ('__ballot_sync', 'int'),
        'any': ('__any_sync', 'int'),
        'all': ('__all_sync', 'int'),

        # 数学函数
        '__sinf': ('sinf', 'float'),
        '__cosf': ('cosf', 'float'),
        '__expf': ('expf', 'float'),
        '__logf': ('logf', 'float'),
        '__sqrtf': ('sqrtf', 'float'),
        '__rsqrtf': ('rsqrtf', 'float'),
        '__powf': ('powf', 'float'),
    }

    def emit_intrinsic(self, name: str, args: List[str]) -> str:
        """发射内在函数调用"""
        if name in self.CUDA_INTRINSICS:
            func, _ = self.CUDA_INTRINSICS[name]
            return f"{func}({', '.join(args)})"
        else:
            raise UnknownIntrinsicError(name)
```

### 3.5 PTX 生成器

```python
class PTXEmitter:
    """CUDA PTX 汇编生成器"""

    def __init__(self):
        self.registers: Dict[str, str] = {}
        self.reg_counter = 0

    def _alloc_reg(self, name: str) -> str:
        """分配寄存器"""
        if name not in self.registers:
            self.registers[name] = f"%r{self.reg_counter}"
            self.reg_counter += 1
        return self.registers[name]

    def emit_add(self, dest: str, src1: str, src2: str) -> str:
        """发射加法指令"""
        d = self._alloc_reg(dest)
        s1 = self._alloc_reg(src1)
        s2 = self._alloc_reg(src2)
        return f"    add.s32 {d}, {s1}, {s2};"

    def emit_ld(self, dest: str, base: str, offset: int) -> str:
        """发射加载指令"""
        d = self._alloc_reg(dest)
        b = self._alloc_reg(base)
        return f"    ld.global.f32 {d}, [{b}+{offset}];"

    def emit_st(self, base: str, offset: int, value: str) -> str:
        """发射存储指令"""
        b = self._alloc_reg(base)
        v = self._alloc_reg(value)
        return f"    st.global.f32 [{b}+{offset}], {v};"

    def emit_ret(self) -> str:
        """发射返回指令"""
        return "    ret;"

    def emit_kernel_prologue(self, kernel: GPUKernel) -> List[str]:
        """生成内核序言"""
        lines = [
            f".global .align 16 .b8 {kernel.name}_param[{kernel.param_size}];",
            "",
            f".visible .entry {kernel.name}(",
            self._emit_param_space(kernel.params),
            ") {",
        ]

        # 保存寄存器
        lines.append("    .reg .pred %p;")
        lines.append("    .reg .f32 %f;")
        lines.append("    .reg .b32 %r;")

        return lines
```

---

## 4. 实现方案

### 4.1 第一阶段：CUDA 支持

1. **基础框架**
   - GPU 后端基类
   - CUDA 后端实现
   - PTX 生成器

2. **内存管理**
   - 设备内存分配
   - 主机-设备数据传输
   - 统一内存 (managed memory)

3. **内核执行**
   - 内核代码生成
   - 启动配置
   - 同步机制

### 4.2 第二阶段：OpenCL 支持

1. **OpenCL 后端**
   - OpenCL 后端实现
   - SPIR-V 生成

2. **跨平台支持**
   - 统一的 GPU API
   - 后端自动选择

### 4.3 第三阶段：标准库

1. **向量运算库**
   - 向量加法/减法
   - 向量点积
   - 向量归约

2. **矩阵运算库**
   - 矩阵乘法
   - 矩阵转置

### 4.4 第四阶段：高级功能

1. **共享内存优化**
   - 共享内存管理
   - 内存合并访问

2. **自动调优**
   - 最佳块大小搜索
   - 性能优化

---

## 5. 测试策略

### 5.1 单元测试

| 测试类别 | 测试内容 | 测试用例数 |
|----------|----------|------------|
| 内存管理 | 分配/释放/复制 | ~20 |
| 内核生成 | 代码生成正确性 | ~30 |
| 内核执行 | 结果正确性 | ~40 |
| 性能测试 | 加速比验证 | ~20 |

### 5.2 集成测试

```python
def test_vector_add_gpu():
    """测试向量加法 GPU 实现"""
    N = 1000000
    h_a = np.random.rand(N).astype(np.float32)
    h_b = np.random.rand(N).astype(np.float32)
    h_result = np.zeros(N, dtype=np.float32)

    # 分配设备内存
    d_a = cuda.malloc(N * 4)
    d_b = cuda.malloc(N * 4)
    d_result = cuda.malloc(N * 4)

    # 复制数据
    cuda.memcpy_host_to_device(d_a, h_a, N * 4)
    cuda.memcpy_host_to_device(d_b, h_b, N * 4)

    # 启动内核
    config = (N + 255) // 256, 256
    vector_add_kernel(config, d_result, d_a, d_b, N)

    # 同步并复制结果
    cuda.synchronize()
    cuda.memcpy_device_to_host(h_result, d_result, N * 4)

    # 验证
    expected = h_a + h_b
    assert np.allclose(h_result, expected)
```

---

## 6. 参考资料

- [CUDA Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/)
- [CUDA Toolkit Documentation](https://docs.nvidia.com/cuda/)
- [OpenCL Specification](https://www.khronos.org/opencl/)
- [OpenCL Programming Guide](https://man.opencl.org/)
- [PTX ISA Documentation](https://docs.nvidia.com/cuda/parallel-thread-execution/)

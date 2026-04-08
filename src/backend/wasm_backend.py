"""
WebAssembly后端
WebAssembly Backend

将中文C代码编译为WebAssembly，支持在浏览器和Node.js中运行。

核心功能：
1. WASM代码生成：将C代码转换为WASM
2. Emscripten集成：使用Emscripten工具链
3. WASM优化：优化生成的WASM代码
4. JavaScript胶水代码：生成JS调用接口

架构重构（2026-04-08）：
- 继承 BackendBase 统一接口
- 支持 CompileOptions 和 CompileResult

使用场景：
- Web应用开发
- 跨平台部署
- 高性能计算
"""

import subprocess
import re
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from pathlib import Path
from dataclasses import dataclass, field
import json

# 导入基类
from .base import (
    BackendBase,
    BackendCapabilities,
    CompileOptions,
    CompileResult,
    OutputFormat,
    BackendError,
)

if TYPE_CHECKING:
    from zhc.ir.program import IRProgram


@dataclass
class WASMCompileResult:
    """WASM编译结果（遗留兼容）"""
    success: bool              # 是否成功
    wasm_file: Optional[str]   # WASM文件路径
    js_file: Optional[str]     # JavaScript胶水文件路径
    html_file: Optional[str]   # HTML文件路径（可选）
    errors: List[str] = field(default_factory=list)          # 错误信息
    warnings: List[str] = field(default_factory=list)         # 警告信息
    metadata: Dict = field(default_factory=dict)             # 元数据（文件大小等）


class WebAssemblyBackend(BackendBase):
    """
    WebAssembly后端

    将中文C代码编译为WebAssembly

    示例：
    >>> backend = WebAssemblyBackend()
    >>> result = backend.compile("main.zhc", "output")
    >>> print(result.wasm_file)
    """

    @property
    def name(self) -> str:
        return "wasm"

    @property
    def description(self) -> str:
        return f"WASM 后端 (Emscripten)"

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            supports_jit=False,
            supports_debug=True,  # WASM 支持 DWARF 调试
            supports_optimization=True,
            supports_cross_compile=True,
            target_platforms=["wasm32"],
            output_formats=[OutputFormat.WASM],
            required_tools=["emcc"],
        )

    def __init__(self,
                 emscripten_path: str = "emcc",
                 optimization_level: str = "O2",
                 enable_simd: bool = True,
                 enable_threads: bool = False):
        """
        初始化WASM后端

        Args:
            emscripten_path: Emscripten编译器路径
            optimization_level: 优化级别（O0, O1, O2, O3, Os, Oz）
            enable_simd: 启用SIMD
            enable_threads: 启用线程支持
        """
        self.emscripten_path = emscripten_path
        self.optimization_level = optimization_level
        self.enable_simd = enable_simd
        self.enable_threads = enable_threads

        # 检查Emscripten是否可用
        self.available = self._check_availability()

        # 统计信息
        self.stats = {
            'total_compiles': 0,
            'successful_compiles': 0,
            'failed_compiles': 0,
            'total_wasm_size': 0,
            'total_js_size': 0
        }

    def _create_debug_listener(
        self,
        source_file: str,
        output_file: str = "debug.json"
    ):
        """
        创建 WASM 后端专用调试监听器

        Args:
            source_file: 源文件路径
            output_file: 输出文件路径

        Returns:
            WASMDebugListener: WASM 后端调试监听器
        """
        from .wasm_debug_listener import WASMDebugListener
        return WASMDebugListener(source_file=source_file, module_name='main')

    # ===== BackendBase 接口实现 =====

    def compile(
        self,
        ir: "IRProgram",
        output_path: Path,
        options: Optional[CompileOptions] = None,
    ) -> CompileResult:
        """
        编译 IR 到 WebAssembly（BackendBase 接口）

        Args:
            ir: IR 程序
            output_path: 输出路径
            options: 编译选项

        Returns:
            CompileResult: 编译结果
        """
        options = options or CompileOptions()

        # TODO: 实现 IR → WASM 转换
        # 当前需要先将 IR 转为 C 代码，再用 Emscripten 编译

        return CompileResult(
            success=False,
            errors=["IR 到 WASM 的直接转换尚未实现"],
        )

    def is_available(self) -> bool:
        """检查 Emscripten 是否可用"""
        return self._check_availability()

    def get_version(self) -> Optional[str]:
        """获取 Emscripten 版本"""
        try:
            result = subprocess.run(
                [self.emscripten_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.splitlines()[0]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    # ===== 原有方法 =====

    def _check_availability(self) -> bool:
        """检查Emscripten是否可用"""
        try:
            result = subprocess.run(
                [self.emscripten_path, "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def compile_to_wasm(self,
                       c_file: str,
                       output_dir: str,
                       output_name: Optional[str] = None,
                       export_functions: Optional[List[str]] = None,
                       export_memory: bool = True,
                       generate_html: bool = False) -> WASMCompileResult:
        """
        将C代码编译为WebAssembly

        Args:
            c_file: C源文件路径
            output_dir: 输出目录
            output_name: 输出文件名（不含扩展名）
            export_functions: 导出的函数列表
            export_memory: 导出内存
            generate_html: 生成HTML测试页面

        Returns:
            WASMCompileResult: 编译结果
        """
        if not self.available:
            return WASMCompileResult(
                success=False,
                wasm_file=None,
                js_file=None,
                html_file=None,
                errors=["Emscripten 不可用"],
            )

        # 构建输出路径
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if output_name is None:
            output_name = Path(c_file).stem

        wasm_file = str(output_path / f"{output_name}.wasm")
        js_file = str(output_path / f"{output_name}.js")

        # 构建 emcc 命令
        cmd = [
            self.emscripten_path,
            c_file,
            "-o", js_file,
            "-s", f"WASM={1}",
            "-s", f"EXPORTED_FUNCTIONS={export_functions or ['_main']}",
        ]

        if export_memory:
            cmd.extend(["-s", "EXPORTED_RUNTIME_METHODS=['ccall','cwrap']"])
            cmd.extend(["-s", "EXPORTED_MEMORY=1"])

        if generate_html:
            cmd.append("--html")

        # 优化级别
        cmd.append(f"-{self.optimization_level}")

        # SIMD
        if self.enable_simd:
            cmd.extend(["-s", "SIMD=1"])

        # 线程
        if self.enable_threads:
            cmd.extend(["-s", "USE_PTHREADS=1"])

        # 执行编译
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            errors = []
            warnings = []

            if result.stderr:
                for line in result.stderr.splitlines():
                    if "error" in line.lower():
                        errors.append(line)
                    elif "warning" in line.lower():
                        warnings.append(line)

            success = result.returncode == 0 and Path(wasm_file).exists()

            if success:
                self.stats['total_compiles'] += 1
                self.stats['successful_compiles'] += 1

                # 更新统计
                wasm_size = Path(wasm_file).stat().st_size
                js_size = Path(js_file).stat().st_size
                self.stats['total_wasm_size'] += wasm_size
                self.stats['total_js_size'] += js_size

            else:
                self.stats['total_compiles'] += 1
                self.stats['failed_compiles'] += 1
                if not errors:
                    errors.append("编译失败")

            return WASMCompileResult(
                success=success,
                wasm_file=wasm_file if success else None,
                js_file=js_file if success else None,
                html_file=str(output_path / f"{output_name}.html") if generate_html else None,
                errors=errors,
                warnings=warnings,
                metadata={
                    "wasm_size": wasm_size if success else 0,
                    "js_size": js_size if success else 0,
                },
            )

        except subprocess.TimeoutExpired:
            return WASMCompileResult(
                success=False,
                wasm_file=None,
                js_file=None,
                html_file=None,
                errors=["编译超时（5分钟）"],
            )
        except FileNotFoundError:
            return WASMCompileResult(
                success=False,
                wasm_file=None,
                js_file=None,
                html_file=None,
                errors=[f"未找到 Emscripten: {self.emscripten_path}"],
            )


if __name__ == "__main__":
    # 测试
    backend = WebAssemblyBackend()

    print(f"后端名称: {backend.name}")
    print(f"后端可用: {backend.is_available()}")
    print(f"版本信息: {backend.get_version()}")
    print(f"支持平台: {backend.capabilities.target_platforms}")

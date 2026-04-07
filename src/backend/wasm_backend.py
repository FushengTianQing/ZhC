"""
WebAssembly后端
WebAssembly Backend

将中文C代码编译为WebAssembly，支持在浏览器和Node.js中运行。

核心功能：
1. WASM代码生成：将C代码转换为WASM
2. Emscripten集成：使用Emscripten工具链
3. WASM优化：优化生成的WASM代码
4. JavaScript胶水代码：生成JS调用接口

使用场景：
- Web应用开发
- 跨平台部署
- 高性能计算
"""

import subprocess
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import json


@dataclass
class WASMCompileResult:
    """WASM编译结果"""
    success: bool              # 是否成功
    wasm_file: Optional[str]   # WASM文件路径
    js_file: Optional[str]     # JavaScript胶水文件路径
    html_file: Optional[str]   # HTML文件路径（可选）
    errors: List[str]          # 错误信息
    warnings: List[str]        # 警告信息
    metadata: Dict             # 元数据（文件大小等）


class WebAssemblyBackend:
    """
    WebAssembly后端
    
    将中文C代码编译为WebAssembly
    
    示例：
    >>> backend = WebAssemblyBackend()
    >>> result = backend.compile("main.zhc", "output")
    >>> print(result.wasm_file)
    """
    
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
        编译为WebAssembly
        
        Args:
            c_file: C源文件路径
            output_dir: 输出目录
            output_name: 输出文件名（不含扩展名）
            export_functions: 导出的函数列表
            export_memory: 导出内存
            generate_html: 生成HTML文件
            
        Returns:
            WASMCompileResult: 编译结果
        """
        self.stats['total_compiles'] += 1
        
        if not self.available:
            self.stats['failed_compiles'] += 1
            return WASMCompileResult(
                success=False,
                wasm_file=None,
                js_file=None,
                html_file=None,
                errors=["Emscripten不可用"],
                warnings=[],
                metadata={}
            )
        
        # 准备参数
        if output_name is None:
            output_name = Path(c_file).stem
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        args = [
            self.emscripten_path,
            c_file,
            f"-{self.optimization_level}",
            "-o", str(output_path / f"{output_name}.js")
        ]
        
        # 导出函数
        if export_functions:
            export_list = ",".join(export_functions)
            args.append(f"-sEXPORTED_FUNCTIONS=[{export_list}]")
        
        # 导出内存
        if export_memory:
            args.append("-sEXPORTED_RUNTIME_METHODS=['ccall','cwrap']")
        
        # SIMD支持
        if self.enable_simd:
            args.append("-msimd128")
        
        # 线程支持
        if self.enable_threads:
            args.append("-pthread")
        
        # 生成HTML
        if generate_html:
            args.append("-sENVIRONMENT='web,node'")
        
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                wasm_file = str(output_path / f"{output_name}.wasm")
                js_file = str(output_path / f"{output_name}.js")
                html_file = str(output_path / f"{output_name}.html") if generate_html else None
                
                # 统计文件大小
                wasm_size = Path(wasm_file).stat().st_size if Path(wasm_file).exists() else 0
                js_size = Path(js_file).stat().st_size if Path(js_file).exists() else 0
                
                self.stats['successful_compiles'] += 1
                self.stats['total_wasm_size'] += wasm_size
                self.stats['total_js_size'] += js_size
                
                return WASMCompileResult(
                    success=True,
                    wasm_file=wasm_file,
                    js_file=js_file,
                    html_file=html_file,
                    errors=[],
                    warnings=[line for line in result.stderr.split('\n') if 'warning' in line.lower()],
                    metadata={
                        'wasm_size': wasm_size,
                        'js_size': js_size,
                        'wasm_size_kb': wasm_size / 1024,
                        'js_size_kb': js_size / 1024
                    }
                )
            else:
                self.stats['failed_compiles'] += 1
                
                return WASMCompileResult(
                    success=False,
                    wasm_file=None,
                    js_file=None,
                    html_file=None,
                    errors=[result.stderr],
                    warnings=[],
                    metadata={}
                )
        
        except subprocess.TimeoutExpired:
            self.stats['failed_compiles'] += 1
            
            return WASMCompileResult(
                success=False,
                wasm_file=None,
                js_file=None,
                html_file=None,
                errors=["编译超时"],
                warnings=[],
                metadata={}
            )
    
    def generate_js_wrapper(self,
                           wasm_file: str,
                           functions: List[Tuple[str, str, List[str]]]) -> str:
        """
        生成JavaScript包装代码
        
        Args:
            wasm_file: WASM文件路径
            functions: 函数列表 [(函数名, 返回类型, 参数类型列表)]
            
        Returns:
            JavaScript包装代码
        """
        lines = []
        lines.append("// 自动生成的WebAssembly包装代码")
        lines.append(f"// WASM文件: {wasm_file}")
        lines.append("")
        lines.append("const wasmModule = {")
        lines.append("  instance: null,")
        lines.append("  memory: null,")
        lines.append("")
        lines.append("  async init() {")
        lines.append(f"    const response = await fetch('{wasm_file}');")
        lines.append("    const bytes = await response.arrayBuffer();")
        lines.append("    const module = await WebAssembly.instantiate(bytes);")
        lines.append("    this.instance = module.instance;")
        lines.append("    this.memory = module.instance.exports.memory;")
        lines.append("  },")
        lines.append("")
        
        # 为每个函数生成包装
        for func_name, return_type, param_types in functions:
            # 类型映射
            type_map = {
                'int': 'number',
                'float': 'number',
                'double': 'number',
                'void': None
            }
            
            param_list = ", ".join([f"p{i}" for i in range(len(param_types))])
            
            lines.append(f"  {func_name}({param_list}) {{")
            lines.append(f"    return this.instance.exports.{func_name}({param_list});")
            lines.append("  },")
            lines.append("")
        
        lines.append("};")
        lines.append("")
        lines.append("// 使用示例")
        lines.append("async function main() {")
        lines.append("  await wasmModule.init();")
        lines.append("  console.log('WASM模块加载完成');")
        lines.append("}")
        lines.append("")
        lines.append("main();")
        
        return '\n'.join(lines)
    
    def optimize_wasm(self, wasm_file: str, output_file: str) -> bool:
        """
        优化WASM文件
        
        Args:
            wasm_file: 输入WASM文件
            output_file: 输出WASM文件
            
        Returns:
            是否成功
        """
        try:
            # 使用wasm-opt优化（如果可用）
            result = subprocess.run(
                ["wasm-opt", "-O", "-o", output_file, wasm_file],
                capture_output=True,
                timeout=30
            )
            
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # wasm-opt不可用，直接复制
            import shutil
            try:
                shutil.copy(wasm_file, output_file)
                return True
            except IOError:
                return False
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            'available': self.available,
            'success_rate': (
                self.stats['successful_compiles'] /
                max(1, self.stats['total_compiles'])
            ),
            'average_wasm_size_kb': (
                self.stats['total_wasm_size'] / 1024 /
                max(1, self.stats['successful_compiles'])
            )
        }


# 便捷函数
def compile_to_wasm(c_file: str, output_dir: str, **kwargs) -> WASMCompileResult:
    """便捷函数：编译为WASM"""
    backend = WebAssemblyBackend()
    return backend.compile_to_wasm(c_file, output_dir, **kwargs)


if __name__ == "__main__":
    # 示例用法
    backend = WebAssemblyBackend()
    
    print("WebAssembly后端状态:")
    print(f"  Emscripten可用: {backend.available}")
    print(f"  统计信息: {backend.get_statistics()}")
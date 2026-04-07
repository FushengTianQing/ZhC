"""
Sanitizers支持
Sanitizers Support

集成Clang/LLVM的各种sanitizer工具，用于运行时错误检测。

核心功能：
1. AddressSanitizer (ASan)：内存错误检测
2. MemorySanitizer (MSan)：未初始化内存读取检测
3. ThreadSanitizer (TSan)：数据竞争检测
4. UndefinedBehaviorSanitizer (UBSan)：未定义行为检测
5. LeakSanitizer (LSan)：内存泄漏检测

使用场景：
- 开发阶段错误检测
- 自动化测试
- 持续集成检查
"""

import subprocess
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class SanitizerType(Enum):
    """Sanitizer类型"""
    ADDRESS = "address"      # AddressSanitizer
    MEMORY = "memory"        # MemorySanitizer
    THREAD = "thread"        # ThreadSanitizer
    UNDEFINED = "undefined"  # UndefinedBehaviorSanitizer
    LEAK = "leak"           # LeakSanitizer


@dataclass
class SanitizerResult:
    """Sanitizer检测结果"""
    sanitizer_type: SanitizerType  # Sanitizer类型
    success: bool                  # 编译是否成功
    passed: bool                   # 运行是否通过
    errors: List[str]              # 错误列表
    warnings: List[str]            # 警告列表
    output: str                    # 完整输出
    metadata: Dict                 # 元数据


class SanitizerIntegration:
    """
    Sanitizers集成
    
    提供各种sanitizer的编译和运行支持
    
    示例：
    >>> sanitizer = SanitizerIntegration()
    >>> result = sanitizer.run_with_asan("main.c", "./a.out")
    >>> print(result.passed)
    """
    
    def __init__(self,
                 clang_path: str = "clang",
                 default_sanitizers: Optional[List[SanitizerType]] = None):
        """
        初始化Sanitizer集成
        
        Args:
            clang_path: Clang编译器路径
            default_sanitizers: 默认启用的sanitizers
        """
        self.clang_path = clang_path
        self.default_sanitizers = default_sanitizers or [SanitizerType.ADDRESS]
        
        # 检查Clang是否可用
        self.available = self._check_availability()
        
        # 统计信息
        self.stats = {
            'total_runs': 0,
            'error_detected': 0,
            'sanitizer_runs': {
                SanitizerType.ADDRESS: 0,
                SanitizerType.MEMORY: 0,
                SanitizerType.THREAD: 0,
                SanitizerType.UNDEFINED: 0,
                SanitizerType.LEAK: 0
            }
        }
    
    def _check_availability(self) -> bool:
        """检查Clang是否可用"""
        try:
            result = subprocess.run(
                [self.clang_path, "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def compile_with_sanitizer(self,
                               source_file: str,
                               output_file: str,
                               sanitizers: Optional[List[SanitizerType]] = None,
                               optimization_level: str = "O1") -> Tuple[bool, List[str]]:
        """
        使用sanitizer编译代码
        
        Args:
            source_file: 源文件
            output_file: 输出文件
            sanitizers: sanitizer列表
            optimization_level: 优化级别
            
        Returns:
            (是否成功, 错误列表)
        """
        if not self.available:
            return False, ["Clang不可用"]
        
        # 使用默认sanitizers
        if sanitizers is None:
            sanitizers = self.default_sanitizers
        
        # 构建编译参数
        args = [
            self.clang_path,
            f"-{optimization_level}",
            "-g",  # 生成调试信息
            "-fno-omit-frame-pointer",  # 保留帧指针
        ]
        
        # 添加sanitizer标志
        sanitizer_flags = []
        for sanitizer in sanitizers:
            flag = f"-fsanitize={sanitizer.value}"
            sanitizer_flags.append(flag)
            args.append(flag)
        
        # 添加其他标志
        args.extend([
            source_file,
            "-o", output_file
        ])
        
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, []
            else:
                return False, [result.stderr]
        
        except subprocess.TimeoutExpired:
            return False, ["编译超时"]
    
    def run_with_sanitizer(self,
                          executable: str,
                          args: Optional[List[str]] = None,
                          timeout: int = 60,
                          sanitizer_type: SanitizerType = SanitizerType.ADDRESS) -> SanitizerResult:
        """
        使用sanitizer运行程序
        
        Args:
            executable: 可执行文件
            args: 程序参数
            timeout: 超时时间（秒）
            sanitizer_type: sanitizer类型
            
        Returns:
            SanitizerResult: 检测结果
        """
        self.stats['total_runs'] += 1
        self.stats['sanitizer_runs'][sanitizer_type] += 1
        
        if not self.available:
            return SanitizerResult(
                sanitizer_type=sanitizer_type,
                success=False,
                passed=False,
                errors=["Clang不可用"],
                warnings=[],
                output="",
                metadata={}
            )
        
        # 运行程序
        try:
            result = subprocess.run(
                [executable] + (args or []),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=self._get_sanitizer_env(sanitizer_type)
            )
            
            output = result.stdout + "\n" + result.stderr
            
            # 检测错误
            errors = self._parse_sanitizer_errors(output, sanitizer_type)
            
            if errors:
                self.stats['error_detected'] += 1
            
            return SanitizerResult(
                sanitizer_type=sanitizer_type,
                success=True,
                passed=result.returncode == 0 and not errors,
                errors=errors,
                warnings=[],
                output=output,
                metadata={
                    'return_code': result.returncode,
                    'timeout': timeout
                }
            )
        
        except subprocess.TimeoutExpired:
            return SanitizerResult(
                sanitizer_type=sanitizer_type,
                success=True,
                passed=False,
                errors=["运行超时"],
                warnings=[],
                output="",
                metadata={'timeout': timeout}
            )
    
    def _get_sanitizer_env(self, sanitizer_type: SanitizerType) -> Dict:
        """获取sanitizer环境变量"""
        import os
        env = os.environ.copy()
        
        # ASan配置
        if sanitizer_type == SanitizerType.ADDRESS:
            env['ASAN_OPTIONS'] = 'detect_leaks=1:halt_on_error=0'
        
        # MSan配置
        elif sanitizer_type == SanitizerType.MEMORY:
            env['MSAN_OPTIONS'] = 'halt_on_error=0'
        
        # TSan配置
        elif sanitizer_type == SanitizerType.THREAD:
            env['TSAN_OPTIONS'] = 'halt_on_error=0'
        
        # UBSan配置
        elif sanitizer_type == SanitizerType.UNDEFINED:
            env['UBSAN_OPTIONS'] = 'halt_on_error=0'
        
        return env
    
    def _parse_sanitizer_errors(self, output: str, sanitizer_type: SanitizerType) -> List[str]:
        """解析sanitizer错误输出"""
        errors = []
        
        # ASan错误模式
        if sanitizer_type == SanitizerType.ADDRESS:
            patterns = [
                r'ERROR: AddressSanitizer: ([^\n]+)',
                r'heap-buffer-overflow',
                r'heap-use-after-free',
                r'stack-buffer-overflow',
                r'use-after-scope',
                r'memory leak'
            ]
        
        # MSan错误模式
        elif sanitizer_type == SanitizerType.MEMORY:
            patterns = [
                r'WARNING: MemorySanitizer: ([^\n]+)',
                r'use-of-uninitialized-value'
            ]
        
        # TSan错误模式
        elif sanitizer_type == SanitizerType.THREAD:
            patterns = [
                r'WARNING: ThreadSanitizer: ([^\n]+)',
                r'data race',
                r'lock-order-inversion'
            ]
        
        # UBSan错误模式
        elif sanitizer_type == SanitizerType.UNDEFINED:
            patterns = [
                r'runtime error: ([^\n]+)',
                r'signed integer overflow',
                r'division by zero',
                r'null pointer dereference'
            ]
        
        # LSan错误模式
        else:  # LEAK
            patterns = [
                r'ERROR: LeakSanitizer: ([^\n]+)',
                r'detected memory leaks'
            ]
        
        # 查找匹配
        for pattern in patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            errors.extend(matches)
        
        return errors
    
    def test_with_asan(self, source_file: str, output_file: str = "./a.out") -> SanitizerResult:
        """使用AddressSanitizer测试"""
        # 编译
        success, errors = self.compile_with_sanitizer(
            source_file,
            output_file,
            [SanitizerType.ADDRESS]
        )
        
        if not success:
            return SanitizerResult(
                sanitizer_type=SanitizerType.ADDRESS,
                success=False,
                passed=False,
                errors=errors,
                warnings=[],
                output="",
                metadata={}
            )
        
        # 运行
        return self.run_with_sanitizer(output_file, sanitizer_type=SanitizerType.ADDRESS)
    
    def test_with_ubsan(self, source_file: str, output_file: str = "./a.out") -> SanitizerResult:
        """使用UndefinedBehaviorSanitizer测试"""
        # 编译
        success, errors = self.compile_with_sanitizer(
            source_file,
            output_file,
            [SanitizerType.UNDEFINED]
        )
        
        if not success:
            return SanitizerResult(
                sanitizer_type=SanitizerType.UNDEFINED,
                success=False,
                passed=False,
                errors=errors,
                warnings=[],
                output="",
                metadata={}
            )
        
        # 运行
        return self.run_with_sanitizer(output_file, sanitizer_type=SanitizerType.UNDEFINED)
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            'available': self.available,
            'error_rate': (
                self.stats['error_detected'] /
                max(1, self.stats['total_runs'])
            )
        }


# 便捷函数
def test_memory_errors(source_file: str) -> SanitizerResult:
    """便捷函数：测试内存错误"""
    sanitizer = SanitizerIntegration()
    return sanitizer.test_with_asan(source_file)


if __name__ == "__main__":
    # 示例用法
    sanitizer = SanitizerIntegration()
    
    print("Sanitizers状态:")
    print(f"  Clang可用: {sanitizer.available}")
    print(f"  统计信息: {sanitizer.get_statistics()}")
# -*- coding: utf-8 -*-
"""
ZhC 编译器工具 - 统一的编译器调用和结果处理

提供跨后端的统一编译器调用接口。

作者：远
日期：2026-04-09
"""

import subprocess
import shlex
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
import tempfile
import logging

from .base import CompileResult, ToolNotFoundError

logger = logging.getLogger(__name__)


@dataclass
class CompilerConfig:
    """编译器配置"""

    executable: str  # 编译器可执行文件路径
    default_flags: List[str] = field(default_factory=list)  # 默认编译参数
    supported_formats: List[str] = field(default_factory=list)  # 支持的输出格式
    env: Dict[str, str] = field(default_factory=dict)  # 环境变量


@dataclass
class CompilerOutput:
    """编译器输出"""

    stdout: str
    stderr: str
    returncode: int
    duration_seconds: float


class CompilerRunner:
    """
    编译器运行器 - 统一处理编译器调用

    提供：
    - 统一的编译器调用接口
    - 智能错误解析
    - 超时控制
    - 输出重定向
    - 临时文件管理

    使用方式：
        runner = CompilerRunner(CompilerConfig(executable="gcc"))

        # 简单调用
        result = runner.run(["-O2", "-o", "output", "input.c"])

        # 带输入文件
        result = runner.run_with_input(
            ["-O2", "-o", "{output}"],
            input_path=Path("input.c"),
            output_path=Path("output")
        )
    """

    # 错误和警告的模式
    ERROR_PATTERNS = [
        r"error:",
        r"fatal error:",
        r"undefined reference",
        r"ld:",
    ]

    WARNING_PATTERNS = [
        r"warning:",
        r"[-W\w+]",
    ]

    def __init__(self, config: CompilerConfig, timeout: int = 300):
        """
        初始化编译器运行器

        Args:
            config: 编译器配置
            timeout: 超时时间（秒）
        """
        self.config = config
        self.timeout = timeout

    def check_available(self) -> bool:
        """检查编译器是否可用"""
        try:
            result = subprocess.run(
                [self.config.executable, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            subprocess.SubprocessError,
        ):
            return False

    def get_version(self) -> Optional[str]:
        """获取编译器版本"""
        try:
            result = subprocess.run(
                [self.config.executable, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.splitlines()[0]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    def run(
        self,
        args: List[str],
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> CompilerOutput:
        """
        运行编译器

        Args:
            args: 编译器参数列表
            cwd: 工作目录
            env: 环境变量

        Returns:
            CompilerOutput: 编译器输出
        """
        import time

        start_time = time.time()

        cmd = [self.config.executable] + args

        # 合并环境变量
        full_env = dict(self.config.env)
        if env:
            full_env.update(env)

        logger.debug(f"Running compiler: {' '.join(shlex.quote(str(c)) for c in cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(cwd) if cwd else None,
                env=full_env if full_env else None,
                timeout=self.timeout,
            )

            duration = time.time() - start_time
            logger.debug(f"Compiler finished in {duration:.2f}s")

            return CompilerOutput(
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                duration_seconds=duration,
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error(f"Compiler timeout after {duration:.2f}s")
            return CompilerOutput(
                stdout="",
                stderr=f"编译超时（{self.timeout}秒）",
                returncode=-1,
                duration_seconds=duration,
            )

        except FileNotFoundError:
            raise ToolNotFoundError(
                self.config.executable, f"请安装 {self.config.executable} 或检查 PATH"
            )

        except subprocess.SubprocessError as e:
            logger.error(f"Compiler error: {e}")
            return CompilerOutput(
                stdout="",
                stderr=str(e),
                returncode=-1,
                duration_seconds=time.time() - start_time,
            )

    def run_with_input(
        self,
        args_template: List[str],
        input_path: Path,
        output_path: Optional[Path] = None,
        cwd: Optional[Path] = None,
    ) -> CompilerOutput:
        """
        运行编译器（带输入/输出文件替换）

        Args:
            args_template: 参数模板，{input} 和 {output} 会被替换
            input_path: 输入文件路径
            output_path: 输出文件路径
            cwd: 工作目录

        Returns:
            CompilerOutput: 编译器输出
        """
        args = []
        for arg in args_template:
            if "{input}" in arg:
                arg = arg.replace("{input}", str(input_path))
            if "{output}" in arg and output_path:
                arg = arg.replace("{output}", str(output_path))
            args.append(arg)

        return self.run(args, cwd)

    def parse_output(self, output: CompilerOutput) -> Tuple[List[str], List[str]]:
        """
        解析编译器输出，提取错误和警告

        Args:
            output: 编译器输出

        Returns:
            Tuple[List[str], List[str]]: (errors, warnings)
        """
        errors = []
        warnings = []

        # 合并 stdout 和 stderr
        combined = output.stdout + "\n" + output.stderr

        for line in combined.splitlines():
            line_lower = line.lower()

            # 检查是否是错误
            if any(pattern.lower() in line_lower for pattern in self.ERROR_PATTERNS):
                errors.append(line.strip())
            # 检查是否是警告
            elif any(
                pattern.lower() in line_lower for pattern in self.WARNING_PATTERNS
            ):
                warnings.append(line.strip())

        return errors, warnings

    def to_compile_result(
        self,
        output: CompilerOutput,
        output_files: List[Path],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CompileResult:
        """
        转换为统一的 CompileResult

        Args:
            output: 编译器输出
            output_files: 生成的输出文件列表
            metadata: 额外的元数据

        Returns:
            CompileResult: 统一的编译结果对象
        """
        errors, warnings = self.parse_output(output)

        return CompileResult(
            success=output.returncode == 0,
            output_files=output_files,
            errors=errors,
            warnings=warnings,
            exit_code=output.returncode,
            metadata=metadata or {},
        )


class TemporaryFileManager:
    """临时文件管理器"""

    def __init__(self, keep_temp: bool = False):
        """
        初始化临时文件管理器

        Args:
            keep_temp: 是否保留临时文件（用于调试）
        """
        self.keep_temp = keep_temp
        self.temp_files: List[Path] = []

    def create_temp_file(self, suffix: str = "", prefix: str = "zhc_") -> Path:
        """
        创建临时文件

        Args:
            suffix: 文件后缀
            prefix: 文件前缀

        Returns:
            Path: 临时文件路径
        """
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        import os

        os.close(fd)
        temp_path = Path(path)
        self.temp_files.append(temp_path)
        return temp_path

    def create_temp_dir(self, prefix: str = "zhc_") -> Path:
        """
        创建临时目录

        Args:
            prefix: 目录前缀

        Returns:
            Path: 临时目录路径
        """
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        self.temp_files.append(temp_dir)
        return temp_dir

    def cleanup(self) -> None:
        """清理临时文件"""
        if self.keep_temp:
            logger.debug(f"Keeping temp files: {self.temp_files}")
            return

        for path in self.temp_files:
            try:
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    import shutil

                    shutil.rmtree(path)
            except Exception as e:
                logger.warning(f"Failed to clean up {path}: {e}")

        self.temp_files.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


def create_c_compiler_runner(
    compiler: str = "gcc",
    optimization_level: str = "O2",
    enable_warnings: bool = True,
) -> CompilerRunner:
    """
    创建 C 编译器运行器

    Args:
        compiler: 编译器名称
        optimization_level: 优化级别
        enable_warnings: 是否启用警告

    Returns:
        CompilerRunner: 编译器运行器
    """
    default_flags = [f"-{optimization_level}"]

    if enable_warnings:
        if compiler == "gcc":
            default_flags.extend(["-pedantic", "-Wall", "-Wextra"])
        elif compiler == "clang":
            default_flags.extend(["-Weverything", "-Wno-documentation", "-Wno-padded"])

    config = CompilerConfig(
        executable=compiler,
        default_flags=default_flags,
        supported_formats=["c", "o", "exe", "s"],
    )

    return CompilerRunner(config)


def create_wasm_compiler_runner(
    emscripten_path: str = "emcc",
    optimization_level: str = "O2",
) -> CompilerRunner:
    """
    创建 WASM 编译器运行器

    Args:
        emscripten_path: Emscripten 路径
        optimization_level: 优化级别

    Returns:
        CompilerRunner: 编译器运行器
    """
    config = CompilerConfig(
        executable=emscripten_path,
        default_flags=[f"-{optimization_level}"],
        supported_formats=["wasm", "js", "html"],
    )

    return CompilerRunner(config, timeout=600)

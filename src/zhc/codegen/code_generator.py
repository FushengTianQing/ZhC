# -*- coding: utf-8 -*-
"""
ZhC 代码生成器

从 LLVM IR 生成目标文件 (.o) 或可执行文件 (.exe)。

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import logging
import os
import tempfile

from zhc.codegen.target_registry import TargetRegistry
from zhc.codegen.target_info import TargetInfo

logger = logging.getLogger(__name__)


class FileType(Enum):
    """输出文件类型"""

    OBJECT = "object"  # 目标文件 (.o)
    ASSEMBLY = "assembly"  # 汇编文件 (.s)
    EXECUTABLE = "executable"  # 可执行文件
    SHARED_LIBRARY = "shared"  # 共享库 (.so/.dylib/.dll)
    STATIC_LIBRARY = "static"  # 静态库 (.a)


@dataclass
class CodeGenOptions:
    """
    代码生成选项

    控制代码生成的各种行为。
    """

    # 目标配置
    target_triple: str = ""
    cpu: str = ""
    features: List[str] = field(default_factory=list)

    # 输出配置
    file_type: FileType = FileType.OBJECT
    output_path: str = ""

    # 优化配置
    optimization_level: int = 2  # 0-3
    debug_info: bool = False
    position_independent: bool = False

    # 链接配置
    link: bool = False
    linker_script: str = ""
    libraries: List[str] = field(default_factory=list)
    library_paths: List[str] = field(default_factory=list)

    # 高级选项
    relax_all: bool = True
    disable_tail_calls: bool = False
    fast_math: bool = False

    def get_feature_string(self) -> str:
        """获取特性字符串"""
        return ",".join(self.features)


@dataclass
class CodeGenResult:
    """
    代码生成结果

    封装代码生成的输出和状态。
    """

    success: bool
    output_path: str = ""
    object_data: bytes = b""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


class CodeGenerator:
    """
    代码生成器

    从 LLVM IR 生成目标代码。

    使用方式：
        # 基本用法
        gen = CodeGenerator(target="x86_64")
        result = gen.generate(module, "output.o")

        # 自定义选项
        options = CodeGenOptions(
            file_type=FileType.OBJECT,
            optimization_level=3,
            debug_info=True,
        )
        gen = CodeGenerator(target="x86_64", options=options)
        result = gen.generate(module, "output.o")
    """

    def __init__(
        self,
        target: Optional[str] = None,
        options: Optional[CodeGenOptions] = None,
    ):
        """
        初始化代码生成器

        Args:
            target: 目标名称或三元组
            options: 代码生成选项
        """
        self.options = options or CodeGenOptions()

        # 解析目标
        if target:
            self.target = TargetRegistry.get(target)
            if self.target is None:
                raise ValueError(f"Unknown target: {target}")
        else:
            self.target = TargetRegistry.get_host_target()

        self.target_info = TargetInfo(self.target)
        self._llvm_context = None

    def generate(
        self,
        module: Any,
        output_path: str,
        file_type: Optional[FileType] = None,
    ) -> CodeGenResult:
        """
        生成目标代码

        Args:
            module: LLVM 模块 (ll.Module)
            output_path: 输出路径
            file_type: 输出文件类型（可选，覆盖选项）

        Returns:
            代码生成结果
        """
        result = CodeGenResult(success=False, output_path=output_path)

        try:
            # 确定文件类型
            ft = file_type or self.options.file_type

            # 设置目标三元组
            self._set_target_triple(module)

            # 生成代码
            if ft == FileType.OBJECT:
                data = self._generate_object(module)
                result.object_data = data
                self._write_output(data, output_path)

            elif ft == FileType.ASSEMBLY:
                data = self._generate_assembly(module)
                self._write_output(data.encode(), output_path)

            elif ft == FileType.EXECUTABLE:
                # 先生成目标文件，然后链接
                obj_path = output_path + ".o"
                data = self._generate_object(module)
                self._write_output(data, obj_path)
                self._link_executable([obj_path], output_path)
                os.remove(obj_path)

            result.success = True
            logger.info(f"Generated {ft.value} to {output_path}")

        except Exception as e:
            result.errors.append(str(e))
            logger.error(f"Code generation failed: {e}")

        return result

    def generate_object(self, module: Any) -> bytes:
        """
        生成目标文件内容

        Args:
            module: LLVM 模块

        Returns:
            目标文件二进制数据
        """
        return self._generate_object(module)

    def generate_assembly(self, module: Any) -> str:
        """
        生成汇编代码

        Args:
            module: LLVM 模块

        Returns:
            汇编代码字符串
        """
        return self._generate_assembly(module)

    def _set_target_triple(self, module: Any) -> None:
        """设置模块的目标三元组"""
        try:
            import importlib.util

            if importlib.util.find_spec("llvmlite") is not None:
                if hasattr(module, "triple"):
                    module.triple = self.target.triple

                if hasattr(module, "data_layout"):
                    module.data_layout = self.target_info.data_layout.string

        except ImportError:
            pass

    def _generate_object(self, module: Any) -> bytes:
        """生成目标文件"""
        try:
            import llvmlite.binding as llvm

            # 获取目标机器
            target_machine = self.target_info.get_llvm_target_machine()
            if target_machine is None:
                raise RuntimeError("Failed to create target machine")

            # 生成目标代码
            target_machine.set_asm_verbosity(True)

            # 添加模块到上下文
            llvm_ir = str(module)

            # 解析 IR
            mod = llvm.parse_assembly(llvm_ir)
            mod.verify()

            # 生成目标代码
            obj = target_machine.emit_object(mod)

            return obj

        except ImportError:
            logger.warning("llvmlite not available, using fallback")
            return self._fallback_generate_object(module)

    def _generate_assembly(self, module: Any) -> str:
        """生成汇编代码"""
        try:
            import llvmlite.binding as llvm

            # 获取目标机器
            target_machine = self.target_info.get_llvm_target_machine()
            if target_machine is None:
                raise RuntimeError("Failed to create target machine")

            # 解析 IR
            llvm_ir = str(module)
            mod = llvm.parse_assembly(llvm_ir)
            mod.verify()

            # 生成汇编
            asm = target_machine.emit_assembly(mod)

            return asm

        except ImportError:
            logger.warning("llvmlite not available, using fallback")
            return self._fallback_generate_assembly(module)

    def _fallback_generate_object(self, module: Any) -> bytes:
        """回退方法：使用外部工具生成目标文件"""
        import subprocess

        # 写入 IR 到临时文件
        with tempfile.NamedTemporaryFile(suffix=".ll", delete=False, mode="w") as f:
            f.write(str(module))
            ir_path = f.name

        try:
            # 使用 llc 生成目标文件
            obj_path = ir_path.replace(".ll", ".o")

            cmd = [
                "llc",
                "-filetype=obj",
                f"-mtriple={self.target.triple}",
                "-o",
                obj_path,
                ir_path,
            ]

            subprocess.run(cmd, check=True, capture_output=True)

            # 读取目标文件
            with open(obj_path, "rb") as f:
                return f.read()

        finally:
            # 清理临时文件
            if os.path.exists(ir_path):
                os.remove(ir_path)
            obj_path = ir_path.replace(".ll", ".o")
            if os.path.exists(obj_path):
                os.remove(obj_path)

    def _fallback_generate_assembly(self, module: Any) -> str:
        """回退方法：使用外部工具生成汇编"""
        import subprocess

        # 写入 IR 到临时文件
        with tempfile.NamedTemporaryFile(suffix=".ll", delete=False, mode="w") as f:
            f.write(str(module))
            ir_path = f.name

        try:
            # 使用 llc 生成汇编
            asm_path = ir_path.replace(".ll", ".s")

            cmd = [
                "llc",
                "-filetype=asm",
                f"-mtriple={self.target.triple}",
                "-o",
                asm_path,
                ir_path,
            ]

            subprocess.run(cmd, check=True, capture_output=True)

            # 读取汇编文件
            with open(asm_path, "r") as f:
                return f.read()

        finally:
            # 清理临时文件
            if os.path.exists(ir_path):
                os.remove(ir_path)
            asm_path = ir_path.replace(".ll", ".s")
            if os.path.exists(asm_path):
                os.remove(asm_path)

    def _write_output(self, data: bytes, path: str) -> None:
        """写入输出文件"""
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

        with open(path, "wb") as f:
            f.write(data)

    def _link_executable(self, object_files: List[str], output_path: str) -> None:
        """链接可执行文件"""
        import subprocess

        linker = self.target_info.get_linker_name()

        cmd = [linker]

        # 添加目标特定选项
        if self.target.os.name == "LINUX":
            cmd.extend(["-o", output_path])
            cmd.extend(object_files)
            cmd.extend(["-lc", "-dynamic-linker", "/lib64/ld-linux-x86-64.so.2"])

        elif self.target.os.name == "DARWIN":
            cmd.extend(["-o", output_path])
            cmd.extend(object_files)
            cmd.extend(["-lSystem"])

        elif self.target.os.name == "WINDOWS":
            cmd.extend([f"/OUT:{output_path}"])
            cmd.extend(object_files)
            cmd.extend(["/ENTRY:main"])

        # 运行链接器
        subprocess.run(cmd, check=True, capture_output=True)

    def get_target_info(self) -> TargetInfo:
        """获取目标信息"""
        return self.target_info

    def get_supported_features(self) -> List[str]:
        """获取支持的特性列表"""
        return self.target.default_features

    def set_cpu(self, cpu: str) -> None:
        """设置目标 CPU"""
        self.options.cpu = cpu

    def set_features(self, features: List[str]) -> None:
        """设置目标特性"""
        self.options.features = features

    def set_optimization_level(self, level: int) -> None:
        """设置优化级别 (0-3)"""
        self.options.optimization_level = max(0, min(3, level))

    def enable_debug_info(self, enable: bool = True) -> None:
        """启用/禁用调试信息"""
        self.options.debug_info = enable

    def enable_position_independent(self, enable: bool = True) -> None:
        """启用/禁用位置无关代码"""
        self.options.position_independent = enable

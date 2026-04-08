#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZhC C 后端 - IR 到 C 代码转换器

将 IR 程序转换为 C 代码，然后调用 GCC/Clang 编译为目标文件。

架构：
IRProgram → CBackend → C代码 → GCC/Clang → 目标文件

作者：远
日期：2026-04-08
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, TYPE_CHECKING

from .base import (
    BackendBase,
    BackendCapabilities,
    CompileOptions,
    CompileResult,
    OutputFormat,
    BackendError,
    ToolNotFoundError,
)

if TYPE_CHECKING:
    from zhc.ir.program import IRProgram


class CBackend(BackendBase):
    """
    C 后端 - IR → C 代码 → 目标文件

    工作流程：
    1. IRProgram → C 代码（IRToCConverter）
    2. C 代码 → 目标文件（GCC/Clang）

    支持的输出格式：
    - C 源码 (.c)
    - 目标文件 (.o)
    - 可执行文件
    - 静态库 (.a)
    - 共享库 (.so)
    """

    # 类型映射表
    TYPE_MAP = {
        "整数型": "int",
        "短整型": "short",
        "长整型": "long",
        "字符型": "char",
        "浮点型": "float",
        "双精度浮点型": "double",
        "布尔型": "int",
        "空类型": "void",
        "字符串型": "char*",
    }

    def __init__(self, compiler: str = "gcc"):
        """
        初始化 C 后端

        Args:
            compiler: C 编译器路径（gcc, clang, arm-gcc 等）
        """
        self.compiler = compiler
        self._check_compiler_available()

    def _create_debug_listener(
        self,
        source_file: str,
        output_file: str = "debug.json"
    ):
        """
        创建 C 后端专用调试监听器

        Args:
            source_file: 源文件路径
            output_file: 输出文件路径

        Returns:
            CDebugListener: C 后端调试监听器
        """
        from .c_debug_listener import CDebugListener
        return CDebugListener(source_file=source_file, output_file=output_file)

    @property
    def name(self) -> str:
        return "c"

    @property
    def description(self) -> str:
        return f"C 后端 ({self.compiler})"

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            supports_jit=False,
            supports_debug=True,
            supports_optimization=True,
            supports_cross_compile=True,
            target_platforms=[
                "x86_64-linux",
                "x86_64-macos",
                "x86_64-windows",
                "arm-linux",
                "aarch64-linux",
                "aarch64-macos",
            ],
            output_formats=[
                OutputFormat.C_CODE,
                OutputFormat.OBJECT,
                OutputFormat.EXECUTABLE,
                OutputFormat.STATIC_LIB,
                OutputFormat.SHARED_LIB,
            ],
            required_tools=[self.compiler],
        )

    def compile(
        self,
        ir: "IRProgram",
        output_path: Path,
        options: Optional[CompileOptions] = None,
    ) -> CompileResult:
        """
        编译 IR 到目标文件

        Args:
            ir: IR 程序
            output_path: 输出路径
            options: 编译选项

        Returns:
            CompileResult: 编译结果
        """
        options = options or CompileOptions()

        # 设置调试信息生成
        debug_manager = self._setup_debug(ir, options)

        # 1. IR → C 代码（发射调试事件）
        c_code = self._generate_c_code(ir, debug_manager)

        # 2. 写入临时 C 文件
        c_file = output_path.with_suffix(".c")
        c_file.write_text(c_code)

        # 3. 根据输出格式选择编译方式
        if options.output_format == OutputFormat.C_CODE:
            # 只输出 C 代码
            return CompileResult(
                success=True,
                output_files=[c_file],
                errors=[],
                warnings=[],
            )

        # 4. 调用编译器
        return self._compile_c_file(c_file, output_path, options)

    def _generate_c_code(
        self,
        ir: "IRProgram",
        debug_manager: Optional[Any] = None
    ) -> str:
        """
        从 IR 生成 C 代码

        Args:
            ir: IR 程序
            debug_manager: 调试管理器（可选）

        Returns:
            str: C 代码
        """
        # 获取源文件路径
        source_file = getattr(ir, 'source_file', 'unknown.zhc')

        # 发射编译单元调试事件
        self._emit_compile_unit_debug(
            debug_manager,
            name=ir.name if hasattr(ir, 'name') else 'main',
            source_file=source_file,
            comp_dir=''
        )

        lines = [
            "// 由 ZhC C 后端生成",
            "#include <stdio.h>",
            "#include <stdlib.h>",
            "#include <string.h>",
            "",
        ]

        # 生成函数声明
        for func in ir.functions:
            lines.append(self._generate_function_declaration(func))

        lines.append("")

        # 生成函数实现（发射调试事件）
        addr_counter = 0  # 模拟地址计数器
        for func in ir.functions:
            func_start_addr = addr_counter
            func_lines = self._generate_function(func, debug_manager, addr_counter)
            lines.append(func_lines)
            lines.append("")
            addr_counter += len(func_lines.splitlines()) * 4  # 模拟地址增长

        # 生成主函数（如果有）
        if ir.has_main:
            lines.append(self._generate_main_function(ir))

        # 完成调试信息
        self._finalize_debug(debug_manager)

        return "\n".join(lines)

    def _generate_function_declaration(self, func) -> str:
        """生成函数声明"""
        ret_type = self.TYPE_MAP.get(func.return_type, func.return_type)
        params = ", ".join(
            f"{self.TYPE_MAP.get(p.type, p.type)} {p.name}"
            for p in func.params
        )
        if not params:
            params = "void"
        return f"{ret_type} {func.name}({params});"

    def _generate_function(
        self,
        func,
        debug_manager: Optional[Any] = None,
        start_addr: int = 0
    ) -> str:
        """
        生成函数实现

        Args:
            func: IR 函数
            debug_manager: 调试管理器（可选）
            start_addr: 起始地址

        Returns:
            str: 函数实现的 C 代码
        """
        # 获取函数行号（从第一个基本块获取）
        start_line = 1
        end_line = 1

        # 发射函数调试事件
        params = [
            {'name': p.name, 'type': p.type, 'line': start_line}
            for p in func.params
        ]
        self._emit_function_debug(
            debug_manager,
            name=func.name,
            start_line=start_line,
            end_line=end_line,
            start_addr=start_addr,
            end_addr=start_addr + 100,  # 估算
            return_type=func.return_type,
            parameters=params
        )

        # 发射参数调试事件
        addr_offset = 8  # 假设参数从 rbp+8 开始
        for p in func.params:
            self._emit_variable_debug(
                debug_manager,
                name=p.name,
                type_name=p.type,
                line_number=start_line,
                address=start_addr + addr_offset,
                is_parameter=True
            )
            addr_offset += 8

        lines = []

        # 函数头
        ret_type = self.TYPE_MAP.get(func.return_type, func.return_type)
        params_str = ", ".join(
            f"{self.TYPE_MAP.get(p.type, p.type)} {p.name}"
            for p in func.params
        )
        if not params_str:
            params_str = "void"
        lines.append(f"{ret_type} {func.name}({params_str}) {{")

        # 函数体
        addr_counter = start_addr + 16  # 假设从 rbp+16 开始局部变量
        for block in func.blocks:
            for inst in block.instructions:
                inst_code = self._generate_instruction(inst, debug_manager, addr_counter)
                lines.append(f"    {inst_code}")
                addr_counter += 4

        # 函数尾
        lines.append("}")
        return "\n".join(lines)

    def _generate_instruction(
        self,
        inst,
        debug_manager: Optional[Any] = None,
        addr: int = 0
    ) -> str:
        """
        生成指令的 C 代码

        Args:
            inst: IR 指令
            debug_manager: 调试管理器（可选）
            addr: 当前地址

        Returns:
            str: C 代码
        """
        # 发射行号映射调试事件
        line_number = getattr(inst, 'line_number', 0)
        if line_number > 0:
            self._emit_line_mapping_debug(
                debug_manager,
                line_number=line_number,
                address=addr
            )

        # 简化实现，实际需要完整的 IR → C 映射
        opcode = inst.opcode.name

        if opcode == "ADD":
            return f"{inst.result} = {inst.operands[0]} + {inst.operands[1]};"
        elif opcode == "SUB":
            return f"{inst.result} = {inst.operands[0]} - {inst.operands[1]};"
        elif opcode == "MUL":
            return f"{inst.result} = {inst.operands[0]} * {inst.operands[1]};"
        elif opcode == "DIV":
            return f"{inst.result} = {inst.operands[0]} / {inst.operands[1]};"
        elif opcode == "RET":
            if inst.operands:
                return f"return {inst.operands[0]};"
            return "return;"
        elif opcode == "CALL":
            args = ", ".join(inst.operands)
            if inst.result:
                return f"{inst.result} = {inst.function_name}({args});"
            return f"{inst.function_name}({args});"
        elif opcode == "LOAD":
            return f"{inst.result} = *{inst.operands[0]};"
        elif opcode == "STORE":
            return f"*{inst.operands[0]} = {inst.operands[1]};"
        elif opcode == "ALLOC":
            # 发射变量调试事件
            if hasattr(inst, 'result') and hasattr(inst, 'type'):
                self._emit_variable_debug(
                    debug_manager,
                    name=inst.result,
                    type_name=inst.type,
                    line_number=line_number,
                    address=addr
                )
            return f"{inst.result} = malloc(sizeof({inst.type}));"

        return f"// 未实现的指令: {opcode}"

    def _generate_main_function(self, ir: "IRProgram") -> str:
        """生成主函数"""
        return """
int main(int argc, char** argv) {
    // ZhC 程序入口
    return 0;
}
"""

    def _compile_c_file(
        self,
        c_file: Path,
        output_path: Path,
        options: CompileOptions,
    ) -> CompileResult:
        """
        调用编译器编译 C 文件

        Args:
            c_file: C 源文件
            output_path: 输出路径
            options: 编译选项

        Returns:
            CompileResult: 编译结果
        """
        cmd = [self.compiler]

        # 优化级别
        cmd.append(f"-{options.optimization_level}")

        # 调试信息
        if options.debug:
            cmd.append("-g")

        # 目标平台
        if options.target:
            cmd.extend(["--target", options.target])

        # 输出格式
        if options.output_format == OutputFormat.OBJECT:
            cmd.extend(["-c", "-o", str(output_path)])
        elif options.output_format == OutputFormat.EXECUTABLE:
            cmd.extend(["-o", str(output_path)])
        elif options.output_format == OutputFormat.SHARED_LIB:
            cmd.extend(["-shared", "-fPIC", "-o", str(output_path)])
        else:
            cmd.extend(["-o", str(output_path)])

        # 输入文件
        cmd.append(str(c_file))

        # 额外标志
        cmd.extend(options.extra_flags)

        # 执行编译
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

            errors = []
            warnings = []

            if proc.stderr:
                for line in proc.stderr.splitlines():
                    if "error" in line.lower():
                        errors.append(line)
                    elif "warning" in line.lower():
                        warnings.append(line)

            return CompileResult(
                success=proc.returncode == 0,
                output_files=[output_path] if proc.returncode == 0 else [],
                errors=errors,
                warnings=warnings,
                exit_code=proc.returncode,
            )

        except FileNotFoundError:
            raise ToolNotFoundError(
                self.compiler,
                f"请安装 {self.compiler} 或指定正确的编译器路径",
            )

    def _check_compiler_available(self) -> None:
        """检查编译器是否可用"""
        try:
            proc = subprocess.run(
                [self.compiler, "--version"],
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                raise ToolNotFoundError(
                    self.compiler,
                    f"{self.compiler} 不可用",
                )
        except FileNotFoundError:
            raise ToolNotFoundError(
                self.compiler,
                f"请安装 {self.compiler}",
            )

    def is_available(self) -> bool:
        """检查后端是否可用"""
        try:
            subprocess.run(
                [self.compiler, "--version"],
                capture_output=True,
            )
            return True
        except FileNotFoundError:
            return False

    def get_version(self) -> Optional[str]:
        """获取编译器版本"""
        try:
            proc = subprocess.run(
                [self.compiler, "--version"],
                capture_output=True,
                text=True,
            )
            if proc.returncode == 0:
                return proc.stdout.splitlines()[0]
        except FileNotFoundError:
            pass
        return None
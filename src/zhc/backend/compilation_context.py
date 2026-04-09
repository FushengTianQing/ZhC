# -*- coding: utf-8 -*-
"""
ZhC 后端编译上下文 - 共享编译状态

用于在指令编译过程中共享状态。

作者：远
日期：2026-04-09
"""

from typing import Dict, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    import llvmlite.ir as ll
    from zhc.ir.instructions import IRInstruction
    from zhc.ir.program import IRFunction


@dataclass
class CompilationContext:
    """
    编译上下文 - 在指令编译过程中共享状态

    属性：
    - module: LLVM 模块
    - functions: 函数映射表
    - blocks: 基本块映射表
    - values: 值映射表
    - string_constants: 字符串常量映射表
    - current_function: 当前编译的函数
    - current_block: 当前编译的基本块
    - type_mapper: 类型映射器
    """

    module: "ll.Module" = None
    functions: Dict[str, "ll.Function"] = field(default_factory=dict)
    blocks: Dict[str, "ll.Block"] = field(default_factory=dict)
    values: Dict[str, "ll.Value"] = field(default_factory=dict)
    string_constants: Dict[str, "ll.GlobalVariable"] = field(default_factory=dict)
    current_function: Optional["IRFunction"] = None
    current_block: Optional["ll.Block"] = None

    def get_value(self, operand) -> "ll.Value":
        """
        获取 LLVM 值

        Args:
            operand: 操作数（可能是字符串、IRValue 等）

        Returns:
            ll.Value: LLVM 值
        """
        import llvmlite.ir as ll

        # 如果是 None
        if operand is None:
            return ll.Constant(ll.IntType(32), 0)

        # 如果是字符串
        if isinstance(operand, str):
            # 检查是否是已存在的值
            if operand in self.values:
                return self.values[operand]

            # 检查是否是字符串常量（以引号开头）
            if operand.startswith('"') and operand.endswith('"'):
                return self._create_global_string(operand[1:-1])

            # 检查是否是数字常量
            try:
                return ll.Constant(ll.IntType(32), int(operand))
            except ValueError:
                pass

            # 检查是否是浮点数常量
            try:
                return ll.Constant(ll.FloatType(), float(operand))
            except ValueError:
                pass

            # 检查是否是变量名（% 开头）
            if operand.startswith("%"):
                name = operand[1:]
                if name in self.values:
                    return self.values[name]

            # 默认返回常量 0
            return ll.Constant(ll.IntType(32), 0)

        # 如果是 IRValue 对象
        if hasattr(operand, "name"):
            name = operand.name
            if name in self.values:
                return self.values[name]

            # 处理常量
            if hasattr(operand, "kind") and hasattr(operand, "const_value"):
                if operand.const_value is not None:
                    try:
                        return ll.Constant(ll.IntType(32), int(operand.const_value))
                    except (ValueError, TypeError):
                        try:
                            return ll.Constant(
                                ll.FloatType(), float(operand.const_value)
                            )
                        except (ValueError, TypeError):
                            pass

        # 如果有 value 属性
        if hasattr(operand, "value"):
            return self.get_value(operand.value)

        # 默认返回常量 0
        return ll.Constant(ll.IntType(32), 0)

    def store_result(self, instr: "IRInstruction", value: "ll.Value") -> None:
        """
        存储指令结果

        Args:
            instr: IR 指令
            value: LLVM 值
        """
        if hasattr(instr, "result") and instr.result:
            res_obj = instr.result[0]
            name = res_obj.name if hasattr(res_obj, "name") else str(res_obj)
            self.values[name] = value

    def get_result_name(self, instr: "IRInstruction") -> Optional[str]:
        """
        获取指令结果名称

        Args:
            instr: IR 指令

        Returns:
            Optional[str]: 结果名称
        """
        if hasattr(instr, "result") and instr.result:
            res_obj = instr.result[0]
            if hasattr(res_obj, "name"):
                return res_obj.name
            return str(res_obj)
        return None

    def get_block(self, label: str) -> "ll.Block":
        """
        获取基本块

        Args:
            label: 基本块标签

        Returns:
            ll.Block: LLVM 基本块
        """
        # 移除可能的 % 前缀
        if label.startswith("%"):
            label = label[1:]

        if label in self.blocks:
            return self.blocks[label]

        # 如果找不到，返回当前块
        if self.current_block:
            return self.current_block

        # 返回第一个块
        if self.blocks:
            return list(self.blocks.values())[0]

        raise ValueError(f"基本块 {label} 不存在")

    def get_function(self, name: str) -> Optional["ll.Function"]:
        """
        获取函数

        Args:
            name: 函数名

        Returns:
            Optional[ll.Function]: LLVM 函数
        """
        return self.functions.get(name)

    def _create_global_string(self, content: str) -> "ll.Value":
        """
        创建或获取全局字符串常量

        Args:
            content: 字符串内容（不含引号）

        Returns:
            ll.Value: 指向字符串的 i8* 指针
        """
        import llvmlite.ir as ll

        # 缓存检查
        if content in self.string_constants:
            return self.string_constants[content]

        # 获取 module
        if not self.module:
            raise RuntimeError("CompilationContext.module 未设置，无法创建全局字符串")

        # 创建唯一的全局变量名
        global_name = f".str.{len(self.string_constants)}"

        # 将字符串编码为 UTF-8 字节
        utf8_bytes = content.encode("utf-8")

        # 创建字符数组类型 [n x i8]
        byte_count = len(utf8_bytes) + 1  # +1 for null terminator
        char_array_type = ll.ArrayType(ll.IntType(8), byte_count)

        # 创建字节串（包含 null 终止符）
        byte_data = [ll.Constant(ll.IntType(8), b) for b in utf8_bytes]
        byte_data.append(ll.Constant(ll.IntType(8), 0))  # null terminator

        # 创建全局变量
        global_var = ll.GlobalVariable(self.module, char_array_type, global_name)
        global_var.linkage = "private"
        global_var.global_constant = True
        global_var.initializer = ll.Constant(char_array_type, byte_data)

        # 缓存全局变量（数组类型）
        self.string_constants[content] = global_var

        # 返回全局变量本身（调用方需要使用 GEP 获取 i8*）
        return global_var

    def get_type_from_operand(self, operand) -> "ll.Type":
        """
        从操作数获取类型

        Args:
            operand: 操作数

        Returns:
            ll.Type: LLVM 类型
        """
        import llvmlite.ir as ll

        if operand is None:
            return ll.IntType(32)

        # 如果有 type 属性
        if hasattr(operand, "type"):
            type_name = operand.type
            return self.get_llvm_type(type_name)

        if hasattr(operand, "ty"):
            type_name = operand.ty
            return self.get_llvm_type(type_name)

        return ll.IntType(32)

    def get_llvm_type(self, type_name: str) -> "ll.Type":
        """
        获取 LLVM 类型

        Args:
            type_name: 类型名

        Returns:
            ll.Type: LLVM 类型
        """
        import llvmlite.ir as ll

        TYPE_MAP = {
            "整数型": ll.IntType(32),
            "浮点型": ll.FloatType(),
            "双精度浮点型": ll.DoubleType(),
            "字符型": ll.IntType(8),
            "字节型": ll.IntType(8),
            "布尔型": ll.IntType(1),
            "空类型": ll.VoidType(),
            "i32": ll.IntType(32),
            "i64": ll.IntType(64),
            "i16": ll.IntType(16),
            "i8": ll.IntType(8),
            "i1": ll.IntType(1),
        }

        return TYPE_MAP.get(type_name, ll.IntType(32))

    def create_merge_block(self) -> "ll.Block":
        """
        创建合并块（用于条件分支）

        Returns:
            ll.Block: 合并块
        """
        if self.current_function:
            # 在当前函数中创建一个合并块
            merge_label = f"merge.{len(self.blocks)}"
            block = self.current_function.append_basic_block(merge_label)
            self.blocks[merge_label] = block
            return block
        raise ValueError("无法创建合并块：没有当前函数")

    def reset(self) -> None:
        """重置上下文"""
        self.values.clear()
        self.blocks.clear()
        self.current_function = None
        self.current_block = None

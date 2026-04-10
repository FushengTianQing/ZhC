# -*- coding: utf-8 -*-
"""
ZhC 后端编译上下文 - 共享编译状态

用于在指令编译过程中共享状态。

作者：远
日期：2026-04-09
"""

from typing import Dict, Optional, List, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from functools import reduce

if TYPE_CHECKING:
    import llvmlite.ir as ll
    from zhc.ir.instructions import IRInstruction
    from zhc.ir.program import IRFunction


@dataclass
class ArrayTypeInfo:
    """数组类型信息"""

    element_type: "ll.Type"  # 元素类型
    dimensions: List[int]  # 各维度大小 [N, M, K] 表示 [N][M][K]
    total_size: int  # 总元素数

    @property
    def ndim(self) -> int:
        """数组维度数"""
        return len(self.dimensions)

    @property
    def element_stride(self) -> int:
        """元素步长（最后一个维度的大小）"""
        return self.dimensions[-1] if self.dimensions else 1


@dataclass
class StructFieldInfo:
    """结构体字段信息"""

    name: str  # 字段名
    field_type: "ll.Type"  # 字段类型
    index: int  # 字段索引
    offset: int  # 字段偏移（字节）


@dataclass
class StructTypeInfo:
    """结构体类型信息"""

    name: str  # 结构体名称
    llvm_type: "ll.Type"  # LLVM 类型
    fields: Dict[str, StructFieldInfo]  # 字段名 -> 字段信息
    field_names: List[str]  # 字段名列表（保持顺序）

    def get_field(self, field_name: str) -> Optional[StructFieldInfo]:
        """获取字段信息"""
        return self.fields.get(field_name)

    def get_field_index(self, field_name: str) -> Optional[int]:
        """获取字段索引"""
        field_info = self.get_field(field_name)
        return field_info.index if field_info else None


class TypeInfoRegistry:
    """全局类型信息注册表

    记录数组和结构体的类型信息，用于 GEP 指令生成。
    """

    def __init__(self):
        self._array_info: Dict[str, ArrayTypeInfo] = {}
        self._struct_info: Dict[str, StructTypeInfo] = {}
        self._value_types: Dict[str, "ll.Type"] = {}  # 值 -> 类型映射

    def register_array(
        self, name: str, element_type: "ll.Type", dimensions: List[int]
    ) -> ArrayTypeInfo:
        """注册数组类型信息

        Args:
            name: 数组名称
            element_type: 元素 LLVM 类型
            dimensions: 各维度大小

        Returns:
            ArrayTypeInfo: 注册的数组类型信息
        """
        total_size = reduce(lambda a, b: a * b, dimensions, 1)
        info = ArrayTypeInfo(
            element_type=element_type, dimensions=dimensions, total_size=total_size
        )
        self._array_info[name] = info
        return info

    def register_struct(
        self, name: str, llvm_type: "ll.Type", fields: List[Tuple[str, "ll.Type"]]
    ) -> StructTypeInfo:
        """注册结构体类型信息

        Args:
            name: 结构体名称
            llvm_type: LLVM 结构体类型
            fields: 字段列表 [(字段名, 类型), ...]

        Returns:
            StructTypeInfo: 注册的结构体类型信息
        """
        field_dict: Dict[str, StructFieldInfo] = {}
        field_names = []

        for idx, (field_name, field_type) in enumerate(fields):
            field_info = StructFieldInfo(
                name=field_name,
                field_type=field_type,
                index=idx,
                offset=0,  # 简化处理，实际计算需要考虑对齐
            )
            field_dict[field_name] = field_info
            field_names.append(field_name)

        info = StructTypeInfo(
            name=name, llvm_type=llvm_type, fields=field_dict, field_names=field_names
        )
        self._struct_info[name] = info
        return info

    def get_array_info(self, name: str) -> Optional[ArrayTypeInfo]:
        """获取数组类型信息"""
        return self._array_info.get(name)

    def get_struct_info(self, name: str) -> Optional[StructTypeInfo]:
        """获取结构体类型信息"""
        return self._struct_info.get(name)

    def get_struct_field_offset(
        self, struct_type: str, field_name: str
    ) -> Optional[int]:
        """获取结构体字段偏移量

        Args:
            struct_type: 结构体类型名
            field_name: 字段名

        Returns:
            Optional[int]: 字段偏移量（字节），如果不存在返回 None
        """
        info = self._struct_info.get(struct_type)
        if info:
            field_info = info.get_field(field_name)
            return field_info.offset if field_info else None
        return None

    def get_array_element_stride(self, array_type: str) -> Optional[int]:
        """获取数组元素步长

        Args:
            array_type: 数组类型名

        Returns:
            Optional[int]: 元素步长，如果不存在返回 None
        """
        info = self._array_info.get(array_type)
        return info.element_stride if info else None

    def register_value_type(self, value_name: str, value_type: "ll.Type"):
        """注册值的类型

        Args:
            value_name: 值名称（如 %arr）
            value_type: LLVM 类型
        """
        self._value_types[value_name] = value_type

    def get_value_type(self, value_name: str) -> Optional["ll.Type"]:
        """获取值的类型

        Args:
            value_name: 值名称

        Returns:
            Optional[ll.Type]: LLVM 类型，如果不存在返回 None
        """
        return self._value_types.get(value_name)

    def infer_gep_result_type(
        self, base_type: "ll.Type", indices: List["ll.Type"]
    ) -> Optional["ll.Type"]:
        """推断 GEP 指令结果类型

        Args:
            base_type: 基指针类型
            indices: 索引类型列表

        Returns:
            Optional[ll.Type]: GEP 结果类型
        """
        import llvmlite.ir as ll

        current_type = base_type

        for idx_type in indices:
            # 解引用指针（兼容 opaque pointer）
            if isinstance(current_type, ll.PointerType):
                if (
                    hasattr(current_type, "pointee")
                    and current_type.pointee is not None
                ):
                    current_type = current_type.pointee
                else:
                    # opaque pointer 模式下无法推断 pointee 类型
                    return None

            # 如果是数组类型，获取元素类型
            if isinstance(current_type, ll.ArrayType):
                current_type = current_type.element

            # 如果是结构体类型，需要知道字段索引
            elif isinstance(current_type, ll.LiteralStructType):
                # 这里需要更多信息来确定字段类型
                # 简化处理：返回第一个字段类型
                if hasattr(current_type, "elements") and current_type.elements:
                    # 索引应该是常量
                    pass

        return current_type


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
    - type_registry: 类型信息注册表（用于 GEP 等指令）
    """

    module: "ll.Module" = None
    functions: Dict[str, "ll.Function"] = field(default_factory=dict)
    blocks: Dict[str, "ll.Block"] = field(default_factory=dict)
    values: Dict[str, "ll.Value"] = field(default_factory=dict)
    string_constants: Dict[str, "ll.GlobalVariable"] = field(default_factory=dict)
    current_function: Optional["IRFunction"] = None
    current_block: Optional["ll.Block"] = None
    type_registry: TypeInfoRegistry = field(default_factory=TypeInfoRegistry)

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
            # 【重要】数字常量检查必须优先！否则 '0' 会错误匹配 values['0']
            try:
                int_val = int(operand)
                return ll.Constant(ll.IntType(32), int_val)
            except ValueError:
                pass

            # 浮点数常量
            try:
                float_val = float(operand)
                return ll.Constant(ll.FloatType(), float_val)
            except ValueError:
                pass

            # 检查是否是已存在的值
            if operand in self.values:
                return self.values[operand]

            # 检查是否是字符串常量（以引号开头）
            if operand.startswith('"') and operand.endswith('"'):
                return self._create_global_string(operand[1:-1])

            # 检查是否是浮点数常量
            try:
                float_val = float(operand)
                return ll.Constant(ll.FloatType(), float_val)
            except ValueError:
                pass

            # 检查是否是变量名（% 开头）
            if operand.startswith("%"):
                name = operand[1:]
                if name in self.values:
                    return self.values[name]

            # 默认返回常量 0
            return ll.Constant(ll.IntType(32), 0)

        # 如果是 IRValue 对象（如 GEP/LOAD 的 operand 是 IRValue）
        if hasattr(operand, "name"):
            name = operand.name

            # 【重要】常量 IRValue 必须优先处理，避免 '0' 被回退匹配到 '%0'
            if hasattr(operand, "kind") and hasattr(operand, "const_value"):
                if operand.const_value is not None:
                    return self._create_constant_from_irvalue(operand)

            # 优先精确查找（含 % 前缀，如 '%0'）
            if name in self.values:
                return self.values[name]
            # 回退：去掉 % 前缀查找（如 '0'）
            if name.startswith("%") and name[1:] in self.values:
                return self.values[name[1:]]
            # 回退：加上 % 前缀查找（如 '0' -> '%0'）
            if not name.startswith("%") and ("%" + name) in self.values:
                return self.values["%" + name]

            # 无法解析：name 不在 values 里，返回常量 0 而非返回 operand 本身
            return ll.Constant(ll.IntType(32), 0)

        # 如果有 value 属性
        if hasattr(operand, "value"):
            return self.get_value(operand.value)

        # 默认返回常量 0
        return ll.Constant(ll.IntType(32), 0)

    def _create_constant_from_irvalue(self, operand) -> "ll.Value":
        """
        从 IRValue 常量创建正确类型的 LLVM 常量。

        IR 生成器已在 _eval_binary 中修正常量的 ty 字段，
        因此这里直接使用 IRValue.ty 即可获得正确类型。

        Args:
            operand: IRValue 对象，kind==CONST，const_value 非空

        Returns:
            ll.Constant: 正确类型的 LLVM 常量
        """
        import llvmlite.ir as ll

        const_value = operand.const_value

        # 使用 IRValue 的 ty 字段确定类型（IR 生成器已保证正确）
        ty_name = getattr(operand, "ty", None)
        if ty_name:
            llvm_type = self.get_llvm_type(ty_name)
            if isinstance(llvm_type, ll.IntType):
                try:
                    return ll.Constant(llvm_type, int(const_value))
                except (ValueError, TypeError):
                    return ll.Constant(llvm_type, 0)
            if isinstance(llvm_type, (ll.FloatType, ll.DoubleType)):
                try:
                    return ll.Constant(llvm_type, float(const_value))
                except (ValueError, TypeError):
                    return ll.Constant(llvm_type, 0.0)

        # fallback：根据值的格式推断类型
        try:
            val_str = str(const_value)
            if "." in val_str or "f" in val_str.lower():
                return ll.Constant(ll.FloatType(), float(const_value))
            return ll.Constant(ll.IntType(32), int(const_value))
        except (ValueError, TypeError):
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

        if type_name in TYPE_MAP:
            return TYPE_MAP[type_name]

        # 处理数组类型，如 "整数型[5]" -> [5 x i32]
        if "[" in type_name and type_name.endswith("]"):
            base_str, bracket_str = type_name.rsplit("[", 1)
            size = int(bracket_str.rstrip("]"))
            # 递归获取元素类型（去除多余空格）
            base_type = base_str.strip()
            elem_llvm = self.get_llvm_type(base_type)
            return ll.ArrayType(elem_llvm, size)

        # 处理结构体类型：查找 IR 中定义的结构体
        struct_info = self.get_struct_type_info(type_name)
        if struct_info and hasattr(struct_info, "llvm_type") and struct_info.llvm_type:
            return struct_info.llvm_type

        # 检查是否有通过 register_struct 注册的结构体
        for st_name, st_info in self.type_registry._struct_info.items():
            if (
                st_name == type_name
                and hasattr(st_info, "llvm_type")
                and st_info.llvm_type
            ):
                return st_info.llvm_type

        return ll.IntType(32)

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

    # ============ 类型信息注册表相关方法 ============

    def register_array_type(
        self, name: str, element_type: "ll.Type", dimensions: List[int]
    ) -> ArrayTypeInfo:
        """注册数组类型信息

        Args:
            name: 数组名称
            element_type: 元素 LLVM 类型
            dimensions: 各维度大小

        Returns:
            ArrayTypeInfo: 注册的数组类型信息
        """
        return self.type_registry.register_array(name, element_type, dimensions)

    def register_struct_type(
        self, name: str, llvm_type: "ll.Type", fields: List[Tuple[str, "ll.Type"]]
    ) -> StructTypeInfo:
        """注册结构体类型信息

        Args:
            name: 结构体名称
            llvm_type: LLVM 结构体类型
            fields: 字段列表

        Returns:
            StructTypeInfo: 注册的结构体类型信息
        """
        return self.type_registry.register_struct(name, llvm_type, fields)

    def get_array_type_info(self, name: str) -> Optional[ArrayTypeInfo]:
        """获取数组类型信息"""
        return self.type_registry.get_array_info(name)

    def get_struct_type_info(self, name: str) -> Optional[StructTypeInfo]:
        """获取结构体类型信息"""
        return self.type_registry.get_struct_info(name)

    def register_value_type(self, value_name: str, value_type: "ll.Type"):
        """注册值的类型"""
        self.type_registry.register_value_type(value_name, value_type)

    def get_value_type(self, value_name: str) -> Optional["ll.Type"]:
        """获取值的类型"""
        return self.type_registry.get_value_type(value_name)

    def infer_gep_base_type(self, base_value: "ll.Value") -> Optional["ll.Type"]:
        """从基指针值推断其指向的类型

        Args:
            base_value: 基指针值

        Returns:
            Optional[ll.Type]: 指向的类型
        """
        import llvmlite.ir as ll

        if hasattr(base_value, "type"):
            ptr_type = base_value.type
            if isinstance(ptr_type, ll.PointerType):
                # 兼容 opaque pointer：有 pointee 则返回，否则返回 None
                if hasattr(ptr_type, "pointee") and ptr_type.pointee is not None:
                    return ptr_type.pointee
        return None

    def create_gep_constant_index(self, value: int) -> "ll.Value":
        """创建 GEP 指令使用的常量索引

        Args:
            value: 索引值

        Returns:
            ll.Value: i32 常量
        """
        import llvmlite.ir as ll

        return ll.Constant(ll.IntType(32), value)

    # ============ GEP 指令辅助方法 ============

    def _fold_constant_indices(
        self, indices: List["ll.Value"]
    ) -> Tuple[List["ll.Value"], int]:
        """常量折叠：尝试将多个连续索引合并

        Args:
            indices: 索引列表

        Returns:
            Tuple[List[ll.Value], int]: (处理后的索引, 合并的偏移量)
        """
        import llvmlite.ir as ll

        merged_offset = 0
        result_indices = []

        for idx in indices:
            if isinstance(idx, ll.Constant) and isinstance(idx.type, ll.IntType):
                # 如果是常量整数，直接累加到偏移量
                merged_offset += idx.constant
            else:
                # 非常量索引，需要保留
                if merged_offset > 0:
                    # 插入合并后的偏移常量
                    result_indices.append(ll.Constant(ll.IntType(32), merged_offset))
                    merged_offset = 0
                result_indices.append(idx)

        return result_indices, merged_offset

    def _compute_array_element_offset(
        self, array_info: ArrayTypeInfo, indices: List["ll.Value"]
    ) -> Optional[int]:
        """计算数组成员偏移量（用于常量索引情况）

        Args:
            array_info: 数组类型信息
            indices: 索引列表

        Returns:
            Optional[int]: 元素偏移量（元素个数），如果无法计算返回 None
        """
        import llvmlite.ir as ll

        # 所有索引必须是常量
        const_indices = []
        for idx in indices:
            if isinstance(idx, ll.Constant) and isinstance(idx.type, ll.IntType):
                const_indices.append(idx.constant)
            else:
                return None  # 包含非常量索引，无法预计算

        # 计算偏移量
        # 例如 [3][4][5] 数组，索引 [i, j, k] 的偏移量是 i*4*5 + j*5 + k
        offset = 0
        stride = 1
        dimensions = array_info.dimensions

        for i, idx in enumerate(const_indices):
            # 验证边界
            if i < len(dimensions):
                if idx < 0 or idx >= dimensions[i]:
                    return None  # 越界
            offset += idx * stride
            if i < len(dimensions) - 1:
                stride *= dimensions[i]

        return offset

    def validate_gep_indices(
        self, ptr_type: "ll.Type", indices: List["ll.Value"]
    ) -> Tuple[bool, str]:
        """验证 GEP 索引有效性

        Args:
            ptr_type: 指针类型（指向数组/结构体）
            indices: 索引列表

        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        import llvmlite.ir as ll

        current_type = ptr_type

        # 第一个索引通常用于基地址
        indices_to_check = indices[1:] if len(indices) > 1 else []

        for i, idx in enumerate(indices_to_check):
            # 检查索引类型
            if isinstance(idx, ll.Constant):
                # 常量索引：检查是否越界
                if hasattr(idx, "constant") and isinstance(idx.constant, int):
                    if idx.constant < 0:
                        return False, f"索引 {i} 不能为负数"

            # 解引用当前类型（兼容 opaque pointer）
            if isinstance(current_type, ll.PointerType):
                if (
                    hasattr(current_type, "pointee")
                    and current_type.pointee is not None
                ):
                    current_type = current_type.pointee
                else:
                    break
            elif isinstance(current_type, ll.ArrayType):
                # 检查索引是否超过数组大小
                if isinstance(idx, ll.Constant) and hasattr(idx, "constant"):
                    if idx.constant >= current_type.count:
                        return False, f"索引 {i} 超出数组边界 ({current_type.count})"
                current_type = current_type.element
            elif isinstance(current_type, ll.LiteralStructType):
                # 结构体字段索引必须是常量
                if not isinstance(idx, ll.Constant):
                    return False, f"结构体字段索引必须是常量"
                field_idx = idx.constant
                if field_idx >= len(current_type.elements):
                    return False, f"结构体字段索引 {field_idx} 超出范围"
                if hasattr(current_type, "elements"):
                    current_type = current_type.elements[field_idx]
            else:
                return False, f"无法对基本类型进行索引"

        return True, ""

    def optimize_gep_indices(
        self, ptr: "ll.Value", indices: List["ll.Value"]
    ) -> Tuple["ll.Value", List["ll.Value"]]:
        """优化 GEP 索引

        移除不必要的零索引，合并常量索引。

        Args:
            ptr: 基指针
            indices: 索引列表

        Returns:
            Tuple[ll.Value, List[ll.Value]]: (优化后的基指针, 索引列表)
        """
        import llvmlite.ir as ll

        optimized_indices = []
        zero_count = 0

        for idx in indices:
            # 移除开头的零索引
            if (
                isinstance(idx, ll.Constant)
                and isinstance(idx.type, ll.IntType)
                and idx.constant == 0
            ):
                zero_count += 1
            else:
                # 遇到非零索引，停止移除
                if zero_count > 0:
                    # 重新添加被移除的零索引（除非后续有更多优化）
                    optimized_indices.extend(
                        [ll.Constant(ll.IntType(32), 0)] * zero_count
                    )
                    zero_count = 0
                optimized_indices.append(idx)

        return ptr, optimized_indices

    def generate_bounds_check(
        self,
        builder: "ll.IRBuilder",
        index: "ll.Value",
        array_size: int,
        context: "CompilationContext",
    ) -> "ll.Value":
        """【GEP-003】生成数组边界检查代码

        生成伪代码：
            if (index >= array_size || index < 0) {
                __zhc_panic("array index out of bounds");
            }

        Args:
            builder: IRBuilder
            index: 索引值
            array_size: 数组大小
            context: 编译上下文

        Returns:
            ll.Value: 检查后的索引值（如果通过检查）
        """
        import llvmlite.ir as ll

        # 创建基本块
        current_block = builder.block
        check_block = current_block.function.append_basic_block("bounds_check")
        ok_block = current_block.function.append_basic_block("bounds_ok")
        panic_block = current_block.function.append_basic_block("bounds_panic")

        # 跳转到检查块
        builder.branch(check_block)
        builder.position_at_end(check_block)

        # 检查条件：index < 0 OR index >= array_size
        zero = ll.Constant(ll.IntType(32), 0)
        size_const = ll.Constant(ll.IntType(32), array_size)

        # index < 0
        is_negative = builder.icmp_signed("<", index, zero, name="is_negative")

        # index >= array_size
        is_overflow = builder.icmp_signed(">=", index, size_const, name="is_overflow")

        # OR 条件
        is_out_of_bounds = builder.or_(
            is_negative, is_overflow, name="is_out_of_bounds"
        )

        # 条件分支
        builder.cbranch(is_out_of_bounds, panic_block, ok_block)

        # Panic 块：调用运行时错误函数
        builder.position_at_end(panic_block)

        # 声明 panic 函数
        panic_func = self._get_or_declare_panic_function(builder.module)
        if panic_func:
            # 创建错误消息字符串（使用全局变量指针）
            global_str = self._create_global_string("array index out of bounds")
            # 获取 i8* 指针（兼容 opaque pointer）
            pointee_type = getattr(global_str.type, "pointee", None)
            if pointee_type is not None and isinstance(pointee_type, ll.ArrayType):
                zero = ll.Constant(ll.IntType(32), 0)
                msg_ptr = builder.gep(global_str, [zero, zero], name="msg_ptr")
            else:
                i8_ptr_type = ll.PointerType(ll.IntType(8))
                msg_ptr = builder.bitcast(global_str, i8_ptr_type, name="msg_ptr")
            builder.call(panic_func, [msg_ptr], name="panic_call")

        builder.unreachable()

        # OK 块：继续执行
        builder.position_at_end(ok_block)

        return index

    def _get_or_declare_panic_function(
        self, module: "ll.Module"
    ) -> Optional["ll.Function"]:
        """获取或声明 panic 函数

        Args:
            module: LLVM 模块

        Returns:
            Optional[ll.Function]: panic 函数
        """
        import llvmlite.ir as ll

        func_name = "__zhc_panic"

        # 检查是否已声明
        for func in module.functions:
            if func.name == func_name:
                return func

        # 声明外部函数
        i8_ptr = ll.PointerType(ll.IntType(8))
        func_type = ll.FunctionType(ll.VoidType(), [i8_ptr])
        func = ll.Function(module, func_type, func_name)
        return func

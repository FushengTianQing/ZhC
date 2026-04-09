"""
结构体布局计算器

提供结构体内存布局计算、LLVM 类型映射和 GEP 优化。

创建日期: 2026-04-09
最后更新: 2026-04-09
维护者: ZHC开发团队
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple, Any
import llvmlite.ir as ll

if False:
    pass


# 平台对齐规则
@dataclass
class AlignmentRules:
    """平台对齐规则"""

    char_align: int = 1  # char = 1
    short_align: int = 2  # short = 2
    int_align: int = 4  # int = 4
    long_align: int = 8  # long = 8
    long_long_align: int = 8  # long long = 8
    float_align: int = 4  # float = 4
    double_align: int = 8  # double = 8
    pointer_align: int = 8  # pointer = 8
    max_align: int = 16  # 最大对齐


@dataclass
class StructMember:
    """结构体成员"""

    name: str  # 成员名
    type_name: str  # 类型名
    offset: int  # 偏移量
    size: int  # 大小
    alignment: int  # 对齐要求
    llvm_type: ll.Type  # LLVM 类型


@dataclass
class StructLayout:
    """结构体布局信息"""

    name: str  # 结构体名
    members: List[StructMember]  # 成员列表
    total_size: int  # 总大小
    alignment: int  # 对齐要求
    llvm_type: Optional[Any] = (
        None  # LLVM 类型 (LiteralStructType or IdentifiedStructType)
    )
    is_packed: bool = False  # 是否 packed


class StructLayoutCalculator:
    """
    结构体布局计算器

    根据目标平台的对齐规则计算结构体成员的偏移量和大小。
    """

    def __init__(self, target_platform: str = "linux"):
        """
        初始化计算器

        Args:
            target_platform: 目标平台 ("linux", "windows", "macos")
        """
        self.target_platform = target_platform
        self._layout_cache: Dict[str, StructLayout] = {}
        self._rules = self._get_alignment_rules()

    def _get_alignment_rules(self) -> AlignmentRules:
        """获取平台对齐规则"""
        if self.target_platform == "windows":
            return AlignmentRules(
                char_align=1,
                short_align=2,
                int_align=4,
                long_align=4,
                long_long_align=8,
                float_align=4,
                double_align=8,
                pointer_align=8,
                max_align=8,
            )
        elif self.target_platform == "macos":
            return AlignmentRules(
                char_align=1,
                short_align=2,
                int_align=4,
                long_align=8,  # macOS 上 long 是 8 字节
                long_long_align=8,
                float_align=4,
                double_align=8,
                pointer_align=8,
                max_align=16,
            )
        else:  # linux
            return AlignmentRules(
                char_align=1,
                short_align=2,
                int_align=4,
                long_align=8,
                long_long_align=8,
                float_align=4,
                double_align=8,
                pointer_align=8,
                max_align=16,
            )

    def calculate_layout(
        self,
        struct_name: str,
        member_types: List[Tuple[str, str]],  # [(name, type), ...]
        is_packed: bool = False,
    ) -> StructLayout:
        """
        计算结构体布局

        Args:
            struct_name: 结构体名
            member_types: 成员类型列表 [(成员名, 类型名), ...]
            is_packed: 是否 packed（不进行对齐）

        Returns:
            结构体布局信息
        """
        # 检查缓存
        cache_key = f"{struct_name}_{is_packed}"
        if cache_key in self._layout_cache:
            return self._layout_cache[cache_key]

        members = []
        current_offset = 0
        max_alignment = 1

        for member_name, type_name in member_types:
            size, alignment = self._get_type_size_and_align(type_name)

            if is_packed:
                # Packed 结构体：不需要对齐
                pass
            else:
                # 计算对齐偏移
                if current_offset % alignment != 0:
                    current_offset = (current_offset // alignment + 1) * alignment

            llvm_type = self._to_llvm_type(type_name)
            member = StructMember(
                name=member_name,
                type_name=type_name,
                offset=current_offset,
                size=size,
                alignment=alignment,
                llvm_type=llvm_type,
            )
            members.append(member)

            current_offset += size
            max_alignment = max(max_alignment, alignment)

        # 计算总大小（需要对齐到最大对齐
        if is_packed:
            total_size = current_offset
        else:
            if current_offset % max_alignment != 0:
                total_size = (current_offset // max_alignment + 1) * max_alignment
            else:
                total_size = current_offset

        layout = StructLayout(
            name=struct_name,
            members=members,
            total_size=total_size,
            alignment=max_alignment,
            is_packed=is_packed,
        )

        # 生成 LLVM 类型
        layout.llvm_type = self._create_llvm_struct_type(members, is_packed)

        self._layout_cache[cache_key] = layout
        return layout

    def _get_type_size_and_align(self, type_name: str) -> Tuple[int, int]:
        """
        获取类型的大小和对齐

        Args:
            type_name: 类型名

        Returns:
            (大小, 对齐)
        """
        rules = self._rules

        # 整数类型
        if type_name == "字符型":
            return 1, rules.char_align
        elif type_name in ("短整型", "无符号短整型"):
            return 2, rules.short_align
        elif type_name in ("整数型", "无符号整数型"):
            return 4, rules.int_align
        elif type_name in ("长整型", "无符号长整型"):
            return 8, rules.long_align
        elif type_name in ("长长整型", "无符号长长整型"):
            return 8, rules.long_long_align
        # 浮点类型
        elif type_name == "浮点型":
            return 4, rules.float_align
        elif type_name == "双精度浮点型":
            return 8, rules.double_align
        # 指针类型
        elif type_name.endswith("指针") or type_name.endswith("*"):
            return 8, rules.pointer_align
        # 布尔类型
        elif type_name == "布尔型":
            return 1, rules.char_align
        # 空类型
        elif type_name == "空型":
            return 1, rules.char_align
        # 默认
        else:
            return 8, rules.pointer_align

    def _to_llvm_type(self, type_name: str) -> ll.Type:
        """
        将 ZhC 类型转换为 LLVM 类型

        Args:
            type_name: ZhC 类型名

        Returns:
            LLVM 类型
        """
        if type_name == "字符型":
            return ll.IntType(8)
        elif type_name in ("短整型", "无符号短整型"):
            return ll.IntType(16)
        elif type_name in ("整数型", "无符号整数型"):
            return ll.IntType(32)
        elif type_name in ("长整型", "无符号长整型", "长长整型", "无符号长长整型"):
            return ll.IntType(64)
        elif type_name == "布尔型":
            return ll.IntType(8)
        elif type_name == "浮点型":
            return ll.FloatType()
        elif type_name == "双精度浮点型":
            return ll.DoubleType()
        elif type_name.endswith("指针") or type_name.endswith("*"):
            base_type_name = type_name.rstrip("指针").rstrip("*").strip()
            base_type = self._to_llvm_type(base_type_name)
            return ll.PointerType(base_type)
        elif type_name == "空型":
            return ll.VoidType()
        else:
            # 可能是嵌套结构体或其他复杂类型
            return ll.IntType(64)

    def _create_llvm_struct_type(
        self, members: List[StructMember], is_packed: bool
    ) -> ll.LiteralStructType:
        """
        创建 LLVM 结构体类型

        Args:
            members: 成员列表
            is_packed: 是否 packed

        Returns:
            LLVM 结构体类型
        """
        llvm_types = [m.llvm_type for m in members]
        return ll.LiteralStructType(llvm_types, packed=is_packed)

    def get_member_offset(
        self, layout: StructLayout, member_name: str
    ) -> Optional[int]:
        """
        获取成员偏移量

        Args:
            layout: 结构体布局
            member_name: 成员名

        Returns:
            偏移量，如果成员不存在则返回 None
        """
        for member in layout.members:
            if member.name == member_name:
                return member.offset
        return None

    def get_member_llvm_index(
        self, layout: StructLayout, member_name: str
    ) -> Optional[int]:
        """
        获取成员的 LLVM 索引

        Args:
            layout: 结构体布局
            member_name: 成员名

        Returns:
            成员索引，如果成员不存在则返回 None
        """
        for i, member in enumerate(layout.members):
            if member.name == member_name:
                return i
        return None


class LLVMStructTypeMapper:
    """
    LLVM 结构体类型映射器

    提供 ZhC 结构体到 LLVM 类型的映射和管理。
    """

    def __init__(self):
        """初始化映射器"""
        self._struct_types: Dict[str, ll.StructType] = {}
        self._layout_calculator = StructLayoutCalculator()

    def register_struct_type(
        self,
        struct_name: str,
        member_types: List[Tuple[str, str]],
        is_packed: bool = False,
    ) -> ll.LiteralStructType:
        """
        注册结构体类型

        Args:
            struct_name: 结构体名
            member_types: 成员类型列表
            is_packed: 是否 packed

        Returns:
            LLVM 结构体类型
        """
        layout = self._layout_calculator.calculate_layout(
            struct_name, member_types, is_packed
        )
        self._struct_types[struct_name] = layout.llvm_type
        return layout.llvm_type

    def get_struct_type(self, struct_name: str) -> Optional[ll.LiteralStructType]:
        """
        获取结构体类型

        Args:
            struct_name: 结构体名

        Returns:
            LLVM 结构体类型
        """
        return self._struct_types.get(struct_name)

    def get_struct_layout(self, struct_name: str) -> Optional[StructLayout]:
        """
        获取结构体布局

        Args:
            struct_name: 结构体名

        Returns:
            结构体布局
        """
        if struct_name in self._struct_types:
            # 重新计算布局（从缓存获取）
            return self._layout_calculator._layout_cache.get(struct_name)
        return None


class StructGepStrategy:
    """
    结构体 GEP 策略

    生成优化的结构体成员访问 GEP 指令。
    """

    def __init__(self, module: "ll.Module"):
        """
        初始化策略

        Args:
            module: LLVM 模块
        """
        self.module = module

    def create_member_gep(
        self,
        builder: "ll.IRBuilder",
        struct_ptr: ll.Value,
        member_index: int,
        struct_type: Any,
        name: str = "member",
    ) -> ll.Value:
        """
        创建结构体成员访问的 GEP

        Args:
            builder: IR 构建器
            struct_ptr: 结构体指针
            member_index: 成员索引
            struct_type: 结构体类型
            name: GEP 名称

        Returns:
            成员指针
        """
        # 使用 inbounds GEP 提升性能
        indices = [
            ll.Constant(ll.IntType(32), 0),  # 第一个索引是结构体本身
            ll.Constant(ll.IntType(32), member_index),  # 第二个索引是成员
        ]

        return builder.gep(struct_ptr, indices, name, inbounds=True)


class NestedStructGepStrategy:
    """
    嵌套结构体 GEP 策略

    处理嵌套结构体的成员访问，生成链式 GEP。
    """

    def __init__(self, module: "ll.Module"):
        """
        初始化策略

        Args:
            module: LLVM 模块
        """
        self.module = module
        self._struct_mapper = LLVMStructTypeMapper()

    def create_nested_member_gep(
        self,
        builder: "ll.IRBuilder",
        struct_ptr: ll.Value,
        member_path: List[int],  # [外层索引, 内层索引, ...]
        struct_type: Any,
        name: str = "nested_member",
    ) -> ll.Value:
        """
        创建嵌套结构体成员访问的 GEP

        Args:
            builder: IR 构建器
            struct_ptr: 结构体指针
            member_path: 成员路径
            struct_type: 结构体类型
            name: GEP 名称

        Returns:
            成员指针
        """
        result = struct_ptr

        for idx in member_path:
            indices = [ll.Constant(ll.IntType(32), 0), ll.Constant(ll.IntType(32), idx)]
            result = builder.gep(result, indices, name, inbounds=True)

        return result

    def parse_member_path(
        self,
        struct_name: str,
        member_access: str,  # e.g., "outer.inner.inner_field"
    ) -> List[int]:
        """
        解析成员访问路径为索引

        Args:
            struct_name: 结构体名
            member_access: 成员访问字符串

        Returns:
            索引列表
        """
        # 这需要结构体定义的完整信息
        # 这里返回一个占位实现
        return []


# 全局实例
_global_struct_mapper: Optional[LLVMStructTypeMapper] = None


def get_struct_mapper() -> LLVMStructTypeMapper:
    """获取全局结构体类型映射器"""
    global _global_struct_mapper
    if _global_struct_mapper is None:
        _global_struct_mapper = LLVMStructTypeMapper()
    return _global_struct_mapper


# 导出公共 API
__all__ = [
    "AlignmentRules",
    "StructMember",
    "StructLayout",
    "StructLayoutCalculator",
    "LLVMStructTypeMapper",
    "StructGepStrategy",
    "NestedStructGepStrategy",
    "get_struct_mapper",
]

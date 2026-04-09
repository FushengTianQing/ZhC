# -*- coding: utf-8 -*-
"""
ZhC 掩码处理模块

处理 SIMD 向量化中的掩码操作，包括：
- 尾部处理（处理不能整除的循环部分）
- 条件执行向量化
- 掩码生成和应用

作者：远
日期：2026-04-09
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MaskStrategy(Enum):
    """掩码策略"""

    NONE = "none"  # 不使用掩码
    TAIL = "tail"  # 仅处理尾部
    FULL = "full"  # 完全掩码
    PREDICATION = "predication"  # 使用谓词执行


@dataclass
class MaskInfo:
    """掩码信息"""

    strategy: MaskStrategy  # 使用的策略
    vector_width: int  # 向量宽度
    active_elements: int  # 活跃元素数量
    mask_value: Optional[int] = None  # 掩码值（如果已知）
    mask_type: str = "i1"  # 掩码类型

    def __str__(self) -> str:
        return f"MaskInfo(strategy={self.strategy.value}, width={self.vector_width}, active={self.active_elements})"


@dataclass
class TailHandlingResult:
    """尾部处理结果"""

    needs_tail_loop: bool  # 是否需要尾部循环
    main_loop_width: int  # 主循环宽度
    tail_width: int  # 尾部宽度
    tail_count: int  # 尾部元素数量
    prologue_instructions: List[str]  # 前导指令
    mask_setup_instructions: List[str]  # 掩码设置指令
    epilogue_instructions: List[str]  # 尾部处理指令


class MaskHandler:
    """
    掩码处理器

    管理 SIMD 向量化中的掩码操作和尾部处理。
    """

    def __init__(self, target_arch: str = "generic"):
        self.target_arch = target_arch
        self._temp_counter = 0

    def create_loop_masks(
        self,
        trip_count: int,
        vector_width: int,
        start_offset: int = 0,
    ) -> Tuple[str, str, str]:
        """
        创建循环掩码

        Args:
            trip_count: 总循环次数
            vector_width: 向量宽度
            start_offset: 起始偏移

        Returns:
            (main_mask, tail_mask, active_count) 元组
        """
        main_mask = self._generate_main_mask(vector_width)
        tail_count = (trip_count - start_offset) % vector_width
        tail_mask = self._generate_tail_mask(tail_count, vector_width)
        active_count = str(trip_count - start_offset)

        return main_mask, tail_mask, active_count

    def _generate_main_mask(self, width: int) -> str:
        """生成主循环掩码（全1）"""
        return (
            f"%mask.allones = shufflemask <{width} x i1> <{' '.join(['true'] * width)}>"
        )

    def _generate_tail_mask(self, active_count: int, width: int) -> str:
        """生成尾部掩码"""
        if active_count == 0:
            return f"%mask.zero = all ones <{width} x i1>"

        mask_parts = []
        for i in range(width):
            if i < active_count:
                mask_parts.append("true")
            else:
                mask_parts.append("false")

        mask_name = self._next_temp("mask.tail")
        return f"{mask_name} = shufflemask <{width} x i1> <{', '.join(mask_parts)}>"

    def calculate_tail_info(
        self,
        trip_count: Optional[int],
        vector_width: int,
        enable_tail_masking: bool = True,
    ) -> TailHandlingResult:
        """
        计算尾部处理信息

        Args:
            trip_count: 循环次数（如果已知）
            vector_width: 向量宽度
            enable_tail_masking: 是否启用尾部掩码

        Returns:
            尾部处理结果
        """
        if trip_count is None:
            return TailHandlingResult(
                needs_tail_loop=enable_tail_masking,
                main_loop_width=vector_width,
                tail_width=0,
                tail_count=0,
                prologue_instructions=[],
                mask_setup_instructions=[],
                epilogue_instructions=[],
            )

        remainder = trip_count % vector_width

        if remainder == 0:
            return TailHandlingResult(
                needs_tail_loop=False,
                main_loop_width=vector_width,
                tail_width=0,
                tail_count=0,
                prologue_instructions=[],
                mask_setup_instructions=[],
                epilogue_instructions=[],
            )

        if enable_tail_masking:
            return self._create_masked_tail(trip_count, vector_width, remainder)
        else:
            return self._create_scalar_tail(trip_count, vector_width, remainder)

    def _create_masked_tail(
        self,
        trip_count: int,
        vector_width: int,
        remainder: int,
    ) -> TailHandlingResult:
        """创建掩码尾部处理"""
        prologue = []
        mask_setup = []
        epilogue = []

        mask_setup.append(f"; 设置尾部掩码: {remainder}/{vector_width} 活跃")
        mask_setup.append(
            f"%tail.count = insertelement <{vector_width} x i32> zeroinitializer, "
            f"i32 {remainder}, i32 0"
        )
        mask_setup.append(
            f"%trip.count.vec = splatvector <{vector_width} x i32> %trip.count"
        )
        mask_setup.append(
            f"%indices = seq <{vector_width} x i32> 0, 1, 2, {vector_width - 1}"
        )
        mask_setup.append(
            f"%in.bounds = icmp ult <{vector_width} x i32> %indices, %trip.count.vec"
        )

        return TailHandlingResult(
            needs_tail_loop=True,
            main_loop_width=vector_width,
            tail_width=vector_width,
            tail_count=remainder,
            prologue_instructions=prologue,
            mask_setup_instructions=mask_setup,
            epilogue_instructions=epilogue,
        )

    def _create_scalar_tail(
        self,
        trip_count: int,
        vector_width: int,
        remainder: int,
    ) -> TailHandlingResult:
        """创建标量尾部循环"""
        prologue = []
        epilogue = []

        if remainder > 0:
            epilogue.append(f"; 标量尾部循环 ({remainder} 迭代)")
            epilogue.append("br label %tail.loop")
            epilogue.append("tail.loop:")
            epilogue.append(
                f"%tail.i = phi i32 [ 0, %vector.loop ], [ %tail.i.next, %tail.loop ]"
            )
            epilogue.append(f"%tail.i.next = add i32 %tail.i, 1")
            epilogue.append(f"%tail.cond = icmp ult i32 %tail.i, {remainder}")
            epilogue.append(f"br i1 %tail.cond, label %tail.body, label %tail.end")
            epilogue.append("tail.body:")
            epilogue.append("br label %tail.loop")
            epilogue.append("tail.end:")

        return TailHandlingResult(
            needs_tail_loop=True,
            main_loop_width=vector_width,
            tail_width=1,
            tail_count=remainder,
            prologue_instructions=prologue,
            mask_setup_instructions=[],
            epilogue_instructions=epilogue,
        )

    def build_vector_compare(
        self,
        vec_a: str,
        vec_b: str,
        predicate: str,
        vec_type: str,
    ) -> str:
        """
        构建向量比较

        Args:
            vec_a: 第一个向量
            vec_b: 第二个向量
            predicate: 比较谓词 (eq, ne, lt, le, gt, ge)
            vec_type: 向量类型

        Returns:
            比较指令
        """
        pred_map = {
            "eq": "eq",
            "ne": "ne",
            "lt": "slt",
            "le": "sle",
            "gt": "sgt",
            "ge": "sge",
            "ult": "ult",
            "ule": "ule",
            "ugt": "ugt",
            "uge": "uge",
        }

        llvm_pred = pred_map.get(predicate.lower(), "eq")
        result_name = self._next_temp("cmp.result")

        return f"{result_name} = icmp {llvm_pred} {vec_type} {vec_a}, {vec_b}"

    def build_masked_load(
        self,
        ptr: str,
        mask: str,
        passthru: str,
        vec_type: str,
    ) -> str:
        """
        构建掩码加载

        Args:
            ptr: 指针
            mask: 掩码
            passthru: 透传值
            vec_type: 向量类型

        Returns:
            加载指令
        """
        result_name = self._next_temp("masked.load")
        elem_count = self._get_element_count(vec_type)
        return (
            f"{result_name} = call {vec_type} @llvm.masked.load("
            f"{vec_type}* {ptr}, i32 1, "
            f"<{elem_count} x i1> {mask}, "
            f"{vec_type} {passthru})"
        )

    def build_masked_store(
        self,
        value: str,
        ptr: str,
        mask: str,
        vec_type: str,
    ) -> str:
        """
        构建掩码存储

        Args:
            value: 要存储的值
            ptr: 指针
            mask: 掩码
            vec_type: 向量类型

        Returns:
            存储指令
        """
        elem_count = self._get_element_count(vec_type)
        return (
            f"call void @llvm.masked.store("
            f"{vec_type} {value}, {vec_type}* {ptr}, i32 1, "
            f"<{elem_count} x i1> {mask})"
        )

    def build_vector_blend(
        self,
        vec_a: str,
        vec_b: str,
        mask: str,
        vec_type: str,
    ) -> str:
        """
        构建向量混合

        Args:
            vec_a: 第一个向量
            vec_b: 第二个向量
            mask: 掩码
            vec_type: 向量类型

        Returns:
            混合指令
        """
        result_name = self._next_temp("blend")
        elem_count = self._get_element_count(vec_type)
        return (
            f"{result_name} = select <{elem_count} x i1> {mask}, "
            f"{vec_type} {vec_b}, {vec_type} {vec_a}"
        )

    def build_gather(
        self,
        base_ptr: str,
        indices: List[str],
        vec_type: str,
        alignment: int = 1,
    ) -> str:
        """
        构建聚集操作（非连续加载）

        Args:
            base_ptr: 基指针
            indices: 索引列表
            vec_type: 向量类型
            alignment: 对齐要求

        Returns:
            gather 指令
        """
        result_name = self._next_temp("gather")
        elem_count = self._get_element_count(vec_type)

        return (
            f"{result_name} = call {vec_type} @llvm.masked.gather."
            f"{vec_type}({vec_type}* {base_ptr}, i32 {alignment}, "
            f"<{elem_count} x i1> <true, true, true, true>)"
        )

    def build_scatter(
        self,
        values: str,
        base_ptr: str,
        indices: List[str],
        vec_type: str,
        alignment: int = 1,
    ) -> str:
        """
        构建分散操作（非连续存储）

        Args:
            values: 要存储的值
            base_ptr: 基指针
            indices: 索引列表
            vec_type: 向量类型
            alignment: 对齐要求

        Returns:
            scatter 指令
        """
        elem_count = self._get_element_count(vec_type)

        return (
            f"call void @llvm.masked.scatter."
            f"{vec_type}({vec_type} {values}, {vec_type}* {base_ptr}, i32 {alignment}, "
            f"<{elem_count} x i1> <true, true, true, true>)"
        )

    def _get_mask_type(self, vec_type: str) -> str:
        """从向量类型获取掩码类型"""
        if "<" in vec_type and ">" in vec_type:
            parts = vec_type.split("<")[1].split(">")[0].split("x")
            count = parts[0].strip()
            return f"{count} x i1"
        return "4 x i1"

    def _get_element_count(self, vec_type: str) -> int:
        """从向量类型获取元素数量"""
        if "<" in vec_type and ">" in vec_type:
            parts = vec_type.split("<")[1].split(">")[0].split("x")
            return int(parts[0].strip())
        return 4

    def _next_temp(self, prefix: str = "tmp") -> str:
        """生成临时变量名"""
        self._temp_counter += 1
        return f"%{prefix}.{self._temp_counter}"

    def supports_masks(self) -> bool:
        """检查目标平台是否支持掩码操作"""
        unsupported = ["generic_old", "sse2_no_mask"]
        return self.target_arch not in unsupported


def create_mask_handler(target_arch: str = "generic") -> MaskHandler:
    """
    创建掩码处理器

    Args:
        target_arch: 目标架构

    Returns:
        MaskHandler 实例
    """
    return MaskHandler(target_arch)

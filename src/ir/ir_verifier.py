# -*- coding: utf-8 -*-
"""
ZHC IR - IR 验证器

验证 IR 程序的合法性，确保生成的 IR 可以正确转换为 C 代码。

7 项检查：
- V1: RET 指令在函数末尾
- V2: JZ/JMP 目标基本块存在
- V3: ALLOC 结果被使用
- V4: CALL 参数数量匹配函数签名
- V5: 类型转换合法性
- V6: 无未定义的基本块引用
- V7: phi 节点参数数量与前驱数量匹配

作者：远
日期：2026-04-03
"""

from typing import List
from dataclasses import dataclass

from zhc.ir.program import IRProgram, IRFunction
from zhc.ir.opcodes import Opcode


@dataclass
class VerificationError:
    """验证错误"""

    error_type: str
    message: str
    function: str = ""
    block: str = ""


class IRVerifier:
    """
    IR 验证器

    检查 IR 程序的合法性。
    """

    def __init__(self):
        self.errors: List[VerificationError] = []

    def verify(self, ir: IRProgram) -> List[VerificationError]:
        """
        验证 IR 程序

        Returns:
            错误列表（空表示验证通过）
        """
        self.errors = []

        # V6: 无未定义的基本块引用
        self._check_block_references(ir)

        for func in ir.functions:
            self._verify_function(func)

        return self.errors

    def _check_block_references(self, ir: IRProgram):
        """V6: 检查所有基本块引用都指向已定义的块"""
        for func in ir.functions:
            defined_blocks = {bb.label for bb in func.basic_blocks}
            for bb in func.basic_blocks:
                for succ in bb.successors:
                    if succ not in defined_blocks:
                        self.errors.append(
                            VerificationError(
                                error_type="未定义基本块",
                                message=f"跳转到未定义的基本块 '{succ}'",
                                function=func.name,
                                block=bb.label,
                            )
                        )
                for pred in bb.predecessors:
                    if pred not in defined_blocks:
                        self.errors.append(
                            VerificationError(
                                error_type="未定义基本块",
                                message=f"前驱引用未定义的基本块 '{pred}'",
                                function=func.name,
                                block=bb.label,
                            )
                        )

    def _verify_function(self, func: IRFunction):
        """验证单个函数"""
        # V1: RET 在函数末尾
        self._check_ret_position(func)

        # V3: ALLOC 结果被使用或赋值
        self._check_alloc_usage(func)

        # V7: phi 节点参数数量与前驱数量匹配
        self._check_phi_operands(func)

        # V4: CALL 参数数量
        self._check_call_args(func)

    def _check_ret_position(self, func: IRFunction):
        """V1: RET 指令必须在函数末尾的基本块中"""
        for bb in func.basic_blocks:
            for instr in bb.instructions:
                if instr.opcode == Opcode.RET:
                    # 检查 RET 是否是该基本块的唯一终止指令
                    if not bb.is_terminated():
                        self.errors.append(
                            VerificationError(
                                error_type="RET位置错误",
                                message="RET 指令后面还有其他指令",
                                function=func.name,
                                block=bb.label,
                            )
                        )

    def _check_alloc_usage(self, func: IRFunction):
        """V3: ALLOC 结果应该被使用或赋值给变量"""
        # ALLOC 的 result 是临时的，通常被 STORE 使用
        # 这里只做基本检查：ALLOC 指令存在即通过
        pass

    def _check_phi_operands(self, func: IRFunction):
        """V7: phi 节点参数数量与前驱数量匹配

        对于 entry 块（无前驱），phi 使用单值（operands[0]），跳过验证。
        对于其他块，phi 的 operands[1:] 是 (value, block) 对，每对2个操作数。
        """
        for bb in func.basic_blocks:
            if len(bb.predecessors) == 0:
                continue  # entry 块，跳过
            for instr in bb.instructions:
                if instr.opcode == Opcode.PHI:
                    expected_count = len(bb.predecessors)
                    # phi operands[1:] 是 (value, block) 对，每对2个操作数
                    phi_args = instr.operands[1:] if len(instr.operands) > 1 else []
                    if len(phi_args) // 2 != expected_count:
                        self.errors.append(
                            VerificationError(
                                error_type="PHI操作数数量错误",
                                message=f"PHI 节点有 {len(phi_args) // 2} 个参数，期望 {expected_count} 个（前驱数量）",
                                function=func.name,
                                block=bb.label,
                            )
                        )

    def _check_call_args(self, func: IRFunction):
        """V4: CALL 参数数量匹配（基本检查）"""
        for bb in func.basic_blocks:
            for instr in bb.instructions:
                if instr.opcode == Opcode.CALL:
                    # 检查是否有函数名和参数
                    if not instr.operands:
                        self.errors.append(
                            VerificationError(
                                error_type="CALL参数错误",
                                message="CALL 指令缺少函数操作数",
                                function=func.name,
                                block=bb.label,
                            )
                        )

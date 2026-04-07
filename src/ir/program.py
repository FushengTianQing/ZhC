# -*- coding: utf-8 -*-
"""
ZHC IR - 程序结构定义

定义 ZHC IR 程序的顶级结构（函数、全局变量、结构体定义等）。

作者：远
日期：2026-04-03
"""

from typing import List, Dict, Optional
from .instructions import IRBasicBlock
from .values import IRValue


class IRStructDef:
    """结构体定义"""

    def __init__(self, name: str):
        self.name = name
        self.members: Dict[str, str] = {}  # member_name -> type_str

    def add_member(self, name: str, ty: str):
        self.members[name] = ty

    def __repr__(self) -> str:
        return f"struct {self.name} {{ {', '.join(f'{t} {n}' for n, t in self.members.items())} }}"


class IRGlobalVar:
    """全局变量"""

    def __init__(self, name: str, ty: str = None, init: IRValue = None):
        self.name = name
        self.ty = ty
        self.init = init

    def __repr__(self) -> str:
        return f"@global {self.name}: {self.ty}"


class IRFunction:
    """
    IR 函数

    Attributes:
        name: 函数名
        return_type: 返回类型（中文类型名）
        params: 参数列表（IRValue）
        basic_blocks: 基本块列表
    """

    def __init__(
        self,
        name: str,
        return_type: str = "空型",
    ):
        self.name = name
        self.return_type = return_type
        self.params: List[IRValue] = []
        self.basic_blocks: List[IRBasicBlock] = []

        # entry 基本块（自动创建）
        self.entry_block = self.add_basic_block("entry")

    def add_param(self, param: IRValue):
        self.params.append(param)

    def add_basic_block(self, label: str) -> IRBasicBlock:
        """添加基本块"""
        bb = IRBasicBlock(label=label)
        self.basic_blocks.append(bb)
        return bb

    def find_basic_block(self, label: str) -> Optional[IRBasicBlock]:
        """按标签查找基本块"""
        for bb in self.basic_blocks:
            if bb.label == label:
                return bb
        return None

    def __repr__(self) -> str:
        params = ", ".join(str(p) for p in self.params)
        return f"define {self.return_type} @{self.name}({params}) {{ {len(self.basic_blocks)} blocks }}"


class IRProgram:
    """
    ZHC IR 程序

    顶层 IR 结构，包含所有函数、全局变量、结构体定义。
    """

    def __init__(self):
        self.functions: List[IRFunction] = []
        self.global_vars: List[IRGlobalVar] = []
        self.structs: List[IRStructDef] = []

    def add_function(self, func: IRFunction):
        self.functions.append(func)

    def add_global(self, gv: IRGlobalVar):
        self.global_vars.append(gv)

    def add_struct(self, struct: IRStructDef):
        self.structs.append(struct)

    def find_function(self, name: str) -> Optional[IRFunction]:
        """按名称查找函数"""
        for f in self.functions:
            if f.name == name:
                return f
        return None

    def __repr__(self) -> str:
        return f"IRProgram({len(self.functions)} functions, {len(self.global_vars)} globals, {len(self.structs)} structs)"

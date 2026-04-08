"""
调试信息监听器协议

定义调试信息事件的统一接口，支持多后端扩展。
"""

from typing import Dict, List, Optional, Any, Protocol


class DebugListener(Protocol):
    """
    调试信息监听器协议

    所有后端（C、LLVM、WASM 等）都需要实现此协议，
    以接收编译过程中的调试信息事件。
    """

    def on_compile_unit(self, name: str, source_file: str, comp_dir: str) -> None:
        """
        编译单元开始事件

        Args:
            name: 编译单元名称
            source_file: 源文件路径
            comp_dir: 编译目录
        """
        ...

    def on_function(
        self,
        name: str,
        start_line: int,
        end_line: int,
        start_addr: int,
        end_addr: int,
        return_type: str = "void",
        parameters: Optional[List[Dict]] = None,
    ) -> None:
        """
        函数定义事件

        Args:
            name: 函数名
            start_line: 起始行号
            end_line: 结束行号
            start_addr: 起始地址
            end_addr: 结束地址
            return_type: 返回类型
            parameters: 参数列表 [{'name': str, 'type': str, 'line': int}]
        """
        ...

    def on_variable(
        self,
        name: str,
        type_name: str,
        line_number: int,
        address: int,
        is_parameter: bool = False,
    ) -> None:
        """
        变量定义事件

        Args:
            name: 变量名
            type_name: 类型名
            line_number: 定义行号
            address: 内存地址
            is_parameter: 是否为函数参数
        """
        ...

    def on_line_mapping(
        self, line_number: int, address: int, column: int = 0, file_index: int = 0
    ) -> None:
        """
        行号映射事件

        Args:
            line_number: 源码行号
            address: 机器码地址
            column: 列号
            file_index: 文件索引
        """
        ...

    def on_type_definition(
        self,
        type_name: str,
        type_kind: str,
        byte_size: int,
        members: Optional[List[Dict]] = None,
        encoding: str = "",
    ) -> None:
        """
        类型定义事件

        Args:
            type_name: 类型名
            type_kind: 类型种类（base, struct, enum, array, pointer）
            byte_size: 字节大小
            members: 成员列表（结构体/枚举）
            encoding: 编码方式（基本类型）
        """
        ...

    def on_finalize(self) -> Dict[str, Any]:
        """
        完成事件

        Returns:
            调试信息输出（格式由各后端决定）
        """
        ...

    def on_reset(self) -> None:
        """
        重置事件

        清空当前调试信息，准备新的编译单元。
        """
        ...

"""
调试信息事件管理器

中央调度器，将调试信息事件分发给所有注册的监听器。
支持多后端同时输出调试信息。
"""

from typing import Dict, List, Optional, Any

from zhc.debug.debug_listener import DebugListener


class DebugManager:
    """
    调试信息事件管理器

    协调调试信息事件的收集和分发。
    - 收集来自编译器的调试信息事件
    - 分发给所有注册的监听器（C、LLVM、WASM 等后端）
    """

    def __init__(self, source_file: str = "", enable_debug: bool = True):
        """
        初始化调试信息管理器

        Args:
            source_file: 源文件路径
            enable_debug: 是否启用调试信息收集
        """
        self.source_file = source_file
        self.enable_debug = enable_debug
        self._listeners: List[DebugListener] = []
        self._current_function: Optional[str] = None

    def add_listener(self, listener: DebugListener) -> None:
        """
        添加调试信息监听器

        Args:
            listener: 实现了 DebugListener 协议的监听器
        """
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: DebugListener) -> None:
        """
        移除调试信息监听器

        Args:
            listener: 要移除的监听器
        """
        if listener in self._listeners:
            self._listeners.remove(listener)

    def clear_listeners(self) -> None:
        """清空所有监听器"""
        self._listeners.clear()

    # ========== 事件分发方法 ==========

    def emit_compile_unit(
        self, name: str, source_file: Optional[str] = None, comp_dir: str = ""
    ) -> None:
        """
        发射编译单元开始事件

        Args:
            name: 编译单元名称
            source_file: 源文件路径（覆盖默认值）
            comp_dir: 编译目录
        """
        if not self.enable_debug or not self._listeners:
            return

        src = source_file or self.source_file
        for listener in self._listeners:
            listener.on_compile_unit(name, src, comp_dir)

    def emit_function(
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
        发射函数定义事件

        Args:
            name: 函数名
            start_line: 起始行号
            end_line: 结束行号
            start_addr: 起始地址
            end_addr: 结束地址
            return_type: 返回类型
            parameters: 参数列表
        """
        if not self.enable_debug or not self._listeners:
            return

        self._current_function = name
        for listener in self._listeners:
            listener.on_function(
                name=name,
                start_line=start_line,
                end_line=end_line,
                start_addr=start_addr,
                end_addr=end_addr,
                return_type=return_type,
                parameters=parameters,
            )

    def emit_variable(
        self,
        name: str,
        type_name: str,
        line_number: int,
        address: int,
        is_parameter: bool = False,
    ) -> None:
        """
        发射变量定义事件

        Args:
            name: 变量名
            type_name: 类型名
            line_number: 定义行号
            address: 内存地址
            is_parameter: 是否为函数参数
        """
        if not self.enable_debug or not self._listeners:
            return

        for listener in self._listeners:
            listener.on_variable(
                name=name,
                type_name=type_name,
                line_number=line_number,
                address=address,
                is_parameter=is_parameter,
            )

    def emit_line_mapping(
        self, line_number: int, address: int, column: int = 0, file_index: int = 0
    ) -> None:
        """
        发射行号映射事件

        Args:
            line_number: 源码行号
            address: 机器码地址
            column: 列号
            file_index: 文件索引
        """
        if not self.enable_debug or not self._listeners:
            return

        for listener in self._listeners:
            listener.on_line_mapping(
                line_number=line_number,
                address=address,
                column=column,
                file_index=file_index,
            )

    def emit_type_definition(
        self,
        type_name: str,
        type_kind: str,
        byte_size: int,
        members: Optional[List[Dict]] = None,
        encoding: str = "",
    ) -> None:
        """
        发射类型定义事件

        Args:
            type_name: 类型名
            type_kind: 类型种类
            byte_size: 字节大小
            members: 成员列表
            encoding: 编码方式
        """
        if not self.enable_debug or not self._listeners:
            return

        for listener in self._listeners:
            listener.on_type_definition(
                type_name=type_name,
                type_kind=type_kind,
                byte_size=byte_size,
                members=members,
                encoding=encoding,
            )

    def emit_finalize(self) -> Dict[str, Any]:
        """
        发射完成事件

        Returns:
            所有监听器输出的调试信息
        """
        if not self.enable_debug:
            return {}

        results = {}
        for listener in self._listeners:
            result = listener.on_finalize()
            if result:
                # 使用监听器类名作为键
                key = listener.__class__.__name__
                results[key] = result
        return results

    def emit_reset(self) -> None:
        """
        发射重置事件
        """
        if not self.enable_debug:
            return

        self._current_function = None
        for listener in self._listeners:
            listener.on_reset()

    @property
    def listeners(self) -> List[DebugListener]:
        """获取所有监听器"""
        return list(self._listeners)

    @property
    def has_listeners(self) -> bool:
        """是否有注册的监听器"""
        return len(self._listeners) > 0

"""
事件驱动调试架构测试

测试 DebugManager、DebugListener 协议和 CDebugListener。
"""

import pytest
from typing import Dict, List, Optional, Any

from zhc.debug.debug_manager import DebugManager
from zhc.debug.debug_listener import DebugListener
from zhc.codegen.c_debug_listener import CDebugListener


class MockDebugListener(DebugListener):
    """模拟调试监听器，用于测试"""
    
    def __init__(self):
        self.events: List[Dict] = []
    
    def on_compile_unit(self, name: str, source_file: str, comp_dir: str) -> None:
        self.events.append({'type': 'compile_unit', 'name': name, 'source_file': source_file})
    
    def on_function(self, name: str, start_line: int, end_line: int,
                   start_addr: int, end_addr: int, return_type: str = "void",
                   parameters: Optional[List[Dict]] = None) -> None:
        self.events.append({
            'type': 'function', 'name': name, 'start_line': start_line,
            'end_line': end_line, 'return_type': return_type
        })
    
    def on_variable(self, name: str, type_name: str, line_number: int,
                   address: int, is_parameter: bool = False) -> None:
        self.events.append({
            'type': 'variable', 'name': name, 'type_name': type_name,
            'line_number': line_number
        })
    
    def on_line_mapping(self, line_number: int, address: int,
                       column: int = 0, file_index: int = 0) -> None:
        self.events.append({'type': 'line_mapping', 'line': line_number, 'address': address})
    
    def on_type_definition(self, type_name: str, type_kind: str, byte_size: int,
                          members: Optional[List[Dict]] = None,
                          encoding: str = "") -> None:
        self.events.append({'type': 'type', 'name': type_name, 'kind': type_kind})
    
    def on_finalize(self) -> Dict[str, Any]:
        return {'events': self.events}
    
    def on_reset(self) -> None:
        self.events.clear()


class TestDebugListener:
    """测试 DebugListener 协议"""
    
    def test_mock_listener_events(self):
        """测试模拟监听器接收事件"""
        listener = MockDebugListener()
        
        listener.on_function("main", 1, 10, 0x1000, 0x1200, "int")
        listener.on_variable("x", "int", 5, 0x2000)
        listener.on_line_mapping(10, 0x1000)
        
        assert len(listener.events) == 3
        assert listener.events[0]['type'] == 'function'
        assert listener.events[0]['name'] == 'main'
        assert listener.events[1]['type'] == 'variable'
        assert listener.events[2]['type'] == 'line_mapping'


class TestDebugManager:
    """测试调试信息事件管理器"""
    
    def test_manager_creation(self):
        """测试管理器创建"""
        manager = DebugManager(source_file="test.zhc", enable_debug=True)
        
        assert manager.source_file == "test.zhc"
        assert manager.enable_debug is True
        assert not manager.has_listeners
    
    def test_add_remove_listener(self):
        """测试添加和移除监听器"""
        manager = DebugManager(enable_debug=True)
        listener = MockDebugListener()
        
        manager.add_listener(listener)
        assert manager.has_listeners
        assert listener in manager.listeners
        
        manager.remove_listener(listener)
        assert not manager.has_listeners
    
    def test_emit_function(self):
        """测试发射函数事件"""
        manager = DebugManager(enable_debug=True)
        listener = MockDebugListener()
        manager.add_listener(listener)
        
        manager.emit_function("main", 1, 10, 0x1000, 0x1200, "int")
        
        assert len(listener.events) == 1
        assert listener.events[0]['type'] == 'function'
        assert listener.events[0]['name'] == 'main'
    
    def test_emit_variable(self):
        """测试发射变量事件"""
        manager = DebugManager(enable_debug=True)
        listener = MockDebugListener()
        manager.add_listener(listener)
        
        manager.emit_variable("计数器", "整数型", 5, 0x2000)
        
        assert len(listener.events) == 1
        assert listener.events[0]['type'] == 'variable'
        assert listener.events[0]['name'] == '计数器'
    
    def test_multiple_listeners(self):
        """测试多监听器"""
        manager = DebugManager(enable_debug=True)
        listener1 = MockDebugListener()
        listener2 = MockDebugListener()
        
        manager.add_listener(listener1)
        manager.add_listener(listener2)
        
        manager.emit_function("main", 1, 10, 0x1000, 0x1200, "int")
        
        assert len(listener1.events) == 1
        assert len(listener2.events) == 1
    
    def test_disabled_manager(self):
        """测试禁用的管理器"""
        manager = DebugManager(enable_debug=False)
        listener = MockDebugListener()
        manager.add_listener(listener)
        
        manager.emit_function("main", 1, 10, 0x1000, 0x1200, "int")
        
        assert len(listener.events) == 0
    
    def test_emit_finalize(self):
        """测试完成事件"""
        manager = DebugManager(enable_debug=True)
        listener = MockDebugListener()
        manager.add_listener(listener)
        
        manager.emit_function("main", 1, 10, 0x1000, 0x1200, "int")
        results = manager.emit_finalize()
        
        assert 'MockDebugListener' in results
        assert len(results['MockDebugListener']['events']) == 1
    
    def test_emit_reset(self):
        """测试重置事件"""
        manager = DebugManager(enable_debug=True)
        listener = MockDebugListener()
        manager.add_listener(listener)
        
        manager.emit_function("main", 1, 10, 0x1000, 0x1200, "int")
        manager.emit_reset()
        
        assert len(listener.events) == 0


class TestCDebugListener:
    """测试 C 后端调试监听器"""
    
    def test_listener_creation(self):
        """测试监听器创建"""
        listener = CDebugListener("test.zhc", "debug.json")
        
        assert listener.source_file == "test.zhc"
        assert listener.output_file == "debug.json"
        assert listener.generator is not None
    
    def test_on_function(self):
        """测试函数事件处理"""
        listener = CDebugListener("test.zhc")
        
        listener.on_function(
            name="主函数",
            start_line=1,
            end_line=10,
            start_addr=0x1000,
            end_addr=0x1200,
            return_type="整数型"
        )
        
        assert len(listener.generator.dwarf.symbol_table.symbols) == 1
        assert listener.generator.dwarf.symbol_table.symbols[0]['name'] == "主函数"
    
    def test_on_variable(self):
        """测试变量事件处理"""
        listener = CDebugListener("test.zhc")
        
        listener.on_variable("计数器", "整数型", 5, 0x2000)
        
        assert len(listener.generator.dwarf.symbol_table.symbols) == 1
    
    def test_on_line_mapping(self):
        """测试行号映射"""
        listener = CDebugListener("test.zhc")
        
        listener.on_line_mapping(10, 0x1000)
        listener.on_line_mapping(20, 0x1100)
        
        assert len(listener.generator.dwarf.line_table.line_entries) == 2
    
    def test_on_type_base(self):
        """测试基本类型定义"""
        listener = CDebugListener("test.zhc")
        
        listener.on_type_definition("自定义整数", "base", 8, encoding="DW_ATE_signed")
        
        assert "自定义整数" in listener.generator.dwarf.type_info.type_table
    
    def test_on_type_struct(self):
        """测试结构体类型定义"""
        listener = CDebugListener("test.zhc")
        
        members = [
            {'name': 'x', 'type': 'int', 'offset': 0},
            {'name': 'y', 'type': 'int', 'offset': 8}
        ]
        listener.on_type_definition("点", "struct", 16, members=members)
        
        assert "点" in listener.generator.dwarf.type_info.type_table
    
    def test_on_finalize(self):
        """测试完成"""
        listener = CDebugListener("test.zhc")
        
        listener.on_function("main", 1, 10, 0x1000, 0x1200, "int")
        result = listener.on_finalize()
        
        assert 'debug_line' in result
        assert 'debug_info' in result


class TestEventDrivenArchitecture:
    """测试完整事件驱动架构"""
    
    def test_full_pipeline(self):
        """测试完整的事件驱动管道"""
        # 创建管理器
        manager = DebugManager(source_file="test.zhc", enable_debug=True)
        
        # 添加多个监听器
        mock_listener = MockDebugListener()
        c_listener = CDebugListener("test.zhc", "debug.json")
        
        manager.add_listener(mock_listener)
        manager.add_listener(c_listener)
        
        # 发射事件
        manager.emit_compile_unit("main", "test.zhc", "/path/to/project")
        manager.emit_function("主函数", 1, 20, 0x1000, 0x1200, "整数型")
        manager.emit_variable("计数器", "整数型", 10, 0x2000)
        manager.emit_line_mapping(10, 0x1000)
        manager.emit_line_mapping(20, 0x1100)
        
        # 验证 Mock 监听器
        assert len(mock_listener.events) == 5
        assert mock_listener.events[0]['type'] == 'compile_unit'
        assert mock_listener.events[1]['type'] == 'function'
        assert mock_listener.events[2]['type'] == 'variable'
        
        # 验证 C 监听器
        assert len(c_listener.generator.dwarf.symbol_table.symbols) == 2
        # 行号条目数量可能因编译单元初始化而多于预期
        assert len(c_listener.generator.dwarf.line_table.line_entries) >= 2
        
        # 完成并获取结果
        results = manager.emit_finalize()
        
        assert 'MockDebugListener' in results
        assert 'CDebugListener' in results
    
    def test_multi_backend_simulation(self):
        """模拟多后端场景"""
        # 创建管理器
        manager = DebugManager(source_file="test.zhc", enable_debug=True)
        
        # 添加两个 C 监听器（模拟不同配置）
        c_listener1 = CDebugListener("test.zhc", "debug_full.json")
        c_listener2 = CDebugListener("test.zhc", "debug_minimal.json")
        
        manager.add_listener(c_listener1)
        manager.add_listener(c_listener2)
        
        # 发射事件
        manager.emit_function("main", 1, 10, 0x1000, 0x1200, "int")
        
        # 两个监听器都收到事件
        assert len(c_listener1.generator.dwarf.symbol_table.symbols) == 1
        assert len(c_listener2.generator.dwarf.symbol_table.symbols) == 1
        
        # 可以分别完成并生成不同格式的输出
        result1 = c_listener1.on_finalize()
        result2 = c_listener2.on_finalize()
        
        # 两者都应该有调试信息
        assert 'debug_line' in result1
        assert 'debug_line' in result2

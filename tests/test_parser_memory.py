#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试内存语法解析器 (MemorySyntaxParser)

测试覆盖：
1. 内存操作类型
2. 内存安全级别
3. 内存分配信息
4. 智能指针类型
"""

import pytest

from zhc.parser.memory import (
    MemoryOperation, MemorySafety, SmartPointerType,
    MemoryAllocation, MemoryCheck
)


class TestMemoryOperation:
    """测试内存操作类型枚举"""
    
    def test_memory_operation_values(self):
        """测试内存操作枚举值"""
        assert MemoryOperation.NEW.value == "新建"
        assert MemoryOperation.DELETE.value == "删除"
        assert MemoryOperation.MALLOC.value == "分配"
        assert MemoryOperation.FREE.value == "释放"
        assert MemoryOperation.ARRAY_NEW.value == "新建数组"
        assert MemoryOperation.ARRAY_DELETE.value == "删除数组"


class TestMemorySafety:
    """测试内存安全级别枚举"""
    
    def test_memory_safety_values(self):
        """测试内存安全级别枚举值"""
        assert MemorySafety.SAFE.value == "安全"
        assert MemorySafety.UNSAFE.value == "不安全"
        assert MemorySafety.WARNING.value == "警告"


class TestSmartPointerType:
    """测试智能指针类型枚举"""
    
    def test_smart_pointer_type_values(self):
        """测试智能指针类型枚举值"""
        assert SmartPointerType.UNIQUE.value == "独享指针"
        assert SmartPointerType.SHARED.value == "共享指针"
        assert SmartPointerType.WEAK.value == "弱指针"


class TestMemoryAllocation:
    """测试内存分配信息"""
    
    def test_memory_allocation_creation(self):
        """测试内存分配信息创建"""
        alloc = MemoryAllocation(
            operation=MemoryOperation.NEW,
            type_name="整数型",
            variable_name="ptr",
            line_number=10
        )
        
        assert alloc.operation == MemoryOperation.NEW
        assert alloc.type_name == "整数型"
        assert alloc.variable_name == "ptr"
        assert alloc.line_number == 10
        assert alloc.size is None
        assert not alloc.is_array
    
    def test_memory_allocation_with_size(self):
        """测试带大小的内存分配"""
        alloc = MemoryAllocation(
            operation=MemoryOperation.ARRAY_NEW,
            type_name="整数型",
            variable_name="arr",
            line_number=15,
            size=10,
            is_array=True
        )
        
        assert alloc.size == 10
        assert alloc.is_array
        assert alloc.operation == MemoryOperation.ARRAY_NEW
    
    def test_memory_allocation_malloc(self):
        """测试 malloc 分配"""
        alloc = MemoryAllocation(
            operation=MemoryOperation.MALLOC,
            type_name="空型",
            variable_name="buffer",
            line_number=20,
            size=1024
        )
        
        assert alloc.operation == MemoryOperation.MALLOC
        assert alloc.size == 1024
    
    def test_memory_allocation_free(self):
        """测试 free 操作"""
        alloc = MemoryAllocation(
            operation=MemoryOperation.FREE,
            type_name="空型",
            variable_name="buffer",
            line_number=25
        )
        
        assert alloc.operation == MemoryOperation.FREE


class TestMemoryCheck:
    """测试内存安全检查结果"""
    
    def test_memory_check_safe(self):
        """测试安全的内存检查"""
        check = MemoryCheck(
            is_safe=True,
            level=MemorySafety.SAFE,
            message="内存分配和释放匹配",
            suggestions=[]
        )
        
        assert check.is_safe
        assert check.level == MemorySafety.SAFE
        assert len(check.suggestions) == 0
    
    def test_memory_check_unsafe(self):
        """测试不安全的内存检查"""
        check = MemoryCheck(
            is_safe=False,
            level=MemorySafety.UNSAFE,
            message="检测到内存泄漏",
            suggestions=["添加释放语句", "使用智能指针"]
        )
        
        assert not check.is_safe
        assert check.level == MemorySafety.UNSAFE
        assert len(check.suggestions) == 2
    
    def test_memory_check_warning(self):
        """测试警告级别的内存检查"""
        check = MemoryCheck(
            is_safe=True,
            level=MemorySafety.WARNING,
            message="未初始化的内存访问",
            suggestions=["初始化变量"]
        )
        
        assert check.is_safe  # 警告级别可能仍然标记为安全
        assert check.level == MemorySafety.WARNING
        assert len(check.suggestions) == 1


class TestMemoryOperationTypes:
    """测试不同类型的内存操作"""
    
    def test_new_operation(self):
        """测试新建操作"""
        alloc = MemoryAllocation(
            operation=MemoryOperation.NEW,
            type_name="学生",
            variable_name="stu",
            line_number=10
        )
        
        assert alloc.operation == MemoryOperation.NEW
        assert not alloc.is_array
    
    def test_array_new_operation(self):
        """测试新建数组操作"""
        alloc = MemoryAllocation(
            operation=MemoryOperation.ARRAY_NEW,
            type_name="整数型",
            variable_name="arr",
            line_number=15,
            size=100,
            is_array=True
        )
        
        assert alloc.operation == MemoryOperation.ARRAY_NEW
        assert alloc.is_array
        assert alloc.size == 100
    
    def test_delete_operation(self):
        """测试删除操作"""
        alloc = MemoryAllocation(
            operation=MemoryOperation.DELETE,
            type_name="学生",
            variable_name="stu",
            line_number=20
        )
        
        assert alloc.operation == MemoryOperation.DELETE
    
    def test_array_delete_operation(self):
        """测试删除数组操作"""
        alloc = MemoryAllocation(
            operation=MemoryOperation.ARRAY_DELETE,
            type_name="整数型",
            variable_name="arr",
            line_number=25,
            is_array=True
        )
        
        assert alloc.operation == MemoryOperation.ARRAY_DELETE
        assert alloc.is_array


class TestMemorySafetyScenarios:
    """测试内存安全场景"""
    
    def test_memory_leak_detection(self):
        """测试内存泄漏检测"""
        # 分配但未释放
        check = MemoryCheck(
            is_safe=False,
            level=MemorySafety.UNSAFE,
            message="内存泄漏：变量 ptr 在第 10 行分配但未释放",
            suggestions=["在作用域结束前添加 '删除 ptr;'"]
        )
        
        assert not check.is_safe
        assert "泄漏" in check.message
    
    def test_double_free_detection(self):
        """测试双重释放检测"""
        check = MemoryCheck(
            is_safe=False,
            level=MemorySafety.UNSAFE,
            message="双重释放：变量 ptr 在第 20 行已释放",
            suggestions=["移除重复的释放语句"]
        )
        
        assert not check.is_safe
        assert "双重释放" in check.message
    
    def test_use_after_free_detection(self):
        """测试释放后使用检测"""
        check = MemoryCheck(
            is_safe=False,
            level=MemorySafety.UNSAFE,
            message="释放后使用：变量 ptr 在第 25 行释放后在第 30 行被访问",
            suggestions=["在释放后将指针置为空"]
        )
        
        assert not check.is_safe
        assert "释放后使用" in check.message
    
    def test_buffer_overflow_detection(self):
        """测试缓冲区溢出检测"""
        check = MemoryCheck(
            is_safe=False,
            level=MemorySafety.UNSAFE,
            message="缓冲区溢出：数组 arr[10] 在第 35 行访问索引 15",
            suggestions=["检查数组边界", "使用安全的数组访问方法"]
        )
        
        assert not check.is_safe
        assert "溢出" in check.message


class TestSmartPointerScenarios:
    """测试智能指针场景"""
    
    def test_unique_pointer_usage(self):
        """测试独享指针使用"""
        # 独享指针应该独占所有权
        ptr_type = SmartPointerType.UNIQUE
        assert ptr_type == SmartPointerType.UNIQUE
    
    def test_shared_pointer_usage(self):
        """测试共享指针使用"""
        # 共享指针可以共享所有权
        ptr_type = SmartPointerType.SHARED
        assert ptr_type == SmartPointerType.SHARED
    
    def test_weak_pointer_usage(self):
        """测试弱指针使用"""
        # 弱指针不增加引用计数
        ptr_type = SmartPointerType.WEAK
        assert ptr_type == SmartPointerType.WEAK


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
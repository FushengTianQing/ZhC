# -*- coding: utf-8 -*-
"""LLVM 类型映射器测试

测试 ZhC 类型到 LLVM 类型的映射。

作者：远
日期：2026-04-08
"""

import pytest


class TestLLVMTypeMapperImport:
    """类型映射器导入测试"""
    
    def test_type_mapper_available(self):
        """测试 llvmlite 是否可用"""
        try:
            from zhc.backend.llvm_type_mapper import LLVMTypeMapper
            available = True
        except ImportError:
            available = False
        
        if not available:
            pytest.skip("llvmlite 未安装，跳过测试")
        
        assert available


class TestLLVMTypeMapperCreation:
    """类型映射器创建测试"""
    
    def test_mapper_creation(self):
        """测试映射器创建"""
        try:
            from zhc.backend.llvm_type_mapper import LLVMTypeMapper
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        mapper = LLVMTypeMapper()
        assert mapper is not None


class TestBasicTypeMapping:
    """基本类型映射测试"""
    
    def test_integer_type(self):
        """测试整数类型"""
        try:
            from zhc.backend.llvm_type_mapper import LLVMTypeMapper
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        mapper = LLVMTypeMapper()
        
        # 整数型
        llvm_type = mapper.map_type("整数型")
        assert str(llvm_type) == "i32"
    
    def test_float_type(self):
        """测试浮点类型"""
        try:
            from zhc.backend.llvm_type_mapper import LLVMTypeMapper
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        mapper = LLVMTypeMapper()
        
        # 浮点型
        llvm_type = mapper.map_type("浮点型")
        assert str(llvm_type) == "float"
        
        # 双精度浮点型
        llvm_type = mapper.map_type("双精度浮点型")
        assert str(llvm_type) == "double"
    
    def test_boolean_type(self):
        """测试布尔类型"""
        try:
            from zhc.backend.llvm_type_mapper import LLVMTypeMapper
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        mapper = LLVMTypeMapper()
        
        llvm_type = mapper.map_type("布尔型")
        assert str(llvm_type) == "i1"
    
    def test_char_type(self):
        """测试字符类型"""
        try:
            from zhc.backend.llvm_type_mapper import LLVMTypeMapper
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        mapper = LLVMTypeMapper()
        
        llvm_type = mapper.map_type("字符型")
        assert str(llvm_type) == "i8"
    
    def test_void_type(self):
        """测试空类型"""
        try:
            from zhc.backend.llvm_type_mapper import LLVMTypeMapper
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        mapper = LLVMTypeMapper()
        
        llvm_type = mapper.map_type("空型")
        assert str(llvm_type) == "void"
    
    def test_llvm_primitives(self):
        """测试 LLVM 原始类型"""
        try:
            from zhc.backend.llvm_type_mapper import LLVMTypeMapper
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        mapper = LLVMTypeMapper()
        
        assert str(mapper.map_type("i1")) == "i1"
        assert str(mapper.map_type("i8")) == "i8"
        assert str(mapper.map_type("i16")) == "i16"
        assert str(mapper.map_type("i32")) == "i32"
        assert str(mapper.map_type("i64")) == "i64"
        assert str(mapper.map_type("float")) == "float"
        assert str(mapper.map_type("double")) == "double"
        assert str(mapper.map_type("void")) == "void"


class TestCompositeTypeMapping:
    """复合类型映射测试"""
    
    def test_pointer_type(self):
        """测试指针类型"""
        try:
            from zhc.backend.llvm_type_mapper import LLVMTypeMapper
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        mapper = LLVMTypeMapper()
        
        # 整数指针
        llvm_type = mapper.map_type("整数型*")
        assert "i32*" in str(llvm_type)
    
    def test_array_type(self):
        """测试数组类型"""
        try:
            from zhc.backend.llvm_type_mapper import LLVMTypeMapper
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        mapper = LLVMTypeMapper()
        
        # 整数数组
        llvm_type = mapper.map_type("整数型[10]")
        assert "[10 x i32]" in str(llvm_type)
    
    def test_function_type(self):
        """测试函数类型"""
        try:
            from zhc.backend.llvm_type_mapper import LLVMTypeMapper
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        mapper = LLVMTypeMapper()
        
        # 函数类型 (i32, i32) -> i32
        func_type = mapper.map_function_type("整数型", ["整数型", "整数型"])
        assert "i32 (i32, i32)" in str(func_type)


class TestTypeInfo:
    """类型信息测试"""
    
    def test_get_type_info(self):
        """测试获取类型信息"""
        try:
            from zhc.backend.llvm_type_mapper import LLVMTypeMapper
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        mapper = LLVMTypeMapper()
        
        # 整数型
        info = mapper.get_type_info("整数型")
        assert info is not None
        assert info.zhc_type == "整数型"
        assert info.llvm_type == "i32"
        assert info.size_bits == 32
        assert info.is_signed is True
        assert info.is_float is False
    
    def test_get_size_bits(self):
        """测试获取位宽"""
        try:
            from zhc.backend.llvm_type_mapper import LLVMTypeMapper
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        mapper = LLVMTypeMapper()
        
        assert mapper.get_size_bits("整数型") == 32
        assert mapper.get_size_bits("长整数型") == 64
        assert mapper.get_size_bits("短整数型") == 16
        assert mapper.get_size_bits("字节型") == 8
        assert mapper.get_size_bits("布尔型") == 1
        assert mapper.get_size_bits("浮点型") == 32
        assert mapper.get_size_bits("双精度浮点型") == 64
    
    def test_type_predicates(self):
        """测试类型谓词"""
        try:
            from zhc.backend.llvm_type_mapper import LLVMTypeMapper
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        mapper = LLVMTypeMapper()
        
        # 有符号
        assert mapper.is_signed("整数型") is True
        assert mapper.is_signed("无符号整数型") is False
        
        # 浮点
        assert mapper.is_float("浮点型") is True
        assert mapper.is_float("整数型") is False
        
        # 指针
        assert mapper.is_pointer("整数型*") is True
        assert mapper.is_pointer("整数型") is False


class TestTypeCreation:
    """类型创建测试"""
    
    def test_create_pointer_type(self):
        """测试创建指针类型"""
        try:
            from zhc.backend.llvm_type_mapper import LLVMTypeMapper
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        mapper = LLVMTypeMapper()
        
        ptr_type = mapper.create_pointer_type("整数型")
        assert "i32*" in str(ptr_type)
    
    def test_create_array_type(self):
        """测试创建数组类型"""
        try:
            from zhc.backend.llvm_type_mapper import LLVMTypeMapper
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        mapper = LLVMTypeMapper()
        
        arr_type = mapper.create_array_type("整数型", 5)
        assert "[5 x i32]" in str(arr_type)
    
    def test_create_struct_type(self):
        """测试创建结构体类型"""
        try:
            from zhc.backend.llvm_type_mapper import LLVMTypeMapper
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        mapper = LLVMTypeMapper()
        
        # 结构体 {i32, float}
        struct_type = mapper.create_struct_type("Point", [("x", "整数型"), ("y", "浮点型")])
        # llvmlite 的结构体类型格式可能不同
        assert "i32" in str(struct_type)
        assert "float" in str(struct_type)


class TestConvenienceFunctions:
    """便捷函数测试"""
    
    def test_map_zhc_type_to_llvm(self):
        """测试便捷映射函数"""
        try:
            from zhc.backend.llvm_type_mapper import map_zhc_type_to_llvm
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        llvm_type = map_zhc_type_to_llvm("整数型")
        assert str(llvm_type) == "i32"
    
    def test_get_type_size_bits(self):
        """测试便捷位宽函数"""
        try:
            from zhc.backend.llvm_type_mapper import get_type_size_bits
        except ImportError:
            pytest.skip("llvmlite 未安装")
        
        assert get_type_size_bits("整数型") == 32
        assert get_type_size_bits("长整数型") == 64
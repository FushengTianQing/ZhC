#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试类解析器 (ClassParser)

测试覆盖：
1. 类声明解析
2. 属性定义
3. 方法定义
4. 访问控制
"""

import pytest

from zhc.parser.class_ import (
    Visibility, AttributeType, AttributeInfo, MethodInfo, ClassInfo
)


class TestVisibility:
    """测试可见性枚举"""
    
    def test_visibility_values(self):
        """测试可见性枚举值"""
        assert Visibility.PUBLIC.value == "public"
        assert Visibility.PRIVATE.value == "private"
        assert Visibility.PROTECTED.value == "protected"


class TestAttributeType:
    """测试属性类型枚举"""
    
    def test_attribute_type_values(self):
        """测试属性类型枚举值"""
        assert AttributeType.INSTANCE.value == "instance"
        assert AttributeType.CLASS.value == "class"
        assert AttributeType.CONSTANT.value == "constant"


class TestAttributeInfo:
    """测试属性信息"""
    
    def test_attribute_info_creation(self):
        """测试属性信息创建"""
        attr = AttributeInfo(
            name="姓名",
            type_name="字符串型",
            visibility=Visibility.PUBLIC,
            attribute_type=AttributeType.INSTANCE,
            line_number=10
        )
        
        assert attr.name == "姓名"
        assert attr.type_name == "字符串型"
        assert attr.visibility == Visibility.PUBLIC
        assert attr.attribute_type == AttributeType.INSTANCE
        assert attr.line_number == 10
        assert attr.default_value is None
        assert not attr.is_static
        assert not attr.is_const
    
    def test_attribute_info_with_default(self):
        """测试带默认值的属性"""
        attr = AttributeInfo(
            name="年龄",
            type_name="整数型",
            visibility=Visibility.PRIVATE,
            attribute_type=AttributeType.INSTANCE,
            line_number=15,
            default_value="0"
        )
        
        assert attr.default_value == "0"
    
    def test_static_attribute(self):
        """测试静态属性"""
        attr = AttributeInfo(
            name="计数器",
            type_name="整数型",
            visibility=Visibility.PRIVATE,
            attribute_type=AttributeType.CLASS,
            line_number=20,
            is_static=True
        )
        
        assert attr.is_static
        assert attr.attribute_type == AttributeType.CLASS
    
    def test_constant_attribute(self):
        """测试常量属性"""
        attr = AttributeInfo(
            name="最大值",
            type_name="整数型",
            visibility=Visibility.PUBLIC,
            attribute_type=AttributeType.CONSTANT,
            line_number=25,
            is_const=True,
            default_value="100"
        )
        
        assert attr.is_const
        assert attr.attribute_type == AttributeType.CONSTANT


class TestMethodInfo:
    """测试方法信息"""
    
    def test_method_info_creation(self):
        """测试方法信息创建"""
        method = MethodInfo(
            name="获取信息",
            return_type="字符串型",
            parameters=[("名", "字符串型"), ("龄", "整数型")],
            visibility=Visibility.PUBLIC,
            line_number=30
        )
        
        assert method.name == "获取信息"
        assert method.return_type == "字符串型"
        assert len(method.parameters) == 2
        assert method.visibility == Visibility.PUBLIC
        assert not method.is_constructor
        assert not method.is_destructor
        assert not method.is_static
        assert not method.is_virtual
    
    def test_constructor_method(self):
        """测试构造函数"""
        method = MethodInfo(
            name="构造函数",
            return_type="空型",
            parameters=[("名", "字符串型")],
            visibility=Visibility.PUBLIC,
            is_constructor=True,
            line_number=35
        )
        
        assert method.is_constructor
        assert method.name == "构造函数"
    
    def test_destructor_method(self):
        """测试析构函数"""
        method = MethodInfo(
            name="析构函数",
            return_type="空型",
            parameters=[],
            visibility=Visibility.PUBLIC,
            is_destructor=True,
            line_number=40
        )
        
        assert method.is_destructor
        assert method.name == "析构函数"
    
    def test_static_method(self):
        """测试静态方法"""
        method = MethodInfo(
            name="计数",
            return_type="整数型",
            parameters=[],
            visibility=Visibility.PUBLIC,
            is_static=True,
            line_number=45
        )
        
        assert method.is_static
    
    def test_virtual_method(self):
        """测试虚函数"""
        method = MethodInfo(
            name="绘制",
            return_type="空型",
            parameters=[],
            visibility=Visibility.PUBLIC,
            is_virtual=True,
            line_number=50
        )
        
        assert method.is_virtual


class TestClassInfo:
    """测试类信息"""
    
    def test_class_info_creation(self):
        """测试类信息创建"""
        cls = ClassInfo(name="学生", line_number=10)
        
        assert cls.name == "学生"
        assert cls.base_class is None
        assert cls.attributes == []
        assert cls.methods == []
        assert cls.visibility == Visibility.PUBLIC
        assert not cls.is_abstract
        assert not cls.is_final
    
    def test_add_attribute(self):
        """测试添加属性"""
        cls = ClassInfo(name="学生", line_number=10)
        attr = AttributeInfo(
            name="姓名",
            type_name="字符串型",
            visibility=Visibility.PUBLIC,
            attribute_type=AttributeType.INSTANCE,
            line_number=15
        )
        
        cls.add_attribute(attr)
        assert len(cls.attributes) == 1
        assert cls.attributes[0] == attr
    
    def test_add_method(self):
        """测试添加方法"""
        cls = ClassInfo(name="学生", line_number=10)
        method = MethodInfo(
            name="获取信息",
            return_type="字符串型",
            parameters=[],
            visibility=Visibility.PUBLIC,
            line_number=20
        )
        
        cls.add_method(method)
        assert len(cls.methods) == 1
        assert cls.methods[0] == method
    
    def test_get_public_attributes(self):
        """测试获取公开属性"""
        cls = ClassInfo(name="学生", line_number=10)
        
        public_attr = AttributeInfo(
            name="姓名",
            type_name="字符串型",
            visibility=Visibility.PUBLIC,
            attribute_type=AttributeType.INSTANCE,
            line_number=15
        )
        
        private_attr = AttributeInfo(
            name="内部ID",
            type_name="整数型",
            visibility=Visibility.PRIVATE,
            attribute_type=AttributeType.INSTANCE,
            line_number=16
        )
        
        cls.add_attribute(public_attr)
        cls.add_attribute(private_attr)
        
        public_attrs = cls.get_public_attributes()
        assert len(public_attrs) == 1
        assert public_attrs[0] == public_attr
    
    def test_get_public_methods(self):
        """测试获取公开方法"""
        cls = ClassInfo(name="学生", line_number=10)
        
        public_method = MethodInfo(
            name="获取信息",
            return_type="字符串型",
            parameters=[],
            visibility=Visibility.PUBLIC,
            line_number=20
        )
        
        private_method = MethodInfo(
            name="验证",
            return_type="逻辑型",
            parameters=[],
            visibility=Visibility.PRIVATE,
            line_number=25
        )
        
        cls.add_method(public_method)
        cls.add_method(private_method)
        
        public_methods = cls.get_public_methods()
        assert len(public_methods) == 1
        assert public_methods[0] == public_method
    
    def test_class_with_base(self):
        """测试带基类的类"""
        cls = ClassInfo(
            name="学生",
            base_class="人员",
            line_number=10
        )
        
        assert cls.base_class == "人员"
    
    def test_abstract_class(self):
        """测试抽象类"""
        cls = ClassInfo(
            name="形状",
            is_abstract=True,
            line_number=10
        )
        
        assert cls.is_abstract
    
    def test_final_class(self):
        """测试最终类"""
        cls = ClassInfo(
            name="最终类",
            is_final=True,
            line_number=10
        )
        
        assert cls.is_final


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
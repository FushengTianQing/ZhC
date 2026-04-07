#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试扩展类解析器 (ClassParserExtended)

测试覆盖：
1. 继承链解析
2. 方法体解析
3. 状态机模式
4. 错误恢复机制
"""

import pytest

from zhc.parser.class_extended import (
    Visibility, AttributeType, ParseState,
    AttributeInfo, ParameterInfo, MethodBody, MethodInfo, ClassInfo
)


class TestParameterInfo:
    """测试参数信息"""
    
    def test_parameter_info_creation(self):
        """测试参数信息创建"""
        param = ParameterInfo(name="参数1", type_name="整数型")
        assert param.name == "参数1"
        assert param.type_name == "整数型"
        assert not param.is_reference
        assert not param.is_const
    
    def test_parameter_reference(self):
        """测试引用参数"""
        param = ParameterInfo(
            name="参数1",
            type_name="整数型",
            is_reference=True
        )
        assert param.is_reference
    
    def test_parameter_const(self):
        """测试常量参数"""
        param = ParameterInfo(
            name="参数1",
            type_name="整数型",
            is_const=True
        )
        assert param.is_const


class TestMethodBody:
    """测试方法体"""
    
    def test_method_body_creation(self):
        """测试方法体创建"""
        body = MethodBody(lines=["行1", "行2"])
        assert len(body.lines) == 2
        assert body.local_variables == []
        assert body.statements == []
    
    def test_method_body_with_locals(self):
        """测试带局部变量的方法体"""
        body = MethodBody(
            lines=["整数型 x = 10;"],
            local_variables=[("x", "整数型")],
            statements=["x = 10"]
        )
        assert len(body.local_variables) == 1
        assert len(body.statements) == 1


class TestMethodInfoExtended:
    """测试扩展的方法信息"""
    
    def test_method_with_body(self):
        """测试带方法体的方法"""
        body = MethodBody(lines=["返回 42;"])
        method = MethodInfo(
            name="获取值",
            return_type="整数型",
            parameters=[],
            visibility=Visibility.PUBLIC,
            line_number=10,
            body=body
        )
        
        assert method.body is not None
        assert len(method.body.lines) == 1
    
    def test_abstract_method(self):
        """测试抽象方法"""
        method = MethodInfo(
            name="绘制",
            return_type="空型",
            parameters=[],
            visibility=Visibility.PUBLIC,
            line_number=10,
            is_abstract=True
        )
        
        assert method.is_abstract
        assert method.body is None
    
    def test_method_with_parameters(self):
        """测试带参数的方法"""
        params = [
            ParameterInfo("名", "字符串型"),
            ParameterInfo("龄", "整数型")
        ]
        method = MethodInfo(
            name="设置信息",
            return_type="空型",
            parameters=params,
            visibility=Visibility.PUBLIC,
            line_number=10
        )
        
        assert len(method.parameters) == 2
        assert method.parameters[0].name == "名"
        assert method.parameters[1].name == "龄"


class TestClassInfoExtended:
    """测试扩展的类信息"""
    
    def test_class_inheritance_chain(self):
        """测试继承链"""
        cls = ClassInfo(
            name="学生",
            base_class="人员",
            inheritance_chain=["人员", "学生"]
        )
        
        assert cls.base_class == "人员"
        assert len(cls.inheritance_chain) == 2
    
    def test_get_constructor(self):
        """测试获取构造函数"""
        cls = ClassInfo(name="学生", line_number=10)
        
        # 添加构造函数
        constructor = MethodInfo(
            name="构造函数",
            return_type="空型",
            parameters=[],
            visibility=Visibility.PUBLIC,
            is_constructor=True,
            line_number=15
        )
        cls.add_method(constructor)
        
        # 添加普通方法
        method = MethodInfo(
            name="获取信息",
            return_type="字符串型",
            parameters=[],
            visibility=Visibility.PUBLIC,
            line_number=20
        )
        cls.add_method(method)
        
        # 获取构造函数
        found = cls.get_constructor()
        assert found is not None
        assert found.is_constructor
        assert found.name == "构造函数"
    
    def test_get_all_methods(self):
        """测试获取所有方法"""
        cls = ClassInfo(name="学生", line_number=10)
        
        method1 = MethodInfo(
            name="方法1",
            return_type="空型",
            parameters=[],
            visibility=Visibility.PUBLIC,
            line_number=15
        )
        method2 = MethodInfo(
            name="方法2",
            return_type="空型",
            parameters=[],
            visibility=Visibility.PRIVATE,
            line_number=20
        )
        
        cls.add_method(method1)
        cls.add_method(method2)
        
        all_methods = cls.get_all_methods()
        assert len(all_methods) == 2


class TestParseState:
    """测试解析状态枚举"""
    
    def test_parse_state_values(self):
        """测试解析状态枚举值"""
        assert ParseState.IDLE.value == "idle"
        assert ParseState.IN_CLASS.value == "in_class"
        assert ParseState.IN_METHOD_BODY.value == "in_method_body"


class TestAttributeTypeExtended:
    """测试扩展的属性类型"""
    
    def test_attribute_type_values(self):
        """测试属性类型枚举值"""
        # 注意：class_extended.py 使用 CLASS_VAR 而不是 CLASS
        assert AttributeType.INSTANCE.value == "instance"
        assert AttributeType.CLASS_VAR.value == "class_var"
        assert AttributeType.CONSTANT.value == "constant"


class TestClassHierarchy:
    """测试类层次结构"""
    
    def test_single_inheritance(self):
        """测试单继承"""
        base = ClassInfo(name="动物", line_number=10)
        derived = ClassInfo(
            name="狗",
            base_class="动物",
            inheritance_chain=["动物", "狗"],
            line_number=20
        )
        
        assert derived.base_class == "动物"
        assert "动物" in derived.inheritance_chain
        assert "狗" in derived.inheritance_chain
    
    def test_multi_level_inheritance(self):
        """测试多级继承"""
        # 动物 -> 哺乳动物 -> 狗
        animal = ClassInfo(name="动物", line_number=10)
        mammal = ClassInfo(
            name="哺乳动物",
            base_class="动物",
            inheritance_chain=["动物", "哺乳动物"],
            line_number=20
        )
        dog = ClassInfo(
            name="狗",
            base_class="哺乳动物",
            inheritance_chain=["动物", "哺乳动物", "狗"],
            line_number=30
        )
        
        assert dog.base_class == "哺乳动物"
        assert len(dog.inheritance_chain) == 3
    
    def test_abstract_class_hierarchy(self):
        """测试抽象类层次结构"""
        abstract_base = ClassInfo(
            name="形状",
            is_abstract=True,
            line_number=10
        )
        
        concrete = ClassInfo(
            name="圆形",
            base_class="形状",
            inheritance_chain=["形状", "圆形"],
            line_number=20
        )
        
        assert abstract_base.is_abstract
        assert not concrete.is_abstract
        assert concrete.base_class == "形状"


class TestMethodOverriding:
    """测试方法重写"""
    
    def test_virtual_method(self):
        """测试虚函数"""
        base_method = MethodInfo(
            name="绘制",
            return_type="空型",
            parameters=[],
            visibility=Visibility.PUBLIC,
            is_virtual=True,
            line_number=10
        )
        
        assert base_method.is_virtual
    
    def test_method_override_in_derived(self):
        """测试派生类重写方法"""
        base = ClassInfo(name="形状", line_number=10)
        base_method = MethodInfo(
            name="绘制",
            return_type="空型",
            parameters=[],
            visibility=Visibility.PUBLIC,
            is_virtual=True,
            line_number=15
        )
        base.add_method(base_method)
        
        derived = ClassInfo(
            name="圆形",
            base_class="形状",
            line_number=20
        )
        derived_method = MethodInfo(
            name="绘制",
            return_type="空型",
            parameters=[],
            visibility=Visibility.PUBLIC,
            is_virtual=True,
            line_number=25
        )
        derived.add_method(derived_method)
        
        # 两个类都有"绘制"方法
        assert len(base.methods) == 1
        assert len(derived.methods) == 1
        assert base.methods[0].name == "绘制"
        assert derived.methods[0].name == "绘制"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
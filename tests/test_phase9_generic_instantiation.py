#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 9 泛型实例化集成测试

测试 GenericInstantiator 集成到 SemanticAnalyzer 的功能。
"""

import pytest
from zhc.parser.lexer import Lexer
from zhc.parser.parser import Parser
from zhc.semantic.semantic_analyzer import SemanticAnalyzer
from zhc.parser.ast_nodes import ASTNodeType


class TestPhase9GenericInstantiation:
    """Phase 9 泛型实例化集成测试"""

    def test_instantiator_lazy_init(self):
        """测试 instantiator 延迟初始化"""
        analyzer = SemanticAnalyzer()
        
        # 初始状态
        assert analyzer._instantiator is None
        
        # 访问后应该初始化
        inst = analyzer.instantiator
        assert inst is not None
        assert analyzer._instantiator is inst

    def test_generic_function_instantiation_integration(self):
        """测试泛型函数实例化集成"""
        # 这是一个端到端测试，需要完整的编译流程
        # 由于泛型解析和实例化需要多个模块配合，这里测试基本流程
        
        analyzer = SemanticAnalyzer()
        
        # 验证 analyzer 有必要的属性
        assert hasattr(analyzer, 'instantiator')
        assert hasattr(analyzer, 'generic_manager')
        assert hasattr(analyzer, '_register_function_instance')

    def test_register_function_instance(self):
        """测试注册实例化后的泛型函数"""
        from zhc.semantic.generics import (
            GenericFunction, FunctionInstance, TypeParameter, ParamInfo
        )
        
        analyzer = SemanticAnalyzer()
        
        # 创建泛型函数
        type_params = [TypeParameter(name="T")]
        generic_func = GenericFunction(
            name="最大值",
            type_params=type_params,
            params=[
                ParamInfo(name="a", type_name="T"),
                ParamInfo(name="b", type_name="T"),
            ],
            return_type="T"
        )
        
        # 注册泛型函数
        analyzer.generic_manager.register_generic_function(generic_func)
        
        # 实例化
        instance = analyzer.instantiator.instantiate_function(
            generic_func, ["整数型"]
        )
        
        # 验证实例化结果
        assert isinstance(instance, FunctionInstance)
        assert instance.specialized_return_type == "整数型"
        assert len(instance.specialized_params) == 2
        
        # 注册到符号表
        analyzer._register_function_instance(instance)
        
        # 验证符号表中有该函数
        symbol = analyzer.symbol_table.lookup("最大值__整数型")
        assert symbol is not None
        assert symbol.return_type == "整数型"

    def test_generic_type_instantiation_integration(self):
        """测试泛型类型实例化集成"""
        from zhc.semantic.generics import (
            GenericType, GenericTypeInstance, TypeParameter
        )
        
        analyzer = SemanticAnalyzer()
        
        # 创建泛型类型
        type_params = [TypeParameter(name="T")]
        generic_type = GenericType(
            name="列表",
            type_params=type_params,
            members=[]
        )
        
        # 注册泛型类型
        analyzer.generic_manager.register_generic_type(generic_type)
        
        # 实例化
        instance = analyzer.instantiator.instantiate_type(
            generic_type, ["整数型"]
        )
        
        # 验证实例化结果
        assert isinstance(instance, GenericTypeInstance)
        assert instance.generic_type.name == "列表"
        assert instance.type_args == ["整数型"]

    def test_generic_manager_is_generic_function(self):
        """测试泛型函数检测"""
        from zhc.semantic.generics import GenericFunction, TypeParameter, ParamInfo
        
        analyzer = SemanticAnalyzer()
        
        # 创建泛型函数
        type_params = [TypeParameter(name="T")]
        generic_func = GenericFunction(
            name="测试函数",
            type_params=type_params,
            params=[ParamInfo(name="x", type_name="T")],
            return_type="T"
        )
        
        # 注册
        analyzer.generic_manager.register_generic_function(generic_func)
        
        # 检测
        assert analyzer.generic_manager.is_generic_function("测试函数") is True
        assert analyzer.generic_manager.is_generic_function("不存在的函数") is False

    def test_instantiator_creates_correct_function_name(self):
        """测试实例化后函数名正确"""
        from zhc.semantic.generics import (
            GenericFunction, TypeParameter, ParamInfo
        )
        
        analyzer = SemanticAnalyzer()
        
        # 创建泛型函数
        generic_func = GenericFunction(
            name="最大值",
            type_params=[TypeParameter(name="T")],
            params=[
                ParamInfo(name="a", type_name="T"),
                ParamInfo(name="b", type_name="T"),
            ],
            return_type="T"
        )
        
        analyzer.generic_manager.register_generic_function(generic_func)
        
        # 实例化为整数型
        instance = analyzer.instantiator.instantiate_function(
            generic_func, ["整数型"]
        )
        
        # 验证修饰后的名字
        assert instance.name == "最大值__整数型"


class TestGenericInstantiatorDirect:
    """直接测试 GenericInstantiator 功能"""

    def test_type_instantiation_with_constraints(self):
        """测试带约束的类型实例化"""
        from zhc.semantic.generics import (
            GenericType, TypeParameter, TypeConstraint, OperatorSignature
        )
        from zhc.semantic.generic_instantiator import GenericInstantiator
        
        # 创建约束
        comparable = TypeConstraint(
            name="可比较",
            required_operators=[
                OperatorSignature(operator="<"),
                OperatorSignature(operator=">"),
            ]
        )
        
        # 创建带约束的泛型类型
        type_params = [TypeParameter(name="T", constraints=[comparable])]
        generic_type = GenericType(
            name="容器",
            type_params=type_params,
            members=[]
        )
        
        instantiator = GenericInstantiator()
        
        # 实例化应该成功（整数型满足可比较约束）
        instance = instantiator.instantiate_type(generic_type, ["整数型"])
        assert instance.type_args == ["整数型"]

    def test_function_instantiation_caching(self):
        """测试函数实例化缓存"""
        from zhc.semantic.generics import (
            GenericFunction, TypeParameter, ParamInfo
        )
        from zhc.semantic.generic_instantiator import GenericInstantiator
        
        generic_func = GenericFunction(
            name="缓存测试",
            type_params=[TypeParameter(name="T")],
            params=[ParamInfo(name="x", type_name="T")],
            return_type="T"
        )
        
        instantiator = GenericInstantiator()
        
        # 第一次实例化
        instance1 = instantiator.instantiate_function(generic_func, ["整数型"])
        
        # 第二次实例化同一类型
        instance2 = instantiator.instantiate_function(generic_func, ["整数型"])
        
        # 应该返回缓存的实例
        assert instance1 is instance2
        
        # 统计信息
        stats = instantiator.get_statistics()
        assert stats['cache_hits'] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
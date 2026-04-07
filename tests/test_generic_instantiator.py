#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泛型实例化器测试 - Test Generic Instantiator

测试泛型实例化功能：
1. 泛型类型实例化
2. 泛型函数实例化
3. 约束检查
4. 实例缓存
5. 类型推导

Phase 4 - Stage 2 - Task 11.1 Day 3

作者：ZHC 开发团队
日期：2026-04-08
"""

import pytest
import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 导入测试框架
from zhc.errors import LexerError

# 导入泛型系统
from zhc.semantic.generics import (
    TypeParameter,
    TypeConstraint,
    GenericType,
    GenericFunction,
    GenericManager,
    get_generic_manager,
    reset_generic_manager,
    TypeParameterCountError,
    ConstraintViolationError,
    Variance,
    MemberInfo,
    ParamInfo,
    PredefinedConstraints,
    create_generic_type,
    create_generic_function,
)

# 导入实例化器
from zhc.semantic.generic_instantiator import (
    GenericInstantiator,
    GenericTypeInferrer,
    InstantiationContext,
    get_instantiator,
    reset_instantiator,
    instantiate_generic_type,
    instantiate_generic_function,
)


class TestInstantiationContext:
    """测试实例化上下文"""
    
    def test_create_context(self):
        """测试创建上下文"""
        context = InstantiationContext()
        
        assert context.type_mapping == {}
        assert context.instantiated_types == set()
        assert context.instantiated_functions == set()
        assert context.instantiation_stack == []
    
    def test_push_pop_type(self):
        """测试类型栈操作"""
        context = InstantiationContext()
        
        assert context.push_type("列表") is True
        assert context.instantiation_stack == ["列表"]
        
        popped = context.pop_type()
        assert popped == "列表"
        assert context.instantiation_stack == []
    
    def test_circular_dependency_detection(self):
        """测试循环依赖检测"""
        context = InstantiationContext()
        
        context.push_type("A")
        context.push_type("B")
        
        # 尝试添加已存在的类型
        assert context.push_type("A") is False
        assert len(context.errors) == 1
        assert "循环依赖" in context.errors[0]
    
    def test_is_instantiating(self):
        """测试实例化状态检查"""
        context = InstantiationContext()
        
        context.push_type("列表")
        
        assert context.is_instantiating("列表") is True
        assert context.is_instantiating("映射") is False


class TestGenericInstantiator:
    """测试泛型实例化器"""
    
    def setup_method(self):
        """每个测试前重置"""
        reset_generic_manager()
        reset_instantiator()
    
    def test_instantiate_simple_type(self):
        """测试简单类型实例化"""
        instantiator = get_instantiator()
        manager = get_generic_manager()
        
        # 创建泛型类型
        generic_list = GenericType(
            name="列表",
            type_params=[TypeParameter(name="T")],
            members=[
                MemberInfo(name="数据", type_name="T[]"),
                MemberInfo(name="长度", type_name="整数型"),
            ]
        )
        manager.register_generic_type(generic_list)
        
        # 实例化
        instance = instantiator.instantiate_type(generic_list, ["整数型"])
        
        assert instance.name == "列表<整数型>"
        assert instance.type_args == ["整数型"]
        assert len(instance.members) == 2
    
    def test_instantiate_type_with_constraint(self):
        """测试带约束的类型实例化"""
        instantiator = get_instantiator()
        manager = get_generic_manager()
        
        # 创建带约束的泛型类型
        comparable = PredefinedConstraints.comparable()
        generic_max = GenericFunction(
            name="最大值",
            type_params=[TypeParameter(name="T", constraints=[comparable])],
            params=[
                ParamInfo(name="a", type_name="T"),
                ParamInfo(name="b", type_name="T"),
            ],
            return_type="T"
        )
        manager.register_generic_function(generic_max)
        
        # 整数型满足可比较约束，应该成功
        instance = instantiator.instantiate_function(generic_max, ["整数型"])
        
        assert instance.name == "最大值__整数型"
        assert instance.specialized_params[0].type_name == "整数型"
        assert instance.specialized_params[1].type_name == "整数型"
        assert instance.specialized_return_type == "整数型"
    
    def test_instantiate_type_constraint_violation(self):
        """测试约束违反"""
        instantiator = get_instantiator()
        manager = get_generic_manager()
        
        # 创建带数值约束的泛型函数
        numeric = PredefinedConstraints.numeric()
        generic_add = GenericFunction(
            name="加法",
            type_params=[TypeParameter(name="T", constraints=[numeric])],
            params=[
                ParamInfo(name="a", type_name="T"),
                ParamInfo(name="b", type_name="T"),
            ],
            return_type="T"
        )
        manager.register_generic_function(generic_add)
        
        # 字符串型不满足数值约束，应该失败
        with pytest.raises(ConstraintViolationError):
            instantiator.instantiate_function(generic_add, ["字符串型"])
    
    def test_type_parameter_count_error(self):
        """测试类型参数数量错误"""
        instantiator = get_instantiator()
        manager = get_generic_manager()
        
        # 创建需要 2 个类型参数的泛型类型
        generic_pair = GenericType(
            name="对",
            type_params=[
                TypeParameter(name="K"),
                TypeParameter(name="V"),
            ]
        )
        manager.register_generic_type(generic_pair)
        
        # 只提供 1 个类型参数，应该失败
        with pytest.raises(TypeParameterCountError):
            instantiator.instantiate_type(generic_pair, ["整数型"])
    
    def test_caching(self):
        """测试实例缓存"""
        instantiator = get_instantiator()
        manager = get_generic_manager()
        
        # 创建泛型类型
        generic_list = GenericType(
            name="列表",
            type_params=[TypeParameter(name="T")]
        )
        manager.register_generic_type(generic_list)
        
        # 第一次实例化
        instance1 = instantiator.instantiate_type(generic_list, ["整数型"])
        
        # 第二次实例化（应该使用缓存）
        instance2 = instantiator.instantiate_type(generic_list, ["整数型"])
        
        assert instance1 is instance2  # 应该是同一个对象
    
    def test_multiple_type_arguments(self):
        """测试多类型参数"""
        instantiator = get_instantiator()
        manager = get_generic_manager()
        
        # 创建需要 2 个类型参数的泛型类型
        generic_pair = GenericType(
            name="对",
            type_params=[
                TypeParameter(name="K"),
                TypeParameter(name="V"),
            ],
            members=[
                MemberInfo(name="键", type_name="K"),
                MemberInfo(name="值", type_name="V"),
            ]
        )
        manager.register_generic_type(generic_pair)
        
        # 实例化
        instance = instantiator.instantiate_type(generic_pair, ["字符串型", "整数型"])
        
        assert instance.name == "对<字符串型, 整数型>"
        assert instance.type_args == ["字符串型", "整数型"]
        assert instance.members[0].type_name == "字符串型"
        assert instance.members[1].type_name == "整数型"
    
    def test_statistics(self):
        """测试统计信息"""
        instantiator = get_instantiator()
        manager = get_generic_manager()
        
        # 创建泛型类型
        generic_list = GenericType(
            name="列表",
            type_params=[TypeParameter(name="T")]
        )
        manager.register_generic_type(generic_list)
        
        # 实例化两次（第二次命中缓存）
        instantiator.instantiate_type(generic_list, ["整数型"])
        instantiator.instantiate_type(generic_list, ["整数型"])
        
        stats = instantiator.get_statistics()
        
        assert stats['type_instantiations'] == 1
        assert stats['cache_hits'] == 1
    
    def test_clear_cache(self):
        """测试清空缓存"""
        instantiator = get_instantiator()
        manager = get_generic_manager()
        
        # 创建泛型类型
        generic_list = GenericType(
            name="列表",
            type_params=[TypeParameter(name="T")]
        )
        manager.register_generic_type(generic_list)
        
        # 实例化
        instantiator.instantiate_type(generic_list, ["整数型"])
        
        # 清空缓存
        instantiator.clear_cache()
        
        stats = instantiator.get_statistics()
        assert stats['type_instantiations'] == 0


class TestGenericTypeInferrer:
    """测试泛型类型推导器"""
    
    def setup_method(self):
        """每个测试前重置"""
        reset_generic_manager()
        reset_instantiator()
    
    def test_infer_from_parameters(self):
        """测试从参数推导"""
        instantiator = get_instantiator()
        manager = get_generic_manager()
        
        # 创建泛型函数
        generic_max = GenericFunction(
            name="最大值",
            type_params=[TypeParameter(name="T")],
            params=[
                ParamInfo(name="a", type_name="T"),
                ParamInfo(name="b", type_name="T"),
            ],
            return_type="T"
        )
        manager.register_generic_function(generic_max)
        
        # 推导
        inferrer = GenericTypeInferrer(instantiator)
        type_args = inferrer.infer_type_arguments(generic_max, ["整数型", "整数型"])
        
        assert type_args == ["整数型"]
    
    def test_infer_mixed_types(self):
        """测试混合类型推导"""
        instantiator = get_instantiator()
        manager = get_generic_manager()
        
        # 创建泛型函数
        generic_max = GenericFunction(
            name="最大值",
            type_params=[TypeParameter(name="T")],
            params=[
                ParamInfo(name="a", type_name="T"),
                ParamInfo(name="b", type_name="T"),
            ],
            return_type="T"
        )
        manager.register_generic_function(generic_max)
        
        # 推导（参数类型不一致）
        inferrer = GenericTypeInferrer(instantiator)
        type_args = inferrer.infer_type_arguments(generic_max, ["整数型", "浮点型"])
        
        assert type_args is None  # 类型冲突，应该返回 None
    
    def test_infer_with_default(self):
        """测试带默认值的推导"""
        instantiator = get_instantiator()
        manager = get_generic_manager()
        
        # 创建带默认值的泛型函数
        generic_func = GenericFunction(
            name="默认值函数",
            type_params=[TypeParameter(name="T", default="整数型")],
            params=[
                ParamInfo(name="a", type_name="T"),
            ],
            return_type="T"
        )
        manager.register_generic_function(generic_func)
        
        # 推导
        inferrer = GenericTypeInferrer(instantiator)
        type_args = inferrer.infer_type_arguments(generic_func, ["浮点型"])
        
        assert type_args == ["浮点型"]


class TestConvenienceFunctions:
    """测试便捷函数"""
    
    def setup_method(self):
        """每个测试前重置"""
        reset_generic_manager()
        reset_instantiator()
    
    def test_instantiate_generic_type(self):
        """测试便捷类型实例化"""
        manager = get_generic_manager()
        
        # 创建泛型类型
        generic_list = GenericType(
            name="列表",
            type_params=[TypeParameter(name="T")]
        )
        manager.register_generic_type(generic_list)
        
        # 实例化
        instance = instantiate_generic_type("列表", ["整数型"])
        
        assert instance.name == "列表<整数型>"
    
    def test_instantiate_generic_function(self):
        """测试便捷函数实例化"""
        manager = get_generic_manager()
        
        # 创建泛型函数
        generic_max = GenericFunction(
            name="最大值",
            type_params=[TypeParameter(name="T")],
            params=[
                ParamInfo(name="a", type_name="T"),
                ParamInfo(name="b", type_name="T"),
            ],
            return_type="T"
        )
        manager.register_generic_function(generic_max)
        
        # 实例化
        instance = instantiate_generic_function("最大值", ["整数型"])
        
        assert instance.name == "最大值__整数型"
    
    def test_instantiate_undefined_type(self):
        """测试未定义的泛型类型"""
        from zhc.semantic.generics import GenericError
        
        with pytest.raises(GenericError):
            instantiate_generic_type("未定义类型", ["整数型"])
    
    def test_instantiate_undefined_function(self):
        """测试未定义的泛型函数"""
        from zhc.semantic.generics import GenericError
        
        with pytest.raises(GenericError):
            instantiate_generic_function("未定义函数", ["整数型"])


class TestCreateFunctions:
    """测试创建函数"""
    
    def setup_method(self):
        """每个测试前重置"""
        reset_generic_manager()
    
    def test_create_generic_type(self):
        """测试创建泛型类型"""
        generic_type = create_generic_type(
            name="列表",
            type_params=[TypeParameter(name="T")],
            members=[MemberInfo(name="长度", type_name="整数型")]
        )
        
        assert generic_type.name == "列表"
        assert len(generic_type.type_params) == 1
        assert generic_type.type_params[0].name == "T"
        
        # 检查管理器
        manager = get_generic_manager()
        assert manager.is_generic_type("列表")
    
    def test_create_generic_function(self):
        """测试创建泛型函数"""
        generic_func = create_generic_function(
            name="最大值",
            type_params=[TypeParameter(name="T")],
            params=[
                ParamInfo(name="a", type_name="T"),
                ParamInfo(name="b", type_name="T"),
            ],
            return_type="T"
        )
        
        assert generic_func.name == "最大值"
        assert len(generic_func.type_params) == 1
        assert generic_func.type_params[0].name == "T"
        assert len(generic_func.params) == 2
        
        # 检查管理器
        manager = get_generic_manager()
        funcs = manager.get_generic_functions("最大值")
        assert len(funcs) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

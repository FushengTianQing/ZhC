"""
泛型类型系统单元测试

Phase 4 - Stage 2 - Task 11.1
测试泛型类型、泛型函数、类型约束等功能

作者：ZHC 开发团队
日期：2026-04-08
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.semantic.generics import (
    # 类型和约束
    TypeParameter, TypeConstraint, GenericType, GenericTypeInstance,
    GenericFunction, FunctionInstance, MemberInfo, ParamInfo,
    MethodSignature, OperatorSignature, Variance,
    # 约束和预设
    PredefinedConstraints,
    # 异常
    GenericError, TypeParameterCountError, ConstraintViolationError,
    # 管理器
    GenericManager, get_generic_manager, reset_generic_manager,
    # 便捷函数
    create_generic_type, create_generic_function, create_constraint,
)


class TestTypeParameter:
    """类型参数测试"""

    def test_simple_type_parameter(self):
        """测试简单类型参数"""
        param = TypeParameter(name="T")
        assert param.name == "T"
        assert param.constraints == []
        assert param.default is None
        assert param.variance == Variance.INVARIANT

    def test_type_parameter_with_constraints(self):
        """测试带约束的类型参数"""
        constraint = TypeConstraint(
            name="可比较",
            required_operators=[
                OperatorSignature(operator="<", return_type="逻辑型"),
                OperatorSignature(operator=">", return_type="逻辑型"),
            ]
        )
        param = TypeParameter(name="T", constraints=[constraint])
        assert param.name == "T"
        assert len(param.constraints) == 1
        assert param.constraints[0].name == "可比较"

    def test_type_parameter_with_default(self):
        """测试带默认值的类型参数"""
        param = TypeParameter(name="T", default="整数型")
        assert param.default == "整数型"

    def test_type_parameter_str(self):
        """测试类型参数字符串表示"""
        param = TypeParameter(name="T")
        assert str(param) == "T"

        constraint = TypeConstraint(name="可比较")
        param_with_constraint = TypeParameter(name="T", constraints=[constraint])
        assert "可比较" in str(param_with_constraint)


class TestTypeConstraint:
    """类型约束测试"""

    def test_simple_constraint(self):
        """测试简单约束"""
        constraint = TypeConstraint(
            name="可比较",
            required_operators=[
                OperatorSignature(operator="<", return_type="逻辑型"),
            ]
        )
        assert constraint.name == "可比较"
        assert len(constraint.required_operators) == 1

    def test_constraint_with_methods(self):
        """测试带方法的约束"""
        constraint = TypeConstraint(
            name="可打印",
            required_methods=[
                MethodSignature(name="转字符串", return_type="字符串型"),
            ]
        )
        assert len(constraint.required_methods) == 1
        assert constraint.required_methods[0].name == "转字符串"

    def test_constraint_equality(self):
        """测试约束相等性"""
        c1 = TypeConstraint(name="可比较")
        c2 = TypeConstraint(name="可比较")
        c3 = TypeConstraint(name="可加")

        assert c1 == c2
        assert c1 != c3


class TestGenericType:
    """泛型类型测试"""

    def setup_method(self):
        """每个测试前重置管理器"""
        reset_generic_manager()

    def test_simple_generic_type(self):
        """测试简单泛型类型"""
        t = TypeParameter(name="T")
        generic_type = GenericType(
            name="列表",
            type_params=[t],
            members=[
                MemberInfo(name="数据", type_name="T"),
                MemberInfo(name="长度", type_name="整数型"),
            ]
        )

        assert generic_type.name == "列表"
        assert len(generic_type.type_params) == 1
        assert generic_type.type_params[0].name == "T"

    def test_generic_type_instantiation(self):
        """测试泛型类型实例化"""
        t = TypeParameter(name="T")
        generic_type = GenericType(
            name="列表",
            type_params=[t],
            members=[
                MemberInfo(name="数据", type_name="T"),
            ]
        )

        # 实例化为 列表<整数型>
        instance = generic_type.instantiate(["整数型"])

        assert instance.name == "列表<整数型>"
        assert instance.generic_type == generic_type
        assert instance.type_args == ["整数型"]

    def test_generic_type_instantiation_with_multiple_params(self):
        """测试多类型参数实例化"""
        k = TypeParameter(name="K")
        v = TypeParameter(name="V")
        generic_type = GenericType(
            name="映射",
            type_params=[k, v],
            members=[
                MemberInfo(name="键", type_name="K"),
                MemberInfo(name="值", type_name="V"),
            ]
        )

        instance = generic_type.instantiate(["字符串型", "整数型"])

        assert instance.name == "映射<字符串型, 整数型>"
        assert instance.type_args == ["字符串型", "整数型"]

    def test_generic_type_parameter_count_mismatch(self):
        """测试类型参数数量不匹配"""
        t = TypeParameter(name="T")
        generic_type = GenericType(name="列表", type_params=[t])

        # 提供 2 个类型参数，但只需要 1 个
        with pytest.raises(TypeParameterCountError) as exc_info:
            generic_type.instantiate(["整数型", "字符串型"])

        assert "需要 1 个类型参数" in str(exc_info.value)
        assert "提供了 2 个" in str(exc_info.value)

    def test_generic_type_caching(self):
        """测试实例化缓存"""
        t = TypeParameter(name="T")
        generic_type = GenericType(name="盒子", type_params=[t])

        # 多次实例化同一类型应返回缓存的结果
        instance1 = generic_type.instantiate(["整数型"])
        instance2 = generic_type.instantiate(["整数型"])

        assert instance1 is instance2  # 应该是同一个对象

    def test_generic_type_str(self):
        """测试泛型类型字符串表示"""
        t = TypeParameter(name="T")
        generic_type = GenericType(name="列表", type_params=[t])

        assert str(generic_type) == "列表<T>"

        generic_type2 = GenericType(name="映射", type_params=[
            TypeParameter(name="K"),
            TypeParameter(name="V")
        ])
        assert str(generic_type2) == "映射<K, V>"


class TestGenericFunction:
    """泛型函数测试"""

    def setup_method(self):
        """每个测试前重置管理器"""
        reset_generic_manager()

    def test_simple_generic_function(self):
        """测试简单泛型函数"""
        t = TypeParameter(name="T")
        generic_func = GenericFunction(
            name="最大值",
            type_params=[t],
            params=[
                ParamInfo(name="a", type_name="T"),
                ParamInfo(name="b", type_name="T"),
            ],
            return_type="T"
        )

        assert generic_func.name == "最大值"
        assert len(generic_func.type_params) == 1
        assert len(generic_func.params) == 2

    def test_generic_function_instantiation(self):
        """测试泛型函数实例化"""
        t = TypeParameter(name="T")
        generic_func = GenericFunction(
            name="最大值",
            type_params=[t],
            params=[
                ParamInfo(name="a", type_name="T"),
                ParamInfo(name="b", type_name="T"),
            ],
            return_type="T"
        )

        # 实例化
        instance = generic_func.instantiate(["整数型"])

        assert instance.name == "最大值__整数型"
        assert instance.generic_function == generic_func
        assert instance.specialized_return_type == "整数型"
        assert len(instance.specialized_params) == 2
        assert instance.specialized_params[0].type_name == "整数型"
        assert instance.specialized_params[1].type_name == "整数型"

    def test_generic_function_parameter_substitution(self):
        """测试参数类型替换"""
        k = TypeParameter(name="K")
        v = TypeParameter(name="V")
        generic_func = GenericFunction(
            name="创建对",
            type_params=[k, v],
            params=[
                ParamInfo(name="first", type_name="K"),
                ParamInfo(name="second", type_name="V"),
            ],
            return_type=f"({k.name}, {v.name})"
        )

        instance = generic_func.instantiate(["字符串型", "整数型"])

        assert instance.specialized_params[0].type_name == "字符串型"
        assert instance.specialized_params[1].type_name == "整数型"
        assert "字符串型" in instance.specialized_return_type
        assert "整数型" in instance.specialized_return_type

    def test_generic_function_mangled_name(self):
        """测试修饰名称生成"""
        generic_func = GenericFunction(
            name="最大值",
            type_params=[TypeParameter(name="T")],
            params=[],
            return_type="T"
        )

        assert generic_func.get_mangled_name(["整数型"]) == "最大值__整数型"
        assert generic_func.get_mangled_name(["字符串型", "整数型"]) == "最大值__字符串型_整数型"


class TestPredefinedConstraints:
    """预定义约束测试"""

    def test_comparable_constraint(self):
        """测试可比较约束"""
        constraint = PredefinedConstraints.comparable()

        assert constraint.name == "可比较"
        assert len(constraint.required_operators) == 3
        operators = {op.operator for op in constraint.required_operators}
        assert operators == {"<", ">", "=="}

    def test_equatable_constraint(self):
        """测试可相等约束"""
        constraint = PredefinedConstraints.equatable()

        assert constraint.name == "可相等"
        operators = {op.operator for op in constraint.required_operators}
        assert operators == {"==", "!="}

    def test_addable_constraint(self):
        """测试可加约束"""
        constraint = PredefinedConstraints.addable()

        assert constraint.name == "可加"
        assert len(constraint.required_operators) == 1
        assert constraint.required_operators[0].operator == "+"

    def test_numeric_constraint(self):
        """测试数值约束"""
        constraint = PredefinedConstraints.numeric()

        assert constraint.name == "数值型"
        operators = {op.operator for op in constraint.required_operators}
        assert operators == {"+", "-", "*", "/"}


class TestGenericManager:
    """泛型管理器测试"""

    def setup_method(self):
        """每个测试前重置管理器"""
        reset_generic_manager()

    def test_register_generic_type(self):
        """测试注册泛型类型"""
        manager = get_generic_manager()
        generic_type = GenericType(name="列表", type_params=[TypeParameter(name="T")])

        manager.register_generic_type(generic_type)

        assert manager.get_generic_type("列表") == generic_type
        assert manager.is_generic_type("列表")
        assert not manager.is_generic_type("不存在")

    def test_register_generic_function(self):
        """测试注册泛型函数"""
        manager = get_generic_manager()
        generic_func = GenericFunction(
            name="最大值",
            type_params=[TypeParameter(name="T")],
            params=[],
            return_type="T"
        )

        manager.register_generic_function(generic_func)

        funcs = manager.get_generic_functions("最大值")
        assert len(funcs) == 1
        assert funcs[0] == generic_func
        assert manager.is_generic_function("最大值")

    def test_register_constraint(self):
        """测试注册约束"""
        manager = get_generic_manager()
        constraint = TypeConstraint(name="自定义约束")

        manager.register_constraint(constraint)

        assert manager.get_constraint("自定义约束") == constraint

    def test_predefined_constraints(self):
        """测试预定义约束"""
        manager = get_generic_manager()

        assert manager.get_constraint("可比较") is not None
        assert manager.get_constraint("可加") is not None
        assert manager.get_constraint("数值型") is not None

    def test_instantiate_type(self):
        """测试实例化类型"""
        manager = get_generic_manager()
        generic_type = GenericType(
            name="盒子",
            type_params=[TypeParameter(name="T")]
        )
        manager.register_generic_type(generic_type)

        instance = manager.instantiate_type("盒子", ["整数型"])
        assert instance.name == "盒子<整数型>"

    def test_instantiate_function(self):
        """测试实例化函数"""
        manager = get_generic_manager()
        generic_func = GenericFunction(
            name="交换",
            type_params=[TypeParameter(name="T")],
            params=[
                ParamInfo(name="a", type_name="T"),
                ParamInfo(name="b", type_name="T"),
            ],
            return_type="T"
        )
        manager.register_generic_function(generic_func)

        instance = manager.instantiate_function("交换", ["浮点型"])
        assert instance.name == "交换__浮点型"

    def test_statistics(self):
        """测试统计信息"""
        manager = get_generic_manager()

        # 注册一些泛型
        manager.register_generic_type(GenericType(
            name="列表", type_params=[TypeParameter(name="T")]
        ))
        manager.register_generic_function(GenericFunction(
            name="最大值",
            type_params=[TypeParameter(name="T")],
            params=[],
            return_type="T"
        ))

        stats = manager.get_statistics()
        assert stats["generic_types"] == 1
        assert stats["generic_functions"] == 1
        assert stats["constraints"] >= 4  # 至少有预定义约束


class TestConvenienceFunctions:
    """便捷函数测试"""

    def setup_method(self):
        """每个测试前重置管理器"""
        reset_generic_manager()

    def test_create_generic_type(self):
        """测试便捷创建泛型类型"""
        t = TypeParameter(name="T")
        generic_type = create_generic_type(
            name="栈",
            type_params=[t],
            members=[
                MemberInfo(name="数据", type_name="T"),
                MemberInfo(name="栈顶", type_name="整数型"),
            ]
        )

        # 应该已经注册到管理器
        manager = get_generic_manager()
        assert manager.get_generic_type("栈") == generic_type

    def test_create_generic_function(self):
        """测试便捷创建泛型函数"""
        t = TypeParameter(name="T")
        generic_func = create_generic_function(
            name="最小值",
            type_params=[t],
            params=[
                ParamInfo(name="a", type_name="T"),
                ParamInfo(name="b", type_name="T"),
            ],
            return_type="T"
        )

        manager = get_generic_manager()
        funcs = manager.get_generic_functions("最小值")
        assert len(funcs) == 1
        assert funcs[0].name == "最小值"

    def test_create_constraint(self):
        """测试便捷创建约束"""
        constraint = create_constraint(
            name="可迭代",
            operators=["==", "!="]
        )

        manager = get_generic_manager()
        assert manager.get_constraint("可迭代") == constraint


class TestIntegration:
    """集成测试"""

    def setup_method(self):
        """每个测试前重置管理器"""
        reset_generic_manager()

    def test_generic_list_usage(self):
        """测试泛型列表使用场景"""
        manager = get_generic_manager()

        # 创建 列表<T> 类型
        t = TypeParameter(name="T")
        list_type = GenericType(
            name="列表",
            type_params=[t],
            members=[
                MemberInfo(name="数据", type_name="T"),
                MemberInfo(name="长度", type_name="整数型"),
            ]
        )
        manager.register_generic_type(list_type)

        # 实例化为 列表<整数型>
        int_list = list_type.instantiate(["整数型"])
        assert int_list.name == "列表<整数型>"
        assert int_list.get_member("长度").type_name == "整数型"

        # 实例化为 列表<字符串型>
        str_list = list_type.instantiate(["字符串型"])
        assert str_list.name == "列表<字符串型>"
        assert str_list.get_member("长度").type_name == "整数型"

    def test_generic_swap_function(self):
        """测试泛型交换函数"""
        manager = get_generic_manager()

        # 创建 交换<T>(T, T) 函数
        t = TypeParameter(name="T")
        swap_func = GenericFunction(
            name="交换",
            type_params=[t],
            params=[
                ParamInfo(name="a", type_name="T"),
                ParamInfo(name="b", type_name="T"),
            ],
            return_type="(T, T)"
        )
        manager.register_generic_function(swap_func)

        # 实例化
        int_swap = swap_func.instantiate(["整数型"])
        assert int_swap.name == "交换__整数型"
        assert int_swap.specialized_params[0].type_name == "整数型"

        str_swap = swap_func.instantiate(["字符串型"])
        assert str_swap.name == "交换__字符串型"
        assert str_swap.specialized_params[0].type_name == "字符串型"

    def test_generic_max_function_with_constraint(self):
        """测试带约束的泛型最大值函数"""
        manager = get_generic_manager()

        # 创建 可比较 约束
        comparable_constraint = PredefinedConstraints.comparable()
        manager.register_constraint(comparable_constraint)

        # 创建 最大值<T: 可比较> 函数
        t = TypeParameter(name="T", constraints=[comparable_constraint])
        max_func = GenericFunction(
            name="最大值",
            type_params=[t],
            params=[
                ParamInfo(name="a", type_name="T"),
                ParamInfo(name="b", type_name="T"),
            ],
            return_type="T"
        )
        manager.register_generic_function(max_func)

        # 实例化（整数型满足可比较约束）
        int_max = max_func.instantiate(["整数型"])
        assert int_max.name == "最大值__整数型"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

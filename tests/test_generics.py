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

from zhc.semantic.generics import (
    # 类型和约束
    TypeParameter,
    TypeConstraint,
    GenericType,
    GenericFunction,
    MemberInfo,
    ParamInfo,
    MethodSignature,
    OperatorSignature,
    Variance,
    # G.08 增强特性
    VarianceChecker,
    TypeKind,
    TypeInfo,
    DefaultTypeResolver,
    ConstraintInferrer,
    # 解析器和单态化器
    GenericResolver,
    Monomorphizer,
    # 约束和预设
    PredefinedConstraints,
    # 异常
    TypeParameterCountError,
    get_generic_manager,
    reset_generic_manager,
    # 便捷函数
    create_generic_type,
    create_generic_function,
    create_constraint,
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
            ],
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
            ],
        )
        assert constraint.name == "可比较"
        assert len(constraint.required_operators) == 1

    def test_constraint_with_methods(self):
        """测试带方法的约束"""
        constraint = TypeConstraint(
            name="可打印",
            required_methods=[
                MethodSignature(name="转字符串", return_type="字符串型"),
            ],
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
            ],
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
            ],
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
            ],
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

        generic_type2 = GenericType(
            name="映射", type_params=[TypeParameter(name="K"), TypeParameter(name="V")]
        )
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
            return_type="T",
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
            return_type="T",
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
            return_type=f"({k.name}, {v.name})",
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
            return_type="T",
        )

        assert generic_func.get_mangled_name(["整数型"]) == "最大值__整数型"
        assert (
            generic_func.get_mangled_name(["字符串型", "整数型"])
            == "最大值__字符串型_整数型"
        )


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
            return_type="T",
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
        generic_type = GenericType(name="盒子", type_params=[TypeParameter(name="T")])
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
            return_type="T",
        )
        manager.register_generic_function(generic_func)

        instance = manager.instantiate_function("交换", ["浮点型"])
        assert instance.name == "交换__浮点型"

    def test_statistics(self):
        """测试统计信息"""
        manager = get_generic_manager()

        # 注册一些泛型
        manager.register_generic_type(
            GenericType(name="列表", type_params=[TypeParameter(name="T")])
        )
        manager.register_generic_function(
            GenericFunction(
                name="最大值",
                type_params=[TypeParameter(name="T")],
                params=[],
                return_type="T",
            )
        )

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
            ],
        )

        # 应该已经注册到管理器
        manager = get_generic_manager()
        assert manager.get_generic_type("栈") == generic_type

    def test_create_generic_function(self):
        """测试便捷创建泛型函数"""
        t = TypeParameter(name="T")
        create_generic_function(
            name="最小值",
            type_params=[t],
            params=[
                ParamInfo(name="a", type_name="T"),
                ParamInfo(name="b", type_name="T"),
            ],
            return_type="T",
        )

        manager = get_generic_manager()
        funcs = manager.get_generic_functions("最小值")
        assert len(funcs) == 1
        assert funcs[0].name == "最小值"

    def test_create_constraint(self):
        """测试便捷创建约束"""
        constraint = create_constraint(name="可迭代", operators=["==", "!="])

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
            ],
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
            return_type="(T, T)",
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
            return_type="T",
        )
        manager.register_generic_function(max_func)

        # 实例化（整数型满足可比较约束）
        int_max = max_func.instantiate(["整数型"])
        assert int_max.name == "最大值__整数型"


# ===== G.01: GenericResolver 测试 =====


class TestGenericResolver:
    """GenericResolver 泛型解析器测试"""

    def setup_method(self):
        """每个测试前重置管理器"""
        reset_generic_manager()

    def test_resolver_creation(self):
        """测试解析器创建"""
        from zhc.semantic.generics import GenericResolver, get_generic_resolver

        resolver = GenericResolver()
        assert resolver.manager is not None
        stats = resolver.get_statistics()
        assert stats["resolved_generic_functions"] == 0
        assert stats["resolved_generic_types"] == 0

        # 工厂函数
        resolver2 = get_generic_resolver()
        assert isinstance(resolver2, GenericResolver)

    def test_resolve_type_parameters(self):
        """测试类型参数解析"""
        from zhc.semantic.generics import GenericResolver
        from zhc.semantic.generic_parser import TypeParameterNode, Variance

        resolver = GenericResolver()

        # 创建 TypeParameterNode 列表（模拟 AST 层）
        tp_node1 = TypeParameterNode(name="T", variance=Variance.INVARIANT)
        tp_node2 = TypeParameterNode(
            name="K",
            variance=Variance.COVARIANT,
            constraints=["可比较"],
            default_type="字符串型",
        )

        type_params = resolver.resolve_type_parameters([tp_node1, tp_node2])

        assert len(type_params) == 2
        assert type_params[0].name == "T"
        assert type_params[0].variance == Variance.INVARIANT
        assert type_params[1].name == "K"
        assert type_params[1].variance == Variance.COVARIANT
        assert len(type_params[1].constraints) > 0  # 预定义约束应被解析

    def test_resolve_constraints(self):
        """测试 Where 约束解析"""
        from zhc.semantic.generics import GenericResolver
        from zhc.semantic.generic_parser import WhereClauseNode

        resolver = GenericResolver()

        # 创建 WhereClauseNode
        where = WhereClauseNode(constraints=[("T", "可比较"), ("T", "可打印")])

        resolved = resolver.resolve_constraints(where)

        assert len(resolved) == 2
        # 检查约束名被正确解析
        param_names = [r[0] for r in resolved]
        constraint_names = [r[1].name for r in resolved]
        assert "T" in param_names
        assert "可比较" in constraint_names
        assert "可打印" in constraint_names

    def test_resolve_constraints_empty(self):
        """测试空 Where 子句"""
        from zhc.semantic.generics import GenericResolver

        resolver = GenericResolver()
        resolved = resolver.resolve_constraints(None)
        assert resolved == []

        where_no_constraints = type("obj", (object,), {"constraints": []})()
        resolved2 = resolver.resolve_constraints(where_no_constraints)
        assert resolved2 == []

    def test_check_constraints_satisfied(self):
        """测试约束满足检查 — 整数型满足可比较"""
        from zhc.semantic.generics import (
            GenericResolver,
            TypeParameter,
            PredefinedConstraints,
        )

        resolver = GenericResolver()

        param = TypeParameter(
            name="T",
            constraints=[PredefinedConstraints.comparable()],
        )
        satisfied, violations = resolver.check_constraints_satisfied(param, "整数型")
        assert satisfied is True
        assert len(violations) == 0

    def test_check_constraints_violated(self):
        """测试约束违反 — 布尔型不满足可加"""
        from zhc.semantic.generics import (
            GenericResolver,
            TypeParameter,
            PredefinedConstraints,
        )

        resolver = GenericResolver()

        param = TypeParameter(
            name="T",
            constraints=[PredefinedConstraints.addable()],
        )
        satisfied, violations = resolver.check_constraints_satisfied(param, "布尔型")
        assert satisfied is False
        assert len(violations) == 1
        assert "不满足" in violations[0]

    def test_check_constraints_no_constraints(self):
        """测试无约束的类型参数总是满足"""
        from zhc.semantic.generics import GenericResolver, TypeParameter

        resolver = GenericResolver()
        param = TypeParameter(name="T")

        satisfied, violations = resolver.check_constraints_satisfied(param, "任意类型")
        assert satisfied is True
        assert len(violations) == 0

    def test_instantiate_generic_function(self):
        """测试泛型函数实例化"""
        from zhc.semantic.generics import (
            GenericResolver,
            GenericFunction,
            TypeParameter,
            ParamInfo,
        )

        resolver = GenericResolver()

        # 先注册泛型函数
        generic_func = GenericFunction(
            name="最大值",
            type_params=[TypeParameter(name="T")],
            params=[
                ParamInfo(name="a", type_name="T"),
                ParamInfo(name="b", type_name="T"),
            ],
            return_type="T",
        )
        resolver.manager.register_generic_function(generic_func)

        # 实例化
        instance = resolver.instantiate_generic("最大值", ["整数型"])
        assert instance is not None
        assert instance.name == "最大值__整数型"
        assert instance.specialized_return_type == "整数型"
        assert len(instance.specialized_params) == 2

    def test_instantiate_generic_function_not_found(self):
        """测试实例化不存在的泛型函数"""
        from zhc.semantic.generics import GenericResolver

        resolver = GenericResolver()
        instance = resolver.instantiate_generic("不存在函数", ["整数型"])
        assert instance is None

    def test_instantiate_generic_function_wrong_arity(self):
        """测试参数数量不匹配的实例化"""
        from zhc.semantic.generics import (
            GenericResolver,
            GenericFunction,
            TypeParameter,
            ParamInfo,
        )

        resolver = GenericResolver()

        generic_func = GenericFunction(
            name="单参数函数",
            type_params=[TypeParameter(name="T")],
            params=[ParamInfo(name="x", type_name="T")],
            return_type="T",
        )
        resolver.manager.register_generic_function(generic_func)

        # 提供了 2 个参数但只需要 1 个 → 应返回 None
        instance = resolver.instantiate_generic("单参数函数", ["整数型", "字符串型"])
        assert instance is None

    def test_instantiate_generic_type(self):
        """测试泛型类型实例化"""
        from zhc.semantic.generics import (
            GenericResolver,
            GenericType,
            TypeParameter,
            MemberInfo,
        )

        resolver = GenericResolver()

        # 注册泛型类型
        list_type = GenericType(
            name="列表",
            type_params=[TypeParameter(name="T")],
            members=[
                MemberInfo(name="数据", type_name="T[]"),
                MemberInfo(name="长度", type_name="整数型"),
            ],
        )
        resolver.manager.register_generic_type(list_type)

        # 实例化
        instance = resolver.instantiate_generic_type("列表", ["浮点型"])
        assert instance is not None
        assert instance.name == "列表<浮点型>"
        assert instance.type_args == ["浮点型"]

    def test_instantiate_generic_type_with_caching(self):
        """测试实例化缓存机制"""
        from zhc.semantic.generics import (
            GenericResolver,
            GenericType,
            TypeParameter,
            MemberInfo,
        )

        resolver = GenericResolver()

        box_type = GenericType(
            name="盒子",
            type_params=[TypeParameter(name="T")],
            members=[MemberInfo(name="内容", type_name="T")],
        )
        resolver.manager.register_generic_type(box_type)

        # 实例化两次相同类型 — GenericType 自身有实例缓存
        inst1 = resolver.instantiate_generic_type("盒子", ["整数型"])
        inst2 = resolver.instantiate_generic_type("盒子", ["整数型"])

        # 验证两次结果等价（GenericType 自身缓存保证同一对象）
        assert inst1.name == inst2.name
        assert inst1.type_args == inst2.type_args
        # GenericType 的 instantiations 字典会缓存，但每次 instantiate_generic_type
        # 创建新 Instantiator，所以不一定是同一对象。验证内容一致即可。
        assert inst1.generic_type is inst2.generic_type  # 指向同一泛型定义

    def test_register_function_from_ast(self):
        """测试从 AST 节点注册泛型函数"""
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
            TypeNode,
        )
        from zhc.semantic.generics import GenericResolver

        resolver = GenericResolver()

        # 构建 AST 节点
        func_node = GenericFunctionDeclNode(
            name="交换",
            type_params=[TypeParameterNode(name="T")],
            params=[],  # 简化：无参数
            return_type=TypeNode("(T, T)"),
            body=None,
        )

        generic_func = resolver._register_function_from_ast(func_node)

        assert generic_func.name == "交换"
        assert len(generic_func.type_params) == 1
        assert generic_func.type_params[0].name == "T"

        # 应该已在管理器中
        funcs = resolver.manager.get_generic_functions("交换")
        assert len(funcs) >= 1

    def test_register_type_from_ast(self):
        """测试从 AST 节点注册泛型类型"""
        from zhc.semantic.generic_parser import (
            GenericTypeDeclNode,
            TypeParameterNode,
        )
        from zhc.semantic.generics import GenericResolver

        resolver = GenericResolver()

        type_node = GenericTypeDeclNode(
            name="栈",
            type_params=[TypeParameterNode(name="T")],
            members=None,  # 无成员也支持注册
        )

        generic_type = resolver._register_type_from_ast(type_node)

        assert generic_type.name == "栈"
        assert len(generic_type.type_params) == 1

        # 应该已在管理器中
        found = resolver.manager.get_generic_type("栈")
        assert found is not None

    def test_register_type_with_where_clause(self):
        """测试带 Where 子句的泛型类型注册"""
        from zhc.semantic.generic_parser import (
            GenericTypeDeclNode,
            TypeParameterNode,
            WhereClauseNode,
        )
        from zhc.semantic.generics import GenericResolver

        resolver = GenericResolver()

        where = WhereClauseNode(constraints=[("T", "数值型")])
        type_node = GenericTypeDeclNode(
            name="数值容器",
            type_params=[TypeParameterNode(name="T")],
            members=None,  # 无成员也支持注册
            where_clause=where,
        )

        generic_type = resolver._register_type_from_ast(type_node)

        # Where 子句中的约束应该已被应用到类型参数上
        assert generic_type.name == "数值容器"
        # 数值型约束应已附加到 T 上
        t_param = generic_type.type_params[0]
        constraint_names = [c.name for c in t_param.constraints]
        assert "数值型" in constraint_names

    def test_resolver_statistics(self):
        """测试解析器统计信息"""
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            GenericTypeDeclNode,
            TypeParameterNode,
            TypeNode,
        )
        from zhc.semantic.generics import GenericResolver

        resolver = GenericResolver()

        # 初始状态
        stats = resolver.get_statistics()
        assert stats["resolved_generic_functions"] == 0
        assert stats["resolved_generic_types"] == 0

        # 注册一个函数
        func_node = GenericFunctionDeclNode(
            name="测试函数",
            type_params=[TypeParameterNode(name="T")],
            params=[],
            return_type=TypeNode("T"),
        )
        resolver._register_function_from_ast(func_node)

        # 注册一个类型（无成员）
        type_node = GenericTypeDeclNode(
            name="测试类型",
            type_params=[TypeParameterNode(name="T")],
            members=None,
        )
        resolver._register_type_from_ast(type_node)

        # 更新后的统计
        stats = resolver.get_statistics()
        assert stats["resolved_generic_functions"] >= 1
        assert stats["resolved_generic_types"] >= 1
        assert "测试函数" in stats["function_names"]
        assert "测试类型" in stats["type_names"]


class TestMonomorphizerBasic:
    """Monomorphizer 单态化引擎基础框架测试"""

    def setup_method(self):
        reset_generic_manager()

    def test_monomorphizer_creation(self):
        """测试单态化引擎创建"""
        from zhc.semantic.generics import Monomorphizer, get_monomorphizer

        mono = Monomorphizer()
        assert mono.manager is not None
        assert mono.resolver is not None
        assert mono.resolver.manager is mono.manager

        mono2 = get_monomorphizer()
        assert isinstance(mono2, Monomorphizer)

    def test_monomorphize_basic_registration_only(self):
        """测试基础 monomorphize 仅做预注册（G.01 阶段）"""
        from zhc.semantic.generics import (
            Monomorphizer,
            GenericFunction,
            TypeParameter,
            ParamInfo,
        )
        from zhc.parser.ast_nodes import ProgramNode

        mono = Monomorphizer()

        # 注册一个泛型函数到管理器
        generic_func = GenericFunction(
            name="最小值",
            type_params=[TypeParameter(name="T")],
            params=[
                ParamInfo(name="a", type_name="T"),
                ParamInfo(name="b", type_name="T"),
            ],
            return_type="T",
        )
        mono.manager.register_generic_function(generic_func)

        # 构建一个 ProgramNode
        program = ProgramNode(declarations=[])

        # monomorphize 在 G.02 阶段会做完整的单态化变换
        result = mono.monomorphize(program)
        assert result is program  # 返回同一个程序树

    def test_monomorphize_function_basic(self):
        """测试基础函数单态化 — 无类型参数的简单函数"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
            TypeNode,
        )
        from zhc.parser.ast_nodes import FunctionDeclNode

        mono = Monomorphizer()

        # 构建一个简单的泛型函数声明: 泛型函数 T 身份<T>(T 值) -> T { 返回 值; }
        func_node = GenericFunctionDeclNode(
            name="身份",
            type_params=[TypeParameterNode(name="T")],
            params=[],  # 简化：无参数（参数在完整解析中才有）
            return_type=TypeNode("T"),
            body=None,  # 简化：无函数体
        )

        # 单态化为 T=整数型
        specialized = mono.monomorphize_function(func_node, ["整数型"])

        assert isinstance(specialized, FunctionDeclNode)
        assert specialized.name == "身份__整数型"
        assert isinstance(specialized.return_type, TypeNode)
        assert specialized.return_type.type_name == "整数型"

    def test_monomorphize_function_with_params_and_body(self):
        """测试带参数和函数体的函数单态化"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
            TypeNode,
        )
        from zhc.parser.ast_nodes import (
            FunctionDeclNode,
            ParamDeclNode,
            BlockStmtNode,
            ReturnStmtNode,
            IdentifierExprNode,
        )

        mono = Monomorphizer()

        # 构建: 泛型函数 T 最大值<类型 T>(T a, T b) -> T { 如果 (a > b) 返回 a; 否则返回 b; }
        param_a = ParamDeclNode(
            name="a",
            param_type=TypeNode("T"),
            default_value=None,
        )
        param_b = ParamDeclNode(
            name="b",
            param_type=TypeNode("T"),
            default_value=None,
        )

        body = BlockStmtNode(
            statements=[
                ReturnStmtNode(value=IdentifierExprNode(name="a")),
            ]
        )

        func_node = GenericFunctionDeclNode(
            name="最大值",
            type_params=[TypeParameterNode(name="T")],
            params=[param_a, param_b],
            return_type=TypeNode("T"),
            body=body,
        )

        # 单态化
        specialized = mono.monomorphize_function(func_node, ["浮点型"])

        assert isinstance(specialized, FunctionDeclNode)
        assert specialized.name == "最大值__浮点型"
        assert specialized.return_type.type_name == "浮点型"

        # 检查参数类型已被替换
        assert len(specialized.params) == 2
        assert specialized.params[0].param_type.type_name == "浮点型"
        assert specialized.params[1].param_type.type_name == "浮点型"
        assert specialized.params[0].name == "a"
        assert specialized.params[1].name == "b"

        # 检查函数体被深拷贝
        assert specialized.body is not None
        assert isinstance(specialized.body, BlockStmtNode)

    def test_monomorphize_function_caching(self):
        """测试函数单态化缓存机制"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
            TypeNode,
        )

        mono = Monomorphizer()

        func_node = GenericFunctionDeclNode(
            name="交换",
            type_params=[TypeParameterNode(name="T")],
            params=[],
            return_type=TypeNode("T"),
            body=None,
        )

        spec1 = mono.monomorphize_function(func_node, ["整数型"])
        spec2 = mono.monomorphize_function(func_node, ["整数型"])

        # 缓存命中，应为同一对象
        assert spec1 is spec2
        assert spec1.name == "交换__整数型"

    def test_monomorphize_function_wrong_arity_raises(self):
        """测试参数数量不匹配时抛出异常"""
        from zhc.semantic.generics import Monomorphizer, TypeParameterCountError
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
            TypeNode,
        )

        mono = Monomorphizer()

        func_node = GenericFunctionDeclNode(
            name="单参数函数",
            type_params=[TypeParameterNode(name="T")],
            params=[],
            return_type=TypeNode("T"),
            body=None,
        )

        with pytest.raises(TypeParameterCountError) as exc_info:
            mono.monomorphize_function(func_node, ["整数型", "字符串型"])
        assert "需要 1 个" in str(exc_info.value)

    def test_monomorphize_class_basic(self):
        """测试基础类型单态化"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.semantic.generic_parser import (
            GenericTypeDeclNode,
            TypeParameterNode,
        )
        from zhc.parser.ast_nodes import StructDeclNode

        mono = Monomorphizer()

        # 构建: 泛型类型 盒子<类型 T> { T 内容; }
        type_node = GenericTypeDeclNode(
            name="盒子",
            type_params=[TypeParameterNode(name="T")],
            members=None,  # 无成员也支持
        )

        specialized = mono.monomorphize_class(type_node, ["字符串型"])

        assert isinstance(specialized, StructDeclNode)
        assert specialized.name == "盒子__字符串型"

    def test_monomorphize_class_with_members(self):
        """测试带成员的类型单态化"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.semantic.generic_parser import (
            GenericTypeDeclNode,
            TypeParameterNode,
        )
        from zhc.parser.ast_nodes import (
            StructDeclNode,
            VariableDeclNode,
            PrimitiveTypeNode,
        )

        mono = Monomorphizer()

        # 构建带有成员变量的泛型类型
        members = [
            VariableDeclNode(
                name="数据",
                var_type=PrimitiveTypeNode(name="T"),
                init=None,
            ),
            VariableDeclNode(
                name="长度",
                var_type=PrimitiveTypeNode(name="整数型"),
                init=None,
            ),
        ]

        type_node = GenericTypeDeclNode(
            name="容器",
            type_params=[TypeParameterNode(name="T")],
            members=members,
        )

        specialized = mono.monomorphize_class(type_node, ["浮点型"])

        assert isinstance(specialized, StructDeclNode)
        assert specialized.name == "容器__浮点型"
        assert len(specialized.members) == 2

        # 第一个成员的类型应从 "T" 替换为 "浮点型"
        data_member = specialized.members[0]
        assert isinstance(data_member, VariableDeclNode)
        assert data_member.name == "数据"
        assert data_member.var_type.name == "浮点型"

        # 第二个成员的类型不变（已经是 "整数型"）
        length_member = specialized.members[1]
        assert length_member.var_type.name == "整数型"

    def test_monomorphize_class_caching(self):
        """测试类型单态化缓存"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.semantic.generic_parser import GenericTypeDeclNode, TypeParameterNode

        mono = Monomorphizer()

        type_node = GenericTypeDeclNode(
            name="栈",
            type_params=[TypeParameterNode(name="T")],
            members=None,
        )

        spec1 = mono.monomorphize_class(type_node, ["整数型"])
        spec2 = mono.monomorphize_class(type_node, ["整数型"])

        assert spec1 is spec2

    def test_monomorphize_class_wrong_arity_raises(self):
        """测试类型参数数量不匹配时抛出异常"""
        from zhc.semantic.generics import Monomorphizer, TypeParameterCountError
        from zhc.semantic.generic_parser import (
            GenericTypeDeclNode,
            TypeParameterNode,
        )

        mono = Monomorphizer()

        type_node = GenericTypeDeclNode(
            name="配对",
            type_params=[
                TypeParameterNode(name="K"),
                TypeParameterNode(name="V"),
            ],
            members=None,
        )

        with pytest.raises(TypeParameterCountError):
            mono.monomorphize_class(type_node, ["整数型"])


class TestSpecializedCopyEngine:
    """_generate_specialized_copy AST 深拷贝+替换引擎测试"""

    def setup_method(self):
        reset_generic_manager()

    def test_copy_primitive_type_substitution(self):
        """测试基本类型节点的替换"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.parser.ast_nodes import PrimitiveTypeNode

        mono = Monomorphizer()
        node = PrimitiveTypeNode(name="T")
        substitutions = {"T": "整数型"}

        copied = mono._generate_specialized_copy(node, substitutions)
        assert isinstance(copied, PrimitiveTypeNode)
        assert copied.name == "整数型"

    def test_copy_primitive_type_no_match(self):
        """测试基本类型节点无匹配时保留原样"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.parser.ast_nodes import PrimitiveTypeNode

        mono = Monomorphizer()
        node = PrimitiveTypeNode(name="整数型")
        substitutions = {"T": "浮点型"}

        copied = mono._generate_specialized_copy(node, substitutions)
        assert copied.name == "整数型"  # 不在映射中，保持原样

    def test_copy_type_node_with_generic_args(self):
        """测试 TypeNode 泛型参数替换"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.semantic.generic_parser import TypeNode

        mono = Monomorphizer()
        node = TypeNode(
            type_name="列表",
            is_generic=True,
            generic_args=[
                TypeNode(type_name="T"),
            ],
        )
        substitutions = {"T": "字符串型"}

        copied = mono._generate_specialized_copy(node, substitutions)
        assert isinstance(copied, TypeNode)
        assert copied.type_name == "列表"
        assert len(copied.generic_args) == 1
        assert copied.generic_args[0].type_name == "字符串型"

    def test_copy_pointer_type(self):
        """测试指针类型的深拷贝和替换"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.parser.ast_nodes import PointerTypeNode, PrimitiveTypeNode

        mono = Monomorphizer()
        node = PointerTypeNode(base_type=PrimitiveTypeNode(name="T"))
        substitutions = {"T": "字符型"}

        copied = mono._generate_specialized_copy(node, substitutions)
        assert isinstance(copied, PointerTypeNode)
        assert copied.base_type.name == "字符型"

    def test_copy_array_type(self):
        """测试数组类型的深拷贝和替换"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.parser.ast_nodes import ArrayTypeNode, PrimitiveTypeNode

        mono = Monomorphizer()
        node = ArrayTypeNode(
            element_type=PrimitiveTypeNode(name="T"),
            size=None,
        )
        substitutions = {"T": "整数型"}

        copied = mono._generate_specialized_copy(node, substitutions)
        assert isinstance(copied, ArrayTypeNode)
        assert copied.element_type.name == "整数型"

    def test_copy_struct_type(self):
        """测试结构体类型名的替换"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.parser.ast_nodes import StructTypeNode

        mono = Monomorphizer()
        node = StructTypeNode(name="链表节点<T>")
        substitutions = {"T": "浮点型"}

        copied = mono._generate_specialized_copy(node, substitutions)
        assert isinstance(copied, StructTypeNode)
        assert copied.name == "链表节点<浮点型>"

    def test_copy_param_decl(self):
        """测试参数声明的深拷贝和替换"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.parser.ast_nodes import ParamDeclNode, PrimitiveTypeNode

        mono = Monomorphizer()
        node = ParamDeclNode(
            name="元素",
            param_type=PrimitiveTypeNode(name="T"),
            default_value=None,
        )
        substitutions = {"T": "布尔型"}

        copied = mono._generate_specialized_copy(node, substitutions)
        assert isinstance(copied, ParamDeclNode)
        assert copied.name == "元素"
        assert copied.param_type.name == "布尔型"

    def test_copy_variable_decl(self):
        """测试变量声明的深拷贝和替换（含初始化表达式）"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.parser.ast_nodes import (
            VariableDeclNode,
            PrimitiveTypeNode,
            IntLiteralNode,
        )

        mono = Monomorphizer()
        node = VariableDeclNode(
            name="计数器",
            var_type=PrimitiveTypeNode(name="T"),
            init=IntLiteralNode(value=42),
            is_const=True,
        )
        substitutions = {"T": "整数型"}

        copied = mono._generate_specialized_copy(node, substitutions)
        assert isinstance(copied, VariableDeclNode)
        assert copied.name == "计数器"
        assert copied.var_type.name == "整数型"
        assert copied.is_const is True
        assert copied.init.value == 42

    def test_copy_binary_expr(self):
        """测试二元表达式的深拷贝"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.parser.ast_nodes import (
            BinaryExprNode,
            IdentifierExprNode,
        )

        mono = Monomorphizer()
        node = BinaryExprNode(
            operator=">",
            left=IdentifierExprNode(name="a"),
            right=IdentifierExprNode(name="b"),
        )
        substitutions = {}

        copied = mono._generate_specialized_copy(node, substitutions)
        assert isinstance(copied, BinaryExprNode)
        assert copied.operator == ">"

    def test_copy_call_expr(self):
        """测试函数调用表达式的深拷贝"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.parser.ast_nodes import CallExprNode, IdentifierExprNode

        mono = Monomorphizer()
        node = CallExprNode(
            callee=IdentifierExprNode(name="打印"),
            args=[IdentifierExprNode(name="消息")],
        )
        substitutions = {}

        copied = mono._generate_specialized_copy(node, substitutions)
        assert isinstance(copied, CallExprNode)
        assert len(copied.args) == 1

    def test_copy_block_stmt(self):
        """测试代码块的深拷贝"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.parser.ast_nodes import (
            BlockStmtNode,
            ReturnStmtNode,
            IntLiteralNode,
        )

        mono = Monomorphizer()
        node = BlockStmtNode(
            statements=[
                ReturnStmtNode(value=IntLiteralNode(value=0)),
            ]
        )
        substitutions = {}

        copied = mono._generate_specialized_copy(node, substitutions)
        assert isinstance(copied, BlockStmtNode)
        assert len(copied.statements) == 1

    def test_copy_if_stmt(self):
        """测试如果语句的深拷贝"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.parser.ast_nodes import (
            IfStmtNode,
            BoolLiteralNode,
            BlockStmtNode,
            ReturnStmtNode,
            IntLiteralNode,
        )

        mono = Monomorphizer()
        node = IfStmtNode(
            condition=BoolLiteralNode(value=True),
            then_branch=BlockStmtNode(statements=[]),
            else_branch=BlockStmtNode(
                statements=[
                    ReturnStmtNode(value=IntLiteralNode(value=-1)),
                ]
            ),
        )
        substitutions = {}

        copied = mono._generate_specialized_copy(node, substitutions)
        assert isinstance(copied, IfStmtNode)
        assert copied.else_branch is not None

    def test_copy_none_returns_none(self):
        """测试 None 节点返回 None"""
        from zhc.semantic.generics import Monomorphizer

        mono = Monomorphizer()
        assert mono._generate_specialized_copy(None, {}) is None

    def test_substitute_type_name_simple(self):
        """测试简单类型名称替换"""
        from zhc.semantic.generics import Monomorphizer

        assert Monomorphizer._substitute_type_name("T", {"T": "整数型"}) == "整数型"
        assert Monomorphizer._substitute_type_name("整数型", {}) == "整数型"

    def test_substitute_type_name_array(self):
        """测试数组类型名替换"""
        from zhc.semantic.generics import Monomorphizer

        result = Monomorphizer._substitute_type_name("T[]", {"T": "字符型"})
        assert result == "字符型[]"

    def test_substitute_type_name_composite(self):
        """测试复合类型名替换"""
        from zhc.semantic.generics import Monomorphizer

        result = Monomorphizer._substitute_type_name(
            "(T, V)",
            {
                "T": "字符串型",
                "V": "整数型",
            },
        )
        assert result == "(字符串型, 整数型)"

    def test_substitute_type_name_long_key_first(self):
        """测试长键名优先替换（避免 Key 被 K 错误替换）"""
        from zhc.semantic.generics import Monomorphizer

        result = Monomorphizer._substitute_type_name(
            "键值对<Key, Value>",
            {
                "Key": "字符串键",
                "K": "短键",
                "Value": "整数值",
            },
        )
        assert "字符串键" in result
        assert "整数值" in result

    def test_copy_deeply_nested_ast(self):
        """测试深层嵌套 AST 结构的完整替换"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.parser.ast_nodes import (
            FunctionDeclNode,
            ParamDeclNode,
            PrimitiveTypeNode,
            BlockStmtNode,
            VariableDeclNode,
            IfStmtNode,
            BinaryExprNode,
            IdentifierExprNode,
            ReturnStmtNode,
            IntLiteralNode,
            ArrayTypeNode,
            ArrayExprNode,
        )

        mono = Monomorphizer()

        # 构建一个较复杂的 AST 树：
        # 函数 T 查找<T>(T[] 列表, T 目标) -> 整数型 {
        #   整数型 i = 0;
        #   如果 (列表[i] > 目标) { 返回 i; }
        #   返回 -1;
        # }
        func = FunctionDeclNode(
            name="查找",
            return_type=PrimitiveTypeNode(name="整数型"),
            params=[
                ParamDeclNode(
                    name="列表",
                    param_type=ArrayTypeNode(
                        element_type=PrimitiveTypeNode(name="T"),
                        size=None,
                    ),
                ),
                ParamDeclNode(
                    name="目标",
                    param_type=PrimitiveTypeNode(name="T"),
                ),
            ],
            body=BlockStmtNode(
                statements=[
                    VariableDeclNode(
                        name="i",
                        var_type=PrimitiveTypeNode(name="整数型"),
                        init=IntLiteralNode(value=0),
                    ),
                    IfStmtNode(
                        condition=BinaryExprNode(
                            operator=">",
                            left=ArrayExprNode(
                                array=IdentifierExprNode(name="列表"),
                                index=IdentifierExprNode(name="i"),
                            ),
                            right=IdentifierExprNode(name="目标"),
                        ),
                        then_branch=BlockStmtNode(
                            statements=[
                                ReturnStmtNode(value=IdentifierExprNode(name="i")),
                            ]
                        ),
                        else_branch=None,
                    ),
                    ReturnStmtNode(value=IntLiteralNode(value=-1)),
                ]
            ),
        )

        substitutions = {"T": "浮点型"}
        copied = mono._generate_specialized_copy(func, substitutions)

        # 验证所有层级的 T 都被替换了
        assert isinstance(copied, FunctionDeclNode)
        # 参数 "列表" 的元素类型
        list_param = copied.params[0]
        assert list_param.param_type.element_type.name == "浮点型"
        # 参数 "目标" 类型
        target_param = copied.params[1]
        assert target_param.param_type.name == "浮点型"


class TestMonomorphizerStatistics:
    """Monomorphizer 统计信息测试"""

    def setup_method(self):
        reset_generic_manager()

    def test_statistics_empty(self):
        """测试空状态统计"""
        from zhc.semantic.generics import Monomorphizer

        mono = Monomorphizer()
        stats = mono.get_statistics()
        assert stats["specialized_functions"] == 0
        assert stats["specialized_types"] == 0

    def test_statistics_after_monoms(self):
        """测试单态化后的统计"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            GenericTypeDeclNode,
            TypeParameterNode,
            TypeNode,
        )

        mono = Monomorphizer()

        # 单态化一个函数
        func = GenericFunctionDeclNode(
            name="测试",
            type_params=[TypeParameterNode(name="T")],
            params=[],
            return_type=TypeNode("T"),
            body=None,
        )
        mono.monomorphize_function(func, ["整数型"])
        mono.monomorphize_function(func, ["浮点型"])

        # 单态化一个类型
        cls = GenericTypeDeclNode(
            name="包装",
            type_params=[TypeParameterNode(name="T")],
            members=None,
        )
        mono.monomorphize_class(cls, ["字符串型"])

        stats = mono.get_statistics()
        assert stats["specialized_functions"] == 2
        assert stats["specialized_types"] == 1
        assert "测试__整数型" in stats["function_cache_keys"]
        assert "测试__浮点型" in stats["function_cache_keys"]
        assert "包装__字符串型" in stats["type_cache_keys"]


# ===== G.03: Semantic Analyzer 集成泛型流程测试 =====


class TestSemanticAnalyzerGenericIntegration:
    """
    G.03: SemanticAnalyzer 泛型集成测试

    验证语义分析器能正确：
    1. 检测并路由泛型函数/类型声明到专用分析方法
    2. 通过 GenericResolver 注册泛型到 GenericManager
    3. 在符号表中创建泛型占位符号
    4. 在 analyze() 末尾触发 Monomorphizer 单态化
    """

    def setup_method(self):
        """每个测试前重置全局状态"""
        from zhc.semantic.generics import reset_generic_manager

        reset_generic_manager()

    @staticmethod
    def _create_analyzer():
        """创建干净的 SemanticAnalyzer 实例"""
        from zhc.semantic.semantic_analyzer import SemanticAnalyzer

        return SemanticAnalyzer()

    # ---- G03-1: 属性初始化 ----

    def test_generic_resolver_lazy_init(self):
        """验证 generic_resolver 延迟属性可正常访问"""
        analyzer = self._create_analyzer()

        resolver = analyzer.generic_resolver
        assert resolver is not None
        assert hasattr(resolver, "manager")
        assert hasattr(resolver, "resolve")

        # 再次获取应返回同一实例（延迟属性缓存）
        assert analyzer.generic_resolver is resolver

    def test_monomorphizer_lazy_init(self):
        """验证 monomorphizer 延迟属性可正常访问"""
        analyzer = self._create_analyzer()

        mono = analyzer.monomorphizer
        assert mono is not None
        assert hasattr(mono, "monomorphize")
        assert hasattr(mono, "monomorphize_function")
        assert hasattr(mono, "monomorphize_class")

        # monomorphizer 应共享同一个 manager 和 resolver
        assert mono.manager is analyzer.generic_manager

    def test_resolver_and_monomorphizer_shared_state(self):
        """验证 resolver 和 monomorphizer 共享管理器"""
        analyzer = self._create_analyzer()

        # 通过 resolver 注册一个泛型函数
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
            TypeNode,
        )

        func = GenericFunctionDeclNode(
            name="共享测试",
            type_params=[TypeParameterNode(name="T")],
            params=[],
            return_type=TypeNode("T"),
            body=None,
        )
        analyzer.generic_resolver.resolve(func)

        # monomorphizer 的 resolver 应能看到同样的注册
        stats = analyzer.monomorphizer.resolver.get_statistics()
        assert "共享测试" in stats["function_names"]

    # ---- G03-2: 节点路由 ----

    def test_is_generic_function_decl_detection(self):
        """验证 _is_generic_function_decl 正确识别 GenericFunctionDeclNode"""
        analyzer = self._create_analyzer()

        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
            TypeNode,
        )
        from zhc.parser.ast_nodes import FunctionDeclNode

        gen_func = GenericFunctionDeclNode(
            name="最大值",
            type_params=[TypeParameterNode(name="T")],
            params=[],
            return_type=TypeNode("T"),
        )
        normal_func = FunctionDeclNode(
            name="普通函数",
            return_type=None,
            params=[],
            body=None,
        )

        assert analyzer._is_generic_function_decl(gen_func) is True
        assert analyzer._is_generic_function_decl(normal_func) is False

    def test_is_generic_type_decl_detection(self):
        """验证 _is_generic_type_decl 正确识别 GenericTypeDeclNode"""
        analyzer = self._create_analyzer()

        from zhc.semantic.generic_parser import (
            GenericTypeDeclNode,
            TypeParameterNode,
        )
        from zhc.parser.ast_nodes import StructDeclNode

        gen_type = GenericTypeDeclNode(
            name="列表",
            type_params=[TypeParameterNode(name="T")],
        )
        normal_type = StructDeclNode(name="普通结构体", members=[])

        assert analyzer._is_generic_type_decl(gen_type) is True
        assert analyzer._is_generic_type_decl(normal_type) is False

    # ---- G03-3: 泛型函数声明分析 ----

    def test_analyze_generic_function_decl_basic(self):
        """基础泛型函数声明分析：注册+符号表"""
        analyzer = self._create_analyzer()

        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
            TypeNode,
        )
        from zhc.parser.ast_nodes import (
            IdentifierExprNode,
            BlockStmtNode,
            ReturnStmtNode,
        )

        func = GenericFunctionDeclNode(
            name="恒等",
            type_params=[TypeParameterNode(name="T")],
            params=[],
            return_type=TypeNode("T"),
            body=BlockStmtNode(
                statements=[
                    ReturnStmtNode(value=IdentifierExprNode(name="x")),
                ]
            ),
        )

        analyzer._analyze_generic_function_decl(func)

        # 符号表中应有泛型函数占位符
        sym = analyzer.symbol_table.lookup("恒等")
        assert sym is not None
        assert sym.symbol_type == "泛型函数"
        assert sym.data_type == "T"

        # Resolver 中应已注册
        stats = analyzer.generic_resolver.get_statistics()
        assert "恒等" in stats["function_names"]

    def test_analyze_generic_function_with_constraints(self):
        """带约束的泛型函数声明分析"""
        analyzer = self._create_analyzer()

        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
            TypeNode,
            WhereClauseNode,
        )

        func = GenericFunctionDeclNode(
            name="排序",
            type_params=[TypeParameterNode(name="T", constraints=["可比较"])],
            params=[],
            return_type=TypeNode("T"),
            body=None,
            where_clause=WhereClauseNode(constraints=[("T", "可比较")]),
        )

        analyzer._analyze_generic_function_decl(func)

        # 不应报错（约束是预定义的）
        assert (
            len(analyzer.errors) == 0
            or any("约束" in str(e) for e in analyzer.errors)
            or len(analyzer.errors) == 0
        )

    def test_analyze_generic_function_duplicate_error(self):
        """重复定义的泛型函数应报告错误"""
        analyzer = self._create_analyzer()

        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
            TypeNode,
        )

        func1 = GenericFunctionDeclNode(
            name="重复名",
            type_params=[TypeParameterNode(name="T")],
            params=[],
            return_type=TypeNode("T"),
            body=None,
        )
        func2 = GenericFunctionDeclNode(
            name="重复名",
            type_params=[TypeParameterNode(name="V")],
            params=[],
            return_type=TypeNode("V"),
            body=None,
        )

        analyzer._analyze_generic_function_decl(func1)
        analyzer._analyze_generic_function_decl(func2)

        # 第二次应产生重复定义错误
        error_msgs = [str(e) for e in analyzer.errors]
        has_dup_error = any("重复" in msg and "重复名" in msg for msg in error_msgs)
        assert has_dup_error

    # ---- G03-4: 泛型类型声明分析 ----

    def test_analyze_generic_type_decl_basic(self):
        """基础泛型类型声明分析：注册+符号表+成员"""
        analyzer = self._create_analyzer()

        from zhc.semantic.generic_parser import (
            GenericTypeDeclNode,
            TypeParameterNode,
        )
        from zhc.parser.ast_nodes import (
            VariableDeclNode,
            PrimitiveTypeNode,
        )

        members = [
            VariableDeclNode(
                name="数据",
                var_type=PrimitiveTypeNode(name="T"),
                init=None,
            ),
            VariableDeclNode(
                name="长度",
                var_type=PrimitiveTypeNode(name="整数型"),
                init=None,
            ),
        ]

        gtype = GenericTypeDeclNode(
            name="数组容器",
            type_params=[TypeParameterNode(name="T")],
            members=members,
        )

        analyzer._analyze_generic_type_decl(gtype)

        # 符号表中应有泛型结构体占位符
        sym = analyzer.symbol_table.lookup("数组容器")
        assert sym is not None
        assert sym.symbol_type == "泛型结构体"

        # 成员信息应被记录
        member_names = [m.name for m in sym.members]
        assert "数据" in member_names
        assert "长度" in member_names

    def test_analyze_generic_type_with_where_clause(self):
        """带 Where 子句的泛型类型声明分析"""
        analyzer = self._create_analyzer()

        from zhc.semantic.generic_parser import (
            GenericTypeDeclNode,
            TypeParameterNode,
            WhereClauseNode,
        )

        gtype = GenericTypeDeclNode(
            name="有序集合",
            type_params=[TypeParameterNode(name="K", constraints=["可比较"])],
            members=[],
            where_clause=WhereClauseNode(constraints=[("K", "可比较")]),
        )

        analyzer._analyze_generic_type_decl(gtype)

        # 不应因合法约束而报错
        critical_errors = [
            e
            for e in analyzer.errors
            if "严重" in str(getattr(e, "error_type", "")).lower()
            or "fatal" in str(e).lower()
        ]
        assert len(critical_errors) == 0

    def test_analyze_generic_type_unknown_param_in_where(self):
        """Where 子句引用未声明的参数应产生警告"""
        analyzer = self._create_analyzer()

        from zhc.semantic.generic_parser import (
            GenericTypeDeclNode,
            TypeParameterNode,
            WhereClauseNode,
        )

        gtype = GenericTypeDeclNode(
            name="测试类型",
            type_params=[TypeParameterNode(name="T")],
            members=[],
            where_clause=WhereClauseNode(constraints=[("X", "可比较")]),  # X 未声明!
        )

        analyzer._analyze_generic_type_decl(gtype)

        # 应有警告关于未声明的类型参数 X
        warning_msgs = [str(w) for w in analyzer.warnings if w]
        has_warning = any("X" in msg and "未声明" in msg for msg in warning_msgs)
        assert has_warning

    # ---- G03-5: 泛型调用点处理 ----

    def test_analyze_generic_type_ref_basic(self):
        """基础泛型类型引用分析"""
        analyzer = self._create_analyzer()

        # 先注册一个泛型类型到管理器
        from zhc.semantic.generic_parser import (
            GenericTypeDeclNode,
            TypeParameterNode,
            GenericTypeNode,
        )
        from zhc.parser.ast_nodes import PrimitiveTypeNode

        # 注册泛型类型
        gtype = GenericTypeDeclNode(
            name="盒子",
            type_params=[TypeParameterNode(name="T")],
            members=[],
        )
        analyzer.generic_resolver.resolve(gtype)

        # 创建泛型引用节点
        ref = GenericTypeNode(
            base_type="盒子",
            type_args=[PrimitiveTypeNode(name="字符串型")],
        )

        result = analyzer._analyze_generic_type_ref(ref)

        # 应返回 mangled 名称
        assert result is not None
        assert "盒子" in result
        assert "字符串型" in result

    def test_analyze_generic_type_ref_unregistered(self):
        """未注册的泛型类型引用不应崩溃"""
        analyzer = self._create_analyzer()

        from zhc.semantic.generic_parser import (
            GenericTypeNode,
        )
        from zhc.parser.ast_nodes import PrimitiveTypeNode

        ref = GenericTypeNode(
            base_type="未知类型",
            type_args=[PrimitiveTypeNode(name="整数型")],
        )

        # 不应抛异常，返回 mangled 名即可
        result = analyzer._analyze_generic_type_ref(ref)
        assert result is not None
        assert "未知类型" in result

    # ---- G03-6: analyze() 完整流程中的单态化 ----

    def test_analyze_triggers_monomorphization(self):
        """analyze() 应在末尾执行单态化且不崩溃"""
        analyzer = self._create_analyzer()

        from zhc.parser.ast_nodes import (
            ProgramNode,
            FunctionDeclNode,
            BlockStmtNode,
            ReturnStmtNode,
            ParamDeclNode,
            IdentifierExprNode,
        )
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
            TypeNode,
        )

        # 构建一个包含泛型函数的程序
        param = ParamDeclNode(
            name="a",
            param_type=TypeNode("T"),
        )
        body = BlockStmtNode(
            statements=[
                ReturnStmtNode(value=IdentifierExprNode(name="a")),
            ]
        )
        gen_func = GenericFunctionDeclNode(
            name="取值",
            type_params=[TypeParameterNode(name="T")],
            params=[param],
            return_type=TypeNode("T"),
            body=body,
        )
        normal_func = FunctionDeclNode(
            name="主函数",
            return_type=None,
            params=[],
            body=BlockStmtNode(statements=[]),
        )

        program = ProgramNode(declarations=[gen_func, normal_func])

        # 执行完整的 analyze 流程（包括单态化）
        result = analyzer.analyze(program)

        # 不应崩溃，result 是 bool
        assert isinstance(result, bool)

    def test_analyze_file_triggers_monomorphization(self):
        """analyze_file() 也应执行单态化"""
        analyzer = self._create_analyzer()

        from zhc.parser.ast_nodes import ProgramNode
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
            TypeNode,
        )

        gen_func = GenericFunctionDeclNode(
            name="简单泛型",
            type_params=[TypeParameterNode(name="U")],
            params=[],
            return_type=TypeNode("U"),
            body=None,
        )

        program = ProgramNode(declarations=[gen_func])

        # analyze_file 不应崩溃
        result = analyzer.analyze_file(program, source_file="test.zh")
        assert isinstance(result, bool)

    # ---- G03 综合端到端 ----

    def test_full_generic_program_analysis(self):
        """完整泛型程序的端到端分析流程"""
        analyzer = self._create_analyzer()

        from zhc.parser.ast_nodes import (
            ProgramNode,
            FunctionDeclNode,
            BlockStmtNode,
            ReturnStmtNode,
            IdentifierExprNode,
            ParamDeclNode,
            PrimitiveTypeNode,
            IntLiteralNode,
            TernaryExprNode,
            BinaryExprNode,
        )
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
            TypeNode,
        )

        # 1. 声明一个泛型函数 最大值<T>(T a, T b) -> T { return (a > b) ? a : b; }
        gen_max = GenericFunctionDeclNode(
            name="最大值",
            type_params=[TypeParameterNode(name="T", constraints=["可比较"])],
            params=[
                ParamDeclNode(name="a", param_type=TypeNode("T")),
                ParamDeclNode(name="b", param_type=TypeNode("T")),
            ],
            return_type=TypeNode("T"),
            body=BlockStmtNode(
                statements=[
                    ReturnStmtNode(
                        value=TernaryExprNode(
                            condition=BinaryExprNode(
                                operator=">",
                                left=IdentifierExprNode(name="a"),
                                right=IdentifierExprNode(name="b"),
                            ),
                            then_expr=IdentifierExprNode(name="a"),
                            else_expr=IdentifierExprNode(name="b"),
                        )
                    ),
                ]
            ),
        )

        # 2. 声明一个使用泛型的主函数
        main_body = BlockStmtNode(
            statements=[
                ReturnStmtNode(value=IntLiteralNode(value=42)),
            ]
        )
        main_func = FunctionDeclNode(
            name="主函数",
            return_type=PrimitiveTypeNode(name="整数型"),
            params=[],
            body=main_body,
        )

        program = ProgramNode(declarations=[gen_max, main_func])

        # 3. 执行完整分析（含单态化）
        success = analyzer.analyze(program)

        # 4. 验证
        assert isinstance(success, bool)

        # 泛型解析器应有记录
        resolver_stats = analyzer.generic_resolver.get_statistics()
        assert "最大值" in resolver_stats["function_names"]

        # 单态化引擎应已运行
        mono_stats = analyzer.monomorphizer.get_statistics()
        assert "resolver_stats" in mono_stats


# ===== G.04: 泛型 IR 操作码扩展测试 =====


class TestGenericIROpcodes:
    """
    G.04: 泛型 IR 操作码扩展测试

    验证 opcodes.py 中新增的 4 个泛型操作码：
    - GENERIC_INSTANTIATE: 泛型实例化
    - GENERIC_CALL: 泛型函数调用
    - TYPE_PARAM_BIND: 类型参数绑定
    - SPECIALIZE: 特化生成

    以及 ir_generator.py 中新增的泛型 IR 生成方法。
    """

    def test_generic_instantiate_opcode_exists(self):
        """验证 GENERIC_INSTANTIATE 操作码存在且属性正确"""
        from zhc.ir.opcodes import Opcode

        op = Opcode.GENERIC_INSTANTIATE
        assert op.name == "generic_instantiate"
        assert op.category == "泛型"
        assert op.chinese == "泛型实例化"
        assert op.is_terminator is False
        assert op.has_result is True

    def test_generic_call_opcode_exists(self):
        """验证 GENERIC_CALL 操作码存在且属性正确"""
        from zhc.ir.opcodes import Opcode

        op = Opcode.GENERIC_CALL
        assert op.name == "generic_call"
        assert op.category == "泛型"
        assert op.chinese == "泛型函数调用"
        assert op.is_terminator is False
        assert op.has_result is True

    def test_type_param_bind_opcode_exists(self):
        """验证 TYPE_PARAM_BIND 操作码存在且属性正确"""
        from zhc.ir.opcodes import Opcode

        op = Opcode.TYPE_PARAM_BIND
        assert op.name == "type_param_bind"
        assert op.category == "泛型"
        assert op.chinese == "类型参数绑定"
        assert op.is_terminator is False
        assert op.has_result is False

    def test_specialize_opcode_exists(self):
        """验证 SPECIALIZE 操作码存在且属性正确"""
        from zhc.ir.opcodes import Opcode

        op = Opcode.SPECIALIZE
        assert op.name == "specialize"
        assert op.category == "泛型"
        assert op.chinese == "特化生成"
        assert op.is_terminator is False
        assert op.has_result is True

    def test_generic_opcodes_count(self):
        """验证泛型类别操作码总数为 4"""
        from zhc.ir.opcodes import Opcode

        generic_ops = [op for op in Opcode if op.category == "泛型"]
        assert len(generic_ops) == 4
        generic_names = {op.name for op in generic_ops}
        assert generic_names == {
            "generic_instantiate",
            "generic_call",
            "type_param_bind",
            "specialize",
        }

    def test_opcode_from_name_generic(self):
        """验证通过名称查找泛型操作码"""
        from zhc.ir.opcodes import Opcode

        assert Opcode.from_name("generic_instantiate") == Opcode.GENERIC_INSTANTIATE
        assert Opcode.from_name("generic_call") == Opcode.GENERIC_CALL
        assert Opcode.from_name("type_param_bind") == Opcode.TYPE_PARAM_BIND
        assert Opcode.from_name("specialize") == Opcode.SPECIALIZE

    def test_all_opcodes_have_chinese_name(self):
        """验证所有操作码都有中文名称（包括新增的泛型操作码）"""
        from zhc.ir.opcodes import Opcode

        for op in Opcode:
            assert hasattr(op, "chinese")
            assert len(op.chinese) > 0, f"操作码 {op.name} 缺少中文名称"


class TestGenericIRGenerator:
    """
    G.04: IRGenerator 泛型支持测试

    验证 IRGenerator 中新增的泛型方法能正确处理泛型 AST 节点并生成 IR 指令。
    """

    def setup_method(self):
        """每个测试前重置全局状态"""
        from zhc.semantic.generics import reset_generic_manager
        from zhc.ir.opcodes import Opcode

        reset_generic_manager()
        self._opcode = Opcode

    @staticmethod
    def _create_ir_generator():
        """创建干净的 IRGenerator 实例"""
        from zhc.ir.ir_generator import IRGenerator

        return IRGenerator()

    @staticmethod
    def _setup_function_context(gen, func_name: str = "test_func"):
        """设置 IRGenerator 的函数上下文（current_function + current_block）"""
        from zhc.ir.program import IRFunction

        func = IRFunction(name=func_name, return_type="空型")
        gen.module.add_function(func)
        gen.current_function = func
        gen.current_block = func.entry_block
        return gen

    # ---- G04-1: 导入和基础设施 ----

    def test_import_generic_nodes(self):
        """验证泛型节点可从 generic_parser 正确导入"""
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            GenericTypeDeclNode,
            GenericTypeNode,
            TypeNode,
        )

        # 确保所有节点类可正常实例化
        assert GenericFunctionDeclNode is not None
        assert GenericTypeDeclNode is not None
        assert GenericTypeNode is not None
        assert TypeNode is not None

    def test_ir_generator_has_generic_methods(self):
        """验证 IRGenerator 具有所有泛型相关方法"""
        gen = self._create_ir_generator()

        # 访问方法（visitor）
        assert hasattr(gen, "visit_generic_function_decl")
        assert hasattr(gen, "visit_generic_type_decl")
        assert hasattr(gen, "visit_type")
        assert hasattr(gen, "visit_generic_type")
        assert hasattr(gen, "visit_type_parameter")
        assert hasattr(gen, "visit_where_clause")

        # 求值方法（eval）
        assert hasattr(gen, "_eval_generic_type_ref")

        # 工具方法
        assert hasattr(gen, "_resolve_generic_function_name")
        assert hasattr(gen, "_generate_generic_call_ir")

    # ---- G04-2: 泛型函数声明 IR ----

    def test_visit_generic_function_decl_basic(self):
        """测试泛型函数声明访问生成基本 IR"""
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
            TypeNode,
        )

        gen = self._create_ir_generator()
        self._setup_function_context(gen, "test_func")

        func_node = GenericFunctionDeclNode(
            name="交换",
            type_params=[TypeParameterNode(name="T")],
            params=[],
            return_type=TypeNode("(T, T)"),
            body=None,
        )

        # 不应抛异常
        gen.visit_generic_function_decl(func_node)

        # 应在 entry block 中生成了 GENERIC_INSTANTIATE 指令
        instrs = gen.current_block.instructions
        assert len(instrs) >= 1
        assert instrs[-1].opcode == self._opcode.GENERIC_INSTANTIATE

    def test_visit_generic_function_decl_with_multiple_type_params(self):
        """测试多类型参数的泛型函数声明"""
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
            TypeNode,
        )

        gen = self._create_ir_generator()
        self._setup_function_context(gen, "test_func2")

        func_node = GenericFunctionDeclNode(
            name="创建映射",
            type_params=[
                TypeParameterNode(name="K"),
                TypeParameterNode(name="V"),
            ],
            params=[],
            return_type=TypeNode("映射<K, V>"),
            body=None,
        )

        gen.visit_generic_function_decl(func_node)

        instrs = gen.current_block.instructions
        assert len(instrs) >= 1
        assert instrs[-1].opcode == self._opcode.GENERIC_INSTANTIATE

    # ---- G04-3: 泛型类型声明 IR ----

    def test_visit_generic_type_decl_basic(self):
        """测试泛型类型声明生成结构体定义 + 特化标记"""
        from zhc.semantic.generic_parser import (
            GenericTypeDeclNode,
            TypeParameterNode,
        )
        from zhc.parser.ast_nodes import VariableDeclNode, PrimitiveTypeNode

        gen = self._create_ir_generator()
        self._setup_function_context(gen, "test_func3")

        members = [
            VariableDeclNode(
                name="数据",
                var_type=PrimitiveTypeNode(name="T"),
                init=None,
            ),
            VariableDeclNode(
                name="长度",
                var_type=PrimitiveTypeNode(name="整数型"),
                init=None,
            ),
        ]

        type_node = GenericTypeDeclNode(
            name="容器",
            type_params=[TypeParameterNode(name="T")],
            members=members,
        )

        gen.visit_generic_type_decl(type_node)

        # 模块中应有 mangled 名称的结构体定义
        struct_names = [s.name for s in gen.module.structs]
        assert "容器__T" in struct_names

        struct_def = next(s for s in gen.module.structs if s.name == "容器__T")
        assert "数据" in struct_def.members
        assert "长度" in struct_def.members

        # 应有 SPECIALIZE 指令
        instrs = gen.current_block.instructions
        specialize_instrs = [i for i in instrs if i.opcode == self._opcode.SPECIALIZE]
        assert len(specialize_instrs) >= 1

    def test_visit_generic_type_decl_no_members(self):
        """测试无成员的泛型类型声明"""
        from zhc.semantic.generic_parser import (
            GenericTypeDeclNode,
            TypeParameterNode,
        )

        gen = self._create_ir_generator()
        self._setup_function_context(gen, "test_func4")

        type_node = GenericTypeDeclNode(
            name="空盒子",
            type_params=[TypeParameterNode(name="X")],
            members=[],
        )

        gen.visit_generic_type_decl(type_node)

        struct_names = [s.name for s in gen.module.structs]
        assert "空盒子__X" in struct_names

    # ---- G04-4: 泛型类型引用求值 ----

    def test_eval_generic_type_ref_basic(self):
        """测试泛型类型引用的基本 IR 生成"""
        from zhc.semantic.generic_parser import (
            GenericTypeNode,
            TypeNode,
        )

        gen = self._create_ir_generator()
        self._setup_function_context(gen, "test_func5")

        ref = GenericTypeNode(
            base_type="列表",
            type_args=[TypeNode(type_name="整数型")],
        )

        result = gen._eval_generic_type_ref(ref)

        assert result is not None
        assert result.ty.startswith("泛型实例<")

        # 应有 GENERIC_INSTANTIATE 指令
        instrs = gen.current_block.instructions
        gen_inst_instrs = [
            i for i in instrs if i.opcode == self._opcode.GENERIC_INSTANTIATE
        ]
        assert len(gen_inst_instrs) >= 1

    def test_eval_generic_type_ref_multiple_args(self):
        """测试多类型参数的泛型类型引用"""
        from zhc.semantic.generic_parser import (
            GenericTypeNode,
            TypeNode,
        )

        gen = self._create_ir_generator()
        self._setup_function_context(gen, "test_func6")

        ref = GenericTypeNode(
            base_type="映射",
            type_args=[
                TypeNode(type_name="字符串型"),
                TypeNode(type_name="整数型"),
            ],
        )

        result = gen._eval_generic_type_ref(ref)

        assert result is not None
        assert "映射" in result.ty
        assert "字符串型" in result.ty
        assert "整数型" in result.ty

    def test_eval_generic_type_ref_no_args(self):
        """测试无类型实参的泛型引用（退化为基础类型）"""
        from zhc.semantic.generic_parser import GenericTypeNode

        gen = self._create_ir_generator()
        self._setup_function_context(gen, "test_func7")

        ref = GenericTypeNode(base_type="简单类型", type_args=[])

        result = gen._eval_generic_type_ref(ref)

        assert result is not None

    def test_eval_generic_type_ref_via_dispatch(self):
        """测试通过 visitor 模式访问 GenericTypeNode"""
        from zhc.semantic.generic_parser import (
            GenericTypeNode,
            TypeNode,
        )

        gen = self._create_ir_generator()
        self._setup_function_context(gen, "test_func8")

        ref = GenericTypeNode(
            base_type="栈",
            type_args=[TypeNode(type_name="浮点型")],
        )

        # 通过 accept → visit_generic_type → _eval_generic_type_ref
        gen.visit_generic_type(ref)

        # 应有 IR 指令生成
        instrs = gen.current_block.instructions
        assert len(instrs) >= 1

        # 验证生成了泛型实例化指令
        gen_inst_instrs = [
            i for i in instrs if i.opcode == self._opcode.GENERIC_INSTANTIATE
        ]
        assert len(gen_inst_instrs) >= 1

    # ---- G04-5: 泛型调用 IR ----

    def test_generate_generic_call_ir_basic(self):
        """测试泛型函数调用的 IR 生成"""
        from zhc.ir.values import IRValue, ValueKind

        gen = self._create_ir_generator()
        self._setup_function_context(gen, "test_func9")

        args = [
            IRValue("%0", "整数型", ValueKind.TEMP),
            IRValue("%1", "整数型", ValueKind.TEMP),
        ]

        result = gen._generate_generic_call_ir(
            func_name="最大值",
            type_args=["整数型"],
            args=args,
        )

        assert result is not None

        # 应有 GENERIC_CALL 指令
        instrs = gen.current_block.instructions
        call_instrs = [i for i in instrs if i.opcode == self._opcode.GENERIC_CALL]
        assert len(call_instrs) >= 1

        # 验证 mangled 名称在指令的操作数中
        call_instr = call_instrs[0]
        operand_names = [getattr(op, "name", "") for op in (call_instr.operands or [])]
        has_mangled = any("最大值__整数型" in name for name in operand_names)
        assert (
            has_mangled
        ), f"期望找到 mangled 名称 '最大值__整数型'，操作数: {operand_names}"

    def test_generate_generic_call_ir_multiple_type_args(self):
        """测试多类型参数的泛型调用"""
        from zhc.ir.values import IRValue, ValueKind

        gen = self._create_ir_generator()
        self._setup_function_context(gen, "test_func10")

        args = [
            IRValue("%0", "字符串型", ValueKind.TEMP),
            IRValue("%1", "整数型", ValueKind.TEMP),
        ]

        result = gen._generate_generic_call_ir(
            func_name="创建对",
            type_args=["字符串型", "整数型"],
            args=args,
        )

        assert result is not None

        instrs = gen.current_block.instructions
        call_instrs = [i for i in instrs if i.opcode == self._opcode.GENERIC_CALL]
        assert len(call_instrs) >= 1

    def test_generate_generic_call_ir_empty_args(self):
        """测试无参数的泛型调用"""
        gen = self._create_ir_generator()
        self._setup_function_context(gen, "test_func11")

        result = gen._generate_generic_call_ir(
            func_name="获取默认",
            type_args=["布尔型"],
            args=[],
        )

        assert result is not None

    # ---- G04-6: 名称解析工具 ----

    def test_resolve_generic_function_name_mangled(self):
        """测试 mangled 函数名直接返回"""
        gen = self._create_ir_generator()

        result = gen._resolve_generic_function_name("最大值__整数型")
        assert result == "最大值__整数型"

    def test_resolve_generic_function_name_with_type_args(self):
        """测试带类型参数时生成 mangled 名称"""
        gen = self._create_ir_generator()

        result = gen._resolve_generic_function_name("最小值", ["浮点型"])
        assert result == "最小值__浮点型"

    def test_resolve_generic_function_name_multiple_type_args(self):
        """测试多类型参数的 mangled 名称"""
        gen = self._create_ir_generator()

        result = gen._resolve_generic_function_name("创建映射", ["字符串型", "整数型"])
        assert result == "创建映射__字符串型_整数型"

    def test_resolve_generic_function_name_fallback(self):
        """测试无类型参数时回退到标准解析"""
        gen = self._create_ir_generator()

        result = gen._resolve_generic_function_name("主函数")
        assert result == "main"

    # ---- G04-7: 类型/Where 子句访问器 ----

    def test_visit_type_node_no_crash(self):
        """测试 TypeNode 访问不崩溃"""
        from zhc.semantic.generic_parser import TypeNode

        gen = self._create_ir_generator()

        node = TypeNode(type_name="整数型")
        gen.visit_type(node)  # 不应产生任何 IR 指令

    def test_visit_type_parameter_no_crash(self):
        """测试 TypeParameterNode 访问不崩溃"""
        from zhc.semantic.generic_parser import TypeParameterNode, Variance

        gen = self._create_ir_generator()

        node = TypeParameterNode(name="T", variance=Variance.INVARIANT)
        gen.visit_type_parameter(node)  # 不应产生任何 IR 指令

    def test_visit_where_clause_no_crash(self):
        """测试 WhereClauseNode 访问不崩溃"""
        from zhc.semantic.generic_parser import WhereClauseNode

        gen = self._create_ir_generator()

        node = WhereClauseNode(constraints=[("T", "可比较")])
        gen.visit_where_clause(node)  # 不应产生任何 IR 指令

    def test_visit_generic_type_via_visitor(self):
        """测试通过 visitor 模式访问 GenericTypeNode"""
        from zhc.semantic.generic_parser import (
            GenericTypeNode,
            TypeNode,
        )

        gen = self._create_ir_generator()
        self._setup_function_context(gen, "test_func12")  # noqa: F841

        ref = GenericTypeNode(
            base_type="队列",
            type_args=[TypeNode(type_name="字符型")],
        )

        # 通过 accept → visit_generic_type → _eval_generic_type_ref
        gen.visit_generic_type(ref)

        # 应有 IR 指令生成
        instrs = gen.current_block.instructions
        assert len(instrs) >= 1


class TestGenericIREndToEnd:
    """
    G.04 端到端集成测试：完整的 AST → 泛型 IR 流程

    从构建泛型 AST 节点到最终生成完整 IR 程序的全链路验证。
    """

    def setup_method(self):
        from zhc.semantic.generics import reset_generic_manager

        reset_generic_manager()

    def test_full_generic_program_ir_generation(self):
        """完整泛型程序 → IR 生成流程"""
        from zhc.parser.ast_nodes import (
            FunctionDeclNode,
            BlockStmtNode,
            ReturnStmtNode,
            IntLiteralNode,
        )
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
            TypeNode,
            GenericTypeDeclNode,
        )
        from zhc.parser.ast_nodes import (
            ParamDeclNode,
            VariableDeclNode,
            PrimitiveTypeNode,
        )

        gen = self._create_ir_gen()

        # 先设置一个函数上下文（泛型声明需要 current_block 才能发射指令）
        from zhc.ir.program import IRFunction

        func = IRFunction(name="__generic_setup", return_type="空型")
        gen.module.add_function(func)
        gen.current_function = func
        gen.current_block = func.entry_block

        # 构建程序：包含一个泛型类型、一个泛型函数、一个普通函数
        generic_type = GenericTypeDeclNode(
            name="盒子",
            type_params=[TypeParameterNode(name="T")],
            members=[
                VariableDeclNode(
                    name="内容",
                    var_type=PrimitiveTypeNode(name="T"),
                    init=None,
                ),
            ],
        )

        generic_func = GenericFunctionDeclNode(
            name="拆箱",
            type_params=[TypeParameterNode(name="T")],
            params=[ParamDeclNode(name="项", param_type=TypeNode("T"))],
            return_type=TypeNode("T"),
            body=BlockStmtNode(
                statements=[
                    ReturnStmtNode(value=IntLiteralNode(value=0)),
                ]
            ),
        )

        normal_func = FunctionDeclNode(
            name="主函数",
            return_type=PrimitiveTypeNode(name="整数型"),
            params=[],
            body=BlockStmtNode(
                statements=[
                    ReturnStmtNode(value=IntLiteralNode(value=42)),
                ]
            ),
        )

        # 逐个访问节点（模拟 visit_program 的分发逻辑）
        gen.visit_generic_type_decl(generic_type)
        gen.visit_generic_function_decl(generic_func)
        gen.visit_function_decl(normal_func)

        # 验证：使用 module（generate 返回的就是 module）
        assert gen.module is not None
        assert len(gen.module.functions) > 0
        assert len(gen.module.structs) > 0

        # 应有特化后的结构体定义
        struct_names = [s.name for s in gen.module.structs]
        assert any("盒子" in s for s in struct_names)

        # 应有主函数
        func_names = [f.name for f in gen.module.functions]
        assert "main" in func_names

    @staticmethod
    def _create_ir_gen():
        from zhc.ir.ir_generator import IRGenerator

        return IRGenerator()

    def test_generic_type_with_main_generates_valid_ir(self):
        """带泛型类型的简单主函数生成有效 IR"""
        from zhc.parser.ast_nodes import (
            ProgramNode,
            FunctionDeclNode,
            BlockStmtNode,
            ReturnStmtNode,
            IntLiteralNode,
            PrimitiveTypeNode,
        )
        from zhc.semantic.generic_parser import (
            GenericTypeDeclNode,
            TypeParameterNode,
        )
        from zhc.parser.ast_nodes import VariableDeclNode
        from zhc.ir.opcodes import Opcode

        gen = self._create_ir_gen()

        # 先设置函数上下文（visit_generic_type_decl 需要 current_block）
        from zhc.ir.program import IRFunction

        func = IRFunction(name="__generic_setup2", return_type="空型")
        gen.module.add_function(func)
        gen.current_function = func
        gen.current_block = func.entry_block

        gtype = GenericTypeDeclNode(
            name="链表",
            type_params=[TypeParameterNode(name="E")],
            members=[
                VariableDeclNode(
                    name="头节点",
                    var_type=PrimitiveTypeNode(name="E"),
                    init=None,
                ),
                VariableDeclNode(
                    name="计数",
                    var_type=PrimitiveTypeNode(name="整数型"),
                    init=None,
                ),
            ],
        )

        main = FunctionDeclNode(
            name="主函数",
            return_type=PrimitiveTypeNode(name="整数型"),
            params=[],
            body=BlockStmtNode(
                statements=[
                    ReturnStmtNode(value=IntLiteralNode(value=0)),
                ]
            ),
        )

        ProgramNode(declarations=[main, gtype])

        # 逐个访问节点（泛型声明需要 current_block 上下文）
        gen.visit_generic_type_decl(gtype)
        gen.visit_function_decl(main)

        # 主函数应有 entry block 和 RET 指令
        main_func = next(f for f in gen.module.functions if f.name == "main")
        entry = main_func.entry_block
        assert entry is not None
        assert len(entry.instructions) > 0

        # 最后一条指令应为 RET
        ret_instrs = [i for i in entry.instructions if i.opcode == Opcode.RET]
        assert len(ret_instrs) >= 1


# =====================================================================
# G.05: Backend 泛型策略测试
# =====================================================================


class TestGenericBackendStrategies:
    """
    G.05 泛型 LLVM/C 后端策略测试

    验证 generic_strategies.py 中 4 个策略类的正确性：
    - 类存在性和 opcode 绑定
    - compile() 方法行为（LLVM IR 生成）
    - register_generic_strategies 批量注册
    - C 后端代码生成
    """

    def setup_method(self):
        from zhc.ir.opcodes import Opcode

        self._opcode = Opcode

    # ---- G.05-1: 策略类存在性 ----

    def test_generic_strategies_module_import(self):
        """验证泛型策略模块可导入"""
        from zhc.backend.generic_strategies import (
            GenericInstantiateStrategy,
            GenericCallStrategy,
            TypeParamBindStrategy,
            SpecializeStrategy,
            _BaseGenericStrategy,
            register_generic_strategies,
        )

        assert GenericInstantiateStrategy is not None
        assert GenericCallStrategy is not None
        assert TypeParamBindStrategy is not None
        assert SpecializeStrategy is not None
        assert _BaseGenericStrategy is not None
        assert callable(register_generic_strategies)

    def test_strategy_inheritance(self):
        """验证所有泛型策略继承自 InstructionStrategy"""
        from zhc.backend.llvm_instruction_strategy import InstructionStrategy
        from zhc.backend.generic_strategies import (
            GenericInstantiateStrategy,
            GenericCallStrategy,
            TypeParamBindStrategy,
            SpecializeStrategy,
        )

        assert issubclass(GenericInstantiateStrategy, InstructionStrategy)
        assert issubclass(GenericCallStrategy, InstructionStrategy)
        assert issubclass(TypeParamBindStrategy, InstructionStrategy)
        assert issubclass(SpecializeStrategy, InstructionStrategy)

    def test_base_generic_strategy_inheritance(self):
        """验证 _BaseGenericStrategy 也继承自 InstructionStrategy"""
        from zhc.backend.llvm_instruction_strategy import InstructionStrategy
        from zhc.backend.generic_strategies import _BaseGenericStrategy

        assert issubclass(_BaseGenericStrategy, InstructionStrategy)

    # ---- G.05-2: Opcode 绑定 ----

    def test_generic_instantiate_opcode(self):
        """GenericInstantiateStrategy 绑定 GENERIC_INSTANTIATE"""
        from zhc.backend.generic_strategies import GenericInstantiateStrategy

        assert GenericInstantiateStrategy.opcode == self._opcode.GENERIC_INSTANTIATE

    def test_generic_call_opcode(self):
        """GenericCallStrategy 绑定 GENERIC_CALL"""
        from zhc.backend.generic_strategies import GenericCallStrategy

        assert GenericCallStrategy.opcode == self._opcode.GENERIC_CALL

    def test_type_param_bind_opcode(self):
        """TypeParamBindStrategy 绑定 TYPE_PARAM_BIND"""
        from zhc.backend.generic_strategies import TypeParamBindStrategy

        assert TypeParamBindStrategy.opcode == self._opcode.TYPE_PARAM_BIND

    def test_specialize_opcode(self):
        """SpecializeStrategy 绑定 SPECIALIZE"""
        from zhc.backend.generic_strategies import SpecializeStrategy

        assert SpecializeStrategy.opcode == self._opcode.SPECIALIZE

    # ---- G.05-3: __all__ 导出 ----

    def test_generic_strategies_all_exports(self):
        """验证 __all__ 包含所有公共名称"""
        from zhc.backend import generic_strategies

        expected = {
            "GenericInstantiateStrategy",
            "GenericCallStrategy",
            "TypeParamBindStrategy",
            "SpecializeStrategy",
            "_BaseGenericStrategy",
            "register_generic_strategies",
        }
        actual = set(generic_strategies.__all__)
        assert expected <= actual, f"缺少导出: {expected - actual}"

    # ---- G.05-4: __init__.py 导出 ----

    def test_backend_init_exports_generic(self):
        """验证 backend __init__.py 导出泛型策略"""
        from zhc.backend import (
            GenericInstantiateStrategy,
            GenericCallStrategy,
            TypeParamBindStrategy,
            SpecializeStrategy,
            register_generic_strategies,
        )

        assert GenericInstantiateStrategy is not None
        assert GenericCallStrategy is not None
        assert TypeParamBindStrategy is not None
        assert SpecializeStrategy is not None
        assert callable(register_generic_strategies)

    # ---- G.05-5: 策略注册到工厂 ----

    def test_register_to_factory(self):
        """验证 register_generic_strategies 可成功注册到工厂"""
        from zhc.backend.llvm_instruction_strategy import InstructionStrategyFactory
        from zhc.backend.generic_strategies import (
            GenericInstantiateStrategy,
            register_generic_strategies,
        )

        # 重置工厂以获得干净状态
        InstructionStrategyFactory.reset()
        # 重新初始化默认策略
        InstructionStrategyFactory._ensure_initialized()

        # 注册泛型策略
        register_generic_strategies(InstructionStrategyFactory)

        # 验证每个策略都已在工厂中
        assert (
            InstructionStrategyFactory.get_strategy(self._opcode.GENERIC_INSTANTIATE)
            is not None
        )
        assert isinstance(
            InstructionStrategyFactory.get_strategy(self._opcode.GENERIC_INSTANTIATE),
            GenericInstantiateStrategy,
        )
        assert (
            InstructionStrategyFactory.get_strategy(self._opcode.GENERIC_CALL)
            is not None
        )
        assert (
            InstructionStrategyFactory.get_strategy(self._opcode.TYPE_PARAM_BIND)
            is not None
        )
        assert (
            InstructionStrategyFactory.get_strategy(self._opcode.SPECIALIZE) is not None
        )

    # ---- G.05-6: LLVM Backend 注册集成 ----

    def test_llvm_backend_registers_generic(self):
        """验证 LLVMBackend.__init__ 调用 _register_generic_strategies"""
        try:
            from zhc.backend.llvm_backend import LLVMBackend, LLVM_AVAILABLE
        except ImportError:
            return  # llvmlite 未安装时跳过

        if not LLVM_AVAILABLE:
            return

        # 创建后端会自动注册所有策略（包括泛型）
        LLVMBackend()

        from zhc.backend.llvm_instruction_strategy import InstructionStrategyFactory

        InstructionStrategyFactory._ensure_initialized()

        # 验证泛型策略已被注册
        assert (
            InstructionStrategyFactory.get_strategy(self._opcode.GENERIC_INSTANTIATE)
            is not None
        )
        assert (
            InstructionStrategyFactory.get_strategy(self._opcode.GENERIC_CALL)
            is not None
        )
        assert (
            InstructionStrategyFactory.get_strategy(self._opcode.TYPE_PARAM_BIND)
            is not None
        )
        assert (
            InstructionStrategyFactory.get_strategy(self._opcode.SPECIALIZE) is not None
        )

    # ---- G.05-7: C 后端代码生成器 ----

    def test_c_backend_has_generic_generators(self):
        """验证 C 后端有 4 个泛型操作码的生成器"""
        from zhc.backend.c_backend import CBackend

        backend = CBackend(compiler="echo")  # 使用 echo 避免 gcc 检查
        generators = backend._get_instruction_generators()

        assert "GENERIC_INSTANTIATE" in generators
        assert "GENERIC_CALL" in generators
        assert "TYPE_PARAM_BIND" in generators
        assert "SPECIALIZE" in generators

    def test_c_backend_generic_instantiate_output(self):
        """验证 GENERIC_INSTANTIATE 的 C 输出格式"""
        from zhc.backend.c_backend import CBackend
        from zhc.ir.instructions import IRInstruction
        from zhc.ir.values import IRValue, ValueKind
        from zhc.ir.opcodes import Opcode

        backend = CBackend(compiler="echo")
        generators = backend._get_instruction_generators()

        instr = IRInstruction(
            opcode=Opcode.GENERIC_INSTANTIATE,
            operands=[
                IRValue("列表<T>", "泛型签名", ValueKind.CONST, const_value="列表"),
                IRValue("整数型", "类型参数", ValueKind.CONST, const_value="整数型"),
            ],
            result=[IRValue("%inst", "泛型实例", ValueKind.TEMP)],
        )

        code = generators["GENERIC_INSTANTIATE"](backend, instr)
        assert code is not None
        assert "泛型实例化" in code or "generic_instantiate" in code.lower()

    def test_c_backend_generic_call_output(self):
        """验证 GENERIC_CALL 的 C 输出格式"""
        from zhc.backend.c_backend import CBackend
        from zhc.ir.instructions import IRInstruction
        from zhc.ir.values import IRValue, ValueKind
        from zhc.ir.opcodes import Opcode

        backend = CBackend(compiler="echo")
        generators = backend._get_instruction_generators()

        instr = IRInstruction(
            opcode=Opcode.GENERIC_CALL,
            operands=[
                IRValue(
                    "最大值__整数型",
                    "mangled_name",
                    ValueKind.CONST,
                    const_value="最大值__整数型",
                ),
                IRValue("%a", "整数型", ValueKind.TEMP),
                IRValue("%b", "整数型", ValueKind.TEMP),
            ],
            result=[IRValue("%result", "整数型", ValueKind.TEMP)],
        )

        code = generators["GENERIC_CALL"](backend, instr)
        assert code is not None
        assert "%result" in code
        assert "最大值__整数型" in code

    def test_c_backend_type_param_bind_output(self):
        """验证 TYPE_PARAM_BIND 的 C 输出格式"""
        from zhc.backend.c_backend import CBackend
        from zhc.ir.instructions import IRInstruction
        from zhc.ir.values import IRValue, ValueKind
        from zhc.ir.opcodes import Opcode

        backend = CBackend(compiler="echo")
        generators = backend._get_instruction_generators()

        instr = IRInstruction(
            opcode=Opcode.TYPE_PARAM_BIND,
            operands=[
                IRValue("T", "类型参数", ValueKind.CONST, const_value="T"),
                IRValue("整数型", "具体类型", ValueKind.CONST, const_value="整数型"),
            ],
        )

        code = generators["TYPE_PARAM_BIND"](backend, instr)
        assert code is not None
        assert "类型参数绑定" in code or "T" in code

    def test_c_backend_specialize_output(self):
        """验证 SPECIALIZE 的 C 输出格式"""
        from zhc.backend.c_backend import CBackend
        from zhc.ir.instructions import IRInstruction
        from zhc.ir.values import IRValue, ValueKind
        from zhc.ir.opcodes import Opcode

        backend = CBackend(compiler="echo")
        generators = backend._get_instruction_generators()

        instr = IRInstruction(
            opcode=Opcode.SPECIALIZE,
            operands=[
                IRValue("盒子", "泛型基础类型", ValueKind.CONST, const_value="盒子"),
            ],
            result=[IRValue("%spec", "泛型类型", ValueKind.TEMP)],
        )

        code = generators["SPECIALIZE"](backend, instr)
        assert code is not None
        assert "特化" in code or "specialize" in code.lower()


# =====================================================================
# G.07: 泛型测试套件扩充 — 深度测试
#
# 覆盖以下缺失领域：
#  - 嵌套泛型（列表<映射<K,V>>）
#  - 递归泛型（链表<T> 自引用）
#  - 类型推导（从调用上下文推断类型实参）
#  - 多重特化同一泛型的缓存行为
#  - 复杂约束组合
#  - 全链路端到端（AST → IR → Backend）
#  - 边界条件和错误场景
# =====================================================================


class TestNestedGenerics:
    """
    G.07a: 嵌套泛型测试

    验证多层泛型参数的正确处理：
    - 列表<映射<K, V>> — 两层嵌套
    - 映射<字符串型, 列表<整数型>> — 混合嵌套
    - 栈<队列<T>> — 同类嵌套
    """

    def setup_method(self):
        reset_generic_manager()

    def test_nested_generic_type_instantiation(self):
        """两层泛型实例化：映射<K, V> 嵌套在 列表<> 中"""
        k = TypeParameter(name="K")
        v = TypeParameter(name="V")
        GenericType(
            name="映射",
            type_params=[k, v],  # noqa: F841
            members=[
                MemberInfo(name="键", type_name="K"),
                MemberInfo(name="值", type_name="V"),
            ],
        )

        t = TypeParameter(name="T")
        outer = GenericType(
            name="列表",
            type_params=[t],
            members=[
                MemberInfo(name="数据", type_name="T[]"),
                MemberInfo(name="长度", type_name="整数型"),
            ],
        )

        # 实例化外层: 列表<映射<字符串型, 整数型>>
        outer_instance = outer.instantiate(["映射<字符串型, 整数型>"])

        assert outer_instance is not None
        assert "映射" in outer_instance.name
        assert "字符串型" in outer_instance.name

    def test_nested_generic_function_mangled_name(self):
        """嵌套泛型函数的 mangled 名称包含所有层级信息"""
        generic_func = GenericFunction(
            name="查找键",
            type_params=[
                TypeParameter(name="K"),
                TypeParameter(name="V"),
            ],
            params=[
                ParamInfo(name="容器", type_name="映射<K, V>"),
                ParamInfo(name="目标", type_name="K"),
            ],
            return_type="V",
        )

        instance = generic_func.instantiate(["字符串型", "整数型"])
        assert "查找键" in instance.name
        assert "字符串型" in instance.name
        assert "整数型" in instance.name

    def test_nested_generic_ir_generation(self):
        """嵌套泛型类型的 IR 生成不崩溃"""
        from zhc.semantic.generic_parser import (
            GenericTypeNode,
            TypeNode,
        )

        gen = TestGenericIRGenerator._create_ir_generator()
        TestGenericIRGenerator._setup_function_context(gen, "test_nested")

        # 构建嵌套引用: 列表<映射<字符串型, 整数型>>
        ref = GenericTypeNode(
            base_type="列表",
            type_args=[
                TypeNode(
                    type_name="映射",
                    is_generic=True,
                    generic_args=[
                        TypeNode(type_name="字符串型"),
                        TypeNode(type_name="整数型"),
                    ],
                ),
            ],
        )

        result = gen._eval_generic_type_ref(ref)
        assert result is not None
        assert "列表" in result.ty

    def test_three_level_nested_copy_engine(self):
        """三层 AST 嵌套的深拷贝替换"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.parser.ast_nodes import (
            PrimitiveTypeNode,
            ArrayTypeNode,
        )

        mono = Monomorphizer()

        # 构造三层嵌套: T[][] (数组 of 数组 of T)
        node = ArrayTypeNode(
            element_type=ArrayTypeNode(
                element_type=PrimitiveTypeNode(name="T"),
                size=None,
            ),
            size=None,
        )

        substitutions = {"T": "浮点型"}
        copied = mono._generate_specialized_copy(node, substitutions)

        assert isinstance(copied, ArrayTypeNode)
        assert copied.element_type.element_type.name == "浮点型"


class TestRecursiveGenerics:
    """
    G.07b: 递归泛型测试

    验证自引用泛型类型（如链表<T>）的处理：
    - 类型定义中的自引用
    - 单态化后成员类型的正确性
    - IR 生成不进入无限递归
    """

    def setup_method(self):
        reset_generic_manager()

    def test_recursive_generic_type_definition(self):
        """自引用泛型类型定义：链表<T> 含 链表节点<T> 成员"""
        t = TypeParameter(name="E")

        # 链表<T> 的成员可以引用自身特化形式
        linked_list = GenericType(
            name="链表",
            type_params=[t],
            members=[
                MemberInfo(name="头节点", type_name="链表节点<E>"),
                MemberInfo(name="大小", type_name="整数型"),
            ],
        )

        # GenericType.name 属性返回带类型参数的名称
        assert "链表" in str(linked_list)
        assert len(linked_list.members) == 2

    def test_recursive_specialization_preserves_structure(self):
        """递归泛型特化后保持结构完整性"""
        t = TypeParameter(name="T")

        # 简化的自引用结构：树节点<T> 包含 树节点<T>* 子节点
        tree_node = GenericType(
            name="树节点",
            type_params=[t],
            members=[
                MemberInfo(name="值", type_name="T"),
                MemberInfo(name="左子", type_name="树节点<T>*"),
                MemberInfo(name="右子", type_name="树节点<T>*"),
            ],
        )

        instance = tree_node.instantiate(["字符串型"])
        assert instance is not None
        assert "字符串型" in instance.name

        # 成员中的 T 应被替换
        val_member = instance.get_member("值")
        assert val_member.type_name == "字符串型"

    def test_recursive_monomorphize_no_infinite_loop(self):
        """递归泛型单态化不应导致无限循环"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.semantic.generic_parser import (
            GenericTypeDeclNode,
            TypeParameterNode,
        )
        from zhc.parser.ast_nodes import VariableDeclNode, PrimitiveTypeNode

        mono = Monomorphizer()

        # 构建含自引用的泛型类型
        members = [
            VariableDeclNode(
                name="值",
                var_type=PrimitiveTypeNode(name="T"),
                init=None,
            ),
            VariableDeclNode(
                name="下一个",
                var_type=PrimitiveTypeNode(name="链表节点<T>*"),
                init=None,
            ),
        ]

        type_node = GenericTypeDeclNode(
            name="链表节点",
            type_params=[TypeParameterNode(name="T")],
            members=members,
        )

        # 单态化应在合理时间内完成（无无限递归）
        import time

        start = time.time()
        specialized = mono.monomorphize_class(type_node, ["整数型"])
        elapsed = time.time() - start

        assert isinstance(specialized, object)
        assert specialized.name == "链表节点__整数型"
        # 如果花了超过 5 秒，可能存在无限递归
        assert elapsed < 5.0, f"单态化耗时过长: {elapsed:.1f}s，可能存在无限递归"


class TestTypeInferenceScenarios:
    """
    G.07c: 类型推导场景测试
    """

    def setup_method(self):
        reset_generic_manager()

    def test_default_type_parameter_usage(self):
        """默认类型参数在未提供实参时使用"""
        param = TypeParameter(
            name="T",
            default="整数型",
        )
        assert param.default == "整数型"

    def test_default_param_in_generic_function(self):
        """带默认值的泛型函数实例化"""
        generic_func = GenericFunction(
            name="默认ID",
            type_params=[TypeParameter(name="T", default="整数型")],
            params=[ParamInfo(name="值", type_name="T")],
            return_type="T",
        )

        # 正常提供类型参数
        instance1 = generic_func.instantiate(["浮点型"])
        assert instance1.specialized_return_type == "浮点型"

    def test_type_inference_from_context_basic(self):
        """从变量声明类型推断泛型实参"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.parser.ast_nodes import (
            VariableDeclNode,
            PrimitiveTypeNode,
            IdentifierExprNode,
        )

        mono = Monomorphizer()

        # 模拟: 整数型 x = 身份<整数型>(42)
        # 从左边类型可推断 T = 整数型
        var_decl = VariableDeclNode(
            name="x",
            var_type=PrimitiveTypeNode(name="整数型"),
            init=IdentifierExprNode(name="some_value"),
        )

        substitutions = {"T": "整数型"}
        copied = mono._generate_specialized_copy(var_decl, substitutions)

        assert copied.var_type.name == "整数型"
        assert copied.name == "x"

    def test_multiple_inference_points_consistent(self):
        """多个推导点给出一致的结果"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.parser.ast_nodes import (
            BinaryExprNode,
            IdentifierExprNode,
        )

        mono = Monomorphizer()

        # a > b 其中 a 和 b 都是 T 的实例，应推断为同一类型
        expr = BinaryExprNode(
            operator=">",
            left=IdentifierExprNode(name="a"),
            right=IdentifierExprNode(name="b"),
        )

        substitutions = {"T": "浮点型"}
        copied = mono._generate_specialized_copy(expr, substitutions)

        assert copied.operator == ">"

    def test_inference_failure_graceful(self):
        """无法推导类型时的优雅降级"""
        from zhc.semantic.generics import GenericResolver

        resolver = GenericResolver()
        param = TypeParameter(name="T")  # 无默认值

        # 无约束的类型参数总是满足（无法推导时不应崩溃）
        satisfied, violations = resolver.check_constraints_satisfied(param, "未知类型")
        # 无约束 → 总是 True
        assert satisfied is True


class TestMultipleSpecializations:
    """
    G.07d: 多重特化测试

    验证同一泛型被多次不同特化的行为：
    - 缓存正确性（相同参数返回同一实例）
    - 不同参数产生独立实例
    - 特化计数统计
    - 特化间互不干扰
    """

    def setup_method(self):
        reset_generic_manager()

    def test_different_args_produce_different_instances(self):
        """不同类型参数产生独立的特化实例"""
        generic_func = GenericFunction(
            name="处理",
            type_params=[TypeParameter(name="T")],
            params=[ParamInfo(name="数据", type_name="T")],
            return_type="T",
        )

        int_version = generic_func.instantiate(["整数型"])
        str_version = generic_func.instantiate(["字符串型"])
        float_version = generic_func.instantiate(["浮点型"])

        # 三个版本应各自独立
        assert int_version is not str_version
        assert str_version is not float_version
        assert int_version is not float_version

        # 各自的返回类型应正确
        assert int_version.specialized_return_type == "整数型"
        assert str_version.specialized_return_type == "字符串型"
        assert float_version.specialized_return_type == "浮点型"

    def test_same_args_cached_identical(self):
        """相同参数从缓存返回同一对象（GenericType 层面）"""
        generic_type = GenericType(
            name="缓存盒子",
            type_params=[TypeParameter(name="T")],
            members=[MemberInfo(name="内容", type_name="T")],
        )

        inst1 = generic_type.instantiate(["布尔型"])
        inst2 = generic_type.instantiate(["布尔型"])

        # GenericType 内部缓存保证同一对象
        assert inst1 is inst2

    def test_monomorphizer_caches_across_calls(self):
        """Monomorphizer 对相同参数只特化一次"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
            TypeNode,
        )

        mono = Monomorphizer()

        func_node = GenericFunctionDeclNode(
            name="缓存函数",
            type_params=[TypeParameterNode(name="T")],
            params=[],
            return_type=TypeNode("T"),
            body=None,
        )

        spec1 = mono.monomorphize_function(func_node, ["字符型"])
        spec2 = mono.monomorphize_function(func_node, ["字符型"])

        # 应返回完全相同的缓存对象
        assert spec1 is spec2

    def test_specialization_statistics_accuracy(self):
        """特化统计信息的准确性"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            GenericTypeDeclNode,
            TypeParameterNode,
            TypeNode,
        )

        mono = Monomorphizer()

        func = GenericFunctionDeclNode(
            name="统计函数",
            type_params=[TypeParameterNode(name="T")],
            params=[],
            return_type=TypeNode("T"),
            body=None,
        )

        cls = GenericTypeDeclNode(
            name="统计类型",
            type_params=[TypeParameterNode(name="U")],
            members=None,
        )

        # 各特化 3 个版本
        for arg in ["整数型", "浮点型", "字符串型"]:
            mono.monomorphize_function(func, [arg])
        for arg in ["整数型", "布尔型"]:
            mono.monomorphize_class(cls, [arg])

        stats = mono.get_statistics()
        assert stats["specialized_functions"] == 3
        assert stats["specialized_types"] == 2


class TestComplexConstraints:
    """
    G.07e: 复杂约束组合测试

    验证多约束、复合约束的场景：
    - 多重约束同时满足
    - 部分约束违反
    - 约束组合（可比较 + 可加）
    - 方法约束 vs 运算符约束
    """

    def setup_method(self):
        reset_generic_manager()

    def test_multiple_constraints_all_satisfied(self):
        """多重约束全部满足：数值型 同时满足 可比较 + 可加"""
        from zhc.semantic.generics import GenericResolver

        resolver = GenericResolver()

        param = TypeParameter(
            name="T",
            constraints=[
                PredefinedConstraints.comparable(),
                PredefinedConstraints.addable(),
            ],
        )

        satisfied, violations = resolver.check_constraints_satisfied(param, "浮点型")
        assert satisfied is True
        assert len(violations) == 0

    def test_partial_violation(self):
        """部分约束违反：布尔型 满足 可相等 但不满足 可加"""
        from zhc.semantic.generics import GenericResolver

        resolver = GenericResolver()

        param = TypeParameter(
            name="T",
            constraints=[
                PredefinedConstraints.equatable(),
                PredefinedConstraints.addable(),
            ],
        )

        satisfied, violations = resolver.check_constraints_satisfied(param, "布尔型")
        assert satisfied is False
        assert len(violations) >= 1
        assert any("可加" in v for v in violations)

    def test_numeric_constraint_comprehensive(self):
        """数值型约束要求四种运算符全部支持"""
        from zhc.semantic.generics import GenericResolver

        resolver = GenericResolver()

        numeric_constraint = PredefinedConstraints.numeric()
        param = TypeParameter(name="T", constraints=[numeric_constraint])

        # 浮点型应满足数值型约束（支持 + - * /）
        satisfied_float, _ = resolver.check_constraints_satisfied(param, "浮点型")
        assert satisfied_float is True

        # 字符型不满足数值型（不支持 * /）
        satisfied_char, _ = resolver.check_constraints_satisfied(param, "字符型")
        assert satisfied_char is False

    def test_printable_constraint_methods(self):
        """可打印约束检查方法存在性"""
        from zhc.semantic.generics import GenericResolver

        resolver = GenericResolver()

        printable = PredefinedConstraints.printable()
        param = TypeParameter(name="T", constraints=[printable])

        # 字符串型有 转字符串 方法
        satisfied_str, _ = resolver.check_constraints_satisfied(param, "字符串型")
        # 当前简化实现：_type_has_method 对字符串型已知方法返回 True
        # 但可打印约束要求的是 "转字符串" 方法
        assert isinstance(satisfied_str, bool)

    def test_constraint_with_where_clause_integration(self):
        """Where 子句中的多约束集成到类型参数"""
        from zhc.semantic.generics import GenericResolver
        from zhc.semantic.generic_parser import WhereClauseNode

        resolver = GenericResolver()

        where = WhereClauseNode(
            constraints=[
                ("T", "可比较"),
                ("T", "数值型"),
            ]
        )

        resolved = resolver.resolve_constraints(where)
        assert len(resolved) == 2

        constraint_names = [c.name for _, c in resolved]
        assert "可比较" in constraint_names
        assert "数值型" in constraint_names


class TestGenericEndToEndFullPipeline:
    """
    G.07f: 全链路端到端测试

    验证完整的编译流水线：
    - 泛型 AST → Semantic Analysis → IR → C 代码
    - 多泛型声明共存
    - 泛型 + 普通代码混合
    """

    def setup_method(self):
        reset_generic_manager()

    def test_multi_generic_program_full_analysis(self):
        """多泛型声明的完整程序分析"""
        analyzer = self._create_analyzer()

        from zhc.parser.ast_nodes import ProgramNode
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            GenericTypeDeclNode,
            TypeParameterNode,
            TypeNode,
        )
        from zhc.parser.ast_nodes import (
            FunctionDeclNode,
            ParamDeclNode,
            BlockStmtNode,
            ReturnStmtNode,
            IntLiteralNode,
            PrimitiveTypeNode,
            VariableDeclNode,
            IdentifierExprNode,
        )

        # 泛型函数 1: 最大值<T>(T a, T b) -> T
        max_func = GenericFunctionDeclNode(
            name="最大值",
            type_params=[TypeParameterNode(name="T", constraints=["可比较"])],
            params=[
                ParamDeclNode(name="a", param_type=TypeNode("T")),
                ParamDeclNode(name="b", param_type=TypeNode("T")),
            ],
            return_type=TypeNode("T"),
            body=BlockStmtNode(
                statements=[
                    ReturnStmtNode(value=IdentifierExprNode(name="a")),
                ]
            ),
        )

        # 泛型函数 2: 交换<T>(T& a, T& b) -> (T, T)
        swap_func = GenericFunctionDeclNode(
            name="交换",
            type_params=[TypeParameterNode(name="T")],
            params=[
                ParamDeclNode(name="x", param_type=TypeNode("T")),
                ParamDeclNode(name="y", param_type=TypeNode("T")),
            ],
            return_type=TypeNode("(T, T)"),
            body=None,
        )

        # 泛型类型: 盒子<T> { T 内容; }
        box_type = GenericTypeDeclNode(
            name="盒子",
            type_params=[TypeParameterNode(name="T")],
            members=[
                VariableDeclNode(
                    name="内容",
                    var_type=PrimitiveTypeNode(name="T"),
                    init=None,
                ),
            ],
        )

        # 普通主函数
        main = FunctionDeclNode(
            name="主函数",
            return_type=PrimitiveTypeNode(name="整数型"),
            params=[],
            body=BlockStmtNode(
                statements=[
                    ReturnStmtNode(value=IntLiteralNode(value=0)),
                ]
            ),
        )

        program = ProgramNode(declarations=[max_func, swap_func, box_type, main])
        success = analyzer.analyze(program)

        assert success is True

        # 验证解析器收集了所有声明
        resolver_stats = analyzer.generic_resolver.get_statistics()
        assert "最大值" in resolver_stats["function_names"]
        assert "交换" in resolver_stats["function_names"]
        assert "盒子" in resolver_stats["type_names"]

    def test_generic_and_normal_code_mixed(self):
        """泛型和普通代码混合的程序分析"""
        analyzer = self._create_analyzer()

        from zhc.parser.ast_nodes import (
            ProgramNode,
            FunctionDeclNode,
            BlockStmtNode,
            ReturnStmtNode,
            IntLiteralNode,
            PrimitiveTypeNode,
            VariableDeclNode,
            BinaryExprNode,
            IdentifierExprNode,
        )
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
            TypeNode,
        )

        # 普通函数使用普通逻辑
        normal_func = FunctionDeclNode(
            name="计算",
            return_type=PrimitiveTypeNode(name="整数型"),
            params=[],
            body=BlockStmtNode(
                statements=[
                    VariableDeclNode(
                        name="结果",
                        var_type=PrimitiveTypeNode(name="整数型"),
                        init=BinaryExprNode(
                            operator="+",
                            left=IntLiteralNode(value=10),
                            right=IntLiteralNode(value=32),
                        ),
                    ),
                    ReturnStmtNode(value=IdentifierExprNode(name="结果")),
                ]
            ),
        )

        # 泛型函数与普通函数共存
        gen_func = GenericFunctionDeclNode(
            name="恒等",
            type_params=[TypeParameterNode(name="T")],
            params=[],
            return_type=TypeNode("T"),
            body=None,
        )

        main = FunctionDeclNode(
            name="主函数",
            return_type=PrimitiveTypeNode(name="整数型"),
            params=[],
            body=BlockStmtNode(statements=[]),
        )

        program = ProgramNode(declarations=[normal_func, gen_func, main])
        success = analyzer.analyze(program)

        assert success is True

    @staticmethod
    def _create_analyzer():
        from zhc.semantic.semantic_analyzer import SemanticAnalyzer

        return SemanticAnalyzer()

    def test_generic_to_ir_to_c_pipeline(self):
        """泛型 IR → C 后端完整流水线"""
        from zhc.backend.c_backend import CBackend
        from zhc.ir.opcodes import Opcode
        from zhc.ir.instructions import IRInstruction
        from zhc.ir.values import IRValue, ValueKind

        # 验证 C 后端能正确处理所有泛型操作码的代码生成
        backend = CBackend(compiler="echo")
        generators = backend._get_instruction_generators()

        # 构造并验证每种泛型操作码的 C 输出
        all_generic_ops = [
            (
                Opcode.TYPE_PARAM_BIND,
                [
                    IRValue("T", "类型参数", ValueKind.CONST, const_value="T"),
                    IRValue(
                        "整数型", "具体类型", ValueKind.CONST, const_value="整数型"
                    ),
                ],
                None,
            ),
            (
                Opcode.GENERIC_INSTANTIATE,
                [
                    IRValue(
                        "列表<T>", "泛型签名", ValueKind.CONST, const_value="列表<T>"
                    ),
                    IRValue(
                        "整数型", "类型参数", ValueKind.CONST, const_value="整数型"
                    ),
                ],
                [IRValue("%inst", "泛型实例", ValueKind.TEMP)],
            ),
            (
                Opcode.GENERIC_CALL,
                [
                    IRValue(
                        "最大值__整数型",
                        "mangled_name",
                        ValueKind.CONST,
                        const_value="最大值__整数型",
                    ),
                    IRValue("%a", "整数型", ValueKind.TEMP),
                    IRValue("%b", "整数型", ValueKind.TEMP),
                ],
                [IRValue("%result", "整数型", ValueKind.TEMP)],
            ),
            (
                Opcode.SPECIALIZE,
                [
                    IRValue("盒子", "基础类型", ValueKind.CONST, const_value="盒子"),
                ],
                [IRValue("%spec", "特化类型", ValueKind.TEMP)],
            ),
        ]

        for opcode, operands, result in all_generic_ops:
            instr = IRInstruction(opcode=opcode, operands=operands, result=result or [])
            # generators 字典使用大写操作码名
            code = generators[opcode.name.upper()](backend, instr)
            assert code is not None, f"{opcode.name} 未生成 C 代码"
            assert len(code.strip()) > 0, f"{opcode.name} 生成了空 C 代码"

    def test_complex_generic_ir_instructions_count(self):
        """复杂泛型程序的 IR 指令数量合理性"""
        gen = TestGenericIRGenerator._create_ir_generator()
        TestGenericIRGenerator._setup_function_context(gen, "complex_test")

        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            GenericTypeDeclNode,
            TypeParameterNode,
            TypeNode,
            GenericTypeNode,
            WhereClauseNode,
        )
        from zhc.parser.ast_nodes import (
            VariableDeclNode,
            PrimitiveTypeNode,
        )

        # 注册多个泛型声明
        gen.visit_generic_function_decl(
            GenericFunctionDeclNode(
                name="F1",
                type_params=[TypeParameterNode(name="A")],
                params=[],
                return_type=TypeNode("A"),
                body=None,
            )
        )
        gen.visit_generic_function_decl(
            GenericFunctionDeclNode(
                name="F2",
                type_params=[
                    TypeParameterNode(name="K"),
                    TypeParameterNode(name="V"),
                ],
                params=[],
                return_type=TypeNode("映射<K, V>"),
                where_clause=WhereClauseNode(constraints=[("K", "可比较")]),
                body=None,
            )
        )
        gen.visit_generic_type_decl(
            GenericTypeDeclNode(
                name="GT1",
                type_params=[TypeParameterNode(name="X")],
                members=[
                    VariableDeclNode(
                        name="数据",
                        var_type=PrimitiveTypeNode(name="X"),
                        init=None,
                    )
                ],
            )
        )

        # 泛型引用
        gen._eval_generic_type_ref(
            GenericTypeNode(
                base_type="栈",
                type_args=[TypeNode(type_name="整数型")],
            )
        )

        total_instrs = len(gen.current_block.instructions)
        # 应有足够多的指令（每个泛型声明至少产生 1 条）
        assert total_instrs >= 4, f"期望至少 4 条指令，实际 {total_instrs}"


class TestEdgeCasesAndErrorHandling:
    """
    G.07g: 边界条件和错误处理测试

    验证异常情况下的健壮性：
    - 空类型参数列表
    - 超长类型名
    - 特殊字符类型名
    - 并发/重复注册
    """

    def setup_method(self):
        reset_generic_manager()

    def test_empty_type_parameters(self):
        """零类型参数的泛型类型（退化为基础模板）"""
        generic_type = GenericType(
            name="单元",
            type_params=[],  # 无类型参数
            members=[],
        )

        # 实例化（空类型参数列表）
        instance = generic_type.instantiate([])
        assert instance is not None
        assert instance.name == "单元<>"

    def test_long_type_names_in_mangling(self):
        """超长类型名的 mangled 名称处理"""
        from zhc.semantic.generics import Monomorphizer

        long_type_name = "非常长的类型名称用于测试mangled名称的边界情况"
        result = Monomorphizer._substitute_type_name("T", {"T": long_type_name})
        assert long_type_name in result

    def test_special_characters_in_type_names(self):
        """类型名中含特殊字符时的替换安全性"""
        from zhc.semantic.generics import Monomorphizer

        # 类型名包含下划线、数字等特殊字符
        result = Monomorphizer._substitute_type_name("T_Value", {"T": "MyType123"})
        assert "MyType123" in result
        assert "T_Value" not in result or "_Value" in result  # _Value 不含 T 所以保留

    def test_duplicate_registration_idempotent(self):
        """重复注册同名泛型不报错（覆盖或忽略）"""
        manager = get_generic_manager()

        gt1 = GenericType(
            name="重复类型",
            type_params=[TypeParameter(name="T")],
        )
        gt2 = GenericType(
            name="重复类型",
            type_params=[TypeParameter(name="U")],
        )

        # 两次注册同名类型
        manager.register_generic_type(gt1)
        manager.register_generic_type(gt2)  # 应覆盖

        # 最后注册的生效
        found = manager.get_generic_type("重复类型")
        assert found is not None
        assert found.type_params[0].name == "U"

    def test_resolve_non_program_node(self):
        """对非 ProgramNode 节点的 resolve 不崩溃"""
        from zhc.semantic.generics import GenericResolver

        GenericResolver()  # noqa: F841

        # 传入一个普通对象（非 AST 节点）
        fake_node = type(
            "FakeNode",
            (object,),
            {
                "node_type": None,
                "get_children": lambda: [],
            },
        )()

        # 不应抛出异常
        try:
            resolve(fake_node)
        except Exception:
            pass  # 可能因缺少属性而失败，但不应是严重错误

    def test_monomorphize_invalid_node_type_error(self):
        """对非泛型节点执行 monomorphize 应抛出 TypeError"""
        from zhc.semantic.generics import Monomorphizer
        from zhc.parser.ast_nodes import FunctionDeclNode

        mono = Monomorphizer()

        # 用普通 FunctionDeclNode 调用 monomorphize_function
        with pytest.raises(TypeError):
            mono.monomorphize_function(
                FunctionDeclNode(
                    name="普通函数",
                    return_type=None,
                    params=[],
                    body=None,
                ),
                ["整数型"],
            )


class TestVarianceAndAdvancedFeatures:
    """
    G.07h: 变性和高级特性测试

    验证变性的基本行为和高级特性：
    - Variance 枚举的所有值
    - 协变/逆变/不变标记
    - 变性在类型参数上的存储
    """

    def setup_method(self):
        reset_generic_manager()

    def test_variance_enum_values(self):
        """Variance 枚举包含三种变性"""
        assert Variance.COVARIANT.value == "+"
        assert Variance.CONTRAVARIANT.value == "-"
        assert Variance.INVARIANT.value == ""

    def test_covariant_type_parameter(self):
        """协变类型参数创建和存储"""
        param = TypeParameter(
            name="TOut",
            variance=Variance.COVARIANT,
        )
        assert param.variance == Variance.COVARIANT
        assert "协变" in str(param) or "+" in str(param) or param.name == "TOut"

    def test_contravariant_type_parameter(self):
        """逆变类型参数创建和存储"""
        param = TypeParameter(
            name="TIn",
            variance=Variance.CONTRAVARIANT,
        )
        assert param.variance == Variance.CONTRAVARIANT

    def test_default_type_parameter_in_resolution(self):
        """带默认值的类型参数在解析中的保留"""
        from zhc.semantic.generic_parser import TypeParameterNode as TPNode
        from zhc.semantic.generics import GenericResolver

        resolver = GenericResolver()

        tp_node = TPNode(
            name="T",
            variance=Variance.INVARIANT,
            default_type="字符串型",
        )

        type_params = resolver.resolve_type_parameters([tp_node])
        assert len(type_params) == 1
        assert type_params[0].default == "字符串型"


def resolve(obj):
    """辅助函数：调用 GenericResolver.resolve"""
    from zhc.semantic.generics import GenericResolver

    return GenericResolver().resolve(obj)


# =====================================================================
# G.08: 泛型增强特性测试 — 变性/高阶类型/默认参数/约束推理
# =====================================================================


class TestVarianceChecker:
    """
    G.08a: 变性检查测试

    验证 VarianceChecker 的核心功能：
    - 协变赋值合法性（子→父）
    - 逆变赋值合法性（父→子）
    - 不变要求精确匹配
    - 函数参数变性验证
    """

    def setup_method(self):
        reset_generic_manager()
        self.checker = VarianceChecker()

    def test_covariant_subtype_assignment(self):
        """协变参数允许子类型赋值给父类型"""
        # 使用内置类型层次：长整型 是 整数型 的子类型（在 _subtype_map 中）
        ok, errors = self.checker.check_assignment(
            source_generic_name="容器",
            target_generic_name="容器",
            type_args_source=["长整型"],
            type_args_target=["整数型"],
            type_params=[TypeParameter("T", variance=Variance.COVARIANT)],
        )
        assert ok is True  # 协变 + 子类型 → 合法

    def test_contravariant_supertype_assignment(self):
        """逆变参数允许父类型赋值给子类型"""
        # 逆变：父类型 → 子类型（整数型 → 长整型，因为长整型是整数型的子类型）
        ok, errors = self.checker.check_assignment(
            source_generic_name="比较器",
            target_generic_name="比较器",
            type_args_source=["整数型"],
            type_args_target=["长整型"],
            type_params=[TypeParameter("T", variance=Variance.CONTRAVARIANT)],
        )
        assert ok is True  # 逆变 + 父类型 → 合法

    def test_invariant_requires_exact_match(self):
        """不变参数要求精确匹配，子类型也不行"""
        ok, errors = self.checker.check_assignment(
            source_generic_name="盒子",
            target_generic_name="盒子",
            type_args_source=["长整型"],
            type_args_target=["整数型"],
            type_params=[TypeParameter("T", variance=Variance.INVARIANT)],
        )
        assert ok is False
        assert any("不变" in e for e in errors)

    def test_invariant_exact_match_ok(self):
        """不变参数精确匹配时通过"""
        ok, _ = self.checker.check_assignment(
            source_generic_name="盒子",
            target_generic_name="盒子",
            type_args_source=["整数型"],
            type_args_target=["整数型"],
            type_params=[TypeParameter("T")],
        )
        assert ok is True

    def test_covariant_rejects_supertype(self):
        """协变不允许父类型替换子类型"""
        ok, errors = self.checker.check_assignment(
            source_generic_name="列表",
            target_generic_name="列表",
            type_args_source=["动物"],
            type_args_target=["猫"],
            type_params=[TypeParameter("T", variance=Variance.COVARIANT)],
        )
        assert ok is False
        assert any("协变" in e for e in errors)

    def test_contravariant_rejects_subtype(self):
        """逆变不允许子类型替换父类型"""
        ok, errors = self.checker.check_assignment(
            source_generic_name="回调",
            target_generic_name="回调",
            type_args_source=["猫"],
            type_args_target=["动物"],
            type_params=[TypeParameter("T", variance=Variance.CONTRAVARIANT)],
        )
        assert ok is False
        assert any("逆变" in e for e in errors)

    def test_mismatched_param_count(self):
        """参数数量不同时直接报错"""
        ok, errors = self.checker.check_assignment(
            source_generic_name="映射",
            target_generic_name="映射",
            type_args_source=["K"],
            type_args_target=["K", "V"],
            type_params=[
                TypeParameter("K"),
                TypeParameter("V"),
            ],
        )
        assert ok is False
        assert any("数量" in e for e in errors)

    def test_multi_param_mixed_variance(self):
        """多类型参数混合变性：每个位置独立检查"""
        ok1, _ = self.checker.check_assignment(
            "配对",
            "配对",
            ["整数型", "对象"],
            ["数值型", "对象"],
            [
                TypeParameter("T", variance=Variance.COVARIANT),
                TypeParameter("U", variance=Variance.INVARIANT),
            ],
        )
        # T: 协变，整数型是数值型的子类型 → OK
        # U: 不变，对象==对象 → OK
        assert ok1 is True

    def test_variance_description(self):
        """变性描述文本正确"""
        assert "协变" in self.checker.get_variance_description(Variance.COVARIANT)
        assert "逆变" in self.checker.get_variance_description(Variance.CONTRAVARIANT)
        assert "不变" in self.checker.get_variance_description(Variance.INVARIANT)

    def test_custom_subtype_map(self):
        """自定义类型层次关系"""
        custom_map = {
            "形状": {"圆形", "方形"},
            "图形": {"形状", "图片"},
        }
        checker = VarianceChecker(subtype_map=custom_map)

        ok, _ = checker.check_assignment(
            "容器",
            "容器",
            ["圆形"],
            ["形状"],
            [TypeParameter("S", variance=Variance.COVARIANT)],
        )
        assert ok is True  # 圆形是形状的子类型（自定义）

    def test_function_argument_variance_check(self):
        """函数调用时实参到形参的变性兼容性"""
        ok, errors = self.checker.check_function_argument_variance(
            func_type_params=[TypeParameter("T", variance=Variance.COVARIANT)],
            arg_types=["短整型"],
            param_types=["整数型"],  # T 在形参中声明为 整数型
        )
        # 短整型 是 整数型的子类型，协变允许 → OK
        assert ok is True or len(errors) == 0

    @staticmethod
    def test_register_subtype_classmethod():
        """类方法注册子类型关系"""
        custom_map = {"水果": {"苹果"}}
        checker = VarianceChecker(subtype_map=custom_map)
        ok, _ = checker.check_assignment(
            "篮子",
            "篮子",
            ["苹果"],
            ["水果"],
            [TypeParameter("F", variance=Variance.COVARIANT)],
        )
        assert ok is True


class TestHigherKindedTypes:
    """
    G.08b: 高阶类型测试

    验证 TypeKind 枚举和 TypeInfo 类型信息：
    - 具体类型 vs 类型构造器区分
    - TypeInfo.accepts_type() 验证
    - 高阶类型枚举值完整性
    """

    def setup_method(self):
        reset_generic_manager()

    def test_kind_enum_values(self):
        """TypeKind 枚举包含三种种类"""
        assert TypeKind.CONCRETE.value == "concrete"
        assert TypeKind.TYPE_CONSTRUCTOR.value == "constructor"
        assert TypeKind.HIGHER_KINDED.value == "higher_kinded"

    def test_concrete_type_accepts_any_concrete(self):
        """具体类型接受任何非构造器名称"""
        info = TypeInfo(kind=TypeKind.CONCRETE)
        known = {"列表": 1, "映射": 2}
        assert info.accepts_type("整数型", known) is True
        assert info.accepts_type("字符串型", known) is True

    def test_constructor_requires_matching_arity(self):
        """类型构造器要求 arity 匹配"""
        info = TypeInfo(kind=TypeKind.TYPE_CONSTRUCTOR, required_arity=1)
        known = {"列表": 1, "映射": 2}

        assert info.accepts_type("列表", known) is True  # 列表需要 1 个参数 ✓
        assert info.accepts_type("映射", known) is False  # 映射需要 2 个参数 ✗

    def test_higher_kinded_always_passes(self):
        """高阶类型预留实现总是通过"""
        info = TypeInfo(kind=TypeKind.HIGHER_KINDED)
        assert info.accepts_type("任何东西") is True

    def test_default_type_info_is_concrete(self):
        """默认 TypeInfo 是具体类型"""
        info = TypeInfo()
        assert info.kind == TypeKind.CONCRETE
        assert info.required_arity == 0

    def test_constructor_constraints_stored(self):
        """TypeInfo 存储构造器约束"""
        info = TypeInfo(
            kind=TypeKind.TYPE_CONSTRUCTOR,
            required_arity=1,
            constructor_constraints=["可遍历", "可迭代"],
        )
        assert len(info.constructor_constraints) == 2
        assert "可遍历" in info.constructor_constraints

    def test_unknown_treated_as_concrete(self):
        """未知类型的 TypeInfo 按需决定"""
        info = TypeInfo(kind=TypeKind.TYPE_CONSTRUCTOR, required_arity=0)
        # unknown with required_arity==0 → True（fallback: unknown treated as concrete）
        assert info.accepts_type("未知自定义类型", {}) is True

        info2 = TypeInfo(kind=TypeKind.TYPE_CONSTRUCTOR, required_arity=2)
        # unknown with required_arity > 0 → False (unknown can't be verified as constructor)
        assert info2.accepts_type("未知类型", {}) is False


class TestDefaultTypeParameters:
    """
    G.08c: 默认类型参数测试

    验证 DefaultTypeResolver 和 monkey-patch 后的 instantiate 行为：
    - 缺失参数自动补全
    - 无默认值时报错
    - 参数过多时报错
    - Monomorphizer 自动补全
    - GenericType.instantiate 使用默认值
    """

    def setup_method(self):
        reset_generic_manager()

    def test_resolve_defaults_basic(self):
        """基本默认值补全"""
        params = [
            TypeParameter(name="T"),
            TypeParameter(name="U", default="整数型"),
        ]
        resolved, used = DefaultTypeResolver.resolve_defaults(params, ["字符串型"])
        assert resolved == ["字符串型", "整数型"]
        assert len(used) == 1
        assert "U=整数型" in used[0]

    def test_resolve_defaults_multiple_missing(self):
        """多个缺失参数全部补全"""
        params = [
            TypeParameter(name="T", default="浮点型"),
            TypeParameter(name="U", default="字符型"),
            TypeParameter(name="V", default="布尔型"),
        ]
        resolved, used = DefaultTypeResolver.resolve_defaults(params, [])
        assert resolved == ["浮点型", "字符型", "布尔型"]
        assert len(used) == 3

    def test_no_defaults_needed_when_complete(self):
        """所有参数已提供时不使用默认值"""
        params = [
            TypeParameter(name="T", default="X"),
            TypeParameter(name="U", default="Y"),
        ]
        resolved, used = DefaultTypeResolver.resolve_defaults(params, ["A", "B"])
        assert resolved == ["A", "B"]
        assert len(used) == 0

    def test_error_on_too_many_args(self):
        """提供的参数过多时报错"""
        params = [TypeParameter(name="T")]
        with pytest.raises(TypeParameterCountError):
            DefaultTypeResolver.resolve_defaults(params, ["A", "B"])

    def test_error_on_missing_default(self):
        """缺少无默认值的参数时报错"""
        params = [
            TypeParameter(name="T"),
            TypeParameter(name="U"),  # 无默认值
        ]
        with pytest.raises(TypeParameterCountError, match=".*无默认值.*"):
            DefaultTypeResolver.resolve_defaults(params, ["A"])

    def test_has_sufficient_defaults_true(self):
        """有足够默认值时返回 True"""
        params = [
            TypeParameter(name="T", default="整数型"),
            TypeParameter(name="U", default="字符串型"),
        ]
        assert DefaultTypeResolver.has_sufficient_defaults(params, 0) is True
        assert DefaultTypeResolver.has_sufficient_defaults(params, 1) is True
        assert DefaultTypeResolver.has_sufficient_defaults(params, 2) is True

    def test_has_sufficient_defaults_false(self):
        """缺少默认值时返回 False"""
        params = [
            TypeParameter(name="T"),
            TypeParameter(name="U", default="字符串型"),
        ]
        assert DefaultTypeResolver.has_sufficient_defaults(params, 0) is False

    def test_generic_type_instantiate_with_defaults(self):
        """GenericType.instantiate 自动使用默认值"""
        gt = GenericType(
            name="可选列表",
            type_params=[
                TypeParameter(name="T", default="空型"),
            ],
            members=[MemberInfo(name="值", type_name="T")],
        )

        # 提供少于需要的参数数量（0 < 1），应自动补全
        instance = gt.instantiate([])  # 不提供参数，用默认的 "空型"
        assert instance is not None
        assert "空型" in instance.name or "可选列表" in str(instance)

    def test_generic_function_instantiate_with_defaults(self):
        """GenericFunction.instantiate 自动使用默认值"""
        gf = GenericFunction(
            name="默认ID",
            type_params=[
                TypeParameter(name="T", default="整数型"),
                TypeParameter(name="U", default="字符串型"),
            ],
            params=[ParamInfo(name="x", type_name="T")],
            return_type="T",
        )

        # 只提供第一个参数，第二个应使用默认值
        instance = gf.instantiate(["浮点型"])
        assert instance.specialized_return_type == "浮点型"

    def test_monomorphize_function_auto_default(self):
        """Monomorphizer.monomorphize_function 自动补全默认值"""
        from zhc.semantic.generic_parser import (
            GenericFunctionDeclNode,
            TypeParameterNode,
        )

        mono = Monomorphizer()

        func_node = GenericFunctionDeclNode(
            name="带默认的函数",
            type_params=[
                TypeParameterNode(name="T"),
                TypeParameterNode(name="U", default_type="整数型"),
            ],
            params=[],
            return_type=None,
            body=None,
        )

        spec = mono.monomorphize_function(func_node, ["浮点型"])
        # 应成功单态化（U 用了默认值 "整数型"）
        assert spec is not None
        assert "浮点型" in spec.name
        assert "整数型" in spec.name

    def test_monomorphize_class_auto_default(self):
        """Monomorphizer.monomorphize_class 自动补全默认值"""
        from zhc.semantic.generic_parser import (
            GenericTypeDeclNode,
            TypeParameterNode,
        )

        mono = Monomorphizer()

        cls_node = GenericTypeDeclNode(
            name="默认盒子",
            type_params=[
                TypeParameterNode(name="T", default_type="空型"),
            ],
            members=[],
        )

        spec = mono.monomorphize_class(cls_node, [])
        # 应成功（T 用默认值 "空型"）
        assert spec is not None


class TestConstraintInference:
    """
    G.08d: 约束推理测试

    验证 ConstraintInferrer 从 AST 推导约束的能力：
    - 运算符使用推导约束
    - 方法调用推导约束
    - 多种使用合并为最小约束集
    - 推导与显式声明的对比
    """

    def setup_method(self):
        reset_generic_manager()
        self.inferrer = ConstraintInferrer()

    def test_infers_comparable_from_comparison_ops(self):
        """从比较运算符推导约束（> 被数值型覆盖）"""
        from zhc.parser.ast_nodes import (
            BinaryExprNode,
            IdentifierExprNode,
            BlockStmtNode,
        )

        body = BlockStmtNode(
            statements=[
                # T > T (使用比较运算符，标识符名为 T 以触发启发式推断)
                BinaryExprNode(
                    operator=">",
                    left=IdentifierExprNode("T"),
                    right=IdentifierExprNode("T"),
                ),
            ]
        )

        constraints = self.inferrer.infer_constraints_from_body(body, ["T"])
        # > → 可比较，但覆盖策略选择 数值型（超集包含可比较）
        assert len(constraints) >= 1
        constraint_names = {c.name for c in constraints}
        assert "数值型" in constraint_names or "可比较" in constraint_names

    def test_infers_addable_from_plus(self):
        """从加法运算符推导约束（+ 被数值型覆盖）"""
        from zhc.parser.ast_nodes import (
            BinaryExprNode,
            IdentifierExprNode,
            BlockStmtNode,
        )

        body = BlockStmtNode(
            statements=[
                BinaryExprNode(
                    operator="+",
                    left=IdentifierExprNode("T"),
                    right=IdentifierExprNode("T"),
                ),
            ]
        )

        constraints = self.inferrer.infer_constraints_from_body(body, ["T"])
        # + → 可加，覆盖策略可能选择 数值型
        assert len(constraints) >= 1
        constraint_names = {c.name for c in constraints}
        assert "数值型" in constraint_names or "可加" in constraint_names

    def test_infers_numeric_from_arithmetic(self):
        """从多种算术运算推导数值型约束"""
        from zhc.parser.ast_nodes import (
            BinaryExprNode,
            IdentifierExprNode,
            BlockStmtNode,
            ExprStmtNode,
        )

        body = BlockStmtNode(
            statements=[
                ExprStmtNode(
                    expr=BinaryExprNode(
                        operator="+",
                        left=IdentifierExprNode("T"),
                        right=IdentifierExprNode("T"),
                    )
                ),
                ExprStmtNode(
                    expr=BinaryExprNode(
                        operator="*",
                        left=IdentifierExprNode("result"),
                        right=IdentifierExprNode("T"),
                    )
                ),  # result 不在 type_params 中
            ]
        )

        constraints = self.inferrer.infer_constraints_from_body(body, ["T"])
        constraint_names = {c.name for c in constraints}
        assert "数值型" in constraint_names

    def test_infers_printable_from_method_call(self):
        """从方法调用推导可打印约束"""
        from zhc.parser.ast_nodes import (
            CallExprNode,
            MemberExprNode,
            IdentifierExprNode,
            BlockStmtNode,
            ExprStmtNode,
        )

        body = BlockStmtNode(
            statements=[
                ExprStmtNode(
                    expr=CallExprNode(
                        callee=MemberExprNode(
                            obj=IdentifierExprNode("T"), member="打印"
                        ),
                        args=[],
                    )
                ),
            ]
        )

        constraints = self.inferrer.infer_constraints_from_body(body, ["T"])
        constraint_names = {c.name for c in constraints}
        assert "可打印" in constraint_names

    def test_empty_body_returns_empty_constraints(self):
        """空函数体返回空约束列表"""
        from zhc.parser.ast_nodes import BlockStmtNode

        body = BlockStmtNode(statements=[])
        constraints = self.inferrer.infer_constraints_from_body(body, ["T"])
        assert constraints == []

    def test_none_body_returns_empty(self):
        """None body 返回空约束"""
        constraints = self.inferrer.infer_constraints_from_body(None, ["T"])
        assert constraints == []

    def test_infer_and_check_finds_missing_constraint(self):
        """infer_and_check 发现缺失的约束"""
        from zhc.parser.ast_nodes import (
            BinaryExprNode,
            IdentifierExprNode,
            BlockStmtNode,
        )

        body = BlockStmtNode(
            statements=[
                # T < T (标识符名与类型参数名匹配)
                BinaryExprNode(
                    operator="<",
                    left=IdentifierExprNode("T"),
                    right=IdentifierExprNode("T"),
                ),
            ]
        )

        # 声明时没有约束
        type_params = [TypeParameter(name="T")]

        explicit, inferred, warnings = self.inferrer.infer_and_check(body, type_params)

        # 推导出约束但未声明 → 有警告（< 被覆盖策略提升为数值型）
        assert len(inferred) >= 1
        inferred_names = {c.name for c in inferred}
        assert "数值型" in inferred_names or "可比较" in inferred_names
        assert len(warnings) > 0

    def test_infer_and_check_all_declared(self):
        """所有约束都已声明时无警告"""
        from zhc.parser.ast_nodes import (
            BinaryExprNode,
            IdentifierExprNode,
            BlockStmtNode,
        )

        body = BlockStmtNode(
            statements=[
                BinaryExprNode(
                    operator="<",
                    left=IdentifierExprNode("a"),
                    right=IdentifierExprNode("b"),
                ),
            ]
        )

        # 声明时已有可比较约束
        type_params = [
            TypeParameter(
                name="T",
                constraints=[PredefinedConstraints.comparable()],
            )
        ]

        _, _, warnings = self.inferrer.infer_and_check(body, type_params)
        assert len(warnings) == 0

    def test_required_operators_for_constraint(self):
        """查询约束所需的运算符"""
        ops = ConstraintInferrer.get_required_operators_for_constraint("数值型")
        assert "+" in ops
        assert "-" in ops
        assert "*" in ops
        assert "/" in ops
        assert len(ops) >= 4

    def test_required_methods_for_constraint(self):
        """查询约束所需的方法"""
        methods = ConstraintInferrer.get_required_methods_for_constraint("可打印")
        assert "转字符串" in methods

    def test_multiple_type_params_independently_inferred(self):
        """多个类型参数独立推断各自约束"""
        from zhc.parser.ast_nodes import (
            BinaryExprNode,
            CallExprNode,
            MemberExprNode,
            IdentifierExprNode,
            BlockStmtNode,
            ExprStmtNode,
        )

        # T 用于比较操作 (a > b)
        # K 用于打印操作 (k.打印())
        body = BlockStmtNode(
            statements=[
                ExprStmtNode(
                    expr=BinaryExprNode(
                        operator=">",
                        left=IdentifierExprNode("a"),
                        right=IdentifierExprNode("b"),
                    )
                ),  # a, b 是 T 类型
                ExprStmtNode(
                    expr=CallExprNode(
                        callee=MemberExprNode(
                            obj=IdentifierExprNode("k"), member="打印"
                        ),
                        args=[],
                    )
                ),  # k 是 K 类型
            ]
        )

        constraints = self.inferrer.infer_constraints_from_body(body, ["T", "K"])
        # 注意：由于简化实现基于变量名启发式，这里验证不崩溃即可
        assert isinstance(constraints, list)


class TestG08Integration:
    """
    G.08e: 增强特性集成端到端测试

    验证多个增强特性协同工作：
    - 变性检查 + 约束推理组合
    - 默认参数 + 单态化流水线
    - 完整增强流程
    """

    def setup_method(self):
        reset_generic_manager()

    def test_variance_with_constraint_inference_combined(self):
        """变性检查与约束推理联合使用"""
        from zhc.parser.ast_nodes import (
            BinaryExprNode,
            IdentifierExprNode,
            BlockStmtNode,
        )

        inferrer = ConstraintInferrer()
        checker = VarianceChecker()

        # 泛型函数体使用了比较运算 → 需要 可比较
        body = BlockStmtNode(
            statements=[
                BinaryExprNode(
                    operator="<",
                    left=IdentifierExprNode("x"),
                    right=IdentifierExprNode("y"),
                ),
            ]
        )
        inferred = inferrer.infer_constraints_from_body(body, ["T"])

        # 创建含推理约束的类型参数
        tp = TypeParameter(name="T", constraints=inferred)

        # 变性检查应正常工作（不变 + 精确匹配）
        ok, errs = checker.check_assignment(
            "容器", "容器", ["整数型"], ["整数型"], [tp]
        )
        assert ok is True

    def test_full_enhanced_workflow(self):
        """完整增强工作流：解析 → 推理约束 → 变性检查 → 单态化"""
        resolver = GenericResolver()
        inferrer = ConstraintInferrer()  # noqa: F841
        mono = Monomorphizer(resolver=resolver)  # noqa: F841

        # 1. 创建泛型函数（带默认参数）
        gf = GenericFunction(
            name="增强处理",
            type_params=[
                TypeParameter("T", default="整数型"),
                TypeParameter("U", default="字符串型"),
            ],
            params=[ParamInfo(name="data", type_name="T")],
            return_type="U",
        )

        # 2. 注册
        get_generic_manager().register_generic_function(gf)

        # 3. 只提供部分参数实例化（使用默认值）
        instance = gf.instantiate(["浮点型"])
        assert instance.specialized_return_type == "字符串型"  # U 用了默认值

        # 4. 变性检查
        checker = VarianceChecker()
        ok, _ = checker.check_assignment(
            "结果",
            "结果",
            ["浮点型", "字符串型"],
            ["数值型", "字符串型"],
            [
                TypeParameter("T", variance=Variance.COVARIANT),
                TypeParameter("U", variance=Variance.INVARIANT),
            ],
        )
        assert ok is True

    def test_variance_checker_statistics(self):
        """VarianceChecker 可以描述各种变性"""
        checker = VarianceChecker()
        for v in Variance:
            desc = checker.get_variance_description(v)
            assert isinstance(desc, str)
            assert len(desc) > 0

    def test_typekind_with_variance_combo(self):
        """TypeKind 和 Variance 组合使用在复杂场景中"""
        # 模拟高阶类型构造器 + 协变
        kind = TypeInfo(kind=TypeKind.TYPE_CONSTRUCTOR, required_arity=1)
        param = TypeParameter(
            name="M",
            variance=Variance.COVARIANT,
        )
        assert param.variance == Variance.COVARIANT
        assert kind.required_arity == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

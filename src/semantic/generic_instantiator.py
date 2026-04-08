#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泛型实例化器 - Generic Instantiator

实现泛型的单态化（Monomorphization）：
1. 类型实例化：将泛型类型参数替换为具体类型
2. 函数实例化：生成具体版本的泛型函数
3. 约束检查：验证类型实参满足约束
4. 实例缓存：避免重复实例化

Phase 4 - Stage 2 - Task 11.1 Day 3

作者：ZHC 开发团队
日期：2026-04-08
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Set, Any, TYPE_CHECKING
from dataclasses import dataclass, field

# 导入泛型类型系统
from .generics import (
    TypeParameter,
    TypeConstraint,
    GenericType,
    GenericFunction,
    GenericTypeInstance,
    FunctionInstance,
    GenericManager,
    get_generic_manager,
    GenericError,
    TypeParameterCountError,
    ConstraintViolationError,
)

# 导入 AST 节点
from ..parser.ast_nodes import ASTNode

if TYPE_CHECKING:
    pass


@dataclass
class InstantiationContext:
    """
    实例化上下文

    跟踪实例化过程中的状态和依赖。
    """

    # 类型参数映射：形参名 -> 实参类型名
    type_mapping: Dict[str, str] = field(default_factory=dict)

    # 已实例化的类型
    instantiated_types: Set[str] = field(default_factory=set)

    # 已实例化的函数
    instantiated_functions: Set[str] = field(default_factory=set)

    # 实例化栈（用于检测循环依赖）
    instantiation_stack: List[str] = field(default_factory=list)

    # 错误收集
    errors: List[str] = field(default_factory=list)

    def push_type(self, type_name: str) -> bool:
        """压入类型到实例化栈"""
        if type_name in self.instantiation_stack:
            self.errors.append(
                f"检测到循环依赖: {' -> '.join(self.instantiation_stack)} -> {type_name}"
            )
            return False
        self.instantiation_stack.append(type_name)
        return True

    def pop_type(self) -> Optional[str]:
        """弹出类型从实例化栈"""
        if self.instantiation_stack:
            return self.instantiation_stack.pop()
        return None

    def is_instantiating(self, type_name: str) -> bool:
        """检查是否正在实例化某类型"""
        return type_name in self.instantiation_stack


class GenericInstantiator:
    """
    泛型实例化器

    负责将泛型类型和函数实例化为具体版本。
    """

    def __init__(self, manager: Optional[GenericManager] = None):
        """
        初始化实例化器

        Args:
            manager: 泛型管理器（默认使用全局单例）
        """
        self.manager = manager or get_generic_manager()

        # 类型实例缓存：键为 (泛型类型名, 类型实参元组)
        self._type_cache: Dict[Tuple[str, Tuple[str, ...]], GenericTypeInstance] = {}

        # 函数实例缓存：键为 (泛型函数名, 类型实参元组)
        self._function_cache: Dict[Tuple[str, Tuple[str, ...]], FunctionInstance] = {}

        # 实例化统计
        self._stats = {
            "type_instantiations": 0,
            "function_instantiations": 0,
            "cache_hits": 0,
            "constraint_checks": 0,
        }

    def instantiate_type(
        self,
        generic_type: GenericType,
        type_args: List[str],
        context: Optional[InstantiationContext] = None,
    ) -> GenericTypeInstance:
        """
        实例化泛型类型

        Args:
            generic_type: 泛型类型定义
            type_args: 类型实参列表
            context: 实例化上下文

        Returns:
            实例化后的具体类型

        Raises:
            TypeParameterCountError: 类型参数数量不匹配
            ConstraintViolationError: 类型不满足约束
        """
        context = context or InstantiationContext()

        # 1. 检查参数数量
        if len(type_args) != len(generic_type.type_params):
            raise TypeParameterCountError(
                f"泛型类型 '{generic_type.name}' 需要 {len(generic_type.type_params)} 个类型参数，"
                f"但提供了 {len(type_args)} 个"
            )

        # 2. 检查缓存
        cache_key = (generic_type.name, tuple(type_args))
        if cache_key in self._type_cache:
            self._stats["cache_hits"] += 1
            return self._type_cache[cache_key]

        # 3. 检查循环依赖
        if not context.push_type(generic_type.name):
            raise GenericError(context.errors[-1])

        try:
            # 4. 检查约束
            self._check_type_constraints(generic_type.type_params, type_args, context)

            # 5. 创建类型映射
            type_mapping = {
                param.name: arg
                for param, arg in zip(generic_type.type_params, type_args)
            }
            context.type_mapping.update(type_mapping)

            # 6. 实例化成员
            instantiated_members = self._instantiate_members(
                generic_type.members, type_mapping, context
            )

            # 7. 创建实例
            instance = GenericTypeInstance(
                generic_type=generic_type,
                type_args=type_args,
                members=instantiated_members,
            )

            # 8. 缓存实例
            self._type_cache[cache_key] = instance
            self._stats["type_instantiations"] += 1

            return instance

        finally:
            context.pop_type()

    def instantiate_function(
        self,
        generic_func: GenericFunction,
        type_args: List[str],
        context: Optional[InstantiationContext] = None,
    ) -> FunctionInstance:
        """
        实例化泛型函数

        Args:
            generic_func: 泛型函数定义
            type_args: 类型实参列表
            context: 实例化上下文

        Returns:
            实例化后的具体函数
        """
        context = context or InstantiationContext()

        # 1. 检查参数数量
        if len(type_args) != len(generic_func.type_params):
            raise TypeParameterCountError(
                f"泛型函数 '{generic_func.name}' 需要 {len(generic_func.type_params)} 个类型参数，"
                f"但提供了 {len(type_args)} 个"
            )

        # 2. 检查缓存
        cache_key = (generic_func.name, tuple(type_args))
        if cache_key in self._function_cache:
            self._stats["cache_hits"] += 1
            return self._function_cache[cache_key]

        # 3. 检查约束
        self._check_type_constraints(generic_func.type_params, type_args, context)

        # 4. 创建类型映射
        type_mapping = {
            param.name: arg for param, arg in zip(generic_func.type_params, type_args)
        }
        context.type_mapping.update(type_mapping)

        # 5. 实例化参数
        instantiated_params = self._instantiate_params(
            generic_func.params, type_mapping, context
        )

        # 6. 实例化返回类型
        instantiated_return = self._substitute_type(
            generic_func.return_type, type_mapping
        )

        # 7. 实例化函数体（如果需要）
        instantiated_body = None
        if generic_func.body:
            instantiated_body = self._instantiate_body(
                generic_func.body, type_mapping, context
            )

        # 8. 创建实例
        instance = FunctionInstance(
            generic_function=generic_func,
            type_args=type_args,
            specialized_params=instantiated_params,
            specialized_return_type=instantiated_return,
            specialized_body=instantiated_body,
        )

        # 9. 缓存实例
        self._function_cache[cache_key] = instance
        self._stats["function_instantiations"] += 1

        return instance

    def _check_type_constraints(
        self,
        type_params: List[TypeParameter],
        type_args: List[str],
        context: InstantiationContext,
    ) -> None:
        """
        检查类型实参是否满足约束

        Args:
            type_params: 类型参数列表
            type_args: 类型实参列表
            context: 实例化上下文

        Raises:
            ConstraintViolationError: 约束违反
        """
        for param, arg in zip(type_params, type_args):
            if not param.constraints:
                continue

            self._stats["constraint_checks"] += 1

            for constraint in param.constraints:
                if not self._check_constraint(arg, constraint):
                    raise ConstraintViolationError(
                        f"类型 '{arg}' 不满足约束 '{constraint.name}'"
                    )

    def _check_constraint(self, type_name: str, constraint: TypeConstraint) -> bool:
        """
        检查类型是否满足单个约束

        Args:
            type_name: 类型名
            constraint: 约束

        Returns:
            是否满足约束
        """
        # 基本类型的约束满足情况
        basic_types = {
            "整数型": {"可比较", "可相等", "可加", "数值型"},
            "浮点型": {"可比较", "可相等", "可加", "数值型"},
            "双精度型": {"可比较", "可相等", "可加", "数值型"},
            "字符型": {"可比较", "可相等"},
            "字符串型": {"可比较", "可相等"},
            "布尔型": {"可相等"},
        }

        # 检查基本类型
        if type_name in basic_types:
            return constraint.name in basic_types[type_name]

        # 自定义类型需要查询类型系统
        # TODO: 集成类型检查器进行完整检查
        return True

    def _instantiate_members(
        self,
        members: List[Any],
        type_mapping: Dict[str, str],
        context: InstantiationContext,
    ) -> List[Any]:
        """
        实例化类型成员

        Args:
            members: 成员列表
            type_mapping: 类型映射
            context: 实例化上下文

        Returns:
            实例化后的成员列表
        """
        from .generics import MemberInfo

        instantiated = []
        for member in members:
            if isinstance(member, MemberInfo):
                # 替换类型
                new_type = self._substitute_type(member.type_name, type_mapping)
                instantiated.append(
                    MemberInfo(
                        name=member.name,
                        type_name=new_type,
                        is_static=member.is_static,
                        is_const=member.is_const,
                    )
                )
            else:
                instantiated.append(member)

        return instantiated

    def _instantiate_params(
        self,
        params: List[Any],
        type_mapping: Dict[str, str],
        context: InstantiationContext,
    ) -> List[Any]:
        """
        实例化函数参数

        Args:
            params: 参数列表
            type_mapping: 类型映射
            context: 实例化上下文

        Returns:
            实例化后的参数列表
        """
        from .generics import ParamInfo

        instantiated = []
        for param in params:
            if isinstance(param, ParamInfo):
                new_type = self._substitute_type(param.type_name, type_mapping)
                instantiated.append(
                    ParamInfo(
                        name=param.name,
                        type_name=new_type,
                        is_reference=param.is_reference,
                        is_const=param.is_const,
                        default_value=param.default_value,
                    )
                )
            else:
                instantiated.append(param)

        return instantiated

    def _instantiate_body(
        self, body: ASTNode, type_mapping: Dict[str, str], context: InstantiationContext
    ) -> ASTNode:
        """
        实例化函数体

        Args:
            body: 函数体 AST
            type_mapping: 类型映射
            context: 实例化上下文

        Returns:
            实例化后的函数体
        """
        # TODO: 实现 AST 深拷贝和类型替换
        # 当前简化实现：返回原函数体
        return body

    def _substitute_type(self, type_name: str, type_mapping: Dict[str, str]) -> str:
        """
        替换类型名中的类型参数

        Args:
            type_name: 类型名（可能包含类型参数）
            type_mapping: 类型映射

        Returns:
            替换后的类型名
        """
        # 简单替换：直接替换类型参数名
        if type_name in type_mapping:
            return type_mapping[type_name]

        # 处理泛型类型：列表<T> -> 列表<整数型>
        # TODO: 实现更复杂的类型替换

        return type_name

    def get_statistics(self) -> Dict[str, Any]:
        """获取实例化统计信息"""
        return {
            **self._stats,
            "cached_types": len(self._type_cache),
            "cached_functions": len(self._function_cache),
        }

    def clear_cache(self) -> None:
        """清空实例缓存"""
        self._type_cache.clear()
        self._function_cache.clear()
        self._stats = {
            "type_instantiations": 0,
            "function_instantiations": 0,
            "cache_hits": 0,
            "constraint_checks": 0,
        }


# ===== 类型推导支持 =====


class GenericTypeInferrer:
    """
    泛型类型推导器

    从函数调用推导泛型类型参数。
    """

    def __init__(self, instantiator: GenericInstantiator):
        self.instantiator = instantiator

    def infer_type_arguments(
        self, generic_func: GenericFunction, arg_types: List[str]
    ) -> Optional[List[str]]:
        """
        从参数类型推导类型实参

        Args:
            generic_func: 泛型函数
            arg_types: 参数类型列表

        Returns:
            推导出的类型实参列表，失败返回 None
        """
        if len(arg_types) != len(generic_func.params):
            return None

        # 类型参数到实参的映射
        type_args: Dict[str, str] = {}

        # 遍历参数，收集类型映射
        for param, arg_type in zip(generic_func.params, arg_types):
            param_type = param.type_name

            # 如果参数类型是类型参数
            if self._is_type_parameter(param_type, generic_func.type_params):
                # 记录映射
                if param_type in type_args:
                    # 检查一致性
                    if type_args[param_type] != arg_type:
                        return None  # 类型冲突
                else:
                    type_args[param_type] = arg_type

        # 构建类型实参列表
        result = []
        for type_param in generic_func.type_params:
            if type_param.name in type_args:
                result.append(type_args[type_param.name])
            elif type_param.default:
                result.append(type_param.default)
            else:
                return None  # 无法推导

        return result

    def _is_type_parameter(
        self, type_name: str, type_params: List[TypeParameter]
    ) -> bool:
        """检查类型名是否是类型参数"""
        return any(p.name == type_name for p in type_params)


# ===== 模块级单例 =====

_instantiator: Optional[GenericInstantiator] = None


def get_instantiator() -> GenericInstantiator:
    """获取泛型实例化器单例"""
    global _instantiator
    if _instantiator is None:
        _instantiator = GenericInstantiator()
    return _instantiator


def reset_instantiator() -> None:
    """重置泛型实例化器"""
    global _instantiator
    _instantiator = None


# ===== 便捷函数 =====


def instantiate_generic_type(
    type_name: str, type_args: List[str]
) -> GenericTypeInstance:
    """
    实例化泛型类型

    Args:
        type_name: 泛型类型名
        type_args: 类型实参列表

    Returns:
        实例化后的类型
    """
    manager = get_generic_manager()
    instantiator = get_instantiator()

    generic_type = manager.get_generic_type(type_name)
    if generic_type is None:
        raise GenericError(f"泛型类型 '{type_name}' 未定义")

    return instantiator.instantiate_type(generic_type, type_args)


def instantiate_generic_function(
    func_name: str, type_args: List[str]
) -> FunctionInstance:
    """
    实例化泛型函数

    Args:
        func_name: 泛型函数名
        type_args: 类型实参列表

    Returns:
        实例化后的函数
    """
    manager = get_generic_manager()
    instantiator = get_instantiator()

    generic_funcs = manager.get_generic_functions(func_name)
    if not generic_funcs:
        raise GenericError(f"泛型函数 '{func_name}' 未定义")

    # 选择匹配的泛型函数
    for generic_func in generic_funcs:
        if len(generic_func.type_params) == len(type_args):
            return instantiator.instantiate_function(generic_func, type_args)

    raise TypeParameterCountError(
        f"泛型函数 '{func_name}' 没有匹配 {len(type_args)} 个类型参数的版本"
    )


# ===== 测试代码 =====

if __name__ == "__main__":
    from .generics import (
        create_generic_type,
        create_generic_function,
        TypeParameter,
        ParamInfo,
    )

    # 创建泛型类型
    print("=" * 70)
    print("测试 1: 泛型类型实例化")
    print("=" * 70)

    type_params = [TypeParameter(name="T", constraints=[])]

    generic_list = create_generic_type(name="列表", type_params=type_params, members=[])

    instantiator = GenericInstantiator()

    # 实例化为 列表<整数型>
    instance = instantiator.instantiate_type(generic_list, ["整数型"])
    print(f"实例化结果: {instance.name}")
    print(f"类型实参: {instance.type_args}")

    # 测试缓存
    instance2 = instantiator.instantiate_type(generic_list, ["整数型"])
    print(f"缓存命中: {instance is instance2}")

    # 创建泛型函数
    print("\n" + "=" * 70)
    print("测试 2: 泛型函数实例化")
    print("=" * 70)

    func_type_params = [TypeParameter(name="T", constraints=[])]

    generic_max = create_generic_function(
        name="最大值",
        type_params=func_type_params,
        params=[
            ParamInfo(name="a", type_name="T"),
            ParamInfo(name="b", type_name="T"),
        ],
        return_type="T",
    )

    # 实例化为 最大值<整数型>
    func_instance = instantiator.instantiate_function(generic_max, ["整数型"])
    print(f"实例化结果: {func_instance.name}")
    print(f"参数: {[(p.name, p.type_name) for p in func_instance.specialized_params]}")
    print(f"返回类型: {func_instance.specialized_return_type}")

    # 统计信息
    print("\n" + "=" * 70)
    print("测试 3: 实例化统计")
    print("=" * 70)
    stats = instantiator.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

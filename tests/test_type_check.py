# -*- coding: utf-8 -*-
"""
ZhC 反射 - 运行时类型检查测试

测试内容：
- TypeHierarchy: 类型层次结构查询
- TypeChecker: 类型兼容性检查
- TypeCast: 类型转换
- ReflectionTypeInfo 扩展方法
- 关键字映射
- IR Opcodes

作者：远
日期：2026-04-11
"""

import pytest
import sys
import os

# 确保 zhc 包可导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from zhc.reflection.type_info import (
    ReflectionTypeInfo,
    ReflectionFieldInfo,
    TypeRegistry,
)
from zhc.reflection.type_check import (
    TypeHierarchy,
    TypeChecker,
    is_type,
    is_subtype,
    implements_interface,
    type_equals,
    type_name,
    check_assignable,
    is_primitive,
)
from zhc.reflection.type_cast import (
    TypeCast,
    TypeCastError,
    safe_cast,
    dynamic_cast,
    require_type,
    cast_to_interface,
    try_cast,
    narrow_cast,
    widen_cast,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def clean_registry():
    """每个测试前后清空注册表"""
    TypeRegistry.clear()
    yield
    TypeRegistry.clear()


def _register_test_types():
    """注册测试用的类型层次"""
    # 基本类型
    TypeRegistry.register_primitive_types()

    # 动物 (基类)
    TypeRegistry.register(
        ReflectionTypeInfo(
            name="动物",
            size=16,
            is_class=True,
            base_class=None,
            interfaces=["可移动"],
            fields=[
                ReflectionFieldInfo(
                    name="名字", type_name="字符串型", offset=0, size=8, alignment=8
                ),
                ReflectionFieldInfo(
                    name="年龄", type_name="整数型", offset=8, size=4, alignment=4
                ),
            ],
        )
    )

    # 狗 继承 动物
    TypeRegistry.register(
        ReflectionTypeInfo(
            name="狗",
            size=24,
            is_class=True,
            base_class="动物",
            interfaces=["可训练"],
            fields=[
                ReflectionFieldInfo(
                    name="品种", type_name="字符串型", offset=16, size=8, alignment=8
                ),
            ],
        )
    )

    # 猫 继承 动物
    TypeRegistry.register(
        ReflectionTypeInfo(
            name="猫",
            size=20,
            is_class=True,
            base_class="动物",
            interfaces=[],
            fields=[
                ReflectionFieldInfo(
                    name="毛色", type_name="字符串型", offset=16, size=4, alignment=4
                ),
            ],
        )
    )

    # 导盲犬 继承 狗
    TypeRegistry.register(
        ReflectionTypeInfo(
            name="导盲犬",
            size=32,
            is_class=True,
            base_class="狗",
            interfaces=["可工作"],
            fields=[
                ReflectionFieldInfo(
                    name="等级", type_name="整数型", offset=24, size=4, alignment=4
                ),
            ],
        )
    )

    # 接口：可飞行
    TypeRegistry.register(
        ReflectionTypeInfo(
            name="可飞行",
            size=0,
            is_class=False,
            base_class=None,
            interfaces=[],
        )
    )

    # 鸟 继承 动物，实现 可飞行
    TypeRegistry.register(
        ReflectionTypeInfo(
            name="鸟",
            size=24,
            is_class=True,
            base_class="动物",
            interfaces=["可飞行", "可移动"],
            fields=[
                ReflectionFieldInfo(
                    name="翼展", type_name="浮点型", offset=16, size=4, alignment=4
                ),
            ],
        )
    )

    # 接口：可移动
    TypeRegistry.register(
        ReflectionTypeInfo(
            name="可移动",
            size=0,
            is_class=False,
            base_class=None,
            interfaces=[],
        )
    )

    # 接口：可训练
    TypeRegistry.register(
        ReflectionTypeInfo(
            name="可训练",
            size=0,
            is_class=False,
            base_class=None,
            interfaces=[],
        )
    )

    # 接口：可工作
    TypeRegistry.register(
        ReflectionTypeInfo(
            name="可工作",
            size=0,
            is_class=False,
            base_class=None,
            interfaces=[],
        )
    )


# =============================================================================
# ReflectionTypeInfo 扩展方法测试
# =============================================================================


class TestReflectionTypeInfoExtensions:
    """测试 ReflectionTypeInfo 新增的扩展方法"""

    def setup_method(self):
        _register_test_types()

    def test_get_ancestors_direct(self):
        """直接父类"""
        dog = TypeRegistry.lookup("狗")
        ancestors = dog.get_ancestors()
        assert ancestors == ["动物"]

    def test_get_ancestors_chain(self):
        """多级继承链"""
        guide_dog = TypeRegistry.lookup("导盲犬")
        ancestors = guide_dog.get_ancestors()
        assert ancestors == ["狗", "动物"]

    def test_get_ancestors_root(self):
        """根类型没有祖先"""
        animal = TypeRegistry.lookup("动物")
        ancestors = animal.get_ancestors()
        assert ancestors == []

    def test_implements_interface_direct(self):
        """直接实现接口"""
        dog = TypeRegistry.lookup("狗")
        assert dog.implements_interface("可训练") is True

    def test_implements_interface_inherited(self):
        """通过继承获得接口"""
        dog = TypeRegistry.lookup("狗")
        assert dog.implements_interface("可移动") is True  # 从 动物 继承

    def test_implements_interface_not(self):
        """未实现接口"""
        cat = TypeRegistry.lookup("猫")
        assert cat.implements_interface("可飞行") is False

    def test_get_mro(self):
        """方法解析顺序"""
        guide_dog = TypeRegistry.lookup("导盲犬")
        mro = guide_dog.get_mro()
        assert mro == ["导盲犬", "狗", "动物"]

    def test_is_instance_of_self(self):
        """自身是自身的实例"""
        dog = TypeRegistry.lookup("狗")
        assert dog.is_instance_of("狗") is True

    def test_is_instance_of_parent(self):
        """子类是父类的实例"""
        dog = TypeRegistry.lookup("狗")
        assert dog.is_instance_of("动物") is True

    def test_is_instance_of_interface(self):
        """实现了接口就是接口的实例"""
        bird = TypeRegistry.lookup("鸟")
        assert bird.is_instance_of("可飞行") is True

    def test_is_instance_of_grandparent(self):
        """孙类是祖类的实例"""
        guide_dog = TypeRegistry.lookup("导盲犬")
        assert guide_dog.is_instance_of("动物") is True

    def test_is_instance_of_not_related(self):
        """不相关的类型"""
        dog = TypeRegistry.lookup("狗")
        assert dog.is_instance_of("猫") is False


# =============================================================================
# TypeHierarchy 测试
# =============================================================================


class TestTypeHierarchy:
    """测试 TypeHierarchy 类型层次查询"""

    def setup_method(self):
        _register_test_types()

    def test_get_parent(self):
        assert TypeHierarchy.get_parent("狗") == "动物"
        assert TypeHierarchy.get_parent("动物") is None
        assert TypeHierarchy.get_parent("不存在") is None

    def test_get_children(self):
        children = TypeHierarchy.get_children("动物")
        assert set(children) == {"狗", "猫", "鸟"}

    def test_get_all_children(self):
        all_children = TypeHierarchy.get_all_children("动物")
        assert "导盲犬" in all_children
        assert "狗" in all_children

    def test_get_interfaces(self):
        ifaces = TypeHierarchy.get_interfaces("狗")
        assert "可训练" in ifaces

    def test_is_a_same(self):
        assert TypeHierarchy.is_a("狗", "狗") is True

    def test_is_a_parent(self):
        assert TypeHierarchy.is_a("狗", "动物") is True

    def test_is_a_grandparent(self):
        assert TypeHierarchy.is_a("导盲犬", "动物") is True

    def test_is_a_interface(self):
        assert TypeHierarchy.is_a("鸟", "可飞行") is True

    def test_is_a_inherited_interface(self):
        assert TypeHierarchy.is_a("狗", "可移动") is True

    def test_is_a_not_related(self):
        assert TypeHierarchy.is_a("狗", "猫") is False

    def test_is_a_unknown_type(self):
        assert TypeHierarchy.is_a("未知", "动物") is False

    def test_get_ancestors(self):
        ancestors = TypeHierarchy.get_ancestors("导盲犬")
        assert ancestors == ["狗", "动物"]

    def test_get_common_base(self):
        base = TypeHierarchy.get_common_base("狗", "猫")
        assert base == "动物"

    def test_get_common_base_grandchild(self):
        base = TypeHierarchy.get_common_base("导盲犬", "猫")
        assert base == "动物"

    def test_get_common_base_same(self):
        base = TypeHierarchy.get_common_base("狗", "狗")
        assert base == "狗"

    def test_get_common_base_none(self):
        base = TypeHierarchy.get_common_base("狗", "整数型")
        assert base is None


# =============================================================================
# TypeChecker 测试
# =============================================================================


class TestTypeChecker:
    """测试 TypeChecker 类型检查"""

    def setup_method(self):
        _register_test_types()
        self.checker = TypeChecker()

    def test_is_type_self(self):
        assert self.checker.is_type("狗", "狗") is True

    def test_is_type_parent(self):
        assert self.checker.is_type("狗", "动物") is True

    def test_is_type_not_related(self):
        assert self.checker.is_type("狗", "猫") is False

    def test_is_subtype(self):
        assert self.checker.is_subtype("导盲犬", "动物") is True

    def test_implements_interface(self):
        assert self.checker.implements_interface("鸟", "可飞行") is True

    def test_implements_interface_not(self):
        assert self.checker.implements_interface("猫", "可飞行") is False

    def test_type_equals_true(self):
        assert self.checker.type_equals("狗", "狗") is True

    def test_type_equals_false(self):
        assert self.checker.type_equals("狗", "猫") is False

    def test_check_assignable_child_to_parent(self):
        assert self.checker.check_assignable("动物", "狗") is True

    def test_check_assignable_not_compatible(self):
        assert self.checker.check_assignable("猫", "狗") is False

    def test_get_type_name(self):
        assert self.checker.get_type_name("狗") == "狗"
        assert self.checker.get_type_name("未知") == "未知"

    def test_is_primitive(self):
        assert self.checker.is_primitive("整数型") is True
        assert self.checker.is_primitive("狗") is False


# =============================================================================
# TypeChecker 公共 API 测试
# =============================================================================


class TestTypeCheckerAPI:
    """测试模块级公共 API"""

    def setup_method(self):
        _register_test_types()

    def test_is_type_api(self):
        assert is_type("狗", "动物") is True
        assert is_type("狗", "猫") is False

    def test_is_subtype_api(self):
        assert is_subtype("导盲犬", "动物") is True

    def test_implements_interface_api(self):
        assert implements_interface("鸟", "可飞行") is True

    def test_type_equals_api(self):
        assert type_equals("狗", "狗") is True
        assert type_equals("狗", "猫") is False

    def test_type_name_api(self):
        assert type_name("狗") == "狗"

    def test_check_assignable_api(self):
        assert check_assignable("动物", "狗") is True

    def test_is_primitive_api(self):
        assert is_primitive("整数型") is True
        assert is_primitive("狗") is False


# =============================================================================
# TypeCast 测试
# =============================================================================


class _ZhCMockObject:
    """模拟 ZhC 对象"""

    def __init__(self, type_name: str):
        self._zhc_type = type_name

    @property
    def __class__(self):
        """覆盖 __class__ 以返回带 _zhc_type_name 的模拟类"""
        mock_cls = type(self._zhc_type, (), {"_zhc_type_name": self._zhc_type})
        return mock_cls


class TestTypeCast:
    """测试 TypeCast 类型转换"""

    def setup_method(self):
        _register_test_types()
        self.caster = TypeCast()

    def test_safe_cast_compatible(self):
        obj = _ZhCMockObject("狗")
        result = self.caster.safe_cast(obj, "动物")
        assert result is obj

    def test_safe_cast_incompatible(self):
        obj = _ZhCMockObject("猫")
        result = self.caster.safe_cast(obj, "狗")
        assert result is None

    def test_safe_cast_none(self):
        result = self.caster.safe_cast(None, "狗")
        assert result is None

    def test_dynamic_cast_compatible(self):
        obj = _ZhCMockObject("狗")
        result = self.caster.dynamic_cast(obj, "动物")
        assert result is obj

    def test_dynamic_cast_incompatible(self):
        obj = _ZhCMockObject("猫")
        with pytest.raises(TypeCastError) as exc_info:
            self.caster.dynamic_cast(obj, "狗")
        assert "猫" in str(exc_info.value)
        assert "狗" in str(exc_info.value)

    def test_dynamic_cast_none(self):
        result = self.caster.dynamic_cast(None, "狗")
        assert result is None

    def test_require_type_match(self):
        obj = _ZhCMockObject("狗")
        result = self.caster.require_type(obj, "狗")
        assert result is obj

    def test_require_type_mismatch(self):
        obj = _ZhCMockObject("猫")
        with pytest.raises(TypeError):
            self.caster.require_type(obj, "狗")

    def test_require_type_none(self):
        with pytest.raises(TypeError):
            self.caster.require_type(None, "狗")

    def test_cast_to_interface(self):
        obj = _ZhCMockObject("鸟")
        result = self.caster.cast_to_interface(obj, "可飞行")
        assert result is obj

    def test_cast_to_interface_not(self):
        obj = _ZhCMockObject("猫")
        result = self.caster.cast_to_interface(obj, "可飞行")
        assert result is None

    def test_try_cast_success(self):
        obj = _ZhCMockObject("狗")
        result = self.caster.try_cast(obj, "动物")
        assert result.success is True
        assert result.result is obj

    def test_try_cast_failure(self):
        obj = _ZhCMockObject("猫")
        result = self.caster.try_cast(obj, "狗")
        assert result.success is False

    def test_narrow_cast(self):
        """窄化转换（向下转型）"""
        obj = _ZhCMockObject("导盲犬")
        result = self.caster.narrow_cast(obj, "狗")
        assert result is obj

    def test_narrow_cast_fail(self):
        obj = _ZhCMockObject("猫")
        result = self.caster.narrow_cast(obj, "狗")
        assert result is None

    def test_widen_cast(self):
        """宽化转换（向上转型）"""
        obj = _ZhCMockObject("狗")
        result = self.caster.widen_cast(obj, "动物")
        assert result is obj

    def test_widen_cast_fail(self):
        obj = _ZhCMockObject("猫")
        with pytest.raises(TypeCastError):
            self.caster.widen_cast(obj, "狗")


# =============================================================================
# TypeCast 公共 API 测试
# =============================================================================


class TestTypeCastAPI:
    """测试模块级类型转换 API"""

    def setup_method(self):
        _register_test_types()

    def test_safe_cast_api(self):
        obj = _ZhCMockObject("狗")
        assert safe_cast(obj, "动物") is obj

    def test_dynamic_cast_api(self):
        obj = _ZhCMockObject("狗")
        assert dynamic_cast(obj, "动物") is obj

    def test_require_type_api(self):
        obj = _ZhCMockObject("狗")
        assert require_type(obj, "狗") is obj

    def test_cast_to_interface_api(self):
        obj = _ZhCMockObject("鸟")
        assert cast_to_interface(obj, "可飞行") is obj

    def test_try_cast_api(self):
        obj = _ZhCMockObject("狗")
        result = try_cast(obj, "动物")
        assert result.success is True

    def test_narrow_cast_api(self):
        obj = _ZhCMockObject("导盲犬")
        assert narrow_cast(obj, "狗") is obj

    def test_widen_cast_api(self):
        obj = _ZhCMockObject("狗")
        assert widen_cast(obj, "动物") is obj


# =============================================================================
# TypeCastError 测试
# =============================================================================


class TestTypeCastError:
    """测试 TypeCastError 异常"""

    def test_error_properties(self):
        err = TypeCastError("猫", "狗")
        assert err.source_type == "猫"
        assert err.target_type == "狗"
        assert "猫" in str(err)
        assert "狗" in str(err)

    def test_error_custom_message(self):
        err = TypeCastError("猫", "狗", "自定义消息")
        assert str(err) == "自定义消息"


# =============================================================================
# 关键字映射测试
# =============================================================================


class TestTypeCheckKeywords:
    """测试类型检查关键字映射"""

    def test_keyword_is_type(self):
        from zhc.keywords import M

        assert M["是类型"] == "zhc_is_type"

    def test_keyword_is_subtype(self):
        from zhc.keywords import M

        assert M["是子类型"] == "zhc_is_subtype"

    def test_keyword_implements_interface(self):
        from zhc.keywords import M

        assert M["实现接口"] == "zhc_implements_interface"

    def test_keyword_type_equals(self):
        from zhc.keywords import M

        assert M["类型相同"] == "zhc_type_equals"

    def test_keyword_safe_cast(self):
        from zhc.keywords import M

        assert M["安全转换"] == "zhc_safe_cast"

    def test_keyword_dynamic_cast(self):
        from zhc.keywords import M

        assert M["动态转换"] == "zhc_dynamic_cast"

    def test_keyword_type_check(self):
        from zhc.keywords import M

        assert M["类型检查"] == "zhc_type_check"

    def test_keyword_assignable(self):
        from zhc.keywords import M

        assert M["可赋值"] == "zhc_check_assignable"

    def test_keyword_prefix(self):
        """带前缀的关键字也能正确映射"""
        from zhc.keywords import M

        assert M.get("中文是类型") == "zhc_is_type"


# =============================================================================
# IR Opcode 测试
# =============================================================================


class TestTypeCheckOpcodes:
    """测试类型检查 IR 操作码"""

    def test_is_type_opcode(self):
        from zhc.ir.opcodes import Opcode

        assert Opcode.IS_TYPE.value[0] == "is_type"
        assert Opcode.IS_TYPE.value[1] == "类型检查"

    def test_is_subtype_opcode(self):
        from zhc.ir.opcodes import Opcode

        assert Opcode.IS_SUBTYPE.value[0] == "is_subtype"

    def test_impl_iface_opcode(self):
        from zhc.ir.opcodes import Opcode

        assert Opcode.IMPL_IFACE.value[0] == "impl_iface"

    def test_type_equals_opcode(self):
        from zhc.ir.opcodes import Opcode

        assert Opcode.TYPE_EQUALS.value[0] == "type_equals"

    def test_safe_cast_opcode(self):
        from zhc.ir.opcodes import Opcode

        assert Opcode.SAFE_CAST.value[0] == "safe_cast"

    def test_dynamic_cast_opcode(self):
        from zhc.ir.opcodes import Opcode

        assert Opcode.DYNAMIC_CAST.value[0] == "dynamic_cast"

    def test_check_assignable_opcode(self):
        from zhc.ir.opcodes import Opcode

        assert Opcode.CHECK_ASSIGNABLE.value[0] == "check_assignable"

    def test_is_primitive_opcode(self):
        from zhc.ir.opcodes import Opcode

        assert Opcode.IS_PRIMITIVE.value[0] == "is_primitive"

    def test_all_opcodes_have_result(self):
        """所有类型检查 opcode 都产生结果"""
        from zhc.ir.opcodes import Opcode

        type_check_opcodes = [
            Opcode.IS_TYPE,
            Opcode.IS_SUBTYPE,
            Opcode.IMPL_IFACE,
            Opcode.TYPE_EQUALS,
            Opcode.SAFE_CAST,
            Opcode.DYNAMIC_CAST,
            Opcode.CHECK_ASSIGNABLE,
            Opcode.IS_PRIMITIVE,
        ]
        for opcode in type_check_opcodes:
            assert opcode.has_result is True, f"{opcode.name} should have result"

    def test_none_are_terminators(self):
        """类型检查 opcode 都不是终止指令"""
        from zhc.ir.opcodes import Opcode

        type_check_opcodes = [
            Opcode.IS_TYPE,
            Opcode.IS_SUBTYPE,
            Opcode.IMPL_IFACE,
            Opcode.TYPE_EQUALS,
            Opcode.SAFE_CAST,
            Opcode.DYNAMIC_CAST,
            Opcode.CHECK_ASSIGNABLE,
            Opcode.IS_PRIMITIVE,
        ]
        for opcode in type_check_opcodes:
            assert (
                opcode.is_terminator is False
            ), f"{opcode.name} should not be terminator"

    def test_all_category(self):
        """所有类型检查 opcode 都属于"类型检查"类别"""
        from zhc.ir.opcodes import Opcode

        type_check_opcodes = [
            Opcode.IS_TYPE,
            Opcode.IS_SUBTYPE,
            Opcode.IMPL_IFACE,
            Opcode.TYPE_EQUALS,
            Opcode.SAFE_CAST,
            Opcode.DYNAMIC_CAST,
            Opcode.CHECK_ASSIGNABLE,
            Opcode.IS_PRIMITIVE,
        ]
        for opcode in type_check_opcodes:
            assert (
                opcode.category == "类型检查"
            ), f"{opcode.name} category should be 类型检查"


# =============================================================================
# Backend 策略注册测试
# =============================================================================


class TestTypeCheckStrategies:
    """测试类型检查后端策略"""

    def test_register_strategies(self):
        """验证策略可以注册到工厂"""
        from zhc.backend.type_check_strategies import register_type_check_strategies
        from zhc.backend.llvm_instruction_strategy import InstructionStrategyFactory

        factory = InstructionStrategyFactory()
        register_type_check_strategies(factory)

        from zhc.ir.opcodes import Opcode

        type_check_opcodes = [
            Opcode.IS_TYPE,
            Opcode.IS_SUBTYPE,
            Opcode.IMPL_IFACE,
            Opcode.TYPE_EQUALS,
            Opcode.SAFE_CAST,
            Opcode.DYNAMIC_CAST,
            Opcode.CHECK_ASSIGNABLE,
            Opcode.IS_PRIMITIVE,
        ]
        for opcode in type_check_opcodes:
            strategy = factory.get_strategy(opcode)
            assert (
                strategy is not None
            ), f"Strategy for {opcode.name} should be registered"

    def test_strategy_classes_exist(self):
        """验证所有策略类都存在"""
        from zhc.backend.type_check_strategies import (
            IsTypeStrategy,
            IsSubtypeStrategy,
            ImplementsInterfaceStrategy,
            TypeEqualsStrategy,
            SafeCastStrategy,
            DynamicCastStrategy,
            CheckAssignableStrategy,
            IsPrimitiveStrategy,
        )

        strategies = [
            IsTypeStrategy,
            IsSubtypeStrategy,
            ImplementsInterfaceStrategy,
            TypeEqualsStrategy,
            SafeCastStrategy,
            DynamicCastStrategy,
            CheckAssignableStrategy,
            IsPrimitiveStrategy,
        ]
        for cls in strategies:
            instance = cls()
            assert instance.opcode is not None


# =============================================================================
# IR Generator 函数名映射测试
# =============================================================================


class TestTypeCheckIRMapping:
    """测试 IR 生成器中的函数名映射"""

    def test_function_name_mapping(self):
        """验证所有类型检查函数名映射正确"""
        from zhc.ir.ir_generator import IRGenerator

        gen = IRGenerator()

        # 调用内部方法验证映射
        assert gen._resolve_function_name("是类型") == "zhc_typecheck_is_type"
        assert gen._resolve_function_name("是子类型") == "zhc_typecheck_is_subtype"
        assert (
            gen._resolve_function_name("实现接口")
            == "zhc_typecheck_implements_interface"
        )
        assert gen._resolve_function_name("类型相同") == "zhc_typecheck_type_equals"
        assert gen._resolve_function_name("安全转换") == "zhc_typecheck_safe_cast"
        assert gen._resolve_function_name("动态转换") == "zhc_typecheck_dynamic_cast"
        assert gen._resolve_function_name("类型检查") == "zhc_typecheck_check"
        assert gen._resolve_function_name("可赋值") == "zhc_typecheck_assignable"

    def test_unknown_function_passthrough(self):
        """未知函数名应该直接通过"""
        from zhc.ir.ir_generator import IRGenerator

        gen = IRGenerator()
        assert gen._resolve_function_name("unknown_func") == "unknown_func"

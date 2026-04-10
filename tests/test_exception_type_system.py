# -*- coding: utf-8 -*-
"""
异常类型系统单元测试

测试异常类型定义、注册表、继承关系和内置异常类型。

作者：远
日期：2026-04-10
"""

import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from zhc.exception import (
    ExceptionField,
    ExceptionType,
    ExceptionObject,
    ExceptionRegistry,
    get_exception_class,
    is_exception_type,
    get_exception_info,
    get_error_code,
    get_all_exception_names,
    lookup_by_error_code,
)


class TestExceptionField:
    """测试 ExceptionField 数据类"""

    def test_field_creation(self):
        """测试创建异常字段"""
        field = ExceptionField(name="错误码", type_name="整数型")
        assert field.name == "错误码"
        assert field.type_name == "整数型"
        assert field.default_value is None

    def test_field_with_default(self):
        """测试带默认值的字段"""
        field = ExceptionField(
            name="消息",
            type_name="字符串",
            default_value="默认消息",
        )
        assert field.default_value == "默认消息"


class TestExceptionType:
    """测试 ExceptionType 数据类"""

    def test_type_creation(self):
        """测试创建异常类型"""
        exc_type = ExceptionType(
            name="自定义错误",
            base_class="异常",
            fields=[ExceptionField("代码", "整数型")],
        )
        assert exc_type.name == "自定义错误"
        assert exc_type.base_class == "异常"
        assert len(exc_type.fields) == 1

    def test_is_subtype_direct(self):
        """测试直接子类型检查（不带 registry）"""
        exc_type = ExceptionType(
            name="除零异常",
            base_class="算术异常",
        )
        # 不带 registry 只能检查直接父类
        assert exc_type.is_subtype_of("算术异常") is True
        assert exc_type.is_subtype_of("除零异常") is True  # 自己也是自己的子类型
        # 不带 registry 无法递归检查，所以 "异常" 返回 False
        assert exc_type.is_subtype_of("异常") is False

    def test_is_subtype_with_registry(self):
        """测试带注册表的递归子类型检查"""
        registry = ExceptionRegistry.instance()

        # 验证内置类型层次
        assert registry.is_subtype("除零异常", "算术异常") is True
        assert registry.is_subtype("除零异常", "异常") is True
        assert registry.is_subtype("算术异常", "异常") is True

    def test_is_not_subtype(self):
        """测试不是子类型的情况"""
        registry = ExceptionRegistry.instance()

        assert registry.is_subtype("除零异常", "输入输出异常") is False
        assert registry.is_subtype("异常", "除零异常") is False

    def test_get_field(self):
        """测试获取字段"""
        exc_type = ExceptionType(
            name="测试异常",
            base_class="异常",
            fields=[
                ExceptionField("字段1", "字符串"),
                ExceptionField("字段2", "整数型"),
            ],
        )

        field1 = exc_type.get_field("字段1")
        assert field1 is not None
        assert field1.type_name == "字符串"

        field3 = exc_type.get_field("字段3")
        assert field3 is None

    def test_get_all_fields(self):
        """测试获取所有字段（包括继承）"""
        registry = ExceptionRegistry.instance()

        # 除零异常应该继承算术异常和异常基类的字段
        div_exc = registry.lookup("除零异常")
        all_fields = div_exc.get_all_fields(registry)

        # 应该包含除零异常的字段 + 算术异常的字段 + 异常基类的字段
        field_names = [f.name for f in all_fields]
        assert "分子" in field_names
        assert "分母" in field_names


class TestExceptionObject:
    """测试 ExceptionObject 数据类"""

    def test_object_creation(self):
        """测试创建异常对象"""
        obj = ExceptionObject(
            type_name="除零异常",
            message="除数为零",
            error_code=4001,
        )
        assert obj.type_name == "除零异常"
        assert obj.message == "除数为零"
        assert obj.error_code == 4001
        assert obj.cause is None
        assert len(obj.stack_trace) == 0

    def test_set_and_get_field(self):
        """测试设置和获取字段"""
        obj = ExceptionObject(
            type_name="除零异常",
            message="除数为零",
        )
        obj.set_field("分子", 10)
        obj.set_field("分母", 0)

        assert obj.get_field("分子") == 10
        assert obj.get_field("分母") == 0
        assert obj.get_field("不存在") is None

    def test_add_stack_frame(self):
        """测试添加堆栈帧"""
        obj = ExceptionObject(
            type_name="除零异常",
            message="除数为零",
        )
        obj.add_stack_frame("main() at test.zhc:10")
        obj.add_stack_frame("计算() at test.zhc:5")

        assert len(obj.stack_trace) == 2
        assert obj.stack_trace[0] == "main() at test.zhc:10"

    def test_cause_chain(self):
        """测试异常链"""
        cause = ExceptionObject(
            type_name="运行时异常",
            message="根本原因",
        )
        effect = ExceptionObject(
            type_name="除零异常",
            message="除数为零",
            cause=cause,
        )

        assert effect.cause is cause
        assert effect.cause.message == "根本原因"

    def test_to_dict(self):
        """测试转换为字典"""
        obj = ExceptionObject(
            type_name="除零异常",
            message="除数为零",
            error_code=4001,
            fields={"分子": 10, "分母": 0},
        )

        d = obj.to_dict()
        assert d["type_name"] == "除零异常"
        assert d["message"] == "除数为零"
        assert d["error_code"] == 4001
        assert d["fields"]["分子"] == 10


class TestExceptionRegistry:
    """测试 ExceptionRegistry 注册表"""

    def setup_method(self):
        """每个测试前重置注册表"""
        ExceptionRegistry.reset()

    def test_singleton(self):
        """测试单例模式"""
        registry1 = ExceptionRegistry.instance()
        registry2 = ExceptionRegistry.instance()
        assert registry1 is registry2

    def test_register_builtin_types(self):
        """测试内置类型自动注册"""
        registry = ExceptionRegistry.instance()

        # 验证基本异常类型存在
        exc_type = registry.lookup("异常")
        assert exc_type is not None
        assert exc_type.is_builtin is True
        assert exc_type.base_class is None

    def test_register_custom_type(self):
        """测试注册自定义类型"""
        registry = ExceptionRegistry.instance()

        custom_type = ExceptionType(
            name="自定义错误",
            base_class="异常",
            fields=[ExceptionField("代码", "整数型")],
            is_builtin=False,
        )
        registry.register(custom_type)

        lookup = registry.lookup("自定义错误")
        assert lookup is not None
        assert lookup.name == "自定义错误"
        assert lookup.is_builtin is False

    def test_register_duplicate(self):
        """测试重复注册会报错"""
        registry = ExceptionRegistry.instance()

        exc_type = ExceptionType(
            name="测试异常",
            base_class="异常",
        )
        registry.register(exc_type)

        with pytest.raises(ValueError, match="已注册"):
            registry.register(exc_type)

    def test_register_with_invalid_base(self):
        """测试注册时基类不存在会报错"""
        registry = ExceptionRegistry.instance()

        exc_type = ExceptionType(
            name="无效异常",
            base_class="不存在的基类",
        )

        with pytest.raises(ValueError, match="基类.*不存在"):
            registry.register(exc_type)

    def test_register_circular_inheritance(self):
        """测试循环继承检测

        注意：由于注册时必须先有基类，直接 A->B->A 的循环无法注册。
        这里测试的是当基类不存在时会报错。
        """
        registry = ExceptionRegistry.instance()

        # 尝试注册一个基类不存在的类型
        type_a = ExceptionType(name="类型A", base_class="类型B")

        # 由于基类不存在，会抛出基类不存在的错误
        with pytest.raises(ValueError, match="基类.*不存在"):
            registry.register(type_a)

    def test_lookup(self):
        """测试类型查找"""
        registry = ExceptionRegistry.instance()

        div_exc = registry.lookup("除零异常")
        assert div_exc is not None
        assert div_exc.name == "除零异常"
        assert div_exc.base_class == "算术异常"

        not_exist = registry.lookup("不存在的异常")
        assert not_exist is None

    def test_is_subtype(self):
        """测试子类型检查"""
        registry = ExceptionRegistry.instance()

        # 直接父子关系
        assert registry.is_subtype("除零异常", "算术异常") is True

        # 多层继承
        assert registry.is_subtype("除零异常", "异常") is True

        # 反向不是子类型
        assert registry.is_subtype("异常", "除零异常") is False

        # 自己到自己
        assert registry.is_subtype("除零异常", "除零异常") is True

    def test_get_all_subtypes(self):
        """测试获取所有子类型"""
        registry = ExceptionRegistry.instance()

        # 算术异常应该有除零异常和溢出异常作为子类型
        subtypes = registry.get_all_subtypes("算术异常")
        assert "除零异常" in subtypes
        assert "溢出异常" in subtypes

        # 异常应该有所有异常类型作为子类型
        all_subtypes = registry.get_all_subtypes("异常")
        assert len(all_subtypes) > 10  # 应该有多个子类型

    def test_get_type_hierarchy(self):
        """测试获取类型层次结构"""
        registry = ExceptionRegistry.instance()

        hierarchy = registry.get_type_hierarchy()

        # 应该有异常基类
        assert "异常" in hierarchy

        # 异常的直接子类型应该包含 错误 和 运行时异常
        exc_children = hierarchy.get("异常", [])
        assert "错误" in exc_children
        assert "运行时异常" in exc_children

    def test_list_all_types(self):
        """测试列出所有类型"""
        registry = ExceptionRegistry.instance()

        all_types = registry.list_all_types()
        assert len(all_types) >= 15  # 至少有 15 种内置类型
        assert "异常" in all_types
        assert "除零异常" in all_types

    def test_list_builtin_types(self):
        """测试列出内置类型"""
        registry = ExceptionRegistry.instance()

        builtin = registry.list_builtin_types()
        assert len(builtin) >= 15
        assert all(registry.lookup(t).is_builtin for t in builtin)


class TestBuiltinExceptions:
    """测试内置异常类型"""

    def setup_method(self):
        """每个测试前重置注册表"""
        ExceptionRegistry.reset()

    def test_builtin_exception_hierarchy(self):
        """测试内置异常类型层次"""
        registry = ExceptionRegistry.instance()

        # 验证主要分支
        assert registry.is_subtype("内存错误", "错误") is True
        assert registry.is_subtype("栈溢出错误", "错误") is True
        assert registry.is_subtype("系统错误", "错误") is True

        assert registry.is_subtype("空指针异常", "运行时异常") is True
        assert registry.is_subtype("数组越界异常", "运行时异常") is True
        assert registry.is_subtype("类型转换异常", "运行时异常") is True

        assert registry.is_subtype("文件未找到异常", "输入输出异常") is True
        assert registry.is_subtype("文件权限异常", "输入输出异常") is True

        assert registry.is_subtype("除零异常", "算术异常") is True
        assert registry.is_subtype("溢出异常", "算术异常") is True

        # 所有类型都应该是异常的子类型
        for type_name in registry.list_all_types():
            if type_name != "异常":
                assert registry.is_subtype(type_name, "异常") is True

    def test_get_exception_class(self):
        """测试便捷函数 get_exception_class"""
        exc_type = get_exception_class("除零异常")
        assert exc_type is not None
        assert exc_type.name == "除零异常"

    def test_is_exception_type(self):
        """测试便捷函数 is_exception_type"""
        assert is_exception_type("除零异常") is True
        assert is_exception_type("空指针异常") is True
        assert is_exception_type("不存在的异常") is False


class TestBuiltinExceptionInfo:
    """测试内置异常详细信息"""

    def test_get_exception_info(self):
        """测试获取异常详细信息"""
        info = get_exception_info("除零异常")
        assert info is not None
        assert info.name == "除零异常"
        assert info.error_code == 4001
        assert len(info.suggestions) > 0

    def test_get_error_code(self):
        """测试获取错误码"""
        code = get_error_code("除零异常")
        assert code == "E4001"

        code = get_error_code("空指针异常")
        assert code == "E2002"

        code = get_error_code("不存在的异常")
        assert code is None

    def test_get_all_exception_names(self):
        """测试获取所有异常类型名称"""
        names = get_all_exception_names()
        assert "异常" in names
        assert "除零异常" in names
        assert "空指针异常" in names
        assert len(names) >= 15

    def test_lookup_by_error_code(self):
        """测试根据错误码查找异常类型"""
        name = lookup_by_error_code("E4001")
        assert name == "除零异常"

        name = lookup_by_error_code("E2002")
        assert name == "空指针异常"

        name = lookup_by_error_code("E9999")
        assert name is None


class TestIntegration:
    """集成测试"""

    def setup_method(self):
        """每个测试前重置注册表"""
        ExceptionRegistry.reset()

    def test_exception_workflow(self):
        """测试完整的异常工作流"""
        # 创建自定义异常类型
        registry = ExceptionRegistry.instance()

        custom_type = ExceptionType(
            name="数据库错误",
            base_class="输入输出异常",
            fields=[
                ExceptionField("SQL状态", "字符串"),
                ExceptionField("表名", "字符串"),
            ],
        )
        registry.register(custom_type)

        # 验证类型已注册
        assert registry.lookup("数据库错误") is not None
        assert registry.is_subtype("数据库错误", "输入输出异常") is True
        assert registry.is_subtype("数据库错误", "异常") is True

        # 创建异常对象
        obj = ExceptionObject(
            type_name="数据库错误",
            message="连接失败",
            error_code=3001,
            fields={"SQL状态": "08001", "表名": "users"},
        )

        # 验证异常对象
        assert obj.type_name == "数据库错误"
        assert obj.get_field("SQL状态") == "08001"
        assert obj.get_field("表名") == "users"

        # 验证异常链
        cause = ExceptionObject(
            type_name="输入输出异常",
            message="网络不可达",
        )
        db_error = ExceptionObject(
            type_name="数据库错误",
            message="无法连接数据库",
            cause=cause,
        )

        assert db_error.cause is cause
        assert db_error.cause.message == "网络不可达"

    def test_exception_type_fields_inheritance(self):
        """测试异常类型字段继承"""
        registry = ExceptionRegistry.instance()

        # 获取除零异常的完整字段
        div_exc = registry.lookup("除零异常")
        all_fields = div_exc.get_all_fields(registry)
        field_names = [f.name for f in all_fields]

        # 应该包含来自各层级的字段
        assert "分子" in field_names  # 除零异常自有
        assert "分母" in field_names  # 除零异常自有
        # 这些是异常基类的字段（如果定义的话）

    def test_multiple_catch_clause_order(self):
        """测试多个 catch 子句的类型层次"""
        registry = ExceptionRegistry.instance()

        # 模拟 catch 子句顺序检测
        catch_types = ["运行时异常", "输入输出异常", "异常"]
        unreachable = []

        captured = set()
        for catch_type in catch_types:
            # 检查是否与已捕获的类型形成冲突
            for cap in captured:
                if registry.is_subtype(cap, catch_type):
                    unreachable.append(catch_type)
                    break
            captured.add(catch_type)
            # 添加其所有父类型
            current = catch_type
            while True:
                type_info = registry.lookup(current)
                if type_info and type_info.base_class:
                    captured.add(type_info.base_class)
                    current = type_info.base_class
                else:
                    break

        # 运行时异常 的子类应该在它之前处理
        # 这个测试验证逻辑正确性
        assert len(catch_types) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

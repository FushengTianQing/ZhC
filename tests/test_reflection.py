#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反射模块综合测试

测试覆盖：
1. 核心数据结构（ReflectionTypeInfo, ReflectionFieldInfo, ReflectionMethodInfo）
2. 类型注册表（TypeRegistry）
3. 类型元数据生成器（TypeMetadataGenerator）
4. Keywords 映射
5. IR 操作码
6. C 运行时头文件常量

作者：远
日期：2026-04-11
"""

from zhc.reflection.type_info import (
    ReflectionFieldInfo,
    ReflectionMethodInfo,
    ReflectionTypeInfo,
    TypeRegistry,
    get_type_info,
    get_type_name,
    get_type_size,
    register_type,
)
from zhc.reflection.metadata import (
    TypeMetadataGenerator,
    ReflectionMetadataCollector,
)
from zhc.keywords import M as KEYWORDS
from zhc.ir.opcodes import Opcode


# ============================================================================
# 核心数据结构测试
# ============================================================================


class TestReflectionFieldInfo:
    """测试 ReflectionFieldInfo"""

    def test_creation(self):
        field = ReflectionFieldInfo(
            name="年龄", type_name="整数型", offset=0, size=4, alignment=4
        )
        assert field.name == "年龄"
        assert field.type_name == "整数型"
        assert field.offset == 0
        assert field.size == 4
        assert field.is_public is True
        assert field.is_static is False
        assert field.is_const is False

    def test_to_dict(self):
        field = ReflectionFieldInfo(
            name="名称", type_name="字符串型", offset=0, size=8, alignment=8
        )
        d = field.to_dict()
        assert d["name"] == "名称"
        assert d["type"] == "字符串型"
        assert d["offset"] == 0
        assert d["size"] == 8

    def test_from_dict(self):
        data = {"name": "价格", "type": "浮点型", "offset": 8, "size": 4}
        field = ReflectionFieldInfo.from_dict(data)
        assert field.name == "价格"
        assert field.type_name == "浮点型"
        assert field.offset == 8

    def test_roundtrip(self):
        field = ReflectionFieldInfo(
            name="x",
            type_name="整数型",
            offset=0,
            size=4,
            alignment=4,
            is_public=True,
            is_static=True,
            is_const=True,
        )
        d = field.to_dict()
        field2 = ReflectionFieldInfo.from_dict(d)
        assert field2.name == field.name
        assert field2.type_name == field.type_name
        assert field2.offset == field.offset
        assert field2.size == field.size
        assert field2.is_public == field.is_public
        assert field2.is_static == field.is_static
        assert field2.is_const == field.is_const


class TestReflectionMethodInfo:
    """测试 ReflectionMethodInfo"""

    def test_creation(self):
        method = ReflectionMethodInfo(
            name="叫声",
            return_type="空型",
            params=[{"name": "volume", "type": "整数型"}],
        )
        assert method.name == "叫声"
        assert method.return_type == "空型"
        assert len(method.params) == 1
        assert method.is_static is False
        assert method.is_virtual is False

    def test_to_dict(self):
        method = ReflectionMethodInfo(
            name="计算",
            return_type="整数型",
            params=[{"name": "x", "type": "整数型"}, {"name": "y", "type": "整数型"}],
            is_static=True,
        )
        d = method.to_dict()
        assert d["name"] == "计算"
        assert d["return_type"] == "整数型"
        assert len(d["params"]) == 2
        assert d["is_static"] is True

    def test_from_dict(self):
        data = {
            "name": "run",
            "return_type": "空型",
            "params": [],
            "is_virtual": True,
            "vtable_index": 3,
        }
        method = ReflectionMethodInfo.from_dict(data)
        assert method.name == "run"
        assert method.is_virtual is True
        assert method.vtable_index == 3


class TestReflectionTypeInfo:
    """测试 ReflectionTypeInfo"""

    def test_creation_primitive(self):
        info = ReflectionTypeInfo(name="整数型", size=4, alignment=4, is_primitive=True)
        assert info.name == "整数型"
        assert info.size == 4
        assert info.is_primitive is True
        assert info.is_class is False
        assert info.is_struct is False

    def test_creation_struct(self):
        fields = [
            ReflectionFieldInfo(name="x", type_name="整数型", offset=0, size=4),
            ReflectionFieldInfo(name="y", type_name="整数型", offset=4, size=4),
        ]
        info = ReflectionTypeInfo(
            name="Point",
            size=8,
            alignment=4,
            is_struct=True,
            fields=fields,
        )
        assert info.name == "Point"
        assert info.size == 8
        assert len(info.fields) == 2

    def test_get_field(self):
        fields = [
            ReflectionFieldInfo(name="年龄", type_name="整数型", offset=0, size=4),
            ReflectionFieldInfo(name="名称", type_name="字符串型", offset=8, size=8),
        ]
        info = ReflectionTypeInfo(name="Person", size=16, alignment=8, fields=fields)

        field = info.get_field("名称")
        assert field is not None
        assert field.name == "名称"
        assert field.type_name == "字符串型"

        assert info.get_field("不存在") is None

    def test_get_method(self):
        methods = [
            ReflectionMethodInfo(name="叫声", return_type="空型"),
            ReflectionMethodInfo(name="获取名称", return_type="字符串型"),
        ]
        info = ReflectionTypeInfo(name="动物", size=16, alignment=8, methods=methods)

        method = info.get_method("叫声")
        assert method is not None
        assert method.name == "叫声"

        assert info.get_method("不存在") is None

    def test_get_field_names(self):
        fields = [
            ReflectionFieldInfo(name="x", type_name="整数型", offset=0, size=4),
            ReflectionFieldInfo(name="y", type_name="浮点型", offset=4, size=4),
        ]
        info = ReflectionTypeInfo(name="Vec2", size=8, alignment=4, fields=fields)
        assert info.get_field_names() == ["x", "y"]

    def test_get_method_names(self):
        methods = [
            ReflectionMethodInfo(name="add", return_type="空型"),
            ReflectionMethodInfo(name="sub", return_type="空型"),
        ]
        info = ReflectionTypeInfo(name="Calc", size=0, alignment=0, methods=methods)
        assert info.get_method_names() == ["add", "sub"]

    def test_to_dict(self):
        fields = [ReflectionFieldInfo(name="x", type_name="整数型", offset=0, size=4)]
        info = ReflectionTypeInfo(
            name="Simple",
            size=4,
            alignment=4,
            is_struct=True,
            fields=fields,
            base_class="Base",
        )
        d = info.to_dict()
        assert d["name"] == "Simple"
        assert d["size"] == 4
        assert d["is_struct"] is True
        assert d["base_class"] == "Base"
        assert len(d["fields"]) == 1

    def test_from_dict(self):
        data = {
            "name": "Dog",
            "size": 24,
            "alignment": 8,
            "is_class": True,
            "base_class": "Animal",
            "fields": [{"name": "age", "type": "整数型", "offset": 16, "size": 4}],
            "methods": [{"name": "bark", "return_type": "空型", "params": []}],
        }
        info = ReflectionTypeInfo.from_dict(data)
        assert info.name == "Dog"
        assert info.is_class is True
        assert info.base_class == "Animal"
        assert len(info.fields) == 1
        assert info.fields[0].name == "age"
        assert len(info.methods) == 1

    def test_is_assignable_from(self):
        # 创建继承链: Animal -> Dog
        animal = ReflectionTypeInfo(name="Animal", size=16, alignment=8)
        dog = ReflectionTypeInfo(name="Dog", size=24, alignment=8, base_class="Animal")

        TypeRegistry.clear()
        TypeRegistry.register(animal)
        TypeRegistry.register(dog)

        # Dog 是 Animal 的子类
        assert animal.is_assignable_from(dog) is True
        # Animal 不是 Dog 的子类
        assert dog.is_assignable_from(animal) is False
        # 同类型
        assert animal.is_assignable_from(animal) is True

        TypeRegistry.clear()


# ============================================================================
# 类型注册表测试
# ============================================================================


class TestTypeRegistry:
    """测试 TypeRegistry"""

    def setup_method(self):
        """每个测试前清空注册表"""
        TypeRegistry.clear()

    def test_register_and_lookup(self):
        info = ReflectionTypeInfo(name="TestType", size=8, alignment=4)
        TypeRegistry.register(info)

        result = TypeRegistry.lookup("TestType")
        assert result is not None
        assert result.name == "TestType"

    def test_lookup_not_found(self):
        assert TypeRegistry.lookup("不存在") is None

    def test_is_registered(self):
        info = ReflectionTypeInfo(name="MyType", size=4, alignment=4)
        TypeRegistry.register(info)

        assert TypeRegistry.is_registered("MyType") is True
        assert TypeRegistry.is_registered("OtherType") is False

    def test_get_all_types(self):
        for name in ["TypeA", "TypeB", "TypeC"]:
            TypeRegistry.register(ReflectionTypeInfo(name=name, size=4, alignment=4))

        all_types = TypeRegistry.get_all_types()
        assert len(all_types) == 3
        names = {t.name for t in all_types}
        assert names == {"TypeA", "TypeB", "TypeC"}

    def test_get_subclasses(self):
        base = ReflectionTypeInfo(name="Base", size=8, alignment=4)
        sub1 = ReflectionTypeInfo(name="Sub1", size=12, alignment=4, base_class="Base")
        sub2 = ReflectionTypeInfo(name="Sub2", size=16, alignment=4, base_class="Base")
        unrelated = ReflectionTypeInfo(name="Other", size=4, alignment=4)

        for t in [base, sub1, sub2, unrelated]:
            TypeRegistry.register(t)

        subs = TypeRegistry.get_subclasses("Base")
        assert len(subs) == 2
        sub_names = {s.name for s in subs}
        assert sub_names == {"Sub1", "Sub2"}

    def test_get_all_subclasses_recursive(self):
        base = ReflectionTypeInfo(name="Base", size=8, alignment=4)
        sub1 = ReflectionTypeInfo(name="Sub1", size=12, alignment=4, base_class="Base")
        sub1_1 = ReflectionTypeInfo(
            name="Sub1_1", size=16, alignment=4, base_class="Sub1"
        )

        for t in [base, sub1, sub1_1]:
            TypeRegistry.register(t)

        all_subs = TypeRegistry.get_all_subclasses("Base")
        assert len(all_subs) == 2
        sub_names = {s.name for s in all_subs}
        assert sub_names == {"Sub1", "Sub1_1"}

    def test_register_primitive_types(self):
        TypeRegistry.register_primitive_types()

        assert TypeRegistry.is_registered("整数型") is True
        assert TypeRegistry.is_registered("字符型") is True
        assert TypeRegistry.is_registered("浮点型") is True
        assert TypeRegistry.is_registered("双精度浮点型") is True
        assert TypeRegistry.is_registered("逻辑型") is True

    def test_clear(self):
        TypeRegistry.register(ReflectionTypeInfo(name="Temp", size=4, alignment=4))
        assert len(TypeRegistry.get_all_types()) == 1
        TypeRegistry.clear()
        assert len(TypeRegistry.get_all_types()) == 0


# ============================================================================
# 公共 API 测试
# ============================================================================


class TestPublicAPI:
    """测试公共 API 函数"""

    def setup_method(self):
        TypeRegistry.clear()

    def test_register_type(self):
        info = register_type("MyStruct", size=16, alignment=8, is_struct=True)
        assert info.name == "MyStruct"
        assert info.size == 16
        assert TypeRegistry.is_registered("MyStruct") is True

    def test_register_type_with_fields(self):
        fields = [
            ReflectionFieldInfo(name="x", type_name="整数型", offset=0, size=4),
            ReflectionFieldInfo(name="y", type_name="整数型", offset=4, size=4),
        ]
        info = register_type(
            "Point", size=8, alignment=4, is_struct=True, fields=fields
        )
        assert len(info.fields) == 2

    def test_get_type_info(self):
        register_type("TestType", size=32, alignment=8)
        info = get_type_info("TestType")
        assert info is not None
        assert info.size == 32

    def test_get_type_name(self):
        register_type("动物", size=16, alignment=8)
        assert get_type_name("动物") == "动物"
        assert get_type_name("不存在") == "不存在"

    def test_get_type_size(self):
        register_type("大小测试", size=64, alignment=8)
        assert get_type_size("大小测试") == 64
        assert get_type_size("不存在") == 0


# ============================================================================
# 类型元数据生成器测试
# ============================================================================


class TestTypeMetadataGenerator:
    """测试 TypeMetadataGenerator"""

    def test_register_struct(self):
        gen = TypeMetadataGenerator(target_platform="macos")
        info = gen.register_struct(
            "Point",
            [("x", "整数型"), ("y", "整数型")],
        )
        assert info.name == "Point"
        assert info.is_struct is True
        assert len(info.fields) == 2
        assert info.fields[0].name == "x"
        assert info.fields[0].type_name == "整数型"
        assert info.fields[0].offset == 0
        assert info.fields[1].name == "y"
        assert info.fields[1].offset == 4  # 对齐后

    def test_register_struct_with_base(self):
        gen = TypeMetadataGenerator()
        gen.register_struct("Animal", [("name", "字符串型")])
        info = gen.register_struct(
            "Dog",
            [("age", "整数型")],
            base_class="Animal",
        )
        assert info.base_class == "Animal"

    def test_generate_all_struct_types(self):
        TypeRegistry.clear()
        gen = TypeMetadataGenerator()
        gen.register_struct_member("Vec2", "x", "浮点型")
        gen.register_struct_member("Vec2", "y", "浮点型")
        gen.register_struct_member("Vec3", "x", "浮点型")
        gen.register_struct_member("Vec3", "y", "浮点型")
        gen.register_struct_member("Vec3", "z", "浮点型")

        results = gen.generate_all_struct_types()
        assert len(results) == 2
        assert TypeRegistry.is_registered("Vec2") is True
        assert TypeRegistry.is_registered("Vec3") is True

    def test_field_layout_calculation(self):
        gen = TypeMetadataGenerator(target_platform="linux")
        info = gen.register_struct(
            "Mixed",
            [("a", "字符型"), ("b", "整数型"), ("c", "字符型")],
        )
        # char a (offset=0, size=1) + padding(3) + int b (offset=4, size=4) + char c (offset=8, size=1) + padding(3) = total 12
        assert info.fields[0].offset == 0
        assert info.fields[0].size == 1
        assert info.fields[1].offset == 4  # 对齐到 4 字节
        assert info.fields[1].size == 4
        assert info.fields[2].offset == 8
        assert info.fields[2].size == 1
        assert info.size == 12  # 对齐到 4 字节

    def setup_method(self):
        TypeRegistry.clear()


class TestReflectionMetadataCollector:
    """测试 ReflectionMetadataCollector"""

    def test_collect_and_generate(self):
        from zhc.type_system.struct_layout import StructLayoutCalculator

        collector = ReflectionMetadataCollector()

        # 手动构建布局
        calculator = StructLayoutCalculator()
        layout = calculator.calculate_layout(
            "TestStruct",
            [("field1", "整数型"), ("field2", "浮点型")],
        )

        collector.collect_struct_layout("TestStruct", layout)
        collector.collect_struct_method(
            "TestStruct", "doSomething", "空型", ["整数型"], is_static=False
        )

        type_info = collector.generate_type_info("TestStruct")
        assert type_info is not None
        assert type_info.name == "TestStruct"
        assert len(type_info.fields) == 2
        assert len(type_info.methods) == 1
        assert type_info.methods[0].name == "doSomething"

    def test_get_all_type_infos(self):
        from zhc.type_system.struct_layout import StructLayoutCalculator

        collector = ReflectionMetadataCollector()
        calc = StructLayoutCalculator()

        layout1 = calc.calculate_layout("S1", [("x", "整数型")])
        layout2 = calc.calculate_layout("S2", [("y", "浮点型")])

        collector.collect_struct_layout("S1", layout1)
        collector.collect_struct_layout("S2", layout2)

        infos = collector.get_all_type_infos()
        assert len(infos) == 2


# ============================================================================
# Keywords 映射测试
# ============================================================================


class TestReflectionKeywords:
    """测试反射相关关键词映射"""

    def test_get_type_info_keyword(self):
        assert "获取类型信息" in KEYWORDS
        assert KEYWORDS["获取类型信息"] == "zhc_get_type_info"

    def test_get_type_name_keyword(self):
        assert "获取类型名称" in KEYWORDS
        assert KEYWORDS["获取类型名称"] == "zhc_get_type_name"

    def test_get_type_size_keyword(self):
        assert "获取类型大小" in KEYWORDS
        assert KEYWORDS["获取类型大小"] == "zhc_get_type_size"

    def test_get_field_keyword(self):
        assert "获取字段" in KEYWORDS
        assert KEYWORDS["获取字段"] == "zhc_get_field"

    def test_get_field_value_keyword(self):
        assert "获取字段值" in KEYWORDS
        assert KEYWORDS["获取字段值"] == "zhc_get_field_value"

    def test_set_field_value_keyword(self):
        assert "设置字段值" in KEYWORDS
        assert KEYWORDS["设置字段值"] == "zhc_set_field_value"

    def test_type_info_keyword(self):
        assert "类型信息" in KEYWORDS
        assert KEYWORDS["类型信息"] == "zhc_type_info"

    def test_field_info_keyword(self):
        assert "字段信息" in KEYWORDS
        assert KEYWORDS["字段信息"] == "zhc_field_info"

    def test_is_primitive_type_keyword(self):
        assert "是基本类型" in KEYWORDS
        assert KEYWORDS["是基本类型"] == "zhc_is_primitive_type"


# ============================================================================
# IR Opcode 测试
# ============================================================================


class TestReflectionOpcodes:
    """测试反射相关 IR 操作码"""

    def test_type_info_get_opcode(self):
        op = Opcode.TYPE_INFO_GET
        assert op.name == "type_info_get"
        assert op.category == "反射"
        assert op.chinese == "获取类型信息"
        assert op.has_result is True

    def test_type_info_name_opcode(self):
        op = Opcode.TYPE_INFO_NAME
        assert op.name == "type_info_name"
        assert op.chinese == "获取类型名称"

    def test_type_info_size_opcode(self):
        op = Opcode.TYPE_INFO_SIZE
        assert op.name == "type_info_size"
        assert op.chinese == "获取类型大小"

    def test_type_info_fields_opcode(self):
        op = Opcode.TYPE_INFO_FIELDS
        assert op.name == "type_info_fields"
        assert op.chinese == "获取字段列表"

    def test_type_info_methods_opcode(self):
        op = Opcode.TYPE_INFO_METHODS
        assert op.name == "type_info_methods"
        assert op.chinese == "获取方法列表"

    def test_type_info_base_opcode(self):
        op = Opcode.TYPE_INFO_BASE
        assert op.name == "type_info_base"
        assert op.chinese == "获取父类"

    def test_field_get_opcode(self):
        op = Opcode.FIELD_GET
        assert op.name == "field_get"
        assert op.chinese == "获取字段信息"

    def test_field_get_value_opcode(self):
        op = Opcode.FIELD_GET_VALUE
        assert op.name == "field_get_value"
        assert op.chinese == "获取字段值"

    def test_field_set_value_opcode(self):
        op = Opcode.FIELD_SET_VALUE
        assert op.name == "field_set_value"
        assert op.chinese == "设置字段值"
        assert op.has_result is False  # 设置操作无返回值

    def test_opcode_from_name(self):
        op = Opcode.from_name("type_info_get")
        assert op == Opcode.TYPE_INFO_GET

    def test_all_reflection_opcodes_category(self):
        """所有反射操作码都属于反射类别"""
        reflection_ops = [
            Opcode.TYPE_INFO_GET,
            Opcode.TYPE_INFO_NAME,
            Opcode.TYPE_INFO_SIZE,
            Opcode.TYPE_INFO_FIELDS,
            Opcode.TYPE_INFO_METHODS,
            Opcode.TYPE_INFO_BASE,
            Opcode.FIELD_GET,
            Opcode.FIELD_GET_VALUE,
            Opcode.FIELD_SET_VALUE,
        ]
        for op in reflection_ops:
            assert op.category == "反射", f"{op.name} 不属于反射类别"


# ============================================================================
# 序列化测试
# ============================================================================


class TestSerialization:
    """测试序列化/反序列化"""

    def test_type_info_roundtrip(self):
        fields = [
            ReflectionFieldInfo(name="x", type_name="整数型", offset=0, size=4),
            ReflectionFieldInfo(name="y", type_name="浮点型", offset=4, size=4),
        ]
        methods = [
            ReflectionMethodInfo(
                name="move",
                return_type="空型",
                params=[
                    {"name": "dx", "type": "整数型"},
                    {"name": "dy", "type": "整数型"},
                ],
            ),
        ]
        info = ReflectionTypeInfo(
            name="Point",
            size=8,
            alignment=4,
            is_struct=True,
            base_class="Object",
            fields=fields,
            methods=methods,
        )

        d = info.to_dict()
        info2 = ReflectionTypeInfo.from_dict(d)

        assert info2.name == info.name
        assert info2.size == info.size
        assert info2.alignment == info.alignment
        assert info2.is_struct == info.is_struct
        assert info2.base_class == info.base_class
        assert len(info2.fields) == len(info.fields)
        assert info2.fields[0].name == "x"
        assert len(info2.methods) == len(info.methods)
        assert info2.methods[0].name == "move"

    def test_nested_type_info_serialization(self):
        """测试嵌套类型的序列化"""
        info = ReflectionTypeInfo(
            name="ComplexType",
            size=64,
            alignment=8,
            is_class=True,
            base_class="BaseClass",
            interfaces=["ISerializable", "IComparable"],
            fields=[
                ReflectionFieldInfo(
                    name="data",
                    type_name="整数型",
                    offset=0,
                    size=4,
                    is_public=False,
                    is_const=True,
                ),
            ],
            methods=[
                ReflectionMethodInfo(
                    name="serialize",
                    return_type="字符串型",
                    is_virtual=True,
                    vtable_index=0,
                ),
            ],
            constants={"MAX_VALUE": 100, "MIN_VALUE": 0},
        )

        d = info.to_dict()
        info2 = ReflectionTypeInfo.from_dict(d)

        assert info2.interfaces == ["ISerializable", "IComparable"]
        assert info2.fields[0].is_const is True
        assert info2.methods[0].vtable_index == 0
        assert info2.constants == {"MAX_VALUE": 100, "MIN_VALUE": 0}

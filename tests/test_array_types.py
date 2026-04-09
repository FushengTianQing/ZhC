"""
数组类型系统单元测试
Unit Tests for Array Type System

测试覆盖：
- ArrayTypeInfo 和 ArrayTypeFactory
- ArrayBoundsChecker 边界检查
- ArrayTypeInferrer 类型推导
- ArraySemanticAnalyzer 语义分析

创建日期: 2026-04-09
"""

import pytest

from zhc.type_system import (
    ArrayTypeInfo,
    ArrayKind,
    ArrayTypeFactory,
    ArrayBoundsChecker,
    Severity,
    ArrayTypeInferrer,
    unify_element_types,
    calculate_array_size,
)

from zhc.semantic import (
    ArraySemanticAnalyzer,
    ArrayTypeValidator,
)


class TestArrayTypeInfo:
    """测试 ArrayTypeInfo"""

    def test_basic_array(self):
        """测试基本数组类型"""
        arr = ArrayTypeInfo("整数型", [10])

        assert arr.element_type == "整数型"
        assert arr.dimensions == [10]
        assert arr.rank == 1
        assert arr.is_complete == True
        assert arr.is_multidimensional == False
        assert arr.total_elements == 10

    def test_multidimensional_array(self):
        """测试多维数组"""
        arr = ArrayTypeInfo("整数型", [3, 4, 5])

        assert arr.rank == 3
        assert arr.is_complete == True
        assert arr.is_multidimensional == True
        assert arr.total_elements == 60

    def test_incomplete_array(self):
        """测试不完整数组"""
        arr = ArrayTypeInfo("整数型", [None])

        assert arr.is_complete == False
        assert arr.total_elements == None

    def test_empty_array(self):
        """测试空数组"""
        arr = ArrayTypeInfo("整数型", [0])

        assert arr.is_empty == True
        assert arr.total_elements == 0

    def test_get_inner_type(self):
        """测试获取内层类型"""
        arr = ArrayTypeInfo("整数型", [3, 4, 5])

        assert arr.get_inner_type() == "整数型[4][5]"

        arr2 = ArrayTypeInfo("整数型", [10])
        assert arr2.get_inner_type() == "整数型"

    def test_get_element_at_depth(self):
        """测试指定深度访问后的类型"""
        arr = ArrayTypeInfo("整数型", [3, 4, 5])

        assert arr.get_element_at_depth(0) == "整数型[3][4][5]"
        assert arr.get_element_at_depth(1) == "整数型[4][5]"
        assert arr.get_element_at_depth(2) == "整数型[5]"
        assert arr.get_element_at_depth(3) == "整数型"

    def test_to_string(self):
        """测试字符串表示"""
        arr = ArrayTypeInfo("整数型", [10])
        assert arr.to_string() == "整数型[10]"

        arr2 = ArrayTypeInfo("浮点型", [3, 4])
        assert arr2.to_string() == "浮点型[3][4]"

    def test_is_compatible_with(self):
        """测试类型兼容性"""
        arr1 = ArrayTypeInfo("整数型", [10])
        arr2 = ArrayTypeInfo("整数型", [10])
        assert arr1.is_compatible_with(arr2) == True

        arr3 = ArrayTypeInfo("浮点型", [10])
        assert arr1.is_compatible_with(arr3) == False

        arr4 = ArrayTypeInfo("整数型", [None])
        assert arr1.is_compatible_with(arr4) == True  # 未知大小兼容

    def test_decay_to_pointer(self):
        """测试退化为指针"""
        arr = ArrayTypeInfo("整数型", [10])
        ptr = arr.decay_to_pointer()

        assert ptr.is_pointer == True
        assert ptr.kind == ArrayKind.INCOMPLETE


class TestArrayTypeFactory:
    """测试 ArrayTypeFactory"""

    def test_create_static(self):
        """测试创建静态数组"""
        arr = ArrayTypeFactory.create_static("整数型", 10)

        assert arr.kind == ArrayKind.STATIC
        assert arr.dimensions == [10]

        arr2 = ArrayTypeFactory.create_static("整数型", 3, 4)
        assert arr2.dimensions == [3, 4]

    def test_create_from_literal(self):
        """测试从字面量创建"""
        arr = ArrayTypeFactory.create_from_literal("整数型", 5)

        assert arr.kind == ArrayKind.LITERAL
        assert arr.dimensions == [5]

    def test_create_dynamic(self):
        """测试创建动态数组"""
        arr = ArrayTypeFactory.create_dynamic("整数型", [None])

        assert arr.kind == ArrayKind.DYNAMIC
        assert arr.is_complete == False

    def test_create_incomplete(self):
        """测试创建不完整数组"""
        arr = ArrayTypeFactory.create_incomplete("整数型")

        assert arr.kind == ArrayKind.INCOMPLETE
        assert arr.is_pointer == True

    def test_parse_from_string(self):
        """测试从字符串解析"""
        arr = ArrayTypeFactory.parse_from_string("整数型[10]")
        assert arr is not None
        assert arr.dimensions == [10]

        arr2 = ArrayTypeFactory.parse_from_string("浮点型[3][4]")
        assert arr2 is not None
        assert arr2.dimensions == [3, 4]

        arr3 = ArrayTypeFactory.parse_from_string("整数型[]")
        assert arr3 is not None
        assert arr3.dimensions == [None]

    def test_merge_types(self):
        """测试合并类型"""
        declared = ArrayTypeInfo("整数型", [None])
        inferred = ArrayTypeInfo("整数型", [5])

        merged = ArrayTypeFactory.merge_types(declared, inferred)
        assert merged.dimensions == [5]

        # 类型不匹配
        declared2 = ArrayTypeInfo("整数型", [10])
        inferred2 = ArrayTypeInfo("浮点型", [5])

        with pytest.raises(ValueError):
            ArrayTypeFactory.merge_types(declared2, inferred2)


class TestArrayBoundsChecker:
    """测试边界检查器"""

    def test_register_array(self):
        """测试注册数组"""
        checker = ArrayBoundsChecker()
        arr = ArrayTypeInfo("整数型", [10])

        checker.register_array("arr", arr)
        assert checker.get_array_info("arr") == arr

    def test_check_valid_access(self):
        """测试有效访问"""
        checker = ArrayBoundsChecker()
        checker.register_array("arr", ArrayTypeInfo("整数型", [10]))

        error = checker.check_access("arr", 5, 0, (1, 5))
        assert error is None

    def test_check_out_of_bounds(self):
        """测试越界访问"""
        checker = ArrayBoundsChecker()
        checker.register_array("arr", ArrayTypeInfo("整数型", [10]))

        error = checker.check_access("arr", 15, 0, (1, 10))
        assert error is not None
        assert error.severity == Severity.ERROR
        assert "越界" in error.message

    def test_check_negative_index(self):
        """测试负数索引"""
        checker = ArrayBoundsChecker()
        checker.register_array("arr", ArrayTypeInfo("整数型", [10]))

        error = checker.check_access("arr", -1, 0, (1, 5))
        assert error is not None
        assert "负数" in error.message

    def test_check_multidim_access(self):
        """测试多维数组访问"""
        checker = ArrayBoundsChecker()
        checker.register_array("matrix", ArrayTypeInfo("整数型", [3, 4]))

        errors = checker.check_multidim_access("matrix", [1, 2], (1, 5))
        assert len(errors) == 0

        errors = checker.check_multidim_access("matrix", [5, 2], (1, 5))
        assert len(errors) > 0

    def test_check_dimension_overflow(self):
        """测试维度过多"""
        checker = ArrayBoundsChecker()
        checker.register_array("arr", ArrayTypeInfo("整数型", [10]))

        errors = checker.check_multidim_access("arr", [1, 2], (1, 5))
        assert len(errors) > 0
        assert "维度过多" in errors[0].message


class TestArrayTypeInferrer:
    """测试类型推导器"""

    def test_infer_from_literal(self):
        """测试从字面量推导"""
        inferrer = ArrayTypeInferrer()

        result = inferrer.infer_from_literal([1, 2, 3])
        assert result.inferred_type.element_type == "整数型"
        assert result.inferred_type.dimensions == [3]

        result2 = inferrer.infer_from_literal([1.0, 2.0, 3.0])
        assert result2.inferred_type.element_type == "浮点型"

    def test_infer_from_empty_literal(self):
        """测试空数组推导"""
        inferrer = ArrayTypeInferrer()

        result = inferrer.infer_from_literal([])
        assert result.inferred_type.element_type == "整数型"
        assert result.inferred_type.dimensions == [0]
        assert len(result.warnings) > 0

    def test_infer_from_multidim_literal(self):
        """测试多维数组推导"""
        inferrer = ArrayTypeInferrer()

        result = inferrer.infer_from_multidim_literal([[1, 2], [3, 4]])
        assert result.inferred_type.dimensions == [2, 2]

    def test_infer_subscript_type(self):
        """测试下标访问类型推导"""
        inferrer = ArrayTypeInferrer()
        arr = ArrayTypeInfo("整数型", [3, 4, 5])

        assert inferrer.infer_subscript_type(arr, 1) == "整数型[4][5]"
        assert inferrer.infer_subscript_type(arr, 2) == "整数型[5]"
        assert inferrer.infer_subscript_type(arr, 3) == "整数型"

    def test_unify_element_types(self):
        """测试类型统一"""
        assert unify_element_types(["整数型", "整数型"]) == "整数型"
        assert unify_element_types(["整数型", "浮点型"]) == "浮点型"
        assert unify_element_types(["字符型", "整数型"]) == "整数型"


class TestArraySemanticAnalyzer:
    """测试语义分析器"""

    def test_analyze_array_declaration(self):
        """测试数组声明分析"""
        analyzer = ArraySemanticAnalyzer()

        result = analyzer.analyze_array_declaration("arr", "整数型[10]")
        assert result.success == True
        assert result.array_type.dimensions == [10]

    def test_analyze_subscript_access(self):
        """测试下标访问分析"""
        analyzer = ArraySemanticAnalyzer()
        analyzer.analyze_array_declaration("arr", "整数型[10]")

        result = analyzer.analyze_subscript_access("arr", [5])
        assert result.success == True

        result2 = analyzer.analyze_subscript_access("arr", [15])
        assert result2.success == False
        assert len(result2.errors) > 0

    def test_analyze_array_parameter(self):
        """测试数组参数分析"""
        analyzer = ArraySemanticAnalyzer()

        result = analyzer.analyze_array_parameter("param", "整数型[]")
        assert result.success == True
        assert result.array_type.is_pointer == True

    def test_analyze_multidim_array(self):
        """测试多维数组分析"""
        analyzer = ArraySemanticAnalyzer()

        result = analyzer.analyze_array_declaration("matrix", "浮点型[3][4]")
        assert result.success == True
        assert result.array_type.rank == 2

        result2 = analyzer.analyze_subscript_access("matrix", [1, 2])
        assert result2.success == True


class TestArrayTypeValidator:
    """测试类型验证器"""

    def test_validate_element_type(self):
        """测试元素类型验证"""
        assert ArrayTypeValidator.validate_element_type("整数型") == True
        assert ArrayTypeValidator.validate_element_type("浮点型") == True
        assert ArrayTypeValidator.validate_element_type("未知类型") == False

    def test_validate_dimensions(self):
        """测试维度验证"""
        valid, errors = ArrayTypeValidator.validate_dimensions([10, 20])
        assert valid == True

        valid2, errors2 = ArrayTypeValidator.validate_dimensions([10, -5])
        assert valid2 == False
        assert len(errors2) > 0

    def test_check_type_compatibility(self):
        """测试类型兼容性检查"""
        arr1 = ArrayTypeInfo("整数型", [10])
        arr2 = ArrayTypeInfo("整数型", [10])

        compatible, msg = ArrayTypeValidator.check_type_compatibility(arr1, arr2)
        assert compatible == True

        arr3 = ArrayTypeInfo("浮点型", [10])
        compatible2, msg2 = ArrayTypeValidator.check_type_compatibility(arr1, arr3)
        assert compatible2 == False


class TestCalculateArraySize:
    """测试数组大小计算"""

    def test_calculate_size(self):
        """测试大小计算"""
        arr = ArrayTypeInfo("整数型", [10])
        # 假设整数型元素大小为 4 字节
        size = calculate_array_size(arr, 4)
        assert size == 40

        arr2 = ArrayTypeInfo("整数型", [3, 4])
        size2 = calculate_array_size(arr2, 4)
        assert size2 == 48

    def test_calculate_incomplete_size(self):
        """测试不完整数组大小"""
        arr = ArrayTypeInfo("整数型", [None])
        size = calculate_array_size(arr, 4)
        assert size is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

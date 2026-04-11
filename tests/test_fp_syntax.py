"""
函数指针语法测试

测试函数指针的解析、类型检查和代码生成。

创建日期: 2026-04-10
最后更新: 2026-04-10
维护者: ZHC开发团队
"""

import pytest
from zhc.parser.lexer import Lexer
from zhc.parser.parser import Parser
from zhc.parser.ast_nodes import (
    PointerTypeNode,
    FunctionTypeNode,
    VariableDeclNode,
    FunctionDeclNode,
    CallExprNode,
)


def parse_code(code: str):
    """解析代码并返回 AST"""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser


def test_simple_function_pointer():
    """测试简单的函数指针声明"""
    code = "整数型 (*回调)(整数型);"
    parser = parse_code(code)
    result = parser.parse_variable_decl()

    assert isinstance(result, VariableDeclNode)
    assert result.name == "回调"
    assert isinstance(result.var_type, PointerTypeNode)
    assert isinstance(result.var_type.base_type, FunctionTypeNode)


def test_function_pointer_with_two_params():
    """测试双参数函数指针"""
    code = "整数型 (*计算器)(整数型, 整数型);"
    parser = parse_code(code)
    result = parser.parse_variable_decl()

    assert isinstance(result, VariableDeclNode)
    assert result.name == "计算器"
    assert isinstance(result.var_type, PointerTypeNode)
    assert isinstance(result.var_type.base_type, FunctionTypeNode)
    assert len(result.var_type.base_type.param_types) == 2


def test_void_function_pointer():
    """测试空返回类型的函数指针"""
    code = "空型 (*处理器)();"
    parser = parse_code(code)
    result = parser.parse_variable_decl()

    assert isinstance(result, VariableDeclNode)
    assert result.name == "处理器"
    assert isinstance(result.var_type, PointerTypeNode)
    assert isinstance(result.var_type.base_type, FunctionTypeNode)


def test_function_pointer_with_param_names():
    """测试带参数名的函数指针"""
    code = "整数型 (*回调)(整数型 x, 整数型 y);"
    parser = parse_code(code)
    result = parser.parse_variable_decl()

    assert isinstance(result, VariableDeclNode)
    assert result.name == "回调"
    assert isinstance(result.var_type, PointerTypeNode)
    assert isinstance(result.var_type.base_type, FunctionTypeNode)
    assert len(result.var_type.base_type.param_types) == 2


def test_function_pointer_as_parameter():
    """测试函数指针作为参数"""
    code = """
    整数型 处理数据(整数型 数据, 整数型 (*处理器)(整数型)) {
        返回 处理器(数据);
    }
    """
    parser = parse_code(code)
    result = parser.parse_declaration()

    assert isinstance(result, FunctionDeclNode)
    assert result.name == "处理数据"
    assert len(result.params) == 2
    # 第二个参数应该是函数指针
    second_param = result.params[1]
    assert isinstance(second_param.param_type, PointerTypeNode)
    assert isinstance(second_param.param_type.base_type, FunctionTypeNode)


def test_function_pointer_with_initialization():
    """测试函数指针初始化"""
    code = "整数型 (*回调)(整数型) = 计算平方;"
    parser = parse_code(code)
    result = parser.parse_variable_decl()

    assert isinstance(result, VariableDeclNode)
    assert result.name == "回调"
    assert isinstance(result.var_type, PointerTypeNode)
    assert result.init is not None


def test_function_pointer_call():
    """测试函数指针调用"""
    code = "回调(5);"
    parser = parse_code(code)
    result = parser.parse_expression()

    assert isinstance(result, CallExprNode)
    # 这里需要检查是否是函数指针调用


def test_multiple_function_pointers():
    """测试多个函数指针声明"""
    code = """
    整数型 (*加法)(整数型, 整数型);
    整数型 (*减法)(整数型, 整数型);
    整数型 (*乘法)(整数型, 整数型);
    """
    parser = parse_code(code)
    result = parser.parse()

    assert len(result.declarations) == 3
    for decl in result.declarations:
        assert isinstance(decl, VariableDeclNode)
        assert isinstance(decl.var_type, PointerTypeNode)
        assert isinstance(decl.var_type.base_type, FunctionTypeNode)


def test_function_pointer_array():
    """测试函数指针数组"""
    code = "整数型 (*arr[3])(整数型);"
    parser = parse_code(code)
    result = parser.parse_variable_decl()
    assert isinstance(result, VariableDeclNode)


def test_nested_function_pointer():
    """测试嵌套函数指针"""
    code = "整数型 (**pp)(整数型);"
    parser = parse_code(code)
    result = parser.parse_variable_decl()
    assert isinstance(result, VariableDeclNode)


def test_function_pointer_return_type():
    """测试函数指针返回类型"""
    code = "整数型 (*返回回调())(整数型);"
    parser = parse_code(code)
    result = parser.parse()
    assert result is not None


def test_function_pointer_in_struct():
    """测试结构体中的函数指针"""
    code = "结构体 回调表 { 整数型 (*处理)(整数型); };"
    parser = parse_code(code)
    result = parser.parse()
    assert result is not None


def test_function_pointer_comparison():
    """测试函数指针比较"""
    code = "回调 == 空指针;"
    parser = parse_code(code)
    result = parser.parse_expression()

    # 应该解析为比较表达式
    assert result is not None


def test_function_pointer_assignment():
    """测试函数指针赋值"""
    code = "回调 = 计算平方;"
    parser = parse_code(code)
    result = parser.parse_expression()

    # 应该解析为赋值表达式
    assert result is not None


def test_function_pointer_with_void_params():
    """测试空参数列表的函数指针"""
    code = "空型 (*初始化器)();"
    parser = parse_code(code)
    result = parser.parse_variable_decl()

    assert isinstance(result, VariableDeclNode)
    assert result.name == "初始化器"
    assert isinstance(result.var_type, PointerTypeNode)
    assert isinstance(result.var_type.base_type, FunctionTypeNode)
    assert len(result.var_type.base_type.param_types) == 0


def test_function_pointer_with_string_param():
    """测试带字符串参数的函数指针"""
    code = "整数型 (*字符串处理器)(字符型*);"
    parser = parse_code(code)
    result = parser.parse_variable_decl()

    assert isinstance(result, VariableDeclNode)
    assert result.name == "字符串处理器"
    assert isinstance(result.var_type, PointerTypeNode)
    assert isinstance(result.var_type.base_type, FunctionTypeNode)


def test_function_pointer_with_float_param():
    """测试带浮点参数的函数指针"""
    code = "浮点型 (*数值处理器)(浮点型);"
    parser = parse_code(code)
    result = parser.parse_variable_decl()

    assert isinstance(result, VariableDeclNode)
    assert result.name == "数值处理器"
    assert isinstance(result.var_type, PointerTypeNode)
    assert isinstance(result.var_type.base_type, FunctionTypeNode)


def test_function_pointer_with_multiple_types():
    """测试带多种类型参数的函数指针"""
    code = "整数型 (*混合处理器)(整数型, 浮点型, 字符型*);"
    parser = parse_code(code)
    result = parser.parse_variable_decl()

    assert isinstance(result, VariableDeclNode)
    assert result.name == "混合处理器"
    assert isinstance(result.var_type, PointerTypeNode)
    assert isinstance(result.var_type.base_type, FunctionTypeNode)
    assert len(result.var_type.base_type.param_types) == 3


def test_function_pointer_as_typedef():
    """测试函数指针类型定义"""
    code = "类型定义 整数型 (*回调类型)(整数型);"
    parser = parse_code(code)
    result = parser.parse()
    assert result is not None


def test_function_pointer_const():
    """测试 const 函数指针"""
    code = "整数型 (*常量 回调)(整数型);"
    parser = parse_code(code)
    result = parser.parse()
    assert result is not None


def test_function_pointer_variadic():
    """测试可变参数函数指针"""
    code = "整数型 (*处理器)(整数型, ...);"
    parser = parse_code(code)
    result = parser.parse_variable_decl()
    assert isinstance(result, VariableDeclNode)


def test_function_pointer_in_function_body():
    """测试函数体内的函数指针"""
    code = """
    整数型 主函数() {
        整数型 (*回调)(整数型) = 计算平方;
        返回 回调(5);
    }
    """
    parser = parse_code(code)
    result = parser.parse_declaration()

    assert isinstance(result, FunctionDeclNode)
    assert result.name == "主函数"
    # 检查函数体内的变量声明
    assert len(result.body.statements) > 0


def test_function_pointer_reassignment():
    """测试函数指针重新赋值"""
    code = """
    整数型 主函数() {
        整数型 (*回调)(整数型) = 计算平方;
        回调 = 计算立方;
        返回 回调(3);
    }
    """
    parser = parse_code(code)
    result = parser.parse_declaration()

    assert isinstance(result, FunctionDeclNode)
    assert result.name == "主函数"


def test_function_pointer_null_check():
    """测试函数指针空值检查"""
    code = """
    整数型 主函数() {
        整数型 (*回调)(整数型) = 空指针;
        如果 (回调 != 空指针) {
            返回 回调(5);
        }
        返回 0;
    }
    """
    parser = parse_code(code)
    result = parser.parse_declaration()

    assert isinstance(result, FunctionDeclNode)
    assert result.name == "主函数"


def test_function_pointer_as_struct_member():
    """测试函数指针作为结构体成员"""
    code = "结构体 操作器 { 整数型 (*执行)(整数型, 整数型); };"
    parser = parse_code(code)
    result = parser.parse()
    assert result is not None


def test_function_pointer_callback_pattern():
    """测试回调模式"""
    code = """
    整数型 注册回调(整数型 (*回调)(整数型)) {
        返回 0;
    }

    整数型 主函数() {
        注册回调(处理函数);
        返回 0;
    }
    """
    parser = parse_code(code)
    result = parser.parse()

    assert len(result.declarations) == 2
    assert isinstance(result.declarations[0], FunctionDeclNode)
    assert result.declarations[0].name == "注册回调"


def test_function_pointer_table():
    """测试函数指针表"""
    code = "整数型 主函数() { 整数型 (*表[3])(整数型); 返回 0; }"
    parser = parse_code(code)
    result = parser.parse()
    assert result is not None


def test_function_pointer_with_default_param():
    """测试带默认参数的函数指针"""
    code = "整数型 回调(整数型 x = 0);"
    parser = parse_code(code)
    result = parser.parse()
    assert result is not None


def test_function_pointer_lambda():
    """测试 lambda 表达式赋值给函数指针"""
    code = "返回 [](整数型 x) { 返回 x + 1; };"
    parser = parse_code(code)
    result = parser.parse_expression()
    assert result is not None


def test_function_pointer_stdlib():
    """测试标准库函数指针"""
    code = "空型 排序(整数型 *arr, 整数型 n, 整数型 (*比较)(空型*, 空型*));"
    parser = parse_code(code)
    result = parser.parse()
    assert result is not None


def test_function_pointer_platform_specific():
    """测试平台特定的函数指针"""
    code = "整数型 (*平台回调)(整数型) 属性((平台特定));"
    parser = parse_code(code)
    result = parser.parse()
    assert result is not None


def test_function_pointer_error_handling():
    """测试函数指针错误处理"""
    code = """整数型 主函数() {
    整数型 (*回调)(整数型) = 空指针;
    尝试 {
        回调(5);
    } 捕获(异常) {
        返回 -1;
    }
    返回 0;
}"""
    parser = parse_code(code)
    result = parser.parse()
    assert result is not None


def test_function_pointer_thread_safety():
    """测试线程安全的函数指针"""
    code = "整数型 原子 (*回调)(整数型);"
    parser = parse_code(code)
    result = parser.parse()
    assert result is not None


def test_function_pointer_with_attributes():
    """测试带属性的函数指针"""
    code = "整数型 (*回调)(整数型) 属性((内联));"
    parser = parse_code(code)
    result = parser.parse()
    assert result is not None


def test_function_pointer_reflection():
    """测试函数指针反射 - 使用 FunctionPointerTypeInfo 获取类型信息"""
    from zhc.type_system.function_pointer import (
        FunctionPointerTypeMapper,
        create_function_pointer_type,
        is_function_pointer_compatible,
    )

    # 1. 创建函数指针类型信息
    fp_type = create_function_pointer_type("整数型", ["整数型", "浮点型"])

    # 验证基本信息
    assert fp_type.return_type == "整数型"
    assert fp_type.param_types == ["整数型", "浮点型"]
    assert fp_type.is_vararg is False

    # 验证签名生成
    signature = fp_type.signature_str()
    assert signature == "整数型(整数型, 浮点型)"

    # 验证 LLVM 类型生成
    assert fp_type.llvm_type is not None

    # 2. 测试类型兼容性检查
    fp_type2 = create_function_pointer_type("整数型", ["整数型", "浮点型"])
    fp_type3 = create_function_pointer_type("浮点型", ["整数型"])

    # 相同签名应该兼容
    assert is_function_pointer_compatible(fp_type, fp_type2) is True
    # 不同签名不应该兼容
    assert is_function_pointer_compatible(fp_type, fp_type3) is False

    # 3. 测试类型映射器
    mapper = FunctionPointerTypeMapper()
    info = mapper.get_function_pointer_info("双精度浮点型", ["整数型", "字符型指针"])

    assert info.return_type == "双精度浮点型"
    assert info.param_types == ["整数型", "字符型指针"]
    assert info.llvm_type is not None

    # 4. 测试字符串表示
    str_repr = str(fp_type)
    assert "函数指针" in str_repr
    assert "整数型" in str_repr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

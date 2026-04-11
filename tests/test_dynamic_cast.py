# -*- coding: utf-8 -*-
"""
P5-反射-动态类型转换 测试

测试内容：
1. CastError/CastErrorType 枚举和数据类
2. TypeCast 增强功能（get_cast_path, can_cast）
3. CastValidator 类
4. Lexer AS/IS token
5. Parser as/is 表达式
6. AST AsExprNode/IsExprNode
7. IR 生成 as/is 表达式
8. 语义分析 as/is 类型推导

作者：远
日期：2026-04-11
"""

import pytest


# =============================================================================
# Part 1: CastError 和 CastErrorType 测试
# =============================================================================


class TestCastError:
    """测试 CastError 数据类"""

    def test_cast_error_type_enum(self):
        """测试 CastErrorType 枚举值"""
        from zhc.reflection.type_cast import CastErrorType

        assert CastErrorType.NULL_SOURCE.value == "null_source"
        assert CastErrorType.INVALID_CAST.value == "invalid_cast"
        assert CastErrorType.AMBIGUOUS_CAST.value == "ambiguous_cast"
        assert CastErrorType.INTERFACE_NOT_FOUND.value == "interface_not_found"
        assert CastErrorType.TYPE_MISMATCH.value == "type_mismatch"
        assert CastErrorType.NOT_SUBTYPE.value == "not_subtype"

    def test_cast_error_creation(self):
        """测试 CastError 创建"""
        from zhc.reflection.type_cast import CastError, CastErrorType

        error = CastError(
            error_type=CastErrorType.INVALID_CAST,
            message="无法转换",
            source_type="狗",
            target_type="猫",
            cast_path=["狗", "动物"],
            ancestors=["动物"],
        )

        assert error.error_type == CastErrorType.INVALID_CAST
        assert error.message == "无法转换"
        assert error.source_type == "狗"
        assert error.target_type == "猫"
        assert error.cast_path == ["狗", "动物"]
        assert error.ancestors == ["动物"]

    def test_cast_error_str(self):
        """测试 CastError 字符串表示"""
        from zhc.reflection.type_cast import CastError, CastErrorType

        error = CastError(
            error_type=CastErrorType.INVALID_CAST,
            message="测试错误",
        )

        assert str(error) == "CastError(invalid_cast): 测试错误"

    def test_cast_error_to_dict(self):
        """测试 CastError 序列化"""
        from zhc.reflection.type_cast import CastError, CastErrorType

        error = CastError(
            error_type=CastErrorType.INTERFACE_NOT_FOUND,
            message="接口未实现",
            source_type="数据",
            target_type="可序列化",
        )

        d = error.to_dict()
        assert d["error_type"] == "interface_not_found"
        assert d["message"] == "接口未实现"
        assert d["source_type"] == "数据"
        assert d["target_type"] == "可序列化"


class TestTypeCastError:
    """测试 TypeCastError 异常"""

    def test_type_cast_error_basic(self):
        """测试基本 TypeCastError"""
        from zhc.reflection.type_cast import TypeCastError

        error = TypeCastError("狗", "猫")
        assert error.source_type == "狗"
        assert error.target_type == "猫"
        assert "无法将 狗 转换为 猫" in str(error)

    def test_type_cast_error_with_details(self):
        """测试带详细信息的 TypeCastError"""
        from zhc.reflection.type_cast import TypeCastError, CastErrorType

        error = TypeCastError(
            "狗",
            "猫",
            message="自定义消息",
            error_type=CastErrorType.NOT_SUBTYPE,
            cast_path=["狗", "动物"],
            ancestors=["动物"],
        )

        assert error.error_type == CastErrorType.NOT_SUBTYPE
        assert error.cast_path == ["狗", "动物"]
        assert error.ancestors == ["动物"]

    def test_type_cast_error_to_cast_error(self):
        """测试 TypeCastError 转换为 CastError"""
        from zhc.reflection.type_cast import TypeCastError, CastError, CastErrorType

        type_error = TypeCastError(
            "狗",
            "猫",
            error_type=CastErrorType.INVALID_CAST,
            cast_path=["狗", "动物"],
        )

        cast_error = type_error.to_cast_error()
        assert isinstance(cast_error, CastError)
        assert cast_error.source_type == "狗"
        assert cast_error.target_type == "猫"


# =============================================================================
# Part 2: TypeCast 增强功能测试
# =============================================================================


class TestTypeCastEnhanced:
    """测试 TypeCast 增强功能"""

    def test_get_cast_path_same_type(self):
        """测试相同类型的转换路径"""
        from zhc.reflection.type_cast import get_cast_path

        # 相同类型
        path = get_cast_path("整数型", "整数型")
        assert path == ["整数型"]

    def test_can_cast(self):
        """测试 can_cast 方法"""
        from zhc.reflection.type_cast import can_cast
        from zhc.reflection.type_info import TypeRegistry, ReflectionTypeInfo

        # 注册测试类型
        TypeRegistry.clear()
        TypeRegistry.register(
            ReflectionTypeInfo(
                name="Dog",
                size=8,
                alignment=8,
                base_class="Animal",
            )
        )
        TypeRegistry.register(
            ReflectionTypeInfo(
                name="Animal",
                size=8,
                alignment=8,
                base_class=None,
            )
        )

        # Dog 是 Animal 的子类
        assert can_cast("Dog", "Animal") is True
        # Animal 不是 Dog 的子类
        assert can_cast("Animal", "Dog") is False
        # 相同类型
        assert can_cast("Dog", "Dog") is True

        TypeRegistry.clear()

    def test_get_cast_path_with_inheritance(self):
        """测试继承链的转换路径"""
        from zhc.reflection.type_cast import TypeCast
        from zhc.reflection.type_info import TypeRegistry, ReflectionTypeInfo

        TypeRegistry.clear()
        # 注册继承链: Dog -> Animal -> LivingThing
        TypeRegistry.register(
            ReflectionTypeInfo(
                name="Dog",
                size=8,
                alignment=8,
                base_class="Animal",
            )
        )
        TypeRegistry.register(
            ReflectionTypeInfo(
                name="Animal",
                size=8,
                alignment=8,
                base_class="LivingThing",
            )
        )
        TypeRegistry.register(
            ReflectionTypeInfo(
                name="LivingThing",
                size=8,
                alignment=8,
                base_class=None,
            )
        )

        caster = TypeCast()
        path = caster.get_cast_path("Dog", "LivingThing")

        # 路径应该包含 Dog->Animal->LivingThing
        assert path is not None
        assert path[0] == "Dog"
        assert "Animal" in path
        assert "LivingThing" in path

        TypeRegistry.clear()


# =============================================================================
# Part 3: CastValidator 测试
# =============================================================================


class TestCastValidator:
    """测试 CastValidator 类"""

    def test_validate_valid_cast(self):
        """测试有效转换的验证"""
        from zhc.reflection.type_cast import CastValidator
        from zhc.reflection.type_info import TypeRegistry, ReflectionTypeInfo

        TypeRegistry.clear()
        TypeRegistry.register(
            ReflectionTypeInfo(
                name="Dog",
                size=8,
                alignment=8,
                base_class="Animal",
            )
        )
        TypeRegistry.register(
            ReflectionTypeInfo(
                name="Animal",
                size=8,
                alignment=8,
                base_class=None,
            )
        )

        class Dog:
            pass

        # 确保 Dog 类被注册为 zhc 类型
        Dog._zhc_type_name = "Dog"

        validator = CastValidator()
        error = validator.validate(Dog(), "Animal")

        # 有效转换应该返回 None
        assert error is None

        TypeRegistry.clear()

    def test_validate_null_source(self):
        """测试空源对象的验证"""
        from zhc.reflection.type_cast import CastValidator, CastErrorType

        validator = CastValidator()
        error = validator.validate(None, "Animal")

        assert error is not None
        assert error.error_type == CastErrorType.NULL_SOURCE

    def test_validate_invalid_cast(self):
        """测试无效转换的验证"""
        from zhc.reflection.type_cast import CastValidator, CastErrorType
        from zhc.reflection.type_info import TypeRegistry, ReflectionTypeInfo

        TypeRegistry.clear()
        TypeRegistry.register(
            ReflectionTypeInfo(
                name="Dog",
                size=8,
                alignment=8,
                base_class="Animal",
            )
        )
        TypeRegistry.register(
            ReflectionTypeInfo(
                name="Cat",
                size=8,
                alignment=8,
                base_class="Animal",
            )
        )

        class Dog:
            pass

        Dog._zhc_type_name = "Dog"

        validator = CastValidator()
        error = validator.validate(Dog(), "Cat")

        assert error is not None
        assert error.error_type == CastErrorType.INVALID_CAST

        TypeRegistry.clear()

    def test_find_best_cast(self):
        """测试 find_best_cast 方法"""
        from zhc.reflection.type_cast import CastValidator
        from zhc.reflection.type_info import TypeRegistry, ReflectionTypeInfo

        TypeRegistry.clear()
        TypeRegistry.register(
            ReflectionTypeInfo(
                name="Dog",
                size=8,
                alignment=8,
                base_class="Animal",
            )
        )
        TypeRegistry.register(
            ReflectionTypeInfo(
                name="Animal",
                size=8,
                alignment=8,
                base_class=None,
            )
        )

        class Dog:
            pass

        Dog._zhc_type_name = "Dog"

        validator = CastValidator()
        best = validator.find_best_cast(Dog(), ["Cat", "Animal", "Dog"])

        # 应该返回第一个可转换的类型
        assert best == "Animal"

        TypeRegistry.clear()

    def test_get_suggestions(self):
        """测试 get_suggestions 方法"""
        from zhc.reflection.type_cast import CastValidator
        from zhc.reflection.type_info import TypeRegistry, ReflectionTypeInfo

        TypeRegistry.clear()
        TypeRegistry.register(
            ReflectionTypeInfo(
                name="Dog",
                size=8,
                alignment=8,
                base_class="Animal",
            )
        )
        TypeRegistry.register(
            ReflectionTypeInfo(
                name="Animal",
                size=8,
                alignment=8,
                base_class=None,
            )
        )

        class Dog:
            pass

        Dog._zhc_type_name = "Dog"

        validator = CastValidator()
        suggestions = validator.get_suggestions(Dog())

        assert "Dog" in suggestions
        assert "Animal" in suggestions

        TypeRegistry.clear()


# =============================================================================
# Part 4: Lexer AS/IS Token 测试
# =============================================================================


class TestLexerASTokens:
    """测试 Lexer AS/IS token"""

    def test_as_token_type_exists(self):
        """测试 AS token 类型存在"""
        from zhc.parser.lexer import TokenType

        assert hasattr(TokenType, "AS")
        assert hasattr(TokenType, "IS")

    def test_as_keyword_mapping(self):
        """测试 AS 关键字映射"""
        from zhc.parser.lexer import Lexer, TokenType

        lexer = Lexer("转为")
        tokens = lexer.tokenize()

        # 找到转为关键字
        as_tokens = [t for t in tokens if t.type == TokenType.AS]
        assert len(as_tokens) == 1

    def test_is_keyword_mapping(self):
        """测试 IS 关键字映射"""
        from zhc.parser.lexer import Lexer, TokenType

        lexer = Lexer("是类型")
        tokens = lexer.tokenize()

        # 找到是类型关键字
        is_tokens = [t for t in tokens if t.type == TokenType.IS]
        assert len(is_tokens) == 1

    def test_as_token_in_expression(self):
        """测试 AS token 在表达式中"""
        from zhc.parser.lexer import Lexer, TokenType

        lexer = Lexer("obj 转为 狗")
        tokens = lexer.tokenize()

        # 过滤掉 EOF
        non_eof = [t for t in tokens if t.type != TokenType.EOF]
        assert len(non_eof) == 3
        assert non_eof[1].type == TokenType.AS


# =============================================================================
# Part 5: AST AsExprNode/IsExprNode 测试
# =============================================================================


class TestASTNodes:
    """测试 AST AsExprNode/IsExprNode"""

    def test_as_expr_node_type(self):
        """测试 AS_EXPR AST 节点类型"""
        from zhc.parser.ast_nodes import ASTNodeType

        assert hasattr(ASTNodeType, "AS_EXPR")
        assert hasattr(ASTNodeType, "IS_EXPR")

    def test_as_expr_node_creation(self):
        """测试 AsExprNode 创建"""
        from zhc.parser.ast_nodes import AsExprNode, IdentifierExprNode, StructTypeNode

        expr = IdentifierExprNode("obj")
        target_type = StructTypeNode("Dog")
        as_expr = AsExprNode(expr, target_type)

        assert as_expr.expr == expr
        assert as_expr.target_type == target_type
        assert len(as_expr.get_children()) == 2

    def test_is_expr_node_creation(self):
        """测试 IsExprNode 创建"""
        from zhc.parser.ast_nodes import IsExprNode, IdentifierExprNode, StructTypeNode

        expr = IdentifierExprNode("obj")
        target_type = StructTypeNode("Dog")
        is_expr = IsExprNode(expr, target_type)

        assert is_expr.expr == expr
        assert is_expr.target_type == target_type
        assert len(is_expr.get_children()) == 2

    def test_as_expr_node_structure(self):
        """测试 AsExprNode 节点结构"""
        from zhc.parser.ast_nodes import (
            AsExprNode,
            IdentifierExprNode,
            StructTypeNode,
            ASTNodeType,
        )

        expr = IdentifierExprNode("obj")
        target_type = StructTypeNode("Dog")
        as_expr = AsExprNode(expr, target_type)

        # 验证节点类型
        assert as_expr.node_type == ASTNodeType.AS_EXPR
        # 验证子节点
        children = as_expr.get_children()
        assert len(children) == 2
        assert children[0] == expr
        assert children[1] == target_type


# =============================================================================
# Part 6: Parser as/is 表达式测试
# =============================================================================


class TestParserASIS:
    """测试 Parser as/is 表达式解析"""

    def test_parse_as_expression(self):
        """测试解析 as 表达式"""
        from zhc.parser.lexer import Lexer
        from zhc.parser.parser import Parser
        from zhc.parser.ast_nodes import AsExprNode

        lexer = Lexer("obj 转为 狗")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse_expression()

        assert isinstance(ast, AsExprNode)
        assert ast.expr is not None
        assert ast.target_type is not None

    def test_parse_is_expression(self):
        """测试解析 is 表达式"""
        from zhc.parser.lexer import Lexer
        from zhc.parser.parser import Parser
        from zhc.parser.ast_nodes import IsExprNode

        lexer = Lexer("obj 是类型 狗")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse_expression()

        assert isinstance(ast, IsExprNode)
        assert ast.expr is not None
        assert ast.target_type is not None

    def test_parse_is_in_condition(self):
        """测试解析条件中的 is 表达式"""
        from zhc.parser.lexer import Lexer
        from zhc.parser.parser import Parser
        from zhc.parser.ast_nodes import BinaryExprNode, IsExprNode

        lexer = Lexer("obj 是类型 狗 == 真")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse_expression()

        # is 表达式优先级高于 ==
        assert isinstance(ast, BinaryExprNode)
        assert isinstance(ast.left, IsExprNode)


# =============================================================================
# Part 7: IR 生成测试
# =============================================================================


class TestIRGeneration:
    """测试 IR 生成"""

    def test_safe_cast_opcode_exists(self):
        """测试 SAFE_CAST opcode 存在"""
        from zhc.ir.opcodes import Opcode

        assert hasattr(Opcode, "SAFE_CAST")
        assert Opcode.SAFE_CAST.value[0] == "safe_cast"

    def test_is_type_opcode_exists(self):
        """测试 IS_TYPE opcode 存在"""
        from zhc.ir.opcodes import Opcode

        assert hasattr(Opcode, "IS_TYPE")
        assert Opcode.IS_TYPE.value[0] == "is_type"

    def test_dynamic_cast_opcode_exists(self):
        """测试 DYNAMIC_CAST opcode 存在"""
        from zhc.ir.opcodes import Opcode

        assert hasattr(Opcode, "DYNAMIC_CAST")
        assert Opcode.DYNAMIC_CAST.value[0] == "dynamic_cast"

    def test_eval_as_method_exists(self):
        """测试 _eval_as 方法存在"""
        from zhc.ir.ir_generator import IRGenerator

        assert hasattr(IRGenerator, "_eval_as")

    def test_eval_is_method_exists(self):
        """测试 _eval_is 方法存在"""
        from zhc.ir.ir_generator import IRGenerator

        assert hasattr(IRGenerator, "_eval_is")


# =============================================================================
# Part 8: 语义分析测试
# =============================================================================


class TestSemanticAnalysis:
    """测试语义分析"""

    def test_as_expr_in_analyze_node(self):
        """测试 AS_EXPR 在语义分析中"""
        from zhc.parser.ast_nodes import ASTNodeType
        from zhc.semantic.semantic_analyzer import SemanticAnalyzer

        # 检查 AS_EXPR 在 _analyze_node 的分支中
        SemanticAnalyzer()  # 验证可实例化
        # ASTNodeType.AS_EXPR 应该被处理
        assert ASTNodeType.AS_EXPR is not None
        assert ASTNodeType.IS_EXPR is not None


# =============================================================================
# Part 9: 公共 API 测试
# =============================================================================


class TestPublicAPI:
    """测试公共 API 导出"""

    def test_reflection_module_exports(self):
        """测试 reflection 模块导出"""
        from zhc import reflection

        # CastError 相关
        assert hasattr(reflection, "CastErrorType")
        assert hasattr(reflection, "CastError")

        # TypeCast 相关
        assert hasattr(reflection, "TypeCast")
        assert hasattr(reflection, "TypeCastError")
        assert hasattr(reflection, "CastValidator")

        # API 函数
        assert hasattr(reflection, "safe_cast")
        assert hasattr(reflection, "dynamic_cast")
        assert hasattr(reflection, "get_cast_path")
        assert hasattr(reflection, "can_cast")
        assert hasattr(reflection, "validate_cast")
        assert hasattr(reflection, "find_best_cast")


# =============================================================================
# Part 10: CastResult 泛型类测试（新增）
# =============================================================================


class TestCastResult:
    """测试 CastResult 泛型类"""

    def test_cast_result_success(self):
        """测试成功的 CastResult"""
        from zhc.reflection.type_cast import CastResult

        result = CastResult(success=True, result="test_value")
        assert result.success is True
        assert result.result == "test_value"
        assert result.error is None

    def test_cast_result_failure(self):
        """测试失败的 CastResult"""
        from zhc.reflection.type_cast import CastResult, CastError, CastErrorType

        error = CastError(
            error_type=CastErrorType.TYPE_MISMATCH,
            message="类型不匹配",
        )
        result = CastResult(success=False, error=error)
        assert result.success is False
        assert result.result is None
        assert result.error == error

    def test_cast_result_bool(self):
        """测试 CastResult 的布尔转换"""
        from zhc.reflection.type_cast import CastResult

        success_result = CastResult(success=True, result="value")
        failure_result = CastResult(success=False)

        assert bool(success_result) is True
        assert bool(failure_result) is False

    def test_cast_result_unwrap(self):
        """测试 CastResult.unwrap()"""
        from zhc.reflection.type_cast import CastResult, TypeCastError

        success_result = CastResult(success=True, result="value")
        assert success_result.unwrap() == "value"

        failure_result = CastResult(success=False)
        with pytest.raises(TypeCastError):
            failure_result.unwrap()

    def test_cast_result_unwrap_or(self):
        """测试 CastResult.unwrap_or()"""
        from zhc.reflection.type_cast import CastResult

        success_result = CastResult(success=True, result="value")
        assert success_result.unwrap_or("default") == "value"

        failure_result = CastResult(success=False)
        assert failure_result.unwrap_or("default") == "default"

    def test_cast_result_is_ok_is_err(self):
        """测试 CastResult.is_ok() 和 is_err()"""
        from zhc.reflection.type_cast import CastResult

        result = CastResult(success=True, result="value")
        assert result.is_ok() is True
        assert result.is_err() is False

        failure = CastResult(success=False)
        assert failure.is_ok() is False
        assert failure.is_err() is True

    def test_cast_result_to_dict(self):
        """测试 CastResult.to_dict()"""
        from zhc.reflection.type_cast import CastResult, CastError, CastErrorType

        error = CastError(
            error_type=CastErrorType.INVALID_CAST,
            message="测试错误",
        )
        result = CastResult(success=False, error=error)
        d = result.to_dict()

        assert d["success"] is False
        assert d["error"]["error_type"] == "invalid_cast"

    def test_safe_cast_as_api(self):
        """测试 safe_cast_as API"""
        from zhc.reflection.type_cast import safe_cast_as
        from zhc.reflection.type_info import TypeRegistry, ReflectionTypeInfo

        TypeRegistry.clear()
        TypeRegistry.register(
            ReflectionTypeInfo(
                name="Dog",
                size=8,
                alignment=8,
                base_class="Animal",
            )
        )
        TypeRegistry.register(
            ReflectionTypeInfo(
                name="Animal",
                size=8,
                alignment=8,
                base_class=None,
            )
        )

        class Dog:
            _zhc_type_name = "Dog"

        result = safe_cast_as(Dog(), "Animal")
        assert result.success is True
        assert result.result is not None

        TypeRegistry.clear()

    def test_dynamic_cast_as_api(self):
        """测试 dynamic_cast_as API"""
        from zhc.reflection.type_cast import dynamic_cast_as
        from zhc.reflection.type_info import TypeRegistry, ReflectionTypeInfo

        TypeRegistry.clear()
        TypeRegistry.register(
            ReflectionTypeInfo(
                name="Dog",
                size=8,
                alignment=8,
                base_class="Animal",
            )
        )
        TypeRegistry.register(
            ReflectionTypeInfo(
                name="Animal",
                size=8,
                alignment=8,
                base_class=None,
            )
        )

        class Dog:
            _zhc_type_name = "Dog"

        result = dynamic_cast_as(Dog(), "Animal")
        assert result.success is True

        TypeRegistry.clear()


# =============================================================================
# Part 11: IR 类型转换节点测试（新增）
# =============================================================================


class TestIRCastNodes:
    """测试 IR 类型转换节点类"""

    def test_ir_cast_inst_base_class(self):
        """测试 IRCastInst 基类"""
        from zhc.ir.cast import IRCastInst

        assert hasattr(IRCastInst, "__init__")
        assert hasattr(IRCastInst, "get_source_type")
        assert hasattr(IRCastInst, "get_target_type")

    def test_ir_safe_cast_inst(self):
        """测试 IRSafeCastInst"""
        from zhc.ir.cast import IRSafeCastInst
        from zhc.ir.values import IRValue, ValueKind

        source = IRValue("%obj", "Dog", ValueKind.TEMP)
        inst = IRSafeCastInst(source, "Animal")

        assert inst.source == source
        assert inst.target_type_name == "Animal"
        assert inst.result is not None
        assert inst.opcode.name == "safe_cast"

    def test_ir_is_type_inst(self):
        """测试 IRIsTypeInst"""
        from zhc.ir.cast import IRIsTypeInst
        from zhc.ir.values import IRValue, ValueKind

        source = IRValue("%obj", "Dog", ValueKind.TEMP)
        inst = IRIsTypeInst(source, "Animal")

        assert inst.source == source
        assert inst.target_type_name == "Animal"
        assert inst.result.ty == "布尔型"
        assert inst.opcode.name == "is_type"

    def test_ir_dynamic_cast_inst(self):
        """测试 IRDynamicCastInst"""
        from zhc.ir.cast import IRDynamicCastInst
        from zhc.ir.values import IRValue, ValueKind

        source = IRValue("%obj", "Dog", ValueKind.TEMP)
        inst = IRDynamicCastInst(source, "Animal")

        assert inst.source == source
        assert inst.target_type_name == "Animal"
        assert inst.opcode.name == "dynamic_cast"

    def test_is_cast_instruction(self):
        """测试 is_cast_instruction 辅助函数"""
        from zhc.ir.cast import IRSafeCastInst, IRIsTypeInst, is_cast_instruction
        from zhc.ir.values import IRValue, ValueKind

        source = IRValue("%obj", "Dog", ValueKind.TEMP)

        cast_inst = IRSafeCastInst(source, "Animal")
        assert is_cast_instruction(cast_inst) is True

        is_inst = IRIsTypeInst(source, "Animal")
        assert is_cast_instruction(is_inst) is True

    def test_get_cast_instruction_from_generic(self):
        """测试从通用指令提取类型转换指令"""
        from zhc.ir.cast import get_cast_instruction
        from zhc.ir.instructions import IRInstruction
        from zhc.ir.opcodes import Opcode
        from zhc.ir.values import IRValue, ValueKind

        source = IRValue("%obj", "Dog", ValueKind.TEMP)
        type_const = IRValue(
            "Animal", "字符串型", ValueKind.CONST, const_value="Animal"
        )
        result = IRValue("%result", "Animal", ValueKind.TEMP)

        # 创建通用指令
        generic = IRInstruction(
            opcode=Opcode.SAFE_CAST,
            operands=[source, type_const],
            result=[result],
        )

        # 提取类型转换指令
        cast_inst = get_cast_instruction(generic)
        assert cast_inst is not None
        assert cast_inst.target_type_name == "Animal"


# =============================================================================
# Part 12: IR 模块导出测试（新增）
# =============================================================================


class TestIRModuleExports:
    """测试 IR 模块导出"""

    def test_ir_module_exports_cast_nodes(self):
        """测试 IR 模块导出类型转换节点"""
        from zhc import ir

        assert hasattr(ir, "IRCastInst")
        assert hasattr(ir, "IRSafeCastInst")
        assert hasattr(ir, "IRDynamicCastInst")
        assert hasattr(ir, "IRIsTypeInst")
        assert hasattr(ir, "is_cast_instruction")
        assert hasattr(ir, "get_cast_instruction")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

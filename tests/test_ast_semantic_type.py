"""
测试套件：AST语义类型推导
Test Suite: AST, Semantic Analysis, Type Inference

统一使用 parser.ast_nodes 的第一套AST节点
更新: 2026-04-03 从 ast_core 迁移到 parser.ast_nodes
"""

import unittest
import sys
import os

# 将 src 目录加入 path，以包方式导入 zhpp
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zhpp.parser.ast_nodes import (
    ASTNode, ASTNodeType,
    ProgramNode, ModuleDeclNode, FunctionDeclNode, StructDeclNode,
    VariableDeclNode, ParamDeclNode,
    BlockStmtNode, IfStmtNode, WhileStmtNode, ForStmtNode,
    BinaryExprNode, UnaryExprNode, CallExprNode,
    IdentifierExprNode, IntLiteralNode, FloatLiteralNode,
    StringLiteralNode, BoolLiteralNode,
    PrimitiveTypeNode, BreakStmtNode, ContinueStmtNode,
    ReturnStmtNode, ExprStmtNode,
)

from zhpp.semantic.semantic_analyzer import (
    SemanticAnalyzer, SymbolTable, Symbol, ScopeType, SemanticError
)

from zhpp.typeinfer.engine import (
    TypeInferenceEngine, TypeEnv, BaseType, TypeVariable
)


# ============================================================================
# 测试：AST节点
# ============================================================================

class TestASTNodes(unittest.TestCase):
    """测试AST节点（第一套 parser.ast_nodes）"""
    
    def test_program_node(self):
        """测试程序节点"""
        var = VariableDeclNode("x", PrimitiveTypeNode("整数型"), IntLiteralNode(42))
        prog = ProgramNode([var])
        self.assertEqual(prog.node_type, ASTNodeType.PROGRAM)
        self.assertEqual(len(prog.declarations), 1)
    
    def test_function_node(self):
        """测试函数声明节点"""
        ret_type = PrimitiveTypeNode("整数型")
        param = ParamDeclNode("n", PrimitiveTypeNode("整数型"))
        body = ReturnStmtNode(IdentifierExprNode("n"))
        func = FunctionDeclNode("add", ret_type, [param], body)
        self.assertEqual(func.node_type, ASTNodeType.FUNCTION_DECL)
        self.assertEqual(func.name, "add")
        self.assertEqual(len(func.params), 1)
    
    def test_struct_node(self):
        """测试结构体声明节点"""
        member = VariableDeclNode("x", PrimitiveTypeNode("整数型"), None)
        struct = StructDeclNode("Point", [member])
        self.assertEqual(struct.node_type, ASTNodeType.STRUCT_DECL)
        self.assertEqual(struct.name, "Point")
        self.assertEqual(len(struct.members), 1)
    
    def test_binary_expression(self):
        """测试二元表达式"""
        left = IntLiteralNode(10)
        right = IntLiteralNode(20)
        binary = BinaryExprNode("+", left, right)
        self.assertEqual(binary.node_type, ASTNodeType.BINARY_EXPR)
        self.assertEqual(binary.operator, "+")
        self.assertEqual(len(binary.get_children()), 2)
    
    def test_parent_reference(self):
        """测试parent引用"""
        var = VariableDeclNode("x", PrimitiveTypeNode("整数型"), IntLiteralNode(0))
        self.assertIs(var.var_type.parent, var)
        self.assertIs(var.init.parent, var)
        self.assertIsNone(var.parent)
    
    def test_get_children(self):
        """测试get_children"""
        block = BlockStmtNode([IntLiteralNode(1), IntLiteralNode(2)])
        children = block.get_children()
        self.assertEqual(len(children), 2)
    
    def test_get_hash(self):
        """测试get_hash"""
        n1 = IntLiteralNode(42)
        n2 = IntLiteralNode(42)
        # 不同节点，哈希相同（相同结构+值）
        self.assertEqual(n1.get_hash(), n2.get_hash())
        # 不同值，哈希不同
        n3 = IntLiteralNode(99)
        self.assertNotEqual(n1.get_hash(), n3.get_hash())
    
    def test_inferred_type(self):
        """测试inferred_type属性"""
        node = IntLiteralNode(42)
        self.assertIsNone(node.inferred_type)
        node.inferred_type = "整数型"
        self.assertEqual(node.inferred_type, "整数型")
    
    def test_to_dict(self):
        """测试to_dict序列化"""
        node = IntLiteralNode(42, line=10, column=5)
        d = node.to_dict()
        self.assertEqual(d['node_type'], 'INT_LITERAL')
        self.assertEqual(d['line'], 10)
        self.assertEqual(d['column'], 5)
        self.assertIn('node_id', d)


# ============================================================================
# 测试：语义分析
# ============================================================================

class TestSemanticAnalyzer(unittest.TestCase):
    """测试语义分析器"""
    
    def test_symbol_table_creation(self):
        """测试符号表创建"""
        table = SymbolTable()
        self.assertIsNotNone(table.global_scope)
        self.assertEqual(table.current_scope, table.global_scope)
    
    def test_scope_management(self):
        """测试作用域管理"""
        table = SymbolTable()
        
        func_scope = table.enter_scope(ScopeType.FUNCTION, "测试函数")
        self.assertEqual(table.current_scope, func_scope)
        
        table.exit_scope()
        self.assertEqual(table.current_scope, table.global_scope)
    
    def test_symbol_addition(self):
        """测试符号添加"""
        table = SymbolTable()
        symbol = Symbol(name="测试变量", symbol_type="变量", data_type="整数型")
        
        self.assertTrue(table.add_symbol(symbol))
        self.assertFalse(table.add_symbol(symbol))  # 重复
    
    def test_symbol_lookup(self):
        """测试符号查找"""
        table = SymbolTable()
        table.add_symbol(Symbol(name="变量1", symbol_type="变量"))
        
        self.assertIsNotNone(table.lookup("变量1"))
        self.assertIsNone(table.lookup("变量2"))
    
    def test_analyzer_creation(self):
        """测试分析器创建"""
        analyzer = SemanticAnalyzer()
        self.assertIsNotNone(analyzer.symbol_table)
        self.assertEqual(len(analyzer.errors), 0)
    
    def test_analyze_simple_program(self):
        """测试简单程序分析"""
        ret_type = PrimitiveTypeNode("空型")
        body = BlockStmtNode([])
        func = FunctionDeclNode("main", ret_type, [], body)
        prog = ProgramNode([func])
        
        analyzer = SemanticAnalyzer()
        success = analyzer.analyze(prog)
        self.assertTrue(success)
        self.assertEqual(len(analyzer.errors), 0)
    
    def test_undefined_identifier(self):
        """测试未定义标识符检测"""
        body = BlockStmtNode([
            ExprStmtNode(IdentifierExprNode("未定义变量"))
        ])
        func = FunctionDeclNode("main", PrimitiveTypeNode("空型"), [], body)
        prog = ProgramNode([func])
        
        analyzer = SemanticAnalyzer()
        analyzer.analyze(prog)
        
        self.assertTrue(any(
            e.error_type == "未定义符号" for e in analyzer.errors
        ))
    
    def test_duplicate_function(self):
        """测试重复函数定义"""
        func1 = FunctionDeclNode("foo", PrimitiveTypeNode("空型"), [], BlockStmtNode([]))
        func2 = FunctionDeclNode("foo", PrimitiveTypeNode("空型"), [], BlockStmtNode([]))
        prog = ProgramNode([func1, func2])
        
        analyzer = SemanticAnalyzer()
        analyzer.analyze(prog)
        
        self.assertTrue(any(
            e.error_type == "重复定义" for e in analyzer.errors
        ))
    
    def test_break_outside_loop(self):
        """测试循环外break检测"""
        body = BlockStmtNode([BreakStmtNode()])
        func = FunctionDeclNode("main", PrimitiveTypeNode("空型"), [], body)
        prog = ProgramNode([func])
        
        analyzer = SemanticAnalyzer()
        analyzer.analyze(prog)
        
        self.assertTrue(any(
            e.error_type == "非法跳出" for e in analyzer.errors
        ))
    
    def test_break_inside_loop(self):
        """测试循环内break合法"""
        loop_body = BlockStmtNode([BreakStmtNode()])
        body = BlockStmtNode([
            WhileStmtNode(BoolLiteralNode(True), loop_body)
        ])
        func = FunctionDeclNode("main", PrimitiveTypeNode("空型"), [], body)
        prog = ProgramNode([func])
        
        analyzer = SemanticAnalyzer()
        success = analyzer.analyze(prog)
        self.assertTrue(success)


# ============================================================================
# 测试：类型推导
# ============================================================================

class TestTypeInference(unittest.TestCase):
    """测试类型推导引擎"""
    
    def test_type_env(self):
        """测试类型环境"""
        env = TypeEnv()
        env2 = env.extend("x", BaseType.INT)
        self.assertEqual(env2.lookup("x"), BaseType.INT)
    
    def test_type_variable_creation(self):
        """测试类型变量创建"""
        engine = TypeInferenceEngine()
        var1 = engine.fresh_type_var()
        var2 = engine.fresh_type_var()
        self.assertNotEqual(var1.id, var2.id)
    
    def test_int_literal_inference(self):
        """测试整数字面量推导"""
        engine = TypeInferenceEngine()
        int_lit = IntLiteralNode(42)
        self.assertEqual(engine.infer(int_lit), BaseType.INT)
    
    def test_float_literal_inference(self):
        """测试浮点字面量推导"""
        engine = TypeInferenceEngine()
        float_lit = FloatLiteralNode(3.14)
        self.assertEqual(engine.infer(float_lit), BaseType.FLOAT)
    
    def test_string_literal_inference(self):
        """测试字符串字面量推导"""
        engine = TypeInferenceEngine()
        str_lit = StringLiteralNode("hello")
        self.assertEqual(engine.infer(str_lit), BaseType.STRING)
    
    def test_bool_literal_inference(self):
        """测试布尔字面量推导"""
        engine = TypeInferenceEngine()
        bool_lit = BoolLiteralNode(True)
        self.assertEqual(engine.infer(bool_lit), BaseType.BOOL)
    
    def test_binary_type_inference(self):
        """测试二元表达式推导"""
        engine = TypeInferenceEngine()
        
        left = IntLiteralNode(10)
        right = IntLiteralNode(20)
        binary = BinaryExprNode("+", left, right)
        
        self.assertEqual(engine.infer(binary), BaseType.INT)
    
    def test_comparison_type_inference(self):
        """测试比较表达式推导"""
        engine = TypeInferenceEngine()
        
        left = IntLiteralNode(10)
        right = IntLiteralNode(20)
        binary = BinaryExprNode("<", left, right)
        
        self.assertEqual(engine.infer(binary), BaseType.BOOL)
    
    def test_float_arithmetic_inference(self):
        """测试浮点算术推导"""
        engine = TypeInferenceEngine()
        
        left = FloatLiteralNode(1.5)
        right = IntLiteralNode(2)
        binary = BinaryExprNode("+", left, right)
        
        self.assertEqual(engine.infer(binary), BaseType.FLOAT)
    
    def test_unification(self):
        """测试类型统一"""
        engine = TypeInferenceEngine()
        
        self.assertTrue(engine.unify(BaseType.INT, BaseType.INT))
        
        var = engine.fresh_type_var()
        self.assertTrue(engine.unify(var, BaseType.INT))
    
    def test_unification_failure(self):
        """测试类型统一失败"""
        engine = TypeInferenceEngine()
        self.assertFalse(engine.unify(BaseType.INT, BaseType.STRING))
    
    def test_annotate_ast(self):
        """测试AST类型标注"""
        engine = TypeInferenceEngine()
        
        node = IntLiteralNode(42)
        engine.annotate_ast(node)
        
        self.assertEqual(node.inferred_type, "整数型")
    
    def test_function_type_inference(self):
        """测试函数调用类型推导"""
        engine = TypeInferenceEngine()
        
        call = CallExprNode(
            IdentifierExprNode("foo"),
            [IntLiteralNode(1), IntLiteralNode(2)]
        )
        
        result = engine.infer(call)
        # 应该是一个 TypeVariable（因为 foo 未知）
        self.assertIsInstance(result, TypeVariable)
    
    def test_identifier_inference(self):
        """测试标识符类型推导"""
        engine = TypeInferenceEngine()
        env = TypeEnv(parent=engine.type_env)
        env2 = env.extend("x", BaseType.INT)
        
        ident = IdentifierExprNode("x")
        self.assertEqual(engine.infer(ident, env2), BaseType.INT)
    
    def test_statistics(self):
        """测试统计信息"""
        engine = TypeInferenceEngine()
        engine.infer(IntLiteralNode(42))
        engine.infer(BinaryExprNode("+", IntLiteralNode(1), IntLiteralNode(2)))
        
        stats = engine.get_statistics()
        # BinaryExprNode 推导时递归分析 left 和 right
        self.assertEqual(stats['nodes_analyzed'], 4)


# ============================================================================
# 运行测试
# ============================================================================

def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestASTNodes))
    suite.addTests(loader.loadTestsFromTestCase(TestSemanticAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestTypeInference))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    print(f"✅ 通过: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ 失败: {len(result.failures)}")
    print(f"⚠️  错误: {len(result.errors)}")
    print(f"📋 总计: {result.testsRun}")
    print("=" * 60)
    
    if result.wasSuccessful():
        print("🎉 所有测试通过！")
    else:
        print("❌ 存在失败的测试")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

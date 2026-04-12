//===--- parser_test.cpp - Parser Unit Tests ----------------------------===//
//
// Unit tests for the ZhC recursive descent parser.
// Tests expression, statement, declaration, and type parsing.
//
//===----------------------------------------------------------------------===//

#include "gtest/gtest.h"

#include "zhc/Lexer.h"
#include "zhc/Parser.h"
#include "zhc/Diagnostics.h"
#include "zhc/SourceManager.h"
#include "zhc/ASTContext.h"

#include <memory>

using namespace zhc;

/// Helper class to set up parser test environment
class ParserTestHelper {
public:
  SourceManager SM;
  DiagnosticsEngine Diag;
  ASTContext Context;
  std::unique_ptr<Lexer> Lex;
  std::unique_ptr<Parser> Parse;
  
  ParserTestHelper(llvm::StringRef source)
      : Diag(), Context(SM) {
    Diag.setSourceManager(&SM);
    uint32_t fileID = SM.addString(source, "test.zhc");
    Lex = std::make_unique<Lexer>(source, fileID);
    Parse = std::make_unique<Parser>(*Lex, Diag, Context);
  }
  
  bool hasErrors() const { return Diag.hasErrors(); }
};

//===----------------------------------------------------------------------===//
// Expression Parsing Tests
//===----------------------------------------------------------------------===//

class ExpressionTest : public ::testing::Test {};

TEST_F(ExpressionTest, IntegerLiteral) {
  ParserTestHelper h("42");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::INT_LITERAL);
  auto* lit = static_cast<IntegerLiteralExpr*>(expr.get());
  EXPECT_EQ(lit->Value, 42);
}

TEST_F(ExpressionTest, FloatLiteral) {
  ParserTestHelper h("3.14");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::FLOAT_LITERAL);
  auto* lit = static_cast<FloatLiteralExpr*>(expr.get());
  EXPECT_DOUBLE_EQ(lit->Value, 3.14);
}

TEST_F(ExpressionTest, StringLiteral) {
  ParserTestHelper h("\"hello\"");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::STRING_LITERAL);
  auto* lit = static_cast<StringLiteralExpr*>(expr.get());
  EXPECT_EQ(lit->Value, "hello");
}

TEST_F(ExpressionTest, BoolLiteralTrue) {
  ParserTestHelper h("真");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::BOOL_LITERAL);
  auto* lit = static_cast<BoolLiteralExpr*>(expr.get());
  EXPECT_TRUE(lit->Value);
}

TEST_F(ExpressionTest, BoolLiteralFalse) {
  ParserTestHelper h("假");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::BOOL_LITERAL);
  auto* lit = static_cast<BoolLiteralExpr*>(expr.get());
  EXPECT_FALSE(lit->Value);
}

TEST_F(ExpressionTest, Identifier) {
  ParserTestHelper h("变量名");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::IDENTIFIER_EXPR);
  auto* id = static_cast<IdentifierExpr*>(expr.get());
  EXPECT_EQ(id->Name, "变量名");
}

TEST_F(ExpressionTest, BinaryAdd) {
  ParserTestHelper h("1 + 2");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::BINARY_EXPR);
  auto* bin = static_cast<BinaryOperatorExpr*>(expr.get());
  EXPECT_EQ(bin->Op, TokenKind::plus);
  EXPECT_EQ(bin->LHS->getKind(), ASTNodeKind::INT_LITERAL);
  EXPECT_EQ(bin->RHS->getKind(), ASTNodeKind::INT_LITERAL);
}

TEST_F(ExpressionTest, BinaryPrecedence) {
  // 1 + 2 * 3 should parse as 1 + (2 * 3)
  ParserTestHelper h("1 + 2 * 3");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::BINARY_EXPR);
  auto* add = static_cast<BinaryOperatorExpr*>(expr.get());
  EXPECT_EQ(add->Op, TokenKind::plus);
  
  // LHS is 1
  EXPECT_EQ(add->LHS->getKind(), ASTNodeKind::INT_LITERAL);
  
  // RHS is 2 * 3
  EXPECT_EQ(add->RHS->getKind(), ASTNodeKind::BINARY_EXPR);
  auto* mul = static_cast<BinaryOperatorExpr*>(add->RHS.get());
  EXPECT_EQ(mul->Op, TokenKind::star);
}

TEST_F(ExpressionTest, ParenthesizedExpression) {
  // (1 + 2) * 3 should parse as (1 + 2) * 3
  ParserTestHelper h("(1 + 2) * 3");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::BINARY_EXPR);
  auto* mul = static_cast<BinaryOperatorExpr*>(expr.get());
  EXPECT_EQ(mul->Op, TokenKind::star);
  
  // LHS is (1 + 2)
  EXPECT_EQ(mul->LHS->getKind(), ASTNodeKind::BINARY_EXPR);
  auto* add = static_cast<BinaryOperatorExpr*>(mul->LHS.get());
  EXPECT_EQ(add->Op, TokenKind::plus);
}

TEST_F(ExpressionTest, UnaryMinus) {
  ParserTestHelper h("-42");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::UNARY_EXPR);
  auto* unary = static_cast<UnaryExpr*>(expr.get());
  EXPECT_EQ(unary->Op, TokenKind::minus);
  EXPECT_TRUE(unary->IsPrefix);
  EXPECT_EQ(unary->Operand->getKind(), ASTNodeKind::INT_LITERAL);
}

TEST_F(ExpressionTest, UnaryLogicalNot) {
  ParserTestHelper h("!真");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::UNARY_EXPR);
  auto* unary = static_cast<UnaryExpr*>(expr.get());
  EXPECT_EQ(unary->Op, TokenKind::logical_not);
}

TEST_F(ExpressionTest, CallExpression) {
  ParserTestHelper h("调用(1, 2)");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::CALL_EXPR);
  auto* call = static_cast<CallExpr*>(expr.get());
  EXPECT_EQ(call->Callee->getKind(), ASTNodeKind::IDENTIFIER_EXPR);
  EXPECT_EQ(call->Args.size(), 2u);
}

TEST_F(ExpressionTest, MemberAccess) {
  ParserTestHelper h("对象.字段");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::MEMBER_EXPR);
  auto* member = static_cast<MemberExpr*>(expr.get());
  EXPECT_FALSE(member->IsArrow);  // dot access
  EXPECT_EQ(member->MemberName, "字段");
}

TEST_F(ExpressionTest, ArrowAccess) {
  ParserTestHelper h("指针->字段");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::MEMBER_EXPR);
  auto* member = static_cast<MemberExpr*>(expr.get());
  EXPECT_TRUE(member->IsArrow);  // arrow access
}

TEST_F(ExpressionTest, ArrayAccess) {
  ParserTestHelper h("数组[0]");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::ARRAY_EXPR);
  auto* arr = static_cast<ArrayExpr*>(expr.get());
  EXPECT_EQ(arr->Base->getKind(), ASTNodeKind::IDENTIFIER_EXPR);
  EXPECT_EQ(arr->Index->getKind(), ASTNodeKind::INT_LITERAL);
}

TEST_F(ExpressionTest, Assignment) {
  ParserTestHelper h("x = 42");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::ASSIGN_EXPR);
  auto* assign = static_cast<AssignExpr*>(expr.get());
  EXPECT_EQ(assign->Op, TokenKind::equal);
  EXPECT_EQ(assign->Target->getKind(), ASTNodeKind::IDENTIFIER_EXPR);
  EXPECT_EQ(assign->Value->getKind(), ASTNodeKind::INT_LITERAL);
}

TEST_F(ExpressionTest, CompoundAssignment) {
  ParserTestHelper h("x += 1");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::ASSIGN_EXPR);
  auto* assign = static_cast<AssignExpr*>(expr.get());
  EXPECT_EQ(assign->Op, TokenKind::pluseq);
}

TEST_F(ExpressionTest, ArrayInitializer) {
  ParserTestHelper h("{1, 2, 3}");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::ARRAY_INIT);
  auto* init = static_cast<ArrayInitExpr*>(expr.get());
  EXPECT_EQ(init->Elements.size(), 3u);
}

//===----------------------------------------------------------------------===//
// Statement Parsing Tests
//===----------------------------------------------------------------------===//

class StatementTest : public ::testing::Test {};

TEST_F(StatementTest, BlockStatement) {
  ParserTestHelper h("{ 语句1; 语句2; }");
  auto stmt = h.Parse->parseStatement();
  ASSERT_NE(stmt, nullptr);
  EXPECT_EQ(stmt->getKind(), ASTNodeKind::BLOCK_STMT);
  auto* block = static_cast<BlockStmt*>(stmt.get());
  EXPECT_EQ(block->Statements.size(), 2u);
}

TEST_F(StatementTest, IfStatement) {
  ParserTestHelper h("如果 (真) { 返回 1; }");
  auto stmt = h.Parse->parseStatement();
  ASSERT_NE(stmt, nullptr);
  EXPECT_EQ(stmt->getKind(), ASTNodeKind::IF_STMT);
  auto* ifStmt = static_cast<IfStmt*>(stmt.get());
  EXPECT_EQ(ifStmt->Condition->getKind(), ASTNodeKind::BOOL_LITERAL);
  EXPECT_NE(ifStmt->ThenBranch, nullptr);
  EXPECT_EQ(ifStmt->ElseBranch, nullptr);
}

TEST_F(StatementTest, IfElseStatement) {
  ParserTestHelper h("如果 (真) { 返回 1; } 否则 { 返回 2; }");
  auto stmt = h.Parse->parseStatement();
  ASSERT_NE(stmt, nullptr);
  EXPECT_EQ(stmt->getKind(), ASTNodeKind::IF_STMT);
  auto* ifStmt = static_cast<IfStmt*>(stmt.get());
  EXPECT_NE(ifStmt->ThenBranch, nullptr);
  EXPECT_NE(ifStmt->ElseBranch, nullptr);
}

TEST_F(StatementTest, WhileStatement) {
  ParserTestHelper h("循环 (真) { 语句; }");
  auto stmt = h.Parse->parseStatement();
  ASSERT_NE(stmt, nullptr);
  EXPECT_EQ(stmt->getKind(), ASTNodeKind::WHILE_STMT);
  auto* whileStmt = static_cast<WhileStmt*>(stmt.get());
  EXPECT_EQ(whileStmt->Condition->getKind(), ASTNodeKind::BOOL_LITERAL);
  EXPECT_NE(whileStmt->Body, nullptr);
}

TEST_F(StatementTest, ForStatement) {
  ParserTestHelper h("对于 (变量 i = 0; i < 10; i = i + 1) { 语句; }");
  auto stmt = h.Parse->parseStatement();
  ASSERT_NE(stmt, nullptr);
  EXPECT_EQ(stmt->getKind(), ASTNodeKind::FOR_STMT);
  auto* forStmt = static_cast<ForStmt*>(stmt.get());
  EXPECT_NE(forStmt->Init, nullptr);
  EXPECT_NE(forStmt->Condition, nullptr);
  EXPECT_NE(forStmt->Increment, nullptr);
  EXPECT_NE(forStmt->Body, nullptr);
}

TEST_F(StatementTest, ReturnStatement) {
  ParserTestHelper h("返回 42");
  auto stmt = h.Parse->parseStatement();
  ASSERT_NE(stmt, nullptr);
  EXPECT_EQ(stmt->getKind(), ASTNodeKind::RETURN_STMT);
  auto* ret = static_cast<ReturnStmt*>(stmt.get());
  EXPECT_NE(ret->Value, nullptr);
  EXPECT_EQ(ret->Value->getKind(), ASTNodeKind::INT_LITERAL);
}

TEST_F(StatementTest, ReturnVoid) {
  ParserTestHelper h("返回");
  auto stmt = h.Parse->parseStatement();
  ASSERT_NE(stmt, nullptr);
  EXPECT_EQ(stmt->getKind(), ASTNodeKind::RETURN_STMT);
  auto* ret = static_cast<ReturnStmt*>(stmt.get());
  EXPECT_EQ(ret->Value, nullptr);
}

TEST_F(StatementTest, BreakStatement) {
  ParserTestHelper h("跳出");
  auto stmt = h.Parse->parseStatement();
  ASSERT_NE(stmt, nullptr);
  EXPECT_EQ(stmt->getKind(), ASTNodeKind::BREAK_STMT);
}

TEST_F(StatementTest, ContinueStatement) {
  ParserTestHelper h("继续");
  auto stmt = h.Parse->parseStatement();
  ASSERT_NE(stmt, nullptr);
  EXPECT_EQ(stmt->getKind(), ASTNodeKind::CONTINUE_STMT);
}

TEST_F(StatementTest, SwitchStatement) {
  ParserTestHelper h("选择 (x) { 当 1: 语句1; 默认: 语句2; }");
  auto stmt = h.Parse->parseStatement();
  ASSERT_NE(stmt, nullptr);
  EXPECT_EQ(stmt->getKind(), ASTNodeKind::SWITCH_STMT);
  auto* sw = static_cast<SwitchStmt*>(stmt.get());
  EXPECT_NE(sw->Subject, nullptr);
  EXPECT_EQ(sw->Cases.size(), 2u);
}

TEST_F(StatementTest, TryCatchStatement) {
  ParserTestHelper h("尝试 { 语句; } 捕获 (异常 e) { 处理; }");
  auto stmt = h.Parse->parseStatement();
  ASSERT_NE(stmt, nullptr);
  EXPECT_EQ(stmt->getKind(), ASTNodeKind::TRY_STMT);
  auto* tryStmt = static_cast<TryStmt*>(stmt.get());
  EXPECT_NE(tryStmt->Body, nullptr);
  EXPECT_EQ(tryStmt->CatchClauses.size(), 1u);
}

TEST_F(StatementTest, ThrowStatement) {
  ParserTestHelper h("抛出 \"错误\"");
  auto stmt = h.Parse->parseStatement();
  ASSERT_NE(stmt, nullptr);
  EXPECT_EQ(stmt->getKind(), ASTNodeKind::THROW_STMT);
  auto* throwStmt = static_cast<ThrowStmt*>(stmt.get());
  EXPECT_EQ(throwStmt->Message, "错误");
}

//===----------------------------------------------------------------------===//
// Declaration Parsing Tests
//===----------------------------------------------------------------------===//

class DeclarationTest : public ::testing::Test {};

TEST_F(DeclarationTest, FunctionDeclaration) {
  ParserTestHelper h("函数 加法(参数1, 参数2) { 返回 参数1 + 参数2; }");
  auto decl = h.Parse->parseDeclaration();
  ASSERT_NE(decl, nullptr);
  EXPECT_EQ(decl->getKind(), ASTNodeKind::FUNCTION_DECL);
  auto* func = static_cast<FuncDecl*>(decl.get());
  EXPECT_EQ(func->Name, "加法");
  EXPECT_EQ(func->Params.size(), 2u);
  EXPECT_NE(func->Body, nullptr);
}

TEST_F(DeclarationTest, FunctionWithReturnType) {
  ParserTestHelper h("函数 获取值() : 整数型 { 返回 42; }");
  auto decl = h.Parse->parseDeclaration();
  ASSERT_NE(decl, nullptr);
  EXPECT_EQ(decl->getKind(), ASTNodeKind::FUNCTION_DECL);
  auto* func = static_cast<FuncDecl*>(decl.get());
  EXPECT_NE(func->ReturnType, nullptr);
}

TEST_F(DeclarationTest, VariableDeclaration) {
  ParserTestHelper h("变量 计数 : 整数型 = 0");
  auto decl = h.Parse->parseDeclaration();
  ASSERT_NE(decl, nullptr);
  EXPECT_EQ(decl->getKind(), ASTNodeKind::VARIABLE_DECL);
  auto* var = static_cast<VarDecl*>(decl.get());
  EXPECT_EQ(var->Name, "计数");
  EXPECT_NE(var->Type, nullptr);
  EXPECT_NE(var->Init, nullptr);
  EXPECT_FALSE(var->IsConst);
}

TEST_F(DeclarationTest, ConstDeclaration) {
  ParserTestHelper h("常量 最大值 = 100");
  auto decl = h.Parse->parseDeclaration();
  ASSERT_NE(decl, nullptr);
  EXPECT_EQ(decl->getKind(), ASTNodeKind::VARIABLE_DECL);
  auto* var = static_cast<VarDecl*>(decl.get());
  EXPECT_TRUE(var->IsConst);
}

TEST_F(DeclarationTest, StructDeclaration) {
  ParserTestHelper h("结构体 点 { 整数型 x; 整数型 y; }");
  auto decl = h.Parse->parseDeclaration();
  ASSERT_NE(decl, nullptr);
  EXPECT_EQ(decl->getKind(), ASTNodeKind::STRUCT_DECL);
  auto* structDecl = static_cast<StructDecl*>(decl.get());
  EXPECT_EQ(structDecl->Name, "点");
  EXPECT_EQ(structDecl->Fields.size(), 2u);
}

TEST_F(DeclarationTest, EnumDeclaration) {
  ParserTestHelper h("枚举 颜色 { 红, 绿, 蓝 }");
  auto decl = h.Parse->parseDeclaration();
  ASSERT_NE(decl, nullptr);
  EXPECT_EQ(decl->getKind(), ASTNodeKind::ENUM_DECL);
  auto* enumDecl = static_cast<EnumDecl*>(decl.get());
  EXPECT_EQ(enumDecl->Name, "颜色");
  EXPECT_EQ(enumDecl->Constants.size(), 3u);
}

TEST_F(DeclarationTest, ImportDeclaration) {
  ParserTestHelper h("导入 模块名 : 符号1, 符号2");
  auto decl = h.Parse->parseDeclaration();
  ASSERT_NE(decl, nullptr);
  EXPECT_EQ(decl->getKind(), ASTNodeKind::IMPORT_DECL);
  auto* import = static_cast<ImportDecl*>(decl.get());
  EXPECT_EQ(import->ModuleName, "模块名");
  EXPECT_EQ(import->Symbols.size(), 2u);
}

TEST_F(DeclarationTest, ModuleDeclaration) {
  ParserTestHelper h("模块 我的模块");
  auto decl = h.Parse->parseDeclaration();
  ASSERT_NE(decl, nullptr);
  EXPECT_EQ(decl->getKind(), ASTNodeKind::MODULE_DECL);
  auto* mod = static_cast<ModuleDecl*>(decl.get());
  EXPECT_EQ(mod->Name, "我的模块");
}

//===----------------------------------------------------------------------===//
// Type Parsing Tests
//===----------------------------------------------------------------------===//

class TypeTest : public ::testing::Test {};

TEST_F(TypeTest, PrimitiveType) {
  ParserTestHelper h("整数型");
  auto type = h.Parse->parseType();
  ASSERT_NE(type, nullptr);
  EXPECT_EQ(type->getKind(), ASTNodeKind::PRIMITIVE_TYPE);
  auto* prim = static_cast<PrimitiveTypeNode*>(type.get());
  EXPECT_EQ(prim->PrimKind, TypeKind::Int32);
}

TEST_F(TypeTest, FloatType) {
  ParserTestHelper h("浮点型");
  auto type = h.Parse->parseType();
  ASSERT_NE(type, nullptr);
  EXPECT_EQ(type->getKind(), ASTNodeKind::PRIMITIVE_TYPE);
  auto* prim = static_cast<PrimitiveTypeNode*>(type.get());
  EXPECT_EQ(prim->PrimKind, TypeKind::Float64);
}

TEST_F(TypeTest, PointerType) {
  ParserTestHelper h("整数型 *");
  auto type = h.Parse->parseType();
  ASSERT_NE(type, nullptr);
  EXPECT_EQ(type->getKind(), ASTNodeKind::POINTER_TYPE);
  auto* ptr = static_cast<PointerTypeNode*>(type.get());
  EXPECT_EQ(ptr->Pointee->getKind(), ASTNodeKind::PRIMITIVE_TYPE);
}

TEST_F(TypeTest, ArrayType) {
  ParserTestHelper h("整数型 [10]");
  auto type = h.Parse->parseType();
  ASSERT_NE(type, nullptr);
  EXPECT_EQ(type->getKind(), ASTNodeKind::ARRAY_TYPE);
  auto* arr = static_cast<ArrayTypeNode*>(type.get());
  EXPECT_EQ(arr->ElementType->getKind(), ASTNodeKind::PRIMITIVE_TYPE);
  EXPECT_NE(arr->Size, nullptr);
}

//===----------------------------------------------------------------------===//
// Translation Unit Tests
//===----------------------------------------------------------------------===//

class TranslationUnitTest : public ::testing::Test {};

TEST_F(TranslationUnitTest, EmptyFile) {
  ParserTestHelper h("");
  auto unit = h.Parse->parseTranslationUnit();
  ASSERT_NE(unit, nullptr);
  EXPECT_EQ(unit->Decls.size(), 0u);
}

TEST_F(TranslationUnitTest, MultipleDeclarations) {
  ParserTestHelper h("变量 x = 1; 变量 y = 2; 函数 主() { 返回 x + y; }");
  auto unit = h.Parse->parseTranslationUnit();
  ASSERT_NE(unit, nullptr);
  EXPECT_EQ(unit->Decls.size(), 3u);
}

//===----------------------------------------------------------------------===//
// Error Recovery Tests
//===----------------------------------------------------------------------===//

class ErrorRecoveryTest : public ::testing::Test {};

TEST_F(ErrorRecoveryTest, MissingSemicolon) {
  // Parser is lenient about missing semicolons (consumeIf pattern)
  // Both declarations should still be parsed
  ParserTestHelper h("变量 x = 1 变量 y = 2");
  auto unit = h.Parse->parseTranslationUnit();
  EXPECT_EQ(unit->Decls.size(), 2u);
}

TEST_F(ErrorRecoveryTest, InvalidToken) {
  ParserTestHelper h("@@ 变量 x = 1");
  auto unit = h.Parse->parseTranslationUnit();
  // Should skip invalid token and parse declaration
  EXPECT_GE(unit->Decls.size(), 1u);
  EXPECT_TRUE(h.hasErrors());
}

TEST_F(ErrorRecoveryTest, MissingClosingBrace) {
  // Parser gracefully handles EOF in block (synchronizes at EOF)
  // No explicit error for missing closing brace at EOF
  ParserTestHelper h("函数 f() { 语句 ");
  auto decl = h.Parse->parseDeclaration();
  EXPECT_NE(decl, nullptr);
}

//===----------------------------------------------------------------------===//
// Precedence Tests (Pratt Parser)
//===----------------------------------------------------------------------===//

class PrecedenceTest : public ::testing::Test {};

TEST_F(PrecedenceTest, MultiplicationHigherThanAddition) {
  // 1 + 2 * 3 => 1 + (2 * 3)
  ParserTestHelper h("1 + 2 * 3");
  auto expr = h.Parse->parseExpression();
  auto* add = static_cast<BinaryOperatorExpr*>(expr.get());
  EXPECT_EQ(add->Op, TokenKind::plus);
  EXPECT_EQ(add->RHS->getKind(), ASTNodeKind::BINARY_EXPR);
}

TEST_F(PrecedenceTest, LogicalAndHigherThanLogicalOr) {
  // a || b && c => a || (b && c)
  ParserTestHelper h("a || b && c");
  auto expr = h.Parse->parseExpression();
  auto* orExpr = static_cast<BinaryOperatorExpr*>(expr.get());
  EXPECT_EQ(orExpr->Op, TokenKind::logical_or);
  EXPECT_EQ(orExpr->RHS->getKind(), ASTNodeKind::BINARY_EXPR);
  auto* andExpr = static_cast<BinaryOperatorExpr*>(orExpr->RHS.get());
  EXPECT_EQ(andExpr->Op, TokenKind::logical_and);
}

TEST_F(PrecedenceTest, ComparisonHigherThanLogicalAnd) {
  // a && b < c => a && (b < c)
  ParserTestHelper h("a && b < c");
  auto expr = h.Parse->parseExpression();
  auto* andExpr = static_cast<BinaryOperatorExpr*>(expr.get());
  EXPECT_EQ(andExpr->Op, TokenKind::logical_and);
  EXPECT_EQ(andExpr->RHS->getKind(), ASTNodeKind::BINARY_EXPR);
}

TEST_F(PrecedenceTest, AssignmentRightAssociative) {
  // a = b = c => a = (b = c)
  ParserTestHelper h("a = b = c");
  auto expr = h.Parse->parseExpression();
  auto* outer = static_cast<AssignExpr*>(expr.get());
  EXPECT_EQ(outer->Op, TokenKind::equal);
  EXPECT_EQ(outer->Value->getKind(), ASTNodeKind::ASSIGN_EXPR);
  auto* inner = static_cast<AssignExpr*>(outer->Value.get());
  EXPECT_EQ(inner->Op, TokenKind::equal);
}

TEST_F(PrecedenceTest, ShiftOperators) {
  // a << b should parse as (a << b)
  ParserTestHelper h("a << b");
  auto expr = h.Parse->parseExpression();
  ASSERT_NE(expr, nullptr);
  EXPECT_EQ(expr->getKind(), ASTNodeKind::BINARY_EXPR);
  auto* shl = static_cast<BinaryOperatorExpr*>(expr.get());
  EXPECT_EQ(shl->Op, TokenKind::shl);
}
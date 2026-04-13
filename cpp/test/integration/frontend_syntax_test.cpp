//===--- frontend_syntax_test.cpp - Frontend Syntax Integration Tests -----===//
//
// Integration tests for frontend syntax correctness.
// Tests complete programs through Lexer → Parser pipeline.
//
//===----------------------------------------------------------------------===//

#include "gtest/gtest.h"

#include "zhc/Lexer.h"
#include "zhc/Parser.h"
#include "zhc/Diagnostics.h"
#include "zhc/SourceManager.h"
#include "zhc/ASTContext.h"

#include <memory>
#include <iostream>

using namespace zhc;

namespace {

/// Integration test helper - minimal setup
class FrontendIntegrationTest : public ::testing::Test {
protected:
  /// Parse source string (no Sema, no node counting)
  std::unique_ptr<TranslationUnit> parse(const std::string& source) {
    SourceManager SM;
    ASTContext Context(SM);
    DiagnosticsEngine Diags;
    Diags.setSourceManager(&SM);
    uint32_t fileID = SM.addString(source, "test.zhc");
    
    Lexer lexer(source, fileID);
    Parser parser(lexer, Diags, Context);
    return parser.parseTranslationUnit();
  }
};

//===----------------------------------------------------------------------===//
// Basic Parsing Tests
//===----------------------------------------------------------------------===//

TEST_F(FrontendIntegrationTest, EmptyProgram) {
  auto ast = parse("");
  ASSERT_TRUE(ast != nullptr);
  EXPECT_EQ(ast->Decls.size(), 0u);
}

TEST_F(FrontendIntegrationTest, SingleFunction) {
  auto ast = parse("函数 测试() { 返回 42; }");
  ASSERT_TRUE(ast != nullptr);
  ASSERT_GE(ast->Decls.size(), 1u);
  EXPECT_EQ(ast->Decls[0]->getKind(), ASTNodeKind::FUNCTION_DECL);
}

TEST_F(FrontendIntegrationTest, FunctionWithReturnType) {
  auto ast = parse("函数 加法(a : 整数型, b : 整数型) : 整数型 { 返回 a + b; }");
  ASSERT_TRUE(ast != nullptr);
  ASSERT_GE(ast->Decls.size(), 1u);
}

TEST_F(FrontendIntegrationTest, VariableDeclaration) {
  auto ast = parse("变量 x : 整数型 = 10;");
  ASSERT_TRUE(ast != nullptr);
  ASSERT_GE(ast->Decls.size(), 1u);
}

TEST_F(FrontendIntegrationTest, MultipleDeclarations) {
  auto ast = parse(
    "变量 x = 1;\n"
    "变量 y = 2;\n"
    "函数 加法() { 返回 x + y; }"
  );
  ASSERT_TRUE(ast != nullptr);
  EXPECT_EQ(ast->Decls.size(), 3u);
}

TEST_F(FrontendIntegrationTest, NestedBlocks) {
  auto ast = parse(
    "函数 深层嵌套() {"
    "  如果 (真) {"
    "    循环 (假) {"
    "      返回 1;"
    "    }"
    "  }"
    "}"
  );
  ASSERT_TRUE(ast != nullptr);
}

TEST_F(FrontendIntegrationTest, StructDeclaration) {
  auto ast = parse(
    "结构体 点 {"
    "  整数型 x;"
    "  整数型 y;"
    "}"
  );
  ASSERT_TRUE(ast != nullptr);
  ASSERT_GE(ast->Decls.size(), 1u);
  EXPECT_EQ(ast->Decls[0]->getKind(), ASTNodeKind::STRUCT_DECL);
}

TEST_F(FrontendIntegrationTest, EnumDeclaration) {
  auto ast = parse(
    "枚举 颜色 {"
    "  红,"
    "  绿,"
    "  蓝"
    "}"
  );
  ASSERT_TRUE(ast != nullptr);
  ASSERT_GE(ast->Decls.size(), 1u);
  EXPECT_EQ(ast->Decls[0]->getKind(), ASTNodeKind::ENUM_DECL);
}

TEST_F(FrontendIntegrationTest, ComplexExpressions) {
  auto ast = parse(
    "函数 表达式测试() : 整数型 {"
    "  变量 a = 1 + 2 * 3 - 4 / 2;"
    "  变量 b = (a > 0) && (a < 10);"
    "  返回 a;"
    "}"
  );
  ASSERT_TRUE(ast != nullptr);
  EXPECT_EQ(ast->Decls.size(), 1u);
}

TEST_F(FrontendIntegrationTest, ForLoop) {
  auto ast = parse(
    "函数 循环测试() {"
    "  对于 (变量 i = 0; i < 10; i = i + 1) {"
    "    i;"
    "  }"
    "}"
  );
  ASSERT_TRUE(ast != nullptr);
}

TEST_F(FrontendIntegrationTest, WhileLoop) {
  auto ast = parse(
    "函数 当循环测试() {"
    "  变量 i = 0;"
    "  循环 (i < 10) {"
    "    i = i + 1;"
    "  }"
    "}"
  );
  ASSERT_TRUE(ast != nullptr);
}

TEST_F(FrontendIntegrationTest, SwitchStatement) {
  auto ast = parse(
    "函数 开关测试(x : 整数型) {"
    "  选择 (x) {"
    "    情况 1: x; 跳出;"
    "    情况 2: x; 跳出;"
    "    默认: x;"
    "  }"
    "}"
  );
  ASSERT_TRUE(ast != nullptr);
}

TEST_F(FrontendIntegrationTest, TryCatch) {
  auto ast = parse(
    "函数 异常测试() {"
    "  尝试 {"
    "    抛出(\"错误\");"
    "  } 捕获 {"
    "    1;"
    "  } 最终 {"
    "    2;"
    "  }"
    "}"
  );
  ASSERT_TRUE(ast != nullptr);
}

}  // anonymous namespace

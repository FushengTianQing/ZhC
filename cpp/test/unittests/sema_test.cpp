//===--- sema_test.cpp - Semantic Analysis Unit Tests --------------------===//
//
// Unit tests for the ZhC semantic analyzer.
// Tests unused variable detection with _ and ! support.
//
//===----------------------------------------------------------------------===//

#include "zhc/Sema.h"
#include "zhc/AST.h"
#include "zhc/ASTContext.h"
#include "zhc/Diagnostics.h"
#include "zhc/SourceManager.h"

#include "gtest/gtest.h"

#include <memory>

using namespace zhc;

namespace {

/// Test helper to build AST nodes and run Sema
class SemaTest : public ::testing::Test {
protected:
  DiagnosticsEngine Diags;
  
  void SetUp() override {
    Diags.clear();
  }
  
  /// Run Sema analysis on a translation unit
  bool analyze(TranslationUnit* unit) {
    Sema sema(Diags);
    return sema.analyze(unit);
  }
  
  /// Count warnings containing the given substring
  unsigned countWarnings(const std::string& substr) {
    unsigned count = 0;
    for (const auto& diag : Diags.getDiagnostics()) {
      if (diag.Level == DiagnosticLevel::Warning && 
          diag.Message.find(substr) != std::string::npos) {
        ++count;
      }
    }
    return count;
  }
  
  /// Check if any warning contains the given substring
  bool hasWarning(const std::string& substr) {
    return countWarnings(substr) > 0;
  }
};

//===----------------------------------------------------------------------===//
// Unused Variable Detection Tests
//===----------------------------------------------------------------------===//

TEST_F(SemaTest, UnusedVariableWarning) {
  // func foo() { var x: int = 5; }
  auto unit = std::make_unique<TranslationUnit>();
  
  auto funcBody = std::make_unique<BlockStmt>();
  auto varType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto initVal = std::make_unique<IntegerLiteralExpr>(5);
  auto varDecl = std::make_unique<VarDecl>(
      "x", std::move(varType), std::move(initVal));
  funcBody->Statements.push_back(std::move(varDecl));
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Void);
  auto func = std::make_unique<FuncDecl>(
      "foo", std::move(retType), 
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      std::move(funcBody));
  unit->Decls.push_back(std::move(func));
  
  EXPECT_TRUE(analyze(unit.get()));
  EXPECT_TRUE(hasWarning("x"));
}

TEST_F(SemaTest, UsedVariableNoWarning) {
  // func foo() { var x: int = 5; return x; }
  auto unit = std::make_unique<TranslationUnit>();
  
  auto funcBody = std::make_unique<BlockStmt>();
  auto varType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto initVal = std::make_unique<IntegerLiteralExpr>(5);
  auto varDecl = std::make_unique<VarDecl>(
      "x", std::move(varType), std::move(initVal));
  funcBody->Statements.push_back(std::move(varDecl));
  
  auto retVal = std::make_unique<IdentifierExpr>("x");
  auto retStmt = std::make_unique<ReturnStmt>(std::move(retVal));
  funcBody->Statements.push_back(std::move(retStmt));
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto func = std::make_unique<FuncDecl>(
      "foo", std::move(retType),
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      std::move(funcBody));
  unit->Decls.push_back(std::move(func));
  
  EXPECT_TRUE(analyze(unit.get()));
  EXPECT_FALSE(hasWarning("x"));
}

TEST_F(SemaTest, UnderscoreVariableNoWarning) {
  // func foo() { var _: int = compute(); }
  auto unit = std::make_unique<TranslationUnit>();
  
  auto funcBody = std::make_unique<BlockStmt>();
  auto varType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto callee = std::make_unique<IdentifierExpr>("compute");
  auto callExpr = std::make_unique<CallExpr>(
      std::move(callee),
      llvm::SmallVector<std::unique_ptr<ExprNode>, 0>());
  auto varDecl = std::make_unique<VarDecl>(
      "_", std::move(varType), std::move(callExpr));
  funcBody->Statements.push_back(std::move(varDecl));
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Void);
  auto func = std::make_unique<FuncDecl>(
      "foo", std::move(retType),
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      std::move(funcBody));
  unit->Decls.push_back(std::move(func));
  
  EXPECT_TRUE(analyze(unit.get()));
  EXPECT_FALSE(hasWarning("_"));
}

TEST_F(SemaTest, DiscardedVariableNoWarning) {
  // func foo() { var result: int = compute() !; }
  auto unit = std::make_unique<TranslationUnit>();
  
  auto funcBody = std::make_unique<BlockStmt>();
  auto varType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto callee = std::make_unique<IdentifierExpr>("compute");
  auto callExpr = std::make_unique<CallExpr>(
      std::move(callee),
      llvm::SmallVector<std::unique_ptr<ExprNode>, 0>());
  auto varDecl = std::make_unique<VarDecl>(
      "result", std::move(varType), std::move(callExpr),
      false, false, false, true);  // isDiscarded = true
  funcBody->Statements.push_back(std::move(varDecl));
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Void);
  auto func = std::make_unique<FuncDecl>(
      "foo", std::move(retType),
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      std::move(funcBody));
  unit->Decls.push_back(std::move(func));
  
  EXPECT_TRUE(analyze(unit.get()));
  EXPECT_FALSE(hasWarning("result"));
}

TEST_F(SemaTest, MultipleUnusedVariables) {
  // func foo() { var a: int = 1; var b: int = 2; var c: int = 3; }
  auto unit = std::make_unique<TranslationUnit>();
  
  auto funcBody = std::make_unique<BlockStmt>();
  
  for (const char* name : {"a", "b", "c"}) {
    auto varType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
    auto initVal = std::make_unique<IntegerLiteralExpr>(1);
    auto varDecl = std::make_unique<VarDecl>(
        name, std::move(varType), std::move(initVal));
    funcBody->Statements.push_back(std::move(varDecl));
  }
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Void);
  auto func = std::make_unique<FuncDecl>(
      "foo", std::move(retType),
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      std::move(funcBody));
  unit->Decls.push_back(std::move(func));
  
  EXPECT_TRUE(analyze(unit.get()));
  EXPECT_EQ(countWarnings("未使用的局部变量"), 3u);
}

TEST_F(SemaTest, UsedAndUnusedMixed) {
  // func foo() { var a: int = 1; var b: int = a; }
  // a is used, b is unused
  auto unit = std::make_unique<TranslationUnit>();
  
  auto funcBody = std::make_unique<BlockStmt>();
  
  auto varType1 = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto initVal1 = std::make_unique<IntegerLiteralExpr>(1);
  auto varDecl1 = std::make_unique<VarDecl>(
      "a", std::move(varType1), std::move(initVal1));
  funcBody->Statements.push_back(std::move(varDecl1));
  
  auto varType2 = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto initVal2 = std::make_unique<IdentifierExpr>("a");
  auto varDecl2 = std::make_unique<VarDecl>(
      "b", std::move(varType2), std::move(initVal2));
  funcBody->Statements.push_back(std::move(varDecl2));
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Void);
  auto func = std::make_unique<FuncDecl>(
      "foo", std::move(retType),
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      std::move(funcBody));
  unit->Decls.push_back(std::move(func));
  
  EXPECT_TRUE(analyze(unit.get()));
  EXPECT_FALSE(hasWarning("'a'"));  // a is used
  EXPECT_TRUE(hasWarning("'b'"));   // b is unused
}

TEST_F(SemaTest, VariableUsedInBinaryExpr) {
  // func foo() { var x: int = 5; return x + 1; }
  auto unit = std::make_unique<TranslationUnit>();
  
  auto funcBody = std::make_unique<BlockStmt>();
  
  auto varType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto initVal = std::make_unique<IntegerLiteralExpr>(5);
  auto varDecl = std::make_unique<VarDecl>(
      "x", std::move(varType), std::move(initVal));
  funcBody->Statements.push_back(std::move(varDecl));
  
  auto lhs = std::make_unique<IdentifierExpr>("x");
  auto rhs = std::make_unique<IntegerLiteralExpr>(1);
  auto binOp = std::make_unique<BinaryOperatorExpr>(
      TokenKind::plus, std::move(lhs), std::move(rhs));
  auto retStmt = std::make_unique<ReturnStmt>(std::move(binOp));
  funcBody->Statements.push_back(std::move(retStmt));
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto func = std::make_unique<FuncDecl>(
      "foo", std::move(retType),
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      std::move(funcBody));
  unit->Decls.push_back(std::move(func));
  
  EXPECT_TRUE(analyze(unit.get()));
  EXPECT_FALSE(hasWarning("x"));
}

TEST_F(SemaTest, VariableUsedInCallExpr) {
  // func foo() { var x: int = 5; bar(x); }
  auto unit = std::make_unique<TranslationUnit>();
  
  auto funcBody = std::make_unique<BlockStmt>();
  
  auto varType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto initVal = std::make_unique<IntegerLiteralExpr>(5);
  auto varDecl = std::make_unique<VarDecl>(
      "x", std::move(varType), std::move(initVal));
  funcBody->Statements.push_back(std::move(varDecl));
  
  auto callee = std::make_unique<IdentifierExpr>("bar");
  auto arg = std::make_unique<IdentifierExpr>("x");
  llvm::SmallVector<std::unique_ptr<ExprNode>, 1> args;
  args.push_back(std::move(arg));
  auto callExpr = std::make_unique<CallExpr>(std::move(callee), std::move(args));
  auto exprStmt = std::make_unique<ExprStmt>(std::move(callExpr));
  funcBody->Statements.push_back(std::move(exprStmt));
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Void);
  auto func = std::make_unique<FuncDecl>(
      "foo", std::move(retType),
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      std::move(funcBody));
  unit->Decls.push_back(std::move(func));
  
  EXPECT_TRUE(analyze(unit.get()));
  EXPECT_FALSE(hasWarning("x"));
}

TEST_F(SemaTest, VariableUsedInIfCondition) {
  // func foo() { var x: int = 5; if (x > 0) {} }
  auto unit = std::make_unique<TranslationUnit>();
  
  auto funcBody = std::make_unique<BlockStmt>();
  
  auto varType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto initVal = std::make_unique<IntegerLiteralExpr>(5);
  auto varDecl = std::make_unique<VarDecl>(
      "x", std::move(varType), std::move(initVal));
  funcBody->Statements.push_back(std::move(varDecl));
  
  auto lhs = std::make_unique<IdentifierExpr>("x");
  auto rhs = std::make_unique<IntegerLiteralExpr>(0);
  auto cond = std::make_unique<BinaryOperatorExpr>(
      TokenKind::gt, std::move(lhs), std::move(rhs));
  auto thenBlock = std::make_unique<BlockStmt>();
  auto ifStmt = std::make_unique<IfStmt>(
      std::move(cond), std::move(thenBlock));
  funcBody->Statements.push_back(std::move(ifStmt));
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Void);
  auto func = std::make_unique<FuncDecl>(
      "foo", std::move(retType),
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      std::move(funcBody));
  unit->Decls.push_back(std::move(func));
  
  EXPECT_TRUE(analyze(unit.get()));
  EXPECT_FALSE(hasWarning("x"));
}

TEST_F(SemaTest, VariableUsedInWhileCondition) {
  // func foo() { var x: int = 5; while (x > 0) {} }
  auto unit = std::make_unique<TranslationUnit>();
  
  auto funcBody = std::make_unique<BlockStmt>();
  
  auto varType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto initVal = std::make_unique<IntegerLiteralExpr>(5);
  auto varDecl = std::make_unique<VarDecl>(
      "x", std::move(varType), std::move(initVal));
  funcBody->Statements.push_back(std::move(varDecl));
  
  auto lhs = std::make_unique<IdentifierExpr>("x");
  auto rhs = std::make_unique<IntegerLiteralExpr>(0);
  auto cond = std::make_unique<BinaryOperatorExpr>(
      TokenKind::gt, std::move(lhs), std::move(rhs));
  auto body = std::make_unique<BlockStmt>();
  auto whileStmt = std::make_unique<WhileStmt>(
      std::move(cond), std::move(body));
  funcBody->Statements.push_back(std::move(whileStmt));
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Void);
  auto func = std::make_unique<FuncDecl>(
      "foo", std::move(retType),
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      std::move(funcBody));
  unit->Decls.push_back(std::move(func));
  
  EXPECT_TRUE(analyze(unit.get()));
  EXPECT_FALSE(hasWarning("x"));
}

TEST_F(SemaTest, NullFunctionNoCrash) {
  auto unit = std::make_unique<TranslationUnit>();
  EXPECT_TRUE(analyze(unit.get()));
}

TEST_F(SemaTest, FunctionWithNullBody) {
  auto unit = std::make_unique<TranslationUnit>();
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Void);
  auto func = std::make_unique<FuncDecl>(
      "foo", std::move(retType),
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      nullptr);  // No body
  unit->Decls.push_back(std::move(func));
  
  EXPECT_TRUE(analyze(unit.get()));
  EXPECT_EQ(Diags.getWarningCount(), 0u);
}

TEST_F(SemaTest, VarDeclShouldSuppressUnusedWarningUnderscore) {
  auto varType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto initVal = std::make_unique<IntegerLiteralExpr>(42);
  auto varDecl = std::make_unique<VarDecl>(
      "_", std::move(varType), std::move(initVal));
  
  EXPECT_TRUE(varDecl->shouldSuppressUnusedWarning());
}

TEST_F(SemaTest, VarDeclShouldSuppressUnusedWarningDiscarded) {
  auto varType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto initVal = std::make_unique<IntegerLiteralExpr>(42);
  auto varDecl = std::make_unique<VarDecl>(
      "result", std::move(varType), std::move(initVal),
      false, false, false, true);  // isDiscarded = true
  
  EXPECT_TRUE(varDecl->shouldSuppressUnusedWarning());
}

TEST_F(SemaTest, VarDeclNormalNotSuppressed) {
  auto varType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto initVal = std::make_unique<IntegerLiteralExpr>(42);
  auto varDecl = std::make_unique<VarDecl>(
      "x", std::move(varType), std::move(initVal));
  
  EXPECT_FALSE(varDecl->shouldSuppressUnusedWarning());
}

//===----------------------------------------------------------------------===//
// Initialization Tracking Tests (S02 Framework)
//===----------------------------------------------------------------------===//

TEST_F(SemaTest, UninitializedVarUsedTriggersError) {
  // func foo() { var x: int; return x; }
  // x is declared without initializer and used → error
  auto unit = std::make_unique<TranslationUnit>();
  
  auto funcBody = std::make_unique<BlockStmt>();
  
  // var x: int;  (no initializer)
  auto varType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto varDecl = std::make_unique<VarDecl>("x", std::move(varType), nullptr);
  funcBody->Statements.push_back(std::move(varDecl));
  
  // return x;
  auto retVal = std::make_unique<IdentifierExpr>("x");
  auto retStmt = std::make_unique<ReturnStmt>(std::move(retVal));
  funcBody->Statements.push_back(std::move(retStmt));
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto func = std::make_unique<FuncDecl>(
      "foo", std::move(retType),
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      std::move(funcBody));
  unit->Decls.push_back(std::move(func));
  
  EXPECT_FALSE(analyze(unit.get()));  // Should fail due to error
  // Check for uninitialized error
  bool hasUninitError = false;
  for (const auto& diag : Diags.getDiagnostics()) {
    if (diag.Message.find("未初始化") != std::string::npos) {
      hasUninitError = true;
      break;
    }
  }
  EXPECT_TRUE(hasUninitError);
}

TEST_F(SemaTest, InitializedVarUsedNoError) {
  // func foo() { var x: int = 5; return x; }
  // x is declared with initializer → no error
  auto unit = std::make_unique<TranslationUnit>();
  
  auto funcBody = std::make_unique<BlockStmt>();
  
  // var x: int = 5;
  auto varType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto initVal = std::make_unique<IntegerLiteralExpr>(5);
  auto varDecl = std::make_unique<VarDecl>(
      "x", std::move(varType), std::move(initVal));
  funcBody->Statements.push_back(std::move(varDecl));
  
  // return x;
  auto retVal = std::make_unique<IdentifierExpr>("x");
  auto retStmt = std::make_unique<ReturnStmt>(std::move(retVal));
  funcBody->Statements.push_back(std::move(retStmt));
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto func = std::make_unique<FuncDecl>(
      "foo", std::move(retType),
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      std::move(funcBody));
  unit->Decls.push_back(std::move(func));
  
  EXPECT_TRUE(analyze(unit.get()));
  // No uninitialized errors
  for (const auto& diag : Diags.getDiagnostics()) {
    EXPECT_TRUE(diag.Message.find("未初始化") == std::string::npos)
        << "Unexpected uninitialized error: " << diag.Message;
  }
}

TEST_F(SemaTest, VarInitializedViaAssignmentNoError) {
  // func foo() { var x: int; x = 5; return x; }
  // x is declared uninitialized, then assigned → no error
  auto unit = std::make_unique<TranslationUnit>();
  
  auto funcBody = std::make_unique<BlockStmt>();
  
  // var x: int;  (no initializer)
  auto varType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto varDecl = std::make_unique<VarDecl>("x", std::move(varType), nullptr);
  funcBody->Statements.push_back(std::move(varDecl));
  
  // x = 5;
  auto target = std::make_unique<IdentifierExpr>("x");
  auto value = std::make_unique<IntegerLiteralExpr>(5);
  auto assign = std::make_unique<AssignExpr>(
      TokenKind::equal, std::move(target), std::move(value));
  auto exprStmt = std::make_unique<ExprStmt>(std::move(assign));
  funcBody->Statements.push_back(std::move(exprStmt));
  
  // return x;
  auto retVal = std::make_unique<IdentifierExpr>("x");
  auto retStmt = std::make_unique<ReturnStmt>(std::move(retVal));
  funcBody->Statements.push_back(std::move(retStmt));
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto func = std::make_unique<FuncDecl>(
      "foo", std::move(retType),
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      std::move(funcBody));
  unit->Decls.push_back(std::move(func));
  
  EXPECT_TRUE(analyze(unit.get()));
  // No uninitialized errors
  for (const auto& diag : Diags.getDiagnostics()) {
    EXPECT_TRUE(diag.Message.find("未初始化") == std::string::npos)
        << "Unexpected uninitialized error: " << diag.Message;
  }
}

TEST_F(SemaTest, UninitializedVarNotUsedNoError) {
  // func foo() { var x: int; }  // x is declared but never used
  // Only unused warning, no uninitialized error
  auto unit = std::make_unique<TranslationUnit>();
  
  auto funcBody = std::make_unique<BlockStmt>();
  
  // var x: int;  (no initializer, no use)
  auto varType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto varDecl = std::make_unique<VarDecl>("x", std::move(varType), nullptr);
  funcBody->Statements.push_back(std::move(varDecl));
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Void);
  auto func = std::make_unique<FuncDecl>(
      "foo", std::move(retType),
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      std::move(funcBody));
  unit->Decls.push_back(std::move(func));
  
  EXPECT_TRUE(analyze(unit.get()));
  // Should have unused warning but no uninitialized error
  EXPECT_TRUE(hasWarning("x"));  // unused warning
  for (const auto& diag : Diags.getDiagnostics()) {
    EXPECT_TRUE(diag.Message.find("未初始化") == std::string::npos)
        << "Unexpected uninitialized error for unused variable: " << diag.Message;
  }
}

TEST_F(SemaTest, MultipleVarsMixedInitState) {
  // func foo() {
  //   var a: int = 1;      // initialized
  //   var b: int;           // uninitialized
  //   var c: int = 3;      // initialized
  //   return a + c;         // uses a and c (both initialized), b unused
  // }
  auto unit = std::make_unique<TranslationUnit>();
  
  auto funcBody = std::make_unique<BlockStmt>();
  
  // var a: int = 1;
  auto typeA = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto initA = std::make_unique<IntegerLiteralExpr>(1);
  auto declA = std::make_unique<VarDecl>("a", std::move(typeA), std::move(initA));
  funcBody->Statements.push_back(std::move(declA));
  
  // var b: int;  (no init)
  auto typeB = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto declB = std::make_unique<VarDecl>("b", std::move(typeB), nullptr);
  funcBody->Statements.push_back(std::move(declB));
  
  // var c: int = 3;
  auto typeC = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto initC = std::make_unique<IntegerLiteralExpr>(3);
  auto declC = std::make_unique<VarDecl>("c", std::move(typeC), std::move(initC));
  funcBody->Statements.push_back(std::move(declC));
  
  // return a + c;
  auto lhs = std::make_unique<IdentifierExpr>("a");
  auto rhs = std::make_unique<IdentifierExpr>("c");
  auto binOp = std::make_unique<BinaryOperatorExpr>(
      TokenKind::plus, std::move(lhs), std::move(rhs));
  auto retStmt = std::make_unique<ReturnStmt>(std::move(binOp));
  funcBody->Statements.push_back(std::move(retStmt));
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto func = std::make_unique<FuncDecl>(
      "foo", std::move(retType),
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      std::move(funcBody));
  unit->Decls.push_back(std::move(func));
  
  EXPECT_TRUE(analyze(unit.get()));
  // b should have unused warning, but no uninitialized error
  EXPECT_TRUE(hasWarning("'b'"));
  for (const auto& diag : Diags.getDiagnostics()) {
    EXPECT_TRUE(diag.Message.find("未初始化") == std::string::npos)
        << "Unexpected uninitialized error: " << diag.Message;
  }
}

TEST_F(SemaTest, UninitVarUsedInBinaryExpr) {
  // func foo() { var x: int; return x + 1; }
  // x used without initialization → error
  auto unit = std::make_unique<TranslationUnit>();
  
  auto funcBody = std::make_unique<BlockStmt>();
  
  auto varType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto varDecl = std::make_unique<VarDecl>("x", std::move(varType), nullptr);
  funcBody->Statements.push_back(std::move(varDecl));
  
  auto lhs = std::make_unique<IdentifierExpr>("x");
  auto rhs = std::make_unique<IntegerLiteralExpr>(1);
  auto binOp = std::make_unique<BinaryOperatorExpr>(
      TokenKind::plus, std::move(lhs), std::move(rhs));
  auto retStmt = std::make_unique<ReturnStmt>(std::move(binOp));
  funcBody->Statements.push_back(std::move(retStmt));
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto func = std::make_unique<FuncDecl>(
      "foo", std::move(retType),
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      std::move(funcBody));
  unit->Decls.push_back(std::move(func));
  
  EXPECT_FALSE(analyze(unit.get()));
  bool hasUninitError = false;
  for (const auto& diag : Diags.getDiagnostics()) {
    if (diag.Message.find("未初始化") != std::string::npos) {
      hasUninitError = true;
      break;
    }
  }
  EXPECT_TRUE(hasUninitError);
}

TEST_F(SemaTest, UninitVarUsedInCallExpr) {
  // func foo() { var x: int; bar(x); }
  // x used without initialization → error
  auto unit = std::make_unique<TranslationUnit>();
  
  auto funcBody = std::make_unique<BlockStmt>();
  
  auto varType = std::make_unique<PrimitiveTypeNode>(TypeKind::Int32);
  auto varDecl = std::make_unique<VarDecl>("x", std::move(varType), nullptr);
  funcBody->Statements.push_back(std::move(varDecl));
  
  auto callee = std::make_unique<IdentifierExpr>("bar");
  auto arg = std::make_unique<IdentifierExpr>("x");
  llvm::SmallVector<std::unique_ptr<ExprNode>, 1> args;
  args.push_back(std::move(arg));
  auto callExpr = std::make_unique<CallExpr>(std::move(callee), std::move(args));
  auto exprStmt = std::make_unique<ExprStmt>(std::move(callExpr));
  funcBody->Statements.push_back(std::move(exprStmt));
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Void);
  auto func = std::make_unique<FuncDecl>(
      "foo", std::move(retType),
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      std::move(funcBody));
  unit->Decls.push_back(std::move(func));
  
  EXPECT_FALSE(analyze(unit.get()));
  bool hasUninitError = false;
  for (const auto& diag : Diags.getDiagnostics()) {
    if (diag.Message.find("未初始化") != std::string::npos) {
      hasUninitError = true;
      break;
    }
  }
  EXPECT_TRUE(hasUninitError);
}

TEST_F(SemaTest, InitCheckFrameworkExists) {
  // Verify the framework methods exist and work correctly
  // Create a simple function with no body - framework should not crash
  auto unit = std::make_unique<TranslationUnit>();
  
  auto retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Void);
  auto func = std::make_unique<FuncDecl>(
      "empty", std::move(retType),
      llvm::SmallVector<std::unique_ptr<ParamDecl>, 0>(),
      nullptr);  // null body
  unit->Decls.push_back(std::move(func));
  
  EXPECT_TRUE(analyze(unit.get()));
  EXPECT_EQ(Diags.getErrorCount(), 0u);
}

}  // anonymous namespace

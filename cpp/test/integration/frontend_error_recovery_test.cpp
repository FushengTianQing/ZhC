//===--- frontend_error_recovery_test.cpp - Error Recovery Tests ----------===//
//
// Integration tests for frontend error recovery.
// Tests that the parser can recover from errors and continue parsing.
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

namespace {

/// Error recovery test helper
class ErrorRecoveryTest : public ::testing::Test {
protected:
  struct ParseResult {
    std::unique_ptr<TranslationUnit> AST;
    DiagnosticsEngine Diags;
    bool HasErrors;
    unsigned ErrorCount;
    unsigned DeclCount;
  };

  ParseResult parse(const std::string& source) {
    ParseResult result;
    SourceManager SM;
    ASTContext Context(SM);
    
    result.Diags.setSourceManager(&SM);
    uint32_t fileID = SM.addString(source, "error_test.zhc");
    
    Lexer lexer(source, fileID);
    Parser parser(lexer, result.Diags, Context);
    
    result.AST = parser.parseTranslationUnit();
    result.HasErrors = result.Diags.hasErrors();
    result.ErrorCount = result.Diags.getErrorCount();
    
    if (result.AST) {
      result.DeclCount = result.AST->Decls.size();
    } else {
      result.DeclCount = 0;
    }
    
    return result;
  }

  /// Check if any error message contains the given substring
  bool hasErrorContaining(const ParseResult& result, const std::string& substr) {
    for (const auto& diag : result.Diags.getDiagnostics()) {
      if (diag.Level == DiagnosticLevel::Error &&
          diag.Message.find(substr) != std::string::npos) {
        return true;
      }
    }
    return false;
  }
};

//===----------------------------------------------------------------------===//
// T1.22b: Error Recovery Tests (5 fixtures)
//===----------------------------------------------------------------------===//

TEST_F(ErrorRecoveryTest, MissingSemicolon) {
  // Missing semicolon after declaration
  // Parser is lenient about missing semicolons (uses consumeIf pattern)
  // Both declarations should still be parsed without errors
  auto result = parse(
    "变量 x = 1\n"  // Missing semicolon
    "变量 y = 2;"   // Should still parse this
  );
  
  // Parser is lenient - no error for missing semicolon
  // (This is intentional: consumeIf(semi) doesn't report error)
  EXPECT_FALSE(result.HasErrors);
  EXPECT_EQ(result.ErrorCount, 0u);
  
  // Both declarations should be parsed
  EXPECT_GE(result.DeclCount, 2u);
}

TEST_F(ErrorRecoveryTest, UnmatchedParenthesis) {
  // Unmatched parenthesis in function call
  auto result = parse(
    "函数 测试() {"
    "  变量 结果 = 调用(1, 2;"  // Missing closing paren
    "  返回 结果;"
    "}"
  );
  
  // Should report error
  EXPECT_TRUE(result.HasErrors);
  
  // Should still have parsed the function
  EXPECT_GE(result.DeclCount, 1u);
}

TEST_F(ErrorRecoveryTest, UnknownToken) {
  // Invalid character in source
  auto result = parse(
    "@@ 变量 x = 1;"  // Invalid @@ at start
  );
  
  // Should report error for unknown token
  EXPECT_TRUE(result.HasErrors);
  EXPECT_TRUE(result.ErrorCount > 0);
  
  // Should still parse the declaration after skipping invalid token
  EXPECT_GE(result.DeclCount, 1u);
}

TEST_F(ErrorRecoveryTest, IncompleteExpression) {
  // Incomplete expression in return statement
  auto result = parse(
    "函数 不完整() {"
    "  返回 1 +"  // Missing RHS operand
    "}"
  );
  
  // Should report error
  EXPECT_TRUE(result.HasErrors);
  
  // Should still have parsed the function
  EXPECT_GE(result.DeclCount, 1u);
}

TEST_F(ErrorRecoveryTest, ErrorInNestedBlock) {
  // Error inside nested block should not affect outer block
  auto result = parse(
    "函数 外层() {"
    "  如果 (真) {"
    "    @@ 变量 内层 = 1;"  // Error inside nested block
    "  }"
    "  变量 外层变量 = 2;"  // Should still parse this
    "}"
  );
  
  // Should report error
  EXPECT_TRUE(result.HasErrors);
  
  // Should still have parsed the function
  EXPECT_GE(result.DeclCount, 1u);
  
  // Function body should have statements
  if (result.AST && result.AST->Decls.size() > 0) {
    auto* func = static_cast<FuncDecl*>(result.AST->Decls[0].get());
    if (func->Body) {
      auto* block = static_cast<BlockStmt*>(func->Body.get());
      EXPECT_GE(block->Statements.size(), 1u);
    }
  }
}

//===----------------------------------------------------------------------===//
// Additional error recovery tests
//===----------------------------------------------------------------------===//

TEST_F(ErrorRecoveryTest, MultipleErrors) {
  // Multiple errors in sequence
  auto result = parse(
    "@@ 变量 a = 1;\n"  // Error 1
    "变量 b = @@;\n"    // Error 2
    "变量 c = 3;"       // Should still parse
  );
  
  EXPECT_TRUE(result.HasErrors);
  EXPECT_GE(result.ErrorCount, 2u);
  
  // Should still parse valid declarations
  EXPECT_GE(result.DeclCount, 1u);
}

TEST_F(ErrorRecoveryTest, MissingClosingBrace) {
  // Missing closing brace at EOF
  auto result = parse(
    "函数 无结束() {"
    "  变量 x = 1;"
    // Missing }
  );
  
  // Should handle gracefully
  EXPECT_TRUE(result.AST != nullptr);
}

TEST_F(ErrorRecoveryTest, InvalidType) {
  // Invalid type name
  auto result = parse(
    "变量 x : 不存在的类型 = 1;"
  );
  
  // Should parse (type is just an identifier)
  EXPECT_TRUE(result.AST != nullptr);
  EXPECT_GE(result.DeclCount, 1u);
}

TEST_F(ErrorRecoveryTest, MissingFunctionBody) {
  // Function without body
  auto result = parse(
    "函数 无体()"  // Missing body
    "变量 y = 2;"
  );
  
  // Should handle gracefully
  EXPECT_TRUE(result.AST != nullptr);
}

TEST_F(ErrorRecoveryTest, RecoveryAtStatementBoundary) {
  // Error followed by valid statement at same level
  auto result = parse(
    "函数 测试() {"
    "  @@ 错误语句\n"  // Error
    "  变量 正确 = 42;"  // Should recover and parse this
    "  返回 正确;"
    "}"
  );
  
  EXPECT_TRUE(result.HasErrors);
  
  // Should still have parsed the function
  EXPECT_GE(result.DeclCount, 1u);
}

TEST_F(ErrorRecoveryTest, DeeplyNestedError) {
  // Error in deeply nested structure
  auto result = parse(
    "函数 深层() {"
    "  如果 (真) {"
    "    循环 (真) {"
    "      对于 (变量 i = 0; i < 10; i = i + 1) {"
    "        @@ 深层错误\n"  // Error at deepest level
    "      }"
    "    }"
    "  }"
    "  变量 恢复 = 1;"  // Should recover to outer level
    "}"
  );
  
  EXPECT_TRUE(result.HasErrors);
  EXPECT_GE(result.DeclCount, 1u);
}

}  // anonymous namespace
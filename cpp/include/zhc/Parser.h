//===--- Parser.h - ZhC Parser Interface ---------------------------------===//
//
// This file defines the recursive descent parser for the ZhC compiler.
//
//===----------------------------------------------------------------------===//

#ifndef ZHC_PARSER_H
#define ZHC_PARSER_H

#include "zhc/Lexer.h"
#include "zhc/Diagnostics.h"
#include "zhc/AST.h"

#include <memory>

namespace zhc {

/// Recursive descent parser for ZhC
class Parser {
public:
  Parser(Lexer& lex, DiagnosticsEngine& diag);
  
  /// Parse a translation unit (top-level declarations)
  std::unique_ptr<TranslationUnit> parseTranslationUnit();
  
  /// Check if any parse errors occurred
  bool hasErrors() const { return DiagEngine.hasErrors(); }
  
private:
  Lexer& Lex;
  DiagnosticsEngine& DiagEngine;
  
  /// Current token
  Token CurrentToken;
  
  /// Advance to the next token
  void advance();
  
  /// Consume a token of the expected kind
  bool expect(TokenKind kind);
  
  /// Consume a token if it matches, otherwise don't advance
  bool consumeIf(TokenKind kind);
  
  //=== Expression Parsing ===
  
  std::unique_ptr<ExprNode> parseExpression();
  std::unique_ptr<ExprNode> parsePrimaryExpr();
  std::unique_ptr<ExprNode> parseBinaryExpr(int precedence = 0);
  
  //=== Statement Parsing ===
  
  std::unique_ptr<StmtNode> parseStatement();
  std::unique_ptr<StmtNode> parseIfStatement();
  std::unique_ptr<StmtNode> parseWhileStatement();
  std::unique_ptr<StmtNode> parseReturnStatement();
  
  //=== Declaration Parsing ===
  
  std::unique_ptr<DeclNode> parseDeclaration();
  std::unique_ptr<FuncDecl> parseFunctionDeclaration();
  std::unique_ptr<VarDecl> parseVariableDeclaration();
};

} // namespace zhc

#endif // ZHC_PARSER_H